#!/usr/bin/env python3
"""
Audit curriculum modules at level, module, or range granularity.

Supports both numbered modules (A1, B1, etc.) and slug-only modules (B2-HIST, C1-BIO, LIT).

Usage:
    npm run audit -- {level}                    # Audit entire level
    npm run audit -- {level} {num}              # Audit single module (numbered)
    npm run audit -- {level} {start}-{end}      # Audit range of modules (numbered)
    npm run audit -- {level} {num1},{num2},...  # Audit specific modules (numbered)
    npm run audit -- {level} {slug}             # Audit by slug (slug-only levels)
    npm run audit -- {level} {slug1},{slug2}    # Audit multiple slugs

Examples:
    npm run audit -- b1                         # Audit all B1 modules
    npm run audit -- a1 1-10                    # Audit A1 modules 1-10
    npm run audit -- b1 1,3,5,7                 # Audit B1 modules 1, 3, 5, 7
    npm run audit -- c1 1-5,10,15-20            # Audit C1 modules 1-5, 10, 15-20
    npm run audit -- b2-hist                    # Audit all B2-HIST modules
    npm run audit -- b2-hist afhanistan         # Audit single B2-HIST module
    npm run audit -- c1-bio shevchenko,franko   # Audit specific C1-BIO modules

Options:
    --fix       Automatically fix YAML schema violations
    --verbose   Show detailed output for each module
"""

import argparse
import glob
import re
import subprocess
import sys
from pathlib import Path

import yaml


def get_module_order_from_curriculum(level: str) -> list[str]:
    """Get canonical module order from curriculum.yaml for a level."""
    curriculum_path = Path("curriculum/l2-uk-en/curriculum.yaml")
    if not curriculum_path.exists():
        return []

    with open(curriculum_path, 'r', encoding='utf-8') as f:
        curriculum = yaml.safe_load(f)

    levels = curriculum.get('levels', {})
    level_data = levels.get(level, {})
    modules = level_data.get('modules', [])

    # Strip any comments from module names (e.g., "slug # [1]" -> "slug")
    clean_modules = []
    for m in modules:
        if isinstance(m, str):
            # Remove inline comments
            slug = m.split('#')[0].strip()
            clean_modules.append(slug)

    return clean_modules


def parse_module_filter(filter_str: str) -> list[int]:
    """Parse module filter string into list of module numbers.

    Supports:
        - Single number: "5" -> [5]
        - Range: "1-5" -> [1, 2, 3, 4, 5]
        - Comma-separated: "1,3,5" -> [1, 3, 5]
        - Mixed: "1-3,5,7-9" -> [1, 2, 3, 5, 7, 8, 9]
    """
    modules = set()

    for part in filter_str.split(','):
        part = part.strip()
        if '-' in part:
            # Range: "1-5"
            start, end = part.split('-', 1)
            try:
                start_num = int(start.strip())
                end_num = int(end.strip())
                modules.update(range(start_num, end_num + 1))
            except ValueError:
                print(f"Warning: Invalid range '{part}', skipping")
        else:
            # Single number
            try:
                modules.add(int(part))
            except ValueError:
                print(f"Warning: Invalid module number '{part}', skipping")

    return sorted(modules)


def find_module_files(level: str, module_filter: str | None = None) -> tuple[list[Path], list[str]]:
    """Find module markdown files for the given level and optional filter.

    Supports two patterns:
    - Numbered modules: 01-slug.md, 02-slug.md (A1, A2, B1, B2, C1, C2)
    - Slug-only modules: slug.md (B2-HIST, C1-BIO, LIT, etc.)

    For numbered modules, filter can be: 5, 1-10, 1,3,5
    For slug-only modules, filter can be: slug name or glob pattern
    
    Returns (found_files, missing_slugs)
    """
    base_path = Path(f"curriculum/l2-uk-en/{level}")
    missing_slugs = []

    if not base_path.exists():
        print(f"Error: Level directory not found: {base_path}")
        sys.exit(1)

    # Try numbered pattern first (e.g., 01-slug.md)
    numbered_pattern = str(base_path / "[0-9]*-*.md")
    numbered_files = sorted(glob.glob(numbered_pattern))

    if numbered_files:
        # Numbered modules - use numeric filtering
        if module_filter is None:
            # Check for missing numbered files if curriculum.yaml exists
            canonical = get_module_order_from_curriculum(level)
            if canonical:
                for slug in canonical:
                    # Find any file starting with [0-9]*-slug.md
                    found = list(base_path.glob(f"[0-9]*-{slug}.md"))
                    if not found:
                        # Try exact slug.md just in case
                        if not (base_path / f"{slug}.md").exists():
                            missing_slugs.append(slug)
            return [Path(f) for f in numbered_files], missing_slugs

        # Parse numeric filter
        module_nums = parse_module_filter(module_filter)
        if not module_nums:
            print(f"Error: No valid module numbers found in filter: {module_filter}")
            sys.exit(1)

        filtered_files = []
        for file_path in numbered_files:
            filename = Path(file_path).name
            match = re.match(r'^(\d+)-', filename)
            if match:
                num = int(match.group(1))
                if num in module_nums:
                    filtered_files.append(Path(file_path))
        return filtered_files, []

    # Try slug-only pattern (e.g., slug.md - no number prefix)
    # Get canonical order from curriculum.yaml
    canonical_order = get_module_order_from_curriculum(level)

    # Build file list in canonical order
    all_md_files = glob.glob(str(base_path / "*.md"))
    file_map = {Path(f).stem: Path(f) for f in all_md_files if not Path(f).name.startswith('_')}

    if canonical_order:
        # Use curriculum.yaml order
        slug_files = []
        for slug in canonical_order:
            if slug in file_map:
                slug_files.append(file_map[slug])
            else:
                missing_slugs.append(slug)
        # Add any files not in curriculum.yaml at the end (shouldn't happen normally)
        for slug, path in file_map.items():
            if path not in slug_files:
                slug_files.append(path)
    else:
        # Fallback to alphabetical if no curriculum.yaml entry
        slug_files = sorted(file_map.values(), key=lambda p: p.stem)

    if not slug_files and not missing_slugs:
        print(f"Error: No module files found in {base_path}")
        sys.exit(1)

    if module_filter is None:
        return slug_files, missing_slugs

    # Check if filter looks like numbers (for positional access)
    # e.g., "1", "1-5", "1,3,5", "1-3,5,7-9"
    if re.match(r'^[\d,\-\s]+$', module_filter):
        # Numeric filter - use positional indexing (1-based) based on curriculum.yaml order
        positions = parse_module_filter(module_filter)
        if not positions:
            print(f"Error: No valid positions found in filter: {module_filter}")
            sys.exit(1)

        filtered = []
        for pos in positions:
            if 1 <= pos <= len(slug_files):
                filtered.append(slug_files[pos - 1])  # Convert to 0-based
            else:
                print(f"Warning: Position {pos} out of range (1-{len(slug_files)})")
        return filtered, []

    # For slug-only modules, filter by glob pattern or exact match
    if '*' in module_filter or '?' in module_filter:
        # Glob pattern
        pattern = str(base_path / f"{module_filter}.md")
        matched = sorted(glob.glob(pattern))
        return [Path(f) for f in matched], []
    else:
        # Comma-separated slugs or single slug
        slugs = [s.strip() for s in module_filter.split(',')]
        filtered = []
        for f in slug_files:
            stem = f.stem  # filename without .md
            if stem in slugs:
                filtered.append(f)
        return filtered, []


def run_audit(files: list[Path], fix: bool = False, verbose: bool = False) -> tuple[int, int, list[str]]:
    """Run audit on the given files. Returns (passed, failed, failed_modules)."""
    passed = 0
    failed = 0
    failed_modules = []

    total = len(files)

    for i, file_path in enumerate(files, 1):
        # Extract module identifier for display
        match = re.match(r'^(\d+)-', file_path.name)
        if match:
            module_id = match.group(1)  # Numbered: "05"
        else:
            module_id = file_path.stem  # Slug-only: "afhanistan"

        # Progress indicator
        print(f"[{i}/{total}] {module_id}: ", end="", flush=True)

        # Build command
        cmd = [".venv/bin/python", "scripts/audit_module.py", str(file_path)]
        if fix:
            cmd.append("--fix")

        # Run audit
        if verbose:
            print()  # Newline before verbose output
            result = subprocess.run(cmd)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅")
            passed += 1
        else:
            print("❌")
            failed += 1
            failed_modules.append(module_id)

    return passed, failed, failed_modules


def main():
    parser = argparse.ArgumentParser(
        description="Audit curriculum modules at level, module, or range granularity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("level", help="Level to audit (a1, a2, b1, b2, c1, c2, b2-hist, c1-bio, etc.)")
    parser.add_argument("modules", nargs="?", help="Module number(s): 5, 1-10, or 1,3,5,7-9")
    parser.add_argument("--fix", action="store_true", help="Automatically fix YAML schema violations")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output for each module")
    parser.add_argument("--check-missing", action="store_true", help="Report missing content files listed in curriculum.yaml")

    args = parser.parse_args()

    # Find files (filter parsing happens inside find_module_files)
    files, missing = find_module_files(args.level, args.modules)

    if not files and not missing:
        if args.modules:
            print(f"Error: No matching modules found for: {args.modules}")
        else:
            print(f"Error: No modules found for level: {args.level}")
        sys.exit(1)

    total_planned = len(files) + len(missing)

    # Header
    level_upper = args.level.upper()
    print("═" * 64)
    if args.modules:
        print(f"  {level_upper} Audit: {len(files)} module(s)")
    else:
        print(f"  {level_upper} Full Level Audit: {total_planned} modules")
    
    if missing and args.check_missing:
        print(f"  (Warning: {len(missing)} modules are missing content files)")
    
    print("═" * 64)
    print()

    # Run audit
    passed, failed, failed_modules = run_audit(files, fix=args.fix, verbose=args.verbose)

    # Summary
    print()
    print("═" * 64)
    print("  Audit Summary")
    print("═" * 64)
    print()
    print(f"Total Planned: {total_planned}")
    print(f"Found:         {len(files)}")
    print(f"Passed:        {passed}")
    print(f"Failed:        {failed}")
    
    if args.check_missing:
        print(f"Missing:       {len(missing)}")

    print()

    if missing and args.check_missing:
        print(f"MISSING MODULES: {', '.join(missing)}")
        print()

    if failed > 0 or (len(missing) > 0 and args.check_missing):
        print(f"Failed modules: {', '.join(failed_modules)}")
        print()
        print("To audit a specific module:")
        print(f"  .venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/{args.level}/[NUM]-*.md")
        print()
        print("To auto-fix YAML issues:")
        print(f"  npm run audit -- {args.level} --fix")
        sys.exit(1)
    else:
        print(f"✅ All {level_upper} modules passed audit!")
        sys.exit(0)


if __name__ == "__main__":
    main()
