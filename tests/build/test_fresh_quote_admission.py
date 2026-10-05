"""Plan-listed source quotes are display occurrences, not learner vocabulary."""

from __future__ import annotations

import copy

import pytest

from scripts.build.fresh import assemble, runner
from scripts.curriculum.resolver import codes, questions, receipts
from scripts.curriculum.resolver.inputs import Allowlist, ExpandedDocument
from scripts.curriculum.resolver.stream import resolve
from tests.build.test_fresh_assemble import make_text_record
from tests.build.test_fresh_runner import _fixture, _FixtureSources, _run_contract

pytestmark = pytest.mark.reads_content


def _quote_fixture():
    draft, plan, pack, words = _fixture()
    lesson = plan["lessons"][0]
    lesson["n"] = draft["lesson"]["n"] = 2
    lesson["inventory"]["phonetics"] = {"letters": ["А", "О", "У", "И"], "sounds": []}
    for sid, numbers in (("s3", range(6, 10)), ("s4", range(22, 26))):
        refs = []
        for number, letter in zip(numbers, lesson["inventory"]["phonetics"]["letters"], strict=True):
            record = make_text_record(number, f"Бачу {letter}, {letter.lower()}. Чую [{letter.lower()}].")
            pack["texts"].append(record)
            refs.append(record["id"])
        step = copy.deepcopy(lesson["steps"][0])
        step.update(id=sid, evidence=refs)
        lesson["steps"].append(step)
        draft["steps"].append({"id": sid, "blocks": [{"kind": "quote", "ref": ref} for ref in refs]})
    return draft, plan, pack, words


def _resolve_quote_fixture(draft, plan, pack, words, *, expanded=None, provenance=None):
    if expanded is None:
        expanded, provenance = assemble.assemble_expanded_document(
            draft, plan, pack, words, "a1", "sample-slug", 2
        )
    doc = ExpandedDocument.from_data(expanded)
    lesson = plan["lessons"][0]
    admitted = assemble.plan_quote_units(doc, provenance, draft, lesson, pack)
    allowed = Allowlist.from_records(words["words"], letters=lesson["inventory"]["phonetics"]["letters"])
    stream = resolve(doc, allowed, _FixtureSources(), source_quote_units=admitted)
    return doc, allowed, stream, admitted


def test_lesson_2_listed_source_models_pass_check_7_and_leave_no_selections(tmp_path, monkeypatch):
    draft, plan, pack, words = _quote_fixture()
    doc, allowed, stream, admitted = _resolve_quote_fixture(draft, plan, pack, words)
    assert len(admitted) == 8
    displayed = [token for token in stream.tokens if token["token"] in {"Бачу", "Чую"}]
    assert len(displayed) == 16
    assert all(token["class"] == "skipped:source_quote" for token in displayed)
    assert all(token["candidates"] == [] and token["selected"] is None for token in displayed)
    assert runner.check_7_deterministic(stream, plan["lessons"][0])["status"] == "passed"
    batch = questions.build_questions(stream, doc, allowed)
    receipt = receipts.build_receipts(stream, batch, {}, None)
    assert all(token["selected"] is None for token in receipt["tokens"] if token["token"] in {"Бачу", "Чую"})
    assert batch["questions"] == []
    # Exercise the production runner's wiring and receipt/render consumers.
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, n=2)
    assert report["passed"] is True
    receipt = receipts.check_receipts(state / "lesson-2.resolutions.yaml")
    assert {token["class"] for token in receipt["tokens"] if token["token"] in {"Бачу", "Чую"}} == {
        "skipped:source_quote"
    }


@pytest.mark.parametrize("text", ["Бачу", "Чую", "{{uk:Бачу}}", "«Чую»"])
def test_same_word_outside_quote_still_fails_check_7(text):
    draft, plan, pack, words = _quote_fixture()
    draft["steps"][0]["blocks"][0]["text"] += " " + text
    _, _, stream, _ = _resolve_quote_fixture(draft, plan, pack, words)
    row = runner.check_7_deterministic(stream, plan["lessons"][0])
    assert (row["status"], row["code"], row["layer"]) == ("failed", "lemma_outside_state", "writer")
    assert row["step"] == "s1"


@pytest.mark.parametrize("mutation", ["unlisted", "wrong_step", "prose", "example", "text", "substring",
                                         "provenance_text", "provenance_ref", "provenance_kind", "offset",
                                         "locator", "partial_spans", "activity", "role", "missing_record"])
def test_quote_admission_requires_listed_exact_whole_record_occurrence(mutation):
    draft, plan, pack, words = _quote_fixture()
    expanded, provenance = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 2)
    index = next(i for i, unit in enumerate(expanded["units"]) if unit["step"] == "s3")
    unit, span = expanded["units"][index], provenance["spans"][index]
    ref = span["ref"]
    if mutation == "unlisted":
        plan["lessons"][0]["steps"][1]["evidence"].remove(ref)
    elif mutation == "wrong_step":
        plan["lessons"][0]["steps"][1]["evidence"].remove(ref)
        plan["lessons"][0]["steps"][2]["evidence"].append(ref)
    elif mutation in {"prose", "example"}:
        draft["steps"][1]["blocks"][0]["kind"] = mutation
    elif mutation in {"text", "substring"}:
        unit["text"] = span["text"] = unit["text"] + " Бачу" if mutation == "text" else "Бачу"
        span["end"] = len(unit["text"])
    elif mutation == "provenance_text":
        span["text"] += " Бачу"
    elif mutation == "provenance_ref":
        span["ref"] = "T-99"
    elif mutation == "provenance_kind":
        span["record_kind"] = "example"
    elif mutation == "offset":
        span["start"] = 1
    elif mutation == "locator":
        span["block"] = 99
    elif mutation == "partial_spans":
        provenance["spans"].pop()
    elif mutation == "activity":
        unit["activity"] = span["activity"] = "a1"
    elif mutation == "role":
        unit["role"] = span["role"] = "item_prompt"
    elif mutation == "missing_record":
        pack["texts"] = [record for record in pack["texts"] if record["id"] != ref]
    _, _, stream, admitted = _resolve_quote_fixture(draft, plan, pack, words, expanded=expanded, provenance=provenance)
    assert index not in admitted
    assert any(failure["code"] == codes.LEMMA_OUTSIDE_STATE and failure["token"] == "Бачу"
               for failure in stream.failures)


@pytest.mark.parametrize("role", ["item_prompt", "item_answer", "instruction"])
def test_source_quote_admission_never_covers_scored_units(role):
    draft, plan, pack, words = _quote_fixture()
    expanded, provenance = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 2)
    expanded["units"].append({"tab": "vpravy", "step": "s3", "activity": "a1", "item": 0,
                              "block": "prompt", "role": role, "text": "Бачу"})
    provenance["spans"].append({**provenance["spans"][-1], **expanded["units"][-1]})
    _, _, stream, _ = _resolve_quote_fixture(draft, plan, pack, words, expanded=expanded, provenance=provenance)
    row = runner.check_7_deterministic(stream, plan["lessons"][0])
    assert (row["status"], row["code"], row["layer"], row["activity"]) == (
        "failed", "lemma_outside_state", "writer", "a1"
    )


def test_source_quote_does_not_satisfy_core_vocabulary_requirement():
    draft, plan, pack, words = _quote_fixture()
    # Display-only admission cannot stand in for a missing core record.
    _, _, stream, _ = _resolve_quote_fixture(draft, plan, pack, words)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"].append({"evidence": "W-99", "forms": []})
    row = runner.check_7_deterministic(stream, plan["lessons"][0])
    assert (row["status"], row["reason"]) == ("failed", "core_record_absent")
    assert row["token"] == "W-99"


def test_already_allowed_quote_words_keep_their_normal_resolution():
    draft, plan, pack, words = _quote_fixture()
    pack["texts"][0]["quote"] = "слово"
    _, _, stream, _ = _resolve_quote_fixture(draft, plan, pack, words)
    token = next(token for token in stream.tokens if token["unit"]["step"] == "s3" and token["token"] == "слово")
    assert token["class"] == codes.RESOLVED
    assert token["selected"]["record"] == "W-1"


def test_resolver_without_engine_quote_verification_stays_strict():
    draft, plan, pack, words = _quote_fixture()
    doc, allowed, _, _ = _resolve_quote_fixture(draft, plan, pack, words)
    stream = resolve(doc, allowed, _FixtureSources())
    assert {failure["token"] for failure in stream.failures} == {"Бачу", "Чую"}
