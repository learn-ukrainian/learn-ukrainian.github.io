"""Repository Claude agents must resolve to their explicit assigned models."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "agents_extensions/shared/agents"
RESERVED_AGENTS = {
    "curriculum-orchestrator": "claude-opus-5-5",
    "curriculum-track-orchestrator": "claude-opus-5-5",
    "curriculum-writer": "claude-opus-5-5",
    "infra-orchestrator": "claude-sonnet-5-5",
}


@pytest.mark.repo_wide
def test_reserved_agent_inventory() -> None:
    assert set(RESERVED_AGENTS).issubset({path.stem for path in AGENTS.glob("*.md")})


@pytest.mark.parametrize("name,model", RESERVED_AGENTS.items())
def test_reserved_agent_frontmatter_pins_assigned_model(name: str, model: str) -> None:
    text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
    opening, frontmatter, body = text.split("---", 2)
    assert not opening.strip(), "agent definitions must start with YAML frontmatter"
    definition = yaml.safe_load(frontmatter)
    assert definition["name"] == name
    assert definition["description"]
    assert definition["tools"]
    assert body.strip()
    assert definition["model"] == model, f"{name} must pin its assigned model"
    catalog = yaml.safe_load((ROOT / "scripts/config/model_catalog.yaml").read_text(encoding="utf-8"))
    assert catalog["models"][definition["model"]].get("lifecycle", "active") == "active"


@pytest.mark.parametrize(
    "relative_path",
    [
        "agents_extensions/shared/agents/infra-orchestrator.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "agents_extensions/shared/skills/drive-epic/references/model-deltas.md",
    ],
)
def test_infra_orchestrator_security_router_only_exception(relative_path: str) -> None:
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    if relative_path.endswith("infra-orchestrator.md"):
        # Check instructions in the body, not merely the frontmatter model pin.
        text = text.split("---", 2)[2]
        prohibition = "never write, edit or review security code yourself"
    else:
        prohibition = "never writes or reviews security code"
    text = " ".join(text.split())
    for phrase in (
        "router-only exception",
        prohibition,
        "every security-code worker and every security-code review to `claude-opus-5-5` (Opus)",
        "review independence still binds: Opus-authored security code is reviewed by the "
        "resolver's `--risk critical` cross-family seat, never Sonnet.",
    ):
        assert phrase in text, f"{relative_path} must state {phrase!r}"
    if relative_path.endswith("model-assignment.md"):
        assert "CTO decision, 2026-10-09" in text
    if not relative_path.endswith("infra-orchestrator.md"):
        assert "never written or reviewed on Sonnet" in text


def test_core_security_row_requires_critical_review_and_excludes_sonnet() -> None:
    text = (ROOT / "agents_extensions/shared/rules/core.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith("| Security code ("))
    assert "never written or reviewed on Sonnet" in row
    assert "review `--risk critical`" in row
    assert "router-only exception" not in text


def test_infra_orchestrator_security_merge_read_uses_independent_verdict() -> None:
    text = (AGENTS / "infra-orchestrator.md").read_text(encoding="utf-8").split("---", 2)[2]
    text = " ".join(text.split())
    assert (
        "on security-code PRs the merge read relies on the Opus or critical review verdict "
        "and is not your own review"
    ) in text


def test_model_deltas_keeps_all_cf_reviews_cross_family() -> None:
    text = (ROOT / "agents_extensions/shared/skills/drive-epic/references/model-deltas.md").read_text(
        encoding="utf-8"
    )
    text = " ".join(text.split())
    assert "CF reviews you route must go to a **non-Anthropic** family" in text
    assert "Other CF reviews" not in text
