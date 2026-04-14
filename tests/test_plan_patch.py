"""Tests for plateau-triggered plan patching."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import yaml

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

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
