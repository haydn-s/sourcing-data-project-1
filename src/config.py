"""Shared configuration: paths, data sources, and modeling assumptions.

Every constant that shapes a result lives here so the analysis can be audited
and re-run under different assumptions without touching analysis code.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW_FRED = RAW / "fred"
RAW_PARTNER = RAW / "partner"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "figures"

# --- FRED series -----------------------------------------------------------
# id -> (human label, native frequency, units)
FRED_SERIES = {
    # Housing market
    "MORTGAGE30US": ("30-Year Fixed Mortgage Rate", "weekly", "percent"),
    "MSPUS":        ("Median Sales Price of Houses Sold", "quarterly", "usd"),
    "ASPUS":        ("Average Sales Price of Houses Sold", "quarterly", "usd"),
    "CSUSHPINSA":   ("Case-Shiller U.S. National Home Price Index", "monthly", "index"),
    "RHORUSQ156N":  ("Homeownership Rate (all ages)", "quarterly", "percent"),
    "G160651A027NBEA": ("Federal HUD Outlays", "annual", "usd_billions"),
    # Macro backdrop
    "PRIME":        ("Bank Prime Loan Rate", "irregular", "percent"),
    "DGS10":        ("10-Year Treasury Constant Maturity", "daily", "percent"),
    "DGS30":        ("30-Year Treasury Constant Maturity", "daily", "percent"),
    "GDP":          ("Gross Domestic Product", "quarterly", "usd_billions"),
    "CPIAUCSL":     ("CPI-U, All Items, SA", "monthly", "index"),
    "UNRATE":       ("Unemployment Rate", "monthly", "percent"),
    "POPTHM":       ("U.S. Population", "monthly", "thousands"),
    # Household balance sheet
    "MEHOINUSA672N": ("Real Median Household Income", "annual", "usd_2024"),
    "MEHOINUSA646N": ("Nominal Median Household Income", "annual", "usd_nominal"),
    "SLOAS":         ("Student Loans Owned and Securitized", "quarterly", "usd_millions"),
    "CCLACBW027SBOG": ("Credit Card Loans, All Commercial Banks", "weekly", "usd_billions"),
}

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

# --- Census Housing Vacancies and Homeownership Survey ---------------------
CENSUS_HVS_TAB19_URL = "https://www.census.gov/housing/hvs/data/histtab19.xlsx"
CENSUS_HVS_TAB19_FILE = "census_hvs_homeownership_by_age.xlsx"

# --- Census CPS ASEC Table H-10: median income by age of householder --------
# The all-ages median income series overstates what a first-time buyer earns.
# H-10 lets us run the affordability math on the 25-34 cohort directly.
CENSUS_H10_URL = (
    "https://www2.census.gov/programs-surveys/cps/tables/time-series/"
    "historical-income-households/h10ar.xlsx"
)
CENSUS_H10_FILE = "census_h10_income_by_age.xlsx"

# Age sections to extract from H-10, mapped to output column prefixes.
H10_AGE_SECTIONS = {
    "15 Years and Over": "all",
    "15 to 24 Years": "age_15_24",
    "25 to 34 Years": "age_25_34",
    "35 to 44 Years": "age_35_44",
}

# The cohort the story is about: prime first-time-homebuyer age.
YOUNG_COHORT = "age_25_34"

# --- Modeling assumptions --------------------------------------------------
# Conventional 30-year fixed purchase, the benchmark loan a first-time buyer
# is actually underwritten against.
DOWN_PAYMENT_PCT = 0.20      # share of purchase price paid up front
LOAN_TERM_YEARS = 30
FRONT_END_DTI = 0.28         # max housing payment as share of gross income
BACK_END_DTI = 0.36          # max total debt service as share of gross income
SAVINGS_RATE = 0.10          # share of gross income a saver can bank per year

# Property tax + homeowners insurance, as an annual share of home value.
# Folded in so "payment" means PITI, not just principal and interest.
TAX_INSURANCE_PCT = 0.0175

# Baseline year for the price-vs-rate counterfactual decomposition.
DECOMP_BASE_YEAR = 2021      # trough in mortgage rates, pre-tightening

ANALYSIS_START_YEAR = 1984   # first year real median household income exists
