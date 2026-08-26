"""Exploratory analysis: summary tables and the figures used in the story.

Writes PNGs to figures/ and prints the findings quoted in the podcast script,
so every number in the narrative is traceable to a command in this repo.
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import (
    DECOMP_BASE_YEAR,
    DOWN_PAYMENT_PCT,
    FIGURES,
    FRONT_END_DTI,
    PROCESSED,
    SAVINGS_RATE,
)

INK = "#1d2433"
ACCENT = "#c1442e"
COOL = "#2b6cb0"
MUTED = "#8a94a6"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelcolor": INK,
    "axes.edgecolor": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "figure.autolayout": True,
})


def _save(fig, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  figures/{name}")


def fig_income_vs_required(df):
    """The scissors: what a buyer earns vs what a lender requires."""
    d = df.dropna(subset=["income_young"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(d.index, d["required_income_real2024"], color=ACCENT, lw=2.2,
            label=f"Income required to qualify (at {FRONT_END_DTI:.0%} DTI)")
    ax.plot(d.index, d["income_young_real2024"], color=COOL, lw=2.2,
            label="Actual median income, householder age 25-34")
    ax.fill_between(d.index, d["income_young_real2024"],
                    d["required_income_real2024"],
                    where=d["required_income_real2024"] > d["income_young_real2024"],
                    color=ACCENT, alpha=0.12)
    ax.set_title("The qualifying gap: what young buyers earn vs what banks require")
    ax.set_ylabel("2024 dollars")
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:.0f}k")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    _save(fig, "01_income_vs_required.png")


def fig_price_vs_payment(df):
    """Prices barely moved after 2021; the payment exploded."""
    d = df.loc[2015:]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    base = d.loc[2015]
    ax.plot(d.index, d["median_price"] / base["median_price"] * 100,
            color=COOL, lw=2.2, label="Median home price")
    ax.plot(d.index, d["monthly_piti"] / base["monthly_piti"] * 100,
            color=ACCENT, lw=2.2, label="Monthly payment (PITI)")
    ax.axhline(100, color=MUTED, lw=0.8, ls="--")
    ax.set_title("Price is not the payment (2015 = 100)")
    ax.set_ylabel("Index, 2015 = 100")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    _save(fig, "02_price_vs_payment.png")


def fig_decomposition(decomp):
    """How much of the payment jump was price, and how much was the rate."""
    d = decomp.loc[DECOMP_BASE_YEAR + 1:].dropna(subset=["total_change"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(d.index, d["price_effect"], color=COOL, label="Higher prices")
    ax.bar(d.index, d["rate_effect"], bottom=d["price_effect"],
           color=ACCENT, label="Higher interest rates")
    ax.bar(d.index, d["interaction"],
           bottom=d["price_effect"] + d["rate_effect"],
           color=MUTED, label="Interaction")
    ax.plot(d.index, d["total_change"], "o", color=INK, ms=5,
            label="Total increase")
    ax.set_title(f"What drove the payment increase since {DECOMP_BASE_YEAR}")
    ax.set_ylabel("Added monthly cost vs " + str(DECOMP_BASE_YEAR))
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")
    ax.set_xticks(d.index)
    partial = d["is_partial_year"].fillna(False).astype(bool)
    ax.set_xticklabels([f"{y}*" if p else str(y) for y, p in zip(d.index, partial)])
    if partial.any():
        yrs = ", ".join(str(y) for y in d.index[partial])
        ax.text(0.0, -0.16, f"* {yrs}: partial year, year-to-date average.",
                transform=ax.transAxes, fontsize=8, color=MUTED)
    ax.legend(frameon=False, fontsize=9)
    _save(fig, "03_payment_decomposition.png")


def fig_affordability_index(df):
    d = df.dropna(subset=["affordability_index"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(d.index, d["affordability_index"], color=ACCENT, lw=2.2)
    ax.axhline(100, color=INK, lw=1.0, ls="--")
    ax.annotate("100 = median young household\nexactly qualifies",
                xy=(d.index.min() + 1, 100), xytext=(0, 8),
                textcoords="offset points", fontsize=8, color=INK)
    ax.fill_between(d.index, d["affordability_index"], 100,
                    where=d["affordability_index"] < 100, color=ACCENT, alpha=0.10)
    ax.set_title("Affordability index for householders age 25-34")
    ax.set_ylabel("Index (100 = can just afford median home)")
    _save(fig, "04_affordability_index.png")


def fig_homeownership(df):
    d = df.dropna(subset=["hor_under_35"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(d.index, d["hor_under_35"], color=ACCENT, lw=2.2, label="Under 35")
    ax.plot(d.index, d["hor_all"], color=COOL, lw=2.2, label="All ages")
    ax.set_title("Homeownership rate: under 35 vs all households")
    ax.set_ylabel("Percent of households owning")
    ax.legend(frameon=False, fontsize=9)
    _save(fig, "05_homeownership_by_age.png")


def fig_down_payment(df):
    d = df.dropna(subset=["years_to_save_down"])
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(d.index, d["years_to_save_down"], color=COOL, lw=2.2)
    ax.set_title(f"Years to save a {DOWN_PAYMENT_PCT:.0%} down payment "
                 f"(saving {SAVINGS_RATE:.0%} of gross income)")
    ax.set_ylabel("Years")
    _save(fig, "06_years_to_down_payment.png")


def print_findings(df, decomp):
    def g(year, col):
        return df.loc[year, col]

    print("\n" + "=" * 72)
    print("KEY FINDINGS (every number below is reproduced by this script)")
    print("=" * 72)

    last_income = int(df["income_young"].last_valid_index())
    last_mkt = int(df["monthly_piti"].last_valid_index())

    print(f"\n1. The payment, not the price, is what moved (2021 -> 2023):")
    print(f"   median price      ${g(2021,'median_price'):>10,.0f} -> ${g(2023,'median_price'):>10,.0f}"
          f"  ({(g(2023,'median_price')/g(2021,'median_price')-1)*100:+.1f}%)")
    print(f"   mortgage rate     {g(2021,'mortgage_rate'):>10.2f}% -> {g(2023,'mortgage_rate'):>10.2f}%"
          f"  ({(g(2023,'mortgage_rate')/g(2021,'mortgage_rate')-1)*100:+.1f}%)")
    print(f"   monthly payment   ${g(2021,'monthly_piti'):>10,.0f} -> ${g(2023,'monthly_piti'):>10,.0f}"
          f"  ({(g(2023,'monthly_piti')/g(2021,'monthly_piti')-1)*100:+.1f}%)")

    r = decomp.loc[2023]
    print(f"\n2. Decomposition of that ${r['total_change']:,.0f}/mo increase:")
    print(f"   higher prices     ${r['price_effect']:>8,.0f}/mo  ({r['price_effect_share']:.0f}%)")
    print(f"   higher rates      ${r['rate_effect']:>8,.0f}/mo  ({r['rate_effect_share']:.0f}%)")
    print(f"   interaction       ${r['interaction']:>8,.0f}/mo  ({r['interaction_share']:.0f}%)")

    print(f"\n3. Young households got a raise and still lost ground (2021 -> 2023):")
    print(f"   median income 25-34  ${g(2021,'income_young'):>9,.0f} -> ${g(2023,'income_young'):>9,.0f}"
          f"  ({(g(2023,'income_young')/g(2021,'income_young')-1)*100:+.1f}%)")
    print(f"   income required      ${g(2021,'required_income'):>9,.0f} -> ${g(2023,'required_income'):>9,.0f}"
          f"  ({(g(2023,'required_income')/g(2021,'required_income')-1)*100:+.1f}%)")
    print(f"   affordability index  {g(2021,'affordability_index'):>9.1f} -> {g(2023,'affordability_index'):>9.1f}")

    ai = df["affordability_index"].dropna()
    print(f"\n4. Affordability index context:")
    print(f"   peak   {ai.idxmax()}: {ai.max():.1f}")
    print(f"   1984 (13.9% rates): {g(1984,'affordability_index'):.1f}"
          f"   |  {last_income}: {g(last_income,'affordability_index'):.1f}")
    print(f"   NOTE: by the monthly-payment test the early 1980s were worse.")
    print(f"   But the down-payment hurdle is far larger now:")
    print(f"   years to save 20%   1984: {g(1984,'years_to_save_down'):.1f}"
          f"  ->  {last_income}: {g(last_income,'years_to_save_down'):.1f}")
    print(f"   price-to-income     1984: {g(1984,'price_to_income'):.1f}"
          f"  ->  {last_income}: {g(last_income,'price_to_income'):.1f}")

    print(f"\n5. Outcome: homeownership under 35")
    hor = df["hor_under_35"].dropna()
    print(f"   1994: {hor.loc[1994]:.1f}%   peak {hor.idxmax()}: {hor.max():.1f}%"
          f"   {int(hor.index.max())}: {hor.iloc[-1]:.1f}%")
    print(f"   Still below its 1994 level after three decades.")

    print(f"\n   Data coverage: market data through {last_mkt}; "
          f"income data through {last_income} (Census CPS lag).")
    print("=" * 72)


def main() -> int:
    df = pd.read_csv(PROCESSED / "affordability.csv", index_col="year")
    decomp = pd.read_csv(PROCESSED / "payment_decomposition.csv", index_col="year")

    print("Writing figures...")
    fig_income_vs_required(df)
    fig_price_vs_payment(df)
    fig_decomposition(decomp)
    fig_affordability_index(df)
    fig_homeownership(df)
    fig_down_payment(df)

    print_findings(df, decomp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
