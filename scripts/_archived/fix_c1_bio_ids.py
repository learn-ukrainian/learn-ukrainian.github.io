#!/usr/bin/env python3
"""
Fix C1-BIO module IDs to match curriculum.yaml order.

The curriculum.yaml defines the canonical order (chronological by birth date).
This script updates all meta and plan files to have consistent IDs.

Usage:
    .venv/bin/python scripts/fix_c1_bio_ids.py --dry-run  # Preview changes
    .venv/bin/python scripts/fix_c1_bio_ids.py            # Apply changes
"""

import yaml
import re
import argparse
from pathlib import Path

# Paths
CURRICULUM_PATH = Path('curriculum/l2-uk-en/curriculum.yaml')
META_DIR = Path('curriculum/l2-uk-en/c1-bio/meta')
PLAN_DIR = Path('curriculum/l2-uk-en/plans/c1-bio')
STATUS_DIR = Path('curriculum/l2-uk-en/c1-bio/status')


def load_curriculum_order():
    """Load the canonical module order from curriculum.yaml."""
    with open(CURRICULUM_PATH) as f:
        curriculum = yaml.safe_load(f)
    return curriculum['levels']['c1-bio']['modules']


def fix_meta_file(slug: str, position: int, dry_run: bool) -> dict:
    """Fix the module ID in a meta file."""
    meta_path = META_DIR / f'{slug}.yaml'
    if not meta_path.exists():
        return {'slug': slug, 'status': 'NO_META_FILE', 'old': None, 'new': None}

    new_id = f'c1-bio-{position:03d}'

    with open(meta_path) as f:
        content = f.read()

    # Parse to get old values
    try:
        meta = yaml.safe_load(content)
        old_module = meta.get('module', 'N/A')
        old_id = meta.get('id', 'N/A')
    except:
        return {'slug': slug, 'status': 'YAML_ERROR', 'old': None, 'new': new_id}

    # Check if already correct
    if old_module == new_id:
        return {'slug': slug, 'status': 'OK', 'old': old_module, 'new': new_id}

    # Replace module and id fields
    new_content = re.sub(
        r'^module:\s*.*$',
        f'module: {new_id}',
        content,
        flags=re.MULTILINE
    )
    new_content = re.sub(
        r'^id:\s*.*$',
        f'id: {new_id}',
        new_content,
        flags=re.MULTILINE
    )

    if not dry_run:
        with open(meta_path, 'w') as f:
            f.write(new_content)

    return {'slug': slug, 'status': 'FIXED', 'old': old_module, 'new': new_id}


def fix_plan_file(slug: str, position: int, dry_run: bool) -> dict:
    """Fix the module ID in a plan file."""
    plan_path = PLAN_DIR / f'{slug}.yaml'
    if not plan_path.exists():
        return {'slug': slug, 'status': 'NO_PLAN_FILE', 'old': None, 'new': None}

    new_id = f'c1-bio-{position:03d}'

    with open(plan_path) as f:
        content = f.read()

    # Parse to get old value
    try:
        plan = yaml.safe_load(content)
        old_module = plan.get('module', 'N/A') if plan else 'N/A'
    except:
        old_module = 'YAML_ERROR'

    # Check if already correct
    if old_module == new_id:
        return {'slug': slug, 'status': 'OK', 'old': old_module, 'new': new_id}

    # Replace module field
    new_content = re.sub(
        r'^module:\s*.*$',
        f'module: {new_id}',
        content,
        flags=re.MULTILINE
    )

    if not dry_run:
        with open(plan_path, 'w') as f:
            f.write(new_content)

    return {'slug': slug, 'status': 'FIXED', 'old': old_module, 'new': new_id}


def fix_status_file(slug: str, position: int, dry_run: bool) -> dict:
    """Fix the module ID in a status JSON file."""
    import json

    status_path = STATUS_DIR / f'{slug}.json'
    if not status_path.exists():
        return {'slug': slug, 'status': 'NO_STATUS_FILE', 'old': None, 'new': None}

    new_id = f'c1-bio-{position:03d}'

    with open(status_path) as f:
        data = json.load(f)

    old_module = data.get('module', 'N/A')

    if old_module == new_id:
        return {'slug': slug, 'status': 'OK', 'old': old_module, 'new': new_id}

    data['module'] = new_id

    if not dry_run:
        with open(status_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    return {'slug': slug, 'status': 'FIXED', 'old': old_module, 'new': new_id}


def main():
    parser = argparse.ArgumentParser(description='Fix C1-BIO module IDs')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()

    modules = load_curriculum_order()

    print(f"{'DRY RUN - ' if args.dry_run else ''}Fixing C1-BIO module IDs")
    print(f"Found {len(modules)} modules in curriculum.yaml\n")

    meta_results = []
    plan_results = []
    status_results = []

    for i, slug in enumerate(modules, 1):
        meta_results.append(fix_meta_file(slug, i, args.dry_run))
        plan_results.append(fix_plan_file(slug, i, args.dry_run))
        status_results.append(fix_status_file(slug, i, args.dry_run))

    # Report
    print("=== META FILE CHANGES ===")
    fixed_meta = [r for r in meta_results if r['status'] == 'FIXED']
    print(f"Fixed: {len(fixed_meta)}, OK: {len([r for r in meta_results if r['status'] == 'OK'])}, Missing: {len([r for r in meta_results if r['status'] == 'NO_META_FILE'])}")
    if fixed_meta:
        print("\nChanges:")
        for r in fixed_meta[:20]:
            print(f"  {r['slug']}: {r['old']} → {r['new']}")
        if len(fixed_meta) > 20:
            print(f"  ... and {len(fixed_meta) - 20} more")

    print("\n=== PLAN FILE CHANGES ===")
    fixed_plan = [r for r in plan_results if r['status'] == 'FIXED']
    print(f"Fixed: {len(fixed_plan)}, OK: {len([r for r in plan_results if r['status'] == 'OK'])}, Missing: {len([r for r in plan_results if r['status'] == 'NO_PLAN_FILE'])}")
    if fixed_plan:
        print("\nChanges:")
        for r in fixed_plan[:20]:
            print(f"  {r['slug']}: {r['old']} → {r['new']}")
        if len(fixed_plan) > 20:
            print(f"  ... and {len(fixed_plan) - 20} more")

    print("\n=== STATUS FILE CHANGES ===")
    fixed_status = [r for r in status_results if r['status'] == 'FIXED']
    print(f"Fixed: {len(fixed_status)}, OK: {len([r for r in status_results if r['status'] == 'OK'])}, Missing: {len([r for r in status_results if r['status'] == 'NO_STATUS_FILE'])}")

    if args.dry_run:
        print("\n⚠️  DRY RUN - No changes made. Run without --dry-run to apply.")
    else:
        print(f"\n✅ Fixed {len(fixed_meta)} meta, {len(fixed_plan)} plan, {len(fixed_status)} status files.")


if __name__ == '__main__':
    main()
