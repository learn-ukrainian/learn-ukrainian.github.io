"""Operator and harness CLI for phase-one session streams."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from .db import SessionStreamDatabase
from .dual_write import (
    ATLAS_HANDOFF_PATH,
    list_handoff_candidates,
    mirror_atlas_handoff,
    mirror_handoff_file,
    resolve_handoff_path,
)
from .hooks import clean_exit_hook, heartbeat_hook, lease_from_environment
from .inventory import epic_handoff_map, inventory_covers_issue_streams, load_stream_epic_inventory
from .model import entry_as_dict
from .store import NotFoundError, SessionStreamError, SessionStreamStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="session-streams",
        description=(
            "Read agent-agnostic epic session streams and invoke their harness hook surface.\n"
            "Use during phase-one shadow/dual-write operation; do not use it to cut over or retire file handoffs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m agents_extensions.shared.session_streams tail --stream epic:4707 --limit 20
  .venv/bin/python -m agents_extensions.shared.session_streams dump --stream epic:4707 --format jsonl --output /tmp/stream.jsonl
  .venv/bin/python -m agents_extensions.shared.session_streams hook heartbeat

Outputs:
  tail writes a bounded pinned-plus-recent view to stdout. dump writes complete stream history
  to stdout or atomically to --output. hook mutates only the exact leased lifecycle projection.

Exit codes:
  0 success; 2 CLI usage; 3 exact stream not found; 4 lifecycle/lease/content refusal; 5 unexpected failure.

Related:
  agents_extensions/shared/docs/session-streams-design.md; tracking issue #5422; stream epic #4707.
""",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help=(
            "SQLite database path. Default: canonical primary-checkout "
            ".agent/session-streams/v1/session-streams.sqlite3."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    tail = subparsers.add_parser(
        "tail",
        help="Print pinned entries followed by the last N non-pinned entries.",
        description="Print the deterministic cold-start projection for one exact stream.",
    )
    tail.add_argument(
        "--stream",
        required=True,
        help="Exact stream ID, for example epic:4707 or shared:fleet.",
    )
    tail.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of recent non-pinned entries to include. Default: 20; range: 0-10000.",
    )
    tail.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output rendering. Default: table; json preserves full typed envelopes.",
    )

    dump = subparsers.add_parser(
        "dump",
        help="Export complete ordered history for one stream.",
        description="Dump sessions, leases, events, entries, refs, migrations, and legacy mirror receipts.",
    )
    dump.add_argument(
        "--stream",
        required=True,
        help="Exact stream ID, for example epic:4707 or shared:fleet.",
    )
    dump.add_argument(
        "--format",
        choices=("json", "jsonl"),
        default="json",
        help="Portable output encoding. Default: json; jsonl emits one typed record per line.",
    )
    dump.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Atomic output file path. Default: stdout; example: /tmp/epic-4707.jsonl.",
    )

    hook = subparsers.add_parser(
        "hook",
        help="Run the common harness-owned heartbeat or clean-exit hook.",
        description=(
            "Renew or close the exact lease from SESSION_STREAM_* environment fields. "
            "This surface is provider-independent."
        ),
    )
    hook.add_argument(
        "action",
        choices=("heartbeat", "close"),
        help="Harness lifecycle action: heartbeat renews TTL; close performs idempotent clean-exit close.",
    )

    mirror = subparsers.add_parser(
        "mirror-atlas",
        help="Mirror the Atlas file handoff into an explicit stream without cutover.",
        description=(
            "Read a stable Atlas handoff file, append it as state under the exact lease, and record its hash. "
            "The source file remains authoritative and is never edited or deleted."
        ),
    )
    mirror.add_argument(
        "--stream",
        required=True,
        help="Explicit Atlas stream ID, for example epic:4700; no Atlas epic is guessed.",
    )
    mirror.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root containing the legacy handoff. Default: current working directory.",
    )
    mirror.add_argument(
        "--source",
        type=Path,
        default=ATLAS_HANDOFF_PATH,
        help=(
            "Atlas handoff path relative to --repo-root. "
            "Default: .claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md."
        ),
    )

    mirror_handoff = subparsers.add_parser(
        "mirror-handoff",
        help="Mirror any registered epic file handoff into its stream (dual-write, no cutover).",
        description=(
            "Append a stable legacy handoff image under the exact lease. "
            "Uses EPIC_HANDOFF_CANDIDATES when --source is omitted. Never edits or deletes the file."
        ),
    )
    mirror_handoff.add_argument(
        "--stream",
        required=True,
        help="Stream ID, for example epic:4387.",
    )
    mirror_handoff.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Default: current working directory.",
    )
    mirror_handoff.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional handoff path (relative to --repo-root). Default: first existing registry path.",
    )
    mirror_handoff.add_argument(
        "--profile",
        default=None,
        help="Mirror profile label (default: stream id without epic: prefix).",
    )

    status = subparsers.add_parser(
        "dual-write-status",
        help="List registered epic handoff paths and whether each file exists (no cutover).",
        description=(
            "Phase-2 dual-write inventory: which streams have on-disk handoffs ready to mirror. "
            "Does not mutate the database."
        ),
    )
    status.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root. Default: current working directory.",
    )

    handoff_status = subparsers.add_parser(
        "handoff-status",
        help="Diagnose whether an epic stream is claimable by a successor driver (#5530).",
        description=(
            "Read-only: report open session, lease TTL, holder PID liveness, and whether "
            "proof-gated force-close + claim is allowed. See docs/runbooks/epic-stream-handoff.md."
        ),
    )
    handoff_status.add_argument(
        "--stream",
        required=True,
        help="Exact stream ID, for example epic:4542.",
    )
    handoff_status.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Output format. Default: text.",
    )

    handoff_claim = subparsers.add_parser(
        "handoff-claim",
        help="Force-close expired dead holder if needed, open a new session, pin new driver (#5530).",
        description=(
            "Cross-agent epic-stream claim. Refuses if a live unexpired lease exists. "
            "Claimer process must be live and instance_id must differ from the expired holder."
        ),
    )
    handoff_claim.add_argument("--stream", required=True, help="Exact stream ID, for example epic:4542.")
    handoff_claim.add_argument("--agent", required=True, help="Successor agent identity, for example claude.")
    handoff_claim.add_argument(
        "--harness",
        required=True,
        help="Successor harness identity, for example claude-code or grok-tui.",
    )
    handoff_claim.add_argument(
        "--instance-id",
        default=None,
        help="Distinct runtime instance id (default: auto-generated).",
    )
    handoff_claim.add_argument(
        "--process-id",
        type=int,
        default=None,
        help="Claimer process id (default: current PID).",
    )
    handoff_claim.add_argument(
        "--lineage-id",
        default=None,
        help="Session lineage id (default: lineage-<stream>-<agent>-<date>).",
    )
    handoff_claim.add_argument(
        "--ttl-seconds",
        type=int,
        default=6 * 3600,
        help="Lease TTL for the new session. Default: 21600.",
    )
    handoff_claim.add_argument(
        "--task-id",
        default=None,
        help="Optional task id for the lease holder.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = SessionStreamStore(SessionStreamDatabase(args.db))
    try:
        if args.command == "tail":
            return _tail(store, args)
        if args.command == "dump":
            return _dump(store, args)
        if args.command == "hook":
            return _hook(store, args)
        if args.command == "mirror-atlas":
            return _mirror_atlas(store, args)
        if args.command == "mirror-handoff":
            return _mirror_handoff(store, args)
        if args.command == "dual-write-status":
            return _dual_write_status(args)
        if args.command == "handoff-status":
            return _handoff_status(store, args)
        if args.command == "handoff-claim":
            return _handoff_claim(store, args)
        parser.error(f"unsupported command: {args.command}")
    except NotFoundError as exc:
        print(f"session-streams: {exc}", file=sys.stderr)
        return 3
    except (SessionStreamError, ValueError) as exc:
        print(f"session-streams: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:  # pragma: no cover - final CLI safety net
        print(f"session-streams: unexpected failure: {exc}", file=sys.stderr)
        return 5
    return 5


def _handoff_status(store: SessionStreamStore, args: argparse.Namespace) -> int:
    from .handoff import diagnose_handoff

    status = diagnose_handoff(store, args.stream)
    if args.format == "json":
        print(json.dumps(status.as_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print(f"stream:              {status.stream_id}")
    print(f"session_id:          {status.session_id or '—'}")
    print(f"session_state:       {status.session_state or '—'}")
    print(f"lease_state:         {status.lease_state or '—'}")
    print(f"lease_expired:       {status.lease_expired}")
    print(f"holder:              {status.holder_agent or '—'}/{status.holder_harness or '—'}")
    print(f"holder_instance_id:  {status.holder_instance_id or '—'}")
    print(f"holder_process_id:   {status.holder_process_id or '—'} alive={status.holder_process_alive}")
    print(f"expires_at:          {status.expires_at or '—'}")
    print(f"heartbeat_at:        {status.heartbeat_at or '—'}")
    print(f"claimable_force_close: {status.claimable_force_close}")
    print(f"reason:              {status.reason}")
    return 0


def _handoff_claim(store: SessionStreamStore, args: argparse.Namespace) -> int:
    from datetime import datetime

    from .handoff import claim_stream, default_instance_id

    stream = args.stream
    agent = args.agent
    instance_id = args.instance_id or default_instance_id(agent)
    process_id = args.process_id or os.getpid()
    lineage = args.lineage_id or (
        f"lineage-{stream.replace(':', '-')}-{agent}-{datetime.now().strftime('%Y%m%d')}"
    )
    receipt = claim_stream(
        store,
        stream_id=stream,
        agent=agent,
        harness=args.harness,
        instance_id=instance_id,
        process_id=process_id,
        lineage_id=lineage,
        ttl_seconds=args.ttl_seconds,
        task_id=args.task_id,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _tail(store: SessionStreamStore, args: argparse.Namespace) -> int:
    digest = store.load_digest(args.stream, limit=args.limit)
    if args.format == "json":
        payload = {
            "stream": digest.stream_id,
            "limit": digest.limit,
            "high_water_entry_id": digest.high_water_entry_id,
            "digest_sha256": digest.digest_sha256,
            "pinned": [entry_as_dict(entry) for entry in digest.pinned],
            "recent": [entry_as_dict(entry) for entry in digest.recent],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print("section\tentry_id\ttype\tts\tagent\tharness\tbody")
    for section, entries in (("PINNED", digest.pinned), ("RECENT", digest.recent)):
        for entry in entries:
            body = entry.body.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")
            print(
                f"{section}\t{entry.entry_id}\t{entry.type.value}\t{entry.ts}\t"
                f"{entry.agent}\t{entry.harness}\t{body}"
            )
    return 0


def _dump(store: SessionStreamStore, args: argparse.Namespace) -> int:
    payload = store.dump_stream(args.stream)
    if args.format == "json":
        rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    else:
        rendered = _dump_jsonl(payload)
    if args.output is None:
        print(rendered, end="")
    else:
        _atomic_write(args.output, rendered)
        print(str(args.output))
    return 0


def _hook(store: SessionStreamStore, args: argparse.Namespace) -> int:
    lease = lease_from_environment()
    result = heartbeat_hook(store, lease) if args.action == "heartbeat" else clean_exit_hook(store, lease)
    print(json.dumps(result.__dict__, ensure_ascii=False, sort_keys=True))
    return 0


def _mirror_atlas(store: SessionStreamStore, args: argparse.Namespace) -> int:
    lease = lease_from_environment()
    result = mirror_atlas_handoff(
        store,
        lease,
        repo_root=args.repo_root,
        stream_id=args.stream,
        source_path=args.source,
    )
    print(
        json.dumps(
            {
                "profile": result.profile,
                "source_path": result.source_path,
                "source_sha256": result.source_sha256,
                "source_bytes": result.source_bytes,
                "entry_id": result.entry.entry_id,
                "mirror_id": result.mirror_id,
            },
            sort_keys=True,
        )
    )
    return 0


def _mirror_handoff(store: SessionStreamStore, args: argparse.Namespace) -> int:
    lease = lease_from_environment()
    source = args.source
    if source is None:
        resolved = resolve_handoff_path(args.stream, args.repo_root)
        if resolved is None:
            known = ", ".join(epic_handoff_map(args.repo_root).get(args.stream, ())) or "(none registered)"
            raise ValueError(
                f"no existing handoff for {args.stream}; candidates: {known}; pass --source explicitly"
            )
        source = resolved
    profile = args.profile or args.stream.removeprefix("epic:")
    result = mirror_handoff_file(
        store,
        lease,
        profile=profile,
        repo_root=args.repo_root,
        stream_id=args.stream,
        source_path=source,
    )
    print(
        json.dumps(
            {
                "profile": result.profile,
                "source_path": result.source_path,
                "source_sha256": result.source_sha256,
                "source_bytes": result.source_bytes,
                "entry_id": result.entry.entry_id,
                "mirror_id": result.mirror_id,
            },
            sort_keys=True,
        )
    )
    return 0


def _dual_write_status(args: argparse.Namespace) -> int:
    rows = list_handoff_candidates(args.repo_root)
    print("stream\tname\texists\tpath")
    for row in rows:
        print(f"{row.stream_id}\t{row.stream_name}\t{int(row.exists)}\t{row.path}")
    inventory = load_stream_epic_inventory(args.repo_root)
    registered = sorted(r.stream_id for r in inventory)
    present = sorted({r.stream_id for r in rows if r.exists})
    ok, missing = inventory_covers_issue_streams(args.repo_root)
    print(
        json.dumps(
            {
                "registered_streams": registered,
                "epic_count": len(inventory),
                "streams_with_file": present,
                "inventory_covers_issue_streams": ok,
                "missing_epics": missing,
                "source": "scripts/config/issue_streams.yaml",
                "cutover": "blocked — dual-write only; file handoffs remain authoritative",
            },
            sort_keys=True,
        )
    )
    return 0


def _dump_jsonl(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in payload.items():
        if isinstance(value, list):
            lines.extend(
                json.dumps({"record_type": key, "data": row}, ensure_ascii=False, sort_keys=True)
                for row in value
            )
        elif value is not None:
            lines.append(
                json.dumps({"record_type": key, "data": value}, ensure_ascii=False, sort_keys=True)
            )
    return "\n".join(lines) + ("\n" if lines else "")


def _atomic_write(path: Path, content: str) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
        temporary_name = None
        directory_fd = os.open(target.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
