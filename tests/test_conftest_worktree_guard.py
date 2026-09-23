"""Session worktree guard: bytes paths, Popen, symlink, and exist_ok.

The hooks under test are the session fixture in ``tests.conftest``. Each test
points that guard at a tmp directory laid out like
``<root>/.worktrees/dispatch/<agent>/<task>``. Nothing here touches the real
checkout's ``.worktrees``.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

import tests.conftest as worktree_guard


@pytest.fixture
def guarded_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Swap the guard's root for a tmp tree. The real checkout stays untouched."""
    root = tmp_path / ".worktrees"
    root.mkdir()
    real = os.path.realpath(root)
    monkeypatch.setattr(worktree_guard, "_REAL_WORKTREES_DIR", real)
    monkeypatch.setattr(worktree_guard, "_REAL_WORKTREES_PREFIX", real + os.sep)
    monkeypatch.setattr(worktree_guard, "_WORKTREE_ENTRIES_AT_START", set())
    monkeypatch.setattr(worktree_guard, "_CREATED_WORKTREE_ENTRIES", set())
    monkeypatch.setattr(worktree_guard, "_GUARD_CLASSIFY_FAILURES", [])
    return Path(real)


def _scaffold(root: Path, task: str) -> Path:
    """Parent of a dispatch entry, created without going through the hooks."""
    parent = root / "dispatch" / "cursor"
    worktree_guard._ORIGINAL_OS_MAKEDIRS(parent, exist_ok=True)
    return parent / task


def _fake_git(directory: Path, status: int) -> Path:
    """Executable named ``git`` that creates ``$GUARD_TEST_DEST`` and exits ``status``."""
    directory.mkdir()
    git = directory / "git"
    git.write_text(
        "#!/bin/sh\n"
        'if [ -n "${GUARD_TEST_DEST:-}" ]; then\n'
        '  mkdir -p -- "$GUARD_TEST_DEST"\n'
        "fi\n"
        f"exit {status}\n"
    )
    git.chmod(0o755)
    return git


def _git_env(dest: Path) -> dict[str, str]:
    return {"GUARD_TEST_DEST": str(dest), "PATH": "/usr/bin:/bin"}


def test_bytes_paths_do_not_break_mkdir(tmp_path: Path, guarded_root: Path) -> None:
    """Sol: ``_worktree_entry_key(b"/tmp/example")`` raised before the real call."""
    assert worktree_guard._worktree_entry_key(b"/tmp/example") is None
    assert worktree_guard._missing_worktree_entries(b"/tmp/example") == []

    plain = tmp_path / "plain"
    os.mkdir(os.fsencode(plain))
    os.makedirs(os.fsencode(tmp_path / "plain" / "nested"))
    assert plain.is_dir()
    assert not worktree_guard._CREATED_WORKTREE_ENTRIES

    dest = _scaffold(guarded_root, "bytes-task")
    os.mkdir(os.fsencode(dest))
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES
    assert worktree_guard._worktree_entry_key(os.fsencode(dest)) == key

    with pytest.raises(TypeError):
        os.mkdir(object())  # type: ignore[arg-type]
    assert worktree_guard._GUARD_CLASSIFY_FAILURES == []


def test_parser_skips_git_globals_and_resolves_against_cd(tmp_path: Path, guarded_root: Path) -> None:
    dest = _scaffold(guarded_root, "parsed")
    argv = [
        "git",
        "-c",
        "user.email=a@b.c",
        "-cabbrev=7",
        "--git-dir=/nope",
        "--work-tree",
        "/also-nope",
        "-C",
        str(dest.parent),
        "worktree",
        "add",
        "-b",
        "branch-name",
        dest.name,
    ]
    key = worktree_guard._worktree_entry_key(dest)
    assert worktree_guard._git_worktree_add_destination(argv, tmp_path) == key
    encoded = [os.fsencode(part) for part in argv]
    assert worktree_guard._git_worktree_add_destination(encoded, os.fsencode(tmp_path)) == key
    assert worktree_guard._git_worktree_add_destination(["git", "-c", "k=v", "status"], None) is None
    assert worktree_guard._git_worktree_add_destination(["git", "-C"], None) is None
    assert worktree_guard._git_worktree_add_destination(["git", "-c"], None) is None


def test_popen_git_worktree_add_with_config_and_cd_is_recorded_after_success(
    tmp_path: Path, guarded_root: Path
) -> None:
    dest = _scaffold(guarded_root, "from-popen")
    git = _fake_git(tmp_path / "bin", status=0)
    key = worktree_guard._worktree_entry_key(dest)
    proc = subprocess.Popen(
        [
            str(git),
            "-c",
            "core.abbrev=7",
            "--git-dir=/tmp/not-a-repo",
            "--work-tree=/tmp/not-a-tree",
            "-C",
            str(dest.parent),
            "worktree",
            "add",
            dest.name,
        ],
        cwd=tmp_path,
        env=_git_env(dest),
    )
    try:
        # __init__ must not record. The process can already have exited.
        assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
        assert proc.wait() == 0
    finally:
        if proc.poll() is None:
            proc.wait()
    assert dest.is_dir()
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES


@pytest.mark.parametrize("invoke", ["run", "check_call", "check_output"])
def test_popen_helpers_record_git_worktree_add(tmp_path: Path, guarded_root: Path, invoke: str) -> None:
    dest = _scaffold(guarded_root, f"from-{invoke}")
    git = _fake_git(tmp_path / invoke, status=0)
    argv = [str(git), "-c", "k=v", "worktree", "add", str(dest)]
    kwargs = {"cwd": tmp_path, "env": _git_env(dest)}
    runners: dict[str, Callable[..., object]] = {
        "run": subprocess.run,
        "check_call": subprocess.check_call,
        "check_output": subprocess.check_output,
    }
    runners[invoke](argv, **kwargs)
    assert dest.is_dir()
    assert worktree_guard._worktree_entry_key(dest) in worktree_guard._CREATED_WORKTREE_ENTRIES


def test_failed_check_call_does_not_record_even_if_the_directory_appeared(
    tmp_path: Path, guarded_root: Path
) -> None:
    dest = _scaffold(guarded_root, "failed-add")
    git = _fake_git(tmp_path / "bin", status=1)
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(
            [str(git), "-c", "k=v", "worktree", "add", str(dest)],
            cwd=tmp_path,
            env=_git_env(dest),
        )
    assert dest.is_dir()
    assert worktree_guard._worktree_entry_key(dest) not in worktree_guard._CREATED_WORKTREE_ENTRIES


def test_symlink_records_the_link_path_not_the_target(tmp_path: Path, guarded_root: Path) -> None:
    target = tmp_path / "target-dir"
    target.mkdir()
    link = _scaffold(guarded_root, "linked-task")
    os.symlink(target, link)
    key = worktree_guard._worktree_entry_key(link)
    assert key == os.path.join(os.path.realpath(link.parent), link.name)
    assert os.path.realpath(link) == os.path.realpath(target)
    assert key != os.path.realpath(link)
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES


def test_makedirs_records_a_new_entry_and_skips_exist_ok(guarded_root: Path) -> None:
    created = _scaffold(guarded_root, "fresh")
    os.makedirs(created)
    key = worktree_guard._worktree_entry_key(created)
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES

    existing = _scaffold(guarded_root, "kept")
    worktree_guard._ORIGINAL_OS_MKDIR(existing)
    worktree_guard._CREATED_WORKTREE_ENTRIES.clear()
    os.makedirs(existing, exist_ok=True)
    os.makedirs(created, exist_ok=True)
    assert not worktree_guard._CREATED_WORKTREE_ENTRIES


def test_nested_directory_inside_an_entry_is_ignored(guarded_root: Path) -> None:
    entry = _scaffold(guarded_root, "checkout")
    os.mkdir(entry)
    worktree_guard._CREATED_WORKTREE_ENTRIES.clear()
    os.mkdir(entry / "src")
    assert not worktree_guard._CREATED_WORKTREE_ENTRIES


def test_classify_error_falls_through_and_is_reported_at_teardown(
    tmp_path: Path, guarded_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(path: object) -> str | None:
        raise RuntimeError(f"classify blew up on {path!r}")

    monkeypatch.setattr(worktree_guard, "_worktree_entry_key", explode)
    target = tmp_path / "still-created"
    os.mkdir(target)
    assert target.is_dir()
    assert worktree_guard._GUARD_CLASSIFY_FAILURES
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is not None
    assert message.startswith("guard could not classify")


def test_worktree_guard_honours_env_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LU_WORKTREE_GUARD", raising=False)
    assert worktree_guard._worktree_guard_enabled() is True
    monkeypatch.setenv("LU_WORKTREE_GUARD", "0")
    assert worktree_guard._worktree_guard_enabled() is False
    monkeypatch.setenv("LU_WORKTREE_GUARD", "1")
    assert worktree_guard._worktree_guard_enabled() is True
