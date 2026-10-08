"""#10083: interactive advisors, reserved pins and bounded Haiku contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused, refuse_mechanical_task
from scripts.review.model_catalog import load_model_catalog

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "agents_extensions/shared"
HAIKU = "claude-haiku-5-5"


def test_interactive_settings_use_documented_model_and_advisor_keys():
    settings = json.loads((SHARED / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-5-5"
    assert settings["advisorModel"] == "claude-opus-5-5"
    assert "CLAUDE_CODE_DISABLE_ADVISOR_TOOL" not in settings.get("env", {})
    assert "CLAUDE_CODE_SUBAGENT_MODEL" not in settings.get("env", {})


@pytest.mark.parametrize("agent,model", [
    ("curriculum-orchestrator", "claude-opus-5-5"),
    ("curriculum-track-orchestrator", "claude-opus-5-5"),
    ("curriculum-writer", "claude-opus-5-5"),
    ("infra-orchestrator", "claude-sonnet-5-5"),
    ("haiku-junior-coder", HAIKU),
    ("haiku-search", HAIKU),
    ("haiku-mechanical", HAIKU),
])
def test_reserved_and_helper_agent_pins(agent, model):
    metadata = yaml.safe_load((SHARED / "agents" / f"{agent}.md").read_text().split("---", 2)[1])
    assert metadata["model"] == model
    if agent in {"haiku-search", "haiku-mechanical"}:
        assert set(metadata["tools"].split(", ")) == {"Read", "Grep", "Glob"}


def test_no_code_or_ukrainian_agent_inherits_a_model():
    for path in (SHARED / "agents").glob("*.md"):
        metadata = yaml.safe_load(path.read_text().split("---", 2)[1])
        assert metadata["model"] != "inherit", path.name


def test_no_global_haiku_subagent_override():
    settings = json.loads((SHARED / "settings.json").read_text())
    assert settings["model"] == "claude-sonnet-5-5"  # Unnamed helper inherits the interactive model.
    for path in [*ROOT.glob("start-*.sh"), ROOT / "scripts/lib/launcher_core.sh"]:
        assert "CLAUDE_CODE_SUBAGENT_MODEL=" not in path.read_text(), path.name


@pytest.mark.parametrize("relative", [
    "agents_extensions/shared/rules/model-assignment.md",
    "agents_extensions/shared/agents/haiku-junior-coder.md",
])
def test_junior_coder_requires_bounded_opus_advice_and_escalation(relative):
    text = (ROOT / relative).read_text()
    for clause in ("exact owned paths", "objective acceptance", "scope ceiling",
                   "Opus 5.5 advisory envelope", "architectural", "security-sensitive", "cross-module"):
        assert clause in " ".join(text.split()), clause
    assert "Haiku is **not** a bounded implementation worker" not in text


def test_core_and_catalog_keep_haiku_bans_and_junior_constraints():
    core = (SHARED / "rules/core.md").read_text()
    assert "Haiku: no Ukrainian text/content/review, review of record, design/approval, security code or drivers" in core
    assert "Junior code requires exact owned paths, objective ACs, scope ceiling, Opus 5.5 envelope" in core
    haiku = load_model_catalog()["models"][HAIKU]
    assert set(haiku["weaknesses"]) == {
        "no_ukrainian_content", "no_formal_review", "no_design_or_approval", "no_security_code", "no_driver",
    }
    assert "completed Opus 5.5 advisory envelope" in haiku["notes"]


@pytest.mark.parametrize("overrides,reason", [
    ({"language_lane": True}, "Ukrainian authoring, review and content"),
    ({"review": True}, "never perform review"),
    ({"paths": ("scripts/agent_runtime/sandbox.py",)}, "security-sensitive"),
    ({"task_role": "driver"}, "driver, design, advisory, approval and content"),
])
def test_haiku_bans_remain_enforced_before_content_or_execution(overrides, reason):
    with pytest.raises(MechanicalAdmissionRefused, match=reason):
        refuse_mechanical_task(
            (HAIKU,), **{
                "mode": "workspace-write", "task_family": "routine_mechanical",
                "paths": ("package-lock.json",), **overrides,
            },
        )
