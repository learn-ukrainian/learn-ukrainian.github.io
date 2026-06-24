from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.build import linear_pipeline


def _plan_with_activity_hints() -> dict[str, Any]:
    return {
        "level": "b1",
        "sequence": 1,
        "module": 1,
        "slug": "iterative-activities",
        "title": "Iterative activities",
        "content_outline": [
            {"section": "Intro", "words": 1, "points": ["Open the topic."]},
            {"section": "Practice", "words": 1, "points": ["Apply the topic."]},
        ],
        "activity_hints": [
            {
                "after_section": "Intro",
                "focus": "Check the opening claim.",
                "placement": "inline",
                "type": "quiz",
            },
            {
                "focus": "Reflect on the whole module.",
                "placement": "workbook",
                "type": "performance",
            },
        ],
    }


def _section_response(section_id: str, title: str) -> str:
    payload = {
        "section_id": section_id,
        "markdown": f"## {title}\n\nGrounded sentence for {title}.",
        "citations_used": [],
        "primary_readings_used": [],
        "vocab_candidates": [],
        "activity_refs": [],
        "self_check": {},
    }
    return "```section_artifact.json\n" + json.dumps(payload) + "\n```"


def _activities_response() -> str:
    payload = [
        {
            "type": "quiz",
            "title": "Opening Check",
            "instruction": "Choose the best answer.",
            "items": [
                {
                    "question": "What does the opening section do?",
                    "answer": "It opens the topic.",
                    "options": ["It opens the topic.", "It introduces a new alphabet."],
                }
            ],
        },
        {
            "type": "performance",
            "title": "Short Retelling",
            "instruction": "Retell the key idea aloud.",
            "prompt": "Retell the key idea aloud.",
            "fragment": "Grounded sentence for Practice.",
            "self_check": ["I used one idea from each section."],
        },
    ]
    return "```json file=activities.yaml\n" + json.dumps(payload) + "\n```"


def test_iterative_writer_generates_schema_valid_activities(tmp_path: Path) -> None:
    calls: list[str] = []

    def invoke(prompt: str, writer: str, **kwargs: Any) -> str:
        del prompt, writer
        section = kwargs["sections"][0]
        calls.append(section)
        if section == linear_pipeline.ITERATIVE_ACTIVITY_WRITER_SECTION:
            return _activities_response()
        return _section_response(f"s{len(calls)}", section)

    result = linear_pipeline.run_iterative_writer(
        _plan_with_activity_hints(),
        knowledge_packet="",
        readings=[],
        writer="gemini-tools",
        invoke_fn=invoke,
        cwd=tmp_path,
        module="folk/iterative-activities",
    )

    activities = yaml.safe_load(result["activities_yaml"])
    assert calls == ["Intro", "Practice", linear_pipeline.ITERATIVE_ACTIVITY_WRITER_SECTION]
    assert isinstance(activities, list)
    assert linear_pipeline._activity_schema_gate(activities)["passed"] is True
    for activity in activities:
        assert not {"after_section", "focus", "placement"} & set(activity)
    performance = next(activity for activity in activities if activity["type"] == "performance")
    assert isinstance(performance["self_check"], list)


def test_iterative_activity_parser_rejects_raw_plan_hint_fields() -> None:
    output = """```json file=activities.yaml
[
  {
    "type": "quiz",
    "after_section": "Intro",
    "focus": "Check the opening claim.",
    "placement": "inline"
  }
]
```"""

    with pytest.raises(linear_pipeline.LinearPipelineError, match="unexpected fields"):
        linear_pipeline.parse_iterative_activities_output(output)
