"""The four worker-default sources agree on the approved resource policy."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_fallback_policy_admits_native_claude_without_excluded_writer():
    path = ROOT / "scripts/config/agent_fallback_substitutions.yaml"
    document = yaml.safe_load(path.read_text())

    assert "post_2026_06_15_hard_rule" not in document
    assert "native Claude CLI workers" in document["worker_resource_policy"]
    assert "Sol is the default eligible code worker" in document["worker_resource_policy"]
    assert "language-free overflow only" in document["worker_resource_policy"]
    assert document["dispatch_fallbacks"]["claude"] == "codex"
    assert all("deepseek" not in row["fallback"].lower() for row in document["substitutions"])


@pytest.mark.parametrize(
    "relative",
    [
        "agents_extensions/shared/rules/model-assignment.md",
        "agents_extensions/shared/skills/drive-epic/references/routing-and-dispatch.md",
    ],
)
def test_routing_prose_uses_sol_default_with_explicit_bounded_routes(relative):
    document = " ".join((ROOT / relative).read_text().split())

    assert "2026-10-09 resource-policy order" in document
    assert "default eligible code worker" in document.lower()
    assert "native Claude CLI" in document
    assert "language-free overflow" in document
    assert "--advisory-task" in document
    for stale in (
        "**Default bounded work:**",
        "Bounded implementation defaults to Luna",
        "subagents of a Sol parent default to Luna",
        "claude seat = only",
        "first pick for mechanical + ordinary",
    ):
        assert stale not in document
