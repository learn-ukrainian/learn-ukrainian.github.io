"""Pin how ci.yml reacts to each event and how CI Gate decides (#8505).

Safety invariant under test: no event path may make the required "CI Gate"
check green or skipped without every required job running (or, in the merge
queue only, a recorded reuse of a green full run of the same tree).

- ci.yml fires on opened/synchronize/reopened only, never `edited` or
  `labeled`. The negated-closing-reference body guard lives in
  pr-body-guard.yml, the only workflow subscribed to `edited`.
- Exactly one job in any workflow is named "CI Gate". It uses `if: always()`
  and fails when a required job was cancelled or skipped unexpectedly;
  GitHub treats a skipped required job as success.

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
            return _call(text, args, context)
        if text in {"true", "false", "null"}:
            return {"true": True, "false": False, "null": None}[text]
        value: Any = context
        for part in text.split("."):
            value = value.get(part) if isinstance(value, dict) else None
        return value

    result = or_expr()
    assert index == len(tokens), f"trailing tokens in {expression!r}"
    return result


def _call(name: str, args: list[Any], context: dict[str, Any]) -> Any:
    if name == "always":
        return True
    # Step status functions read the job status so far (``job.status``):
    # success until a step fails, cancelled once the run is cancelled.
    status = context.get("job", {}).get("status", "success")
    if name in {"success", "failure", "cancelled"}:
        assert not args, name
        return status == name
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
    assert _evaluate("!cancelled() && success()", ctx) is True
    assert _evaluate("!cancelled()", {"job": {"status": "failure"}}) is True
    assert _evaluate("success()", {"job": {"status": "failure"}}) is False
    assert _evaluate("!cancelled()", {"job": {"status": "cancelled"}}) is False


# --- ci.yml job simulation -------------------------------------------------


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


def _simulate(
    github: dict[str, Any], *, reuse: str = "false", failures: set[str] | None = None
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (job id -> success|skipped, job id -> evaluated check name) for ci.yml.

    Follows GitHub's rule: a job whose `if` has no status function carries an
    implicit success() and is skipped when any `needs` job did not succeed.
    Every job that runs is assumed to succeed; the reuse job outputs `reuse`.
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
                    "outputs": {"reuse": reuse} if need == "reuse" and results[need] == "success" else {},
                }
                for need in needs
            },
        }
        condition = job.get("if")
        explicit_status = condition is not None and _STATUS_FUNCTIONS.search(str(condition))
        if not explicit_status and any(results[need] != "success" for need in needs):
            ran = False
        else:
            ran = True if condition is None else _condition(condition, context)
        results[job_id] = ("failure" if failures and job_id in failures else "success") if ran else "skipped"
        names[job_id] = _interpolate(job.get("name", job_id), context)
    return results, names


def _concurrency_group(github: dict[str, Any]) -> str:
    return _interpolate(_load("ci.yml")["concurrency"]["group"], {"github": github})


def test_ci_triggers_on_code_events_only() -> None:
    # Neither `edited` nor `labeled` may start CI on an unchanged SHA.
    assert _pr_types(_load("ci.yml")) == {"opened", "synchronize", "reopened"}


def test_no_workflow_reruns_ci_on_a_label() -> None:
    assert not (_WORKFLOWS / "full-ci-label.yml").exists()
    for path in _WORKFLOWS.glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "gh run rerun" not in text, path.name
        assert "label-noop" not in text, path.name


@pytest.mark.parametrize("event", sorted(_EVENTS))
def test_every_event_runs_every_job(event: str) -> None:
    results, names = _simulate(_EVENTS[event])
    skipped = {job for job, result in results.items() if result != "success"}
    # The reuse check and the queue commit's metadata scan exist only in the merge queue.
    assert skipped == (set() if event == "merge_group" else {"reuse", "queue-metadata-scan"})
    assert names["ci-gate"] == "CI Gate"


def test_merge_queue_reuse_skips_every_reused_job() -> None:
    results, _ = _simulate(_EVENTS["merge_group"], reuse="true")
    reused = {"secret-scan", "checks", "freeze-durations", "frontend", "dependency-audit", "pytest", "pytest-report"}
    assert {job for job, result in results.items() if result != "success"} == reused
    # The queue commit's message, author and committer are scanned even on reuse.
    assert results["queue-metadata-scan"] == "success"


def test_only_the_history_shard_checks_out_full_history() -> None:
    from scripts.ci.split_tests import HISTORY_SHARD

    pytest_job = _load("ci.yml")["jobs"]["pytest"]
    checkout = next(step for step in pytest_job["steps"] if step.get("uses", "").startswith("actions/checkout@"))
    depths = {
        shard: _interpolate(checkout["with"]["fetch-depth"], {"matrix": {"shard": float(shard)}})
        for shard in pytest_job["strategy"]["matrix"]["shard"]
    }
    # fetch-depth 0 is full history; 1 is a shallow checkout of the tested commit.
    assert depths == {shard: "0" if shard == HISTORY_SHARD else "1" for shard in depths}
    # Shallow shards block network git, so a fetch cannot hide a history need.
    script = next(step["run"] for step in pytest_job["steps"] if step.get("name") == "Run pytest")
    assert f'[ "$SHARD" = {HISTORY_SHARD} ] || export GIT_ALLOW_PROTOCOL=file' in script


def test_pr_runs_share_one_group_per_pr_number() -> None:
    # A push cancels the in-flight run for the previous SHA of the PR.
    groups = {_concurrency_group(_EVENTS[name]) for name in ("opened", "synchronize", "reopened")}
    assert groups == {"CI-pull_request-7"}
    assert _concurrency_group(_EVENTS["merge_group"]).startswith("CI-merge_group-refs/heads/gh-readonly-queue/")


def test_body_guard_lives_in_pr_body_guard() -> None:
    ci_text = (_WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert "lint_pr_closing_references" not in ci_text

    guard = _load("pr-body-guard.yml")
    # The guard runs at push time (opened/synchronize/reopened) and on body edits.
    assert {"opened", "edited", "synchronize", "reopened"} <= _pr_types(guard)
    guard_text = (_WORKFLOWS / "pr-body-guard.yml").read_text(encoding="utf-8")
    assert "lint_pr_closing_references.py --stdin" in guard_text
    assert guard.get("permissions") == {"contents": "read"}


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
    aggregation_steps = [step for step in _ci_gate_job()["steps"] if step.get("name") == "Require every job"]
    assert len(aggregation_steps) == 1
    script = aggregation_steps[0]["run"]
    assert isinstance(script, str)
    return script


def test_ci_gate_needs_every_other_job() -> None:
    jobs = set(_load("ci.yml")["jobs"])
    assert set(_ci_gate_job()["needs"]) == jobs - {"ci-gate"}


def test_ci_gate_runs_after_cancel() -> None:
    # A skipped required check is success on GitHub. The Gate must run after a
    # concurrency cancel (`always()`) and fail in the step.
    condition = str(_ci_gate_job()["if"])
    assert condition == "always()"
    assert _condition(condition, {"github": _EVENTS["synchronize"], "needs": {}}) is True
    assert "required job was cancelled" in _gate_script()


_GREEN = {
    "SECRET_SCAN": "success",
    "CHECKS": "success",
    "FREEZE_DURATIONS": "success",
    "FRONTEND": "success",
    "DEPENDENCY_AUDIT": "success",
    "PYTEST": "success",
    "PYTEST_REPORT": "success",
}


def _run_gate(event: str, **results: str) -> subprocess.CompletedProcess[str]:
    metadata_scan = "success" if event == "merge_group" else "skipped"
    env = {
        "EVENT_NAME": event,
        "REUSE_JOB": "skipped",
        "REUSE": "",
        "REUSED_RUN": "",
        "METADATA_SCAN": metadata_scan,
        **_GREEN,
        **results,
    }
    return subprocess.run(
        ["bash", "-e", "-c", _gate_script()],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": "o/r", **env},
        timeout=30,
    )


def test_gate_passes_a_green_pull_request_run() -> None:
    result = _run_gate("pull_request")
    assert result.returncode == 0, result.stdout
    assert "CI Gate green" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"FREEZE_DURATIONS": "failure"},
        {"PYTEST": "failure"},
        {"PYTEST": "skipped"},
        {"PYTEST_REPORT": "skipped"},
        {"CHECKS": "cancelled"},
        {"SECRET_SCAN": ""},
        {"FRONTEND": "skipped"},
        {"DEPENDENCY_AUDIT": "failure"},
        {"DEPENDENCY_AUDIT": "skipped"},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1"},  # reuse outside the queue
        {"METADATA_SCAN": "success"},  # a queue-only job outside the queue
    ],
)
def test_gate_fails_a_pull_request_run_missing_any_job(overrides: dict[str, str]) -> None:
    result = _run_gate("pull_request", **overrides)
    assert result.returncode != 0, result.stdout


def test_gate_names_a_cancelled_job() -> None:
    result = _run_gate("pull_request", PYTEST="cancelled")
    assert result.returncode != 0
    assert "required job was cancelled: pytest" in result.stdout


_REUSED = {name: "skipped" for name in _GREEN}


def test_gate_accepts_merge_queue_reuse_with_a_run_id() -> None:
    result = _run_gate("merge_group", REUSE_JOB="success", REUSE="true", REUSED_RUN="123", **_REUSED)
    assert result.returncode == 0, result.stdout
    for job in ("secret-scan", "checks", "freeze-durations", "frontend", "dependency-audit", "pytest", "pytest-report"):
        assert f"{job} reused from run 123" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "", **_REUSED},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1", **_REUSED, "PYTEST": "success"},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1", **_REUSED, "CHECKS": "failure"},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1", **_REUSED, "SECRET_SCAN": "cancelled"},
        {"REUSE_JOB": "success", "REUSE": "false", **_REUSED},
        {"REUSE_JOB": "success", "REUSE": "false", "PYTEST": "skipped", "PYTEST_REPORT": "skipped"},
        {"REUSE_JOB": "failure", "REUSE": "", "PYTEST": "success"},
        {"REUSE_JOB": "cancelled", "REUSE": ""},
        {"REUSE_JOB": "skipped"},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1", **_REUSED, "METADATA_SCAN": "skipped"},
        {"REUSE_JOB": "success", "REUSE": "true", "REUSED_RUN": "1", **_REUSED, "METADATA_SCAN": "failure"},
        {"REUSE_JOB": "success", "REUSE": "false", "METADATA_SCAN": "cancelled"},
    ],
)
def test_gate_fails_closed_in_the_merge_queue(overrides: dict[str, str]) -> None:
    result = _run_gate("merge_group", **overrides)
    assert result.returncode != 0, result.stdout


def test_gate_passes_a_full_merge_queue_run() -> None:
    result = _run_gate("merge_group", REUSE_JOB="success", REUSE="false")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("failed_job", ["checks", "freeze-durations"])
def test_pytest_runs_after_lint_or_freeze_failure(failed_job: str) -> None:
    results, _ = _simulate(_EVENTS["workflow_dispatch"], failures={failed_job})
    assert results[failed_job] == "failure"
    assert results["pytest"] == "success"


def test_ci_gate_job_timeout_is_five_minutes() -> None:
    assert _ci_gate_job()["timeout-minutes"] == 5


def test_ci_gate_guard_step_order_and_event_conditions() -> None:
    steps = _ci_gate_job()["steps"]
    step_names = [step.get("name") for step in steps]
    assert "Require every job" in step_names
    assert "Check large files guard" in step_names

    guard_idx = step_names.index("Check large files guard")
    aggregation_idx = step_names.index("Require every job")
    assert guard_idx < aggregation_idx

    # All steps preceding the aggregation step must be guarded for pull_request and merge_group only
    guard_steps = steps[:aggregation_idx]
    assert len(guard_steps) == 3

    for step in guard_steps:
        cond = step.get("if")
        assert cond is not None, f"Step {step.get('name')} missing condition"
        # Test against all defined events
        assert _condition(cond, {"github": _EVENTS["opened"]}) is True
        assert _condition(cond, {"github": _EVENTS["synchronize"]}) is True
        assert _condition(cond, {"github": _EVENTS["reopened"]}) is True
        assert _condition(cond, {"github": _EVENTS["merge_group"]}) is True
        assert _condition(cond, {"github": _EVENTS["schedule"]}) is False
        assert _condition(cond, {"github": _EVENTS["workflow_dispatch"]}) is False

    # Check checkout step configuration and expression bindings
    checkout_step = steps[0]
    assert checkout_step.get("uses", "").startswith("actions/checkout@")
    assert checkout_step["with"]["fetch-depth"] == 0
    assert checkout_step["with"]["persist-credentials"] is False

    pr_ctx = {
        "github": {
            "event_name": "pull_request",
            "event": {"pull_request": {"base": {"sha": "pr_base_sha_abc"}}},
        }
    }
    mg_ctx = {
        "github": {
            "event_name": "merge_group",
            "event": {"merge_group": {"head_sha": "mg_head_sha_def", "base_sha": "mg_base_sha_123"}},
        }
    }

    # Evaluate checkout ref binding
    ref_template = checkout_step["with"]["ref"]
    assert _interpolate(ref_template, pr_ctx) == ""
    assert _interpolate(ref_template, mg_ctx) == "mg_head_sha_def"

    # Evaluate guard base SHA binding
    guard_step = steps[2]
    base_template = guard_step["env"]["BASE_SHA"]
    assert _interpolate(base_template, pr_ctx) == "pr_base_sha_abc"
    assert _interpolate(base_template, mg_ctx) == "mg_base_sha_123"


def test_ci_gate_guard_step_missing_sha_fails() -> None:
    steps = _ci_gate_job()["steps"]
    guard_step = next(s for s in steps if s.get("name") == "Check large files guard")
    script = guard_step["run"]

    # In PR event with missing BASE_SHA:
    res_pr = subprocess.run(
        ["bash", "-e", "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "EVENT_NAME": "pull_request", "BASE_SHA": ""},
        check=False,
        timeout=30,
    )
    assert res_pr.returncode != 0
    assert "Missing base SHA" in (res_pr.stdout + res_pr.stderr)

    # In merge_group event with missing HEAD_SHA:
    res_mg = subprocess.run(
        ["bash", "-e", "-c", script],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "EVENT_NAME": "merge_group",
            "HEAD_SHA": "",
            "BASE_SHA": "some_base",
        },
        check=False,
        timeout=30,
    )
    assert res_mg.returncode != 0
    assert "Missing merge_group head_sha" in (res_mg.stdout + res_mg.stderr)


def test_ci_gate_guard_steps_lack_continue_on_error() -> None:
    steps = _ci_gate_job()["steps"]
    step_names = [step.get("name") for step in steps]
    aggregation_idx = step_names.index("Require every job")
    guard_steps = steps[:aggregation_idx]
    assert len(guard_steps) == 3
    for step in guard_steps:
        assert "continue-on-error" not in step or not step["continue-on-error"], (
            f"Step {step.get('name')!r} must not have continue-on-error"
        )
