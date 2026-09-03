"""Hermetic coverage for #4811 runner-queue starvation guards that survive
the 2026-09-03 simple-CI cutover.

The scheduled ``ci-gate-queue-recovery.yml`` workflow and
``scripts/ci/queue_starvation_recovery.py`` keyed their tail-job detection on
the now-deleted ``Coverage floor`` job name and were retired with it (Fable
VERDICT: FIX on #7657). This file keeps the surviving job-graph invariants:
secret-scan stays separate from contracts, always-on parallel runner slots
stay within budget, and the always-on-vs-scheduled fan-out split for
hygiene/security/UI-policy is unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.ci import gate_required_results as gate

pytestmark = pytest.mark.repo_invariant

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI = _REPO_ROOT / ".github/workflows/ci.yml"
_HYGIENE = _REPO_ROOT / ".github/workflows/hygiene.yml"

# Always-on jobs that start together on every CI event.
_MAX_ALWAYS_ON_PARALLEL_SLOTS = 6

# Secret-scan timeout budget (#7263 / #4811):
# Sized to the 3-attempt TruffleHog cadence with backoff sleeps:
# 75s checkout + 3*(10s pull + 50s scan) + (10s + 30s) sleeps = 295s (~5 min) + 2 min margin = 7 min.
# A 7-minute bound keeps landing secret scanning bounded without starving the runner queue (#4811):
# 1. Parallel slots: secret-scan occupies 1 runner slot, keeping always-on parallel
#    jobs (6) within the _MAX_ALWAYS_ON_PARALLEL_SLOTS budget.
# 2. Critical path: secret-scan (<=7m) completes well before pytest (40m timeout,
#    ~10-15m runtime) and contracts/frontend (25m), so it is not the critical path.
_MAX_SECRET_SCAN_TIMEOUT_MINUTES = 7


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _triggers(workflow: dict) -> dict:
    raw = workflow.get("on", workflow.get(True))
    assert raw is not None
    return raw


def test_ci_keeps_secret_scan_separate_from_full_contracts() -> None:
    jobs = _load(_CI)["jobs"]
    assert "security" not in jobs
    assert "pr-body-references" not in jobs
    secret_steps = "\n".join(
        step.get("name", "")
        + "\n"
        + str(step.get("if", ""))
        + "\n"
        + str(step.get("uses", ""))
        + "\n"
        + str(step.get("run", ""))
        for step in jobs["secret-scan"]["steps"]
    )
    contracts_steps = "\n".join(
        step.get("name", "") + "\n" + str(step.get("uses", "")) + "\n" + str(step.get("run", ""))
        for step in jobs["contracts"]["steps"]
    )
    assert jobs["secret-scan"].get("if") is None
    assert "trufflesecurity/trufflehog@" in secret_steps
    assert "lint_opsec_leaks.py" in secret_steps
    assert "check_no_internal_ids.py" in secret_steps
    assert "lint_pr_closing_references.py" in secret_steps
    assert "github.event_name == 'pull_request'" in secret_steps
    assert "trufflesecurity/trufflehog@" not in contracts_steps
    assert "lint_opsec_leaks.py" not in contracts_steps
    assert "check_no_internal_ids.py" not in contracts_steps
    assert "lint_pr_closing_references.py" not in contracts_steps
    assert "check_teacher_cloze_content.py" in contracts_steps
    # Rule of thumb: assert an invariant, not a snapshot; if changing X
    # legitimately requires editing >1 test, the test is a snapshot.
    # ci-gate.needs is pinned exactly once — by the canonical set the gate
    # evaluator itself exports (gate_required_results.GATE_NEEDS_JOBS).
    assert set(jobs["ci-gate"]["needs"]) == set(gate.GATE_NEEDS_JOBS)
    assert "if" not in jobs["contracts"]
    assert "if" not in jobs["pytest"]
    assert "if" not in jobs["frontend"]
    assert "ruff" in jobs
    gate_steps = "\n".join(step.get("name", "") + "\n" + str(step.get("run", "")) for step in jobs["ci-gate"]["steps"])
    assert "gate_required_results.py" in gate_steps
    assert "contains(needs.*.result, 'skipped')" not in gate_steps


def test_secret_scan_bounds_landing_secret_and_opsec_scans() -> None:
    workflow = _CI.read_text(encoding="utf-8")
    secret_scan = _load(_CI)["jobs"]["secret-scan"]
    assert secret_scan["timeout-minutes"] <= _MAX_SECRET_SCAN_TIMEOUT_MINUTES
    assert "Resolve secret scan commit scope (#7141)" in workflow
    assert "MERGE_GROUP_BASE_SHA: ${{ github.event.merge_group.base_sha || '' }}" in workflow
    assert "MERGE_GROUP_HEAD_SHA: ${{ github.event.merge_group.head_sha || '' }}" in workflow
    assert "PUSH_BEFORE_SHA: ${{ github.event.before || '' }}" in workflow
    assert "PUSH_AFTER_SHA: ${{ github.event.after || '' }}" in workflow
    assert "base: ${{ steps.secret-scan-scope.outputs.trufflehog_base }}" in workflow
    assert "head: ${{ steps.secret-scan-scope.outputs.trufflehog_head }}" in workflow
    assert '--commit-range "$OPSEC_RANGE" --public-identifiers' in workflow
    assert 'if [ "$EVENT_NAME" = "pull_request" ]; then' in workflow
    scope_index = workflow.index("Resolve secret scan commit scope (#7141)")
    assert scope_index < workflow.index("Gate scrubbed public identifiers")
    assert scope_index < workflow.index("TruffleHog secret scan (attempt 1)")


def test_always_on_parallel_runner_slots_stay_within_budget() -> None:
    jobs = _load(_CI)["jobs"]
    parallel = 0
    for name, job in jobs.items():
        if name == "ci-gate":
            continue
        if "needs" in job:
            continue
        matrix = job.get("strategy", {}).get("matrix", {})
        shards = matrix.get("shard")
        if isinstance(shards, list):
            parallel += len(shards)
        else:
            parallel += 1
    assert parallel <= _MAX_ALWAYS_ON_PARALLEL_SLOTS, (
        f"always-on parallel slots={parallel} exceed budget {_MAX_ALWAYS_ON_PARALLEL_SLOTS} (#4811)"
    )


def test_hygiene_uses_one_composite_checks_job() -> None:
    jobs = _load(_HYGIENE)["jobs"]
    assert "hygiene-checks" in jobs
    assert "changes" not in jobs, "path-filter job retired with PR fan-out trim (#6943)"
    for retired in (
        "quality-gates",
        "lint-prompts",
        "postmortem-hygiene",
        "agent-config",
        "scripts-root-guard",
    ):
        assert retired not in jobs, f"{retired} must stay folded into hygiene-checks (#4811)"


def test_hygiene_left_pull_request_fanout() -> None:
    triggers = _triggers(_load(_HYGIENE))
    assert "pull_request" not in triggers
    assert "schedule" in triggers
    assert "merge_group" in triggers
    assert "workflow_dispatch" in triggers


def test_security_and_ui_policy_left_pull_request_fanout() -> None:
    security = _REPO_ROOT / ".github/workflows/security-audit.yml"
    ui = _REPO_ROOT / ".github/workflows/ui-policy-gate.yml"
    sec_triggers = _triggers(_load(security))
    ui_triggers = _triggers(_load(ui))
    assert "pull_request" not in sec_triggers
    assert "schedule" in sec_triggers
    assert "pull_request" not in ui_triggers
    assert "schedule" in ui_triggers
    assert "workflow_dispatch" in ui_triggers
    # paths: is invalid on merge_group (actionlint); UI policy stays schedule-only.


def test_recovery_workflow_and_script_are_retired() -> None:
    """The recovery workflow keyed on the deleted `Coverage floor` job name."""
    recovery = _REPO_ROOT / ".github/workflows/ci-gate-queue-recovery.yml"
    script = _REPO_ROOT / "scripts/ci/queue_starvation_recovery.py"
    assert not recovery.exists()
    assert not script.exists()
