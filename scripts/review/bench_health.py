"""Reviewer bench health check CLI.

Evaluates reviewer seat eligibility for each author family:
anthropic, google, openai, moonshot, zhipu, xai, deepseek.

Inventories the catalog, including explicit-pin reserves; it does not dispatch
or change automatic routing. Prints a table of eligible seats per family and
exits 1 if any family has fewer than 2 eligible reviewers.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, ResolverInputs, evaluate_candidate

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
    """Inventory formal seats, including explicit-pin reserves, by author family.

    Automatic ladders intentionally omit pin-only reserves. Probe each catalog
    candidate with its concrete pin while retaining formal identity, family,
    egress, role and health gates. Near-cap routes are unavailable to this health
    inventory even though an actual explicit pressure override may admit them.
    Returns a mapping of author_family -> list of eligible candidate names;
    inclusion is not authorization to dispatch an explicit-pin reserve.
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
        eligible = []
        for candidate in REVIEW_CANDIDATES.values():
            result = evaluate_candidate(candidate, replace(inputs, pinned_candidate=candidate.name))
            if result.status == "eligible" and result.health != "near_cap":
                eligible.append(result.name)
        family_eligible[family] = eligible

    return family_eligible


def main(argv: list[str] | None = None, *, routing_snapshot: Mapping[str, Any] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory eligible formal reviewers across author families, including explicit-pin reserves.\n"
            "Use for bench health diagnostics; use closeout_cli resolve-reviewer for automatic routing."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.bench_health\n"
            "  .venv/bin/python -m scripts.review.bench_health --profile infra --risk critical\n"
            "Outputs: stdout seat counts; read-only, no files written or reviewers dispatched.\n"
            "Exit codes: 0 = every family has >= 2 eligible seats; 1 = insufficient bench capacity.\n"
            "Related: scripts/config/model_catalog.yaml; scripts.review.closeout_cli resolve-reviewer; #9394."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data-egress-policy",
        default="local_interactive",
        help="Data egress policy context (default: local_interactive). Example: ci",
    )
    parser.add_argument(
        "--risk",
        default="medium",
        choices=("low", "medium", "high", "critical"),
        help="Review risk level to evaluate (default: medium). Example: critical",
    )
    parser.add_argument(
        "--profile",
        default="code",
        choices=("code", "infra"),
        help="Review profile (default: code). Example: infra",
    )
    args = parser.parse_args(argv)

    results = check_bench_health(
        routing_snapshot=routing_snapshot,
        data_egress_policy=args.data_egress_policy,
        review_profile=args.profile,
        risk=args.risk,
    )

    print("Catalog bench inventory includes explicit-pin reserves; automatic routing is unchanged.")
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
