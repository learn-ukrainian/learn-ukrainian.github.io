#!/usr/bin/env python3
"""
Generate curriculum.yaml manifest from existing meta files.
Per RFC #410: Single manifest, slug-only for tracks, hard cutover.
"""

import re
from pathlib import Path
import yaml

from slug_utils import to_bare_slug


def extract_module_info(meta_file: Path) -> dict:
    """Extract slug and title from a meta YAML file."""
    content = yaml.safe_load(meta_file.read_text())

    # Get slug - either from slug field or derive from filename
    slug = content.get('slug')
    if not slug:
        # Derive from filename: 01-some-name.yaml -> some-name
        slug = to_bare_slug(meta_file.stem)

    return {
        'slug': slug,
        'title': content.get('title', slug),
        'filename': meta_file.stem,
    }


def sort_key(filename: str) -> tuple:
    """Sort key that handles numeric prefixes properly."""
    match = re.match(r'^(\d+)-(.+)$', filename)
    if match:
        # Numeric prefix: sort by number first, then by rest
        return (0, int(match.group(1)), match.group(2))
    else:
        # No numeric prefix: sort alphabetically after numbered ones
        return (1, 0, filename)


def get_modules_for_level(base_path: Path, level: str, is_track: bool = False) -> list[dict]:
    """Get all modules for a level, sorted appropriately."""
    meta_dir = base_path / level / 'meta'
    if not meta_dir.exists():
        return []

    modules = []
    meta_files = list(meta_dir.glob('*.yaml'))

    # Sort: core levels by numeric prefix, tracks alphabetically
    if is_track:
        meta_files.sort(key=lambda f: f.stem)
    else:
        meta_files.sort(key=lambda f: sort_key(f.stem))

    for meta_file in meta_files:
        info = extract_module_info(meta_file)
        modules.append(info)

    return modules


def generate_manifest(base_path: Path) -> dict:
    """Generate the full curriculum manifest."""

    manifest = {
        'version': '1.0',
        'description': 'L2 Ukrainian-English Curriculum Manifest (RFC #410)',
        'levels': {}
    }

    # Core levels with numbered modules
    core_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']

    # Tracks with slug-only modules
    tracks = ['b2-hist', 'c1-bio', 'lit']

    # Process core levels
    for level in core_levels:
        modules = get_modules_for_level(base_path, level, is_track=False)
        if modules:
            manifest['levels'][level] = {
                'type': 'core',
                'modules': [m['slug'] for m in modules]
            }
            print(f"  {level}: {len(modules)} modules")

    # Process tracks
    for track in tracks:
        modules = get_modules_for_level(base_path, track, is_track=True)
        if modules:
            manifest['levels'][track] = {
                'type': 'track',
                'modules': [m['slug'] for m in modules]
            }
            print(f"  {track}: {len(modules)} modules")

    return manifest


def main():
    base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'
    output_path = base_path / 'curriculum.yaml'

    print("Generating curriculum manifest...")
    print()

    manifest = generate_manifest(base_path)

    # Calculate totals
    total = sum(len(level['modules']) for level in manifest['levels'].values())

    print()
    print(f"Total: {total} modules across {len(manifest['levels'])} levels/tracks")
    print()

    # Write manifest
    with open(output_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Written to: {output_path}")


if __name__ == '__main__':
    main()
