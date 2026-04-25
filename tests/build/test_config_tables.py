from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

ACTIVITY_CONFIGS = import_module("pipeline.config_tables").ACTIVITY_CONFIGS


TYPE_LIST_KEYS = (
    "INLINE_ALLOWED_TYPES",
    "WORKBOOK_ALLOWED_TYPES",
    "INLINE_PRIORITY_TYPES",
    "WORKBOOK_PRIORITY_TYPES",
    "ALLOWED_ACTIVITY_TYPES",
    "PRIORITY_TYPES",
)


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
