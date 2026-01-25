#!/usr/bin/env python3
"""
Generate level status index files showing module completion overview.

Usage:
    python scripts/generate_level_status.py b2-hist
    python scripts/generate_level_status.py all
"""

import subprocess
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime

# Project root
ROOT = Path(__file__).parent.parent

# All levels
LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'b2-hist', 'c1-bio', 'c1-hist', 'lit']

def load_curriculum_yaml():
    """Load curriculum.yaml to get module order."""
    curriculum_path = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    with open(curriculum_path) as f:
        return yaml.safe_load(f)

def find_md_file(level: str, slug: str) -> Path | None:
    """Find markdown file for given level and slug."""
    level_dir = ROOT / "curriculum" / "l2-uk-en" / level

    # Try slug-only first (tracks)
    slug_only = level_dir / f"{slug}.md"
    if slug_only.exists():
        return slug_only

    # Try numbered pattern (core levels)
    numbered = list(level_dir.glob(f"*-{slug}.md"))
    if numbered:
        return numbered[0]

    # Try finding by slug in filename
    matches = list(level_dir.glob(f"*{slug}*.md"))
    if matches:
        return matches[0]

    return None

def audit_module(md_file: Path) -> dict:
    """Run audit and extract key metrics."""
    try:
        result = subprocess.run(
            [".venv/bin/python", "scripts/audit_module.py", str(md_file)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=ROOT
        )
        output = result.stdout + result.stderr

        # Extract metrics
        status = "✅ PASS" if "✅ AUDIT PASSED" in output else "❌ FAIL"

        # Word counts
        word_match = re.search(r'Words\s+\S+\s+(\d+)/(\d+)', output)
        if word_match:
            actual_words = int(word_match.group(1))
            target_words = int(word_match.group(2))
        else:
            actual_words = 0
            target_words = 0

        # Identify issues
        issues = []
        if "HYDRATION ERROR" in output:
            issues.append("hydration")
        if actual_words < 100:
            issues.append("empty")
            status = "📝 STUB"
        elif actual_words < target_words * 0.95:
            issues.append("word_count")
        if "Missing required activity types" in output:
            issues.append("activities")
        if "Structure" in output and "❌" in output:
            issues.append("structure")

        return {
            "status": status,
            "actual_words": actual_words,
            "target_words": target_words,
            "issues": issues if issues else ["-"]
        }
    except Exception as e:
        return {
            "status": "⚠️ ERROR",
            "actual_words": 0,
            "target_words": 0,
            "issues": [str(e)[:20]]
        }

def generate_status_for_level(level: str):
    """Generate status file for a single level."""
    print(f"Generating status for {level}...")

    curriculum = load_curriculum_yaml()
    if level not in curriculum.get('levels', {}):
        print(f"  ❌ Level {level} not found in curriculum.yaml")
        return

    level_data = curriculum['levels'][level]
    modules = level_data.get('modules', [])

    if not modules:
        print(f"  ⚠️ No modules found for {level}")
        return

    # Collect module data
    module_rows = []
    stats = {"pass": 0, "fail": 0, "stub": 0, "error": 0}

    for i, slug in enumerate(modules, 1):
        md_file = find_md_file(level, slug)

        if not md_file:
            module_rows.append({
                "num": i,
                "slug": slug,
                "status": "⚠️ MISSING",
                "actual_words": 0,
                "target_words": 0,
                "issues": ["no_file"]
            })
            stats["error"] += 1
            continue

        # Run audit
        audit_result = audit_module(md_file)

        # Update stats
        if audit_result["status"] == "✅ PASS":
            stats["pass"] += 1
        elif audit_result["status"] == "📝 STUB":
            stats["stub"] += 1
        elif audit_result["status"] == "❌ FAIL":
            stats["fail"] += 1
        else:
            stats["error"] += 1

        module_rows.append({
            "num": i,
            "slug": slug,
            **audit_result
        })

    # Generate markdown
    level_upper = level.upper()
    output_file = ROOT / "docs" / f"{level_upper}-STATUS.md"

    with open(output_file, 'w') as f:
        f.write(f"# {level_upper} Module Status\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Modules:** {len(modules)}\n")
        f.write(f"**Status:** {stats['pass']} passing, {stats['fail']} failing, {stats['stub']} stubs, {stats['error']} errors\n\n")

        # Summary by status
        f.write("## Quick Summary\n\n")
        f.write(f"- ✅ **Passing:** {stats['pass']}/{len(modules)} ({stats['pass']*100//len(modules)}%)\n")
        f.write(f"- ❌ **Failing:** {stats['fail']}/{len(modules)}\n")
        f.write(f"- 📝 **Stubs:** {stats['stub']}/{len(modules)}\n")
        if stats['error'] > 0:
            f.write(f"- ⚠️ **Errors:** {stats['error']}/{len(modules)}\n")
        f.write("\n")

        # Table
        f.write("## Module Details\n\n")
        f.write("| # | Slug | Status | Words | Issues |\n")
        f.write("|---|------|--------|-------|--------|\n")

        for row in module_rows:
            issues_str = ", ".join(row["issues"])
            words_str = f"{row['actual_words']}/{row['target_words']}"
            f.write(f"| {row['num']:03d} | {row['slug']} | {row['status']} | {words_str} | {issues_str} |\n")

        # Footer
        f.write("\n---\n\n")
        f.write("**Legend:**\n")
        f.write("- ✅ PASS: All audit gates pass\n")
        f.write("- ❌ FAIL: Some audit gates fail\n")
        f.write("- 📝 STUB: Empty or < 100 words\n")
        f.write("- ⚠️ ERROR/MISSING: File not found or audit error\n\n")
        f.write("**Issue codes:**\n")
        f.write("- `hydration`: Meta content_outline doesn't sum to word_target\n")
        f.write("- `word_count`: Content < 95% of target\n")
        f.write("- `empty`: < 100 words (stub)\n")
        f.write("- `activities`: Missing required activity types\n")
        f.write("- `structure`: Missing required sections\n")
        f.write("- `-`: No issues\n\n")
        f.write(f"*Auto-generated by `scripts/generate_level_status.py` - Re-run anytime to update*\n")

    print(f"  ✅ Generated: {output_file}")
    print(f"     {stats['pass']} passing, {stats['fail']} failing, {stats['stub']} stubs")

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_level_status.py {level|all}")
        print(f"Levels: {', '.join(LEVELS)}")
        sys.exit(1)

    level_arg = sys.argv[1].lower()

    if level_arg == "all":
        for level in LEVELS:
            generate_status_for_level(level)
            print()
    elif level_arg in LEVELS:
        generate_status_for_level(level_arg)
    else:
        print(f"❌ Unknown level: {level_arg}")
        print(f"Available levels: {', '.join(LEVELS)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
