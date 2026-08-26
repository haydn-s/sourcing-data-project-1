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
a bank required jumped **54%**, from about $79,000 to $122,000.

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
2. **Rates did the damage.** A counterfactual decomposition splits the
   $1,002/month increase into $209 from prices (21%), $712 from rates (71%), and
   $81 from their interaction (8%).
3. **Young households out-earn the typical household.** Median income for
   householders aged 25–34 was $90,100 in 2024 versus $83,730 for all households
   — **1.08×** the all-ages median. The all-ages figure is dragged down by
   retirees. "Young people just don't earn enough" is not what the data shows.
4. **They got a raise and still lost.** Income 25–34 rose 14.6% from 2021 to
   2023 while required income rose 54.4%. Our affordability index fell from 94.8
   to 70.3.
5. **The 1980s were worse on the payment — but not on the down payment.** At
   13.9% mortgage rates, 1984's affordability index was 63.8, below 2024's 75.6.
   The down-payment barrier, however, has grown sharply: saving a 20% down
   payment took **6.7 years** of income in 1984 and **9.3 years** in 2024.
6. **The outcome shows up in ownership.** The homeownership rate for households
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
| CPS ASEC Table H-10 | Age of Householder — Households by Median and Mean Income | 1967–2024, annual |

> U.S. Census Bureau, *Housing Vacancies and Homeownership (CPS/HVS)*, Table 19.
> https://www.census.gov/housing/hvs/data/histtab19.xlsx
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
| `hor_gap_under35` | All-ages homeownership rate − under-35 rate | The outcome variable |
| `student_debt_per_capita` | `SLOAS` ÷ population | Competing claim on the same income |

**On the decomposition.** To split the payment change since 2021 into price and
rate components, we hold one input at its 2021 level and let the other move.
Because the payment is multiplicative in price and non-linear in rate, the two
effects do not sum to the total; the residual **interaction** term is reported
explicitly rather than being quietly assigned to one factor.

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
writes all six figures, and prints every number quoted in the podcast script.
Add `--refresh` to re-download the raw sources from scratch.

<details>
<summary>Running the stages individually</summary>

```bash
python src/ingest.py     # download raw data  -> data/raw/
python src/clean.py      # tidy panels        -> data/processed/
python src/features.py   # affordability math -> data/processed/
python src/eda.py        # figures + findings -> figures/
```
</details>

### Repository layout

```
├── src/
│   ├── config.py       # paths, series list, and every modeling assumption
│   ├── ingest.py       # download raw data from FRED + Census (resumable)
│   ├── clean.py        # tidy panels; parses the two Census workbooks
│   ├── features.py     # affordability metrics + payment decomposition
│   ├── eda.py          # figures and printed findings
│   └── run_all.py      # end-to-end pipeline driver
├── data/
│   ├── raw/fred/       # untouched FRED CSVs
│   ├── raw/partner/    # Census workbooks + partner reference files
│   └── processed/      # cleaned panels and engineered features
├── figures/            # generated PNGs
├── podcast/            # episode script and show notes
└── requirements.txt
```

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

- **Podcast episode:** script and show notes in [`podcast/`](podcast/)
- **GitHub repository:** this repo
- **Presentation:** September 29th, in class

## Collaboration

Work is done on feature branches and merged via pull request, with each group
member authoring at least one PR and reviewing the other's.

| Branch | Contributor | Scope |
|---|---|---|
| `initial-setup` | Haydn Stucker | Pipeline, feature engineering, EDA, podcast script |
| _(see PRs)_ | Natalie Zachariah | Data sourcing, source evaluation, review |
