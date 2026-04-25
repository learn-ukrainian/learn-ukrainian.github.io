"""Schema for the embedding manifest database.

Schema versions:
  v1 (#1348): unit identity = (unit_key, text_sha256, model)
              No versioning for index_max_length / chunk_policy / pooling_mode.
  v2 (#1553): unit identity carries the full encoder config so that
              changes to INDEX_MAX_LENGTH, chunk policy, or pooling mode
              force a re-encode instead of producing a silently mixed
              index. Pre-existing v1 rows are stamped at __init__-time
              with LEGACY_SHIPPED_CONFIG defaults so the upgrade is
              non-destructive.
"""

from __future__ import annotations

#: Defaults baked into the v2 ALTER TABLE so legacy rows match the
#: actually-shipped #1348 configuration. These constants MUST mirror
#: ``LEGACY_SHIPPED_CONFIG`` in ``embedding_manifest`` — keep them in
#: sync via the test in ``tests/wiki/test_embedding_manifest.py``.
LEGACY_INDEX_MAX_LENGTH = 512
LEGACY_CHUNK_POLICY_VERSION = "legacy:v1-shipped-1348"
LEGACY_POOLING_MODE = "cls"


#: v1 schema (#1348) — base shape created on a fresh manifest. The
#: v2 columns and config index are added by the migration logic in
#: ``EmbeddingManifest._ensure_schema_v2`` after this DDL runs, so the
#: same code path works whether opening a fresh or pre-existing DB.
EMBEDDING_MANIFEST_DDL_V1 = """
CREATE TABLE IF NOT EXISTS embedding_shards (
    shard_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    corpus       TEXT NOT NULL,
    path         TEXT NOT NULL,
    rows         INTEGER NOT NULL,
    dims         INTEGER NOT NULL DEFAULT 1024,
    dtype        TEXT NOT NULL DEFAULT 'float16',
    committed_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_embshards_corpus ON embedding_shards(corpus);

CREATE TABLE IF NOT EXISTS embedding_units (
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
CREATE INDEX IF NOT EXISTS idx_embunits_corpus ON embedding_units(corpus, deleted);
CREATE INDEX IF NOT EXISTS idx_embunits_parent ON embedding_units(corpus, parent_key);
CREATE INDEX IF NOT EXISTS idx_embunits_shard ON embedding_units(shard_id);
""".strip()

#: Backwards-compatibility alias — older callers used this name.
EMBEDDING_MANIFEST_DDL = EMBEDDING_MANIFEST_DDL_V1


#: v2 columns added to ``embedding_units`` by the migration logic.
#: Tuple of ``(name, type, default_sql)`` — the migration ALTERs the
#: live table when these are missing on open.
V2_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("index_max_length", "INTEGER NOT NULL", str(LEGACY_INDEX_MAX_LENGTH)),
    ("chunk_policy_version", "TEXT NOT NULL", f"'{LEGACY_CHUNK_POLICY_VERSION}'"),
    ("pooling_mode", "TEXT NOT NULL", f"'{LEGACY_POOLING_MODE}'"),
)
