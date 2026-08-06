"""Fast hermetic tests for the text-free Phase 3 source-universe freezer."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import phase3_source_universe as freezer

SOURCE_TABLES = tuple(freezer.SOURCES_FAMILIES.values())
FREEZE_SCHEMA = freezer.ROOT / "data/projects/open_model_data/contracts/phase3_source_universe_freeze_v1.schema.json"


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _contract() -> dict[str, object]:
    families = []
    family_ids = set(freezer.SOURCES_FAMILIES) | {
        "antonenko_textbook_representation", "lexical_vesum", "calque_inventory", "lexical_r2u",
        "pravopys_2019_complete", "pravopys_2026_complete", "other_normative_style_inventory",
    }
    for family_id in sorted(family_ids):
        count = 1
        if family_id == "other_normative_style_inventory":
            count = 0
        if family_id in {"calque_inventory", "lexical_r2u", "pravopys_2019_complete", "pravopys_2026_complete"}:
            count = 5 if family_id.startswith("pravopys") else 3
        families.append({
            "family_id": family_id,
            "coverage_mode": "lexical_structural_and_used_subset" if family_id.startswith("lexical_") else "source_conversion",
            "input_identity": {"observed_input_total": count, "unit_grain": "fixture"},
            "rights": {"source_text_committed": False, "locator_only_allowed": True, "rights_limited_disposition": "rights_limited_locator_only"},
        })
    return {"mandatory_families": families}


def _sources_db(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        for table in SOURCE_TABLES:
            if table == "style_guide":
                connection.execute('CREATE TABLE "style_guide" (id INTEGER PRIMARY KEY, source TEXT, text TEXT)')
                connection.execute("INSERT INTO style_guide VALUES (1, ?, ?)", ("Антоненко", "secret source sentence"))
            elif table == "textbooks":
                connection.execute('CREATE TABLE "textbooks" (id INTEGER PRIMARY KEY, source_file TEXT, text TEXT)')
                connection.execute(
                    "INSERT INTO textbooks VALUES (1, ?, ?)",
                    ("antonenko-davydovych-yak-my-hovorymo", "secret source sentence"),
                )
            else:
                connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY, payload TEXT)')
                connection.execute(f'INSERT INTO "{table}" VALUES (1, ?)', ("secret source sentence",))


def _vesum_db(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, tags TEXT, pos TEXT)")
        connection.execute("INSERT INTO forms VALUES ('secret', 'secret', 'x', 'x')")


def _inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    sources, vesum = tmp_path / "sources.db", tmp_path / "vesum.db"
    _sources_db(sources)
    _vesum_db(vesum)
    contract, cache, module = tmp_path / "contract.json", tmp_path / "r2u.json", tmp_path / "calque.py"
    _json(contract, _contract())
    entries = [{"query": "one"}, {"query": "two"}, {"query": "three"}]
    _json(cache, {"cache_id": "fixture", "entries": entries, "entries_sha256": freezer._unit_hash(entries)})
    module.write_text("CURATED_CALQUES={'a': {'x': 1}}\nPHRASAL_CALQUES={'b': {'x': 2}}\nSENSE_RESTRICTED_CALQUES={'c': {'x': 3}}\n", encoding="utf-8")
    pdf2019, pdf2026 = tmp_path / "2019.pdf", tmp_path / "2026.pdf"
    pdf2019.write_bytes(b"fixture 2019")
    pdf2026.write_bytes(b"fixture 2026")
    monkeypatch.setattr(freezer, "EXPECTED_2019_SHA256", freezer.sha256_file(pdf2019))
    monkeypatch.setattr(freezer, "EXPECTED_2026_SHA256", freezer.sha256_file(pdf2026).upper())
    monkeypatch.setattr(freezer, "EXPECTED_PARAGRAPH_COUNT", 2)
    monkeypatch.setattr(freezer, "extract_pdf_pages", lambda path, tool: ["РОЗДІЛ I\n§ 1. heading\n1. unit", "§ 2. heading\nа) unit"])
    monkeypatch.setattr(
        freezer,
        "_verify_merged_main_binding",
        lambda sha: {
            "implementation_version": freezer.FREEZER_IMPLEMENTATION_VERSION,
            "script_path": freezer.FREEZER_SCRIPT_PATH,
            "script_sha256": "b" * 64,
        },
    )
    return {
        "coverage_contract": contract, "sources_db": sources, "vesum_db": vesum,
        "pravopys_2019_pdf": pdf2019, "pravopys_2026_pdf": pdf2026,
        "pravopys_2019_retrieved_at": "2026-08-05T22:07:34Z",
        "pravopys_2019_retrieval_locator": "https://web.archive.org/fixture-2019",
        "pravopys_2026_retrieved_at": "2026-08-05T22:05:39Z",
        "pravopys_2026_retrieval_locator": "https://data.commoncrawl.org/fixture-2026",
        "calque_module": module, "r2u_cache": cache, "pdftotext": tmp_path / "unused",
        "merged_main_sha": "a" * 40,
    }


def _freeze(inputs: dict[str, object], output_dir: Path) -> dict[str, object]:
    return freezer.freeze(**inputs, output_dir=output_dir)


def test_freeze_writes_all_21_text_free_ledgers_deterministically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    first, second = tmp_path / "first", tmp_path / "second"
    receipt = _freeze(inputs, first)
    _freeze(inputs, second)
    assert len(receipt["families"]) == 21
    assert {path.name for path in first.iterdir()} == freezer.EXPECTED_OUTPUT_FILES
    assert sorted(path.name for path in first.iterdir()) == sorted(path.name for path in second.iterdir())
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()
        assert b"secret source sentence" not in path.read_bytes()
    unit = json.loads((first / "ua_gec.units.jsonl").read_text(encoding="utf-8"))
    assert set(unit) >= {"unit_id", "unit_sha256", "locator", "duplicate_group_id", "parse_status", "rights", "provenance"}
    structural = json.loads((first / "lexical_structural_freeze_v1.json").read_text(encoding="utf-8"))
    assert [item["family_id"] for item in structural["families"]] == sorted(
        item["family_id"] for item in receipt["families"] if item["family_id"].startswith("lexical_")
    )
    assert all(item["binding_fields"] == ["unit_id", "unit_sha256", "duplicate_group_id", "parse_status", "provenance"] for item in structural["families"])
    assert not (first / "lexical_balla_en_uk.structural.json").exists()
    assert receipt["other_normative_style_inventory"] == {"candidate_tables": [], "additional_family_count": 0, "zero_additional_family_inventory": True}
    assert receipt["pdf_editions"]["pravopys_2019_complete"] == {
        "edition_identity": "pravopys_2019_complete", "input_sha256": freezer.EXPECTED_2019_SHA256,
        "official_download_locator": freezer.PRAVOPYS_2019_OFFICIAL_DOWNLOAD_LOCATOR,
        "page_count_extracted": 2, "paragraph_count": 2,
        "retrieval_locator": "https://web.archive.org/fixture-2019",
        "retrieved_at": "2026-08-05T22:07:34Z",
        "rights_provenance_classification": "rights_limited_locator_only",
        "source_text_committed": False, "stable_grain": "pdf_numbered_hierarchy",
    }
    assert receipt["pdf_editions"]["pravopys_2026_complete"]["official_decision_locator"] == freezer.PRAVOPYS_2026_DECISION_LOCATOR
    assert receipt["pdf_editions"]["pravopys_2026_complete"]["official_download_locator"] == freezer.PRAVOPYS_2026_OFFICIAL_DOWNLOAD_LOCATOR
    Draft202012Validator(json.loads(FREEZE_SCHEMA.read_text(encoding="utf-8"))).validate(receipt)
    manifest = receipt["artifact_manifest"]
    assert manifest["artifact_count"] == 10
    assert manifest["payload_file_count"] == 9
    assert {item["path"] for item in manifest["payloads"]} == freezer.PAYLOAD_FILES
    assert manifest["payload_manifest_sha256"] == freezer._unit_hash(manifest["payloads"])
    for item in manifest["payloads"]:
        payload = first / item["path"]
        assert item["sha256"] == freezer.sha256_file(payload)
        assert item["byte_count"] == payload.stat().st_size


def test_count_mismatch_fails_before_output_publication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    contract = json.loads(inputs["coverage_contract"].read_text(encoding="utf-8"))
    next(item for item in contract["mandatory_families"] if item["family_id"] == "lexical_balla_en_uk")["input_identity"]["observed_input_total"] = 2
    _json(inputs["coverage_contract"], contract)
    output = tmp_path / "out"
    with pytest.raises(freezer.FreezeError, match="frozen unit count mismatch"):
        _freeze(inputs, output)
    assert not output.exists() or not list(output.iterdir())


def test_stale_output_file_fails_before_freeze(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    output = tmp_path / "out"
    output.mkdir()
    (output / "stale.json").write_text("{}", encoding="utf-8")
    with pytest.raises(freezer.FreezeError, match="stale or unexpected"):
        _freeze(inputs, output)


def test_merged_main_binding_fails_on_noncanonical_sha() -> None:
    with pytest.raises(freezer.FreezeError, match="40 lowercase hex"):
        freezer._verify_merged_main_binding("A" * 40)


def test_merged_main_binding_requires_current_remote_head(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        freezer.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=("b" * 40 + "\n").encode()),
    )
    with pytest.raises(freezer.FreezeError, match="not the current origin/main"):
        freezer._verify_merged_main_binding("a" * 40)


def test_merged_main_binding_requires_identical_freezer_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = iter(
        [
            SimpleNamespace(returncode=0, stdout=("a" * 40 + "\n").encode()),
            SimpleNamespace(returncode=0, stdout=b"different freezer"),
        ]
    )
    monkeypatch.setattr(freezer.subprocess, "run", lambda *args, **kwargs: next(calls))
    with pytest.raises(freezer.FreezeError, match="running freezer bytes differ"):
        freezer._verify_merged_main_binding("a" * 40)


def test_receipt_schema_rejects_artifact_manifest_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _freeze(_inputs(tmp_path, monkeypatch), tmp_path / "out")
    receipt["artifact_manifest"]["artifact_count"] = 9
    validator = Draft202012Validator(json.loads(FREEZE_SCHEMA.read_text(encoding="utf-8")))
    with pytest.raises(ValidationError):
        validator.validate(receipt)


def test_receipt_schema_rejects_wrong_family_receipt_shape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    receipt = _freeze(_inputs(tmp_path, monkeypatch), tmp_path / "out")
    lexical = next(item for item in receipt["families"] if item["family_id"] == "lexical_balla_en_uk")
    lexical.clear()
    lexical.update({
        "family_id": "lexical_balla_en_uk",
        "unit_count": 1,
        "ledger_sha256": "a" * 64,
        "ledger_file": "lexical_balla_en_uk.units.jsonl",
    })
    validator = Draft202012Validator(json.loads(FREEZE_SCHEMA.read_text(encoding="utf-8")))
    with pytest.raises(ValidationError):
        validator.validate(receipt)


def test_pdf_hash_mismatch_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(freezer, "EXPECTED_2026_SHA256", "0" * 64)
    with pytest.raises(freezer.FreezeError, match="official pravopys_2026_complete PDF hash mismatch"):
        _freeze(inputs, tmp_path / "out")


def test_retrieval_provenance_fails_closed_before_publication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    inputs["pravopys_2026_retrieved_at"] = "2026-08-05"
    output = tmp_path / "out"
    with pytest.raises(freezer.FreezeError, match="retrieval time must be canonical UTC"):
        _freeze(inputs, output)
    assert not output.exists() or not list(output.iterdir())


def test_database_drift_fails_against_frozen_count(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    _freeze(inputs, tmp_path / "first")
    with sqlite3.connect(inputs["sources_db"]) as connection:
        connection.execute("INSERT INTO balla_en_uk VALUES (2, 'drift')")
    with pytest.raises(freezer.FreezeError, match="lexical_balla_en_uk"):
        _freeze(inputs, tmp_path / "second")


def test_other_normative_inventory_enumerates_discovered_additions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    contract = json.loads(inputs["coverage_contract"].read_text(encoding="utf-8"))
    next(item for item in contract["mandatory_families"] if item["family_id"] == "other_normative_style_inventory")["input_identity"]["observed_input_total"] = 1
    _json(inputs["coverage_contract"], contract)
    with sqlite3.connect(inputs["sources_db"]) as connection:
        connection.execute("CREATE TABLE normative_guide (id INTEGER PRIMARY KEY, text TEXT)")
        connection.execute("INSERT INTO normative_guide VALUES (1, 'secret source sentence')")
    receipt = _freeze(inputs, tmp_path / "out")
    assert receipt["other_normative_style_inventory"]["zero_additional_family_inventory"] is False
    assert receipt["other_normative_style_inventory"]["additional_family_count"] == 1


def test_dynamic_text_primary_key_is_hash_only_in_ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    contract = json.loads(inputs["coverage_contract"].read_text(encoding="utf-8"))
    next(item for item in contract["mandatory_families"] if item["family_id"] == "other_normative_style_inventory")["input_identity"]["observed_input_total"] = 1
    _json(inputs["coverage_contract"], contract)
    with sqlite3.connect(inputs["sources_db"]) as connection:
        connection.execute("CREATE TABLE normative_text_key (rule TEXT PRIMARY KEY, payload TEXT)")
        connection.execute("INSERT INTO normative_text_key VALUES (?, ?)", ("source-bearing-key", "secret source sentence"))
    output = tmp_path / "out"
    _freeze(inputs, output)
    ledger = (output / "other_normative_style_inventory.units.jsonl").read_text(encoding="utf-8")
    unit = json.loads(ledger)
    assert "source-bearing-key" not in ledger
    assert unit["locator"] == {
        "kind": "sqlite_row",
        "primary_key_fields": ["rule"],
        "primary_key_sha256": freezer._unit_hash({"rule": "source-bearing-key"}),
        "table": "normative_text_key",
    }


def test_pdf_hierarchy_filters_toc_and_binds_nested_unique_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(
        freezer,
        "extract_pdf_pages",
        lambda path, tool: ["§ 1. contents…..18\nРОЗДІЛ I\n§ 1. heading\n1. part\n1) point\nа) subpoint\n4.2.4. decimal\n§ 2. heading"],
    )
    family = next(
        item for item in _contract()["mandatory_families"] if item["family_id"] == "pravopys_2026_complete"
    )
    units, report = freezer._pdf_units(inputs["pravopys_2026_pdf"], "pravopys_2026_complete", family, inputs["pdftotext"])
    paths = [tuple(unit["locator"]["section_path"]) for unit in units]
    assert report["paragraph_count"] == 2
    assert len(paths) == len(set(paths))
    assert ("chapter:i", "paragraph:1", "part:1", "point:1", "subpoint:а") in paths
    assert ("chapter:i", "decimal:4", "decimal:4.2", "decimal:4.2.4") in paths
    assert ("chapter:i", "decimal:4", "decimal:4.2", "decimal:4.2.4", "paragraph:2") in paths


def test_pdf_ellipsis_title_is_not_treated_as_a_contents_leader(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(freezer, "EXPECTED_PARAGRAPH_COUNT", 162)
    body = "\n".join(["РОЗДІЛ I", *(f"§ {number}. heading" for number in range(1, 162)), "§ 162. title (...)"])
    monkeypatch.setattr(freezer, "extract_pdf_pages", lambda path, tool: [body])
    family = next(
        item for item in _contract()["mandatory_families"] if item["family_id"] == "pravopys_2019_complete"
    )
    units, report = freezer._pdf_units(inputs["pravopys_2019_pdf"], "pravopys_2019_complete", family, inputs["pdftotext"])
    assert report["paragraph_count"] == 162
    assert any(unit["locator"]["section_path"][-1] == "paragraph:162" for unit in units)


def test_pdf_leaderless_navigation_duplicate_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(freezer, "EXPECTED_PARAGRAPH_COUNT", 3)
    monkeypatch.setattr(
        freezer,
        "extract_pdf_pages",
        lambda path, tool: ["§ 1. contents\n§ 2. contents\nРОЗДІЛ I\n§ 1. body\n§ 2. body"],
    )
    family = next(
        item for item in _contract()["mandatory_families"] if item["family_id"] == "pravopys_2026_complete"
    )
    with pytest.raises(freezer.FreezeError, match="possible unfiltered navigation capture"):
        freezer._pdf_units(inputs["pravopys_2026_pdf"], "pravopys_2026_complete", family, inputs["pdftotext"])


def test_pdf_trailing_navigation_is_excluded_after_complete_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)
    monkeypatch.setattr(freezer, "EXPECTED_PARAGRAPH_COUNT", 168)
    body = "\n".join(["РОЗДІЛ I", *(f"§ {number}. body" for number in range(1, 169))])
    monkeypatch.setattr(
        freezer,
        "extract_pdf_pages",
        lambda path, tool: [f"{body}\n§ 1. contents ........ 4\n§ 2. contents"],
    )
    family = next(
        item for item in _contract()["mandatory_families"] if item["family_id"] == "pravopys_2019_complete"
    )
    units, report = freezer._pdf_units(
        inputs["pravopys_2019_pdf"], "pravopys_2019_complete", family, inputs["pdftotext"]
    )
    assert report["paragraph_count"] == 168
    assert units[-1]["unit_sha256"] == freezer.sha256_bytes("§ 168. body".encode())
    assert units[-1]["locator"]["end_line"] == 169


def test_second_database_open_failure_closes_first_connection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _inputs(tmp_path, monkeypatch)

    class SourceConnection:
        closed = False

        def close(self) -> None:
            self.closed = True

    source = SourceConnection()

    def connect(path: Path) -> SourceConnection:
        if path == inputs["sources_db"]:
            return source
        raise freezer.FreezeError("synthetic VESUM open failure")

    monkeypatch.setattr(freezer, "_connect", connect)
    with pytest.raises(freezer.FreezeError, match="synthetic VESUM open failure"):
        _freeze(inputs, tmp_path / "out")
    assert source.closed is True
