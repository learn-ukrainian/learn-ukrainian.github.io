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

CREATE VIRTUAL TABLE literary_fts USING fts5(
    title, text, content='literary_texts', content_rowid='id', tokenize='unicode61'
);

CREATE TABLE external_articles (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    url_normalized TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    domain TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0,
    channel_id TEXT DEFAULT '',
    speaker TEXT DEFAULT '',
    register_tag TEXT DEFAULT '',
    decolonization_tag TEXT DEFAULT '',
    quality_tier INTEGER DEFAULT 2,
    publish_date TEXT DEFAULT '',
    duration_s INTEGER DEFAULT 0,
    chunk_start_ts INTEGER,
    chunk_end_ts INTEGER,
    video_id TEXT DEFAULT ''
);

CREATE VIRTUAL TABLE external_fts USING fts5(
    title, text, speaker, content='external_articles', content_rowid='id', tokenize='unicode61'
);

CREATE TABLE wikipedia (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    char_count INTEGER DEFAULT 0,
    fetched_at TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE wikipedia_fts USING fts5(
    title, text, content='wikipedia', content_rowid='id', tokenize='unicode61'
);

CREATE TABLE ukrainian_wiki (
    id INTEGER PRIMARY KEY,
    passage_id TEXT NOT NULL UNIQUE,
    article_slug TEXT NOT NULL,
    article_title TEXT NOT NULL DEFAULT '',
    article_path TEXT NOT NULL DEFAULT '',
    track TEXT NOT NULL DEFAULT '',
    heading_path TEXT NOT NULL DEFAULT '',
    section_path TEXT NOT NULL DEFAULT '',
    chunk_index INTEGER NOT NULL DEFAULT 0,
    paragraph_start INTEGER NOT NULL DEFAULT 0,
    paragraph_end INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    text TEXT NOT NULL DEFAULT '',
    source_registry_path TEXT NOT NULL DEFAULT '',
    gate_report_json TEXT NOT NULL DEFAULT '',
    inserted_at TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE ukrainian_wiki_fts USING fts5(
    article_title, section_path, text,
    content='ukrainian_wiki',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE TABLE resource_catalogue (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    channel TEXT NOT NULL,
    season INTEGER,
    episode INTEGER,
    access TEXT NOT NULL,
    audio_access TEXT,
    notes_access TEXT,
    levels TEXT NOT NULL,
    modules TEXT NOT NULL,
    topics TEXT NOT NULL,
    source_files TEXT NOT NULL,
    source_entries TEXT NOT NULL,
    discovery_evidence TEXT NOT NULL,
    search_text TEXT NOT NULL,
    http_status INTEGER,
    checked_at TEXT,
    link_check TEXT NOT NULL
, letters TEXT NOT NULL DEFAULT '[]', letter_evidence TEXT NOT NULL DEFAULT '[]', access_evidence TEXT NOT NULL DEFAULT '[]');

CREATE VIRTUAL TABLE resource_catalogue_fts USING fts5(
    title, search_text, content='resource_catalogue', content_rowid='id',
    tokenize='unicode61'
);

CREATE TABLE puls_cefr (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    guideword TEXT DEFAULT '',
    level TEXT DEFAULT '',
    pos TEXT DEFAULT '',
    type TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE ua_gec_errors (
                id INTEGER PRIMARY KEY,
                error TEXT NOT NULL,
                correct TEXT NOT NULL,
                error_type TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                annotator_id TEXT NOT NULL,
                partition TEXT NOT NULL,
                is_native INTEGER,
                source_lang TEXT
            );

CREATE VIRTUAL TABLE ua_gec_errors_fts
            USING fts5(error, correct, error_type, content='ua_gec_errors', content_rowid='id', tokenize='unicode61');

CREATE TABLE style_guide (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    section TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
, word_lower TEXT, excerpt_full TEXT, page INTEGER, russianism_pattern TEXT);

CREATE TABLE sum11 (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
, sovietization_risk INTEGER NOT NULL DEFAULT 0, sovietization_keywords TEXT NOT NULL DEFAULT '');

CREATE TABLE grinchenko (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE VIRTUAL TABLE esum_etymology USING fts5(
    lemma,
    etymology_text,
    cognates,
    vol UNINDEXED,
    page UNINDEXED,
    tokenize = 'unicode61 remove_diacritics 0'
);

CREATE TABLE esum_etymology_meta (
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

CREATE TABLE frazeolohichnyi (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE ukrajinet (
    id INTEGER PRIMARY KEY,
    synset_id TEXT DEFAULT '',
    words TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE balla_en_uk (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definition TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE dmklinger_uk_en (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    pos TEXT DEFAULT '',
    translations TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE wiktionary (
    id INTEGER PRIMARY KEY,
    word TEXT NOT NULL,
    definitions TEXT DEFAULT '',
    synonyms TEXT DEFAULT '',
    antonyms TEXT DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source TEXT DEFAULT ''
);

CREATE TABLE "ulif_dictua_entries" (
    id INTEGER PRIMARY KEY,
    normalized_query TEXT NOT NULL,
    homonym_index INTEGER NOT NULL DEFAULT 1 CHECK (homonym_index >= 1),
    canonical_headword TEXT NOT NULL DEFAULT '',
    grammatical_label TEXT NOT NULL DEFAULT '',
    sense_gloss TEXT NOT NULL DEFAULT '',
    content_sha256 TEXT NOT NULL DEFAULT '',
    register_position TEXT NOT NULL DEFAULT '',
    homonym_checked INTEGER NOT NULL DEFAULT 0 CHECK (homonym_checked IN (0, 1)),
    raw_response_ref TEXT NOT NULL DEFAULT '',
    retrieved_at TEXT NOT NULL DEFAULT '',
    response_sha256 TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('ok', 'not_found', 'transient_error', 'parse_error')),
    UNIQUE(normalized_query, homonym_index)
);

CREATE TABLE ulif_dictua_sections (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES ulif_dictua_entries(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('paradigm', 'synonyms', 'antonyms', 'phraseology')),
    source_order INTEGER NOT NULL CHECK (source_order >= 0),
    sense_or_group_id TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL,
    UNIQUE(entry_id, kind, source_order)
);

CREATE TABLE ulif_forms (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES ulif_dictua_entries(id) ON DELETE CASCADE,
    entry_key TEXT NOT NULL,
    form_unstressed TEXT NOT NULL,
    form_stressed TEXT NOT NULL,
    stress_vowel_indices TEXT NOT NULL DEFAULT '[]',
    grammatical_tags TEXT NOT NULL DEFAULT '[]',
    unmapped_labels TEXT NOT NULL DEFAULT '[]',
    variant_order INTEGER NOT NULL DEFAULT 1,
    preposition TEXT NOT NULL DEFAULT '',
    marked_asterisk INTEGER NOT NULL DEFAULT 0,
    is_lemma INTEGER NOT NULL DEFAULT 0,
    is_invariable INTEGER NOT NULL DEFAULT 0,
    dual_stress_flag INTEGER NOT NULL DEFAULT 0,
    pedagogical_stressed_form TEXT NOT NULL DEFAULT '',
    source_page_sha256 TEXT NOT NULL DEFAULT '',
    parser_version TEXT NOT NULL DEFAULT '',
    source_entry_fingerprint TEXT NOT NULL DEFAULT ''
);

CREATE TABLE ulif_forms_build (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state TEXT NOT NULL CHECK (state IN ('building', 'complete', 'failed')),
    parser_version TEXT NOT NULL,
    total_entries INTEGER NOT NULL DEFAULT 0,
    entries_done INTEGER NOT NULL DEFAULT 0,
    entries_failed INTEGER NOT NULL DEFAULT 0,
    total_forms INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT '',
    finished_at TEXT NOT NULL DEFAULT '',
    source_fingerprint TEXT NOT NULL DEFAULT ''
);

CREATE TABLE sum20_articles (
    id INTEGER PRIMARY KEY,
    wordid INTEGER NOT NULL UNIQUE,
    normalized_lookup_key TEXT NOT NULL,
    headword TEXT NOT NULL,
    stressed_headword TEXT NOT NULL,
    pos TEXT NOT NULL DEFAULT '',
    grammar TEXT NOT NULL DEFAULT '',
    article_html TEXT NOT NULL,
    article_text TEXT NOT NULL,
    definition_text TEXT NOT NULL DEFAULT '',
    official_url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    quarantine_reason TEXT NOT NULL DEFAULT ''
);

CREATE VIRTUAL TABLE sum20_articles_fts USING fts5(
    normalized_lookup_key UNINDEXED,
    headword,
    definition_text,
    content='sum20_articles',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TABLE sum20_senses (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES sum20_articles(id) ON DELETE CASCADE,
    sense_order INTEGER NOT NULL,
    definition TEXT NOT NULL,
    register_labels TEXT NOT NULL DEFAULT '[]',
    UNIQUE(article_id, sense_order)
);

CREATE TABLE sum20_citations (
    id INTEGER PRIMARY KEY,
    article_id INTEGER NOT NULL REFERENCES sum20_articles(id) ON DELETE CASCADE,
    sense_ref INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    citation_text TEXT NOT NULL,
    parsed_bib_fields TEXT NOT NULL DEFAULT '{}',
    UNIQUE(article_id, "order")
);

CREATE TABLE slovnyk_me_entries (
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

CREATE VIRTUAL TABLE slovnyk_me_entries_fts USING fts5(
    word,
    title,
    snippet,
    text,
    dictionary_label,
    content='slovnyk_me_entries',
    content_rowid='id',
    tokenize='unicode61'
);

CREATE INDEX idx_sections_grade ON textbook_sections (grade);

CREATE INDEX idx_sections_source_grade ON textbook_sections (source_file, grade);

CREATE INDEX idx_textbooks_chunk_id ON textbooks(chunk_id);

CREATE INDEX idx_textbooks_parent ON textbooks (parent_section_id);

CREATE INDEX idx_textbooks_subject ON textbooks(subject);

CREATE INDEX idx_literary_chunk_id ON literary_texts(chunk_id);

CREATE INDEX idx_literary_period ON literary_texts(language_period);

CREATE INDEX idx_literary_period_genre ON literary_texts(language_period, genre);

CREATE INDEX idx_literary_work_id ON literary_texts(work_id);

CREATE INDEX idx_ext_channel ON external_articles(channel_id);

CREATE INDEX idx_ext_quality ON external_articles(quality_tier);

CREATE INDEX idx_ext_url ON external_articles(url);

CREATE INDEX idx_ext_url_norm ON external_articles(url_normalized);

CREATE INDEX idx_wiki_title ON wikipedia(title);

CREATE INDEX idx_ukrainian_wiki_section ON ukrainian_wiki(article_slug, paragraph_start);

CREATE INDEX idx_ukrainian_wiki_slug ON ukrainian_wiki(article_slug);

CREATE INDEX idx_puls_level ON puls_cefr(level);

CREATE INDEX idx_puls_word ON puls_cefr(word COLLATE NOCASE);

CREATE INDEX idx_style_word ON style_guide(word COLLATE NOCASE);

CREATE UNIQUE INDEX idx_style_guide_word_page ON style_guide(word, page);

CREATE INDEX idx_sum11_sovietization ON sum11(sovietization_risk) WHERE sovietization_risk > 0;

CREATE INDEX idx_sum11_word ON sum11(word COLLATE NOCASE);

CREATE INDEX idx_grinchenko_word ON grinchenko(word COLLATE NOCASE);

CREATE INDEX idx_esum_etymology_meta_lemma
ON esum_etymology_meta(lemma COLLATE NOCASE);

CREATE INDEX idx_esum_etymology_meta_vol_page
ON esum_etymology_meta(vol, page);

CREATE INDEX idx_fraz_word ON frazeolohichnyi(word COLLATE NOCASE);

CREATE INDEX idx_ukrajinet_words ON ukrajinet(words COLLATE NOCASE);

CREATE INDEX idx_balla_word ON balla_en_uk(word COLLATE NOCASE);

CREATE INDEX idx_dmklinger_word ON dmklinger_uk_en(word COLLATE NOCASE);

CREATE INDEX idx_wiktionary_word ON wiktionary(word COLLATE NOCASE);

CREATE INDEX idx_ulif_dictua_entries_status
                ON ulif_dictua_entries(status, normalized_query)
                ;

CREATE INDEX idx_ulif_dictua_sections_entry_kind_order
    ON ulif_dictua_sections(entry_id, kind, source_order);

CREATE INDEX idx_ulif_forms_entry_id ON ulif_forms(entry_id);

CREATE INDEX idx_ulif_forms_form_unstressed ON ulif_forms(form_unstressed);

CREATE INDEX idx_sum20_articles_lookup
    ON sum20_articles(normalized_lookup_key, wordid);

CREATE INDEX idx_sum20_senses_article
    ON sum20_senses(article_id, sense_order);

CREATE INDEX idx_sum20_citations_article
    ON sum20_citations(article_id, "order");

CREATE INDEX idx_slovnyk_me_dialect
    ON slovnyk_me_entries(is_dialect) WHERE is_dialect = 1;

CREATE INDEX idx_slovnyk_me_dict
    ON slovnyk_me_entries(dictionary_slug);

CREATE INDEX idx_slovnyk_me_modern
    ON slovnyk_me_entries(is_modern) WHERE is_modern = 1;

CREATE INDEX idx_slovnyk_me_word
    ON slovnyk_me_entries(normalized_word COLLATE NOCASE);

CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

CREATE TRIGGER literary_ai AFTER INSERT ON literary_texts BEGIN
    INSERT INTO literary_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

CREATE TRIGGER external_ai AFTER INSERT ON external_articles BEGIN
    INSERT INTO external_fts(rowid, title, text, speaker)
    VALUES (new.id, new.title, new.text, new.speaker);
END;

CREATE TRIGGER wikipedia_ai AFTER INSERT ON wikipedia BEGIN
    INSERT INTO wikipedia_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;

CREATE TRIGGER ukrainian_wiki_ad AFTER DELETE ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(ukrainian_wiki_fts, rowid, article_title, section_path, text)
    VALUES ('delete', old.id, old.article_title, old.section_path, old.text);
END;

CREATE TRIGGER ukrainian_wiki_ai AFTER INSERT ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(rowid, article_title, section_path, text)
    VALUES (new.id, new.article_title, new.section_path, new.text);
END;

CREATE TRIGGER ukrainian_wiki_au AFTER UPDATE ON ukrainian_wiki BEGIN
    INSERT INTO ukrainian_wiki_fts(ukrainian_wiki_fts, rowid, article_title, section_path, text)
    VALUES ('delete', old.id, old.article_title, old.section_path, old.text);
    INSERT INTO ukrainian_wiki_fts(rowid, article_title, section_path, text)
    VALUES (new.id, new.article_title, new.section_path, new.text);
END;

CREATE TRIGGER resource_catalogue_ad AFTER DELETE ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(resource_catalogue_fts,rowid,title,search_text)
    VALUES('delete',old.id,old.title,old.search_text);
END;

CREATE TRIGGER resource_catalogue_ai AFTER INSERT ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(rowid,title,search_text) VALUES(new.id,new.title,new.search_text);
END;

CREATE TRIGGER resource_catalogue_au AFTER UPDATE ON resource_catalogue BEGIN
    INSERT INTO resource_catalogue_fts(resource_catalogue_fts,rowid,title,search_text)
    VALUES('delete',old.id,old.title,old.search_text);
    INSERT INTO resource_catalogue_fts(rowid,title,search_text) VALUES(new.id,new.title,new.search_text);
END;

CREATE TRIGGER ua_gec_errors_ad AFTER DELETE ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(ua_gec_errors_fts, rowid, error, correct, error_type)
                VALUES('delete', old.id, old.error, old.correct, old.error_type);
            END;

CREATE TRIGGER ua_gec_errors_ai AFTER INSERT ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type)
                VALUES (new.id, new.error, new.correct, new.error_type);
            END;

CREATE TRIGGER ua_gec_errors_au AFTER UPDATE ON ua_gec_errors BEGIN
                INSERT INTO ua_gec_errors_fts(ua_gec_errors_fts, rowid, error, correct, error_type)
                VALUES('delete', old.id, old.error, old.correct, old.error_type);
                INSERT INTO ua_gec_errors_fts(rowid, error, correct, error_type)
                VALUES (new.id, new.error, new.correct, new.error_type);
            END;

CREATE TRIGGER sum20_articles_ad
AFTER DELETE ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(
        sum20_articles_fts, rowid, normalized_lookup_key, headword, definition_text
    )
    VALUES ('delete', old.id, old.normalized_lookup_key, old.headword, old.definition_text);
END;

CREATE TRIGGER sum20_articles_ai
AFTER INSERT ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(rowid, normalized_lookup_key, headword, definition_text)
    VALUES (new.id, new.normalized_lookup_key, new.headword, new.definition_text);
END;

CREATE TRIGGER sum20_articles_au
AFTER UPDATE ON sum20_articles BEGIN
    INSERT INTO sum20_articles_fts(
        sum20_articles_fts, rowid, normalized_lookup_key, headword, definition_text
    )
    VALUES ('delete', old.id, old.normalized_lookup_key, old.headword, old.definition_text);
    INSERT INTO sum20_articles_fts(rowid, normalized_lookup_key, headword, definition_text)
    VALUES (new.id, new.normalized_lookup_key, new.headword, new.definition_text);
END;

CREATE TRIGGER slovnyk_me_entries_ad
AFTER DELETE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
END;

CREATE TRIGGER slovnyk_me_entries_ai
AFTER INSERT ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;

CREATE TRIGGER slovnyk_me_entries_au
AFTER UPDATE ON slovnyk_me_entries BEGIN
    INSERT INTO slovnyk_me_entries_fts(
        slovnyk_me_entries_fts, rowid, word, title, snippet, text, dictionary_label
    )
    VALUES ('delete', old.id, old.word, old.title, old.snippet, old.text, old.dictionary_label);
    INSERT INTO slovnyk_me_entries_fts(rowid, word, title, snippet, text, dictionary_label)
    VALUES (new.id, new.word, new.title, new.snippet, new.text, new.dictionary_label);
END;
