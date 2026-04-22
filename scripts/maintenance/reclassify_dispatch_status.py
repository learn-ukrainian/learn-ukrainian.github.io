#!/usr/bin/env python
"""Reclassify persisted delegate task states after runtime classifier fixes.

Walks ``batch_state/tasks/*.json`` and revisits any task currently marked
``rate_limited`` using the current adapter parsing logic plus whatever saved
signals we still have in the task file / usage logs.

Issue: #1404
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import delegate
from agent_runtime.runner import _load_adapter

DEFAULT_TASKS_DIR = REPO_ROOT / "batch_state" / "tasks"
DEFAULT_USAGE_DIR = REPO_ROOT / "batch_state" / "api_usage"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _backup_task_file(path: Path) -> Path:
    backup_path = path.with_suffix(f"{path.suffix}.bak")
    if not backup_path.exists():
        shutil.copy2(path, backup_path)
    return backup_path


def _load_usage_by_task_id(usage_dir: Path) -> dict[str, dict[str, Any]]:
    """Return the newest usage record we have for each task_id."""
    records: dict[str, dict[str, Any]] = {}
    if not usage_dir.exists():
        return records

    for path in sorted(usage_dir.glob("usage_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            task_id = record.get("task_id")
            ts = record.get("ts")
            if not task_id or not ts:
                continue
            existing = records.get(task_id)
            if existing is None or ts >= existing.get("ts", ""):
                records[task_id] = record
    return records


def _reconstruct_streams(
    *,
    task_state: dict[str, Any],
    usage_record: dict[str, Any] | None,
) -> tuple[str, str, int | None, Path | None]:
    """Best-effort recovery of the raw signals the adapter classified.

    The #1404 historical false positive lost its true stdout because delegate
    caught ``RateLimitedError`` and only persisted the synthesized excerpt. For
    Claude with ``returncode == 0``, that usage ``stderr_excerpt`` is actually
    the original stdout body, so we feed it back as stdout for reclassification.
    """
    result_file: Path | None = None
    result_file_raw = task_state.get("result_file")
    if result_file_raw:
        candidate = Path(result_file_raw)
        if candidate.exists():
            result_file = candidate

    returncode = task_state.get("returncode")
    if returncode is None and usage_record is not None:
        returncode = usage_record.get("returncode")

    stdout = result_file.read_text().strip() if result_file is not None else ""
    stderr = ""

    agent = task_state.get("agent")
    usage_excerpt = (usage_record or {}).get("stderr_excerpt") or ""
    task_excerpt = task_state.get("stderr_excerpt") or ""

    if agent == "claude" and returncode == 0 and usage_excerpt and not stdout:
        stdout = usage_excerpt
    else:
        stderr = usage_excerpt or task_excerpt

    return stdout, stderr, returncode, result_file


def _reclassify_task(
    task_path: Path,
    *,
    usage_by_task_id: dict[str, dict[str, Any]],
    dry_run: bool,
) -> tuple[str, str, str] | None:
    task_state = _read_json(task_path)
    if task_state.get("status") != "rate_limited":
        return None

    task_id = task_state.get("task_id", task_path.stem)
    agent = task_state.get("agent")
    if not agent:
        return "skipped", task_id, "missing agent"

    usage_record = usage_by_task_id.get(task_id)
    stdout, stderr, returncode, result_file = _reconstruct_streams(
        task_state=task_state,
        usage_record=usage_record,
    )
    if returncode is None and not stdout and not stderr:
        return "skipped", task_id, "missing saved stderr/stdout/returncode"

    adapter = _load_adapter(agent)
    parse = adapter.parse_response(
        stdout=stdout,
        stderr=stderr,
        returncode=returncode if returncode is not None else 1,
        output_file=result_file,
    )
    new_status = delegate._classify_final_status(
        cancelled=False,
        rate_limited=parse.rate_limited,
        ok_outcome=parse.ok,
    )
    if new_status == task_state["status"]:
        return None
    if new_status != "done":
        return "skipped", task_id, f"reclassified to {new_status}, left unchanged"

    previous_status = task_state["status"]
    if dry_run:
        return "changed", task_id, f"{previous_status} -> {new_status} (dry-run)"

    backup_path = _backup_task_file(task_path)
    task_state["status"] = new_status
    _write_json(task_path, task_state)
    return "changed", task_id, f"{previous_status} -> {new_status} (backup: {backup_path.name})"


def reclassify_rate_limited_tasks(
    *,
    tasks_dir: Path = DEFAULT_TASKS_DIR,
    usage_dir: Path = DEFAULT_USAGE_DIR,
    dry_run: bool = False,
) -> dict[str, list[tuple[str, str]]]:
    usage_by_task_id = _load_usage_by_task_id(usage_dir)
    changes: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    if not tasks_dir.exists():
        return {"changed": changes, "skipped": skipped}

    for task_path in sorted(tasks_dir.glob("*.json")):
        outcome = _reclassify_task(
            task_path,
            usage_by_task_id=usage_by_task_id,
            dry_run=dry_run,
        )
        if outcome is None:
            continue
        kind, task_id, detail = outcome
        if kind == "changed":
            changes.append((task_id, detail))
        else:
            skipped.append((task_id, detail))
    return {"changed": changes, "skipped": skipped}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tasks-dir",
        type=Path,
        default=DEFAULT_TASKS_DIR,
        help="Directory containing delegate task JSON state files.",
    )
    parser.add_argument(
        "--usage-dir",
        type=Path,
        default=DEFAULT_USAGE_DIR,
        help="Directory containing runtime usage JSONL logs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report proposed task-state changes without rewriting JSON files.",
    )
    args = parser.parse_args()

    usage_by_task_id = _load_usage_by_task_id(args.usage_dir)
    changed: list[tuple[str, str]] = []
    skipped: list[tuple[str, str]] = []
    if args.tasks_dir.exists():
        for task_path in sorted(args.tasks_dir.glob("*.json")):
            outcome = _reclassify_task(
                task_path,
                usage_by_task_id=usage_by_task_id,
                dry_run=args.dry_run,
            )
            if outcome is None:
                continue
            kind, task_id, detail = outcome
            if kind == "changed":
                changed.append((task_id, detail))
            else:
                skipped.append((task_id, detail))

    for task_id, detail in changed:
        print(f"{task_id}: {detail}")
    for task_id, detail in skipped:
        print(f"{task_id}: skipped ({detail})")

    if not changed and not skipped:
        print("No task states changed.")
        return 0
    if args.dry_run:
        print(f"Dry run only. Proposed changes: {len(changed)}")
        return 0

    if changed:
        print(f"Changed: {len(changed)}")
    if skipped:
        print(f"Skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
