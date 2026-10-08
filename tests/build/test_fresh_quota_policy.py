"""Quota-free sizing, retaining the critic's pre-existing #9565 held-out draft."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.build.fresh import assemble, runner
from scripts.curriculum.evidence import lock
from scripts.curriculum.resolver.inputs import Allowlist
from scripts.curriculum.validate import codes
from tests.build.test_fresh_page_safety import FIXTURE, reassemble_attempt5

pytestmark = pytest.mark.reads_content
REPO = Path(__file__).resolve().parents[2]
H1_SHA256 = "73ea2720238389d491067593a8b5f7401754518381c7be4ac5e34246de57a999"


def held_out(target=None):
    raw = (FIXTURE / "inputs.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == H1_SHA256
    data = json.loads(raw)
    lesson = data["plan"]["lessons"][0]
    if target is None:
        lesson.pop("word_target")
    else:
        lesson["word_target"] = target
    return data


def expanded(data):
    document, _ = assemble.assemble_expanded_document(
        data["draft"], data["plan"], data["pack"], data["words"], "a1", "sounds-letters-and-hello", 1
    )
    return document


@pytest.mark.parametrize("target", [None, 550])
def test_short_complete_lesson_passes(target):
    data = held_out(target)
    assert runner.check_3_structure(data["draft"], data["plan"]["lessons"][0])["status"] == "passed"
    row = runner.check_6_count(expanded(data), data["words"])
    assert row["check"] == 6 and row["status"] == "passed"
    assert row["details"] == {
        "urok_tokens": 306,
        "ukrainian_tokens": 7,
        "ukrainian_share": 0.022876,
        "not_checked": ["lesson_structural_minimums_not_calibrated"],
    }
    # Real assembly/stress/rendering with the pinned draft and resolution stream.
    page, _ = reassemble_attempt5(data)
    original = json.loads((FIXTURE / "inputs.json").read_bytes())
    original_page, _ = reassemble_attempt5(original)
    assert page == original_page


@pytest.mark.parametrize("mutation,reason", [("step", "step_ids_or_order"), ("practice", "step_practice_order")])
def test_incomplete_lesson_still_fails(mutation, reason):
    data = held_out()
    if mutation == "step":
        data["draft"]["steps"].pop(0)
    else:
        step = next(step for step in data["draft"]["steps"] if any(b["kind"] == "activity" for b in step["blocks"]))
        step["blocks"] = [b for b in step["blocks"] if b["kind"] != "activity"]
    row = runner.check_3_structure(data["draft"], data["plan"]["lessons"][0])
    assert (row["check"], row["status"], row["reason"]) == (3, "failed", reason)


def test_missing_gloss_still_fails():
    data = held_out()
    doc = expanded(data)
    gloss = next(unit for unit in doc["units"] if unit["role"] == "gloss_ref" and unit["tab"] == "urok")
    rid = gloss["text"].removeprefix("{{gloss:").removesuffix("}}")
    words = copy.deepcopy(data["words"])
    words["words"] = [word for word in words["words"] if word["id"] != rid]
    row = runner.check_6_count(doc, words)
    assert (row["check"], row["status"], row["reason"], row["layer"]) == (6, "failed", "gloss_record_missing", "pack")


@pytest.mark.parametrize("target", [None, 550])
def test_held_out_runner_retains_current_listening_gate(tmp_path, target):
    """The archived draft predates a retained gate; quota removal cannot bypass it.

    Full runner call-site coverage is supplied separately by the complete integration
    fixture in test_fresh_runner; this immutable oracle supplies counts and rendering.
    """
    data = held_out(target)
    state = tmp_path / "state"
    state.mkdir()
    lock.write(state / "lesson-1.draft.yaml", lock.yaml_bytes(data["draft"]))

    report = runner.run_lesson(
        "a1", "sounds-letters-and-hello", 1,
        draft=data["draft"], plan=data["plan"], pack=data["pack"], words=data["words"],
        state_dir=state, repo_root=tmp_path, plans_dir=tmp_path, evidence_dir=tmp_path,
        allowlist=Allowlist.from_records(data["words"]["words"], words_lock="f" * 64),
        sources=object(),
    )
    assert [row["status"] for row in report["checks"][:3]] == ["passed"] * 3, report
    row = report["checks"][3]
    assert (row["check"], row["status"], row["reason"], row["layer"]) == (
        4, "failed", "listening_model_undeclared", "pack"
    )
    assert all(row["status"] == "not_checked" for row in report["checks"][4:])


def test_counts_remain_descriptive():
    row = runner.check_6_count({"units": []})
    assert row["status"] == "passed"
    assert row["details"]["urok_tokens"] == row["details"]["ukrainian_share"] == 0
    formula = {"id": "W-1", "kind": "formula", "text": "one two", "gloss_en": "three"}
    row = runner.check_6_count(
        {"units": [{"tab": "urok", "role": "gloss_ref", "text": "{{gloss:W-1}}"}]}, {"words": [formula]}
    )
    assert row["details"]["urok_tokens"] == 3
    assert row["details"]["ukrainian_tokens"] == 2
    assert runner.check_6_count({"units": [{"tab": "urok", "role": "gloss_ref", "text": "invalid"}]})["status"] == "failed"


def test_quota_calibration_outcomes_retired():
    retired = {"word_target_not_calibrated", "lesson_activity_minimums_not_calibrated"}
    assert not hasattr(codes, "WORD_TARGET_NOT_CALIBRATED")
    assert not hasattr(codes, "LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED")
    assert not retired.intersection(codes.NOT_CHECKED_CODES)
    assert not retired.intersection(codes.DESCRIPTIONS)
    assert "minutes_constants_undefined" in codes.NOT_CHECKED_CODES


@pytest.mark.parametrize("name", ["plan-review", "lesson-review", "lesson-rereview"])
def test_review_sizing_is_job_adequacy(name):
    text = (REPO / "scripts/review/prompts" / f"{name}.md.j2").read_text()
    assert "no word or activity target" in text
    assert "job adequacy" in text and "45 minutes" in text and "counts are descriptive" in text


@pytest.mark.parametrize("path", [
    "scripts/review/prompts/plan-review.md.j2",
    "docs/epics/fresh-build-review-contracts.md",
    "docs/epics/fresh-build-a1-arc.md",
])
def test_plan_review_sizing_anchor_is_guidance(path):
    text = " ".join((REPO / path).read_text().split())
    assert "too much new inventory for an hour" not in text
    assert "too much new inventory for about 45 minutes of total learner work; guidance, not a quota" in text
