from __future__ import annotations

from scripts.build import linear_pipeline

WRITER_PROMPT = (
    linear_pipeline.PROJECT_ROOT / "scripts/build/phases/linear-write.md"
)


def test_writer_prompt_pins_translate_item_authoring_fields() -> None:
    prompt = WRITER_PROMPT.read_text(encoding="utf-8")

    assert "`translate` activity items" in prompt
    assert "MUST use `source`" in prompt
    assert "correct target answer is the option with `correct: true`" in prompt
    assert "Do NOT use `prompt:`/`answer:` aliases" in prompt
    assert "do NOT emit a bare `target:` field" in prompt
