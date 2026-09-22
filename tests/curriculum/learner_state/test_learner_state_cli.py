"""CLI tests for learner state and immersion band (issue #8414).

Runs the CLI in a clean-environment subprocess with timeout=.
Verifies:
- planned command with text and --json
- band command with text and --json
- --help lists every code registered in codes.py
- Failure scenarios exit with code 1
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.evidence import lock
from scripts.curriculum.learner_state import codes

pytestmark = pytest.mark.reads_content

PYTHON = sys.executable


def _write_yaml(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _setup_fixture(root: Path, level: str = "a1") -> tuple[Path, Path]:
    plans_dir = root / f"curriculum/l2-uk-en/lesson-plans/{level}"
    evidence_dir = root / f"curriculum/l2-uk-en/evidence/{level}"
    plans_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

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
                        "tags": "pron",
                        "stressed": "base-w1",
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
                        "tags": "noun:inanim:m:v_naz",
                        "stressed": "tok1",
                        "stress_source": "ulif",
                        "markers": [],
                        "learner": True,
                    }
                ],
            },
            {
                "id": "W-11",
                "lemma": "core-w2",
                "pos": "verb",
                "forms": [
                    {
                        "form": "core-w2",
                        "tags": "verb:pres:s:1",
                        "stressed": "core-w2",
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
                        "core": [{"lemma": "core-w1", "evidence": "W-10", "forms": ["noun:inanim:m:v_naz"]}],
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
                        "core": [{"lemma": "core-w2", "evidence": "W-11", "forms": ["verb:pres:s:1"]}],
                        "recycled": ["W-10"],
                    }
                },
                "steps": [
                    {
                        "id": "s1",
                        "kind": "teach",
                        "teach": "T2",
                        "introduces": {"letters": [], "grammar": [], "vocabulary": ["W-11"]},
                        "uses": {"grammar": [], "vocabulary": ["W-10"]},
                        "evidence": ["E-02"],
                        "practice": ["a1"],
                    }
                ],
                "activities": [{"id": "a1", "type": "quiz", "placement": "inline", "focus": "Q"}],
            },
        ],
    }
    _write_yaml(plans_dir / "mod-01.yaml", plan)
    return plans_dir, evidence_dir


def test_cli_help_lists_all_codes() -> None:
    res = subprocess.run(
        [PYTHON, "-m", "scripts.curriculum.learner_state", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    for code in codes.DESCRIPTIONS:
        assert code in res.stdout


def test_cli_planned_text_output(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "planned",
            "a1",
            "1",
            "2",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    assert "Planned learner state: level=a1, position=1, lesson=2" in res.stdout
    assert "Cumulative core vocabulary count: 1" in res.stdout


def test_cli_planned_json_output(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "planned",
            "a1",
            "1",
            "2",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["level"] == "a1"
    assert payload["position"] == 1
    assert payload["lesson_n"] == 2
    assert payload["cumulative_core_count"] == 1
    assert "W-10" in payload["core_ids"]
    assert "W-1" in payload["base_ids"]


def test_cli_band_json_output(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "band",
            "a1",
            "1",
            "2",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["band_key"] == "a1-m01-03"
    assert payload["source"] == "ulp_vocab"
    assert codes.LESSON_STRUCTURAL_MINIMUMS_NOT_CALIBRATED in payload["not_checked"]


def test_cli_failing_planned_exits_nonzero(tmp_path: Path) -> None:
    # Empty directory -> no plan found
    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "planned",
            "a1",
            "1",
            "1",
            "--plans-dir",
            str(tmp_path),
            "--evidence-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 1
    assert "Error [base_layer_missing]" in res.stderr


def test_cli_band_a2_json_output() -> None:
    """A2 band loads from arc table without requiring base layer or plans."""
    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "band",
            "a2",
            "1",
            "1",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["band_key"] == "a2-bridge"
    assert payload["source"] == "arc_table"
    assert payload["advisory_uk_share"] == [75, 100]


def test_cli_band_a1_fails_closed_when_prior_plan_missing(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    # Move mod-01.yaml to position 2 so position 1 is missing
    p1 = plans_dir / "mod-01.yaml"
    data = yaml.safe_load(p1.read_text(encoding="utf-8"))
    data["arc_ref"]["position"] = 2
    _write_yaml(plans_dir / "mod-02.yaml", data)
    p1.unlink()

    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "band",
            "a1",
            "2",
            "1",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 1
    assert "prior_plans_missing" in res.stderr


def test_cli_band_a1_allow_missing_prior_includes_waiver(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    # Move mod-01.yaml to position 2 so position 1 is missing
    p1 = plans_dir / "mod-01.yaml"
    data = yaml.safe_load(p1.read_text(encoding="utf-8"))
    data["arc_ref"]["position"] = 2
    _write_yaml(plans_dir / "mod-02.yaml", data)
    p1.unlink()

    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "band",
            "a1",
            "2",
            "1",
            "--allow-missing-prior",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert "waiver" in payload
    assert "prior_plans_missing" in payload["waiver"]


def test_cli_band_a1_strict_refuses_waiver(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    # Move mod-01.yaml to position 2 so position 1 is missing
    p1 = plans_dir / "mod-01.yaml"
    data = yaml.safe_load(p1.read_text(encoding="utf-8"))
    data["arc_ref"]["position"] = 2
    _write_yaml(plans_dir / "mod-02.yaml", data)
    p1.unlink()

    res = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "band",
            "a1",
            "2",
            "1",
            "--allow-missing-prior",
            "--strict",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res.returncode == 1
    assert "prior_plans_missing" in res.stderr


def test_cli_observed_and_gate_pass(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    state_dir = evidence_dir / "_state" / "mod-01"
    state_dir.mkdir(parents=True, exist_ok=True)

    exp_doc = {
        "lesson": {"level": "a1", "slug": "mod-01", "n": 1},
        "units": [{"tab": "urok", "activity": None, "item": None, "block": 0, "role": "record_print", "text": "tok1"}],
    }
    exp_path = state_dir / "lesson-1.expanded.yaml"
    exp_bytes = yaml.safe_dump(exp_doc, allow_unicode=True, sort_keys=False).encode("utf-8")
    exp_path.write_bytes(exp_bytes)
    lock.write(exp_path, exp_bytes)

    res_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 1},
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
                "selected": {"record": "W-10", "forms": ["noun:inanim:m:v_naz"], "stressed": "tok1"},
                "provenance": "deterministic",
            }
        ],
    }
    res_path = state_dir / "lesson-1.resolutions.yaml"
    res_bytes = yaml.safe_dump(res_doc, allow_unicode=True, sort_keys=False).encode("utf-8")
    res_path.write_bytes(res_bytes)
    lock.write(res_path, res_bytes)

    # 1. observed command
    res_obs = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "observed",
            "a1",
            "mod-01",
            "1",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res_obs.returncode == 0
    obs_payload = json.loads(res_obs.stdout)
    assert obs_payload["observed_schema"] == 1
    assert obs_payload["lesson"]["slug"] == "mod-01"
    assert len(obs_payload["records"]) == 1
    assert obs_payload["records"][0]["id"] == "W-10"

    # 2. gate command
    res_gate = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "gate",
            "a1",
            "mod-01",
            "1",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res_gate.returncode == 0
    gate_payload = json.loads(res_gate.stdout)
    assert gate_payload["ok"] is True
    assert gate_payload["failures"] == []


def test_cli_gate_failing_output(tmp_path: Path) -> None:
    plans_dir, evidence_dir = _setup_fixture(tmp_path)
    state_dir = evidence_dir / "_state" / "mod-01"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Token outside allowlist
    res_doc = {
        "resolutions_schema": 1,
        "lesson": {"level": "a1", "slug": "mod-01", "n": 1},
        "inputs": {
            "expanded_sha256": "0" * 64,
            "allowlist_sha256": "0" * 64,
            "words_lock": "0" * 64,
            "vesum": "0" * 64,
            "trie_digest": "0" * 64,
        },
        "tokens": [
            {
                "unit": {"tab": "vpravy", "activity": "a1", "item": 0, "block": 0},
                "offset": 0,
                "token": "bad-tok",
                "surface": "sentence_token",
                "class": "resolved",
                "candidates": ["W-99"],
                "selected": {"record": "W-99", "forms": ["noun:inanim:m:v_naz"], "stressed": "bad-tok"},
                "provenance": "deterministic",
            }
        ],
    }
    res_path = state_dir / "lesson-1.resolutions.yaml"
    res_bytes = yaml.safe_dump(res_doc, allow_unicode=True, sort_keys=False).encode("utf-8")
    res_path.write_bytes(res_bytes)
    lock.write(res_path, res_bytes)

    # Text mode: exits 1 and writes failure to stderr
    res_gate_txt = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "gate",
            "a1",
            "mod-01",
            "1",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res_gate_txt.returncode == 1
    assert "lemma_outside_state" in res_gate_txt.stderr
    assert "bad-tok" in res_gate_txt.stderr
    assert "vpravy" in res_gate_txt.stderr

    # JSON mode: exits 1 and emits ok: false
    res_gate_json = subprocess.run(
        [
            PYTHON,
            "-m",
            "scripts.curriculum.learner_state",
            "gate",
            "a1",
            "mod-01",
            "1",
            "--plans-dir",
            str(plans_dir),
            "--evidence-dir",
            str(evidence_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert res_gate_json.returncode == 1
    payload = json.loads(res_gate_json.stdout)
    assert payload["ok"] is False
    assert len(payload["failures"]) >= 1
    codes_found = {f["code"] for f in payload["failures"]}
    assert "lemma_outside_state" in codes_found
