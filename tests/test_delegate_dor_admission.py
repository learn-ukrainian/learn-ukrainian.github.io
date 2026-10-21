"""Admission classification at both existing mode guards (#10565)."""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.ci import check_issue_task_quality as checker
from tests.test_check_issue_task_quality import COMPLETE
from tests.test_delegate import (
    _fixture_runtime_tmp_root,  # noqa: F401 -- isolate full-dispatch scratch
    _fixture_worktree_lock_dir,  # noqa: F401 -- isolate full-dispatch locks
    _make_run_stub,
    _review_target_from_fixture_refs,  # noqa: F401 -- fixture remote, no live PRs
    _synthetic_routing_budget,  # noqa: F401 -- no live provider telemetry
    _tmp_dispatch_repo_root,
    _worktree_add_via_run,  # noqa: F401 -- retain the git command stub at provisioning
    delegate,
)

PRIVATE = "learn-ukrainian/learn-ukrainian-infra-private"


def admission(monkeypatch, payload, *, reason=None, repo=None):
    def run(command, **kwargs):
        if command[:2] == ["gh", "api"]:
            return subprocess.CompletedProcess(command, 0, '{"number":123}', "")
        return subprocess.CompletedProcess(command, int(payload["verdict"] != "PASS"), json.dumps(payload), "")

    monkeypatch.setattr(delegate.subprocess, "run", run)
    return delegate._run_dor_preflight("Implement #123", reason, dispatch_repo=repo or delegate._CANONICAL_GITHUB_REPO)


@pytest.mark.parametrize("code", ["dod_structure_malformed", "membership_conflicting_ancestry"])
@pytest.mark.parametrize("reason", [None, "repair reason"])
def test_non_overridable_codes(monkeypatch, code, reason):
    refusal, record = admission(monkeypatch, {"verdict": "WARN", "missing": [code]}, reason=reason)
    assert code in refusal and "no override applies" in refusal
    assert record["warnings"] == {"123": code}


@pytest.mark.parametrize(
    "code",
    [
        "dod_structure_absent",
        "membership_missing_parent",
        "membership_registry_absent",
        "membership_unknown",
        "membership_timeout",
        "membership_rate_limited",
        "checker_error",
    ],
)
def test_overrides_recorded_only_for_overrideable_codes(monkeypatch, code):
    payload = {"verdict": "WARN", "missing": [code]}
    assert admission(monkeypatch, payload)[0]
    refusal, record = admission(monkeypatch, payload, reason="evidence gap accepted")
    assert refusal is None
    assert record["allow_warn_reason"] == "evidence gap accepted"
    assert record["issues"] == [123] and record["warnings"] == {"123": code}


def test_old_shape_meaning_preserved_without_membership_proof(monkeypatch):
    refusal, record = admission(monkeypatch, {"verdict": "PASS", "missing": []})
    assert refusal is None
    assert record == {"issues": [123], "warnings": {}, "dor": "PASS"}
    assert record.get("membership", {}).get("123", {}).get("status") != "PASS"


def test_private_complete_card_admits_cursor_and_preserves_router_keys(monkeypatch):
    from scripts.api import delegate_router

    # Held-out complete private card: real checker and fleet registry decision.
    membership = checker.observe_membership({"body": COMPLETE}, PRIVATE, 123)
    assert membership["status"] == "membership_not_applicable"
    payload = checker.evaluate_issue({"body": COMPLETE}, membership)
    refusal, record = admission(monkeypatch, payload, repo=PRIVATE)
    assert refusal is None
    assert record["issues"] == [123] and record["warnings"] == {}
    assert record["membership"][f"{PRIVATE}#123"]["status"] == "membership_not_applicable"
    assert record["issue_repositories"] == [{"issue": 123, "repo": PRIVATE}]
    assert delegate_router._linked_issues_from_dor({"dor_preflight": record}) == [{"issue": 123, "repository": PRIVATE}]
    args = argparse.Namespace(
        mode="danger",
        research_role="implementation",
        research_task_family=None,
        owned_path=["scripts/example.py"],
        review=False,
        review_attempt=None,
        require_review_verdict=False,
        review_profile=None,
    )
    assert delegate._cursor_auto_refusal(args, agent="cursor", model="auto", dor_record=record) is None
    record["allow_warn_reason"] = "override"
    assert "not PASS" in delegate._cursor_auto_refusal(args, agent="cursor", model="auto", dor_record=record)


@pytest.mark.parametrize("mode,expected", [("read-only", 0), ("workspace-write", 1), ("danger", 1)])
@pytest.mark.parametrize("callsite", [0, 1])
def test_both_actual_dispatch_mode_guards(mode, expected, callsite):
    # Execute the actual dispatch guard statement in isolation, so all three
    # modes reach the production conditional without launching a worker.
    tree = ast.parse(textwrap.dedent(inspect.getsource(delegate._dispatch)))
    guards = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and any(
            isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == "_run_dor_preflight"
            for sub in ast.walk(ast.Module(body=node.body, type_ignores=[]))
        )
    ]
    assert len(guards) == 2
    calls = []

    def preflight(*a, **k):
        calls.append(a)
        return None, {"issues": [123], "warnings": {}}

    namespace = {
        "args": argparse.Namespace(mode=mode),
        "early_prompt": "early #123",
        "prompt": "stdin #123",
        "dor_reason": None,
        "fleet_repo": argparse.Namespace(github=PRIVATE),
        "_run_dor_preflight": preflight,
    }
    node = ast.fix_missing_locations(
        ast.FunctionDef(
            name="guard",
            args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[guards[callsite]],
            decorator_list=[],
        )
    )
    exec(
        compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), "dispatch-mode-guard", "exec"),
        namespace,
    )
    namespace["guard"]()
    assert len(calls) == expected


@pytest.mark.parametrize("reason", [None, "override"])
def test_membership_timeout_never_downgrades_malformed_dod(monkeypatch, capsys, reason):
    """Reviewer timeout probe through the real checker main and delegate mapping."""
    import signal

    malformed = COMPLETE + "\n- [ ] AC-01: duplicate"
    monkeypatch.setattr(checker, "fetch_issue", lambda *a: {"body": malformed, "title": "target", "labels": []})
    budget = checker.time_budget
    monkeypatch.setattr(checker, "time_budget", lambda: budget(0.01))
    monkeypatch.setattr(checker, "observe_membership", lambda *a: signal.pause())
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["missing"] == ["dod_structure_malformed", "membership_timeout"]
    assert payload["dod"]["status"] == "WARN"
    refusal, record = admission(monkeypatch, payload, reason=reason)
    assert "dod_structure_malformed" in refusal
    assert "no override applies" in refusal
    assert record["warnings"] == {"123": "dod_structure_malformed,membership_timeout"}


def test_delegate_uses_checker_non_overridable_set(monkeypatch):
    monkeypatch.setattr(checker, "NON_OVERRIDABLE", checker.NON_OVERRIDABLE | {"future_structure_defect"})
    refusal, _ = admission(monkeypatch, {"verdict": "WARN", "missing": ["future_structure_defect"]}, reason="override")
    assert "future_structure_defect" in refusal and "no override applies" in refusal


def test_trivial_malformed_dod_remains_advisory_in_delegate(monkeypatch):
    payload = checker.evaluate_issue({"body": "trivial: yes\n" + COMPLETE + "\n- [ ] AC-01: duplicate"}, checker.section("PASS"))
    refusal, record = admission(monkeypatch, payload)
    assert payload["dod"]["errors"][0]["code"] == "dod_structure_malformed"
    assert refusal is None
    assert record["warnings"] == {}


def test_delegate_allows_both_checker_read_budgets(monkeypatch):
    timeouts = []

    def run(command, **kwargs):
        if command[:2] == ["gh", "api"]:
            return subprocess.CompletedProcess(command, 0, '{"number":123}', "")
        timeouts.append(kwargs["timeout"])
        return subprocess.CompletedProcess(command, 0, '{"verdict":"PASS","missing":[]}', "")

    monkeypatch.setattr(delegate.subprocess, "run", run)
    refusal, _ = delegate._run_dor_preflight("Implement #123", None, dispatch_repo=delegate._CANONICAL_GITHUB_REPO)
    assert refusal is None
    assert timeouts == [135]


# #11283 (R6): one row per DoR check outcome with its dispatch decision. A
# membership timeout on a complete card is an UNKNOWN advisory and needs no
# --allow-dor-warn; the hard tier and tool errors keep their existing refusals.
NO_OUTCOME = COMPLETE.replace("## User-visible outcome\nShip the advisory checker.\n", "")
NO_CRITERIA = COMPLETE.split("## Acceptance Criteria")[0]
TIMEOUT = checker.membership_error("membership_timeout_live_audit_root_1_of_3_issue_123")


@pytest.mark.parametrize(
    "body,membership,refused,dor",
    [
        pytest.param(COMPLETE, checker.section("PASS"), False, "PASS", id="pass"),
        pytest.param(NO_OUTCOME, checker.section("PASS"), True, "WARN", id="hard-tier-fail"),
        pytest.param(NO_OUTCOME, TIMEOUT, True, "WARN", id="hard-tier-fail-with-timeout"),
        pytest.param(NO_CRITERIA, TIMEOUT, True, "WARN", id="no-criteria-with-timeout"),
        pytest.param(COMPLETE, checker.membership_error("membership_missing_parent"), True, "WARN", id="content-warn"),
        pytest.param(COMPLETE, TIMEOUT, False, "UNKNOWN (timeout)", id="timeout"),
    ],
)
def test_dor_outcome_dispatch_decision(monkeypatch, capsys, body, membership, refused, dor):
    refusal, record = admission(monkeypatch, checker.evaluate_issue({"body": body}, membership))
    assert bool(refusal) is refused
    if refused:
        assert "--allow-dor-warn" in refusal
    assert record["dor"] == dor
    assert "allow_warn_reason" not in record
    if dor == "UNKNOWN (timeout)":
        assert record["warnings"] == {}
        assert record["unknown"] == {"123": TIMEOUT["errors"][0]["code"]}
        assert "UNKNOWN (timeout)" in capsys.readouterr().err


def _tool_error_admission(monkeypatch, failure):
    def run(command, **kwargs):
        if command[:2] == ["gh", "api"]:
            if failure == "no-issue":
                return subprocess.CompletedProcess(command, 1, "", "Not Found")
            return subprocess.CompletedProcess(command, 0, '{"number":123}', "")
        if failure == "checker-subprocess-timeout":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        if failure == "target-fetch-timeout":
            payload = {
                "verdict": "WARN",
                "missing": ["input", "checker_error", "membership_timeout_target_fetch"],
                "dor": checker.section("unchecked"),
                "dod": checker.section("unchecked"),
                "membership": checker.section("unchecked"),
            }
            return subprocess.CompletedProcess(command, 1, json.dumps(payload), "")
        if failure == "checker-abnormal-exit":
            # A timeout-only payload is UNKNOWN only under the strict WARN exit (1).
            payload = checker.evaluate_issue({"body": COMPLETE}, TIMEOUT)
            return subprocess.CompletedProcess(command, -9, json.dumps(payload), "")
        return subprocess.CompletedProcess(command, 1, "Traceback (most recent call last):", "")

    monkeypatch.setattr(delegate.subprocess, "run", run)
    return delegate._run_dor_preflight("Implement #123", None, dispatch_repo=delegate._CANONICAL_GITHUB_REPO)


@pytest.mark.parametrize(
    "failure",
    ["no-issue", "checker-crash", "checker-subprocess-timeout", "target-fetch-timeout", "checker-abnormal-exit"],
)
def test_tool_error_still_requires_override(monkeypatch, failure):
    refusal, record = _tool_error_admission(monkeypatch, failure)
    assert "--allow-dor-warn" in refusal
    assert record["dor"] == "WARN"
    if failure != "checker-abnormal-exit":
        assert "checker_error" in record["warnings"]["123"]
    assert "unknown" not in record


def test_real_checker_membership_timeout_admits_without_override(monkeypatch, capsys):
    """The real checker main, timing out in membership, read through the real delegate mapping."""
    import signal

    monkeypatch.setattr(checker, "fetch_issue", lambda *a: {"body": COMPLETE, "title": "target", "labels": []})
    budget = checker.time_budget
    monkeypatch.setattr(checker, "time_budget", lambda: budget(0.01))
    monkeypatch.setattr(checker, "observe_membership", lambda *a: signal.pause())
    assert checker.main(["--issue", "123", "--strict", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "WARN" and payload["missing"] == ["membership_timeout"]
    refusal, record = admission(monkeypatch, payload)
    assert refusal is None
    assert record == {
        "issues": [123],
        "warnings": {},
        "unknown": {"123": "membership_timeout"},
        "dor": "UNKNOWN (timeout)",
        "membership": {"123": payload["membership"]},
    }


def test_unknown_dor_is_not_pass_for_cursor_auto(monkeypatch):
    _refusal, record = admission(monkeypatch, checker.evaluate_issue({"body": COMPLETE}, TIMEOUT))
    args = argparse.Namespace(
        mode="danger",
        research_role="implementation",
        research_task_family=None,
        owned_path=["scripts/example.py"],
        review=False,
        review_attempt=None,
        require_review_verdict=False,
        review_profile=None,
    )
    assert "not PASS" in delegate._cursor_auto_refusal(args, agent="cursor", model="auto", dor_record=record)


def test_unknown_with_overridden_warning_records_warn(monkeypatch):
    def run(command, **kwargs):
        if command[:2] == ["gh", "api"]:
            number = int(command[2].rsplit("/", 1)[1])
            return subprocess.CompletedProcess(command, 0, json.dumps({"number": number}), "")
        number = int(command[command.index("--issue") + 1])
        membership = TIMEOUT if number == 1 else checker.membership_error("membership_missing_parent")
        return subprocess.CompletedProcess(
            command, 1, json.dumps(checker.evaluate_issue({"body": COMPLETE}, membership)), ""
        )

    monkeypatch.setattr(delegate.subprocess, "run", run)
    canonical = delegate._CANONICAL_GITHUB_REPO
    refusal, record = delegate._run_dor_preflight("Implement #1 and #2", None, dispatch_repo=canonical)
    assert "#2: membership_missing_parent" in refusal and "#1" not in refusal
    refusal, record = delegate._run_dor_preflight("Implement #1 and #2", "accepted", dispatch_repo=canonical)
    assert refusal is None
    assert record["dor"] == "WARN"
    assert record["unknown"] == {"1": TIMEOUT["errors"][0]["code"]}
    assert record["warnings"] == {"2": "membership_missing_parent"}


# #11283 review F1: partial or contradictory timeout evidence keeps the
# existing overridable WARN refusal, and an explicit non-PASS ``dor`` is never
# Cursor Auto evidence, with or without the auxiliary ``unknown`` map.
def _complete_timeout(**overrides):
    payload = checker.evaluate_issue({"body": COMPLETE}, checker.membership_error("membership_timeout"))
    payload.update(overrides)
    return payload


PARTIAL_TIMEOUT_EVIDENCE = [
    pytest.param(
        {"verdict": "WARN", "missing": ["membership_timeout"], "dor": {"status": "PASS"}}, id="review-reproducer-a"
    ),
    pytest.param(
        _complete_timeout(
            dod=checker.section(
                "WARN", [checker.error("dod", "acceptance_criteria", "dod_structure_malformed", "malformed")]
            )
        ),
        id="dod-error-omitted-from-top-level",
    ),
    pytest.param(
        _complete_timeout(membership=checker.membership_error("membership_audit_stale")), id="membership-section-stale"
    ),
    pytest.param(
        checker.evaluate_issue(
            {"body": COMPLETE}, checker.membership_error("membership_timeout_target_fetch_extra")
        ),
        id="forged-target-fetch-prefix",
    ),
]


@pytest.mark.parametrize("payload", PARTIAL_TIMEOUT_EVIDENCE)
def test_partial_timeout_evidence_keeps_warn_refusal(monkeypatch, capsys, payload):
    """Defect class: an incomplete or contradictory checker result admitted as UNKNOWN."""
    refusal, record = admission(monkeypatch, payload)
    assert "--allow-dor-warn" in refusal
    assert record["dor"] == "WARN"
    assert record["warnings"] == {"123": ",".join(payload["missing"])}
    assert "unknown" not in record
    assert "UNKNOWN" not in capsys.readouterr().err
    # The real override still admits exactly as before, with its reason recorded.
    refusal, record = admission(monkeypatch, payload, reason="membership evidence gap accepted")
    assert refusal is None
    assert record["dor"] == "WARN" and record["allow_warn_reason"] == "membership evidence gap accepted"


def _cursor_auto_args():
    return argparse.Namespace(
        mode="danger",
        research_role="implementation",
        research_task_family=None,
        owned_path=["scripts/example.py"],
        review=False,
        review_attempt=None,
        require_review_verdict=False,
        review_profile=None,
    )


@pytest.mark.parametrize(
    "record",
    [
        pytest.param({"issues": [123], "warnings": {}, "dor": "UNKNOWN (timeout)"}, id="review-reproducer-b"),
        pytest.param({"issues": [123], "dor": "UNKNOWN (timeout)"}, id="unknown-without-any-map"),
        pytest.param(
            {"issues": [123], "warnings": {}, "unknown": {"123": "membership_timeout"}}, id="unknown-map-without-dor"
        ),
        pytest.param({"issues": [123], "warnings": {}, "dor": "WARN"}, id="warn-without-warnings"),
        pytest.param({"issues": [123], "warnings": {}, "dor": None}, id="explicit-null"),
        pytest.param({"issues": [123], "warnings": {}, "dor": "pass"}, id="case-variant"),
    ],
)
def test_explicit_non_pass_dor_is_not_cursor_auto_evidence(record):
    """Defect class: a consumer reading only auxiliary maps and missing an explicit non-PASS state."""
    refusal = delegate._cursor_auto_refusal(_cursor_auto_args(), agent="cursor", model="auto", dor_record=record)
    assert refusal is not None and "not PASS" in refusal


@pytest.mark.parametrize(
    "record",
    [
        pytest.param({"issues": [123], "warnings": {}}, id="legacy-without-dor"),
        pytest.param({"issues": [123], "warnings": {}, "dor": "PASS"}, id="explicit-pass"),
    ],
)
def test_pass_dor_records_remain_cursor_auto_evidence(record):
    """Defect class: a new refusal for formerly valid PASS records (OO-53)."""
    assert delegate._cursor_auto_refusal(_cursor_auto_args(), agent="cursor", model="auto", dor_record=record) is None


@pytest.mark.usefixtures(
    "_fixture_runtime_tmp_root",
    "_fixture_worktree_lock_dir",
    "_review_target_from_fixture_refs",
    "_synthetic_routing_budget",
    "_worktree_add_via_run",
)
@pytest.mark.parametrize(
    "agent,final_status,changed,override,guard_disabled",
    [
        pytest.param("cursor", "UNKNOWN (timeout)", True, False, False, id="late-timeout"),
        pytest.param("cursor", "WARN", True, False, False, id="late-warn"),
        pytest.param("cursor", "non-overridable", True, False, False, id="late-hard-failure"),
        pytest.param("cursor", "PASS", True, False, False, id="late-pass"),
        pytest.param("cursor", "PASS", False, False, False, id="unchanged-pass"),
        pytest.param("cursor", "WARN", True, True, False, id="override-refuses-before-late-warn"),
        pytest.param("cursor", "PASS", False, True, False, id="override-refuses-clean-pass"),
        pytest.param("codex", "UNKNOWN (timeout)", True, False, False, id="non-cursor-late-timeout"),
        pytest.param("cursor", "UNKNOWN (timeout)", True, False, True, id="flag-stays-false-if-guard-regresses"),
    ],
)
def test_full_dispatch_cursor_auto_uses_final_dor(
    monkeypatch, tmp_path, capsys, agent, final_status, changed, override, guard_disabled
):
    """Defect classes: stale PASS admission, misleading timeout advice, and a false PASS flag."""
    _tmp_dispatch_repo_root(tmp_path, monkeypatch)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setenv("LU_ALLOW_NOTEBOOK_DISPATCH", "1")
    monkeypatch.setattr(delegate, "project_interpreter", lambda: Path(sys.executable))
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("Implement #123", encoding="utf-8")
    calls, git_run = _make_run_stub(rev_parse_head_sha="a" * 40)
    checked_issues = []

    def run(command, **kwargs):
        if command[:2] == ["gh", "api"]:
            number = int(command[-1].rsplit("/", 1)[-1])
            return subprocess.CompletedProcess(command, 0, json.dumps({"number": number}), "")
        if "--issue" in command:
            issue = int(command[command.index("--issue") + 1])
            checked_issues.append(issue)
            status = final_status if issue == 124 else "PASS"
            membership = {
                "UNKNOWN (timeout)": TIMEOUT,
                "WARN": checker.membership_error("membership_missing_parent"),
            }.get(status, checker.section("PASS"))
            body = COMPLETE + "\n- [ ] AC-01: duplicate" if status == "non-overridable" else COMPLETE
            payload = checker.evaluate_issue({"body": body}, membership)
            # Deterministic prompt drift between the early read and launch read.
            if changed:
                prompt_file.write_text("Implement #124", encoding="utf-8")
            return subprocess.CompletedProcess(command, int(payload["verdict"] != "PASS"), json.dumps(payload), "")
        return git_run(command, **kwargs)

    monkeypatch.setattr(delegate.subprocess, "run", run)
    spawn = MagicMock(return_value=MagicMock(pid=24681))
    monkeypatch.setattr(delegate.subprocess, "Popen", spawn)
    write_state = MagicMock(wraps=delegate._write_state_atomic)
    monkeypatch.setattr(delegate, "_write_state_atomic", write_state)
    if guard_disabled:
        # Fault injection proves that the stored flag itself cannot certify UNKNOWN.
        monkeypatch.setattr(delegate, "_cursor_auto_refusal", lambda *a, **k: None)
    options = ["--model", "auto"] if agent == "cursor" else []
    if override:
        options += ["--allow-dor-warn", "accepted evidence gap"]
    args = delegate.build_parser().parse_args(
        [
            "dispatch", "--agent", agent, *options, "--mode", "danger",
            "--task-id", "final-dor", "--prompt-file", str(prompt_file),
            "--research-role", "implementation", "--owned-path", "scripts/example.py",
            "--worktree", str(tmp_path / ".worktrees" / "dispatch" / agent / "final-dor"),
        ]
    )
    result = delegate.cmd_dispatch(args)
    state = delegate._read_state(delegate._state_path("final-dor"))
    assert checked_issues == ([123, 124] if changed and not override else [123])
    admitted = not override and (agent != "cursor" or final_status == "PASS" or guard_disabled)
    if admitted:
        assert result == 0
        assert spawn.call_count == 1
        assert state["dor_preflight"]["dor"] == final_status
        assert "allow_warn_reason" not in state["dor_preflight"]
        if agent == "cursor":
            assert state["cursor_auto_admission"] == {
                "admitted": final_status == "PASS", "model": "auto", "issues": [124 if changed else 123]
            }
        else:
            assert "cursor_auto_admission" not in state
    else:
        assert result == 2
        spawn.assert_not_called()
        write_state.assert_not_called()
        assert state is None
        assert not any(command[:3] == ["git", "worktree", "add"] for command in calls)
        err = capsys.readouterr().err
        if final_status == "UNKNOWN (timeout)":
            assert "UNKNOWN (timeout)" in err
            assert "advisory only" not in err
        if final_status == "UNKNOWN (timeout)" or override:
            assert "cursor_auto_outside_coding_task" in err
        elif final_status == "non-overridable":
            assert "dod_structure_malformed" in err and "no override applies" in err
        else:
            assert "DoR issue card WARN" in err
