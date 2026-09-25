"""Pin the #8505 trigger split: body edits and labels must not start CI.

Safety invariant under test: no event path may make the required "CI Gate"
check green or skipped without the classified tier running.

- ci.yml fires on opened/synchronize/reopened only, never `edited` or
  `labeled`. The negated-closing-reference body guard lives in
  pr-body-guard.yml, the only workflow subscribed to `edited` (S2).
- `full-ci` is read from the API by the Changes job (see
  scripts/ci/test_classify_changes.py), for pull_request and merge_group (S3).
- Exactly one job in any workflow is named "CI Gate". It uses `if: always()`
  and fails when a required dependency was cancelled or skipped unexpectedly
  (S1); GitHub treats a skipped required job as success.

Job conditions, names and the concurrency group are GitHub expressions. The
evaluator below implements the subset ci.yml uses, with GitHub semantics
(case-insensitive string equality, `&&`/`||` return an operand), so the tests
evaluate the real YAML against every event shape instead of grepping it.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.ci.classify_changes import preflight_for

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOWS = _REPO_ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    workflow = yaml.safe_load((_WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), f"{name} did not parse to a mapping"
    return workflow


def _triggers(workflow: dict) -> dict:
    # PyYAML (YAML 1.1) parses the bare ``on:`` key as the boolean True.
    raw = workflow.get("on", workflow.get(True))
    assert isinstance(raw, dict), "workflow has no `on:` mapping"
    return raw


def _pr_types(workflow: dict) -> set[str]:
    pull_request = _triggers(workflow).get("pull_request")
    if pull_request is None:
        return set()
    if isinstance(pull_request, dict):
        return set(pull_request.get("types") or [])
    return {"opened", "synchronize", "reopened"}  # default type set


# --- GitHub Actions expression subset -------------------------------------

_TOKEN = re.compile(
    r"\s*(?:(?P<str>'(?:[^']|'')*')|(?P<op>&&|\|\||==|!=|[!(),])"
    r"|(?P<num>\d+(?:\.\d+)?)|(?P<ident>[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*))"
)
_STATUS_FUNCTIONS = re.compile(r"\b(?:always|success|failure|cancelled)\s*\(")


def _truthy(value: Any) -> bool:
    if isinstance(value, float) and math.isnan(value):
        return False
    return value not in (None, False, 0, "")


def _equal(left: Any, right: Any) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.casefold() == right.casefold()
    return left == right


def _tokens(expression: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    position = 0
    stripped = expression.rstrip()
    while position < len(stripped):
        match = _TOKEN.match(stripped, position)
        assert match and match.end() > position, f"unsupported expression: {expression!r}"
        kind = match.lastgroup
        assert kind is not None
        out.append((kind, match.group(kind)))
        position = match.end()
    return out


def _evaluate(expression: str, context: dict[str, Any]) -> Any:
    tokens = _tokens(expression)
    index = 0

    def peek() -> str | None:
        return tokens[index][1] if index < len(tokens) else None

    def take(expected: str | None = None) -> tuple[str, str]:
        nonlocal index
        token = tokens[index]
        assert expected is None or token[1] == expected, (expected, token, expression)
        index += 1
        return token

    def or_expr() -> Any:
        value = and_expr()
        while peek() == "||":
            take()
            right = and_expr()
            value = value if _truthy(value) else right
        return value

    def and_expr() -> Any:
        value = comparison()
        while peek() == "&&":
            take()
            right = comparison()
            value = right if _truthy(value) else value
        return value

    def comparison() -> Any:
        value = unary()
        if peek() in {"==", "!="}:
            op = take()[1]
            right = unary()
            same = _equal(value, right)
            return same if op == "==" else not same
        return value

    def unary() -> Any:
        if peek() == "!":
            take()
            return not _truthy(unary())
        return primary()

    def primary() -> Any:
        kind, text = take()
        if text == "(":
            value = or_expr()
            take(")")
            return value
        if kind == "str":
            return text[1:-1].replace("''", "'")
        if kind == "num":
            return float(text)
        assert kind == "ident", (kind, text, expression)
        if peek() == "(":
            take("(")
            args: list[Any] = []
            while peek() != ")":
                args.append(or_expr())
                if peek() == ",":
                    take(",")
            take(")")
            return _call(text, args)
        if text in {"true", "false", "null"}:
            return {"true": True, "false": False, "null": None}[text]
        value: Any = context
        for part in text.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value

    result = or_expr()
    assert index == len(tokens), f"trailing tokens in {expression!r}"
    return result


def _call(name: str, args: list[Any]) -> Any:
    if name == "always":
        return True
    if name == "format":
        text = str(args[0])
        for number, arg in enumerate(args[1:]):
            text = text.replace("{" + str(number) + "}", _render(arg))
        return text
    raise AssertionError(f"unsupported function {name}()")


def _render(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _interpolate(template: Any, context: dict[str, Any]) -> str:
    return re.sub(r"\$\{\{(.*?)\}\}", lambda m: _render(_evaluate(m.group(1), context)), str(template))


def _condition(raw: Any, context: dict[str, Any]) -> bool:
    text = str(raw).strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2]
    return _truthy(_evaluate(text, context))


def test_expression_evaluator_follows_github_semantics() -> None:
    ctx = {"github": {"event": {"action": "opened", "label": {"name": "Full-CI"}}}}
    assert _evaluate("github.event.label.name == 'full-ci'", ctx) is True  # case-insensitive
    assert _evaluate("github.event.missing == 'opened'", ctx) is False
    assert _evaluate("github.event.missing != 'opened'", ctx) is True
    assert _evaluate("false && 'x' || ''", ctx) == ""
    assert _evaluate("true && 'x' || ''", ctx) == "x"
    assert _evaluate("!(true && false)", ctx) is True
    assert _interpolate("a-${{ 7 }}-${{ null }}", ctx) == "a-7-"


# --- ci.yml job simulation -------------------------------------------------

_FULL_TIER = {"docs_only": "false", "backend": "true", "frontend": "true", "shards": "[1]", "pytest_mode": "full"}


def _changes_outputs(github: dict[str, Any]) -> dict[str, str]:
    """A full-tier Changes result for this event; preflight comes from the classifier."""
    return {**_FULL_TIER, "preflight": preflight_for(github["event_name"], _FULL_TIER)}


def _github(event_name: str, event: dict[str, Any], ref: str = "refs/pull/7/merge") -> dict[str, Any]:
    return {"workflow": "CI", "event_name": event_name, "event": event, "ref": ref}


def _pr_event(action: str) -> dict[str, Any]:
    return _github(
        "pull_request",
        {"action": action, "pull_request": {"number": 7, "head": {"sha": "a" * 40}, "labels": []}},
    )


_EVENTS = {
    "opened": _pr_event("opened"),
    "synchronize": _pr_event("synchronize"),
    "reopened": _pr_event("reopened"),
    "merge_group": _github(
        "merge_group",
        {"action": "checks_requested", "merge_group": {"head_sha": "b" * 40}},
        ref="refs/heads/gh-readonly-queue/main/pr-7-" + "c" * 40,
    ),
    "schedule": _github("schedule", {"schedule": "30 3 * * *"}, ref="refs/heads/main"),
    "workflow_dispatch": _github("workflow_dispatch", {}, ref="refs/heads/main"),
}


def _simulate(github: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Return (job id -> ran|skipped, job id -> evaluated check name) for ci.yml.

    Follows GitHub's rule: a job whose `if` has no status function carries an
    implicit success() and is skipped when any `needs` job did not succeed.
    Every job that runs is assumed to succeed.
    """
    results: dict[str, str] = {}
    names: dict[str, str] = {}
    for job_id, job in _load("ci.yml")["jobs"].items():
        needs = job.get("needs") or []
        needs = [needs] if isinstance(needs, str) else needs
        context = {
            "github": github,
            "matrix": {},
            "needs": {
                need: {
                    "result": results[need],
                    "outputs": _changes_outputs(github) if need == "changes" and results[need] == "ran" else {},
                }
                for need in needs
            },
        }
        condition = job.get("if")
        explicit_status = condition is not None and _STATUS_FUNCTIONS.search(str(condition))
        if not explicit_status and any(results[need] != "ran" for need in needs):
            ran = False
        else:
            ran = True if condition is None else _condition(condition, context)
        results[job_id] = "ran" if ran else "skipped"
        names[job_id] = _interpolate(job.get("name", job_id), context)
    return results, names


def _concurrency_group(github: dict[str, Any]) -> str:
    return _interpolate(_load("ci.yml")["concurrency"]["group"], {"github": github})


def test_ci_triggers_on_code_events_only() -> None:
    # AC-01: neither `edited` nor `labeled` may start CI on an unchanged SHA.
    assert _pr_types(_load("ci.yml")) == {"opened", "synchronize", "reopened"}


def test_no_workflow_reruns_ci_on_a_label() -> None:
    assert not (_WORKFLOWS / "full-ci-label.yml").exists()
    for path in _WORKFLOWS.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "gh run rerun" not in text, path.name
        assert "label-noop" not in text, path.name


@pytest.mark.parametrize("event", sorted(_EVENTS))
def test_every_event_runs_every_tier_job_and_reports_ci_gate(event: str) -> None:
    results, names = _simulate(_EVENTS[event])
    # Preflight (#8750) runs on pull_request only; every other job runs on every event.
    expected_skips = set() if _EVENTS[event]["event_name"] == "pull_request" else {"preflight"}
    assert {job for job, result in results.items() if result != "ran"} == expected_skips
    assert names["ci-gate"] == "CI Gate"
    assert names["changes"] == "Changes"


def test_pr_runs_share_one_group_per_pr_number() -> None:
    # AC-05: a push cancels the in-flight run for the previous SHA of the PR.
    groups = {_concurrency_group(_EVENTS[name]) for name in ("opened", "synchronize", "reopened")}
    assert groups == {"CI-pull_request-7"}
    assert _concurrency_group(_EVENTS["merge_group"]).startswith(
        "CI-merge_group-refs/heads/gh-readonly-queue/"
    )


def test_body_guard_moved_out_of_ci_into_pr_body_guard() -> None:
    ci_text = (_WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "lint_pr_closing_references" not in ci_text

    guard = _load("pr-body-guard.yml")
    # S2: the guard still runs at push time (opened/synchronize/reopened) and
    # now also on body edits.
    assert {"opened", "edited", "synchronize", "reopened"} <= _pr_types(guard)
    guard_text = (_WORKFLOWS / "pr-body-guard.yml").read_text(encoding="utf-8")
    assert "lint_pr_closing_references.py --stdin" in guard_text
    assert guard.get("permissions") == {"contents": "read"}


def test_changes_job_reads_labels_for_pull_request_and_merge_group() -> None:
    # S3 wiring: classify_changes.py reads PR labels via the API (needs
    # pull-requests: read) and resolves merge-group PRs from the queue ref.
    changes = _load("ci.yml")["jobs"]["changes"]
    assert changes["permissions"]["pull-requests"] == "read"
    env = changes["steps"][-1]["env"]
    assert env["HEAD_REF"] == "${{ github.event.merge_group.head_ref }}"
    assert "github.event.merge_group.base_sha" in env["BASE"]


def test_exactly_one_ci_gate_job_across_workflows() -> None:
    carriers = []
    for path in sorted(_WORKFLOWS.glob("*.yml")):
        for job_id, job in (_load(path.name).get("jobs") or {}).items():
            if "ci gate" in str(job.get("name", "")).casefold():
                carriers.append((path.name, job_id))
    assert carriers == [("ci.yml", "ci-gate")]
    assert _load("ci.yml")["jobs"]["ci-gate"]["name"] == "CI Gate"


def _ci_gate_job() -> dict:
    return _load("ci.yml")["jobs"]["ci-gate"]


def _gate_script() -> str:
    steps = _ci_gate_job()["steps"]
    assert len(steps) == 1
    script = steps[0]["run"]
    assert isinstance(script, str)
    return script


def test_ci_gate_runs_after_cancel() -> None:
    # S1: a skipped required check is success on GitHub. The Gate must run
    # after a concurrency cancel (`always()`) and fail in the step.
    condition = str(_ci_gate_job()["if"])
    assert condition == "always()"
    assert _condition(condition, {"github": _EVENTS["synchronize"], "needs": {}}) is True
    assert "required job was cancelled" in _gate_script()


def _run_gate(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", _gate_script()],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        timeout=30,
    )


_GREEN = {
    "DOCS_ONLY": "false",
    "FRONTEND": "false",
    "BACKEND": "true",
    "PREFLIGHT_SCHEDULED": "true",
    "CHANGES": "success",
    "PREFLIGHT": "success",
    "RUFF": "success",
    "SECRET": "success",
    "PYTEST": "success",
    "CONTRACTS": "success",
    "FRONTEND_JOB": "skipped",
    "TYPESAFE_TRIAGE": "success",
    "PLAN_VALIDATE": "success",
}


def test_ci_gate_passes_a_green_full_tier() -> None:
    result = _run_gate(_GREEN)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "CI Gate green" in result.stdout


def test_ci_gate_fails_when_a_required_job_was_cancelled() -> None:
    result = _run_gate({**_GREEN, "PYTEST": "cancelled"})
    assert result.returncode != 0
    assert "CI Gate green" not in result.stdout


def test_ci_gate_fails_when_a_required_job_was_skipped() -> None:
    result = _run_gate({**_GREEN, "SECRET": "skipped"})
    assert result.returncode != 0
    assert "CI Gate green" not in result.stdout


def test_ci_gate_fails_when_changes_was_cancelled() -> None:
    result = _run_gate({**_GREEN, "CHANGES": "cancelled"})
    assert result.returncode != 0
    assert "CI Gate green" not in result.stdout


def test_ci_gate_allows_a_tier_skip_and_rejects_cancelled_tier_skip() -> None:
    docs = {**_GREEN, "DOCS_ONLY": "true", "RUFF": "skipped", "CONTRACTS": "skipped"}
    assert _run_gate(docs).returncode == 0
    cancelled = _run_gate({**docs, "RUFF": "cancelled"})
    assert cancelled.returncode != 0
    assert "cancelled" in cancelled.stdout


_JOB_RESULTS = ("success", "failure", "cancelled", "skipped")


@pytest.mark.parametrize("result", _JOB_RESULTS)
@pytest.mark.parametrize("scheduled", ["true", "false"])
def test_ci_gate_preflight_rule(scheduled: str, result: str) -> None:
    # #8750: scheduled → only success passes; not scheduled → only skipped.
    gate = _run_gate({**_GREEN, "PREFLIGHT_SCHEDULED": scheduled, "PREFLIGHT": result})
    passes = result == ("success" if scheduled == "true" else "skipped")
    assert (gate.returncode == 0) is passes, gate.stdout + gate.stderr
    assert ("CI Gate green" in gate.stdout) is passes
    if not passes:
        assert "preflight was" in gate.stdout


def test_ci_gate_preflight_wiring() -> None:
    env = _ci_gate_job()["steps"][0]["env"]
    assert env["PREFLIGHT_SCHEDULED"] == "${{ needs.changes.outputs.preflight }}"
    assert env["PREFLIGHT"] == "${{ needs.preflight.result }}"
    assert "preflight" in _ci_gate_job()["needs"]


def test_ci_gate_still_fails_when_changes_fails_without_a_preflight_output() -> None:
    # A failed Changes job emits no outputs; the gate must fail on CHANGES first.
    for changes in ("failure", "cancelled"):
        gate = _run_gate({**_GREEN, "CHANGES": changes, "PREFLIGHT_SCHEDULED": "", "PREFLIGHT": "skipped"})
        assert gate.returncode != 0
        assert "CI Gate green" not in gate.stdout
