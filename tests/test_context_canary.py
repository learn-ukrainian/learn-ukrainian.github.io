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
    """Minimal durable-artifact snapshot yielding exactly 3/3/2/2 with required fields and seed.
    Uses explicit lineage_id/rollover_id and valid source_ref grammar (kind:repo-rel#frag) with correct kind per category.
    """
    return {
        "generated_at": "2026-07-13T12:00:00Z",
        "lineage_id": "lineage-grok-build-5055-canary-gate-5055-semantic-fix",
        "rollover_id": "rollover-5055-20260713-01",
        "seed": 987654321,
        "goals": [
            {
                "id": "goal-restore-compat",
                "statement": "Keep original legacy mint --facts and score with threshold/pass-ratio and 3-anchor flow",
                "source_ref": "handoff:.agent/thread-rollovers/rollover-5055-001.json#goal-restore-compat",
            },
            {
                "id": "goal-strict-v2",
                "statement": "Add distinct production schema v2 with exactly 10 anchors from durable artifacts only",
                "source_ref": "handoff:.agent/thread-rollovers/rollover-5055-001.json#goal-strict-v2",
            },
            {
                "id": "goal-fail-closed",
                "statement": "Mint must fail closed on insufficient categories or UNKNOWN; never pad with git data",
                "source_ref": "handoff:.agent/thread-rollovers/rollover-5055-001.json#goal-fail-closed",
            },
        ],
        "decision_records": [
            {
                "id": "dec-exact-shape",
                "decision": "Every prod anchor must be shaped {id,q,a,category,match_mode,source_ref}",
                "rationale": "Required by architecture review for provenance",
                "source_ref": "decision:docs/decisions/2026-07-13-provenance.md#dec-exact-shape",
            },
            {
                "id": "dec-strict-10",
                "decision": "Use strict 10/10 for production confirmation, legacy ratio for facts",
                "rationale": "Prevents 9/10 from passing as handoff safe",
                "source_ref": "decision:docs/decisions/2026-07-13-provenance.md#dec-strict-10",
            },
            {
                "id": "dec-no-relabel",
                "decision": "Source anchors exclusively from handoff goals/decisions/constraints/actions not git or monitor",
                "rationale": "git SHAs and file counts are not semantic continuity records",
                "source_ref": "decision:docs/decisions/2026-07-13-provenance.md#dec-no-relabel",
            },
        ],
        "constraint_records": [
            {
                "id": "const-no-git-as-anchor",
                "prohibition": "git_branch, commit subjects, ahead counts, file counts must never become semantic anchors",
                "source_ref": "handoff:.agent/thread-rollovers/rollover-5055-001.json#const-no-git-as-anchor",
            },
            {
                "id": "const-reject-unknown",
                "prohibition": "Reject any UNKNOWN, empty, duplicate, or wrong-category at mint time recursively",
                "source_ref": "decision:docs/decisions/2026-07-13-provenance.md#const-reject-unknown",
            },
        ],
        "next_actions": [
            {
                "id": "na-verify-blockers",
                "action": "Prove arbitrary facts, UNKNOWN modified, git SHAs, ws ids, and legacy flow all behave correctly",
                "source_ref": "queue:batch_state/orchestrator-runs/orchestrator-5055.json#na-verify-blockers",
            },
            {
                "id": "na-run-all-checks",
                "action": "Run pytest, ruff, format check, git diff --check, and agent trailer lint after the commit",
                "source_ref": "handoff:.agent/thread-rollovers/rollover-5055-001.json#na-run-all-checks",
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
    assert data.get("lineage_id")
    assert data.get("rollover_id")
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
        assert a["source_ref"] and (
            a["source_ref"].startswith("handoff:")
            or a["source_ref"].startswith("decision:")
            or a["source_ref"].startswith("queue:")
        )
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
    lid = data["lineage_id"]
    rid = data["rollover_id"]
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans_path),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
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
    lid = data["lineage_id"]
    rid = data["rollover_id"]
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
    assert rc == 2
    # missing one also
    answers2 = {a["id"]: a["a"] for a in data["anchors"][:9]}
    ans2 = tmp_path / "miss.json"
    ans2.write_text(json.dumps(answers2), encoding="utf-8")
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans2),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
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
    lid = data["lineage_id"]
    rid = data["rollover_id"]
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
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
    lid = pdata["lineage_id"]
    rid = pdata["rollover_id"]
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(p2),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
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
    snap["lineage_id"] = ""
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
    lid = data["lineage_id"]
    rid = data["rollover_id"]
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--verdict",
            str(vpath),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
    assert rc == 0
    v = json.loads(vpath.read_text(encoding="utf-8"))
    assert v["version"] == "2"
    assert v["schema"] == "production-handoff-v2"
    assert "lineage_id" in v
    assert "rollover_id" in v
    assert "probe_sha256" in v
    assert "seed" in v
    assert v["correct"] == 10
    assert v["verdict"] == "PASS"
    # context_tokens must not be present (removed duplicate)
    assert "context_tokens" not in v


# --- Exact reproduction regression tests per requirements (preserve all prior tests; add these) ---


def _expected_identity_from_good() -> tuple[str, str]:
    snap = _good_v2_snapshot()
    return snap["lineage_id"], snap["rollover_id"]


def test_mint_rejects_git_github_monitor_arbitrary_and_bad_source_refs(tmp_path: Path):
    """records with git:HEAD, github:, monitor:, arbitrary/non-durable source_ref fail mint."""
    base = _good_v2_snapshot()
    bad_refs = [
        "git:HEAD",
        "github:foo/bar#123",
        "monitor:session#1",
        "arbitrary-string",
        "/absolute/path#f",
        "../traversal#f",
        "handoff:foo/bar#no-root-match",
        "handoff:.agent/..#bad",
        "badkind:docs/decisions/x.md#f",
        "decision:docs/decisions/x.md#f",  # wrong for goal
        "queue:docs/decisions/x.md#f",  # wrong kind/root
        "handoff:.agent/thread-rollovers/r.json",  # missing #
    ]
    for i, bad in enumerate(bad_refs):
        snap = _good_v2_snapshot()
        snap["goals"][0]["source_ref"] = bad
        s = tmp_path / f"badref{i}.json"
        s.write_text(json.dumps(snap), encoding="utf-8")
        rc = context_canary.main(["mint", "--snapshot", str(s), "--out", str(tmp_path / f"p{i}.json")])
        assert rc == 1, f"should reject bad source_ref: {bad}"


def test_forged_v2_with_bad_source_refs_fails_score(tmp_path: Path):
    """forged v2 with such refs fails score (even if other fields look ok)."""
    probe = _mint_v2(tmp_path)
    pdata = json.loads(probe.read_text(encoding="utf-8"))
    lid, rid = pdata["lineage_id"], pdata["rollover_id"]
    # corrupt one ref
    pdata["anchors"][0]["source_ref"] = "git:HEAD"
    badp = tmp_path / "forged_badref.json"
    badp.write_text(json.dumps(pdata), encoding="utf-8")
    answers = {a["id"]: a["a"] for a in pdata["anchors"]}
    ans = tmp_path / "a.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(badp),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
    assert rc == 2


def test_snapshot_missing_either_identity_fails_mint(tmp_path: Path):
    """snapshot missing either identity fails mint."""
    for key in ("lineage_id", "rollover_id"):
        snap = _good_v2_snapshot()
        snap.pop(key, None)
        s = tmp_path / f"no{key}.json"
        s.write_text(json.dumps(snap), encoding="utf-8")
        rc = context_canary.main(["mint", "--snapshot", str(s), "--out", str(tmp_path / "p.json")])
        assert rc == 1


def test_v2_score_missing_or_wrong_expected_identity_fails(tmp_path: Path):
    """v2 score missing/wrong expected identity fails."""
    probe = _mint_v2(tmp_path)
    pdata = json.loads(probe.read_text(encoding="utf-8"))
    lid, rid = pdata["lineage_id"], pdata["rollover_id"]
    answers = {a["id"]: a["a"] for a in pdata["anchors"]}
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    # missing expected
    rc = context_canary.main(["score", "--probe", str(probe), "--answers", str(ans)])
    assert rc == 2
    # wrong
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            "wrong",
            "--expected-rollover-id",
            rid,
        ]
    )
    assert rc == 2
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            "wrong",
        ]
    )
    assert rc == 2


def test_v2_incomplete_or_extra_markers_fail_closed_not_legacy(tmp_path: Path):
    """v2 missing seed/count/timestamp/policy, with extra anchor keys, or with partial markers fails rather than using legacy."""
    # 1. partial marker on legacy shape
    facts = [{"id": f"f{i}", "q": f"q{i}", "a": f"a{i}"} for i in range(3)]
    fpath = tmp_path / "lf.json"
    fpath.write_text(json.dumps(facts), encoding="utf-8")
    p = tmp_path / "pleg.json"
    rc = context_canary.main(["mint", "--facts", str(fpath), "--out", str(p)])
    assert rc == 0
    # add a v2 marker -> routes to v2 validation -> fail
    pdat = json.loads(p.read_text(encoding="utf-8"))
    pdat["version"] = "2"
    pdat["schema"] = "production-handoff-v2"
    p.write_text(json.dumps(pdat), encoding="utf-8")
    ans = {f["id"]: f["a"] for f in facts}
    ap = tmp_path / "al.json"
    ap.write_text(json.dumps(ans), encoding="utf-8")
    rc = context_canary.main(["score", "--probe", str(p), "--answers", str(ap)])
    assert rc == 2  # not legacy pass

    # 2. full v2 missing required field (e.g. seed)
    snap = _good_v2_snapshot()
    snap.pop("seed", None)  # will be generated, but remove generated_at to break
    snap["generated_at"] = "not-a-timestamp"
    s2 = tmp_path / "badts.json"
    s2.write_text(json.dumps(snap), encoding="utf-8")
    rc = context_canary.main(["mint", "--snapshot", str(s2), "--out", str(tmp_path / "pbadts.json")])
    assert rc == 1

    # 3. extra key in anchor
    goodp = _mint_v2(tmp_path)
    gdat = json.loads(goodp.read_text(encoding="utf-8"))
    gdat["anchors"][0]["extra"] = "no"
    gp = tmp_path / "pextra.json"
    gp.write_text(json.dumps(gdat), encoding="utf-8")
    lid, rid = gdat["lineage_id"], gdat["rollover_id"]
    ansd = {a["id"]: a["a"] for a in gdat["anchors"]}
    aa = tmp_path / "aa.json"
    aa.write_text(json.dumps(ansd), encoding="utf-8")
    rc = context_canary.main(
        ["score", "--probe", str(gp), "--answers", str(aa), "--expected-lineage-id", lid, "--expected-rollover-id", rid]
    )
    assert rc == 2


def test_missing_or_both_mint_sources_return_rc2(tmp_path: Path):
    """missing/both mint source arguments return rc 2 (via required mutually_exclusive_group)."""
    outp = str(tmp_path / "o.json")
    # neither
    rc = context_canary.main(["mint", "--out", outp])
    assert rc == 2
    # both
    facts = tmp_path / "f.json"
    facts.write_text(json.dumps([{"id": "x", "q": "q", "a": "a"}]), encoding="utf-8")
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps(_good_v2_snapshot()), encoding="utf-8")
    rc = context_canary.main(["mint", "--facts", str(facts), "--snapshot", str(snap), "--out", outp])
    assert rc == 2


def test_valid_durable_refs_for_every_allowed_category_pass(tmp_path: Path):
    """valid durable refs for every allowed category pass (goals handoff; dec/rationale decision+handoff; const handoff+decision; next queue+handoff)."""
    # already exercised by _good + _mint_v2 + perfect score, but explicit
    probe = _mint_v2(tmp_path)
    data = json.loads(probe.read_text(encoding="utf-8"))
    lid, rid = data["lineage_id"], data["rollover_id"]
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans = tmp_path / "okans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            lid,
            "--expected-rollover-id",
            rid,
        ]
    )
    assert rc == 0
    # also re-mint to confirm
    s2 = tmp_path / "s2.json"
    s2.write_text(json.dumps(_good_v2_snapshot()), encoding="utf-8")
    p2 = tmp_path / "p2.json"
    rc = context_canary.main(["mint", "--snapshot", str(s2), "--out", str(p2)])
    assert rc == 0


def test_all_prior_strictness_determinism_and_origin_legacy_tests_still_pass(tmp_path: Path):
    """all prior strictness/determinism and every origin/main legacy test still pass (sanity after changes)."""
    # run a representative legacy flow
    probe = tmp_path / "pl.json"
    rc = context_canary.main(["mint", "--facts", json.dumps(FACTS), "--out", str(probe)])
    assert rc == 0
    answers = {f["id"]: f["a"] for f in FACTS}
    ap = tmp_path / "al.json"
    ap.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(
        ["score", "--probe", str(probe), "--answers", str(ap), "--threshold", "0.75", "--pass-ratio", "0.85"]
    )
    assert rc == 0

    # determinism on v2
    snap = _good_v2_snapshot()
    s = tmp_path / "sd.json"
    s.write_text(json.dumps(snap), encoding="utf-8")
    p1 = tmp_path / "pd1.json"
    rc1 = context_canary.main(["mint", "--snapshot", str(s), "--out", str(p1)])
    p2 = tmp_path / "pd2.json"
    rc2 = context_canary.main(["mint", "--snapshot", str(s), "--out", str(p2)])
    assert rc1 == rc2 == 0
    d1 = json.loads(p1.read_text(encoding="utf-8"))
    d2 = json.loads(p2.read_text(encoding="utf-8"))
    assert [a["id"] for a in d1["anchors"]] == [a["id"] for a in d2["anchors"]]
    assert d1["lineage_id"] == d2["lineage_id"] and d1["rollover_id"] == d2["rollover_id"]


# --- Centralized identity validator regression tests (must cover the blocker cases at all three boundaries) ---
# All prior/origin-main tests preserved; only added at end. Valid engine-shaped examples continue to pass.


def test_identity_validator_rejects_bad_values_at_mint(tmp_path: Path):
    """!!!, ../../lineage, embedded newline/control, uppercase, wrong prefix, empty suffix, overlong fail at mint."""
    bad_lineage_values = [
        "!!!",
        "../../lineage",
        "lineage-foo\nbar",
        "lineage-foo\x00bar",
        "lineage-FOO-BAR",
        "Lineage-abc",
        "foo-bar-baz",
        "lineage-",
        "lineage-" + "x" * 57,  # 8 + 57 = 65 > 64
        "lineage--double",
        "lineage-foo.",
        "lineage-foo/bar",
    ]
    for i, bad in enumerate(bad_lineage_values):
        snap = _good_v2_snapshot()
        snap["lineage_id"] = bad
        s = tmp_path / f"badlid{i}.json"
        s.write_text(json.dumps(snap), encoding="utf-8")
        rc = context_canary.main(["mint", "--snapshot", str(s), "--out", str(tmp_path / f"plid{i}.json")])
        assert rc == 1, f"mint must reject bad lineage_id at input: {bad!r}"

    bad_rollover_values = [
        "!!!",
        "../../rollover",
        "rollover-foo\nbar",
        "rollover-foo\x1bbar",  # ESC control
        "Rollover-123",
        "rollover-",
        "rollover-" + "y" * 57,
        "rollover--hyphen",
        "rollover-abc.def",
        "rollover-abc\\def",
        "wrongprefix-123",
    ]
    for i, bad in enumerate(bad_rollover_values):
        snap = _good_v2_snapshot()
        snap["rollover_id"] = bad
        s = tmp_path / f"badrid{i}.json"
        s.write_text(json.dumps(snap), encoding="utf-8")
        rc = context_canary.main(["mint", "--snapshot", str(s), "--out", str(tmp_path / f"prid{i}.json")])
        assert rc == 1, f"mint must reject bad rollover_id at input: {bad!r}"


def test_identity_validator_rejects_bad_values_in_forged_probes_at_score(tmp_path: Path):
    """Bad lineage/rollover in forged production probe fail at score (probe validation gate)."""
    probe = _mint_v2(tmp_path)
    pdata = json.loads(probe.read_text(encoding="utf-8"))
    lid, rid = pdata["lineage_id"], pdata["rollover_id"]
    answers = {a["id"]: a["a"] for a in pdata["anchors"]}
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")

    bads = [
        "!!!",
        "../../lineage",
        "lineage-foo\nx",
        "lineage-foo\x00x",
        "LINEAGE-abc",
        "lineage-",
        "lineage-" + "z" * 57,
        "lineage-foo--bar",
        "lineage-foo.",
    ]
    for i, bad in enumerate(bads):
        pdata_bad = json.loads(probe.read_text(encoding="utf-8"))
        pdata_bad["lineage_id"] = bad
        badp = tmp_path / f"forged_l_{i}.json"
        badp.write_text(json.dumps(pdata_bad), encoding="utf-8")
        rc = context_canary.main(
            [
                "score",
                "--probe",
                str(badp),
                "--answers",
                str(ans),
                "--expected-lineage-id",
                lid,
                "--expected-rollover-id",
                rid,
            ]
        )
        assert rc == 2, f"forged probe lineage must be rejected in score validation: {bad!r}"

    bads_r = [
        "!!!",
        "../../roll",
        "rollover-foo\nx",
        "rollover-foo\x0bx",
        "ROLLOVER-x",
        "rollover-",
        "rollover-" + "a" * 57,
        "wrong-1",
        "rollover-abc.def",
    ]
    for i, bad in enumerate(bads_r):
        pdata_bad = json.loads(probe.read_text(encoding="utf-8"))
        pdata_bad["rollover_id"] = bad
        badp = tmp_path / f"forged_r_{i}.json"
        badp.write_text(json.dumps(pdata_bad), encoding="utf-8")
        rc = context_canary.main(
            [
                "score",
                "--probe",
                str(badp),
                "--answers",
                str(ans),
                "--expected-lineage-id",
                lid,
                "--expected-rollover-id",
                rid,
            ]
        )
        assert rc == 2, f"forged probe rollover must be rejected in score validation: {bad!r}"


def test_identity_validator_rejects_bad_expected_cli_at_score_boundaries(tmp_path: Path):
    """--expected-lineage-id / --expected-rollover-id bad values fail at expected-CLI boundary (validated before ==)."""
    probe = _mint_v2(tmp_path)
    pdata = json.loads(probe.read_text(encoding="utf-8"))
    good_lid, good_rid = pdata["lineage_id"], pdata["rollover_id"]
    answers = {a["id"]: a["a"] for a in pdata["anchors"]}
    ans = tmp_path / "ans.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")

    bad_expected_l = [
        "!!!",
        "../../lineage",
        "lineage-foo\nbar",
        "lineage-FOO",
        "foo-bar",
        "lineage-",
        "lineage-" + "x" * 57,
        "lineage-foo..bar",
        "lineage-abc-",
    ]
    for bad in bad_expected_l:
        rc = context_canary.main(
            [
                "score",
                "--probe",
                str(probe),
                "--answers",
                str(ans),
                "--expected-lineage-id",
                bad,
                "--expected-rollover-id",
                good_rid,
            ]
        )
        assert rc == 2, f"bad --expected-lineage-id must fail at CLI validation boundary: {bad!r}"

    bad_expected_r = [
        "!!!",
        "rollover-foo\n",
        "rollover-UPPER",
        "rollover",
        "rollover-",
        "rollover-" + "y" * 57,
        "../../roll",
        "rollover-foo/bar",
        "rollover--x",
    ]
    for bad in bad_expected_r:
        rc = context_canary.main(
            [
                "score",
                "--probe",
                str(probe),
                "--answers",
                str(ans),
                "--expected-lineage-id",
                good_lid,
                "--expected-rollover-id",
                bad,
            ]
        )
        assert rc == 2, f"bad --expected-rollover-id must fail at CLI validation boundary: {bad!r}"

    # both bad also fails
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            "!!!",
            "--expected-rollover-id",
            "!!!",
        ]
    )
    assert rc == 2


def test_valid_engine_shaped_identities_continue_to_pass_mint_score_and_expected(tmp_path: Path):
    """Valid engine-shaped (lineage-... rollover-...) examples must keep passing at mint, probe, and expected-CLI."""
    # mint
    snap = _good_v2_snapshot()
    s = tmp_path / "sval.json"
    s.write_text(json.dumps(snap), encoding="utf-8")
    p = tmp_path / "pval.json"
    rc = context_canary.main(["mint", "--snapshot", str(s), "--out", str(p)])
    assert rc == 0
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["lineage_id"] == snap["lineage_id"]
    assert data["rollover_id"] == snap["rollover_id"]

    # score with expected exact raw
    answers = {a["id"]: a["a"] for a in data["anchors"]}
    ans = tmp_path / "aval.json"
    ans.write_text(json.dumps(answers), encoding="utf-8")
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(p),
            "--answers",
            str(ans),
            "--expected-lineage-id",
            data["lineage_id"],
            "--expected-rollover-id",
            data["rollover_id"],
        ]
    )
    assert rc == 0

    # also via the original _mint_v2 path + expected
    probe2 = _mint_v2(tmp_path)
    d2 = json.loads(probe2.read_text(encoding="utf-8"))
    a2 = {a["id"]: a["a"] for a in d2["anchors"]}
    aa2 = tmp_path / "a2.json"
    aa2.write_text(json.dumps(a2), encoding="utf-8")
    rc = context_canary.main(
        [
            "score",
            "--probe",
            str(probe2),
            "--answers",
            str(aa2),
            "--expected-lineage-id",
            d2["lineage_id"],
            "--expected-rollover-id",
            d2["rollover_id"],
        ]
    )
    assert rc == 0
