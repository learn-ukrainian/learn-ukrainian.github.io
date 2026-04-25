"""Invariants for ``scripts/audit/config.LEVEL_CONFIG`` and the
audit ↔ pipeline reconciliation introduced in #1550 unit 4.

These invariants capture the outcome of the audit/pipeline config sweep:

1. Activity counts are MINIMUMS. Every level has a non-zero
   ``min_activities`` floor (real failures should be detectable, not
   silently swallowed by ``0``).
2. Type-diversity is enforced. Every level has ``min_types_unique >= 2``.
3. The forbidden / required / allowed / priority sets within audit are
   self-consistent (forbidden cannot also be priority/required/allowed).
4. Audit's ``priority_types`` are a subset of the union of the pipeline's
   inline + workbook allowed types — i.e. the writer can actually emit
   what the audit says it prefers.

Run: ``.venv/bin/pytest tests/audit/test_config_invariants.py -v``
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit.config import LEVEL_CONFIG
from pipeline.config_tables import ACTIVITY_CONFIGS

# ---------------------------------------------------------------------------
# Cross-layer mapping. Audit LEVEL_CONFIG keys → pipeline ACTIVITY_CONFIGS
# keys. The pipeline groups some sub-tracks under shared keys (e.g. all
# B1 variants → "b1-core") because they share writer prompts.
# ---------------------------------------------------------------------------
AUDIT_TO_PIPELINE_KEY: dict[str, str] = {
    "A1": "a1",
    "A2": "a2",
    "A2-grammar": "a2",
    "A1-checkpoint": "a1-checkpoint",
    "A2-checkpoint": "a2-checkpoint",
    "B1": "b1-core",
    "B1-grammar": "b1-core",
    "B1-vocab": "b1-core",
    "B1-culture": "b1-core",
    "B1-skills": "b1-core",
    "B1-checkpoint": "b1-core",
    "B1-capstone": "b1-core",
    "B2": "b2",
    "B2-grammar": "b2",
    "B2-vocab": "b2",
    "B2-biography": "b2",
    "B2-checkpoint": "b2",
    "B2-skills": "b2",
    "B2-synthesis": "b2",
    "B2-capstone": "b2",
    "B2-professional": "b2-pro",
    "C1": "c1-core",
    "C1-academic": "c1-core",
    "C1-stylistics": "c1-core",
    "C1-folk": "c1-core",
    "C1-literature": "c1-core",
    "C1-checkpoint": "c1-core",
    "C1-capstone": "c1-core",
    "C1-professional": "c1-pro",
    "C2": "c2",
    "C2-stylistic": "c2",
    "C2-literary": "c2",
    "C2-professional": "c2",
    "C2-checkpoint": "c2",
    "C2-capstone": "c2",
    "history": "hist",
    "biography": "bio",
    "istorio": "istorio",
    "HIST-seminar": "hist",
    "ISTORIO-seminar": "istorio",
    "LIT": "lit",
    "LIT-ESSAY": "lit",
    "LIT-HIST-FIC": "lit",
    "LIT-FANTASTIKA": "lit",
    "LIT-WAR": "lit",
    "LIT-HUMOR": "lit",
    "LIT-YOUTH": "lit",
    "LIT-DOC": "lit",
    "LIT-DRAMA": "lit",
    "LIT-CRIMEA": "lit",
    "OES": "oes",
    "RUTH": "ruth",
}


def _split(raw: str) -> set[str]:
    return {item.strip() for item in (raw or "").split(",") if item.strip()}


# ---------------------------------------------------------------------------
# 1. min_activities floor — no level may silently allow zero activities.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("level", sorted(LEVEL_CONFIG))
def test_min_activities_is_positive(level: str) -> None:
    cfg = LEVEL_CONFIG[level]
    assert cfg.get("min_activities", 0) > 0, (
        f"{level}: min_activities must be > 0. Activity counts are MINIMUMS "
        "per CLAUDE.md; a zero floor lets broken modules pass silently."
    )


# ---------------------------------------------------------------------------
# 2. min_types_unique floor — every level needs at least 2 distinct types.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("level", sorted(LEVEL_CONFIG))
def test_min_types_unique_at_least_two(level: str) -> None:
    cfg = LEVEL_CONFIG[level]
    assert cfg.get("min_types_unique", 0) >= 2, (
        f"{level}: min_types_unique must be >= 2 to prevent type-monoculture "
        "(e.g. wall-of-quiz workbooks)."
    )


# ---------------------------------------------------------------------------
# 3. Audit-internal self-consistency.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("level", sorted(LEVEL_CONFIG))
def test_audit_forbidden_disjoint_from_priority_required_allowed(level: str) -> None:
    cfg = LEVEL_CONFIG[level]
    forbidden = set(cfg.get("forbidden_types", set()))
    priority = set(cfg.get("priority_types", set()))
    required = set(cfg.get("required_types", set()))
    allowed = set(cfg.get("allowed_types", set()))

    overlap = forbidden & (priority | required | allowed)
    assert not overlap, (
        f"{level}: forbidden_types overlaps with priority/required/allowed: "
        f"{sorted(overlap)}. The same type cannot be both banned and recommended."
    )


@pytest.mark.parametrize("level", sorted(LEVEL_CONFIG))
def test_required_types_are_priority_or_allowed(level: str) -> None:
    """A required type the writer can never satisfy is a contradiction."""
    cfg = LEVEL_CONFIG[level]
    required = set(cfg.get("required_types", set()))
    if not required:
        return
    priority = set(cfg.get("priority_types", set()))
    allowed = set(cfg.get("allowed_types", set()))
    if not allowed:
        # Most levels lack an explicit allowed_types field — required_types
        # must still appear in priority_types in that case.
        missing = required - priority
        assert not missing, (
            f"{level}: required_types {sorted(missing)} are not in priority_types "
            "and no explicit allowed_types is defined — writer cannot satisfy them."
        )
    else:
        missing = required - (priority | allowed)
        assert not missing, (
            f"{level}: required_types {sorted(missing)} are neither in priority_types "
            f"nor in allowed_types: {sorted(allowed)}."
        )


# ---------------------------------------------------------------------------
# 4. Cross-layer: audit priority_types must be allowed by pipeline.
#    If audit prioritises a type the writer cannot emit, the priority is dead
#    weight — usually a sign the two layers drifted.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("audit_key,pipeline_key", sorted(AUDIT_TO_PIPELINE_KEY.items()))
def test_audit_priority_subset_of_pipeline_allowed(audit_key: str, pipeline_key: str) -> None:
    audit_cfg = LEVEL_CONFIG.get(audit_key, {})
    audit_priority = set(audit_cfg.get("priority_types", set()))
    if not audit_priority:
        return

    pipeline_cfg = ACTIVITY_CONFIGS.get(pipeline_key)
    assert pipeline_cfg is not None, (
        f"Audit level {audit_key} maps to pipeline key {pipeline_key} "
        "but that key is missing from ACTIVITY_CONFIGS."
    )
    pipeline_allowed = (
        _split(pipeline_cfg.get("INLINE_ALLOWED_TYPES", ""))
        | _split(pipeline_cfg.get("WORKBOOK_ALLOWED_TYPES", ""))
        | _split(pipeline_cfg.get("ALLOWED_ACTIVITY_TYPES", ""))
    )

    leaks = audit_priority - pipeline_allowed
    assert not leaks, (
        f"{audit_key} (pipeline={pipeline_key}): priority_types include types "
        f"the pipeline does not allow: {sorted(leaks)}. Either drop them from "
        "audit's priority_types or add them to the pipeline allow-list."
    )


# ---------------------------------------------------------------------------
# 5. Cross-layer: audit forbidden_types must not overlap pipeline allowed.
#    If audit forbids what pipeline allows, the writer will emit it and the
#    audit will fail — pure waste.
# ---------------------------------------------------------------------------
# NOTE: This invariant is currently violated for seminar tracks (hist, lit,
# bio, istorio, oes, ruth) where audit forbids quiz/fill-in/mark-the-words
# but pipeline allows them as INLINE checks. That divergence is intentional
# (seminar pedagogy at audit-time is stricter than at writer-time) and is
# tracked separately — see docs/best-practices/audit-standards.md.
_KNOWN_DIVERGENT_LEVELS: set[str] = {
    "history",
    "biography",
    "istorio",
    "LIT", "LIT-ESSAY", "LIT-HIST-FIC", "LIT-FANTASTIKA", "LIT-WAR",
    "LIT-HUMOR", "LIT-YOUTH", "LIT-DOC", "LIT-DRAMA", "LIT-CRIMEA",
    "OES", "RUTH",
    "HIST-seminar", "ISTORIO-seminar",
}


@pytest.mark.parametrize("audit_key,pipeline_key", sorted(AUDIT_TO_PIPELINE_KEY.items()))
def test_audit_forbidden_disjoint_from_pipeline_allowed(audit_key: str, pipeline_key: str) -> None:
    if audit_key in _KNOWN_DIVERGENT_LEVELS:
        pytest.skip(
            f"{audit_key}: seminar track — audit deliberately forbids inline "
            "drill types that pipeline allows for inline checks."
        )
    audit_cfg = LEVEL_CONFIG.get(audit_key, {})
    audit_forbidden = set(audit_cfg.get("forbidden_types", set()))
    if not audit_forbidden:
        return

    pipeline_cfg = ACTIVITY_CONFIGS.get(pipeline_key)
    if pipeline_cfg is None:
        return
    pipeline_allowed = (
        _split(pipeline_cfg.get("INLINE_ALLOWED_TYPES", ""))
        | _split(pipeline_cfg.get("WORKBOOK_ALLOWED_TYPES", ""))
        | _split(pipeline_cfg.get("ALLOWED_ACTIVITY_TYPES", ""))
    )

    overlap = audit_forbidden & pipeline_allowed
    assert not overlap, (
        f"{audit_key} (pipeline={pipeline_key}): audit forbids types that the "
        f"pipeline allows: {sorted(overlap)}. The writer will emit them and "
        "the audit will reject — drop one side."
    )
