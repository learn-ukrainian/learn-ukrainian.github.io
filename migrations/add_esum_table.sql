CREATE VIRTUAL TABLE IF NOT EXISTS esum_etymology USING fts5(
    lemma,
    etymology_text,
    cognates,
    vol UNINDEXED,
    page UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 0'
);

CREATE TABLE IF NOT EXISTS esum_etymology_meta (
    id INTEGER PRIMARY KEY,
    lemma TEXT NOT NULL,
    vol INTEGER NOT NULL,
    page INTEGER NOT NULL,
    entry_hash TEXT NOT NULL DEFAULT '',
    etymology_text TEXT NOT NULL,
    cognates TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'ЕСУМ',
    UNIQUE(lemma, vol, page, entry_hash)
);

CREATE INDEX IF NOT EXISTS idx_esum_etymology_meta_lemma
ON esum_etymology_meta(lemma COLLATE NOCASE);

CREATE INDEX IF NOT EXISTS idx_esum_etymology_meta_vol_page
ON esum_etymology_meta(vol, page);
