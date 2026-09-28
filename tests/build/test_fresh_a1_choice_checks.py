"""A1 post-resolution choice checks using independently inspected VESUM forms.

VESUM source locations: брат 487702-487719, книга 2614480-2614493,
бути 542216-542245, читати 6561736-6561760, великий 611137-611177,
м'яч 3260520-3260537.
"""

from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.build.fresh.runner import check_7_a1_choices
from scripts.curriculum.resolver import receipts


def _record(number: int, lemma: str, forms: list[tuple[str, str]]) -> dict:
    return {
        "id": f"W-{number}",
        "lemma": lemma,
        "forms": [{"form": text, "tags": tags, "learner": True} for text, tags in forms],
    }


BROTHER = _record(
    1,
    "брат",
    [
        ("брата", "noun:anim:m:v_rod"),
        ("брата", "noun:anim:m:v_zna"),
        ("брату", "noun:anim:m:v_dav"),
        ("брату", "noun:anim:m:v_mis"),
    ],
)
BOOK = _record(
    2,
    "книга",
    [
        ("книги", "noun:inanim:f:v_rod"),
        ("книги", "noun:inanim:p:v_naz"),
        ("книги", "noun:inanim:p:v_zna"),
        ("книгу", "noun:inanim:f:v_zna"),
    ],
)
BE = _record(
    3,
    "бути",
    [
        ("буду", "verb:imperf:futr:s:1"),
        ("буде", "verb:imperf:futr:s:3"),
        ("будемо", "verb:imperf:futr:p:1"),
    ],
)
READ = _record(
    4,
    "читати",
    [
        ("читати", "verb:imperf:inf"),
        ("читаю", "verb:imperf:pres:s:1"),
        ("читаєш", "verb:imperf:pres:s:2"),
        ("читав", "verb:imperf:past:m"),
    ],
)
BIG = _record(
    6,
    "великий",
    [
        ("велике", "adj:n:v_naz:compb"),
        ("великому", "adj:n:v_dav:compb"),
    ],
)
BREAKFAST = _record(
    7,
    "поснідати",
    [
        ("поснідала", "verb:perf:past:f"),
        ("поснідали", "verb:perf:past:p"),
        ("поснідав", "verb:perf:past:m"),
    ],
)
WATCH = _record(8, "дивитися", [("дивився", "verb:rev:imperf:past:m"), ("дивилися", "verb:rev:imperf:past:p")])
GIVE = _record(
    9,
    "дати",
    [
        ("дай", "verb:perf:impr:s:2"),
        ("дати", "verb:perf:inf"),
        ("дайте", "verb:perf:impr:p:2"),
    ],
)
COST = _record(
    10,
    "коштувати",
    [("коштує", "verb:imperf:pres:s:3"), ("коштувала", "verb:imperf:past:f")],
)
WORK = _record(
    11,
    "працювати",
    [("працюємо", "verb:imperf:pres:p:1"), ("працювали", "verb:imperf:past:p")],
)


def _check(
    tmp_path: Path,
    item: dict,
    record: dict,
    *,
    extra_records: list[dict] | None = None,
    lookup=None,
    typ: str = "quiz",
) -> dict:
    draft = {"activities": [{"id": "a1", "items": [item]}], "steps": []}
    lesson = {"activities": [{"id": "a1", "type": typ}]}
    words = {"words": [record, *(extra_records or [])]}
    stream = SimpleNamespace(
        lesson={"level": "a1", "slug": "sample", "n": 1}, inputs={"draft_sha256": "a" * 64}, tokens=[]
    )
    return check_7_a1_choices(
        draft,
        lesson,
        words,
        stream,
        state_dir=tmp_path,
        lesson_n=1,
        vesum_lookup=lookup or (lambda words: {word: [] for word in words}),
    )


def _form(options: list[str], record: dict, demand: dict[str, str], *, key: int = 0, taught: str = "Case") -> dict:
    return {
        "kind": "form",
        "options": options,
        "correct": key,
        "option_records": [record["id"]] * len(options),
        "tests_feature": taught,
        "requires": demand,
    }


def test_brother_accusative_accepts_only_key_and_records_missing_receipt(tmp_path: Path) -> None:
    item = _form(["брата", "брату"], BROTHER, {"Case": "Acc"})
    row = _check(tmp_path, item, BROTHER)
    assert row["status"] == "passed"
    assert row["details"]["requirement_receipts"] == [{"activity": "a1", "item": 0, "requirement": "not_checked"}]
    swapped = copy.deepcopy(item)
    swapped["correct"] = 1
    assert _check(tmp_path, swapped, BROTHER)["code"] == "form_not_unique_for_requires"


def test_book_plural_accusative_needs_singular_demand(tmp_path: Path) -> None:
    item = _form(["книгу", "книги"], BOOK, {"Case": "Acc", "Number": "Sing"}, taught="Number")
    assert _check(tmp_path, item, BOOK)["status"] == "passed"
    item["requires"] = {"Case": "Acc"}
    item["tests_feature"] = "Case"
    assert _check(tmp_path, item, BOOK)["code"] == "form_not_unique_for_requires"


@pytest.mark.parametrize(
    ("record", "options", "requires", "taught", "expected"),
    [
        (
            BREAKFAST,
            ["поснідала", "поснідали"],
            {"Gender": "Fem", "Number": "Sing", "VerbForm": "Fin"},
            "Gender",
            "passed",
        ),
        (
            BREAKFAST,
            ["поснідала", "поснідав"],
            {"Gender": "Fem", "Number": "Sing", "VerbForm": "Fin"},
            "Gender",
            "passed",
        ),
        (WATCH, ["дивився", "дивилися"], {"Gender": "Masc", "Number": "Sing", "VerbForm": "Fin"}, "Gender", "passed"),
        (GIVE, ["дай", "дати"], {"Number": "Sing", "Person": "2", "VerbForm": "Fin"}, "Number", "passed"),
        (GIVE, ["дай", "дайте"], {"Number": "Sing", "Person": "2", "VerbForm": "Fin"}, "Number", "passed"),
        (
            COST,
            ["коштує", "коштувала"],
            {"Person": "3", "Number": "Sing"},
            "Person",
            "form_option_missing_required_group",
        ),
        (
            WORK,
            ["працюємо", "працювали"],
            {"Person": "1", "Number": "Plur"},
            "Person",
            "form_option_missing_required_group",
        ),
        (READ, ["читаю", "читав"], {"Person": "1", "Number": "Sing"}, "Person", "form_option_missing_required_group"),
    ],
)
def test_carried_feature_exclusion_and_key_swaps(
    tmp_path: Path, record: dict, options: list[str], requires: dict[str, str], taught: str, expected: str
) -> None:
    item = _form(options, record, requires, taught=taught)
    row = _check(tmp_path, item, record)
    if expected == "passed":
        assert row["status"] == "passed"
    else:
        assert row["code"] == expected
    item["correct"] = 1
    swapped = _check(tmp_path, item, record)
    assert swapped["code"] == (
        "form_not_unique_for_requires" if expected == "passed" else "form_option_missing_required_group"
    )


def test_one_noncontradicting_analysis_makes_distractor_undecidable(tmp_path: Path) -> None:
    # Both tags for «дати» are sourced VESUM analyses of that surface. This synthetic
    # bound record forces the checker to consider the noun homograph too.
    mixed = _record(
        12,
        "дати",
        [
            ("дайте", "verb:perf:impr:p:2"),
            ("дати", "verb:perf:inf"),
            ("дати", "noun:inanim:p:v_naz"),
        ],
    )
    item = _form(["дайте", "дати"], mixed, {"Person": "2", "Number": "Plur", "VerbForm": "Fin"}, taught="Person")
    assert _check(tmp_path, item, mixed)["code"] == "form_option_missing_required_group"
    item["correct"] = 1
    assert _check(tmp_path, item, mixed)["code"] == "form_option_missing_required_group"


@pytest.mark.parametrize(
    ("sentence", "record", "options", "requires", "feature"),
    [
        ("Я ___ книгу", READ, ["читаю", "читаєш"], {"Person": "1", "Number": "Sing"}, "Person"),
        (
            "Вікно ___ і чисте",
            BIG,
            ["велике", "великому"],
            {"Gender": "Neut", "Number": "Sing", "Case": "Nom"},
            "Gender",
        ),
    ],
)
def test_header_agreement_examples_reject_swapped_key(
    tmp_path: Path, sentence: str, record: dict, options: list[str], requires: dict[str, str], feature: str
) -> None:
    item = _form(options, record, requires, taught=feature)
    item["sentence"] = sentence
    assert _check(tmp_path, item, record)["status"] == "passed"
    item["correct"] = 1
    assert _check(tmp_path, item, record)["code"] == "form_not_unique_for_requires"


@pytest.mark.parametrize(
    ("seat", "accepted"),
    [
        ("codex@gpt-6-sol", False),
        ("grok@grok-4.7", True),
        ("cursor@grok-4.7", False),
        ("codex@grok-4.7", False),
        ("grok@unknown", False),
    ],
)
def test_ambiguous_group_entry_needs_other_family_language_seat(tmp_path: Path, seat: str, accepted: bool) -> None:
    (tmp_path / "lesson-1.writer.yaml").write_text("model: gpt-6-sol\n", encoding="utf-8")
    activity = {
        "id": "a1",
        "grouping_feature": "Case",
        "groups": [
            {"value": "Gen", "items": [{"text": "книги", "record": "W-2", "why": "Selected by context."}]},
            {"value": "Nom", "items": []},
        ],
    }
    stream = SimpleNamespace(
        lesson={"level": "a1", "slug": "sample", "n": 1},
        inputs={},
        tokens=[
            {
                "unit": {"activity": "a1", "block": "group_0_0"},
                "provenance": f"question:{seat}:Q-001",
            }
        ],
    )
    row = check_7_a1_choices(
        {"activities": [activity], "steps": []},
        {"activities": [{"id": "a1", "type": "group-sort"}]},
        {"words": [BOOK]},
        stream,
        state_dir=tmp_path,
        lesson_n=1,
        vesum_lookup=lambda words: {word: [] for word in words},
    )
    assert row["status"] == ("passed" if accepted else "failed")
    if not accepted:
        assert row["code"] == "group_entry_ambiguous_without_receipt"


def test_analytic_future_uses_single_store_forms(tmp_path: Path) -> None:
    aux = _form(["буду", "буде", "будемо"], BE, {"Person": "1", "Number": "Sing"}, taught="Person")
    assert _check(tmp_path, aux, BE)["status"] == "passed"
    infinitive = _form(["читати", "читаю", "читав"], READ, {"VerbForm": "Inf"}, taught="VerbForm")
    assert _check(tmp_path, infinitive, READ)["status"] == "passed"
    infinitive["options"][0] = "буду читати"
    assert _check(tmp_path, infinitive, READ)["code"] == "form_option_without_analysis"


def test_requirement_confirmation_is_bound_to_demand_and_other_family(tmp_path: Path) -> None:
    item = _form(["брата", "брату"], BROTHER, {"Case": "Acc"})
    doc = {
        "requirements_schema": 1,
        "lesson": {"level": "a1", "slug": "sample", "n": 1},
        "inputs": {"draft_sha256": "a" * 64},
        "items": [
            {
                "activity": "a1",
                "item": 0,
                "requires": {"Case": "Acc"},
                "confirmed": True,
                "writer": {"seat": "codex@sol", "family": "openai"},
                "reviewer": {"seat": "grok@grok", "family": "xai", "lane": "language"},
            }
        ],
    }
    receipts.write_requirement_receipts(receipts.requirement_receipt_path(tmp_path, 1), doc)
    assert _check(tmp_path, item, BROTHER)["details"]["requirement_receipts"][0]["requirement"] == "confirmed"
    item["requires"] = {"Case": "Gen"}
    assert _check(tmp_path, item, BROTHER)["details"]["requirement_receipts"][0]["requirement"] == "not_checked"


def test_missing_vesum_fails_as_named_check_not_exception(tmp_path: Path) -> None:
    # The runner wraps the lookup's FileNotFoundError as a check-7 engine failure;
    # this direct checker still exposes the missing dependency for that wrapper.
    item = {
        "kind": "orthography",
        "mode": "orthography",
        "sentence": "м___яч",
        "options": ["'", ""],
        "answer": "'",
        "target_record": "W-5",
    }
    ball = _record(5, "м'яч", [("м'яч", "noun:inanim:m:v_naz")])
    with pytest.raises(FileNotFoundError):
        _check(
            tmp_path,
            item,
            ball,
            typ="fill-in",
            lookup=lambda _words: (_ for _ in ()).throw(FileNotFoundError("VESUM missing")),
        )
