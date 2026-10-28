"""Pin how ci.yml reacts to each event and how CI Gate decides (#8505).

Safety invariant under test: no event path may make the required "CI Gate"
check green or skipped without every job required by the event tier running.

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

import json
import math
import os
import re
import subprocess
import sys
import tempfile
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


@pytest.mark.parametrize(
    "mode,budget", [(None, 5), ("bounded", 5), ("full-history-audit", 60), ("", 5), ("garbage", 5)]
)
@pytest.mark.parametrize("event", ["workflow_dispatch", "pull_request", "merge_group", "push", "schedule"])
def test_secret_scan_audit_budget_cannot_widen_other_events(event: str, mode: str | None, budget: int) -> None:
    """Only an explicit manual audit gets the larger job budget; the scan still runs."""
    workflow = _load("ci.yml")
    dispatch = _triggers(workflow)["workflow_dispatch"]["inputs"]["secret_scan_mode"]
    assert dispatch["type"] == "choice"
    assert dispatch["default"] == "bounded"
    assert dispatch["options"] == ["bounded", "full-history-audit"]
    scan = workflow["jobs"]["secret-scan"]
    context = {
        "github": {"event_name": event, "token": "read-token"},
        "inputs": {} if mode is None else {"secret_scan_mode": mode},
        "needs": {"reuse": {"outputs": {"reuse": "false"}}},
    }
    assert _interpolate(scan["timeout-minutes"], context) == str(budget if event == "workflow_dispatch" else 5)
    assert _condition(scan["if"], context)
    scope = next(step for step in scan["steps"] if step.get("id") == "secret-scan-scope")
    assert _interpolate(scope["env"]["DISPATCH_SCAN_MODE"], context) == (mode or "")
    assert _interpolate(scope["env"]["GH_TOKEN"], context) == ("read-token" if event == "schedule" else "")
    assert "if" not in scope
    scanner = next(
        step for step in scan["steps"] if str(step.get("uses", "")).startswith("trufflesecurity/trufflehog@")
    )
    assert "if" not in scanner
    assert scanner["uses"] == "trufflesecurity/trufflehog@e76dff8a7e57d6df0c60ad8cbf5d5cba505a8fc9"
    assert scanner["with"]["version"] == "3.99.0"

    # Artifact publication is the coverage receipt. It follows a successful
    # scanner and is unavailable to PRs, queue runs, branches and bounded dispatch.
    record = next(step for step in scan["steps"] if step.get("name") == "Record successfully scanned head")
    upload = next(step for step in scan["steps"] if step.get("name") == "Save successfully scanned head")
    assert scan["steps"].index(scanner) < scan["steps"].index(record) < scan["steps"].index(upload)
    assert record["env"]["SCANNED_HEAD"] == "${{ steps.secret-scan-scope.outputs.trufflehog_head }}"
    assert upload["with"]["name"] == "secret-scan-covered-head-v1"
    for branch in ("main", "feature"):
        for status in ("success", "failure", "cancelled"):
            context["github"].update(ref=f"refs/heads/{branch}", event={"repository": {"default_branch": "main"}})
            context["job"] = {"status": status}
            expected = (
                status == "success"
                and branch == "main"
                and (event == "schedule" or (event == "workflow_dispatch" and mode == "full-history-audit"))
            )
            assert _condition(record["if"], context) is expected
            assert _condition(upload["if"], context) is expected


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
    github: dict[str, Any], *, failures: set[str] | None = None
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (job id -> success|skipped, job id -> evaluated check name) for ci.yml.

    Follows GitHub's rule: a job whose `if` has no status function carries an
    implicit success() and is skipped when any `needs` job did not succeed.
    Every job that runs is assumed to succeed unless a failure is injected.
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
                    "outputs": {},
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


@pytest.mark.parametrize("event", sorted(_EVENTS))
def test_every_event_runs_every_job(event: str) -> None:
    results, names = _simulate(_EVENTS[event])
    skipped = {job for job, result in results.items() if result != "success"}
    expected = set() if event == "merge_group" else {"queue-metadata-scan"}
    if event in {"opened", "synchronize", "reopened"}:
        expected |= {"frontend", "refresh-pytest-durations", "pytest", "pytest-report"}
    assert skipped == expected
    assert names["ci-gate"] == "CI Gate"


def test_merge_queue_always_executes_full_suite() -> None:
    results, _ = _simulate(_EVENTS["merge_group"])
    assert all(result == "success" for result in results.values())
    assert "reuse" not in results


def test_pr_runs_share_one_group_per_pr_number() -> None:
    # A push cancels the in-flight run for the previous SHA of the PR.
    groups = {_concurrency_group(_EVENTS[name]) for name in ("opened", "synchronize", "reopened")}
    assert groups == {"CI-pull_request-7"}
    assert _concurrency_group(_EVENTS["merge_group"]).startswith("CI-merge_group-refs/heads/gh-readonly-queue/")


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
    assert "required job was cancelled" in (_REPO_ROOT / "scripts/ci/gate.py").read_text()


_GREEN = {
    "SECRET_SCAN": "success",
    "CHECKS": "success",
    "PR_AFFECTED": "success",
    "FRONTEND": "success",
    "DEPENDENCY_AUDIT": "success",
    "PYTEST": "success",
    "PYTEST_REPORT": "success",
}


def _run_gate(event: str, **results: str) -> subprocess.CompletedProcess[str]:
    # Candidate identity and ancestry belong to this fixture, not the source
    # checkout, which may contain only HEAD in a real queue shard.
    with tempfile.TemporaryDirectory(dir=os.environ["TMPDIR"]) as directory:
        repo = Path(directory) / "candidate"
        subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True, timeout=30)
        commits = []
        for message in ("base", "candidate"):
            subprocess.run(
                ["git", "-C", str(repo), "-c", "user.name=CI fixture", "-c", "user.email=ci@example.invalid",
                 "commit", "--allow-empty", "-qm", message],
                check=True, capture_output=True, timeout=30,
            )
            commits.append(subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True, timeout=30,
            ).strip())
        base, actual = commits
        payload = {"repository": {"default_branch": "main"}}
        ref = "refs/heads/main"
        if event == "pull_request":
            payload.update(action="opened", pull_request={"number": 7, "base": {"sha": "b" * 40}, "head": {"sha": "a" * 40}})
            ref = "refs/pull/7/merge"
        elif event == "merge_group":
            ref = "refs/heads/gh-readonly-queue/main/pr-7-" + "d" * 40
            payload.update(action="checks_requested", merge_group={"base_sha": base, "base_ref": "refs/heads/main", "head_sha": actual, "head_ref": ref})
        elif event == "schedule":
            payload["schedule"] = "30 3 * * *"
        elif event == "workflow_dispatch":
            payload["ref"] = "refs/heads/main"
        jobs = {**_GREEN, "REFRESH": "success", "METADATA_SCAN": "success" if event == "merge_group" else "skipped"}
        if event == "pull_request":
            jobs.update({name: "skipped" for name in ("FRONTEND", "REFRESH", "PYTEST", "PYTEST_REPORT")})
        # Existing test bodies can corrupt the real entry-point event and candidate.
        overrides = {key: results.pop(key) for key in list(results) if key.startswith("GITHUB_") or key == "NEEDS_JSON"}
        raw_payload = overrides.pop("GITHUB_EVENT_JSON", json.dumps(payload))
        jobs.update(results)
        mapping = {"PR_AFFECTED": "pr-affected", "SECRET_SCAN": "secret-scan", "CHECKS": "checks", "FRONTEND": "frontend", "DEPENDENCY_AUDIT": "dependency-audit", "REFRESH": "refresh-pytest-durations", "PYTEST": "pytest", "PYTEST_REPORT": "pytest-report", "METADATA_SCAN": "queue-metadata-scan"}
        needs = {mapping.get(name, name): {"result": value} for name, value in jobs.items()}
        event_path = Path(directory) / "event.json"
        event_path.write_text(raw_payload)
        result = subprocess.run(
            ["bash", "-e", "-c", _gate_script()], cwd=_REPO_ROOT, check=False, capture_output=True, text=True,
            env={**os.environ, "GIT_DIR": str(repo / ".git"), "GIT_WORK_TREE": str(repo), "PYTHON_BIN": sys.executable, "EVENT_NAME": event, "GITHUB_EVENT_PATH": str(event_path), "GITHUB_SHA": actual, "GITHUB_REF": ref, "GITHUB_STEP_SUMMARY": str(Path(directory) / "summary"), "NEEDS_JSON": json.dumps(needs), **overrides}, timeout=30,
        )
        if result.returncode == 0:
            summary = (Path(directory) / "summary").read_text()
            assert ("full pytest was not run" in summary) == (event == "pull_request")
        return result



def test_gate_passes_a_green_pull_request_run() -> None:
    result = _run_gate("pull_request")
    assert result.returncode == 0, result.stdout
    assert "CI Gate green" in result.stdout
    assert "full pytest was not run" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"PYTEST": "failure"}, {"PYTEST": "success"}, {"PYTEST_REPORT": "success"},
        {"CHECKS": "cancelled"}, {"SECRET_SCAN": ""}, {"FRONTEND": "success"},
        {"DEPENDENCY_AUDIT": "failure"}, {"DEPENDENCY_AUDIT": "skipped"},
        {"REFRESH": "success"}, {"METADATA_SCAN": "success"},
    ],
)
def test_gate_fails_a_pull_request_run_missing_any_job(overrides: dict[str, str]) -> None:
    result = _run_gate("pull_request", **overrides)
    assert result.returncode != 0, result.stdout


def test_gate_requires_real_event_and_candidate_identity() -> None:
    for event in ("pull_request", "merge_group", "schedule", "workflow_dispatch"):
        assert _run_gate(event).returncode == 0
        for key in ("SECRET_SCAN", "CHECKS", "DEPENDENCY_AUDIT", "PYTEST", "PYTEST_REPORT", "REFRESH", "FRONTEND"):
            assert _run_gate(event, **{key: "unknown"}).returncode != 0
        for corruption in ({"GITHUB_EVENT_JSON": "{}"}, {"GITHUB_EVENT_JSON": "{"}, {"GITHUB_SHA": "f" * 40}, {"GITHUB_REF": "refs/heads/wrong\n$(false)"}):
            result = _run_gate(event, **corruption)
            assert result.returncode != 0, (event, corruption, result.stdout)
    # GitHub's primary webhook fixture uses a fully qualified dispatch ref;
    # API branch names normalize to the same candidate, never another tier.
    for ref in ("main", "refs/heads/main"):
        payload = {"repository": {"default_branch": "main"}, "ref": ref, "inputs": None}
        assert _run_gate("workflow_dispatch", GITHUB_EVENT_JSON=json.dumps(payload)).returncode == 0
    for event in ("", "push", "pull_request_target", "unknown", "merge_group\n$(false)"):
        assert _run_gate(event).returncode != 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"PYTEST": "skipped"}, {"PYTEST_REPORT": "skipped"}, {"CHECKS": "failure"},
        {"SECRET_SCAN": "cancelled"}, {"FRONTEND": "skipped"}, {"PYTEST": ""},
        {"REFRESH": "failure"}, {"REFRESH": "cancelled"}, {"REFRESH": "skipped"},
        {"METADATA_SCAN": "skipped"}, {"METADATA_SCAN": "failure"}, {"METADATA_SCAN": "cancelled"},
    ],
)
def test_gate_fails_closed_in_the_merge_queue(overrides: dict[str, str]) -> None:
    result = _run_gate("merge_group", **overrides)
    assert result.returncode != 0, result.stdout


def test_gate_passes_a_full_merge_queue_run() -> None:
    result = _run_gate("merge_group")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("failed_job", ["checks"])
def test_pytest_runs_after_lint_failure(failed_job: str) -> None:
    results, _ = _simulate(_EVENTS["workflow_dispatch"], failures={failed_job})
    assert results[failed_job] == "failure"
    assert results["pytest"] == "success"


def test_ci_gate_guard_step_order_and_event_conditions() -> None:
    steps = _ci_gate_job()["steps"]
    step_names = [step.get("name") for step in steps]
    assert "Require every job" in step_names
    assert "Check large files guard" in step_names

    guard_idx = step_names.index("Check large files guard")
    aggregation_idx = step_names.index("Require every job")
    assert guard_idx < aggregation_idx

    # Checkout/setup run for every event so the parser can verify the actual candidate.
    guard_steps = steps[:aggregation_idx]
    assert len(guard_steps) == 3

    for step in guard_steps[2:]:
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
    assert all("if" not in step for step in guard_steps[:2])
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

def test_pr_affected_checks_are_required_and_defer_truthfully() -> None:
    """Missing or non-success changed-test proof must never admit a PR."""
    job = _load('ci.yml')['jobs']['pr-affected']
    assert job['timeout-minutes'] == 10
    assert 'needs' not in job
    assert 'continue-on-error' not in job
    assert 'pr-affected' in _ci_gate_job()['needs']
    checkout = next(s for s in job['steps'] if str(s.get('uses', '')).startswith('actions/checkout@'))
    assert checkout['with'] == {'persist-credentials': False, 'fetch-depth': 0}
    setup = next(s for s in job['steps'] if s.get('name') == 'Set up bubblewrap')
    assert setup['if'] == "github.event_name == 'pull_request'"
    assert setup['run'] == 'bash scripts/ci/setup_bubblewrap.sh'
    assert not setup.get('continue-on-error', False)
    shared = (_REPO_ROOT / 'scripts/ci/setup_bubblewrap.sh').read_text()
    assert 'set -euo pipefail' in shared
    assert 'for pkg in bubblewrap "$@" apparmor; do' in shared
    assert 'bwrap --unshare-user --unshare-pid --ro-bind / / -- /usr/bin/true' in shared
    postgres = (_REPO_ROOT / 'scripts/ci/start_postgres.sh').read_text()
    assert 'bash "$(dirname "${BASH_SOURCE[0]}")/setup_bubblewrap.sh" postgresql-16 libpq-dev' in postgres
    step = next(s for s in job['steps'] if s.get('name') == 'Run changed test files and guards')
    assert job['steps'].index(setup) < job['steps'].index(step)
    assert '.venv/bin/python -m scripts.ci.pr_affected_tests' in step['run']
    assert '"$EVENT_NAME" = pull_request' in step['run']
    for status in ('failure', 'skipped', 'cancelled', '', 'unknown'):
        result = _run_gate('pull_request', PR_AFFECTED=status)
        assert result.returncode == 1, result.stdout
    result = _run_gate('pull_request', PR_AFFECTED='success')
    assert result.returncode == 0
    assert 'full pytest was not run' in result.stdout
    # An absent dependency is distinct from a present dependency with no result.
    from scripts.ci.gate import COMMON
    assert 'pr-affected' in COMMON
    needs = {name: {'result': 'success'} for name in COMMON - {'pr-affected'}}
    needs.update({name: {'result': 'skipped'} for name in ('queue-metadata-scan', 'frontend', 'refresh-pytest-durations', 'pytest', 'pytest-report')})
    assert _run_gate('pull_request', NEEDS_JSON=json.dumps(needs)).returncode == 1
    result = _run_gate('pull_request', UNEXPECTED='success')
    assert result.returncode == 1
