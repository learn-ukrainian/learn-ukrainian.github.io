#!/usr/bin/env python3
"""Check decision journal for stale/expired decisions.

Reads docs/decisions/decisions.yaml, flags any active decision past its
expiry date, and optionally creates GH issues for them. Also reads
scripts/config/stack_pins.yaml and reports rows whose review_by is before
today as overdue reviews beside expired decisions. An overdue review does
not invalidate the accepted pin.

Usage:
    .venv/bin/python scripts/check_decisions.py              # full report
    .venv/bin/python scripts/check_decisions.py --quiet       # one-liner for session-setup
    .venv/bin/python scripts/check_decisions.py --create-issues  # create GH issues for stale

Exit codes:
    0 = no stale decisions and no overdue stack reviews
    1 = stale decisions, overdue stack reviews, or an unreadable pin file
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.common import github_client
from scripts.opsec.prepublish import PublishBlocked, publication_cli
from scripts.publish.github import Request, request_run

DECISIONS_FILE = PROJECT_ROOT / "docs" / "decisions" / "decisions.yaml"
STACK_PINS_FILE = PROJECT_ROOT / "scripts" / "config" / "stack_pins.yaml"

BUDGET_WARN = 40
BUDGET_MAX = 50
STALE_LABEL = "decision:stale"
PIN_OWNERS = frozenset({"DevOps", "Infra", "Monitor"})
_PIN_TEXT_FIELDS = ("pinned", "source", "note")


class StackPinsError(ValueError):
    """stack_pins.yaml failed to load or a row failed validation."""


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


def _pin_name(row: dict) -> str:
    name = row.get("name")
    if isinstance(name, str) and name.strip():
        return name
    return "?"


def _coerce_review_by(value: object, name: str) -> date:
    """Return a calendar date, or raise when review_by is not YYYY-MM-DD."""
    if isinstance(value, datetime):
        raise StackPinsError(f"stack pin {name} has a malformed review_by")
    if isinstance(value, date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise StackPinsError(f"stack pin {name} has a malformed review_by") from exc
    raise StackPinsError(f"stack pin {name} has a malformed review_by")


def _review_by_text(value: object) -> str:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def load_stack_pins(path: Path | None = None) -> list[dict]:
    """Load pin rows. Missing owner, a bad date, or a duplicate name is an error."""
    pin_path = STACK_PINS_FILE if path is None else path
    if not pin_path.is_file():
        raise StackPinsError(f"missing stack pins file: {pin_path}")
    data = yaml.safe_load(pin_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("pins"), list):
        raise StackPinsError("stack_pins.yaml must contain a pins list")
    seen: set[str] = set()
    rows: list[dict] = []
    for row in data["pins"]:
        if not isinstance(row, dict):
            raise StackPinsError("stack pin row must be a mapping")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise StackPinsError("stack pin row is missing a name")
        if name in seen:
            raise StackPinsError(f"duplicate stack pin name: {name}")
        seen.add(name)
        owner = row.get("owner")
        if not isinstance(owner, str) or not owner.strip():
            raise StackPinsError(f"stack pin {name} is missing an owner")
        if owner not in PIN_OWNERS:
            raise StackPinsError(f"stack pin {name} has owner {owner!r}; expected one of DevOps, Infra, Monitor")
        _coerce_review_by(row.get("review_by"), name)
        for field in _PIN_TEXT_FIELDS:
            field_value = row.get(field)
            if not isinstance(field_value, str) or not field_value.strip():
                raise StackPinsError(f"stack pin {name} is missing {field}")
        rows.append(row)
    return rows


def find_overdue_reviews(rows: list[dict], *, today: date | None = None) -> list[dict]:
    """Rows whose review_by is before today. A date of today is not overdue."""
    current = date.today() if today is None else today
    overdue: list[dict] = []
    for row in rows:
        review_date = _coerce_review_by(row.get("review_by"), _pin_name(row))
        if review_date < current:
            overdue.append(row)
    return overdue


def _gh_issue_exists(dec_id: str) -> bool:
    """Check if a GH issue already exists for this stale decision."""
    try:
        result = github_client.run(
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
        request_run(
            Request(
                "label-create",
                name=STALE_LABEL,
                description="Decision past expiry date — needs re-evaluation",
                color="FBCA04",
            ),
            capture_output=True,
            timeout=15,
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
        result = request_run(
            Request("issue-create", title=title, body=body, labels=[STALE_LABEL, "area:docs"]),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except PublishBlocked as exc:
        print(f"publish_blocked: {exc}", file=sys.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


@publication_cli()
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check decision journal for staleness.\nUse during decision audits; writes require --create-issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  .venv/bin/python scripts/audit/check_decisions.py --quiet\n"
            "Outputs and exit codes: Report stdout; optional issue and label writes. "
            "0: no stale decisions and no overdue stack reviews; "
            "1: stale decisions, overdue stack reviews, or an unreadable pin file.\n"
            "Related: #9297"
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="One-liner output for session-setup")
    parser.add_argument("--create-issues", action="store_true", help="Create GH issues for stale decisions")
    args = parser.parse_args()

    decisions = load_decisions()
    try:
        overdue = find_overdue_reviews(load_stack_pins())
        pins_error = None
    except StackPinsError as exc:
        overdue = []
        pins_error = str(exc)

    stale = find_stale(decisions) if decisions else []
    budget_msg = check_budget(decisions) if decisions else None
    attention = bool(stale or overdue or pins_error)

    if args.quiet:
        parts = []
        if stale:
            ids = ", ".join(d["id"] for d in stale)
            parts.append(f"Stale decisions: {ids}")
        if budget_msg:
            parts.append(budget_msg)
        if pins_error:
            parts.append(f"Stack pins: {pins_error}")
        elif overdue:
            names = ", ".join(str(row["name"]) for row in overdue)
            parts.append(f"Overdue stack reviews: {names}")
        if parts:
            print(" | ".join(parts))
        return 1 if attention else 0

    # Full report
    if not decisions:
        print("No decisions found.")
    else:
        active = [d for d in decisions if d.get("status") == "active"]
        print(f"Decision journal: {len(active)} active, {len(decisions)} total (budget: {BUDGET_MAX})")
        if budget_msg:
            print(f"  {budget_msg}")
        if not stale:
            print("  No stale decisions.")
        else:
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

    if pins_error:
        print(f"\n  Stack pins: {pins_error}")
    elif not overdue:
        print("  No overdue stack reviews.")
    else:
        print(f"\n  Overdue stack reviews ({len(overdue)}):\n")
        for row in overdue:
            print(f"  {row['name']} | review_by {_review_by_text(row.get('review_by'))} | {row.get('note', '')}")

    return 1 if attention else 0


if __name__ == "__main__":
    sys.exit(main())
