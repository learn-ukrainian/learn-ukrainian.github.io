#!/usr/bin/env python3
"""
Generate curriculum.yaml from current filesystem state.

This script reads all module meta files and generates a manifest
that captures the current curriculum structure.

Usage:
    .venv/bin/python scripts/generate_curriculum_yaml.py
"""

import re
import yaml
from pathlib import Path
from collections import OrderedDict

# Custom YAML representer for ordered output
def represent_ordereddict(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())

yaml.add_representer(OrderedDict, represent_ordereddict)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CURRICULUM_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en"
OUTPUT_FILE = CURRICULUM_DIR / "curriculum.yaml"

LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']


def extract_slug(filename: str) -> str:
    """Extract slug from numbered filename."""
    match = re.match(r'^(\d{2,3})-(.+)\.(md|yaml)$', filename)
    if match:
        return match.group(2)
    return None


def extract_number(filename: str) -> int:
    """Extract number from filename."""
    match = re.match(r'^(\d{2,3})-', filename)
    if match:
        return int(match.group(1))
    return 999


def load_meta(meta_path: Path) -> dict:
    """Load module metadata from YAML file."""
    try:
        with open(meta_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"  Warning: Could not load {meta_path}: {e}")
        return {}


def get_modules_for_level(level: str) -> list[dict]:
    """Get all modules for a level, ordered by number."""
    level_dir = CURRICULUM_DIR / level
    meta_dir = level_dir / "meta"

    modules = []

    # Get all .md files in level directory
    md_files = sorted(level_dir.glob('[0-9]*.md'), key=lambda p: extract_number(p.name))

    for md_file in md_files:
        slug = extract_slug(md_file.name)
        if not slug:
            continue

        # Try to load meta
        meta_file = meta_dir / f"{md_file.stem}.yaml"
        meta = load_meta(meta_file) if meta_file.exists() else {}

        module = OrderedDict()
        module['slug'] = slug
        module['title'] = meta.get('title', slug.replace('-', ' ').title())

        if meta.get('phase'):
            module['phase'] = meta['phase']
        if meta.get('focus'):
            module['focus'] = meta['focus']
        if meta.get('tags'):
            module['tags'] = meta['tags']

        modules.append(module)

    return modules


def generate_manifest() -> dict:
    """Generate complete curriculum manifest."""
    manifest = OrderedDict()
    manifest['version'] = "2.0"
    manifest['language_pair'] = "uk-en"
    manifest['name'] = "Ukrainian for English Speakers"

    # Settings
    manifest['settings'] = OrderedDict()
    manifest['settings']['default_transliteration'] = True

    # Core path
    manifest['core'] = OrderedDict()

    level_names = {
        'a1': 'A1 - Beginner',
        'a2': 'A2 - Elementary',
        'b1': 'B1 - Intermediate',
        'b2': 'B2 - Upper Intermediate',
        'c1': 'C1 - Advanced',
        'c2': 'C2 - Mastery'
    }

    for level in LEVELS:
        print(f"Processing {level.upper()}...")
        modules = get_modules_for_level(level)

        level_data = OrderedDict()
        level_data['name'] = level_names[level]
        level_data['modules'] = modules

        manifest['core'][level] = level_data
        print(f"  Found {len(modules)} modules")

    # Tracks placeholder (for future)
    manifest['tracks'] = OrderedDict()
    manifest['tracks']['_comment'] = "Specialized tracks will be added after reorganization (#409)"

    return manifest


def main():
    print("Generating curriculum.yaml from current state...\n")

    manifest = generate_manifest()

    # Write YAML with nice formatting
    with open(OUTPUT_FILE, 'w') as f:
        yaml.dump(manifest, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False,
                  width=100)

    print(f"\nWritten to: {OUTPUT_FILE}")

    # Summary
    total = sum(len(manifest['core'][level]['modules']) for level in LEVELS)
    print(f"Total modules: {total}")


if __name__ == '__main__':
    main()
