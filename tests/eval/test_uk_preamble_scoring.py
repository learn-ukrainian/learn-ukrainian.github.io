"""Scorer and response-validation tests on a hand-built mini set (#9623)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import scripts.delegate as delegate
from scripts.eval.uk_preamble.common import HarnessError
from scripts.eval.uk_preamble.dataset import ReviewItem, Span, load_set
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


# --------------------------------------------------------------------------- hits and misses (mini set)
# Primary counts come from corrected_text alone; the oracle cases of the contract live in
# test_uk_preamble_scoring_contract.py. These cover the mini set and the logging diagnostics.


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
    assert result["logging"] == {
        "change_units": 2,
        "claimed_change_units": 2,
        "claims": 2,
        "applied_claims": 2,
        "unapplied_claims": 0,
        "noop_claims": 0,
        "unanchored_claims": 0,
        "protected_accused_unchanged": 0,
    }


# --------------------------------------------------------------------------- finding 2: corrections must be applied


def test_logged_correction_not_applied_in_corrected_text_is_not_a_hit(eval_set):
    """Reviewer probe: the correct fix is logged but the original error stays in corrected_text."""
    item = _item(eval_set, "R1")
    result = score_review_item(
        item, answer(item.text, [fix(item.text, "приймав участь", "брав участь")], corrected=item.text)
    )
    assert result["hits"] == 0 and not result["failed"]
    assert result["false_alarms"] == 0
    assert (result["logging"]["applied_claims"], result["logging"]["unapplied_claims"]) == (0, 1)


# --------------------------------------------------------------------------- false alarms


# --------------------------------------------------------------------------- adjacent seeds


# --------------------------------------------------------------------------- style suggestions


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
