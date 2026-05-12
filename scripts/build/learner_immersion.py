"""Learner immersion helpers derived from cumulative vocabulary state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import yaml

CURRICULUM_ROOT = Path(__file__).resolve().parents[2] / "curriculum" / "l2-uk-en"
CACHE_ROOT = Path(".cache")


def _parse_slug(entry: object) -> str:
    if isinstance(entry, str):
        return entry.split("#")[0].strip()
    return str(entry)


def _load_curriculum_modules(track: str) -> list[str]:
    path = CURRICULUM_ROOT / "curriculum.yaml"
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    modules = data.get("levels", {}).get(track, {}).get("modules", [])
    if not isinstance(modules, list):
        return []
    return [_parse_slug(entry) for entry in modules]


def _load_vocab_lemmas(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    items = data.get("items", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    lemmas: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("lemma"):
            lemmas.append(str(item["lemma"]).lower())
    return lemmas


def _extract_all_ukrainian_surfaces(content: str) -> list[str]:
    try:
        from scripts.audit.checks.learner_state import _strip_non_body_prose, _vesum_helpers
    except ModuleNotFoundError:  # pragma: no cover - CLI path compatibility
        from audit.checks.learner_state import _strip_non_body_prose, _vesum_helpers

    iter_surfaces, normalize_for_vesum = _vesum_helpers()
    normalized = normalize_for_vesum(_strip_non_body_prose(content))
    return [word.lower() for word in iter_surfaces(normalized)]


def _source_paths(track: str, up_to_module: int) -> list[Path]:
    paths: list[Path] = []
    for slug in _load_curriculum_modules(track)[: max(0, up_to_module - 1)]:
        module_dir = CURRICULUM_ROOT / track / slug
        paths.append(module_dir / "vocabulary.yaml")
        paths.append(module_dir / "module.md")
    return paths


def _cache_path(track: str, up_to_module: int) -> Path:
    return CACHE_ROOT / f"lemma-frequency-{track}-{up_to_module}.json"


def _cache_is_fresh(cache_path: Path, source_paths: list[Path]) -> bool:
    if not cache_path.exists():
        return False
    cache_mtime = cache_path.stat().st_mtime
    return all(not path.exists() or path.stat().st_mtime <= cache_mtime for path in source_paths)


def _read_cache(cache_path: Path) -> dict[str, list[tuple[int, int]]]:
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    return {
        str(lemma): [(int(module_num), int(count)) for module_num, count in rows]
        for lemma, rows in raw.items()
    }


def _write_cache(cache_path: Path, data: dict[str, list[tuple[int, int]]]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        lemma: [[module_num, count] for module_num, count in rows]
        for lemma, rows in sorted(data.items())
    }
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{cache_path.name}.",
        suffix=".tmp",
        dir=str(cache_path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp_name, cache_path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def build_lemma_frequency_map(track: str, up_to_module: int) -> dict[str, list[tuple[int, int]]]:
    """Return per-lemma surface-form counts from modules before up_to_module.

    The result maps each declared lemma to ``[(module_num, surface_form_count), ...]``.
    Counts are cached in ``.cache/lemma-frequency-{track}-{module}.json`` and
    rebuilt when any source vocabulary or module body file is newer than the cache.
    """
    normalized_track = track.lower()
    source_paths = _source_paths(normalized_track, up_to_module)
    cache_path = _cache_path(normalized_track, up_to_module)
    if _cache_is_fresh(cache_path, source_paths):
        return _read_cache(cache_path)

    frequencies: dict[str, list[tuple[int, int]]] = {}
    slugs = _load_curriculum_modules(normalized_track)
    for module_index, slug in enumerate(slugs[: max(0, up_to_module - 1)], start=1):
        module_dir = CURRICULUM_ROOT / normalized_track / slug
        lemmas = _load_vocab_lemmas(module_dir / "vocabulary.yaml")
        body_path = module_dir / "module.md"
        surfaces = (
            _extract_all_ukrainian_surfaces(body_path.read_text(encoding="utf-8"))
            if body_path.exists()
            else []
        )
        surface_counts = {lemma: surfaces.count(lemma) for lemma in set(lemmas)}
        for lemma in lemmas:
            frequencies.setdefault(lemma, []).append((module_index, surface_counts.get(lemma, 0)))

    _write_cache(cache_path, frequencies)
    return frequencies
