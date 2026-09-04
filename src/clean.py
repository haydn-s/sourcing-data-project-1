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
    CENSUS_HVS_TAB11_FILE,
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


def parse_asking_rent() -> pd.DataFrame:
    """Parse Census HVS Table 11A into tidy quarterly median asking rent.

    Three quirks, none of them optional:

    **Two tables share one sheet.** 11A is asking *rent* (~$1,500/month) and
    11B, further down, is asking *sales price* (~$400,000). They have identical
    row structure, so a parser that just scans for quarter rows silently
    averages rents together with house prices. We bound the scan between the two
    title rows and fail if either is missing.

    **Revised year blocks.** Some years appear twice -- "1989" then "1989r1" --
    where Census reissued an estimate (the footnotes explain r1/r2/r3 as
    revisions for year-round units and the 1990 and 2000 censuses). We keep the
    revised figure. That is the same principle H-10 follows, even though the
    layouts differ: H-10 lists its revision first, this table lists it second.

    **An "Annual" row per block.** Census's own mean of the four quarters. We
    skip it and let build_annual_panel do the aggregation, so every series in
    the project is collapsed to the year by one rule rather than two.
    """
    path = RAW_PARTNER / CENSUS_HVS_TAB11_FILE
    if not path.exists():
        raise FileNotFoundError(f"{path} missing — run `python src/ingest.py` first")
    raw = pd.read_excel(path, sheet_name=0, header=None)

    titles = {}
    for i, cell in raw[0].items():
        text = str(cell).strip()
        for key in ("Table 11A", "Table 11B"):
            if text.startswith(key):
                titles.setdefault(key, i)
    if "Table 11A" not in titles:
        raise ValueError("HVS Table 11A title row not found — layout may have changed")
    # No 11B means the sheet changed shape; refuse rather than read past the end.
    if "Table 11B" not in titles:
        raise ValueError("HVS Table 11B title row not found — cannot bound Table 11A")

    block = raw.loc[titles["Table 11A"]:titles["Table 11B"] - 1]

    records, current_year, current_is_revision = {}, None, False
    for _, row in block.iterrows():
        label = str(row[0]).strip()

        # "1989" opens a block; "1989r1" opens a revised block for the same year.
        year_match = re.match(r"^(\d{4})(?:\.0)?(r\d)?$", label)
        if year_match:
            current_year = int(year_match.group(1))
            current_is_revision = year_match.group(2) is not None
            continue

        quarter = QUARTER_PREFIX.get(label[:3])
        if quarter is None or current_year is None:
            continue                      # "Annual…", blanks, footnotes
        value = pd.to_numeric(row[1], errors="coerce")
        if pd.isna(value):
            continue

        key = (current_year, quarter)
        # A revision supersedes the original; an original never overwrites one.
        if key in records and not current_is_revision:
            continue
        records[key] = {"year": current_year, "quarter": quarter,
                        "asking_rent": float(value), "is_revised": current_is_revision}

    df = pd.DataFrame(list(records.values()))
    if df.empty:
        raise ValueError("parsed zero rows from HVS Table 11A — layout may have changed")
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
    monthly: pd.DataFrame, hor: pd.DataFrame, inc_age: pd.DataFrame,
    rent: pd.DataFrame
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
    annual = annual.join(rent.groupby("year")[["asking_rent"]].mean(), how="left")

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

    rent = parse_asking_rent()
    rent.to_csv(PROCESSED / "asking_rent.csv", index=False)
    print(f"asking_rent.csv        {rent.shape[0]:>5} quarters "
          f"({rent['year'].min()} to {rent['year'].max()}, "
          f"{int(rent['is_revised'].sum())} revised)")

    inc_age = parse_income_by_age()
    inc_age.to_csv(PROCESSED / "income_by_age.csv")
    print(f"income_by_age.csv      {inc_age.shape[0]:>5} years x {inc_age.shape[1]} columns "
          f"({inc_age.index.min()} to {inc_age.index.max()})")

    annual = build_annual_panel(monthly, hor, inc_age, rent)
    annual.to_csv(PROCESSED / "annual_panel.csv")
    partial = annual.index[annual["is_partial_year"]].tolist()
    print(f"annual_panel.csv       {annual.shape[0]:>5} years x {annual.shape[1]} columns "
          f"({annual.index.min()} to {annual.index.max()})")
    print(f"  partial years (incomplete source data): {partial}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
