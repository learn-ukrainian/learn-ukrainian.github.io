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


def test_model_assignment_routing_table_excludes_deepseek_and_retired_pro_pins() -> None:
    body = (REPO / "agents_extensions/shared/rules/model-assignment.md").read_text(
        encoding="utf-8"
    )
    coding, review = (
        next(line for line in body.splitlines() if line.startswith(prefix)).split("|")[1:-1]
        for prefix in ("| **Coding / impl / fixtures** |", "| **Code review** (")
    )
    assert all("deepseek" not in cell.lower() for cell in coding[1:4] + review[1:4])
    assert "pin the model (`auto` only for a well-defined coding dispatch)" in coding[1]
    assert coding[3].strip() == "grok"
    assert coding[4].strip().endswith("retired Pro pins are historical only")
    assert review[2].strip().endswith("GLM-5.3 · pool **`laguna-s-2.1`**")
    # High risk names the three qualified lanes and defers to admission;
    # native AGY is admitted only in the low/medium defaults (#10073).
    high, practical = review[2].split("**medium/low formal CF defaults:**")
    assert high.strip().startswith("**high:** `gpt-6.1-sol`, `claude-opus-5-5`, or `grok-4.7`")
    assert "review admission rules" in high and "sonnet" not in high.lower() and "laguna" not in high.lower()
    assert "gemini" not in high.lower() and "native AGY `gemini-3.8-flash-high`" in practical
    assert "high/medium/low" not in review[2] and "claude-sonnet-5-5" in practical
    assert review[3].strip() == "**second dissent / volume:** Pool S 2.1"
    assert review[4].strip().endswith(
        "DeepSeek is excluded from formal review; Flash remains an active catalog identity, while Pro is retired"
    )


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
