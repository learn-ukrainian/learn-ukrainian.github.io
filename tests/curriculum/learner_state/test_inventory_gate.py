"""Tests for inventory_gate (issue #8414 Brief Part 2).

Verifies:
- a resolved record outside the set fails naming token, sentence and tab;
- three different case forms of one allowed record pass;
- `у` and `в` (two base records) both pass;
- a core id absent fails (core_not_introduced);
- a recycled id absent fails (recycled_not_used);
- a taught form present only outside a teaching position fails (taught_form_absent),
  present in a paradigm table passes;
- an `outside_allowlist` or unclassifiable token fails (token_unresolved);
- a `pending` stress fails (pending_stress);
- a declared speaker id passes, an undeclared name fails;
- `skipped:<field>` tokens ignored.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.inventory_gate import check_lesson

pytestmark = pytest.mark.reads_content


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
            {"id": "W-BASE-U", "lemma": "base-u", "pos": "prep"},
            {"id": "W-BASE-V", "lemma": "base-v", "pos": "prep"},
            {"id": "W-CORE-01", "lemma": "core-w1", "pos": "noun"},
            {"id": "W-RECYCLED-01", "lemma": "recycled-w1", "pos": "noun"},
            {"id": "W-NAME-01", "lemma": "name-spk1", "pos": "noun"},
            {"id": "W-OUTSIDE-01", "lemma": "outside-w1", "pos": "noun"},
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
                        "core": [{"lemma": "core-w1", "evidence": "W-CORE-01", "forms": ["tag:acc"]}],
                        "recycled": ["W-RECYCLED-01"],
                    }
                },
                "dialogue": {
                    "speakers": [{"name": "Spk1", "evidence": "W-NAME-01"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T1",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-CORE-01"]},
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    },
                    {
                        "id": "s2",
                        "kind": "teach",
                        "teach": "T2",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": []},
                        "uses": {"grammar": [], "vocabulary": ["W-CORE-01"]},
                        "evidence": ["E-02"],
                        "practice": ["a2"],
                    },
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Q"}],
            }
        ],
    }
    _write_yaml(plans_dir / "mod-01.yaml", plan)

    return {
        "plans_dir": plans_dir,
        "evidence_dir": evidence_dir,
        "words_path": evidence_dir / "_words.yaml",
        "base_request_path": evidence_dir / "_base.request.yaml",
    }


def _make_stream(tokens: list[dict[str, Any]], failures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "lesson": {"level": "a1", "slug": "mod-01", "n": 1},
        "inputs": {},
        "tokens": tokens,
        "failures": failures or [],
    }


def test_gate_all_pass_synthetic(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        # core-w1 in teaching position (introducing step s1) with tag:acc
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        # recycled-w1
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s2"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # base-u and base-v
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 10,
            "token": "tok-u",
            "sentence": "tok-u sent",
            "class": "resolved",
            "selected": {"record": "W-BASE-U", "forms": ["prep"], "stressed": "tok-u"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 15,
            "token": "tok-v",
            "sentence": "tok-v sent",
            "class": "resolved",
            "selected": {"record": "W-BASE-V", "forms": ["prep"], "stressed": "tok-v"},
        },
        # dialogue speaker name
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 20,
            "token": "tok-spk",
            "sentence": "tok-spk sent",
            "class": "resolved",
            "selected": {"record": "W-NAME-01", "forms": ["tag:nom"], "stressed": "tok-spk"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is True
    assert len(report.failures) == 0


def test_gate_lemma_outside_state_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s2"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Outside record
        {
            "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
            "offset": 10,
            "token": "bad-tok",
            "sentence": "bad token sentence text",
            "class": "resolved",
            "selected": {"record": "W-OUTSIDE-01", "forms": ["tag:nom"], "stressed": "bad-tok"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    failures = [f for f in report.failures if f.code == codes.LEMMA_OUTSIDE_STATE]
    assert len(failures) == 1
    f = failures[0]
    assert f.level == "a1"
    assert f.slug == "mod-01"
    assert f.lesson == 1
    assert f.tab == "vpravy"
    assert f.token == "bad-tok"
    assert f.sentence == "bad token sentence text"
    assert f.record == "W-OUTSIDE-01"


def test_gate_three_case_forms_one_allowed_record_pass(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        # Three different case forms of allowed record W-CORE-01
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "form-nom",
            "sentence": "form nom sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:nom"], "stressed": "form-nom"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 10,
            "token": "form-gen",
            "sentence": "form gen sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:gen"], "stressed": "form-gen"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 20,
            "token": "form-acc",
            "sentence": "form acc sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "form-acc"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 30,
            "token": "rec",
            "sentence": "rec sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "rec"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is True


def test_gate_u_and_v_both_pass(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # W-BASE-U and W-BASE-V
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 10,
            "token": "u",
            "sentence": "u sent",
            "class": "resolved",
            "selected": {"record": "W-BASE-U", "forms": ["prep"], "stressed": "u"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 15,
            "token": "v",
            "sentence": "v sent",
            "class": "resolved",
            "selected": {"record": "W-BASE-V", "forms": ["prep"], "stressed": "v"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is True


def test_gate_core_not_introduced_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Only recycled-w1 is present, core-w1 is missing
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.CORE_NOT_INTRODUCED in codes_set


def test_gate_recycled_not_used_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Only core-w1 is present, recycled-w1 is missing
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.RECYCLED_NOT_USED in codes_set


def test_gate_taught_form_absent_fails_outside_teaching_position(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # core-w1 has tag:acc in plan forms.
    # It appears only in step s2 (not the introducing step s1, not an activity, not a paradigm)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s2", "role": "narration"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.TAUGHT_FORM_ABSENT in codes_set


def test_gate_taught_form_in_paradigm_passes(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # core-w1 tag:acc appears in paradigm table
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "paradigm"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is True


def test_gate_token_unresolved_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Unclassifiable / outside allowlist token
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 10,
            "token": "unknown-token",
            "sentence": "unknown token sentence",
            "class": "outside_allowlist",
            "selected": None,
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.TOKEN_UNRESOLVED in codes_set


def test_gate_pending_stress_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "pending"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is False
    codes_set = {f.code for f in report.failures}
    assert codes.PENDING_STRESS in codes_set


def test_gate_speaker_name_declared_passes_undeclared_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens_declared = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Declared speaker W-NAME-01
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 10,
            "token": "name1",
            "sentence": "name1 sent",
            "class": "resolved",
            "selected": {"record": "W-NAME-01", "forms": ["tag:nom"], "stressed": "name1"},
        },
    ]
    rep1 = check_lesson("a1", "mod-01", 1, _make_stream(tokens_declared), **paths)
    assert rep1.ok is True

    # Undeclared speaker W-NAME-UNDECLARED
    tokens_undeclared = [
        *tokens_declared,
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 15,
            "token": "undeclared-name",
            "sentence": "undeclared name sentence",
            "class": "resolved",
            "selected": {"record": "W-NAME-UNDECLARED", "forms": ["tag:nom"], "stressed": "undeclared"},
        },
    ]
    rep2 = check_lesson("a1", "mod-01", 1, _make_stream(tokens_undeclared), **paths)
    assert rep2.ok is False
    failures = [f for f in rep2.failures if f.code == codes.LEMMA_OUTSIDE_STATE]
    assert len(failures) == 1
    assert failures[0].record == "W-NAME-UNDECLARED"


def test_gate_skipped_tokens_ignored(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    tokens = [
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 0,
            "token": "tok1",
            "sentence": "tok1 sent",
            "class": "resolved",
            "selected": {"record": "W-CORE-01", "forms": ["tag:acc"], "stressed": "tok1"},
        },
        {
            "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
            "offset": 5,
            "token": "tok2",
            "sentence": "tok2 sent",
            "class": "resolved",
            "selected": {"record": "W-RECYCLED-01", "forms": ["tag:nom"], "stressed": "tok2"},
        },
        # Skipped error_text and distractor tokens: must be completely ignored
        {
            "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
            "offset": 10,
            "token": "err-tok",
            "sentence": "err sent",
            "class": "skipped:error_text",
            "surface": "skipped",
            "selected": {"record": "W-OUTSIDE-01", "forms": ["tag:nom"], "stressed": "err-tok"},
        },
        {
            "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
            "offset": 15,
            "token": "distr-tok",
            "sentence": "distr sent",
            "class": "skipped:item_option",
            "surface": "skipped",
            "selected": None,
        },
    ]
    report = check_lesson("a1", "mod-01", 1, _make_stream(tokens), **paths)
    assert report.ok is True
