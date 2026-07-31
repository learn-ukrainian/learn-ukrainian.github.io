from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness import build_v02_review_packet as packet
from scripts.projects.ua_eval_harness import validate_v02_annotations as validator

ROOT = Path(__file__).resolve().parents[1]


def _reviewer(number: int) -> dict[str, object]:
    return {"reviewer_id": f"test-fixture-reviewer-{number}", "human": True, "ukrainian_qualification": "credentialed_ukrainian_linguist", "qualification_evidence": "synthetic test-fixture credential", "test_fixture": True}


def _review(number: int, proposed: str) -> dict[str, object]:
    return {"reviewer": _reviewer(number), "proposed_decision": proposed, "uncertainty": ["synthetic test-fixture uncertainty"], "source_citations": [{"kind": "primary_source", "locator": "test fixture", "supports": "test-only source context"}], "rationale": "Synthetic test-fixture blind-review rationale."}


def _decision(row: dict[str, object], *, conflict: bool = True) -> dict[str, object]:
    receipts = row["frozen_receipts"]
    assert isinstance(receipts, dict)
    reviews = [_review(1, "valid_alternative"), _review(2, "unresolved" if conflict else "valid_alternative")]
    return {"schema_version": validator.DECISION_SCHEMA, "item_id": row["item_id"], "source_sha256": receipts["source_sha256"], "review_state": "unresolved" if conflict else "adjudicated", "decision": "unresolved" if conflict else "valid_alternative", "uncertainty": ["synthetic test-fixture final uncertainty"], "source_citations": [{"kind": "primary_source", "locator": "test fixture", "supports": "test-only final context"}], "rationale": "Synthetic test-fixture final rationale.", "first_pass_reviews": reviews, "final_resolution": {"kind": "unresolved_conflict" if conflict else "first_pass_agreement"}}


def _decisions(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [_decision(row) for row in rows]


def _third_human_decision(row: dict[str, object]) -> dict[str, object]:
    decision = _decision(row)
    third_review = _review(3, "valid_alternative")
    decision["review_state"] = "adjudicated"
    decision["decision"] = third_review["proposed_decision"]
    decision["uncertainty"] = third_review["uncertainty"]
    decision["source_citations"] = third_review["source_citations"]
    decision["rationale"] = third_review["rationale"]
    decision["final_resolution"] = {"kind": "third_human_adjudication", "third_review": third_review}
    return decision


def test_packet_is_byte_stable_and_preserves_freeze(tmp_path: Path) -> None:
    freeze = ROOT / "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json"
    before = hashlib.sha256(freeze.read_bytes()).hexdigest()
    first, second = tmp_path / "first.jsonl", tmp_path / "second.jsonl"
    rows = packet.write_packet(first)
    packet.write_packet(second)
    assert first.read_bytes() == second.read_bytes()
    assert len(rows) == 14 == len({row["item_id"] for row in rows})
    signals = [set(row["coordinator_priority_metadata"]["signals"]) for row in rows]
    assert sum("needs_ua_review" in value for value in signals) == 14
    assert sum("possible_benchmark_defect" in value for value in signals) == 12
    assert sum("protected_variation_risk" in value for value in signals) == 3
    assert all(row["review_state"] == "pending" and row["decision"] is None for row in rows)
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered", "unqualified", "contradictory"])
def test_validator_rejects_unsafe_decision_imports(mutation: str) -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    if mutation == "missing":
        decisions.pop()
    elif mutation == "duplicate":
        decisions[1]["item_id"] = decisions[0]["item_id"]
    elif mutation == "reordered":
        decisions[0], decisions[1] = decisions[1], decisions[0]
    elif mutation == "unqualified":
        decisions[0]["first_pass_reviews"][0]["reviewer"]["human"] = False
    else:
        decisions[0]["review_state"] = "adjudicated"
    with pytest.raises(validator.AnnotationError):
        validator.validate(rows, decisions, allow_test_fixtures=True)


@pytest.mark.parametrize("field, value", [("extra", "forbidden"), ("kind", "invented")])
def test_validator_rejects_structural_schema_violation(field: str, value: str) -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0]["source_citations"][0][field] = value
    with pytest.raises(validator.AnnotationError, match="schema violation"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_rejects_missing_second_reviewer() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0]["first_pass_reviews"].pop()
    with pytest.raises(validator.AnnotationError, match="schema violation"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_rejects_duplicate_first_pass_reviewer_id() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0]["first_pass_reviews"][1]["reviewer"]["reviewer_id"] = "test-fixture-reviewer-1"
    with pytest.raises(validator.AnnotationError, match="distinct identities"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_rejects_conflict_without_valid_resolution() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0]["final_resolution"] = {"kind": "first_pass_agreement"}
    with pytest.raises(validator.AnnotationError, match="third adjudication or unresolved"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_accepts_unresolved_conflict_from_two_test_reviewers() -> None:
    rows = packet.build_rows()
    validator.validate(rows, _decisions(rows), allow_test_fixtures=True)


def test_validator_rejects_identity_only_third_human_resolution() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0]["final_resolution"] = {"kind": "third_human_adjudication", "third_reviewer": _reviewer(3)}
    with pytest.raises(validator.AnnotationError, match="schema violation"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_rejects_arbitrary_final_after_third_review() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0] = _third_human_decision(rows[0])
    decisions[0]["decision"] = "model_error"
    with pytest.raises(validator.AnnotationError, match="final decision must equal"):
        validator.validate(rows, decisions, allow_test_fixtures=True)


def test_validator_accepts_attributable_distinct_third_human_adjudication() -> None:
    rows = packet.build_rows()
    decisions = _decisions(rows)
    decisions[0] = _third_human_decision(rows[0])
    validator.validate(rows, decisions, allow_test_fixtures=True)


def test_test_fixture_reviewers_are_not_importable_as_real_decisions() -> None:
    rows = packet.build_rows()
    with pytest.raises(validator.AnnotationError, match="test-fixture reviewer"):
        validator.validate(rows, _decisions(rows))


def test_packet_file_is_jsonl() -> None:
    path = ROOT / "data/projects/ua_eval_harness/v0.2/review_packet_priority_v1.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    packet.validate_packet_rows(rows)
    assert [packet.canonical(row) for row in rows] == [
        packet.canonical(row) for row in packet.build_rows()
    ]


def test_packet_schema_rejects_nonpending_row() -> None:
    rows = packet.build_rows()
    rows[0]["decision"] = "model_error"
    with pytest.raises(packet.PacketError, match="packet schema violation"):
        packet.validate_packet_rows(rows)
