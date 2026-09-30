"""Move verified legacy Codex skills into retained storage outside discovery.

Capture uses an exclusive atomic rename with descriptor-bound parents. No file
or backup is deleted: writers holding an old file descriptor continue writing
the retained inode. Inventory drift fails closed with both captured and newly
created active content preserved for reconciliation.
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import hashlib
import os
import stat
import subprocess
import sys
import uuid
from importlib.util import source_from_cache
from pathlib import Path

BACKUP_DIRECTORY = "retired-skills"
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_SKILLS_PREFIX = "agents_extensions/shared/skills"


class _SkillIndex:
    """One ``git ls-files`` of the skills tree, shared by every file in an inventory."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self._stages: dict[bytes, list[tuple[bytes, bytes]]] | None = None

    def stages(self, git_path: str) -> list[tuple[bytes, bytes]]:
        """Index stages for ``git_path``: ``(mode, stage)`` per entry, in git's order."""
        if self._stages is None:
            tracked = subprocess.run(
                ["git", "ls-files", "--stage", "-z", "--", _SKILLS_PREFIX],
                cwd=self.root, capture_output=True, check=False, timeout=30,
            )
            found: dict[bytes, list[tuple[bytes, bytes]]] = {}
            if tracked.returncode == 0:
                for entry in tracked.stdout.split(b"\0"):
                    if not entry or b"\t" not in entry:
                        continue
                    metadata, path = entry.split(b"\t", 1)
                    mode, _, stage = metadata.split()
                    found.setdefault(path, []).append((mode, stage))
            self._stages = found
        return self._stages.get(os.fsencode(git_path), [])


def cache_source_is_tracked(root: Path, relative: str, index: _SkillIndex | None = None) -> bool:
    """Classify retained runtime bytes by cache path, without loading bytecode."""
    cache = Path(relative)
    fields = cache.name.split(".")
    # source_from_cache also accepts wrong suffixes and empty cache tags.
    if cache.parent.name != "__pycache__" or len(fields) not in (3, 4):
        return False
    if fields[-1] != "pyc" or not fields[0] or not fields[1]:
        return False
    try:
        source_relative = Path(source_from_cache(relative))
    except (ValueError, NotImplementedError):
        return False
    source_root = root / _SKILLS_PREFIX
    source = source_root / source_relative
    if not source.is_file() or source.is_symlink():
        return False
    for parent in source.parents:
        if parent.is_symlink():
            return False
        if parent == root:
            break
    git_path = source.relative_to(root).as_posix()
    stages = (index or _SkillIndex(root)).stages(git_path)
    # One clean stage only: a conflict or a missing path is not a tracked source.
    if len(stages) != 1:
        return False
    mode, stage = stages[0]
    return mode in (b"100644", b"100755") and stage == b"0"


def source_matches(root: Path, relative: str, payload: bytes, index: _SkillIndex | None = None) -> bool:
    """Require tracked current bytes or a regular-file blob at this exact path."""
    source_path = f"{_SKILLS_PREFIX}/{relative}"
    source = root / source_path
    tracked = bool((index or _SkillIndex(root)).stages(source_path))
    if tracked and source.is_file() and not source.is_symlink() and payload == source.read_bytes():
        return True
    digest = subprocess.run(
        ["git", "hash-object", "--stdin"], input=payload,
        cwd=root, capture_output=True, check=False, timeout=30,
    )
    history = subprocess.run(
        ["git", "log", "--format=", "--raw", "--no-abbrev", "--", source_path],
        cwd=root, capture_output=True, check=False, timeout=30,
    )
    if digest.returncode != 0 or history.returncode != 0:
        return False
    blob = digest.stdout.strip()
    for line in history.stdout.splitlines():
        fields = line.split(b"\t", 1)[0].split()
        if len(fields) != 5 or not fields[0].startswith(b":"):
            continue
        old_mode, new_mode, old_blob, new_blob, _ = fields
        if (old_mode[1:] in (b"100644", b"100755") and old_blob == blob) or (
            new_mode in (b"100644", b"100755") and new_blob == blob
        ):
            return True
    return False


def signature(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def inventory(root: Path, tree_fd: int, prefix: str = "", index: _SkillIndex | None = None) -> dict[str, tuple]:
    """Read a complete inventory without following links at any component."""
    result: dict[str, tuple] = {}
    for name in sorted(os.listdir(tree_fd)):
        relative = f"{prefix}/{name}" if prefix else name
        info = os.stat(name, dir_fd=tree_fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            source = root / "agents_extensions/shared/skills" / relative
            if "__pycache__" in Path(prefix).parts:
                raise ValueError("Nested legacy cache directory; preserve and reconcile")
            # Python creates this runtime directory only where a script runs;
            # its canonical-source counterpart need not exist on this host.
            if name != "__pycache__" and (not source.is_dir() or source.is_symlink()):
                raise ValueError("Unknown legacy Codex skill directory; preserve and reconcile")
            child_fd = os.open(name, DIRECTORY_FLAGS, dir_fd=tree_fd)
            try:
                if signature(os.fstat(child_fd)) != signature(info):
                    raise ValueError("Legacy directory changed during inventory; preserve and reconcile")
                result[relative] = signature(info)
                result.update(inventory(root, child_fd, relative, index))
            finally:
                os.close(child_fd)
        elif stat.S_ISREG(info.st_mode):
            file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=tree_fd)
            with os.fdopen(file_fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or signature(before) != signature(info):
                    raise ValueError("Legacy file changed during inventory; preserve and reconcile")
                payload = stream.read()
                if signature(os.fstat(stream.fileno())) != signature(before):
                    raise ValueError("Legacy file changed during inventory; preserve and reconcile")
            is_cache = Path(prefix).name == "__pycache__"
            accepted = (
                cache_source_is_tracked(root, relative, index)
                if is_cache
                else source_matches(root, relative, payload, index)
            )
            if not accepted:
                raise ValueError(f"Unverified legacy Codex skill content: {relative}; preserve and reconcile")
            result[relative] = (*signature(before), hashlib.sha256(payload).hexdigest())
        else:
            raise ValueError("Legacy Codex skills contain symlink or unsupported content; preserve and reconcile")
    return result


def rename_exclusive(source_fd: int, source: str, target_fd: int, target: str) -> None:
    """Atomic no-replace rename on supported deployment hosts; no unsafe fallback."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        flags = 0x00000004  # RENAME_EXCL, sys/stdio.h
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        flags = 1  # RENAME_NOREPLACE
    else:
        raise ValueError("Exclusive atomic rename unavailable; preserve and reconcile")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(source_fd, os.fsencode(source), target_fd, os.fsencode(target), flags) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def directory_still_bound(parent_fd: int, name: str, directory_fd: int) -> bool:
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    opened = os.fstat(directory_fd)
    return stat.S_ISDIR(current.st_mode) and (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino)


def active_exists(codex_fd: int) -> bool:
    try:
        os.stat("skills", dir_fd=codex_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def migrate(root: Path, mode: str) -> int:
    captured = ""
    try:
        with contextlib.ExitStack() as stack:
            def open_directory(name: str | Path, parent_fd: int | None = None) -> int:
                fd = os.open(name, DIRECTORY_FLAGS, dir_fd=parent_fd)
                stack.callback(os.close, fd)
                return fd

            root_fd = open_directory(root)
            try:
                codex_fd = open_directory(".codex", root_fd)
            except FileNotFoundError:
                return 0
            try:
                source_fd = open_directory("skills", codex_fd)
            except FileNotFoundError:
                return 0
            index = _SkillIndex(root)
            before = inventory(root, source_fd, index=index)
            if mode == "verify":
                return 0
            if not directory_still_bound(root_fd, ".codex", codex_fd) or not directory_still_bound(codex_fd, "skills", source_fd):
                raise ValueError("Legacy discovery binding changed; preserve and reconcile")
            with contextlib.suppress(FileExistsError):
                os.mkdir(BACKUP_DIRECTORY, mode=0o700, dir_fd=codex_fd)
            backup_fd = open_directory(BACKUP_DIRECTORY, codex_fd)
            capture_name = uuid.uuid4().hex
            # mkdir is exclusive. A collision or interrupted prior operation is
            # preserved, never overwritten or reused.
            os.mkdir(capture_name, mode=0o700, dir_fd=backup_fd)
            capture_fd = open_directory(capture_name, backup_fd)
            capture_path = f".codex/{BACKUP_DIRECTORY}/{capture_name}/skills"
            rename_exclusive(codex_fd, "skills", capture_fd, "skills")
            captured = capture_path
            captured_fd = open_directory("skills", capture_fd)
            captured_info, source_info = os.fstat(captured_fd), os.fstat(source_fd)
            if (captured_info.st_dev, captured_info.st_ino) != (source_info.st_dev, source_info.st_ino):
                raise ValueError("Legacy discovery tree replaced during capture; preserve and reconcile")
            after = inventory(root, captured_fd, index=index)
            if before != after:
                raise ValueError("Legacy inventory changed during capture; preserve and reconcile")
            if not directory_still_bound(root_fd, ".codex", codex_fd) or not directory_still_bound(codex_fd, BACKUP_DIRECTORY, backup_fd):
                raise ValueError("Codex backup binding changed during capture; preserve and reconcile")
            if not directory_still_bound(backup_fd, capture_name, capture_fd) or not directory_still_bound(capture_fd, "skills", captured_fd):
                raise ValueError("Retained capture binding changed; preserve and reconcile")
            if active_exists(codex_fd):
                raise ValueError("Legacy discovery was recreated during capture; preserve and reconcile")
            print(f"Retained legacy Codex skills at {capture_path}; no backup files deleted")
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        retained = f" Retained capture: {captured}." if captured else ""
        print(f"ERROR: {exc}.{retained} No backup files deleted; preserve and reconcile.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify or retain the legacy Codex skill mirror outside discovery. "
            "Use during agent deployment; never use this to delete custom skills or backups."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/deploy/retire_codex_skills.py verify
  .venv/bin/python scripts/deploy/retire_codex_skills.py apply
Outputs: apply atomically moves .codex/skills into .codex/retired-skills/<id>/skills.
  Standard __pycache__ files mapped to tracked Python sources are retained as
  opaque runtime artifacts; their bytes are never executed or authenticated.
  No backup files are deleted. Verify does not move files.
Exit codes: 0 = absent or accepted mirror; 1 = preserve and reconcile an error.
Related: scripts/deploy_prompts.sh; agents_extensions/README.md; issue #7964.
""",
    )
    parser.add_argument("mode", choices=("verify", "apply"), help="verify only, or apply retained capture (required)")
    args = parser.parse_args()
    return migrate(Path(__file__).resolve().parents[2], args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
