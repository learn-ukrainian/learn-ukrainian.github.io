from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

ACTIVITY_CONFIGS = import_module("pipeline.config_tables").ACTIVITY_CONFIGS
LEVEL_CONFIG = import_module("audit.config").LEVEL_CONFIG


TYPE_LIST_KEYS = (
    "INLINE_ALLOWED_TYPES",
    "WORKBOOK_ALLOWED_TYPES",
    "INLINE_PRIORITY_TYPES",
    "WORKBOOK_PRIORITY_TYPES",
    "ALLOWED_ACTIVITY_TYPES",
    "PRIORITY_TYPES",
)


# Pipeline → audit-canonical key mapping. Used for cross-layer reconciliation
# checks added in #1550 unit 4. Pipeline keys group sub-tracks under shared
# writer-prompt keys; the audit canonical key is the broadest matching
# LEVEL_CONFIG entry.
PIPELINE_TO_AUDIT_KEY: dict[str, str] = {
    "a1": "A1",
    "a2": "A2",
    "a1-checkpoint": "A1-checkpoint",
    "a2-checkpoint": "A2-checkpoint",
    "b1-core": "B1",
    "b2": "B2",
    "c1-core": "C1",
    "c2": "C2",
    "hist": "history",
    "bio": "biography",
    "istorio": "istorio",
    "lit": "LIT",
    "b2-pro": "B2-professional",
    "c1-pro": "C1-professional",
    "oes": "OES",
    "ruth": "RUTH",
}


def _split(raw: str) -> set[str]:
    return {item.strip() for item in (raw or "").split(",") if item.strip()}


def test_forbidden_activity_types_are_not_allowed_or_priority_types():
    for config_name, config in ACTIVITY_CONFIGS.items():
        forbidden = _split(config.get("FORBIDDEN_ACTIVITY_TYPES", ""))
        allowed_or_priority = set().union(
            *(_split(config.get(key, "")) for key in TYPE_LIST_KEYS)
        )

        assert forbidden.isdisjoint(allowed_or_priority), (
            f"{config_name} has forbidden type(s) also allowed/recommended: "
            f"{sorted(forbidden & allowed_or_priority)}"
        )


# ---------------------------------------------------------------------------
# Cross-layer assertions (#1550 unit 4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pipeline_key,audit_key", sorted(PIPELINE_TO_AUDIT_KEY.items()))
def test_items_min_aligns_with_audit_per_type_floor(pipeline_key: str, audit_key: str) -> None:
    """Pipeline ``ITEMS_MIN`` must not undershoot the LOWEST per-type audit floor.

    The actual density gate uses ``audit.config.ACTIVITY_COMPLEXITY[type][level]
    ['min_items']`` per activity, falling back to ``min_items_per_activity`` only
    for types without a per-type entry. Pipeline ``ITEMS_MIN`` is the writer's
    universal floor — it must be ≥ the lowest applicable per-type minimum so
    items the writer ships always satisfy the per-type density check.
    """
    from audit.config import ACTIVITY_COMPLEXITY

    pipeline_cfg = ACTIVITY_CONFIGS.get(pipeline_key, {})
    items_min_pipeline = int(pipeline_cfg.get("ITEMS_MIN", "0") or 0)
    if items_min_pipeline == 0:
        return

    # Collect the per-type min_items floors that apply to this audit level.
    per_type_floors: list[int] = []
    for type_rules in ACTIVITY_COMPLEXITY.values():
        rules = type_rules.get(audit_key)
        if not rules:
            continue
        for k in ("min_items", "pairs_min", "items_min"):
            if k in rules:
                per_type_floors.append(int(rules[k]))
                break
    if not per_type_floors:
        return

    # The writer's floor must clear the LOWEST per-type floor; per-type
    # complexity entries above pipeline ITEMS_MIN are caught by the audit's
    # per-type density gate and trigger writer self-correction.
    min_per_type = min(per_type_floors)
    assert items_min_pipeline >= min_per_type, (
        f"{pipeline_key} ITEMS_MIN={items_min_pipeline} is below the lowest "
        f"per-type audit floor for {audit_key} ({min_per_type}). Writer will "
        "ship sub-floor activities the audit rejects."
    )


@pytest.mark.parametrize("pipeline_key,audit_key", sorted(PIPELINE_TO_AUDIT_KEY.items()))
def test_pipeline_required_subset_of_audit_required_or_priority(
    pipeline_key: str, audit_key: str
) -> None:
    """Pipeline ``REQUIRED_TYPES`` must align with audit's required/priority sets.

    A pipeline-required type that is not at least audit-priority is suspicious:
    the writer is forced to produce something audit doesn't even prefer.
    """
    pipeline_cfg = ACTIVITY_CONFIGS.get(pipeline_key, {})
    audit_cfg = LEVEL_CONFIG.get(audit_key, {})
    pipeline_required = _split(pipeline_cfg.get("REQUIRED_TYPES", ""))
    if not pipeline_required:
        return
    audit_priority_or_required = set(audit_cfg.get("priority_types", set())) | set(
        audit_cfg.get("required_types", set())
    )
    leaks = pipeline_required - audit_priority_or_required
    assert not leaks, (
        f"{pipeline_key} REQUIRED_TYPES include types not in {audit_key} "
        f"priority_types/required_types: {sorted(leaks)}. Either drop the pipeline "
        "requirement or add to audit priority."
    )

