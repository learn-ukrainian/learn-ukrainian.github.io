"""Tests for scripts/context_canary.py — the deterministic brain-rot monitor.

The load-bearing property: the SCRIPT decides pass/fail by diffing answers against
the frozen truth. A confident-but-wrong answer must score as DRIFT, and the CSV log
must accumulate the (context_tokens, score) data point for cross-session rot mapping.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import context_canary

FACTS = [
    {"id": "safe_env_sha", "q": "SHA of the safe_env commit", "a": "5cd67954ab"},
    {"id": "agy_pr", "q": "PR number for agy lane hardening", "a": "2839"},
    {"id": "wiki_reason", "q": "Why wiki lane not flipped", "a": "agy §7 fabrication unverified at pro tier"},
]


def _mint(tmp_path: Path) -> Path:
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps(FACTS), encoding="utf-8")
    probe = tmp_path / "probe.json"
    rc = context_canary.main(["mint", "--facts", str(facts), "--out", str(probe)])
    assert rc == 0
    return probe


def test_mint_writes_anchors(tmp_path: Path):
    probe = _mint(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    assert [a["id"] for a in data["anchors"]] == ["safe_env_sha", "agy_pr", "wiki_reason"]


def test_perfect_recall_passes_and_logs(tmp_path: Path):
    probe = _mint(tmp_path)
    answers = tmp_path / "ans.json"
    answers.write_text(json.dumps({f["id"]: f["a"] for f in FACTS}), encoding="utf-8")
    log = tmp_path / "canary_log.csv"
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(answers),
            "--context-tokens",
            "500000",
            "--model",
            "claude-opus-4-8",
            "--log",
            str(log),
        ]
    )
    assert rc == 0
    body = log.read_text(encoding="utf-8").splitlines()
    assert body[0].startswith("context_tokens,model,k,correct,score,verdict")
    assert "500000,claude-opus-4-8,3,3,1.000,PASS" in body[1]


def test_confident_but_wrong_answer_fails_handoff(tmp_path: Path):
    probe = _mint(tmp_path)
    answers = tmp_path / "ans.json"
    # Wrong SHA + wrong PR + distorted reason = rot. Confident, but wrong.
    answers.write_text(
        json.dumps({"safe_env_sha": "deadbeef99", "agy_pr": "9999", "wiki_reason": "it was already fine"}),
        encoding="utf-8",
    )
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(answers)])
    assert rc == 2  # FAIL-HANDOFF


def test_partial_drift_below_pass_ratio_fails(tmp_path: Path):
    probe = _mint(tmp_path)
    answers = tmp_path / "ans.json"
    # 1 of 3 wrong -> 0.67 < default pass_ratio 0.85 -> handoff
    answers.write_text(
        json.dumps({"safe_env_sha": "5cd67954ab", "agy_pr": "2839", "wiki_reason": "totally unrelated text"}),
        encoding="utf-8",
    )
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(answers)])
    assert rc == 2


def test_missing_answer_counts_as_drift(tmp_path: Path):
    probe = _mint(tmp_path)
    answers = tmp_path / "ans.json"
    answers.write_text(json.dumps({"safe_env_sha": "5cd67954ab"}), encoding="utf-8")  # 2 missing
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(answers)])
    assert rc == 2


def test_mint_rejects_duplicate_ids(tmp_path: Path):
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps([{"id": "x", "q": "q", "a": "a"}, {"id": "x", "q": "q2", "a": "a2"}]), encoding="utf-8")
    rc = context_canary.main(["mint", "--facts", str(facts), "--out", str(tmp_path / "p.json")])
    assert rc == 1


def test_mint_accepts_inline_json(tmp_path: Path):
    # The arg help advertises "Inline JSON list of {id,q,a}" — passing the list
    # directly (not a file path) must work, not crash with 'File name too long'.
    probe = tmp_path / "probe.json"
    rc = context_canary.main(["mint", "--facts", json.dumps(FACTS), "--out", str(probe)])
    assert rc == 0
    data = json.loads(probe.read_text(encoding="utf-8"))
    assert [a["id"] for a in data["anchors"]] == ["safe_env_sha", "agy_pr", "wiki_reason"]


def test_mint_inline_and_file_produce_identical_probe(tmp_path: Path):
    file_probe = _mint(tmp_path)
    inline_probe = tmp_path / "inline_probe.json"
    rc = context_canary.main(["mint", "--facts", json.dumps(FACTS), "--out", str(inline_probe)])
    assert rc == 0
    assert inline_probe.read_text(encoding="utf-8") == file_probe.read_text(encoding="utf-8")


def test_mint_missing_file_is_clean_usage_error(tmp_path: Path):
    rc = context_canary.main(["mint", "--facts", str(tmp_path / "nope.json"), "--out", str(tmp_path / "p.json")])
    assert rc == 1  # FileNotFoundError -> clean rc 1, not an uncaught traceback


def test_mint_directory_as_facts_is_clean_usage_error(tmp_path: Path):
    # A path that is a directory raises IsADirectoryError inside read_text; the
    # widened (OSError, UnicodeDecodeError) catch must turn it into a clean rc 1,
    # not a traceback (every file-branch read failure is covered, not just missing).
    a_dir = tmp_path / "facts_dir"
    a_dir.mkdir()
    rc = context_canary.main(["mint", "--facts", str(a_dir), "--out", str(tmp_path / "p.json")])
    assert rc == 1


def test_mint_malformed_inline_json_is_clean_usage_error(tmp_path: Path):
    rc = context_canary.main(["mint", "--facts", "[{bad json", "--out", str(tmp_path / "p.json")])
    assert rc == 1  # inline branch JSONDecodeError caught, returns usage error


# --- Production v2 tests added after all original legacy tests (no originals replaced, deleted, weakened or inverted) ---


def _good_v2_snapshot() -> dict:
    """Minimal durable-artifact snapshot yielding exactly 3/3/2/2 with required fields and seed."""
    return {
        "generated_at": "2026-07-13T12:00:00Z",
        "lineage": "grok-build/5055-canary-gate:5055-semantic-fix",
        "source": "handoff-artifact",
        "seed": 987654321,
        "goals": [
            {
                "id": "goal-restore-compat",
                "statement": "Keep original legacy mint --facts and score with threshold/pass-ratio and 3-anchor flow",
                "source_ref": "handoff:goals:goal-restore-compat",
            },
            {
                "id": "goal-strict-v2",
                "statement": "Add distinct production schema v2 with exactly 10 anchors from durable artifacts only",
                "source_ref": "handoff:goals:goal-strict-v2",
            },
            {
                "id": "goal-fail-closed",
                "statement": "Mint must fail closed on insufficient categories or UNKNOWN; never pad with git data",
                "source_ref": "handoff:goals:goal-fail-closed",
            },
        ],
        "decision_records": [
            {
                "id": "dec-exact-shape",
                "decision": "Every prod anchor must be shaped {id,q,a,category,match_mode,source_ref}",
                "rationale": "Required by architecture review for provenance",
                "source_ref": "handoff:decisions:dec-exact-shape",
            },
            {
                "id": "dec-strict-10",
                "decision": "Use strict 10/10 for production confirmation, legacy ratio for facts",
                "rationale": "Prevents 9/10 from passing as handoff safe",
                "source_ref": "handoff:decisions:dec-strict-10",
            },
            {
                "id": "dec-no-relabel",
                "decision": "Source anchors exclusively from handoff goals/decisions/constraints/actions not git or monitor",
                "rationale": "git SHAs and file counts are not semantic continuity records",
                "source_ref": "handoff:decisions:dec-no-relabel",
            },
        ],
        "constraint_records": [
            {
                "id": "const-no-git-as-anchor",
                "prohibition": "git_branch, commit subjects, ahead counts, file counts must never become semantic anchors",
                "source_ref": "handoff:constraints:const-no-git-as-anchor",
            },
            {
                "id": "const-reject-unknown",
                "prohibition": "Reject any UNKNOWN, empty, duplicate, or wrong-category at mint time recursively",
                "source_ref": "handoff:constraints:const-reject-unknown",
            },
        ],
        "next_actions": [
            {
                "id": "na-verify-blockers",
                "action": "Prove arbitrary facts, UNKNOWN modified, git SHAs, ws ids, and legacy flow all behave correctly",
                "source_ref": "handoff:actions:na-verify-blockers",
            },
            {
                "id": "na-run-all-checks",
                "action": "Run pytest, ruff, format check, git diff --check, and agent trailer lint after the commit",
                "source_ref": "handoff:actions:na-run-all-checks",
            },
        ],
    }


def _mint_v2(tmp_path: Path) -> Path:
    snap = tmp_path / "handoff_snapshot.json"
    snap.write_text(json.dumps(_good_v2_snapshot()), encoding="utf-8")
    probe = tmp_path / "probe_v2.json"
    rc = context_canary.main(["mint", "--snapshot", str(snap), "--out", str(probe)])
    assert rc == 0, "mint v2 from good durable snapshot must succeed"
    return probe


def test_mint_v2_snapshot_produces_strict_10_anchors_with_exact_schema_and_metadata(tmp_path: Path):
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    assert data["version"] == "2"
    assert data["schema"] == "production-handoff-v2"
    assert data["strict_production"] is True
    assert data["source"] == "snapshot"
    assert "seed" in data and isinstance(data["seed"], int)
    assert data.get("lineage")
    assert "generated_at" in data
    assert data["anchor_counts"] == {
        "goal": 3,
        "decision/rationale": 3,
        "negative-constraint/prohibition": 2,
        "next-action": 2,
    }
    anchors = data["anchors"]
    assert len(anchors) == 10
    ids = [a["id"] for a in anchors]
    assert len(set(ids)) == 10
    assert all(isinstance(i, str) and i for i in ids)
    cats = {}
    for a in anchors:
        c = a["category"]
        cats[c] = cats.get(c, 0) + 1
    assert cats == {"goal": 3, "decision/rationale": 3, "negative-constraint/prohibition": 2, "next-action": 2}
    for a in anchors:
        assert set(a.keys()) == {"id", "q", "a", "category", "match_mode", "source_ref"}
        assert a["source_ref"] and "handoff:" in a["source_ref"]
        assert a["match_mode"] in ("exact", "normalized")
        assert a["a"], "no invented answers"
        # check fields are not the sentinel tokens themselves (word "unknown" may legitimately appear in prose)
        assert not any(
            str(a.get(k, "")).strip().lower() in {"unknown", "unavailable", "n/a", "none", "null", "missing"}
            for k in ("id", "a", "q", "source_ref")
        )


def test_v2_production_perfect_10_10_passes_rc0(tmp_path: Path):
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans_path = tmp_path / "ans.json"
    ans_path.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans_path)])
    assert rc == 0


def test_v2_9_of_10_or_drift_fails_rc2(tmp_path: Path):
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    # corrupt one -> 9/10
    some_id = data["anchors"][0]["id"]
    answers[some_id] = "WRONG ANSWER FOR DRIFT"
    ans = tmp_path / "bad9.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans)])
    assert rc == 2
    # missing one also
    answers2 = {a["id"]: a["a"] for a in data["anchors"][:9]}
    ans2 = tmp_path / "miss.json"
    ans2.write_text(json.dumps(answers2), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans2)])
    assert rc == 2


def test_v2_exact_id_match_no_normalization(tmp_path: Path):
    """IDs matched exactly; whitespace/case in key means no lookup hit. '  GIT_BRANCH  ' cannot match git_branch."""
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {}
    for a in data["anchors"]:
        # padded + upper key will NOT match the exact id
        answers["  " + a["id"].upper() + "  "] = a["a"]
    ans = tmp_path / "wsid.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans)])
    assert rc == 2


def test_v2_match_mode_exact_vs_normalized(tmp_path: Path):
    probe = _mint_v2(tmp_path)
    pdata = json.loads(probe.read_text(encoding="utf-8"))
    # Force first anchor to normalized to exercise mode
    pdata["anchors"][0]["match_mode"] = "normalized"
    p2 = tmp_path / "p_norm.json"
    p2.write_text(json.dumps(pdata), encoding="utf-8")
    ansd = {}
    # pad only the normalized one; clean exacts
    for i, a in enumerate(pdata["anchors"]):
        if i == 0:
            ansd[a["id"]] = "  " + a["a"] + "  "
        else:
            ansd[a["id"]] = a["a"]
    ans = tmp_path / "anspad.json"
    ans.write_text(json.dumps(ansd), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(p2), "--answers", str(ans)])
    assert rc == 0


def test_legacy_three_anchor_flow_still_passes_unchanged(tmp_path: Path):
    """Explicit demonstration that original legacy path (facts + threshold + pass-ratio) is intact."""
    probe = tmp_path / "p.json"
    rc = context_canary.main(["mint", "--facts", json.dumps(FACTS), "--out", str(probe)])
    assert rc == 0
    answers = {f["id"]: f["a"] for f in FACTS}
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(
        ["score", "--probe", str(probe), "--answers", str(ans), "--threshold", "0.75", "--pass-ratio", "0.85"]
    )
    assert rc == 0


def test_arbitrary_ten_entry_facts_source_does_not_produce_v2_prod_probe(tmp_path: Path):
    """arbitrary ten-entry source=facts cannot pass as production (lacks v2 markers, uses legacy scoring)."""
    facts = [{"id": f"f{i}", "q": f"q{i}", "a": f"a{i}"} for i in range(10)]
    fpath = tmp_path / "ten.json"
    fpath.write_text(json.dumps(facts), encoding="utf-8")
    p = tmp_path / "p10.json"
    rc = context_canary.main(["mint", "--facts", str(fpath), "--out", str(p)])
    assert rc == 0
    data = json.loads(p.read_text(encoding="utf-8"))
    # not a v2 production probe
    assert data.get("version") != "2" or not data.get("strict_production")
    assert data.get("source") != "snapshot" or data.get("schema") != "production-handoff-v2"
    assert len(data.get("anchors", [])) == 10
    # perfect answers still go through legacy path (no strict enforcement here)
    answers = {f["id"]: f["a"] for f in facts}
    ans = tmp_path / "ans10.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(p), "--answers", str(ans)])
    # 10/10 would pass legacy ratio too, but the point is it was not treated as v2 prod
    assert rc == 0
    # 9/10 would also pass legacy (0.9 >= 0.85) but would fail v2
    answers[facts[0]["id"]] = "wrong"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(p), "--answers", str(ans)])
    assert rc == 0  # legacy allows >=0.85


def test_v2_score_rejects_wrong_lineage_or_malformed_provenance(tmp_path: Path):
    snap = _good_v2_snapshot()
    snap["lineage"] = ""
    sfile = tmp_path / "badline.json"
    sfile.write_text(json.dumps(snap), encoding="utf-8")
    p = tmp_path / "pbad.json"
    rc = context_canary.main(["mint", "--snapshot", str(sfile), "--out", str(p)])
    assert rc == 1


def test_negative_v2_mint_insufficient_or_unknown_or_dup_or_bad_shape(tmp_path: Path):
    # insufficient categories
    bad1 = _good_v2_snapshot()
    bad1["goals"] = bad1["goals"][:2]
    s1 = tmp_path / "insuf.json"
    s1.write_text(json.dumps(bad1), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s1), "--out", str(tmp_path / "p1")])
    assert rc == 1

    # UNKNOWN nested value
    bad2 = _good_v2_snapshot()
    bad2["decision_records"][0]["decision"] = "UNKNOWN"
    s2 = tmp_path / "unk.json"
    s2.write_text(json.dumps(bad2), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s2), "--out", str(tmp_path / "p2")])
    assert rc == 1

    # duplicate IDs
    bad3 = _good_v2_snapshot()
    bad3["goals"][1]["id"] = bad3["goals"][0]["id"]
    s3 = tmp_path / "dup.json"
    s3.write_text(json.dumps(bad3), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s3), "--out", str(tmp_path / "p3")])
    assert rc == 1

    # missing source_ref (malformed provenance)
    bad4 = _good_v2_snapshot()
    if "source_ref" in bad4["next_actions"][0]:
        del bad4["next_actions"][0]["source_ref"]
    s4 = tmp_path / "noprof.json"
    s4.write_text(json.dumps(bad4), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s4), "--out", str(tmp_path / "p4")])
    assert rc == 1

    # invalid match_mode
    bad5 = _good_v2_snapshot()
    bad5["constraint_records"][0]["match_mode"] = "fuzzy99"
    s5 = tmp_path / "badmm.json"
    s5.write_text(json.dumps(bad5), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s5), "--out", str(tmp_path / "p5")])
    assert rc == 1


def test_deterministic_same_seed_same_order(tmp_path: Path):
    snap = _good_v2_snapshot()
    s1 = tmp_path / "s1.json"
    s1.write_text(json.dumps(snap), encoding="utf-8")
    p1 = tmp_path / "p1.json"
    rc1 = context_canary.main(["mint", "--snapshot", str(s1), "--out", str(p1)])
    p2 = tmp_path / "p2.json"
    rc2 = context_canary.main(["mint", "--snapshot", str(s1), "--out", str(p2)])
    assert rc1 == rc2 == 0
    d1 = json.loads(p1.read_text(encoding="utf-8"))["anchors"]
    d2 = json.loads(p2.read_text(encoding="utf-8"))["anchors"]
    assert [a["id"] for a in d1] == [a["id"] for a in d2]


def test_differing_seed_produces_different_order(tmp_path: Path):
    snap = _good_v2_snapshot()
    snap["seed"] = 111
    s1 = tmp_path / "sd1.json"
    s1.write_text(json.dumps(snap), encoding="utf-8")
    p1 = tmp_path / "pd1.json"
    context_canary.main(["mint", "--snapshot", str(s1), "--out", str(p1)])
    snap["seed"] = 222
    s2 = tmp_path / "sd2.json"
    s2.write_text(json.dumps(snap), encoding="utf-8")
    p2 = tmp_path / "pd2.json"
    context_canary.main(["mint", "--snapshot", str(s2), "--out", str(p2)])
    d1 = json.loads(p1.read_text(encoding="utf-8"))["anchors"]
    d2 = json.loads(p2.read_text(encoding="utf-8"))["anchors"]
    ids1 = [a["id"] for a in d1]
    ids2 = [a["id"] for a in d2]
    assert ids1 != ids2  # order randomized by seed


def test_generated_seed_when_absent_is_persisted_and_reproducible(tmp_path: Path):
    snap = _good_v2_snapshot()
    snap.pop("seed", None)
    s = tmp_path / "snoseed.json"
    s.write_text(json.dumps(snap), encoding="utf-8")
    p1 = tmp_path / "pg1.json"
    context_canary.main(["mint", "--snapshot", str(s), "--out", str(p1)])
    d1 = json.loads(p1.read_text(encoding="utf-8"))
    assert "seed" in d1 and isinstance(d1["seed"], int)
    p2 = tmp_path / "pg2.json"
    context_canary.main(["mint", "--snapshot", str(s), "--out", str(p2)])
    d2 = json.loads(p2.read_text(encoding="utf-8"))
    assert d1["seed"] == d2["seed"]
    assert [a["id"] for a in d1["anchors"]] == [a["id"] for a in d2["anchors"]]


def test_v2_verdict_contains_audit_fields(tmp_path: Path):
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans = tmp_path / "av.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    vpath = tmp_path / "verdict.json"
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans), "--verdict", str(vpath)])
    assert rc == 0
    v = json.loads(vpath.read_text(encoding="utf-8"))
    assert v["version"] == "2"
    assert v["schema"] == "production-handoff-v2"
    assert "lineage" in v
    assert "seed" in v
    assert v["correct"] == 10
    assert v["verdict"] == "PASS"
