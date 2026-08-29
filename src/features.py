"""Engineer the affordability features the story is built on.

The raw series answer "what did homes cost?". A buyer never faces a price --
they face a monthly payment and an underwriting test. These features translate
prices and rates into what a 25-34 year old household actually experiences:

  monthly_piti          the real monthly cost of the median home
  required_income       income needed to qualify at a 28% front-end DTI
  affordability_index   young-household income as a % of that requirement
  years_to_save_down    years to bank a 20% down payment
  price_effect /        counterfactual decomposition splitting the payment
  rate_effect           change into its price and interest-rate components

Writes data/processed/affordability.csv.
"""

import sys

import numpy as np
import pandas as pd

from config import (
    BACK_END_DTI,
    DECOMP_BASE_YEAR,
    DOWN_PAYMENT_PCT,
    FRONT_END_DTI,
    LOAN_TERM_YEARS,
    PROCESSED,
    SAVINGS_RATE,
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

    # --- inflation-adjusted views (2024 dollars) --------------------------
    # NOTE: deflated with CPI-U, whereas Census deflates its own real income
    # series with CPI-U-RS. The two differ slightly; see README limitations.
    cpi_base = df.loc[2024, "cpi"]
    for col in ["median_price", "monthly_piti", "required_income", "income_young",
                "down_payment"]:
        df[f"{col}_real2024"] = df[col] * cpi_base / df["cpi"]

    # --- homeownership outcomes ------------------------------------------
    df["hor_under_35"] = annual["hor_under_35"]
    df["hor_all"] = annual["hor_all"]
    df["hor_gap_under35"] = annual["hor_all"] - annual["hor_under_35"]

    # --- competing debt ---------------------------------------------------
    # Student debt is a stock in $M; population is in thousands.
    df["student_debt_per_capita"] = annual["SLOAS"] * 1e6 / (annual["POPTHM"] * 1e3)
    df["student_debt_pct_income"] = df["student_debt_per_capita"] / df["income_young"] * 100
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
