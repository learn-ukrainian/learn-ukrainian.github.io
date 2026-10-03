"""Synthetic fixtures only: no book text or writes to the live corpus."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pymupdf
import pytest

from scripts.ingest import pohribnyi_pronunciation_ingest as ingest
from scripts.ingest import pohribnyi_tooling as tooling


@pytest.fixture
def table():
    return tooling.load_notation()


@pytest.fixture
def frozen(table):
    # Synthetic freeze metadata, never evidence of a book inventory review.
    result = copy.deepcopy(table)
    result.update(provisional=False, pending_classes=[], freeze_reviewers=["fixture-a", "fixture-b"])
    for symbol in result["symbols"]:
        symbol["provisional"] = False
    tooling.validate_notation(result)
    return result


def row(text="[а́]", *, page=10, paragraph=1):
    return {
        "page": page,
        "paragraph": paragraph,
        "text": text,
        "underlining": [],
        "status": "adjudicated",
        "adjudicated_by": "fixture-adjudicator",
    }


def packet(*rows):
    return {
        "rows": list(rows),
        "paragraph_counts": {str(page): sum(r["page"] == page for r in rows) for page in {r["page"] for r in rows}},
    }


def test_provisional_inventory_and_starter_codepoints(table):
    assert table["provisional"] is True
    assert {"U+0301", "U+A675", "U+2DF7", "U+0306", "U+0361"} <= {s["codepoint"] for s in table["symbols"]}
    assert "ґ" in table["letters"] and "г" in table["letters"]
    assert table["pending_classes"]


@pytest.mark.parametrize("text", ["[а́]", "[еꙵ]", "[иⷷ]", "[ў]", "[д͡з]", "[ґг]", "[лʼ]"])
def test_starter_symbols_are_preserved(text, table):
    assert tooling.validate_text(text, table)[0]["text"] == text


@pytest.mark.parametrize(
    "text, message",
    [
        ("[a]", "Latin"),
        ("[é]", "Latin"),
        ("[іi]", "Latin"),
        ("[ə]", "Latin"),
        ("[аː]", "Unknown"),
        ("[а\u200b]", "Unknown"),
        ("[у\u0306]", "NFC"),
        ("[и\u0306]", "NFC"),
        ("[а", "Unclosed"),
        ("а]", "Unmatched"),
        ("[[а]]", "Nested"),
        ("[]", "Empty"),
    ],
)
def test_transcription_refusals(text, message, table):
    with pytest.raises(ValueError, match=message):
        tooling.validate_text(text, table)


def test_latin_prose_allowed_and_offsets_stable(table):
    text = "fixture [а́] fixture [ў]"
    spans = tooling.validate_text(text, table)
    assert len(spans) == 2
    assert all(text[s["start"] : s["end"]] == s["text"] for s in spans)


@pytest.mark.parametrize(
    "change",
    [
        {"provisional": "true"},
        {"normalization": "NFD"},
        {"letters": "аa"},
        {"symbols": [{"role": "latin", "codepoint": "U+0061", "provisional": True}]},
        {"symbols": [{"role": "invalid", "codepoint": "U+110000", "provisional": True}]},
        {"symbols": [{"role": "surrogate", "codepoint": "U+D800", "provisional": True}]},
        {"symbols": []},
        {"unknown_field": True},
        {"underlining": {}},
        {"provisional": False},
    ],
)
def test_notation_schema_rejects_invalid_tables(tmp_path, table, change):
    table.update(change)
    path = tmp_path / "table.json"
    path.write_text(json.dumps(table), encoding="utf-8")
    with pytest.raises(ValueError):
        tooling.load_notation(path)


def test_duplicate_symbol_rejected(table):
    table["symbols"].append(copy.deepcopy(table["symbols"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        tooling.validate_notation(table)


@pytest.mark.parametrize(
    "change",
    [
        {"page": True},
        {"page": 29},
        {"paragraph": 0},
        {"text": ""},
        {"underlining": None},
        {"underlining": [{"start": 0, "end": 999}]},
        {"underlining": [{"start": 0, "end": 2}, {"start": 1, "end": 3}]},
    ],
)
def test_row_validation(change, table):
    item = row()
    item.update(change)
    with pytest.raises(ValueError):
        tooling.validate_rows([item], table)


def test_underlining_and_duplicate_locator(table):
    item = row("fixture [а́]")
    item["underlining"] = [{"start": 0, "end": 7}]
    tooling.validate_rows([item], table)
    with pytest.raises(ValueError, match="Duplicate"):
        tooling.validate_rows([item, item], table)


def test_diff_lists_replacement_insert_and_missing_page(table):
    left = [row("[а́] [ў] [д͡з]"), row("[ґ]", page=11)]
    right = [row("[а] [ў] [ґ] [д͡з]")]
    report = tooling.diff_transcriptions(left, right, table)
    spans = [r for r in report["disagreements"] if r["kind"] == "bracketed_span"]
    assert len(spans) == 3
    assert spans[0]["left"]["text"] == "[а́]" and spans[0]["right"]["text"] == "[а]"
    assert spans[1]["left"] is None and spans[1]["right"]["text"] == "[ґ]"
    assert spans[2]["page"] == 11 and spans[2]["right"] is None
    assert report["pages"] == [
        {
            "page": 10,
            "left_paragraphs": 1,
            "right_paragraphs": 1,
            "left_bracketed_spans": 3,
            "right_bracketed_spans": 4,
        },
        {
            "page": 11,
            "left_paragraphs": 1,
            "right_paragraphs": 0,
            "left_bracketed_spans": 1,
            "right_bracketed_spans": 0,
        },
    ]
    assert any(r["kind"] == "missing_paragraph" and r["page"] == 11 for r in report["disagreements"])
    assert all(r["resolution"] is None and r["resolved_by"] is None for r in report["disagreements"])
    assert tooling.diff_transcriptions(left, left, table)["disagreement_count"] == 0


def test_diff_detects_prose_underlining_and_deleted_span(table):
    a, b = row("fixture [а] [ў]"), row("changed [а]")
    b["underlining"] = [{"start": 0, "end": 7}]
    kinds = {r["kind"] for r in tooling.diff_transcriptions([a], [b], table)["disagreements"]}
    assert kinds == {"paragraph_text", "underlining", "bracketed_span"}


@pytest.fixture
def schema_copy(tmp_path):
    # Schema snapshot from read-only sqlite_master inspection, no live data.
    source = sqlite3.connect(tmp_path / "schema.db")
    source.executescript("""
        CREATE TABLE textbooks (
            id INTEGER PRIMARY KEY, chunk_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '', text TEXT NOT NULL DEFAULT '',
            source_file TEXT NOT NULL DEFAULT '', grade TEXT DEFAULT '',
            author TEXT DEFAULT '', char_count INTEGER DEFAULT 0,
            parent_section_id INTEGER REFERENCES textbook_sections(section_id),
            author_uk TEXT DEFAULT '', subject TEXT
        );
        CREATE TABLE textbook_sections (
            section_id INTEGER PRIMARY KEY, source_file TEXT NOT NULL,
            grade INTEGER NOT NULL, section_title TEXT NOT NULL, section_number TEXT,
            page_start INTEGER, page_end INTEGER, chunk_count INTEGER NOT NULL,
            full_text TEXT NOT NULL, UNIQUE (source_file, section_title)
        );
    """)
    db = tmp_path / "copy.db"
    conn = sqlite3.connect(db)
    source.backup(conn)
    source.close()
    ingest.ingest_pages(conn, [ingest.Page(10, "fixture OCR"), ingest.Page(11, "other OCR")])
    conn.commit()
    yield db, conn
    conn.close()


def test_ingest_preserves_ocr_and_locators_and_is_idempotent(schema_copy, frozen):
    _, conn = schema_copy
    before = conn.execute("SELECT chunk_id,text FROM textbooks ORDER BY id").fetchall()
    r = row("fixture [а́]")
    r["underlining"] = [{"start": 0, "end": 7}]
    data = packet(r, row("[ў]", paragraph=2))
    assert ingest.ingest_adjudicated(conn, data, frozen) == (2, 0)
    assert ingest.ingest_adjudicated(conn, data, frozen) == (0, 2)
    assert conn.execute("SELECT chunk_id,text FROM textbooks WHERE id<=2 ORDER BY id").fetchall() == before
    assert conn.execute("SELECT transcription_status FROM textbooks ORDER BY id").fetchall() == [
        ("superseded",),
        (None,),
        ("adjudicated",),
        ("adjudicated",),
    ]
    records = conn.execute(
        "SELECT page_number,paragraph_number,underlining_json,notation_sha256,"
        "parent_section_id FROM textbooks WHERE transcription_status='adjudicated' ORDER BY id"
    ).fetchall()
    assert [(r[0], r[1]) for r in records] == [(10, 1), (10, 2)]
    assert json.loads(records[0][2]) == data["rows"][0]["underlining"]
    assert all(len(r[3]) == 64 and r[4] is not None for r in records)
    assert conn.execute(
        "SELECT page_start,page_end,section_number FROM textbook_sections "
        "WHERE transcription_status='adjudicated' ORDER BY section_id"
    ).fetchall() == [(10, 10, "10.1"), (10, 10, "10.2")]
    assert conn.execute(
        "SELECT full_text FROM textbook_sections WHERE transcription_status='superseded'"
    ).fetchall() == [("fixture OCR\n",)]


def test_ingest_refuses_provisional_and_incomplete_without_schema_changes(schema_copy, table, frozen):
    _, conn = schema_copy
    before = conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    with pytest.raises(ValueError, match="provisional"):
        ingest.ingest_adjudicated(conn, packet(row()), table)
    data = packet(row())
    data["paragraph_counts"]["10"] = 2
    with pytest.raises(ValueError, match="Incomplete"):
        ingest.ingest_adjudicated(conn, data, frozen)
    assert conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before


@pytest.mark.parametrize("change", [{"status": "agreed"}, {"adjudicated_by": ""}, {"text": "[i]"}])
def test_ingest_requires_valid_adjudication(schema_copy, frozen, change):
    _, conn = schema_copy
    r = row()
    r.update(change)
    with pytest.raises(ValueError):
        ingest.ingest_adjudicated(conn, packet(r), frozen)
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


def test_conflicting_ingest_rolls_back_earlier_insert(schema_copy, frozen):
    _, conn = schema_copy
    ingest.ingest_adjudicated(conn, packet(row(page=11)), frozen)
    conn.commit()
    with pytest.raises(ValueError, match="Conflicting"):
        ingest.ingest_adjudicated(conn, packet(row(), row("[ў]", page=11)), frozen)
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3
    assert (
        conn.execute(
            "SELECT transcription_status FROM textbooks WHERE chunk_id=?", (f"{ingest.SOURCE_FILE}_p10",)
        ).fetchone()[0]
        is None
    )


def test_sql_failure_rolls_back_migration_and_supersession(schema_copy, frozen):
    _, conn = schema_copy
    conn.execute("CREATE TRIGGER refuse_insert BEFORE INSERT ON textbooks BEGIN SELECT RAISE(ABORT,'fixture'); END")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError, match="fixture"):
        ingest.ingest_adjudicated(conn, packet(row()), frozen)
    assert "transcription_status" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


def test_render_300dpi_hash_and_ignore_guard(tmp_path, monkeypatch):
    pdf = tmp_path / "fixture.pdf"
    with pymupdf.open() as doc:
        doc.new_page(width=72, height=72)
        doc.save(pdf)
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    # Use the real worktree Git ignore rules; generated image remains private.
    cache = Path(".cache") / tmp_path.name
    manifest = tooling.render_pages(pdf, cache, expected_sha256=digest, expected_pages=1)
    assert manifest["page_count"] == 1 and manifest["dpi"] == 300
    image = pymupdf.Pixmap(cache / "page-01.png")
    assert (image.width, image.height, image.xres, image.yres) == (300, 300, 300, 300)
    assert manifest["pages"][0]["sha256"] == hashlib.sha256((cache / "page-01.png").read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="SHA"):
        tooling.render_pages(pdf, cache, expected_sha256="0" * 64, expected_pages=1)
    with pytest.raises(ValueError, match="denominator"):
        tooling.render_pages(pdf, cache, expected_sha256=digest, expected_pages=2)
    with pytest.raises(ValueError, match="Git-ignored"):
        tooling.render_pages(pdf, Path("public-images"), expected_sha256=digest, expected_pages=1)
    with pytest.raises(ValueError, match="inside"):
        tooling.render_pages(pdf, tmp_path, expected_sha256=digest, expected_pages=1)


def test_tooling_cli_validate_diff_and_invalid_input(tmp_path, capsys):
    a, b, output = tmp_path / "a.json", tmp_path / "b.json", tmp_path / "diff.json"
    a.write_text(json.dumps([row()]), encoding="utf-8")
    b.write_text(json.dumps([row("[а]")]), encoding="utf-8")
    assert tooling.main(["validate", "--input", str(a)]) == 0
    assert tooling.main(["diff", "--left", str(a), "--right", str(b), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["disagreement_count"] == 2
    a.write_text(json.dumps([row("[a]")]), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        tooling.main(["validate", "--input", str(a)])
    assert exc.value.code == 1
    assert "Latin codepoint" in capsys.readouterr().err


def test_ingest_cli_private_packet_and_dry_run(schema_copy, frozen, tmp_path, capsys):
    db, conn = schema_copy
    data, notation = tmp_path / "rows.json", tmp_path / "notation.json"
    data.write_text(json.dumps(packet(row())), encoding="utf-8")
    notation.write_text(json.dumps(frozen), encoding="utf-8")
    args = ["--adjudicated", str(data), "--notation", str(notation), "--db", str(db)]
    assert ingest.main([*args, "--dry-run"]) == 0
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2
    assert ingest.main(args) == 0
    assert "inserted=1, skipped=0" in capsys.readouterr().out
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3
    with pytest.raises(SystemExit):
        ingest.main([*args, "--force"])
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--adjudicated", str(data), "--db", str(db)])
    assert exc.value.code == 1


def test_ingest_transaction_is_owned_by_caller(schema_copy, frozen):
    _, conn = schema_copy
    assert not conn.in_transaction
    ingest.ingest_adjudicated(conn, packet(row()), frozen)
    assert conn.in_transaction
    conn.rollback()
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2
    assert "transcription_status" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}


def test_ingest_requires_retained_ocr_page(schema_copy, frozen):
    _, conn = schema_copy
    with pytest.raises(ValueError, match="retained OCR"):
        ingest.ingest_adjudicated(conn, packet(row(page=12)), frozen)
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"rows": []},
        {"rows": [row()], "paragraph_counts": {}},
        {"rows": [row()], "paragraph_counts": {"10": True}},
    ],
)
def test_invalid_adjudicated_packets(data, frozen):
    with pytest.raises(ValueError):
        ingest.validate_adjudicated_packet(data, frozen)


def test_freeze_requires_complete_nonprovisional_table(frozen):
    frozen["symbols"][0]["provisional"] = True
    with pytest.raises(ValueError, match="provisional symbols"):
        tooling.validate_notation(frozen)
    frozen["symbols"][0]["provisional"] = False
    frozen["freeze_reviewers"] = ["one"]
    with pytest.raises(ValueError, match="two reviewers"):
        tooling.validate_notation(frozen)


def test_render_cli_prints_only_manifest_summary(monkeypatch, capsys):
    calls = []

    def render(pdf, cache):
        calls.append((pdf, cache))
        return {"page_count": 28, "dpi": 300, "pdf_sha256": tooling.PDF_SHA256}

    monkeypatch.setattr(tooling, "render_pages", render)
    assert tooling.main(["render", "--pdf", "held.pdf"]) == 0
    assert calls == [(Path("held.pdf"), tooling.CACHE_DIR)]
    assert json.loads(capsys.readouterr().out)["page_count"] == 28


def test_ingest_cli_refuses_missing_db_without_creating_it(tmp_path, frozen):
    data, notation, missing = tmp_path / "rows.json", tmp_path / "table.json", tmp_path / "missing.db"
    data.write_text(json.dumps(packet(row())), encoding="utf-8")
    notation.write_text(json.dumps(frozen), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--adjudicated", str(data), "--notation", str(notation), "--db", str(missing)])
    assert exc.value.code == 1
    assert not missing.exists()
