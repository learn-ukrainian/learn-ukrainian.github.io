# 2026-04-26 — LLM QG per-level per-dimension thresholds

> **Status**: DRAFT — pending 3-agent review (`ab discuss architecture --with codex,gemini`)
> **Issue**: #1586 (`reboot-blocker`)
> **Authority chain**: `docs/north-star.md` SHIPPABLE §7 → `docs/best-practices/strict-reviewer-persona.md` → this decision → `scripts/common/thresholds.py`
> **Supersedes**: nothing. Companions: ADR-007 (no LLM rewrite), `module-contract.md` §8 (per-dim reviewer scope)
> **Expiry**: revisit when Phase 4 exemplar lands (ACs in #1577) — empirical floor calibration may shift

## Binding constraint (North Star §7, paraphrased)

> LLM QG passes only when **Pedagogical, Naturalness, Decolonization, Engagement, Tone** each ≥ the per-level floor in `LEVEL_THRESHOLDS`. **No weighted average. One failing dim fails the module.**

This document specifies the schema + aggregator semantics that satisfy this constraint and supplies the per-level per-dim default floors.

## What's broken today

`scripts/common/thresholds.py` provides:

| Constant | Scope | Value |
|---|---|---|
| `REVIEW_PASS_FLOOR` | global, level-agnostic | 8.0 |
| `REVIEW_REJECT_FLOOR` | global, level-agnostic | 6.0 |
| `LevelThresholds.naturalness_min` | per-level, single dim | A1/A2/B1=9.0, B2+=8.0 |

The Phase 4 LLM QG contract requires per-level floors for **all 5 dims**, not just naturalness. The current schema can't express that without ad-hoc parallel constants. `scripts/build/v6_build.py:1854-1858` already enforces a single global `REVIEW_TARGET_SCORE` per-dim floor (`dim_floor_fail` predicate); the aggregator is already MIN (`min(raw_scores)`, line 1844). The change is in the **floor lookup**, not the aggregator shape.

## Schema (proposed)

```python
# scripts/common/thresholds.py — additions

QG_DIMS: tuple[str, ...] = (
    "pedagogical",
    "naturalness",
    "decolonization",
    "engagement",
    "tone",
)
"""The 5 LLM QG dimensions per North Star §7. Tests assert this tuple
matches the per-dim reviewer prompt set under
``scripts/build/phases/v6-review/`` (post-retirement of legacy 9-dim)."""


@dataclass(frozen=True, slots=True)
class DimensionFloor:
    """Per-dimension PASS and REJECT floors for one (level, dim) pair."""
    pass_floor: float   # score >= pass_floor → dim PASSes
    reject_floor: float # score < reject_floor → module REJECT-eligible

    def __post_init__(self) -> None:
        if not (0.0 <= self.reject_floor <= self.pass_floor <= 10.0):
            raise ValueError(
                f"DimensionFloor invariant: 0 ≤ reject ({self.reject_floor}) "
                f"≤ pass ({self.pass_floor}) ≤ 10"
            )


@dataclass(frozen=True, slots=True)
class LevelThresholds:
    target_words: int
    review_floors: Mapping[str, DimensionFloor]
    """Per-LLM-QG-dim floors. Keys must be QG_DIMS."""

    @property
    def naturalness_min(self) -> float:
        """Backward-compat alias. New code uses review_floors['naturalness']."""
        return self.review_floors["naturalness"].pass_floor

    def __post_init__(self) -> None:
        missing = set(QG_DIMS) - set(self.review_floors.keys())
        extra = set(self.review_floors.keys()) - set(QG_DIMS)
        if missing or extra:
            raise ValueError(
                f"review_floors must cover exactly QG_DIMS. "
                f"missing={missing} extra={extra}"
            )
```

## Per-level per-dim default floors

Rationale: A1/A2/B1 are stricter than B2+ because thin source material at lower CEFR levels makes awkwardness easier to miss; this matches the existing `naturalness_min` pattern. **Decolonization is held high regardless of level** — it's identity-critical and not a complexity-tradeoff. **Pedagogical and Naturalness track Decolonization at lower levels** because a beginner module that fails either of those is unshippable. **Engagement and Tone hold steady at 8.0** — these are quality-stretch dims that tolerate B-grade and still ship.

| Level | pedagogical | naturalness | decolonization | engagement | tone |
|---|---|---|---|---|---|
| A1   | 9.0 | 9.0 | 9.0 | 8.0 | 8.0 |
| A2   | 9.0 | 9.0 | 9.0 | 8.0 | 8.0 |
| B1   | 9.0 | 9.0 | 9.0 | 8.0 | 8.0 |
| B2   | 8.0 | 8.0 | 9.0 | 8.0 | 8.0 |
| C1   | 8.0 | 8.0 | 9.0 | 8.0 | 8.0 |
| C2   | 8.0 | 8.0 | 9.0 | 8.0 | 8.0 |

REJECT floor: **6.0 across all (level, dim)** — matches the current `REVIEW_REJECT_FLOOR` global. Below 6 means the module is structurally broken and needs a re-plan, not a fix-loop. (User policy 2026-04-23 in strict-reviewer-persona.md.)

These are **defaults, not commitments** — each is overridable per-level via `_LEVEL_THRESHOLDS` and per-variant via the existing `scripts/audit/config.LEVEL_CONFIG` override path.

## Aggregator (single-source-of-truth helper)

```python
# scripts/common/thresholds.py — additions

@dataclass(frozen=True, slots=True)
class ReviewVerdict:
    verdict: Literal["PASS", "REVISE", "REJECT"]
    failing_dims: tuple[str, ...]   # below pass_floor (subset of rejected_dims ∪ revising)
    rejected_dims: tuple[str, ...]  # below reject_floor
    min_score: float
    min_dim: str


def aggregate_review(
    scores: Mapping[str, float],
    level_code: str | None,
) -> ReviewVerdict:
    """MIN aggregator. PASS iff every QG dim ≥ pass_floor.
    REJECT if any QG dim < reject_floor. Otherwise REVISE."""
    floors = get_level_thresholds(level_code).review_floors

    # Restrict to QG dims actually scored; warn (in caller) if any QG dim missing.
    scored_qg = {dim: score for dim, score in scores.items() if dim in floors}
    if not scored_qg:
        raise ValueError(f"No QG dims found in scores: {sorted(scores)}")

    failing = tuple(
        dim for dim, score in scored_qg.items()
        if score < floors[dim].pass_floor
    )
    rejected = tuple(
        dim for dim, score in scored_qg.items()
        if score < floors[dim].reject_floor
    )
    min_dim = min(scored_qg, key=scored_qg.__getitem__)
    min_score = scored_qg[min_dim]

    if rejected:
        verdict = "REJECT"
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
```

## Migration path

| Caller | Today | After #1586 |
|---|---|---|
| Phase 4 LLM QG (new, #1577 Phase 4) | does not exist | uses `aggregate_review(scores, level)` end-to-end |
| `scripts/build/v6_build.py` (legacy V6 reviewer) | uses `REVIEW_TARGET_SCORE` global | **leave as-is** — V6 is being retired by Phase 4. Migration would be wasted work. Mark with comment referencing this ADR. |
| `scripts/wiki/review.py`, `scripts/wiki/compile.py`, `scripts/wiki/rebuild.py` | uses `REVIEW_PASS_FLOOR` global as single overall-score threshold | **leave as-is** — wiki review is single-score, not per-dim. Single-score wiki review is conceptually different from module per-dim QG. Document in module docstring. |
| `scripts/audit/checks/review_gaming.py` (mean-based heuristic) | uses `REVIEW_PASS_FLOOR` for v6 anti-gaming check | **leave as-is** — also v6-specific. Mark with comment. |
| `scripts/audit/checks/review_validation.py` (`_V6_REVIEW_MIN_SCORE`) | already isolated | already correct |
| `scripts/scoring/sampling.py` (`NATURALNESS_THRESHOLD`) | aliases `REVIEW_PASS_FLOOR` | migrate to `get_level_thresholds(level).review_floors["naturalness"].pass_floor` (per-level) |
| `scripts/api/module_dashboard.py` | uses global as single-score gate | migrate to per-level if dashboard knows the level; otherwise keep as worst-case fallback with comment |

**Net change**: new schema lands, Phase 4 uses it. V6 stays on the global until V6 is retired (post-Phase-4 fan-out). No big-bang migration.

## Tests required

1. `tests/test_thresholds_per_dim.py`:
   - `LevelThresholds` `__post_init__` rejects missing or extra dim keys
   - `DimensionFloor` rejects `reject > pass`
   - `aggregate_review` PASS path: all dims at/above pass_floor → PASS, no failing/rejected
   - `aggregate_review` REVISE path: one dim between reject_floor and pass_floor → REVISE, that dim in failing_dims
   - `aggregate_review` REJECT path: one dim below reject_floor → REJECT regardless of other dims
   - `aggregate_review` extra-dim (legacy v6 dim like "language") tolerated, but only QG dims considered for verdict
   - `aggregate_review` empty / missing-QG-dim raises ValueError
   - per-level default floor table values match this doc's table
2. `tests/test_threshold_source_of_truth.py` (extend existing):
   - assert no NEW module-level threshold constants outside `scripts/common/thresholds.py`
   - assert no caller imports `REVIEW_PASS_FLOOR` for **new** purposes (hard list of legacy callers; new imports fail)
3. `tests/test_review_floors_table_sync.py` (new):
   - assert per-level dim floors exactly match this doc's table — this doc is the source of truth, code must agree

## Out of scope for #1586

- Retiring V6 9-dim reviewer (Phase 4 implementation, separate)
- Per-dim reviewer prompt files in `scripts/build/phases/v6-review/` — those are Phase 4 work
- Wiki review per-dim migration — single-score wiki review is conceptually fine
- The actual Phase 4 LLM QG runner — separate brief, separate dispatch

## Implementation brief outline (for Codex dispatch after this design lands)

1. Worktree: `.worktrees/codex-1586-llm-qg-thresholds`
2. Files:
   - `scripts/common/thresholds.py` — add `QG_DIMS`, `DimensionFloor`, `ReviewVerdict`, `aggregate_review`; extend `LevelThresholds.review_floors`; add `__post_init__` invariants
   - `scripts/audit/config.py` — keep `naturalness_min_score` derivation (uses backward-compat alias on `LevelThresholds`)
   - `scripts/scoring/sampling.py` — accept `level_code` parameter; thread through to per-level lookup
   - `scripts/api/module_dashboard.py` — same
   - `tests/test_thresholds_per_dim.py` — new
   - `tests/test_threshold_source_of_truth.py` — extend
   - `tests/test_review_floors_table_sync.py` — new
3. Run `.venv/bin/ruff check` per edit, `.venv/bin/pytest tests/test_thresholds_per_dim.py tests/test_threshold_source_of_truth.py tests/test_review_floors_table_sync.py tests/test_thresholds_consumers.py -x` per phase
4. Single PR titled `feat(thresholds): per-level per-dim LLM QG floors (#1586)`
5. Mandatory worktree per `.claude/rules/delegate-must-use-worktree.md`

## Decision-doc invariant (per `docs/decisions/INDEX.md`)

This file MUST be referenced from `scripts/common/thresholds.py` module docstring after merge so the chain (north-star.md § SHIPPABLE 7 → this doc → code) is traversable from any of its three nodes.
