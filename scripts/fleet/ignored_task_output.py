"""Preserve ignored task output before automatic worktree removal (#9645)."""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import stat
import subprocess
import sys
import uuid
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration.task_record_store import task_record_path

# Bound automatic disk duplication. Larger outputs require owner disposition;
# the complete source checkout survives rather than receiving a partial copy.
MAX_PRESERVED_BYTES = 256 * 1024 * 1024


def _ignored_output_files(worktree: Path, primary: Path, record: Mapping[str, Any]) -> list[str]:
    """Inventory output, including unignored files when no index was checked out."""
    started_at = record.get("started_at")
    cutoff = None
    if started_at is not None:
        started = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        if started.tzinfo is None:
            raise ValueError("task start must include a timezone")
        cutoff = started.timestamp()

    # Retain the existing named-link safety checks and nested-repository gates.
    named = artifacts._named_artifact_files(worktree, record, primary=primary)
    names = artifacts._git_paths(worktree, "--others", "--ignored", "--exclude-standard")
    if not artifacts._git_paths(worktree, "--cached"):
        # --no-checkout leaves an empty index and no on-disk .gitignore.
        # Unignored scratch can be task output too; inventory both classes.
        names += artifacts._git_paths(worktree, "--others", "--exclude-standard")
    files: set[str] = set()
    root = worktree.resolve(strict=True)
    for name in names:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("ignored output inventory escaped worktree")
        if artifacts._is_disposable_path(relative):
            continue
        source = worktree / relative
        status = source.lstat()
        if stat.S_ISLNK(status.st_mode):
            resolved = source.resolve(strict=True)
            if resolved.is_relative_to(primary / "batch_state") and not resolved.is_relative_to(root):
                continue  # Shared state survives removal of the link.
            if name in {"data/sources.db", "data/vesum.db"} and resolved == (primary / name).resolve(strict=True):
                continue  # Dispatcher-provisioned database link; never read it.
            if resolved.is_relative_to(root):
                continue  # Local target is inventoried independently or tracked.
            raise ValueError("ignored output links outside the checkout")
        if source.resolve(strict=True) != source.absolute():
            raise ValueError("ignored output is not a local regular file")
        if stat.S_ISDIR(status.st_mode):
            files.update(artifacts._inspect_directory_artifact(source, name, worktree=worktree))
        elif stat.S_ISREG(status.st_mode):
            files.add(name)
        else:
            raise ValueError("ignored output is not a regular file")
    files.update(named)
    return sorted(
        name
        for name in files
        if not artifacts._is_disposable_path(Path(name))
        and (cutoff is None or max((worktree / name).stat().st_mtime, (worktree / name).stat().st_ctime) >= cutoff)
    )


def preserve_worktree_artifacts(
    worktree: Path,
    *,
    primary: Path,
    task_id: str | None,
    tasks_dir: Path,
    task_record: Mapping[str, Any] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Copy all ignored output before removal, independent of terminal status.

    Call under the remover's existing ownership/liveness lock. Missing task
    start conservatively includes all non-cache ignored files. An absent task
    identity is derived from the dispatch path, or uses a worktree path digest. Each
    preservation has its own destination, keeping earlier attempts intact.
    Inventory, cap, copy, verification and record errors retain the
    checkout. Existing preservation layout and verified-copy mechanics are reused.
    """
    if task_id is None:
        from scripts.orchestration.reap_worktrees import _dispatch_task_id_for_path

        task_id = _dispatch_task_id_for_path(primary, worktree)
    record_path = task_record_path(tasks_dir, task_id) if task_id else None
    record = dict(task_record or {})
    metadata = None
    try:
        if record_path is not None and record_path.exists():
            stored = json.loads(record_path.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                raise ValueError("task record is not an object")
            record.update(stored)
        primary = primary.resolve(strict=True)
        files = _ignored_output_files(worktree, primary, record)
        if not files:
            return True, "", None
        identity = task_id or "worktree-" + hashlib.sha256(str(worktree.resolve()).encode()).hexdigest()[:24]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity):
            raise ValueError("artifact preservation requires a safe task identity")
        total_bytes = sum((worktree / name).stat().st_size for name in files)
        if total_bytes > MAX_PRESERVED_BYTES:
            raise ValueError(f"ignored output exceeds preservation cap ({total_bytes} > {MAX_PRESERVED_BYTES} bytes)")
        location = primary / "batch_state" / "preserved" / identity / uuid.uuid4().hex
        if location.is_relative_to(worktree.resolve()):
            raise ValueError("preservation destination is inside the worktree")
        for name in files:
            destination = location / name
            if destination.resolve() != destination.absolute():
                raise ValueError("preserved artifact destination contains a symlink")
            artifacts._copy_verified(worktree / name, destination)
        # Recheck the complete inventory and all bytes after the last copy.
        if (
            files != _ignored_output_files(worktree, primary, record)
            or sum((location / name).stat().st_size for name in files) != total_bytes
            or any(artifacts._fingerprint(worktree / name) != artifacts._fingerprint(location / name) for name in files)
        ):
            raise ValueError("ignored output changed during preservation")
        metadata = {"count": len(files), "bytes": total_bytes, "location": str(location)}
        if record_path is None or not artifacts._update_existing_task_record(
            record_path, {"preserved_artifacts": metadata}, clear=("artifact_preservation_error",)
        ):
            metadata["record_update"] = "skipped_missing_record"
            receipt_path = location.with_suffix(".receipt.json")
            metadata["receipt_path"] = str(receipt_path)
            with receipt_path.open("x", encoding="utf-8") as receipt_file:
                json.dump(metadata, receipt_file, sort_keys=True)
                receipt_file.write("\n")
            print(f"Preserved {len(files)} files ({total_bytes} bytes) at {location}; receipt: {receipt_path}", file=sys.stderr)
        else:
            print(f"Preserved {len(files)} files ({total_bytes} bytes) at {location}", file=sys.stderr)
        if isinstance(task_record, dict):
            task_record["preserved_artifacts"] = metadata
            task_record.pop("artifact_preservation_error", None)
        return True, "", metadata
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        reason = f"artifact preservation failed: {exc}; refusing worktree removal"
        if isinstance(task_record, dict):
            task_record["artifact_preservation_error"] = reason
        if record_path is not None:
            with contextlib.suppress(OSError, ValueError):
                artifacts._update_existing_task_record(record_path, {"artifact_preservation_error": reason})
        return False, reason, metadata
