"""Tests for strict structured review verification (issue #5284)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import scripts.verify_review as verify_review_cli
from scripts.common.git_context import sanitized_git_env
from scripts.review.evidence import (
    OUTCOME_LINE_MISMATCH,
    OUTCOME_OUT_OF_SCOPE,
    OUTCOME_QUOTE_MISSING,
    OUTCOME_VERIFIED,
    EvidenceError,
    find_verbatim_match,
    is_safe_repo_relative_path,
    normalize_line_endings,
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


def _ctx(
    repo: Path,
    target,
    raw: str,
    **kwargs,
) -> VerifyContext:
    return VerifyContext(
        issue_ref=kwargs.get("issue_ref", "#5284"),
        scope=kwargs.get("scope", {"owner_boundary": "scripts/verify_review.py"}),
        author=kwargs.get("author", _identity(model="gpt-5.6-sol", family="openai")),
        reviewer=kwargs.get(
            "reviewer",
            _identity(
                model="grok-4.5",
                family="xai",
                harness="grok-build",
                selection_reason="routing-substitution-cross-family",
            ),
        ),
        target=target,
        repo_root=repo,
        input_sha256=sha256_text(raw),
        expected_head=kwargs.get("expected_head"),
        expected_input_sha256=kwargs.get("expected_input_sha256"),
        tests=kwargs.get("tests", {"commands": ["pytest"], "passed": True}),
        behavior_proof=kwargs.get(
            "behavior_proof",
            {
                "source_aware": {"status": "pass"},
                "source_blind": {"status": "n/a", "reason": "no user-visible surface"},
            },
        ),
        dispositions=kwargs.get("dispositions", {}),
        routing_lineage=kwargs.get(
            "routing_lineage",
            {
                "implementation_agent": "grok/5284-strict-review-receipts",
                "accountable_advisor": "GPT-5.6 Sol",
            },
        ),
    )


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
    result = verify_review(raw, _ctx(repo, target, raw))
    assert result.exit_code == EXIT_ACTIONABLE
    assert result.validations[0].outcome == OUTCOME_VERIFIED
    assert result.validations[0].matched_line == 2
    assert result.receipt["target"]["mode"] == "local"
    assert result.receipt["target"]["input_sha256"] == sha256_text(raw)
    assert result.receipt["author"]["family"] == "openai"
    assert result.receipt["reviewer"]["model"] == "grok-4.5"


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
    ok = verify_review(raw, _ctx(repo, target, raw))
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
    result = verify_review(raw, _ctx(repo, target, raw))
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
    result = verify_review(raw, _ctx(repo, target, raw))
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
    result = verify_review(raw, _ctx(repo, target, raw))
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
    result = verify_review(raw, _ctx(repo, target, raw))
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
    assert r["target"]["input_sha256"]
    assert r["tests"]["passed"] is True
    assert "source_aware" in r["behavior_proof"]
    assert "source_blind" in r["behavior_proof"]
    assert r["routing_lineage"]["accountable_advisor"] == "GPT-5.6 Sol"
    assert r["final_disposition"] == "clean"


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
            "--mode",
            "local",
            "--repo-root",
            str(repo),
            "--receipt-path",
            str(receipt),
            "--issue-ref",
            "#5284",
        ]
    )
    assert code == EXIT_CLEAN
    assert receipt.is_file()
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["final_disposition"] == "clean"

    forbidden = tmp_path / "data" / "telemetry" / "receipt.json"
    code2 = verify_review_cli.main(
        [
            "--review-file",
            str(review),
            "--mode",
            "local",
            "--repo-root",
            str(repo),
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
            "--mode",
            "local",
            "--repo-root",
            str(repo),
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
