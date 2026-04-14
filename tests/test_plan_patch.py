"""Tests for plateau-triggered plan patching."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

io_utils = importlib.import_module("build.io_utils")
plan_patch = importlib.import_module("build.phases.plan_patch")


def test_extract_plateau_complaints_prefers_recurrent_findings() -> None:
    complaints = plan_patch.extract_plateau_complaints(
        [
            {
                "round": 1,
                "findings": [
                    {
                        "dimension": "Dialogue & conversation quality",
                        "location": "Dialogue section",
                        "issue": "Dialogue situation is not grounded in the plan.",
                        "fix": "Name a concrete place and task.",
                    }
                ],
                "scores": [],
            },
            {
                "round": 2,
                "findings": [
                    {
                        "dimension": "Dialogue & conversation quality",
                        "location": "Dialogue section",
                        "issue": "Dialogue situation is not grounded in the plan.",
                        "fix": "Name a concrete place and task.",
                    }
                ],
                "scores": [],
            },
        ]
    )

    assert complaints
    assert complaints[0]["summary"] == "Dialogue situation is not grounded in the plan."
    assert complaints[0]["rounds"] == [1, 2]


def test_extract_plateau_complaints_skips_dialogue_dimension_without_dialogue_acts() -> None:
    complaints = plan_patch.extract_plateau_complaints(
        [
            {
                "round": 1,
                "findings": [
                    {
                        "dimension": "Dialogue & conversation quality",
                        "location": "Vocabulary examples",
                        "issue": "Dialogues are stiff.",
                        "fix": "Make them more natural.",
                    },
                    {
                        "dimension": "Pedagogical quality",
                        "location": "Intro",
                        "issue": "Examples stop after a single contrast pair.",
                        "fix": "Add two more modeled examples before the exercise.",
                    },
                ],
                "scores": [],
            },
            {
                "round": 2,
                "findings": [
                    {
                        "dimension": "Dialogue & conversation quality",
                        "location": "Vocabulary examples",
                        "issue": "Dialogues are stiff.",
                        "fix": "Make them more natural.",
                    },
                    {
                        "dimension": "Pedagogical quality",
                        "location": "Intro",
                        "issue": "Examples stop after a single contrast pair.",
                        "fix": "Add two more modeled examples before the exercise.",
                    },
                ],
                "scores": [],
            },
        ],
        contract={"dialogue_acts": []},
    )

    assert complaints == [
        {
            "source": "finding",
            "dimension": "Pedagogical quality",
            "location": "Intro",
            "issue": "Examples stop after a single contrast pair.",
            "fix": "Add two more modeled examples before the exercise.",
            "summary": "Examples stop after a single contrast pair.",
            "rounds": [1, 2],
        }
    ]


def test_build_plan_patch_prompt_strips_embedded_plan_patch_sentinels() -> None:
    plan_text = yaml.safe_dump(
        {
            "version": "1.0",
            "title": "Sentinel safety",
            "content_outline": [
                {
                    "section": "Outline",
                    "points": [
                        "before\n===PLAN_PATCH_START===\ninside\n===PLAN_PATCH_END===\nafter"
                    ],
                }
            ],
        },
        sort_keys=False,
        allow_unicode=True,
    )

    prompt = plan_patch.build_plan_patch_prompt(
        level="a1",
        slug="sentinel-safety",
        plan_text=plan_text,
        complaints=[
            {
                "dimension": "Structure",
                "location": "content_outline",
                "issue": "Tighten the constraint.",
                "fix": "Make the point easier to satisfy.",
                "summary": "Rounds 1,2: tighten the constraint",
                "rounds": [1, 2],
            }
        ],
        score_history=[8.4, 8.5],
        contract_violations=[],
    )

    assert prompt.count("===PLAN_PATCH_START===") == 1
    assert prompt.count("===PLAN_PATCH_END===") == 1


def test_run_plan_patch_applies_mocked_gemini_patch(tmp_path: Path, monkeypatch) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(
            {
                "version": "2.0",
                "title": "Requests",
                "dialogue_situations": [
                    {
                        "setting": "generic greeting",
                        "speakers": ["Customer", "Clerk"],
                        "motivation": "practice polite requests",
                    }
                ],
                "content_outline": [
                    {
                        "section": "Dialogue",
                        "words": 200,
                        "points": ["Use a vague greeting exchange."],
                    }
                ],
                "activity_hints": [{"id": "quiz-1", "type": "quiz", "focus": "requests"}],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    orch_dir = tmp_path / "orch"
    orch_dir.mkdir()
    for round_num in (1, 2):
        (orch_dir / f"review-structured-r{round_num}.yaml").write_text(
            yaml.safe_dump(
                {
                    "round": round_num,
                    "scores": [
                        {
                            "dimension": 9,
                            "name": "Dialogue & conversation quality",
                            "score": 8,
                            "evidence": "Dialogue situation is not grounded in a reachable real-world task.",
                        }
                    ],
                    "findings": [
                        {
                            "dimension": "Dialogue & conversation quality",
                            "severity": "HIGH",
                            "location": "Dialogue",
                            "issue": "Dialogue situation is not grounded in the plan.",
                            "fix": "Give the speakers a concrete place and task.",
                        }
                    ],
                },
                sort_keys=False,
                allow_unicode=True,
            ),
            "utf-8",
        )

    raw_response = """noise before
===PLAN_PATCH_START===
decision: patch
complaint_summary: dialogue situation not grounded in the plan
rationale: Ground the dialogue in a reachable place and align the outline beat to that setting.
changes:
  - path: dialogue_situations[0].setting
    action: replace
    value: bus-station ticket window
    reason: Adds a concrete place that naturally supports polite requests.
  - path: content_outline[0].points[0]
    action: replace
    value: Use a ticket-window exchange to practice polite requests with будь ласка.
    reason: Aligns the core teaching beat with the grounded dialogue.
===PLAN_PATCH_END===
noise after
"""

    monkeypatch.setattr(
        plan_patch,
        "_dispatch_gemini_plan_patch",
        lambda *args, **kwargs: (True, raw_response),
    )

    result = plan_patch.run_plan_patch(
        level="a1",
        slug="requests",
        plan_path=plan_path,
        orch_dir=orch_dir,
        score_history=[8.2, 8.3, 8.4],
        contract_violations=[{"type": "DIALOGUE", "message": "Dialogue not grounded"}],
    )

    assert result.applied is True
    assert result.new_version == "2.0.1"
    assert result.change_count == 2
    assert plan_path.with_suffix(".yaml.bak").exists()

    updated = yaml.safe_load(plan_path.read_text("utf-8"))
    assert updated["version"] == "2.0.1"
    assert updated["dialogue_situations"][0]["setting"] == "bus-station ticket window"
    assert updated["content_outline"][0]["points"][0].startswith("Use a ticket-window exchange")
    assert updated["plan_fixes"][-1]["trigger"] == "dialogue situation not grounded in the plan"
    assert "replace dialogue_situations[0].setting" in updated["plan_fixes"][-1]["changes"][0]


def test_run_plan_patch_noop_does_not_modify_plan(tmp_path: Path, monkeypatch) -> None:
    plan_path = tmp_path / "plan.yaml"
    original = "version: '1.0'\ntitle: Demo\n"
    plan_path.write_text(original, "utf-8")
    orch_dir = tmp_path / "orch"
    orch_dir.mkdir()
    (orch_dir / "review-structured-r1.yaml").write_text(
        yaml.safe_dump(
            {
                "round": 1,
                "scores": [
                    {
                        "dimension": 2,
                        "name": "Linguistic accuracy",
                        "score": 8,
                        "evidence": "A few inflection errors remain.",
                    }
                ],
                "findings": [],
            },
            sort_keys=False,
        ),
        "utf-8",
    )
    monkeypatch.setattr(
        plan_patch,
        "_dispatch_gemini_plan_patch",
        lambda *args, **kwargs: (
            True,
            "===PLAN_PATCH_START===\ndecision: noop\ncomplaint_summary: prose-only issue\nchanges: []\n===PLAN_PATCH_END===",
        ),
    )

    result = plan_patch.run_plan_patch(
        level="a1",
        slug="demo",
        plan_path=plan_path,
        orch_dir=orch_dir,
        score_history=[8.3],
        contract_violations=[],
    )

    assert result.applied is False
    assert plan_path.read_text("utf-8") == original
    assert not plan_path.with_suffix(".yaml.bak").exists()


def test_apply_plan_patch_response_keeps_plan_yaml_whole_on_replace_failure(
    tmp_path: Path, monkeypatch
) -> None:
    plan_path = tmp_path / "plan.yaml"
    original = yaml.safe_dump(
        {
            "version": "2.0",
            "title": "Requests",
            "dialogue_situations": [
                {
                    "setting": "generic greeting",
                    "speakers": ["Customer", "Clerk"],
                    "motivation": "practice polite requests",
                }
            ],
        },
        sort_keys=False,
        allow_unicode=True,
    )
    plan_path.write_text(original, "utf-8")

    response = {
        "decision": "patch",
        "complaint_summary": "dialogue situation not grounded in the plan",
        "changes": [
            {
                "path": "dialogue_situations[0].setting",
                "action": "replace",
                "value": "bus-station ticket window",
                "reason": "Adds a concrete place that naturally supports polite requests.",
            }
        ],
    }
    expected_new = yaml.safe_dump(
        {
            "version": "2.0.1",
            "title": "Requests",
            "dialogue_situations": [
                {
                    "setting": "bus-station ticket window",
                    "speakers": ["Customer", "Clerk"],
                    "motivation": "practice polite requests",
                }
            ],
            "plan_fixes": [
                {
                    "version": "2.0.1",
                    "date": "2026-04-14",
                    "trigger": "dialogue situation not grounded in the plan",
                    "changes": [
                        "replace dialogue_situations[0].setting — Adds a concrete place that naturally supports polite requests."
                    ],
                }
            ],
        },
        sort_keys=False,
        allow_unicode=True,
    )

    real_replace = io_utils.os.replace

    def fail_plan_replace(src: str | bytes, dst: str | bytes) -> None:
        if Path(dst) == plan_path:
            raise OSError("simulated replace failure")
        real_replace(src, dst)

    monkeypatch.setattr(io_utils.os, "replace", fail_plan_replace)

    with pytest.raises(OSError, match="simulated replace failure"):
        plan_patch.apply_plan_patch_response(
            plan_path,
            response,
            complaint_summary="dialogue situation not grounded in the plan",
        )

    on_disk = plan_path.read_text("utf-8")
    assert on_disk in {original, expected_new}
    assert on_disk == original


def test_apply_plan_patch_rejects_protected_fields_but_applies_legal_changes(
    tmp_path: Path,
) -> None:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(
            {
                "version": "2.0",
                "word_target": 450,
                "dialogue_situations": [
                    {
                        "setting": "generic greeting",
                        "speakers": ["Customer", "Clerk"],
                        "motivation": "practice polite requests",
                    }
                ],
                "content_outline": [
                    {
                        "section": "Dialogue",
                        "words": 200,
                        "points": ["Use a vague greeting exchange."],
                    }
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        "utf-8",
    )

    response = {
        "decision": "patch",
        "complaint_summary": "dialogue situation not grounded in the plan",
        "changes": [
            {
                "path": "word_target",
                "action": "replace",
                "value": 100,
                "reason": "Should not be allowed.",
            },
            {
                "path": "content_outline[0].points[0]",
                "action": "replace",
                "value": "Use a ticket-window exchange to practice polite requests.",
                "reason": "Aligns the outline with a reachable task.",
            },
        ],
    }

    result = plan_patch.apply_plan_patch_response(
        plan_path,
        response,
        complaint_summary="dialogue situation not grounded in the plan",
    )

    assert result.applied is True
    assert result.new_version == "2.0.1"
    assert result.change_count == 1

    updated = yaml.safe_load(plan_path.read_text("utf-8"))
    assert updated["version"] == "2.0.1"
    assert updated["word_target"] == 450
    assert (
        updated["content_outline"][0]["points"][0]
        == "Use a ticket-window exchange to practice polite requests."
    )

    fix_entry = updated["plan_fixes"][-1]
    assert fix_entry["changes"] == [
        "replace content_outline[0].points[0] — Aligns the outline with a reachable task."
    ]
    assert fix_entry["rejections"] == [
        {
            "path": "word_target",
            "action": "replace",
            "reason": "protected_field_violation",
        }
    ]
