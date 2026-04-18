"""Track-level learned constraints and writer prompt assembly."""

from __future__ import annotations

from collections import defaultdict
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


def promote_track_constraints(
    curriculum_root: Path,
    *,
    output_path: Path | None = None,
    min_modules: int = 8,
    min_levels: int = 2,
) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "constraints": [],
            "levels": set(),
            "modules": set(),
            "conflicts_with_plan": False,
            "metrics": {
                "attempt0_pass_rate_up": False,
                "hard_floor_failures_down": False,
                "recurrence_down": False,
            },
        }
    )

    for memory_file in sorted(curriculum_root.glob("*/orchestration/*/module-memory.yaml")):
        level = memory_file.parents[2].name
        slug = memory_file.parent.name
        payload = _read_yaml(memory_file)
        if not isinstance(payload, dict):
            continue
        for constraint in _active_constraints(payload):
            key = str(
                constraint.get("normalized_id")
                or constraint.get("id")
                or constraint.get("error_class")
            )
            group = groups[key]
            group["constraints"].append(constraint)
            group["levels"].add(level)
            group["modules"].add((level, slug))
            group["conflicts_with_plan"] = group["conflicts_with_plan"] or bool(
                constraint.get("conflicts_with_plan")
            )
            metrics = _promotion_metrics(constraint)
            for metric_name, passed in metrics.items():
                group["metrics"][metric_name] = group["metrics"][metric_name] or passed

    promoted = []
    for _key, group in sorted(groups.items()):
        if len(group["modules"]) < min_modules:
            continue
        if len(group["levels"]) < min_levels:
            continue
        if group["conflicts_with_plan"]:
            continue
        if not all(group["metrics"].values()):
            continue

        exemplar = dict(group["constraints"][0])
        exemplar["status"] = "promoted"
        exemplar["promoted_from_modules"] = len(group["modules"])
        exemplar["promoted_levels"] = sorted(group["levels"])
        exemplar["promotion_metrics"] = dict(group["metrics"])
        promoted.append(exemplar)

    result = {"constraints": promoted}
    destination = output_path or curriculum_root / TRACK_CONSTRAINTS_FILENAME
    _write_yaml(destination, result)
    return result


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


def build_writer_constraints_section(
    *,
    curriculum_root: Path,
    level: str,
    slug: str,
    track_constraints_path: Path | None = None,
) -> str:
    constraints = load_effective_constraints(
        curriculum_root=curriculum_root,
        level=level,
        slug=slug,
        track_constraints_path=track_constraints_path,
    )
    if not constraints:
        return ""

    lines = [
        "## Learned Constraints",
        "",
        "These constraints come from prior review rounds. They apply to the writer only.",
        "",
    ]
    for constraint in constraints:
        scope = constraint.get("scope") or {}
        scope_parts = [
            f"section={scope.get('section_title') or scope.get('section')}"
            if scope.get("section_title") or scope.get("section")
            else None,
            f"speaker={scope.get('speaker')}" if scope.get("speaker") else None,
            f"lexeme={scope.get('target_lexeme')}" if scope.get("target_lexeme") else None,
        ]
        scope_text = ", ".join(part for part in scope_parts if part) or "global"
        lines.append(
            "- "
            + f"[{constraint.get('dimension')}/{constraint.get('error_class')}] "
            + f"{constraint.get('directive')} ({scope_text})"
        )
    return "\n".join(lines) + "\n"
