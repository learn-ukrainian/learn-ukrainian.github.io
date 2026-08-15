#!/usr/bin/env python3
"""Generate gated Atlas-entry candidates from content delta lemmas.

Run from the repository root:

    .venv/bin/python -m scripts.lexicon.grow_lexicon_from_content --limit 50 --report
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sqlite3
import sys
import tempfile
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
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
from scripts.lexicon.lemma_normalization import strip_acute_stress

DEFAULT_OUT = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
DEFAULT_CHECKPOINT_INTERVAL = 10
GENERATED_FROM = "content_lexicon_reconciler.missing_lemmas"
_WARNING_CLASSIFICATIONS = {"russianism", "sovietism", "surzhyk"}
_POS_PRIORITY = {
    "noun": 0,
    "verb": 1,
    "adj": 2,
    "adv": 3,
}


def _write_atomically(path: Path, content: bytes) -> None:
    """Write content to path atomically via a temporary file in path.parent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
            tmp_name = tmp.name
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    finally:
        if tmp_name:
            with contextlib.suppress(FileNotFoundError):
                Path(tmp_name).unlink()


def _flush_caches() -> None:
    """Flush any dirty in-memory fetch caches to disk."""
    with suppress(Exception):
        enrich_manifest._write_wiki_reference_cache()
    with suppress(Exception):
        enrich_manifest._write_grac_frequency_cache()


def load_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    """Load previously enriched entries from an existing candidates file.

    Returns a mapping of lemma -> entry dict. If the file is missing, empty, or
    corrupted, returns an empty mapping and logs a warning to stderr.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            print(f"[grow_lexicon] Warning: checkpoint {path} is not a JSON object; starting fresh.", file=sys.stderr)
            return {}
        entries_by_lemma: dict[str, dict[str, Any]] = {}
        for entry in data.get("auto_merge", []):
            if isinstance(entry, dict) and "lemma" in entry:
                entries_by_lemma[str(entry["lemma"])] = entry
        for item in data.get("needs_review", []):
            if isinstance(item, dict):
                entry = item.get("entry")
                if isinstance(entry, dict) and "lemma" in entry:
                    entries_by_lemma[str(entry["lemma"])] = entry
        return entries_by_lemma
    except Exception as exc:
        print(f"[grow_lexicon] Warning: could not load checkpoint from {path} ({exc}); starting fresh.", file=sys.stderr)
        return {}


def build_skeleton_entry(lemma: str) -> dict[str, Any]:
    """Build the minimal Atlas entry candidate for a content delta lemma."""
    lemma = strip_acute_stress(lemma.strip())
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


def write_candidates(payload: dict[str, Any], out: Path = DEFAULT_OUT) -> None:
    """Atomically write the candidates JSON payload to disk."""
    content = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _write_atomically(out, content)


def write_checkpoint(
    entries: Sequence[dict[str, Any]],
    *,
    total_delta: int,
    limit: int | None,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    """Save an intermediate checkpoint atomically to disk."""
    auto_merge, needs_review = split_candidates(entries)
    payload = build_payload(
        total_delta=total_delta,
        processed=len(entries),
        auto_merge=auto_merge,
        needs_review=needs_review,
        limit=limit,
    )
    write_candidates(payload, out)
    _flush_caches()
    return payload


def generate_candidates(
    *,
    limit: int | None = None,
    out: Path = DEFAULT_OUT,
    checkpoint_interval: int = DEFAULT_CHECKPOINT_INTERVAL,
    resume: bool = True,
    quiet: bool = False,
) -> dict[str, Any]:
    """Generate, write, and return gated Atlas-entry candidates with checkpointing."""
    paths = discover_content_mdx_paths()
    result = reconcile_content(paths, manifest_path=LEXICON_MANIFEST_PATH)
    delta = _limited_delta(result.missing_lemmas, limit)
    total_missing = len(result.missing_lemmas)
    total_to_process = len(delta)

    checkpointed = load_checkpoint(out) if resume and out.exists() else {}
    resumed_count = 0
    newly_enriched_count = 0

    if not quiet:
        print(
            f"[grow_lexicon] Starting candidates generation: {total_to_process} delta items "
            f"(total missing: {total_missing}, checkpointed: {len(checkpointed)}, interval: {checkpoint_interval})",
            file=sys.stderr,
        )

    entries: list[dict[str, Any]] = []
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    with _source_connection(enrich_manifest.SOURCES_DB) as conn, _preserve_wiki_reference_cache():
        has_sum11_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for idx, item in enumerate(delta, start=1):
            if resume and item.lemma in checkpointed:
                entry = checkpointed[item.lemma]
                entries.append(entry)
                resumed_count += 1
                if not quiet and (
                    idx % max(1, checkpoint_interval) == 0 or idx == total_to_process
                ):
                    print(
                        f"[grow_lexicon] [{idx}/{total_to_process}] lemma='{item.lemma}' (resumed, total_resumed={resumed_count}, newly_enriched={newly_enriched_count})",
                        file=sys.stderr,
                    )
            else:
                entry = build_skeleton_entry(item.lemma)
                enrich_manifest.enrich_entry(
                    entry,
                    conn,
                    kaikki_lookup,
                    has_sum11_flags=has_sum11_flags,
                )
                entries.append(entry)
                newly_enriched_count += 1
                if not quiet and (
                    idx % max(1, checkpoint_interval) == 0 or idx == total_to_process
                ):
                    print(
                        f"[grow_lexicon] [{idx}/{total_to_process}] lemma='{item.lemma}' (enriched, total_resumed={resumed_count}, newly_enriched={newly_enriched_count})",
                        file=sys.stderr,
                    )
                if checkpoint_interval > 0 and newly_enriched_count % checkpoint_interval == 0:
                    write_checkpoint(
                        entries,
                        total_delta=total_missing,
                        limit=limit,
                        out=out,
                    )
                    if not quiet:
                        print(
                            f"[grow_lexicon] Checkpoint saved: {len(entries)} items ({newly_enriched_count} newly enriched) -> {out}",
                            file=sys.stderr,
                        )

    auto_merge, needs_review = split_candidates(entries)
    payload = build_payload(
        total_delta=total_missing,
        processed=len(delta),
        auto_merge=auto_merge,
        needs_review=needs_review,
        limit=limit,
    )
    write_candidates(payload, out)
    _flush_caches()
    if not quiet:
        print(
            f"[grow_lexicon] Completed: {len(entries)} items written to {out} "
            f"({resumed_count} resumed, {newly_enriched_count} newly enriched; "
            f"auto_merge={len(auto_merge)}, needs_review={len(needs_review)})",
            file=sys.stderr,
        )
    return payload


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
    parser = argparse.ArgumentParser(description="Generate gated Atlas-entry candidates from content delta lemmas.")
    parser.add_argument("--limit", type=int, help="Limit processed delta lemmas")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Candidate JSON output path (default: {DEFAULT_OUT.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument("--report", action="store_true", help="Print candidate bucket counts")
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=DEFAULT_CHECKPOINT_INTERVAL,
        help=f"Periodic checkpoint interval in lemmas (default: {DEFAULT_CHECKPOINT_INTERVAL})",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Do not resume from existing candidates file, start fresh",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stderr progress heartbeat",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be non-negative")
    if args.checkpoint_interval < 0:
        parser.error("--checkpoint-interval must be non-negative")

    try:
        payload = generate_candidates(
            limit=args.limit,
            out=args.out,
            checkpoint_interval=args.checkpoint_interval,
            resume=not args.no_resume,
            quiet=args.quiet,
        )
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
    """Maintain cache persistence across runs and flush dirty caches on exit."""
    try:
        yield
    finally:
        _flush_caches()


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

