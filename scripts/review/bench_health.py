"""Reviewer bench health check CLI.

Evaluates reviewer seat eligibility for each author family:
anthropic, google, openai, moonshot, zhipu, xai, deepseek.

Counts only seats eligible for automatic routing; it does not dispatch
or change routing policy. Prints a table of eligible seats per family and
exits 1 if any family falls below its required minimum. Two seats are required
except for explicitly accepted single-seat benches at high/critical risk.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_REPO_ROOT = str(Path(__file__).resolve().parents[2])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from scripts.review.reviewer_resolver import REVIEW_CANDIDATES, REVIEW_LADDERS, ResolverInputs, evaluate_candidate

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

# #9423 AC-02 accepts Sol alone for Anthropic authors at high/critical risk.
# #9538 / #9583 limit these reviews to Sol and Opus, leaving the symmetric
# OpenAI-author bench with Opus alone. Only these family/risk pairs accept one
# automatic seat; zero seats still fails and resolver eligibility never changes.
ACCEPTED_SINGLE_SEAT_BENCHES = frozenset(
    {
        ("anthropic", "high"),
        ("anthropic", "critical"),
        ("openai", "high"),
        ("openai", "critical"),
    }
)


def check_bench_health(
    routing_snapshot: Mapping[str, Any] | None = None,
    *,
    data_egress_policy: str | None = "local_interactive",
    review_profile: str = "code",
    risk: str = "medium",
) -> dict[str, list[str]]:
    """Return automatic eligible candidate names by author family."""
    eligible, _ = _bench_inventory(
        routing_snapshot,
        data_egress_policy=data_egress_policy,
        review_profile=review_profile,
        risk=risk,
    )
    return eligible


def _bench_inventory(
    routing_snapshot: Mapping[str, Any] | None,
    *,
    data_egress_policy: str | None,
    review_profile: str,
    risk: str,
) -> tuple[dict[str, list[str]], dict[str, dict[str, str]]]:
    """Evaluate automatic eligibility and retain catalog exclusion reasons.

    No candidate is pinned: retired routes, quota pressure and all other
    resolver gates remain binding. Eligible catalog reserves outside the
    active risk ladder are displayed as excluded from the automatic count.
    """
    if routing_snapshot is None:
        try:
            from scripts.api.state_router import compute_routing_budget

            routing_snapshot = compute_routing_budget()
        except Exception:
            routing_snapshot = {}

    family_eligible: dict[str, list[str]] = {}
    family_excluded: dict[str, dict[str, str]] = {}
    automatic_names = {candidate.name for rung in REVIEW_LADDERS[risk] for candidate in rung}
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
        excluded = {}
        for candidate in REVIEW_CANDIDATES.values():
            result = evaluate_candidate(candidate, inputs)
            if result.status != "eligible":
                excluded[result.name] = result.reason or result.status
            elif result.name not in automatic_names:
                excluded[result.name] = f"not on automatic {risk} ladder (catalog reserve)"
            else:
                eligible.append(result.name)
        family_eligible[family] = eligible
        family_excluded[family] = excluded

    return family_eligible, family_excluded


def main(argv: list[str] | None = None, *, routing_snapshot: Mapping[str, Any] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count formal reviewers eligible for automatic routing across author families.\n"
            "Use for bench health diagnostics; use closeout_cli resolve-reviewer for automatic routing."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.bench_health\n"
            "  .venv/bin/python -m scripts.review.bench_health --profile infra --risk critical\n"
            "Outputs: stdout automatic seat counts and expected single-seat labels;\n"
            "stderr JSON shortfall findings with exclusion reasons.\n"
            "Read-only, no files written or reviewers dispatched.\n"
            "Exit codes: 0 = every family meets its required minimum; 1 = insufficient bench capacity.\n"
            "Minimum: 2 eligible seats, except Anthropic/OpenAI authors at high/critical risk\n"
            "accept 1 eligible seat (#9423, #9538, #9583). Zero seats always fails.\n"
            "Related: scripts/config/model_catalog.yaml; scripts.review.closeout_cli resolve-reviewer; #9394; #9423."
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

    results, excluded = _bench_inventory(
        routing_snapshot=routing_snapshot,
        data_egress_policy=args.data_egress_policy,
        review_profile=args.profile,
        risk=args.risk,
    )

    print("Automatic bench inventory; explicit-pin reserves never count toward the minimum.")
    print(f"{'Author Family':<15} | {'Count':<5} | {'Eligible Seats'}")
    print("-" * 60)

    failing = False
    for family in AUTHOR_FAMILIES:
        seats = results.get(family, [])
        count = len(seats)
        seats_str = ", ".join(seats) if seats else "NONE"
        minimum = 1 if (family, args.risk) in ACCEPTED_SINGLE_SEAT_BENCHES else MIN_ELIGIBLE_SEATS
        status_flag = ""
        if count < minimum:
            status_flag = f" [FAIL < {minimum}]"
            failing = True
            print(
                json.dumps(
                    {
                        "type": "insufficient_bench_capacity",
                        "author_family": family,
                        "minimum": minimum,
                        "counted_seats": seats,
                        "excluded_seats": excluded[family],
                    }
                ),
                file=sys.stderr,
            )
        elif count == 1:
            status_flag = " [EXPECTED single seat]"
        print(f"{family:<15} | {count:<5} | {seats_str}{status_flag}")

    print("-" * 60)
    if failing:
        print("BENCH HEALTH FAIL: At least one author family is below its required reviewer minimum.", file=sys.stderr)
        return 1

    print("BENCH HEALTH PASS: All author families meet their required reviewer minimum.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
