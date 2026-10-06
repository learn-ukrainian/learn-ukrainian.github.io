"""Redirect refusal and concurrent context claims, including dead/live holders."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks"
HELPER = HOOKS / "context-hook-state.py"
SESSION = "state-session"


@pytest.fixture
def state_module():
    spec = importlib.util.spec_from_file_location("context_hook_state", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def hook_case(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    record = tmp_path / "record.json"
    record.write_text(json.dumps({
        "session_id": SESSION,
        "actual_context_window_tokens": 1_000_000,
        "actual_context_window_provenance": "declared-profile",
        "rollover_warning_percentages": [65, 70, 75],
        "rollover_mode": "operator_restart",
    }))
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(json.dumps({
        "type": "assistant", "message": {"usage": {"input_tokens": 760_000}},
    }) + "\n")
    env = os.environ.copy()
    for name in (
        "CLAUDE_NON_INTERACTIVE", "LEARN_UK_PIPELINE", "LEARN_UKRAINIAN_PIPELINE",
        "GEMINI_SESSION", "GROK_AGENT", "CODEX_THREAD_ID", "CODEX_SESSION_ID",
        "SESSION_HANDOFF_AGENT", "LEARN_UKRAINIAN_DISPATCH_TASK_ID", "SESSION_EPIC",
        "CODEX_CANONICAL_REPO_ROOT",
    ):
        env.pop(name, None)
    env.update({
        "CLAUDE_PROJECT_DIR": str(project),
        "LEARN_UKRAINIAN_SESSION_RECORD": str(record),
        "THREAD_ROLLOVER_PYTHON": sys.executable,
    })
    payload = json.dumps({
        "session_id": SESSION, "transcript_path": str(transcript),
        "hook_event_name": "UserPromptSubmit",
    })
    return project, env, payload


def run_hook(case, hook="context-monitor.sh"):
    project, env, payload = case
    result = subprocess.run(
        [str(HOOKS / hook)], input=payload, env=env, cwd=project,
        text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    return result.stdout


@pytest.mark.parametrize("redirect", ["tier", "lock", "directory", "batch_state"])
@pytest.mark.parametrize("hook", ["context-monitor.sh", "context-rollover-guard.sh"])
def test_redirect_refused_leaves_outside_byte_identical(hook_case, tmp_path, redirect, hook):
    project, _, _ = hook_case
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / f"{SESSION}.tier"
    original = b"3 760000\n"
    target.write_bytes(original)
    state = project / "batch_state/context_monitor"
    if redirect == "batch_state":
        (outside / "context_monitor").mkdir()
        (outside / "context_monitor" / f"{SESSION}.tier").write_bytes(original)
        (project / "batch_state").symlink_to(outside, target_is_directory=True)
    elif redirect == "directory":
        state.parent.mkdir()
        state.symlink_to(outside, target_is_directory=True)
    else:
        state.mkdir(parents=True)
        (state / f"{SESSION}.{redirect}").symlink_to(target)
    before = {str(p.relative_to(outside)): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
    assert run_hook(hook_case, hook) == ""
    assert run_hook(hook_case, hook) == ""
    after = {str(p.relative_to(outside)): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
    assert after == before


def test_legacy_predictable_temp_name_is_never_used(hook_case, tmp_path):
    project, _, _ = hook_case
    state = project / "batch_state/context_monitor"
    state.mkdir(parents=True)
    target = tmp_path / "outside"
    target.write_bytes(b"unchanged\n")
    # Cover old <name>.tmp.<pid> names for the actual hook processes.
    processes = [subprocess.Popen(
        [str(HOOKS / "context-monitor.sh")], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=hook_case[1], cwd=project,
    ) for _ in range(12)]
    try:
        for process in processes:
            (state / f"{SESSION}.tier.tmp.{process.pid}").symlink_to(target)
        outputs = [process.communicate(hook_case[2], timeout=30) for process in processes]
        assert all(process.returncode == 0 for process in processes)
        assert all(stderr == "" for _, stderr in outputs)
        assert sum(bool(stdout) for stdout, _ in outputs) == 1
        assert target.read_bytes() == b"unchanged\n"
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait()


@pytest.mark.parametrize("hide_flock", [False, True])
def test_twelve_concurrent_calls_announce_each_tier_once(hook_case, tmp_path, hide_flock):
    project, env, payload = hook_case
    if hide_flock:
        binaries = tmp_path / "bin"
        binaries.mkdir()
        for name in ("cat", "jq", "tail", "dirname", "basename"):
            executable = shutil.which(name)
            assert executable
            (binaries / name).symlink_to(executable)
        env["PATH"] = str(binaries)
        assert shutil.which("flock", path=env["PATH"]) is None
    else:
        assert shutil.which("flock", path=env["PATH"])
    transcript = Path(json.loads(payload)["transcript_path"])
    for tier, tokens, prefix in ((1, 655_000, "HEADS UP:"), (2, 705_000, "CRITICAL:"), (3, 760_000, "EMERGENCY:")):
        transcript.write_text(json.dumps({
            "type": "assistant", "message": {"usage": {"input_tokens": tokens}},
        }) + "\n")
        with ThreadPoolExecutor(max_workers=12) as pool:
            outputs = list(pool.map(lambda _: run_hook(hook_case), range(12)))
        announcements = [json.loads(output)["hookSpecificOutput"]["additionalContext"]
                         for output in outputs if output]
        assert len(announcements) == 1
        assert announcements[0].startswith(prefix)
        assert (project / f"batch_state/context_monitor/{SESSION}.tier").read_text() == f"{tier} {tokens}\n"


def test_live_holder_never_stolen_and_killed_holder_recovered(hook_case):
    project, _, _ = hook_case
    holder = subprocess.Popen([
        sys.executable, "-c",
        "import importlib.util,sys; "
        "s=importlib.util.spec_from_file_location('state',sys.argv[1]); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "d=m.open_state_dir(sys.argv[2],create=True); "
        "lock=m.lock_session(d,sys.argv[3]+'.lock'); "
        "print('locked',flush=True); sys.stdin.read()",
        str(HELPER), str(project), SESSION,
    ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        assert holder.stdout.readline() == "locked\n"
        # A full hook waits only a bounded time, fails open, and cannot claim.
        assert run_hook(hook_case) == ""
        assert holder.poll() is None
        assert not (project / f"batch_state/context_monitor/{SESSION}.tier").exists()
        lock = project / f"batch_state/context_monitor/{SESSION}.lock"
        inode = lock.stat().st_ino
        holder.kill()
        holder.wait(timeout=5)
        assert run_hook(hook_case)
        assert lock.stat().st_ino == inode  # reuse the stale inode, never steal/unlink
        assert run_hook(hook_case) == ""
    finally:
        if holder.poll() is None:
            holder.kill()
        holder.communicate(timeout=5)


def test_random_temp_collision_refused_without_unlinking_link(state_module, tmp_path, monkeypatch):
    directory = state_module.open_state_dir(str(tmp_path), create=True)
    outside = tmp_path / "outside"
    outside.write_bytes(b"preserved")
    temporary = tmp_path / f"batch_state/context_monitor/.{SESSION}.tier.collision.tmp"
    temporary.symlink_to(outside)
    monkeypatch.setattr(state_module.secrets, "token_hex", lambda _: "collision")
    try:
        with pytest.raises(FileExistsError):
            state_module.replace_state(directory, f"{SESSION}.tier", 3, 760_000)
        assert temporary.is_symlink()
        assert outside.read_bytes() == b"preserved"
    finally:
        os.close(directory)


def test_atomic_replace_uses_same_directory_and_exclusive_random_temp(state_module, tmp_path, monkeypatch):
    directory = state_module.open_state_dir(str(tmp_path), create=True)
    original_open, original_replace = os.open, os.replace
    names = []

    def checked_open(name, flags, *args, **kwargs):
        if name.endswith(".tmp"):
            assert flags & os.O_EXCL and flags & os.O_NOFOLLOW
            assert kwargs["dir_fd"] == directory
            names.append(name)
        return original_open(name, flags, *args, **kwargs)

    def checked_replace(source, destination, **kwargs):
        assert kwargs == {"src_dir_fd": directory, "dst_dir_fd": directory}
        assert source in names
        return original_replace(source, destination, **kwargs)

    monkeypatch.setattr(state_module.os, "open", checked_open)
    monkeypatch.setattr(state_module.os, "replace", checked_replace)
    try:
        for tier in (1, 2):
            state_module.replace_state(directory, f"{SESSION}.tier", tier, 700_000)
        assert len(set(names)) == 2
        assert all(len(name.split(".")[-2]) == 32 for name in names)
        assert state_module.read_state(directory, f"{SESSION}.tier") == (2, 700_000)
        assert not list((tmp_path / "batch_state/context_monitor").glob("*.tmp"))
    finally:
        os.close(directory)


@pytest.mark.parametrize("name", [f"{SESSION}.tier", f"{SESSION}.lock"])
@pytest.mark.parametrize("kind", ["hardlink", "fifo", "directory"])
def test_nonregular_or_shared_inode_refused(state_module, tmp_path, name, kind):
    state = tmp_path / "batch_state/context_monitor"
    state.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_bytes(b"3 760000\n")
    if kind == "hardlink":
        os.link(outside, state / name)
    elif kind == "fifo":
        os.mkfifo(state / name)
    else:
        (state / name).mkdir()
    assert state_module.main(["claim", str(tmp_path), SESSION, "3", "760000"]) == 0
    assert outside.read_bytes() == b"3 760000\n"


@pytest.mark.parametrize("session", ["", "../outside", "a/b", "a..b", "a\x00b"])
def test_invalid_session_refused_before_any_write(state_module, tmp_path, session):
    assert state_module.main(["claim", str(tmp_path), session, "1", "655000"]) == 0
    assert not (tmp_path / "batch_state").exists()


@pytest.mark.parametrize("raw", [b"broken\n", b"4 760000\n", b"3 -1\n", b""])
def test_invalid_state_rearms_safely(state_module, tmp_path, raw, capsys):
    state = tmp_path / "batch_state/context_monitor"
    state.mkdir(parents=True)
    (state / f"{SESSION}.tier").write_bytes(raw)
    assert state_module.main(["claim", str(tmp_path), SESSION, "3", "760000"]) == 0
    assert capsys.readouterr().out == "claimed\n"
    assert (state / f"{SESSION}.tier").read_bytes() == b"3 760000\n"


def test_helper_unavailable_fails_open_without_announcement(hook_case):
    hook_case[1]["THREAD_ROLLOVER_PYTHON"] = "/unavailable/interpreter"
    assert run_hook(hook_case) == ""
    assert not (hook_case[0] / "batch_state").exists()


def test_missing_resolver_fails_open_without_path_python(hook_case):
    hook_case[1].pop("THREAD_ROLLOVER_PYTHON")
    assert run_hook(hook_case) == ""
    assert not (hook_case[0] / "batch_state").exists()


def test_invalid_worktree_metadata_refuses_interpreter(hook_case):
    project, env, _ = hook_case
    env.pop("THREAD_ROLLOVER_PYTHON")
    scripts = project / "scripts/lib"
    scripts.mkdir(parents=True)
    canonical = HOOKS.parents[2]
    (scripts / "project_interpreter.sh").symlink_to(canonical / "scripts/lib/project_interpreter.sh")
    # A fixture worktree with real Git metadata, pointing to this repository's
    # canonical shared interpreter; no worktree-local interpreter is created.
    (project / ".git").write_text(f"gitdir: {canonical / '.git'}\n")
    # Invalid metadata must fail closed, rather than select a planted Python.
    assert run_hook(hook_case) == ""
    assert not (project / ".venv").exists()


def test_rename_failure_cleans_temp_and_preserves_prior_state(state_module, tmp_path, monkeypatch):
    directory = state_module.open_state_dir(str(tmp_path), create=True)
    state = tmp_path / f"batch_state/context_monitor/{SESSION}.tier"
    state.write_bytes(b"1 655000\n")

    def fail_replace(*args, **kwargs):
        raise OSError("injected rename failure")

    monkeypatch.setattr(state_module.os, "replace", fail_replace)
    try:
        with pytest.raises(OSError, match="injected rename failure"):
            state_module.replace_state(directory, f"{SESSION}.tier", 2, 705_000)
        assert state.read_bytes() == b"1 655000\n"
        assert not list(state.parent.glob("*.tmp"))
    finally:
        os.close(directory)


def test_directory_redirect_between_mkdir_and_open_refused(state_module, tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    original_mkdir = os.mkdir

    def redirect(name, *args, **kwargs):
        original_mkdir(name, *args, **kwargs)
        if name == "context_monitor":
            parent = tmp_path / "batch_state"
            (parent / name).rename(parent / "original")
            (parent / name).symlink_to(outside, target_is_directory=True)

    monkeypatch.setattr(state_module.os, "mkdir", redirect)
    assert state_module.main(["claim", str(tmp_path), SESSION, "3", "760000"]) == 0
    assert list(outside.iterdir()) == []
    assert list((tmp_path / "batch_state/original").iterdir()) == []


def test_replaced_lock_name_refused(state_module, tmp_path, monkeypatch):
    directory = state_module.open_state_dir(str(tmp_path), create=True)
    lock = tmp_path / f"batch_state/context_monitor/{SESSION}.lock"
    original_flock = state_module.fcntl.flock

    def replace_lock(fd, operation):
        original_flock(fd, operation)
        lock.rename(lock.with_suffix(".old"))
        lock.touch()

    monkeypatch.setattr(state_module.fcntl, "flock", replace_lock)
    try:
        with pytest.raises(ValueError, match="lock name changed"):
            state_module.lock_session(directory, lock.name)
    finally:
        os.close(directory)
