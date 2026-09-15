"""Shared picker for a1-v1 archive-only fixture slugs.

Tests that exercise archive-fallback behavior must not pin a slug that is
slated for upgrade: once it graduates to canonical a1/{slug}/lessons.yaml (or
a1/{slug}/module.md), a hardcoded pin silently stops testing the archive
path. Picking dynamically keeps the fixture honest as slugs graduate.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CURRICULUM_ROOT = Path(__file__).resolve().parents[2] / "curriculum" / "l2-uk-en"


def _vocabulary_is_lemma_shaped(vocabulary_path: Path) -> bool:
    """Return whether every entry uses the current ``lemma`` vocabulary key.

    A handful of pre-upgrade a1-v1 modules still use the older ``word`` key.
    That is a real content-schema inconsistency, out of scope for this
    machinery fix, so the picker steers around it rather than tripping
    ``post_build_review``'s vocabulary parsing.
    """
    if not vocabulary_path.is_file():
        return True
    rows = yaml.safe_load(vocabulary_path.read_text(encoding="utf-8")) or []
    if not isinstance(rows, list):
        return False
    return all(isinstance(row, dict) and isinstance(row.get("lemma"), str) and row["lemma"].strip() for row in rows)


def pick_archive_only_slug(curriculum_root: Path = CURRICULUM_ROOT) -> str:
    archive_root = curriculum_root / "a1-v1"
    canonical_root = curriculum_root / "a1"
    plans_root = curriculum_root / "plans" / "a1"
    candidates = sorted(
        path.name
        for path in archive_root.iterdir()
        if path.is_dir() and (path / "module.md").is_file()
    )
    for slug in candidates:
        upgraded = (canonical_root / slug / "lessons.yaml").is_file() or (
            canonical_root / slug / "module.md"
        ).is_file()
        if upgraded:
            continue
        if not (plans_root / f"{slug}.yaml").is_file():
            continue
        if not _vocabulary_is_lemma_shaped(archive_root / slug / "vocabulary.yaml"):
            continue
        return slug
    raise RuntimeError("No archive-only a1-v1 slug remains for the archive-resolution fixtures")
