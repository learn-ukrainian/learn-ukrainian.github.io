from __future__ import annotations

import json
from typing import Any

from scripts.build import linear_pipeline


def _plan() -> dict[str, Any]:
    return {
        "content_outline": [
            {"section": "Opening", "words": 1, "points": ["Introduce the topic."]},
            {"section": "Practice", "words": 1, "points": ["Extend the topic."]},
        ]
    }


def _artifact(section_id: str, candidates: list[dict[str, Any]]) -> linear_pipeline.SectionArtifact:
    return linear_pipeline.SectionArtifact(
        section_id=section_id,
        markdown=f"## Section {section_id}\n\nText.",
        citations_used=[],
        primary_readings_used=[],
        vocab_candidates=candidates,
        activity_refs=[],
        self_check={},
    )


def _candidate(
    word: str,
    translation: str,
    *,
    pos: str = "noun",
    usage: str | None = None,
) -> dict[str, Any]:
    return {
        "word": word,
        "ipa": "test-ipa",
        "pos": pos,
        "definition": f"Definition for {word}.",
        "translation": translation,
        "usage": f"{word} з'являється в уривку." if usage is None else usage,
    }


def test_merge_vocab_harvests_section_candidates_as_valid_schema_entries() -> None:
    artifacts = [
        _artifact(
            "s1",
            [
                _candidate("веснянка", "spring ritual song"),
                _candidate("гаївка", "Easter round dance song"),
            ],
        ),
        _artifact("s2", [_candidate("приспів", "refrain")]),
    ]

    vocab = linear_pipeline._merge_vocab(_plan(), artifacts)

    assert vocab == [
        {
            "lemma": "веснянка",
            "translation": "spring ritual song",
            "pos": "noun",
            "usage": "веснянка з'являється в уривку.",
        },
        {
            "lemma": "гаївка",
            "translation": "Easter round dance song",
            "pos": "noun",
            "usage": "гаївка з'являється в уривку.",
        },
        {
            "lemma": "приспів",
            "translation": "refrain",
            "pos": "noun",
            "usage": "приспів з'являється в уривку.",
        },
    ]
    linear_pipeline._validate_writer_json_artifact("vocabulary.yaml", vocab)


def test_merge_vocab_dedupes_by_casefolded_lemma_preserving_first_order() -> None:
    artifacts = [
        _artifact(
            "s1",
            [
                _candidate("Веснянка", "spring ritual song"),
                _candidate("веснянка", "duplicate gloss"),
            ],
        ),
        _artifact("s2", [_candidate("гаївка", "Easter round dance song")]),
    ]

    vocab = linear_pipeline._merge_vocab(_plan(), artifacts)

    assert [item["lemma"] for item in vocab] == ["Веснянка", "гаївка"]
    assert vocab[0]["translation"] == "spring ritual song"


def test_merge_vocab_drops_candidates_missing_required_fields() -> None:
    missing_word = _candidate("", "missing word")
    missing_translation = _candidate("спів", "")
    missing_pos = _candidate("коло", "circle song", pos="")
    missing_usage = _candidate("лад", "order", usage="")
    valid = _candidate("обряд", "rite")

    vocab = linear_pipeline._merge_vocab(
        _plan(),
        [_artifact("s1", [missing_word, missing_translation, missing_pos, missing_usage, valid])],
    )

    assert vocab == [
        {
            "lemma": "обряд",
            "translation": "rite",
            "pos": "noun",
            "usage": "обряд з'являється в уривку.",
        }
    ]


def test_merge_vocab_empty_input_returns_empty_list() -> None:
    assert linear_pipeline._merge_vocab(_plan(), []) == []
    assert linear_pipeline._merge_vocab(_plan(), [_artifact("s1", [])]) == []


def test_parse_section_writer_output_preserves_translation_and_usage() -> None:
    task = linear_pipeline.SectionTask(
        section_id="s1",
        title="Opening",
        word_budget=1,
        points=[],
        assigned_readings=[],
        knowledge_slice="",
        framing_rules="",
        ledger=linear_pipeline.Ledger(),
    )
    payload = {
        "section_id": "s1",
        "markdown": "## Opening\n\nText.",
        "citations_used": [],
        "primary_readings_used": [],
        "vocab_candidates": [
            {
                "word": "веснянка",
                "ipa": "test-ipa",
                "pos": "noun",
                "definition": "A spring ritual song.",
                "translation": "spring ritual song",
                "usage": "Веснянка звучить у весняному колі.",
            }
        ],
        "activity_refs": [],
        "self_check": {},
    }
    output = "```json file=section_artifact.json\n" + json.dumps(payload) + "\n```"

    artifact = linear_pipeline.parse_section_writer_output(output, task)

    assert artifact.vocab_candidates[0]["translation"] == "spring ritual song"
    assert artifact.vocab_candidates[0]["usage"] == "Веснянка звучить у весняному колі."
