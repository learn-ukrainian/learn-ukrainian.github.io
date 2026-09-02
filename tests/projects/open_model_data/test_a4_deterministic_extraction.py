"""V4 A4 deterministic extraction is text-free, builder-packet-gated, and
carries forward every A2 residual unchanged.

A4 is the first builder-facing stage after the A3 held-out firewall. It
must never see which source-family A3 assigned to the held-out pool -- see
``dataset_v4_a3_heldout_source_family_seal_receipt_v1.json``'s
``access_firewall`` entry for ``A4_deterministic_extraction``. As of this
receipt, A3 has not yet issued a builder packet
(``temporal_firewall.builder_packet_issued`` is ``false``), so A4 is
correctly blocked: zero source units extracted, zero dataset rows emitted,
and a single explicit residual naming the missing builder-packet issuance.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a4_deterministic_extraction as extraction

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a4_deterministic_extraction_receipt_v1.schema.json"
A2_RECEIPT = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
A3_RECEIPT = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"

V4_SHA256 = "78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20"

FORBIDDEN_KEYS = {
    "content",
    "text",
    "source_body",
    "source_text",
    "prompt",
    "label",
    "gold",
    "heldout_membership",
    "heldout_locator",
    "heldout_fingerprint",
    "heldout_neighbour",
    "heldout_near_neighbour",
    "held_out_membership",
    "heldout_family_pool",
    "heldout_membership_locator",
}

EXTRACTION_ALGORITHM_DESCRIPTOR = {
    "algorithm_id": "v4-a4-deterministic-span-extraction-v1",
    "algorithm_version": "v1",
    "unit_of_extraction": "sentence_span",
    "content_blind": False,
    "ordering": "source_unit_id_ascending_then_byte_offset_ascending",
    "input_hash_formula": "sha256(raw_span_bytes_utf8)",
    "output_hash_formula": (
        "sha256(canonical_json({source_unit_id, span_index, span_byte_length, "
        "input_sha256, extraction_algorithm_id, extraction_algorithm_version}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_identical_source_unit_bytes_and_frozen_segmentation_rule",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _receipt() -> dict[str, Any]:
    return _load(RECEIPT)


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda error: list(error.path))


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


def test_a4_extraction_schema_and_v4_control_binding() -> None:
    receipt = _receipt()

    assert not _errors(receipt)
    assert receipt["controlling_outcome_sha256"] == V4_SHA256
    assert receipt["text_free"] is True
    assert receipt["status"] == "A4_DETERMINISTIC_EXTRACTION_BLOCKED_NO_BUILDER_PACKET"

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a4_extraction_bindings_match_exact_inputs() -> None:
    receipt = _receipt()

    for binding in receipt["bindings"].values():
        bound_path = ROOT / binding["path"]
        assert bound_path.is_file()
        assert hashlib.sha256(bound_path.read_bytes()).hexdigest() == binding["sha256"]

    assert receipt["bindings"]["a3_heldout_source_family_seal"]["path"] == str(A3_RECEIPT.relative_to(ROOT))


def test_a4_extraction_algorithm_is_frozen_and_hashed() -> None:
    receipt = _receipt()
    algorithm = receipt["extraction_algorithm"]
    declared = {k: algorithm[k] for k in EXTRACTION_ALGORITHM_DESCRIPTOR}

    # Recomputed from a formula frozen in this test file (independent of the
    # receipt and of the implementation module), so a different
    # implementation that silently changed the formula cannot keep this hash.
    assert declared == EXTRACTION_ALGORITHM_DESCRIPTOR
    assert (
        algorithm["algorithm_descriptor_sha256"]
        == hashlib.sha256(_canonical_json(EXTRACTION_ALGORITHM_DESCRIPTOR).encode("utf-8")).hexdigest()
    )
    assert algorithm["text_emitted"] is False
    assert algorithm["algorithm_descriptor_sha256"] == extraction.EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256


def test_a4_extraction_builder_packet_gate_is_closed_and_matches_live_a3_state() -> None:
    receipt = _receipt()
    gate = receipt["builder_packet_gate"]
    a3_receipt = _load(A3_RECEIPT)

    assert gate["a3_seal_complete"] is True
    assert gate["builder_packet_issued"] is False
    assert gate["builder_eligible_source_unit_ids_known_to_a4"] is False
    assert gate["blocked_reason_code"] == "builder_packet_not_issued"
    assert gate["owner_role"] == "A3_heldout"

    # The gate must track the *live* A3 receipt's own declared state, not a
    # value frozen independently of it.
    assert a3_receipt["temporal_firewall"]["builder_packet_issued"] == gate["builder_packet_issued"]
    assert a3_receipt["execution_counters"]["builder_packets_issued"] == 0

    live_gate = extraction.check_builder_packet_gate()
    assert live_gate["gate_open"] is False
    assert live_gate["blocked_reason_code"] == "builder_packet_not_issued"


def test_a4_extraction_ledger_is_empty_while_gate_is_closed() -> None:
    receipt = _receipt()

    assert receipt["extraction_ledger"] == []
    assert receipt["execution_counters"]["source_units_extracted"] == 0
    assert receipt["execution_counters"]["spans_extracted"] == 0
    assert receipt["execution_counters"]["dataset_rows_emitted"] == 0
    assert receipt["execution_counters"]["builder_packets_consumed"] == 0
    assert receipt["safety_assertions"]["extraction_executed_without_builder_packet"] is False
    assert receipt["safety_assertions"]["text_emitted"] is False
    assert receipt["safety_assertions"]["held_out_membership_referenced"] is False


def test_a4_extraction_receipt_never_names_a_held_out_family_or_source_text() -> None:
    receipt = _receipt()
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    assert "fam-" not in serialized  # A3 family_ids never appear in a builder-facing receipt
    assert not _all_keys(receipt) & {"salt", "private_salt", "heldout_family_pool"}


def test_a4_extraction_carries_forward_every_a2_residual_unchanged() -> None:
    receipt = _receipt()
    a2_receipt = _load(A2_RECEIPT)

    a2_residual_ids = {entry["residual_id"] for entry in a2_receipt["residuals"]}
    carried_ids = {entry["residual_id"] for entry in receipt["a2_residuals_carried_forward"]}

    assert carried_ids == a2_residual_ids
    for entry in receipt["a2_residuals_carried_forward"]:
        assert entry["origin_stage"] == "A2"
        assert entry["status"] == "unresolved_carried_to_a4"


def test_a4_residuals_name_the_builder_packet_block() -> None:
    receipt = _receipt()
    residuals = receipt["a4_residuals"]

    assert len(residuals) == 1
    residual = residuals[0]
    assert residual["residual_id"] == "a4-residual-builder-packet-not-issued"
    assert residual["stage"] == "A4"
    assert residual["reason_code"] == "builder_packet_not_issued"
    assert residual["owner_role"] == "A3_heldout"
    assert residual["retryability"] == "retryable"
    assert residual["evidence_refs"]


def test_a4_deterministic_extraction_output_hash_is_a_pure_function_of_identity_fields() -> None:
    """No source text feeds the output hash -- only already-hashed
    ``input_sha256`` and the record's own identity fields."""
    first = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "a" * 64)
    second = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "a" * 64)
    different_index = extraction.extraction_record_output_hash("db.wikipedia", 1, 42, "a" * 64)
    different_input = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "b" * 64)

    assert first == second  # reproducible
    assert first != different_index
    assert first != different_input


def test_a4_script_verifies_the_checked_in_receipt() -> None:
    receipt = _receipt()
    extraction.validate_receipt_independently(receipt)  # must not raise


def test_a4_script_refuses_a_tampered_binding_hash() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["bindings"]["a3_heldout_source_family_seal"]["sha256"] = "0" * 64

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(tampered)


def test_a4_script_refuses_a_forged_open_gate_that_contradicts_live_a3_state() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["builder_packet_gate"]["builder_packet_issued"] = True
    forged["builder_packet_gate"]["builder_eligible_source_unit_ids_known_to_a4"] = True
    forged["builder_packet_gate"]["blocked_reason_code"] = None

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


def test_a4_script_refuses_extraction_ledger_entries_while_gate_is_closed() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["extraction_ledger"] = [
        {
            "source_unit_id": "db.wikipedia",
            "span_index": 0,
            "span_byte_length": 10,
            "input_sha256": "a" * 64,
            "output_sha256": extraction.extraction_record_output_hash("db.wikipedia", 0, 10, "a" * 64),
        }
    ]

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


def test_a4_script_refuses_a_ledger_entry_with_a_wrong_output_hash() -> None:
    """Isolates ``validate_extraction_ledger_hashes`` directly -- called on
    its own (not via ``validate_receipt_independently``) so this exercises
    the output-hash recomputation itself rather than the earlier
    gate-consistency check, which would already refuse a ledger entry while
    the gate is closed regardless of whether its hash is correct."""
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["extraction_ledger"] = [
        {
            "source_unit_id": "db.wikipedia",
            "span_index": 0,
            "span_byte_length": 10,
            "input_sha256": "a" * 64,
            "output_sha256": "b" * 64,
        }
    ]

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_extraction_ledger_hashes(forged)
