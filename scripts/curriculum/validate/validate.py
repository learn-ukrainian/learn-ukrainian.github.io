"""Module plan validator — library and CLI (issue #8412, Briefs A and B).

The complete §6 gate of docs/epics/fresh-build-plan-schema.md: §2 rules 1–7
with the semantics of §2a. One plan is checked against its evidence pack and
the level word store (rules 1, 2, 3, 6, 7, the inventory/introductions
equality, the single-plan part of rule 4), against every plan at an earlier
arc position (rule 4), against the level arc (rule 5), against the level
grammar registry, and against its own generated scope sidecar and its module
title. Pilots written out of order can be validated with an explicit, printed
waiver (--allow-missing-prior); --strict refuses every waiver flag and
verifies the registry is append-only over git history, so a plan that needs a
waiver can never be built or merged as buildable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from . import codes
from .cross import check_arc, check_rule4, load_level_plans
from .loader import (
    PLAN_SCHEMA_PATH,
    REPO_ROOT,
    PlanError,
    check_plan_slug,
    evidence_root,
    load_plan,
    read_plan_text,
    resolve_plan_path,
    sha256_of,
)
from .pack import load_pack, load_words, lock_digest
from .registry import check_append_only, check_plan_against_registry, load_registry, registry_path_for
from .report import Outcome, Report
from .scope import check_scope_sidecar, check_title, title_quantities_outcome

_CYRILLIC = re.compile(r"[А-Яа-яЇїІіЄєҐґЬь]")
_STRESS_MARKS = ("\u0301", "\u0300")  # combining acute, combining grave

#: Where a needs entry's evidence record lives (r9): pack id prefix, or the
#: step's own paradigm block.
_NEED_ID_PREFIX = {"example": "EX-", "quote": "T-", "culture": "T-", "error": "E-", "video": "V-"}


#: Cyrillic is allowed only in these prose fields (rule 7, §2a "Rule 7,
#: precisely"), plus single letters in phonetics.letters / introduces.letters
#: (schema-enforced), dialogue.places[].name (r9: prose, like speaker name) and
#: the inventory vocabulary lemmas (rule 7: a lemma equals the word-store
#: record's lemma, which is Ukrainian).
def _cyrillic_allowed(path: tuple) -> bool:
    """path is the JSON path of a string value inside the plan."""
    if path in (("title",), ("subtitle",), ("focus",)):
        return True
    if path[0] == "objectives":
        return True
    if path[0] != "lessons" or len(path) < 3:
        return False
    rest = path[2:]
    # single letters in phonetics.letters and introduces.letters (schema
    # already enforces the single-letter shape)
    if rest == ("inventory", "phonetics", "letters", rest[-1]) and len(rest) == 4:
        return True
    if len(rest) == 5 and rest[0] == "steps" and rest[2:] == ("introduces", "letters", rest[-1]):
        return True
    # vocabulary lemmas equal the word-store record's lemma, which is Ukrainian
    if len(rest) == 5 and rest[:3] in (("inventory", "vocabulary", "core"), ("inventory", "vocabulary", "incidental")):
        return rest[4] == "lemma"
    if rest in (("title",), ("job",), ("rationale",)):
        return True
    if len(rest) >= 2 and rest[0] == "steps" and rest[2:] == ("teach",):
        return True
    if len(rest) >= 2 and rest[0] == "activities" and rest[2:] == ("focus",):
        return True
    if len(rest) >= 2 and rest[0] == "videos" and rest[2:] == ("use",):
        return True
    if rest[0] == "dialogue":
        if rest[1:] in (("situation",), ("setting",), ("target_grammar",)):
            return True
        if len(rest) >= 3 and rest[1] == "speakers" and rest[3:] == ("name",):
            return True
        if len(rest) >= 3 and rest[1] == "places" and rest[3:] == ("name",):
            return True
    return False


def _fail(report: Report, code: str, message: str, lesson: int | None = None, step: str | None = None) -> None:
    report.failures.append(Outcome(code, message, lesson, step))


def _always_not_checked(report: Report) -> None:
    """The not_checked items every run reports (§2a), pass or fail."""
    report.not_checked.append(
        Outcome(codes.MINUTES_CONSTANTS_UNDEFINED, codes.DESCRIPTIONS[codes.MINUTES_CONSTANTS_UNDEFINED])
    )
    report.not_checked.append(
        Outcome(codes.WORD_TARGET_NOT_CALIBRATED, codes.DESCRIPTIONS[codes.WORD_TARGET_NOT_CALIBRATED])
    )
    report.not_checked.append(
        Outcome(
            codes.LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED,
            codes.DESCRIPTIONS[codes.LESSON_ACTIVITY_MINIMUMS_NOT_CALIBRATED],
        )
    )
    report.not_checked.append(
        Outcome(
            codes.ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY,
            codes.DESCRIPTIONS[codes.ARC_HAS_NO_STRUCTURED_GRAMMAR_OR_VOCABULARY],
        )
    )


def _check_stress_marks(report: Report, plan_text: str) -> None:
    """U+0301 or U+0300 anywhere in the plan file fails (rule 7)."""
    for line_no, line in enumerate(plan_text.splitlines(), start=1):
        for mark in _STRESS_MARKS:
            if mark in line:
                _fail(
                    report,
                    codes.STRESS_MARK_IN_PLAN,
                    f"U+{ord(mark):04X} in {line.strip()!r} (line {line_no}); stress lives in the word store",
                )


def _check_cyrillic(report: Report, plan: dict) -> None:
    """Cyrillic outside the allowed prose fields fails (rule 7)."""

    def walk(node: object, path: tuple) -> None:
        if isinstance(node, str):
            if _CYRILLIC.search(node) and not _cyrillic_allowed(path):
                _fail(report, codes.CYRILLIC_IN_DISALLOWED_FIELD, f"{'/'.join(map(str, path))}: {node!r}")
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(value, (*path, key))
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, (*path, index))

    walk(plan, ())


def _activity_allowlist(report: Report, level: str, schema_path: Path | None) -> set[str] | None:
    """The level's activity type allowlist, read at run time; None when it failed."""
    schema_path = schema_path or REPO_ROOT / f"schemas/activities-{level}.schema.json"
    if not schema_path.is_file():
        _fail(
            report,
            codes.ACTIVITY_SCHEMA_UNAVAILABLE,
            f"{schema_path} does not exist; there is no fallback to another level or to activities-base",
        )
        return None
    definitions = json.loads(schema_path.read_text(encoding="utf-8")).get("definitions", {})
    allowed: set[str] = set()
    for key in definitions:
        if not key.endswith(f"-{level}"):
            _fail(
                report,
                codes.ACTIVITY_SCHEMA_MALFORMED,
                f"{schema_path} definition {key!r} lacks the -{level} suffix; "
                "there is no fallback to another level or to activities-base",
            )
            return None
        allowed.add(key[: -len(f"-{level}")])
    return allowed


def _check_lesson_shape(report: Report, plan: dict) -> None:
    """Rule 1, the lesson-kind rules and rule 2 (§2a)."""
    lessons = plan["lessons"]
    if not lessons:
        _fail(report, codes.LESSONS_EMPTY, "lessons is empty; a module has at least one lesson (rule 1)")
        return
    numbers = [lesson["n"] for lesson in lessons]
    if numbers != list(range(1, len(lessons) + 1)):
        _fail(
            report,
            codes.LESSON_N_NOT_CONTIGUOUS,
            f"lesson n values are {numbers}, not 1..{len(lessons)} contiguous (rule 1)",
        )

    checkpoint_module = all(lesson["kind"] == "checkpoint" for lesson in lessons)
    teach_lessons = sum(1 for lesson in lessons if lesson["kind"] == "teach")

    for index, lesson in enumerate(lessons):
        n = lesson["n"]
        last = index == len(lessons) - 1
        if lesson.get("closes_with_recap") and not last:
            _fail(
                report,
                codes.CLOSES_WITH_RECAP_NOT_LAST,
                "closes_with_recap is allowed only on the last lesson (rule 1)",
                lesson=n,
            )
        for step in lesson["steps"]:
            step_id = step["id"]
            introduces = step.get("introduces") or {}
            introduced = any(introduces.get(key) for key in ("letters", "grammar", "vocabulary"))
            if step["kind"] != "teach" and introduced:
                _fail(
                    report,
                    codes.INTRODUCES_ON_NON_TEACH_STEP,
                    f"a {step['kind']} step carries a non-empty introduces (§2a)",
                    lesson=n,
                    step=step_id,
                )
        if lesson["kind"] != "teach":
            inventory = lesson["inventory"]
            phonetics = inventory.get("phonetics") or {}
            non_empty = (
                bool(phonetics.get("letters"))
                or bool(phonetics.get("sounds"))
                or bool(inventory.get("grammar"))
                or bool(inventory["vocabulary"]["core"])
            )
            if non_empty:
                _fail(
                    report,
                    codes.NON_TEACH_LESSON_INTRODUCES,
                    f"a {lesson['kind']} lesson introduces nothing: phonetics, grammar and "
                    "vocabulary.core must be empty (§2a)",
                    lesson=n,
                )
            for step in lesson["steps"]:
                if step["kind"] == "teach":
                    _fail(
                        report,
                        codes.TEACH_STEP_OUTSIDE_TEACH_LESSON,
                        f"a teach step exists only in a teach lesson, not in a {lesson['kind']} lesson (§2a)",
                        lesson=n,
                        step=step["id"],
                    )
        if lesson["kind"] == "checkpoint":
            for step in lesson["steps"]:
                if step["kind"] != "practice":
                    _fail(
                        report,
                        codes.CHECKPOINT_STEP_KIND,
                        f"a checkpoint lesson has practice steps only, not {step['kind']} (§2a)",
                        lesson=n,
                        step=step["id"],
                    )

    if checkpoint_module:
        return  # checkpoint modules are exempt from the closing shapes (rule 1)
    last_lesson = lessons[-1]
    if last_lesson["kind"] == "recap":
        return  # closing shape (a)
    if last_lesson["kind"] == "teach" and last_lesson.get("closes_with_recap"):
        final = last_lesson["steps"][-1] if last_lesson["steps"] else None
        introduces = (final or {}).get("introduces") or {}
        clean_recap = (
            final is not None
            and final["kind"] == "recap"
            and not any(introduces.get(key) for key in ("letters", "grammar", "vocabulary"))
        )
        if clean_recap and teach_lessons <= 2:
            report.notes.append(
                Outcome(
                    codes.CLOSING_SHAPE_B_NEEDS_PLAN_REVIEW,
                    "the module closes with a teach lesson carrying closes_with_recap; "
                    "the plan review must confirm this closing shape (rule 1b)",
                    lesson=last_lesson["n"],
                )
            )
            return
        why = []
        if teach_lessons > 2:
            why.append(f"the module has {teach_lessons} teach lessons, more than two")
        if not clean_recap:
            why.append("its last step is not a recap step that introduces nothing")
        _fail(
            report,
            codes.CLOSING_SHAPE_INVALID,
            "closing shape (b) is broken: " + "; ".join(why) + " (rule 1)",
            lesson=last_lesson["n"],
        )
        return
    _fail(
        report,
        codes.CLOSING_SHAPE_INVALID,
        f"the last lesson is kind {last_lesson['kind']!r}; the module must close with a recap lesson "
        "or with a teach lesson carrying closes_with_recap (rule 1)",
        lesson=last_lesson["n"],
    )


def _step_introduces(step: dict) -> dict[str, list]:
    introduces = step.get("introduces") or {}
    return {key: list(introduces.get(key) or []) for key in ("letters", "grammar", "vocabulary")}


def _check_inventory_and_order(report: Report, plan: dict) -> None:
    """Inventory equals declared introductions; the single-plan part of rule 4 (§2a)."""
    for lesson in plan["lessons"]:
        n = lesson["n"]
        inventory = lesson["inventory"]
        vocabulary = inventory["vocabulary"]

        introduced_by: dict[tuple[str, str], list[str]] = {}
        for step in lesson["steps"]:
            for kind, items in _step_introduces(step).items():
                for item in items:
                    introduced_by.setdefault((kind, item), []).append(step["id"])

        if lesson["kind"] == "teach":
            # a non-teach lesson's non-empty inventory already failed NON_TEACH_LESSON_INTRODUCES
            for (kind, item), step_ids in sorted(introduced_by.items()):
                if len(step_ids) > 1:
                    _fail(
                        report,
                        codes.INTRODUCED_TWICE,
                        f"{kind} item {item!r} is introduced by two steps: {', '.join(step_ids)} (§2a)",
                        lesson=n,
                    )

            declared = {
                "letters": sorted((inventory.get("phonetics") or {}).get("letters") or []),
                "grammar": sorted(entry["id"] for entry in inventory.get("grammar") or []),
                "vocabulary": sorted(entry["evidence"] for entry in vocabulary["core"]),
            }
            introduced = {kind: sorted(item for (k, item) in introduced_by if k == kind) for kind in declared}
            for kind in ("letters", "grammar", "vocabulary"):
                missing = sorted(set(introduced[kind]) - set(declared[kind]))
                extra = sorted(set(declared[kind]) - set(introduced[kind]))
                label = {
                    "letters": "phonetics.letters",
                    "grammar": "grammar[].id",
                    "vocabulary": "vocabulary.core[].evidence",
                }[kind]
                if missing:
                    _fail(
                        report,
                        codes.INVENTORY_INTRODUCTION_MISMATCH,
                        f"introduced by steps but missing from {label}: {', '.join(missing)} (§2a)",
                        lesson=n,
                    )
                if extra:
                    _fail(
                        report,
                        codes.INVENTORY_INTRODUCTION_MISMATCH,
                        f"in {label} but introduced by no step: {', '.join(extra)} (§2a)",
                        lesson=n,
                    )

            # Within-lesson order: a used id the same lesson introduces must come
            # from an earlier step (rule 4, single-plan part).
            introduced_so_far: set[str] = set()
            for step in lesson["steps"]:
                uses = step.get("uses") or {}
                for kind in ("grammar", "vocabulary"):
                    for item in uses.get(kind) or []:
                        if (kind, item) in introduced_by and item not in introduced_so_far:
                            _fail(
                                report,
                                codes.USES_BEFORE_INTRODUCTION,
                                f"{kind} id {item} is used here but introduced by a later step of this lesson (rule 4)",
                                lesson=n,
                                step=step["id"],
                            )
                for _kind, items in _step_introduces(step).items():
                    introduced_so_far.update(items)

        # Recycled-vocabulary checks need only the current lesson; they run for
        # every lesson kind, teach or not (§2a).
        lesson_introduced_words = {item for (kind, item) in introduced_by if kind == "vocabulary"}
        recycled = list(vocabulary["recycled"])
        used_words = [
            (step["id"], item)
            for step in lesson["steps"]
            for item in ((step.get("uses") or {}).get("vocabulary") or [])
        ]
        for step_id, item in used_words:
            if item not in lesson_introduced_words and item not in recycled:
                _fail(
                    report,
                    codes.USES_NOT_RECYCLED,
                    f"vocabulary id {item} is neither introduced by this lesson nor listed in recycled (§2a)",
                    lesson=n,
                    step=step_id,
                )
        for item in recycled:
            if item in lesson_introduced_words:
                _fail(
                    report,
                    codes.RECYCLED_INTRODUCED_HERE,
                    f"recycled id {item} is introduced by this same lesson (§2a)",
                    lesson=n,
                )
            if item not in {used for _, used in used_words}:
                _fail(
                    report,
                    codes.RECYCLED_NOT_USED,
                    f"recycled id {item} is used by no step of this lesson (§2a)",
                    lesson=n,
                )


def _check_activities(report: Report, plan: dict, allowlist: set[str] | None) -> None:
    """Rule 6 and the r9 error_refs/paradigm checks."""
    for lesson in plan["lessons"]:
        n = lesson["n"]
        activities = lesson.get("activities") or []
        seen: set[str] = set()
        defined: set[str] = set()
        for activity in activities:
            activity_id = activity["id"]
            if activity_id in seen:
                _fail(
                    report,
                    codes.DUPLICATE_ACTIVITY_ID,
                    f"activity id {activity_id!r} is defined twice (rule 6)",
                    lesson=n,
                )
            seen.add(activity_id)
            defined.add(activity_id)
            if allowlist is not None and activity["type"] not in allowlist:
                _fail(
                    report,
                    codes.UNKNOWN_ACTIVITY_TYPE,
                    f"activity {activity_id} has type {activity['type']!r}, not in the level allowlist (rule 6)",
                    lesson=n,
                )
            error_refs = activity.get("error_refs")
            if activity["type"] == "error-correction" and not error_refs:
                _fail(
                    report,
                    codes.ERROR_REFS_MISSING,
                    f"activity {activity_id} is error-correction but carries no error_refs (r9)",
                    lesson=n,
                )
            if activity["type"] != "error-correction" and error_refs:
                _fail(
                    report,
                    codes.ERROR_REFS_FORBIDDEN,
                    f"activity {activity_id} is {activity['type']}, not error-correction, but carries error_refs (r9)",
                    lesson=n,
                )
        referenced: list[tuple[str, str | None]] = []
        for step in lesson["steps"]:
            if step["kind"] == "teach" and not (step.get("practice") or []):
                _fail(
                    report,
                    codes.TEACH_STEP_WITHOUT_PRACTICE,
                    "a teach step lists at least one practice activity (rule 6)",
                    lesson=n,
                    step=step["id"],
                )
            referenced += [(activity_id, step["id"]) for activity_id in step.get("practice") or []]
        referenced += [(activity_id, None) for activity_id in lesson.get("consolidation") or []]
        referenced += [(activity_id, None) for activity_id in (lesson.get("practice") or {}).get("patterns") or []]
        for activity_id, step_id in referenced:
            if activity_id not in defined:
                where = f"referenced by step {step_id}" if step_id else "referenced by consolidation/practice.patterns"
                _fail(
                    report,
                    codes.UNKNOWN_ACTIVITY_ID,
                    f"activity id {activity_id!r} ({where}) is not defined in this lesson (rule 6)",
                    lesson=n,
                )


def _check_dialogue_and_needs(report: Report, plan: dict) -> None:
    """The r9 dialogue.step, speaker evidence, needs and paradigm id checks."""
    for lesson in plan["lessons"]:
        n = lesson["n"]
        step_ids: list[str] = []
        seen_step_ids: set[str] = set()
        for step in lesson["steps"]:
            if step["id"] in seen_step_ids:
                _fail(
                    report,
                    codes.DUPLICATE_STEP_ID,
                    f"step id {step['id']!r} appears twice in this lesson; dialogue.step and "
                    "within-lesson ordering become ambiguous (rule 6)",
                    lesson=n,
                    step=step["id"],
                )
            seen_step_ids.add(step["id"])
            step_ids.append(step["id"])
        dialogue = lesson.get("dialogue")
        if dialogue is not None:
            if "step" not in dialogue:
                _fail(report, codes.DIALOGUE_STEP_MISSING, "the dialogue block carries no step id (r9)", lesson=n)
            elif dialogue["step"] not in step_ids:
                _fail(
                    report,
                    codes.DIALOGUE_STEP_UNKNOWN,
                    f"dialogue.step {dialogue['step']!r} is not a step of this lesson (r9)",
                    lesson=n,
                )
            for index, speaker in enumerate(dialogue.get("speakers") or []):
                if "evidence" not in speaker:
                    _fail(
                        report,
                        codes.SPEAKER_EVIDENCE_MISSING,
                        f"speaker {index + 1} ({speaker.get('name')!r}) carries no word-store evidence id (r9)",
                        lesson=n,
                    )
        paradigm_ids: set[str] = set()
        for step in lesson["steps"]:
            paradigm = step.get("paradigm")
            if paradigm is not None:
                if paradigm["id"] in paradigm_ids:
                    _fail(
                        report,
                        codes.DUPLICATE_PARADIGM_ID,
                        f"paradigm id {paradigm['id']} appears twice in this lesson (r9)",
                        lesson=n,
                        step=step["id"],
                    )
                paradigm_ids.add(paradigm["id"])
            evidence = step.get("evidence") or []
            for need in step.get("needs") or []:
                if need == "paradigm":
                    satisfied = paradigm is not None
                else:
                    satisfied = any(item.startswith(_NEED_ID_PREFIX[need]) for item in evidence)
                if not satisfied:
                    _fail(
                        report,
                        codes.NEED_KIND_UNSATISFIED,
                        f"needs lists {need!r} but the step has no matching evidence record "
                        f"({'the step carries no paradigm' if need == 'paradigm' else 'no ' + _NEED_ID_PREFIX[need] + '… id in evidence'}) (r9)",
                        lesson=n,
                        step=step["id"],
                    )


def _text_hosting_step_ids(lesson: dict) -> set[str]:
    """Steps a true-false statement is checked against.

    A text host is the step named by ``dialogue.step``, or a step whose ``needs``
    contain ``quote``. Bilingual passages and ``video`` / ``culture`` needs are
    excluded on purpose: they are not texts a statement is checked against at
    this stage.
    """
    step_ids = {step["id"] for step in lesson.get("steps") or []}
    hosts: set[str] = set()
    dialogue = lesson.get("dialogue")
    if isinstance(dialogue, dict) and dialogue.get("step") in step_ids:
        hosts.add(dialogue["step"])
    for step in lesson.get("steps") or []:
        if "quote" in (step.get("needs") or []):
            hosts.add(step["id"])
    return hosts


def _activity_is_true_false(catalog: dict, activity_id: str) -> bool:
    activity = catalog.get(activity_id)
    return isinstance(activity, dict) and activity.get("type") == "true-false"


def _check_true_false_placement(report: Report, plan: dict) -> None:
    """R-19: true-false follows a text, stays within the text count, and does not run together."""
    for lesson in plan["lessons"]:
        n = lesson["n"]
        hosts = _text_hosting_step_ids(lesson)
        by_id = {activity["id"]: activity for activity in lesson.get("activities") or []}

        practice_refs: list[tuple[str, str]] = []
        for step in lesson.get("steps") or []:
            for activity_id in step.get("practice") or []:
                if not _activity_is_true_false(by_id, activity_id):
                    continue
                practice_refs.append((step["id"], activity_id))
                if step["id"] not in hosts:
                    _fail(
                        report,
                        codes.TRUE_FALSE_NOT_POST_TEXT,
                        f"true-false activity {activity_id} is in the practice of step {step['id']}, "
                        "which hosts neither the dialogue nor a quote (R-19)",
                        lesson=n,
                        step=step["id"],
                    )
        consolidation = list(lesson.get("consolidation") or [])
        consolidation_refs = [
            activity_id for activity_id in consolidation if _activity_is_true_false(by_id, activity_id)
        ]
        if consolidation_refs and not hosts:
            for activity_id in consolidation_refs:
                _fail(
                    report,
                    codes.TRUE_FALSE_NOT_POST_TEXT,
                    f"true-false activity {activity_id} is in consolidation, and this lesson has no text-hosting step (R-19)",
                    lesson=n,
                )
        total = len(practice_refs) + len(consolidation_refs)
        if total > len(hosts):
            _fail(
                report,
                codes.TRUE_FALSE_OVER_TEXT_COUNT,
                f"{total} true-false activities (practice and consolidation together) and {len(hosts)} text-hosting steps (R-19)",
                lesson=n,
            )
        for index in range(len(consolidation) - 1):
            left, right = consolidation[index], consolidation[index + 1]
            if _activity_is_true_false(by_id, left) and _activity_is_true_false(by_id, right):
                _fail(
                    report,
                    codes.TRUE_FALSE_RUN,
                    f"true-false activities {left} and {right} are adjacent in consolidation (R-19)",
                    lesson=n,
                )


def _check_word_facts(report: Report, plan: dict, store) -> None:
    """Rule 7's lemma/forms equality and the r8 incidental forms ban."""
    for lesson in plan["lessons"]:
        n = lesson["n"]
        vocabulary = lesson["inventory"]["vocabulary"]
        for entry in vocabulary["core"]:
            record = store.records.get(entry["evidence"])
            if record is None:
                continue  # UNKNOWN_WORD_ID is reported by the resolution pass
            if entry["lemma"] != record.lemma:
                _fail(
                    report,
                    codes.LEMMA_MISMATCH,
                    f"core entry {entry['evidence']} has lemma {entry['lemma']!r}, "
                    f"the word store records {record.lemma!r} (rule 7)",
                    lesson=n,
                )
            for tag in entry["forms"]:
                if tag not in record.form_tags:
                    _fail(
                        report,
                        codes.UNKNOWN_FORM_TAG,
                        f"core entry {entry['evidence']} cites form tag {tag!r}, "
                        "which the word-store record does not list (rule 7)",
                        lesson=n,
                    )
        for entry in vocabulary["incidental"]:
            if "forms" in entry:
                _fail(
                    report,
                    codes.INCIDENTAL_FORMS_PRESENT,
                    f"incidental entry {entry['evidence']} ({entry['lemma']!r}) carries forms; an incidental "
                    "word is neither taught nor drilled, so forms is forbidden on it (rule 7, r8)",
                    lesson=n,
                )
            record = store.records.get(entry["evidence"])
            if record is not None and entry["lemma"] != record.lemma:
                _fail(
                    report,
                    codes.LEMMA_MISMATCH,
                    f"incidental entry {entry['evidence']} has lemma {entry['lemma']!r}, "
                    f"the word store records {record.lemma!r} (rule 7)",
                    lesson=n,
                )
        for step in lesson["steps"]:
            paradigm = step.get("paradigm")
            if paradigm is None:
                continue
            record = store.records.get(paradigm["word"])
            if record is None:
                continue
            for tag in paradigm["forms"]:
                if tag not in record.form_tags:
                    _fail(
                        report,
                        codes.UNKNOWN_FORM_TAG,
                        f"paradigm {paradigm['id']} cites form tag {tag!r} of {paradigm['word']}, "
                        "which the word-store record does not list (rule 7, r9)",
                        lesson=n,
                        step=step["id"],
                    )


def _word_ids_in_plan(plan: dict) -> list[tuple[int, str | None, str]]:
    """Every W-… id the plan cites, with its lesson number and step id (rule 3)."""
    found: list[tuple[int, str | None, str]] = []
    for lesson in plan["lessons"]:
        n = lesson["n"]
        vocabulary = lesson["inventory"]["vocabulary"]
        found += [(n, None, entry["evidence"]) for entry in vocabulary["core"]]
        found += [(n, None, entry["evidence"]) for entry in vocabulary["incidental"]]
        found += [(n, None, item) for item in vocabulary["recycled"]]
        for step in lesson["steps"]:
            introduces = step.get("introduces") or {}
            uses = step.get("uses") or {}
            found += [(n, step["id"], item) for item in introduces.get("vocabulary") or []]
            found += [(n, step["id"], item) for item in uses.get("vocabulary") or []]
            if step.get("paradigm"):
                found.append((n, step["id"], step["paradigm"]["word"]))
        practice = lesson.get("practice") or {}
        found += [(n, None, item) for item in practice.get("stress") or []]
        dialogue = lesson.get("dialogue")
        if dialogue is not None:
            found += [
                (n, None, speaker["evidence"]) for speaker in dialogue.get("speakers") or [] if "evidence" in speaker
            ]
            found += [(n, None, place["evidence"]) for place in dialogue.get("places") or []]
    return found


def _pack_ids_in_plan(plan: dict) -> list[tuple[int, str | None, str]]:
    """Every non-W-… evidence id the plan cites, with its lesson number and step id (rule 3)."""
    found: list[tuple[int, str | None, str]] = []
    for lesson in plan["lessons"]:
        n = lesson["n"]
        for entry in lesson["inventory"].get("grammar") or []:
            found += [(n, None, item) for item in entry["evidence"]]
        for step in lesson["steps"]:
            found += [(n, step["id"], item) for item in step.get("evidence") or []]
        for activity in lesson.get("activities") or []:
            if "model" in activity:
                found.append((n, None, activity["model"]))
            found += [(n, None, item) for item in activity.get("error_refs") or []]
        for video in lesson.get("videos") or []:
            found.append((n, None, video["evidence"]))
        dialogue = lesson.get("dialogue")
        if dialogue is not None:
            found += [(n, None, item) for item in dialogue.get("evidence") or []]
    return found


def _check_error_ref_records(report: Report, plan: dict, pack) -> None:
    """error_refs resolve to E- error records of the pack, not any pack id (r9)."""
    for lesson in plan["lessons"]:
        for activity in lesson.get("activities") or []:
            for item in activity.get("error_refs") or []:
                if item in pack.ids and item not in pack.error_ids:
                    _fail(
                        report,
                        codes.ERROR_REF_NOT_ERROR_RECORD,
                        f"activity {activity['id']} cites {item} in error_refs, but {item} is not an "
                        "E- error record of the module pack (r9)",
                        lesson=lesson["n"],
                    )


def _schema_location(plan: dict, path) -> tuple[int | None, str | None]:
    """The lesson n and step id a schema error path points into, when it does."""
    lesson_no: int | None = None
    step_id: str | None = None
    parts = list(path)
    lessons = plan.get("lessons")
    if not (
        len(parts) >= 2
        and parts[0] == "lessons"
        and isinstance(parts[1], int)
        and isinstance(lessons, list)
        and 0 <= parts[1] < len(lessons)
        and isinstance(lessons[parts[1]], dict)
    ):
        return lesson_no, step_id
    lesson = lessons[parts[1]]
    n = lesson.get("n")
    lesson_no = n if isinstance(n, int) else None
    steps = lesson.get("steps")
    if (
        len(parts) >= 4
        and parts[2] == "steps"
        and isinstance(parts[3], int)
        and isinstance(steps, list)
        and 0 <= parts[3] < len(steps)
        and isinstance(steps[parts[3]], dict)
    ):
        candidate = steps[parts[3]].get("id")
        step_id = candidate if isinstance(candidate, str) else None
    return lesson_no, step_id


def _declared_pack_path(root: Path, declared: str) -> Path:
    """Resolve evidence_ref.path against the plan's curriculum/l2-uk-en root.

    The declared reference — not the conventional <slug>.yaml name — identifies
    the pack that gets checked (rule 3). A curriculum/l2-uk-en/ prefix is
    accepted; a path escaping the root fails closed as PACK_NOT_FOUND.
    """
    relative = declared.removeprefix("curriculum/l2-uk-en/")
    resolved = (root / relative).resolve()
    if resolved != root.resolve() and root.resolve() not in resolved.parents:
        raise PlanError(
            codes.PACK_NOT_FOUND,
            f"evidence_ref.path {declared!r} resolves to {resolved}, outside {root}",
        )
    return resolved


def validate_plan(
    level: str,
    slug: str,
    *,
    plan_path: Path | None = None,
    pack_path: Path | None = None,
    words_path: Path | None = None,
    activity_schema_path: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
    write_scope: bool = False,
) -> Report:
    """Validate one module plan: the complete §6 gate of §2/§2a.

    path overrides exist for tests; the lesson-plans/ root rule applies to
    plan_path regardless, and a pack_path override must match the plan's
    evidence_ref.path (rule 3). activity_schema_path overrides the activity allowlist
    schema (tests only; never a fallback level). allow_missing_prior turns exactly
    the missing-prior-plans failure into a printed waiver; strict refuses waiver
    flags (the CLI enforces that) and verifies the grammar registry is append-only
    over git history; write_scope regenerates the scope sidecar instead of checking
    it. Never raises for plan content problems — they come back as failures in the
    Report.
    """
    report = Report(level=level, slug=slug)
    _always_not_checked(report)
    try:
        plan_path = resolve_plan_path(level, slug, plan_path)
        plan_text = read_plan_text(plan_path)
        plan = load_plan(plan_path)
        check_plan_slug(plan_path, slug, plan)
    except PlanError as error:
        _fail(report, error.code, error.message)
        report.not_checked.append(title_quantities_outcome(None))
        return report

    report.not_checked.append(title_quantities_outcome(plan))
    root = evidence_root(plan_path)
    words_path = words_path or root / f"evidence/{level}/_words.yaml"

    _check_stress_marks(report, plan_text)

    schema = json.loads((REPO_ROOT / PLAN_SCHEMA_PATH).read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(plan), key=str)
    if errors:
        for error in errors:
            where = "/".join(str(p) for p in error.absolute_path) or "<root>"
            lesson_no, step_id = _schema_location(plan, error.absolute_path)
            _fail(
                report,
                codes.SCHEMA_VIOLATION,
                f"the plan fails {PLAN_SCHEMA_PATH} at {where}: {error.message}",
                lesson=lesson_no,
                step=step_id,
            )
        return report

    pack = None
    store = None
    try:
        declared_pack = _declared_pack_path(root, plan["evidence_ref"]["path"])
        if pack_path is None:
            pack_path = declared_pack
        elif pack_path.resolve() != declared_pack:
            raise PlanError(
                codes.PACK_PATH_MISMATCH,
                f"pack override {pack_path} does not match evidence_ref.path "
                f"{plan['evidence_ref']['path']!r}, which resolves to {declared_pack}; "
                "the declared path must identify the checked pack (rule 3)",
            )
        pack = load_pack(pack_path)
        store = load_words(words_path)
    except PlanError as error:
        _fail(report, error.code, error.message)

    if pack is not None and store is not None:
        pack_digest = sha256_of(pack_path)
        try:
            if lock_digest(pack_path, codes.PACK_LOCK_MISMATCH) != pack_digest:
                _fail(report, codes.PACK_LOCK_MISMATCH, f"{pack_path} bytes disagree with {pack_path}.lock (rule 3)")
        except PlanError as error:
            _fail(report, error.code, error.message)
        if pack_digest != plan["evidence_ref"]["sha256"]:
            _fail(
                report,
                codes.PACK_HASH_MISMATCH,
                f"{pack_path} sha256 {pack_digest[:12]}… disagrees with evidence_ref.sha256 "
                f"{plan['evidence_ref']['sha256'][:12]}… (rule 3)",
            )
        try:
            if lock_digest(words_path, codes.WORDS_LOCK_MISMATCH) != sha256_of(words_path):
                _fail(report, codes.WORDS_LOCK_MISMATCH, f"{words_path} bytes disagree with {words_path}.lock (rule 3)")
        except PlanError as error:
            _fail(report, error.code, error.message)

    _check_lesson_shape(report, plan)
    _check_inventory_and_order(report, plan)
    _check_cyrillic(report, plan)
    allowlist = _activity_allowlist(report, level, activity_schema_path)
    _check_activities(report, plan, allowlist)
    _check_dialogue_and_needs(report, plan)
    _check_true_false_placement(report, plan)

    if pack is not None and store is not None:
        pack_ids = pack.ids
        for lesson_n, step_id, item in _pack_ids_in_plan(plan):
            if item not in pack_ids:
                _fail(
                    report,
                    codes.UNKNOWN_PACK_ID,
                    f"evidence id {item} does not exist in the module pack {pack_path.name} (rule 3)",
                    lesson=lesson_n,
                    step=step_id,
                )
        _check_error_ref_records(report, plan, pack)
        word_records = store.records
        for lesson_n, step_id, item in _word_ids_in_plan(plan):
            if item not in word_records:
                _fail(
                    report,
                    codes.UNKNOWN_WORD_ID,
                    f"word id {item} does not exist in the level word store {words_path.name} (rule 3)",
                    lesson=lesson_n,
                    step=step_id,
                )
        _check_word_facts(report, plan, store)

    # Cross-plan rules (Brief B): earlier plans and the arc (rules 4 and 5),
    # the grammar registry, the scope sidecar and the module title.
    check_rule4(report, plan, plan_path, allow_missing_prior=allow_missing_prior)
    check_arc(report, level, plan, plan_path)
    registry_path = registry_path_for(plan_path)
    registry_failures: list[Outcome] = []
    registry = load_registry(registry_path, level, registry_failures)
    report.failures.extend(registry_failures)
    check_plan_against_registry(report, plan, plan_path, registry)
    if strict and registry is not None:
        check_append_only(report, registry_path, registry[0])
    scope_letters = check_scope_sidecar(report, plan, plan_path, write=write_scope)
    check_title(report, plan, scope_letters)
    return report


def validate_level(
    level: str,
    *,
    level_dir: Path | None = None,
    allow_missing_prior: bool = False,
    strict: bool = False,
    write_scope: bool = False,
) -> list[Report]:
    """Whole-level mode: every plan of the level, in position order (§6).

    level_dir overrides the level directory (tests only; production runs use
    the conventional curriculum/l2-uk-en/lesson-plans/<level>/).
    """
    level_dir = level_dir or REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}"
    plans = load_level_plans(level_dir)
    reports = [
        validate_plan(
            level,
            plan_slug,
            plan_path=path,
            allow_missing_prior=allow_missing_prior,
            strict=strict,
            write_scope=write_scope,
        )
        for _position, (plan_slug, _plan, path) in sorted(plans.by_position.items())
    ]
    if plans.failures and not reports:
        # No plan could be ordered at all; surface the level-directory failures.
        report = Report(level=level, slug="<level>")
        report.failures.extend(plans.failures)
        reports.append(report)
    return reports


def _report_exit_code(report: Report) -> int:
    if report.failures:
        return 1
    return 3 if report.waivers else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plan-validate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Validate a module plan (plan_schema: 2): the complete plan-validate gate of\n"
            "docs/epics/fresh-build-plan-schema.md §6 — §2 rules 1–7 with the semantics of\n"
            "§2a. One plan is checked against its evidence pack and the level word store,\n"
            "against every plan at an earlier arc position (rule 4), against the level arc\n"
            "(rule 5), against the level grammar registry, and against its own generated\n"
            "scope sidecar and its module title. Do NOT use for v1 plans under plans/\n"
            "(they are rejected).\n"
            "\n"
            "Waivers: --allow-missing-prior turns exactly the missing-earlier-plans failure\n"
            "into the printed, machine-readable waiver 'waived: prior_plans_missing' (with\n"
            "the positions), for pilots written out of order. A waived run is never clean:\n"
            "the summary line and --json say 'waived' and the exit code is 3, and an id that\n"
            "cannot be found in the plans that do exist is not_checked, never a pass.\n"
            "--strict refuses every waiver flag (exit 2) and additionally verifies that the\n"
            "grammar registry is append-only against git merge-base HEAD origin/main — the\n"
            "build preflight and CI run --strict, so a plan that needs a waiver can never be\n"
            "built or merged as buildable.\n"
            "\n"
            "The title check: a run of two or more enumerated single letters in the module's\n"
            "title or subtitle must equal the scope letter list. 'A run of enumerated single\n"
            "letters' is a maximal sequence of two or more tokens, each exactly one UPPERCASE\n"
            "Cyrillic letter, separated only by commas, semicolons or whitespace. One letter\n"
            "alone is not a run, and a lowercase one-letter Ukrainian word (я, і, у, в, а, о)\n"
            "inside a sentence is never an enumeration. ASCII digits are never parsed; they\n"
            "are quoted in not_checked: title_quantities_not_parsed."
        ),
        epilog=(
            "Inputs:\n"
            "  curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml     the plan (schema v2)\n"
            "  curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml       the generated level arc\n"
            "  curriculum/l2-uk-en/lesson-plans/<level>/_grammar.yaml   the grammar registry\n"
            "  curriculum/l2-uk-en/lesson-plans/<level>/_scope/<slug>.yaml  the scope sidecar\n"
            "  curriculum/l2-uk-en/evidence/<level>/<slug>.yaml(.lock)  the module pack\n"
            "  curriculum/l2-uk-en/evidence/<level>/_words.yaml(.lock)  the word store\n"
            "  schemas/module-plan-v2.schema.json, schemas/activities-<level>.schema.json\n"
            "Outputs: stdout only; read-only unless --write-scope is given. The scope sidecar\n"
            "is deterministic (fixed key order, UTF-8, trailing newline); --write-scope\n"
            "creates it with mode 0600 and a created _scope directory with mode 0700 — no\n"
            "group-write or world bits.\n"
            "Exit codes: 0 = clean pass; 1 = failures; 2 = usage error, including --strict\n"
            "given together with a waiver flag; 3 = waived (no failures, but a waiver was\n"
            "used — never a clean pass). not_checked items never fail the run.\n"
            "Examples:\n"
            "  .venv/bin/python -m scripts.curriculum.validate a1 sounds-letters-and-hello\n"
            "  .venv/bin/python -m scripts.curriculum.validate a1 sounds-letters-and-hello --json\n"
            "  .venv/bin/python -m scripts.curriculum.validate a1 --all --strict   (CI)\n"
            "  .venv/bin/python -m scripts.curriculum.validate a1 mod-two --allow-missing-prior\n"
            "  .venv/bin/python -m scripts.curriculum.validate a1 mod-two --write-scope\n"
            "Related: docs/epics/fresh-build-plan-schema.md §2/§2a/§6; issues #8412, #8397.\n"
            "Outcome codes:\n" + codes.help_text()
        ),
    )
    parser.add_argument("level", help="level directory under lesson-plans/, e.g. a1")
    parser.add_argument("slug", nargs="?", default=None, help="module slug; the plan file is <slug>.yaml")
    parser.add_argument("--all", action="store_true", help="validate every plan of the level in position order")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse every waiver flag and verify the grammar registry is append-only against "
        "git merge-base HEAD origin/main (the build preflight and CI mode)",
    )
    parser.add_argument(
        "--allow-missing-prior",
        action="store_true",
        help="waiver: turn the missing-earlier-plans failure into the printed waiver "
        "'waived: prior_plans_missing'; a waived run exits 3, never clean",
    )
    parser.add_argument(
        "--write-scope",
        action="store_true",
        help="write the generated scope sidecar _scope/<slug>.yaml instead of checking it byte for byte",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=None,
        help="plan path override (tests); the lesson-plans/<level>/ root rule still applies",
    )
    parser.add_argument(
        "--pack",
        type=Path,
        default=None,
        help="pack path override (tests); must match the plan's evidence_ref.path",
    )
    parser.add_argument("--words", type=Path, default=None, help="word store path override (tests)")
    parser.add_argument(
        "--level-dir",
        type=Path,
        default=None,
        help="level directory override for --all (tests); default curriculum/l2-uk-en/lesson-plans/<level>/",
    )
    parser.add_argument("--json", action="store_true", help="print the machine-readable report instead of text")
    args = parser.parse_args(argv)

    if args.strict and args.allow_missing_prior:
        parser.error(
            "--strict refuses every waiver flag (--allow-missing-prior): a plan that needs a "
            "waiver cannot be built or merged as buildable (§2a)"
        )
    if args.all and args.slug:
        parser.error("--all validates every plan of the level; do not name a slug")
    if not args.all and not args.slug:
        parser.error("a slug is required unless --all is given")

    if args.all:
        reports = validate_level(
            args.level,
            level_dir=args.level_dir,
            allow_missing_prior=args.allow_missing_prior,
            strict=args.strict,
            write_scope=args.write_scope,
        )
        if args.json:
            payload = {
                "level": args.level,
                "status": "pass",
                "plans": [report.to_json() for report in reports],
            }
            if any(report.failures for report in reports):
                payload["status"] = "fail"
            elif any(report.waivers for report in reports):
                payload["status"] = "waived"
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if not reports:
                print(f"level {args.level}: no plans under lesson-plans/{args.level}/")
            for report in reports:
                summary = report.status
                if report.failures:
                    summary += f" ({len(report.failures)} failures)"
                print(f"{report.level}/{report.slug}: {summary}")
            for report in reports:
                if report.status != "pass":
                    print()
                    print(report.render_text())
        if any(report.failures for report in reports):
            return 1
        if any(report.waivers for report in reports):
            return 3
        return 0

    report = validate_plan(
        args.level,
        args.slug,
        plan_path=args.plan,
        pack_path=args.pack,
        words_path=args.words,
        allow_missing_prior=args.allow_missing_prior,
        strict=args.strict,
        write_scope=args.write_scope,
    )
    if args.json:
        print(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    else:
        print(report.render_text())
    return _report_exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
