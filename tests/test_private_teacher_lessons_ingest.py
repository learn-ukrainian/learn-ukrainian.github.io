"""Synthetic DOCX/SQLite tests. Never read the private host corpus."""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from scripts.ingest import private_teacher_lessons_ingest as ingest


def paragraph(text: str, style: str = "") -> str:
    prop = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{prop}<w:r><w:t>{text}</w:t></w:r></w:p>"


def docx(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "synthetic.docx"
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", f'<w:document xmlns:w="{ingest.W[1:-1]}"><w:body>{body}</w:body></w:document>')
        archive.writestr("word/media/unused.bin", b"not an image")
    return path


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "sources.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE NOT NULL,
            title TEXT, text TEXT, source_file TEXT, grade TEXT,
            author TEXT, author_uk TEXT, char_count INTEGER);
        CREATE VIRTUAL TABLE textbooks_fts USING fts5(text, content=textbooks, content_rowid=id);
        CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
            INSERT INTO textbooks_fts(rowid,text) VALUES (new.id,new.text);
        END;
        CREATE TRIGGER textbooks_ad AFTER DELETE ON textbooks BEGIN
            INSERT INTO textbooks_fts(textbooks_fts,rowid,text) VALUES ('delete',old.id,old.text);
        END;
        INSERT INTO textbooks (chunk_id,source_file,text) VALUES ('unrelated','other','unrelated');
    """)
    yield conn, path
    conn.close()


def test_extract_order_boundaries_and_preserve_date_suffix(tmp_path):
    source = docx(tmp_path, paragraph("Synthetic front", "Title")
        + paragraph("04/03/2025 and 05/03/2025")
        + paragraph("Dialogue alpha", "Heading1")
        + '<w:tbl><w:tr><w:tc>' + paragraph("cell one") + '</w:tc><w:tc>'
        + paragraph("01/01/2020 is a table example") + '</w:tc></w:tr></w:tbl>'
        + '<w:sdt><w:sdtContent><w:p><w:hyperlink><w:r><w:t>link label</w:t>'
        + '<w:tab/><w:t>tabbed</w:t><w:br/><w:t>new line</w:t></w:r></w:hyperlink></w:p></w:sdtContent></w:sdt>'
        + paragraph("03.03.2025Attached exercise") + paragraph("last body")
        + paragraph("Synthetic appendix", "Title") + paragraph("Excluded tail"))
    parsed = ingest.parse_docx(source)
    assert len(parsed.lessons) == 2
    assert parsed.front_matter == 1
    assert parsed.appendix == 2
    assert parsed.lessons[0].text == (
        "04/03/2025 and 05/03/2025\nDialogue alpha\ncell one\n"
        "01/01/2020 is a table example\nlink label\ttabbed\nnew line\n"
    )
    assert parsed.lessons[1].text == "03.03.2025Attached exercise\nlast body\n"


def test_header_only_entries_are_not_silently_dropped(tmp_path):
    parsed = ingest.parse_docx(docx(tmp_path, paragraph("02/01/2025") + paragraph("01/01/2025")))
    assert len(parsed.lessons) == 2
    assert [lesson.body_paragraphs for lesson in parsed.lessons] == [0, 0]


def test_ids_stable_when_new_lessons_are_prepended(tmp_path):
    old = ingest.parse_docx(docx(tmp_path, paragraph("01/01/2025") + paragraph("original")))
    new = ingest.parse_docx(docx(tmp_path, paragraph("02/01/2025") + paragraph("new")
        + paragraph("01.01.2025") + paragraph("original")))
    assert old.lessons[0].chunk_id == new.lessons[1].chunk_id


@pytest.mark.parametrize("body", [
    paragraph("no dated units"),
    paragraph("31/02/2025"),
    paragraph("01/01/2025") + paragraph("01.01.2025"),
    paragraph("01/01/2025") + paragraph("appendix", "Title") + paragraph("02/01/2025"),
    '<w:txbxContent>' + paragraph("01/01/2025") + '</w:txbxContent>',
])
def test_invalid_structure_fails_closed(tmp_path, body):
    with pytest.raises(ValueError):
        ingest.parse_docx(docx(tmp_path, body))


def lessons():
    return [ingest.Lesson("2025-01-01", "Synthetic searchablealpha\n", 1),
            ingest.Lesson("2025-01-02", "Synthetic searchablebeta\n", 1)]


def test_ingest_idempotence_sections_metadata_and_fts(db):
    conn, _ = db
    assert ingest.ingest_lessons(conn, lessons()) == (2, 0)
    assert ingest.ingest_lessons(conn, lessons()) == (0, 2)
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3
    assert conn.execute("SELECT count(*) FROM textbook_sections").fetchone()[0] == 2
    assert conn.execute("SELECT count(*) FROM textbooks WHERE parent_section_id IS NOT NULL").fetchone()[0] == 2
    assert conn.execute("SELECT DISTINCT author, author_uk, grade FROM textbooks WHERE source_file=?",
                        (ingest.SOURCE_FILE,)).fetchall() == [(ingest.AUTHOR, ingest.AUTHOR, "")]
    assert conn.execute("SELECT count(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'searchablealpha'").fetchone()[0] == 1


def test_force_replaces_only_source_and_fts(db):
    conn, _ = db
    ingest.ingest_lessons(conn, lessons())
    conn.execute("INSERT INTO textbook_sections (source_file,grade,section_title,chunk_count,full_text) VALUES ('other',0,'other',1,'untouched')")
    conn.commit()
    changed = [ingest.Lesson("2025-01-01", "Synthetic replacement\n", 1)]
    with pytest.raises(ValueError, match="Source changed"):
        ingest.ingest_lessons(conn, changed)
    assert ingest.ingest_lessons(conn, changed, force=True) == (1, 0)
    assert conn.execute("SELECT text FROM textbooks WHERE source_file='other'").fetchone()[0] == "unrelated"
    assert conn.execute("SELECT full_text FROM textbook_sections WHERE source_file='other'").fetchone()[0] == "untouched"
    assert conn.execute("SELECT count(*) FROM textbook_sections WHERE source_file=?", (ingest.SOURCE_FILE,)).fetchone()[0] == 1
    assert conn.execute("SELECT count(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'searchablealpha'").fetchone()[0] == 0
    assert conn.execute("SELECT count(*) FROM textbooks_fts WHERE textbooks_fts MATCH 'replacement'").fetchone()[0] == 1


def test_force_failure_rolls_back_deleted_rows_and_sections(db):
    conn, _ = db
    ingest.ingest_lessons(conn, lessons())
    before = conn.execute("SELECT * FROM textbooks").fetchall()
    sections = conn.execute("SELECT * FROM textbook_sections").fetchall()
    conn.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON textbooks BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        ingest.ingest_lessons(conn, lessons(), force=True)
    assert conn.execute("SELECT * FROM textbooks").fetchall() == before
    assert conn.execute("SELECT * FROM textbook_sections").fetchall() == sections


@pytest.mark.parametrize("items", [[], [lessons()[0], lessons()[0]]])
def test_force_rejects_empty_or_duplicate_input_without_deleting(db, items):
    conn, _ = db
    ingest.ingest_lessons(conn, lessons())
    with pytest.raises(ValueError):
        ingest.ingest_lessons(conn, items, force=True)
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3


def test_cli_help_uses_portable_example():
    result = subprocess.run(
        [sys.executable, "-m", "scripts.ingest.private_teacher_lessons_ingest", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    help_text = result.stdout + result.stderr
    assert ".venv/bin/python -m scripts.ingest.private_teacher_lessons_ingest" in help_text
    assert "/home/" not in help_text


def test_cli_counts_only_and_no_extracted_files(tmp_path, db):
    _, db_path = db
    source = docx(tmp_path, paragraph("01/01/2025") + paragraph("SYNTHETIC_SECRET_SENTINEL"))
    before = set(tmp_path.iterdir())
    result = subprocess.run([sys.executable, "-m", "scripts.ingest.private_teacher_lessons_ingest",
        "--docx", str(source), "--db", str(db_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "BEFORE: source_rows=0" in result.stdout
    assert "AFTER: source_rows=1 inserted=1 skipped=0" in result.stdout
    assert "SYNTHETIC_SECRET_SENTINEL" not in result.stdout + result.stderr
    assert str(source) not in result.stdout + result.stderr
    assert set(tmp_path.iterdir()) == before


def test_cli_dry_run_missing_db_and_private_error_redaction(tmp_path, capsys):
    source = docx(tmp_path, paragraph("01/01/2025") + paragraph("SYNTHETIC_SECRET_SENTINEL"))
    assert ingest.main(["--docx", str(source), "--dry-run"]) == 0
    missing = tmp_path / "missing.db"
    assert ingest.main(["--docx", str(source), "--db", str(missing)]) == 2
    assert not missing.exists()
    source.write_bytes(b"invalid private payload SYNTHETIC_SECRET_SENTINEL")
    assert ingest.main(["--docx", str(source), "--dry-run"]) == 2
    output = capsys.readouterr()
    assert "SYNTHETIC_SECRET_SENTINEL" not in output.out + output.err
    assert str(source) not in output.out + output.err
