"""Parallel-agent coordination ledger.

This module stores runtime coordination state under ``batch_state/`` so
parallel workers can report task state without editing shared markdown
handoff files. It is intentionally small and local-first: delegate.py still
owns process lifecycle, while this ledger owns task metadata, ownership, and
events needed by the orchestrator.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
ACTIVE_STATUSES = {"planned", "queued", "running", "reviewing", "blocked"}
TERMINAL_STATUSES = {"done", "closed", "cancelled", "failed", "timeout"}
VALID_STATUSES = ACTIVE_STATUSES | TERMINAL_STATUSES
TASK_FAMILIES = {
    "architecture",
    "code_review",
    "coding",
    "content_writing",
    "creative_writing",
    "design",
    "documentation",
    "operations_release",
    "pedagogy_review",
    "refactoring",
    "research_verification",
    "translation_localization",
}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class LedgerError(ValueError):
    """Raised for invalid ledger input."""


class OwnershipConflictError(LedgerError):
    """Raised when two active tasks claim overlapping owned paths."""

    def __init__(self, task_id: str, conflicts: list[dict[str, Any]]) -> None:
        super().__init__(f"task {task_id!r} conflicts with active owned paths")
        self.task_id = task_id
        self.conflicts = conflicts


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def safe_id(value: str) -> str:
    raw = value.strip()
    if not SAFE_ID_RE.fullmatch(raw):
        raise LedgerError("task ids must match [A-Za-z0-9][A-Za-z0-9._:-]*")
    return raw


def safe_path_component(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "_", value).strip("._") or "task"


def ledger_dir(repo_root: Path) -> Path:
    return repo_root / "batch_state" / "agent-ledger"


def tasks_dir(repo_root: Path) -> Path:
    return ledger_dir(repo_root) / "tasks"


def task_path(repo_root: Path, task_id: str) -> Path:
    return tasks_dir(repo_root) / f"{safe_path_component(task_id)}.json"


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def normalize_owned_path(path: str) -> str:
    value = path.strip().replace("\\", "/")
    value = re.sub(r"/+", "/", value).strip("/")
    if not value or value.startswith("..") or "/../" in f"/{value}/":
        raise LedgerError(f"invalid owned path: {path!r}")
    return value


def normalize_owned_paths(paths: list[str] | None) -> list[str]:
    normalized: list[str] = []
    for path in paths or []:
        item = normalize_owned_path(path)
        if item not in normalized:
            normalized.append(item)
    return normalized


def paths_overlap(left: str, right: str) -> bool:
    left = normalize_owned_path(left)
    right = normalize_owned_path(right)
    return left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/")


def list_tasks(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not tasks_dir(repo_root).exists():
        return rows
    for path in sorted(tasks_dir(repo_root).glob("*.json")):
        task = read_json(path)
        if task:
            rows.append(task)
    rows.sort(key=lambda row: str(row.get("updated_at") or row.get("created_at") or ""), reverse=True)
    return rows


def get_task(repo_root: Path, task_id: str) -> dict[str, Any] | None:
    return read_json(task_path(repo_root, safe_id(task_id)))


def active_tasks(repo_root: Path) -> list[dict[str, Any]]:
    return [task for task in list_tasks(repo_root) if task.get("status") in ACTIVE_STATUSES]


def _overlap_conflicts(
    repo_root: Path,
    *,
    task_id: str,
    owned_paths: list[str],
) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    if not owned_paths:
        return conflicts
    for task in active_tasks(repo_root):
        other_id = str(task.get("task_id") or "")
        if other_id == task_id:
            continue
        for left in owned_paths:
            for right in task.get("owned_paths") or []:
                if paths_overlap(left, str(right)):
                    conflicts.append(
                        {
                            "task_id": other_id,
                            "agent": task.get("agent"),
                            "status": task.get("status"),
                            "owned_path": right,
                            "requested_path": left,
                        }
                    )
    return conflicts


def task_event(
    *,
    event_type: str,
    actor: str,
    message: str = "",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "timestamp": isoformat_z(utc_now()),
        "type": event_type,
        "actor": actor,
        "message": message,
        "data": data or {},
    }


def upsert_task(
    repo_root: Path,
    *,
    task_id: str,
    agent: str,
    status: str = "planned",
    issue: int | None = None,
    lane: str | None = None,
    module_family: str | None = None,
    task_family: str | None = None,
    model: str | None = None,
    thread_id: str | None = None,
    branch: str | None = None,
    worktree: str | None = None,
    owned_paths: list[str] | None = None,
    allow_conflicts: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task_id = safe_id(task_id)
    if status not in VALID_STATUSES:
        raise LedgerError(f"invalid status: {status}")
    if task_family and task_family not in TASK_FAMILIES:
        raise LedgerError(f"invalid task_family: {task_family}")

    owned = normalize_owned_paths(owned_paths)
    if status in ACTIVE_STATUSES and not allow_conflicts:
        conflicts = _overlap_conflicts(repo_root, task_id=task_id, owned_paths=owned)
        if conflicts:
            raise OwnershipConflictError(task_id, conflicts)

    now = isoformat_z(utc_now())
    existing = get_task(repo_root, task_id) or {}
    events = list(existing.get("events") or [])
    if not existing:
        events.append(task_event(event_type="created", actor=agent, message="task registered"))
    elif existing.get("status") != status:
        events.append(
            task_event(
                event_type="status",
                actor=agent,
                message=f"{existing.get('status')} -> {status}",
            )
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": task_id,
        "issue": issue,
        "lane": lane,
        "module_family": module_family,
        "task_family": task_family,
        "agent": agent,
        "model": model,
        "thread_id": thread_id,
        "branch": branch,
        "worktree": worktree,
        "owned_paths": owned,
        "status": status,
        "heartbeat_at": existing.get("heartbeat_at"),
        "validation": existing.get("validation") or {},
        "review": existing.get("review") or {},
        "ci": existing.get("ci") or {},
        "pr_url": existing.get("pr_url"),
        "metadata": {**(existing.get("metadata") or {}), **(metadata or {})},
        "events": events,
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
    }
    write_json_atomic(task_path(repo_root, task_id), payload)
    return payload


def append_event(
    repo_root: Path,
    task_id: str,
    *,
    event_type: str,
    actor: str,
    message: str = "",
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    task = get_task(repo_root, task_id)
    if task is None:
        raise LedgerError(f"task not found: {task_id}")
    task.setdefault("events", []).append(
        task_event(event_type=event_type, actor=actor, message=message, data=data)
    )
    task["updated_at"] = isoformat_z(utc_now())
    write_json_atomic(task_path(repo_root, task_id), task)
    return task


def heartbeat(repo_root: Path, task_id: str, *, actor: str, message: str = "") -> dict[str, Any]:
    task = append_event(
        repo_root,
        task_id,
        event_type="heartbeat",
        actor=actor,
        message=message,
    )
    task["heartbeat_at"] = task["events"][-1]["timestamp"]
    write_json_atomic(task_path(repo_root, task_id), task)
    return task


def summary(repo_root: Path) -> dict[str, Any]:
    tasks = list_tasks(repo_root)
    active = [task for task in tasks if task.get("status") in ACTIVE_STATUSES]
    by_family: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    for task in tasks:
        family = str(task.get("task_family") or "unspecified")
        agent = str(task.get("agent") or "unknown")
        by_family[family] = by_family.get(family, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "total": len(tasks),
        "active": len(active),
        "tasks": tasks,
        "by_task_family": by_family,
        "by_agent": by_agent,
    }


def _json_arg(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise LedgerError("--metadata/--data must be a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root_from_file()))
    sub = parser.add_subparsers(dest="command", required=True)

    upsert = sub.add_parser("upsert-task")
    upsert.add_argument("--task-id", required=True)
    upsert.add_argument("--agent", required=True)
    upsert.add_argument("--status", default="planned", choices=sorted(VALID_STATUSES))
    upsert.add_argument("--issue", type=int)
    upsert.add_argument("--lane")
    upsert.add_argument("--module-family")
    upsert.add_argument("--task-family", choices=sorted(TASK_FAMILIES))
    upsert.add_argument("--model")
    upsert.add_argument("--thread-id")
    upsert.add_argument("--branch")
    upsert.add_argument("--worktree")
    upsert.add_argument("--owned-path", action="append", default=[])
    upsert.add_argument("--allow-conflicts", action="store_true")
    upsert.add_argument("--metadata")

    event = sub.add_parser("event")
    event.add_argument("--task-id", required=True)
    event.add_argument("--type", required=True, dest="event_type")
    event.add_argument("--actor", required=True)
    event.add_argument("--message", default="")
    event.add_argument("--data")

    beat = sub.add_parser("heartbeat")
    beat.add_argument("--task-id", required=True)
    beat.add_argument("--actor", required=True)
    beat.add_argument("--message", default="")

    sub.add_parser("summary")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root)
    try:
        if args.command == "upsert-task":
            payload = upsert_task(
                repo_root,
                task_id=args.task_id,
                agent=args.agent,
                status=args.status,
                issue=args.issue,
                lane=args.lane,
                module_family=args.module_family,
                task_family=args.task_family,
                model=args.model,
                thread_id=args.thread_id,
                branch=args.branch,
                worktree=args.worktree,
                owned_paths=args.owned_path,
                allow_conflicts=args.allow_conflicts,
                metadata=_json_arg(args.metadata),
            )
        elif args.command == "event":
            payload = append_event(
                repo_root,
                args.task_id,
                event_type=args.event_type,
                actor=args.actor,
                message=args.message,
                data=_json_arg(args.data),
            )
        elif args.command == "heartbeat":
            payload = heartbeat(repo_root, args.task_id, actor=args.actor, message=args.message)
        else:
            payload = summary(repo_root)
    except OwnershipConflictError as exc:
        print(json.dumps({"error": "ownership_conflict", "conflicts": exc.conflicts}, indent=2))
        return 2
    except LedgerError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
