"""Tests for the A1 base layer word-store request file (WP 10, #8414, #8397).

Validates schema conformity, closed-class rules, and that build_words accepts it
on a synthetic store without writing any words file into git.
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import sources, words
from scripts.curriculum.learner_state.base_layer import resolve_base_ids
from scripts.rag.config import VESUM_DB_PATH

REPO_ROOT = Path(__file__).resolve().parents[3]
BASE_REQUEST_PATH = REPO_ROOT / "curriculum/l2-uk-en/evidence/a1/_base.request.yaml"

pytestmark = pytest.mark.reads_content


def test_a1_base_request_schema_and_rules() -> None:
    """_base.request.yaml exists, validates against evidence-words-request-v1, and obeys base layer rules."""
    assert BASE_REQUEST_PATH.is_file(), f"missing base request file: {BASE_REQUEST_PATH}"

    raw_text = BASE_REQUEST_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw_text)

    # 1. Validates against schema
    words.validate_request_data(data)

    assert data["request_schema"] == 1
    assert data["level"] == "a1"
    req_words = data["words"]
    assert len(req_words) > 0

    allowed_pos = {"noun", "adj", "prep", "conj", "part", "adv"}
    forbidden_lemmas = {
        "один",
        "два",
        "три",
        "чотири",
        "п'ять",
        "шість",
        "сім",
        "вісім",
        "дев'ять",
        "десять",
        "можна",
        "треба",
        "потрібно",
        "хто",
        "що",
        "який",
        "де",
        "куди",
        "звідки",
        "чому",
        "чого",
        "скільки",
        "коли",
    }

    lemmas_seen = set()
    for item in req_words:
        lemma = item["lemma"]
        pos = item["pos"]
        want = item["want"]
        note = item.get("note")

        assert want == "new", f"base layer request must specify want='new', got {want!r} for {lemma}"
        assert pos in allowed_pos, f"pos {pos!r} for {lemma} not in allowed closed classes"
        assert note and isinstance(note, str) and len(note.strip()) > 0, f"missing closed-class note for {lemma}"
        assert lemma not in forbidden_lemmas, f"forbidden lemma {lemma!r} in base layer"
        assert lemma not in lemmas_seen, f"duplicate lemma {lemma!r} in base layer request"
        lemmas_seen.add(lemma)

    # Euphonic pairs required by the brief
    required_euphonic_pairs = [
        ("у", "в"),
        ("з", "із"),
        ("з", "зі"),
        ("з", "зо"),
        ("і", "й"),
        ("вже", "уже"),
        ("ще", "іще"),
        ("під", "піді"),
        ("під", "підо"),
        ("над", "наді"),
        ("над", "надо"),
        ("перед", "переді"),
        ("перед", "передо"),
        ("від", "од"),
    ]
    for w1, w2 in required_euphonic_pairs:
        assert w1 in lemmas_seen, f"missing euphonic partner {w1!r}"
        assert w2 in lemmas_seen, f"missing euphonic partner {w2!r}"


def test_a1_base_request_accepted_by_build_words(tmp_path: Path) -> None:
    """build_words accepts the base request on a synthetic store without writing words into git."""
    raw_data = yaml.safe_load(BASE_REQUEST_PATH.read_text(encoding="utf-8"))
    req_words = raw_data["words"]
    lemmas = [w["lemma"] for w in req_words]

    # Build isolated synthetic VESUM DB populated with the lemmas' real VESUM rows
    synthetic_vesum = tmp_path / "synthetic-vesum.db"
    with sqlite3.connect(synthetic_vesum) as conn:
        conn.executescript("""
            CREATE TABLE forms_all (id INTEGER PRIMARY KEY, entry_id INTEGER,
                word_form TEXT, lemma TEXT, pos TEXT, tags TEXT, source_comment TEXT, source_location TEXT);
            CREATE TABLE form_markers (form_id INTEGER, marker TEXT, origin TEXT, marker_class TEXT);
            CREATE TABLE vesum_build_metadata (key TEXT, value TEXT);
            CREATE VIEW forms AS SELECT word_form, lemma, pos, tags FROM forms_all;
        """)
        conn.execute(
            "INSERT INTO vesum_build_metadata VALUES (?, ?)",
            ("canonical_jsonl_sha256", hashlib.sha256(b"synthetic-vesum").hexdigest()),
        )
        with sqlite3.connect(f"file:{VESUM_DB_PATH}?mode=ro", uri=True) as real_conn:
            slots = ",".join("?" * len(lemmas))
            rows = real_conn.execute(
                f"SELECT id, entry_id, word_form, lemma, pos, tags, source_comment, source_location FROM forms_all WHERE lemma IN ({slots})",
                lemmas,
            ).fetchall()
            conn.executemany("INSERT INTO forms_all VALUES (?,?,?,?,?,?,?,?)", rows)
            form_ids = [r[0] for r in rows]
            if form_ids:
                fslots = ",".join("?" * len(form_ids))
                m_rows = real_conn.execute(
                    f"SELECT form_id, marker, origin, marker_class FROM form_markers WHERE form_id IN ({fslots})",
                    form_ids,
                ).fetchall()
                conn.executemany("INSERT INTO form_markers VALUES (?,?,?,?)", m_rows)

    # Build isolated synthetic sources DB
    synthetic_sources = tmp_path / "synthetic-sources.db"
    with sqlite3.connect(synthetic_sources) as conn:
        conn.executescript("""
            CREATE TABLE ulif_dictua_entries (id INTEGER PRIMARY KEY, normalized_query TEXT,
                homonym_index INTEGER, canonical_headword TEXT, grammatical_label TEXT,
                sense_gloss TEXT, homonym_checked INTEGER, status TEXT, retrieved_at TEXT);
            CREATE TABLE ulif_dictua_sections (id INTEGER PRIMARY KEY, entry_id INTEGER,
                kind TEXT, source_order INTEGER, sense_or_group_id TEXT, payload_json TEXT);
            CREATE TABLE dmklinger_uk_en (id INTEGER PRIMARY KEY, word TEXT, pos TEXT,
                translations TEXT, text TEXT, source TEXT);
            CREATE TABLE puls_cefr (id INTEGER PRIMARY KEY, word TEXT, level TEXT);
            CREATE TABLE textbook_sections (section_id INTEGER PRIMARY KEY, source_file TEXT,
                grade INTEGER, section_title TEXT, section_number INTEGER, page_start INTEGER,
                page_end INTEGER, chunk_count INTEGER, full_text TEXT);
            CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT,
                text TEXT, source_file TEXT, grade INTEGER, author TEXT, char_count INTEGER,
                parent_section_id INTEGER, author_uk TEXT, subject TEXT);
            CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT,
                text TEXT, source_file TEXT, author TEXT, work TEXT, work_id TEXT, year INTEGER,
                genre TEXT, language_period TEXT, char_count INTEGER, source_url TEXT);
            CREATE TABLE ua_gec_errors (id INTEGER PRIMARY KEY, error TEXT, correct TEXT,
                error_type TEXT, doc_id TEXT, annotator_id TEXT, partition TEXT, is_native INTEGER,
                source_lang TEXT);
            CREATE TABLE style_guide (id INTEGER PRIMARY KEY, word TEXT, section TEXT,
                text TEXT, source TEXT, word_lower TEXT, excerpt_full TEXT, page INTEGER,
                russianism_pattern TEXT);
        """)

    with sources.Sources(sources_db=synthetic_sources, vesum_db=synthetic_vesum) as api:
        res = words.build_words(
            "a1",
            BASE_REQUEST_PATH,
            evidence_dir=tmp_path,
            sources_instance=api,
            dry_run=False,
        )

    assert res["status"] == "ok"
    assert res["words_count"] == len(req_words)
    assert res["unresolved_count"] == 0
    assert res["resolved_count"] == len(req_words)

    # Verify that resolve_base_ids resolves all records cleanly
    base_ids = resolve_base_ids("a1", evidence_dir=tmp_path, base_request_path=BASE_REQUEST_PATH)
    assert len(base_ids) == len(req_words)
    for bid in base_ids:
        assert bid.startswith("W-")
