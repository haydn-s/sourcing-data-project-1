# Priced Out: What Actually Broke Home Buying for Young Americans

**AIPI-510 (Sourcing Data for Analytics) — Module Project 1: Data Storytelling**
Duke University, Fall 2026

**Authors:** Natalie Zachariah, Haydn Stucker

---

## Overview

Everyone knows houses got expensive. That framing is incomplete, and the
incompleteness matters.

A buyer never actually pays a price — they pay a *monthly payment*, and they
have to pass a lender's income test to get it. Those depend on the price **and**
the interest rate together. Once you model the payment instead of the sticker
price, the recent history of American housing looks very different:

> Between 2021 and 2023, the median U.S. home price rose **11%**.
> The monthly payment on that same median home rose **54%**.
> **71%** of that increase came from interest rates, not from prices.

Over the same two years, the median household headed by a 25–34 year old got a
**14.6% raise** — and became dramatically *less* able to buy, because the income
a bank required jumped **54%**, from about \$79,000 to \$122,000.

That 71% is a statement about **2021–2023**, and 2021 was the all-time low in
mortgage rates — the anchor most favourable to a rates-driven reading. So we
tested it, re-running the identical decomposition from *every* anchor across a
20-year window, in both nominal and constant dollars.

The test does not weaken the claim. It sharpens it:

> **Rates are the larger factor from any anchor since 2012 — but only once you
> stop counting inflation as house-price growth.**

In constant dollars, rising rates outweigh rising prices from every anchor back
to 2012. That is a far stronger result than the 2021 anchor alone could support.
Real prices dominate only from a mid-2000s baseline — and that baseline is the
housing bubble.

Run the *nominal* sweep and you get the opposite answer for every anchor before
2020, because CPI rose **60%** across the window and a nominal split hands prices
the credit for it. The two crossovers sit eight years apart. We publish both, and
the gap between them — see [key finding 3](#key-findings) and
[`figures/07_decomposition_sensitivity.png`](figures/07_decomposition_sensitivity.png).

This project reconstructs that story from primary federal sources, engineers the
affordability metrics a buyer actually faces, and packages it for a general
audience as a podcast episode.

### Audience

Renters roughly 25–40 who are trying to decide whether buying is realistic, and
who keep hearing conflicting explanations for why it isn't. Secondary audience:
anyone who has been told that young people can't buy homes because they earn too
little or spend carelessly. The data does not support that explanation.

### Key findings

1. **The payment moved, not the price.** 2021→2023: prices +11.4%, mortgage rate
   +130% (2.96% → 6.80%), monthly payment +54.4%.
2. **Rates did the damage — over that window.** A counterfactual decomposition
   splits the $1,002/month increase into $209 from prices (21%), $712 from rates
   (71%), and $81 from their interaction (8%).
3. **The split depends on the anchor and on inflation — and we publish both.**
   The same decomposition, re-run from all 17 anchors from 2005 to 2021,
   measured through 2025. Effects are the added monthly payment each factor
   accounts for:

   | Anchor | Nominal: prices / rates | Constant-2024$: prices / rates | Real verdict |
   |---|---|---|---|
   | 2006 | $1,110 / $24 | $164 / $37 | prices |
   | 2009 | $1,153 / $171 | $516 / $250 | prices |
   | 2011 | $1,046 / $242 | $500 / $337 | prices |
   | **2012** | $876 / $353 | **$363 / $482** | **rates** ← real crossover |
   | 2015 | $632 / $399 | $80 / $528 | rates |
   | 2019 | $499 / $422 | $62 / $518 | rates |
   | **2020** | **$426 / $553** | $34 / $670 | rates ← nominal crossover |
   | 2021 | $156 / $672 | −$186 / $777 | rates |

   In constant dollars rates lead from **2012** on; nominally they only lead
   from **2020**. The eight-year gap is inflation: CPI rose 60% over the window,
   so a nominal split credits prices for it. Real prices actually *fell* between
   2021 and 2025, which is why that last row's price effect is negative.
   Constant dollars is the affordability-relevant lens, and it makes the
   rates story hold across two decades rather than two years.
4. **Young households out-earn the typical household.** Median income for
   householders aged 25–34 was $90,100 in 2024 versus $83,730 for all households
   — **1.08×** the all-ages median. The all-ages figure is dragged down by
   retirees. "Young people just don't earn enough" is not what the data shows.
5. **They got a raise and still lost.** Income 25–34 rose 14.6% from 2021 to
   2023 while required income rose 54.4%. Our affordability index fell from 94.8
   to 70.3.
6. **The 1980s were worse on the payment — but not on the down payment.** At
   13.9% mortgage rates, 1984's affordability index was 63.8, below 2024's 75.6.
   The down-payment barrier, however, has grown sharply: saving a 20% down
   payment took **6.7 years** of income in 1984 and **9.3 years** in 2024.
7. **Rent is what actually got more expensive — and it explains finding 6.**
   In constant 2024 dollars, the monthly cost of *owning* the median home is
   about where it was in 1988 ($2,831 → $2,819). Renting rose **+62%** over the
   same span ($909 → $1,474). Rent now takes **20%** of a 25–34 household's gross
   income, up from **14%** in 1988 — and that is the same income a down payment
   has to be saved out of. Owning has always cost more per month than renting
   (3.1× in 1988, 1.9× now); the barrier was never the monthly cost, it was
   getting in the door.
8. **The outcome shows up in ownership.** The homeownership rate for households
   under 35 is **36.0%** (2026 YTD) — still below its **37.4%** level in 1994,
   and well off its 2004 peak of 43.1%.

Figures are in [`figures/`](figures/).

---

## Data sources and citations

All data is public, federal, and downloaded programmatically from its primary
source by [`src/ingest.py`](src/ingest.py). Nothing is hand-edited.

### Federal Reserve Economic Data (FRED), Federal Reserve Bank of St. Louis

Retrieved via `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>`.

| Series ID | Description | Frequency |
|---|---|---|
| `MORTGAGE30US` | 30-Year Fixed Rate Mortgage Average (Freddie Mac PMMS) | Weekly |
| `MSPUS` | Median Sales Price of Houses Sold (Census/HUD) | Quarterly |
| `ASPUS` | Average Sales Price of Houses Sold | Quarterly |
| `CSUSHPINSA` | S&P CoreLogic Case-Shiller U.S. National Home Price Index | Monthly |
| `RHORUSQ156N` | Homeownership Rate, United States | Quarterly |
| `MEHOINUSA646N` | Median Household Income, current dollars | Annual |
| `MEHOINUSA672N` | Real Median Household Income (2024 dollars) | Annual |
| `SLOAS` | Student Loans Owned and Securitized | Quarterly |
| `CCLACBW027SBOG` | Credit Card Loans, All Commercial Banks | Weekly |
| `CUSR0000SEHA` | CPI: Rent of Primary Residence, SA | Monthly |
| `CPIAUCSL` | Consumer Price Index for All Urban Consumers | Monthly |
| `UNRATE` | Unemployment Rate | Monthly |
| `POPTHM` | Population, Total | Monthly |
| `GDP` | Gross Domestic Product | Quarterly |
| `PRIME` | Bank Prime Loan Rate | Irregular |
| `DGS10` / `DGS30` | 10- and 30-Year Treasury Constant Maturity Rate | Daily |
| `G160651A027NBEA` | Federal Outlays: Housing and Urban Development | Annual |

> Federal Reserve Bank of St. Louis, *FRED Economic Data*.
> https://fred.stlouisfed.org/ (retrieved August 2026).

### U.S. Census Bureau

| Table | Description | Coverage |
|---|---|---|
| HVS Table 19 | Homeownership Rates by Age of Householder | 1994–2026, quarterly |
| HVS Table 11A | Median Asking Rent, U.S. and regions | 1988–2026, quarterly |
| CPS ASEC Table H-10 | Age of Householder — Households by Median and Mean Income | 1967–2024, annual |

> U.S. Census Bureau, *Housing Vacancies and Homeownership (CPS/HVS)*, Tables 19
> and 11A.
> https://www.census.gov/housing/hvs/data/histtab19.xlsx
> https://www.census.gov/housing/hvs/data/histtab11.xlsx
>
> U.S. Census Bureau, *Current Population Survey, Annual Social and Economic
> Supplement*, Table H-10.
> https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-income-households/h10ar.xlsx

### Partner-supplied reference data

`data/raw/partner/` also contains files carried over from the project's
[initial data-sourcing repository](https://github.com/nez6/Housing-Data-Analysis):
Census congressional apportionment counts, and Macrotrends exports of historical
inflation and unemployment. The Macrotrends series are **not** used in the final
analysis — they are superseded by `CPIAUCSL` and `UNRATE`, which come directly
from BLS via FRED and are properly citable.

---

## Engineered features

The raw series answer "what did homes cost?" A buyer faces a monthly payment and
an underwriting test. [`src/features.py`](src/features.py) translates one into
the other. Every assumption is a named constant in
[`src/config.py`](src/config.py) so results can be re-run under different rules.

| Feature | Definition | Why it matters |
|---|---|---|
| `monthly_pi` | Amortizing P&I on the median home, 20% down, 30-year fixed, at that year's rate | The payment, not the price |
| `monthly_piti` | `monthly_pi` + taxes/insurance at 1.75% of value per year | What a buyer actually owes monthly |
| `required_income` | `monthly_piti × 12 ÷ 0.28` | Inverts the 28% front-end DTI rule to get the income a lender demands |
| `affordability_index` | Median income (age 25–34) ÷ `required_income` × 100 | 100 = the median young household exactly qualifies |
| `years_to_save_down` | 20% of price ÷ (income × 10% savings rate) | The barrier a payment-based measure misses entirely |
| `price_effect` / `rate_effect` / `interaction` | Two-factor counterfactual decomposition of the payment change vs 2021 | Separates how much of the pain is prices vs rates |
| `real_price_effect` / `real_rate_effect` | The same split with the base-year price deflated to 2024 dollars | Over long horizons the nominal split credits prices for inflation |
| `hor_gap_under35` | All-ages homeownership rate − under-35 rate | The outcome variable |
| `student_debt_per_capita` | `SLOAS` ÷ population | Competing claim on the same income |
| `monthly_ownership_cost` | `monthly_piti` + maintenance at 1% of value per year | The all-in cash cost of owning, comparable to a rent cheque |
| `own_to_rent_ratio` | `monthly_ownership_cost` ÷ median asking rent | Owning has always cost more per month; the barrier is entry, not carry |
| `rent_to_income` | 12 × rent ÷ income (age 25–34) | Rent competes directly with saving a deposit |
| `income_after_rent` | income (25–34) − annual rent | The pool a down payment is actually saved from |
| `credit_card_debt_per_capita` | `CCLACBW027SBOG` ÷ population | The other competing claim; the back-end DTI test counts revolving balances too |
| `consumer_debt_per_capita` | student + credit-card debt per capita | Student debt alone understates what a young buyer carries |

**On the decomposition.** To split the payment change since 2021 into price and
rate components, we hold one input at its 2021 level and let the other move.
Because the payment is multiplicative in price and non-linear in rate, the two
effects do not sum to the total; the residual **interaction** term is reported
explicitly rather than being quietly assigned to one factor.

**On the base year.** The decomposition answers "compared to *when*?", and that
choice moves the result more than any modeling assumption in this repo. 2021 was
the all-time low in mortgage rates, so anchoring there maximises the share
attributed to rates. `decompose_sensitivity()` re-runs the split from all 17
anchors between 2005 and 2021 and writes
`data/processed/decomposition_sensitivity.csv`.

**On nominal versus real.** Over two years the two agree; over twenty they do
not. CPI rose ~60% from 2006 to 2025 against ~70% nominal growth in the median
price, so a *nominal* split hands prices the credit for inflation. The test: if
prices, incomes and rents all doubled with inflation while rates held flat, a
nominal decomposition would report "prices did 100% of it" — while affordability
was untouched. The `real_*` columns deflate the base-year price to
`REAL_DOLLAR_BASE_YEAR` dollars so the price effect is real appreciation only.
Both are written; the real one is the affordability-relevant reading, and the
divergence between them is itself reported rather than quietly resolved.

**The same trap, one figure over.** `02_price_vs_payment.png` indexes price and
payment to a common base year, and an earlier version indexed at 2015 — which
made the two look permanently divergent. They are not: from 2005 the median price
is up ~73% and the payment on it ~80%. The divergence is real but it is a
*post-2021* phenomenon, so the figure now runs the full window (`INDEX_BASE_YEAR`)
and shades the shock rather than choosing the base that flatters the claim.

**On unreadable shares.** Percentage shares only mean something while both
effects push the same way. Real prices fell after 2021, so from those anchors the
price effect is negative and the shares run past 100% and below zero. Those rows
carry `real_shares_readable = False`, and the figure plots dollars rather than
shares so the sign is visible instead of hidden.

---

## Reproducing the analysis

Requires Python 3.12+ and an internet connection.

**1. Clone and enter the repo**

```bash
git clone https://github.com/haydn-s/sourcing-data-project-1.git
cd sourcing-data-project-1
```

**2. Create a virtual environment and install dependencies**

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

<details>
<summary>Using <code>uv</code> instead</summary>

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
```
</details>

**3. Run the whole pipeline**

```bash
python src/run_all.py
```

This downloads raw data, builds the cleaned panels, engineers the features,
writes all eight figures, exports the viewer's JSON, and prints every number
quoted in the podcast script.
Add `--refresh` to re-download the raw sources from scratch.

<details>
<summary>Running the stages individually</summary>

```bash
python src/ingest.py     # download raw data  -> data/raw/
python src/clean.py      # tidy panels        -> data/processed/
python src/features.py   # affordability math -> data/processed/
python src/eda.py        # figures + findings -> figures/
python src/export_for_web.py  # viewer JSON     -> web/data/
```
</details>

### Tests

```bash
pip install -r requirements-dev.txt
pytest
```

No network required — the suite runs against the committed CSVs. Four groups:

| File | Covers |
|---|---|
| [`tests/test_features.py`](tests/test_features.py) | The mortgage maths against a hand-computed amortisation value, and the decomposition identity: `price_effect + rate_effect + interaction` must reconstruct `total_change` exactly, or the residual is hiding a bug rather than reporting one |
| [`tests/test_clean.py`](tests/test_clean.py) | The three Census workbook parsers, against miniature fixtures that reproduce the real quirks — dot-leader quarter labels, footnote markers glued to years, duplicate years, and the two column-header rows. Also asserts each parser *fails loudly* when its assumed layout is gone |
| [`tests/test_readme_claims.py`](tests/test_readme_claims.py) | Every number in this README, read back out of the markdown by regex and compared to `data/processed/`. Edit a figure in one place and not the other and this fails, naming the claim |
| [`tests/test_eda.py`](tests/test_eda.py) | The partial-year footnote helper, plus smoke tests that every figure renders and `print_findings` runs |

`pytest -m "not requires_data"` skips the group that needs a pipeline run.
[CI](.github/workflows/tests.yml) runs the suite on every push and additionally
checks that the committed CSVs and JSON still regenerate byte-for-byte.

### Repository layout

```
├── src/
│   ├── config.py       # paths, series list, and every modeling assumption
│   ├── ingest.py       # download raw data from FRED + Census (resumable)
│   ├── clean.py        # tidy panels; parses the two Census workbooks
│   ├── features.py     # affordability metrics + payment decomposition
│   ├── eda.py          # figures and printed findings
│   ├── export_for_web.py  # processed CSVs -> web/data/*.json
│   └── run_all.py      # end-to-end pipeline driver
├── data/
│   ├── raw/fred/       # untouched FRED CSVs
│   ├── raw/partner/    # Census workbooks + partner reference files
│   └── processed/      # cleaned panels and engineered features
├── figures/            # generated PNGs
├── web/                # story page: index.html + main.js + exported JSON
├── tests/              # pytest suite (see above)
├── LICENSE             # MIT for code, CC BY-4.0 for the written analysis
├── .github/workflows/  # CI: tests + a staleness check on committed outputs
├── pyproject.toml      # pytest config only; the project is scripts, not a package
├── requirements.txt
└── requirements-dev.txt
```

**A note on imports.** `src/` has no `__init__.py`, and the modules import
their siblings directly (`from config import ...`). That resolves because Python
puts a script's own directory on `sys.path`, so everything must be run as a
script path — `python src/eda.py`, never `python -m src.eda`. The test suite
matches this via `pythonpath = ["src"]` in `pyproject.toml` rather than forcing a
package refactor that would break the documented commands above.

**A note on `src/ingest.py`:** FRED's CSV endpoint drops connections from
clients sending an unrecognized `User-Agent`. Both a custom project UA and a
spoofed browser UA failed consistently; the `requests` library default is served
normally. The script therefore sends the library default and identifies the
project here instead. Downloads are resumable — a re-run skips files already
present, so an interrupted run costs nothing.

---

## Limitations, bias, and ethical considerations

**This models one specific buyer, and that buyer is a construct.** Every figure
assumes a conventional 30-year fixed mortgage, 20% down, at the national median
price, judged against a 28% front-end DTI. Real buyers use FHA loans with 3.5%
down, get help from family, buy below the median, or stretch past 28%. The
national median home does not exist anywhere; housing markets are local, and a
single national series hides enormous variation between Austin and Cleveland.
Read these as an index of *pressure over time*, not a prediction for any person.

**Medians conceal distribution.** A median income paired with a median price
tells you nothing about who is actually buying. If the buyer pool shifts toward
wealthier households, medians can look stable while access narrows sharply
underneath. Our data cannot see that.

**Group averages erase the largest disparities.** We analyze young households as
one block. Homeownership rates differ enormously by race, and the Black–white
homeownership gap is wider today than it was when housing discrimination was
legal. Down-payment ability in particular is inherited — it reflects whether a
family *already* owned. An age-only cut is silent on the deepest inequity in
American housing, and readers should not treat "young people" as a homogeneous
group.

**The income and ownership cohorts are not the same people.** Income comes from
CPS H-10 for householders aged **25–34**; the homeownership rate comes from HVS
Table 19 for householders **under 35**, which includes everyone below 25. The two
are close enough to narrate together and are not interchangeable; we never divide
one by the other.

**"Young households out-earn all households" is partly composition.** A 25–34
household is more likely to hold two earners than the all-ages median, which
includes single retirees. The comparison is fair as a rebuttal to "young people
don't earn enough" — that claim is about the same households — but it is not
evidence that a young *individual* out-earns an older one.

**The rent comparison is softer than it looks.** Census Table 11A reports
asking rent on *vacant* units — what a mover faces, which is the right series for
someone deciding whether to buy, but not what a sitting tenant pays. Units on the
market also skew smaller than the median owned home, so we are not comparing
like with like on size. Read the rent figures as **trends, not levels**: the
+62% real growth is robust to that mismatch in a way the 1.9× ratio is not. The
comparison is also cash-only — it credits an owner nothing for equity and charges
a renter nothing for having none, so it is a measure of the monthly hurdle, not a
verdict on which is the better deal.

**Survey data has real error bars.** Census CPS and HVS estimates come from
household samples with sampling error, and CPS income questions changed
methodology in 2013 and 2017 (Census publishes two estimates for those years; we
keep the revised one). Year-over-year wiggles of a few tenths of a point are
noise, not signal.

**Two inflation adjustments are in play.** We deflate with CPI-U (`CPIAUCSL`)
while Census deflates its own real-income series with CPI-U-RS. The two differ
slightly. To avoid mixing them, the affordability ratio is computed entirely in
*nominal* dollars; real values appear only for display.

**Incomplete years are flagged, not hidden.** Market data runs through August
2026, so 2026 is a year-to-date average and is marked with an asterisk in
figures and an `is_partial_year` column in the data. Census income data lags by
design and ends in 2024, so the affordability index simply stops there rather
than being extrapolated.

**The framing is a choice.** Deciding to measure affordability by the monthly
payment is a defensible choice, but it is a choice, and it drives the headline.
By that measure the early 1980s were *worse* than today — we report this
explicitly rather than omitting an inconvenient comparison. Measuring instead by
the down payment, or by price-to-income, points the other way. Honest
storytelling means showing the reader which dial you turned.

**Causal language is avoided.** We show that rates and prices *account for* the
payment increase arithmetically. That is decomposition, not causal inference. We
do not claim to identify why rates rose, and nothing here should be read as
financial advice.

---

## Deliverables

- **Podcast episode:** script and show notes (not yet in this repo)
- **Story page:** [`web/`](web/) — the eight figures in narrative order, with an
  interactive explorer for all 17 source series underneath. Serve from the repo
  root (`python3 -m http.server 8000`, then `/web/`); see
  [`web/README.md`](web/README.md)
- **GitHub repository:** this repo
- **Presentation:** September 29th, in class

---

## License

Three parts, because the repository holds three different kinds of thing — see
[`LICENSE`](LICENSE) for the full terms.

| What | Where | Licence |
|---|---|---|
| Code | `src/`, `tests/`, `web/*.{html,js,css}`, root config | [MIT](LICENSE) |
| Written analysis and figures | this README, `web/index.html`, `figures/` | [CC BY-4.0](https://creativecommons.org/licenses/by/4.0/) |
| Source data | `data/raw/` | Public domain — U.S. government works, [17 U.S.C. § 105](https://www.law.cornell.edu/uscode/text/17/105) |

If you use the underlying series, please cite FRED and the Census Bureau
directly rather than this repository. The full citations are above.
