"""The figure layer: the partial-year footnote, and that every figure renders.

Most of eda.py is drawing code that can only really be judged by looking at the
output. Two things are worth pinning anyway: the footnote helper, which has real
branching and once mangled its own output, and a smoke test that all seven
figures still render from the committed data — the cheapest guard against an
edit to one figure breaking another through the shared helpers.
"""

import pandas as pd
import pytest

import eda
from eda import _partial_note


def _frame(flags):
    return pd.DataFrame({"is_partial_year": list(flags.values())},
                        index=pd.Index(list(flags), name="year"))


# ------------------------------------------------------------ partial-year note

def test_no_note_when_the_column_is_absent():
    assert _partial_note(pd.DataFrame(index=[2024, 2025])) is None


def test_no_note_when_every_year_is_complete():
    assert _partial_note(_frame({2024: False, 2025: False})) is None


def test_missing_flags_are_treated_as_complete():
    """A NaN in is_partial_year must not be read as truthy and footnoted."""
    df = pd.DataFrame({"is_partial_year": [None, False]}, index=[2024, 2025])
    assert _partial_note(df) is None


def test_single_partial_year_reads_as_singular():
    note = _partial_note(_frame({2025: False, 2026: True}))
    assert note == "2026 is a year-to-date average, not a full year."


def test_several_partial_years_read_as_plural():
    """The old wording said 'is a year-to-date average' however many it named."""
    note = _partial_note(_frame({2025: True, 2026: True}))
    assert note == "2025, 2026 are year-to-date averages, not full years."


def test_marker_is_applied_to_every_partial_year():
    """Figure 03 asterisks its partial tick labels and needs the footnote to
    match. The previous implementation rewrote the finished sentence and so
    only ever marked the first year."""
    note = _partial_note(_frame({2025: True, 2026: True}), marker="* ")
    assert note.startswith("* 2025, * 2026")
    assert note.count("*") == 2


def test_marker_defaults_to_nothing():
    assert _partial_note(_frame({2026: True}), marker="").startswith("2026")


# ----------------------------------------------------------------- smoke test

@pytest.mark.requires_data
def test_every_figure_renders(tmp_path, monkeypatch):
    """Draw all seven from the committed data, into a temp directory.

    Catches the failure mode this file exists for: the figures share _style,
    _save, _dollars and _partial_note, so a change made for one can raise in
    another, and nothing else in the suite would notice.
    """
    processed = eda.PROCESSED
    for name in ("affordability.csv", "payment_decomposition.csv",
                 "decomposition_sensitivity.csv"):
        if not (processed / name).exists():
            pytest.skip(f"run `python src/run_all.py` first; missing {name}")

    monkeypatch.setattr(eda, "FIGURES", tmp_path)
    df = pd.read_csv(processed / "affordability.csv", index_col="year")
    decomp = pd.read_csv(processed / "payment_decomposition.csv", index_col="year")
    sens = pd.read_csv(processed / "decomposition_sensitivity.csv",
                       index_col="base_year")

    eda.fig_income_vs_required(df)
    eda.fig_price_vs_payment(df)
    eda.fig_decomposition(decomp)
    eda.fig_affordability_index(df)
    eda.fig_homeownership(df)
    eda.fig_down_payment(df)
    eda.fig_decomposition_sensitivity(sens)

    written = sorted(p.name for p in tmp_path.glob("*.png"))
    assert len(written) == 7, f"expected 7 figures, got {written}"
    assert all((tmp_path / n).stat().st_size > 10_000 for n in written), \
        "a figure rendered suspiciously small — likely an empty axes"


@pytest.mark.requires_data
def test_findings_print_without_error(capsys, monkeypatch):
    """print_findings indexes named years directly, so a data refresh that drops
    one would raise here rather than in front of an audience."""
    processed = eda.PROCESSED
    if not (processed / "decomposition_sensitivity.csv").exists():
        pytest.skip("run `python src/run_all.py` first")

    df = pd.read_csv(processed / "affordability.csv", index_col="year")
    decomp = pd.read_csv(processed / "payment_decomposition.csv", index_col="year")
    sens = pd.read_csv(processed / "decomposition_sensitivity.csv",
                       index_col="base_year")

    eda.print_findings(df, decomp, sens)
    out = capsys.readouterr().out
    assert "KEY FINDINGS" in out
    # The six numbered findings must all be present and in order.
    assert [line.strip()[:2] for line in out.splitlines()
            if line.strip()[:2] in {f"{i}." for i in range(1, 7)}] == \
        [f"{i}." for i in range(1, 7)]
