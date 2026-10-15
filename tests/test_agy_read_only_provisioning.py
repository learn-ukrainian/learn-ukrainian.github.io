"""Fresh read-only AGY launches provision the guard before the baseline (#10727).

The AGY adapter installs the missing ``.agents/hooks.json`` guard while it
builds the invocation, which used to happen after the read-only pre-snapshot,
so every fresh read-only dispatch failed with its own harness write counted as
a provider mutation. The worker now completes that framework provisioning
before the immutable baseline, and the snapshot fingerprints the hook bytes so
a valid-to-valid rewrite that keeps the ignored Git status still fails.

The seven lifecycle cases drive the real worker in a real linked dispatch
worktree of a throwaway repository: the real worktree creation, the real
pre/post snapshots and the real ``AgyAdapter.build_invocation`` provisioning
and validation boundary. Only the external provider process is substituted:
a fake ``agy`` binary answers the version probe, and a Python script stands in
for the model's tool calls in the worktree. No network, ``origin`` or provider
call is needed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate
from agent_runtime.adapters import agy as agy_module
from agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime import agy_hook_config as hooks

HOOK = ".agents/hooks.json"
_MODEL = "gemini-3.1-pro-high"


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PRE_COMMIT"))}


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env=_clean_env(),
        timeout=30,
    )
    return proc.stdout.strip()


def _status(worktree: Path) -> str:
    return _git(worktree, "status", "--porcelain=v1", "--ignored", "--untracked-files=all")


def _framework_hook() -> dict:
    """What the installer writes into an absent workspace file."""
    return {hooks.GUARD_NAME: hooks.guard_registration()}


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    return tasks_dir


@pytest.fixture
def primary(tmp_path, monkeypatch) -> Path:
    """A primary checkout that ignores ``.agents/`` like the real repository."""
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("AGENT_NO_MERGE", raising=False)
    # An ordinary HOME with no AGY hooks file: the workspace file is the only candidate.
    monkeypatch.setenv("HOME", str(tmp_path / "ordinary-home"))
    repo = (tmp_path / "primary").resolve()
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / ".gitignore").write_text(".agents/\n.worktrees/\nbatch_state/\n", encoding="utf-8")
    for relative in ("data/projects/f.txt", "data/lexicon/f.txt", "data/datasets/f.txt", "scripts/f.txt"):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{relative}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "fixture")
    monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
    return repo


@pytest.fixture
def fake_agy(tmp_path, monkeypatch) -> Path:
    """The provider binary: answers ``--version`` with a supported build, nothing else."""
    fake = tmp_path / "provider-bin" / "agy"
    fake.parent.mkdir()
    fake.write_text("#!/bin/sh\nprintf '%s\\n' '2.0.0'\n", encoding="utf-8")
    fake.chmod(0o755)
    original_which = agy_module.shutil.which
    monkeypatch.setattr(
        agy_module.shutil,
        "which",
        lambda name, *args, **kwargs: str(fake) if name == "agy" else original_which(name, *args, **kwargs),
    )
    agy_module._agy_version.cache_clear()
    yield fake
    agy_module._agy_version.cache_clear()


def _dispatch_worktree(primary: Path, task_id: str) -> Path:
    worktree, _, _ = delegate._ensure_worktree(
        agent="agy",
        task_id=task_id,
        raw_path=str(primary / ".worktrees" / "dispatch" / "agy" / task_id),
        resolved_base_sha=_git(primary, "rev-parse", "HEAD"),
        detached=True,
    )
    assert worktree.resolve().is_relative_to((primary / ".worktrees" / "dispatch").resolve())
    assert (worktree / ".git").is_file()
    return worktree


def _launch(
    worktree: Path,
    task_id: str,
    provider_script: str,
    *,
    mode: str = "read-only",
    provider_ok: bool = True,
) -> tuple[int, dict, list[dict]]:
    """Run the real worker; substitute only the AGY process behind the adapter.

    Each provider start records what the provider found: the hook bytes and
    their validation, the baseline sidecar keys and the Git status around the
    tool calls.
    """
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(worktree), "mode": mode, "model": _MODEL, "cli_version": "fixture"},
    )
    launches: list[dict] = []

    def provider(agent, prompt, *, mode, cwd, model, task_id, tool_config, **_kwargs):
        assert agent == "agy"
        # The real provider-time boundary: model resolution, hook provisioning and validation.
        AgyAdapter().build_invocation(
            prompt=prompt,
            mode=mode,
            cwd=cwd,
            model=model,
            task_id=task_id,
            session_id=None,
            tool_config=tool_config,
        )
        hook = cwd / HOOK
        pre_sidecar = delegate._read_only_snapshot_sidecar_path(task_id, "pre")
        launch = {
            "hook_bytes": hook.read_bytes() if hook.exists() else None,
            "hook_check": hooks.check_hook_config(hooks.hook_locations(cwd, Path.home())),
            "baseline_paths": (
                sorted(json.loads(pre_sidecar.read_text(encoding="utf-8"))) if pre_sidecar.exists() else None
            ),
            "status_before": _status(cwd),
        }
        subprocess.run([sys.executable, "-c", provider_script], cwd=cwd, check=True, timeout=60)
        launch["status_after"] = _status(cwd)
        launch["hook_check_after"] = hooks.check_hook_config(hooks.hook_locations(cwd, Path.home()))
        launches.append(launch)
        return type(
            "_Result",
            (),
            {
                "ok": provider_ok,
                "response": "VERDICT: PASS" if provider_ok else "",
                "stderr_excerpt": None if provider_ok else "provider fixture exited 1",
                "returncode": 0 if provider_ok else 1,
                "rate_limited": False,
                "model": _MODEL,
                "effort": "high",
                "cli_version": "fixture",
            },
        )()

    with patch("agent_runtime.runner.invoke", side_effect=provider):
        rc = delegate._run_worker(
            task_id=task_id,
            agent="agy",
            prompt="Read scripts/f.txt and report its first line; do not edit the tree.",
            mode=mode,
            cwd_str=str(worktree),
            model=_MODEL,
            hard_timeout=60,
        )
    state = delegate._read_state(state_path)
    assert state is not None
    return rc, state, launches


_READ = "open('scripts/f.txt', encoding='utf-8').read()\n"
# Valid to valid: the guard stays registered, only the bytes change.
_REWRITE_HOOK = f"""
import json
path = {HOOK!r}
data = json.load(open(path, encoding="utf-8"))
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=4)
"""
_EDIT_TRACKED = "open('scripts/f.txt', 'a', encoding='utf-8').write('provider edit\\n')\n"


# --- The seven lifecycle cases (#10727 denominator) -------------------------


def test_fresh_read_only_launch_has_guard_in_baseline_and_settles_done(primary, tmp_tasks_dir, fake_agy):
    """Case 1 (AC-01): a fresh read-only launch is not failed by the framework's own guard."""
    task_id = "ro-10727-fresh-success"
    worktree = _dispatch_worktree(primary, task_id)
    assert not (worktree / HOOK).exists()

    rc, state, launches = _launch(worktree, task_id, _READ)

    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "done"
    assert len(launches) == 1
    launch = launches[0]
    assert HOOK in launch["baseline_paths"]
    assert launch["hook_check"] == hooks.HookConfigResult("PASS", "guard_registered")
    assert json.loads(launch["hook_bytes"]) == _framework_hook()
    assert (worktree / HOOK).read_bytes() == launch["hook_bytes"]
    assert state["last_error"] is None
    assert rc == 0
    assert _git(worktree, "status", "--porcelain") == ""


def test_fresh_read_only_provider_failure_is_not_blamed_on_the_guard(primary, tmp_tasks_dir, fake_agy):
    """Case 2 (AC-01): a failed provider keeps its own failure, with no false mutation."""
    task_id = "ro-10727-fresh-failure"
    worktree = _dispatch_worktree(primary, task_id)

    rc, state, launches = _launch(worktree, task_id, _READ, provider_ok=False)

    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "failed"
    assert len(launches) == 1
    assert HOOK in launches[0]["baseline_paths"]
    assert launches[0]["hook_check"].passed
    assert "read_only_checkout_mutation" not in (state["last_error"] or "")
    assert rc == 1
    assert _git(worktree, "status", "--porcelain") == ""


def test_repeated_read_only_launch_keeps_one_stable_guard(primary, tmp_tasks_dir, fake_agy):
    """Case 3 (AC-01): reusing the worktree neither rewrites the guard nor reports it."""
    worktree = _dispatch_worktree(primary, "ro-10727-repeat")
    results = [_launch(worktree, task_id, _READ) for task_id in ("ro-10727-repeat", "ro-10727-repeat-2")]

    first_bytes = results[0][2][0]["hook_bytes"]
    for rc, state, launches in results:
        assert state["read_only_mutation_paths"] == []
        assert state["status"] == "done"
        assert rc == 0
        assert launches[0]["hook_bytes"] == first_bytes
        assert HOOK in launches[0]["baseline_paths"]
    assert json.loads(first_bytes) == _framework_hook()
    assert (worktree / HOOK).read_bytes() == first_bytes
    assert _git(worktree, "status", "--porcelain") == ""


def test_valid_hook_rewrite_with_unchanged_ignored_status_still_fails(primary, tmp_tasks_dir, fake_agy):
    """Case 4 (AC-02): Git status cannot see this rewrite; the hook fingerprint does."""
    task_id = "ro-10727-hook-rewrite"
    worktree = _dispatch_worktree(primary, task_id)
    hooks.install_worktree_guard(worktree)  # An earlier dispatch already provisioned this worktree.
    before = (worktree / HOOK).read_bytes()

    rc, state, launches = _launch(worktree, task_id, _REWRITE_HOOK)

    launch = launches[0]
    assert launch["hook_bytes"] == before
    assert (worktree / HOOK).read_bytes() != before
    assert json.loads((worktree / HOOK).read_bytes()) == json.loads(before)
    assert launch["hook_check_after"].passed
    assert launch["status_before"] == launch["status_after"]
    assert f"!! {HOOK}" in launch["status_after"].splitlines()
    assert state["read_only_mutation_paths"] == [HOOK]
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_mutation, count 1"
    assert rc == 1


def test_invalid_pre_existing_hook_is_refused_not_repaired(primary, tmp_tasks_dir, fake_agy):
    """Case 5 (AC-02): early provisioning never merges a guard into an existing file."""
    task_id = "ro-10727-invalid-hook"
    worktree = _dispatch_worktree(primary, task_id)
    original = b'{"unrelated-hook": {"Stop": []}}\n'
    (worktree / ".agents").mkdir()
    (worktree / HOOK).write_bytes(original)

    rc, state, launches = _launch(worktree, task_id, _READ)

    assert launches == []
    assert (worktree / HOOK).read_bytes() == original
    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "failed"
    assert "agy_hook_config_refused: missing_guard" in state["stderr_excerpt"]
    assert rc == 1


def test_unrelated_provider_mutation_still_fails_alone(primary, tmp_tasks_dir, fake_agy):
    """Case 6 (AC-02): a real checkout write is named, and the guard is not."""
    task_id = "ro-10727-unrelated-write"
    worktree = _dispatch_worktree(primary, task_id)

    rc, state, launches = _launch(worktree, task_id, _EDIT_TRACKED)

    assert launches[0]["hook_check"].passed
    assert state["read_only_mutation_paths"] == ["scripts/f.txt"]
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_mutation, count 1"
    assert rc == 1


def test_workspace_write_launch_still_gets_valid_guard_wiring(primary, tmp_tasks_dir, fake_agy):
    """Case 7 (AC-02): write mode keeps provider-time installation and validation."""
    task_id = "rw-10727-wiring"
    worktree = _dispatch_worktree(primary, task_id)
    assert not (worktree / HOOK).exists()

    _rc, state, launches = _launch(worktree, task_id, _READ, mode="workspace-write")

    assert len(launches) == 1
    assert launches[0]["hook_check"] == hooks.HookConfigResult("PASS", "guard_registered")
    assert json.loads(launches[0]["hook_bytes"]) == _framework_hook()
    assert launches[0]["baseline_paths"] is None
    assert "read_only_mutation_paths" not in state or not state["read_only_mutation_paths"]


# --- Supporting coverage, outside the seven-case denominator -----------------


def test_unreadable_hook_fails_closed_instead_of_settling_done(primary, tmp_tasks_dir, fake_agy, monkeypatch):
    """A guard file the snapshot cannot read is missing evidence, never a clean checkout."""
    task_id = "ro-10727-unreadable-hook"
    worktree = _dispatch_worktree(primary, task_id)
    hooks.install_worktree_guard(worktree)
    hook = str(worktree / HOOK)
    original_open = os.open

    def unreadable(path, flags, *args, **kwargs):
        if path == Path(hook):
            raise PermissionError("fixture hook unreadable")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", unreadable)
    rc, state, launches = _launch(worktree, task_id, _READ)

    assert len(launches) == 1
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_checkout_snapshot_error"] == f"agy hook snapshot failed: {HOOK}: PermissionError"
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_snapshot_failed"
    assert rc == 1


def test_hook_fingerprint_distinguishes_bytes_links_and_file_types(tmp_path):
    """Absent stays absent; content, link text and file type are each recorded."""
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").write_text("not a directory\n", encoding="utf-8")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").unlink()
    (tmp_path / ".agents").mkdir()
    hook = tmp_path / HOOK
    hook.write_bytes(b"{}\n")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        {"sha256": "ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356"},
        None,
    )
    hook.unlink()
    hook.symlink_to("elsewhere.json")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == ({"link_text": "elsewhere.json"}, None)
    hook.unlink()
    os.mkfifo(hook)
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == ({"file_type": 0o010000}, None)


def test_early_provisioning_never_writes_outside_a_dispatch_worktree(primary):
    """The primary checkout is left to the adapter's refusal; nothing is created there."""
    delegate._provision_agy_read_only_guard(primary)
    assert not (primary / ".agents").exists()
