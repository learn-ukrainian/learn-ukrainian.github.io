from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from wiki.embedding_manifest import (
    LEGACY_SHIPPED_CONFIG,
    EmbeddingManifest,
    EncoderConfig,
    UnitSpecInput,
    append_shard,
    filter_new_or_changed,
)
from wiki.embedding_manifest_schema import (
    LEGACY_CHUNK_POLICY_VERSION,
    LEGACY_INDEX_MAX_LENGTH,
    LEGACY_POOLING_MODE,
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
        )
        for index in range(rows)
    ]


def test_runtime_default_config_matches_legacy_shipped() -> None:
    """``current_encoder_config`` must produce ``LEGACY_SHIPPED_CONFIG``
    on the post-#1553-step-0, pre-#1553-step-1 main branch.

    Why: opening a pre-existing manifest after merging step 0 must
    NOT mark every existing row as stale (which would force a full
    re-encode). That only works if the runtime's per-corpus config
    matches the legacy stamp values applied by the migration. If
    the runtime drifts (e.g. someone bumps INDEX_MAX_LENGTH in the
    same commit as a chunker change without bumping the policy
    version), this test fails loudly.

    Codex review (msg #455): "A small
    current_encoder_config(...) == LEGACY_SHIPPED_CONFIG test for
    step 0 would also catch accidental drift between runtime
    defaults and migration defaults."
    """

    from wiki.dense_rerank import current_encoder_config

    for corpus in (
        "textbook_sections",
        "modern_literary",
        "archaic_literary",
        "external",
        "wikipedia",
        "ukrainian_wiki",
    ):
        assert current_encoder_config(corpus) == LEGACY_SHIPPED_CONFIG, (
            f"current_encoder_config({corpus!r}) drifted from "
            f"LEGACY_SHIPPED_CONFIG; this WILL force a full re-encode "
            f"of corpus {corpus!r} on next open. Either bump "
            f"chunk_policy_version intentionally or revert the drift."
        )


def test_legacy_shipped_config_matches_schema_defaults() -> None:
    """``LEGACY_SHIPPED_CONFIG`` must mirror the schema-baked defaults.

    The ALTER TABLE in ``_ensure_schema_v2`` stamps pre-existing v1
    rows with the schema-level ``LEGACY_*`` constants. If those drift
    from ``LEGACY_SHIPPED_CONFIG``, ``filter_new_or_changed`` will see
    legacy rows as stale on first open and trigger a full re-encode.
    """

    assert LEGACY_SHIPPED_CONFIG.index_max_length == LEGACY_INDEX_MAX_LENGTH
    assert LEGACY_SHIPPED_CONFIG.chunk_policy_version == LEGACY_CHUNK_POLICY_VERSION
    assert LEGACY_SHIPPED_CONFIG.pooling_mode == LEGACY_POOLING_MODE


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
            'idx_embunits_shard',
            'idx_embunits_config'
        )
        ORDER BY name
        """
    ).fetchall()
    conn.close()

    assert rows == [
        ("table", "embedding_shards"),
        ("table", "embedding_units"),
        ("index", "idx_embshards_corpus"),
        ("index", "idx_embunits_config"),
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
    # 2 tables + 5 indexes (incl. config index) — must be idempotent on reopen
    assert counts == (7,)


def test_v2_columns_present_with_legacy_defaults_on_fresh_init(tmp_path: Path) -> None:
    """A fresh manifest comes up with the v2 schema directly."""

    manifest = _make_manifest(tmp_path)
    manifest.close()

    conn = sqlite3.connect(_manifest_path(tmp_path))
    columns = {row[1]: row[4] for row in conn.execute("PRAGMA table_info(embedding_units)").fetchall()}
    conn.close()

    assert "index_max_length" in columns
    assert "chunk_policy_version" in columns
    assert "pooling_mode" in columns
    assert columns["index_max_length"] == str(LEGACY_INDEX_MAX_LENGTH)
    assert columns["chunk_policy_version"] == f"'{LEGACY_CHUNK_POLICY_VERSION}'"
    assert columns["pooling_mode"] == f"'{LEGACY_POOLING_MODE}'"


def test_partial_v2_schema_migration_completes_missing_columns(tmp_path: Path) -> None:
    """A manifest stuck mid-migration must finish on next open.

    Real-world: a previous run added one or two of the v2 columns
    but crashed before adding the rest (or before creating the
    config index). Opening the file again must complete the work,
    not bail on a duplicate-column error.
    """

    db_path = _manifest_path(tmp_path)
    db_path.parent.mkdir(parents=True)

    legacy_conn = sqlite3.connect(str(db_path))
    legacy_conn.executescript(
        """
        CREATE TABLE embedding_shards (
            shard_id INTEGER PRIMARY KEY AUTOINCREMENT,
            corpus TEXT NOT NULL,
            path TEXT NOT NULL,
            rows INTEGER NOT NULL,
            dims INTEGER NOT NULL DEFAULT 1024,
            dtype TEXT NOT NULL DEFAULT 'float16',
            committed_at TEXT NOT NULL
        );

        CREATE TABLE embedding_units (
            unit_key TEXT PRIMARY KEY,
            corpus TEXT NOT NULL,
            parent_key TEXT,
            text_sha256 TEXT NOT NULL,
            model TEXT NOT NULL,
            shard_id INTEGER NOT NULL REFERENCES embedding_shards(shard_id),
            row_idx INTEGER NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        """
    )
    # Only add the FIRST v2 column (simulates partial migration).
    legacy_conn.execute(
        f"ALTER TABLE embedding_units ADD COLUMN index_max_length "
        f"INTEGER NOT NULL DEFAULT {LEGACY_INDEX_MAX_LENGTH}"
    )
    legacy_conn.commit()
    legacy_conn.close()

    # Open with the upgraded code — must complete columns 2+3
    # without crashing.
    manifest = _make_manifest(tmp_path)
    try:
        # All v2 columns now exist, including the index.
        conn = sqlite3.connect(str(db_path))
        column_names = {
            row[1] for row in conn.execute("PRAGMA table_info(embedding_units)").fetchall()
        }
        index_names = {
            row[1] for row in conn.execute(
                "SELECT type, name FROM sqlite_master WHERE name = 'idx_embunits_config'"
            ).fetchall()
        }
        conn.close()
        assert {"index_max_length", "chunk_policy_version", "pooling_mode"} <= column_names
        assert "idx_embunits_config" in index_names
    finally:
        manifest.close()


def test_concurrent_migration_does_not_race(tmp_path: Path) -> None:
    """Two processes opening a v1 manifest simultaneously must not
    both attempt the same ALTER (would crash with duplicate-column).

    Codex review (msg #455) flagged the v1-locking PRAGMA + ALTER
    pattern as concurrency-unsafe. Fix wraps schema check + ALTERs
    in BEGIN IMMEDIATE; the second writer blocks until the first
    commits, then re-reads PRAGMA and sees the new columns.

    Threads share the SQLite file but each opens its own connection
    — same race surface as separate processes for this purpose.
    """

    import threading

    db_path = _manifest_path(tmp_path)
    db_path.parent.mkdir(parents=True)

    # Pre-create a v1-shaped manifest with a representative row.
    legacy_conn = sqlite3.connect(str(db_path))
    legacy_conn.executescript(
        """
        CREATE TABLE embedding_shards (
            shard_id INTEGER PRIMARY KEY AUTOINCREMENT,
            corpus TEXT NOT NULL,
            path TEXT NOT NULL,
            rows INTEGER NOT NULL,
            dims INTEGER NOT NULL DEFAULT 1024,
            dtype TEXT NOT NULL DEFAULT 'float16',
            committed_at TEXT NOT NULL
        );

        CREATE TABLE embedding_units (
            unit_key TEXT PRIMARY KEY,
            corpus TEXT NOT NULL,
            parent_key TEXT,
            text_sha256 TEXT NOT NULL,
            model TEXT NOT NULL,
            shard_id INTEGER NOT NULL REFERENCES embedding_shards(shard_id),
            row_idx INTEGER NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        );
        """
    )
    legacy_conn.commit()
    legacy_conn.close()

    barrier = threading.Barrier(parties=4)
    failures: list[BaseException] = []
    manifests: list[EmbeddingManifest] = []
    lock = threading.Lock()

    def opener() -> None:
        try:
            barrier.wait()  # release all 4 threads simultaneously
            m = EmbeddingManifest(db_path)
            with lock:
                manifests.append(m)
        except BaseException as exc:
            with lock:
                failures.append(exc)

    threads = [threading.Thread(target=opener) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    for m in manifests:
        m.close()

    assert not failures, f"concurrent migration raced: {failures!r}"

    # Verify final state: all 3 v2 columns present, manifest queryable.
    conn = sqlite3.connect(str(db_path))
    column_names = {
        row[1] for row in conn.execute("PRAGMA table_info(embedding_units)").fetchall()
    }
    conn.close()
    assert {"index_max_length", "chunk_policy_version", "pooling_mode"} <= column_names


def test_v1_to_v2_migration_stamps_legacy_rows(tmp_path: Path) -> None:
    """Pre-#1553 manifests must upgrade in place without losing rows.

    Builds a v1-shaped manifest by hand (no v2 columns), inserts
    representative shard + unit rows, opens the file with the
    upgraded code, and asserts:

    1. The v2 columns now exist.
    2. The legacy unit row inherits ``LEGACY_SHIPPED_CONFIG`` values.
    3. ``filter_new_or_changed`` with the legacy config sees the row
       as up-to-date (not stale, not new) — no spurious re-encode.
    """

    db_path = _manifest_path(tmp_path)
    db_path.parent.mkdir(parents=True)

    legacy_conn = sqlite3.connect(str(db_path))
    legacy_conn.executescript(
        """
        CREATE TABLE embedding_shards (
            shard_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            corpus       TEXT NOT NULL,
            path         TEXT NOT NULL,
            rows         INTEGER NOT NULL,
            dims         INTEGER NOT NULL DEFAULT 1024,
            dtype        TEXT NOT NULL DEFAULT 'float16',
            committed_at TEXT NOT NULL
        );
        CREATE INDEX idx_embshards_corpus ON embedding_shards(corpus);

        CREATE TABLE embedding_units (
            unit_key     TEXT PRIMARY KEY,
            corpus       TEXT NOT NULL,
            parent_key   TEXT,
            text_sha256  TEXT NOT NULL,
            model        TEXT NOT NULL,
            shard_id     INTEGER NOT NULL REFERENCES embedding_shards(shard_id),
            row_idx      INTEGER NOT NULL,
            deleted      INTEGER NOT NULL DEFAULT 0,
            updated_at   TEXT NOT NULL
        );
        CREATE INDEX idx_embunits_corpus ON embedding_units(corpus, deleted);
        CREATE INDEX idx_embunits_parent ON embedding_units(corpus, parent_key);
        CREATE INDEX idx_embunits_shard ON embedding_units(shard_id);
        """
    )
    legacy_conn.execute(
        "INSERT INTO embedding_shards (corpus, path, rows, committed_at) VALUES (?, ?, ?, ?)",
        ("textbook_sections", "textbook_sections/shard-000001.npy", 1, "2026-04-19T12:00:00Z"),
    )
    legacy_conn.execute(
        """
        INSERT INTO embedding_units (
            unit_key, corpus, parent_key, text_sha256, model, shard_id, row_idx, updated_at
        ) VALUES (?, ?, ?, ?, ?, 1, 0, ?)
        """,
        (
            "textbook_sections:42",
            "textbook_sections",
            "ukrlit-grade-7",
            "sha-legacy",
            "bge-m3-mlx-fp16",
            "2026-04-19T12:00:00Z",
        ),
    )
    legacy_conn.commit()
    legacy_conn.close()

    # Open with upgraded code — migration runs implicitly.
    manifest = _make_manifest(tmp_path)
    try:
        new_keys, stale_keys = filter_new_or_changed(
            manifest,
            corpus="textbook_sections",
            candidates=[("textbook_sections:42", "sha-legacy")],
            expected_config=LEGACY_SHIPPED_CONFIG,
        )
        # Legacy row, queried with legacy config -> neither new nor stale.
        assert new_keys == []
        assert stale_keys == []

        row = manifest.get_unit("textbook_sections:42")
        assert row is not None
        assert row.index_max_length == LEGACY_INDEX_MAX_LENGTH
        assert row.chunk_policy_version == LEGACY_CHUNK_POLICY_VERSION
        assert row.pooling_mode == LEGACY_POOLING_MODE
    finally:
        manifest.close()

    conn = sqlite3.connect(str(db_path))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(embedding_units)").fetchall()}
    conn.close()
    assert {"index_max_length", "chunk_policy_version", "pooling_mode"} <= columns


def test_append_shard_writes_manifest_rows_and_npy_file(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)

    shard_id = append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(100),
        unit_specs=_unit_inputs(100, corpus="textbook_sections"),
        encoder_config=LEGACY_SHIPPED_CONFIG,
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


def test_append_shard_stamps_encoder_config_on_every_row(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    custom_config = EncoderConfig(
        model="bge-m3-mlx-fp16",
        index_max_length=2048,
        chunk_policy_version="textbook:v2-paragraph-aware",
        pooling_mode="cls",
    )

    append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(5),
        unit_specs=_unit_inputs(5, corpus="textbook_sections"),
        encoder_config=custom_config,
    )

    rows = manifest.active_units_for_corpus("textbook_sections")
    manifest.close()

    assert len(rows) == 5
    for row in rows:
        assert row.model == custom_config.model
        assert row.index_max_length == custom_config.index_max_length
        assert row.chunk_policy_version == custom_config.chunk_policy_version
        assert row.pooling_mode == custom_config.pooling_mode


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
            encoder_config=LEGACY_SHIPPED_CONFIG,
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
        encoder_config=LEGACY_SHIPPED_CONFIG,
    )

    candidates = [(f"external:{index}", f"sha-{index}") for index in range(30)]
    candidates.extend((f"external:{index}", f"changed-sha-{index}") for index in range(30, 45))
    candidates.extend((f"external:{index}", f"sha-{index}") for index in range(50, 80))

    new_keys, stale_keys = filter_new_or_changed(
        manifest,
        corpus="external",
        candidates=candidates,
        expected_config=LEGACY_SHIPPED_CONFIG,
    )
    manifest.close()

    assert new_keys == [f"external:{index}" for index in range(50, 80)]
    assert stale_keys == [f"external:{index}" for index in range(30, 45)]


@pytest.mark.parametrize(
    "config_field",
    ["model", "index_max_length", "chunk_policy_version", "pooling_mode"],
)
def test_filter_marks_stale_when_any_config_field_differs(tmp_path: Path, config_field: str) -> None:
    """Each component of EncoderConfig must independently force re-encode.

    Regression for the #1553 root cause: pre-fix manifest only
    compared (unit_key, text_sha256), so bumping ``INDEX_MAX_LENGTH``
    or swapping models silently produced a mixed-config index.
    Codex's review asked specifically for the model-field case
    because that bug exists today, before the chunking work even lands.
    """

    manifest = _make_manifest(tmp_path)
    append_shard(
        manifest,
        corpus="external",
        vectors=_vectors(3),
        unit_specs=_unit_inputs(3, corpus="external"),
        encoder_config=LEGACY_SHIPPED_CONFIG,
    )

    overrides = {
        "model": "another-encoder-v1",
        "index_max_length": 2048,
        "chunk_policy_version": "external:v2-paragraph-aware",
        "pooling_mode": "mean",
    }
    different_config = EncoderConfig(
        model=overrides[config_field] if config_field == "model" else LEGACY_SHIPPED_CONFIG.model,
        index_max_length=overrides[config_field] if config_field == "index_max_length" else LEGACY_SHIPPED_CONFIG.index_max_length,
        chunk_policy_version=overrides[config_field] if config_field == "chunk_policy_version" else LEGACY_SHIPPED_CONFIG.chunk_policy_version,
        pooling_mode=overrides[config_field] if config_field == "pooling_mode" else LEGACY_SHIPPED_CONFIG.pooling_mode,
    )

    candidates = [(f"external:{index}", f"sha-{index}") for index in range(3)]

    # Same config -> nothing stale.
    new_keys, stale_keys = filter_new_or_changed(
        manifest,
        corpus="external",
        candidates=candidates,
        expected_config=LEGACY_SHIPPED_CONFIG,
    )
    assert new_keys == []
    assert stale_keys == []

    # Different config in any one field -> all stale.
    new_keys, stale_keys = filter_new_or_changed(
        manifest,
        corpus="external",
        candidates=candidates,
        expected_config=different_config,
    )
    manifest.close()
    assert new_keys == []
    assert stale_keys == [f"external:{index}" for index in range(3)]


def test_active_units_for_corpus_excludes_deleted_rows(tmp_path: Path) -> None:
    manifest = _make_manifest(tmp_path)
    append_shard(
        manifest,
        corpus="wikipedia",
        vectors=_vectors(50),
        unit_specs=_unit_inputs(50, corpus="wikipedia"),
        encoder_config=LEGACY_SHIPPED_CONFIG,
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
        append_shard(
            manifest,
            corpus="archaic_literary",
            vectors=_vectors(10),
            unit_specs=_unit_inputs(10, start=0, corpus="archaic_literary"),
            encoder_config=LEGACY_SHIPPED_CONFIG,
        ),
        append_shard(
            manifest,
            corpus="archaic_literary",
            vectors=_vectors(20),
            unit_specs=_unit_inputs(20, start=10, corpus="archaic_literary"),
            encoder_config=LEGACY_SHIPPED_CONFIG,
        ),
        append_shard(
            manifest,
            corpus="archaic_literary",
            vectors=_vectors(30),
            unit_specs=_unit_inputs(30, start=30, corpus="archaic_literary"),
            encoder_config=LEGACY_SHIPPED_CONFIG,
        ),
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
        encoder_config=LEGACY_SHIPPED_CONFIG,
    )
    second_shard = append_shard(
        manifest,
        corpus="textbook_sections",
        vectors=_vectors(10),
        unit_specs=_unit_inputs(10, start=10, corpus="textbook_sections"),
        encoder_config=LEGACY_SHIPPED_CONFIG,
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
