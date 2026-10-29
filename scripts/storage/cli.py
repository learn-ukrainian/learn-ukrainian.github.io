"""CLI for storage topology, SQLite permission holds and Sources store generations.

What it does: reports topology; holds/lifts database and companion permissions;
runs a writer under the Sources store writer lock; bootstraps the generation
layout; reports generations.
When to use: onboarding, path debugging, quiesced SQLite maintenance, and any
write to the live Sources store by a script that does not take the lock itself.
When NOT to use: do not use this to copy, delete, or evict corpus files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from scripts.storage import generations
from scripts.storage.topology import resolve_topology
from scripts.storage.wal_permissions import hold_database, lift_database

# A writer run through ``write`` is killed after this long unless --timeout says otherwise.
WRITER_TIMEOUT_SECONDS = 24 * 60 * 60


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.storage",
        description=(
            "Report storage topology or hold/lift SQLite database permissions.\n"
            "Use status for debugging and hold/lift for quiesced maintenance; "
            "never use this to evict/delete bulk sources."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.storage status\n"
            "  .venv/bin/python -m scripts.storage status --json\n"
            "  .venv/bin/python -m scripts.storage hold example.db --json\n"
            "  .venv/bin/python -m scripts.storage generations --json\n"
            "  .venv/bin/python -m scripts.storage write -- .venv/bin/python scripts/ingest/x.py --db data/sources.db\n"
            "\n"
            "From a dispatch worktree, use the primary checkout interpreter:\n"
            "  <primary-checkout>/.venv/bin/python -m scripts.storage status\n"
            "Never create or use a worktree-local .venv for project commands.\n"
            "\n"
            "Outputs:\n"
            "  Human text or JSON on stdout. Status is read-only. Hold/lift change\n"
            "  db and existing companion modes to 0444/0644. No cloud materialization.\n"
            "\n"
            "Exit codes:\n"
            "  0 — status emitted or permissions changed\n"
            "  1 — permission change failed (see stderr for rollback failures)\n"
            "  2 — invalid arguments\n"
            "  3 — a Sources store operation was refused (reason on stderr)\n"
            "  write — the writer's own exit code once the lock was held; 124 if it timed out\n"
            "\n"
            "Related:\n"
            "  docs/runbooks/storage-topology.md\n"
            "  agents_extensions/shared/rules/storage-topology.md\n"
            "  issue #6375 (Phase 3 recovery storage dependency)\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status = sub.add_parser(
        "status",
        help="Print read-only topology status (active DB + bulk root + Mac cache).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    status.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON (default: human text). Default: false.",
    )
    status.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Repository root to inspect (default: discover from cwd).",
    )
    for command, mode in (("hold", "0444"), ("lift", "0644")):
        permissions = sub.add_parser(
            command,
            help=f"Set database and existing companion permissions to {mode}.",
            description=(
                f"Set database and existing -wal/-shm/-journal permissions to {mode}.\n"
                "Quiesce clients first and reopen connections afterwards. This is\n"
                "not crash-atomic; original modes are restored on chmod failure."
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                f"Example: .venv/bin/python -m scripts.storage {command} example.db --json\n"
                "Outputs: changed path/mode pairs on stdout; file modes changed.\n"
                "Exit codes: 0 success; 1 filesystem/rollback failure; 2 invalid arguments.\n"
                "Related: docs/runbooks/storage-topology.md; issue #11284."
            ),
        )
        permissions.add_argument("db_path", type=Path, help="SQLite database path, e.g. example.db.")
        permissions.add_argument(
            "--json", action="store_true", help="Emit affected paths and octal modes as JSON (default: human text)."
        )

    store_help = "Sources store path, the selector or pre-bootstrap file (default: the primary checkout's)."
    status_parser = sub.add_parser(
        "generations",
        help="Print the Sources selector, the selected generation and retained generations (read-only).",
    )
    status_parser.add_argument("--json", action="store_true", help="Emit JSON (default: human text).")
    status_parser.add_argument("--store", type=Path, default=None, help=store_help)

    write = sub.add_parser(
        "write",
        help="Run one writer command under the Sources store writer lock.",
        description=(
            "Take the store writer lock (refused if busy), make the selected generation\n"
            "writable, run COMMAND with the locked descriptor inherited, then hold the\n"
            "generation again and release the lock. The command opens data/sources.db\n"
            "as before; the selector cannot move while it runs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    write.add_argument("--store", type=Path, default=None, help=store_help)
    write.add_argument(
        "--timeout",
        type=float,
        default=WRITER_TIMEOUT_SECONDS,
        help=(
            "Seconds the writer may run before it is killed and the lock released "
            f"(default: {WRITER_TIMEOUT_SECONDS:.0f}). SQLite rolls back an interrupted transaction."
        ),
    )
    write.add_argument("writer", nargs=argparse.REMAINDER, help="-- followed by the writer command and its arguments.")

    bootstrap = sub.add_parser(
        "bootstrap",
        help="Turn the regular data/sources.db into the first generation (maintenance window only).",
        description=(
            "Maintenance window only: every Sources reader and writer is stopped and a\n"
            "backup exists. Folds the WAL, refuses if any connection is still active,\n"
            "links the file into data/sources-generations/ and replaces data/sources.db\n"
            "with the selector. See docs/runbooks/storage-topology.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    bootstrap.add_argument("--store", type=Path, default=None, help=store_help)
    bootstrap.add_argument(
        "--maintenance-window",
        action="store_true",
        help="Confirm that all Sources readers and writers are stopped and a backup was taken.",
    )

    restore = sub.add_parser(
        "restore-generation",
        help="Select a generation restored under its own name in data/sources-generations/.",
        description=(
            "Used by restore: GENERATION must already sit in the store's generation\n"
            "directory under its own name. Takes the writer lock, holds the file\n"
            "read-only and switches the selector to it through the publisher. Works\n"
            "with no selector yet (a fresh restore) or an existing one."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    restore.add_argument("generation", type=Path, help="Restored generation file.")
    restore.add_argument("--store", type=Path, default=None, help=store_help)
    return parser


def _restore_generation(selector: Path, generation: Path) -> generations.Publication:
    with generations.writer_lock(selector, allow_missing=True) as held:
        return generations.publish_generation(generation, held, mode="restore")


def _selector(argument: Path | None) -> Path:
    return argument if argument is not None else generations.live_store_path()


def _change_permissions(command: str, db_path: Path) -> list[Path]:
    """Hold or lift a plain database, or the Sources store's selected generation under the lock."""
    operation = hold_database if command == "hold" else lift_database
    ref = generations.store_kind(db_path)
    if ref.kind == "other":
        return operation(db_path)
    if ref.selector is None:
        raise generations.GenerationError("generation_named_directly", "name the selector data/sources.db")
    with generations.writer_lock(ref.selector) as held:
        assert held.generation is not None
        return operation(held.generation)


def _run_writer(selector: Path, command: list[str], timeout: float) -> int:
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        raise generations.GenerationError("writer_command_missing")
    with generations.writer_lock(selector, lift=True) as held:
        if held.generation is None:
            raise generations.GenerationError("selector_missing")
        env = {
            **os.environ,
            generations.ENV_WRITER_FD: str(held.fd),
            generations.ENV_WRITER_SELECTOR: str(held.selector),
        }
        try:
            return subprocess.run(command, env=env, pass_fds=(held.fd,), check=False, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            print(f"write: writer killed after {timeout:g} s; the lock is released", file=sys.stderr)
            return 124


def _bootstrap(selector: Path) -> generations.Publication:
    with generations.writer_lock(selector) as held:
        generations.checkpoint_legacy_store(held)
        return generations.publish_generation(held.selector, held, mode="bootstrap")


def _format_human(payload: dict) -> str:
    lines: list[str] = []
    lines.append(f"schema: {payload['schema']}")
    lines.append(f"repository_root: {payload['repository_root']}")
    adb = payload["active_database"]
    lines.append("active_database:")
    lines.append(f"  path: {adb['path']}")
    lines.append(f"  exists: {adb['exists']}")
    lines.append(f"  is_local: {adb['is_local']}")
    lines.append(f"  refused_network: {adb['refused_network']}")
    lines.append(f"  reason: {adb['reason']}")
    lines.append(f"  size_bytes: {adb.get('size_bytes')}")
    lines.append(f"  journal_mode: {adb.get('journal_mode')}")
    lines.append(f"  wal_bytes: {adb.get('wal_bytes')}")
    bulk = payload["bulk_root"]
    lines.append("bulk_root:")
    lines.append(f"  available: {bulk['available']}")
    lines.append(f"  path: {bulk['path']}")
    lines.append(f"  source: {bulk['source']}")
    lines.append(f"  reason: {bulk['reason']}")
    if bulk.get("candidates"):
        lines.append("  candidates:")
        for cand in bulk["candidates"]:
            lines.append(
                f"    - kind={cand['kind']} present={cand['present']} "
                f"marker_valid={cand['marker_valid']} path={cand['path']} "
                f"reason={cand['reason']}"
            )
    cache = payload["mac_cache"]
    lines.append("mac_cache:")
    lines.append(f"  applicable: {cache['applicable']}")
    lines.append(f"  bulk_source: {cache['bulk_source']}")
    lines.append(f"  sampled_entries: {cache['sampled_entries']}")
    lines.append(f"  local_or_unknown: {cache['local_or_unknown']}")
    lines.append(f"  dataless_or_cloud_only: {cache['dataless_or_cloud_only']}")
    lines.append(f"  reason: {cache['reason']}")
    lines.append(f"  remove_download: {cache['remove_download_instruction']}")
    if payload.get("notes"):
        lines.append("notes:")
        for note in payload["notes"]:
            lines.append(f"  - {note}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {"generations", "write", "bootstrap", "restore-generation"}:
        selector = _selector(args.store)
        try:
            if args.command == "write":
                return _run_writer(selector, args.writer, args.timeout)
            if args.command == "bootstrap":
                if not args.maintenance_window:
                    parser.error("bootstrap requires --maintenance-window (see docs/runbooks/storage-topology.md)")
                publication = _bootstrap(selector)
                print(f"selector now selects {publication.generation.name}")
                return 0
            if args.command == "restore-generation":
                publication = _restore_generation(selector, args.generation)
                print(f"selector now selects {publication.generation.name}")
                return 0
        except generations.GenerationError as error:
            print(f"{args.command} refused: {error.reason}", file=sys.stderr)
            return 3
        payload = generations.generation_status(selector)
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"layout: {payload['layout']} ({payload['reason']})")
            print(f"selected: {payload['selected']} held={payload['held']}")
            for row in payload["generations"]:
                marker = "*" if row["selected"] else " "
                print(f" {marker} {row['name']} {row['size_bytes']} bytes receipt={row['receipt_state']}")
        return 0
    if args.command in {"hold", "lift"}:
        mode = 0o444 if args.command == "hold" else 0o644
        try:
            affected = _change_permissions(args.command, args.db_path)
        except generations.GenerationError as error:
            print(f"{args.command} refused: {error.reason}", file=sys.stderr)
            return 3
        except (OSError, ExceptionGroup) as error:
            print(f"{args.command} failed: {error}", file=sys.stderr)
            if isinstance(error, ExceptionGroup):
                for failure in error.exceptions:
                    print(f"  {failure}", file=sys.stderr)
            return 1
        payload = {str(path): f"{mode:04o}" for path in affected}
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for path, new_mode in payload.items():
                print(f"{path}: {new_mode}")
        return 0
    if args.command != "status":
        parser.error(f"unsupported command: {args.command}")
        return 2

    status = resolve_topology(repository_root=args.repo)
    payload = status.to_dict()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_human(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
