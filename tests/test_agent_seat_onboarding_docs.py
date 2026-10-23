"""Docs-contract tests for #6027 agent-seat onboarding and ownership surfaces.

These tests pin documentation wording only. They do not invoke ACPX, GitHub,
or network auth. Mutable live facts (plane mode, model pins) must be queried,
not hard-coded as present-tense claims in the owned docs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

ONBOARDING = REPO / "docs/runbooks/agent-seat-onboarding.md"
SCRIPTS = REPO / "docs/SCRIPTS.md"
COOPERATION = REPO / "docs/best-practices/agent-cooperation.md"
RUNTIME = REPO / "docs/agent-runtime-guide.md"
ROSTER = REPO / "docs/runbooks/epic-orchestrator-roster.md"
FLEET_COMMS = REPO / "agents_extensions/shared/rules/fleet-comms-coordination.md"
OWNED_DOCS = (
    ONBOARDING,
    SCRIPTS,
    COOPERATION,
    RUNTIME,
    ROSTER,
    FLEET_COMMS,
)


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required doc: {path.relative_to(REPO)}"
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def onboarding() -> str:
    return _read(ONBOARDING)


@pytest.fixture(scope="module")
def all_owned() -> dict[str, str]:
    return {str(p.relative_to(REPO)): _read(p) for p in OWNED_DOCS}


def test_kimi_routes_are_retired_not_a_live_effort_default(
    onboarding: str, all_owned: dict[str, str]
) -> None:
    """OO-58: owned docs must not state a live KimiCC-high or native-max route.

    The defect is a present-tense effort default that would send a dispatch
    to a retired catalog id. Retirement wording is the required contract.
    """
    for rel in (
        "docs/runbooks/agent-seat-onboarding.md",
        "docs/agent-runtime-guide.md",
        "docs/SCRIPTS.md",
        "docs/best-practices/agent-cooperation.md",
        "agents_extensions/shared/rules/fleet-comms-coordination.md",
    ):
        folded = all_owned[rel].lower()
        assert "kimi" in folded, rel
        assert "retired" in folded, rel
        assert "k3 defaults" not in folded, rel
        assert "max-only" not in folded, rel
    assert "do not dispatch" in onboarding.lower()
    assert "do not\nselect kimicc" in onboarding.lower()
