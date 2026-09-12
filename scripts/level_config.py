"""Resolve explicitly declared parallel levels to their pedagogical base."""

from functools import lru_cache
from pathlib import Path

import yaml

MANIFEST = Path(__file__).resolve().parents[1] / "curriculum/l2-uk-en/curriculum.yaml"


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
