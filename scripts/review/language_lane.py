"""Shared Ukrainian review classification for runtime evidence and publication."""

from collections.abc import Mapping
from typing import Any

UKRAINIAN_TASK_FAMILIES = frozenset({"ukrainian-authoring", "ukrainian-review"})


def is_ukrainian_review(task: Mapping[str, Any]) -> bool:
    """Recognize the task's profile, lane flags, or research family."""
    return (
        str(task.get("review_profile") or "").strip().casefold() == "ukrainian"
        or bool(task.get("review_language_lane") or task.get("language_lane"))
        or str(task.get("research_task_family") or task.get("task_family") or "").strip().casefold()
        in UKRAINIAN_TASK_FAMILIES
    )
