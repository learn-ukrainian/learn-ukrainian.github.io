"""Integrity checks for the metadata-only #7425 P1 freeze."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from projects.open_model_data.freeze_phase3_p1_universe import build_manifest

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/projects/open_model_data"
SCHEMA = DATA / "contracts/phase3_p1_universe_freeze_v1.schema.json"
ARTIFACT = DATA / "evidence/phase3_p1_universe_freeze_v1.json"


def test_p1_artifact_matches_deterministic_builder() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert artifact == build_manifest()


def test_p1_artifact_validates_and_freezes_boundaries() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(artifact)

    language = artifact["language_universe"]
    assert language["modern_contact_classes"] == [
        "russian", "belarusian", "bulgarian", "macedonian", "serbian_cyrillic", "montenegrin_cyrillic"
    ]
    assert language["modern_contact_classes_exhaustive"] is True
    assert artifact["historical_protection"]["historical_forms_protected"] is True
    assert artifact["historical_protection"]["modern_correction_eligible"] is False
    assert artifact["historical_protection"]["old_east_slavic_is_modern_russian"] is False
    assert artifact["historical_protection"]["historical_ruskyi_auto_mapped_to_modern_russian"] is False


def test_p1_source_units_have_one_disposition_and_rights_blockers_are_visible() -> None:
    units = ARTIFACT.read_text(encoding="utf-8")
    artifact = json.loads(units)
    source_units = artifact["source_manifest"]["source_units"]
    assert artifact["source_manifest"]["source_unit_count"] == len(source_units)
    assert len({unit["source_unit_id"] for unit in source_units}) == len(source_units)
    assert all(unit["metadata_only"] and unit["source_unit_disposition"] for unit in source_units)
    unknown_rights = [unit for unit in source_units if unit["rights"]["required_state"] == "unknown"]
    assert unknown_rights
    assert all(unit["rights"]["blocked_lanes"] for unit in unknown_rights)


def test_p1_predicate_and_cells_are_explicit_and_fail_closed() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    predicate = artifact["applicability"]
    assert {clause["field"] for clause in predicate["all_of"]} == {
        "language_identity", "script_profile", "context_role", "contrasted_contact_class", "scope_status", "human_adjudication"
    }
    assert predicate["else_route"] == "abstain"

    cells = artifact["required_cell_manifest"]["cells"]
    assert len({item["cell_id"] for item in cells}) == len(cells)
    assert all(item["status"] != "not_applicable_with_evidence" or not item["protection_required"] for item in cells)
    assert any(item["role"] == "protected_historical" and item["protection_required"] for item in cells)
    assert artifact["required_cell_manifest"]["implicit_cartesian_product"] is False


def test_p1_has_no_provider_or_dataset_side_effect_claims() -> None:
    safety = json.loads(ARTIFACT.read_text(encoding="utf-8"))["safety"]
    assert safety == {
        "provider_calls": False,
        "labels_created": False,
        "dataset_rows_emitted": False,
        "gold_created": False,
        "training_performed": False,
    }
