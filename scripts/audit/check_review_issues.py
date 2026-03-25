#!/usr/bin/env python3
"""Check open review-result GH issues and close those whose modules now pass audit.

For each open issue with a title matching "Review: {slug}-review-...":
1. Extract the module slug from the title
2. Find the module's markdown file
3. Run audit_module.py to check all gates
4. If all gates pass → close the issue with a comment citing results
5. If any gate fails → leave open, add a comment with current status

Usage:
    .venv/bin/python scripts/check_review_issues.py [--close] [--dry-run]

Flags:
    --close    Actually close passing issues (default: report only)
    --dry-run  Show what would happen without querying audit or GH
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CURRICULUM_BASE = PROJECT_ROOT / "curriculum" / "l2-uk-en"
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")


def _run_gh(args: list[str], check: bool = True) -> str:
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True, text=True, check=check,
        cwd=str(PROJECT_ROOT),
    )
    return result.stdout.strip()


def _get_open_review_issues() -> list[dict]:
    """Fetch open issues with 'Review:' in the title."""
    raw = _run_gh([
        "issue", "list",
        "--state", "open",
        "--search", "Review: in:title",
        "--json", "number,title,labels",
        "--limit", "50",
    ])
    if not raw:
        return []
    return json.loads(raw)


def _extract_slug_and_level(title: str) -> tuple[str, str] | None:
    """Extract module slug and level from issue title.

    Expected format: "Review: {slug}-review-result ..." or
    "Review: {slug} — review findings"
    """
    # Try: "Review: slug-review-result"
    m = re.search(r"Review:\s+(.+?)-review-result", title)
    if m:
        slug = m.group(1).strip()
    else:
        # Try: "Review: slug —" or "Review: slug -"
        m = re.search(r"Review:\s+(.+?)(?:\s+[—–-]|\s*$)", title)
        if not m:
            return None
        slug = m.group(1).strip()

    # Find the level by searching for the slug in curriculum
    for level_dir in CURRICULUM_BASE.iterdir():
        if not level_dir.is_dir():
            continue
        md_path = level_dir / f"{slug}.md"
        if md_path.exists():
            return slug, level_dir.name
        # Also check orchestration dir as indicator
        orch_dir = level_dir / "orchestration" / slug
        if orch_dir.is_dir():
            return slug, level_dir.name

    return None


def _find_module_md(slug: str, level: str) -> Path | None:
    """Find the module's markdown file."""
    md_path = CURRICULUM_BASE / level / f"{slug}.md"
    if md_path.exists():
        return md_path
    return None


def _run_audit(md_path: Path) -> tuple[bool, str]:
    """Run audit_module.py and return (all_passed, output_text)."""
    result = subprocess.run(
        [VENV_PYTHON, str(PROJECT_ROOT / "scripts" / "audit_module.py"), str(md_path)],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )
    output = result.stdout + result.stderr
    # Check for overall pass — audit_module prints "PASS" or all gates show ✅
    all_passed = result.returncode == 0 and "FAIL" not in output.upper().split("GATE")[-1:]
    # More reliable: check if any ❌ appears
    if "❌" in output:
        all_passed = False
    if "✅" in output and "❌" not in output:
        all_passed = True
    return all_passed, output


def _close_issue(number: int, comment: str) -> None:
    """Close a GH issue with a comment."""
    _run_gh(["issue", "comment", str(number), "--body", comment])
    _run_gh(["issue", "close", str(number)])


def _comment_issue(number: int, comment: str) -> None:
    """Add a comment to a GH issue."""
    _run_gh(["issue", "comment", str(number), "--body", comment])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--close", action="store_true",
                        help="Actually close passing issues")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would happen without running audit")
    args = parser.parse_args()

    issues = _get_open_review_issues()
    if not issues:
        print("No open review issues found.")
        return

    print(f"Found {len(issues)} open review issue(s)\n")

    for issue in issues:
        number = issue["number"]
        title = issue["title"]
        print(f"#{number}: {title}")

        parsed = _extract_slug_and_level(title)
        if not parsed:
            print("  ⚠ Could not extract slug from title — skipping\n")
            continue

        slug, level = parsed
        print(f"  Module: {level}/{slug}")

        if args.dry_run:
            print(f"  [DRY-RUN] Would audit {level}/{slug}.md\n")
            continue

        md_path = _find_module_md(slug, level)
        if not md_path:
            print("  ⚠ Module file not found — skipping\n")
            continue

        all_passed, audit_output = _run_audit(md_path)

        if all_passed:
            print("  ✅ All audit gates PASS")
            if args.close:
                comment = (
                    f"**Auto-checked by `check_review_issues.py`**\n\n"
                    f"Module `{level}/{slug}` now passes all audit gates. Closing.\n\n"
                    f"```\n{audit_output[:2000]}\n```"
                )
                _close_issue(number, comment)
                print(f"  → Closed #{number}")
            else:
                print("  → Would close (run with --close to apply)")
        else:
            print("  ❌ Audit gate failures remain")
            # Extract failing gates for summary
            failing_lines = [
                line for line in audit_output.splitlines()
                if "❌" in line or "FAIL" in line.upper()
            ]
            for line in failing_lines[:5]:
                print(f"    {line.strip()}")
            if args.close:
                comment = (
                    f"**Auto-checked by `check_review_issues.py`**\n\n"
                    f"Module `{level}/{slug}` still has failing audit gates:\n\n"
                    f"```\n{audit_output[:2000]}\n```"
                )
                _comment_issue(number, comment)
                print("  → Commented with current status")
        print()


if __name__ == "__main__":
    main()
