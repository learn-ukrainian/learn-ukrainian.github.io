#!/usr/bin/env python3
"""Decide whether a completed CI run should be re-run after runner-queue starvation.

Issue #4811: under account concurrent-job pressure, the last-to-start job
(usually ``CI Gate``) waits ~15 minutes for a GitHub-hosted runner and is then
cancelled with empty logs. Every other job in the run succeeded. That cancel
fails the sole required check and blocks ``gh pr merge --auto``.

This module encodes a fail-closed signature for that incident class so a
``workflow_run`` recovery job can re-run only the cancelled tail jobs — never
genuine test/contract failures, and never a mid-run cancel from
``cancel-in-progress`` (multiple non-tail jobs cancelled).

Root capacity (org concurrent-job limit) remains an owner setting. This is the
in-repo stopgap listed as mitigation #3 on #4811.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

# Jobs that become eligible only after the heavy parallel fan-out finishes.
# Queue starvation cancels these; ``cancel-in-progress`` cancels earlier jobs too.
TAIL_JOB_NAMES = frozenset({"CI Gate", "Coverage floor"})
# Re-run dependencies before dependents when both were queue-cancelled.
TAIL_RERUN_ORDER = ("Coverage floor", "CI Gate")

CI_WORKFLOW_NAME = "CI"
DEFAULT_MAX_ATTEMPTS = 2


@dataclass(frozen=True)
class RecoveryDecision:
    """Structured verdict for the recovery workflow."""

    should_rerun: bool
    reason: str
    job_ids: tuple[int, ...] = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def _conclusion(job: Mapping[str, Any]) -> str:
    raw = job.get("conclusion")
    if raw is None:
        return ""
    return str(raw).strip().lower()


def _job_name(job: Mapping[str, Any]) -> str:
    return str(job.get("name") or "").strip()


def _job_id(job: Mapping[str, Any]) -> int | None:
    raw = job.get("id")
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw if raw > 0 else None
    if isinstance(raw, str) and raw.isdigit():
        value = int(raw)
        return value if value > 0 else None
    return None


def decide_queue_starvation_rerun(
    jobs: Sequence[Mapping[str, Any]],
    *,
    run_attempt: int,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    workflow_name: str = CI_WORKFLOW_NAME,
    expected_workflow_name: str = CI_WORKFLOW_NAME,
) -> RecoveryDecision:
    """Return whether cancelled tail jobs should be re-run once.

    Parameters
    ----------
    jobs:
        GitHub Actions job objects (``name``, ``conclusion``, ``id``).
    run_attempt:
        ``run_attempt`` from the completed workflow run (1-based).
    max_attempts:
        Do not re-run once this many attempts have already completed.
    workflow_name / expected_workflow_name:
        Recovery only applies to the primary ``CI`` workflow.
    """
    if workflow_name != expected_workflow_name:
        return RecoveryDecision(
            False,
            f"workflow {workflow_name!r} is not {expected_workflow_name!r}",
        )
    if run_attempt < 1:
        return RecoveryDecision(False, f"invalid run_attempt={run_attempt}")
    if max_attempts < 1:
        return RecoveryDecision(False, f"invalid max_attempts={max_attempts}")
    if run_attempt >= max_attempts:
        return RecoveryDecision(
            False,
            f"run_attempt {run_attempt} already at max_attempts {max_attempts}",
        )

    named = [job for job in jobs if _job_name(job)]
    if not named:
        return RecoveryDecision(False, "no named jobs in run")

    conclusions = {_job_name(job): _conclusion(job) for job in named}
    if any(conclusion == "failure" for conclusion in conclusions.values()):
        return RecoveryDecision(False, "run contains a failed job (not queue starvation)")

    cancelled = {name for name, conclusion in conclusions.items() if conclusion == "cancelled"}
    if not cancelled:
        return RecoveryDecision(False, "no cancelled jobs")
    if "CI Gate" not in cancelled:
        return RecoveryDecision(False, "CI Gate was not cancelled")
    if not cancelled <= TAIL_JOB_NAMES:
        return RecoveryDecision(
            False,
            "non-tail jobs were cancelled (likely cancel-in-progress / superseded run)",
        )

    successes = [name for name, conclusion in conclusions.items() if conclusion == "success"]
    if not successes:
        return RecoveryDecision(False, "no successful jobs — refusing to treat as tail starvation")

    job_ids_by_name: dict[str, int] = {}
    for job in named:
        name = _job_name(job)
        if name in cancelled and _conclusion(job) == "cancelled":
            job_id = _job_id(job)
            if job_id is None:
                return RecoveryDecision(
                    False,
                    f"cancelled job {name!r} has no numeric id — cannot request a job re-run",
                )
            job_ids_by_name[name] = job_id

    job_ids = tuple(
        job_ids_by_name[name] for name in TAIL_RERUN_ORDER if name in job_ids_by_name
    )

    return RecoveryDecision(
        True,
        "CI Gate cancelled after upstream successes — queue-starvation signature (#4811)",
        job_ids,
    )


def _load_jobs(payload: str) -> list[dict[str, Any]]:
    text = payload.strip()
    if text.startswith("["):
        raw = json.loads(text)
    else:
        with open(payload, encoding="utf-8") as handle:
            raw = json.load(handle)
    if not isinstance(raw, list):
        raise SystemExit("jobs payload must be a JSON array")
    return [item for item in raw if isinstance(item, dict)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs-json",
        required=True,
        help="Path to a JSON array of workflow jobs, or a literal JSON array string",
    )
    parser.add_argument("--run-attempt", required=True, type=int)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--workflow-name", default=CI_WORKFLOW_NAME)
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Also emit should_rerun / job_ids / reason lines for $GITHUB_OUTPUT",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    jobs = _load_jobs(args.jobs_json)
    decision = decide_queue_starvation_rerun(
        jobs,
        run_attempt=args.run_attempt,
        max_attempts=args.max_attempts,
        workflow_name=args.workflow_name,
    )
    print(decision.to_json())
    if args.github_output:
        import os

        out_path = os.environ.get("GITHUB_OUTPUT")
        if not out_path:
            raise SystemExit("--github-output requires GITHUB_OUTPUT")
        with open(out_path, "a", encoding="utf-8") as handle:
            handle.write(f"should_rerun={'true' if decision.should_rerun else 'false'}\n")
            handle.write(f"reason={decision.reason}\n")
            handle.write(f"job_ids={','.join(str(job_id) for job_id in decision.job_ids)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
