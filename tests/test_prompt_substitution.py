from pathlib import Path

import pytest

from scripts.build.prompt_builder import PLACEHOLDERS, render_prompt

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "scripts" / "build" / "phases"

ACTIVE_PROMPTS = (
    PROMPTS_DIR / "linear-write.md",
    PROMPTS_DIR / "linear-write-grok.md",
    PROMPTS_DIR / "linear-review-dim.md",
)


@pytest.mark.parametrize("template", ACTIVE_PROMPTS)
def test_no_unfilled_placeholders(template: Path) -> None:
    rendered = render_prompt(template)
    for placeholder in PLACEHOLDERS:
        assert placeholder not in rendered, (
            f"Template {template.name} still has {placeholder} after render"
        )


def test_full_context_writer_loads_shared_contract_context() -> None:
    rendered = render_prompt(PROMPTS_DIR / "linear-write-grok.md")
    assert "WHO — the learner" in rendered
    assert "B1 onwards is uniformly 100 % Ukrainian" in rendered
    assert "Tab 3 — Вправи" in rendered
    assert "Deprecated; subsumed by `mark-the-words`" in rendered


def test_active_prompts_expose_size_policy_token() -> None:
    for template in ACTIVE_PROMPTS:
        rendered = render_prompt(template)
        assert "{SIZE_POLICY}" in rendered


def test_compact_writer_references_shared_contract_path() -> None:
    rendered = render_prompt(PROMPTS_DIR / "linear-write.md")
    assert "scripts/build/contracts/module-contract.md" in rendered


@pytest.mark.parametrize("template", (
    PROMPTS_DIR / "linear-write.md",
    PROMPTS_DIR / "linear-write-grok.md",
))
def test_v7_writer_prompts_keep_size_and_padding_rules(template: Path) -> None:
    prompt = template.read_text(encoding="utf-8")

    assert "{SIZE_POLICY}" in prompt
    assert "source-backed" in prompt
    assert "pad" in prompt.lower()
    if template.name == "linear-write.md":
        assert "old 150% multiplier thinking" in prompt
    else:
        assert "The plan floor still binds" in prompt


@pytest.mark.parametrize("template", (
    PROMPTS_DIR / "linear-write.md",
    PROMPTS_DIR / "linear-write-grok.md",
))
def test_v7_writer_prompts_keep_bad_form_marker_rules(template: Path) -> None:
    prompt = template.read_text(encoding="utf-8")

    assert "<!-- bad -->...<!-- /bad -->" in prompt
    assert (
        "Do NOT use single-asterisk italics" in prompt
        or "Do not use italics or bare prose" in prompt
    )
    assert "bare" in prompt


@pytest.mark.parametrize("template", (
    PROMPTS_DIR / "linear-write.md",
    PROMPTS_DIR / "linear-write-grok.md",
))
def test_v7_writer_prompts_keep_activity_split_rules(template: Path) -> None:
    prompt = template.read_text(encoding="utf-8")

    assert "activity_split_audit" in prompt
    assert "inline" in prompt.lower()
    assert "workbook" in prompt.lower()
    if template.name == "linear-write.md":
        assert "INJECT_ACTIVITY" in prompt


@pytest.mark.parametrize("template", (
    PROMPTS_DIR / "linear-write.md",
    PROMPTS_DIR / "linear-write-grok.md",
))
def test_v7_writer_prompts_keep_teacher_plan_leak_bans(template: Path) -> None:
    prompt = template.read_text(encoding="utf-8")

    assert "Welcome to" in prompt
    assert "In this section" in prompt
    if template.name == "linear-write.md":
        for phrase in ("this section teaches", "learners will", "the activity asks"):
            assert phrase in prompt
