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
from scripts.curriculum.evidence import lock
from tests.build.test_fresh_assemble import (
    make_word_record,
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
    assert (state / "lesson-1.provenance.yaml.lock").is_file()
    assert lock.check(prov_path) is True
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
    assert corr_span["text"] == "слово"  # record print: the pack's `correct` text, unstressed
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
    orig_sentence = bad_ambiguous["activities"][0]["items"][0]["sentence"]
    bad_ambiguous["activities"][0]["items"][0]["sentence"] = f"{orig_sentence} {orig_sentence}"
    res, _ = runner.check_4_activities(bad_ambiguous, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "error_text_ambiguous", "writer")

    # error-correction: correction and answer conflict
    bad_conflict = copy.deepcopy(draft)
    bad_conflict["activities"][0]["items"][0]["answer"] = "слова"
    res, _ = runner.check_4_activities(bad_conflict, plan["lessons"][0], words, pack)
    assert (res["check"], res["reason"], res["layer"]) == (4, "answer_key_conflict", "writer")


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

    # Ambiguous key via duplicate matching string options
    item_dup_str = {
        "question": "слово",
        "options": ["слово", "слово"],
        "answer": "слово",
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_dup_str]}]
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

    # Conflicting key styles (correct index vs dict option)
    item_conf_dict = {
        "question": "слово",
        "options": [
            {"text": "слово", "correct": True},
            {"text": "слова", "correct": False},
        ],
        "correct": 1,
        "explanation": "Exp",
    }
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": [item_conf_dict]}]
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


def test_a1_choice_types_provenance_and_key_assignment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    form_a = {
        **words["words"][0]["forms"][0],
        "form": "слова",
        "stressed": "слова\u0301",
        "tags": "noun:inanim:n:v_rod",
    }
    form_e = {
        **words["words"][0]["forms"][0],
        "form": "слове",
        "stressed": "сло́ве",
        "tags": "noun:inanim:n:v_kly",
    }
    words["words"][0]["forms"].extend([form_a, form_e])
    plan["lessons"][0]["inventory"]["vocabulary"]["core"][0]["forms"].extend([form_a["tags"], form_e["tags"]])
    # Every taught form has a teaching position in the urok text: a string `answer` key is no
    # longer a resolved unit (it is a key like the integer `correct`), so `слова` is taught here.
    draft["steps"][0]["blocks"][0]["text"] = ("слово " * 9) + "слова слове "

    w_a = make_word_record(2, "а", pos="conj", gloss_en="and")
    w_ya = make_word_record(3, "я", pos="pron", gloss_en="I")
    words["words"].extend([w_a, w_ya])
    plan["lessons"][0]["inventory"]["vocabulary"]["core"].extend(
        [
            {"lemma": "а", "evidence": "W-2", "forms": [w_a["forms"][0]["tags"]]},
            {"lemma": "я", "evidence": "W-3", "forms": [w_ya["forms"][0]["tags"]]},
        ]
    )

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
            "sentence": "я слово ___",
            "answer": "а",
            "options": ["а", "я"],
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

    # 4. image-to-letter: fails check 9 closed until #8716 (see
    # test_live_runner_image_to_letter_fails_closed_until_8716), so it is not in this run.

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

    # 7. pick-syllables
    pick_act = {
        "id": "a_pick",
        "instruction": "Pick",
        "category": "cat",
        "syllables": ["слово", "слова"],
        "correctIndices": [0],
        "explanation": "E",
    }

    act_ids = ["a1", "a2", "a3", "a5", "a6", "a7"]
    plan["lessons"][0]["steps"][0]["practice"] = act_ids
    plan["lessons"][0]["activities"] = [
        {"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"},
        {"id": "a2", "type": "fill-in", "placement": "inline", "focus": "Fill"},
        {"id": "a3", "type": "error-correction", "placement": "inline", "focus": "Err", "error_refs": ["E-001"]},
        {"id": "a5", "type": "translate", "placement": "inline", "focus": "Trans"},
        {"id": "a6", "type": "odd-one-out", "placement": "inline", "focus": "Odd"},
        {"id": "a7", "type": "pick-syllables", "placement": "inline", "focus": "Pick"},
    ]

    for aid in act_ids:
        draft["steps"][0]["blocks"].append({"kind": "activity", "ref": aid})

    draft["activities"] = [
        {"id": "a1", "instruction": "Quiz", "items": quiz_items},
        {"id": "a2", "instruction": "Fill", "items": fill_orth},
        {"id": "a3", "instruction": "Err", "items": err_items},
        {"id": "a5", "instruction": "Trans", "items": trans_items},
        {"id": "a6", "instruction": "Odd", "items": odd_items},
        {**pick_act, "id": "a7"},
    ]

    validate_fixture_words(words)
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report

    prov_path = state / "lesson-1.provenance.yaml"
    assert prov_path.is_file()
    assert (state / "lesson-1.provenance.yaml.lock").is_file()
    assert lock.check(prov_path) is True
    prov = yaml.safe_load(prov_path.read_text(encoding="utf-8"))

    validator = get_provenance_validator()
    validator.validate(prov)

    # Check each activity type has choice spans with option_origin and is_key
    spans = prov["spans"]

    # Quiz 0: int correct: 0
    q0 = [
        s
        for s in spans
        if s.get("activity") == "a1" and s.get("item") == 0 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q0) == 2
    assert q0[0]["is_key"] is True and "слово" in q0[0]["text"]
    assert q0[1]["is_key"] is False and "слова" in q0[1]["text"]

    # Quiz 1: str answer: слова
    q1 = [
        s
        for s in spans
        if s.get("activity") == "a1" and s.get("item") == 1 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q1) == 2
    assert q1[0]["is_key"] is False and "слово" in q1[0]["text"]
    assert q1[1]["is_key"] is True and "слова" in q1[1]["text"]

    # Quiz 2: dict option
    q2 = [
        s
        for s in spans
        if s.get("activity") == "a1" and s.get("item") == 2 and str(s.get("block", "")).startswith("opt_")
    ]
    assert len(q2) == 2
    assert q2[0]["is_key"] is True and "слово" in q2[0]["text"]
    assert q2[1]["is_key"] is False and "слова" in q2[1]["text"]

    # Fill-in orthography
    fi = [s for s in spans if s.get("activity") == "a2" and str(s.get("block", "")).startswith("opt_")]
    assert len(fi) == 2
    assert fi[0]["is_key"] is True and fi[0]["text"] == "а"
    assert fi[1]["is_key"] is False and fi[1]["text"] == "я"

    # Error-correction options
    eo = [s for s in spans if s.get("activity") == "a3" and str(s.get("block", "")).startswith("opt_")]
    assert len(eo) == 2
    assert eo[0]["is_key"] is True and "слово" in eo[0]["text"]
    assert eo[1]["is_key"] is False and "слова" in eo[1]["text"]

    # Translate
    tr = [s for s in spans if s.get("activity") == "a5" and str(s.get("block", "")).startswith("opt_")]
    assert len(tr) == 2
    assert tr[0]["is_key"] is True and "слово" in tr[0]["text"]
    assert tr[1]["is_key"] is False and "слова" in tr[1]["text"]

    # Odd-one-out
    od = [s for s in spans if s.get("activity") == "a6" and str(s.get("block", "")).startswith("opt_")]
    assert len(od) == 3
    assert od[0]["is_key"] is False and "слово" in od[0]["text"]
    assert od[1]["is_key"] is True and "слова" in od[1]["text"]
    assert od[2]["is_key"] is False and "слове" in od[2]["text"]

    # Pick-syllables
    pk = [s for s in spans if s.get("activity") == "a7" and str(s.get("block", "")).startswith("opt_")]
    assert len(pk) == 2
    assert pk[0]["is_key"] is True and "слово" in pk[0]["text"]
    assert pk[1]["is_key"] is False and "слова" in pk[1]["text"]

    # A string `answer` key (quiz item 1, odd-one-out) is no provenance unit: the page carries it
    # only as the option flagged correct, and the check verifies that flag against is_key.
    assert [s["block"] for s in spans if s.get("activity") == "a1" and s.get("item") == 1] == [
        "prompt",
        "opt_0",
        "opt_1",
        "explanation",
    ]
    assert not any(s.get("activity") == "a6" and s.get("block") == "answer" for s in spans)
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert '{"text": "слово", "correct": false}, {"text": "слова", "correct": true}' in mdx


def test_live_runner_a2_select_provenance_and_key_assignment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    draft, plan, pack, words = _fixture()
    plan["level"] = "a2"
    plan["module"] = "sample-slug"
    plan["slug"] = "sample-slug"
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [
        {"id": "a1", "type": "select", "placement": "inline", "focus": "Select"},
    ]
    draft["lesson"]["module"] = "a2/sample-slug"
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Select correct",
            "items": [
                {
                    "question": "слово",
                    "options": [
                        {"text": "слово", "correct": True},
                        {"text": "слова", "correct": False},
                    ],
                    "min_correct": 1,
                    "explanation": "Exp",
                }
            ],
        }
    ]
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft, level="a2")

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, level="a2")
    assert report["passed"] is True, report

    prov_path = state / "lesson-1.provenance.yaml"
    assert prov_path.is_file()
    assert (state / "lesson-1.provenance.yaml.lock").is_file()
    assert lock.check(prov_path) is True
    prov = yaml.safe_load(prov_path.read_text(encoding="utf-8"))

    validator = get_provenance_validator()
    validator.validate(prov)

    sel_spans = [s for s in prov["spans"] if s.get("activity") == "a1" and str(s.get("block", "")).startswith("opt_")]
    assert len(sel_spans) == 2
    assert sel_spans[0]["is_key"] is True
    assert sel_spans[0]["option_origin"] == "writer_typed"
    assert sel_spans[0]["source"] == "writer_prose"
    assert sel_spans[1]["is_key"] is False
    assert sel_spans[1]["option_origin"] == "writer_typed"
    assert sel_spans[1]["source"] == "writer_prose"

    # Also verify that in A1, select with min_correct: 1 fails check 4 (requires min 2)
    plan_a1 = copy.deepcopy(plan)
    plan_a1["level"] = "a1"
    res, _ = runner.check_4_activities(draft, plan_a1["lessons"][0], words, pack, level="a1")
    assert (res["check"], res["reason"], res["layer"]) == (4, "select_correct_set_invalid", "writer")


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
                "span": 0,
                "start": 0,
                "end": 11,
                "source": "writer_prose",
                "ref": None,
                "role": "narration",
                "text": "sample text",
                "record_kind": None,
                "record_side": None,
                "option_origin": None,
                "is_key": None,
            }
        ],
    }
    validator.validate(valid_doc)

    # Valid with record source and record_kind
    valid_record = copy.deepcopy(valid_doc)
    valid_record["spans"][0]["source"] = "record"
    valid_record["spans"][0]["ref"] = "W-1"
    valid_record["spans"][0]["record_kind"] = "word"
    validator.validate(valid_record)

    # Reject record source with null record_kind (Finding 5)
    bad_record = copy.deepcopy(valid_doc)
    bad_record["spans"][0]["source"] = "record"
    bad_record["spans"][0]["ref"] = "W-1"
    bad_record["spans"][0]["record_kind"] = None
    assert len(list(validator.iter_errors(bad_record))) > 0

    # Reject writer_prose with non-null record_kind (Finding 5)
    bad_prose = copy.deepcopy(valid_doc)
    bad_prose["spans"][0]["source"] = "writer_prose"
    bad_prose["spans"][0]["record_kind"] = "word"
    assert len(list(validator.iter_errors(bad_prose))) > 0

    # Reject invalid record_kind
    bad_kind = copy.deepcopy(valid_record)
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

    # Reject an unknown role
    bad_role = copy.deepcopy(valid_doc)
    bad_role["spans"][0]["role"] = "footnote"
    assert len(list(validator.iter_errors(bad_role))) > 0

    # Reject missing span/start/end/role (Finding 4, r3)
    for missing_field in ("span", "start", "end", "role"):
        bad_pos = copy.deepcopy(valid_doc)
        del bad_pos["spans"][0][missing_field]
        assert len(list(validator.iter_errors(bad_pos))) > 0


def test_assembler_unknown_record_prefix_fails_with_engine_layer() -> None:
    # Finding 5: unknown record prefix fails with engine layer
    with pytest.raises(assemble.AssemblerError) as exc_info:
        assemble.derive_record_kind("Q-001")
    assert exc_info.value.code == "unknown_record_prefix"
    assert exc_info.value.layer == "engine"

    with pytest.raises(assemble.AssemblerError) as exc_info2:
        assemble.derive_record_kind("R-001")
    assert exc_info2.value.code == "unknown_record_prefix"
    assert exc_info2.value.layer == "engine"

    with pytest.raises(assemble.AssemblerError) as exc_info3:
        assemble.derive_record_kind("UNKNOWN-123")
    assert exc_info3.value.code == "unknown_record_prefix"
    assert exc_info3.value.layer == "engine"


def test_check_9_unit_absent_from_rendered_output_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Finding 1: the urok steps are dropped after assembly, so the renderer emits nothing at the
    # prose units' location; check 9 must fail closed for those units, not search the page.
    draft, plan, pack, words = _fixture()
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    _expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    draft["steps"] = []

    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **kw: type("State", (), {"cumulative_core_count": 10, "waiver": None})()
    )
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]}
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": "a1"})())

    stream = type("Stream", (), {"tokens": []})()
    res = assemble.check_9_stress_and_render(
        _expanded,
        draft,
        plan,
        pack,
        words,
        stream,
        "a1",
        "sample-slug",
        1,
        provenance_doc=prov,
        repo_root=tmp_path,
        output_dir=tmp_path / "state",
        plans_dir=tmp_path,
        evidence_dir=tmp_path,
    )
    assert res.passed is False
    assert "span_location_unrendered" in (res.reason or "")
    assert "('urok', 's1', None, None, 0)" in (res.reason or "")
    assert res.layer == "engine"


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


# --- r3: spans partition their unit, unit-relative offsets, renderer-located verification ---


def _spans_by_unit(prov_doc: dict) -> dict[tuple, list[dict]]:
    by_unit: dict[tuple, list[dict]] = {}
    for s in prov_doc["spans"]:
        by_unit.setdefault((s["tab"], s["step"], s["activity"], s["item"], s["block"]), []).append(s)
    return by_unit


def _assert_spans_partition_units(prov_doc: dict) -> None:
    for spans in _spans_by_unit(prov_doc).values():
        ordered = sorted(spans, key=lambda s: s["start"])
        assert [s["span"] for s in ordered] == list(range(len(ordered)))
        cursor = 0
        for s in ordered:
            assert s["start"] == cursor
            assert s["end"] == cursor + len(s["text"])
            cursor = s["end"]
        assert "".join(s["text"] for s in ordered) == ordered[-1]["text"] if len(ordered) == 1 else True


SRC_ROOT = Path(__file__).resolve().parents[2]


def _write_observed_from_receipts(state: Path, plan: dict) -> None:
    """A schema-valid observed index for the runner's real receipts (the digest reads record roles).

    The learner-state writer needs base-layer and prior-plan fixtures that belong to another
    package; the roles here come from the plan inventory like the real writer's do.
    """
    receipts = yaml.safe_load((state / "lesson-1.resolutions.yaml").read_text(encoding="utf-8"))
    inventory = plan["lessons"][0]["inventory"]["vocabulary"]
    core = {c["evidence"] for c in inventory.get("core", [])}
    records: dict[str, dict] = {}
    for token in receipts["tokens"]:
        selected = token.get("selected")
        if not selected:
            continue
        role = "taught" if selected["record"] in core else "incidental"
        rec = records.setdefault(selected["record"], {"id": selected["record"], "role": role, "forms": []})
        for tags in selected["forms"]:
            form = next((f for f in rec["forms"] if f["tags"] == tags), None)
            if form is None:
                form = {"tags": tags, "count_by_tab": {"urok": 0, "slovnyk": 0, "vpravy": 0, "resursy": 0}}
                rec["forms"].append(form)
            form["count_by_tab"][token["unit"]["tab"]] += 1
    doc = {
        "observed_schema": 1,
        "lesson": receipts["lesson"],
        "records": list(records.values()),
        "untaught_forms": {"count": 0, "share": 0.0, "forms": []},
    }
    schema = json.loads((SRC_ROOT / "schemas/learner-observed-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(doc)
    lock.write(state / "lesson-1.observed.yaml", lock.yaml_bytes(doc))


def _digest_tree(tmp_path: Path, state: Path, plan: dict) -> Path:
    """Arrange the runner's outputs in the canonical repo layout the digest generator reads."""
    root = tmp_path / "digest-root"
    plans_dir = root / "curriculum/l2-uk-en/lesson-plans/a1"
    state_dir = root / "curriculum/l2-uk-en/evidence/a1/_state/sample-slug"
    mdx_dir = root / "site/src/content/docs/a1/sample-slug"
    schemas_dir = root / "schemas"
    for d in (plans_dir, state_dir, mdx_dir, schemas_dir):
        d.mkdir(parents=True)
    for name in (
        "module-plan-v2.schema.json",
        "resolution-receipts-v1.schema.json",
        "learner-observed-v1.schema.json",
        "module-digest-v1.schema.json",
        "lesson-provenance-v1.schema.json",
    ):
        (schemas_dir / name).write_bytes((SRC_ROOT / "schemas" / name).read_bytes())
    (plans_dir / "sample-slug.yaml").write_bytes(lock.yaml_bytes(plan))
    for name in ("provenance", "resolutions", "observed"):
        for suffix in ("", ".lock"):
            src = state / f"lesson-1.{name}.yaml{suffix}"
            (state_dir / src.name).write_bytes(src.read_bytes())
    (mdx_dir / "1.mdx").write_bytes((tmp_path / "site" / "1.mdx").read_bytes())
    return root


def test_live_runner_and_digest_two_spans_in_one_unit_and_gloss_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Live path: the prose unit holds four spans (narration, quoted term, narration, gloss ref).

    Every span's receipt token sits at offset 0 of its own resolver unit; the digest must map the
    quoted term to span 1 and the gloss reference to the word-record span 3, not to span 0.
    """
    from scripts.review.digest import build_digest, validate_digest

    draft, plan, pack, words = _fixture(text=("слово " * 10) + "{{uk:слово}} {{gloss:W-1}}")
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words, gloss_ids={"W-1"})
    assert report["passed"] is True, report
    _write_observed_from_receipts(state, plan)

    prov_doc = yaml.safe_load((state / "lesson-1.provenance.yaml").read_text(encoding="utf-8"))
    get_provenance_validator().validate(prov_doc)
    _assert_spans_partition_units(prov_doc)

    prose = _spans_by_unit(prov_doc)[("urok", "s1", None, None, 0)]
    assert [s["role"] for s in prose] == ["narration", "quoted_term", "narration", "gloss_ref"]
    assert [s["text"] for s in prose] == ["сло́во " * 10, "сло́во", " ", "слово (term)"]
    assert [(s["start"], s["end"]) for s in prose] == [(0, 70), (70, 76), (76, 77), (77, 89)]
    gloss = prose[3]
    assert (gloss["source"], gloss["ref"], gloss["record_kind"]) == ("record", "W-1", "word")
    # The page shows exactly the concatenation of the unit's spans
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert "".join(s["text"] for s in prose) in mdx

    doc = build_digest("a1", "sample-slug", 2, repo_root=_digest_tree(tmp_path, state, plan))  # lessons 1..up_to-1
    validate_digest(doc)
    occ = [o for o in doc["lessons"][0]["occurrences"] if o["locator"] == {**o["locator"], "tab": "urok", "block": 0}]
    by_span: dict[int, list[dict]] = {}
    for o in occ:
        by_span.setdefault(o["locator"]["span"], []).append(o)
    # The quoted term's receipt offset is 0 (its own resolver unit); it lands in span 1, not span 0.
    assert sorted(by_span) == [0, 1]
    assert [o["offset"] for o in by_span[0]] == list(range(0, 60, 6))
    assert [(o["offset"], o["span_source"], o["record"]) for o in by_span[1]] == [(0, "writer_prose", "W-1")]
    # The gloss reference reports no occurrence (no form), but the real receipts align to its span
    from scripts.review.digest.generator import align_receipt_tokens

    receipts = yaml.safe_load((state / "lesson-1.resolutions.yaml").read_text(encoding="utf-8"))
    prose_tokens = [t for t in receipts["tokens"] if (t["unit"]["tab"], t["unit"]["block"]) == ("urok", 0)]
    assert [(t["offset"], t["token"]) for t in prose_tokens][-3:] == [(54, "слово"), (0, "слово"), (8, "W-1")]
    assert align_receipt_tokens(prose, prose_tokens)[-3:] == [(0, 63), (1, 70), (3, 77)]


def test_live_runner_error_correction_spans_partition_prompt_and_correction_is_rendered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    draft, plan, pack, words = _fixture()
    w_ya = make_word_record(3, "я", pos="pron", gloss_en="I")
    words["words"].append(w_ya)
    plan["lessons"][0]["inventory"]["vocabulary"]["core"].append(
        {"lemma": "я", "evidence": "W-3", "forms": [w_ya["forms"][0]["tags"]]}
    )
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
        {"id": "a1", "type": "error-correction", "placement": "inline", "focus": "Correct", "error_refs": ["E-001"]}
    ]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Correct the error",
            "items": [
                {
                    "sentence": "я слове",
                    "error": "слове",
                    "correction": "слово",
                    "explanation": "C",
                    "error_ref": "E-001",
                }
            ],
        }
    ]
    validate_fixture_words(words)
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)

    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    prov_doc = yaml.safe_load((state / "lesson-1.provenance.yaml").read_text(encoding="utf-8"))
    _assert_spans_partition_units(prov_doc)
    prompt = _spans_by_unit(prov_doc)[("vpravy", "s1", "a1", 0, "prompt")]
    assert [(s["text"], s["start"], s["end"], s["source"], s["record_side"]) for s in prompt] == [
        ("я ", 0, 2, "writer_prose", None),
        ("слове", 2, 7, "record", "incorrect"),
    ]
    answer = _spans_by_unit(prov_doc)[("vpravy", "s1", "a1", 0, "answer")]
    # The correction is a record print: the page shows the E- record's `correct` text as the pack
    # has it (the ErrorCorrection component compares the unstressed option chips to it exactly).
    assert [(s["text"], s["record_side"]) for s in answer] == [("слово", "correct")]
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert '"correctForm": "слово"' in mdx and '"я слове"' in mdx


def test_check_9_activity_absent_from_rendered_output_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Finding 1: the activity is dropped after assembly; its spans are absent from the page and the
    # renderer identified no location for them -> fail closed, no whole-page search.
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [
        {
            "id": "a1",
            "instruction": "Quiz",
            "items": [{"question": "слово", "options": ["слово", "слова"], "correct": 0, "explanation": "E"}],
        }
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    draft["activities"] = []
    draft["steps"][0]["blocks"] = [b for b in draft["steps"][0]["blocks"] if b.get("kind") != "activity"]

    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **kw: type("State", (), {"cumulative_core_count": 10, "waiver": None})()
    )
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]}
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": "a1"})())
    res = assemble.check_9_stress_and_render(
        expanded,
        draft,
        plan,
        pack,
        words,
        type("Stream", (), {"tokens": []})(),
        "a1",
        "sample-slug",
        1,
        provenance_doc=prov,
        repo_root=tmp_path,
        output_dir=tmp_path / "state",
        plans_dir=tmp_path,
        evidence_dir=tmp_path,
    )
    assert res.passed is False
    assert "span_location_unrendered" in (res.reason or "")
    assert "('vpravy', 's1', 'a1', None, 'instruction')" in (res.reason or "")
    assert res.layer == "engine"
    assert not (tmp_path / "state" / "lesson-1.provenance.yaml").exists()


def _finalize_inputs() -> tuple[dict, dict]:
    draft, plan, pack, words = _fixture(text="слово {{uk:слово}}")
    expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    stressed = {"stressed_schema": 1, "lesson": expanded["lesson"], "units": copy.deepcopy(expanded["units"])}
    return prov, stressed


def test_finalize_two_spans_with_one_rendered_piece_fails() -> None:
    # Reviewer reproduction: two distinct spans, the renderer emitted only one of them.
    prov, stressed = _finalize_inputs()
    pieces = {i: u["text"] for i, u in enumerate(stressed["units"])}
    del pieces[1]
    with pytest.raises(assemble.AssemblerError) as exc_info:
        assemble.finalize_provenance_from_stressed_units(prov, stressed, pieces)
    assert exc_info.value.code == "span_location_unrendered"
    assert "unit 1" in exc_info.value.message
    assert exc_info.value.layer == "engine"


def test_finalize_rejects_whitespace_tolerant_match() -> None:
    # Reviewer reproduction: the full text is absent, its trimmed text appears elsewhere.
    prov, stressed = _finalize_inputs()
    slovnyk_idx = next(i for i, u in enumerate(stressed["units"]) if u["tab"] == "slovnyk")
    pieces = {i: u["text"] for i, u in enumerate(stressed["units"])}
    pieces[slovnyk_idx] = stressed["units"][slovnyk_idx]["text"] + " "
    with pytest.raises(assemble.AssemblerError) as exc_info:
        assemble.finalize_provenance_from_stressed_units(prov, stressed, pieces)
    assert exc_info.value.code == "span_text_not_in_rendered_output"
    # The urok tab compares exactly, so even a stress-only difference is refused there
    pieces = {i: u["text"] for i, u in enumerate(stressed["units"])}
    pieces[0] = "сло́во "
    with pytest.raises(assemble.AssemblerError) as exc_info:
        assemble.finalize_provenance_from_stressed_units(prov, stressed, pieces)
    assert exc_info.value.code == "span_text_not_in_rendered_output"


def test_finalize_rebuilds_unit_relative_offsets_from_rendered_pieces() -> None:
    prov, stressed = _finalize_inputs()
    stressed["units"][1]["text"] = "сло́во"
    pieces = {i: u["text"] for i, u in enumerate(stressed["units"])}
    final = assemble.finalize_provenance_from_stressed_units(prov, stressed, pieces)
    _assert_spans_partition_units(final)
    prose = _spans_by_unit(final)[("urok", "s1", None, None, 0)]
    assert [(s["span"], s["start"], s["end"], s["text"]) for s in prose] == [
        (0, 0, 6, "слово "),
        (1, 6, 12, "сло́во"),
    ]
    assert prov["spans"][1]["text"] == "слово"  # the check-5 document is left untouched


def test_assembly_rejects_form_choice_item_without_record() -> None:
    # r2 MINOR: direct assembly raises the same named reason as check 4 instead of labelling
    # the options as writer prose.
    draft, plan, pack, words = _fixture()
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
                    "explanation": "C",
                    "mode": "form-choice",
                }
            ],
        }
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    with pytest.raises(assemble.AssemblerError) as exc_info:
        assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    assert exc_info.value.code == "form_choice_options_invalid"
    assert exc_info.value.layer == "writer"
    row, _ = runner.check_4_activities(draft, plan["lessons"][0], words, pack)
    assert row["reason"] == "form_choice_options_invalid"


# --- r4: verification runs against what the page receives ---


def _check_9_direct(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    expanded: dict,
    prov: dict,
    draft: dict,
    plan: dict,
    pack: dict,
    words: dict,
) -> assemble.CheckResult:
    monkeypatch.setattr(
        assemble, "planned_state", lambda *a, **kw: type("State", (), {"cumulative_core_count": 10, "waiver": None})()
    )
    monkeypatch.setattr(assemble.lesson_lock, "check_lesson_lock", lambda *a, **kw: (True, ""))
    monkeypatch.setattr(
        assemble.lesson_lock, "compute_lesson_lock", lambda *a, **kw: {"lessons": [{"n": 1, "entry_sha256": "0" * 64}]}
    )
    monkeypatch.setattr(assemble, "compute_lesson_immersion_band", lambda **kw: type("Band", (), {"band_key": "a1"})())
    return assemble.check_9_stress_and_render(
        expanded,
        draft,
        plan,
        pack,
        words,
        type("Stream", (), {"tokens": []})(),
        "a1",
        "sample-slug",
        1,
        provenance_doc=prov,
        repo_root=tmp_path,
        output_dir=tmp_path / "state",
        site_dir=tmp_path / "site",
        plans_dir=tmp_path,
        evidence_dir=tmp_path,
    )


def _quiz_fixture(items: list[dict]) -> tuple[dict, dict, dict, dict]:
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a1"]
    plan["lessons"][0]["activities"] = [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Quiz"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a1"})
    draft["activities"] = [{"id": "a1", "instruction": "Quiz", "items": items}]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    return draft, plan, pack, words


def test_component_props_from_jsx_round_trips_escaped_text() -> None:
    # The props are read back exactly as the JS engine cooks the template literal `_dump_safe_json`
    # escaped (backslashes, backticks, `${`) and as MDX decodes the string props.
    from scripts.yaml_activities import ActivityParser

    parser = ActivityParser()
    question = 'сло́во `q` "d" \\ ${e}\nnl'
    act = parser._parse_activity(
        {
            "type": "quiz",
            "id": "a1",
            "instruction": 'Say "hi" `x` ${y}',
            "items": [{"question": question, "options": ["слово", "слова"], "correct": 0, "explanation": "E"}],
        }
    )
    props = assemble.component_props_from_jsx(parser._activity_to_mdx(act, False))
    assert props["instruction"] == 'Say "hi" `x` ${y}'
    assert props["questions"][0]["question"] == question
    assert assemble.page_field_text("quiz", props, 0, "opt_1") == "слова"
    assert assemble.page_option_is_key("quiz", props, 0, 0) is True
    assert assemble.page_option_is_key("quiz", props, 0, 1) is False
    # An error-correction instruction is a JSX attribute string: `&quot;` is decoded, nothing else
    ec = parser._parse_activity(
        {
            "type": "error-correction",
            "id": "a3",
            "instruction": 'Fix "it"',
            "items": [{"sentence": "я слове", "error": "слове", "correction": "слово", "explanation": "E"}],
        }
    )
    ec_props = assemble.component_props_from_jsx(parser._activity_to_mdx(ec, False))
    assert ec_props["instruction"] == 'Fix "it"'
    assert assemble.page_field_text("error-correction", ec_props, 0, "answer") == "слово"
    assert assemble.page_field_text("error-correction", ec_props, 0, "error") == "слове"


def test_check_9_parser_dropping_a_field_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # BLOCKER (r3): the mapping was taken before the activity parser ran. A parser that drops one
    # field (here: the explanation of item 0) must fail check 9 at that unit's location, because
    # the page component never receives the text the provenance describes.
    from scripts.yaml_activities import ActivityParser

    draft, plan, pack, words = _quiz_fixture(
        [{"question": "слово", "options": ["слово", "слова"], "correct": 0, "explanation": "E"}]
    )
    expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    original = ActivityParser._parse_quiz

    def dropping_parse_quiz(self, data):
        act = original(self, data)
        act.items[0].explanation = None
        return act

    monkeypatch.setattr(ActivityParser, "_parse_quiz", dropping_parse_quiz)
    res = _check_9_direct(tmp_path, monkeypatch, expanded, prov, draft, plan, pack, words)
    assert res.passed is False
    assert res.layer == "engine"
    assert (res.reason or "").startswith("span_location_unrendered: ")
    assert "('vpravy', 's1', 'a1', 0, 'explanation')" in (res.reason or "")
    assert "the quiz component receives '' in its 'explanation' field" in (res.reason or "")
    assert not (tmp_path / "state" / "lesson-1.provenance.yaml").exists()
    assert not (tmp_path / "site" / "1.mdx").exists()

    # A parser that alters a field (option 1 text) fails the same way: the text is not in its field.
    def altering_parse_quiz(self, data):
        act = original(self, data)
        act.items[0].options[1].text = act.items[0].options[1].text + " "
        return act

    monkeypatch.setattr(ActivityParser, "_parse_quiz", altering_parse_quiz)
    res = _check_9_direct(tmp_path, monkeypatch, expanded, prov, draft, plan, pack, words)
    assert res.passed is False
    assert "span_location_unrendered" in (res.reason or "")
    assert "('vpravy', 's1', 'a1', 0, 'opt_1')" in (res.reason or "")


def test_check_9_page_key_disagreement_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The page's own key must be the provenance key: a component flagging another option correct
    # would blame the wrong span (R2b) and mislead the learner.
    from scripts.yaml_activities import ActivityParser

    draft, plan, pack, words = _quiz_fixture(
        [{"question": "слово", "options": ["слово", "слова"], "correct": 1, "explanation": "E"}]
    )
    expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    original = ActivityParser._parse_quiz

    def flipping_parse_quiz(self, data):
        act = original(self, data)
        for opt in act.items[0].options:
            opt.correct = not opt.correct
        return act

    monkeypatch.setattr(ActivityParser, "_parse_quiz", flipping_parse_quiz)
    res = _check_9_direct(tmp_path, monkeypatch, expanded, prov, draft, plan, pack, words)
    assert res.passed is False
    assert res.layer == "engine"
    assert (res.reason or "").startswith("span_key_not_on_page: ")
    assert "('vpravy', 's1', 'a1', 0, 'opt_0')" in (res.reason or "")


def test_live_runner_quiz_string_answer_key_follows_unstressed_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Options are never stressed (resolver SKIPPED_ROLES) but an `answer` unit was, so the page
    # got a quiz with no correct option. The key is no unit; it follows the option it names.
    draft, plan, pack, words = _quiz_fixture(
        [{"question": "слово", "options": ["слово", "слова"], "answer": "слово", "explanation": "E"}]
    )
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    prov_doc = yaml.safe_load((state / "lesson-1.provenance.yaml").read_text(encoding="utf-8"))
    by_unit = _spans_by_unit(prov_doc)
    assert ("vpravy", "s1", "a1", 0, "answer") not in by_unit
    assert by_unit[("vpravy", "s1", "a1", 0, "prompt")][0]["text"] == "сло́во"
    assert [(s["text"], s["is_key"]) for s in by_unit[("vpravy", "s1", "a1", 0, "opt_0")]] == [("слово", True)]
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert '{"text": "слово", "correct": true}, {"text": "слова", "correct": false}' in mdx


def test_live_runner_translate_without_options_answer_is_the_single_page_option(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No choices: the answer is text (a resolved, stressed unit) and the Translate component
    # receives it as its one correct option, where the unit is located.
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a5"]
    plan["lessons"][0]["activities"] = [{"id": "a5", "type": "translate", "placement": "inline", "focus": "Trans"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a5"})
    draft["activities"] = [
        {"id": "a5", "instruction": "Trans", "items": [{"source": "word", "answer": "слово", "explanation": "E"}]}
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    prov_doc = yaml.safe_load((state / "lesson-1.provenance.yaml").read_text(encoding="utf-8"))
    answer = _spans_by_unit(prov_doc)[("vpravy", "s1", "a5", 0, "answer")]
    assert [(s["text"], s["role"]) for s in answer] == [("сло́во", "item_answer")]
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    assert '"options": [{"text": "сло́во", "correct": true}]' in mdx


def _image_to_letter_fixture() -> tuple[dict, dict, dict, dict]:
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["steps"][0]["practice"] = ["a4"]
    plan["lessons"][0]["activities"] = [{"id": "a4", "type": "image-to-letter", "placement": "inline", "focus": "Img"}]
    draft["steps"][0]["blocks"].append({"kind": "activity", "ref": "a4"})
    draft["activities"] = [
        {
            "id": "a4",
            "instruction": "Img",
            "items": [{"image": "image.png", "letter": "слово", "options": ["слово", "слова"], "explanation": "E"}],
        }
    ]
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    return draft, plan, pack, words


def test_live_runner_image_to_letter_fails_closed_until_8716(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Reviewer reproduction (r3 BLOCKER): a schema-valid image-to-letter item passed check 9 while
    # the ActivityParser dropped image/letter/options. Now the unit's field is read from the page
    # props and check 9 fails closed. Delete this test with the xfail marker below once #8716 lands.
    draft, plan, pack, words = _image_to_letter_fixture()
    report, state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = next(c for c in report["checks"] if c["check"] == 9)
    assert c9["status"] == "failed" and c9["layer"] == "engine"
    assert c9["reason"].startswith("span_location_unrendered: ")
    assert "'a4'" in c9["reason"]
    # The provenance on disk is still check 5's document; nothing of check 9 reached disk
    _expanded, check_5_prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    assert (state / "lesson-1.provenance.yaml").read_bytes() == lock.yaml_bytes(check_5_prov)
    assert not (tmp_path / "site" / "1.mdx").exists()


@pytest.mark.xfail(
    strict=True,
    reason="#8716: ActivityParser reads emoji/answer/distractors, the A1 schema has image/letter/options",
)
def test_image_to_letter_options_reach_the_page() -> None:
    # Starts failing loudly (XPASS) once #8716 makes the parser read the schema's fields: then
    # remove the marker (and the fail-closed live test above).
    from scripts.yaml_activities import ActivityParser

    parser = ActivityParser()
    act = parser._parse_activity(
        {
            "type": "image-to-letter",
            "id": "a4",
            "instruction": "Img",
            "items": [{"image": "image.png", "letter": "слово", "options": ["слово", "слова"], "explanation": "E"}],
        }
    )
    props = assemble.component_props_from_jsx(parser._activity_to_mdx(act))
    assert assemble.page_field_text("image-to-letter", props, 0, "opt_0", key_index=0) == "слово"
    assert assemble.page_field_text("image-to-letter", props, 0, "opt_1", key_index=0) == "слова"


def test_urok_renderer_emits_mapped_bytes_without_final_strip() -> None:
    # Reviewer reproduction (r3 BLOCKER b): the renderer's final `.strip()` removed whitespace the
    # mapped piece kept. The mapping now describes exactly the bytes emitted. (Assembly drops
    # end-of-line whitespace from draft text, see page_text; the stressed unit carries it here
    # to pin the renderer's own contract.)
    draft, plan, pack, words = _fixture()
    draft["consolidation"]["lead_in"] = "слово"
    validate_fixture_draft(draft)
    expanded, prov = assemble.assemble_expanded_document(draft, plan, pack, words, "a1", "sample-slug", 1)
    stressed = {"stressed_schema": 1, "lesson": expanded["lesson"], "units": copy.deepcopy(expanded["units"])}
    lead_idx = next(i for i, u in enumerate(stressed["units"]) if u["block"] == "consolidation_lead_in")
    stressed["units"][lead_idx]["text"] = "слово "
    urok_md, unit_map = assemble._render_urok_markdown(draft, stressed, pack, words)
    pieces = unit_map.texts()
    assert pieces[lead_idx] == "слово "
    assert urok_md.endswith("слово ")
    assert not urok_md.endswith("\n")  # the renderer's own trailing separators are still dropped
    final = assemble.finalize_provenance_from_stressed_units(prov, stressed, {**pieces, **_record_tab_pieces(stressed)})
    lead = _spans_by_unit(final)[("urok", None, None, None, "consolidation_lead_in")]
    assert [(s["text"], s["start"], s["end"]) for s in lead] == [("слово ", 0, 6)]
    assert urok_md[-6:] == lead[0]["text"]


def _record_tab_pieces(stressed: dict) -> dict[int, str]:
    return {i: u["text"] for i, u in enumerate(stressed["units"]) if u["tab"] in ("slovnyk", "resursy")}


# ---------------------------------------------------------------------------
# Round 5 (reviewer BLOCKER r4): every Urok unit is verified at its own location in the final
# Lesson tab, after every `generate_mdx` transform; a transform that removes or rewrites a unit
# fails check 9 closed (engine layer).
# ---------------------------------------------------------------------------


def _page_and_provenance(tmp_path: Path) -> tuple[str, dict]:
    mdx = (tmp_path / "site" / "1.mdx").read_text(encoding="utf-8")
    prov = yaml.safe_load((tmp_path / "state" / "lesson-1.provenance.yaml").read_text(encoding="utf-8"))
    return mdx, prov


def _lesson_tab(mdx: str) -> str:
    return mdx.split('<TabItem label="Урок — Lesson">')[1].split("</TabItem>")[0]


def _check_9_row(report: dict) -> dict:
    return next(c for c in report["checks"] if c["check"] == 9)


def test_live_runner_prose_heading_removed_by_generate_mdx_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Reviewer reproduction (r4 BLOCKER): a prose unit `# слово` produced a provenance span with
    # the heading while generate_mdx removed the duplicate H1 from the Lesson tab. The unit is
    # now read back at its location in the final MDX: the transform removed it -> fail closed.
    draft, plan, pack, words = _fixture()
    draft["steps"][0]["blocks"].insert(0, {"kind": "prose", "text": "# слово", "explains": ["W-1"]})
    validate_fixture_draft(draft)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = _check_9_row(report)
    assert c9["status"] == "failed" and c9["layer"] == "engine"
    assert c9["reason"].startswith("span_location_unrendered: unit 0 at ('urok', 's1', None, None, 0): ")
    assert "transform 'remove_duplicate_h1' removed the bytes of unit 0 ('# сло́во')" in c9["reason"]
    assert not (tmp_path / "site" / "1.mdx").exists()


def test_live_runner_duplicate_heading_removed_by_generate_mdx_is_not_reattached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Reviewer reproduction (r5 BLOCKER): two identical `# слово` prose units; generate_mdx
    # removes the first (duplicate H1) and the identical second line survives on the page. The
    # map moves units by the transform's own edit record, never by matching text, so the
    # removed unit is not re-attached to the surviving copy: check 9 fails closed for it.
    draft, plan, pack, words = _fixture()
    for _ in range(2):
        draft["steps"][0]["blocks"].insert(0, {"kind": "prose", "text": "# слово", "explains": ["W-1"]})
    validate_fixture_draft(draft)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = _check_9_row(report)
    assert c9["status"] == "failed" and c9["layer"] == "engine"
    assert c9["reason"].startswith("span_location_unrendered: unit 0 at ('urok', 's1', None, None, 0): ")
    assert "transform 'remove_duplicate_h1' removed the bytes of unit 0 ('# сло́во')" in c9["reason"]
    assert not (tmp_path / "site" / "1.mdx").exists()


def test_live_runner_heading_inside_prose_unit_rewritten_by_generate_mdx_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The same heading as the first line of a longer prose unit: the page keeps the rest of the
    # unit, so the unit is rewritten (not removed) and the reason names the transform.
    draft, plan, pack, words = _fixture(text="# слово\n\n" + "слово " * 10)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = _check_9_row(report)
    assert c9["layer"] == "engine"
    assert c9["reason"].startswith("span_text_not_in_rendered_output: unit 0 at ('urok', 's1', None, None, 0): ")
    assert "transform 'remove_duplicate_h1' rewrote the bytes of unit 0" in c9["reason"]
    assert not (tmp_path / "site" / "1.mdx").exists()


def _video_fixture() -> tuple[dict, dict, dict, dict]:
    from tests.build.test_fresh_assemble import make_video_record

    draft, plan, pack, words = _fixture()
    pack["videos"] = [make_video_record(1, "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "LearnUA", use="Listen")]
    plan["lessons"][0]["videos"] = [{"evidence": "V-1", "use": "Listen once"}]
    draft["steps"][0]["blocks"].append({"kind": "video", "ref": "V-1", "lead_in": "Watch: {{uk:слово}}"})
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    return draft, plan, pack, words


def test_live_runner_youtube_link_becomes_component_and_lead_in_unit_keeps_its_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The video block's link line (a pack record, no unit) is replaced by the YouTubeVideo
    # component; the lead-in units before it are verified at their (unchanged) location.
    draft, plan, pack, words = _video_fixture()
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    mdx, prov = _page_and_provenance(tmp_path)
    lesson = _lesson_tab(mdx)
    component = '<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=dQw4w9WgXcQ" label="LearnUA" />'
    assert component in lesson
    assert "[LearnUA](" not in lesson
    lead = _spans_by_unit(prov)[("urok", "s1", None, None, "video_lead_1")]
    assert [(s["role"], s["text"]) for s in lead] == [("narration", "Watch: "), ("quoted_term", "сло́во")]
    lead_text = "".join(s["text"] for s in lead)
    assert lesson.count(lead_text) == 1
    assert lesson.index(lead_text) < lesson.index(component)
    _assert_spans_partition_units(prov)


def test_live_runner_youtube_link_inside_prose_unit_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A prose unit that contains a YouTube markdown link is rewritten into a component by
    # generate_mdx: the unit's bytes no longer stand together on the page -> fail closed.
    draft, plan, pack, words = _fixture(text="слово " * 10 + "[слово](https://youtu.be/dQw4w9WgXcQ) слово")
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = _check_9_row(report)
    assert c9["layer"] == "engine"
    assert c9["reason"].startswith("span_text_not_in_rendered_output: unit 0 at ('urok', 's1', None, None, 0): ")
    assert "transform 'embed_youtube_video_links' rewrote the bytes of unit 0" in c9["reason"]


def test_live_runner_readings_block_insertion_keeps_unit_locations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # generate_mdx inserts the reading list in front of the Lesson content; every unit after
    # it is verified at its shifted location.
    from scripts.generate_mdx.reading_links import reading_href_for

    href = reading_href_for("duma-marusia-bohuslavka")
    assert href, "hosted reading fixture missing"
    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["reading_passages"] = [
        {"title": "Маруся Богуславка", "reading_slug": "duma-marusia-bohuslavka", "genre": "дума"}
    ]
    validate_fixture_plan(plan)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    mdx, prov = _page_and_provenance(tmp_path)
    lesson = _lesson_tab(mdx)
    block = f"**Тексти для читання**\n\n- [Маруся Богуславка]({href}) — дума"
    assert block in lesson
    prose = _spans_by_unit(prov)[("urok", "s1", None, None, 0)]
    assert [s["text"] for s in prose] == [("сло́во " * 11).rstrip()]
    assert lesson.index(block) < lesson.index(prose[0]["text"])
    _assert_spans_partition_units(prov)


def test_live_runner_dialogue_units_live_in_the_dialogue_box_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Dialogue lines reach the page as the DialogueBox `exchanges` prop. The renderer emits
    # that component itself and maps each line's units into the payload bytes (escaped for
    # JSON and for the JS string literal); check 9 decodes them back at their location.
    import re

    from scripts.generate_mdx.unit_map import decode_js_json_string

    draft, plan, pack, words = _fixture()
    plan["lessons"][0]["dialogue"] = {
        "step": "s1",
        "situation": "Meeting",
        "setting": "Street",
        "speakers": [{"name": "Оксана", "role": "student", "gender": "f"}],
        "register": "informal",
        "target_grammar": "greeting",
        "evidence": [],
    }
    draft["steps"][0]["blocks"].append({"kind": "dialogue"})
    draft["dialogue"] = {
        "lines": [
            {"speaker": "Оксана", "text": "слово {{uk:слово}} 'слово'"},
            {"speaker": "Оксана", "text": 'слово "слово" \\ слово'},
        ]
    }
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    mdx, prov = _page_and_provenance(tmp_path)
    lesson = _lesson_tab(mdx)
    assert lesson.count("<DialogueBox") == 1
    payload = re.search(r"^  exchanges=\{JSON\.parse\('(.*)'\)\}$", lesson, flags=re.MULTILINE).group(1)
    exchanges = json.loads(re.sub(r"\\([\\'])", r"\1", payload))
    by_unit = _spans_by_unit(prov)
    line_texts = ["".join(s["text"] for s in by_unit[("urok", "s1", None, None, f"dialogue_{i}")]) for i in range(2)]
    assert line_texts == ["сло́во сло́во 'сло́во'", 'сло́во "сло́во" \\ сло́во']
    assert [(e["speaker"], e["text"]) for e in exchanges] == [("Оксана", line_texts[0]), ("Оксана", line_texts[1])]
    assert decode_js_json_string(payload.split('"text":"')[2].split('"}')[0]) == line_texts[1]
    _assert_spans_partition_units(prov)


def test_live_runner_end_of_line_whitespace_is_dropped_at_assembly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The page's normalizer strips whitespace at the end of a line; unit text is taken from the
    # draft the same way (page_text), so the spans and the page agree byte for byte.
    draft, plan, pack, words = _fixture(text="слово " * 6 + "\t\n" + "слово " * 5)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    mdx, prov = _page_and_provenance(tmp_path)
    prose = _spans_by_unit(prov)[("urok", "s1", None, None, 0)]
    expected = ("сло́во " * 6).rstrip() + "\n" + ("сло́во " * 5).rstrip()
    assert [(s["text"], s["start"], s["end"]) for s in prose] == [(expected, 0, len(expected))]
    assert expected in _lesson_tab(mdx)


def test_live_runner_callout_and_table_units_keep_locations_through_generate_mdx(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Block kinds whose markdown generate_mdx rewrites around the unit (callouts -> admonitions,
    # tables, bilingual rows, quotes, examples): the unit's own bytes stay, so it is located.
    from tests.build.test_fresh_assemble import make_example_record, make_text_record

    draft, plan, pack, words = _fixture()
    pack["texts"] = [make_text_record(1, "слово слово")]
    pack["examples"] = [make_example_record(1, "слово", "word", words=["W-1"])]
    plan["lessons"][0]["steps"][0]["evidence"] = ["W-1", "T-1", "EX-1"]
    draft["steps"][0]["blocks"].extend(
        [
            {"kind": "example", "ref": "EX-1"},
            {"kind": "quote", "ref": "T-1"},
            {"kind": "table", "rows": [["слово", "слово"], ["слово", "слово"]], "explains": ["W-1"]},
            {"kind": "pronunciation", "text": "слово", "explains": ["W-1"]},
            {"kind": "culture", "text": "слово слово", "explains": ["T-1"]},
            {"kind": "tip", "text": "слово"},
            {"kind": "summary", "text": "слово"},
            {"kind": "callout", "text": "слово"},
            {"kind": "bilingual", "uk": ["слово"], "en": ["word"]},
        ]
    )
    validate_fixture_pack(pack)
    validate_fixture_plan(plan)
    validate_fixture_draft(draft)
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is True, report
    mdx, prov = _page_and_provenance(tmp_path)
    lesson = _lesson_tab(mdx)
    assert ":::note[" in lesson and ":::tip[" in lesson and "> [!" not in lesson
    urok_blocks = {loc[4] for loc in _spans_by_unit(prov) if loc[0] == "urok"}
    assert {1, 2, "table_3_0_0", "table_3_1_1", 4, 5, 6, 7, 8, "bilingual_9_0"} <= urok_blocks
    for loc, spans in _spans_by_unit(prov).items():
        if loc[0] == "urok":
            assert "".join(s["text"] for s in spans) in lesson, loc
    _assert_spans_partition_units(prov)


def test_live_runner_activity_jsx_rewritten_by_generate_mdx_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Vpravy units are located in the component JSX as it stands in the final MDX. A shared
    # transform that rewrites the payload (here fix_html_for_jsx on a `<br>` in an
    # explanation) fails closed for the activity instead of passing on the pre-transform JSX.
    draft, plan, pack, words = _quiz_fixture(
        [{"question": "слово", "options": ["слово", "слова"], "correct": 0, "explanation": "E<br>F"}]
    )
    report, _state, _ = _run_contract(tmp_path, monkeypatch, draft, plan, pack, words)
    assert report["passed"] is False
    c9 = _check_9_row(report)
    assert c9["layer"] == "engine"
    assert c9["reason"].startswith("span_text_not_in_rendered_output: activity 'a1' component: ")
    assert "transform 'fix_html_for_jsx' rewrote the bytes of unit ('activity', 'a1', 0)" in c9["reason"]
    assert not (tmp_path / "site" / "1.mdx").exists()
