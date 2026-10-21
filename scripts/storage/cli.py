"""CLI for storage topology and SQLite database permission holds.

What it does: reports topology or holds/lifts database and companion permissions.
When to use: onboarding, path debugging, and quiesced SQLite maintenance.
When NOT to use: do not use this to copy, delete, or evict corpus files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.storage.topology import resolve_topology
from scripts.storage.wal_permissions import hold_database, lift_database


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
    return parser


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
    if args.command in {"hold", "lift"}:
        operation, mode = (hold_database, 0o444) if args.command == "hold" else (lift_database, 0o644)
        try:
            affected = operation(args.db_path)
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
