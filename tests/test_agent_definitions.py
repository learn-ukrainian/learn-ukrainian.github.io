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
