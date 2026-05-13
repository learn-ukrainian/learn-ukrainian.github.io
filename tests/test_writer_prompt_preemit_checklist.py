from __future__ import annotations

from scripts.build import linear_pipeline

WRITER_TEMPLATE = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
)

CHECKLIST_HEADER = "## Pre-emit verification (run BEFORE you write any artifact)"

REQUIRED_TOOL_MENTIONS = (
    "mcp__sources__search_text",
    "mcp__sources__query_wikipedia",
    "mcp__sources__search_external",
    "mcp__sources__search_images",
    "mcp__sources__verify_words",
    "mcp__sources__search_style_guide",
)


def _writer_template() -> str:
    return WRITER_TEMPLATE.read_text(encoding="utf-8")


def test_writer_prompt_has_preemit_checklist() -> None:
    prompt = _writer_template()
    assert CHECKLIST_HEADER in prompt, (
        "Pre-emit checklist header missing from writer prompt — see #1969."
    )


def test_writer_prompt_preemit_lists_required_tool_calls() -> None:
    prompt = _writer_template()
    # Find the checklist section, assert each required tool is mentioned
    # inside it (not just somewhere in the file).
    idx = prompt.find(CHECKLIST_HEADER)
    assert idx >= 0
    hard_stop_idx = prompt.find("## HARD STOP RULE", idx)
    assert hard_stop_idx > idx, "HARD STOP RULE must follow the checklist"
    checklist_body = prompt[idx:hard_stop_idx]
    for tool in REQUIRED_TOOL_MENTIONS:
        assert tool in checklist_body, f"{tool} missing from pre-emit checklist"


def test_writer_prompt_preemit_precedes_hard_stop() -> None:
    prompt = _writer_template()
    checklist_idx = prompt.find(CHECKLIST_HEADER)
    hard_stop_idx = prompt.find("## HARD STOP RULE")
    assert 0 <= checklist_idx < hard_stop_idx, (
        "Pre-emit checklist must appear before HARD STOP RULE, "
        "and HARD STOP RULE must remain the final section."
    )
