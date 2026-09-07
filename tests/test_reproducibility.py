"""The committed outputs must be what the committed code produces.

This guards against a real and easy mistake: changing a formula or an assumption
in config.py, and committing the code without re-running the pipeline — so the
figures and the README quote numbers the code no longer produces.

**Why this is not a byte comparison.** It used to be: a CI step regenerated the
CSVs and ran `git diff --exit-code`. That failed permanently, because the check
demanded bit-identical floating point across machines. `piti()` raises `(1+r)`
to the 360th power, and the last unit in the last place of `pow` differs between
macOS ARM64 and the Linux x86-64 runner; pinning pandas and numpy pins neither
the CPU nor libm. Writing 17 significant digits to CSV then preserves the
difference, and every one of the 17 rows in decomposition_sensitivity.csv moved.

So the comparison is numeric with a tight relative tolerance. 1e-9 is many
orders of magnitude looser than platform noise (~1e-13 relative) and many orders
tighter than any real change: altering a rate, a DTI ratio or a formula moves
these values by whole percent, not by billionths.
"""

import json
import re

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from config import PROCESSED, ROOT
from features import (
    build_affordability,
    decompose_payment_change,
    decompose_sensitivity,
)

pytestmark = pytest.mark.requires_data

# Loose enough to absorb cross-platform float noise, tight enough that any
# real change to the model fails loudly.
RTOL = 1e-9


def _committed(name, index_col="year"):
    path = PROCESSED / name
    if not path.exists():
        pytest.skip(f"run `python src/run_all.py` first; missing {name}")
    return pd.read_csv(path, index_col=index_col)


@pytest.fixture(scope="module")
def annual():
    return _committed("annual_panel.csv")


def _same(committed, regenerated, name):
    assert list(committed.columns) == list(regenerated.columns), (
        f"{name}: columns differ — regenerate with `python src/run_all.py`.\n"
        f"  only committed: {sorted(set(committed.columns) - set(regenerated.columns))}\n"
        f"  only produced:  {sorted(set(regenerated.columns) - set(committed.columns))}")
    assert list(committed.index) == list(regenerated.index), \
        f"{name}: row index differs — regenerate with `python src/run_all.py`"
    assert_frame_equal(committed, regenerated, check_exact=False,
                       rtol=RTOL, check_dtype=False, obj=name)


def test_affordability_csv_matches_the_code(annual):
    _same(_committed("affordability.csv"), build_affordability(annual),
          "affordability.csv")


def test_payment_decomposition_matches_the_code(annual):
    _same(_committed("payment_decomposition.csv"),
          decompose_payment_change(build_affordability(annual)),
          "payment_decomposition.csv")


def test_decomposition_sensitivity_matches_the_code(annual):
    _same(_committed("decomposition_sensitivity.csv", index_col="base_year"),
          decompose_sensitivity(build_affordability(annual)),
          "decomposition_sensitivity.csv")


# ------------------------------------------------------------------ web export

def test_exported_json_covers_every_source_table():
    """The viewer's JSON is generated from the processed CSVs. Byte-comparing it
    would inherit the same float problem, so check the structure instead: every
    table the exporter is configured to publish must be present, with the same
    columns and row count as the CSV it came from."""
    import export_for_web

    published = {}
    for category in export_for_web.CATEGORY_MAP:
        path = ROOT / "web" / "data" / f"{category}.json"
        if not path.exists():
            pytest.skip("run `python src/run_all.py` first; web/data is missing")
        for ds in json.loads(path.read_text()):
            published[ds["name"]] = ds

    for category, files in export_for_web.CATEGORY_MAP.items():
        for fname in files:
            assert fname in published, \
                f"{fname} is in CATEGORY_MAP but absent from {category}.json — re-export"
            source = pd.read_csv(PROCESSED / fname)
            ds = published[fname]
            assert list(ds["columns"]) == list(source.columns), \
                f"{fname}: exported columns are stale — re-export"
            assert len(ds["records"]) == len(source), \
                f"{fname}: exported row count is stale — re-export"


def test_readme_documents_every_processed_table():
    """A new processed table that nothing documents is a table nobody can use."""
    readme = (ROOT / "README.md").read_text()
    for path in sorted(PROCESSED.glob("*.csv")):
        assert re.search(rf"\b{re.escape(path.name)}\b", readme), \
            f"{path.name} is generated but never mentioned in the README"
