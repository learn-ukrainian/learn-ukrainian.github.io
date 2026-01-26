#!/usr/bin/env python3
"""
Migration script for V2 Architecture (Plan-Build-Status).

Part 1: Split meta.yaml files into:
- plans/{level}/{slug}.yaml (Immutable Plan)
- {level}/meta/{slug}.yaml (Mutable Build Metadata)

Part 2: Generate Status Cache (TODO)
"""

import os
import sys
import yaml
import shutil
from pathlib import Path
from datetime import datetime

# Custom YAML representer to preserve formatting
def str_representer(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_representer)

BASE_PATH = Path(__file__).parent.parent / "curriculum" / "l2-uk-en"
PLANS_PATH = BASE_PATH / "plans"

# Fields that belong in the PLAN (Immutable)
PLAN_FIELDS = [
    'title',
    'subtitle',
    'content_outline',
    'word_target',
    'vocabulary_hints',
    'activity_hints',
    'focus',
    'pedagogy',
    'prerequisites',
    'connects_to',
    'objectives',
    'learning_outcomes',
    'grammar',
    'module_type',
    'sources',
    'immersion',
    'register',
    'phase' # Phase is strictly planning
]

# Fields that belong in the BUILD METADATA (Mutable)
BUILD_FIELDS = [
    'id',
    'slug',
    'module', # identifier
    'version', # architecture version
    'naturalness',
    'build',
    'status' # sometimes used for dev status
]

def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

def migrate_module(level: str, meta_path: Path, dry_run: bool = False):
    meta_data = load_yaml(meta_path)
    if not meta_data:
        print(f"⚠️  Empty meta file: {meta_path}")
        return

    slug = meta_data.get('slug') or meta_data.get('module')
    if not slug:
        # Fallback to filename stem
        slug = meta_path.stem
        # Try to strip number prefix if present in filename but not in slug
        import re
        m = re.match(r'^\d+-(.+)$', slug)
        if m:
            slug = m.group(1)

    # Determine filename for plan
    # Maintain same filename as meta file for 1:1 mapping
    plan_filename = meta_path.name
    plan_path = PLANS_PATH / level / plan_filename

    # 1. Prepare Plan Data
    plan_data = {
        'module': meta_data.get('module', slug),
        'level': level.upper(),
        'slug': slug,
        'version': '2.0'
    }

    # Extract Plan Fields
    has_plan_data = False
    for field in PLAN_FIELDS:
        if field in meta_data:
            plan_data[field] = meta_data[field]
            has_plan_data = True

    if not has_plan_data:
        print(f"ℹ️  No planning data found in {meta_path.name}, skipping split.")
        return

    # 2. Prepare Build Data
    build_data = {
        'module': meta_data.get('module', slug),
        'level': level.upper(),
        'slug': slug,
        'version': '2.0'
    }

    # Extract Build Fields
    for field in BUILD_FIELDS:
        if field in meta_data:
            build_data[field] = meta_data[field]

    # Preserve any other fields in Build for now to avoid data loss, 
    # but exclude Plan fields
    for k, v in meta_data.items():
        if k not in PLAN_FIELDS and k not in BUILD_FIELDS:
            build_data[k] = v

    # Add build timestamp
    if 'build' not in build_data:
        build_data['build'] = {}
    if 'last_modified' not in build_data['build']:
        build_data['build']['last_modified'] = datetime.now().strftime('%Y-%m-%d')

    if dry_run:
        print(f"DRY RUN: Would split {meta_path.name}")
        print(f"  -> Plan: {plan_path} ({len(plan_data)} keys)")
        print(f"  -> Meta: {meta_path} ({len(build_data)} keys)")
    else:
        # Save Plan
        save_yaml(plan_path, plan_data)
        # Save Meta (Overwrite)
        save_yaml(meta_path, build_data)
        print(f"✅ Migrated {meta_path.name}")

def migrate_level(level: str, dry_run: bool = False):
    print(f"\n🚀 Migrating Level: {level}")
    meta_dir = BASE_PATH / level / "meta"
    
    if not meta_dir.exists():
        print(f"❌ Meta directory not found: {meta_dir}")
        return

    files = sorted(list(meta_dir.glob("*.yaml")))
    print(f"Found {len(files)} meta files.")

    for meta_file in files:
        migrate_module(level, meta_file, dry_run)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Migrate content to V2 Architecture")
    parser.add_argument("level", help="Level to migrate (e.g., b1, b2, all)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without changes")
    
    args = parser.parse_args()

    levels = [args.level]
    if args.level == 'all':
        levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'b2-hist', 'c1-bio', 'c1-hist', 'lit']
    
    for lvl in levels:
        migrate_level(lvl, args.dry_run)

if __name__ == "__main__":
    main()
