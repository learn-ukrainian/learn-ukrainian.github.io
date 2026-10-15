#!/usr/bin/env python3
"""Safe-field Fleet Comms notice for learn-ukrainian-sources failures (#10674).

Episodes. An episode is one failed run of ``learn-ukrainian-sources.service``
(one systemd invocation id), or the moment systemd refuses to restart it
because the start limit is hit. Each episode sends exactly one message to
the ``cto`` channel. A watchdog kill that systemd recovers from by
restarting is an episode and notifies: the server hung, and its stack dump
is waiting to be read. The start limit caps the episodes per window.

Two steps, two units, so neither delays a restart and none is lost when
systemd merges triggers:

``record learn-ukrainian-sources.service``
    Run by ``learn-ukrainian-sources-alert@.service`` through ``OnFailure=``.
    Local and quick: it classifies the failure from systemd's ``MONITOR_*``
    variables and writes one record file into its owner-only state
    directory. Its ``OnSuccess=`` starts the publisher.
``publish``
    Run by ``learn-ukrainian-sources-alert-publish.service``. Publishes every
    pending record through the existing Fleet Comms publisher, with a stable
    idempotency key per episode, then deletes it. A publish that fails keeps
    its record, and the unit retries.

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
RECORD_SUFFIX = ".json"
MAX_PENDING = 64
PUBLISH_BUDGET_S = 150.0
DUPLICATE_KEY = "idempotency_key_reused_with_different_payload"
_EPISODE = re.compile(r"[0-9a-f]{32}")
_INVOCATION = re.compile(r"[0-9a-f]{32}")
_UTC = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_RECORD_KEYS = frozenset({"schema", "service", "episode", "class", "at"})

Publisher = Callable[[str, str], None]


@dataclass(frozen=True)
class Record:
    episode: str
    classification: str
    at: str

    @property
    def name(self) -> str:
        return self.episode + RECORD_SUFFIX

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
    if not _INVOCATION.fullmatch(invocation):
        # No invocation id: nothing stable to key on.
        return secrets.token_hex(16)
    digest = hashlib.sha256(f"lu-sources-episode:v{SCHEMA}:{invocation}:{classification}".encode())
    return digest.hexdigest()[:32]


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(dir_fd: int) -> list[Record]:
    """Valid records, oldest first; invalid files are removed unread by anyone."""
    records = []
    for name in os.listdir(dir_fd):
        if not name.endswith(RECORD_SUFFIX) or name.startswith("."):
            continue
        record = None
        with contextlib.suppress(OSError):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=dir_fd)
            with os.fdopen(fd, "rb") as handle:
                record = parse_record(handle.read(4096))
        if record is None or record.name != name:
            with contextlib.suppress(OSError):
                os.unlink(name, dir_fd=dir_fd)
            print("sources-alert: removed an invalid record", file=sys.stderr)
            continue
        records.append(record)
    records.sort(key=lambda record: (record.at, record.episode))
    return records


def write_record(dir_fd: int, record: Record) -> bool:
    """Create the record once (fsync, then link, then directory fsync); False if it exists."""
    temporary = f".{record.episode}-{secrets.token_hex(4)}.tmp"
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=dir_fd)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(record.as_json() + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, record.name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd, follow_symlinks=False)
        except FileExistsError:
            return False
        os.fsync(dir_fd)
        return True
    finally:
        with contextlib.suppress(OSError):
            os.unlink(temporary, dir_fd=dir_fd)


def record_failure(environ: Mapping[str, str], unit: str, *, alerts_fd: int, sources_fd: int | None, now: str) -> str:
    """Record one failure notice from the ``MONITOR_*`` variables of an ``OnFailure=`` run."""
    if unit != UNIT or environ.get("MONITOR_UNIT") != UNIT:
        raise AlertError("not a learn-ukrainian-sources failure")
    result = environ.get("MONITOR_SERVICE_RESULT", "")
    if not result or result == "success":
        return "no failure to record"
    invocation = environ.get("MONITOR_INVOCATION_ID", "")
    reached_ready = None if sources_fd is None else read_ready_marker(sources_fd) == invocation
    classification = classify(result, reached_ready)
    record = Record(episode_id(invocation, classification), classification, now)
    created = write_record(alerts_fd, record)
    # Bounded backlog: while Fleet Comms is unreachable, keep the newest.
    pending = _load(alerts_fd)
    for stale in pending[: max(0, len(pending) - MAX_PENDING)]:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(stale.name, dir_fd=alerts_fd)
    return f"{classification} episode {record.episode} " + ("recorded" if created else "already recorded")


def publish_pending(
    alerts_fd: int,
    publish: Publisher,
    *,
    budget_s: float = PUBLISH_BUDGET_S,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[int, int]:
    """Publish and delete pending records, oldest first; return (sent, failed).

    One publisher at a time (an exclusive lock on the directory). It rescans
    until nothing new is pending, so a record written while it runs is sent
    in the same run; a record that failed once waits for the next run.
    """
    fcntl.flock(alerts_fd, fcntl.LOCK_EX)
    deadline = clock() + budget_s
    sent = 0
    failed: set[str] = set()
    while clock() < deadline:
        pending = [record for record in _load(alerts_fd) if record.episode not in failed]
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
            with contextlib.suppress(FileNotFoundError):
                os.unlink(record.name, dir_fd=alerts_fd)
            os.fsync(alerts_fd)
            sent += 1
    return sent, len(failed)


def _state_dir(path: str | None) -> int:
    directory = path or os.environ.get("STATE_DIRECTORY", "").split(":")[0]
    if not directory:
        raise AlertError("no state directory: run under the alert units or pass --state-dir")
    try:
        return open_state_dir(directory)
    except StateDirectoryError as error:
        raise AlertError(str(error)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--state-dir", help="owner-only record directory (default: $STATE_DIRECTORY)")
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record", help="record the failure named by systemd's MONITOR_* variables")
    record.add_argument("unit", help=f"the failed unit; only {UNIT}")
    record.add_argument(
        "--sources-state-dir",
        help="the sources unit's state directory, to tell a start-up failure from a later one",
    )
    sub.add_parser("publish", help="publish and delete every pending record")
    return parser


def main(argv: list[str] | None = None, publish: Publisher | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        alerts_fd = _state_dir(args.state_dir)
        try:
            if args.command == "record":
                sources_fd = None
                if args.sources_state_dir:
                    with contextlib.suppress(StateDirectoryError):
                        sources_fd = open_state_dir(args.sources_state_dir)
                try:
                    print(
                        "sources-alert: "
                        + record_failure(
                            os.environ, args.unit, alerts_fd=alerts_fd, sources_fd=sources_fd, now=utc_now()
                        )
                    )
                finally:
                    if sources_fd is not None:
                        os.close(sources_fd)
                return 0
            sent, failed = publish_pending(alerts_fd, publish or fleet_comms_publisher(PROJECT_ROOT))
            print(f"sources-alert: published {sent}, failed {failed}")
            return 1 if failed else 0
        finally:
            os.close(alerts_fd)
    except AlertError as error:
        print(f"sources-alert: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
