"""Hermetic and production-smoke tests for Pravopys delta primitives."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_pravopys_delta as delta


def _units(edition: str, count: int) -> list[dict[str, object]]:
    return [{
        "family_id": edition,
        "unit_id": f"{edition}.{number}",
        "unit_sha256": hashlib.sha256(f"unit-{edition}-{number}".encode()).hexdigest(),
        "normalized_text_sha256": hashlib.sha256(f"hash-{number}".encode()).hexdigest(),
        "ordinal": number,
        "locator": {
            "kind": "pdf_numbered_hierarchy",
            "edition_sha256": delta.EDITION_HASHES[edition],
            "page": number,
            "line": 1,
            "end_page": number,
            "end_line": 1,
            "section_path": [f"paragraph:{number}"],
        },
        "duplicate_group_id": f"duplicate.{edition}.{number}",
        "parse_status": "numbered_hierarchy_parsed",
        "rights": {
            "source_text_committed": False,
            "locator_only_allowed": True,
            "rights_limited_disposition": "rights_limited_locator_only",
        },
        "provenance": {
            "input_sha256": delta.EDITION_HASHES[edition],
            "unit_grain": "pdf_numbered_hierarchy",
        },
    } for number in range(1, count + 1)]


def _review(*, semantic: bool = False) -> dict[str, object]:
    binding = delta.load_ukrainian_reviewer_binding()
    return {
        **binding,
        "review_receipt_locator": "immutable://review-receipt/opaque-1",
        "review_receipt_sha256": "a" * 64,
        "evidence_locator": "immutable://review/opaque-1",
        "evidence_sha256": "b" * 64,
        "adjudication_state": "externally_reviewed",
        "semantic_review": semantic,
    }


def _synthetic_ledger() -> tuple[
    list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]
]:
    old, new = _units(delta.EDITION_2019, 1090), _units(delta.EDITION_2026, 1466)
    candidates = delta.generate_candidate_alignment(old, new)
    rows = []
    for candidate in candidates:
        old_ids, new_ids = candidate["unit_ids_2019"], candidate["unit_ids_2026"]
        disposition = "unchanged"
        semantic = False
        if old_ids and not new_ids:
            disposition, semantic = "removed_rule_bearing_unit", True
        elif new_ids and not old_ids:
            disposition, semantic = "added_rule_bearing_unit", True
        rows.append({
            "delta_id": f"delta.{candidate['candidate_id']}",
            "delta_disposition": disposition,
            "candidate_ids": [candidate["candidate_id"]],
            "unit_ids_2019": sorted(old_ids),
            "unit_ids_2026": sorted(new_ids),
            "edition_section_identity": "opaque-section",
            "ukrainian_review": _review(semantic=semantic),
        })
    return old, new, candidates, rows


def test_real_source_freeze_smoke_loads_2556_rows_and_candidate_partition() -> None:
    receipt, old, new = delta.load_frozen_pravopys_ledgers()
    first = delta.generate_candidate_alignment(old, new)
    assert receipt["schema_version"] == "phase3_source_universe_freeze_v1"
    assert len(old) == 1090
    assert len(new) == 1466
    assert first == delta.generate_candidate_alignment(old, new)
    assert {unit_id for row in first for unit_id in row["unit_ids_2019"]} == {row["unit_id"] for row in old}
    assert {unit_id for row in first for unit_id in row["unit_ids_2026"]} == {row["unit_id"] for row in new}
    assert all("source sentence" not in delta.canonical_json(row) for row in first)


def test_role_contract_loader_requires_exact_seat_and_task_binding() -> None:
    assert delta.load_ukrainian_reviewer_binding() == {
        "role_contract_sha256": delta.ROLE_CONTRACT_SHA256,
        "seat_id": "seat_ukrainian_source_reviewer",
        "role_id": delta.UKRAINIAN_REVIEWER_ROLE,
        "review_task_id": delta.UKRAINIAN_REVIEWER_TASK_ID,
        "reviewer_controller_identity": delta.UKRAINIAN_REVIEWER_CONTROLLER_ID,
    }


def test_bidirectional_ledger_and_immutable_review_requirements() -> None:
    old, new, candidates, rows = _synthetic_ledger()
    assert delta.validate_delta_ledger(rows, candidates, old, new)["edition_totals"] == {
        delta.EDITION_2019: 1090,
        delta.EDITION_2026: 1466,
    }
    next(row for row in rows if row["delta_disposition"] == "added_rule_bearing_unit")["ukrainian_review"]["evidence_locator"] = "https://mutable.example.invalid/review"
    with pytest.raises(delta.PravopysDeltaError, match="immutable review evidence"):
        delta.validate_delta_ledger(rows, candidates, old, new)


def test_candidate_partition_is_pinned_to_deterministic_generator() -> None:
    old, new, candidates, rows = _synthetic_ledger()
    broken = copy.deepcopy(candidates)
    pair = next(candidate for candidate in broken if candidate["candidate_kind"] == "candidate_pair")
    broken.remove(pair)
    for old_ids, new_ids, kind in (
        (pair["unit_ids_2019"], [], "unmatched_2019"),
        ([], pair["unit_ids_2026"], "unmatched_2026"),
    ):
        identity = {"basis": "unmatched", "unit_ids_2019": old_ids, "unit_ids_2026": new_ids}
        broken.append({
            "candidate_id": delta.sha256_json(identity),
            "candidate_basis": "unmatched",
            "candidate_kind": kind,
            "unit_ids_2019": old_ids,
            "unit_ids_2026": new_ids,
        })
    with pytest.raises(delta.PravopysDeltaError, match="deterministic mechanical generator"):
        delta.validate_delta_ledger(rows, broken, old, new)


def test_one_sided_candidates_require_edition_specific_dispositions() -> None:
    old, new, candidates, rows = _synthetic_ledger()
    broken = copy.deepcopy(rows)
    one_sided = next(row for row in broken if row["delta_disposition"] == "added_rule_bearing_unit")
    one_sided["delta_disposition"] = "unchanged"
    one_sided["ukrainian_review"]["semantic_review"] = False
    with pytest.raises(delta.PravopysDeltaError, match="unchanged delta must cover both editions"):
        delta.validate_delta_ledger(broken, candidates, old, new)


def test_standalone_review_validation_matches_schema_locator_and_hash_syntax() -> None:
    old, new, candidates, rows = _synthetic_ledger()
    bad_locator = copy.deepcopy(rows)
    bad_locator[0]["ukrainian_review"]["review_receipt_locator"] = "immutable://"
    with pytest.raises(delta.PravopysDeltaError, match="receipt locator"):
        delta.validate_delta_ledger(bad_locator, candidates, old, new)

    bad_hash = copy.deepcopy(rows)
    bad_hash[0]["ukrainian_review"]["review_receipt_sha256"] = "z" * 64
    with pytest.raises(delta.PravopysDeltaError, match="receipt hash"):
        delta.validate_delta_ledger(bad_hash, candidates, old, new)


def test_population_seed_requires_common_contract_without_private_fallback() -> None:
    _, _, _, rows = _synthetic_ledger()
    population = delta.freeze_population(rows)
    seed = {
        "population_sha256": population["population_sha256"],
        "seed_owner_role_id": delta.AUDITOR_ROLE,
        "auditor_attests_only": True,
        "author_or_root_choices": False,
        "reroll_count": 0,
        "audit_id": "pravopys_delta",
        "family_id": "pravopys_2019_2026_delta",
        "first_containing_origin_main_squash_merge_sha": "a" * 40,
        "universe_sha256": delta.source_universe_sha256(),
    }
    with pytest.raises(delta.PravopysDeltaError, match="approved-common-entropy-contract-required"):
        delta.draw_audit_sample(rows, population, seed)


def test_complete_bundle_closes_schema_and_runtime_role_contract_invariants() -> None:
    _, old, new = delta.load_frozen_pravopys_ledgers()
    candidates = delta.generate_candidate_alignment(old, new)
    rows = []
    for candidate in candidates:
        old_ids = candidate["unit_ids_2019"]
        new_ids = candidate["unit_ids_2026"]
        disposition = "unchanged"
        semantic = False
        if old_ids and not new_ids:
            disposition, semantic = "removed_rule_bearing_unit", True
        elif new_ids and not old_ids:
            disposition, semantic = "added_rule_bearing_unit", True
        rows.append({
            "delta_id": f"delta.{candidate['candidate_id']}",
            "delta_disposition": disposition,
            "candidate_ids": [candidate["candidate_id"]],
            "unit_ids_2019": sorted(old_ids),
            "unit_ids_2026": sorted(new_ids),
            "edition_section_identity": "opaque-section",
            "ukrainian_review": _review(semantic=semantic),
        })

    population = delta.freeze_population(rows)
    seed = {
        "population_sha256": population["population_sha256"],
        "seed_owner_role_id": delta.AUDITOR_ROLE,
        "auditor_attests_only": True,
        "author_or_root_choices": False,
        "reroll_count": 0,
        "audit_id": "pravopys_delta",
        "family_id": "pravopys_2019_2026_delta",
        "first_containing_origin_main_squash_merge_sha": "a" * 40,
        "universe_sha256": delta.source_universe_sha256(),
    }

    class ApprovedEntropy:
        def derive_audit_entropy(self, context: object) -> bytes:
            assert context
            return b"approved-common-entropy-test-fixture"

    entropy = ApprovedEntropy()
    sample = delta.draw_audit_sample(
        rows,
        population,
        seed,
        approved_common_entropy_contract=entropy,
    )
    bundle = {
        "schema_version": delta.SCHEMA_VERSION,
        "text_free": True,
        "source_freeze": {
            "receipt_path": "data/projects/open_model_data/evidence/source_universe_v1/source-universe-freeze-receipt.json",
            "receipt_sha256": delta.SOURCE_FREEZE_RECEIPT_SHA256,
            "ledger_sha256": delta.SOURCE_LEDGER_SHA256,
        },
        "units_2019": old,
        "units_2026": new,
        "candidate_alignment": candidates,
        "delta_ledger": rows,
        "population_freeze": population,
        "auditor_seed": seed,
        "audit_sample": sample,
        "audit_results": [{
            "delta_id": delta_id,
            "decision": "agree",
            "repair_applied": False,
        } for delta_id in sample["sample_delta_ids"]],
    }

    result = delta.validate_bundle(
        bundle,
        approved_common_entropy_contract=entropy,
    )
    schema = json.loads(Path(delta.SCHEMA_PATH).read_text(encoding="utf-8"))
    assert schema["$defs"]["review"]["properties"]["role_contract_sha256"]["const"] == (
        delta.ROLE_CONTRACT_SHA256
    )
    assert result["edition_totals"] == delta.EDITION_TOTALS


def test_hamilton_allocation_and_schema_are_strict() -> None:
    assert delta.hamilton_allocation({("a", "x"): 7, ("b", "y"): 3, ("c", "z"): 2}, 5) == {
        ("a", "x"): 3,
        ("b", "y"): 1,
        ("c", "z"): 1,
    }
    schema = json.loads(Path(delta.SCHEMA_PATH).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$id"].endswith("/phase3_pravopys_delta_bundle_v1.schema.json")
