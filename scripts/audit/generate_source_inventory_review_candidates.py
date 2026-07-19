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
    # Note: one-shot bulk inventories (ohoiko-ulp-curated-*, textbook-jsonl-curated-*)
    # stay on disk for audit trail + decision binding, but are NOT merged into the
    # ongoing review-candidate generator — they deliberately restate lemmas with
    # SUM/author glosses that conflict with smaller curated keyword inventories.
    PROJECT_ROOT / "data/lexicon/source-inventory/pos-balanced-grammar-sample.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-seed.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-39-58.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-59-78.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-79-98.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-99-118.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-119-138.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-139-158.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-159-178.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-179-198.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-199-218.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-219-238.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-239-258.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-259-278.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-279-298.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/private-teacher-lesson-vocabulary-table-1-rows-299-610.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-family-numerals.yaml",
    PROJECT_ROOT / "data/lexicon/source-inventory/vashulenko-grade3-headwords.yaml",
)

DEFAULT_OUT = Path("/tmp/atlas-source-inventory-review-candidates.json")
DEFAULT_QUEUE_REPORT_OUT = Path("/tmp/atlas-source-inventory-publish-review-queue.md")
WORKFLOW_ID = "source_inventory_review_candidates.v1"
TRIAGE_WORKFLOW_ID = "source_inventory_review_triage.v1"
PUBLISH_REVIEW_QUEUE_WORKFLOW_ID = "source_inventory_publish_review_queue.v1"
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
LIVE_REVIEW_FORBIDDEN_OUTPUT_DIRS: tuple[Path, ...] = (
    LIVE_ATLAS_OUTPUT_DIR,
    PROJECT_ROOT / "site/public/lexicon",
)


def generate_review_candidates(
    *, limit: int | None = None, out: Path = DEFAULT_OUT
) -> dict[str, Any]:
    """Generate candidates without live Atlas/static-practice outputs."""
    output_path = resolve_review_output_path(out)
    temp_out = output_path.with_name(f".{output_path.name}.{uuid.uuid4().hex}.tmp")
    try:
        payload = grow.generate_candidates(
            inventory_paths=COMMITTED_SOURCE_INVENTORIES,
            limit=limit,
            out=temp_out,
        )
        validate_source_provenance(payload)
        screen_auto_merge_lemma_validity(payload)
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


_USE_DEFAULT_LOOKUP = object()


def screen_auto_merge_lemma_validity(
    payload: dict[str, Any],
    *,
    vesum: Any = _USE_DEFAULT_LOOKUP,
    heritage: Any = _USE_DEFAULT_LOOKUP,
) -> list[str]:
    """Demote VESUM-absent ``auto_merge`` candidates to ``needs_review``.

    Defense-in-depth from the 14th-window lesson (PR #4415): the candidates stage
    auto-merged «благополуччя», which is absent from VESUM and would only have been
    caught by the ledger reject / the publish-time ``lemma_in_vesum`` self-check.
    Reuses the conformance gate's policy verbatim — multi-word/proper-noun/deliberate-
    warning exemptions, Грінченко/ЕСУМ heritage fallback, curated modern-technical
    allowlist, and silent skip when ``data/vesum.db`` is unavailable (CI parity with
    the gate itself). Returns the demoted lemmas.
    """
    from scripts.audit import validate_atlas_conformance as conformance

    if vesum is _USE_DEFAULT_LOOKUP:
        vesum = conformance.DEFAULT_VESUM if conformance.DEFAULT_VESUM.exists() else None
    if heritage is _USE_DEFAULT_LOOKUP:
        heritage = conformance.DEFAULT_SOURCES_DB if conformance.DEFAULT_SOURCES_DB.exists() else None
    lookup = conformance._coerce_vesum_lookup(vesum)
    heritage_lookup = conformance._coerce_heritage_lookup(heritage)
    should_close_lookup = (
        isinstance(lookup, conformance.VesumLemmaLookup) and lookup is not vesum
    )
    should_close_heritage = (
        isinstance(heritage_lookup, conformance.HeritageLemmaLookup)
        and heritage_lookup is not heritage
    )
    demoted: list[str] = []
    try:
        kept: list[dict[str, Any]] = []
        for entry in payload.get("auto_merge", []):
            if not isinstance(entry, dict):
                kept.append(entry)
                continue
            lemma = str(entry.get("lemma") or "").strip()
            violations: list[conformance.Violation] = []
            conformance._check_lemma_in_vesum(
                entry, lemma, lookup, violations, heritage=heritage_lookup
            )
            if violations:
                payload.setdefault("needs_review", []).append(
                    {
                        "entry": entry,
                        "reason": f"lemma_in_vesum:{violations[0].detail}",
                    }
                )
                demoted.append(lemma)
            else:
                kept.append(entry)
        payload["auto_merge"] = kept
    finally:
        if should_close_lookup:
            lookup.close()
        if should_close_heritage:
            heritage_lookup.close()

    counts = payload.get("counts")
    if isinstance(counts, dict) and demoted:
        counts["auto_merge"] = len(payload.get("auto_merge", []))
        counts["needs_review"] = len(payload.get("needs_review", []))
    if demoted:
        print(
            "lemma-validity screen demoted "
            f"{len(demoted)} auto_merge candidate(s) to needs_review: {', '.join(sorted(demoted))}"
        )
    return demoted


def validate_source_provenance(payload: dict[str, Any]) -> None:
    """Reject candidate payloads that lost source inventory provenance."""
    missing = [
        str(entry.get("lemma") or "<unknown>")
        for entry in iter_candidate_entries(payload)
        if not entry.get("source_provenance")
    ]
    if missing:
        raise SourceInventoryError(
            f"missing source_provenance: {', '.join(sorted(missing))}"
        )


def iter_candidate_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return auto-merge and review-wrapped candidate entries."""
    entries = [entry for entry in payload.get("auto_merge", []) if isinstance(entry, dict)]
    entries.extend(
        item["entry"]
        for item in payload.get("needs_review", [])
        if isinstance(item, dict) and isinstance(item.get("entry"), dict)
    )
    return entries


def build_review_triage(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return conservative review metadata before any live publish decision."""
    publish_ready: list[dict[str, Any]] = []
    needs_publish_review: list[dict[str, Any]] = []
    reason_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()

    for entry, bucket, reasons in _publish_triage_items(payload):
        _count_entry(entry, source_family_counts=source_family_counts, pos_counts=pos_counts)
        if reasons:
            reason_counts.update(reasons)
            needs_publish_review.append(
                _triage_row(entry, bucket=bucket, reasons=reasons)
            )
            continue
        publish_ready.append(_triage_row(entry, bucket=bucket, reasons=[]))

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
            "total_candidates": len(publish_ready) + len(needs_publish_review),
            "grow_auto_merge": _candidate_bucket_count(payload, "auto_merge"),
            "grow_needs_review": _candidate_bucket_count(payload, "needs_review"),
            "publish_ready": len(publish_ready),
            "needs_publish_review": len(needs_publish_review),
        },
        "needs_publish_review_reasons": dict(sorted(reason_counts.items())),
        "by_source_family": dict(sorted(source_family_counts.items())),
        "by_pos": dict(sorted(pos_counts.items())),
        "publish_ready_sample": publish_ready[:TRIAGE_SAMPLE_LIMIT],
        "needs_publish_review_sample": needs_publish_review[:TRIAGE_SAMPLE_LIMIT],
    }


def build_publish_review_queue(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the full review-only queue for candidates blocked from publishing."""
    needs_review_items = [
        (entry, bucket, reasons)
        for entry, bucket, reasons in _publish_triage_items(payload)
        if reasons
    ]
    needs_review_items.sort(key=_triage_item_sort_key)
    queue = [
        _publish_review_queue_row(
            index=index,
            entry=entry,
            bucket=bucket,
            reasons=reasons,
        )
        for index, (entry, bucket, reasons) in enumerate(needs_review_items, start=1)
    ]
    reason_counts: Counter[str] = Counter()
    source_family_counts: Counter[str] = Counter()
    pos_counts: Counter[str] = Counter()
    for row in queue:
        reason_counts.update(row["reasons"])
        for family in row["source_families"] or ["unknown"]:
            source_family_counts[family] += 1
        pos_counts[_clean_text(row.get("pos")) or "unknown"] += 1

    return {
        "workflow": PUBLISH_REVIEW_QUEUE_WORKFLOW_ID,
        "policy": (
            "Review-only human queue. Rows require an explicit reviewer decision "
            "before any live Atlas publish batch."
        ),
        "counts": {
            "needs_publish_review": len(queue),
            "reason_count": len(reason_counts),
            "source_family_count": len(source_family_counts),
            "pos_count": len(pos_counts),
        },
        "needs_publish_review_reasons": dict(sorted(reason_counts.items())),
        "by_source_family": dict(sorted(source_family_counts.items())),
        "by_pos": dict(sorted(pos_counts.items())),
        "queue": queue,
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


def _candidate_bucket_count(payload: Mapping[str, Any], bucket: str) -> int:
    if bucket == "auto_merge":
        return len([entry for entry in payload.get("auto_merge", []) if isinstance(entry, dict)])
    if bucket == "needs_review":
        return len(
            [
                item
                for item in payload.get("needs_review", [])
                if isinstance(item, dict) and isinstance(item.get("entry"), dict)
            ]
        )
    return 0


def _publish_triage_items(
    payload: Mapping[str, Any],
) -> list[tuple[Mapping[str, Any], str, list[str]]]:
    items: list[tuple[Mapping[str, Any], str, list[str]]] = []
    for entry in payload.get("auto_merge", []):
        if isinstance(entry, Mapping):
            items.append((entry, "auto_merge", publish_review_reasons(entry)))
    for item in payload.get("needs_review", []):
        if not isinstance(item, Mapping) or not isinstance(item.get("entry"), Mapping):
            continue
        entry = item["entry"]
        grow_reason = str(item.get("reason") or "unspecified").strip() or "unspecified"
        reasons = [f"grow_needs_review:{grow_reason}"]
        reasons.extend(publish_review_reasons(entry))
        items.append((entry, "needs_review", reasons))
    return items


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


def _publish_review_queue_row(
    *,
    index: int,
    entry: Mapping[str, Any],
    bucket: str,
    reasons: Sequence[str],
) -> dict[str, Any]:
    row = _triage_row(entry, bucket=bucket, reasons=reasons)
    row["queue_id"] = f"source-inventory-publish-review-{index:04d}"
    row["source_references"] = _source_reference_labels(entry)
    return row


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


def _source_reference_labels(entry: Mapping[str, Any]) -> list[str]:
    provenance = entry.get("source_provenance")
    if not isinstance(provenance, list):
        return []
    labels: list[str] = []
    for item in provenance:
        if not isinstance(item, Mapping):
            continue
        parts = [
            _clean_text(item.get("source_family")),
            _clean_text(item.get("source_id")),
            _clean_text(item.get("source_locator")),
        ]
        labels.append(" / ".join(part for part in parts if part))
    return sorted(label for label in labels if label)


def _triage_sort_key(row: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("lemma") or "").casefold(),
        str(row.get("pos") or "").casefold(),
    )


def _triage_item_sort_key(
    item: tuple[Mapping[str, Any], str, Sequence[str]],
) -> tuple[str, str, str, tuple[str, ...], tuple[str, ...]]:
    entry, bucket, reasons = item
    return (
        str(entry.get("lemma") or "").casefold(),
        str(entry.get("pos") or "").casefold(),
        bucket,
        tuple(sorted(reasons)),
        tuple(_source_reference_labels(entry)),
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


def format_publish_review_queue_summary(payload: Mapping[str, Any]) -> str:
    queue = build_publish_review_queue(payload)
    counts = queue["counts"]
    return "\n".join(
        [
            f"publish_review_queue_rows: {counts['needs_publish_review']}",
            f"publish_review_queue_workflow: {queue['workflow']}",
        ]
    )


def format_publish_review_queue_report(payload: Mapping[str, Any]) -> str:
    queue = build_publish_review_queue(payload)
    lines = [
        "# Source Inventory Publish Review Queue",
        "",
        f"- workflow: `{queue['workflow']}`",
        f"- needs_publish_review: {queue['counts']['needs_publish_review']}",
        "- production_outputs_updated: []",
        "",
        queue["policy"],
        "",
        "## Reason Summary",
        "",
    ]
    reasons = queue["needs_publish_review_reasons"]
    if reasons:
        lines.extend(f"- `{reason}`: {count}" for reason, count in reasons.items())
    else:
        lines.append("- no rows")
    lines.extend(
        [
            "",
            "## Queue",
            "",
            "| ID | Lemma | POS | Bucket | English Anchor | Reasons | Sources | Decision | Notes |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if not queue["queue"]:
        lines.append("| - | - | - | - | - | - | - | - | - |")
        return "\n".join(lines)

    for row in queue["queue"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(row["queue_id"]),
                    _markdown_cell(row["lemma"]),
                    _markdown_cell(row.get("pos") or ""),
                    _markdown_cell(row["bucket"]),
                    _markdown_cell("yes" if row["has_english_anchor"] else "no"),
                    _markdown_cell("; ".join(row["reasons"])),
                    _markdown_cell("; ".join(row["source_references"])),
                    "",
                    "",
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", r"\|")


def write_publish_review_queue_report(payload: Mapping[str, Any], out: Path) -> Path:
    """Write a review-only Markdown queue outside the repository."""
    output_path = resolve_ephemeral_review_output_path(out)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        format_publish_review_queue_report(payload) + "\n",
        encoding="utf-8",
    )
    return output_path


def resolve_ephemeral_review_output_path(out: Path) -> Path:
    """Resolve queue reports and reject tracked/generated repository paths."""
    resolved = resolve_review_output_path(out).resolve()
    if resolved.is_relative_to(PROJECT_ROOT.resolve()):
        raise SourceInventoryError(
            "review queue reports must be written outside the repository"
        )
    return resolved


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
    parser.add_argument(
        "--queue-report",
        action="store_true",
        help="Print the full publish-review queue as Markdown",
    )
    parser.add_argument(
        "--queue-report-out",
        type=Path,
        help=(
            "Optional review-only Markdown queue path outside the repository "
            f"(example: {DEFAULT_QUEUE_REPORT_OUT})"
        ),
    )
    parser.add_argument("--report", action="store_true", help="Print candidate bucket counts")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")

    try:
        queue_report_output = (
            resolve_ephemeral_review_output_path(args.queue_report_out)
            if args.queue_report_out
            else None
        )
        payload = generate_review_candidates(limit=args.limit, out=args.out)
        if queue_report_output:
            write_publish_review_queue_report(payload, queue_report_output)
    except (FileNotFoundError, SourceInventoryError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print(grow.format_report(payload))
        print(format_triage_report(payload))
        print(format_publish_review_queue_summary(payload))
        if queue_report_output:
            print(f"review_queue_report_output: {queue_report_output}")
        print(f"review_output: {payload['review_only']['candidate_output']}")
    if args.queue_report:
        print(format_publish_review_queue_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
