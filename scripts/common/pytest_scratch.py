"""Give ordinary pytest runs invocation ownership for the scheduled sweep (#10831).

A reviewer sandbox mounts the shared scratch root read-only (#11317). The root
is then still verified, and refused if a symlink, foreign-owned or writable by
group or others, but the run itself is allocated in a fresh owner-only
directory under the sandbox's writable temp: ``TMPDIR``, else shared memory.
``TMPDIR`` is used only if no other user can replace any directory on its path
(each owned by this user or root, and writable by others only when sticky);
shared memory only if others may not rename entries in it. The run must land
in the very directory created there.

``TMPDIR`` is carried byte for byte from the environment to the allocation:
nothing strips, expands, normalizes or resolves it, because each of those can
name a directory other than the one supplied. A value that cannot be carried
that way (empty, relative, holding a NUL or an unencodable character, or too
long for the kernel to resolve whole) is skipped for the next candidate.
"""

from __future__ import annotations

import errno
import os
import secrets
import stat
import tempfile
from collections.abc import Callable
from functools import partial
from pathlib import Path

import pytest

from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import TaskScratch, TaskScratchError, _verify_private_dir, allocate

NAMESPACE = "pytest-runs"
RUNS_DIRNAME = "runs"
PRIVATE_MODE = 0o700
FALLBACK_PREFIX = "lu-pytest-"
SHARED_MEMORY_TEMP = Path("/dev/shm")
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
# A read-only mount or a denied write. Any other failure stays loud.
_UNWRITABLE_ERRNOS = frozenset({errno.EROFS, errno.EACCES})


def _is_unwritable(exc: OSError) -> bool:
    return exc.errno in _UNWRITABLE_ERRNOS


def _not_private(root: Path) -> TaskScratchError:
    return TaskScratchError(f"pytest scratch root is group- or other-writable and cannot be made private: {root}")


def _private_shared_root() -> Path | None:
    """Return the verified shared pytest root, or None when it is safe but this sandbox cannot write it."""
    root = ensure_scratch_root() / NAMESPACE
    try:
        os.mkdir(root, PRIVATE_MODE)
    except FileExistsError:
        pass
    except OSError as exc:
        if not _is_unwritable(exc) or os.path.lexists(root):
            raise
        return None  # No root exists to verify, and none can be made here.
    checked = _verify_private_dir(root, what="pytest scratch root")
    try:
        fd = os.open(root, _DIR_FLAGS)
    except OSError as exc:
        # A read-only mount still opens for reading: this is the root's own mode, never a fallback.
        if stat.S_IMODE(checked.st_mode) & 0o022:
            raise _not_private(root) from exc
        raise
    try:
        # Recheck what the descriptor holds: the path may have been replaced since the check.
        st = os.fstat(fd)
        if (st.st_dev, st.st_ino) != (checked.st_dev, checked.st_ino):
            raise TaskScratchError(f"pytest scratch root changed during verification: {root}")
        if st.st_uid != os.geteuid():
            raise TaskScratchError(f"pytest scratch root is owned by uid {st.st_uid}, not {os.geteuid()}: {root}")
        mode = stat.S_IMODE(st.st_mode)
        if mode != PRIVATE_MODE:
            # The pre-push gate also verifies ancestors of its test fixtures. Do not
            # let a collaborative umask create a group-writable pytest parent.
            try:
                os.fchmod(fd, PRIVATE_MODE)
            except OSError as exc:
                if not _is_unwritable(exc):
                    raise
                if mode & 0o022:
                    raise _not_private(root) from exc
                return None
    finally:
        os.close(fd)
    return root


def _others_can_rename_in(mode: int) -> bool:
    """Group or others may write the directory without the sticky bit, so may swap our entry in it."""
    return bool(mode & 0o022) and not mode & stat.S_ISVTX


def _replaceable_by_others(st: os.stat_result) -> bool:
    """Another user could rename or replace entries of this directory: it is theirs, or theirs to write."""
    return st.st_uid not in (0, os.geteuid()) or _others_can_rename_in(st.st_mode)


def _open_unreplaceable(path: str) -> int | None:
    """Open ``path`` from ``/`` one component at a time; None if another user could replace any of it.

    Owner-only mode on ``path`` does not protect its name in its parent, so every
    directory from ``/`` down must be unreplaceable. ``O_NOFOLLOW`` refuses a symlink.
    The components are walked as supplied: normalizing first would drop a symlink
    that a following ``..`` steps out of, so ``..`` is refused instead. The whole
    value must then resolve, as the kernel reads it, to the directory walked.
    """
    parts = [part for part in path.split("/") if part]
    if ".." in parts:
        return None
    fd = os.open("/", _DIR_FLAGS)
    try:
        for part in parts:
            if _replaceable_by_others(os.fstat(fd)):
                os.close(fd)
                return None
            child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        walked = os.fstat(fd)
        # Allocation names the directory by this very string; a value too long to resolve whole raises here.
        named = os.stat(path, follow_symlinks=False)
        if _replaceable_by_others(walked) or (named.st_dev, named.st_ino) != (walked.st_dev, walked.st_ino):
            os.close(fd)
            return None
    except BaseException:
        os.close(fd)
        raise
    return fd


def _open_shared_memory(path: str) -> int | None:
    """Open the provisioned shared-memory temp; None if others may rename entries in it."""
    fd = os.open(path, _DIR_FLAGS)
    if _others_can_rename_in(os.fstat(fd).st_mode):
        os.close(fd)
        return None
    return fd


def _verbatim_absolute(value: str) -> str | None:
    """``value`` unchanged if the OS can take it as one absolute path exactly as written, else None."""
    if not value.startswith("/") or "\0" in value:
        return None
    try:
        os.fsencode(value)
    except UnicodeEncodeError:
        return None
    return value


def _fallback_bases() -> list[tuple[str, Callable[[], int | None]]]:
    """Each candidate temp with how to open it: TMPDIR only if its whole path, as supplied, is unreplaceable."""
    bases: list[tuple[str, Callable[[], int | None]]] = []
    tmpdir = _verbatim_absolute(os.environ.get("TMPDIR", ""))
    if tmpdir is not None:
        bases.append((tmpdir, partial(_open_unreplaceable, tmpdir)))
    shared_memory = os.fspath(SHARED_MEMORY_TEMP)
    bases.append((shared_memory, partial(_open_shared_memory, shared_memory)))
    return bases


def _make_private_dir(base_fd: int) -> str:
    """Create a fresh 0700 directory with a random name below ``base_fd``; return its name."""
    for _ in range(100):
        name = FALLBACK_PREFIX + secrets.token_hex(4)
        try:
            os.mkdir(name, PRIVATE_MODE, dir_fd=base_fd)
        except FileExistsError:
            continue
        return name
    raise FileExistsError(errno.EEXIST, "no unused private temp name")


def _allocate_in_created(base: str, base_fd: int, name: str) -> TaskScratch:
    """Allocate below ``base/name`` only if the run lands in the directory this process just created."""
    # Appended to the supplied value as it is; the one Path made here is what is checked and what allocate() gets.
    private = Path(os.path.join(base, name))
    try:
        fd = os.open(name, _DIR_FLAGS, dir_fd=base_fd)
    except OSError as exc:
        raise TaskScratchError(f"pytest private temp changed after creation: {private}") from exc
    try:
        st = os.fstat(fd)
        if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != PRIVATE_MODE:
            raise TaskScratchError(f"pytest private temp is not owner-only: {private}")
        # allocate() takes a path: it must still name this directory, or it would write elsewhere.
        try:
            named = os.stat(private, follow_symlinks=False)
        except OSError as exc:
            raise TaskScratchError(f"pytest private temp changed after creation: {private}") from exc
        if (named.st_dev, named.st_ino) != (st.st_dev, st.st_ino):
            raise TaskScratchError(f"pytest private temp changed after creation: {private}")
        scratch = allocate("pytest", root=private, namespace_dirname=RUNS_DIRNAME)
        # allocate() walks the path again; reach the run from the descriptor and compare.
        expected = (scratch.lease["dir"]["dev"], scratch.lease["dir"]["ino"])
        try:
            runs_fd = os.open(RUNS_DIRNAME, _DIR_FLAGS, dir_fd=fd)
            try:
                run = os.stat(scratch.invocation_id, dir_fd=runs_fd, follow_symlinks=False)
            finally:
                os.close(runs_fd)
            contained = (run.st_dev, run.st_ino) == expected
        except OSError:
            contained = False
        if not contained:
            scratch.preserve()
            raise TaskScratchError(f"pytest private temp changed during allocation: {private}")
        return scratch
    finally:
        os.close(fd)


def _allocate_private_fallback() -> TaskScratch:
    """Allocate in a fresh owner-only directory below the first writable temp no other user can tamper with."""
    failures = []
    for base, open_base in _fallback_bases():
        try:
            base_fd = open_base()
            if base_fd is None:
                failures.append("replaceable")
                continue
            try:
                # A new 0700 directory with a random name: exclusive even in a shared sticky parent.
                name = _make_private_dir(base_fd)
            except OSError:
                os.close(base_fd)
                raise
        except OSError as exc:
            failures.append(errno.errorcode.get(exc.errno or 0, "error"))
            continue
        try:
            return _allocate_in_created(base, base_fd, name)
        finally:
            os.close(base_fd)
    raise TaskScratchError(
        "pytest scratch root is not writable and no private writable temp could be created "
        f"(TMPDIR, then shared memory): {', '.join(failures)}"
    )


def _allocate_run() -> TaskScratch:
    root = _private_shared_root()
    if root is not None:
        try:
            return allocate("pytest", root=root, namespace_dirname=RUNS_DIRNAME)
        except OSError as exc:
            if not _is_unwritable(exc):
                raise
    return _allocate_private_fallback()


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Hold one invocation lock until teardown; explicit base temps retain their owner."""
    if hasattr(config, "workerinput") or config.option.basetemp is not None:
        return
    scratch = _allocate_run()
    # Pytest recreates --basetemp. Keep ownership metadata outside that payload.
    config.option.basetemp = str(scratch.payload_dir / "base")
    config.add_cleanup(scratch.preserve)
    # Fixtures and ordinary tempfile users must share a containment root.
    # Workers inherit TMPDIR; this process may already have cached tempdir.
    previous_env = os.environ.get("TMPDIR")
    previous_tempdir = tempfile.tempdir
    os.environ["TMPDIR"] = str(scratch.payload_dir)
    tempfile.tempdir = str(scratch.payload_dir)

    def restore_tempdir() -> None:
        tempfile.tempdir = previous_tempdir
        if previous_env is None:
            os.environ.pop("TMPDIR", None)
        else:
            os.environ["TMPDIR"] = previous_env

    config.add_cleanup(restore_tempdir)
