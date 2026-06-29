#!/usr/bin/env python3
"""Generate review-only Atlas candidates from committed source inventories."""

from __future__ import annotations

import argparse
import sys
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from scripts.audit import grow_lexicon_from_sources as grow
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

COMMITTED_SOURCE_INVENTORIES: tuple[Path, ...] = (
    PROJECT_ROOT / "data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml",
)

DEFAULT_OUT = Path("/tmp/atlas-source-inventory-review-candidates.json")
WORKFLOW_ID = "source_inventory_review_candidates.v1"

LIVE_ATLAS_OUTPUTS: tuple[Path, ...] = (
    PROJECT_ROOT / "site/src/data/lexicon-manifest.json",
    PROJECT_ROOT / "site/src/data/lexicon-search-index.json",
    PROJECT_ROOT / "site/src/data/lexicon-browse-meta.json",
    PROJECT_ROOT / "site/src/data/lexicon-browse-flagged.json",
    PROJECT_ROOT / "site/src/data/lexicon-daily-pool.json",
    PROJECT_ROOT / "site/src/data/lexicon-practice-reviewed-sources.json",
    PROJECT_ROOT / "site/src/data/lexicon-manifest.pointer.json",
    PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json",
)
LIVE_ATLAS_OUTPUT_DIR = PROJECT_ROOT / "site/src/data"


def generate_review_candidates(
    *,
    limit: int | None = None,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Generate candidates without writing live Atlas/static-practice outputs."""
    output_path = resolve_review_output_path(out)
    temp_out = output_path.with_name(f".{output_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        payload = grow.generate_candidates(
            inventory_paths=COMMITTED_SOURCE_INVENTORIES,
            limit=limit,
            out=temp_out,
        )
        validate_source_provenance(payload)
    finally:
        temp_out.unlink(missing_ok=True)

    payload["review_only"] = {
        "workflow": WORKFLOW_ID,
        "source_inventory_paths": [
            str(path.relative_to(PROJECT_ROOT)) for path in COMMITTED_SOURCE_INVENTORIES
        ],
        "candidate_output": str(output_path),
        "production_outputs_updated": [],
    }
    grow.write_candidates(payload, output_path)
    return payload


def validate_source_provenance(payload: dict[str, Any]) -> None:
    """Reject candidate payloads that lost source inventory provenance."""
    missing = [
        str(entry.get("lemma") or "<unknown>")
        for entry in iter_candidate_entries(payload)
        if not entry.get("source_provenance")
    ]
    if missing:
        raise SourceInventoryError(
            "source inventory review candidates missing source_provenance: "
            + ", ".join(missing)
        )


def iter_candidate_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return auto-merge and review-wrapped candidate entries."""
    entries = [
        entry for entry in payload.get("auto_merge", []) if isinstance(entry, dict)
    ]
    entries.extend(
        item["entry"]
        for item in payload.get("needs_review", [])
        if isinstance(item, dict) and isinstance(item.get("entry"), dict)
    )
    return entries


def resolve_review_output_path(out: Path) -> Path:
    """Resolve and reject live Atlas/static-practice output paths."""
    output_path = out if out.is_absolute() else PROJECT_ROOT / out
    resolved = output_path.resolve()
    if resolved in {path.resolve() for path in LIVE_ATLAS_OUTPUTS}:
        raise SourceInventoryError(
            f"review-only source candidates must not overwrite {resolved.relative_to(PROJECT_ROOT)}"
        )
    if resolved.is_relative_to(LIVE_ATLAS_OUTPUT_DIR.resolve()):
        raise SourceInventoryError(
            "review-only source candidates must not write under site/src/data"
        )
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate review-only Atlas candidates from committed source inventories."
        )
    )
    parser.add_argument("--limit", type=int, help="Limit processed source headwords")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Review-only JSON output path (default: {DEFAULT_OUT})",
    )
    parser.add_argument("--report", action="store_true", help="Print candidate bucket counts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    try:
        payload = generate_review_candidates(limit=args.limit, out=args.out)
    except (FileNotFoundError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print(grow.format_report(payload))
        print(f"review_output: {payload['review_only']['candidate_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
