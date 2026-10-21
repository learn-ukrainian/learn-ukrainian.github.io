"""Give ordinary pytest runs invocation ownership for the scheduled sweep (#10831).

A reviewer sandbox mounts the shared scratch root read-only (#11317). The root
is then still verified, and refused if a symlink, foreign-owned or writable by
group or others, but the run itself is allocated in a fresh owner-only
directory under the sandbox's writable temp: ``TMPDIR``, else shared memory.
A temp where others may rename entries (writable, not sticky) is skipped, and
the run must land in the very directory created there.
"""

from __future__ import annotations

import errno
import os
import stat
import tempfile
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


def _fallback_bases() -> list[Path]:
    bases = []
    tmpdir = os.environ.get("TMPDIR", "").strip()
    if os.path.isabs(tmpdir):
        bases.append(Path(tmpdir))
    bases.append(SHARED_MEMORY_TEMP)
    return bases


def _others_can_rename_in(base: Path) -> bool:
    """Group or others may write ``base`` without the sticky bit, so may swap our entry in it."""
    mode = os.stat(base).st_mode
    return bool(mode & 0o022) and not mode & stat.S_ISVTX


def _allocate_in_created(private: Path) -> TaskScratch:
    """Allocate below ``private`` only if the run lands in the directory this process just created."""
    try:
        fd = os.open(private, _DIR_FLAGS)
    except OSError as exc:
        raise TaskScratchError(f"pytest private temp changed after creation: {private}") from exc
    try:
        st = os.fstat(fd)
        if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != PRIVATE_MODE:
            raise TaskScratchError(f"pytest private temp is not owner-only: {private}")
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
    """Allocate in a fresh owner-only directory below the first writable temp no other user can rename in."""
    failures = []
    for base in _fallback_bases():
        try:
            if _others_can_rename_in(base):
                failures.append("not-sticky")
                continue
            # A new 0700 directory with a random name: exclusive even in a shared sticky parent.
            private = Path(tempfile.mkdtemp(prefix=FALLBACK_PREFIX, dir=base))
        except OSError as exc:
            failures.append(errno.errorcode.get(exc.errno or 0, "error"))
            continue
        return _allocate_in_created(private)
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
