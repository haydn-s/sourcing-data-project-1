"""Every number the README asserts, checked against the generated data.

The README quotes roughly forty figures. Each one was true when it was written,
and any of them can go stale the moment a source publishes a revision or an
assumption in config.py changes — silently, because prose does not raise.

So the README is the input here, not the expectation: each claim is *read out of
the markdown* by regex and compared against the CSVs in data/processed/. Edit a
number in one place and not the other and this fails, naming the claim.

Marked `requires_data` — it needs a pipeline run. `pytest -m "not requires_data"`
skips it on a fresh clone.
"""

import re
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

pytestmark = pytest.mark.requires_data


# ------------------------------------------------------------------ fixtures

@pytest.fixture(scope="module")
def readme():
    """The README with whitespace collapsed, so a claim that wraps across two
    lines still matches a single-line regex."""
    text = (ROOT / "README.md").read_text()
    return re.sub(r"\s+", " ", text)


@pytest.fixture(scope="module")
def data():
    needed = ["affordability.csv", "decomposition_sensitivity.csv",
              "payment_decomposition.csv"]
    missing = [f for f in needed if not (PROCESSED / f).exists()]
    if missing:
        pytest.skip(f"run `python src/run_all.py` first; missing {missing}")
    return {
        "aff": pd.read_csv(PROCESSED / "affordability.csv", index_col="year"),
        "sens": pd.read_csv(PROCESSED / "decomposition_sensitivity.csv",
                            index_col="base_year"),
        "decomp": pd.read_csv(PROCESSED / "payment_decomposition.csv",
                              index_col="year"),
    }


def _to_float(token):
    r"""Normalise a number lifted out of prose or a table cell.

    Handles thousands separators, the Unicode minus the table uses, a leading
    dollar sign, and a trailing sentence period that `[\d.]+` happily swallows.
    """
    t = token.strip().replace(",", "").replace("−", "-").replace("$", "")
    return float(t.rstrip("."))


def claimed(readme, pattern, group=1):
    """Pull one number out of the README, or fail saying which claim vanished."""
    m = re.search(pattern, readme)
    assert m, f"claim not found in README (did the wording change?): {pattern}"
    return _to_float(m.group(group))


def pct_change(df, col, start, end):
    return (df.loc[end, col] / df.loc[start, col] - 1) * 100


# --------------------------------------------------- findings 1 and 2

def test_headline_changes_2021_to_2023(readme, data):
    aff = data["aff"]
    assert claimed(readme, r"prices \+([\d.]+)%, mortgage rate") == pytest.approx(
        pct_change(aff, "median_price", 2021, 2023), abs=0.05)
    assert claimed(readme, r"mortgage rate \+(\d+)%") == pytest.approx(
        pct_change(aff, "mortgage_rate", 2021, 2023), abs=1.0)
    assert claimed(readme, r"monthly payment \+([\d.]+)%") == pytest.approx(
        pct_change(aff, "monthly_piti", 2021, 2023), abs=0.05)


def test_headline_rates_quoted_for_2021_and_2023(readme, data):
    aff = data["aff"]
    assert claimed(readme, r"\(([\d.]+)% → [\d.]+%\)") == pytest.approx(
        aff.loc[2021, "mortgage_rate"], abs=0.01)
    assert claimed(readme, r"\([\d.]+% → ([\d.]+)%\)") == pytest.approx(
        aff.loc[2023, "mortgage_rate"], abs=0.01)


def test_decomposition_of_the_2023_increase(readme, data):
    row = data["decomp"].loc[2023]
    assert claimed(readme, r"splits the \$([\d,]+)/month increase") == pytest.approx(
        row["total_change"], abs=1)
    assert claimed(readme, r"into \$(\d+) from prices") == pytest.approx(
        row["price_effect"], abs=1)
    assert claimed(readme, r"\$(\d+) from rates") == pytest.approx(
        row["rate_effect"], abs=1)
    assert claimed(readme, r"\$(\d+) from their interaction") == pytest.approx(
        row["interaction"], abs=1)


# --------------------------------------------------- finding 3: the sweep

def _sensitivity_table(raw_readme):
    """Parse the finding-3 markdown table.

    Cells carry bold markers and trailing '<- crossover' annotations, and the
    negative price effect uses a Unicode minus, so everything is stripped back
    to plain numbers before comparison.
    """
    rows = {}
    # A money cell is an optional sign, then an optional $, then digits -- the
    # sign sits OUTSIDE the dollar sign in the negative row ("−$186").
    money = r"([−-]?\$?[\d,]+)"
    pattern = re.compile(
        r"^\s*\|\s*\**(\d{4})\**\s*\|"                     # anchor year
        rf"\s*\**{money}\s*/\s*{money}\**\s*\|"              # nominal pair
        rf"\s*\**{money}\s*/\s*{money}\**\s*\|"              # real pair
        r"\s*\**(prices|rates)\**",                            # verdict
        re.MULTILINE)
    for m in pattern.finditer(raw_readme):
        year = int(m.group(1))
        nums = [_to_float(g) for g in m.groups()[1:5]]
        rows[year] = {"nom_price": nums[0], "nom_rate": nums[1],
                      "real_price": nums[2], "real_rate": nums[3],
                      "verdict": m.group(6).rstrip("s")}
    return rows


def test_sensitivity_table_was_parsed_at_all():
    raw = (ROOT / "README.md").read_text()
    rows = _sensitivity_table(raw)
    assert len(rows) >= 8, f"expected the 8-row finding-3 table, parsed {len(rows)}"


@pytest.mark.parametrize("anchor", [2006, 2009, 2011, 2012, 2015, 2019, 2020, 2021])
def test_sensitivity_table_row_matches_the_data(anchor, data):
    raw = (ROOT / "README.md").read_text()
    claim = _sensitivity_table(raw)[anchor]
    row = data["sens"].loc[anchor]
    assert claim["nom_price"] == pytest.approx(row["price_effect"], abs=1)
    assert claim["nom_rate"] == pytest.approx(row["rate_effect"], abs=1)
    assert claim["real_price"] == pytest.approx(row["real_price_effect"], abs=1)
    assert claim["real_rate"] == pytest.approx(row["real_rate_effect"], abs=1)
    assert claim["verdict"] == row["real_dominant_factor"]


def test_sweep_span_and_end_year(readme, data):
    sens = data["sens"]
    assert claimed(readme, r"all (\d+) anchors from") == len(sens)
    assert claimed(readme, r"anchors from (\d{4}) to") == sens.index.min()
    assert claimed(readme, r"anchors from \d{4} to (\d{4})") == sens.index.max()
    assert claimed(readme, r"measured through (\d{4})") == sens["end_year"].iloc[0]


def test_both_crossover_years(readme, data):
    sens = data["sens"]
    real = int(sens.index[sens["real_dominant_factor"].eq("rate")].min())
    nominal = int(sens.index[sens["dominant_factor"].eq("rate")].min())
    assert claimed(readme, r"rates lead from \*\*(\d{4})\*\* on") == real
    assert claimed(readme, r"they only lead from \*\*(\d{4})\*\*") == nominal
    assert nominal - real == 8, "the README calls this an eight-year gap"


def test_cpi_growth_across_the_window(readme, data):
    aff, sens = data["aff"], data["sens"]
    end = int(sens["end_year"].iloc[0])
    actual = (aff.loc[end, "cpi"] / aff.loc[2006, "cpi"] - 1) * 100
    assert claimed(readme, r"CPI rose (\d+)%") == pytest.approx(actual, abs=1)


def test_real_prices_fell_after_the_shock(readme, data):
    """The README says real prices 'actually fell' between 2021 and 2025 — the
    reason the last table row carries a negative price effect."""
    assert data["sens"].loc[2021, "real_price_effect"] < 0


# --------------------------------------------------- findings 4 to 7

def test_income_comparison(readme, data):
    aff = data["aff"]
    assert claimed(readme, r"was \$([\d,]+) in 2024 versus") == pytest.approx(
        aff.loc[2024, "income_young"], abs=1)
    assert claimed(readme, r"versus \$([\d,]+) for all households") == pytest.approx(
        aff.loc[2024, "income_all_ages"], abs=1)
    assert claimed(readme, r"\*\*([\d.]+)×\*\* the all-ages median") == pytest.approx(
        aff.loc[2024, "income_young"] / aff.loc[2024, "income_all_ages"], abs=0.005)


def test_affordability_index_fall(readme, data):
    aff = data["aff"]
    assert claimed(readme, r"index fell from (\d+\.\d+)") == pytest.approx(
        aff.loc[2021, "affordability_index"], abs=0.05)
    assert claimed(readme, r"index fell from \d+\.\d+ to (\d+\.\d+)") == pytest.approx(
        aff.loc[2023, "affordability_index"], abs=0.05)


def test_the_1980s_comparison(readme, data):
    aff = data["aff"]
    assert claimed(readme, r"1984's affordability index was ([\d.]+)") == pytest.approx(
        aff.loc[1984, "affordability_index"], abs=0.05)
    assert claimed(readme, r"below 2024's ([\d.]+)") == pytest.approx(
        aff.loc[2024, "affordability_index"], abs=0.05)
    assert claimed(readme, r"\*\*([\d.]+) years\*\* of income in 1984") == pytest.approx(
        aff.loc[1984, "years_to_save_down"], abs=0.05)
    assert claimed(readme, r"\*\*([\d.]+) years\*\* in 2024") == pytest.approx(
        aff.loc[2024, "years_to_save_down"], abs=0.05)


def test_homeownership_outcome(readme, data):
    hor = data["aff"]["hor_under_35"].dropna()
    assert claimed(readme, r"under 35 is \*\*([\d.]+)%\*\*") == pytest.approx(
        hor.iloc[-1], abs=0.05)
    assert claimed(readme, r"below its \*\*([\d.]+)%\*\* level in 1994") == pytest.approx(
        hor.loc[1994], abs=0.05)
    assert claimed(readme, r"2004 peak of ([\d.]+)%") == pytest.approx(
        hor.loc[2004], abs=0.05)


# --------------------------------------------------- finding 7: rent

def test_real_rent_and_ownership_cost_endpoints(readme, data):
    aff = data["aff"]
    r = aff.dropna(subset=["asking_rent_real2024"])
    first, last = int(r.index.min()), int(r.index.max())

    assert claimed(readme, r"about where it was in (\d{4})") == first
    assert claimed(readme, r"\(\$([\d,]+) → \$[\d,]+\)\. Renting") == pytest.approx(
        aff.loc[first, "monthly_ownership_cost_real2024"], abs=1)
    assert claimed(readme, r"\(\$[\d,]+ → \$([\d,]+)\)\. Renting") == pytest.approx(
        aff.loc[last, "monthly_ownership_cost_real2024"], abs=1)
    assert claimed(readme, r"rose \*\*\+(\d+)%\*\* over") == pytest.approx(
        (r.loc[last, "asking_rent_real2024"] / r.loc[first, "asking_rent_real2024"] - 1) * 100,
        abs=1)
    assert claimed(readme, r"same span \(\$([\d,]+) →") == pytest.approx(
        r.loc[first, "asking_rent_real2024"], abs=1)
    assert claimed(readme, r"same span \(\$[\d,]+ → \$([\d,]+)\)") == pytest.approx(
        r.loc[last, "asking_rent_real2024"], abs=1)


def test_owning_really_is_about_flat_in_real_terms(readme, data):
    """The claim the finding rests on. If a revision moves it, the wording has
    to change, not just the numbers."""
    aff = data["aff"]
    r = aff.dropna(subset=["asking_rent_real2024"])
    first, last = int(r.index.min()), int(r.index.max())
    change = (aff.loc[last, "monthly_ownership_cost_real2024"]
              / aff.loc[first, "monthly_ownership_cost_real2024"] - 1) * 100
    assert abs(change) < 5, f"owning moved {change:+.1f}% — 'about where it was' no longer holds"


def test_rent_burden_endpoints(readme, data):
    rti = data["aff"]["rent_to_income"].dropna()
    assert claimed(readme, r"takes \*\*(\d+)%\*\* of a 25") == pytest.approx(
        rti.iloc[-1] * 100, abs=1)
    assert claimed(readme, r"up from \*\*(\d+)%\*\* in \d{4}") == pytest.approx(
        rti.iloc[0] * 100, abs=1)


def test_own_to_rent_ratio_endpoints(readme, data):
    ratio = data["aff"]["own_to_rent_ratio"].dropna()
    first = int(data["aff"].dropna(subset=["asking_rent_real2024"]).index.min())
    assert claimed(readme, r"\((\d\.\d)× in \d{4}") == pytest.approx(
        ratio.loc[first], abs=0.05)
    assert claimed(readme, r"× in \d{4}, (\d\.\d)× now\)") == pytest.approx(
        ratio.iloc[-1], abs=0.05)
    assert (ratio > 1).all(), "the README says owning has *always* cost more per month"


# --------------------------------------------------- methodology notes

def test_figure_02_index_endpoints(readme, data):
    """The note explaining why figure 02 no longer indexes at 2015."""
    aff = data["aff"].loc[2005:].dropna(subset=["median_price", "monthly_piti"])
    last = aff.index.max()
    assert claimed(readme, r"price is up ~(\d+)%") == pytest.approx(
        pct_change(aff, "median_price", 2005, last), abs=1)
    assert claimed(readme, r"the payment on it ~(\d+)%") == pytest.approx(
        pct_change(aff, "monthly_piti", 2005, last), abs=1)


def test_nominal_price_growth_quoted_in_the_methodology_note(readme, data):
    aff = data["aff"]
    end = int(data["sens"]["end_year"].iloc[0])
    actual = (aff.loc[end, "median_price"] / aff.loc[2006, "median_price"] - 1) * 100
    assert claimed(readme, r"~(\d+)% nominal growth in the median price") == pytest.approx(
        actual, abs=1)
