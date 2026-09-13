"""Resolve explicitly declared parallel levels to their pedagogical base."""

from collections.abc import Collection, Mapping
from functools import lru_cache
from pathlib import Path

import yaml

MANIFEST = Path(__file__).resolve().parents[1] / "curriculum/l2-uk-en/curriculum.yaml"

# Canonical A1 is published incrementally; old slug references remain valid.
PREVIOUS_EDITIONS = {"a1": "a1-v1"}


def resolve_module_track(level: str, slug: str, modules: Collection[tuple[str, str]]) -> str:
    """Resolve a slug against manifest membership without changing any roster."""
    previous = PREVIOUS_EDITIONS.get(level)
    if (level, slug) not in modules and previous and (previous, slug) in modules:
        return previous
    return level


def resolve_manifest_module_track(level: str, slug: str, levels: Mapping) -> str:
    """Accept raw or validated manifest levels, preserving canonical precedence."""
    candidates = (level, PREVIOUS_EDITIONS.get(level))
    modules = {
        (track, item)
        for track in candidates if track
        for item in levels.get(track, {}).get("modules", [])
    }
    return resolve_module_track(level, slug, modules)


def resolve_content_track(level: str, slug: str, curriculum_root: Path) -> str:
    """Select one content edition as a whole; never mix its companion files.

    Plans and empty output directories do not shadow the archived learner bundle.
    A canonical module or lesson body takes precedence as soon as it is written.
    """
    def has_content(track: str) -> bool:
        directory = curriculum_root / track
        return (
            (directory / slug / "module.md").is_file()
            or (directory / f"{slug}.md").is_file()
            or any((directory / slug).glob("lesson-*/module.md"))
            or any(directory.glob(f"[0-9]*-{slug}.md"))
        )

    previous = PREVIOUS_EDITIONS.get(level)
    if previous and not has_content(level) and has_content(previous):
        return previous
    return level


@lru_cache(maxsize=8)
def _levels(manifest: Path, modified_ns: int) -> dict:
    return yaml.safe_load(manifest.read_text(encoding="utf-8"))["levels"]


def base_level(level: str, *, manifest: Path = MANIFEST) -> str:
    """Follow manifest aliases; reject cycles and dangling base declarations."""
    key = level.lower()
    levels = _levels(manifest, manifest.stat().st_mtime_ns)
    seen: set[str] = set()
    while isinstance(levels.get(key), dict) and levels[key].get("base_level"):
        if key in seen:
            raise ValueError(f"Cyclic base_level declaration: {level}")
        seen.add(key)
        key = str(levels[key]["base_level"]).lower()
        if key not in levels:
            raise ValueError(f"Unknown base_level for {level}: {key}")
    return key
