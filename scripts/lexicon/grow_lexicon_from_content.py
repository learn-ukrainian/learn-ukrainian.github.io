#!/usr/bin/env python3
"""Generate gated Atlas-entry candidates from content delta lemmas.

Run from the repository root:

    .venv/bin/python -m scripts.lexicon.grow_lexicon_from_content --limit 50 --report
"""

from __future__ import annotations

import argparse
import copy
import json
import sqlite3
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from scripts.lexicon import enrich_manifest
from scripts.lexicon.content_lexicon_reconciler import (
    LEXICON_MANIFEST_PATH,
    PROJECT_ROOT,
    LemmaExample,
    discover_content_mdx_paths,
    reconcile_content,
)

DEFAULT_OUT = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
GENERATED_FROM = "content_lexicon_reconciler.missing_lemmas"
_WARNING_CLASSIFICATIONS = {"russianism", "sovietism", "surzhyk"}
_POS_PRIORITY = {
    "noun": 0,
    "verb": 1,
    "adj": 2,
    "adv": 3,
}


def build_skeleton_entry(lemma: str) -> dict[str, Any]:
    """Build the minimal Atlas entry candidate for a content delta lemma."""
    entry: dict[str, Any] = {"lemma": lemma}
    pos = _vesum_pos(lemma)
    if pos:
        entry["pos"] = pos
    return entry


def review_reason(entry: dict[str, Any]) -> str | None:
    """Return the deterministic gate reason, or ``None`` when auto-mergeable."""
    reasons: list[str] = []
    if not _has_dictionary_definition(entry):
        reasons.append("missing dictionary definition")
    if not str(entry.get("pos") or "").strip():
        reasons.append("unresolved pos")

    heritage_status = entry.get("heritage_status")
    if not isinstance(heritage_status, dict):
        reasons.append("missing heritage_status")
    else:
        reasons.extend(_heritage_review_reasons(heritage_status))

    return "; ".join(dict.fromkeys(reasons)) if reasons else None


def split_candidates(entries: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split enriched candidates into auto-merge and review buckets."""
    auto_merge: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    for entry in entries:
        reason = review_reason(entry)
        if reason:
            needs_review.append({"entry": entry, "reason": reason})
        else:
            auto_merge.append(entry)
    return auto_merge, needs_review


def build_payload(
    *,
    total_delta: int,
    processed: int,
    auto_merge: Sequence[dict[str, Any]],
    needs_review: Sequence[dict[str, Any]],
    limit: int | None,
) -> dict[str, Any]:
    """Build the gated candidates JSON payload."""
    return {
        "generated_from": GENERATED_FROM,
        "counts": {
            "total_delta": total_delta,
            "processed": processed,
            "auto_merge": len(auto_merge),
            "needs_review": len(needs_review),
        },
        "limit": limit,
        "auto_merge": list(auto_merge),
        "needs_review": list(needs_review),
    }


def generate_candidates(
    *,
    limit: int | None = None,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Generate, write, and return gated Atlas-entry candidates."""
    paths = discover_content_mdx_paths()
    result = reconcile_content(paths, manifest_path=LEXICON_MANIFEST_PATH)
    delta = _limited_delta(result.missing_lemmas, limit)

    entries: list[dict[str, Any]] = []
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    with _source_connection(enrich_manifest.SOURCES_DB) as conn, _preserve_wiki_reference_cache():
        has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for item in delta:
            entry = build_skeleton_entry(item.lemma)
            enrich_manifest.enrich_entry(
                entry,
                conn,
                kaikki_lookup,
                has_sum11_flags=has_sum11_flags,
            )
            entries.append(entry)

    auto_merge, needs_review = split_candidates(entries)
    payload = build_payload(
        total_delta=len(result.missing_lemmas),
        processed=len(delta),
        auto_merge=auto_merge,
        needs_review=needs_review,
        limit=limit,
    )
    write_candidates(payload, out)
    return payload


def write_candidates(payload: dict[str, Any], out: Path = DEFAULT_OUT) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_report(payload: dict[str, Any]) -> str:
    counts = payload["counts"]
    return "\n".join(
        [
            f"total_delta: {counts['total_delta']}",
            f"processed: {counts['processed']}",
            f"auto_merge: {counts['auto_merge']}",
            f"needs_review: {counts['needs_review']}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate gated Atlas-entry candidates from content delta lemmas."
    )
    parser.add_argument("--limit", type=int, help="Limit processed delta lemmas")
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
        payload = generate_candidates(limit=args.limit, out=args.out)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print(format_report(payload))
    return 0


def _source_connection(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(f"sources.db absent in worktree: {path.relative_to(PROJECT_ROOT)}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _limited_delta(items: Sequence[LemmaExample], limit: int | None) -> Sequence[LemmaExample]:
    if limit is None:
        return items
    return items[:limit]


def _vesum_pos(lemma: str) -> str | None:
    base = enrich_manifest._base_lemma(lemma)
    if " " in base.strip():
        return None
    try:
        forms = enrich_manifest.verify_lemma(base)
    except Exception:
        return None
    base_key = enrich_manifest._lookup_key(base).casefold()
    candidates: list[tuple[bool, bool, int, str]] = []
    for row in forms:
        pos = str(row.get("pos") or "").strip()
        if pos:
            word_form = enrich_manifest._lookup_key(str(row.get("word_form") or "")).casefold()
            tags = str(row.get("tags") or "")
            candidates.append(
                (
                    word_form != base_key,
                    ":arch" in tags or tags == "arch",
                    _POS_PRIORITY.get(pos, 99),
                    pos,
                )
            )
    if not candidates:
        return None
    return min(candidates)[3]


@contextmanager
def _preserve_wiki_reference_cache() -> Iterator[None]:
    path = enrich_manifest.WIKI_REFERENCE_CACHE
    original_bytes = path.read_bytes() if path.exists() else None
    original_data = copy.deepcopy(enrich_manifest._WIKI_REFERENCE_CACHE_DATA)
    original_dirty = enrich_manifest._WIKI_REFERENCE_CACHE_DIRTY
    try:
        yield
    finally:
        if original_bytes is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(original_bytes)
        enrich_manifest._WIKI_REFERENCE_CACHE_DATA = original_data
        enrich_manifest._WIKI_REFERENCE_CACHE_DIRTY = original_dirty


def _has_dictionary_definition(entry: dict[str, Any]) -> bool:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return False

    meaning = enrichment.get("meaning")
    if isinstance(meaning, dict) and _has_definitions(meaning):
        return True

    cards = enrichment.get("definition_cards")
    if not isinstance(cards, list):
        return False
    return any(isinstance(card, dict) and _has_definitions(card) for card in cards)


def _has_definitions(block: dict[str, Any]) -> bool:
    definitions = block.get("definitions")
    if not isinstance(definitions, list):
        return False
    return any(str(definition or "").strip() for definition in definitions)


def _heritage_review_reasons(status: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    classification = str(status.get("classification") or "")
    if status.get("is_russianism") or classification in _WARNING_CLASSIFICATIONS:
        reasons.append("heritage_status flags russianism")
    if status.get("curated_calque"):
        reasons.append("heritage_status flags curated_calque")
    if status.get("calque_warning"):
        reasons.append("heritage_status flags calque_warning")
    if status.get("russian_shadow"):
        reasons.append("heritage_status flags russian_shadow")
    if status.get("warning"):
        reasons.append("heritage_status flags warning")
    return reasons


if __name__ == "__main__":
    raise SystemExit(main())
