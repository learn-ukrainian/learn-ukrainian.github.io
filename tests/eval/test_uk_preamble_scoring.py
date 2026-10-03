"""Scorer and response-validation tests on a hand-built mini set (#9623)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import scripts.delegate as delegate
from scripts.eval.uk_preamble.common import HarnessError
from scripts.eval.uk_preamble.dataset import load_set, parse_variant, protocol_shortfalls
from scripts.eval.uk_preamble.prompts import (
    build_prompt,
    extract_json,
    review_payload,
    validate_response,
    writing_payload,
)
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
    assert result["unlogged_changes"] is False


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
    result = score_review_item(item, answer(item.text, [correction], corrected=item.text))
    assert result["errors"][1]["hit"] is True
    assert result["unlogged_changes"] is True  # corrected_text was left unchanged


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


def test_overlapping_corrections_fail_the_item_but_keep_its_errors(eval_set):
    item = _item(eval_set, "R3")
    result = score_review_item(
        item,
        answer(
            item.text,
            [fix(item.text, "являється слідуючим", "є наступним"), fix(item.text, "слідуючим", "наступним")],
            corrected=item.text,
        ),
    )
    assert result["failed"] is True
    assert len(result["errors"]) == 2 and result["hits"] == 0


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

    from scripts.eval.uk_preamble.dataset import ReviewItem, Span

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
def test_prompts_pass_the_read_only_write_shape_guard(eval_set, kind):
    payload = review_payload(eval_set.review) if kind == "review" else writing_payload(eval_set.writing)
    assert not delegate._has_write_directive(build_prompt(kind, payload))


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
