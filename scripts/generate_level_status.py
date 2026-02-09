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
import sys
import re
import yaml
from pathlib import Path
from datetime import datetime
from multiprocessing import Pool

# Add project root to sys.path
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Also add scripts dir to sys.path for audit imports
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

try:
    from audit.core import audit_module as run_module_audit
except ImportError:
    # Fallback for different environments
    run_module_audit = None

# All levels
LEVELS = ["a1", "a2", "b1", "b2", "c1", "c2", "b2-hist", "c1-bio", "c1-hist", "lit", "oes", "ruth"]


def parse_module_filter(filter_str: str) -> set[int]:
    """Parse module filter string into set of module numbers."""
    result = set()
    parts = filter_str.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                result.update(range(int(start), int(end) + 1))
            except ValueError:
                continue
        else:
            try:
                result.add(int(part))
            except ValueError:
                continue
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
            
        source_mtimes = cache.get('source_mtimes', {})
        last_audit_str = cache.get('last_audit', '1970-01-01T00:00:00Z').replace('Z', '')

        # Freshness check
        is_stale = False

        if not source_mtimes:
            # Legacy check: md mtime vs last_audit
            md_mtime = md_file.stat().st_mtime
            if '.' in last_audit_str:
                last_audit_dt = datetime.fromisoformat(last_audit_str)
            else:
                last_audit_dt = datetime.strptime(last_audit_str, '%Y-%m-%dT%H:%M:%S')
            
            if last_audit_dt.timestamp() < md_mtime:
                is_stale = True
        else:
            # Robust check: all source_mtimes
            base_path = md_file.parent
            for key, cached_mtime in source_mtimes.items():
                if cached_mtime is None:
                    continue

                # Resolve path
                path = None
                if key == 'md': path = md_file
                elif key == 'meta': path = base_path / 'meta' / f"{slug}.yaml"
                elif key == 'activities': path = base_path / 'activities' / f"{slug}.yaml"
                elif key == 'vocabulary': path = base_path / 'vocabulary' / f"{slug}.yaml"
                elif key == 'plan': path = ROOT / 'curriculum' / 'l2-uk-en' / 'plans' / base_path.name / f"{slug}.yaml"
                elif key == 'grammar':
                    path = base_path / 'audit' / f"{slug}-grammar.yaml"
                    if not path.exists(): path = base_path / f"{slug}-grammar.yaml"
                elif key == 'quality':
                    path = base_path / 'audit' / f"{slug}-quality.md"
                    if not path.exists(): path = base_path / f"{slug}-quality.md"

                if path and path.exists():
                    current_mtime = datetime.fromtimestamp(path.stat().st_mtime).isoformat() + "Z"
                    if current_mtime != cached_mtime:
                        is_stale = True
                        break

        if is_stale:
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


def get_module_status(md_file: Path) -> dict:
    """Run audit or read from cache."""
    level = md_file.parent.name
    slug = md_file.stem
    
    # Try cache first
    cached = get_json_cache(level, slug, md_file)
    if cached:
        return cached

    # If we are here, cache is stale or missing
    # Run audit
    if run_module_audit:
        # Capture stdout to avoid clutter
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            run_module_audit(str(md_file))

        # After audit, cache should be updated. Try reading it again.
        cached = get_json_cache(level, slug, md_file)
        if cached:
            return cached

    # Fallback to older subprocess method if direct call failed or unavailable
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "audit_module.py"), str(md_file)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=ROOT
        )
        # Try reading cache one last time
        cached = get_json_cache(level, slug, md_file)
        if cached:
            return cached

        # If cache still not there, parse output
        output = result.stdout + result.stderr
        status = "✅ PASS" if "✅ AUDIT PASSED" in output else "❌ FAIL"
        word_match = re.search(r'Words\s+\S+\s+(\d+)/(\d+)', output)
        actual_words = int(word_match.group(1)) if word_match else 0
        target_words = int(word_match.group(2)) if word_match else 0
        issues = []
        if "HYDRATION ERROR" in output: issues.append("hydration")
        if actual_words < 100:
            issues.append("empty")
            status = "📝 STUB"
        elif actual_words < target_words * 0.95:
            issues.append("word_count")
        if "Missing required activity types" in output: issues.append("activities")
        if "Structure" in output and "❌" in output: issues.append("structure")
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


def process_module(args):
    """Worker function for multiprocessing."""
    num, slug, level, module_filter, modules_to_audit, existing_rows = args

    if module_filter and num not in modules_to_audit:
        if num in existing_rows:
            return existing_rows[num]
        return None

    md_file = find_md_file(level, slug)
    if not md_file:
        return {"num": num, "slug": slug, "status": "⚠️ MISSING", "actual_words": 0, "target_words": 0, "issues": ["no_file"]}

    result = get_module_status(md_file)
    result["num"] = num
    result["slug"] = slug
    return result


def generate_status_for_level(level: str, module_filter: set[int] | None = None):
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

    # Prepare tasks for pool
    tasks = []
    for i, slug in enumerate(modules, 1):
        # Handle curriculum.yaml entry which might be "slug # comments"
        clean_slug = slug.split('#')[0].strip()
        tasks.append((i, clean_slug, level, module_filter, modules_to_audit, existing_rows))

    # Run tasks in parallel
    with Pool() as pool:
        results = pool.map(process_module, tasks)

    module_rows = [r for r in results if r is not None]

    # Calculate stats
    stats = {"pass": 0, "fail": 0, "stub": 0, "error": 0}
    for row in module_rows:
        if row["status"] == "✅ PASS": stats["pass"] += 1
        elif row["status"] == "📝 STUB": stats["stub"] += 1
        elif row["status"] == "❌ FAIL": stats["fail"] += 1
        else: stats["error"] += 1
    
    # Write report
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
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_level_status.py {level|all} [module_filter]")
        sys.exit(1)
    level_arg = sys.argv[1].lower()
    module_filter = None
    if len(sys.argv) >= 3:
        module_filter = parse_module_filter(sys.argv[2])
    if level_arg == "all":
        for level in LEVELS:
            generate_status_for_level(level)
    elif level_arg in LEVELS:
        generate_status_for_level(level_arg, module_filter)
    else:
        print(f"❌ Unknown level: {level_arg}")
        sys.exit(1)


if __name__ == "__main__":
    main()
