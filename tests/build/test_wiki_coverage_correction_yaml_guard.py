from __future__ import annotations

import json
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


def _events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


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


def test_oversize_insert_text_rejected_and_event_emitted() -> None:
    body = "x" * 241
    fixes = [{"insert_after": "anchor", "text": body}]

    accepted, rejected = linear_pipeline._validate_reviewer_fix_shapes(fixes)
    events: list[dict[str, Any]] = []
    linear_pipeline._emit_reviewer_fix_oversize_rejections(
        rejected,
        gate="wiki_coverage_gate",
        group_key="group",
        event_sink=_sink(events),
    )

    assert accepted == []
    assert rejected == fixes
    assert events[0]["event"] == "reviewer_fix_oversize_rejected"
    assert events[0]["body_field"] == "text"
    assert events[0]["body_len"] == 241
    assert events[0]["line_count"] == 1


def test_within_limit_fix_accepted() -> None:
    fixes = [{"find": "old", "replace": "line 1\nline 2\nline 3"}]

    accepted, rejected = linear_pipeline._validate_reviewer_fix_shapes(fixes)

    assert accepted == fixes
    assert rejected == []


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


def test_activities_yaml_valid_shape_passes() -> None:
    linear_pipeline._validate_wiki_coverage_artifact_text(
        "activities.yaml",
        VALID_ACTIVITIES,
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


def test_python_qg_reviewer_correction_rejects_oversize_fix(
    tmp_path: Path,
) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    module_path = module_dir / "module.md"
    module_path.write_text("Anchor sentence.\n", encoding="utf-8")
    telemetry = tmp_path / "events.jsonl"
    oversize = "\n".join(f"line {index}" for index in range(10))

    with linear_pipeline.telemetry_event_sink(telemetry):
        changed, unmatched = linear_pipeline._apply_python_qg_correction(
            "l2_exposure_floor",
            {"gates": {"l2_exposure_floor": {"passed": False}}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=None,
            reviewer_corrector=lambda _context: (
                "<fixes><fix><find>Anchor sentence.</find>"
                f"<replace>{oversize}</replace></fix></fixes>"
            ),
            dictionary_lookup_fn=None,
            writer="claude-tools",
            invoker=None,
        )

    assert changed is True
    assert unmatched == frozenset()
    assert module_path.read_text(encoding="utf-8") == "Anchor sentence.\n"
    events = _events(telemetry)
    assert [event["event"] for event in events] == ["reviewer_fix_oversize_rejected"]
    assert events[0]["gate"] == "l2_exposure_floor"
