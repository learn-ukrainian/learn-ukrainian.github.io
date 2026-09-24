"""Session worktree guard: bytes paths, Popen, symlink, and exist_ok.

The hooks under test are the session fixture in ``tests.conftest``. Each test
points that guard at a tmp directory laid out like
``<root>/.worktrees/dispatch/<agent>/<task>``. Nothing here touches the real
checkout's ``.worktrees``.
"""

from __future__ import annotations

import os
import subprocess
import time
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
    monkeypatch.setattr(worktree_guard, "_CREATED_WORKTREE_ATTRIBUTION", {})
    monkeypatch.setattr(worktree_guard, "_POPEN_WORKTREE_CALLS", [])
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
        assert any(call.destination == key and call.absent_before for call in worktree_guard._POPEN_WORKTREE_CALLS)
        assert proc.wait(timeout=30) == 0
    finally:
        if proc.poll() is None:
            proc.wait(timeout=30)
    assert dest.is_dir()
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is not None
    assert key in message


@pytest.mark.parametrize("invoke", ["run", "check_call", "check_output"])
def test_popen_helpers_record_git_worktree_add(tmp_path: Path, guarded_root: Path, invoke: str) -> None:
    dest = _scaffold(guarded_root, f"from-{invoke}")
    git = _fake_git(tmp_path / invoke, status=0)
    argv = [str(git), "-c", "k=v", "worktree", "add", str(dest)]
    kwargs = {"cwd": tmp_path, "env": _git_env(dest), "timeout": 30}
    runners: dict[str, Callable[..., object]] = {
        "run": subprocess.run,
        "check_call": subprocess.check_call,
        "check_output": subprocess.check_output,
    }
    runners[invoke](argv, **kwargs)
    assert dest.is_dir()
    key = worktree_guard._worktree_entry_key(dest)
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is not None
    assert key in message


def test_popen_never_waited_is_reported_when_the_destination_appears(
    tmp_path: Path, guarded_root: Path
) -> None:
    """A short-lived ``git worktree add`` is reported without wait or poll."""
    dest = _scaffold(guarded_root, "unwaited")
    git = _fake_git(tmp_path / "bin", status=0)
    key = worktree_guard._worktree_entry_key(dest)
    proc = subprocess.Popen(
        [str(git), "worktree", "add", str(dest)],
        cwd=tmp_path,
        env=_git_env(dest),
    )
    try:
        deadline = time.monotonic() + 30
        while not dest.is_dir():
            if time.monotonic() > deadline:
                raise AssertionError(f"{dest} was not created")
            time.sleep(0.01)
        assert proc.returncode is None
        message = worktree_guard._worktree_guard_teardown_message()
        assert message is not None
        assert key in message
    finally:
        if proc.poll() is None:
            proc.wait(timeout=30)


def test_unfinished_worktree_add_is_unclassified_not_created(
    tmp_path: Path, guarded_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A still-running add is not reported as created, even if the path appears."""
    monkeypatch.setattr(worktree_guard, "_POPEN_CLASSIFY_TIMEOUT_SECONDS", 0.05)
    parent = guarded_root / "dispatch" / "cursor"
    worktree_guard._ORIGINAL_OS_MKDIR(guarded_root / "dispatch")
    worktree_guard._ORIGINAL_OS_MKDIR(parent)
    dest = parent / "still-running"
    git = tmp_path / "git"
    git.write_text("#!/bin/sh\nsleep 30\n")
    git.chmod(0o755)
    key = worktree_guard._worktree_entry_key(dest)
    proc = subprocess.Popen([str(git), "worktree", "add", str(dest)], cwd=tmp_path)
    try:
        worktree_guard._ORIGINAL_OS_MKDIR(dest)
        message = worktree_guard._worktree_guard_teardown_message()
        assert message is not None
        assert message.startswith("guard could not classify")
        assert "this pytest process created" not in message
        assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=30)


def test_failed_git_worktree_add_is_not_attributed_when_the_directory_remains(
    tmp_path: Path, guarded_root: Path
) -> None:
    """A non-zero exit is not this process creating the worktree."""
    dest = _scaffold(guarded_root, "failed-add")
    git = _fake_git(tmp_path / "bin", status=1)
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call(
            [str(git), "-c", "k=v", "worktree", "add", str(dest)],
            cwd=tmp_path,
            env=_git_env(dest),
            timeout=30,
        )
    assert dest.is_dir()
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is None or key not in message


def test_later_worktree_add_is_reported_after_an_earlier_existing_destination(
    tmp_path: Path, guarded_root: Path
) -> None:
    """An earlier add against a path that already exists must not hide a later create.

    Sol r4: ``setdefault`` kept ``existed_before=True`` from attempt 1, so
    teardown stayed silent after the path was removed and attempt 2 created it.
    """
    dest = _scaffold(guarded_root, "again")
    worktree_guard._ORIGINAL_OS_MKDIR(dest)
    git = _fake_git(tmp_path / "bin", status=0)
    argv = [str(git), "worktree", "add", str(dest)]
    subprocess.run(argv, cwd=tmp_path, env=_git_env(dest), timeout=30, check=True)
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    calls = [call for call in worktree_guard._POPEN_WORKTREE_CALLS if call.destination == key]
    assert [call.absent_before for call in calls] == [False]
    dest.rmdir()
    subprocess.run(argv, cwd=tmp_path, env=_git_env(dest), timeout=30, check=True)
    assert dest.is_dir()
    calls = [call for call in worktree_guard._POPEN_WORKTREE_CALLS if call.destination == key]
    assert [call.absent_before for call in calls] == [False, True]
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is not None
    assert key in message


def test_later_mkdir_is_recorded_from_the_call_that_created_it(guarded_root: Path) -> None:
    """An earlier hit on an existing path does not decide a later mkdir."""
    dest = _scaffold(guarded_root, "mkdir-again")
    worktree_guard._ORIGINAL_OS_MKDIR(dest)
    os.makedirs(dest, exist_ok=True)
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
    os.rmdir(dest)
    os.mkdir(dest)
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES


def test_failed_mkdir_after_external_create_is_not_attributed(guarded_root: Path) -> None:
    """Sol r5: a failed mkdir must not inherit an earlier absent observation.

    mkdir fails because the parent is missing. An external actor creates the
    path. A second mkdir fails with FileExistsError. Neither call created it.
    """
    dest = guarded_root / "dispatch" / "cursor" / "external-actor"
    with pytest.raises(FileNotFoundError):
        os.mkdir(dest)
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
    # The real mkdir, not os.makedirs: makedirs calls the hooked mkdir.
    worktree_guard._ORIGINAL_OS_MKDIR(guarded_root / "dispatch")
    worktree_guard._ORIGINAL_OS_MKDIR(guarded_root / "dispatch" / "cursor")
    worktree_guard._ORIGINAL_OS_MKDIR(dest)
    with pytest.raises(FileExistsError):
        os.mkdir(dest)
    assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
    assert worktree_guard._worktree_guard_teardown_message() is None


def test_later_symlink_is_recorded_from_the_call_that_created_it(
    tmp_path: Path, guarded_root: Path
) -> None:
    dest = _scaffold(guarded_root, "link-again")
    target = tmp_path / "target"
    target.mkdir()
    worktree_guard._ORIGINAL_OS_SYMLINK(target, dest)
    with pytest.raises(FileExistsError):
        os.symlink(target, dest)
    key = worktree_guard._worktree_entry_key(dest)
    assert key is not None
    assert key not in worktree_guard._CREATED_WORKTREE_ENTRIES
    os.unlink(dest)
    os.symlink(target, dest)
    assert key in worktree_guard._CREATED_WORKTREE_ENTRIES


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


def test_acp_redirect_is_only_the_primary_checkout_itself() -> None:
    """Primary cwd is redirected. A dispatch worktree uses the real helper.

    ``resolve_main_root`` maps that worktree to the primary, which used to
    redirect both branches.
    """
    from scripts.ai_agent_bridge import _acp_execution
    from scripts.common.repo_root import main_checkout_root
    from scripts.guardrails.worktree_containment import resolve_main_root

    primary = main_checkout_root(worktree_guard._REPO_ROOT).resolve()
    dispatch = primary / ".worktrees" / "dispatch" / "cursor" / "acp-branch-8523"
    assert resolve_main_root(dispatch) == primary
    assert dispatch.resolve() != primary

    with _acp_execution.acp_execution_cwd(primary, task_id="guard-8523-primary") as workspace:
        assert Path(workspace).resolve() != primary
        assert Path(workspace).resolve().is_relative_to(primary / ".worktrees") is False

    with _acp_execution.acp_execution_cwd(dispatch, task_id="guard-8523-dispatch") as workspace:
        assert Path(workspace).resolve() == dispatch.resolve()


def test_real_checkout_acp_execution_does_not_mkdir_dispatch() -> None:
    """Discuss/ask tests must not leave ``.worktrees/dispatch`` on the real checkout."""
    from scripts.ai_agent_bridge import _acp_execution
    from scripts.common.repo_root import main_checkout_root

    root = main_checkout_root(worktree_guard._REPO_ROOT).resolve()
    dispatch = root / ".worktrees" / "dispatch"
    existed = dispatch.exists()
    with _acp_execution.acp_execution_cwd(root, task_id="guard-8523") as workspace:
        assert Path(workspace).resolve().is_relative_to(root / ".worktrees") is False
    if not existed:
        assert not dispatch.exists()


def test_recorded_creation_names_the_test_and_caller(guarded_root: Path) -> None:
    dest = _scaffold(guarded_root, "attributed")
    os.mkdir(dest)
    message = worktree_guard._worktree_guard_teardown_message()
    assert message is not None
    assert "test_recorded_creation_names_the_test_and_caller" in message
    assert "PYTEST_CURRENT_TEST=" in message
    assert "(call)" in message
    assert "tests/test_conftest_worktree_guard.py:" in message
    assert "caller=" in message


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


def test_github_guard_has_independent_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LU_WORKTREE_GUARD", "0")
    monkeypatch.delenv("LU_GH_GUARD", raising=False)
    assert worktree_guard._worktree_guard_enabled() is False
    assert worktree_guard._gh_guard_enabled() is True
    monkeypatch.setenv("LU_GH_GUARD", "0")
    assert worktree_guard._gh_guard_enabled() is False


def test_real_gh_cannot_be_exempted_by_agent_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_gh = tmp_path / "real-gh"
    fake_backend = tmp_path / "fake-gh"
    real_gh.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_backend.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    real_gh.chmod(0o755)
    fake_backend.chmod(0o755)
    monkeypatch.setattr(worktree_guard, "_REAL_GH_BINARY", os.path.realpath(real_gh))

    with pytest.raises(pytest.fail.Exception, match="spawned real gh") as exc_info:
        worktree_guard._guard_live_github_spawn(
            [str(real_gh), "issue", "view", "1"],
            {"env": {"AGENT_REAL_GH": str(fake_backend)}},
        )
    assert (
        "@pytest.mark.live_github opts this test into real gh/network access; it does not skip the test in CI"
        in str(exc_info.value)
    )


def test_runtime_gh_shim_allows_explicit_fake_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_gh = tmp_path / "real-gh"
    fake_backend = tmp_path / "fake-gh"
    shim = tmp_path / "agent_runtime" / "shims" / "gh"
    for path in (real_gh, fake_backend, shim):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(worktree_guard, "_REAL_GH_BINARY", os.path.realpath(real_gh))

    worktree_guard._guard_live_github_spawn(
        [str(shim), "issue", "view", "1"],
        {"env": {"AGENT_REAL_GH": str(fake_backend)}},
    )


def test_runtime_gh_shim_with_real_backend_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_gh = tmp_path / "real-gh"
    shim = tmp_path / "agent_runtime" / "shims" / "gh"
    for path in (real_gh, shim):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(worktree_guard, "_REAL_GH_BINARY", os.path.realpath(real_gh))

    with pytest.raises(pytest.fail.Exception, match="spawned real gh"):
        worktree_guard._guard_live_github_spawn(
            [str(shim), "issue", "view", "1"],
            {"env": {"AGENT_REAL_GH": str(real_gh)}},
        )


def test_runtime_git_shim_is_not_a_github_spawn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_gh = tmp_path / "real-gh"
    shim = tmp_path / "agent_runtime" / "shims" / "git"
    for path in (real_gh, shim):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(worktree_guard, "_REAL_GH_BINARY", os.path.realpath(real_gh))

    worktree_guard._guard_live_github_spawn(
        [str(shim), "checkout", "some-branch"],
        {"env": {}},
    )


def test_runtime_gh_shim_without_backend_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_gh = tmp_path / "real-gh"
    shim = tmp_path / "agent_runtime" / "shims" / "gh"
    for path in (real_gh, shim):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        path.chmod(0o755)
    monkeypatch.setattr(worktree_guard, "_REAL_GH_BINARY", os.path.realpath(real_gh))

    with pytest.raises(pytest.fail.Exception, match="spawned real gh"):
        worktree_guard._guard_live_github_spawn(
            [str(shim), "issue", "view", "1"],
            {"env": {}},
        )
