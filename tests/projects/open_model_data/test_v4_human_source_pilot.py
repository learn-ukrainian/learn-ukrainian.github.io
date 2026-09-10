"""Tests for the first private human-source dataset pilot and 1/1 proof (Issue #7430)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

import scripts.projects.open_model_data.v4_human_source_pilot as pilot_mod

MANIFEST_PATH = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_manifest_v1.json")
CONTRACTS_DIR = Path("data/projects/open_model_data/contracts")


def test_schema_contracts_valid() -> None:
    """The 3 JSON schemas for pilot manifest, record, and receipt must be valid Draft 2020-12 schemas."""
    for schema_name in [
        "v4_human_source_pilot_manifest_v1.schema.json",
        "v4_human_source_pilot_record_v1.schema.json",
        "v4_human_source_pilot_receipt_v1.schema.json",
    ]:
        p = CONTRACTS_DIR / schema_name
        assert p.is_file(), f"Missing schema contract: {p}"
        schema_data = json.loads(p.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema_data)


def test_proof_1_of_1_record_fidelity_and_provenance() -> None:
    """Verify the 1/1 human-source proof record satisfies all acceptance invariants (PILOT-1)."""
    receipt_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    proof = receipt["user_visible_proof_1_of_1"]

    assert proof["builder_training_cleared"] is True
    assert proof["verbatim_preserved"] is True
    assert len(proof["span_sha256"]) == 64
    assert proof["record_id"].startswith("record.human.")
    assert proof["work_family_id"] == "work_family.literary.yuriy_andrukhovych_moskoviada"


def test_pilot_strata_denominator_and_residual_accounting() -> None:
    """Check explicit denominator accounting and residual tracking (PILOT-2 & PILOT-3)."""
    manifest_data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    strata = manifest_data["pilot_denominator"]["strata_coverage"]

    assert strata["literary_prose"] == "covered"
    assert strata["educational_textbook"] == "covered"
    assert strata["stem_technical"] == "residual_operator_excluded"
    assert strata["video_captions"] == "residual_operator_excluded"
    assert strata["ocr_scans"] == "residual_operator_excluded"

    receipt_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    acct = receipt["pilot_accounting"]

    assert acct["selected_spans"] == 1419
    assert acct["admitted_spans"] == 1418
    assert acct["exported_training_spans"] == 614
    assert acct["rejected_quarantine_spans"] == 1
    assert acct["abstained_evaluation_spans"] == 559
    assert acct["abstained_development_spans"] == 245


def test_pilot_reproducibility_from_frozen_code() -> None:
    """A separate invocation must reproduce exact cryptographic digests (PILOT-4)."""
    res1 = pilot_mod.build(MANIFEST_PATH)
    res2 = pilot_mod.build(MANIFEST_PATH)
    assert res1["receipt_id"] == res2["receipt_id"]
    assert res1["records_sha256"] == res2["records_sha256"]


def test_verify_detects_tampered_records_or_receipt(tmp_path: Path) -> None:
    """Verification must fail if any digest is tampered."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json")
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_records_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl")
    out_rec = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl"
    out_rec.parent.mkdir(parents=True)
    out_rec.write_text(orig_records_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["records_sha256"] = "f" * 64
    out_rcpt = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json"
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(pilot_mod.PilotDatasetError, match=r"Records SHA-256 mismatch"):
        pilot_mod.verify(MANIFEST_PATH, input_root=repo_root, output_root=tampered_out)


def test_verify_detects_prohibited_private_host_paths(tmp_path: Path) -> None:
    """Verification must fail if receipt contains forbidden private host paths."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json")
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_records_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl")
    out_rec = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl"
    out_rec.parent.mkdir(parents=True)
    out_rec.write_text(orig_records_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["notes"] = "Emitted from /home/ops/cluster"
    out_rcpt = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json"
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(
        pilot_mod.PilotDatasetError, match=r"Receipt contains prohibited private or absolute host paths"
    ):
        pilot_mod.verify(MANIFEST_PATH, input_root=repo_root, output_root=tampered_out)


def test_build_and_verify_clean_exit() -> None:
    """Build and verify must execute cleanly against repository artifacts."""
    res_build = pilot_mod.build(MANIFEST_PATH)
    assert res_build["verdict"] == "PILOT_DATASET_CONFIRMED"

    res_verify = pilot_mod.verify(MANIFEST_PATH)
    assert res_verify["status"] == "PASS"
    assert res_verify["verdict"] == "PILOT_DATASET_CONFIRMED"
    assert res_verify["selected_spans"] == 1419
    assert res_verify["exported_training_spans"] == 614
