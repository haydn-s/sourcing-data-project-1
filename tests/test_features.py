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

from config import DOWN_PAYMENT_PCT, MAINTENANCE_PCT, TAX_INSURANCE_PCT
from features import (
    build_affordability,
    decompose_payment_change,
    decompose_sensitivity,
    latest_complete_year,
    complete_year_means,
    housing_supply,
    inflation_summary,
    metro_price_growth,
    supply_summary,
    monthly_payment,
    piti,
    real_change,
    years_to_save_moving,
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
            "cpi_inflation": [0.1, 1.8, 1.2, 4.7, 3.0, 2.5, 2.4],
            "hor_under_35": [34.7, 36.7, 39.2, 38.2, 37.1, 37.1, 36.0],
            "hor_all": [63.7, 64.6, 66.6, 65.5, 65.6, 65.2, 64.9],
            "SLOAS": [1_300_000.0] * n,
            "CCLACBW027SBOG": [750.0] * n,
            "POPTHM": [320_000.0, 328_000, 330_000, 332_000, 340_000, 342_000, 343_000],
            "asking_rent": [780.0, 1005, 1104, 1216, 1487, 1490, 1555],
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


# ------------------------------------------------------------- rent versus own

def test_ownership_cost_adds_maintenance_on_top_of_piti(affordability):
    d = affordability
    expected = d["monthly_piti"] + d["median_price"] * MAINTENANCE_PCT / 12
    assert d["monthly_ownership_cost"].values == pytest.approx(expected.values)


def test_ownership_cost_always_exceeds_piti(affordability):
    """Maintenance is a cost a renter never sees; it can only add."""
    assert (affordability["monthly_ownership_cost"]
            > affordability["monthly_piti"]).all()


def test_own_to_rent_ratio_matches_its_components(affordability):
    d = affordability
    assert d["own_to_rent_ratio"].values == pytest.approx(
        (d["monthly_ownership_cost"] / d["asking_rent"]).values)
    assert d["own_minus_rent"].values == pytest.approx(
        (d["monthly_ownership_cost"] - d["asking_rent"]).values)


def test_rent_burden_is_annualised_against_income(affordability):
    """rent_to_income compares twelve months of rent to a year of income; using
    the monthly figure would understate the burden twelvefold."""
    d = affordability.dropna(subset=["rent_to_income"])
    assert d["rent_to_income"].values == pytest.approx(
        (d["asking_rent"] * 12 / d["income_young"]).values)
    assert (d["rent_to_income"] < 1).all()


def test_income_after_rent_is_the_saving_pool(affordability):
    d = affordability.dropna(subset=["income_after_rent"])
    assert d["income_after_rent"].values == pytest.approx(
        (d["income_young"] - d["asking_rent"] * 12).values)
    assert (d["income_after_rent"] < d["income_young"]).all()


def test_rent_has_a_real_series_for_the_long_comparison(affordability):
    """The headline rent-vs-own claim is about real growth over 38 years, so the
    deflated column has to exist and agree in the base year."""
    row = affordability.loc[2024]
    assert row["asking_rent_real2024"] == pytest.approx(row["asking_rent"])
    assert row["monthly_ownership_cost_real2024"] == pytest.approx(
        row["monthly_ownership_cost"])


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


# ------------------------------------------------------- regional price growth

def _metro_frame(values_by_year, months=12):
    """Monthly metro indices from per-year levels, one column per series id.

    `values_by_year` maps a series id to {year: level}. The level is repeated
    for each month unless it is a list, which supplies the months directly --
    that is how a seasonal pattern or a missing month gets in.
    """
    frames = {}
    for sid, by_year in values_by_year.items():
        points = {}
        for year, level in by_year.items():
            monthly = level if isinstance(level, list) else [level] * months
            for m, v in enumerate(monthly, start=1):
                points[pd.Timestamp(year=year, month=m, day=1)] = v
        frames[sid] = pd.Series(points, dtype=float)
    return pd.DataFrame(frames).sort_index()


@pytest.fixture
def cpi():
    return pd.Series({2021: 100.0, 2022: 105.0, 2023: 110.0, 2024: 115.0, 2025: 120.0})


def test_metro_growth_compares_annual_means_not_single_months(cpi):
    """The indices are not seasonally adjusted. A June-to-June or January-to-
    January comparison would pick up the season; the annual mean cancels it."""
    seasonal = [90.0] * 6 + [110.0] * 6          # mean 100, but no month is 100
    metros = _metro_frame({"AAA": {2021: seasonal, 2025: [v * 1.5 for v in seasonal]}})
    out = metro_price_growth(metros, cpi, base_year=2021, end_year=2025)
    assert out.loc["AAA", "index_base"] == pytest.approx(100.0)
    assert out.loc["AAA", "growth_pct"] == pytest.approx(50.0)


def test_metro_real_growth_is_zero_when_prices_only_track_inflation(cpi):
    metros = _metro_frame({"AAA": {2021: 200.0, 2025: 240.0}})   # +20%, CPI +20%
    out = metro_price_growth(metros, cpi, base_year=2021, end_year=2025)
    assert out.loc["AAA", "growth_pct"] == pytest.approx(20.0)
    assert out.loc["AAA", "real_growth_pct"] == pytest.approx(0.0, abs=1e-9)


def test_metro_ranking_runs_fastest_to_slowest_and_deflating_cannot_reorder_it(cpi):
    metros = _metro_frame({
        "SLOW": {2021: 100.0, 2025: 110.0},
        "FAST": {2021: 100.0, 2025: 150.0},
        "MID":  {2021: 100.0, 2025: 125.0},
    })
    out = metro_price_growth(metros, cpi, base_year=2021, end_year=2025)
    assert list(out.index) == ["FAST", "MID", "SLOW"]
    assert list(out["rank"]) == [1, 2, 3]
    assert list(out["growth_pct"]) == sorted(out["growth_pct"], reverse=True)
    assert out.loc["SLOW", "real_growth_pct"] < 0 < out.loc["FAST", "real_growth_pct"]


def test_metro_names_come_from_config(cpi):
    metros = _metro_frame({"MIXRNSA": {2021: 100.0, 2025: 110.0},
                           "UNKNOWN": {2021: 100.0, 2025: 110.0}})
    out = metro_price_growth(metros, cpi, base_year=2021, end_year=2025)
    assert out.loc["MIXRNSA", "metro"] == "Miami"
    assert out.loc["UNKNOWN", "metro"] == "UNKNOWN"     # falls back to the id


def test_metro_window_ends_at_the_last_year_every_metro_completed(cpi):
    """2025 is complete for one metro but the other is still a month short, so
    the default window must stop at 2024 rather than rank the two on different
    spans -- the same bug latest_complete_year guards for the national panel."""
    metros = _metro_frame({
        "AAA": {2021: 100.0, 2024: 120.0, 2025: 130.0},
        "BBB": {2021: 100.0, 2024: 110.0, 2025: [115.0] * 11 + [np.nan]},
    })
    out = metro_price_growth(metros, cpi, base_year=2021)
    assert set(out["end_year"]) == {2024}
    assert out.loc["AAA", "growth_pct"] == pytest.approx(20.0)


def test_metro_growth_rejects_an_incomplete_base_year(cpi):
    metros = _metro_frame({"AAA": {2021: [100.0] * 6 + [np.nan] * 6, 2025: 130.0}})
    with pytest.raises(ValueError, match="base year 2021"):
        metro_price_growth(metros, cpi, base_year=2021, end_year=2025)


def test_metro_growth_rejects_a_year_with_no_cpi(cpi):
    metros = _metro_frame({"AAA": {2021: 100.0, 2025: 130.0}})
    with pytest.raises(ValueError, match="no CPI"):
        metro_price_growth(metros, cpi.drop(2025), base_year=2021, end_year=2025)


# ----------------------------------------------------------------- supply check

def _monthly(values_by_year):
    """Monthly series from per-year levels; a list supplies the months directly."""
    points = {}
    for year, level in values_by_year.items():
        months = level if isinstance(level, list) else [level] * 12
        for m, v in enumerate(months, start=1):
            points[pd.Timestamp(year=year, month=m, day=1)] = v
    return pd.Series(points, dtype=float)


def test_complete_year_means_drop_short_years():
    s = _monthly({2020: 10.0, 2021: [20.0] * 11 + [np.nan]})
    out = complete_year_means(s)
    assert list(out.index) == [2020]
    assert out[2020] == pytest.approx(10.0)


def test_supply_summary_reads_both_halves_of_the_claim():
    years = range(2004, 2024)
    starts = {y: 1000.0 for y in years}
    starts.update({2005: 1500.0, 2006: 1300.0, 2021: 1200.0, 2022: 1100.0})
    monthly = pd.DataFrame({
        "ACTLISCOUUS": _monthly({**{y: 1000.0 for y in (2017, 2018, 2019)},
                                 **{y: 500.0 for y in (2021, 2022, 2023)}}),
        "RHVRUSQ156N": _monthly({**{y: 2.0 for y in years}, 2023: 0.8}),
        "HOUST1F": _monthly(starts),
        "MSACSR": _monthly({2021: 5.0, 2023: 8.0}),
    })
    s = supply_summary(monthly, shock=(2021, 2023), baseline=(2017, 2019))
    assert s["listings_ratio"] == pytest.approx(0.5)
    assert (s["vacancy_first_year"], s["vacancy_low_year"]) == (2004, 2023)
    # 2021 beats every year back to 2006, which is itself higher: "most since 2006".
    assert (s["starts_peak_year"], s["starts_last_higher_year"]) == (2021, 2006)
    assert s["starts_highest_since_peak"] == pytest.approx(1100.0)
    assert (s["new_home_supply_start"], s["new_home_supply_end"]) == (5.0, 8.0)


def test_housing_supply_indexes_each_series_to_its_own_baseline():
    listings = {2017: 1000.0, 2018: 1200.0, 2019: 800.0, 2021: 500.0}
    starts = {2016: 50.0, 2017: 90.0, 2018: 100.0, 2019: 110.0, 2021: 130.0}
    monthly = pd.DataFrame({"ACTLISCOUUS": _monthly(listings), "HOUST1F": _monthly(starts)})
    out = housing_supply(monthly, baseline=(2017, 2019))
    # 2016 has starts but no listings, so both lines begin together in 2017.
    assert list(out.index) == [2017, 2018, 2019, 2021]
    assert out.loc[2017:2019, "listings_index"].mean() == pytest.approx(100.0)
    assert out.loc[2017:2019, "starts_index"].mean() == pytest.approx(100.0)
    assert out.loc[2021, "listings_index"] == pytest.approx(50.0)
    assert out.loc[2021, "starts_index"] == pytest.approx(130.0)
    assert set(out["baseline_start"]) == {2017} and set(out["baseline_end"]) == {2019}


# -------------------------------------------------------------------- inflation

def test_real_mortgage_rate_subtracts_that_years_inflation(affordability):
    assert affordability.loc[2021, "real_mortgage_rate"] == pytest.approx(2.96 - 4.7)
    assert affordability.loc[2024, "real_mortgage_rate"] == pytest.approx(6.72 - 3.0)


def test_real_change_is_zero_when_a_series_only_tracks_cpi():
    df = pd.DataFrame({"x": [100.0, 150.0], "cpi": [200.0, 300.0]}, index=[2000, 2010])
    assert real_change(df, "x", 2000, 2010) == pytest.approx(0.0, abs=1e-12)


def test_moving_target_reduces_to_the_static_measure_when_nothing_moves():
    """$400k at 20% down is $80k; 10% of $90k a year is $9k, so 8.89 years --
    the same arithmetic as years_to_save_down."""
    assert years_to_save_moving(400_000, 90_000, 0, 0, 0) == pytest.approx(80_000 / 9_000)


def test_moving_target_takes_longer_when_prices_outrun_savings():
    static = years_to_save_moving(400_000, 90_000, 0, 0, 0)
    both_track_inflation = years_to_save_moving(400_000, 90_000, 0.03, 0.03, 0.03)
    savings_earn_nothing = years_to_save_moving(400_000, 90_000, 0.03, 0.03, 0.0)
    prices_outrun_incomes = years_to_save_moving(400_000, 90_000, 0.04, 0.03, 0.03)
    # Everything growing together, savings included, is the static case scaled up.
    assert both_track_inflation == pytest.approx(static, abs=0.35)
    assert savings_earn_nothing > both_track_inflation
    assert prices_outrun_incomes > both_track_inflation


def test_inflation_summary_deflates_against_the_same_cpi_as_the_real_columns(panel):
    # The summary reads the configured years (2005, 2021, 2023), so fill the
    # fixture's gaps into a continuous annual panel first.
    years = range(2005, 2027)
    numeric = panel.drop(columns=["is_partial_year", "months_observed"])
    full = numeric.reindex(years).astype(float).interpolate(limit_direction="both")
    full["is_partial_year"] = [y == 2026 for y in years]
    full["months_observed"] = [8 if y == 2026 else 12 for y in years]
    affordability = build_affordability(full)
    deflators = pd.DataFrame({"CUSR0000SA0L2": affordability["cpi"] * 0.9}, index=affordability.index)
    s = inflation_summary(affordability, deflators)
    base, last = 2021, s["latest_year"]
    expected = ((affordability.loc[last, "median_price_real2024"]
                 / affordability.loc[base, "median_price_real2024"]) - 1) * 100
    assert s["price_real_since_shock"] == pytest.approx(expected)
    # A deflator proportional to CPI must give the same real rent change.
    assert s["rent_real_less_shelter"] == pytest.approx(s["rent_real_cpi"])
