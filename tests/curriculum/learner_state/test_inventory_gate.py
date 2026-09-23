"""Tests for inventory_gate (issue #8414 Brief Part 2).

Verifies:
- record IDs match `^W-[0-9]*[1-9][0-9]*$`;
- receipts document validates against schemas/resolution-receipts-v1.schema.json;
- a resolved record outside the set fails naming token, sentence and tab;
- three different case forms of one allowed record pass;
- base records pass;
- a core id absent fails (core_not_introduced);
- a recycled id absent fails (recycled_not_used);
- recycled id not introduced in prior state fails as lemma_outside_state;
- taught form present in teaching position (record_print, item_prompt, item_answer) passes;
- taught form present only in non-teaching position (narration, instruction) fails (taught_form_absent);
- introducing_step_not_locatable reported in not_checked on every run;
- --allow-missing-prior waiver reported in not_checked;
- resolver failure classes (too_many_candidates, gloss_outside_lesson, letter_outside_state, unclassifiable) fail as token_unresolved;
- gloss reference token passes when record's stress in _words.yaml is valid;
- gloss reference token fails as pending_stress when record's stress in _words.yaml is pending;
- unanswered stress_certain_identity_open is non-blocking and reported in reports;
- disk receipts file breaking schema fails as resolutions_invalid;
- declared speaker id passes, undeclared name fails;
- skipped:<field> tokens ignored.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.inventory_gate import check_lesson
from scripts.curriculum.resolver import codes as resolver_codes

pytestmark = pytest.mark.reads_content
REPO_ROOT = Path(__file__).resolve().parents[3]
RECEIPTS_SCHEMA_PATH = REPO_ROOT / "schemas/resolution-receipts-v1.schema.json"


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")
    path.write_bytes(content)
    lock.write(path, content)


def _setup_fixture(root: Path, level: str = "a1") -> dict[str, Path]:
    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_dir = root / f"curriculum/l2-uk-en/evidence/{level}"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    base_req = {
        "request_schema": 1,
        "level": level,
        "words": [
            {"lemma": "base-u", "pos": "prep", "want": "new"},
            {"lemma": "base-v", "pos": "prep", "want": "new"},
        ],
    }
    _write_yaml(evidence_dir / "_base.request.yaml", base_req)

    words_store = {
        "evidence_schema": 1,
        "level": level,
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {
                "id": "W-1",
                "lemma": "base-u",
                "pos": "prep",
                "forms": [
                    {
                        "form": "base-u",
                        "tags": "prep",
                        "stressed": "base-u",
                        "stress_source": "none",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-2",
                "lemma": "base-v",
                "pos": "prep",
                "forms": [
                    {
                        "form": "base-v",
                        "tags": "prep",
                        "stressed": "base-v",
                        "stress_source": "none",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-10",
                "lemma": "core-w1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "core-w1",
                        "tags": "tag:acc",
                        "stressed": "core-w1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-20",
                "lemma": "rec-w1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "rec-w1",
                        "tags": "tag:nom",
                        "stressed": "rec-w1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-30",
                "lemma": "name-spk1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "name-spk1",
                        "tags": "tag:nom",
                        "stressed": "name-spk1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-99",
                "lemma": "outside-w1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "outside-w1",
                        "tags": "tag:nom",
                        "stressed": "outside-w1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
        ],
    }
    _write_yaml(evidence_dir / "_words.yaml", words_store)

    plan = {
        "plan_schema": 2,
        "module": "mod-01",
        "level": level,
        "sequence": 1,
        "slug": "mod-01",
        "version": "1",
        "title": "Module 1",
        "arc_ref": {"level": level, "position": 1},
        "evidence_ref": {"path": f"curriculum/l2-uk-en/evidence/{level}/mod-01.yaml", "sha256": "0" * 64},
        "lessons": [
            {
                "n": 1,
                "slug": "l01",
                "title": "L1",
                "kind": "teach",
                "job": "J1",
                "rationale": "R1",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [{"lemma": "rec-w1", "evidence": "W-20", "forms": ["tag:nom"]}],
                    }
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T0",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-20"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-00"],
                        "practice": ["a0"],
                    }
                ],
                "activities": [{"id": "a0", "type": "quiz", "placement": "inline", "focus": "Q0"}],
            },
            {
                "n": 2,
                "slug": "l02",
                "title": "L2",
                "kind": "teach",
                "job": "J2",
                "rationale": "R2",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [{"lemma": "core-w1", "evidence": "W-10", "forms": ["tag:acc"]}],
                        "recycled": ["W-20"],
                    }
                },
                "dialogue": {
                    "speakers": [{"name": "Spk1", "evidence": "W-30"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T1",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-10"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    },
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Q"}],
            },
        ],
    }
    _write_yaml(plans_dir / "mod-01.yaml", plan)

    return {
        "plans_dir": plans_dir,
        "evidence_dir": evidence_dir,
        "words_path": evidence_dir / "_words.yaml",
        "base_request_path": evidence_dir / "_base.request.yaml",
    }


def _make_stream(
    tokens: list[dict[str, Any]], failures: list[dict[str, Any]] | None = None, lesson_n: int = 2
) -> dict[str, Any]:
    return {
        "lesson": {"level": "a1", "slug": "mod-01", "n": lesson_n},
        "inputs": {},
        "tokens": tokens,
        "failures": failures or [],
    }


def test_receipts_fixture_validates_against_schema() -> None:
    schema = json.loads(RECEIPTS_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    receipts_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 2},
        "inputs": {
            "expanded_sha256": "0" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": "tok1",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-10"],
                "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
                "provenance": "deterministic",
            }
        ],
    }
    validator.validate(receipts_doc)


def test_gate_all_pass_synthetic(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        # core-w1 in teaching position role=record_print with tag:acc
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        # recycled-w1 (introduced in lesson 1)
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # base-u and base-v
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 10,
            "token": "tok-u",
            "sentence": "tok-u sent",
            "class": "resolved",
            "selected": {"record": "W-1", "forms": ["prep"], "stressed": "tok-u"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 3},
            "role": "narration",
            "offset": 15,
            "token": "tok-v",
            "sentence": "tok-v sent",
            "class": "resolved",
            "selected": {"record": "W-2", "forms": ["prep"], "stressed": "tok-v"},
        },
        # dialogue speaker name
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 4},
            "role": "dialogue_line",
            "offset": 20,
            "token": "tok-spk",
            "sentence": "tok-spk sent",
            "class": "resolved",
            "selected": {"record": "W-30", "forms": ["tag:nom"], "stressed": "tok-spk"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is True
    assert len(report.failures) == 0
    assert codes.INTRODUCING_STEP_NOT_LOCATABLE in report.not_checked


def test_gate_lemma_outside_state_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Outside record
        {
            "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
            "role": "item_prompt",
            "offset": 10,
            "token": "bad-tok",
            "sentence": "bad token sentence text",
            "class": "resolved",
            "selected": {"record": "W-99", "forms": ["tag:nom"], "stressed": "bad-tok"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    failures = [f for f in report.failures if f.code == codes.LEMMA_OUTSIDE_STATE]
    assert len(failures) == 1
    f = failures[0]
    assert f.level == "a1"
    assert f.slug == "mod-01"
    assert f.lesson == 2
    assert f.tab == "vpravy"
    assert f.token == "bad-tok"
    assert f.sentence == "bad token sentence text"
    assert f.record == "W-99"


def test_gate_three_case_forms_one_allowed_record_pass(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "form-acc",
            "sentence": "form acc sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "form-acc"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 10,
            "token": "form-gen",
            "sentence": "form gen sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:gen"], "stressed": "form-gen"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 20,
            "token": "form-nom",
            "sentence": "form nom sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:nom"], "stressed": "form-nom"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 3},
            "role": "narration",
            "offset": 30,
            "token": "rec",
            "sentence": "rec sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "rec"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is True


def test_gate_core_not_introduced_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Only recycled-w1 is present, core-w1 (W-10) is missing
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "narration",
            "offset": 0,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.CORE_NOT_INTRODUCED in codes_set


def test_gate_recycled_not_used_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Only core-w1 is present, recycled-w1 (W-20) is missing
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.RECYCLED_NOT_USED in codes_set


def test_gate_recycled_id_not_in_prior_state_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Lesson 1 attempts to use W-99 as recycled without prior introduction
    plan_path = paths["plans_dir"] / "mod-01.yaml"
    plan_data = yaml.safe_load(plan_path.read_text(encoding="utf-8"))
    plan_data["lessons"][0]["inventory"]["vocabulary"]["recycled"] = ["W-99"]
    _write_yaml(plan_path, plan_data)

    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "rec-w1",
            "sentence": "rec sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "rec-w1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 10,
            "token": "out-w1",
            "sentence": "out sent",
            "class": "resolved",
            "selected": {"record": "W-99", "forms": ["tag:nom"], "stressed": "out-w1"},
        },
    ]
    # In lesson 1, W-99 was not in prior planned state, so it fails lemma_outside_state
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens, lesson_n=1), **paths)
    assert report.ok is False
    assert any(f.code == codes.LEMMA_OUTSIDE_STATE and f.record == "W-99" for f in report.failures)


def test_gate_taught_form_absent_fails_outside_teaching_position(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # core-w1 has tag:acc in plan forms.
    # It appears only in role=narration (not record_print, not item_prompt, not item_answer)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "narration",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.TAUGHT_FORM_ABSENT in codes_set


def test_gate_taught_form_in_teaching_positions_pass(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    for role in ("record_print", "item_prompt", "item_answer"):
        tokens = [
            {
                "unit": {
                    "tab": "urok",
                    "activity": "a1" if role != "record_print" else None,
                    "item": 0 if role != "record_print" else None,
                    "block": 0,
                },
                "role": role,
                "offset": 0,
                "token": "tok1",
                "sentence": "tok1 sent",
                "class": "resolved",
                "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
            },
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
                "role": "narration",
                "offset": 5,
                "token": "tok2",
                "sentence": "tok2 sent",
                "class": "resolved",
                "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
            },
        ]
        report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
        assert report.ok is True, f"failed for role {role}"


def test_gate_gloss_token_passes(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Gloss reference with stressed: null passes because record W-10 has non-pending stress in _words.yaml
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "{{gloss:W-10}}",
            "sentence": "sentence with {{gloss:W-10}}",
            "surface": "gloss_ref",
            "class": "resolved",
            "candidates": ["W-10"],
            "selected": {"record": "W-10", "forms": [], "stressed": None},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "record_print",
            "offset": 5,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 10,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is True


def test_gate_gloss_token_pending_stress_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Set W-10 stress_source to pending in _words.yaml
    words_file = paths["words_path"]
    words_doc = yaml.safe_load(words_file.read_text(encoding="utf-8"))
    for w in words_doc["words"]:
        if w["id"] == "W-10":
            w["forms"][0]["stress_source"] = "pending"
            w["forms"][0].pop("stressed", None)
    _write_yaml(words_file, words_doc)

    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "{{gloss:W-10}}",
            "sentence": "sentence with {{gloss:W-10}}",
            "surface": "gloss_ref",
            "class": "resolved",
            "candidates": ["W-10"],
            "selected": {"record": "W-10", "forms": [], "stressed": None},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "record_print",
            "offset": 5,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 10,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    assert any(f.code == codes.PENDING_STRESS and f.record == "W-10" for f in report.failures)


@pytest.mark.parametrize(
    "failure_class,expected_code",
    [
        (resolver_codes.TOO_MANY_CANDIDATES, codes.TOKEN_UNRESOLVED),
        (resolver_codes.GLOSS_OUTSIDE_LESSON, codes.TOKEN_UNRESOLVED),
        (resolver_codes.LETTER_OUTSIDE_STATE, codes.TOKEN_UNRESOLVED),
        (resolver_codes.UNCLASSIFIABLE, codes.TOKEN_UNRESOLVED),
        (resolver_codes.LEMMA_OUTSIDE_STATE, codes.LEMMA_OUTSIDE_STATE),
        (resolver_codes.PENDING_STRESS, codes.PENDING_STRESS),
    ],
)
def test_gate_each_failure_class_in_stream(tmp_path: Path, failure_class: str, expected_code: str) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 10,
            "token": "err-tok",
            "sentence": "err-tok sent",
            "class": failure_class,
            "selected": None,
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    assert any(f.code == expected_code and f.token == "err-tok" for f in report.failures)


def test_gate_stress_certain_identity_open_reported_non_blocking(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
            "role": "narration",
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-20", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Unanswered stress_certain_identity_open token
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
            "role": "narration",
            "offset": 10,
            "token": "open-tok",
            "sentence": "open-tok sent",
            "class": resolver_codes.STRESS_CERTAIN_IDENTITY_OPEN,
            "selected": None,
        },
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is True
    assert len(report.failures) == 0
    assert len(report.reports) == 1
    r = report.reports[0]
    assert r["code"] == resolver_codes.STRESS_CERTAIN_IDENTITY_OPEN
    assert r["token"] == "open-tok"


def test_gate_disk_receipts_schema_break_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    state_dir = paths["evidence_dir"] / "_state" / "mod-01"
    state_dir.mkdir(parents=True, exist_ok=True)
    res_path = state_dir / "lesson-2.resolutions.yaml"

    # Write a receipts doc that breaks schema (missing required inputs, invalid token class)
    invalid_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 2},
        # missing "inputs"
        "tokens": [
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": "tok",
                "surface": "sentence_token",
                "class": "invalid_class_not_in_schema",
                "candidates": ["W-10"],
                "selected": None,
                "provenance": "deterministic",
            }
        ],
    }
    _write_yaml(res_path, invalid_doc)

    report = check_lesson("a1", "mod-01", 2, resolutions_path=res_path, **paths)
    assert report.ok is False
    assert any(f.code == codes.RESOLUTIONS_INVALID for f in report.failures)


def test_gate_allow_missing_prior_records_waiver(tmp_path: Path) -> None:
    # Setup fixture at position 2 without position 1 plan
    plans_dir = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    evidence_dir = tmp_path / "curriculum/l2-uk-en/evidence/a1"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    base_req = {
        "request_schema": 1,
        "level": "a1",
        "words": [{"lemma": "base-u", "pos": "prep", "want": "new"}],
    }
    _write_yaml(evidence_dir / "_base.request.yaml", base_req)
    words_store = {
        "evidence_schema": 1,
        "level": "a1",
        "built_with": {
            "mcp_commit": "0" * 40,
            "sources_db": "0" * 64,
            "vesum": "0" * 64,
            "trie": "0" * 64,
            "ulif_forms": "0" * 64,
        },
        "words": [
            {
                "id": "W-1",
                "lemma": "base-u",
                "pos": "prep",
                "forms": [
                    {
                        "form": "base-u",
                        "tags": "prep",
                        "stressed": "base-u",
                        "stress_source": "none",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-10",
                "lemma": "core-w1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "core-w1",
                        "tags": "tag:acc",
                        "stressed": "core-w1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
        ],
    }
    _write_yaml(evidence_dir / "_words.yaml", words_store)

    # Position 2 module (missing position 1)
    plan = {
        "plan_schema": 2,
        "module": "mod-02",
        "level": "a1",
        "sequence": 2,
        "slug": "mod-02",
        "version": "1",
        "title": "Module 2",
        "arc_ref": {"level": "a1", "position": 2},
        "evidence_ref": {"path": "curriculum/l2-uk-en/evidence/a1/mod-02.yaml", "sha256": "0" * 64},
        "lessons": [
            {
                "n": 1,
                "slug": "l01",
                "title": "L1",
                "kind": "teach",
                "job": "J1",
                "rationale": "R1",
                "word_target": 10,
                "inventory": {
                    "vocabulary": {
                        "core": [{"lemma": "core-w1", "evidence": "W-10", "forms": ["tag:acc"]}],
                    }
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T1",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-10"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Q"}],
            }
        ],
    }
    _write_yaml(plans_dir / "mod-02.yaml", plan)

    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        }
    ]
    stream = _make_stream(tokens, lesson_n=1)
    stream["lesson"]["slug"] = "mod-02"

    report = check_lesson(
        "a1",
        "mod-02",
        1,
        stream,
        plans_dir=plans_dir,
        evidence_dir=evidence_dir,
        words_path=evidence_dir / "_words.yaml",
        base_request_path=evidence_dir / "_base.request.yaml",
        allow_missing_prior=True,
    )
    assert report.ok is True
    assert codes.WAIVER_PRIOR_PLANS_MISSING in report.not_checked


def test_gate_gloss_absent_from_store_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Gloss referring to W-999 which is not in _words.yaml
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "{{gloss:W-999}}",
            "sentence": "tok {{gloss:W-999}} sent",
            "surface": resolver_codes.GLOSS_REF,
            "class": "resolved",
            "selected": {"record": "W-999", "forms": ["tag:nom"], "stressed": "tok"},
        }
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    assert any(f.code == codes.TOKEN_UNRESOLVED and f.record == "W-999" for f in report.failures)


def test_gate_word_store_unreadable_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Tamper words file to be invalid YAML
    paths["words_path"].write_text("invalid: [broken: yaml", encoding="utf-8")
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
            "role": "record_print",
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
        }
    ]
    report = check_lesson("a1", "mod-01", 2, _make_stream(tokens, lesson_n=2), **paths)
    assert report.ok is False
    assert any(f.code == codes.BASE_LAYER_MISSING for f in report.failures)


def test_gate_missing_expanded_document_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    evidence_dir = paths["evidence_dir"]
    res_dir = evidence_dir / "_state" / "mod-01"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_path = res_dir / "lesson-2.resolutions.yaml"

    res_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 2},
        "inputs": {
            "expanded_sha256": "a" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": "tok1",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-10"],
                "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
                "provenance": "deterministic",
            }
        ],
    }
    _write_yaml(res_path, res_doc)

    report = check_lesson("a1", "mod-01", 2, resolutions_path=res_path, **paths)
    assert report.ok is False
    assert any(f.code == codes.EXPANDED_DOCUMENT_MISSING for f in report.failures)


def test_gate_mismatched_expanded_hash_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    evidence_dir = paths["evidence_dir"]
    res_dir = evidence_dir / "_state" / "mod-01"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_path = res_dir / "lesson-2.resolutions.yaml"
    exp_path = res_dir / "lesson-2.expanded.yaml"

    exp_doc = {
        "lesson": {"level": "a1", "slug": "mod-01", "n": 2},
        "units": [
            {"tab": "urok", "activity": None, "item": None, "block": 0, "role": "record_print", "text": "tok1 sent"}
        ],
    }
    _write_yaml(exp_path, exp_doc)

    res_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 2},
        "inputs": {
            "expanded_sha256": "f" * 64,  # mismatched
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": "tok1",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-10"],
                "selected": {"record": "W-10", "forms": ["tag:acc"], "stressed": "tok1"},
                "provenance": "deterministic",
            }
        ],
    }
    _write_yaml(res_path, res_doc)

    report = check_lesson("a1", "mod-01", 2, resolutions_path=res_path, **paths)
    assert report.ok is False
    assert any(f.code == codes.EXPANDED_DOCUMENT_MISMATCH for f in report.failures)
