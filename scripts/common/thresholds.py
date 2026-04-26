"""Single source of truth for pipeline thresholds.

Consolidates reviewer floors, style-review gates, and per-level word /
naturalness thresholds so drift is impossible: one file, explicit
semantics, immutable values.

Every threshold-typed module-level constant outside this file is a
regression and will be caught by ``tests/test_threshold_source_of_truth.py``.

Decision chain:
    ``docs/north-star.md`` SHIPPABLE §7 →
    ``docs/decisions/2026-04-26-llm-qg-per-dim-thresholds.md`` →
    this module.

Why both global and per-level reviewer floors?
    Phase 4 LLM QG uses per-level per-dim floors in
    :data:`LEVEL_THRESHOLDS` and :func:`aggregate_review`. Legacy V6 and
    wiki single-score review still use the global ``REVIEW_*`` constants
    until those surfaces are retired or deliberately migrated.

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
from typing import Literal

# ---------------------------------------------------------------------------
# Review pipeline floors — global (level-agnostic)
# ---------------------------------------------------------------------------

REVIEW_PASS_FLOOR: float = 8.0
"""Per-dimension reviewer PASS floor. Dim scores below this trigger a
REVISE verdict in the general reviewer (see scripts/build/v6_build.py)."""

REVIEW_REJECT_FLOOR: float = 6.0
"""Hard reject floor. Dim scores below this fail review unconditionally."""

QG_DIMS: tuple[str, ...] = (
    "pedagogical",
    "naturalness",
    "decolonization",
    "engagement",
    "tone",
)
"""The 5 LLM QG dimensions per North Star §7."""

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
class DimensionFloor:
    """Per-dimension PASS and REJECT floors for one (level, dim) pair."""

    pass_floor: float
    """Score must be at or above this floor for the dimension to PASS."""

    reject_floor: float
    """Score below this floor makes the module REJECT-eligible."""

    def __post_init__(self) -> None:
        if not (0.0 <= self.reject_floor <= self.pass_floor <= 10.0):
            raise ValueError(
                f"DimensionFloor invariant: 0 ≤ reject ({self.reject_floor}) "
                f"≤ pass ({self.pass_floor}) ≤ 10"
            )


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

    review_floors: Mapping[str, DimensionFloor]
    """Per-LLM-QG-dim floors. Keys must be exactly ``QG_DIMS``."""

    @property
    def naturalness_min(self) -> float:
        """Backward-compat alias. New code uses review_floors['naturalness']."""
        return self.review_floors["naturalness"].pass_floor

    def __post_init__(self) -> None:
        missing = set(QG_DIMS) - set(self.review_floors.keys())
        extra = set(self.review_floors.keys()) - set(QG_DIMS)
        if missing or extra:
            raise ValueError(
                "review_floors must cover exactly QG_DIMS. "
                f"missing={missing} extra={extra}"
            )
        object.__setattr__(
            self,
            "review_floors",
            MappingProxyType(dict(self.review_floors)),
        )


@dataclass(frozen=True, slots=True)
class ReviewVerdict:
    """Aggregate LLM QG verdict and the dimensions that drove it."""

    verdict: Literal["PASS", "REVISE", "REJECT"]
    failing_dims: tuple[str, ...]
    rejected_dims: tuple[str, ...]
    min_score: float
    min_dim: str


def _make_review_floors(
    *,
    pedagogical: float,
    naturalness: float,
    decolonization: float,
    engagement: float,
    tone: float,
) -> Mapping[str, DimensionFloor]:
    pass_floors = {
        "pedagogical": pedagogical,
        "naturalness": naturalness,
        "decolonization": decolonization,
        "engagement": engagement,
        "tone": tone,
    }
    return MappingProxyType({
        dim: DimensionFloor(pass_floor=pass_floor, reject_floor=REVIEW_REJECT_FLOOR)
        for dim, pass_floor in pass_floors.items()
    })


_LEVEL_THRESHOLDS: dict[str, LevelThresholds] = {
    "A1": LevelThresholds(
        target_words=1200,
        review_floors=_make_review_floors(
            pedagogical=9.0,
            naturalness=9.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
    "A2": LevelThresholds(
        target_words=2000,
        review_floors=_make_review_floors(
            pedagogical=9.0,
            naturalness=9.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
    "B1": LevelThresholds(
        target_words=4000,
        review_floors=_make_review_floors(
            pedagogical=9.0,
            naturalness=9.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
    "B2": LevelThresholds(
        target_words=4000,
        review_floors=_make_review_floors(
            pedagogical=8.0,
            naturalness=8.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
    "C1": LevelThresholds(
        target_words=4000,
        review_floors=_make_review_floors(
            pedagogical=8.0,
            naturalness=8.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
    "C2": LevelThresholds(
        target_words=5000,
        review_floors=_make_review_floors(
            pedagogical=8.0,
            naturalness=8.0,
            decolonization=9.0,
            engagement=8.0,
            tone=8.0,
        ),
    ),
}

LEVEL_THRESHOLDS: Mapping[str, LevelThresholds] = MappingProxyType(_LEVEL_THRESHOLDS)
"""Read-only view of per-level family thresholds."""

_DEFAULT_THRESHOLDS = LevelThresholds(
    target_words=4000,
    review_floors=_make_review_floors(
        pedagogical=8.0,
        naturalness=8.0,
        decolonization=9.0,
        engagement=8.0,
        tone=8.0,
    ),
)
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


def aggregate_review(
    scores: Mapping[str, float],
    level_code: str | None,
) -> ReviewVerdict:
    """MIN aggregator for Phase 4 LLM QG.

    PASS iff every scored QG dim is at or above its per-level pass floor.
    REJECT if any scored QG dim is below its reject floor. Otherwise REVISE.
    """
    floors = get_level_thresholds(level_code).review_floors
    scored_qg = {dim: score for dim, score in scores.items() if dim in floors}
    if not scored_qg:
        raise ValueError(f"No QG dims found in scores: {sorted(scores)}")

    failing = tuple(
        dim
        for dim, score in scored_qg.items()
        if score < floors[dim].pass_floor
    )
    rejected = tuple(
        dim
        for dim, score in scored_qg.items()
        if score < floors[dim].reject_floor
    )
    min_dim = min(scored_qg, key=scored_qg.__getitem__)
    min_score = scored_qg[min_dim]

    if rejected:
        verdict: Literal["PASS", "REVISE", "REJECT"] = "REJECT"
    elif failing:
        verdict = "REVISE"
    else:
        verdict = "PASS"

    return ReviewVerdict(
        verdict=verdict,
        failing_dims=failing,
        rejected_dims=rejected,
        min_score=min_score,
        min_dim=min_dim,
    )


def get_target_words(level_code: str | None) -> int:
    """Shortcut — per-level family word target. Variant overrides live in
    ``scripts/audit/config.LEVEL_CONFIG``; callers that respect those
    should use ``scripts.audit.config.get_word_target`` instead."""
    return get_level_thresholds(level_code).target_words
