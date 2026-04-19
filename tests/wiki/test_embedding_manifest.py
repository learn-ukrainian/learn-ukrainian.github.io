from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.embedding_manifest import (
    EmbeddingManifest,
    UnitSpecInput,
    append_shard,
    filter_new_or_changed,
)

from wiki import embedding_manifest


def _manifest_path(tmp_path: Path) -> Path:
    return tmp_path / "embeddings" / "manifest.db"


def _make_manifest(tmp_path: Path) -> EmbeddingManifest:
    return EmbeddingManifest(_manifest_path(tmp_path))


def _vectors(rows: int) -> np.ndarray:
    base = np.linspace(
        0.0,
        1.0,
        num=rows * embedding_manifest.DEFAULT_DIMS,
        endpoint=False,
        dtype=np.float32,
    )
    return base.reshape(rows, embedding_manifest.DEFAULT_DIMS).astype(np.float16)


def _unit_inputs(
    rows: int,
    *,
    start: int = 0,
    corpus: str = "demo",
) -> list[UnitSpecInput]:
    return [
        UnitSpecInput(
            unit_key=f"{corpus}:{start + index}",
            parent_key=f"parent-{(start + index) // 5}",
            text_sha256=f"sha-{start + index}",
            model="bge-m3-mlx-fp16",
        )
        for index in range(rows)
    ]


def test_schema_init_creates_expected_tables_and_indexes(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    manifest.close()

    conn = sqlite3.connect(_manifest_path(tmp_path))
    rows = conn.execute(
        """
        SELECT type, name
        FROM sqlite_master
        WHERE name IN (
            'embedding_shards',
            'embedding_units',
            'idx_embshards_corpus',
            'idx_embunits_corpus',
            'idx_embunits_parent',
            'idx_embunits_shard'
        )
        ORDER BY name
        """
    ).fetchall()
    conn.close()

    assert rows == [
        ("table", "embedding_shards"),
        ("table", "embedding_units"),
        ("index", "idx_embshards_corpus"),
        ("index", "idx_embunits_corpus"),
        ("index", "idx_embunits_parent"),
        ("index", "idx_embunits_shard"),
    ]

    reopened = _make_manifest(tmp_path)
    reopened.close()

    conn = sqlite3.connect(_manifest_path(tmp_path))
    counts = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name LIKE 'idx_emb%' OR name LIKE 'embedding_%'"
    ).fetchone()
    conn.close()
    assert counts == (6,)


def test_append_shard_writes_manifest_rows_and_npy_file(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)

    shard_id = append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(100),
        unit_specs=_unit_inputs(100, corpus="textbook_sections"),
    )

    stats = manifest.stats()
    shard_map = manifest.shard_map_for_corpus("textbook_sections")
    manifest.close()

    assert shard_id in shard_map
    assert stats["corpora"]["textbook_sections"]["shards"] == 1
    assert stats["corpora"]["textbook_sections"]["units"] == 100

    npy_path = shard_map[shard_id]
    assert npy_path.exists()

    stored = np.load(npy_path)
    assert stored.shape == (100, embedding_manifest.DEFAULT_DIMS)
    assert stored.dtype == np.float16

    conn = sqlite3.connect(_manifest_path(tmp_path))
    shard_count = conn.execute("SELECT COUNT(*) FROM embedding_shards").fetchone()[0]
    unit_count = conn.execute("SELECT COUNT(*) FROM embedding_units").fetchone()[0]
    conn.close()

    assert shard_count == 1
    assert unit_count == 100


def test_append_shard_commit_failure_cleans_renamed_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original_connect = sqlite3.connect

    class FailingCommitConnection(sqlite3.Connection):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            self.fail_commit = False

        def execute(self, sql: str, parameters=(), /):
            normalized = " ".join(sql.split())
            if normalized.startswith("INSERT INTO embedding_shards"):
                self.fail_commit = True
            return super().execute(sql, parameters)

        def commit(self) -> None:
            if self.fail_commit:
                self.fail_commit = False
                raise sqlite3.OperationalError("synthetic commit failure")
            return super().commit()

    def failing_connect(*args, **kwargs):
        kwargs["factory"] = FailingCommitConnection
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(embedding_manifest.sqlite3, "connect", failing_connect)

    manifest = _make_manifest(tmp_path)
    with pytest.raises(sqlite3.OperationalError, match="synthetic commit failure"):
        append_shard(
            manifest,
            corpus="modern_literary",
            vectors=_vectors(12),
            unit_specs=_unit_inputs(12, corpus="modern_literary"),
        )

    shard_path = manifest.embeddings_dir / "modern_literary" / "shard-000001.npy"
    manifest.close()

    conn = original_connect(_manifest_path(tmp_path))
    shard_count = conn.execute("SELECT COUNT(*) FROM embedding_shards").fetchone()[0]
    conn.close()

    print(f"fault injection cleanup: file_exists={shard_path.exists()} shard_rows={shard_count}")
    assert not shard_path.exists()
    assert shard_count == 0


def test_filter_new_or_changed_classifies_new_and_stale_keys(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    append_shard(
        manifest,
        corpus="external",
        vectors=_vectors(50),
        unit_specs=_unit_inputs(50, corpus="external"),
    )

    candidates = [(f"external:{index}", f"sha-{index}") for index in range(30)]
    candidates.extend((f"external:{index}", f"changed-sha-{index}") for index in range(30, 45))
    candidates.extend((f"external:{index}", f"sha-{index}") for index in range(50, 80))

    new_keys, stale_keys = filter_new_or_changed(manifest, corpus="external", candidates=candidates)
    manifest.close()

    assert new_keys == [f"external:{index}" for index in range(50, 80)]
    assert stale_keys == [f"external:{index}" for index in range(30, 45)]


def test_active_units_for_corpus_excludes_deleted_rows(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    append_shard(
        manifest,
        corpus="wikipedia",
        vectors=_vectors(50),
        unit_specs=_unit_inputs(50, corpus="wikipedia"),
    )

    deleted_keys = [f"wikipedia:{index}" for index in range(10)]
    for unit_key in deleted_keys:
        manifest.mark_deleted(unit_key)

    active_units = manifest.active_units_for_corpus("wikipedia")
    manifest.close()

    assert len(active_units) == 40
    assert {row.unit_key for row in active_units}.isdisjoint(deleted_keys)


def test_shard_map_for_corpus_returns_absolute_paths(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    shard_ids = [
        append_shard(manifest, corpus="archaic_literary", vectors=_vectors(10), unit_specs=_unit_inputs(10, start=0, corpus="archaic_literary")),
        append_shard(manifest, corpus="archaic_literary", vectors=_vectors(20), unit_specs=_unit_inputs(20, start=10, corpus="archaic_literary")),
        append_shard(manifest, corpus="archaic_literary", vectors=_vectors(30), unit_specs=_unit_inputs(30, start=30, corpus="archaic_literary")),
    ]

    shard_map = manifest.shard_map_for_corpus("archaic_literary")
    manifest.close()

    assert list(shard_map) == shard_ids
    assert len(shard_map) == 3
    assert all(path.is_absolute() and path.exists() for path in shard_map.values())


def test_vacuum_orphaned_shards_removes_deleted_only_shard(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    first_shard = append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(10),
        unit_specs=_unit_inputs(10, corpus="textbook_sections"),
    )
    second_shard = append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(10),
        unit_specs=_unit_inputs(10, start=10, corpus="textbook_sections"),
    )

    first_units = [f"textbook_sections:{index}" for index in range(10)]
    for unit_key in first_units:
        manifest.mark_deleted(unit_key)

    removed = manifest.vacuum_orphaned_shards()
    shard_map = manifest.shard_map_for_corpus("textbook_sections")
    manifest.close()

    assert removed == 1
    assert first_shard not in shard_map
    assert second_shard in shard_map
    assert not (tmp_path / "embeddings" / "textbook_sections" / "shard-000001.npy").exists()

    conn = sqlite3.connect(_manifest_path(tmp_path))
    shard_rows = conn.execute("SELECT COUNT(*) FROM embedding_shards").fetchone()[0]
    unit_rows = conn.execute("SELECT COUNT(*) FROM embedding_units").fetchone()[0]
    conn.close()

    assert shard_rows == 1
    assert unit_rows == 10
