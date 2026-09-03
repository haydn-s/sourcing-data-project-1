"""Run the full pipeline end to end: ingest -> clean -> features -> EDA.

    python src/run_all.py            # reuse already-downloaded raw data
    python src/run_all.py --refresh  # re-download every source first
"""

import argparse
import sys

import clean
import eda
import features
import ingest
import export_for_web


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh", action="store_true",
                    help="re-download raw data from FRED and Census")
    args = ap.parse_args()

    steps = [
        ("INGEST   downloading raw sources", lambda: ingest.main_with(args.refresh)),
        ("CLEAN    building tidy panels", clean.main),
        ("FEATURES engineering affordability metrics", features.main),
        ("EDA      figures and findings", eda.main),
        ("WEB      export JSON for web UI", export_for_web.main),
    ]
    for title, fn in steps:
        print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
        rc = fn()
        if rc:
            print(f"step failed: {title}")
            return rc

    print("\nPipeline complete. See figures/ and data/processed/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
