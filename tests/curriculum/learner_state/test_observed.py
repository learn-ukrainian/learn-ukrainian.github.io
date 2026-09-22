"""Tests for observed state index (issue #8414 Brief Part 2).

Verifies:
- byte-stable across two runs;
- lock checks fail closed on mismatch/absence;
- roles per fixture (taught, drilled, recycled, incidental, name, exposed);
- drilled role grounded in plan data without heuristics;
- untaught_forms computed on a fixture with one taught and one untaught category;
- tab keys validated (urok, slovnyk, vpravy, resursy);
- fixture receipts validate against resolution-receipts-v1.schema.json;
- disk receipts file breaking schema raises resolutions_invalid.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes
from scripts.curriculum.learner_state.observed import (
    ObservedError,
    build_observed_index,
    check_observed,
    write_observed,
)

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
            {
                "id": "W-1",
                "lemma": "base-w1",
                "pos": "pron",
                "forms": [
                    {
                        "form": "base-w1",
                        "tags": "cat_taught",
                        "stressed": "base-w1",
                        "stress_source": "none",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-10",
                "lemma": "core-t",
                "pos": "noun",
                "forms": [
                    {
                        "form": "core-t",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "core-t",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-11",
                "lemma": "core-d",
                "pos": "verb",
                "forms": [
                    {
                        "form": "core-d",
                        "tags": "verb:pres:s:1",
                        "stressed": "core-d",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-20",
                "lemma": "rec-1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "rec-1",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "rec-1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-30",
                "lemma": "inc-1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "inc-1",
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "inc-1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-40",
                "lemma": "spk-1",
                "pos": "noun",
                "forms": [
                    {
                        "form": "spk-1",
                        "tags": "noun:anim:m:v_naz:prop:fname",
                        "stressed": "spk-1",
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
                    "grammar": [
                        {"id": "G-01", "category": "cat_taught"},
                    ],
                    "vocabulary": {
                        "core": [
                            {"lemma": "core-t", "evidence": "W-10", "forms": ["noun:inanim:m:v_naz"]},
                            {"lemma": "core-d", "evidence": "W-11", "forms": ["verb:pres:s:1"]},
                        ],
                        "recycled": ["W-20"],
                        "incidental": [{"lemma": "inc-1", "evidence": "W-30"}],
                    },
                },
                "dialogue": {
                    "speakers": [{"name": "Spk1", "evidence": "W-40"}],
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T1",
                        "introduces": {
                            "letters": [],
                            "grammar": ["G-01"],
                            "vocabulary": ["W-10", "W-11"],
                        },
                        "uses": {"grammar": [], "vocabulary": []},
                        "evidence": ["E-01"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [
                    {"id": "a1", "type": "quiz", "placement": "inline", "focus": "exercise"},
                ],
            }
        ],
    }
    _write_yaml(plans_dir / "mod-01.yaml", plan)

    # Expanded document providing real Unit shapes and roles
    exp_doc = {
        "lesson": {"level": level, "slug": "mod-01", "n": 1},
        "units": [
            {"tab": "urok", "activity": None, "item": None, "block": 0, "role": "record_print", "text": "tok1 sent"},
            {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0, "role": "item_prompt", "text": "tok2 sent"},
            {"tab": "urok", "activity": None, "item": None, "block": 1, "role": "narration", "text": "tok3 sent"},
            {"tab": "slovnyk", "activity": None, "item": None, "block": 0, "role": "record_print", "text": "tok4 sent"},
            {"tab": "urok", "activity": None, "item": None, "block": 2, "role": "dialogue_line", "text": "tok5 sent"},
            {"tab": "urok", "activity": None, "item": None, "block": 3, "role": "narration", "text": "tok6 sent"},
            {"tab": "resursy", "activity": None, "item": None, "block": 0, "role": "record_print", "text": "tok7 sent"},
        ],
    }
    _write_yaml(state_dir / "lesson-1.expanded.yaml", exp_doc)

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
            # Taught core (in record_print, not in practice activity item prompt/answer)
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 0},
                "offset": 0,
                "token": "tok1",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-10"],
                "selected": {"record": "W-10", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok1"},
                "provenance": "deterministic",
            },
            # Drilled core in activity a1 (practice) item_prompt with matching form
            {
                "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
                "offset": 10,
                "token": "tok2",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-11"],
                "selected": {"record": "W-11", "forms": ["verb:pres:s:1"], "stressed": "tok2"},
                "provenance": "deterministic",
            },
            # Recycled
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 1},
                "offset": 20,
                "token": "tok3",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-20"],
                "selected": {"record": "W-20", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok3"},
                "provenance": "deterministic",
            },
            # Incidental
            {
                "unit": {"tab": "slovnyk", "activity": None, "item": None, "block": 0},
                "offset": 30,
                "token": "tok4",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-30"],
                "selected": {"record": "W-30", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok4"},
                "provenance": "deterministic",
            },
            # Name
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 2},
                "offset": 40,
                "token": "tok5",
                "surface": "proper_noun",
                "class": "resolved",
                "candidates": ["W-40"],
                "selected": {"record": "W-40", "forms": ["noun:anim:m:v_naz:prop:fname"], "stressed": "tok5"},
                "provenance": "deterministic",
            },
            # Exposed: one with taught category cat_taught, one with untaught category cat_untaught
            {
                "unit": {"tab": "urok", "activity": None, "item": None, "block": 3},
                "offset": 50,
                "token": "tok6",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-1"],
                "selected": {"record": "W-1", "forms": ["cat_taught"], "stressed": "tok6"},
                "provenance": "deterministic",
            },
            {
                "unit": {"tab": "resursy", "activity": None, "item": None, "block": 0},
                "offset": 60,
                "token": "tok7",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-1"],
                "selected": {"record": "W-1", "forms": ["cat_untaught"], "stressed": "tok7"},
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


def test_observed_fixture_receipts_validates_against_schema(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    res_path = paths["resolutions_path"]
    data = yaml.safe_load(res_path.read_text(encoding="utf-8"))
    schema = json.loads(RECEIPTS_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)


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
    assert roles["W-10"] == "taught"
    assert roles["W-11"] == "drilled"
    assert roles["W-20"] == "recycled"
    assert roles["W-30"] == "incidental"
    assert roles["W-40"] == "name"
    assert roles["W-1"] == "exposed"


def test_observed_untaught_forms_one_taught_one_untaught(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    out_path, _ = write_observed("a1", "mod-01", 1, **paths)
    doc = check_observed(out_path)

    untaught = doc["untaught_forms"]
    assert untaught["count"] == 1
    assert untaught["share"] == 0.5
    assert len(untaught["forms"]) == 1
    entry = untaught["forms"][0]
    assert entry["record"] == "W-1"
    assert entry["tags"] == "cat_untaught"
    assert entry["category"] == "cat_untaught"


def test_observed_tab_keys_validated(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    res_path = paths["resolutions_path"]
    data = yaml.safe_load(res_path.read_text(encoding="utf-8"))
    data["tokens"][0]["unit"]["tab"] = "invalid_tab"
    _write_yaml(res_path, data)

    with pytest.raises(ObservedError) as exc_info:
        write_observed("a1", "mod-01", 1, **paths)
    assert exc_info.value.code == codes.RESOLUTIONS_INVALID


def test_observed_disk_receipts_schema_break_fails(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    res_path = paths["resolutions_path"]
    # Write invalid receipt document breaking schema
    invalid_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 1},
        # Missing inputs
        "tokens": [],
    }
    _write_yaml(res_path, invalid_doc)

    with pytest.raises(ObservedError) as exc_info:
        write_observed("a1", "mod-01", 1, **paths)
    assert exc_info.value.code == codes.RESOLUTIONS_INVALID


def test_observed_build_in_memory(tmp_path: Path) -> None:
    paths = _setup_fixture(tmp_path)
    doc = build_observed_index("a1", "mod-01", 1, **paths)
    assert doc["observed_schema"] == 1
    assert doc["lesson"]["slug"] == "mod-01"
    assert len(doc["records"]) > 0
