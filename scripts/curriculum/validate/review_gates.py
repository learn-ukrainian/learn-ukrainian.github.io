"""Plan gates for the defects plan reviewers marked checkable (issue #9487).

The first full-access plan reviews of A1 positions 1 and 2 recorded findings
that a script can decide; each cost a review round. These gates decide them
from data the validator already reads — the plan, the module pack's video
models, the level word store, the arc and the earlier plans — so a plan with
the defect fails before a reviewer is spent.

  C1  a word id named in a dialogue's target_grammar, or in the focus of an activity in a
      step's practice, is introduced at or before that step (failure)
  C2  two or more activities of one lesson carry the same focus text (failure)
  C3  a listening activity whose cited videos model exactly one target, so every item has
      the same key (failure)
  C4  in a letter-stage module, an incidental word none of whose word-store spellings can be
      read with the letters taught through its lesson (failure); a lemma that cannot be read
      while another of its forms can is a note
  C5  a teach-text clause that says a word id is heard, in a step citing no video whose
      models.words lists it (note)
  C6  core records of earlier positions that no recycled list of the module names (note)

Check 7 of #9487 is a learner-state fix (scripts/curriculum/learner_state/planned.py).

How exact each gate is:

- C1 reads word ids (``W-<digits>``), never prose. The step a dialogue is presented in is
  ``dialogue.step``; the activities a step scores are its ``practice`` list. An id that a
  later step of the same lesson introduces fails; so does an id that no step up to this one
  introduces and that is outside the lesson's allowed set (earlier lessons and positions,
  the base layer, the lesson's incidental, recycled and dialogue-name records).
- C2 compares focus text after collapsing whitespace.
- C3 applies to an activity whose focus declares its item kind as ``kind: listening``.
  The keys such an activity can have are the targets its cited videos model
  (``models.letters`` and ``models.words`` in the pack; descriptions never establish
  models). One target in all means one key for every item. A cited video without models
  leaves the targets unknown, so the gate does not decide.
- C4 applies where the arc position carries letters (the rule 5 definition of a letter-stage
  module) and from the first lesson that has a taught letter; before it nothing is read,
  so every word is heard. The letters of a word are its Cyrillic letters; an apostrophe is
  not a letter. Incidental entries carry no forms, so the plan does not say which form is
  used: the gate fails only when no spelling of the record is readable.
- C5 is a note because "heard" is read from prose: a clause (split at punctuation and at
  then/before/after) that holds a hearing word (hear, heard, listen, …) and a word id. A
  clause such as "hear Т before reading W-101" would be misread, so a person confirms it;
  making it a failure needs a structured field, which is a plan-schema change.
- C6 is a note by design (#9487): recycling is a pedagogical choice the review makes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..arc.loader import ArcPosition
from . import codes
from .cross import LevelPlans
from .mechanical import Gates
from .pack import Pack, WordStore
from .report import Outcome, Report
from .scope import CYRILLIC_LETTER_CLASS

_LETTER = re.compile(f"[{CYRILLIC_LETTER_CLASS}]")
_WORD_ID = re.compile(r"\bW-\d+\b")
_VIDEO_ID = re.compile(r"\bV-\d+\b")
_LISTENING_KIND = re.compile(r"\bkind:\s*listening\b")
_CLAUSE_BREAK = re.compile(r"[.;:,!?()]|\b(?:then|before|after)\b", re.IGNORECASE)
_HEARING = re.compile(r"\b(?:hear|hears|heard|hearing|listen|listens|listened|listening)\b", re.IGNORECASE)


def _ids(pattern: re.Pattern[str], text: str) -> list[str]:
    """The ids pattern finds in text, in order, once each."""
    return list(dict.fromkeys(pattern.findall(text or "")))


def _normalized(text: str) -> str:
    return " ".join((text or "").split())


@dataclass
class ReviewGates(Gates):
    pack: Pack = field(kw_only=True)

    def fail(self, code: str, message: str, lesson: int | None, step: str | None = None) -> None:
        self.report.failures.append(Outcome(code, message, lesson, step))

    # -- C1 -------------------------------------------------------------------

    def check_named_before_introduction(self) -> None:
        for index, lesson in enumerate(self.plan["lessons"]):
            steps = lesson["steps"]
            order = {step["id"]: position for position, step in enumerate(steps)}
            introduced_at: dict[str, int] = {}
            for position, step in enumerate(steps):
                for item in (step.get("introduces") or {}).get("vocabulary") or []:
                    introduced_at.setdefault(item, position)
            activities: dict[str, dict] = {}
            for activity in lesson.get("activities") or []:
                activities.setdefault(activity["id"], activity)  # a duplicate id is duplicate_activity_id (rule 6)

            sources: list[tuple[str, int, str]] = []  # (what names the ids, step position, text)
            dialogue = lesson.get("dialogue") or {}
            if dialogue.get("step") in order and dialogue.get("target_grammar"):
                sources.append(
                    (
                        f"the dialogue's target_grammar (dialogue step {dialogue['step']})",
                        order[dialogue["step"]],
                        dialogue["target_grammar"],
                    )
                )
            for position, step in enumerate(steps):
                for activity_id in step.get("practice") or []:
                    if activity_id in activities:
                        sources.append(
                            (
                                f"activity {activity_id} focus (practice of step {step['id']})",
                                position,
                                activities[activity_id]["focus"],
                            )
                        )

            allowed: set[str] | None = None
            for where, position, text in sources:
                later, unknown = [], []
                for item in _ids(_WORD_ID, text):
                    if item in introduced_at:
                        if introduced_at[item] > position:
                            later.append(f"{item} (introduced by step {steps[introduced_at[item]]['id']})")
                        continue
                    if allowed is None:
                        allowed = self.allowed_ids(index, "C1")
                        if allowed is None:
                            return
                    if item not in allowed:
                        unknown.append(item)
                step_id = steps[position]["id"]
                if later:
                    self.fail(
                        codes.NAMED_BEFORE_INTRODUCTION,
                        f"{where} names {', '.join(later)}, which a later step of this lesson introduces; "
                        "a word is introduced at or before the step that presents or scores it (#9487 C1)",
                        lesson["n"],
                        step_id,
                    )
                if unknown:
                    self.fail(
                        codes.NAMED_BEFORE_INTRODUCTION,
                        f"{where} names {', '.join(unknown)}, which no step up to {step_id} introduces and "
                        "which is outside the lesson's allowed set (earlier lessons and positions, base layer, "
                        "incidental, recycled, dialogue names) (#9487 C1)",
                        lesson["n"],
                        step_id,
                    )

    # -- C2 -------------------------------------------------------------------

    def check_duplicate_focus(self) -> None:
        for lesson in self.plan["lessons"]:
            by_focus: dict[str, list[str]] = {}
            for activity in lesson.get("activities") or []:
                by_focus.setdefault(_normalized(activity["focus"]), []).append(activity["id"])
            for focus, activity_ids in by_focus.items():
                if len(activity_ids) > 1:
                    self.fail(
                        codes.DUPLICATE_ACTIVITY_FOCUS,
                        f"activities {', '.join(activity_ids)} carry the same focus text {focus[:80]!r}"
                        f"{'…' if len(focus) > 80 else ''}; each activity states its own operation (#9487 C2)",
                        lesson["n"],
                    )

    # -- C3 -------------------------------------------------------------------

    def check_listening_single_key(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                if not _LISTENING_KIND.search(activity["focus"]):
                    continue
                videos = _ids(_VIDEO_ID, activity["focus"])
                if not videos or any(video not in self.pack.video_models for video in videos):
                    continue  # targets unknown: no cited video, or a cited video without models
                targets = {
                    *(f"letter {letter}" for video in videos for letter in self.pack.video_models[video].letters),
                    *(f"word {word}" for video in videos for word in self.pack.video_models[video].words),
                }
                if len(targets) == 1:
                    self.fail(
                        codes.LISTENING_QUIZ_SINGLE_KEY,
                        f"listening activity {activity['id']} cites {', '.join(videos)}, which together model "
                        f"only {next(iter(targets))}; every item has that one key (#9487 C3)",
                        lesson["n"],
                    )

    # -- C4 -------------------------------------------------------------------

    def check_incidental_decodable(self) -> None:
        lessons = [lesson for lesson in self.plan["lessons"] if lesson["inventory"]["vocabulary"]["incidental"]]
        if not lessons:
            return
        through = self.letter_state_or_skip("C4", True)
        if through is None:
            return  # not a letter-stage module, or its arc is unavailable (skipped above)
        for lesson in lessons:
            taught = through.get(lesson["n"], set())
            if not taught:
                continue  # before the first taught letter nothing is read
            for entry in lesson["inventory"]["vocabulary"]["incidental"]:
                record = self.store.records.get(entry["evidence"])
                spellings = [entry["lemma"], *(record.form_texts if record else ())]
                readable = [text for text in dict.fromkeys(spellings) if self._readable(text, taught)]
                if entry["lemma"] in readable:
                    continue
                untaught = sorted({letter for letter in self._letters(entry["lemma"]) if letter not in taught})
                if not readable:
                    self.fail(
                        codes.INCIDENTAL_NOT_DECODABLE,
                        f"incidental {entry['evidence']} ({entry['lemma']!r}) needs {', '.join(untaught)}, not taught "
                        f"through lesson {lesson['n']}, and no spelling of its word record is readable with the "
                        "taught letters (#9487 C4)",
                        lesson["n"],
                    )
                else:
                    self.note(
                        codes.INCIDENTAL_LEMMA_NOT_DECODABLE,
                        f"incidental lemma {entry['lemma']!r} ({entry['evidence']}) needs {', '.join(untaught)}, not "
                        f"taught through lesson {lesson['n']}; readable forms: {', '.join(readable)}; the plan does "
                        "not bind the form, so the plan review confirms it (#9487 C4)",
                        lesson["n"],
                    )

    @staticmethod
    def _letters(text: str) -> set[str]:
        return {letter.casefold() for letter in _LETTER.findall(text)}

    @classmethod
    def _readable(cls, text: str, taught: set[str]) -> bool:
        return cls._letters(text) <= taught

    # -- C5 -------------------------------------------------------------------

    def check_heard_words(self) -> None:
        for lesson in self.plan["lessons"]:
            for step in lesson["steps"]:
                heard = list(
                    dict.fromkeys(
                        item
                        for clause in _CLAUSE_BREAK.split(step.get("teach") or "")
                        if clause and _HEARING.search(clause)
                        for item in _ids(_WORD_ID, clause)
                    )
                )
                videos = [item for item in step.get("evidence") or [] if item.startswith("V-")]
                modelled = {
                    word
                    for video in videos
                    if video in self.pack.video_models
                    for word in self.pack.video_models[video].words
                }
                missing = [item for item in heard if item not in modelled]
                if missing:
                    self.note(
                        codes.HEARD_WORD_WITHOUT_VIDEO,
                        f"the teach text says {', '.join(missing)} {'is' if len(missing) == 1 else 'are'} heard, "
                        f"but no video the step cites ({', '.join(videos) or 'none'}) lists "
                        f"{'it' if len(missing) == 1 else 'them'} in models.words; the clause is read from prose, "
                        "so the plan review confirms it (#9487 C5)",
                        lesson["n"],
                        step["id"],
                    )

    # -- C6 -------------------------------------------------------------------

    def check_earlier_core_recycled(self) -> None:
        position = self.plan["arc_ref"]["position"]
        if position <= 1:
            return
        missing = [p for p in range(1, position) if p not in self.level_plans.by_position]
        if missing:
            self.skip("C6", "earlier arc positions " + ", ".join(map(str, missing)) + " have no plan file")
            return
        earlier: dict[str, int] = {}
        for prior in range(1, position):
            for lesson in self.level_plans.by_position[prior][1].get("lessons") or []:
                vocabulary = ((lesson or {}).get("inventory") or {}).get("vocabulary") or {}
                for entry in vocabulary.get("core") or []:
                    if isinstance(entry, dict) and isinstance(entry.get("evidence"), str):
                        earlier.setdefault(entry["evidence"], prior)
        recycled = {item for lesson in self.plan["lessons"] for item in lesson["inventory"]["vocabulary"]["recycled"]}
        absent = sorted(set(earlier) - recycled)
        if absent:
            listed = ", ".join(
                f"{item} {self.store.records[item].lemma!r} (position {earlier[item]})"
                if item in self.store.records
                else f"{item} (position {earlier[item]})"
                for item in absent
            )
            self.note(
                codes.EARLIER_CORE_NOT_RECYCLED,
                f"{len(absent)} of {len(earlier)} core records of earlier positions appear in no recycled list "
                f"of this module: {listed} (#9487 C6)",
                None,
            )


def check_review_gates(
    report: Report,
    plan: dict,
    *,
    level: str,
    store: WordStore,
    pack: Pack,
    arc: list[ArcPosition] | None,
    level_plans: LevelPlans,
    words_path: Path,
) -> None:
    """Run gates C1–C6 on a plan that already passed the schema, with its pack and word store loaded."""
    gates = ReviewGates(report, plan, level, store, arc, level_plans, words_path, pack=pack)
    gates.check_named_before_introduction()
    gates.check_duplicate_focus()
    gates.check_listening_single_key()
    gates.check_incidental_decodable()
    gates.check_heard_words()
    gates.check_earlier_core_recycled()
