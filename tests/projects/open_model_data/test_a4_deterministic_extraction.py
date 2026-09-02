"""V4 A4 deterministic extraction: frozen byte-level algorithm (unexecuted),
real packet-receipt-gated consumption of the real private builder packet.

Private-artifact-dependent paths (``consume_builder_packet``,
``verify_builder_packet_consumption_privately``, gate open/closed
transitions) are exercised against synthetic tmp_path fixtures -- mirroring
``test_a3_builder_packet.py``'s own style -- so this suite passes in a fresh
checkout with no ``batch_state/``. The checked-in production receipt is
verified separately, using only public files on disk. Every test
family_id/source_unit_id below is synthetic, never a real V4 family.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import v4_a3_builder_packet as packet
from scripts.projects.open_model_data import v4_a3_heldout_family_assignment as heldout
from scripts.projects.open_model_data import v4_a4_deterministic_extraction as extraction

ROOT = Path(__file__).resolve().parents[3]
ADMISSION = ROOT / "data/projects/open_model_data/admission"
CONTRACTS = ROOT / "data/projects/open_model_data/contracts"
RECEIPT = ADMISSION / "dataset_v4_a4_deterministic_extraction_receipt_v1.json"
SCHEMA = CONTRACTS / "dataset_v4_a4_deterministic_extraction_receipt_v1.schema.json"
A2_RECEIPT = ADMISSION / "dataset_v4_a2_source_operation_admission_receipt_v1.json"
REAL_SEAL_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json"
REAL_PACKET_RECEIPT_PATH = ADMISSION / "dataset_v4_a3_builder_packet_receipt_v1.json"
REAL_SEAL_RECEIPT = json.loads(REAL_SEAL_RECEIPT_PATH.read_text(encoding="utf-8"))

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
    "salt",
    "salt_hex",
    "private_salt",
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

UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR = {
    "algorithm_id": "v4-a4-unit-commitment-hmac-sha256-v1",
    "algorithm_version": "v1",
    "identity_dimensions": ["source_unit_id"],
    "content_blind": True,
    "formula": (
        "unit_commitment_sha256(id) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_DOMAIN + 0x00 + canonical_json({source_unit_id: id})); "
        "consumed_units_commitment_sha256(ids) = hmac_sha256(key=private_a4_salt, "
        "msg=UNIT_COMMITMENT_ROOT_DOMAIN + 0x00 + canonical_json({source_unit_ids: sorted(ids), "
        "count: len(ids)}))"
    ),
    "text_emitted": False,
    "reproducibility": "byte_stable_given_the_same_private_a4_salt_and_the_same_builder_eligible_source_unit_id_set",
}

FAMILY_IDS = [f"fam-synthetic-{index:02d}" for index in range(9)]
assert len(FAMILY_IDS) == len(REAL_SEAL_RECEIPT["source_family_registry"]["families"])


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()), set())
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value), set())
    return set()


# --- synthetic fixtures (mirror test_a3_builder_packet.py) -----------------


def _seal_receipt_shape(family_ids: list[str]) -> dict:
    receipt = copy.deepcopy(REAL_SEAL_RECEIPT)
    receipt["source_family_registry"]["families"] = [
        {
            "family_id": fid,
            "member_source_unit_ids": [f"synthetic.{fid}"],
            "source_class": "existing_corpus_collection",
            "grouping_rationale": (
                "distinct_existing_local_corpus_collection_identity_no_cross_collection_merge_evidence"
            ),
        }
        for fid in family_ids
    ]
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    algorithm["salt_commitment_sha256"] = ""
    algorithm["assignment_commitment_sha256"] = ""
    return receipt


def _sealed_receipt(salt: bytes, family_ids: list[str]) -> tuple[dict, dict]:
    result = heldout.assign(salt, family_ids)
    summary = heldout.public_commitment_summary(salt, result)
    receipt = _seal_receipt_shape(family_ids)
    algorithm = receipt["heldout_partition_seal"]["assignment_algorithm"]
    algorithm["salt_commitment_sha256"] = summary["salt_commitment_sha256"]
    algorithm["assignment_commitment_sha256"] = summary["assignment_commitment_sha256"]
    return receipt, result


def _write_seal_receipt(tmp_path: Path, receipt: dict, name: str = "seal_receipt.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(receipt))
    return path


def _seed_membership(tmp_path: Path, salt: bytes, result: dict, receipt: dict, name: str = "private") -> Path:
    membership_dir = tmp_path / name
    membership_path = membership_dir / heldout.MEMBERSHIP_FILENAME
    binding = heldout.receipt_binding_sha256(receipt)
    heldout.write_private_artifact(membership_path, salt, result, binding)
    return membership_dir


def _issue_synthetic_packet(tmp_path: Path, family_ids: list[str] = FAMILY_IDS) -> tuple[Path, Path, dict]:
    """Sealed A3 receipt + real private membership + real issued private
    packet -- everything ``consume_builder_packet`` needs, built the same
    way ``test_a3_builder_packet.py`` builds it. Never touches the real
    production family registry or the real private artifacts."""
    salt = secrets.token_bytes(32)
    receipt, result = _sealed_receipt(salt, family_ids)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)
    membership_dir = _seed_membership(tmp_path, salt, result, receipt)
    packet_dir = tmp_path / "packet"
    packet.issue_packet(seal_receipt_path, membership_dir, packet_dir)
    return seal_receipt_path, packet_dir, result


def _write_admission(tmp_path: Path, *, seal_bytes: bytes | None = None, packet_bytes: bytes | None = None) -> Path:
    admission_dir = tmp_path / "data/projects/open_model_data/admission"
    admission_dir.mkdir(parents=True)
    if seal_bytes is not None:
        (admission_dir / "dataset_v4_a3_heldout_source_family_seal_receipt_v1.json").write_bytes(seal_bytes)
    if packet_bytes is not None:
        (admission_dir / "dataset_v4_a3_builder_packet_receipt_v1.json").write_bytes(packet_bytes)
    return tmp_path


# --- frozen algorithm descriptors -------------------------------------------


def test_extraction_algorithm_descriptor_is_frozen_and_hashed() -> None:
    assert extraction.EXTRACTION_ALGORITHM_DESCRIPTOR == EXTRACTION_ALGORITHM_DESCRIPTOR
    assert (
        hashlib.sha256(_canonical_json(EXTRACTION_ALGORITHM_DESCRIPTOR).encode("utf-8")).hexdigest()
        == extraction.EXTRACTION_ALGORITHM_DESCRIPTOR_SHA256
    )


def test_unit_commitment_algorithm_descriptor_is_frozen_and_hashed() -> None:
    assert extraction.UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR == UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR
    assert (
        hashlib.sha256(_canonical_json(UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR).encode("utf-8")).hexdigest()
        == extraction.UNIT_COMMITMENT_ALGORITHM_DESCRIPTOR_SHA256
    )


def test_extraction_record_output_hash_is_pure_function_of_identity_fields() -> None:
    """No source text feeds the output hash -- only already-hashed
    ``input_sha256`` and the record's own identity fields."""
    first = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "a" * 64)
    second = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "a" * 64)
    different_index = extraction.extraction_record_output_hash("db.wikipedia", 1, 42, "a" * 64)
    different_input = extraction.extraction_record_output_hash("db.wikipedia", 0, 42, "b" * 64)

    assert first == second  # reproducible
    assert first != different_index
    assert first != different_input


# --- unit commitment: keyed, reproducible, unenumerable, domain-separated --


def test_unit_commitment_is_reproducible_given_the_same_salt() -> None:
    salt = secrets.token_bytes(32)
    assert extraction.unit_commitment_sha256(salt, "db.wikipedia") == extraction.unit_commitment_sha256(
        salt, "db.wikipedia"
    )


def test_unit_commitment_differs_by_id_and_by_salt() -> None:
    salt_a = secrets.token_bytes(32)
    salt_b = secrets.token_bytes(32)
    assert extraction.unit_commitment_sha256(salt_a, "db.wikipedia") != extraction.unit_commitment_sha256(
        salt_a, "db.literary_texts"
    )
    assert extraction.unit_commitment_sha256(salt_a, "db.wikipedia") != extraction.unit_commitment_sha256(
        salt_b, "db.wikipedia"
    )


def test_unit_commitment_resists_public_enumeration() -> None:
    """With a small, fully public family_id/source_unit_id registry, a plain
    unsalted sha256(id) would be enumerable -- an attacker just hashes every
    known candidate id and matches. Keying on a private salt closes that off."""
    salt = secrets.token_bytes(32)
    real_commitment = extraction.unit_commitment_sha256(salt, "db.wikipedia")
    for candidate in ["db.wikipedia", "db.literary_texts", "db.textbooks.public", "db.external_articles"]:
        guess = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        assert guess != real_commitment


def test_root_commitment_domain_separated_from_unit_commitment() -> None:
    salt = secrets.token_bytes(32)
    ids = ["db.wikipedia", "db.literary_texts"]
    root = extraction.root_commitment_sha256(salt, ids)
    per_unit = [extraction.unit_commitment_sha256(salt, unit_id) for unit_id in ids]
    assert root not in per_unit


def test_builder_eligible_unit_commitments_sorted_by_value_unique_and_reproducible() -> None:
    salt = secrets.token_bytes(32)
    ids = ["db.wikipedia", "db.literary_texts", "db.textbooks.public"]
    commitments = extraction.builder_eligible_unit_commitments(salt, ids)
    assert commitments == sorted(commitments)
    assert len(commitments) == len(ids)
    assert len(set(commitments)) == len(ids)
    assert extraction.builder_eligible_unit_commitments(salt, ids) == commitments


# --- builder-packet gate: public-only ---------------------------------------


def test_gate_open_against_the_real_production_receipts() -> None:
    gate = extraction.check_builder_packet_gate()
    assert gate["gate_open"] is True
    assert gate["a3_seal_complete"] is True
    assert gate["builder_packet_issued"] is True
    assert gate["packet_receipt_binding_verified"] is True
    assert gate["blocked_reason_code"] is None


def test_gate_closed_when_no_packet_receipt_present(tmp_path: Path) -> None:
    root = _write_admission(tmp_path, seal_bytes=REAL_SEAL_RECEIPT_PATH.read_bytes())
    gate = extraction.check_builder_packet_gate(root)
    assert gate["gate_open"] is False
    assert gate["builder_packet_issued"] is False
    assert gate["blocked_reason_code"] == "builder_packet_not_issued"
    assert gate["a3_seal_complete"] is True


def test_gate_open_when_packet_receipt_matches_the_live_seal(tmp_path: Path) -> None:
    root = _write_admission(
        tmp_path,
        seal_bytes=REAL_SEAL_RECEIPT_PATH.read_bytes(),
        packet_bytes=REAL_PACKET_RECEIPT_PATH.read_bytes(),
    )
    gate = extraction.check_builder_packet_gate(root)
    assert gate["gate_open"] is True
    assert gate["blocked_reason_code"] is None
    assert gate["builder_eligible_source_unit_ids_known_to_a4"] is True


def test_gate_refuses_packet_receipt_bound_to_drifted_seal_bytes(tmp_path: Path) -> None:
    root = _write_admission(
        tmp_path,
        seal_bytes=REAL_SEAL_RECEIPT_PATH.read_bytes() + b" ",
        packet_bytes=REAL_PACKET_RECEIPT_PATH.read_bytes(),
    )
    with pytest.raises(extraction.ExtractionError, match="does not match the live on-disk"):
        extraction.check_builder_packet_gate(root)


def test_gate_never_reads_the_a3_seals_own_eternal_false_temporal_field() -> None:
    """The A3 seal's own temporal_firewall.builder_packet_issued is a
    permanent, past-tense fact about the seal event -- always false. The
    live gate is open anyway, proving it is not sourced from that field."""
    assert REAL_SEAL_RECEIPT["temporal_firewall"]["builder_packet_issued"] is False
    gate = extraction.check_builder_packet_gate()
    assert gate["builder_packet_issued"] is True


# --- real builder-packet consumption (synthetic private fixtures) ----------


def test_consume_builder_packet_computes_real_reproducible_id_free_commitments(tmp_path: Path) -> None:
    seal_receipt_path, packet_dir, result = _issue_synthetic_packet(tmp_path)
    a4_private_dir = tmp_path / "a4-private"

    summary = extraction.consume_builder_packet(seal_receipt_path, packet_dir, a4_private_dir)

    assert summary["packet_consumed"] is True
    assert summary["consumed_source_unit_count"] == len(result["builder_eligible_family_ids"])
    assert len(summary["unit_commitments"]) == summary["consumed_source_unit_count"]
    serialized = json.dumps(summary)
    assert not any(fid in serialized for fid in FAMILY_IDS)
    assert not any(f"synthetic.{fid}" in serialized for fid in FAMILY_IDS)

    salt_path = a4_private_dir / extraction.A4_SALT_FILENAME
    assert salt_path.is_file()
    assert stat.S_IMODE(salt_path.stat().st_mode) == heldout.PRIVATE_FILE_MODE

    # Rerunning against the same private artifacts (verify-only path) reproduces exactly.
    again = extraction.consume_builder_packet(seal_receipt_path, packet_dir, a4_private_dir)
    assert again == summary


def test_consume_builder_packet_refuses_when_private_packet_missing(tmp_path: Path) -> None:
    salt = secrets.token_bytes(32)
    receipt, _ = _sealed_receipt(salt, FAMILY_IDS)
    seal_receipt_path = _write_seal_receipt(tmp_path, receipt)

    with pytest.raises(heldout.AssignmentError, match="missing"):
        extraction.consume_builder_packet(seal_receipt_path, tmp_path / "no-packet", tmp_path / "a4-private")


def test_consume_builder_packet_refuses_a_tampered_private_packet(tmp_path: Path) -> None:
    seal_receipt_path, packet_dir, _ = _issue_synthetic_packet(tmp_path)
    packet_path = packet_dir / packet.PACKET_FILENAME
    payload = json.loads(packet_path.read_text(encoding="utf-8"))
    payload["builder_eligible_source_unit_ids"] = ["synthetic.tampered"]
    os.chmod(packet_path, 0o600)
    packet_path.write_text(json.dumps(payload))
    os.chmod(packet_path, heldout.PRIVATE_FILE_MODE)

    with pytest.raises(extraction.ExtractionError, match="does not reproduce"):
        extraction.consume_builder_packet(seal_receipt_path, packet_dir, tmp_path / "a4-private")


def test_consume_builder_packet_salt_artifact_refuses_drift_on_rerun(tmp_path: Path) -> None:
    """A second consumption against *different* seal/packet content but the
    same A4 salt path must refuse (drift), not silently regenerate -- mirrors
    A3's own fail-closed rerun discipline for the membership artifact."""
    seal_receipt_path, packet_dir, _ = _issue_synthetic_packet(tmp_path)
    a4_private_dir = tmp_path / "a4-private"
    extraction.consume_builder_packet(seal_receipt_path, packet_dir, a4_private_dir)

    # A genuinely different family_id registry -- not just a different salt --
    # so the seal's receipt_binding_sha256 (which covers source_family_registry
    # but not the salt-dependent commitment values) actually differs.
    other_family_ids = [f"fam-synthetic-b-{index:02d}" for index in range(9)]
    other_root = tmp_path / "other"
    other_root.mkdir()
    other_seal_receipt_path, other_packet_dir, _ = _issue_synthetic_packet(other_root, other_family_ids)
    with pytest.raises(extraction.ExtractionError, match="drift"):
        extraction.consume_builder_packet(other_seal_receipt_path, other_packet_dir, a4_private_dir)


def test_verify_builder_packet_consumption_privately_reproduces(tmp_path: Path) -> None:
    seal_receipt_path, packet_dir, _ = _issue_synthetic_packet(tmp_path)
    a4_private_dir = tmp_path / "a4-private"
    summary = extraction.consume_builder_packet(seal_receipt_path, packet_dir, a4_private_dir)

    receipt = {"builder_packet_consumption": summary}
    extraction.verify_builder_packet_consumption_privately(receipt, seal_receipt_path, packet_dir, a4_private_dir)


def test_verify_builder_packet_consumption_privately_detects_tampered_commitment(tmp_path: Path) -> None:
    seal_receipt_path, packet_dir, _ = _issue_synthetic_packet(tmp_path)
    a4_private_dir = tmp_path / "a4-private"
    summary = extraction.consume_builder_packet(seal_receipt_path, packet_dir, a4_private_dir)

    tampered = copy.deepcopy(summary)
    tampered["unit_commitments"] = sorted([*tampered["unit_commitments"][1:], "0" * 64])
    receipt = {"builder_packet_consumption": tampered}
    with pytest.raises(extraction.ExtractionError, match="does not reproduce"):
        extraction.verify_builder_packet_consumption_privately(receipt, seal_receipt_path, packet_dir, a4_private_dir)


# --- real production receipt: schema + independent verification ------------


def _receipt() -> dict[str, Any]:
    return _load(RECEIPT)


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _errors(value: dict[str, Any]) -> list[object]:
    return sorted(_validator().iter_errors(value), key=lambda error: list(error.path))


def test_a4_extraction_schema_and_v4_control_binding() -> None:
    receipt = _receipt()

    assert not _errors(receipt)
    assert receipt["controlling_outcome_sha256"] == V4_SHA256
    assert receipt["text_free"] is True
    assert receipt["status"] == "A4_BUILDER_PACKET_CONSUMED_GATE_OPEN_TEXT_FREE_NO_COMPLEMENT_ENUMERATION"

    changed = copy.deepcopy(receipt)
    changed["controlling_outcome_sha256"] = "0" * 64
    assert _errors(changed)


def test_a4_extraction_bindings_match_exact_inputs() -> None:
    receipt = _receipt()

    for binding in receipt["bindings"].values():
        bound_path = ROOT / binding["path"]
        assert bound_path.is_file()
        assert hashlib.sha256(bound_path.read_bytes()).hexdigest() == binding["sha256"]

    assert receipt["bindings"]["a3_heldout_source_family_seal"]["path"] == str(REAL_SEAL_RECEIPT_PATH.relative_to(ROOT))
    assert receipt["bindings"]["a3_builder_packet_receipt"]["path"] == str(REAL_PACKET_RECEIPT_PATH.relative_to(ROOT))


def test_a4_extraction_algorithm_still_frozen_and_unexecuted() -> None:
    receipt = _receipt()
    algorithm = receipt["extraction_algorithm"]
    declared = {k: algorithm[k] for k in EXTRACTION_ALGORITHM_DESCRIPTOR}

    assert declared == EXTRACTION_ALGORITHM_DESCRIPTOR
    assert (
        algorithm["algorithm_descriptor_sha256"]
        == hashlib.sha256(_canonical_json(EXTRACTION_ALGORITHM_DESCRIPTOR).encode("utf-8")).hexdigest()
    )
    assert algorithm["text_emitted"] is False
    assert receipt["extraction_ledger"] == []
    assert receipt["execution_counters"]["source_units_extracted"] == 0
    assert receipt["execution_counters"]["spans_extracted"] == 0
    assert receipt["execution_counters"]["dataset_rows_emitted"] == 0


def test_a4_builder_packet_gate_is_open_and_matches_live_public_state() -> None:
    receipt = _receipt()
    gate = receipt["builder_packet_gate"]

    assert gate["a3_seal_complete"] is True
    assert gate["builder_packet_issued"] is True
    assert gate["builder_eligible_source_unit_ids_known_to_a4"] is True
    assert gate["packet_receipt_binding_verified"] is True
    assert gate["blocked_reason_code"] is None
    assert gate["owner_role"] == "A3_heldout"

    live_gate = extraction.check_builder_packet_gate()
    assert live_gate["gate_open"] is True
    assert live_gate["blocked_reason_code"] is None


def test_a4_builder_packet_consumption_is_real_and_id_free() -> None:
    receipt = _receipt()
    consumption = receipt["builder_packet_consumption"]

    assert consumption["packet_consumed"] is True
    assert consumption["consumed_source_unit_count"] == 8
    assert len(consumption["unit_commitments"]) == 8
    assert consumption["unit_commitments"] == sorted(consumption["unit_commitments"])
    assert len(set(consumption["unit_commitments"])) == 8

    packet_receipt = _load(REAL_PACKET_RECEIPT_PATH)
    assert consumption["consumed_source_unit_count"] == packet_receipt["packet"]["builder_eligible_source_unit_count"]


def test_a4_extraction_receipt_never_names_a_held_out_family_or_source_unit_or_source_text() -> None:
    receipt = _receipt()
    serialized = json.dumps(receipt, ensure_ascii=False, sort_keys=True)

    assert not _all_keys(receipt) & FORBIDDEN_KEYS
    assert "fam-" not in serialized  # A3 family_ids never appear in a builder-facing receipt
    assert not _all_keys(receipt) & {"salt", "salt_hex", "private_salt", "heldout_family_pool"}
    for family in REAL_SEAL_RECEIPT["source_family_registry"]["families"]:
        for unit_id in family["member_source_unit_ids"]:
            assert unit_id not in serialized  # no builder-eligible id, even by elimination


def test_a4_extraction_carries_forward_every_a2_residual_unchanged() -> None:
    receipt = _receipt()
    a2_receipt = _load(A2_RECEIPT)

    a2_residual_ids = {entry["residual_id"] for entry in a2_receipt["residuals"]}
    carried_ids = {entry["residual_id"] for entry in receipt["a2_residuals_carried_forward"]}

    assert carried_ids == a2_residual_ids
    for entry in receipt["a2_residuals_carried_forward"]:
        assert entry["origin_stage"] == "A2"
        assert entry["status"] == "unresolved_carried_to_a4"


def test_a4_residual_names_the_byte_level_extraction_gap_not_any_source() -> None:
    receipt = _receipt()
    residuals = receipt["a4_residuals"]

    assert len(residuals) == 1
    residual = residuals[0]
    assert residual["residual_id"] == "a4-residual-byte-level-extraction-pending-source-ingestion"
    assert residual["stage"] == "A4"
    assert residual["reason_code"] == "source_byte_content_not_yet_ingested_for_v4"
    assert residual["owner_role"] == "V4_source_byte_ingestion"
    assert residual["retryability"] == "retryable"
    assert residual["evidence_refs"]
    assert "fam-" not in residual["next_action"]


def test_a4_script_verifies_the_checked_in_receipt() -> None:
    receipt = _receipt()
    extraction.validate_receipt_independently(receipt)  # must not raise


def test_a4_script_refuses_a_tampered_binding_hash() -> None:
    receipt = _receipt()
    tampered = copy.deepcopy(receipt)
    tampered["bindings"]["a3_heldout_source_family_seal"]["sha256"] = "0" * 64

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(tampered)


def test_a4_script_refuses_a_forged_closed_gate_that_contradicts_live_public_state() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["builder_packet_gate"]["builder_packet_issued"] = False
    forged["builder_packet_gate"]["builder_eligible_source_unit_ids_known_to_a4"] = False
    forged["builder_packet_gate"]["blocked_reason_code"] = "builder_packet_not_issued"

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


def test_a4_script_refuses_extraction_ledger_entries_even_though_gate_is_open() -> None:
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
    """Isolates ``validate_extraction_ledger_hashes`` directly (not via
    ``validate_receipt_independently``, which would already refuse a
    non-empty ledger regardless of hash correctness)."""
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


def test_a4_script_refuses_consumption_count_drift_against_public_packet_receipt() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["builder_packet_consumption"]["consumed_source_unit_count"] = 999

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


def test_a4_script_refuses_duplicate_unit_commitments() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["builder_packet_consumption"]["unit_commitments"][1] = forged["builder_packet_consumption"]["unit_commitments"][0]

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


def test_a4_script_refuses_unsorted_unit_commitments() -> None:
    receipt = _receipt()
    forged = copy.deepcopy(receipt)
    forged["builder_packet_consumption"]["unit_commitments"] = list(
        reversed(forged["builder_packet_consumption"]["unit_commitments"])
    )

    with pytest.raises(extraction.ExtractionError):
        extraction.validate_receipt_independently(forged)


# --- CLI ---------------------------------------------------------------


def test_cli_default_verify_prints_gate_and_status(capsys: pytest.CaptureFixture) -> None:
    extraction.main([])
    printed = json.loads(capsys.readouterr().out)
    assert printed["status"] == "A4_BUILDER_PACKET_CONSUMED_GATE_OPEN_TEXT_FREE_NO_COMPLEMENT_ENUMERATION"
    assert printed["builder_packet_gate"]["gate_open"] is True


def test_cli_consume_wired_to_path_overrides(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    seal_receipt_path, packet_dir, _ = _issue_synthetic_packet(tmp_path)
    a4_private_dir = tmp_path / "a4-private"

    extraction.main(
        [
            "--consume",
            "--seal-receipt", str(seal_receipt_path),
            "--packet-dir", str(packet_dir),
            "--a4-private-dir", str(a4_private_dir),
        ]
    )
    printed = json.loads(capsys.readouterr().out)
    assert printed["packet_consumed"] is True
    assert not any(fid in json.dumps(printed) for fid in FAMILY_IDS)
