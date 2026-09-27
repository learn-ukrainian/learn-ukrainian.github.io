"""A1 post-resolution choice checks using independently inspected VESUM forms.

VESUM source locations: брат 487702-487719, книга 2614480-2614493,
бути 542216-542245, читати 6561736-6561760, м'яч 3260520-3260537.
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
        ("читав", "verb:imperf:past:m"),
    ],
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
