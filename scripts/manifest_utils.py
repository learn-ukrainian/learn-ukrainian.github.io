#!/usr/bin/env python3
"""
Manifest utilities for curriculum.yaml.

Provides loading, validation, and query functions for the manifest-driven
architecture. Used by generate_mdx.py, audit_module.py, and other scripts.

Usage:
    from manifest_utils import load_manifest, get_module_by_slug, validate_manifest

RFC: docs/RFC-410-MANIFEST-DRIVEN-ARCHITECTURE.md

Manifest format (RFC #410):
    version: '1.0'
    levels:
      a1:
        type: core
        modules:
          - 01-the-cyrillic-code-i    # Numbered slugs for core
          - 02-the-cyrillic-code-ii
      b2-hist:
        type: track
        modules:
          - trypillian-civilization   # Slug-only for tracks
"""

import re
import yaml
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml"
CURRICULUM_PATH = PROJECT_ROOT / "curriculum" / "l2-uk-en"

CORE_LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
LEVELS = CORE_LEVELS  # Backward compatibility
TRACKS = ['b2-hist', 'c1-hist', 'c1-bio', 'lit', 'oes', 'ruth']


@dataclass
class Module:
    """Represents a curriculum module."""
    slug: str
    title: str
    level: str
    track: str  # 'core' or track name
    local_num: int
    global_num: int
    phase: Optional[str] = None
    focus: Optional[str] = None
    tags: Optional[list[str]] = None

    @property
    def path(self) -> str:
        """URL path for this module."""
        # RFC #410: All modules use slug-based paths
        return f"/{self.level}/{self.slug}"

    @property
    def numbered_slug(self) -> str:
        """Legacy numbered filename (for compatibility during migration)."""
        return f"{self.local_num:02d}-{self.slug}"

    @property
    def file_path(self) -> Path:
        """Path to the module markdown file."""
        # Try flat track structure first: curriculum/l2-uk-en/{track}/{slug}.md
        if self.track != 'core':
            track_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / self.track / f"{self.slug}.md"
            if track_path.exists():
                return track_path

        # Try level-based structure: curriculum/l2-uk-en/{level}/{slug}.md
        slug_path = PROJECT_ROOT / "curriculum" / "l2-uk-en" / self.level / f"{self.slug}.md"
        if slug_path.exists():
            return slug_path

        # Fallback to numbered format
        return PROJECT_ROOT / "curriculum" / "l2-uk-en" / self.level / f"{self.numbered_slug}.md"


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    """Load and cache curriculum manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def clear_manifest_cache():
    """Clear cached manifest."""
    load_manifest.cache_clear()
    _load_meta_file.cache_clear()


@lru_cache(maxsize=256)
def _load_meta_file(level: str, slug: str) -> dict:
    """Load and cache meta file for a module.

    Also checks plan file for title if meta doesn't have it.
    """
    result = {}

    # First try meta file
    meta_dir = CURRICULUM_PATH / level / 'meta'
    meta_path = meta_dir / f"{slug}.yaml"

    if meta_path.exists():
        with open(meta_path) as f:
            result = yaml.safe_load(f) or {}
    else:
        # Search for matching meta file by slug field inside or filename match
        if meta_dir.exists():
            for meta_file in meta_dir.glob('*.yaml'):
                try:
                    content = yaml.safe_load(meta_file.read_text()) or {}
                    # Match by slug field or filename
                    if content.get('slug') == slug or meta_file.stem == slug:
                        result = content
                        break
                    # Handle numbered filenames matching numbered slugs
                    _, base_slug = parse_numbered_slug(slug)
                    _, file_base = parse_numbered_slug(meta_file.stem)
                    if file_base == base_slug:
                        result = content
                        break
                except Exception:
                    continue

    # If no title in meta, check plan file
    if not result.get('title'):
        plan_dir = CURRICULUM_PATH / 'plans' / level
        plan_path = plan_dir / f"{slug}.yaml"
        if plan_path.exists():
            try:
                with open(plan_path) as f:
                    plan_data = yaml.safe_load(f) or {}
                    if plan_data.get('title'):
                        result['title'] = plan_data['title']
            except Exception:
                pass

    return result


def parse_numbered_slug(slug: str) -> tuple[Optional[int], str]:
    """Parse a numbered slug into (number, base_slug)."""
    match = re.match(r'^(\d+)-(.+)$', slug)
    if match:
        return int(match.group(1)), match.group(2)
    return None, slug


def get_module_by_slug(slug: str) -> Optional[Module]:
    """Find module by slug across core and tracks."""
    manifest = load_manifest()

    # Strip number prefix for comparison
    _, target_base = parse_numbered_slug(slug)

    # Search all levels (new format uses 'levels' key)
    global_num = 0
    for level_name, level_data in manifest.get('levels', {}).items():
        if not isinstance(level_data, dict):
            continue

        is_track = level_data.get('type') == 'track'
        modules = level_data.get('modules', [])

        for local_num, mod_slug in enumerate(modules, 1):
            if not is_track:
                global_num += 1

            # Modules in new format are just slug strings
            _, mod_base = parse_numbered_slug(mod_slug)

            if mod_slug == slug or mod_base == target_base:
                meta = _load_meta_file(level_name, mod_slug)
                return Module(
                    slug=mod_base,  # Store base slug without number prefix
                    title=meta.get('title', mod_base),
                    level=level_name,
                    track=level_name if is_track else 'core',
                    local_num=local_num,
                    global_num=global_num if not is_track else 0,
                    phase=meta.get('phase'),
                    focus=meta.get('focus'),
                    tags=meta.get('tags')
                )

    return None


def get_modules_for_level(level: str) -> list[Module]:
    """Get ordered list of modules for a level or track."""
    manifest = load_manifest()
    modules = []

    level_data = manifest.get('levels', {}).get(level, {})
    if not level_data:
        return []

    is_track = level_data.get('type') == 'track'
    mod_slugs = level_data.get('modules', [])

    # Calculate global offset for core levels
    global_offset = 0
    if not is_track:
        for lvl in CORE_LEVELS:
            if lvl == level:
                break
            lvl_data = manifest.get('levels', {}).get(lvl, {})
            global_offset += len(lvl_data.get('modules', []))

    for local_num, mod_slug in enumerate(mod_slugs, 1):
        _, base_slug = parse_numbered_slug(mod_slug)
        meta = _load_meta_file(level, mod_slug)

        modules.append(Module(
            slug=base_slug,
            title=meta.get('title', base_slug),
            level=level,
            track=level if is_track else 'core',
            local_num=local_num,
            global_num=(global_offset + local_num) if not is_track else 0,
            phase=meta.get('phase'),
            focus=meta.get('focus'),
            tags=meta.get('tags')
        ))

    return modules


def get_module_by_number(level: str, num: int) -> Optional[Module]:
    """Get module by level and local number."""
    modules = get_modules_for_level(level)
    if 1 <= num <= len(modules):
        return modules[num - 1]
    return None


def resolve_slug_link(slug: str) -> tuple[str, str]:
    """Resolve a slug to title and path."""
    module = get_module_by_slug(slug)
    if module:
        return (module.title, module.path)
    raise ValueError(f"Unknown module slug: {slug}")


def validate_manifest() -> list[str]:
    """Validate manifest integrity."""
    errors = []
    manifest = load_manifest()
    seen_slugs = set()

    for level_name, level_data in manifest.get('levels', {}).items():
        if not isinstance(level_data, dict):
            continue

        modules = level_data.get('modules', [])
        level_type = level_data.get('type', 'core')
        context = f"{level_type}.{level_name}"

        for i, mod_slug in enumerate(modules):
            if not mod_slug:
                errors.append(f"{context}[{i}]: missing slug")
                continue

            _, base_slug = parse_numbered_slug(mod_slug)
            if base_slug in seen_slugs:
                errors.append(f"{context}[{i}]: duplicate slug '{mod_slug}'")
            seen_slugs.add(base_slug)

    return errors


def validate_filesystem_match(level: str = None) -> list[str]:
    """Validate that manifest matches filesystem state.

    Checks:
    - Every module in manifest has a corresponding .md file
    - Every .md file has a corresponding manifest entry

    Args:
        level: Optional level to check (None = all levels)

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    manifest = load_manifest()

    levels_to_check = [level] if level else list(manifest.get('levels', {}).keys())

    for lvl in levels_to_check:
        level_data = manifest.get('levels', {}).get(lvl, {})
        if not level_data:
            errors.append(f"{lvl}: not found in manifest")
            continue

        level_dir = CURRICULUM_PATH / lvl
        if not level_dir.exists():
            errors.append(f"{lvl}: directory not found at {level_dir}")
            continue

        # Get manifest slugs (clean of comments)
        manifest_slugs = set()
        for mod_slug in level_data.get('modules', []):
            if isinstance(mod_slug, str):
                _, base_slug = parse_numbered_slug(mod_slug)
                manifest_slugs.add(base_slug)

        # Get filesystem slugs
        filesystem_slugs = set()

        # Check for numbered files (core levels): 01-slug.md
        for md_file in level_dir.glob('[0-9]*-*.md'):
            match = re.match(r'^\d+-(.+)\.md$', md_file.name)
            if match:
                filesystem_slugs.add(match.group(1))

        # Check for slug-only files (tracks): slug.md
        for md_file in level_dir.glob('*.md'):
            if not md_file.name[0].isdigit() and not md_file.name.startswith('_'):
                filesystem_slugs.add(md_file.stem)

        # Find mismatches
        in_manifest_not_fs = manifest_slugs - filesystem_slugs
        in_fs_not_manifest = filesystem_slugs - manifest_slugs

        for slug in sorted(in_manifest_not_fs):
            errors.append(f"{lvl}: manifest has '{slug}' but no .md file found")

        for slug in sorted(in_fs_not_manifest):
            errors.append(f"{lvl}: filesystem has '{slug}.md' but not in manifest")

    return errors


def get_manifest_stats() -> dict:
    """Get statistics about the manifest."""
    manifest = load_manifest()

    stats = {
        'version': manifest.get('version'),
        'levels': {},
        'total_modules': 0,
        'tracks': {}
    }

    for level_name, level_data in manifest.get('levels', {}).items():
        if not isinstance(level_data, dict):
            continue

        count = len(level_data.get('modules', []))
        level_type = level_data.get('type', 'core')

        if level_type == 'track':
            stats['tracks'][level_name] = count
        else:
            stats['levels'][level_name] = count
            stats['total_modules'] += count

    return stats


def main():
    """CLI for testing manifest utilities."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  .venv/bin/python scripts/manifest_utils.py validate")
        print("  .venv/bin/python scripts/manifest_utils.py validate-fs [level]")
        print("  .venv/bin/python scripts/manifest_utils.py stats")
        print("  .venv/bin/python scripts/manifest_utils.py lookup <slug>")
        print("  .venv/bin/python scripts/manifest_utils.py level <level>")
        return

    cmd = sys.argv[1]

    if cmd == 'validate':
        errors = validate_manifest()
        if errors:
            print(f"Found {len(errors)} errors:\n")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            print("Manifest is valid!")

    elif cmd == 'validate-fs':
        level = sys.argv[2] if len(sys.argv) > 2 else None
        errors = validate_filesystem_match(level)
        if errors:
            print(f"Found {len(errors)} filesystem mismatches:\n")
            for err in errors:
                print(f"  - {err}")
            sys.exit(1)
        else:
            scope = level or "all levels"
            print(f"Filesystem matches manifest for {scope}!")

    elif cmd == 'stats':
        stats = get_manifest_stats()
        print(f"Manifest version: {stats['version']}")
        print(f"\nCore modules by level:")
        for level, count in stats['levels'].items():
            print(f"  {level.upper()}: {count}")
        print(f"\nTotal core: {stats['total_modules']}")

        if stats['tracks']:
            print(f"\nTracks:")
            for track, count in stats['tracks'].items():
                print(f"  {track}: {count}")

    elif cmd == 'lookup' and len(sys.argv) > 2:
        slug = sys.argv[2]
        module = get_module_by_slug(slug)
        if module:
            print(f"Found: {module.title}")
            print(f"  Level: {module.level}")
            print(f"  Number: {module.local_num} (global: {module.global_num})")
            print(f"  Path: {module.path}")
            print(f"  File: {module.file_path}")
            if module.phase:
                print(f"  Phase: {module.phase}")
            if module.focus:
                print(f"  Focus: {module.focus}")
        else:
            print(f"Module not found: {slug}")
            sys.exit(1)

    elif cmd == 'level' and len(sys.argv) > 2:
        level = sys.argv[2].lower()
        modules = get_modules_for_level(level)
        print(f"{level.upper()} modules ({len(modules)}):\n")
        for mod in modules:
            print(f"  {mod.local_num:02d}. {mod.title} [{mod.slug}]")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()
