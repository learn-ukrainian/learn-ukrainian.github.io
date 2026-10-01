"""Copy ignored worker evidence before removal; failures retain the checkout (#9449)."""

from __future__ import annotations

import contextlib
import errno
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
from scripts.orchestration.dead_worker_state import task_state_lock
from scripts.orchestration.task_record_store import task_record_path

_DISPOSABLE_DIRECTORIES = frozenset(
    {".pytest_cache", ".ruff_cache", ".mypy_cache", "__pycache__", "node_modules", ".venv", ".git"}
)


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


_RESOLVER_ERRORS = {errno.ELOOP: "symlink loop", errno.ENAMETOOLONG: "name too long"}


def _resolve_named(root: Path, parts: tuple[str, ...]) -> tuple[Path, os.stat_result] | None:
    """Resolve a name as the filesystem does; ``None`` when nothing exists there.

    No lexical normalization: ``..`` after a symlinked directory applies to the
    link's target. Any other resolver failure refuses removal, naming only the
    failure class, never the path text.
    """
    try:
        resolved = Path(os.path.realpath(root.joinpath(*parts)))
        return resolved, resolved.stat()
    except (FileNotFoundError, NotADirectoryError):
        return None
    except RuntimeError:
        kind = _RESOLVER_ERRORS[errno.ELOOP]
    except ValueError:
        kind = "embedded NUL"
    except OSError as exc:
        kind = _RESOLVER_ERRORS.get(exc.errno) or errno.errorcode.get(exc.errno or 0, type(exc).__name__)
    raise ValueError(f"a named artifact path cannot be resolved ({kind})")


def _leaves_through_link(root: Path, parts: tuple[str, ...]) -> bool:
    """Whether resolving ``parts`` leaves the checkout through a link inside it.

    Climbing out of the root with ``..`` is not a checkout name; removal
    cannot take what such a name reaches.
    """
    current = root
    for part in parts:
        inside = current.is_relative_to(root)
        current = current.parent if part == ".." else Path(os.path.realpath(current / part))
        if part != ".." and inside and not current.is_relative_to(root):
            return True
    return False


def _named_artifact_files(worktree: Path, record: Mapping[str, Any], *, primary: Path) -> set[str]:
    """Inventory only explicitly named, non-empty ignored files outside caches.

    Tracked files survive in Git; directories are not evidence inventories.
    A name stands for the file the filesystem resolves it to: a target inside
    the checkout is inventoried under its resolved path, because removal
    destroys it; a target file reached through a link out of the checkout
    cannot be preserved here and refuses removal, unless it already lives
    under the primary's batch_state. Backticks/quotes and Markdown links
    support spaced paths.
    """
    root = worktree.resolve()
    shared_state = primary / "batch_state"
    files: set[str] = set()
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
        if path.is_absolute():
            base = next((base for base in (worktree, root) if path.is_relative_to(base)), None)
            if base is None:
                continue
            path = path.relative_to(base)
        parts = path.parts
        if _DISPOSABLE_DIRECTORIES.intersection(parts):
            continue
        found = _resolve_named(root, parts)
        if found is None:
            continue
        resolved, status = found
        if not stat.S_ISREG(status.st_mode) or not status.st_size:
            continue
        if not resolved.is_relative_to(root):
            # Never copied: following an outbound link would read outside the checkout.
            if not resolved.is_relative_to(shared_state) and _leaves_through_link(root, parts):
                raise ValueError(f"named artifact {path.as_posix()} links outside the checkout and cannot be preserved")
            continue
        relative = resolved.relative_to(root)
        if _DISPOSABLE_DIRECTORIES.intersection(relative.parts):
            continue
        name = relative.as_posix()
        ignored = _git_paths(worktree, "--others", "--ignored", "--exclude-standard", "--", name)
        if name in ignored:
            files.add(name)
    return files


def _update_existing_task_record(path: Path, updates: Mapping[str, Any], *, clear: tuple[str, ...] = ()) -> bool:
    """Merge only the guard's fields into fresh state under the shared writer lock.

    Returns ``False``, without creating a record, when none exists.
    """
    with task_state_lock(path):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return False
        if not isinstance(record, dict):
            raise ValueError("task record is not an object")
        record.update(updates)
        for key in clear:
            record.pop(key, None)
        reaper_lifecycle._atomic_write(path, record)
        return True


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
    Records the location in existing task records before allowing removal.
    Reports a missing record without creating one. Missing identity, unreadable
    inventory, unsafe paths, copy/verification/record failures all fail closed.
    Empty directories and __pycache__ require no preservation.
    """
    record_path = task_record_path(tasks_dir, task_id) if task_id else None
    record: dict[str, Any] = dict(task_record or {})
    metadata = None
    detail = ""
    try:
        if record_path is not None and record_path.exists():
            stored = json.loads(record_path.read_text(encoding="utf-8"))
            if not isinstance(stored, dict):
                raise ValueError("task record is not an object")
            record.update(stored)
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
        for name in sorted(_named_artifact_files(worktree, record, primary=primary) - set(files)):
            source = worktree / name
            if source.resolve() != source.absolute() or not stat.S_ISREG(source.lstat().st_mode):
                raise ValueError(f"artifact is not a local regular file: {name}")
            files.append(name)
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
            if not _update_existing_task_record(
                record_path, {"preserved_artifacts": metadata}, clear=("artifact_preservation_error",)
            ):
                metadata["record_update"] = "skipped_missing_record"
                detail = "task record missing; preserved files without record update"
            if isinstance(task_record, dict):
                task_record["preserved_artifacts"] = metadata
                task_record.pop("artifact_preservation_error", None)
        return True, detail, metadata
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        reason = f"artifact preservation failed: {exc}; refusing worktree removal"
        if isinstance(task_record, dict):
            task_record["artifact_preservation_error"] = reason
        if record_path is not None:
            # The caller also records the refusal in its removal receipt.
            with contextlib.suppress(OSError, ValueError):
                _update_existing_task_record(record_path, {"artifact_preservation_error": reason})
        return False, reason, metadata
