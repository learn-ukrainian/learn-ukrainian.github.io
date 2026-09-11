"""Tests for the complete private human-source dataset denominator and coverage audit (Issue #7432)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.v4_human_source_dataset import (
    OPERATOR_EXCLUDED_RESIDUALS,
    _get_language_usage_masks,
    assert_no_private_host_paths,
    build_dataset,
    clear_caches,
    load_dataset_stream,
    load_partition_view,
    resolve_record_loss_masks,
    resolve_record_text,
    verify_dataset,
)

CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")
DATASET_DIR = Path("data/projects/open_model_data/dataset")
MANIFEST_PATH = DATASET_DIR / "v4_human_source_dataset_manifest_v1.json"
RECEIPT_PATH = DATASET_DIR / "v4_human_source_dataset_receipt_v1.json"
RECORDS_PATH = DATASET_DIR / "v4_human_source_dataset_records_v1.jsonl"


def test_schema_contracts_valid() -> None:
    """The 3 JSON schemas for dataset manifest, record, and receipt must be valid Draft 2020-12 schemas."""
    for schema_name in [
        "v4_human_source_dataset_manifest_v1.schema.json",
        "v4_human_source_dataset_record_v1.schema.json",
        "v4_human_source_dataset_receipt_v1.schema.json",
    ]:
        p = CONTRACTS_DIR / schema_name
        assert p.is_file(), f"Missing schema contract: {p}"
        schema_data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema_data)


def test_manifest_denominator_accounting() -> None:
    """Check explicit denominator accounting and residual tracking (SCALE-1 & SCALE-2)."""
    assert MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}"
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest_data["schema_version"] == "v4_human_source_dataset_manifest_v1"
    assert manifest_data["dataset_version"] == "v4.0.0-human-pilot-scale"

    acct = manifest_data["denominator_accounting"]
    assert acct["total_holdings_sources"] == 16
    assert acct["total_selected_sources"] == 3
    assert acct["total_work_families"] == 3
    assert acct["total_evaluated_spans"] == 1419
    assert acct["total_admitted_spans"] == 1418
    assert acct["exported_training_spans"] == 614
    assert acct["firewalled_heldout_evaluation_spans"] == 559
    assert acct["development_spans"] == 245
    assert acct["quarantined_spans"] == 1

    strata = acct["strata_coverage"]
    assert strata["literary_prose"] == "covered"
    assert strata["educational_textbook"] == "covered"
    assert strata["stem_technical"] == "residual_operator_excluded"
    assert strata["video_captions"] == "residual_operator_excluded"
    assert strata["ocr_scans"] == "residual_operator_excluded"
    assert strata["private_teaching_material"] == "residual_operator_excluded"

    assert acct["operator_excluded_residuals"] == OPERATOR_EXCLUDED_RESIDUALS


def test_dataset_receipt_and_storage_accounting() -> None:
    """Verify receipt accounting, deduplication yield, and storage limits (SCALE-4 & SCALE-5)."""
    assert RECEIPT_PATH.is_file(), f"Missing receipt: {RECEIPT_PATH}"
    receipt_data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert receipt_data["verdict"] == "DATASET_CONFIRMED"
    assert receipt_data["dataset_version"] == "v4.0.0-human-pilot-scale"

    acct = receipt_data["dataset_accounting"]
    assert acct["total_evaluated_spans"] == 1419
    assert acct["total_admitted_spans"] == 1418
    assert acct["exported_training_spans"] == 614
    assert acct["firewalled_heldout_evaluation_spans"] == 559
    assert acct["development_spans"] == 245
    assert acct["rejected_quarantine_spans"] == 1
    assert acct["silent_drops"] == 0

    dedup = receipt_data["deduplication_yield"]
    assert dedup["unique_spans_count"] == 1419
    assert dedup["duplicate_spans_count"] == 0
    assert dedup["deduplication_rate"] == 1.0

    storage = receipt_data["storage_accounting"]
    assert storage["below_2000kb_precommit_limit"] is True
    assert storage["records_byte_size"] < 2000 * 1024

    assert receipt_data["frozen_for_downstream"]["open_weight_learning_study_issue"] == 7889
    assert receipt_data["frozen_for_downstream"]["deliverable_reproduction_issue"] == 7433


def test_dataset_record_fidelity_and_invariants() -> None:
    """Verify individual records satisfy verbatim preservation and privacy invariants (SCALE-3)."""
    assert RECORDS_PATH.is_file(), f"Missing records: {RECORDS_PATH}"
    with RECORDS_PATH.open("r", encoding="utf-8") as f:
        header = json.loads(f.readline())
        assert header["schema_version"] == "v4_human_source_dataset_records_v1"
        assert header["records"] == 1419

        sample_count = 0
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            rec = json.loads(line_str)
            assert rec["schema_version"] == "v4_human_source_dataset_record_v1"
            assert rec["record_id"].startswith("record.human.")
            assert rec["source_fidelity"]["is_native_text"] is True
            assert rec["source_fidelity"]["verbatim_preserved"] is True
            assert rec["admission_evidence"]["firewall_verified"] is True
            sample_count += 1

        assert sample_count == 1419


def test_privacy_host_paths_clean() -> None:
    """Ensure zero private host paths exist in any public dataset artifact."""
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(manifest_data)

    receipt_data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert_no_private_host_paths(receipt_data)

    with pytest.raises(ValueError, match="Prohibited host path detected"):
        assert_no_private_host_paths({"bad": "/home/ops/secret"})


def test_verify_dataset_clean_pass() -> None:
    """The verify_dataset function must return True on intact artifacts."""
    assert verify_dataset(Path.cwd()) is True


def test_build_dataset_atomic_prewrite_validation_on_denominator_mismatch(tmp_path: Path) -> None:
    """Denominator discrepancy must raise ValueError before writing files, leaving targets untouched."""
    repo_root = Path.cwd()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir(parents=True)

    # Recreate input paths in fake_repo
    contracts_target = fake_repo / "data/projects/open_model_data/contracts"
    contracts_target.parent.mkdir(parents=True, exist_ok=True)
    contracts_target.symlink_to((repo_root / CONTRACTS_DIR).resolve())

    for dir_name in ["language", "extraction", "provenance", "pilot"]:
        target = fake_repo / f"data/projects/open_model_data/{dir_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to((repo_root / f"data/projects/open_model_data/{dir_name}").resolve())

    splits_dir = fake_repo / "data/projects/open_model_data/splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    (splits_dir / "v4_work_grouping_split_receipt_v1.json").symlink_to(
        (repo_root / "data/projects/open_model_data/splits/v4_work_grouping_split_receipt_v1.json").resolve()
    )

    # Create split_index with one line missing to create an intentional denominator mismatch
    src_split_index = repo_root / "data/projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl"
    lines = src_split_index.read_text(encoding="utf-8").splitlines()
    truncated_lines = [lines[0], *lines[2:]]  # drop line 1 (1 span omitted)
    (splits_dir / "v4_work_grouping_split_index_v1.jsonl").write_text(
        "\n".join(truncated_lines) + "\n", encoding="utf-8"
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content
    test_manifest_out.write_text("sentinel manifest", encoding="utf-8")
    test_records_out.write_text("sentinel records", encoding="utf-8")
    test_receipt_out.write_text("sentinel receipt", encoding="utf-8")

    with pytest.raises(ValueError, match="Evaluated spans 1418 does not match manifest 1419"):
        build_dataset(fake_repo, test_manifest_out, test_records_out, test_receipt_out)

    # Verify target files were NOT overwritten
    assert test_manifest_out.read_text(encoding="utf-8") == "sentinel manifest"
    assert test_records_out.read_text(encoding="utf-8") == "sentinel records"
    assert test_receipt_out.read_text(encoding="utf-8") == "sentinel receipt"

    # Verify no temporary files were leaked
    tmp_files = list(out_dir.glob("*.tmp*"))
    assert tmp_files == []


def test_build_dataset_transactional_rollback_on_replacement_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If an error occurs during atomic replacement, all target files roll back to previous state."""
    repo_root = Path.cwd()
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content
    test_manifest_out.write_text("sentinel manifest", encoding="utf-8")
    test_records_out.write_text("sentinel records", encoding="utf-8")
    test_receipt_out.write_text("sentinel receipt", encoding="utf-8")

    orig_replace = Path.replace

    def mock_replace(self: Path, target: Path | str) -> Path:
        target_path = Path(target)
        if target_path.name == "receipt.json" and ".tmp." in self.name:
            raise OSError("Simulated disk error during receipt replacement")
        return orig_replace(self, target)

    monkeypatch.setattr(Path, "replace", mock_replace)

    with pytest.raises(OSError, match="Simulated disk error"):
        build_dataset(repo_root, test_manifest_out, test_records_out, test_receipt_out)

    # All targets must have rolled back to sentinel contents
    assert test_manifest_out.read_text(encoding="utf-8") == "sentinel manifest"
    assert test_records_out.read_text(encoding="utf-8") == "sentinel records"
    assert test_receipt_out.read_text(encoding="utf-8") == "sentinel receipt"

    # No stray tmp or backup files remain
    assert list(out_dir.glob("*.tmp*")) == []
    assert list(out_dir.glob("*.bak*")) == []


def test_build_dataset_backup_cleanup_failure_does_not_rollback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If an error occurs while deleting backups after targets are replaced, publication succeeds and targets remain."""
    repo_root = Path.cwd()
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content
    test_manifest_out.write_text("sentinel manifest", encoding="utf-8")
    test_records_out.write_text("sentinel records", encoding="utf-8")
    test_receipt_out.write_text("sentinel receipt", encoding="utf-8")

    orig_unlink = Path.unlink

    def mock_unlink(self: Path, missing_ok: bool = False) -> None:
        if ".bak." in self.name:
            raise OSError("Simulated permission error unlinking backup")
        orig_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", mock_unlink)

    receipt_data = build_dataset(repo_root, test_manifest_out, test_records_out, test_receipt_out)
    assert receipt_data["storage_accounting"]["below_2000kb_precommit_limit"] is True
    assert receipt_data["dataset_accounting"]["total_evaluated_spans"] == 1419

    # All targets must contain the new publication, not sentinel content
    assert test_manifest_out.read_text(encoding="utf-8") != "sentinel manifest"
    assert test_records_out.read_text(encoding="utf-8") != "sentinel records"
    assert test_receipt_out.read_text(encoding="utf-8") != "sentinel receipt"


def test_authenticated_loss_mask_resolver() -> None:
    """Verify that resolve_record_loss_masks and load_dataset_stream resolve modern_view loss masks."""
    records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True))
    assert len(records) == 1419

    # Verify first record
    rec0 = records[0]
    m0 = rec0["language_views"]["modern_view"]
    assert "loss_mask_spans" in m0
    assert len(m0["loss_mask_spans"]) == m0["loss_mask_count"]
    for span in m0["loss_mask_spans"]:
        assert "start_char" in span
        assert "end_char" in span
        assert "reason" in span
        assert span["start_char"] <= span["end_char"]

    # Verify partition loading with resolved modern_view loss masks
    training_resolved = load_partition_view(RECORDS_PATH, "training", resolve_masks=True)
    assert len(training_resolved) == 614
    assert "loss_mask_spans" in training_resolved[0]["language_views"]["modern_view"]

    # Verify direct resolution on raw record dict
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()  # skip header
        raw_line = f.readline()
    rec_raw = json.loads(raw_line)
    resolved_masks = resolve_record_loss_masks(rec_raw)
    assert resolved_masks == m0["loss_mask_spans"]

    # Test error handling on missing sha or mismatched count
    with pytest.raises(ValueError, match=r"Record is missing source_fidelity\.span_sha256"):
        resolve_record_loss_masks({})

    tampered_rec = dict(rec_raw)
    tampered_rec["language_views"] = {"modern_view": {"loss_mask_count": 999999}}
    with pytest.raises(ValueError, match=r"does not match record loss_mask_count"):
        resolve_record_loss_masks(tampered_rec)


def _has_full_sources_db() -> bool:
    candidates = [Path("data/sources.db"), Path.cwd() / "data/sources.db"]
    for p in [Path.cwd(), *Path.cwd().parents]:
        candidates.append(p / "data/sources.db")
    for cand in candidates:
        if cand.is_file():
            try:
                conn = sqlite3.connect(f"file:{cand.resolve()}?mode=ro", uri=True)
                cur = conn.cursor()
                cur.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('literary_texts', 'textbooks')"
                )
                tables = {row[0] for row in cur.fetchall()}
                conn.close()
                if "literary_texts" in tables and "textbooks" in tables:
                    return True
            except Exception:
                pass
    return False


def test_authenticated_source_text_resolver() -> None:
    """Verify that resolve_record_text and load_dataset_stream resolve private source text."""
    if not _has_full_sources_db():
        pytest.skip("Full data/sources.db with literary_texts/textbooks not available in test runner environment")

    records = list(load_dataset_stream(RECORDS_PATH, resolve_masks=True, resolve_text=True))
    assert len(records) == 1419

    rec0 = records[0]
    assert "text" in rec0
    assert "text" in rec0["source_fidelity"]
    assert len(rec0["text"]) == rec0["source_fidelity"]["char_length"]
    assert hashlib.sha256(rec0["text"].encode("utf-8")).hexdigest() == rec0["source_fidelity"]["span_sha256"]

    # Verify direct resolution
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()
        raw_line = f.readline()
    rec_raw = json.loads(raw_line)
    resolved_text = resolve_record_text(rec_raw)
    assert resolved_text == rec0["text"]

    # Test error handling on missing sha or tampered sha
    with pytest.raises(ValueError, match=r"Record is missing source_fidelity\.span_sha256"):
        resolve_record_text({})

    tampered_rec = dict(rec_raw)
    tampered_rec["source_fidelity"] = dict(rec_raw["source_fidelity"])
    tampered_rec["source_fidelity"]["span_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"
    with pytest.raises(KeyError, match=r"not found in authenticated extraction index"):
        resolve_record_text(tampered_rec)


def test_mock_authenticated_source_text_resolver(tmp_path: Path) -> None:
    """Verify text resolution in an isolated mock environment (runs in CI without full sources.db)."""
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()

    # 1. Create mock sqlite DB
    mock_db = tmp_path / "mock_sources.db"
    conn = sqlite3.connect(str(mock_db))
    cur = conn.cursor()
    cur.execute("CREATE TABLE literary_texts (source_file TEXT, chunk_id INTEGER, text TEXT)")
    cur.execute("CREATE TABLE textbooks (source_file TEXT, chunk_id INTEGER, text TEXT)")
    sample_text = "Тестовий український текст для перевірки динамічного завантаження."
    sample_sha = hashlib.sha256(sample_text.encode("utf-8")).hexdigest()
    sample_len = len(sample_text)
    cur.execute(
        "INSERT INTO literary_texts (source_file, chunk_id, text) VALUES (?, ?, ?)",
        ("lit_sample.txt", 42, sample_text),
    )
    conn.commit()
    conn.close()

    # 2. Create mock extraction index
    ext_dir = fake_repo / "data/projects/open_model_data/extraction"
    ext_dir.mkdir(parents=True)
    ext_file = ext_dir / "v4_native_extraction_index_v1.jsonl"
    ext_entry = {
        "extraction_id": "ext.test.1",
        "source_file": "lit_sample.txt",
        "chunk_id": 42,
        "source_family": "literary",
        "span_locator": {"span_sha256": sample_sha},
    }
    ext_file.write_text("# header\n" + json.dumps(ext_entry) + "\n", encoding="utf-8")

    # 3. Create mock record
    mock_rec = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test_mock_1",
        "source_id": "source.literary.test",
        "source_fidelity": {
            "char_length": sample_len,
            "span_sha256": sample_sha,
            "is_native_text": True,
            "verbatim_preserved": True,
        },
    }

    # Direct resolution with injected sources_db_path
    resolved = resolve_record_text(mock_rec, repo_root=fake_repo, sources_db_path=mock_db)
    assert resolved == sample_text

    # Stream loader with mock record file
    rec_file = tmp_path / "mock_records.jsonl"
    rec_file.write_text("# header\n" + json.dumps(mock_rec) + "\n", encoding="utf-8")
    records = list(load_dataset_stream(rec_file, resolve_text=True, repo_root=fake_repo, sources_db_path=mock_db))
    assert len(records) == 1
    assert records[0]["text"] == sample_text
    assert records[0]["source_fidelity"]["text"] == sample_text

    # Tampered database text detected via SHA mismatch
    cur2 = sqlite3.connect(str(mock_db))
    cur2.execute("UPDATE literary_texts SET text = ? WHERE chunk_id = ?", ("Невідповідний текст", 42))
    cur2.commit()
    cur2.close()
    clear_caches()
    with pytest.raises(ValueError, match=r"does not match expected"):
        resolve_record_text(mock_rec, repo_root=fake_repo, sources_db_path=mock_db)


def test_cache_refresh_on_content_change(tmp_path: Path) -> None:
    """Verify that language usage masks cache reloads when index file changes (Finding 2)."""
    fake_repo = tmp_path / "fake_repo"
    lang_dir = fake_repo / "data/projects/open_model_data/language"
    lang_dir.mkdir(parents=True)
    lang_file = lang_dir / "v4_language_usage_index_v1.jsonl"

    item1 = {
        "language_usage_id": "lu.1",
        "span_locator": {"span_sha256": "aaaa" * 16},
        "consumer_views": {"modern_view": {"loss_mask_spans": [{"start_char": 0, "end_char": 5, "reason": "dialect"}]}},
    }
    lang_file.write_text("# header\n" + json.dumps(item1) + "\n", encoding="utf-8")
    clear_caches()

    masks1 = _get_language_usage_masks(fake_repo)
    assert "aaaa" * 16 in masks1
    assert len(masks1["aaaa" * 16]) == 1

    # Modify file by adding second entry
    item2 = {
        "language_usage_id": "lu.2",
        "span_locator": {"span_sha256": "bbbb" * 16},
        "consumer_views": {"modern_view": {"loss_mask_spans": [{"start_char": 2, "end_char": 8, "reason": "archaic"}]}},
    }
    lang_file.write_text("# header\n" + json.dumps(item1) + "\n" + json.dumps(item2) + "\n", encoding="utf-8")

    # Without calling clear_caches, the digest-keyed cache must automatically pick up the new content
    masks2 = _get_language_usage_masks(fake_repo)
    assert "bbbb" * 16 in masks2
    assert len(masks2["bbbb" * 16]) == 1


def test_retains_backups_when_rollback_cannot_restore(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that when rollback fails during publication error recovery, surviving backups are retained (Finding 4)."""

    repo_root = Path.cwd()
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir(parents=True)

    # Recreate input paths in fake_repo
    contracts_target = fake_repo / "data/projects/open_model_data/contracts"
    contracts_target.parent.mkdir(parents=True, exist_ok=True)
    contracts_target.symlink_to((repo_root / CONTRACTS_DIR).resolve())

    for dir_name in ["language", "extraction", "provenance", "pilot", "splits"]:
        target = fake_repo / f"data/projects/open_model_data/{dir_name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to((repo_root / f"data/projects/open_model_data/{dir_name}").resolve())

    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    test_manifest_out = out_dir / "manifest.json"
    test_records_out = out_dir / "records.jsonl"
    test_receipt_out = out_dir / "receipt.json"

    # Pre-populate sentinel content that will be backed up
    test_manifest_out.write_text("original manifest", encoding="utf-8")
    test_records_out.write_text("original records", encoding="utf-8")
    test_receipt_out.write_text("original receipt", encoding="utf-8")

    original_replace = Path.replace

    # Inject failure during target publication (step 2) and failure during rollback
    def failing_replace(self: Path, target: Path | str) -> Path:
        target_path = Path(target)
        # If moving staged receipt_tmp to test_receipt_out, raise error to trigger rollback
        if target_path == test_receipt_out:
            raise OSError("Simulated disk error moving receipt")
        # If during rollback, restoring manifest bak fails, raise error
        if ".bak." in str(self) and target_path == test_manifest_out:
            raise OSError("Simulated rollback error restoring manifest")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_replace)

    with pytest.raises(RuntimeError, match=r"Rollback failed during publish recovery"):
        build_dataset(fake_repo, test_manifest_out, test_records_out, test_receipt_out)

    # Verify that the un-restored backup file was NOT deleted in finally
    bak_files = list(out_dir.glob("*.bak.*"))
    assert len(bak_files) > 0, "Surviving backups must be retained when rollback fails"


def test_verify_dataset_rejects_duplicate_record_id_or_span_sha(tmp_path: Path) -> None:
    """Verify that verify_dataset rejects duplicate record IDs or duplicate span hashes (Finding 3)."""
    with open(RECORDS_PATH, encoding="utf-8") as f:
        header = f.readline()
        lines = [f.readline() for _ in range(1419)]

    # 1. Duplicate record_id
    rec1 = json.loads(lines[0])
    rec2 = json.loads(lines[1])
    rec2_dup_id = dict(rec2)
    rec2_dup_id["record_id"] = rec1["record_id"]

    dup_id_file = tmp_path / "dup_id_records.jsonl"
    dup_id_file.write_text(header + lines[0] + json.dumps(rec2_dup_id) + "\n" + "".join(lines[2:]), encoding="utf-8")
    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(
                dup_id_file.relative_to(Path.cwd()) if dup_id_file.is_relative_to(Path.cwd()) else dup_id_file
            ),
        )
        is False
    )

    # 2. Duplicate span_sha256
    rec2_dup_sha = dict(rec2)
    rec2_dup_sha["source_fidelity"] = dict(rec2["source_fidelity"])
    rec2_dup_sha["source_fidelity"]["span_sha256"] = rec1["source_fidelity"]["span_sha256"]
    dup_sha_file = tmp_path / "dup_sha_records.jsonl"
    dup_sha_file.write_text(header + lines[0] + json.dumps(rec2_dup_sha) + "\n" + "".join(lines[2:]), encoding="utf-8")
    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(
                dup_sha_file.relative_to(Path.cwd()) if dup_sha_file.is_relative_to(Path.cwd()) else dup_sha_file
            ),
        )
        is False
    )


def test_verify_dataset_rejects_schema_violating_record(tmp_path: Path) -> None:
    """Verify that verify_dataset rejects records violating schema contract e.g. firewall_verified=False (Finding 1)."""
    with open(RECORDS_PATH, encoding="utf-8") as f:
        header = f.readline()
        lines = [f.readline() for _ in range(1419)]

    rec1 = json.loads(lines[0])
    rec1_bad = dict(rec1)
    rec1_bad["admission_evidence"] = dict(rec1["admission_evidence"])
    rec1_bad["admission_evidence"]["firewall_verified"] = False  # Schema const: true

    bad_rec_file = tmp_path / "bad_schema_records.jsonl"
    bad_rec_file.write_text(header + json.dumps(rec1_bad) + "\n" + "".join(lines[1:]), encoding="utf-8")
    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(
                bad_rec_file.relative_to(Path.cwd()) if bad_rec_file.is_relative_to(Path.cwd()) else bad_rec_file
            ),
        )
        is False
    )


def test_verify_dataset_rejects_tampered_non_first_record_mask(tmp_path: Path) -> None:
    """Verify that verify_dataset rejects when a non-first record has an invalid loss mask (Finding 2)."""
    with open(RECORDS_PATH, encoding="utf-8") as f:
        header = f.readline()
        lines = [f.readline() for _ in range(1419)]

    # Tamper with record 50's loss_mask_count so loader or mask resolver fails
    rec50 = json.loads(lines[50])
    rec50_bad = dict(rec50)
    rec50_bad["language_views"] = dict(rec50["language_views"])
    rec50_bad["language_views"]["modern_view"] = dict(rec50["language_views"]["modern_view"])
    rec50_bad["language_views"]["modern_view"]["loss_mask_count"] = 999999

    bad_file = tmp_path / "bad_rec50_records.jsonl"
    bad_file.write_text(
        header + "".join(lines[:50]) + json.dumps(rec50_bad) + "\n" + "".join(lines[51:]), encoding="utf-8"
    )
    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(bad_file.relative_to(Path.cwd()) if bad_file.is_relative_to(Path.cwd()) else bad_file),
        )
        is False
    )


def test_validate_mask_span_schema_and_interval_bounds() -> None:
    """Verify that validate_mask_span rejects missing required fields and invalid interval bounds."""
    from scripts.projects.open_model_data.v4_human_source_dataset import validate_mask_span

    # Valid mask span
    valid_span = {"start_char": 10, "end_char": 25, "reason": "historical_period"}
    assert validate_mask_span(valid_span, char_len=50) is True

    # Reject empty dict
    assert validate_mask_span({}, char_len=50) is False

    # Reject missing reason
    assert validate_mask_span({"start_char": 10, "end_char": 25}, char_len=50) is False
    assert validate_mask_span({"start_char": 10, "end_char": 25, "reason": ""}, char_len=50) is False

    # Reject missing start_char or end_char
    assert validate_mask_span({"end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": 10, "reason": "historical_period"}, char_len=50) is False

    # Reject non-integer or boolean coordinates
    assert validate_mask_span({"start_char": True, "end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": "10", "end_char": 25, "reason": "historical_period"}, char_len=50) is False
    assert validate_mask_span({"start_char": -1, "end_char": 25, "reason": "historical_period"}, char_len=50) is False

    # Reject inverted interval (start > end)
    assert validate_mask_span({"start_char": 30, "end_char": 20, "reason": "historical_period"}, char_len=50) is False

    # Reject end_char exceeding record char_length
    assert validate_mask_span({"start_char": 10, "end_char": 60, "reason": "historical_period"}, char_len=50) is False

    # Reject unexpected extra fields (additionalProperties: False)
    assert (
        validate_mask_span(
            {"start_char": 10, "end_char": 25, "reason": "historical_period", "extra": "field"},
            char_len=50,
        )
        is False
    )


def test_persisted_records_reject_preexisting_raw_text(tmp_path: Path) -> None:
    """Ensure load_dataset_stream and verify_dataset reject persisted records containing raw text."""
    bad_records_file = tmp_path / "bad_records.jsonl"
    bad_record = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test12345678901234",
        "source_id": "source.literary.test",
        "text": "Private corpus text directly serialized",
    }
    bad_records_file.write_text("# header\n" + json.dumps(bad_record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="contains raw text"):
        next(load_dataset_stream(bad_records_file, resolve_masks=False, resolve_text=False))

    bad_record2 = {
        "schema_version": "v4_human_source_dataset_record_v1",
        "record_id": "record.human.test12345678901235",
        "source_fidelity": {"text": "Private text in fidelity"},
    }
    bad_records_file.write_text("# header\n" + json.dumps(bad_record2) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="contains raw text"):
        next(load_dataset_stream(bad_records_file, resolve_masks=False, resolve_text=False))


def test_record_schema_forbids_raw_text() -> None:
    """Ensure v4_human_source_dataset_record_v1 schema rejects raw text property."""
    import jsonschema

    schema_path = CONTRACTS_DIR / "v4_human_source_dataset_record_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Valid base record without text
    with open(RECORDS_PATH, encoding="utf-8") as f:
        _ = f.readline()
        record = json.loads(f.readline())

    jsonschema.validate(instance=record, schema=schema)

    # Adding raw text at root must fail schema validation
    rec_with_text = dict(record)
    rec_with_text["text"] = "Sample corpus text"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=rec_with_text, schema=schema)

    # Adding raw text under source_fidelity must fail schema validation
    rec_with_fidelity_text = dict(record)
    rec_with_fidelity_text["source_fidelity"] = dict(record["source_fidelity"])
    rec_with_fidelity_text["source_fidelity"]["text"] = "Sample corpus text"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=rec_with_fidelity_text, schema=schema)


def test_verify_dataset_rejects_tampered_or_missing_records_header(tmp_path: Path) -> None:
    """Verify that verify_dataset rejects records with invalid, missing, or mismatched header even with matching SHA."""
    from scripts.projects.open_model_data.v4_human_source_dataset import sha256_file

    with open(RECORDS_PATH, encoding="utf-8") as f:
        header_line = f.readline()
        header = json.loads(header_line)
        lines = [f.readline() for _ in range(1419)]

    # 1. Tampered records count in header
    bad_header1 = dict(header)
    bad_header1["records"] = 100
    bad_file1 = tmp_path / "bad_count_records.jsonl"
    bad_file1.write_text(json.dumps(bad_header1) + "\n" + "".join(lines), encoding="utf-8")

    receipt_data = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    receipt_data["records_sha256"] = sha256_file(bad_file1)
    fake_rcpt1 = tmp_path / "fake_receipt1.json"
    fake_rcpt1.write_text(json.dumps(receipt_data), encoding="utf-8")

    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(bad_file1.relative_to(Path.cwd()) if bad_file1.is_relative_to(Path.cwd()) else bad_file1),
            receipt_rel=str(
                fake_rcpt1.relative_to(Path.cwd()) if fake_rcpt1.is_relative_to(Path.cwd()) else fake_rcpt1
            ),
        )
        is False
    )

    # 2. Tampered manifest_sha256 in header
    bad_header2 = dict(header)
    bad_header2["manifest_sha256"] = "0" * 64
    bad_file2 = tmp_path / "bad_manifest_records.jsonl"
    bad_file2.write_text(json.dumps(bad_header2) + "\n" + "".join(lines), encoding="utf-8")

    receipt_data["records_sha256"] = sha256_file(bad_file2)
    fake_rcpt2 = tmp_path / "fake_receipt2.json"
    fake_rcpt2.write_text(json.dumps(receipt_data), encoding="utf-8")

    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(bad_file2.relative_to(Path.cwd()) if bad_file2.is_relative_to(Path.cwd()) else bad_file2),
            receipt_rel=str(
                fake_rcpt2.relative_to(Path.cwd()) if fake_rcpt2.is_relative_to(Path.cwd()) else fake_rcpt2
            ),
        )
        is False
    )

    # 3. Missing header (first line is a data record)
    bad_file3 = tmp_path / "missing_header_records.jsonl"
    bad_file3.write_text("".join(lines), encoding="utf-8")

    receipt_data["records_sha256"] = sha256_file(bad_file3)
    fake_rcpt3 = tmp_path / "fake_receipt3.json"
    fake_rcpt3.write_text(json.dumps(receipt_data), encoding="utf-8")

    assert (
        verify_dataset(
            Path.cwd(),
            records_rel=str(bad_file3.relative_to(Path.cwd()) if bad_file3.is_relative_to(Path.cwd()) else bad_file3),
            receipt_rel=str(
                fake_rcpt3.relative_to(Path.cwd()) if fake_rcpt3.is_relative_to(Path.cwd()) else fake_rcpt3
            ),
        )
        is False
    )
