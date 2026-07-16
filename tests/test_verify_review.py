"""Tests for strict structured review verification (issue #5284)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.verify_review as verify_review_cli
from scripts.common.git_context import sanitized_git_env
from scripts.review.evidence import (
    CANONICAL_DIFF_ARGS,
    OUTCOME_LINE_MISMATCH,
    OUTCOME_OUT_OF_SCOPE,
    OUTCOME_QUOTE_MISSING,
    OUTCOME_VERIFIED,
    EvidenceError,
    build_target_manifest,
    compute_target_input_fingerprint,
    find_verbatim_match,
    is_safe_repo_relative_path,
    match_at_line,
    normalize_line_endings,
    path_surface_bytes,
    resolve_safe_path,
    split_lines_preserve_content,
)
from scripts.review.review_contract import (
    EXIT_ACTIONABLE,
    EXIT_CLEAN,
    EXIT_INCOMPLETE,
    EXIT_INVALID,
    EXIT_STALE,
    EXIT_UNVERIFIABLE,
    SCHEMA_VERSION,
    AgentIdentity,
    ContractError,
    VerifyContext,
    load_schema,
    parse_reviewer_json,
    sha256_text,
    sort_findings_deterministically,
    validate_reviewer_payload,
    verify_review,
)
from scripts.review.target_resolution import (
    resolve_branch_target,
    resolve_commit_target,
    resolve_local_target,
    resolve_pr_target,
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        env=sanitized_git_env(),
    )


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "trunk")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "app.py").write_text("print('v1')\nvalue = 1\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


def _identity(**overrides: str) -> AgentIdentity:
    base = {
        "model": "test-model",
        "family": "test-family",
        "harness": "test-harness",
        "selection_reason": "fixture",
    }
    base.update(overrides)
    return AgentIdentity(**base)


def _clean_payload() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "correct",
            "explanation": "No issues on the frozen target.",
            "confidence": 0.95,
        },
        "findings": [],
    }


def _finding(
    *,
    fid: str = "F001",
    path: str = "app.py",
    start: int = 2,
    end: int | None = None,
    verbatim: str = "value = 2",
    claim_type: str = "present",
    priority: str = "P1",
    category: str = "bug",
) -> dict:
    return {
        "id": fid,
        "title": f"Title {fid}",
        "body": f"Body for {fid}",
        "priority": priority,
        "confidence": 0.8,
        "category": category,
        "location": {
            "path": path,
            "start_line": start,
            "end_line": end if end is not None else start,
            "claim_type": claim_type,
        },
        "verbatim": verbatim,
        "why_wrong": "It is wrong because the constant is incorrect.",
        "smallest_fix": "Set value = 1 instead.",
        "sources": ["none"],
    }


def _full_envelope_kwargs(repo: Path, target, **overrides):
    """Runner envelope sufficient for clean/actionable closeout."""
    fp = compute_target_input_fingerprint(repo, target)
    intended_behavior = "test intended behavior"

    def clause(surface: str) -> dict:
        return {
            "claim": intended_behavior,
            "target_input_sha256": fp,
            "command": f"prove {surface}",
            "cwd": str(repo),
            "exit_code": 0,
            "observation": f"{surface} observed",
            "evidence_ref": f"test:{surface}",
        }

    base = {
        "issue_ref": "#5284",
        "scope": {"owner_boundary": "scripts/verify_review.py"},
        "author": _identity(model="author-model", family="author-family"),
        "reviewer": _identity(
            model="reviewer-model",
            family="reviewer-family",
            harness="reviewer-harness",
            selection_reason="cross-family-gate",
        ),
        "tests": {"commands": ["pytest"], "passed": True},
        "behavior_proof": {
            "source_aware": {"status": "pass", "clauses": [clause("source-aware")]},
            "source_blind": {
                "status": "pass",
                "clauses": [clause("source-blind")],
                "blind_enforced": False,
            },
        },
        "frozen_intended_behavior": intended_behavior,
        "routing_lineage": {
            "implementation_agent": "test-impl",
            "accountable_advisor": "test-advisor",
        },
        "expected_input_sha256": fp,
        "dispositions": {},
    }
    base.update(overrides)
    return base


def _ctx(
    repo: Path,
    target,
    raw: str,
    **kwargs,
) -> VerifyContext:
    env = _full_envelope_kwargs(repo, target, **kwargs)
    return VerifyContext(
        issue_ref=env["issue_ref"],
        scope=env["scope"],
        author=env["author"],
        reviewer=env["reviewer"],
        target=target,
        repo_root=repo,
        input_sha256=env.get("input_sha256", env["expected_input_sha256"] or ""),
        reviewer_output_sha256=sha256_text(raw),
        expected_head=env.get("expected_head"),
        expected_input_sha256=env.get("expected_input_sha256"),
        tests=env["tests"],
        behavior_proof=env["behavior_proof"],
        frozen_intended_behavior=env["frozen_intended_behavior"],
        dispositions=env["dispositions"],
        routing_lineage=env["routing_lineage"],
    )


def _cli_envelope_args(repo: Path, *, dispositions: dict | None = None) -> list[str]:
    target = resolve_local_target(repo)
    fp = compute_target_input_fingerprint(repo, target)
    intended_behavior = "test intended behavior"
    state_file = repo.parent / "behavior-proof-state.json"

    def clause(surface: str) -> dict:
        return {
            "claim": intended_behavior,
            "target_input_sha256": fp,
            "command": f"prove {surface}",
            "cwd": str(repo),
            "exit_code": 0,
            "observation": f"{surface} observed",
            "evidence_ref": f"test:{surface}",
        }

    state_file.write_text(
        json.dumps(
            {
                "baseline": {
                    "intended_behavior": intended_behavior,
                    "target": asdict(target),
                },
                "behavior_proof": {
                    "source_aware": {"status": "pass", "clauses": [clause("source-aware")]},
                    "source_blind": {
                        "status": "pass",
                        "clauses": [clause("source-blind")],
                        "blind_enforced": False,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    args = [
        "--mode",
        "local",
        "--repo-root",
        str(repo),
        "--expected-input-sha256",
        fp,
        "--issue-ref",
        "#5284",
        "--scope-json",
        json.dumps({"owner_boundary": "app.py"}),
        "--author-model",
        "author-model",
        "--author-family",
        "author-family",
        "--author-harness",
        "author-harness",
        "--author-selection-reason",
        "fixture",
        "--reviewer-model",
        "reviewer-model",
        "--reviewer-family",
        "reviewer-family",
        "--reviewer-harness",
        "reviewer-harness",
        "--reviewer-selection-reason",
        "cross-family-gate",
        "--tests-json",
        json.dumps({"commands": ["pytest"], "passed": True}),
        "--behavior-proof-state-file",
        str(state_file),
        "--routing-lineage-json",
        json.dumps(
            {
                "implementation_agent": "test-impl",
                "accountable_advisor": "test-advisor",
            }
        ),
    ]
    if dispositions is not None:
        args.extend(["--dispositions-json", json.dumps(dispositions)])
    return args


# --- normalization / path safety ---------------------------------------------


def test_line_ending_normalization_only():
    assert normalize_line_endings("a\r\nb\rc") == "a\nb\nc"
    # Whitespace and backticks are preserved for matching.
    left = 'x = "a  b"'
    right = 'x = "a  b"'
    assert find_verbatim_match(left + "\n", right)[0] == 1
    assert find_verbatim_match('x = "a b"\n', 'x = "a  b"')[0] is None
    assert find_verbatim_match("`code`\n", "code")[0] is None


def test_split_lines_preserves_internal_whitespace():
    lines = split_lines_preserve_content("  a  \n\tb\n")
    assert lines == ["  a  ", "\tb"]


def test_unsafe_paths_rejected(tmp_path):
    repo = _init_repo(tmp_path)
    assert not is_safe_repo_relative_path("/etc/passwd")
    assert not is_safe_repo_relative_path("C:\\Windows\\System32")
    assert not is_safe_repo_relative_path("../outside")
    assert not is_safe_repo_relative_path("foo/../bar")
    assert not is_safe_repo_relative_path("")
    assert is_safe_repo_relative_path("app.py")
    with pytest.raises(EvidenceError):
        resolve_safe_path(repo, "../outside")


def test_symlink_escape_rejected(tmp_path):
    repo = _init_repo(tmp_path)
    outside = tmp_path / "secret.txt"
    outside.write_text("secret\n", encoding="utf-8")
    link = repo / "link_escape"
    link.symlink_to(outside)
    with pytest.raises(EvidenceError, match=r"symlink_escape|path_escapes"):
        # resolve_safe_path follows the symlink and must fail closed.
        resolve_safe_path(repo, "link_escape")


# --- schema / parse ----------------------------------------------------------


def test_schema_rejects_unknown_fields_and_bad_enums():
    payload = _clean_payload()
    payload["extra"] = True
    with pytest.raises(ContractError, match="schema_violation"):
        validate_reviewer_payload(payload)

    payload = _clean_payload()
    payload["findings"] = [_finding(priority="P9")]
    with pytest.raises(ContractError, match="schema_violation"):
        validate_reviewer_payload(payload)

    payload = _clean_payload()
    payload["findings"] = [_finding()]
    payload["findings"][0]["confidence"] = 1.5
    with pytest.raises(ContractError, match="schema_violation"):
        validate_reviewer_payload(payload)


def test_legacy_finding_text_fails_closed():
    legacy = "FINDING:\nFILE:LINE: app.py:1\n"
    with pytest.raises(ContractError, match="legacy_FINDING"):
        parse_reviewer_json(legacy)


def test_non_json_chatter_fails_closed():
    with pytest.raises(ContractError, match="non_json"):
        parse_reviewer_json('Here is my review:\n{"schema_version": "x"}\nThanks!')


def test_empty_input_is_incomplete():
    with pytest.raises(ContractError) as exc:
        parse_reviewer_json("   ")
    assert exc.value.exit_code == EXIT_INCOMPLETE


def test_multi_finding_order_is_deterministic():
    findings = [
        _finding(fid="Z", path="b.py", start=2),
        _finding(fid="A", path="a.py", start=5),
        _finding(fid="B", path="a.py", start=1),
    ]
    ordered = sort_findings_deterministically(findings)
    assert [f["id"] for f in ordered] == ["B", "A", "Z"]


# --- target modes ------------------------------------------------------------


def test_local_target_verified_and_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    assert "app.py" in target.changed_paths

    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "value should remain 1.",
            "confidence": 0.9,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {
                    "disposition": "in_scope_blocker",
                    "rationale": "bad constant",
                }
            },
        ),
    )
    assert result.exit_code == EXIT_ACTIONABLE
    assert result.validations[0].outcome == OUTCOME_VERIFIED
    assert result.validations[0].matched_line == 2
    assert result.receipt["target"]["mode"] == "local"
    # input_sha256 is target fingerprint, not reviewer JSON hash
    assert result.receipt["target"]["input_sha256"] == compute_target_input_fingerprint(
        repo, target
    )
    assert result.receipt["reviewer_output_sha256"] == sha256_text(raw)
    assert result.receipt["author"]["family"] == "author-family"
    assert result.receipt["reviewer"]["model"] == "reviewer-model"


def test_local_clean_review_exit_zero(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.exit_code == EXIT_CLEAN
    assert result.final_disposition == "clean"


def test_commit_target_quote_and_line_checks(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "bad value")
    target = resolve_commit_target(repo, "HEAD")

    # verified
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "bad constant",
            "confidence": 0.9,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    ok = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {"disposition": "in_scope_blocker", "rationale": "x"},
            },
        ),
    )
    assert ok.validations[0].outcome == OUTCOME_VERIFIED

    # line_mismatch: quote exists at 2 but claimed 1
    payload["findings"] = [_finding(start=1, verbatim="value = 2")]
    raw = json.dumps(payload)
    mm = verify_review(raw, _ctx(repo, target, raw))
    assert mm.validations[0].outcome == OUTCOME_LINE_MISMATCH
    assert mm.validations[0].matched_line == 2
    assert mm.exit_code == EXIT_UNVERIFIABLE

    # quote_missing
    payload["findings"] = [_finding(start=2, verbatim="value = 999")]
    raw = json.dumps(payload)
    qm = verify_review(raw, _ctx(repo, target, raw))
    assert qm.validations[0].outcome == OUTCOME_QUOTE_MISSING
    assert qm.exit_code == EXIT_UNVERIFIABLE


def test_branch_target(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "branch", "feature")
    _git(repo, "checkout", "-q", "feature")
    (repo / "app.py").write_text("print('v1')\nvalue = 3\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "feature change")
    target = resolve_branch_target(repo, "feature", "trunk")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "value wrong",
            "confidence": 0.7,
        },
        "findings": [_finding(start=2, verbatim="value = 3")],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {"disposition": "follow_up", "rationale": "scope note"},
            },
        ),
    )
    assert result.validations[0].outcome == OUTCOME_VERIFIED
    assert result.receipt["target"]["mode"] == "branch"
    assert result.receipt["target"]["base_sha"]
    assert result.receipt["target"]["head_sha"]


def test_pr_target(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    # Simulate a second commit as PR head.
    (repo / "app.py").write_text("print('v1')\nvalue = 4\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "pr head")
    head2 = _git(repo, "rev-parse", "HEAD").stdout.strip()
    base = _git(repo, "rev-parse", "HEAD^").stdout.strip()

    def fake_gh(args, cwd, timeout=30.0):
        class R:
            returncode = 0
            stdout = json.dumps(
                {
                    "number": 99,
                    "baseRefName": "trunk",
                    "baseRefOid": base,
                    "headRefName": "feature",
                    "headRefOid": head2,
                }
            )
            stderr = ""

        return R()

    monkeypatch.setattr(
        "scripts.review.target_resolution._run_gh",
        fake_gh,
    )
    target = resolve_pr_target(repo, 99)
    assert target.mode == "pr"
    assert target.head_sha == head2
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "pr defect",
            "confidence": 0.8,
        },
        "findings": [_finding(start=2, verbatim="value = 4")],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {"disposition": "in_scope_blocker", "rationale": "pr"},
            },
        ),
    )
    assert result.validations[0].outcome == OUTCOME_VERIFIED
    assert result.receipt["target"]["mode"] == "pr"
    # unused var guard
    assert head


# --- scope / stale / adversarial ---------------------------------------------


def test_unknown_changed_path_is_out_of_scope(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "x",
            "confidence": 0.5,
        },
        "findings": [
            _finding(path="other.py", start=1, verbatim="nope"),
        ],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.validations[0].outcome == OUTCOME_OUT_OF_SCOPE
    assert result.exit_code == EXIT_UNVERIFIABLE


def test_unchanged_line_out_of_scope_for_present_claim(tmp_path):
    repo = _init_repo(tmp_path)
    # Change only line 2; claim present defect on line 1 (unchanged content).
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "x",
            "confidence": 0.5,
        },
        "findings": [
            _finding(start=1, verbatim="print('v1')"),
        ],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.validations[0].outcome == OUTCOME_OUT_OF_SCOPE


def test_missing_claim_allows_contextual_evidence_without_changed_line(tmp_path):
    """Missing-code claims need path-in-scope + verbatim context, not a fake diff line."""
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    # Contextual evidence on an unchanged line is OK for claim_type=missing.
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "guard missing after print",
            "confidence": 0.6,
        },
        "findings": [
            _finding(
                start=1,
                verbatim="print('v1')",
                claim_type="missing",
            )
        ],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {"disposition": "follow_up", "rationale": "context ok"},
            },
        ),
    )
    assert result.validations[0].outcome == OUTCOME_VERIFIED


def test_stale_head_fails_closed(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    _git(repo, "commit", "-aq", "-m", "v2")
    target = resolve_commit_target(repo, "HEAD")
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, expected_head="0" * 40),
    )
    assert result.exit_code == EXIT_STALE
    assert "stale_head" in (result.error or "")


def test_stale_input_hash_fails_closed(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, expected_input_sha256="deadbeef" * 8),
    )
    assert result.exit_code == EXIT_STALE
    assert "stale_input_hash" in (result.error or "")


def test_absolute_path_in_finding_fails_schema():
    payload = _clean_payload()
    f = _finding(path="/tmp/evil.py")
    payload["findings"] = [f]
    with pytest.raises(ContractError, match="schema_violation"):
        validate_reviewer_payload(payload)


def test_dotdot_path_in_finding_fails_schema():
    payload = _clean_payload()
    f = _finding(path="../secrets.py")
    payload["findings"] = [f]
    with pytest.raises(ContractError, match="schema_violation"):
        validate_reviewer_payload(payload)


def test_multi_finding_all_preserved_and_ordered(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\nextra = 3\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "two issues",
            "confidence": 0.8,
        },
        "findings": [
            _finding(fid="F2", start=3, verbatim="extra = 3"),
            _finding(fid="F1", start=2, verbatim="value = 2"),
        ],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F1": {"disposition": "in_scope_blocker", "rationale": "a"},
                "F2": {"disposition": "follow_up", "rationale": "b"},
            },
        ),
    )
    assert [v.id for v in result.validations] == ["F1", "F2"]
    assert all(v.outcome == OUTCOME_VERIFIED for v in result.validations)
    assert result.exit_code == EXIT_ACTIONABLE


def test_uncertain_without_findings_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('x')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "uncertain",
            "explanation": "Could not finish review.",
            "confidence": 0.2,
        },
        "findings": [],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.exit_code == EXIT_INCOMPLETE


def test_invalid_schema_exit(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('x')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps({"schema_version": "nope", "overall": {}, "findings": []})
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.exit_code == EXIT_INVALID


def test_receipt_includes_required_envelope_fields(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(raw, _ctx(repo, target, raw))
    r = result.receipt
    assert r["schema_version"] == "code-review-receipt.v1"
    assert r["issue_ref"] == "#5284"
    assert "scope" in r
    assert r["author"]["model"]
    assert r["reviewer"]["selection_reason"]
    assert r["target"]["changed_paths"]
    assert r["target"]["input_sha256"] == compute_target_input_fingerprint(repo, target)
    assert r["reviewer_output_sha256"] == sha256_text(raw)
    assert r["tests"]["passed"] is True
    assert "source_aware" in r["behavior_proof"]
    assert "source_blind" in r["behavior_proof"]
    assert r["routing_lineage"]["accountable_advisor"] == "test-advisor"
    assert r["final_disposition"] == "clean"


# --- fingerprint / location / envelope (review cycle 1) ----------------------


def test_target_fingerprint_changes_after_local_mutation(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target1 = resolve_local_target(repo)
    fp1 = compute_target_input_fingerprint(repo, target1)
    (repo / "app.py").write_text("print('v1')\nvalue = 3\n", encoding="utf-8")
    target2 = resolve_local_target(repo)
    fp2 = compute_target_input_fingerprint(repo, target2)
    assert fp1 != fp2
    assert len(fp1) == 64


def test_missing_expected_fingerprint_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, expected_input_sha256=None),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "expected_input_sha256" in (result.error or "")


def test_missing_lineage_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, routing_lineage={}),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "routing_lineage" in (result.error or "")
    assert result.receipt["routing_lineage"] == {}


def test_placeholder_identity_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            author=_identity(model="unknown", family="unspecified"),
            reviewer=_identity(selection_reason="not_provided"),
        ),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "placeholder" in (result.error or "")


def test_receipt_does_not_fabricate_lineage(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, routing_lineage={}),
    )
    lineage = result.receipt["routing_lineage"]
    assert "grok/5284" not in json.dumps(lineage)
    assert "GPT-5.6" not in json.dumps(lineage)
    assert lineage == {}


def test_duplicate_quote_later_occurrence_verifies(tmp_path):
    repo = _init_repo(tmp_path)
    # Same line text appears twice; claim the later occurrence.
    (repo / "app.py").write_text(
        "flag = True\nshared = 1\nmiddle = 0\nshared = 1\n",
        encoding="utf-8",
    )
    target = resolve_local_target(repo)
    assert match_at_line(
        (repo / "app.py").read_text(encoding="utf-8"), "shared = 1", 4
    )[0]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "later dup",
            "confidence": 0.8,
        },
        "findings": [_finding(start=4, end=4, verbatim="shared = 1")],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {"disposition": "in_scope_blocker", "rationale": "dup"},
            },
        ),
    )
    assert result.validations[0].outcome == OUTCOME_VERIFIED
    assert result.validations[0].matched_line == 4
    assert result.exit_code == EXIT_ACTIONABLE


def test_inflated_range_fails_line_mismatch(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\nextra = 9\n", encoding="utf-8")
    target = resolve_local_target(repo)
    # One-line quote claiming a multi-line inflated range.
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "inflated",
            "confidence": 0.8,
        },
        "findings": [_finding(start=2, end=3, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.validations[0].outcome == OUTCOME_LINE_MISMATCH
    assert "range_span_mismatch" in result.validations[0].detail
    assert result.exit_code == EXIT_UNVERIFIABLE


def test_short_range_fails_line_mismatch(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "short range",
            "confidence": 0.8,
        },
        "findings": [
            _finding(start=1, end=1, verbatim="a = 1\nb = 2"),
        ],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.validations[0].outcome == OUTCOME_LINE_MISMATCH
    assert "range_span_mismatch" in result.validations[0].detail


def test_decode_failure_is_fail_closed_evidence(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)

    def boom(*_a, **_k):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad")

    monkeypatch.setattr("scripts.review.evidence.load_file_text", boom)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "x",
            "confidence": 0.5,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.validations[0].outcome == OUTCOME_QUOTE_MISSING
    assert "decode" in result.validations[0].detail or "read_or_decode" in result.validations[
        0
    ].detail
    assert result.exit_code == EXIT_UNVERIFIABLE


def test_disposition_unknown_id_and_missing_rationale(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "x",
            "confidence": 0.9,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    # Unknown disposition key
    r1 = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "OTHER": {"disposition": "in_scope_blocker", "rationale": "x"},
            },
        ),
    )
    assert r1.exit_code not in (EXIT_CLEAN, EXIT_ACTIONABLE)
    assert "disposition" in (r1.error or "")

    # Missing rationale
    r2 = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={"F001": {"disposition": "in_scope_blocker", "rationale": ""}},
        ),
    )
    assert r2.exit_code == EXIT_INCOMPLETE
    assert "rationale" in (r2.error or "")


# --- CLI ---------------------------------------------------------------------


def test_cli_receipt_path_and_forbidden_paths(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps(_clean_payload()), encoding="utf-8")
    receipt = tmp_path / "out" / "receipt.json"

    code = verify_review_cli.main(
        [
            "--review-file",
            str(review),
            * _cli_envelope_args(repo),
            "--receipt-path",
            str(receipt),
        ]
    )
    assert code == EXIT_CLEAN
    assert receipt.is_file()
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["final_disposition"] == "clean"
    assert data["reviewer_output_sha256"]
    assert data["target"]["input_sha256"] != data["reviewer_output_sha256"]

    forbidden = tmp_path / "data" / "telemetry" / "receipt.json"
    code2 = verify_review_cli.main(
        [
            "--review-file",
            str(review),
            * _cli_envelope_args(repo),
            "--receipt-path",
            str(forbidden),
        ]
    )
    assert code2 == EXIT_INVALID


def test_cli_issue_mode_posts_opt_in_comment(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "bad",
            "confidence": 0.9,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    calls: list[list[str]] = []

    def fake_run(cmd, input_text=None):
        calls.append(cmd)
        if cmd[:3] == ["gh", "issue", "view"]:
            return json.dumps({"comments": [{"body": json.dumps(payload)}]})
        if cmd[:3] == ["gh", "issue", "comment"]:
            return ""
        raise AssertionError(cmd)

    monkeypatch.setattr(verify_review_cli, "_run", fake_run)
    code = verify_review_cli.main(
        [
            "--issue",
            "5284",
            * _cli_envelope_args(
                repo,
                dispositions={
                    "F001": {
                        "disposition": "in_scope_blocker",
                        "rationale": "introduced here",
                    }
                },
            ),
            "--post-comment",
            "--print-findings",
        ]
    )
    assert code == EXIT_ACTIONABLE
    out = capsys.readouterr().out
    assert "verified" in out
    assert calls[-1][:3] == ["gh", "issue", "comment"]


def test_cli_stdin_legacy_text_exit_invalid(tmp_path, monkeypatch, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("x\n", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", type("S", (), {"read": lambda self: "FINDING:\nFILE:LINE: app.py:1\n"})())
    code = verify_review_cli.main(
        ["--from-stdin", "--mode", "local", "--repo-root", str(repo)]
    )
    assert code == EXIT_INVALID


def test_cli_emit_target_manifest_source_blind(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    code = verify_review_cli.main(
        ["--emit-target-manifest", "--mode", "local", "--repo-root", str(repo)]
    )
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["schema_version"] == "code-review-target-manifest.v1"
    assert data["mode"] == "local"
    assert "app.py" in data["changed_paths"]
    assert len(data["input_sha256"]) == 64
    # Mutate and re-emit — fingerprint must change.
    (repo / "app.py").write_text("print('v1')\nvalue = 9\n", encoding="utf-8")
    code2 = verify_review_cli.main(
        ["--emit-target-manifest", "--mode", "local", "--repo-root", str(repo)]
    )
    assert code2 == 0
    data2 = json.loads(capsys.readouterr().out)
    assert data2["input_sha256"] != data["input_sha256"]


def test_cli_missing_lineage_cannot_exit_clean(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps(_clean_payload()), encoding="utf-8")
    target = resolve_local_target(repo)
    fp = compute_target_input_fingerprint(repo, target)
    code = verify_review_cli.main(
        [
            "--review-file",
            str(review),
            "--mode",
            "local",
            "--repo-root",
            str(repo),
            "--expected-input-sha256",
            fp,
            "--issue-ref",
            "#5284",
            "--scope-json",
            json.dumps({"owner": "app.py"}),
            "--author-model",
            "a",
            "--author-family",
            "b",
            "--author-harness",
            "c",
            "--author-selection-reason",
            "d",
            "--reviewer-model",
            "e",
            "--reviewer-family",
            "f",
            "--reviewer-harness",
            "g",
            "--reviewer-selection-reason",
            "h",
            "--tests-json",
            json.dumps({"passed": True}),
            "--behavior-proof-json",
            json.dumps(
                {
                    "source_aware": {"status": "pass"},
                    "source_blind": {"status": "pass"},
                }
            ),
            # deliberately omit --routing-lineage-json
        ]
    )
    assert code == EXIT_INCOMPLETE
    data = json.loads(capsys.readouterr().out)
    assert data["exit_code"] == EXIT_INCOMPLETE
    assert data["final_disposition"] != "clean"


def test_cli_duplicate_later_and_inflated_range(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text(
        "shared = 1\nx = 0\nshared = 1\n",
        encoding="utf-8",
    )
    # Later duplicate verifies via CLI
    payload_ok = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "later",
            "confidence": 0.8,
        },
        "findings": [_finding(start=3, end=3, verbatim="shared = 1")],
    }
    review = tmp_path / "ok.json"
    review.write_text(json.dumps(payload_ok), encoding="utf-8")
    code = verify_review_cli.main(
        [
            "--review-file",
            str(review),
            * _cli_envelope_args(
                repo,
                dispositions={
                    "F001": {"disposition": "in_scope_blocker", "rationale": "later"},
                },
            ),
        ]
    )
    assert code == EXIT_ACTIONABLE
    capsys.readouterr()

    # Inflated range fails
    payload_bad = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "inflated",
            "confidence": 0.8,
        },
        "findings": [_finding(start=3, end=10, verbatim="shared = 1")],
    }
    review2 = tmp_path / "bad.json"
    review2.write_text(json.dumps(payload_bad), encoding="utf-8")
    code2 = verify_review_cli.main(
        [
            "--review-file",
            str(review2),
            * _cli_envelope_args(repo),
        ]
    )
    assert code2 == EXIT_UNVERIFIABLE
    data = json.loads(capsys.readouterr().out)
    assert data["findings"][0]["outcome"] == OUTCOME_LINE_MISMATCH


def test_dispositions_attached_on_receipt(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "overall": {
            "correctness": "incorrect",
            "explanation": "bad",
            "confidence": 0.9,
        },
        "findings": [_finding(start=2, verbatim="value = 2")],
    }
    raw = json.dumps(payload)
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            dispositions={
                "F001": {
                    "disposition": "in_scope_blocker",
                    "rationale": "Introduced by this change.",
                }
            },
        ),
    )
    assert result.validations[0].disposition == "in_scope_blocker"
    assert "Introduced" in (result.validations[0].disposition_rationale or "")
    assert result.exit_code == EXIT_ACTIONABLE


def test_build_target_manifest_matches_fingerprint_helper(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v1')\nvalue = 2\n", encoding="utf-8")
    target = resolve_local_target(repo)
    manifest = build_target_manifest(repo, target)
    assert manifest["input_sha256"] == compute_target_input_fingerprint(repo, target)


# --- closeout gate / fingerprint / invalid CLI (review cycle 2) --------------


def test_failed_tests_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            tests={"commands": ["pytest"], "passed": False},
        ),
    )
    assert result.exit_code == EXIT_ACTIONABLE
    assert result.final_disposition == "actionable"
    assert "tests_failed" in (result.error or "")
    assert result.exit_code != EXIT_CLEAN


def test_failed_behavior_proof_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            behavior_proof={
                "source_aware": {"status": "fail"},
                "source_blind": {"status": "fail"},
            },
        ),
    )
    assert result.exit_code == EXIT_ACTIONABLE
    assert "behavior_proof.source_aware_failed" in (result.error or "")
    assert "behavior_proof.source_blind_failed" in (result.error or "")


def test_bare_passing_behavior_proof_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            behavior_proof={
                "source_aware": {"status": "pass"},
                "source_blind": {"status": "pass", "blind_enforced": False},
            },
        ),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "behavior_proof.source_aware_clauses_missing" in (result.error or "")
    assert "behavior_proof.source_blind_clauses_missing" in (result.error or "")


def test_mismatched_behavior_proof_target_binding_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    proof = _full_envelope_kwargs(repo, target)["behavior_proof"]
    proof["source_aware"]["clauses"][0]["target_input_sha256"] = "wrong-target"
    result = verify_review(raw, _ctx(repo, target, raw, behavior_proof=proof))
    assert result.exit_code == EXIT_INCOMPLETE
    assert "behavior_proof.source_aware_target_binding_mismatch" in (result.error or "")


def test_missing_behavior_proof_target_binding_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    proof = _full_envelope_kwargs(repo, target)["behavior_proof"]
    del proof["source_aware"]["clauses"][0]["target_input_sha256"]
    result = verify_review(raw, _ctx(repo, target, raw, behavior_proof=proof))
    assert result.exit_code == EXIT_INCOMPLETE
    assert "behavior_proof.source_aware_target_binding_mismatch" in (result.error or "")


def test_blind_enforcement_requires_attestation_and_unenforced_is_rendered(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    unenforced = verify_review(raw, _ctx(repo, target, raw))
    assert unenforced.exit_code == EXIT_CLEAN
    assert (
        unenforced.receipt["behavior_proof"]["source_blind"]["blind_enforcement"]
        == "declared-blind/unenforced"
    )

    enforced_proof = _full_envelope_kwargs(repo, target)["behavior_proof"]
    enforced_proof["source_blind"]["blind_enforced"] = True
    enforced = verify_review(raw, _ctx(repo, target, raw, behavior_proof=enforced_proof))
    assert enforced.exit_code == EXIT_INCOMPLETE
    assert "behavior_proof.source_blind_enforced_without_attestation" in (enforced.error or "")


def test_blind_enforcement_uses_optional_target_bound_attestation_validator(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    proof = _full_envelope_kwargs(repo, target)["behavior_proof"]
    proof["source_blind"]["blind_enforced"] = True
    proof["source_blind"]["isolation_attestation"] = {
        "target_input_sha256": compute_target_input_fingerprint(repo, target),
        "attestation_id": "provided-by-5285",
    }
    ctx = _ctx(repo, target, raw, behavior_proof=proof)
    ctx.isolation_attestation_validator = lambda attestation, reviewed_target: (
        attestation["attestation_id"] == "provided-by-5285" and reviewed_target == target
    )
    result = verify_review(raw, ctx)
    assert result.exit_code == EXIT_CLEAN


def test_same_family_lineage_cannot_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            author=_identity(model="author-model", family="OpenAI"),
            reviewer=_identity(
                model="reviewer-model",
                family="openai",
                selection_reason="same-family-advisory",
            ),
        ),
    )
    assert result.exit_code == EXIT_ACTIONABLE
    assert "same_family_review" in (result.error or "")
    assert result.final_disposition != "clean"


def test_justified_na_tests_and_behavior_proof_can_exit_clean(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    behavior_proof = _full_envelope_kwargs(repo, target)["behavior_proof"]
    behavior_proof["source_blind"] = {
        "status": "n/a",
        "reason": "no user-visible surface",
    }
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            tests={
                "status": "n/a",
                "reason": "no automated suite for docs-only surface",
            },
            behavior_proof=behavior_proof,
        ),
    )
    assert result.exit_code == EXIT_CLEAN
    assert result.error is None


def test_missing_behavior_status_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(
            repo,
            target,
            raw,
            behavior_proof={
                "source_aware": {"note": "present without status"},
                "source_blind": {"status": "pass"},
            },
        ),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "behavior_proof.source_aware_status_missing" in (result.error or "")


def test_tests_passed_without_commands_is_incomplete(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    target = resolve_local_target(repo)
    raw = json.dumps(_clean_payload())
    result = verify_review(
        raw,
        _ctx(repo, target, raw, tests={"passed": True}),
    )
    assert result.exit_code == EXIT_INCOMPLETE
    assert "tests_commands_missing" in (result.error or "")


def test_tracked_binary_same_length_mutation_changes_fingerprint(tmp_path):
    repo = _init_repo(tmp_path)
    blob_a = b"\x00\x01\x02\x03AAAA"
    blob_b = b"\x00\x01\x02\x03BBBB"
    assert len(blob_a) == len(blob_b)
    (repo / "asset.bin").write_bytes(blob_a)
    _git(repo, "add", "asset.bin")
    _git(repo, "commit", "-q", "-m", "add binary")
    (repo / "asset.bin").write_bytes(blob_b)
    target = resolve_local_target(repo)
    assert "asset.bin" in target.changed_paths
    surface = path_surface_bytes(repo, target, "asset.bin")
    # Full-index + binary surface carries content identity, not only abbrev.
    assert b"index " in surface
    index_line = next(
        line for line in surface.splitlines() if line.startswith(b"index ")
    )
    # full-index: two 40-char hex object ids separated by ".."
    assert b".." in index_line
    left, right = index_line.split(b" ", 1)[1].split(b" ")[0].split(b"..")
    assert len(left) == 40 and len(right) == 40
    assert all(c in b"0123456789abcdef" for c in left + right)
    fp1 = compute_target_input_fingerprint(repo, target)
    (repo / "asset.bin").write_bytes(blob_a)  # mutate back to committed
    # Same content as HEAD → no change surface for this path; force second
    # same-length mutation different from both prior blobs? Use third blob.
    blob_c = b"\x00\x01\x02\x03CCCC"
    (repo / "asset.bin").write_bytes(blob_c)
    target2 = resolve_local_target(repo)
    fp2 = compute_target_input_fingerprint(repo, target2)
    assert fp1 != fp2
    # Untracked path still hashes raw bytes.
    (repo / "new.bin").write_bytes(blob_a)
    target3 = resolve_local_target(repo)
    assert "new.bin" in target3.changed_paths
    untracked = path_surface_bytes(repo, target3, "new.bin")
    assert untracked == blob_a


def test_fingerprint_not_controlled_by_abbrev_formatting(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "asset.bin").write_bytes(b"\xff\xfeBINARY-DATA-01")
    _git(repo, "add", "asset.bin")
    _git(repo, "commit", "-q", "-m", "bin")
    (repo / "asset.bin").write_bytes(b"\xff\xfeBINARY-DATA-02")
    target = resolve_local_target(repo)
    fp_default = compute_target_input_fingerprint(repo, target)

    # Even if process env requests ultra-short abbrev, canonical flags win.
    calls: list[list[str]] = []
    real_run = subprocess.run

    def tracking_run(cmd, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "git":
            calls.append(list(cmd))
        return real_run(cmd, **kwargs)

    monkeypatch.setattr(subprocess, "run", tracking_run)
    # Local git config that would otherwise shrink index lines.
    _git(repo, "config", "core.abbrev", "4")
    fp_short = compute_target_input_fingerprint(repo, target)
    assert fp_short == fp_default
    # Fingerprint path uses the stable flag set.
    diff_calls = [c for c in calls if "diff" in c]
    assert any(all(flag in c for flag in CANONICAL_DIFF_ARGS) for c in diff_calls)
    surface = path_surface_bytes(repo, target, "asset.bin")
    index_line = next(line for line in surface.splitlines() if line.startswith(b"index "))
    ids = index_line.split(b" ", 1)[1].split(b" ")[0].split(b"..")
    assert all(len(part) == 40 for part in ids)


def test_load_schema_invalid_json_is_contract_error(tmp_path, monkeypatch):
    bad = tmp_path / "schemas"
    bad.mkdir()
    schema_file = bad / "code-review-findings.v1.schema.json"
    schema_file.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.review.review_contract.package_repo_root",
        lambda: tmp_path,
    )
    with pytest.raises(ContractError, match="schema_invalid_json") as exc:
        load_schema()
    assert exc.value.exit_code == EXIT_INVALID


def test_load_schema_unreadable_is_contract_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "scripts.review.review_contract.package_repo_root",
        lambda: tmp_path / "missing-root",
    )
    with pytest.raises(ContractError, match="schema_unavailable") as exc:
        load_schema()
    assert exc.value.exit_code == EXIT_INVALID


def test_invalid_meta_schema_is_contract_error():
    with pytest.raises(ContractError, match="schema_meta_invalid") as exc:
        validate_reviewer_payload(_clean_payload(), schema={"type": "not-a-type"})
    assert exc.value.exit_code == EXIT_INVALID


def test_cli_malformed_envelope_json_exits_invalid(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps(_clean_payload()), encoding="utf-8")
    labels = (
        "--scope-json",
        "--tests-json",
        "--behavior-proof-json",
        "--dispositions-json",
        "--routing-lineage-json",
    )
    for label in labels:
        args = [
            "--review-file",
            str(review),
            "--mode",
            "local",
            "--repo-root",
            str(repo),
            label,
            "{not-json",
        ]
        code = verify_review_cli.main(args)
        assert code == EXIT_INVALID, label
        err = capsys.readouterr().err
        data = json.loads(err)
        assert data["exit_code"] == EXIT_INVALID
        assert data["final_disposition"] == "invalid"
        assert "invalid_json" in data["error"]


def test_cli_failed_proof_and_same_family_non_clean(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps(_clean_payload()), encoding="utf-8")
    target = resolve_local_target(repo)
    fp = compute_target_input_fingerprint(repo, target)
    base = [
        "--review-file",
        str(review),
        "--mode",
        "local",
        "--repo-root",
        str(repo),
        "--expected-input-sha256",
        fp,
        "--issue-ref",
        "#5284",
        "--scope-json",
        json.dumps({"owner": "app.py"}),
        "--author-model",
        "a",
        "--author-family",
        "openai",
        "--author-harness",
        "h",
        "--author-selection-reason",
        "author",
        "--reviewer-model",
        "b",
        "--reviewer-harness",
        "h",
        "--reviewer-selection-reason",
        "review",
        "--routing-lineage-json",
        json.dumps({"implementation_agent": "impl"}),
    ]

    # Failed tests + failed behavior proof
    code = verify_review_cli.main(
        [
            *base,
            "--reviewer-family",
            "xai",
            "--tests-json",
            json.dumps({"commands": ["pytest"], "passed": False}),
            "--behavior-proof-json",
            json.dumps(
                {
                    "source_aware": {"status": "fail"},
                    "source_blind": {"status": "fail"},
                }
            ),
        ]
    )
    assert code == EXIT_ACTIONABLE
    data = json.loads(capsys.readouterr().out)
    assert data["final_disposition"] == "actionable"
    assert data["exit_code"] == EXIT_ACTIONABLE
    assert "tests_failed" in (data.get("error") or "")

    # Same-family with otherwise green proof
    code2 = verify_review_cli.main(
        [
            *base,
            "--reviewer-family",
            "OpenAI",
            "--tests-json",
            json.dumps({"commands": ["pytest"], "passed": True}),
            "--behavior-proof-json",
            json.dumps(
                {
                    "source_aware": {"status": "n/a", "reason": "not exercised"},
                    "source_blind": {"status": "n/a", "reason": "not exercised"},
                }
            ),
        ]
    )
    assert code2 == EXIT_ACTIONABLE
    data2 = json.loads(capsys.readouterr().out)
    assert data2["final_disposition"] == "actionable"
    assert "same_family_review" in (data2.get("error") or "")


def test_cli_subprocess_malformed_scope_exits_2(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "app.py").write_text("print('v2')\n", encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps(_clean_payload()), encoding="utf-8")
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [
            str(root / ".venv" / "bin" / "python"),
            str(root / "scripts" / "verify_review.py"),
            "--review-file",
            str(review),
            "--mode",
            "local",
            "--repo-root",
            str(repo),
            "--scope-json",
            "{not-json",
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env=sanitized_git_env(),
    )
    assert proc.returncode == EXIT_INVALID
    err = json.loads(proc.stderr)
    assert err["exit_code"] == EXIT_INVALID
    assert "invalid_json" in err["error"]
