#!/usr/bin/env python3
"""Durable offline enrich driver for the Atlas 20k ULIF path (#5230 / #5331).

Consumes a reduce candidate (``candidate-ulif-reduce.json``) or any Atlas-style
entries manifest, runs sealed CEFR + relations + per-chunk leaf enrichment via
:func:`scripts.lexicon.runner.offline_engine.enrich_offline_slice`, and stages a
resumable ledger under ``--work-dir``.

**Stops before** finalize / publication archive / pin-flip.  Those are separate
operator steps (``finalize.py`` + publish gate) and are intentionally out of
scope for this driver.

#5393 class: bare invocation and ``--help`` never start a multi-hour enrich run.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

# VPS defaults (MemoryHigh=1.5G MemoryMax=2.0G); local tests override.
DEFAULT_MEMORY_HIGH_MIB = 1536
DEFAULT_MEMORY_MAX_MIB = 2048
DEFAULT_CHUNK_SIZE = 25


def _load_repo(repo: Path) -> None:
    sys.path.insert(0, str(repo))


def _event(name: str, **fields: Any) -> None:
    print(
        json.dumps({"event": name, "at": time.time(), **fields}, ensure_ascii=False, sort_keys=True),
        flush=True,
    )


def _resolve_input(args: argparse.Namespace) -> Path | None:
    """Return the candidate/manifest path (``--candidate`` wins over ``--manifest``)."""
    if args.candidate is not None:
        return Path(args.candidate)
    if args.manifest is not None:
        return Path(args.manifest)
    return None


def _count_entries(path: Path) -> int:
    """Count entries without building a full in-memory list when ijson is available."""
    try:
        import ijson  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        ijson = None  # type: ignore[assignment]

    if ijson is None:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise ValueError(f"{path} missing entries list")
        return len(entries)

    count = 0
    with path.open("rb") as handle:
        for _ in ijson.items(handle, "entries.item"):
            count += 1
    return count


def _slice_candidate(
    source: Path,
    dest: Path,
    *,
    max_lemmas: int,
) -> dict[str, Any]:
    """Write a truncated Atlas-style candidate with the first ``max_lemmas`` entries."""
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a JSON object")
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"{source} missing entries list")
    sliced = entries[: max(0, int(max_lemmas))]
    out = {**data, "entries": sliced}
    # Preserve reduce phase markers when present; mark slice for operators.
    out["offline_enrich_slice"] = {
        "max_lemmas": int(max_lemmas),
        "source_entry_count": len(entries),
        "sliced_entry_count": len(sliced),
        "source_path": str(source),
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps(out, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "path": str(dest),
        "source_entry_count": len(entries),
        "sliced_entry_count": len(sliced),
    }


def _load_grac_cache(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object (lemma_key → rank payload)")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Working directory for ledger, seals, side DBs, artifacts (required to run)",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        default=None,
        help="Reduce candidate JSON (e.g. candidate-ulif-reduce.json)",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Alias for --candidate: any Atlas-style {entries:[...]} manifest",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=None,
        help="sources.db (default: <repo>/data/sources.db)",
    )
    parser.add_argument(
        "--kaikki-json",
        type=Path,
        default=None,
        help="kaikki_uk_lookup.json (default: <repo>/data/lexicon/kaikki_uk_lookup.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Enriched candidate JSON (default: <work-dir>/candidate-enriched.json)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Lemmas per leaf chunk (default {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--stop-after-chunks",
        type=int,
        default=None,
        help="Process at most N pending chunks this invocation (resume-friendly)",
    )
    parser.add_argument(
        "--max-lemmas",
        type=int,
        default=None,
        help="Truncate input to first N lemmas before enrich (fixture / dry-run slices)",
    )
    parser.add_argument("--ledger", type=Path, default=None, help="Ledger path (default: <work-dir>/ledger.sqlite)")
    parser.add_argument("--run-id", type=str, default=None, help="Resume this ledger run_id")
    parser.add_argument("--force-new-run", action="store_true")
    parser.add_argument(
        "--grac-cache",
        type=Path,
        default=None,
        help="Optional pre-seeded GRAC frequency JSON (tests / offline hosts)",
    )
    parser.add_argument("--memory-high-mib", type=int, default=DEFAULT_MEMORY_HIGH_MIB)
    parser.add_argument("--memory-max-mib", type=int, default=DEFAULT_MEMORY_MAX_MIB)
    parser.add_argument(
        "--require-memory-cap",
        action="store_true",
        help="Fail if OS cannot enforce MemoryPolicy (default on Linux VPS launch)",
    )
    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Run leaf enrich in-process (skip capped worker spawn; tests / tiny slices)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print plan only; do not open sources.db or enrich",
    )
    parser.add_argument(
        "--owner-id",
        type=str,
        default=None,
        help="Ledger owner id (default: process-local auto)",
    )
    return parser


def _refuse_bare(parser: argparse.ArgumentParser) -> int:
    parser.print_usage(sys.stderr)
    print(
        "refusing: bare invocation would start offline enrich. "
        "Pass --candidate/--manifest and --work-dir (or --help / --dry-run).",
        file=sys.stderr,
    )
    return 2


def dry_run_plan(args: argparse.Namespace) -> int:
    """Emit a dry-run plan event without starting enrichment."""
    repo = args.repo.resolve()
    input_path = _resolve_input(args)
    work_dir = args.work_dir.resolve() if args.work_dir is not None else None
    sources = (
        Path(args.sources_db).resolve()
        if args.sources_db is not None
        else (repo / "data" / "sources.db")
    )
    kaikki = (
        Path(args.kaikki_json).resolve()
        if args.kaikki_json is not None
        else (repo / "data" / "lexicon" / "kaikki_uk_lookup.json")
    )
    output = (
        Path(args.output).resolve()
        if args.output is not None
        else ((work_dir / "candidate-enriched.json") if work_dir is not None else None)
    )

    entry_count: int | None = None
    missing: list[str] = []
    if input_path is None:
        missing.append("candidate/manifest")
    else:
        if not input_path.is_file():
            missing.append(f"input missing: {input_path}")
        else:
            try:
                entry_count = _count_entries(input_path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                missing.append(f"input unreadable: {exc}")

    if work_dir is None:
        missing.append("work-dir")
    if not sources.is_file():
        missing.append(f"sources-db missing: {sources}")
    if not kaikki.is_file():
        missing.append(f"kaikki-json missing: {kaikki}")

    effective_count = entry_count
    if entry_count is not None and args.max_lemmas is not None:
        effective_count = min(entry_count, max(0, int(args.max_lemmas)))
    chunk_size = max(1, int(args.chunk_size))
    planned_chunks = (
        (effective_count + chunk_size - 1) // chunk_size if effective_count is not None else None
    )

    plan = {
        "kind": "atlas-offline-enrich-dry-run",
        "issue_refs": ["#5230", "#5331"],
        "repo": str(repo),
        "work_dir": str(work_dir) if work_dir else None,
        "input": str(input_path) if input_path else None,
        "sources_db": str(sources),
        "kaikki_json": str(kaikki),
        "output": str(output) if output else None,
        "entry_count": entry_count,
        "effective_entry_count": effective_count,
        "chunk_size": chunk_size,
        "planned_chunks": planned_chunks,
        "stop_after_chunks": args.stop_after_chunks,
        "max_lemmas": args.max_lemmas,
        "memory_high_mib": args.memory_high_mib,
        "memory_max_mib": args.memory_max_mib,
        "in_process": bool(args.in_process),
        "stops_before": ["finalize", "publish", "pin_flip"],
        "missing": missing,
        "ok": not missing,
    }
    _event("offline_enrich_dry_run", **plan)
    return 0 if not missing else 2


def _run(args: argparse.Namespace) -> int:
    if args.dry_run:
        return dry_run_plan(args)

    input_path = _resolve_input(args)
    if input_path is None or args.work_dir is None:
        return _refuse_bare(build_parser())

    repo = args.repo.resolve()
    _load_repo(repo)
    from scripts.lexicon.runner.memory import MemoryPolicy, apply_worker_memory_limit
    from scripts.lexicon.runner.offline_engine import enrich_offline_slice

    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    input_path = input_path.resolve()
    if not input_path.is_file():
        _event("offline_enrich_failed", error="input_missing", path=str(input_path))
        return 2

    sources = (
        Path(args.sources_db).resolve()
        if args.sources_db is not None
        else (repo / "data" / "sources.db")
    )
    kaikki = (
        Path(args.kaikki_json).resolve()
        if args.kaikki_json is not None
        else (repo / "data" / "lexicon" / "kaikki_uk_lookup.json")
    )
    if not sources.is_file():
        _event("offline_enrich_failed", error="sources_db_missing", path=str(sources))
        return 2
    if not kaikki.is_file():
        _event("offline_enrich_failed", error="kaikki_json_missing", path=str(kaikki))
        return 2

    memory_policy = MemoryPolicy(
        high_bytes=int(args.memory_high_mib) * 1024**2,
        max_bytes=int(args.memory_max_mib) * 1024**2,
    )
    enforcement = apply_worker_memory_limit(memory_policy)
    _event(
        "memory_policy",
        enforcement=enforcement,
        high_bytes=memory_policy.high_bytes,
        max_bytes=memory_policy.max_bytes,
    )
    if args.require_memory_cap and enforcement == "none":
        raise RuntimeError("MemoryPolicy could not enforce a hard cap")

    manifest_for_engine = input_path
    if args.max_lemmas is not None:
        slice_path = work_dir / "candidate-slice.json"
        slice_meta = _slice_candidate(input_path, slice_path, max_lemmas=int(args.max_lemmas))
        _event("offline_enrich_slice", **slice_meta)
        manifest_for_engine = slice_path

    output = (
        Path(args.output).resolve()
        if args.output is not None
        else (work_dir / "candidate-enriched.json")
    )
    ledger_path = Path(args.ledger).resolve() if args.ledger is not None else None
    grac_cache = _load_grac_cache(Path(args.grac_cache) if args.grac_cache else None)

    _event(
        "offline_enrich_start",
        candidate=str(manifest_for_engine),
        sources=str(sources),
        kaikki=str(kaikki),
        work_dir=str(work_dir),
        output=str(output),
        chunk_size=int(args.chunk_size),
        stop_after_chunks=args.stop_after_chunks,
        in_process=bool(args.in_process),
    )

    result = enrich_offline_slice(
        manifest_path=manifest_for_engine,
        sources_db=sources,
        kaikki_json=kaikki,
        work_dir=work_dir,
        output_path=output,
        grac_cache=grac_cache,
        memory_policy=memory_policy,
        chunk_size=max(1, int(args.chunk_size)),
        require_memory_self_test=bool(args.require_memory_cap),
        skip_workers=bool(args.in_process),
        ledger_path=ledger_path,
        run_id=args.run_id,
        force_new_run=bool(args.force_new_run),
        stop_after_chunks=args.stop_after_chunks,
        owner_id=args.owner_id,
    )

    summary_keys = (
        "run_id",
        "fingerprint",
        "completed",
        "failed_terminal",
        "interrupted",
        "processed_this_invocation",
        "entry_count",
        "output_path",
        "ledger_path",
        "cefr_seal",
        "relations_seal",
        "error",
        "detail",
        "resumable_run_id",
    )
    _event(
        "offline_enrich_summary",
        **{key: result.get(key) for key in summary_keys if key in result or key == "error"},
        stops_before=["finalize", "publish", "pin_flip"],
    )
    if result.get("error"):
        return 3
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    raw = list(sys.argv[1:] if argv is None else argv)
    # #5393: bare invocation must not start multi-hour enrich.
    if not raw:
        return _refuse_bare(parser)
    args = parser.parse_args(raw)
    # --help is handled by argparse (SystemExit 0) before we get here.
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
