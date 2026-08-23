"""Local durable occupancy seats: session-stream leases and optional markers.

These sources never probe a remote host. They read the Monitor checkout's
session-stream DB (same path as ``/api/session-streams``) and an optional
marker file or directory. Opaque ``host_id`` values only; paths stay off the
JSON wire.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import parse_timestamp
from scripts.api.occupancy_sanitize import occupant as _occupant
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.api.occupancy_sanitize import safe_field as _safe_field
from scripts.api.session_streams_router import _db_path as session_streams_db_path
from scripts.api.session_streams_router import _repo_root
from scripts.lexicon.runner import atlas_job

ENV_DRIVER_HOST_ID = "MONITOR_OCCUPANCY_DRIVER_HOST_ID"
ENV_MARKERS = "MONITOR_OCCUPANCY_MARKERS"
ENV_FOUNDRY_HOST_ID = "MONITOR_OCCUPANCY_FOUNDRY_HOST_ID"
MARKERS_SCHEMA = "monitor-occupancy-markers.v1"
MARKER_KINDS = frozenset({"driver", "worker", "job", "service"})
DEFAULT_MARKER_TTL_S = 15 * 60
_MARKERS_REL = Path(".agent") / "occupancy" / "markers"


def markers_root() -> Path:
    raw = os.environ.get(ENV_MARKERS, "").strip()
    if raw:
        return Path(raw)
    return _repo_root() / _MARKERS_REL


def self_host_opaque_ids(mapping: dict[str, str]) -> set[str]:
    """Opaque ids whose canonical token is this process (no remote guess)."""
    claimed: set[str] = set()
    for canonical, opaque in mapping.items():
        if atlas_job.is_self_host(canonical) and _opaque_host_id(opaque):
            claimed.add(opaque)
    return claimed


def driver_seat_host_id(mapping: dict[str, str], selected: dict[str, str | None]) -> str | None:
    """Opaque host that may claim local session-stream driver seats."""
    explicit = os.environ.get(ENV_DRIVER_HOST_ID, "").strip().lower()
    if explicit:
        return explicit if _opaque_host_id(explicit) and explicit in selected else None
    claimed = self_host_opaque_ids(mapping) & set(selected)
    if len(claimed) == 1:
        return next(iter(claimed))
    return None


def _parse_when(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return parse_timestamp(value.strip())
    except ValueError:
        return None


def _epic_from_stream(stream_id: str) -> str | None:
    if not stream_id.startswith("epic:"):
        return None
    number = stream_id.removeprefix("epic:")
    return number if number.isdigit() else None


def occupants_from_session_streams(
    *,
    host_id: str,
    mapping: dict[str, str],
    selected: dict[str, str | None],
    db_path: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, str | None]]:
    """Active epic-driver leases attached to one opaque host."""
    if driver_seat_host_id(mapping, selected) != host_id:
        return []
    path = session_streams_db_path() if db_path is None else db_path
    if not path.is_file():
        return []
    clock = now or datetime.now(UTC)
    try:
        database = SessionStreamDatabase(path)
        with database.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT l.stream_id, l.holder_agent, l.holder_task_id, l.expires_at
                FROM stream_leases AS l
                JOIN sessions AS s ON s.stream_id = l.stream_id
                    AND s.session_id = l.session_id
                WHERE l.state = 'active'
                  AND s.state IN ('open', 'rolling')
                """
            ).fetchall()
    except (OSError, sqlite3.Error, ValueError):
        return []

    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        try:
            expires_at = parse_timestamp(str(row["expires_at"]))
        except (KeyError, ValueError):
            continue
        if expires_at <= clock:
            continue
        stream_id = str(row["stream_id"] or "")
        epic = _epic_from_stream(stream_id)
        if epic is None:
            continue
        task_id = _safe_field(row["holder_task_id"], role="task_id") or f"epic-{epic}"
        occupant = _occupant(
            kind="driver",
            agent=row["holder_agent"],
            task_id=task_id,
            epic=epic,
        )
        if occupant is None:
            continue
        key = (occupant["kind"], occupant["task_id"] or "")
        if key in seen:
            continue
        seen.add(key)
        occupants.append(occupant)
    return occupants


def _marker_fresh(payload: dict[str, Any], *, now: datetime) -> bool:
    expires = _parse_when(payload.get("expires_at"))
    if expires is not None:
        return expires > now
    updated = _parse_when(payload.get("updated_at"))
    if updated is None:
        return True
    return (now - updated).total_seconds() <= DEFAULT_MARKER_TTL_S


def _occupant_from_marker(
    payload: dict[str, Any],
    *,
    host_id: str,
    now: datetime,
) -> dict[str, str | None] | None:
    if not isinstance(payload, dict):
        return None
    marker_host = str(payload.get("host_id") or "").strip().lower()
    if marker_host != host_id or not _opaque_host_id(marker_host):
        return None
    kind = str(payload.get("kind") or "").strip()
    if kind not in MARKER_KINDS:
        return None
    if not _marker_fresh(payload, now=now):
        return None
    return _occupant(
        kind=kind,
        agent=payload.get("agent"),
        task_id=payload.get("task_id"),
        epic=payload.get("epic"),
    )


def _iter_marker_payloads(root: Path) -> Iterator[dict[str, Any]]:
    if root.is_file():
        candidates = [root]
    elif root.is_dir():
        candidates = sorted(path for path in root.iterdir() if path.is_file() and path.suffix == ".json")
    else:
        return
    for path in candidates:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeError):
            continue
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    yield item
            continue
        if not isinstance(raw, dict):
            continue
        occupants = raw.get("occupants")
        if isinstance(occupants, list):
            for item in occupants:
                if isinstance(item, dict):
                    yield item
            continue
        yield raw


def occupants_from_markers(
    *,
    host_id: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, str | None]]:
    """Optional Foundry/compiler (or other service) heartbeats for one host."""
    path = markers_root() if root is None else root
    clock = now or datetime.now(UTC)
    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    try:
        payloads = _iter_marker_payloads(path)
    except OSError:
        return []
    for payload in payloads:
        occupant = _occupant_from_marker(payload, host_id=host_id, now=clock)
        if occupant is None:
            continue
        key = (occupant["kind"], occupant["task_id"] or "")
        if key in seen:
            continue
        seen.add(key)
        occupants.append(occupant)
    return occupants


def _marker_filename(kind: str, task_id: str) -> str:
    return f"{kind}-{task_id}.json"


def write_marker(
    *,
    kind: str,
    task_id: str,
    host_id: str,
    agent: str | None = None,
    epic: str | None = None,
    path: Path | None = None,
    ttl_seconds: int = DEFAULT_MARKER_TTL_S,
    now: datetime | None = None,
) -> Path | None:
    """Write one sanitized marker. Returns None when the row cannot be published."""
    if kind not in MARKER_KINDS or not _opaque_host_id(host_id):
        return None
    occupant = _occupant(kind=kind, agent=agent, task_id=task_id, epic=epic)
    if occupant is None:
        return None
    clock = now or datetime.now(UTC)
    expires = clock + timedelta(seconds=max(1, int(ttl_seconds)))
    payload = {
        "schema": MARKERS_SCHEMA,
        "kind": occupant["kind"],
        "agent": occupant["agent"],
        "task_id": occupant["task_id"],
        "epic": occupant["epic"],
        "host_id": host_id,
        "updated_at": clock.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z"),
    }
    dest = markers_root() if path is None else path
    try:
        as_file = dest.suffix == ".json" and not dest.is_dir()
        if as_file:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return dest
        dest.mkdir(parents=True, exist_ok=True)
        target = dest / _marker_filename(str(occupant["kind"]), str(occupant["task_id"]))
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return target
    except OSError:
        return None


def clear_marker(*, kind: str, task_id: str, path: Path | None = None) -> None:
    dest = markers_root() if path is None else path
    try:
        if dest.is_file():
            dest.unlink()
            return
        if dest.is_dir():
            target = dest / _marker_filename(kind, task_id)
            if target.is_file():
                target.unlink()
    except OSError:
        return


@contextmanager
def occupancy_marker_scope(
    *,
    kind: str,
    task_id: str,
    host_id: str | None = None,
    agent: str | None = None,
    epic: str | None = None,
    path: Path | None = None,
    ttl_seconds: int = DEFAULT_MARKER_TTL_S,
) -> Iterator[Path | None]:
    """Publish a marker for the life of a Foundry/compiler run. No-op if unconfigured."""
    resolved_host = (host_id or os.environ.get(ENV_FOUNDRY_HOST_ID, "")).strip().lower()
    dest = path
    if dest is None and not os.environ.get(ENV_MARKERS, "").strip():
        yield None
        return
    if not resolved_host or not _opaque_host_id(resolved_host):
        yield None
        return
    written = write_marker(
        kind=kind,
        task_id=task_id,
        host_id=resolved_host,
        agent=agent,
        epic=epic,
        path=dest,
        ttl_seconds=ttl_seconds,
    )
    try:
        yield written
    finally:
        if written is not None:
            clear_marker(kind=kind, task_id=task_id, path=dest or written)


def foundry_marker_host_id(mapping: dict[str, str]) -> str | None:
    explicit = os.environ.get(ENV_FOUNDRY_HOST_ID, "").strip().lower()
    if explicit and _opaque_host_id(explicit):
        return explicit
    claimed = self_host_opaque_ids(mapping)
    if len(claimed) == 1:
        return next(iter(claimed))
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish or clear a sanitized occupancy marker (opaque host_id only).")
    sub = parser.add_subparsers(dest="command", required=True)
    heartbeat = sub.add_parser("heartbeat", help="write one marker")
    heartbeat.add_argument("--kind", required=True)
    heartbeat.add_argument("--task-id", required=True)
    heartbeat.add_argument("--host-id", required=True)
    heartbeat.add_argument("--agent")
    heartbeat.add_argument("--epic")
    heartbeat.add_argument("--ttl-seconds", type=int, default=DEFAULT_MARKER_TTL_S)
    clear = sub.add_parser("clear", help="remove one marker")
    clear.add_argument("--kind", required=True)
    clear.add_argument("--task-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "heartbeat":
        written = write_marker(
            kind=args.kind,
            task_id=args.task_id,
            host_id=args.host_id,
            agent=args.agent,
            epic=args.epic,
            ttl_seconds=args.ttl_seconds,
        )
        if written is None:
            print("occupancy-marker: refused", flush=True)
            return 2
        print(f"occupancy-marker: kind={args.kind} task_id={args.task_id} host_id={args.host_id}")
        return 0
    clear_marker(kind=args.kind, task_id=args.task_id)
    print(f"occupancy-marker: cleared kind={args.kind} task_id={args.task_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
