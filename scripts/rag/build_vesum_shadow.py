#!/usr/bin/env python3
"""Build and validate a marker-preserving VESUM shadow database.

The command never activates a production dictionary.  It downloads the pinned
v6.8.0 asset unless ``--asset`` supplies an already-downloaded copy, verifies
that asset against the committed lock, and writes only an explicit shadow path.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.vesum_reingest import DEFAULT_LOCK_PATH, build_from_lock


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="Explicit shadow SQLite output path")
    parser.add_argument(
        "--fixture-manifest",
        required=True,
        type=Path,
        help="Path where the source-derived fixture manifest is written",
    )
    parser.add_argument("--lock", default=DEFAULT_LOCK_PATH, type=Path, help="Pinned source lock")
    parser.add_argument(
        "--asset",
        type=Path,
        help="Optional cached release asset; it is still verified against --lock",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Release-asset cache directory when --asset is not supplied",
    )
    args = parser.parse_args()

    summary = build_from_lock(
        args.lock,
        args.output,
        args.fixture_manifest,
        asset_path=args.asset,
        cache_dir=args.cache_dir,
    )
    print(json.dumps(summary.as_lock_expected(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
