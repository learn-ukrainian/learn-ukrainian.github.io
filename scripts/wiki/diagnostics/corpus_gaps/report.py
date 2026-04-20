#!/usr/bin/env python3
"""Render the A1 corpus-coverage smoke-test report from existing audit data."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from wiki.diagnostics.corpus_gaps.audit import (
    A1_REPORT_PATH,
    ARTICLE_CONCEPTS_PATH,
    COVERAGE_MAP_PATH,
    classify_gap_categories,
    load_json,
    render_a1_report_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--article-concepts",
        default=str(ARTICLE_CONCEPTS_PATH),
        help=f"Path to article_concepts.json (default: {ARTICLE_CONCEPTS_PATH})",
    )
    parser.add_argument(
        "--coverage-map",
        default=str(COVERAGE_MAP_PATH),
        help=f"Path to coverage_map.json (default: {COVERAGE_MAP_PATH})",
    )
    parser.add_argument(
        "--output",
        default=str(A1_REPORT_PATH),
        help=f"Path to the markdown report (default: {A1_REPORT_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    article_concepts = load_json(Path(args.article_concepts))
    coverage_map = load_json(Path(args.coverage_map))
    categories = classify_gap_categories(coverage_map)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_a1_report_markdown(article_concepts, coverage_map, categories),
        encoding="utf-8",
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
