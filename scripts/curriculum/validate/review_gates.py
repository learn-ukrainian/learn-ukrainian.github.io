"""Plan gates for the defects plan reviewers marked checkable (issue #9487).

The full-access plan reviews of A1 positions 1–3 recorded findings that a
script can decide; each cost a review round. These gates decide them from data
the validator already reads — the plan, the module pack (video models and
URLs, quote bytes), the level word store, the arc and the earlier plans — so a
plan with the defect fails before a reviewer is spent. C1–C6 come from the
first reviews, C7–C14 from the second.

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
  C7  a recap lesson declares no first-person story, or scores its comprehension on another
      host (failure)
  C8  in a recap lesson, an activity other than an unscored presentation is linked before a
      comprehension activity (failure)
  C9  an activity focus names a pack record that no step of its lesson cites as evidence (failure)
  C10 in a letter-stage module, a word a step introduces or uses that cannot be read with the letters taught so
      far and that no recording the lesson cites models (failure); a recycled word that is
      readable only through a recording the step itself does not cite (failure); a lemma that
      cannot be read while another form can (note)
  C11 an odd-one-out row drawn from a quote host without exactly one member differing in the
      stated feature (failure); a feature the gate cannot compute (note)
  C12 a quote host whose bytes carry a private-use code point, a non-Cyrillic symbol inside a
      transcription bracket, a web-address watermark or a word that is neither a word-store
      spelling nor a VESUM form (failure; quote_bytes.py)
  C13 a count-syllables activity whose targets all have the same syllable count (failure); the
      same when the count depends on a form the plan does not bind (note)
  C14 two video entries of one lesson whose pack records are the same recording (failure)

Check 7 of #9487 is a learner-state fix (scripts/curriculum/learner_state/planned.py). Check 9 of the
second round is in pack-verify (scripts/curriculum/evidence/sources.py, Standard line numbering).

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
- C7–C8, C11–C13 read the item kind and host an activity focus declares in the writer contract's
  own syntax (``kind: comprehension``, ``host: {kind: quote, ref: T-…}``, or "quote host refs
  T-…"); prose is never read for them. A recap's first-person story (A1 arc D4, plan schema §2b)
  is its dialogue block with exactly one speaker, the narrator: the plan has no other field for
  it. Its side-by-side English is a draft field (``dialogue.translation_en``) the plan cannot
  state. C7 and C8 apply to ``kind: recap`` lessons; a closing-shape (b) recap step is left to the
  plan review (rule 1b already flags that shape).
- C8: in D4 order the story is followed by its questions and then the production task. Every
  activity linked (steps in order, each practice list in order, then consolidation) before a
  comprehension activity must be an ``observe`` activity — the story's display or a recall.
- C9 reads pack ids (``T-``, ``X-``, ``EX-``, ``E-``, ``V-``, ``S-``, ``U-`` …) that exist in the pack,
  and compares them with the union of the lesson's step evidence: the writer receives a lesson's
  records through its steps (R-26), so a record only a focus names never reaches it.
- C10 applies where the arc position carries letters. The letters taught so far at a step are those
  of earlier positions and lessons plus the letters this lesson's steps introduce up to and including
  it. A word is decodable when its lemma is. When only another form of its record is, the plan does
  not bind which form the step uses, so that is a note; with no readable spelling it fails.
  The words of a step are its ``introduces.vocabulary`` and ``uses.vocabulary``.
  A recording is a video whose pack record lists the word in ``models.words``; the lesson cites it
  in ``videos`` or in a step's evidence.
- C11 applies to an ``odd-one-out`` activity, or one whose focus asks for the member that "differs"
  or is "odd", hosted on a quote. A row is a quote line of three or more words and nothing else.
  The feature is read from the focus: initial/first letter or glyph, final/last letter, syllables
  (or vowel nuclei), letter count. Letters are compared case-folded.
- C13 computes the key of every type whose key is a function of the target form alone: at A1 that is
  ``count-syllables`` (the number of vowel letters). Its targets are the word ids its focus names. A
  target's form is the one a cited quote host prints, else the forms its core entry teaches, else
  any form of the record, which makes the outcome a note.
- C12's quote hosts are the records an activity focus declares as its quote host and the quote
  records cited by a step whose ``needs`` holds ``quote`` (the records the preflight treats as
  printable quotes); the preflight runs the same checks (scripts/build/fresh/preflight.py).
- C14 compares a YouTube video by its id, any other URL without its fragment and trailing slash,
  together with ``models.segment``: two segments of one video are two recordings.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from scripts.practice.euphony_stem_engine import VOWELS as VOWEL_LETTERS

from ..arc.loader import ArcPosition
from . import codes, quote_bytes
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
_PACK_ID = re.compile(r"\b[A-Z][A-Z0-9]*-\d+\b")
_COMPREHENSION_KIND = re.compile(r"\bkind:\s*comprehension\b")
_HOST = re.compile(r"\{\s*kind:\s*(dialogue|quote|video)\s*(?:,\s*ref:\s*([A-Z][A-Z0-9]*-\d+)\s*)?\}")
_QUOTE_HOST_REFS = re.compile(r"\bquote host refs?\s+(T-\d+(?:\s*(?:,|/|and)\s*T-\d+)*)")
_ODD_ONE_OUT = re.compile(r"\bodd\b|\bdiffers?\s+from\b", re.IGNORECASE)
_ROW_WORD = f"[{CYRILLIC_LETTER_CLASS}]+(?:['’ʼ-][{CYRILLIC_LETTER_CLASS}]+)*"
_ROW = re.compile(rf"\s*{_ROW_WORD}(?:[\s,;]+{_ROW_WORD}){{2,}}[\s,;.]*")
_ROW_TOKEN = re.compile(_ROW_WORD)
_YOUTUBE = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/|v/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)


def _vowel_count(text: str) -> int:
    return sum(1 for char in text.casefold() if char in VOWEL_LETTERS)


def _word_letters(text: str) -> list[str]:
    return [letter.casefold() for letter in _LETTER.findall(text)]


#: Odd-one-out features a focus can state and the gate can compute (C11): pattern, name, value of a word.
_FEATURES: tuple[tuple[re.Pattern[str], str, Callable[[str], object]], ...] = (
    (
        re.compile(r"\b(?:initial|first)\s+(?:glyph|letter|sound)s?\b", re.IGNORECASE),
        "initial letter",
        lambda word: _word_letters(word)[0],
    ),
    (
        re.compile(r"\b(?:final|last)\s+(?:glyph|letter)s?\b", re.IGNORECASE),
        "final letter",
        lambda word: _word_letters(word)[-1],
    ),
    (re.compile(r"\bsyllables?\b|\bvowel nuclei\b", re.IGNORECASE), "syllable count", _vowel_count),
    (
        re.compile(r"\bletter count\b|\bnumber of letters\b|\blength\b", re.IGNORECASE),
        "letter count",
        lambda word: len(_word_letters(word)),
    ),
)

#: Activity types whose every item's key is a function of its target form alone (C13).
_COMPUTED_KEYS: dict[str, tuple[str, Callable[[str], object]]] = {"count-syllables": ("syllable count", _vowel_count)}


def _ids(pattern: re.Pattern[str], text: str) -> list[str]:
    """The ids pattern finds in text, in order, once each."""
    return list(dict.fromkeys(pattern.findall(text or "")))


def _normalized(text: str) -> str:
    return " ".join((text or "").split())


def _host(focus: str) -> tuple[str, str | None] | None:
    """The (kind, ref) host an activity focus declares, in the writer contract's syntax."""
    match = _HOST.search(focus)
    if match:
        return match.group(1), match.group(2)
    match = _QUOTE_HOST_REFS.search(focus)
    if match:
        return "quote", _ids(re.compile(r"T-\d+"), match.group(1))[0]
    return None


def _quote_host_refs(focus: str) -> list[str]:
    """Every quote record an activity focus declares as its host."""
    refs = [match.group(2) for match in _HOST.finditer(focus) if match.group(1) == "quote" and match.group(2)]
    for match in _QUOTE_HOST_REFS.finditer(focus):
        refs += re.findall(r"T-\d+", match.group(1))
    return list(dict.fromkeys(refs))


def _linked(lesson: dict) -> list[tuple[int, int, str]]:
    """(step index, slot, activity id) in presentation order; consolidation counts as one more step."""
    steps = lesson["steps"]
    linked = [
        (index, slot, item) for index, step in enumerate(steps) for slot, item in enumerate(step.get("practice") or [])
    ]
    linked += [(len(steps), slot, item) for slot, item in enumerate(lesson.get("consolidation") or [])]
    return linked


def _shown_rows(rows: list[tuple[str, list[str]]]) -> str:
    shown = "; ".join(" ".join(words) for _ref, words in rows[:3])
    return shown + (f"; … {len(rows) - 3} more rows" if len(rows) > 3 else "")


def _video_key(url: str, segment: str | None) -> tuple[str, str | None]:
    match = _YOUTUBE.search(url)
    if match:
        return f"youtube:{match.group(1)}", segment
    return url.split("#", 1)[0].rstrip("/").casefold(), segment


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

    # -- second round: C7–C14 ------------------------------------------------------------

    def _comprehension(self, lesson: dict) -> list[dict]:
        return [a for a in lesson.get("activities") or [] if _COMPREHENSION_KIND.search(a["focus"])]

    # -- C7 -------------------------------------------------------------------

    def check_recap_story(self) -> None:
        for lesson in self.plan["lessons"]:
            if lesson["kind"] != "recap":
                continue
            dialogue = lesson.get("dialogue")
            speakers = (dialogue or {}).get("speakers") or []
            if dialogue is None or len(speakers) != 1:
                found = "no dialogue block" if dialogue is None else f"a dialogue with {len(speakers)} speakers"
                self.fail(
                    codes.RECAP_STORY_MISSING,
                    f"the recap declares no first-person story: it has {found}; a recap is one short first-person "
                    "story side by side in Ukrainian and English, declared as a dialogue block with one speaker, "
                    "the narrator (A1 arc D4, plan schema §2b) (#9487 C7)",
                    lesson["n"],
                )
            comprehension = self._comprehension(lesson)
            if not comprehension:
                self.fail(
                    codes.RECAP_COMPREHENSION_NOT_ON_STORY,
                    "no activity of the recap declares kind: comprehension; the recap asks Ukrainian-only "
                    "questions about its story (A1 arc D4) (#9487 C7)",
                    lesson["n"],
                )
            for activity in comprehension:
                host = _host(activity["focus"])
                if host is None or host[0] != "dialogue":
                    declared = (
                        "no host" if host is None else f"host kind {host[0]}" + (f" ({host[1]})" if host[1] else "")
                    )
                    self.fail(
                        codes.RECAP_COMPREHENSION_NOT_ON_STORY,
                        f"comprehension activity {activity['id']} declares {declared}; a recap's scored comprehension "
                        "is hosted on its first-person story block (host: {kind: dialogue}) (#9487 C7)",
                        lesson["n"],
                    )

    # -- C8 -------------------------------------------------------------------

    def check_recap_order(self) -> None:
        for lesson in self.plan["lessons"]:
            if lesson["kind"] != "recap":
                continue
            activities = {a["id"]: a for a in reversed(lesson.get("activities") or [])}
            comprehension = {a["id"] for a in self._comprehension(lesson)}
            linked = _linked(lesson)
            for index, (step_index, _slot, activity_id) in enumerate(linked):
                if activity_id not in comprehension:
                    continue
                before = [
                    f"{item} ({activities[item]['type']})"
                    for _s, _t, item in linked[:index]
                    if item in activities and item not in comprehension and activities[item]["type"] != "observe"
                ]
                if before:
                    steps = lesson["steps"]
                    where = steps[step_index]["id"] if step_index < len(steps) else "consolidation"
                    self.fail(
                        codes.RECAP_COMPREHENSION_AFTER_PRODUCTION,
                        f"comprehension activity {activity_id} (linked in {where}) comes after "
                        f"{', '.join(dict.fromkeys(before))}; in a recap the story's questions come before the "
                        "production task, and only an unscored observe (the story's display or a recall) precedes "
                        "them (A1 arc D4) (#9487 C8)",
                        lesson["n"],
                        steps[step_index]["id"] if step_index < len(steps) else None,
                    )

    # -- C9 -------------------------------------------------------------------

    def check_focus_evidence(self) -> None:
        for lesson in self.plan["lessons"]:
            cited = {item for step in lesson["steps"] for item in step.get("evidence") or []}
            for activity in lesson.get("activities") or []:
                own = {activity.get("model"), *(activity.get("error_refs") or [])}
                missing = [
                    item
                    for item in _ids(_PACK_ID, activity["focus"])
                    if not item.startswith("W-") and item in self.pack.ids and item not in cited and item not in own
                ]
                if missing:
                    self.fail(
                        codes.FOCUS_EVIDENCE_NOT_IN_STEPS,
                        f"activity {activity['id']} focus names {', '.join(missing)}, which no step of this lesson "
                        "cites as evidence and which is not the activity's model or error_refs; the writer receives "
                        "only the records the lesson cites (R-26) (#9487 C9)",
                        lesson["n"],
                    )

    # -- C10 ------------------------------------------------------------------

    @cached_property
    def taught_before(self) -> dict[int, set[str]] | None:
        """Letters taught before each lesson starts, or None outside a letter stage."""
        through = self.taught_through
        if through is None:
            return None
        position = self.plan["arc_ref"]["position"]
        before = {letter.casefold() for e in self.arc or [] if e.position < position for letter in e.letters or []}
        state: dict[int, set[str]] = {}
        for lesson in self.plan["lessons"]:
            state[lesson["n"]] = set(before)
            before = set(through[lesson["n"]])
        return state

    def _modelled(self, video_ids: list[str]) -> set[str]:
        return {
            word
            for video in video_ids
            if video in self.pack.video_models
            for word in self.pack.video_models[video].words
        }

    def check_step_words_decodable(self) -> None:
        cyrillic = any(
            _LETTER.search(record.lemma)
            for lesson in self.plan["lessons"]
            for step in lesson["steps"]
            for key in ("introduces", "uses")
            for item in (step.get(key) or {}).get("vocabulary") or []
            if (record := self.store.records.get(item)) is not None
        )
        if self.letter_state_or_skip("C10", cyrillic) is None or self.taught_before is None:
            return
        for lesson in self.plan["lessons"]:
            lesson_videos = [video["evidence"] for video in lesson.get("videos") or []]
            lesson_videos += [
                item for step in lesson["steps"] for item in step.get("evidence") or [] if item.startswith("V-")
            ]
            lesson_modelled = self._modelled(lesson_videos)
            recycled = set(lesson["inventory"]["vocabulary"]["recycled"])
            taught = set(self.taught_before[lesson["n"]])
            for step in lesson["steps"]:
                taught |= {letter.casefold() for letter in (step.get("introduces") or {}).get("letters") or []}
                step_modelled = self._modelled([item for item in step.get("evidence") or [] if item.startswith("V-")])
                unreadable, in_print, lemma_only = [], [], []
                shown = (step.get("introduces") or {}).get("vocabulary") or []
                shown = list(dict.fromkeys([*shown, *((step.get("uses") or {}).get("vocabulary") or [])]))
                for item in shown:
                    record = self.store.records.get(item)
                    if record is None:
                        continue  # unknown_word_id (rule 3)
                    spellings = [record.lemma, *record.form_texts]
                    untaught = ", ".join(sorted(set(self._letters(record.lemma)) - taught))
                    readable = [text for text in dict.fromkeys(spellings) if self._readable(text, taught)]
                    if record.lemma in readable or item in step_modelled:
                        continue
                    if readable:
                        if item not in lesson_modelled:
                            lemma_only.append(
                                f"{item} {record.lemma!r} (needs {untaught}; readable: {', '.join(readable[:4])})"
                            )
                        continue
                    if item not in lesson_modelled:
                        unreadable.append(f"{item} {record.lemma!r} (needs {untaught})")
                    elif item in recycled:
                        in_print.append(f"{item} {record.lemma!r} (needs {untaught})")
                if unreadable:
                    self.fail(
                        codes.STEP_WORD_NOT_DECODABLE,
                        f"step {step['id']} introduces or uses {', '.join(unreadable)}: no spelling is readable with the letters "
                        "taught so far and no recording the lesson cites models it (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )
                if lemma_only:
                    self.note(
                        codes.STEP_WORD_LEMMA_NOT_DECODABLE,
                        f"step {step['id']} introduces or uses {', '.join(lemma_only)}: the lemma needs letters not taught so far "
                        "and no recording the lesson cites models it, while another form is readable; the plan does "
                        "not bind the form, so the plan review confirms it (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )
                if in_print:
                    self.fail(
                        codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT,
                        f"step {step['id']} recycles {', '.join(in_print)}: not readable with the letters taught so "
                        "far, and the recording that models it is not cited by this step, so the step meets it in "
                        "print (#9487 C10)",
                        lesson["n"],
                        step["id"],
                    )

    # -- C11 ------------------------------------------------------------------

    def check_odd_one_out_rows(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                focus = activity["focus"]
                if activity["type"] != "odd-one-out" and not _ODD_ONE_OUT.search(focus):
                    continue
                refs = [ref for ref in _quote_host_refs(focus) if ref in self.pack.quotes]
                rows = [
                    (ref, _ROW_TOKEN.findall(line))
                    for ref in refs
                    for line in self.pack.quotes[ref].splitlines()
                    if _ROW.fullmatch(line)
                ]
                if not rows:
                    continue
                feature = next((entry for entry in _FEATURES if entry[0].search(focus)), None)
                if feature is None:
                    self.note(
                        codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
                        f"activity {activity['id']} draws odd-one-out rows from {', '.join(refs)} "
                        f"({_shown_rows(rows)}), and its focus states no feature the "
                        "gate computes (initial or final letter, syllables, letter count); the plan review confirms "
                        "each row has exactly one odd member (#9487 C11)",
                        lesson["n"],
                    )
                    continue
                _pattern, name, value = feature
                for ref, words in rows:
                    values = [value(word) for word in words]
                    counts = Counter(values)
                    if len(counts) == 2 and min(counts.values()) == 1:
                        continue
                    shown = ", ".join(f"{word} ({val})" for word, val in zip(words, values, strict=True))
                    self.fail(
                        codes.ODD_ONE_OUT_ROW_INVALID,
                        f"activity {activity['id']} row {' '.join(words)!r} of {ref} does not have exactly one member "
                        f"differing in {name}: {shown} (#9487 C11)",
                        lesson["n"],
                    )

    # -- C12 ------------------------------------------------------------------

    def check_quote_host_bytes(self, lookup: Callable[[list[str]], set[str]] | None = None) -> None:
        hosts: dict[str, list[str]] = {}  # ref -> where it hosts
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                for ref in _quote_host_refs(activity["focus"]):
                    if ref in self.pack.quotes:
                        hosts.setdefault(ref, []).append(f"lesson {lesson['n']} {activity['id']}")
            for step in lesson["steps"]:
                if "quote" in (step.get("needs") or []):
                    for ref in step.get("evidence") or []:
                        if ref in self.pack.quotes:
                            hosts.setdefault(ref, []).append(f"lesson {lesson['n']} step {step['id']}")
        if not hosts:
            return
        for ref, where in hosts.items():
            for defect in quote_bytes.byte_defects(self.pack.quotes[ref]):
                self.fail(
                    _QUOTE_CODES[defect.kind],
                    f"quote host {ref} (hosting {', '.join(where)}) carries {defect.kind.replace('_', ' ')}: "
                    f"{defect.detail}; the engine prints quote bytes exactly (#9487 C12)",
                    None,
                )
        tokens = {ref: quote_bytes.word_tokens(self.pack.quotes[ref]) for ref in hosts}
        known = quote_bytes.known_spellings(
            text for record in self.store.records.values() for text in (record.lemma, *record.form_texts)
        )
        try:
            unknown = set(
                quote_bytes.unknown_words(
                    [token for ref_tokens in tokens.values() for token in ref_tokens],
                    known,
                    lookup or quote_bytes.vesum_lookup,
                )
            )
        except quote_bytes.VesumUnavailable as error:
            self.skip("C12", f"VESUM is unavailable ({error}), so quote-host words are not looked up")
            return
        for ref, ref_tokens in tokens.items():
            words = [token.surface for token in ref_tokens if token.surface in unknown]
            if words:
                self.fail(
                    codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM,
                    f"quote host {ref} (hosting {', '.join(hosts[ref])}) prints {', '.join(map(repr, words))}, which "
                    "are neither word-store spellings nor VESUM forms: an OCR fragment, a split word, or a word VESUM "
                    "does not list (#9487 C12)",
                    None,
                )

    # -- C13 ------------------------------------------------------------------

    @cached_property
    def _core_forms(self) -> dict[str, set[str]]:
        """Word id -> the form tags core entries of this and earlier plans teach."""
        plans = [self.plan] + [
            self.level_plans.by_position[p][1]
            for p in range(1, self.plan["arc_ref"]["position"])
            if p in self.level_plans.by_position
        ]
        forms: dict[str, set[str]] = {}
        for plan in plans:
            for lesson in plan.get("lessons") or []:
                for entry in (((lesson or {}).get("inventory") or {}).get("vocabulary") or {}).get("core") or []:
                    if isinstance(entry, dict) and isinstance(entry.get("evidence"), str):
                        forms.setdefault(entry["evidence"], set()).update(entry.get("forms") or [])
        return forms

    def check_computed_key(self) -> None:
        for lesson in self.plan["lessons"]:
            for activity in lesson.get("activities") or []:
                if activity["type"] not in _COMPUTED_KEYS:
                    continue
                name, key = _COMPUTED_KEYS[activity["type"]]
                targets = [item for item in _ids(_WORD_ID, activity["focus"]) if item in self.store.records]
                if not targets:
                    continue
                printed = {
                    token.casefold()
                    for ref in _ids(re.compile(r"\bT-\d+\b"), activity["focus"])
                    if ref in self.pack.quotes
                    for token in _ROW_TOKEN.findall(self.pack.quotes[ref])
                }
                bound, unbound = {}, {}
                for item in targets:
                    record = self.store.records[item]
                    spellings = [record.lemma, *record.form_texts]
                    source = [text for text in spellings if text.casefold() in printed]
                    taught = [text for tag, text in record.tagged_forms if tag in self._core_forms.get(item, set())]
                    if source or taught:
                        bound[item] = {key(text) for text in source or taught}
                    else:
                        unbound[item] = ({key(record.lemma)}, {key(text) for text in spellings})
                least = set().union(*bound.values(), *(lemma for lemma, _all in unbound.values()))
                most = set().union(*bound.values(), *(every for _lemma, every in unbound.values()))
                if len(most) == 1:
                    self.fail(
                        codes.COMPUTED_KEY_SINGLE_VALUE,
                        f"{activity['type']} activity {activity['id']} targets {', '.join(targets)}, whose {name} is "
                        f"{next(iter(most))} for every target, so every item has the same key (#9487 C13)",
                        lesson["n"],
                    )
                elif len(least) == 1:
                    self.note(
                        codes.COMPUTED_KEY_FORM_DEPENDENT,
                        f"{activity['type']} activity {activity['id']} targets {', '.join(targets)}: their bound forms "
                        f"and lemmas all have {name} {next(iter(least))}; another key needs a form the plan does not "
                        f"bind ({', '.join(unbound)}), so the plan review confirms the keys vary (#9487 C13)",
                        lesson["n"],
                    )

    # -- C14 ------------------------------------------------------------------

    def check_duplicate_videos(self) -> None:
        for lesson in self.plan["lessons"]:
            groups: dict[tuple[str, str | None], list[str]] = {}
            for entry in lesson.get("videos") or []:
                source = self.pack.video_sources.get(entry["evidence"])
                if source is not None:
                    groups.setdefault(_video_key(*source), []).append(entry["evidence"])
            for (identity, segment), video_ids in groups.items():
                if len(video_ids) > 1:
                    self.fail(
                        codes.DUPLICATE_LESSON_VIDEO,
                        f"video entries {', '.join(video_ids)} resolve to one recording ({identity}"
                        f"{', segment ' + segment if segment else ', whole video'}); the page would embed it "
                        f"{len(video_ids)} times (#9487 C14)",
                        lesson["n"],
                    )


_QUOTE_CODES = {
    quote_bytes.PRIVATE_USE: codes.QUOTE_HOST_PRIVATE_USE,
    quote_bytes.TRANSCRIPTION_SYMBOL: codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL,
    quote_bytes.WATERMARK: codes.QUOTE_HOST_WATERMARK,
}


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
    """Run gates C1–C14 on a plan that already passed the schema, with its pack and word store loaded."""
    gates = ReviewGates(report, plan, level, store, arc, level_plans, words_path, pack=pack)
    gates.check_named_before_introduction()
    gates.check_duplicate_focus()
    gates.check_listening_single_key()
    gates.check_incidental_decodable()
    gates.check_heard_words()
    gates.check_earlier_core_recycled()
    gates.check_recap_story()
    gates.check_recap_order()
    gates.check_focus_evidence()
    gates.check_step_words_decodable()
    gates.check_odd_one_out_rows()
    gates.check_quote_host_bytes()
    gates.check_computed_key()
    gates.check_duplicate_videos()
