"""Plan v2 loader and path resolver (issue #8412, #8431).

Provides authoritative loading and validation of fresh module plans (schema v2):
curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.curriculum.validate.loader import (
    PLAN_SCHEMA_PATH,
    PlanError,
    check_plan_slug,
    evidence_root,
    read_plan_text,
    resolve_plan_path,
    sha256_of,
)
from scripts.curriculum.validate.loader import (
    load_plan as _loader_load_plan,
)

__all__ = [
    "PLAN_SCHEMA_PATH",
    "PlanError",
    "check_plan_slug",
    "evidence_root",
    "load_lesson_entry",
    "load_plan",
    "read_plan_text",
    "resolve_plan_path",
    "sha256_of",
]


def load_plan(plan_path: Path) -> dict[str, Any]:
    """Load module plan v2 from disk, validating schema 2 and rejecting v1 fields."""
    return _loader_load_plan(plan_path)


def load_lesson_entry(
    level: str, slug: str, lesson_n: int, *, plan_path: Path | None = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve plan path, load plan v2, and return (plan_dict, lesson_entry)."""
    path = resolve_plan_path(level, slug, plan_path=plan_path)
    plan_dict = load_plan(path)
    lesson_entry = next((l for l in plan_dict.get("lessons", []) if l.get("n") == lesson_n), None)
    if lesson_entry is None:
        raise ValueError(f"Lesson {lesson_n} not found in plan {path}")
    return plan_dict, lesson_entry
