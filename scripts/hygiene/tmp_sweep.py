"""Attribute unmanaged system-temp directories; preserve every unproven owner (#8755).

The opt-in unattributed-scratch class (#9737, operator retention decision
2026-10-06) also reaps hand-made top-level scratch that no task owns, once it
is proven quiet and unreferenced by any inspectable process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.common.scratch import DEFAULT_SCRATCH_ROOT, fallback_scratch_root, resolve_scratch_root
from scripts.common.task_scratch import TaskScratchError, mount_points
from scripts.common.task_store_paths import tasks_dir
from scripts.hygiene.retention_engine import plan_digest, reap_attributed_temp
from scripts.orchestration.tmp_leak_sweep import (
    _process_state,
    _process_vanished,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
# Unsettled deliverables (needs_finalize), blocked work and dry-run records are held.
REAPABLE_STATES = frozenset({"done", "failed", "timeout", "cancelled", "crashed", "rate_limited", "no_deliverable"})
HARNESS_NAMES = re.compile(r"^(?:claude|codex|gemini|agy|cursor|kimi|hermes|acpx)(?:[-_.]|$)")
# Never swept: dot-entries, harness/session sockets and systemd private trees.
EXCLUDED_NAMES = re.compile(r"^(?:\.|claude-|tmux-|ssh-|systemd-)")
SYSTEM_TEMP_AREAS = (Path("/tmp"), Path("/private/tmp"), Path("/var/tmp"))


@dataclass(frozen=True)
class ScratchPolicy:
    """Unattributed-scratch thresholds (#9737); both default to 24 hours.

    ``min_age_s`` gates the top-level entry itself; ``quiet_s`` gates the
    newest write anywhere below it. Change time counts as a write, so an
    archive extracted recently with old preserved mtimes stays young.
    """

    min_age_s: float = 24 * 3600
    quiet_s: float = 24 * 3600

    def __post_init__(self) -> None:
        for value in (self.min_age_s, self.quiet_s):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("scratch thresholds must be finite and positive")


def load_tasks(root: Path) -> dict[str, dict[str, Any]]:
    """Read only current task records; missing/invalid records never authorize removal."""
    records = {}
    for path in root.glob("*.json"):
        # Even an unreadable/malformed newer run shadows an older parent ID.
        records[path.stem] = {"status": None, "finished_at": None, "record_sha256": None}
        try:
            if path.is_symlink():
                continue
            raw = path.read_bytes()
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("task_id") == path.stem:
                records[path.stem] = {
                    "status": data.get("status"),
                    "finished_at": data.get("finished_at"),
                    "record_sha256": hashlib.sha256(raw).hexdigest(),
                }
        except (OSError, ValueError):
            continue
    return records


def task_attribution(name: str, records: dict[str, dict[str, Any]]) -> list[str]:
    """Use complete task IDs with a suffix boundary, never issue/prefix guesses."""
    matches = [key for key in records if name == key or any(name.startswith(key + sep) for sep in ("-", ".", "_"))]
    # A specific run takes precedence over its earlier, shorter task ID.
    return sorted(matches, key=lambda key: (-len(key), key))[:1]


def process_snapshot(
    proc_root: Path = Path("/proc"), *, tolerate_uninspectable: bool = False
) -> tuple[list[tuple[int, Path]], bool]:
    """Collect cwd/open-FD references for ALL users; unreadable live processes are unknown.

    The caller is included. Zombies and processes that vanish during inspection
    hold no references. No command lines, environment values or private paths
    are emitted in reports. ``tolerate_uninspectable`` keeps the snapshot
    complete when the kernel denies access (non-dumpable or foreign-user
    processes): the unattributed-scratch rule covers every process the agent
    user can inspect, as the operator's manual rule did. Any other read
    failure still makes the snapshot incomplete.
    """
    references: list[tuple[int, Path]] = []
    complete = True
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        return [], False
    for entry in entries:
        if not entry.name.isdigit():
            continue
        state = _process_state(entry)
        if state in {"Z", "X"}:
            continue
        targets: list[str] = []
        try:
            if state is None:
                raise OSError("unknown process state")
            targets = [os.readlink(entry / "cwd")]
            for fd in (entry / "fd").iterdir():
                try:
                    targets.append(os.readlink(fd))
                except FileNotFoundError:
                    continue  # descriptor closed during the scan
        except OSError as error:
            denied = tolerate_uninspectable and isinstance(error, PermissionError)
            if not denied and not _process_vanished(entry):
                complete = False
        for target in targets:
            if target.startswith("/"):
                references.append((int(entry.name), Path(target.removesuffix(" (deleted)"))))
    return references, complete


def registered_worktrees(repo_root: Path) -> set[Path] | None:
    """Query the current repository; a failed Git probe is never clear."""
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain", "-z"],
            cwd=repo_root,
            capture_output=True,
            check=False,
            timeout=15,
        )
        if result.returncode:
            return None
        return {
            Path(os.fsdecode(field[9:])).resolve()
            for field in result.stdout.split(b"\0")
            if field.startswith(b"worktree ")
        }
    except (OSError, subprocess.SubprocessError):
        return None


def tree_facts(path: Path) -> tuple[int, float, float, str | None]:
    """Allocated bytes, latest write and latest change; refuse Git metadata, foreign owners and mounts.

    Never follow symlinks or cross devices. In-tree Git metadata also protects
    worktrees registered with a repository other than this checkout. A file
    can be a bind-mount target, so every node is checked against the mounts.
    """
    allocated = 0
    newest = 0.0
    changed = 0.0
    reason = None
    try:
        mounts = mount_points()
        if mounts is None:
            return 0, 0, 0, "mount_probe_unknown"
        root_stat = path.lstat()
        device = root_stat.st_dev
        seen = set()
        pending = [path]
        while pending:
            node = pending.pop()
            info = node.lstat()
            newest = max(newest, info.st_mtime)
            changed = max(changed, info.st_mtime, info.st_ctime)
            identity = info.st_dev, info.st_ino
            if identity not in seen:
                allocated += info.st_blocks * 512
                seen.add(identity)
            if not stat.S_ISDIR(info.st_mode) and info.st_nlink > 1:
                reason = reason or "hardlinked_content"
            if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
                # Socket descriptors name kernel inodes, not filesystem paths;
                # a cwd/FD-path scan cannot prove such an endpoint unused.
                reason = reason or "special_file"
            if info.st_uid != os.geteuid():
                reason = reason or "foreign_tree_owner"
            if node.name == ".git":
                reason = reason or "git_metadata"
            if info.st_dev != device or str(node) in mounts:
                reason = reason or "mount_point"
                continue
            if stat.S_ISDIR(info.st_mode):
                pending.extend(node.iterdir())
    except OSError:
        return allocated, newest, changed, "tree_unknown"
    return allocated, newest, changed, reason


def protected_roots() -> set[Path]:
    """Exclude managed roots and their ancestors, independently of worker TMPDIR."""
    roots = {resolve_scratch_root(), DEFAULT_SCRATCH_ROOT, fallback_scratch_root()}
    for key in ("LU_RUNTIME_TMP_BASE_ROOT", "TMPDIR"):
        value = os.environ.get(key)
        if value:
            roots.add(Path(value))
    return {path.resolve() for path in roots}


def classify_path(
    path: Path,
    *,
    records: dict[str, dict[str, Any]],
    references: list[tuple[int, Path]],
    process_complete: bool,
    worktrees: set[Path] | None,
    managed: set[Path],
    now: float,
    min_age_s: float,
    scratch: ScratchPolicy | None = None,
    scratch_process_complete: bool = False,
) -> dict[str, Any]:
    """Return a privacy-safe inventory row and the proof used by the apply recheck.

    Without ``scratch`` only directories attributed to a settled task can be
    reaped. With it, regular files are inventoried too, and an entry with no
    task attribution is reaped as ``unattributed_scratch`` when it is old,
    quiet throughout, and unreferenced by every inspectable process.
    """
    row: dict[str, Any] = {"name": path.name, "decision": "preserve", "bytes": None, "task": None, "live_pids": []}
    info = path.lstat()
    row["identity"] = [info.st_dev, info.st_ino, info.st_uid]
    row["kind"] = "file" if stat.S_ISREG(info.st_mode) else "directory" if stat.S_ISDIR(info.st_mode) else "other"
    resolved = path.resolve()
    if path.is_symlink() or not (row["kind"] == "directory" or (scratch and row["kind"] == "file")):
        row["reason"] = "symlink_or_not_directory"
        return row
    if any(resolved == root or resolved in root.parents or root in resolved.parents for root in managed):
        row["reason"] = "managed_scratch"
        return row
    if HARNESS_NAMES.match(path.name):
        row["reason"] = "harness_runtime"
        return row
    if EXCLUDED_NAMES.match(path.name):
        row["reason"] = "excluded_name"
        return row
    row["bytes"], newest, changed, tree_reason = tree_facts(path)
    row["newest_mtime"] = newest
    row["newest_change"] = changed
    row["age_hours"] = round(max(0, now - newest) / 3600, 2)
    matches = task_attribution(path.name, records)
    if matches:
        row["task"] = matches[0]
        row["task_record"] = records[matches[0]]
    row["live_pids"] = sorted({pid for pid, ref in references if ref == resolved or resolved in ref.parents})
    liveness_complete = scratch_process_complete if scratch and not matches else process_complete
    # Conservatively protect ancestors and descendants of registrations.
    if worktrees is None:
        reason = "git_registration_unknown"
    elif any(resolved == w or resolved in w.parents or w in resolved.parents for w in worktrees):
        reason = "registered_worktree"
    elif info.st_uid != os.geteuid():
        reason = "foreign_owner"
    elif tree_reason:
        reason = tree_reason
    elif row["live_pids"]:
        reason = "live_process"
    elif not liveness_complete:
        reason = "liveness_unknown"
    elif not matches and scratch is None:
        reason = "unattributed"
    elif not matches:
        if now - max(info.st_mtime, info.st_ctime) < scratch.min_age_s:
            reason = "too_young"
        elif now - changed < scratch.quiet_s:
            reason = "recent_deep_write"
        else:
            reason = "unattributed_scratch"
            row["decision"] = "would_reap"
    elif records[matches[0]]["status"] not in REAPABLE_STATES:
        reason = "task_not_settled"
    elif now - newest < min_age_s:
        reason = "too_young"
    else:
        try:
            finished = datetime.fromisoformat(str(records[matches[0]]["finished_at"]).replace("Z", "+00:00"))
            if finished.tzinfo is None or not 0 < finished.timestamp() <= now:
                raise ValueError("invalid completion time")
        except ValueError:
            reason = "task_completion_unknown"
        else:
            reason = "dead_attributed_task"
            row["decision"] = "would_reap"
    row["reason"] = reason
    return row


def proof_digest(row: dict[str, Any]) -> str:
    """Bind identity, newest write, allocation and exact task bytes, excluding age."""
    return plan_digest({key: value for key, value in row.items() if key != "age_hours"})


def liveness(scratch_enabled: bool) -> tuple[list[tuple[int, Path]], bool, bool]:
    """Return references, strict completeness and scratch-scope completeness.

    The strict probe is always taken; the tolerant one only when the
    scratch class is enabled and the strict probe could not inspect every
    process.
    """
    references, complete = process_snapshot()
    if not scratch_enabled or complete:
        return references, complete, complete
    tolerant_refs, tolerant_complete = process_snapshot(tolerate_uninspectable=True)
    return references + tolerant_refs, complete, tolerant_complete


def attribution_changed(row: dict[str, Any], records: dict[str, dict[str, Any]]) -> bool:
    """True when the task owning ``row`` (or its absence) no longer holds byte-for-byte."""
    expected = [row["task"]] if row["task"] else []
    if task_attribution(row["name"], records) != expected:
        return True
    return bool(row["task"]) and records.get(row["task"]) != row.get("task_record")


def sweep(
    *,
    temp_root: Path = Path("/tmp"),
    task_root: Path | None = None,
    repo_root: Path = REPO_ROOT,
    min_age_s: float = 12 * 3600,
    scratch: ScratchPolicy | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """Inventory top-level unmanaged entries; recheck every gate before common reap."""
    if not math.isfinite(min_age_s) or min_age_s <= 0:
        raise ValueError("minimum age must be finite and positive")
    if (
        temp_root.is_symlink()
        or not temp_root.is_dir()
        or temp_root.resolve() in {Path("/"), Path.home().resolve(), repo_root.resolve()}
    ):
        raise ValueError("temp root must be a real temporary directory")
    root = temp_root.resolve()
    allowed_areas = {*SYSTEM_TEMP_AREAS, *protected_roots()}
    if not any(root == area.resolve() or area.resolve() in root.parents for area in allowed_areas):
        raise ValueError("temp root is outside system temp and configured scratch areas")
    if scratch is not None and not any(
        root == area.resolve() or area.resolve() in root.parents for area in SYSTEM_TEMP_AREAS
    ):
        raise ValueError("unattributed scratch runs only within the system temp area")
    tasks = task_root if task_root is not None else tasks_dir()
    records = load_tasks(tasks)
    references, complete, scratch_complete = liveness(scratch is not None)
    worktrees = registered_worktrees(repo_root)
    managed = protected_roots()
    rows = []
    errors = 0
    reclaimed = 0
    for path in sorted(root.iterdir()):
        try:
            if not (path.is_symlink() or path.is_dir() or (scratch is not None and path.is_file())):
                continue
            row = classify_path(
                path,
                records=records,
                references=references,
                process_complete=complete,
                worktrees=worktrees,
                managed=managed,
                now=time.time(),
                min_age_s=min_age_s,
                scratch=scratch,
                scratch_process_complete=scratch_complete,
            )
            if apply and row["decision"] == "would_reap":
                fresh_refs, fresh_complete, fresh_scratch_complete = liveness(scratch is not None)
                fresh = classify_path(
                    path,
                    records=load_tasks(tasks),
                    references=fresh_refs,
                    process_complete=fresh_complete,
                    worktrees=registered_worktrees(repo_root),
                    managed=protected_roots(),
                    now=time.time(),
                    min_age_s=min_age_s,
                    scratch=scratch,
                    scratch_process_complete=fresh_scratch_complete,
                )
                if fresh["decision"] != "would_reap" or proof_digest(fresh) != proof_digest(row):
                    row = fresh | {"decision": "preserve", "reason": "proof_changed"}
                else:
                    # The full tree recheck can take time. Probe processes and
                    # task bytes again AFTER it, immediately before the reaper.
                    last_refs, strict_complete, last_scratch_complete = liveness(scratch is not None)
                    last_complete = (
                        last_scratch_complete if row["reason"] == "unattributed_scratch" else strict_complete
                    )
                    last_live = sorted({pid for pid, ref in last_refs if ref == path or path in ref.parents})
                    if last_live or not last_complete or attribution_changed(row, load_tasks(tasks)):
                        row.update(decision="preserve", reason="final_liveness_or_task_changed", live_pids=last_live)
                        rows.append(row)
                        continue
                    reap_attributed_temp(
                        path,
                        repo_root=repo_root,
                        temp_root=root,
                        expected_dev=row["identity"][0],
                        expected_ino=row["identity"][1],
                    )
                    if path.exists() or path.is_symlink():
                        raise OSError("common reaper left residue")
                    row["decision"] = "reaped"
                    reclaimed += row["bytes"]
            rows.append(row)
        except (OSError, ValueError, TaskScratchError):
            errors += 1
            rows.append(
                {
                    "name": path.name,
                    "decision": "preserve",
                    "reason": "scan_or_reap_error",
                    "bytes": 0,
                    "task": None,
                    "live_pids": [],
                }
            )
    free = shutil.disk_usage(root).free
    reclaimable = sum(row["bytes"] for row in rows if row["decision"] == "would_reap")
    report = {
        "schema": "tmp-sweep.v1",
        "mode": "apply" if apply else "dry-run",
        "min_age_hours": min_age_s / 3600,
        "scratch_policy": None
        if scratch is None
        else {"min_age_hours": scratch.min_age_s / 3600, "quiet_hours": scratch.quiet_s / 3600},
        "rows": rows,
        "directories": sum(1 for row in rows if row.get("kind") != "file"),
        "files": sum(1 for row in rows if row.get("kind") == "file"),
        "errors": errors,
        "process_probe_complete": complete,
        "scratch_process_probe_complete": scratch_complete if scratch is not None else None,
        "bytes_reclaimable": reclaimable,
        "bytes_reclaimed": reclaimed,
        "free_bytes": free,
        "projected_free_bytes": free + reclaimable,
    }
    report["digest"] = plan_digest(report)
    return report


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    """Counts and byte totals only: no entry names, safe for logs and public reports."""
    summary = {key: value for key, value in report.items() if key != "rows"}
    summary["by_decision"] = dict(sorted(Counter(row["decision"] for row in report["rows"]).items()))
    summary["by_reason"] = dict(sorted(Counter(row["reason"] for row in report["rows"]).items()))
    summary["bytes_by_reason"] = {
        reason: sum(row["bytes"] or 0 for row in report["rows"] if row["reason"] == reason)
        for reason in summary["by_reason"]
    }
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Attribute and safely reap unmanaged top-level temp entries.\n"
            "Use for legacy task residue and, with --unattributed-scratch, quiet hand-made scratch; "
            "never for managed scratch or harness state."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --json\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --summary\n"
            "  .venv/bin/python -m scripts.hygiene.tmp_sweep --unattributed-scratch --apply --summary\n"
            "Outputs: stdout inventory (or --summary counts) and allocation/headroom totals; "
            "deletion only with --apply.\n"
            "Exit codes: 0 inventory complete; 1 scan/reap errors; 2 invalid arguments.\n"
            "Related: #8755, #9737; docs/runbooks/tmp-retention.md; scripts.hygiene.retention_engine; "
            "packaging/systemd/learn-ukrainian-tmp-sweep.*."
        ),
    )
    parser.add_argument(
        "--temp-root",
        type=Path,
        default=Path("/tmp"),
        help="System temp area to inventory (default /tmp; example /private/tmp).",
    )
    parser.add_argument(
        "--task-root",
        type=Path,
        help="Task-record directory (default shared batch_state/tasks; example fixture/tasks).",
    )
    parser.add_argument(
        "--min-age-hours",
        type=float,
        default=12,
        help="Task-attributed class: minimum latest-write age (positive hours; default 12; example 24).",
    )
    parser.add_argument(
        "--unattributed-scratch",
        action="store_true",
        help=(
            "Also reap agent-owned top-level files and directories with no task owner once they pass "
            "the scratch age, quiet and liveness gates (default off; #9737)."
        ),
    )
    parser.add_argument(
        "--scratch-age-hours",
        type=float,
        default=24,
        help="Scratch class: minimum age of the top-level entry itself (positive hours; default 24; example 48).",
    )
    parser.add_argument(
        "--scratch-quiet-hours",
        type=float,
        default=24,
        help="Scratch class: no write or change anywhere inside for this long (positive hours; default 24).",
    )
    parser.add_argument(
        "--apply", action="store_true", help="Recheck proofs and call the common reaper (default dry-run)."
    )
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--json", action="store_true", help="Print machine-readable inventory (default Markdown table)."
    )
    output.add_argument(
        "--summary",
        action="store_true",
        help="Print JSON counts and byte totals only, without entry names (default off).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        scratch = (
            ScratchPolicy(min_age_s=args.scratch_age_hours * 3600, quiet_s=args.scratch_quiet_hours * 3600)
            if args.unattributed_scratch
            else None
        )
        report = sweep(
            temp_root=args.temp_root,
            task_root=args.task_root,
            min_age_s=args.min_age_hours * 3600,
            scratch=scratch,
            apply=args.apply,
        )
    except (ValueError, OSError):
        parser.error("invalid or unreadable temporary/task area; no deletion authorized")
    if args.json:
        print(json.dumps(report, sort_keys=True, indent=2))
    elif args.summary:
        print(json.dumps(summarize(report), sort_keys=True, indent=2))
    else:
        print("| Entry | Allocated bytes | Task / live PID attribution | Decision | Reason |")
        print("|---|---:|---|---|---|")
        for row in report["rows"]:
            name = json.dumps(row["name"], ensure_ascii=True).replace("|", "\\|")
            owner = row["task"] or ("live process" if row["live_pids"] else "unknown")
            print(f"| {name} | {row['bytes']} | {owner} | {row['decision']} | {row['reason']} |")
        print(
            f"mode={report['mode']} directories={report['directories']} files={report['files']} errors={report['errors']}"
        )
        print(
            f"bytes_reclaimable={report['bytes_reclaimable']} bytes_reclaimed={report['bytes_reclaimed']} free_bytes={report['free_bytes']} projected_free_bytes={report['projected_free_bytes']}"
        )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
