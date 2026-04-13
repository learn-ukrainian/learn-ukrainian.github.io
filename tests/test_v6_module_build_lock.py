"""Regression tests for ModuleBuildLock in v6_build.py."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

v6_build = importlib.import_module("build.v6_build")


def test_release_does_not_unlink_locked_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    curriculum_root = tmp_path / "curriculum" / "l2-uk-en"
    monkeypatch.setattr(v6_build, "CURRICULUM_ROOT", curriculum_root)

    lock1 = v6_build.ModuleBuildLock("a2", "a2-bridge")
    assert lock1.acquire() is True

    lock_path = curriculum_root / "a2" / "orchestration" / "a2-bridge" / ".build.lock"
    assert lock_path.exists()

    original_flock = v6_build.fcntl.flock
    nested_lock: v6_build.ModuleBuildLock | None = None

    def race_on_unlock(fd: int, operation: int) -> None:
        nonlocal nested_lock
        original_flock(fd, operation)
        if operation == v6_build.fcntl.LOCK_UN and nested_lock is None:
            nested_lock = v6_build.ModuleBuildLock("a2", "a2-bridge")
            assert nested_lock.acquire() is True

    monkeypatch.setattr(v6_build.fcntl, "flock", race_on_unlock)

    try:
        lock1.release()
    finally:
        monkeypatch.setattr(v6_build.fcntl, "flock", original_flock)

    assert nested_lock is not None
    assert lock_path.exists()

    third_lock = v6_build.ModuleBuildLock("a2", "a2-bridge")
    try:
        assert third_lock.acquire() is False
    finally:
        if third_lock._fd is not None:
            third_lock.release()
        nested_lock.release()
