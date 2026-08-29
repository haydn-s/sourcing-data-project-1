"""Clean raw sources into tidy analysis panels.

Produces three artifacts in data/processed/:
  fred_monthly.csv       every FRED series on a common month index
  homeownership_age.csv  Census HVS homeownership rate by age of householder
  income_by_age.csv      Census CPS H-10 median income by age of householder
  annual_panel.csv       the calendar-year panel the analysis is built on

Aggregation rule: all higher-frequency series are collapsed to the calendar
year by *mean*. For rates (mortgage, prime, unemployment) this is the average
prevailing level that year; for stocks (student debt, credit card debt) it is
the average outstanding balance. Using the mean rather than a year-end
snapshot keeps a single year from being defined by one volatile print.
"""

import re
import sys

import pandas as pd

from config import (
    ANALYSIS_START_YEAR,
    CENSUS_H10_FILE,
    CENSUS_HVS_TAB19_FILE,
    H10_AGE_SECTIONS,
    FRED_SERIES,
    PROCESSED,
    RAW_FRED,
    RAW_PARTNER,
)

QUARTER_PREFIX = {"1st": 1, "2nd": 2, "3rd": 3, "4th": 4}


def load_fred_series(series_id: str) -> pd.Series:
    """Read one FRED CSV into a float Series indexed by observation date.

    FRED encodes missing observations as '.', which must not be coerced to 0.
    """
    path = RAW_FRED / f"{series_id}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run `python src/ingest.py` first")
    df = pd.read_csv(path, parse_dates=["observation_date"])
    value_col = [c for c in df.columns if c != "observation_date"][0]
    s = pd.to_numeric(df[value_col], errors="coerce")
    s.index = df["observation_date"]
    s.name = series_id
    return s.dropna()


def build_monthly_frame() -> pd.DataFrame:
    """Put every FRED series on a shared monthly index.

    Sub-monthly series are averaged within the month; quarterly and annual
    series are forward-filled across the months they cover so that a monthly
    mortgage payment can be computed against the prevailing price level.
    """
    monthly = {}
    for series_id, (_label, freq, _units) in FRED_SERIES.items():
        s = load_fred_series(series_id)
        m = s.resample("MS").mean()
        if freq in {"quarterly", "annual", "irregular"}:
            m = m.ffill()
        monthly[series_id] = m
    df = pd.DataFrame(monthly).sort_index()
    df.index.name = "date"
    return df


def parse_homeownership_by_age() -> pd.DataFrame:
    """Parse Census HVS Table 19 into tidy quarterly rows.

    The workbook is a display table: a bare year row is followed by four
    quarter rows whose labels are padded with dot leaders ('1st…………'), plus
    header and footnote rows that carry no data. We therefore track the most
    recent year seen and accept only rows whose label starts with a quarter
    token and whose U.S. column parses as a number.
    """
    path = RAW_PARTNER / CENSUS_HVS_TAB19_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run `python src/ingest.py` first")
    raw = pd.read_excel(path, sheet_name=0, header=None)

    age_cols = {
        1: "hor_all",
        2: "hor_under_35",
        3: "hor_35_44",
        4: "hor_45_54",
        5: "hor_55_64",
        6: "hor_65_plus",
    }

    records, current_year = [], None
    for _, row in raw.iterrows():
        label = str(row[0]).strip()
        # A bare 4-digit year row opens a new year block.
        if label.isdigit() and len(label) == 4:
            current_year = int(label)
            continue
        quarter = QUARTER_PREFIX.get(label[:3])
        if quarter is None or current_year is None:
            continue
        values = {name: pd.to_numeric(row[i], errors="coerce")
                  for i, name in age_cols.items()}
        if pd.isna(values["hor_all"]):
            continue
        records.append({"year": current_year, "quarter": quarter, **values})

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("parsed zero rows from HVS Table 19 — layout may have changed")
    df["date"] = pd.PeriodIndex(
        [f"{y}Q{q}" for y, q in zip(df["year"], df["quarter"])], freq="Q"
    ).to_timestamp()
    return df.sort_values("date").reset_index(drop=True)


def parse_income_by_age() -> pd.DataFrame:
    """Parse Census CPS Table H-10 into median income by age of householder.

    The workbook stacks one block per age group: a section header row (e.g.
    "25 to 34 Years") followed by one row per year, newest first. Year labels
    carry footnote markers ("2020 (41)") and some years appear twice where a
    methodology change means two published estimates for the same year. Census
    lists the revised estimate first, so we keep the first occurrence.

    Returns columns <prefix>_median_current and <prefix>_median_2024 for each
    requested age section, indexed by year.
    """
    path = RAW_PARTNER / CENSUS_H10_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run `python src/ingest.py` first")
    raw = pd.read_excel(path, sheet_name=0, header=None)

    # Locate each requested age section by its header row.
    header_rows = {}
    for i, row in raw.iterrows():
        label = str(row[0]).strip()
        if label in H10_AGE_SECTIONS and pd.isna(row[1]):
            header_rows.setdefault(label, i)
    missing = set(H10_AGE_SECTIONS) - set(header_rows)
    if missing:
        raise ValueError(f"H-10 layout changed; sections not found: {sorted(missing)}")

    frames = []
    for label, start in header_rows.items():
        prefix = H10_AGE_SECTIONS[label]
        records = {}
        for _, row in raw.loc[start + 1:].iterrows():
            cell = str(row[0]).strip()
            m = re.match(r"^(\d{4})", cell)
            if not m:
                # Each section header is followed by two column-header rows
                # ("Age and year" / "Current dollars"), so only treat a
                # non-year label as the next section once data has started.
                if records and cell not in ("nan", ""):
                    break
                continue
            year = int(m.group(1))
            if year in records:      # duplicate year: keep first (revised) estimate
                continue
            records[year] = {
                f"{prefix}_median_current": pd.to_numeric(row[2], errors="coerce"),
                f"{prefix}_median_2024": pd.to_numeric(row[3], errors="coerce"),
            }
        frames.append(pd.DataFrame.from_dict(records, orient="index"))

    df = pd.concat(frames, axis=1).sort_index()
    df.index.name = "year"
    return df


def build_annual_panel(
    monthly: pd.DataFrame, hor: pd.DataFrame, inc_age: pd.DataFrame
) -> pd.DataFrame:
    """Collapse to calendar years and attach homeownership + coverage flags."""
    annual = monthly.resample("YS").mean()
    annual.index = annual.index.year
    annual.index.name = "year"

    # Months of observed data behind each year, so partial years are visible
    # downstream instead of silently reading as a complete year.
    obs = monthly["MORTGAGE30US"].notna().resample("YS").sum()
    obs.index = obs.index.year
    annual["months_observed"] = obs
    annual["is_partial_year"] = annual["months_observed"] < 12

    hor_annual = hor.groupby("year")[
        ["hor_all", "hor_under_35", "hor_35_44", "hor_45_54", "hor_55_64", "hor_65_plus"]
    ].mean()
    annual = annual.join(hor_annual, how="left")
    annual = annual.join(inc_age, how="left")

    return annual.loc[annual.index >= ANALYSIS_START_YEAR]


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)

    monthly = build_monthly_frame()
    monthly.to_csv(PROCESSED / "fred_monthly.csv")
    print(f"fred_monthly.csv       {monthly.shape[0]:>5} months x {monthly.shape[1]} series "
          f"({monthly.index.min():%Y-%m} to {monthly.index.max():%Y-%m})")

    hor = parse_homeownership_by_age()
    hor.to_csv(PROCESSED / "homeownership_age.csv", index=False)
    print(f"homeownership_age.csv  {hor.shape[0]:>5} quarters "
          f"({hor['year'].min()} to {hor['year'].max()})")

    inc_age = parse_income_by_age()
    inc_age.to_csv(PROCESSED / "income_by_age.csv")
    print(f"income_by_age.csv      {inc_age.shape[0]:>5} years x {inc_age.shape[1]} columns "
          f"({inc_age.index.min()} to {inc_age.index.max()})")

    annual = build_annual_panel(monthly, hor, inc_age)
    annual.to_csv(PROCESSED / "annual_panel.csv")
    partial = annual.index[annual["is_partial_year"]].tolist()
    print(f"annual_panel.csv       {annual.shape[0]:>5} years x {annual.shape[1]} columns "
          f"({annual.index.min()} to {annual.index.max()})")
    print(f"  partial years (incomplete source data): {partial}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
