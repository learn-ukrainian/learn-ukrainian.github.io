"""Read-only checkout guard and harness initialization on the v2 dispatcher (C-2188 unit D4).

Every test here is a port of a legacy ``delegate.py`` test, copy-adapted to
``scripts.dispatcher.read_only_guard`` and the real ``worker.supervise``; the
legacy originals stay untouched. The supervisor runs in-process with only the
common reaper stubbed, so harness initialization, both snapshots, the provider
process and the settle are the production path. Provider stubs mutate the
checkout from ``parse``, which runs after the provider exited and before the
post-snapshot, where the legacy tests mutated from the mocked provider call.
"""

from __future__ import annotations

import json
import os
import shlex
import signal
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.agent_runtime import agy_hook_config as hooks
from scripts.dispatcher import providers, read_only_guard, store, worker
from scripts.dispatcher.types import Invocation, ParsedResult

_DEPENDENCY = ".opencode/node_modules/example/index.js"
_PLUGIN = ".opencode/plugins/example.js"
_ROUTES = ("deepseek-v4.1-flash", "openrouter/deepseek/deepseek-v4.1-flash")
HOOK = ".agents/hooks.json"
# The v2 opencode provider reads JSON events, and its child environment carries no
# fixture variables, so the run log sits beside the script instead of in the env.
_FAKE_OPENCODE = r"""
import json
import os
import sys
from pathlib import Path

if sys.argv[1:] == ["--version"]:
    print("1.19.3")
    raise SystemExit(0)
initializing = sys.argv[1:3] == ["debug", "config"]
with open(Path(__file__).with_name("init.log"), "a") as log:
    log.write("init\n" if initializing else "run\n")
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
print("configuration output must not escape" if initializing else json.dumps({"type": "text", "part": {"text": "OK"}}))
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def _status(worktree: Path) -> str:
    return _git(worktree, "status", "--porcelain=v1", "--ignored", "--untracked-files=all")


@pytest.fixture
def tmp_tasks_dir(tmp_path, monkeypatch):
    tasks_dir = tmp_path / "tasks"
    (tasks_dir / "logs").mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks_dir))
    return tasks_dir


@pytest.fixture(autouse=True)
def in_process_supervisor(monkeypatch):
    """Keep the supervisor's signal, umask and reaper side effects inside this test."""
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)
    handlers = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)}
    mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
    umask = os.umask(0o022)
    os.umask(umask)
    monkeypatch.setattr(worker, "_reap_settled", lambda record, path: None)
    yield
    for signum, handler in handlers.items():
        signal.signal(signum, handler)
    signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    os.umask(umask)


def _stub_provider(response="OK", returncode=0):
    """A provider process that answers without touching the checkout."""
    return SimpleNamespace(
        build=lambda spec, env: Invocation(
            [sys.executable, "-c", f"import sys; sys.exit({returncode})"], None, env, None
        ),
        parse=lambda stdout, stderr, code, final: ParsedResult(response or None, None, None),
    )


def _supervise(monkeypatch, checkout, task_id, *, agent, model, mode="read-only", provider=None, mutation=None):
    """Run one task through ``worker.supervise``; return (exit code, record, launches)."""
    path = store.record_path(task_id)
    prompt = path.with_suffix(".prompt")
    prompt.write_text("Read tracked.txt and report.", encoding="utf-8")
    record = {
        "schema_version": 2, "task_id": task_id, "agent": agent, "model": model, "effort": None,
        "mode": mode, "worktree_path": str(checkout), "prompt_file": str(prompt),
        "result_file": str(path.with_suffix(".result")), "claude_account": None, "provider": None,
        "status": "spawning", "started_at": store.now(), "run_nonce": "fixture",
        "worktree_base_sha": _git(checkout, "rev-parse", "HEAD"), "worktree_branch": "main",
    }
    path.write_text(json.dumps(record), encoding="utf-8")
    real = provider or providers.load(agent)
    launches = []

    def build(spec, env):
        pre = read_only_guard._read_only_snapshot_sidecar_path(task_id, "pre")
        launches.append(json.loads(pre.read_text()) if pre.exists() else {})
        return real.build(spec, env)

    def parse(*args):
        if mutation:
            mutation(checkout)
        return real.parse(*args)

    monkeypatch.setattr(providers, "load", lambda name: SimpleNamespace(build=build, parse=parse))
    worker.supervise(path, {}, 60)
    state = json.loads(path.read_text())
    return (0 if state["status"] == "done" else 1), state, launches


# --- Ported from tests/agent_runtime/test_read_only_harness_init.py ----------


@pytest.fixture
def checkout(tmp_path, monkeypatch, tmp_tasks_dir):
    """Use a private repository and executable, never the host harness or provider."""
    from scripts.agent_runtime.adapters.glm import _CI_ENV_VARS

    # The fake CLI has no provider egress; exercise initialization in CI too.
    for key in _CI_ENV_VARS:
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
    return repo


def _launch(checkout, monkeypatch, *, model=_ROUTES[0], mutation=None, agent="opencode", mode="read-only"):
    provider = _stub_provider() if agent != "opencode" else None
    return _supervise(
        monkeypatch, checkout, "readonly-harness-fixture",
        agent=agent, model=model, mode=mode, provider=provider, mutation=mutation,
    )


@pytest.mark.parametrize("model", _ROUTES)
def test_harness_only_install_is_in_baseline_and_passes_guard(checkout, monkeypatch, model):
    """AC-01: installing ignored dependencies must not false-fail either DeepSeek route."""
    rc, state, launches = _launch(checkout, monkeypatch, model=model)
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
def test_post_baseline_worker_writes_fail_even_for_ignored_existing_dependencies(checkout, monkeypatch, relative):
    """AC-02: ignored status, tracked plugins and lookalike names cannot hide worker edits."""

    def mutate(repo):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("worker mutation\n")

    rc, state, _ = _launch(checkout, monkeypatch, mutation=mutate)
    assert rc == 1
    assert state["status"] == "failed"
    assert relative in state["read_only_mutation_paths"]


def test_post_baseline_symlink_escape_is_a_mutation(checkout, monkeypatch):
    """AC-02: an ignored escaping symlink is still worker output."""
    outside = checkout.parent / "outside"
    outside.mkdir()
    rc, state, _ = _launch(
        checkout, monkeypatch, mutation=lambda repo: (repo / ".opencode/node_modules/escape").symlink_to(outside)
    )
    assert rc == 1
    assert ".opencode/node_modules/escape" in state["read_only_mutation_paths"]


def test_existing_ignored_dependency_rewrite_is_not_hidden_by_unchanged_git_status(checkout, monkeypatch):
    """The guard must detect content changes even when both Git statuses remain ignored."""
    subprocess.run(["opencode", "debug", "config"], cwd=checkout, check=True, capture_output=True, timeout=30)
    rc, state, _ = _launch(checkout, monkeypatch, mutation=lambda repo: (repo / _DEPENDENCY).write_text("worker edit\n"))
    assert rc == 1
    assert state["read_only_mutation_paths"] == [_DEPENDENCY]


def test_preexisting_dirty_plugin_rewrite_still_fails(checkout, monkeypatch):
    """A tracked plugin already marked modified must not hide a second edit."""
    (checkout / _PLUGIN).write_text("preexisting user edit\n")
    rc, state, _ = _launch(checkout, monkeypatch, mutation=lambda repo: (repo / _PLUGIN).write_text("worker edit\n"))
    assert rc == 1
    assert state["read_only_mutation_paths"] == [_PLUGIN]


def test_post_baseline_dependency_deletion_still_fails(checkout, monkeypatch):
    """Moving installation before the baseline must not hide removal of that installation."""
    rc, state, _ = _launch(checkout, monkeypatch, mutation=lambda repo: (repo / _DEPENDENCY).unlink())
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
    rc, state, launches = _launch(checkout, monkeypatch)
    assert rc == 1
    assert launches == []
    assert "initialization failed (TimeoutExpired)" in state["error"]


def test_unreadable_opencode_snapshot_fails_closed(checkout, monkeypatch):
    """Missing content evidence must not report a successful guarded run."""
    real_open = read_only_guard.os.open

    def open_path(path, *args, **kwargs):
        if path == "index.js":
            raise PermissionError("fixture unreadable")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(read_only_guard.os, "open", open_path)
    rc, state, _ = _launch(checkout, monkeypatch)
    assert rc == 1
    assert state["read_only_checkout_snapshot_error"] == "opencode snapshot failed: PermissionError"


@pytest.mark.parametrize("failure", ["exit", "warning"])
def test_failed_initialization_starts_no_worker_and_does_not_expose_output(checkout, monkeypatch, capsys, failure):
    """A failed install, including OpenCode's swallowed install error, cannot start the worker."""
    monkeypatch.setenv("LU_HARNESS_INIT_FAILURE", failure)
    rc, state, launches = _launch(checkout, monkeypatch)
    assert rc == 1
    assert state["status"] == "failed"
    assert launches == []
    assert "OpenCode dependency initialization failed" in state["error"]
    assert "private diagnostic" not in json.dumps(state) + str(capsys.readouterr())


@pytest.mark.parametrize("mode", ["workspace-write"])
def test_write_mode_does_not_gain_initialization(checkout, monkeypatch, mode):
    """The read-only correction must leave write-mode startup unchanged."""
    _, _, launches = _launch(checkout, monkeypatch, mode=mode)
    assert len(launches) == 1
    assert (checkout.parent / "init.log").read_text() == "run\n"


def test_other_harness_starts_without_opencode_initialization(checkout, monkeypatch):
    """A non-OpenCode worker must not start an unrelated harness."""
    rc, state, _ = _launch(checkout, monkeypatch, agent="codex", model="gpt-6.1-sol")
    assert rc == 0
    assert state["status"] == "done"
    assert not (checkout.parent / "init.log").exists()


@pytest.mark.parametrize("case", ["git-missing", "post-git-timeout-after-write", "generic-pre-then-fail-closed-post"])
def test_unacquired_checkout_snapshot_settles_failed_never_done(checkout, monkeypatch, case):
    """Without both checkout snapshots there is no content evidence, so a read-only task cannot settle done."""
    phase = {"post": False}
    real_run = read_only_guard.subprocess.run
    real_opencode = read_only_guard._read_only_opencode_fingerprints

    def run(command, *args, **kwargs):
        if command[:2] == ["git", "status"] and "-z" in command:
            if case == "git-missing":
                raise FileNotFoundError(2, "private diagnostic", "git")
            if case == "post-git-timeout-after-write" and phase["post"]:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            if case == "generic-pre-then-fail-closed-post" and not phase["post"]:
                return subprocess.CompletedProcess(command, 128, "", "fatal: private diagnostic\n")
        return real_run(command, *args, **kwargs)

    def opencode(cwd):
        if case == "generic-pre-then-fail-closed-post" and phase["post"]:
            raise PermissionError("private diagnostic")
        return real_opencode(cwd)

    def mutate(repo):
        phase["post"] = True
        (repo / "tracked.txt").write_text("worker mutation\n")

    monkeypatch.setattr(read_only_guard.subprocess, "run", run)
    monkeypatch.setattr(read_only_guard, "_read_only_opencode_fingerprints", opencode)
    rc, state, launches = _launch(checkout, monkeypatch, agent="codex", model="gpt-6.1-sol", mutation=mutate)
    assert len(launches) == 1
    assert rc == 1
    assert state["status"] == "failed"
    assert "read_only_checkout_snapshot_failed" in state["error"]
    assert "private diagnostic" not in state["error"]
    assert state["read_only_snapshot_retention"] == "full"


# --- Ported from tests/test_delegate_readonly_guard.py -----------------------


def _seed_read_only_checkout_fixture(repo: Path) -> None:
    """Git repo with production-shaped ignore rules + one tracked file."""
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    entire = repo / ".entire"
    entire.mkdir(parents=True, exist_ok=True)
    (entire / ".gitignore").write_text(
        "tmp/\nsettings.local.json\nmetadata/\nlogs/\nredactors/local/\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text(
        ".agent/\n.mcp/servers/message-broker/*.log\nscratch/\n.cache/\nbatch_state/\n.pytest_cache/\n"
        ".pytest_breadcrumbs/\n.ruff_cache/\n__pycache__/\n.runtime/\n*.sqlite3-wal\n*.sqlite3-shm\n"
        "*.sqlite3-journal\n",
        encoding="utf-8",
    )
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", ".entire/.gitignore", ".gitignore", "tracked.txt")
    _git(repo, "commit", "-qm", "fixture")


def test_read_only_snapshot_excluded_path_classification():
    """#7124: every ``.worktrees/`` path is out of snapshot scope."""
    assert read_only_guard._is_read_only_snapshot_excluded_path(".worktrees")
    assert read_only_guard._is_read_only_snapshot_excluded_path(
        ".worktrees/dispatch/other-lane/other-task/scripts/foo.py"
    )
    assert read_only_guard._is_read_only_snapshot_excluded_path("./.worktrees/dispatch/a/b/")
    assert not read_only_guard._is_read_only_snapshot_excluded_path("tracked.txt")
    assert not read_only_guard._is_read_only_snapshot_excluded_path("sub/.worktrees/file")
    assert not read_only_guard._is_read_only_snapshot_excluded_path(".worktreesish/file")


def test_read_only_delegate_snapshot_sidecar_path_is_runtime_state():
    """#7203/#7208: repo-root dispatches observe the sidecar as ``tasks/<id>.snapshots/…``."""
    sidecar = "tasks/read-only-task.snapshots/read_only_checkout_pre.json"
    digest = "tasks/read-only-task.snapshots/digest.json"
    assert read_only_guard._is_read_only_delegate_snapshot_sidecar_path(sidecar)
    assert read_only_guard._is_read_only_delegate_snapshot_sidecar_path(digest)
    assert read_only_guard._is_read_only_runtime_state_path(digest)
    assert read_only_guard._is_read_only_runtime_state_path(sidecar)
    assert not read_only_guard._is_read_only_runtime_telemetry_path(sidecar)


def test_read_only_checkout_snapshot_excludes_worktrees_tree(tmp_path):
    """#7124: the snapshot records no ``.worktrees/`` entries at all."""
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo)
    noise = repo / ".worktrees" / "dispatch" / "gemini" / "other-task"
    noise.mkdir(parents=True)
    (noise / "draft.md").write_text("other lane\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("visible\n", encoding="utf-8")

    snapshot, error = read_only_guard._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert "untracked.txt" in snapshot
    assert not any(read_only_guard._is_read_only_snapshot_excluded_path(path) for path in snapshot)


def test_watcher_log_exemption_is_exact_and_never_exempts_tracked_edits():
    relative = ".mcp/servers/message-broker/watcher.log"
    assert read_only_guard._is_read_only_runtime_state_path(relative)
    for path in (
        "watcher.log",
        "other/watcher.log",
        ".mcp/servers/other/watcher.log",
        relative + ".bak",
        ".mcp/servers/message-broker/scratch.log",
    ):
        assert not read_only_guard._is_read_only_runtime_state_path(path)
    assert read_only_guard._read_only_mutation_paths({}, {relative: "!! new"}) == []
    assert read_only_guard._read_only_mutation_paths({relative: "!! old"}, {relative: "!! new"}) == []
    assert read_only_guard._read_only_mutation_paths({relative: "tracked old"}, {relative: " M new"}) == [relative]


@pytest.mark.parametrize("edit", ["overwrite", "append"])
def test_read_only_worker_fails_after_changing_terminal_result(edit, tmp_tasks_dir, tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    (tmp_tasks_dir / "impl-task.json").write_text(
        json.dumps({"task_id": "impl-task", "status": "done", "run_nonce": "first"}), encoding="utf-8"
    )
    foreign_path = tmp_tasks_dir / "impl-task.result"
    foreign_path.write_text("original\n", encoding="utf-8")

    def overwrite_foreign_record(_checkout):
        if edit == "append":
            with foreign_path.open("a", encoding="utf-8") as output:
                output.write("appended\n")
        else:
            foreign_path.write_text("replaced\n", encoding="utf-8")

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=overwrite_foreign_record,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == [f"batch_state/tasks/{foreign_path.name}"]
    assert state["error"] == "read_only_checkout_mutation, count 1"


def test_read_only_review_ignores_sibling_task_lifecycle(tmp_tasks_dir, tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    sibling_path = tmp_tasks_dir / "sibling-task.json"
    sibling_path.write_text(json.dumps({"task_id": "sibling-task", "status": "spawning"}), encoding="utf-8")

    def finish_sibling(_checkout):
        sibling_path.write_text(json.dumps({"task_id": "sibling-task", "status": "running"}), encoding="utf-8")
        sibling_path.with_suffix(".result").write_text("completed\n", encoding="utf-8")
        sibling_path.write_text(json.dumps({"task_id": "sibling-task", "status": "done"}), encoding="utf-8")

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=finish_sibling,
    )

    assert rc == 0
    assert state["status"] == "done"
    assert state["read_only_mutation_paths"] == []


def test_read_only_record_snapshot_ignores_result_vanishing_during_read(tmp_tasks_dir, monkeypatch):
    state_path = tmp_tasks_dir / "finished-task.json"
    state_path.write_text(json.dumps({"task_id": "finished-task", "status": "done"}), encoding="utf-8")
    result_path = state_path.with_suffix(".result")
    result_path.write_text("original\n", encoding="utf-8")
    baseline, error = read_only_guard._read_only_task_record_snapshot("review-task")
    assert error is None
    assert baseline

    original_read_bytes = Path.read_bytes

    def vanished_on_read(path):
        if path == result_path:
            raise FileNotFoundError(result_path)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", vanished_on_read)
    after, error = read_only_guard._read_only_task_record_snapshot("review-task", baseline)
    assert error is None
    assert after == {}


def test_read_only_checkout_snapshot_keeps_rename_source_into_worktrees(tmp_path):
    """#7147: renaming a tracked file INTO ``.worktrees/`` keeps the source."""
    repo = (tmp_path / "repo").resolve()
    repo.mkdir(parents=True, exist_ok=True)
    _seed_read_only_checkout_fixture(repo)
    lane = repo / ".worktrees" / "lane"
    lane.mkdir(parents=True)
    _git(repo, "mv", "tracked.txt", ".worktrees/lane/tracked.txt")

    snapshot, error = read_only_guard._read_only_checkout_snapshot(repo)

    assert error is None
    assert snapshot is not None
    assert snapshot["tracked.txt"] == "R :source"
    assert ".worktrees/lane/tracked.txt" not in snapshot


# --- Ported from tests/test_agy_read_only_provisioning.py --------------------


@pytest.fixture
def primary(tmp_path, monkeypatch) -> Path:
    """A primary checkout that ignores ``.agents/`` like the real repository."""
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
    return repo


def _dispatch_worktree(primary: Path, task_id: str, agent: str = "agy") -> Path:
    worktree = primary / ".worktrees" / "dispatch" / agent / task_id
    _git(primary, "worktree", "add", "-q", "--detach", str(worktree), "HEAD")
    assert worktree.resolve().is_relative_to((primary / ".worktrees" / "dispatch").resolve())
    assert (worktree / ".git").is_file()
    return worktree


def _launch_agy(monkeypatch, worktree, task_id, provider_script):
    launches = []

    def build(spec, env):
        hook = spec.worktree / HOOK
        launches.append({
            "hook_bytes": hook.read_bytes() if hook.exists() else None,
            "hook_check": hooks.check_hook_config(hooks.hook_locations(spec.worktree, Path.home())),
            "status_before": _status(spec.worktree),
        })
        return Invocation([sys.executable, "-c", provider_script], None, env, None)

    def parse(stdout, stderr, returncode, final_text):
        launches[-1]["status_after"] = _status(worktree)
        launches[-1]["hook_check_after"] = hooks.check_hook_config(hooks.hook_locations(worktree, Path.home()))
        return ParsedResult("VERDICT: PASS", None, None)

    rc, state, baselines = _supervise(
        monkeypatch, worktree, task_id, agent="agy", model="gemini-3.8-flash-high",
        provider=SimpleNamespace(build=build, parse=parse),
    )
    for launch, baseline in zip(launches, baselines, strict=True):
        launch["baseline_paths"] = sorted(baseline)
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


def test_fresh_read_only_launch_has_guard_in_baseline_and_settles_done(primary, tmp_tasks_dir, monkeypatch):
    """Case 1 (AC-01): a fresh read-only launch is not failed by the framework's own guard."""
    task_id = "ro-10727-fresh-success"
    worktree = _dispatch_worktree(primary, task_id)
    assert not (worktree / HOOK).exists()

    rc, state, launches = _launch_agy(monkeypatch, worktree, task_id, _READ)

    assert state["read_only_mutation_paths"] == []
    assert state["status"] == "done"
    assert len(launches) == 1
    launch = launches[0]
    assert HOOK in launch["baseline_paths"]
    assert launch["hook_check"] == hooks.HookConfigResult("PASS", "guard_registered")
    assert json.loads(launch["hook_bytes"]) == {hooks.GUARD_NAME: hooks.guard_registration()}
    assert (worktree / HOOK).read_bytes() == launch["hook_bytes"]
    assert state["error"] is None
    assert rc == 0
    assert _git(worktree, "status", "--porcelain") == ""


def test_valid_hook_rewrite_with_unchanged_ignored_status_still_fails(primary, tmp_tasks_dir, monkeypatch):
    """Case 4 (AC-02): Git status cannot see this rewrite; the hook fingerprint does."""
    task_id = "ro-10727-hook-rewrite"
    worktree = _dispatch_worktree(primary, task_id)
    hooks.install_worktree_guard(worktree)  # An earlier dispatch already provisioned this worktree.
    before = (worktree / HOOK).read_bytes()

    rc, state, launches = _launch_agy(monkeypatch, worktree, task_id, _REWRITE_HOOK)

    launch = launches[0]
    assert launch["hook_bytes"] == before
    assert (worktree / HOOK).read_bytes() != before
    assert json.loads((worktree / HOOK).read_bytes()) == json.loads(before)
    assert launch["hook_check_after"].passed
    assert launch["status_before"] == launch["status_after"]
    assert f"!! {HOOK}" in launch["status_after"].splitlines()
    assert state["read_only_mutation_paths"] == [HOOK]
    assert state["status"] == "failed"
    assert state["error"] == "read_only_checkout_mutation, count 1"
    assert rc == 1


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("unrelated-existing-hook", "missing_guard"),
        ("invalid-existing-hook", "invalid_json"),
        ("provisioning-failed", "missing_file"),
    ],
)
def test_agy_without_a_valid_guard_registration_is_refused_before_spawn(
    primary, tmp_tasks_dir, monkeypatch, case, reason
):
    """An existing hook is never repaired, and a launch it or failed provisioning leaves unguarded never starts."""
    task_id = f"ro-agy-refused-{case}"
    worktree = _dispatch_worktree(primary, task_id)
    contents = {"unrelated-existing-hook": b'{"unrelated-hook":{"Stop":[]}}\n', "invalid-existing-hook": b"not json\n"}
    if case in contents:
        (worktree / ".agents").mkdir()
        (worktree / HOOK).write_bytes(contents[case])
    else:

        def refuse(cwd, **kwargs):
            raise hooks.AgyHookConfigError("unsafe_install_path")

        monkeypatch.setattr(hooks, "install_worktree_guard", refuse)

    rc, state, launches = _launch_agy(monkeypatch, worktree, task_id, _READ)

    assert launches == []
    assert rc == 1
    assert state["status"] == "failed"
    assert state["error"] == f"adapter rejected before spawn: agy_hook_config_refused: {reason}"
    if case in contents:
        assert (worktree / HOOK).read_bytes() == contents[case]
    else:
        assert not (worktree / HOOK).exists()


def test_hook_fingerprint_distinguishes_bytes_links_and_file_types(tmp_path):
    """Absent stays absent; content, every link crossed, target and file type are each recorded."""
    import stat

    tmp_path = tmp_path.resolve()
    regular = {"file_type": stat.S_IFREG}
    empty_sha = "ca3d163bab055381827226140568f3bef7eaac187cebd76878e0b63e9e442356"
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").write_text("not a directory\n", encoding="utf-8")
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (None, None)
    (tmp_path / ".agents").unlink()
    (tmp_path / ".agents").mkdir()
    hook = tmp_path / HOOK
    hook.write_bytes(b"{}\n")
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        {"links": [], "target": {"path": str(hook), **regular}, "sha256": empty_sha},
        None,
    )
    hook.unlink()
    hook.symlink_to("elsewhere.json")
    final_link = {"path": str(hook), "link_text": "elsewhere.json", "file_type": stat.S_IFLNK}
    (tmp_path / ".agents" / "elsewhere.json").write_bytes(b"{}\n")
    target = {"path": str(tmp_path / ".agents" / "elsewhere.json"), **regular}
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        {"links": [final_link], "target": target, "sha256": empty_sha},
        None,
    )
    # Every link of a chain, absolute or relative, is kept even though the target is the same.
    (tmp_path / ".agents").rename(tmp_path / "guard")
    (tmp_path / "current").symlink_to(str(tmp_path / "guard"))
    (tmp_path / ".agents").symlink_to("./current/../current")
    target = {"path": str(tmp_path / "guard" / "elsewhere.json"), **regular}
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        {
            "links": [
                {"path": str(tmp_path / ".agents"), "link_text": "./current/../current", "file_type": stat.S_IFLNK},
                {"path": str(tmp_path / "current"), "link_text": str(tmp_path / "guard"), "file_type": stat.S_IFLNK},
                # ``..`` leaves the directory the link led to, not the link's own directory.
                {"path": str(tmp_path / "current"), "link_text": str(tmp_path / "guard"), "file_type": stat.S_IFLNK},
                {**final_link, "path": str(tmp_path / "guard" / "hooks.json")},
            ],
            "target": target,
            "sha256": empty_sha,
        },
        None,
    )
    (tmp_path / ".agents").unlink()
    (tmp_path / "current").unlink()
    (tmp_path / "guard").rename(tmp_path / ".agents")
    hook.unlink()
    os.mkfifo(hook)
    fifo = {"file_type": stat.S_IFIFO}
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        {"links": [], "target": {"path": str(hook), **fifo}, "sha256": None},
        None,
    )


@pytest.mark.parametrize(
    ("link_text", "error"),
    [
        ("elsewhere.json", "FileNotFoundError"),  # Leads nowhere from the start.
        ("hooks.json", "OSError"),  # A loop: more links than the kernel follows.
        ("../.agents/hooks.json", "OSError"),
        ("../not-a-directory/hooks.json", "NotADirectoryError"),
        ("../not-a-directory/.", "NotADirectoryError"),
        ("../not-a-directory/", "NotADirectoryError"),
        ("../not-a-directory/../not-a-directory", "NotADirectoryError"),
    ],
)
def test_hook_whose_link_target_cannot_be_acquired_is_an_error(tmp_path, link_text, error):
    """F2 (#10748): an observed link whose target cannot be acquired is never a clean baseline."""
    (tmp_path / ".agents").mkdir()
    (tmp_path / "not-a-directory").write_text("file\n", encoding="utf-8")
    (tmp_path / HOOK).symlink_to(link_text)
    with pytest.raises(OSError):  # The kernel cannot open it either.
        (tmp_path / HOOK).read_bytes()
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        None,
        f"agy hook snapshot failed: {HOOK}: {error}",
    )


def test_hook_chain_at_the_kernel_link_limit_is_still_acquired(tmp_path):
    """The walk follows exactly as many links as the kernel: forty pass, a forty-first is a loop."""
    (tmp_path / ".agents").mkdir()
    (tmp_path / "guard.json").write_bytes(b"{}\n")
    previous = "guard.json"
    for index in range(39):
        (tmp_path / f"link-{index}").symlink_to(previous)
        previous = f"link-{index}"
    (tmp_path / HOOK).symlink_to(f"../{previous}")
    assert (tmp_path / HOOK).read_bytes() == b"{}\n"
    fingerprint, error = read_only_guard._read_only_agy_hook_fingerprint(tmp_path)
    assert error is None
    assert len(fingerprint["links"]) == 40
    (tmp_path / HOOK).unlink()
    (tmp_path / "link-39").symlink_to(previous)
    (tmp_path / HOOK).symlink_to("../link-39")
    with pytest.raises(OSError):
        (tmp_path / HOOK).read_bytes()
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
        None,
        f"agy hook snapshot failed: {HOOK}: OSError",
    )


def test_hook_behind_a_looping_parent_is_an_error_not_absence(tmp_path):
    """Only a missing hook is absent; a parent the kernel cannot traverse fails acquisition."""
    (tmp_path / ".agents").symlink_to(".agents")
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
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
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == (
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
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == changed

    monkeypatch.setattr(os, "open", original_open)
    hook.unlink()
    (tmp_path / "a.json").write_bytes(b"{}\n")
    (tmp_path / "b.json").write_bytes(b"{}\n")
    hook.symlink_to("../a.json")
    original_digest = read_only_guard._read_only_agy_hook_digest

    def retarget_after_read(identity, inode):
        digest = original_digest(identity, inode)
        hook.unlink()
        hook.symlink_to("../b.json")
        return digest

    monkeypatch.setattr(read_only_guard, "_read_only_agy_hook_digest", retarget_after_read)
    assert read_only_guard._read_only_agy_hook_fingerprint(tmp_path) == changed


def test_early_provisioning_never_writes_outside_a_dispatch_worktree(primary):
    """The primary checkout is left to the adapter's refusal; nothing is created there."""
    read_only_guard._provision_agy_read_only_guard(primary)
    assert not (primary / ".agents").exists()


# --- Beyond legacy: evidence the snapshots above could not see --------------


def _seed_terminal_sibling(tmp_tasks_dir: Path) -> Path:
    (tmp_tasks_dir / "impl-task.json").write_text(
        json.dumps({"task_id": "impl-task", "status": "done", "run_nonce": "first"}), encoding="utf-8"
    )
    result_path = tmp_tasks_dir / "impl-task.result"
    result_path.write_text("original\n", encoding="utf-8")
    return result_path


def test_unreadable_terminal_result_settles_failed_with_task_records_snapshot_failed(
    tmp_tasks_dir, tmp_path, monkeypatch
):
    """A baselined result that cannot be read again is no evidence, never an archival."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    result_path = _seed_terminal_sibling(tmp_tasks_dir)
    original_read_bytes = Path.read_bytes

    def denied(path):
        if path == result_path:
            raise PermissionError(13, "private diagnostic", str(path))
        return original_read_bytes(path)

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=lambda _checkout: monkeypatch.setattr(Path, "read_bytes", denied),
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["error"] == "task_records_snapshot_failed"
    assert "private diagnostic" not in state["error"]


def test_unchanged_status_content_rewrite_is_detected(tmp_tasks_dir, tmp_path, monkeypatch):
    """A file already dirty or untracked keeps its status through a rewrite; its content must not."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    (checkout / "tracked.txt").write_text("dirty before the task\n", encoding="utf-8")
    (checkout / "notes.txt").write_text("untracked before the task\n", encoding="utf-8")
    before = _status(checkout)

    def rewrite(repo):
        (repo / "tracked.txt").write_text("rewritten by the worker\n", encoding="utf-8")
        (repo / "notes.txt").write_text("rewritten by the worker\n", encoding="utf-8")
        assert _status(repo) == before

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=rewrite,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == ["notes.txt", "tracked.txt"]
    assert state["error"] == "read_only_checkout_mutation, count 2"


def test_read_only_task_that_commits_settles_failed(tmp_tasks_dir, tmp_path, monkeypatch):
    """A commit leaves the checkout clean, so HEAD and the task branch settle it."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    branch = _git(checkout, "symbolic-ref", "HEAD")

    def commit(repo):
        (repo / "tracked.txt").write_text("committed by the worker\n", encoding="utf-8")
        _git(repo, "commit", "-qam", "worker commit")
        assert _status(repo) == ""

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=commit,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ref_mutations"] == ["HEAD", branch]
    assert state["error"] == "read_only_ref_mutation"


def test_read_only_task_that_pushes_settles_failed(tmp_tasks_dir, tmp_path, monkeypatch):
    """A push by URL moves no local ref, so the task branch's remote tip settles it."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    branch = _git(checkout, "symbolic-ref", "HEAD")
    remote = tmp_path / "remote.git"
    _git(checkout, "init", "-q", "--bare", str(remote))
    _git(checkout, "remote", "add", "origin", str(remote))
    _git(checkout, "push", "-q", "origin", f"HEAD:{branch}")

    def push(repo):
        tree = _git(repo, "rev-parse", "HEAD^{tree}")
        unseen = _git(repo, "commit-tree", tree, "-p", "HEAD", "-m", "worker push")
        _git(repo, "push", "-q", str(remote), f"{unseen}:{branch}")
        assert _status(repo) == ""

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=push,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ref_mutations"] == [f"ls-remote origin {branch}"]
    assert state["error"] == "read_only_remote_push"


def _seed_pushed_checkout(tmp_path: Path) -> tuple[Path, str]:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _seed_read_only_checkout_fixture(checkout)
    branch = _git(checkout, "symbolic-ref", "HEAD")
    for name in ("remote.git", "push.git"):
        _git(checkout, "init", "-q", "--bare", str(tmp_path / name))
        _git(checkout, "push", "-q", str(tmp_path / name), f"HEAD:{branch}")
    _git(checkout, "remote", "add", "origin", str(tmp_path / "remote.git"))
    for alias in ("refs/heads/alias-a", "refs/heads/alias-b"):
        _git(checkout, "symbolic-ref", alias, branch)
    for tag in ("baseline-deleted", "baseline-moved"):
        _git(checkout, "tag", tag, "HEAD")
    return checkout, branch


def _rewrite_baseline_tags(repo: Path, tmp: Path) -> None:
    _git(repo, "tag", "review-leak", "HEAD")
    _git(repo, "tag", "-d", "baseline-deleted")
    unseen = _git(repo, "commit-tree", _git(repo, "rev-parse", "HEAD^{tree}"), "-m", "x")
    _git(repo, "tag", "-f", "baseline-moved", unseen)


def _add_empty_push_url(repo: Path, tmp: Path) -> None:
    _git(repo, "init", "-q", "--bare", str(tmp / "empty.git"))
    _git(repo, "remote", "set-url", "--push", "origin", str(tmp / "empty.git"))


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (
            _rewrite_baseline_tags,
            lambda repo: ["refs/tags/baseline-deleted", "refs/tags/baseline-moved", "refs/tags/review-leak"],
        ),
        (lambda repo, tmp: _git(repo, "branch", "review-leak"), lambda repo: ["refs/heads/review-leak"]),
        (lambda repo, tmp: _git(repo, "notes", "add", "-m", "unauthorized", "HEAD"), lambda repo: ["refs/notes/commits"]),
        (
            lambda repo, tmp: _git(
                repo, "replace", "HEAD", _git(repo, "commit-tree", _git(repo, "rev-parse", "HEAD^{tree}"), "-m", "x")
            ),
            lambda repo: [f"refs/replace/{_git(repo, 'rev-parse', 'HEAD')}"],
        ),
        (lambda repo, tmp: _git(repo, "update-ref", "refs/worktree/leak", "HEAD"), lambda repo: ["refs/worktree/leak"]),
        (_add_empty_push_url, lambda repo: ["config"]),
        (lambda repo, tmp: _git(repo, "config", "core.hooksPath", str(tmp)), lambda repo: ["config"]),
        (
            lambda repo, tmp: _git(repo, "symbolic-ref", "HEAD", "refs/heads/alias-b"),
            lambda repo: ["HEAD immediate symbolic-ref"],
        ),
        (
            lambda repo, tmp: _git(repo, "symbolic-ref", "refs/heads/alias-b", "refs/heads/alias-a"),
            lambda repo: ["refs/heads/alias-b"],
        ),
    ],
    ids=["tag", "heads", "notes", "replace", "worktree-ref", "pushurl", "config", "head-alias", "symref-alias"],
)
def test_read_only_task_that_writes_any_ref_or_config_settles_failed(
    tmp_tasks_dir, tmp_path, monkeypatch, mutate, expected
):
    """Every ref, HEAD and the effective config are compared, not only the task branch."""
    checkout, _branch = _seed_pushed_checkout(tmp_path)

    def write(repo):
        mutate(repo, tmp_path)
        assert _status(repo) == ""

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=write,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ref_mutations"] == expected(checkout)
    assert state["error"] == "read_only_ref_mutation"


def _plain_push_url(repo: Path, tmp: Path) -> str:
    push_url = str(tmp / "push.git")
    _git(repo, "remote", "set-url", "--push", "origin", push_url)
    return push_url


def _rewritten_push_url(repo: Path, tmp: Path) -> str:
    """``alias:`` rewrites to ``B/`` and ``B/`` to ``C/``; a push reaches ``B/`` after one rewrite."""
    for name in ("B", "C"):
        _git(repo, "clone", "-q", "--bare", str(tmp / "push.git"), str(tmp / name / "push.git"))
    _git(repo, "config", f"url.{tmp}/B/.insteadOf", "alias:")
    _git(repo, "config", f"url.{tmp}/C/.insteadOf", f"{tmp}/B/")
    _git(repo, "remote", "set-url", "--push", "origin", "alias:push.git")
    return "origin"


@pytest.mark.parametrize("configure", [_plain_push_url, _rewritten_push_url], ids=["plain", "rewritten-twice"])
def test_read_only_task_that_pushes_to_a_separate_push_url_settles_failed(
    tmp_tasks_dir, tmp_path, monkeypatch, configure
):
    """A configured push URL is probed as well as the fetch URL it differs from."""
    checkout, branch = _seed_pushed_checkout(tmp_path)
    push_url = configure(checkout, tmp_path)

    def push(repo):
        tree = _git(repo, "rev-parse", "HEAD^{tree}")
        unseen = _git(repo, "commit-tree", tree, "-p", "HEAD", "-m", "worker push")
        _git(repo, "push", "-q", push_url, f"{unseen}:{branch}")
        assert _status(repo) == ""

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=push,
    )

    assert rc == 1
    assert state["status"] == "failed"
    assert state["read_only_mutation_paths"] == []
    assert state["read_only_ref_mutations"] == [f"ls-remote origin push {branch}"]
    assert state["error"] == "read_only_remote_push"


@pytest.mark.parametrize("tagged", [None, "fetched", "worker"], ids=["branch", "auto-followed-tag", "worker-tag"])
def test_read_only_task_whose_fetch_advances_a_remote_tracking_ref_settles_done(
    tmp_tasks_dir, tmp_path, monkeypatch, tagged
):
    """A fetch writes remote-tracking refs, FETCH_HEAD and new tags it auto-follows, which read-only work may do.

    A new tag passes only when the remote has that name at that object, so tags
    a worker creates beside the fetch, one reusing a remote tag's name and one
    reusing its object, still fail.
    """
    checkout, _branch = _seed_pushed_checkout(tmp_path)
    remote = str(tmp_path / "remote.git")
    _git(checkout, "push", "-q", remote, "HEAD:refs/heads/other")
    _git(checkout, "fetch", "-q", "origin")
    advanced = _git(checkout, "commit-tree", _git(checkout, "rev-parse", "HEAD^{tree}"), "-p", "HEAD", "-m", "other")
    _git(checkout, "push", "-q", remote, f"{advanced}:refs/heads/other")
    if tagged:
        _git(checkout, "push", "-q", remote, f"{advanced}:refs/tags/fetched")

    def fetch(repo):
        before = _git(repo, "rev-parse", "refs/remotes/origin/other")
        if tagged == "worker":
            _git(repo, "tag", "fetched", "HEAD")
            _git(repo, "tag", "worker-made", advanced)
        _git(repo, "fetch", "-q", "origin")
        assert _git(repo, "rev-parse", "refs/remotes/origin/other") != before
        if tagged == "fetched":
            assert _git(repo, "rev-parse", "refs/tags/fetched") == advanced
        assert _status(repo) == ""

    rc, state, _ = _supervise(
        monkeypatch, checkout, "review-task", agent="codex", model="gpt-6.1-sol",
        provider=_stub_provider("done"), mutation=fetch,
    )

    if tagged == "worker":
        assert rc == 1
        assert state["status"] == "failed"
        assert state["read_only_ref_mutations"] == ["refs/tags/fetched", "refs/tags/worker-made"]
        assert state["read_only_ref_snapshot_error"] is None
        assert state["error"] == "read_only_ref_mutation"
        return
    assert rc == 0
    assert state["status"] == "done"
    assert state["read_only_ref_mutations"] == []
