"""The three Census workbook parsers.

These are the most fragile code in the project. Both workbooks are *display*
tables built for humans — dot-leader row labels, footnote markers glued to
years, header rows carrying no data, and the same year published twice where a
methodology changed. Table 11 goes further and puts two different
tables on one sheet. The parsers read them positionally, so a reflow at Census
breaks them silently and every downstream number moves.

The fixtures below rebuild those quirks in miniature rather than depending on
the real downloads, so the tests keep working offline and pin the *behaviour*
rather than today's file. The last test in each group asserts the parser fails
loudly when the layout it assumes is gone — a wrong number is far worse than a
crash here.
"""

import numpy as np
import pandas as pd
import pytest

import clean
from config import H10_AGE_SECTIONS


def _write(rows, path):
    """Write raw rows to a headerless sheet, the way Census ships them."""
    pd.DataFrame(rows).to_excel(path, header=False, index=False)
    return path


# ============================ HVS Table 19: homeownership by age ============

def _hvs_rows():
    """Table 19's real shape: preamble, a column-header row, then per-year
    blocks of four dot-leadered quarter rows separated by blanks."""
    n = np.nan
    return [
        ["Table with row headings in column A and column headings in rows 4-7.", n, n, n, n, n, n],
        ["Table 19. Homeownership Rates by Age of Householder: 1994 to Present", n, n, n, n, n, n],
        [n, n, n, n, n, n, n],
        ["Year and         Quarter", "U.S.", "Under 35 years", "35 to 44 years",
         "45 to 54 years", "55 to 64 years", "65 years and over"],
        [n, n, n, n, n, n, n],
        [1994, n, n, n, n, n, n],
        ["1st………….......", 63.8, 37.1, 64.4, 75.0, 79.3, 77.4],
        ["2nd……….........", 63.8, 36.8, 64.6, 75.2, 79.1, 77.2],
        ["3rd……….......", 64.1, 37.5, 64.3, 75.5, 79.4, 77.2],
        ["4th……..…......", 64.2, 38.0, 64.7, 74.9, 79.2, 77.7],
        [n, n, n, n, n, n, n],
        [1995, n, n, n, n, n, n],
        ["1st………….......", 64.2, 38.4, 65.2, 75.1, 79.4, 78.1],
        ["2nd……….........", 64.7, 38.6, 65.6, 75.3, 79.6, 78.4],
        # A quarter row Census has not published yet: label present, values blank.
        ["3rd……….......", n, n, n, n, n, n],
        [n, n, n, n, n, n, n],
        ["Note: A dash means the estimate is not available.", n, n, n, n, n, n],
    ]


@pytest.fixture
def hvs(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write(_hvs_rows(), tmp_path / clean.CENSUS_HVS_TAB19_FILE)
    return clean.parse_homeownership_by_age()


def test_hvs_reads_quarter_rows_despite_dot_leaders(hvs):
    """Labels arrive as '1st………….......' — the quarter is the first three chars."""
    assert list(hvs["quarter"]) == [1, 2, 3, 4, 1, 2]


def test_hvs_attaches_each_quarter_to_the_year_block_above_it(hvs):
    assert list(hvs["year"]) == [1994] * 4 + [1995] * 2


def test_hvs_maps_columns_to_the_right_age_groups(hvs):
    first = hvs.iloc[0]
    assert first["hor_all"] == 63.8
    assert first["hor_under_35"] == 37.1
    assert first["hor_35_44"] == 64.4
    assert first["hor_65_plus"] == 77.4


def test_hvs_drops_quarters_with_no_published_value(hvs):
    """1995 Q3 has a label but no data; it must not enter as a zero or a NaN row."""
    assert len(hvs) == 6
    assert not ((hvs["year"] == 1995) & (hvs["quarter"] == 3)).any()


def test_hvs_builds_quarter_start_dates(hvs):
    assert list(hvs["date"][:4]) == list(pd.to_datetime(
        ["1994-01-01", "1994-04-01", "1994-07-01", "1994-10-01"]))


def test_hvs_ignores_preamble_and_footnote_rows(hvs):
    assert hvs["year"].between(1994, 1995).all()


def test_hvs_raises_when_no_rows_parse(tmp_path, monkeypatch):
    """A reflow that removes the quarter labels must fail, not return empty."""
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write([["Table 19."], [1994], ["Q1", 63.8]], tmp_path / clean.CENSUS_HVS_TAB19_FILE)
    with pytest.raises(ValueError, match="parsed zero rows"):
        clean.parse_homeownership_by_age()


def test_hvs_raises_a_helpful_error_when_the_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    with pytest.raises(FileNotFoundError, match="ingest.py"):
        clean.parse_homeownership_by_age()


# ============================ CPS Table H-10: income by age =================

def _h10_section(label, years):
    """One age block: a header row, the two column-header rows, then the years
    newest-first. `years` is a list of (label, current$, 2024$)."""
    n = np.nan
    return [
        [label, n, n, n],
        ["Age and year", "Number (thousands)", "Median income", n],
        [n, n, "Current\ndollars", "2024\ndollars"],
        *[[y, 20_000, cur, real] for y, cur, real in years],
    ]


def _h10_rows():
    rows = []
    rows += _h10_section("15 Years and Over", [(2024, 83_730, 83_730), (2023, 80_610, 82_690)])
    rows += _h10_section("15 to 24 Years", [(2024, 51_000, 51_000), (2023, 49_000, 50_260)])
    rows += _h10_section("25 to 34 Years", [
        (2024, 90_100, 90_100),
        (2023, 85_780, 88_000),
        # Census publishes two estimates where methodology changed; the revised
        # one is listed first and is the one to keep.
        ("2017", 70_000, 88_500),
        ("2017", 66_666, 84_000),
        # Footnote markers are glued straight onto the year.
        ("2013 (38)", 60_000, 79_000),
        ("2013", 59_999, 78_000),
    ])
    rows += _h10_section("35 to 44 Years", [(2024, 105_000, 105_000)])
    rows += [[np.nan] * 4, ["Note: households as of March of the following year."]]
    return rows


@pytest.fixture
def h10(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write(_h10_rows(), tmp_path / clean.CENSUS_H10_FILE)
    return clean.parse_income_by_age()


def test_h10_extracts_every_requested_age_section(h10):
    for prefix in H10_AGE_SECTIONS.values():
        assert f"{prefix}_median_current" in h10.columns
        assert f"{prefix}_median_2024" in h10.columns


def test_h10_maps_current_and_constant_dollar_columns_separately(h10):
    """Column 2 is current dollars, column 3 is 2024 dollars. Swapping them
    would silently deflate the affordability ratio."""
    assert h10.loc[2023, "age_25_34_median_current"] == 85_780
    assert h10.loc[2023, "age_25_34_median_2024"] == 88_000


def test_h10_keeps_the_first_of_two_estimates_for_a_repeated_year(h10):
    """Census lists the revised estimate first."""
    assert h10.loc[2017, "age_25_34_median_current"] == 70_000


def test_h10_strips_footnote_markers_from_year_labels(h10):
    assert 2013 in h10.index
    assert h10.loc[2013, "age_25_34_median_current"] == 60_000


def test_h10_does_not_read_column_headers_as_data(h10):
    """'Age and year' and 'Current dollars' sit between the section header and
    the first year; reading either as a row would poison the series."""
    assert h10.index.min() == 2013
    assert h10.index.is_monotonic_increasing


def test_h10_stops_each_section_at_the_next_one(h10):
    """The 35-44 block only has 2024, so its earlier years must be blank rather
    than bleeding in from the section above."""
    assert h10.loc[2024, "age_35_44_median_current"] == 105_000
    assert pd.isna(h10.loc[2023, "age_35_44_median_current"])


def test_h10_raises_when_an_expected_section_is_gone(tmp_path, monkeypatch):
    """If Census renames a block, fail loudly rather than returning a frame with
    a silently missing cohort."""
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write(_h10_section("15 Years and Over", [(2024, 83_730, 83_730)]),
           tmp_path / clean.CENSUS_H10_FILE)
    with pytest.raises(ValueError, match="H-10 layout changed"):
        clean.parse_income_by_age()


def test_h10_raises_a_helpful_error_when_the_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    with pytest.raises(FileNotFoundError, match="ingest.py"):
        clean.parse_income_by_age()


# ============================ HVS Table 11A: asking rent ====================

def _rent_block(title, rows, price_scale=1):
    """One HVS Table 11 sub-table: title, units note, header, then year blocks."""
    n = np.nan
    out = [[title, n, n], ["(current dollars)", n, n], [n, n, n],
           ["Year and Quarter", "U.S.", "Northeast"]]
    for label, quarters in rows:
        out.append([label, n, n])
        for q, v in zip(("1st………….....", "2nd……….......", "3rd…………......",
                         "4th…………....."), quarters):
            out.append([q, None if v is None else v * price_scale, n])
        out.append([n, n, n])
        vals = [v for v in quarters if v is not None]
        out.append(["Annual………….", sum(vals) / len(vals) * price_scale, n])
        out.append([n, n, n])
    return out


def _tab11_rows():
    """Both sub-tables, because they share one sheet and look identical."""
    rent = _rent_block("Table 11A. Median Asking Rent for the U.S. and Regions", [
        (1988, (330, 344, 347, 350)),
        (1989, (345, 358, 355, 370)),        # original estimate
        ("1989r1", (331, 344, 345, 358)),    # revision, published after it
        (2026, (1531, 1579, None, None)),    # year still in progress
    ])
    price = _rent_block("Table 11B. Median Asking Sales Price for the U.S. and Regions", [
        (1988, (57000, 63500, 60300, 59100)),
        (1989, (61600, 64300, 57600, 57400)),
    ])
    return rent + price + [["Source: U.S. Census Bureau", np.nan, np.nan],
                           ["r1 Revised to include year-round units", np.nan, np.nan]]


@pytest.fixture
def rent(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write(_tab11_rows(), tmp_path / clean.CENSUS_HVS_TAB11_FILE)
    return clean.parse_asking_rent()


def test_rent_parser_stops_before_the_sales_price_table(rent):
    """11A and 11B share a sheet with identical row structure. Reading past the
    boundary would average $350 rents together with $57,000 sale prices."""
    assert rent["asking_rent"].max() < 5_000
    assert len(rent) == 10          # 1988 x4, 1989 x4 (revised), 2026 x2


def test_rent_parser_prefers_the_revised_estimate(rent):
    """1989 is published twice; "1989r1" supersedes it."""
    q1 = rent[(rent.year == 1989) & (rent.quarter == 1)].iloc[0]
    assert q1["asking_rent"] == 331      # the revision, not the original 345
    assert bool(q1["is_revised"]) is True


def test_rent_parser_keeps_one_row_per_quarter(rent):
    assert not rent.duplicated(["year", "quarter"]).any()


def test_rent_parser_skips_the_census_annual_row(rent):
    """Census publishes its own annual mean per block; letting it through would
    add a phantom fifth quarter."""
    assert set(rent["quarter"].unique()) <= {1, 2, 3, 4}
    assert (rent.groupby("year").size() <= 4).all()


def test_rent_parser_drops_quarters_not_yet_published(rent):
    assert len(rent[rent.year == 2026]) == 2


def test_rent_parser_refuses_a_sheet_it_cannot_bound(tmp_path, monkeypatch):
    """Without the 11B title there is no end marker, so the parser would run on
    into whatever follows. It must refuse instead."""
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    _write(_rent_block("Table 11A. Median Asking Rent", [(1988, (330, 344, 347, 350))]),
           tmp_path / clean.CENSUS_HVS_TAB11_FILE)
    with pytest.raises(ValueError, match="Table 11B"):
        clean.parse_asking_rent()


def test_rent_parser_raises_when_the_file_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_PARTNER", tmp_path)
    with pytest.raises(FileNotFoundError, match="ingest.py"):
        clean.parse_asking_rent()


# ============================ FRED CSV loading ==============================

def test_fred_missing_values_are_not_coerced_to_zero(tmp_path, monkeypatch):
    """FRED encodes a missing observation as '.', which read_csv would happily
    turn into 0.0 with the wrong converter — a zero mortgage rate would sail
    through every downstream formula."""
    monkeypatch.setattr(clean, "RAW_FRED", tmp_path)
    (tmp_path / "TEST.csv").write_text(
        "observation_date,TEST\n2020-01-01,1.5\n2020-02-01,.\n2020-03-01,2.5\n")
    s = clean.load_fred_series("TEST")
    assert list(s.values) == [1.5, 2.5]
    assert len(s) == 2


def test_fred_series_is_indexed_by_observation_date(tmp_path, monkeypatch):
    monkeypatch.setattr(clean, "RAW_FRED", tmp_path)
    (tmp_path / "TEST.csv").write_text("observation_date,TEST\n2020-01-01,1.5\n")
    s = clean.load_fred_series("TEST")
    assert s.index[0] == pd.Timestamp("2020-01-01")
    assert s.name == "TEST"
