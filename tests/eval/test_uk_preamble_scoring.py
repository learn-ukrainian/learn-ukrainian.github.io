"""Scorer and response-validation tests on a hand-built mini set (#9623)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import scripts.delegate as delegate
from scripts.eval.uk_preamble.common import HarnessError
from scripts.eval.uk_preamble.dataset import ReviewItem, Span, load_set, parse_variant, protocol_shortfalls
from scripts.eval.uk_preamble.prompts import (
    build_prompt,
    extract_json,
    review_payload,
    validate_response,
    writing_payload,
)
from scripts.eval.uk_preamble.runner import render, rules_block
from scripts.eval.uk_preamble.scoring import score_review_item


@pytest.fixture
def eval_set(tmp_path: Path, mini_set_dict: dict[str, Any]):
    path = tmp_path / "set.json"
    path.write_text(json.dumps(mini_set_dict, ensure_ascii=False), encoding="utf-8")
    return load_set(path)


def _item(eval_set, item_id: str):
    return eval_set.review_by_id()[item_id]


def fix(text: str, fragment: str, replacement: str, *, occurrence: int = 0, offset_shift: int = 0) -> dict[str, Any]:
    start = -1
    for _ in range(occurrence + 1):
        start = text.index(fragment, start + 1)
    return {
        "span": fragment,
        "start": start + offset_shift,
        "end": start + len(fragment) + offset_shift,
        "correction": replacement,
        "error_type": "other",
        "evidence": "test",
    }


def answer(text: str, corrections: list[dict[str, Any]], style: list[dict[str, Any]] | None = None, corrected=None):
    if corrected is None:
        corrected = text
        for c in sorted(corrections, key=lambda c: c["start"], reverse=True):
            corrected = corrected[: c["start"]] + c["correction"] + corrected[c["end"] :]
    return {"id": "x", "corrected_text": corrected, "corrections": corrections, "style_suggestions": style or []}


# --------------------------------------------------------------------------- hits and misses


def test_exact_hits_and_accepted_alternative(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(
        item,
        answer(
            item.text,
            [fix(item.text, "приймав участь", "брав участь"), fix(item.text, "на протязі години", "упродовж години")],
        ),
    )
    assert result["hits"] == 2
    assert [e["hit"] for e in result["errors"]] == [True, True]
    assert result["false_alarms"] == 0
    assert (result["unlogged_change_units"], result["unapplied_logged_units"]) == (0, 0)


def test_miss_when_error_untouched(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(item, answer(item.text, [fix(item.text, "приймав участь", "брав участь")]))
    assert result["hits"] == 1
    assert {e["id"]: e["hit"] for e in result["errors"]} == {"R1-e1": True, "R1-e2": False}


def test_wrong_correction_on_error_span_is_miss_not_false_alarm(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(item, answer(item.text, [fix(item.text, "на протязі", "впродовж часу")]))
    assert result["hits"] == 0
    assert result["wrong_corrections"] == 1
    assert result["false_alarms"] == 0


def test_wider_span_with_unchanged_context_still_hits(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(item, answer(item.text, [fix(item.text, "я приймав участь у", "я брав участь у")]))
    assert result["errors"][0]["hit"] is True
    assert result["false_alarms"] == 0


def test_bad_offsets_relocated_by_span_and_whitespace_apostrophe_normalised(eval_set):
    item = _item(eval_set, "R1")
    correction = fix(item.text, "на протязі години", "протягом  години", offset_shift=5)
    corrected = item.text.replace("на протязі години", "протягом   години")
    result = score_review_item(item, answer(item.text, [correction], corrected=corrected))
    assert result["errors"][1]["hit"] is True
    assert result["false_alarms"] == 0 and result["unlogged_change_units"] == 0


# --------------------------------------------------------------------------- finding 2: corrections must be applied


def test_logged_correction_not_applied_in_corrected_text_is_not_a_hit(eval_set):
    """Reviewer probe: the correct fix is logged but the original error stays in corrected_text."""
    item = _item(eval_set, "R1")
    result = score_review_item(
        item, answer(item.text, [fix(item.text, "приймав участь", "брав участь")], corrected=item.text)
    )
    assert result["hits"] == 0 and not result["failed"]
    assert result["unapplied_logged_units"] == 1 and result["false_alarms"] == 0


def test_silent_change_to_protected_text_counts_although_unlogged(eval_set):
    """Reviewer probe: a logged correct fix plus a silent replacement of protected text."""
    item = _item(eval_set, "R1")
    corrected = item.text.replace("приймав участь", "брав участь").replace("пляцки", "пироги")
    result = score_review_item(
        item, answer(item.text, [fix(item.text, "приймав участь", "брав участь")], corrected=corrected)
    )
    assert result["hits"] == 1
    assert (result["fa_protected"], result["protected_touched"]) == (1, ["R1-p1"])
    assert result["unlogged_change_units"] == 1


def test_unlogged_fix_in_corrected_text_is_a_hit(eval_set):
    item = _item(eval_set, "R1")
    corrected = item.text.replace("на протязі години", "протягом години")
    result = score_review_item(item, answer(item.text, [], corrected=corrected))
    assert {e["id"]: e["hit"] for e in result["errors"]} == {"R1-e1": False, "R1-e2": True}
    assert result["false_alarms"] == 0 and result["unlogged_change_units"] == 1


def test_whitespace_and_apostrophe_variants_in_corrected_text_change_nothing(eval_set):
    item = _item(eval_set, "R2")
    corrected = "  " + item.text.replace("п'ятницю", "пʼятницю").replace(" ", "  ") + "\n"
    result = score_review_item(item, answer(item.text, [], corrected=corrected))
    assert result["false_alarms"] == 0 and result["unlogged_change_units"] == 0


def test_apostrophe_only_change_is_noop_not_false_alarm(eval_set):
    item = _item(eval_set, "R2")
    result = score_review_item(item, answer(item.text, [fix(item.text, "п'ятницю", "п’ятницю")]))
    assert result["noop_corrections"] == 1
    assert result["false_alarms"] == 0
    assert result["protected_touched"] == []


# --------------------------------------------------------------------------- false alarms


def test_change_to_protected_span_is_false_alarm_even_in_item_with_errors(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(
        item,
        answer(item.text, [fix(item.text, "приймав участь", "брав участь"), fix(item.text, "пляцки", "пироги")]),
    )
    assert result["hits"] == 1
    assert result["fa_protected"] == 1
    assert result["protected_touched"] == ["R1-p1"]
    assert result["false_alarms"] == 1


def test_change_to_other_correct_text_is_false_alarm(eval_set):
    item = _item(eval_set, "R2")
    result = score_review_item(item, answer(item.text, [fix(item.text, "допомогу", "поміч")]))
    assert (result["fa_other"], result["fa_protected"], result["false_alarms"]) == (1, 0, 1)


def test_unanchored_correction_is_unsupported_accusation(eval_set):
    item = _item(eval_set, "R2")
    bogus = {"span": "неіснуючий", "start": 0, "end": 10, "correction": "x", "error_type": "other", "evidence": "?"}
    result = score_review_item(item, answer(item.text, [bogus], corrected=item.text))
    assert (result["fa_unanchored"], result["false_alarms"]) == (1, 1)


def test_insertion_next_to_protected_span_does_not_touch_it(eval_set):
    item = _item(eval_set, "R2")
    result = score_review_item(item, answer(item.text, [fix(item.text, "Петре", "Петре!")]))
    assert result["fa_protected"] == 0
    assert result["fa_other"] == 1


# --------------------------------------------------------------------------- overlapping spans


def test_one_correction_covering_two_seeded_errors_hits_both(eval_set):
    item = _item(eval_set, "R3")
    result = score_review_item(item, answer(item.text, [fix(item.text, "являється слідуючим", "є наступним")]))
    assert result["hits"] == 2


def test_one_correction_covering_two_errors_fixing_one_hits_one(eval_set):
    item = _item(eval_set, "R3")
    result = score_review_item(item, answer(item.text, [fix(item.text, "являється слідуючим", "є слідуючим")]))
    assert {e["id"]: e["hit"] for e in result["errors"]} == {"R3-e1": True, "R3-e2": False}
    assert result["false_alarms"] == 0


def test_overlapping_logged_corrections_are_scored_from_the_corrected_text(eval_set):
    item = _item(eval_set, "R3")
    corrections = [fix(item.text, "являється слідуючим", "є наступним"), fix(item.text, "слідуючим", "наступним")]
    unapplied = score_review_item(item, answer(item.text, corrections, corrected=item.text))
    assert unapplied["failed"] is False and unapplied["hits"] == 0
    assert unapplied["unapplied_logged_units"] == 2
    applied = score_review_item(item, answer(item.text, corrections, corrected="Цей пункт є наступним кроком."))
    assert applied["hits"] == 2 and applied["false_alarms"] == 0 and applied["unapplied_logged_units"] == 0


# --------------------------------------------------------------------------- finding 3: packaging does not matter

PACKAGED = "Цей пункт являється без сумніву слідуючим кроком."


def _packaged_item() -> ReviewItem:
    def span(fragment: str, ident: str, accepted=()) -> Span:
        start = PACKAGED.index(fragment)
        return Span(ident, start, start + len(fragment), fragment, "lexical-russianism", tuple(accepted))

    errors = (span("являється", "e1", ["є"]), span("слідуючим", "e2", ["наступним"]))
    return ReviewItem("P", PACKAGED, errors, (span("без сумніву", "p1"),))


_KEYS = ("hits", "fa_protected", "fa_other", "fa_unanchored", "wrong_corrections")


@pytest.mark.parametrize(
    ("corrected", "packagings", "expected"),
    [
        # Two errors fixed around unchanged protected text: no false alarm however grouped.
        (
            "Цей пункт є без сумніву наступним кроком.",
            [
                [("являється без сумніву слідуючим", "є без сумніву наступним")],
                [("являється", "є"), ("слідуючим", "наступним")],
                [],
            ],
            (2, 0, 0, 0, 0),
        ),
        # An error fix combined with a replacement of unprotected correct text: one false alarm however grouped.
        (
            "Цей пункт є без сумніву наступним етапом.",
            [
                [("являється без сумніву слідуючим кроком", "є без сумніву наступним етапом")],
                [("являється", "є"), ("слідуючим кроком", "наступним етапом")],
                [("являється", "є"), ("слідуючим", "наступним"), ("кроком", "етапом")],
                [],
            ],
            (2, 0, 1, 0, 0),
        ),
        # A collateral rewrite of protected text inside one combined correction.
        (
            "Цей пункт є безперечно наступним кроком.",
            [
                [("являється без сумніву слідуючим", "є безперечно наступним")],
                [("являється", "є"), ("без сумніву", "безперечно"), ("слідуючим", "наступним")],
            ],
            (2, 1, 0, 0, 0),
        ),
    ],
)
def test_counts_do_not_depend_on_how_corrections_are_grouped(corrected, packagings, expected):
    item = _packaged_item()
    for packaging in packagings:
        corrections = [fix(PACKAGED, span, replacement) for span, replacement in packaging]
        result = score_review_item(item, answer(PACKAGED, corrections, corrected=corrected))
        assert tuple(result[k] for k in _KEYS) == expected, packaging


def _loggings(text: str, edits: list[tuple[int, int, str]]) -> list[list[dict[str, Any]]]:
    """Every schema-valid way of logging ``edits`` (disjoint, in source order) as corrections that apply them.

    Unlogged; each edit alone in every span that reaches into its neighbours' gaps
    (the others logged minimally); and one correction over every span covering all edits.
    """

    def entry(start: int, end: int, replacement: str) -> dict[str, Any]:
        return {
            "span": text[start:end],
            "start": start,
            "end": end,
            "correction": replacement,
            "error_type": "other",
            "evidence": "test",
        }

    def minimal(i: int) -> dict[str, Any]:
        return entry(*edits[i])

    loggings: list[list[dict[str, Any]]] = [[], [minimal(i) for i in range(len(edits))]]
    for i, (e_start, e_end, replacement) in enumerate(edits):
        left = edits[i - 1][1] if i else 0
        right = edits[i + 1][0] if i + 1 < len(edits) else len(text)
        for start in range(left, e_start + 1):
            for end in range(e_end, right + 1):
                wide = entry(start, end, text[start:e_start] + replacement + text[e_end:end])
                loggings.append([wide if j == i else minimal(j) for j in range(len(edits))])
    corrected = _apply(text, edits)
    for start in range(edits[0][0] + 1):
        for end in range(edits[-1][1], len(text) + 1):
            loggings.append([entry(start, end, corrected[start : len(corrected) - (len(text) - end)])])
    return loggings


def _apply(text: str, edits: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in reversed(edits):
        text = text[:start] + replacement + text[end:]
    return text


def _span_item(text: str, errors: list[tuple[str, list[str]]], protected: list[str]) -> ReviewItem:
    def span(fragment: str, ident: str, kind: str, accepted=()) -> Span:
        start = text.index(fragment)
        return Span(ident, start, start + len(fragment), fragment, kind, tuple(accepted))

    return ReviewItem(
        "Q",
        text,
        tuple(span(fragment, f"e{i}", "lexical-russianism", accepted) for i, (fragment, accepted) in enumerate(errors)),
        tuple(span(fragment, f"p{i}", "regional") for i, fragment in enumerate(protected)),
    )


_SCORE_KEYS = ("hits", "fa_protected", "fa_other", "fa_unanchored", "false_alarms", "wrong_corrections")


def test_reviewer_probe_safe_to_safer_scores_the_same_as_an_insertion():
    """Round 2: ``bad safe`` -> ``good safer`` gave 1 false alarm as ``safe -> safer`` and 2 as an insertion."""
    item = _span_item("bad safe", [("bad", ["good"])], [])
    fix_bad = fix("bad safe", "bad", "good")
    as_word = [fix_bad, fix("bad safe", "safe", "safer")]
    as_insertion = [fix_bad, {**fix("bad safe", "safe", "r"), "span": "", "start": 8, "end": 8}]
    for corrections in (as_word, as_insertion):
        result = score_review_item(item, answer("bad safe", corrections, corrected="good safer"))
        assert (result["hits"], result["false_alarms"], result["fa_other"]) == (1, 1, 1), corrections
        assert (result["unlogged_change_units"], result["unapplied_logged_units"]) == (0, 0)


@pytest.mark.parametrize(
    ("text", "errors", "protected", "edits", "expected"),
    [
        # The reviewer's probe: an error fix plus a suffix insertion on a correct word.
        ("bad safe", [("bad", ["good"])], [], [(0, 3, "good"), (8, 8, "r")], (1, 0, 1, 0, 1, 0)),
        # Error fix, a comma inserted between correct words, and a suffix grown inside protected text.
        (
            "Цей пункт являється без сумніву слідуючим кроком.",
            [("являється", ["є"]), ("слідуючим", ["наступним"])],
            ["без сумніву"],
            [(10, 19, "є"), (31, 31, "в"), (32, 41, "наступним")],
            (2, 1, 0, 0, 1, 0),
        ),
        # A comma error fixed by insertion and a correct word deleted.
        ("Я знаю що він прийде.", [], [], [(6, 6, ","), (9, 13, "")], (0, 0, 2, 0, 2, 0)),
        # A wrong correction of an error (a miss, not a false alarm) and a punctuation swap.
        (
            "Цей пункт являється кроком.",
            [("являється", ["є"])],
            [],
            [(10, 19, "буде"), (26, 27, "!")],
            (0, 0, 1, 0, 1, 1),
        ),
    ],
)
def test_every_way_of_logging_an_applied_edit_scores_the_same(text, errors, protected, edits, expected):
    item = _span_item(text, errors, protected)
    corrected = _apply(text, edits)
    loggings = _loggings(text, edits)
    assert len(loggings) > len(edits) + 2
    for corrections in loggings:
        result = score_review_item(item, answer(text, corrections, corrected=corrected))
        assert tuple(result[k] for k in _SCORE_KEYS) == expected, corrections
        if corrections:
            assert result["unapplied_logged_units"] == 0, corrections


def test_unapplied_accusation_of_correct_text_counts_once_however_grouped():
    item = _packaged_item()
    one = [fix(PACKAGED, "пункт являється", "розділ являється")]
    two = [fix(PACKAGED, "пункт", "розділ"), fix(PACKAGED, "пункт", "розділ")]
    for corrections in (one, two):
        result = score_review_item(item, answer(PACKAGED, corrections, corrected=PACKAGED))
        assert (result["fa_other"], result["unapplied_logged_units"]) == (1, 1)


def test_insertion_error_hit_by_comma(eval_set):
    item = _item(eval_set, "R4")
    result = score_review_item(item, answer(item.text, [fix(item.text, "знаю", "знаю,")]))
    assert result["hits"] == 1
    assert result["false_alarms"] == 0


# --------------------------------------------------------------------------- style suggestions


def test_style_suggestions_are_not_errors_or_false_alarms(eval_set):
    item = _item(eval_set, "R1")
    style = [
        {
            "span": "пляцки",
            "start": item.text.index("пляцки"),
            "end": item.text.index("пляцки") + 6,
            "suggestion": "тістечка",
            "reason": "нейтральніше",
        },
        {
            "span": "на протязі години",
            "start": item.text.index("на протязі"),
            "end": item.text.index("на протязі") + len("на протязі години"),
            "suggestion": "протягом години",
            "reason": "x",
        },
    ]
    result = score_review_item(item, answer(item.text, [], style=style))
    assert result["hits"] == 0
    assert result["false_alarms"] == 0
    assert result["style"] == {"total": 2, "on_protected": 1, "on_error": 1, "unanchored": 0}


def test_newly_introduced_invalid_forms_counted():
    class Sources:
        def invalid_forms(self, text: str) -> set[str]:
            return {w for w in ("бравв",) if w in text}

        def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
            raise AssertionError

    text = "Я приймав участь."
    item = ReviewItem("R", text, (Span("e", 2, 16, "приймав участь", "lexical-russianism", ("брав участь",)),), ())
    result = score_review_item(item, answer(text, [fix(text, "приймав", "бравв")]), sources=Sources())
    assert result["new_invalid_forms"] == ["бравв"]


def test_failed_item_counts_errors_as_misses(eval_set):
    item = _item(eval_set, "R1")
    result = score_review_item(item, None, "schema violation")
    assert result["failed"] is True and result["reason"] == "schema violation"
    assert len(result["errors"]) == 2 and not any(e["hit"] for e in result["errors"])


# --------------------------------------------------------------------------- response validation


def _review_entry(item_id: str, text: str) -> dict[str, Any]:
    return {"id": item_id, "corrected_text": text, "corrections": [], "style_suggestions": []}


def test_validation_accepts_fenced_json_and_flags_each_bad_item():
    good = _review_entry("A", "текст")
    extra = {**_review_entry("B", "текст"), "note": "extra field"}
    bad_type = {
        **_review_entry("C", "текст"),
        "corrections": [{"span": "т", "start": "0", "end": 1, "correction": "", "error_type": "", "evidence": ""}],
    }
    dup = _review_entry("D", "текст")
    response = "Here you go:\n```json\n" + json.dumps({"items": [good, extra, bad_type, dup, dup]}) + "\n```"
    results = {r.item_id: r for r in validate_response("review", response, ["A", "B", "C", "D", "E"])}
    assert results["A"].entry == good and results["A"].error is None
    assert "schema violation" in results["B"].error
    assert "corrections/0/start" in results["C"].error
    assert "2 times" in results["D"].error
    assert results["E"].error == "item missing from response"


@pytest.mark.parametrize("response", [None, "not json at all", '{"answer": []}', "[1, 2]"])
def test_unusable_response_fails_every_item_never_drops(response):
    results = validate_response("writing", response, ["W1", "W2"])
    assert [r.item_id for r in results] == ["W1", "W2"]
    assert all(r.entry is None and r.error for r in results)


def test_extract_json_prefers_whole_text_then_fence_then_braces():
    assert extract_json('{"items": []}') == {"items": []}
    assert extract_json('prose {"items": [1]} more prose') == {"items": [1]}


# --------------------------------------------------------------------------- prompts and set loading


def test_variants_differ_only_by_leading_preamble(eval_set):
    for kind, payload in (("review", review_payload(eval_set.review)), ("writing", writing_payload(eval_set.writing))):
        base = build_prompt(kind, payload)
        with_preamble = build_prompt(kind, payload, "Ти — редактор.\n")
        assert with_preamble == "Ти — редактор.\n\n" + base


@pytest.mark.parametrize("kind", ["review", "writing", "judge"])
def test_rendered_prompts_pass_the_read_only_write_intent_guard(eval_set, kind):
    payload = review_payload(eval_set.review) if kind == "review" else writing_payload(eval_set.writing)
    prompt = render(build_prompt(kind, payload, "Ти — редактор."), rules_block())
    assert delegate._read_only_write_intent_error(mode="read-only", prompt=prompt) is None


def test_set_validation_rejects_span_mismatch_and_overlap(tmp_path: Path, mini_set_dict):
    mini_set_dict["review"][0]["errors"][0]["span"] = "інше"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(mini_set_dict, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(HarnessError, match="span does not equal"):
        load_set(path)


def test_set_validation_rejects_error_overlapping_protected(tmp_path: Path, mini_set_dict):
    first = mini_set_dict["review"][0]
    first["protected"][0].update(first["errors"][0] | {"id": "R1-p1", "kind": "x"})
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(mini_set_dict, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(HarnessError, match="overlaps protected"):
        load_set(path)


def test_protocol_minimums_reported(eval_set):
    problems = protocol_shortfalls(eval_set)
    assert any("seeded errors" in p for p in problems)
    assert any("A2" in p and "C1" in p for p in problems)


def test_variant_parsing(tmp_path: Path):
    preamble = tmp_path / "p.md"
    preamble.write_text("Ти — редактор.\n", encoding="utf-8")
    variant = parse_variant(f"adapted-v2={preamble}")
    assert (variant.label, variant.preamble) == ("adapted-v2", "Ти — редактор.")
    assert parse_variant("none").preamble is None
    with pytest.raises(HarnessError):
        parse_variant("none=whatever")
