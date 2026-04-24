"""Helpers for tracking plan drift against v6 pipeline state."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

PLAN_HASH_PHASES = ("skeleton", "write", "honesty-annotate", "exercises", "annotate", "verify")
PLAN_DRIFT_GUARD_STEPS = {"review", "publish", "audit"}
_PHASE_SATISFIED_STATUSES = {"complete", "skipped"}
_PHASE_TS_FUDGE_SECONDS = 1.0


@dataclass(frozen=True)
class PlanHashDrift:
    """A detected plan drift event for a module state."""

    current_plan_hash: str
    stale_start_phase: str
    mismatched_phases: tuple[str, ...]


def plan_path_for(curriculum_root: Path, track: str, slug: str) -> Path | None:
    """Resolve the module plan path for any track without level-specific branching."""
    plans_root = curriculum_root / "plans"

    direct = plans_root / track / f"{slug}.yaml"
    if direct.exists():
        return direct

    flat = plans_root / f"{slug}.yaml"
    if flat.exists():
        return flat

    matches = sorted(plans_root.glob(f"*/{slug}.yaml"))
    if len(matches) == 1:
        return matches[0]

    for candidate in matches:
        if candidate.parent.name == track:
            return candidate

    return None


def current_plan_hash_for(curriculum_root: Path, track: str, slug: str) -> str | None:
    """Return the SHA256 of the current plan YAML bytes."""
    plan_path = plan_path_for(curriculum_root, track, slug)
    if not plan_path or not plan_path.exists():
        return None
    return hashlib.sha256(plan_path.read_bytes()).hexdigest()


def plan_mtime_for(curriculum_root: Path, track: str, slug: str) -> datetime | None:
    """Return the current plan mtime in UTC, if the plan exists."""
    plan_path = plan_path_for(curriculum_root, track, slug)
    if not plan_path or not plan_path.exists():
        return None
    return datetime.fromtimestamp(plan_path.stat().st_mtime, tz=UTC)


def parse_phase_timestamp(raw_ts: object) -> datetime | None:
    """Parse v6 phase timestamps produced by isoformat() / RFC3339-like strings."""
    if not isinstance(raw_ts, str) or not raw_ts.strip():
        return None
    normalized = raw_ts.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def ordered_phases_from(
    phase_order: list[str] | tuple[str, ...],
    start_phase: str,
    existing_phases: dict[str, object] | None = None,
) -> tuple[str, ...]:
    """Return pipeline phases from start_phase onward, preserving pipeline order."""
    try:
        start_idx = phase_order.index(start_phase)
    except ValueError:
        return ()

    ordered = phase_order[start_idx:]
    if existing_phases is None:
        return tuple(ordered)
    return tuple(phase for phase in ordered if phase in existing_phases)


def detect_plan_hash_drift(
    state: dict,
    current_plan_hash: str | None,
) -> PlanHashDrift | None:
    """Detect whether tracked writer phases were run against an older plan hash."""
    if not current_plan_hash:
        return None

    phases = state.get("phases", {})
    if not isinstance(phases, dict):
        return None

    mismatched = []
    for phase in PLAN_HASH_PHASES:
        info = phases.get(phase)
        if not isinstance(info, dict):
            continue
        if info.get("status") not in _PHASE_SATISFIED_STATUSES:
            continue
        if info.get("plan_hash") != current_plan_hash:
            mismatched.append(phase)

    if not mismatched:
        return None

    return PlanHashDrift(
        current_plan_hash=current_plan_hash,
        stale_start_phase=mismatched[0],
        mismatched_phases=tuple(mismatched),
    )


def detect_plan_timestamp_drift(
    state: dict,
    plan_mtime: datetime | None,
) -> str | None:
    """Find the earliest tracked phase older than the current plan file."""
    if plan_mtime is None:
        return None

    phases = state.get("phases", {})
    if not isinstance(phases, dict):
        return None

    for phase in PLAN_HASH_PHASES:
        info = phases.get(phase)
        if not isinstance(info, dict):
            continue
        if info.get("status") not in _PHASE_SATISFIED_STATUSES:
            continue
        phase_ts = parse_phase_timestamp(info.get("ts"))
        if phase_ts is None:
            continue
        if phase_ts.timestamp() + _PHASE_TS_FUDGE_SECONDS < plan_mtime.timestamp():
            return phase

    return None
