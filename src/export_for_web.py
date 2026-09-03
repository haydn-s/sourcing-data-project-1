"""Export processed data into JSON files for the web UI.

Creates `web/data/<category>.json` containing each processed dataset assigned
to one of three categories so the static HTML can load and render plots.
"""
from pathlib import Path
import json
import pandas as pd

from config import ROOT, PROCESSED


CATEGORY_MAP = {
    "macro_trends": [
        "fred_monthly.csv",
        "annual_panel.csv",
    ],
    "housing_market": [
        "homeownership_age.csv",
        "affordability.csv",
        "annual_panel.csv",
    ],
    "consumer_debt": [
        "payment_decomposition.csv",
        "annual_panel.csv",
    ],
}


def _rowify(df: pd.DataFrame):
    records = []
    for r in df.to_dict(orient="records"):
        clean = {}
        for k, v in r.items():
            # pandas Timestamp -> ISO string
            if pd.isna(v):
                clean[k] = None
                continue
            if hasattr(v, "isoformat"):
                clean[k] = v.isoformat()
                continue
            try:
                # numpy types -> native python
                if hasattr(v, "item"):
                    clean[k] = v.item()
                else:
                    clean[k] = v
            except Exception:
                clean[k] = None
        records.append(clean)
    return records


def export(target_dir: Path = None) -> None:
    target = target_dir or (ROOT / "web" / "data")
    target.mkdir(parents=True, exist_ok=True)

    for category, files in CATEGORY_MAP.items():
        out = []
        for fname in files:
            path = PROCESSED / fname
            if not path.exists():
                continue
            try:
                df = pd.read_csv(path, parse_dates=True)
            except Exception:
                df = pd.read_csv(path)
            dataset = {
                "name": fname,
                "columns": list(df.columns),
                "records": _rowify(df),
            }
            out.append(dataset)

        with open(target / f"{category}.json", "w", encoding="utf8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)


def main() -> int:
    export()
    print("Exported web JSON files to web/data/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
