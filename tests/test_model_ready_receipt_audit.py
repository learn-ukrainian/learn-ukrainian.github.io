from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import audit_model_ready_receipts as audit

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_RECEIPT = ROOT / "data/projects/open_model_data/model_views/model_ready_product_audit_v1.json"


def rebind(receipt: dict[str, object]) -> None:
    material = dict(receipt)
    material.pop("audit_id")
    receipt["audit_id"] = "model-ready-product-audit:" + hashlib.sha256(
        audit.canonical_json(material).encode("utf-8")
    ).hexdigest()


def mutate(receipt: dict[str, object], name: str) -> None:
    truth = receipt["product_truth"]  # type: ignore[index]
    inventory = truth["corpus_inventory"]  # type: ignore[index]
    silver = truth["silver"]  # type: ignore[index]
    lanes = silver["lanes"]  # type: ignore[index]
    if name == "faithful_count":
        truth["continued_pretraining"]["faithful"]["records"] = 1  # type: ignore[index]
    elif name == "modern_count":
        truth["continued_pretraining"]["modern"]["records"] = 1  # type: ignore[index]
    elif name == "silver_count":
        silver["records"] = 1  # type: ignore[index]
    elif name == "evaluation_count":
        truth["heldout_evaluation"]["records"] = 1  # type: ignore[index]
    elif name == "inventory_rows":
        inventory["public_or_external_source"]["database_rows"] = 1  # type: ignore[index]
    elif name == "inventory_words":
        inventory["public_or_external_source"]["lexical_words"] = 1  # type: ignore[index]
    elif name == "inventory_gate_interpretation":
        inventory["interpretation"] = "the historical gate denies later capability rows"  # type: ignore[index]
    elif name == "disposition":
        silver["distributions"]["by_disposition"]["unresolved"] -= 1  # type: ignore[index]
    elif name == "evidence_grade":
        silver["distributions"]["by_evidence_grade"]["unresolved"] -= 1  # type: ignore[index]
    elif name == "source_family":
        silver["distributions"]["by_source_family"]["literary"] -= 1  # type: ignore[index]
    elif name == "period":
        silver["distributions"]["by_period"]["modern"] -= 1  # type: ignore[index]
    elif name == "genre":
        silver["distributions"]["by_genre"]["poetry"] -= 1  # type: ignore[index]
    elif name == "genre_reallocation":
        silver["distributions"]["by_genre"]["poetry"] -= 1  # type: ignore[index]
        silver["distributions"]["by_genre"]["chronicle"] += 1  # type: ignore[index]
    elif name == "register":
        silver["distributions"]["by_register"]["literary"] -= 1  # type: ignore[index]
    elif name == "lane_state":
        lanes["correction_instruction"]["state"] = "emitted"  # type: ignore[index]
    elif name == "lane_eligibility":
        lanes["pairwise_preference"]["eligible"] = 1  # type: ignore[index]
    elif name == "lane_emission":
        lanes["quality_filter"]["emitted"] = 1  # type: ignore[index]
    elif name == "lane_blocked":
        lanes["correction_instruction"]["blocked"] = 1  # type: ignore[index]
    elif name == "lane_artifact":
        lanes["pairwise_preference"]["artifact"]["bytes"] = 1  # type: ignore[index]
    elif name == "empty_lane_explanation":
        receipt["empty_lane_explanation"]["interpretation"] = "source material is unusable"  # type: ignore[index]
    elif name == "evaluation_isolation":
        truth["heldout_evaluation"]["isolation_verified"] = False  # type: ignore[index]
    elif name == "silver_eligibility":
        silver["record_learning_or_export_eligible"] = True  # type: ignore[index]
    elif name == "heldout_eligibility":
        truth["heldout_evaluation"]["learning_eligible"] = True  # type: ignore[index]
    elif name == "availability":
        receipt["payload_availability"]["faithful_continued_pretraining"]["state"] = "available"  # type: ignore[index]
    elif name == "release_status":
        receipt["public_release_and_redistribution"]["status"] = "public"  # type: ignore[index]
    elif name == "release_permission":
        receipt["public_release_and_redistribution"]["redistribution_permission_evidence"] = "permitted"  # type: ignore[index]
    elif name == "safety":
        receipt["safety_claims"]["training_performed"] = True  # type: ignore[index]
    elif name == "phase":
        receipt["phase_1_entry_conditions"]["state"] = "blocked"  # type: ignore[index]
    elif name == "phase_deliverable":
        receipt["phase_1_remaining_deliverables"].pop()  # type: ignore[index]
    elif name == "direct_input_hash":
        receipt["direct_inputs"]["data/projects/open_model_data/silver/language_contact_silver_receipt_v1.json"]["sha256"] = "0" * 64  # type: ignore[index]
    elif name == "unknown_property":
        receipt["unexpected"] = True
    else:
        raise AssertionError(name)


def test_current_receipt_reproduces_and_is_schema_valid(tmp_path: Path) -> None:
    inputs = audit.default_inputs()
    receipt = audit.build_receipt(inputs)
    tracked = json.loads(CANONICAL_RECEIPT.read_text(encoding="utf-8"))

    assert receipt == tracked
    audit.validate_receipt(receipt, inputs.schema, inputs)
    schema = json.loads(inputs.schema.read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(receipt))

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    audit.write_receipt(first, receipt)
    audit.write_receipt(second, audit.build_receipt(inputs))
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().endswith(b"\n")


@pytest.mark.parametrize(
    "name",
    [
        "faithful_count", "modern_count", "silver_count", "evaluation_count", "inventory_rows", "inventory_words", "inventory_gate_interpretation",
        "disposition", "evidence_grade", "source_family", "period", "genre", "genre_reallocation", "register",
        "lane_state", "lane_eligibility", "lane_emission", "lane_blocked", "lane_artifact", "empty_lane_explanation",
        "evaluation_isolation", "silver_eligibility", "heldout_eligibility", "availability",
        "release_status", "release_permission", "safety", "phase", "phase_deliverable", "direct_input_hash", "unknown_property",
    ],
)
def test_planted_mutations_are_rejected(name: str) -> None:
    inputs = audit.default_inputs()
    receipt = audit.build_receipt(inputs)
    mutate(receipt, name)
    rebind(receipt)

    with pytest.raises(audit.AuditError):
        audit.validate_receipt(receipt, inputs.schema, inputs)


def test_cli_writes_and_verifies_existing_receipt(tmp_path: Path) -> None:
    target = tmp_path / "receipt.json"

    assert audit.main(["--output", str(target)]) == 0
    assert audit.main(["--output", str(target), "--verify-existing"]) == 0
    target.write_text("{}\n", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        audit.main(["--output", str(target), "--verify-existing"])
    assert excinfo.value.code == 2


def test_schema_is_strict() -> None:
    schema = json.loads(audit.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["product_truth"]["additionalProperties"] is False
