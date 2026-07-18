#!/usr/bin/env python3
"""Deterministic local-source triage for grow ``needs_review`` lemmas.

For every held entry in ``data/lexicon/grow_candidates.json``, probe local
dictionaries in ``data/sources.db`` (batched SQL, no per-word loops) and decide
a machine action by code:

* ``promote_with_gloss`` — ≥1 gloss-bearing source has a definition
* ``truly_missing`` — no local gloss source has the lemma
* ``heritage_flag`` — heritage/calque held reason (kept aside regardless of hits)

When to use: answering "which dictionary are the 2,316 held grow words missing
from?" with counts — never LLM judging. When NOT to use: linguistic sense
disambiguation or promotion itself (this tool only triages).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_words
from scripts.wiki import sources_db as sdb

DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
DEFAULT_SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"
DEFAULT_OUT = PROJECT_ROOT / "data" / "lexicon" / "needs-review-triage.json"
DEFAULT_SUMMARY = PROJECT_ROOT / "data" / "lexicon" / "needs-review-triage-summary.md"

# Gloss priority for best_gloss / promote_with_gloss (user contract).
GLOSS_SOURCE_PRIORITY: tuple[str, ...] = (
    "sum11",
    "dmklinger",
    "grinchenko",
    "slovnyk_me",
    "balla",
)
# Full sources_hit key order (stable JSON / summary columns).
SOURCE_HIT_KEYS: tuple[str, ...] = (
    "sum11",
    "dmklinger",
    "grinchenko",
    "slovnyk_me",
    "balla",
    "esum",
    "puls_cefr",
)

MACHINE_PROMOTE = "promote_with_gloss"
MACHINE_MISSING = "truly_missing"
MACHINE_HERITAGE = "heritage_flag"
SAMPLE_ROWS = 20
_BATCH = 400

LookupFn = Callable[[list[str]], dict[str, list[dict[str, Any]]]]
VesumFn = Callable[[list[str]], dict[str, list[dict[str, Any]]]]


@dataclass(frozen=True)
class HeldEntry:
    lemma: str
    pos: str | None
    held_reason: str
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class TriageResult:
    entries: list[dict[str, Any]]
    summary_md: str
    counts_by_action: dict[str, int]
    candidates_found: bool
    written: bool
    dry_run: bool


def load_held_entries(candidates_path: Path) -> list[HeldEntry]:
    """Parse ``needs_review`` rows from a grow_candidates payload."""
    payload = json.loads(candidates_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"candidates payload must be a JSON object: {candidates_path}")
    raw_items = payload.get("needs_review") or []
    if not isinstance(raw_items, list):
        raise ValueError(f"needs_review must be a list: {candidates_path}")

    held: list[HeldEntry] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            continue
        entry = item.get("entry") if isinstance(item.get("entry"), Mapping) else item
        if not isinstance(entry, Mapping):
            continue
        lemma = strip_acute_stress(str(entry.get("lemma") or "").strip())
        if not lemma:
            continue
        pos_raw = entry.get("pos")
        pos = str(pos_raw).strip() if pos_raw is not None and str(pos_raw).strip() else None
        reason = str(item.get("reason") or entry.get("held_reason") or "").strip()
        held.append(HeldEntry(lemma=lemma, pos=pos, held_reason=reason, raw=item))
    return held


def is_heritage_held(reason: str) -> bool:
    """True when the hold reason is a heritage/calque carve-out."""
    return "heritage_status" in (reason or "")


def extract_gloss_text(source_key: str, hit: Mapping[str, Any]) -> str | None:
    """Pull a non-empty definition/gloss string from one source row."""
    if source_key == "dmklinger":
        translations = hit.get("translations")
        if isinstance(translations, str) and translations.strip():
            try:
                parsed = json.loads(translations)
            except json.JSONDecodeError:
                text = translations.strip()
                return text or None
            if isinstance(parsed, list):
                for item in parsed:
                    text = str(item or "").strip()
                    if text:
                        return text
            text = str(parsed).strip()
            return text or None
        if isinstance(translations, list):
            for item in translations:
                text = str(item or "").strip()
                if text:
                    return text
        text = str(hit.get("text") or "").strip()
        return text or None

    for field in ("definition", "text", "etymology_text"):
        text = str(hit.get(field) or "").strip()
        if text:
            return text
    return None


def choose_best_gloss(
    hits_by_source: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, str] | None:
    """First non-empty gloss in GLOSS_SOURCE_PRIORITY order."""
    for source_key in GLOSS_SOURCE_PRIORITY:
        for hit in hits_by_source.get(source_key) or []:
            text = extract_gloss_text(source_key, hit)
            if text:
                return {"text": text, "source": source_key}
    return None


def decide_machine_action(
    *,
    held_reason: str,
    best_gloss: Mapping[str, str] | None,
) -> str:
    """Code-only action bucket (no linguistic judgment)."""
    if is_heritage_held(held_reason):
        return MACHINE_HERITAGE
    if best_gloss is not None:
        return MACHINE_PROMOTE
    return MACHINE_MISSING


def _chunked(items: Sequence[str], size: int = _BATCH) -> list[list[str]]:
    return [list(items[i : i + size]) for i in range(0, len(items), size)]


def _merge_batch_lookup(
    lemmas: Sequence[str],
    lookup: LookupFn,
) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {lemma: [] for lemma in lemmas}
    if not lemmas:
        return out
    unique = list(dict.fromkeys(lemmas))
    for chunk in _chunked(unique):
        batch = lookup(chunk)
        for lemma in chunk:
            out[lemma] = list(batch.get(lemma) or [])
    return out


def probe_sources(
    lemmas: Sequence[str],
    *,
    db_path: Path | None = None,
    lookups: Mapping[str, LookupFn] | None = None,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Batched local probes keyed by source then lemma."""
    if lookups is not None:
        return {key: _merge_batch_lookup(lemmas, fn) for key, fn in lookups.items()}

    path = str(db_path) if db_path is not None else None

    def _sum11(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_definitions_batch(words, db_path=path)

    def _dmk(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_dmklinger_uk_en_batch(words, db_path=path)

    def _grin(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_grinchenko_batch(words, db_path=path)

    def _slov(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_slovnyk_me_entries_batch(words, db_path=path)

    def _balla(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_balla_en_uk_batch(words, db_path=path)

    def _esum(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.search_esum_batch(words, db_path=path)

    def _cefr(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return sdb.query_cefr_levels(words, db_path=path)

    default_lookups: dict[str, LookupFn] = {
        "sum11": _sum11,
        "dmklinger": _dmk,
        "grinchenko": _grin,
        "slovnyk_me": _slov,
        "balla": _balla,
        "esum": _esum,
        "puls_cefr": _cefr,
    }
    return {key: _merge_batch_lookup(lemmas, fn) for key, fn in default_lookups.items()}


def probe_vesum(
    lemmas: Sequence[str],
    *,
    vesum_db: Path | None = None,
    vesum_fn: VesumFn | None = None,
) -> dict[str, bool]:
    """Batch VESUM validity (chunked to stay under SQLite placeholder limits)."""
    if not lemmas:
        return {}
    unique = list(dict.fromkeys(lemmas))
    valid: dict[str, bool] = {lemma: False for lemma in unique}
    checker = vesum_fn
    if checker is None:

        def checker(words: list[str]) -> dict[str, list[dict[str, Any]]]:
            return verify_words(words, db_path=vesum_db)

    for chunk in _chunked(unique):
        try:
            batch = checker(chunk)
        except FileNotFoundError:
            # No VESUM DB in worktree/sparse checkout — report false, do not crash.
            for lemma in chunk:
                valid[lemma] = False
            continue
        for lemma in chunk:
            valid[lemma] = bool(batch.get(lemma))
    return valid


def triage_held_entries(
    held: Sequence[HeldEntry],
    *,
    db_path: Path | None = None,
    vesum_db: Path | None = None,
    lookups: Mapping[str, LookupFn] | None = None,
    vesum_fn: VesumFn | None = None,
) -> list[dict[str, Any]]:
    """Return per-lemma triage records (deterministic, code-decided)."""
    lemmas = [item.lemma for item in held]
    by_source = probe_sources(lemmas, db_path=db_path, lookups=lookups)
    vesum_valid = probe_vesum(lemmas, vesum_db=vesum_db, vesum_fn=vesum_fn)

    records: list[dict[str, Any]] = []
    for item in held:
        hits: dict[str, list[dict[str, Any]]] = {}
        sources_hit: dict[str, int] = {}
        for key in SOURCE_HIT_KEYS:
            source_map = by_source.get(key) or {}
            row_hits = list(source_map.get(item.lemma) or [])
            hits[key] = row_hits
            sources_hit[key] = len(row_hits)

        best_gloss = choose_best_gloss(hits)
        cefr_hits = hits.get("puls_cefr") or []
        cefr_level: str | None = None
        if cefr_hits:
            level = cefr_hits[0].get("level")
            cefr_level = str(level).strip() if level is not None and str(level).strip() else None

        action = decide_machine_action(held_reason=item.held_reason, best_gloss=best_gloss)
        records.append(
            {
                "lemma": item.lemma,
                "pos": item.pos,
                "held_reason": item.held_reason,
                "sources_hit": sources_hit,
                "best_gloss": best_gloss,
                "cefr": cefr_level,
                "vesum_valid": bool(vesum_valid.get(item.lemma)),
                "machine_action": action,
            }
        )
    return records


def build_summary_markdown(records: Sequence[Mapping[str, Any]]) -> str:
    """Counts per action / source-hit combo / POS + 20-row samples."""
    action_counts = Counter(str(r.get("machine_action") or "") for r in records)
    pos_counts = Counter(str(r.get("pos") or "(none)") for r in records)

    combo_counts: Counter[str] = Counter()
    for record in records:
        hits = record.get("sources_hit") if isinstance(record.get("sources_hit"), Mapping) else {}
        present = [key for key in SOURCE_HIT_KEYS if int(hits.get(key) or 0) > 0]
        label = "+".join(present) if present else "(none)"
        combo_counts[label] += 1

    lines: list[str] = [
        "# Needs-review triage summary",
        "",
        "Deterministic local-source probe of grow `needs_review` lemmas.",
        "No LLM judging — machine_action is decided by code.",
        "",
        f"Total held: **{len(records)}**",
        "",
        "## Counts by machine_action",
        "",
    ]
    for action in (MACHINE_PROMOTE, MACHINE_MISSING, MACHINE_HERITAGE):
        lines.append(f"- `{action}`: {action_counts.get(action, 0)}")
    for action, count in sorted(action_counts.items()):
        if action not in {MACHINE_PROMOTE, MACHINE_MISSING, MACHINE_HERITAGE}:
            lines.append(f"- `{action}`: {count}")

    lines.extend(["", "## Counts by POS", ""])
    for pos, count in pos_counts.most_common():
        lines.append(f"- `{pos}`: {count}")

    lines.extend(
        [
            "",
            "## Counts by source-hit combination",
            "",
            "Keys present (count > 0), joined with `+`. `(none)` = zero hits.",
            "",
        ]
    )
    for combo, count in combo_counts.most_common():
        lines.append(f"- `{combo}`: {count}")

    lines.extend(["", "## Per-source hit totals (lemma has ≥1 row)", ""])
    for key in SOURCE_HIT_KEYS:
        n = sum(
            1
            for record in records
            if isinstance(record.get("sources_hit"), Mapping)
            and int(record["sources_hit"].get(key) or 0) > 0
        )
        lines.append(f"- `{key}`: {n}")

    for action in (MACHINE_PROMOTE, MACHINE_MISSING, MACHINE_HERITAGE):
        bucket = [r for r in records if r.get("machine_action") == action]
        lines.extend(
            [
                "",
                f"## Sample ({SAMPLE_ROWS}) — `{action}` (n={len(bucket)})",
                "",
                "| lemma | pos | held_reason | sources_hit | best_gloss |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for record in bucket[:SAMPLE_ROWS]:
            hits = record.get("sources_hit") if isinstance(record.get("sources_hit"), Mapping) else {}
            hit_bits = ",".join(
                f"{k}={hits.get(k, 0)}" for k in SOURCE_HIT_KEYS if int(hits.get(k) or 0) > 0
            ) or "—"
            gloss = record.get("best_gloss")
            if isinstance(gloss, Mapping) and gloss.get("text"):
                gloss_cell = f"{gloss.get('source')}: {_md_cell(str(gloss.get('text'))[:80])}"
            else:
                gloss_cell = "—"
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(str(record.get("lemma") or "")),
                        _md_cell(str(record.get("pos") or "")),
                        _md_cell(str(record.get("held_reason") or "")[:60]),
                        _md_cell(hit_bits),
                        gloss_cell,
                    ]
                )
                + " |"
            )

    lines.append("")
    return "\n".join(lines)


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def run_triage(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    db_path: Path | None = DEFAULT_SOURCES_DB,
    vesum_db: Path | None = None,
    out_path: Path = DEFAULT_OUT,
    summary_path: Path = DEFAULT_SUMMARY,
    write: bool = False,
    limit: int | None = None,
    lookups: Mapping[str, LookupFn] | None = None,
    vesum_fn: VesumFn | None = None,
) -> TriageResult:
    """Load candidates, probe sources, optionally write artifacts."""
    candidates_path = _resolve(candidates_path)
    out_path = _resolve(out_path)
    summary_path = _resolve(summary_path)
    if db_path is not None:
        db_path = _resolve(db_path)
    if vesum_db is not None:
        vesum_db = _resolve(vesum_db)

    if not candidates_path.exists():
        empty_summary = build_summary_markdown([])
        return TriageResult(
            entries=[],
            summary_md=empty_summary,
            counts_by_action={},
            candidates_found=False,
            written=False,
            dry_run=not write,
        )

    held = load_held_entries(candidates_path)
    if limit is not None:
        held = held[: max(0, limit)]

    records = triage_held_entries(
        held,
        db_path=db_path,
        vesum_db=vesum_db,
        lookups=lookups,
        vesum_fn=vesum_fn,
    )
    summary_md = build_summary_markdown(records)
    counts = dict(Counter(str(r["machine_action"]) for r in records))

    written = False
    if write:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_by": "scripts/lexicon/triage_needs_review.py",
            "candidates": str(candidates_path),
            "sources_db": str(db_path) if db_path is not None else None,
            "counts": {
                "total": len(records),
                **{f"action_{k}": v for k, v in sorted(counts.items())},
            },
            "entries": records,
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(summary_md, encoding="utf-8")
        written = True

    return TriageResult(
        entries=records,
        summary_md=summary_md,
        counts_by_action=counts,
        candidates_found=True,
        written=written,
        dry_run=not write,
    )


def format_cli_summary(result: TriageResult) -> str:
    lines = [
        f"Mode: {'write' if result.written else 'probe (read-only)'}",
        f"Candidates found: {str(result.candidates_found).lower()}",
        f"Held triaged: {len(result.entries)}",
        f"Written: {str(result.written).lower()}",
    ]
    for action in (MACHINE_PROMOTE, MACHINE_MISSING, MACHINE_HERITAGE):
        lines.append(f"  {action}: {result.counts_by_action.get(action, 0)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically triage grow needs_review lemmas against local "
            "sources.db dictionaries (batched SQL + VESUM). "
            "Use this when you need code-decided counts of which held words "
            "already have a local gloss vs truly missing; do not use it for "
            "LLM judging or for writing the live manifest."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Read-only probe (stdout counts; no files written)\n"
            "  .venv/bin/python scripts/lexicon/triage_needs_review.py --probe\n"
            "\n"
            "  # Write JSON + markdown summary\n"
            "  .venv/bin/python scripts/lexicon/triage_needs_review.py --write \\\n"
            "    --db data/sources.db --candidates data/lexicon/grow_candidates.json\n"
            "\n"
            "  # Sparse worktree: pass absolute paths from the primary checkout\n"
            "  .venv/bin/python scripts/lexicon/triage_needs_review.py --write \\\n"
            "    --db /path/to/primary/data/sources.db \\\n"
            "    --candidates /path/to/primary/data/lexicon/grow_candidates.json\n"
            "\n"
            "Outputs (only with --write):\n"
            "  data/lexicon/needs-review-triage.json     per-lemma machine triage\n"
            "  data/lexicon/needs-review-triage-summary.md  counts + samples\n"
            "\n"
            "Exit codes:\n"
            "  0  success (--help, --probe, or successful --write)\n"
            "  2  refused (no --write/--probe) or argparse/input error\n"
            "\n"
            "Related:\n"
            "  scripts/lexicon/promote_grow_candidates.py  — promote auto_merge only\n"
            "  scripts/wiki/sources_db.py                 — batched dictionary probes\n"
            "  issue #5230                                — Atlas re-enrich arc\n"
        ),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help=(
            "Path to grow_candidates.json with needs_review[] "
            f"(default: {DEFAULT_CANDIDATES})"
        ),
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_SOURCES_DB,
        help=f"Path to sources.db (default: {DEFAULT_SOURCES_DB})",
    )
    parser.add_argument(
        "--vesum-db",
        type=Path,
        default=None,
        help="Optional VESUM SQLite path override (default: project VESUM_DB_PATH)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"JSON triage output path (default: {DEFAULT_OUT})",
    )
    parser.add_argument(
        "--summary-out",
        type=Path,
        default=DEFAULT_SUMMARY,
        help=f"Markdown summary output path (default: {DEFAULT_SUMMARY})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on held entries processed (probe/debug; default: all)",
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write needs-review-triage.json and the markdown summary. "
            "Default without --write/--probe: refuse (exit 2)."
        ),
    )
    mode.add_argument(
        "--probe",
        action="store_true",
        help=(
            "Read-only probe: run all batched lookups and print counts to stdout; "
            "do not write files."
        ),
    )
    parser.add_argument(
        "--print-summary",
        action="store_true",
        help="Also print the full markdown summary to stdout after the count line.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.write and not args.probe:
        parser.error(
            "refusing to run without --write or --probe "
            "(pass --probe for read-only counts, or --write to emit triage files)"
        )

    try:
        result = run_triage(
            candidates_path=args.candidates,
            db_path=args.db,
            vesum_db=args.vesum_db,
            out_path=args.out,
            summary_path=args.summary_out,
            write=bool(args.write),
            limit=args.limit,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(format_cli_summary(result))
    if args.print_summary:
        print()
        print(result.summary_md)
    return 0


def _resolve(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
