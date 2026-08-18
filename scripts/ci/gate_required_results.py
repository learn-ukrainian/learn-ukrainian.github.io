#!/usr/bin/env python3
"""Event-aware CI Gate aggregation for the two-tier merge-queue cutover.

``CI Gate`` is the sole required check context. It must report on both
``pull_request`` and ``merge_group`` and fail closed when any dependency that
is required *for that event* is failed, cancelled, skipped, or missing.

Skipped ≠ success for a required dependency. Jobs that are intentionally out
of the pull_request tier may be skipped on PRs; the same skip on
``merge_group`` (or push / workflow_dispatch) is a gate failure.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping

# Light PR tier: early signal without the four-shard suite.
LIGHT_REQUIRED: tuple[str, ...] = (
    "ruff",
    "pytest-fastlane",
    "contracts",
    "frontend",
)

# Merge-queue / main / dispatch tier: strictly a superset of the light tier.
FULL_REQUIRED: tuple[str, ...] = (
    *LIGHT_REQUIRED,
    "pytest-plan",
    "python",
    "coverage-floor",
)

FULL_TIER_EVENTS: frozenset[str] = frozenset(
    {"merge_group", "push", "workflow_dispatch"}
)

SUCCESS = "success"


def required_jobs(event_name: str) -> tuple[str, ...]:
    """Return the job ids CI Gate must see as success for this event."""
    if event_name == "pull_request":
        return LIGHT_REQUIRED
    if event_name in FULL_TIER_EVENTS:
        return FULL_REQUIRED
    # Unknown events fail closed as full tier — never treat as light.
    return FULL_REQUIRED


def evaluate_gate(
    event_name: str,
    results: Mapping[str, str],
) -> list[str]:
    """Return human-readable failure reasons (empty ⇒ gate green).

    ``results`` maps job id → GitHub ``needs.<job>.result`` string.
    Missing keys for required jobs are failures (not silent success).
    """
    failures: list[str] = []
    required = required_jobs(event_name)
    for job in required:
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
        help="github.event_name (pull_request|merge_group|push|workflow_dispatch)",
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
    print(f"required={','.join(required_jobs(args.event))}")
    print(f"results={args.results}")
    if failures:
        for reason in failures:
            print(f"::error::CI Gate fail-closed: {reason}", file=sys.stderr)
        return 1
    print("CI Gate: every required dependency succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
