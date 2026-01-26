#!/usr/bin/env python3
"""
Update status files for curriculum levels.

This script scans module files and updates status/{level}.yaml with
current module status based on file existence and audit results.

Usage:
    python scripts/update_status.py b1              # Update B1 status
    python scripts/update_status.py b1 5            # Update single module
    python scripts/update_status.py all             # Update all levels
    python scripts/update_status.py --init b1       # Initialize status file

Status stages:
    planned    - Has plan file, no content
    content    - Has content MD file (>100 words)
    activities - Has activities YAML file
    reviewed   - Has naturalness score >= threshold
"""

import sys
import re
import yaml
import subprocess
from pathlib import Path
from datetime import datetime, timezone

# Project root
ROOT = Path(__file__).parent.parent

# All levels
LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'b2-hist', 'c1-bio', 'c1-hist', 'lit']

# Status directory
STATUS_DIR = ROOT / "curriculum" / "l2-uk-en" / "status"


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


def count_words(content: str) -> int:
    """Count Ukrainian words in markdown content, excluding code blocks and frontmatter."""
    # Remove frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    # Remove code blocks
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    # Remove inline code
    content = re.sub(r'`[^`]+`', '', content)
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    # Remove markdown links (keep text)
    content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
    # Count words
    words = re.findall(r'\b[\w\u0400-\u04FF]+\b', content)
    return len(words)


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


def find_activities_file(level: str, slug: str) -> Path | None:
    """Find activities YAML file."""
    activities_dir = ROOT / "curriculum" / "l2-uk-en" / level / "activities"

    # Direct match
    direct = activities_dir / f"{slug}.yaml"
    if direct.exists():
        return direct

    # Numbered match
    numbered = list(activities_dir.glob(f"*-{slug}.yaml"))
    if numbered:
        return numbered[0]

    return None


def find_plan_file(level: str, slug: str) -> Path | None:
    """Find plan file."""
    plans_dir = ROOT / "curriculum" / "l2-uk-en" / "plans" / level

    direct = plans_dir / f"{slug}.yaml"
    if direct.exists():
        return direct

    return None


def find_meta_file(level: str, slug: str) -> Path | None:
    """Find meta file."""
    meta_dir = ROOT / "curriculum" / "l2-uk-en" / level / "meta"

    # Try exact slug match
    exact = meta_dir / f"{slug}.yaml"
    if exact.exists():
        return exact

    # Try numbered pattern
    numbered = list(meta_dir.glob(f"*-{slug}.yaml"))
    if numbered:
        return numbered[0]

    return None


def get_naturalness_score(level: str, slug: str) -> int | None:
    """Get naturalness score from meta file."""
    meta_file = find_meta_file(level, slug)
    if not meta_file:
        return None

    try:
        with open(meta_file) as f:
            meta = yaml.safe_load(f)
        naturalness = meta.get('naturalness', {})
        if isinstance(naturalness, dict):
            return naturalness.get('score')
        elif isinstance(naturalness, int):
            return naturalness
    except Exception:
        pass
    return None


def get_word_target(level: str, slug: str) -> int:
    """Get word target from meta or plan file."""
    # Try meta first
    meta_file = find_meta_file(level, slug)
    if meta_file:
        try:
            with open(meta_file) as f:
                meta = yaml.safe_load(f)
            if meta.get('word_target'):
                return meta.get('word_target')
        except Exception:
            pass

    # Try plan
    plan_file = find_plan_file(level, slug)
    if plan_file:
        try:
            with open(plan_file) as f:
                plan = yaml.safe_load(f)
            if plan.get('word_target'):
                return plan.get('word_target')
        except Exception:
            pass

    return 1500  # Default


def determine_module_status(level: str, slug: str) -> dict:
    """Determine status and metrics for a module."""
    result = {
        'status': 'planned',
        'last_updated': datetime.now().strftime('%Y-%m-%d')
    }

    # Check for plan file
    plan_file = find_plan_file(level, slug)
    if plan_file:
        try:
            with open(plan_file) as f:
                plan = yaml.safe_load(f)
            result['plan_version'] = plan.get('version', '1.0')
        except Exception:
            pass

    # Check for content file
    md_file = find_md_file(level, slug)
    if md_file:
        try:
            content = md_file.read_text()
            word_count = count_words(content)
            result['content_words'] = word_count
            result['word_target'] = get_word_target(level, slug)

            if word_count > 100:
                result['status'] = 'content'
        except Exception:
            pass

    # Check for activities file
    activities_file = find_activities_file(level, slug)
    if activities_file:
        try:
            with open(activities_file) as f:
                activities = yaml.safe_load(f)
            if activities and isinstance(activities, list):
                result['activity_count'] = len(activities)
                if result['status'] == 'content':
                    result['status'] = 'activities'
        except Exception:
            pass

    # Check for naturalness score (indicates review)
    naturalness = get_naturalness_score(level, slug)
    if naturalness:
        result['naturalness'] = naturalness
        if naturalness >= 7 and result['status'] == 'activities':
            result['status'] = 'reviewed'

    return result


def load_status_file(level: str) -> dict:
    """Load existing status file or create empty structure."""
    status_file = STATUS_DIR / f"{level}.yaml"

    if status_file.exists():
        with open(status_file) as f:
            return yaml.safe_load(f) or {}

    # Return empty structure
    return {
        'level': level,
        'updated': datetime.now(timezone.utc).isoformat(),
        'summary': {
            'total': 0,
            'planned': 0,
            'content': 0,
            'activities': 0,
            'reviewed': 0
        },
        'modules': {}
    }


def save_status_file(level: str, status: dict):
    """Save status file with nice formatting."""
    STATUS_DIR.mkdir(parents=True, exist_ok=True)
    status_file = STATUS_DIR / f"{level}.yaml"

    # Update timestamp
    status['updated'] = datetime.now(timezone.utc).isoformat()

    # Recalculate summary
    modules = status.get('modules', {})
    status['summary'] = {
        'total': len(modules),
        'planned': sum(1 for m in modules.values() if m.get('status') == 'planned'),
        'content': sum(1 for m in modules.values() if m.get('status') == 'content'),
        'activities': sum(1 for m in modules.values() if m.get('status') == 'activities'),
        'reviewed': sum(1 for m in modules.values() if m.get('status') == 'reviewed')
    }

    with open(status_file, 'w', encoding='utf-8') as f:
        yaml.dump(status, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, width=120)


def update_level_status(level: str, module_filter: set[int] | None = None,
                        init: bool = False):
    """Update status for all modules in a level."""
    filter_desc = f" (modules: {sorted(module_filter)})" if module_filter else ""
    print(f"Updating status for {level}{filter_desc}...")

    curriculum = load_curriculum_yaml()
    if level not in curriculum.get('levels', {}):
        print(f"  Level {level} not found in curriculum.yaml")
        return

    level_data = curriculum['levels'][level]
    modules = level_data.get('modules', [])

    if not modules:
        print(f"  No modules found for {level}")
        return

    # Load or init status
    if init:
        status = {
            'level': level,
            'updated': datetime.now(timezone.utc).isoformat(),
            'summary': {'total': 0, 'planned': 0, 'content': 0, 'activities': 0, 'reviewed': 0},
            'modules': {}
        }
    else:
        status = load_status_file(level)

    # Process modules
    stats = {'planned': 0, 'content': 0, 'activities': 0, 'reviewed': 0}

    for i, slug in enumerate(modules, 1):
        if module_filter and i not in module_filter:
            continue

        module_status = determine_module_status(level, slug)
        status['modules'][slug] = module_status
        stats[module_status['status']] += 1

        # Progress indicator
        symbol = {'planned': '.', 'content': 'c', 'activities': 'a', 'reviewed': 'R'}
        print(symbol[module_status['status']], end='', flush=True)

    print()  # Newline after progress

    # Save status
    save_status_file(level, status)

    # Print summary
    total = len(modules)
    print(f"  Summary: {stats['reviewed']} reviewed, {stats['activities']} activities, "
          f"{stats['content']} content, {stats['planned']} planned")
    print(f"  Saved: {STATUS_DIR / f'{level}.yaml'}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_status.py {level|all} [module_filter]")
        print("       python scripts/update_status.py --init {level|all}")
        print(f"\nLevels: {', '.join(LEVELS)}")
        print("\nModule filter examples:")
        print("  b1 5         # Single module")
        print("  b1 1-10      # Range")
        sys.exit(1)

    init = '--init' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--init']

    if not args:
        print("Error: no level specified")
        sys.exit(1)

    level_arg = args[0].lower()
    module_filter = None

    # Parse optional module filter
    if len(args) >= 2:
        try:
            module_filter = parse_module_filter(args[1])
        except ValueError:
            print(f"Invalid module filter: {args[1]}")
            sys.exit(1)

    if level_arg == 'all':
        if module_filter:
            print("Module filter not supported with 'all'")
            sys.exit(1)
        for level in LEVELS:
            update_level_status(level, init=init)
            print()
    elif level_arg in LEVELS:
        update_level_status(level_arg, module_filter, init=init)
    else:
        print(f"Unknown level: {level_arg}")
        print(f"Available: {', '.join(LEVELS)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
