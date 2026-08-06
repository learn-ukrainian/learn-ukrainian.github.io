"""Hermetic integrity tests for the Phase 3 source-universe freeze verifier."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.projects.open_model_data import verify_phase3_source_universe_freeze as verifier


def _token(value: str) -> str:
    return value * 64


def _write_json(path: Path, value: object) -> None:
    path.write_text(verifier.canonical_json(value) + "\n", encoding="utf-8")


def _script_binding() -> tuple[str, str]:
    merged_main_sha = subprocess.run(
        ["git", "-C", str(verifier.ROOT), "rev-parse", "origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    script = subprocess.run(
        [
            "git", "-C", str(verifier.ROOT), "show",
            f"{merged_main_sha}:scripts/projects/open_model_data/phase3_source_universe.py",
        ],
        check=True,
        capture_output=True,
    ).stdout
    return merged_main_sha, verifier.sha256_bytes(script)


def _record(family_id: str, ordinal: int = 1) -> dict[str, Any]:
    record: dict[str, Any] = {
        "family_id": family_id,
        "unit_id": f"unit.{family_id}.{_token('1')}",
        "unit_sha256": _token("2"),
        "ordinal": ordinal,
        "duplicate_group_id": f"duplicate.{family_id}.{_token('3')}",
        "parse_status": "parsed",
        "rights": {
            "source_text_committed": False,
            "locator_only_allowed": True,
            "rights_limited_disposition": "rights_limited_locator_only",
        },
        "provenance": {"input_sha256": _token("4"), "unit_grain": "fixture_unit"},
    }
    if family_id == "calque_inventory":
        record["locator"] = {"kind": "python_mapping_entry", "collection": "fixture", "entry_id_sha256": _token("5")}
    elif family_id.startswith("pravopys_"):
        record["parse_status"] = "numbered_hierarchy_parsed"
        record["normalized_text_sha256"] = _token("6")
        record["locator"] = {
            "kind": "pdf_numbered_hierarchy", "edition_sha256": _token("7"),
            "page": 1, "line": 1, "end_page": 1, "end_line": 1,
            "section_path": ["paragraph:1"],
        }
    else:
        record["locator"] = {
            "kind": "sqlite_row", "table": "fixture", "primary_key_fields": ["id"],
            "primary_key_sha256": _token("8"),
        }
    return record


def _lexical_summary(family_id: str) -> dict[str, Any]:
    provenance = {"input_sha256": _token("9"), "unit_grain": "fixture_lexical"}
    binding = {
        "unit_id": f"unit.{family_id}.{_token('a')}",
        "unit_sha256": _token("b"),
        "duplicate_group_id": f"duplicate.{family_id}.{_token('c')}",
        "parse_status": "parsed",
        "provenance": provenance,
    }
    encoded = verifier.canonical_json(binding).encode("utf-8")
    rolling = verifier.sha256_bytes(len(encoded).to_bytes(8, "big") + encoded)
    return {
        "family_id": family_id,
        "unit_count": 1,
        "ordered_rolling_sha256": rolling,
        "parse_status_counts": {"parsed": 1},
        "binding_fields": verifier.BINDING_FIELDS,
        "provenance": provenance,
    }


def _manifest(receipt: dict[str, Any], evidence_dir: Path) -> None:
    payloads = []
    for name in sorted(verifier.PAYLOAD_FILES):
        path = evidence_dir / name
        payloads.append({"path": name, "sha256": verifier.sha256_file(path), "byte_count": path.stat().st_size})
    receipt["artifact_manifest"] = {
        "artifact_count": 10,
        "payload_file_count": 9,
        "payloads": payloads,
        "payload_manifest_sha256": verifier.sha256_bytes(verifier.canonical_json(payloads).encode("utf-8")),
        "receipt_file": verifier.RECEIPT_FILE,
    }


def _write_receipt(receipt: dict[str, Any], evidence_dir: Path) -> None:
    _write_json(evidence_dir / verifier.RECEIPT_FILE, receipt)


def _refresh_payload(receipt: dict[str, Any], evidence_dir: Path, name: str) -> None:
    item = next(item for item in receipt["artifact_manifest"]["payloads"] if item["path"] == name)
    path = evidence_dir / name
    item["sha256"] = verifier.sha256_file(path)
    item["byte_count"] = path.stat().st_size
    payloads = receipt["artifact_manifest"]["payloads"]
    receipt["artifact_manifest"]["payload_manifest_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json(payloads).encode("utf-8")
    )


def _evidence(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    evidence_dir = tmp_path / "source_universe_v1"
    evidence_dir.mkdir(parents=True)
    families: list[dict[str, Any]] = []
    for family_id in sorted(verifier.LEDGER_FAMILIES):
        name = f"{family_id}.units.jsonl"
        path = evidence_dir / name
        path.write_text(verifier.canonical_json(_record(family_id)) + "\n", encoding="utf-8")
        families.append({
            "family_id": family_id, "unit_count": 1,
            "ledger_sha256": verifier.sha256_file(path), "ledger_file": name,
        })
    summaries = [_lexical_summary(family_id) for family_id in sorted(verifier.LEXICAL_FAMILIES)]
    _write_json(evidence_dir / verifier.STRUCTURAL_FILE, {
        "schema_version": "lexical_structural_freeze_v1", "text_free": True, "families": summaries,
    })
    structural_hash = verifier.sha256_file(evidence_dir / verifier.STRUCTURAL_FILE)
    families.extend({
        "family_id": summary["family_id"], "unit_count": summary["unit_count"],
        "structural_receipt_file": verifier.STRUCTURAL_FILE,
        "structural_receipt_sha256": structural_hash,
        "structural_universe_sha256": summary["ordered_rolling_sha256"],
    } for summary in summaries)
    merged_main_sha, script_sha256 = _script_binding()
    receipt: dict[str, Any] = {
        "schema_version": "phase3_source_universe_freeze_v1",
        "text_free": True,
        "merged_main_sha": merged_main_sha,
        "freezer": {
            "implementation_version": "phase3_source_universe_freezer_v2",
            "script_path": "scripts/projects/open_model_data/phase3_source_universe.py",
            "script_sha256": script_sha256,
        },
        "coverage_contract_sha256": _token("d"),
        "input_sha256": {
            "sources_db": _token("e"), "vesum_db": _token("f"), "calque_module": _token("0"),
            "r2u_cache": _token("1"), "pravopys_2019_pdf": _token("2"), "pravopys_2026_pdf": _token("3"),
        },
        "pdf_editions": {
            "pravopys_2019_complete": {
                "edition_identity": "pravopys_2019_complete", "input_sha256": _token("2"),
                "official_download_locator": "https://example.invalid/2019.pdf",
                "retrieval_locator": "https://example.invalid/2019-retrieval.pdf",
                "retrieved_at": "2026-01-01T00:00:00Z", "page_count_extracted": 1,
                "stable_grain": "pdf_numbered_hierarchy", "paragraph_count": 1,
                "source_text_committed": False, "rights_provenance_classification": "rights_limited_locator_only",
            },
            "pravopys_2026_complete": {
                "edition_identity": "pravopys_2026_complete", "input_sha256": _token("3"),
                "official_decision_locator": "https://example.invalid/decision",
                "official_download_locator": "https://example.invalid/2026.pdf",
                "retrieval_locator": "https://example.invalid/2026-retrieval.pdf",
                "retrieved_at": "2026-01-01T00:00:00Z", "page_count_extracted": 1,
                "stable_grain": "pdf_numbered_hierarchy", "paragraph_count": 1,
                "source_text_committed": False, "rights_provenance_classification": "rights_limited_locator_only",
            },
        },
        "other_normative_style_inventory": {
            "candidate_tables": [], "additional_family_count": 0, "zero_additional_family_inventory": True,
        },
        "families": families,
        "status": "SOURCE_UNIVERSE_FROZEN_NOT_COVERAGE_READY",
        "blocking_requirements": [
            "source_unit_dispositions_and_dual_population_audits", "textbook_nonhit_audit",
            "pravopys_2019_2026_delta_coverage_and_audit", "lexical_used_subset_census",
        ],
    }
    _manifest(receipt, evidence_dir)
    _write_receipt(receipt, evidence_dir)
    return evidence_dir, receipt


def _validate(evidence_dir: Path) -> dict[str, Any]:
    return verifier.validate(evidence_dir, repo_root=verifier.ROOT)


def test_valid_freeze_reports_integrity_only(tmp_path: Path) -> None:
    evidence_dir, _ = _evidence(tmp_path)

    result = _validate(evidence_dir)

    assert result["integrity_verified"] is True
    assert "status" not in result


def test_committed_freeze_integrity() -> None:
    result = verifier.validate(verifier.DEFAULT_EVIDENCE_DIR, repo_root=verifier.ROOT)

    assert result == {
        "ok": True,
        "integrity_verified": True,
        "artifact_count": 10,
        "family_count": 21,
        "merged_main_sha": "ffaea4e2dde08e29ab78a9acc1063ab63ccd4a5f",
    }


def test_valid_freeze_accepts_empty_ledger(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    path = evidence_dir / "other_normative_style_inventory.units.jsonl"
    path.write_text("", encoding="utf-8")
    ledger = next(
        item for item in receipt["families"]
        if item["family_id"] == "other_normative_style_inventory"
    )
    ledger["unit_count"] = 0
    ledger["ledger_sha256"] = verifier.sha256_file(path)
    _refresh_payload(receipt, evidence_dir, path.name)
    _write_receipt(receipt, evidence_dir)

    assert _validate(evidence_dir)["integrity_verified"] is True


@pytest.mark.parametrize("mutation", ["extra", "missing", "symlink", "nested"])
def test_rejects_exact_file_set_violations(tmp_path: Path, mutation: str) -> None:
    evidence_dir, _ = _evidence(tmp_path)
    if mutation == "extra":
        (evidence_dir / "extra.json").write_text("{}\n", encoding="utf-8")
    elif mutation == "missing":
        (evidence_dir / "ua_gec.units.jsonl").unlink()
    elif mutation == "symlink":
        target = tmp_path / "target.jsonl"
        target.write_text("{}\n", encoding="utf-8")
        (evidence_dir / "ua_gec.units.jsonl").unlink()
        (evidence_dir / "ua_gec.units.jsonl").symlink_to(target)
    else:
        (evidence_dir / "nested").mkdir()

    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)


@pytest.mark.parametrize("field, value", [("sha256", _token("f")), ("byte_count", 999)])
def test_rejects_payload_hash_and_byte_count_mutations(tmp_path: Path, field: str, value: object) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    receipt["artifact_manifest"]["payloads"][0][field] = value
    payloads = receipt["artifact_manifest"]["payloads"]
    receipt["artifact_manifest"]["payload_manifest_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json(payloads).encode("utf-8")
    )
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)


def test_rejects_ledger_line_count_and_duplicate_family(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    ledger = next(item for item in receipt["families"] if item["family_id"] == "ua_gec")
    ledger["unit_count"] = 2
    _write_receipt(receipt, evidence_dir)
    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)

    evidence_dir, receipt = _evidence(tmp_path / "duplicate")
    receipt["families"][1]["family_id"] = receipt["families"][0]["family_id"]
    _write_receipt(receipt, evidence_dir)
    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)


def test_rejects_source_bearing_unexpected_record_field(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    path = evidence_dir / "ua_gec.units.jsonl"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["source_text"] = "forbidden"
    path.write_text(verifier.canonical_json(record) + "\n", encoding="utf-8")
    ledger = next(item for item in receipt["families"] if item["family_id"] == "ua_gec")
    ledger["ledger_sha256"] = verifier.sha256_file(path)
    _refresh_payload(receipt, evidence_dir, path.name)
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError, match="unexpected record shape"):
        _validate(evidence_dir)


def test_rejects_inverted_pdf_locator_range(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    path = evidence_dir / "pravopys_2026_complete.units.jsonl"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["locator"].update({"page": 5, "line": 2, "end_page": 4, "end_line": 9})
    path.write_text(verifier.canonical_json(record) + "\n", encoding="utf-8")
    ledger = next(
        item for item in receipt["families"]
        if item["family_id"] == "pravopys_2026_complete"
    )
    ledger["ledger_sha256"] = verifier.sha256_file(path)
    _refresh_payload(receipt, evidence_dir, path.name)
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError, match="inverted PDF locator bounds"):
        _validate(evidence_dir)


def test_rejects_wrong_receipt_family_shape(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    ledger = next(item for item in receipt["families"] if item["family_id"] == "ua_gec")
    ledger["unexpected"] = True
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)


def test_rejects_structural_summary_mismatch(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    path = evidence_dir / verifier.STRUCTURAL_FILE
    structural = json.loads(path.read_text(encoding="utf-8"))
    structural["families"][0]["unit_count"] = 2
    structural["families"][0]["parse_status_counts"] = {"parsed": 2}
    _write_json(path, structural)
    structural_hash = verifier.sha256_file(path)
    for family in receipt["families"]:
        if family["family_id"] in verifier.LEXICAL_FAMILIES:
            family["structural_receipt_sha256"] = structural_hash
    _refresh_payload(receipt, evidence_dir, path.name)
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError, match="structural unit count mismatch"):
        _validate(evidence_dir)


@pytest.mark.parametrize("sha", ["F" * 40, "0" * 40])
def test_rejects_malformed_and_nonancestor_merged_sha(tmp_path: Path, sha: str) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    receipt["merged_main_sha"] = sha
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError):
        _validate(evidence_dir)


def test_rejects_freezer_script_hash_mismatch(tmp_path: Path) -> None:
    evidence_dir, receipt = _evidence(tmp_path)
    receipt["freezer"]["script_sha256"] = _token("f")
    _write_receipt(receipt, evidence_dir)

    with pytest.raises(verifier.IntegrityError, match="freezer script hash mismatch"):
        _validate(evidence_dir)
