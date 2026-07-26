"""Tests for fleet taxonomy and area assignments validation."""

from __future__ import annotations

from typing import Any

import pytest
import yaml

import scripts.config
from scripts.orchestration.validate_fleet_taxonomy import (
    ASSIGNMENTS_PATH,
    ASSIGNMENTS_SCHEMA_PATH,
    TAXONOMY_PATH,
    TAXONOMY_SCHEMA_PATH,
    FleetTaxonomyValidationError,
    validate_fleet_taxonomy,
)


def test_scripts_config_resolves_to_module() -> None:
    """Guard test: import scripts.config must resolve to the module, not a package."""
    assert scripts.config.__file__ is not None
    assert scripts.config.__file__.rstrip("c").endswith("scripts/config.py")



def _write_yaml(path: Any, data: dict[str, Any]) -> None:
    path.write_text(yaml.dump(data), encoding="utf-8")


def test_happy_path_real_files() -> None:
    """Validate real fleet_taxonomy.yaml and area_assignments.yaml."""
    res = validate_fleet_taxonomy()
    assert res["ok"] is True
    assert res["areas_count"] == 7
    assert res["epics_count"] == 18
    assert res["assignments_count"] == 7


def test_negative_duplicate_alias_across_areas(tmp_path: Any) -> None:
    """Negative invariant test: duplicate alias across areas raises FleetTaxonomyValidationError."""
    tax_data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    ass_data = yaml.safe_load(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))

    # Break taxonomy data by adding an alias from harness ('eval-harness') into infra
    tax_data["areas"]["infra"]["aliases"].append("eval-harness")

    tax_file = tmp_path / "fleet_taxonomy.yaml"
    ass_file = tmp_path / "area_assignments.yaml"
    _write_yaml(tax_file, tax_data)
    _write_yaml(ass_file, ass_data)

    with pytest.raises(FleetTaxonomyValidationError) as exc_info:
        validate_fleet_taxonomy(
            taxonomy_path=tax_file,
            assignments_path=ass_file,
            taxonomy_schema_path=TAXONOMY_SCHEMA_PATH,
            assignments_schema_path=ASSIGNMENTS_SCHEMA_PATH,
        )

    assert "not injective" in str(exc_info.value)
    assert "eval-harness" in str(exc_info.value)


def test_negative_epic_in_two_areas(tmp_path: Any) -> None:
    """Negative invariant test: duplicate epic across areas raises FleetTaxonomyValidationError."""
    tax_data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    ass_data = yaml.safe_load(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))

    # Break taxonomy by adding epic 4707 (from infra) into devops as well
    tax_data["areas"]["devops"]["epics"].append({"number": 4707, "name": "Duplicate 4707"})

    tax_file = tmp_path / "fleet_taxonomy.yaml"
    ass_file = tmp_path / "area_assignments.yaml"
    _write_yaml(tax_file, tax_data)
    _write_yaml(ass_file, ass_data)

    with pytest.raises(FleetTaxonomyValidationError) as exc_info:
        validate_fleet_taxonomy(
            taxonomy_path=tax_file,
            assignments_path=ass_file,
            taxonomy_schema_path=TAXONOMY_SCHEMA_PATH,
            assignments_schema_path=ASSIGNMENTS_SCHEMA_PATH,
        )

    assert "Epic number 4707 belongs to multiple areas" in str(exc_info.value)


def test_negative_assignment_for_unknown_area(tmp_path: Any) -> None:
    """Negative invariant test: assignment for unknown area raises FleetTaxonomyValidationError."""
    tax_data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    ass_data = yaml.safe_load(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))

    # Break assignments by adding an unknown area
    ass_data["assignments"]["ghost_area"] = {
        "driver_agent_type": "infra-orchestrator",
        "slots": [],
    }

    tax_file = tmp_path / "fleet_taxonomy.yaml"
    ass_file = tmp_path / "area_assignments.yaml"
    _write_yaml(tax_file, tax_data)
    _write_yaml(ass_file, ass_data)

    with pytest.raises(FleetTaxonomyValidationError) as exc_info:
        validate_fleet_taxonomy(
            taxonomy_path=tax_file,
            assignments_path=ass_file,
            taxonomy_schema_path=TAXONOMY_SCHEMA_PATH,
            assignments_schema_path=ASSIGNMENTS_SCHEMA_PATH,
        )

    assert "Assignment for unknown area(s)" in str(exc_info.value)
    assert "ghost_area" in str(exc_info.value)


def test_negative_schema_violation(tmp_path: Any) -> None:
    """Negative invariant test: JSON Schema violation raises FleetTaxonomyValidationError."""
    tax_data = yaml.safe_load(TAXONOMY_PATH.read_text(encoding="utf-8"))
    ass_data = yaml.safe_load(ASSIGNMENTS_PATH.read_text(encoding="utf-8"))

    # Break taxonomy schema by adding forbidden additional top-level property
    tax_data["forbidden_top_level_prop"] = True

    tax_file = tmp_path / "fleet_taxonomy.yaml"
    ass_file = tmp_path / "area_assignments.yaml"
    _write_yaml(tax_file, tax_data)
    _write_yaml(ass_file, ass_data)

    with pytest.raises(FleetTaxonomyValidationError) as exc_info:
        validate_fleet_taxonomy(
            taxonomy_path=tax_file,
            assignments_path=ass_file,
            taxonomy_schema_path=TAXONOMY_SCHEMA_PATH,
            assignments_schema_path=ASSIGNMENTS_SCHEMA_PATH,
        )

    assert "fleet_taxonomy schema violation" in str(exc_info.value)
