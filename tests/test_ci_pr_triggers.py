"""Pin the #8505 trigger split: body edits and labels must not rerun full CI.

Safety invariant under test: no event path may make the required "CI Gate"
check green or skipped without the classified tier running, and a label may
never leave an earlier, lighter-tier green Gate standing.

- ci.yml fires on opened/synchronize/reopened/labeled, never `edited`. The
  negated-closing-reference body guard lives in pr-body-guard.yml, which is
  the only workflow subscribed to `edited` (S2).
- A `full-ci` label is an ordinary full-tier run (S3). Its full-ci-pending job
  reports a failing "CI Gate" at once; the run's real Gate supersedes it.
- Any other label is a no-op run: every job skips, the gate job is renamed so
  no "CI Gate" check is reported, and the run has its own concurrency group.
- The Gate uses `if: always()` and fails when a required dependency was
  cancelled or skipped unexpectedly (S1). GitHub treats a skipped required job
  as success. On pull_request it re-reads labels and fails if `full-ci` is set
  but the tier was not full.

The job conditions, job names, and concurrency group are GitHub expressions.
The evaluator below implements the subset ci.yml uses, with GitHub semantics
(case-insensitive string equality, `&&`/`||` return an operand), so the tests
evaluate the real YAML against every event shape instead of grepping it.
"""

from __future__ import annotations

import math
import os
import re
import subprocess
import textwrap
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
    ctx = {"github": {"event": {"action": "labeled", "label": {"name": "Full-CI"}}}}
    assert _evaluate("github.event.label.name == 'full-ci'", ctx) is True  # case-insensitive
    assert _evaluate("github.event.missing == 'labeled'", ctx) is False
    assert _evaluate("github.event.missing != 'labeled'", ctx) is True
    assert _evaluate("false && 'x' || ''", ctx) == ""
    assert _evaluate("true && 'x' || ''", ctx) == "x"
    assert _evaluate("!(true && false)", ctx) is True
    assert _interpolate("a-${{ 7 }}-${{ null }}", ctx) == "a-7-"


# --- ci.yml job simulation -------------------------------------------------

_REAL_OUTPUTS = {
    "changes": {"docs_only": "false", "backend": "true", "frontend": "true", "shards": "[1]"},
}


def _github(event_name: str, event: dict[str, Any], ref: str = "refs/pull/7/merge") -> dict[str, Any]:
    return {"workflow": "CI", "event_name": event_name, "event": event, "ref": ref}


def _pr_event(action: str, label: str | None = None) -> dict[str, Any]:
    event: dict[str, Any] = {
        "action": action,
        "pull_request": {"number": 7, "head": {"sha": "a" * 40}, "labels": []},
    }
    if label is not None:
        event["label"] = {"name": label}
    return _github("pull_request", event)


_REAL_EVENTS = {
    "opened": _pr_event("opened"),
    "synchronize": _pr_event("synchronize"),
    "reopened": _pr_event("reopened"),
    "labeled-full-ci": _pr_event("labeled", "full-ci"),
    "merge_group": _github(
        "merge_group",
        {"action": "checks_requested", "merge_group": {"head_sha": "b" * 40}},
        ref="refs/heads/gh-readonly-queue/main/pr-7-" + "b" * 40,
    ),
    "schedule": _github("schedule", {"schedule": "30 3 * * *"}, ref="refs/heads/main"),
    "workflow_dispatch": _github("workflow_dispatch", {}, ref="refs/heads/main"),
}
_NOOP_EVENTS = {
    "labeled-area": _pr_event("labeled", "area:infra"),
    "labeled-near-miss": _pr_event("labeled", "full-ci-later"),
    "labeled-quote": _pr_event("labeled", "it's"),
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
                    "outputs": _REAL_OUTPUTS.get(need, {}) if results[need] == "ran" else {},
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


def test_ci_triggers_on_labeled_but_not_edited() -> None:
    assert _pr_types(_load("ci.yml")) == {"opened", "synchronize", "reopened", "labeled"}


def test_full_ci_label_rerun_workflow_is_gone() -> None:
    # The labeled run replaces the API rerun side-workflow (#8505 round 4).
    assert not (_WORKFLOWS / "full-ci-label.yml").exists()
    for path in _WORKFLOWS.glob("*.yml"):
        assert "gh run rerun" not in path.read_text(encoding="utf-8"), path.name


@pytest.mark.parametrize("event", sorted(_REAL_EVENTS))
def test_real_events_run_every_tier_job_and_report_ci_gate(event: str) -> None:
    results, names = _simulate(_REAL_EVENTS[event])
    real_jobs = {job for job in results if job != "full-ci-pending"}
    assert {job for job in real_jobs if results[job] != "ran"} == set()
    assert names["ci-gate"] == "CI Gate"
    assert names["changes"] == "Changes"


@pytest.mark.parametrize("event", sorted(set(_REAL_EVENTS) - {"labeled-full-ci"}))
def test_pending_marker_is_skipped_and_never_named_ci_gate_outside_full_ci(event: str) -> None:
    # A skipped job reports success; a skipped "CI Gate" would be green.
    results, names = _simulate(_REAL_EVENTS[event])
    assert results["full-ci-pending"] == "skipped"
    assert names["full-ci-pending"] != "CI Gate"


def test_full_ci_label_marks_ci_gate_failed_immediately() -> None:
    results, names = _simulate(_REAL_EVENTS["labeled-full-ci"])
    marker = _load("ci.yml")["jobs"]["full-ci-pending"]
    # No needs: it reports before the 15-minute tier, superseding an older
    # lighter-tier green Gate; the real Gate reports later and supersedes it.
    assert "needs" not in marker
    assert results["full-ci-pending"] == "ran" and names["full-ci-pending"] == "CI Gate"
    steps = marker["steps"]
    assert len(steps) == 1
    completed = subprocess.run(
        ["bash", "-c", steps[0]["run"]], check=False, capture_output=True, text=True
    )
    assert completed.returncode != 0
    assert "full-ci" in completed.stdout


@pytest.mark.parametrize("event", sorted(_NOOP_EVENTS))
def test_other_labels_are_noop_runs_that_report_no_ci_gate(event: str) -> None:
    github = _NOOP_EVENTS[event]
    results, names = _simulate(github)
    assert set(results.values()) == {"skipped"}
    # Skipped or not, no job in a no-op run may carry the required name:
    # it would report success and mask a red Gate on the same SHA.
    assert "CI Gate" not in names.values()


@pytest.mark.parametrize("event", sorted(_NOOP_EVENTS))
def test_noop_runs_cannot_cancel_a_real_run(event: str) -> None:
    noop_group = _concurrency_group(_NOOP_EVENTS[event])
    real_groups = {_concurrency_group(_REAL_EVENTS[name]) for name in ("synchronize", "labeled-full-ci")}
    assert real_groups == {"CI-pull_request-7"}
    assert noop_group == "CI-pull_request-7-label-noop"


def test_full_ci_label_run_shares_the_pr_group_to_cancel_a_lighter_run() -> None:
    assert _concurrency_group(_REAL_EVENTS["labeled-full-ci"]) == _concurrency_group(
        _REAL_EVENTS["synchronize"]
    )
    assert _concurrency_group(_REAL_EVENTS["merge_group"]).startswith("CI-merge_group-refs/heads/")


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


def test_ci_changes_job_can_read_pr_labels() -> None:
    # S3 wiring: the API label lookup in classify_changes.py needs
    # pull-requests: read on the Changes job (manual rerun payloads are stale).
    changes = _load("ci.yml")["jobs"]["changes"]
    assert changes["permissions"]["pull-requests"] == "read"


def test_only_ci_yml_can_report_ci_gate() -> None:
    carriers = []
    for path in sorted(_WORKFLOWS.glob("*.yml")):
        for job_id, job in (_load(path.name).get("jobs") or {}).items():
            if "CI Gate" in str(job.get("name", "")):
                carriers.append((path.name, job_id))
    assert carriers == [("ci.yml", "full-ci-pending"), ("ci.yml", "ci-gate")]


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
    # after a concurrency cancel (`always()`) and fail in the step. The
    # simulation shows it still runs when every dependency was skipped.
    condition = str(_ci_gate_job()["if"])
    assert condition.startswith("always()")
    assert "cancelled()" not in condition
    github = _REAL_EVENTS["synchronize"]
    context = {"github": github, "needs": {}}
    assert _condition(condition, context) is True
    script = _gate_script()
    assert "required job was cancelled" in script
    assert "full-ci" in script and "PYTEST_MODE" in script


def _run_gate(env: dict[str, str], *, gh: str | None = None) -> subprocess.CompletedProcess[str]:
    extra = {**os.environ, **env}
    if gh is not None:
        extra["PATH"] = gh + os.pathsep + os.environ.get("PATH", "")
    return subprocess.run(
        ["bash", "-c", _gate_script()],
        check=False,
        capture_output=True,
        text=True,
        env=extra,
    )


_GREEN = {
    "DOCS_ONLY": "false",
    "FRONTEND": "false",
    "BACKEND": "true",
    "PYTEST_MODE": "full",
    "CHANGES": "success",
    "RUFF": "success",
    "SECRET": "success",
    "PYTEST": "success",
    "CONTRACTS": "success",
    "FRONTEND_JOB": "skipped",
    "TYPESAFE_TRIAGE": "success",
    "PLAN_VALIDATE": "success",
    "EVENT_NAME": "merge_group",
    "REPO": "owner/repo",
    "PR_NUMBER": "",
}


def test_ci_gate_fails_when_a_required_job_was_cancelled() -> None:
    result = _run_gate({**_GREEN, "PYTEST": "cancelled"})
    assert result.returncode != 0
    assert "CI Gate green" not in result.stdout


def test_ci_gate_fails_when_a_required_job_was_skipped() -> None:
    result = _run_gate({**_GREEN, "SECRET": "skipped"})
    assert result.returncode != 0
    assert "CI Gate green" not in result.stdout


def test_ci_gate_allows_a_tier_skip_and_rejects_cancelled_tier_skip(tmp_path: Path) -> None:
    docs = {
        **_GREEN,
        "DOCS_ONLY": "true",
        "PYTEST_MODE": "docs",
        "RUFF": "skipped",
        "CONTRACTS": "skipped",
        "EVENT_NAME": "schedule",
    }
    assert _run_gate(docs).returncode == 0
    cancelled = _run_gate({**docs, "RUFF": "cancelled"})
    assert cancelled.returncode != 0
    assert "cancelled" in cancelled.stdout


def test_ci_gate_fails_when_full_ci_label_does_not_match_tier(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text(
        textwrap.dedent(
            """\
            #!/bin/sh
            printf '%s\\n' full-ci
            """
        ),
        encoding="utf-8",
    )
    (bin_dir / "gh").chmod(0o755)
    result = _run_gate(
        {
            **_GREEN,
            "PYTEST_MODE": "docs",
            "DOCS_ONLY": "true",
            "RUFF": "skipped",
            "CONTRACTS": "skipped",
            "EVENT_NAME": "pull_request",
            "PR_NUMBER": "7",
        },
        gh=str(bin_dir),
    )
    assert result.returncode != 0
    assert "full-ci" in result.stdout
    assert "CI Gate green" not in result.stdout


def test_ci_gate_passes_when_full_ci_label_matches_full_tier(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text("#!/bin/sh\nprintf '%s\\n' full-ci\n", encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    result = _run_gate(
        {**_GREEN, "EVENT_NAME": "pull_request", "PR_NUMBER": "7"},
        gh=str(bin_dir),
    )
    assert result.returncode == 0, result.stderr
    assert "CI Gate green" in result.stdout


def test_ci_gate_fails_closed_when_the_label_lookup_errors(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gh").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (bin_dir / "gh").chmod(0o755)
    result = _run_gate(
        {**_GREEN, "EVENT_NAME": "pull_request", "PR_NUMBER": "7"},
        gh=str(bin_dir),
    )
    assert result.returncode != 0
    assert "label lookup failed" in result.stdout
    assert "CI Gate green" not in result.stdout
