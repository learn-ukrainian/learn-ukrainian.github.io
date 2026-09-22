"""The cross-plan rules: rule 4 (used means introduced earlier) and rule 5
(the plan matches the arc) — issue #8412, Brief B.

Earlier plans are found by reading every ``<slug>.yaml`` (names beginning with
``_`` skipped) under ``curriculum/l2-uk-en/lesson-plans/<level>/`` and ordering
them by their own ``arc_ref.position`` — the arc is not an input to rule 4.
Two plans claiming one position fail. A sibling that cannot be read fails
closed: its introductions cannot be trusted. ``incidental`` items never count
as introduced (introductions come from steps' ``introduces`` only, which by
design never list incidental words).

Missing earlier plans fail closed: if any position below the plan's own has no
plan file, validation fails listing the missing positions.
``--allow-missing-prior`` turns exactly that failure into the printed,
machine-readable waiver ``waived: prior_plans_missing``; an id that cannot be
found in the plans that do exist then yields ``not_checked:
introduced_earlier_unverified``, never a pass.

Rule 5 is limited to what the arc carries as data (§2a): ``arc_ref`` exists in
``load_arc(level)``, the plan's slug equals the arc slug at that position, and
— only when the arc record has ``letters`` — the union of the lessons'
``phonetics.letters`` equals that list (missing and extra reported separately;
a letter introduced in two lessons fails). On a position without letters,
``phonetics.letters`` and ``introduces.letters`` must be empty everywhere.
Lesson counts are never compared with the arc's estimate, and
``not_checked: arc_has_no_structured_grammar_or_vocabulary`` is always emitted
(by validate.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from ..arc.loader import ArcStaleError, load_arc
from . import codes
from .loader import evidence_root
from .report import Outcome, Report

_INTRO_KINDS = ("letters", "grammar", "vocabulary")


@dataclass
class LevelPlans:
    """Every sibling plan of a level directory, ordered by its own arc_ref.position."""

    # position -> (slug, plan dict, path); first claimant wins, deterministically
    # by file name, so a duplicate position never changes rule 4's answer
    by_position: dict[int, tuple[str, dict, Path]] = field(default_factory=dict)
    failures: list[Outcome] = field(default_factory=list)


def load_level_plans(level_dir: Path) -> LevelPlans:
    """Read every non-underscore ``*.yaml`` of the level directory, leniently.

    Lenient on purpose: a sibling is not being validated, only mined for its
    position and introductions — but a file that yields no usable
    ``arc_ref.position`` fails closed as PRIOR_PLAN_UNREADABLE, because rule 4
    cannot know which positions it covers.
    """
    result = LevelPlans()
    for path in sorted(level_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            result.failures.append(
                Outcome(
                    codes.PRIOR_PLAN_UNREADABLE,
                    f"{path} cannot be read ({error}); earlier introductions cannot be trusted",
                )
            )
            continue
        position = data.get("arc_ref", {}).get("position") if isinstance(data, dict) else None
        slug = data.get("slug") if isinstance(data, dict) else None
        if not isinstance(position, int) or not isinstance(slug, str):
            result.failures.append(
                Outcome(
                    codes.PRIOR_PLAN_UNREADABLE,
                    f"{path} has no usable arc_ref.position or slug; earlier introductions cannot be trusted",
                )
            )
            continue
        if position in result.by_position:
            first = result.by_position[position]
            result.failures.append(
                Outcome(
                    codes.POSITION_CLAIMED_TWICE,
                    f"arc position {position} is claimed by both {first[2].name} and {path.name}",
                )
            )
            continue
        result.by_position[position] = (slug, data, path)
    return result


def collect_introductions(plan: dict) -> dict[str, set[str]]:
    """The ids a plan introduces, from its steps' introduces (incidental never counts)."""
    introduced: dict[str, set[str]] = {kind: set() for kind in _INTRO_KINDS}
    for lesson in plan.get("lessons") or []:
        if not isinstance(lesson, dict):
            continue
        for step in lesson.get("steps") or []:
            if not isinstance(step, dict):
                continue
            introduces = step.get("introduces") or {}
            for kind in _INTRO_KINDS:
                introduced[kind].update(introduces.get(kind) or [])
    return introduced


def check_rule4(
    report: Report,
    plan: dict,
    plan_path: Path,
    *,
    allow_missing_prior: bool,
    level_plans: LevelPlans | None = None,
) -> None:
    """Rule 4: every used or recycled id was introduced in an earlier lesson of this
    plan or in the plan of an earlier arc position (§2a)."""
    level_plans = level_plans if level_plans is not None else load_level_plans(plan_path.parent)
    report.failures.extend(level_plans.failures)

    position = plan["arc_ref"]["position"]
    present_prior = sorted(p for p in level_plans.by_position if p < position)
    missing = [p for p in range(1, position) if p not in level_plans.by_position]
    waived = False
    if missing:
        message = f"missing positions: {', '.join(map(str, missing))}"
        if allow_missing_prior:
            report.waivers.append(Outcome(codes.WAIVER_PRIOR_PLANS_MISSING, message))
            waived = True
        else:
            report.failures.append(
                Outcome(
                    codes.PRIOR_PLANS_MISSING,
                    f"positions below {position} have no plan file ({message}); rule 4 fails closed — "
                    "write the earlier plans, or re-run with --allow-missing-prior for an explicit waiver (§2a)",
                )
            )

    prior_introduced: dict[str, set[str]] = {kind: set() for kind in _INTRO_KINDS}
    for prior_position in present_prior:
        _slug, prior_plan, _path = level_plans.by_position[prior_position]
        for kind, ids in collect_introductions(prior_plan).items():
            prior_introduced[kind].update(ids)

    def unverifiable(item: str, lesson_n: int, step_id: str | None, what: str) -> None:
        report.not_checked.append(
            Outcome(
                codes.INTRODUCED_EARLIER_UNVERIFIED,
                f"{what} id {item} is introduced in no plan that exists; earlier positions are "
                "missing under a waiver, so introduction cannot be verified (never a pass) (§2a)",
                lesson=lesson_n,
                step=step_id,
            )
        )

    def unknown(item: str, kind: str, lesson_n: int, step_id: str | None, what: str) -> None:
        report.failures.append(
            Outcome(
                codes.USED_NOT_INTRODUCED_EARLIER,
                f"{what} {kind} id {item} was introduced in no earlier lesson of this plan and in "
                "no plan of an earlier arc position (rule 4)",
                lesson=lesson_n,
                step=step_id,
            )
        )

    earlier_lessons: dict[str, set[str]] = {kind: set() for kind in _INTRO_KINDS}
    for lesson in plan["lessons"]:
        n = lesson["n"]
        lesson_introduced = collect_introductions({"lessons": [lesson]})
        for step in lesson["steps"]:
            uses = step.get("uses") or {}
            for kind in ("grammar", "vocabulary"):
                for item in uses.get(kind) or []:
                    if item in lesson_introduced[kind]:
                        continue  # introduced by this lesson; within-lesson order is rule 4's single-plan part
                    if item in earlier_lessons[kind] or item in prior_introduced[kind]:
                        continue
                    if waived:
                        unverifiable(item, n, step["id"], "used")
                    else:
                        unknown(item, kind, n, step["id"], "used")
        for item in lesson["inventory"]["vocabulary"]["recycled"]:
            if item in lesson_introduced["vocabulary"]:
                continue  # recycled_introduced_here (single-plan check) already fails this
            if item in earlier_lessons["vocabulary"] or item in prior_introduced["vocabulary"]:
                continue
            if waived:
                unverifiable(item, n, None, "recycled")
            else:
                unknown(item, "vocabulary", n, None, "recycled")
        for kind in _INTRO_KINDS:
            earlier_lessons[kind].update(lesson_introduced[kind])


def check_arc(report: Report, level: str, plan: dict, plan_path: Path) -> None:
    """Rule 5: arc_ref exists in the arc, the slug matches, and the letters agree —
    limited to what the arc carries as data (§2a)."""
    arc_path = plan_path.parent / "_arc.yaml"
    if not arc_path.is_file():
        report.failures.append(
            Outcome(
                codes.ARC_UNAVAILABLE,
                f"{arc_path} does not exist; rule 5 needs the generated level arc "
                "(scripts/curriculum/arc/generate_arc.py --write)",
            )
        )
        return
    try:
        source_rel = (yaml.safe_load(arc_path.read_text(encoding="utf-8")) or {}).get("source", {}).get("path")
    except yaml.YAMLError:
        source_rel = None
    repo_root = evidence_root(plan_path).parent.parent
    doc_path = repo_root / source_rel if isinstance(source_rel, str) else None
    try:
        arc = load_arc(level, arc_path=arc_path, doc_path=doc_path)
    except (OSError, ValueError, ArcStaleError) as error:
        report.failures.append(Outcome(codes.ARC_UNAVAILABLE, f"{arc_path}: {error}"))
        return

    arc_ref = plan["arc_ref"]
    if arc_ref["level"] != level:
        report.failures.append(
            Outcome(
                codes.ARC_REF_UNKNOWN,
                f"arc_ref.level is {arc_ref['level']!r} but the plan is validated as level {level!r} (rule 5)",
            )
        )
        return
    record = next((entry for entry in arc if entry.position == arc_ref["position"]), None)
    if record is None:
        report.failures.append(
            Outcome(
                codes.ARC_REF_UNKNOWN,
                f"arc position {arc_ref['position']} does not exist in {arc_path} "
                f"(the arc has positions 1..{max(e.position for e in arc)}) (rule 5)",
            )
        )
        return
    if plan["slug"] != record.slug:
        report.failures.append(
            Outcome(
                codes.ARC_SLUG_MISMATCH,
                f"the plan's slug {plan['slug']!r} differs from the arc slug at position "
                f"{record.position}, {record.slug!r} (rule 5)",
            )
        )

    letters_by_lesson: list[tuple[int, list[str]]] = []
    for lesson in plan["lessons"]:
        letters = list((lesson["inventory"].get("phonetics") or {}).get("letters") or [])
        if letters:
            letters_by_lesson.append((lesson["n"], letters))
    taught = [letter for _n, letters in letters_by_lesson for letter in letters]

    if record.letters is None:
        step_letters = [
            (lesson["n"], step["id"], letter)
            for lesson in plan["lessons"]
            for step in lesson["steps"]
            for letter in (step.get("introduces") or {}).get("letters") or []
        ]
        if letters_by_lesson or step_letters:
            detail = []
            if letters_by_lesson:
                detail.append(
                    "phonetics.letters in lessons "
                    + ", ".join(f"{n} ({' '.join(letters)})" for n, letters in letters_by_lesson)
                )
            if step_letters:
                detail.append(
                    "introduces.letters in steps "
                    + ", ".join(f"{n}/{step} ({letter})" for n, step, letter in step_letters)
                )
            report.failures.append(
                Outcome(
                    codes.LETTERS_IN_NON_LITERACY_PLAN,
                    f"arc position {record.position} ({record.slug}) carries no letters, so the plan "
                    "introduces no letters; found " + "; ".join(detail) + " (rule 5)",
                )
            )
        return

    seen: dict[str, int] = {}
    for n, letters in letters_by_lesson:
        for letter in letters:
            if letter in seen:
                report.failures.append(
                    Outcome(
                        codes.LETTER_INTRODUCED_TWICE,
                        f"letter {letter} is introduced by both lesson {seen[letter]} and lesson {n} (rule 5)",
                        lesson=n,
                    )
                )
            else:
                seen[letter] = n
    arc_letters = set(record.letters)
    taught_set = set(taught)
    missing = sorted(arc_letters - taught_set)
    extra = sorted(taught_set - arc_letters)
    if missing:
        report.failures.append(
            Outcome(
                codes.ARC_LETTERS_MISMATCH,
                f"letters the arc assigns to position {record.position} but no lesson teaches "
                f"(missing): {' '.join(missing)} (rule 5)",
            )
        )
    if extra:
        report.failures.append(
            Outcome(
                codes.ARC_LETTERS_MISMATCH,
                f"letters the lessons teach that the arc does not assign to position "
                f"{record.position} (extra): {' '.join(extra)} (rule 5)",
            )
        )
