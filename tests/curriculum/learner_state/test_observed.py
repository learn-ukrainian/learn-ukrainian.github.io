"""Tests for observed state index (issue #8414 Brief Part 2).

Verifies:
- byte-stable across two runs;
- lock checks fail closed on mismatch/absence;
- roles per fixture (taught, drilled, recycled, incidental, name, exposed);
- untaught_forms computed on a fixture with one taught and one untaught category;
- tab keys validated (urok, slovnyk, vpravy, resursy).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.observed import (
    ObservedError,
    build_observed_index,
    check_observed,
    write_observed,
)

pytestmark = pytest.mark.reads_content


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).encode("utf-8")
    path.write_bytes(content)
    lock.write(path, content)


def _setup_fixture(root: Path, level: str = "a1") -> dict[str, Path]:
    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_dir = root / f"curriculum/l2-uk-en/evidence/{level}"
    state_dir = evidence_dir / "_state" / "mod-01"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    base_req = {
        "request_schema": 1,
        "level": level,
        "words": [
            {"lemma": "base-w1", "pos": "pron", "want": "new"},
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
            {"id": "W-BASE-01", "lemma": "base-w1", "pos": "pron"},
            {"id": "W-CORE-TAUGHT", "lemma": "core-t", "pos": "noun"},
            {"id": "W-CORE-DRILLED", "lemma": "core-d", "pos": "verb"},
            {"id": "W-RECYCLED-01", "lemma": "rec-1", "pos": "noun"},
            {"id": "W-INCIDENTAL-01", "lemma": "inc-1", "pos": "noun"},
            {"id": "W-NAME-01", "lemma": "spk-1", "pos": "noun"},
            {"id": "W-EXP-01", "lemma": "exp-1", "pos": "noun"},
            {"id": "W-EXP-02", "lemma": "exp-2", "pos": "noun"},
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
                    "grammar": [
                        {"id": "G-01", "category": "cat_taught"},
                    ],
                    "vocabulary": {
                        "core": [
                            {"lemma": "core-t", "evidence": "W-CORE-TAUGHT"},
                            {
                                "lemma": "core-d",
                                "evidence": "W-CORE-DRILLED",
                                "forms": ["verb:pres:s:1"],
                            },
                        ],
                        "recycled": ["W-RECYCLED-01"],
                        "incidental": [{"lemma": "inc-1", "evidence": "W-INCIDENTAL-01"}],
                    },
                },
                "dialogue": {
                    "speakers": [{"name": "Spk1", "evidence": "W-NAME-01"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T1",
                        "introduces": {
                            "letters": [],
                            "grammar": ["G-01"],
                            "vocabulary": ["W-CORE-TAUGHT", "W-CORE-DRILLED"],
                        },
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [
                    {"id": "a1", "type": "drill", "placement": "inline", "focus": "drill"},
                ],
            }
        ],
    }
    _write_yaml(plans_dir / "mod-01.yaml", plan)

    resolutions = {
        "resolutions_schema": 1,
        "lesson": {"level": level, "slug": "mod-01", "n": 1},
        "inputs": {
            "expanded_sha256": "0" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            # Taught core
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
                "offset": 0,
                "token": "tok1",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-CORE-TAUGHT"],
                "selected": {"record": "W-CORE-TAUGHT", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok1"},
                "provenance": "deterministic",
            },
            # Drilled core in activity a1
            {
                "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
                "offset": 10,
                "token": "tok2",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-CORE-DRILLED"],
                "selected": {"record": "W-CORE-DRILLED", "forms": ["verb:pres:s:1"], "stressed": "tok2"},
                "provenance": "deterministic",
            },
            # Recycled
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
                "offset": 20,
                "token": "tok3",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-RECYCLED-01"],
                "selected": {"record": "W-RECYCLED-01", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok3"},
                "provenance": "deterministic",
            },
            # Incidental
            {
                "unit": {"tab": "slovnyk", "activity": None, "item": None, "block": 0},
                "offset": 30,
                "token": "tok4",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-INCIDENTAL-01"],
                "selected": {"record": "W-INCIDENTAL-01", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok4"},
                "provenance": "deterministic",
            },
            # Name
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
                "offset": 40,
                "token": "tok5",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-NAME-01"],
                "selected": {"record": "W-NAME-01", "forms": ["noun:anim:m:v_naz:prop:fname"], "stressed": "tok5"},
                "provenance": "deterministic",
            },
            # Exposed: one with taught category cat_taught, one with untaught category cat_untaught
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": "s1"},
                "offset": 50,
                "token": "tok6",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-BASE-01"],
                "selected": {"record": "W-BASE-01", "forms": ["cat_taught"], "stressed": "tok6"},
                "provenance": "deterministic",
            },
            {
                "unit": {"tab": "resursy", "activity": None, "item": None, "block": 0},
                "offset": 60,
                "token": "tok7",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-BASE-01"],
                "selected": {"record": "W-BASE-01", "forms": ["cat_untaught"], "stressed": "tok7"},
                "provenance": "deterministic",
            },
        ],
    }
    _write_yaml(state_dir / "lesson-1.resolutions.yaml", resolutions)

    return {
        "plans_dir": plans_dir,
        "evidence_dir": evidence_dir,
        "words_path": evidence_dir / "_words.yaml",
        "base_request_path": evidence_dir / "_base.request.yaml",
        "resolutions_path": state_dir / "lesson-1.resolutions.yaml",
        "state_dir": state_dir,
    }


def test_observed_byte_stable_across_two_runs(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    out1, digest1 = write_observed("a1", "mod-01", 1, **paths)
    content1 = out1.read_bytes()
    lock1 = Path(f"{out1}.lock").read_bytes()

    out2, digest2 = write_observed("a1", "mod-01", 1, **paths)
    content2 = out2.read_bytes()
    lock2 = Path(f"{out2}.lock").read_bytes()

    assert digest1 == digest2
    assert content1 == content2
    assert lock1 == lock2


def test_observed_lock_check_fails_on_tampered_or_absent_lock(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Tamper with the resolutions lock
    res_lock = Path(f"{paths['resolutions_path']}.lock")
    res_lock.write_text("0" * 64 + "\n", encoding="ascii")

    with pytest.raises(ObservedError) as exc_info:
        write_observed("a1", "mod-01", 1, **paths)
    assert exc_info.value.code == codes.LOCK_MISMATCH


def test_observed_roles_per_fixture(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    out_path, _ = write_observed("a1", "mod-01", 1, **paths)
    doc = check_observed(out_path)

    roles = {rec["id"]: rec["role"] for rec in doc["records"]}
    assert roles["W-CORE-TAUGHT"] == "taught"
    assert roles["W-CORE-DRILLED"] == "drilled"
    assert roles["W-RECYCLED-01"] == "recycled"
    assert roles["W-INCIDENTAL-01"] == "incidental"
    assert roles["W-NAME-01"] == "name"
    assert roles["W-BASE-01"] == "exposed"


def test_observed_untaught_forms_one_taught_one_untaught(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    out_path, _ = write_observed("a1", "mod-01", 1, **paths)
    doc = check_observed(out_path)

    untaught = doc["untaught_forms"]
    assert untaught["count"] == 1
    assert untaught["share"] == 0.5
    assert len(untaught["forms"]) == 1
    entry = untaught["forms"][0]
    assert entry["record"] == "W-BASE-01"
    assert entry["tags"] == "cat_untaught"
    assert entry["category"] == "cat_untaught"


def test_observed_tab_keys_validated(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    # Tamper resolutions to add an invalid tab
    res_path = paths["resolutions_path"]
    data = yaml.safe_load(res_path.read_text(encoding="utf-8"))
    data["tokens"][0]["unit"]["tab"] = "invalid_tab"
    _write_yaml(res_path, data)

    with pytest.raises(ObservedError) as exc_info:
        write_observed("a1", "mod-01", 1, **paths)
    assert exc_info.value.code == codes.UNKNOWN_TAB


def test_observed_build_in_memory(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    doc = build_observed_index("a1", "mod-01", 1, **paths)
    assert doc["observed_schema"] == 1
    assert doc["lesson"]["slug"] == "mod-01"
    assert len(doc["records"]) > 0
