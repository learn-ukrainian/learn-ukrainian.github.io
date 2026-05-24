from pathlib import Path

PHASES_DIR = Path("scripts/build/phases")
CHECKLIST_HEADING = "## Pre-emit verification"
OBLIGATION_LABELS = (
    "Textbook",
    "Multimedia",
    "VESUM",
    "Russianism",
)


def _pre_emit_checklist_body(prompt_path: Path) -> str:
    prompt = prompt_path.read_text(encoding="utf-8")
    heading_start = prompt.index(CHECKLIST_HEADING)
    next_heading_start = prompt.index("\n## ", heading_start + len(CHECKLIST_HEADING))
    return prompt[heading_start:next_heading_start]


def _assert_prompt_contains_pre_emit_checklist(prompt_name: str) -> None:
    checklist = _pre_emit_checklist_body(PHASES_DIR / prompt_name)

    assert "Pre-emit verification" in checklist
    for label in OBLIGATION_LABELS:
        assert label in checklist


def test_linear_write_contains_pre_emit_checklist() -> None:
    _assert_prompt_contains_pre_emit_checklist("linear-write.md")


def test_linear_write_grok_contains_pre_emit_checklist() -> None:
    _assert_prompt_contains_pre_emit_checklist("linear-write-grok.md")
