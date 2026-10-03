-- Schema-only snapshot from live sqlite_master (read-only); no corpus rows.
CREATE TABLE literary_texts (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    author TEXT DEFAULT '',
    work TEXT DEFAULT '',
    work_id TEXT DEFAULT '',
    year INTEGER,
    genre TEXT DEFAULT '',
    language_period TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
, source_url TEXT);

CREATE TABLE textbook_sections (
    section_id INTEGER PRIMARY KEY,
    source_file TEXT NOT NULL,
    grade INTEGER NOT NULL,
    section_title TEXT NOT NULL,
    section_number TEXT,
    page_start INTEGER,
    page_end INTEGER,
    chunk_count INTEGER NOT NULL,
    full_text TEXT NOT NULL,
    UNIQUE (source_file, section_title)
);

CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    grade TEXT DEFAULT '',
    author TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
, parent_section_id INTEGER REFERENCES textbook_sections(section_id), author_uk TEXT DEFAULT '', subject TEXT);

CREATE VIRTUAL TABLE textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);

CREATE INDEX idx_sections_grade ON textbook_sections (grade);

CREATE INDEX idx_sections_source_grade ON textbook_sections (source_file, grade);

CREATE INDEX idx_textbooks_chunk_id ON textbooks(chunk_id);

CREATE INDEX idx_textbooks_parent ON textbooks (parent_section_id);

CREATE INDEX idx_textbooks_subject ON textbooks(subject);

CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
