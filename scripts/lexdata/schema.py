"""lexdata generation schema (design r3 §4 L1, §5.4 adjudication, §6 meta).

L1 containers (``l1_source_unit``, ``l1_line``, ``l1_unit_disposition``,
``l1_unit_input``) are never linked to L2. Every L1 leaf (``l1_lex_item``) has
exactly one ``l2_link``. ``l3_card_input`` is a view, so it is recomputed with
every generation. The L1 DDL hash is part of every source's transform digest;
the L2/meta DDL is not, because L2 and L3 are recomputed per generation.

Additions beyond the §4 column list, needed by §6: ``l1_lex_item.item_key``
(the parser-stable leaf identity adjudications bind to across generations),
``l1_source_unit.parent_l0_locator`` and ``l1_unit_input`` (the unit's L0 join
closure, so ``verify`` can recompute ``unit_input_fingerprint``).
"""

from __future__ import annotations

from scripts.lexdata.canonical import sha256_text

L1_SCHEMA_VERSION = "1"
GENERATION_SCHEMA_VERSION = "1"

L2_STATUSES = ("refused", "unavailable", "held", "split", "exact", "ambiguous", "unmatched")
HOLD_REASONS = ("capital_only", "unknown_competitor", "ulif_unresolved", "vesum_unbridged",
                "pos_conflict", "adjudication_invalidated")
ADJUDICATION_STATES = ("proposed", "admitted", "invalidated")


def _in(values: tuple[str, ...]) -> str:
    return ", ".join(f"'{value}'" for value in values)


L1_DDL = """
CREATE TABLE l1_source_unit (
    unit_id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL,
    l0_locator TEXT NOT NULL,
    unit_input_fingerprint TEXT NOT NULL CHECK (length(unit_input_fingerprint) = 64),
    l1_transform_digest TEXT NOT NULL CHECK (length(l1_transform_digest) = 64),
    unit_kind TEXT NOT NULL CHECK (unit_kind IN ('file', 'chunk', 'section', 'page', 'zone')),
    parent_l0_locator TEXT,
    parent_unit_id INTEGER REFERENCES l1_source_unit(unit_id),
    UNIQUE (source_id, l0_locator)
);
CREATE TABLE l1_unit_input (
    unit_id INTEGER NOT NULL REFERENCES l1_source_unit(unit_id),
    l0_row_locator TEXT NOT NULL,
    l0_row_fingerprint TEXT NOT NULL CHECK (length(l0_row_fingerprint) = 64),
    PRIMARY KEY (unit_id, l0_row_locator)
) WITHOUT ROWID;
CREATE TABLE l1_line (
    unit_id INTEGER NOT NULL REFERENCES l1_source_unit(unit_id),
    line_no INTEGER NOT NULL,
    raw_line_sha256 TEXT NOT NULL CHECK (length(raw_line_sha256) = 64),
    disposition TEXT NOT NULL,
    PRIMARY KEY (unit_id, line_no)
) WITHOUT ROWID;
CREATE TABLE l1_unit_disposition (
    unit_id INTEGER PRIMARY KEY REFERENCES l1_source_unit(unit_id),
    disposition TEXT NOT NULL
);
CREATE TABLE l1_lex_item (
    item_id INTEGER PRIMARY KEY,
    unit_id INTEGER NOT NULL REFERENCES l1_source_unit(unit_id),
    item_key TEXT NOT NULL UNIQUE,
    line_no INTEGER,
    span_start INTEGER,
    span_end INTEGER,
    parent_item_id INTEGER REFERENCES l1_lex_item(item_id),
    member_index INTEGER,
    role TEXT NOT NULL CHECK (role IN ('headword', 'equivalent_lexeme', 'variant', 'aspect_partner', 'form', 'mwe')),
    raw_span TEXT NOT NULL,
    surface TEXT NOT NULL,
    key_stressed TEXT,
    key_unstressed TEXT,
    key_fold TEXT,
    case_signal TEXT CHECK (case_signal IS NULL OR case_signal IN ('lower', 'initial_cap', 'all_caps', 'mixed')),
    grammar_raw TEXT,
    grammar_parsed TEXT,
    homonym_marker TEXT,
    norm_flags TEXT NOT NULL,
    proposed_repairs TEXT NOT NULL,
    refusal_code TEXT,
    rights_class TEXT NOT NULL,
    row_sha256 TEXT NOT NULL CHECK (length(row_sha256) = 64),
    importer_version TEXT NOT NULL,
    CHECK ((parent_item_id IS NULL) = (member_index IS NULL)),
    CHECK ((refusal_code IS NULL AND key_stressed IS NOT NULL AND key_unstressed IS NOT NULL
            AND key_fold IS NOT NULL)
        OR (refusal_code IS NOT NULL AND key_stressed IS NULL AND key_unstressed IS NULL
            AND key_fold IS NULL))
);
CREATE INDEX l1_lex_item_unit ON l1_lex_item(unit_id);
CREATE INDEX l1_lex_item_fold ON l1_lex_item(key_fold);
CREATE TABLE l1_sense (
    item_id INTEGER NOT NULL REFERENCES l1_lex_item(item_id),
    sense_no INTEGER NOT NULL,
    gloss_raw TEXT NOT NULL,
    applies_to TEXT NOT NULL CHECK (applies_to IN ('self', 'all_members')),
    PRIMARY KEY (item_id, sense_no)
) WITHOUT ROWID;
CREATE TABLE l1_example (
    item_id INTEGER NOT NULL REFERENCES l1_lex_item(item_id),
    ex_no INTEGER NOT NULL,
    uk_raw TEXT,
    en_raw TEXT,
    PRIMARY KEY (item_id, ex_no)
) WITHOUT ROWID;
CREATE TABLE l1_verb_form (
    item_id INTEGER NOT NULL REFERENCES l1_lex_item(item_id),
    form_no INTEGER NOT NULL,
    aspect TEXT,
    tense TEXT,
    person_number TEXT,
    form_raw TEXT NOT NULL,
    PRIMARY KEY (item_id, form_no)
) WITHOUT ROWID;
CREATE TABLE l1_government (
    item_id INTEGER NOT NULL REFERENCES l1_lex_item(item_id),
    gov_no INTEGER NOT NULL,
    pattern_raw TEXT NOT NULL,
    PRIMARY KEY (item_id, gov_no)
) WITHOUT ROWID;
"""

L2_DDL = f"""
CREATE TABLE l2_link (
    link_id INTEGER PRIMARY KEY,
    item_id INTEGER NOT NULL UNIQUE REFERENCES l1_lex_item(item_id),
    key_stressed TEXT,
    key_unstressed TEXT,
    key_fold TEXT,
    status TEXT NOT NULL CHECK (status IN ({_in(L2_STATUSES)})),
    hold_reason TEXT CHECK (hold_reason IS NULL OR hold_reason IN ({_in(HOLD_REASONS)})),
    unavailable_reason TEXT,
    lexeme_id TEXT,
    candidate_set_sha256 TEXT CHECK (candidate_set_sha256 IS NULL OR length(candidate_set_sha256) = 64),
    adjudication_id INTEGER REFERENCES l2_adjudication(adjudication_id),
    resolver_version TEXT NOT NULL,
    CHECK ((status = 'held') = (hold_reason IS NOT NULL)),
    CHECK ((status = 'unavailable') = (unavailable_reason IS NOT NULL))
);
CREATE INDEX l2_link_fold ON l2_link(key_fold);
CREATE INDEX l2_link_lexeme ON l2_link(lexeme_id);
CREATE TABLE l2_candidate (
    link_id INTEGER NOT NULL REFERENCES l2_link(link_id),
    lexeme_id TEXT NOT NULL,
    headword_stressed TEXT,
    pos TEXT,
    is_proper INTEGER,
    eligibility TEXT NOT NULL CHECK (eligibility IN ('eligible', 'unknown')),
    entry_fingerprint TEXT,
    dropped_by_rule TEXT,
    PRIMARY KEY (link_id, lexeme_id)
) WITHOUT ROWID;
CREATE TABLE l2_adjudication (
    adjudication_id INTEGER PRIMARY KEY,
    item_key TEXT NOT NULL,
    link_id INTEGER REFERENCES l2_link(link_id),
    target_lexeme_id TEXT NOT NULL,
    evidence TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL CHECK (length(input_fingerprint) = 64),
    resolver_version TEXT NOT NULL,
    store_fingerprints TEXT NOT NULL,
    seat TEXT NOT NULL,
    model TEXT NOT NULL,
    family TEXT NOT NULL,
    harness TEXT NOT NULL,
    receipt TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ({_in(ADJUDICATION_STATES)})),
    invalidated_reason TEXT,
    CHECK ((state = 'invalidated') = (invalidated_reason IS NOT NULL))
);
CREATE INDEX l2_adjudication_item ON l2_adjudication(item_key);
CREATE VIEW l3_card_input AS
SELECT l.lexeme_id AS lexeme_id,
       l.link_id AS l2_link_id,
       u.source_id AS source_id,
       u.l0_locator AS l0_locator,
       i.rights_class AS rights_class,
       i.item_id AS item_id,
       i.key_stressed AS key_stressed,
       i.key_unstressed AS key_unstressed,
       i.key_fold AS key_fold,
       l.adjudication_id AS adjudication_id
FROM l2_link AS l
JOIN l1_lex_item AS i ON i.item_id = l.item_id
JOIN l1_source_unit AS u ON u.unit_id = i.unit_id
WHERE l.lexeme_id IS NOT NULL
  AND (l.status = 'exact'
       OR (l.status = 'held' AND EXISTS (
            SELECT 1 FROM l2_adjudication AS a
            WHERE a.adjudication_id = l.adjudication_id AND a.state = 'admitted')));
"""

META_DDL = """
CREATE TABLE meta (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    generation TEXT NOT NULL,
    generation_seq INTEGER NOT NULL,
    generation_schema_version TEXT NOT NULL,
    l1_schema_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    input_manifest TEXT NOT NULL,
    input_manifest_sha256 TEXT NOT NULL,
    transform_manifest TEXT NOT NULL,
    l1_transform_digests TEXT NOT NULL,
    normalizer_manifest TEXT NOT NULL,
    normalizer_digest TEXT NOT NULL,
    store_fingerprints TEXT NOT NULL,
    resolver_version TEXT NOT NULL,
    diff_receipt TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'published')),
    verify_receipt_sha256 TEXT,
    CHECK ((status = 'published') = (verify_receipt_sha256 IS NOT NULL))
);
"""

FULL_DDL = L1_DDL + L2_DDL + META_DDL


def l1_ddl_sha256() -> str:
    return sha256_text(L1_DDL)


def schema_contents() -> dict[str, object]:
    return {"l1_schema_version": L1_SCHEMA_VERSION, "l1_ddl_sha256": l1_ddl_sha256()}
