"""Standalone TUI launchers must point at shared fleet-comms mid-cutover doctrine."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/lib/fleet_comms_cold_start.sh"
RULE = REPO / "agents_extensions/shared/rules/fleet-comms-coordination.md"

# Epic-capable standalone TUIs / UIs that cold-start drivers.
LAUNCHERS = (
    "start-grok.sh",
    "start-gemini.sh",
    "start-kimi.sh",
    "start-claude.sh",
    "start-codex.sh",
)


def test_shared_fleet_comms_rule_and_helper_exist() -> None:
    assert RULE.is_file(), "missing shared rule SSOT"
    body = RULE.read_text(encoding="utf-8")
    assert "plane-status" in body
    assert "review-pr" in body
    assert "dual_write" in body or "dual-write" in body
    assert "competing design" in body
    assert HELPER.is_file(), "missing shared launcher helper"
    helper = HELPER.read_text(encoding="utf-8")
    assert "fleet_comms_cold_clause" in helper
    assert "fleet_comms_resolve_plane_mode" in helper
    assert "fleet-comms-coordination.md" in helper


def test_epic_launchers_source_shared_helper_or_rule_pointer() -> None:
    for name in LAUNCHERS:
        path = REPO / name
        assert path.is_file(), f"missing launcher {name}"
        text = path.read_text(encoding="utf-8")
        assert "fleet_comms_cold_start.sh" in text, (
            f"{name} must source scripts/lib/fleet_comms_cold_start.sh "
            "(or at least reference it for dual-aware banners)"
        )


def test_prompt_injecting_launchers_include_plane_and_cf_surfaces() -> None:
    """Grok / Gemini / Kimi inject free-text cold prompts — must mention dual-aware surfaces."""
    for name in ("start-grok.sh", "start-gemini.sh", "start-kimi.sh"):
        text = (REPO / name).read_text(encoding="utf-8")
        # Clause comes from shared helper function name or inlined fallback.
        assert "fleet_comms_cold_clause" in text or "plane-status" in text
        assert "fleet-comms-coordination" in text or "fleet_comms_cold_clause" in text


def test_agents_md_carries_fleet_comms_mid_cutover_digest() -> None:
    """Codex-family boots from AGENTS.md — need a non-skippable digest pointer."""
    body = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "fleet-comms-coordination.md" in body
    assert "plane-status" in body
    assert "dual_write" in body or "dual-write" in body or "plane" in body
