CREATE TABLE forms_all (
    id INTEGER PRIMARY KEY,
    entry_id INTEGER NOT NULL,
    word_form TEXT NOT NULL,
    lemma TEXT NOT NULL,
    pos TEXT NOT NULL,
    tags TEXT NOT NULL,
    source_comment TEXT,
    source_location TEXT NOT NULL,
    word_form_folded TEXT NOT NULL,
    lemma_folded TEXT NOT NULL
);

CREATE TABLE form_markers (
    form_id INTEGER NOT NULL REFERENCES forms_all(id) ON DELETE CASCADE,
    marker TEXT NOT NULL,
    origin TEXT NOT NULL CHECK (origin IN ('tag', 'comment')),
    marker_class TEXT NOT NULL,
    PRIMARY KEY (form_id, marker, origin)
);

CREATE TABLE vesum_build_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE VIEW forms AS
SELECT word_form, lemma, tags, pos
FROM forms_all AS form
WHERE NOT EXISTS (
    SELECT 1
    FROM form_markers AS marker
    WHERE marker.form_id = form.id
      AND marker.marker IN ('bad', 'obsc', 'subst')
);

CREATE INDEX idx_forms_all_lemma ON forms_all(lemma);

CREATE INDEX idx_forms_all_lemma_folded ON forms_all(lemma_folded);

CREATE INDEX idx_forms_all_word_form ON forms_all(word_form);

CREATE INDEX idx_forms_all_word_form_folded ON forms_all(word_form_folded);

CREATE INDEX idx_form_markers_form_id ON form_markers(form_id);

CREATE INDEX idx_form_markers_marker ON form_markers(marker);
