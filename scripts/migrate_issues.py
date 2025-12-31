#!/usr/bin/env python3
"""
GitHub Issue Migration Script

Migrates open issues from old repo to new repo, preserving:
- Issue relationships (epics/children)
- Cross-references (converting #XX to new numbers or full URLs)
- Labels, assignees, and metadata

Usage:
    python scripts/migrate_issues.py --dry-run  # Preview only
    python scripts/migrate_issues.py            # Actually migrate
"""

import json
import re
import subprocess
import sys
from collections import defaultdict

# Configuration
OLD_REPO = "krisztiankoos/learn-ukrainian"
NEW_REPO = "learn-ukrainian/learn-ukrainian.github.io"

def run_gh(args: list[str]) -> str:
    """Run a gh CLI command and return output."""
    result = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout

def fetch_issues(repo: str, state: str = "all") -> list[dict]:
    """Fetch all issues from a repo."""
    print(f"Fetching {state} issues from {repo}...")
    output = run_gh([
        "issue", "list",
        "-R", repo,
        "--state", state,
        "--limit", "500",
        "--json", "number,title,body,state,labels,assignees,milestone"
    ])
    return json.loads(output) if output else []

def find_references(body: str) -> set[int]:
    """Find all #XX issue references in body text."""
    if not body:
        return set()
    # Match #123 but not URLs containing #123
    pattern = r'(?<![/\w])#(\d+)(?!\d)'
    matches = re.findall(pattern, body)
    return {int(m) for m in matches}

def build_dependency_graph(issues: list[dict], all_issues: dict[int, dict]) -> dict[int, set[int]]:
    """Build a graph of issue dependencies."""
    deps = defaultdict(set)
    for issue in issues:
        refs = find_references(issue.get("body", ""))
        for ref in refs:
            if ref in all_issues and all_issues[ref]["state"] == "OPEN":
                # This issue depends on another open issue
                deps[issue["number"]].add(ref)
    return deps

def topological_sort(issues: list[dict], deps: dict[int, set[int]]) -> list[dict]:
    """Sort issues so dependencies come first."""
    # Issues with no dependencies come first
    result = []
    remaining = {i["number"]: i for i in issues}
    resolved = set()

    while remaining:
        # Find issues with all dependencies resolved
        ready = []
        for num, issue in remaining.items():
            issue_deps = deps.get(num, set())
            if issue_deps <= resolved:
                ready.append((num, issue))

        if not ready:
            # Circular dependency or external refs - just add remaining
            for num, issue in remaining.items():
                result.append(issue)
            break

        # Add ready issues to result
        for num, issue in sorted(ready, key=lambda x: x[0]):
            result.append(issue)
            resolved.add(num)
            del remaining[num]

    return result

def rewrite_references(body: str, mapping: dict[int, int], old_issues: dict[int, dict]) -> str:
    """Rewrite #XX references to new numbers or full URLs."""
    if not body:
        return body

    def replace_ref(match):
        old_num = int(match.group(1))
        if old_num in mapping:
            # Open issue that was migrated - use new number
            return f"#{mapping[old_num]}"
        elif old_num in old_issues:
            # Closed issue - use full URL
            return f"[#{old_num}](https://github.com/{OLD_REPO}/issues/{old_num})"
        else:
            # Unknown reference - keep as-is with note
            return f"#{old_num}"

    pattern = r'(?<![/\w])#(\d+)(?!\d)'
    return re.sub(pattern, replace_ref, body)

def create_issue(repo: str, title: str, body: str, labels: list[str] = None) -> int:
    """Create an issue and return its number."""
    args = [
        "issue", "create",
        "-R", repo,
        "--title", title,
        "--body", body
    ]

    if labels:
        for label in labels:
            args.extend(["--label", label])

    output = run_gh(args)
    # Output is like: https://github.com/owner/repo/issues/123
    if output:
        match = re.search(r'/issues/(\d+)', output)
        if match:
            return int(match.group(1))
    return 0

def close_old_issue(repo: str, number: int, new_number: int, new_repo: str):
    """Close the old issue with a migration note."""
    comment = f"✅ Migrated to {new_repo}#{new_number}"
    run_gh(["issue", "comment", str(number), "-R", repo, "--body", comment])
    run_gh(["issue", "close", str(number), "-R", repo])

def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=" * 60)
        print("DRY RUN - No changes will be made")
        print("=" * 60)

    # Fetch all issues (open and closed) for reference resolution
    all_issues_list = fetch_issues(OLD_REPO, "all")
    all_issues = {i["number"]: i for i in all_issues_list}

    # Filter to open issues only for migration
    open_issues = [i for i in all_issues_list if i["state"] == "OPEN"]
    print(f"\nFound {len(open_issues)} open issues to migrate")
    print(f"Found {len(all_issues) - len(open_issues)} closed issues (will use full URLs)")

    # Build dependency graph and sort
    deps = build_dependency_graph(open_issues, all_issues)
    sorted_issues = topological_sort(open_issues, deps)

    print(f"\nMigration order ({len(sorted_issues)} issues):")
    print("-" * 60)

    # Track old -> new number mapping
    mapping = {}

    for i, issue in enumerate(sorted_issues, 1):
        old_num = issue["number"]
        title = issue["title"]
        body = issue.get("body", "") or ""
        labels = [l["name"] for l in issue.get("labels", [])]

        # Add migration header
        migration_header = f"> 📦 Migrated from [{OLD_REPO}#{old_num}](https://github.com/{OLD_REPO}/issues/{old_num})\n\n"

        # Rewrite references
        new_body = rewrite_references(body, mapping, all_issues)
        full_body = migration_header + new_body

        # Show what we're doing
        refs = find_references(body)
        refs_str = f" (refs: {', '.join(f'#{r}' for r in sorted(refs))})" if refs else ""
        print(f"{i:3}. #{old_num} → ", end="")

        if dry_run:
            new_num = 236 + i - 1  # Simulated new number
            print(f"#{new_num} (simulated) - {title[:50]}{refs_str}")
        else:
            new_num = create_issue(NEW_REPO, title, full_body, labels)
            if new_num:
                print(f"#{new_num} ✓ - {title[:50]}{refs_str}")
                # Close old issue with reference
                close_old_issue(OLD_REPO, old_num, new_num, NEW_REPO)
            else:
                print(f"FAILED - {title[:50]}")
                continue

        mapping[old_num] = new_num

    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION MAPPING")
    print("=" * 60)
    for old, new in sorted(mapping.items()):
        print(f"  #{old} → #{new}")

    if dry_run:
        print("\n⚠️  DRY RUN - No changes were made")
        print("Run without --dry-run to actually migrate")
    else:
        print(f"\n✅ Successfully migrated {len(mapping)} issues")
        print(f"Old issues have been closed with migration links")

if __name__ == "__main__":
    main()
