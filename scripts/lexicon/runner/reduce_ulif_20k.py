#!/usr/bin/env python3
"""Durable offline reduce for the Atlas 20k ULIF network cache (#5230).

Consumes ``network-cache.sqlite`` raw envelopes (read-only) written by
``fetch_ulif_20k.py``, parses DictUA HTML into structured lemma artifacts,
stages a resumable ledger phase ``offline_reduce``, and emits a candidate
export + aggregate divergence summary.  Stops before publish/pin-flip.

Does not open ``sources.db`` unless ``--with-offline-enrich`` is passed (then
delegates to :func:`scripts.lexicon.runner.offline_engine.enrich_offline_slice`
for sealed CEFR/relations — memory-heavy; prefer VPS under 1.5/2.0 GiB caps).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

EXPECTED_COHORT_SHA256 = "858f0c7ce34d0d1e27c3519695073ea3e62bc0623010c03683137b7b730dcab4"
EXPECTED_COHORT_COUNT = 20_323


def _load_repo(repo: Path) -> None:
    sys.path.insert(0, str(repo))


def _event(name: str, **fields: Any) -> None:
    print(
        json.dumps({"event": name, "at": time.time(), **fields}, ensure_ascii=False, sort_keys=True),
        flush=True,
    )


def _run(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    _load_repo(repo)
    from scripts.lexicon.runner.memory import MemoryPolicy, apply_worker_memory_limit
    from scripts.lexicon.runner.offline_reduce import reduce_offline_slice

    work_dir = args.work_dir.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

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

    lemmas: list[str] | None = None
    expected_sha = EXPECTED_COHORT_SHA256 if not args.skip_cohort_pin else None
    expected_count = EXPECTED_COHORT_COUNT if not args.skip_cohort_pin else None
    if args.slice_file is not None:
        lemmas = [
            line.strip() for line in Path(args.slice_file).read_text(encoding="utf-8").splitlines() if line.strip()
        ]
        expected_sha = None
        expected_count = None

    result = reduce_offline_slice(
        network_cache=args.network_cache.resolve(),
        work_dir=work_dir,
        cohort_path=None if lemmas is not None else args.cohort.resolve(),
        lemmas=lemmas,
        output_path=args.output.resolve() if args.output else None,
        divergence_path=args.divergence.resolve() if args.divergence else None,
        baseline_path=args.baseline.resolve() if args.baseline else None,
        ledger_path=args.ledger.resolve() if args.ledger else None,
        run_id=args.run_id,
        force_new_run=args.force_new_run,
        max_lemmas=args.max_lemmas,
        include_raw_html=args.include_raw_html,
        expected_cohort_sha256=expected_sha,
        expected_cohort_count=expected_count,
    )
    if result.get("error"):
        _event("reduce_failed", **result)
        return 2
    _event("reduce_summary", **{k: v for k, v in result.items() if k != "divergence"})
    if args.with_offline_enrich:
        return _maybe_enrich(args, repo, work_dir, result)
    return 0


def _maybe_enrich(
    args: argparse.Namespace,
    repo: Path,
    work_dir: Path,
    reduce_result: dict[str, Any],
) -> int:
    """Optional sealed offline enrich pass (CEFR + relations) on the candidate."""
    sources = args.sources_db
    kaikki = args.kaikki_json
    if sources is None or not Path(sources).is_file():
        _event(
            "offline_enrich_blocked",
            reason="sources.db missing",
            sources=str(sources),
        )
        return 0
    if kaikki is None or not Path(kaikki).is_file():
        _event(
            "offline_enrich_blocked",
            reason="kaikki lookup missing",
            kaikki=str(kaikki),
        )
        return 0
    candidate = Path(reduce_result["candidate"]["output_path"])
    if not candidate.is_file():
        _event("offline_enrich_blocked", reason="candidate missing", path=str(candidate))
        return 0

    from scripts.lexicon.runner.memory import MemoryPolicy
    from scripts.lexicon.runner.offline_engine import enrich_offline_slice

    enrich_dir = work_dir / "offline_enrich"
    enrich_dir.mkdir(parents=True, exist_ok=True)
    out = enrich_dir / "candidate-enriched.json"
    policy = MemoryPolicy(
        high_bytes=int(args.memory_high_mib) * 1024**2,
        max_bytes=int(args.memory_max_mib) * 1024**2,
    )
    _event("offline_enrich_start", candidate=str(candidate), sources=str(sources))
    enrich_result = enrich_offline_slice(
        manifest_path=candidate,
        sources_db=Path(sources),
        kaikki_json=Path(kaikki),
        work_dir=enrich_dir,
        output_path=out,
        grac_cache={},
        memory_policy=policy,
        chunk_size=int(args.enrich_chunk_size),
        require_memory_self_test=bool(args.require_memory_cap),
        skip_workers=True,
        stop_after_chunks=args.enrich_stop_after_chunks,
    )
    summary_keys = (
        "run_id",
        "completed",
        "failed_terminal",
        "interrupted",
        "output_path",
        "error",
    )
    _event(
        "offline_enrich_summary",
        **{key: enrich_result.get(key) for key in summary_keys},
    )
    if enrich_result.get("error"):
        return 3
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("/home/ops/atlas-runner/run-20k"),
    )
    parser.add_argument(
        "--network-cache",
        type=Path,
        default=None,
        help="Path to network-cache.sqlite (default: <work-dir>/network-cache.sqlite)",
    )
    parser.add_argument(
        "--cohort",
        type=Path,
        default=Path("data/lexicon/cohort-20k-20260717.txt"),
    )
    parser.add_argument(
        "--slice-file",
        type=Path,
        default=None,
        help="Optional lemma list for dry-run slices (skips cohort pin)",
    )
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--divergence", type=Path, default=None)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Optional live Atlas baseline manifest for #5331 aggregate deltas",
    )
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--force-new-run", action="store_true")
    parser.add_argument("--max-lemmas", type=int, default=None)
    parser.add_argument("--include-raw-html", action="store_true")
    parser.add_argument("--skip-cohort-pin", action="store_true")
    parser.add_argument("--memory-high-mib", type=int, default=1536)
    parser.add_argument("--memory-max-mib", type=int, default=2048)
    parser.add_argument(
        "--require-memory-cap",
        action="store_true",
        help="Fail if OS cannot enforce MemoryPolicy (default on Linux VPS launch)",
    )
    parser.add_argument(
        "--with-offline-enrich",
        action="store_true",
        help="After reduce, run sealed CEFR/relations offline_engine on the candidate",
    )
    parser.add_argument(
        "--sources-db",
        type=Path,
        default=None,
        help="sources.db for --with-offline-enrich",
    )
    parser.add_argument(
        "--kaikki-json",
        type=Path,
        default=None,
        help="kaikki_uk_lookup.json for --with-offline-enrich",
    )
    parser.add_argument("--enrich-chunk-size", type=int, default=25)
    parser.add_argument("--enrich-stop-after-chunks", type=int, default=None)
    args = parser.parse_args()
    if args.network_cache is None:
        args.network_cache = args.work_dir / "network-cache.sqlite"
    if args.with_offline_enrich:
        if args.sources_db is None:
            args.sources_db = args.repo / "data" / "sources.db"
        if args.kaikki_json is None:
            args.kaikki_json = args.repo / "data" / "lexicon" / "kaikki_uk_lookup.json"
    return _run(args)


if __name__ == "__main__":
    raise SystemExit(main())
