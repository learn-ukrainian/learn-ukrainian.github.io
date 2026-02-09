#!/usr/bin/env python3
"""
Audit changed modules only.
Used in CI to provide fast feedback.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return result.stdout.splitlines()

def get_changed_modules():
    # If GITHUB_BASE_REF is set, we are in a PR
    base_ref = os.getenv('GITHUB_BASE_REF')

    files = []
    if base_ref:
        print(f"PR context detected. Comparing with origin/{base_ref}")
        files = run_command(['git', 'diff', '--name-only', f'origin/{base_ref}...HEAD'])
        if not files:
             # Try without origin prefix if it fails
             files = run_command(['git', 'diff', '--name-only', f'{base_ref}...HEAD'])
    else:
        # Check if we are in a git repo
        if os.path.exists('.git'):
            # Just look at changes in the last commit or staged/unstaged changes
            files = run_command(['git', 'diff', '--name-only', 'HEAD~1'])
            # Also add current uncommitted changes
            files.extend(run_command(['git', 'diff', '--name-only']))
            files.extend(run_command(['git', 'diff', '--cached', '--name-only']))

    # Unique files
    files = list(set(files))

    # Filter for curriculum modules
    # Pattern: curriculum/l2-uk-en/{level}/{num}-{slug}.md
    modules = []
    for f in files:
        if f.startswith('curriculum/l2-uk-en/') and f.endswith('.md') and not f.endswith('README.md'):
            # Ensure it's in a level directory (not just root of curriculum)
            parts = f.split('/')
            if len(parts) >= 4:
                modules.append(f)

    return modules

def main():
    modules = get_changed_modules()
    if not modules:
        print("No changed curriculum modules found to audit.")
        sys.exit(0)

    print(f"Found {len(modules)} changed module(s):")
    for m in modules:
        print(f"  - {m}")

    failed = False
    for m in modules:
        if not os.path.exists(m):
            print(f"\nSkipping {m} (file deleted)")
            continue

        print(f"\n{'='*60}")
        print(f"AUDITING: {m}")
        print(f"{'='*60}")

        # Run audit_module.py
        # We use --naturalness to trigger naturalness check (which we mock in CI)
        res = subprocess.run([sys.executable, 'scripts/audit_module.py', m, '--naturalness'])
        if res.returncode != 0:
            failed = True

    if failed:
        print("\n❌ SOME AUDITS FAILED.")
        sys.exit(1)
    else:
        print("\n✅ ALL AUDITS PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
