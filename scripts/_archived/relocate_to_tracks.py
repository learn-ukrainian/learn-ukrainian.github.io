#!/usr/bin/env python3
"""
Relocate modules to specialized tracks.

Phase C of RFC #409 (Curriculum Reorganization):
- B2 M71-131 → b2-hist (61 modules, renumbered 01-61)
- C1 M36-131 → c1-bio (96 modules, renumbered 01-96)

Usage:
    .venv/bin/python scripts/relocate_to_tracks.py --dry-run  # Preview changes
    .venv/bin/python scripts/relocate_to_tracks.py            # Execute relocation
"""

import re
import shutil
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
MANIFEST_PATH = CURRICULUM_DIR / "curriculum.yaml"

# Relocation definitions
RELOCATIONS = [
    {
        'name': 'B2 History → b2-hist',
        'source_level': 'b2',
        'target_track': 'b2-hist',
        'start_module': 71,
        'end_module': 131,  # Inclusive
        'description': 'Ukrainian History modules'
    },
    {
        'name': 'C1 Biography → c1-bio',
        'source_level': 'c1',
        'target_track': 'c1-bio',
        'start_module': 36,
        'end_module': 131,  # Inclusive
        'description': 'Famous Ukrainians biography modules'
    }
]

SIDECAR_DIRS = ['activities', 'meta', 'vocabulary', 'audit']


def get_module_files(level_dir: Path, module_num: int) -> list[tuple[Path, str]]:
    """Get all files for a module (main .md + sidecars)."""
    files = []

    # Find main .md file
    pattern = f"{module_num:02d}-*.md" if module_num < 100 else f"{module_num}-*.md"
    md_files = list(level_dir.glob(pattern))

    if not md_files:
        # Try 3-digit pattern
        pattern = f"{module_num:03d}-*.md"
        md_files = list(level_dir.glob(pattern))

    for md_file in md_files:
        files.append((md_file, 'md'))
        stem = md_file.stem  # e.g., "71-trypillian-civilization"

        # Find sidecar files
        for sidecar_dir in SIDECAR_DIRS:
            sidecar_path = level_dir / sidecar_dir / f"{stem}.yaml"
            if sidecar_path.exists():
                files.append((sidecar_path, sidecar_dir))

    return files


def extract_slug(filename: str) -> str:
    """Extract slug from numbered filename."""
    match = re.match(r'^\d+-(.+)\.(md|yaml)$', filename)
    if match:
        return match.group(1)
    return None


def relocate_module(
    source_file: Path,
    file_type: str,
    target_dir: Path,
    new_number: int,
    dry_run: bool = True
) -> tuple[Path, Path]:
    """Relocate a single file to the target directory with new numbering."""
    slug = extract_slug(source_file.name)
    if not slug:
        return None, None

    # Determine new filename
    ext = source_file.suffix
    new_filename = f"{new_number:02d}-{slug}{ext}"

    # Determine target path
    if file_type == 'md':
        target_path = target_dir / new_filename
    else:
        target_path = target_dir / file_type / new_filename

    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_file), str(target_path))

    return source_file, target_path


def update_module_frontmatter(file_path: Path, new_module_id: str, dry_run: bool = True):
    """Update module ID in frontmatter."""
    if dry_run or not file_path.exists():
        return

    content = file_path.read_text(encoding='utf-8')

    # Update module: field in frontmatter
    content = re.sub(
        r'^(module:\s*)[^\n]+',
        f'\\g<1>{new_module_id}',
        content,
        flags=re.MULTILINE
    )

    file_path.write_text(content, encoding='utf-8')


def update_meta_module_id(meta_path: Path, new_module_id: str, dry_run: bool = True):
    """Update module ID in meta YAML file."""
    if dry_run or not meta_path.exists():
        return

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = yaml.safe_load(f) or {}

    meta['module'] = new_module_id

    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def run_relocation(dry_run: bool = True):
    """Execute all relocations."""
    print(f"{'[DRY RUN] ' if dry_run else ''}Starting module relocation...\n")

    all_moves = []
    manifest_updates = {}

    for reloc in RELOCATIONS:
        print(f"=== {reloc['name']} ===")

        source_dir = CURRICULUM_DIR / reloc['source_level']
        target_dir = CURRICULUM_DIR / reloc['target_track']

        if not source_dir.exists():
            print(f"  Source directory not found: {source_dir}")
            continue

        moved_modules = []
        new_number = 1

        for module_num in range(reloc['start_module'], reloc['end_module'] + 1):
            files = get_module_files(source_dir, module_num)

            if not files:
                print(f"  Module {module_num}: No files found")
                continue

            # Get module info from first file
            main_file = files[0][0]
            slug = extract_slug(main_file.name)
            new_module_id = f"{reloc['target_track']}-{new_number:02d}"

            print(f"  M{module_num:03d} → {reloc['target_track']}/M{new_number:02d} ({slug})")

            # Relocate all files
            for source_file, file_type in files:
                src, dst = relocate_module(source_file, file_type, target_dir, new_number, dry_run)
                if src and dst:
                    all_moves.append((src, dst, file_type, new_module_id))

            # Track for manifest update
            moved_modules.append({
                'old_num': module_num,
                'new_num': new_number,
                'slug': slug,
                'new_module_id': new_module_id
            })

            new_number += 1

        manifest_updates[reloc['target_track']] = {
            'source_level': reloc['source_level'],
            'modules': moved_modules
        }

        print(f"  Total: {len(moved_modules)} modules to relocate\n")

    # Update frontmatter and meta files
    if not dry_run:
        print("Updating module IDs in files...")
        for src, dst, file_type, new_module_id in all_moves:
            if file_type == 'md':
                update_module_frontmatter(dst, new_module_id, dry_run)
            elif file_type == 'meta':
                update_meta_module_id(dst, new_module_id, dry_run)

    # Summary
    print("=" * 60)
    print(f"Total files to move: {len(all_moves)}")
    print(f"Total modules to relocate: {sum(len(u['modules']) for u in manifest_updates.values())}")

    if dry_run:
        print("\n[DRY RUN] No files were moved. Run without --dry-run to execute.")
    else:
        print("\nRelocation complete! Remember to:")
        print("  1. Run: .venv/bin/python scripts/generate_curriculum_yaml.py")
        print("  2. Verify: .venv/bin/python scripts/manifest_utils.py validate")
        print("  3. Commit the changes")

    return manifest_updates


def main():
    import sys

    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv

    if not dry_run:
        print("WARNING: This will move files. Use --dry-run to preview first.")
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            return

    run_relocation(dry_run=dry_run)


if __name__ == '__main__':
    main()
