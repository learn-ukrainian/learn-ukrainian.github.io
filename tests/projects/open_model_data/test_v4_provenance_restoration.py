"""V4 provenance restoration (#7883 PROV-1..PROV-4) is evidence-bound and fail-closed."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import source_work_locator_index as locators
from scripts.projects.open_model_data import v4_provenance_restoration as restoration

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "data/projects/open_model_data/evidence"
PROVENANCE = ROOT / "data/projects/open_model_data/provenance"
CONTRACT = ROOT / "data/projects/open_model_data/contracts/v4_provenance_restoration_v1.schema.json"
CONFIG = PROVENANCE / "v4_provenance_restoration_config_v1.json"
LOCATOR_CONFIG = EVIDENCE / "source_work_locator_config_v1.json"
INDEX = PROVENANCE / "v4_provenance_restoration_index_v1.jsonl"
UNRESOLVED = PROVENANCE / "v4_provenance_restoration_unresolved_v1.json"
RECEIPT = PROVENANCE / "v4_provenance_restoration_receipt_v1.json"


def _database(root: Path) -> Path:
    database = root / "data" / "sources.db"
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE literary_texts (source_file TEXT, work_id TEXT, source_url TEXT, title TEXT, author TEXT, year INTEGER, genre TEXT, language_period TEXT, text TEXT)"
        )
        connection.executemany(
            "INSERT INTO literary_texts (source_file, work_id, source_url, title, author, year, genre, language_period, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("lit-a", "work-a", "https://example.test/a.pdf#page=1", "Title A", "Author A", 1900, "poetry", "modern", "LITERARY SECRET"),
                ("lit-a", "work-a", "https://example.test/a.pdf#page=2", "Title A", "Author A", 1900, "poetry", "modern", "LITERARY SECRET"),
                ("lit-b", "work-b", None, "Title B", "Author B", 1700, "chronicle", "middle_ukrainian", "LITERARY SECRET"),
            ],
        )
        connection.execute(
            "CREATE TABLE textbooks (source_file TEXT, title TEXT, author TEXT, author_uk TEXT, grade TEXT, subject TEXT, text TEXT)"
        )
        connection.executemany(
            "INSERT INTO textbooks (source_file, title, author, author_uk, grade, subject, text) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("tb-lang", "Підручник", "author", "Автор", "5", "ukrmova", "TEXTBOOK SECRET"),
                ("tb-stem", "Algebra", "author", "Автор", "8", "algebra", "TEXTBOOK SECRET"),
                ("tb-lost", "Istoriya", "author", "Автор", "3", "istoriya", "TEXTBOOK SECRET"),
                ("anna-ohoiko-500-verbs", "Private", "author", "Автор", "1", "ukrmova", "PRIVATE SECRET"),
            ],
        )
        connection.execute(
            "CREATE TABLE external_articles (source_file TEXT, url_normalized TEXT, url TEXT, title TEXT, speaker TEXT, domain TEXT, publish_date TEXT, channel_id TEXT, text TEXT)"
        )
        connection.execute(
            "INSERT INTO external_articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("ext", "https://example.test/a", "https://example.test/a", "Article", "Speaker", "example.test", "2026-01-01", "channel", "EXTERNAL SECRET"),
        )
        connection.execute("CREATE TABLE wikipedia (fetched_at TEXT, title TEXT, url TEXT, text TEXT)")
        connection.execute(
            "INSERT INTO wikipedia VALUES (?, ?, ?, ?)",
            ("2026-01-01T00:00:00Z", "Page", "https://uk.wikipedia.org/wiki/Page", "WIKI SECRET"),
        )
    return database


def _ledger(root: Path, *, ocr_status: str = "not_ingested", textbook_diff: dict | None = None) -> None:
    inventory = root / "data/projects/open_model_data/inventory"
    inventory.mkdir(parents=True, exist_ok=True)
    records = [
        {"asset_id": "drive.literary_raw_reconciliation", "details": {"database_only": [], "raw_only": []}},
        {
            "asset_id": "drive.textbook_raw_reconciliation",
            "details": textbook_diff
            if textbook_diff is not None
            else {"raw_only": [], "database_only_or_raw_chunk_unresolved": ["tb-lost"]},
        },
        {"asset_id": "drive.deferred_textbook_scans", "lineage": {"ingestion_status": ocr_status}},
        {"asset_id": "drive.orphan_ocr", "lineage": {"ingestion_status": ocr_status}},
    ]
    (inventory / "recovery_ledger_v1.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )


def _snapshot(root: Path) -> None:
    evidence = root / "data/projects/open_model_data/evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    locators.build(
        config_path=LOCATOR_CONFIG,
        input_root=root,
        output=evidence / "source_work_locator_index_v1.compact.jsonl",
    )


def _environment(tmp_path: Path) -> Path:
    root = tmp_path / "env"
    _database(root)
    _snapshot(root)
    _ledger(root)
    return root


def _build(root: Path) -> dict:
    return restoration.build(config_path=CONFIG, input_root=root, output_root=root)


def _index_rows(root: Path) -> tuple[dict, list[dict]]:
    lines = (root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl").read_text(
        encoding="utf-8"
    ).splitlines()
    return json.loads(lines[0]), [json.loads(line) for line in lines[1:]]


def _artifact(root: Path, name: str) -> dict:
    return json.loads((root / f"data/projects/open_model_data/provenance/{name}").read_text(encoding="utf-8"))


def test_committed_config_validates_against_contract() -> None:
    schema = json.loads(CONTRACT.read_text())
    validator = Draft202012Validator({"$ref": "#/$defs/config", "$defs": schema["$defs"]})
    assert not list(validator.iter_errors(json.loads(CONFIG.read_text())))


def test_committed_artifacts_are_schema_valid_and_snapshot_bound() -> None:
    """PROV-4 on committed evidence: structure, hashes, binding; full verify runs in build tests."""
    schema = json.loads(CONTRACT.read_text())
    lines = INDEX.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    header_validator = Draft202012Validator({"$ref": "#/$defs/indexHeader", "$defs": schema["$defs"]})
    assert not list(header_validator.iter_errors(header))
    snapshot_header = json.loads(
        (EVIDENCE / "source_work_locator_index_v1.compact.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert header["snapshot"]["semantic_jsonl_sha256"] == snapshot_header["semantic_jsonl_sha256"]
    assert header["records"] == len(lines) - 1
    rows_bytes = "".join(line + "\n" for line in lines[1:]).encode("utf-8")
    assert hashlib.sha256(rows_bytes).hexdigest() == header["rows_sha256"]
    record_validator = Draft202012Validator(schema)
    for position in sorted({1, len(lines) // 2, len(lines) - 1}):
        assert not list(record_validator.iter_errors(json.loads(lines[position])))
    report = json.loads(UNRESOLVED.read_text())
    report_validator = Draft202012Validator({"$ref": "#/$defs/unresolvedReport", "$defs": schema["$defs"]})
    assert not list(report_validator.iter_errors(report))
    assert report["index_sha256"] == hashlib.sha256(INDEX.read_bytes()).hexdigest()
    assert report["human_source_approvals_reopened"] is False
    receipt = json.loads(RECEIPT.read_text())
    receipt_validator = Draft202012Validator({"$ref": "#/$defs/receipt", "$defs": schema["$defs"]})
    assert not list(receipt_validator.iter_errors(receipt))
    assert receipt["outputs"]["index"]["sha256"] == report["index_sha256"]
    assert receipt["outputs"]["unresolved_report"]["sha256"] == hashlib.sha256(UNRESOLVED.read_bytes()).hexdigest()
    assert receipt["outputs"]["index"]["records"] == header["records"]
    assert receipt["human_source_approvals_reopened"] is False


def test_build_restores_links_binds_identities_and_classifies(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    result = _build(root)
    header, rows = _index_rows(root)
    assert result["records"] == 4 == header["records"] == len(rows)
    assert header["snapshot"]["records"] == 7
    by_id = {row["restoration_id"]: row for row in rows}
    assert len(by_id) == 4
    literary = next(row for row in rows if row["work_locator"].get("work_id") == "work-a")
    assert literary["source_id"].startswith("source.literary.")
    assert literary["work_id"].startswith("work.literary.")
    assert literary["links"]["canonical_url"] == "https://example.test/a.pdf"
    assert literary["links"]["acquisition_ref"] == "gdrive:learn-ukrainian-data/literary_texts/lit-a.jsonl"
    assert literary["links"]["edition"] == {"author": "Author A", "title": "Title A", "year": "1900"}
    assert literary["classification"]["period"]["value"] == "modern"
    assert literary["classification"]["period"]["status"] == "restored"
    assert literary["classification"]["domain"]["value"] == "poetry"
    assert literary["unresolved"] == ["original_language", "register", "translation_status"]
    chronicle = next(row for row in rows if row["work_locator"].get("work_id") == "work-b")
    assert chronicle["links"]["canonical_url"] is None
    assert chronicle["classification"]["period"]["value"] == "middle_ukrainian"
    assert "canonical_source_url" in chronicle["unresolved"]
    textbook = next(row for row in rows if row["source_locator"]["source_file"] == "tb-lang")
    assert textbook["links"]["acquisition_ref"] == "gdrive:learn-ukrainian-data/textbook_chunks#tb-lang"
    assert textbook["classification"]["domain"] == {
        "value": "ukrmova",
        "status": "restored",
        "source_ref": "snapshot:source_work_locator_index_v1#metadata.subject",
    }
    lost = next(row for row in rows if row["source_locator"]["source_file"] == "tb-lost")
    assert lost["links"]["acquisition_ref"] is None
    assert "acquisition_raw_locator" in lost["unresolved"]


def test_build_excludes_stem_private_caption_and_non_view_families(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    _header, rows = _index_rows(root)
    sources = {row["source_locator"]["source_file"] for row in rows}
    assert sources == {"lit-a", "lit-b", "tb-lang", "tb-lost"}
    receipt = _artifact(root, "v4_provenance_restoration_receipt_v1.json")
    exclusions = {(entry["basis"], entry["scope"]): entry for entry in receipt["selection"]["exclusions"]}
    stem = exclusions[("stem_operator_exclusion_2026-09-10", "public_textbooks")]
    assert stem["rows"] == 1 and stem["subjects"] == {"algebra": 1}
    assert exclusions[("video_captions_and_transcripts_excluded_by_operator_decision_2026-09-10", "external_articles")]["rows"] == 1
    assert exclusions[("not_a_selected_consumer_view_for_the_first_eligible_cohort", "wikipedia")]["rows"] == 1
    private = exclusions[("private_teaching_material_operator_exclusion_2026-09-10", "db.textbooks.private")]
    assert len(private["sources"]) == 8
    ocr = exclusions[("ocr_derived_text_operator_exclusion_2026-09-10", "un-ingested retained OCR candidates")]
    assert ocr["inventory_asset_ids"] == ["drive.deferred_textbook_scans", "drive.orphan_ocr"]
    assert receipt["human_source_approvals_reopened"] is False


def test_unresolved_report_is_separate_and_reopens_no_approvals(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    report = _artifact(root, "v4_provenance_restoration_unresolved_v1.json")
    assert report["human_source_approvals_reopened"] is False
    assert report["by_cohort"]["literary-non-ocr"]["records"] == 2
    assert report["by_cohort"]["literary-non-ocr"]["unresolved_keys"]["canonical_source_url"] == 1
    assert report["by_cohort"]["public-textbooks-non-stem-non-ocr"]["unresolved_keys"]["acquisition_raw_locator"] == 1
    receipt = _artifact(root, "v4_provenance_restoration_receipt_v1.json")
    assert report["index_sha256"] == receipt["outputs"]["index"]["sha256"]


def test_verify_passes_on_fresh_build(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    built = _build(root)
    verified = restoration.verify(config_path=CONFIG, input_root=root, output_root=root)
    assert verified["records"] == built["records"] == 4
    assert verified["index_sha256"] == built["index_sha256"]


def test_build_is_byte_deterministic(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    first = _build(root)
    paths = [
        root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl",
        root / "data/projects/open_model_data/provenance/v4_provenance_restoration_unresolved_v1.json",
        root / "data/projects/open_model_data/provenance/v4_provenance_restoration_receipt_v1.json",
    ]
    before = [path.read_bytes() for path in paths]
    second = _build(root)
    assert first == second
    assert [path.read_bytes() for path in paths] == before


def test_no_corpus_text_leaks_into_artifacts(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    provenance = root / "data/projects/open_model_data/provenance"
    for name in (
        "v4_provenance_restoration_index_v1.jsonl",
        "v4_provenance_restoration_unresolved_v1.json",
        "v4_provenance_restoration_receipt_v1.json",
    ):
        content = (provenance / name).read_text(encoding="utf-8")
        assert "SECRET" not in content


def test_tampered_snapshot_fails_closed(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    snapshot = root / "data/projects/open_model_data/evidence/source_work_locator_index_v1.compact.jsonl"
    lines = snapshot.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    header["semantic_jsonl_sha256"] = "0" * 64
    snapshot.write_text("\n".join([locators.canonical_json(header), *lines[1:]]) + "\n", encoding="utf-8")
    with pytest.raises(locators.LocatorError):
        _build(root)


def test_missing_classification_column_fails_closed(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute("ALTER TABLE literary_texts RENAME COLUMN genre TO genre_old")
    with pytest.raises(restoration.RestorationError, match="missing classification columns"):
        _build(root)


def test_conflicting_period_within_work_fails_closed(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute(
            "INSERT INTO literary_texts (source_file, work_id, source_url, title, author, year, genre, language_period, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("lit-b", "work-b", None, "Title B", "Author B", 1700, "chronicle", "modern", "CONFLICT"),
        )
    with pytest.raises(restoration.RestorationError, match="conflicting period"):
        _build(root)


def test_snapshot_database_group_drift_fails_closed(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute(
            "INSERT INTO literary_texts (source_file, work_id, source_url, title, author, year, genre, language_period, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("lit-new", "work-new", None, "New", "Author", 2000, "prose", "modern", "DRIFT"),
        )
    with pytest.raises(restoration.RestorationError, match="group drift"):
        _build(root)


def test_out_of_vocabulary_classification_fails_closed(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    with sqlite3.connect(root / "data" / "sources.db") as connection:
        connection.execute("UPDATE literary_texts SET genre = 'unconfigured-genre'")
    with pytest.raises(restoration.RestorationError, match="outside the configured vocabulary"):
        _build(root)


def test_ingested_ocr_evidence_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "env"
    _database(root)
    _snapshot(root)
    _ledger(root, ocr_status="ingested")
    with pytest.raises(restoration.RestorationError, match="OCR exclusion evidence"):
        _build(root)


def test_nonempty_reconciliation_diff_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "env"
    _database(root)
    _snapshot(root)
    _ledger(root, textbook_diff={"raw_only": ["surprise-raw"], "database_only_or_raw_chunk_unresolved": []})
    with pytest.raises(restoration.RestorationError, match=r"non-empty or non-list raw_only diff"):
        _build(root)


def test_private_source_in_snapshot_fails_closed(tmp_path: Path) -> None:
    rows = [
        {
            "source_family": "public_textbooks",
            "source_locator": {"source_file": "ulp-1-00-lesson-notes"},
        }
    ]
    config = json.loads(CONFIG.read_text())
    with pytest.raises(restoration.RestorationError, match="private teaching sources"):
        restoration._check_private_sources_absent(config, rows)


def test_unknown_config_key_fails_schema(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    config = json.loads(CONFIG.read_text())
    config["unexpected"] = True
    mutated = tmp_path / "config.json"
    mutated.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(restoration.RestorationError, match="schema failure"):
        restoration.build(config_path=mutated, input_root=root, output_root=root)


def test_verify_detects_tampered_index_and_reordered_rows(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[-1])
    tampered["links"]["canonical_url"] = "https://attacker.example/forge"
    lines[-1] = restoration.canonical_json(tampered)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(restoration.RestorationError, match="rows hash disagrees"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)

    root = _environment(tmp_path / "reordered")
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    header, rows = lines[0], [json.loads(line) for line in lines[1:]]
    rows.reverse()
    reordered_rows = "".join(restoration.canonical_json(row) + "\n" for row in rows)
    header_value = json.loads(header)
    header_value["rows_sha256"] = hashlib.sha256(reordered_rows.encode("utf-8")).hexdigest()
    index.write_text(restoration.canonical_json(header_value) + "\n" + reordered_rows, encoding="utf-8")
    with pytest.raises(restoration.RestorationError, match="reordered"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_atomic_publication_failure_preserves_prior_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    before = index.read_bytes()

    def fail(_source: Path, _target: Path) -> None:
        raise OSError("planned publication failure")

    monkeypatch.setattr(restoration, "_replace", fail)
    with pytest.raises(OSError, match="planned publication failure"):
        _build(root)
    assert index.read_bytes() == before
    assert not list(index.parent.glob(".*.tmp"))


def _reseal_tampered_artifacts(root: Path) -> None:
    """Helper to coherently reseal hashes across index header, unresolved report, and receipt."""
    provenance = root / "data/projects/open_model_data/provenance"
    index_path = provenance / "v4_provenance_restoration_index_v1.jsonl"
    report_path = provenance / "v4_provenance_restoration_unresolved_v1.json"
    receipt_path = provenance / "v4_provenance_restoration_receipt_v1.json"

    lines = index_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    rows = [json.loads(line) for line in lines[1:]]
    rows_bytes = "".join(restoration.canonical_json(r) + "\n" for r in rows).encode("utf-8")
    header["records"] = len(rows)
    header["rows_sha256"] = hashlib.sha256(rows_bytes).hexdigest()
    index_content = (restoration.canonical_json(header) + "\n").encode("utf-8") + rows_bytes
    index_path.write_bytes(index_content)
    index_sha256 = hashlib.sha256(index_content).hexdigest()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["index_sha256"] = index_sha256
    recomputed = restoration._build_unresolved_report(
        rows, index_sha256=index_sha256, config_sha256=report["config_sha256"], snapshot=header["snapshot"]
    )
    report["by_cohort"] = recomputed["by_cohort"]
    report_content = (restoration.canonical_json(report) + "\n").encode("utf-8")
    report_path.write_bytes(report_content)
    report_sha256 = hashlib.sha256(report_content).hexdigest()

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["outputs"]["index"]["sha256"] = index_sha256
    receipt["outputs"]["index"]["records"] = len(rows)
    receipt["outputs"]["unresolved_report"]["sha256"] = report_sha256
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_verify_rejects_fabricated_edition_metadata(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["links"]["edition"]["title"] = "Fabricated Edition Title"
    lines[1] = restoration.canonical_json(row)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="edition metadata diverges"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_fabricated_acquisition_ref(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["links"]["acquisition_ref"] = "gdrive:learn-ukrainian-data/literary_texts/forged.jsonl"
    lines[1] = restoration.canonical_json(row)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="acquisition_ref diverges"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_fabricated_textbook_domain(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    # tb-lang is row index 3
    found = False
    for i in range(1, len(lines)):
        row = json.loads(lines[i])
        if row["cohort_id"] == "public-textbooks-non-stem-non-ocr" and row["classification"]["domain"]["status"] == "restored":
            current_val = row["classification"]["domain"]["value"]
            row["classification"]["domain"]["value"] = "ekonomika" if current_val != "ekonomika" else "pravoznavstvo"
            lines[i] = restoration.canonical_json(row)
            found = True
            break
    assert found
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="invalid restored metadata classification"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_fabricated_column_classification(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    # lit-a poetry
    found = False
    for i in range(1, len(lines)):
        row = json.loads(lines[i])
        if row["cohort_id"] == "literary-non-ocr" and row["classification"]["domain"]["status"] == "restored":
            row["classification"]["domain"]["value"] = "chronicle"
            lines[i] = restoration.canonical_json(row)
            found = True
            break
    assert found
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="invalid restored column classification"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_inconsistent_unresolved_status(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["unresolved"] = []
    lines[1] = restoration.canonical_json(row)
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="unresolved keys diverge"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_partial_selection(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    # Drop first 2 rows
    lines = [lines[0], lines[1], lines[2]]
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match=r"disagrees with expected selection|does not match complete eligible selection"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_duplicate_locator(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    # Duplicate row 1 in place of row 2 so total count matches expected selection
    lines[2] = lines[1]
    index.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="duplicate locator_id"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_divergent_receipt_selection_or_exclusions(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    receipt_path = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_receipt_v1.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["selection"]["cohorts"][0]["selected_rows"] = 999
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    with pytest.raises(restoration.RestorationError, match="receipt cohort accounting disagrees"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_acquisition_plan_rejects_missing_or_invalid_reconciliation_details() -> None:
    cohort = {
        "cohort_id": "c",
        "acquisition": {
            "inventory_asset_id": "asset-1",
            "ref_template": "ref:{source_stem}",
            "require_empty_diffs": ["diff_a"],
        },
    }
    # Missing record
    with pytest.raises(restoration.RestorationError, match="missing inventory reconciliation record"):
        restoration._acquisition_plan(cohort, {})

    # Missing details
    with pytest.raises(restoration.RestorationError, match="missing or non-dict details object"):
        restoration._acquisition_plan(cohort, {"asset-1": {"asset_id": "asset-1"}})

    # Non-dict details
    with pytest.raises(restoration.RestorationError, match="missing or non-dict details object"):
        restoration._acquisition_plan(cohort, {"asset-1": {"asset_id": "asset-1", "details": None}})

    # Missing diff key
    with pytest.raises(restoration.RestorationError, match="missing required diff key: diff_a"):
        restoration._acquisition_plan(cohort, {"asset-1": {"asset_id": "asset-1", "details": {}}})

    # Non-empty diff
    with pytest.raises(restoration.RestorationError, match="has a non-empty or non-list diff_a diff"):
        restoration._acquisition_plan(cohort, {"asset-1": {"asset_id": "asset-1", "details": {"diff_a": ["bad"]}}})

    # Non-list diff
    with pytest.raises(restoration.RestorationError, match="has a non-empty or non-list diff_a diff"):
        restoration._acquisition_plan(cohort, {"asset-1": {"asset_id": "asset-1", "details": {"diff_a": None}}})

    # Unresolved detail key checks
    cohort_with_unresolved = {
        "cohort_id": "c2",
        "acquisition": {
            "inventory_asset_id": "asset-2",
            "ref_template": "ref:{source_stem}",
            "require_empty_diffs": ["diff_a"],
            "unresolved_detail_key": "unresolved_list",
        },
    }
    # Missing unresolved key
    with pytest.raises(restoration.RestorationError, match="missing unresolved detail key"):
        restoration._acquisition_plan(cohort_with_unresolved, {"asset-2": {"asset_id": "asset-2", "details": {"diff_a": []}}})

    # Non-list unresolved key
    with pytest.raises(restoration.RestorationError, match="is not a list"):
        restoration._acquisition_plan(cohort_with_unresolved, {"asset-2": {"asset_id": "asset-2", "details": {"diff_a": [], "unresolved_list": "bad"}}})


def test_verify_rejects_reassigned_cohort(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    header_line = lines[0]
    records = [json.loads(line) for line in lines[1:]]
    # Reassign a literary row to the textbooks cohort
    target_row = next(r for r in records if r["cohort_id"] == "literary-non-ocr")
    target_row["cohort_id"] = "public-textbooks-non-stem-non-ocr"
    ordered = sorted(
        records,
        key=lambda r: (r["cohort_id"], r["source_id"], r["work_id"], r["locator_id"]),
    )
    new_lines = [header_line] + [restoration.canonical_json(r) for r in ordered]
    index.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="diverges from reconstructed cohort"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_duplicate_restoration_id(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines[1:]]
    # Copy restoration_id from record 0 onto record 1
    records[1]["restoration_id"] = records[0]["restoration_id"]
    new_lines = [lines[0]] + [restoration.canonical_json(r) for r in records]
    index.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match="duplicate restoration_id"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)


def test_verify_rejects_fabricated_restoration_id(tmp_path: Path) -> None:
    root = _environment(tmp_path)
    _build(root)
    index = root / "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl"
    lines = index.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines[1:]]
    # Fabricate schema-conforming restoration_id on record 0
    records[0]["restoration_id"] = "restore." + "0" * 24
    new_lines = [lines[0]] + [restoration.canonical_json(r) for r in records]
    index.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    _reseal_tampered_artifacts(root)
    with pytest.raises(restoration.RestorationError, match=r"diverges from expected"):
        restoration.verify(config_path=CONFIG, input_root=root, output_root=root)
