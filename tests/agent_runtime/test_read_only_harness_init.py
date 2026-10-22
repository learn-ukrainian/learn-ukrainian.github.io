"""OpenCode initialization must precede, never bypass, the checkout guard (#11347)."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import delegate

_DEPENDENCY = ".opencode/node_modules/example/index.js"
_PLUGIN = ".opencode/plugins/example.js"
_ROUTES = ("deepseek-v4.1-flash", "openrouter/deepseek/deepseek-v4.1-flash")
_FAKE_OPENCODE = r"""
import json
import os
import sys
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    print("1.19.3")
    raise SystemExit(0)
initializing = sys.argv[1:3] == ["debug", "config"]
with open(os.environ["LU_HARNESS_INIT_LOG"], "a") as log:
    log.write("init\n" if initializing else "run\n")
Path("../init-env.json" if initializing else "../run-env.json").write_text(json.dumps({
        "secrets_present": [name for name in (
            "FAKE_SECRET_TOKEN", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"
        ) if name in os.environ],
        "LANG": os.environ.get("LANG"),
        "output_token_max": os.environ.get("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX"),
    }))
if initializing and os.environ.get("LU_HARNESS_INIT_FAILURE") == "exit":
    print("private diagnostic must not escape", file=sys.stderr)
    raise SystemExit(7)
if initializing and os.environ.get("LU_HARNESS_INIT_FAILURE") == "warning":
    print("WARN background dependency install failed private diagnostic", file=sys.stderr)
    raise SystemExit(0)
for name, content in {
    ".opencode/.gitignore": "node_modules\n.gitignore\n",
    ".opencode/node_modules/example/index.js": "original dependency\n",
}.items():
    path = Path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)
print("configuration output must not escape" if initializing else "OK")
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    """Use a private repository and executable, never the host harness or provider."""
    from scripts.agent_runtime.adapters.glm import _CI_ENV_VARS

    # The fake CLI has no provider egress; exercise initialization in CI too.
    for key in _CI_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    (repo / ".gitignore").write_text("batch_state/\n")
    plugin = repo / _PLUGIN
    plugin.parent.mkdir(parents=True)
    plugin.write_text("original plugin\n")
    (repo / "tracked.txt").write_text("original\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "fixture", "--no-gpg-sign")
    script = tmp_path / "fake_opencode.py"
    script.write_text(_FAKE_OPENCODE)
    binary = tmp_path / "opencode"
    binary.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(script))} "$@"\n')
    binary.chmod(0o700)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("LU_HARNESS_INIT_LOG", str(tmp_path / "init.log"))
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    return repo


def _launch(checkout, *, model=_ROUTES[0], mutation=None, agent="deepseek", mode="read-only"):
    task_id = "readonly-harness-fixture"
    state_path = delegate._state_path(task_id)
    delegate._write_state_atomic(
        state_path,
        {
            "task_id": task_id,
            "cwd": str(checkout),
            "mode": mode,
            "model": model,
            "cli_version": "fixture",
        },
    )
    launches = []

    def provider(_agent, _prompt, **kwargs):
        pre = delegate._read_only_snapshot_sidecar_path(task_id, "pre")
        launches.append(json.loads(pre.read_text()) if pre.exists() else {})
        if agent in {"deepseek", "glm"}:
            from scripts.agent_runtime.env_sanitize import build_agent_env
            from scripts.agent_runtime.runner import _load_adapter, _prepare_spawn_command

            plan = _load_adapter(agent).build_invocation(prompt="", mode=mode, cwd=checkout, model=model)
            env = build_agent_env(provider=agent, model=model, overrides=plan.env_overrides)
            command, env = _prepare_spawn_command([plan.cmd[0], "run"], env)
            subprocess.run(command, env=env, cwd=checkout, check=True, capture_output=True, timeout=30)
        if mutation:
            mutation(checkout)
        return SimpleNamespace(
            ok=True,
            response="OK",
            stderr_excerpt=None,
            returncode=0,
            rate_limited=False,
            model=model,
            effort="high",
            cli_version="fixture",
        )

    with patch("agent_runtime.runner.invoke", side_effect=provider):
        rc = delegate._run_worker(
            task_id=task_id,
            agent=agent,
            prompt="Read tracked.txt and report.",
            mode=mode,
            cwd_str=str(checkout),
            model=model,
            hard_timeout=60,
        )
    return rc, delegate._read_state(state_path), launches


@pytest.mark.parametrize("model", _ROUTES)
def test_harness_only_install_is_in_baseline_and_passes_guard(checkout, model):
    """AC-01: installing ignored dependencies must not false-fail either DeepSeek route."""
    rc, state, launches = _launch(checkout, model=model)
    assert rc == 0
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []
    assert _DEPENDENCY in launches[0]
    assert (checkout.parent / "init.log").read_text() == "init\nrun\n"


@pytest.mark.parametrize(
    "relative",
    [
        "tracked.txt",
        _PLUGIN,
        "new.txt",
        ".opencode/new.txt",
        ".opencode-lookalike/new.txt",
        ".opencode/node_modules/new.js",
        _DEPENDENCY,
        ".opencode/node_modules/__pycache__/worker.pyc",
        ".opencode/node_modules/worker.db-wal",
    ],
)
def test_post_baseline_worker_writes_fail_even_for_ignored_existing_dependencies(checkout, relative):
    """AC-02: ignored status, tracked plugins and lookalike names cannot hide worker edits."""

    def mutate(repo):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("worker mutation\n")

    rc, state, _ = _launch(checkout, mutation=mutate)
    assert rc == 1
    assert state["status"] == "failed"
    assert relative in state["read_only_mutation_paths"]


def test_post_baseline_symlink_escape_is_a_mutation(checkout):
    """AC-02: an ignored escaping symlink is still worker output."""
    outside = checkout.parent / "outside"
    outside.mkdir()
    rc, state, _ = _launch(checkout, mutation=lambda repo: (repo / ".opencode/node_modules/escape").symlink_to(outside))
    assert rc == 1
    assert ".opencode/node_modules/escape" in state["read_only_mutation_paths"]


def test_existing_ignored_dependency_rewrite_is_not_hidden_by_unchanged_git_status(checkout):
    """The guard must detect content changes even when both Git statuses remain ignored."""
    subprocess.run(["opencode", "debug", "config"], cwd=checkout, check=True, capture_output=True, timeout=30)
    rc, state, _ = _launch(checkout, mutation=lambda repo: (repo / _DEPENDENCY).write_text("worker edit\n"))
    assert rc == 1
    assert state["read_only_mutation_paths"] == [_DEPENDENCY]


def test_preexisting_dirty_plugin_rewrite_still_fails(checkout):
    """A tracked plugin already marked modified must not hide a second edit."""
    (checkout / _PLUGIN).write_text("preexisting user edit\n")
    rc, state, _ = _launch(checkout, mutation=lambda repo: (repo / _PLUGIN).write_text("worker edit\n"))
    assert rc == 1
    assert state["read_only_mutation_paths"] == [_PLUGIN]


def test_post_baseline_dependency_deletion_still_fails(checkout):
    """Moving installation before the baseline must not hide removal of that installation."""
    rc, state, _ = _launch(checkout, mutation=lambda repo: (repo / _DEPENDENCY).unlink())
    assert rc == 1
    assert _DEPENDENCY in state["read_only_mutation_paths"]


def test_initialization_timeout_starts_no_worker(checkout, monkeypatch):
    """A stalled initialization cannot fall through to provider execution."""
    from scripts.agent_runtime.adapters import deepseek

    real_run = deepseek.subprocess.run

    def run(command, *args, **kwargs):
        if command[1:3] == ["debug", "config"]:
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(deepseek.subprocess, "run", run)
    rc, state, launches = _launch(checkout)
    assert rc == 1
    assert launches == []
    assert "initialization failed (TimeoutExpired)" in state["stderr_excerpt"]


@pytest.mark.parametrize("agent,model", [("deepseek", _ROUTES[0]), ("glm", "glm-5.3-flash")])
def test_missing_harness_binary_refuses_worker_without_environment_fallback(checkout, monkeypatch, agent, model):
    """A missing CLI must report a typed refusal without worker or unsanitized retry."""
    from scripts.agent_runtime.adapters import deepseek
    from scripts.agent_runtime.binary_resolve import augment_path_for_login_bins, resolve_agent_binary

    home = checkout.parent / "empty-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", os.pathsep.join(("/usr/bin", "/bin")))
    monkeypatch.setenv("FAKE_SECRET_TOKEN", "fixture-value")
    monkeypatch.setenv("LANG", "C.UTF-8")
    assert resolve_agent_binary("opencode", path=os.environ["PATH"]) is None
    message = "OpenCode dependency initialization failed (opencode harness binary not found); worker not started"
    with patch.object(deepseek.subprocess, "run", wraps=deepseek.subprocess.run) as run:
        with pytest.raises(ValueError, match="opencode harness binary not found") as error:
            deepseek.initialize_opencode_dependencies(checkout, agent=agent, model=model)
        assert str(error.value) == message
        rc, state, launches = _launch(checkout, agent=agent, model=model)

    assert rc == 1
    assert state["status"] == "failed"
    assert state["stderr_excerpt"] == f"adapter rejected before spawn: {message}"
    assert state["returncode"] is None
    assert launches == []
    assert not (checkout.parent / "init.log").exists()
    attempts = [call for call in run.call_args_list if call.args[0][0] == "opencode"]
    assert len(attempts) == 2
    for attempt in attempts:
        assert attempt.args[0] == ["opencode", "debug", "config", "--print-logs"]
        env = attempt.kwargs["env"]
        assert "FAKE_SECRET_TOKEN" not in env
        assert env["PATH"] == augment_path_for_login_bins(os.environ["PATH"])
        assert env["LANG"] == "C.UTF-8"


def test_unreadable_opencode_snapshot_fails_closed(checkout, monkeypatch):
    """Missing content evidence must not report a successful guarded run."""
    real_open = delegate.os.open

    def open_path(path, *args, **kwargs):
        if path == "index.js":
            raise PermissionError("fixture unreadable")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(delegate.os, "open", open_path)
    rc, state, _ = _launch(checkout)
    assert rc == 1
    assert state["read_only_checkout_snapshot_error"] == "opencode snapshot failed: PermissionError"


@pytest.mark.parametrize("failure", ["exit", "warning"])
def test_failed_initialization_starts_no_worker_and_does_not_expose_output(checkout, monkeypatch, capsys, failure):
    """A failed install, including OpenCode's swallowed install error, cannot start the worker."""
    monkeypatch.setenv("LU_HARNESS_INIT_FAILURE", failure)
    rc, state, launches = _launch(checkout)
    assert rc == 1
    assert state["status"] == "failed"
    assert launches == []
    assert "OpenCode dependency initialization failed" in state["stderr_excerpt"]
    assert "private diagnostic" not in json.dumps(state) + str(capsys.readouterr())


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_write_mode_does_not_gain_initialization(checkout, mode):
    """The read-only correction must leave write-mode startup unchanged."""
    _, _, launches = _launch(checkout, mode=mode)
    assert len(launches) == 1
    assert (checkout.parent / "init.log").read_text() == "run\n"


def test_glm_opencode_sibling_initializes_before_baseline(checkout):
    """GLM uses the same OpenCode dependency install and needs the same ordering."""
    rc, state, _ = _launch(checkout, agent="glm", model="glm-5.3-flash")
    assert rc == 0
    assert state["read_only_mutation_paths"] == []
    assert (checkout.parent / "init.log").read_text() == "init\nrun\n"


def test_other_harness_starts_without_opencode_initialization(checkout):
    """A non-OpenCode worker must not start an unrelated harness."""
    rc, state, _ = _launch(checkout, agent="grok", model="grok-4.7")
    assert rc == 0
    assert state["status"] == "done"
    assert not (checkout.parent / "init.log").exists()


@pytest.mark.parametrize("agent,model", [("deepseek", route) for route in _ROUTES] + [("glm", "glm-5.3-flash")])
def test_initialization_withholds_runtime_secrets_and_preserves_allowed_context(checkout, monkeypatch, agent, model):
    """B1: checkout plugin code must not receive credentials withheld from the actual run."""
    for name in ("FAKE_SECRET_TOKEN", "OPENROUTER_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.setenv(name, "fixture-value")
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.setenv("OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX", "1")
    from scripts.agent_runtime.env_sanitize import build_agent_env

    with patch("scripts.agent_runtime.adapters.deepseek.build_agent_env", wraps=build_agent_env) as build_env:
        rc, state, _ = _launch(checkout, agent=agent, model=model)
    assert build_env.call_args.kwargs == {
        "provider": agent,
        "model": model,
        "overrides": {"OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX": "131072"},
    }
    observed = json.loads((checkout.parent / "init-env.json").read_text())
    assert observed["secrets_present"] == []
    assert observed["LANG"] == "C.UTF-8"
    assert observed == json.loads((checkout.parent / "run-env.json").read_text())
    assert rc == 0
    assert state["status"] == "done"


@pytest.mark.parametrize("login_bin", [".local/bin", ".opencode/bin"])
def test_minimal_path_finds_login_only_binary_for_initialization_and_run(checkout, monkeypatch, login_bin):
    """S1: bootstrap must find the same login-installed CLI as the runtime under a minimal PATH."""
    home = checkout.parent / "home"
    binary = home / login_bin / "opencode"
    binary.parent.mkdir(parents=True)
    (checkout.parent / "opencode").rename(binary)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", os.pathsep.join(("/usr/bin", "/bin")))
    assert shutil.which("opencode") is None
    rc, state, launches = _launch(checkout)
    assert rc == 0
    assert state["status"] == "done"
    assert _DEPENDENCY in launches[0]
    assert (checkout.parent / "init.log").read_text() == "init\nrun\n"
