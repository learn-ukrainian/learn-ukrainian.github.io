"""Pin the #8505 trigger split: body edits and labels must not rerun full CI.

Safety invariant under test: no event path may make the required "CI Gate"
check green or skipped without the classified tier running.

- ci.yml fires only on opened/synchronize/reopened; `edited` and `labeled`
  would restart the 15-minute CI on an unchanged commit.
- The negated-closing-reference body guard moved to pr-body-guard.yml, which
  is the only workflow subscribed to `edited` (S2).
- The `full-ci` label is served by full-ci-label.yml, which reruns the latest
  ci.yml run; scripts/ci/classify_changes.py then reads CURRENT labels via the
  API and fails closed to the full tier (S3) — that fail-closed behavior is
  unit-tested in scripts/ci/test_classify_changes.py.
- Exactly one job in the fleet is named "CI Gate" (ci.yml), and it keeps
  `if: always() && !cancelled()`, so a cancelled run concludes `cancelled`,
  never success — PR-number concurrency cannot launder a green Gate (S1).
"""

from __future__ import annotations

from pathlib import Path

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


def test_ci_does_not_trigger_on_edited_or_labeled() -> None:
    types = _pr_types(_load("ci.yml"))
    assert types == {"opened", "synchronize", "reopened"}
    assert "edited" not in types and "labeled" not in types


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


def test_full_ci_label_workflow_fails_closed_shape() -> None:
    workflow = _load("full-ci-label.yml")
    assert _pr_types(workflow) == {"labeled"}
    # Least privilege: write scope lives on the job, not the workflow.
    assert workflow.get("permissions") == {"contents": "read"}
    jobs = workflow["jobs"]
    assert len(jobs) == 1
    job = next(iter(jobs.values()))
    assert job["if"] == "github.event.label.name == 'full-ci'"
    assert job["permissions"] == {"contents": "read", "actions": "write"}
    text = (_WORKFLOWS / "full-ci-label.yml").read_text(encoding="utf-8")
    assert "workflows/ci.yml/runs" in text and "gh run rerun" in text


def test_ci_changes_job_can_read_pr_labels() -> None:
    # S3 wiring: the API label lookup in classify_changes.py needs
    # pull-requests: read on the Changes job (rerun payloads are stale).
    changes = _load("ci.yml")["jobs"]["changes"]
    assert changes["permissions"]["pull-requests"] == "read"


def test_exactly_one_ci_gate_job_and_it_never_runs_when_cancelled() -> None:
    # S1: a skipped or fake "CI Gate" from another event path would satisfy the
    # required check without the tier running. Only ci.yml may define it, and
    # its `!cancelled()` guard keeps a cancelled run's conclusion non-success.
    gate_jobs = []
    for path in sorted(_WORKFLOWS.glob("*.yml")):
        workflow = _load(path.name)
        for job in (workflow.get("jobs") or {}).values():
            if job.get("name") == "CI Gate":
                gate_jobs.append((path.name, job))
    assert [name for name, _ in gate_jobs] == ["ci.yml"]
    gate = gate_jobs[0][1]
    assert "always()" in gate["if"] and "!cancelled()" in gate["if"]
