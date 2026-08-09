"""Tests for the incremental textbook ingest (#4593 wave-1 path)."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from ingest import incremental_textbook_ingest as iti

SCHEMA = """
CREATE TABLE textbooks (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT,
    title TEXT,
    text TEXT,
    source_file TEXT,
    subject TEXT,
    grade TEXT,
    author TEXT,
    author_uk TEXT DEFAULT '',
    char_count INTEGER
);
CREATE VIRTUAL TABLE textbooks_fts USING fts5(
    title, text, content='textbooks', content_rowid='id', tokenize='unicode61'
);
CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
    INSERT INTO textbooks_fts(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
"""


@pytest.fixture()
def fixture_env(tmp_path, monkeypatch):
    db = tmp_path / "sources.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()

    chunks = tmp_path / "textbook_chunks"
    monkeypatch.setattr(iti, "CHUNKS_DIR", chunks)
    slug = "9-klas-khimiya-popel-2017"
    jsonl = chunks / "grade-09" / f"{slug}.jsonl"
    jsonl.parent.mkdir(parents=True)
    entries = [
        {
            "chunk_id": f"{slug}_s{i:04d}",
            "section_title": "§ 1. Хімія",
            "text": f"Хімія фотосинтез рівняння приклад {i}",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
            "token_count": 10,
        }
        for i in range(3)
    ]
    jsonl.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in entries))
    return db, slug


def test_ingest_inserts_with_subject_and_author_uk(fixture_env):
    db, slug = fixture_env
    counts = iti.ingest([slug], db_path=db, dry_run=False)
    assert counts == {slug: 3}
    conn = sqlite3.connect(str(db))
    rows = conn.execute("SELECT subject, author_uk FROM textbooks WHERE source_file=?", (slug,)).fetchall()
    assert rows == [("khimiya", "Попель")] * 3
    char_counts = conn.execute(
        "SELECT char_count, length(text) FROM textbooks WHERE source_file=? ORDER BY id",
        (slug,),
    ).fetchall()
    assert char_counts == [
        (len(text), len(text))
        for text in (
            "Хімія фотосинтез рівняння приклад 0",
            "Хімія фотосинтез рівняння приклад 1",
            "Хімія фотосинтез рівняння приклад 2",
        )
    ]
    sections = conn.execute(
        "SELECT section_title, chunk_count FROM textbook_sections WHERE source_file=?",
        (slug,),
    ).fetchall()
    assert sections == [("§ 1. Хімія", 3)]
    linked = conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
        (slug,),
    ).fetchone()[0]
    assert linked == 3
    fts = conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'").fetchone()[0]
    assert fts == 3
    conn.close()


def test_reingest_is_idempotent(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    n = conn.execute("SELECT COUNT(*) FROM textbooks WHERE source_file=?", (slug,)).fetchone()[0]
    fts = conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'").fetchone()[0]
    assert (n, fts) == (3, 3), "delete+insert+fts-rebuild must not duplicate"
    conn.close()


def test_dry_run_rolls_back(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=True)
    conn = sqlite3.connect(str(db))
    n = conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0]
    assert n == 0
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='textbook_sections'").fetchone()[0] == 0
    conn.close()


def test_normal_ingest_writes_integrity_receipt(fixture_env, tmp_path):
    db, slug = fixture_env
    receipt_path = tmp_path / "ingest-receipt.json"

    counts = iti.ingest(
        [slug],
        db_path=db,
        dry_run=False,
        receipt_path=receipt_path,
    )

    assert counts == {slug: 3}
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "incremental-textbook-ingest.v2"
    assert receipt["status"] == "committed"
    assert receipt["before"] == {"textbook_rows": 0, "fts_rows": 0, "section_rows": 0}
    assert receipt["after_transaction"] == {
        "textbook_rows": 3,
        "fts_rows": 3,
        "section_rows": 1,
    }
    assert receipt["integrity_check"] == "ok"
    assert receipt["foreign_key_failures_unchanged"] is True
    assert receipt["db_sha256_before"] != receipt["db_sha256_after"]
    assert receipt["per_source"][0]["fts"]["parity"] is True


def test_dry_run_receipt_proves_database_hash_is_unchanged(fixture_env, tmp_path):
    db, slug = fixture_env
    receipt_path = tmp_path / "dry-run-receipt.json"

    iti.ingest(
        [slug],
        db_path=db,
        dry_run=True,
        receipt_path=receipt_path,
    )

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "dry_run_rolled_back"
    assert receipt["db_sha256_before"] == receipt["db_sha256_after"]
    assert receipt["after_transaction"]["textbook_rows"] == 3


def test_chunks_root_override_is_threaded_without_using_default(fixture_env, tmp_path):
    db, slug = fixture_env
    canonical = tmp_path / "canonical-drive" / "textbook_chunks"
    jsonl = canonical / "grade-09" / f"{slug}.jsonl"
    jsonl.parent.mkdir(parents=True)
    jsonl.write_text(
        json.dumps(
            {
                "chunk_id": "canonical_s0000",
                "section_title": "§ 1. Канонічне джерело",
                "text": "Канонічний текст фотосинтезу для перевірки.",
                "author": "popel",
                "author_uk": None,
                "grade": 9,
                "token_count": 1,
            },
            ensure_ascii=False,
        )
        + "\n",
    )
    assert iti.find_jsonl(slug, chunks_root=canonical) == jsonl
    assert iti.ingest([slug], db_path=db, dry_run=False, chunks_root=canonical) == {slug: 1}
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT chunk_id FROM textbooks").fetchone()[0] == "canonical_s0000"
    conn.close()


def test_combined_grade_source_resolves_one_exact_cross_grade_path(tmp_path):
    root = tmp_path / "textbook_chunks"
    slug = "10-11-klas-mystectvo-nazarenko-2018"
    expected = root / "grade-11" / f"{slug}.jsonl"
    expected.parent.mkdir(parents=True)
    expected.write_text("{}\n", encoding="utf-8")

    assert iti.find_jsonl(slug, chunks_root=root) == expected


def test_university_source_uses_grade_zero_storage_and_university_db_label(tmp_path):
    root = tmp_path / "university_corpus" / "jsonl"
    slug = "uni-ukrlit-kalinichenko-2024"
    expected = root / "grade-00" / f"{slug}.jsonl"
    expected.parent.mkdir(parents=True)
    expected.write_text(
        json.dumps(
            {
                "chunk_id": f"{slug}_s0000",
                "section_title": "Літературознавча стаття",
                "text": "Український літературознавчий текст.",
                "author": "kalinichenko",
                "author_uk": None,
                "grade": 0,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    assert iti.find_jsonl(slug, chunks_root=root) == expected
    row = iti.build_rows(slug, chunks_root=root)[0]
    assert row[4] == "ukrlit"
    assert row[5] == "university"
    assert row[7] == "Калініченко"
    grouping_row = iti._section_row_for_grouping(
        iti.ChunkRow(1, row[0], "Сторінка 1", row[2], slug, row[5])
    )
    assert grouping_row.grade == "grade-00"


def test_cross_grade_source_fails_closed_when_duplicate_paths_exist(tmp_path):
    root = tmp_path / "textbook_chunks"
    slug = "10-11-klas-mystectvo-nazarenko-2018"
    for grade in ("grade-11", "grade-12"):
        path = root / grade / f"{slug}.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text("{}\n", encoding="utf-8")

    with pytest.raises(iti.IngestError, match="ambiguous"):
        iti.find_jsonl(slug, chunks_root=root)


def test_unverified_ocr_is_rejected_before_database_mutation(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entry = json.loads(jsonl.read_text(encoding="utf-8").splitlines()[0])
    entry.update(
        {
            "extraction_mode": "apple_vision_ocr",
            "quality": {"visual_verification": {"status": "required", "evidence_id": None}},
        }
    )
    jsonl.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(iti.IngestError, match="requires exact page-image verification"):
        iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 0
    conn.close()


def test_unverified_native_text_anomaly_is_rejected_before_database_mutation(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entry = json.loads(jsonl.read_text(encoding="utf-8").splitlines()[0])
    entry.update(
        {
            "extraction_mode": "native_text",
            "page_extraction_mode": "native_text",
            "layout": {
                "native_text_anomalies": {
                    "requires_visual_verification": True,
                    "total_findings": 1,
                }
            },
            "quality": {"visual_verification": {"status": "required", "evidence_id": None}},
        }
    )
    jsonl.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(iti.IngestError, match="requires exact page-image verification"):
        iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 0
    conn.close()


def test_soft_hyphen_layout_marker_is_ingested_without_altering_raw_text(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    source_text = "взаємопов’яза\u00ad них процесів"
    rows[0].update(
        {
            "text": source_text,
            "extraction_mode": "native_text",
            "page_extraction_mode": "native_text",
        }
    )
    jsonl.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )

    counts = iti.ingest([slug], db_path=db, dry_run=False)

    assert counts[slug] == len(rows)
    conn = sqlite3.connect(str(db))
    stored_text = conn.execute(
        "SELECT text FROM textbooks WHERE chunk_id = ?",
        (rows[0]["chunk_id"],),
    ).fetchone()[0]
    conn.close()
    assert stored_text == source_text


def test_hash_bound_native_anomaly_quarantine_removes_only_exact_archived_chunk(fixture_env, tmp_path):
    from projects.open_model_data.textbook_native_exactness import (
        atomic_write,
        audit_chunk_files,
        write_quarantine_rows,
    )

    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    rows = [json.loads(line) for line in jsonl.read_text(encoding="utf-8").splitlines()]
    repeated = "Рекомендовано Міністерством освіти і науки України"
    rows[1].update({"page_start": 2, "page_end": 2, "text": f"{repeated}\n{repeated}"})
    jsonl.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    audit, quarantined = audit_chunk_files(iti.CHUNKS_DIR)
    audit_path = tmp_path / "audit.json"
    atomic_write(audit_path, json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    quarantine_dir = tmp_path / "quarantine"
    write_quarantine_rows(quarantine_dir, audit, quarantined)

    dry_run = iti.quarantine_native_anomaly_chunks(
        audit_path=audit_path,
        chunks_root=iti.CHUNKS_DIR,
        quarantine_dir=quarantine_dir,
        db_path=db,
        dry_run=True,
    )
    assert dry_run["status"] == "dry_run_rolled_back"
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 3
    conn.close()

    receipt = iti.quarantine_native_anomaly_chunks(
        audit_path=audit_path,
        chunks_root=iti.CHUNKS_DIR,
        quarantine_dir=quarantine_dir,
        db_path=db,
        dry_run=False,
    )

    assert receipt["status"] == "committed"
    assert receipt["removed_source_count"] == 1
    assert receipt["removed_chunk_count"] == 1
    assert receipt["integrity_check"] == "ok"
    assert receipt["foreign_key_failures_unchanged"] is True
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts").fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM textbooks WHERE chunk_id = ?",
        (rows[1]["chunk_id"],),
    ).fetchone()[0] == 0
    conn.close()

    replay = iti.quarantine_native_anomaly_chunks(
        audit_path=audit_path,
        chunks_root=iti.CHUNKS_DIR,
        quarantine_dir=quarantine_dir,
        db_path=db,
        dry_run=False,
    )
    assert replay["status"] == "committed"
    assert replay["audited_source_count"] == 1
    assert replay["removed_source_count"] == 0
    assert replay["removed_chunk_count"] == 0
    assert replay["already_absent_chunk_count"] == 1
    assert replay["per_source"][0]["section_policy"] == "unchanged_already_absent"


@pytest.mark.parametrize("marker", ["extraction_mode", "page_extraction_mode"])
def test_either_ocr_marker_requires_verification(fixture_env, marker):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entry = json.loads(jsonl.read_text(encoding="utf-8").splitlines()[0])
    entry.update(
        {
            marker: "apple_vision_ocr",
            "quality": {"visual_verification": {"status": "required", "evidence_id": None}},
        }
    )
    jsonl.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(iti.IngestError, match="requires exact page-image verification"):
        iti.ingest([slug], db_path=db, dry_run=False)


def test_conflicting_extraction_markers_are_rejected(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entry = json.loads(jsonl.read_text(encoding="utf-8").splitlines()[0])
    entry.update(
        {
            "extraction_mode": "native_text",
            "page_extraction_mode": "apple_vision_ocr",
            "quality": {"visual_verification": {"status": "verified", "evidence_id": "page-image-check-1"}},
        }
    )
    jsonl.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(iti.IngestError, match="conflicting extraction-mode metadata"):
        iti.ingest([slug], db_path=db, dry_run=False)


def test_replace_and_quarantine_share_one_atomic_fts_rebuild(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    conn.execute(
        """INSERT INTO textbooks
           (chunk_id, title, text, source_file, subject, grade, author, author_uk, char_count)
           VALUES ('scan_s0000', 'Scan', 'неперевірений текст',
                   'scan-only-source', 'matematyka', '2', '', '', 20)"""
    )
    conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES('rebuild')")
    conn.commit()
    conn.close()

    counts = iti.ingest(
        [slug],
        db_path=db,
        dry_run=False,
        quarantine_slugs=["scan-only-source"],
    )

    assert counts == {slug: 3}
    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks WHERE source_file='scan-only-source'").fetchone()[0] == 0
    assert (
        conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'неперевірений'").fetchone()[0] == 0
    )
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'").fetchone()[0] == 3
    conn.close()


def test_section_replacement_preserves_other_sources_and_fts(fixture_env):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    conn.execute(
        """INSERT INTO textbooks
           (chunk_id, title, text, source_file, subject, grade, author, author_uk, char_count)
           VALUES ('other_s0000', 'Other', 'інший корпус', 'other-source', 'other', '9', '', '', 12)"""
    )
    other_id = conn.execute("SELECT id FROM textbooks WHERE chunk_id='other_s0000'").fetchone()[0]
    conn.execute(
        """INSERT INTO textbook_sections
           (source_file, grade, section_title, section_number, page_start, page_end, chunk_count, full_text)
           VALUES ('other-source', 9, '§ other', 'other', 1, 1, 1, 'інший корпус')"""
    )
    other_section = conn.execute(
        "SELECT section_id FROM textbook_sections WHERE source_file='other-source'"
    ).fetchone()[0]
    conn.execute("UPDATE textbooks SET parent_section_id=? WHERE id=?", (other_section, other_id))
    conn.commit()
    conn.close()

    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entries = [
        {
            "chunk_id": f"replacement_s{i:04d}",
            "section_title": "§ 2. Оновлена тема",
            "text": f"Оновлений хлорофіл рядок {i}.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
            "token_count": 999,
        }
        for i in range(2)
    ]
    jsonl.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )
    iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT COUNT(*) FROM textbooks WHERE source_file=?", (slug,)).fetchone()[0] == 2
    assert conn.execute("SELECT section_title FROM textbook_sections WHERE source_file=?", (slug,)).fetchall() == [
        ("§ 2. Оновлена тема",)
    ]
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
            (slug,),
        ).fetchone()[0]
        == 2
    )
    assert conn.execute("SELECT section_title FROM textbook_sections WHERE source_file='other-source'").fetchall() == [
        ("§ other",)
    ]
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'оновлений'").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'хлорофіл'").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'").fetchone()[0] == 0
    conn.close()


def test_failure_after_replacement_rolls_back_rows_sections_and_fts(fixture_env, monkeypatch):
    db, slug = fixture_env
    iti.ingest([slug], db_path=db, dry_run=False)
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    jsonl.write_text(
        json.dumps(
            {
                "chunk_id": "failed_s0000",
                "section_title": "§ 9. Не застосовано",
                "text": "Нова лексема, яка не має залишитися.",
                "author": "popel",
                "author_uk": None,
                "grade": 9,
                "token_count": 1,
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    def fail_fts(*_args, **_kwargs):
        raise iti.IngestError("forced FTS failure")

    monkeypatch.setattr(iti, "_fts_source_evidence", fail_fts)
    with pytest.raises(iti.IngestError, match="forced FTS failure"):
        iti.ingest([slug], db_path=db, dry_run=False)

    conn = sqlite3.connect(str(db))
    assert conn.execute("SELECT chunk_id FROM textbooks WHERE source_file=?", (slug,)).fetchall() == [
        (f"{slug}_s0000",),
        (f"{slug}_s0001",),
        (f"{slug}_s0002",),
    ]
    assert conn.execute("SELECT section_title FROM textbook_sections WHERE source_file=?", (slug,)).fetchall() == [
        ("§ 1. Хімія",)
    ]
    assert conn.execute("SELECT COUNT(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'фотосинтез'").fetchone()[0] == 3
    conn.close()


def test_page_labeled_rows_use_exact_page_parents_without_heading_inference(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entries = [
        {
            "chunk_id": f"unlinked_s{i:04d}",
            "section_title": f"Сторінка {i + 1}",
            "text": "Текст без заголовка, який не можна невидимо прийняти.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
        }
        for i in range(2)
    ]
    jsonl.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    assert conn.execute(
        "SELECT section_title FROM textbook_sections WHERE source_file=? ORDER BY page_start",
        (slug,),
    ).fetchall() == [("Сторінка 1",), ("Сторінка 2",)]
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
            (slug,),
        ).fetchone()[0]
        == 2
    )
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM textbook_sections WHERE section_title LIKE 'Текст без заголовка%'"
        ).fetchone()[0]
        == 0
    )
    conn.close()


def test_leading_front_matter_gets_bounded_parent_section(fixture_env):
    db, slug = fixture_env
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    entries = [
        {
            "chunk_id": "front_s0000",
            "section_title": "Сторінка 1",
            "text": "Текст без заголовка, який передує першому структурованому розділу.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
        },
        {
            "chunk_id": "body_s0001",
            "section_title": "§ 1. Хімія",
            "text": "Перший структурований розділ підручника.",
            "author": "popel",
            "author_uk": None,
            "grade": 9,
        },
    ]
    jsonl.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )
    iti.ingest([slug], db_path=db, dry_run=False)
    conn = sqlite3.connect(str(db))
    assert conn.execute(
        "SELECT section_title, chunk_count FROM textbook_sections WHERE source_file=? ORDER BY section_id",
        (slug,),
    ).fetchall() == [(iti.FRONT_MATTER_SECTION, 1), ("§ 1. Хімія", 1)]
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM textbooks WHERE source_file=? AND parent_section_id IS NOT NULL",
            (slug,),
        ).fetchone()[0]
        == 2
    )
    conn.close()


def test_unmapped_author_refuses(fixture_env, tmp_path):
    db, _ = fixture_env
    slug = "9-klas-khimiya-nemaie-2017"
    jsonl = iti.CHUNKS_DIR / "grade-09" / f"{slug}.jsonl"
    jsonl.write_text(
        json.dumps({"chunk_id": "x", "text": "т", "author": "nemaie", "author_uk": None}, ensure_ascii=False)
    )
    with pytest.raises(iti.IngestError, match="no canonical Cyrillic form"):
        iti.ingest([slug], db_path=db, dry_run=True)


def test_missing_jsonl_refuses(fixture_env):
    db, _ = fixture_env
    with pytest.raises(iti.IngestError, match="chunk file missing"):
        iti.ingest(["5-klas-informatyka-ryvkind-2022"], db_path=db, dry_run=True)


def test_wave1_slugs_all_have_author_mappings():
    for slug in iti.WAVE1_SLUGS:
        author = slug.split("-")[-2]
        assert author.lower() in iti.AUTHOR_UK, slug
