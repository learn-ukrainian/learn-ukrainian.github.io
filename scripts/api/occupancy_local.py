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
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from agents_extensions.shared.session_streams.db import SessionStreamDatabase
from agents_extensions.shared.session_streams.model import parse_timestamp
from scripts.api import config
from scripts.api.occupancy_sanitize import occupant as _occupant
from scripts.api.occupancy_sanitize import opaque_host_id as _opaque_host_id
from scripts.api.occupancy_sanitize import safe_field as _safe_field
from scripts.api.repository_authority import preparation_data_root
from scripts.lexicon.runner import atlas_job

ENV_DRIVER_HOST_ID = "MONITOR_OCCUPANCY_DRIVER_HOST_ID"
ENV_MARKERS = "MONITOR_OCCUPANCY_MARKERS"
ENV_FOUNDRY_HOST_ID = "MONITOR_OCCUPANCY_FOUNDRY_HOST_ID"
MAC_OPERATOR_HOST_ID = "mac-operator"
# Keep in sync with scripts.api.occupancy.PRODUCTION_LINUX_HOST_ID (cycle-safe).
PRODUCTION_LINUX_HOST_ID = "host-teacher"
MARKERS_SCHEMA = "monitor-occupancy-markers.v1"
MARKER_KINDS = frozenset({"driver", "worker", "job", "service"})
DEFAULT_MARKER_TTL_S = 15 * 60
_MARKERS_REL = Path(".agent") / "occupancy" / "markers"


def _repo_root() -> Path:
    return preparation_data_root(
        project_root=Path(config.PROJECT_ROOT),
        live_repo_root=Path(config.LIVE_REPO_ROOT),
    )


def session_streams_db_path() -> Path:
    return _repo_root() / ".agent" / "session-streams" / "v1" / "session-streams.sqlite3"


@dataclass(frozen=True)
class OccupancyRead:
    """Sanitized occupants plus the read health needed by burn-state derivation."""

    occupants: list[dict[str, str | None]]
    readable: bool
    observation_age_s: float


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


def empty_map_api_host_opaque() -> str | None:
    """Opaque glance id this API process fills when ``MONITOR_OCCUPANCY_HOST_IDS`` is empty.

    One production Linux host + Mac observer: on Linux the API process is the
    production glance row; on Darwin it is the Mac observer seat.
    """
    if sys.platform == "darwin":
        return MAC_OPERATOR_HOST_ID
    return PRODUCTION_LINUX_HOST_ID


def driver_seat_host_id(mapping: dict[str, str], selected: dict[str, str | None]) -> str | None:
    """Opaque host that may claim local session-stream driver seats.

    Empty-map fallback is Linux-only (``host-teacher``). Darwin remains
    observer-only — never attach session-stream drivers to ``mac-operator``.
    """
    explicit = os.environ.get(ENV_DRIVER_HOST_ID, "").strip().lower()
    if explicit:
        return explicit if _opaque_host_id(explicit) and explicit in selected else None
    claimed = self_host_opaque_ids(mapping) & set(selected)
    if len(claimed) == 1:
        return next(iter(claimed))
    # Empty map: Linux API owns production glance drivers. Darwin: no seat.
    if not mapping and sys.platform != "darwin":
        fallback = empty_map_api_host_opaque()
        if fallback is not None and fallback in selected:
            return fallback
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


def _observation_age(observed_at: list[datetime], *, now: datetime) -> float:
    if not observed_at:
        return 0.0
    return round(max(0.0, min((now - value).total_seconds() for value in observed_at)), 2)


def read_session_streams(
    *,
    host_id: str,
    mapping: dict[str, str],
    selected: dict[str, str | None],
    db_path: Path | None = None,
    now: datetime | None = None,
) -> OccupancyRead:
    """Active epic-driver leases attached to one opaque host."""
    if driver_seat_host_id(mapping, selected) != host_id:
        return OccupancyRead([], True, 0.0)
    path = session_streams_db_path() if db_path is None else db_path
    try:
        if not path.is_file():
            return OccupancyRead([], False, 0.0)
    except OSError:
        return OccupancyRead([], False, 0.0)
    clock = now or datetime.now(UTC)
    try:
        database = SessionStreamDatabase(path)
        with database.connect(read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT l.stream_id, l.holder_agent, l.holder_task_id,
                       l.heartbeat_at, l.expires_at
                FROM stream_leases AS l
                JOIN sessions AS s ON s.stream_id = l.stream_id
                    AND s.session_id = l.session_id
                WHERE l.state = 'active'
                  AND s.state IN ('open', 'rolling')
                """
            ).fetchall()
    except Exception:
        return OccupancyRead([], False, 0.0)

    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str, str]] = set()
    observed_at: list[datetime] = []
    for row in rows:
        try:
            heartbeat_at = parse_timestamp(str(row["heartbeat_at"]))
            expires_at = parse_timestamp(str(row["expires_at"]))
        except (KeyError, TypeError, ValueError):
            return OccupancyRead(occupants, False, _observation_age(observed_at, now=clock))
        observed_at.append(heartbeat_at)
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
        key = (occupant["kind"], occupant["task_id"] or "", occupant.get("epic") or "")
        if key in seen:
            continue
        seen.add(key)
        occupants.append(occupant)
    return OccupancyRead(occupants, True, _observation_age(observed_at, now=clock))


def occupants_from_session_streams(
    *,
    host_id: str,
    mapping: dict[str, str],
    selected: dict[str, str | None],
    db_path: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, str | None]]:
    """Compatibility list-only view of the read-only lease projection."""
    return read_session_streams(
        host_id=host_id,
        mapping=mapping,
        selected=selected,
        db_path=db_path,
        now=now,
    ).occupants


def _marker_fresh(payload: dict[str, Any], *, now: datetime) -> bool:
    expires = _parse_when(payload.get("expires_at"))
    if expires is not None:
        return expires > now
    updated = _parse_when(payload.get("updated_at"))
    if updated is None:
        return False
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
    if kind not in MARKER_KINDS and kind not in {
        "foundry",
        "evidence-compiler",
        "other",
    }:
        return None
    if not _marker_fresh(payload, now=now):
        return None
    mapped = {
        "worker": "service",
        "foundry": "service",
        "evidence-compiler": "service",
        "other": "service",
    }.get(kind, kind)
    if mapped not in MARKER_KINDS:
        return None
    return _occupant(
        kind=mapped,
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
        except (OSError, json.JSONDecodeError, UnicodeError) as exc:
            raise OSError from exc
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


def read_markers(
    *,
    host_id: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> OccupancyRead:
    """Optional Foundry/compiler (or other service) heartbeats for one host."""
    path = markers_root() if root is None else root
    clock = now or datetime.now(UTC)
    occupants: list[dict[str, str | None]] = []
    seen: set[tuple[str, str]] = set()
    observed_at: list[datetime] = []
    optional_default = root is None and not os.environ.get(ENV_MARKERS, "").strip()
    try:
        if not path.exists():
            return OccupancyRead([], optional_default, 0.0)
        if not path.is_file() and not path.is_dir():
            return OccupancyRead([], False, 0.0)
        for payload in _iter_marker_payloads(path):
            for timestamp_key in ("updated_at", "expires_at"):
                if timestamp_key in payload and payload[timestamp_key] is not None:
                    parsed = _parse_when(payload[timestamp_key])
                    if parsed is None:
                        return OccupancyRead(occupants, False, _observation_age(observed_at, now=clock))
                    if timestamp_key == "updated_at":
                        observed_at.append(parsed)
            occupant = _occupant_from_marker(payload, host_id=host_id, now=clock)
            if occupant is None:
                continue
            key = (occupant["kind"], occupant["task_id"] or "")
            if key in seen:
                continue
            seen.add(key)
            occupants.append(occupant)
    except OSError:
        return OccupancyRead(occupants, False, _observation_age(observed_at, now=clock))
    return OccupancyRead(occupants, True, _observation_age(observed_at, now=clock))


def occupants_from_markers(
    *,
    host_id: str,
    root: Path | None = None,
    now: datetime | None = None,
) -> list[dict[str, str | None]]:
    """Compatibility list-only view of the marker store."""
    return read_markers(host_id=host_id, root=root, now=now).occupants


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


def resolve_launcher_host_id() -> str:
    """Resolve the launcher host id from the canonical occupancy configuration."""
    explicit = os.environ.get("LU_MONITOR_HOST_ID")
    if explicit is not None:
        return explicit or "local"

    driver_host_id = os.environ.get(ENV_DRIVER_HOST_ID, "").strip().lower()
    if driver_host_id and _opaque_host_id(driver_host_id):
        return driver_host_id

    try:
        from scripts.api.occupancy import parse_host_id_map  # noqa: PLC0415 — # lazy-ok: occupancy cycle breaker

        mapping = parse_host_id_map()
        claimed = self_host_opaque_ids(mapping)
    except Exception:
        return empty_map_api_host_opaque() or "local"
    if len(claimed) == 1:
        return next(iter(claimed))
    if not mapping:
        return empty_map_api_host_opaque() or "local"
    return "local"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Publish or clear a sanitized occupancy marker (opaque host_id only).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("resolve-host-id", help="resolve the current process's opaque occupancy host id")
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
    if args.command == "resolve-host-id":
        print(resolve_launcher_host_id())
        return 0
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
