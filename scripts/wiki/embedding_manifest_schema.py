"""Schema for the embedding manifest database."""

from __future__ import annotations

EMBEDDING_MANIFEST_DDL = """
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
