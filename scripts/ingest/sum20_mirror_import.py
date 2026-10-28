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
bit on the file or its sidecars), and no process may hold a writable descriptor
on it. This applies when ``build`` starts and again at publication. A
publication also requires the live file to be identical to the one the
candidate was copied from, with an empty WAL. Before the rename, ``--drain-unit``
units are stopped and every other holder is awaited for ``--wait-drained``
seconds. The units are started again afterwards, whatever the outcome. Only
``--allow-readonly-holders`` lets a publication proceed while read-only
descriptors remain; those readers keep the old inode until they reopen.

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
2 refused (arguments, locality, lock, staging, hold, holders, barrier).
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
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
    """Processes with a descriptor on any of ``paths`` (matched by inode), and whether it is writable.

    Processes whose descriptors cannot be read (another user) are counted, not
    guessed. This process is excluded.
    """
    inodes = {}
    for path in paths:
        try:
            info = path.stat()
        except FileNotFoundError:
            continue
        inodes[(info.st_dev, info.st_ino)] = path.name
    found: dict[int, dict[str, Any]] = {}
    unreadable = 0
    for entry in proc.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            descriptors = list((entry / "fd").iterdir())
        except PermissionError:
            unreadable += 1
            continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        for descriptor in descriptors:
            try:
                info = descriptor.stat()
                flags = next(
                    int(line.split()[1], 8)
                    for line in (entry / "fdinfo" / descriptor.name).read_text().splitlines()
                    if line.startswith("flags:")
                )
            except (OSError, StopIteration, ValueError):
                continue
            if (info.st_dev, info.st_ino) not in inodes:
                continue
            holder = found.setdefault(int(entry.name), {"pid": int(entry.name), "writable": False, "files": []})
            holder["writable"] = holder["writable"] or (flags & os.O_ACCMODE) != os.O_RDONLY
            if inodes[(info.st_dev, info.st_ino)] not in holder["files"]:
                holder["files"].append(inodes[(info.st_dev, info.st_ino)])
    for pid, holder in found.items():
        try:
            holder["command"] = (proc / str(pid) / "comm").read_text().strip()
        except OSError:
            holder["command"] = ""
    return {"holders": sorted(found.values(), key=lambda h: h["pid"]), "unreadable_processes": unreadable}


def _live_files(target: Target) -> list[Path]:
    return [target.live, *_sidecars(target.live)]


def _require_no_writers(target: Target, scan: Callable[[Sequence[Path]], dict[str, Any]]) -> None:
    writers = [h for h in scan(_live_files(target))["holders"] if h["writable"]]
    if writers:
        raise Refused("live_store_has_writers", holders=writers)


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


@contextmanager
def drained(units: Sequence[str], control: Callable[[str, str], None]) -> Iterator[None]:
    """Stop ``units`` for the duration; start them again in reverse order whatever happens."""
    stopped: list[str] = []
    try:
        for unit in units:
            control("stop", unit)
            stopped.append(unit)
        yield
    finally:
        for unit in reversed(stopped):
            control("start", unit)


def _await_holders(
    target: Target,
    scan: Callable[[Sequence[Path]], dict[str, Any]],
    wait_s: float,
    sleep: Callable[[float], None],
    clock: Callable[[], float],
    allowed: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Poll until every holder is allowed or ``wait_s`` passes; return the holders that remain."""
    deadline = clock() + wait_s
    while True:
        remaining = [h for h in scan(_live_files(target))["holders"] if not allowed(h)]
        if not remaining or clock() >= deadline:
            return remaining
        sleep(DRAIN_POLL_S)


def _unit_pids(units: Sequence[str], proc: Path = Path("/proc")) -> Callable[[dict[str, Any]], bool]:
    """Whether a holder runs inside one of ``units`` (its cgroup path ends in the unit name)."""

    def allowed(holder: dict[str, Any]) -> bool:
        try:
            cgroup = (proc / str(holder["pid"]) / "cgroup").read_text()
        except OSError:
            return False
        return any(line.rstrip().endswith(f"/{unit}") for line in cgroup.splitlines() for unit in units)

    return allowed


def _publish(
    target: Target,
    source: Path,
    expected_sha256: str,
    parent: dict[str, Any],
    parent_sha256: str,
    kind: str,
    options: dict[str, Any],
) -> str:
    """Wait for holders, drain units, check the barrier, retain the live inode and rename ``source`` over it.

    The barrier runs before the hard link and again after it, so a backup never
    shares an inode that is being written; an unchanged identity also proves the
    live bytes still hash to ``parent_sha256``. A backup created here is removed if
    the rename does not happen. The old WAL is empty, so its sidecars carry nothing.
    Both full-file digests run before any unit is drained.
    """
    if file_sha256(source) != expected_sha256:
        raise VerificationFailed("candidate_digest_mismatch")
    scan, control = options["scan"], options["control"]
    sleep, clock = options.get("sleep", time.sleep), options.get("clock", time.monotonic)
    units = options["drain_units"]
    remaining = _await_holders(target, scan, options["wait_drained"], sleep, clock, _unit_pids(units))
    if any(h["writable"] for h in remaining):
        raise Refused("live_store_has_writers", holders=remaining)
    if remaining and not options["allow_readonly_holders"]:
        raise Refused("live_store_has_readers", holders=remaining)

    def barrier() -> None:
        now = live_identity(target.live)
        if now != parent:
            raise Refused("live_store_changed_since_candidate")
        _require_quiet(now)
        _require_held(target.live)
        left = scan(_live_files(target))["holders"]
        if any(h["writable"] for h in left):
            raise Refused("live_store_has_writers", holders=left)
        if left and not options["allow_readonly_holders"]:
            raise Refused("live_store_has_readers", holders=left)

    with drained(units, control):
        barrier()
        previous_sha = parent_sha256
        previous = generation_id(previous_sha)
        backup = target.backup(previous)
        target.backups_dir.mkdir(parents=True, exist_ok=True)
        created = False
        if backup.exists():
            if backup.stat().st_ino != parent["ino"] and file_sha256(backup) != previous_sha:
                raise Refused("backup_name_conflict")
        else:
            os.link(target.live, backup)
            created = True
        replaced = False
        try:
            barrier()
            if not target.receipt(previous).exists():
                _write_json(
                    target.receipt(previous),
                    {
                        "generation": previous,
                        "sha256": previous_sha,
                        "kind": kind,
                        "state": "retained",
                        "recorded_at": _now(),
                    },
                )
            _remove(_sidecars(target.live))
            os.replace(source, target.live)
            replaced = True
            _fsync(target.data_dir, directory=True)
            _fsync(target.backups_dir, directory=True)
        finally:
            if created and not replaced:
                backup.unlink()
    return previous


def _publish_options(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "scan": holders,
        "control": systemctl,
        "drain_units": list(args.drain_unit or []),
        "wait_drained": float(args.wait_drained),
        "allow_readonly_holders": bool(args.allow_readonly_holders),
    }


def publish(target: Target, generation: str, options: dict[str, Any]) -> dict[str, Any]:
    with build_lock(target):
        candidate, receipt_path = target.candidate(generation), target.receipt(generation)
        if candidate.is_symlink() or not candidate.is_file() or not receipt_path.is_file():
            raise Refused("candidate_unknown")
        receipt = _read_json(receipt_path)
        if receipt.get("state") != "candidate":
            raise Refused("candidate_unknown")
        previous = _publish(
            target,
            candidate,
            receipt["sha256"],
            receipt["parent_identity"],
            receipt["parent_sha256"],
            "retained_before_import",
            options,
        )
        receipt.update(
            {"state": "published", "published_at": _now(), "previous": previous, "inode": target.live.stat().st_ino}
        )
        _write_json(receipt_path, receipt)
        return {
            "status": "published",
            "generation": generation,
            "previous": previous,
            "default_reader": default_reader_check(receipt),
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
            previous = _publish(target, temp, expected, parent, parent_sha256, "retained_before_restore", options)
        except BaseException:
            _remove([temp])
            raise
        return {"status": "restored", "generation": generation, "sha256": expected, "previous": previous}


def generations(target: Target) -> dict[str, Any]:
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
    return {"status": "generations", "generations": rows}


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
            "Exit codes: 0 success; 1 verification failed (live store untouched); 2 refused.\n"
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
        cmd.add_argument(
            "--allow-readonly-holders",
            action="store_true",
            help="Proceed while read-only descriptors remain; they keep the old inode (default refuse).",
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
        print(json.dumps({"status": "refused", "reason": exc.reason, **exc.detail}))
        return 2
    except VerificationFailed as exc:
        print(json.dumps({"status": "verification_failed", "reason": str(exc)}))
        return 1
    except subprocess.SubprocessError as exc:
        print(json.dumps({"status": "refused", "reason": f"systemctl_failed:{type(exc).__name__}"}))
        return 2
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
