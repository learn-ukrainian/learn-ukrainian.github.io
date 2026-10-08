"""Tests for V4 source custody access resolution and verification (#7884).

Validates ACCESS-1 through ACCESS-4 under epic #7423.
"""

from __future__ import annotations

import atexit
import copy
import json
import os
import re
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_source_custody_access as custody
from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR
from scripts.storage.topology import ENV_BULK_ROOT, REQUIRED_BULK_MARKERS
from tests._host_path_guard import FIXTURE_HOME, FIXTURE_USER, checkout_path_hits, host_path_hits

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_CUSTODY_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "custody"
CONFIG_PATH = REGISTRY_CUSTODY_DIR / "v4_source_custody_access_config_v1.json"
CONFIG_SCHEMA = Path("registry/projects/open_model_data/contracts/v4_source_custody_access_config_v1.schema.json")
ITEM_SCHEMA = Path("registry/projects/open_model_data/contracts/v4_source_custody_access_item_v1.schema.json")
MISSING_SCHEMA = Path("registry/projects/open_model_data/contracts/v4_source_custody_missing_report_v1.schema.json")
RECEIPT_SCHEMA = Path("registry/projects/open_model_data/contracts/v4_source_custody_access_receipt_v1.schema.json")
SYNTHETIC_PROVENANCE = Path(__file__).parent / "fixtures/v4_source_custody_provenance.jsonl"


_SYNTHETIC_CUSTODY_DIR: Path | None = None


def _get_synthetic_custody_dir() -> Path:
    global _SYNTHETIC_CUSTODY_DIR
    if _SYNTHETIC_CUSTODY_DIR is None:
        base = Path(tempfile.mkdtemp(prefix="v4-synthetic-custody-"))
        atexit.register(shutil.rmtree, base, ignore_errors=True)

        in_root = base / "in"
        prov_dir = in_root / "data/projects/open_model_data/provenance"
        prov_dir.mkdir(parents=True)
        shutil.copyfile(SYNTHETIC_PROVENANCE, prov_dir / "v4_provenance_restoration_index_v1.jsonl")
        (prov_dir / "v4_provenance_restoration_receipt_v1.json").write_bytes(
            (REGISTRY_OPEN_MODEL_DATA_DIR / "provenance/v4_provenance_restoration_receipt_v1.json").read_bytes()
        )

        out_root = base / "out"
        custody.build(CONFIG_PATH, input_root=in_root, output_root=out_root)
        _SYNTHETIC_CUSTODY_DIR = base
    return _SYNTHETIC_CUSTODY_DIR


class SyntheticCustodyBundle:
    def __init__(self, in_dir: Path, out_dir: Path):
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.custody_dir = out_dir / "data/projects/open_model_data/custody"
        self.index_path = self.custody_dir / "v4_source_custody_access_index_v1.jsonl"
        self.missing_path = self.custody_dir / "v4_source_custody_missing_report_v1.json"
        self.receipt_path = self.custody_dir / "v4_source_custody_access_receipt_v1.json"

    def read_index(self) -> tuple[str, list[dict[str, Any]]]:
        lines = self.index_path.read_text(encoding="utf-8").splitlines()
        return lines[0], [json.loads(line) for line in lines[1:]]

    def write_index(self, header: str, records: list[dict[str, Any]]) -> None:
        lines = [header] + [json.dumps(r) for r in records]
        self.index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def read_receipt(self) -> dict[str, Any]:
        return json.loads(self.receipt_path.read_text(encoding="utf-8"))

    def write_receipt(self, receipt: dict[str, Any]) -> None:
        self.receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    def read_missing(self) -> dict[str, Any]:
        return json.loads(self.missing_path.read_text(encoding="utf-8"))

    def write_missing(self, missing: dict[str, Any]) -> None:
        self.missing_path.write_text(json.dumps(missing), encoding="utf-8")

    def rehash_receipt(self, receipt: dict[str, Any] | None = None) -> dict[str, Any]:
        if receipt is None:
            receipt = self.read_receipt()
        receipt["index_sha256"] = custody.sha256_file(self.index_path)
        receipt["missing_report_sha256"] = custody.sha256_file(self.missing_path)
        receipt["receipt_id"] = custody._make_receipt_id(
            receipt["config_sha256"], receipt["index_sha256"], receipt["missing_report_sha256"]
        )
        self.write_receipt(receipt)
        return receipt

    def verify(self, config_path: Path = CONFIG_PATH, *, require_database: bool = False) -> bool:
        return custody.verify(
            config_path, input_root=self.in_dir, output_root=self.out_dir, require_database=require_database
        )


@pytest.fixture
def synthetic_bundle(
    tmp_path: Path, requires_sources_db: Path, requires_textbook_chunks: Path
) -> SyntheticCustodyBundle:
    base = _get_synthetic_custody_dir()
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    shutil.copytree(base / "in", in_dir)
    shutil.copytree(base / "out", out_dir)
    return SyntheticCustodyBundle(in_dir, out_dir)


@pytest.fixture
def repo_root() -> Path:
    return Path.cwd()


def test_contracts_are_valid_schemas() -> None:
    for schema_path in (CONFIG_SCHEMA, ITEM_SCHEMA, MISSING_SCHEMA, RECEIPT_SCHEMA):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_config_passes_schema() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    schema = json.loads(CONFIG_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(config))
    assert not errors, f"Config schema errors: {errors}"


def test_schema_cache_reloads_changed_content_at_same_path(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    first = {"type": "object", "required": ["first"]}
    second = {"type": "object", "required": ["second"]}
    schema_path.write_text(json.dumps(first), encoding="utf-8")
    validator = custody._load_schema(schema_path, [tmp_path])
    assert not list(validator.iter_errors({"first": 1}))

    schema_path.write_text(json.dumps(second), encoding="utf-8")
    updated = custody._load_schema(schema_path, [tmp_path])
    assert updated is not validator
    assert list(updated.iter_errors({"first": 1}))
    assert not list(updated.iter_errors({"second": 1}))


def test_schema_cache_preserves_utf8_bom_rejection(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    schema_path.write_bytes(b'\xef\xbb\xbf{"type": "object"}')
    with pytest.raises(json.JSONDecodeError):
        custody._load_schema(schema_path, [tmp_path])


@pytest.fixture
def requires_textbook_chunks(requires_sources_db: Path) -> Path:
    candidate = Path("data/textbook_chunks")
    if candidate.is_dir():
        return candidate
    candidate = requires_sources_db.parent / "textbook_chunks"
    if candidate.is_dir():
        return candidate
    pytest.skip("requires data/textbook_chunks corpus directory (not provisioned in CI)")


def test_verify_passes_on_committed_artifacts(
    tmp_path: Path,
    requires_sources_db: Path,
    requires_textbook_chunks: Path,
) -> None:
    hydrated_root = requires_sources_db.parent.parent
    output_root = tmp_path / "out"
    custody_dir = output_root / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)
    shutil.copyfile(
        hydrated_root / "data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl",
        custody_dir / "v4_source_custody_access_index_v1.jsonl",
    )
    for filename in ("v4_source_custody_missing_report_v1.json", "v4_source_custody_access_receipt_v1.json"):
        shutil.copyfile(REGISTRY_CUSTODY_DIR / filename, custody_dir / filename)
    assert custody.verify(CONFIG_PATH, input_root=hydrated_root, output_root=output_root, require_database=True) is True


def test_open_model_data_scripts_have_no_baked_run_root_default() -> None:
    production_paths = (
        Path("scripts/projects/open_model_data/v4_source_custody_access.py"),
        Path("scripts/projects/open_model_data/v4_language_usage_separation.py"),
        Path("scripts/projects/open_model_data/v4_native_extraction_validation.py"),
        Path("scripts/projects/open_model_data/validate_source_records.py"),
        Path("scripts/projects/open_model_data/model_view_exporter.py"),
        Path("docs/projects/open-model-data/SOURCE_RECORD_CONTRACT.md"),
        Path("scripts/config/fleet_repos.yaml"),
    )
    for path in production_paths:
        text = path.read_text(encoding="utf-8")
        assert not checkout_path_hits(text), f"{path} still bakes a host run-root"
        assert not re.search(r"/home/<", text), f"{path} still documents a host path template"


def test_watch_desk_narrative_docs_have_no_baked_host_run_root() -> None:
    # Narrative operator docs must not bake a host checkout path. Detector
    # needles in tests and OPSEC scanners stay in those suites.
    narrative_docs = (
        Path("docs/audits/2026-09-11-uldr-program-audit.md"),
        Path("docs/dispatch-briefs/2026-09-12-cu-p0-pilot-repair-brief.md"),
        Path("docs/dispatch-briefs/2026-09-12-cu-p0-pilot-writer-brief.md"),
        Path("docs/projects/open-model-data/PHASE_3_5_COT_CLAIM_VERIFIER.md"),
        Path("docs/projects/open-model-data/PHASE_3_6_PILOT_CANARY.md"),
        Path("docs/runbooks/cursor-driver.md"),
        Path("docs/runbooks/background-session-tasks.md"),
        Path("docs/runbooks/word-atlas-source-inventory-review-candidates.md"),
        Path("docs/runbooks/codex-hooks.md"),
        Path("docs/projects/ua-open-weight-eval/HF_JOBS_BASELINE.md"),
    )
    for path in narrative_docs:
        text = path.read_text(encoding="utf-8")
        assert not host_path_hits(text), f"{path} still documents a host run-root or checkout path"


def test_primary_repo_root_uses_env_when_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(custody.PRIMARY_REPO_ROOT_ENV, str(tmp_path))
    assert custody._primary_repo_root() == tmp_path.resolve()


def test_primary_repo_root_resolves_cwd_relative_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    extra = tmp_path / "extra-root"
    extra.mkdir()
    monkeypatch.setenv(custody.PRIMARY_REPO_ROOT_ENV, "extra-root")
    assert custody._primary_repo_root() == extra.resolve()


def test_primary_repo_root_fails_closed_on_invalid_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(custody.PRIMARY_REPO_ROOT_ENV, str(tmp_path / "missing"))
    with pytest.raises(custody.CustodyAccessError, match=custody.PRIMARY_REPO_ROOT_ENV):
        custody._primary_repo_root()


def test_primary_repo_root_returns_none_when_cwd_has_no_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(custody.PRIMARY_REPO_ROOT_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    assert custody._primary_repo_root() is None


def test_first_eligible_cohort_100_percent_accessible() -> None:
    receipt_path = REGISTRY_CUSTODY_DIR / "v4_source_custody_access_receipt_v1.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    first_cohort = receipt["summary"]["first_eligible_cohort"]

    assert first_cohort["cohort_id"] == "literary-non-ocr"
    assert first_cohort["total_sources"] == 229
    assert first_cohort["accessible_sources"] == 229
    assert first_cohort["confirmed_native"] == 229
    assert first_cohort["coverage_ratio"] == 1.0
    assert first_cohort["permitted_to_proceed"] is True
    assert receipt["safety_assertions"]["first_eligible_cohort_ready"] is True
    assert receipt["verdict"] == "PROCEED_WITH_ACCESSIBLE_SOURCES"


def test_missing_report_records_unmounted_archive_and_owner() -> None:
    missing_path = REGISTRY_CUSTODY_DIR / "v4_source_custody_missing_report_v1.json"
    report = json.loads(missing_path.read_text(encoding="utf-8"))

    assert report["schema_version"] == "v4_source_custody_missing_report_v1"
    assert report["owner"] == "existing custody/source-access owner"
    assert report["operator_decision_date"] == "2026-09-10"
    assert report["issue"] == 7884
    assert len(report["missing_inputs"]) > 0

    for item in report["missing_inputs"]:
        assert item["owner"] == "existing custody/source-access owner"
        assert item["cohort_id"] == "public-textbooks-non-stem-non-ocr"
        assert any(term in item["reason"] for term in ("unmounted", "does_not_match", "not_found", "missing"))
        assert "direct PDF byte extraction" in item["blocks"]

    proceed = report["accessible_eligible_sources_permitted_to_proceed"]
    assert proceed["permitted"] is True
    assert "literary-non-ocr" in proceed["permitted_cohort_ids"]


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl",
)
def test_index_records_pass_schema_and_have_no_corpus_text() -> None:
    index_path = Path("data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl")
    schema = json.loads(ITEM_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    with index_path.open(encoding="utf-8") as f:
        header = json.loads(f.readline())
        assert header["schema_version"] == "v4_source_custody_access_index_v1"
        assert header["records"] == 351

        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            errors = list(validator.iter_errors(row))
            assert not errors, f"Row error: {errors}"
            # Ensure no corpus text leaked
            assert "text" not in row
            assert "content" not in row
            assert "raw" not in row


def test_check_chunk_file_lineage_native(tmp_path: Path) -> None:
    chunk_file = tmp_path / "native_sample.jsonl"
    rows = [
        {
            "chunk_id": "c1",
            "extraction_mode": "native_text",
            "page_extraction_mode": "native_text",
            "text": "Привіт світ.",
        },
        {
            "chunk_id": "c2",
            "extraction_mode": "native_pdf_text",
            "page_extraction_mode": "native_pdf_text",
            "text": "Українська мова.",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, chars, digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "mixed_native"
    assert is_ocr is False
    assert count == 2
    assert chars > 0
    assert digest is not None


def test_check_chunk_file_lineage_pure_native_text(tmp_path: Path) -> None:
    chunk_file = tmp_path / "native_text_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "native_text"
    assert is_ocr is False
    assert count == 1
    assert digest is not None


def test_check_chunk_file_lineage_ocr_excluded(tmp_path: Path) -> None:
    chunk_file = tmp_path / "ocr_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "page_extraction_mode": "native_text", "text": "Привіт."},
        {
            "chunk_id": "c2",
            "extraction_mode": "apple_vision_ocr",
            "page_extraction_mode": "apple_vision_ocr",
            "text": "Скан.",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "apple_vision_ocr"
    assert is_ocr is True
    assert count == 2


def test_check_chunk_file_lineage_unknown_fails_closed(tmp_path: Path) -> None:
    chunk_file = tmp_path / "unknown_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "some_heuristic_extract", "text": "Привіт."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, _count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "unknown"
    assert is_ocr is False


def test_check_chunk_file_lineage_unlabelled_mixed_row_fails_closed(tmp_path: Path) -> None:
    """Finding 1: Unlabelled/absent extraction mode mixed with native row must fail closed as unknown."""
    chunk_file = tmp_path / "mixed_unlabelled.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "native_text", "page_extraction_mode": "native_text", "text": "Привіт."},
        {"chunk_id": "c2", "text": "Unlabelled row."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "unknown"
    assert is_ocr is False
    assert count == 2


def test_bounded_custody_reader_mock_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "test_sources.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    cur.executemany(
        "INSERT INTO literary_texts (chunk_id, source_file, text) VALUES (?, ?, ?);",
        [
            ("c1", "sample_source", "CONFIDENTIAL CORPUS TEXT 1"),
            ("c2", "sample_source", "CONFIDENTIAL CORPUS TEXT 2"),
            ("c3", "other_source", "OTHER TEXT"),
        ],
    )
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_path)
    result = reader.read_source_stream("literary_texts", "sample_source", batch_size=2)

    assert result["source_file"] == "sample_source"
    assert result["table"] == "literary_texts"
    assert result["records_streamed"] == 2
    assert result["chars_streamed"] == len("CONFIDENTIAL CORPUS TEXT 1") + len("CONFIDENTIAL CORPUS TEXT 2")
    assert result["stream_sha256"] is not None
    # Verify stream hash does NOT disclose text directly
    assert "CONFIDENTIAL" not in str(result)


def test_stream_digest_sensitive_to_same_length_text_replacement(tmp_path: Path) -> None:
    """Finding 2A: Stream digest must change if text content is altered even with identical character count."""
    db1_path = tmp_path / "db1.db"
    conn1 = sqlite3.connect(db1_path)
    conn1.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn1.execute("INSERT INTO literary_texts (chunk_id, source_file, text) VALUES ('c1', 'src', 'TEXT_AAAAA');")
    conn1.commit()
    conn1.close()

    db2_path = tmp_path / "db2.db"
    conn2 = sqlite3.connect(db2_path)
    conn2.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    # Same length (10 chars), different content
    conn2.execute("INSERT INTO literary_texts (chunk_id, source_file, text) VALUES ('c1', 'src', 'TEXT_BBBBB');")
    conn2.commit()
    conn2.close()

    reader1 = custody.BoundedCustodyReader(db1_path)
    reader2 = custody.BoundedCustodyReader(db2_path)

    res1 = reader1.read_source_stream("literary_texts", "src")
    res2 = reader2.read_source_stream("literary_texts", "src")

    assert res1["chars_streamed"] == res2["chars_streamed"]
    assert res1["stream_sha256"] != res2["stream_sha256"]


def test_discrepant_database_chunks_fail_closed(tmp_path: Path) -> None:
    """Finding 2B: Database rows with different chunk IDs or text from native chunk file must fail closed."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn.execute("INSERT INTO textbooks (chunk_id, source_file, text) VALUES ('db_chunk_X', 'tb_test', 'DB text');")
    conn.commit()

    chunk_file = tmp_path / "tb_test.jsonl"
    chunk_rows = [
        {
            "chunk_id": "chk_chunk_Y",
            "extraction_mode": "native_pdf_text",
            "page_extraction_mode": "native_pdf_text",
            "text": "CHK text",
        },
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in chunk_rows) + "\n", encoding="utf-8")

    chunks_map = {"tb_test": chunk_file}
    cohort_cfg = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_family": "public_textbooks",
        "resolver_kind": "hybrid_sqlite_chunks_archive",
        "lineage_rule": "native_pdf_text",
        "archive_locator": "gdrive:test/tb_test.pdf",
        "excluded_modes": ["apple_vision_ocr", "ocr"],
    }

    record, missing = custody.resolve_source_access(
        source_id="source.public_textbooks.1234567890abcdef12345678",
        source_file="tb_test",
        cohort_id="public-textbooks-non-stem-non-ocr",
        source_family="public_textbooks",
        cohort_cfg=cohort_cfg,
        input_root=tmp_path,
        db_conn=conn,
        chunks_map=chunks_map,
    )

    conn.close()

    assert record["permitted_to_proceed"] is False
    assert record["lineage_verification"]["status"] == "UNKNOWN_LINEAGE"
    assert record["blocking_reason"] == "database_content_does_not_match_lineage_chunk_evidence"
    assert missing is not None
    assert missing["reason"] == "database_content_does_not_match_lineage_chunk_evidence"


def test_verify_detects_contradictory_eligibility_and_forged_summary(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """Finding 3: Verify must reject contradictory index records and recompute/reject forged receipt summaries."""
    header, records = synthetic_bundle.read_index()

    # Tamper 1: Make a permitted record contradictory (EXCLUDED_OCR but permitted_to_proceed=True)
    records[0]["lineage_verification"]["status"] = "EXCLUDED_OCR"
    records[0]["lineage_verification"]["is_ocr_derived"] = True
    records[0]["permitted_to_proceed"] = True
    records[0]["blocking_reason"] = None

    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    # Must fail schema / semantic invariant validation
    with pytest.raises(custody.CustodyAccessError, match=r"(error|Contradictory|CONFIRMED_NATIVE)"):
        synthetic_bundle.verify()

    # Tamper 2: Restore valid index, but forge receipt summary count
    base = _get_synthetic_custody_dir()
    shutil.copyfile(
        base / "out/data/projects/open_model_data/custody/v4_source_custody_access_index_v1.jsonl",
        synthetic_bundle.index_path,
    )
    receipt_forged = synthetic_bundle.read_receipt()
    receipt_forged["summary"]["accessible_sources_count"] += 999
    synthetic_bundle.rehash_receipt(receipt_forged)

    with pytest.raises(custody.CustodyAccessError, match=r"Receipt summary accessible_sources_count mismatch"):
        synthetic_bundle.verify()


def test_verify_detects_hash_tampering(synthetic_bundle: SyntheticCustodyBundle) -> None:
    receipt_data = synthetic_bundle.read_receipt()
    receipt_data["config_sha256"] = "0" * 64
    synthetic_bundle.write_receipt(receipt_data)

    with pytest.raises(custody.CustodyAccessError, match="Receipt config_sha256 mismatch"):
        synthetic_bundle.verify()


def test_verify_detects_forged_receipt_id_and_verdict(synthetic_bundle: SyntheticCustodyBundle) -> None:
    receipt_data = synthetic_bundle.read_receipt()

    # Test 1: Forged receipt_id
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["receipt_id"] = "receipt.custody.111122223333444455556666"
    synthetic_bundle.write_receipt(receipt_tampered)
    with pytest.raises(custody.CustodyAccessError, match="Receipt receipt_id mismatch"):
        synthetic_bundle.verify()

    # Test 2: Forged verdict
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["verdict"] = "HALT_INACCESSIBLE_SOURCES"
    synthetic_bundle.write_receipt(receipt_tampered)
    with pytest.raises(custody.CustodyAccessError, match="Receipt verdict mismatch"):
        synthetic_bundle.verify()

    # Test 3: Contradictory safety assertion
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["safety_assertions"]["first_eligible_cohort_ready"] = False
    synthetic_bundle.write_receipt(receipt_tampered)
    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.first_eligible_cohort_ready mismatch"
    ):
        synthetic_bundle.verify()


def test_verify_detects_forged_access_id(synthetic_bundle: SyntheticCustodyBundle) -> None:
    header, records = synthetic_bundle.read_index()
    records[0]["access_id"] = "access.000000000000000000000000"
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"access_id mismatch"):
        synthetic_bundle.verify()


def test_verify_detects_duplicate_source_id(synthetic_bundle: SyntheticCustodyBundle) -> None:
    header, records = synthetic_bundle.read_index()
    records[1] = copy.deepcopy(records[0])
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source_id"):
        synthetic_bundle.verify()


def test_verify_detects_duplicate_source_locator(synthetic_bundle: SyntheticCustodyBundle) -> None:
    header, records = synthetic_bundle.read_index()
    records[2]["source_locator"]["source_file"] = records[1]["source_locator"]["source_file"]
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source locator"):
        synthetic_bundle.verify()


def test_verify_detects_provenance_projection_mismatch(synthetic_bundle: SyntheticCustodyBundle) -> None:
    header, records = synthetic_bundle.read_index()
    records[0]["source_locator"]["source_file"] = "tampered_source_file"
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"projection does not match provenance denominator"):
        synthetic_bundle.verify()


def test_verify_detects_missing_provenance_index(synthetic_bundle: SyntheticCustodyBundle, tmp_path: Path) -> None:
    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config_data["inputs"]["provenance_index"] = "data/projects/open_model_data/nonexistent_provenance_index.jsonl"
    tampered_config = tmp_path / "config.json"
    tampered_config.write_text(json.dumps(config_data), encoding="utf-8")
    expected_config_sha = custody.sha256_file(tampered_config)

    header, records = synthetic_bundle.read_index()
    header_dict = json.loads(header)
    header_dict["config_sha256"] = expected_config_sha
    synthetic_bundle.write_index(json.dumps(header_dict), records)

    receipt = synthetic_bundle.read_receipt()
    receipt["config_sha256"] = expected_config_sha
    synthetic_bundle.rehash_receipt(receipt)

    with pytest.raises(custody.CustodyAccessError, match=r"Provenance index missing"):
        synthetic_bundle.verify(tampered_config)


def test_is_private_or_absolute_host_path() -> None:
    # Allowed clean paths and prose
    assert not custody._is_private_or_absolute_host_path("")
    assert not custody._is_private_or_absolute_host_path("sources/textbooks/math.pdf")
    assert not custody._is_private_or_absolute_host_path("data/clean/source.txt")
    assert not custody._is_private_or_absolute_host_path("file:data/textbook_chunks/grade-06/6-klas.jsonl")
    assert not custody._is_private_or_absolute_host_path("sqlite:sources.db#textbooks")
    assert not custody._is_private_or_absolute_host_path("gdrive:learn-ukrainian-data/textbooks/6-klas.pdf")
    assert not custody._is_private_or_absolute_host_path("A: follow up with the custodian")
    assert not custody._is_private_or_absolute_host_path("B: check item status")
    assert not custody._is_private_or_absolute_host_path("Note: this is clean text")
    assert not custody._is_private_or_absolute_host_path("private archive unavailable")
    assert not custody._is_private_or_absolute_host_path("root cause analysis")
    assert not custody._is_private_or_absolute_host_path("temp storage failure")
    assert not custody._is_private_or_absolute_host_path("clean users list")
    assert not custody._is_private_or_absolute_host_path("home page link")
    assert not custody._is_private_or_absolute_host_path("var environment unset")

    # Unix absolute paths and home expansion
    assert custody._is_private_or_absolute_host_path("/opt/data/book.pdf")
    assert custody._is_private_or_absolute_host_path(f"{FIXTURE_HOME}/book.pdf")
    assert custody._is_private_or_absolute_host_path("~/data.txt")
    assert custody._is_private_or_absolute_host_path(f"~{FIXTURE_USER}/data.txt")

    # Windows drive paths
    assert custody._is_private_or_absolute_host_path(r"C:\Users\alice\private\book.pdf")
    assert custody._is_private_or_absolute_host_path("c:/users/bob/doc.txt")
    assert custody._is_private_or_absolute_host_path(r"D:\repo\data.txt")

    # Windows UNC paths
    assert custody._is_private_or_absolute_host_path(r"\\server\share\data.pdf")
    assert custody._is_private_or_absolute_host_path("//server/share/data.pdf")

    # Private directory segments in path-shaped tokens
    assert custody._is_private_or_absolute_host_path("foo/home/bar.txt")
    assert custody._is_private_or_absolute_host_path("foo/appdata/bar.txt")
    assert custody._is_private_or_absolute_host_path("foo/tmp/bar.txt")
    assert custody._is_private_or_absolute_host_path(r"foo\private\bar.txt")
    assert custody._is_private_or_absolute_host_path("Users/alice/doc.pdf")
    assert custody._is_private_or_absolute_host_path("private/archive")
    assert custody._is_private_or_absolute_host_path(r"private\archive")
    assert custody._is_private_or_absolute_host_path("root/folder")
    assert custody._is_private_or_absolute_host_path("temp/dir")

    # Absolute and private paths after assignment and field separators (=, :)
    assert custody._is_private_or_absolute_host_path("location=/opt/private-corpus")
    assert custody._is_private_or_absolute_host_path("prefix:/opt/private-corpus")
    assert custody._is_private_or_absolute_host_path(r"assignment=C:\Users\alice\private\book.pdf")
    assert custody._is_private_or_absolute_host_path("field:c:/users/bob/doc.txt")
    assert custody._is_private_or_absolute_host_path(r"share=\\server\share\data.pdf")
    assert custody._is_private_or_absolute_host_path("share=//server/share/data.pdf")
    assert custody._is_private_or_absolute_host_path("path=foo/home/bar.txt")


@pytest.mark.parametrize(
    "bad_path",
    [
        pytest.param(f"{FIXTURE_HOME}/books/reader.pdf", id="fixture-home-book"),
        r"C:\Users\alice\private\book.pdf",
        r"\\server\share\private\book.pdf",
        "relative/path/appdata/secrets.txt",
    ],
)
def test_verify_detects_recomputed_safety_assertion_violations(
    synthetic_bundle: SyntheticCustodyBundle, bad_path: str
) -> None:
    header, records = synthetic_bundle.read_index()
    records[0]["custody_resolution"]["archive_store"] = bad_path
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        synthetic_bundle.verify()


@pytest.mark.parametrize(
    "bad_evidence_ref",
    [
        "/home/alice/source.jsonl",
        r"C:\Users\alice\source.jsonl",
        r"\\server\share\evidence.jsonl",
    ],
)
def test_verify_detects_evidence_ref_private_host_path(
    synthetic_bundle: SyntheticCustodyBundle, bad_evidence_ref: str
) -> None:
    header, records = synthetic_bundle.read_index()
    records[0]["lineage_verification"]["evidence_ref"] = bad_evidence_ref
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        synthetic_bundle.verify()


@pytest.mark.parametrize(
    ("field_path", "bad_val"),
    [
        pytest.param(
            ("unmounted_archive_locator",), f"{FIXTURE_HOME}/secret_archive", id="field_path0-fixture-home-archive"
        ),
        (("owner",), "alice at /home/alice"),
        (("scope",), r"processing C:\Users\alice\data"),
        (("accessible_eligible_sources_permitted_to_proceed", "description"), r"Proceed using \\server\share\data.pdf"),
        pytest.param(
            ("missing_inputs", 0, "reason"), f"unmounted at {FIXTURE_HOME}/gdrive", id="field_path4-fixture-home-mount"
        ),
        (("missing_inputs", 0, "blocks"), r"blocked by C:\private\job"),
        (("missing_inputs", 0, "owner"), "/root/admin"),
        (("unmounted_archive_locator",), "location=/opt/private-corpus"),
        (("scope",), "prefix:/opt/private-corpus"),
    ],
)
def test_verify_detects_missing_report_freeform_private_host_paths(
    synthetic_bundle: SyntheticCustodyBundle, field_path: tuple, bad_val: str
) -> None:
    missing_data = synthetic_bundle.read_missing()
    target = missing_data
    for k in field_path[:-1]:
        target = target[k]
    target[field_path[-1]] = bad_val
    synthetic_bundle.write_missing(missing_data)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError, match=r"Receipt safety_assertions\.no_private_host_paths_disclosed mismatch"
    ):
        synthetic_bundle.verify()


def test_verify_allows_missing_report_valid_prose_with_reserved_words(
    synthetic_bundle: SyntheticCustodyBundle, tmp_path: Path
) -> None:
    # Use valid prose containing reserved words ('root', 'temp', 'private') in scope
    prose = "root cause analysis: temp failure investigation for private archive reachability"
    cfg_data = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    cfg_data["ownership"]["blocks_scope"] = prose
    test_cfg_path = tmp_path / "test_config.json"
    test_cfg_path.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")

    header, records = synthetic_bundle.read_index()
    header_dict = json.loads(header)
    header_dict["config_sha256"] = custody.sha256_file(test_cfg_path)
    synthetic_bundle.write_index(custody.canonical_json(header_dict), records)

    missing_data = synthetic_bundle.read_missing()
    missing_data["scope"] = prose
    synthetic_bundle.write_missing(missing_data)

    receipt = synthetic_bundle.read_receipt()
    receipt["config_sha256"] = custody.sha256_file(test_cfg_path)
    synthetic_bundle.rehash_receipt(receipt)

    assert synthetic_bundle.verify(test_cfg_path) is True


def test_check_chunk_file_lineage_preserves_excluded_mode(tmp_path: Path) -> None:
    chunk_file = tmp_path / "scanned_sample.jsonl"
    rows = [
        {"chunk_id": "c1", "extraction_mode": "scanned_image", "text": "Скан."},
    ]
    chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file)
    assert mode == "scanned_image"
    assert is_ocr is True
    assert count == 1


def _fake_bulk_root(root: Path) -> Path:
    for marker in REQUIRED_BULK_MARKERS:
        (root / marker).mkdir(parents=True)
    return root


def test_archive_locator_resolves_through_bulk_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """#8803: gdrive locators name the bulk root, found via the storage resolver."""
    bulk = _fake_bulk_root(tmp_path / "bulk")
    (bulk / "textbooks" / "grade-5").mkdir(parents=True)
    (bulk / "textbooks" / "grade-5" / "tb_one.pdf").write_bytes(b"%PDF-")
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))

    for locator in ("gdrive:learn-ukrainian-data/textbooks", "gdrive:textbooks", "textbooks"):
        assert custody._resolve_archive_mount(locator) == (bulk / "textbooks").resolve()
    archive_map = custody._build_archive_cache_map("gdrive:learn-ukrainian-data/textbooks", "native_pdf_text")
    assert archive_map == {"tb_one": (bulk / "textbooks").resolve() / "grade-5" / "tb_one.pdf"}
    assert custody._check_archive_on_host("gdrive:learn-ukrainian-data/textbooks", "tb_one", "native_pdf_text")


def test_archive_locator_ignores_repository_data_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A repository-relative ``data/textbooks`` is never a stand-in for the bulk root."""
    repo = tmp_path / "repo"
    (repo / "data" / "textbooks").mkdir(parents=True)
    (repo / "data" / "textbooks" / "tb_one.pdf").write_bytes(b"%PDF-")
    (repo / "textbooks").mkdir()
    monkeypatch.chdir(repo)
    # An LU_BULK_ROOT without markers makes the bulk root unavailable (fail closed).
    monkeypatch.setenv(ENV_BULK_ROOT, str(tmp_path / "not-a-bulk-root"))

    for locator in ("gdrive:learn-ukrainian-data/textbooks", "data/textbooks", "textbooks"):
        assert custody._resolve_archive_mount(locator) is None
    assert custody._build_archive_cache_map("data/textbooks", "native_pdf_text") == {}
    assert not custody._check_archive_on_host("data/textbooks", "tb_one", "native_pdf_text")


def test_archive_locator_bare_data_path_is_bulk_relative_not_repo_relative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With a valid bulk root, ``data/textbooks`` still means ``<bulk>/data/textbooks``, never the repo path."""
    repo = tmp_path / "repo"
    (repo / "data" / "textbooks").mkdir(parents=True)
    bulk = _fake_bulk_root(tmp_path / "bulk")
    monkeypatch.chdir(repo)
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))

    assert custody._resolve_archive_mount("data/textbooks") is None


@pytest.mark.parametrize(
    ("locator", "kind"),
    [
        ("gdrive:../x", "gdrive"),
        ("gdrive:learn-ukrainian-data/../x", "gdrive"),
        ("gdrive:textbooks/../../x", "gdrive"),
        ("gdrive:/x", "gdrive"),
        ("gdrive:", "gdrive"),
        ("gdrive:.", "gdrive"),
        ("../x", "archive"),
        ("/x", "archive"),
    ],
)
def test_archive_locator_rejects_escape_and_absolute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, locator: str, kind: str
) -> None:
    """Locators must stay inside the bulk root; the error names the kind, not a path."""
    bulk = _fake_bulk_root(tmp_path / "bulk")
    (tmp_path / "x").mkdir()
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))

    with pytest.raises(custody.CustodyAccessError, match=rf"^{kind} locator ") as excinfo:
        custody._resolve_archive_mount(locator)
    assert str(tmp_path) not in str(excinfo.value)
    with pytest.raises(custody.CustodyAccessError):
        custody._build_archive_cache_map(locator, "native_pdf_text")
    with pytest.raises(custody.CustodyAccessError):
        custody._check_archive_on_host(locator, "tb_one", "native_pdf_text")


def test_archive_locator_rejects_symlink_escaping_bulk_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A symlink inside the bulk root that points outside it does not count as inside the root."""
    bulk = _fake_bulk_root(tmp_path / "bulk")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "tb_one.pdf").write_bytes(b"%PDF-")
    (bulk / "textbooks").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))

    with pytest.raises(custody.CustodyAccessError, match=r"^gdrive locator resolves outside the bulk root$"):
        custody._resolve_archive_mount("gdrive:learn-ukrainian-data/textbooks")


def test_archive_locator_accepts_symlink_staying_inside_bulk_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A symlink whose target is still inside the bulk root is accepted and returned resolved."""
    bulk = _fake_bulk_root(tmp_path / "bulk")
    (bulk / "real_textbooks").mkdir()
    (bulk / "textbooks").symlink_to(bulk / "real_textbooks", target_is_directory=True)
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))

    assert custody._resolve_archive_mount("gdrive:textbooks") == (bulk / "real_textbooks").resolve()


def test_input_root_takes_precedence_over_cwd(tmp_path: Path) -> None:
    custom_input = tmp_path / "input"
    prov_dir = custom_input / "data/projects/open_model_data/provenance"
    prov_dir.mkdir(parents=True)
    custom_prov = prov_dir / "v4_source_provenance_index_v1.jsonl"
    custom_prov.write_text("CUSTOM_PROV_HEADER\n", encoding="utf-8")

    rel_path = Path("data/projects/open_model_data/provenance/v4_source_provenance_index_v1.jsonl")
    resolved = custody._resolve_file(rel_path, [custom_input, Path.cwd()])
    assert resolved == custom_prov


def test_verify_detects_cohort_id_mismatch_in_summary(synthetic_bundle: SyntheticCustodyBundle) -> None:
    receipt_data = synthetic_bundle.read_receipt()

    # Tamper first_eligible_cohort cohort_id
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["summary"]["first_eligible_cohort"]["cohort_id"] = "wrong-cohort"
    synthetic_bundle.write_receipt(receipt_tampered)
    with pytest.raises(custody.CustodyAccessError, match=r"Receipt first_eligible_cohort discrepancy"):
        synthetic_bundle.verify()

    # Tamper textbook_cohort cohort_id
    receipt_tampered2 = copy.deepcopy(receipt_data)
    receipt_tampered2["summary"]["textbook_cohort"]["cohort_id"] = "wrong-cohort"
    synthetic_bundle.write_receipt(receipt_tampered2)
    with pytest.raises(custody.CustodyAccessError, match=r"Receipt textbook_cohort discrepancy"):
        synthetic_bundle.verify()


def test_read_command_fails_when_source_yields_zero_records(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()
    conn.close()

    exit_code = custody.main(
        ["read", "--database", str(db_path), "--table", "literary_texts", "--source-file", "nonexistent"]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Access proof failed" in captured.err
    assert '"records_streamed":0' in captured.out


def test_resolve_source_access_requires_exact_cohort_and_source_family(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()

    # Empty cohort_cfg
    with pytest.raises(custody.CustodyAccessError, match=r"requires an exact configured cohort entry"):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    # Cohort ID mismatch
    with pytest.raises(custody.CustodyAccessError, match=r"requires an exact configured cohort entry"):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={"cohort_id": "other-cohort", "source_family": "literary"},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    # Source family mismatch
    with pytest.raises(
        custody.CustodyAccessError,
        match=r"source_family 'literary' does not match configured cohort source_family 'public_textbooks'",
    ):
        custody.resolve_source_access(
            source_id="s1",
            source_file="f1",
            cohort_id="literary-non-ocr",
            source_family="literary",
            cohort_cfg={"cohort_id": "literary-non-ocr", "source_family": "public_textbooks"},
            input_root=tmp_path,
            db_conn=conn,
            chunks_map={},
        )

    conn.close()


def test_build_and_verify_detect_unconfigured_and_mismatched_cohort(tmp_path: Path, repo_root: Path) -> None:
    custom_input = tmp_path / "input"
    custom_out = tmp_path / "out"
    custom_input.mkdir(parents=True)
    custom_out.mkdir(parents=True)

    config_path = custom_input / "config.json"
    config_data = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    config_data["cohorts"] = [c for c in config_data["cohorts"] if c["cohort_id"] == "literary-non-ocr"]
    config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    prov_dir = custom_input / "data/projects/open_model_data/provenance"
    prov_dir.mkdir(parents=True)
    prov_file = prov_dir / "v4_provenance_restoration_index_v1.jsonl"
    prov_rows = [
        json.dumps({"schema_version": "v4_provenance_restoration_index_v1", "records": 1}),
        json.dumps(
            {
                "source_id": "source.public_textbooks.123",
                "cohort_id": "public-textbooks-non-stem-non-ocr",
                "source_family": "public_textbooks",
                "source_locator": {"source_file": "tb1"},
            }
        ),
    ]
    prov_file.write_text("\n".join(prov_rows) + "\n", encoding="utf-8")

    db_file = custom_input / "data/sources.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, source_file TEXT, chunk_id TEXT, text TEXT);")
    conn.commit()
    conn.close()

    with pytest.raises(
        custody.CustodyAccessError, match=r"references unconfigured cohort_id 'public-textbooks-non-stem-non-ocr'"
    ):
        custody.build(config_path, input_root=custom_input, output_root=custom_out)

    # Mismatched source_family between provenance row and config cohort
    config_data2 = json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8"))
    for c in config_data2["cohorts"]:
        if c["cohort_id"] == "public-textbooks-non-stem-non-ocr":
            c["source_family"] = "literary"
            c["resolver_kind"] = "sqlite_database"
            c["lineage_rule"] = "native_digital_source"
            c["primary_store"] = "sqlite:sources.db#literary_texts"
    config_path2 = custom_input / "config2.json"
    config_path2.write_text(json.dumps(config_data2, indent=2), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"does not match configured cohort source_family"):
        custody.build(config_path2, input_root=custom_input, output_root=custom_out)


def test_validate_cohort_spec_enforces_compatible_resolver_and_lineage_rule() -> None:
    # Literary incompatible resolver_kind
    with pytest.raises(custody.CustodyAccessError, match=r"requires resolver_kind 'sqlite_database'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_digital_source",
            }
        )

    # Literary incompatible lineage_rule
    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_digital_source'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_pdf_text",
            }
        )

    # Public textbooks incompatible resolver_kind
    with pytest.raises(custody.CustodyAccessError, match=r"requires resolver_kind 'hybrid_sqlite_chunks_archive'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_pdf_text",
            }
        )

    # Public textbooks incompatible lineage_rule
    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_pdf_text'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_digital_source",
            }
        )

    # Unknown source_family
    with pytest.raises(custody.CustodyAccessError, match=r"unsupported source_family 'unknown'"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "unknown",
                "source_family": "unknown",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_digital_source",
            }
        )


def test_verify_detects_incompatible_cohort_lineage_rule_in_config(tmp_path: Path, repo_root: Path) -> None:
    tampered_out = tmp_path / "out"
    custody_dir = tampered_out / "data/projects/open_model_data/custody"
    custody_dir.mkdir(parents=True)

    # Tamper config so literary specifies native_pdf_text
    config_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    for c in config_data["cohorts"]:
        if c["cohort_id"] == "literary-non-ocr":
            c["lineage_rule"] = "native_pdf_text"
    tampered_config = tmp_path / "config.json"
    tampered_config.write_text(json.dumps(config_data), encoding="utf-8")

    with pytest.raises(custody.CustodyAccessError, match=r"requires lineage_rule 'native_digital_source'"):
        custody.verify(tampered_config, input_root=repo_root, output_root=tampered_out)


def test_verify_rejects_unknown_mode_labeled_as_confirmed_native(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """Codex finding r3980769771: Blocked record with status=CONFIRMED_NATIVE and lineage_mode=unknown must fail."""
    header, records = synthetic_bundle.read_index()

    # Pick a blocked textbook record
    target_idx = None
    for i, r in enumerate(records):
        if not r["permitted_to_proceed"] and r["lineage_verification"]["status"] == "UNKNOWN_LINEAGE":
            target_idx = i
            break
    assert target_idx is not None

    # Set status to CONFIRMED_NATIVE while leaving lineage_mode as unknown (and permitted_to_proceed=False)
    records[target_idx]["lineage_verification"]["status"] = "CONFIRMED_NATIVE"
    records[target_idx]["lineage_verification"]["lineage_mode"] = "unknown"

    synthetic_bundle.write_index(header, records)

    # Re-hash index and update receipt summary counts to test semantic rejection
    receipt_data = synthetic_bundle.read_receipt()
    receipt_data["summary"]["confirmed_native_count"] += 1
    receipt_data["summary"]["textbook_cohort"]["confirmed_native"] += 1
    synthetic_bundle.rehash_receipt(receipt_data)

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is CONFIRMED_NATIVE but lineage_mode is 'unknown'",
    ):
        synthetic_bundle.verify()


def test_verify_rejects_contradictory_lineage_status_and_mode_combinations(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """Validate that any mismatch between lineage status and mode is rejected by verify."""
    header, records = synthetic_bundle.read_index()

    # Test 1: UNKNOWN_LINEAGE status with native_digital_source mode
    records_copy = copy.deepcopy(records)
    for r in records_copy:
        if not r["permitted_to_proceed"]:
            r["lineage_verification"]["lineage_mode"] = "native_digital_source"
            break
    synthetic_bundle.write_index(header, records_copy)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is UNKNOWN_LINEAGE but lineage_mode is 'native_digital_source'",
    ):
        synthetic_bundle.verify()

    # Test 2: EXCLUDED_OCR status with native_digital_source mode (and is_ocr_derived=True so schema passes)
    records_copy = copy.deepcopy(records)
    for r in records_copy:
        if not r["permitted_to_proceed"]:
            r["lineage_verification"]["status"] = "EXCLUDED_OCR"
            r["lineage_verification"]["lineage_mode"] = "native_digital_source"
            r["lineage_verification"]["is_ocr_derived"] = True
            break
    synthetic_bundle.write_index(header, records_copy)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"lineage status is EXCLUDED_OCR but lineage_mode is 'native_digital_source'",
    ):
        synthetic_bundle.verify()


def test_bounded_custody_reader_rejects_non_positive_batch_size(tmp_path: Path) -> None:
    """BoundedCustodyReader.read_source_stream must reject batch_size <= 0 (ACCESS-3)."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE tbl (source_file TEXT, text TEXT)")
    conn.execute("INSERT INTO tbl VALUES ('f1', 'hello')")
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_path)
    with pytest.raises(custody.CustodyAccessError, match=r"batch_size must be strictly positive \(> 0\), got 0"):
        reader.read_source_stream("tbl", "f1", batch_size=0)

    with pytest.raises(custody.CustodyAccessError, match=r"batch_size must be strictly positive \(> 0\), got -10"):
        reader.read_source_stream("tbl", "f1", batch_size=-10)


def test_textbook_cohort_summary_missing_on_host_reflects_archive_reachability(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """Receipt summary must count all textbooks with unmounted host archives as missing_on_host."""
    real_receipt = json.loads(
        (REGISTRY_CUSTODY_DIR / "v4_source_custody_access_receipt_v1.json").read_text(encoding="utf-8")
    )
    assert real_receipt["summary"]["textbook_cohort"]["missing_on_host"] == 122

    receipt_data = synthetic_bundle.read_receipt()
    expected_missing = receipt_data["summary"]["textbook_cohort"]["missing_on_host"]

    # Tamper missing_on_host to a different count and verify rejection
    receipt_tampered = copy.deepcopy(receipt_data)
    receipt_tampered["summary"]["textbook_cohort"]["missing_on_host"] = expected_missing - 1
    synthetic_bundle.write_receipt(receipt_tampered)

    with pytest.raises(custody.CustodyAccessError, match=r"Receipt textbook_cohort discrepancy"):
        synthetic_bundle.verify()


@pytest.mark.parametrize(
    ("meta_key", "tampered_val", "expected_err"),
    [
        ("owner", "unauthorized-party", r"Missing report owner mismatch"),
        ("scope", "all datasets globally", r"Missing report scope mismatch"),
        ("operator_decision_date", "1999-01-01", r"Missing report operator_decision_date mismatch"),
        ("issue", 12345, r"Missing report issue mismatch"),
        ("unmounted_archive_locator", "s3://tampered-bucket", r"Missing report unmounted_archive_locator mismatch"),
    ],
)
def test_verify_detects_tampered_missing_report_metadata(
    synthetic_bundle: SyntheticCustodyBundle, meta_key: str, tampered_val: Any, expected_err: str
) -> None:
    """Missing report metadata must strictly match custody config (ACCESS-4)."""
    missing_data = synthetic_bundle.read_missing()
    missing_data[meta_key] = tampered_val
    synthetic_bundle.write_missing(missing_data)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=expected_err):
        synthetic_bundle.verify()


def test_verify_detects_tampered_missing_report_items(synthetic_bundle: SyntheticCustodyBundle) -> None:
    """Missing report items must strictly match derived missing items from the access index (ACCESS-4)."""
    orig_missing = synthetic_bundle.read_missing()

    # Case 1: Dropping an item (count mismatch)
    missing_tampered = copy.deepcopy(orig_missing)
    missing_tampered["missing_inputs"].pop()
    synthetic_bundle.write_missing(missing_tampered)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"Missing report item count mismatch"):
        synthetic_bundle.verify()

    # Case 2: Unexpected source_id
    missing_tampered = copy.deepcopy(orig_missing)
    missing_tampered["missing_inputs"][0]["source_id"] = "source.public_textbooks.unexpected_fictitious_id"
    synthetic_bundle.write_missing(missing_tampered)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError, match=r"unexpected source_id 'source\.public_textbooks\.unexpected_fictitious_id'"
    ):
        synthetic_bundle.verify()

    # Case 3: Altered field in an item (e.g. reason)
    missing_tampered = copy.deepcopy(orig_missing)
    sid = missing_tampered["missing_inputs"][0]["source_id"]
    missing_tampered["missing_inputs"][0]["reason"] = "tampered_arbitrary_reason"
    synthetic_bundle.write_missing(missing_tampered)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=rf"Missing report entry for '{re.escape(sid)}' mismatch"):
        synthetic_bundle.verify()


def test_receipt_id_includes_missing_report_sha256() -> None:
    """Receipt ID must cryptographically bind config, index, and missing report hashes."""
    id1 = custody._make_receipt_id("cfg_hash", "idx_hash", "missing_hash_1")
    id2 = custody._make_receipt_id("cfg_hash", "idx_hash", "missing_hash_2")
    assert id1 != id2

    receipt_orig = REGISTRY_CUSTODY_DIR / "v4_source_custody_access_receipt_v1.json"
    receipt_data = json.loads(receipt_orig.read_text(encoding="utf-8"))
    expected_id = custody._make_receipt_id(
        receipt_data["config_sha256"],
        receipt_data["index_sha256"],
        receipt_data["missing_report_sha256"],
    )
    assert receipt_data["receipt_id"] == expected_id


def test_validate_and_resolve_paths_rejects_aliasing_collision_and_escaping(tmp_path: Path) -> None:
    """Validate that output paths cannot alias inputs, collide with each other, or escape output_root."""
    in_root = tmp_path / "inputs"
    out_root = tmp_path / "outputs"
    in_root.mkdir()
    out_root.mkdir()

    base_cfg: dict[str, Any] = {
        "inputs": {
            "provenance_index": "data/provenance.jsonl",
            "database": "data/sources.db",
            "textbook_chunks_dir": "data/chunks",
        },
        "outputs": {
            "index": "out/index.jsonl",
            "missing_report": "out/missing.json",
            "receipt": "out/receipt.json",
        },
    }

    # Normal valid resolution
    _res_in, res_out = custody.validate_and_resolve_paths(base_cfg, in_root, out_root)
    assert res_out["index"] == (out_root / "out/index.jsonl").resolve()

    # Output aliases database input
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data/sources.db").touch()
    (tmp_path / "data/chunks").mkdir(parents=True, exist_ok=True)
    cfg_alias_db = copy.deepcopy(base_cfg)
    cfg_alias_db["outputs"]["index"] = "data/sources.db"
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'database'"):
        custody.validate_and_resolve_paths(cfg_alias_db, input_root=tmp_path, output_root=tmp_path)

    # Output inside textbook_chunks_dir
    cfg_inside_chunks = copy.deepcopy(base_cfg)
    cfg_inside_chunks["outputs"]["index"] = "data/chunks/sub/index.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"located inside input directory 'textbook_chunks_dir'"):
        custody.validate_and_resolve_paths(cfg_inside_chunks, input_root=tmp_path, output_root=tmp_path)

    # Output collision between two outputs
    cfg_collision = copy.deepcopy(base_cfg)
    cfg_collision["outputs"]["receipt"] = "out/index.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"Output path collision between 'index' and 'receipt'"):
        custody.validate_and_resolve_paths(cfg_collision, in_root, out_root)

    # Output escapes output_root
    cfg_escape = copy.deepcopy(base_cfg)
    cfg_escape["outputs"]["index"] = "../../escaped.jsonl"
    with pytest.raises(custody.CustodyAccessError, match=r"escapes output_root"):
        custody.validate_and_resolve_paths(cfg_escape, in_root, out_root)

    # Missing required output key
    cfg_missing_key = copy.deepcopy(base_cfg)
    del cfg_missing_key["outputs"]["receipt"]
    with pytest.raises(custody.CustodyAccessError, match=r"Missing required output key in config: 'receipt'"):
        custody.validate_and_resolve_paths(cfg_missing_key, in_root, out_root)


def test_cohort_spec_and_reader_reject_unapproved_table_names_and_sql_injection(tmp_path: Path) -> None:
    """Cohort config, stream reader, and verifier reject unapproved tables and SQL injection."""
    # Config cohort with SQL injection in primary_store
    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match approved store"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "lit",
                "source_family": "literary",
                "resolver_kind": "sqlite_database",
                "lineage_rule": "native_digital_source",
                "primary_store": "sqlite:sources.db#literary_texts WHERE source_file = ? OR 1=1 --",
            }
        )

    # Config cohort with unapproved table
    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match approved store"):
        custody.validate_cohort_spec(
            {
                "cohort_id": "tb",
                "source_family": "public_textbooks",
                "resolver_kind": "hybrid_sqlite_chunks_archive",
                "lineage_rule": "native_pdf_text",
                "primary_store": "sqlite:sources.db#sqlite_master",
            }
        )

    # BoundedCustodyReader rejects unapproved table
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE foo (id INT);")
    conn.commit()
    conn.close()

    reader = custody.BoundedCustodyReader(db_file)
    with pytest.raises(custody.CustodyAccessError, match=r"not an approved custody database table"):
        reader.read_source_stream("sqlite_master", "dummy")

    with pytest.raises(custody.CustodyAccessError, match=r"not an approved custody database table"):
        reader.read_source_stream("literary_texts WHERE 1=1 --", "dummy")


def test_verify_detects_duplicate_missing_source_id_and_omissions(synthetic_bundle: SyntheticCustodyBundle) -> None:
    """Missing report verification detects duplicate source IDs and omitted items."""
    orig_missing = synthetic_bundle.read_missing()
    # Duplicate an entry while keeping list length identical
    dup_missing = copy.deepcopy(orig_missing)
    dup_missing["missing_inputs"][1] = copy.deepcopy(dup_missing["missing_inputs"][0])
    synthetic_bundle.write_missing(dup_missing)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"duplicate source_id .* in missing_inputs"):
        synthetic_bundle.verify()


@pytest.mark.parametrize(
    ("mutation_key", "mutation_val"),
    [
        ("permitted", False),
        ("permitted_cohort_ids", ["public-textbooks-non-stem-non-ocr"]),
        ("description", "Tampered progression decision text without any private paths"),
    ],
)
def test_verify_detects_tampered_progression_decision(
    synthetic_bundle: SyntheticCustodyBundle, mutation_key: str, mutation_val: Any
) -> None:
    """Missing report progression decision tampering is caught by verify()."""
    missing_data = synthetic_bundle.read_missing()
    missing_data["accessible_eligible_sources_permitted_to_proceed"][mutation_key] = mutation_val
    synthetic_bundle.write_missing(missing_data)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"Missing report accessible_eligible_sources_permitted_to_proceed mismatch",
    ):
        synthetic_bundle.verify()


def test_verify_detects_tampered_primary_store_in_index(synthetic_bundle: SyntheticCustodyBundle) -> None:
    """Index record with tampered primary_store (e.g. SQL injection suffix) is rejected by verify()."""
    header, records = synthetic_bundle.read_index()
    records[0]["custody_resolution"]["primary_store"] = "sqlite:sources.db#literary_texts WHERE 1=1 --"
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"primary_store .* does not match expected"):
        synthetic_bundle.verify()


def test_validate_and_resolve_paths_protects_config_and_schemas_from_aliases(repo_root: Path) -> None:
    """Outputs cannot alias consumed config file or schema contracts."""
    base_cfg: dict[str, Any] = {
        "inputs": {
            "provenance_index": "data/provenance.jsonl",
            "database": "data/sources.db",
            "textbook_chunks_dir": "data/chunks",
        },
        "outputs": {
            "index": "out/index.jsonl",
            "missing_report": "out/missing.json",
            "receipt": "out/receipt.json",
        },
    }

    # Output aliases config path
    cfg_alias_config = copy.deepcopy(base_cfg)
    cfg_alias_config["outputs"]["index"] = str(custody.DEFAULT_CONFIG)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'config'"):
        custody.validate_and_resolve_paths(
            cfg_alias_config, input_root=repo_root, output_root=repo_root, config_path=custody.DEFAULT_CONFIG
        )

    # Output aliases item schema
    cfg_alias_schema = copy.deepcopy(base_cfg)
    cfg_alias_schema["outputs"]["index"] = str(custody.ITEM_SCHEMA_PATH)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'item_schema'"):
        custody.validate_and_resolve_paths(cfg_alias_schema, input_root=repo_root, output_root=repo_root)

    # Output aliases missing report schema
    cfg_alias_missing_schema = copy.deepcopy(base_cfg)
    cfg_alias_missing_schema["outputs"]["index"] = str(custody.MISSING_REPORT_SCHEMA_PATH)
    with pytest.raises(custody.CustodyAccessError, match=r"aliases input 'missing_report_schema'"):
        custody.validate_and_resolve_paths(cfg_alias_missing_schema, input_root=repo_root, output_root=repo_root)


def test_validate_cohort_spec_and_lineage_reject_non_ocr_excluded_modes(tmp_path: Path) -> None:
    """Cohort configuration and chunk lineage reader reject non-OCR extraction modes in excluded_modes."""
    for bad_mode in ("native_text", "native_pdf_text", "unknown", "invalid_mode"):
        with pytest.raises(custody.CustodyAccessError, match=r"excluded_modes contains unsupported or non-OCR mode"):
            custody.validate_cohort_spec(
                {
                    "cohort_id": "tb",
                    "source_family": "public_textbooks",
                    "resolver_kind": "hybrid_sqlite_chunks_archive",
                    "lineage_rule": "native_pdf_text",
                    "excluded_modes": [bad_mode],
                }
            )

        with pytest.raises(custody.CustodyAccessError, match=r"excluded_modes contains unsupported or non-OCR mode"):
            custody.check_chunk_file_lineage(tmp_path / "dummy.jsonl", excluded_modes=[bad_mode])


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl",
)
def test_validate_and_resolve_paths_preserves_cwd_fallback(tmp_path: Path, repo_root: Path) -> None:
    """When an input is not present under input_root, validate_and_resolve_paths falls back to cwd."""
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    cfg: dict[str, Any] = {
        "inputs": {
            "provenance_index": "data/projects/open_model_data/provenance/v4_provenance_restoration_index_v1.jsonl",
            "database": "data/sources.db",
            "textbook_chunks_dir": "data/textbook_chunks",
        },
        "outputs": {
            "index": "out/index.jsonl",
            "missing_report": "out/missing.json",
            "receipt": "out/receipt.json",
        },
    }

    # tmp_path has no provenance_index or database, so it falls back to cwd (repo_root)
    resolved_in, _ = custody.validate_and_resolve_paths(cfg, input_root=tmp_path, output_root=out_dir)
    assert resolved_in["provenance_index"] == (repo_root / cfg["inputs"]["provenance_index"]).resolve()

    # When input_root does contain the file, input_root wins
    custom_prov = tmp_path / cfg["inputs"]["provenance_index"]
    custom_prov.parent.mkdir(parents=True, exist_ok=True)
    custom_prov.write_text("CUSTOM_INDEX\n", encoding="utf-8")
    resolved_in2, _ = custody.validate_and_resolve_paths(cfg, input_root=tmp_path, output_root=out_dir)
    assert resolved_in2["provenance_index"] == custom_prov.resolve()


def test_derive_missing_report_item_separates_lineage_exclusion_from_reachable_archive() -> None:
    """Textbooks with reachable archives on host are never reported as missing, even when blocked by OCR or lineage."""
    cfg = {"ownership": {"unmounted_archive_owner": "custody-owner"}}

    # Blocked by OCR, but raw archive is mounted and reachable on host
    reachable_ocr_row = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_id": "source.public_textbooks.reachable_ocr",
        "source_locator": {"source_file": "10-klas-ocr-book"},
        "custody_resolution": {
            "status": "RESOLVED_ACCESSIBLE",
            "primary_store": "sqlite:sources.db#textbooks",
            "archive_store": "gdrive:learn-ukrainian-data/textbooks/10-klas-ocr-book.pdf",
            "host_reachable": True,
        },
        "lineage_verification": {
            "status": "EXCLUDED_OCR",
            "lineage_mode": "ocr",
            "is_ocr_derived": True,
        },
        "permitted_to_proceed": False,
        "blocking_reason": "ocr_derived_extraction_mode_excluded",
    }
    assert custody.derive_missing_report_item(reachable_ocr_row, cfg) is None

    # Blocked by lineage discrepancy, but raw archive is mounted and reachable on host
    reachable_discrepancy_row = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_id": "source.public_textbooks.reachable_discrepancy",
        "source_locator": {"source_file": "10-klas-discrepancy-book"},
        "custody_resolution": {
            "status": "RESOLVED_ACCESSIBLE",
            "primary_store": "sqlite:sources.db#textbooks",
            "archive_store": "gdrive:learn-ukrainian-data/textbooks/10-klas-discrepancy-book.pdf",
            "host_reachable": True,
        },
        "lineage_verification": {
            "status": "UNKNOWN_LINEAGE",
            "lineage_mode": "unknown",
            "is_ocr_derived": False,
        },
        "permitted_to_proceed": False,
        "blocking_reason": "database_content_does_not_match_lineage_chunk_evidence",
    }
    assert custody.derive_missing_report_item(reachable_discrepancy_row, cfg) is None

    # Unmounted archive on host (PARTIAL_CHUNKS_AND_DB_ONLY) -> reported as missing
    unmounted_row = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_id": "source.public_textbooks.unmounted",
        "source_locator": {"source_file": "10-klas-unmounted-book"},
        "custody_resolution": {
            "status": "PARTIAL_CHUNKS_AND_DB_ONLY",
            "primary_store": "sqlite:sources.db#textbooks",
            "archive_store": "gdrive:learn-ukrainian-data/textbooks/10-klas-unmounted-book.pdf",
            "host_reachable": True,
        },
        "lineage_verification": {
            "status": "CONFIRMED_NATIVE",
            "lineage_mode": "native_pdf_text",
            "is_ocr_derived": False,
        },
        "permitted_to_proceed": True,
        "blocking_reason": None,
    }
    item = custody.derive_missing_report_item(unmounted_row, cfg)
    assert item is not None
    assert item["reason"] == "execution_host_resolver_unmounted"

    # Completely unreachable on host (UNREACHABLE_ON_HOST) -> reported as missing
    unreachable_row = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_id": "source.public_textbooks.unreachable",
        "source_locator": {"source_file": "10-klas-unreachable-book"},
        "custody_resolution": {
            "status": "UNREACHABLE_ON_HOST",
            "primary_store": "sqlite:sources.db#textbooks",
            "archive_store": "gdrive:learn-ukrainian-data/textbooks/10-klas-unreachable-book.pdf",
            "host_reachable": False,
        },
        "lineage_verification": {
            "status": "UNKNOWN_LINEAGE",
            "lineage_mode": "unknown",
            "is_ocr_derived": False,
        },
        "permitted_to_proceed": False,
        "blocking_reason": "missing_chunk_file_and_unmounted_archive",
    }
    item2 = custody.derive_missing_report_item(unreachable_row, cfg)
    assert item2 is not None
    assert item2["reason"] == "missing_chunk_file_and_unmounted_archive"


def test_check_chunk_file_lineage_classifies_ocr_modes_with_empty_excluded_modes(tmp_path: Path) -> None:
    """Known OCR modes are recognized as OCR even when excluded_modes is empty or incomplete (ACCESS-2)."""
    for mode_name in sorted(custody.OCR_LINEAGE_MODES):
        chunk_file = tmp_path / f"{mode_name}_sample.jsonl"
        rows = [
            {"chunk_id": "c1", "extraction_mode": mode_name, "text": "Текст."},
        ]
        chunk_file.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

        mode, is_ocr, count, _chars, _digest = custody.check_chunk_file_lineage(chunk_file, excluded_modes=[])
        assert mode == mode_name
        assert is_ocr is True
        assert count == 1


def test_resolve_source_access_normalizes_relative_input_root(tmp_path: Path) -> None:
    """resolve_source_access relativizes chunk paths against normalized input_root when relative path is given."""
    chunks_dir = tmp_path / "data/textbook_chunks/grade-10"
    chunks_dir.mkdir(parents=True)
    chunk_file = (chunks_dir / "10-klas-book.jsonl").resolve()
    chunk_file.write_text(
        json.dumps(
            {
                "chunk_id": "c1",
                "extraction_mode": "native_pdf_text",
                "page_extraction_mode": "native_pdf_text",
                "text": "Текст",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn.execute("INSERT INTO textbooks (chunk_id, source_file, text) VALUES ('c1', '10-klas-book', 'Текст');")
    conn.commit()

    cohort_cfg = {
        "cohort_id": "public-textbooks-non-stem-non-ocr",
        "source_family": "public_textbooks",
        "resolver_kind": "hybrid_sqlite_chunks_archive",
        "lineage_rule": "native_pdf_text",
        "archive_locator": "gdrive:learn-ukrainian-data/textbooks",
        "primary_store": "sqlite:sources.db#textbooks",
    }

    rel_root = Path(os.path.relpath(tmp_path, Path.cwd()))
    record, _missing = custody.resolve_source_access(
        source_id="source.public_textbooks.rel_test",
        source_file="10-klas-book",
        cohort_id="public-textbooks-non-stem-non-ocr",
        source_family="public_textbooks",
        cohort_cfg=cohort_cfg,
        input_root=rel_root,
        db_conn=conn,
        chunks_map={"10-klas-book": chunk_file},
    )
    conn.close()

    assert record["custody_resolution"]["chunks_store"] == "file:data/textbook_chunks/grade-10/10-klas-book.jsonl"


def test_verify_detects_unmounted_textbook_tampered_as_accessible(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() rejects an index claiming RESOLVED_ACCESSIBLE when the archive is unmounted on host (ACCESS-4)."""
    header, records = synthetic_bundle.read_index()

    tampered_sid = None
    for r in records:
        if (
            r["cohort_id"] == "public-textbooks-non-stem-non-ocr"
            and r["custody_resolution"]["status"] == "PARTIAL_CHUNKS_AND_DB_ONLY"
            and tampered_sid is None
        ):
            tampered_sid = r["source_id"]
            r["custody_resolution"]["status"] = "RESOLVED_ACCESSIBLE"
            r["custody_resolution"]["host_reachable"] = True
            break

    assert tampered_sid is not None
    synthetic_bundle.write_index(header, records)

    orig_missing = synthetic_bundle.read_missing()
    missing_tampered = copy.deepcopy(orig_missing)
    missing_tampered["missing_inputs"] = [
        item for item in missing_tampered["missing_inputs"] if item["source_id"] != tampered_sid
    ]
    synthetic_bundle.write_missing(missing_tampered)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"custody status (claims 'RESOLVED_ACCESSIBLE' but host archive is unmounted|mismatch)",
    ):
        synthetic_bundle.verify(require_database=True)


def test_archive_locator_grade_tree_and_mount_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """_resolve_archive_mount, _build_archive_cache_map, and _check_archive_on_host resolve across grade directories and logical locators (Finding 2)."""
    bulk = _fake_bulk_root(tmp_path / "bulk")
    monkeypatch.setenv(ENV_BULK_ROOT, str(bulk))
    tb_dir = bulk / "textbooks"
    tb_dir.mkdir(parents=True)
    (tb_dir / "top_book.pdf").touch()
    (tb_dir / "grade-10").mkdir()
    (tb_dir / "grade-10" / "grade10_book.pdf").touch()
    (tb_dir / "sub_other").mkdir()
    (tb_dir / "sub_other" / "other_book.pdf").touch()

    lit_dir = bulk / "lit_archive"
    lit_dir.mkdir()
    (lit_dir / "lit_book.jsonl").touch()

    # Test _resolve_archive_mount
    m1 = custody._resolve_archive_mount("gdrive:learn-ukrainian-data/textbooks")
    assert m1 == tb_dir
    m3 = custody._resolve_archive_mount("gdrive:lit_archive")
    assert m3 == lit_dir
    assert custody._resolve_archive_mount("") is None
    assert custody._resolve_archive_mount("nonexistent") is None

    # Test _build_archive_cache_map
    tb_map = custody._build_archive_cache_map(
        "gdrive:learn-ukrainian-data/textbooks",
        "native_pdf_text",
    )
    assert "top_book" in tb_map
    assert "grade10_book" in tb_map
    assert "other_book" in tb_map
    assert tb_map["grade10_book"] == tb_dir / "grade-10" / "grade10_book.pdf"

    lit_map = custody._build_archive_cache_map(
        "gdrive:lit_archive",
        "native_digital_source",
    )
    assert "lit_book" in lit_map

    # Test _check_archive_on_host with cache
    assert custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "grade10_book",
        "native_pdf_text",
        cached_map=tb_map,
    )
    assert not custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "missing_book",
        "native_pdf_text",
        cached_map=tb_map,
    )

    # Test _check_archive_on_host without cache (direct filesystem scan)
    assert custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "top_book",
        "native_pdf_text",
        cached_map=None,
    )
    assert custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "grade10_book",
        "native_pdf_text",
        cached_map=None,
    )
    assert custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "other_book",
        "native_pdf_text",
        cached_map=None,
    )
    assert not custody._check_archive_on_host(
        "gdrive:learn-ukrainian-data/textbooks",
        "missing_book",
        "native_pdf_text",
        cached_map=None,
    )


def test_precompute_table_source_metrics_matches_stream_and_chunk_digests(tmp_path: Path) -> None:
    """_precompute_table_source_metrics computes exact per-source stream and chunk metrics in a single pass."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE literary_texts (id INTEGER PRIMARY KEY, chunk_id TEXT, source_file TEXT, text TEXT);")
    conn.execute(
        "INSERT INTO literary_texts (chunk_id, source_file, text) VALUES "
        "('c1', 'src_a', 'Text A1'), "
        "('c2', 'src_a', 'Text A2'), "
        "('c1', 'src_b', 'Text B1');"
    )
    conn.commit()

    s_m, c_m = custody._precompute_table_source_metrics(conn, "literary_texts")
    assert set(s_m.keys()) == {"src_a", "src_b"}
    assert set(c_m.keys()) == {"src_a", "src_b"}

    assert s_m["src_a"][0] == 2  # records
    assert s_m["src_a"][1] == len("Text A1") + len("Text A2")  # characters
    assert c_m["src_a"][0] == 2  # chunk records

    empty_s, empty_c = custody._precompute_table_source_metrics(conn, "nonexistent_table")
    assert empty_s == {}
    assert empty_c == {}
    conn.close()


def test_verify_detects_tampered_database_stream_metrics(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() detects when index observed_records, observed_characters, or stream_sha256 disagree with sources.db (Finding 1)."""
    header, records = synthetic_bundle.read_index()

    tampered_idx = None
    for i, r in enumerate(records):
        if r.get("cohort_id") == "literary-non-ocr" and r.get("permitted_to_proceed"):
            tampered_idx = i
            break
    assert tampered_idx is not None

    # 1. Tamper observed_records
    records_rec = copy.deepcopy(records)
    records_rec[tampered_idx]["bounded_read_metrics"]["observed_records"] += 999
    synthetic_bundle.write_index(header, records_rec)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"observed_records mismatch"):
        synthetic_bundle.verify(require_database=True)

    # 2. Tamper stream_sha256
    records_hash = copy.deepcopy(records)
    records_hash[tampered_idx]["bounded_read_metrics"]["stream_sha256"] = "0" * 64
    synthetic_bundle.write_index(header, records_hash)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"stream_sha256 mismatch"):
        synthetic_bundle.verify(require_database=True)


def test_verify_detects_unpermitted_source_in_database(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() detects when a source marked unpermitted is present in the database (Finding 1)."""
    header, records = synthetic_bundle.read_index()

    tampered_idx = None
    for i, r in enumerate(records):
        if r.get("cohort_id") == "literary-non-ocr" and r.get("permitted_to_proceed"):
            tampered_idx = i
            break
    assert tampered_idx is not None

    records[tampered_idx]["permitted_to_proceed"] = False
    records[tampered_idx]["blocking_reason"] = "manually_blocked_for_test"
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"source marked unpermitted but found in database table"):
        synthetic_bundle.verify(require_database=True)


def test_verify_detects_chunk_file_missing_for_permitted_textbook(
    synthetic_bundle: SyntheticCustodyBundle,
    tmp_path: Path,
) -> None:
    """verify() detects when a permitted textbook's chunk file is missing on host (Finding 1)."""
    empty_chunks = tmp_path / "empty_chunks"
    empty_chunks.mkdir()

    cfg = copy.deepcopy(json.loads(Path(CONFIG_PATH).read_text(encoding="utf-8")))
    cfg["inputs"]["textbook_chunks_dir"] = str(empty_chunks.resolve())
    cfg_path = tmp_path / "custom_config.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    header, records = synthetic_bundle.read_index()
    header_dict = json.loads(header)
    cfg_hash = custody.sha256_file(cfg_path)
    header_dict["config_sha256"] = cfg_hash
    synthetic_bundle.write_index(json.dumps(header_dict), records)

    receipt = synthetic_bundle.read_receipt()
    receipt["config_sha256"] = cfg_hash
    synthetic_bundle.rehash_receipt(receipt)

    with pytest.raises(
        custody.CustodyAccessError,
        match=r"(chunk file not on host, but index has status=CONFIRMED_NATIVE, permitted=True|custody status mismatch)",
    ):
        synthetic_bundle.verify(cfg_path, require_database=True)


def test_verify_detects_mismatched_custody_status_or_host_reachable(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() rejects when stored status or host_reachable contradicts independent host probe (Finding 4)."""
    header, records = synthetic_bundle.read_index()

    tampered_sid = None
    for r in records:
        if (
            r["cohort_id"] == "public-textbooks-non-stem-non-ocr"
            and not r["permitted_to_proceed"]
            and r["custody_resolution"]["status"] == "UNREACHABLE_ON_HOST"
            and tampered_sid is None
        ):
            tampered_sid = r["source_id"]
            r["custody_resolution"]["status"] = "PARTIAL_CHUNKS_AND_DB_ONLY"
            r["custody_resolution"]["host_reachable"] = True
            break

    assert tampered_sid is not None
    synthetic_bundle.write_index(header, records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"(custody status mismatch|host_reachable mismatch)"):
        synthetic_bundle.verify(require_database=True)


def test_verify_detects_index_header_tampering_and_corpus_leakage(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() strictly validates index header schema and rejects unexpected keys or leaked text (Finding 3)."""
    header, records = synthetic_bundle.read_index()
    header_dict = json.loads(header)

    # 1. Injected unexpected key ('note') into header
    header_tampered = copy.deepcopy(header_dict)
    header_tampered["note"] = "Injected header note"
    synthetic_bundle.write_index(json.dumps(header_tampered), records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"Index header keys mismatch"):
        synthetic_bundle.verify()

    # 2. Injected forbidden text into header ('text')
    header_tampered = copy.deepcopy(header_dict)
    header_tampered["text"] = "Corpus text leakage"
    synthetic_bundle.write_index(json.dumps(header_tampered), records)
    synthetic_bundle.rehash_receipt()

    with pytest.raises(custody.CustodyAccessError, match=r"(Index header keys mismatch|no_corpus_text_emitted)"):
        synthetic_bundle.verify()


def test_precompute_table_source_metrics_filters_selected_sources(tmp_path: Path) -> None:
    """_precompute_table_source_metrics restricts queries to selected_source_files (Finding 1)."""
    db_file = tmp_path / "test.db"
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE TABLE literary_texts (source_file TEXT, id INTEGER, chunk_id TEXT, text TEXT)")
    cur.execute("INSERT INTO literary_texts VALUES ('src_in', 1, 'c1', 'Hello')")
    cur.execute("INSERT INTO literary_texts VALUES ('src_in', 2, 'c2', 'World')")
    cur.execute("INSERT INTO literary_texts VALUES ('src_out', 3, 'c3', 'Secret out-of-scope text')")
    conn.commit()

    # Pass selected_source_files containing only 'src_in'
    s_m, _c_m = custody._precompute_table_source_metrics(conn, "literary_texts", selected_source_files={"src_in"})
    assert "src_in" in s_m
    assert "src_out" not in s_m
    assert s_m["src_in"][0] == 2
    assert s_m["src_in"][1] == 10

    # If selected_source_files is empty, returns empty without querying
    s_empty, c_empty = custody._precompute_table_source_metrics(conn, "literary_texts", selected_source_files=set())
    assert s_empty == {}
    assert c_empty == {}
    conn.close()


def test_verify_handles_stub_database_with_missing_tables(
    synthetic_bundle: SyntheticCustodyBundle,
) -> None:
    """verify() treats stub databases lacking required tables as unprovisioned when require_database=False,
    and raises CustodyAccessError mentioning missing tables when require_database=True.
    """
    # 1. Create stub database lacking required tables (only has esum_etymology)
    stub_dir = synthetic_bundle.in_dir / "data"
    stub_dir.mkdir(parents=True, exist_ok=True)
    stub_db = stub_dir / "sources.db"
    conn = sqlite3.connect(stub_db)
    conn.execute("DROP TABLE IF EXISTS literary_texts")
    conn.execute("DROP TABLE IF EXISTS textbooks")
    conn.execute("CREATE TABLE IF NOT EXISTS esum_etymology (id INTEGER PRIMARY KEY, word TEXT)")
    conn.commit()
    conn.close()

    # 2. When require_database=False (unprovisioned CI with stub database on disk),
    # verify() detects missing tables, leaves db_conn=None, and passes without error.
    res = custody.verify(
        CONFIG_PATH, input_root=synthetic_bundle.in_dir, output_root=synthetic_bundle.out_dir, require_database=False
    )
    assert res is True

    # 3. When require_database=True, verify() detects missing required tables and raises CustodyAccessError
    with pytest.raises(custody.CustodyAccessError, match=r"missing required tables:.*(literary_texts|textbooks)"):
        custody.verify(
            CONFIG_PATH, input_root=synthetic_bundle.in_dir, output_root=synthetic_bundle.out_dir, require_database=True
        )
