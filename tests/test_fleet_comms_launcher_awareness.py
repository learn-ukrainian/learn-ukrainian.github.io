"""Standalone TUI launchers must point at shared fleet-comms mid-cutover doctrine."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/lib/fleet_comms_cold_start.sh"
RULE = REPO / "agents_extensions/shared/rules/fleet-comms-coordination.md"

# Public wrappers dispatch driver lifecycle through one shared core.
LAUNCHERS = (
    "start-grok-driver.sh",
    "start-gemini-driver.sh",
    "start-claude-driver.sh",
    "start-codex-driver.sh",
)


def test_shared_fleet_comms_rule_and_helper_exist() -> None:
    assert RULE.is_file(), "missing shared rule SSOT"
    body = RULE.read_text(encoding="utf-8")
    assert "plane-status" in body
    assert "review-pr" in body
    assert "dual_write" in body or "dual-write" in body
    assert "competing design" in body
    # Post-#5632 Sol alignment (drive-epic skill).
    assert "drive-epic" in body
    assert "-driver.sh" in body
    assert "authoritative" in body.lower()
    assert "not implemented" in body.lower() or "shadow/mirror" in body.lower()
    assert "PR_NUMBER" in body or "PR number" in body.lower()
    assert HELPER.is_file(), "missing shared launcher helper"
    helper = HELPER.read_text(encoding="utf-8")
    assert "fleet_comms_cold_clause" in helper
    assert "fleet_comms_resolve_plane_mode" in helper
    assert "fleet-comms-coordination.md" in helper
    assert "drive-epic" in helper
    assert "authoritative" in helper


def test_epic_launchers_source_shared_helper_or_rule_pointer() -> None:
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "fleet_comms_cold_start.sh" in core
    for name in LAUNCHERS:
        path = REPO / name
        assert path.is_file(), f"missing launcher {name}"
        text = path.read_text(encoding="utf-8")
        assert "launcher_core.sh" in text


def test_prompt_injecting_launchers_include_plane_and_cf_surfaces() -> None:
    """The shared driver prompt must include dual-aware fleet-comms surfaces."""
    text = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "fleet_comms_cold_clause" in text or "plane-status" in text
    assert "fleet-comms" in text


def test_agents_md_carries_fleet_comms_mid_cutover_digest() -> None:
    """Codex-family boots from AGENTS.md — need a non-skippable digest pointer."""
    body = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "fleet-comms-coordination.md" in body
    assert "plane-status" in body
    assert "dual_write" in body or "dual-write" in body or "plane" in body
    assert "drive-epic" in body
    assert "authoritative" in body.lower()


def test_driver_wrappers_use_the_shared_core() -> None:
    """The consolidated drivers bind fleet-comms through launcher_core."""
    for name in (
        "start-grok-driver.sh",
        "start-gemini-driver.sh",
        "start-claude-driver.sh",
        "start-codex-driver.sh",
    ):
        path = REPO / name
        assert path.is_file(), f"missing {name}"
        text = path.read_text(encoding="utf-8")
        assert "launcher_core.sh" in text
    core = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "drive-epic" in core
