"""Give ordinary pytest runs invocation ownership for the scheduled sweep (#10831).

A reviewer sandbox mounts the shared scratch root read-only (#11317). The root
is then still verified, and refused if a symlink, foreign-owned or writable by
group or others, but the run itself is allocated in a fresh owner-only
directory under the sandbox's writable temp: ``TMPDIR``, else shared memory.
``TMPDIR`` is used only if no other user can replace any directory on its path
(each owned by this user or root, and writable by others only when sticky);
shared memory only if others may not rename entries in it.

Once that directory is verified and held open, every entry of the run (its
directory, ``runs``, the run, the lease files and ``scratch``) is created
relative to a held descriptor, never by path, so a replaced directory cannot
redirect a write. The run is named by path only when complete; if that path
does not reach the held run, the candidate is removed through the descriptors
and the next one is tried.

``TMPDIR`` is carried byte for byte from the environment to the allocation:
nothing strips, expands, normalizes or resolves it, because each of those can
name a directory other than the one supplied. A value that cannot be carried
that way (empty, relative, holding a NUL or an unencodable character, or too
long for the kernel to resolve whole) is skipped for the next candidate.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import os
import secrets
import stat
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from functools import partial
from pathlib import Path
from typing import Any

import pytest

from scripts.common.acp_runtime_lock import process_start_time
from scripts.common.scratch import ensure_scratch_root
from scripts.common.task_scratch import (
    LEASE_FILENAME,
    LEASE_SCHEMA_VERSION,
    LOCK_FILENAME,
    PAYLOAD_DIRNAME,
    TaskScratch,
    TaskScratchError,
    _rmdir_held,
    _verify_private_dir,
    _write_lease_at,
    allocate,
    current_boot_id,
)
from scripts.common.task_scratch import NAMESPACE_DIRNAME as LEASE_KIND

NAMESPACE = "pytest-runs"
RUNS_DIRNAME = "runs"
PRIVATE_MODE = 0o700
FALLBACK_PREFIX = "lu-pytest-"
SHARED_MEMORY_TEMP = Path("/dev/shm")
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
# A read-only mount or a denied write. Any other failure stays loud.
_UNWRITABLE_ERRNOS = frozenset({errno.EROFS, errno.EACCES})
_RUN = pytest.StashKey[TaskScratch]()
_POLICY_REMOVES_PASSED = pytest.StashKey[bool]()
_IN_MAIN = pytest.StashKey[bool]()
_LOOP_RETURNED = pytest.StashKey[bool]()
_FINISH_RETURNED = pytest.StashKey[bool]()


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


class _Unusable(Exception):
    """This candidate cannot hold the run; the reason is reported if no candidate can."""


def _reason(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "error")


def _make_unique_dir(parent_fd: int, prefix: str) -> str:
    """Create a fresh 0700 directory with a random name below ``parent_fd``; return its name."""
    for _ in range(100):
        name = prefix + secrets.token_hex(4)
        try:
            os.mkdir(name, PRIVATE_MODE, dir_fd=parent_fd)
        except FileExistsError:
            continue
        return name
    raise FileExistsError(errno.EEXIST, "no unused private temp name")


def _make_private_dir(base_fd: int) -> str:
    return _make_unique_dir(base_fd, FALLBACK_PREFIX)


def _open_made(parent_fd: int, name: str, made: list[tuple[int, str, int]]) -> int:
    """Hold the directory just made as ``name`` below ``parent_fd``; refuse it unless it is ours and owner-only."""
    try:
        fd = os.open(name, _DIR_FLAGS, dir_fd=parent_fd)
    except OSError as exc:
        raise _Unusable("changed") from exc
    st = os.fstat(fd)
    if st.st_uid != os.geteuid() or stat.S_IMODE(st.st_mode) != PRIVATE_MODE:
        os.close(fd)
        raise _Unusable("changed")
    made.append((parent_fd, name, fd))
    return fd


def _names_held(path: str, fd: int) -> bool:
    """``path`` reaches, as the kernel resolves it now, the very directory ``fd`` holds."""
    try:
        named = os.stat(path, follow_symlinks=False)
    except OSError:
        return False
    held = os.fstat(fd)
    return (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino)


def _discard(made: list[tuple[int, str, int]], run_fd: int | None, lock_fd: int | None) -> None:
    """Remove what this candidate made, through the held descriptors only, and release its lease."""
    if run_fd is not None:
        for entry in (LEASE_FILENAME, f".{LEASE_FILENAME}.tmp", LOCK_FILENAME):
            with contextlib.suppress(OSError):
                os.unlink(entry, dir_fd=run_fd)
    if lock_fd is not None:
        os.close(lock_fd)
    for parent_fd, name, fd in reversed(made):
        # Removed only while ``name`` still is the held directory; a replacement is left alone.
        with contextlib.suppress(OSError, TaskScratchError):
            _rmdir_held(parent_fd, name, held_fd=fd, held_st=os.fstat(fd))
        os.close(fd)


def _allocate_in_created(base: str, base_fd: int, name: str) -> TaskScratch:
    """Allocate the run inside ``base/name``, creating every entry relative to a held descriptor.

    Nothing is created by path, so replacing any directory on the way cannot move
    a write out of the directories held. Only once the run is complete is it
    named by path, for pytest; that path must reach the held run and payload, or
    the candidate is removed through the descriptors and refused.
    """
    made: list[tuple[int, str, int]] = []
    run_fd: int | None = None
    lock_fd: int | None = None
    try:
        private_fd = _open_made(base_fd, name, made)
        os.mkdir(RUNS_DIRNAME, PRIVATE_MODE, dir_fd=private_fd)
        runs_fd = _open_made(private_fd, RUNS_DIRNAME, made)
        run_name = _make_unique_dir(runs_fd, "pytest.")
        run_fd = _open_made(runs_fd, run_name, made)
        lock_fd = os.open(
            LOCK_FILENAME, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=run_fd
        )
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        held = os.fstat(run_fd)
        # The lease allocate() writes, so lease readers treat this run like any other.
        lease: dict[str, Any] = {
            "schema_version": LEASE_SCHEMA_VERSION,
            "kind": LEASE_KIND,
            "task_id": "pytest",
            "invocation_id": run_name,
            "uid": os.geteuid(),
            "dir": {"dev": held.st_dev, "ino": held.st_ino},
            "owner": {"pid": os.getpid(), "start_time": process_start_time(os.getpid()), "boot_id": current_boot_id()},
            "child": None,
            "state": "registered",
            "created_at": time.time(),
        }
        _write_lease_at(run_fd, lease)
        os.mkdir(PAYLOAD_DIRNAME, PRIVATE_MODE, dir_fd=run_fd)
        payload_fd = _open_made(run_fd, PAYLOAD_DIRNAME, made)
        # Appended to the supplied value as it is: the one path pytest and every tempfile user get.
        run = os.path.join(base, name, RUNS_DIRNAME, run_name)
        payload = os.path.join(run, PAYLOAD_DIRNAME)
        if not (_names_held(run, run_fd) and _names_held(payload, payload_fd)):
            raise _Unusable("changed")
    except BaseException as exc:
        _discard(made, run_fd, lock_fd)
        if isinstance(exc, OSError):
            raise _Unusable(_reason(exc)) from exc
        raise
    for _parent_fd, _name, fd in made:
        if fd != run_fd:
            os.close(fd)
    return TaskScratch(
        task_id="pytest",
        invocation_id=run_name,
        namespace=Path(os.path.dirname(run)),
        path=Path(run),
        payload_dir=Path(payload),
        lease=lease,
        _dir_fd=run_fd,
        _lock_fd=lock_fd,
    )


def _allocate_private_fallback() -> TaskScratch:
    """Allocate in a fresh owner-only directory below the first writable temp no other user can tamper with."""
    failures = []
    for base, open_base in _fallback_bases():
        try:
            base_fd = open_base()
        except OSError as exc:
            failures.append(_reason(exc))
            continue
        if base_fd is None:
            failures.append("replaceable")
            continue
        try:
            # A new 0700 directory with a random name: exclusive even in a shared sticky parent.
            name = _make_private_dir(base_fd)
            return _allocate_in_created(base, base_fd, name)
        except OSError as exc:
            failures.append(_reason(exc))
        except _Unusable as exc:
            failures.append(str(exc))
        finally:
            os.close(base_fd)
    raise TaskScratchError(
        "pytest scratch root is not writable and no private writable temp could be created "
        f"(TMPDIR, then shared memory): {', '.join(failures)}"
    )


def _around_outermost_call(caller: Any, around: Callable[[Callable[[], Any], Mapping[str, Any]], Any]) -> None:
    """Run each outermost call of a hook through ``around``, outside all of the hook's code.

    ``around`` wraps the hook caller's executor (pluggy's private ``_hookexec``),
    which runs every implementation, wrapper and hook-call monitor, whatever
    their order, so it sees how the whole call ended, including a pytest.exit
    that pytest catches later. A nested call of the same hook runs unobserved.
    If pluggy stops providing or calling that executor, nothing is observed
    and every session keeps its run.
    """
    inner = getattr(caller, "_hookexec", None)
    if not callable(inner):
        return
    depth = 0

    def hookexec(name: str, impls: Any, kwargs: Mapping[str, Any], firstresult: bool) -> Any:
        nonlocal depth
        if depth:
            return inner(name, impls, kwargs, firstresult)
        depth += 1
        try:
            return around(partial(inner, name, impls, kwargs, firstresult), kwargs)
        finally:
            depth -= 1

    with contextlib.suppress(AttributeError):
        caller._hookexec = hookexec


def _record_return(stash: pytest.Stash, key: pytest.StashKey[bool]) -> Callable[..., Any]:
    """Record in the stash whether the call returned normally."""

    def around(call: Callable[[], Any], _kwargs: Mapping[str, Any]) -> Any:
        stash[key] = False
        result = call()
        stash[key] = True
        return result

    return around


def _release(scratch: TaskScratch, *, remove: bool) -> None:
    """Remove a passed run, as pytest removes its own basetemp; keep any other run for inspection."""
    try:
        if remove:
            with contextlib.suppress(OSError, TaskScratchError):
                scratch.remove()
    finally:
        scratch.preserve()


def _release_at_teardown(stash: pytest.Stash | None, scratch: TaskScratch) -> None:
    """Keep the run, unless pytest's main command settles it once the command returns."""
    if stash is None or not stash.get(_IN_MAIN, False):
        scratch.preserve()


def _settle_after_main(call: Callable[[], Any], kwargs: Mapping[str, Any]) -> Any:
    """Run pytest's main command, then release the run, removing it only when the session passed.

    Pytest itself deletes the basetemp of a passed session under the "failed"
    retention policy, but only when no --basetemp was given, and this plugin
    always gives one. Every hook and every config cleanup has run when the
    command returns, so its return code is final and any failure among them
    propagates out of it. The test loop and the whole session-finish call
    must also have returned normally. Any other session keeps its run.
    """
    stash = getattr(kwargs.get("config"), "stash", None)
    if stash is None:
        return call()
    stash[_IN_MAIN] = True
    passed = False
    try:
        result = call()
        passed = (
            result == pytest.ExitCode.OK
            and stash.get(_POLICY_REMOVES_PASSED, False)
            and stash.get(_LOOP_RETURNED, False)
            and stash.get(_FINISH_RETURNED, False)
        )
        return result
    finally:
        stash[_IN_MAIN] = False
        scratch = stash.get(_RUN, None)
        if scratch is not None:
            _release(scratch, remove=passed)


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
    # A caller without a stash gets the plain preservation it always had.
    stash = getattr(config, "stash", None)
    if stash is not None:
        stash[_RUN] = scratch
        stash[_POLICY_REMOVES_PASSED] = config.getini("tmp_path_retention_policy") == "failed"
    config.add_cleanup(partial(_release_at_teardown, stash, scratch))
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


def pytest_plugin_registered(plugin: object, manager: pytest.PytestPluginManager) -> None:
    """Watch pytest's main command from outside; registration comes before the command runs."""
    if plugin is sys.modules[__name__]:
        _around_outermost_call(manager.hook.pytest_cmdline_main, _settle_after_main)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Watch how the session's test loop and finish end."""
    stash = getattr(session.config, "stash", None)
    if stash is None or _RUN not in stash:
        return
    hook = session.config.pluginmanager.hook
    _around_outermost_call(hook.pytest_runtestloop, _record_return(stash, _LOOP_RETURNED))
    _around_outermost_call(hook.pytest_sessionfinish, _record_return(stash, _FINISH_RETURNED))
