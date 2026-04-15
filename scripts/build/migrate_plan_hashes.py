#!/usr/bin/env python3
"""Backfill missing plan hashes in orchestration state files."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from build.io_utils import plan_hash, write_text_atomic
from build.plan_tracking import PLAN_HASH_PHASES

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
MISSING_PLAN_REASON = "plan_file_missing"


@dataclass(frozen=True)
class MigrationResult:
    """Outcome for a single state file."""

    level: str
    slug: str
    updated_phase_records: int
    stale_phase_records: int
    actions: tuple[str, ...]


def iter_state_files(curriculum_root: Path | None = None) -> list[Path]:
    """Return orchestration state paths for every track."""
    root = CURRICULUM_ROOT if curriculum_root is None else curriculum_root
    return sorted(root.glob("*/orchestration/*/state.json"))


def _read_state(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _plan_path(level: str, slug: str) -> Path:
    return CURRICULUM_ROOT / "plans" / level / f"{slug}.yaml"


def _clear_missing_plan_stale_marker(info: dict[str, Any]) -> bool:
    """Undo this migration's missing-plan stale marker if a plan now exists."""
    if info.get("status") != "stale" or info.get("stale_reason") != MISSING_PLAN_REASON:
        return False

    previous_status = info.get("previous_status")
    if isinstance(previous_status, str) and previous_status:
        info["status"] = previous_status
    else:
        info.pop("status", None)

    info.pop("previous_status", None)
    info.pop("stale_reason", None)
    return True


def _backfill_phase_record(
    info: dict[str, Any],
    *,
    current_plan_hash: str,
) -> tuple[bool, list[str]]:
    changed = False
    actions: list[str] = []

    info["plan_hash"] = current_plan_hash
    changed = True
    actions.append("added plan_hash")

    if _clear_missing_plan_stale_marker(info):
        changed = True
        actions.append("cleared missing-plan stale marker")

    return changed, actions


def _mark_phase_plan_missing(info: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    changed = False
    stale_marked = False
    actions: list[str] = []

    if info.get("status") != "stale" or info.get("stale_reason") != MISSING_PLAN_REASON:
        previous_status = info.get("status")
        if isinstance(previous_status, str) and previous_status:
            info["previous_status"] = previous_status
        info["status"] = "stale"
        info["stale_reason"] = MISSING_PLAN_REASON
        changed = True
        stale_marked = True
        actions.append("marked stale (plan_file_missing)")

    return changed, stale_marked, actions


def migrate_state_file(state_path: Path, *, dry_run: bool = False) -> MigrationResult | None:
    """Migrate one state.json file if it has tracked phase records without plan_hash."""
    state = _read_state(state_path)
    if state is None:
        return None

    phases = state.get("phases")
    if not isinstance(phases, dict):
        return None

    level = state_path.parents[2].name
    slug = state_path.parent.name
    plan_path = _plan_path(level, slug)
    current_plan_hash = plan_hash(plan_path) if plan_path.exists() else None

    updated_phase_records = 0
    stale_phase_records = 0
    actions: list[str] = []

    for phase_name in PLAN_HASH_PHASES:
        phase_info = phases.get(phase_name)
        if not isinstance(phase_info, dict):
            continue
        if "plan_hash" in phase_info:
            continue

        if current_plan_hash is not None:
            changed, phase_actions = _backfill_phase_record(
                phase_info,
                current_plan_hash=current_plan_hash,
            )
            if changed:
                updated_phase_records += 1
                actions.append(f"{phase_name}: {', '.join(phase_actions)}")
            continue

        changed, stale_marked, phase_actions = _mark_phase_plan_missing(phase_info)
        if changed:
            updated_phase_records += 1
            actions.append(f"{phase_name}: {', '.join(phase_actions)}")
        if stale_marked:
            stale_phase_records += 1

    if updated_phase_records and not dry_run:
        state["phases"] = phases
        write_text_atomic(
            state_path,
            json.dumps(state, indent=2, ensure_ascii=False),
        )

    return MigrationResult(
        level=level,
        slug=slug,
        updated_phase_records=updated_phase_records,
        stale_phase_records=stale_phase_records,
        actions=tuple(actions),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned migration without writing state.json files.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    scanned_modules = 0
    touched_modules = 0
    updated_phase_records = 0
    stale_phase_records = 0

    for state_path in iter_state_files():
        scanned_modules += 1
        result = migrate_state_file(state_path, dry_run=args.dry_run)
        if result is None or result.updated_phase_records == 0:
            continue

        touched_modules += 1
        updated_phase_records += result.updated_phase_records
        stale_phase_records += result.stale_phase_records

        action_label = "DRY RUN" if args.dry_run else "UPDATED"
        action_summary = "; ".join(result.actions)
        print(f"{action_label} {result.level}/{result.slug}: {action_summary}")

    mode = "dry-run" if args.dry_run else "apply"
    print(
        "Summary "
        f"({mode}): scanned {scanned_modules} modules; "
        f"updated {updated_phase_records} phase records; "
        f"marked {stale_phase_records} stale; "
        f"touched {touched_modules} modules"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
