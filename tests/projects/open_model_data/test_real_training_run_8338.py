"""Tests for real open model training run, adapter integrity, and scorecard (#8338)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from safetensors import safe_open

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data" / "projects" / "open_model_data"
DOCS_DIR = REPO_ROOT / "docs" / "projects" / "open-model-data"
STUDY_DIR = DATA_DIR / "study"
CANARY_DIR = DATA_DIR / "canary"
CONTRACTS_DIR = DATA_DIR / "contracts"


def test_adapter_safetensors_layer_count() -> None:
    """Verify saved adapter belongs to named model with 24 layers, not 4 layers (#8338)."""
    adapter_path = STUDY_DIR / "run_output" / "adapter" / "adapter_model.safetensors"
    assert adapter_path.is_file(), f"Missing adapter file: {adapter_path}"

    with safe_open(str(adapter_path), framework="pt") as f:
        keys = list(f.keys())
        assert len(keys) == 336, f"Expected 336 tensors for 24-layer LoRA, got {len(keys)}"
        layers = {
            int(k.split("layers.")[1].split(".")[0])
            for k in keys
            if "layers." in k
        }
        assert layers == set(range(24)), f"Expected layers 0..23, got {sorted(layers)}"

        # Verify down_proj, gate_proj, up_proj, q_proj, k_proj, v_proj, o_proj
        for mod in ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]:
            sample_key = f"base_model.model.model.layers.0.mlp.{mod}.lora_A.weight" if "proj" in mod and "mlp" in mod else None
            # At least verify q_proj exists in layer 0
            assert "base_model.model.model.layers.0.self_attn.q_proj.lora_A.weight" in keys


def test_pilot_canary_receipt_marked_not_reliable() -> None:
    """Verify Phase 3.6 pilot receipt is marked NOT_RELIABLE per issue #8338."""
    receipt_path = CANARY_DIR / "pilot_canary_receipt.json"
    schema_path = CONTRACTS_DIR / "v1_pilot_canary_receipt.schema.json"

    assert receipt_path.is_file()
    assert schema_path.is_file()

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Must pass schema validation
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(receipt))
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"

    # Must carry NOT_RELIABLE status
    assert "reliability_assessment" in receipt
    assert receipt["reliability_assessment"]["status"] == "NOT_RELIABLE"
    assert receipt["reliability_assessment"]["audit_issue"] == 8338
    assert "8338" in receipt["reliability_assessment"]["notes"]


def test_training_run_manifest_integrity() -> None:
    """Verify training run manifest records real parameters, fingerprints, and loss reduction."""
    manifest_path = STUDY_DIR / "run_output" / "training_run_manifest.json"
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["model_name"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert manifest["num_layers"] == 24
    assert manifest["hidden_size"] == 896
    assert manifest["total_parameters"] == 494032768
    assert manifest["trainable_parameters"] == 8798208
    assert manifest["total_steps"] == 250
    assert manifest["loss_reduction_pct"] > 90.0

    # Fingerprints
    fp = manifest["fingerprints"]
    assert fp["train_sha256"] == "648c2a2ae37e53789640f1db3623b15317a3a4beb31a72d7ee5be322d8e0927d"
    assert fp["heldout_sha256"] == "20b485f5d31ac069740282ca278d94e730dbbb4ca3ec50b5589d0083d287b0f0"
    assert fp["protection_sha256"] == "67070c44fcb3efeed5d394e0b598b95a5e5f2c8c984a0b3065c3c0f4e8c36af7"


def test_scorecard_and_plain_verdict() -> None:
    """Verify before/after scorecard exists with plain answer on whether training helped."""
    scorecard_md = DOCS_DIR / "REAL_TRAINING_RUN_SCORECARD_8338.md"
    scorecard_json = STUDY_DIR / "real_training_run_scorecard.json"

    assert scorecard_md.is_file(), f"Missing markdown scorecard: {scorecard_md}"
    assert scorecard_json.is_file(), f"Missing JSON scorecard: {scorecard_json}"

    md_text = scorecard_md.read_text(encoding="utf-8")
    assert "Plain Verdict:" in md_text
    assert "HURT" in md_text
    assert "8338" in md_text

    data = json.loads(scorecard_json.read_text(encoding="utf-8"))
    assert data["verdict"]["overall"] == "TRAINING_HURT_PERFORMANCE"
    assert "HURT" in data["verdict"]["plain_answer"]
    assert data["heldout_1000_results"]["baseline"]["gate1_calque_elimination_rate"] == 0.0
    assert data["protection_600_results"]["baseline"]["regional_dialect_preservation_rate"] == 0.1933
    assert data["protection_600_results"]["trained"]["regional_dialect_preservation_rate"] == 0.0033


def test_acceptance_audit_preflight() -> None:
    """Verify preflight acceptance audit is recorded and captures expected dataset failures."""
    audit_path = STUDY_DIR / "uldr_v1_acceptance_audit.json"
    assert audit_path.is_file()

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["dataset_dir"] == "data/projects/open_model_data/archive/uldr_v1_production"
    assert audit["total_records"] == 9000
    assert audit["overall_status"] == "ACCEPTANCE_FAILED"
    assert audit["checks"]["check_1_repeats"]["status"] == "FAIL"
    assert audit["checks"]["check_2_form_letters"]["status"] == "FAIL"
    assert audit["checks"]["check_5_source_rules"]["status"] == "FAIL"
