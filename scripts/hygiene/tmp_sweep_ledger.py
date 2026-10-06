"""Append-only deletion ledger and quarantine state for the temp sweep (#9887).

Every entry the sweep takes from its original path gets a ``quarantine``
record here first, written with ``O_APPEND`` and flushed with ``fsync`` before
the rename. Each later step of the same entry (confirmed, returned, restored,
purged, reconciled after a crash) is another appended record with the same
``ledger_id``; no record is ever rewritten. Folding the records by
``ledger_id`` gives each entry's current state.

The ledger lives in the XDG state home under the repository's namespace
(``$XDG_STATE_HOME/learn-ukrainian/tmp-sweep/ledger.jsonl``, default
``~/.local/state/...``), never under the temp root or inside the repository,
so cleaning the temp area never takes the record of what was removed with it.
"""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
import secrets
import stat
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.common.jsonl import jsonl_lines

SCHEMA = "tmp-sweep-ledger.v1"
STATE_NAMESPACE = ("learn-ukrainian", "tmp-sweep")
LEDGER_NAME = "ledger.jsonl"
LOCK_NAME = "ledger.lock"
DEFAULT_DIGEST_LIMIT = 64 * 1024 * 1024
DEFAULT_QUARANTINE_S = 7 * 86400
# Event -> state. "reconciled" takes its state from the record's outcome, and
# "restore_failed" returns the entry to the state it had before the restore.
EVENT_STATES = {
    "quarantine": "pending",
    "quarantined": "quarantined",
    "quarantine_failed": "at_origin",
    "returned": "returned",
    "return_blocked": "return_blocked",
    "purge": "purging",
    "purge_failed": "purging",
    "purged": "purged",
    "restore": "restoring",
    "restored": "restored",
}
RECONCILE_OUTCOMES = frozenset({"at_origin", "returned", "return_blocked", "missing", "purged"})
TERMINAL_STATES = frozenset({"at_origin", "returned", "missing", "purged", "restored"})
# States whose entry should still sit in its quarantine location.
HELD_STATES = frozenset({"pending", "quarantined", "return_blocked", "purging", "restoring"})
_FILE_FLAGS = os.O_NOFOLLOW | os.O_CLOEXEC


class LedgerError(Exception):
    """The ledger cannot be read, written or locked; nothing may leave its path."""


class DurabilityError(LedgerError):
    """A directory could not be synced, so a step cannot be recorded as complete; the run stops."""


def sync_directory(directory: Path | int) -> None:
    """``fsync`` a directory (a path or an open descriptor) so its entries survive power loss.

    Creating, renaming or removing an entry changes its parent directory, and
    ``fsync(2)`` on the file alone does not persist that change; the directory
    itself must be synced. Raises ``DurabilityError`` when the sync fails.
    """
    try:
        if isinstance(directory, int):
            os.fsync(directory)
            return
        fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as error:
        raise DurabilityError(f"directory sync failed: {error.strerror}") from error


def default_state_dir() -> Path:
    """``$XDG_STATE_HOME/learn-ukrainian/tmp-sweep``; a relative or empty value is ignored per the XDG spec."""
    configured = os.environ.get("XDG_STATE_HOME", "")
    base = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / ".local" / "state"
    return base.joinpath(*STATE_NAMESPACE)


def utc_iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def parse_iso(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def new_id() -> str:
    return secrets.token_hex(6)


def new_run_id(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


def validate_state_dir(state_dir: Path, *, forbidden: tuple[Path, ...]) -> Path:
    """Return the resolved state directory; refuse one at or under any ``forbidden`` root (temp root, repository)."""
    resolved = state_dir.expanduser().resolve()
    for root in forbidden:
        root = root.resolve()
        if resolved == root or root in resolved.parents:
            raise LedgerError("the ledger directory must not be under the temp root or inside the repository")
    return resolved


@dataclass
class Entry:
    """One quarantined entry: its ``quarantine`` record, current state and every record in order."""

    ledger_id: str
    intent: dict[str, Any]
    state: str
    records: list[dict[str, Any]] = field(default_factory=list)
    prior_state: str | None = None

    @property
    def original(self) -> Path:
        return Path(self.intent["original_path"])

    @property
    def location(self) -> Path:
        return Path(self.intent["quarantine_path"])

    @property
    def quarantined_at(self) -> float:
        return parse_iso(self.intent["at"])

    @property
    def confirmed_at(self) -> float | None:
        confirmed = [r for r in self.records if r["event"] == "quarantined"]
        return parse_iso(confirmed[-1]["at"]) if confirmed else None


class Ledger:
    """The JSONL ledger file plus the lock that serializes every writer (apply runs and restores)."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.path = directory / LEDGER_NAME

    def ensure_directory(self) -> None:
        """Create the directory (owner-only) and any missing ancestor, syncing each new entry's parent."""
        try:
            missing = []
            directory = self.directory
            while not os.path.lexists(directory):
                missing.append(directory)
                directory = directory.parent
            for created in reversed(missing):
                # Ancestors take the default mode, as ``mkdir -p`` would; the ledger directory is 0700.
                with contextlib.suppress(FileExistsError):
                    os.mkdir(created, 0o700 if created == self.directory else 0o777)
                # Synced even when a concurrent writer won the race: its sync may not have happened yet.
                sync_directory(created.parent)
            info = os.lstat(self.directory)
        except OSError as error:
            raise LedgerError(f"ledger directory unavailable: {error.strerror}") from error
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            raise LedgerError("ledger directory is not a directory owned by this user")

    @contextlib.contextmanager
    def exclusive(self, *, wait: bool) -> Iterator[None]:
        """Hold the writer lock; with ``wait=False`` a held lock raises ``LedgerError`` at once."""
        self.ensure_directory()
        try:
            fd = os.open(self.directory / LOCK_NAME, os.O_RDWR | os.O_CREAT | _FILE_FLAGS, 0o600)
        except OSError as error:
            raise LedgerError(f"ledger lock unavailable: {error.strerror}") from error
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if wait else fcntl.LOCK_NB))
            except BlockingIOError as error:
                raise LedgerError("another sweep or restore holds the ledger; retry later") from error
            yield
        finally:
            os.close(fd)

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        """Append one record durably: ``O_APPEND`` write, then ``fsync`` (and the directory's on creation).

        A torn last line from a crash is closed with a newline first, so it
        stays one malformed record and never merges with this one.
        """
        record = {"schema": SCHEMA, **record}
        data = (json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
        self.ensure_directory()
        created = not os.path.lexists(self.path)
        try:
            # Read access only to inspect the last byte; every write lands at the end.
            fd = os.open(self.path, os.O_RDWR | os.O_APPEND | os.O_CREAT | _FILE_FLAGS, 0o600)
        except OSError as error:
            raise LedgerError(f"ledger not writable: {error.strerror}") from error
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise LedgerError("ledger is not a regular file owned by this user")
            if info.st_size and os.pread(fd, 1, info.st_size - 1) != b"\n":
                data = b"\n" + data
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view) :]
            os.fsync(fd)
        except OSError as error:
            raise LedgerError(f"ledger write failed: {error.strerror}") from error
        finally:
            os.close(fd)
        if created:
            sync_directory(self.directory)
        return record

    def read(self) -> tuple[list[dict[str, Any]], int]:
        """Every well-formed record in file order, and the count of malformed lines (torn writes)."""
        try:
            fd = os.open(self.path, os.O_RDONLY | _FILE_FLAGS)
        except FileNotFoundError:
            return [], 0
        except OSError as error:
            raise LedgerError(f"ledger not readable: {error.strerror}") from error
        try:
            with os.fdopen(fd, "rb") as handle:
                text = handle.read().decode("utf-8", errors="replace")
        except OSError as error:
            raise LedgerError(f"ledger not readable: {error.strerror}") from error
        records: list[dict[str, Any]] = []
        malformed = 0
        for line in jsonl_lines(text):
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                malformed += 1
                continue
            if isinstance(record, dict) and isinstance(record.get("ledger_id"), str) and record.get("event"):
                records.append(record)
            else:
                malformed += 1
        return records, malformed

    def entries(self) -> tuple[dict[str, Entry], int]:
        """Fold records into entries by ``ledger_id``; records without a ``quarantine`` intent count as malformed."""
        records, malformed = self.read()
        entries: dict[str, Entry] = {}
        for record in records:
            ledger_id, event = record["ledger_id"], record["event"]
            if event == "quarantine":
                if ledger_id in entries:
                    malformed += 1
                    continue
                entries[ledger_id] = Entry(ledger_id, record, "pending", [record])
                continue
            entry = entries.get(ledger_id)
            if entry is None:
                malformed += 1
                continue
            entry.records.append(record)
            if event == "restore":
                entry.prior_state = entry.state
            if event == "reconciled" and record.get("outcome") in RECONCILE_OUTCOMES:
                entry.state = record["outcome"]
            elif event == "restore_failed":
                entry.state = entry.prior_state or "quarantined"
            elif event in EVENT_STATES:
                entry.state = EVENT_STATES[event]
            else:
                malformed += 1
        return entries, malformed


def _read_digest(path: Path, info: os.stat_result) -> str:
    """SHA-256 of a regular file read by descriptor without following links or touching atime."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | _FILE_FLAGS | getattr(os, "O_NOATIME", 0))
    except PermissionError:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | _FILE_FLAGS)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise OSError("file replaced while hashing")
        digest = hashlib.sha256()
        while chunk := os.read(fd, 1 << 20):
            digest.update(chunk)
        return digest.hexdigest()
    finally:
        os.close(fd)


def build_manifest(path: Path, *, digest_limit: int = DEFAULT_DIGEST_LIMIT, ctime: bool = False) -> dict[str, Any]:
    """Describe every node below ``path`` (``.`` is the entry itself), sorted by relative path.

    Each node has its type, permission bits and mtime (ns); regular files add
    size and, up to ``digest_limit`` bytes, a SHA-256 (larger ones carry
    ``digest_skipped_size`` and are counted in ``digest_skipped_files``);
    symlinks add their target. With ``ctime`` each node also carries
    ``ctime_ns``, for comparisons that are never recorded. Symlinks are never
    followed and devices never crossed; raises ``OSError`` when a node cannot
    be read.
    """
    nodes: list[dict[str, Any]] = []
    total = files = skipped = 0
    newest_m = newest_c = 0.0
    device = path.lstat().st_dev
    pending = [(path, ".")]
    while pending:
        node, relative = pending.pop()
        info = node.lstat()
        if info.st_dev != device:
            raise OSError(f"{relative} is on another device")
        newest_m, newest_c = max(newest_m, info.st_mtime), max(newest_c, info.st_ctime)
        item: dict[str, Any] = {"path": relative, "mode": stat.S_IMODE(info.st_mode), "mtime_ns": info.st_mtime_ns}
        if ctime:
            item["ctime_ns"] = info.st_ctime_ns
        if stat.S_ISDIR(info.st_mode):
            item["type"] = "directory"
            prefix = "" if relative == "." else relative + "/"
            pending.extend((child, prefix + child.name) for child in node.iterdir())
        elif stat.S_ISREG(info.st_mode):
            item |= {"type": "file", "size": info.st_size}
            total += info.st_size
            files += 1
            if info.st_size <= digest_limit:
                item["sha256"] = _read_digest(node, info)
            else:
                item["digest_skipped_size"] = True
                skipped += 1
        elif stat.S_ISLNK(info.st_mode):
            item |= {"type": "symlink", "target": os.readlink(node)}
        else:
            raise OSError(f"{relative} is not a file, directory or symlink")
        nodes.append(item)
    nodes.sort(key=lambda item: item["path"])
    return {
        "total_bytes": total,
        "file_count": files,
        "newest_mtime": utc_iso(newest_m),
        "newest_ctime": utc_iso(newest_c),
        "digest_limit_bytes": digest_limit,
        "digest_skipped_files": skipped,
        "manifest": nodes,
    }


def manifest_mismatches(recorded: list[dict[str, Any]], current: list[dict[str, Any]]) -> list[str]:
    """Relative paths whose node differs, is missing or is new; empty when the trees match exactly."""
    before = {item["path"]: item for item in recorded}
    after = {item["path"]: item for item in current}
    return sorted(path for path in before.keys() | after.keys() if before.get(path) != after.get(path))


def digest_unverified(recorded: list[dict[str, Any]], mismatches: list[str]) -> list[str]:
    """Recorded files above the digest limit that matched only by size and mtime, so their bytes are unproven."""
    changed = set(mismatches)
    return [item["path"] for item in recorded if item.get("digest_skipped_size") and item["path"] not in changed]


def _parent(relative: str) -> str:
    return relative.rsplit("/", 1)[0] if "/" in relative else "."


def surviving_mismatches(
    recorded: list[dict[str, Any]], current: list[dict[str, Any]], *, changed_by: float
) -> list[str]:
    """Nodes an interrupted deletion left that are new, changed, or changed after ``changed_by`` (epoch seconds).

    ``current`` comes from ``build_manifest(..., ctime=True)``. A recorded node
    may be missing: the deletion already removed it. Removing a child sets its
    directory's mtime and ctime, so a directory that lost a recorded child is
    compared by type and mode only; any other surviving node must equal its
    record exactly and have no ctime after ``changed_by``.
    """
    before = {item["path"]: item for item in recorded}
    after = {item["path"]: item for item in current}
    emptied = {_parent(path) for path in before.keys() - after.keys()}
    unexpected = []
    for path, item in after.items():
        node = {key: value for key, value in item.items() if key != "ctime_ns"}
        old = before.get(path)
        if old is None:
            unexpected.append(path)
        elif path in emptied and node["type"] == "directory":
            if node | {"mtime_ns": None} != old | {"mtime_ns": None}:
                unexpected.append(path)
        elif node != old or item["ctime_ns"] / 1e9 > changed_by:
            unexpected.append(path)
    return sorted(unexpected)
