"""Exploratory analysis: summary tables and the figures used in the story.

Writes PNGs to figures/ and prints the findings quoted in the podcast script,
so every number in the narrative is traceable to a command in this repo.
"""

import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
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
GRID = "#dfe3ea"

SOURCE = ("Sources: FRED (Freddie Mac PMMS, Census/HUD, BLS); "
          "U.S. Census Bureau HVS Table 19 and CPS ASEC Table H-10.")

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelcolor": INK,
    "axes.labelsize": 9.5,
    "axes.edgecolor": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.axisbelow": True,
    "text.color": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.autolayout": False,
})


def _style(ax, xlim=None):
    """Apply the shared grid/limit treatment every panel uses."""
    ax.grid(axis="y", color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    if xlim is not None:
        ax.set_xlim(*xlim)          # keep the axis tight to observed data
    return ax


def _label_point(ax, x, y, text, offset, color=INK):
    """Annotate a data point, aligning the text away from the point.

    A negative x-offset must right-align the text, otherwise it starts at the
    offset position and runs back across (or off) the edge of the axes.
    """
    ha = "center" if offset[0] == 0 else ("right" if offset[0] < 0 else "left")
    ax.annotate(text, xy=(x, y), xytext=offset, textcoords="offset points",
                fontsize=8.5, color=color, ha=ha)


def _dollars(ax, thousands=False):
    if thousands:
        ax.yaxis.set_major_formatter(lambda v, _: f"${v/1000:,.0f}k")
    else:
        ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}")


def _partial_note(df):
    """Footnote text naming any year built from less than 12 months of data."""
    if "is_partial_year" not in df:
        return None
    partial = df.index[df["is_partial_year"].fillna(False).astype(bool)]
    if not len(partial):
        return None
    yrs = ", ".join(str(y) for y in partial)
    return f"{yrs} is a year-to-date average, not a full year."


def _save(fig, name, note=None):
    """Add the source footer (plus any caveat) and write the file."""
    # constrained layout handles multi-panel gridspecs that tight_layout warns on
    if fig.get_layout_engine() is None:
        fig.tight_layout()
    footer = SOURCE if note is None else f"Note: {note}  |  {SOURCE}"
    fig.text(0.005, -0.01, footer, fontsize=7, color=MUTED,
             ha="left", va="top", wrap=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / name
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  figures/{name}")


def fig_income_vs_required(df):
    """The scissors: what a buyer earns vs what a lender requires."""
    d = df.dropna(subset=["income_young", "required_income_real2024"])
    req, inc = d["required_income_real2024"], d["income_young_real2024"]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))

    ax.fill_between(d.index, inc, req, where=req > inc,
                    color=ACCENT, alpha=0.10, lw=0)
    ax.plot(d.index, req, color=ACCENT, lw=2.2,
            label=f"Income a lender requires (at {FRONT_END_DTI:.0%} of gross)")
    ax.plot(d.index, inc, color=COOL, lw=2.2,
            label="Actual median income, householder age 25-34")

    # Direct end labels beat arrows here: the series are far apart at the right
    # edge, so a leader line would only add ink.
    last = int(d.index.max())
    for series, color in ((req, ACCENT), (inc, COOL)):
        ax.annotate(f"${series.loc[last]/1000:.0f}k", xy=(last, series.loc[last]),
                    xytext=(5, 0), textcoords="offset points", color=color,
                    fontsize=9, fontweight="bold", va="center", ha="left",
                    annotation_clip=False)

    # One vertical connector marking the widest recent gap, labelled to its left
    # so it can never collide with the right edge.
    yr = 2023
    lo, hi = inc.loc[yr], req.loc[yr]
    ax.annotate("", xy=(yr, hi), xytext=(yr, lo),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
    # Sit the label in the open area left of the spike; directly beside the
    # connector it would be crossed by the steeply rising required-income line.
    ax.annotate(f"{yr}: ${(hi - lo)/1000:.0f}k\nshort of qualifying",
                xy=(yr - 5.5, (hi + lo) / 2 * 1.04), fontsize=8.5, color=INK,
                ha="center", va="center")

    ax.set_title("The qualifying gap: what young buyers earn vs what banks require")
    ax.set_ylabel("Annual income (2024 dollars)")
    _dollars(ax, thousands=True)
    _style(ax, xlim=(d.index.min(), last + 1.6))
    ax.legend(frameon=False, loc="upper left")
    _save(fig, "01_income_vs_required.png", _partial_note(d))


def fig_price_vs_payment(df):
    """Prices barely moved after 2021; the payment exploded."""
    d = df.loc[2015:].dropna(subset=["median_price", "monthly_piti"])
    base = d.loc[2015]
    price = d["median_price"] / base["median_price"] * 100
    pay = d["monthly_piti"] / base["monthly_piti"] * 100

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.fill_between(d.index, price, pay, where=pay > price,
                    color=ACCENT, alpha=0.10, lw=0)
    ax.plot(d.index, price, color=COOL, lw=2.2, label="Median home price")
    ax.plot(d.index, pay, color=ACCENT, lw=2.2, label="Monthly payment on that home")
    ax.axhline(100, color=MUTED, lw=0.9, ls=(0, (4, 3)))

    # Label the endpoints so the divergence is readable without the axis.
    last = d.index.max()
    for series, color in ((pay, ACCENT), (price, COOL)):
        ax.annotate(f"+{series.loc[last] - 100:.0f}%",
                    xy=(last, series.loc[last]), xytext=(5, 0),
                    textcoords="offset points", color=color, fontsize=9,
                    fontweight="bold", va="center", ha="left",
                    annotation_clip=False)

    ax.set_title("Same house, two very different stories (2015 = 100)")
    ax.set_ylabel("Index, 2015 = 100")
    _style(ax, xlim=(2015, last + 0.55))
    ax.set_xticks(range(2015, last + 1, 2))
    ax.legend(frameon=False, loc="upper left")
    _save(fig, "02_price_vs_payment.png", _partial_note(d))


def fig_decomposition(decomp):
    """How much of the payment jump was price, and how much was the rate."""
    d = decomp.loc[DECOMP_BASE_YEAR + 1:].dropna(subset=["total_change"])
    fig, ax = plt.subplots(figsize=(8, 4.6))

    ax.bar(d.index, d["price_effect"], color=COOL, label="Higher prices", width=0.62)
    ax.bar(d.index, d["rate_effect"], bottom=d["price_effect"],
           color=ACCENT, label="Higher interest rates", width=0.62)
    ax.bar(d.index, d["interaction"],
           bottom=d["price_effect"] + d["rate_effect"],
           color=MUTED, label="Interaction", width=0.62)

    # Put the rate share inside the red block; it is the headline of the chart.
    for yr in d.index:
        r = d.loc[yr]
        ax.text(yr, r["price_effect"] + r["rate_effect"] / 2,
                f"{r['rate_effect_share']:.0f}%", ha="center", va="center",
                color="white", fontsize=9, fontweight="bold")
        ax.text(yr, r["total_change"] + 18, f"${r['total_change']:,.0f}",
                ha="center", va="bottom", color=INK, fontsize=8.5)

    ax.set_title(f"What actually drove the payment increase since {DECOMP_BASE_YEAR}")
    ax.set_ylabel(f"Added monthly cost vs {DECOMP_BASE_YEAR}")
    _dollars(ax)
    _style(ax)
    ax.set_ylim(0, d["total_change"].max() * 1.18)
    partial = d["is_partial_year"].fillna(False).astype(bool)
    ax.set_xticks(list(d.index))
    ax.set_xticklabels([f"{y}*" if p else str(y) for y, p in zip(d.index, partial)])
    ax.legend(frameon=False, loc="upper right", ncol=1)
    note = _partial_note(d)
    _save(fig, "03_payment_decomposition.png",
          note.replace(str(d.index[partial][0]), f"* {d.index[partial][0]}")
          if note and partial.any() else note)


def fig_affordability_index(df):
    d = df.dropna(subset=["affordability_index"])
    ai = d["affordability_index"]
    fig, ax = plt.subplots(figsize=(8, 4.6))

    # No shaded band: nearly every year sits below 100, so filling that region
    # tints the whole panel without distinguishing anything. The threshold line
    # alone carries the meaning.
    ax.axhline(100, color=INK, lw=1.1, ls=(0, (4, 3)))
    ax.plot(d.index, ai, color=ACCENT, lw=2.2)

    peak_yr, trough_yr, last_yr = int(ai.idxmax()), 2023, int(d.index.max())
    for yr, txt, off in ((peak_yr, f"{peak_yr} peak: {ai.loc[peak_yr]:.0f}", (0, 11)),
                         (trough_yr, f"{trough_yr}: {ai.loc[trough_yr]:.0f}", (0, -20)),
                         (1984, f"1984: {ai.loc[1984]:.0f}\n(rates near 14%)", (7, -6))):
        ax.plot(yr, ai.loc[yr], "o", color=ACCENT, ms=5.5, zorder=5)
        _label_point(ax, yr, ai.loc[yr], txt, off)

    ax.text(d.index.min() + 0.5, 100.9, "100 = the median young household exactly qualifies",
            fontsize=8, color=INK, va="bottom")
    ax.set_title("Can the typical 25-34 household afford the typical home?")
    ax.set_ylabel("Affordability index")
    _style(ax, xlim=(d.index.min() - 0.8, d.index.max() + 1.0))
    ax.set_ylim(ai.min() - 4, max(ai.max(), 100) + 6)
    _save(fig, "04_affordability_index.png", _partial_note(d))


def fig_homeownership(df):
    """Two panels: a 28-point level gap makes a shared y-axis unreadable."""
    d = df.dropna(subset=["hor_under_35"])
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(8, 6.2), sharex=True, layout="constrained",
        gridspec_kw={"height_ratios": [1.35, 1]})

    u = d["hor_under_35"]
    ref = u.loc[1994]
    ax1.axhline(ref, color=MUTED, lw=1.0, ls=(0, (4, 3)))
    ax1.plot(d.index, u, color=ACCENT, lw=2.2)
    ax1.fill_between(d.index, u, ref, where=u < ref, color=ACCENT, alpha=0.10, lw=0)

    peak_yr, last_yr = int(u.idxmax()), int(d.index.max())
    for yr, txt, off in ((1994, f"1994: {ref:.1f}%", (7, -15)),
                         (peak_yr, f"{peak_yr} peak: {u.loc[peak_yr]:.1f}%", (0, 11)),
                         (last_yr, f"{last_yr}: {u.iloc[-1]:.1f}%", (-7, -18))):
        ax1.plot(yr, u.loc[yr], "o", color=ACCENT, ms=5.5, zorder=5)
        _label_point(ax1, yr, u.loc[yr], txt, off)

    ax1.set_title("Under 35: still below where it started three decades ago")
    ax1.set_ylabel("Percent owning, under 35")
    ax1.set_ylim(u.min() - 1.6, u.max() + 2.2)
    _style(ax1)

    a = d["hor_all"]
    ax2.plot(d.index, a, color=COOL, lw=2.2)
    ax2.set_title("All households, for comparison", fontsize=10.5)
    ax2.set_ylabel("Percent owning, all ages")
    ax2.set_ylim(a.min() - 1.2, a.max() + 1.2)
    _style(ax2, xlim=(d.index.min(), d.index.max()))

    _save(fig, "05_homeownership_by_age.png", _partial_note(d))


def fig_down_payment(df):
    d = df.dropna(subset=["years_to_save_down"])
    y = d["years_to_save_down"]
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(d.index, y, color=COOL, lw=2.2)

    first_yr, last_yr = int(d.index.min()), int(d.index.max())
    # Both labels sit below their points: the series is flat at the left edge
    # and dips just above the right label's line, so above-placement collides.
    for yr, off in ((first_yr, (9, -13)), (last_yr, (-8, -30))):
        ax.plot(yr, y.loc[yr], "o", color=COOL, ms=5.5, zorder=5)
        _label_point(ax, yr, y.loc[yr], f"{yr}: {y.loc[yr]:.1f} years", off)

    ax.set_title(f"The barrier that got worse: years to save a "
                 f"{DOWN_PAYMENT_PCT:.0%} down payment")
    ax.set_ylabel(f"Years, saving {SAVINGS_RATE:.0%} of gross income")
    # Force whole-year ticks: the default 0.5 locator with a 0-decimal
    # formatter rendered duplicate labels ("10, 10, 10, 9, 9").
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}")
    _style(ax, xlim=(first_yr - 1.2, last_yr + 1.2))
    _save(fig, "06_years_to_down_payment.png", _partial_note(d))


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
