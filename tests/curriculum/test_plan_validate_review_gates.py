"""Tests for the review-checkable plan gates C1–C14 (issue #9487).

Each gate has a failing (or noted) fixture and a passing one, each built by a
single mutation of the mechanical gates' passing baseline: a letter-stage
module at arc position 2 (lessons 1 М А, 2 Н О and a recap) with a small
Cyrillic word store. Check 7 of #9487 (the learner-state fix) is tested in
tests/curriculum/learner_state/test_planned.py.

The Cyrillic strings are placeholders assembled from the fixture's letters;
they are fixture data for the gates' letter arithmetic, not claims about
Ukrainian.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes, quote_bytes
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import validate_plan
from tests.curriculum.test_plan_validate import LEVEL, NOT_CHECKED, PRIOR_SLUG, SLUG, prior_plan, write_world
from tests.curriculum.test_plan_validate_mechanical import (
    MAMA,
    MAN,
    MANA,
    NONA,
    ON,
    _drop_letters,
    mechanical_pack,
    mechanical_plan,
    mechanical_words,
)

pytestmark = pytest.mark.reads_content

REVIEW_GATE_CODES = {
    codes.NAMED_BEFORE_INTRODUCTION,
    codes.DUPLICATE_ACTIVITY_FOCUS,
    codes.LISTENING_QUIZ_SINGLE_KEY,
    codes.INCIDENTAL_NOT_DECODABLE,
    codes.INCIDENTAL_LEMMA_NOT_DECODABLE,
    codes.HEARD_WORD_WITHOUT_VIDEO,
    codes.EARLIER_CORE_NOT_RECYCLED,
    codes.RECAP_STORY_MISSING,
    codes.RECAP_COMPREHENSION_NOT_ON_STORY,
    codes.RECAP_COMPREHENSION_AFTER_PRODUCTION,
    codes.FOCUS_EVIDENCE_NOT_IN_STEPS,
    codes.STEP_WORD_NOT_DECODABLE,
    codes.STEP_WORD_LEMMA_NOT_DECODABLE,
    codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT,
    codes.ODD_ONE_OUT_ROW_INVALID,
    codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
    codes.QUOTE_HOST_PRIVATE_USE,
    codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL,
    codes.QUOTE_HOST_WATERMARK,
    codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM,
    codes.COMPUTED_KEY_SINGLE_VALUE,
    codes.COMPUTED_KEY_FORM_DEPENDENT,
    codes.DUPLICATE_LESSON_VIDEO,
}

# extra word ids for these fixtures
PRIOR_ONE, PRIOR_TWO, MANOK = "W-209", "W-210", "W-211"
#: The word VESUM is stubbed to list in this module (the real lookup is never used by these tests).
VESUM_FORMS = {"мамою"}


@pytest.fixture(autouse=True)
def _stub_vesum(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote words outside the word store are looked up in a stub, so the cases never need VESUM."""
    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: {word for word in words if word in VESUM_FORMS})


Mutate = Callable[[dict, dict, dict, dict], None]  # plan, pack, words, prior plan


def _lesson(plan: dict, n: int) -> dict:
    return plan["lessons"][n - 1]


def _activity(plan: dict, n: int, activity_id: str) -> dict:
    return next(a for a in _lesson(plan, n)["activities"] if a["id"] == activity_id)


def _step(plan: dict, n: int, step_id: str) -> dict:
    return next(s for s in _lesson(plan, n)["steps"] if s["id"] == step_id)


def _focus(n: int, activity_id: str, focus: str) -> Mutate:
    return lambda plan, pack, words, prior: _activity(plan, n, activity_id).__setitem__("focus", focus)


def _dialogue(step: str, target_grammar: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 1)["dialogue"] = {
            "step": step,
            "situation": "Two speakers meet.",
            "setting": "A room.",
            "speakers": [
                {"name": "Speaker One", "role": "host", "gender": "f", "evidence": MAMA},
                {"name": "Speaker Two", "role": "guest", "gender": "m", "evidence": MANA},
            ],
            "register": "informal",
            "target_grammar": target_grammar,
            "evidence": ["T-001"],
        }

    return mutate


def _videos(**models: tuple[list[str], list[str]] | None) -> Mutate:
    """Pack video records: V-id -> (letters, words) models, or None for a record without models."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for video_id, model in models.items():
            record: dict = {"id": video_id.replace("_", "-")}
            if model is not None:
                record["models"] = {"letters": model[0], "words": model[1], "segment": None}
            pack["videos"].append(record)
            _step(plan, 1, "s1")["evidence"].append(record["id"])  # a focus names only records a step cites (C9)

    return mutate


def _incidental(n: int, word_id: str, lemma: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, n)["inventory"]["vocabulary"]["incidental"].append({"lemma": lemma, "evidence": word_id})

    return mutate


def _word(word_id: str, lemma: str, *forms: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        words["words"].append(
            {
                "id": word_id,
                "lemma": lemma,
                "pos": "noun",
                "forms": [{"form": form, "tags": "tag-a"} for form in (lemma, *forms)],
                "cefr": {"level": "A1"},
            }
        )

    return mutate


def _teach(n: int, step_id: str, teach: str, evidence: list[str] | None = None) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        step = _step(plan, n, step_id)
        step["teach"] = teach
        if evidence is not None:
            step["evidence"] = evidence

    return mutate


def _prior_core(plan: dict, pack: dict, words: dict, prior: dict) -> None:
    """Position 1 introduces two core records the module may recycle."""
    _word(PRIOR_ONE, "амо")(plan, pack, words, prior)
    _word(PRIOR_TWO, "ано")(plan, pack, words, prior)
    lesson = prior["lessons"][0]
    lesson["inventory"]["vocabulary"]["core"] = [
        {"lemma": "амо", "evidence": PRIOR_ONE, "forms": ["tag-a"]},
        {"lemma": "ано", "evidence": PRIOR_TWO, "forms": ["tag-a"]},
    ]
    lesson["steps"][0]["introduces"]["vocabulary"] += [PRIOR_ONE, PRIOR_TWO]


def _recycle(*word_ids: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        two = _lesson(plan, 2)
        two["inventory"]["vocabulary"]["recycled"] += list(word_ids)
        _step(plan, 2, "s2")["uses"]["vocabulary"] += list(word_ids)  # after О is taught (C10)

    return mutate


def _all(*mutations: Mutate) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for mutation in mutations:
            mutation(plan, pack, words, prior)

    return mutate


def _recap_activities(practice: list[str], *extra: dict) -> Mutate:
    """Add activities to the recap (lesson 3) and set its step's practice order."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 3)["activities"] += list(extra)
        _step(plan, 3, "s1")["practice"] = practice

    return mutate


def _quote(text: str, activity: dict | None = None) -> Mutate:
    """Pack text T-002 with quote bytes, cited by lesson 2 step s2, hosting activity (in consolidation)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["texts"].append({"id": "T-002", "quote": text})
        _step(plan, 2, "s2")["evidence"].append("T-002")
        host = activity or {
            "id": "b4",
            "type": "quiz",
            "placement": "workbook",
            "focus": "Read the source line. kind: comprehension; host: {kind: quote, ref: T-002}.",
        }
        _lesson(plan, 2)["activities"].append(host)
        _lesson(plan, 2)["consolidation"].append(host["id"])

    return mutate


def _odd_one_out(focus: str) -> dict:
    return {"id": "b4", "type": "odd-one-out", "placement": "workbook", "focus": focus}


def _video_records(*records: tuple[str, str, str | None]) -> Mutate:
    """Pack video records (id, url, segment) listed as lesson 1 videos."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for video_id, url, segment in records:
            pack["videos"].append(
                {"id": video_id, "url": url, "models": {"letters": ["М"], "words": [], "segment": segment}}
            )
            _lesson(plan, 1)["videos"].append({"evidence": video_id, "use": "Step s1 letter model."})

    return mutate


def _recycle_prior_at_lesson_two_s1(step_cites_video: bool) -> Mutate:
    """Lesson 2 step s1 (before О is taught) recycles position 1's амо/ано; lesson 2 cites V-902 modelling them."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _prior_core(plan, pack, words, prior)
        two = _lesson(plan, 2)
        two["inventory"]["vocabulary"]["recycled"] += [PRIOR_ONE, PRIOR_TWO]
        _step(plan, 2, "s1")["uses"]["vocabulary"] += [PRIOR_ONE, PRIOR_TWO]
        pack["videos"].append(
            {"id": "V-902", "models": {"letters": [], "words": [PRIOR_ONE, PRIOR_TWO], "segment": None}}
        )
        two["videos"] = [{"evidence": "V-902", "use": "Whole-word model."}]
        if step_cites_video:
            _step(plan, 2, "s1")["evidence"].append("V-902")

    return mutate


def _core_in_lesson_two(word_id: str, lemma: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 2)["inventory"]["vocabulary"]["core"].append(
            {"lemma": lemma, "evidence": word_id, "forms": ["tag-a"]}
        )
        _step(plan, 2, "s2")["introduces"]["vocabulary"].append(word_id)

    return mutate


@dataclass(frozen=True)
class Case:
    name: str
    mutate: Mutate | None = None
    failures: frozenset[str] = frozenset()
    notes: frozenset[str] = frozenset()
    not_checked: frozenset[str] = frozenset()
    says: str = ""


LISTENING = "Required item kind: listening; each item binds host {kind: video, ref: V-id}."

CASES = [
    Case("baseline_passes"),
    # C1 -- a word named before its step introduces it
    Case(
        "c1_dialogue_target_grammar_names_a_word_a_later_step_introduces",
        _dialogue("s1", f"Whole {MAMA} chunk only."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says=f"names {MAMA} (introduced by step s2), which a later step of this lesson introduces",
    ),
    Case("c1_dialogue_at_the_introducing_step_passes", _dialogue("s2", f"Whole {MAMA} chunk only.")),
    Case(
        "c1_practice_focus_scores_a_word_a_later_step_introduces",
        _focus(1, "a1", f"Checks the letter М and the word {MAMA}."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says="activity a1 focus (practice of step s1) names W-201 (introduced by step s2)",
    ),
    Case(
        "c1_practice_focus_scores_a_word_no_lesson_introduced_yet",
        _focus(1, "a1", f"Checks the letter М and the word {NONA}."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says=f"names {NONA}, which no step up to s1 introduces",
    ),
    Case(
        "c1_practice_focus_scoring_an_introduced_or_earlier_word_passes",
        _all(
            _focus(1, "a2", f"Complete «мама» ({MAMA}) and «ман» with А."),
            _focus(2, "b1", f"Checks the letter Н next to {MAMA}."),
        ),
    ),
    Case(
        "c1_consolidation_focus_is_not_a_step_practice",
        _focus(1, "a4", f"Count syllables in «мама» and {MAN} and {NONA}."),
    ),
    # C2 -- identical focus text within one lesson
    Case(
        "c2_two_activities_with_the_same_focus_fail",
        _focus(2, "b3", "Match «мама», «мана»  and «нона» to pictures;\n find О."),  # b2's, whitespace aside
        failures=frozenset({codes.DUPLICATE_ACTIVITY_FOCUS}),
        says="activities b2, b3 carry the same focus text",
    ),
    Case(
        "c2_the_same_focus_in_two_lessons_passes",
        _focus(1, "a4", "Checks the letter Н."),  # lesson 2's b1 focus, word for word
    ),
    # C3 -- a listening activity whose videos model one target
    Case(
        "c3_listening_quiz_on_one_single_letter_video_fails",
        _all(_videos(V_001=(["М"], [])), _focus(1, "a1", f"Checks the letter М from V-001. {LISTENING}")),
        failures=frozenset({codes.LISTENING_QUIZ_SINGLE_KEY}),
        says="cites V-001, which together model only letter М",
    ),
    Case(
        "c3_listening_quiz_on_two_targets_passes",
        _all(
            _videos(V_001=(["М"], []), V_002=(["А"], [])),
            _focus(1, "a1", f"Checks the letter М against А: V-001/T-001, V-002/T-001. {LISTENING}"),
        ),
    ),
    Case(
        "c3_listening_quiz_on_a_video_without_models_is_not_decided",
        _all(_videos(V_001=None), _focus(1, "a1", f"Checks the letter М from V-001. {LISTENING}")),
    ),
    Case(
        "c3_a_quiz_not_declared_listening_is_not_read",
        _all(_videos(V_001=(["М"], [])), _focus(1, "a1", "Checks the letter М after V-001.")),
    ),
    # C4 -- incidental words readable with the taught letters
    Case(
        "c4_incidental_with_no_readable_spelling_fails",
        _incidental(1, ON, "он"),
        failures=frozenset({codes.INCIDENTAL_NOT_DECODABLE}),
        says=f"incidental {ON} ('он') needs н, о, not taught through lesson 1",
    ),
    Case("c4_incidental_readable_once_its_letters_are_taught_passes", _incidental(2, ON, "он")),
    Case(
        "c4_lemma_unreadable_but_a_form_readable_is_a_note",
        _all(_word(MANOK, "манок", "мано"), _incidental(2, MANOK, "манок")),
        notes=frozenset({codes.INCIDENTAL_LEMMA_NOT_DECODABLE}),
        says="incidental lemma 'манок' (W-211) needs к, not taught through lesson 2; readable forms: мано",
    ),
    Case(
        "c4_non_letter_stage_module_is_not_checked_for_readability",
        _all(
            lambda plan, pack, words, prior: _drop_letters(plan, pack, words),
            _focus(1, "a1", "Checks the first sounds."),
            _focus(2, "b1", "Checks the next sounds."),
            _incidental(1, ON, "он"),
        ),
    ),
    # C5 -- a heard word with no video modelling it
    Case(
        "c5_heard_word_without_a_modelling_video_is_a_note",
        _teach(1, "s2", f"The letter А. Hear {MAMA} as a whole word."),
        notes=frozenset({codes.HEARD_WORD_WITHOUT_VIDEO}),
        says=f"the teach text says {MAMA} is heard, but no video the step cites (none)",
    ),
    Case(
        "c5_heard_word_with_a_modelling_video_passes",
        _all(
            _videos(V_003=([], [MAMA])),
            _teach(1, "s2", f"The letter А. Hear {MAMA} as a whole word.", ["T-001", "V-003"]),
        ),
    ),
    Case(
        "c5_a_word_read_in_another_clause_is_not_heard",
        _teach(1, "s2", f"Hear А from the primer, then read {MAMA}; listen again before reading {MANA}."),
    ),
    # C6 -- earlier positions' core records the module never recycles
    Case(
        "c6_earlier_core_not_recycled_is_listed",
        _all(_prior_core, _recycle(PRIOR_ONE)),
        notes=frozenset({codes.EARLIER_CORE_NOT_RECYCLED}),
        says=f"1 of 2 core records of earlier positions appear in no recycled list of this module: {PRIOR_TWO} 'ано' (position 1)",
    ),
    Case("c6_all_earlier_core_recycled_passes", _all(_prior_core, _recycle(PRIOR_ONE, PRIOR_TWO))),
    # C7 -- a recap's first-person story and the host of its comprehension
    Case(
        "c7_recap_without_a_story_block_fails",
        lambda plan, pack, words, prior: _lesson(plan, 3).pop("dialogue"),
        failures=frozenset({codes.RECAP_STORY_MISSING}),
        says="the recap declares no first-person story: it has no dialogue block",
    ),
    Case(
        "c7_recap_with_a_two_speaker_dialogue_fails",
        lambda plan, pack, words, prior: _lesson(plan, 3)["dialogue"]["speakers"].append(
            {"name": "Second", "role": "listener", "gender": "m", "evidence": MANA}
        ),
        failures=frozenset({codes.RECAP_STORY_MISSING}),
        says="it has a dialogue with 2 speakers",
    ),
    Case(
        "c7_recap_comprehension_hosted_on_a_quote_fails",
        _focus(3, "c1", "Review quiz. kind: comprehension; host: {kind: quote, ref: T-001}."),
        failures=frozenset({codes.RECAP_COMPREHENSION_NOT_ON_STORY}),
        says="comprehension activity c1 declares host kind quote (T-001)",
    ),
    Case(
        "c7_recap_without_a_comprehension_activity_fails",
        _focus(3, "c1", "Review quiz."),
        failures=frozenset({codes.RECAP_COMPREHENSION_NOT_ON_STORY}),
        says="no activity of the recap declares kind: comprehension",
    ),
    # C8 -- the story's questions come before the production task
    Case(
        "c8_production_linked_before_the_questions_fails",
        _recap_activities(
            ["c2", "c1"],
            {"id": "c2", "type": "letter-grid", "placement": "inline", "focus": "Copy the story into a notebook."},
        ),
        failures=frozenset({codes.RECAP_COMPREHENSION_AFTER_PRODUCTION}),
        says="comprehension activity c1 (linked in s1) comes after c2 (letter-grid)",
    ),
    Case(
        "c8_story_display_before_and_production_after_the_questions_passes",
        _recap_activities(
            ["c0", "c1", "c2"],
            {"id": "c0", "type": "observe", "placement": "inline", "focus": "Read the story."},
            {"id": "c2", "type": "letter-grid", "placement": "inline", "focus": "Copy the story into a notebook."},
        ),
    ),
    # C9 -- a record a focus names reaches the writer only through the lesson's citations
    Case(
        "c9_focus_names_a_record_no_step_cites_fails",
        _focus(1, "a1", "Checks the letter М against the X-001 row."),
        failures=frozenset({codes.FOCUS_EVIDENCE_NOT_IN_STEPS}),
        says="activity a1 focus names X-001, which no step of this lesson cites",
    ),
    Case(
        "c9_focus_names_its_own_model_or_step_evidence_passes",
        _all(
            _focus(1, "a2", "Complete «мама» and «ман» with А from the X-001 rows."),
            _focus(1, "a1", "Checks the letter М in T-001."),
        ),
    ),
    # C10 -- a step's words are decodable so far, or recorded
    Case(
        "c10_step_word_with_an_untaught_letter_and_no_recording_fails",
        lambda plan, pack, words, prior: _lesson(plan, 1).__setitem__("videos", []),
        failures=frozenset({codes.STEP_WORD_NOT_DECODABLE}),
        says=f"step s2 introduces or uses {MANA} 'мана' (needs н), {MAN} 'ман' (needs н)",
    ),
    Case(
        "c10_recycled_word_recorded_elsewhere_in_the_lesson_fails_in_print",
        _recycle_prior_at_lesson_two_s1(step_cites_video=False),
        failures=frozenset({codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT}),
        says=f"step s1 recycles {PRIOR_ONE} 'амо' (needs о), {PRIOR_TWO} 'ано' (needs о)",
    ),
    Case(
        "c10_recycled_word_whose_step_cites_its_recording_passes",
        _recycle_prior_at_lesson_two_s1(step_cites_video=True),
    ),
    Case(
        "c10_lemma_unreadable_while_a_form_is_readable_is_a_note",
        _all(_word(MANOK, "манок", "мано"), _core_in_lesson_two(MANOK, "манок")),
        notes=frozenset({codes.STEP_WORD_LEMMA_NOT_DECODABLE}),
        says=f"step s2 introduces or uses {MANOK} 'манок' (needs к; readable: мано)",
    ),
    # C11 -- odd-one-out rows drawn from a quote host
    Case(
        "c11_row_without_one_odd_member_fails",
        _quote(
            "мама мана нона\nмама мана мана",
            _odd_one_out("Pick the member whose initial letter differs. host: {kind: quote, ref: T-002}."),
        ),
        failures=frozenset({codes.ODD_ONE_OUT_ROW_INVALID}),
        says="row 'мама мана мана' of T-002 does not have exactly one member differing in initial letter",
    ),
    Case(
        "c11_rows_with_one_odd_member_pass",
        _quote(
            "мама мана нона\nман нона нона",
            _odd_one_out("Pick the member whose first letter differs. host: {kind: quote, ref: T-002}."),
        ),
    ),
    Case(
        "c11_syllable_count_feature_is_computed",
        _quote(
            "мама ман мана", _odd_one_out("Pick the member whose syllables differ. host: {kind: quote, ref: T-002}.")
        ),
    ),
    Case(
        "c11_feature_the_gate_cannot_compute_is_a_note",
        _quote("мама мана нона", _odd_one_out("Pick the odd member. host: {kind: quote, ref: T-002}.")),
        notes=frozenset({codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED}),
        says="activity b4 draws odd-one-out rows from T-002 (мама мана нона)",
    ),
    # C12 -- quote-host bytes the engine prints verbatim
    Case(
        "c12_private_use_code_point_fails",
        _quote("мама \uf0fc мана"),
        failures=frozenset({codes.QUOTE_HOST_PRIVATE_USE}),
        says="quote host T-002 (hosting lesson 2 b4) carries private use: U+F0FC",
    ),
    Case(
        "c12_symbol_inside_a_transcription_bracket_fails",
        _quote("мама [ма\u00bea]"),
        failures=frozenset({codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL}),
        says="'[ма¾a]' holds",
    ),
    Case(
        "c12_publisher_watermark_fails",
        _quote("мама мана\nPidruchnyk.com.ua"),
        failures=frozenset({codes.QUOTE_HOST_WATERMARK}),
        says="carries watermark: 'Pidruchnyk.com.ua'",
    ),
    Case(
        "c12_word_neither_in_the_store_nor_in_vesum_fails",
        _quote("мама номана мамою"),
        failures=frozenset({codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM}),
        says="prints 'номана', which are neither word-store spellings nor VESUM forms",
    ),
    Case(
        "c12_clean_quote_with_schemes_syllables_and_hyphenation_passes",
        _quote("Ма-ма, мана [ = • – ] [ма′на]\nма мо му нона ма-\nна мамою"),
    ),
    # C13 -- a computed key that is the same for every target
    Case(
        "c13_count_syllables_with_one_count_across_targets_fails",
        _focus(1, "a4", f"Count syllables in {MAMA} and {MANA}."),
        failures=frozenset({codes.COMPUTED_KEY_SINGLE_VALUE}),
        says=f"count-syllables activity a4 targets {MAMA}, {MANA}, whose syllable count is 2 for every target",
    ),
    Case(
        "c13_count_syllables_with_two_counts_passes",
        _focus(1, "a4", f"Count syllables in {MAMA} and {MAN}."),
    ),
    Case(
        "c13_another_count_only_through_an_unbound_form_is_a_note",
        _all(_word(MANOK, "манок", "мано", "манками"), _focus(1, "a4", f"Count syllables in {MAMA} and {MANOK}.")),
        notes=frozenset({codes.COMPUTED_KEY_FORM_DEPENDENT}),
        says=f"another key needs a form the plan does not bind ({MANOK})",
    ),
    # C14 -- one recording embedded twice in a lesson
    Case(
        "c14_two_entries_for_one_youtube_video_fail",
        _video_records(
            ("V-910", "https://www.youtube.com/watch?v=ksXIXj7CXwc", None),
            ("V-911", "https://youtu.be/ksXIXj7CXwc", None),
        ),
        failures=frozenset({codes.DUPLICATE_LESSON_VIDEO}),
        says="video entries V-910, V-911 resolve to one recording (youtube:ksXIXj7CXwc, whole video)",
    ),
    Case(
        "c14_two_segments_of_one_video_pass",
        _video_records(
            ("V-910", "https://www.youtube.com/watch?v=ksXIXj7CXwc", "0:00–0:10"),
            ("V-911", "https://www.youtube.com/watch?v=ksXIXj7CXwc", "0:10–0:20"),
        ),
    ),
]


def run(root: Path, mutate: Mutate | None) -> Report:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    if mutate is not None:
        mutate(plan, pack, words, prior)
    world = write_world(root, plan, pack, words)
    (world.plan_path.parent / f"{PRIOR_SLUG}.yaml").write_text(
        yaml.safe_dump(prior, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    request = {"request_schema": 1, "level": LEVEL, "words": [{"lemma": "мам", "pos": "noun", "want": "new"}]}
    (world.words_path.parent / "_base.request.yaml").write_text(
        yaml.safe_dump(request, allow_unicode=True), encoding="utf-8"
    )
    return validate_plan(LEVEL, SLUG, plan_path=world.plan_path)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_case(tmp_path: Path, case: Case) -> None:
    report = run(tmp_path, case.mutate)
    text = report.render_text()
    assert {o.code for o in report.failures} == set(case.failures), text
    assert {o.code for o in report.notes} == set(case.notes), text
    assert {o.code for o in report.not_checked} == NOT_CHECKED | set(case.not_checked), text
    if case.says:
        assert any(case.says in o.message for o in report.failures + report.notes + report.not_checked), text


def test_outcomes_name_lesson_and_step(tmp_path: Path) -> None:
    report = run(tmp_path, next(c for c in CASES if c.name.startswith("c1_dialogue_target")).mutate)
    outcome = report.failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.NAMED_BEFORE_INTRODUCTION, 1, "s1")


def test_unavailable_base_layer_skips_c1_instead_of_guessing(tmp_path: Path) -> None:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    _focus(1, "a1", f"Checks the letter М and the word {NONA}.")(plan, pack, words, prior)
    world = write_world(tmp_path, plan, pack, words)  # no _base.request.yaml: the base layer is unknown
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.NAMED_BEFORE_INTRODUCTION not in {o.code for o in report.failures}, report.render_text()
    gates = {o.message.split()[1] for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED}
    assert "C1" in gates, report.render_text()


def test_c4_skips_a_lesson_before_the_first_taught_letter() -> None:
    plan = mechanical_plan()
    _lesson(plan, 1)["inventory"]["vocabulary"]["incidental"].append({"lemma": "он", "evidence": ON})
    store = type("Store", (), {"records": {}})()
    gates = ReviewGates(Report(LEVEL, SLUG), plan, LEVEL, store, None, None, Path("unused"), pack=None)  # type: ignore[arg-type]
    gates.__dict__["taught_through"] = {1: set(), 2: {"м", "а", "н", "о"}, 3: {"м", "а", "н", "о"}}
    gates.check_incidental_decodable()
    assert gates.report.failures == []


def produced_review_gate_codes(root: Path) -> set[str]:
    produced: set[str] = set()
    for index, case in enumerate(CASES):
        produced |= run(root / f"case-{index}", case.mutate).codes()
    return produced


def test_every_review_gate_code_is_produced(tmp_path: Path) -> None:
    assert produced_review_gate_codes(tmp_path) >= REVIEW_GATE_CODES


def test_c12_unavailable_vesum_is_not_checked_not_passed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)
    report = run(tmp_path, _quote("мама номана мана \uf0fc"))
    assert {o.code for o in report.failures} == {codes.QUOTE_HOST_PRIVATE_USE}, report.render_text()
    gates = {o.message.split()[1] for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED}
    assert "C12" in gates, report.render_text()


def test_c8_outcome_names_the_comprehension_step(tmp_path: Path) -> None:
    case = next(c for c in CASES if c.name == "c8_production_linked_before_the_questions_fails")
    outcome = run(tmp_path, case.mutate).failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.RECAP_COMPREHENSION_AFTER_PRODUCTION, 3, "s1")
