"""Download every raw input from its primary source.

Writes untouched source files to data/raw/. Downloads are resumable: a series
whose CSV already exists is skipped unless --force is passed, so a run
interrupted by FRED throttling can simply be re-run.

Usage:
    python src/ingest.py            # fetch anything missing
    python src/ingest.py --force    # re-download everything
"""

import argparse
import sys
import time

import requests

from config import (
    CENSUS_H10_FILE,
    CENSUS_H10_URL,
    CENSUS_HVS_TAB19_FILE,
    CENSUS_HVS_TAB19_URL,
    FRED_CSV_URL,
    FRED_SERIES,
    RAW_FRED,
    RAW_PARTNER,
)

TIMEOUT = 60

# NOTE: do not set a custom User-Agent here. fredgraph.csv refuses unrecognized
# UA strings (a custom "AIPI-510/1.0" and a spoofed browser UA both had their
# connections dropped every time), while the requests library default is served
# normally. We therefore send the library default and identify the project in
# the README instead. Retries remain for genuine transient network errors.
HEADERS = {"Connection": "close"}

POLITE_DELAY = 1.0
BACKOFF_SCHEDULE = (5, 15, 30)


def _get(url: str) -> bytes:
    last = None
    # The trailing None is the final attempt: try, then give up rather than sleep.
    for backoff in (*BACKOFF_SCHEDULE, None):
        try:
            # Connection: close — reused sockets are what FRED tends to drop.
            r = requests.get(url, timeout=TIMEOUT, headers=HEADERS)
            r.raise_for_status()
            return r.content
        except requests.RequestException as exc:
            last = exc
            if backoff is None:
                break
            print(f"      transient {type(exc).__name__}; retrying in {backoff}s")
            time.sleep(backoff)
    raise RuntimeError(f"failed to download {url}: {last}")


def fetch_fred(force: bool) -> None:
    RAW_FRED.mkdir(parents=True, exist_ok=True)
    for series_id, (label, freq, _units) in FRED_SERIES.items():
        dest = RAW_FRED / f"{series_id}.csv"
        if dest.exists() and not force:
            print(f"  skip {series_id:<16} (already present)")
            continue
        time.sleep(POLITE_DELAY)
        content = _get(FRED_CSV_URL.format(series_id=series_id))
        dest.write_bytes(content)
        n = content.count(b"\n") - 1
        print(f"  FRED {series_id:<16} {n:>6} obs  {freq:<9} {label}")


def fetch_census(force: bool) -> None:
    RAW_PARTNER.mkdir(parents=True, exist_ok=True)
    for label, url, filename in (
        ("HVS Table 19 (homeownership by age)", CENSUS_HVS_TAB19_URL, CENSUS_HVS_TAB19_FILE),
        ("CPS Table H-10 (income by age)", CENSUS_H10_URL, CENSUS_H10_FILE),
    ):
        dest = RAW_PARTNER / filename
        if dest.exists() and not force:
            print(f"  skip {dest.name} (already present)")
            continue
        time.sleep(POLITE_DELAY)
        dest.write_bytes(_get(url))
        print(f"  Census {label} -> {dest.name} ({dest.stat().st_size:,} bytes)")


def main_with(force: bool) -> int:
    """Programmatic entry point used by run_all.py."""
    print("Downloading FRED series...")
    fetch_fred(force)
    print("Downloading Census tables...")
    fetch_census(force)
    print("\nRaw data written to data/raw/")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    args = ap.parse_args()
    return main_with(args.force)


if __name__ == "__main__":
    sys.exit(main())
