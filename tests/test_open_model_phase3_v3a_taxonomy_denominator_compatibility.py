"""Adversarial checks for the metadata-only Phase 3 V3-A freeze."""

from __future__ import annotations

import copy
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.projects.open_model_data import freeze_phase3_v3a_taxonomy_denominator_compatibility as v3a


def _main() -> dict[str, Any]:
    return json.loads(v3a.ARTIFACT_PATH.read_text(encoding="utf-8"))


def _matrix() -> dict[str, Any]:
    return json.loads(v3a.MATRIX_PATH.read_text(encoding="utf-8"))


def _rehash(value: dict[str, Any]) -> None:
    value["receipt_sha256"] = v3a.receipt_sha(value)


def _source_db_has_textbooks(path: Path) -> bool:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='textbooks'"
            ).fetchone()
            is not None
        )
    finally:
        connection.close()


def _reject_main(value: dict[str, Any], pattern: str) -> None:
    _rehash(value)
    with pytest.raises(v3a.V3AError, match=pattern):
        v3a.validate(value, _matrix())


def _reject_matrix(value: dict[str, Any], pattern: str) -> None:
    _rehash(value)
    with pytest.raises(v3a.V3AError, match=pattern):
        v3a.validate(_main(), value)


def test_tracked_artifacts_are_strict_deterministic_and_text_free() -> None:
    schema = json.loads(v3a.SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    main = _main()
    matrix = _matrix()
    v3a.validate(main, matrix)
    assert v3a.ARTIFACT_PATH.read_bytes() == v3a.canonical_bytes(main)
    assert v3a.MATRIX_PATH.read_bytes() == v3a.canonical_bytes(matrix)
    assert v3a.main.__name__ == "main"


def test_exact_denominator_distinguishes_lineage_from_coverage_credit() -> None:
    denominator = _main()["denominator"]
    assert denominator == {
        "source_units": 57,
        "legacy_unknown_rights_units": 39,
        "rule_slots_R": 0,
        "v2_visible_cells": 16,
        "v3_child_cells": 3,
        "visible_cells": 19,
        "active_coverage_target_cells": 16,
        "active_coverage_blocked_cells": 16,
        "not_applicable_cells": 2,
        "lineage_only_parent_cells": 1,
        "legacy_blocked_snapshot_records": 17,
        "satisfied_cells": 0,
        "no_double_count_proof": "13_v2_targets_excluding_parent_plus_3_children_equals_16",
    }


def test_denominator_is_derived_from_bound_predecessors_and_partition() -> None:
    p1 = v3a.read_json(v3a.P1_PATH)
    v3 = v3a.read_json(v3a.V3_ARTIFACT_PATH)
    children = v3a._children()
    assert v3a._derive_denominator(p1, v3, children) == _main()["denominator"]

    expanded_p1 = copy.deepcopy(p1)
    extra_unit = copy.deepcopy(expanded_p1["source_manifest"]["source_units"][0])
    extra_unit["source_unit_id"] = "derivation-test-only"
    extra_unit["rights"]["required_state"] = "unknown"
    expanded_p1["source_manifest"]["source_units"].append(extra_unit)
    expanded_children = copy.deepcopy(children)
    expanded_children.append(copy.deepcopy(children[0]))

    derived = v3a._derive_denominator(expanded_p1, v3, expanded_children)
    assert derived["source_units"] == 58
    assert derived["legacy_unknown_rights_units"] == 40
    assert derived["v3_child_cells"] == 4
    assert derived["visible_cells"] == 20
    assert derived["active_coverage_target_cells"] == 17
    assert derived["active_coverage_blocked_cells"] == 17
    assert derived["legacy_blocked_snapshot_records"] == 18
    assert derived["no_double_count_proof"] == "13_v2_targets_excluding_parent_plus_4_children_equals_17"


def test_partition_is_three_source_attested_macro_regions_without_credit() -> None:
    partition = _main()["dialect_partition"]
    assert partition["partition_complete"] is True
    assert partition["membership_frozen"] is True
    assert partition["parent_coverage_role"] == "lineage_only"
    assert partition["parent_direct_coverage_credit"] is False
    assert [row["region_id"] for row in partition["child_strata"]] == [
        "northern_polissian",
        "southeastern",
        "southwestern",
    ]
    assert all(row["coverage_status"] == "coverage_blocked" for row in partition["child_strata"])
    assert all(row["coverage_credit"] is False for row in partition["child_strata"])


def test_fake_partition_completeness_and_invented_dimensions_are_rejected() -> None:
    value = _main()
    value["dialect_partition"]["child_strata"].pop()
    _reject_main(value, "schema violation|exactly three|dialect regions")

    value = _main()
    value["dialect_partition"]["child_strata"][0]["period_id"] = "invented_period"
    _reject_main(value, "schema violation|period drift|source evidence")

    value = _main()
    value["dialect_partition"]["child_strata"][0]["register_id"] = "invented_register"
    _reject_main(value, "schema violation|register drift|source evidence")


def test_fake_satisfaction_and_parent_or_child_credit_are_rejected() -> None:
    value = _main()
    value["dialect_partition"]["child_strata"][0]["coverage_status"] = "satisfied"
    _reject_main(value, "schema violation|falsely marked satisfied|source evidence")

    value = _main()
    value["dialect_partition"]["parent_direct_coverage_credit"] = True
    _reject_main(value, "schema violation|parent received coverage credit")

    value = _main()
    value["dialect_partition"]["child_strata"][0]["coverage_credit"] = True
    _reject_main(value, "schema violation|unearned credit|source evidence")


def test_reviewed_taxonomy_cannot_collapse_or_drift() -> None:
    value = _main()
    value["taxonomy"]["axes"].pop()
    _reject_main(value, "schema violation|reviewed taxonomy drift")

    value = _main()
    value["taxonomy"]["identity_boundaries"]["surzhyk_is_contact_composition"] = False
    _reject_main(value, "schema violation|reviewed taxonomy drift")


def test_rights_matrix_is_exactly_57_by_7_and_never_infers_permission() -> None:
    rights = _main()["rights_capabilities"]
    assert rights["source_unit_count"] == 57
    assert rights["operation_cell_count"] == 399
    assert len(rights["source_unit_rows"]) == 57
    assert all(len(row["operations"]) == 7 for row in rights["source_unit_rows"])
    assert all(item["state"] == "unknown" for row in rights["source_unit_rows"] for item in row["operations"])
    assert set(rights["unknown_source_units_by_operation"].values()) == {57}


def test_missing_source_or_operation_and_inferred_grant_are_rejected() -> None:
    value = _main()
    value["rights_capabilities"]["source_unit_rows"].pop()
    _reject_main(value, "schema violation|rights source-unit denominator|source IDs")

    value = _main()
    value["rights_capabilities"]["source_unit_rows"][0]["operations"].pop()
    _reject_main(value, "schema violation|operation set|rights evidence")

    value = _main()
    value["rights_capabilities"]["source_unit_rows"][0]["operations"][0]["state"] = "allowed"
    _reject_main(value, "inferred|rights evidence")


def test_publication_scope_cannot_turn_metadata_into_body_permission() -> None:
    value = _main()
    publication = next(
        item
        for item in value["rights_capabilities"]["source_unit_rows"][0]["operations"]
        if item["operation"] == "publish_text_or_metadata"
    )
    publication.pop("scope_qualifier")
    _reject_main(value, "publication scope conflation|rights evidence")


def test_compatibility_has_15_exact_rows_and_one_partition_successor() -> None:
    matrix = _matrix()
    assert matrix["row_count"] == 16
    assert matrix["carried_forward_exact_count"] == 15
    assert matrix["superseded_by_partition_count"] == 1
    parent = next(row for row in matrix["rows"] if row["v2_cell_id"] == v3a.PARENT_CELL_ID)
    assert parent["disposition"] == "superseded_by_partition"
    assert parent["denominator_effect"] == "parent_visible_children_no_double_count"
    assert len(parent["child_partition_ids"]) == 3


def test_compatibility_omission_and_parent_double_count_are_rejected() -> None:
    value = _matrix()
    value["rows"].pop()
    _reject_matrix(value, "schema violation|row count")

    value = _matrix()
    parent = next(row for row in value["rows"] if row["v2_cell_id"] == v3a.PARENT_CELL_ID)
    parent["denominator_effect"] = "same_parent_denominator"
    _reject_matrix(value, "parent denominator effect drift")


def test_forbidden_body_and_heldout_fields_are_rejected() -> None:
    value = _main()
    value["dialect_partition"]["child_strata"][0]["source_body"] = "forbidden"
    _reject_main(value, "schema violation|forbidden field")

    value = _main()
    value["heldout_contract"]["heldout_membership"] = "forbidden"
    _reject_main(value, "schema violation|forbidden field")


def test_predecessor_byte_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = v3a.sha256_file

    def tampered(path: Path) -> str:
        return "0" * 64 if path == v3a.P1_PATH else original(path)

    monkeypatch.setattr(v3a, "sha256_file", tampered)
    with pytest.raises(v3a.V3AError, match="predecessor byte drift"):
        v3a.validate(_main(), _matrix())


def test_receipts_detect_mutation_without_rehash() -> None:
    value = copy.deepcopy(_main())
    value["denominator"]["visible_cells"] = 20
    with pytest.raises(v3a.V3AError, match=r"schema violation|receipt hash drift"):
        v3a.validate(value, _matrix())


def test_local_source_db_reproduces_content_blind_evidence_when_available() -> None:
    source_db = v3a.ROOT / "data/sources.db"
    if not source_db.is_file():
        pytest.skip("local source DB is not installed")
    if not _source_db_has_textbooks(source_db):
        pytest.skip("local source DB does not contain the textbook corpus")
    v3a.verify_source_db(source_db)


def test_source_db_availability_requires_textbooks_schema(tmp_path: Path) -> None:
    placeholder = tmp_path / "sources.db"
    connection = sqlite3.connect(placeholder)
    connection.close()
    assert _source_db_has_textbooks(placeholder) is False

    connection = sqlite3.connect(placeholder)
    try:
        connection.execute("CREATE TABLE textbooks (chunk_id TEXT)")
    finally:
        connection.close()
    assert _source_db_has_textbooks(placeholder) is True
