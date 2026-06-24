from __future__ import annotations

from scripts.build import linear_pipeline


def test_section_writer_prompt_marks_word_budget_as_hard_minimum() -> None:
    task = linear_pipeline.SectionTask(
        section_id="s1",
        title="Opening",
        word_budget=120,
        points=["Frame the topic."],
        assigned_readings=[],
        knowledge_slice="",
        framing_rules="",
        ledger=linear_pipeline.Ledger(),
    )

    prompt = linear_pipeline.render_section_writer_prompt(
        plan={"content_outline": [{"section": "Opening", "words": 120, "points": []}]},
        task=task,
        knowledge_packet="",
        readings=[],
    )

    assert "- hard_minimum_words: 120" in prompt
    assert "- upper_range_words: 180" in prompt
    assert "Write AT LEAST 120 words for this section" in prompt
    assert "aim for 120-180 words" in prompt
    assert "Undershooting the target is a failure." in prompt
