"""Guard the merge-group kick comment step on CI Gate (#7042).

Kicked PRs (merge_group CI Gate red, GitHub dequeues the PR) used to look
CLEAN and just sit — nothing told the driver to look. This adds ONE
best-effort step to the existing `ci-gate` job: on a merge_group failure it
comments the source PR with the run URL and per-job results. No new
workflow, no new required check, no recovery bot — see
agents_extensions/shared/skills/drive-epic/SKILL.md §7.

These tests assert the wiring statically (no GitHub Actions run required):
the step only fires on `failure() && merge_group`, the job gained exactly
the permissions it needs to comment, and no job was added to the workflow.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from scripts.ci import gate_required_results as gate

_REPO_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci_gate() -> dict:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    return workflow["jobs"]["ci-gate"]


def _comment_step(ci_gate: dict) -> dict:
    for step in ci_gate["steps"]:
        if step.get("name") == "Comment merge-queue kick on source PR":
            return step
    raise AssertionError("ci-gate is missing the merge-queue kick comment step")


def test_comment_step_only_fires_on_merge_group_failure() -> None:
    step = _comment_step(_load_ci_gate())
    assert step["if"] == "failure() && github.event_name == 'merge_group'", (
        "the comment step must fire only when the gate failed on a merge_group run, "
        "never on pull_request or push"
    )


def test_ci_gate_job_grants_only_the_needed_write() -> None:
    ci_gate = _load_ci_gate()
    assert ci_gate["permissions"] == {"contents": "read", "pull-requests": "write"}, (
        "ci-gate must scope its own permissions rather than widening workflow-level perms"
    )
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    assert workflow["permissions"] == {"contents": "read"}, (
        "workflow-level permissions must stay untouched by the job-level grant"
    )


def test_comment_step_never_overrides_the_gate_result() -> None:
    step = _comment_step(_load_ci_gate())
    run_lines = [line.strip() for line in step["run"].splitlines() if line.strip()]
    assert run_lines[0] == "set +e", (
        "a parse/comment failure inside this step must never flip an already-failed "
        "gate to something else — the step disables -e before doing anything fallible"
    )
    assert run_lines[-1] == "exit 0", (
        "the step must end by exiting 0 so its own result never changes the gate's "
        "already-computed pass/fail"
    )


def test_comment_step_reads_pr_number_and_results_from_env_not_interpolation() -> None:
    step = _comment_step(_load_ci_gate())
    env = step["env"]
    assert env["HEAD_REF"] == "${{ github.event.merge_group.head_ref }}"
    assert "RESULTS" in env and "needs.ruff.result" in env["RESULTS"]
    run = step["run"]
    # Untrusted merge_group head_ref must be read through $HEAD_REF, never
    # spliced into the script via ${{ }} (see check_untrusted_workflow_interpolation.py).
    assert "${{" not in run
    assert "$HEAD_REF" in run


def test_no_new_job_was_added_to_ci_workflow() -> None:
    workflow = yaml.safe_load(_WORKFLOW.read_text(encoding="utf-8"))
    # Rule of thumb: assert an invariant, not a snapshot; if changing X
    # legitimately requires editing >1 test, the test is a snapshot. The job
    # inventory derives from the one canonical ci-gate.needs set exported by
    # the gate evaluator, plus the two frozen-by-decision jobs that hang off
    # the gate rather than feed it (frontend-e2e waits on ci-gate; ci-gate is
    # the gate itself).
    expected_jobs = set(gate.GATE_NEEDS_JOBS) | {"frontend-e2e", "ci-gate"}
    assert set(workflow["jobs"]) == expected_jobs, (
        "the merge-group kick comment must be a step on ci-gate, not an unrelated job"
    )
