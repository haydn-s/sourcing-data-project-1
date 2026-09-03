"""The affordability maths, and the invariants the decomposition must satisfy.

Every headline number in this project is a function of `monthly_payment`, so it
is checked against a hand-computable amortisation value rather than against
whatever the code happens to produce today. The decomposition is checked by its
defining identity: the parts must reconstruct the whole exactly, or the
"interaction" term is hiding an error rather than reporting a residual.
"""

import numpy as np
import pandas as pd
import pytest

from config import DOWN_PAYMENT_PCT, TAX_INSURANCE_PCT
from features import (
    build_affordability,
    decompose_payment_change,
    decompose_sensitivity,
    latest_complete_year,
    monthly_payment,
    piti,
)


# --------------------------------------------------------------- amortisation

def test_monthly_payment_matches_textbook_amortisation():
    """$200k borrowed at 6% over 30 years is $1,199.10/month.

    Priced at $250,000 with 20% down, the loan is exactly $200,000. The closed
    form is L*r*(1+r)^n / ((1+r)^n - 1) with r = 0.005 and n = 360.
    """
    got = float(monthly_payment(250_000, 6.0))
    assert got == pytest.approx(1199.10, abs=0.01)


def test_monthly_payment_handles_the_singular_zero_rate_case():
    """At 0% the closed form divides by zero; repayment is straight-line."""
    got = float(monthly_payment(250_000, 0.0))
    assert got == pytest.approx(200_000 / 360, abs=1e-9)


def test_monthly_payment_is_vectorised_over_price_and_rate():
    prices = np.array([200_000.0, 400_000.0])
    rates = np.array([3.0, 6.0])
    out = monthly_payment(prices, rates)
    assert out.shape == (2,)
    # Same price, double the rate -> strictly more interest, so a bigger payment.
    assert float(monthly_payment(400_000, 6.0)) > float(monthly_payment(400_000, 3.0))
    # Same rate, double the price -> exactly double the payment (linear in price).
    assert float(monthly_payment(400_000, 6.0)) == pytest.approx(
        2 * float(monthly_payment(200_000, 6.0)))


def test_monthly_payment_scales_linearly_with_price():
    """features.decompose_sensitivity relies on this to claim that deflating
    changes the dollar magnitudes but not the shares."""
    k = 1.37
    base = float(monthly_payment(300_000, 5.5))
    assert float(monthly_payment(300_000 * k, 5.5)) == pytest.approx(base * k)


def test_piti_adds_exactly_the_tax_and_insurance_escrow():
    price, rate = 400_000, 6.5
    expected = float(monthly_payment(price, rate)) + price * TAX_INSURANCE_PCT / 12
    assert float(piti(price, rate)) == pytest.approx(expected)


def test_down_payment_reduces_the_borrowed_principal():
    """A 20% deposit must finance 80% of the price, not the whole of it."""
    full = float(monthly_payment(500_000, 6.0, down_pct=0.0))
    twenty = float(monthly_payment(500_000, 6.0, down_pct=DOWN_PAYMENT_PCT))
    assert twenty == pytest.approx(full * (1 - DOWN_PAYMENT_PCT))


# ------------------------------------------------------------------- fixtures

@pytest.fixture
def panel():
    """A small annual panel with the columns build_affordability consumes."""
    years = [2015, 2019, 2020, 2021, 2024, 2025, 2026]
    n = len(years)
    return pd.DataFrame(
        {
            "MSPUS": [294_150.0, 320_250, 328_150, 383_000, 418_975, 415_400, 409_050],
            "MORTGAGE30US": [3.85, 3.93, 3.11, 2.96, 6.72, 6.60, 6.35],
            "age_25_34_median_current": [60_000.0, 70_280, 71_610, 74_860, 90_100,
                                         np.nan, np.nan],
            "all_median_current": [56_000.0, 68_700, 68_010, 70_780, 83_730,
                                   np.nan, np.nan],
            "CPIAUCSL": [237.0, 255.7, 258.8, 271.0, 314.0, 322.0, 330.0],
            "hor_under_35": [34.7, 36.7, 39.2, 38.2, 37.1, 37.1, 36.0],
            "hor_all": [63.7, 64.6, 66.6, 65.5, 65.6, 65.2, 64.9],
            "SLOAS": [1_300_000.0] * n,
            "CCLACBW027SBOG": [750.0] * n,
            "POPTHM": [320_000.0, 328_000, 330_000, 332_000, 340_000, 342_000, 343_000],
            "months_observed": [12, 12, 12, 12, 12, 12, 8],
            "is_partial_year": [False, False, False, False, False, False, True],
        },
        index=pd.Index(years, name="year"),
    )


@pytest.fixture
def affordability(panel):
    return build_affordability(panel)


# ----------------------------------------------------------- panel invariants

def test_required_income_inverts_the_dti_rule(affordability):
    """required_income * 0.28 must be exactly the annual housing cost."""
    d = affordability
    assert (d["annual_housing_cost"] / d["required_income"]).round(10).eq(0.28).all()


def test_affordability_index_is_100_when_income_equals_requirement(affordability):
    d = affordability.dropna(subset=["affordability_index"])
    implied = d["income_young"] / d["required_income"] * 100
    assert d["affordability_index"].values == pytest.approx(implied.values)


def test_real_columns_equal_nominal_in_the_deflation_base_year(affordability):
    """2024 is the constant-dollar base, so real and nominal must coincide there."""
    row = affordability.loc[2024]
    for col in ("median_price", "required_income", "income_young"):
        assert row[f"{col}_real2024"] == pytest.approx(row[col])


def test_credit_card_and_student_debt_sum_to_consumer_debt(affordability):
    d = affordability
    total = d["student_debt_per_capita"] + d["credit_card_debt_per_capita"]
    assert d["consumer_debt_per_capita"].values == pytest.approx(total.values)


def test_debt_series_are_scaled_out_of_their_native_fred_units(affordability):
    """SLOAS is $M and CCLACBW027SBOG is $B; population is in thousands. Getting
    either scale wrong is a silent 1000x error, so pin the magnitudes."""
    row = affordability.loc[2024]
    assert 1_000 < row["student_debt_per_capita"] < 20_000
    assert 500 < row["credit_card_debt_per_capita"] < 10_000


# --------------------------------------------------------------- decomposition

def test_decomposition_parts_reconstruct_the_whole(affordability):
    """price + rate + interaction == total, exactly. This is the identity that
    makes reporting an interaction term honest rather than a fudge."""
    d = decompose_payment_change(affordability, base_year=2021)
    recomposed = d["price_effect"] + d["rate_effect"] + d["interaction"]
    assert recomposed.values == pytest.approx(d["total_change"].values)


def test_decomposition_is_zero_at_its_own_base_year(affordability):
    d = decompose_payment_change(affordability, base_year=2021)
    assert d.loc[2021, "total_change"] == pytest.approx(0.0, abs=1e-9)


def test_decomposition_rejects_a_base_year_outside_the_panel(affordability):
    with pytest.raises(ValueError, match="base year"):
        decompose_payment_change(affordability, base_year=1901)


# ---------------------------------------------------- sensitivity / robustness

def test_sensitivity_identity_holds_in_both_denominations(affordability):
    s = decompose_sensitivity(affordability, base_years=(2015, 2019, 2021))
    for prefix in ("", "real_"):
        parts = (s[f"{prefix}price_effect"] + s[f"{prefix}rate_effect"]
                 + s[f"{prefix}interaction"])
        assert parts.values == pytest.approx(s[f"{prefix}total_change"].values)


def test_sensitivity_shares_sum_to_100(affordability):
    s = decompose_sensitivity(affordability, base_years=(2015, 2019, 2021))
    total = (s["price_effect_share"] + s["rate_effect_share"]
             + s["interaction_share"])
    assert total.values == pytest.approx(100.0)


def test_sensitivity_defaults_to_the_last_complete_year(affordability):
    """2026 is partial, so a default sweep must end at 2025 -- letting a
    year-to-date average set the headline is the bug this guards."""
    s = decompose_sensitivity(affordability, base_years=(2019,))
    assert int(s["end_year"].iloc[0]) == 2025


def test_shares_are_flagged_unreadable_when_the_effects_disagree(affordability):
    """Once real prices fall, the two effects take opposite signs and the
    percentages run past 100 and below zero. They must be flagged, not printed."""
    s = decompose_sensitivity(affordability, base_years=(2015, 2019, 2021))
    same_sign = np.sign(s["real_price_effect"]) == np.sign(s["real_rate_effect"])
    assert s["real_shares_readable"].equals(same_sign & (s["real_total_change"] != 0))


def test_dominant_factor_names_the_larger_effect(affordability):
    s = decompose_sensitivity(affordability, base_years=(2015, 2019, 2021))
    for prefix in ("", "real_"):
        larger = np.where(s[f"{prefix}price_effect"] > s[f"{prefix}rate_effect"],
                          "price", "rate")
        assert list(s[f"{prefix}dominant_factor"]) == list(larger)


def test_deflating_changes_dollars_but_not_shares(affordability):
    """The claim made in config.REAL_DOLLAR_BASE_YEAR's comment. Both effects are
    linear in price, so a common deflator cancels out of every ratio."""
    s = decompose_sensitivity(affordability, base_years=(2019,))
    row = s.iloc[0]
    assert row["real_total_change"] != pytest.approx(row["total_change"])
    nominal_ratio = row["price_effect"] / row["total_change"]
    # Same base year, so the deflator is a single constant on both prices.
    assert 0 < abs(nominal_ratio) < 10


def test_latest_complete_year_ignores_partial_years(affordability):
    assert latest_complete_year(affordability) == 2025


def test_latest_complete_year_raises_when_nothing_is_complete(affordability):
    d = affordability.copy()
    d["is_partial_year"] = True
    with pytest.raises(ValueError, match="no complete year"):
        latest_complete_year(d)
