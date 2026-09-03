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
    HIGH_RATE_ERA_YEAR,
    HOR_BASE_YEAR,
    INDEX_BASE_YEAR,
    PROCESSED,
    REAL_DOLLAR_BASE_YEAR,
    SAVINGS_RATE,
    SHOCK_END_YEAR,
    SHOCK_START_YEAR,
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
    yr = SHOCK_END_YEAR
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
    """Over 20 years price and payment land in the same place. The gap is recent.

    An earlier version of this chart indexed at 2015, which made the two look
    permanently divergent. They are not: from 2005 the median price is up ~73%
    and the payment on it ~80%. What is real is the *post-2021* split, so the
    chart shows the whole window and shades the shock instead of picking the
    base year that flatters the claim.
    """
    base_yr = INDEX_BASE_YEAR
    d = df.loc[base_yr:].dropna(subset=["median_price", "monthly_piti"])
    price = d["median_price"] / d.loc[base_yr, "median_price"] * 100
    pay = d["monthly_piti"] / d.loc[base_yr, "monthly_piti"] * 100

    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    shock, last = SHOCK_START_YEAR, int(d.index.max())

    # Shade the shock window -- the span the divergence actually belongs to.
    ax.axvspan(shock, last, color=ACCENT, alpha=0.055, lw=0)
    ax.plot(d.index, price, color=COOL, lw=2.2, label="Median home price")
    ax.plot(d.index, pay, color=ACCENT, lw=2.2, label="Monthly payment on that home")
    ax.axhline(100, color=MUTED, lw=0.9, ls=(0, (4, 3)))

    for series, color in ((pay, ACCENT), (price, COOL)):
        ax.annotate(f"+{series.loc[last] - 100:.0f}%",
                    xy=(last, series.loc[last]), xytext=(5, 0),
                    textcoords="offset points", color=color, fontsize=9,
                    fontweight="bold", va="center", ha="left",
                    annotation_clip=False)

    # The claim this chart is actually making, stated over the span it holds on.
    dp = (d.loc[last, "median_price"] / d.loc[shock, "median_price"] - 1) * 100
    dy = (d.loc[last, "monthly_piti"] / d.loc[shock, "monthly_piti"] - 1) * 100
    ax.annotate(f"Since {shock}:\nprice +{dp:.0f}%, payment +{dy:.0f}%",
                xy=(shock + (last - shock) / 2, 0.06),
                xycoords=ax.get_xaxis_transform(), fontsize=8.5, color=INK,
                ha="center", va="bottom")

    ax.set_title(f"Over two decades they land together. The gap opens after {shock}.")
    ax.set_ylabel(f"Index, {base_yr} = 100")
    _style(ax, xlim=(base_yr, last + 0.9))
    ax.set_xticks(range(base_yr, last + 1, 3))
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

    peak_yr, trough_yr = int(ai.idxmax()), SHOCK_END_YEAR
    era, era_rate = HIGH_RATE_ERA_YEAR, d.loc[HIGH_RATE_ERA_YEAR, "mortgage_rate"]
    for yr, txt, off in ((peak_yr, f"{peak_yr} peak: {ai.loc[peak_yr]:.0f}", (0, 11)),
                         (trough_yr, f"{trough_yr}: {ai.loc[trough_yr]:.0f}", (0, -20)),
                         (era, f"{era}: {ai.loc[era]:.0f}\n(rates near {era_rate:.0f}%)", (7, -6))):
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
    ref = u.loc[HOR_BASE_YEAR]
    ax1.axhline(ref, color=MUTED, lw=1.0, ls=(0, (4, 3)))
    ax1.plot(d.index, u, color=ACCENT, lw=2.2)
    ax1.fill_between(d.index, u, ref, where=u < ref, color=ACCENT, alpha=0.10, lw=0)

    peak_yr, last_yr = int(u.idxmax()), int(d.index.max())
    for yr, txt, off in ((HOR_BASE_YEAR, f"{HOR_BASE_YEAR}: {ref:.1f}%", (7, -15)),
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


def fig_decomposition_sensitivity(sens):
    """Where the price/rate crossover sits, and how far inflation moves it.

    Two panels sharing an anchor-year axis, each plotting the two effects in
    dollars per month rather than as shares. Dollars because once real prices
    start falling the two effects take opposite signs, and percentage shares of
    a total then run past 100 and below zero -- readable arithmetic, unreadable
    chart. The crossover -- where the rate line passes the price line -- is the
    finding, and it sits eight years earlier once inflation is taken out.
    """
    d = sens.sort_index()
    end_year = int(d["end_year"].iloc[0])

    fig, axes = plt.subplots(2, 1, figsize=(8.4, 7.0), sharex=True,
                             layout="constrained")

    panels = (
        (axes[0], "", "Nominal dollars",
         "Counts inflation as house-price growth"),
        (axes[1], "real_", f"Constant {REAL_DOLLAR_BASE_YEAR} dollars",
         "Real appreciation only -- the affordability-relevant split"),
    )

    for ax, prefix, title, subtitle in panels:
        price = d[f"{prefix}price_effect"]
        rate = d[f"{prefix}rate_effect"]

        # Shade the anchors from which rates are the larger factor.
        rate_wins = rate > price
        ax.fill_between(d.index, 0, 1, where=rate_wins, transform=ax.get_xaxis_transform(),
                        color=ACCENT, alpha=0.055, lw=0)

        ax.axhline(0, color=MUTED, lw=0.9)
        ax.plot(d.index, price, color=COOL, lw=2.2, label="Higher prices")
        ax.plot(d.index, rate, color=ACCENT, lw=2.2, label="Higher interest rates")

        # The crossover: first anchor from which rates carry more of the rise.
        if rate_wins.any():
            cross = int(d.index[rate_wins].min())
            ax.axvline(cross, color=INK, lw=1.0, ls=(0, (4, 3)))
            # Flip the label inside the axes when the crossover sits near the
            # right edge, or it is written off the end of the panel.
            span = d.index.max() - d.index.min()
            late = (cross - d.index.min()) / span > 0.7
            ax.annotate(f"rates take over\nfrom {cross}", xy=(cross, 0.94),
                        xycoords=ax.get_xaxis_transform(),
                        xytext=(-6 if late else 6, 0),
                        textcoords="offset points", fontsize=8.5, color=INK,
                        ha="right" if late else "left", va="top")

        ax.set_title(title, loc="left", pad=22)
        ax.annotate(subtitle, xy=(0, 1), xycoords="axes fraction", xytext=(0, 7),
                    textcoords="offset points", fontsize=9, color=MUTED,
                    ha="left", va="bottom")
        ax.set_ylabel("Added $/month")
        _dollars(ax)
        _style(ax, xlim=(d.index.min(), d.index.max()))

    # Inside the top panel: the two lines are far apart at the left edge, so the
    # band between them is the one place the legend collides with neither them,
    # the crossover labels, nor the source footer under the figure.
    axes[0].legend(frameon=False, loc="center left")
    axes[1].set_xlabel("Anchor year the comparison starts from")
    axes[1].set_xticks(range(d.index.min(), d.index.max() + 1, 2))

    fig.suptitle("Was it prices or rates? It depends on when you start "
                 "-- and on whether\nyou count inflation as house-price growth",
                 fontsize=12, fontweight="bold", ha="left", x=0.008)
    _save(fig, "07_decomposition_sensitivity.png",
          f"Each x-value re-runs the split from that anchor through {end_year}. "
          f"Deflating moves the crossover eight years earlier.")


def print_findings(df, decomp, sens):
    def g(year, col):
        return df.loc[year, col]

    print("\n" + "=" * 72)
    print("KEY FINDINGS (every number below is reproduced by this script)")
    print("=" * 72)

    last_income = int(df["income_young"].last_valid_index())
    last_mkt = int(df["monthly_piti"].last_valid_index())

    start, end = SHOCK_START_YEAR, SHOCK_END_YEAR

    def pct_change(col):
        return (g(end, col) / g(start, col) - 1) * 100

    print(f"\n1. The payment, not the price, is what moved ({start} -> {end}):")
    print(f"   median price      ${g(start,'median_price'):>10,.0f} -> ${g(end,'median_price'):>10,.0f}"
          f"  ({pct_change('median_price'):+.1f}%)")
    print(f"   mortgage rate     {g(start,'mortgage_rate'):>10.2f}% -> {g(end,'mortgage_rate'):>10.2f}%"
          f"  ({pct_change('mortgage_rate'):+.1f}%)")
    print(f"   monthly payment   ${g(start,'monthly_piti'):>10,.0f} -> ${g(end,'monthly_piti'):>10,.0f}"
          f"  ({pct_change('monthly_piti'):+.1f}%)")

    r = decomp.loc[end]
    print(f"\n2. Decomposition of that ${r['total_change']:,.0f}/mo increase:")
    print(f"   higher prices     ${r['price_effect']:>8,.0f}/mo  ({r['price_effect_share']:.0f}%)")
    print(f"   higher rates      ${r['rate_effect']:>8,.0f}/mo  ({r['rate_effect_share']:.0f}%)")
    print(f"   interaction       ${r['interaction']:>8,.0f}/mo  ({r['interaction_share']:.0f}%)")

    end_year = int(sens["end_year"].iloc[0])
    print(f"\n3. ROBUSTNESS: the split depends on the anchor -- and on inflation")
    print(f"   (effect on the monthly payment, each anchor -> {end_year})")
    print(f"   {'':>6}  {'nominal $/mo':>23}  {'constant-' + str(REAL_DOLLAR_BASE_YEAR) + ' $/mo':>23}")
    print(f"   {'from':>6}  {'price':>7} {'rate':>7} {'blames':>7}"
          f"  {'price':>7} {'rate':>7} {'blames':>7}")
    for yr, r in sens.iterrows():
        print(f"   {yr:>6}  {r['price_effect']:>7,.0f} {r['rate_effect']:>7,.0f} "
              f"{r['dominant_factor']:>7}  {r['real_price_effect']:>7,.0f} "
              f"{r['real_rate_effect']:>7,.0f} {r['real_dominant_factor']:>7}")

    def crossover(col):
        rate_led = sens.index[sens[col].eq("rate")]
        return int(rate_led.min()) if len(rate_led) else None

    nom_x, real_x = crossover("dominant_factor"), crossover("real_dominant_factor")
    cpi_growth = (df.loc[end_year, "cpi"] / df.loc[sens.index.min() + 1, "cpi"] - 1) * 100
    print(f"   crossover: rates lead from {nom_x} in nominal terms, "
          f"but from {real_x} once deflated.")
    print(f"   Over this window most nominal \"price growth\" is simply CPI "
          f"(+{cpi_growth:.0f}% since {sens.index.min() + 1}).")
    print(f"   Deflated, rates are the larger factor from {real_x} on -- which is the")
    print(f"   affordability-relevant reading, and it supports the rates story more")
    print(f"   strongly than the {SHOCK_START_YEAR} anchor alone ever did.")

    print(f"\n4. Young households got a raise and still lost ground ({start} -> {end}):")
    print(f"   median income 25-34  ${g(start,'income_young'):>9,.0f} -> ${g(end,'income_young'):>9,.0f}"
          f"  ({pct_change('income_young'):+.1f}%)")
    print(f"   income required      ${g(start,'required_income'):>9,.0f} -> ${g(end,'required_income'):>9,.0f}"
          f"  ({pct_change('required_income'):+.1f}%)")
    print(f"   affordability index  {g(start,'affordability_index'):>9.1f} -> {g(end,'affordability_index'):>9.1f}")
    print(f"   and by {last_income} it had recovered only to "
          f"{g(last_income,'affordability_index'):.1f} -- still short of qualifying.")

    ai = df["affordability_index"].dropna()
    print(f"\n5. Affordability index context:")
    print(f"   peak   {ai.idxmax()}: {ai.max():.1f}")
    era = HIGH_RATE_ERA_YEAR
    print(f"   {era} ({g(era,'mortgage_rate'):.1f}% rates): {g(era,'affordability_index'):.1f}"
          f"   |  {last_income}: {g(last_income,'affordability_index'):.1f}")
    print(f"   NOTE: by the monthly-payment test the early 1980s were worse.")
    print(f"   But the down-payment hurdle is far larger now:")
    print(f"   years to save 20%   {era}: {g(era,'years_to_save_down'):.1f}"
          f"  ->  {last_income}: {g(last_income,'years_to_save_down'):.1f}")
    print(f"   price-to-income     {era}: {g(era,'price_to_income'):.1f}"
          f"  ->  {last_income}: {g(last_income,'price_to_income'):.1f}")

    print(f"\n6. Outcome: homeownership under 35")
    hor = df["hor_under_35"].dropna()
    print(f"   {HOR_BASE_YEAR}: {hor.loc[HOR_BASE_YEAR]:.1f}%   peak {hor.idxmax()}: {hor.max():.1f}%"
          f"   {int(hor.index.max())}: {hor.iloc[-1]:.1f}%")
    print(f"   Still below its {HOR_BASE_YEAR} level after three decades.")

    print(f"\n   Data coverage: market data through {last_mkt}; "
          f"income data through {last_income} (Census CPS lag).")
    print("=" * 72)


def main() -> int:
    df = pd.read_csv(PROCESSED / "affordability.csv", index_col="year")
    decomp = pd.read_csv(PROCESSED / "payment_decomposition.csv", index_col="year")
    sens = pd.read_csv(PROCESSED / "decomposition_sensitivity.csv", index_col="base_year")

    print("Writing figures...")
    fig_income_vs_required(df)
    fig_price_vs_payment(df)
    fig_decomposition(decomp)
    fig_affordability_index(df)
    fig_homeownership(df)
    fig_down_payment(df)
    fig_decomposition_sensitivity(sens)

    print_findings(df, decomp, sens)
    return 0


if __name__ == "__main__":
    sys.exit(main())
