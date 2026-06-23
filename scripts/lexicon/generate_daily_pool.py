"""Generate the small daily-curated Word Atlas pool from the manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path("site/src/data/lexicon-manifest.json")
DEFAULT_OUT = Path("site/src/data/lexicon-daily-pool.json")
EARLY_CEFR = {"A1", "A2", "B1"}


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _first_course_track(entry: dict[str, Any]) -> str | None:
    course_usage = entry.get("course_usage")
    if not isinstance(course_usage, list) or not course_usage:
        return None
    first = course_usage[0]
    if not isinstance(first, dict):
        return None
    track = first.get("track")
    return track if _has_text(track) else None


def _early_cefr(entry: dict[str, Any]) -> str | None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        return None
    cefr = enrichment.get("cefr")
    return cefr if cefr in EARLY_CEFR else None


def compute_weight(entry: dict[str, Any]) -> int:
    """Return the deterministic daily-pool priority weight for a manifest entry."""
    weight = 0
    if _first_course_track(entry) is not None:
        weight += 3
    if entry.get("primary_source") == "surzhyk_to_avoid" and _has_text(entry.get("gloss")):
        weight += 2
    if _early_cefr(entry) is not None:
        weight += 2
    return weight


def _pool_item(entry: dict[str, Any]) -> dict[str, Any] | None:
    lemma = entry.get("lemma")
    slug = entry.get("url_slug")
    if not _has_text(lemma) or not _has_text(slug):
        return None

    weight = compute_weight(entry)
    gloss = entry.get("gloss")
    if weight == 0 and not _has_text(gloss):
        return None

    item: dict[str, Any] = {
        "lemma": lemma,
        "slug": slug,
        "gloss": gloss if isinstance(gloss, str) else None,
        "weight": weight,
    }
    lesson_tag = _first_course_track(entry)
    if lesson_tag is not None:
        item["lessonTag"] = lesson_tag
    cefr = _early_cefr(entry)
    if cefr is not None:
        item["cefr"] = cefr
    return item


def build_pool(entries: list[dict[str, Any]], size: int = 300) -> list[dict[str, Any]]:
    """Build the daily pool, selecting by weight then returning lemma-sorted JSON rows."""
    if size < 0:
        raise ValueError("size must be non-negative")

    candidates = [item for entry in entries if (item := _pool_item(entry)) is not None]
    selected = sorted(candidates, key=lambda item: (-item["weight"], item["lemma"]))[:size]
    return sorted(selected, key=lambda item: item["lemma"])


def write_pool(pool: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(pool, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--size", type=int, default=300)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    pool = build_pool(entries, args.size)
    write_pool(pool, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
