# Priced Out: The $712 Nobody Talks About — Show Notes

Everyone blames home prices. The data says prices are about a fifth of the
problem.

Between 2021 and 2023 the median U.S. home price rose 11% — but the monthly
payment on that same house rose 54%. We decompose that increase and find 71% of
it came from interest rates, not prices. Meanwhile the median household headed
by a 25–34 year old got a 14.6% raise over those two years and still fell
further behind, because the income needed to qualify for a mortgage jumped from
about $79,000 to $122,000.

## In this episode

- **(1:15)** Why the price of a house is the wrong number to watch
- **(4:30)** Splitting the payment increase into prices vs. interest rates
- **(9:00)** The finding that surprised us: young households out-earn the typical
  American household
- **(13:00)** "But rates were 14% in the eighties" — the objection, and where
  it's right
- **(16:00)** Homeownership under 35 is lower today than in 1994
- **(18:00)** What our analysis can't see

## Key figures

| | |
|---|---|
| Median home price, 2021 → 2023 | $383,000 → $426,525 (**+11.4%**) |
| Monthly payment, same house | $1,843 → $2,845 (**+54.4%**) |
| Share of that increase from rates | **71%** |
| Income needed to qualify | $78,987 → $121,948 (**+54.4%**) |
| Median income, householder 25–34 | $74,860 → $85,780 (**+14.6%**) |
| Years to save a 20% down payment | 6.7 (1984) → **9.3** (2024) |
| Homeownership rate, under 35 | 37.4% (1994) → **36.0%** (2026 YTD) |

## Data sources

All public and federal:

- Federal Reserve Economic Data (FRED), Federal Reserve Bank of St. Louis —
  mortgage rates, home prices, CPI, population, debt balances.
  https://fred.stlouisfed.org/
- U.S. Census Bureau, Housing Vacancies and Homeownership (HVS), Table 19 —
  homeownership rate by age of householder.
- U.S. Census Bureau, Current Population Survey ASEC, Table H-10 — median income
  by age of householder.

## Reproduce every number

Code, raw data, and cleaned data: https://github.com/haydn-s/sourcing-data-project-1

```bash
git clone https://github.com/haydn-s/sourcing-data-project-1.git
cd sourcing-data-project-1
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python src/run_all.py
```

Every figure cited in the episode is printed by that last command. All modeling
assumptions — down payment percentage, debt-to-income limit, savings rate — are
named constants in `src/config.py`. Change them and rerun to see how sensitive
the conclusions are.

## Caveats

We model a conventional 30-year mortgage with 20% down at the national median
price. Real buyers differ, housing is local, and medians hide distribution. We
analyze young households as a single group, which is silent on the large racial
disparities in homeownership and inherited down-payment wealth. Our decomposition
is arithmetic, not causal inference. Nothing here is financial advice.

*Produced for AIPI-510 (Sourcing Data for Analytics), Duke University, Fall 2026.
Natalie Zachariah and Haydn Stucker.*
