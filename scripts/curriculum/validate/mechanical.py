"""Mechanical plan gates M1, M3 and M5 (issue #9138).

Three structural plan defects that plan reviewers had to find by hand, each
decided from data the validator already reads — the plan, the level arc, the
level word store — never from a typed list of Ukrainian
facts. The only Ukrainian inventories used are ones the code already owns:
the closed Cyrillic letter class (scope.CYRILLIC_LETTER_CLASS) and the vowel
letters of scripts.practice.euphony_stem_engine (M3's syllable-shaped tokens).

  M1  a step introduces a letter that no activity in its practice names in its focus
  M3  a quoted Ukrainian token in a step's teach text or an activity's focus resolves only to
      records outside the lesson's allowed set
  M5  a core lemma's word-record CEFR level is above the module's level

Severity, per gate. No gate fails the run: each is reported for the plan reviewer,
because the plan contract does not make any of it an invariant of a valid plan:

- M1 (note): a focus can describe practising a letter without printing the glyph.
- M3 (note): a token the plan quotes («…», "…", “…”, '…' or backticks; never unquoted prose) that resolves only to out-of-allowlist records. A token
  that resolves to no store record, or that is spelled like a syllable (one vowel,
  only letters the lesson has taught) and so may be the syllable the plan teaches
  rather than the word it collides with, is not_checked.
- M5 (note): the plan contract sets no CEFR ceiling for core vocabulary.

Dropped under the #9138 residual policy (a rule with another false-positive class goes):
M2 (a step letter with no allowed word record; word-completion practice is not a reliable
signal), M4 (copy-task model letters; a letter-grid is a reference grid, not a copy task),
M6 and M7 (item counts; items are draft fields the plan does not bind) and M8 (core word or
grammar never reused; practice.stress and other drills use words the plan does not bind).

Gate M1 applies to letter-stage
modules only: those whose arc position carries letters (the rule 5 definition).
The taught-letter state at a lesson is the arc's letters of every earlier position
plus the letters this plan introduces through that lesson.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from scripts.practice.euphony_stem_engine import VOWELS as VOWEL_LETTERS

from ..arc.loader import ArcPosition
from . import codes
from .cross import LevelPlans, collect_introductions
from .pack import WordRecord, WordStore
from .report import Outcome, Report
from .scope import CYRILLIC_LETTER_CLASS

CEFR_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")

_LETTER = re.compile(f"[{CYRILLIC_LETTER_CLASS}]")
_TOKEN = re.compile(f"[{CYRILLIC_LETTER_CLASS}]+(?:['’ʼ-][{CYRILLIC_LETTER_CLASS}]+)*")
_QUOTED = re.compile(
    rf"«([^»]*)»|\"([^\"]*)\"|“([^”]*)”|`([^`]*)`"
    rf"|(?<![{CYRILLIC_LETTER_CLASS}])'([^']*)'(?![{CYRILLIC_LETTER_CLASS}])"
)
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'"})


def tokens_of(text: str) -> list[str]:
    """The quoted Ukrainian tokens (two or more letters) of text, case-folded, in order, once each.

    Only spans in «…», "…", “…”, '…' or backticks are read; unquoted prose is never a token.
    An apostrophe between letters is part of a word, not a quote mark."""
    seen: dict[str, None] = {}
    for quoted in _QUOTED.finditer(text):
        span = next(group for group in quoted.groups() if group is not None)
        for match in _TOKEN.finditer(span):
            token = match.group(0).translate(_APOSTROPHES).casefold()
            if len(_LETTER.findall(token)) >= 2:
                seen.setdefault(token)
    return list(seen)


def _names_letter(text: str, letter: str) -> bool:
    """Whether letter stands alone in text (not inside a longer run of letters)."""
    pattern = rf"(?<![{CYRILLIC_LETTER_CLASS}]){re.escape(letter)}(?![{CYRILLIC_LETTER_CLASS}])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def syllable_shaped(token: str, taught: set[str]) -> bool:
    """Whether token reads as one syllable of the taught letters: one vowel letter, no untaught letter."""
    letters = [letter.casefold() for letter in _LETTER.findall(token)]
    return sum(1 for letter in letters if letter in VOWEL_LETTERS) == 1 and set(letters) <= taught


@dataclass
class Gates:
    """The gates' shared state (word index, taught letters, allowed ids) and reporting;
    review_gates.py (#9487) builds on the same state."""

    report: Report
    plan: dict
    level: str
    store: WordStore
    arc: list[ArcPosition] | None
    level_plans: LevelPlans
    words_path: Path
    not_checked_rules: set[str] = field(default_factory=set)

    # -- shared state ---------------------------------------------------------

    @cached_property
    def index(self) -> dict[str, set[str]]:
        """Case-folded surface text -> ids of every store record listing it as lemma or form."""
        index: dict[str, set[str]] = {}
        for record in self.store.records.values():
            for text in (record.lemma, *record.form_texts):
                index.setdefault(text.translate(_APOSTROPHES).casefold(), set()).add(record.id)
        return index

    @cached_property
    def taught_through(self) -> dict[int, set[str]] | None:
        """Letters taught through the end of each lesson, or None outside a letter stage."""
        position = self.plan["arc_ref"]["position"]
        record = next((entry for entry in self.arc or [] if entry.position == position), None)
        if record is None or record.letters is None:
            return None
        taught = {
            letter.casefold() for entry in self.arc or [] if entry.position < position for letter in entry.letters or []
        }
        through: dict[int, set[str]] = {}
        for lesson in self.plan["lessons"]:
            taught |= {
                letter.casefold() for letter in (lesson["inventory"].get("phonetics") or {}).get("letters") or []
            }
            for step in lesson["steps"]:
                taught |= {letter.casefold() for letter in (step.get("introduces") or {}).get("letters") or []}
            through[lesson["n"]] = set(taught)
        return through

    @cached_property
    def _base_layer(self) -> tuple[frozenset[str] | None, str]:
        from ..learner_state.base_layer import BaseLayerError, resolve_base_ids

        try:
            ids = resolve_base_ids(self.level, evidence_dir=self.words_path.parent, words_path=self.words_path)
        except BaseLayerError as error:
            return None, error.message
        return frozenset(ids), ""

    @cached_property
    def _earlier_introduced(self) -> tuple[set[str] | None, str]:
        position = self.plan["arc_ref"]["position"]
        missing = [p for p in range(1, position) if p not in self.level_plans.by_position]
        if missing:
            return None, "earlier arc positions " + ", ".join(map(str, missing)) + " have no plan file"
        ids: set[str] = set()
        for prior in range(1, position):
            ids |= collect_introductions(self.level_plans.by_position[prior][1])["vocabulary"]
        return ids, ""

    def allowed_ids(self, lesson_index: int, rule: str) -> set[str] | None:
        """The word ids lesson lessons[lesson_index] may use (learner state + its own inventory).

        None, with a not_checked line for rule, when the base layer or an earlier plan is unavailable.
        """
        base, base_reason = self._base_layer
        earlier, earlier_reason = self._earlier_introduced
        if base is None or earlier is None:
            self.skip(rule, f"the lesson's allowed word set is unknown ({base_reason or earlier_reason})")
            return None
        allowed = set(base) | earlier
        lessons = self.plan["lessons"]
        for lesson in lessons[:lesson_index]:
            allowed |= collect_introductions({"lessons": [lesson]})["vocabulary"]
        lesson = lessons[lesson_index]
        allowed |= collect_introductions({"lessons": [lesson]})["vocabulary"]
        vocabulary = lesson["inventory"]["vocabulary"]
        allowed |= {entry["evidence"] for entry in vocabulary["core"] + vocabulary["incidental"]}
        allowed |= set(vocabulary["recycled"])
        for step in lesson["steps"]:
            allowed |= set((step.get("uses") or {}).get("vocabulary") or [])
            if step.get("paradigm"):
                allowed.add(step["paradigm"]["word"])
        dialogue = lesson.get("dialogue") or {}
        allowed |= {speaker["evidence"] for speaker in dialogue.get("speakers") or [] if "evidence" in speaker}
        allowed |= {place["evidence"] for place in dialogue.get("places") or []}
        return allowed

    # -- reporting ------------------------------------------------------------

    def note(self, code: str, message: str, lesson: int | None, step: str | None = None) -> None:
        self.report.notes.append(Outcome(code, message, lesson, step))

    def unchecked(self, code: str, message: str, lesson: int | None, step: str | None = None) -> None:
        self.report.not_checked.append(Outcome(code, message, lesson, step))

    def skip(self, rule: str, reason: str) -> None:
        if rule in self.not_checked_rules:
            return
        self.not_checked_rules.add(rule)
        self.report.not_checked.append(
            Outcome(codes.MECHANICAL_RULE_NOT_CHECKED, f"gate {rule} was not checked: {reason}")
        )

    def letter_state_or_skip(self, rule: str, needed: bool) -> dict[int, set[str]] | None:
        """The taught-letter state, or None (skipping M-rule when a letter stage's arc is unavailable)."""
        if self.taught_through is None and self.arc is None and needed:
            self.skip(rule, "the level arc is unavailable, so the taught-letter state is unknown")
        return self.taught_through

    def word_records(self, ids: set[str]) -> list[WordRecord]:
        return [self.store.records[i] for i in sorted(ids) if i in self.store.records]

    # -- M1 ---------------------------------------------------------------

    def check_step_letters(self) -> None:
        introduced = [
            (lesson, step, letter)
            for lesson in self.plan["lessons"]
            for step in lesson["steps"]
            for letter in (step.get("introduces") or {}).get("letters") or []
        ]
        if not introduced or self.letter_state_or_skip("M1", True) is None:
            return
        for lesson, step, letter in introduced:
            activities: dict[str, dict] = {}
            for activity in lesson.get("activities") or []:
                activities.setdefault(activity["id"], activity)  # a duplicate id is duplicate_activity_id (rule 6)
            practice = [activities[a] for a in step.get("practice") or [] if a in activities]
            if not practice:
                continue  # teach_step_without_practice (rule 6) already fails a teach step with none
            if not any(_names_letter(activity["focus"], letter) for activity in practice):
                ids = ", ".join(activity["id"] for activity in practice) or "none"
                self.note(
                    codes.STEP_LETTER_NOT_PRACTISED,
                    f"step {step['id']} introduces the letter {letter}, but no activity in its practice "
                    f"({ids}) names {letter} in its focus; the focus may describe the practice without the glyph, "
                    "so the plan review confirms it (gate M1)",
                    lesson["n"],
                    step["id"],
                )

    # -- M3 -------------------------------------------------------------------

    def check_tokens(self) -> None:
        lessons = self.plan["lessons"]
        for index, lesson in enumerate(lessons):
            sources = [
                (f"step {step['id']} teach text", step["id"], step["teach"])
                for step in lesson["steps"]
                if step.get("teach")
            ]
            sources += [
                (f"activity {activity['id']} focus", None, activity["focus"])
                for activity in lesson.get("activities") or []
            ]
            sources = [(where, step_id, text) for where, step_id, text in sources if tokens_of(text)]
            if not sources:
                continue
            allowed = self.allowed_ids(index, "M3")
            if allowed is None:
                return
            taught = (self.taught_through or {}).get(lesson["n"], set())
            for where, step_id, text in sources:
                unresolved, syllables = [], []
                for token in tokens_of(text):
                    ids = self.index.get(token)
                    if not ids:
                        unresolved.append(token)
                    elif ids & allowed:
                        continue
                    elif syllable_shaped(token, taught):
                        syllables.append(token)
                    else:
                        self.note(
                            codes.TOKEN_NOT_ALLOWED,
                            f"{where} quotes {token!r}, which resolves to {', '.join(sorted(ids))} — no record "
                            f"of lesson {lesson['n']}'s allowed set (gate M3)",
                            lesson["n"],
                            step_id,
                        )
                if unresolved:
                    self.unchecked(
                        codes.TOKEN_UNRESOLVED,
                        f"{where} quotes {', '.join(repr(t) for t in unresolved)}, which resolve to no "
                        "record of the level word store; a syllable or a sound is not a word, so a person "
                        "confirms these (gate M3)",
                        lesson["n"],
                        step_id,
                    )
                if syllables:
                    self.unchecked(
                        codes.TOKEN_UNRESOLVED,
                        f"{where} quotes {', '.join(repr(t) for t in syllables)}, spelled with letters lesson "
                        f"{lesson['n']} has taught and one vowel, and matching only word records outside its "
                        "allowed set; it may be a syllable the plan teaches rather than that word, so a person "
                        "confirms these (gate M3)",
                        lesson["n"],
                        step_id,
                    )

    # -- M5 -------------------------------------------------------------------

    def check_cefr(self) -> None:
        if self.level.upper() not in CEFR_ORDER:
            return
        limit = CEFR_ORDER.index(self.level.upper())
        missing: list[str] = []
        for lesson in self.plan["lessons"]:
            for entry in lesson["inventory"]["vocabulary"]["core"]:
                record = self.store.records.get(entry["evidence"])
                if record is None:
                    continue
                if record.cefr_level not in CEFR_ORDER:
                    missing.append(record.id)
                elif (bands := CEFR_ORDER.index(record.cefr_level) - limit) > 0:
                    self.note(
                        codes.CORE_CEFR_ABOVE_MODULE,
                        f"core lemma {entry['lemma']!r} ({record.id}) is {record.cefr_level} in the word store, "
                        f"{bands} band{'s' * (bands > 1)} above the module's level {self.level.upper()} (gate M5)",
                        lesson["n"],
                    )
        if missing:
            self.skip("M5", "core word records carry no CEFR level: " + ", ".join(sorted(set(missing))))


def check_mechanical(
    report: Report,
    plan: dict,
    *,
    level: str,
    store: WordStore,
    arc: list[ArcPosition] | None,
    level_plans: LevelPlans,
    words_path: Path,
) -> None:
    """Run gates M1, M3 and M5 on a plan that already passed the schema."""
    gates = Gates(report, plan, level, store, arc, level_plans, words_path)
    gates.check_step_letters()
    gates.check_tokens()
    gates.check_cefr()
