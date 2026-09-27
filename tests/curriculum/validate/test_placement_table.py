"""Tests for the generated activity placement table (issue #8889 r5 §B2).

Fixture pedagogy docs and level schemas are built in test code (tmp_path);
the one exception is `test_committed_table_is_not_stale`, which regenerates
from the real docs/best-practices/activity-pedagogy.md and the real
schemas/activities-<level>.schema.json files and compares against the
committed scripts/curriculum/validate/placement_table.yaml byte for byte —
the "a test fails when the generated file is stale" requirement.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate.placement_table import (
    CORE_LEVELS,
    REPO_ROOT,
    PlacementTableError,
    build_placement_table,
    generate,
    load_placement_table,
    parse_pedagogy_matrix,
    render_placement_table,
    schema_activity_types,
)
from scripts.curriculum.validate.placement_table import (
    main as placement_main,
)

MATRIX_DOC = """# Activity Pedagogy — Type System and Allowlist Matrix

## 3. Full Allowlist Matrix

### Type → level matrix

| Type | a1 | a2 | b1-core | b2 | c1-core | c2 |
|---|---|---|---|---|---|---|
| quiz | B | B | B | B | B | B |
| classify | - | - | - | - | - | - |
| translate | W | W | W | W | W | - |
| only-in-doc | B | - | - | - | - | - |

Reading the matrix: ...
"""


def _write_schema(path: Path, level: str, types: list[str]) -> None:
    definitions = {f"{activity_type}-{level}": {"type": "object"} for activity_type in types}
    path.write_text(json.dumps({"definitions": definitions}), encoding="utf-8")


def _write_schemas(root: Path, per_level: dict[str, list[str]]) -> None:
    for level, types in per_level.items():
        _write_schema(root / f"activities-{level}.schema.json", level, types)


def test_parse_pedagogy_matrix_reads_header_and_rows() -> None:
    matrix = parse_pedagogy_matrix(MATRIX_DOC)
    assert matrix["quiz"] == {
        "a1": "B",
        "a2": "B",
        "b1-core": "B",
        "b2": "B",
        "c1-core": "B",
        "c2": "B",
    }
    assert matrix["classify"]["a1"] == "-"
    assert matrix["translate"]["c2"] == "-"


def test_parse_pedagogy_matrix_requires_the_heading() -> None:
    with pytest.raises(PlacementTableError, match="Type → level matrix"):
        parse_pedagogy_matrix("# no matrix here\n")


def test_parse_pedagogy_matrix_rejects_row_cell_count_mismatch() -> None:
    doc = MATRIX_DOC.replace("| quiz | B | B | B | B | B | B |", "| quiz | B | B |")
    with pytest.raises(PlacementTableError, match="matrix row has"):
        parse_pedagogy_matrix(doc)


def test_schema_activity_types_reads_definitions(tmp_path: Path) -> None:
    schema_path = tmp_path / "activities-a1.schema.json"
    _write_schema(schema_path, "a1", ["quiz", "match-up"])
    assert schema_activity_types("a1", schema_path) == {"quiz", "match-up"}


def test_schema_activity_types_rejects_missing_suffix(tmp_path: Path) -> None:
    schema_path = tmp_path / "bad.schema.json"
    schema_path.write_text(json.dumps({"definitions": {"quiz": {}}}), encoding="utf-8")
    with pytest.raises(PlacementTableError, match="lacks the -a1 suffix"):
        schema_activity_types("a1", schema_path)


def test_schema_activity_types_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PlacementTableError, match="does not exist"):
        schema_activity_types("a1", tmp_path / "missing.schema.json")


def _build_with_fixture_schemas(tmp_path: Path, per_level: dict[str, list[str]]) -> dict:
    import scripts.curriculum.validate.placement_table as pt_module

    _write_schemas(tmp_path, per_level)
    original = pt_module.schema_activity_types

    def fake(level: str, schema_path: Path | None = None) -> set[str]:
        return original(level, tmp_path / f"activities-{level}.schema.json")

    pt_module.schema_activity_types = fake
    try:
        return build_placement_table(MATRIX_DOC, "docs/fixture.md", "0" * 64)
    finally:
        pt_module.schema_activity_types = original


def test_agreement_resolves_to_the_doc_cell(tmp_path: Path) -> None:
    per_level = {level: ["quiz"] for level in CORE_LEVELS}
    table = _build_with_fixture_schemas(tmp_path, per_level)
    assert table["levels"]["a1"]["quiz"] == "both"
    assert table["levels"]["c2"]["quiz"] == "both"


def test_schema_allows_doc_forbids_resolves_to_forbidden_with_discrepancy(tmp_path: Path) -> None:
    """classify: the schema still defines it, the doc marks it deprecated."""
    per_level = {level: ["quiz", "classify"] for level in CORE_LEVELS}
    table = _build_with_fixture_schemas(tmp_path, per_level)
    assert table["levels"]["a1"]["classify"] == "forbidden"
    discrepancy = next(d for d in table["discrepancies"] if d["type"] == "classify" and d["level"] == "a1")
    assert discrepancy == {
        "type": "classify",
        "level": "a1",
        "schema": "allowed",
        "doc": "-",
        "resolution": "forbidden",
    }


def test_doc_allows_schema_absent_resolves_to_forbidden_with_discrepancy(tmp_path: Path) -> None:
    """only-in-doc: the pedagogy doc allows it at a1, but no schema defines it there."""
    per_level = {level: ["quiz"] for level in CORE_LEVELS}
    table = _build_with_fixture_schemas(tmp_path, per_level)
    assert table["levels"]["a1"]["only-in-doc"] == "forbidden"
    discrepancy = next(d for d in table["discrepancies"] if d["type"] == "only-in-doc" and d["level"] == "a1")
    assert discrepancy["schema"] == "not_defined"
    assert discrepancy["doc"] == "B"


def test_type_not_in_doc_at_all_is_not_listed(tmp_path: Path) -> None:
    """select: schema defines it, but the row does not exist in the matrix at all."""
    per_level = {level: ["quiz", "select"] for level in CORE_LEVELS}
    table = _build_with_fixture_schemas(tmp_path, per_level)
    assert table["levels"]["a1"]["select"] == "forbidden"
    discrepancy = next(d for d in table["discrepancies"] if d["type"] == "select" and d["level"] == "a1")
    assert discrepancy == {
        "type": "select",
        "level": "a1",
        "schema": "allowed",
        "doc": "not_listed",
        "resolution": "forbidden",
    }


def test_agreement_on_forbidden_is_not_a_discrepancy(tmp_path: Path) -> None:
    """translate at c2: doc says '-' and no level in this fixture defines it there either."""
    per_level = {level: ["quiz"] for level in CORE_LEVELS}
    table = _build_with_fixture_schemas(tmp_path, per_level)
    assert table["levels"]["c2"]["translate"] == "forbidden"
    assert not [d for d in table["discrepancies"] if d["type"] == "translate" and d["level"] == "c2"]


def test_render_placement_table_is_deterministic_and_ends_in_newline() -> None:
    table = {"placement_table_schema": 1, "levels": {"a1": {"quiz": "both"}}, "discrepancies": []}
    text = render_placement_table(table)
    assert text.endswith("\n")
    assert yaml.safe_load(text) == table
    assert render_placement_table(table) == text


def test_generate_round_trips_through_load(tmp_path: Path) -> None:
    doc_path = tmp_path / "activity-pedagogy.md"
    doc_path.write_text(MATRIX_DOC, encoding="utf-8")
    per_level = {level: ["quiz"] for level in CORE_LEVELS}
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    _write_schemas(schemas_dir, per_level)
    import scripts.curriculum.validate.placement_table as pt_module

    original = pt_module.REPO_ROOT
    pt_module.REPO_ROOT = tmp_path
    try:
        text = generate(doc_path)
        out_path = tmp_path / "placement_table.yaml"
        out_path.write_text(text, encoding="utf-8")
        table = load_placement_table(out_path)
    finally:
        pt_module.REPO_ROOT = original
    assert table["levels"]["a1"]["quiz"] == "both"
    assert table["source_doc"]["path"] == "activity-pedagogy.md"


def test_load_placement_table_rejects_malformed_file(tmp_path: Path) -> None:
    bad = tmp_path / "placement_table.yaml"
    bad.write_text("not_levels: {}\n", encoding="utf-8")
    with pytest.raises(PlacementTableError, match="malformed 'levels'"):
        load_placement_table(bad)


def test_cli_check_reports_stale_and_write_fixes_it(tmp_path: Path) -> None:
    doc_path = tmp_path / "activity-pedagogy.md"
    doc_path.write_text(MATRIX_DOC, encoding="utf-8")
    per_level = {level: ["quiz"] for level in CORE_LEVELS}
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()
    _write_schemas(schemas_dir, per_level)
    import scripts.curriculum.validate.placement_table as pt_module

    original = pt_module.REPO_ROOT
    pt_module.REPO_ROOT = tmp_path
    out_path = tmp_path / "placement_table.yaml"
    try:
        assert placement_main(["--check", "--doc", str(doc_path), "--output", str(out_path)]) == 1
        assert placement_main(["--write", "--doc", str(doc_path), "--output", str(out_path)]) == 0
        assert placement_main(["--check", "--doc", str(doc_path), "--output", str(out_path)]) == 0
    finally:
        pt_module.REPO_ROOT = original


def test_cli_reports_usage_error_for_bad_doc(tmp_path: Path) -> None:
    assert placement_main(["--check", "--doc", str(tmp_path / "missing.md")]) == 2


def test_committed_table_is_not_stale() -> None:
    """The frozen requirement: a test fails when placement_table.yaml is stale."""
    committed_path = REPO_ROOT / "scripts/curriculum/validate/placement_table.yaml"
    fresh = generate(REPO_ROOT / "docs/best-practices/activity-pedagogy.md")
    committed = committed_path.read_text(encoding="utf-8")
    assert committed == fresh, (
        "placement_table.yaml is stale; regenerate with "
        ".venv/bin/python scripts/curriculum/validate/placement_table.py --write"
    )
