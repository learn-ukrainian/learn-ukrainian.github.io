"""Inbox notifications and bounded supervisory wakes for live fleet drivers.

The default mode only reports unconsumed messages. The live driver
remains responsible for reading the full inbox and recording consumption with
``ai_agent_bridge ack --consumed-by-live-driver``. Explicit supervisory modes
use Fleet Comms authority and the existing launcher/session supervisor.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from agent_runtime.agent_identity import seat_read_aliases
from secret_redactor import redact_text

from ._channels import resolve_recipient_alias
from ._config import DB_PATH, PRIMARY_REPO_ROOT

if TYPE_CHECKING:
    from agents_extensions.shared.session_streams.model import Lease
    from scripts.fleet_comms.authority import AuthorityDelivery, AuthorityService
    from scripts.session_supervisor import SessionSupervisor
    from scripts.session_supervisor.remote import RemoteEpicClient

DEFAULT_POLL_INTERVAL_SECONDS = 15.0
MAX_PREVIEW_CHARS = 240
DEFAULT_LOCK_DIR = PRIMARY_REPO_ROOT / ".agent"
SUPERVISORY_RESTART_EXIT = 75
SUPERVISORY_DELIVERY_SECONDS = 60


@dataclass(frozen=True)
class SupervisoryRequest:
    """A bounded event, never a command or a provider/model routing override."""

    delivery_id: str
    stream_id: str
    action: str
    generation: int

    @property
    def prepared_body(self) -> str:
        return (f"Supervisory restart {self.delivery_id} prepared for generation {self.generation}. "
                "Resume from the durable stream digest and reconcile outstanding work before dispatch.")

    @property
    def successor_session_id(self) -> str:
        # All requests for the same predecessor converge on one session identity.
        # Reusing a closed identity is refused by the existing session store.
        digest = hashlib.sha256(f"{self.stream_id}:{self.generation}".encode()).hexdigest()
        return f"supervisory-{digest[:32]}"


def supervisory_recipient(stream_id: str) -> str:
    """Keep automated events out of the ordinary human/worker inbox queue."""
    if not re.fullmatch(r"epic:[1-9][0-9]*", stream_id):
        raise ValueError("supervisory wake requires a numeric epic stream")
    return f"supervisor:{stream_id}"


def require_supervisory_api(service: AuthorityService) -> None:
    """Never replace generation-bound consumption with a generic acknowledgment."""
    for name in (
        "record_supervisory_consumption", "act_on_supervisory_delivery",
        "refuse_supervisory_delivery", "supervisory_delivery_status",
    ):
        if not callable(getattr(service, name, None)):
            raise RuntimeError("generation-bound supervisory consumption API is unavailable")


def read_supervisory_request(service: AuthorityService, delivery_id: str, stream_id: str) -> SupervisoryRequest:
    """Validate the durable event's complete shape before any process side effect."""
    delivery = service.get_delivery(delivery_id)
    message = service.get_message(delivery.message_id)
    if delivery.recipient != supervisory_recipient(stream_id) or message.kind != "supervisory-request":
        raise ValueError("delivery is not a supervisory event for this stream")
    body = service.read_message_body(message.message_id)
    if len(body.encode("utf-8")) > 1024:
        raise ValueError("supervisory event exceeds the bounded envelope")
    payload = json.loads(body)
    if (
        not isinstance(payload, dict)
        or set(payload) != {"schema", "action", "stream_id", "generation"}
        or payload["schema"] != "supervisory-wake.v1"
        or not isinstance(payload["action"], str)
        or payload["action"] not in {"wake", "restart"}
        or payload["stream_id"] != stream_id
        or type(payload["generation"]) is not int
        or payload["generation"] < 0
    ):
        raise ValueError("invalid supervisory event envelope")
    return SupervisoryRequest(delivery_id, stream_id, payload["action"], payload["generation"])


def pending_supervisory_delivery(service: AuthorityService, stream_id: str) -> AuthorityDelivery | None:
    """Read one durable queue head; cursor advancement never loses a wake."""
    row = service.store.connection.execute(
        """SELECT delivery_id FROM authority_deliveries
           WHERE recipient = ? AND state IN ('queued', 'running')
           ORDER BY created_at ASC, delivery_id ASC LIMIT 1""",
        (supervisory_recipient(stream_id),),
    ).fetchone()
    return service.get_delivery(str(row["delivery_id"])) if row else None


def supervisory_launch_plan(
    service: AuthorityService, remote: RemoteEpicClient, delivery_id: str, stream_id: str,
) -> SupervisoryRequest | None:
    """Return a fenced successor identity only when the event can still act.

    This is a read-only preflight, not a lease claim. The existing launcher must
    still claim through Monitor and verify the resulting generation before
    starting a provider. A deterministic session identity fences delayed retries
    even after the original successor has already exited.
    """
    require_supervisory_api(service)
    request = read_supervisory_request(service, delivery_id, stream_id)
    delivery = service.get_delivery(delivery_id)
    if delivery.state not in {"queued", "running"}:
        return None
    projection = remote.stream(stream_id)
    current = projection.get("lease")
    if current is not None:
        if current.get("state") == "active":
            return None
        if current.get("state") not in {"released", "expired"}:
            raise RuntimeError("unknown remote lease state; wake refused")
        generation = current["generation"]
    else:
        generation = 0
    if generation != request.generation:
        return None
    if request.action == "restart" and current is not None and current["state"] == "released":
        # A clean-exit restart requires both fenced consumption and the exact
        # prepared handoff. An expired predecessor uses Monitor's TTL/CAS path.
        digest = remote.digest_from_response(projection)
        if service.supervisory_delivery_status(delivery_id) != "live_driver_consumed" or not any(
            entry.body == request.prepared_body for entry in (*digest.pinned, *digest.recent)
        ):
            return None
    return request


def consume_supervisory_event(
    service: AuthorityService, supervisor: SessionSupervisor, lease: Lease, *, now: str | None = None,
) -> SupervisoryRequest | None:
    """Consume under the live envelope; prepare restart or reconcile its successor.

    This runs as a child of the existing launcher, only while its provider child
    is alive. It never closes a lease or creates a process. The launcher alone
    stops/reaps its provider and releases the exact envelope before a successor.
    """
    require_supervisory_api(service)
    if supervisor.remote is None:
        raise ValueError("supervisory consumption requires remote Monitor authority")
    supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=lease)
    worker_id = f"supervisor:{lease.session_id}"
    delivery = pending_supervisory_delivery(service, lease.stream_id)
    if delivery is None:
        return None
    now_value = now or datetime.now(UTC).isoformat()
    if delivery.state == "running":
        expires = datetime.fromisoformat(delivery.lease_expires_at.replace("Z", "+00:00"))
        if expires > datetime.fromisoformat(now_value.replace("Z", "+00:00")):
            if delivery.lease_owner != worker_id:
                return None
        else:
            delivery = None
    if delivery is None or delivery.state == "queued":
        claimed = service.claim_next_delivery(
            supervisory_recipient(lease.stream_id), worker_id,
            lease_seconds=SUPERVISORY_DELIVERY_SECONDS, max_attempts=3, now=now,
        )
        if claimed is None:
            return None
        delivery = claimed.delivery
    args = {"worker_id": worker_id, "fence_token": delivery.fence_token, "now": now}
    generation_identity = hashlib.sha256(json.dumps(
        supervisor.remote._lease_payload(lease), sort_keys=True,
    ).encode()).hexdigest()
    service.record_supervisory_consumption(
        delivery.delivery_id, driver_generation=generation_identity, **args,
    )
    # Consumption is intent. Reconcile authority again before preparing any exit.
    supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=lease)
    try:
        request = read_supervisory_request(service, delivery.delivery_id, lease.stream_id)
    except (ValueError, TypeError):
        service.refuse_supervisory_delivery(delivery.delivery_id, result=b"invalid-event", **args)
        return None
    if request.generation > lease.generation:
        service.refuse_supervisory_delivery(delivery.delivery_id, result=b"future-generation", **args)
    elif request.generation < lease.generation:
        if lease.session_id == request.successor_session_id and lease.generation == request.generation + 1:
            service.act_on_supervisory_delivery(delivery.delivery_id, acknowledgment=b"successor-live", **args)
        else:
            service.refuse_supervisory_delivery(delivery.delivery_id, result=b"superseded-generation", **args)
    elif request.action == "wake":
        service.act_on_supervisory_delivery(delivery.delivery_id, acknowledgment=b"already-live", **args)
    else:
        supervisor.handoff_driver(
            role="driver", lease=lease, entry_type="state",
            body=request.prepared_body,
            idempotency_key="supervisory-restart-" + hashlib.sha256(
                f"{delivery.delivery_id}:{lease.generation}".encode(),
            ).hexdigest()[:32],
        )
        supervisor.build_capsule(role="driver", stream_id=lease.stream_id, lease=lease)
        return request
    return None


def wake_driver_once(
    service: AuthorityService, remote: RemoteEpicClient, *, stream_id: str, launcher: Path, epic: str, run=None,
) -> bool:
    """Bridge one durable event to the existing launcher, without claiming a lease."""
    require_supervisory_api(service)
    # Old-generation events remain unacknowledged until a live driver reconciles
    # them. They must not hide a newer actionable wake while the driver is offline.
    rows = service.store.connection.execute(
        """SELECT delivery_id FROM authority_deliveries
           WHERE recipient = ? AND state IN ('queued', 'running')
           ORDER BY created_at DESC, delivery_id DESC LIMIT 64""",
        (supervisory_recipient(stream_id),),
    ).fetchall()
    plan = None
    for row in rows:
        plan = supervisory_launch_plan(service, remote, str(row["delivery_id"]), stream_id)
        if plan is not None:
            break
    if plan is None:
        return False
    environment = {key: value for key, value in os.environ.items() if not key.startswith("SESSION_STREAM_")}
    environment["SESSION_SUPERVISOR_WAKE_DELIVERY"] = plan.delivery_id
    environment["SESSION_SUPERVISOR_WAKE_STREAM"] = plan.stream_id
    environment["SESSION_SUPERVISOR_UNATTENDED"] = "1"
    # Provider/model/approval settings come only from the existing launcher and
    # operator environment. The message cannot supply argv, paths, or shell code.
    result = (run or subprocess.run)(
        [str(launcher), "--epic", epic], env=environment, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("supervisory launcher failed; event retained for reconciliation")
    return True


def run_live_supervisory_watcher(*, interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS) -> int:
    """Watch in the launcher-owned generation; return 75 only after preparation."""
    from agents_extensions.shared.session_streams.hooks import lease_from_environment
    from scripts.fleet_comms.authority import AuthorityService
    from scripts.session_supervisor import SessionSupervisor
    from scripts.session_supervisor.remote import RemoteEpicClient

    lease = lease_from_environment()
    supervisor = SessionSupervisor(None, repo_root=Path.cwd(), remote=RemoteEpicClient())
    with AuthorityService() as service:
        require_supervisory_api(service)
        while True:
            request = consume_supervisory_event(service, supervisor, lease)
            if request is not None:
                print(request.delivery_id, flush=True)
                return SUPERVISORY_RESTART_EXIT
            time.sleep(interval_seconds)


def run_supervisory_wake_watcher(agent: str, provider: str, epic: str, *, interval_seconds: float, once: bool) -> None:
    """Run inbox-watch's host-resident wake bridge in its existing process slot."""
    from scripts.fleet_comms.authority import AuthorityService
    from scripts.session_supervisor.remote import RemoteEpicClient

    repo_root = Path(__file__).resolve().parents[2]
    resolved = subprocess.run(
        ["bash", "-c", 'source "$1/scripts/lib/handoff_identity.sh"; launcher_selector_stream "$2"',
         "supervisory-selector", str(repo_root), epic],
        check=True, capture_output=True, text=True, timeout=30,
    )
    stream_id = resolved.stdout.strip()
    supervisory_recipient(stream_id)
    launcher = repo_root / f"start-{provider}-driver.sh"
    lock = acquire_watcher_lock(agent)
    try:
        with AuthorityService() as service:
            remote = RemoteEpicClient()
            require_supervisory_api(service)
            while True:
                wake_driver_once(service, remote, stream_id=stream_id, launcher=launcher, epic=epic)
                if once:
                    return
                time.sleep(interval_seconds)
    finally:
        lock.release()


class WatcherAlreadyRunningError(RuntimeError):
    """Raised when another watcher owns an agent slot's lock."""


@dataclass(frozen=True)
class InboxEvent:
    """Stable metadata needed for a driver to decide whether to drain its inbox."""

    message_id: int
    sender: str
    request_id: str
    content: str

    def notification_line(self) -> str:
        """Return a one-line, bounded notification safe for Monitor stdout."""
        return (
            "INBOX-WATCH "
            f"id={self.message_id} "
            f"sender={_escape_one_line(self.sender)} "
            f"request_id={_escape_one_line(self.request_id)} "
            f"preview={_bounded_preview(self.content)}"
        )


@dataclass(frozen=True)
class WatcherLock:
    """An exclusive, per-seat process lock stored outside the broker database."""

    fd: int

    def release(self) -> None:
        """Release the advisory lock; the next watcher safely replaces its stale pid."""
        try:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)


def recipients_for_agent(agent: str) -> tuple[str, ...]:
    """Resolve the bridge's permanent dual-read aliases for an agent seat."""
    recipients = seat_read_aliases(resolve_recipient_alias(agent))
    if not recipients:
        raise ValueError("agent slot must not be empty")
    return recipients


def canonical_slot(agent: str) -> str:
    """Return the canonical slot used for duplicate-watcher locking."""
    return recipients_for_agent(agent)[0]


def build_poll_query(recipients: tuple[str, ...]) -> str:
    """Build the parameterized, read-only query for newly visible messages."""
    if not recipients:
        raise ValueError("at least one recipient is required")
    placeholders = ", ".join("?" for _ in recipients)
    return f"""
        SELECT id, from_llm, task_id, content
        FROM messages
        WHERE to_llm IN ({placeholders})
          AND consumed_by_live_driver = 0
          AND id > ?
        ORDER BY id ASC
    """


def poll_once(
    conn: sqlite3.Connection,
    agent: str,
    last_seen: int = 0,
) -> list[InboxEvent]:
    """Return currently unconsumed messages after the in-memory cursor.

    A fresh watcher starts with ``last_seen=0``, deliberately surfacing every
    current unconsumed row, including rows that predate the watcher process.
    """
    recipients = recipients_for_agent(agent)
    rows = conn.execute(build_poll_query(recipients), (*recipients, last_seen)).fetchall()
    return [
        InboxEvent(
            message_id=int(row["id"]),
            sender=str(row["from_llm"]),
            request_id=str(row["task_id"] or "-"),
            content=str(row["content"]),
        )
        for row in rows
    ]


def emit_notifications(events: list[InboxEvent], last_seen: int, output: TextIO) -> int:
    """Write events and advance the cursor only after each successful flush."""
    for event in events:
        output.write(f"{event.notification_line()}\n")
        output.flush()
        last_seen = event.message_id
    return last_seen


def open_readonly_db(db_path: Path) -> sqlite3.Connection:
    """Open the broker database without running migrations or taking a write lock."""
    database_uri = f"{db_path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(database_uri, uri=True, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def watcher_lock_path(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> Path:
    """Return the ignored per-seat pidfile path, rejecting unsafe slot strings."""
    slot = canonical_slot(agent)
    if not slot.replace("-", "").replace("_", "").replace(".", "").isalnum():
        raise ValueError(f"agent slot contains unsupported lock-path characters: {slot!r}")
    return lock_dir / f"inbox-watch-{slot}.pid"


def acquire_watcher_lock(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> WatcherLock:
    """Acquire an exclusive watcher lock and record the owning process id."""
    path = watcher_lock_path(agent, lock_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = f"{os.getpid()}\n"

    fd = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(fd)
        existing_pid = _read_lock_pid(path)
        slot = canonical_slot(agent)
        pid_detail = f" (pid {existing_pid})" if existing_pid is not None else ""
        raise WatcherAlreadyRunningError(
            f"inbox watcher already running for {slot!r}{pid_detail}; "
            f"stop it with scripts/ai_agent_bridge/inbox_watch.sh --stop {slot}"
        ) from exc

    try:
        os.ftruncate(fd, 0)
        os.write(fd, payload.encode("utf-8"))
    except Exception:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        raise
    return WatcherLock(fd=fd)


def stop_watcher(agent: str, lock_dir: Path = DEFAULT_LOCK_DIR) -> str:
    """Request a clean SIGTERM stop for the watcher that owns an agent slot."""
    path = watcher_lock_path(agent, lock_dir)
    if not path.exists():
        return f"No inbox watcher lock exists for {canonical_slot(agent)!r}."

    fd = os.open(path, os.O_WRONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
        return f"No inbox watcher is running for {canonical_slot(agent)!r}."

    pid = _read_lock_pid(path)
    if pid is None or not _pid_is_running(pid):
        return f"Inbox watcher lock for {canonical_slot(agent)!r} is no longer active."

    os.kill(pid, signal.SIGTERM)
    return f"Requested clean stop for inbox watcher {canonical_slot(agent)!r} (pid {pid})."


def run_watcher(
    agent: str,
    *,
    interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
    db_path: Path = DB_PATH,
    lock_dir: Path = DEFAULT_LOCK_DIR,
    output: TextIO = sys.stdout,
    once: bool = False,
) -> int:
    """Run the persistent watcher and return the final in-memory cursor.

    No messages-table mutation occurs here.  On a write/flush failure the
    exception exits the process before the failed event advances ``last_seen``;
    restarting then deliberately re-emits all still-unconsumed rows.
    """
    if interval_seconds <= 0:
        raise ValueError("poll interval must be greater than zero")

    lock = acquire_watcher_lock(agent, lock_dir)
    conn: sqlite3.Connection | None = None
    last_seen = 0
    watchdog_warned = False
    try:
        conn = open_readonly_db(db_path)
        while True:
            try:
                from ._ask_lifecycle import run_ask_watchdog

                run_ask_watchdog()
            except Exception as exc:
                if not watchdog_warned:
                    print(
                        f"⚠️  inbox watcher: ask watchdog failed: {type(exc).__name__}: {exc}",
                        file=sys.stderr,
                    )
                    watchdog_warned = True
            events = poll_once(conn, agent, last_seen)
            last_seen = emit_notifications(events, last_seen, output)
            if once:
                return last_seen
            time.sleep(interval_seconds)
    finally:
        if conn is not None:
            conn.close()
        lock.release()


def _escape_one_line(value: str) -> str:
    """Escape line breaks so one message always yields exactly one event line."""
    return value.replace("\\", "\\\\").replace("\r", "\\r").replace("\n", "\\n")


def _bounded_preview(content: str) -> str:
    """Redact, escape, and truncate message content for a compact notification."""
    preview = _escape_one_line(redact_text(content) or "")
    if len(preview) > MAX_PREVIEW_CHARS:
        return f"{preview[:MAX_PREVIEW_CHARS]}..."
    return preview


def _read_lock_pid(path: Path) -> int | None:
    """Read a positive pid from a lockfile, tolerating a partial stale write."""
    try:
        first_field = path.read_text(encoding="utf-8").split(maxsplit=1)[0]
        pid = int(first_field)
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None
    return pid if pid > 0 else None


def _pid_is_running(pid: int) -> bool:
    """Return whether a process exists without changing its state."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def build_parser() -> argparse.ArgumentParser:
    """Build the one-command watcher interface used by harness Monitor tools."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  scripts/ai_agent_bridge/inbox_watch.sh grok-infra
  scripts/ai_agent_bridge/inbox_watch.sh grok-infra --wake-driver grok --epic infra

Outputs: bounded notifications; supervisory modes consume Fleet Comms events,
prepare durable handoffs, or invoke existing driver launchers.
Exit codes: 0 success; 2 refusal/error; 75 launcher-owned restart prepared.
Related: docs/runbooks/session-supervisor.md; scripts.session_supervisor.
""",
    )
    parser.add_argument("agent", help="driver handoff agent slot to watch")
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_POLL_INTERVAL_SECONDS,
        help=f"seconds between polls (default: {DEFAULT_POLL_INTERVAL_SECONDS:g})",
    )
    parser.add_argument("--once", action="store_true", help=argparse.SUPPRESS)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--stop", action="store_true", help="request a clean stop for this slot's watcher")
    modes.add_argument("--wake-driver", choices=("grok", "gemini", "claude", "codex"),
                       help="bridge durable events to this existing driver launcher (default: notifications only)")
    modes.add_argument("--live-supervisory", action="store_true",
                       help="launcher-owned consumption under the inherited live lease (default: off)")
    parser.add_argument("--notify-parent", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument("--launch-plan", metavar="DELIVERY_ID",
                       help="validate one event before launcher claim; emits its fenced identity (default: off)")
    parser.add_argument("--epic", help="existing launcher selector for --wake-driver, for example infra or atlas")
    parser.add_argument("--stream", help="exact numeric stream for --launch-plan, for example epic:6943")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the watcher CLI while keeping normal polling stdout event-only."""
    args = build_parser().parse_args(argv)
    notify_parent = None
    try:
        if args.interval <= 0:
            raise ValueError("poll interval must be greater than zero")
        if args.launch_plan:
            from scripts.fleet_comms.authority import AuthorityService
            from scripts.session_supervisor.remote import RemoteEpicClient

            if not args.stream:
                raise ValueError("--launch-plan requires --stream")
            with AuthorityService() as service:
                plan = supervisory_launch_plan(service, RemoteEpicClient(), args.launch_plan, args.stream)
            if plan is None:
                raise ValueError("supervisory wake is occupied, stale, or unprepared")
            print(json.dumps({"session_id": plan.successor_session_id, "generation": plan.generation + 1}))
            return 0
        if args.live_supervisory:
            if args.notify_parent:
                from agents_extensions.shared.session_streams.hooks import lease_from_environment

                if lease_from_environment().holder.process_id != os.getppid():
                    raise ValueError("supervisory watcher must be a direct child of its lease-owning launcher")
                notify_parent = os.getppid()
            return run_live_supervisory_watcher(interval_seconds=args.interval)
        if args.wake_driver:
            if not args.epic:
                raise ValueError("--wake-driver requires --epic")
            run_supervisory_wake_watcher(args.agent, args.wake_driver, args.epic,
                                         interval_seconds=args.interval, once=args.once)
            return 0
        if args.stop:
            print(stop_watcher(args.agent), file=sys.stderr)
            return 0
        run_watcher(args.agent, interval_seconds=args.interval, once=args.once)
    except (OSError, RuntimeError, ValueError, sqlite3.Error) as exc:
        print(f"inbox watcher: {exc}", file=sys.stderr)
        return 2
    finally:
        if notify_parent is not None and os.getppid() == notify_parent:
            os.kill(notify_parent, signal.SIGUSR1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
