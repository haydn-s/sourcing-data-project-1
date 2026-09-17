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


def test_page_credits_the_metro_price_source(flat):
    """The regional chart draws on a second FRED family; the Sources section
    must say so, or the chart looks like it came from nowhere."""
    assert re.search(r"Case-Shiller 20-City Composite", flat), \
        "the metro home price indices are charted but not credited"


# -------------------------------------------------------------------- regional

def _js_function(js, name):
    m = re.search(rf"(?:async )?function {name}\(.*?\n}}\n", js, re.S)
    assert m, f"main.js no longer defines {name}"
    return m.group(0)


def test_regional_chart_reads_the_pipeline_export_not_literals():
    """The chart this replaced typed six city growth rates straight into
    main.js, with no source and no window. Every value must now come from
    web/data/regional_markets.json, which features.metro_price_growth writes."""
    body = _js_function((WEB / "main.js").read_text(), "renderRegionalComparison")
    assert "data/regional_markets.json" in body
    assert not re.search(r"-?\d+\.\d+", body), \
        "renderRegionalComparison contains a decimal literal — is data hardcoded again?"


@pytest.mark.requires_data
def test_regional_export_ranks_every_configured_metro():
    from config import METRO_HPI_SERIES
    path = WEB / "data" / "regional_markets.json"
    if not path.exists():
        pytest.skip("run `python src/run_all.py` first")
    rows = next(ds["records"] for ds in json.loads(path.read_text())
                if ds["name"] == "metro_price_growth.csv")
    assert sorted(r["metro"] for r in rows) == sorted(METRO_HPI_SERIES.values())
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))


# -------------------------------------------------------------------- figures

def test_stated_figure_count_matches_the_figures_shown(flat, page):
    m = re.search(r"The story, in ([a-z]+|\d+) figures", flat)
    assert m, "the story section no longer states a figure count"
    shown = len(re.findall(r'<img src="\.\./figures/', page))
    assert word_or_digit(m.group(1)) == shown


# Figures the story deliberately leaves out, and why. Anything else in figures/
# must be on the page. A hardcoded list of the figures *shown* -- which this
# replaced -- passes when a figure silently drops out, which is how figure 05,
# the outcome the project measures, went missing without a test failing.
EXCLUDED_FIGURES = {
    "03_payment_decomposition.png":
        "Methodology. Reason 2 quotes its headline split in prose; the chart is in the README.",
    "07_decomposition_sensitivity.png":
        "Methodology: the base-year robustness check, documented in the README.",
}


def test_every_generated_figure_appears_on_the_page(page):
    on_disk = {p.name for p in FIGURES.glob("*.png")}
    referenced = set(re.findall(r'<img src="\.\./figures/([^"]+)"', page))
    missing = on_disk - referenced - set(EXCLUDED_FIGURES)
    assert not missing, f"generated but neither shown nor deliberately excluded: {sorted(missing)}"


def test_figure_exclusions_are_still_true(page):
    """An exclusion for a figure that no longer exists, or that is now shown,
    is a stale reason nobody will notice."""
    referenced = set(re.findall(r'<img src="\.\./figures/([^"]+)"', page))
    for name in EXCLUDED_FIGURES:
        assert (FIGURES / name).exists(), f"{name} is excluded but no longer generated"
        assert name not in referenced, f"{name} is excluded but the page shows it"


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


def test_header_links_to_the_repository(page):
    """A reader landing mid-page should be able to reach the repo without
    scrolling to the bottom."""
    header = re.search(r"<header[^>]*>.*?</header>", page, re.S)
    assert header, "no site header found"
    assert re.search(r'href="https://github\.com/[\w.-]+/[\w.-]+"', header.group(0)), \
        "the header does not link to the repository"


def test_external_nav_links_open_safely(page):
    """target=_blank without rel=noopener hands the new tab a window.opener
    reference back to this page."""
    for tag in re.findall(r"<a [^>]*target=\"_blank\"[^>]*>", page):
        assert "noopener" in tag, f"external link missing rel=noopener: {tag[:80]}"


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
    data = pd.read_csv(csv, index_col="year")
    rent = data.loc[~data["is_partial_year"].astype(bool),
                    "asking_rent_real2024"].dropna()
    growth = (rent.iloc[-1] / rent.iloc[0] - 1) * 100

    m = re.search(r'stat-value">\+(\d+)%</span>\s*<span class="stat-label">Median asking rent after inflation',
                  flat)
    assert m, "the hero no longer states the real rent figure"
    assert int(m.group(1)) == pytest.approx(growth, abs=1)


@pytest.mark.requires_data
def test_headline_claims_about_price_and_payment_match_the_data(flat, inflation):
    """The headline once said housing was "at an all-time high", then that
    prices "barely eased" -- true before inflation (-4% from the 2022 peak) but
    not after it (-13%). It now makes the after-inflation claim, checked here."""
    h1 = re.search(r"<h1>(.*?)</h1>", flat)
    assert h1, "the hero has no headline"
    headline = h1.group(1)
    assert not re.search(r"all-time high|record high", headline.lower())
    assert "median new-home sale price" in headline
    from config import SHOCK_START_YEAR
    m = re.search(r"After inflation, it fell (\d+)% from (\d{4}) to (\d{4})—"
                  r"and the modeled monthly payment still rose (\d+)%", headline)
    assert m, "the headline changed wording"
    assert int(m.group(2)) == SHOCK_START_YEAR
    assert int(m.group(3)) == inflation["latest_year"]
    assert inflation["price_real_since_shock"] < 0, "prices no longer down after inflation"
    assert int(m.group(1)) == round(-inflation["price_real_since_shock"])
    assert int(m.group(4)) == round(inflation["payment_real_since_shock"])


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


# ------------------------------------------------------------- house hacking

def _house_hack(flat):
    """The house-hacking section plus the leverage and summary cards that
    close it out in Takeaways -- everywhere its numbers appear."""
    section = re.search(r'<section id="house-hack".*?</section>', flat)
    leverage = re.search(r"<h3>Leverage Cuts Both Ways.*?</table>", flat)
    assert section and leverage, "the house hacking section or its leverage card is gone"
    return section.group(0) + leverage.group(0)


def _quoted(text, pattern):
    m = re.search(pattern, text)
    assert m, f"claim not found on the page (did the wording change?): {pattern}"
    return float(m.group(1).replace(",", ""))


@pytest.fixture(scope="module")
def aff():
    import pandas as pd
    csv = ROOT / "data" / "processed" / "affordability.csv"
    if not csv.exists():
        pytest.skip("run `python src/run_all.py` first")
    return pd.read_csv(csv, index_col="year")


@pytest.mark.requires_data
def test_house_hack_rent_and_income_claims_match_the_data(flat, aff):
    """This section used to credit a +62% rent rise to the CPI rent index (it is
    Census asking rent) and put renters' housing costs at "30% to 45%" of
    income, which the project's own rent_to_income series does not show."""
    text = _house_hack(flat)
    pct = lambda col: (aff.loc[2024, col] / aff.loc[1988, col] - 1) * 100
    assert _quoted(text, r"asking rent rose <strong>(\d+)%</strong> after inflation from 1988 to 2024") \
        == round(pct("asking_rent_real2024"))
    assert _quoted(text, r"aged 25–34 rose <strong>(\d+)%</strong>") == round(pct("income_young_real2024"))
    assert _quoted(text, r"grew from <strong>(\d+)%</strong> to") == round(aff.loc[1988, "rent_to_income"] * 100)
    assert _quoted(text, r"grew from <strong>\d+%</strong> to <strong>(\d+)%</strong>") \
        == round(aff.loc[2024, "rent_to_income"] * 100)


@pytest.mark.requires_data
def test_house_hack_rent_offset_illustration_matches_the_data(flat, aff):
    text = _house_hack(flat)
    cost, rent = aff.loc[2024, "monthly_ownership_cost"], aff.loc[2024, "asking_rent"]
    assert _quoted(text, r"with 20% down.*?was <strong>\$([\d,]+)</strong>") == round(cost)
    assert _quoted(text, r"median asking rent of <strong>\$([\d,]+)</strong>") == round(rent)
    assert _quoted(text, r"would cover <strong>(\d+)%</strong>") == round(rent / cost * 100)


def test_house_hack_principal_paydown_matches_the_amortisation(flat):
    """The section once said $4,000 to $6,000 of principal is repaid in year one
    on $350,000 at 6.5%. The schedule says about $3,900."""
    from features import monthly_payment
    text = _house_hack(flat)
    loan = _quoted(text, r"on a <strong>\$([\d,]+)</strong> 30-year fixed loan")
    rate = _quoted(text, r"30-year fixed loan at <strong>([\d.]+)%</strong>")
    payment = float(monthly_payment(loan, rate, down_pct=0.0))
    balance, r = loan, rate / 100 / 12
    for _ in range(12):
        balance -= payment - balance * r
    principal = loan - balance
    assert _quoted(text, r"about <strong>\$([\d,]+)</strong> of the first year's payments") \
        == pytest.approx(principal, abs=50)
    assert _quoted(text, r"the other <strong>\$([\d,]+)</strong> or so is interest") \
        == pytest.approx(payment * 12 - principal, abs=50)


@pytest.mark.requires_data
def test_leverage_card_uses_the_project_price_history(flat, aff):
    """The appreciation rate in the leverage example is the data's own long-run
    pace, and the downside cites years the data actually shows."""
    text = _house_hack(flat)
    price = aff.loc[~aff["is_partial_year"].astype(bool), "median_price"]
    first, last = price.index.min(), price.index.max()
    cagr = ((price[last] / price[first]) ** (1 / (last - first)) - 1) * 100
    assert re.search(rf"average yearly rise from {first} to {last}", text), \
        "the leverage card's averaging window no longer matches the data"
    assert _quoted(text, r"that rises <strong>(\d+)%</strong> in a year") == round(cagr)
    drop = _quoted(text, r"fell about <strong>(\d+)%</strong> in both 2008 and 2009")
    changes = price.pct_change() * 100
    for year in (2008, 2009):
        assert changes[year] == pytest.approx(-drop, abs=0.5)

    down = _quoted(text, r"with <strong>5%</strong> down \(<strong>\$([\d,]+)</strong>\)")
    home = _quoted(text, r"a <strong>\$([\d,]+)</strong> home bought")
    gain = _quoted(text, r"gains <strong>\$([\d,]+)</strong>")
    assert down == home * 0.05 and gain == home * round(cagr) / 100
    assert _quoted(text, r"or <strong>(\d+)%</strong> of the down payment") == gain / down * 100


def test_house_hack_sources_are_credited(page):
    sources = re.search(r'<section id="sources".*?</section>', page, re.S)
    assert sources, "no Sources section"
    for cited in ("Survey of Consumer Finances", "Eligibility Matrix",
                  "Publication 527", "Publication 523"):
        assert cited in sources.group(0), f"the house hacking section relies on {cited}, uncredited"


def test_house_hack_makes_no_riskless_return_claims(flat):
    """The summary card once called house hacking "mathematically proven" and
    said it minimized downside risk. Leverage does the opposite."""
    text = _house_hack(flat).lower()
    for phrase in ("mathematically proven", "minimizing downside", "minimize downside",
                   "guaranteed", "risk-free", "no risk"):
        assert phrase not in text, f"overclaim in the house hacking section: {phrase!r}"


# --------------------------------------------------------------------- story

@pytest.fixture(scope="module")
def inflation():
    import pandas as pd
    from features import inflation_summary
    processed = ROOT / "data" / "processed"
    if not (processed / "annual_panel.csv").exists():
        pytest.skip("run `python src/run_all.py` first")
    return inflation_summary(pd.read_csv(processed / "affordability.csv", index_col="year"),
                             pd.read_csv(processed / "annual_panel.csv", index_col="year"))


@pytest.mark.requires_data
def test_hero_tiles_say_which_basis_they_use(flat, inflation):
    """The price and payment tiles were before inflation and the rent tile after
    it, side by side and unlabelled. Every tile now names its basis."""
    tiles = re.findall(r'stat-value">([^<]+)</span>\s*<span class="stat-label">([^<]+)<', flat)
    assert len(tiles) == 3
    for _, label in tiles:
        assert "after inflation" in label, f"tile does not say it is after inflation: {label!r}"
    pct = lambda v: int(v.replace("−", "-").replace("%", ""))
    (price, price_label), (payment, payment_label), _ = tiles
    assert pct(price) == round(inflation["price_real_shock"])
    assert pct(payment) == round(inflation["payment_real_shock"])
    assert f"+{round(inflation['price_nominal_shock'])}% before inflation" in price_label
    assert f"+{round(inflation['payment_nominal_shock'])}% before inflation" in payment_label



def _panel_attr(page, n, attr):
    m = re.search(rf'<figure id="story-figure-{n}"[^>]*\b{attr}="([^"]*)"', page)
    assert m, f"story panel {n} has no {attr}"
    return m.group(1)


def test_story_heading_counts_the_reason_tabs(flat):
    """The heading once promised "Six Reasons" over four reason tabs."""
    m = re.search(r"The Story: ([A-Za-z]+) Reasons", flat)
    assert m, "the story heading no longer states a count"
    tabs = re.findall(r'data-storyfig="\d+">Reason (\d+)<', flat)
    assert word_or_digit(m.group(1)) == len(tabs)
    assert [int(t) for t in tabs] == list(range(1, len(tabs) + 1))


def test_story_tabs_and_panels_pair_up(page):
    buttons = [int(n) for n in re.findall(r'class="story-figure-btn[^"]*" data-storyfig="(\d+)"', page)]
    panels = [int(n) for n in re.findall(r'<figure id="story-figure-(\d+)"', page)]
    assert buttons == panels == list(range(1, len(panels) + 1))


def test_each_story_chart_matches_its_fallback_figure(page):
    """Chart keys are the PNG numbers. Reason 3's chart was keyed "3" but drew
    figure 04, and Reason 2's text described a different chart from its own;
    pairing each chart with the PNG beside it keeps the two describing one thing."""
    pairs = re.findall(r'data-story-chart="(\d{2})".*?<img src="\.\./figures/(\d{2})_', page, re.S)
    assert pairs, "no story charts found"
    for chart, png in pairs:
        assert chart == png, f"story chart {chart} sits beside figure {png}"
    js = (WEB / "main.js").read_text()
    drawn = set(re.findall(r"'(\d{2})': element =>", js))
    assert {c for c, _ in pairs} <= drawn, "a story chart has no renderer in main.js"


def test_first_story_summary_matches_reason_one(flat, page):
    """The summary shown on load differed from Reason 1's own, so it changed the
    first time a reader clicked back to Reason 1."""
    static = re.search(r'id="story-figure-summary"[^>]*>\s*(.*?)\s*</div>', flat).group(1)
    title = re.search(r'id="story-figure-title">(.*?)</h3>', flat).group(1)
    assert static == _panel_attr(page, 1, "data-figure-summary")
    assert title == _panel_attr(page, 1, "data-figure-title")


def test_story_charts_use_the_configured_narrative_years():
    """Reason 2's chart indexed at 2021, the base year config.INDEX_BASE_YEAR's
    comment explains was rejected for flattering the claim."""
    import config
    js = (WEB / "main.js").read_text()
    for name in ("INDEX_BASE_YEAR", "SHOCK_START_YEAR", "SHOCK_END_YEAR", "HOR_BASE_YEAR"):
        m = re.search(rf"const {name} = (\d{{4}});", js)
        assert m, f"main.js no longer defines {name}"
        assert int(m.group(1)) == getattr(config, name), f"main.js {name} drifted from config"


def test_story_charts_skip_missing_values_and_partial_years():
    """Number(null) is 0, so a finiteness check alone drew every unpublished
    year as $0 and sent the income lines off the bottom of Reason 1."""
    body = _js_function((WEB / "main.js").read_text(), "validRows")
    assert "!= null" in body and "is_partial_year" in body


def _money(token):
    return float(token.replace(",", "").replace("$", ""))


@pytest.mark.requires_data
def test_reason_one_income_figures_match_the_data(page, aff, inflation):
    """In 2024 dollars, like its fallback PNG. Before inflation, "incomes kept
    rising" was mostly prices rising: young-household income grew 4% in real
    terms from 2021 to 2024."""
    text = _panel_attr(page, 1, "data-figure-summary")
    m = re.search(r"In 2024 dollars, the median household aged 25–34 earned \$([\d,]+) in (\d{4}) against "
                  r"\$([\d,]+) required; by (\d{4}) it earned \$([\d,]+) against \$([\d,]+)", text)
    assert m, "Reason 1's income comparison changed wording"
    latest = int(aff["income_young"].dropna().index.max())
    assert int(m.group(4)) == latest, "Reason 1 does not quote the latest income year"
    for year, earned, required in ((int(m.group(2)), m.group(1), m.group(3)),
                                   (latest, m.group(5), m.group(6))):
        assert _money(earned) == round(aff.loc[year, "income_young_real2024"])
        assert _money(required) == round(aff.loc[year, "required_income_real2024"])
    m = re.search(r"After inflation its income rose (\d+)% while the benchmark income required rose (\d+)%", text)
    assert m, "Reason 1's after-inflation comparison changed wording"
    assert int(m.group(1)) == round(inflation["income_young_real_since_shock"])
    assert int(m.group(2)) == round(inflation["required_income_real_since_shock"])

    renderer = re.search(r"'01': element => \{(.*?)\n    \},", (WEB / "main.js").read_text(), re.S).group(1)
    for field in ("income_young_real2024", "income_all_ages_real2024", "required_income_real2024"):
        assert field in renderer, f"Reason 1's chart no longer draws {field}"


@pytest.mark.requires_data
def test_reason_two_price_and_payment_figures_match_the_data(page, aff):
    import pandas as pd
    from config import INDEX_BASE_YEAR, SHOCK_END_YEAR, SHOCK_START_YEAR
    text = _panel_attr(page, 2, "data-figure-summary")
    full = aff[~aff["is_partial_year"].astype(bool)]
    last = int(full[["median_price", "monthly_piti"]].dropna().index.max())
    pct = lambda col, start: round((full.loc[last, col] / full.loc[start, col] - 1) * 100)

    m = re.search(rf"[Ff]rom {INDEX_BASE_YEAR} to {last} the median new-home sale price rose (\d+)% "
                  r"and the modeled monthly payment on it (\d+)%", text)
    assert m, "Reason 2's long-run comparison changed wording or years"
    assert int(m.group(1)) == pct("median_price", INDEX_BASE_YEAR)
    assert int(m.group(2)) == pct("monthly_piti", INDEX_BASE_YEAR)

    m = re.search(rf"after {SHOCK_START_YEAR}\. Since then the price is up (\d+)% and the payment (\d+)%", text)
    assert m, "Reason 2's since-the-shock comparison changed wording"
    assert int(m.group(1)) == pct("median_price", SHOCK_START_YEAR)
    assert int(m.group(2)) == pct("monthly_piti", SHOCK_START_YEAR)

    csv = ROOT / "data" / "processed" / "payment_decomposition.csv"
    row = pd.read_csv(csv, index_col="year").loc[SHOCK_END_YEAR]
    m = re.search(rf"(\d+)% of the \$([\d,]+) monthly increase from {SHOCK_START_YEAR} "
                  rf"to {SHOCK_END_YEAR} came from higher rates", text)
    assert m, "Reason 2's decomposition claim changed wording"
    assert int(m.group(1)) == round(row["rate_effect_share"])
    assert _money(m.group(2)) == round(row["total_change"])


@pytest.mark.requires_data
def test_reason_three_index_figures_match_the_data(flat, page, aff):
    text = _panel_attr(page, 3, "data-figure-summary")
    m = re.search(r"fell from ([\d.]+) in (\d{4}) to ([\d.]+) in (\d{4}), "
                  r"and recovered only to ([\d.]+) in (\d{4})", text)
    assert m, "Reason 3's index path changed wording"
    idx = aff["affordability_index"].dropna()
    assert int(m.group(2)) == idx.idxmax(), "Reason 3's starting point is no longer the peak"
    assert int(m.group(6)) == idx.index.max(), "Reason 3 does not end at the latest year"
    for value, year in ((m.group(1), m.group(2)), (m.group(3), m.group(4)), (m.group(5), m.group(6))):
        assert float(value) == round(idx[int(year)], 1)

    m = re.search(r"lower still in 1984 \(([\d.]+)\), when mortgage rates averaged ([\d.]+)%", flat)
    assert m, "Reason 3's 1984 comparison changed wording"
    assert float(m.group(1)) == round(aff.loc[1984, "affordability_index"], 1)
    assert float(m.group(2)) == round(aff.loc[1984, "mortgage_rate"], 1)


@pytest.mark.requires_data
def test_reason_four_saving_figures_match_the_data(page, aff):
    text = _panel_attr(page, 4, "data-figure-summary")
    m = re.search(r"needed ([\d.]+) years to save a 20% down payment on the median newly sold home "
                  r"in (\d{4}) and ([\d.]+) years in (\d{4})", text)
    assert m, "Reason 4's saving comparison changed wording"
    years = aff["years_to_save_down"].dropna()
    assert int(m.group(4)) == years.index.max()
    for value, year in ((m.group(1), m.group(2)), (m.group(3), m.group(4))):
        assert float(value) == round(years[int(year)], 1)


@pytest.mark.requires_data
def test_result_homeownership_figures_match_the_data(page, aff):
    from config import HOR_BASE_YEAR
    text = _panel_attr(page, 5, "data-figure-summary")
    full = aff[~aff["is_partial_year"].astype(bool)]
    under, allages = full["hor_under_35"].dropna(), full["hor_all"].dropna()
    m = re.search(r"peaked at ([\d.]+)% in (\d{4}) and fell to ([\d.]+)% in (\d{4})\. "
                  rf"In (\d{{4}}) it was ([\d.]+)%, just below the ([\d.]+)% of {HOR_BASE_YEAR}, "
                  rf"while the rate for all ages, ([\d.]+)%, was above its {HOR_BASE_YEAR} level of ([\d.]+)%", text)
    assert m, "the result's homeownership summary changed wording"
    peak, low, latest = int(m.group(2)), int(m.group(4)), int(m.group(5))
    assert peak == under.idxmax() and low == under.loc[peak:].idxmin() and latest == under.index.max()
    assert float(m.group(1)) == round(under[peak], 1)
    assert float(m.group(3)) == round(under[low], 1)
    assert float(m.group(6)) == round(under[latest], 1)
    assert float(m.group(7)) == round(under[HOR_BASE_YEAR], 1)
    assert under[latest] < under[HOR_BASE_YEAR], "'just below' the base year no longer holds"
    assert float(m.group(8)) == round(allages[latest], 1)
    assert float(m.group(9)) == round(allages[HOR_BASE_YEAR], 1)
    assert allages[latest] > allages[HOR_BASE_YEAR], "'above its base-year level' no longer holds"


# ----------------------------------------------------------------- structure

def test_page_is_one_document(page):
    """The page once closed </body></html> twice, with the footer after the
    first </html> and main.js loaded a second time, which threw "Identifier
    'INK' has already been declared" on every load."""
    assert page.count("</html>") == 1, "the document closes more than once"
    assert len(re.findall(r'<script src="main\.js"', page)) == 1, "main.js is loaded more than once"
    footer, main_end, body_end = page.find("<footer"), page.find("</main>"), page.find("</body>")
    assert -1 < main_end < footer < body_end, "the footer is not between </main> and </body>"


def test_nav_lists_every_section_in_page_order(page):
    """The nav once ran Explore, Story, Forces while the page ran Explore,
    Forces, Story, and left House Hacking out entirely."""
    header = re.search(r"<nav[^>]*>.*?</nav>", page, re.S).group(0)
    linked = re.findall(r'href="#([\w-]+)"', header)
    sections = re.findall(r'<section id="([\w-]+)"', page)
    assert linked == sections, f"nav {linked} does not match page order {sections}"


def test_page_title_uses_the_site_name(page):
    brand = re.search(r'class="brand"[^>]*>(.*?)</a>', page).group(1).replace("&nbsp;", " ")
    title = re.search(r"<title>(.*?)</title>", page).group(1)
    assert title.startswith(brand), f"tab title {title!r} does not carry the site name {brand!r}"


def test_explorer_charts_every_fred_series_exactly_once(page):
    """web/README.md promises every downloaded series, one chart each. Four FRED
    series had no card while two others had a card in two tabs."""
    explore = re.search(r'<section id="explore".*?</section>', page, re.S).group(0)
    cards = re.findall(r'data-series="([^"]+)"', explore)
    duplicated = sorted({c for c in cards if cards.count(c) > 1})
    assert not duplicated, f"series charted more than once: {duplicated}"
    missing = sorted(set(FRED_SERIES) - set(cards))
    assert not missing, f"FRED series with no explorer card: {missing}"


def test_page_explains_itself_when_the_data_cannot_load(page):
    """Opened from disk, every chart's fetch() fails. The page used to show
    empty boxes, and 27 explorer cards told the reader to re-run a pipeline
    that had already run. A browser test is out of reach here, so this pins the
    pieces the fallback depends on."""
    assert re.search(r'<div id="data-warning"[^>]*\bhidden\b', page), \
        "the data warning banner is missing or visible by default"
    js = (WEB / "main.js").read_text()
    assert "location.protocol === 'file:'" in js, "file:// no longer triggers the warning"
    fallback = _js_function(js, "showStaticStoryFigures")
    assert "noscript" in fallback, "the story no longer falls back to its PNGs"
    story_catch = re.search(r"renderStoryFigures\(\)\.catch\(error => \{(.*?)\}\);", js, re.S)
    assert story_catch and "showStaticStoryFigures()" in story_catch.group(1)
    # Every story chart needs a PNG beside it for the fallback to show anything.
    charts = re.findall(r'data-story-chart="(\d{2})"', page)
    fallbacks = re.findall(r'<noscript><img src="\.\./figures/(\d{2})_', page)
    assert charts == fallbacks


# -------------------------------------------------------------------- supply

@pytest.fixture(scope="module")
def supply():
    import pandas as pd
    from features import supply_summary
    csv = ROOT / "data" / "processed" / "fred_monthly.csv"
    if not csv.exists():
        pytest.skip("run `python src/run_all.py` first")
    return supply_summary(pd.read_csv(csv, index_col="date", parse_dates=["date"]))


def _tab_intro(flat, tab):
    m = re.search(rf'<div id="{tab}"[^>]*>\s*<p class="section-intro">(.*?)</p>', flat)
    assert m, f"the {tab} intro is gone"
    return m.group(1)


def test_supply_chart_reads_the_pipeline_export():
    """The index is computed in features.housing_supply, like the regional
    ranking; main.js only draws it. No year may be typed into the chart: the
    baseline arrives with the data and the shock years come from the config-
    tested constants."""
    body = _js_function((WEB / "main.js").read_text(), "renderSupplyChart")
    assert "data/housing_supply.json" in body
    years = re.findall(r"\b(?:19|20)\d{2}\b", re.sub(r"/\*.*?\*/", "", body, flags=re.S))
    assert not years, f"renderSupplyChart hardcodes years: {years}"


@pytest.mark.requires_data
def test_hero_supply_claims_match_the_data(flat, supply):
    """The hero once said the payment shock overwhelmed "the limited supply
    response", with no supply data in the project. The data splits that claim:
    homes for sale were scarce, but construction did respond."""
    from config import SHOCK_END_YEAR, SHOCK_START_YEAR, SUPPLY_BASELINE_YEARS
    lede = re.search(r'<p class="lede">(.*?)</p>', flat).group(1)
    assert "since 2008" not in lede, "lenders tested income long before 2008"

    b0, b1 = SUPPLY_BASELINE_YEARS
    assert re.search(rf"In {SHOCK_START_YEAR}–{SHOCK_END_YEAR}, .*active listings averaged about half "
                     rf"their {b0}–{b1} level", lede), "the listings claim changed wording or years"
    assert 0.4 <= supply["listings_ratio"] <= 0.6, f"listings ran {supply['listings_ratio']:.0%} of baseline, not about half"

    m = re.search(r"homeowner vacancy rate fell to its lowest since (\d{4})", lede)
    assert m, "the vacancy claim changed wording"
    assert int(m.group(1)) == supply["vacancy_first_year"]
    assert SHOCK_START_YEAR <= supply["vacancy_low_year"] <= SHOCK_END_YEAR

    m = re.search(r"builders started more single-family homes in (\d{4}) than in any year since (\d{4})", lede)
    assert m, "the construction claim changed wording"
    assert int(m.group(1)) == supply["starts_peak_year"]
    assert int(m.group(2)) == supply["starts_last_higher_year"]
    assert supply["starts_highest_since_peak"] < supply["starts_peak"], "a later year has overtaken the peak"


@pytest.mark.requires_data
def test_housing_tab_intro_matches_the_data(flat, aff, supply):
    from config import SHOCK_END_YEAR, SHOCK_START_YEAR
    text = _tab_intro(flat, "tab-housing")
    assert "supply constraints" not in text and "price discovery" not in text
    rate = aff["mortgage_rate"]
    assert f"mortgage rates more than doubled from {SHOCK_START_YEAR} to {SHOCK_END_YEAR}" in text
    assert rate[SHOCK_END_YEAR] > 2 * rate[SHOCK_START_YEAR]
    m = re.search(r"the median new-home sale price still rose (\d+)%", text)
    assert m, "the price claim changed wording"
    price = aff["median_price"]
    assert int(m.group(1)) == round((price[SHOCK_END_YEAR] / price[SHOCK_START_YEAR] - 1) * 100)
    assert "the vacancy rate hit a record low" in text
    assert SHOCK_START_YEAR <= supply["vacancy_low_year"] <= SHOCK_END_YEAR
    assert "the months' supply of new homes climbed" in text
    assert supply["new_home_supply_end"] > supply["new_home_supply_start"]


@pytest.mark.requires_data
def test_debt_tab_intro_matches_the_data(flat, aff):
    """The national stock comparison is checked without treating it as applicant
    debt service or evidence about an age-specific qualification decision."""
    text = _tab_intro(flat, "tab-debt")
    assert "does not determine how other debts affected qualification" in text
    assert "not age-specific" in text and "do not measure the monthly debt service" in text
    m = re.search(r"per U\.S\. resident equaled ([\d.]+)% of median young-household income in (\d{4}) "
                  r"and ([\d.]+)% in (\d{4})", text)
    assert m, "the consumer debt claim changed wording"
    debt = aff["consumer_debt_pct_income"]
    start, end = int(m.group(2)), int(m.group(4))
    assert float(m.group(1)) == round(debt[start], 1) and float(m.group(3)) == round(debt[end], 1)
    assert end == debt.dropna().index.max() and debt[end] < debt[start]

    m = re.search(r"rose from (\d+)% to (\d+)% of (?:young-household|that) income between (\d{4}) and (\d{4})", text)
    assert m, "the payment-to-income claim changed wording"
    ratio = aff["payment_to_income"] * 100
    assert int(m.group(1)) == round(ratio[int(m.group(3))])
    assert int(m.group(2)) == round(ratio[int(m.group(4))])



@pytest.mark.requires_data
def test_reason_two_after_inflation_figures_match_the_data(flat, page, inflation):
    text = _panel_attr(page, 2, "data-figure-summary")
    m = re.search(r"most of that was inflation: after it, they rose (\d+)% and (\d+)%", text)
    assert m, "Reason 2's long-run after-inflation claim changed wording"
    assert int(m.group(1)) == round(inflation["price_real_long"])
    assert int(m.group(2)) == round(inflation["payment_real_long"])
    m = re.search(r"or down (\d+)% and up (\d+)% after inflation", text)
    assert m, "Reason 2's since-the-shock after-inflation claim changed wording"
    assert inflation["price_real_since_shock"] < 0 < inflation["payment_real_since_shock"]
    assert int(m.group(1)) == round(-inflation["price_real_since_shock"])
    assert int(m.group(2)) == round(inflation["payment_real_since_shock"])

    m = re.search(r"ex-post mortgage rate minus same-year CPI inflation moved from −([\d.]+)% in (\d{4}) to \+([\d.]+)% in (\d{4})", flat)
    assert m, "Reason 2's real-rate sentence changed wording"
    assert -float(m.group(1)) == round(inflation["real_rate_low"], 1)
    assert int(m.group(2)) == inflation["real_rate_low_year"]
    assert float(m.group(3)) == round(inflation["real_rate_latest"], 1)
    assert int(m.group(4)) == inflation["latest_year"]


@pytest.mark.requires_data
def test_price_measure_caveat_contrasts_new_home_median_and_case_shiller(flat, inflation):
    """The headline measure and the constant-quality index moved in opposite
    directions after inflation, so the page must name both rather than present
    the new-home median as the whole market."""
    m = re.search(r"It fell ([\d.]+)% after CPI inflation from 2021 to 2023, "
                  r"while the .*?Case-Shiller national repeat-sales index .*? rose ([\d.]+)% after inflation", flat)
    assert m, "the page no longer explains the scope-sensitive price result"
    assert -float(m.group(1)) == pytest.approx(inflation["price_real_shock"], abs=0.05)
    assert float(m.group(2)) == pytest.approx(inflation["case_shiller_real_shock"], abs=0.05)


@pytest.mark.requires_data
def test_reason_four_moving_target_matches_the_data(flat, inflation):
    """years_to_save_down assumes the price holds still while you save."""
    m = re.search(r"If prices and incomes keep their (\d{4})–(\d{4}) pace, saving from (\d{4}) takes "
                  r"([\d.]+) years when savings keep up with inflation, and ([\d.]+) when they earn nothing", flat)
    assert m, "Reason 4's moving-target caption changed wording"
    assert (int(m.group(1)), int(m.group(2))) == inflation["growth_window"]
    assert int(m.group(3)) == inflation["latest_income_year"]
    assert float(m.group(4)) == round(inflation["save_years_savings_keep_up"], 1)
    assert float(m.group(5)) == round(inflation["save_years_savings_earn_nothing"], 1)


@pytest.mark.requires_data
def test_housing_tab_and_limitations_state_inflation_figures(flat, inflation):
    assert f"still rose {round(inflation['price_nominal_shock'])}% before inflation " \
           f"(a {round(-inflation['price_real_shock'])}% fall after it)" in flat
    m = re.search(r"CPI less shelter instead makes the rent finding stronger, \+(\d+)% rather than "
                  r"\+(\d+)% from (\d{4}) to (\d{4})", flat)
    assert m, "the deflator limitation changed wording"
    assert int(m.group(1)) == round(inflation["rent_real_less_shelter"])
    assert int(m.group(2)) == round(inflation["rent_real_cpi"])
    assert (int(m.group(3)), int(m.group(4))) == inflation["rent_window"]
    assert inflation["rent_real_less_shelter"] > inflation["rent_real_cpi"], "the check no longer strengthens the finding"
