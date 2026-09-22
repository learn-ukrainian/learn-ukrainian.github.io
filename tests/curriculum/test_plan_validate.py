"""Tests for the module plan validator's single-plan rules (issue #8412, Brief A).

Fixtures are built in test code and written into a tmp curriculum tree
(curriculum/l2-uk-en/lesson-plans/<level>/ + evidence/<level>/). No fixture
contains Ukrainian word forms beyond single letters copied from
docs/epics/fresh-build-plan-schema.md §2 (А, О): lemma values are ASCII
placeholders the fixture word store defines, and no fixture carries a stress
mark except the two fixtures that must fail for one. The one Cyrillic token
("мама") is copied from the schema document's §2 example; it fails rule 7 in a
disallowed field and passes as an inventory lemma that matches the word store.

Brief B made the validator the complete §6 gate, so the fixture world also
carries what the cross-plan rules read: a prior position-1 plan (mod-zero,
which introduces W-003 — the word the base fixture recycles), a generated
fixture arc (_arc.yaml + its source document) whose position 2 matches the
fixture plan, a grammar registry derived from the plan's introductions, and
the generated scope sidecar. These are derived from the (mutated) plan so the
Brief A cases stay neutral to the cross-plan rules; fixtures that exercise the
cross-plan rules themselves live in test_plan_validate_cross.py.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes
from scripts.curriculum.validate.scope import compute_scope, write_scope_sidecar
from scripts.curriculum.validate.validate import Report, validate_plan
from scripts.curriculum.validate.validate import main as validate_main

pytestmark = pytest.mark.reads_content

REPO_ROOT = Path(__file__).resolve().parents[2]
LEVEL = "a1"
SLUG = "mod-one"

NOT_CHECKED = {
    codes.MINUTES_CONSTANTS_UNDEFINED,
    codes.WORD_TARGET_NOT_CALIBRATED,
    codes.LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED,
    codes.ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY,
    codes.TITLE_QUANTITIES_NOT_PARSED,
}

LETTER_A = "А"  # copied from docs/epics/fresh-build-plan-schema.md §2
LETTER_O = "О"  # copied from docs/epics/fresh-build-plan-schema.md §2
LEMMA_MAMA = "мама"  # copied from docs/epics/fresh-build-plan-schema.md §2

PRIOR_SLUG = "mod-zero"
ARC_DOC_REL = "docs/epics/fresh-build-a1-arc.md"


def base_plan() -> dict:
    """The valid literacy fixture, also carrying all six revision-9 fields."""
    return {
        "plan_schema": 2,
        "module": SLUG,
        "level": LEVEL,
        "sequence": 1,
        "slug": SLUG,
        "version": "1",
        "title": "Module one title",
        "arc_ref": {"level": LEVEL, "position": 2},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{LEVEL}/{SLUG}.yaml", "sha256": "0" * 64},
        "lessons": [
            {
                "n": 1,
                "slug": "lesson-one",
                "title": "Lesson one",
                "kind": "teach",
                "job": "Learner can do thing one.",
                "rationale": "Why here, why in this order.",
                "word_target": 10,
                "inventory": {
                    "phonetics": {"letters": [LETTER_A, LETTER_O], "sounds": []},
                    "grammar": [{"id": "G-a1-001", "point": "First grammar point.", "evidence": ["T-001"]}],
                    "vocabulary": {
                        "core": [{"lemma": "lemma-one", "evidence": "W-001", "forms": ["tag-a", "tag-b"]}],
                        "incidental": [{"lemma": "lemma-two", "evidence": "W-002"}],
                        "recycled": ["W-003"],
                    },
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "The first letter.",
                        "introduces": {"letters": [LETTER_A], "grammar": [], "vocabulary": []},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["T-001", "EX-001"],
                        "practice": ["a1"],
                        "needs": ["example", "paradigm"],
                        "paradigm": {"id": "P-01", "word": "W-001", "forms": ["tag-a"]},
                    },
                    {
                        "id": "s2",
                        "kind": "teach",
                        "teach": "The second letter and the first point.",
                        "introduces": {"letters": [LETTER_O], "grammar": ["G-a1-001"], "vocabulary": ["W-001"]},
                        "uses": {"grammar": [], "vocabulary": ["W-003"]},
                        "evidence": ["T-002"],
                        "practice": ["a2"],
                    },
                    {
                        "id": "s3",
                        "kind": "practice",
                        "teach": "Dialogue practice.",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": []},
                        "uses": {"grammar": ["G-a1-001"], "vocabulary": ["W-001"]},
                        "evidence": ["T-003"],
                        "practice": ["a3"],
                    },
                ],
                "consolidation": ["a3"],
                "activities": [
                    {"id": "a1", "type": "quiz", "placement": "inline", "focus": "Checks the letters."},
                    {
                        "id": "a2",
                        "type": "error-correction",
                        "placement": "workbook",
                        "focus": "Fix the errors.",
                        "error_refs": ["E-001"],
                    },
                    {"id": "a3", "type": "match-up", "placement": "inline", "focus": "Match pairs.", "model": "X-001"},
                ],
                "videos": [{"evidence": "V-001", "use": "After step two."}],
                "dialogue": {
                    "step": "s3",
                    "situation": "At a table.",
                    "setting": "A room with a table.",
                    "speakers": [
                        {"name": "Name One", "role": "host", "gender": "f", "evidence": "W-004"},
                        {"name": "Name Two", "role": "guest", "gender": "m", "evidence": "W-005"},
                    ],
                    "places": [{"name": "Place One", "evidence": "W-006"}],
                    "register": "informal",
                    "target_grammar": "Shows the first point.",
                    "evidence": ["T-003", "EX-001"],
                },
                "practice": {"vocabulary": "core", "stress": ["W-001"], "patterns": ["a1"]},
            },
            {
                "n": 2,
                "slug": "lesson-two",
                "title": "Lesson two",
                "kind": "recap",
                "job": "Review the module.",
                "rationale": "Closes the module.",
                "word_target": 5,
                "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
                "steps": [{"id": "s1", "kind": "practice", "evidence": ["T-001"], "practice": ["a1"]}],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Review quiz."}],
            },
        ],
    }


def base_pack() -> dict:
    return {
        "evidence_schema": 1,
        "module": f"{LEVEL}/{SLUG}",
        "texts": [{"id": "T-001"}, {"id": "T-002"}, {"id": "T-003"}],
        "exercises": [{"id": "X-001"}],
        "examples": [{"id": "EX-001"}],
        "errors": [{"id": "E-001"}],
        "videos": [{"id": "V-001"}],
        "standard": [{"id": "S-001"}],
    }


def base_words() -> dict:
    def record(number: int, lemma: str, tags: list[str]) -> dict:
        return {"id": f"W-{number:03d}", "lemma": lemma, "forms": [{"tags": tag} for tag in tags]}

    return {
        "words": [
            record(1, "lemma-one", ["tag-a", "tag-b", "tag-c"]),
            record(2, "lemma-two", ["tag-a"]),
            record(3, "lemma-three", ["tag-a"]),
            record(4, "name-one", ["tag-a"]),
            record(5, "name-two", ["tag-a"]),
            record(6, "place-one", ["tag-a"]),
            record(7, "lemma-seven", ["tag-a", "tag-b"]),
            record(8, "lemma-eight", ["tag-a"]),
            record(9, "lemma-nine", ["tag-a"]),
        ]
    }


def prior_plan() -> dict:
    """The position-1 plan: introduces W-003, which the base fixture recycles.

    It is never validated, only mined for its position and introductions
    (rule 4), so it needs no pack of its own.
    """
    return {
        "plan_schema": 2,
        "slug": PRIOR_SLUG,
        "arc_ref": {"level": LEVEL, "position": 1},
        "lessons": [
            {
                "n": 1,
                "slug": "prior-lesson",
                "kind": "teach",
                "inventory": {"vocabulary": {"core": [], "incidental": [], "recycled": []}},
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-003"]},
                    }
                ],
            }
        ],
    }


def fixture_arc(plan: dict) -> dict:
    """A generated-looking arc whose position 2 matches the (mutated) fixture plan.

    Derived from the plan so Brief A fixtures stay neutral to rule 5; fixtures
    that exercise rule 5 itself live in test_plan_validate_cross.py.
    """
    scope = compute_scope(plan, LEVEL, plan["slug"])

    def record(position: int, slug: str, letters: list[str]) -> dict:
        entry = {
            "position": position,
            "slug": slug,
            "est_lessons": 2,
            "job": f"Job of {slug}.",
            "inventory_text": None,
            "phase": "A1.1",
            "skills_text": "W",
            "skills": ["W"],
            "standard_line_refs": [],
        }
        if letters:
            entry["letters"] = letters
        return entry

    return {
        "arc_schema": 1,
        "level": LEVEL,
        "source": {"path": ARC_DOC_REL, "sha256": "0" * 64},  # rebound by write_world
        "est_lessons_total": 4,
        "positions": [
            record(1, PRIOR_SLUG, []),
            record(2, plan["slug"], scope["letters"]["list"]),
        ],
    }


def derived_registry(plan: dict) -> list[dict]:
    """Registry records matching the plan's own grammar introductions (§2a)."""
    records = []
    for lesson in plan["lessons"]:
        if lesson["kind"] != "teach":
            continue
        for entry in lesson["inventory"].get("grammar") or []:
            records.append(
                {
                    "id": entry["id"],
                    "point": entry["point"],
                    "introduced_at": {"position": plan["arc_ref"]["position"], "lesson": lesson["slug"]},
                }
            )
    return records


@dataclass(frozen=True)
class World:
    plan_path: Path
    pack_path: Path
    words_path: Path


def _dump(data: object) -> bytes:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")


def write_world(root: Path, plan: dict, pack: dict, words: dict, slug: str = SLUG) -> World:
    base = root / "curriculum/l2-uk-en"
    plan_dir = base / "lesson-plans" / LEVEL
    evidence_dir = base / "evidence" / LEVEL
    plan_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)

    pack_bytes = _dump(pack)
    pack_path = evidence_dir / f"{slug}.yaml"
    pack_path.write_bytes(pack_bytes)
    pack_digest = hashlib.sha256(pack_bytes).hexdigest()
    Path(f"{pack_path}.lock").write_text(f"{pack_digest}\n", encoding="ascii")

    words_bytes = _dump(words)
    words_path = evidence_dir / "_words.yaml"
    words_path.write_bytes(words_bytes)
    Path(f"{words_path}.lock").write_text(f"{hashlib.sha256(words_bytes).hexdigest()}\n", encoding="ascii")

    plan = copy.deepcopy(plan)
    plan["evidence_ref"]["sha256"] = pack_digest
    plan_path = plan_dir / f"{slug}.yaml"
    plan_path.write_bytes(_dump(plan))

    # The cross-plan fixture files (Brief B): the prior plan, the arc, the
    # grammar registry and the scope sidecar — all derived above.
    (plan_dir / f"{PRIOR_SLUG}.yaml").write_bytes(_dump(prior_plan()))
    doc_path = root / ARC_DOC_REL
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_bytes(f"# fixture arc document for {slug}\n".encode())
    arc = fixture_arc(plan)
    arc["source"]["sha256"] = hashlib.sha256(doc_path.read_bytes()).hexdigest()
    (plan_dir / "_arc.yaml").write_bytes(_dump(arc))
    registry = derived_registry(plan)
    if registry:
        (plan_dir / "_grammar.yaml").write_bytes(_dump(registry))
    write_scope_sidecar(plan_path, slug, compute_scope(plan, LEVEL, slug))
    return World(plan_path=plan_path, pack_path=pack_path, words_path=words_path)


def build_base() -> tuple[dict, dict, dict]:
    return base_plan(), base_pack(), base_words()


def build_non_literacy() -> tuple[dict, dict, dict]:
    plan, pack, words = build_base()
    del plan["lessons"][0]["inventory"]["phonetics"]
    for step in plan["lessons"][0]["steps"]:
        step["introduces"]["letters"] = []
    return plan, pack, words


def build_cyrillic_lemma() -> tuple[dict, dict, dict]:
    """A core lemma in Cyrillic that exactly matches the word-store record (rule 7)."""
    plan, pack, words = build_base()
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["lemma"] = LEMMA_MAMA
    words["words"][0]["lemma"] = LEMMA_MAMA
    return plan, pack, words


def _checkpoint_lesson(n: int = 1) -> dict:
    return {
        "n": n,
        "slug": f"lesson-{n}",
        "title": "Checkpoint",
        "kind": "checkpoint",
        "job": "Show the module's skills.",
        "rationale": "Learner-position checkpoint.",
        "word_target": 5,
        "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
        "steps": [{"id": "s1", "kind": "practice", "evidence": ["T-001"], "practice": ["a1"]}],
        "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Checkpoint quiz."}],
    }


def build_checkpoint() -> tuple[dict, dict, dict]:
    plan, pack, words = build_base()
    plan["lessons"] = [_checkpoint_lesson()]
    return plan, pack, words


def _teach_close_lesson(n: int, slug: str) -> dict:
    return {
        "n": n,
        "slug": slug,
        "title": "Closing lesson",
        "kind": "teach",
        "closes_with_recap": True,
        "job": "The last new material.",
        "rationale": "Closes with a recap step.",
        "word_target": 5,
        "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
        "steps": [
            {"id": "s1", "kind": "practice", "evidence": ["T-002"], "practice": ["a1"]},
            {"id": "s2", "kind": "recap", "evidence": ["T-001"], "practice": []},
        ],
        "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Final quiz."}],
    }


def _plain_teach_lesson(n: int, slug: str) -> dict:
    lesson = _teach_close_lesson(n, slug)
    del lesson["closes_with_recap"]
    lesson["steps"] = lesson["steps"][:1]
    return lesson


def build_shape_b() -> tuple[dict, dict, dict]:
    plan, pack, words = build_base()
    plan["lessons"] = [plan["lessons"][0], _teach_close_lesson(2, "lesson-two")]
    return plan, pack, words


def build_shape_b_three_teach() -> tuple[dict, dict, dict]:
    plan, pack, words = build_base()
    plan["lessons"] = [
        plan["lessons"][0],
        _plain_teach_lesson(2, "lesson-two"),
        _teach_close_lesson(3, "lesson-three"),
    ]
    return plan, pack, words


Mutate = Callable[[dict, dict, dict], None]
Post = Callable[[World, dict, dict, dict], Path | None]
Kwargs = Callable[[World], dict]


@dataclass(frozen=True)
class Case:
    name: str
    build: Callable[[], tuple[dict, dict, dict]] = build_base
    mutate: Mutate | None = None
    post: Post | None = None
    kwargs: Kwargs | None = None
    expected: frozenset[str] = frozenset()
    notes: frozenset[str] = frozenset()


def _mutate(fn: Mutate) -> Mutate:
    return fn


def _post_write_plan(new_plan_path: Path) -> Post:
    def post(world: World, plan: dict, pack: dict, words: dict) -> Path:
        new_plan_path.parent.mkdir(parents=True, exist_ok=True)
        new_plan_path.write_bytes(_dump(plan))
        return new_plan_path

    return post


VALID_CASES = [
    Case("valid_literacy_r9"),
    Case("valid_non_literacy", build=build_non_literacy),
    Case("valid_cyrillic_lemma", build=build_cyrillic_lemma),
    Case("valid_checkpoint", build=build_checkpoint),
    Case("valid_closing_shape_b", build=build_shape_b, notes=frozenset({codes.CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW})),
]

FAILING_CASES = [
    # rule 1 and the kind rules
    Case(
        "lessons_empty",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("lessons", [])),
        expected=frozenset({codes.LESSONS_EMPTY}),
    ),
    Case(
        "lesson_n_not_contiguous",
        mutate=_mutate(lambda p, pk, w: p["lessons"][1].__setitem__("n", 3)),
        expected=frozenset({codes.LESSON_N_NOT_CONTIGUOUS}),
    ),
    Case(
        "closing_shape_invalid_teach_last",
        mutate=_mutate(lambda p, pk, w: p["lessons"][1].__setitem__("kind", "teach")),
        expected=frozenset({codes.CLOSING_SHAPE_INVALID}),
    ),
    Case(
        "closing_shape_b_three_teach_lessons",
        build=build_shape_b_three_teach,
        expected=frozenset({codes.CLOSING_SHAPE_INVALID}),
    ),
    Case(
        "closes_with_recap_not_last",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0].__setitem__("closes_with_recap", True)),
        expected=frozenset({codes.CLOSES_WITH_RECAP_NOT_LAST}),
    ),
    Case(
        "teach_step_in_practice_lesson",
        mutate=_mutate(
            lambda p, pk, w: (
                p["lessons"].insert(
                    1,
                    {
                        "n": 2,
                        "slug": "lesson-mid",
                        "title": "Middle lesson",
                        "kind": "practice",
                        "job": "Practice.",
                        "rationale": "Between.",
                        "word_target": 5,
                        "inventory": {"grammar": [], "vocabulary": {"core": [], "incidental": [], "recycled": []}},
                        "steps": [
                            {
                                "id": "s1",
                                "kind": "teach",
                                "teach": "A teach step in the wrong lesson.",
                                "evidence": ["T-001"],
                                "practice": ["a1"],
                            }
                        ],
                        "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz."}],
                    },
                )
                or p["lessons"][2].__setitem__("n", 3)
            )
        ),
        expected=frozenset({codes.TEACH_STEP_OUTSIDE_TEACH_LESSON}),
    ),
    Case(
        "non_teach_lesson_introduces",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][1]["inventory"]["vocabulary"].__setitem__(
                "core", [{"lemma": "lemma-one", "evidence": "W-001", "forms": ["tag-a"]}]
            )
        ),
        expected=frozenset({codes.NON_TEACH_LESSON_INTRODUCES}),
    ),
    Case(
        "checkpoint_lesson_with_recap_step",
        build=build_checkpoint,
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"].append({"id": "s2", "kind": "recap", "evidence": ["T-002"]})
        ),
        expected=frozenset({codes.CHECKPOINT_STEP_KIND}),
    ),
    Case(
        "introduces_on_non_teach_step",
        mutate=_mutate(
            lambda p, pk, w: (
                p["lessons"][0]["steps"][2]["introduces"].__setitem__("vocabulary", ["W-009"]),
                p["lessons"][0]["inventory"]["vocabulary"]["core"].append(
                    {"lemma": "lemma-nine", "evidence": "W-009", "forms": ["tag-a"]}
                ),
            )
        ),
        expected=frozenset({codes.INTRODUCES_ON_NON_TEACH_STEP}),
    ),
    # inventory equals declared introductions
    Case(
        "introduced_twice",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"][1]["introduces"].__setitem__("letters", [LETTER_O, LETTER_A])
        ),
        expected=frozenset({codes.INTRODUCED_TWICE}),
    ),
    Case(
        "inventory_item_in_no_step",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["inventory"]["vocabulary"].__setitem__(
                "core", [{"lemma": "lemma-seven", "evidence": "W-007", "forms": ["tag-a", "tag-b"]}]
            )
        ),
        expected=frozenset({codes.INVENTORY_INTRODUCTION_MISMATCH}),
    ),
    # within-lesson order and recycled
    Case(
        "uses_before_introducing_step",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][0]["uses"].__setitem__("grammar", ["G-a1-001"])),
        expected=frozenset({codes.USES_BEFORE_INTRODUCTION}),
    ),
    Case(
        "uses_not_introduced_not_recycled",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"][1]["uses"].__setitem__("vocabulary", ["W-003", "W-008"])
        ),
        expected=frozenset({codes.USES_NOT_RECYCLED, codes.USED_NOT_INTRODUCED_EARLIER}),
    ),
    Case(
        "recycled_used_by_no_step",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][1]["uses"].__setitem__("vocabulary", [])),
        expected=frozenset({codes.RECYCLED_NOT_USED}),
    ),
    Case(
        "recycled_introduced_by_same_lesson",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["inventory"]["vocabulary"].__setitem__("recycled", ["W-003", "W-001"])
        ),
        expected=frozenset({codes.RECYCLED_INTRODUCED_HERE}),
    ),
    Case(
        "uses_not_recycled_in_recap_lesson",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][1]["steps"][0].__setitem__("uses", {"grammar": [], "vocabulary": ["W-001"]})
        ),
        expected=frozenset({codes.USES_NOT_RECYCLED}),
    ),
    Case(
        "recycled_not_used_in_recap_lesson",
        mutate=_mutate(lambda p, pk, w: p["lessons"][1]["inventory"]["vocabulary"].__setitem__("recycled", ["W-001"])),
        expected=frozenset({codes.RECYCLED_NOT_USED}),
    ),
    # rule 3: evidence resolves and the pack is the locked one
    Case(
        "unknown_pack_id",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][1].__setitem__("evidence", ["T-002", "T-099"])),
        expected=frozenset({codes.UNKNOWN_PACK_ID}),
    ),
    Case(
        "unknown_word_id",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["practice"].__setitem__("stress", ["W-001", "W-099"])),
        expected=frozenset({codes.UNKNOWN_WORD_ID}),
    ),
    Case(
        "unknown_word_id_in_step",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"][1]["uses"].__setitem__("vocabulary", ["W-003", "W-099"])
        ),
        expected=frozenset({codes.UNKNOWN_WORD_ID, codes.USES_NOT_RECYCLED, codes.USED_NOT_INTRODUCED_EARLIER}),
    ),
    Case(
        "evidence_ref_path_identifies_checked_pack",
        mutate=_mutate(lambda p, pk, w: p["evidence_ref"].__setitem__("path", "evidence/a1/nonexistent.yaml")),
        expected=frozenset({codes.PACK_NOT_FOUND}),
    ),
    Case(
        "pack_override_must_match_declared_path",
        mutate=_mutate(lambda p, pk, w: p["evidence_ref"].__setitem__("path", "evidence/a1/nonexistent.yaml")),
        kwargs=lambda world: {"pack_path": world.pack_path},
        expected=frozenset({codes.PACK_PATH_MISMATCH}),
    ),
    Case(
        "pack_hash_differs_from_evidence_ref",
        post=lambda world, p, pk, w: _write_plan_with_wrong_hash(world, p),
        expected=frozenset({codes.PACK_HASH_MISMATCH}),
    ),
    Case(
        "pack_lock_differs_from_file",
        post=lambda world, p, pk, w: _rewrite_pack_stale_lock(world, p, pk),
        expected=frozenset({codes.PACK_LOCK_MISMATCH}),
    ),
    Case(
        "words_lock_differs_from_file",
        post=lambda world, p, pk, w: _rewrite_words_stale_lock(world, w),
        expected=frozenset({codes.WORDS_LOCK_MISMATCH}),
    ),
    Case(
        "words_list_inside_pack",
        mutate=_mutate(lambda p, pk, w: pk.__setitem__("words", [])),
        expected=frozenset({codes.PACK_WORDS_LIST_PRESENT}),
    ),
    Case(
        "duplicate_pack_ids",
        mutate=_mutate(lambda p, pk, w: pk["texts"].append({"id": "T-001"})),
        expected=frozenset({codes.DUPLICATE_PACK_ID}),
    ),
    Case(
        "duplicate_word_ids",
        mutate=_mutate(lambda p, pk, w: w["words"].append({"id": "W-001", "lemma": "lemma-one", "forms": []})),
        expected=frozenset({codes.DUPLICATE_WORD_ID}),
    ),
    Case(
        "pack_record_without_id",
        mutate=_mutate(lambda p, pk, w: pk["texts"].append({"source": "no id"})),
        expected=frozenset({codes.PACK_MALFORMED}),
    ),
    Case(
        "word_record_without_lemma",
        mutate=_mutate(lambda p, pk, w: w["words"].append({"id": "W-100", "forms": []})),
        expected=frozenset({codes.WORDS_MALFORMED}),
    ),
    # rule 6: steps and activities
    Case(
        "teach_step_without_practice",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][1].__setitem__("practice", [])),
        expected=frozenset({codes.TEACH_STEP_WITHOUT_PRACTICE}),
    ),
    Case(
        "activity_id_not_defined",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0].__setitem__("consolidation", ["a3", "a9"])),
        expected=frozenset({codes.UNKNOWN_ACTIVITY_ID}),
    ),
    Case(
        "duplicate_activity_id",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["activities"].append(
                {"id": "a1", "type": "quiz", "placement": "inline", "focus": "Duplicate."}
            )
        ),
        expected=frozenset({codes.DUPLICATE_ACTIVITY_ID}),
    ),
    Case(
        "duplicate_step_id",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"].append(
                {"id": "s2", "kind": "practice", "evidence": ["T-001"], "practice": ["a1"]}
            )
        ),
        expected=frozenset({codes.DUPLICATE_STEP_ID}),
    ),
    Case(
        "unknown_activity_type",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["activities"][2].__setitem__("type", "jetons")),
        expected=frozenset({codes.UNKNOWN_ACTIVITY_TYPE}),
    ),
    Case(
        "activity_schema_file_missing",
        kwargs=lambda world: {"activity_schema_path": world.plan_path.parent / "no-such-schema.json"},
        expected=frozenset({codes.ACTIVITY_SCHEMA_UNAVAILABLE}),
    ),
    Case(
        "activity_schema_key_without_level_suffix",
        kwargs=lambda world: {"activity_schema_path": _write_bad_activity_schema(world)},
        expected=frozenset({codes.ACTIVITY_SCHEMA_MALFORMED}),
    ),
    # rule 7 and revision 8
    Case(
        "lemma_differs_from_store",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["inventory"]["vocabulary"]["core"][0].__setitem__("lemma", "lemma-wrong")
        ),
        expected=frozenset({codes.LEMMA_MISMATCH}),
    ),
    Case(
        "forms_tag_not_in_record",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["inventory"]["vocabulary"]["core"][0].__setitem__(
                "forms", ["tag-a", "tag-zzz"]
            )
        ),
        expected=frozenset({codes.UNKNOWN_FORM_TAG}),
    ),
    Case(
        "incidental_entry_with_forms",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["inventory"]["vocabulary"]["incidental"][0].__setitem__("forms", ["tag-a"])
        ),
        expected=frozenset({codes.INCIDENTAL_FORMS_PRESENT}),
    ),
    Case(
        "cyrillic_in_disallowed_field",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["inventory"]["grammar"][0].__setitem__("point", "мама")),
        expected=frozenset({codes.CYRILLIC_IN_DISALLOWED_FIELD}),
    ),
    Case(
        "combining_acute_in_job",
        mutate=_mutate(lambda p, pk, w: p["lessons"][1].__setitem__("job", "Review the module.́")),
        expected=frozenset({codes.STRESS_MARK_IN_PLAN}),
    ),
    Case(
        "combining_grave_in_title",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("title", "Module one titlè")),
        expected=frozenset({codes.STRESS_MARK_IN_PLAN}),
    ),
    # revision 9 fields
    Case(
        "dialogue_without_step",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["dialogue"].pop("step")),
        expected=frozenset({codes.DIALOGUE_STEP_MISSING}),
    ),
    Case(
        "dialogue_step_not_in_steps",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["dialogue"].__setitem__("step", "s9")),
        expected=frozenset({codes.DIALOGUE_STEP_UNKNOWN}),
    ),
    Case(
        "speaker_without_evidence",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["dialogue"]["speakers"][0].pop("evidence")),
        expected=frozenset({codes.SPEAKER_EVIDENCE_MISSING}),
    ),
    Case(
        "needs_example_without_ex_record",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][0].__setitem__("evidence", ["T-001"])),
        expected=frozenset({codes.NEED_KIND_UNSATISFIED}),
    ),
    Case(
        "paradigm_form_tag_not_in_record",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["steps"][0]["paradigm"].__setitem__("forms", ["tag-zzz"])),
        expected=frozenset({codes.UNKNOWN_FORM_TAG}),
    ),
    Case(
        "duplicate_paradigm_id",
        mutate=_mutate(
            lambda p, pk, w: p["lessons"][0]["steps"][1].__setitem__(
                "paradigm", {"id": "P-01", "word": "W-001", "forms": ["tag-a"]}
            )
        ),
        expected=frozenset({codes.DUPLICATE_PARADIGM_ID}),
    ),
    Case(
        "error_correction_without_error_refs",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["activities"][1].pop("error_refs")),
        expected=frozenset({codes.ERROR_REFS_MISSING}),
    ),
    Case(
        "error_refs_on_quiz",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["activities"][0].__setitem__("error_refs", ["E-001"])),
        expected=frozenset({codes.ERROR_REFS_FORBIDDEN}),
    ),
    Case(
        "error_ref_id_not_e_shaped",
        mutate=_mutate(lambda p, pk, w: p["lessons"][0]["activities"][1].__setitem__("error_refs", ["X-001"])),
        expected=frozenset({codes.SCHEMA_VIOLATION}),
    ),
    Case(
        "error_ref_not_an_error_record",
        mutate=_mutate(
            lambda p, pk, w: (
                pk["texts"].append({"id": "E-099"}),
                p["lessons"][0]["activities"][1].__setitem__("error_refs", ["E-099"]),
            )
        ),
        expected=frozenset({codes.ERROR_REF_NOT_ERROR_RECORD}),
    ),
    # loader and schema
    Case(
        "missing_plan_schema_is_v1",
        mutate=_mutate(lambda p, pk, w: p.pop("plan_schema")),
        expected=frozenset({codes.V1_PLAN}),
    ),
    Case(
        "content_outline_is_v1",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("content_outline", [])),
        expected=frozenset({codes.V1_PLAN}),
    ),
    Case(
        "minutes_key_fails",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("minutes", 60)),
        expected=frozenset({codes.REMOVED_V1_FIELD}),
    ),
    Case(
        "module_word_target_fails",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("word_target", 100)),
        expected=frozenset({codes.REMOVED_V1_FIELD}),
    ),
    Case(
        "scope_key_fails",
        mutate=_mutate(lambda p, pk, w: p.__setitem__("scope", {})),
        expected=frozenset({codes.SCOPE_KEY_IN_PLAN}),
    ),
    Case(
        "schema_violation_missing_title",
        mutate=_mutate(lambda p, pk, w: p.pop("title")),
        expected=frozenset({codes.SCHEMA_VIOLATION}),
    ),
    Case(
        "plan_under_plans_dir",
        post=lambda world, p, pk, w: _post_write_plan(world.plan_path.parents[2] / "plans" / LEVEL / f"{SLUG}.yaml")(
            world, p, pk, w
        ),
        expected=frozenset({codes.PLAN_OUTSIDE_LESSON_PLANS}),
    ),
    Case(
        "plan_outside_curriculum_tree",
        post=lambda world, p, pk, w: _post_write_plan(world.plan_path.parents[5] / "elsewhere.yaml")(world, p, pk, w),
        expected=frozenset({codes.PLAN_OUTSIDE_LESSON_PLANS}),
    ),
    Case(
        "underscore_file_is_not_a_plan",
        post=lambda world, p, pk, w: _post_write_plan(world.plan_path.parent / "_x.yaml")(world, p, pk, w),
        expected=frozenset({codes.NOT_A_PLAN}),
    ),
    Case(
        "plan_file_missing",
        post=lambda world, p, pk, w: world.plan_path.unlink() and None,
        expected=frozenset({codes.PLAN_NOT_FOUND}),
    ),
    Case(
        "plan_file_invalid_yaml",
        post=lambda world, p, pk, w: world.plan_path.write_text("x: [unclosed", encoding="utf-8") and None,
        expected=frozenset({codes.PLAN_YAML_INVALID}),
    ),
    Case(
        "pack_file_missing",
        post=lambda world, p, pk, w: world.pack_path.unlink() and None,
        expected=frozenset({codes.PACK_NOT_FOUND}),
    ),
    Case(
        "pack_file_invalid_yaml",
        post=lambda world, p, pk, w: world.pack_path.write_text("x: [unclosed", encoding="utf-8") and None,
        expected=frozenset({codes.PACK_YAML_INVALID}),
    ),
    Case(
        "words_file_missing",
        post=lambda world, p, pk, w: world.words_path.unlink() and None,
        expected=frozenset({codes.WORDS_NOT_FOUND}),
    ),
    Case(
        "words_file_invalid_yaml",
        post=lambda world, p, pk, w: world.words_path.write_text("x: [unclosed", encoding="utf-8") and None,
        expected=frozenset({codes.WORDS_YAML_INVALID}),
    ),
]

ALL_CASES = VALID_CASES + FAILING_CASES


def _write_plan_with_wrong_hash(world: World, plan: dict) -> None:
    """Rebind evidence_ref.sha256 to a wrong value; the pack and its lock stay consistent."""
    plan = copy.deepcopy(plan)
    plan["evidence_ref"]["sha256"] = "0" * 64
    world.plan_path.write_bytes(_dump(plan))
    return None


def _rewrite_pack_stale_lock(world: World, plan: dict, pack: dict) -> None:
    """Rewrite the pack (new bytes), rebind evidence_ref, leave the lock stale."""
    pack = copy.deepcopy(pack)
    pack["standard"].append({"id": "S-002"})
    pack_bytes = _dump(pack)
    world.pack_path.write_bytes(pack_bytes)
    plan["evidence_ref"]["sha256"] = hashlib.sha256(pack_bytes).hexdigest()
    world.plan_path.write_bytes(_dump(plan))
    return None


def _rewrite_words_stale_lock(world: World, words: dict) -> None:
    words = copy.deepcopy(words)
    words["words"].append({"id": "W-100", "lemma": "lemma-hundred", "forms": []})
    world.words_path.write_bytes(_dump(words))
    return None


def _write_bad_activity_schema(world: World) -> Path:
    path = world.plan_path.parent / "bad-activities-schema.json"
    path.write_text(json.dumps({"definitions": {"quiz": {}}}), encoding="utf-8")
    return path


def case_by_name(name: str) -> Case:
    return next(case for case in ALL_CASES if case.name == name)


def run_case(root: Path, case: Case) -> Report:
    plan, pack, words = case.build()
    if case.mutate:
        case.mutate(plan, pack, words)
    world = write_world(root, plan, pack, words)
    plan_path = world.plan_path
    if case.post:
        result = case.post(world, plan, pack, words)
        if result is not None:
            plan_path = result
    kwargs = case.kwargs(world) if case.kwargs else {}
    return validate_plan(LEVEL, SLUG, plan_path=plan_path, **kwargs)


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda case: case.name)
def test_case(tmp_path: Path, case: Case) -> None:
    report = run_case(tmp_path, case)
    assert {o.code for o in report.failures} == set(case.expected), report.render_text()
    assert {o.code for o in report.notes} == set(case.notes), report.render_text()
    assert {o.code for o in report.not_checked} == NOT_CHECKED
    assert report.ok == (not case.expected)


def test_valid_plan_reports_all_not_checked_and_full_gate(tmp_path: Path) -> None:
    report = run_case(tmp_path, VALID_CASES[0])
    text = report.render_text()
    assert "the §6 gate" in text
    assert "cross_plan_rules_pending" not in text
    for code in NOT_CHECKED:
        assert f"NOT_CHECKED {code}" in text
    payload = report.to_json()
    assert payload["status"] == "pass"
    assert "the §6 gate" in payload["validator"]
    assert {entry["code"] for entry in payload["not_checked"]} == NOT_CHECKED
    assert payload["waivers"] == []


def test_failure_names_code_lesson_step_and_value(tmp_path: Path) -> None:
    report = run_case(tmp_path, case_by_name("introduced_twice"))
    outcome = report.failures[0]
    assert outcome.code == codes.INTRODUCED_TWICE
    assert outcome.lesson == 1
    assert LETTER_A in outcome.message
    step_report = run_case(tmp_path / "b", case_by_name("uses_before_introducing_step"))
    step_outcome = step_report.failures[0]
    assert step_outcome.lesson == 1
    assert step_outcome.step == "s1"
    assert "G-a1-001" in step_outcome.message


def test_evidence_failures_keep_lesson_and_step(tmp_path: Path) -> None:
    report = run_case(tmp_path, case_by_name("unknown_pack_id"))
    outcome = next(o for o in report.failures if o.code == codes.UNKNOWN_PACK_ID)
    assert outcome.lesson == 1
    assert outcome.step == "s2"
    word_report = run_case(tmp_path / "b", case_by_name("unknown_word_id_in_step"))
    word_outcome = next(o for o in word_report.failures if o.code == codes.UNKNOWN_WORD_ID)
    assert word_outcome.lesson == 1
    assert word_outcome.step == "s2"


def test_schema_failure_keeps_lesson_and_step(tmp_path: Path) -> None:
    plan, pack, words = build_base()
    plan["lessons"][0]["steps"][1]["kind"] = "bogus"
    world = write_world(tmp_path, plan, pack, words)
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    outcome = next(o for o in report.failures if o.code == codes.SCHEMA_VIOLATION)
    assert outcome.lesson == 1
    assert outcome.step == "s2"
    assert "kind" in outcome.message


def test_inventory_mismatch_reports_missing_and_extra_separately(tmp_path: Path) -> None:
    report = run_case(tmp_path, case_by_name("inventory_item_in_no_step"))
    messages = [o.message for o in report.failures if o.code == codes.INVENTORY_INTRODUCTION_MISMATCH]
    assert len(messages) == 2
    assert any("missing from" in message and "W-001" in message for message in messages)
    assert any("introduced by no step" in message and "W-007" in message for message in messages)


def test_code_registry_matches_produced_codes(tmp_path: Path) -> None:
    produced: set[str] = set()
    for index, case in enumerate(ALL_CASES):
        produced |= run_case(tmp_path / f"case-{index}", case).codes()
    from tests.curriculum.test_plan_validate_cross import produced_cross_codes

    produced |= produced_cross_codes(tmp_path / "cross")
    assert produced == set(codes.DESCRIPTIONS)


def test_pack_override_matching_declared_path_passes(tmp_path: Path) -> None:
    world = write_world(tmp_path, *build_base())
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path, pack_path=world.pack_path)
    assert report.ok, report.render_text()


def test_cli_text_output(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    world = write_world(tmp_path, *build_base())
    assert validate_main([LEVEL, SLUG, "--plan", str(world.plan_path)]) == 0
    out = capsys.readouterr().out
    assert "the §6 gate" in out
    assert "status: pass" in out
    for code in NOT_CHECKED:
        assert code in out


def test_cli_json_output(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    world = write_world(tmp_path, *build_base())
    assert validate_main([LEVEL, SLUG, "--plan", str(world.plan_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    assert "the §6 gate" in payload["validator"]
    assert {entry["code"] for entry in payload["not_checked"]} == NOT_CHECKED


def test_cli_failing_plan_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    plan, pack, words = build_base()
    plan["minutes"] = 60
    world = write_world(tmp_path, plan, pack, words)
    assert validate_main([LEVEL, SLUG, "--plan", str(world.plan_path)]) == 1
    assert codes.REMOVED_V1_FIELD in capsys.readouterr().out


def test_help_lists_every_code(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as excinfo:
        validate_main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for code in codes.DESCRIPTIONS:
        assert code in out


def test_cli_subprocess_clean_environment(tmp_path: Path) -> None:
    """The CLI runs from the repository root under env -i (only PATH and HOME)."""
    good = write_world(tmp_path / "good", *build_base())
    bad_plan, bad_pack, bad_words = build_base()
    bad_plan["minutes"] = 60
    bad = write_world(tmp_path / "bad", bad_plan, bad_pack, bad_words)
    env = [f"PATH={os.environ['PATH']}", f"HOME={os.environ.get('HOME', str(tmp_path))}"]

    def run(plan_path: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "env",
                "-i",
                *env,
                sys.executable,
                "-m",
                "scripts.curriculum.validate",
                LEVEL,
                SLUG,
                "--plan",
                str(plan_path),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )

    ok = run(good.plan_path)
    assert ok.returncode == 0, ok.stderr
    assert "the §6 gate" in ok.stdout
    failing = run(bad.plan_path)
    assert failing.returncode == 1
    assert codes.REMOVED_V1_FIELD in failing.stdout
