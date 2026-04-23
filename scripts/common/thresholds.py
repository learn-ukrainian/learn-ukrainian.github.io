"""Single source of truth for pipeline thresholds.

Consolidates reviewer floors, style-review gates, and per-level word /
naturalness thresholds so drift is impossible: one file, explicit
semantics, immutable values.

Every threshold-typed module-level constant outside this file is a
regression and will be caught by ``tests/test_threshold_source_of_truth.py``.

Why not per-level for reviewer floors?
    Reviewer personas evaluate a dimension on its own merits — a "6/10
    factual accuracy" is weak regardless of the target CEFR level. The
    audit-side naturalness gate *is* level-varying (stricter at A1/A2/B1
    because thin source material needs extra polish); that lives in
    :data:`LEVEL_THRESHOLDS`.

Why not per-level for style-review thresholds either?
    Same reason. The style reviewer evaluates pragmatic authenticity,
    stylistic consistency, culture + register, and naturalness against
    absolute targets.

Plan-level ``word_target`` overrides the level default at generation
time (see ``scripts/pipeline/core.py``). That's a per-module attribute,
not a threshold — keep it in plan YAML, not here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

# ---------------------------------------------------------------------------
# Review pipeline floors — global (level-agnostic)
# ---------------------------------------------------------------------------

REVIEW_PASS_FLOOR: float = 8.0
"""Per-dimension reviewer PASS floor. Dim scores below this trigger a
REVISE verdict in the general reviewer (see scripts/build/v6_build.py)."""

REVIEW_REJECT_FLOOR: float = 6.0
"""Hard reject floor. Dim scores below this fail review unconditionally."""

STYLE_REVIEW_TARGET: float = 9.0
"""Style-reviewer verdict target. Stricter than the general reviewer
because pragmatic authenticity / stylistic consistency / culture-register /
naturalness are language-native dimensions where "just ok" is not
shippable."""

STYLE_REVIEW_DIMENSION_FLOOR: float = 8.5
"""Per-dimension floor for the style reviewer."""

# ---------------------------------------------------------------------------
# Per-level thresholds — families (A1..C2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LevelThresholds:
    """Immutable per-level thresholds.

    Variant configs (A1-checkpoint, A2-grammar, B2-biography, seminar
    tracks, ...) may legitimately override these family baselines. When
    they do, the override lives in ``scripts/audit/config.LEVEL_CONFIG``
    and the reason belongs in a comment there, not here.
    """

    target_words: int
    """Minimum total words per module (audit gate + writer word budget)."""

    naturalness_min: float
    """Audit gate for the ``naturalness`` review dimension. Stricter at
    A1/A2/B1 where source material is thin and awkward phrasing is easy
    to miss; relaxed to 8.0 at B2+ where complexity naturally increases."""


_LEVEL_THRESHOLDS: dict[str, LevelThresholds] = {
    "A1": LevelThresholds(target_words=1200, naturalness_min=9.0),
    "A2": LevelThresholds(target_words=2000, naturalness_min=9.0),
    "B1": LevelThresholds(target_words=4000, naturalness_min=9.0),
    "B2": LevelThresholds(target_words=4000, naturalness_min=8.0),
    "C1": LevelThresholds(target_words=4000, naturalness_min=8.0),
    "C2": LevelThresholds(target_words=5000, naturalness_min=8.0),
}

LEVEL_THRESHOLDS: Mapping[str, LevelThresholds] = MappingProxyType(_LEVEL_THRESHOLDS)
"""Read-only view of per-level family thresholds."""

_DEFAULT_THRESHOLDS = LevelThresholds(target_words=4000, naturalness_min=8.0)
"""Fallback for unknown level codes. Matches the audit-side ``default``
row historically used in ``AUDIT_THRESHOLDS['naturalness_min_score']``."""


def get_level_thresholds(level_code: str | None) -> LevelThresholds:
    """Resolve thresholds for a level family.

    Accepts both bare families (``"A1"``, ``"b2"``) and variant codes
    (``"A1-checkpoint"``, ``"B2-grammar"``) — maps to the family prefix.
    Unknown codes fall back to ``_DEFAULT_THRESHOLDS``.
    """
    if not level_code:
        return _DEFAULT_THRESHOLDS
    prefix = level_code.upper().split("-", 1)[0]
    return LEVEL_THRESHOLDS.get(prefix, _DEFAULT_THRESHOLDS)


def get_naturalness_min(level_code: str | None) -> float:
    """Shortcut — per-level audit naturalness gate."""
    return get_level_thresholds(level_code).naturalness_min


def get_target_words(level_code: str | None) -> int:
    """Shortcut — per-level family word target. Variant overrides live in
    ``scripts/audit/config.LEVEL_CONFIG``; callers that respect those
    should use ``scripts.audit.config.get_word_target`` instead."""
    return get_level_thresholds(level_code).target_words
