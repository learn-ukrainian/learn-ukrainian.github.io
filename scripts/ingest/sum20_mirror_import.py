#!/usr/bin/env python3
"""Import the staged СУМ-20 mirror into a new, verified ``sources.db`` generation (#8579).

``build`` takes the frozen staging bytes and a copy of the live
``data/sources.db``. It imports every staged slovnyk.me ``newsum`` article into
the copy's ``sum20_mirror_*`` tables (``scripts.wiki.sum20_mirror``), verifies
the copy and seals it as a candidate generation. ``publish`` swaps a candidate
in atomically and keeps the previous generation in ``data/sources/backups/``
as a hard link of its unchanged inode. ``restore`` brings a retained generation
back the same way. The official ``sum20_*`` tables, their quarantine marks and
the crawl tables are never written; verification proves them unchanged.

**Exclusion.** The live store must be held (``scripts.storage hold``: no write
bit on the file or its sidecars). Kernel file leases are the proof; the
``/proc`` scan and lock table only explain a refusal and pace the wait.

- ``build`` takes a read lease on the live file and its sidecars. Linux grants
  one only when no process, of any user and whether or not ``/proc`` can list
  it, holds a writable descriptor. The scan's unknown descriptors and write
  locks refuse too.
- A publication holds write leases, granted only when no other descriptor
  exists at all, from the barrier to the rename. It waits up to
  ``--wait-drained`` seconds for other users to close, then stops the
  ``--drain-unit`` units. It also requires the live file to be identical to the
  one the candidate was copied from, with an empty WAL.

**Publication.** A journal is written before the previous generation is
retained as a durable hard link. The old inode is then fenced at mode 000, so a
new open fails. An open that began earlier breaks a lease and refuses the
publication. Only then comes the rename. Every command first finishes or undoes a publication a crash
interrupted. Units are started again whatever happens, and a failure to
restart one is reported apart from the committed swap.

The writer runs only from the primary checkout on a local filesystem, under an
exclusive non-blocking lock. It makes no network request.

Examples:
  .venv/bin/python -m scripts.ingest.sum20_mirror_import plan
  .venv/bin/python -m scripts.ingest.sum20_mirror_import build --expect-staging-sha256 <sha256>
  .venv/bin/python -m scripts.ingest.sum20_mirror_import publish --generation <id> \\
      --drain-unit learn-ukrainian-sources.service --wait-drained 900
  .venv/bin/python -m scripts.ingest.sum20_mirror_import restore --generation <id> \\
      --drain-unit learn-ukrainian-sources.service --wait-drained 900
  .venv/bin/python -m scripts.ingest.sum20_mirror_import generations

Outputs: one JSON object on stdout; candidates, backups and receipts under
``data/sources/``.
Exit codes: 0 success; 1 verification failed (live store untouched);
2 refused (arguments, locality, lock, staging, hold, holders, barrier, unit stop);
3 published or restored, but a drained unit failed to start again.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterator, Sequence
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.repo_root import main_checkout_root
from scripts.lexicon import reconcile_sum20
from scripts.lib.readonly_sqlite import SQLiteConnection, open_readonly
from scripts.storage import topology
from scripts.wiki import sum20_mirror
from scripts.wiki.sum20_official import live_article_predicate, normalize_sum20_lookup

STAGING_NAME = "sum20_slovnyk_staging.db"
WORK_DIR = "sources"
OFFICIAL_TABLES = (
    ("sum20_articles", "id"),
    ("sum20_senses", "id"),
    ("sum20_citations", "id"),
    ("sum20_crawl_checkpoint", "singleton"),
    ("sum20_crawl_outcomes", "wordid"),
)
SAMPLE_PER_RELATION = 5
BATCH_ROWS = 5000
DISK_RESERVE_BYTES = 10 * 1024**3
CHUNK = 8 * 1024 * 1024
DRAIN_POLL_S = 5.0
SYSTEMCTL_TIMEOUT_S = 120


class Refused(RuntimeError):
    """Stopped before the live store was touched; ``reason`` is path-free."""

    def __init__(self, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


class VerificationFailed(RuntimeError):
    """The new generation failed a check; the live store was not touched."""

    def __init__(self, reason: str, **detail: Any) -> None:
        super().__init__(reason)
        self.detail = detail


@dataclass(frozen=True)
class Target:
    data_dir: Path
    root: Path
    live: Path

    @property
    def staging(self) -> Path:
        return self.data_dir / STAGING_NAME

    @property
    def work_dir(self) -> Path:
        return self.data_dir / WORK_DIR

    @property
    def candidates_dir(self) -> Path:
        return self.work_dir / "candidates"

    @property
    def backups_dir(self) -> Path:
        return self.work_dir / "backups"

    @property
    def receipts_dir(self) -> Path:
        return self.work_dir / "receipts"

    @property
    def lock_path(self) -> Path:
        return self.work_dir / ".build.lock"

    def candidate(self, generation: str) -> Path:
        return self.candidates_dir / f"sources.{generation}.db"

    def backup(self, generation: str) -> Path:
        return self.backups_dir / f"sources.{generation}.db"

    def receipt(self, generation: str) -> Path:
        return self.receipts_dir / f"{generation}.json"

    def temp(self, label: str) -> Path:
        return self.work_dir / f"sources.{label}.db.tmp"


def writer_target(repository_root: Path | None = None, *, test_data_dir: Path | None = None) -> Target:
    """The primary checkout's ``data/``, or an explicit test directory.

    Like the lexdata writer it refuses a linked worktree, symlinked store paths
    and a network or unknown filesystem.
    """
    if test_data_dir is not None:
        data_dir, root = test_data_dir, test_data_dir.parent
    else:
        root = topology.default_repository_root(repository_root).resolve()
        primary = main_checkout_root(root).resolve()
        if root != primary:
            raise Refused("linked_worktree")
        data_dir = primary / "data"
    if data_dir.is_symlink():
        raise Refused("symlinked_path")
    if not data_dir.is_dir():
        raise Refused("data_dir_missing")
    # The canonical file of this root, never an environment override: the writer
    # replaces exactly the store the resolver serves by default.
    resolved = topology.resolve_store("sources", root, env={})
    if isinstance(resolved, topology.StoreRefusal):
        raise Refused(f"live_{resolved.reason}")
    live = resolved.path
    if live.is_symlink() or live.parent != data_dir.resolve():
        raise Refused("symlinked_path")
    target = Target(data_dir.resolve(), root, live)
    for path in (target.work_dir, target.candidates_dir, target.backups_dir, target.receipts_dir):
        if path.is_symlink():
            raise Refused("symlinked_path")
    locality = topology.store_locality(target.data_dir)
    if locality != "local":
        raise Refused(f"locality_{locality}")
    return target


@contextmanager
def build_lock(target: Target) -> Iterator[None]:
    """Exclusive non-blocking ``flock``: a second writer is refused, never queued."""
    target.work_dir.mkdir(exist_ok=True)
    fd = os.open(target.lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refused("build_locked") from None
        yield
    finally:
        os.close(fd)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def generation_id(sha256: str) -> str:
    """Generations are content-addressed: equal bytes are the same generation."""
    return sha256[:16]


def _fsync(path: Path, *, directory: bool = False) -> None:
    fd = os.open(path, os.O_RDONLY | (os.O_DIRECTORY if directory else 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sidecars(path: Path) -> list[Path]:
    return [Path(f"{path}{suffix}") for suffix in ("-wal", "-shm", "-journal")]


def _remove(paths: Sequence[Path]) -> None:
    for path in paths:
        if path.exists() or path.is_symlink():
            path.unlink()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _fsync(temp)
    temp.replace(path)
    _fsync(path.parent, directory=True)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


# --- the live store: identity, hold and holders --------------------------------------------------------


def live_identity(path: Path) -> dict[str, int]:
    """File identity, mode and journal state; any change between copy and swap refuses the swap."""
    info = path.stat()
    wal = Path(f"{path}-wal")
    return {
        "dev": info.st_dev,
        "ino": info.st_ino,
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "mode": stat.S_IMODE(info.st_mode),
        "wal_bytes": wal.stat().st_size if wal.exists() else 0,
        "journal": int(Path(f"{path}-journal").exists()),
    }


def _require_held(path: Path) -> None:
    """The file and every existing sidecar carry no write bit: no new writer can open them."""
    for part in [path, *_sidecars(path)]:
        if part.exists() and stat.S_IMODE(part.stat().st_mode) & 0o222:
            raise Refused("live_store_not_held")


def _require_quiet(identity: dict[str, int]) -> None:
    """An empty WAL and no rollback journal: the main file holds every committed page."""
    if identity["wal_bytes"] or identity["journal"]:
        raise Refused("live_store_not_checkpointed")


def holders(paths: Sequence[Path], proc: Path = Path("/proc")) -> dict[str, Any]:
    """Every observable use of ``paths`` (matched by inode), for the exclusion checks.

    - ``holders``: processes with a descriptor on a path; ``writable`` is ``None``
      when the descriptor's access mode cannot be read, and counts as unknown.
    - ``locks``: POSIX locks on a path from ``/proc/locks``. That table covers every
      process, including those whose descriptors cannot be listed, and SQLite
      holds such locks for each connection that has read the database.
    - ``unscannable``: live processes whose descriptor table cannot be listed.
      Exited processes are skipped; this process is excluded.
    """
    inodes: dict[tuple[int, int], str] = {}
    for path in paths:
        try:
            info = path.stat()
        except FileNotFoundError:
            continue
        inodes[(info.st_dev, info.st_ino)] = path.name
    found: dict[int, dict[str, Any]] = {}
    unscannable: list[dict[str, Any]] = []
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            descriptors = list((entry / "fd").iterdir())
        except PermissionError:
            unscannable.append({"pid": int(entry.name), "command": _comm(proc, int(entry.name))})
            continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        blind = False
        for descriptor in descriptors:
            try:
                info = descriptor.stat()
            except FileNotFoundError:
                continue  # closed between listing and reading
            except OSError:
                blind = True  # an open file this scan cannot identify
                continue
            name = inodes.get((info.st_dev, info.st_ino))
            if name is None:
                continue
            holder = found.setdefault(int(entry.name), {"pid": int(entry.name), "writable": False, "files": []})
            try:
                flags = next(
                    int(line.split()[1], 8)
                    for line in (entry / "fdinfo" / descriptor.name).read_text().splitlines()
                    if line.startswith("flags:")
                )
                writable: bool | None = (flags & os.O_ACCMODE) != os.O_RDONLY
            except FileNotFoundError:
                continue
            except (OSError, StopIteration, ValueError):
                writable = None
            if holder["writable"] is not True:  # unknown stays unknown unless a writer is proven
                holder["writable"] = (
                    True if writable else None if writable is None or holder["writable"] is None else False
                )
            if name not in holder["files"]:
                holder["files"].append(name)
        if blind:
            unscannable.append({"pid": int(entry.name), "command": _comm(proc, int(entry.name))})
    for pid, holder in found.items():
        holder["command"] = _comm(proc, pid)
    return {
        "holders": sorted(found.values(), key=lambda h: h["pid"]),
        "locks": _locks(inodes, proc / "locks"),
        "unscannable": sorted(unscannable, key=lambda h: h["pid"]),
    }


def _comm(proc: Path, pid: int) -> str:
    try:
        return (proc / str(pid) / "comm").read_text().strip()
    except OSError:
        return ""


def _locks(inodes: dict[tuple[int, int], str], table: Path) -> list[dict[str, Any]] | None:
    """Kernel lock-table entries on ``inodes``; ``None`` when the table cannot be read (unknown, not empty).

    ``major:minor:inode`` is the hexadecimal device and the decimal inode.
    """
    wanted = {(os.major(dev), os.minor(dev), ino): name for (dev, ino), name in inodes.items()}
    found = []
    try:
        lines = table.read_text().splitlines()
    except OSError:
        return None
    for line in lines:
        fields = line.split()
        try:
            at = next(i for i, field in enumerate(fields) if field.count(":") == 2)
            major, minor, ino = fields[at].split(":")
            key = (int(major, 16), int(minor, 16), int(ino))
        except (StopIteration, ValueError):
            continue
        if key in wanted:
            found.append(
                {
                    "pid": int(fields[at - 1]) if fields[at - 1].isdigit() else None,
                    "access": fields[at - 2],
                    "file": wanted[key],
                }
            )
    return found


def _live_files(target: Target) -> list[Path]:
    return [target.live, *_sidecars(target.live)]


@contextmanager
def leases(paths: Sequence[Path], kind: int, diagnose: Callable[[], dict[str, Any]]) -> Iterator[Callable[[], bool]]:
    """Kernel file leases on every existing path: the exclusion proof, across all users and processes.

    Linux grants ``F_WRLCK`` only when no other descriptor for the file exists
    anywhere, and ``F_RDLCK`` only when none is open for writing, including in
    processes ``/proc`` cannot list. While a lease is held, another open blocks
    and breaks it (``SIGIO``); the yielded check is false once any lease broke.
    Refusals carry ``diagnose()``, the ``/proc`` view of who holds the store.
    """
    broken: list[int] = []
    previous = signal.signal(signal.SIGIO, lambda signum, frame: broken.append(signum))
    fds: list[int] = []
    try:
        for path in paths:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            except FileNotFoundError:
                continue
            fds.append(fd)
            try:
                fcntl.fcntl(fd, fcntl.F_SETLEASE, kind)
            except BlockingIOError:
                raise Refused("live_store_in_use", lease=path.name, **diagnose()) from None
            except OSError as exc:
                raise Refused(f"lease_unavailable_{errno.errorcode.get(exc.errno, exc.errno)}") from None
        yield lambda: not broken and all(fcntl.fcntl(fd, fcntl.F_GETLEASE) == kind for fd in fds)
    finally:
        for fd in fds:
            with contextlib.suppress(OSError):
                fcntl.fcntl(fd, fcntl.F_SETLEASE, fcntl.F_UNLCK)
            os.close(fd)
        signal.signal(signal.SIGIO, previous)


def _require_no_writers(target: Target, scan: Callable[[Sequence[Path]], dict[str, Any]]) -> None:
    """No writable descriptor on the live files anywhere: a read lease proves it; the scan explains refusals."""
    observed = scan(_live_files(target))
    writers = [h for h in observed["holders"] if h["writable"] is not False]
    locks = observed["locks"]
    if writers or locks is None or any(lock["access"] == "WRITE" for lock in locks):
        raise Refused("live_store_has_writers", holders=writers, locks=locks)
    with leases(_live_files(target), fcntl.F_RDLCK, lambda: _undrained(observed, lambda holder: False)):
        pass


def _undrained(observed: dict[str, Any], allowed: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
    """What still uses the live store, apart from processes of the units about to be drained.

    ``locks`` is ``None`` when the lock table could not be read, which counts as in use.
    """
    locks = observed["locks"]
    return {
        "holders": [h for h in observed["holders"] if not allowed(h)],
        "locks": None if locks is None else [lock for lock in locks if lock["pid"] is None or not allowed(lock)],
    }


# --- staging ---------------------------------------------------------------------------------------------


def _staging_identity(path: Path) -> tuple:
    info = path.stat()
    wal = Path(f"{path}-wal")
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        wal.stat().st_size if wal.exists() else 0,
        Path(f"{path}-journal").exists(),
    )


def snapshot_staging(target: Target, expect_sha256: str) -> tuple[Path, str]:
    """Copy the staging main file while hashing it, so the imported bytes are the admitted bytes.

    A WAL holding frames, a rollback journal, or any change during the copy
    refuses: committed content outside the main file would escape the digest.
    The snapshot is read only with ``immutable=1``.
    """
    resolved = topology.resolve_store("sources", target.root, binding=topology.StoreBinding("sources", target.staging))
    if isinstance(resolved, topology.StoreRefusal):
        raise Refused(f"staging_{resolved.reason}")
    before = _staging_identity(resolved.path)
    if before[4] or before[5]:
        raise Refused("staging_not_checkpointed")
    snapshot = target.work_dir / f"staging.{os.getpid()}.snapshot.db"
    digest = hashlib.sha256()
    with resolved.path.open("rb") as source, snapshot.open("wb") as copy:
        while chunk := source.read(CHUNK):
            digest.update(chunk)
            copy.write(chunk)
        copy.flush()
        os.fsync(copy.fileno())
    if _staging_identity(resolved.path) != before:
        _remove([snapshot])
        raise Refused("staging_changed_during_snapshot")
    if digest.hexdigest() != expect_sha256.lower():
        _remove([snapshot])
        raise Refused("staging_digest_mismatch")
    snapshot.chmod(0o444)
    return snapshot, digest.hexdigest()


def _open_ro(path: Path, *, immutable: bool = False) -> SQLiteConnection:
    conn = open_readonly(path, immutable=immutable)
    conn.row_factory = sqlite3.Row
    return conn


def staging_summary(conn: SQLiteConnection) -> dict[str, Any]:
    """A complete checkpoint: every article has an ``ok`` outcome and the checkpoint counts them all."""
    records = conn.execute("SELECT COUNT(*) FROM sum20_slovnyk_articles").fetchone()[0]
    ok = conn.execute(
        "SELECT COUNT(*) FROM sum20_slovnyk_articles AS a JOIN sum20_slovnyk_outcomes AS o "
        "ON o.url = a.url WHERE o.status = 'ok'"
    ).fetchone()[0]
    outcomes = conn.execute("SELECT COUNT(*) FROM sum20_slovnyk_outcomes").fetchone()[0]
    checkpoint = conn.execute(
        "SELECT completed_count, last_url, updated_at FROM sum20_slovnyk_checkpoint WHERE singleton = 1"
    ).fetchone()
    if checkpoint is None or not records or not (records == ok == outcomes == checkpoint[0]):
        raise Refused("staging_incomplete")
    return {
        "records": records,
        "checkpoint_count": checkpoint[0],
        "checkpoint_last_url": checkpoint[1],
        "checkpoint_updated_at": checkpoint[2],
    }


def staged_articles(conn: SQLiteConnection) -> Iterator[sqlite3.Row]:
    yield from conn.execute(
        "SELECT url, source_url, mirror, lemma, headword, title, text, senses_json, fetched_at, content_sha256 "
        "FROM sum20_slovnyk_articles ORDER BY url"
    )


def _row_digest(digest: Any, *fields: str) -> None:
    *head, text = fields
    digest.update(json.dumps([*head, hashlib.sha256(text.encode("utf-8")).hexdigest()]).encode("utf-8") + b"\n")


def staging_digest(conn: SQLiteConnection) -> str:
    digest = hashlib.sha256()
    for row in staged_articles(conn):
        _row_digest(
            digest,
            row["url"],
            row["source_url"],
            row["mirror"],
            row["lemma"],
            row["headword"],
            row["title"],
            row["fetched_at"],
            row["content_sha256"],
            row["senses_json"],
            row["text"],
        )
    return digest.hexdigest()


def imported_digest(conn: SQLiteConnection) -> str:
    digest = hashlib.sha256()
    for row in conn.execute(
        "SELECT mirror_url, source_url, mirror, lemma, headword, title, fetched_at, content_sha256, senses_json, "
        "article_text FROM sum20_mirror_articles ORDER BY mirror_url"
    ):
        _row_digest(digest, *row)
    return digest.hexdigest()


# --- official rows and the rule ------------------------------------------------------------------------


def official_digest(conn: SQLiteConnection) -> str:
    """Full-row digest of the official collection and its crawl tables (absent tables digest as absent)."""
    digest = hashlib.sha256()
    for table, key in OFFICIAL_TABLES:
        columns = [str(row[1]) for row in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
        digest.update(json.dumps([table, columns]).encode("utf-8") + b"\n")
        if not columns:
            continue
        for row in conn.execute(f'SELECT * FROM "{table}" ORDER BY "{key}"'):
            digest.update(json.dumps(list(row), ensure_ascii=False).encode("utf-8") + b"\n")
    return digest.hexdigest()


def table_counts(conn: SQLiteConnection) -> dict[str, int]:
    """Row counts of every ordinary table outside the mirror tables."""
    names = [
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "AND sql NOT LIKE 'CREATE VIRTUAL TABLE%' ORDER BY name"
        )
    ]
    return {
        name: conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        for name in names
        if name not in sum20_mirror.MIRROR_TABLES
    }


def official_by_key(conn: SQLiteConnection) -> dict[str, list[tuple[str, str, str, bool]]]:
    columns = [str(row[1]) for row in conn.execute("PRAGMA table_info(sum20_articles)").fetchall()]
    grouped: dict[str, list[tuple[str, str, str, bool]]] = {}
    if not columns:
        return grouped
    for headword, text, key, live in conn.execute(
        f"SELECT headword, article_text, normalized_lookup_key, ({live_article_predicate(columns)}) "
        "FROM sum20_articles ORDER BY wordid"
    ):
        grouped.setdefault(str(key), []).append((str(headword or ""), str(text or ""), str(key), bool(live)))
    return grouped


def classify_staging(staging: SQLiteConnection, official: SQLiteConnection) -> dict[str, Any]:
    """Relation counts under the rule, plus the reconciliation report's differences mapped onto them.

    ``reconcile_sum20`` groups by URL lemma; every identity it reports as differing
    must stay served and flagged under the import's headword identity.
    """
    by_key = official_by_key(official)
    relations: Counter[str] = Counter()
    by_lemma: dict[str, set[str]] = {}
    samples: dict[str, list[str]] = {relation: [] for relation in sum20_mirror.RELATIONS}
    for row in staged_articles(staging):
        key = sum20_mirror.mirror_key(row["headword"])
        if not key:
            raise Refused("staging_headword_missing")
        relation = sum20_mirror.classify(row["headword"], row["text"], by_key.get(key, []))
        relations[relation] += 1
        by_lemma.setdefault(normalize_sum20_lookup(row["lemma"]), set()).add(relation)
        if len(samples[relation]) < SAMPLE_PER_RELATION and key not in samples[relation]:
            samples[relation].append(key)
    _, staged = reconcile_sum20._inventory(staging, staging=True)
    _, ingested = reconcile_sum20._inventory(official, staging=False)
    differing = sorted(key for key in staged.keys() & ingested.keys() if staged[key] != ingested[key])
    flagged = {sum20_mirror.DIFFERS, sum20_mirror.OFFICIAL_QUARANTINED}
    return {
        "relation_counts": sum20_mirror.relation_counts(relations.elements()),
        "reconcile_differing": len(differing),
        "reconcile_differing_unflagged": [key for key in differing if not by_lemma.get(key, set()) <= flagged],
        "samples": samples,
    }


# --- build -------------------------------------------------------------------------------------------------


def _copy_live(live: Path, destination: Path) -> None:
    """SQLite online backup from a read-only connection into a fresh file."""
    with closing(open_readonly(live)) as source, closing(sqlite3.connect(destination)) as copy:
        source.backup(copy)


def _import(
    conn: SQLiteConnection,
    staging: SQLiteConnection,
    info: dict[str, Any],
    plan: dict[str, Any],
    label: str,
    official: str,
) -> None:
    """Replace only the derived mirror rows; earlier import receipts stay as history."""
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(sum20_mirror.SCHEMA_SQL)
    conn.execute("DELETE FROM sum20_mirror_articles")
    cursor = conn.execute(
        "INSERT INTO sum20_mirror_imports (generation, rule_version, staging_sha256, staging_records, "
        "checkpoint_count, checkpoint_last_url, checkpoint_updated_at, official_digest, relation_counts, imported_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            label,
            sum20_mirror.RULE_VERSION,
            info["sha256"],
            info["records"],
            info["checkpoint_count"],
            info["checkpoint_last_url"],
            info["checkpoint_updated_at"],
            official,
            json.dumps(plan["relation_counts"], sort_keys=True),
            _now(),
        ),
    )
    import_id = cursor.lastrowid
    batch: list[tuple] = []
    for row in staged_articles(staging):
        batch.append(
            (
                row["url"],
                row["source_url"],
                row["mirror"],
                row["lemma"],
                row["headword"],
                sum20_mirror.mirror_key(row["headword"]),
                row["title"],
                row["text"],
                row["senses_json"],
                row["fetched_at"],
                row["content_sha256"],
                import_id,
            )
        )
        if len(batch) >= BATCH_ROWS:
            _insert(conn, batch)
            batch = []
    if batch:
        _insert(conn, batch)
    conn.commit()


def _insert(conn: SQLiteConnection, batch: list[tuple]) -> None:
    conn.executemany(
        "INSERT INTO sum20_mirror_articles (mirror_url, source_url, mirror, lemma, headword, normalized_lookup_key, "
        "title, article_text, senses_json, fetched_at, content_sha256, import_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        batch,
    )


def _imported_relations(conn: SQLiteConnection) -> Iterator[str]:
    by_key = official_by_key(conn)
    for headword, text, key in conn.execute(
        "SELECT headword, article_text, normalized_lookup_key FROM sum20_mirror_articles"
    ):
        yield sum20_mirror.classify(str(headword), str(text), by_key.get(str(key), []))


def verify(
    path: Path, live: Path, staging: SQLiteConnection, pre: dict[str, Any], plan: dict[str, Any]
) -> dict[str, Any]:
    """Every check the new generation must pass before it may become a candidate."""
    from scripts.wiki.sources_db import query_sum20

    failures: list[str] = []
    with closing(_open_ro(path)) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            failures.append("integrity_check")
        if conn.execute("PRAGMA foreign_key_check(sum20_mirror_articles)").fetchall():
            failures.append("foreign_key_check")
        if imported_digest(conn) != staging_digest(staging):
            failures.append("mirror_rows_differ_from_staging")
        if official_digest(conn) != pre["official_digest"]:
            failures.append("official_rows_changed")
        if table_counts(conn) != pre["table_counts"]:
            failures.append("other_table_counts_changed")
        counts = sum20_mirror.relation_counts(_imported_relations(conn))
    if counts != plan["relation_counts"]:
        failures.append("relation_counts_differ_from_plan")
    if plan["reconcile_differing_unflagged"]:
        failures.append("reconcile_difference_not_flagged")
    sampled = 0
    for relation, keys in plan["samples"].items():
        for key in keys:
            records = query_sum20(key, db_path=path)
            mirror = [r for r in records if r.get("source_role") == "mirror"]
            official = [r for r in records if r.get("source_role") == "official"]
            if sum20_mirror.is_served(relation):
                if not any(r["official_relation"] == relation for r in mirror):
                    failures.append(f"sample_not_served:{relation}")
            elif mirror or not official:
                failures.append(f"sample_not_suppressed:{relation}")
            before = [r for r in query_sum20(key, db_path=live) if r.get("source_role") == "official"]
            if official != before:
                failures.append(f"sample_official_changed:{relation}")
            sampled += 1
    if failures:
        raise VerificationFailed(",".join(sorted(set(failures))))
    return {"checks": "passed", "sampled_lookups": sampled, "relation_counts": counts}


def _seal(path: Path, mode: int) -> None:
    """Persist WAL mode in the header, close cleanly and leave one self-contained file."""
    with closing(sqlite3.connect(path)) as conn:
        if str(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower() != "wal":
            raise VerificationFailed("journal_mode_not_wal")
    if any(sidecar.exists() for sidecar in _sidecars(path)):
        raise VerificationFailed("sidecar_left_after_close")
    _fsync(path)
    path.chmod(mode)


def _pre_image(target: Target, scan: Callable[[Sequence[Path]], dict[str, Any]]) -> dict[str, Any]:
    identity = live_identity(target.live)
    _require_quiet(identity)
    _require_held(target.live)
    _require_no_writers(target, scan)
    if shutil.disk_usage(target.data_dir).free < 2 * identity["size"] + DISK_RESERVE_BYTES:
        raise Refused("disk_space")
    return {"identity": identity, "sha256": file_sha256(target.live)}


def plan(target: Target) -> dict[str, Any]:
    """Read-only relation counts against the live official rows; nothing is copied or written."""
    with closing(_open_ro(target.staging)) as staging, closing(_open_ro(target.live)) as live:
        summary = staging_summary(staging)
        result = classify_staging(staging, live)
    return {
        "status": "plan",
        "rule_version": sum20_mirror.RULE_VERSION,
        "staging_records": summary["records"],
        **result,
    }


def build(
    target: Target, expect_sha256: str, *, scan: Callable[[Sequence[Path]], dict[str, Any]] = holders
) -> dict[str, Any]:
    """Copy, import and verify into a sealed candidate generation; the live store is only read."""
    with build_lock(target):
        pre = _pre_image(target, scan)
        snapshot, staging_sha = snapshot_staging(target, expect_sha256)
        temp = target.temp("building")
        _remove([temp, *_sidecars(temp)])
        try:
            with closing(_open_ro(snapshot, immutable=True)) as staging:
                info = {"sha256": staging_sha, **staging_summary(staging)}
                with closing(_open_ro(target.live)) as live:
                    pre["official_digest"] = official_digest(live)
                    pre["table_counts"] = table_counts(live)
                    result = classify_staging(staging, live)
                if result["reconcile_differing_unflagged"]:
                    raise VerificationFailed("reconcile_difference_not_flagged")
                _copy_live(target.live, temp)
                label = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
                with closing(sqlite3.connect(temp)) as conn:
                    _import(conn, staging, info, result, label, pre["official_digest"])
                checks = verify(temp, target.live, staging, pre, result)
            _seal(temp, pre["identity"]["mode"])
            sha256 = file_sha256(temp)
            generation = generation_id(sha256)
            target.candidates_dir.mkdir(parents=True, exist_ok=True)
            os.replace(temp, target.candidate(generation))
            _fsync(target.candidates_dir, directory=True)
        except BaseException:
            _remove([temp, *_sidecars(temp)])
            raise
        finally:
            _remove([snapshot])
        receipt = {
            "generation": generation,
            "sha256": sha256,
            "kind": "sum20_mirror_import",
            "state": "candidate",
            "parent": generation_id(pre["sha256"]),
            "parent_sha256": pre["sha256"],
            "parent_identity": pre["identity"],
            "import_label": label,
            "staging_sha256": staging_sha,
            "staging_records": info["records"],
            "rule_version": sum20_mirror.RULE_VERSION,
            "reconcile_differing": result["reconcile_differing"],
            "samples": result["samples"],
            "verification": checks,
            "recorded_at": _now(),
        }
        _write_json(target.receipt(generation), receipt)
        return {"status": "candidate", **receipt}


# --- publication -----------------------------------------------------------------------------------------


def systemctl(action: str, unit: str) -> None:
    env = dict(os.environ)
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    subprocess.run(
        ["systemctl", "--user", action, unit], check=True, env=env, timeout=SYSTEMCTL_TIMEOUT_S, capture_output=True
    )


class Drain:
    """Stop units for a critical section and always try to start every one of them again.

    A stop or start failure of one unit never skips another. Stop failures refuse
    the section; start failures are collected in ``restart_errors`` and never
    hide whether the section itself committed.
    """

    def __init__(self, units: Sequence[str], control: Callable[[str, str], None]) -> None:
        self.units, self.control = list(units), control
        self.restart_errors: list[str] = []

    def __enter__(self) -> Drain:
        stop_errors = []
        try:
            for unit in self.units:
                try:
                    self.control("stop", unit)
                except Exception as exc:  # any failure leaves the unit's state unknown
                    stop_errors.append(f"stop {unit}: {type(exc).__name__}")
        except BaseException:  # an interruption still starts every unit before it propagates
            self._start_all()
            raise
        if stop_errors:
            self._start_all()
            raise Refused("unit_stop_failed", unit_errors=stop_errors + self.restart_errors)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._start_all()
        if isinstance(exc, (Refused, VerificationFailed)) and self.restart_errors:
            exc.detail["unit_restart_errors"] = self.restart_errors
        return False

    def _start_all(self) -> None:
        interrupted: BaseException | None = None
        for unit in reversed(self.units):
            try:
                self.control("start", unit)
            except Exception as exc:
                self.restart_errors.append(f"start {unit}: {type(exc).__name__}")
            except BaseException as exc:  # finish the other starts, then let the interruption through
                self.restart_errors.append(f"start {unit}: {type(exc).__name__}")
                interrupted = interrupted or exc
        if interrupted is not None:
            raise interrupted


def _unit_pids(units: Sequence[str], proc: Path = Path("/proc")) -> Callable[[dict[str, Any]], bool]:
    """Whether a holder or lock belongs to one of ``units`` (its cgroup path ends in the unit name)."""

    def allowed(holder: dict[str, Any]) -> bool:
        try:
            cgroup = (proc / str(holder["pid"]) / "cgroup").read_text()
        except OSError:
            return False
        return any(line.rstrip().endswith(f"/{unit}") for line in cgroup.splitlines() for unit in units)

    return allowed


def _await_drain(target: Target, options: dict[str, Any], allowed: Callable[[dict[str, Any]], bool]) -> None:
    """Poll until nothing but the drain units uses the live store, or refuse after ``wait_drained``."""
    scan, sleep, clock = options["scan"], options.get("sleep", time.sleep), options.get("clock", time.monotonic)
    deadline = clock() + options["wait_drained"]
    while True:
        left = _undrained(scan(_live_files(target)), allowed)
        if not left["holders"] and left["locks"] == []:
            return
        if clock() >= deadline:
            raise Refused("live_store_in_use", **left)
        sleep(DRAIN_POLL_S)


def _barrier(target: Target, parent: dict[str, Any]) -> None:
    """Unchanged since the candidate's copy, checkpointed and held; the write leases prove it unused."""
    now = live_identity(target.live)
    if now != parent:
        raise Refused("live_store_changed_since_candidate")
    _require_quiet(now)
    _require_held(target.live)


def _journal(target: Target) -> Path:
    return target.work_dir / "publication.json"


def recover(target: Target) -> dict[str, Any] | None:
    """Finish or undo a publication that a crash interrupted; run under the lock before any other step.

    If the rename did not happen, the live file gets its mode back and a backup
    link sharing its inode is removed (a backup must never alias the live inode).
    If it did, the retained file gets its mode back and the receipts are completed.
    """
    journal = _journal(target)
    if not journal.is_file():
        return None
    state = _read_json(journal)
    backup = target.backup(state["previous"])
    live = target.live.stat()
    if live.st_ino == state["old_ino"]:
        target.live.chmod(state["old_mode"])
        if backup.exists() and backup.stat().st_ino == live.st_ino:
            backup.unlink()
            _fsync(target.backups_dir, directory=True)
        outcome = "rolled_back"
    else:
        if backup.exists():
            backup.chmod(state["old_mode"])
        _finish_receipts(target, state)
        outcome = "rolled_forward"
    journal.unlink()
    _fsync(target.work_dir, directory=True)
    return {"recovered": outcome, "previous": state["previous"]}


def _finish_receipts(target: Target, state: dict[str, Any]) -> None:
    if not target.receipt(state["previous"]).exists():
        _write_json(
            target.receipt(state["previous"]),
            {
                "generation": state["previous"],
                "sha256": state["previous_sha256"],
                "kind": state["kind"],
                "state": "retained",
                "recorded_at": _now(),
            },
        )
    published = state.get("published")
    if published and target.receipt(published).is_file():
        receipt = _read_json(target.receipt(published))
        if receipt.get("state") != "published":
            receipt.update(
                {
                    "state": "published",
                    "published_at": _now(),
                    "previous": state["previous"],
                    "inode": target.live.stat().st_ino,
                }
            )
            _write_json(target.receipt(published), receipt)


def _publish(
    target: Target,
    source: Path,
    expected_sha256: str,
    parent: dict[str, Any],
    parent_sha256: str,
    kind: str,
    options: dict[str, Any],
    published: str | None = None,
) -> dict[str, Any]:
    """Drain, retain the live inode durably, fence it, and rename ``source`` over it.

    Order: both digests before any unit stops; wait until only drain-unit
    processes use the store; stop the units; barrier; journal the intent;
    hard-link the live inode into backups and fsync that and the receipt; set the
    old inode to mode 000, so a new open fails instead of reading it; barrier
    again; rename; give the retained inode its mode back; finish the receipts.
    ``recover`` completes or undoes any step a crash interrupts. An unchanged
    identity proves the live bytes still hash to ``parent_sha256``.
    """
    if file_sha256(source) != expected_sha256:
        raise VerificationFailed("candidate_digest_mismatch")
    scan = options["scan"]
    allowed = _unit_pids(options["drain_units"])
    _await_drain(target, options, allowed)
    previous = generation_id(parent_sha256)
    backup = target.backup(previous)
    state = {
        "previous": previous,
        "previous_sha256": parent_sha256,
        "old_ino": parent["ino"],
        "old_mode": parent["mode"],
        "kind": kind,
        "published": published,
    }
    diagnose = lambda: _undrained(scan(_live_files(target)), lambda holder: False)  # noqa: E731
    with Drain(options["drain_units"], options["control"]) as drain:
        _barrier(target, parent)
        if backup.exists() and backup.stat().st_ino != parent["ino"] and file_sha256(backup) != parent_sha256:
            raise Refused("backup_name_conflict")
        with leases(_live_files(target), fcntl.F_WRLCK, diagnose) as intact:
            target.backups_dir.mkdir(parents=True, exist_ok=True)
            _write_json(_journal(target), state)
            replaced = False
            try:
                if not backup.exists():
                    os.link(target.live, backup)
                _fsync(target.backups_dir, directory=True)
                _finish_receipts(target, {**state, "published": None})
                target.live.chmod(0)
                # An open that began before the fence breaks a lease; refuse rather than leave it the old inode.
                if not intact():
                    raise Refused("live_store_opened_during_publication", **diagnose())
                _barrier(target, {**parent, "mode": 0})
                _remove(_sidecars(target.live))
                os.replace(source, target.live)
                replaced = True
                _fsync(target.data_dir, directory=True)
            finally:
                recover(target)  # replaced: unfence the retained inode and finish; otherwise undo
        if not replaced:
            raise Refused("publication_not_completed")
    return {"previous": previous, "unit_restart_errors": drain.restart_errors}


def _publish_options(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "scan": holders,
        "control": systemctl,
        "drain_units": list(args.drain_unit or []),
        "wait_drained": float(args.wait_drained),
    }


def publish(target: Target, generation: str, options: dict[str, Any]) -> dict[str, Any]:
    with build_lock(target):
        recovered = recover(target)
        candidate, receipt_path = target.candidate(generation), target.receipt(generation)
        if candidate.is_symlink() or not candidate.is_file() or not receipt_path.is_file():
            raise Refused("candidate_unknown")
        receipt = _read_json(receipt_path)
        if receipt.get("state") != "candidate":
            raise Refused("candidate_unknown")
        result = _publish(
            target,
            candidate,
            receipt["sha256"],
            receipt["parent_identity"],
            receipt["parent_sha256"],
            "retained_before_import",
            options,
            published=generation,
        )
        return {
            "status": "published",
            "generation": generation,
            "recovered_first": recovered,
            "default_reader": default_reader_check(_read_json(receipt_path)),
            **result,
        }


def default_reader_check(receipt: dict[str, Any]) -> dict[str, Any]:
    """Whether the default ``query_sum20`` selection now serves a sampled mirror-only key."""
    from scripts.wiki.sources_db import query_sum20

    keys = (receipt.get("samples") or {}).get(sum20_mirror.MIRROR_ONLY) or []
    if not keys:
        return {"key_sampled": False}
    records = query_sum20(keys[0])
    return {"key_sampled": True, "serves_mirror": any(r.get("source_role") == "mirror" for r in records)}


def restore(target: Target, generation: str, options: dict[str, Any]) -> dict[str, Any]:
    with build_lock(target):
        recovered = recover(target)
        backup, receipt_path = target.backup(generation), target.receipt(generation)
        if backup.is_symlink() or not backup.is_file() or not receipt_path.is_file():
            raise Refused("generation_unknown")
        expected = _read_json(receipt_path)["sha256"]
        parent = live_identity(target.live)
        _require_quiet(parent)
        _require_held(target.live)
        parent_sha256 = file_sha256(target.live)
        if parent_sha256 == expected:
            return {"status": "already_live", "generation": generation}
        temp = target.temp(f"restoring-{generation}")
        try:
            shutil.copyfile(backup, temp)
            _fsync(temp)
            temp.chmod(parent["mode"])
            result = _publish(target, temp, expected, parent, parent_sha256, "retained_before_restore", options)
        finally:
            _remove([temp])
        return {
            "status": "restored",
            "generation": generation,
            "sha256": expected,
            "recovered_first": recovered,
            **result,
        }


def generations(target: Target) -> dict[str, Any]:
    with build_lock(target):
        recovered = recover(target)
        live_ino = target.live.stat().st_ino
        rows = []
        for path in sorted(target.receipts_dir.glob("*.json")) if target.receipts_dir.is_dir() else []:
            receipt = _read_json(path)
            generation = receipt["generation"]
            held = [p for p in (target.backup(generation), target.candidate(generation)) if p.is_file()]
            rows.append(
                {
                    "generation": generation,
                    "kind": receipt.get("kind"),
                    "state": receipt.get("state"),
                    "recorded_at": receipt.get("recorded_at"),
                    "live": receipt.get("inode") == live_ino or any(p.stat().st_ino == live_ino for p in held),
                    "restorable": target.backup(generation).is_file(),
                }
            )
    return {"status": "generations", "recovered_first": recovered, "generations": rows}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import the staged СУМ-20 mirror into a new verified sources.db generation, publish it, or "
            "list/restore generations. Primary checkout only; never writes the official sum20 tables."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.ingest.sum20_mirror_import build --expect-staging-sha256 <sha256>\n"
            "  .venv/bin/python -m scripts.ingest.sum20_mirror_import publish --generation <id> "
            "--drain-unit learn-ukrainian-sources.service --wait-drained 900\n"
            "  .venv/bin/python -m scripts.ingest.sum20_mirror_import restore --generation <id> "
            "--drain-unit learn-ukrainian-sources.service --wait-drained 900\n\n"
            "Outputs: JSON on stdout; candidates, backups and receipts under data/sources/.\n"
            "Exit codes: 0 success; 1 verification failed (live store untouched); 2 refused; 3 swapped, unit restart failed.\n"
            "Related: issue #8579; docs/runbooks/dictionary-acquisition.md; scripts/wiki/sum20_mirror.py."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Read-only relation counts for the staged mirror against the live official rows.")
    build_cmd = sub.add_parser(
        "build", help="Build and verify a sealed candidate generation; the live store is read only."
    )
    build_cmd.add_argument(
        "--expect-staging-sha256",
        required=True,
        help="SHA-256 of the admitted staging file (required), e.g. the admission record's digest.",
    )
    for name, help_text in (
        ("publish", "Swap a candidate generation in."),
        ("restore", "Swap a retained generation back in."),
    ):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("--generation", required=True, help="Generation id from `generations`, e.g. 0123456789abcdef.")
        cmd.add_argument(
            "--drain-unit",
            action="append",
            help="systemd user unit to stop around the swap and start again (repeatable; default none).",
        )
        cmd.add_argument(
            "--wait-drained",
            type=float,
            default=0.0,
            help="Seconds to wait for other holders of the live store to exit (default 0).",
        )
    sub.add_parser("generations", help="List recorded generations and which one is live.")
    return parser


def main(argv: list[str] | None = None, *, test_data_dir: Path | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        target = writer_target(test_data_dir=test_data_dir)
        if args.command == "plan":
            payload = plan(target)
        elif args.command == "build":
            payload = build(target, args.expect_staging_sha256)
        elif args.command == "publish":
            payload = publish(target, args.generation, _publish_options(args))
        elif args.command == "restore":
            payload = restore(target, args.generation, _publish_options(args))
        else:
            payload = generations(target)
    except Refused as exc:
        print(json.dumps({"status": "refused", "reason": exc.reason, **exc.detail}, ensure_ascii=False))
        return 2
    except VerificationFailed as exc:
        print(json.dumps({"status": "verification_failed", "reason": str(exc), **exc.detail}, ensure_ascii=False))
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    # The swap is committed either way; a unit that did not start again needs the operator.
    return 3 if payload.get("unit_restart_errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
