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

# A push to main also owns the duration publish. Keeping it in the push gate
# set makes a missing validating-run artifact fail on the visible push check.
PUSH_REQUIRED: tuple[str, ...] = (*FULL_REQUIRED, "pytest-duration-publish")

FULL_TIER_EVENTS: frozenset[str] = frozenset(
    {"merge_group", "push", "schedule", "workflow_dispatch"}
)

SUCCESS = "success"
CLASS_DOCS_SKILLS = "docs_skills"
CLASS_FULL = "full"
CLASS_MQ_VALIDATED = "mq_validated"
KNOWN_CLASSES = frozenset({CLASS_DOCS_SKILLS, CLASS_FULL, CLASS_MQ_VALIDATED})


def required_jobs(event_name: str, landing_class: str = CLASS_FULL) -> tuple[str, ...]:
    """Return the job ids CI Gate must see as success for this event."""
    if event_name == "pull_request":
        return LIGHT_REQUIRED
    if event_name == "push" and landing_class != CLASS_DOCS_SKILLS:
        return PUSH_REQUIRED
    if event_name in FULL_TIER_EVENTS:
        return FULL_REQUIRED
    # Unknown events fail closed as full tier — never treat as light.
    return FULL_REQUIRED


def evaluate_gate(
    event_name: str,
    results: Mapping[str, str],
    *,
    landing_class: str = CLASS_FULL,
    python_noop: bool = False,
    validating_run_id: str = "",
) -> list[str]:
    """Return human-readable failure reasons (empty ⇒ gate green).

    ``results`` maps job id → GitHub ``needs.<job>.result`` string.
    Missing keys for required jobs are failures (not silent success).
    """
    failures: list[str] = []
    if landing_class not in KNOWN_CLASSES:
        failures.append(f"class: {landing_class} (unknown landing class)")
    if landing_class == CLASS_FULL and python_noop:
        failures.append("class=full: python no-op is not allowed")
    if landing_class == CLASS_MQ_VALIDATED:
        if not validating_run_id.strip():
            failures.append("class=mq_validated: validating run proof is missing")
        if not python_noop:
            failures.append("class=mq_validated: python jobs did not take the no-op path")

    required = required_jobs(event_name, landing_class)
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
        help="github.event_name (pull_request|merge_group|push|schedule|workflow_dispatch)",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Comma-separated job=result pairs from needs.*.result",
    )
    parser.add_argument(
        "--class",
        dest="landing_class",
        default=CLASS_FULL,
        choices=sorted(KNOWN_CLASSES),
        help="landing-class output",
    )
    parser.add_argument(
        "--python-noop",
        default="false",
        choices=("true", "false"),
        help="whether the Python matrix used its intentional no-op success path",
    )
    parser.add_argument(
        "--validating-run-id",
        default="",
        help="run id proving mq_validated (required for that class)",
    )
    args = parser.parse_args(argv)

    try:
        results = parse_results(args.results)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    failures = evaluate_gate(
        args.event,
        results,
        landing_class=args.landing_class,
        python_noop=args.python_noop == "true",
        validating_run_id=args.validating_run_id,
    )
    print(f"event={args.event}")
    print(f"class={args.landing_class}")
    print(f"required={','.join(required_jobs(args.event, args.landing_class))}")
    print(f"results={args.results}")
    if failures:
        for reason in failures:
            print(f"::error::CI Gate fail-closed: {reason}", file=sys.stderr)
        return 1
    print("CI Gate: every required dependency succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
