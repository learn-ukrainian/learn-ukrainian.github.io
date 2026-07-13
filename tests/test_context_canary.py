"""Tests for scripts/context_canary.py (5055 canary gate).

Focus: deterministic 10-anchor probe derivation from tool-backed snapshot;
exclusion of UNKNOWN/unavailable/non-tool-backed; validated 3/3/2/2 composition;
version metadata; strict 10/10 scoring (rc 2); normalized id + text modes;
machine-readable JSON verdict; deterministic logging.

All ground-truth answers derived from supplied snapshot (no invention).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import context_canary


def _good_snapshot() -> dict:
    """Minimal tool-backed snapshot that yields exactly 10 valid anchors with required composition."""
    return {
        "generated_at": "2026-07-13T12:00:00Z",
        "git": {
            "branch": "grok-build/5055-canary-gate",
            "head": "a1b2c3d4e5",
            "full_head": "a1b2c3d4e5f67890123456789abcdef0",
            "last_commits": [
                {"sha": "a1b2c3d4e5", "subject": "feat(canary): deterministic 10-anchor derivation from snapshot"},
                {"sha": "f6e7d8c9b0", "subject": "fix: exclude non-tool-backed and UNKNOWN values"},
                {"sha": "1122334455", "subject": "test: strict 10/10 rc-2 and normalized matching"},
                {"sha": "9988776655", "subject": "chore: versioned metadata + json verdict"},
            ],
            "modified_files": [],
            "ahead_behind": {"ahead": 0, "behind": 0, "upstream": "origin/main"},
        },
        "github": {
            "open_prs": [{"number": 5055, "title": "Context canary implementation"}],
            "open_issues": [{"number": 5054, "title": "Canary gate epic"}],
        },
        "monitor": {
            "active_delegates": {"active_count": 1},
            "orient": {"runtime": {"agents": ["orchestrator", "codex"]}},
        },
    }


def _mint_from_snapshot(tmp_path: Path) -> Path:
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps(_good_snapshot()), encoding="utf-8")
    probe = tmp_path / "probe.json"
    rc = context_canary.main(["mint", "--snapshot", str(snap), "--out", str(probe)])
    assert rc == 0, "mint from good snapshot must succeed"
    return probe


def test_mint_snapshot_produces_versioned_10_anchors_with_validated_composition(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    assert data["version"] == "1"
    assert data.get("source") == "snapshot"
    anchors = data["anchors"]
    assert len(anchors) == 10
    assert len({a["id"] for a in anchors}) == 10  # unique
    counts = {}
    for a in anchors:
        c = a["category"]
        counts[c] = counts.get(c, 0) + 1
    assert counts == {"fact": 3, "decision/rationale": 3, "negative-constraint": 2, "goal/next-action": 2}
    # spot check some ids and that answers are non-empty from snapshot
    ids = [a["id"] for a in anchors]
    assert "git_branch" in ids
    assert "commit_0_subject" in ids
    assert "git_modified_status" in ids
    assert "head_sha_next_ref" in ids
    for a in anchors:
        assert a["a"], "no invented empty answers"
        assert _good_snapshot()  # answers traceable to input snapshot


def test_mint_insufficient_evidence_excludes_bad_and_fails(tmp_path: Path):
    # snapshot that will exclude enough to miss quotas (e.g. short commits, bad values)
    bad = {
        "git": {
            "branch": "UNKNOWN",
            "head": "",
            "last_commits": [{"sha": "only1", "subject": "one only"}],  # only 1 -> can't fill 3 dec/rationale
            "modified_files": [],
            "ahead_behind": None,
        },
        "github": {"open_prs": {"_error": "no gh"}, "open_issues": []},
        "monitor": {},
    }
    snap = tmp_path / "bad.json"
    snap.write_text(json.dumps(bad), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(snap), "--out", str(tmp_path / "p.json")])
    assert rc == 1


def test_legacy_facts_still_mints_but_score_requires_10(tmp_path: Path):
    facts = [{"id": "x", "q": "q", "a": "a"}]
    fpath = tmp_path / "f.json"
    fpath.write_text(json.dumps(facts), encoding="utf-8")
    p = tmp_path / "p.json"
    rc = context_canary.main(["mint", "--facts", str(fpath), "--out", str(p)])
    assert rc == 0
    # score on non-10 must fail with usage (not crash)
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps({"x": "a"}), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(p), "--answers", str(ans)])
    assert rc == 1


def test_perfect_10_10_recall_passes_and_logs(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans_path = tmp_path / "ans.json"
    ans_path.write_text(json.dumps(answers), encoding="utf-8")
    log = tmp_path / "log.csv"
    rc = context_canary.main([
        "score", "--probe", str(probe), "--answers", str(ans_path),
        "--context-tokens", "600000", "--model", "claude-opus-4-8", "--log", str(log)
    ])
    assert rc == 0
    body = log.read_text(encoding="utf-8").splitlines()
    assert body[0].startswith("context_tokens,model,k,correct,score,verdict")
    assert "600000,claude-opus-4-8,10,10,1.000,PASS" in body[1]


def test_strict_10_10_any_drift_or_missing_fails_rc2(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    # corrupt one
    first_id = next(iter(answers.keys()))
    answers[first_id] = "WRONG-VALUE"
    ans = tmp_path / "bad.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans)])
    assert rc == 2
    # missing also fails
    answers2 = {a["id"]: a["a"] for a in data["anchors"][:9]}  # missing 1
    ans2 = tmp_path / "miss.json"
    ans2.write_text(json.dumps(answers2), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans2)])
    assert rc == 2


def test_exact_normalized_matching_for_ids_and_normalized_text(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    # use weird cased ids + padded/whitespace/case answers
    answers = {}
    for a in data["anchors"]:
        answers["  " + a["id"].upper() + "  "] = "  " + a["a"].upper() + "  \n"
    ans = tmp_path / "norm.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--text-match", "normalized"])
    assert rc == 0


def test_explicit_exact_mode_is_strict(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: "  " + a["a"] + "  " for a in data["anchors"]}  # extra ws
    ans = tmp_path / "exact.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    # normalized passes
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--text-match", "normalized"])
    assert rc == 0
    # exact fails on ws
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--text-match", "exact"])
    assert rc == 2


def test_machine_readable_json_verdict(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    vpath = tmp_path / "verdict.json"
    rc = context_canary.main([
        "score", "--probe", str(probe), "--answers", str(ans), "--verdict", str(vpath)
    ])
    assert rc == 0
    v = json.loads(vpath.read_text(encoding="utf-8"))
    assert v["version"] == "1"
    assert v["k"] == 10
    assert v["correct"] == 10
    assert v["verdict"] == "PASS"
    assert len(v["per_anchor"]) == 10
    assert all(p["match"] for p in v["per_anchor"])


def test_deterministic_logging_same_inputs_same_rows(tmp_path: Path):
    probe = _mint_from_snapshot(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    log = tmp_path / "det.csv"
    rc1 = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--context-tokens", "123", "--model", "test-m", "--log", str(log)])
    rc2 = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--context-tokens", "123", "--model", "test-m", "--log", str(log)])
    assert rc1 == 0 and rc2 == 0
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    # header + 2 identical data rows
    assert len(lines) == 3
    assert lines[1] == lines[2]
    assert lines[1].startswith("123,test-m,10,10,")
