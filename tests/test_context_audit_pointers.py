"""Mechanical pointer checks for the context-audit docs tickets (#7012–#7014)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_claude_md_points_at_tracked_memory_and_rules() -> None:
    body = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    assert "`agents_extensions/shared/memory/MEMORY.md`" in body
    assert "`agents_extensions/shared/rules/non-negotiable-rules.md`" in body
    assert "GET /api/rules" in body
    assert "`memory/MEMORY.md`" not in body
    assert "`.claude/rules/non-negotiable-rules.md`" not in body


def test_model_assignment_does_not_claim_claude_autoload() -> None:
    body = (REPO / "agents_extensions/shared/rules/model-assignment.md").read_text(
        encoding="utf-8"
    )
    assert "`agents_extensions/shared/memory/MEMORY.md`" in body
    assert "GET /api/rules" in body
    assert "loads via `npm run agents:deploy` into `.claude/rules/`" not in body


def test_gemini_md_names_live_v7_build_command() -> None:
    body = (REPO / "GEMINI.md").read_text(encoding="utf-8")
    assert "scripts/build/v6_build.py" not in body
    assert "scripts/build/v7_build.py {level} {slug}" in body
    assert "--worktree" in body


def test_scripts_md_indexes_live_mcp_sources() -> None:
    body = (REPO / "docs/SCRIPTS.md").read_text(encoding="utf-8")
    assert "rag-and-dictionaries.md" not in body
    assert "claude_extensions/consultation-queue" not in body
    assert "mcp__rag__" not in body
    assert "agents_extensions/shared/rules/mcp-sources-and-dictionaries.md" in body
    assert "agents_extensions/shared/consultation-queue/README.md" in body
    assert "`mcp__sources__verify_word`" in body
    assert "`mcp__sources__search_text`" in body
    assert "`mcp__sources__search_definitions`" in body
    assert "`mcp__sources__search_style_guide`" in body
