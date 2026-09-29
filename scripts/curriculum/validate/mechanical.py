"""Mechanical plan gates M1–M8 (issue #9138).

Eight structural plan defects that plan reviewers had to find by hand, each
decided from data the validator already reads — the plan, the level arc, the
level word store, the module pack — never from a typed list of Ukrainian
facts. The only Ukrainian inventories used are ones the code already owns:
the closed Cyrillic letter class (scope.CYRILLIC_LETTER_CLASS) and the vowel
letters of scripts.practice.euphony_stem_engine (syllable counts, M7).

  M1  a step introduces a letter that no activity in its practice names in its focus
  M2  a step introduces a letter that no allowed word record contains, while its
      practice includes a word-completion activity (pick-syllables, divide-words, match-up)
  M3  a Ukrainian token in a step's teach text or an activity's focus resolves to
      no record of the lesson's allowed set
  M4  a copy task's text uses letters outside the taught-letter set
  M5  a core lemma's word-record CEFR level is above the module's level (fail from two
      bands above, note at one)
  M6  a match-up binds fewer than three items; a workbook word activity binds fewer
      than three decodable word records
  M7  a count-syllables item set has one distinct syllable count
  M8  a core word (note) or grammar id (fail) is never used or recycled by a later lesson

Severity, per gate (a rule that can misfire on a valid plan must not fail it):
M1, M2, the not-allowed part of M3, the focus part of M4, M6, M7, the grammar half
of M8 and the two-band part of M5 are failures, because plan and store data decide
them. What reads a proxy is reported without failing the run: a token that resolves
to no store record may be a syllable or a sound (not_checked); the pack quote of a
copy task's model may carry the primer's instruction line beside the lines to copy
(note); a core lemma one CEFR band above the module is a note, since a per-lemma
frequency band is noisy at the boundary and a module may teach its own metalanguage
(the position-1 plan teaches звук/літера, which the store lists at A2); a core word
never reused is a note, since decodable practice words and names are core by design
and a recap cannot recycle all of them. Two or more bands above, and a grammar id no
later lesson uses, are failures.

Letter gates (M1, M2, M4 and the decodability half of M6) apply to letter-stage
modules only: those whose arc position carries letters (the rule 5 definition).
The taught-letter state at a lesson is the arc's letters of every earlier position
plus the letters this plan introduces through that lesson.

An activity's items are not in the plan (the plan states type, focus, placement and
model; items are draft fields, §2). The gates read what the plan does state: the
Ukrainian tokens its focus enumerates. M6's match-up count uses only those; a focus
that names none states no item set, so it is not applicable. For M6's workbook
decodable count and M7's syllable counts a focus that names none falls back to the
lesson's own word pool — its core and recycled records (§2: practice.vocabulary is
core) — because those activities draw their words from the lesson.
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
from .pack import Pack, WordRecord, WordStore
from .report import Outcome, Report
from .scope import CYRILLIC_LETTER_CLASS

WORD_COMPLETION_TYPES = frozenset({"pick-syllables", "divide-words", "match-up"})
COPY_TASK_TYPES = frozenset({"letter-grid"})
MATCH_UP_MIN_ITEMS = 3
WORKBOOK_MIN_DECODABLE = 3
CEFR_ORDER = ("A1", "A2", "B1", "B2", "C1", "C2")
CORE_CEFR_FAIL_BANDS = 2

_LETTER = re.compile(f"[{CYRILLIC_LETTER_CLASS}]")
_TOKEN = re.compile(f"[{CYRILLIC_LETTER_CLASS}]+(?:['’ʼ-][{CYRILLIC_LETTER_CLASS}]+)*")
_COPY_WORD = re.compile(r"\bcop(?:y|ies|ying)\b", re.IGNORECASE)
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'"})


def letters_of(text: str) -> set[str]:
    """The distinct Cyrillic letters of text, case-folded."""
    return {letter.casefold() for letter in _LETTER.findall(text)}


def tokens_of(text: str) -> list[str]:
    """The Ukrainian tokens (two or more letters) of text, case-folded, in order, once each."""
    seen: dict[str, None] = {}
    for match in _TOKEN.finditer(text):
        token = match.group(0).translate(_APOSTROPHES).casefold()
        if len(_LETTER.findall(token)) >= 2:
            seen.setdefault(token)
    return list(seen)


def _names_letter(text: str, letter: str) -> bool:
    """Whether letter stands alone in text (not inside a longer run of letters)."""
    pattern = rf"(?<![{CYRILLIC_LETTER_CLASS}]){re.escape(letter)}(?![{CYRILLIC_LETTER_CLASS}])"
    return re.search(pattern, text, re.IGNORECASE) is not None


def syllables_of(lemma: str) -> int:
    return sum(1 for letter in lemma.casefold() if letter in VOWEL_LETTERS)


def _is_copy_task(activity: dict) -> bool:
    return activity["type"] in COPY_TASK_TYPES or _COPY_WORD.search(activity["focus"]) is not None


def _joined(items) -> str:
    return " ".join(sorted(items))


@dataclass
class _Gates:
    report: Report
    plan: dict
    level: str
    store: WordStore
    pack: Pack | None
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

    def fail(self, code: str, message: str, lesson: int | None, step: str | None = None) -> None:
        self.report.failures.append(Outcome(code, message, lesson, step))

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

    # -- M1, M2 ---------------------------------------------------------------

    def check_step_letters(self) -> None:
        introduced = [
            (lesson, step, letter)
            for lesson in self.plan["lessons"]
            for step in lesson["steps"]
            for letter in (step.get("introduces") or {}).get("letters") or []
        ]
        if not introduced or self.letter_state_or_skip("M1/M2", True) is None:
            return
        lessons = self.plan["lessons"]
        for lesson, step, letter in introduced:
            activities: dict[str, dict] = {}
            for activity in lesson.get("activities") or []:
                activities.setdefault(activity["id"], activity)  # a duplicate id is duplicate_activity_id (rule 6)
            practice = [activities[a] for a in step.get("practice") or [] if a in activities]
            if not practice:
                continue  # teach_step_without_practice (rule 6) already fails a teach step with none
            if not any(_names_letter(activity["focus"], letter) for activity in practice):
                ids = ", ".join(activity["id"] for activity in practice) or "none"
                self.fail(
                    codes.STEP_LETTER_NOT_PRACTISED,
                    f"step {step['id']} introduces the letter {letter}, but no activity in its practice "
                    f"({ids}) names {letter} in its focus (gate M1)",
                    lesson["n"],
                    step["id"],
                )
            completion = [a for a in practice if a["type"] in WORD_COMPLETION_TYPES]
            if not completion:
                continue
            allowed = self.allowed_ids(lessons.index(lesson), "M2")
            if allowed is None:
                continue
            wanted = letter.casefold()
            if not any(
                wanted in letters_of(" ".join((record.lemma, *record.form_texts)))
                for record in self.word_records(allowed)
            ):
                self.fail(
                    codes.STEP_LETTER_NO_WORD_RECORD,
                    f"step {step['id']} introduces the letter {letter} and practises it with "
                    f"{', '.join(a['id'] + ' (' + a['type'] + ')' for a in completion)}, but no allowed word "
                    f"record of lesson {lesson['n']} contains {letter} (gate M2)",
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
            for where, step_id, text in sources:
                unresolved = []
                for token in tokens_of(text):
                    ids = self.index.get(token)
                    if not ids:
                        unresolved.append(token)
                    elif not ids & allowed:
                        names = ", ".join(sorted(ids))
                        self.fail(
                            codes.TOKEN_NOT_ALLOWED,
                            f"{where} quotes {token!r}, which resolves to {names} — no record of lesson "
                            f"{lesson['n']}'s allowed set (gate M3)",
                            lesson["n"],
                            step_id,
                        )
                if unresolved:
                    self.report.not_checked.append(
                        Outcome(
                            codes.TOKEN_UNRESOLVED,
                            f"{where} quotes {', '.join(repr(t) for t in unresolved)}, which resolve to no "
                            "record of the level word store; a syllable or a sound is not a word, so a person "
                            "confirms these (gate M3)",
                            lesson["n"],
                            step_id,
                        )
                    )

    # -- M4 -------------------------------------------------------------------

    def check_copy_tasks(self) -> None:
        lessons = self.plan["lessons"]
        copy_tasks = [
            (lesson, activity)
            for lesson in lessons
            for activity in lesson.get("activities") or []
            if _is_copy_task(activity)
        ]
        through = self.letter_state_or_skip("M4", bool(copy_tasks)) if copy_tasks else None
        if through is None:
            return
        for lesson, activity in copy_tasks:
            taught = through[lesson["n"]]
            outside = {t for t in tokens_of(activity["focus"]) if letters_of(t) - taught}
            if outside:
                extra = _joined(letters_of(" ".join(outside)) - taught)
                self.fail(
                    codes.COPY_TASK_LETTER_NOT_TAUGHT,
                    f"copy task {activity['id']} names {', '.join(sorted(outside))} in its focus, which use "
                    f"letters not taught by lesson {lesson['n']}: {extra} (gate M4)",
                    lesson["n"],
                )
            model = activity.get("model")
            text = self.pack.exercise_text.get(model, "") if self.pack is not None and model else ""
            extra = letters_of(text) - taught
            if extra:
                self.report.notes.append(
                    Outcome(
                        codes.COPY_MODEL_LETTER_NOT_TAUGHT,
                        f"copy task {activity['id']}'s model {model} contains letters not taught by lesson "
                        f"{lesson['n']}: {_joined(extra)}; a primer exercise may carry its instruction line "
                        "beside the lines to copy, so the plan review confirms which text is copied (gate M4)",
                        lesson["n"],
                    )
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
                    above = f"{bands} band{'s' * (bands > 1)} above the module's level {self.level.upper()}"
                    message = (
                        f"core lemma {entry['lemma']!r} ({record.id}) is {record.cefr_level} in the word store, "
                        f"{above} (gate M5)"
                    )
                    if bands >= CORE_CEFR_FAIL_BANDS:
                        self.fail(codes.CORE_CEFR_ABOVE_MODULE, message, lesson["n"])
                    else:
                        self.report.notes.append(Outcome(codes.CORE_CEFR_ONE_BAND_ABOVE, message, lesson["n"]))
        if missing:
            self.skip("M5", "core word records carry no CEFR level: " + ", ".join(sorted(set(missing))))

    # -- M6, M7 ---------------------------------------------------------------

    def lesson_pool(self, lesson: dict) -> list[WordRecord]:
        """The word records a lesson's activities draw on: its core and recycled words (§2 practice: core)."""
        vocabulary = lesson["inventory"]["vocabulary"]
        ids = {entry["evidence"] for entry in vocabulary["core"]} | set(vocabulary["recycled"])
        return self.word_records(ids)

    def check_activity_sets(self) -> None:
        through = self.taught_through
        for lesson in self.plan["lessons"]:
            taught = through[lesson["n"]] if through is not None else None
            pool = self.lesson_pool(lesson)
            for activity in lesson.get("activities") or []:
                kind = activity["type"]
                tokens = tokens_of(activity["focus"])
                where = f"activity {activity['id']} ({kind}, {activity['placement']})"
                if kind == "match-up" and tokens and len(tokens) < MATCH_UP_MIN_ITEMS:
                    self.fail(
                        codes.MATCH_UP_TOO_FEW_ITEMS,
                        f"{where} binds {len(tokens)} item(s) ({', '.join(tokens)}); a match-up needs at least "
                        f"{MATCH_UP_MIN_ITEMS} (gate M6)",
                        lesson["n"],
                    )
                if kind == "count-syllables":
                    self.check_syllable_counts(lesson["n"], where, tokens, pool, taught)
                # no letter taught yet (a by-ear lesson): no word is decodable, and decoding is not the activity's job
                if kind in WORD_COMPLETION_TYPES and activity["placement"] == "workbook" and taught:
                    named = [r for t in tokens for r in self.word_records(self.index.get(t, set()))]
                    source = (
                        f"named in its focus ({', '.join(tokens)})"
                        if tokens
                        else "of the lesson's core and recycled words"
                    )
                    decodable = {r.id for r in (named if tokens else pool) if letters_of(r.lemma) <= taught}
                    if len(decodable) < WORKBOOK_MIN_DECODABLE:
                        self.fail(
                            codes.WORKBOOK_TOO_FEW_DECODABLE,
                            f"{where} binds {len(decodable)} decodable word record(s) {source}; a workbook word "
                            f"activity needs at least {WORKBOOK_MIN_DECODABLE} whose letters are all taught by "
                            f"lesson {lesson['n']} (gate M6)",
                            lesson["n"],
                        )

    def check_syllable_counts(
        self, lesson_n: int, where: str, tokens: list[str], pool: list[WordRecord], taught: set[str] | None
    ) -> None:
        """M7: the item set is the focus's words, or else the lesson's decodable core and recycled words."""
        if tokens:
            unresolved = [token for token in tokens if not self.index.get(token)]
            if unresolved:
                self.skip("M7", f"{where} names {', '.join(unresolved)}, which resolve to no word record")
                return
            records = [self.word_records(self.index[token])[0] for token in tokens]
            source = ", ".join(tokens)
        else:
            records = [r for r in pool if taught is None or letters_of(r.lemma) <= taught]
            source = (
                "the lesson's "
                + ("decodable " if taught is not None else "")
                + "core and recycled words "
                + ", ".join(r.lemma for r in records)
            )
        counts = {syllables_of(record.lemma) for record in records}
        if records and len(counts) == 1:
            self.fail(
                codes.COUNT_SYLLABLES_ONE_COUNT,
                f"{where} has an item set ({source}) whose words all have {next(iter(counts))} syllable(s); "
                "one distinct syllable count does not exercise counting (gate M7)",
                lesson_n,
            )

    # -- M8 -------------------------------------------------------------------

    def check_reuse(self) -> None:
        lessons = self.plan["lessons"]
        for index, lesson in enumerate(lessons[:-1]):
            later = lessons[index + 1 :]
            used: dict[str, set[str]] = {"vocabulary": set(), "grammar": set()}
            for other in later:
                used["vocabulary"] |= set(other["inventory"]["vocabulary"]["recycled"])
                for step in other["steps"]:
                    uses = step.get("uses") or {}
                    used["vocabulary"] |= set(uses.get("vocabulary") or [])
                    used["grammar"] |= set(uses.get("grammar") or [])
            for entry in lesson["inventory"]["vocabulary"]["core"]:
                if entry["evidence"] not in used["vocabulary"]:
                    self.report.notes.append(
                        Outcome(
                            codes.CORE_WORD_NOT_REUSED,
                            f"core word {entry['evidence']} ({entry['lemma']!r}) is never used or recycled by "
                            f"lessons {later[0]['n']}–{later[-1]['n']} (gate M8)",
                            lesson["n"],
                        )
                    )
            for entry in lesson["inventory"].get("grammar") or []:
                if entry["id"] not in used["grammar"]:
                    self.fail(
                        codes.GRAMMAR_NOT_REUSED,
                        f"grammar {entry['id']} is never used by lessons {later[0]['n']}–{later[-1]['n']} (gate M8)",
                        lesson["n"],
                    )


def check_mechanical(
    report: Report,
    plan: dict,
    *,
    level: str,
    store: WordStore,
    pack: Pack | None,
    arc: list[ArcPosition] | None,
    level_plans: LevelPlans,
    words_path: Path,
) -> None:
    """Run gates M1–M8 on a plan that already passed the schema."""
    gates = _Gates(report, plan, level, store, pack, arc, level_plans, words_path)
    gates.check_step_letters()
    gates.check_tokens()
    gates.check_copy_tasks()
    gates.check_cefr()
    gates.check_activity_sets()
    gates.check_reuse()
