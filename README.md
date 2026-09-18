# Priced Out: Why Home Buying Got Harder for Young Americans

**AIPI-510 (Sourcing Data for Analytics) — Module Project 1: Data Storytelling**
Duke University, Fall 2026

**Authors:** Natalie Zachariah, Haydn Stucker

---

## Overview

Everyone knows houses got expensive. That framing is incomplete, and the
incompleteness matters.

The sticker price alone does not determine monthly affordability. A financed
buyer also faces an interest rate and an underwriting test. Once those are
modeled together, the recent history of American housing looks very different:

> Between 2021 and 2023, the median sale price of newly built single-family
> houses rose **11%**.
> The modeled monthly payment on that median newly sold home rose **54%**.
> The rate effect accounted for **71%** of that increase; prices accounted for
> 21%, with 8% from their interaction.

Over the same two years, the median household headed by a 25–34 year old got a
**14.6% raise** — and became dramatically *less* able to buy, because the income
the project's qualification benchmark implied jumped **54%**, from about
\$79,000 to \$122,000.

That 71% is a statement about **2021–2023**, and 2021 was the all-time low in
mortgage rates — the anchor most favourable to a rates-driven reading. So we
tested it, re-running the identical decomposition from *every* anchor across a
20-year window, in both nominal and constant dollars.

The test does not weaken the claim. It sharpens it:

> **Rates are the larger factor from any anchor since 2012 — but only once you
> stop counting inflation as house-price growth.**

In constant dollars, rising rates outweigh rising prices from every anchor back
to 2012. That is a far stronger result than the 2021 anchor alone could support.
Changes in the inflation-adjusted new-home median dominate only from a
mid-2000s baseline — and that baseline is the housing bubble.

Run the *nominal* sweep and you get the opposite answer for every anchor before
2020, because CPI rose **60%** across the window and a nominal split hands prices
the credit for it. The two crossovers sit eight years apart. We publish both, and
the gap between them — see [key finding 3](#key-findings) and
[`figures/07_decomposition_sensitivity.png`](figures/07_decomposition_sensitivity.png).

This project reconstructs that story from federal and third-party data sources,
engineers a transparent set of affordability benchmarks, and packages it for a
general audience as an interactive website.

### Audience

Renters roughly 25–40 who are trying to decide whether buying is realistic, and
who keep hearing conflicting explanations for why it is difficult. The project
evaluates market prices, financing, income, rent, and saving; it does not measure
individual household spending choices.

### Key findings

1. **The modeled payment moved much more than the new-home median.** 2021→2023:
   median new-home sale price +11.4%, mortgage rate +130% (2.96% → 6.80%),
   modeled monthly payment +54.4%.
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
   so a nominal split credits prices for it. The real median sale price of new
   houses fell between 2021 and 2025, which is why that last row's price effect
   is negative.
   Constant dollars is the affordability-relevant lens, and it makes the
   rates story hold across two decades rather than two years.
4. **Young households out-earn the typical household.** Median income for
   householders aged 25–34 was $90,100 in 2024 versus $83,730 for all households
   — **1.08×** the all-ages median. The all-ages figure is dragged down by
   retirees. This comparison cautions against treating the all-ages median as a
   proxy for young-household income; it does not measure individual earnings or
   spending behavior.
5. **They got a raise and still lost.** Income 25–34 rose 14.6% from 2021 to
   2023 while income required under the benchmark rose 54.4%. Our affordability
   index fell from 94.8 to 70.3.
6. **The 1980s were worse on the payment — but not on the down payment.** At
   13.9% mortgage rates, 1984's affordability index was 63.8, below 2024's 75.6.
   The down-payment barrier, however, has grown sharply: saving a 20% down
   payment took **6.7 years** of income in 1984 and **9.3 years** in 2024.
7. **Rent grew much faster than the modeled ownership cost, tightening the path
   to a down payment.** From 1988 to the latest complete market year, 2025, the
   modeled monthly cash cost of the median newly sold home rose **6%** after
   inflation ($2,831 → $2,995). Median asking rent rose **60%** over the same
   span ($909 → $1,452). Through 2024, the latest year with matching income data,
   rent took **20%** of a 25–34 household's gross income, up from **14%** in 1988.
   The modeled ownership cost remained higher than asking rent (3.1× in 1988,
   2.1× in 2025), so both the monthly carrying cost and the entry barrier matter.

   **Base-year caveat, applied to ourselves.** 1988 is where the Census rent
   series begins, so it is forced rather than chosen — but it was a **10.3%**
   mortgage-rate year, the 86th percentile of the whole series, and it therefore
   flatters the ownership line. Measured from any anchor between **1990 and 2019**,
   real ownership cost is *higher*, by between 8% and 51%. The rent finding
   survives the same test over the same window: up by 18% to 68%, from every one
   of those anchors. (We bound the sweep at 2019 because an anchor a year or two
   from the endpoint measures noise, not a trend — from 2023, both series are
   slightly *down*.) The stronger conclusion is comparative: rent grew much
   faster than this standardized ownership-cost model from the high-rate era.
8. **The outcome shows up in ownership.** The homeownership rate for households
   under 35 was **37.1%** in 2025 — still below its **37.4%** level in 1994,
   and well off its 2004 peak of 43.1%.

Figures are in [`figures/`](figures/).

---

## Data sources and citations

The analysis combines federal public-domain data with copyrighted third-party
series distributed through FRED. [`src/ingest.py`](src/ingest.py) downloads the
files programmatically; nothing is hand-edited. FRED is the retrieval service,
not the owner of every series.

### Federal Reserve Economic Data (FRED), Federal Reserve Bank of St. Louis

Retrieved via `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES_ID>`.

| Series ID | Description | Frequency |
|---|---|---|
| `MORTGAGE30US` | 30-Year Fixed Rate Mortgage Average (Freddie Mac PMMS) | Weekly |
| `MSPUS` | Median Sales Price of New Houses Sold (Census/HUD) | Quarterly |
| `ASPUS` | Average Sales Price of New Houses Sold | Quarterly |
| `CSUSHPINSA` | S&P CoreLogic Case-Shiller U.S. National Home Price Index | Monthly |
| `RHORUSQ156N` | Homeownership Rate, United States | Quarterly |
| `MEHOINUSA646N` | Median Household Income, current dollars | Annual |
| `MEHOINUSA672N` | Real Median Household Income (2024 dollars) | Annual |
| `SLOAS` | Student Loans Owned and Securitized | Quarterly |
| `CCLACBW027SBOG` | Credit Card Loans, All Commercial Banks | Weekly |
| `CUSR0000SEHA` | CPI: Rent of Primary Residence, SA | Monthly |
| `CPIAUCSL` | Consumer Price Index for All Urban Consumers | Monthly |
| `CUSR0000SA0L2` | CPI for All Urban Consumers: All Items Less Shelter (a check on the deflator) | Monthly |
| `UNRATE` | Unemployment Rate | Monthly |
| `POPTHM` | Population, Total | Monthly |
| `GDP` | Gross Domestic Product | Quarterly |
| `PRIME` | Bank Prime Loan Rate | Irregular |
| `DGS10` / `DGS30` | 10- and 30-Year Treasury Constant Maturity Rate | Daily |
| `G160651A027NBEA` | Federal Outlays: Housing and Urban Development | Annual |
| `ACTLISCOUUS` | Housing Inventory: Active Listing Count (Realtor.com) | Monthly, from July 2016 |
| `RHVRUSQ156N` | Homeowner Vacancy Rate (Census HVS) | Quarterly |
| `HOUST1F` | New Privately-Owned Housing Units Started: Single-Family Units | Monthly |
| `MSACSR` | Monthly Supply of New Houses | Monthly |

> Federal Reserve Bank of St. Louis, *FRED Economic Data*.
> https://fred.stlouisfed.org/ (retrieved August 2026; the four supply series
> and CPI less shelter September 2026). `ACTLISCOUUS` is Realtor.com Economic Research data published
> through FRED.

#### Source rights and reuse

FRED series do not share one license. The repository preserves them for this
non-commercial educational analysis under their original terms and does not
relicense them:

- Census, BLS, BEA, and other federal series are generally marked by FRED as
  public domain with citation requested.
- `MORTGAGE30US` (Freddie Mac) and `ACTLISCOUUS` (Realtor.com) are copyrighted
  with citation required.
- The national and metro S&P Cotality Case-Shiller indices are copyrighted by
  S&P Dow Jones Indices and marked **Copyrighted: Pre-Approval Required** by
  FRED. FRED permits non-commercial educational or personal use under its terms;
  other reuse requires permission from the data owner.

Review the [FRED terms of use](https://fred.stlouisfed.org/legal/terms/) and the
rights notice on each series page before reusing raw files. Key notices:
[Freddie Mac](https://fred.stlouisfed.org/series/MORTGAGE30US),
[Realtor.com](https://fred.stlouisfed.org/series/ACTLISCOUUS), and
[Case-Shiller](https://fred.stlouisfed.org/series/CSUSHPINSA).

#### Regional home prices: S&P Cotality Case-Shiller 20-City metros

The regional comparison on the story page uses the home price index for every
metro in the S&P Cotality Case-Shiller 20-City Composite (formerly S&P
CoreLogic), retrieved from the same FRED endpoint. All are monthly and not
seasonally adjusted, matching `CSUSHPINSA`. They are listed in
`METRO_HPI_SERIES` in [`src/config.py`](src/config.py), kept apart from the
national series above because they are a cross-section of one measure rather
than inputs to the monthly panel.

| Series ID | Metro | Series ID | Metro |
|---|---|---|---|
| `ATXRNSA` | Atlanta | `MIXRNSA` | Miami |
| `BOXRNSA` | Boston | `MNXRNSA` | Minneapolis |
| `CRXRNSA` | Charlotte | `NYXRNSA` | New York |
| `CHXRNSA` | Chicago | `PHXRNSA` | Phoenix |
| `CEXRNSA` | Cleveland | `POXRNSA` | Portland |
| `DAXRNSA` | Dallas | `SDXRNSA` | San Diego |
| `DNXRNSA` | Denver | `SFXRNSA` | San Francisco |
| `DEXRNSA` | Detroit | `SEXRNSA` | Seattle |
| `LVXRNSA` | Las Vegas | `TPXRNSA` | Tampa |
| `LXXRNSA` | Los Angeles | `WDXRNSA` | Washington, DC |

> S&P Dow Jones Indices LLC, *S&P Cotality Case-Shiller Home Price Indices*,
> retrieved from FRED, Federal Reserve Bank of St. Louis (retrieved September 2026).

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

The unused Macrotrends exports and congressional-apportionment reference file
from the initial sourcing exercise were removed. `data/raw/partner/` now contains
only the Census workbooks used by the analysis.

---

## Engineered features

The raw series answer "what did homes cost?" A buyer faces a monthly payment and
an underwriting test. [`src/features.py`](src/features.py) translates one into
the other. Every assumption is a named constant in
[`src/config.py`](src/config.py) so results can be re-run under different rules.

| Feature | Definition | Why it matters |
|---|---|---|
| `monthly_pi` | Amortizing P&I on the median newly sold home, 20% down, 30-year fixed, at that year's rate | Standardized payment benchmark |
| `monthly_piti` | `monthly_pi` + estimated taxes/insurance at 1.75% of value per year | Modeled PITI; excludes HOA fees and transaction costs |
| `required_income` | `monthly_piti × 12 ÷ 0.28` | Income implied by a common 28% front-end DTI benchmark, not a universal lender rule |
| `affordability_index` | Median income (age 25–34) ÷ `required_income` × 100 | 100 = the median young household meets the benchmark |
| `years_to_save_down` | 20% of price ÷ (income × 10% savings rate) | The barrier a payment-based measure misses entirely |
| `price_effect` / `rate_effect` / `interaction` | Two-factor counterfactual decomposition of the payment change vs 2021 | Separates how much of the pain is prices vs rates |
| `real_mortgage_rate` | `mortgage_rate` − that year's CPI-U inflation (`cpi_inflation`) | Ex-post annual proxy; below zero means the nominal rate was below realized CPI inflation, not that home prices rose |
| `real_price_effect` / `real_rate_effect` | The same split with the base-year price deflated to 2024 dollars | Over long horizons the nominal split credits prices for inflation |
| `hor_gap_under35` | All-ages homeownership rate − under-35 rate | The outcome variable |
| `student_debt_per_capita` | `SLOAS` ÷ total population | National balance-sheet context; not age-specific debt or monthly debt service |
| `monthly_ownership_cost` | `monthly_piti` + maintenance at 1% of value per year | Standardized cash-cost model; not a complete buyer budget |
| `own_to_rent_ratio` | `monthly_ownership_cost` ÷ median asking rent | Comparison of two unlike national benchmarks; use the trend, not the level |
| `rent_to_income` | 12 × rent ÷ income (age 25–34) | Rent competes directly with saving a deposit |
| `income_after_rent` | income (25–34) − annual rent | The pool a down payment is actually saved from |
| `credit_card_debt_per_capita` | `CCLACBW027SBOG` ÷ total population | National revolving-credit stock per resident |
| `consumer_debt_per_capita` | student + credit-card debt per capita | Context only; it cannot represent a young applicant's back-end DTI |
| `growth_pct` / `real_growth_pct` | Change in each of 20 Case-Shiller metro indices from 2021 to the latest complete year, from annual means; the real version deflates by national CPI-U | Regional comparison; one deflator shifts every metro equally, so it does not reorder the ranking |
| `listings_index` / `starts_index` | Active listings and single-family starts, each as an annual mean ÷ its own 2017–2019 average × 100 | Puts two supply measures with no shared unit on one axis: how far each was from normal |

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

**The same trap, one figure over.** `02_price_vs_payment.png` indexes the new-home
median and payment to a common base year, and an earlier version indexed at 2015
— which made the two look permanently divergent. They are not: from 2005 through
the latest complete year, 2025, the new-home median is up ~76% and the payment on
it ~86%. The divergence is real but it is a *post-2021* phenomenon, so the figure
now runs the full window (`INDEX_BASE_YEAR`) and shades the shock rather than
choosing the base that flatters the claim.

**On unreadable shares.** Percentage shares only mean something while both
effects push the same way. The real new-home median fell after 2021, so from
those anchors the price effect is negative and the shares run past 100% and
below zero. Those rows
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
writes all eight figures, exports the viewer's JSON, and prints the key findings
used in the public story.
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

No network required — the suite runs against the committed CSVs. Six groups:

| File | Covers |
|---|---|
| [`tests/test_features.py`](tests/test_features.py) | The mortgage maths against a hand-computed amortisation value, and the decomposition identity: `price_effect + rate_effect + interaction` must reconstruct `total_change` exactly, or the residual is hiding a bug rather than reporting one. Also the metro growth ranking: annual means, a window only as long as every metro has data for, and a deflator that cannot reorder it |
| [`tests/test_clean.py`](tests/test_clean.py) | The three Census workbook parsers, against miniature fixtures that reproduce the real quirks — dot-leader quarter labels, footnote markers glued to years, duplicate years, and the two column-header rows. Also asserts each parser *fails loudly* when its assumed layout is gone |
| [`tests/test_readme_claims.py`](tests/test_readme_claims.py) | Every number in this README, read back out of the markdown by regex and compared to `data/processed/`. Edit a figure in one place and not the other and this fails, naming the claim |
| [`tests/test_eda.py`](tests/test_eda.py) | The partial-year footnote helper, plus smoke tests that every figure renders and `print_findings` runs |
| [`tests/test_web_page.py`](tests/test_web_page.py) | The claims `web/index.html` makes in prose — the series count, the Census tables credited, the figure count — plus that every generated figure is actually shown, every explorer card resolves to an exported series, the regional chart reads the exported ranking rather than numbers typed into `main.js`, the supply, debt, income-test and inflation claims match the data, the headline's price and payment claims hold, and every number in the house hacking section matches the data or the amortisation schedule |
| [`tests/test_reproducibility.py`](tests/test_reproducibility.py) | That the committed CSVs are what the committed code produces. Compared numerically at a 1e-9 relative tolerance, not byte-for-byte: `piti()` raises `(1+r)` to the 360th power, and the last bit of `pow` differs between an arm64 laptop and an x86-64 CI runner |

`pytest -m "not requires_data"` skips the group that needs a pipeline run.
[CI](.github/workflows/tests.yml) runs the suite on every push.

### Generated tables

`python src/run_all.py` writes eleven tables to `data/processed/`. The first five
are cleaned sources; the last six are the analysis.

| File | Shape | What it holds |
|---|---|---|
| `fred_monthly.csv` | 956 × 24 | Every FRED series on a shared monthly index |
| `metro_hpi_monthly.csv` | 474 × 21 | The 20 Case-Shiller metro indices, monthly, not forward-filled |
| `homeownership_age.csv` | 130 × 9 | HVS Table 19, quarterly, by age of householder |
| `asking_rent.csv` | 154 × 5 | HVS Table 11A, quarterly median asking rent |
| `income_by_age.csv` | 58 × 9 | CPS H-10, median income by age of householder |
| `annual_panel.csv` | 43 × 42 | The calendar-year panel everything downstream is built on |
| `affordability.csv` | 43 × 47 | The engineered features — payment, required income, the index, rent vs own |
| `payment_decomposition.csv` | 43 × 13 | Price/rate/interaction split against the 2021 base year |
| `decomposition_sensitivity.csv` | 17 × 25 | The same split re-run from all 17 anchors, nominal and real |
| `housing_supply.csv` | 9 × 7 | Active listings and single-family starts by year, each indexed to its 2017–2019 average |
| `metro_price_growth.csv` | 20 × 9 | Each metro's home price growth from 2021 to the latest complete year, nominal and real, ranked |

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
│   ├── raw/partner/    # Census source workbooks
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
new-home sale price, judged against a common 28% front-end DTI benchmark. That
threshold is a comparison rule, not a universal lender cap. Taxes, insurance,
and maintenance are estimates; HOA fees, transaction costs, and buyer-specific
charges are excluded. Real buyers use FHA loans with 3.5% down, get help from
family, buy below the median, or use different DTI thresholds. The national
median newly sold home does not exist anywhere; housing markets are local, and a
single national series hides enormous variation between Austin and Cleveland.
Read these as an index of *pressure over time*, not a prediction for any person.

**The headline price is the median for newly sold homes, not all homes.** The
payment model needs a dollar price, so it uses Census/HUD's `MSPUS`: the median
sale price of new single-family houses. A median can change when the mix of homes
sold changes. From 2021 to 2023 it fell **1.0%** after CPI inflation, while the
national Case-Shiller repeat-sales index in this repository rose **4.6%** after
inflation. Case-Shiller follows repeat sales of existing homes and better holds
quality constant, but it is an index rather than a dollar price. The headline
therefore describes the new-home median, not every measure of U.S. home values.

**The regional comparison is 20 metros, not the country.** Case-Shiller tracks
20 large metros, so fast-growing markets outside that set (Austin, Nashville,
Raleigh) and smaller cities are absent. Its repeat-sales method follows the
same homes over time, which removes changes in *what* sold but also leaves out
new construction. The real growth figures deflate every metro by national CPI,
not local living costs, which shifts all 20 bars by the same factor without
changing their order.

**Supply is measured nationally, and in two halves that disagree.** Active
listings and the homeowner vacancy rate describe the existing stock for sale;
single-family starts and the months' supply of new homes describe construction.
In 2021–2023 the first two sat near their lows while the last two ran above their
pre-pandemic levels, so "supply" without saying which half is ambiguous. Listings only begin in July 2016, so the
pre-pandemic baseline is 2017–2019, a short one. None of these series is local,
and scarce listings holding prices up is consistent with the data, not proven by
it.

**Medians conceal distribution.** A median income paired with the median
new-home sale price tells you nothing about who is actually buying. If the buyer
pool or mix of homes sold shifts, medians can look stable while access narrows
sharply underneath. Our data cannot see that.

**Group averages erase the largest disparities.** We analyze young households as
one block. Homeownership rates differ enormously by race, and the Black–white
homeownership gap is wider today than it was when housing discrimination was
legal ([Urban Institute](https://www.urban.org/urban-wire/black-homeownership-gap-wider-today-than-it-was-when-segregation-was-legal)).
Down-payment ability in particular is shaped by intergenerational wealth and
whether a family already owned. An age-only cut is silent on the deepest
inequity in American housing, and readers should not treat "young people" as a
homogeneous group.

**The income and ownership cohorts are not the same people.** Income comes from
CPS H-10 for householders aged **25–34**; the homeownership rate comes from HVS
Table 19 for householders **under 35**, which includes everyone below 25. The two
are close enough to narrate together and are not interchangeable; we never divide
one by the other.

**"Young households out-earn all households" is partly composition.** A 25–34
household is more likely to hold two earners than the all-ages median, which
includes single retirees. The comparison shows that age-group household income
did not trail the all-household median in 2024, but it does not establish why a
particular household could or could not buy, and it is not evidence that a young
*individual* out-earns an older one.

**The rent comparison is softer than it looks.** Census Table 11A reports
asking rent on *vacant* units — what a mover faces, which is the right series for
someone deciding whether to buy, but not what a sitting tenant pays. Units on the
market also skew smaller than the median newly sold home, so we are not comparing
like with like on size. Read the rent figures as **trends, not levels**: the
+60% real growth through 2025 is robust to that mismatch in a way the 2.1× ratio
is not. The comparison is also cash-only — it credits an owner nothing for equity
and charges a renter nothing for having none, so it is a measure of the monthly
hurdle, not a verdict on which is the better deal. And the 1988 start flatters the ownership
side, for the reason set out in finding 7: it was a 10.3%-rate year. We ran the
same base-year sweep on ourselves that figure 07 runs on the decomposition, and
report the result rather than the single anchor the data handed us.

**Survey data has real error bars.** Census CPS and HVS estimates come from
household samples with sampling error, and CPS income questions changed
methodology in 2013 and 2017 (Census publishes two estimates for those years; we
keep the revised one). Year-over-year wiggles of a few tenths of a point are
noise, not signal.

**Two inflation adjustments are in play.** We deflate with CPI-U (`CPIAUCSL`)
while Census deflates its own real-income series with CPI-U-RS. The two differ
slightly. To avoid mixing them, the affordability ratio is computed entirely in
*nominal* dollars; real values appear only for display.

**The deflator is partly housing.** Shelter is about a third of CPI-U, so
deflating rents and prices by it partly deflates housing by itself. As a check,
`CUSR0000SA0L2` (CPI less shelter) is downloaded too: deflated by it, the median
asking rent rose **74%** from 1988 to 2025 rather than **60%**, so the rent
finding gets stronger, not weaker. `python src/eda.py` prints both.

**Years to save assumes the price holds still.** `years_to_save_down` divides
today's down payment by today's savings. If the new-home median and young-household
income keep their 1984–2024 pace (+4.2% and +3.4% a year), saving from 2024 takes
**10.4** years rather than **9.3** when savings keep up with CPI, and **12.5** when
they earn nothing (`features.years_to_save_moving`).

**Incomplete years are flagged and excluded from endpoint claims.** Market data
runs through August 2026, so 2026 is a year-to-date average and carries an
`is_partial_year` flag. The public narrative and its endpoint comparisons stop
at the latest complete year; the explorer retains the partial observations for
transparency, and figure 03 marks its 2026 bar with an asterisk. Census income
data lags by design and ends in 2024, so the affordability index stops there
rather than being extrapolated.

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

- **Public communication website:** [`web/`](web/) — six of the eight figures as
  a narrative, a
  regional comparison of 20 metros, and an interactive explorer for all 23
  national FRED series underneath. Serve from the repo
  root (`python3 -m http.server 8000`, then `/web/`); see
  [`web/README.md`](web/README.md)
- **GitHub repository:** this repo
- **Presentation:** September 29th, in class

---

## License

Code and original written content use separate licenses. Source data remains
under its original owners' terms — see
[`LICENSE`](LICENSE) for the full terms.

| What | Where | Licence |
|---|---|---|
| Code | `src/`, `tests/`, `web/*.{html,js,css}`, root config | [MIT](LICENSE) |
| Written analysis and figures | this README, `web/index.html`, `figures/` | [CC BY-4.0](https://creativecommons.org/licenses/by/4.0/) |
| Source data | `data/raw/` | Not relicensed; federal and third-party source terms apply |

If you use the underlying series, cite FRED and the original data owner and
follow the per-series rights notices described above.
