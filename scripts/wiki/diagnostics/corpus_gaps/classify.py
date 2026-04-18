#!/usr/bin/env python3
"""Render gap categories from an existing coverage map."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from wiki.diagnostics.corpus_gaps.audit import (
    COVERAGE_MAP_PATH,
    GAP_CATEGORIES_PATH,
    classify_gap_categories,
    load_json,
    render_gap_categories_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coverage-map",
        default=str(COVERAGE_MAP_PATH),
        help=f"Path to coverage_map.json (default: {COVERAGE_MAP_PATH})",
    )
    parser.add_argument(
        "--output",
        default=str(GAP_CATEGORIES_PATH),
        help=f"Path to gap_categories.md (default: {GAP_CATEGORIES_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    coverage_map = load_json(Path(args.coverage_map))
    categories = classify_gap_categories(coverage_map)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_gap_categories_markdown(coverage_map, categories), encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
