"""Tests for ULDR Phase 1 JSON schema contracts and seed fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
SEEDS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "seeds"


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


def test_seed_trajectories_validate(trajectory_schema: dict) -> None:
    seed_path = SEEDS_DIR / "seed_decolonization_trajectories.jsonl"
    assert seed_path.is_file(), f"Missing seed file: {seed_path}"

    validator = jsonschema.Draft202012Validator(trajectory_schema)
    records = []
    with seed_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            errors = list(validator.iter_errors(record))
            assert not errors, f"Validation errors on line {idx}: {[e.message for e in errors]}"
            records.append(record)

    assert len(records) >= 3
    # Verify unique trajectory IDs
    traj_ids = [r["trajectory_id"] for r in records]
    assert len(traj_ids) == len(set(traj_ids))

    # Linguistic assertions on seed contents
    targets = {r["target_term"] for r in records}
    assert "пилосос" in targets
    assert "переключити" in targets
    assert "приймати участь" in targets


def test_seed_dpo_pairs_validate(dpo_pair_schema: dict) -> None:
    seed_path = SEEDS_DIR / "seed_decolonization_dpo_pairs.jsonl"
    assert seed_path.is_file(), f"Missing seed file: {seed_path}"

    validator = jsonschema.Draft202012Validator(dpo_pair_schema)
    records = []
    with seed_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
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


def test_trajectory_schema_negative_rejection(trajectory_schema: dict) -> None:
    validator = jsonschema.Draft202012Validator(trajectory_schema)
    # Missing required field
    invalid_record = {
        "schema_version": "v1_decolonization_trajectory",
        "trajectory_id": "traj.decolonize.0000000000000000",
        "query": "Як правильно?",
        "target_term": "тест",
        "is_calque_or_russianism": True,
        # Missing morphemic_breakdown and other required fields
    }
    assert not validator.is_valid(invalid_record)


def test_dpo_pair_schema_negative_rejection(dpo_pair_schema: dict) -> None:
    validator = jsonschema.Draft202012Validator(dpo_pair_schema)
    # Invalid flaw enum
    invalid_record = {
        "schema_version": "v1_decolonization_dpo_pair",
        "pair_id": "dpo.decolonize.0000000000000000",
        "prompt": "Як правильно?",
        "chosen": "Правильний текст розгорнутої відповіді.",
        "rejected": "Неправильний текст радянської відповіді.",
        "metadata": {
            "target_term": "тест",
            "rejected_flaw": "invalid_flaw_category",
            "primary_alternative": "тест2",
            "vesum_verified": True,
        },
    }
    assert not validator.is_valid(invalid_record)
