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

Every function takes the selector path (``data/sources.db``) it works on; only
``live_store_path`` names the primary checkout's store, through the sanctioned
resolver in ``scripts.storage.topology``.

Retention: publication keeps every generation. Pruning is a separate,
operator-run command and is not part of this module.
"""

from __future__ import annotations

import contextlib
import fcntl
import functools
import hashlib
import json
import os
import re
import secrets
import shutil
import sqlite3
import stat
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from scripts.common.repo_root import main_checkout_root
from scripts.lib.readonly_sqlite import SQLiteConnection
from scripts.storage.wal_permissions import get_companion_paths, hold_database, lift_database

GENERATIONS_DIRNAME = "sources-generations"
SELECTOR_NAME = "sources.db"
WRITER_LOCK_NAME = ".sources-writer.lock"
RECEIPT_SUFFIX = ".receipt.json"
RECEIPT_SCHEMA = "sources-generation.receipt.v1"
# A process started by ``python -m scripts.storage write`` inherits the
# parent's locked descriptor and the selector it locked.
ENV_WRITER_FD = "LU_SOURCES_WRITER_FD"
ENV_WRITER_SELECTOR = "LU_SOURCES_WRITER_SELECTOR"

_GENERATION_NAME = re.compile(r"sources\.\d{8}T\d{6}Z-[0-9a-f]{12}\.db")
_REPO_ROOT = Path(__file__).resolve().parents[2]
_WRITE_BITS = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

StoreKind = Literal["selector", "generation", "legacy_live", "other"]
Layout = Literal["selector", "legacy_file", "missing"]
PublishMode = Literal["publish", "bootstrap", "restore"]


class GenerationError(RuntimeError):
    """A refused store operation. ``reason`` is a stable, path-free code."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(f"{reason}: {detail}" if detail else reason)


def is_generation_name(name: str) -> bool:
    return bool(_GENERATION_NAME.fullmatch(name))


def generation_name(sha256_hex: str, published_at: datetime) -> str:
    stamp = published_at.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"sources.{stamp}-{sha256_hex[:12]}.db"


@dataclass(frozen=True)
class SelectorState:
    """What a selector path is right now; ``generation`` is the file it selects."""

    layout: Layout | Literal["invalid"]
    reason: str
    generation: Path | None = None


def inspect_selector(selector: Path) -> SelectorState:
    """Classify the selector without following anything outside the generation directory."""
    try:
        info = selector.lstat()
    except FileNotFoundError:
        return SelectorState("missing", "selector_missing")
    if stat.S_ISREG(info.st_mode):
        return SelectorState("legacy_file", "regular_file", selector)
    if not stat.S_ISLNK(info.st_mode):
        return SelectorState("invalid", "selector_not_file_or_link")
    parts = PurePosixPath(os.readlink(selector)).parts
    if len(parts) != 2 or parts[0] != GENERATIONS_DIRNAME or not is_generation_name(parts[1]):
        return SelectorState("invalid", "selector_target_outside_generations")
    directory = selector.parent / GENERATIONS_DIRNAME
    try:
        if not stat.S_ISDIR(directory.lstat().st_mode):
            return SelectorState("invalid", "generations_dir_not_real_directory")
        target_info = (directory / parts[1]).lstat()
    except FileNotFoundError:
        return SelectorState("invalid", "selected_generation_missing")
    if not stat.S_ISREG(target_info.st_mode):
        return SelectorState("invalid", "selected_generation_not_regular_file")
    return SelectorState("selector", "selector", directory / parts[1])


@functools.cache
def live_store_path() -> Path:
    """The primary checkout's store path (selector, or the regular file before the bootstrap)."""
    from scripts.storage.topology import resolve_active_sources_db

    return resolve_active_sources_db(main_checkout_root(_REPO_ROOT), env={}).path


@dataclass(frozen=True)
class StoreRef:
    """Whether a path names the Sources store; ``lock_dir`` holds its writer lock."""

    kind: StoreKind
    selector: Path | None = None
    lock_dir: Path | None = None


def store_kind(path: str | os.PathLike[str]) -> StoreRef:
    """Say whether ``path`` names the Sources store.

    A selector is a link named ``sources.db`` whose text starts with the
    generation directory. A generation is any path that resolves into a
    generation directory (a differently named link to one included). Before the
    bootstrap the store is the primary checkout's regular ``data/sources.db``.
    Every other path (fixtures, staged copies, temporary builds) is ``other``.
    """
    raw = Path(os.path.abspath(os.fspath(path)))
    try:
        if raw.name == SELECTOR_NAME and raw.is_symlink():
            parts = PurePosixPath(os.readlink(raw)).parts
            if parts and parts[0] == GENERATIONS_DIRNAME:
                return StoreRef("selector", raw, raw.parent)
        resolved = raw.resolve()
    except (OSError, RuntimeError, ValueError):
        return StoreRef("other")
    if resolved.parent.name == GENERATIONS_DIRNAME and is_generation_name(resolved.name):
        return StoreRef("generation", None, resolved.parent.parent)
    try:
        live = live_store_path()
        if resolved == live.resolve() and live.is_file() and not live.is_symlink():
            return StoreRef("legacy_live", live, live.parent)
    except (OSError, RuntimeError, ValueError):
        return StoreRef("other")
    return StoreRef("other")


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


def _inherited(directory: Path) -> tuple[int, Path] | None:
    """The descriptor and selector a ``scripts.storage write`` parent passed down for this store."""
    raw_fd = os.environ.get(ENV_WRITER_FD)
    raw_selector = os.environ.get(ENV_WRITER_SELECTOR)
    if raw_fd is None or raw_selector is None:
        return None
    selector = Path(raw_selector)
    if not selector.is_absolute() or _key(selector.parent) != _key(directory):
        return None
    try:
        fd = int(raw_fd)
        held = os.fstat(fd)
        expected = _lock_path(directory).lstat()
    except (ValueError, OSError):
        return None
    if (held.st_dev, held.st_ino) != (expected.st_dev, expected.st_ino):
        return None
    try:
        # The parent's open file description already holds LOCK_EX; taking it
        # again through the same description succeeds, any other holder fails.
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return None
    return fd, selector


def _current(directory: Path) -> HeldWriter | None:
    with _held_lock:
        held = _held.get(_key(directory))
    if held is not None:
        return held
    inherited = _inherited(directory)
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
    directory = selector.parent
    key = _key(directory)
    with _held_lock:
        if key in _held:
            raise GenerationError("writer_lock_busy", "already held by this process")
    inherited = _inherited(directory)
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
        try:
            yield held
        finally:
            with _held_lock:
                _held.pop(key, None)
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


def writable_open_refusal(database: str | os.PathLike[str]) -> str | None:
    """``None`` when ``database`` may be opened writable here, else a path-free reason.

    Paths that are not the store are always allowed by this check. The store
    needs this process to hold the writer lock (or to have inherited it), and
    the path must resolve to the generation the selector selects now.
    """
    ref = store_kind(database)
    if ref.kind == "other":
        return None
    if ref.lock_dir is None:
        return "store_unavailable"
    held = _current(ref.lock_dir)
    if held is None:
        return "writer_lock_not_held"
    state = inspect_selector(held.selector)
    if state.generation is None:
        return state.reason
    try:
        target = Path(os.fspath(database)).resolve()
    except (OSError, RuntimeError, ValueError):
        return "store_unavailable"
    if target != state.generation.resolve():
        return "not_selected_generation"
    return None


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
    """Fold the pre-bootstrap file's WAL into it; refuse while another connection reads it."""
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
