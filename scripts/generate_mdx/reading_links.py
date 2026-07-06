"""Reading-reference cross-linking (render-time, integrity-gated).

Folk and seminar lessons link primary-source excerpts to the global
``/readings/{slug}/`` library only when the corresponding reading file exists.
The index is built from ``site/src/content/readings/*.mdx`` frontmatter and file
slugs, so generated lesson MDX cannot emit a broken reading link.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# scripts/generate_mdx/reading_links.py -> parents[2] == repo root.
_DEFAULT_READINGS_DIR = Path(__file__).resolve().parents[2] / "site" / "src" / "content" / "readings"

_STRESS_MARKS = {"́", "̀"}
_APOSTROPHES = {"’", "ʼ", "ʹ", "`", "´", "‘"}
_QUOTE_CHARS = {'"', "'", "«", "»", "“", "”", "„", "‟", "‹", "›"}
_SEPARATOR_RE = re.compile(r"[\s\-_–—/:;,.!?…()[\]{}]+")
_QUOTED_SPAN_RE = re.compile(r"[«\"“](?P<title>[^»\"”]+)[»\"”]")


def normalize_work_title(work: str) -> str:
    """Normalize a reading title, English title, or file slug to a lookup key."""
    if not work:
        return ""

    decomposed = unicodedata.normalize("NFD", work)
    out: list[str] = []
    for ch in decomposed:
        if ch in _STRESS_MARKS or ch in _QUOTE_CHARS:
            continue
        if ch in _APOSTROPHES:
            ch = "'"
        out.append(ch)

    normalized = unicodedata.normalize("NFC", "".join(out))
    normalized = _SEPARATOR_RE.sub(" ", normalized)
    return normalized.strip().casefold()


def _frontmatter_for(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _candidate_titles(frontmatter: dict[str, Any], slug: str) -> set[str]:
    values = {slug}
    for key in ("title", "title_en"):
        value = frontmatter.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        values.add(value)
        for match in _QUOTED_SPAN_RE.finditer(value):
            values.add(match.group("title"))
    return values


def _is_public_reading(frontmatter: dict[str, Any]) -> bool:
    return frontmatter.get("published", True) is not False and frontmatter.get("canonical", True) is not False


@lru_cache(maxsize=4)
def _load_index(readings_dir: str) -> dict[str, str]:
    """Build ``{normalized_title_or_slug: slug}`` from existing reading files."""
    root = Path(readings_dir)
    if not root.is_dir():
        return {}

    index: dict[str, str] = {}
    for path in sorted(root.glob("*.mdx")):
        slug = path.stem
        try:
            frontmatter = _frontmatter_for(path)
        except OSError:
            continue
        if not _is_public_reading(frontmatter):
            continue
        for candidate in _candidate_titles(frontmatter, slug):
            key = normalize_work_title(candidate)
            if key:
                index.setdefault(key, slug)
    return index


@lru_cache(maxsize=4)
def _load_titles(readings_dir: str) -> dict[str, str]:
    """Build ``{slug: learner-facing title}`` for existing reading files."""
    root = Path(readings_dir)
    if not root.is_dir():
        return {}

    titles: dict[str, str] = {}
    for path in sorted(root.glob("*.mdx")):
        slug = path.stem
        try:
            frontmatter = _frontmatter_for(path)
        except OSError:
            continue
        if not _is_public_reading(frontmatter):
            continue
        title = frontmatter.get("title")
        if isinstance(title, str) and title.strip():
            titles[slug] = " ".join(title.split())
    return titles


def reading_href_for(work: str, readings_dir: str | Path | None = None) -> str | None:
    """Return ``/readings/{slug}/`` for ``work`` iff that reading file exists."""
    key = normalize_work_title(work)
    if not key:
        return None
    path = str(readings_dir) if readings_dir is not None else str(_DEFAULT_READINGS_DIR)
    slug = _load_index(path).get(key)
    return f"/readings/{slug}/" if slug else None


def reading_title_for(slug: str, readings_dir: str | Path | None = None) -> str | None:
    """Return the learner-facing title for a hosted reading slug, if present."""
    if not slug:
        return None
    path = str(readings_dir) if readings_dir is not None else str(_DEFAULT_READINGS_DIR)
    return _load_titles(path).get(slug)
