"""Adversarial metadata-only checks for the #7429 historical channels.

These tests never open source bodies or private receipts.  Fixtures contain
only frozen identifiers, hashes, counts, and explicit fail-closed states.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import phase3_historical_protection_channels as protection

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/projects/open_model_data"
ARTIFACT = DATA / "admission/phase3_historical_protection_channels_v1.json"
SCHEMA = DATA / "contracts/phase3_historical_protection_channels_v1.schema.json"
SHA256 = "a" * 64

EXPECTED_BINDINGS = {
    "historical_protection_channels_schema": "7dbf2a92fff8f78860ae5fd71768742bbd037ee7b86263c6f397afa3342e4d9d",
    "p1": "0b1cd81448b96b4e818aa1dedd7df7633ff88eb500bb4d6ac3668be02962a35b",
    "p1_schema": "24d1547695da9c5928d1351fa149ec1010c12acceb20c250e7c4d7a650225d34",
    "p1_dialect_amendment": "5a4b259f764a3d41499f0a989c02fed921c18b62c9831d361d18d19dcc948afa",
    "p1_dialect_amendment_schema": "d4b987925484fb5d1e08a94d266d2f3ad01e6779335df13725244db6c61cdb10",
    "p2": "dc8dfdf207728ef386cea14ddb328289b2beee5159afb98bf076e5f117602ea3",
    "p2_schema": "8e93c51af812b8d32e91ae7ff55eff2332668feb7c6b990e350f2df50880d5bf",
    "scope_circularity_firewall": "4470448c6d0f665196375cf28255d7c092148700a99934b2d0dd1f43a8a3e24c",
    "scope_circularity_firewall_schema": "fb419508d86ee00c3d28d90bd5a999ae45483e93789907a6be4cddca568ac4ae",
    "historical_spine_v2": "4a7a8f8648a7f5f8bbf05c9a9e60b348a646f054e4e5e69ebf1585447b573891",
    "historical_spine_v2_schema": "8bce6863f05d20b3d31f890ff79b0fc162497fbed3b04e83014aa9a254b55108",
    "periodization_freeze_v1": "94d07a2e4e2fe453334a494007bc823cf4be7ce07f0a21779c73163ac821a198",
    "periodization_freeze_v1_schema": "4098ce26e3cb4ea1b4df7164d2487f9877121876ca3994a25a7481e7e5ad7c01",
}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _contract() -> dict[str, Any]:
    return copy.deepcopy(protection.build_contract())


def _schema() -> dict[str, Any]:
    value = _json(SCHEMA)
    Draft202012Validator.check_schema(value)
    return value


def _record_schema() -> dict[str, Any]:
    schema = _schema()
    return {"$schema": schema["$schema"], "$defs": schema["$defs"], **schema["$defs"]["disposition_record"]}


def _channel(channel_id: str) -> dict[str, Any]:
    return next(item for item in _contract()["channels"] if item["channel_id"] == channel_id)


def _protected_record(channel_id: str) -> dict[str, Any]:
    contract = _contract()
    channel = next(item for item in contract["channels"] if item["channel_id"] == channel_id)
    kind_by_identity = {
        "old_east_slavic_kyivan_rus": "protected_old_east_slavic",
        "middle_ukrainian": "protected_middle_ukrainian",
        "church_slavonic_recension": "protected_church_slavonic_recension",
        "source_attested_rusyn": "protected_rusyn",
    }
    identity = channel["protected_identity"]
    source_ids = list(channel["source_unit_ids"])
    units = {unit["source_unit_id"]: unit for unit in contract["source_inventory"]}
    refs = []
    for index, source_id in enumerate(source_ids):
        unit = units[source_id]
        refs.append(
            {
                "evidence_ref_id": f"evidence:{channel_id}:{index}",
                "claim_role": "protected_historical_identity" if index == 0 else "rights_provenance",
                "source_unit_id": source_id,
                "source_unit_identity_sha256": unit["source_identity_sha256"],
                "source_artifact_sha256": unit["source_artifact_sha256"],
                "provenance_sha256": unit["provenance_sha256"],
            }
        )
    if len(refs) == 1:
        refs.append(copy.deepcopy(refs[0]))
        refs[-1]["evidence_ref_id"] = f"evidence:{channel_id}:rights"
        refs[-1]["claim_role"] = "rights_provenance"
    return {
        "schema_version": protection.RECORD_SCHEMA_VERSION,
        "record_kind": kind_by_identity[identity],
        "record_id": f"protected:{channel_id}:fixture",
        "channel_id": channel_id,
        "language_identity": identity,
        "source_qualified_identity": True,
        "source_unit_ids": source_ids,
        "evidence_refs": refs,
        "review": {
            "reviewer_kind": "human",
            "qualification_status": "registered_source_qualified_human",
            "adjudication_record_sha256": SHA256,
            "evidence_ref_ids": [ref["evidence_ref_id"] for ref in refs],
        },
        "period_id": "period:historical",
        "region_id": "region:source-attested",
        "register_id": "register:source-attested",
        "recension_editorial_layer_id": "recension:source-attested",
        "identity_candidates": [identity],
        "language_layer_ids": [f"historical:{identity}", "editorial:source-attested"],
        "mixed_layers_allowed": True,
        "single_label_forced": False,
        "protection_invariants": copy.deepcopy(protection.NON_ERASURE_INVARIANTS),
        "body_free": True,
    }


def _coverage_blocked(channel_id: str = "old_east_slavic_kyivan_rus") -> dict[str, Any]:
    return protection.build_coverage_blocked_record(channel_id)


def _unresolved(channel_id: str = "source_attested_rusyn", *, abstention: bool = False) -> dict[str, Any]:
    return protection.build_unresolved_record(channel_id, abstention=abstention)


def test_artifact_reproduces_exactly_from_frozen_inputs() -> None:
    assert _json(ARTIFACT) == protection.build_contract()
    assert protection.validate_contract_integrity(_json(ARTIFACT)) is True


def test_schema_is_valid_and_artifact_is_strictly_metadata_only() -> None:
    value = _json(ARTIFACT)
    Draft202012Validator(_schema()).validate(value)
    assert value["text_free"] is True
    assert value["safety"] == {
        "source_text_emitted": False,
        "modernized_text_emitted": False,
        "private_locator_emitted": False,
        "dataset_rows_emitted": False,
        "labels_created": False,
        "gold_created": False,
        "provider_calls": False,
        "training_performed": False,
    }


def test_all_required_upstream_bindings_are_exact_and_hash_bound() -> None:
    contract = _contract()
    assert {key: value["sha256"] for key, value in contract["bindings"].items()} == EXPECTED_BINDINGS
    assert contract["controlling_outcome_sha256"] == protection.OUTCOME_SHA256
    assert contract["input_state"]["p2_composite_input_sha256"] == "83b59c6b62fff0beaf68dec7c3ca40b70033693dc19c50f26d27c553265352b0"
    assert contract["heldout_contract"]["firewall_artifact_sha256"] == EXPECTED_BINDINGS["scope_circularity_firewall"]


def test_historical_non_erasure_and_mixed_layer_invariants_are_frozen() -> None:
    invariants = _contract()["historical_protection"]
    for key, expected in protection.NON_ERASURE_INVARIANTS.items():
        assert invariants[key] is expected
    assert invariants["protected_identity_classes"] == list(protection.HISTORICAL_CLASSES)
    assert invariants["script_is_not_language_identity"] is True
    assert invariants["mixed_layers_allowed"] is True
    assert invariants["forced_single_label_forbidden"] is True
    assert invariants["no_automatic_successor_mapping"] is True


def test_historical_spine_source_inventory_retains_rights_and_review_gaps() -> None:
    inventory = _contract()["source_inventory"]
    assert {item["collection_id"] for item in inventory} == {
        "saint-sophia-inscriptions",
        "korniienko-spas-na-berestovi-2013",
        "bobrovskyy-near-caves-dipinto-2010",
        "ud-old-east-slavic-ruthenian-05a029e00ccf",
        "plug2-zenodo-19482961",
    }
    assert all(item["metadata_only"] is True for item in inventory)
    assert all(item["semantic_gold"] is False for item in inventory)
    assert all(item["phase3_historical_training_eligible"] is False for item in inventory)
    assert any(item["rights_status"] == "publicly_downloadable_license_not_declared" for item in inventory)
    assert any(item["rights_status"] == "private_research_artifact_only" for item in inventory)
    assert all("source_text" not in item and "private_locator" not in item for item in inventory)


def test_channels_keep_old_east_slavic_middle_church_and_rusyn_distinct() -> None:
    channels = {item["channel_id"]: item for item in _contract()["channels"]}
    assert set(channels) == {
        "old_east_slavic_kyivan_rus",
        "middle_ukrainian",
        "church_slavonic_recension",
        "source_attested_rusyn",
        "unresolved_historical_cyrillic",
    }
    assert channels["old_east_slavic_kyivan_rus"]["protected_identity"] != "source_attested_rusyn"
    assert channels["church_slavonic_recension"]["protected_identity"] != "middle_ukrainian"
    assert channels["source_attested_rusyn"]["source_unit_ids"] == [
        "historical.ud-old-east-slavic-ruthenian-05a029e00ccf"
    ]
    assert channels["source_attested_rusyn"]["status"] == "unresolved"
    assert channels["unresolved_historical_cyrillic"]["source_unit_ids"] == []
    assert _contract()["source_contract"]["source_attested_rusyn_policy"] == {
        "requires_source_qualified_identity": True,
        "ruthenian_is_not_rusyn_alias": True,
        "unresolved_without_source_attestation": True,
    }


def test_dialect_amendment_and_historical_channels_do_not_change_denominator() -> None:
    contract = _contract()
    assert contract["denominator"] == {
        "source_units": 57,
        "unknown_rights_blockers": 39,
        "p1_base_required_cells": 15,
        "p1_composite_required_cells": 16,
        "p2_rule_slots_R": 0,
        "historical_source_collections": 5,
        "modern_correction_denominator_unchanged": True,
        "historical_channels_additive_protection_only": True,
        "blocked_and_unresolved_remain_denominator_visible": True,
        "partial_denominator_permitted": False,
        "cell_status_counts": {"coverage_blocked": 14, "not_applicable_with_evidence": 2},
    }
    assert protection.validate_source_channel(
        next(item for item in contract["channels"] if item["channel_id"] == "old_east_slavic_kyivan_rus"), contract
    ) is True


def test_current_review_and_heldout_states_are_explicitly_non_admitting() -> None:
    contract = _contract()
    assert contract["review_contract"]["semantic_admission_permitted"] is False
    assert contract["review_contract"]["adjudication_registry_status"] == "FROZEN_NONADMITTING"
    assert contract["heldout_contract"]["state"] == "evaluation_only"
    assert contract["heldout_contract"]["builder_receives_membership"] is False
    assert contract["heldout_contract"]["heldout_cases_selected"] == 0
    assert contract["heldout_contract"]["zero_heldout_cases_state"] == "BLOCKED_NOT_ZERO"
    assert contract["heldout_contract"]["split_atomicity"] == [
        "source",
        "document",
        "work",
        "edition",
        "exact_duplicate_component",
        "near_duplicate_connected_component",
    ]
    assert "prompts" in contract["heldout_contract"]["deny_namespaces"]
    assert "synthetic_siblings" in contract["heldout_contract"]["deny_namespaces"]


def test_schema_binding_is_part_of_the_contract_and_receipt() -> None:
    contract = _contract()
    binding = contract["bindings"]["historical_protection_channels_schema"]
    assert binding == {
        "path": "data/projects/open_model_data/contracts/phase3_historical_protection_channels_v1.schema.json",
        "sha256": protection.SCHEMA_SHA256,
    }
    assert protection._receipt_sha256(contract) == contract["receipt_sha256"]


def test_missing_contract_schema_fails_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    contract = _contract()
    monkeypatch.setattr(protection, "SCHEMA_PATH", tmp_path / "missing.schema.json")
    assert protection.validate_contract_integrity(contract) is False
    with pytest.raises(ValueError, match="historical_protection_schema_path_drift"):
        protection.build_contract()
    with pytest.raises(ValueError, match="historical_protection_schema_path_drift"):
        protection.main(["--check"])


def test_modified_contract_schema_fails_closed_even_if_a_digest_is_supplied(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    contract = _contract()
    modified = copy.deepcopy(_schema())
    modified["additionalProperties"] = True
    modified_path = tmp_path / "modified.schema.json"
    modified_path.write_bytes(protection.canonical_json(modified))
    monkeypatch.setattr(protection, "SCHEMA_PATH", modified_path)
    monkeypatch.setattr(protection, "PINNED_SCHEMA_PATH", modified_path)
    monkeypatch.setitem(protection.PINS, modified_path, protection.sha256_file(modified_path))
    assert protection.validate_contract_integrity(contract) is False
    with pytest.raises(ValueError, match="historical_protection_schema_pin_drift"):
        protection.build_contract()
    with pytest.raises(ValueError, match="historical_protection_schema_pin_drift"):
        protection.main(["--check"])


@pytest.mark.parametrize("binding", sorted(EXPECTED_BINDINGS))
def test_binding_digest_mutation_fails_closed(binding: str) -> None:
    contract = _contract()
    contract["bindings"][binding]["sha256"] = SHA256
    assert protection.validate_contract_integrity(contract) is False


@pytest.mark.parametrize(
    "field",
    ["historical_forms_protected", "modern_correction_eligible", "old_east_slavic_is_modern_russian", "historical_ruskyi_auto_mapped_to_modern_russian"],
)
def test_non_erasure_boolean_mutations_fail_closed(field: str) -> None:
    contract = _contract()
    contract["historical_protection"][field] = not protection.NON_ERASURE_INVARIANTS[field]
    assert protection.validate_contract_integrity(contract) is False


@pytest.mark.parametrize("field", ["p1_base_required_cells", "p1_composite_required_cells", "p2_rule_slots_R", "source_units", "unknown_rights_blockers"])
def test_denominator_shrinkage_fails_closed(field: str) -> None:
    contract = _contract()
    contract["denominator"][field] = 1 if contract["denominator"][field] == 0 else 0
    assert protection.validate_contract_integrity(contract) is False


@pytest.mark.parametrize("field", ["source_rows_emitted", "historical_protected_rows_admitted", "rusyn_rows_admitted", "provider_calls", "training_rows"])
def test_zero_counter_mutations_fail_closed(field: str) -> None:
    contract = _contract()
    contract["zero_counters"][field] = 1
    assert protection.validate_contract_integrity(contract) is False


def test_contract_receipt_digest_and_unexpected_fields_are_bound() -> None:
    contract = _contract()
    contract["unexpected_metadata"] = "must-reject"
    assert protection.validate_contract_integrity(contract) is False
    contract = _contract()
    contract["receipt_sha256"] = SHA256
    assert protection.validate_contract_integrity(contract) is False


def test_schema_rejects_unknown_top_level_and_nested_fields() -> None:
    validator = Draft202012Validator(_schema())
    top = _json(ARTIFACT)
    top["unexpected_metadata"] = True
    with pytest.raises(ValidationError):
        validator.validate(top)
    nested = _json(ARTIFACT)
    nested["historical_protection"]["source_text"] = "forbidden"
    with pytest.raises(ValidationError):
        validator.validate(nested)


def test_schema_rejects_uppercase_binding_digest() -> None:
    value = _json(ARTIFACT)
    value["bindings"]["p1"]["sha256"] = value["bindings"]["p1"]["sha256"].upper()
    with pytest.raises(ValidationError):
        Draft202012Validator(_schema()).validate(value)


@pytest.mark.parametrize(
    "record",
    [
        _coverage_blocked(),
        _unresolved(),
        _unresolved(abstention=True),
    ],
)
def test_state_specific_record_schema_accepts_body_free_shapes(record: dict[str, Any]) -> None:
    Draft202012Validator(_record_schema()).validate(record)
    assert protection.validate_disposition_shape(record) is True


def test_current_blocked_unresolved_and_abstention_routes_are_admissible() -> None:
    assert protection.validate_disposition_record(_coverage_blocked()) is True
    assert protection.validate_disposition_record(_unresolved()) is True
    assert protection.validate_disposition_record(_unresolved(abstention=True)) is True
    assert protection.validate_record(_coverage_blocked("unresolved_historical_cyrillic")) is True


def test_coverage_blocked_metadata_receipts_do_not_emit_dataset_rows() -> None:
    disposition = _contract()["disposition_contract"]
    assert disposition["coverage_blocked_emits_record"] is False
    assert disposition["coverage_blocked_emission_scope"] == "dataset_rows_only"
    blocked = _coverage_blocked()
    assert protection.validate_disposition_shape(blocked) is True
    assert protection.validate_disposition_record(blocked) is True


@pytest.mark.parametrize(
    "bad_dimensions",
    [
        ["period_id"],
        ["period_id", "region_id", "register_id", "recension_editorial_layer_id", "unrelated"],
        ["region_id", "period_id", "register_id", "recension_editorial_layer_id"],
    ],
)
def test_unknown_dimension_set_is_exact_for_every_nonsemantic_route(bad_dimensions: list[str]) -> None:
    for record in (_coverage_blocked(), _unresolved(), _unresolved(abstention=True)):
        record["unknown_dimensions"] = bad_dimensions
        assert protection.validate_disposition_shape(record) is False
        with pytest.raises(ValidationError):
            Draft202012Validator(_record_schema()).validate(record)


@pytest.mark.parametrize("channel_id", [item["channel_id"] for item in protection._channels() if item["source_unit_ids"]])
def test_semantic_protected_records_remain_non_admitting_until_review(channel_id: str) -> None:
    record = _protected_record(channel_id)
    assert protection.validate_disposition_shape(record) is False
    assert protection.validate_disposition_record(record) is False


def test_frozen_registry_rejects_bare_adjudication_sha_and_identity_rights_refs() -> None:
    contract = _contract()
    record = _protected_record("old_east_slavic_kyivan_rus")
    assert contract["review_contract"]["adjudication_registry_status"] == "FROZEN_NONADMITTING"
    assert record["review"]["adjudication_record_sha256"] == SHA256
    assert {ref["claim_role"] for ref in record["evidence_refs"]} == {
        "protected_historical_identity",
        "rights_provenance",
    }
    assert protection.validate_disposition_shape(record, contract) is False
    assert protection.validate_disposition_record(record, contract) is False


@pytest.mark.parametrize(
    ("record_kind", "channel_id"),
    [
        ("protected_old_east_slavic", "old_east_slavic_kyivan_rus"),
        ("protected_middle_ukrainian", "middle_ukrainian"),
        ("protected_church_slavonic_recension", "church_slavonic_recension"),
        ("protected_rusyn", "source_attested_rusyn"),
    ],
)
def test_missing_period_region_register_or_recension_fails_closed(record_kind: str, channel_id: str) -> None:
    record = _protected_record(channel_id)
    assert record["record_kind"] == record_kind
    for field in ("period_id", "region_id", "register_id", "recension_editorial_layer_id"):
        mutated = copy.deepcopy(record)
        del mutated[field]
        assert protection.validate_disposition_shape(mutated) is False
        mutated = copy.deepcopy(record)
        mutated[field] = ""
        assert protection.validate_disposition_shape(mutated) is False


@pytest.mark.parametrize("field", ["historical_forms_protected", "modern_correction_eligible", "old_east_slavic_is_modern_russian", "historical_ruskyi_auto_mapped_to_modern_russian"])
def test_record_non_erasure_mutations_fail_closed(field: str) -> None:
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["protection_invariants"][field] = not protection.NON_ERASURE_INVARIANTS[field]
    assert protection.validate_disposition_shape(record) is False


@pytest.mark.parametrize("mutation", [{"single_label_forced": True}, {"mixed_layers_allowed": False}, {"language_layer_ids": []}])
def test_mixed_layer_collapse_or_forced_single_label_fails_closed(mutation: dict[str, Any]) -> None:
    record = _protected_record("church_slavonic_recension")
    record.update(mutation)
    assert protection.validate_disposition_shape(record) is False


def test_oes_to_modern_russian_mapping_and_modern_record_kinds_fail_closed() -> None:
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["language_identity"] = "modern_standard_ukrainian"
    assert protection.validate_disposition_shape(record) is False
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["protection_invariants"]["old_east_slavic_is_modern_russian"] = True
    assert protection.validate_disposition_shape(record) is False
    blocked = _coverage_blocked()
    blocked["record_kind"] = "correct_modern_production"
    assert protection.validate_disposition_shape(blocked) is False


def test_rusyn_relabeling_requires_the_source_attested_rusyn_channel() -> None:
    record = _protected_record("source_attested_rusyn")
    record["language_identity"] = "old_east_slavic_kyivan_rus"
    assert protection.validate_disposition_shape(record) is False
    record = _protected_record("source_attested_rusyn")
    record["channel_id"] = "old_east_slavic_kyivan_rus"
    assert protection.validate_disposition_shape(record) is False


def test_absent_oes_and_church_slavonic_artifacts_remain_blocked() -> None:
    contract = _contract()
    unresolved = _channel("unresolved_historical_cyrillic")
    assert unresolved["status"] == "coverage_blocked"
    assert unresolved["source_unit_ids"] == []
    assert "source_artifact_not_frozen" in unresolved["blocker_codes"]
    church = _channel("church_slavonic_recension")
    assert "church_slavonic_historical_ukrainian_layer_separation_pending" in church["blocker_codes"]
    assert not list(DATA.rglob("*church*slavonic*"))
    assert not list(DATA.rglob("*rusyn*"))
    assert contract["zero_counters"]["church_slavonic_rows_admitted"] == 0
    assert contract["zero_counters"]["rusyn_rows_admitted"] == 0


@pytest.mark.parametrize("field", ["source_unit_identity_sha256", "source_artifact_sha256", "provenance_sha256"])
def test_evidence_hash_drift_fails_closed(field: str) -> None:
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["evidence_refs"][0][field] = SHA256
    assert protection.validate_disposition_shape(record) is False


def test_evidence_source_and_review_identity_laundering_fails_closed() -> None:
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["source_unit_ids"] = ["historical.ud-old-east-slavic-ruthenian-05a029e00ccf"]
    assert protection.validate_disposition_shape(record) is False
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["review"]["evidence_ref_ids"] = ["evidence:not-cited"]
    assert protection.validate_disposition_shape(record) is False
    record = _protected_record("old_east_slavic_kyivan_rus")
    record["evidence_refs"][0]["claim_role"] = "source_qualified_human_adjudication"
    assert protection.validate_disposition_shape(record) is False


def test_model_proposals_cannot_promote_or_add_to_a_protection_record() -> None:
    record = _coverage_blocked()
    record["producer_kind"] = "model"
    record["promotion_decision"] = "accepted"
    assert protection.validate_disposition_shape(record) is False
    assert protection.validate_disposition_record(record) is False


def test_unresolved_route_requires_explicit_unknown_dimensions() -> None:
    record = _unresolved()
    record["unknown_dimensions"] = []
    assert protection.validate_disposition_shape(record) is False
    record = _unresolved(abstention=True)
    record.pop("region_id")
    assert protection.validate_disposition_shape(record) is False


@pytest.mark.parametrize("forbidden", sorted(protection.FORBIDDEN_RECORD_KEYS))
def test_body_label_prompt_and_modernization_fields_are_rejected(forbidden: str) -> None:
    record = _coverage_blocked()
    record[forbidden] = "forbidden"
    assert protection.validate_disposition_shape(record) is False


def test_source_channel_cannot_be_forged_or_relabelled() -> None:
    contract = _contract()
    channel = copy.deepcopy(_channel("old_east_slavic_kyivan_rus"))
    channel["protected_identity"] = "source_attested_rusyn"
    assert protection.validate_source_channel(channel, contract) is False
    channel = copy.deepcopy(_channel("old_east_slavic_kyivan_rus"))
    channel["source_unit_ids"] = []
    assert protection.validate_source_channel(channel, contract) is False


def test_generator_check_is_byte_exact_and_does_not_rewrite_artifact() -> None:
    before = ARTIFACT.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            protection.ROOT / "scripts/projects/open_model_data/phase3_historical_protection_channels.py",
            "--check",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert ARTIFACT.read_bytes() == before
