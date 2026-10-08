"""Registry/adoption refusal tests. All approvals here are synthetic, never adoption proof."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import activity_rubric as ar

ROOT = Path(__file__).resolve().parents[2]


def install_synthetic_approval(root: Path) -> dict:
    """Controlled fixture bytes only; no genuine approver receipt is claimed."""
    data = (ROOT / ar.RUBRIC_PATH).read_bytes()
    candidate = root / ar.RUBRIC_PATH
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(data)
    record = {
        "approval_version": 1,
        "status": "approved",
        "rubric_sha256": hashlib.sha256(data).hexdigest(),
        "author_model": "gpt-6.1-sol",
        "approver_model": "claude-opus-5-5",
        "approval_reference": "synthetic-test-only://fixture/approval",
        "approval_sha256": "1" * 64,
        "synthetic_test_only": True,
    }
    (root / ar.APPROVAL_PATH).write_text(yaml.safe_dump(record))
    return ar.approved_pins("a1", root)


@pytest.fixture
def rubric():
    return ar.validate_rubric((ROOT / ar.RUBRIC_PATH).read_bytes())


def test_complete_inventory_alias_and_placement(rubric):
    assert len(rubric["rows"]) == 20
    assert sum(row["verdict"] != "forbidden" for row in rubric["rows"]) == 19
    assert [row["id"] for row in rubric["rows"]] == [f"A1-ACT-{n:03d}" for n in range(1, 21)]
    plan = {"lessons": [{"n": 1, "activities": [{"id": "x", "type": "multiple-choice"}]}]}
    assert ar.activity_table(plan, rubric)[0]["row"] == "A1-ACT-016"
    assert ar.activity_table(plan, rubric, 1)[0]["type"] == "multiple-choice"
    assert ar.is_a1("a1") and ar.is_a1("a1-bridge") and not ar.is_a1("a2")
    with pytest.raises(ar.ActivityRubricError, match="no requested lesson"):
        ar.activity_table(plan, rubric, 2)


@pytest.mark.parametrize("typ", ["letter-grid", "observe", "phrase-table", "watch-and-repeat"])
def test_unscored_support_applicability_is_preserved_in_actual_table(rubric, typ):
    row = next(row for row in rubric["rows"] if row["type"] == typ)
    assert row["verdict"] in {"scaffold", "unscored_support"}
    plan = {"lessons": [{"n": 1, "activities": [{"id": "support", "type": typ}]}]}
    (entry,) = ar.activity_table(plan, rubric)
    assert "A1-C01" in entry["clauses"] and "A1-B05" in entry["clauses"]
    assert "A1-C04" not in entry["clauses"] and "A1-B06" not in entry["clauses"]
    assert row["applicability"]["A1-B05"]["reason"]


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("missing", "20 schema"),
        ("duplicate-row", "duplicate row"),
        ("duplicate-type", "duplicate row"),
        ("duplicate-clause", "duplicate clause"),
        ("placement", "placement"),
        ("classify", "classify"),
        ("applicability", "fixed applicability"),
        ("reason", "reason required"),
        ("source", "unknown source"),
        ("private", "private_permission"),
        ("empty-source", "source role"),
        ("empty-conditions", "conditions"),
        ("row-id", "invalid row"),
        ("clause-id", "invalid clause"),
        ("empty-clause", "text and references"),
        ("version", "version 1"),
        ("verdict", "invalid verdict"),
        ("sources", "source ledger"),
    ],
)
def test_registry_refusals(rubric, mutation, match):
    doc = copy.deepcopy(rubric)
    if mutation == "missing":
        doc["rows"].pop()
    elif mutation == "duplicate-row":
        doc["rows"][1]["id"] = doc["rows"][0]["id"]
    elif mutation == "duplicate-type":
        doc["rows"][1]["type"] = doc["rows"][0]["type"]
    elif mutation == "duplicate-clause":
        doc["clauses"].append(doc["clauses"][0])
    elif mutation == "placement":
        doc["rows"][0]["placement"] = "inline"
    elif mutation == "classify":
        doc["rows"][1]["verdict"] = "conditional"
    elif mutation == "applicability":
        doc["rows"][0]["applicability"].pop("A1-C01")
    elif mutation == "reason":
        doc["rows"][0]["applicability"]["A1-C01"]["reason"] = ""
    elif mutation == "source":
        doc["rows"][0]["references"] = ["missing"]
    elif mutation == "private":
        doc["sources"]["POLICY"]["rights"] = "private_permission"
    elif mutation == "empty-source":
        doc["sources"]["POLICY"]["locator"] = ""
    elif mutation == "empty-conditions":
        doc["rows"][0]["conditions"] = ""
    elif mutation == "row-id":
        doc["rows"][0]["id"] = "invalid"
    elif mutation == "clause-id":
        doc["clauses"][0]["id"] = "invalid"
    elif mutation == "empty-clause":
        doc["clauses"][0]["text"] = ""
    elif mutation == "version":
        doc["rubric_version"] = 2
    elif mutation == "verdict":
        doc["rows"][0]["verdict"] = "approved"
    elif mutation == "sources":
        doc.pop("sources")
    with pytest.raises(ar.ActivityRubricError, match=match):
        ar.validate_rubric(yaml.safe_dump(doc).encode())


@pytest.mark.parametrize("data", [b"[]", b"[", b"\xff"])
def test_malformed_yaml(data):
    with pytest.raises(ar.ActivityRubricError):
        ar.validate_rubric(data)


@pytest.mark.parametrize("typ", ["classify", "unmapped"])
def test_forbidden_or_unknown_activity(rubric, typ):
    with pytest.raises(ar.ActivityRubricError):
        ar.activity_table({"lessons": [{"n": 1, "activities": [{"id": "x", "type": typ}]}]}, rubric)


def test_duplicate_activity_ids(rubric):
    activity = {"id": "x", "type": "quiz"}
    with pytest.raises(ar.ActivityRubricError, match="duplicate"):
        ar.activity_table({"lessons": [{"n": 1, "activities": [activity, activity]}]}, rubric)


def test_adoption_pending_and_no_silent_refresh(tmp_path):
    pins = install_synthetic_approval(tmp_path)
    assert ar.pinned_rubric("a1", pins, lambda p: (tmp_path / p).read_bytes())
    path = tmp_path / ar.RUBRIC_PATH
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ar.ActivityRubricError, match="changed"):
        ar.pinned_rubric("a1", pins, lambda p: (tmp_path / p).read_bytes())
    with pytest.raises(ar.ActivityRubricError, match="approved digest"):
        ar.approved_pins("a1", tmp_path)
    pending = (ROOT / ar.APPROVAL_PATH).read_bytes()
    with pytest.raises(ar.ActivityRubricError, match="pending"):
        ar.validate_approval(pending, pins["activity_rubric"]["sha256"])


@pytest.mark.parametrize("key", ["author_model", "approver_model", "approval_reference", "approval_sha256"])
def test_missing_designated_approval_provenance(tmp_path, key):
    install_synthetic_approval(tmp_path)
    record = yaml.safe_load((tmp_path / ar.APPROVAL_PATH).read_bytes())
    record[key] = None
    with pytest.raises(ar.ActivityRubricError, match="designated"):
        ar.validate_approval(yaml.safe_dump(record).encode(), record["rubric_sha256"])


def test_missing_and_a2_pins(tmp_path):
    with pytest.raises(ar.ActivityRubricError, match="unavailable"):
        ar.approved_pins("a1", tmp_path)
    with pytest.raises(ar.ActivityRubricError, match="missing"):
        ar.pin_contract("a1", {})
    pins = install_synthetic_approval(tmp_path)
    with pytest.raises(ar.ActivityRubricError, match="A1-only"):
        ar.pin_contract("a2", pins)
    assert ar.approved_pins("a2", tmp_path) == {}
    assert ar.pinned_rubric("a2", {}, lambda _: pytest.fail("A2 read")) is None


def test_alias_contract_and_malformed_pin_mapping(rubric):
    rubric["aliases"] = {}
    with pytest.raises(ar.ActivityRubricError, match="aliases"):
        ar.validate_rubric(yaml.safe_dump(rubric).encode())
    with pytest.raises(ar.ActivityRubricError, match="missing A1 pin mapping"):
        ar.pin_contract("a1", None)
    ar.pin_contract("a2", None)


@pytest.mark.parametrize("kind", ["lesson", "plan"])
def test_manifest_schema_a1_requires_both_a2_refuses_both(kind):
    schema = json.loads((ROOT / f"schemas/{kind}-review-manifest-v1.schema.json").read_bytes())
    # Exercise the new conditional in isolation; old schema fixtures cover its other fields.
    rule = {"$defs": schema["$defs"], **schema["allOf"][-1]}
    validator = Draft202012Validator(rule)
    pin = {"path": ar.RUBRIC_PATH, "sha256": "1" * 64}
    assert list(validator.iter_errors({"level": "a1", "inputs": {}}))
    assert not list(validator.iter_errors({"level": "a2", "inputs": {}}))
    assert list(validator.iter_errors({"level": "a2", "inputs": {"activity_rubric": pin}}))
    assert not list(
        validator.iter_errors({"level": "a1", "inputs": {"activity_rubric": pin, "activity_rubric_approval": pin}})
    )


def test_existing_forbidden_gate_cites_stable_row():
    from scripts.build.fresh.draft_schema import _activity_fresh_constraint_errors
    from scripts.build.fresh.runner import check_4_activities

    errors = _activity_fresh_constraint_errors({"activities": [{"id": "x"}]}, "a1", None, {"x": "classify"})
    assert "A1-ACT-002" in errors[0].reason
    result, _ = check_4_activities(
        {"activities": [{"id": "x"}]}, {"activities": [{"id": "x", "type": "classify"}]}, {}, {}, level="a1"
    )
    assert "A1-ACT-002" in result["reason"]
    assert result["code"] == "classify_forbidden"
