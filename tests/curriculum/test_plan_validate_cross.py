"""Tests for the cross-plan rules of plan-validate (issue #8412, Brief B).

Rule 4 (used means introduced earlier), rule 5 (the plan matches the arc),
the grammar registry and its --strict append-only check over git history, the
generated scope sidecar, the module title check, waivers, and whole-level
mode. Fixtures are multi-plan worlds written into a tmp curriculum tree; the
git tests build a temporary repository in tmp_path. Real arc letter lists
(position 1; the 33-letter union of positions 1–3) come through load_arc,
never typed.
"""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.arc.loader import load_arc
from scripts.curriculum.validate import codes
from scripts.curriculum.validate.scope import compute_scope, letter_runs, write_scope_sidecar
from scripts.curriculum.validate.validate import Report, validate_plan
from scripts.curriculum.validate.validate import main as validate_main

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
LEVEL = "a1"
SLUG = "mod-one"
ARC_DOC_REL = "docs/epics/fresh-build-a1-arc.md"

ALWAYS_NOT_CHECKED = {
    codes.MINUTES_CONSTANTS_UNDEFINED,
    codes.WORD_TARGET_NOT_CALIBRATED,
    codes.LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED,
    codes.ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY,
    codes.TITLE_QUANTITIES_NOT_PARSED,
}

GIT_TIMEOUT = 30
GIT_IDENTITY = ["-c", "user.name=fixture", "-c", "user.email=fixture@example.com", "-c", "commit.gpgsign=false"]


@functools.cache
def real_position_letters(position: int) -> list[str]:
    """The real A1 arc's letter list for a literacy position — through load_arc, never typed."""
    arc = load_arc(LEVEL)
    record = next(entry for entry in arc if entry.position == position)
    assert record.letters is not None
    return list(record.letters)


def _dump(data: object) -> bytes:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")


def point_of(grammar_id: str) -> str:
    return f"Point of {grammar_id}."


def grammar_entry(grammar_id: str) -> dict:
    return {"id": grammar_id, "point": point_of(grammar_id), "evidence": ["T-001"]}


def registry_record(grammar_id: str, position: int, lesson: str, superseded_by: str | None = None) -> dict:
    record = {
        "id": grammar_id,
        "point": point_of(grammar_id),
        "introduced_at": {"position": position, "lesson": lesson},
    }
    if superseded_by is not None:
        record["superseded_by"] = superseded_by
    return record


def core_entry(word_id: str) -> dict:
    return {"lemma": f"lemma-{word_id[2:]}", "evidence": word_id, "forms": ["tag-a"]}


def teach_lesson(
    n: int,
    slug: str | None = None,
    *,
    letters: list[str] | tuple = (),
    grammar: list[str] | tuple = (),
    core: list[str] | tuple = (),
    incidental: list[str] | tuple = (),
    recycled: list[str] | tuple = (),
    uses_grammar: list[str] | tuple = (),
    uses_vocab: list[str] | tuple = (),
    closes: bool = False,
    title: str | None = None,
) -> dict:
    slug = slug or f"lesson-{n}"
    steps = [
        {
            "id": "s1",
            "kind": "teach",
            "teach": "The teach step.",
            "introduces": {"letters": list(letters), "grammar": list(grammar), "vocabulary": list(core)},
            "uses": {"grammar": [], "vocabulary": []},
            "evidence": ["T-001"],
            "practice": ["a1"],
        }
    ]
    activities = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Checks the step."}]
    if uses_grammar or uses_vocab:
        steps.append(
            {
                "id": "s2",
                "kind": "practice",
                "uses": {"grammar": list(uses_grammar), "vocabulary": list(uses_vocab)},
                "evidence": ["T-002"],
                "practice": ["a2"],
            }
        )
        activities.append({"id": "a2", "type": "quiz", "placement": "inline", "focus": "Practices the use."})
    lesson = {
        "n": n,
        "slug": slug,
        "title": title or f"Lesson {n}",
        "kind": "teach",
        "job": f"Learner can do thing {n}.",
        "rationale": "Why here.",
        "word_target": 10,
        "inventory": {
            **({"phonetics": {"letters": list(letters), "sounds": []}} if letters else {}),
            "grammar": [grammar_entry(item) for item in grammar],
            "vocabulary": {
                "core": [core_entry(item) for item in core],
                "incidental": [{"lemma": f"lemma-{item[2:]}", "evidence": item} for item in incidental],
                "recycled": list(recycled),
            },
        },
        "steps": steps,
        "activities": activities,
    }
    if closes:
        lesson["closes_with_recap"] = True
        lesson["steps"].append({"id": "s9", "kind": "recap", "evidence": ["T-003"], "practice": []})
    return lesson


def recap_lesson(n: int) -> dict:
    return {
        "n": n,
        "slug": f"lesson-{n}",
        "title": f"Lesson {n}",
        "kind": "recap",
        "job": "Review the module.",
        "rationale": "Closes the module.",
        "word_target": 5,
        "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
        "steps": [{"id": "s1", "kind": "practice", "evidence": ["T-001"], "practice": ["a1"]}],
        "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Review quiz."}],
    }


def make_plan(
    slug: str,
    position: int,
    lessons: list[dict],
    *,
    title: str = "Module title",
    subtitle: str | None = None,
) -> dict:
    plan = {
        "plan_schema": 2,
        "module": slug,
        "level": LEVEL,
        "sequence": position,
        "slug": slug,
        "version": "1",
        "title": title,
        "arc_ref": {"level": LEVEL, "position": position},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{LEVEL}/{slug}.yaml", "sha256": "0" * 64},
        "lessons": lessons,
    }
    if subtitle is not None:
        plan["subtitle"] = subtitle
    return plan


def target_plan(
    slug: str = SLUG,
    position: int = 1,
    *,
    title: str = "Module title",
    subtitle: str | None = None,
    **lesson_kwargs,
) -> dict:
    """A one-teach-lesson plan plus a recap lesson (closing shape a)."""
    return make_plan(
        slug,
        position,
        [teach_lesson(1, "lesson-one", **lesson_kwargs), recap_lesson(2)],
        title=title,
        subtitle=subtitle,
    )


def arc_position(position: int, slug: str, letters: list[str] | None = None) -> dict:
    record = {
        "position": position,
        "slug": slug,
        "est_lessons": 3,
        "job": f"Job of {slug}.",
        "inventory_text": None,
        "phase": "A1.1",
        "skills_text": "W",
        "skills": ["W"],
        "standard_line_refs": [],
    }
    if letters is not None:
        record["letters"] = letters
    return record


def default_arc(target_slug: str = SLUG, target_position: int = 1) -> list[dict]:
    """An arc whose every position matches the default (letter-free) fixture plans."""
    return [arc_position(target_position, target_slug)]


def base_pack(slug: str) -> dict:
    return {
        "evidence_schema": 1,
        "module": f"{LEVEL}/{slug}",
        "texts": [{"id": "T-001"}, {"id": "T-002"}, {"id": "T-003"}],
        "exercises": [{"id": "X-001"}],
        "examples": [{"id": "EX-001"}],
        "errors": [{"id": "E-001"}],
        "videos": [{"id": "V-001"}],
        "standard": [{"id": "S-001"}],
    }


def base_words() -> dict:
    return {
        "words": [
            {"id": f"W-{number:03d}", "lemma": f"lemma-{number:03d}", "forms": [{"tags": "tag-a"}, {"tags": "tag-b"}]}
            for number in range(1, 41)
        ]
    }


def write_level(
    root: Path,
    *,
    plans: list[dict],
    arc: list[dict] | None,
    registry: list[dict] | str | None = None,
    scopes: bool = True,
    extra_files: dict[str, str] | None = None,
) -> dict[str, Path]:
    """Write a multi-plan level world; returns slug -> plan path."""
    base = root / "curriculum/l2-uk-en"
    plan_dir = base / "lesson-plans" / LEVEL
    evidence_dir = base / "evidence" / LEVEL
    plan_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)

    words_bytes = _dump(base_words())
    words_path = evidence_dir / "_words.yaml"
    words_path.write_bytes(words_bytes)
    Path(f"{words_path}.lock").write_text(f"{hashlib.sha256(words_bytes).hexdigest()}\n", encoding="ascii")

    paths: dict[str, Path] = {}
    for raw_plan in plans:
        plan = copy.deepcopy(raw_plan)
        pack_bytes = _dump(base_pack(plan["slug"]))
        pack_path = evidence_dir / f"{plan['slug']}.yaml"
        pack_path.write_bytes(pack_bytes)
        pack_digest = hashlib.sha256(pack_bytes).hexdigest()
        Path(f"{pack_path}.lock").write_text(f"{pack_digest}\n", encoding="ascii")
        plan["evidence_ref"]["sha256"] = pack_digest
        plan_path = plan_dir / f"{plan['slug']}.yaml"
        plan_path.write_bytes(_dump(plan))
        paths[plan["slug"]] = plan_path
        if scopes:
            write_scope_sidecar(plan_path, plan["slug"], compute_scope(plan, LEVEL, plan["slug"]))

    if arc is not None:
        doc_path = root / ARC_DOC_REL
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_bytes(b"# fixture arc document\n")
        arc_document = {
            "arc_schema": 1,
            "level": LEVEL,
            "source": {"path": ARC_DOC_REL, "sha256": hashlib.sha256(doc_path.read_bytes()).hexdigest()},
            "est_lessons_total": 3 * len(arc),
            "positions": arc,
        }
        (plan_dir / "_arc.yaml").write_bytes(_dump(arc_document))
    if isinstance(registry, str):
        (plan_dir / "_grammar.yaml").write_text(registry, encoding="utf-8")
    elif registry is not None:
        (plan_dir / "_grammar.yaml").write_bytes(_dump(registry))
    for name, text in (extra_files or {}).items():
        (plan_dir / name).write_text(text, encoding="utf-8")
    return paths


# --- case table -------------------------------------------------------------


@dataclass(frozen=True)
class CrossCase:
    name: str
    plans: list[dict]
    arc: list[dict] | None
    registry: list[dict] | str | None = None
    target: str = SLUG
    kwargs: dict = field(default_factory=dict)
    extra_files: dict[str, str] = field(default_factory=dict)
    scopes: bool = True
    expected: frozenset[str] = frozenset()
    waived: frozenset[str] = frozenset()
    notes: frozenset[str] = frozenset()


def _letters(start: int, stop: int) -> list[str]:
    return real_position_letters(1)[start:stop]


def _letters_union() -> list[str]:
    """The 33 letters of real arc positions 1–3, through load_arc, never typed."""
    union: list[str] = []
    for position in (1, 2, 3):
        for letter in real_position_letters(position):
            if letter not in union:
                union.append(letter)
    return union


RULE4_CASES = [
    CrossCase(
        "rule4_recycled_introduced_in_earlier_lesson",
        plans=[
            make_plan(
                SLUG,
                1,
                [
                    teach_lesson(1, "lesson-one", core=["W-012"]),
                    teach_lesson(2, "lesson-two", core=["W-013"], recycled=["W-012"], uses_vocab=["W-012"]),
                    recap_lesson(3),
                ],
            )
        ],
        arc=default_arc(),
    ),
    CrossCase(
        "rule4_recycled_introduced_in_earlier_position",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson", core=["W-012"]), recap_lesson(2)]),
            make_plan(
                SLUG,
                2,
                [
                    teach_lesson(1, "lesson-one", core=["W-013"], recycled=["W-012"], uses_vocab=["W-012"]),
                    recap_lesson(2),
                ],
            ),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
    ),
    CrossCase(
        "rule4_only_incidental_earlier_fails",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson", incidental=["W-010"]), recap_lesson(2)]),
            make_plan(
                SLUG, 2, [teach_lesson(1, "lesson-one", recycled=["W-010"], uses_vocab=["W-010"]), recap_lesson(2)]
            ),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
        expected=frozenset({codes.USED_NOT_INTRODUCED_EARLIER}),
    ),
    CrossCase(
        "rule4_introduced_only_in_later_position_fails",
        plans=[
            make_plan(
                SLUG, 1, [teach_lesson(1, "lesson-one", recycled=["W-011"], uses_vocab=["W-011"]), recap_lesson(2)]
            ),
            make_plan("mod-later", 2, [teach_lesson(1, "later-lesson", core=["W-011"]), recap_lesson(2)]),
        ],
        arc=[arc_position(1, SLUG), arc_position(2, "mod-later")],
        expected=frozenset({codes.USED_NOT_INTRODUCED_EARLIER}),
    ),
    CrossCase(
        "rule4_earlier_position_missing_fails",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson"), recap_lesson(2)]),
            target_plan(position=3),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, "mod-two"), arc_position(3, SLUG)],
        expected=frozenset({codes.PRIOR_PLANS_MISSING}),
    ),
    CrossCase(
        "rule4_missing_prior_waived",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson"), recap_lesson(2)]),
            target_plan(position=3),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, "mod-two"), arc_position(3, SLUG)],
        kwargs={"allow_missing_prior": True},
        waived=frozenset({codes.WAIVER_PRIOR_PLANS_MISSING}),
    ),
    CrossCase(
        "rule4_waived_id_unverifiable_is_not_checked",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson"), recap_lesson(2)]),
            target_plan(position=3, recycled=["W-009"], uses_vocab=["W-009"]),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, "mod-two"), arc_position(3, SLUG)],
        kwargs={"allow_missing_prior": True},
        waived=frozenset({codes.WAIVER_PRIOR_PLANS_MISSING}),
    ),
    CrossCase(
        "rule4_two_plans_claim_one_position",
        plans=[
            target_plan(),
            make_plan("mod-dup", 1, [teach_lesson(1, "dup-lesson"), recap_lesson(2)]),
        ],
        arc=default_arc(),
        expected=frozenset({codes.POSITION_CLAIMED_TWICE}),
    ),
    CrossCase(
        "rule4_prior_plan_unreadable",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson"), recap_lesson(2)]),
            target_plan(position=2),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
        extra_files={"broken.yaml": "x: [unclosed"},
        expected=frozenset({codes.PRIOR_PLAN_UNREADABLE}),
    ),
]

ARC_CASES = [
    CrossCase(
        "rule5_arc_file_missing",
        plans=[target_plan()],
        arc=None,
        expected=frozenset({codes.ARC_UNAVAILABLE}),
    ),
    CrossCase(
        "rule5_wrong_position",
        plans=[target_plan()],
        arc=[arc_position(2, SLUG)],
        expected=frozenset({codes.ARC_REF_UNKNOWN}),
    ),
    CrossCase(
        "rule5_slug_differs_from_arc",
        plans=[target_plan()],
        arc=[arc_position(1, "mod-other")],
        expected=frozenset({codes.ARC_SLUG_MISMATCH}),
    ),
    CrossCase(
        "rule5_missing_and_extra_letters",
        plans=[target_plan(letters=_letters(0, 1) + _letters(5, 6))],
        arc=[arc_position(1, SLUG, _letters(0, 3))],
        expected=frozenset({codes.ARC_LETTERS_MISMATCH}),
    ),
    CrossCase(
        "rule5_letter_introduced_by_two_lessons",
        plans=[
            make_plan(
                SLUG,
                1,
                [
                    teach_lesson(1, "lesson-one", letters=_letters(0, 1)),
                    teach_lesson(2, "lesson-two", letters=_letters(0, 1)),
                    recap_lesson(3),
                ],
            )
        ],
        arc=[arc_position(1, SLUG, _letters(0, 1))],
        expected=frozenset({codes.LETTER_INTRODUCED_TWICE}),
    ),
    CrossCase(
        "rule5_letters_in_non_literacy_position",
        plans=[target_plan(letters=_letters(0, 1))],
        arc=[arc_position(1, SLUG)],
        expected=frozenset({codes.LETTERS_IN_NON_LITERACY_PLAN}),
    ),
]

REGISTRY_CASES = [
    CrossCase(
        "registry_duplicate_id",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=[
            registry_record("G-a1-001", 1, "lesson-one"),
            registry_record("G-a1-001", 1, "lesson-one"),
        ],
        expected=frozenset({codes.REGISTRY_DUPLICATE_ID}),
    ),
    CrossCase(
        "registry_id_at_wrong_position_or_lesson",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=[registry_record("G-a1-001", 3, "lesson-x")],
        expected=frozenset({codes.GRAMMAR_ID_WRONG_POSITION}),
    ),
    CrossCase(
        "registry_point_string_differs",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=[
            {"id": "G-a1-001", "point": "Edited point.", "introduced_at": {"position": 1, "lesson": "lesson-one"}}
        ],
        expected=frozenset({codes.GRAMMAR_POINT_MISMATCH}),
    ),
    CrossCase(
        "registry_superseded_id_introduced",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=[
            registry_record("G-a1-001", 1, "lesson-one", superseded_by="G-a1-002"),
            registry_record("G-a1-002", 2, "lesson-two"),
        ],
        expected=frozenset({codes.SUPERSEDED_GRAMMAR_INTRODUCED}),
    ),
    CrossCase(
        "registry_superseded_id_used",
        plans=[
            make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson", grammar=["G-a1-001"]), recap_lesson(2)]),
            make_plan(
                SLUG,
                2,
                [teach_lesson(1, "lesson-one", grammar=["G-a1-002"], uses_grammar=["G-a1-001"]), recap_lesson(2)],
            ),
        ],
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
        registry=[
            registry_record("G-a1-001", 1, "prior-lesson", superseded_by="G-a1-002"),
            registry_record("G-a1-002", 2, "lesson-one"),
        ],
        expected=frozenset({codes.SUPERSEDED_GRAMMAR_USED}),
    ),
    CrossCase(
        "registry_superseded_by_dangling",
        plans=[target_plan()],
        arc=default_arc(),
        registry=[
            registry_record("G-a1-001", 1, "lesson-one", superseded_by="G-a1-999"),
        ],
        expected=frozenset({codes.SUPERSEDED_BY_UNKNOWN}),
    ),
    CrossCase(
        "registry_superseded_by_superseded",
        plans=[target_plan()],
        arc=default_arc(),
        registry=[
            registry_record("G-a1-001", 1, "lesson-one", superseded_by="G-a1-002"),
            registry_record("G-a1-002", 2, "lesson-two", superseded_by="G-a1-003"),
            registry_record("G-a1-003", 3, "lesson-three"),
        ],
        expected=frozenset({codes.SUPERSEDED_BY_SUPERSEDED}),
    ),
    CrossCase(
        "registry_missing_while_plan_introduces_grammar",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=None,
        expected=frozenset({codes.REGISTRY_MISSING}),
    ),
    CrossCase(
        "registry_id_not_registered",
        plans=[target_plan(grammar=["G-a1-001"])],
        arc=default_arc(),
        registry=[registry_record("G-a1-007", 1, "lesson-one")],
        expected=frozenset({codes.GRAMMAR_ID_NOT_REGISTERED}),
    ),
    CrossCase(
        "registry_id_malformed",
        plans=[target_plan()],
        arc=default_arc(),
        registry=[registry_record("G-a1-1", 1, "lesson-one")],
        expected=frozenset({codes.REGISTRY_ID_MALFORMED}),
    ),
    CrossCase(
        "registry_record_malformed",
        plans=[target_plan()],
        arc=default_arc(),
        registry="[1, 2]\n",
        expected=frozenset({codes.REGISTRY_MALFORMED}),
    ),
    CrossCase(
        "registry_yaml_invalid",
        plans=[target_plan()],
        arc=default_arc(),
        registry="x: [unclosed",
        expected=frozenset({codes.REGISTRY_YAML_INVALID}),
    ),
]

SCOPE_CASES = [
    CrossCase(
        "scope_sidecar_missing",
        plans=[target_plan()],
        arc=default_arc(),
        scopes=False,
        expected=frozenset({codes.SCOPE_SIDECAR_MISSING}),
    ),
]

TITLE_CASES = [
    CrossCase(
        "title_seven_enumerated_over_33_taught",
        plans=[
            make_plan(
                SLUG,
                1,
                [
                    teach_lesson(1, "lesson-one", letters=_letters(0, 13)),
                    teach_lesson(2, "lesson-two", letters=_letters_union()[13:25]),
                    teach_lesson(3, "lesson-three", letters=_letters_union()[25:]),
                    recap_lesson(4),
                ],
                subtitle="Літери " + " ".join(_letters(0, 7)),
            )
        ],
        arc=[arc_position(1, SLUG, _letters_union())],
        expected=frozenset({codes.TITLE_LETTER_ENUMERATION_MISMATCH}),
    ),
    CrossCase(
        "title_single_letter_is_not_a_run",
        plans=[target_plan(letters=_letters(0, 2), title=f"The letter {_letters(0, 1)[0]} first")],
        arc=[arc_position(1, SLUG, _letters(0, 2))],
    ),
    CrossCase(
        "title_one_letter_ukrainian_word_is_not_a_run",
        plans=[target_plan(letters=_letters(0, 2), subtitle="Я і ти читаємо разом")],
        arc=[arc_position(1, SLUG, _letters(0, 2))],
    ),
    CrossCase(
        "title_lesson_title_enumerating_subset_is_ignored",
        plans=[
            make_plan(
                SLUG,
                1,
                [
                    teach_lesson(1, "lesson-one", letters=_letters(0, 3), title="Літери " + " ".join(_letters(0, 2))),
                    recap_lesson(2),
                ],
            )
        ],
        arc=[arc_position(1, SLUG, _letters(0, 3))],
    ),
]


ALL_CROSS_CASES = RULE4_CASES + ARC_CASES + REGISTRY_CASES + SCOPE_CASES + TITLE_CASES


def run_cross(root: Path, case: CrossCase) -> Report:
    plans = copy.deepcopy(case.plans)
    paths = write_level(
        root,
        plans=plans,
        arc=copy.deepcopy(case.arc),
        registry=copy.deepcopy(case.registry),
        scopes=case.scopes,
        extra_files=case.extra_files,
    )
    return validate_plan(LEVEL, case.target, plan_path=paths[case.target], **case.kwargs)


@pytest.mark.parametrize("case", ALL_CROSS_CASES, ids=lambda case: case.name)
def test_cross_case(tmp_path: Path, case: CrossCase) -> None:
    report = run_cross(tmp_path, case)
    assert {o.code for o in report.failures} == set(case.expected), report.render_text()
    assert {o.code for o in report.waivers} == set(case.waived), report.render_text()
    assert {o.code for o in report.notes} == set(case.notes), report.render_text()
    expected_not_checked = set(ALWAYS_NOT_CHECKED)
    if case.name == "rule4_waived_id_unverifiable_is_not_checked":
        expected_not_checked.add(codes.INTRODUCED_EARLIER_UNVERIFIED)
    assert {o.code for o in report.not_checked} == expected_not_checked, report.render_text()
    assert report.ok == (not case.expected)
    assert report.status == ("fail" if case.expected else ("waived" if case.waived else "pass"))


# --- message-level assertions -----------------------------------------------


def test_missing_prior_lists_positions(tmp_path: Path) -> None:
    case = next(case for case in RULE4_CASES if case.name == "rule4_earlier_position_missing_fails")
    report = run_cross(tmp_path, case)
    outcome = next(o for o in report.failures if o.code == codes.PRIOR_PLANS_MISSING)
    assert "missing positions: 2" in outcome.message


def test_letters_mismatch_reports_missing_and_extra_separately(tmp_path: Path) -> None:
    case = next(case for case in ARC_CASES if case.name == "rule5_missing_and_extra_letters")
    report = run_cross(tmp_path, case)
    outcomes = [o for o in report.failures if o.code == codes.ARC_LETTERS_MISMATCH]
    assert len(outcomes) == 2, report.render_text()
    missing = next(o for o in outcomes if "missing" in o.message)
    extra = next(o for o in outcomes if "extra" in o.message)
    assert " ".join(_letters(1, 3)) in missing.message
    assert _letters(5, 6)[0] in extra.message


def test_registry_missing_says_how_to_add_the_record(tmp_path: Path) -> None:
    case = next(case for case in REGISTRY_CASES if case.name == "registry_missing_while_plan_introduces_grammar")
    report = run_cross(tmp_path, case)
    outcome = next(o for o in report.failures if o.code == codes.REGISTRY_MISSING)
    assert "introduced_at" in outcome.message
    assert "append" in outcome.message
    assert "G-a1-001" in outcome.message


def test_title_quantities_quotes_digits(tmp_path: Path) -> None:
    case = CrossCase(
        "title_digits_quoted",
        plans=[target_plan(title="Module 1 title", subtitle="About 7 things")],
        arc=default_arc(),
    )
    report = run_cross(tmp_path, case)
    outcome = next(o for o in report.not_checked if o.code == codes.TITLE_QUANTITIES_NOT_PARSED)
    assert "1" in outcome.message and "7" in outcome.message
    assert report.ok


def test_real_position1_letters_through_load_arc(tmp_path: Path) -> None:
    """A plan matching the real position-1 arc (letters via load_arc) passes, and a
    title enumerating exactly the scope letter list passes the title check."""
    letters = real_position_letters(1)
    slug = "sounds-letters-and-hello"
    paths = write_level(
        tmp_path,
        plans=[
            make_plan(
                slug,
                1,
                [
                    teach_lesson(1, "lesson-one", letters=letters[:7]),
                    teach_lesson(2, "lesson-two", letters=letters[7:]),
                    recap_lesson(3),
                ],
                title="Звуки і літери: " + ", ".join(letters),
            )
        ],
        arc=None,
    )
    # the real generated arc and its real source document, copied byte for byte
    plan_dir = paths[slug].parent
    real_arc = REPO_ROOT / "curriculum/l2-uk-en/lesson-plans/a1/_arc.yaml"
    real_doc = REPO_ROOT / "docs/epics/fresh-build-a1-arc.md"
    plan_dir.joinpath("_arc.yaml").write_bytes(real_arc.read_bytes())
    doc_path = tmp_path / ARC_DOC_REL
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_bytes(real_doc.read_bytes())
    report = validate_plan(LEVEL, slug, plan_path=paths[slug])
    assert report.ok, report.render_text()
    assert not any(o.code == codes.TITLE_LETTER_ENUMERATION_MISMATCH for o in report.failures)
    assert any(o.code == codes.ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY for o in report.not_checked)


def test_title_seven_over_33_message(tmp_path: Path) -> None:
    case = next(case for case in TITLE_CASES if case.name == "title_seven_enumerated_over_33_taught")
    report = run_cross(tmp_path, case)
    outcome = next(o for o in report.failures if o.code == codes.TITLE_LETTER_ENUMERATION_MISMATCH)
    assert "missing:" in outcome.message
    assert " ".join(_letters(0, 7)) in outcome.message


def test_letter_runs_boundaries() -> None:
    """The definition of 'a run of enumerated single letters' at its edges."""
    letters = real_position_letters(1)
    a, o, u = letters[0], letters[1], letters[2]
    assert letter_runs(f"{a}") == []  # one letter alone is not a run
    assert letter_runs(f"{a} {o}") == [[a, o]]
    assert letter_runs(f"{a}, {o}, {u}") == [[a, o, u]]
    assert letter_runs(f"{a},{o}; {u}") == [[a, o, u]]
    assert letter_runs("Я і ти читаємо") == []  # a one-letter word in a sentence is not an enumeration
    assert letter_runs(f"{a}{o} {u}") == []  # a two-letter word is not two letters
    assert letter_runs("About 7 things") == []


# --- scope sidecar behavior ---------------------------------------------------


def _write_scope_twice_and_validate(root: Path) -> tuple[Report, Path]:
    plan = target_plan(grammar=["G-a1-001"], core=["W-012"], letters=_letters(0, 2))
    paths = write_level(
        root,
        plans=[plan],
        arc=[arc_position(1, SLUG, _letters(0, 2))],
        registry=[registry_record("G-a1-001", 1, "lesson-one")],
        scopes=False,
    )
    plan_path = paths[SLUG]
    first = validate_plan(LEVEL, SLUG, plan_path=plan_path, write_scope=True)
    assert first.ok, first.render_text()
    sidecar = plan_path.parent / "_scope" / f"{SLUG}.yaml"
    first_bytes = sidecar.read_bytes()
    second = validate_plan(LEVEL, SLUG, plan_path=plan_path, write_scope=True)
    assert sidecar.read_bytes() == first_bytes  # byte-stable across two writes
    assert second.ok, second.render_text()
    report = validate_plan(LEVEL, SLUG, plan_path=plan_path)
    return report, sidecar


def test_write_scope_then_validate_passes_and_file_mode(tmp_path: Path) -> None:
    report, sidecar = _write_scope_twice_and_validate(tmp_path)
    assert report.ok, report.render_text()
    assert stat.S_IMODE(sidecar.stat().st_mode) == 0o600  # no group-write, no world bits
    assert stat.S_IMODE(sidecar.parent.stat().st_mode) == 0o700
    assert sidecar.read_bytes().endswith(b"\n")  # trailing newline


def test_stale_scope_fails_with_diff(tmp_path: Path) -> None:
    _report, sidecar = _write_scope_twice_and_validate(tmp_path)
    sidecar.write_bytes(sidecar.read_bytes() + b"count: 99\n")
    plan_path = sidecar.parent.parent / f"{SLUG}.yaml"
    report = validate_plan(LEVEL, SLUG, plan_path=plan_path)
    outcome = next(o for o in report.failures if o.code == codes.SCOPE_SIDECAR_STALE)
    assert "Diff:" in outcome.message
    assert "-count: 99" in outcome.message  # the committed sidecar carries the stale line


# --- waivers and the CLI ------------------------------------------------------


def _waived_world(root: Path) -> Path:
    plans = [
        make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson"), recap_lesson(2)]),
        target_plan(position=3),
    ]
    paths = write_level(
        root,
        plans=plans,
        arc=[arc_position(1, "mod-zero"), arc_position(2, "mod-two"), arc_position(3, SLUG)],
    )
    return paths[SLUG]


def test_cli_waived_run_is_not_clean_and_has_distinct_exit_code(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    plan_path = _waived_world(tmp_path)
    assert validate_main([LEVEL, SLUG, "--plan", str(plan_path), "--allow-missing-prior"]) == 3
    out = capsys.readouterr().out
    assert "status: waived" in out
    assert "waived: prior_plans_missing (missing positions: 2)" in out
    assert validate_main([LEVEL, SLUG, "--plan", str(plan_path), "--allow-missing-prior", "--json"]) == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "waived"
    assert payload["waivers"][0]["code"] == codes.WAIVER_PRIOR_PLANS_MISSING
    assert "missing positions: 2" in payload["waivers"][0]["message"]


def test_cli_strict_refuses_waiver_flag(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    plan_path = _waived_world(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        validate_main([LEVEL, SLUG, "--plan", str(plan_path), "--strict", "--allow-missing-prior"])
    assert excinfo.value.code == 2
    assert "refuses every waiver flag" in capsys.readouterr().err


# --- --strict append-only over a temporary git repository ----------------------


@dataclass(frozen=True)
class GitScenario:
    name: str
    baseline: list[dict] | None
    final: list[dict]
    origin: str = "base"  # base | head | orphan
    expected: frozenset[str] = frozenset()


def _r1() -> dict:
    return registry_record("G-a1-001", 1, "prior-lesson")


def _r2() -> dict:
    return registry_record("G-a1-002", 2, "lesson-one")


GIT_SCENARIOS = [
    GitScenario("strict_new_record_appended_passes", baseline=[_r1()], final=[_r1(), _r2()]),
    GitScenario(
        "strict_record_removed_fails",
        baseline=[_r1(), _r2(), registry_record("G-a1-003", 3, "other-lesson")],
        final=[_r1(), _r2()],
        expected=frozenset({codes.REGISTRY_APPEND_ONLY_VIOLATION}),
    ),
    GitScenario(
        "strict_record_reordered_fails",
        baseline=[_r1(), _r2()],
        final=[_r2(), _r1()],
        expected=frozenset({codes.REGISTRY_APPEND_ONLY_VIOLATION}),
    ),
    GitScenario(
        "strict_point_edited_fails",
        baseline=[_r1(), _r2()],
        final=[
            {"id": "G-a1-001", "point": "Edited point.", "introduced_at": {"position": 1, "lesson": "prior-lesson"}},
            _r2(),
        ],
        expected=frozenset({codes.REGISTRY_APPEND_ONLY_VIOLATION}),
    ),
    GitScenario(
        "strict_introduced_at_edited_fails",
        baseline=[_r1(), _r2()],
        final=[registry_record("G-a1-001", 5, "prior-lesson"), _r2()],
        expected=frozenset({codes.REGISTRY_APPEND_ONLY_VIOLATION}),
    ),
    GitScenario(
        "strict_record_inserted_in_middle_fails",
        baseline=[_r1(), _r2()],
        final=[_r1(), registry_record("G-a1-003", 3, "other-lesson"), _r2()],
        expected=frozenset({codes.REGISTRY_APPEND_ONLY_VIOLATION}),
    ),
    GitScenario(
        "strict_only_superseded_by_added_passes",
        baseline=[_r1(), _r2()],
        final=[registry_record("G-a1-001", 1, "prior-lesson", superseded_by="G-a1-002"), _r2()],
    ),
    GitScenario("strict_registry_absent_at_merge_base_passes", baseline=None, final=[_r1(), _r2()]),
    GitScenario("strict_on_main_passes", baseline=[_r1(), _r2()], final=[_r1(), _r2()], origin="head"),
    GitScenario(
        "strict_no_merge_base_fails",
        baseline=[_r1(), _r2()],
        final=[_r1(), _r2()],
        origin="orphan",
        expected=frozenset({codes.MERGE_BASE_UNAVAILABLE}),
    ),
]


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *GIT_IDENTITY, *args],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
    )


def run_git_scenario(root: Path, scenario: GitScenario) -> Report:
    plans = [
        make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson", grammar=["G-a1-001"]), recap_lesson(2)]),
        make_plan(SLUG, 2, [teach_lesson(1, "lesson-one", grammar=["G-a1-002"]), recap_lesson(2)]),
    ]
    paths = write_level(
        root,
        plans=plans,
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
        registry=scenario.baseline,
    )
    assert _git(root, "init", "-q", "-b", "main").returncode == 0
    assert _git(root, "add", "-A").returncode == 0
    assert _git(root, "commit", "-q", "-m", "baseline").returncode == 0
    assert _git(root, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0

    registry_path = paths[SLUG].parent / "_grammar.yaml"
    registry_path.write_bytes(_dump(scenario.final))
    assert _git(root, "add", "-A").returncode == 0
    assert _git(root, "commit", "-q", "--allow-empty", "-m", "registry change").returncode == 0

    if scenario.origin == "head":
        assert _git(root, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
    elif scenario.origin == "orphan":
        assert _git(root, "checkout", "-q", "--orphan", "unrelated").returncode == 0
        assert _git(root, "rm", "-q", "-rf", ".").returncode == 0
        assert _git(root, "commit", "-q", "--allow-empty", "-m", "unrelated root").returncode == 0
        assert _git(root, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
        assert _git(root, "checkout", "-q", "main").returncode == 0

    return validate_plan(LEVEL, SLUG, plan_path=paths[SLUG], strict=True)


@pytest.mark.parametrize("scenario", GIT_SCENARIOS, ids=lambda scenario: scenario.name)
def test_git_scenario(tmp_path: Path, scenario: GitScenario) -> None:
    report = run_git_scenario(tmp_path, scenario)
    assert {o.code for o in report.failures} == set(scenario.expected), report.render_text()


def test_no_merge_base_says_fetch_full_history(tmp_path: Path) -> None:
    scenario = next(scenario for scenario in GIT_SCENARIOS if scenario.name == "strict_no_merge_base_fails")
    report = run_git_scenario(tmp_path, scenario)
    outcome = next(o for o in report.failures if o.code == codes.MERGE_BASE_UNAVAILABLE)
    assert "fetch full history" in outcome.message


# --- whole-level mode ----------------------------------------------------------


def _three_plan_level(root: Path) -> Path:
    plans = [
        make_plan(
            "mod-b",
            2,
            [teach_lesson(1, "lesson-b", core=["W-014"], recycled=["W-012"], uses_vocab=["W-012"]), recap_lesson(2)],
        ),
        make_plan("mod-a", 1, [teach_lesson(1, "lesson-a", core=["W-012"]), recap_lesson(2)]),
        make_plan(
            "mod-c",
            3,
            [teach_lesson(1, "lesson-c", core=["W-015"], recycled=["W-014"], uses_vocab=["W-014"]), recap_lesson(2)],
        ),
    ]
    write_level(
        root,
        plans=plans,
        arc=[arc_position(1, "mod-a"), arc_position(2, "mod-b"), arc_position(3, "mod-c")],
    )
    return root / "curriculum/l2-uk-en/lesson-plans" / LEVEL


def test_all_prints_one_summary_line_per_plan_in_position_order(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    level_dir = _three_plan_level(tmp_path)
    assert validate_main([LEVEL, "--all", "--level-dir", str(level_dir)]) == 0
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.startswith(f"{LEVEL}/mod-")]
    assert lines == [f"{LEVEL}/mod-a: pass", f"{LEVEL}/mod-b: pass", f"{LEVEL}/mod-c: pass"]


def test_all_subprocess_clean_environment_strict(tmp_path: Path) -> None:
    """The CLI runs --all --strict from the repository root under env -i (only PATH and HOME)."""
    plans = [
        make_plan("mod-zero", 1, [teach_lesson(1, "prior-lesson", grammar=["G-a1-001"]), recap_lesson(2)]),
        make_plan(SLUG, 2, [teach_lesson(1, "lesson-one", grammar=["G-a1-002"]), recap_lesson(2)]),
    ]
    write_level(
        tmp_path,
        plans=plans,
        arc=[arc_position(1, "mod-zero"), arc_position(2, SLUG)],
        registry=[_r1(), _r2()],
    )
    assert _git(tmp_path, "init", "-q", "-b", "main").returncode == 0
    assert _git(tmp_path, "add", "-A").returncode == 0
    assert _git(tmp_path, "commit", "-q", "-m", "baseline").returncode == 0
    assert _git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
    level_dir = tmp_path / "curriculum/l2-uk-en/lesson-plans" / LEVEL
    env = [f"PATH={os.environ['PATH']}", f"HOME={os.environ.get('HOME', str(tmp_path))}"]
    completed = subprocess.run(
        [
            "env",
            "-i",
            *env,
            sys.executable,
            "-m",
            "scripts.curriculum.validate",
            LEVEL,
            "--all",
            "--strict",
            "--level-dir",
            str(level_dir),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    assert f"{LEVEL}/mod-zero: pass" in completed.stdout
    assert f"{LEVEL}/{SLUG}: pass" in completed.stdout


# --- registry completeness aggregation (used by test_plan_validate.py) ---------


def produced_cross_codes(root: Path) -> set[str]:
    produced: set[str] = set()
    for index, case in enumerate(ALL_CROSS_CASES):
        produced |= run_cross(root / f"case-{index}", case).codes()
    for index, scenario in enumerate(GIT_SCENARIOS):
        produced |= run_git_scenario(root / f"git-{index}", scenario).codes()
    clean_report, sidecar = _write_scope_twice_and_validate(root / "scope")
    produced |= clean_report.codes()
    sidecar.write_bytes(sidecar.read_bytes() + b"count: 99\n")
    plan_path = sidecar.parent.parent / f"{SLUG}.yaml"
    produced |= validate_plan(LEVEL, SLUG, plan_path=plan_path).codes()  # scope_sidecar_stale
    return produced
