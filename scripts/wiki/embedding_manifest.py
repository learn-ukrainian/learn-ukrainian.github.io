"""Storage layer for embedding shard manifests."""

from __future__ import annotations

import os
import re
import sqlite3
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .embedding_manifest_schema import EMBEDDING_MANIFEST_DDL

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
DEFAULT_MANIFEST_DB = DEFAULT_EMBEDDINGS_DIR / "manifest.db"
DEFAULT_DIMS = 1024
DEFAULT_DTYPE = "float16"
_SQLITE_BUSY_TIMEOUT_MS = 30_000
_SHARD_NAME_RE = re.compile(r"shard-(\d{6})\.npy$")


@dataclass(frozen=True)
class UnitSpecInput:
    unit_key: str
    parent_key: str | None
    text_sha256: str
    model: str


@dataclass(frozen=True)
class UnitSpec:
    unit_key: str
    corpus: str
    parent_key: str | None
    text_sha256: str
    model: str
    shard_id: int
    row_idx: int


@dataclass(frozen=True)
class UnitRow(UnitSpec):
    deleted: bool
    updated_at: str


class EmbeddingManifest:
    """SQLite-backed manifest for embedding shard files."""

    def __init__(self, db_path: Path = DEFAULT_MANIFEST_DB) -> None:
        self._db_path = Path(db_path)
        self._embeddings_dir = self._db_path.parent
        self._embeddings_dir.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute(f"PRAGMA busy_timeout = {_SQLITE_BUSY_TIMEOUT_MS}")
        self._conn.executescript(EMBEDDING_MANIFEST_DDL)
        self._conn.commit()

    def add_shard(
        self,
        *,
        corpus: str,
        path: Path,
        rows: int,
        dims: int = DEFAULT_DIMS,
        dtype: str = DEFAULT_DTYPE,
    ) -> int:
        self._begin_immediate()
        try:
            shard_id = self._insert_shard(
                corpus=corpus,
                path=self._relative_path(path),
                rows=rows,
                dims=dims,
                dtype=dtype,
                committed_at=_utc_timestamp(),
            )
            self._conn.commit()
            return shard_id
        except Exception:
            self._rollback_quietly()
            raise

    def add_units(self, rows: list[UnitSpec]) -> None:
        if not rows:
            return
        self._begin_immediate()
        try:
            self._upsert_units(rows, updated_at=_utc_timestamp())
            self._conn.commit()
        except Exception:
            self._rollback_quietly()
            raise

    def get_unit(self, unit_key: str) -> UnitRow | None:
        row = self._conn.execute(
            """
            SELECT
                unit_key,
                corpus,
                parent_key,
                text_sha256,
                model,
                shard_id,
                row_idx,
                deleted,
                updated_at
            FROM embedding_units
            WHERE unit_key = ?
            """,
            (unit_key,),
        ).fetchone()
        return _row_to_unit(row) if row is not None else None

    def get_units(self, unit_keys: list[str]) -> dict[str, UnitRow]:
        if not unit_keys:
            return {}

        found: dict[str, UnitRow] = {}
        for batch in _chunked(unit_keys, size=900):
            placeholders = ",".join("?" for _ in batch)
            rows = self._conn.execute(
                f"""
                SELECT
                    unit_key,
                    corpus,
                    parent_key,
                    text_sha256,
                    model,
                    shard_id,
                    row_idx,
                    deleted,
                    updated_at
                FROM embedding_units
                WHERE unit_key IN ({placeholders})
                """,
                tuple(batch),
            ).fetchall()
            found.update({_row_to_unit(row).unit_key: _row_to_unit(row) for row in rows})
        return found

    def mark_stale(self, unit_key: str) -> None:
        self._mark_deleted_alias(unit_key)

    def mark_deleted(self, unit_key: str) -> None:
        self._mark_deleted_alias(unit_key)

    def active_units_for_corpus(self, corpus: str) -> list[UnitRow]:
        rows = self._conn.execute(
            """
            SELECT
                unit_key,
                corpus,
                parent_key,
                text_sha256,
                model,
                shard_id,
                row_idx,
                deleted,
                updated_at
            FROM embedding_units
            WHERE corpus = ? AND deleted = 0
            ORDER BY unit_key
            """,
            (corpus,),
        ).fetchall()
        return [_row_to_unit(row) for row in rows]

    def shard_map_for_corpus(self, corpus: str) -> dict[int, Path]:
        rows = self._conn.execute(
            """
            SELECT shard_id, path
            FROM embedding_shards
            WHERE corpus = ?
            ORDER BY shard_id
            """,
            (corpus,),
        ).fetchall()
        return {
            int(row["shard_id"]): (self._embeddings_dir / row["path"]).resolve()
            for row in rows
        }

    def vacuum_orphaned_shards(self) -> int:
        self._begin_immediate()
        try:
            orphan_rows = self._conn.execute(
                """
                SELECT shard_id, path
                FROM embedding_shards
                WHERE rows = 0
                   OR NOT EXISTS (
                        SELECT 1
                        FROM embedding_units
                        WHERE embedding_units.shard_id = embedding_shards.shard_id
                          AND embedding_units.deleted = 0
                   )
                ORDER BY shard_id
                """
            ).fetchall()
            if not orphan_rows:
                self._conn.commit()
                return 0

            shard_ids = [int(row["shard_id"]) for row in orphan_rows]
            placeholders = ",".join("?" for _ in shard_ids)
            self._conn.execute(
                f"DELETE FROM embedding_units WHERE shard_id IN ({placeholders})",
                tuple(shard_ids),
            )
            self._conn.execute(
                f"DELETE FROM embedding_shards WHERE shard_id IN ({placeholders})",
                tuple(shard_ids),
            )
            self._conn.commit()
        except Exception:
            self._rollback_quietly()
            raise

        for row in orphan_rows:
            try:
                (self._embeddings_dir / row["path"]).unlink(missing_ok=True)
            except OSError:
                continue
        return len(orphan_rows)

    def stats(self) -> dict:
        corpus_stats: dict[str, dict[str, int]] = {}

        for row in self._conn.execute(
            """
            SELECT corpus, COUNT(*) AS shard_count, COALESCE(SUM(rows), 0) AS shard_rows
            FROM embedding_shards
            GROUP BY corpus
            ORDER BY corpus
            """
        ).fetchall():
            corpus = str(row["corpus"])
            corpus_stats[corpus] = {
                "shards": int(row["shard_count"]),
                "shard_rows": int(row["shard_rows"]),
                "units": 0,
                "active_units": 0,
                "deleted_units": 0,
            }

        for row in self._conn.execute(
            """
            SELECT
                corpus,
                COUNT(*) AS unit_count,
                SUM(CASE WHEN deleted = 0 THEN 1 ELSE 0 END) AS active_units,
                SUM(CASE WHEN deleted = 1 THEN 1 ELSE 0 END) AS deleted_units
            FROM embedding_units
            GROUP BY corpus
            ORDER BY corpus
            """
        ).fetchall():
            corpus = str(row["corpus"])
            corpus_stats.setdefault(
                corpus,
                {
                    "shards": 0,
                    "shard_rows": 0,
                    "units": 0,
                    "active_units": 0,
                    "deleted_units": 0,
                },
            )
            corpus_stats[corpus]["units"] = int(row["unit_count"])
            corpus_stats[corpus]["active_units"] = int(row["active_units"] or 0)
            corpus_stats[corpus]["deleted_units"] = int(row["deleted_units"] or 0)

        return {
            "db_path": str(self._db_path),
            "corpora": corpus_stats,
            "total_shards": sum(stats["shards"] for stats in corpus_stats.values()),
            "total_units": sum(stats["units"] for stats in corpus_stats.values()),
            "active_units": sum(stats["active_units"] for stats in corpus_stats.values()),
            "deleted_units": sum(stats["deleted_units"] for stats in corpus_stats.values()),
        }

    def close(self) -> None:
        self._conn.close()

    def _begin_immediate(self) -> None:
        self._conn.execute("BEGIN IMMEDIATE")

    def _insert_shard(
        self,
        *,
        corpus: str,
        path: Path,
        rows: int,
        dims: int,
        dtype: str,
        committed_at: str,
    ) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO embedding_shards (corpus, path, rows, dims, dtype, committed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (corpus, path.as_posix(), rows, dims, dtype, committed_at),
        )
        return int(cursor.lastrowid)

    def _upsert_units(self, rows: list[UnitSpec], *, updated_at: str) -> None:
        self._conn.executemany(
            """
            INSERT INTO embedding_units (
                unit_key,
                corpus,
                parent_key,
                text_sha256,
                model,
                shard_id,
                row_idx,
                deleted,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
            ON CONFLICT(unit_key) DO UPDATE SET
                corpus = excluded.corpus,
                parent_key = excluded.parent_key,
                text_sha256 = excluded.text_sha256,
                model = excluded.model,
                shard_id = excluded.shard_id,
                row_idx = excluded.row_idx,
                deleted = 0,
                updated_at = excluded.updated_at
            """,
            [
                (
                    row.unit_key,
                    row.corpus,
                    row.parent_key,
                    row.text_sha256,
                    row.model,
                    row.shard_id,
                    row.row_idx,
                    updated_at,
                )
                for row in rows
            ],
        )

    def _relative_path(self, path: Path) -> Path:
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate.relative_to(self._embeddings_dir)
        return candidate

    def _mark_deleted_alias(self, unit_key: str) -> None:
        self._begin_immediate()
        try:
            self._conn.execute(
                """
                UPDATE embedding_units
                SET deleted = 1, updated_at = ?
                WHERE unit_key = ?
                """,
                (_utc_timestamp(), unit_key),
            )
            self._conn.commit()
        except Exception:
            self._rollback_quietly()
            raise

    def _next_shard_relative_path(self, corpus: str) -> Path:
        max_number = 0
        rows = self._conn.execute(
            "SELECT path FROM embedding_shards WHERE corpus = ? ORDER BY shard_id",
            (corpus,),
        ).fetchall()
        for row in rows:
            match = _SHARD_NAME_RE.search(str(row["path"]))
            if match is not None:
                max_number = max(max_number, int(match.group(1)))
        return Path(corpus) / f"shard-{max_number + 1:06d}.npy"

    @property
    def embeddings_dir(self) -> Path:
        return self._embeddings_dir

    def _rollback_quietly(self) -> None:
        with suppress(sqlite3.Error):
            self._conn.rollback()


def append_shard(
    manifest: EmbeddingManifest,
    *,
    corpus: str,
    vectors: NDArray[np.float16],
    unit_specs: list[UnitSpecInput],
) -> int:
    """Atomically append a shard file and its manifest rows."""

    if vectors.dtype != np.float16:
        raise ValueError("vectors must use float16 dtype")
    if vectors.ndim != 2 or vectors.shape[1] != DEFAULT_DIMS:
        raise ValueError(f"vectors must have shape (N, {DEFAULT_DIMS})")
    if len(unit_specs) != int(vectors.shape[0]):
        raise ValueError("unit_specs length must match vector row count")

    shard_rel_path = manifest._next_shard_relative_path(corpus)
    shard_abs_path = manifest.embeddings_dir / shard_rel_path
    tmp_path = Path(f"{shard_abs_path}.tmp")
    shard_abs_path.parent.mkdir(parents=True, exist_ok=True)

    renamed = False
    try:
        with tmp_path.open("wb") as handle:
            np.save(handle, vectors)
            handle.flush()
            os.fsync(handle.fileno())

        os.rename(tmp_path, shard_abs_path)
        renamed = True

        committed_at = _utc_timestamp()
        manifest._begin_immediate()
        shard_id = manifest._insert_shard(
            corpus=corpus,
            path=shard_rel_path,
            rows=int(vectors.shape[0]),
            dims=int(vectors.shape[1]),
            dtype=str(vectors.dtype),
            committed_at=committed_at,
        )
        manifest._upsert_units(
            [
                UnitSpec(
                    unit_key=spec.unit_key,
                    corpus=corpus,
                    parent_key=spec.parent_key,
                    text_sha256=spec.text_sha256,
                    model=spec.model,
                    shard_id=shard_id,
                    row_idx=row_idx,
                )
                for row_idx, spec in enumerate(unit_specs)
            ],
            updated_at=committed_at,
        )
        manifest._conn.commit()
        return shard_id
    except Exception:
        manifest._rollback_quietly()
        tmp_path.unlink(missing_ok=True)
        if renamed:
            shard_abs_path.unlink(missing_ok=True)
        raise


def reserve_corpus_shard(manifest: EmbeddingManifest, *, corpus: str) -> int:
    """Register a corpus in the manifest with a zero-row reserved shard."""

    shard_map = manifest.shard_map_for_corpus(corpus)
    if shard_map:
        return next(iter(shard_map))

    return append_shard(
        manifest,
        corpus=corpus,
        vectors=np.zeros((0, DEFAULT_DIMS), dtype=np.float16),
        unit_specs=[],
    )


def filter_new_or_changed(
    manifest: EmbeddingManifest,
    *,
    corpus: str,
    candidates: Iterable[tuple[str, str]],
) -> tuple[list[str], list[str]]:
    """Classify unit keys that need a first encode or a replacement encode."""

    candidate_rows = list(candidates)
    existing = manifest.get_units([unit_key for unit_key, _ in candidate_rows])

    new_keys: list[str] = []
    stale_keys: list[str] = []
    for unit_key, text_sha256 in candidate_rows:
        row = existing.get(unit_key)
        if row is None or row.deleted:
            new_keys.append(unit_key)
            continue
        if row.corpus != corpus:
            new_keys.append(unit_key)
            continue
        if row.text_sha256 != text_sha256:
            stale_keys.append(unit_key)
    return new_keys, stale_keys


def _utc_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_unit(row: sqlite3.Row) -> UnitRow:
    return UnitRow(
        unit_key=str(row["unit_key"]),
        corpus=str(row["corpus"]),
        parent_key=str(row["parent_key"]) if row["parent_key"] is not None else None,
        text_sha256=str(row["text_sha256"]),
        model=str(row["model"]),
        shard_id=int(row["shard_id"]),
        row_idx=int(row["row_idx"]),
        deleted=bool(row["deleted"]),
        updated_at=str(row["updated_at"]),
    )


def _chunked(items: list[str], *, size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]
