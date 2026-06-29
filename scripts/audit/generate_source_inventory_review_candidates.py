#!/usr/bin/env python3
"""Generate review-only Atlas candidates from committed source inventories."""

from __future__ import annotations

import argparse
import sys
import uuid
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.audit import grow_lexicon_from_sources as grow
from scripts.audit.source_inventory_intake import SourceInventoryError
from scripts.lexicon.content_lexicon_reconciler import PROJECT_ROOT

COMMITTED_SOURCE_INVENTORIES: tuple[Path, ...] = (
    PROJECT_ROOT / "data/lexicon/source-inventory/bolshakova-bukvar-keywords.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-abetka-keywords.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml",
)

DEFAULT_OUT = Path("/tmp/atlas-source-inventory-review-candidates.json")
WORKFLOW_ID = "source_inventory_review_candidates.v1"
TRIAGE_WORKFLOW_ID = "source_inventory_review_triage.v1"
TRIAGE_SAMPLE_LIMIT = 20

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
LIVE_STATIC_LEXICON_OUTPUT_DIR = PROJECT_ROOT / "site/public/lexicon"
LIVE_REVIEW_FORBIDDEN_OUTPUT_DIRS: tuple[Path, ...] = (
    LIVE_ATLAS_OUTPUT_DIR,
    LIVE_STATIC_LEXICON_OUTPUT_DIR,
)


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

    payload["review_triage"] = build_review_triage(payload)
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


def build_review_triage(payload: dict[str, Any]) -> dict[str, Any]:
    """Return conservative review metadata before any live publish decision."""
    publish_ready: list[dict[str, Any]] = []
    needs_publish_review: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()

    auto_merge_entries = [
        entry for entry in payload.get("auto_merge", []) if isinstance(entry, dict)
    ]
    needs_review_items = [
        item
        for item in payload.get("needs_review", [])
        if isinstance(item, dict) and isinstance(item.get("entry"), dict)
    ]

    for entry in auto_merge_entries:
        _count_entry(entry, source_family_counts=source_family_counts, pos_counts=pos_counts)
        reasons = publish_review_reasons(entry)
        if reasons:
            for reason in reasons:
                reason_counts[reason] += 1
            needs_publish_review.append(_triage_row(entry, bucket="auto_merge", reasons=reasons))
            continue
        publish_ready.append(_triage_row(entry, bucket="auto_merge", reasons=[]))

    for item in needs_review_items:
        entry = item["entry"]
        _count_entry(entry, source_family_counts=source_family_counts, pos_counts=pos_counts)
        grow_reason = str(item.get("reason") or "unspecified").strip()
        reasons = [f"grow_needs_review:{grow_reason}"]
        reasons.extend(publish_review_reasons(entry))
        for reason in reasons:
            reason_counts[reason] += 1
        needs_publish_review.append(_triage_row(entry, bucket="needs_review", reasons=reasons))

    publish_ready.sort(key=_triage_sort_key)
    needs_publish_review.sort(key=_triage_sort_key)

    return {
        "workflow": TRIAGE_WORKFLOW_ID,
        "policy": (
            "Review-only triage; grow auto_merge is not publish approval. "
            "Publish-ready requires grow auto_merge plus source provenance, POS, "
            "and a visible English anchor."
        ),
        "counts": {
            "total_candidates": len(auto_merge_entries) + len(needs_review_items),
            "grow_auto_merge": len(auto_merge_entries),
            "grow_needs_review": len(needs_review_items),
            "publish_ready": len(publish_ready),
            "needs_publish_review": len(needs_publish_review),
        },
        "needs_publish_review_reasons": dict(sorted(reason_counts.items())),
        "by_source_family": dict(sorted(source_family_counts.items())),
        "by_pos": dict(sorted(pos_counts.items())),
        "publish_ready_sample": publish_ready[:TRIAGE_SAMPLE_LIMIT],
        "needs_publish_review_sample": needs_publish_review[:TRIAGE_SAMPLE_LIMIT],
    }


def publish_review_reasons(entry: Mapping[str, Any]) -> list[str]:
    """Return publish-review blockers independent of grow auto-merge bucket."""
    reasons: list[str] = []
    if not entry.get("source_provenance"):
        reasons.append("missing_source_provenance")
    if not _clean_text(entry.get("pos")):
        reasons.append("missing_pos")
    if not has_visible_english_anchor(entry):
        reasons.append("missing_english_anchor")
    return reasons


def has_visible_english_anchor(entry: Mapping[str, Any]) -> bool:
    """Return true if search/browse can surface learner-facing English."""
    if _clean_text(entry.get("gloss")):
        return True
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return False
    translation = enrichment.get("translation")
    if not isinstance(translation, Mapping):
        return False
    terms = translation.get("en")
    if not isinstance(terms, list):
        return False
    return any(_clean_text(term) for term in terms)


def _count_entry(
    entry: Mapping[str, Any],
    *,
    source_family_counts: Counter[str],
    pos_counts: Counter[str],
) -> None:
    families = _source_families(entry)
    for family in families or ["unknown"]:
        source_family_counts[family] += 1
    pos_counts[_clean_text(entry.get("pos")) or "unknown"] += 1


def _triage_row(
    entry: Mapping[str, Any], *, bucket: str, reasons: Sequence[str]
) -> dict[str, Any]:
    provenance = entry.get("source_provenance")
    source_count = len(provenance) if isinstance(provenance, list) else 0
    return {
        "lemma": str(entry.get("lemma") or ""),
        "pos": _clean_text(entry.get("pos")),
        "bucket": bucket,
        "source_families": _source_families(entry),
        "source_count": source_count,
        "has_english_anchor": has_visible_english_anchor(entry),
        "reasons": list(reasons),
    }


def _source_families(entry: Mapping[str, Any]) -> list[str]:
    provenance = entry.get("source_provenance")
    if not isinstance(provenance, list):
        return []
    families = {
        family
        for item in provenance
        if isinstance(item, Mapping)
        for family in [_clean_text(item.get("source_family"))]
        if family
    }
    return sorted(families)


def _triage_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("lemma") or "").casefold(),
        str(row.get("pos") or "").casefold(),
    )


def _clean_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def format_triage_report(payload: Mapping[str, Any]) -> str:
    triage = payload.get("review_triage")
    if not isinstance(triage, Mapping):
        return "review_triage: missing"
    counts = triage.get("counts") if isinstance(triage.get("counts"), Mapping) else {}
    lines = [
        f"publish_ready: {counts.get('publish_ready', 0)}",
        f"needs_publish_review: {counts.get('needs_publish_review', 0)}",
    ]
    reasons = triage.get("needs_publish_review_reasons")
    if isinstance(reasons, Mapping) and reasons:
        lines.append("needs_publish_review_reasons:")
        lines.extend(f"- {reason}: {count}" for reason, count in sorted(reasons.items()))
    return "\n".join(lines)


def resolve_review_output_path(out: Path) -> Path:
    """Resolve and reject live Atlas/static-practice output paths."""
    output_path = out if out.is_absolute() else PROJECT_ROOT / out
    resolved = output_path.resolve()
    if resolved in {path.resolve() for path in LIVE_ATLAS_OUTPUTS}:
        raise SourceInventoryError(
            f"review-only source candidates must not overwrite {resolved.relative_to(PROJECT_ROOT)}"
        )
    for output_dir in LIVE_REVIEW_FORBIDDEN_OUTPUT_DIRS:
        if not resolved.is_relative_to(output_dir.resolve()):
            continue
        raise SourceInventoryError(
            "review-only source candidates must not write under "
            f"{output_dir.relative_to(PROJECT_ROOT)}"
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
        print(format_triage_report(payload))
        print(f"review_output: {payload['review_only']['candidate_output']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
