"""Copy ignored worker evidence before removal; failures retain the checkout (#9449)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from scripts.orchestration import reaper_lifecycle
from scripts.orchestration.task_record_store import task_record_path


def _git_paths(worktree: Path, *args: str) -> list[str]:
    """Read NUL-delimited paths, refusing an unavailable inventory."""
    result = subprocess.run(
        ["git", "ls-files", "-z", *args],
        cwd=worktree,
        env={key: value for key, value in os.environ.items() if not key.startswith("GIT_")},
        capture_output=True,
        check=True,
        timeout=30,
    )
    return [os.fsdecode(path) for path in result.stdout.split(b"\0") if path]


def _fingerprint(path: Path) -> tuple[int, str]:
    """Verify copied bytes independently of the copy operation."""
    with path.open("rb") as handle:
        return os.fstat(handle.fileno()).st_size, hashlib.file_digest(handle, "sha256").hexdigest()


def _copy_verified(source: Path, destination: Path) -> None:
    """Copy atomically, verifying size and SHA-256 and refusing conflicting evidence."""
    before = _fingerprint(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.is_symlink() or _fingerprint(destination) != before:
            raise ValueError("preserved artifact already exists with different bytes")
        return
    fd, temporary_name = tempfile.mkstemp(prefix=".preserve-", dir=destination.parent)
    temporary = Path(temporary_name)
    try:
        os.close(fd)
        shutil.copyfile(source, temporary)
        if _fingerprint(temporary) != before or _fingerprint(source) != before:
            raise ValueError("artifact size or SHA-256 changed during preservation")
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        # Another checkout of this task may preserve concurrently. Never replace
        # evidence it published after our initial existence check.
        os.link(temporary, destination)
        if _fingerprint(destination) != before:
            raise ValueError("preserved artifact size or SHA-256 mismatch")
    finally:
        temporary.unlink(missing_ok=True)


def _named_artifact_refusal(worktree: Path, record: Mapping[str, Any], preserved: set[str]) -> str | None:
    """Retain named local evidence outside the supported ignored batch_state inventory.

    Tracked paths survive in Git and primary-checkout result sidecars are outside
    the removal target. Backticks/quotes and Markdown links support spaced paths.
    """
    text = str(record.get("response") or "")
    result_file = record.get("result_file")
    if result_file:
        result_path = Path(str(result_file))
        if not result_path.is_absolute():
            result_path = worktree / result_path
        if result_path.is_file():
            text += "\n" + result_path.read_text(encoding="utf-8")
    candidates = re.findall(r"[`\"']([^`\"'\n]+)[`\"']|\[[^\]\n]*\]\(([^)]+)\)|([^\s`\"'<>(),;]+)", text)
    for match in candidates:
        candidate = next(part for part in match if part).rstrip(".:!?")
        candidate = re.sub(r":\d+(?::\d+)?$", "", candidate)
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = worktree / path
        path = Path(os.path.normpath(path))
        try:
            relative = path.relative_to(worktree)
        except ValueError:
            continue
        if ".." in relative.parts or not path.exists():
            continue
        # Inventory only the named path; never sweep unrelated ignored caches.
        names = set(_git_paths(worktree, "--others", "--exclude-standard", "--", relative.as_posix()))
        names.update(_git_paths(worktree, "--others", "--ignored", "--exclude-standard", "--", relative.as_posix()))
        for name in sorted(names - preserved):
            artifact = worktree / name
            if "__pycache__" not in Path(name).parts and artifact.stat().st_size:
                return f"result names unpreserved artifact {name}; refusing worktree removal"
    return None


def preserve_worktree_artifacts(
    worktree: Path,
    *,
    primary: Path,
    task_id: str | None,
    tasks_dir: Path,
    task_record: Mapping[str, Any] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Shared removal guard, called under the existing worktree lock.

    Copies (never moves) non-empty ignored batch_state files, retaining their
    worktree-relative paths under primary/batch_state/preserved/<task-id>.
    Records the location before allowing removal. Missing identity, unreadable
    inventory, unsafe paths, copy/verification/record failures all fail closed.
    Empty directories and __pycache__ require no preservation.
    """
    record_path = task_record_path(tasks_dir, task_id) if task_id else None
    record: dict[str, Any] = dict(task_record or {})
    record_readable = False
    metadata = None
    try:
        if record_path is not None and record_path.exists():
            stored = json.loads(record_path.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                raise ValueError("task record is not an object")
            record.update(stored)
        record_readable = True
        if task_id:
            record.setdefault("task_id", task_id)
        primary = primary.resolve()
        batch_root = worktree / "batch_state"
        if batch_root.is_symlink():
            target = batch_root.resolve()
            if not target.is_relative_to(primary) or target.is_relative_to(worktree.resolve()):
                raise ValueError("batch_state is a symlink to unpreserved local artifacts")
        names = _git_paths(worktree, "--others", "--ignored", "--exclude-standard", "--", "batch_state/")
        files: list[str] = []
        for name in names:
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "batch_state":
                raise ValueError("artifact inventory escaped batch_state")
            if "__pycache__" in relative.parts:
                continue
            source = worktree / relative
            resolved = source.resolve()
            # Shared primary task records/sidecars are not destroyed with the link.
            if resolved.is_relative_to(tasks_dir.resolve()) and resolved.is_relative_to(primary):
                continue
            if resolved != source.absolute() or not stat.S_ISREG(source.lstat().st_mode):
                raise ValueError(f"artifact is not a local regular file: {name}")
            if source.stat().st_size:
                files.append(name)
        refusal = _named_artifact_refusal(worktree, record, set(files))
        if refusal:
            raise ValueError(refusal)
        if files:
            if not task_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", task_id):
                raise ValueError("artifact preservation requires a safe task identity")
            location = primary / "batch_state" / "preserved" / task_id
            for name in files:
                destination = location / name
                if destination.resolve() != destination.absolute():
                    raise ValueError("preserved artifact destination contains a symlink")
                _copy_verified(worktree / name, destination)
            metadata = {"count": len(files), "location": str(location)}
            record["preserved_artifacts"] = metadata
            record.pop("artifact_preservation_error", None)
            reaper_lifecycle._atomic_write(record_path, record)
            if isinstance(task_record, dict):
                task_record.update({"preserved_artifacts": metadata})
                task_record.pop("artifact_preservation_error", None)
        return True, "", metadata
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        reason = f"artifact preservation failed: {exc}; refusing worktree removal"
        if isinstance(task_record, dict):
            task_record["artifact_preservation_error"] = reason
        if record_path is not None and record_readable:
            try:
                record["artifact_preservation_error"] = reason
                reaper_lifecycle._atomic_write(record_path, record)
            except (OSError, ValueError):
                pass  # The caller also records the refusal in its removal receipt.
        return False, reason, metadata
