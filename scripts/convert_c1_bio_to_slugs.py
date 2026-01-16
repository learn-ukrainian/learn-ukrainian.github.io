#!/usr/bin/env python3
"""
Convert C1-BIO to pure slugs and reorder by birth date.

This script:
1. Extracts birth dates from markdown content
2. Renames files from numbered format to pure slugs
3. Generates manifest entries ordered by birth date
4. Updates related files (meta, activities, vocabulary, audit)

Usage:
    .venv/bin/python scripts/convert_c1_bio_to_slugs.py --dry-run
    .venv/bin/python scripts/convert_c1_bio_to_slugs.py --execute
"""

import argparse
import re
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
C1_BIO_DIR = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "c1-bio"
DOCUSAURUS_DIR = PROJECT_ROOT / "docusaurus" / "docs" / "c1-bio"


@dataclass
class Module:
    """Represents a C1-BIO module with birth date."""
    number: int
    slug: str
    title: str
    birth_year: Optional[int]
    death_year: Optional[int]
    md_path: Path

    @property
    def sort_key(self) -> tuple:
        """Sort by birth year, then by current number as tiebreaker."""
        # Unknown birth years go to the end
        year = self.birth_year if self.birth_year else 9999
        return (year, self.number)


def extract_title(content: str) -> str:
    """Extract title from markdown content."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return "Untitled"


def extract_birth_year(content: str) -> Optional[int]:
    """Extract birth year from markdown content.

    Looks for patterns like:
    - | 1866 | Народження... |
    - | бл. 890-920 | Народження... |
    - | 1974 | Народився на Луганщині |
    - (1814—1861)
    - народився близько 942 року
    - (нар. 1974)
    """
    # Pattern 1: Table format with Народження
    # | 1866 | Народження...
    match = re.search(r'\|\s*(?:бл\.\s*)?(\d{3,4})(?:-\d+)?\s*\|\s*Народження', content)
    if match:
        return int(match.group(1))

    # Pattern 2: Table format with Народився/Народилася
    # | 1974 | Народився на Луганщині |
    match = re.search(r'\|\s*(\d{3,4})\s*\|\s*Народи(?:вся|лася)', content)
    if match:
        return int(match.group(1))

    # Pattern 3: Life dates in parentheses after name
    # (1814—1861) or (1814-1861) or (бл. 1595–1657)
    match = re.search(r'\((?:бл\.\s*)?(\d{3,4})[—\-–](\d{3,4})\)', content)
    if match:
        return int(match.group(1))

    # Pattern 4: Born year in prose with близько
    # народився близько 942 року
    match = re.search(r'народи(?:вся|лася)\s+близько\s+(\d{3,4})', content, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 5: Born year mentioned directly in prose
    # народився у 1814 році
    match = re.search(r'народи(?:вся|лася)\s+(?:у\s+)?(\d{4})', content, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Pattern 6: Abbreviated form (нар. 1974)
    match = re.search(r'\(нар\.\s*(\d{4})\)', content)
    if match:
        return int(match.group(1))

    return None


def extract_death_year(content: str) -> Optional[int]:
    """Extract death year from markdown content."""
    # Pattern 1: Life dates in parentheses
    match = re.search(r'\((\d{4})[—\-–](\d{4})\)', content)
    if match:
        return int(match.group(2))

    # Pattern 2: Table format with Смерть
    match = re.search(r'\|\s*(\d{4})\s*\|\s*Смерть', content)
    if match:
        return int(match.group(1))

    return None


def collect_modules() -> list[Module]:
    """Collect all C1-BIO modules with metadata."""
    modules = []

    for md_file in sorted(C1_BIO_DIR.glob("*.md")):
        # Parse filename: 01-knyahynia-olha.md -> (1, knyahynia-olha)
        stem = md_file.stem
        parts = stem.split("-", 1)

        if len(parts) != 2 or not parts[0].isdigit():
            print(f"  Skipping non-standard file: {md_file.name}")
            continue

        number = int(parts[0])
        slug = parts[1]

        # Read content
        content = md_file.read_text(encoding='utf-8')
        title = extract_title(content)
        birth_year = extract_birth_year(content)
        death_year = extract_death_year(content)

        modules.append(Module(
            number=number,
            slug=slug,
            title=title,
            birth_year=birth_year,
            death_year=death_year,
            md_path=md_file
        ))

    return modules


def rename_file(old_path: Path, new_name: str, dry_run: bool) -> bool:
    """Rename a file to new name in same directory."""
    new_path = old_path.parent / new_name

    if new_path.exists() and old_path != new_path:
        print(f"  WARNING: Target exists: {new_path}")
        return False

    if old_path == new_path:
        return True  # Already renamed

    if dry_run:
        print(f"  Would rename: {old_path.name} -> {new_name}")
    else:
        old_path.rename(new_path)
        print(f"  Renamed: {old_path.name} -> {new_name}")

    return True


def rename_module_files(module: Module, dry_run: bool):
    """Rename all files for a module (md, meta, activities, vocab, audit)."""
    old_prefix = f"{module.number:02d}-{module.slug}"
    new_name = module.slug

    # Main markdown file
    rename_file(module.md_path, f"{new_name}.md", dry_run)

    # Related directories
    subdirs = ["meta", "activities", "vocabulary", "audit"]
    extensions = ["yaml", "yaml", "yaml", "md"]

    for subdir, ext in zip(subdirs, extensions):
        subdir_path = C1_BIO_DIR / subdir
        if not subdir_path.exists():
            continue

        # Try numbered format
        old_file = subdir_path / f"{old_prefix}.{ext}"
        if old_file.exists():
            rename_file(old_file, f"{new_name}.{ext}", dry_run)
        else:
            # Also check for already-renamed files
            new_file = subdir_path / f"{new_name}.{ext}"
            if not new_file.exists():
                # Check for audit review files
                if subdir == "audit":
                    old_review = subdir_path / f"{old_prefix}-review.{ext}"
                    if old_review.exists():
                        rename_file(old_review, f"{new_name}-review.{ext}", dry_run)


def generate_manifest_yaml(modules: list[Module]) -> str:
    """Generate YAML manifest entries for c1-bio track."""
    # Sort by birth year
    sorted_modules = sorted(modules, key=lambda m: m.sort_key)

    lines = [
        "  c1-bio:",
        "    name: C1 Biography Track",
        "    description: Notable Ukrainians through history",
        "    prerequisite: c1",
        "    modules:"
    ]

    for mod in sorted_modules:
        # Escape single quotes in title
        safe_title = mod.title.replace("'", "''")

        lines.append(f"    - slug: {mod.slug}")
        lines.append(f"      title: '{safe_title}'")
        lines.append(f"      focus: biography")

        if mod.birth_year:
            lines.append(f"      birth_year: {mod.birth_year}")
        if mod.death_year:
            lines.append(f"      death_year: {mod.death_year}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert C1-BIO to pure slugs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--execute", action="store_true", help="Actually perform renames")
    parser.add_argument("--manifest-only", action="store_true", help="Only generate manifest YAML")
    args = parser.parse_args()

    if not args.dry_run and not args.execute and not args.manifest_only:
        print("Please specify --dry-run, --execute, or --manifest-only")
        return 1

    print("Collecting C1-BIO modules...")
    modules = collect_modules()
    print(f"Found {len(modules)} modules\n")

    # Report birth dates
    with_dates = [m for m in modules if m.birth_year]
    without_dates = [m for m in modules if not m.birth_year]

    print(f"Birth dates found: {len(with_dates)}/{len(modules)}")
    if without_dates:
        print("\nModules without birth dates:")
        for m in without_dates:
            print(f"  {m.number:02d}. {m.title} ({m.slug})")

    # Sort by birth year for display
    sorted_modules = sorted(modules, key=lambda m: m.sort_key)

    print("\n=== Chronological Order (by birth year) ===")
    for i, mod in enumerate(sorted_modules, 1):
        year_str = str(mod.birth_year) if mod.birth_year else "????"
        print(f"{i:3d}. [{year_str}] {mod.title}")

    if args.manifest_only:
        print("\n=== Manifest YAML ===")
        print(generate_manifest_yaml(modules))
        return 0

    # Rename files
    print("\n=== Renaming Files ===")
    dry_run = args.dry_run

    for mod in modules:
        print(f"\nModule {mod.number}: {mod.slug}")
        rename_module_files(mod, dry_run)

    # Generate manifest
    print("\n=== Manifest YAML (add to curriculum.yaml tracks section) ===")
    print(generate_manifest_yaml(modules))

    if dry_run:
        print("\n[DRY RUN - no changes made. Use --execute to apply]")
    else:
        print("\n[Files renamed. Add manifest YAML to curriculum.yaml]")

    return 0


if __name__ == "__main__":
    exit(main())
