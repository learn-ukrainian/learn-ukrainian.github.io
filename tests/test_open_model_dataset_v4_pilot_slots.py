"""V4 pilot entry contract is deterministic, bounded, and expression-free."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
ADMISSION = ROOT / "data/projects/open_model_data/admission"
SCHEMA = CONTRACTS / "dataset_v4_pilot_slot_manifest_v1.schema.json"
MANIFEST = ADMISSION / "dataset_v4_pilot_slot_manifest_v1.json"
V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _slot_ids(manifest: dict[str, Any]) -> list[str]:
    return [
        f"{series['id_prefix']}-{number:03d}"
        for series in manifest["slot_series"]
        for number in range(series["start"], series["start"] + series["count"])
    ]


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value)) if value else set()
    return set()


def test_v4_pilot_slot_manifest_validates_and_binds_the_controlling_outcome() -> None:
    schema = _load(SCHEMA)
    manifest = _load(MANIFEST)

    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(manifest), key=lambda item: list(item.path))

    assert not errors
    assert manifest["controlling_outcome_sha256"] == V4_SHA256
    assert manifest["text_free"] is True


def test_v4_pilot_slot_series_expands_to_exactly_one_hundred_unique_stable_ids() -> None:
    manifest = _load(MANIFEST)
    ids = _slot_ids(manifest)
    quotas = {series["stratum"]: series["count"] for series in manifest["slot_series"]}

    assert len(ids) == 100
    assert len(set(ids)) == 100
    assert quotas == {
        "standard_correct": 15,
        "correction": 15,
        "literary": 15,
        "dialect_regional": 15,
        "archaic_historical": 15,
        "mixing": 10,
        "quotation_interference": 10,
        "abstention": 5,
    }


def test_v4_pilot_slot_manifest_has_required_roles_gates_and_no_private_payload() -> None:
    manifest = _load(MANIFEST)
    keys = _all_keys(manifest)

    assert set(manifest["required_role_ids"]) == {f"A{index}" for index in range(14)}
    assert set(manifest["required_gate_ids"]) == {
        "VPS_CUSTODY_CAPACITY",
        "SOURCE_OPERATION_ADMISSION",
        "SEALED_HELDOUT_SOURCE_FAMILY_SPLIT",
        "NON_SELF_ARENA_VOTING",
        "MODEL_AGREEMENT_NOT_GOLD",
        "SILVER_FIRST_STABLE_IDS",
    }
    assert manifest["sealed_heldout_commitment"]["heldout_membership_included"] is False
    assert manifest["sealed_heldout_commitment"]["assignment_owner"] == "A2_A3_PRIVATE_ARTIFACT"
    assert not keys & {
        "content",
        "correction",
        "gold",
        "heldout_membership",
        "label",
        "provider_output",
        "source_body",
        "source_identity",
        "source_locator",
        "source_text",
        "text",
    }
