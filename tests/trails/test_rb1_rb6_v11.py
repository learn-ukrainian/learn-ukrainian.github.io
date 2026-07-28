"""Tests for RB-1 / RB-6 v1.1 trail specs and the v1 estate registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.orchestration.validate_trailspec import (
    DEFAULT_ESTATE_REGISTRY_PATH,
    PROJECT_ROOT,
    TrailSpecValidationError,
    validate_estate_registry,
    validate_estate_registry_data,
    validate_trailspec,
    validate_trailspec_data,
)

RB1_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb1-cold-start.trail.yaml"
RB6_TRAIL_PATH = PROJECT_ROOT / "scripts/config/trails/rb6-estate-probes.trail.yaml"
ESTATE_PATH = DEFAULT_ESTATE_REGISTRY_PATH


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_rb1_trail_validates_v11() -> None:
    """RB-1 v1.1 passes validator, has non-empty hash, and is execution eligible."""
    res = validate_trailspec(spec_path=RB1_TRAIL_PATH)
    assert res["ok"] is True
    spec = res["spec"]
    assert spec["trail_id"] == "rb1-cold-start"
    assert spec["version"] == "1.0.0"
    assert spec["steps_count"] == 10
    assert spec["execution_eligible"] is True
    assert len(spec["trail_hash"]) == 64


def test_rb6_trail_validates_v11() -> None:
    """RB-6 v1.1 passes validator, has non-empty hash, and is execution eligible."""
    res = validate_trailspec(spec_path=RB6_TRAIL_PATH)
    assert res["ok"] is True
    spec = res["spec"]
    assert spec["trail_id"] == "rb6-estate-probes"
    assert spec["version"] == "1.0.0"
    assert spec["steps_count"] == 7
    assert spec["execution_eligible"] is True
    assert len(spec["trail_hash"]) == 64


def test_estate_registry_seed_validates() -> None:
    """Estate registry seed estate.v1.yaml validates against estate-registry.v1 schema."""
    res = validate_estate_registry(registry_path=ESTATE_PATH)
    assert res["ok"] is True
    assert res["schema_version"] == "estate-registry.v1"
    assert res["refused_surfaces_count"] == 4


def test_rb6_references_estate_registry_entries() -> None:
    """RB-6 probes explicitly reference estate surfaces defined in estate.v1.yaml."""
    estate_data = _load_yaml(ESTATE_PATH)
    rb6_data = _load_yaml(RB6_TRAIL_PATH)

    surfaces = estate_data["surfaces"]
    refused = set(estate_data["refused_mutation_surfaces"])

    # Extract declared estate surface identities
    vps_aliases = {v["ssh_alias"] for v in surfaces["vps_hosts"]}
    services = {s["systemd_unit"] for s in surfaces["services"]}
    repos = {Path(r["local_path"]).name for r in surfaces["repositories"]}
    sites = {s["url"] for s in surfaces["public_sites"]}

    assert "vps" in vps_aliases
    assert "hramatka-api" in services
    assert "learn-ukrainian-infra-private" in repos
    assert "https://learn-ukrainian.github.io/" in sites

    # Refused surfaces check
    assert "pilot-vps" in refused
    assert "hramatka-api" in refused
    assert "learn-ukrainian-infra-private" in refused
    assert "public-site" in refused

    # Verify RB-6 step intents reference these surfaces
    step_intents = " ".join(s["intent"] for s in rb6_data["steps"])
    assert "pilot-vps" in step_intents or "vps" in step_intents
    assert "hramatka-api" in step_intents
    assert "learn-ukrainian-infra-private" in step_intents
    assert "https://learn-ukrainian.github.io/" in step_intents


def test_negative_rb1_dropped_predicate_clause_fails() -> None:
    """Mutation negative test: dropping a clause from a transition evidence fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    # Remove all clauses from the first transition evidence
    data["steps"][0]["transitions"]["none"]["evidence"]["clauses"] = []

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "schema violation" in str(exc_info.value) or "clauses" in str(exc_info.value)


def test_negative_rb1_unpublished_stop_code_fails() -> None:
    """Mutation negative test: using an unpublished STOP code fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    data["stop_codes"].append("STOP-invented-code")

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Unknown stop_code" in str(exc_info.value)


def test_negative_rb1_duplicate_predicate_id_fails() -> None:
    """Mutation negative test: reusing a predicate_id within a step fails validation."""
    data = _load_yaml(RB1_TRAIL_PATH)
    step = data["steps"][0]
    # Reuse detect-rollover-none in pending_start transition
    step["transitions"]["pending_start"]["evidence"]["predicate_id"] = "detect-rollover-none"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Exactly-one-predicate rule violated" in str(exc_info.value)


def test_negative_rb6_unquoted_parameter_in_shell_fails() -> None:
    """Mutation negative test: unquoted parameter interpolation in a shell program string fails."""
    data = _load_yaml(RB6_TRAIL_PATH)
    # Reintroduce {handoff_agent} in argv[2]
    data["steps"][0]["command"]["argv"][2] = "echo {handoff_agent}"

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_trailspec_data(data)
    assert "Unquoted parameter interpolation prohibited" in str(exc_info.value)


def test_negative_estate_registry_extra_properties_fails() -> None:
    """Mutation negative test: adding illegal top-level property to estate registry fails strict schema."""
    data = _load_yaml(ESTATE_PATH)
    data["illegal_extra_property"] = True

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_estate_registry_data(data)
    assert "EstateRegistry schema violation" in str(exc_info.value)


def test_negative_estate_registry_missing_refused_surface_fails() -> None:
    """Mutation negative test: removing a required surface section from estate registry fails schema."""
    data = _load_yaml(ESTATE_PATH)
    del data["surfaces"]["vps_hosts"]

    with pytest.raises(TrailSpecValidationError) as exc_info:
        validate_estate_registry_data(data)
    assert "EstateRegistry schema violation" in str(exc_info.value)
