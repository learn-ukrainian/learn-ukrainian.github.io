"""Admission classification at both existing mode guards (#10565)."""

from __future__ import annotations

import argparse
import ast
import inspect
import json
import subprocess
import textwrap

import pytest

from scripts.ci import check_issue_task_quality as checker
from tests.test_check_issue_task_quality import COMPLETE
from tests.test_delegate import delegate

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
    assert record == {"issues": [123], "warnings": {}}
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
