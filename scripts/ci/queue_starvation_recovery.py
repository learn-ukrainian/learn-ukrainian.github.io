#!/usr/bin/env python3
"""Decide whether a completed CI run should be re-run after runner-queue starvation.

Issue #4811: under account concurrent-job pressure, the last-to-start job
(usually ``CI Gate``) waits ~15 minutes for a GitHub-hosted runner and is then
cancelled with empty logs. Every other job in the run succeeded. That cancel
fails the sole required check and blocks ``gh pr merge --auto``.

This module encodes a fail-closed signature for that incident class so a
scheduled (or manually dispatched) recovery job can re-run only the cancelled
tail jobs — never genuine test/contract failures, and never a mid-run cancel
from ``cancel-in-progress`` (multiple non-tail jobs cancelled).

Trigger choice (#4811 / zizmor): prefer ``schedule`` + ``workflow_dispatch``
that scans recent CI runs via the Actions API. Do **not** use
``workflow_run`` — zizmor flags it as a fundamentally insecure trigger
(privileged recovery would otherwise run in response to untrusted workflow
completions). Checkout stays default-branch only; never execute recovery
logic from a subject run's head SHA.

Root capacity (org concurrent-job limit) remains an owner setting. This is the
in-repo stopgap listed as mitigation #3 on #4811.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

# Jobs that become eligible only after the heavy parallel fan-out finishes.
# Queue starvation cancels these; ``cancel-in-progress`` cancels earlier jobs too.
TAIL_JOB_NAMES = frozenset({"CI Gate", "Coverage floor"})
# Re-run dependencies before dependents when both were queue-cancelled.
TAIL_RERUN_ORDER = ("Coverage floor", "CI Gate")

CI_WORKFLOW_NAME = "CI"
CI_WORKFLOW_FILE = "ci.yml"
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_LOOKBACK_MINUTES = 90
DEFAULT_MAX_RUNS = 30
_CANDIDATE_CONCLUSIONS = frozenset({"cancelled", "failure"})


@dataclass(frozen=True)
class RecoveryDecision:
    """Structured verdict for the recovery workflow."""

    should_rerun: bool
    reason: str
    job_ids: tuple[int, ...] = ()

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


@dataclass(frozen=True)
class ScanAction:
    """One run the scanner decided to recover (or skipped with a reason)."""

    run_id: int
    decision: RecoveryDecision
    applied: bool = False
    apply_error: str | None = None


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


def _parse_github_timestamp(raw: str) -> datetime | None:
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def select_candidate_runs(
    runs: Sequence[Mapping[str, Any]],
    *,
    now: datetime,
    lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES,
    max_runs: int = DEFAULT_MAX_RUNS,
    expected_workflow_name: str = CI_WORKFLOW_NAME,
) -> list[dict[str, Any]]:
    """Filter Actions run objects down to recent cancelled/failed CI candidates."""
    if lookback_minutes < 1:
        raise ValueError(f"lookback_minutes must be >= 1, got {lookback_minutes}")
    if max_runs < 1:
        raise ValueError(f"max_runs must be >= 1, got {max_runs}")
    now = now.replace(tzinfo=UTC) if now.tzinfo is None else now.astimezone(UTC)
    cutoff = now - timedelta(minutes=lookback_minutes)

    selected: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, Mapping):
            continue
        name = str(run.get("name") or "").strip()
        if name != expected_workflow_name:
            continue
        if str(run.get("status") or "").strip().lower() != "completed":
            continue
        conclusion = str(run.get("conclusion") or "").strip().lower()
        if conclusion not in _CANDIDATE_CONCLUSIONS:
            continue
        updated = _parse_github_timestamp(str(run.get("updated_at") or run.get("created_at") or ""))
        if updated is None or updated < cutoff:
            continue
        run_id = run.get("id")
        if not isinstance(run_id, int) or run_id < 1:
            continue
        selected.append(dict(run))
        if len(selected) >= max_runs:
            break
    return selected


def scan_and_recover(
    runs: Sequence[Mapping[str, Any]],
    *,
    fetch_jobs: Callable[[int], Sequence[Mapping[str, Any]]],
    rerun_job: Callable[[int], None] | None = None,
    apply: bool = False,
    now: datetime | None = None,
    lookback_minutes: int = DEFAULT_LOOKBACK_MINUTES,
    max_runs: int = DEFAULT_MAX_RUNS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    expected_workflow_name: str = CI_WORKFLOW_NAME,
) -> list[ScanAction]:
    """Scan recent CI runs and optionally re-run queue-starved tail jobs once."""
    clock = now if now is not None else datetime.now(UTC)
    actions: list[ScanAction] = []
    for run in select_candidate_runs(
        runs,
        now=clock,
        lookback_minutes=lookback_minutes,
        max_runs=max_runs,
        expected_workflow_name=expected_workflow_name,
    ):
        run_id = int(run["id"])
        run_attempt_raw = run.get("run_attempt", 1)
        try:
            run_attempt = int(run_attempt_raw)
        except (TypeError, ValueError):
            decision = RecoveryDecision(False, f"invalid run_attempt={run_attempt_raw!r}")
            actions.append(ScanAction(run_id=run_id, decision=decision))
            continue

        jobs = fetch_jobs(run_id)
        decision = decide_queue_starvation_rerun(
            jobs,
            run_attempt=run_attempt,
            max_attempts=max_attempts,
            workflow_name=str(run.get("name") or expected_workflow_name),
            expected_workflow_name=expected_workflow_name,
        )
        if not decision.should_rerun or not apply:
            actions.append(ScanAction(run_id=run_id, decision=decision, applied=False))
            continue
        if rerun_job is None:
            actions.append(
                ScanAction(
                    run_id=run_id,
                    decision=decision,
                    applied=False,
                    apply_error="apply requested but no rerun_job callback",
                )
            )
            continue
        try:
            for job_id in decision.job_ids:
                rerun_job(job_id)
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
            actions.append(
                ScanAction(
                    run_id=run_id,
                    decision=decision,
                    applied=False,
                    apply_error=str(exc),
                )
            )
            continue
        actions.append(ScanAction(run_id=run_id, decision=decision, applied=True))
    return actions


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


def _gh_env(token: str) -> dict[str, str]:
    env = dict(os.environ)
    env["GH_TOKEN"] = token
    return env


def _gh_api(args: Sequence[str], *, token: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", "api", *args],
        check=False,
        capture_output=True,
        text=True,
        env=_gh_env(token),
    )


def _decode_paginated_json_arrays(text: str) -> list[Any]:
    """Decode one or more JSON arrays concatenated by ``gh api --paginate``."""
    stripped = text.strip()
    if not stripped:
        return []
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
        raise RuntimeError("expected JSON array from gh api --paginate")
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        idx = 0
        items: list[Any] = []
        while idx < len(stripped):
            while idx < len(stripped) and stripped[idx].isspace():
                idx += 1
            if idx >= len(stripped):
                break
            chunk, offset = decoder.raw_decode(stripped, idx)
            idx = offset
            if not isinstance(chunk, list):
                raise RuntimeError("expected JSON array pages from gh api --paginate") from None
            items.extend(chunk)
        return items


def _list_workflow_runs(repo: str, *, token: str, per_page: int) -> list[dict[str, Any]]:
    path = (
        f"repos/{repo}/actions/workflows/{CI_WORKFLOW_FILE}/runs"
        f"?status=completed&per_page={per_page}"
    )
    completed = _gh_api(["--paginate", path, "--jq", ".workflow_runs"], token=token)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"gh api failed listing runs for {path}")
    runs = _decode_paginated_json_arrays(completed.stdout)
    return [item for item in runs if isinstance(item, dict)]


def _fetch_run_jobs(repo: str, run_id: int, *, token: str) -> list[dict[str, Any]]:
    path = f"repos/{repo}/actions/runs/{run_id}/jobs?per_page=100"
    completed = _gh_api(
        [
            "--paginate",
            path,
            "--jq",
            ".jobs[] | {id, name, conclusion, status}",
        ],
        token=token,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"gh api failed listing jobs for run {run_id}")
    jobs: list[dict[str, Any]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if isinstance(item, dict):
            jobs.append(item)
    return jobs


def _rerun_job(repo: str, job_id: int, *, token: str) -> None:
    path = f"repos/{repo}/actions/jobs/{job_id}/rerun"
    completed = _gh_api(["--method", "POST", path], token=token)
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(detail or f"gh api failed re-running job {job_id}")


def _run_scan_cli(args: argparse.Namespace) -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("--scan requires GH_TOKEN or GITHUB_TOKEN")

    runs = _list_workflow_runs(args.repo, token=token, per_page=min(100, max(args.max_runs * 2, 30)))
    actions = scan_and_recover(
        runs,
        fetch_jobs=lambda run_id: _fetch_run_jobs(args.repo, run_id, token=token),
        rerun_job=(lambda job_id: _rerun_job(args.repo, job_id, token=token)) if args.apply else None,
        apply=args.apply,
        lookback_minutes=args.lookback_minutes,
        max_runs=args.max_runs,
        max_attempts=args.max_attempts,
        expected_workflow_name=args.workflow_name,
    )

    recovered = 0
    applied = 0
    for action in actions:
        payload = {
            "run_id": action.run_id,
            "should_rerun": action.decision.should_rerun,
            "reason": action.decision.reason,
            "job_ids": list(action.decision.job_ids),
            "applied": action.applied,
            "apply_error": action.apply_error,
        }
        print(json.dumps(payload, sort_keys=True))
        if action.decision.should_rerun:
            recovered += 1
            if args.apply and action.apply_error:
                print(f"::warning::run {action.run_id} recovery failed: {action.apply_error}")
            elif args.apply and action.applied:
                applied += 1
                print(f"::notice::re-ran jobs {action.decision.job_ids} for run {action.run_id}")
            elif not args.apply:
                print(f"::notice::dry-run would re-run jobs {action.decision.job_ids} for run {action.run_id}")

    if args.github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if not out_path:
            raise SystemExit("--github-output requires GITHUB_OUTPUT")
        with open(out_path, "a", encoding="utf-8") as handle:
            handle.write(f"candidate_runs={len(actions)}\n")
            handle.write(f"recoverable={recovered}\n")
            handle.write(f"applied={applied}\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--jobs-json",
        help="Path to a JSON array of workflow jobs, or a literal JSON array string",
    )
    parser.add_argument("--run-attempt", type=int)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--workflow-name", default=CI_WORKFLOW_NAME)
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="Also emit GitHub Actions output lines for $GITHUB_OUTPUT",
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan recent CI workflow runs for queue-starvation signatures",
    )
    parser.add_argument("--repo", help="OWNER/REPO for --scan (required with --scan)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="With --scan, POST job re-runs for matching cancelled tails",
    )
    parser.add_argument(
        "--lookback-minutes",
        type=int,
        default=DEFAULT_LOOKBACK_MINUTES,
        help=f"Only consider CI runs updated in this window (default {DEFAULT_LOOKBACK_MINUTES})",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=DEFAULT_MAX_RUNS,
        help=f"Max candidate runs to evaluate per scan (default {DEFAULT_MAX_RUNS})",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.scan:
        if not args.repo:
            raise SystemExit("--scan requires --repo OWNER/REPO")
        return _run_scan_cli(args)

    if not args.jobs_json or args.run_attempt is None:
        raise SystemExit("single-run mode requires --jobs-json and --run-attempt (or use --scan)")

    jobs = _load_jobs(args.jobs_json)
    decision = decide_queue_starvation_rerun(
        jobs,
        run_attempt=args.run_attempt,
        max_attempts=args.max_attempts,
        workflow_name=args.workflow_name,
    )
    print(decision.to_json())
    if args.github_output:
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
