#!/usr/bin/env python3
"""Condensed Monitor API cold start for Cursor (200k context).

Skips /api/rules (AGENTS.md + CLAUDE.md already in Cursor workspace rules).
Prints a compact markdown briefing (~3–5k tokens) for session orientation.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://localhost:8765"
TIMEOUT_S = 5.0


def _get(path: str) -> dict | list | None:
    url = DEFAULT_BASE + path
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"<!-- monitor api unreachable: {exc} -->", file=sys.stderr)
        return None


def _lines_orient(orient: dict) -> list[str]:
    lines: list[str] = []
    git_info = orient.get("git") or {}
    lines.append(
        f"- **git:** `{git_info.get('branch', '?')}` @ `{str(git_info.get('head', ''))[:10]}`"
        f" (ahead {git_info.get('ahead_of_origin', 0)})"
    )
    for commit in (git_info.get("recent_commits") or [])[:3]:
        sha = str(commit.get("sha", ""))[:8]
        subject = str(commit.get("subject", ""))[:100]
        lines.append(f"  - `{sha}` {subject}")

    health = orient.get("health") or {}
    bad = [k for k, v in health.items() if v is False]
    if bad:
        lines.append(f"- **health:** FAIL {', '.join(bad)}")
    else:
        lines.append("- **health:** all green")

    delegate = orient.get("delegate") or {}
    active = delegate.get("active_count", 0)
    lines.append(f"- **delegate:** {active} active")
    for row in (delegate.get("recent") or [])[:3]:
        if row.get("status") == "done":
            continue
        lines.append(
            f"  - {row.get('agent')}/{row.get('task_id')}: {row.get('status')}"
        )

    gov = orient.get("governance") or {}
    stale = gov.get("decisions_stale", 0)
    exp = gov.get("decisions_approaching_expiry", 0)
    if stale or exp:
        lines.append(f"- **governance:** stale={stale} expiring={exp}")

    issues = orient.get("issues") or []
    if issues:
        lines.append("- **open issues (top):**")
        for issue in issues[:5]:
            num = issue.get("number", "?")
            title = str(issue.get("title", ""))[:80]
            lines.append(f"  - #{num} {title}")
    elif orient.get("issues_error"):
        lines.append(f"- **issues:** unavailable ({orient['issues_error']})")

    hints = orient.get("session_hints") or []
    for hint in hints[:3]:
        if isinstance(hint, dict):
            text = f"{hint.get('file', '')}: {hint.get('first_line', '')}"[:120]
        else:
            text = str(hint)[:120]
        lines.append(f"- **hint:** {text}")

    return lines


def main() -> int:
    manifest = _get("/api/state/manifest")
    orient = _get("/api/orient")

    print("# Cursor cold start\n")
    if manifest:
        rules_hash = (manifest.get("rules") or {}).get("hash", "")[:12]
        print(f"_manifest rules={rules_hash}… (rules skipped — already in workspace)_\n")

    if orient:
        print("## Live state\n")
        for line in _lines_orient(orient):
            print(line)
        print()
    else:
        print("## Live state\n")
        print("- Monitor API down — run `git status --short --branch`\n")

    print("## Context budget (200k)\n")
    print("- Workspace rules: ~50k (AGENTS + CLAUDE, do not re-read)")
    print("- This briefing: ~3–5k")
    print("- Task budget: ~140k; fetch scoped endpoints only when needed")
    print("- Full protocol: `agents_extensions/cursor/rules/cold-start.md`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
