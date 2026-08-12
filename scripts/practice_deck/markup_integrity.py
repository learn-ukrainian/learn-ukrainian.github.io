"""Detect and gate ZNO practice items that require visual markup.

Official ZNO/НМТ tasks often highlight, underline, or bold letters and words in
stems and answer options.  Plain-text extraction drops those marks, which makes
the item unsolvable.  This module identifies markup-dependent stems, applies a
tracked overlay when marks are recoverable, and quarantines everything else.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OVERLAY = ROOT / "data" / "practice" / "zno-markup-overlay.json"

# Reviewable predicates — exact wording from live corpus audit (2026-08-12).
_OPTION_MARK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"однаковий\s+звук\s+позначають\s+букви", re.I),
    re.compile(r"(?:виділ|підкресл).{0,40}(?:букв|літер|звук)", re.I),
    re.compile(r"(?:виділ|підкресл)(?:ен|ена|ені|енi|енн)?\s+(?:букв|літер)", re.I),
    re.compile(r"правильно\s+виділено\s+букви\s+на\s+позначення\s+наголошен", re.I),
    re.compile(r"виділене\s+слово", re.I),
    re.compile(r"жирним\s+шрифтом", re.I),
)

_STEM_PASSAGE_MARK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"цифр(?:а|и)?\s+позначає\s+(?:наступне|попередн)", re.I),
    re.compile(r"цифр(?:и)?,?\s+окрім", re.I),
)


def stem_requires_option_marks(stem: str) -> bool:
    """Return True when answer options must carry letter/word highlights."""
    text = stem.strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _OPTION_MARK_PATTERNS)


def stem_requires_passage_marks(stem: str) -> bool:
    """Return True when the stem passage body needs stress/letter highlights."""
    text = stem.strip()
    if not text:
        return False
    return any(pattern.search(text) for pattern in _STEM_PASSAGE_MARK_PATTERNS)


def stem_requires_markup(stem: str) -> bool:
    """Return True when the item cannot be honestly solvable without marks."""
    return stem_requires_option_marks(stem) or stem_requires_passage_marks(stem)


def _normalize_marks(raw_marks: Any) -> list[dict[str, Any]] | None:
    if not isinstance(raw_marks, list):
        return None
    marks: list[dict[str, Any]] = []
    for entry in raw_marks:
        if not isinstance(entry, dict):
            return None
        start = entry.get("start")
        end = entry.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
            return None
        mark: dict[str, Any] = {"start": start, "end": end}
        style = entry.get("style")
        if style is not None:
            if style not in {"underline", "bold"}:
                return None
            mark["style"] = style
        marks.append(mark)
    return marks


def _normalize_option_marks(raw: Any, *, option_count: int) -> list[list[dict[str, Any]]] | None:
    if not isinstance(raw, list) or len(raw) != option_count:
        return None
    normalized: list[list[dict[str, Any]]] = []
    for per_option in raw:
        marks = _normalize_marks(per_option)
        if marks is None:
            return None
        normalized.append(marks)
    return normalized


def load_markup_overlay(path: Path = DEFAULT_OVERLAY) -> dict[str, dict[str, Any]]:
    """Load znoTaskId → overlay payload.  Missing file is an empty overlay."""
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items")
    if not isinstance(items, dict):
        raise ValueError(f"{path}: expected object field 'items'")
    return items


def item_has_required_marks(item: dict[str, Any]) -> bool:
    """Return True when an emitted item carries the markup its stem requires."""
    stem = str(item.get("stem", ""))
    options = item.get("options")
    if not isinstance(options, list):
        return False
    needs_option = stem_requires_option_marks(stem)
    needs_passage = stem_requires_passage_marks(stem)
    if needs_option:
        option_marks = _normalize_option_marks(item.get("optionMarks"), option_count=len(options))
        if option_marks is None or not any(option_marks):
            return False
    if needs_passage:
        stem_marks = _normalize_marks(item.get("stemMarks"))
        if stem_marks is None or not stem_marks:
            return False
    return needs_option or needs_passage


def overlay_has_required_marks(
    overlay: dict[str, Any] | None,
    *,
    stem: str,
    options: list[str],
) -> bool:
    if not overlay:
        return False
    needs_option = stem_requires_option_marks(stem)
    needs_passage = stem_requires_passage_marks(stem)
    if needs_option:
        option_marks = _normalize_option_marks(overlay.get("optionMarks"), option_count=len(options))
        if option_marks is None or not any(option_marks):
            return False
    if needs_passage:
        stem_marks = _normalize_marks(overlay.get("stemMarks"))
        if stem_marks is None or not stem_marks:
            return False
    return needs_option or needs_passage


def apply_markup_overlay(
    item: dict[str, Any],
    overlay: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Attach overlay marks or quarantine markup-dependent items."""
    stem = str(item.get("stem", ""))
    options = item.get("options")
    if not isinstance(options, list):
        return None, "invalid_options"

    if not stem_requires_markup(stem):
        return item, None

    if not overlay_has_required_marks(overlay, stem=stem, options=options):
        return None, "broken_missing_markup"

    enriched = dict(item)
    if stem_requires_option_marks(stem):
        option_marks = _normalize_option_marks(overlay["optionMarks"], option_count=len(options))
        if option_marks is None:
            return None, "broken_missing_markup"
        enriched["optionMarks"] = option_marks
    if stem_requires_passage_marks(stem):
        stem_marks = _normalize_marks(overlay.get("stemMarks"))
        if stem_marks is None:
            return None, "broken_missing_markup"
        enriched["stemMarks"] = stem_marks
    return enriched, None


def assert_emit_integrity(shards: dict[str, dict[str, Any]]) -> None:
    """Fail closed if any emitted item still lacks required markup."""
    violations: list[str] = []
    for deck_key, deck in shards.items():
        for item in deck.get("items", []):
            stem = str(item.get("stem", ""))
            if not stem_requires_markup(stem):
                continue
            options = item.get("options")
            if not isinstance(options, list):
                violations.append(f"{deck_key}:{item.get('znoTaskId')}:invalid_options")
                continue
            if not item_has_required_marks(item):
                violations.append(f"{deck_key}:{item.get('znoTaskId')}:broken_missing_markup")
    if violations:
        sample = ", ".join(violations[:5])
        extra = f" (+{len(violations) - 5} more)" if len(violations) > 5 else ""
        raise RuntimeError(f"ZNO markup integrity gate failed: {sample}{extra}")
