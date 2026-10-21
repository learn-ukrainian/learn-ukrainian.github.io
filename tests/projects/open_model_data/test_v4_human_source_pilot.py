"""Tests for the first private human-source dataset pilot and 1/1 proof (Issue #7430)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import scripts.projects.open_model_data.v4_human_source_pilot as pilot_mod
from scripts.projects.open_model_data.paths import resolve_open_model_path
from tests._host_path_guard import FIXTURE_HOME

MANIFEST_PATH = resolve_open_model_path("data/projects/open_model_data/pilot/v4_human_source_pilot_manifest_v1.json")
_RECEIPT = "data/projects/open_model_data/pilot/v4_human_source_pilot_receipt_v1.json"
@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl",
)
def test_pilot_reproducibility_from_frozen_code(tmp_path: Path) -> None:
    """A separate invocation must reproduce exact cryptographic digests (PILOT-4)."""
    repo = Path.cwd()
    res1 = pilot_mod.build(MANIFEST_PATH, input_root=repo, output_root=tmp_path / "first")
    res2 = pilot_mod.build(MANIFEST_PATH, input_root=repo, output_root=tmp_path / "second")
    assert res1["receipt_id"] == res2["receipt_id"]
    assert res1["records_sha256"] == res2["records_sha256"]


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl",
)
def test_verify_detects_tampered_records_or_receipt(tmp_path: Path) -> None:
    """Verification must fail if any digest is tampered."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = resolve_open_model_path(_RECEIPT)
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_records_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl")
    out_rec = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl"
    out_rec.parent.mkdir(parents=True)
    out_rec.write_text(orig_records_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["records_sha256"] = "f" * 64
    out_rcpt = resolve_open_model_path(_RECEIPT, repo=tampered_out)
    out_rcpt.parent.mkdir(parents=True, exist_ok=True)
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(pilot_mod.PilotDatasetError, match=r"Records SHA-256 mismatch"):
        pilot_mod.verify(MANIFEST_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl",
)
def test_verify_detects_prohibited_private_host_paths(tmp_path: Path) -> None:
    """Verification must fail if receipt contains forbidden private host paths."""
    repo_root = Path.cwd()
    tampered_out = tmp_path / "tampered"
    tampered_out.mkdir(parents=True)

    orig_receipt_path = resolve_open_model_path(_RECEIPT)
    orig_receipt = json.loads(orig_receipt_path.read_text(encoding="utf-8"))

    orig_records_path = Path("data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl")
    out_rec = tampered_out / "data/projects/open_model_data/pilot/v4_human_source_pilot_records_v1.jsonl"
    out_rec.parent.mkdir(parents=True)
    out_rec.write_text(orig_records_path.read_text(encoding="utf-8"), encoding="utf-8")

    tampered_rcpt = copy.deepcopy(orig_receipt)
    tampered_rcpt["notes"] = f"Emitted from {FIXTURE_HOME}/cluster"
    out_rcpt = resolve_open_model_path(_RECEIPT, repo=tampered_out)
    out_rcpt.parent.mkdir(parents=True, exist_ok=True)
    out_rcpt.write_text(json.dumps(tampered_rcpt, indent=2), encoding="utf-8")

    with pytest.raises(
        pilot_mod.PilotDatasetError, match=r"Receipt contains prohibited private or absolute host paths"
    ):
        pilot_mod.verify(MANIFEST_PATH, input_root=repo_root, output_root=tampered_out)


@pytest.mark.needs_artifact(
    "open_model_other_indexes",
    "projects/open_model_data/splits/v4_work_grouping_split_index_v1.jsonl",
)
def test_build_and_verify_clean_exit() -> None:
    """Build and verify must execute cleanly against repository artifacts."""
    res_build = pilot_mod.build(MANIFEST_PATH)
    assert res_build["verdict"] == "PILOT_DATASET_CONFIRMED"

    res_verify = pilot_mod.verify(MANIFEST_PATH)
    assert res_verify["status"] == "PASS"
    assert res_verify["verdict"] == "PILOT_DATASET_CONFIRMED"
    assert res_verify["selected_spans"] == 1419
    assert res_verify["exported_training_spans"] == 614
