#!/usr/bin/env python3
"""Lint PR commits for the required ``X-Agent`` trailer.

Every commit on a non-main feature branch (i.e. a branch destined for a PR)
must declare which agent authored it via an ``X-Agent: <agent>/<task-id>``
trailer. Without this we cannot distinguish Codex / Gemini / Claude-headless
/ orchestrator-inline commits — the ``git committer`` field is always the
user's local config and is identical across agents.

Use when
========
- CI pre-merge gate on PRs.
- Pre-push hook on dispatch worktrees.

Do NOT use to retroactively rewrite history of already-merged commits — the
trailer is for forward-only enforcement.

Examples
========

    # Check every commit since branching from main
    .venv/bin/python scripts/audit/lint_agent_trailer.py

    # Check a specific range
    .venv/bin/python scripts/audit/lint_agent_trailer.py origin/main..HEAD

    # Check a single commit
    .venv/bin/python scripts/audit/lint_agent_trailer.py HEAD~1..HEAD

Outputs
=======
- stdout: per-commit verdict (PASS / FAIL with reason) and a final tally.
- exit 0 if every non-skipped commit has a valid ``X-Agent`` trailer.
- exit 1 if any commit is missing the trailer.

Skipped (exit 0 regardless)
===========================
- merge commits (``git log --no-merges`` is applied)
- dependabot branches (committer email ends with ``@dependabot``)
- the initial commit on main (no prior trailer expected)

Trailer format
==============
``X-Agent: <agent>/<task-id>``

Where ``agent`` ∈ {``claude-inline``, ``claude``, ``codex``, ``gemini``,
``agy-inline``, ``agy``, ``grok``, ``grok-build``, ``grok-hermes``,
``deepseek-v4-pro``, ``cursor``, ``dependabot``} and ``task-id`` is the
dispatch task identifier or the ``inline`` literal for orchestrator commits.
``grok-build`` is a permanent alias of the native ``grok`` seat (historical
trailers must keep validating). Examples::

    X-Agent: claude-inline/orchestrator
    X-Agent: codex/1879-fix-ci-and-wikipedia
    X-Agent: claude/1657-adr-010
    X-Agent: gemini/1787-15-handoff-verifier

Related
=======
- EPIC: parent of this lint (TBD — orchestrator-visibility follow-up)
- Sibling guardrails: scripts/audit/lint_dispatch_brief.py (#1788),
  scripts/audit/lint_anti_menu.py (#1789), scripts/audit/lint_session_state.py (#1792)
- Original ask: 2026-05-11 session — "can we make sure we know which agent is committing?"
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

_TRAILER_RE = re.compile(
    r"^X-Agent:\s+(?P<agent>claude-inline|claude|codex|gemini|agy-inline|agy|grok|grok-build|grok-hermes|deepseek-v4-pro|cursor|dependabot)/(?P<task>[A-Za-z0-9._-]+)\s*$",
    re.MULTILINE,
)


def _git(*args: str) -> str:
    """Run a git command and return stdout, raising on non-zero exit."""
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.PIPE
    ).strip()


def _commits_in_range(rev_range: str) -> list[str]:
    """Return commit SHAs (newest first) in the range, excluding merges."""
    raw = _git("log", "--no-merges", "--format=%H", rev_range)
    return raw.splitlines() if raw else []


def _commit_meta(sha: str) -> tuple[str, str, str, str]:
    """Return (committer_email, author_email, author_name, subject)."""
    raw = _git("log", "-1", "--format=%ce%n%ae%n%an%n%s", sha)
    parts = raw.splitlines()
    while len(parts) < 4:
        parts.append("")
    return parts[0], parts[1], parts[2], parts[3]


def _commit_body(sha: str) -> str:
    return _git("log", "-1", "--format=%B", sha)


def _looks_like_dependabot(committer_email: str, author_email: str, author_name: str, subject: str) -> bool:
    """Recognize dependabot commits even after squash-merge rebases them through the user."""
    if "dependabot" in (committer_email + author_email + author_name).lower():
        return True
    if committer_email.endswith("@noreply.github.com"):
        return True
    # Squash-merged dependabot commit conventions
    return subject.startswith(("deps:", "Bump ", "build(deps"))


def _check_commit(sha: str) -> tuple[str, str]:
    """Return (verdict, reason). verdict ∈ {'PASS', 'SKIP', 'FAIL'}."""
    committer_email, author_email, author_name, subject = _commit_meta(sha)

    if _looks_like_dependabot(committer_email, author_email, author_name, subject):
        return "SKIP", f'dependabot/bot ("{subject[:50]}")'

    body = _commit_body(sha)
    match = _TRAILER_RE.search(body)
    if match is None:
        return "FAIL", f'missing X-Agent trailer in commit "{subject[:60]}"'

    return "PASS", f"X-Agent: {match.group('agent')}/{match.group('task')}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint PR commits for required X-Agent trailer.\n"
        "Catches commits where the authoring agent isn't recorded — needed because\n"
        "git committer field is identical across all locally-dispatched agents.",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "rev_range",
        nargs="?",
        default="origin/main..HEAD",
        help='Git rev range to check (default: "origin/main..HEAD"). '
        'Examples: "origin/main..HEAD", "HEAD~3..HEAD", "abc123..def456".',
    )
    args = parser.parse_args(argv)

    try:
        shas = _commits_in_range(args.rev_range)
    except subprocess.CalledProcessError as exc:
        print(f"git log failed: {exc.stderr or exc}", file=sys.stderr)
        return 2

    if not shas:
        print(f"No commits in range {args.rev_range!r} (nothing to check).")
        return 0

    fails = 0
    print(f"Checking {len(shas)} commit(s) in {args.rev_range}:\n")
    for sha in shas:
        short = sha[:10]
        verdict, reason = _check_commit(sha)
        if verdict == "FAIL":
            fails += 1
            print(f"  {short}  FAIL  {reason}")
        else:
            print(f"  {short}  {verdict}  {reason}")

    print()
    if fails:
        print(
            f"❌ {fails}/{len(shas)} commit(s) missing X-Agent trailer.\n"
            "   Add a trailer to each failing commit. Example for an orchestrator inline commit:\n"
            "       git commit --amend --trailer 'X-Agent: claude-inline/orchestrator'\n"
            "   For dispatched-agent commits, the dispatch brief should specify the trailer.\n"
            "   See AGENTS.md rule #11 / GEMINI.md / agents_extensions/shared/rules/delegate-must-use-worktree.md."
        )
        return 1

    print(f"✅ All {len(shas)} non-skipped commit(s) carry an X-Agent trailer.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
