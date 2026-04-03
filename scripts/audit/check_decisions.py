#!/usr/bin/env python3
"""Check decision journal for stale/expired decisions.

Reads docs/decisions/decisions.yaml, flags any active decision past its
expiry date, and optionally creates GH issues for them.

Usage:
    .venv/bin/python scripts/check_decisions.py              # full report
    .venv/bin/python scripts/check_decisions.py --quiet       # one-liner for session-setup
    .venv/bin/python scripts/check_decisions.py --create-issues  # create GH issues for stale

Exit codes:
    0 = no stale decisions
    1 = stale decisions found
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DECISIONS_FILE = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"

BUDGET_WARN = 40
BUDGET_MAX = 50
STALE_LABEL = "decision:stale"


def load_decisions() -> list[dict]:
    """Load decisions from YAML file."""
    if not DECISIONS_FILE.exists():
        return []
    data = yaml.safe_load(DECISIONS_FILE.read_text("utf-8"))
    return data.get("decisions", []) if data else []


def find_stale(decisions: list[dict]) -> list[dict]:
    """Find active decisions past their expiry date."""
    today = date.today()
    stale = []
    for dec in decisions:
        if dec.get("status") != "active":
            continue
        expires = dec.get("expires")
        if not expires:
            continue
        try:
            exp_date = date.fromisoformat(str(expires))
        except (ValueError, TypeError):
            continue
        if exp_date <= today:
            stale.append(dec)
    return stale


def check_budget(decisions: list[dict]) -> str | None:
    """Check if decision count is approaching or exceeding budget."""
    active = [d for d in decisions if d.get("status") == "active"]
    count = len(active)
    if count >= BUDGET_MAX:
        return f"Decision budget EXCEEDED: {count}/{BUDGET_MAX} active. Archive expired/superseded decisions."
    if count >= BUDGET_WARN:
        return f"Decision budget warning: {count}/{BUDGET_MAX} active. Consider archiving."
    return None


def _gh_issue_exists(dec_id: str) -> bool:
    """Check if a GH issue already exists for this stale decision."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--label", STALE_LABEL, "--search", dec_id, "--json", "number"],
            capture_output=True, text=True, timeout=15,
        )
        return bool(result.stdout.strip() and result.stdout.strip() != "[]")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _ensure_label_exists() -> None:
    """Create the stale decision label if it doesn't exist."""
    import contextlib
    with contextlib.suppress(subprocess.TimeoutExpired, FileNotFoundError):
        subprocess.run(
            ["gh", "label", "create", STALE_LABEL,
             "--description", "Decision past expiry date — needs re-evaluation",
             "--color", "FBCA04"],
            capture_output=True, timeout=15,
        )


def create_issue(dec: dict) -> str | None:
    """Create a GH issue for a stale decision. Returns issue URL or None."""
    dec_id = dec["id"]
    title = f"{dec_id}: {dec['title']} (expired {dec['expires']})"

    alternatives_text = ""
    for alt in dec.get("alternatives", []):
        alternatives_text += f"- **{alt['option']}** — rejected: {alt['rejected_because']}\n"

    body = f"""## Stale Decision

**ID:** {dec_id}
**Decided:** {dec['date']}
**Expired:** {dec['expires']}
**Scope:** {dec.get('scope', 'unknown')}

## Original Reasoning

{dec.get('reasoning', 'No reasoning recorded.')}

## Evidence

{dec.get('evidence', 'None recorded.')}

## Alternatives Considered

{alternatives_text or 'None recorded.'}

## Action Required

- [ ] **Re-affirm**: extend `expires` date with justification
- [ ] **Supersede**: create new decision, set `superseded_by: {dec_id}`
- [ ] **Archive**: set `status: archived` if no longer relevant
"""

    try:
        result = subprocess.run(
            ["gh", "issue", "create",
             "--title", title,
             "--body", body,
             "--label", STALE_LABEL,
             "--label", "area:docs"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check decision journal for staleness")
    parser.add_argument("--quiet", action="store_true", help="One-liner output for session-setup")
    parser.add_argument("--create-issues", action="store_true", help="Create GH issues for stale decisions")
    args = parser.parse_args()

    decisions = load_decisions()
    if not decisions:
        if not args.quiet:
            print("No decisions found.")
        return 0

    stale = find_stale(decisions)
    budget_msg = check_budget(decisions)

    if args.quiet:
        parts = []
        if stale:
            ids = ", ".join(d["id"] for d in stale)
            parts.append(f"Stale decisions: {ids}")
        if budget_msg:
            parts.append(budget_msg)
        if parts:
            print(" | ".join(parts))
        return 1 if stale else 0

    # Full report
    active = [d for d in decisions if d.get("status") == "active"]
    print(f"Decision journal: {len(active)} active, {len(decisions)} total (budget: {BUDGET_MAX})")

    if budget_msg:
        print(f"  {budget_msg}")

    if not stale:
        print("  No stale decisions.")
        return 0

    print(f"\n  {len(stale)} stale decision(s):\n")
    for dec in stale:
        print(f"  {dec['id']} | expired {dec['expires']} | {dec['title']}")
        if args.create_issues:
            if _gh_issue_exists(dec["id"]):
                print("    GH issue already exists — skipping")
            else:
                _ensure_label_exists()
                url = create_issue(dec)
                if url:
                    print(f"    Created: {url}")
                else:
                    print("    Failed to create GH issue")

    return 1


if __name__ == "__main__":
    sys.exit(main())
