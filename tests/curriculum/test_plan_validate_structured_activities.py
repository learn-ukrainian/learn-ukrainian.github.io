"""Structured C1/C18/C21/C26 declarations, paired with #9487's prose cases.

Cyrillic strings here are letter-arithmetic fixtures, not linguistic claims.
"""

from pathlib import Path

import pytest

from scripts.curriculum.validate import codes, quote_bytes
from tests.curriculum.test_plan_validate_mechanical import MAMA, MAN, MONA, NONA
from tests.curriculum.test_plan_validate_review_gates import (
    _activity,
    _all,
    _focus,
    _lesson,
    _quote,
    _step,
    _word,
    run,
)

pytestmark = pytest.mark.reads_content


@pytest.fixture(autouse=True)
def stub_vesum(monkeypatch):
    monkeypatch.setattr(quote_bytes, "vesum_lookup", lambda words: set())


def declaration(n, activity_id, **fields):
    def mutate(plan, pack, words, prior):
        _activity(plan, n, activity_id).update(fields)

    return mutate


def link(n, activity_id, *steps):
    def mutate(plan, pack, words, prior):
        for step in _lesson(plan, n)["steps"]:
            step["practice"] = [item for item in step.get("practice", []) if item != activity_id]
        for step_id in steps:
            _step(plan, n, step_id).setdefault("practice", []).append(activity_id)

    return mutate


# Each case declares the exact failure-code set for the selected gate, with one
# mutation from a passing world. Other gates' findings remain separately visible.
STRUCTURED_CODES = {
    codes.TARGET_NOT_AVAILABLE,
    codes.CHOICE_OPTION_NOT_DECODABLE,
    codes.LEARNER_READ_REF_NOT_PRINTABLE,
    codes.LEARNER_READ_WORD_NOT_IN_PRINT,
    codes.MODELED_PRINT_NOT_DECODABLE,
    codes.COMPREHENSION_TARGET_UNKNOWN,
    codes.COMPREHENSION_TARGET_NOT_IN_HOST,
    codes.OPTIONS_NOT_NFC,
}

CASES = [
    ("c1_same_step", _all(link(1, "a1", "s2"), declaration(1, "a1", targets=[MAMA])), set()),
    ("c1_later", declaration(1, "a1", targets=[MAMA]), {codes.TARGET_NOT_AVAILABLE}),
    (
        "c1_earliest_of_two",
        _all(link(1, "a1", "s1", "s2"), declaration(1, "a1", targets=[MAMA])),
        {codes.TARGET_NOT_AVAILABLE},
    ),
    ("c1_unlinked_lesson_end", _all(link(1, "a1"), declaration(1, "a1", targets=[MAMA])), set()),
    ("c1_unlinked_out_of_set", _all(link(1, "a1"), declaration(1, "a1", targets=[NONA])), {codes.TARGET_NOT_AVAILABLE}),
    ("c1_unscored_presentation", declaration(1, "a3", targets=[MAMA]), set()),
    ("c1_unknown", declaration(1, "a1", targets=["W-999"]), {codes.TARGET_NOT_AVAILABLE}),
    ("c1_empty_ignores_prose", _all(_focus(1, "a1", f"Checks {NONA}."), declaration(1, "a1", targets=[])), set()),
    ("c18_glyph_pass", declaration(1, "a1", options=["М"]), set()),
    ("c18_glyph_fail", declaration(1, "a1", options=["А"]), {codes.CHOICE_OPTION_NOT_DECODABLE}),
    ("c18_single_step_word", declaration(1, "a1", options=["мама"]), {codes.CHOICE_OPTION_NOT_DECODABLE}),
    ("c18_recording_no_exemption", declaration(1, "a1", options=["мана"]), {codes.CHOICE_OPTION_NOT_DECODABLE}),
    ("c18_formula_and_empty", declaration(1, "a4", options=["мама мама", "", "’"]), set()),
    ("c18_formula_all_letters", declaration(1, "a4", options=["мама мало"]), {codes.CHOICE_OPTION_NOT_DECODABLE}),
    (
        "c18_earliest_of_two",
        _all(link(1, "a1", "s1", "s2"), declaration(1, "a1", options=["А"])),
        {codes.CHOICE_OPTION_NOT_DECODABLE},
    ),
    ("c18_unlinked_end", _all(link(1, "a1"), declaration(1, "a1", options=["А"])), set()),
    (
        "c18_empty_ignores_prose",
        _all(_focus(1, "a1", "The printed options: мама, мало."), declaration(1, "a1", options=[])),
        set(),
    ),
    (
        "options_nfc",
        declaration(1, "a1", options=["і\u0308"]),
        {codes.OPTIONS_NOT_NFC, codes.CHOICE_OPTION_NOT_DECODABLE},
    ),
    ("c21_all_print_pass", _all(_quote("мама мона"), declaration(2, "b4", learner_reads=["T-002"])), set()),
    (
        "c21_all_print_fail",
        _all(_quote("мама мало"), declaration(2, "b4", learner_reads=["T-002"])),
        {codes.MODELED_PRINT_NOT_DECODABLE},
    ),
    (
        "c21_narrow_print",
        _all(_quote("мама мало"), declaration(2, "b4", learner_reads=[{"ref": "T-002", "words": ["мама"]}])),
        set(),
    ),
    (
        "c21_selection_absent",
        _all(_quote("мама"), declaration(2, "b4", learner_reads=[{"ref": "T-002", "words": ["мона"]}])),
        {codes.LEARNER_READ_WORD_NOT_IN_PRINT},
    ),
    (
        "c21_selection_exact_case",
        _all(_quote("Мама"), declaration(2, "b4", learner_reads=[{"ref": "T-002", "words": ["мама"]}])),
        {codes.LEARNER_READ_WORD_NOT_IN_PRINT},
    ),
    ("c21_non_printable", declaration(1, "a1", learner_reads=["V-900"]), {codes.LEARNER_READ_REF_NOT_PRINTABLE}),
    ("c21_unknown_ref", declaration(1, "a1", learner_reads=["T-999"]), {codes.LEARNER_READ_REF_NOT_PRINTABLE}),
    (
        "c21_step_timing",
        _all(_quote("мона"), link(2, "b4", "s1", "s2"), declaration(2, "b4", learner_reads=["T-002"])),
        {codes.MODELED_PRINT_NOT_DECODABLE},
    ),
    (
        "c21_empty_ignores_prose",
        _all(_quote("мало"), _focus(2, "b4", "Read the exact print of T-002."), declaration(2, "b4", learner_reads=[])),
        set(),
    ),
    ("c26_quote_pass", _all(_quote("мама"), declaration(2, "b4", targets=[MAMA])), set()),
    (
        "c26_quote_absent",
        _all(_quote("мама"), declaration(2, "b4", targets=[MONA])),
        {codes.COMPREHENSION_TARGET_NOT_IN_HOST},
    ),
    (
        "c26_unknown",
        _all(_quote("мама"), declaration(2, "b4", targets=["W-999"])),
        {codes.TARGET_NOT_AVAILABLE, codes.COMPREHENSION_TARGET_UNKNOWN},
    ),
    (
        "c26_empty_ignores_prose",
        _all(
            _quote("мама"),
            _focus(2, "b4", "Checks W-999. kind: comprehension; host: {kind: quote, ref: T-002}."),
            declaration(2, "b4", targets=[]),
        ),
        set(),
    ),
]


@pytest.mark.parametrize("name,mutate,expected", CASES, ids=[case[0] for case in CASES])
def test_structured_gate(tmp_path, name, mutate, expected):
    report = run(tmp_path, mutate, strict=True)
    assert {o.code for o in report.failures} & STRUCTURED_CODES == expected, report.render_text()
    assert codes.CYRILLIC_IN_DISALLOWED_FIELD not in report.codes(), report.render_text()
    if name == "c1_earliest_of_two":
        assert next(o for o in report.failures if o.code == codes.TARGET_NOT_AVAILABLE).step == "s1"
    if name == "c21_step_timing":
        assert next(o for o in report.failures if o.code == codes.MODELED_PRINT_NOT_DECODABLE).step == "s1"


def produced_structured_codes(root: Path):
    produced = set()
    for name, mutate, _ in CASES:
        produced |= run(root / name, mutate).codes()
    produced |= run(root / "forbidden", declaration(1, "a3", options=[])).codes()
    return produced


@pytest.mark.parametrize(
    "activity_id,present,code", [("a1", False, codes.OPTIONS_MISSING), ("a3", True, codes.OPTIONS_FORBIDDEN)]
)
def test_options_policy_is_a_note_in_pr1(tmp_path, activity_id, present, code):
    report = run(tmp_path, declaration(1, activity_id, options=[]) if present else None, strict=True)
    assert any(o.code == code for o in report.notes), report.render_text()
    assert not any(o.code == code for o in report.failures)


@pytest.mark.parametrize(
    "focus,field,values,note,fail",
    [
        (f"Checks {MAMA}.", "targets", [MAMA], codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED, codes.TARGET_NOT_AVAILABLE),
        (
            f"Checks {MAMA} and do not give hints.",
            "targets",
            [MAMA],
            codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
            codes.TARGET_NOT_AVAILABLE,
        ),
        (
            f"Do not score {MAMA}.",
            "targets",
            [MAMA],
            codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
            codes.TARGET_NOT_AVAILABLE,
        ),
        (
            "The printed options are мама and мало.",
            "options",
            ["мама", "мало"],
            codes.CHOICE_OPTION_UNVERIFIED,
            codes.CHOICE_OPTION_NOT_DECODABLE,
        ),
        (
            "The printed options: мама, мало.",
            "options",
            ["мама", "мало"],
            codes.CHOICE_OPTION_UNVERIFIED,
            codes.CHOICE_OPTION_NOT_DECODABLE,
        ),
        (
            "The teacher never prints the options мама and мало.",
            "options",
            ["мама", "мало"],
            codes.CHOICE_OPTION_UNVERIFIED,
            codes.CHOICE_OPTION_NOT_DECODABLE,
        ),
    ],
)
def test_adversarial_prose_and_structured_pairs(tmp_path, focus, field, values, note, fail):
    legacy = run(tmp_path / "prose", _focus(1, "a1", focus))
    declared = run(tmp_path / "structured", _all(_focus(1, "a1", focus), declaration(1, "a1", **{field: values})))
    assert any(o.code == note for o in legacy.notes)
    assert not legacy.failures
    assert any(o.code == fail for o in declared.failures)
    assert not any(o.code == note for o in declared.notes)


@pytest.mark.parametrize(
    "text,held",
    [
        ("мама мона", True),
        ("мона мама", False),
        ("мама ман мона", False),
        ("мама\nмона", True),
        ("мама STOP мона", False),
    ],
)
def test_c26_formula_is_a_contiguous_token_run(tmp_path, text, held):
    formula = "W-299"
    report = run(tmp_path, _all(_word(formula, "мама мона"), _quote(text), declaration(2, "b4", targets=[formula])))
    assert any(o.code == codes.COMPREHENSION_TARGET_NOT_IN_HOST for o in report.failures) == (not held), (
        report.render_text()
    )


@pytest.mark.parametrize(
    "host,note",
    [
        ("host: {kind: dialogue}", codes.COMPREHENSION_TARGET_UNVERIFIED),
        ("host: {kind: quote, ref: T-002}", codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED),
    ],
)
def test_c26_undecidable_host_notes(tmp_path, host, note):
    report = run(
        tmp_path,
        _all(_quote("[мона]"), _focus(2, "b4", f"kind: comprehension; {host}."), declaration(2, "b4", targets=[MAMA])),
    )
    assert any(o.code == note for o in report.notes), report.render_text()
    if note == codes.COMPREHENSION_TARGET_UNVERIFIED:
        assert not any("no host" in o.message for o in report.notes if o.code == note)


@pytest.mark.parametrize(
    "focus",
    [
        "kind: comprehension; host: {kind: quote, ref: T-002}. Do not score W-206.",
        "kind: comprehension; host: {kind: quote, ref: T-002}. As in b2 (host: {kind: dialogue}), W-206.",
        "kind: comprehension; host: {kind: quote, ref: T-999}.",
        "kind: comprehension.",
    ],
)
def test_c26_prose_cannot_shelter_declared_target(tmp_path, focus):
    report = run(tmp_path, _all(_quote("мама"), _focus(2, "b4", focus), declaration(2, "b4", targets=[MONA])))
    assert any(o.code == codes.COMPREHENSION_TARGET_NOT_IN_HOST for o in report.failures), report.render_text()


@pytest.mark.parametrize(
    "fields",
    [
        {"targets": [MAMA, MAMA]},
        {"targets": ["not-a-word-id"]},
        {"targets": "W-201"},
        {"options": [1]},
        {"learner_reads": [{"ref": "T-002"}]},
        {"learner_reads": [{"ref": "T-002", "words": "мама"}]},
        {"learner_reads": [{"ref": "T-002", "words": [], "extra": True}]},
        {"learner_reads": ["not-a-pack-id"]},
    ],
)
def test_structured_schema_rejects_invalid_shapes(tmp_path, fields):
    report = run(tmp_path, declaration(1, "a1", **fields))
    assert any(o.code == codes.SCHEMA_VIOLATION for o in report.failures), report.render_text()


@pytest.mark.parametrize(
    "selection,expected",
    [
        ({"ref": "T-002", "words": ["мама мона"]}, set()),
        ({"ref": "T-002", "words": ["мона мама"]}, {codes.LEARNER_READ_WORD_NOT_IN_PRINT}),
        ({"ref": "T-002", "words": ["STOP мама"]}, {codes.LEARNER_READ_WORD_NOT_IN_PRINT}),
        ({"ref": "T-002", "words": []}, set()),
    ],
)
def test_c21_formula_selectors_match_exact_print(tmp_path, selection, expected):
    report = run(tmp_path, _all(_quote("мама мона"), declaration(2, "b4", learner_reads=[selection])))
    assert {o.code for o in report.failures} & STRUCTURED_CODES == expected, report.render_text()


def test_c26_recorded_host_holds_structured_target(tmp_path):
    report = run(
        tmp_path,
        _all(
            _focus(1, "a1", "kind: comprehension; host: {kind: video, ref: V-900}."),
            link(1, "a1", "s2"),
            declaration(1, "a1", targets=[MAN]),
        ),
    )
    assert not any(
        o.code in {codes.COMPREHENSION_TARGET_UNKNOWN, codes.COMPREHENSION_TARGET_NOT_IN_HOST} for o in report.failures
    ), report.render_text()


def test_structured_options_before_first_taught_letter_fail(tmp_path):
    def mutate(plan, pack, words, prior):
        _step(plan, 1, "s1")["introduces"]["letters"] = []
        _activity(plan, 1, "a1")["options"] = ["М"]

    report = run(tmp_path, mutate)
    assert any(o.code == codes.CHOICE_OPTION_NOT_DECODABLE and o.step == "s1" for o in report.failures), (
        report.render_text()
    )


@pytest.mark.parametrize("text,noted", [("[мама]", True), ("[мама\nмона]", True), ("мама [мама]", False)])
def test_c26_matching_spelling_inside_transcription_stays_advisory(tmp_path, text, noted):
    report = run(tmp_path, _all(_quote(text), declaration(2, "b4", targets=[MAMA])))
    assert any(o.code == codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED for o in report.notes) == noted, (
        report.render_text()
    )
    assert not any(o.code == codes.COMPREHENSION_TARGET_NOT_IN_HOST for o in report.failures)


@pytest.mark.parametrize(
    "path,allowed",
    [
        (("objectives", 0), True),
        (("connects_to", 0), False),
        (("lessons", 0, "dialogue", "situation"), True),
        (("lessons", 0, "dialogue", "speakers", 0, "name"), True),
        (("lessons", 0, "dialogue", "places", 0, "name"), True),
        (("lessons", 0, "dialogue", "speakers", 0, "role"), False),
        (("lessons", 0, "activities", 0, "options", 0), True),
        (("lessons", 0, "activities", 0, "learner_reads", 0, "words", 0), True),
        (("lessons", 0, "activities", 0, "learner_reads", 0, "ref"), False),
        (("lessons", 0, "activities", 0, "model"), False),
    ],
)
def test_cyrillic_permission_is_limited_to_text_fields(path, allowed):
    from scripts.curriculum.validate.validate import _cyrillic_allowed

    assert _cyrillic_allowed(path) is allowed


@pytest.mark.parametrize(
    "text,held", [("мама\nмона", True), ("мама [мона] мона", False), ("мама [мона\nмама] мона", False)]
)
def test_formula_wrapping_does_not_join_across_transcription(tmp_path, text, held):
    formula = "W-299"
    report = run(tmp_path, _all(_word(formula, "мама мона"), _quote(text), declaration(2, "b4", targets=[formula])))
    finding = {o.code for o in report.failures + report.notes}
    assert (
        codes.COMPREHENSION_TARGET_NOT_IN_HOST not in finding
        and codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED not in finding
    ) == held, report.render_text()


def test_c21_selected_formula_can_wrap_in_source_print(tmp_path):
    report = run(
        tmp_path,
        _all(_quote("мама\nмона"), declaration(2, "b4", learner_reads=[{"ref": "T-002", "words": ["мама мона"]}])),
    )
    assert not any(o.code == codes.LEARNER_READ_WORD_NOT_IN_PRINT for o in report.failures), report.render_text()
