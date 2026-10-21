from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline

VALID_ACTIVITIES = """\
- id: act-1
  type: error-correction
  items:
  - sentence: Я прокидаюся.
    error: прокидаєшся
    correction: прокидаюся
"""


def _sink(events: list[dict[str, Any]]):
    def append(event: str, **fields: Any) -> None:
        events.append({"event": event, **fields})

    return append


def test_oversize_replace_rejected_and_event_emitted() -> None:
    body = "\n".join(f"line {index}" for index in range(10))
    fixes = [{"find": "old", "replace": body}]

    accepted, rejected = linear_pipeline._validate_reviewer_fix_shapes(fixes)
    events: list[dict[str, Any]] = []
    linear_pipeline._emit_reviewer_fix_oversize_rejections(
        rejected,
        gate="wiki_coverage_gate",
        group_key="(artifact=activities.yaml, obligation_type=l2_error)",
        event_sink=_sink(events),
    )

    assert accepted == []
    assert rejected == fixes
    assert events == [
        {
            "event": "reviewer_fix_oversize_rejected",
            "gate": "wiki_coverage_gate",
            "group_key": "(artifact=activities.yaml, obligation_type=l2_error)",
            "body_field": "replace",
            "body_len": len(body),
            "line_count": 10,
            "body_preview": body,
        }
    ]


def test_activities_yaml_m20_pronunciation_scalar_raises() -> None:
    malformed = """\
- id: act-1
  type: error-correction
  items:
  - sentence: Вимова: [прокидайешся]
    error: Вимова: [прокидайешся]
    correction: Вимова: [прокидайес':а]
"""

    with pytest.raises(linear_pipeline.LinearPipelineError, match="invalid YAML"):
        linear_pipeline._validate_wiki_coverage_artifact_text(
            "activities.yaml",
            malformed,
        )


def test_round_trip_mismatch_raises() -> None:
    non_portable = """\
- id: act-1
  type: select
  notes: !!omap
  - a: 1
  - b: 2
"""

    with pytest.raises(linear_pipeline.LinearPipelineError, match="round-trip"):
        linear_pipeline._validate_wiki_coverage_artifact_text(
            "activities.yaml",
            non_portable,
        )


def test_apply_wiki_coverage_fixes_rejects_oversize_and_preserves_artifact(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "activities.yaml"
    artifact_path.write_text(VALID_ACTIVITIES, encoding="utf-8")
    oversize = "\n".join(f"- id: act-{index}" for index in range(10))
    events: list[dict[str, Any]] = []

    applied = linear_pipeline._apply_wiki_coverage_fixes(
        module_dir=tmp_path,
        artifact="activities.yaml",
        fixes=[{"find": VALID_ACTIVITIES, "replace": oversize}],
        phase="batched",
        iteration=1,
        event_sink=_sink(events),
        group_key="(artifact=activities.yaml, obligation_type=l2_error)",
    )

    assert applied == 0
    assert artifact_path.read_text(encoding="utf-8") == VALID_ACTIVITIES
    assert events[0]["event"] == "reviewer_fix_oversize_rejected"
    assert events[0]["gate"] == "wiki_coverage_gate"
    assert events[0]["line_count"] == 10


def test_apply_wiki_coverage_fixes_valid_fix_applies_and_validates(
    tmp_path: Path,
) -> None:
    artifact_path = tmp_path / "activities.yaml"
    artifact_path.write_text(VALID_ACTIVITIES, encoding="utf-8")
    events: list[dict[str, Any]] = []

    applied = linear_pipeline._apply_wiki_coverage_fixes(
        module_dir=tmp_path,
        artifact="activities.yaml",
        fixes=[
            {
                "find": "  - sentence: Я прокидаюся.\n",
                "replace": "  - sentence: Я прокидаюся зараз.\n",
            }
        ],
        phase="batched",
        iteration=1,
        event_sink=_sink(events),
        group_key="(artifact=activities.yaml, obligation_type=l2_error)",
    )

    assert applied == 1
    assert "Я прокидаюся зараз." in artifact_path.read_text(encoding="utf-8")
    assert events[-1]["event"] == "wiki_coverage_correction_fixes_applied"
