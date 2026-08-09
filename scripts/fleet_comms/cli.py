"""Fleet-comms CLI: plane status, formal-job get, formal-job accept (+ optional publish).

Usage::

    .venv/bin/python -m scripts.fleet_comms plane-status
    .venv/bin/python -m scripts.fleet_comms formal-job get <review_id>
    .venv/bin/python -m scripts.fleet_comms formal-job accept \\
        --pr 5571 --verdict APPROVED --model M --family F --harness H
    .venv/bin/python -m scripts.fleet_comms metrics
    .venv/bin/python -m scripts.fleet_comms backlog
    .venv/bin/python -m scripts.fleet_comms dead-letters
    .venv/bin/python -m scripts.fleet_comms fleet status
    .venv/bin/python -m scripts.fleet_comms fleet broker-report --days 7
    .venv/bin/python -m scripts.fleet_comms github-metrics
    .venv/bin/python -m scripts.fleet_comms authority-import --legacy-db /path/to/messages.db --source legacy-broker

``formal-job accept`` is the post-``review-pr`` glue (create/reuse job + sealed
verdict accept). Optional ``--publish`` posts GitHub comment/status via PR-G.
Does not cut over ``review-pr`` itself.

``metrics`` / ``backlog`` / ``dead-letters`` are Sol PR-M efficiency surfaces
(metadata only; never message content). In plane mode ``authority`` they read
Fleet Comms authority tables by default; ``--legacy`` forces the broker path.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_dead_letters_authority,
    collect_delivery_backlog,
    collect_delivery_backlog_authority,
    collect_efficiency_metrics,
    collect_efficiency_metrics_authority,
    collect_stream_bottleneck_metrics,
    resolve_metrics_source,
)
from scripts.fleet_comms.github_pr_metrics import collect_github_pr_metrics
from scripts.fleet_comms.legacy_broker_report import build_legacy_broker_report
from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status
from scripts.fleet_comms.review_publication import DEFAULT_GATE_KIND

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 1
EXIT_ERROR = 3


class FleetCommsCliError(RuntimeError):
    """CLI refused an operation."""


@contextmanager
def _active_acpx_transport() -> Iterator[None]:
    """Authorize ACPX active mode only for the explicit ``acp-discuss`` call."""
    variable = "LU_ACPX_TRANSPORT"
    previous = os.environ.get(variable)
    os.environ[variable] = "active"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(variable, None)
        else:
            os.environ[variable] = previous


def _json_dump(payload: Any, *, indent: int | None = 2) -> str:
    return json.dumps(payload, indent=indent, sort_keys=True, default=str) + "\n"


def cmd_plane_status(args: argparse.Namespace) -> int:
    """Dump ``read_plane_status`` JSON (same surface as Monitor API)."""
    root = Path(args.root).expanduser() if args.root else None
    repo_root = Path(args.repo_root).expanduser() if args.repo_root else None
    telemetry = Path(args.telemetry).expanduser() if args.telemetry else None
    status = read_plane_status(
        repo_root=repo_root,
        root=root,
        telemetry_path=telemetry,
        recent_limit=args.recent_limit,
    )
    sys.stdout.write(_json_dump(status))
    return EXIT_OK


def _short_plane_health(status: dict[str, Any]) -> dict[str, Any]:
    """Return a compact health projection without creating a second authority."""
    schema = status.get("schema") or {}
    enabled = status.get("enabled") is True
    read_only = status.get("read_only") is True
    db_exists = schema.get("db_exists") is True
    return {
        "healthy": enabled and read_only and db_exists,
        "enabled": enabled,
        "mode": status.get("mode"),
        "read_only": read_only,
        "db_exists": db_exists,
        "schema_version": schema.get("applied_version"),
    }


def cmd_fleet_status(args: argparse.Namespace) -> int:
    """Facade status: existing plane-status data plus a short health summary."""
    root = Path(args.root).expanduser() if args.root else None
    repo_root = Path(args.repo_root).expanduser() if args.repo_root else None
    telemetry = Path(args.telemetry).expanduser() if args.telemetry else None
    status = read_plane_status(
        repo_root=repo_root,
        root=root,
        telemetry_path=telemetry,
        recent_limit=args.recent_limit,
    )
    sys.stdout.write(_json_dump({"plane_status": status, "health": _short_plane_health(status)}))
    return EXIT_OK


def cmd_broker_report(args: argparse.Namespace) -> int:
    """Emit read-only #6106 legacy Broker Ops observation evidence."""
    routes_db = Path(args.routes_db).expanduser() if args.routes_db else None
    bridge_db = Path(args.bridge_db).expanduser() if args.bridge_db else None
    try:
        payload = build_legacy_broker_report(
            args.days,
            routes_db=routes_db,
            bridge_db=bridge_db,
        )
    except ValueError as exc:
        raise FleetCommsCliError(str(exc)) from exc
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_fleet_reap_report(args: argparse.Namespace) -> int:
    """Run the established reaper with its normal P0 guards, dry by default."""
    from scripts.orchestration import reap_worktrees

    command = ["--merged", "--apply" if args.apply else "--dry-run"]
    if args.repo_root:
        command.extend(["--repo-root", args.repo_root])
    if args.json:
        command.append("--json")
    return int(reap_worktrees.main(command))


def cmd_fleet_help(_args: argparse.Namespace) -> int:
    """Map the facade to existing Truth, Hand, and Eyes surfaces."""
    sys.stdout.write(
        _json_dump(
            {
                "truth": {
                    "status": "fleet status (plane-status plus compact health)",
                    "metrics": "fleet metrics (durable authority metrics)",
                    "broker_report": "fleet broker-report (legacy retirement evidence)",
                },
                "hand": {
                    "reap_report": "fleet reap-report --apply (existing merged-head reaper guards)",
                },
                "eyes": {
                    "board": "fleet board (cold-start driver board)",
                    "backlog": "fleet backlog (pending deliveries)",
                    "dead": "fleet dead (dead-letter inventory)",
                },
                "note": "Thin facade only; Fleet Comms remains the authoritative message plane.",
            }
        )
    )
    return EXIT_OK


def _default_message_db() -> Path:
    env = os.environ.get("AB_DB_PATH")
    if env:
        return Path(env).expanduser()
    # Prefer cwd-relative broker path (matches Monitor API MESSAGE_DB default).
    return Path(".mcp/servers/message-broker/messages.db")


def _resolve_message_db(args: argparse.Namespace) -> Path:
    if getattr(args, "db", None):
        return Path(args.db).expanduser()
    return _default_message_db()


def _resolve_plane_db(args: argparse.Namespace) -> Path:
    root = Path(args.root).expanduser() if getattr(args, "root", None) else default_plane_root()
    return root / "comms.sqlite3"


def _force_legacy(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "legacy", False))


def cmd_metrics(args: argparse.Namespace) -> int:
    """Efficiency metrics from durable timestamps (no content)."""
    source = resolve_metrics_source(force_legacy=_force_legacy(args))
    if source == "authority":
        db = _resolve_plane_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "content_included": False,
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_efficiency_metrics_authority(db)
    else:
        db = _resolve_message_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "content_included": False,
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_efficiency_metrics(db)
    payload["db_path"] = str(db)
    payload["source"] = source
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_bottleneck_metrics(args: argparse.Namespace) -> int:
    """Per-stream lifecycle bottlenecks from task, plane, and GitHub metadata."""
    tasks_dir = Path(args.tasks_dir).expanduser()
    plane_root = Path(args.root).expanduser() if args.root else default_plane_root()
    plane_db = plane_root / "comms.sqlite3"
    # Always call the collector: it is fail-open per source and refuses to
    # sqlite3.connect-create a missing plane DB (is_file guard inside). Skipping
    # here would drop valid dispatch metrics when plane is uninit (Claude CF r4).
    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir,
        plane_db=plane_db,
    )
    payload["tasks_dir"] = str(tasks_dir)
    payload["plane_db"] = str(plane_db)
    if not plane_db.is_file():
        payload["db_missing"] = True
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_backlog(args: argparse.Namespace) -> int:
    """Pending delivery backlog excluding retired endpoints by default."""
    source = resolve_metrics_source(force_legacy=_force_legacy(args))
    exclude_retired = not args.include_retired
    if source == "authority":
        db = _resolve_plane_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "total": 0,
                        "by_agent": {},
                        "by_status": {},
                        "rows": [],
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_delivery_backlog_authority(
            db,
            limit=args.limit,
            exclude_retired=exclude_retired,
        )
    else:
        db = _resolve_message_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "total": 0,
                        "by_agent": {},
                        "by_status": {},
                        "rows": [],
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_delivery_backlog(
            db,
            limit=args.limit,
            exclude_retired=exclude_retired,
        )
    payload["db_path"] = str(db)
    payload["content_included"] = False
    payload["source"] = source
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_dead_letters(args: argparse.Namespace) -> int:
    """Dead-letter inventory (metadata only)."""
    source = resolve_metrics_source(force_legacy=_force_legacy(args))
    if source == "authority":
        db = _resolve_plane_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "total": 0,
                        "by_reason": {},
                        "rows": [],
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_dead_letters_authority(db, limit=args.limit)
    else:
        db = _resolve_message_db(args)
        if not db.is_file():
            sys.stdout.write(
                _json_dump(
                    {
                        "total": 0,
                        "by_reason": {},
                        "rows": [],
                        "db_missing": True,
                        "db_path": str(db),
                        "source": source,
                    }
                )
            )
            return EXIT_OK
        payload = collect_dead_letters(db, limit=args.limit)
    payload["db_path"] = str(db)
    payload["content_included"] = False
    payload["source"] = source
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def _open_plane_db_ro(root: Path) -> sqlite3.Connection:
    db_path = root / "comms.sqlite3"
    if not db_path.is_file():
        raise FleetCommsCliError(f"plane DB not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone()
    return row is not None


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def get_formal_review_job(
    review_id: str,
    *,
    root: Path | None = None,
    repo_root: Path | None = None,
    include_attempts: bool = True,
) -> dict[str, Any]:
    """Read-only formal-job dump from the plane SQLite (no PR-F service required).

    Tables are created by fleet-comms migrations (schema v1). This helper does
    **not** call writers, migrations, or GitHub.
    """
    rid = (review_id or "").strip()
    if not rid:
        raise FleetCommsCliError("review_id is required")

    plane_root = Path(root) if root is not None else default_plane_root(repo_root=repo_root)
    conn = _open_plane_db_ro(plane_root)
    try:
        if not _table_exists(conn, "formal_review_jobs"):
            raise FleetCommsCliError(
                f"formal_review_jobs table missing under {plane_root} "
                "(run fleet-comms migrations first)"
            )
        row = conn.execute(
            "SELECT * FROM formal_review_jobs WHERE review_id = ?",
            (rid,),
        ).fetchone()
        if row is None:
            raise FleetCommsCliError(f"formal review job not found: {rid}")

        payload = _row_to_dict(row)
        payload["attempts"] = []
        if include_attempts and _table_exists(conn, "formal_review_attempts"):
            attempts = conn.execute(
                """SELECT * FROM formal_review_attempts
                   WHERE review_id = ?
                   ORDER BY attempt_number ASC""",
                (rid,),
            ).fetchall()
            payload["attempts"] = [_row_to_dict(a) for a in attempts]
        return payload
    finally:
        conn.close()


def cmd_formal_job_get(args: argparse.Namespace) -> int:
    """Dump one formal review job (+ attempts) as JSON."""
    root = Path(args.root).expanduser() if args.root else None
    repo_root = Path(args.repo_root).expanduser() if args.repo_root else None
    try:
        payload = get_formal_review_job(
            args.review_id,
            root=root,
            repo_root=repo_root,
            include_attempts=not args.no_attempts,
        )
    except FleetCommsCliError as exc:
        message = str(exc)
        sys.stderr.write(message + "\n")
        if message.startswith("formal review job not found:"):
            return EXIT_NOT_FOUND
        return EXIT_ERROR
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_formal_job_accept(args: argparse.Namespace) -> int:
    """Create/reuse formal job, accept sealed verdict, optionally publish."""
    from scripts.fleet_comms.formal_review_finalize import (
        FormalReviewFinalizeError,
        finalize_formal_review_verdict,
    )

    root = Path(args.root).expanduser() if args.root else None
    verdict_file = Path(args.verdict_file) if args.verdict_file else None
    findings = Path(args.findings_json) if args.findings_json else None
    verdict_text = None
    if verdict_file is not None:
        try:
            verdict_text = verdict_file.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"verdict_file_unreadable: {exc}\n")
            return EXIT_ERROR

    try:
        result = finalize_formal_review_verdict(
            pr_number=int(args.pr),
            model=args.model,
            family=args.family,
            harness=args.harness,
            repository=args.repository,
            gate_kind=args.gate_kind,
            verdict=args.verdict,
            verdict_text=verdict_text,
            findings_path=findings,
            review_id=args.review_id,
            head_sha=args.head_sha,
            publish=bool(args.publish),
            dry_run_publish=bool(args.dry_run_publish),
            plane_root=root,
        )
    except FormalReviewFinalizeError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR

    sys.stdout.write(_json_dump(result.to_dict()))
    return EXIT_OK


def cmd_authority_import(args: argparse.Namespace) -> int:
    """Run an explicit, idempotent historical import into a chosen plane root.

    The command has no default source database and never contacts a live bridge;
    callers must name the legacy SQLite file or a JSONL record file explicitly.
    JSON output deliberately contains metadata/counts, never imported bodies.
    """
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    root = Path(args.root).expanduser() if args.root else None
    try:
        with AuthorityService(root=root) as service:
            if args.legacy_db:
                result = service.import_legacy_sqlite(
                    Path(args.legacy_db).expanduser(),
                    source=args.source,
                )
            else:
                record_path = Path(args.records_jsonl).expanduser()
                try:
                    lines = record_path.read_text(encoding="utf-8").splitlines()
                    records = [json.loads(line) for line in lines if line.strip()]
                except (OSError, json.JSONDecodeError) as exc:
                    raise FleetCommsCliError("authority_import_records_unreadable") from exc
                if not all(isinstance(record, dict) for record in records):
                    raise FleetCommsCliError("authority_import_records_must_be_objects")
                result = service.import_records(records, source=args.source)
    except AuthorityServiceError as exc:
        # Authority errors intentionally contain only stable codes; message
        # bodies and imported metadata are never printed by this command.
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR
    except FleetCommsCliError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR
    sys.stdout.write(_json_dump(result.to_dict()))
    return EXIT_OK


def _authority_root(args: argparse.Namespace) -> Path | None:
    return Path(args.root).expanduser() if args.root else None


def _body_argument(value: str) -> str:
    return sys.stdin.read() if value == "-" else value


def _json_object(value: str | None) -> dict[str, Any]:
    if value is None:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise FleetCommsCliError("metadata_json_invalid") from exc
    if not isinstance(parsed, dict):
        raise FleetCommsCliError("metadata_json_must_be_object")
    return parsed


def cmd_channel_create(args: argparse.Namespace) -> int:
    """Create or exactly replay one authority-owned asynchronous channel."""
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    try:
        with AuthorityService(root=_authority_root(args)) as service:
            channel = service.create_channel(
                args.name,
                subscribers=args.subscriber,
                metadata=_json_object(args.metadata_json),
            )
    except AuthorityServiceError as exc:
        raise FleetCommsCliError(str(exc)) from exc
    sys.stdout.write(_json_dump(asdict(channel)))
    return EXIT_OK


def cmd_channel_subscribe(args: argparse.Namespace) -> int:
    """Add durable future fan-out recipients to an authority channel."""
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    try:
        with AuthorityService(root=_authority_root(args)) as service:
            channel = service.subscribe(
                args.name,
                args.recipient,
                metadata=_json_object(args.metadata_json),
            )
    except AuthorityServiceError as exc:
        raise FleetCommsCliError(str(exc)) from exc
    sys.stdout.write(_json_dump(asdict(channel)))
    return EXIT_OK


def cmd_channel_context(args: argparse.Namespace) -> int:
    """Seal a context revision and atomically make it current for the channel."""
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    try:
        with AuthorityService(root=_authority_root(args)) as service:
            revision = service.set_channel_context(
                args.name,
                _body_argument(args.body),
                producer=args.producer,
            )
    except AuthorityServiceError as exc:
        raise FleetCommsCliError(str(exc)) from exc
    sys.stdout.write(_json_dump(asdict(revision)))
    return EXIT_OK


def cmd_channel_publish(args: argparse.Namespace) -> int:
    """Append one immutable message and atomically create its fan-out deliveries."""
    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    try:
        with AuthorityService(root=_authority_root(args)) as service:
            message = service.publish_message(
                sender=args.sender,
                body=_body_argument(args.body),
                channel=args.name,
                recipients=args.recipient or None,
                kind=args.kind,
                conversation_id=args.conversation_id,
                in_reply_to=args.in_reply_to,
                correlation_id=args.correlation_id,
                provenance={"Source": args.source, "Agent": args.sender, "Via": "fleet-comms"},
                deadline_at=args.deadline_at,
                idempotency_key=args.idempotency_key,
            )
    except AuthorityServiceError as exc:
        raise FleetCommsCliError(str(exc)) from exc
    payload = asdict(message)
    payload["content_included"] = False
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK



def cmd_github_metrics(args: argparse.Namespace) -> int:
    """PR open→merge latency from GitHub (metadata only; Sol PR-M residual)."""
    payload = collect_github_pr_metrics(
        repo=args.repo,
        search=args.search,
        limit=args.limit,
    )
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK if payload.get("ok", True) else EXIT_ERROR


def cmd_acp_discuss(args: argparse.Namespace) -> int:
    """Run the explicitly authorized bounded ACPX discussion (stdin-only prompt)."""
    from scripts.agent_runtime.acpx_discuss import (
        AcpxDiscussionBusyError,
        AcpxDiscussionError,
        run_discussion,
    )

    prompt = sys.stdin.read()
    try:
        with _active_acpx_transport():
            payload = run_discussion(
                prompt=prompt,
                cwd=Path(args.cwd),
                task_id=args.task_id,
                correlation_id=args.correlation_id,
                idempotency_key=args.idempotency_key,
                rounds=args.rounds,
                root=Path(args.root).expanduser() if args.root else None,
            )
    except AcpxDiscussionBusyError:
        sys.stdout.write(
            _json_dump(
                {
                    "classification": "busy",
                    "state": "BUSY",
                    "queued": False,
                    "retryable": False,
                },
                indent=None,
            )
        )
        return EXIT_ERROR
    except AcpxDiscussionError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR
    sys.stdout.write(_json_dump(payload, indent=None if args.json else 2))
    return EXIT_OK if payload["state"] == "COMPLETE" else EXIT_ERROR


def cmd_acp_verify(args: argparse.Namespace) -> int:
    """Verify one body-free durable ACP conversation receipt."""
    from scripts.agent_runtime.acpx_discuss import (
        AcpxDiscussionError,
        AcpxDiscussionNotFoundError,
        verify_discussion_receipt,
    )

    root = (
        Path(args.root).expanduser()
        if args.root
        else default_plane_root(repo_root=Path.cwd())
    )
    try:
        payload = verify_discussion_receipt(
            root=root,
            conversation_id=args.conversation_id,
            require_replay=args.require_replay,
        )
    except AcpxDiscussionNotFoundError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_NOT_FOUND
    except AcpxDiscussionError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR
    sys.stdout.write(_json_dump(payload, indent=None if args.json else 2))
    return EXIT_OK if payload["verified"] else EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.fleet_comms",
        description=(
            "Fleet-comms CLI: plane-status, formal-job get (read-only), "
            "formal-job accept (writer + optional GitHub publish), "
            "authority-import, metrics/backlog/dead-letters (Sol PR-M)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    plane = sub.add_parser(
        "plane-status",
        help="Dump message-plane mode/schema/parity telemetry as JSON",
    )
    plane.add_argument(
        "--root",
        default=None,
        help="Plane storage root (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    plane.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve default plane path (default: cwd)",
    )
    plane.add_argument(
        "--telemetry",
        default=None,
        help="Parity telemetry JSONL path (default: FLEET_COMMS_PLANE_TELEMETRY or under plane root)",
    )
    plane.add_argument(
        "--recent-limit",
        type=int,
        default=50,
        help="Max recent parity events to include (default: 50)",
    )
    plane.set_defaults(func=cmd_plane_status)

    fleet = sub.add_parser(
        "fleet",
        help="Seat-facing facade over existing Fleet Comms read-only surfaces",
    )
    fleet_sub = fleet.add_subparsers(dest="fleet_command", required=True)

    fleet_status = fleet_sub.add_parser("status", help="plane-status plus compact health")
    fleet_status.add_argument("--root", default=None, help="Plane storage root")
    fleet_status.add_argument("--repo-root", default=None, help="Repo root for plane resolution")
    fleet_status.add_argument("--telemetry", default=None, help="Parity telemetry JSONL path")
    fleet_status.add_argument("--recent-limit", type=int, default=50, help="Max recent parity events")
    fleet_status.set_defaults(func=cmd_fleet_status)

    fleet_board = fleet_sub.add_parser("board", help="Delegate to cold-start-board")
    fleet_board.add_argument("--format", choices=["json", "markdown"], default="json")
    fleet_board.add_argument("--stream-id", default=None)
    fleet_board.add_argument("--agent", default=None)
    fleet_board.add_argument("--needle", default=None)
    fleet_board.add_argument("--root", default=None)
    fleet_board.add_argument("--repo-root", default=None)
    fleet_board.set_defaults(func=cmd_cold_start_board)

    fleet_metrics = fleet_sub.add_parser("metrics", help="Delegate to metrics")
    fleet_metrics.add_argument("--db", default=None, help="Legacy broker SQLite path")
    fleet_metrics.add_argument("--root", default=None, help="Plane storage root")
    fleet_metrics.add_argument("--legacy", action="store_true", help="Force legacy broker source")
    fleet_metrics.set_defaults(func=cmd_metrics)

    fleet_backlog = fleet_sub.add_parser("backlog", help="Delegate to backlog")
    fleet_backlog.add_argument("--db", default=None, help="Legacy broker SQLite path")
    fleet_backlog.add_argument("--root", default=None, help="Plane storage root")
    fleet_backlog.add_argument("--limit", type=int, default=100, help="Max rows")
    fleet_backlog.add_argument("--include-retired", action="store_true")
    fleet_backlog.add_argument("--legacy", action="store_true", help="Force legacy broker source")
    fleet_backlog.set_defaults(func=cmd_backlog)

    fleet_dead = fleet_sub.add_parser("dead", help="Delegate to dead-letters")
    fleet_dead.add_argument("--db", default=None, help="Legacy broker SQLite path")
    fleet_dead.add_argument("--root", default=None, help="Plane storage root")
    fleet_dead.add_argument("--limit", type=int, default=100, help="Max rows")
    fleet_dead.add_argument("--legacy", action="store_true", help="Force legacy broker source")
    fleet_dead.set_defaults(func=cmd_dead_letters)

    fleet_reap = fleet_sub.add_parser(
        "reap-report",
        help="Dry-run merged worktree reap report; --apply keeps established guards",
    )
    fleet_reap.add_argument("--repo-root", default=None, help="Repository root to inspect")
    fleet_reap.add_argument("--apply", action="store_true", help="Apply only existing reaper safeguards")
    fleet_reap.add_argument("--json", action="store_true", help="Emit reaper JSON")
    fleet_reap.set_defaults(func=cmd_fleet_reap_report)

    fleet_broker = fleet_sub.add_parser(
        "broker-report",
        help="Read-only #6106 legacy Broker Ops usage report",
    )
    fleet_broker.add_argument("--days", type=int, default=7, help="Observation window, 1-90 days")
    fleet_broker.add_argument("--routes-db", default=None, help="Legacy HTTP telemetry SQLite path")
    fleet_broker.add_argument("--bridge-db", default=None, help="Optional legacy bridge SQLite path")
    fleet_broker.set_defaults(func=cmd_broker_report)

    fleet_help = fleet_sub.add_parser("help", help="Map Truth, Hand, and Eyes")
    fleet_help.set_defaults(func=cmd_fleet_help)

    formal = sub.add_parser(
        "formal-job",
        help="Formal review job get (RO) and accept (writer)",
    )
    formal_sub = formal.add_subparsers(dest="formal_command", required=True)

    formal_get = formal_sub.add_parser(
        "get",
        help="Dump one formal_review_jobs row (+ attempts) by review_id",
    )
    formal_get.add_argument("review_id", help="Primary key of formal_review_jobs")
    formal_get.add_argument(
        "--root",
        default=None,
        help="Plane storage root (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    formal_get.add_argument(
        "--repo-root",
        default=None,
        help="Repo root used to resolve default plane path (default: cwd)",
    )
    formal_get.add_argument(
        "--no-attempts",
        action="store_true",
        help="Omit formal_review_attempts rows",
    )
    formal_get.set_defaults(func=cmd_formal_job_get)

    formal_accept = formal_sub.add_parser(
        "accept",
        help=(
            "Create/reuse formal job for PR head, accept sealed verdict, "
            "optionally publish (post-review-pr glue)"
        ),
    )
    formal_accept.add_argument("--pr", type=int, required=True, help="Pull request number")
    formal_accept.add_argument("--model", required=True, help="Exact reviewer model ID")
    formal_accept.add_argument("--family", required=True, help="Reviewer model family")
    formal_accept.add_argument("--harness", required=True, help="Reviewer harness")
    formal_accept.add_argument(
        "--repository",
        default="learn-ukrainian/learn-ukrainian.github.io",
        help="owner/repo (default: learn-ukrainian/learn-ukrainian.github.io)",
    )
    formal_accept.add_argument(
        "--gate-kind",
        default=DEFAULT_GATE_KIND,
        help=f"Gate kind (default: {DEFAULT_GATE_KIND})",
    )
    formal_accept.add_argument("--verdict", help="APPROVED|CHANGES_REQUESTED|BLOCKED")
    formal_accept.add_argument(
        "--verdict-file",
        help="Text file containing VERDICT: … line",
    )
    formal_accept.add_argument(
        "--findings-json",
        help="Findings JSON with top-level verdict field",
    )
    formal_accept.add_argument(
        "--review-id",
        help="Optional review_id when creating the job (default: auto)",
    )
    formal_accept.add_argument(
        "--head-sha",
        help="Override PR head SHA (default: gh pr view)",
    )
    formal_accept.add_argument(
        "--root",
        default=None,
        help="Plane ArtifactStore root (default under batch_state/fleet-comms/v1)",
    )
    formal_accept.add_argument(
        "--publish",
        action="store_true",
        help="After accept, live-publish comment + fleet/cross-family-review status",
    )
    formal_accept.add_argument(
        "--dry-run-publish",
        action="store_true",
        help="Plan publication without mutating GitHub (still accepts sealed verdict)",
    )
    formal_accept.set_defaults(func=cmd_formal_job_accept)

    authority_import = sub.add_parser(
        "authority-import",
        help="Explicit idempotent import of legacy bridge/channel metadata into Fleet Comms",
    )
    authority_import.add_argument(
        "--source",
        required=True,
        help="Stable source namespace used for idempotent import receipts",
    )
    authority_import.add_argument(
        "--root",
        default=None,
        help="Authority plane root (never defaults to a legacy database)",
    )
    authority_input = authority_import.add_mutually_exclusive_group(required=True)
    authority_input.add_argument(
        "--legacy-db",
        help="Read-only legacy bridge/channel SQLite source; not modified",
    )
    authority_input.add_argument(
        "--records-jsonl",
        help="JSONL source records for import; bodies are never echoed",
    )
    authority_import.set_defaults(func=cmd_authority_import)

    channel = sub.add_parser(
        "channel",
        help="Authority-owned asynchronous channel operations",
    )
    channel_sub = channel.add_subparsers(dest="channel_command", required=True)

    channel_create = channel_sub.add_parser("create", help="Create an authority channel")
    channel_create.add_argument("name")
    channel_create.add_argument("--subscriber", action="append", default=[])
    channel_create.add_argument("--metadata-json")
    channel_create.add_argument("--root")
    channel_create.set_defaults(func=cmd_channel_create)

    channel_subscribe = channel_sub.add_parser(
        "subscribe", help="Add durable future fan-out recipients"
    )
    channel_subscribe.add_argument("name")
    channel_subscribe.add_argument("recipient", nargs="+")
    channel_subscribe.add_argument("--metadata-json")
    channel_subscribe.add_argument("--root")
    channel_subscribe.set_defaults(func=cmd_channel_subscribe)

    channel_context = channel_sub.add_parser(
        "context", help="Seal and select the current channel context revision"
    )
    channel_context.add_argument("name")
    channel_context.add_argument("body", help="Context text or '-' for stdin")
    channel_context.add_argument("--producer", default="fleet-comms-cli")
    channel_context.add_argument("--root")
    channel_context.set_defaults(func=cmd_channel_context)

    channel_publish = channel_sub.add_parser(
        "publish", help="Append an immutable message and create fan-out deliveries"
    )
    channel_publish.add_argument("name")
    channel_publish.add_argument("body", help="Message text or '-' for stdin")
    channel_publish.add_argument("--sender", required=True)
    channel_publish.add_argument("--source", default="operator")
    channel_publish.add_argument("--recipient", action="append", default=[])
    channel_publish.add_argument("--kind", default="message")
    channel_publish.add_argument("--conversation-id")
    channel_publish.add_argument("--in-reply-to")
    channel_publish.add_argument("--correlation-id")
    channel_publish.add_argument("--deadline-at")
    channel_publish.add_argument("--idempotency-key", required=True)
    channel_publish.add_argument("--root")
    channel_publish.set_defaults(func=cmd_channel_publish)

    metrics = sub.add_parser(
        "metrics",
        help="Efficiency metrics from durable timestamps (no content; Sol PR-M)",
    )
    metrics.add_argument(
        "--db",
        default=None,
        help="Broker SQLite path (default: AB_DB_PATH or .mcp/servers/message-broker/messages.db)",
    )
    metrics.add_argument(
        "--root",
        default=None,
        help="Plane storage root for authority reads (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    metrics.add_argument(
        "--legacy",
        action="store_true",
        help="Force broker SQLite even when plane mode is authority (source=legacy_forced)",
    )
    metrics.set_defaults(func=cmd_metrics)

    bottlenecks = sub.add_parser(
        "bottleneck-metrics",
        help="Per-stream dispatch/review/merge bottlenecks (metadata only)",
    )
    bottlenecks.add_argument(
        "--tasks-dir",
        default="batch_state/tasks",
        help="Delegate task-state directory (default: batch_state/tasks)",
    )
    bottlenecks.add_argument(
        "--root",
        default=None,
        help="Plane storage root (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    bottlenecks.set_defaults(func=cmd_bottleneck_metrics)

    backlog = sub.add_parser(
        "backlog",
        help="Pending/dispatched delivery backlog without bodies (Sol PR-M)",
    )
    backlog.add_argument(
        "--db",
        default=None,
        help="Broker SQLite path (default: AB_DB_PATH or .mcp/servers/message-broker/messages.db)",
    )
    backlog.add_argument(
        "--root",
        default=None,
        help="Plane storage root for authority reads (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    backlog.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max backlog rows (default: 100)",
    )
    backlog.add_argument(
        "--include-retired",
        action="store_true",
        help="Include retired endpoints such as gemini (default: exclude)",
    )
    backlog.add_argument(
        "--legacy",
        action="store_true",
        help="Force broker SQLite even when plane mode is authority (source=legacy_forced)",
    )
    backlog.set_defaults(func=cmd_backlog)

    dead = sub.add_parser(
        "dead-letters",
        help="Dead-letter inventory metadata only (Sol PR-M)",
    )
    dead.add_argument(
        "--db",
        default=None,
        help="Broker SQLite path (default: AB_DB_PATH or .mcp/servers/message-broker/messages.db)",
    )
    dead.add_argument(
        "--root",
        default=None,
        help="Plane storage root for authority reads (default: FLEET_COMMS_ROOT or batch_state/fleet-comms/v1)",
    )
    dead.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Max dead-letter rows (default: 100)",
    )
    dead.add_argument(
        "--legacy",
        action="store_true",
        help="Force broker SQLite even when plane mode is authority (source=legacy_forced)",
    )
    dead.set_defaults(func=cmd_dead_letters)


    gh_metrics = sub.add_parser(
        "github-metrics",
        help="PR open→merge latency from GitHub (metadata only; Sol PR-M residual)",
    )
    gh_metrics.add_argument(
        "--repo",
        default="learn-ukrainian/learn-ukrainian.github.io",
        help="owner/repo",
    )
    gh_metrics.add_argument(
        "--search",
        default="fleet-comms",
        help="GitHub PR search filter (default: fleet-comms)",
    )
    gh_metrics.add_argument("--limit", type=int, default=30, help="Max merged PRs")
    gh_metrics.set_defaults(func=cmd_github_metrics)

    acp = sub.add_parser(
        "acp-discuss",
        help="Bounded active ACPX Codex↔Grok discussion; prompt is accepted only on stdin",
    )
    acp.add_argument("--cwd", required=True, help="Registered worktree for both fixed participants")
    acp.add_argument("--task-id", required=True)
    acp.add_argument("--correlation-id", required=True)
    acp.add_argument("--idempotency-key", required=True)
    acp.add_argument("--rounds", type=int, default=2, help="Discussion rounds (1-3; default 2)")
    acp.add_argument("--root", default=None, help="Fleet-comms storage root")
    acp.add_argument("--json", action="store_true", help="Emit compact JSON")
    acp.set_defaults(func=cmd_acp_discuss)

    verify = sub.add_parser(
        "acp-verify",
        help="Read-only verification of one durable, body-free ACP receipt",
    )
    verify.add_argument("--conversation-id", required=True)
    verify.add_argument("--root", default=None, help="Fleet-comms storage root")
    verify.add_argument(
        "--require-replay",
        action="store_true",
        help="Require an observed idempotent replay receipt",
    )
    verify.add_argument("--json", action="store_true", help="Emit compact JSON")
    verify.set_defaults(func=cmd_acp_verify)

    board = sub.add_parser(
        "cold-start-board",
        help="Emit fail-open driver cold start board (Sol PR-2)",
    )
    board.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    board.add_argument(
        "--stream-id",
        default=None,
        help="Optional session stream ID (default: SESSION_STREAM_ID env var)",
    )
    board.add_argument(
        "--agent",
        default=None,
        help="Optional agent/harness identifier (default: SESSION_HANDOFF_AGENT or AGENT env var)",
    )
    board.add_argument(
        "--needle",
        default=None,
        help="Optional single-token search needle across status",
    )
    board.add_argument(
        "--root",
        default=None,
        help="Plane storage root",
    )
    board.add_argument(
        "--repo-root",
        default=None,
        help="Repo root",
    )
    board.set_defaults(func=cmd_cold_start_board)

    return parser


def cmd_cold_start_board(args: argparse.Namespace) -> int:
    """Emit fail-open driver cold start board as JSON or Markdown (PR-2)."""
    from scripts.fleet_comms.cold_start_board import (
        build_cold_start_board,
        render_markdown_board,
    )

    root = Path(args.root).expanduser() if args.root else None
    repo_root = Path(args.repo_root).expanduser() if args.repo_root else None

    board_data = build_cold_start_board(
        stream_id=args.stream_id,
        agent=args.agent,
        needle=args.needle,
        root=root,
        repo_root=repo_root,
    )

    output = (
        render_markdown_board(board_data)
        if args.format == "markdown"
        else _json_dump(board_data)
    )

    sys.stdout.write(output)
    return EXIT_OK



def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    try:
        return int(func(args))
    except FleetCommsCliError as exc:
        sys.stderr.write(str(exc) + "\n")
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
