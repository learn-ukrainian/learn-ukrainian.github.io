from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.build import linear_pipeline


def _task(section_id: str = "s1", title: str = "Opening") -> linear_pipeline.SectionTask:
    return linear_pipeline.SectionTask(
        section_id=section_id,
        title=title,
        word_budget=1,
        points=["Cover the section."],
        assigned_readings=[],
        knowledge_slice="",
        framing_rules="",
        ledger=linear_pipeline.Ledger(),
    )


def _metadata(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "section_id": "s1",
        "citations_used": ["cite-1"],
        "primary_readings_used": ["reading-1"],
        "vocab_candidates": [
            {
                "word": "гаївка",
                "ipa": "ha-yiv-ka",
                "pos": "noun",
                "definition": "Обрядова весняна пісня або хоровод.",
                "translation": "Easter round dance song",
                "usage": "Гаївка звучить у колі біля церкви.",
            }
        ],
        "activity_refs": ["act-1"],
        "self_check": {"grounded": True},
    }
    payload.update(overrides)
    return payload


def _section_output(markdown: str, metadata_body: str | None = None) -> str:
    body = metadata_body
    if body is None:
        body = json.dumps(_metadata(), ensure_ascii=False, indent=2)
    return (
        f"````markdown file=section.md\n{markdown}\n````\n"
        f"```json file=section_artifact.json\n{body}\n```"
    )


ADVERSARIAL_MARKDOWN = (
    'Перший абзац містить слова "гай", {обряд}, C:\\спів і «весняний хід».\n'
    "\n"
    'Другий абзац не структурований як JSON: {"не": "метадані"}.\n'
    "\n"
    "```text\n"
    'literal { brace } and "quote" plus \\ backslash\n'
    "```\n"
    "\n"
    "> Ой весна, весна, днем красна,\n"
    "> Що ти нам принесла?"
)


def test_parse_section_writer_output_preserves_adversarial_markdown_verbatim() -> None:
    artifact = linear_pipeline.parse_section_writer_output(
        _section_output(ADVERSARIAL_MARKDOWN),
        _task(),
    )

    assert artifact.markdown == ADVERSARIAL_MARKDOWN
    assert artifact.section_id == "s1"
    assert artifact.citations_used == ["cite-1"]
    assert artifact.primary_readings_used == ["reading-1"]
    assert artifact.activity_refs == ["act-1"]
    assert artifact.self_check == {"grounded": True}
    assert artifact.vocab_candidates[0]["translation"] == "Easter round dance song"
    assert artifact.vocab_candidates[0]["usage"] == "Гаївка звучить у колі біля церкви."


def test_parse_section_writer_output_handles_hay_quote_pattern() -> None:
    markdown = (
        'Назва гаївки походить від слова "гай" — сакрального місця, '
        "де громада співає весняний приспів."
    )

    artifact = linear_pipeline.parse_section_writer_output(
        _section_output(markdown),
        _task(),
    )

    assert artifact.markdown == markdown
    assert 'слова "гай"' in artifact.markdown


def test_parse_section_writer_output_recovers_metadata_with_trailing_commas() -> None:
    metadata_body = """
{
  "section_id": "s1",
  "citations_used": ["cite-1",],
  "primary_readings_used": [],
  "vocab_candidates": [],
  "activity_refs": [],
  "self_check": {"repair": true},
}
""".strip()

    artifact = linear_pipeline.parse_section_writer_output(
        _section_output("Body with clean markdown.", metadata_body),
        _task(),
    )

    assert artifact.markdown == "Body with clean markdown."
    assert artifact.citations_used == ["cite-1"]
    assert artifact.self_check == {"repair": True}


def test_parse_section_writer_output_rejects_unrecoverable_metadata_with_section() -> None:
    metadata_body = '{"section_id": "s1", "citations_used": [}'

    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match=r"s1.*section_artifact\.json.*unrecoverable",
    ):
        linear_pipeline.parse_section_writer_output(
            _section_output("Body still must not be dropped.", metadata_body),
            _task(),
        )


def test_render_section_writer_prompt_requires_separate_markdown_and_json_blocks() -> None:
    task = _task()
    prompt = linear_pipeline.render_section_writer_prompt(
        plan={"content_outline": [{"section": "Opening", "words": 1, "points": []}]},
        task=task,
        knowledge_packet="",
        readings=[],
    )

    assert "````markdown file=section.md" in prompt
    assert "```json file=section_artifact.json" in prompt
    assert "Do NOT put the section prose inside the JSON" in prompt
    assert '"markdown":' not in prompt
