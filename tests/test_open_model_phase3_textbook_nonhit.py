"""Hermetic tests for the text-free textbook non-hit scanner boundary."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import phase3_functional_roles as functional_roles
from scripts.projects.open_model_data import phase3_textbook_nonhit as scanner


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _source_db(path: Path, total: int) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE textbooks (id INTEGER PRIMARY KEY, chunk_id TEXT, title TEXT, text TEXT, "
            "source_file TEXT, grade TEXT, author TEXT, char_count INTEGER, parent_section_id INTEGER, "
            "author_uk TEXT, subject TEXT)"
        )
        connection.execute(
            "CREATE TABLE textbook_sections (section_id INTEGER PRIMARY KEY, source_file TEXT, grade INTEGER, "
            "section_title TEXT, section_number TEXT, page_start INTEGER, page_end INTEGER, chunk_count INTEGER, full_text TEXT)"
        )
        for section_id in range(1, 5):
            source_file = f"file-{(section_id - 1) % 3}"
            connection.execute(
                "INSERT INTO textbook_sections VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (section_id, source_file, 5, "forbidden section title", str(section_id), section_id, section_id, 2, "forbidden full text"),
            )
        for index in range(total):
            source_file = f"file-{index % 3}"
            parent = (index % 4) + 1 if index < 4 else None
            # Keep parent/source identity coherent for the linked fixture rows.
            if parent is not None:
                source_file = f"file-{(parent - 1) % 3}"
            connection.execute(
                "INSERT INTO textbooks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (index + 1, f"chunk-{index}", "forbidden title", "forbidden textbook text", source_file, "5", "author", 10, parent, "author-uk", "subject"),
            )


def _frozen_unit(row_id: int) -> dict[str, object]:
    return {
        "unit_id": scanner._source_universe_unit_id(row_id),
        "unit_sha256": f"{row_id + 100:064x}",
        "locator": {
            "kind": "sqlite_row", "table": "textbooks", "primary_key_fields": ["id"],
            "primary_key_sha256": scanner._hash({"id": row_id}),
        },
    }


def _action(
    contract: dict[str, object], *, role_id: str, action_kind: str, input_sha256: str, output_sha256: str, role_sha256: str,
) -> dict[str, object]:
    binding = functional_roles.binding_for_role(contract, role_id)
    execution = next(item for item in contract["functional_roles"] if item["role_id"] == role_id)
    identity = {
        "role_id": binding["role_id"], "task_id": binding["task_id"],
        "input_manifest_sha256": input_sha256,
        "evaluation_cycle_id": contract["evaluation_cycle"]["evaluation_cycle_id"],
        "output_sha256": output_sha256, "status": "completed",
    }
    return {
        "receipt_id": "phase3_functional_action:" + scanner._hash(identity),
        **identity,
        "action_kind": action_kind, "provider": "fixture",
        "exact_model": execution["exact_model"], "model_family": execution["model_family"], "harness": execution["harness"],
        "base_contract_sha256": functional_roles.BASE_SHA256,
        "amendment_sha256": functional_roles.AMENDMENT_SHA256,
        "combined_contract_sha256": functional_roles.COMBINED_SHA256,
        "functional_role_contract_sha256": role_sha256,
        "conflict_graph_sha256": functional_roles.conflict_graph_sha256(contract),
        "started_at": "2026-08-09T00:00:00Z", "completed_at": "2026-08-09T00:01:00Z",
    }


def _fixture_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, total: int = 8) -> dict[str, object]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(scanner, "EXPECTED_UNIT_TOTAL", total)
    monkeypatch.setattr(scanner, "EXPECTED_TRACKED_FILE_TOTAL", 3)
    monkeypatch.setattr(scanner, "EXPECTED_SECTION_TOTAL", 4)
    monkeypatch.setattr(scanner, "_validate_schema", lambda *args, **kwargs: None)
    sources_db = tmp_path / "sources.db"
    _source_db(sources_db, total)
    units = [_frozen_unit(index + 1) for index in range(total)]
    ledger = tmp_path / "school.units.jsonl"
    ledger.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in units), encoding="utf-8")
    coverage, roles, freeze = tmp_path / "coverage.json", tmp_path / "roles.json", tmp_path / "freeze.json"
    _json(coverage, {"text_free": True, "mandatory_families": [{"family_id": "school_textbooks", "scanner_nonhit_audit": {"auditor_role_id": scanner.AUDITOR_ROLE_ID, "seed_owner_role_id": scanner.AUDITOR_ROLE_ID, "sample_formula": "min(1000,nonhit_total)", "stratification": ["tracked_file", "source_identity"], "rubric_frozen_before_sampling": True, "zero_misses_required": True}}]})
    role_value = json.loads(functional_roles.LEDGER_PATH.read_text(encoding="utf-8"))
    _json(roles, role_value)
    _json(freeze, {
        "text_free": True, "input_sha256": {"sources_db": scanner.sha256_file(sources_db)},
        "families": [{"family_id": "school_textbooks", "unit_count": total, "ledger_sha256": scanner.sha256_file(ledger)}],
    })
    rubric = {"rubric_id": "rubric-fixture-v1", "candidate_classes": list(scanner.CANDIDATE_CLASSES), "positive_fixture_ids": ["positive-1"], "negative_fixture_ids": ["negative-1"], "expected_decisions": {"positive-1": True, "negative-1": False}}
    classifications = scanner.neutral_classifications(units)
    classifications[1]["candidate_classes"] = ["rule_bearing"]
    classifications[6]["candidate_classes"] = ["contrast"]
    inputs: dict[str, object] = {
        "coverage_contract": coverage, "role_contract": roles, "source_freeze_receipt": freeze,
        "school_units": ledger, "sources_db": sources_db, "classifications": classifications,
        "rubric": rubric,
    }
    bindings = scanner.validate_bindings(
        coverage_contract=coverage, role_contract=roles, source_freeze_receipt=freeze,
        school_units=ledger, sources_db=sources_db,
    )
    classified = scanner._validated_classifications(units, bindings["metadata_rows"], classifications)
    scanner_sha256 = scanner.sha256_file(scanner.ROOT / scanner.SCANNER_SCRIPT_PATH)
    classification_sha256 = scanner._hash(classified)
    rubric_sha256 = scanner._hash(rubric)
    input_sha256 = scanner._hash({"producer_task_id": scanner.SCANNER_IMPLEMENTATION_TASK_ID, "scanner_sha256": scanner_sha256, "metadata_index_sha256": bindings["metadata_index_sha256"], "classification_universe_sha256": classification_sha256, "rubric_sha256": rubric_sha256})
    author_input_sha256 = scanner._hash({"producer_task_id": scanner.SCANNER_IMPLEMENTATION_TASK_ID, "scanner_sha256": scanner_sha256, "candidate_classes": list(scanner.CANDIDATE_CLASSES), "rubric_id": rubric["rubric_id"]})
    author_action = _action(
        role_value, role_id="ukrainian_source_reviewer", action_kind="textbook_eligibility_rubric_fixture_freeze",
        input_sha256=author_input_sha256, output_sha256=rubric_sha256, role_sha256=bindings["functional_role_contract_sha256"],
    )
    critic_input_sha256 = scanner._hash({"rubric_author_action_receipt_sha256": scanner._hash(author_action), "rubric_sha256": rubric_sha256, "positive_fixture_ids": rubric["positive_fixture_ids"], "negative_fixture_ids": rubric["negative_fixture_ids"], "expected_decisions": rubric["expected_decisions"]})
    critic_action = _action(
        role_value, role_id="scope_circularity_critic", action_kind="textbook_eligibility_rubric_zero_miss_review",
        input_sha256=critic_input_sha256, output_sha256=scanner._hash({"rubric_sha256": rubric_sha256, "zero_miss": True}), role_sha256=bindings["functional_role_contract_sha256"],
    )
    review = {
        "schema_version": "phase3_textbook_scanner_inputs_v2_1", "text_free": True,
        "producer_task_id": scanner.SCANNER_IMPLEMENTATION_TASK_ID,
        "scanner": {"implementation_version": scanner.SCANNER_IMPLEMENTATION_VERSION, "script_path": scanner.SCANNER_SCRIPT_PATH, "script_sha256": scanner_sha256},
        "metadata_index_sha256": bindings["metadata_index_sha256"], "classification_universe_sha256": classification_sha256,
        "rubric_sha256": rubric_sha256, "input_manifest_sha256": input_sha256,
        "rubric_author_action_receipt": author_action, "scope_critic_action_receipt": critic_action,
        **{name: bindings[name] for name in ("base_contract_sha256", "amendment_sha256", "combined_contract_sha256", "functional_role_contract_sha256", "conflict_graph_sha256", "evaluation_cycle_id")},
    }
    review_path = tmp_path / "review.json"
    _json(review_path, review)
    inputs["scanner_review_receipt"] = review_path
    return inputs


def _bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    return scanner.build_bundle(**_fixture_inputs(tmp_path, monkeypatch))


def _entropy() -> dict[str, str]:
    return {
        "derived_seed": "fixed-approved-derived-seed",
        "entropy_receipt_sha256": "a" * 64,
        "first_containing_merge_sha": "b" * 40,
        "canonical_tuple_sha256": "c" * 64,
    }


def test_build_derives_strata_and_preserves_complete_complement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    population = bundle["population"]
    assert population["frozen_unit_total"] == 8
    assert len(population["candidate_units"]) == 2
    assert len(population["nonhit_units"]) == 6
    assert bundle["source_bindings"]["tracked_file_total"] == 3
    assert bundle["source_bindings"]["section_total"] == 4
    assert {row["tracked_file"] for row in population["all_units"]} == {"file-0", "file-1", "file-2"}
    assert all(row["source_identity"].startswith("source.school_textbooks.") for row in population["all_units"])
    assert all("text" not in row for row in population["all_units"])


def test_metadata_and_review_tampering_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    inputs = _fixture_inputs(tmp_path, monkeypatch)
    inputs["classifications"][0]["tracked_file"] = "caller-invented"
    with pytest.raises(scanner.TextbookNonhitError, match="closed and source-free"):
        scanner.build_bundle(**inputs)
    inputs = _fixture_inputs(tmp_path / "review", monkeypatch)
    review = json.loads(inputs["scanner_review_receipt"].read_text(encoding="utf-8"))
    review["producer_task_id"] = "phase3-v2-1-textbook-nonhit-audit"
    _json(inputs["scanner_review_receipt"], review)
    with pytest.raises(scanner.TextbookNonhitError, match="producer task"):
        scanner.build_bundle(**inputs)
    inputs = _fixture_inputs(tmp_path / "db", monkeypatch)
    with sqlite3.connect(inputs["sources_db"]) as connection:
        connection.execute("UPDATE textbooks SET source_file='drifted' WHERE id=1")
    with pytest.raises(scanner.TextbookNonhitError, match="sources database does not match"):
        scanner.build_bundle(**inputs)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("missing_author", "receipt fields must be closed"),
        ("swapped", "rubric author action receipt task binding"),
        ("tampered_critic", "scope critic action input/output binding"),
    ],
)
def test_rubric_author_and_scope_critic_receipts_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str, error: str,
) -> None:
    inputs = _fixture_inputs(tmp_path, monkeypatch)
    review_path = inputs["scanner_review_receipt"]
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if mutation == "missing_author":
        review.pop("rubric_author_action_receipt")
    elif mutation == "swapped":
        review["rubric_author_action_receipt"] = review["scope_critic_action_receipt"]
    else:
        review["scope_critic_action_receipt"]["input_manifest_sha256"] = "0" * 64
    _json(review_path, review)
    with pytest.raises(scanner.TextbookNonhitError, match=error):
        scanner.build_bundle(**inputs)


def test_legacy_controller_role_contract_is_not_current_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _fixture_inputs(tmp_path, monkeypatch)
    _json(inputs["role_contract"], {"root": {"controller_identity_id": "controller_root"}, "seats": []})
    with pytest.raises(scanner.TextbookNonhitError, match="functional-role"):
        scanner.build_bundle(**inputs)


def test_post_build_partition_retarget_cannot_reuse_old_review_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    population = bundle["population"]
    moved = population["nonhit_units"].pop(0)
    moved["candidate_classes"] = ["rule_bearing"]
    population["candidate_units"].append(moved)
    population["candidate_units"].sort(key=lambda row: row["unit_id"])
    all_row = next(row for row in population["all_units"] if row["unit_id"] == moved["unit_id"])
    all_row["candidate_classes"] = ["rule_bearing"]
    population["candidate_total"] = len(population["candidate_units"])
    population["nonhit_total"] = len(population["nonhit_units"])
    population["all_units_sha256"] = scanner._hash(population["all_units"])
    population["candidate_universe_sha256"] = scanner._hash(population["candidate_units"])
    population["nonhit_universe_sha256"] = scanner._hash(population["nonhit_units"])
    bundle["scanner"]["classification_universe_sha256"] = population["all_units_sha256"]

    with pytest.raises(scanner.TextbookNonhitError, match="review receipt classification hash drifted"):
        scanner.draw_audit_sample(bundle, entropy_receipt={})


def test_entropy_fails_closed_until_approved_helper_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    monkeypatch.setattr(scanner.importlib, "import_module", lambda name: (_ for _ in ()).throw(ImportError(name)))
    with pytest.raises(scanner.TextbookNonhitError, match="approved common anti-grinding"):
        scanner.draw_audit_sample(bundle, entropy_receipt={})


def test_audit_recomputes_sample_and_binds_immutable_auditor_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    monkeypatch.setattr(scanner, "_verify_approved_entropy", lambda *args, **kwargs: _entropy())
    sample = scanner.draw_audit_sample(bundle, entropy_receipt={"opaque": "verified-by-common-helper"})
    decisions = [{"unit_id": row["unit_id"], "decision": "agree"} for row in sample["sample_units"]]
    roles = json.loads(functional_roles.LEDGER_PATH.read_text(encoding="utf-8"))
    action_input = scanner._hash({"bundle_sha256": scanner._hash(bundle), "sample_sha256": sample["sample_sha256"], "entropy_receipt_sha256": sample["entropy_receipt_sha256"]})
    receipt = {
        "schema_version": "phase3_textbook_nonhit_decision_receipt_v1", "text_free": True,
        "auditor_role_binding": bundle["audit_contract"]["auditor_role_binding"],
        "bundle_sha256": scanner._hash(bundle), "sample_sha256": sample["sample_sha256"],
        "entropy_receipt_sha256": sample["entropy_receipt_sha256"], "decisions": decisions,
        "decisions_sha256": scanner._hash(decisions),
        "action_receipt": _action(roles, role_id=scanner.AUDITOR_ROLE_ID, action_kind="textbook_nonhit_audit_results", input_sha256=action_input, output_sha256=scanner._hash(decisions), role_sha256=bundle["audit_contract"]["functional_role_contract_sha256"]),
    }
    receipt_path = tmp_path / "decisions.json"
    _json(receipt_path, receipt)
    passed = scanner.validate_audit_results(bundle, sample, entropy_receipt={}, decision_receipt_path=receipt_path)
    assert passed["status"] == "PASS_ZERO_MISSES"
    assert passed["result_sha256"] == scanner._hash({key: value for key, value in passed.items() if key != "result_sha256"})
    receipt["action_receipt"]["task_id"] = "phase3-v2-1-rule-author-extraction"
    _json(receipt_path, receipt)
    with pytest.raises(scanner.TextbookNonhitError, match="task binding"):
        scanner.validate_audit_results(bundle, sample, entropy_receipt={}, decision_receipt_path=receipt_path)
    sample["sample_units"][0] = dict(bundle["population"]["candidate_units"][0])
    with pytest.raises(scanner.TextbookNonhitError, match="sample differs"):
        scanner.validate_audit_results(bundle, sample, entropy_receipt={}, decision_receipt_path=receipt_path)


def test_nonagree_result_invalidates_population_and_requires_fresh_entropy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _bundle(tmp_path, monkeypatch)
    monkeypatch.setattr(scanner, "_verify_approved_entropy", lambda *args, **kwargs: _entropy())
    sample = scanner.draw_audit_sample(bundle, entropy_receipt={})
    decisions = [{"unit_id": row["unit_id"], "decision": "agree"} for row in sample["sample_units"]]
    decisions[0]["decision"] = "ambiguous_eligibility"
    roles = json.loads(functional_roles.LEDGER_PATH.read_text(encoding="utf-8"))
    action_input = scanner._hash({"bundle_sha256": scanner._hash(bundle), "sample_sha256": sample["sample_sha256"], "entropy_receipt_sha256": sample["entropy_receipt_sha256"]})
    receipt = {
        "schema_version": "phase3_textbook_nonhit_decision_receipt_v1", "text_free": True,
        "auditor_role_binding": bundle["audit_contract"]["auditor_role_binding"],
        "bundle_sha256": scanner._hash(bundle), "sample_sha256": sample["sample_sha256"],
        "entropy_receipt_sha256": sample["entropy_receipt_sha256"], "decisions": decisions,
        "decisions_sha256": scanner._hash(decisions),
        "action_receipt": _action(roles, role_id=scanner.AUDITOR_ROLE_ID, action_kind="textbook_nonhit_audit_results", input_sha256=action_input, output_sha256=scanner._hash(decisions), role_sha256=bundle["audit_contract"]["functional_role_contract_sha256"]),
    }
    path = tmp_path / "miss.json"
    _json(path, receipt)
    failed = scanner.validate_audit_results(bundle, sample, entropy_receipt={}, decision_receipt_path=path)
    assert failed["status"] == "INVALID_SCANNER_POPULATION_AND_SAMPLE"
    assert failed["requires_new_scanner_hash_and_auditor_seed"] is True
    assert failed["prior_sample_reuse_forbidden"] is True


def test_hamilton_and_production_schema_pins_denominators() -> None:
    assert scanner.hamilton_quotas({"a": 4, "b": 3, "c": 3}, 5) == {"a": 2, "b": 2, "c": 1}
    schema = json.loads(scanner.BUNDLE_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["additionalProperties"] is False
    population = schema["$defs"]["population"]["properties"]
    assert population["frozen_unit_total"] == {"const": 54979}
    assert population["all_units"]["minItems"] == population["all_units"]["maxItems"] == 54979
    source = schema["$defs"]["source_bindings"]["properties"]
    assert source["tracked_file_total"] == {"const": 168}
    assert source["section_total"] == {"const": 7250}
