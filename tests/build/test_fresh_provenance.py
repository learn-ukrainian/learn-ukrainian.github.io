"""Tests for engine E3c-1: provenance kinds and review layer assignment."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.build.fresh import assemble, runner
from scripts.build.fresh.assemble import PROVENANCE_SCHEMA_PATH, get_provenance_validator
from tests.build.test_fresh_assemble import (
    validate_fixture_draft,
    validate_fixture_pack,
    validate_fixture_plan,
    validate_fixture_words,
)
from tests.build.test_fresh_runner import _fixture, _run_contract

pytestmark = pytest.mark.reads_content


def test_live_runner_error_correction_item_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    pack["errors"] = [
        {
            "id": "E-001",
            "source": {"table": "ua_gec_errors", "id": 1},
            "incorrect": "слове",
            "correct": "слово",
            "error_type": "form",
            "pattern": "fixture",
        }
    ]
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [
        {
            "id": "a1",
            "type": "error-correction",
            "placement": "inline",
            "focus": "Correct",
            "error_refs": ["E-001"],
        }
    ]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Correct the error",
            "items": [
                {
                    "sentence": "слове",
                    "error": "слове",
                    "correction": "слово",
                    "explanation": "Correct",
                    "error_ref": "E-001",
                }
            ],
        }
    ]
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report

    prov_path = state / "lesson-1.provenance.yaml"
    assert prov_path.is_file()
    prov_doc = yaml.safe_load(prov_path.read_text(encoding="utf-8"))

    validator = get_provenance_validator()
    validator.validate(prov_doc)

    spans = prov_doc["spans"]
    e_spans = [s for s in spans if s.get("ref") == "E-001"]
    assert len(e_spans) >= 2

    inc_span = next(s for s in e_spans if s["record_side"] == "incorrect")
    assert inc_span["text"] == "слове"
    assert inc_span["source"] == "record"
    assert inc_span["record_kind"] == "error"
    assert inc_span["option_origin"] is None
    assert inc_span["is_key"] is None

    corr_span = next(s for s in e_spans if s["record_side"] == "correct")
    assert corr_span["text"] == "слово"
    assert corr_span["source"] == "record"
    assert corr_span["record_kind"] == "error"
    assert corr_span["option_origin"] is None
    assert corr_span["is_key"] is None


def test_live_runner_form_choice_item_provenance_rendered_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    form = {
        **words["words"][0]["forms"][0],
        "form": "слова",
        "stressed": "слова\u0301",
        "tags": "noun:inanim:n:v_rod",
    }
    words["words"][0]["forms"].append(form)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].append(form["tags"])
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "____",
                    "answer": "слово",
                    "options": ["слово", "слова"],
                    "explanation": "Choose",
                    "mode": "form-choice",
                    "record": "W-1",
                    "answer_tags": words["words"][0]["forms"][0]["tags"],
                }
            ],
        }
    ]
    validate_fixture_words(words)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report

    prov_path = state / "lesson-1.provenance.yaml"
    prov_doc = yaml.safe_load(prov_path.read_text(encoding="utf-8"))
    validator = get_provenance_validator()
    validator.validate(prov_doc)

    opt_spans = [
        s
        for s in prov_doc["spans"]
        if s.get("tab") == "vpravy"
        and s.get("activity") == "a1"
        and isinstance(s.get("block"), str)
        and s["block"].startswith("opt_")
    ]
    assert len(opt_spans) == 2

    key_opt = next(s for s in opt_spans if s["is_key"] is True)
    assert key_opt["text"] == "сло\u0301во"
    assert key_opt["source"] == "record"
    assert key_opt["ref"] == "W-1"
    assert key_opt["record_kind"] == "word"
    assert key_opt["option_origin"] == "store"
    assert key_opt["record_side"] is None

    dist_opt = next(s for s in opt_spans if s["is_key"] is False)
    assert dist_opt["text"] == "слова\u0301"
    assert dist_opt["source"] == "record"
    assert dist_opt["ref"] == "W-1"
    assert dist_opt["record_kind"] == "word"
    assert dist_opt["option_origin"] == "store"
    assert dist_opt["record_side"] is None


def test_live_runner_quiz_typed_distractors_provenance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Quiz instruction",
            "items": [
                {
                    "question": "слово",
                    "options": ["слово", "слова"],
                    "correct": 0,
                    "explanation": "Explanation",
                }
            ],
        }
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report

    prov_path = state / "lesson-1.provenance.yaml"
    prov_doc = yaml.safe_load(prov_path.read_text(encoding="utf-8"))
    validator = get_provenance_validator()
    validator.validate(prov_doc)

    opt_spans = [
        s
        for s in prov_doc["spans"]
        if s.get("tab") == "vpravy"
        and s.get("activity") == "a1"
        and isinstance(s.get("block"), str)
        and s["block"].startswith("opt_")
    ]
    assert len(opt_spans) == 2
    for s in opt_spans:
        assert s["source"] == "writer_prose"
        assert s["ref"] is None
        assert s["record_kind"] is None
        assert s["option_origin"] == "writer_typed"

    keys = [s for s in opt_spans if s["is_key"] is True]
    assert len(keys) == 1
    assert keys[0]["text"] == "слово"

    distractors = [s for s in opt_spans if s["is_key"] is False]
    assert len(distractors) == 1
    assert distractors[0]["text"] == "слова"


def test_check_4_error_text_mismatch_and_ambiguous() -> None:
    draft, plan, pack, words = _fixture()
    pack["errors"] = [
        {
            "id": "E-001",
            "source": {"table": "ua_gec_errors", "id": 1},
            "incorrect": "слове",
            "correct": "слово",
            "error_type": "form",
            "pattern": "fixture",
        }
    ]
    plan["lessons"][0]["activities"] = [
        {
            "id": "a1",
            "type": "error-correction",
            "placement": "inline",
            "focus": "Correct",
            "error_refs": ["E-001"],
        }
    ]
    item = {
        "sentence": "слове",
        "error": "слове",
        "correction": "слово",
        "explanation": "Correct",
        "error_ref": "E-001",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Correct", "items": [item]}]

    # Valid item passes
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert res["status"] == "passed"

    # error field does not match record incorrect
    bad_error = copy.deepcopy(draft)
    bad_error["activities"][0]["items"][0]["error"] = "слова"
    res, _ = runner.check_4_activities(bad_error, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "error_text_mismatch", "writer")

    # record incorrect does not occur in sentence
    bad_sentence = copy.deepcopy(draft)
    bad_sentence["activities"][0]["items"][0]["sentence"] = "слово"
    res, _ = runner.check_4_activities(bad_sentence, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "error_text_mismatch", "writer")

    # record incorrect occurs twice in sentence
    bad_ambiguous = copy.deepcopy(draft)
    bad_ambiguous["activities"][0]["items"][0]["sentence"] = "слове слове"
    res, _ = runner.check_4_activities(bad_ambiguous, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "error_text_ambiguous", "writer")


def test_check_4_key_failure_reasons() -> None:
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]

    # Index out of range
    item_oor = {
        "question": "слово",
        "options": ["слово", "слова"],
        "correct": 5,
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_oor]}]
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_index_out_of_range", "writer")

    # Ambiguous key in dict options (two correct: true)
    item_amb = {
        "question": "слово",
        "options": [
            {"text": "слово", "correct": True},
            {"text": "слова", "correct": True},
        ],
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_amb]}]
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_key_ambiguous", "writer")

    # Conflicting key styles (correct=0 points to слово, answer="слова")
    item_conf = {
        "question": "слово",
        "options": ["слово", "слова"],
        "correct": 0,
        "answer": "слова",
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_conf]}]
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_key_conflict", "writer")

    # Missing key
    item_miss = {
        "question": "слово",
        "options": ["слово", "слова"],
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_miss]}]
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_key_missing", "writer")

    # Answer string not in options
    item_notin = {
        "question": "слово",
        "options": ["слово", "слова"],
        "answer": "інше",
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_notin]}]
    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_not_in_options", "writer")


def test_a1_choice_types_provenance_and_key_assignment() -> None:
    draft, plan, pack, words = _fixture()

    # 1. quiz - all three key forms
    quiz_items = [
        {"question": "слово", "options": ["слово", "слова"], "correct": 0, "explanation": "E"},
        {"question": "слово", "options": ["слово", "слова"], "answer": "слова", "explanation": "E"},
        {
            "question": "слово",
            "options": [{"text": "слово", "correct": True}, {"text": "слова", "correct": False}],
            "explanation": "E",
        },
    ]

    # 2. fill-in - orthography
    fill_orth = [
        {
            "sentence": "____",
            "answer": "слово",
            "options": ["слово", "слова"],
            "explanation": "E",
            "mode": "orthography",
        }
    ]

    # 3. error-correction - with options
    pack["errors"] = [
        {
            "id": "E-001",
            "source": {"table": "ua_gec_errors", "id": 1},
            "incorrect": "слове",
            "correct": "слово",
            "error_type": "form",
            "pattern": "fixture",
        }
    ]
    err_items = [
        {
            "sentence": "слове",
            "error": "слове",
            "correction": "слово",
            "options": ["слово", "слова"],
            "explanation": "E",
            "error_ref": "E-001",
        }
    ]

    # 4. image-to-letter
    img_items = [{"image": "image.png", "letter": "слово", "options": ["слово", "слова"], "explanation": "E"}]

    # 5. translate
    trans_items = [
        {
            "source": "word",
            "options": [{"text": "слово", "correct": True}, {"text": "слова", "correct": False}],
            "explanation": "E",
        }
    ]

    # 6. odd-one-out
    odd_items = [{"words": ["слово", "слова", "слове"], "correct": 1, "explanation": "E"}]

    plan["lessons"][0]["activities"] = [
        {"id": "a_quiz", "type": "quiz", "placement": "inline", "focus": "Quiz"},
        {"id": "a_fill", "type": "fill-in", "placement": "inline", "focus": "Fill"},
        {"id": "a_err", "type": "error-correction", "placement": "inline", "focus": "Err", "error_refs": ["E-001"]},
        {"id": "a_img", "type": "image-to-letter", "placement": "inline", "focus": "Img"},
        {"id": "a_trans", "type": "translate", "placement": "inline", "focus": "Trans"},
        {"id": "a_odd", "type": "odd-one-out", "placement": "inline", "focus": "Odd"},
        {"id": "a_pick", "type": "pick-syllables", "placement": "inline", "focus": "Pick"},
    ]

    draft["activities"] = [
        {"id": "a_quiz", "instruction": "Quiz", "items": quiz_items},
        {"id": "a_fill", "instruction": "Fill", "items": fill_orth},
        {"id": "a_err", "instruction": "Err", "items": err_items},
        {"id": "a_img", "instruction": "Img", "items": img_items},
        {"id": "a_trans", "instruction": "Trans", "items": trans_items},
        {"id": "a_odd", "instruction": "Odd", "items": odd_items},
        {
            "id": "a_pick",
            "instruction": "Pick",
            "category": "cat",
            "syllables": ["слово", "слова"],
            "correctIndices": [0],
            "explanation": "E",
        },
    ]

    res, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert res["status"] == "passed"

    _expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    validator = get_provenance_validator()
    validator.validate(prov)

    # Check each activity type has choice spans with option_origin and is_key
    spans = prov["spans"]

    # Quiz 0: int correct: 0
    q0 = [
        s
        for s in spans
        if s.get("activity") == "a_quiz" and s.get("item") == 0 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q0) == 2
    assert q0[0]["is_key"] is True and q0[0]["text"] == "слово"
    assert q0[1]["is_key"] is False and q0[1]["text"] == "слова"

    # Quiz 1: str answer: слова
    q1 = [
        s
        for s in spans
        if s.get("activity") == "a_quiz" and s.get("item") == 1 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q1) == 2
    assert q1[0]["is_key"] is False and q1[0]["text"] == "слово"
    assert q1[1]["is_key"] is True and q1[1]["text"] == "слова"

    # Quiz 2: dict option
    q2 = [
        s
        for s in spans
        if s.get("activity") == "a_quiz" and s.get("item") == 2 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q2) == 2
    assert q2[0]["is_key"] is True and q2[0]["text"] == "слово"
    assert q2[1]["is_key"] is False and q2[1]["text"] == "слова"

    # Fill-in orthography
    fi = [s for s in spans if s.get("activity") == "a_fill" and str(s.get("block", "")).startswith("opt_")]
    assert len(fi) == 2
    assert fi[0]["is_key"] is True and fi[0]["text"] == "слово"
    assert fi[1]["is_key"] is False and fi[1]["text"] == "слова"

    # Error-correction options
    eo = [s for s in spans if s.get("activity") == "a_err" and str(s.get("block", "")).startswith("opt_")]
    assert len(eo) == 2
    assert eo[0]["is_key"] is True and eo[0]["text"] == "слово"
    assert eo[1]["is_key"] is False and eo[1]["text"] == "слова"

    # Image-to-letter
    im = [s for s in spans if s.get("activity") == "a_img" and str(s.get("block", "")).startswith("opt_")]
    assert len(im) == 2
    assert im[0]["is_key"] is True and im[0]["text"] == "слово"
    assert im[1]["is_key"] is False and im[1]["text"] == "слова"

    # Translate
    tr = [s for s in spans if s.get("activity") == "a_trans" and str(s.get("block", "")).startswith("opt_")]
    assert len(tr) == 2
    assert tr[0]["is_key"] is True and tr[0]["text"] == "слово"
    assert tr[1]["is_key"] is False and tr[1]["text"] == "слова"

    # Odd-one-out
    od = [s for s in spans if s.get("activity") == "a_odd" and str(s.get("block", "")).startswith("opt_")]
    assert len(od) == 3
    assert od[0]["is_key"] is False and od[0]["text"] == "слово"
    assert od[1]["is_key"] is True and od[1]["text"] == "слова"
    assert od[2]["is_key"] is False and od[2]["text"] == "слове"

    # Pick-syllables
    pk = [s for s in spans if s.get("activity") == "a_pick" and str(s.get("block", "")).startswith("opt_")]
    assert len(pk) == 2
    assert pk[0]["is_key"] is True and pk[0]["text"] == "слово"
    assert pk[1]["is_key"] is False and pk[1]["text"] == "слова"


def test_provenance_schema_rejects_invalid() -> None:
    schema = json.loads(PROVENANCE_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    valid_doc = {
        "provenance_schema": 1,
        "lesson": {"level": "a1", "slug": "sample-slug", "n": 1},
        "spans": [
            {
                "tab": "urok",
                "step": "s1",
                "activity": None,
                "item": None,
                "block": "narration",
                "source": "writer_prose",
                "ref": None,
                "text": "sample text",
                "record_kind": None,
                "record_side": None,
                "option_origin": None,
                "is_key": None,
            }
        ],
    }
    validator.validate(valid_doc)

    # Reject invalid record_kind
    bad_kind = copy.deepcopy(valid_doc)
    bad_kind["spans"][0]["record_kind"] = "unrecognized_kind"
    assert len(list(validator.iter_errors(bad_kind))) > 0

    # Reject invalid record_side
    bad_side = copy.deepcopy(valid_doc)
    bad_side["spans"][0]["record_side"] = "neutral"
    assert len(list(validator.iter_errors(bad_side))) > 0

    # Reject invalid option_origin
    bad_origin = copy.deepcopy(valid_doc)
    bad_origin["spans"][0]["option_origin"] = "machine_generated"
    assert len(list(validator.iter_errors(bad_origin))) > 0

    # Reject missing required span property
    bad_missing = copy.deepcopy(valid_doc)
    del bad_missing["spans"][0]["is_key"]
    assert len(list(validator.iter_errors(bad_missing))) > 0


def test_provenance_byte_stable_rerun(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    form = {
        **words["words"][0]["forms"][0],
        "form": "слова",
        "stressed": "слова\u0301",
        "tags": "noun:inanim:n:v_rod",
    }
    words["words"][0]["forms"].append(form)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].append(form["tags"])
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Forms"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Choose",
            "items": [
                {
                    "sentence": "____",
                    "answer": "слово",
                    "options": ["слово", "слова"],
                    "explanation": "Choose",
                    "mode": "form-choice",
                    "record": "W-1",
                    "answer_tags": words["words"][0]["forms"][0]["tags"],
                }
            ],
        }
    ]
    validate_fixture_words(words)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    first_report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert first_report["passed"] is True
    prov_path = state / "lesson-1.provenance.yaml"
    first_bytes = prov_path.read_bytes()

    second_report, _, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert second_report["passed"] is True
    second_bytes = prov_path.read_bytes()

    assert first_bytes == second_bytes
