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
from pathlib import Path

BACKUP_DIRECTORY = "retired-skills"
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def source_matches(root: Path, relative: str, payload: bytes) -> bool:
    """Require tracked current bytes or a regular-file blob at this exact path."""
    source_path = f"agents_extensions/shared/skills/{relative}"
    source = root / source_path
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", source_path],
        cwd=root, capture_output=True, check=False, timeout=30,
    )
    if tracked.returncode == 0 and source.is_file() and not source.is_symlink() and payload == source.read_bytes():
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


def inventory(root: Path, tree_fd: int, prefix: str = "") -> dict[str, tuple]:
    """Read a complete inventory without following links at any component."""
    result: dict[str, tuple] = {}
    for name in sorted(os.listdir(tree_fd)):
        relative = f"{prefix}/{name}" if prefix else name
        info = os.stat(name, dir_fd=tree_fd, follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode):
            source = root / "agents_extensions/shared/skills" / relative
            if not source.is_dir() or source.is_symlink():
                raise ValueError("Unknown legacy Codex skill directory; preserve and reconcile")
            child_fd = os.open(name, DIRECTORY_FLAGS, dir_fd=tree_fd)
            try:
                if signature(os.fstat(child_fd)) != signature(info):
                    raise ValueError("Legacy directory changed during inventory; preserve and reconcile")
                result[relative] = signature(info)
                result.update(inventory(root, child_fd, relative))
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
            if not source_matches(root, relative, payload):
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
            before = inventory(root, source_fd)
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
            after = inventory(root, captured_fd)
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "apply"))
    args = parser.parse_args()
    return migrate(Path(__file__).resolve().parents[2], args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
