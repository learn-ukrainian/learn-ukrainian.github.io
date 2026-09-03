#!/usr/bin/env python3
"""CI Gate aggregation: one required-job tuple, evaluated fail-closed.

``CI Gate`` is the sole required check. It succeeds only when every job in
``REQUIRED_JOBS`` reports success; missing, failed, cancelled, or skipped all
count as a gate failure. There is no per-event tier (2026-09-03 simple-CI
cutover): the same jobs run, and the same tuple is required, on every event
this workflow triggers on (pull_request, merge_group, push, schedule,
workflow_dispatch).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping

# The one canonical inventory of the workflow's ``ci-gate.needs``: every job
# whose result the gate evaluates, on every event. Tests compare ci.yml
# against this tuple instead of restating it, so a legitimate needs change is
# a one-file edit here, not a test-pin cascade.
REQUIRED_JOBS: tuple[str, ...] = (
    "ruff",
    "secret-scan",
    "pytest-fastlane",
    "pytest",
    "contracts",
    "frontend",
)

GATE_NEEDS_JOBS: frozenset[str] = frozenset(REQUIRED_JOBS)

SUCCESS = "success"


def evaluate_gate(event_name: str, results: Mapping[str, str]) -> list[str]:
    """Return human-readable failure reasons (empty ⇒ gate green).

    ``results`` maps job id → GitHub ``needs.<job>.result`` string. Missing
    keys for required jobs are failures (not silent success).
    """
    failures: list[str] = []
    for job in REQUIRED_JOBS:
        if job not in results:
            failures.append(f"{job}: missing (required for {event_name})")
            continue
        outcome = results[job]
        if outcome != SUCCESS:
            failures.append(f"{job}: {outcome} (required for {event_name})")
    return failures


def parse_results(raw: str) -> dict[str, str]:
    """Parse ``job=result,job=result`` from the workflow env."""
    results: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"malformed result entry (expected job=result): {item!r}")
        job, _, outcome = item.partition("=")
        job, outcome = job.strip(), outcome.strip()
        if not job or not outcome:
            raise ValueError(f"malformed result entry: {item!r}")
        results[job] = outcome
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--event",
        required=True,
        help="github.event_name (pull_request|merge_group|push|schedule|workflow_dispatch)",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Comma-separated job=result pairs from needs.*.result",
    )
    args = parser.parse_args(argv)

    try:
        results = parse_results(args.results)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    failures = evaluate_gate(args.event, results)
    print(f"event={args.event}")
    print(f"required={','.join(REQUIRED_JOBS)}")
    print(f"results={args.results}")
    if failures:
        for reason in failures:
            print(f"::error::CI Gate fail-closed: {reason}", file=sys.stderr)
        return 1
    print("CI Gate: every required dependency succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
