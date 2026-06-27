#!/usr/bin/env python3
"""Generate gated Atlas-entry candidates from a newline-delimited lemma file.

Run from the repository root:

.venv/bin/python -m scripts.audit.grow_lexicon_from_lemmas \
  --lemmas-file .agent/tmp/krisztian-doc-lemmas.txt \
  --limit 800 \
  --out .agent/tmp/doc-candidates-800.json \
  --report
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts.lexicon import enrich_manifest
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT
from scripts.lexicon.grow_lexicon_from_content import (
    _preserve_wiki_reference_cache,
    _source_connection,
    build_payload,
    build_skeleton_entry,
    format_report,
    split_candidates,
    write_candidates,
)
from scripts.lexicon.lemma_normalization import strip_acute_stress

DEFAULT_OUT = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates_from_lemmas.json"


def read_lemmas(path: Path) -> list[str]:
    """Read non-empty stripped lemmas from a newline-delimited file."""
    lemmas: list[str] = []
    seen: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        lemma = strip_acute_stress(line.strip())
        if not lemma or lemma in seen:
            continue
        seen.add(lemma)
        lemmas.append(lemma)
    return lemmas


def generate_candidates(
    *,
    lemmas_file: Path,
    limit: int | None = None,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Generate, write, and return gated Atlas-entry candidates."""
    lemmas = read_lemmas(lemmas_file)
    delta = _limited_lemmas(lemmas, limit)

    entries: list[dict[str, Any]] = []
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    with _source_connection(enrich_manifest.SOURCES_DB) as conn, _preserve_wiki_reference_cache():
        has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for lemma in delta:
            entry = build_skeleton_entry(lemma)
            enrich_manifest.enrich_entry(
                entry,
                conn,
                kaikki_lookup,
                has_sum11_flags=has_sum11_flags,
            )
            entries.append(entry)

    auto_merge, needs_review = split_candidates(entries)
    payload = build_payload(
        total_delta=len(lemmas),
        processed=len(delta),
        auto_merge=auto_merge,
        needs_review=needs_review,
        limit=limit,
    )
    write_candidates(payload, out)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate gated Atlas-entry candidates from newline-delimited lemmas.")
    parser.add_argument("--lemmas-file", type=Path, required=True, help="One lemma per line")
    parser.add_argument("--limit", type=int, help="Limit processed lemmas")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Candidate JSON output path (default: {DEFAULT_OUT.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument("--report", action="store_true", help="Print candidate bucket counts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    try:
        payload = generate_candidates(lemmas_file=args.lemmas_file, limit=args.limit, out=args.out)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print(format_report(payload))
    return 0


def _limited_lemmas(items: Sequence[str], limit: int | None) -> Sequence[str]:
    if limit is None:
        return items
    return items[:limit]


if __name__ == "__main__":
    raise SystemExit(main())
