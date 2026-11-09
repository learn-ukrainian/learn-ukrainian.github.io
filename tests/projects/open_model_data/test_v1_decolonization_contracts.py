"""Tests for ULDR Phase 1 JSON schema contracts and seed fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.projects.open_model_data.paths import REGISTRY_OPEN_MODEL_DATA_DIR
from scripts.storage.paths import artifact_set

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REGISTRY_OPEN_MODEL_DATA_DIR / "contracts"


def _seed_lines(name: str) -> list[str]:
    snapshot = artifact_set("open_model_other_indexes")
    return snapshot.artifacts[f"projects/open_model_data/decolonization/seeds/{name}"].decode("utf-8").splitlines()


@pytest.fixture(scope="module")
def trajectory_schema() -> dict:
    schema_path = CONTRACTS_DIR / "v1_decolonization_trajectory.schema.json"
    assert schema_path.is_file(), f"Missing schema: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.fixture(scope="module")
def dpo_pair_schema() -> dict:
    schema_path = CONTRACTS_DIR / "v1_decolonization_dpo_pair.schema.json"
    assert schema_path.is_file(), f"Missing schema: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)
    return schema


@pytest.mark.needs_artifact(
    "open_model_other_indexes", "projects/open_model_data/decolonization/seeds/seed_decolonization_trajectories.jsonl"
)
def test_seed_trajectories_validate(trajectory_schema: dict) -> None:

    validator = jsonschema.Draft202012Validator(trajectory_schema)
    records = []
    for idx, line in enumerate(_seed_lines("seed_decolonization_trajectories.jsonl"), 1):
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        errors = list(validator.iter_errors(record))
        assert not errors, f"Validation errors on line {idx}: {[e.message for e in errors]}"
        records.append(record)

    # Verify register_spectrum alternatives are fully covered in vesum_attestation
    for r in records:
        vesum_lemmas = {v["lemma"] for v in r["vesum_attestation"]}
        for alt in r["register_spectrum"]["alternatives"]:
            assert alt["lemma"] in vesum_lemmas, (
                f"Alternative {alt['lemma']} in {r['target_term']} not in vesum_attestation"
            )

    assert len(records) >= 3
    # Verify unique trajectory IDs
    traj_ids = [r["trajectory_id"] for r in records]
    assert len(traj_ids) == len(set(traj_ids))

    # Linguistic assertions on seed contents
    targets = {r["target_term"] for r in records}
    assert "пилосос" in targets
    assert "переключити" in targets
    assert "приймати участь" in targets


@pytest.mark.needs_artifact(
    "open_model_other_indexes", "projects/open_model_data/decolonization/seeds/seed_decolonization_dpo_pairs.jsonl"
)
def test_seed_dpo_pairs_validate(dpo_pair_schema: dict) -> None:

    validator = jsonschema.Draft202012Validator(dpo_pair_schema)
    records = []
    for idx, line in enumerate(_seed_lines("seed_decolonization_dpo_pairs.jsonl"), 1):
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        errors = list(validator.iter_errors(record))
        assert not errors, f"Validation errors on line {idx}: {[e.message for e in errors]}"
        records.append(record)

    assert len(records) >= 3
    pair_ids = [r["pair_id"] for r in records]
    assert len(pair_ids) == len(set(pair_ids))


def test_pilot_canary_receipt_schema_contract() -> None:
    """Validate v1_pilot_canary_receipt schema against meta-schema and validate pilot canary receipt fixture."""
    schema_path = CONTRACTS_DIR / "v1_pilot_canary_receipt.schema.json"
    assert schema_path.is_file(), f"Missing schema: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.Draft202012Validator.check_schema(schema)

    receipt_path = REGISTRY_OPEN_MODEL_DATA_DIR / "canary" / "pilot_canary_receipt.json"
    assert receipt_path.is_file(), f"Missing receipt: {receipt_path}"
    with receipt_path.open("r", encoding="utf-8") as rf:
        receipt = json.load(rf)
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(receipt))
    assert not errors, f"Validation errors on canary receipt: {[e.message for e in errors]}"
