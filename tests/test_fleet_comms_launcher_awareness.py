"""Standalone TUI launchers must point at shared fleet-comms authority doctrine."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/lib/fleet_comms_cold_start.sh"
RULE = REPO / "agents_extensions/shared/rules/fleet-comms-coordination.md"
CURSOR_COLD_START = REPO / "agents_extensions/cursor/rules/cold-start.md"

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
    assert "fleet-comms is the durable source of truth" in body.lower()
    assert "legacy stores are read-only" in body.lower()
    assert "acp" in body.lower() and "provider transport" in body.lower()
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
    assert 'source "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh"' in text


def test_shared_launcher_clause_onboards_authority_and_acp_layers() -> None:
    helper = HELPER.read_text(encoding="utf-8")
    for required in (
        "LU_AGENT_COMM_TRANSPORT",
        "All normal inter-agent asks",
        "2–6 seat discussions",
        "sealed formal review provider calls use ACP",
        "never fall back to bridge/provider execution",
        "fleet-comms owns durable state",
        "legacy bridge/channel stores are read-only",
        "Continuity: stream lease already claimed",
    ):
        assert required in helper


def test_cursor_cold_start_points_to_same_acp_contract() -> None:
    body = CURSOR_COLD_START.read_text(encoding="utf-8")
    assert "agent-seat-onboarding.md" in body
    assert "route eligible two-seat read-only" in body
    assert "Codex" in body and "KimiCC K3" in body and "Pool" in body
    assert "automatically" in body
    assert "never\nsilently replays" in body
    assert "does not replace fleet\ncoordination or formal" in body


def test_no_launcher_starts_an_acp_process_at_cold_start() -> None:
    launcher_paths = [REPO / "scripts/lib/launcher_core.sh", *REPO.glob("start-*.sh")]
    for path in launcher_paths:
        assert "acp-discuss" not in path.read_text(encoding="utf-8"), path.name


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
