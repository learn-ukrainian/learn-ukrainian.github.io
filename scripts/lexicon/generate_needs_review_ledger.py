#!/usr/bin/env python3
"""Generate a sha-bound needs_review re-entry ledger from deterministic triage.

Reads grow ``needs_review`` candidates plus ``needs-review-triage.json`` and emits
a fail-closed ``atlas_grow_needs_review_decisions`` YAML ledger: one decision per
held entry, bound to both file SHA digests. CODE maps triage actions only —
``promote_with_gloss`` → approve (+ approved_gloss), ``truly_missing`` /
``heritage_flag`` → deferred (heritage rows carry ``heritage: true``).

When to use: after triage has ranked held grow lemmas and before
``promote_grow_candidates.py --needs-review-ledger`` promotes the approve set.
When NOT to use: inventing glosses, partial human spot-check ledgers outside
this code path, or writing the live manifest (promotion is a separate step).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.promote_grow_candidates import (
    NEEDS_REVIEW_LEDGER_KIND,
    _held_rows,
    index_by_decision_key,
    require_exact_decision_coverage,
)
from scripts.lexicon.triage_needs_review import (
    MACHINE_HERITAGE,
    MACHINE_MISSING,
    MACHINE_PROMOTE,
)

DEFAULT_CANDIDATES = PROJECT_ROOT / "data" / "lexicon" / "grow_candidates.json"
DEFAULT_TRIAGE = PROJECT_ROOT / "data" / "lexicon" / "needs-review-triage.json"
DEFAULT_DECISIONS_DIR = PROJECT_ROOT / "data" / "lexicon" / "source-inventory-review-decisions"
BATCH_SLUG = "grow-needs-review-batch-01"


@dataclass(frozen=True)
class GenerateResult:
    ledger: dict[str, Any]
    out_path: Path
    written: bool
    dry_run: bool
    approve_count: int
    deferred_count: int
    heritage_count: int
    total: int


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_triage_entries(triage_path: Path) -> list[Mapping[str, Any]]:
    payload = json.loads(triage_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"triage payload must be a JSON object: {triage_path}")
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"triage entries must be a list: {triage_path}")
    return [row for row in entries if isinstance(row, Mapping)]


def load_candidates_payload(candidates_path: Path) -> dict[str, Any]:
    payload = json.loads(candidates_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"candidates payload must be a JSON object: {candidates_path}")
    return payload


def decision_from_triage(row: Mapping[str, Any]) -> dict[str, Any]:
    """Map one triage record to a ledger decision row (code-only)."""
    lemma = str(row.get("lemma") or "").strip()
    pos = str(row.get("pos") or "").strip()
    if not lemma:
        raise ValueError("triage row lacks lemma")
    if not pos:
        raise ValueError(f"triage row lacks pos: {lemma!r}")

    action = str(row.get("machine_action") or "").strip()
    base: dict[str, Any] = {"lemma": lemma, "pos": pos}

    if action == MACHINE_PROMOTE:
        gloss = row.get("best_gloss")
        if not isinstance(gloss, Mapping):
            raise ValueError(f"promote_with_gloss row lacks best_gloss: {lemma!r}")
        text = str(gloss.get("text") or "").strip()
        source = str(gloss.get("source") or "").strip()
        if not text or not source:
            raise ValueError(f"promote_with_gloss best_gloss incomplete: {lemma!r}")
        base["decision"] = "approve"
        base["approved_gloss"] = {"text": text, "source": source}
        return base

    if action == MACHINE_MISSING:
        base["decision"] = "deferred"
        base["reason"] = "truly_missing"
        return base

    if action == MACHINE_HERITAGE:
        base["decision"] = "deferred"
        base["heritage"] = True
        base["reason"] = "heritage_flag"
        held = str(row.get("held_reason") or "").strip()
        if held:
            base["held_reason"] = held
        return base

    raise ValueError(f"unknown machine_action for {lemma!r}: {action!r}")


def build_needs_review_ledger(
    *,
    candidates_path: Path,
    triage_path: Path,
    reviewed_at: str | None = None,
    batch_id: str | None = None,
) -> dict[str, Any]:
    """Build the full ledger mapping; exact-covers needs_review vs triage."""
    candidates_path = _resolve(candidates_path)
    triage_path = _resolve(triage_path)
    if not candidates_path.exists():
        raise ValueError(f"candidates file not found: {candidates_path}")
    if not triage_path.exists():
        raise ValueError(f"triage file not found: {triage_path}")

    candidates_payload = load_candidates_payload(candidates_path)
    held_rows = _held_rows(candidates_payload.get("needs_review", []))
    held_entries = [row.entry for row in held_rows]
    held_by_key = index_by_decision_key(held_entries, label="needs_review candidate")

    triage_entries = load_triage_entries(triage_path)
    triage_by_key = index_by_decision_key(triage_entries, label="triage entry")
    require_exact_decision_coverage(
        set(held_by_key),
        set(triage_by_key),
        scope_label="needs_review candidates",
        ledger_label="triage JSON",
    )

    # Emit decisions in candidates needs_review order (stable, fail-closed coverage).
    decisions: list[dict[str, Any]] = []
    for key in held_by_key:
        decisions.append(decision_from_triage(triage_by_key[key]))

    approve_count = sum(1 for row in decisions if row.get("decision") == "approve")
    deferred_count = sum(1 for row in decisions if row.get("decision") == "deferred")
    heritage_count = sum(1 for row in decisions if row.get("heritage") is True)

    day = reviewed_at or datetime.now(UTC).date().isoformat()
    resolved_batch_id = batch_id or f"{BATCH_SLUG}-{day}"

    return {
        "version": 1,
        "kind": NEEDS_REVIEW_LEDGER_KIND,
        "batch_id": resolved_batch_id,
        "batch_label": BATCH_SLUG,
        "reviewed_at": day,
        "generated_by": "scripts/lexicon/generate_needs_review_ledger.py",
        "epic": "#5230 needs_review re-entry (code-decided promote_with_gloss batch)",
        "scope": (
            "Full needs_review set from grow_candidates.json; decisions mapped "
            "from needs-review-triage.json machine_action only (no LLM judging)."
        ),
        "provenance": {
            "candidates_sha256": file_sha256(candidates_path),
            "triage_sha256": file_sha256(triage_path),
            "candidates": _display_path(candidates_path),
            "triage": _display_path(triage_path),
        },
        "decision_counts": {
            "approve": approve_count,
            "deferred": deferred_count,
            "heritage_flag": heritage_count,
            "total": len(decisions),
        },
        "decisions": decisions,
    }


def default_out_path(*, reviewed_at: str | None = None, out_dir: Path | None = None) -> Path:
    day = reviewed_at or datetime.now(UTC).date().isoformat()
    directory = _resolve(out_dir) if out_dir is not None else DEFAULT_DECISIONS_DIR
    return directory / f"{day}-{BATCH_SLUG}.yaml"


def generate_needs_review_ledger(
    *,
    candidates_path: Path = DEFAULT_CANDIDATES,
    triage_path: Path = DEFAULT_TRIAGE,
    out_path: Path | None = None,
    write: bool = False,
    reviewed_at: str | None = None,
) -> GenerateResult:
    """Build (and optionally write) the needs_review decisions ledger."""
    ledger = build_needs_review_ledger(
        candidates_path=candidates_path,
        triage_path=triage_path,
        reviewed_at=reviewed_at,
    )
    day = str(ledger.get("reviewed_at") or datetime.now(UTC).date().isoformat())
    resolved_out = _resolve(out_path) if out_path is not None else default_out_path(reviewed_at=day)
    counts = ledger.get("decision_counts") if isinstance(ledger.get("decision_counts"), Mapping) else {}
    approve_count = int(counts.get("approve") or 0)
    deferred_count = int(counts.get("deferred") or 0)
    heritage_count = int(counts.get("heritage_flag") or 0)
    total = int(counts.get("total") or len(ledger.get("decisions") or []))

    written = False
    if write:
        resolved_out.parent.mkdir(parents=True, exist_ok=True)
        resolved_out.write_text(
            yaml.safe_dump(ledger, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        written = True

    return GenerateResult(
        ledger=ledger,
        out_path=resolved_out,
        written=written,
        dry_run=not write,
        approve_count=approve_count,
        deferred_count=deferred_count,
        heritage_count=heritage_count,
        total=total,
    )


def format_cli_summary(result: GenerateResult) -> str:
    return "\n".join(
        [
            f"Mode: {'write' if result.written else 'dry-run (not written)'}",
            f"Out: {_display_path(result.out_path)}",
            f"Written: {str(result.written).lower()}",
            f"Total decisions: {result.total}",
            f"  approve: {result.approve_count}",
            f"  deferred: {result.deferred_count}",
            f"  heritage_flag (subset of deferred): {result.heritage_count}",
            f"kind: {NEEDS_REVIEW_LEDGER_KIND}",
            f"candidates_sha256: {result.ledger['provenance']['candidates_sha256']}",
            f"triage_sha256: {result.ledger['provenance']['triage_sha256']}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a sha-bound atlas_grow_needs_review_decisions ledger from "
            "deterministic needs-review triage. Use this after triage_needs_review.py "
            "and before promote_grow_candidates.py --needs-review-ledger; do not use it "
            "to write the live manifest or to invent glosses."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Dry-run counts (no files written)\n"
            "  .venv/bin/python scripts/lexicon/generate_needs_review_ledger.py --dry-run \\\n"
            "    --candidates data/lexicon/grow_candidates.json \\\n"
            "    --triage data/lexicon/needs-review-triage.json\n"
            "\n"
            "  # Write the dated batch ledger (orchestrator on primary)\n"
            "  .venv/bin/python scripts/lexicon/generate_needs_review_ledger.py --write \\\n"
            "    --candidates data/lexicon/grow_candidates.json \\\n"
            "    --triage data/lexicon/needs-review-triage.json\n"
            "\n"
            "Outputs (only with --write):\n"
            "  data/lexicon/source-inventory-review-decisions/"
            "<date>-grow-needs-review-batch-01.yaml\n"
            "\n"
            "Exit codes:\n"
            "  0  success (--help, --dry-run, or successful --write)\n"
            "  2  refused (no --write/--dry-run) or validation/input error\n"
            "\n"
            "Related:\n"
            "  scripts/lexicon/triage_needs_review.py       — produces triage JSON\n"
            "  scripts/lexicon/promote_grow_candidates.py   — consumes this ledger\n"
            "  issue #5230                                 — needs_review re-entry arc\n"
        ),
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=DEFAULT_CANDIDATES,
        help=f"Path to grow_candidates.json (default: {DEFAULT_CANDIDATES})",
    )
    parser.add_argument(
        "--triage",
        type=Path,
        default=DEFAULT_TRIAGE,
        help=f"Path to needs-review-triage.json (default: {DEFAULT_TRIAGE})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Output YAML path (default: "
            "data/lexicon/source-inventory-review-decisions/<UTC-date>-"
            f"{BATCH_SLUG}.yaml)"
        ),
    )
    parser.add_argument(
        "--reviewed-at",
        type=str,
        default=None,
        help="Optional ISO date for batch filename/metadata (default: UTC today)",
    )
    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write the ledger YAML. Default without --write/--dry-run: refuse (exit 2).",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print decision counts without writing files.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.write and not args.dry_run:
        parser.error(
            "refusing to run without --write or --dry-run "
            "(pass --dry-run for counts only, or --write to emit the ledger YAML)"
        )

    try:
        result = generate_needs_review_ledger(
            candidates_path=args.candidates,
            triage_path=args.triage,
            out_path=args.out,
            write=bool(args.write),
            reviewed_at=args.reviewed_at,
        )
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(format_cli_summary(result))
    return 0


def _resolve(path: Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _display_path(path: Path) -> str:
    path = _resolve(path)
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
