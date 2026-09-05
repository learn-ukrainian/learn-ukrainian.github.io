"""Loader and query utilities for navsi200.com lesson catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "corpus_audit" / "navsi200-catalog.json"

PRIORITY_TOPICS = (
    "пароніми",
    "наголос",
    "лексична норма",
    "найтиповіші завдання ЗНО",
)


def load_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Load and return the navsi200 catalog dictionary.

    Args:
        path: Optional path to the catalog JSON file. Defaults to
            `data/corpus_audit/navsi200-catalog.json`.

    Returns:
        Dictionary containing catalog metadata, topic indices, and lesson entries.
    """
    catalog_path = Path(path) if path else DEFAULT_CATALOG_PATH
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog file not found: {catalog_path}")

    with catalog_path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    return data


def get_lessons_by_topic(catalog: dict[str, Any], topic: str) -> list[dict[str, Any]]:
    """Retrieve all lessons belonging to a specified topic.

    Args:
        catalog: Loaded catalog dictionary.
        topic: Topic name to filter by (case-insensitive).

    Returns:
        List of matching lesson entries.
    """
    target_topic = topic.strip().lower()
    matches: list[dict[str, Any]] = []

    for lesson in catalog.get("lessons", []):
        lesson_topics = [t.lower() for t in lesson.get("topics", [])]
        primary_topic = lesson.get("topic", "").lower()
        if target_topic in lesson_topics or target_topic == primary_topic:
            matches.append(lesson)

    return matches


def get_priority_lessons(catalog: dict[str, Any], topic: str | None = None) -> list[dict[str, Any]]:
    """Retrieve priority lessons, optionally filtered by a specific priority topic.

    Args:
        catalog: Loaded catalog dictionary.
        topic: Optional priority topic name (must be one of `PRIORITY_TOPICS` if provided).

    Returns:
        List of priority lesson entries.
    """
    if topic:
        target = topic.strip().lower()
        if target not in [p.lower() for p in PRIORITY_TOPICS]:
            raise ValueError(f"Unknown priority topic '{topic}'. Expected one of: {PRIORITY_TOPICS}")
        return get_lessons_by_topic(catalog, target)

    # Return all lessons flagged as priority
    return [lesson for lesson in catalog.get("lessons", []) if lesson.get("is_priority", False)]


def get_lesson_by_id(catalog: dict[str, Any], lesson_id: str) -> dict[str, Any] | None:
    """Find a lesson by its unique catalog ID."""
    for lesson in catalog.get("lessons", []):
        if lesson.get("id") == lesson_id:
            return lesson
    return None


def get_lesson_by_video_id(catalog: dict[str, Any], video_id: str) -> dict[str, Any] | None:
    """Find a lesson by its YouTube video ID."""
    for lesson in catalog.get("lessons", []):
        if lesson.get("video_id") == video_id:
            return lesson
    return None


def get_catalog_summary(catalog: dict[str, Any]) -> dict[str, Any]:
    """Return high-level summary statistics of the catalog."""
    summary: dict[str, Any] = catalog.get("summary", {})
    return summary
