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
    in ``notices/`` under the unit's state directory. If that write fails
    (a full disk, any ``OSError``), the record goes to ``notices/`` under
    the unit's runtime directory instead: a memory file system systemd keeps
    until reboot, so it does not depend on the write that failed. Local and
    quick: it never contacts Fleet Comms or systemd, so it cannot delay a
    restart by more than its own few hundred milliseconds, and a recorder
    that fails anyway only exits non-zero, which the unit ignores.
``notify``
    ``learn-ukrainian-sources-alert.service``, started by the server's
    ``OnFailure=`` and every 5 minutes by its timer. Before each scan it
    reads the server unit's current state from systemd and records a failure
    the unit is still in. That is how the start-limit refusal is recorded:
    no server process runs, so there is no ``ExecStopPost=``, but the unit
    stays failed until an operator resets it, so the next scan or timer run
    finds it even when its ``OnFailure=`` trigger was merged away. It moves
    records from the runtime directory to the state directory when it can,
    then publishes every pending record in both through the existing Fleet
    Comms publisher, with a stable idempotency key per episode, and keeps a
    ``.sent`` marker so the persisting state is not recorded again. Exit 0
    means nothing is pending; exit 75 means records are still pending (a
    failed or unattempted publish) and the timer's next run retries them.

Bounded backlog, nothing dropped. The notifier is the only process that
removes a pending record, and only after publishing it or after counting it
in an ``overflow`` record: when more than ``MAX_PENDING`` per-run records wait
(Fleet Comms unreachable for hours), the oldest beyond the bound, and any
earlier overflow record, are merged into one new overflow record (how many
episodes it counts, the first and last episode ids) that is written before
anything it counts is removed. The overflow record is published as its own
notice and keeps the run pending (exit 75) until it is sent. A crash between
writing it and removing what it counts can only count those episodes twice.

A record holds only the allowlisted fields: schema version, fixed service
name, opaque episode id, UTC time and a classification (``watchdog``,
``start_limit``, ``startup``, ``other``), plus, for ``overflow``, the count
and the first and last counted episode ids. The message is built from those
fields and nothing else; exception text, health bodies, paths and stacks
never reach it. Rebuilding the same record gives the same bytes, so a
publish interrupted after Fleet Comms stored it is deduplicated by the key.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
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
OVERFLOW = "overflow"
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
    OVERFLOW: (
        "more failure notices waited than the backlog keeps while they could not be sent; "
        "these episodes are counted here instead of sent one by one."
    ),
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
_OVERFLOW_KEYS = _RECORD_KEYS | {"count", "first", "last"}
SHOW_PROPERTIES = ("ActiveState", "SubState", "Result", "InvocationID")

Publisher = Callable[[str, str], None]
UnitState = Callable[[], Mapping[str, str]]


@dataclass(frozen=True)
class Record:
    episode: str
    classification: str
    at: str
    # An overflow record only: how many episodes it counts, and the first and last.
    count: int = 0
    first: str = ""
    last: str = ""

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
        fields: dict[str, object] = {
            "schema": SCHEMA,
            "service": SERVICE,
            "episode": self.episode,
            "class": self.classification,
            "at": self.at,
        }
        if self.classification == OVERFLOW:
            fields.update(count=self.count, first=self.first, last=self.last)
        return json.dumps(fields, sort_keys=True)


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
    if not isinstance(data, dict):
        return None
    overflow = data.get("class") == OVERFLOW
    if set(data) != (_OVERFLOW_KEYS if overflow else _RECORD_KEYS):
        return None
    if data["schema"] != SCHEMA or data["service"] != SERVICE or not (overflow or data["class"] in CLASSES):
        return None
    episode, at = data["episode"], data["at"]
    if not (_is_episode(episode) and isinstance(at, str) and _UTC.fullmatch(at)):
        return None
    if not overflow:
        return Record(episode, data["class"], at)
    count, first, last = data["count"], data["first"], data["last"]
    if type(count) is not int or count < 1 or not (_is_episode(first) and _is_episode(last)):
        return None
    return Record(episode, OVERFLOW, at, count, first, last)


def _is_episode(value: object) -> bool:
    return isinstance(value, str) and _EPISODE.fullmatch(value) is not None


def render(record: Record) -> str:
    """The whole message: a function of the record's fields only."""
    counted = (
        f" count={record.count} first={record.first} last={record.last}" if record.classification == OVERFLOW else ""
    )
    return (
        f"[sources-alert] schema={SCHEMA} service={SERVICE} class={record.classification} "
        f"episode={record.episode} at={record.at}{counted}\n{SUMMARIES[record.classification]}\n"
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


def overflow_id(count: int, first: str, last: str) -> str:
    """Opaque and a function of what the overflow record counts: a merged one gets a new key."""
    return hashlib.sha256(f"lu-sources-overflow:v{SCHEMA}:{count}:{first}:{last}".encode()).hexdigest()[:32]


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


def _sent_elsewhere(record: Record, others: Sequence[int]) -> bool:
    """Whether another spool holds the record's sent marker (an unreadable spool holds none).

    A pending copy elsewhere does not count: it may be the one whose write
    failed, and two pending copies are published once and the spare removed.
    """
    for fd in others:
        with contextlib.suppress(OSError):
            if _exists(fd, record.sent_name):
                return True
    return False


def write_record(notices_fd: int, record: Record, *, others: Sequence[int] = ()) -> bool:
    """Create the record once (fsync, link, directory fsync); False if recorded or sent before.

    ``others`` are the other spools' notices directories: a record sent
    from there is not written again.
    """
    if _exists(notices_fd, record.sent_name) or _sent_elsewhere(record, others):
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


def persist(record: Record, notices_fd: int | None, fallback_fd: int | None) -> str:
    """Write the record to the state directory, or to the runtime directory when that fails.

    Raises :class:`AlertError` naming the errors when neither takes it.
    """
    spools = [(fd, "") for fd in (notices_fd,) if fd is not None]
    spools += [(fd, " in the runtime directory") for fd in (fallback_fd,) if fd is not None]
    errors = []
    for fd, where in spools:
        others = [other for other, _where in spools if other != fd]
        try:
            created = write_record(fd, record, others=others)
        except OSError as error:
            errors.append(errno.errorcode.get(error.errno or 0, type(error).__name__))
            continue
        return ("recorded" + where) if created else "already recorded"
    raise AlertError("could not write the record anywhere: " + (", ".join(errors) or "no notices directory"))


def _record(
    notices_fd: int | None, state_fd: int | None, result: str, invocation: str, now: str, fallback_fd: int | None
) -> str:
    reached_ready = None if state_fd is None else read_ready_marker(state_fd) == invocation
    classification = classify(result, reached_ready)
    record = Record(episode_id(invocation, classification), classification, now)
    # Never removes anything: only the notifier does, after publishing or counting.
    return f"{classification} episode {record.episode} " + persist(record, notices_fd, fallback_fd)


def record_stopped_run(
    environ: Mapping[str, str],
    *,
    state_fd: int | None,
    notices_fd: int | None,
    now: str,
    fallback_fd: int | None = None,
) -> str:
    """Record the run that just stopped, from the ``ExecStopPost=`` environment."""
    result = environ.get("SERVICE_RESULT", "")
    if not result or result == "success":
        return "no failure to record"
    return _record(notices_fd, state_fd, result, environ.get("INVOCATION_ID", ""), now, fallback_fd)


def record_unit_state(
    unit_state: UnitState,
    *,
    state_fd: int | None,
    notices_fd: int | None,
    now: str,
    fallback_fd: int | None = None,
) -> str:
    """Record the failure the server unit is in now, if any, as systemd reports it."""
    state = unit_state()
    result = state.get("Result", "")
    failed = state.get("ActiveState") == "failed" or state.get("SubState", "").startswith("auto-restart")
    if not failed or not result or result == "success":
        return "the unit is not in a failed state"
    return _record(notices_fd, state_fd, result, state.get("InvocationID", ""), now, fallback_fd)


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
    # The rename is done; a marker lost to a crash only re-sends the same bytes, which the key deduplicates.
    with contextlib.suppress(OSError):
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


def _sort_key(record: Record) -> tuple[str, str]:
    return (record.at, record.episode)


def _pending(spools: Sequence[int]) -> list[tuple[int, Record]]:
    """Valid records of every spool, oldest first; a record in two spools counts once (the first)."""
    seen: dict[str, tuple[int, Record]] = {}
    for fd in spools:
        for record in _load(fd):
            seen.setdefault(record.episode, (fd, record))
    return sorted(seen.values(), key=lambda item: _sort_key(item[1]))


def migrate(notices_fd: int, fallback_fd: int) -> None:
    """Move records from the runtime directory to the state directory, which survives a reboot."""
    for record in _load(fallback_fd):
        try:
            write_record(notices_fd, record)  # False: already there or sent, so the copy is moot
        except OSError:
            return  # the state directory still fails; the record waits where it is
        with contextlib.suppress(FileNotFoundError):
            os.unlink(record.name, dir_fd=fallback_fd)


def coalesce(notices_fd: int, now: str) -> None:
    """Bound the per-run records to ``MAX_PENDING`` without dropping one.

    The oldest beyond the bound and every earlier overflow record are merged
    into one new overflow record, written before any of them is removed.
    """
    records = _load(notices_fd)
    runs = [record for record in records if record.classification != OVERFLOW]
    overflows = [record for record in records if record.classification == OVERFLOW]
    excess = runs[: max(0, len(runs) - MAX_PENDING)]
    if not excess and len(overflows) <= 1:
        return
    count = sum(record.count for record in overflows) + len(excess)
    first = overflows[0].first if overflows else excess[0].episode
    last = excess[-1].episode if excess else overflows[-1].last
    merged = Record(overflow_id(count, first, last), OVERFLOW, now, count, first, last)
    try:
        write_record(notices_fd, merged)
    except OSError as error:
        # Nothing is removed: the backlog stays above the bound until a write succeeds.
        print(f"sources-alert: could not write the overflow record: {type(error).__name__}", file=sys.stderr)
        return
    for record in (*overflows, *excess):
        if record.episode != merged.episode:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(record.name, dir_fd=notices_fd)
    with contextlib.suppress(OSError):
        os.fsync(notices_fd)


def publish_pending(
    notices_fd: int | None,
    publish: Publisher,
    *,
    fallback_fd: int | None = None,
    before_scan: Callable[[], object] | None = None,
    budget_s: float = PUBLISH_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> PublishResult:
    """Publish pending records of both spools, oldest first, and mark each sent.

    One publisher at a time (an exclusive lock on each spool). Before each
    scan it moves records from the runtime directory to the state directory,
    calls ``before_scan`` (the unit-state check) and bounds the backlog, and
    it rescans until nothing new is pending, so a record written while it
    runs is sent in the same run; a record whose publish failed waits for the
    next run. No publish starts after the budget. ``pending`` counts what is
    left.
    """
    spools = [fd for fd in (notices_fd, fallback_fd) if fd is not None]
    for fd in spools:
        fcntl.flock(fd, fcntl.LOCK_EX)
    deadline = clock() + budget_s
    sent = 0
    failed: set[str] = set()
    while clock() < deadline:
        if notices_fd is not None and fallback_fd is not None:
            migrate(notices_fd, fallback_fd)
        if before_scan is not None:
            before_scan()
        coalesce(spools[0], utc_now())
        pending = [(fd, record) for fd, record in _pending(spools) if record.episode not in failed]
        if not pending:
            break
        for fd, record in pending:
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
            try:
                _mark_sent(fd, record)
            except OSError as error:
                print(f"sources-alert: could not mark episode {record.episode} sent: {error.strerror}", file=sys.stderr)
                failed.add(record.episode)
                continue
            sent += 1
    for fd in spools:
        with contextlib.suppress(OSError):
            _prune_sent(fd)
    return PublishResult(sent, len(failed), len(_pending(spools)))


def notify(
    state_fd: int | None,
    notices_fd: int | None,
    publish: Publisher,
    unit_state: UnitState,
    *,
    fallback_fd: int | None = None,
    budget_s: float = PUBLISH_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    """Record the unit's current failure, publish everything pending; return the exit code."""
    errors: list[str] = []

    def check_unit() -> None:
        try:
            record_unit_state(
                unit_state, state_fd=state_fd, notices_fd=notices_fd, now=utc_now(), fallback_fd=fallback_fd
            )
        except AlertError as error:
            if str(error) not in errors:
                errors.append(str(error))

    result = publish_pending(
        notices_fd, publish, fallback_fd=fallback_fd, before_scan=check_unit, budget_s=budget_s, clock=clock
    )
    print(f"sources-alert: published {result.sent}, failed {result.failed}, pending {result.pending}")
    for error in errors:
        print(f"sources-alert: could not record the unit state: {error}", file=sys.stderr)
    if errors:
        return 1
    return EXIT_PENDING if result.pending else 0


def _open_private(path: str) -> int:
    try:
        return open_state_dir(path)
    except StateDirectoryError as error:
        raise AlertError(str(error)) from None


def _directory(path: str | None, variable: str) -> str:
    # systemd sets $STATE_DIRECTORY and $RUNTIME_DIRECTORY, colon-separated when a unit names several.
    return path or os.environ.get(variable, "").split(":")[0]


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
            "the next timer run retries; 1 error (the state directory or the unit state could not be used; "
            "whatever could be recorded or published was); 2 usage."
        ),
    )
    parser.add_argument("--state-dir", help="the sources unit's owner-only state directory (default: $STATE_DIRECTORY)")
    parser.add_argument(
        "--runtime-dir",
        help="the owner-only runtime directory that takes records the state directory refuses "
        "(default: $RUNTIME_DIRECTORY)",
    )
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


def _open_spool(
    stack: contextlib.ExitStack, directory: str, label: str, problems: list[str]
) -> tuple[int | None, int | None]:
    """The directory's descriptor and its notices directory's; None for what could not be opened."""
    try:
        base = _open_private(directory)
    except AlertError as error:
        problems.append(f"{label} directory: {error}")
        return None, None
    stack.callback(os.close, base)
    try:
        notices = open_notices(base)
    except (AlertError, OSError) as error:
        problems.append(f"{label} directory: {error}")
        return base, None
    stack.callback(os.close, notices)
    return base, notices


def main(
    argv: list[str] | None = None,
    publish: Publisher | None = None,
    unit_state: UnitState | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> int:
    args = build_parser().parse_args(argv)
    problems: list[str] = []
    with contextlib.ExitStack() as stack:
        state_fd = notices_fd = fallback_fd = None
        state = _directory(args.state_dir, "STATE_DIRECTORY")
        if state:
            state_fd, notices_fd = _open_spool(stack, state, "state", problems)
        else:
            problems.append("no state directory: run under the sources units or pass --state-dir")
        runtime = _directory(args.runtime_dir, "RUNTIME_DIRECTORY")
        if runtime:
            _runtime_fd, fallback_fd = _open_spool(stack, runtime, "runtime", problems)
        if notices_fd is None and fallback_fd is None:
            for problem in problems:
                print(f"sources-alert: {problem}", file=sys.stderr)
            return 1
        try:
            if args.command == "record":
                note = record_stopped_run(
                    os.environ, state_fd=state_fd, notices_fd=notices_fd, now=utc_now(), fallback_fd=fallback_fd
                )
                print(f"sources-alert: {note}")
                code = 0
            else:
                code = notify(
                    state_fd,
                    notices_fd,
                    publish or fleet_comms_publisher(PROJECT_ROOT),
                    unit_state or systemctl_unit_state(_manager(args.manager, os.environ)),
                    fallback_fd=fallback_fd,
                    clock=clock,
                )
        except AlertError as error:
            problems.append(str(error))
            code = 1
    for problem in problems:
        print(f"sources-alert: {problem}", file=sys.stderr)
    return 1 if problems else code


if __name__ == "__main__":
    sys.exit(main())
