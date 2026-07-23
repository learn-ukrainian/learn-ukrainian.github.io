"""Adapt privacy-safe Hramatka lessons to the LLM-QG review-target contract.

Hramatka lessons are teacher-service payloads, rather than curriculum module
directories.  This boundary selects only learner-visible fields, removes
teacher/pipeline data before it can be serialized, and materializes the four
files consumed by :mod:`qg_workflow` and :mod:`qg_shadow_run`.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.audit.content_surface_gates import SurfacePolicy, policy_for_level
from scripts.audit.hramatka_qg_rules import adapt_lesson_json, write_adapted_module_dir
from scripts.audit.qg_workflow import ReviewTarget

_SENSITIVE_KEY_PARTS = frozenset(
    {
        "annotation",
        "api_key",
        "auth",
        "credential",
        "email",
        "internal",
        "metadata",
        "note",
        "password",
        "private",
        "provenance",
        "rationale",
        "secret",
        "source",
        "system",
        "teacher",
        "token",
        "trace",
        "user",
    }
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_SECRET_RE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|private[_ -]?token|secret|password)\b"
    r"\s*(?:[:=]|is)\s*[^\s,;]+"
)
_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+")


@dataclass(frozen=True, slots=True)
class AdaptedHramatkaReviewTarget:
    """A materialized target plus its privacy-safe capture identity."""

    review_target: ReviewTarget
    canonical_payload: dict[str, Any]
    content_sha256: str
    policy: SurfacePolicy
    excluded_fields: tuple[str, ...]


def canonical_serialize(value: Mapping[str, Any]) -> str:
    """Return a stable UTF-8 JSON representation for capture identity."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_sha256(value: Mapping[str, Any]) -> str:
    """Hash a canonical, already-sanitized lesson payload."""
    return hashlib.sha256(canonical_serialize(value).encode("utf-8")).hexdigest()


def map_hramatka_level_and_policy(lesson: Mapping[str, Any]) -> tuple[str, SurfacePolicy]:
    """Map Hramatka's level labels to a standard QG CEFR level and policy."""
    raw = lesson.get("level") or lesson.get("cefr") or lesson.get("difficulty") or "a1"
    normalized = re.sub(r"[\s_]+", "-", str(raw).strip().casefold())
    aliases = {
        "beginner": "a1",
        "elementary": "a1",
        "pre-a1": "a1",
        "starter": "a1",
        "pre-intermediate": "a2",
        "intermediate": "b1",
        "upper-intermediate": "b2",
        "advanced": "c1",
        "proficient": "c2",
    }
    level = aliases.get(normalized, normalized)
    match = re.search(r"(?:a|b|c)[12]", level)
    level = match.group(0) if match else "a1"
    return level, policy_for_level(level)


def _key_is_sensitive(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_text(value: str) -> str:
    value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = _IPV4_RE.sub("[REDACTED_IP]", value)
    value = _SECRET_RE.sub("[REDACTED_SECRET]", value)
    return _BEARER_RE.sub("Bearer [REDACTED_TOKEN]", value)


def _sanitize_value(value: Any, excluded: set[str]) -> Any:
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for key, child in value.items():
            key_s = str(key)
            if _key_is_sensitive(key_s):
                excluded.add(key_s)
                continue
            sanitized[key_s] = _sanitize_value(child, excluded)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item, excluded) for item in value]
    if isinstance(value, str):
        return _redact_text(value)
    return value


def select_learner_facing_fields(lesson: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Select and sanitize fields eligible for learner-facing evaluation.

    Only title, level, anchor text, and learner activity/answer fields cross
    this boundary.  Unknown top-level fields are deliberately not forwarded.
    """
    if not isinstance(lesson, Mapping):
        raise ValueError("hramatka lesson must be a mapping")
    level, _policy = map_hramatka_level_and_policy(lesson)
    excluded: set[str] = {str(key) for key in lesson if key not in {"title", "level", "cefr", "difficulty", "anchor", "blocks"}}
    anchor = lesson.get("anchor")
    anchor_text = anchor.get("text") if isinstance(anchor, Mapping) else anchor
    blocks = lesson.get("blocks") if isinstance(lesson.get("blocks"), list) else []
    sanitized_blocks = _sanitize_value(blocks, excluded)
    selected = {
        "title": _redact_text(str(lesson.get("title") or "").strip()),
        "level": level,
        "anchor": {"text": _redact_text(str(anchor_text or "").strip())},
        "blocks": sanitized_blocks,
    }
    return selected, tuple(sorted(excluded))


class HramatkaLessonAdapter:
    """Convert Hramatka teacher-lesson payloads into shadow-capture targets."""

    def adapt(
        self,
        lesson: Mapping[str, Any],
        module_dir: Path,
        *,
        slug: str | None = None,
    ) -> AdaptedHramatkaReviewTarget:
        selected, excluded = select_learner_facing_fields(lesson)
        level, policy = map_hramatka_level_and_policy(selected)
        adapted = adapt_lesson_json(selected, slug=slug)
        write_adapted_module_dir(adapted, module_dir)
        canonical_payload = {
            "schema": "hramatka_qg_shadow_target.v1",
            "level": level,
            "slug": adapted.slug,
            "lesson": selected,
        }
        target = ReviewTarget(level=level, slug=adapted.slug, module_dir=module_dir)
        return AdaptedHramatkaReviewTarget(
            review_target=target,
            canonical_payload=canonical_payload,
            content_sha256=content_sha256(canonical_payload),
            policy=policy,
            excluded_fields=excluded,
        )


def convert_hramatka_lesson_to_review_target(
    lesson: Mapping[str, Any], module_dir: Path, *, slug: str | None = None
) -> ReviewTarget:
    """Materialize a Hramatka lesson and return the native QG target shape."""
    return HramatkaLessonAdapter().adapt(lesson, module_dir, slug=slug).review_target
