"""Thin read-only CLI for fleet-comms plane status and formal review jobs.

Usage::

    .venv/bin/python -m scripts.fleet_comms plane-status
    .venv/bin/python -m scripts.fleet_comms formal-job get <review_id>

No writers, no GitHub, no review-pr cutover. Dumps JSON to stdout.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from scripts.fleet_comms.message_plane import default_plane_root, read_plane_status

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_FOUND = 1
EXIT_ERROR = 3


class FleetCommsCliError(RuntimeError):
    """CLI refused a read-only operation."""


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.fleet_comms",
        description=(
            "Thin read-only fleet-comms CLI: plane-status dump and formal-job get. "
            "No GitHub mutation, no review-pr cutover."
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
        help="Read-only formal review job queries (plane SQLite)",
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
