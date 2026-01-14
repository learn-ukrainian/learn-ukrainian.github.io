#!/usr/bin/env python3
"""
Manifest utilities for curriculum.yaml.

Provides loading, validation, and query functions for the manifest-driven
architecture. Used by generate_mdx.py, audit_module.py, and other scripts.

Usage:
    from manifest_utils import load_manifest, get_module_by_slug, validate_manifest

RFC: docs/RFC-410-MANIFEST-DRIVEN-ARCHITECTURE.md
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

LEVELS = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']


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
        return f"/{self.level}/module-{self.local_num:02d}"

    @property
    def numbered_slug(self) -> str:
        """Current numbered filename (for compatibility)."""
        return f"{self.local_num:02d}-{self.slug}"

    @property
    def file_path(self) -> Path:
        """Path to the module markdown file."""
        return PROJECT_ROOT / "curriculum" / "l2-uk-en" / self.level / f"{self.numbered_slug}.md"


@lru_cache(maxsize=1)
def load_manifest() -> dict:
    """Load and cache curriculum manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found: {MANIFEST_PATH}")

    with open(MANIFEST_PATH) as f:
        return yaml.safe_load(f)


def clear_manifest_cache():
    """Clear the cached manifest (for testing or after updates)."""
    load_manifest.cache_clear()


def get_module_by_slug(slug: str) -> Optional[Module]:
    """
    Find module by slug across all levels and tracks.

    Args:
        slug: The module slug (e.g., 'the-cyrillic-code-i')

    Returns:
        Module object or None if not found
    """
    manifest = load_manifest()
    global_num = 0

    # Search core levels
    for level in LEVELS:
        level_data = manifest.get('core', {}).get(level, {})
        modules = level_data.get('modules', [])

        for local_num, mod in enumerate(modules, 1):
            global_num += 1
            if mod.get('slug') == slug:
                return Module(
                    slug=slug,
                    title=mod.get('title', ''),
                    level=level,
                    track='core',
                    local_num=local_num,
                    global_num=global_num,
                    phase=mod.get('phase'),
                    focus=mod.get('focus'),
                    tags=mod.get('tags')
                )

    # Search tracks
    for track_name, track_data in manifest.get('tracks', {}).items():
        if track_name.startswith('_'):  # Skip comments
            continue
        modules = track_data.get('modules', [])

        for local_num, mod in enumerate(modules, 1):
            if mod.get('slug') == slug:
                return Module(
                    slug=slug,
                    title=mod.get('title', ''),
                    level=track_name,
                    track=track_name,
                    local_num=local_num,
                    global_num=0,  # Tracks don't have global numbers
                    phase=mod.get('phase'),
                    focus=mod.get('focus'),
                    tags=mod.get('tags')
                )

    return None


def get_modules_for_level(level: str) -> list[Module]:
    """
    Get ordered list of modules for a level.

    Args:
        level: Level code (e.g., 'a1', 'b2')

    Returns:
        List of Module objects in curriculum order
    """
    manifest = load_manifest()
    modules = []

    # Calculate global offset
    global_offset = 0
    for lvl in LEVELS:
        if lvl == level:
            break
        level_data = manifest.get('core', {}).get(lvl, {})
        global_offset += len(level_data.get('modules', []))

    # Get modules for this level
    level_data = manifest.get('core', {}).get(level, {})
    for local_num, mod in enumerate(level_data.get('modules', []), 1):
        modules.append(Module(
            slug=mod.get('slug'),
            title=mod.get('title', ''),
            level=level,
            track='core',
            local_num=local_num,
            global_num=global_offset + local_num,
            phase=mod.get('phase'),
            focus=mod.get('focus'),
            tags=mod.get('tags')
        ))

    return modules


def get_module_by_number(level: str, num: int) -> Optional[Module]:
    """
    Get module by level and local number.

    Args:
        level: Level code (e.g., 'a1')
        num: Local module number (1-based)

    Returns:
        Module object or None
    """
    modules = get_modules_for_level(level)
    if 1 <= num <= len(modules):
        return modules[num - 1]
    return None


def resolve_slug_link(slug: str) -> tuple[str, str]:
    """
    Resolve a slug to its title and path.

    Args:
        slug: Module slug

    Returns:
        Tuple of (title, path) or raises ValueError if not found
    """
    module = get_module_by_slug(slug)
    if module:
        return (module.title, module.path)
    raise ValueError(f"Unknown module slug: {slug}")


def validate_manifest() -> list[str]:
    """
    Validate manifest integrity.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    try:
        manifest = load_manifest()
    except Exception as e:
        return [f"Failed to load manifest: {e}"]

    seen_slugs = set()

    def check_slug(slug: str, context: str):
        # Check format
        if not slug:
            errors.append(f"{context}: missing slug")
            return

        if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
            errors.append(f"{context}: invalid slug format '{slug}'")

        # Check uniqueness
        if slug in seen_slugs:
            errors.append(f"{context}: duplicate slug '{slug}'")
        seen_slugs.add(slug)

        # Check length
        if len(slug) > 60:
            errors.append(f"{context}: slug too long ({len(slug)} chars): '{slug}'")

    def check_modules(modules: list, context: str):
        for i, mod in enumerate(modules):
            slug = mod.get('slug')
            check_slug(slug, f"{context}[{i}]")

            if not mod.get('title'):
                errors.append(f"{context}[{i}] ({slug}): missing title")

            # Check focus if present
            valid_focus = [
                # Core types
                'grammar', 'vocabulary', 'cultural', 'checkpoint', 'integration', 'review',
                # Content types
                'history', 'biography', 'literature', 'phraseology',
                # Skills & professional
                'skills', 'professional', 'academic', 'practical',
                # Cultural specializations
                'folk-culture', 'fine-arts', 'culture',
                # Style & linguistics
                'style', 'sociolinguistics', 'society',
                # Project/synthesis
                'project', 'synthesis', 'practice', 'domain', 'genre',
                # Bridge modules (B1 metalanguage)
                'bridge'
            ]
            focus = mod.get('focus')
            if focus and focus not in valid_focus:
                errors.append(f"{context}[{i}] ({slug}): invalid focus '{focus}'")

    # Check core levels
    for level in LEVELS:
        level_data = manifest.get('core', {}).get(level, {})
        modules = level_data.get('modules', [])
        check_modules(modules, f"core.{level}")

    # Check tracks
    for track_name, track_data in manifest.get('tracks', {}).items():
        if track_name.startswith('_'):
            continue
        if isinstance(track_data, dict):
            modules = track_data.get('modules', [])
            check_modules(modules, f"tracks.{track_name}")

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

    for level in LEVELS:
        level_data = manifest.get('core', {}).get(level, {})
        count = len(level_data.get('modules', []))
        stats['levels'][level] = count
        stats['total_modules'] += count

    for track_name, track_data in manifest.get('tracks', {}).items():
        if track_name.startswith('_'):
            continue
        if isinstance(track_data, dict):
            stats['tracks'][track_name] = len(track_data.get('modules', []))

    return stats


# =============================================================================
# CLI for testing
# =============================================================================

def main():
    """CLI for testing manifest utilities."""
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  .venv/bin/python scripts/manifest_utils.py validate")
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

    elif cmd == 'stats':
        stats = get_manifest_stats()
        print(f"Manifest version: {stats['version']}")
        print(f"\nCore modules by level:")
        for level, count in stats['levels'].items():
            print(f"  {level.upper()}: {count}")
        print(f"\nTotal: {stats['total_modules']}")

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
