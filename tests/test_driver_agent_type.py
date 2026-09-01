"""Tests for scripts.orchestration.driver_agent_type."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestration.driver_agent_type import (
    DEFAULT_ASSIGNMENTS_PATH,
    DEFAULT_TAXONOMY_PATH,
    main,
    resolve_driver_agent_type,
)

FIXTURE = """
schema_version: 1
assignments:
  infra:
    driver_agent_type: infra-orchestrator
    slots: [claude-infra, codex-infra]
  seminars:
    driver_agent_type: curriculum-orchestrator
    slots: [claude-folk, claude-bio]
  broken:
    slots: [claude-broken]
"""

TAXONOMY_FIXTURE = """
schema_version: 1
areas:
  infra:
    id: infra
    aliases: [infra-harness]
  seminars:
    id: seminars
    aliases: [seminars-folk, seminars-bio]
"""


@pytest.fixture
def assignments(tmp_path: Path) -> Path:
    path = tmp_path / "area_assignments.yaml"
    path.write_text(FIXTURE, encoding="utf-8")
    return path


@pytest.fixture
def taxonomy(tmp_path: Path) -> Path:
    path = tmp_path / "fleet_taxonomy.yaml"
    path.write_text(TAXONOMY_FIXTURE, encoding="utf-8")
    return path


def test_area_key_resolves_directly(assignments: Path) -> None:
    assert resolve_driver_agent_type("infra", assignments_path=assignments) == "infra-orchestrator"


def test_lane_resolves_through_slot_membership(assignments: Path) -> None:
    assert resolve_driver_agent_type("folk", assignments_path=assignments) == "curriculum-orchestrator"
    assert resolve_driver_agent_type("bio", assignments_path=assignments) == "curriculum-orchestrator"


def test_stream_alias_resolves_to_canonical_area(assignments: Path, taxonomy: Path) -> None:
    assert (
        resolve_driver_agent_type("infra-harness", assignments_path=assignments, taxonomy_path=taxonomy)
        == "infra-orchestrator"
    )
    assert (
        resolve_driver_agent_type("seminars-bio", assignments_path=assignments, taxonomy_path=taxonomy)
        == "curriculum-orchestrator"
    )


def test_alias_resolution_precedes_slot_fallback(tmp_path: Path) -> None:
    # An alias of area A must not be captured by a different area's slot list.
    assignments = tmp_path / "area_assignments.yaml"
    assignments.write_text(
        """
schema_version: 1
assignments:
  atlas:
    driver_agent_type: atlas-driver
    slots: []
  other:
    driver_agent_type: other-driver
    slots: [claude-atlas-practice]
""",
        encoding="utf-8",
    )
    taxonomy = tmp_path / "fleet_taxonomy.yaml"
    taxonomy.write_text(
        """
schema_version: 1
areas:
  atlas:
    id: atlas
    aliases: [atlas-practice]
""",
        encoding="utf-8",
    )
    assert (
        resolve_driver_agent_type("atlas-practice", assignments_path=assignments, taxonomy_path=taxonomy)
        == "atlas-driver"
    )


def test_unknown_alias_fails_closed(assignments: Path, taxonomy: Path) -> None:
    assert resolve_driver_agent_type("nope", assignments_path=assignments, taxonomy_path=taxonomy) is None
    assert (
        resolve_driver_agent_type(
            "infra-harness",
            assignments_path=assignments,
            taxonomy_path=taxonomy.parent / "absent.yaml",
        )
        is None
    )


def test_unknown_lane_and_missing_type_return_none(assignments: Path) -> None:
    assert resolve_driver_agent_type("nope", assignments_path=assignments) is None
    assert resolve_driver_agent_type("broken", assignments_path=assignments) is None
    assert resolve_driver_agent_type("", assignments_path=assignments) is None


def test_unreadable_file_returns_none(tmp_path: Path) -> None:
    assert resolve_driver_agent_type("infra", assignments_path=tmp_path / "absent.yaml") is None


def test_cli_prints_type_or_exits_one(assignments: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--lane", "infra", "--assignments", str(assignments)]) == 0
    assert capsys.readouterr().out.strip() == "infra-orchestrator"
    assert main(["--lane", "nope", "--assignments", str(assignments)]) == 1


def test_live_registry_maps_infra_and_hramatka() -> None:
    assert DEFAULT_ASSIGNMENTS_PATH.is_file()
    assert resolve_driver_agent_type("infra") == "infra-orchestrator"
    assert resolve_driver_agent_type("hramatka") == "curriculum-orchestrator"
    assert resolve_driver_agent_type("folk") == "curriculum-orchestrator"


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("atlas-practice", "infra-orchestrator"),
        ("atlas-intake", "infra-orchestrator"),
        ("infra-harness", "infra-orchestrator"),
        ("eval-harness", "infra-orchestrator"),
        ("benchmark-2156", "infra-orchestrator"),
        ("corpus-channels", "infra-orchestrator"),
        ("core-quality", "curriculum-orchestrator"),
    ],
)
def test_live_taxonomy_aliases_resolve(alias: str, expected: str) -> None:
    """fleet_taxonomy.yaml stream aliases must not fall back to the curriculum default (#F1)."""
    assert DEFAULT_TAXONOMY_PATH.is_file()
    assert resolve_driver_agent_type(alias) == expected
