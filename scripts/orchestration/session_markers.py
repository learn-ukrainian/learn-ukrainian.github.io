"""Short-lived local markers for notebook harness sessions.

Markers are local discovery state for the Mac observer heartbeat.  They never
leave the notebook: the heartbeat publishes only sanitized session identity
and context counters, never this module's paths or process ids.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from scripts.api.occupancy_sanitize import safe_field

MARKER_SCHEMA = "monitor-notebook-session.v1"
MARKER_MAX_AGE_SECONDS = 24 * 60 * 60
MARKER_ROOT_ENV = "LU_MONITOR_SESSION_MARKERS"
DEFAULT_MARKER_ROOT = Path.home() / ".codex" / "mac-observer" / "sessions"
ALLOWED_SESSION_AGENTS = frozenset({"claude", "codex", "cursor"})


@dataclass(frozen=True)
class SessionMarker:
    agent: str
    harness: str
    instance_id: str
    epic: str | None
    task_id: str | None
    pid: int
    started_at: str


def marker_root(root: Path | str | None = None) -> Path:
    if root is not None:
        return Path(root)
    configured = os.environ.get(MARKER_ROOT_ENV, "").strip()
    return Path(configured) if configured else DEFAULT_MARKER_ROOT


def _marker_path(instance_id: str, root: Path | str | None = None) -> Path | None:
    safe_instance = safe_field(instance_id, role="task_id")
    if safe_instance is None:
        return None
    return marker_root(root) / f"{safe_instance}.json"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_started_at(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(UTC)


def _normalise_marker(data: object) -> SessionMarker | None:
    if not isinstance(data, dict) or data.get("schema") != MARKER_SCHEMA:
        return None
    agent = safe_field(data.get("agent"), role="agent")
    harness = safe_field(data.get("harness"), role="agent")
    instance_id = safe_field(data.get("instance_id"), role="task_id")
    epic = safe_field(data.get("epic"), role="epic")
    task_id = safe_field(data.get("task_id"), role="task_id")
    started_at = data.get("started_at")
    pid = data.get("pid")
    if agent not in ALLOWED_SESSION_AGENTS or harness is None or instance_id is None:
        return None
    if epic is not None and data.get("epic") is not None and safe_field(data.get("epic"), role="epic") is None:
        return None
    if task_id is not None and data.get("task_id") is not None and safe_field(data.get("task_id"), role="task_id") is None:
        return None
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return None
    if _parse_started_at(started_at) is None:
        return None
    if not isinstance(started_at, str):
        return None
    return SessionMarker(
        agent=agent,
        harness=harness,
        instance_id=instance_id,
        epic=epic,
        task_id=task_id,
        pid=pid,
        started_at=started_at,
    )


def write_session_marker(
    *,
    agent: str,
    harness: str,
    instance_id: str,
    epic: str | None = None,
    task_id: str | None = None,
    pid: int | None = None,
    started_at: str | None = None,
    root: Path | str | None = None,
) -> Path | None:
    """Atomically write one validated marker and return its local path."""
    marker_pid = os.getppid() if pid is None else pid
    data = {
        "schema": MARKER_SCHEMA,
        "agent": agent,
        "harness": harness,
        "instance_id": instance_id,
        "epic": epic,
        "task_id": task_id,
        "pid": marker_pid,
        "started_at": started_at or _utc_now().isoformat().replace("+00:00", "Z"),
    }
    marker = _normalise_marker(data)
    path = _marker_path(instance_id, root)
    if marker is None or path is None:
        return None
    destination_root = path.parent
    destination_root.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps({"schema": MARKER_SCHEMA, **marker.__dict__}, separators=(",", ":")).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(prefix=".session-", suffix=".tmp", dir=destination_root)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    return path


def remove_session_marker(
    instance_id: str,
    *,
    root: Path | str | None = None,
    expected_pid: int | None = None,
) -> bool:
    """Remove only the marker named by the validated session id."""
    path = _marker_path(instance_id, root)
    if path is None or not path.is_file() or path.is_symlink():
        if path is not None and path.is_symlink():
            path.unlink(missing_ok=True)
        return False
    if expected_pid is not None:
        try:
            with path.open(encoding="utf-8") as handle:
                marker = _normalise_marker(json.load(handle))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False
        if marker is None or marker.pid != expected_pid:
            return False
    path.unlink(missing_ok=True)
    return True


def _pid_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except (ProcessLookupError, OSError):
        return False
    return True


def iter_session_markers(
    *,
    root: Path | str | None = None,
    now: datetime | None = None,
    pid_alive: Callable[[int], bool] | None = None,
) -> Iterator[SessionMarker]:
    """Yield fresh live markers, deleting malformed or ghost markers."""
    directory = marker_root(root)
    if not directory.is_dir():
        return
    current = (now or _utc_now()).astimezone(UTC)
    is_alive = _pid_is_alive if pid_alive is None else pid_alive
    for path in sorted(directory.glob("*.json")):
        marker: SessionMarker | None = None
        try:
            if path.is_symlink():
                path.unlink(missing_ok=True)
                continue
            with path.open(encoding="utf-8") as handle:
                marker = _normalise_marker(json.load(handle))
            started = _parse_started_at(marker.started_at) if marker else None
            too_old = started is None or current - started > timedelta(seconds=MARKER_MAX_AGE_SECONDS)
            if marker is None or too_old or not is_alive(marker.pid):
                path.unlink(missing_ok=True)
                continue
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            path.unlink(missing_ok=True)
            continue
        yield marker


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage local notebook session markers")
    parser.add_argument("--root")
    sub = parser.add_subparsers(dest="command", required=True)
    write = sub.add_parser("write")
    write.add_argument("--agent", required=True)
    write.add_argument("--harness", required=True)
    write.add_argument("--instance-id", required=True)
    write.add_argument("--epic")
    write.add_argument("--task-id")
    write.add_argument("--pid", type=int, required=True)
    write.add_argument("--started-at")
    remove = sub.add_parser("remove")
    remove.add_argument("--instance-id", required=True)
    remove.add_argument("--pid", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "write":
        written = write_session_marker(
            agent=args.agent,
            harness=args.harness,
            instance_id=args.instance_id,
            epic=args.epic,
            task_id=args.task_id,
            pid=args.pid,
            started_at=args.started_at,
            root=args.root,
        )
        return 0 if written is not None else 2
    remove_session_marker(args.instance_id, root=args.root, expected_pid=args.pid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
