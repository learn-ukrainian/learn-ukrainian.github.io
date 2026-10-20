"""Command line for the lexdata store: build, verify, status, digests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.lexdata import build_store, generation, transforms, verify
from scripts.lib.readonly_sqlite import open_readonly
from scripts.storage import topology

RELATED = ("Related: design lexdata layer v1 r3 (§3, §4, §6, §8); "
           "agents_extensions/shared/rules/storage-topology.md; epic #8977.")


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def cmd_build(args: argparse.Namespace) -> int:
    try:
        target = build_store.writer_target()
        result = build_store.build(target)
    except build_store.BuildRefused as exc:
        _print({"status": "refused", "reason": exc.reason})
        return 2
    _print({"status": "published", "generation": result.generation, "size_bytes": result.size_bytes,
            "diff": result.diff, "peak_rss_bytes": result.peak_rss_bytes,
            "verify_ok": result.verify_receipt["ok"]})
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    if args.path is None:
        resolved = topology.resolve_store("lexdata")
    else:
        resolved = topology.resolve_store("lexdata", binding=topology.StoreBinding("lexdata", Path(args.path)))
    if isinstance(resolved, topology.StoreRefusal):
        _print({"status": "unavailable", "reason": resolved.reason})
        return 2
    conn = open_readonly(resolved.path)
    try:
        report = verify.verify_generation(conn, expect_status="published")
    finally:
        conn.close()
    _print(report.receipt())
    return 0 if report.ok else 1


def cmd_status(args: argparse.Namespace) -> int:
    opened = generation.open_generation()
    if isinstance(opened, generation.Unavailable):
        _print({"status": "unavailable", "reason": opened.reason, "generation": opened.generation})
        return 2
    try:
        meta = opened.meta
        _print({"status": "published", "generation": meta["generation"], "created_at": meta["created_at"],
                "normalizer_digest": meta["normalizer_digest"], "l1_transform_digests": meta["l1_transform_digests"],
                "diff": meta["diff_receipt"]})
    finally:
        opened.close()
    return 0


def cmd_digests(args: argparse.Namespace) -> int:
    problems = transforms.undeclared_imports()
    _print({"normalizer_digest": transforms.normalizer_digest(),
            "sources": {source: transforms.transform_digest(source) for source in sorted(transforms.SOURCES)},
            "undeclared_imports": problems})
    return 1 if problems else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.lexdata",
        description=("Build, verify and inspect the derived lexical store data/lexdata.db (L1 staging, L2 "
                     "crosswalk, L3 card inputs).\nUse it for lexdata generations only; it never writes "
                     "sources.db or vesum.db, and it is not a lookup tool (use the sources MCP for that)."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.lexdata status\n"
            "  .venv/bin/python -m scripts.lexdata digests\n"
            "  .venv/bin/python -m scripts.lexdata verify --path data/lexdata.db\n"
            "  .venv/bin/python -m scripts.lexdata build   # primary checkout only; detach if > 15 min\n"
            "Outputs: JSON on stdout. Only `build` writes: data/lexdata/lexdata.<gen>.db.tmp, then "
            "data/lexdata.db (atomic swap), data/lexdata/backups/, data/lexdata/reports/{build,verify}-<gen>.json.\n"
            "Exit codes: 0 = success; 1 = verification failed or undeclared transform imports; "
            "2 = refused or unavailable (reason printed, never a path).\n" + RELATED),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    build = sub.add_parser(
        "build", help="Build, verify and publish a new generation (single writer).",
        description=("Build one new generation under an exclusive lock, verify it, back up the current one and "
                     "swap it in atomically.\nRun from the primary checkout only: a linked worktree, a network or "
                     "unknown filesystem, or symlinked data paths are refused. Not for dry runs."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("Example:\n  .venv/bin/python -m scripts.lexdata build\n"
                "Outputs: data/lexdata.db; data/lexdata/backups/lexdata-<previous gen>-<utc>.db (two kept); "
                "data/lexdata/reports/build-<gen>.json and verify-<gen>.json (counts only).\n"
                "Budgets: refuses to start below 8.5 GB + 20 GB free; aborts below 20 GB free or above 2 GiB RSS. "
                "SQLite temp files are pinned to data/lexdata/tmp by the build itself (no launcher setting); "
                "it refuses when it cannot prove that.\n"
                "Exit codes: 0 = published; 2 = refused (build_locked, linked_worktree, disk_admission_refused, "
                "verify_failed, input_snapshot_changed:<source>, identity_store_changed, "
                "sqlite_tmpdir_outside_budget, ...).\n" + RELATED),
    )
    build.set_defaults(func=cmd_build)

    check = sub.add_parser(
        "verify", help="Run every generation invariant read-only and print the receipt.",
        description=("Run the §8 invariants on a published generation, read-only.\nUse it to audit a published "
                     "file; the build already verifies before it publishes."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("Example:\n  .venv/bin/python -m scripts.lexdata verify\n"
                "Outputs: the verify receipt (counts only) on stdout; nothing written.\n"
                "Exit codes: 0 = all invariants hold; 1 = a violation; 2 = store unavailable.\n" + RELATED),
    )
    check.add_argument("--path", default=None,
                       help="Absolute path of a generation file to verify (default: the resolved data/lexdata.db, "
                            "or LU_LEXDATA_DB). Example: /abs/path/data/lexdata.db")
    check.set_defaults(func=cmd_verify)

    status = sub.add_parser(
        "status", help="Say whether the published generation is usable by this code, and why not.",
        description=("Open the published generation the way every reader does and print its generation and "
                     "digests,\nor the unavailable reason (lexdata_unpublished, normalizer_mismatch, lexdata_stale "
                     "when this\ncode's transform digests differ from the generation's, ...)."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("Example:\n  .venv/bin/python -m scripts.lexdata status\n"
                "Outputs: JSON on stdout; nothing written.\n"
                "Exit codes: 0 = usable; 2 = unavailable.\n" + RELATED),
    )
    status.set_defaults(func=cmd_status)

    digests = sub.add_parser(
        "digests", help="Print this code's normalizer and per-source L1 transform digests.",
        description=("Print the content-addressed digests this checkout would build with, and any registered "
                     "module\nthat imports an unregistered project module. Use before a deploy to see whether "
                     "a rebuild is due."),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=("Example:\n  .venv/bin/python -m scripts.lexdata digests\n"
                "Outputs: JSON on stdout; nothing written.\n"
                "Exit codes: 0 = registry closed; 1 = undeclared transform imports.\n" + RELATED),
    )
    digests.set_defaults(func=cmd_digests)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
