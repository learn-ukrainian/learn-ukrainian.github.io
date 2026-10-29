"""Immutable-name generations behind the ``data/sources.db`` selector.

Layout: each published Sources store is one file under the real directory
``data/sources-generations/`` named ``sources.<utc>-<sha12>.db``; a name is
never reused. ``data/sources.db`` is a relative symlink, the selector, whose
text is exactly ``sources-generations/<name>``. SQLite resolves the link when it
opens the database and names the ``-wal``/``-shm`` sidecars after the
generation, so an opener that read the selector before a switch keeps a whole
old generation and can never pair it with another generation's sidecars.

Writers: one store-wide writer lock, ``data/.sources-writer.lock``, which is
never a generation file. A writer takes the lock, then resolves the selector,
and closes its connections before it releases the lock (``store_writer``).
The publisher holds the same lock from the moment it fingerprints the current
generation until the selector is switched, and refuses when the current
generation changed under it (``publish_generation``). A writable open of the
store without the lock is refused by ``scripts.lib.readonly_sqlite``.

Every function takes the selector path (``data/sources.db``) it works on. The
selector checks and ``live_store_path`` live in ``scripts.storage.topology`` (the
resolver); the lock bookkeeping the write guard reads lives in ``scripts.lib.readonly_sqlite``.

Retention: publication keeps every generation. Pruning is a separate,
operator-run command and is not part of this module.
"""

from __future__ import annotations

import contextlib
import contextvars
import fcntl
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import stat
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from scripts.lib.readonly_sqlite import (
    ENV_STORE_WRITER_FD,
    ENV_STORE_WRITER_SELECTOR,
    STORE_WRITER_LOCK_NAME,
    SQLiteConnection,
    inherited_store_writer,
    register_store_writer,
    unregister_store_writer,
    writable_store_refusal,
)
from scripts.storage.topology import (
    GENERATIONS_DIRNAME,
    SELECTOR_NAME,
    Layout,
    SelectorState,
    StoreKind,
    StoreRef,
    inspect_selector,
    is_generation_name,
    live_store_path,
    store_kind,
)
from scripts.storage.wal_permissions import get_companion_paths, hold_database, lift_database

__all__ = [
    "GENERATIONS_DIRNAME",
    "SELECTOR_NAME",
    "GenerationError",
    "HeldWriter",
    "Layout",
    "Publication",
    "SelectorState",
    "StoreKind",
    "StoreRef",
    "inspect_selector",
    "is_generation_name",
    "live_store_path",
    "one_generation",
    "publish_generation",
    "reader_pin",
    "store_kind",
    "store_writer",
    "writable_open_refusal",
    "writer_lock",
]

# The write guard in scripts.lib.readonly_sqlite owns the check; this is its name here.
writable_open_refusal = writable_store_refusal

WRITER_LOCK_NAME = STORE_WRITER_LOCK_NAME
RECEIPT_SUFFIX = ".receipt.json"
RECEIPT_SCHEMA = "sources-generation.receipt.v1"
# A process started by ``python -m scripts.storage write`` inherits the
# parent's locked descriptor and the selector it locked.
ENV_WRITER_FD = ENV_STORE_WRITER_FD
ENV_WRITER_SELECTOR = ENV_STORE_WRITER_SELECTOR

_WRITE_BITS = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

PublishMode = Literal["publish", "bootstrap", "restore"]


class GenerationError(RuntimeError):
    """A refused store operation. ``reason`` is a stable, path-free code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(f"{reason}: {detail}" if detail else reason)


def generation_name(sha256_hex: str, published_at: datetime) -> str:
    stamp = published_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"sources.{stamp}-{sha256_hex[:12]}.db"


def _wal_identity(generation: Path) -> tuple[int, int, int] | None:
    """An empty or absent WAL carries no frames, so both compare equal."""
    try:
        info = Path(f"{generation}-wal").lstat()
    except FileNotFoundError:
        return None
    if info.st_size == 0:
        return None
    return (info.st_ino, info.st_size, info.st_mtime_ns)


def fingerprint(generation: Path) -> tuple[Any, ...]:
    """Identity and content stamp of a generation and its WAL (the ``-shm`` index is excluded)."""
    info = generation.lstat()
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, _wal_identity(generation))


def is_held(generation: Path) -> bool:
    """True when the generation and every existing companion are read-only (0444-style)."""
    return all(not path.lstat().st_mode & _WRITE_BITS for path in (generation, *get_companion_paths(generation)))


@dataclass
class HeldWriter:
    """The store-wide writer lock, held by this process (or inherited from its parent)."""

    selector: Path
    layout: Layout
    generation: Path | None
    fingerprint: tuple[Any, ...] | None
    lifted: bool = False
    inherited: bool = False
    _fd: int = -1
    _connections: list[SQLiteConnection] = field(default_factory=list)
    _released: bool = False

    @property
    def data_dir(self) -> Path:
        return self.selector.parent

    @property
    def fd(self) -> int:
        """The locked descriptor; ``scripts.storage write`` passes it to its child."""
        return self._fd

    def track(self, connection: SQLiteConnection) -> None:
        """Close ``connection`` when the lock is released, if its owner has not."""
        self._connections.append(connection)


_held: dict[Path, HeldWriter] = {}
_held_lock = threading.Lock()


def _key(directory: Path) -> Path:
    return Path(os.path.realpath(directory))


def _lock_path(directory: Path) -> Path:
    return directory / WRITER_LOCK_NAME


def _open_lock(directory: Path) -> int:
    fd = os.open(_lock_path(directory), os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise GenerationError("writer_lock_not_regular_file")
    return fd


def _current(directory: Path) -> HeldWriter | None:
    with _held_lock:
        held = _held.get(_key(directory))
    if held is not None:
        return held
    inherited = inherited_store_writer(directory)
    if inherited is None:
        return None
    fd, selector = inherited
    state = inspect_selector(selector)
    if state.layout not in ("selector", "legacy_file"):
        return None
    return HeldWriter(selector, state.layout, state.generation, None, inherited=True, _fd=fd)  # type: ignore[arg-type]


@contextlib.contextmanager
def writer_lock(
    selector: Path,
    *,
    lift: bool = False,
    allow_missing: bool = False,
) -> Iterator[HeldWriter]:
    """Hold the store-wide writer lock; resolve the selector only after it is held.

    The lock is never waited for: a busy lock is the refusal ``writer_lock_busy``.
    ``lift`` makes a held (read-only) generation writable for this holder and
    holds it again on release. Connections passed to ``HeldWriter.track`` are
    closed before the lock is released.
    """
    selector = Path(os.path.abspath(selector))
    if selector.name != SELECTOR_NAME:
        # The lock binds the canonical selector; another link in the directory never carries it.
        raise GenerationError("selector_not_canonical")
    directory = selector.parent
    key = _key(directory)
    with _held_lock:
        if key in _held:
            raise GenerationError("writer_lock_busy", "already held by this process")
    inherited = inherited_store_writer(directory)
    fd = inherited[0] if inherited is not None else _open_lock(directory)
    try:
        if inherited is None:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise GenerationError("writer_lock_busy") from None
        state = inspect_selector(selector)
        if state.layout == "invalid" or (state.layout == "missing" and not allow_missing):
            raise GenerationError(state.reason)
        generation = state.generation
        held = HeldWriter(
            selector,
            state.layout,  # type: ignore[arg-type]
            generation,
            None if generation is None else fingerprint(generation),
            inherited=inherited is not None,
            _fd=fd,
        )
        if lift and generation is not None and inherited is None and is_held(generation):
            lift_database(generation)
            held.lifted = True
        with _held_lock:
            _held[key] = held
            register_store_writer(selector)
        try:
            yield held
        finally:
            with _held_lock:
                _held.pop(key, None)
                unregister_store_writer(selector)
            held._released = True
            errors: list[Exception] = []
            for connection in held._connections:
                try:
                    connection.close()
                except sqlite3.Error as error:
                    errors.append(error)
            if held.lifted and held.generation is not None:
                try:
                    hold_database(held.generation, strict=False)
                except OSError as error:
                    errors.append(error)
            if errors:
                raise ExceptionGroup("writer lock release", errors)
    finally:
        if inherited is None:
            os.close(fd)


@contextlib.contextmanager
def store_writer(path: str | os.PathLike[str]) -> Iterator[Path]:
    """Yield the file a writer may open for ``path``, under the writer lock when it is the store.

    The store (selector or pre-bootstrap live file) is resolved after the lock
    is held, and its held generation is lifted for the duration. Any other path
    (a fixture, a staged copy) is yielded unchanged with no lock. Naming a
    generation file directly is refused: a writer must go through the selector.
    """
    ref = store_kind(path)
    if ref.kind == "other":
        yield Path(path)
        return
    if ref.kind == "generation" or ref.selector is None or ref.lock_dir is None:
        raise GenerationError("generation_named_directly", "open the selector data/sources.db instead")
    current = _current(ref.lock_dir)
    if current is not None and current.inherited:
        if current.generation is None:
            raise GenerationError("selector_missing")
        yield current.generation
        return
    with writer_lock(ref.selector, lift=True) as held:
        assert held.generation is not None
        yield held.generation


def track_connection(path: str | os.PathLike[str], connection: SQLiteConnection) -> None:
    """Register a writable store connection so the lock's release closes it."""
    ref = store_kind(path)
    if ref.kind == "other" or ref.lock_dir is None:
        return
    held = _current(ref.lock_dir)
    if held is not None and not held.inherited:
        held.track(connection)


@dataclass
class ReaderPin:
    """One Sources generation for one lookup or request.

    Shared by every thread of the lookup and by both import names of
    ``scripts.wiki.sources_db`` (each has its own connection cache): the first
    reader fixes ``generation``, and every later one gets a connection to it.
    """

    generation: Path | None = None
    readers: dict[str, Any] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock)


_reader_pin: contextvars.ContextVar[ReaderPin | None] = contextvars.ContextVar("sources_reader_pin", default=None)


@contextlib.contextmanager
def one_generation() -> Iterator[None]:
    """Read one generation throughout this block; a nested block keeps the outer pin.

    The pin is filled at the first read, so a missing store still fails there.
    Worker threads see it when they run in a copy of this context.
    """
    if _reader_pin.get() is not None:
        yield
        return
    token = _reader_pin.set(ReaderPin())
    try:
        yield
    finally:
        _reader_pin.reset(token)


def reader_pin() -> ReaderPin | None:
    return _reader_pin.get()


def required_free_bytes(generation_bytes: int) -> int:
    """A generation, plus the evidence readers' free-disk floor, plus room for a full WAL."""
    from scripts.curriculum.evidence.config import free_disk_floor_bytes, wal_ceiling_bytes

    return generation_bytes + free_disk_floor_bytes() + wal_ceiling_bytes()


def require_free_space(directory: Path, generation_bytes: int) -> None:
    needed = required_free_bytes(generation_bytes)
    free = shutil.disk_usage(directory).free
    if free < needed:
        raise GenerationError("insufficient_free_space", f"{free} bytes free, {needed} required")


def _fsync_path(path: Path, *, directory: bool = False) -> None:
    flags = os.O_RDONLY | (os.O_DIRECTORY if directory else 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def receipt_path(generation: Path) -> Path:
    return generation.with_name(generation.name + RECEIPT_SUFFIX)


def read_receipt(generation: Path) -> dict[str, Any] | None:
    try:
        return json.loads(receipt_path(generation).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def _write_receipt(generation: Path, payload: dict[str, Any]) -> None:
    target = receipt_path(generation)
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(4)}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)
    _fsync_path(target.parent, directory=True)


def _complete_receipt(generation: Path) -> None:
    """The selector switch is the commit point: a selected ``staged`` receipt is published."""
    receipt = read_receipt(generation)
    if receipt is not None and receipt.get("state") != "published":
        _write_receipt(generation, {**receipt, "state": "published"})


def _ensure_generations_dir(selector: Path) -> Path:
    directory = selector.parent / GENERATIONS_DIRNAME
    try:
        directory.mkdir(mode=0o755)
        _fsync_path(selector.parent, directory=True)
    except FileExistsError:
        pass
    if not stat.S_ISDIR(directory.lstat().st_mode):
        raise GenerationError("generations_dir_not_real_directory")
    return directory


def _header_journal_mode(path: Path) -> str | None:
    """Bytes 18-19 of the SQLite header: 2,2 is WAL."""
    with path.open("rb") as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return None
    return "wal" if header[18] == 2 and header[19] == 2 else "other"


def _declare_wal(candidate: Path) -> None:
    """Generations stay in WAL; the last connection's close leaves no sidecars behind."""
    connection = sqlite3.connect(candidate.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
    try:
        mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()
    if mode != "wal":
        raise GenerationError("candidate_not_wal", f"journal_mode={mode}")


def _switch_selector(selector: Path, name: str) -> None:
    temporary = selector.parent / f".{selector.name}.{secrets.token_hex(6)}.link"
    os.symlink(f"{GENERATIONS_DIRNAME}/{name}", temporary)
    try:
        os.replace(temporary, selector)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
        raise
    _fsync_path(selector.parent, directory=True)


@dataclass(frozen=True)
class Publication:
    generation: Path
    previous: Path | None
    sha256: str
    mode: PublishMode


def publish_generation(
    candidate: Path,
    held: HeldWriter,
    *,
    mode: PublishMode = "publish",
    now: datetime | None = None,
) -> Publication:
    """Make ``candidate`` the selected generation, or refuse with ``GenerationError``.

    ``publish``: ``candidate`` is a complete, closed SQLite file on the store's
    filesystem, built from the current generation while ``held`` was held. It is
    linked into the generation directory under a new name and the staging name
    is removed. ``bootstrap``: the selector is still the legacy regular file,
    which becomes the first generation (maintenance window only). ``restore``:
    ``candidate`` is an existing generation file, restored under its own name.

    Order: refuse on a changed or writable current generation and on low disk;
    fsync the generation and its directory; write a ``staged`` receipt; replace
    the selector with a temporary link through ``os.replace`` and fsync the data
    directory (the commit point); mark the receipt ``published``.
    """
    selector = held.selector
    with _held_lock:
        owns = _held.get(_key(held.data_dir)) is held
    if not owns or held._released or held.inherited:
        raise GenerationError("writer_lock_not_held")
    if held.lifted:
        raise GenerationError("publisher_lifted_generation")
    state = inspect_selector(selector)
    if state.layout == "invalid":
        raise GenerationError(state.reason)
    allowed = {"publish": ("selector",), "bootstrap": ("legacy_file",), "restore": ("selector", "missing")}[mode]
    if state.layout not in allowed:
        raise GenerationError("selector_is_regular_file" if state.layout == "legacy_file" else state.reason)
    previous = state.generation
    if previous is not None:
        if previous != held.generation or fingerprint(previous) != held.fingerprint:
            raise GenerationError("current_generation_changed")
        if not is_held(previous):
            raise GenerationError("current_generation_writable")
        if state.layout == "selector":
            _complete_receipt(previous)

    candidate = Path(os.path.abspath(candidate))
    info = candidate.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise GenerationError("candidate_not_regular_file")
    if info.st_dev != held.data_dir.stat().st_dev:
        raise GenerationError("candidate_on_other_filesystem")
    directory = _ensure_generations_dir(selector)
    if mode == "bootstrap":
        if candidate != selector:
            raise GenerationError("bootstrap_candidate_not_selector")
        if _wal_identity(candidate) is not None:
            raise GenerationError("legacy_wal_not_empty")
    elif mode == "restore":
        if candidate.parent != directory or not is_generation_name(candidate.name):
            raise GenerationError("restore_candidate_not_generation")
    else:
        if candidate.parent == directory or candidate == selector:
            raise GenerationError("candidate_is_store_file")
        if _wal_identity(candidate) is not None:
            raise GenerationError("candidate_has_wal")
        journal = _header_journal_mode(candidate)
        if journal is None:
            raise GenerationError("candidate_not_sqlite")
        if journal != "wal":
            # A retry finds the candidate already in WAL and held read-only.
            _declare_wal(candidate)
    if _header_journal_mode(candidate) != "wal":
        raise GenerationError("candidate_not_wal")
    require_free_space(held.data_dir, candidate.stat().st_size)

    stamp = (now or datetime.now(UTC)).astimezone(UTC)
    digest = _sha256(candidate)
    if mode == "restore":
        generation = candidate
        hold_database(generation, strict=False)
    else:
        generation = directory / generation_name(digest, stamp)
        if mode == "publish":
            hold_database(candidate)
        try:
            os.link(candidate, generation)
        except FileExistsError:
            # A retry after a failure past this point finds its own staged link.
            if not os.path.samefile(candidate, generation):
                raise GenerationError("generation_name_taken") from None
    _fsync_path(generation)
    _fsync_path(directory, directory=True)
    receipt = read_receipt(generation) or {}
    _write_receipt(
        generation,
        {
            **receipt,
            "schema": RECEIPT_SCHEMA,
            "generation": generation.name,
            "previous": None if previous is None or mode == "bootstrap" else previous.name,
            "sha256": receipt.get("sha256", digest),
            "size_bytes": generation.stat().st_size,
            "published_at": receipt.get("published_at", stamp.strftime("%Y-%m-%dT%H:%M:%SZ")),
            "mode": mode,
            "state": "staged",
        },
    )
    _switch_selector(selector, generation.name)
    if mode == "publish":
        candidate.unlink()
    elif mode == "bootstrap":
        # New openers resolve the link and use the generation's sidecar names;
        # the legacy names are empty (checked above) and no longer reachable.
        for suffix in ("-wal", "-shm"):
            with contextlib.suppress(FileNotFoundError):
                Path(f"{selector}{suffix}").unlink()
    _complete_receipt(generation)
    held.generation = generation
    held.fingerprint = fingerprint(generation)
    held.layout = "selector"
    return Publication(generation, None if mode == "bootstrap" else previous, digest, mode)


def checkpoint_legacy_store(held: HeldWriter) -> None:
    """Fold the pre-bootstrap file's WAL into it; refuse while any other connection has it open.

    SQLite deletes the WAL and the shared-memory index when the last connection
    in WAL mode closes. A sidecar still present after this connection closes
    therefore means another process still has the store open, idle or not.
    """
    if held.layout != "legacy_file" or held.generation is None or held.lifted:
        raise GenerationError("bootstrap_requires_legacy_file")
    was_held = is_held(held.generation)
    if was_held:
        lift_database(held.generation)
    try:
        connection = sqlite3.connect(held.generation.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
        try:
            busy, _, _ = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        finally:
            connection.close()
    finally:
        if was_held:
            hold_database(held.generation, strict=False)
    if busy:
        raise GenerationError("store_in_use", "a reader or writer is still connected")
    if any(Path(f"{held.generation}{suffix}").exists() for suffix in ("-wal", "-shm")):
        raise GenerationError("store_in_use", "another connection still has the store open")
    held.fingerprint = fingerprint(held.generation)


def generation_status(selector: Path) -> dict[str, Any]:
    """Read-only summary for operators: selector state, selected generation, retained files."""
    state = inspect_selector(selector)
    directory = selector.parent / GENERATIONS_DIRNAME
    retained: list[dict[str, Any]] = []
    if directory.is_dir() and not directory.is_symlink():
        for path in sorted(directory.iterdir()):
            if is_generation_name(path.name):
                receipt = read_receipt(path) or {}
                retained.append(
                    {
                        "name": path.name,
                        "size_bytes": path.lstat().st_size,
                        "selected": state.generation is not None and path == state.generation,
                        "receipt_state": receipt.get("state"),
                        "previous": receipt.get("previous"),
                    }
                )
    return {
        "layout": state.layout,
        "reason": state.reason,
        "selected": None if state.generation is None else state.generation.name,
        "held": None if state.generation is None else is_held(state.generation),
        "generations": retained,
    }
