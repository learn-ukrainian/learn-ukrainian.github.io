#!/usr/bin/env python3
"""Module health dashboard — shows build status across modules.

Reads status/*.json and review/*-review.md for a given level,
outputs a summary table of what passes, what fails, and why.

Usage:
    .venv/bin/python scripts/module_dashboard.py a1
    .venv/bin/python scripts/module_dashboard.py a1 --failing-only
    .venv/bin/python scripts/module_dashboard.py a1 --first 6

Issue: #970 AC5-AC6
"""

import argparse
import contextlib
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"


def _load_curriculum_order(level: str) -> list[str]:
    """Load module slugs in curriculum order from curriculum.yaml."""
    import yaml

    manifest = CURRICULUM_ROOT / "curriculum.yaml"
    if not manifest.exists():
        return []
    data = yaml.safe_load(manifest.read_text())
    modules = data.get("levels", {}).get(level, {}).get("modules", [])
    return [m.strip() for m in modules if isinstance(m, str) and m.strip()]


def _load_status(level: str, slug: str) -> dict | None:
    """Load status JSON for a module."""
    path = CURRICULUM_ROOT / level / "status" / f"{slug}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _extract_review_score(level: str, slug: str) -> str | None:
    """Extract review score from review file."""
    path = CURRICULUM_ROOT / level / "review" / f"{slug}-review.md"
    if not path.exists():
        return None
    text = path.read_text()
    # Look for "Overall Score: X/10" or "**Overall Score:** X/10"
    m = re.search(r"Overall Score[:\s*]*(\d+(?:\.\d+)?)/10", text)
    if m:
        return m.group(1)
    # Look for post-fix score estimate (preferred — reflects actual quality)
    m_post = re.search(r"Estimated Post-Fix Score[:\s*]*(\d+(?:\.\d+)?)/10", text)
    if m_post:
        return m_post.group(1)
    # Look for "Status: PASS" or "Status: FAIL"
    m = re.search(r"\*\*Status:\*\*\s*(PASS|FAIL)", text)
    if m:
        return m.group(1)
    return None


def _count_frictions(level: str, slug: str) -> tuple[int, int]:
    """Count active and resolved frictions. Returns (active, resolved)."""
    path = CURRICULUM_ROOT / level / "orchestration" / slug / "friction.yaml"
    if not path.exists():
        return (0, 0)
    try:
        import yaml

        data = yaml.safe_load(path.read_text())
        frictions = data.get("frictions", []) if data else []
        active = sum(1 for f in frictions if f.get("status") == "active")
        resolved = sum(1 for f in frictions if f.get("status") == "resolved")
        return (active, resolved)
    except Exception:
        return (0, 0)


def _get_blocking_issues(status: dict) -> list[str]:
    """Extract short blocking issue descriptions from status."""
    issues = []
    gates = status.get("gates", {})
    for gate_name, gate_data in gates.items():
        if gate_data.get("status") == "fail":
            msg = gate_data.get("message", "")
            # Truncate long messages
            short = msg[:60] + "..." if len(msg) > 60 else msg
            issues.append(f"{gate_name}: {short}")
    return issues


def dashboard(level: str, failing_only: bool = False, first_n: int = 0) -> int:
    """Print the module health dashboard. Returns exit code."""
    slugs = _load_curriculum_order(level)
    if not slugs:
        print(f"No modules found for level {level}")
        return 1

    if first_n > 0:
        slugs = slugs[:first_n]

    rows = []
    for i, slug in enumerate(slugs, 1):
        status = _load_status(level, slug)
        review_score = _extract_review_score(level, slug)
        active_frictions, resolved_frictions = _count_frictions(level, slug)

        if status:
            audit_status = status.get("overall", {}).get("status", "?").upper()
            blocking = _get_blocking_issues(status)
        else:
            audit_status = "NO DATA"
            blocking = []

        # A module is only shippable if audit PASS + review ≥ 8.0
        review_num = None
        if review_score and review_score not in ("PASS", "FAIL"):
            with contextlib.suppress(ValueError):
                review_num = float(review_score)

        if review_num is not None and review_num < 8.0:
            blocking.append(f"review: {review_num}/10 (need ≥8)")
        elif review_score is None or review_score == "-":
            blocking.append("review: not completed")

        is_shippable = audit_status == "PASS" and not blocking

        if failing_only and is_shippable:
            continue

        rows.append({
            "num": i,
            "slug": slug,
            "audit": audit_status,
            "review": review_score or "-",
            "frictions": f"{active_frictions}a/{resolved_frictions}r" if (active_frictions + resolved_frictions) > 0 else "-",
            "blocking": blocking,
            "shippable": is_shippable,
        })

    if not rows:
        print(f"✅ All {len(slugs)} modules in {level.upper()} are passing.")
        return 0

    # Print table
    print(f"\n{'='*80}")
    print(f"  Module Dashboard — {level.upper()} ({len(rows)}/{len(slugs)} shown)")
    print(f"{'='*80}\n")

    print(f"{'#':>3}  {'Module':<35} {'Ship':>6} {'Review':>7} {'Fric':>6}  Blocking")
    print(f"{'-'*3}  {'-'*35} {'-'*6} {'-'*7} {'-'*6}  {'-'*20}")

    pass_count = 0
    fail_count = 0

    for row in rows:
        if row["shippable"]:
            status_icon = "✅"
            pass_count += 1
        else:
            status_icon = "❌"
            fail_count += 1

        blocking_str = "; ".join(row["blocking"][:2]) if row["blocking"] else ""
        if len(row["blocking"]) > 2:
            blocking_str += f" (+{len(row['blocking'])-2} more)"

        print(f"{row['num']:>3}  {row['slug']:<35} {status_icon:>6} {row['review']:>7} {row['frictions']:>6}  {blocking_str}")

    print(f"\n{'='*80}")
    print(f"  Summary: {pass_count} passing, {fail_count} failing/incomplete")
    print(f"{'='*80}\n")

    return 1 if fail_count > 0 else 0


def main():
    parser = argparse.ArgumentParser(description="Module health dashboard")
    parser.add_argument("level", help="Level to show (e.g., a1, a2, b1)")
    parser.add_argument("--failing-only", action="store_true",
                        help="Show only failing/incomplete modules")
    parser.add_argument("--first", type=int, default=0, metavar="N",
                        help="Show only first N modules")
    args = parser.parse_args()

    sys.exit(dashboard(args.level, args.failing_only, args.first))


if __name__ == "__main__":
    main()
