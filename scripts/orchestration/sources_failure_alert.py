#!/usr/bin/env python3
"""Safe-field Fleet Comms notice for learn-ukrainian-sources failures (#10674).

Episodes. An episode is one failed run of ``learn-ukrainian-sources.service``
(one systemd invocation id), or the moment systemd refuses to restart it
because the start limit is hit. Each episode sends exactly one message to
the ``cto`` channel. A watchdog kill that systemd recovers from by
restarting is an episode and notifies: the server hung, and its stack dump
is waiting to be read. The start limit caps the episodes per window.

No notice depends on a systemd trigger surviving. systemd merges a start
request into a run of the same unit that is still going, so a notice that
waited for its own trigger could be lost. Instead:

``record``
    ``ExecStopPost=`` of the server unit. systemd runs it after every run of
    the server, in that run's own stop path, with the run's
    ``$SERVICE_RESULT`` and ``$INVOCATION_ID``; a failed run gets one record
    in ``notices/`` under the unit's state directory. Local and quick: it
    never contacts Fleet Comms or systemd, so it cannot delay a restart by
    more than its own few hundred milliseconds.
``notify``
    ``learn-ukrainian-sources-alert.service``, started by the server's
    ``OnFailure=`` and every 5 minutes by its timer. Before each scan it
    reads the server unit's current state from systemd and records a failure
    the unit is still in. That is how the start-limit refusal is recorded:
    no server process runs, so there is no ``ExecStopPost=``, but the unit
    stays failed until an operator resets it, so the next scan or timer run
    finds it even when its ``OnFailure=`` trigger was merged away. It then
    publishes every pending record through the existing Fleet Comms
    publisher, with a stable idempotency key per episode, and keeps a
    ``.sent`` marker so the persisting state is not recorded again. Exit 0
    means nothing is pending; exit 75 means records are still pending (a
    failed or unattempted publish) and the timer's next run retries them.

A record holds only the allowlisted fields: schema version, fixed service
name, opaque episode id, UTC time and a classification (``watchdog``,
``start_limit``, ``startup``, ``other``). The message is built from those
fields and nothing else; exception text, health bodies, paths and stacks
never reach it. Rebuilding the same record gives the same bytes, so a
publish interrupted after Fleet Comms stored it is deduplicated by the key.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.orchestration.backup_failure_alert import AlertError, fleet_comms_publisher
from scripts.rag.hang_diagnostics import StateDirectoryError, open_state_dir, read_ready_marker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNIT = "learn-ukrainian-sources.service"
SERVICE = "sources"
SCHEMA = 1
CLASSES = ("watchdog", "start_limit", "startup", "other")
SUMMARIES = {
    "watchdog": (
        "systemd killed the sources MCP server after missed health pings and restarted it; "
        "its all-thread stack dump is in the unit's state directory."
    ),
    "start_limit": (
        "systemd stopped restarting the sources MCP server: its restart budget is exhausted. "
        "It stays down until an operator runs reset-failed and start."
    ),
    "startup": "the sources MCP server failed before it became ready.",
    "other": "the sources MCP server stopped with a failure outside the health watchdog.",
}
NOTICES_DIR = "notices"
RECORD_SUFFIX = ".json"
SENT_SUFFIX = ".sent"
MAX_PENDING = 64
MAX_SENT = 256
# Started publish calls end within the publisher's own 120 s timeout, so a
# run takes at most this budget plus one call (the unit allows 300 s).
PUBLISH_BUDGET_S = 150.0
SYSTEMCTL_TIMEOUT_S = 15.0
EXIT_PENDING = 75  # EX_TEMPFAIL: records remain; the next timer run retries
DUPLICATE_KEY = "idempotency_key_reused_with_different_payload"
_EPISODE = re.compile(r"[0-9a-f]{32}")
_INVOCATION = re.compile(r"[0-9a-f]{32}")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_RECORD_KEYS = frozenset({"schema", "service", "episode", "class", "at"})
SHOW_PROPERTIES = ("ActiveState", "SubState", "Result", "InvocationID")

Publisher = Callable[[str, str], None]
UnitState = Callable[[], Mapping[str, str]]


@dataclass(frozen=True)
class Record:
    episode: str
    classification: str
    at: str

    @property
    def name(self) -> str:
        return self.episode + RECORD_SUFFIX

    @property
    def sent_name(self) -> str:
        return self.episode + SENT_SUFFIX

    @property
    def idempotency_key(self) -> str:
        return f"lu-sources-alert:v{SCHEMA}:{self.episode}"

    def as_json(self) -> str:
        return json.dumps(
            {
                "schema": SCHEMA,
                "service": SERVICE,
                "episode": self.episode,
                "class": self.classification,
                "at": self.at,
            },
            sort_keys=True,
        )


@dataclass(frozen=True)
class PublishResult:
    sent: int
    failed: int
    pending: int  # valid records left after the run: failed, unattempted or new


def parse_record(raw: bytes) -> Record | None:
    """A record only if every field is allowlisted and well formed."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(data, dict) or set(data) != _RECORD_KEYS:
        return None
    if data["schema"] != SCHEMA or data["service"] != SERVICE or data["class"] not in CLASSES:
        return None
    episode, at = data["episode"], data["at"]
    if not (isinstance(episode, str) and _EPISODE.fullmatch(episode) and isinstance(at, str) and _UTC.fullmatch(at)):
        return None
    return Record(episode, data["class"], at)


def render(record: Record) -> str:
    """The whole message: a function of the record's fields only."""
    return (
        f"[sources-alert] schema={SCHEMA} service={SERVICE} class={record.classification} "
        f"episode={record.episode} at={record.at}\n{SUMMARIES[record.classification]}\n"
    )


def classify(result: str, reached_ready: bool | None) -> str:
    """Map systemd's service result to the notice class.

    ``reached_ready`` is whether the failed run had sent READY=1 (None when
    the server's state directory could not be read).
    """
    if result == "start-limit-hit":
        return "start_limit"
    if result == "watchdog":
        return "watchdog"
    if reached_ready is False:
        return "startup"
    return "other"


def episode_id(invocation: str, classification: str) -> str:
    """Opaque and stable: the same run and class always give the same id."""
    if not _INVOCATION.fullmatch(invocation):
        raise AlertError("systemd gave no valid invocation id")
    digest = hashlib.sha256(f"lu-sources-episode:v{SCHEMA}:{invocation}:{classification}".encode())
    return digest.hexdigest()[:32]


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def open_notices(state_fd: int) -> int:
    """Open (creating once) the owner-only ``notices`` directory under the state directory."""
    with contextlib.suppress(FileExistsError):
        os.mkdir(NOTICES_DIR, 0o700, dir_fd=state_fd)
    try:
        fd = os.open(NOTICES_DIR, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=state_fd)
    except OSError as error:
        raise AlertError(f"cannot open the notices directory: {type(error).__name__}") from None
    info = os.fstat(fd)
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        os.close(fd)
        raise AlertError("the notices directory is not owner-only")
    return fd


def _load(notices_fd: int) -> list[Record]:
    """Valid records, oldest first; invalid files are removed unread by anyone."""
    records = []
    for name in os.listdir(notices_fd):
        if not name.endswith(RECORD_SUFFIX) or name.startswith("."):
            continue
        record = None
        with contextlib.suppress(OSError):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=notices_fd)
            with os.fdopen(fd, "rb") as handle:
                record = parse_record(handle.read(4096))
        if record is None or record.name != name:
            with contextlib.suppress(OSError):
                os.unlink(name, dir_fd=notices_fd)
            print("sources-alert: removed an invalid record", file=sys.stderr)
            continue
        records.append(record)
    records.sort(key=lambda record: (record.at, record.episode))
    return records


def _exists(notices_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=notices_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def write_record(notices_fd: int, record: Record) -> bool:
    """Create the record once (fsync, link, directory fsync); False if recorded or sent before."""
    if _exists(notices_fd, record.sent_name):
        return False
    temporary = f".{record.episode}-{secrets.token_hex(4)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(temporary, flags, 0o600, dir_fd=notices_fd)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(record.as_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, record.name, src_dir_fd=notices_fd, dst_dir_fd=notices_fd, follow_symlinks=False)
        except FileExistsError:
            return False
        os.fsync(notices_fd)
        return True
    finally:
        with contextlib.suppress(OSError):
            os.unlink(temporary, dir_fd=notices_fd)


def _record(notices_fd: int, state_fd: int | None, result: str, invocation: str, now: str) -> str:
    reached_ready = None if state_fd is None else read_ready_marker(state_fd) == invocation
    classification = classify(result, reached_ready)
    record = Record(episode_id(invocation, classification), classification, now)
    created = write_record(notices_fd, record)
    # Bounded backlog: while Fleet Comms is unreachable, keep the newest.
    pending = _load(notices_fd)
    for stale in pending[: max(0, len(pending) - MAX_PENDING)]:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(stale.name, dir_fd=notices_fd)
    return f"{classification} episode {record.episode} " + ("recorded" if created else "already recorded")


def record_stopped_run(environ: Mapping[str, str], *, state_fd: int, notices_fd: int, now: str) -> str:
    """Record the run that just stopped, from the ``ExecStopPost=`` environment."""
    result = environ.get("SERVICE_RESULT", "")
    if not result or result == "success":
        return "no failure to record"
    return _record(notices_fd, state_fd, result, environ.get("INVOCATION_ID", ""), now)


def record_unit_state(unit_state: UnitState, *, state_fd: int | None, notices_fd: int, now: str) -> str:
    """Record the failure the server unit is in now, if any, as systemd reports it."""
    state = unit_state()
    result = state.get("Result", "")
    failed = state.get("ActiveState") == "failed" or state.get("SubState", "").startswith("auto-restart")
    if not failed or not result or result == "success":
        return "the unit is not in a failed state"
    return _record(notices_fd, state_fd, result, state.get("InvocationID", ""), now)


def systemctl_unit_state(manager: str) -> UnitState:
    """Read the server unit's state from the given service manager (``user`` or ``system``)."""
    command = ["systemctl", *(["--user"] if manager == "user" else []), "show", UNIT]
    command += [f"--property={name}" for name in SHOW_PROPERTIES]

    def read() -> Mapping[str, str]:
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=SYSTEMCTL_TIMEOUT_S)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AlertError(f"systemctl show could not run: {type(error).__name__}") from None
        if result.returncode != 0:
            raise AlertError(f"systemctl show exited {result.returncode}")
        state = dict(line.partition("=")[::2] for line in result.stdout.splitlines())
        return {name: state.get(name, "") for name in SHOW_PROPERTIES}

    return read


def _mark_sent(notices_fd: int, record: Record) -> None:
    with contextlib.suppress(FileNotFoundError):
        os.rename(record.name, record.sent_name, src_dir_fd=notices_fd, dst_dir_fd=notices_fd)
    os.fsync(notices_fd)


def _prune_sent(notices_fd: int) -> None:
    """Keep the newest ``MAX_SENT`` markers; episode ids are never reused, so older ones are moot."""
    markers = []
    for name in os.listdir(notices_fd):
        if name.endswith(SENT_SUFFIX) and not name.startswith("."):
            with contextlib.suppress(FileNotFoundError):
                markers.append((os.stat(name, dir_fd=notices_fd, follow_symlinks=False).st_mtime_ns, name))
    markers.sort(reverse=True)
    for _mtime, name in markers[MAX_SENT:]:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(name, dir_fd=notices_fd)


def publish_pending(
    notices_fd: int,
    publish: Publisher,
    *,
    before_scan: Callable[[], object] | None = None,
    budget_s: float = PUBLISH_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> PublishResult:
    """Publish pending records, oldest first, and mark each sent.

    One publisher at a time (an exclusive lock on the directory). Before
    each scan it calls ``before_scan`` (the unit-state check), and it rescans
    until nothing new is pending, so a record written while it runs is sent
    in the same run; a record whose publish failed waits for the next run.
    No publish starts after the budget. ``pending`` counts what is left.
    """
    fcntl.flock(notices_fd, fcntl.LOCK_EX)
    deadline = clock() + budget_s
    sent = 0
    failed: set[str] = set()
    while clock() < deadline:
        if before_scan is not None:
            before_scan()
        pending = [record for record in _load(notices_fd) if record.episode not in failed]
        if not pending:
            break
        for record in pending:
            if clock() >= deadline:
                break
            try:
                publish(render(record), record.idempotency_key)
            except AlertError as error:
                # The key is unique to this episode: a conflicting payload
                # means Fleet Comms already holds its message.
                if DUPLICATE_KEY not in str(error):
                    print(f"sources-alert: publish failed for episode {record.episode}: {error}", file=sys.stderr)
                    failed.add(record.episode)
                    continue
            _mark_sent(notices_fd, record)
            sent += 1
    _prune_sent(notices_fd)
    return PublishResult(sent, len(failed), len(_load(notices_fd)))


def notify(
    state_fd: int,
    notices_fd: int,
    publish: Publisher,
    unit_state: UnitState,
    *,
    budget_s: float = PUBLISH_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Record the unit's current failure, publish everything pending; return the exit code."""
    errors: list[str] = []

    def check_unit() -> None:
        try:
            record_unit_state(unit_state, state_fd=state_fd, notices_fd=notices_fd, now=utc_now())
        except AlertError as error:
            if str(error) not in errors:
                errors.append(str(error))

    result = publish_pending(notices_fd, publish, before_scan=check_unit, budget_s=budget_s, clock=clock)
    print(f"sources-alert: published {result.sent}, failed {result.failed}, pending {result.pending}")
    for error in errors:
        print(f"sources-alert: could not read the unit state: {error}", file=sys.stderr)
    if errors:
        return 1
    return EXIT_PENDING if result.pending else 0


def _open_state(path: str | None) -> int:
    directory = path or os.environ.get("STATE_DIRECTORY", "").split(":")[0]
    if not directory:
        raise AlertError("no state directory: run under the sources units or pass --state-dir")
    try:
        return open_state_dir(directory)
    except StateDirectoryError as error:
        raise AlertError(str(error)) from None


def _manager(choice: str, environ: Mapping[str, str]) -> str:
    # systemd sets $MANAGERPID only for processes of a per-user manager.
    if choice == "auto":
        return "user" if environ.get("MANAGERPID") else "system"
    return choice


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exit codes: 0 done (notify: nothing pending); 75 notify left records pending, "
            "the next timer run retries; 1 error; 2 usage."
        ),
    )
    parser.add_argument("--state-dir", help="the sources unit's owner-only state directory (default: $STATE_DIRECTORY)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("record", help="record the run that just stopped ($SERVICE_RESULT, $INVOCATION_ID)")
    notify_parser = sub.add_parser("notify", help="record the unit's current failure, then publish pending records")
    notify_parser.add_argument(
        "--manager",
        choices=("auto", "user", "system"),
        default="auto",
        help="service manager to read the unit from (default: user under a per-user manager, else system)",
    )
    return parser


def main(
    argv: list[str] | None = None,
    publish: Publisher | None = None,
    unit_state: UnitState | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        state_fd = _open_state(args.state_dir)
        try:
            notices_fd = open_notices(state_fd)
            try:
                if args.command == "record":
                    print(
                        "sources-alert: "
                        + record_stopped_run(os.environ, state_fd=state_fd, notices_fd=notices_fd, now=utc_now())
                    )
                    return 0
                return notify(
                    state_fd,
                    notices_fd,
                    publish or fleet_comms_publisher(PROJECT_ROOT),
                    unit_state or systemctl_unit_state(_manager(args.manager, os.environ)),
                    clock=clock,
                )
            finally:
                os.close(notices_fd)
        finally:
            os.close(state_fd)
    except AlertError as error:
        print(f"sources-alert: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
