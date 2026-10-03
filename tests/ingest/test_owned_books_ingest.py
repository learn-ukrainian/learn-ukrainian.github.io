"""Synthetic private fixtures prove extraction, full accounting and corpus rehearsal."""

import argparse
import io
import sqlite3
import zipfile
from pathlib import Path

import pymupdf
import pytest
import yaml
from docx import Document

from scripts.ingest import owned_books_ingest as owned

SCHEMA = """
CREATE TABLE textbooks (
 id INTEGER PRIMARY KEY, chunk_id TEXT UNIQUE, title TEXT, text TEXT,
 source_file TEXT, grade TEXT, author TEXT, author_uk TEXT, char_count INTEGER
);
CREATE VIRTUAL TABLE textbooks_fts USING fts5(title,text,content='textbooks',content_rowid='id');
CREATE TRIGGER textbooks_ai AFTER INSERT ON textbooks BEGIN
 INSERT INTO textbooks_fts(rowid,title,text) VALUES(new.id,new.title,new.text);
END;
"""


def pdf(*pages, encrypted=False):
    with pymupdf.open() as doc:
        for text in pages:
            page = doc.new_page()
            if text:
                page.insert_text((40, 40), text)
        return (
            doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="synthetic", user_pw="synthetic")
            if encrypted
            else doc.tobytes()
        )


def archive(members):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        for name, content in members:
            z.writestr(name, content)
    return stream.getvalue()


def docx(*paragraphs):
    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    table = doc.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "Synthetic table content."
    stream = io.BytesIO()
    doc.save(stream)
    return stream.getvalue()


def epub():
    return archive(
        [
            (
                "META-INF/container.xml",
                '<container><rootfiles><rootfile full-path="book/package.opf"/></rootfiles></container>',
            ),
            (
                "book/package.opf",
                '<package><manifest><item id="z" href="z.xhtml"/><item id="a" href="a.xhtml"/></manifest><spine><itemref idref="z"/><itemref idref="a"/></spine></package>',
            ),
            ("book/a.xhtml", "<html><body>Second chapter.</body></html>"),
            ("book/z.xhtml", "<html><body>First chapter.<script>Hidden code.</script></body></html>"),
        ]
    )


def pptx():
    return archive(
        [
            (
                "ppt/presentation.xml",
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><p:sldIdLst><p:sldId id="256" r:id="second"/><p:sldId id="257" r:id="first"/></p:sldIdLst></p:presentation>',
            ),
            (
                "ppt/_rels/presentation.xml.rels",
                '<Relationships><Relationship Id="first" Target="slides/slide1.xml"/><Relationship Id="second" Target="slides/slide2.xml"/></Relationships>',
            ),
            (
                "ppt/slides/slide1.xml",
                '<slide xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:p><a:t>Last </a:t><a:t>slide.</a:t></a:p></slide>',
            ),
            (
                "ppt/slides/slide2.xml",
                '<slide xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:p><a:t>First </a:t><a:t>slide.</a:t></a:p></slide>',
            ),
        ]
    )


@pytest.fixture
def env(tmp_path):
    db = tmp_path / "corpus.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(SCHEMA)
    root = tmp_path / "drive-ukrainian"
    root.mkdir()
    inventory = tmp_path / "INVENTORY.yaml"
    return db, root, inventory, tmp_path / "private-jsonl"


def row(**updates):
    result = {
        "id": "synthetic-work",
        "title": "Synthetic reference",
        "author": "Synthetic author",
        "rights": "owned_cite_only",
        "files": ["**/*.pdf"],
    }
    result.update(updates)
    return result


def args(env, rows=None, **updates):
    db, _root, inventory, out = env
    inventory.write_text(yaml.safe_dump({"schema": 1, "works": rows or [row()]}))
    result = argparse.Namespace(
        inventory=inventory, out_dir=out, db=db, check=False, dry_run=False, force=False, only=None
    )
    for key, value in updates.items():
        setattr(result, key, value)
    return result


def test_ingest_noop_check_force_and_stale_input(env):
    db, root, _inventory, out = env
    file = root / "fixture.pdf"
    file.write_bytes(pdf("Extraordinaryword original sentence."))
    request = args(env)
    report, code = owned.run(request)
    assert code == 0 and report["rows"][0]["status"] == "ingested"
    assert report["rows"][0]["retrieval"]["chunk_id"].startswith("owned-synthetic-work_")
    before = db.read_bytes(), {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()}
    assert owned.run(request)[1] == 0
    assert before == (db.read_bytes(), {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()})
    request.check = True
    assert owned.run(request)[1] == 0
    file.write_bytes(pdf("Replacementword completely changed sentence."))
    assert owned.run(request)[0]["rows"][0]["status"] == "error:stale_input"
    request.check = False
    request.force = True
    assert owned.run(request)[1] == 0
    with sqlite3.connect(db) as conn:
        assert not conn.execute(
            "SELECT rowid FROM textbooks_fts WHERE textbooks_fts MATCH 'Extraordinaryword'"
        ).fetchall()
        assert conn.execute("SELECT rowid FROM textbooks_fts WHERE textbooks_fts MATCH 'Replacementword'").fetchall()
        assert conn.execute("SELECT count(*) FROM textbook_sections").fetchone()[0] == 1
    assert "Replacementword" in (out / "owned-synthetic-work.jsonl").read_text()


@pytest.mark.parametrize("mode", ["dry_run", "check"])
def test_read_only_modes_never_write(env, mode):
    db, root, _inventory, out = env
    (root / "fixture.pdf").write_bytes(pdf("Synthetic readable sentence."))
    request = args(env, **{mode: True})
    before = db.read_bytes()
    report, code = owned.run(request)
    assert code == (mode == "check")
    assert report["rows"][0]["status"] == ("error:not_ingested" if mode == "check" else "ingested")
    assert db.read_bytes() == before and not out.exists()


@pytest.mark.parametrize(
    "extension,content,expected",
    [
        (".pdf", lambda: pdf("First sentence.", "Second sentence."), ["First sentence.", "Second sentence."]),
        (
            ".docx",
            lambda: docx("First paragraph.", "Second paragraph."),
            ["First paragraph.", "Second paragraph.", "Synthetic table content."],
        ),
        (".epub", epub, ["First chapter.", "Second chapter."]),
        (".pptx", pptx, ["First slide.", "Last slide."]),
    ],
)
def test_format_extraction_follows_document_order(extension, content, expected):
    units, pages, status = owned.extract(content(), extension)
    text = "\n".join(t for _, t in units)
    assert status == "extracted"
    assert all(p["status"] == "text" for p in pages)
    assert [text.index(part) for part in expected] == sorted(text.index(part) for part in expected)
    assert "Hidden code" not in text


def test_mixed_and_scanned_pdf_account_for_every_page():
    units, pages, status = owned.extract(pdf("Synthetic content.", "", "More content."), ".pdf")
    assert status == "extracted" and len(units) == 2
    assert [p["status"] for p in pages] == ["text", "page_no_text", "text"]
    units, pages, status = owned.extract(pdf("Synthetic content.", "", ""), ".pdf")
    assert status == "skipped:scanned_needs_ocr" and not units and len(pages) == 3
    assert owned.extract(pdf(""), ".pdf")[2] == "skipped:scanned_needs_ocr"


@pytest.mark.parametrize(
    "payload,extension,code",
    [
        (lambda: pdf("Protected.", encrypted=True), ".pdf", "encrypted"),
        (lambda: b"not a PDF", ".pdf", "corrupt"),
        (lambda: b"not a docx", ".docx", "corrupt"),
        (lambda: archive([]), ".epub", "corrupt"),
        (lambda: archive([]), ".pptx", "corrupt"),
        (lambda: b"unknown content", ".unknown", "unsupported_format"),
    ],
)
def test_closed_extraction_errors(payload, extension, code):
    with pytest.raises(owned.IngestError, match=f"^{code}$"):
        owned.extract(payload(), extension)


def test_archive_sorting_nested_depth_ignored_members_and_size_cap(env, monkeypatch):
    _db, root, _inventory, out = env
    a = pdf("Alphabeticalword first content.")
    z = pdf("Zoologicalword second content.")
    packed = archive(
        [
            ("z.pdf", z),
            ("a.pdf", a),
            ("__MACOSX/secret.pdf", z),
            (".DS_Store", "secret"),
            ("nested.zip", archive([("inner.pdf", z), ("deeper.zip", archive([("deep.pdf", z)]))])),
            ("audio.mp3", "sound"),
            ("bad.bin", b"unknown"),
        ]
    )
    (root / "fixture.zip").write_bytes(packed)
    request = args(env, [row(files=["*.zip"])], dry_run=True)
    report, code = owned.run(request)
    assert code == 1  # unknown leaf never hidden by another successful chunk
    file_reports = report["rows"][0]["files"]
    assert file_reports[1]["file_index"] == "1.1"
    assert any(f["status"] == "skipped:nested_archive_depth" for f in file_reports)
    assert any(f["status"] == "error:unsupported_format" for f in file_reports)
    assert any(f["status"] == "skipped:audio_or_deck" for f in file_reports)
    monkeypatch.setattr(owned, "MEMBER_CAP", 10)
    report, code = owned.run(request)
    assert any(f["status"] == "skipped:member_too_large" for f in report["rows"][0]["files"])
    assert not out.exists()


def test_pdf_only_archive_filter(env):
    _db, root, _inventory, _out = env
    (root / "fixture.zip").write_bytes(
        archive([("file.pdf", pdf("Syntheticword readable text.")), ("file.docx", docx("Ignore me."))])
    )
    report, code = owned.run(args(env, [row(files=["*.zip"], ingest="pdf_text_only")]))
    assert code == 0 and report["rows"][0]["chunks"] == 1
    assert report["rows"][0]["files"][-1]["status"] == "extracted"
    assert any(f["status"] == "skipped:pdf_text_only" for f in report["rows"][0]["files"])


@pytest.mark.parametrize(
    "text,ratio,duplicate",
    [
        ("First synthetic sentence. Second synthetic sentence.", 1.0, True),
        ("First synthetic sentence. Completely novel sentence.", 0.5, False),
        ("Brandnewword entirely novel sentence.", 0.0, False),
    ],
)
def test_ulp_dedupe_includes_sentence_across_existing_chunk_boundaries(env, text, ratio, duplicate):
    db, root, _inventory, _out = env
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO textbooks(chunk_id,source_file,text) VALUES('lesson-1','ulp-1-00-lesson-notes','First synthetic')"
        )
        conn.execute(
            "INSERT INTO textbooks(chunk_id,source_file,text) VALUES('lesson-2','ulp-1-00-lesson-notes','sentence. Second synthetic sentence.')"
        )
    (root / "Season 1.pdf").write_bytes(pdf(text))
    request = args(env, [row(ingest="new_text_only")])
    report, code = owned.run(request)
    assert code == 0
    entry = report["rows"][0]["files"][0]
    assert entry["overlap_ratio"] == ratio
    assert (entry["status"] == "duplicate_of:ulp-1-00-lesson-notes") is duplicate
    request.check = True
    assert owned.run(request)[1] == 0


def test_normalisation_furniture_nfc_and_stress():
    assert owned.normalise("cafe\u0301\n  123\n  Hello   world.  \nUkrainianLessons.com") == "café Hello world."
    assert owned.sentences("First sentence\nwrapped here. Second sentence!") == [
        "First sentence wrapped here.",
        "Second sentence!",
    ]
    assert owned.season_hint("Season 3.zip") == 3
    assert owned.season_hint("unmarked.pdf", 4) == 4
    assert owned.season_hint("unknown") is None
    assert owned.overlap_ratio([], set()) == 0


@pytest.mark.parametrize("state", sorted(owned.SKIPS))
def test_typed_inventory_skip(env, state):
    report, code = owned.run(args(env, [row(ingest=state)], check=True))
    assert code == 0 and report["rows"][0]["status"] == f"skipped:{state}"


def test_legacy_identity_rights_only_and_missing_source(env):
    db, root, _inventory, out = env
    (root / "existing.pdf").write_bytes(pdf("Legacyword unchanged work."))
    request = args(env, [row(ingest="already_ingested", source_file="legacy-book", title=None, author=None)])
    assert owned.run(request)[0]["rows"][0]["status"] == "error:existing_source_missing"
    with sqlite3.connect(db) as conn:
        conn.execute(
            "INSERT INTO textbooks(chunk_id,source_file,text) VALUES('legacy-id','legacy-book','Existing body')"
        )
    before = db.read_bytes()
    assert owned.run(request)[0]["rows"][0]["status"] == "already_ingested"
    assert db.read_bytes() == before and not out.exists()


def test_missing_expected_file_and_unexplained_row_fail_check(env):
    request = args(env, check=True)
    report, code = owned.run(request)
    assert code == 1 and report["rows"][0]["status"] == "error:missing_file"
    assert report["rows"][0]["files"] == [{"file_index": "pattern-1", "status": "error:missing_file"}]
    request = args(env, [row(files=[])], check=True)
    with pytest.raises(owned.IngestError, match="invalid_inventory"):
        owned.run(request)


def test_partial_success_ingests_available_text_without_hiding_file_errors(env):
    db, root, _inventory, out = env
    (root / "good.pdf").write_bytes(pdf("Syntheticword readable text."))
    (root / "broken.pdf").write_bytes(b"corrupt")
    report, code = owned.run(args(env))
    assert code == 1 and report["rows"][0]["status"] == "error:file_failure"
    assert len(report["rows"][0]["files"]) == 2 and out.exists()
    with sqlite3.connect(db) as conn:
        assert conn.execute("select count(*) from textbooks").fetchone()[0] == 1
    request = args(env, check=True)
    assert owned.run(request)[1] == 1


def test_private_name_and_content_never_appear_in_diagnostics_or_db_metadata(env, capsys, caplog):
    db, root, inventory, out = env
    sentinel = "SENSITIVE_NAME_SENTINEL"
    (root / f"{sentinel}.docx").write_bytes(docx(f"{sentinel} Syntheticword content."))
    args(
        env,
        [row(id="teacher-a-slides", rights="private_permission", title=sentinel, author=sentinel, files=["*.docx"])],
    )
    assert owned.main(["--inventory", str(inventory), "--out-dir", str(out), "--db", str(db)]) == 0
    captured = capsys.readouterr()
    assert sentinel not in captured.out + captured.err + caplog.text
    with sqlite3.connect(db) as conn:
        metadata = conn.execute(
            "SELECT chunk_id,title,source_file,grade,author,author_uk,subject FROM textbooks"
        ).fetchall()
        sections = conn.execute("SELECT source_file,section_title,section_number FROM textbook_sections").fetchall()
    assert sentinel not in str(metadata) + str(sections)
    assert metadata[0][1] == "Teacher materials A" and metadata[0][4:6] == ("", "")
    assert sentinel not in Path("registry/sources/owned-rights.yaml").read_text()
    # Broken input also stays sanitized; messages never carry private filenames.
    (root / f"{sentinel}.docx").write_bytes(sentinel.encode())
    assert owned.main(["--inventory", str(inventory), "--out-dir", str(out), "--db", str(db), "--force"]) == 1
    captured = capsys.readouterr()
    assert sentinel not in captured.out + captured.err + caplog.text


def test_chunk_ids_and_metadata_are_stable_and_lossless(monkeypatch):
    monkeypatch.setattr(owned, "CHUNK_SIZE", 5)
    content = "abcdefghij whole content"
    result = owned.chunks(row(author=None), [("1", 3, content)])
    assert "".join(r["text"] for r in result) == content
    assert result == owned.chunks(row(author=None), [("1", 3, content)])
    assert result[0]["chunk_id"] == "owned-synthetic-work_f1_p0003_c0001"
    assert result[0]["author"] == result[0]["author_uk"] == ""


def test_saved_artifacts_and_db_links_must_match(env):
    db, root, _inventory, out = env
    (root / "fixture.pdf").write_bytes(pdf("Syntheticword test content."))
    request = args(env)
    assert owned.run(request)[1] == 0
    request.check = True
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE textbooks SET parent_section_id=NULL")
    assert owned.run(request)[0]["rows"][0]["status"] == "error:artifact_mismatch"
    request.check = False
    request.force = True
    assert owned.run(request)[1] == 0
    request.check = True
    (out / "owned-synthetic-work.jsonl").write_text("invalid json")
    assert owned.run(request)[0]["rows"][0]["status"] == "error:artifact_mismatch"
    (out / "owned-synthetic-work.manifest.json").write_text("invalid json")
    assert owned.run(request)[0]["rows"][0]["status"] == "error:invalid_receipt"


def test_path_refusals_and_cli_errors_are_sanitized(env, monkeypatch, capsys):
    db, _root, _inventory, out = env
    request = args(env)
    request.out_dir = owned.REPOSITORY / "private-output"
    with pytest.raises(owned.IngestError, match="output_inside_repository"):
        owned.run(request)
    request.out_dir = out
    monkeypatch.setattr(owned, "is_network_filesystem_path", lambda p: True)
    with pytest.raises(owned.IngestError, match="network_database_refused"):
        owned.run(request)
    monkeypatch.setattr(owned, "is_network_filesystem_path", lambda p: False)
    request.db = db.parent / "missing.db"
    with pytest.raises(owned.IngestError, match="database_missing"):
        owned.run(request)
    with pytest.raises(SystemExit) as exc:
        owned.main(["--SENSITIVE_NAME_SENTINEL"])
    assert exc.value.code == 2
    assert "SENSITIVE_NAME_SENTINEL" not in capsys.readouterr().err


def test_inventory_validation_unknown_id_and_entrypoint_failure(env, capsys):
    db, _root, inventory, out = env
    request = args(env, only="unregistered")
    with pytest.raises(owned.IngestError, match="unknown_id"):
        owned.run(request)
    inventory.write_text("invalid yaml: [")
    assert owned.main(["--inventory", str(inventory), "--out-dir", str(out), "--db", str(db)]) == 1
    assert "invalid_inventory" in capsys.readouterr().out


def test_unique_encrypted_zip_and_xml_entity_boundaries():
    info = zipfile.ZipInfo("hidden.pdf")
    info.file_size = owned.MEMBER_CAP + 1
    with pytest.raises(owned.IngestError, match="member_too_large"):
        owned.read_member(None, info)
    info.file_size = 3
    info.flag_bits = 1
    with pytest.raises(owned.IngestError, match="encrypted"):
        owned.read_member(None, info)
    tree = owned.xml(b'<!DOCTYPE p [<!ENTITY secret SYSTEM "file:///synthetic-secret">]><p>&secret;</p>')
    assert tree.text is None


def test_fts_delete_trigger_variant_and_retrieval_failure(env):
    db, _root, _inventory, _out = env
    with sqlite3.connect(db) as conn:
        conn.execute(
            "CREATE TRIGGER textbooks_ad AFTER DELETE ON textbooks BEGIN INSERT INTO textbooks_fts(textbooks_fts,rowid,title,text) VALUES('delete',old.id,old.title,old.text); END"
        )
        record = owned.chunks(row(), [("1", 1, "Syntheticword original content.")])
        owned.replace_work(conn, "owned-synthetic-work", record)
        record[0]["text"] = "Replacementword new content."
        owned.replace_work(conn, "owned-synthetic-work", record)
        assert not conn.execute("SELECT rowid FROM textbooks_fts WHERE textbooks_fts MATCH 'Syntheticword'").fetchall()
        assert owned.retrieval_proof(conn, "owned-synthetic-work")["token"]
        with pytest.raises(owned.IngestError, match="retrieval_unverified"):
            owned.retrieval_proof(conn, "unknown")


def test_rehearsal_jsonl_loads_separate_db_without_rewriting_artifacts(env):
    db, root, _inventory, out = env
    (root / "fixture.pdf").write_bytes(pdf("Syntheticword readable fixture."))
    request = args(env)
    assert owned.run(request)[1] == 0
    original = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()}
    second = db.with_name("second.db")
    with sqlite3.connect(second) as conn:
        conn.executescript(SCHEMA)
    request.db = second
    request.check = True
    assert owned.run(request)[1] == 1
    request.check = False
    request.dry_run = True
    assert owned.run(request)[1] == 0
    with sqlite3.connect(second) as conn:
        assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 0
    request.dry_run = False
    assert owned.run(request)[1] == 0
    assert original == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in out.iterdir()}
    request.check = True
    assert owned.run(request)[1] == 0


def test_unexplained_inventory_state_reports_that_row_and_keeps_denominator(env):
    report, code = owned.run(
        args(env, [row(ingest="unexplained"), row(id="skipped-work", ingest="missing_source")], check=True)
    )
    assert code == 1 and report["denominator"] == 2
    assert report["rows"][0]["status"] == "error:unexplained_row"
    assert report["rows"][1]["status"] == "skipped:missing_source"


def test_pdf_page_error_does_not_hide_other_pages_or_private_exception(monkeypatch):
    original = pymupdf.Page.get_text

    def get_text(page, *args, **kwargs):
        if page.number == 1:
            raise ValueError("SENSITIVE_NAME_SENTINEL")
        return original(page, *args, **kwargs)

    monkeypatch.setattr(pymupdf.Page, "get_text", get_text)
    units, pages, status = owned.extract(pdf("First page.", "Second page.", "Third page."), ".pdf")
    assert status == "error:corrupt"
    assert [page["status"] for page in pages] == ["text", "error:corrupt", "text"]
    assert [page for page, _ in units] == [1, 3]
    assert "SENSITIVE_NAME_SENTINEL" not in str(pages)


def test_archive_crc_failure_accounts_for_leaf_and_continues_other_members(env):
    _db, root, _inventory, _out = env
    payload = pdf("Corruptibleword sentence.")
    data = bytearray(archive([("a.pdf", payload), ("b.pdf", pdf("Retainedword sentence."))]))
    offset = data.index(payload)
    data[offset] ^= 1
    (root / "archive.zip").write_bytes(data)
    report, code = owned.run(args(env, [row(files=["*.zip"])]))
    assert code == 1
    assert report["rows"][0]["files"][1]["status"] == "error:corrupt"
    assert report["rows"][0]["files"][2]["status"] == "extracted"
    assert report["rows"][0]["chunks"] == 1


def test_inline_markup_preserves_words_and_block_boundaries():
    payload = archive(
        [
            ("META-INF/container.xml", '<container><rootfile full-path="package.opf"/></container>'),
            (
                "package.opf",
                '<package><manifest><item id="c" href="chapter.xhtml"/></manifest><spine><itemref idref="c"/></spine></package>',
            ),
            ("chapter.xhtml", "<html><body><p>Extra<b>ordinary</b>word.</p><p>Next paragraph.</p></body></html>"),
        ]
    )
    assert owned.package_text(payload, ".epub") == [(1, "Extraordinaryword.\n\nNext paragraph.")]
    payload = archive(
        [
            ("ppt/presentation.xml", '<p xmlns:r="relationships"><sldId r:id="slide"/></p>'),
            ("ppt/_rels/presentation.xml.rels", '<rels><rel Id="slide" Target="slides/slide.xml"/></rels>'),
            (
                "ppt/slides/slide.xml",
                '<slide xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:p><a:t>Extra</a:t><a:t>ordinaryword.</a:t></a:p><a:p><a:t>Next paragraph.</a:t></a:p></slide>',
            ),
        ]
    )
    assert owned.package_text(payload, ".pptx") == [(1, "Extraordinaryword.\nNext paragraph.")]
