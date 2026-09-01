"""Tests for scripts.orchestration.driver_agent_type."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.orchestration.driver_agent_type import (
    DEFAULT_ASSIGNMENTS_PATH,
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


@pytest.fixture
def assignments(tmp_path: Path) -> Path:
    path = tmp_path / "area_assignments.yaml"
    path.write_text(FIXTURE, encoding="utf-8")
    return path


def test_area_key_resolves_directly(assignments: Path) -> None:
    assert resolve_driver_agent_type("infra", assignments_path=assignments) == "infra-orchestrator"


def test_lane_resolves_through_slot_membership(assignments: Path) -> None:
    assert resolve_driver_agent_type("folk", assignments_path=assignments) == "curriculum-orchestrator"
    assert resolve_driver_agent_type("bio", assignments_path=assignments) == "curriculum-orchestrator"


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
