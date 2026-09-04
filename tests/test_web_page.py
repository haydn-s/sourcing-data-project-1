"""Claims the story page makes about the project, checked against the project.

`web/index.html` asserts things in prose — how many series are downloaded, which
Census tables are parsed, how many figures the story runs to — and none of it is
generated, so all of it can go stale the moment the pipeline grows. It did: the
rent analysis added an eighteenth FRED series and a third Census table while the
page still said "Seventeen series" and named two tables.

This is the page's counterpart to test_readme_claims.py. The page is the input;
the code and the generated outputs are the truth.
"""

import json
import re
from pathlib import Path

import pytest

from config import FRED_SERIES

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
FIGURES = ROOT / "figures"

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


@pytest.fixture(scope="module")
def page():
    return (WEB / "index.html").read_text()


@pytest.fixture(scope="module")
def flat(page):
    """Whitespace collapsed, so a claim that wraps still matches one regex."""
    return re.sub(r"\s+", " ", page)


def word_or_digit(token):
    token = token.strip().lower()
    return NUMBER_WORDS.get(token, None) if not token.isdigit() else int(token)


# ------------------------------------------------------------------- sourcing

def test_stated_fred_series_count_matches_config(flat):
    m = re.search(r"([A-Za-z]+|\d+) series retrieved programmatically", flat)
    assert m, "the page no longer states how many FRED series it downloads"
    assert word_or_digit(m.group(1)) == len(FRED_SERIES)


def test_every_census_table_the_pipeline_parses_is_credited(flat):
    """clean.py parses three workbooks; the page must name all three.

    Matched with a trailing boundary rather than `in`: a plain substring test
    passes on "Table 11A-REMOVED", and on "Table 1" inside "Table 19".
    """
    for table in ("Table 19", "Table 11A", "Table H-10"):
        assert re.search(rf"{re.escape(table)}(?![\w-])", flat), \
            f"{table} is parsed but not credited on the page"


def test_citation_block_lists_both_hvs_tables(flat):
    assert re.search(r"Housing Vacancies and Homeownership.{0,40}Tables 19 and 11A",
                     flat), "the HVS citation does not name both tables"


# -------------------------------------------------------------------- figures

def test_stated_figure_count_matches_the_figures_shown(flat, page):
    m = re.search(r"The story, in ([a-z]+|\d+) figures", flat)
    assert m, "the story section no longer states a figure count"
    shown = len(re.findall(r'<img src="\.\./figures/', page))
    assert word_or_digit(m.group(1)) == shown


def test_every_generated_figure_appears_on_the_page(page):
    """Catches the failure this file was written after: a new figure lands in
    figures/ and nothing on the page ever references it."""
    on_disk = {p.name for p in FIGURES.glob("*.png")}
    referenced = set(re.findall(r'<img src="\.\./figures/([^"]+)"', page))
    assert on_disk - referenced == set(), \
        f"generated but never shown: {sorted(on_disk - referenced)}"


def test_no_figure_reference_is_broken(page):
    referenced = set(re.findall(r'<img src="\.\./figures/([^"]+)"', page))
    missing = {f for f in referenced if not (FIGURES / f).exists()}
    assert not missing, f"referenced but absent from figures/: {sorted(missing)}"


def test_every_figure_carries_real_alt_text(page):
    """Each figure is the load-bearing content of its beat; an empty alt makes
    the beat meaningless to a screen reader."""
    for tag in re.findall(r"<img [^>]*>", page):
        alt = re.search(r'alt="([^"]*)"', tag)
        assert alt and len(alt.group(1)) > 40, f"weak or missing alt text: {tag[:90]}"


def test_beats_are_numbered_consecutively_from_one(page):
    nums = [int(n) for n in re.findall(r'<span class="beat-num">(\d+)</span>', page)]
    assert nums == list(range(1, len(nums) + 1)), f"beat numbering is {nums}"


# ------------------------------------------------------------------ repository

REPO_RE = r"https://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?(?=[\s\"<)])"


def test_page_links_to_the_repository(page):
    """The repo is the deliverable this page summarises; a reader who wants to
    reproduce anything needs to be able to reach it."""
    assert re.search(r'href="https://github\.com/[\w.-]+/[\w.-]+"', page), \
        "no link to the GitHub repository on the page"


def test_page_and_readme_agree_on_the_repository(page):
    """Both name the repo — in a clone command here and there. If one moves and
    the other doesn't, a reader follows a dead link."""
    on_page = set(re.findall(REPO_RE, page))
    in_readme = set(re.findall(REPO_RE, (ROOT / "README.md").read_text()))
    # The README also credits the partner's original sourcing repo, which is a
    # different project and correctly absent from the page.
    shared = on_page & in_readme
    assert shared, f"page names {sorted(on_page)}, README names {sorted(in_readme)}"
    assert len(on_page) == 1, f"page points at more than one repo: {sorted(on_page)}"


def test_clone_command_uses_the_same_repo_as_the_link(page):
    linked = set(re.findall(r'href="https://github\.com/([\w.-]+/[\w.-]+)"', page))
    cloned = set(re.findall(r"git clone https://github\.com/([\w.-]+/[\w.-]+?)\.git", page))
    assert cloned, "the reproduce block has no clone command"
    assert cloned == linked, f"clone command {cloned} does not match the link {linked}"


# ----------------------------------------------------------------------- hero

@pytest.mark.requires_data
def test_hero_rent_figure_matches_the_data(flat):
    """The third stat tile carries the one long-run claim that survives a change
    of base year, so it had better match the series it quotes."""
    import pandas as pd
    csv = ROOT / "data" / "processed" / "affordability.csv"
    if not csv.exists():
        pytest.skip("run `python src/run_all.py` first")
    rent = pd.read_csv(csv, index_col="year")["asking_rent_real2024"].dropna()
    growth = (rent.iloc[-1] / rent.iloc[0] - 1) * 100

    m = re.search(r'stat-value">\+(\d+)%</span>\s*<span class="stat-label">Real cost of renting',
                  flat)
    assert m, "the hero no longer states the real rent figure"
    assert int(m.group(1)) == pytest.approx(growth, abs=1)


def test_any_flatness_claim_in_the_hero_names_its_anchor(flat):
    """"Owning is flat" holds only from the two highest-rate anchors in the
    series, so it is honest only when the anchor is stated alongside it. This
    does not forbid the claim — the third tile makes it deliberately — it
    forbids making it unanchored.

    Rewritten: the first version banned the word "flat" while allowing
    "sideways", which is the same claim and is the word the tile actually uses.
    It passed while permitting exactly what it existed to prevent.
    """
    tiles = re.findall(r'class="stat-label">([^<]+)<', flat)
    assert tiles, "no hero stat tiles found"
    hedges = ("flat", "sideways", "unchanged", "barely moved", "went nowhere",
              "stayed put", "no higher")
    for tile in tiles:
        if any(h in tile.lower() for h in hedges):
            assert re.search(r"\b(?:19|20)\d{2}\b", tile), \
                f"ownership-flatness claim with no anchor year: {tile!r}"


# -------------------------------------------------------------------- explorer

@pytest.mark.requires_data
def test_every_explorer_card_resolves_to_an_exported_series(page):
    """A card whose series is absent renders an error box to the reader."""
    bundles = list(WEB.glob("data/*.json"))
    if not bundles:
        pytest.skip("run `python src/run_all.py` first")
    available = set()
    for path in bundles:
        for ds in json.loads(path.read_text()):
            available.update(ds.get("columns", []))

    declared = set(re.findall(r'data-series="([^"]+)"', page))
    assert declared, "no explorer cards found"
    assert declared <= available, \
        f"cards with no exported series: {sorted(declared - available)}"


def test_every_explorer_card_has_a_label_and_units(page):
    """main.js falls back to the raw FRED id when metadata is missing, which
    tells a reader nothing."""
    js = (WEB / "main.js").read_text()
    meta_keys = set(re.findall(r"^\s{2}([A-Za-z0-9_]+):\s*\{", js, re.MULTILINE))
    declared = set(re.findall(r'data-series="([^"]+)"', page))
    assert declared <= meta_keys, \
        f"cards missing SERIES_META entries: {sorted(declared - meta_keys)}"
