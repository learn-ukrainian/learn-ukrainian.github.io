"""Synthetic fixtures only: no book text or writes to the live corpus."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import unicodedata
from itertools import permutations
from pathlib import Path

import pymupdf
import pytest

from scripts.ingest import pohribnyi_pronunciation_ingest as ingest
from scripts.ingest import pohribnyi_tooling as tooling
from tests.pohribnyi_schema import open_schema_copy


@pytest.fixture
def table():
    return tooling.load_notation()


@pytest.fixture
def frozen(table):
    return copy.deepcopy(table)


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


def test_frozen_inventory_and_provenance(table):
    assert table["status"] == "frozen" and table["provisional"] is False
    assert table["pending_classes"] == []
    assert table["freeze_reviewers"] == [
        "gpt-6.1-sol/e3c-freeze-sol", "claude-opus-5-5/e3c-freeze-opus",
    ]
    assert table["driver_reconciliation"]["issue"] == 9604
    assert table["driver_reconciliation"]["driver"] == "claude-open-model-data"
    assert {"U+A675", "U+2DF7", "U+A677", "U+2DEA", "U+1E08F", "U+1ABB", "U+1ABC",
            "U+0301", "U+0300", "U+032D", "U+0358", "U+0361", "U+02B9", "U+02BC",
            "U+02D0", "U+044B", "U+0020", "U+002C", "U+003B", "U+2010", "U+2013",
            "U+1E034", "U+1E036", "U+1E037", "U+1E040", "U+1E044", "U+1E045", "U+1E046",
            "U+045E", "U+0439", "U+0450", "U+045D"} <= {s["codepoint"] for s in table["symbols"]}
    assert set("ґгы") <= set(table["letters"])
    assert set("ўйѐѝ") <= set(table["precomposed_letters"])
    for symbol in table["symbols"]:
        assert symbol["provisional"] is False
        assert symbol["source_page"] >= 4
        if symbol["source_kind"] in {"key", "body"}:
            assert symbol["definition_uk"]


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
        ("[аˈ]", "Unknown"),
        ("[л·]", "Unknown"),
        ("[н:]", "Unknown"),
        ("[еⁱ]", "Latin"),
        ("[еꙶ]", "Unknown"),
        ("[а\u0378]", "Unassigned"),
        ("fixture \u0378 [а]", "Unassigned"),
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


@pytest.mark.parametrize("mark, letter", [
    ("\ua675", "и"), ("\u2df7", "е"), ("\ua677", "у"),
    ("\u2dea", "о"), ("\U0001e08f", "і"),
])
@pytest.mark.parametrize("degree_mark, degree", [("", 0), ("\u1abb", 1), ("\u1abc", 2)])
@pytest.mark.parametrize("stress_mark, stress", [("", None), ("\u0301", "primary"), ("\u0300", "secondary")])
def test_approximation_degree_stress_roundtrip(mark, letter, degree_mark, degree, stress_mark, stress, table):
    text = f"[е{mark}{degree_mark}{stress_mark}]"
    groups = tooling.parse_transcription(text, table)
    assert groups[0]["base"] == "е"
    assert groups[0]["approximation_letter"] == letter
    assert groups[0]["degree"] == degree
    assert groups[0]["stress"] == stress
    assert tooling.serialize_transcription(groups, table) == text


@pytest.mark.parametrize("point, letter", [
    (0x1E034, "д"), (0x1E037, "з"), (0x1E044, "ц"), (0x1E036, "ж"),
    (0x1E046, "ш"), (0x1E045, "ч"), (0x1E040, "т"),
])
@pytest.mark.parametrize("softness, value", [("", None), ("ʹ", "soft"), ("ʼ", "half_soft")])
def test_raised_letters_keep_their_own_softness_and_survive_nfc(point, letter, softness, value, table):
    text = f"[дʹː{chr(point)}{softness}а]"
    groups = tooling.parse_transcription(text, table)
    assert groups[0]["softness"] == "soft"
    assert groups[0]["length"] is True
    assert groups[0]["raised_group"] == [{"letter": letter, "tie": False, "softness": value}]
    assert tooling.serialize_transcription(groups, table) == text
    assert tooling.normalize_transcription(text, table) == text
    folded = unicodedata.normalize("NFKC", text)
    assert folded != text
    assert tooling.diff_transcriptions([row(text)], [row(folded)], table)["disagreement_count"] > 0


def test_raised_affricate_tie_and_softness_roundtrip(table):
    text = "[дʹ\U0001e034͡\U0001e037ʹі́]"
    groups = tooling.parse_transcription(text, table)
    assert groups[0]["raised_group"] == [
        {"letter": "д", "tie": True, "softness": None},
        {"letter": "з", "tie": False, "softness": "soft"},
    ]
    assert tooling.serialize_transcription(groups, table) == text


@pytest.mark.parametrize("text", [
    "[л͘и́]", "[р̭]", "[лʹ]", "[лʼ]", "[нʹː]", "[д͡зʹ]", "[д͡ж]",
    "[ўйѐѝы]", "[а б,в;г‐д–е]", "[ї́й́ў̀]", "[ЎЙЀЍЫ]",
])
def test_other_symbol_classes_roundtrip(text, table):
    groups = tooling.parse_transcription(text, table)
    assert tooling.serialize_transcription(groups, table) == text


def test_all_mark_classes_in_reconciled_order(table):
    text = "[е\u032d\ua675\u1abb\u0301\u0358\u0361ʹː\U0001e034͡\U0001e037ʹа]"
    groups = tooling.parse_transcription(text, table)
    assert groups[0]["devoicing"] and groups[0]["slight_softening"] and groups[0]["tie"]
    assert tooling.serialize_transcription(groups, table) == text
    assert tooling.normalize_transcription(text, table) == text


@pytest.mark.parametrize("marks", ["".join(p) for p in permutations("\ua675\u1abb\u0301") if p != tuple("\ua675\u1abb\u0301")])
def test_equal_class_permutations_are_rejected(marks, table):
    text = f"[е{marks}]"
    assert unicodedata.normalize("NFC", text) == text
    with pytest.raises(ValueError, match="combining mark order"):
        tooling.validate_text(text, table)


@pytest.mark.parametrize("text, message", [
    ("[е̭́]", "NFC"), ("[л͘͡з]", "NFC"),
    ("[нːʹ]", "base letter"), ("[нʹʹ]", "base letter"), ("[нːː]", "base letter"),
    ("[ʹн]", "base letter"), ("[\U0001e034а]", "base letter"),
    ("[д\U0001e034ːа]", "base letter"), ("[д\U0001e034́а]", "base letter"),
    ("[е\u1abb]", "requires an approximation"), ("[еꙵⷷ]", "Duplicate approximation"),
    ("[е́̀]", "Duplicate stress"), ("[еꙵ\u1abb\u1abc]", "Duplicate degree"),
    ("[л͘͘]", "Duplicate slight"), ("[р̭̭]", "Duplicate devoicing"),
    ("[д͡͡з]", "Duplicate tie"), ("[д͡]", "following base"),
    ("[д\U0001e034͡а]", "following raised"), ("[ӑ]", "NFC"),
    ("[ӗ]", "NFC"), ("[о̆]", "intrinsic"),
])
def test_structural_and_order_refusals(text, message, table):
    with pytest.raises(ValueError, match=message):
        tooling.validate_text(text, table)


@pytest.mark.parametrize("text", ["prose [а]", "[а] [б]", "а"])
def test_structured_parser_requires_one_whole_span(text, table):
    with pytest.raises(ValueError, match="exactly one"):
        tooling.parse_transcription(text, table)


def test_serializer_refuses_fields_that_do_not_roundtrip(table):
    groups = tooling.parse_transcription("[а]", table)
    groups[0]["degree"] = 1
    with pytest.raises(ValueError, match="requires an approximation"):
        tooling.serialize_transcription(groups, table)
    groups[0]["degree"] = 0
    groups[0]["extra"] = "not serializable"
    with pytest.raises(ValueError, match="does not round-trip"):
        tooling.serialize_transcription(groups, table)


@pytest.mark.parametrize("field, value", [("glyph", "а"), ("unicode_name", "wrong"), ("combining_class", 0)])
def test_notation_checks_unicode_metadata(field, value, table):
    table["symbols"][0][field] = value
    with pytest.raises(ValueError, match="metadata mismatch"):
        tooling.validate_notation(table)


def test_notation_refuses_unassigned_symbols(table):
    table["symbols"][0]["codepoint"] = "U+0378"
    with pytest.raises(ValueError, match="Unassigned"):
        tooling.validate_notation(table)


def test_notation_pins_reconciled_order(table):
    order = table["combining_mark_order"]
    order[2], order[9] = order[9], order[2]
    with pytest.raises(ValueError, match="driver reconciliation"):
        tooling.validate_notation(table)


def test_notation_requires_unicode_15(monkeypatch, table):
    monkeypatch.setattr(tooling.unicodedata, "unidata_version", "14.0.0")
    with pytest.raises(ValueError, match="Unicode 15"):
        tooling.validate_notation(table)


def test_notation_rejects_inconsistent_status(table):
    table["status"] = "provisional"
    with pytest.raises(ValueError, match="status and provisional"):
        tooling.validate_notation(table)



@pytest.mark.parametrize("point", ["U+02B9", "U+02D0", "U+1E034", "U+2010"])
def test_frozen_table_cannot_omit_a_symbol_class(point, table):
    table["symbols"] = [s for s in table["symbols"] if s["codepoint"] != point]
    with pytest.raises(ValueError, match="Frozen symbol inventory"):
        tooling.validate_notation(table)


@pytest.mark.parametrize("point", ["U+A675", "U+1E034"])
def test_table_rejects_missing_or_wrong_derived_letters(point, table):
    symbol = next(s for s in table["symbols"] if s["codepoint"] == point)
    symbol["letter"] = "а"
    with pytest.raises(ValueError, match="letter mapping"):
        tooling.validate_notation(table)
    del symbol["letter"]
    with pytest.raises(ValueError, match="letter mapping"):
        tooling.validate_notation(table)


def test_table_rejects_relabelled_raised_letter(table):
    symbol = next(s for s in table["symbols"] if s["role"] == "raised_de")
    symbol["role"] = "ordinary_de"
    with pytest.raises(ValueError, match="Raised letter mapping"):
        tooling.validate_notation(table)


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
        {"combining_mark_order": []},
        {"combining_mark_order": ["U+0301"]},
        {"precomposed_letters": "é"},
        {"provisional": True},
        {"status": "provisional"},
        {"minimum_unicode_version": "14.0.0"},
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
    db = tmp_path / "copy.db"
    conn = open_schema_copy(db)
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
    assert ingest.ingest_adjudicated(conn, data, frozen, census_counts={"10": 2}) == (2, 0)
    assert ingest.ingest_adjudicated(conn, data, frozen, census_counts={"10": 2}) == (0, 2)
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
    provisional = copy.deepcopy(table)
    provisional.update(status="provisional", provisional=True)
    with pytest.raises(ValueError, match="provisional"):
        ingest.ingest_adjudicated(conn, packet(row()), provisional, census_counts={"10": 1})
    data = packet(row())
    data["paragraph_counts"]["10"] = 2
    with pytest.raises(ValueError, match="Incomplete"):
        ingest.ingest_adjudicated(conn, data, frozen, census_counts={"10": 2})
    assert conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before


@pytest.mark.parametrize("change", [{"status": "agreed"}, {"adjudicated_by": ""}, {"text": "[i]"}])
def test_ingest_requires_valid_adjudication(schema_copy, frozen, change):
    _, conn = schema_copy
    r = row()
    r.update(change)
    with pytest.raises(ValueError):
        ingest.ingest_adjudicated(conn, packet(r), frozen, census_counts={"10": 1})
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


def test_conflicting_ingest_rolls_back_earlier_insert(schema_copy, frozen):
    _, conn = schema_copy
    ingest.ingest_adjudicated(conn, packet(row(page=11)), frozen, census_counts={"11": 1})
    conn.commit()
    with pytest.raises(ValueError, match="Conflicting"):
        ingest.ingest_adjudicated(conn, packet(row(), row("[ў]", page=11)), frozen, census_counts={"10": 1, "11": 1})
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
        ingest.ingest_adjudicated(conn, packet(row()), frozen, census_counts={"10": 1})
    assert "transcription_status" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


def test_render_300dpi_hash_and_ignore_guard(tmp_path, monkeypatch):
    pdf = tmp_path / "fixture.pdf"
    with pymupdf.open() as doc:
        doc.new_page(width=72, height=72)
        doc.save(pdf)
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    # A disposable Git repository exercises the real ignore guard without residue.
    import subprocess

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    (tmp_path / ".gitignore").write_text(".cache/\n")
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".cache"
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
        tooling.render_pages(pdf, tmp_path.parent, expected_sha256=digest, expected_pages=1)


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
    census = tmp_path / "census.json"
    census.write_text(json.dumps({"10": 1}))
    args = ["--adjudicated", str(data), "--notation", str(notation), "--db", str(db), "--census", str(census)]
    assert ingest.main([*args, "--dry-run"]) == 0
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2
    assert ingest.main([*args, "--apply"]) == 0
    assert "inserted=1, skipped=0" in capsys.readouterr().out
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3
    with pytest.raises(SystemExit):
        ingest.main([*args, "--apply", "--force"])
    assert ingest.main(["--adjudicated", str(data), "--db", str(db), "--census", str(census), "--dry-run"]) == 0


def test_ingest_transaction_is_owned_by_caller(schema_copy, frozen):
    _, conn = schema_copy
    assert not conn.in_transaction
    ingest.ingest_adjudicated(conn, packet(row()), frozen, census_counts={"10": 1})
    assert conn.in_transaction
    conn.rollback()
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2
    assert "transcription_status" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}


def test_ingest_requires_retained_ocr_page(schema_copy, frozen):
    _, conn = schema_copy
    with pytest.raises(ValueError, match="retained OCR"):
        ingest.ingest_adjudicated(conn, packet(row(page=12)), frozen, census_counts={"12": 1})
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
        ingest.validate_adjudicated_packet(data, frozen, census_counts={"10": 1})


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
    census = tmp_path / "census.json"
    census.write_text(json.dumps({"10": 1}))
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--adjudicated", str(data), "--notation", str(notation), "--db", str(missing), "--census", str(census), "--apply"])
    assert exc.value.code == 1
    assert not missing.exists()


@pytest.mark.parametrize("marks", ["\u2df7\u0301", "\ua675\u1abb\u0301", "\ua677\u1abc\u0300"])
def test_equal_class_order_is_pinned_and_diff_normalizes(marks, table):
    canonical = tooling.normalize_transcription(f"[е{marks}]", table)
    reversed_text = unicodedata.normalize("NFC", f"[е{marks[::-1]}]")
    tooling.validate_text(canonical, table)
    with pytest.raises(ValueError, match="combining mark order"):
        tooling.validate_text(reversed_text, table)
    assert tooling.diff_transcriptions([row(canonical)], [row(reversed_text)], table)["disagreement_count"] == 0
    assert tooling.normalize_transcription(canonical, table) == canonical


@pytest.mark.parametrize("base, composed", [("к", "ќ"), ("К", "Ќ"), ("г", "ѓ"), ("Г", "Ѓ")])
def test_listed_nfc_precomposed_accent_letters(base, composed, table):
    with pytest.raises(ValueError, match="NFC"):
        tooling.validate_text(f"[{base}\u0301]", table)
    assert tooling.normalize_transcription(f"[{base}\u0301]", table) == f"[{composed}]"
    assert tooling.validate_text(f"[{composed}]", table)[0]["text"] == f"[{composed}]"
    assert tooling.diff_transcriptions([row(f"[{base}\u0301]")], [row(f"[{composed}]")], table)["disagreement_count"] == 0


def test_diff_remaps_underlining_after_composition(table):
    a, b = row("[к\u0301]"), row("[ќ]")
    a["underlining"] = [{"start": 1, "end": 3}]
    b["underlining"] = [{"start": 1, "end": 2}]
    before = copy.deepcopy(a)
    assert tooling.diff_transcriptions([a], [b], table)["disagreement_count"] == 0
    assert a == before
    a["underlining"] = [{"start": 1, "end": 2}]
    with pytest.raises(ValueError, match="splits"):
        tooling.diff_transcriptions([a], [b], table)


@pytest.mark.parametrize("census", [{}, {"10": 2}, {"10": True}, None])
def test_ingest_refuses_independent_census_mismatch(schema_copy, frozen, census):
    _, conn = schema_copy
    before = conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall()
    with pytest.raises(ValueError, match="independent census"):
        ingest.ingest_adjudicated(conn, packet(row()), frozen, census_counts=census)
    assert conn.execute("SELECT sql FROM sqlite_master ORDER BY name").fetchall() == before
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 2


def test_shorter_packet_supersedes_all_previous_page_rows(schema_copy, frozen):
    _, conn = schema_copy
    ingest.ingest_adjudicated(conn, packet(row(), row("[ў]", paragraph=2)), frozen, census_counts={"10": 2})
    conn.commit()
    before = conn.execute("SELECT id,text FROM textbooks ORDER BY id").fetchall()
    # A separate corrected image census permits the shorter packet.
    assert ingest.ingest_adjudicated(conn, packet(row()), frozen, census_counts={"10": 1}) == (0, 1)
    assert conn.execute("SELECT id,text FROM textbooks ORDER BY id").fetchall() == before
    assert conn.execute("SELECT paragraph_number FROM textbooks WHERE transcription_status='adjudicated'").fetchall() == [(1,)]
    assert conn.execute("SELECT section_number FROM textbook_sections WHERE transcription_status='adjudicated'").fetchall() == [("10.1",)]
    assert conn.execute("SELECT count(*) FROM textbooks WHERE transcription_status='superseded'").fetchone()[0] == 2
    assert conn.execute("SELECT transcription_status FROM textbooks WHERE chunk_id=?", (f"{ingest.SOURCE_FILE}_p11",)).fetchone()[0] is None


def test_default_retrieval_excludes_retained_rows_and_explicit_request_includes_them(schema_copy, frozen, monkeypatch):
    from wiki import sources_db

    _, conn = schema_copy
    text = "fixture " * 50 + "[а́]"
    conn.execute("UPDATE textbooks SET text=? WHERE chunk_id=?", (text, f"{ingest.SOURCE_FILE}_p10"))
    # The live schema's trigger indexes new rows. Rebuild only this fixture's
    # index after the synthetic OCR update (the live DDL has no update trigger).
    conn.execute("INSERT INTO textbooks_fts(textbooks_fts) VALUES ('rebuild')")
    ingest.ingest_adjudicated(conn, packet(row(text)), frozen, census_counts={"10": 1})
    conn.row_factory = sqlite3.Row
    monkeypatch.setattr(sources_db, "_get_conn", lambda: conn)
    assert [r["transcription_status"] for r in sources_db.search_textbooks({"fixture"})] == ["adjudicated"]
    assert {r["transcription_status"] for r in sources_db.search_textbooks({"fixture"}, include_superseded=True)} == {"adjudicated", "superseded"}
    results = sources_db._search_sections_fts5([], {"fixture"}, track="a1", max_chunk_candidates=1)
    assert len(results) == 1 and "adjudicated" in results[0]["section_title"]
    assert len(sources_db._search_sections_fts5([], {"fixture"}, track="a1", include_superseded=True)) == 2


def test_write_cli_requires_explicit_db_and_apply(tmp_path):
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--apply"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--db", str(tmp_path / "copy.db")])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        ingest.main(["--db", str(tmp_path / "copy.db"), "--apply", "--dry-run"])
    assert exc.value.code == 2


def test_dry_run_requires_existing_ocr_and_does_not_migrate(schema_copy, frozen, tmp_path):
    db, conn = schema_copy
    data, notation, census = (tmp_path / name for name in ("rows.json", "table.json", "census.json"))
    notation.write_text(json.dumps(frozen))
    args = ["--adjudicated", str(data), "--notation", str(notation), "--db", str(db), "--census", str(census), "--dry-run"]
    before = db.read_bytes()
    data.write_text(json.dumps(packet(row())))
    census.write_text(json.dumps({"10": 1}))
    assert ingest.main(args) == 0
    assert db.read_bytes() == before
    data.write_text(json.dumps(packet(row(page=12))))
    census.write_text(json.dumps({"12": 1}))
    with pytest.raises(SystemExit) as exc:
        ingest.main(args)
    assert exc.value.code == 1
    assert db.read_bytes() == before
    assert "transcription_status" not in {r[1] for r in conn.execute("PRAGMA table_info(textbooks)")}


def test_legacy_cli_also_requires_apply_and_existing_db(schema_copy, tmp_path, monkeypatch):
    db, conn = schema_copy
    monkeypatch.setattr(ingest, "REFERENCES_DIR", tmp_path)
    (tmp_path / ingest.TXT_FILENAME).write_text("\ffixture OCR", encoding="utf-8")
    before = db.read_bytes()
    assert ingest.main(["--db", str(db), "--dry-run"]) == 0
    assert db.read_bytes() == before
    assert ingest.main(["--db", str(db), "--apply"]) == 0
    assert conn.execute("SELECT count(*) FROM textbooks").fetchone()[0] == 3
    missing = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        ingest.main(["--db", str(missing), "--apply"])
    assert not missing.exists()


def test_legacy_cli_reports_missing_input(schema_copy, tmp_path, monkeypatch):
    db, _ = schema_copy
    monkeypatch.setattr(ingest, "REFERENCES_DIR", tmp_path)
    assert ingest.main(["--db", str(db), "--dry-run"]) == 2
