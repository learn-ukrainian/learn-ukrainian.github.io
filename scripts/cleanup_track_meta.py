#!/usr/bin/env python3
"""
Cleanup track meta files per RFC #410 decisions:
1. Remove `module:` field from all track meta files
2. Strip number prefixes from `slug:` fields (e.g., 127-aneksiia-krymu → aneksiia-krymu)

Tracks affected: b2-hist, c1-bio, lit
"""

import re
from pathlib import Path


def clean_meta_file(filepath: Path) -> tuple[bool, list[str]]:
    """
    Clean a single meta YAML file.
    Returns (was_modified, list_of_changes).
    """
    content = filepath.read_text()
    changes = []
    modified = False

    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # Remove module: field entirely
        if line.strip().startswith('module:'):
            changes.append(f"Removed: {line.strip()}")
            modified = True
            continue

        # Strip number prefix from slug field
        slug_match = re.match(r'^(\s*slug:\s*)(\d+-)?(.+)$', line)
        if slug_match:
            indent = slug_match.group(1)
            number_prefix = slug_match.group(2)
            slug_value = slug_match.group(3)

            if number_prefix:
                new_line = f"{indent}{slug_value}"
                changes.append(f"Slug: {line.strip()} → slug: {slug_value}")
                new_lines.append(new_line)
                modified = True
                continue

        new_lines.append(line)

    if modified:
        # Remove any resulting double blank lines
        new_content = '\n'.join(new_lines)
        new_content = re.sub(r'\n\n\n+', '\n\n', new_content)
        filepath.write_text(new_content)

    return modified, changes


def main():
    base_path = Path(__file__).parent.parent / 'curriculum' / 'l2-uk-en'

    tracks = ['b2-hist', 'c1-bio', 'lit']

    total_modified = 0
    total_changes = []

    for track in tracks:
        meta_dir = base_path / track / 'meta'
        if not meta_dir.exists():
            print(f"⚠️  {track}/meta not found, skipping")
            continue

        print(f"\n📁 Processing {track}/meta...")
        track_modified = 0

        for yaml_file in sorted(meta_dir.glob('*.yaml')):
            was_modified, changes = clean_meta_file(yaml_file)
            if was_modified:
                track_modified += 1
                total_modified += 1
                print(f"  ✓ {yaml_file.name}")
                for change in changes:
                    print(f"      {change}")
                    total_changes.append(f"{track}/{yaml_file.name}: {change}")

    print(f"\n{'='*60}")
    print(f"✅ Modified {total_modified} files across {len(tracks)} tracks")
    print(f"   Total changes: {len(total_changes)}")


if __name__ == '__main__':
    main()
