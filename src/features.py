"""Engineer the affordability features the story is built on.

The raw series answer "what did homes cost?". A buyer never faces a price --
they face a monthly payment and an underwriting test. These features translate
prices and rates into what a 25-34 year old household actually experiences:

  monthly_piti          the actual monthly cost of the median home (before inflation)
  required_income       income needed to qualify at a 28% front-end DTI
  affordability_index   young-household income as a % of that requirement
  years_to_save_down    years to bank a 20% down payment
  price_effect /        counterfactual decomposition splitting the payment
  rate_effect           change into its price and interest-rate components
  growth_pct /          home price growth in each Case-Shiller metro, nominal
  real_growth_pct       and inflation-adjusted, for the regional comparison

  real_mortgage_rate    the 30-year rate less that year's CPI inflation
  listings_index /      homes for sale and single-family starts, each as a
  starts_index          share of its 2017-2019 average, for the supply chart

Writes affordability.csv, payment_decomposition.csv,
decomposition_sensitivity.csv, metro_price_growth.csv and housing_supply.csv to
data/processed/.
"""

import sys

import numpy as np
import pandas as pd

from config import (
    BACK_END_DTI,
    DECOMP_BASE_YEAR,
    DECOMP_SENSITIVITY_BASE_YEARS,
    DOWN_PAYMENT_PCT,
    FRONT_END_DTI,
    INDEX_BASE_YEAR,
    LOAN_TERM_YEARS,
    MAINTENANCE_PCT,
    METRO_GROWTH_BASE_YEAR,
    METRO_HPI_SERIES,
    PROCESSED,
    REAL_DOLLAR_BASE_YEAR,
    SAVINGS_RATE,
    SHOCK_END_YEAR,
    SHOCK_START_YEAR,
    SUPPLY_BASELINE_YEARS,
    TAX_INSURANCE_PCT,
    YOUNG_COHORT,
)


def monthly_payment(price, annual_rate_pct, down_pct=DOWN_PAYMENT_PCT,
                    term_years=LOAN_TERM_YEARS):
    """Level-payment principal & interest on a fully amortizing fixed mortgage.

    Vectorized over price and rate. The zero-rate case (never seen in this
    data, but numerically singular) falls back to straight-line repayment.
    """
    price = np.asarray(price, dtype=float)
    annual_rate_pct = np.asarray(annual_rate_pct, dtype=float)

    loan = price * (1.0 - down_pct)
    r = annual_rate_pct / 100.0 / 12.0
    n = term_years * 12

    with np.errstate(invalid="ignore", divide="ignore"):
        growth = (1.0 + r) ** n
        pi = loan * r * growth / (growth - 1.0)
    return np.where(r == 0, loan / n, pi)


def piti(price, annual_rate_pct, tax_ins_pct=TAX_INSURANCE_PCT, **kw):
    """Total monthly housing cost: P&I plus taxes and insurance escrow."""
    return monthly_payment(price, annual_rate_pct, **kw) + price * tax_ins_pct / 12.0


def build_affordability(annual: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(index=annual.index)

    price_col, rate_col = "MSPUS", "MORTGAGE30US"
    income_col = f"{YOUNG_COHORT}_median_current"

    df["is_partial_year"] = annual["is_partial_year"]
    df["months_observed"] = annual["months_observed"]

    df["median_price"] = annual[price_col]
    df["mortgage_rate"] = annual[rate_col]
    df["income_young"] = annual[income_col]
    df["income_all_ages"] = annual["all_median_current"]
    df["cpi"] = annual["CPIAUCSL"]
    df["cpi_inflation"] = annual["cpi_inflation"]
    # Ex post: the nominal rate less the inflation that actually happened that
    # year, not what borrowers expected. Negative means prices rose faster than
    # the loan charged, so the real burden of the debt shrank.
    df["real_mortgage_rate"] = df["mortgage_rate"] - df["cpi_inflation"]

    # --- what the buyer actually pays ------------------------------------
    df["monthly_pi"] = monthly_payment(df["median_price"], df["mortgage_rate"])
    df["monthly_piti"] = piti(df["median_price"], df["mortgage_rate"])
    df["annual_housing_cost"] = df["monthly_piti"] * 12

    # --- the underwriting test -------------------------------------------
    # Lenders cap housing cost at ~28% of gross income, so invert that to get
    # the income a bank would require for the median home.
    df["required_income"] = df["annual_housing_cost"] / FRONT_END_DTI

    # 100 = the median young household earns exactly enough to qualify.
    df["affordability_index"] = df["income_young"] / df["required_income"] * 100
    df["affordability_index_all_ages"] = (
        df["income_all_ages"] / df["required_income"] * 100
    )
    df["income_shortfall"] = df["required_income"] - df["income_young"]

    # --- burden ratios ----------------------------------------------------
    df["price_to_income"] = df["median_price"] / df["income_young"]
    df["payment_to_income"] = df["annual_housing_cost"] / df["income_young"]

    # --- the down payment hurdle -----------------------------------------
    df["down_payment"] = df["median_price"] * DOWN_PAYMENT_PCT
    df["years_to_save_down"] = df["down_payment"] / (df["income_young"] * SAVINGS_RATE)

    # --- renting, the alternative the audience is actually choosing from ---
    # Census HVS Table 11A: median asking rent on *vacant* units, i.e. what a
    # mover faces. That is the right series for someone deciding whether to buy,
    # since they are by definition moving -- but it is not what a sitting tenant
    # pays, and the units on the market skew smaller than the median home. So
    # the level of this comparison is soft; its trend is what carries weight.
    df["asking_rent"] = annual["asking_rent"]
    df["annual_rent"] = df["asking_rent"] * 12

    # Owning costs more than the mortgage. TAX_INSURANCE_PCT already covers tax
    # and insurance; maintenance is the remaining cost a renter never sees.
    df["maintenance_monthly"] = df["median_price"] * MAINTENANCE_PCT / 12
    df["monthly_ownership_cost"] = df["monthly_piti"] + df["maintenance_monthly"]

    # NOTE: cash cost only. It credits the owner nothing for equity, and charges
    # the renter nothing for having none. Read it as the monthly hurdle, not as
    # a verdict on which is the better deal.
    df["own_minus_rent"] = df["monthly_ownership_cost"] - df["asking_rent"]
    df["own_to_rent_ratio"] = df["monthly_ownership_cost"] / df["asking_rent"]
    df["rent_to_income"] = df["annual_rent"] / df["income_young"]

    # What is left of a young household's income after rent -- the pool a down
    # payment has to be saved out of. This is the link between the two halves of
    # the story: rent is the mechanism that makes the down payment unreachable.
    df["income_after_rent"] = df["income_young"] - df["annual_rent"]

    # --- inflation-adjusted views (2024 dollars) --------------------------
    # NOTE: deflated with CPI-U, whereas Census deflates its own real income
    # series with CPI-U-RS. The two differ slightly; see README limitations.
    cpi_base = df.loc[REAL_DOLLAR_BASE_YEAR, "cpi"]
    for col in ["median_price", "monthly_piti", "required_income", "income_young",
                "income_all_ages", "down_payment", "asking_rent", "monthly_ownership_cost",
                "income_after_rent"]:
        df[f"{col}_real2024"] = df[col] * cpi_base / df["cpi"]

    # --- homeownership outcomes ------------------------------------------
    df["hor_under_35"] = annual["hor_under_35"]
    df["hor_all"] = annual["hor_all"]
    df["hor_gap_under35"] = annual["hor_all"] - annual["hor_under_35"]

    # --- competing debt ---------------------------------------------------
    # Both are stocks carried on FRED in different units, and population is in
    # thousands: SLOAS is $M, CCLACBW027SBOG is $B.
    df["student_debt_per_capita"] = annual["SLOAS"] * 1e6 / (annual["POPTHM"] * 1e3)
    df["credit_card_debt_per_capita"] = (
        annual["CCLACBW027SBOG"] * 1e9 / (annual["POPTHM"] * 1e3)
    )
    # Student debt alone understates the claim on a young buyer's income; the
    # back-end DTI test a lender applies counts revolving balances too.
    df["consumer_debt_per_capita"] = (
        df["student_debt_per_capita"] + df["credit_card_debt_per_capita"]
    )
    df["student_debt_pct_income"] = df["student_debt_per_capita"] / df["income_young"] * 100
    df["consumer_debt_pct_income"] = df["consumer_debt_per_capita"] / df["income_young"] * 100
    # Room left for a mortgage after other debt service, as a share of income.
    df["dti_headroom"] = BACK_END_DTI - df["payment_to_income"]

    return df


def decompose_payment_change(df: pd.DataFrame,
                             base_year: int = DECOMP_BASE_YEAR) -> pd.DataFrame:
    """Split the change in monthly payment since `base_year` into price vs rate.

    Two-factor counterfactual decomposition. Holding one input at its base-year
    level isolates the other's contribution; because payment is multiplicative
    in price and non-linear in rate, the residual interaction term is reported
    explicitly rather than being silently folded into either factor.
    """
    if base_year not in df.index:
        raise ValueError(f"base year {base_year} not in panel")

    p_b = df.loc[base_year, "median_price"]
    r_b = df.loc[base_year, "mortgage_rate"]
    base_payment = float(piti(p_b, r_b))

    out = pd.DataFrame(index=df.index)
    out["is_partial_year"] = df["is_partial_year"]
    out["base_payment"] = base_payment
    out["actual_payment"] = df["monthly_piti"]

    # Price moves, rate frozen at base -> pure price contribution.
    out["payment_price_only"] = piti(df["median_price"], r_b)
    # Rate moves, price frozen at base -> pure rate contribution.
    out["payment_rate_only"] = piti(p_b, df["mortgage_rate"])

    out["total_change"] = out["actual_payment"] - base_payment
    out["price_effect"] = out["payment_price_only"] - base_payment
    out["rate_effect"] = out["payment_rate_only"] - base_payment
    out["interaction"] = out["total_change"] - out["price_effect"] - out["rate_effect"]

    for col in ["price_effect", "rate_effect", "interaction"]:
        out[f"{col}_share"] = out[col] / out["total_change"] * 100

    return out


def latest_complete_year(df: pd.DataFrame) -> int:
    """Most recent year built from a full 12 months of price and rate data."""
    complete = ~df["is_partial_year"].fillna(False).astype(bool)
    usable = df.loc[complete, ["median_price", "mortgage_rate"]].dropna()
    if usable.empty:
        raise ValueError("no complete year with both price and rate")
    return int(usable.index.max())


def _split(price_b, rate_b, price_e, rate_e):
    """Two-factor counterfactual split of one payment change.

    Returns (base_payment, total, price_effect, rate_effect, interaction).
    Holding one input at its base level isolates the other's contribution;
    because piti is linear in price but non-linear in rate, the two do not sum
    to the total and the residual is returned rather than absorbed.
    """
    base = float(piti(price_b, rate_b))
    total = float(piti(price_e, rate_e)) - base
    price_effect = float(piti(price_e, rate_b)) - base
    rate_effect = float(piti(price_b, rate_e)) - base
    return base, total, price_effect, rate_effect, total - price_effect - rate_effect


def decompose_sensitivity(df: pd.DataFrame,
                          base_years=DECOMP_SENSITIVITY_BASE_YEARS,
                          end_year: int | None = None) -> pd.DataFrame:
    """Re-run the price-vs-rate split from every anchor across a 20-year window.

    Two things move the answer, and this reports both.

    **The anchor.** The headline decomposition starts at 2021, the all-time low
    in mortgage rates -- the anchor most favourable to a "rates did it" reading.

    **The denomination.** Over two years nominal and real agree. Over twenty
    they do not: CPI rose ~60% from 2006 to 2025 against ~70% nominal growth in
    the median price, so a nominal split hands prices the credit for inflation.
    If prices, incomes and rents all doubled with inflation and rates held flat,
    the nominal split would report "prices did 100% of it" while affordability
    was untouched. The real columns deflate the base-year price to
    REAL_DOLLAR_BASE_YEAR dollars so the price effect is real appreciation only.

    Real terms is the correct lens for a long horizon; the nominal columns are
    kept so the divergence itself can be shown rather than quietly resolved.

    `end_year` defaults to the latest year with a full 12 months of data, so a
    partial final year never sets the headline.
    """
    if end_year is None:
        end_year = latest_complete_year(df)
    if end_year not in df.index:
        raise ValueError(f"end year {end_year} not in panel")

    p_e, r_e = df.loc[end_year, "median_price"], df.loc[end_year, "mortgage_rate"]
    cpi_base = df.loc[REAL_DOLLAR_BASE_YEAR, "cpi"]
    p_e_real = p_e * cpi_base / df.loc[end_year, "cpi"]

    rows = []
    for base_year in base_years:
        if base_year not in df.index:
            raise ValueError(f"base year {base_year} not in panel")
        p_b, r_b = df.loc[base_year, "median_price"], df.loc[base_year, "mortgage_rate"]
        p_b_real = p_b * cpi_base / df.loc[base_year, "cpi"]

        base, total, price_eff, rate_eff, inter = _split(p_b, r_b, p_e, r_e)
        rbase, rtotal, rprice, rrate, rinter = _split(p_b_real, r_b, p_e_real, r_e)

        rows.append({
            "base_year": base_year, "end_year": end_year,
            "base_price": p_b, "base_rate": r_b,
            "base_payment": base, "total_change": total,
            "price_effect": price_eff, "rate_effect": rate_eff,
            "interaction": inter,
            "base_price_real": p_b_real, "base_payment_real": rbase,
            "real_total_change": rtotal, "real_price_effect": rprice,
            "real_rate_effect": rrate, "real_interaction": rinter,
        })

    out = pd.DataFrame(rows).set_index("base_year")

    for prefix in ("", "real_"):
        total = out[f"{prefix}total_change"]
        for part in ("price_effect", "rate_effect", "interaction"):
            out[f"{prefix}{part}_share"] = out[f"{prefix}{part}"] / total * 100
        price, rate = out[f"{prefix}price_effect"], out[f"{prefix}rate_effect"]
        out[f"{prefix}dominant_factor"] = np.where(price > rate, "price", "rate")
        # A share is only readable while both effects push the same way. Once
        # one turns negative the pair still sums to the total but the
        # percentages run past 100 and below zero, so flag rather than print.
        out[f"{prefix}shares_readable"] = (
            (np.sign(price) == np.sign(rate)) & (total != 0))

    return out


def complete_metro_years(metros: pd.DataFrame) -> list[int]:
    """Years in which every metro has all 12 monthly index values."""
    counts = metros.notna().groupby(metros.index.year).sum()
    return [int(y) for y in counts.index[(counts == 12).all(axis=1)]]


def metro_price_growth(metros: pd.DataFrame, cpi: pd.Series,
                       base_year: int = METRO_GROWTH_BASE_YEAR,
                       end_year: int | None = None) -> pd.DataFrame:
    """Home price growth in each Case-Shiller metro between two calendar years.

    `metros` is the monthly frame from clean.build_metro_frame; `cpi` is annual
    CPI-U indexed by year. Each year is the mean of its 12 monthly values, the
    same collapse rule as the national panel, which also cancels the
    seasonality in these not-seasonally-adjusted indices. Both years must be
    complete for every metro -- a metro compared on fewer months than the
    others would be ranked on a different window.

    Nominal growth is the change a seller saw. Real growth deflates it by
    national CPI, so a metro that only kept pace with inflation reads as zero.
    One deflator applies to every metro, so it shifts the bars without
    reordering them. Rows are sorted fastest to slowest in real terms.
    """
    complete = complete_metro_years(metros)
    if end_year is None:
        if not complete:
            raise ValueError("no year with all 12 months for every metro")
        end_year = max(complete)
    for label, year in (("base", base_year), ("end", end_year)):
        if year not in complete:
            raise ValueError(f"{label} year {year} lacks 12 months for every metro")
        if pd.isna(cpi.get(year)):
            raise ValueError(f"{label} year {year} has no CPI to deflate by")

    annual = metros.groupby(metros.index.year).mean()
    start, end = annual.loc[base_year], annual.loc[end_year]
    growth = (end / start - 1) * 100
    inflation = cpi[end_year] / cpi[base_year]

    out = pd.DataFrame({
        "metro": [METRO_HPI_SERIES.get(sid, sid) for sid in annual.columns],
        "base_year": base_year,
        "end_year": end_year,
        "index_base": start,
        "index_end": end,
        "growth_pct": growth,
        "real_growth_pct": ((end / start) / inflation - 1) * 100,
    }, index=annual.columns)
    out.index.name = "series_id"
    out = out.sort_values("real_growth_pct", ascending=False)
    out["rank"] = range(1, len(out) + 1)
    return out


def real_change(df: pd.DataFrame, col: str, start: int, end: int) -> float:
    """Percent change in `col` from start to end after removing CPI inflation."""
    nominal = df.loc[end, col] / df.loc[start, col]
    return (nominal / (df.loc[end, "cpi"] / df.loc[start, "cpi"]) - 1) * 100


def years_to_save_moving(price, income, price_growth, income_growth, savings_return,
                         savings_rate=SAVINGS_RATE, down_pct=DOWN_PAYMENT_PCT,
                         max_years=100) -> float:
    """Years to save a down payment when the price keeps moving while you save.

    `years_to_save_down` divides today's down payment by today's savings, as if
    the price stood still. Here the price and income grow each year and the
    savings earn `savings_return`. With all three at zero this reduces to the
    static measure exactly, fractional final year included.
    """
    saved = 0.0
    for year in range(1, max_years + 1):
        grown = saved * (1 + savings_return)
        contribution = income * savings_rate
        target = price * down_pct
        if grown + contribution >= target:
            return year - 1 + max(0.0, (target - grown) / contribution)
        saved = grown + contribution
        price *= 1 + price_growth
        income *= 1 + income_growth
    return float("inf")


def inflation_summary(aff: pd.DataFrame, panel: pd.DataFrame) -> dict:
    """How the page's claims read once inflation is taken out.

    `aff` is affordability.csv and `panel` the annual panel (for CPI less
    shelter). Price and payment changes are deflated by CPI-U; the rent check is
    repeated with CPI less shelter, since shelter is about a third of CPI and
    deflating housing by it partly deflates housing by itself.
    """
    full = aff[~aff["is_partial_year"].fillna(False).astype(bool)]
    last = latest_complete_year(aff)
    last_income = int(full["income_young"].dropna().index.max())
    s0, s1 = SHOCK_START_YEAR, SHOCK_END_YEAR
    rate = full["real_mortgage_rate"].dropna()

    first = int(full["income_young"].dropna().index.min())
    span = last_income - first
    growth = lambda col: (full.loc[last_income, col] / full.loc[first, col]) ** (1 / span) - 1
    price_g, income_g, cpi_g = growth("median_price"), growth("income_young"), growth("cpi")
    start = full.loc[last_income]

    rent = full["asking_rent"].dropna()
    r0 = int(rent.index.min())
    less_shelter = panel["CUSR0000SA0L2"]
    rent_real = lambda deflator: ((rent[last] / rent[r0]) / (deflator[last] / deflator[r0]) - 1) * 100

    return {
        "latest_year": last,
        "latest_income_year": last_income,
        "price_real_shock": real_change(full, "median_price", s0, s1),
        "payment_real_shock": real_change(full, "monthly_piti", s0, s1),
        "price_nominal_shock": (full.loc[s1, "median_price"] / full.loc[s0, "median_price"] - 1) * 100,
        "payment_nominal_shock": (full.loc[s1, "monthly_piti"] / full.loc[s0, "monthly_piti"] - 1) * 100,
        "price_real_since_shock": real_change(full, "median_price", s0, last),
        "payment_real_since_shock": real_change(full, "monthly_piti", s0, last),
        "price_real_long": real_change(full, "median_price", INDEX_BASE_YEAR, last),
        "payment_real_long": real_change(full, "monthly_piti", INDEX_BASE_YEAR, last),
        "income_young_real_since_shock": real_change(full, "income_young", s0, last_income),
        "required_income_real_since_shock": real_change(full, "required_income", s0, last_income),
        "real_rate_low_year": int(rate.loc[s0:].idxmin()),
        "real_rate_low": rate.loc[s0:].min(),
        "real_rate_latest": rate[last],
        "real_rate_rise": rate[last] - rate.loc[s0:].min(),
        "payment_erosion_since_shock": (full.loc[s0, "cpi"] / full.loc[last_income, "cpi"] - 1) * 100,
        "growth_window": (first, last_income),
        "price_growth": price_g * 100,
        "income_growth": income_g * 100,
        "cpi_growth": cpi_g * 100,
        "save_years_static": start["years_to_save_down"],
        "save_years_savings_keep_up": years_to_save_moving(
            start["median_price"], start["income_young"], price_g, income_g, cpi_g),
        "save_years_savings_earn_nothing": years_to_save_moving(
            start["median_price"], start["income_young"], price_g, income_g, 0.0),
        "rent_window": (r0, last),
        "rent_real_cpi": rent_real(full["cpi"]),
        "rent_real_less_shelter": rent_real(less_shelter),
    }


def complete_year_means(series: pd.Series) -> pd.Series:
    """Calendar-year means of a monthly series, over years with all 12 months.

    Averaging a year keeps one volatile month from defining it, and dropping
    short years keeps a year-to-date average from reading as a full year.
    """
    s = series.dropna()
    counts = s.groupby(s.index.year).count()
    return s.groupby(s.index.year).mean()[counts == 12]


def housing_supply(monthly: pd.DataFrame,
                   baseline=SUPPLY_BASELINE_YEARS) -> pd.DataFrame:
    """Homes for sale against homes being built, each indexed to its own baseline.

    The two measures share no unit -- a count of listings, and starts at an
    annual rate -- so neither can sit on the other's axis. Indexing each to its
    2017-2019 average (= 100) asks the same question of both: how far from
    normal was it? Calendar-year means over complete years only, from the first
    year both series cover.
    """
    b0, b1 = baseline
    listings = complete_year_means(monthly["ACTLISCOUUS"])
    starts = complete_year_means(monthly["HOUST1F"])
    out = pd.DataFrame({"active_listings": listings,
                        "single_family_starts": starts}).dropna()
    # DatetimeIndex.year is int32; a year read back from CSV is int64.
    out.index = out.index.astype("int64")
    out.index.name = "year"
    for raw, index in (("active_listings", "listings_index"),
                       ("single_family_starts", "starts_index")):
        out[index] = out[raw] / out.loc[b0:b1, raw].mean() * 100
    out["baseline_start"], out["baseline_end"] = b0, b1
    return out


def supply_summary(monthly: pd.DataFrame,
                   shock=(SHOCK_START_YEAR, SHOCK_END_YEAR),
                   baseline=SUPPLY_BASELINE_YEARS) -> dict:
    """What housing supply did during the rate shock, from the monthly panel.

    The page claims homes for sale were scarce while builders responded. This
    is the arithmetic behind each half: listings against their pre-pandemic
    level and the vacancy rate against its whole history (the existing stock),
    then single-family starts and the months' supply of new homes (the
    construction response).
    """
    listings = complete_year_means(monthly["ACTLISCOUUS"])
    vacancy = complete_year_means(monthly["RHVRUSQ156N"])
    starts = complete_year_means(monthly["HOUST1F"])
    new_supply = complete_year_means(monthly["MSACSR"])
    (s0, s1), (b0, b1) = shock, baseline

    starts_peak_year = int(starts.loc[s0:s1].idxmax())
    starts_peak = starts[starts_peak_year]
    earlier_higher = starts.loc[:starts_peak_year - 1]
    earlier_higher = earlier_higher[earlier_higher > starts_peak]
    return {
        "listings_shock_mean": listings.loc[s0:s1].mean(),
        "listings_baseline_mean": listings.loc[b0:b1].mean(),
        "listings_ratio": listings.loc[s0:s1].mean() / listings.loc[b0:b1].mean(),
        "vacancy_first_year": int(vacancy.index.min()),
        "vacancy_low_year": int(vacancy.idxmin()),
        "vacancy_low": vacancy.min(),
        "starts_peak_year": starts_peak_year,
        "starts_peak": starts_peak,
        "starts_last_higher_year": int(earlier_higher.index.max()) if len(earlier_higher) else None,
        "starts_highest_since_peak": starts.loc[starts_peak_year + 1:].max(),
        "new_home_supply_start": new_supply[s0],
        "new_home_supply_end": new_supply[s1],
    }


def main() -> int:
    panel_path = PROCESSED / "annual_panel.csv"
    if not panel_path.exists():
        raise FileNotFoundError("run `python src/clean.py` first")
    annual = pd.read_csv(panel_path, index_col="year")

    df = build_affordability(annual)
    df.to_csv(PROCESSED / "affordability.csv")
    print(f"affordability.csv      {df.shape[0]:>5} years x {df.shape[1]} features")

    decomp = decompose_payment_change(df)
    decomp.to_csv(PROCESSED / "payment_decomposition.csv")
    print(f"payment_decomposition.csv {decomp.shape[0]:>2} years "
          f"(base year {DECOMP_BASE_YEAR})")

    sens = decompose_sensitivity(df)
    sens.to_csv(PROCESSED / "decomposition_sensitivity.csv")
    end_year = int(sens["end_year"].iloc[0])
    print(f"decomposition_sensitivity.csv {sens.shape[0]:>2} base years "
          f"({sens.index.min()}-{sens.index.max()}) -> {end_year}")
    for label, col in (("nominal", "dominant_factor"), ("real", "real_dominant_factor")):
        blames = sens[col]
        flip = blames.ne(blames.shift()).cumsum().max() > 1
        print(f"  {label:<8} blames prices in {(blames == 'price').sum():>2}/{len(blames)} "
              f"anchors{'  (dominant factor FLIPS)' if flip else ''}")

    monthly = pd.read_csv(PROCESSED / "fred_monthly.csv", index_col="date", parse_dates=["date"])
    supply = housing_supply(monthly)
    supply.to_csv(PROCESSED / "housing_supply.csv")
    print(f"housing_supply.csv     {supply.shape[0]:>5} years ({supply.index.min()}-{supply.index.max()}), "
          f"indexed to {SUPPLY_BASELINE_YEARS[0]}-{SUPPLY_BASELINE_YEARS[1]}")

    metro_path = PROCESSED / "metro_hpi_monthly.csv"
    if not metro_path.exists():
        raise FileNotFoundError("run `python src/clean.py` first")
    metros = pd.read_csv(metro_path, index_col="date", parse_dates=["date"])
    growth = metro_price_growth(metros, annual["CPIAUCSL"])
    growth.to_csv(PROCESSED / "metro_price_growth.csv")
    top, bottom = growth.iloc[0], growth.iloc[-1]
    print(f"metro_price_growth.csv {growth.shape[0]:>5} metros "
          f"({int(top['base_year'])} -> {int(top['end_year'])}, real): "
          f"{top['metro']} {top['real_growth_pct']:+.1f}% ... "
          f"{bottom['metro']} {bottom['real_growth_pct']:+.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
