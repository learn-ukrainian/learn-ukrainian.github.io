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
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from scripts.common import github_client
from scripts.common import github_payload as gp
from scripts.opsec.prepublish import PublishBlocked, publication_cli
from scripts.publish.github import Request, request_run

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


def parse_issue_list(stdout: Any) -> bool:
    """Whether ``gh issue list --json number`` output names at least one issue, or raise.

    The payload goes through the shared strict decoder (:mod:`scripts.common.github_payload`):
    a JSON list without duplicate keys or failure evidence at any depth, and every element an
    object whose ``number`` is an exact positive 32-bit int. Anything else raises
    :class:`~scripts.common.github_payload.UnavailablePayload`: it is not evidence that an issue
    exists, and not evidence that none does.
    """
    issues = gp.parse(stdout, root=list)
    for issue in issues:
        gp.require_int(gp.field(gp.require_object(issue, "issue"), "number", "issue.number"), "issue.number", minimum=1)
    return bool(issues)


_ISSUE_URL = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/issues/[1-9][0-9]*")


def parse_created_issue_url(stdout: Any) -> str:
    """The URL ``gh issue create`` printed, or raise: one line, an issue URL with a positive number."""
    url = gp.require_str(stdout, "issue_create_output").strip()
    if not _ISSUE_URL.fullmatch(url):
        raise gp.UnavailablePayload("issue_create_output")
    return url


def _gh_issue_exists(dec_id: str) -> bool | None:
    """Whether a GH issue already exists for this stale decision.

    ``None`` means the lookup was refused or failed or its payload failed validation: the answer
    is unknown, so the caller must neither claim an issue exists nor create a duplicate. The return
    code is checked before the output is parsed (a refusal is a non-zero result whose stdout is
    error JSON).
    """
    try:
        result = github_client.run(
            ["gh", "issue", "list", "--label", STALE_LABEL, "--search", dec_id, "--json", "number"],
            capture_output=True, text=True, timeout=15,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if type(result.returncode) is not int or result.returncode != 0:
        return None
    try:
        return parse_issue_list(result.stdout)
    except gp.UnavailablePayload:
        return None


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
            return parse_created_issue_url(result.stdout)
    except PublishBlocked as exc:
        print(f"publish_blocked: {exc}", file=sys.stderr)
    except (gp.UnavailablePayload, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


@publication_cli()
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check decision journal for staleness.\nUse during decision audits; writes require --create-issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  .venv/bin/python scripts/audit/check_decisions.py --quiet\nOutputs and exit codes: Report stdout; optional issue and label writes. 0: no stale decisions; 1: stale decisions.\nRelated: #9297",
    )
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
    lookups_unavailable = False
    for dec in stale:
        print(f"  {dec['id']} | expired {dec['expires']} | {dec['title']}")
        if args.create_issues:
            # After one refused or failed lookup the rest would meet the same refusal: ask no more.
            exists = None if lookups_unavailable else _gh_issue_exists(dec["id"])
            if exists is None:
                lookups_unavailable = True
                print("    GH issue lookup unavailable — skipping issue creation (rerun later)")
            elif exists:
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
