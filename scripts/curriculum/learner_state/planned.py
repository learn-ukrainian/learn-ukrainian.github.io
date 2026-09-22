"""Planned learner state at lesson grain (docs/epics/fresh-build-plan-schema.md §4, #8414).

Planned state is available at plan time, used by plan-validate and as the writer's
allowlist:
- base_ids: project-wide base layer of closed-class function words (W- ids)
- core_ids: every vocabulary.core[].evidence id of earlier plans plus core ids of
  lessons 1..lesson_n-1 of this plan, each with (position, lesson) introduced at
- grammar_ids and letters: accumulated the same way
- name_ids: speaker and place ids from every earlier plan and this plan's dialogues
  of lessons 1..lesson_n (same scope as core_ids; admitted for use, never counted as vocab)
- cumulative_core_count = len(core_ids) — base layer and names excluded from count
- incidental ids never enter state
- Rule 1: Planned state is ids, never lemmas. A bare lemma anywhere is a failure (bare_lemma).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.curriculum.validate.loader import PlanError, load_plan

from . import codes
from .base_layer import BaseLayerError, resolve_base_ids

REPO_ROOT = Path(__file__).resolve().parents[3]


class PlannedStateError(Exception):
    """Failure outcome in planned state calculation."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PlannedState:
    """Deterministic planned learner state for a specific lesson position."""

    level: str
    position: int
    lesson_n: int
    base_ids: tuple[str, ...]
    core_ids: dict[str, dict[str, int]]
    grammar_ids: dict[str, dict[str, int]]
    letters: dict[str, dict[str, int]]
    name_ids: dict[str, dict[str, int]]
    cumulative_core_count: int
    waiver: str | None = None

    @property
    def all_allowed_ids(self) -> frozenset[str]:
        """All word-store IDs allowed for natural Ukrainian in this lesson."""
        return frozenset(self.base_ids) | frozenset(self.core_ids.keys()) | frozenset(self.name_ids.keys())

    def to_dict(self) -> dict[str, Any]:
        """Machine-readable dictionary representation."""
        result: dict[str, Any] = {
            "level": self.level,
            "position": self.position,
            "lesson_n": self.lesson_n,
            "cumulative_core_count": self.cumulative_core_count,
            "base_ids": list(self.base_ids),
            "core_ids": self.core_ids,
            "grammar_ids": self.grammar_ids,
            "letters": self.letters,
            "name_ids": self.name_ids,
        }
        if self.waiver:
            result["waiver"] = self.waiver
        return result

    def render_text(self) -> str:
        """Human-readable text summary."""
        lines = [
            f"Planned learner state: level={self.level}, position={self.position}, lesson={self.lesson_n}",
            f"Cumulative core vocabulary count: {self.cumulative_core_count}",
            f"Base layer IDs: {len(self.base_ids)}",
            f"Core vocabulary IDs: {len(self.core_ids)}",
            f"Grammar IDs: {len(self.grammar_ids)}",
            f"Letters: {len(self.letters)}",
            f"Name IDs: {len(self.name_ids)}",
        ]
        if self.waiver:
            lines.append(f"Waiver: {self.waiver}")
        return "\n".join(lines)


def _validate_id(identifier: Any, context: str) -> str:
    """Rule 1: verify that an identifier is a word-store ID (W-...), not a bare lemma."""
    if not isinstance(identifier, str) or not identifier.startswith("W-"):
        raise PlannedStateError(
            codes.BARE_LEMMA,
            f"bare lemma or invalid ID {identifier!r} found in {context}; planned state requires IDs (rule 1)",
        )
    return identifier


def planned_state(
    level: str,
    position: int,
    lesson_n: int,
    *,
    allow_missing_prior: bool = False,
    strict: bool = False,
    plans_dir: Path | None = None,
    evidence_dir: Path | None = None,
    words_path: Path | None = None,
    base_request_path: Path | None = None,
) -> PlannedState:
    """Compute planned learner state at (level, position, lesson_n).

    Reads plans through scripts.curriculum.validate.loader, discovers plans in
    lesson-plans/<level>/ (skipping names starting with _), joins base layer from
    evidence/<level>/_base.request.yaml and _words.yaml, and accumulates core vocab,
    grammar, letters, and dialogue names.
    """
    plans_root = plans_dir or (REPO_ROOT / f"curriculum/l2-uk-en/lesson-plans/{level}")
    evidence_root = evidence_dir or (REPO_ROOT / f"curriculum/l2-uk-en/evidence/{level}")

    if not plans_root.is_dir():
        raise PlannedStateError(
            codes.PLAN_NOT_FOUND,
            f"plans directory does not exist: {plans_root}",
        )

    # 1. Resolve base layer IDs
    try:
        base_ids = resolve_base_ids(
            level,
            evidence_dir=evidence_root,
            words_path=words_path,
            base_request_path=base_request_path,
        )
    except BaseLayerError as err:
        raise PlannedStateError(err.code, err.message) from err

    # 2. Discover and load all module plans in level
    plans_by_position: dict[int, dict[str, Any]] = {}
    plan_files = sorted(p for p in plans_root.glob("*.yaml") if not p.name.startswith("_"))

    for p_path in plan_files:
        try:
            data = load_plan(p_path)
        except PlanError as err:
            raise PlannedStateError(err.code, err.message) from err
        except Exception as err:
            raise PlannedStateError(
                codes.PLAN_YAML_INVALID,
                f"plan file {p_path} failed loading: {err}",
            ) from err

        arc_ref = data.get("arc_ref")
        if not isinstance(arc_ref, dict) or "position" not in arc_ref:
            raise PlannedStateError(
                codes.PLAN_YAML_INVALID,
                f"plan file {p_path} missing arc_ref.position",
            )
        pos = arc_ref["position"]
        if pos in plans_by_position:
            raise PlannedStateError(
                codes.PLAN_YAML_INVALID,
                f"duplicate plan for arc position {pos}: {p_path.name} and previous",
            )
        plans_by_position[pos] = data

    # 3. Check target position existence
    if position not in plans_by_position:
        raise PlannedStateError(
            codes.PLAN_NOT_FOUND,
            f"no plan found for level {level} at arc position {position}",
        )
    current_plan = plans_by_position[position]

    # 4. Check prior positions (1..position-1)
    missing_prior = [p for p in range(1, position) if p not in plans_by_position]
    waiver: str | None = None
    if missing_prior:
        if strict:
            raise PlannedStateError(
                codes.PRIOR_PLANS_MISSING,
                f"missing prior plan(s) for position(s) {missing_prior}; --strict refuses waiver",
            )
        if allow_missing_prior:
            waiver = f"waived: {codes.PRIOR_PLANS_MISSING} (missing positions: {missing_prior})"
        else:
            raise PlannedStateError(
                codes.PRIOR_PLANS_MISSING,
                f"missing prior plan(s) for position(s) {missing_prior}; use --allow-missing-prior to waive",
            )

    # 5. Check target lesson existence
    lessons = current_plan.get("lessons", [])
    if not any(isinstance(l, dict) and l.get("n") == lesson_n for l in lessons):
        raise PlannedStateError(
            codes.LESSON_NOT_FOUND,
            f"lesson {lesson_n} not found in plan at arc position {position}",
        )

    # 6. Accumulate state
    core_ids: dict[str, dict[str, int]] = {}
    grammar_ids: dict[str, dict[str, int]] = {}
    letters: dict[str, dict[str, int]] = {}
    name_ids: dict[str, dict[str, int]] = {}

    # Sort available positions
    sorted_positions = sorted(p for p in plans_by_position if p <= position)

    for pos in sorted_positions:
        plan = plans_by_position[pos]
        for lesson in plan.get("lessons", []):
            if not isinstance(lesson, dict):
                continue
            l_n = lesson.get("n")
            if l_n is None:
                continue

            inv = lesson.get("inventory") or {}

            # Core vocabulary, grammar, letters:
            # - For pos < position: all lessons
            # - For pos == position: lessons 1..lesson_n-1
            is_prior_vocab = (pos < position) or (pos == position and l_n < lesson_n)
            if is_prior_vocab:
                # Core vocabulary (rule 1: ids only; rule 2: incidental never enters)
                vocab = inv.get("vocabulary") or {}
                for item in vocab.get("core", []):
                    if not isinstance(item, dict):
                        continue
                    wid = item.get("evidence")
                    _validate_id(wid, f"position {pos} lesson {l_n} core vocabulary")
                    if wid not in core_ids:
                        core_ids[str(wid)] = {"position": pos, "lesson": l_n}

                # Grammar
                for g in inv.get("grammar", []):
                    if isinstance(g, dict) and "id" in g:
                        gid = str(g["id"])
                        if gid not in grammar_ids:
                            grammar_ids[gid] = {"position": pos, "lesson": l_n}

                # Letters
                phonetics = inv.get("phonetics") or {}
                for ch in phonetics.get("letters", []):
                    if ch and ch not in letters:
                        letters[str(ch)] = {"position": pos, "lesson": l_n}

            # Name IDs (speaker and place ids):
            # - For pos < position: all lessons
            # - For pos == position: lessons 1..lesson_n (same scope as core_ids; admitted for use)
            is_prior_or_current_name = (pos < position) or (pos == position and l_n <= lesson_n)
            if is_prior_or_current_name:
                dial = lesson.get("dialogue") or {}
                for spk in dial.get("speakers", []):
                    if isinstance(spk, dict) and "evidence" in spk:
                        nid = spk["evidence"]
                        _validate_id(nid, f"position {pos} lesson {l_n} dialogue speaker")
                        if nid not in name_ids:
                            name_ids[str(nid)] = {"position": pos, "lesson": l_n}
                for plc in dial.get("places", []):
                    if isinstance(plc, dict) and "evidence" in plc:
                        nid = plc["evidence"]
                        _validate_id(nid, f"position {pos} lesson {l_n} dialogue place")
                        if nid not in name_ids:
                            name_ids[str(nid)] = {"position": pos, "lesson": l_n}

    # Determinism: sort dict keys
    core_ids = dict(sorted(core_ids.items()))
    grammar_ids = dict(sorted(grammar_ids.items()))
    letters = dict(sorted(letters.items()))
    name_ids = dict(sorted(name_ids.items()))

    # cumulative_core_count = len(core_ids) — base layer and names excluded
    cumulative_core_count = len(core_ids)

    return PlannedState(
        level=level,
        position=position,
        lesson_n=lesson_n,
        base_ids=base_ids,
        core_ids=core_ids,
        grammar_ids=grammar_ids,
        letters=letters,
        name_ids=name_ids,
        cumulative_core_count=cumulative_core_count,
        waiver=waiver,
    )
