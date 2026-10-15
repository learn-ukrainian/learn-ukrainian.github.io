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
_CODEX_MODEL = "gpt-6.1-sol"


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


def _dispatch_worktree(primary: Path, task_id: str, agent: str = "agy") -> Path:
    worktree, _, _ = delegate._ensure_worktree(
        agent=agent,
        task_id=task_id,
        raw_path=str(primary / ".worktrees" / "dispatch" / agent / task_id),
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
    agent: str = "agy",
) -> tuple[int, dict, list[dict]]:
    """Run the real worker; substitute only the provider process behind the adapter.

    Each provider start records what the provider found: the hook bytes and
    their validation (AGY only), the baseline sidecar keys and the Git status
    around the tool calls.
    """
    model_id = _MODEL if agent == "agy" else _CODEX_MODEL
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {"task_id": task_id, "cwd": str(worktree), "mode": mode, "model": model_id, "cli_version": "fixture"},
    )
    launches: list[dict] = []

    def provider(provider_agent, prompt, *, mode, cwd, model, task_id, tool_config, **_kwargs):
        assert provider_agent == agent
        if agent == "agy":
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
            "hook_bytes": hook.read_bytes() if agent == "agy" and hook.exists() else None,
            "hook_check": hooks.check_hook_config(hooks.hook_locations(cwd, Path.home())) if agent == "agy" else None,
            "baseline_paths": (
                sorted(json.loads(pre_sidecar.read_text(encoding="utf-8"))) if pre_sidecar.exists() else None
            ),
            "status_before": _status(cwd),
        }
        subprocess.run([sys.executable, "-c", provider_script], cwd=cwd, check=True, timeout=60)
        launch["status_after"] = _status(cwd)
        if agent == "agy":
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
                "model": model_id,
                "effort": "high",
                "cli_version": "fixture",
            },
        )()

    with patch("agent_runtime.runner.invoke", side_effect=provider):
        rc = delegate._run_worker(
            task_id=task_id,
            agent=agent,
            prompt="Read scripts/f.txt and report its first line; do not edit the tree.",
            mode=mode,
            cwd_str=str(worktree),
            model=model_id,
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
    """Absent stays absent; content, link texts, target and file type are each recorded."""
    import stat

    directory = {"file_type": stat.S_IFDIR}
    regular = {"file_type": stat.S_IFREG}
    empty_sha = "ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356"
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").write_text("not a directory\n", encoding="utf-8")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").unlink()
    (tmp_path / ".agents").mkdir()
    hook = tmp_path / HOOK
    hook.write_bytes(b"{}\n")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        {"parent": directory, "hook": regular, "target": {"path": str(hook), **regular}, "sha256": empty_sha},
        None,
    )
    hook.unlink()
    hook.symlink_to("elsewhere.json")
    link = {"file_type": stat.S_IFLNK, "link_text": "elsewhere.json"}
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        {"parent": directory, "hook": link, "target": None, "sha256": None},
        None,
    )
    (tmp_path / ".agents" / "elsewhere.json").write_bytes(b"{}\n")
    target = {"path": str(tmp_path / ".agents" / "elsewhere.json"), **regular}
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        {"parent": directory, "hook": link, "target": target, "sha256": empty_sha},
        None,
    )
    hook.unlink()
    os.mkfifo(hook)
    fifo = {"file_type": stat.S_IFIFO}
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        {"parent": directory, "hook": fifo, "target": {"path": str(hook), **fifo}, "sha256": None},
        None,
    )
    hook.unlink()
    hook.symlink_to("hooks.json")  # A loop the adapter cannot load either; never opened.
    fingerprint, error = delegate._read_only_agy_hook_fingerprint(tmp_path)
    assert error is None
    assert fingerprint["hook"] == {"file_type": stat.S_IFLNK, "link_text": "hooks.json"}
    assert fingerprint["sha256"] is None


def test_hook_behind_a_looping_parent_is_an_error_not_absence(tmp_path):
    """Only a missing hook is absent; a parent the kernel cannot traverse fails acquisition."""
    (tmp_path / ".agents").symlink_to(".agents")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        None,
        f"agy hook snapshot failed: {HOOK}: OSError",
    )


def test_hook_lost_between_observations_is_an_error_not_absence(tmp_path, monkeypatch):
    """A regular hook gone at the target lstat, after the first lstat, fails acquisition."""
    (tmp_path / ".agents").mkdir()
    hook = tmp_path / HOOK
    hook.write_bytes(b"{}\n")
    original_lstat = os.lstat

    def lost(path, *args, **kwargs):
        if os.fspath(path) == str(hook):
            raise FileNotFoundError(path)
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", lost)
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == (
        None,
        f"agy hook snapshot failed: {HOOK}: FileNotFoundError",
    )


def test_hook_replaced_while_it_is_read_is_an_error(tmp_path, monkeypatch):
    """The hashed descriptor must be the observed target, and the links must not move meanwhile."""
    (tmp_path / ".agents").mkdir()
    hook = tmp_path / HOOK
    hook.write_bytes(b"{}\n")
    original_open = os.open

    def replaced(path, flags, *args, **kwargs):
        if os.fspath(path) == str(hook):
            os.replace(tmp_path / "replacement.json", hook)
        return original_open(path, flags, *args, **kwargs)

    (tmp_path / "replacement.json").write_bytes(b"{}\n")
    monkeypatch.setattr(os, "open", replaced)
    changed = (None, f"agy hook snapshot failed: {HOOK}: changed during snapshot")
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == changed

    monkeypatch.setattr(os, "open", original_open)
    hook.unlink()
    (tmp_path / "a.json").write_bytes(b"{}\n")
    (tmp_path / "b.json").write_bytes(b"{}\n")
    hook.symlink_to("../a.json")
    original_digest = delegate._read_only_agy_hook_digest

    def retarget_after_read(identity, inode):
        digest = original_digest(identity, inode)
        hook.unlink()
        hook.symlink_to("../b.json")
        return digest

    monkeypatch.setattr(delegate, "_read_only_agy_hook_digest", retarget_after_read)
    assert delegate._read_only_agy_hook_fingerprint(tmp_path) == changed


def test_early_provisioning_never_writes_outside_a_dispatch_worktree(primary):
    """The primary checkout is left to the adapter's refusal; nothing is created there."""
    delegate._provision_agy_read_only_guard(primary)
    assert not (primary / ".agents").exists()


# --- Accepted link layouts and acquisition races (#10727 review F1/F2) -------
#
# The adapter accepts a symlinked final hook and a symlinked ``.agents``
# parent, and it validates the bytes they lead to. Those layouts stay
# eligible, but a change the adapter would see through them is a mutation.
# A hook that was observed and then lost while the snapshot reads it is an
# acquisition failure, never an absent hook. The races below are real: the
# fixture moves files around the snapshot's own system calls, so the kernel
# returns the genuine error; only snapshot calls are intercepted.

_GUARD_BYTES = (json.dumps(_framework_hook(), indent=2) + "\n").encode("utf-8")


def _guard_dir(worktree: Path, name: str) -> Path:
    directory = worktree / "batch_state" / name
    directory.mkdir(parents=True)
    (directory / "hooks.json").write_bytes(_GUARD_BYTES)
    return directory


def _final_link_layout(worktree: Path) -> Path:
    """``.agents/hooks.json`` is a symlink to an ignored file holding a valid guard."""
    target = worktree / "batch_state" / "effective-hooks.json"
    target.parent.mkdir(parents=True)
    target.write_bytes(_GUARD_BYTES)
    (worktree / ".agents").mkdir()
    (worktree / HOOK).symlink_to("../batch_state/effective-hooks.json")
    return target


def _parent_link_layout(worktree: Path) -> None:
    """``.agents`` is a symlink to an ignored directory holding a valid guard."""
    _guard_dir(worktree, "guard-a")
    _guard_dir(worktree, "guard-b")
    (worktree / ".agents").symlink_to("batch_state/guard-a")


def _chained_parent_link_layout(worktree: Path) -> None:
    """``.agents`` -> ``batch_state/current`` -> ``guard-a``; the middle link is the moving part."""
    _guard_dir(worktree, "guard-a")
    _guard_dir(worktree, "guard-b")
    (worktree / "batch_state" / "current").symlink_to("guard-a")
    (worktree / ".agents").symlink_to("batch_state/current")


_REWRITE_LINK_TARGET = """
import json
path = "batch_state/effective-hooks.json"
data = json.load(open(path, encoding="utf-8"))
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=4)
"""
_RETARGET_PARENT = "import os\nos.remove('.agents')\nos.symlink('batch_state/guard-b', '.agents')\n"
_RETARGET_CHAIN = "import os\nos.remove('batch_state/current')\nos.symlink('guard-b', 'batch_state/current')\n"
_RETARGET_FINAL = "import os\nos.remove('.agents/hooks.json')\nos.symlink('../batch_state/guard-b/hooks.json', '.agents/hooks.json')\n"


def _assert_hook_mutation(rc: int, state: dict, launches: list[dict]) -> None:
    """The provider saw a valid guard before and after, Git status did not move, and the task failed."""
    assert len(launches) == 1
    launch = launches[0]
    assert launch["hook_check"].passed
    assert launch["hook_check_after"].passed
    assert launch["status_before"] == launch["status_after"]
    assert state["read_only_mutation_paths"] == [HOOK]
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_mutation, count 1"
    assert rc == 1


def test_symlinked_hook_target_rewrite_fails(primary, tmp_tasks_dir, fake_agy):
    """H1 (F1): the adapter validates the link target's bytes, so their rewrite is a mutation."""
    task_id = "ro-10727-h1-final-link"
    worktree = _dispatch_worktree(primary, task_id)
    target = _final_link_layout(worktree)

    rc, state, launches = _launch(worktree, task_id, _REWRITE_LINK_TARGET)

    assert target.read_bytes() != _GUARD_BYTES
    assert json.loads(target.read_bytes()) == json.loads(_GUARD_BYTES)
    _assert_hook_mutation(rc, state, launches)


def test_symlinked_parent_retarget_between_identical_guards_fails(primary, tmp_tasks_dir, fake_agy):
    """H2 (F1): retargeting ``.agents`` swaps the hook the adapter loads, even with equal bytes."""
    task_id = "ro-10727-h2-parent-link"
    worktree = _dispatch_worktree(primary, task_id)
    _parent_link_layout(worktree)

    rc, state, launches = _launch(worktree, task_id, _RETARGET_PARENT)

    assert os.readlink(worktree / ".agents") == "batch_state/guard-b"
    _assert_hook_mutation(rc, state, launches)


def test_retargeted_middle_link_of_the_parent_chain_fails(primary, tmp_tasks_dir, fake_agy):
    """H2 sibling (F1): the ``.agents`` link text is unchanged; the link it leads through moved."""
    task_id = "ro-10727-h2-chain-link"
    worktree = _dispatch_worktree(primary, task_id)
    _chained_parent_link_layout(worktree)

    rc, state, launches = _launch(worktree, task_id, _RETARGET_CHAIN)

    assert os.readlink(worktree / ".agents") == "batch_state/current"
    _assert_hook_mutation(rc, state, launches)


def test_retargeted_final_link_between_identical_guards_fails(primary, tmp_tasks_dir, fake_agy):
    """F1 sibling: the final link's own retarget stays detected."""
    task_id = "ro-10727-final-retarget"
    worktree = _dispatch_worktree(primary, task_id)
    _final_link_layout(worktree)
    _guard_dir(worktree, "guard-b")

    rc, state, launches = _launch(worktree, task_id, _RETARGET_FINAL)

    _assert_hook_mutation(rc, state, launches)


@pytest.mark.parametrize("layout", [_final_link_layout, _parent_link_layout, _chained_parent_link_layout])
def test_untouched_accepted_link_layouts_still_settle_done(primary, tmp_tasks_dir, fake_agy, layout):
    """F1 control: link layouts the adapter accepts are not a new eligibility restriction."""
    task_id = f"ro-10727-layout-{layout.__name__.strip('_')}"
    worktree = _dispatch_worktree(primary, task_id)
    layout(worktree)

    rc, state, launches = _launch(worktree, task_id, _READ)

    assert len(launches) == 1
    assert launches[0]["hook_check"] == hooks.HookConfigResult("PASS", "guard_registered")
    assert HOOK in launches[0]["baseline_paths"]
    assert state["read_only_checkout_snapshot_error"] is None
    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "done"
    assert state["last_error"] is None
    assert rc == 0


def _race_snapshot_call(monkeypatch, worktree: Path, name: str, matches: set[str], lose, restore) -> list[int]:
    """Make ``os.<name>`` on a hook path lose the hook for the call itself, then restore it.

    Only calls made while the read-only checkout snapshot runs are raced, so
    the adapter and provider still see the restored, valid layout. Returns the
    errno each raced call genuinely raised.
    """
    original = getattr(os, name)
    original_snapshot = delegate._read_only_checkout_snapshot
    active: list[bool] = []
    raised: list[int] = []

    def snapshot(cwd, **options):
        active.append(True)
        try:
            return original_snapshot(cwd, **options)
        finally:
            active.pop()

    def raced(path, *args, **kwargs):
        if not active or not active[-1] or os.fspath(path) not in matches:
            return original(path, *args, **kwargs)
        active.append(False)  # The fixture's own calls below are never raced.
        try:
            saved = lose()
            try:
                return original(path, *args, **kwargs)
            except OSError as exc:
                raised.append(exc.errno)
                raise
            finally:
                restore(saved)
        finally:
            active.pop()

    monkeypatch.setattr(delegate, "_read_only_checkout_snapshot", snapshot)
    monkeypatch.setattr(os, name, raced)
    return raised


def _assert_acquisition_failed(rc: int, state: dict, launches: list[dict], raised: list[int], errno_value: int) -> None:
    """The fixture produced a real error, the provider still saw a valid guard, and the task failed closed."""
    assert raised and set(raised) == {errno_value}
    assert len(launches) == 1
    assert launches[0]["hook_check"].passed
    assert state["read_only_checkout_snapshot_error"].startswith(f"agy hook snapshot failed: {HOOK}: ")
    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_snapshot_failed"
    assert rc == 1


def test_regular_hook_lost_around_open_fails_closed(primary, tmp_tasks_dir, fake_agy, monkeypatch):
    """H3 (F2): ENOENT after a successful lstat is a lost hook, not an absent one."""
    import errno

    task_id = "ro-10727-h3-open-race"
    worktree = _dispatch_worktree(primary, task_id)
    hooks.install_worktree_guard(worktree)
    hook = worktree / HOOK
    away = worktree / "batch_state" / "hooks.away"
    away.parent.mkdir()

    raised = _race_snapshot_call(
        monkeypatch,
        worktree,
        "open",
        {str(hook), os.path.realpath(hook)},
        lose=lambda: os.rename(hook, away),
        restore=lambda _saved: os.rename(away, hook),
    )
    rc, state, launches = _launch(worktree, task_id, _READ)

    _assert_acquisition_failed(rc, state, launches, raised, errno.ENOENT)
    assert hook.read_bytes() == launches[0]["hook_bytes"]


def test_parent_replaced_by_a_file_around_open_fails_closed(primary, tmp_tasks_dir, fake_agy, monkeypatch):
    """H3b (F2): ENOTDIR after a successful lstat is a lost hook, not an absent one."""
    import errno

    task_id = "ro-10727-h3b-parent-race"
    worktree = _dispatch_worktree(primary, task_id)
    hooks.install_worktree_guard(worktree)
    hook = worktree / HOOK
    parent = worktree / ".agents"
    away = worktree / "batch_state" / "agents.away"
    away.parent.mkdir()

    def lose():
        os.rename(parent, away)
        parent.write_text("not a directory\n", encoding="utf-8")

    def restore(_saved):
        parent.unlink()
        os.rename(away, parent)

    raised = _race_snapshot_call(
        monkeypatch, worktree, "open", {str(hook), os.path.realpath(hook)}, lose=lose, restore=restore
    )
    rc, state, launches = _launch(worktree, task_id, _READ)

    _assert_acquisition_failed(rc, state, launches, raised, errno.ENOTDIR)


def test_final_link_lost_around_readlink_fails_closed(primary, tmp_tasks_dir, fake_agy, monkeypatch):
    """H3c (F2): a symlinked hook that vanishes under readlink is lost, not absent."""
    import errno

    task_id = "ro-10727-h3c-readlink-race"
    worktree = _dispatch_worktree(primary, task_id)
    _final_link_layout(worktree)
    hook = worktree / HOOK

    def lose():
        text = os.readlink(hook)
        hook.unlink()
        return text

    raised = _race_snapshot_call(
        monkeypatch, worktree, "readlink", {str(hook)}, lose=lose, restore=lambda text: hook.symlink_to(text)
    )
    rc, state, launches = _launch(worktree, task_id, _READ)

    _assert_acquisition_failed(rc, state, launches, raised, errno.ENOENT)
    assert os.readlink(hook) == "../batch_state/effective-hooks.json"


def test_parent_link_lost_around_readlink_fails_closed(primary, tmp_tasks_dir, fake_agy, monkeypatch):
    """F2 sibling: a symlinked ``.agents`` that vanishes under readlink is lost, not absent."""
    import errno

    task_id = "ro-10727-parent-readlink-race"
    worktree = _dispatch_worktree(primary, task_id)
    _parent_link_layout(worktree)
    parent = worktree / ".agents"

    def lose():
        text = os.readlink(parent)
        parent.unlink()
        return text

    raised = _race_snapshot_call(
        monkeypatch, worktree, "readlink", {str(parent)}, lose=lose, restore=lambda text: parent.symlink_to(text)
    )
    rc, state, launches = _launch(worktree, task_id, _READ)

    _assert_acquisition_failed(rc, state, launches, raised, errno.ENOENT)


# --- Agent scope of the hook acquisition (#10727 review F3) ------------------
#
# Only AGY executes the workspace guard, so only an AGY read-only worker
# acquires it and fails closed when it cannot. Another agent keeps the base
# snapshot: a static, ignored ``.agents`` loop is no evidence it lacks, while
# its Git-status, database-link and task-record checks still run.


def _hook_parent_loop(worktree: Path) -> None:
    """``.agents`` -> ``.agents``: the kernel refuses to traverse it (ELOOP)."""
    import errno

    (worktree / ".agents").symlink_to(".agents")
    with pytest.raises(OSError) as loop:
        (worktree / HOOK).lstat()
    assert loop.value.errno == errno.ELOOP


def test_non_agy_read_only_worker_ignores_a_static_hook_loop(primary, tmp_tasks_dir):
    """F3: a Codex worker beside a static ignored hook-parent loop settles ``done`` as on base."""
    task_id = "ro-10727-codex-loop"
    worktree = _dispatch_worktree(primary, task_id, agent="codex")
    _hook_parent_loop(worktree)

    rc, state, launches = _launch(worktree, task_id, _READ, agent="codex")

    assert len(launches) == 1
    assert launches[0]["status_before"] == launches[0]["status_after"]
    assert HOOK not in launches[0]["baseline_paths"]
    assert state["read_only_checkout_snapshot_error"] is None
    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "done"
    assert state["last_error"] is None
    assert rc == 0
    assert os.readlink(worktree / ".agents") == ".agents"


def test_non_agy_read_only_worker_still_fails_on_a_checkout_mutation(primary, tmp_tasks_dir):
    """F3 control: the loop is ignored, the Codex worker's tracked-file write is not."""
    task_id = "ro-10727-codex-loop-write"
    worktree = _dispatch_worktree(primary, task_id, agent="codex")
    _hook_parent_loop(worktree)

    rc, state, launches = _launch(worktree, task_id, _EDIT_TRACKED, agent="codex")

    assert len(launches) == 1
    assert state["read_only_checkout_snapshot_error"] is None
    assert state["read_only_mutation_paths"] == ["scripts/f.txt"]
    assert state["status"] == "failed"
    assert state["last_error"] == "read_only_checkout_mutation, count 1"
    assert rc == 1


def test_agy_read_only_worker_still_fails_closed_on_the_same_loop(primary, tmp_tasks_dir, fake_agy):
    """F3 control: for AGY the unreadable guard is withheld evidence, never a clean checkout."""
    task_id = "ro-10727-agy-loop"
    worktree = _dispatch_worktree(primary, task_id)
    _hook_parent_loop(worktree)

    rc, state, _launches = _launch(worktree, task_id, _READ)

    assert state["read_only_checkout_snapshot_error"] == f"agy hook snapshot failed: {HOOK}: OSError"
    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "failed"
    assert rc == 1
    assert os.readlink(worktree / ".agents") == ".agents"


def test_checkout_snapshot_acquires_the_hook_only_when_asked(tmp_path):
    """The shared helper keeps its base call contract; the AGY worker opts in to the hook."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".gitignore").write_text(".agents/\n", encoding="utf-8")
    (repo / ".agents").mkdir()
    (repo / HOOK).write_bytes(b"{}\n")

    base, error = delegate._read_only_checkout_snapshot(repo)
    assert error is None
    assert base[HOOK] == "!!"
    with_hook, error = delegate._read_only_checkout_snapshot(repo, agy_hook=True)
    assert error is None
    assert with_hook[HOOK].startswith("!!:")
    assert json.loads(with_hook[HOOK][3:])["sha256"] is not None

    (repo / ".agents" / "hooks.json").unlink()
    (repo / ".agents").rmdir()
    _hook_parent_loop(repo)
    assert delegate._read_only_checkout_snapshot(repo)[1] is None
    assert delegate._read_only_checkout_snapshot(repo, agy_hook=True) == (
        None,
        f"agy hook snapshot failed: {HOOK}: OSError",
    )
