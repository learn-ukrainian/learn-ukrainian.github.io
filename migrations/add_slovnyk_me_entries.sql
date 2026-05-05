-- Migration: add curated slovnyk.me verification snapshots
-- Issue: #1715
--
-- This table is intentionally a bounded per-word / URL-reference store, not
-- a bulk mirror of slovnyk.me. See docs/audits/slovnyk-me-ingestion-feasibility.md.

CREATE TABLE IF NOT EXISTS slovnyk_me_entries (
    id INTEGER PRIMARY KEY,
    query TEXT NOT NULL DEFAULT '',
    word TEXT NOT NULL,
    normalized_word TEXT NOT NULL DEFAULT '',
    dictionary_slug TEXT NOT NULL,
    dictionary_label TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'slovnyk_me',
    source_url TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    snippet TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    is_modern INTEGER NOT NULL DEFAULT 0,
    is_dialect INTEGER NOT NULL DEFAULT 0,
    is_russianism INTEGER NOT NULL DEFAULT 0,
    sovietization_risk INTEGER NOT NULL DEFAULT 0,
    sovietization_keywords TEXT NOT NULL DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT '',
    UNIQUE(normalized_word, dictionary_slug, source_url)
);

CREATE VIRTUAL TABLE IF NOT EXISTS slovnyk_me_entries_fts USING fts5(
    word,
    title,
    snippet,
    text,
    dictionary_label,
    content='slovnyk_me_entries',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_ai
AFTER INSERT ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;

CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_ad
AFTER DELETE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
END;

CREATE TRIGGER IF NOT EXISTS slovnyk_me_entries_au
AFTER UPDATE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;

CREATE INDEX IF NOT EXISTS idx_slovnyk_me_word
    ON slovnyk_me_entries(normalized_word COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_dict
    ON slovnyk_me_entries(dictionary_slug);
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_modern
    ON slovnyk_me_entries(is_modern) WHERE is_modern = 1;
CREATE INDEX IF NOT EXISTS idx_slovnyk_me_dialect
    ON slovnyk_me_entries(is_dialect) WHERE is_dialect = 1;
