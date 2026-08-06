"""Hermetic tamper tests for the text-free Phase 3 disposition adapter."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from scripts.projects.open_model_data import phase3_source_dispositions as dispositions
from scripts.projects.open_model_data.phase3_source_universe import canonical_json


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(canonical_json(value), encoding="utf-8")


@pytest.fixture
def tiny_totals(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    totals = {family_id: 1 for family_id in dispositions.FAMILY_IDS}
    totals["other_normative_style_inventory"] = 0
    monkeypatch.setattr(dispositions, "FAMILY_TOTALS", totals)
    return totals


def _freeze(tmp_path: Path, totals: dict[str, int]) -> tuple[Path, dict[str, list[dict[str, str]]]]:
    freeze = tmp_path / "freeze"
    freeze.mkdir()
    unit_rows: dict[str, list[dict[str, str]]] = {}
    families = []
    for family_id in sorted(totals):
        rows = []
        ledger_records = []
        for ordinal in range(totals[family_id]):
            locator = {"kind": "opaque", "ordinal": ordinal}
            record = {
                "family_id": family_id,
                "unit_id": f"unit.{family_id}.{_sha(f'{family_id}:id:{ordinal}')}",
                "unit_sha256": _sha(f"{family_id}:unit:{ordinal}"),
                "locator": locator,
            }
            rows.append({
                "unit_id": record["unit_id"],
                "unit_sha256": record["unit_sha256"],
                "locator_sha256": _sha(canonical_json(locator)),
            })
            ledger_records.append(record)
        (freeze / f"{family_id}.units.jsonl").write_text(
            "".join(canonical_json(record) + "\n" for record in ledger_records), encoding="utf-8"
        )
        ledger = freeze / f"{family_id}.units.jsonl"
        families.append({
            "family_id": family_id,
            "ledger_file": ledger.name,
            "ledger_sha256": dispositions.sha256_file(ledger),
            "unit_count": totals[family_id],
        })
        unit_rows[family_id] = rows
    _json(freeze / dispositions.FREEZE_RECEIPT_FILE, {
        "schema_version": "phase3_source_universe_freeze_v1", "text_free": True, "families": families,
    })
    return freeze, unit_rows


def _role_contract(path: Path) -> None:
    _json(path, {
        "seats": [
            {"role_id": "rule_author_extractor", "assignment_state": "assigned_verified", "controller_identity_attested": True, "controller_identity_id": "controller.extractor"},
            {"role_id": "ukrainian_source_reviewer", "assignment_state": "assigned_verified", "controller_identity_attested": True, "controller_identity_id": "controller.source_reviewer"},
        ],
        "task_bindings": [
            {"role_id": "rule_author_extractor", "reserved_task_id": "task.extractor", "controller_identity_id": "controller.extractor", "status": "identity_attested_pre_artifact"},
            {"role_id": "ukrainian_source_reviewer", "reserved_task_id": "task.source_reviewer", "controller_identity_id": "controller.source_reviewer", "status": "identity_attested_pre_artifact"},
        ],
    })


def _input(freeze: Path, units: dict[str, list[dict[str, str]]], totals: dict[str, int], role: Path) -> dict[str, object]:
    families = []
    for family_id in sorted(totals):
        ledger = freeze / f"{family_id}.units.jsonl"
        rows = []
        for unit in units[family_id]:
            rows.append({
                **unit,
                "disposition_code": "converted",
                "canonical_identity": f"canonical.{_sha(unit['unit_id'])}",
                "source_role": "reviewed_source",
                "claim_type": "reviewed_claim",
                "evidence_locator_sha256s": [_sha(f"evidence:{unit['unit_id']}")],
                "consumer_view": {"view_id": "consumer.reviewed", "view_sha256": _sha(unit["unit_id"])},
                "predicate_sha256": _sha(f"predicate:{unit['unit_id']}"),
                "artifact_sha256": _sha(f"artifact:{unit['unit_id']}"),
            })
        families.append({
            "family_id": family_id, "ledger_sha256": dispositions.sha256_file(ledger),
            "unit_count": totals[family_id], "dispositions": rows,
        })
    document = {
        "schema_version": dispositions.INPUT_SCHEMA_VERSION, "text_free": True,
        "source_freeze_receipt_sha256": dispositions.sha256_file(freeze / dispositions.FREEZE_RECEIPT_FILE),
        "role_contract_sha256": dispositions.sha256_file(role),
        "author_binding": {"role_id": "rule_author_extractor", "controller_identity_id": "controller.extractor", "task_id": "task.extractor"},
        "source_review_binding": {"role_id": "ukrainian_source_reviewer", "controller_identity_id": "controller.source_reviewer", "task_id": "task.source_reviewer", "receipt_sha256": "0" * 64},
        "families": families,
    }
    review_receipt = {
        "schema_version": dispositions.SOURCE_REVIEW_RECEIPT_SCHEMA_VERSION,
        "text_free": True,
        "reviewer_role_id": "ukrainian_source_reviewer",
        "controller_identity_id": "controller.source_reviewer",
        "task_id": "task.source_reviewer",
        "source_freeze_receipt_sha256": document["source_freeze_receipt_sha256"],
        "disposition_families_sha256": dispositions.sha256_bytes(
            canonical_json(document["families"]).encode("utf-8")
        ),
        "verdict": "APPROVE",
    }
    _json(role.parent / "source-review-receipt.json", review_receipt)
    document["source_review_binding"]["receipt_sha256"] = dispositions.sha256_file(
        role.parent / "source-review-receipt.json"
    )
    return document


def _compile(tmp_path: Path, freeze: Path, document: dict[str, object], role: Path) -> dict[str, object]:
    reviewed = tmp_path / "reviewed.json"
    _json(reviewed, document)
    return dispositions.compile_dispositions(
        source_freeze_dir=freeze, reviewed_input_path=reviewed, output_dir=tmp_path / "out",
        source_review_receipt_path=role.parent / "source-review-receipt.json", role_contract_path=role,
    )


def _refresh_review_receipt(document: dict[str, object], role: Path) -> None:
    receipt_path = role.parent / "source-review-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["disposition_families_sha256"] = dispositions.sha256_bytes(
        canonical_json(document["families"]).encode("utf-8")
    )
    _json(receipt_path, receipt)
    document["source_review_binding"]["receipt_sha256"] = dispositions.sha256_file(receipt_path)


def test_compiles_exact_text_free_bijection_and_zero_receipt(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    receipt = _compile(tmp_path, freeze, document, role)
    assert receipt["zero_family_receipt"] == {
        "family_id": "other_normative_style_inventory", "frozen_input_identity_total": 0,
        "input_disposition_row_count": 0, "output_disposition_row_count": 0, "status": "ZERO_FAMILY_ACCOUNTED",
    }
    assert receipt["disposition_ledger"]["row_count"] == 7
    assert receipt["author_binding"] == document["author_binding"]
    assert receipt["source_review_binding"] == document["source_review_binding"]
    assert all(item["ledger_universe_sha256"] == item["audit_universe_sha256"] for item in receipt["families"])
    rendered = (tmp_path / "out" / dispositions.OUTPUT_LEDGER_FILE).read_text(encoding="utf-8")
    assert "secret" not in rendered


def test_cli_wires_argument_destinations_to_compiler(
    tmp_path: Path, tiny_totals: dict[str, int], capsys: pytest.CaptureFixture[str],
) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    reviewed = tmp_path / "reviewed.json"
    _json(reviewed, _input(freeze, units, tiny_totals, role))

    assert dispositions.main([
        "--source-freeze-dir", str(freeze),
        "--reviewed-input", str(reviewed),
        "--output-dir", str(tmp_path / "cli-out"),
        "--source-review-receipt", str(tmp_path / "source-review-receipt.json"),
        "--schema", str(dispositions.DEFAULT_SCHEMA),
        "--role-contract", str(role),
    ]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output == {"ok": True, "receipt": dispositions.OUTPUT_RECEIPT_FILE, "rows": 7}


@pytest.mark.parametrize("tamper, error", [
    ("omission", "input disposition count mismatch"),
    ("duplicate", "duplicate disposition unit binding"),
    ("wrong_unit_hash", "does not match freeze"),
    ("wrong_locator_hash", "does not match freeze"),
    ("wrong_family_total", "input family total mismatch"),
])
def test_fails_closed_on_bijection_tampering(
    tmp_path: Path, tiny_totals: dict[str, int], tamper: str, error: str,
) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    family = next(item for item in document["families"] if item["family_id"] == "ua_gec")
    if tamper == "omission":
        family["dispositions"] = []
    elif tamper == "duplicate":
        family["dispositions"].append(deepcopy(family["dispositions"][0]))
    elif tamper == "wrong_unit_hash":
        family["dispositions"][0]["unit_sha256"] = "0" * 64
    elif tamper == "wrong_locator_hash":
        family["dispositions"][0]["locator_sha256"] = "0" * 64
    else:
        family["unit_count"] = 2
    with pytest.raises(dispositions.DispositionError, match=error):
        _compile(tmp_path, freeze, document, role)


def test_fails_closed_on_wrong_frozen_total(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    receipt_path = freeze / dispositions.FREEZE_RECEIPT_FILE
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    next(item for item in receipt["families"] if item["family_id"] == "ua_gec")["unit_count"] = 2
    _json(receipt_path, receipt)
    document = _input(freeze, units, tiny_totals, role)
    with pytest.raises(dispositions.DispositionError, match="wrong frozen family total"):
        _compile(tmp_path, freeze, document, role)


def test_schema_forbids_conversion_artifacts_on_nonconverted(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    row = next(item for item in document["families"] if item["family_id"] == "ua_gec")["dispositions"][0]
    row["disposition_code"] = "evaluation_only"
    row["nonconversion"] = {"reason_code": "heldout_partition", "unit_specific_locator_sha256": _sha("partition")}
    with pytest.raises(dispositions.DispositionError, match="schema violation"):
        _compile(tmp_path, freeze, document, role)


def test_converted_disposition_forbids_nonconversion_payload(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    row = next(item for item in document["families"] if item["family_id"] == "ua_gec")["dispositions"][0]
    row["nonconversion"] = {
        "reason_code": "contradictory_payload",
        "unit_specific_locator_sha256": _sha("contradiction"),
    }
    with pytest.raises(dispositions.DispositionError, match="schema violation"):
        _compile(tmp_path, freeze, document, role)


def test_repeated_nonconversion_reason_requires_predicate_or_rationale(tmp_path: Path, tiny_totals: dict[str, int], monkeypatch: pytest.MonkeyPatch) -> None:
    totals = dict(tiny_totals)
    totals["ua_gec"] = 10
    monkeypatch.setattr(dispositions, "FAMILY_TOTALS", totals)
    freeze, units = _freeze(tmp_path, totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, totals, role)
    for row in next(item for item in document["families"] if item["family_id"] == "ua_gec")["dispositions"]:
        for key in ("canonical_identity", "source_role", "claim_type", "evidence_locator_sha256s", "consumer_view", "predicate_sha256", "artifact_sha256"):
            row.pop(key)
        row["disposition_code"] = "blocked_with_reason"
        row["nonconversion"] = {"reason_code": "awaiting_review", "unit_specific_locator_sha256": _sha(row["unit_id"])}
    with pytest.raises(dispositions.DispositionError, match="repeated nonconversion reason"):
        _compile(tmp_path, freeze, document, role)


def test_textbook_duplicate_requires_deterministic_source_identity(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    row = next(item for item in document["families"] if item["family_id"] == "antonenko_textbook_representation")["dispositions"][0]
    for key in ("canonical_identity", "source_role", "claim_type", "evidence_locator_sha256s", "consumer_view", "predicate_sha256", "artifact_sha256"):
        row.pop(key)
    row["disposition_code"] = "duplicate_representation"
    row["nonconversion"] = {"reason_code": "duplicate_source", "unit_specific_locator_sha256": _sha(row["unit_id"])}
    with pytest.raises(dispositions.DispositionError, match="deterministic source identity"):
        _compile(tmp_path, freeze, document, role)
    row["representation_source_identity"] = dispositions.ANTONENKO_REPRESENTATION_SOURCE_ID
    _refresh_review_receipt(document, role)
    receipt = _compile(tmp_path, freeze, document, role)
    assert receipt["disposition_ledger"]["row_count"] == 7


def test_fails_closed_on_provenance_binding_and_zero_receipt_tampering(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    document["author_binding"]["controller_identity_id"] = "controller.other"
    with pytest.raises(dispositions.DispositionError, match="rule_author_extractor controller binding mismatch"):
        _compile(tmp_path, freeze, document, role)
    document = _input(freeze, units, tiny_totals, role)
    zero = next(item for item in document["families"] if item["family_id"] == "other_normative_style_inventory")
    zero["dispositions"].append({"unit_id": "unit.fake.abc", "unit_sha256": "0" * 64, "locator_sha256": "0" * 64, "disposition_code": "blocked_with_reason", "nonconversion": {"reason_code": "fake", "unit_specific_locator_sha256": "0" * 64}})
    with pytest.raises(dispositions.DispositionError, match="does not match freeze"):
        _compile(tmp_path, freeze, document, role)


def test_fails_closed_on_role_contract_hash_tampering(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    document["role_contract_sha256"] = "0" * 64
    with pytest.raises(dispositions.DispositionError, match="role contract binding mismatch"):
        _compile(tmp_path, freeze, document, role)


@pytest.mark.parametrize("tamper, error", [
    ("missing", "schema violation"),
    ("swapped", "rule_author_extractor controller binding mismatch"),
    ("self_review", "identities must differ"),
    ("wrong_task", "rule_author_extractor task binding mismatch"),
    ("receipt", "source review receipt binding mismatch"),
])
def test_fails_closed_on_source_authoring_provenance_tampering(
    tmp_path: Path, tiny_totals: dict[str, int], tamper: str, error: str,
) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    if tamper == "missing":
        document.pop("author_binding")
    elif tamper == "swapped":
        document["author_binding"]["controller_identity_id"] = "controller.source_reviewer"
        document["source_review_binding"]["controller_identity_id"] = "controller.extractor"
    elif tamper == "self_review":
        document["source_review_binding"]["controller_identity_id"] = "controller.extractor"
    elif tamper == "wrong_task":
        document["author_binding"]["task_id"] = "task.other"
    else:
        (tmp_path / "source-review-receipt.json").write_text("drifted fixture receipt", encoding="utf-8")
    with pytest.raises(dispositions.DispositionError, match=error):
        _compile(tmp_path, freeze, document, role)


def test_fails_closed_on_drifted_role_contract_identity(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    contract = json.loads(role.read_text(encoding="utf-8"))
    contract["seats"][0]["controller_identity_id"] = "controller.drifted"
    contract["task_bindings"][0]["controller_identity_id"] = "controller.drifted"
    _json(role, contract)
    document["role_contract_sha256"] = dispositions.sha256_file(role)
    with pytest.raises(dispositions.DispositionError, match="rule_author_extractor controller binding mismatch"):
        _compile(tmp_path, freeze, document, role)


def test_fails_closed_on_unattested_role_task_status(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    contract = json.loads(role.read_text(encoding="utf-8"))
    contract["task_bindings"][0]["status"] = "reserved_not_launched"
    _json(role, contract)
    document["role_contract_sha256"] = dispositions.sha256_file(role)
    with pytest.raises(dispositions.DispositionError, match="task binding is not pre-artifact attested"):
        _compile(tmp_path, freeze, document, role)


def test_source_review_receipt_binds_exact_disposition_payload(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    family = next(item for item in document["families"] if item["family_id"] == "ua_gec")
    family["dispositions"][0]["artifact_sha256"] = "f" * 64
    with pytest.raises(dispositions.DispositionError, match="source review receipt disposition binding mismatch"):
        _compile(tmp_path, freeze, document, role)


def test_fails_closed_when_source_review_receipt_is_missing(tmp_path: Path, tiny_totals: dict[str, int]) -> None:
    freeze, units = _freeze(tmp_path, tiny_totals)
    role = tmp_path / "roles.json"
    _role_contract(role)
    document = _input(freeze, units, tiny_totals, role)
    (tmp_path / "source-review-receipt.json").unlink()
    with pytest.raises(dispositions.DispositionError, match="source review receipt is missing"):
        _compile(tmp_path, freeze, document, role)


def test_closed_input_schema_rejects_unknown_fields() -> None:
    schema = json.loads(dispositions.DEFAULT_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    with pytest.raises(ValidationError):
        validator.validate({"schema_version": dispositions.INPUT_SCHEMA_VERSION, "text_free": True, "source_freeze_receipt_sha256": "0" * 64, "role_contract_sha256": "0" * 64, "author_binding": {"role_id": "rule_author_extractor", "controller_identity_id": "controller.x", "task_id": "task.x"}, "source_review_binding": {"role_id": "ukrainian_source_reviewer", "controller_identity_id": "controller.y", "task_id": "task.y", "receipt_sha256": "0" * 64}, "families": [], "source_text": "forbidden"})
