-- Rollback for: 2026-05-04-1659-sum11-sovietization-flag.sql
-- Issue: #1659
--
-- SQLite < 3.35 does not support DROP COLUMN; this rollback uses the
-- table-rebuild dance (CREATE temp + INSERT + DROP + RENAME). Modern SQLite
-- (≥ 3.35, May 2021) supports DROP COLUMN directly. Both paths preserved.
--
-- Path A — modern SQLite (≥ 3.35):
--   ALTER TABLE sum11 DROP COLUMN sovietization_keywords;
--   ALTER TABLE sum11 DROP COLUMN sovietization_risk;
--   DROP INDEX IF EXISTS idx_sum11_sovietization;
--
-- Path B — legacy SQLite (< 3.35):
--   BEGIN TRANSACTION;
--   CREATE TABLE sum11_new (
--       id INTEGER PRIMARY KEY,
--       word TEXT NOT NULL,
--       definition TEXT NOT NULL DEFAULT '',
--       text TEXT NOT NULL DEFAULT '',
--       source TEXT DEFAULT ''
--   );
--   INSERT INTO sum11_new (id, word, definition, text, source)
--       SELECT id, word, definition, text, source FROM sum11;
--   DROP TABLE sum11;
--   ALTER TABLE sum11_new RENAME TO sum11;
--   CREATE INDEX idx_sum11_word ON sum11(word COLLATE NOCASE);
--   COMMIT;

DROP INDEX IF EXISTS idx_sum11_sovietization;
ALTER TABLE sum11 DROP COLUMN sovietization_keywords;
ALTER TABLE sum11 DROP COLUMN sovietization_risk;
