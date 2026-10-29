"""Prevention fixtures for the FOLK field and shape regressions in #4822."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline as pipeline

VALID_ACTIVITIES = [
    {"type": "essay-response", "prompt": "Discuss.", "instruction": "Write.",
     "model_answer": "Example.", "rubric": [{"criteria": "Content", "description": "Clear."}]},
    {"type": "critical-analysis", "prompt": "Analyze.", "model_answers": ["Example: quoted."]},
    {"type": "comparative-study", "items_to_compare": ["First", "Second"],
     "criteria": ["Form"], "prompt": "Compare."},
    {"type": "ritual-sequencing", "steps": ["First", "Second"], "correct_order": [0, 1]},
    {"type": "variant-comparison", "variants": [{"label": "First"}, {"label": "Second"}],
     "features": ["Form"]},
    {"type": "motif-formula", "passage": "Text.", "formulas": ["Formula."]},
    {"type": "performance", "prompt": "Perform.", "self_check": ["Clear: yes."]},
]


@pytest.mark.parametrize("activity", VALID_ACTIVITIES, ids=lambda activity: activity["type"])
def test_folk_schema_accepts_canonical_writer_shapes(activity: dict) -> None:
    """Canonical instruction, model_answers, and rubric objects survive emission."""
    activity = {"id": "example", **activity}
    pipeline._validate_writer_json_artifact("activities.yaml", [activity])
    emitted = yaml.safe_load(yaml.safe_dump([activity]))
    assert pipeline._activity_schema_gate(emitted, level="folk")["passed"] is True
    prompt = pipeline._render_component_props_schema(activity["type"], level="folk")
    assert '"additionalProperties": false' in prompt
    assert "Quote YAML string list entries" in prompt


@pytest.mark.parametrize(
    ("index", "patch", "field"),
    [
        (0, {"source_reading": "reading"}, "source_reading"),
        (0, {"task": "Write."}, "task"),
        (0, {"peer_review_guidelines": ["Check."]}, "peer_review_guidelines"),
        (1, {"model_answer": "Example."}, "model_answer"),
        (0, {"rubric": ["Content: clear"]}, "rubric"),
        (1, {"model_answers": yaml.safe_load("- Example: unquoted")}, "model_answers"),
        (3, {"correct_order": ["First", "Second"]}, "correct_order"),
    ],
    ids=["source-reading", "task-instead-of-instruction", "peer-guidance",
         "singular-model-answer", "string-rubric", "unquoted-colon", "display-order"],
)
def test_folk_forbidden_fields_and_shapes_block_handoff(
    tmp_path: Path, index: int, patch: dict, field: str,
) -> None:
    """All seven reported defect classes fail the existing post-emit schema gate."""
    activity = {**deepcopy(VALID_ACTIVITIES[index]), **patch}
    plan = {
        "module": "folk-001", "level": "FOLK", "sequence": 1, "slug": "example",
        "title": "Example", "subtitle": "Example", "word_target": 1,
        "content_outline": [{"section": "Example", "words": 1, "points": []}],
        "references": [{"title": "Fixture reference"}],
    }
    (tmp_path / "plan.yaml").write_text(yaml.safe_dump(plan), encoding="utf-8")
    (tmp_path / "module.md").write_text("# Example\n", encoding="utf-8")
    for name, data in (("activities", [activity]), ("vocabulary", []), ("resources", [])):
        (tmp_path / f"{name}.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")

    report = pipeline.run_python_qg(tmp_path, tmp_path / "plan.yaml")

    assert report["passed"] is False
    assert report["gates"]["activity_schema"]["passed"] is False
    assert field in report["gates"]["activity_schema"]["message"]
    assert "word_count" not in report["gates"]
