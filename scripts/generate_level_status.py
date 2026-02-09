#!/usr/bin/env python3
"""
Generate level status index files showing module completion overview.

Usage:
    python scripts/generate_level_status.py b2-hist          # Full level
    python scripts/generate_level_status.py a2 5             # Single module
    python scripts/generate_level_status.py a2 1-4,6-10      # Module ranges
    python scripts/generate_level_status.py all              # All levels
"""

import json
import os
import argparse
import subprocess
import sys
import re
import yaml
import multiprocessing
import io
from pathlib import Path
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr
from functools import partial

# Project root
ROOT = Path(__file__).parent.parent

# All levels
LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2", "b2-hist", "c1-bio", "c1-hist", "lit"]


def parse_module_filter(filter_str: str) -> set[int]:
    """Parse module filter string into set of module numbers."""
    result = set()
    parts = filter_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            result.update(range(int(start), int(end) + 1))
        else:
            result.add(int(part))
    return result


def load_curriculum_yaml():
    """Load curriculum.yaml to get module order."""
    curriculum_path = ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    with open(curriculum_path) as f:
        return yaml.safe_load(f)


def find_md_file(level: str, slug: str) -> Path | None:
    """Find markdown file for given level and slug."""
    level_dir = ROOT / "curriculum" / "l2-uk-en" / level
    slug_only = level_dir / f"{slug}.md"
    if slug_only.exists():
        return slug_only
    numbered = list(level_dir.glob(f"*-{slug}.md"))
    if numbered:
        return numbered[0]
    matches = list(level_dir.glob(f"*{slug}*.md"))
    if matches:
        return matches[0]
    return None


def get_json_cache(level: str, slug: str, md_file: Path) -> dict | None:
    """Read audit result from JSON cache if it exists and is fresh."""
    status_dir = md_file.parent / "status"
    cache_file = status_dir / f"{slug}.json"
    
    if not cache_file.exists():
        return None
        
    try:
        with cache_file.open('r', encoding='utf-8') as f:
            cache = json.load(f)
            
        # Check freshness: md mtime vs last_audit
        md_mtime = md_file.stat().st_mtime
        last_audit_str = cache.get('last_audit', '1970-01-01T00:00:00Z').replace('Z', '')
        if '.' in last_audit_str:
            last_audit_dt = datetime.fromisoformat(last_audit_str)
        else:
            last_audit_dt = datetime.strptime(last_audit_str, '%Y-%m-%dT%H:%M:%S')
            
        if last_audit_dt.timestamp() < md_mtime:
            return None # Stale
            
        # Map cache to status format
        overall = cache.get('overall', {})
        gates = cache.get('gates', {})
        
        status = "✅ PASS" if overall.get('status') == 'pass' else "❌ FAIL"
        
        # Word counts
        lesson_msg = gates.get('lesson', {}).get('message', '')
        word_match = re.search(r'(\d+)/(\d+)', lesson_msg)
        actual_words = int(word_match.group(1)) if word_match else 0
        target_words = int(word_match.group(2)) if word_match else 0
        
        if actual_words < 100:
            status = "📝 STUB"
            
        issues = overall.get('blocking_issues', [])
        
        return {
            "status": status,
            "actual_words": actual_words,
            "target_words": target_words,
            "issues": issues if issues else ["-"],
            "cached": True
        }
    except Exception:
        return None


def audit_worker(md_file: Path) -> dict:
    """Worker function to audit a single file and return status."""
    level = md_file.parent.name
    slug = md_file.stem
    
    # Try cache first
    cached = get_json_cache(level, slug, md_file)
    if cached:
        return {**cached, "slug": slug}

    # Fallback to direct import (Optimized)
    # Add scripts to path for worker
    script_dir = str(Path(__file__).parent)
    if script_dir not in sys.path:
        sys.path.append(script_dir)

    from audit import audit_module

    f = io.StringIO()
    success = False
    with redirect_stdout(f), redirect_stderr(f):
        try:
            success = audit_module(str(md_file))
        except Exception as e:
            print(f"Error auditing {md_file}: {e}")
            success = False

    output = f.getvalue()
    status = "✅ PASS" if success else "❌ FAIL"

    # Re-parse word counts from output if needed, or better, read from fresh status cache
    # Since audit_module saves the cache, we can just read it back
    fresh_cached = get_json_cache(level, slug, md_file)
    if fresh_cached:
        return {**fresh_cached, "slug": slug}

    # Fallback to parsing output
    word_match = re.search(r'Words\s+\S+\s+(\d+)/(\d+)', output)
    actual_words = int(word_match.group(1)) if word_match else 0
    target_words = int(word_match.group(2)) if word_match else 0
    issues = []
    if actual_words < 100:
        issues.append("empty")
        status = "📝 STUB"
    elif target_words > 0 and actual_words < target_words * 0.95:
        issues.append("word_count")
    if "Missing required activity types" in output: issues.append("activities")
    if "Structure" in output and "❌" in output: issues.append("structure")

    return {
        "slug": slug,
        "status": status,
        "actual_words": actual_words,
        "target_words": target_words,
        "issues": issues if issues else ["-"]
    }


def _parse_existing_status(status_file: Path) -> dict[int, dict]:
    """Parse existing status file to extract module rows."""
    rows = {}
    try:
        content = status_file.read_text()
        for line in content.split('\n'):
            if line.startswith('|') and not line.startswith('| #') and not line.startswith('|---'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 5:
                    try:
                        num = int(parts[0])
                        words_parts = parts[3].split('/')
                        rows[num] = {
                            "num": num,
                            "slug": parts[1],
                            "status": parts[2],
                            "actual_words": int(words_parts[0]) if words_parts[0].isdigit() else 0,
                            "target_words": int(words_parts[1]) if len(words_parts) > 1 and words_parts[1].isdigit() else 0,
                            "issues": [parts[4]] if parts[4] != "-" else ["-"]
                        }
                    except (ValueError, IndexError):
                        continue
    except Exception:
        pass
    return rows


def generate_status_for_level(level: str, module_filter: set[int] | None = None, jobs: int = 1):
    """Generate status file for a single level."""
    filter_desc = f" (modules: {sorted(module_filter)})" if module_filter else ""
    print(f"Generating status for {level}{filter_desc}...")
    curriculum = load_curriculum_yaml()
    if level not in curriculum.get('levels', {}):
        print(f"  ❌ Level {level} not found in curriculum.yaml")
        return
    level_data = curriculum['levels'][level]
    modules = level_data.get('modules', [])
    if not modules:
        print(f"  ⚠️ No modules found for {level}")
        return
    modules_to_audit = module_filter if module_filter else set(range(1, len(modules) + 1))
    level_upper = level.upper()
    output_file = ROOT / "docs" / f"{level_upper}-STATUS.md"
    existing_rows = {}
    if module_filter and output_file.exists():
        existing_rows = _parse_existing_status(output_file)
    module_rows = []
    stats = {"pass": 0, "fail": 0, "stub": 0, "error": 0}

    # Prepare files to audit
    files_to_audit = []
    module_indices = []

    for i, slug in enumerate(modules, 1):
        if module_filter and i not in modules_to_audit:
            if i in existing_rows:
                row = existing_rows[i]
                module_rows.append(row)
                if row["status"] == "✅ PASS": stats["pass"] += 1
                elif row["status"] == "📝 STUB": stats["stub"] += 1
                elif row["status"] == "❌ FAIL": stats["fail"] += 1
                else: stats["error"] += 1
            else:
                # Placeholder for filtered out modules not in existing rows
                module_rows.append({"num": i, "slug": slug, "status": "⚪️ SKIP", "actual_words": 0, "target_words": 0, "issues": ["-"]})
            continue

        md_file = find_md_file(level, slug)
        if not md_file:
            module_rows.append({"num": i, "slug": slug, "status": "⚠️ MISSING", "actual_words": 0, "target_words": 0, "issues": ["no_file"]})
            stats["error"] += 1
            continue

        files_to_audit.append(md_file)
        module_indices.append(i)

    # Run audits in parallel if jobs > 1
    if jobs > 1 and len(files_to_audit) > 1:
        print(f"  Auditing {len(files_to_audit)} modules using {jobs} jobs...")
        with multiprocessing.Pool(processes=jobs) as pool:
            results = pool.map(audit_worker, files_to_audit)

        for i, idx in enumerate(module_indices):
            audit_result = results[i]
            if audit_result["status"] == "✅ PASS": stats["pass"] += 1
            elif audit_result["status"] == "📝 STUB": stats["stub"] += 1
            elif audit_result["status"] == "❌ FAIL": stats["fail"] += 1
            else: stats["error"] += 1
            module_rows.append({"num": idx, "slug": slug, **audit_result})
    else:
        # Sequential
        for i, md_file in zip(module_indices, files_to_audit):
            audit_result = audit_worker(md_file)
            if audit_result["status"] == "✅ PASS": stats["pass"] += 1
            elif audit_result["status"] == "📝 STUB": stats["stub"] += 1
            elif audit_result["status"] == "❌ FAIL": stats["fail"] += 1
            else: stats["error"] += 1
            module_rows.append({"num": i, "slug": audit_result["slug"], **audit_result})

    # Sort results by module number
    module_rows.sort(key=lambda x: x["num"])
    
    with open(output_file, 'w') as f:
        f.write(f"# {level_upper} Module Status\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Modules:** {len(modules)}\n")
        f.write(f"**Status:** {stats['pass']} passing, {stats['fail']} failing, {stats['stub']} stubs, {stats['error']} errors\n\n")
        f.write("## Quick Summary\n\n")
        f.write(f"- ✅ **Passing:** {stats['pass']}/{len(modules)} ({stats['pass']*100//len(modules) if modules else 0}%)\n")
        f.write(f"- ❌ **Failing:** {stats['fail']}/{len(modules)}\n")
        f.write(f"- 📝 **Stubs:** {stats['stub']}/{len(modules)}\n")
        if stats['error'] > 0: f.write(f"- ⚠️ **Errors:** {stats['error']}/{len(modules)}\n")
        f.write("\n## Module Details\n\n")
        f.write("| # | Slug | Status | Words | Issues |\n")
        f.write("|---|------|--------|-------|--------|\n")
        for row in module_rows:
            issues_str = ", ".join(row["issues"])
            words_str = f"{row['actual_words']}/{row['target_words']}"
            f.write(f"| {row['num']:03d} | {row['slug']} | {row['status']} | {words_str} | {issues_str} |\n")
        f.write("\n---\n\n**Legend:**\n- ✅ PASS: All audit gates pass\n- ❌ FAIL: Some audit gates fail\n- 📝 STUB: Empty or < 100 words\n- ⚠️ ERROR/MISSING: File not found or audit error\n\n")
        f.write("**Issue codes:**\n- `hydration`: Meta content_outline doesn't sum to word_target\n- `word_count`: Content < 95% of target\n- `empty`: < 100 words (stub)\n- `activities`: Missing required activity types\n- `structure`: Missing required sections\n- `-`: No issues\n\n*Auto-generated by `scripts/generate_level_status.py` - Re-run anytime to update*\n")
    print(f"  ✅ Generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate level status index files.")
    parser.add_argument("level", help="Level (a1, a2, ... or 'all')")
    parser.add_argument("filter", nargs="?", help="Module filter (e.g., 1-5)")
    parser.add_argument("--jobs", "-j", type=int, default=multiprocessing.cpu_count(),
                        help="Number of parallel jobs")

    args = parser.parse_args()

    level_arg = args.level.lower()
    module_filter = None
    if args.filter:
        module_filter = parse_module_filter(args.filter)

    if level_arg == "all":
        for level in LEVELS:
            generate_status_for_level(level, jobs=args.jobs)
    elif level_arg in LEVELS:
        generate_status_for_level(level_arg, module_filter, jobs=args.jobs)
    else:
        print(f"❌ Unknown level: {level_arg}")
        sys.exit(1)


if __name__ == "__main__":
    main()