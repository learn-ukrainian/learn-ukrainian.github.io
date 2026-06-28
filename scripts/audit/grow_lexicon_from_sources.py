#!/usr/bin/env python3
"""Generate gated Atlas-entry candidates from curated source inventories.

Run from repository root:

    .venv/bin/python -m scripts.lexicon.grow_lexicon_from_sources \
        --inventory data/lexicon/source-inventory/ulp.yaml \
        --out data/lexicon/grow_candidates.json \
        --report
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts.audit.source_inventory_intake import (
    SourceInventoryCandidate,
    SourceInventoryError,
    read_source_inventories,
    source_inventory_candidates,
)
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

DEFAULT_OUT = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates_from_sources.json"
GENERATED_FROM = "source_inventory_intake.v1"
PRIMARY_SOURCE = "source_inventory_grow"


def generate_candidates(
    *,
    inventory_paths: Sequence[Path],
    limit: int | None = None,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Generate, enrich, split, and write source-fed Atlas candidates."""
    if not inventory_paths:
        raise SourceInventoryError("at least one --inventory file is required")

    records = read_source_inventories(inventory_paths, project_root=PROJECT_ROOT)
    candidates = source_inventory_candidates(records)
    delta = _limited_candidates(candidates, limit)

    entries: list[dict[str, Any]] = []
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    with _source_connection(enrich_manifest.SOURCES_DB) as conn, _preserve_wiki_reference_cache():
        has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for item in delta:
            entry = build_skeleton_entry(item.lemma)
            if item.pos and not entry.get("pos"):
                entry["pos"] = item.pos
            entry["primary_source"] = PRIMARY_SOURCE
            entry["source_provenance"] = list(item.source_provenance)
            enrich_manifest.enrich_entry(
                entry,
                conn,
                kaikki_lookup,
                has_sum11_flags=has_sum11_flags,
            )
            entries.append(entry)

    auto_merge, needs_review = split_candidates(entries)
    payload = build_payload(
        total_delta=len(candidates),
        processed=len(delta),
        auto_merge=auto_merge,
        needs_review=needs_review,
        limit=limit,
    )
    payload["generated_from"] = GENERATED_FROM
    write_candidates(payload, out)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Atlas candidates from source inventories.")
    parser.add_argument(
        "--inventory",
        dest="inventory_paths",
        action="append",
        type=Path,
        required=True,
        help="Curated source inventory file (repeat for multiple files).",
    )
    parser.add_argument("--limit", type=int, help="Limit processed source headwords")
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
        payload = generate_candidates(
            inventory_paths=args.inventory_paths,
            limit=args.limit,
            out=args.out,
        )
    except (FileNotFoundError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print(format_report(payload))
    return 0


def _limited_candidates(
    items: Sequence[SourceInventoryCandidate],
    limit: int | None,
) -> Sequence[SourceInventoryCandidate]:
    if limit is None:
        return items
    return items[:limit]


if __name__ == "__main__":
    raise SystemExit(main())
