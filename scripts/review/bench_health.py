"""Reviewer bench health check CLI.

Evaluates reviewer seat eligibility for each author family:
anthropic, google, openai, moonshot, zhipu, xai, deepseek.

Prints a table of eligible seats per family and exits 1 if any family
has fewer than 2 eligible reviewers.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer

AUTHOR_FAMILIES = (
    "anthropic",
    "google",
    "openai",
    "moonshot",
    "zhipu",
    "xai",
    "deepseek",
)

MIN_ELIGIBLE_SEATS = 2


def check_bench_health(
    routing_snapshot: Mapping[str, Any] | None = None,
    *,
    data_egress_policy: str | None = "local_interactive",
    review_profile: str = "code",
    risk: str = "medium",
) -> dict[str, list[str]]:
    """Evaluate eligible seats per author family given a routing snapshot.

    Returns a mapping of author_family -> list of eligible candidate names.
    """
    if routing_snapshot is None:
        try:
            from scripts.api.state_router import compute_routing_budget

            routing_snapshot = compute_routing_budget()
        except Exception:
            routing_snapshot = {}

    family_eligible: dict[str, list[str]] = {}
    for family in AUTHOR_FAMILIES:
        inputs = ResolverInputs(
            author_model=family,
            author_family=family,
            review_profile=review_profile,
            risk=risk,
            data_egress_policy=data_egress_policy,
            routing_snapshot=routing_snapshot,
        )
        resolution = resolve_reviewer(inputs)
        eligible = [
            item.name
            for item in resolution.trace
            if item.status in {"eligible", "selected"}
        ]
        family_eligible[family] = eligible

    return family_eligible


def main(argv: list[str] | None = None, *, routing_snapshot: Mapping[str, Any] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check reviewer bench health across author families.")
    parser.add_argument(
        "--data-egress-policy",
        default="local_interactive",
        help="Data egress policy context (default: local_interactive)",
    )
    parser.add_argument(
        "--risk",
        default="medium",
        help="Review risk level to evaluate (default: medium)",
    )
    parser.add_argument(
        "--profile",
        default="code",
        help="Review profile (default: code)",
    )
    args = parser.parse_args(argv)

    results = check_bench_health(
        routing_snapshot=routing_snapshot,
        data_egress_policy=args.data_egress_policy,
        review_profile=args.profile,
        risk=args.risk,
    )

    print(f"{'Author Family':<15} | {'Count':<5} | {'Eligible Seats'}")
    print("-" * 60)

    failing = False
    for family in AUTHOR_FAMILIES:
        seats = results.get(family, [])
        count = len(seats)
        seats_str = ", ".join(seats) if seats else "NONE"
        status_flag = "" if count >= MIN_ELIGIBLE_SEATS else " [FAIL < 2]"
        if count < MIN_ELIGIBLE_SEATS:
            failing = True
        print(f"{family:<15} | {count:<5} | {seats_str}{status_flag}")

    print("-" * 60)
    if failing:
        print("BENCH HEALTH FAIL: At least one author family has < 2 eligible reviewers.", file=sys.stderr)
        return 1

    print("BENCH HEALTH PASS: All author families have >= 2 eligible reviewers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
