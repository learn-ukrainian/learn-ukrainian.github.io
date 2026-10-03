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
from pathlib import Path
from typing import Any

from scripts.orchestration import worktree_artifacts as artifacts
from scripts.orchestration.task_record_store import archived_task_record_path, task_record_path

# Bound automatic disk duplication. Larger outputs require owner disposition;
# the complete source checkout survives rather than receiving a partial copy.
MAX_PRESERVED_BYTES = 256 * 1024 * 1024


def _ignored_output_files(worktree: Path, primary: Path, record: Mapping[str, Any]) -> list[str]:
    """Inventory output, including unignored files when no index was checked out."""
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
    return sorted(name for name in files if not artifacts._is_disposable_path(Path(name)))


def _record_matches_worktree(record: Mapping[str, Any], worktree: Path) -> bool:
    """Task names are hints; only resolved filesystem identity binds a record."""
    location = record.get("worktree_path") or record.get("cwd")
    if not isinstance(location, str) or not location:
        return False
    try:
        return Path(location).resolve(strict=True) == worktree.resolve(strict=True)
    except (OSError, ValueError, RuntimeError):
        return False


def _update_bound_task_record(
    path: Path, worktree: Path, updates: Mapping[str, Any], *, clear: tuple[str, ...] = ()
) -> bool:
    """Recheck binding under the writer lock, including re-dispatch during copying."""
    with artifacts.task_state_lock(path):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return False
        if not isinstance(record, dict):
            raise ValueError("task record is not an object")
        if not _record_matches_worktree(record, worktree):
            return False
        record.update(updates)
        for key in clear:
            record.pop(key, None)
        artifacts.reaper_lifecycle._atomic_write(path, record)
        return True


def _content_digest(root: Path, files: list[str]) -> str:
    """Hash the ordered file names, sizes and bytes, refusing linked copy paths."""
    entries = []
    for name in files:
        source = root / name
        if source.resolve(strict=True) != source.absolute() or not stat.S_ISREG(source.lstat().st_mode):
            raise ValueError("preserved artifact is not a local regular file")
        entries.append((name, *artifacts._fingerprint(source)))
    return hashlib.sha256(json.dumps(entries, ensure_ascii=True).encode()).hexdigest()


def _reusable_copy(parent: Path, worktree: Path, files: list[str], digest: str) -> Path | None:
    """A manifest is a locator; verify the complete copy's names and bytes again."""
    for manifest in sorted(parent.glob("*.manifest.json")):
        try:
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            if not isinstance(saved, dict) or saved.get("worktree_path") != str(worktree):
                continue
            if saved.get("content_sha256") != digest:
                continue
            location = manifest.with_name(manifest.name.removesuffix(".manifest.json"))
            if location.resolve(strict=True) != location.absolute():
                continue
            entries = list(location.rglob("*"))
            if any(entry.is_symlink() for entry in entries):
                continue
            names = sorted(entry.relative_to(location).as_posix() for entry in entries if not entry.is_dir())
            if names == files and _content_digest(location, files) == digest:
                return location
        except (OSError, ValueError, RuntimeError):
            continue  # Invalid or incomplete attempts never license removal.
    return None


def preserve_worktree_artifacts(
    worktree: Path,
    *,
    primary: Path,
    task_id: str | None,
    tasks_dir: Path,
    task_record: Mapping[str, Any] | None = None,
) -> tuple[bool, str, dict[str, Any] | None]:
    """Copy all ignored output before removal, independent of terminal status.

    Call under the remover's existing ownership/liveness lock. Task start values
    never affect selection: earlier attempts' output must survive too. An absent task
    identity is derived from the dispatch path, or uses a worktree path digest. Each
    changed output has its own destination; identical verified copies are reused.
    Inventory, cap, copy, verification and record errors retain the
    checkout. Existing preservation layout and verified-copy mechanics are reused.
    """
    if task_id is None:
        from scripts.orchestration.reap_worktrees import _dispatch_task_id_for_path

        task_id = _dispatch_task_id_for_path(primary, worktree)
    record_path = None
    record = {}
    metadata = None
    try:
        worktree = worktree.resolve(strict=True)
        primary = primary.resolve(strict=True)
        if task_id:
            for candidate in (task_record_path(tasks_dir, task_id), archived_task_record_path(tasks_dir, task_id)):
                if not candidate.exists():
                    continue
                stored = json.loads(candidate.read_text(encoding="utf-8"))
                if not isinstance(stored, dict):
                    raise ValueError("task record is not an object")
                if _record_matches_worktree(stored, worktree):
                    record_path, record = candidate, stored
                    break
        if not record and task_record and _record_matches_worktree(task_record, worktree):
            record = dict(task_record)
        files = _ignored_output_files(worktree, primary, record)
        if not files:
            return True, "", None
        identity = task_id or "worktree-" + hashlib.sha256(str(worktree.resolve()).encode()).hexdigest()[:24]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", identity):
            raise ValueError("artifact preservation requires a safe task identity")
        total_bytes = sum((worktree / name).stat().st_size for name in files)
        if total_bytes > MAX_PRESERVED_BYTES:
            raise ValueError(f"ignored output exceeds preservation cap ({total_bytes} > {MAX_PRESERVED_BYTES} bytes)")
        parent = primary / "batch_state" / "preserved" / identity
        if parent.is_relative_to(worktree):
            raise ValueError("preservation destination is inside the worktree")
        digest = _content_digest(worktree, files)
        location = _reusable_copy(parent, worktree, files, digest)
        reused = location is not None
        if location is None:
            location = parent / uuid.uuid4().hex
            for name in files:
                destination = location / name
                if destination.resolve() != destination.absolute():
                    raise ValueError("preserved artifact destination contains a symlink")
                artifacts._copy_verified(worktree / name, destination)
        # Recheck the complete inventory and all bytes after the last copy.
        if (
            files != _ignored_output_files(worktree, primary, record)
            or sum((location / name).stat().st_size for name in files) != total_bytes
            or _content_digest(worktree, files) != digest
            or _content_digest(location, files) != digest
        ):
            raise ValueError("ignored output changed during preservation")
        metadata = {
            "count": len(files),
            "bytes": total_bytes,
            "location": str(location),
            "worktree_path": str(worktree),
            "content_sha256": digest,
            "reused": reused,
        }
        if not reused:
            with location.with_suffix(".manifest.json").open("x", encoding="utf-8") as manifest:
                json.dump(metadata, manifest, sort_keys=True)
                manifest.write("\n")
        if record_path is None or not _update_bound_task_record(
            record_path, worktree, {"preserved_artifacts": metadata}, clear=("artifact_preservation_error",)
        ):
            metadata["record_update"] = "skipped_missing_record"
            receipt_path = location.with_name(location.name + ("-" + uuid.uuid4().hex if reused else "") + ".receipt.json")
            metadata["receipt_path"] = str(receipt_path)
            with receipt_path.open("x", encoding="utf-8") as receipt_file:
                json.dump(metadata, receipt_file, sort_keys=True)
                receipt_file.write("\n")
            print(f"Preserved {len(files)} files ({total_bytes} bytes) at {location}; receipt: {receipt_path}", file=sys.stderr)
        else:
            print(f"Preserved {len(files)} files ({total_bytes} bytes) at {location}", file=sys.stderr)
        if isinstance(task_record, dict) and _record_matches_worktree(task_record, worktree):
            task_record["preserved_artifacts"] = metadata
            task_record.pop("artifact_preservation_error", None)
        return True, "", metadata
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        reason = f"artifact preservation failed: {exc}; refusing worktree removal"
        if isinstance(task_record, dict) and _record_matches_worktree(task_record, worktree):
            task_record["artifact_preservation_error"] = reason
        if record_path is not None:
            with contextlib.suppress(OSError, ValueError):
                _update_bound_task_record(record_path, worktree, {"artifact_preservation_error": reason})
        return False, reason, metadata
