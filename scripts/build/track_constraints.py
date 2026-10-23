"""Track-level learned constraints and writer prompt assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from build.module_memory import module_memory_path

TRACK_CONSTRAINTS_FILENAME = "learned-constraints-track.yaml"


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text("utf-8"))


def _write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        "utf-8",
    )


def _active_constraints(payload: dict[str, Any]) -> list[dict[str, Any]]:
    constraints = payload.get("constraints") or []
    return [
        item
        for item in constraints
        if isinstance(item, dict) and str(item.get("status") or "") in {"active", "promoted"}
    ]


def _promotion_metrics(constraint: dict[str, Any]) -> dict[str, bool]:
    raw = constraint.get("promotion_metrics") or constraint.get("measured_improvement") or {}
    if not isinstance(raw, dict):
        raw = {}
    return {
        "attempt0_pass_rate_up": bool(raw.get("attempt0_pass_rate_up")),
        "hard_floor_failures_down": bool(raw.get("hard_floor_failures_down")),
        "recurrence_down": bool(raw.get("recurrence_down")),
    }


def load_track_constraints(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = _read_yaml(path)
    if not isinstance(payload, dict):
        return []
    return [
        item
        for item in (payload.get("constraints") or [])
        if isinstance(item, dict) and str(item.get("status") or "") == "promoted"
    ]


def load_effective_constraints(
    *,
    curriculum_root: Path,
    level: str,
    slug: str,
    track_constraints_path: Path | None = None,
) -> list[dict[str, Any]]:
    track_path = track_constraints_path or curriculum_root / TRACK_CONSTRAINTS_FILENAME
    track_constraints = load_track_constraints(track_path)

    module_path = module_memory_path(curriculum_root, level, slug)
    module_constraints: list[dict[str, Any]] = []
    if module_path.exists():
        payload = _read_yaml(module_path)
        if isinstance(payload, dict):
            module_constraints = _active_constraints(payload)

    effective: list[dict[str, Any]] = []
    overridden_keys: set[str] = set()
    for constraint in module_constraints:
        if constraint.get("override_track_level"):
            overridden_keys.add(
                str(constraint.get("normalized_id") or constraint.get("id") or "")
            )

    for constraint in track_constraints:
        key = str(constraint.get("normalized_id") or constraint.get("id") or "")
        if key in overridden_keys:
            continue
        effective.append(dict(constraint))

    effective.extend(dict(constraint) for constraint in module_constraints)
    return effective
