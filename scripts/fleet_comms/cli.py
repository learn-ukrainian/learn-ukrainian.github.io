"""Fleet-comms CLI: plane status, formal-job get, formal-job accept (+ optional publish).

Usage::

    .venv/bin/python -m scripts.fleet_comms plane-status
    .venv/bin/python -m scripts.fleet_comms formal-job get <review_id>
    .venv/bin/python -m scripts.fleet_comms formal-job accept \\
        --pr 5571 --verdict APPROVED --model M --family F --harness H
    .venv/bin/python -m scripts.fleet_comms metrics
    .venv/bin/python -m scripts.fleet_comms backlog
    .venv/bin/python -m scripts.fleet_comms dead-letters
    .venv/bin/python -m scripts.fleet_comms github-metrics

``formal-job accept`` is the post-``review-pr`` glue (create/reuse job + sealed
verdict accept). Optional ``--publish`` posts GitHub comment/status via PR-G.
Does not cut over ``review-pr`` itself.

``metrics`` / ``backlog`` / ``dead-letters`` are Sol PR-M efficiency surfaces
(metadata only; never message content).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from scripts.fleet_comms.efficiency_metrics import (
    collect_dead_letters,
    collect_delivery_backlog,
    collect_efficiency_metrics,
    collect_stream_bottleneck_metrics,
)
from scripts.fleet_comms.github_pr_metrics import collect_github_pr_metrics
from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status
from scripts.fleet_comms.review_publication import DEFAULT_GATE_KIND

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 1
EXIT_ERROR = 3


class FleetCommsCliError(RuntimeError):
    """CLI refused an operation."""


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


def cmd_metrics(args: argparse.Namespace) -> int:
    """Efficiency metrics from durable timestamps (no content)."""
    db = _resolve_message_db(args)
    if not db.is_file():
        sys.stdout.write(_json_dump({"content_included": False, "db_missing": True, "db_path": str(db)}))
        return EXIT_OK
    payload = collect_efficiency_metrics(db)
    payload["db_path"] = str(db)
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_bottleneck_metrics(args: argparse.Namespace) -> int:
    """Per-stream lifecycle bottlenecks from task, plane, and GitHub metadata."""
    tasks_dir = Path(args.tasks_dir).expanduser()
    plane_root = Path(args.root).expanduser() if args.root else default_plane_root()
    payload = collect_stream_bottleneck_metrics(
        tasks_dir=tasks_dir,
        plane_db=plane_root / "comms.sqlite3",
    )
    payload["tasks_dir"] = str(tasks_dir)
    payload["plane_db"] = str(plane_root / "comms.sqlite3")
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_backlog(args: argparse.Namespace) -> int:
    """Pending delivery backlog excluding retired endpoints by default."""
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
                }
            )
        )
        return EXIT_OK
    payload = collect_delivery_backlog(
        db,
        limit=args.limit,
        exclude_retired=not args.include_retired,
    )
    payload["db_path"] = str(db)
    payload["content_included"] = False
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK


def cmd_dead_letters(args: argparse.Namespace) -> int:
    """Dead-letter inventory (metadata only)."""
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
                }
            )
        )
        return EXIT_OK
    payload = collect_dead_letters(db, limit=args.limit)
    payload["db_path"] = str(db)
    payload["content_included"] = False
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



def cmd_github_metrics(args: argparse.Namespace) -> int:
    """PR open→merge latency from GitHub (metadata only; Sol PR-M residual)."""
    payload = collect_github_pr_metrics(
        repo=args.repo,
        search=args.search,
        limit=args.limit,
    )
    sys.stdout.write(_json_dump(payload))
    return EXIT_OK if payload.get("ok", True) else EXIT_ERROR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.fleet_comms",
        description=(
            "Fleet-comms CLI: plane-status, formal-job get (read-only), "
            "formal-job accept (writer + optional GitHub publish), "
            "metrics/backlog/dead-letters (Sol PR-M)."
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

    metrics = sub.add_parser(
        "metrics",
        help="Efficiency metrics from durable timestamps (no content; Sol PR-M)",
    )
    metrics.add_argument(
        "--db",
        default=None,
        help="Broker SQLite path (default: AB_DB_PATH or .mcp/servers/message-broker/messages.db)",
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
        "--limit",
        type=int,
        default=100,
        help="Max dead-letter rows (default: 100)",
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

    return parser


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
