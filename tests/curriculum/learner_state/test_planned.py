"""Tests for planned learner state (docs/epics/fresh-build-plan-schema.md §4, #8414).

Fixtures are tiny synthetic plans and word stores built in test code.
No fixture writes Ukrainian forms beyond placeholders.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.planned import PlannedStateError, planned_state

pytestmark = pytest.mark.reads_content


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _make_plan(
    position: int,
    slug: str,
    lessons: list[dict],
    level: str = "a1",
) -> dict:
    return {
        "plan_schema": 2,
        "module": slug,
        "level": level,
        "sequence": position,
        "slug": slug,
        "version": "1",
        "title": f"Plan for position {position}",
        "arc_ref": {"level": level, "position": position},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{level}/{slug}.yaml", "sha256": "0" * 64},
        "lessons": lessons,
    }


def _setup_synthetic_curriculum(root: Path, level: str = "a1") -> tuple[Path, Path]:
    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_dir = root / f"curriculum/l2-uk-en/evidence/{level}"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Base layer request
    base_req = {
        "request_schema": 1,
        "level": level,
        "words": [
            {"lemma": "base-pron-1", "pos": "pron", "want": "new", "note": "personal pronoun"},
            {"lemma": "base-prep-1", "pos": "prep", "want": "new", "note": "preposition"},
        ],
    }
    _write_yaml(evidence_dir / "_base.request.yaml", base_req)

    # Word store
    words_store = {
        "evidence_schema": 1,
        "level": level,
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {"id": "W-BASE-01", "lemma": "base-pron-1", "pos": "pron"},
            {"id": "W-BASE-02", "lemma": "base-prep-1", "pos": "prep"},
            {"id": "W-CORE-01", "lemma": "core-one", "pos": "noun"},
            {"id": "W-CORE-02", "lemma": "core-two", "pos": "verb"},
            {"id": "W-CORE-03", "lemma": "core-three", "pos": "adj"},
            {"id": "W-INC-01", "lemma": "inc-one", "pos": "noun"},
            {"id": "W-NAME-01", "lemma": "name-one", "pos": "noun"},
            {"id": "W-NAME-02", "lemma": "place-one", "pos": "noun"},
            {"id": "W-NAME-03", "lemma": "name-two", "pos": "noun"},
        ],
    }
    _write_yaml(evidence_dir / "_words.yaml", words_store)

    # Plan 1 (position 1)
    plan_pos_1 = _make_plan(
        position=1,
        slug="module-one",
        level=level,
        lessons=[
            {
                "n": 1,
                "slug": "m01-l01",
                "title": "Lesson 1",
                "kind": "teach",
                "job": "Teach thing 1",
                "rationale": "Order rationale",
                "word_target": 10,
                "inventory": {
                    "phonetics": {"letters": ["А", "Б"], "sounds": []},
                    "grammar": [{"id": "G-a1-001", "point": "Grammar point 1"}],
                    "vocabulary": {
                        "core": [{"lemma": "core-one", "evidence": "W-CORE-01"}],
                        "incidental": [{"lemma": "inc-one", "evidence": "W-INC-01"}],
                        "recycled": [],
                    },
                },
                "dialogue": {
                    "step": "s1",
                    "speakers": [{"name": "Speaker One", "evidence": "W-NAME-01"}],
                    "places": [{"name": "Place One", "evidence": "W-NAME-02"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "Teach step",
                        "introduces": {"letters": ["А", "Б"], "grammar": ["G-a1-001"], "vocabulary": ["W-CORE-01"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}],
            },
            {
                "n": 2,
                "slug": "m01-l02",
                "title": "Lesson 2",
                "kind": "teach",
                "job": "Teach thing 2",
                "rationale": "Order rationale",
                "word_target": 10,
                "inventory": {
                    "grammar": [{"id": "G-a1-002", "point": "Grammar point 2"}],
                    "vocabulary": {
                        "core": [{"lemma": "core-two", "evidence": "W-CORE-02"}],
                        "recycled": ["W-CORE-01"],
                    },
                },
                "dialogue": {
                    "step": "s1",
                    "speakers": [{"name": "Speaker Two", "evidence": "W-NAME-03"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "Teach step 2",
                        "introduces": {"letters": [], "grammar": ["G-a1-002"], "vocabulary": ["W-CORE-02"]},
                        "uses": {"grammar": [], "vocabulary": ["W-CORE-01"]},
                        "evidence": ["E-02"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}],
            },
        ],
    )
    _write_yaml(plans_dir / "module-one.yaml", plan_pos_1)

    # Plan 2 (position 2)
    plan_pos_2 = _make_plan(
        position=2,
        slug="module-two",
        level=level,
        lessons=[
            {
                "n": 1,
                "slug": "m02-l01",
                "title": "Module 2 Lesson 1",
                "kind": "teach",
                "job": "Teach thing 3",
                "rationale": "Order rationale",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [{"lemma": "core-three", "evidence": "W-CORE-03"}],
                    },
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "Teach step 3",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-CORE-03"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-03"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}],
            }
        ],
    )
    _write_yaml(plans_dir / "module-two.yaml", plan_pos_2)

    return plans_dir, evidence_dir


def test_core_id_known_in_lesson_2_and_next_position(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # Position 1, lesson 1: core-one is NOT in core_ids yet (introduced in this lesson)
    s1_1 = planned_state("a1", 1, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-CORE-01" not in s1_1.core_ids
    assert s1_1.cumulative_core_count == 0

    # Position 1, lesson 2: core-one IS known
    s1_2 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-CORE-01" in s1_2.core_ids
    assert s1_2.core_ids["W-CORE-01"] == {"position": 1, "lesson": 1}
    assert s1_2.cumulative_core_count == 1

    # Position 2, lesson 1: both core-one and core-two are known
    s2_1 = planned_state("a1", 2, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-CORE-01" in s2_1.core_ids
    assert "W-CORE-02" in s2_1.core_ids
    assert s2_1.cumulative_core_count == 2


def test_incidental_id_never_enters_state(tmp_path: Path) -> None:
    """Rule 2: incidental never enters state, in the lesson that lists it or later."""
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # Check lesson 1, lesson 2, and next position
    s1_1 = planned_state("a1", 1, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    s1_2 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    s2_1 = planned_state("a1", 2, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)

    for state in (s1_1, s1_2, s2_1):
        assert "W-INC-01" not in state.core_ids
        assert "W-INC-01" not in state.base_ids
        assert "W-INC-01" not in state.name_ids
        assert "W-INC-01" not in state.all_allowed_ids


def test_id_introduced_at_later_position_not_known(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # Position 1, lesson 2: W-CORE-03 (introduced at pos 2) is NOT known
    s1_2 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-CORE-03" not in s1_2.core_ids
    assert "W-CORE-03" not in s1_2.all_allowed_ids


def test_base_ids_present_and_excluded_from_cumulative_core_count(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    s1_1 = planned_state("a1", 1, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert s1_1.base_ids == ("W-BASE-01", "W-BASE-02")
    # Base layer excluded from cumulative_core_count
    assert s1_1.cumulative_core_count == 0
    assert "W-BASE-01" in s1_1.all_allowed_ids
    assert "W-BASE-02" in s1_1.all_allowed_ids


def test_name_ids_present_and_excluded_from_cumulative_core_count(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # In lesson 1, names from lesson 1 (W-NAME-01, W-NAME-02) are admitted
    s1_1 = planned_state("a1", 1, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-NAME-01" in s1_1.name_ids
    assert "W-NAME-02" in s1_1.name_ids
    assert "W-NAME-03" not in s1_1.name_ids
    assert s1_1.cumulative_core_count == 0

    # In lesson 2, names from lessons 1 and 2 are admitted
    s1_2 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert "W-NAME-01" in s1_2.name_ids
    assert "W-NAME-02" in s1_2.name_ids
    assert "W-NAME-03" in s1_2.name_ids
    # Names excluded from cumulative count: count is 1 (W-CORE-01 only)
    assert s1_2.cumulative_core_count == 1


def test_missing_earlier_plan_fails_closed_with_positions_listed(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # Delete position 1 plan
    (plans_dir / "module-one.yaml").unlink()

    # Querying position 2 fails closed, listing missing position 1
    with pytest.raises(PlannedStateError) as exc_info:
        planned_state("a1", 2, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert exc_info.value.code == codes.PRIOR_PLANS_MISSING
    assert "[1]" in exc_info.value.message


def test_missing_earlier_plan_waiver_with_allow_missing_prior(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)
    (plans_dir / "module-one.yaml").unlink()

    # With allow_missing_prior=True, succeeds with waiver recorded
    state = planned_state(
        "a1",
        2,
        1,
        allow_missing_prior=True,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
    )
    assert state.waiver is not None
    assert f"waived: {codes.PRIOR_PLANS_MISSING}" in state.waiver


def test_strict_refuses_waiver_even_with_allow_missing_prior(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)
    (plans_dir / "module-one.yaml").unlink()

    # --strict refuses the waiver even when both flags are given
    with pytest.raises(PlannedStateError) as exc_info:
        planned_state(
            "a1",
            2,
            1,
            allow_missing_prior=True,
            strict=True,
            plans_dir=plans_dir,
            evidence_dir=evidence_dir,
        )
    assert exc_info.value.code == codes.PRIOR_PLANS_MISSING
    assert "--strict refuses waiver" in exc_info.value.message


def test_missing_base_layer_fails(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)
    (evidence_dir / "_base.request.yaml").unlink()

    with pytest.raises(PlannedStateError) as exc_info:
        planned_state("a1", 1, 1, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert exc_info.value.code == codes.BASE_LAYER_MISSING


def test_bare_lemma_in_plan_fails(tmp_path: Path) -> None:
    """Rule 1: bare lemma in planned state is a failure (bare_lemma)."""
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    # Edit plan 1 lesson 1 to have a bare lemma instead of an id
    p1_file = plans_dir / "module-one.yaml"
    data = yaml.safe_load(p1_file.read_text(encoding="utf-8"))
    data["lessons"][0]["inventory"]["vocabulary"]["core"][0]["evidence"] = "bare_lemma_word"
    _write_yaml(p1_file, data)

    # In lesson 2, accumulating lesson 1 core vocab fails with bare_lemma
    with pytest.raises(PlannedStateError) as exc_info:
        planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    assert exc_info.value.code == codes.BARE_LEMMA


def test_determinism_byte_identical_output(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_synthetic_curriculum(tmp_path)

    s1 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)
    s2 = planned_state("a1", 1, 2, plans_dir=plans_dir, evidence_dir=evidence_dir)

    json1 = json.dumps(s1.to_dict(), sort_keys=True)
    json2 = json.dumps(s2.to_dict(), sort_keys=True)
    assert json1 == json2
    assert s1.render_text() == s2.render_text()
