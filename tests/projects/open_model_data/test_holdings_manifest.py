"""Per-component holdings manifest (#9609, plan PA2): coverage, provenance and hashing."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

from scripts.ingest.sum20_quarantine_unverified import EXPECTED_ROWS
from scripts.projects.open_model_data import holdings_manifest as hm

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTER = REPO_ROOT / "docs" / "sources" / "permissions-register.yaml"

# Every source the plan's P2 roles and component table name (the issue's denominator).
PLAN_SOURCES = {
    "ua_gec_gec_only_train",  # C1 human corrections
    "ua_gec_gec_fluency_train",  # C6 F/Calque
    "ua_gec_test_ruler",  # ruler
    "vesum_forms_all",  # forms
    "ulif_paradigm_sections",  # forms
    "ulif_forms",  # stress
    "pravopys_2019_paragraphs",  # spelling
    "pohribnyi_1992_ocr_pages",  # literary pronunciation
    "ulif_synonym_sections",
    "ulif_antonym_sections",
    "ulif_phraseology_sections",
    "frazeolohichnyi",
    "sum20_live_articles",  # meaning
    "vts_entries",  # meaning, checking only
    "esum_etymology",  # etymology
    "antonenko_book_chunks",  # calques
    "sum11_contrast",  # Russification evidence
    "textbook_sections",  # C9
    "zno_keyed_tasks",  # ruler
}


def _manifest() -> dict:
    return yaml.safe_load(hm.DEFAULT_OUTPUT.read_text(encoding="utf-8"))


def test_manifest_lists_every_holding_the_code_defines():
    assert [holding["id"] for holding in _manifest()["holdings"]] == [holding.id for holding in hm.HOLDINGS]


def test_manifest_covers_every_component_and_the_rulers():
    manifest = _manifest()
    covered = {component for holding in manifest["holdings"] for component in holding["components"]}
    covered |= {item["components"] for item in manifest["not_yet_built"]}
    assert set(hm.COMPONENTS) <= covered


def test_manifest_covers_every_planned_source():
    assert {holding["id"] for holding in _manifest()["holdings"]} >= PLAN_SOURCES


def test_every_holding_has_a_count_a_hash_and_provenance():
    for holding in _manifest()["holdings"]:
        measured = ("rows", "rows_sha256") if holding["store"] != "ua-gec" else ("files", "files_sha256")
        assert all(holding.get(key) not in (None, "") for key in measured), holding["id"]
        assert len(holding[measured[1]]) == 64, holding["id"]
        assert holding["origin"].strip() and holding["edition"].strip(), holding["id"]


def test_register_ids_resolve_to_applied_rows():
    registered = {row["id"] for row in yaml.safe_load(REGISTER.read_text(encoding="utf-8"))["sources"]}
    assert {h["register_id"] for h in _manifest()["holdings"]} <= registered


def test_quarantined_sum20_count_matches_the_quarantine_script():
    holdings = {holding["id"]: holding for holding in _manifest()["holdings"]}
    assert holdings["sum20_quarantined_articles"]["rows"] == len(EXPECTED_ROWS)
    assert holdings["sum20_live_articles"]["rows"] + len(EXPECTED_ROWS) == 100


def test_manifest_holds_no_source_text_or_host_paths():
    text = hm.DEFAULT_OUTPUT.read_text(encoding="utf-8")
    assert "/home/" not in text and "/Users/" not in text


def _fixture_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, word TEXT, n INTEGER)")
    conn.executemany("INSERT INTO t VALUES (?, ?, ?)", [(2, "два", 2), (1, "один", None)])
    conn.commit()
    return conn


def test_row_hash_is_deterministic_and_sensitive_to_any_change(tmp_path):
    conn = _fixture_db(tmp_path / "a.db")
    first = hm.measure_rows(conn, "SELECT * FROM t ORDER BY id")
    assert first["rows"] == 2 and first["columns"] == ["id", "word", "n"]
    assert hm.measure_rows(conn, "SELECT * FROM t ORDER BY id") == first
    expected = hm._row_digest([(1, "один", None), (2, "два", 2)])[1]
    assert first["rows_sha256"] == expected
    conn.execute("UPDATE t SET word = 'три' WHERE id = 2")
    assert hm.measure_rows(conn, "SELECT * FROM t ORDER BY id")["rows_sha256"] != first["rows_sha256"]


def test_file_measure_counts_documents_and_calque_edits(tmp_path):
    annotated = tmp_path / "data" / "gec-fluency" / "train" / "annotated"
    annotated.mkdir(parents=True)
    (annotated / "0001.a1.ann").write_text("{даний=>цей:::error_type=F/Calque} {а=>б:::error_type=G/Case}", "utf-8")
    (annotated / "0001.a2.ann").write_text("{даний=>цей:::error_type=F/Calque}", "utf-8")
    (annotated / "0002.a1.ann").write_text("text", "utf-8")
    measured = hm.measure_files(tmp_path, "data/gec-fluency/train/annotated/*.ann")
    assert (measured["files"], measured["documents"], measured["f_calque_edits"]) == (3, 2, 2)
    (annotated / "0002.a1.ann").write_text("changed", "utf-8")
    assert (
        hm.measure_files(tmp_path, "data/gec-fluency/train/annotated/*.ann")["files_sha256"] != measured["files_sha256"]
    )


def test_drift_reports_changed_missing_and_new_holdings():
    committed = {"holdings": [{"id": "a", "rows": 1, "rows_sha256": "x"}, {"id": "gone", "rows": 1}]}
    fresh = {"holdings": [{"id": "a", "rows": 2, "rows_sha256": "x"}, {"id": "new", "rows": 1}]}
    problems = hm.drift(committed, fresh)
    assert "a: rows 1 -> 2" in problems
    assert "new: not in the committed manifest" in problems
    assert "gone: missing from the fresh manifest" in problems
    assert hm.drift(committed, committed) == []


def test_generator_cli_writes_counts_and_hashes_then_detects_drift(tmp_path, monkeypatch, capsys):
    database = tmp_path / "synthetic ї # ?.db"
    conn = _fixture_db(database)
    conn.close()
    clone = tmp_path / "clone"
    clone.mkdir()
    (clone / "a.ann").write_text("synthetic annotation", encoding="utf-8")
    monkeypatch.setattr(
        hm,
        "HOLDINGS",
        (
            hm.Holding(
                "synthetic_rows", ("C1",), "fixture", "sources.db", "SELECT * FROM t ORDER BY id", "fixture", "fixture"
            ),
            hm.Holding("synthetic_files", ("rulers",), "fixture", "ua-gec", "*.ann", "fixture", "fixture"),
        ),
    )
    output = tmp_path / "manifest.yaml"
    args = [
        "--sources-db",
        str(database),
        "--vesum-db",
        str(database),
        "--ua-gec",
        str(clone),
        "--measured-at",
        "2026-01-01T00:00:00Z",
        "--output",
        str(output),
    ]
    before = database.read_bytes()
    assert hm.main(args) == 0
    assert database.read_bytes() == before
    manifest = yaml.safe_load(output.read_text())
    assert manifest["holdings"][0]["rows"] == 2
    assert manifest["holdings"][1]["files"] == 1
    assert hm.main([*args, "--check"]) == 0
    (clone / "a.ann").write_text("changed annotation", encoding="utf-8")
    assert hm.main([*args, "--check"]) == 1
    assert "files_sha256" in capsys.readouterr().err
