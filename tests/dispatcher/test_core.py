"""Exercise the real dispatcher with stub processes and real disposable Git remotes."""

import concurrent.futures
import dataclasses
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import yaml

from scripts.dispatcher import checks, git, store, worker
from scripts.dispatcher.cli import ALIASES, build_parser
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.providers import muse
from scripts.dispatcher.types import TaskSpec
from scripts.review.record_cf_verdict import _review_branch

SOURCE = Path(__file__).resolve().parents[2]


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()


@pytest.fixture
def sandbox(tmp_path):
    repo, tasks = tmp_path / "public", tmp_path / "tasks"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "stub@example.invalid")
    run_git(repo, "config", "user.name", "Stub")
    for relative in ("scripts/dispatcher", "scripts/common", "scripts/review", "scripts/storage"):
        shutil.copytree(SOURCE / relative, repo / relative, ignore=shutil.ignore_patterns("__pycache__"))
    for relative in ("scripts/agent_runtime/bounded_advisory.py",
                     "scripts/orchestration/worktree_paths.py", "scripts/orchestration/task_record_store.py"):
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(SOURCE / relative, target)
    # Disposable repositories share the test interpreter; they own no project environment.
    resolver = repo / "scripts/common/repo_root.py"
    with resolver.open("a") as stream:
        stream.write(f"\n\ndef project_interpreter(root=None):\n    return Path({sys.executable!r})\n")
    shutil.copy(SOURCE / "scripts/dispatch.py", repo / "scripts/dispatch.py")
    (repo / "scripts/__init__.py").write_text(f"__path__.append({str(SOURCE / 'scripts')!r})\n")
    (repo / "scripts/fleet").mkdir()
    (repo / "scripts/fleet/__init__.py").touch()
    config = repo / "scripts/config"
    config.mkdir()
    (config / "fleet_repos.yaml").write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {
                        "default": True,
                        "local_name": "public",
                        "github": str(remote),
                        "transport": "file",
                        "role": "public-monorepo",
                    },
                    "private": {"local_name": "private", "github": "example/private", "role": "private-product"},
                }
            }
        )
    )
    shutil.copy(SOURCE / "scripts/config/model_catalog.yaml", config / "model_catalog.yaml")
    shutil.copy(Path(__file__).with_name("stub_provider.py"), repo / "scripts/dispatcher/providers/codex.py")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "fixture")
    run_git(repo, "init", "--bare", str(remote))
    run_git(repo, "remote", "add", "origin", str(remote))
    run_git(repo, "push", "-u", "origin", "main")
    env = {**os.environ, "LU_TASKS_DIR": str(tasks)}
    env.pop("PYTHONPATH", None)

    def cli(*args, expected=0, stdin=None):
        result = subprocess.run(
            [sys.executable, "scripts/dispatch.py", *args],
            cwd=repo,
            env=env,
            input=stdin,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == expected, (result.stdout, result.stderr)
        return result

    def dispatch(model="echo", *args):
        result = cli("dispatch", "--agent", "sol", "--model", model, "--prompt", "literal final response", *args)
        task_id, nonce = result.stdout.splitlines()
        return task_id, nonce

    def settle(task, expected=0):
        return json.loads(
            cli(
                "wait", task[0], "--run-nonce", task[1], "--timeout", "15", "--poll-interval", "0.02", expected=expected
            ).stdout
        )

    box = SimpleNamespace(repo=repo, tasks=tasks, remote=remote, env=env, cli=cli, dispatch=dispatch, settle=settle)
    yield box
    # Reap detached test supervisors, including a test interrupted by an assertion.
    for path in tasks.glob("*.json"):
        record = json.loads(path.read_text())
        if record["status"] in store.ACTIVE and worker._identity(record.get("pid")) == record.get("process_start"):
            cli("cancel", record["task_id"], "--run-nonce", record["run_nonce"])


def await_file(path):
    deadline = time.monotonic() + 10
    while not path.exists():
        assert time.monotonic() < deadline, f"stub did not create {path.name}"
        time.sleep(0.02)
    return path.read_text()


def stub_common_reaper(box):
    fleet = box.repo / "scripts/fleet"
    fleet.mkdir(exist_ok=True)
    (fleet / "post_task_reap.py").write_text('''import json, os, sys
from pathlib import Path
from scripts.dispatcher.worker import _identity
tasks = Path(os.environ["LU_TASKS_DIR"])
task_id = sys.argv[2]
record = json.loads((tasks / (task_id + ".json")).read_text())
with (tasks / (task_id + ".reap-calls")).open("a") as calls:
    calls.write("called\\n")
receipt = dict(argv=sys.argv[1:], cwd=os.getcwd(), record=record, alive=_identity(record["pid"]))
target = tasks / (task_id + ".reaped")
target.with_suffix(".tmp").write_text(json.dumps(receipt))
target.with_suffix(".tmp").replace(target)
print(json.dumps({"main_worktree": {"action": "retained"}}))
sys.exit(1 if (tasks / "reap-fail").exists() else 0)
''')


@pytest.mark.parametrize("flags,restored", [
    ([], set()), (["--full-checkout"], {"curriculum", "site/src/data"}),
    (["--sparse-include", "/curriculum/"], {"curriculum"}),
    (["--sparse-include", "curriculum", "--sparse-include", "site/src/data"], {"curriculum", "site/src/data"}),
])
def test_sparse_dispatch_never_turns_on_sparse_checkout_in_primary_or_sibling_worktrees(sandbox, flags, restored):
    excluded = {
        "curriculum", "wiki", "data/projects", "data/lexicon", "data/datasets", "data/processed",
        "registry/projects", "registry/lexicon/source-inventory",
        "registry/lexicon/source-inventory-review-decisions", "site/src/content", "site/src/data",
    }
    for directory in excluded | {"site/src/components", "registry/lexicon/kept"}:
        path = sandbox.repo / directory / "fixture.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("tracked fixture")
    (sandbox.repo / "data/kept.txt").write_text("parent file")
    run_git(sandbox.repo, "add", ".")
    run_git(sandbox.repo, "commit", "-m", "heavy fixture trees")
    run_git(sandbox.repo, "push", "origin", "main")
    sibling = sandbox.repo.parent / "sibling"
    run_git(sandbox.repo, "worktree", "add", "-b", "sibling", str(sibling))
    untracked = sandbox.repo / "curriculum/untracked.txt"
    untracked.write_text("uncommitted primary file")
    record = sandbox.settle(sandbox.dispatch("echo", *flags))
    worktree = Path(record["cwd"])
    for directory in excluded:
        assert (worktree / directory / "fixture.txt").exists() == ("--full-checkout" in flags or directory in restored)
    assert (worktree / "site/src/components/fixture.txt").exists()
    assert (worktree / "registry/lexicon/kept/fixture.txt").exists()
    assert (worktree / "data/kept.txt").exists()
    assert run_git(worktree, "status", "--porcelain") == ""
    assert untracked.read_text() == "uncommitted primary file"
    for checkout in (sandbox.repo, sibling):
        assert (checkout / "curriculum/fixture.txt").read_text() == "tracked fixture"
        config = run_git(checkout, "config", "--show-origin", "--list")
        assert "core.sparsecheckout=true" not in config.lower()
    assert run_git(sandbox.repo, "config", "--local", "--get", "extensions.worktreeConfig") == "true"
    if "--full-checkout" not in flags:
        origin = run_git(worktree, "config", "--show-origin", "--get", "core.sparseCheckout")
        assert origin.endswith("/config.worktree\ttrue")


@pytest.mark.parametrize("redirected", [False, True])
def test_sparse_dispatch_never_turns_on_sparse_checkout_in_primary_with_git_redirects(sandbox, monkeypatch, redirected):
    tracked = sandbox.repo / "curriculum/tracked.txt"
    tracked.parent.mkdir()
    tracked.write_text("tracked primary file")
    run_git(sandbox.repo, "add", "curriculum")
    run_git(sandbox.repo, "commit", "-m", "excluded tree")
    untracked = tracked.with_name("untracked.txt")
    untracked.write_text("untracked primary file")
    sha = run_git(sandbox.repo, "rev-parse", "HEAD")
    path = sandbox.repo / ".worktrees/dispatch/sol/redirects"
    if redirected:
        for key, value in {
            "GIT_DIR": sandbox.repo / ".git", "GIT_WORK_TREE": sandbox.repo,
            "GIT_COMMON_DIR": sandbox.repo / ".git", "GIT_INDEX_FILE": sandbox.repo / ".git/index",
        }.items():
            monkeypatch.setenv(key, str(value))
    with monkeypatch.context() as injected:
        injected.setenv("GIT_CONFIG_PARAMETERS", "'core.sparseCheckout=false'")
        injected.setenv("GIT_CONFIG_COUNT", "2")
        injected.setenv("GIT_CONFIG_KEY_0", "core.worktree")
        injected.setenv("GIT_CONFIG_VALUE_0", str(sandbox.repo))
        injected.setenv("GIT_CONFIG_KEY_1", "core.hooksPath")
        injected.setenv("GIT_CONFIG_VALUE_1", str(sandbox.repo / "missing-hooks"))
        git.create_worktree(sandbox.repo, path, "sol/redirects", sha)
    if redirected:
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
            monkeypatch.delenv(key)
    assert tracked.read_text() == "tracked primary file"
    assert untracked.read_text() == "untracked primary file"
    assert not (path / "curriculum").exists()
    primary = subprocess.run(
        ["git", "-C", str(sandbox.repo), "config", "--show-origin", "--get", "core.sparseCheckout"],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert (primary.returncode, primary.stdout) == (1, "")
    assert run_git(path, "config", "--show-origin", "--get", "core.sparseCheckout").endswith("/config.worktree\ttrue")
    assert run_git(sandbox.repo, "diff", "--cached") == ""


@pytest.mark.parametrize("model,state", [
    ("echo", "done"), ("fail", "failed"), ("crash", "crashed"), ("blocked", "timeout"), ("tree", "cancelled"),
    ("pushed", "done"),
])
def test_settled_clean_read_only_task_worktree_is_reaped_through_the_common_reaper(sandbox, model, state):
    stub_common_reaper(sandbox)
    task = sandbox.dispatch(model, "--hard-timeout", "0.2" if state == "timeout" else "0",
                            "--mode", "workspace-write" if model == "pushed" else "read-only")
    if state == "cancelled":
        await_file(sandbox.tasks / f"{task[0]}.grandchild")
        sandbox.cli("cancel", task[0], "--run-nonce", task[1])
    sandbox.settle(task, expected=0 if state == "done" else 1)
    receipt = json.loads(await_file(sandbox.tasks / f"{task[0]}.reaped"))
    assert receipt["record"]["status"] == state
    assert receipt["record"]["worktree_dirty_on_exit"] is False
    assert receipt["record"]["push_state"] == ("pushed" if model == "pushed" else "not_applicable")
    assert receipt["argv"] == ["--task-id", task[0], "--apply", "--tasks-dir", str(sandbox.tasks)]
    assert receipt["cwd"] == str(sandbox.repo)
    assert receipt["alive"] is None
    assert (sandbox.tasks / f"{task[0]}.reap-calls").read_text() == "called\n"


@pytest.mark.parametrize("mode,model", [("read-only", "dirty"), ("workspace-write", "dirty"), ("workspace-write", "unpushed")])
def test_dirty_or_unpushed_worktree_is_never_reaped(sandbox, mode, model):
    stub_common_reaper(sandbox)
    task = sandbox.dispatch(model, "--mode", mode)
    record = sandbox.settle(task, expected=0 if mode == "read-only" else 1)
    deadline = time.monotonic() + 5
    while worker._identity(record["pid"]):
        assert time.monotonic() < deadline
        time.sleep(0.02)
    assert not (sandbox.tasks / f"{task[0]}.reap-calls").exists()
    assert (Path(record["cwd"]) / "delivered.txt").read_text() == "literal delivered value\n"


@pytest.mark.parametrize("dirty,push", [(None, "pushed"), (False, "unknown"), (False, "unpushed")])
def test_unknown_or_unpushed_delivery_never_starts_a_reaper(tmp_path, monkeypatch, dirty, push):
    def forbidden():
        pytest.fail("ineligible delivery forked a reaper")
    monkeypatch.setattr(worker.os, "fork", forbidden)
    worker._reap_settled(dict(status="done", worktree_dirty_on_exit=dirty, push_state=push,
                              mode="workspace-write"), tmp_path / "task.json")


@pytest.mark.parametrize("status", ["running", "spawning", "unknown", None])
def test_running_or_unknown_task_never_starts_a_reaper(tmp_path, monkeypatch, status):
    monkeypatch.setattr(worker.os, "fork", lambda: pytest.fail("unsettled task forked a reaper"))
    worker._reap_settled(dict(status=status, worktree_dirty_on_exit=False, push_state="pushed",
                              mode="workspace-write"), tmp_path / "task.json")
    assert json.loads((tmp_path / "task.json").read_text())["reap_note"] == (
        f"common reaper skipped: task status is not terminal ({status})"
    )


def test_zombie_supervisor_fix_preserves_pid_reuse_cancellation_guard(monkeypatch):
    identity = worker._identity(os.getpid())
    record = dict(schema_version=2, status="running", pid=os.getpid(), process_start=identity)
    identities = iter([identity, f"{identity}-reused"])
    monkeypatch.setattr(worker.store, "read", lambda *_args: record)
    monkeypatch.setattr(worker, "_identity", lambda _pid: next(identities))
    send_signal = Mock()
    monkeypatch.setattr(worker.signal, "pidfd_send_signal", send_signal)
    with pytest.raises(ValueError, match="supervisor identity changed; cancellation refused"):
        worker.cancel("reused-supervisor")
    send_signal.assert_not_called()


def test_reaper_failure_does_not_change_task_status(sandbox):
    stub_common_reaper(sandbox)
    sandbox.tasks.mkdir()
    (sandbox.tasks / "reap-fail").touch()
    task = sandbox.dispatch()
    record = sandbox.settle(task)
    assert record["status"] == "done"
    path = sandbox.tasks / f"{task[0]}.json"
    deadline = time.monotonic() + 5
    while "reap_note" not in record:
        assert time.monotonic() < deadline
        time.sleep(0.02)
        record = json.loads(path.read_text())
    assert record["status"] == "done"
    assert record["returncode"] == 0
    assert record["reap_note"] == "common reaper failed"
    assert Path(record["cwd"]).is_dir()


def test_dispatch_returns_before_blocked_child_and_client_timeout_does_not_cancel(sandbox):
    task = sandbox.dispatch("blocked")
    pid = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    assert worker._identity(pid)
    response = sandbox.cli("wait", task[0], "--run-nonce", task[1], "--timeout", "0.05", expected=124)
    assert json.loads(response.stdout)["status"] == "running"
    assert worker._identity(pid)
    (sandbox.tasks / f"{task[0]}.release").touch()
    record = sandbox.settle(task)
    assert record["status"] == "done"
    assert Path(record["result_file"]).read_text() == "literal final response"
    assert record["returncode"] == 0
    assert "review_branch" not in record
    assert "pinned_head" not in record
    assert record["started_at"] <= record["finished_at"]
    assert record["duration_s"] > 0
    assert record["usage"] == {"tokens": 7}
    assert record["result_sha256"] == hashlib.sha256(b"literal final response").hexdigest()
    assert (sandbox.tasks / "logs" / f"{task[0]}.stderr.log").read_text() == "stub stderr\n"
    assert not {"resolved_model", "resolved_model_known", "resolved_model_source"} & record.keys()
    assert (sandbox.tasks / f"{task[0]}.json").stat().st_mode & 0o777 == 0o600
    assert Path(record["prompt_file"]).stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("models", [[], ["Grok 4.7 256K High"], ["Grok 4.7 256K High", "different"]])
def test_cursor_v2_record_never_attests_a_model_the_runtime_did_not_report(sandbox, monkeypatch, models, mode):
    from scripts.review import record_cf_verdict as recorder

    binary_dir = sandbox.repo.parent / "bin"
    binary_dir.mkdir()
    executable = binary_dir / "cursor-agent"
    events = [{"type": "system", "subtype": "init", "model": model} for model in models]
    events.append({"type": "result", "subtype": "success", "result": "VERDICT: APPROVE"})
    stdout = "\n".join(json.dumps(event) for event in events)
    executable.write_text(f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nprint({stdout!r})\n")
    executable.chmod(0o755)
    sandbox.env["PATH"] = str(binary_dir) + os.pathsep + os.defpath
    sandbox.env["CURSOR_API_KEY"] = "stub-process-key"
    run_git(sandbox.repo, "branch", "review-source")
    dispatched = sandbox.cli(
        "dispatch",
        "--agent",
        "grok",
        "--model",
        "requested-model-is-not-proof",
        "--prompt",
        "The prompt claims Grok 4.7 256K High",
        "--mode",
        mode,
        "--branch",
        "review-source",
    )
    record = sandbox.settle(dispatched.stdout.splitlines(), expected=0 if mode == "read-only" else 1)
    known = len(models) == 1
    assert record["schema_version"] == 2
    assert record["model"] == "requested-model-is-not-proof"
    assert record["resolved_model"] == ("Grok 4.7 256K High" if known else "unknown")
    assert record["resolved_model_known"] is known
    assert record["resolved_model_source"] == ("cursor-stream-json" if known else "pending")
    if mode == "read-only":

        def stop_before_forge(*_args):
            raise recorder.RecordError("synthetic stop before forge")

        monkeypatch.setattr(recorder, "_pr", stop_before_forge)
        reason = "synthetic stop before forge" if known else "Cursor reviewer model unknown"
        with pytest.raises(recorder.RecordError, match=reason):
            recorder.record(record["task_id"], task_root=sandbox.tasks, lock_root=sandbox.tasks / "locks")


@pytest.mark.parametrize(
    ("model", "state", "code"),
    [("fail", "failed", 17), ("error", "failed", 0), ("empty", "failed", 0), ("crash", "crashed", -9)],
)
def test_nonzero_error_empty_and_signal_cannot_report_done(sandbox, model, state, code):
    record = sandbox.settle(sandbox.dispatch(model), expected=1)
    assert record["status"] == state
    assert record["returncode"] == code


def test_provider_final_file_and_exact_stdin_bytes(sandbox):
    result = sandbox.cli(
        "dispatch", "--agent", "codex", "--model", "file", "--prompt-file", "-", stdin="exact\nbytes\n"
    )
    record = sandbox.settle(result.stdout.splitlines())
    assert Path(record["result_file"]).read_bytes() == b"exact\nbytes\n"
    assert record["prompt_sha256"] == hashlib.sha256(b"exact\nbytes\n").hexdigest()


@pytest.mark.parametrize("text,model,required,error", [
    ("\nReview details\nVERDICT: APPROVE\n  \t", "file", True, None),
    ("VERDICT: REQUEST_CHANGES", "echo", True, None),
    ("VERDICT: APPROVE\nVERDICT: APPROVE", "echo", True, None),
    ("Review has no decision", "echo", True, "review_missing_verdict_line"),
    ("VERDICT: APPROVE\nVERDICT: REQUEST_CHANGES", "echo", True, "review_ambiguous_verdict"),
    ("> VERDICT: APPROVE\nI might report VERDICT: APPROVE later", "echo", True,
     "review_missing_verdict_line"),
    ("VERDICT: APPROVE", "fail", True, "provider exited unsuccessfully"),
    ("Review has no decision", "fail", True, "provider exited unsuccessfully"),
    ("Review has no decision", "echo", False, None),
])
def test_review_gate_prevents_false_completion_and_preserves_results(sandbox, text, model, required, error):
    """Defect classes: false completion, failure promotion, result corruption and opt-in leakage."""
    # Use the production shared parser and its dependencies in the disposable CLI repo.
    stub_common_reaper(sandbox)
    (sandbox.repo / "scripts/fleet/__init__.py").touch()
    (sandbox.repo / "scripts/__init__.py").write_text(f"__path__.append({str(SOURCE / 'scripts')!r})\n")
    dispatched = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", model, "--prompt", text,
        *(["--require-review-verdict"] if required else []),
    )
    task = dispatched.stdout.splitlines()
    record = sandbox.settle(task, expected=1 if error else 0)
    assert record["status"] == ("failed" if error else "done")
    assert record["error"] == error
    assert record["returncode"] == (17 if model == "fail" else 0)
    assert Path(record["result_file"]).read_bytes() == text.encode()
    assert record["result_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert json.loads(sandbox.cli("status", task[0]).stdout)["status"] == record["status"]
    assert json.loads(sandbox.cli("list", "--status", record["status"]).stdout)[0]["task_id"] == task[0]


def test_review_gate_exception_cannot_leave_supervisor_running(sandbox):
    """Defect class: scanner exceptions lose terminal failure or expose exception contents."""
    review = sandbox.repo / "scripts/review"
    review.mkdir(exist_ok=True)
    (review / "__init__.py").touch()
    (review / "verdict_parser.py").write_text(
        "def recognized_verdicts(text):\n    raise RuntimeError('sensitive scanner diagnostic')\n"
    )
    record = sandbox.settle(sandbox.dispatch("echo", "--require-review-verdict"), expected=1)
    assert record["status"] == "failed"
    assert record["error"] == "review_gate_error"
    assert record["returncode"] == 0
    assert record["finished_at"] is not None
    assert Path(record["result_file"]).read_text() == "literal final response"
    assert "sensitive scanner diagnostic" not in json.dumps(record)


def test_nonce_refuses_status_wait_and_cancel(sandbox):
    task = sandbox.dispatch("blocked")
    await_file(sandbox.tasks / f"{task[0]}.started")
    for command in ("status", "wait", "cancel"):
        result = sandbox.cli(command, task[0], "--run-nonce", "stale", expected=2)
        assert result.stderr == "dispatcher: run nonce mismatch\n"
    assert json.loads(sandbox.cli("status", task[0], "--run-nonce", task[1]).stdout)["status"] == "running"
    sandbox.cli("cancel", task[0], "--run-nonce", task[1])


def test_cancel_kills_child_process_group(sandbox):
    task = sandbox.dispatch("tree")
    child = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    grandchild = int(await_file(sandbox.tasks / f"{task[0]}.grandchild"))
    record = json.loads(sandbox.cli("cancel", task[0], "--run-nonce", task[1]).stdout)
    assert record["status"] == "cancelled"
    assert worker._identity(child) is None
    assert worker._identity(grandchild) is None


def test_deadline_settles_as_timeout(sandbox):
    task = sandbox.dispatch("blocked", "--hard-timeout", "0.2")
    record = sandbox.settle(task, expected=1)
    assert record["status"] == "timeout"
    assert record["returncode"] == -9


def test_immediate_cancel_and_duplicate_id_do_not_leave_a_second_run(sandbox):
    task = sandbox.dispatch("blocked", "--task-id", "one-run")
    cancelled = json.loads(sandbox.cli("cancel", task[0], "--run-nonce", task[1]).stdout)
    assert cancelled["status"] == "cancelled"
    branches = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--task-id", "one-run", expected=2
    )
    assert result.stderr == "dispatcher: task id already exists; choose a new task id\n"
    assert run_git(sandbox.repo, "branch", "--list") == branches
    assert json.loads((sandbox.tasks / "one-run.json").read_text())["run_nonce"] == task[1]


def test_supervisor_crash_is_reconciled_without_claiming_success(sandbox):
    task = sandbox.dispatch("blocked")
    child = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    record = json.loads(sandbox.cli("status", task[0]).stdout)
    os.kill(record["pid"], signal.SIGKILL)
    # The provider remains separately identifiable for test cleanup after a supervisor SIGKILL.
    os.killpg(child, signal.SIGKILL)
    record = sandbox.settle(task, expected=1)
    assert record["status"] == "crashed"
    assert record["finished_at"]


def test_concurrent_dispatches_use_distinct_records(sandbox):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        tasks = list(pool.map(lambda _: sandbox.dispatch(), range(2)))
    assert len({task[0] for task in tasks}) == 2
    assert len({task[1] for task in tasks}) == 2
    assert all(sandbox.settle(task)["status"] == "done" for task in tasks)


@pytest.mark.parametrize(
    ("model", "push_state", "ahead", "dirty"),
    [
        ("pushed", "pushed", 1, False),
        ("unpushed", "unpushed", 1, False),
        ("dirty", "unpushed", 0, True),
    ],
)
def test_delivery_observes_actual_remote_and_dirty_worktree(sandbox, model, push_state, ahead, dirty):
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write"), expected=0 if model == "pushed" else 1)
    assert record["push_state"] == push_state
    assert record["commits_ahead"] == ahead
    assert record["worktree_dirty_on_exit"] is dirty
    assert record["head_sha"] == run_git(Path(record["cwd"]), "rev-parse", "HEAD")
    if push_state == "pushed":
        assert (
            record["remote_head_sha"]
            == run_git(sandbox.repo, "ls-remote", "origin", f"refs/heads/{record['worktree_branch']}").split()[0]
        )
        # A stale tracking ref must not be mistaken for the actual remote branch.
        run_git(sandbox.remote, "update-ref", "-d", f"refs/heads/{record['worktree_branch']}")
        probe = TaskSpec(
            record["task_id"],
            "codex",
            "echo",
            None,
            "workspace-write",
            Path(record["cwd"]),
            Path(record["prompt_file"]),
            Path(record["result_file"]),
        )
        observed = git.snapshot_delivery(probe, record)
        assert observed["push_state"] == "unpushed"
        run_git(probe.worktree, "remote", "set-url", "origin", str(sandbox.tasks / "missing-remote"))
        assert (
            git.snapshot_delivery(probe, record)["push_state"]
            == "unknown"
        )


@pytest.mark.parametrize("model,mode,owned,state,cause", [
    ("pushed", "workspace-write", ["other/"], "no_deliverable", "outside_owned_paths: delivered.txt"),
    ("pushed", "workspace-write", ["delivered.txt"], "done", None),
    ("pushed-nested", "workspace-write", ["src/*.txt"], "done", None),
    ("pushed", "workspace-write", ["delivered"], "no_deliverable", "outside_owned_paths: delivered.txt"),
    ("pushed-nested", "workspace-write", ["src/"], "done", None),
    ("pushed-dirty", "workspace-write", [], "no_deliverable", "worktree_dirty_or_unknown"),
    ("echo", "read-only", ["other/"], "done", None),
    ("dirty", "read-only", ["other/"], "done", None),
    ("pushed", "read-only", ["other/"], "done", None),
])
def test_settle_rejects_out_of_scope_or_unpublished_write_delivery(sandbox, model, mode, owned, state, cause):
    """A provider's successful response cannot hide scope violations or undelivered work."""
    flags = [flag for path in owned for flag in ("--owned-path", path)]
    record = sandbox.settle(sandbox.dispatch(model, "--mode", mode, *flags), expected=0 if state == "done" else 1)
    assert record["status"] == state
    assert record["owned_paths"] == owned
    assert record["research_owned_paths"] == []
    assert record["error"] == cause
    assert record.get("no_deliverable_reason") == cause
    assert record["returncode"] == 0
    assert Path(record["result_file"]).read_text() == "literal final response"


def test_v2_record_without_owned_paths_remains_readable(sandbox):
    record = sandbox.settle(sandbox.dispatch())
    record.pop("owned_paths", None)
    (sandbox.tasks / f"{record['task_id']}.json").write_text(json.dumps(record))
    assert json.loads(sandbox.cli("status", record["task_id"]).stdout)["status"] == "done"


@pytest.fixture
def delivery_settle(sandbox):
    run_git(sandbox.repo, "push", "origin", "main:release")
    record = sandbox.settle(sandbox.dispatch("echo", "--base", "origin/release"))
    # Finish the initial reaper's record write before reusing this run for settle probes.
    deadline = time.monotonic() + 10
    path = sandbox.tasks / f"{record['task_id']}.json"
    while "reap_note" not in json.loads(path.read_text()):
        assert time.monotonic() < deadline, "initial reaper did not finish"
        time.sleep(0.02)
    # Synthetic write records need the trusted remote omitted from read-only dispatches.
    record["worktree_remote_url"] = str(sandbox.remote)
    def settle(model="echo", owned=("delivered.txt",)):
        record.update(mode="workspace-write", model=model, status="running", owned_paths=list(owned or []))
        if owned is None:
            record.pop("owned_paths")
        path = sandbox.tasks / f"{record['task_id']}.json"
        path.write_text(json.dumps(record))
        subprocess.run([
            sys.executable, "-c", "import sys; from pathlib import Path; "
            "from scripts.dispatcher.worker import supervise; "
            "supervise(Path(sys.argv[1]), {}, 0.2 if sys.argv[2] == 'blocked' else 10)", str(path), model,
        ], cwd=sandbox.repo, env=sandbox.env, check=True, timeout=30)
        return json.loads(path.read_text())
    return record, settle


@pytest.mark.parametrize("owned", [None, []])
@pytest.mark.parametrize("model,cause", [
    ("pushed", None), ("dirty", "worktree_dirty_or_unknown"),
    ("unpushed", "work_not_pushed_or_unknown"), ("echo", "no_commits_or_unknown"),
])
def test_write_settle_without_ownership(delivery_settle, owned, model, cause):
    _, settle = delivery_settle
    result = settle(model, owned)
    assert result["status"] == ("no_deliverable" if cause else "done")
    assert result["error"] == cause
    assert ("owned_paths" in result) is (owned is not None)


@pytest.mark.parametrize("model,status,error", [
    ("fail", "failed", "provider exited unsuccessfully"),
    ("cancel", "cancelled", "cancelled by client"),
    ("blocked", "timeout", "process deadline exceeded"),
    ("crash", "crashed", "provider exited unsuccessfully"),
])
def test_unsuccessful_settle_preserves_cause_with_outside_commit(delivery_settle, model, status, error):
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    (tree / "outside.txt").write_text("outside\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "outside scope")
    result = settle(model)
    assert (result["status"], result["error"]) == (status, error)
    assert "no_deliverable_reason" not in result


@pytest.mark.parametrize("history", ["merged", "restored", "rename-in", "rename-out", "deleted"])
def test_scope_checks_each_own_commit(sandbox, delivery_settle, history, monkeypatch):
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    if history == "merged":
        run_git(tree, "commit", "--allow-empty", "-m", "worker before upstream")
    if history != "restored":
        source = "delivered.txt" if history == "rename-out" else "outside.txt"
        (sandbox.repo / source).write_text("upstream\n")
        run_git(sandbox.repo, "add", source)
        run_git(sandbox.repo, "commit", "-m", "upstream")
        run_git(sandbox.repo, "push", "origin", "main:release")
        run_git(tree, "merge", "--no-edit", "main")
    if history.startswith("rename"):
        run_git(tree, "mv", source, "delivered.txt" if history == "rename-in" else "outside.txt")
    elif history == "deleted":
        run_git(tree, "rm", "outside.txt")
    else:
        (tree / "delivered.txt").write_text("delivery\n")
        if history == "restored":
            (tree / "outside.txt").write_text("outside\n")
            run_git(tree, "add", ".")
            run_git(tree, "commit", "-m", "temporary outside path")
            run_git(tree, "rm", "outside.txt")
    run_git(tree, "add", ".")
    run_git(tree, "commit", "-m", "worker delivery")
    run_git(tree, "push", "origin", "HEAD")
    result = settle()
    if history == "rename-in":
        # Force rename detection before the guard's explicit --no-renames override.
        original = git._verification_git
        monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                            original(path, command, *(("-M",) if command == "log" else ()), *args, **kw))
        result["status"] = "done"
        worker._enforce_delivery(result)
    assert result["status"] == ("done" if history == "merged" else "no_deliverable")
    assert result["error"] == (None if history == "merged" else "outside_owned_paths: outside.txt")


@pytest.mark.parametrize("status", ["done", "failed", "cancelled", "timeout", "crashed"])
@pytest.mark.parametrize("command", ["fetch", "merge-base", "version", "rev-list", "log"])
def test_scope_verification_failure_only_rejects_success(delivery_settle, monkeypatch, status, command):
    record, settle = delivery_settle
    record = settle("pushed")
    record.update(status=status, error="original cause")
    original = git._verification_git
    def broken(path, *args, **kwargs):
        if args[0] == command:
            raise subprocess.CalledProcessError(1, ["git", command])
        return original(path, *args, **kwargs)
    monkeypatch.setattr(git, "_verification_git", broken)
    worker._enforce_delivery(record)
    assert record["status"] == ("no_deliverable" if status == "done" else status)
    assert record["error"] == ("owned_paths_verification_failed" if status == "done" else "original cause")


@pytest.mark.parametrize("history", ["conflict", "no-commit", "unrelated", "parentless", "clean"])
def test_merge_resolution_and_root_paths_cannot_escape_scope(sandbox, delivery_settle, history, monkeypatch):
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    branch = record["worktree_branch"]
    if history in {"unrelated", "parentless"}:
        run_git(tree, "checkout", "--orphan", "new-root")
        run_git(tree, "read-tree", "--empty")
        (tree / "outside.txt").write_text("root addition\n")
        run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "-m", "parentless outside addition")
        if history == "unrelated":
            run_git(tree, "checkout", branch)
            run_git(tree, "merge", "--allow-unrelated-histories", "--no-edit", "new-root")
        else:
            # Keep the parentless commit as HEAD's first-parent ancestor.
            run_git(tree, "merge", "--allow-unrelated-histories", "--no-edit", branch)
            run_git(tree, "branch", "-f", branch, "HEAD")
            run_git(tree, "checkout", branch)
    else:
        (sandbox.repo / "outside.txt").write_text("upstream\n")
        run_git(sandbox.repo, "add", "outside.txt")
        run_git(sandbox.repo, "commit", "-m", "upstream outside path")
        if history == "conflict":
            (tree / "outside.txt").write_text("worker conflict\n")
            run_git(tree, "add", "outside.txt")
            run_git(tree, "commit", "-m", "worker side")
            # This models a commit already present at dispatch. Only the merge is new.
            record["worktree_base_sha"] = run_git(tree, "rev-parse", "HEAD")
        else:
            run_git(tree, "commit", "--allow-empty", "-m", "worker side")
        merge = subprocess.run(["git", "-C", str(tree), "merge", "--no-commit", "main"],
                               capture_output=True, text=True, timeout=30)
        assert merge.returncode == (1 if history == "conflict" else 0)
        if history != "clean":
            (tree / "outside.txt").write_text("worker merge edit\n")
            run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "--no-edit")
    run_git(sandbox.repo, "push", "origin", "main:release")
    # A new owned commit makes the supervisor exercise delivery after the merge.
    result = settle("pushed")
    assert result["status"] == ("done" if history == "clean" else "no_deliverable")
    assert result["error"] == (None if history == "clean" else "outside_owned_paths: outside.txt")
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "git version 2.35.0" if command == "version" else original(path, command, *args, **kw))
    result.update(status="done", error=None)
    worker._enforce_delivery(result)
    assert (result["status"], result["error"]) == ("no_deliverable", "owned_paths_verification_failed")


@pytest.mark.parametrize("reuse_cwd", [False, True])
def test_preexisting_branch_commits_are_not_attributed_to_new_task(sandbox, reuse_cwd, monkeypatch):
    if reuse_cwd:
        initial = sandbox.settle(sandbox.dispatch())
        tree = Path(initial["cwd"])
        flags = ["--cwd", str(tree)]
    else:
        tree = sandbox.repo
        run_git(tree, "checkout", "-b", "feature-x")
        flags = ["--branch", "feature-x"]
    (tree / "outside.txt").write_text("previous task\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "preexisting outside scope")
    starting_head = run_git(tree, "rev-parse", "HEAD")
    result = sandbox.settle(sandbox.dispatch("pushed", "--mode", "workspace-write",
                                            "--owned-path", "delivered.txt", *flags))
    assert result["worktree_base_sha"] == starting_head
    assert (result["status"], result["error"]) == ("done", None)
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "git version 2.35.0" if command == "version" else original(path, command, *args, **kw))
    worker._enforce_delivery(result)
    assert (result["status"], result["error"]) == ("done", None)


def test_scope_error_is_bounded_and_local_base_fails_closed(delivery_settle, monkeypatch):
    record, settle = delivery_settle
    record = settle("pushed")
    original = git._verification_git
    monkeypatch.setattr(git, "_verification_git", lambda path, command, *args, **kw:
                        "\0".join(f"outside-{n:04d}.txt" for n in range(200)) if command == "log"
                        else original(path, command, *args, **kw))
    worker._enforce_delivery(record)
    assert record["status"] == "no_deliverable"
    assert record["error"].startswith("outside_owned_paths: outside-0000.txt")
    assert len(record["error"]) <= 1024
    assert record["error"].endswith("... (truncated)")
    record.update(status="done", worktree_base_ref="main")
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("no_deliverable", "owned_paths_verification_failed")


@pytest.mark.parametrize("transport", ["ssh", "https"])
def test_canonical_origins_does_not_reject_same_identity_when_clone_transport_differs(transport):
    """Clone transport mismatches must not reject the registered repository identity."""
    origins = git.canonical_origins({"github": "org/repo", "transport": transport})
    assert "https://github.com/org/repo.git" in origins
    accepted = {
        "https://github.com/org/repo.git", "https://github.com/org/repo",
        "git@github.com:org/repo.git", "git@github.com:org/repo",
        "ssh://git@github.com/org/repo.git", "ssh://git@github.com/org/repo",
    }
    assert set(origins) == accepted
    assert len(origins) == len(accepted)
    refused = [
        "https://github.com/org/other.git", "git@github.com:org/other.git", "https://github.com/org/rep.git",
        "https://github.com/org/repo-fork.git", "https://github.com/someone/repo.git", "git@github.com:someone/repo.git",
        "https://gitlab.com/org/repo.git", "git@gitlab.com:org/repo.git", "ssh://git@example.com/org/repo.git",
        "/srv/org/repo.git", "file:///srv/org/repo.git", "https://user:token@github.com/org/repo.git",
        "https://token@github.com/org/repo.git", "ssh://user:token@github.com/org/repo.git",
        "https://github.com/Org/repo.git", "https://GitHub.com/org/repo.git", "git@github.com:org/Repo.git",
        "https://github.com/org/repo/", "https://github.com/org/repo.git/", "git@github.com:org/repo.git/",
        "https://github.com/org/repo.git.bak", "git@github.com:org/repo.gitx", "https://github.com/org/repo.git/extra",
        " https://github.com/org/repo.git", "\tgit@github.com:org/repo.git", "https://github.com/org/repo.git\n",
    ]
    for origin in refused:
        assert origin not in origins


def test_prior_worker_origin_poisoning_refuses_dispatch_and_fails_closed(sandbox):
    """Shared config poisoned before dispatch cannot certify a forged empty range."""
    earlier = sandbox.settle(sandbox.dispatch("unpushed", "--mode", "workspace-write"), expected=1)
    fake = sandbox.repo.parent / "forged.git"
    tree = Path(earlier["cwd"])
    run_git(tree, "clone", "--bare", str(sandbox.remote), str(fake))
    run_git(tree, "remote", "set-url", "origin", str(fake))
    result = sandbox.cli(
        "dispatch", "--agent", "sol", "--model", "pushed", "--prompt", "deliver",
        "--task-id", "poisoned", "--mode", "workspace-write", "--owned-path", "delivered.txt", expected=2,
    )
    assert "origin must match the registered canonical repository URL" in result.stderr
    assert not (sandbox.tasks / "poisoned.json").exists()
    assert not (sandbox.tasks / "poisoned.started").exists()
    # Read-only admission still records missing trust; even a later write settle fails closed.
    record = sandbox.settle(sandbox.dispatch())
    assert record["worktree_remote_url"] is None
    tree = Path(record["cwd"])
    for name in ("outside.txt", "delivered.txt"):
        (tree / name).write_text("forged delivery\n")
    run_git(tree, "add", "outside.txt", "delivered.txt")
    run_git(tree, "commit", "-m", "forged delivery")
    run_git(tree, "push", "origin", "HEAD", "HEAD:main")
    record.update(
        mode="workspace-write", owned_paths=["delivered.txt"], head_sha=run_git(tree, "rev-parse", "HEAD"),
        push_state="pushed", commits_ahead=1, worktree_dirty_on_exit=False,
    )
    assert run_git(fake, "rev-parse", "main") == record["head_sha"]
    assert run_git(sandbox.remote, "rev-parse", "main") == record["worktree_base_sha"]
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("no_deliverable", "owned_paths_verification_failed")


@pytest.mark.parametrize("attack", ["alias-shell", "alias-empty", "replace", "origin", "insteadOf", "pushInsteadOf"])
def test_worker_git_state_cannot_hide_outside_commit(sandbox, delivery_settle, attack):
    """Worker aliases, replacements and remote rewrites cannot certify owned delivery."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    (tree / "outside.txt").write_text("outside scope\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "outside scope")
    record = settle("pushed")
    assert record["error"] == "outside_owned_paths: outside.txt"
    if attack.startswith("alias"):
        run_git(tree, "config", "alias.log", "!true" if attack == "alias-shell" else "log -n 0")
    elif attack == "replace":
        clean_tree = run_git(tree, "rev-parse", f"{record['worktree_base_sha']}^{{tree}}")
        replacement = run_git(tree, "commit-tree", clean_tree, "-p", record["worktree_base_sha"], "-m", "clean")
        run_git(tree, "replace", record["head_sha"], replacement)
        assert run_git(tree, "log", "-1", "--format=", "--name-only") == ""
    else:
        fake = sandbox.repo.parent / "forged.git"
        run_git(tree, "clone", "--bare", str(tree), str(fake))
        run_git(fake, "update-ref", "refs/heads/release", record["head_sha"])
        if attack == "origin":
            run_git(tree, "remote", "set-url", "origin", str(fake))
        else:
            run_git(tree, "config", f"url.{fake}.{attack}", str(sandbox.remote))
    record.update(status="done", error=None)
    worker._enforce_delivery(record)
    expected = "outside_owned_paths: outside.txt" if attack == "replace" else "owned_paths_verification_failed"
    assert (record["status"], record["error"]) == ("no_deliverable", expected)


def test_ownership_walk_verifies_distinct_publish_branch(sandbox, delivery_settle):
    """Publish-branch confusion must neither reject owned delivery nor hide outside paths."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    record["publish_branch"] = "fix/published"
    delivery_ref = f"refs/heads/{record['publish_branch']}"
    (tree / "delivered.txt").write_text("owned delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "owned delivery")
    run_git(tree, "push", "origin", f"HEAD:{delivery_ref}")
    assert run_git(sandbox.remote, "for-each-ref", f"refs/heads/{record['worktree_branch']}") == ""
    delivered = settle()
    assert delivered["remote_ref"] == delivery_ref
    assert (delivered["status"], delivered["error"]) == ("done", None)
    (tree / "outside.txt").write_text("outside scope\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "outside scope")
    run_git(tree, "push", "origin", f"HEAD:{delivery_ref}")
    rejected = settle()
    assert rejected["remote_ref"] == delivery_ref
    assert (rejected["status"], rejected["error"]) == ("no_deliverable", "outside_owned_paths: outside.txt")


@pytest.mark.parametrize("publish_branch", ["release", "fix/published"])
def test_ownership_walk_requires_distinct_refs_and_nonempty_range(sandbox, delivery_settle, publish_branch):
    """Equal delivery/base refs and empty inspected ranges fail ownership verification."""
    record, settle = delivery_settle
    tree = Path(record["cwd"])
    record["publish_branch"] = publish_branch
    (tree / "outside.txt").write_text("scope fixture\n")
    run_git(tree, "add", "outside.txt")
    run_git(tree, "commit", "-m", "scope fixture")
    refs = list(dict.fromkeys(("refs/heads/release", f"refs/heads/{publish_branch}")))
    run_git(tree, "push", "origin", *(f"HEAD:{ref}" for ref in refs))
    rejected = settle()
    assert rejected["remote_ref"] == f"refs/heads/{publish_branch}"
    assert rejected["commits_ahead"] == 1
    assert (rejected["status"], rejected["error"]) == ("no_deliverable", "owned_paths_verification_failed")


def test_ownership_walk_ignores_worker_config_includes_and_ambient_git_env(sandbox, delivery_settle, monkeypatch):
    """Local/worktree includes and injected process config cannot alter the private walk."""
    record, settle = delivery_settle
    record = settle("pushed")
    tree = Path(record["cwd"])
    included = sandbox.repo.parent / "included.config"
    included.write_text("[worker]\n included = untrusted\n")
    for scope in ("--local", "--worktree"):
        run_git(tree, "config", scope, "worker.marker", "untrusted")
        run_git(tree, "config", scope, "include.path", str(included))
    global_config = sandbox.repo.parent / "global.config"
    global_config.write_text("[worker]\n global = untrusted\n[alias]\n log = !true\n")
    for key, value in {
        "GIT_CONFIG_GLOBAL": str(global_config), "GIT_CONFIG_SYSTEM": str(global_config),
        "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "alias.log", "GIT_CONFIG_VALUE_0": "!true",
        "GIT_CONFIG_PARAMETERS": "'alias.log=log -n 0'", "GIT_DIR": str(sandbox.remote),
        "GIT_CONFIG": str(global_config), "GIT_REPLACE_REF_BASE": "refs/heads/",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("TMPDIR", raising=False)
    with git.ownership_git(record) as run:
        config = run("config", "--list", "--includes")
        assert "worker." not in config
        assert "alias." not in config
        assert run("rev-parse", "refs/heads/delivery") == record["head_sha"]
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("done", None)


@pytest.mark.parametrize("shape", ["linear", "merge"])
def test_ownership_walk_does_not_fetch_full_history(tmp_path, monkeypatch, shape):
    """A multi-gigabyte remote must not be fetched whole: only blob-less history since the task base.

    A delivery containing a merge is the exception: re-running a merge needs the complete ancestry
    of its parents. The merge shape has a common ancestor older than the bounded window, and the
    walk must obtain non-shallow history and apply the ownership rules to it.
    """
    remote, tree = tmp_path / "remote.git", tmp_path / "tree"
    run_git(tmp_path, "init", "--bare", str(remote))
    run_git(remote, "config", "uploadpack.allowFilter", "true")
    run_git(tmp_path, "init", "-b", "main", str(tree))
    run_git(tree, "config", "user.email", "stub@example.invalid")
    run_git(tree, "config", "user.name", "Stub")
    run_git(tree, "remote", "add", "origin", str(remote))
    old_commits, old_blobs = set(), set()
    for n in range(20):
        monkeypatch.setenv("GIT_COMMITTER_DATE", f"2020-01-{n + 1:02d}T00:00:00Z")
        (tree / f"old-{n}.txt").write_text(f"old history {n}\n")
        run_git(tree, "add", ".")
        run_git(tree, "commit", "-m", f"old history {n}")
        commit, blob = run_git(tree, "rev-parse", "HEAD", f"HEAD:old-{n}.txt").split()
        old_commits.add(commit)
        old_blobs.add(blob)
    if shape == "merge":
        (tree / "outside.txt").write_text("outside\n")
        run_git(tree, "add", "outside.txt")
        run_git(tree, "commit", "-m", "A")
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    if shape == "linear":
        run_git(tree, "commit", "--allow-empty", "-m", "task base")
        run_git(tree, "push", "origin", "main")
        run_git(tree, "checkout", "-b", "sol/fetch")
    else:
        # A is older than the bounded window; P and Q are newer and share only A as an ancestor.
        # B = merge(P, Q) is the task base.
        run_git(tree, "checkout", "-b", "q")
        (tree / "q.txt").write_text("q\n")
        run_git(tree, "add", "q.txt")
        run_git(tree, "commit", "-m", "Q")
        run_git(tree, "checkout", "main")
        run_git(tree, "rm", "outside.txt")
        run_git(tree, "commit", "-m", "P")
        run_git(tree, "merge", "--no-ff", "-m", "task base", "q")
        run_git(tree, "push", "origin", "main")
        # The delivery branch has two merges above the task base: D of P and Q, then F of B into D.
        run_git(tree, "checkout", "-b", "sol/fetch", "main^1")
        run_git(tree, "merge", "--no-ff", "--no-commit", "q")
        run_git(tree, "checkout", "main^1^1", "--", "outside.txt")
        run_git(tree, "commit", "-m", "D")
        run_git(tree, "merge", "--no-commit", "main")
        run_git(tree, "rm", "outside.txt")
        run_git(tree, "commit", "-m", "F")
    (tree / "delivered.txt").write_text("delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "delivery")
    run_git(tree, "push", "origin", "HEAD")
    base, head = run_git(tree, "rev-parse", "main", "HEAD").split()
    record = dict(
        task_id="fetch", worktree_path=str(tree), worktree_remote_url=str(remote),
        worktree_base_ref="refs/remotes/origin/main", worktree_base_sha=base, worktree_branch="sol/fetch",
        head_sha=head, mode="workspace-write", status="done", owned_paths=["delivered.txt"],
        worktree_dirty_on_exit=False, commits_ahead=1, push_state="pushed",
    )
    with git.ownership_git(record) as run:
        present = set(run("cat-file", "--batch-all-objects", "--batch-check=%(objectname)").split())
        shallow = run("rev-parse", "--is-shallow-repository")
    assert {base, head} <= present
    assert old_blobs.isdisjoint(present)
    assert run_git(tree, "rev-parse", "HEAD:delivered.txt") not in present
    if shape == "linear":
        assert shallow == "true"
        assert old_commits.isdisjoint(present)
        expected = ("done", None)
    else:
        assert shallow == "false"
        expected = ("no_deliverable", "outside_owned_paths: outside.txt")
    worker._enforce_delivery(record)
    assert (record["status"], record.get("error")) == expected


def test_ownership_walk_falls_back_to_full_history_when_tips_predate_skewed_task_base(tmp_path, monkeypatch):
    """Clock skew: a future-dated task base must not reject a valid delivery.

    With both remote tips dated before the cutoff, Git selects no commits for --shallow-since and
    aborts the bounded fetch. The walk must take the full-history fallback and apply the ownership
    rules to it.
    """
    remote, tree = tmp_path / "remote.git", tmp_path / "tree"
    run_git(tmp_path, "init", "--bare", str(remote))
    run_git(remote, "config", "uploadpack.allowFilter", "true")
    run_git(tmp_path, "init", "-b", "main", str(tree))
    run_git(tree, "config", "user.email", "stub@example.invalid")
    run_git(tree, "config", "user.name", "Stub")
    run_git(tree, "remote", "add", "origin", str(remote))
    for date, message in (("2020-01-01", "old history"), ("2099-01-01", "task base")):
        monkeypatch.setenv("GIT_COMMITTER_DATE", f"{date}T00:00:00Z")
        monkeypatch.setenv("GIT_AUTHOR_DATE", f"{date}T00:00:00Z")
        run_git(tree, "commit", "--allow-empty", "-m", message)
    base = run_git(tree, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2020-02-01T00:00:00Z")
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2020-02-01T00:00:00Z")
    run_git(tree, "commit", "--allow-empty", "-m", "base branch moves on")
    run_git(tree, "push", "origin", "main")
    run_git(tree, "checkout", "-b", "sol/skew", base)
    (tree / "delivered.txt").write_text("delivery\n")
    run_git(tree, "add", "delivered.txt")
    run_git(tree, "commit", "-m", "delivery")
    run_git(tree, "push", "origin", "HEAD")
    head = run_git(tree, "rev-parse", "HEAD")
    since = int(run_git(tree, "show", "-s", "--format=%ct", base)) - git.HISTORY_SLACK_SECONDS
    probe = tmp_path / "probe.git"
    run_git(tmp_path, "init", "--bare", str(probe))
    rejected = subprocess.run(["git", "-C", str(probe), "fetch", f"--shallow-since=@{since}", str(remote),
                               "main", "sol/skew"], capture_output=True, text=True, timeout=30)
    assert "no commits selected for shallow requests" in rejected.stderr

    def record(owned):
        return dict(
            task_id="skew", worktree_path=str(tree), worktree_remote_url=str(remote),
            worktree_base_ref="refs/remotes/origin/main", worktree_base_sha=base, worktree_branch="sol/skew",
            head_sha=head, mode="workspace-write", status="done", owned_paths=owned,
            worktree_dirty_on_exit=False, commits_ahead=1, push_state="pushed",
        )

    with git.ownership_git(record(["delivered.txt"])) as run:
        assert run("rev-parse", "--is-shallow-repository") == "false"
    for owned, expected in ((["delivered.txt"], ("done", None)),
                            (["other.txt"], ("no_deliverable", "outside_owned_paths: delivered.txt"))):
        settled = record(owned)
        worker._enforce_delivery(settled)
        assert (settled["status"], settled.get("error")) == expected


@pytest.mark.parametrize("missing", ["worktree_remote_url", "git-binary", "scratch", "remote-tip"])
def test_missing_ownership_protection_fails_closed(delivery_settle, monkeypatch, missing):
    record, settle = delivery_settle
    record = settle("pushed")
    if missing == "git-binary":
        monkeypatch.setattr(git, "GIT_BINARY", None)
    elif missing == "scratch":
        monkeypatch.setattr(git, "allocate", Mock(side_effect=worker.TaskScratchError("unavailable")))
    elif missing == "remote-tip":
        record["head_sha"] = "0" * 40
    else:
        record.pop(missing)
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("no_deliverable", "owned_paths_verification_failed")


@pytest.mark.parametrize("remote_available", [True, False])
def test_delivery_dirty_same_head_cannot_report_pushed_or_unknown(sandbox, remote_available):
    """Uncommitted work is unpushed even when HEAD matches origin or origin cannot be read."""
    record = sandbox.settle(sandbox.dispatch("pushed", "--mode", "workspace-write"))
    worktree = Path(record["cwd"])
    (worktree / "delivered.txt").write_text("uncommitted delivery\n")
    if not remote_available:
        run_git(worktree, "remote", "set-url", "origin", str(sandbox.tasks / "missing-remote"))
    probe = TaskSpec(
        record["task_id"],
        "codex",
        "echo",
        None,
        "workspace-write",
        worktree,
        Path(record["prompt_file"]),
        Path(record["result_file"]),
    )
    assert git.snapshot_delivery(probe, record) == {
        "head_sha": record["head_sha"],
        "remote_head_sha": record["head_sha"] if remote_available else None,
        "remote_ref": f"refs/heads/{record['worktree_branch']}" if remote_available else None,
        "publish_branch": None,
        "push_state": "unpushed",
        "push_state_reason": "dirty_worktree",
        "commits_ahead": 1,
        "worktree_dirty_on_exit": True,
    }


@pytest.mark.parametrize(
    ("target", "commits", "dirty", "expected", "reason", "crash"),
    [
        ("pinned", 1, False, "pushed", "remote_head_matches", False),
        ("pinned", 1, False, "pushed", "remote_head_matches", True),
        ("own", 1, False, "pushed", "remote_head_matches", False),
        ("unrelated", 1, False, "unpushed", "remote_head_differs", False),
        ("prefix", 1, False, "unpushed", "remote_branch_missing", False),
        ("pinned", 1, True, "unpushed", "dirty_worktree", False),
        (None, 0, False, "unpushed", "remote_branch_missing", False),
        ("pinned", 0, False, "pushed", "remote_head_matches", False),
    ],
)
def test_delivery_only_counts_exact_heads_on_authorized_branches(sandbox, target, commits, dirty, expected, reason, crash):
    """Prefix tricks and supervisor crashes cannot falsify pinned-branch delivery evidence."""
    pinned = "codex/existing-pr"
    run_git(sandbox.repo, "branch", pinned, "main")
    if target not in {None, "prefix"}:
        run_git(sandbox.repo, "push", "origin", pinned)
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--branch", pinned)
    record_path = sandbox.tasks / f"{task[0]}.json"
    record = json.loads(record_path.read_text())
    assert record["publish_branch"] == pinned
    child = int(await_file(Path(record["prompt_file"]).with_suffix(".started")))
    worktree = Path(record["worktree_path"])
    branch = record["worktree_branch"]
    if commits:
        (worktree / "fix.txt").write_text("fix round\n")
        run_git(worktree, "add", "fix.txt")
        run_git(worktree, "commit", "-m", "fix round")
    remote_branch = {
        "pinned": pinned, "own": branch, "unrelated": "codex/unrelated", "prefix": f"x/refs/heads/{pinned}",
    }.get(target)
    if remote_branch:
        run_git(worktree, "push", "origin", f"HEAD:refs/heads/{remote_branch}")
    if dirty:
        (worktree / "uncommitted.txt").write_text("still local\n")
    if crash:
        before_crash = git.snapshot_delivery(worker._spec(record, {}), record)
        assert before_crash["push_state"] == "pushed"
        assert before_crash["remote_ref"] == f"refs/heads/{pinned}"
        os.kill(record["pid"], signal.SIGKILL)
        os.killpg(child, signal.SIGKILL)
    else:
        Path(record["prompt_file"]).with_suffix(".release").touch()
    delivery_error = (
        "worktree_dirty_or_unknown" if dirty else "no_commits_or_unknown" if not commits
        else "work_not_pushed_or_unknown" if expected != "pushed" else None
    )
    observed = sandbox.settle(task, expected=1 if crash or delivery_error else 0)
    assert observed["status"] == ("crashed" if crash else "no_deliverable" if delivery_error else "done")
    if not crash:
        assert observed.get("no_deliverable_reason") == delivery_error
    head = run_git(worktree, "rev-parse", "HEAD")
    matched = remote_branch if target in {"pinned", "own"} else None
    assert observed["push_state"] == expected
    assert observed["push_state_reason"] == reason
    assert observed["publish_branch"] == pinned
    assert observed["remote_ref"] == (f"refs/heads/{matched}" if matched else None)
    if crash:
        assert observed["remote_ref"] == before_crash["remote_ref"]
    assert observed["head_sha"] == head
    assert observed["commits_ahead"] == commits
    assert observed["worktree_dirty_on_exit"] is dirty
    if matched:
        assert observed["remote_head_sha"] == head
        assert run_git(sandbox.remote, "rev-parse", f"refs/heads/{matched}") == head
    else:
        assert observed["remote_head_sha"] == (record["worktree_base_sha"] if target not in {None, "prefix"} else None)


def test_review_uses_exact_commit_on_fresh_branch_and_cwd_reuses(sandbox):
    task = sandbox.dispatch("unpushed", "--mode", "workspace-write")
    first = sandbox.settle(task, expected=1)
    result = sandbox.cli(
        "dispatch",
        "--agent",
        "sol",
        "--model",
        "echo",
        "--prompt",
        "review",
        "--pr",
        "42",
        "--branch",
        first["worktree_branch"],
        "--pinned-head",
        first["head_sha"],
    )
    review = sandbox.settle(result.stdout.splitlines())
    assert review["worktree_base_sha"] == first["head_sha"]
    assert review["pinned_head"] == first["head_sha"]
    assert review["review_branch"] == first["worktree_branch"]
    assert _review_branch(review) == first["worktree_branch"]
    assert review["worktree_branch"] != first["worktree_branch"]
    assert review["push_state"] == "not_applicable"
    reused = sandbox.dispatch("echo", "--cwd", review["cwd"])
    assert sandbox.settle(reused)["cwd"] == review["cwd"]
    assert run_git(sandbox.repo, "branch", "--show-current") == "main"


def test_selected_sibling_repo_keeps_records_in_shared_store(sandbox):
    private = sandbox.repo.parent / "private"
    private.mkdir()
    run_git(private, "init", "-b", "main")
    run_git(private, "config", "user.name", "Stub")
    run_git(private, "config", "user.email", "stub@example.invalid")
    run_git(private, "commit", "--allow-empty", "-m", "private fixture")
    task = sandbox.dispatch("echo", "--repo", "private", "--base", "main")
    record = sandbox.settle(task)
    assert record["repo"] == "private"
    assert record["repository_id"] == record["repository"] == "example/private"
    assert Path(record["cwd"]).is_relative_to(private / ".worktrees/dispatch/codex")
    assert Path(record["prompt_file"]).parent == sandbox.tasks
    assert run_git(private, "branch", "--show-current") == "main"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_dry_run_and_invalid_flags_create_nothing(sandbox, mode):
    before = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "preview", "--dry-run")
    plan = json.loads(result.stdout)
    assert plan["argv"][2] == "echo"
    assert not Path(plan["worktree"]).exists()
    assert not sandbox.tasks.exists()
    assert run_git(sandbox.repo, "branch", "--list") == before
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--force-new", expected=2)
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--prompt-file", "y", expected=2)
    for include in ("../curriculum", "site/src", "unknown", ""):
        sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--sparse-include", include, expected=2)
    for branch in ("unsafe..branch", "origin/feature", "refs/heads/feature", "bad:name", ""):
        sandbox.cli(
            "dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x",
            "--mode", mode, "--branch", branch,
            "--pinned-head", run_git(sandbox.repo, "rev-parse", "HEAD"), expected=2,
        )
    assert run_git(sandbox.repo, "branch", "--list") == before
    assert not sandbox.tasks.exists()


@pytest.mark.parametrize("contributor", ["on", "off", None])
def test_muse_cli_forwards_contributor_mode_and_keeps_auditable_record(sandbox, contributor):
    """Missing CLI options must not silently force explicit contributor requests off."""
    args = ["dispatch", "--agent", "muse", "--model", "muse-wonder-full-1.0", "--prompt", "public input"]
    if contributor is not None:
        args += ["--contributor-mode", contributor]
    plan = json.loads(sandbox.cli(*args, "--dry-run").stdout)
    argv = plan["argv"]
    assert argv[argv.index("--contributor-mode") + 1] == (contributor or "off")
    assert not sandbox.tasks.exists()
    assert not Path(plan["worktree"]).exists()

    # Exercise persistence and the detached lifecycle without a paid Muse invocation.
    shutil.copy(Path(__file__).with_name("stub_provider.py"), sandbox.repo / "scripts/dispatcher/providers/muse.py")
    run_git(sandbox.repo, "add", "scripts/dispatcher/providers/muse.py")
    run_git(sandbox.repo, "commit", "-m", "fixture Muse transport")
    run_git(sandbox.repo, "push", "origin", "main")
    task = sandbox.cli(*args).stdout.splitlines()
    record = sandbox.settle(task)
    assert record["contributor_mode"] == (contributor or "off")
    assert json.loads((sandbox.tasks / f"{task[0]}.json").read_text())["contributor_mode"] == (contributor or "off")


@pytest.mark.parametrize("agent", sorted((set(ALIASES) | set(ALIASES.values()) | {"claude"}) - {"muse"}))
@pytest.mark.parametrize("contributor", ["on", "off"])
def test_contributor_mode_refuses_non_muse_agents_without_side_effects(sandbox, agent, contributor):
    before = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli(
        "dispatch",
        "--agent",
        agent,
        "--model",
        "echo",
        "--prompt",
        "public input",
        "--contributor-mode",
        contributor,
        expected=2,
    )
    assert result.stderr == "dispatcher: --contributor-mode is only supported with --agent muse\n"
    assert not sandbox.tasks.exists()
    assert run_git(sandbox.repo, "branch", "--list") == before


def test_legacy_archive_is_read_only_and_nonce_checked(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    archive = tmp_path / "archive"
    archive.mkdir()
    result = archive / "old.result"
    result.write_text("archived report")
    path = archive / "old.json"
    path.write_text(
        json.dumps(
            dict(task_id="old", status="needs_finalize", run_nonce="n", result_file=str(tmp_path / "old.result"))
        )
    )
    before = path.read_bytes()
    assert store.read("old", "n")["result_file"] == str(result)
    assert store.list_tasks() == []
    assert len(store.list_tasks(include_archive=True)) == 1
    with pytest.raises(ValueError, match="nonce mismatch"):
        store.read("old", "wrong")
    with pytest.raises(ValueError, match="legacy task"):
        worker.cancel("old", "n")
    assert path.read_bytes() == before


@pytest.fixture
def spec(tmp_path):
    prompt = tmp_path / "brief.txt"
    prompt.write_text("public input")
    return TaskSpec("task", "muse", "model", None, "read-only", tmp_path, prompt, tmp_path / "task.result")


def assert_private_input_policy(spec, repo_key, error):
    if spec.agent == "muse":
        spec = dataclasses.replace(spec, options={**spec.options, "contributor_mode": "on"})
        checks.check_private_input(spec, repo_key)
        argv = muse.build(spec, {}).argv
        assert argv[argv.index("--contributor-mode") + 1] == "off"
    else:
        with pytest.raises(ValueError, match=error):
            checks.check_private_input(spec, repo_key)


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
@pytest.mark.parametrize("classification", [{"role": "private-product"}, {"role": "product", "private": True}])
def test_private_repo_and_prompt_origin_cannot_bypass_private_policy(spec, private_repos, agent):
    private, alias = private_repos
    spec = dataclasses.replace(spec, agent=agent)
    assert_private_input_policy(spec, "private", "private input")
    for origin in (private / "secret.txt", alias / "secret.txt"):
        assert_private_input_policy(
            dataclasses.replace(spec, options={"prompt_file": str(origin)}), "public", "private prompt file"
        )


@pytest.fixture
def classification():
    return {"role": "private-product"}


@pytest.fixture
def private_repos(tmp_path, monkeypatch, classification):
    config = tmp_path / "repos.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {"default": True, "local_name": "public", "role": "public-monorepo"},
                    "private": {
                        "local_name": "vault-data",
                        "github": "ExampleOrg/SealedNotes",
                        **classification,
                    },
                }
            }
        )
    )
    monkeypatch.setattr(git, "CONFIG", config)
    monkeypatch.setattr(git, "ROOT", tmp_path / "public")
    private = tmp_path / "vault-data"
    private.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(private, target_is_directory=True)
    return private, alias


@pytest.mark.parametrize("classification", [{"role": "private-product"}, {"role": "product", "private": True}])
@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("source", ["repo", "prompt-origin", "symlink-origin", "owned-path", "encoded-identifier"])
def test_private_muse_never_receives_contributor_on(spec, private_repos, mode, source):
    private, alias = private_repos
    options = {"contributor_mode": "on", "unrelated": "preserved"}
    if source in {"prompt-origin", "symlink-origin"}:
        root = private if source == "prompt-origin" else alias
        options["prompt_file"] = str(root / "brief.txt")
    elif source == "owned-path":
        spec.prompt_file.write_text(f"Owned paths: {private}/notes.md")
    elif source == "encoded-identifier":
        spec.prompt_file.write_text("Owned paths: %56AULT%2dDATA/notes.md")
    expected_options = {**options, "contributor_mode": "off"}
    spec = dataclasses.replace(spec, mode=mode, options=options)
    before = spec.prompt_file.read_bytes()

    checks.check_private_input(spec, "private" if source == "repo" else "public")

    argv = muse.build(spec, {}).argv
    assert argv[argv.index("--contributor-mode") + 1] == "off"
    assert spec.options == expected_options
    assert spec.prompt_file.read_bytes() == before


def test_public_muse_contributor_on_is_preserved(spec, private_repos):
    spec = dataclasses.replace(spec, options={"contributor_mode": "on"})
    checks.check_private_input(spec, "public")
    argv = muse.build(spec, {}).argv
    assert argv[argv.index("--contributor-mode") + 1] == "on"


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
@pytest.mark.parametrize(
    "prompt",
    [
        pytest.param('Read "{private}/a=b.txt".', id="quoted-equals-private-path"),
        pytest.param("Read ({private}/a=b.txt).", id="parenthesized-equals-private-path"),
        pytest.param("Read file://{private}/secret.txt?v=1", id="file-uri-query-equals"),
        pytest.param("Read source:{encoded}", id="encoded-source-private-path"),
    ],
)
def test_private_path_equals_and_encoded_source_cannot_bypass_private_policy(spec, private_repos, agent, prompt):
    """Old tokenizer lost the private path after '=' or left source: escapes undecoded."""
    private, _ = private_repos
    prompt = prompt.format(private=private, encoded=str(private / "secret.txt").replace("/", "%2F"))
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    assert_private_input_policy(spec, "public", "private path")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
@pytest.mark.parametrize(
    "prompt",
    [
        pytest.param("Discuss VAULT-DATA notes.", id="plain-directory"),
        pytest.param("Discuss EXAMPLEORG/SEALEDNOTES.", id="plain-slug"),
        pytest.param("Read file://{private}/secret.txt", id="file-uri-private-root"),
        pytest.param("Read file:///ExampleOrg/SealedNotes/secret.txt", id="file-uri-slug"),
        pytest.param("Discuss %56AULT%2dDATA notes.", id="once-encoded-directory"),
        pytest.param("Discuss %45XAMPLEORG%2f%53EALEDNOTES.", id="once-encoded-slug"),
        pytest.param("Read {encoded}", id="once-encoded-path"),
        pytest.param("Read --input={private}/secret.txt", id="option-private-path"),
    ],
)
def test_private_identifier_substring_contract(spec, private_repos, agent, prompt):
    """CTO policy replaces path tokenization with conservative identifier substrings."""
    private, _ = private_repos
    prompt = prompt.format(private=private, encoded=str(private / "secret.txt").replace("/", "%2F"))
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    assert_private_input_policy(spec, "public", "private path")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
@pytest.mark.parametrize("prompt", ["[notes](100%.md)", "Read file:///public/100%.md"])
def test_public_literal_percent_is_not_a_malformed_escape_refusal(spec, private_repos, agent, prompt):
    """Old tokenizer incorrectly refused public100percent CommonMark and file URI inputs."""
    spec = dataclasses.replace(spec, agent=agent)
    spec.prompt_file.write_text(prompt)
    checks.check_private_input(spec, "public")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
@pytest.mark.parametrize(
    "prompt",
    [
        "./alias/secret.txt",
        "'alias/a file.txt'",
        "--input=alias/secret.txt",
        "%2556AULT%252dDATA",
        "https://example.invalid/guide?q=100%25",
        "Public input with 100% progress, %GG, and an unfinished [link](",
    ],
)
def test_lexical_contract_allows_aliases_double_encoding_and_public_text(spec, private_repos, agent, prompt):
    """Approved policy change: old alias refusals now pass; no alias resolution or recursive decoding."""
    spec = dataclasses.replace(spec, agent=agent, options={"prompt_file": "-"})
    spec.prompt_file.write_text(prompt)
    checks.check_private_input(spec, "public")
    assert spec.prompt_file.read_text() == prompt


@pytest.mark.parametrize("agent", ["codex", "claude", "cursor", "agy"])
def test_private_input_policy_leaves_other_providers_unchanged(spec, private_repos, agent):
    private, _ = private_repos
    spec = dataclasses.replace(spec, agent=agent, options={"prompt_file": str(private / "brief.txt")})
    spec.prompt_file.write_text("Read ExampleOrg/SealedNotes with 100% progress.")
    checks.check_private_input(spec, "private")


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
def test_empty_private_identifiers_do_not_refuse_all_public_prompts(spec, tmp_path, monkeypatch, agent):
    config = tmp_path / "repos.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "private": {"default": True, "local_name": "", "github": "", "private": True},
                    "public": {"local_name": "public"},
                }
            }
        )
    )
    monkeypatch.setattr(git, "CONFIG", config)
    root = tmp_path / "protected-root"
    monkeypatch.setattr(git, "ROOT", root)
    spec = dataclasses.replace(spec, agent=agent)
    checks.check_private_input(spec, "public")
    spec.prompt_file.write_text(f"Read {root}/secret.txt")
    assert_private_input_policy(spec, "public", "private path")


@pytest.mark.parametrize("character", ["\n", "\u202e", "\u2028"])
def test_worktree_path_contract_defers_unicode_characters_to_git(sandbox, character):
    """Approved policy change: remove extra Unicode refusal while retaining dispatch containment."""
    path = sandbox.repo / ".worktrees/dispatch/codex" / f"name{character}part"
    planned, branch, sha = git.worktree_plan(sandbox.repo, "codex", "path-policy", "main", worktree=path)
    assert planned == path
    assert branch == "codex/path-policy"
    assert sha == run_git(sandbox.repo, "rev-parse", "main")


def test_worktree_plan_retains_containment_symlinks_repo_identity_and_git_failures(sandbox):
    parent = sandbox.repo / ".worktrees/dispatch/codex"
    parent.mkdir(parents=True)
    alias = parent / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    for path in (sandbox.repo / "outside", alias / "child"):
        with pytest.raises(ValueError, match="dispatch directory without symlinks"):
            git.worktree_plan(sandbox.repo, "codex", "safe-path", "main", worktree=path)
    with pytest.raises(subprocess.CalledProcessError):
        git.worktree_plan(sandbox.repo, "codex", "missing-cwd", "main", cwd=parent / "missing")
    path = parent / "existing"
    sha = run_git(sandbox.repo, "rev-parse", "main")
    git.create_worktree(sandbox.repo, path, "codex/existing", sha)
    assert git.worktree_plan(sandbox.repo, "codex", "existing", "main", cwd=path) == (path, "codex/existing", sha)
    with pytest.raises(ValueError, match="existing dispatch worktree root"):
        git.worktree_plan(sandbox.repo, "codex", "nested", "main", cwd=path / "scripts")
    foreign = parent / "foreign"
    foreign.mkdir()
    run_git(foreign, "init", "-b", "main")
    with pytest.raises(ValueError, match="different repository"):
        git.worktree_plan(sandbox.repo, "codex", "foreign", "main", cwd=foreign)


def test_review_family_uses_model_family_not_harness_and_refuses_unknown():
    checks.check_review_family("gpt-6.1-sol", "claude-opus-5-5")
    checks.check_review_family("claude-opus-5-5", "grok-4.7-high")
    for author, reviewer in (
        ("gpt-6.1-sol", "gpt-6-luna"),
        ("claude-opus-5-5", "claude-sonnet-5-5"),
        ("unknown", "gpt-6.1-sol"),
        ("gpt-6.1-sol", "unknown"),
    ):
        with pytest.raises(ValueError, match="known, different"):
            checks.check_review_family(author, reviewer)


def test_resource_floor_and_both_filesystems_with_injected_values(tmp_path, monkeypatch):
    real_read = Path.read_text
    available = 8.5 * 1024**3
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: (
            f"MemAvailable: {int(available / 1024)} kB\n"
            if path == Path("/proc/meminfo")
            else real_read(path, *a, **kw)
        ),
    )
    probes = []
    monkeypatch.setattr(
        checks.shutil, "disk_usage", lambda path: probes.append(path) or SimpleNamespace(used=89, total=100)
    )
    checks.check_resources([tmp_path, tmp_path / "nonexistent"])
    assert probes == [tmp_path, tmp_path]
    available -= 1024
    with pytest.raises(ValueError, match=r"8\.5 GiB"):
        checks.check_resources([tmp_path])
    available += 1024
    monkeypatch.setattr(checks.shutil, "disk_usage", lambda path: SimpleNamespace(used=90, total=100))
    with pytest.raises(ValueError, match="90%"):
        checks.check_resources([tmp_path])


def test_environment_contains_only_context_and_selected_auth(spec, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in ("GH_TOKEN", "SSH_AUTH_SOCK", "INFRA_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "MUSE_API_KEY"):
        monkeypatch.setenv(name, f"test-{name.lower()}")
    env = child_env(spec)
    assert env["MUSE_API_KEY"] == "test-muse_api_key"
    assert not {"GH_TOKEN", "SSH_AUTH_SOCK", "INFRA_TOKEN", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"} & env.keys()
    for account, directory in (("a", ".claude"), ("b", ".claude-b")):
        env = child_env(dataclasses.replace(spec, agent="claude", claude_account=account))
        assert env["CLAUDE_CONFIG_DIR"] == str(tmp_path / directory)
        assert "MUSE_API_KEY" not in env


def test_cursor_child_env_present_process_key_wins_over_env_file(spec, monkeypatch):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    monkeypatch.setenv("CURSOR_API_KEY", "stub-process-key")

    env = child_env(dataclasses.replace(spec, agent="cursor"))

    assert env["CURSOR_API_KEY"] == "stub-process-key"
    loader.assert_not_called()


@pytest.mark.parametrize("process_key", [None, "", " \t\n"], ids=["missing", "blank", "whitespace_only"])
def test_cursor_child_env_missing_or_blank_process_key_falls_back_to_env_file(spec, monkeypatch, process_key):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    env = child_env(dataclasses.replace(spec, agent="cursor"))

    assert env["CURSOR_API_KEY"] == "stub-file-key"
    assert os.environ.get("CURSOR_API_KEY") == process_key
    loader.assert_called_once_with()


@pytest.mark.parametrize("process_key", [None, "", " \t\n"], ids=["missing", "blank", "whitespace_only"])
def test_cursor_child_env_missing_or_blank_key_without_file_key_forwards_nothing(spec, monkeypatch, process_key):
    loader = Mock(return_value=None)
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent="cursor"))
    loader.assert_called_once_with()


@pytest.mark.parametrize("agent", ["codex", "claude", "agy", "muse", "opencode", "hermes"])
@pytest.mark.parametrize("process_key", [None, "stub-process-key", "", " \t\n"])
def test_non_cursor_child_env_never_loads_or_forwards_cursor_key(spec, monkeypatch, agent, process_key):
    loader = Mock(return_value="stub-file-key")
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._load_cursor_api_key_from_env_file", loader)
    if process_key is None:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CURSOR_API_KEY", process_key)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent=agent))
    loader.assert_not_called()


def test_cursor_child_env_corrupt_invalid_utf8_file_forwards_no_key_without_raising(spec, monkeypatch, tmp_path, capsys):
    key_file = tmp_path / "api.key.env"
    key_file.write_bytes(b"CURSOR_API_KEY=stub-\xff-key\n")
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr("scripts.agent_runtime.adapters.cursor._cursor_api_key_env_path", lambda: key_file)

    assert "CURSOR_API_KEY" not in child_env(dataclasses.replace(spec, agent="cursor"))
    assert capsys.readouterr() == ("", "")


def test_aliases_and_all_retained_metadata_flags_parse():
    assert dict(sol="codex", grok="cursor", gemini="agy", deepseek="opencode", openrouter="hermes") == ALIASES
    args = build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "sol",
            "--model",
            "gpt-6.1-sol",
            "--prompt",
            "x",
            "--owned-path",
            "scripts",
            "--research-owned-path",
            "tests",
            "--risk",
            "critical",
            "--review-mode",
            "red_team",
            "--language-lane",
            "en",
            "--output-schema",
            "schema.json",
        ]
    )
    assert args.owned_path == ["scripts"]
    assert args.research_owned_path == ["tests"]


# Unit G0: legacy tests copied and adapted; originals remain unchanged.


def test_worker_writable_python_paths_cannot_execute_in_trusted_supervisor_or_reaper(sandbox, tmp_path):
    """A worker shadow module must never execute with the trusted parent's environment."""
    sentinel = tmp_path / "trusted-shadow-imported"
    supervisor_env_file = tmp_path / "supervisor-env.json"
    shadow = sandbox.repo / "scripts/json.py"
    shadow.write_text(
        "import os, sysconfig\nfrom pathlib import Path\n"
        "if os.environ.get('G0_TRUSTED_ONLY'):\n"
        f"    Path({str(sentinel)!r}).write_text('worker code ran in a trusted process')\n"
        "__package__ = 'json'\n"
        "__path__ = [str(Path(sysconfig.get_path('stdlib')) / 'json')]\n"
        "exec((Path(__path__[0]) / '__init__.py').read_text())\n"
    )
    supervisor = sandbox.repo / "scripts/dispatcher/worker.py"
    supervisor.write_text(supervisor.read_text().replace(
        "    settings = json.load(sys.stdin)",
        f"    Path({str(supervisor_env_file)!r}).write_text(json.dumps(dict(os.environ)))\n"
        "    settings = json.load(sys.stdin)",
    ).replace(
        "        _reap_settled(record, path)",
        "        os.environ['PYTHONPATH'] = str(spec.worktree / 'scripts')\n"
        "        _reap_settled(record, path)",
    ))
    stub_common_reaper(sandbox)
    (sandbox.repo / "scripts/fleet/__init__.py").write_text(
        f"__path__.append({str(SOURCE / 'scripts/fleet')!r})\n"
    )
    reaper = sandbox.repo / "scripts/fleet/post_task_reap.py"
    reaper.write_text(reaper.read_text().replace("receipt = dict(", "receipt = dict(env=dict(os.environ), "))
    run_git(sandbox.repo, "add", "scripts")
    run_git(sandbox.repo, "commit", "-m", "fixture shadow module and trusted environment probes")
    run_git(sandbox.repo, "push", "origin", "main")
    sandbox.env.clear()
    sandbox.env.update(
        PATH=os.defpath, HOME=str(tmp_path), LANG="C.UTF-8", LU_TASKS_DIR=str(sandbox.tasks),
        G0_TRUSTED_ONLY="present", LU_SCRATCH_ROOT=str(tmp_path / "scratch"),
    )

    task = sandbox.dispatch()
    record = sandbox.settle(task)
    receipt = json.loads(await_file(sandbox.tasks / f"{task[0]}.reaped"))
    environments = [json.loads(supervisor_env_file.read_text()), receipt["env"]]

    assert not sentinel.exists(), "worker shadow module executed in the supervisor or common reaper"
    from tests import cursor_exec_tripwire

    for env in environments:
        assert not {
            "PYTEST_PLUGINS", "PYTHONPYCACHEPREFIX", "TMPDIR",
            "MYPY_CACHE_DIR", "RUFF_CACHE_DIR", "LU_RUNTIME_TMP_ROOT", "LU_TASK_EVIDENCE_DIR",
        } & env.keys()
        assert env["PYTHONPATH"] == str(cursor_exec_tripwire.child_directory)
        assert not any(record["worktree_path"] in value or record["runtime_tmp_root"] in value
                       for value in env.values())
    assert record["tmp_reap_error"] is None
    assert not Path(record["runtime_tmp_root"]).exists()


def test_worker_environment_split_keeps_provider_exports_and_exact_supervisor_keys(sandbox, tmp_path):
    """No worker paths or pool overrides cross into the wrong process environment."""
    supervisor_env_file, provider_env_file = tmp_path / "supervisor.json", tmp_path / "provider.json"
    supervisor = sandbox.repo / "scripts/dispatcher/worker.py"
    supervisor.write_text(supervisor.read_text().replace(
        "    settings = json.load(sys.stdin)",
        f"    Path({str(supervisor_env_file)!r}).write_text(json.dumps(dict(os.environ)))\n"
        "    settings = json.load(sys.stdin)",
    ))
    provider = sandbox.repo / "scripts/dispatcher/providers/codex.py"
    provider.write_text(provider.read_text().replace(
        "    raise SystemExit(main())",
        f"    Path({str(provider_env_file)!r}).write_text(__import__('json').dumps(dict(os.environ)))\n"
        "    raise SystemExit(main())",
    ))
    run_git(sandbox.repo, "add", "scripts")
    run_git(sandbox.repo, "commit", "-m", "fixture supervisor and provider environment probes")
    run_git(sandbox.repo, "push", "origin", "main")
    parent = {
        "PATH": os.defpath, "HOME": str(tmp_path), "LANG": "C.UTF-8", "TERM": "dumb",
        "LU_TASKS_DIR": str(sandbox.tasks), "LU_SCRATCH_ROOT": str(tmp_path / "scratch"),
        "OPENAI_API_KEY": "fixture-selected-auth", "GH_TOKEN": "fixture-parent-auth",
        "ANTHROPIC_API_KEY": "fixture-unrelated-auth", "AB_POOL_OVERRIDE": "fixture-parent-pool",
    }
    worker_only = {
        "PYTHONPATH", "PYTEST_PLUGINS", "PYTHONPYCACHEPREFIX", "TMPDIR", "MYPY_CACHE_DIR",
        "RUFF_CACHE_DIR", "LU_RUNTIME_TMP_ROOT", "LU_TASK_EVIDENCE_DIR", "LU_X_AGENT_TRAILER",
        "LU_RUNTIME_TMP_BASE_ROOT",
    }
    sandbox.env.clear()
    sandbox.env.update(parent, **dict.fromkeys(worker_only, str(tmp_path / "inherited-worker-path")))
    sandbox.env.update(LEARN_UKRAINIAN_DISPATCH_TASK_ID="parent-task", LEARN_UKRAINIAN_DISPATCH_AGENT="claude")

    task = sandbox.dispatch("echo", "--initiator", "g0-test")
    record = sandbox.settle(task)
    trusted, provider_env = json.loads(supervisor_env_file.read_text()), json.loads(provider_env_file.read_text())
    identity = {
        "LEARN_UKRAINIAN_DISPATCH_TASK_ID": task[0], "LEARN_UKRAINIAN_DISPATCH_AGENT": "codex",
        "LU_RUNTIME_RUN_NONCE": task[1], "LU_RUNTIME_INITIATOR": "g0-test",
        "LU_RUNTIME_INITIATOR_SOURCE": "explicit",
    }
    # The test execution tripwire adds its own trusted path at the exec boundary.
    from tests import cursor_exec_tripwire

    tripwire = {key: sandbox.env[key] for key in (
        "LU_TEST_CURSOR_SESSION_TOKEN", "LU_TEST_CURSOR_TARGETS", "LU_TEST_CURSOR_ROOTS",
    )}
    trusted_path = str(cursor_exec_tripwire.child_directory)
    expected_trusted = {**parent, **identity, **tripwire, "PYTHONPATH": trusted_path}
    assert set(trusted) == set(expected_trusted)
    assert trusted == expected_trusted
    lease = Path(record["runtime_tmp_root"])
    assert provider_env == {
        **{key: parent[key] for key in ("HOME", "LANG", "TERM", "OPENAI_API_KEY")}, **identity, **tripwire,
        "PATH": os.defpath,
        "LU_X_AGENT_TRAILER": f"X-Agent: codex/{task[0]}",
        "PYTHONPATH": f"{trusted_path}{os.pathsep}{Path(record['worktree_path']) / 'scripts'}",
        "PYTEST_PLUGINS": "ci.pytest_dispatch_cap", "TMPDIR": str(lease), "LU_RUNTIME_TMP_ROOT": str(lease),
        "LU_TASK_EVIDENCE_DIR": str(lease / "evidence"), "LU_RUNTIME_TMP_BASE_ROOT": str(lease.parent.parent),
        "MYPY_CACHE_DIR": str(lease / "tool-cache/mypy"),
        "PYTHONPYCACHEPREFIX": str(lease / "tool-cache/pycache"), "RUFF_CACHE_DIR": str(lease / "tool-cache/ruff"),
    }
_SOURCE_INVENTORY_TREES = (
    "registry/lexicon/source-inventory", "registry/lexicon/source-inventory-review-decisions",
)
_SOURCE_INVENTORY = _SOURCE_INVENTORY_TREES


# Ported from tests/test_delegate.py::test_normalize_sparse_include_dedupes_and_strips.
def test_normalize_sparse_include_dedupes_and_strips():
    from scripts.dispatcher import sparse
    assert sparse._normalize_sparse_include(None) == ()
    assert sparse._normalize_sparse_include(["curriculum/", " wiki ", "curriculum"]) == (
        "curriculum",
        "wiki",
    )
    assert sparse._normalize_sparse_include(["data/projects/", " data/lexicon ", "registry/projects"]) == (
        "data/projects",
        "data/lexicon",
        "registry/projects",
    )


# Ported from tests/test_delegate.py::test_normalize_sparse_include_rejects_nested_and_unknown.
def test_normalize_sparse_include_rejects_nested_and_unknown():
    import pytest

    from scripts.dispatcher import sparse

    with pytest.raises(ValueError, match="must name a default-excluded tree"):
        sparse._normalize_sparse_include(["curriculum/l2-uk-en"])
    with pytest.raises(ValueError, match="not a default-excluded"):
        sparse._normalize_sparse_include(["scripts"])
    with pytest.raises(ValueError, match="must name a default-excluded tree"):
        sparse._normalize_sparse_include(["data/raw"])
    with pytest.raises(ValueError, match="empty or invalid"):
        sparse._normalize_sparse_include([""])


# Ported from tests/test_delegate.py::test_infer_sparse_include_from_owned_paths_and_prompt.
def test_infer_sparse_include_from_owned_paths_and_prompt():
    from scripts.dispatcher import sparse
    assert sparse._infer_sparse_include(None) == ()
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["curriculum/l2-uk-en/bio/foo", "scripts/x.py"],
    ) == ("curriculum",)
    assert sparse._infer_sparse_include(
        ["wiki"],
        owned_paths=["curriculum/a", "wiki/b"],
    ) == ("wiki", "curriculum")
    assert sparse._infer_sparse_include(
        None,
        prompt_text="Edit curriculum/l2-uk-en/a1/foo.md and leave scripts alone.",
    ) == ("curriculum",)
    assert "wiki" not in sparse._infer_sparse_include(
        None,
        prompt_text="Discuss Wikipedia articles without path refs.",
    )
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["scripts/projects/open_model_data/mine.py"],
    ) == ("data/projects",)
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["tests/projects/open_model_data/test_mine.py"],
    ) == ("data/projects",)
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["registry/projects/open_model_data/grammar/grammar_rules.json"],
    ) == ("registry/projects",)
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["scripts/lexicon/manifest_io.py", "site/src/pages/index.astro"],
    ) == (*_SOURCE_INVENTORY_TREES, "site/src/content", "site/src/data")
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["site/src/pages/index.astro"],
    ) == ("site/src/content", "site/src/data")
    assert sparse._infer_sparse_include(
        None,
        owned_paths=["tests/test_open_model_foundry_cli.py"],
    ) == ("data/projects",)
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["tests/test_open_model_data_timeouts.py"],
        )
        == ()
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["scripts/audit/source_inventory_review_decisions.py"],
        )
        == _SOURCE_INVENTORY_TREES
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["scripts/audit/source_inventory_intake.py"],
        )
        == ()
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["tests/test_source_inventory_intake.py"],
        )
        == _SOURCE_INVENTORY_TREES
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["scripts/practice/author_densified_pairs.py"],
        )
        == _SOURCE_INVENTORY_TREES
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["scripts/practice/thin_mode_source_inventory.py"],
        )
        == _SOURCE_INVENTORY_TREES
    )
    assert (
        sparse._infer_sparse_include(
            None,
            owned_paths=["scripts/practice/noun_mechanics_engine.py"],
        )
        == ()
    )
    assert sparse._infer_sparse_include(
        None,
        prompt_text="Read data/projects/foo.jsonl and leave data/raw alone.",
    ) == ("data/projects",)


# Ported from tests/test_dispatch_checkout_size.py::test_owned_path_includes_the_trees_it_needs.
@pytest.mark.parametrize(
    ("owned", "expected"),
    [
        ("site/src/data/curriculum-stats.json", ("site/src/data",)),
        ("site/src/pages/index.astro", ("site/src/content", "site/src/data")),
        ("site", ("site/src/content", "site/src/data")),
        ("registry/lexicon", _SOURCE_INVENTORY),
        ("data", ("data/datasets", "data/lexicon", "data/processed", "data/projects")),
        ("scripts/sparse.py", ()),
        ("tests/test_preparation_api.py", ("site/src/content",)),
        ("tests/test_landings_use_levellanding.py", ("curriculum", "site/src/content", "site/src/data")),
        ("tests/test_env_sanitize.py", ()),
        ("scripts/generate_landing_pages.py", ("curriculum", "site/src/content")),
        ("scripts/audit/check_static_practice_assets.py", ("site/src/data",)),
        ("scripts/lexicon/lesson_atlas_link_census.py", (*_SOURCE_INVENTORY, "site/src/content", "site/src/data")),
        (".", ()),
    ],
)
def test_owned_path_includes_the_trees_it_needs(owned: str, expected: tuple[str, ...]) -> None:
    from scripts.dispatcher import sparse
    assert sparse._infer_sparse_include(None, owned_paths=[owned]) == expected


# Ported from tests/test_dispatch_checkout_size.py::test_owned_path_aliases_include_what_their_canonical_spelling_includes.
@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("./site/src/data/curriculum-stats.json", "site/src/data/curriculum-stats.json"),
        ("registry/./projects/open_model_data/x.json", "registry/projects/open_model_data/x.json"),
        ("site//src//data/curriculum-stats.json", "site/src/data/curriculum-stats.json"),
        ("site/src/data/", "site/src/data"),
        ("site/src/data/**", "site/src/data"),
        ("./registry/lexicon/", "registry/lexicon"),
        (".\\site\\src\\data\\curriculum-stats.json", "site/src/data/curriculum-stats.json"),
    ],
)
def test_owned_path_aliases_include_what_their_canonical_spelling_includes(alias: str, canonical: str) -> None:
    """Every spelling ownership admission accepts names the same trees (#10777)."""
    from scripts.dispatcher import sparse
    from scripts.guardrails.delegate_ownership import owned_path_matcher

    assert owned_path_matcher(alias) is not None
    expected = sparse._infer_sparse_include(None, owned_paths=[canonical])

    assert expected
    assert sparse._infer_sparse_include(None, owned_paths=[alias]) == expected


# Ported from tests/test_dispatch_checkout_size.py::test_owned_glob_includes_the_trees_its_literal_directories_reach.
@pytest.mark.parametrize(
    ("glob", "expected"),
    [
        ("curriculum/l2-uk-en/evidence/a1/**/lessons.lock.yaml", ("curriculum",)),
        ("site/src/data/lexicon-*.json", ("site/src/data",)),
        # fnmatch's ``*`` crosses ``/``: this glob can own files in both site trees.
        ("site/*.json", ("site/src/content", "site/src/data")),
        ("./registry/projects/*/x.json", ("registry/projects",)),
        ("scripts/*.py", ()),
    ],
)
def test_owned_glob_includes_the_trees_its_literal_directories_reach(glob: str, expected: tuple[str, ...]) -> None:
    from scripts.dispatcher import sparse
    assert sparse._infer_sparse_include(None, owned_paths=[glob]) == expected


# Ported from tests/test_dispatch_checkout_size.py::test_owned_path_prefix_confusion_includes_nothing.
@pytest.mark.parametrize(
    "owned",
    [
        "site-extra/src/data/x.json",
        "site-extra",
        "registry/projects2/x.json",
        "registry/projects2",
        "data/projects-old/x",
        "curriculum2/a1.yaml",
        "registry/lexicon/source-inventory-old/x.yaml",
    ],
)
def test_owned_path_prefix_confusion_includes_nothing(owned: str) -> None:
    from scripts.dispatcher import sparse
    assert sparse._infer_sparse_include(None, owned_paths=[owned]) == ()


# Ported from tests/test_dispatch_checkout_size.py::test_an_owned_path_that_owns_nothing_includes_nothing.
@pytest.mark.parametrize("owned", ["", ".", "./", "/site/src/data", "site/../site/src/data", "**", "./**", "*/x"])
def test_an_owned_path_that_owns_nothing_includes_nothing(owned: str) -> None:
    """Admission refuses these claims; inference reads them the same way."""
    from scripts.dispatcher import sparse
    from scripts.guardrails.delegate_ownership import owned_path_matcher

    assert owned_path_matcher(owned) is None
    assert sparse._infer_sparse_include(None, owned_paths=[owned]) == ()


# Ported from tests/test_dispatch_checkout_size.py::test_an_owned_test_gets_the_excluded_trees_its_marks_name.
def test_an_owned_test_gets_the_excluded_trees_its_marks_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.dispatcher import sparse
    test_file = tmp_path / "tests" / "test_reader.py"
    test_file.parent.mkdir()
    test_file.write_text(
        "import pytest\n"
        'needs_data = pytest.mark.needs_sparse_tree("site/src/data")\n'
        '@pytest.mark.needs_sparse_tree("data/projects", "not/excluded")\n'
        "def test_x(): pass\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_broken.py").write_text("def (\n", encoding="utf-8")
    monkeypatch.setattr(sparse, "_REPO_ROOT", tmp_path)

    assert sparse._owned_test_marked_trees("tests/test_reader.py") == ("data/projects", "site/src/data")
    assert sparse._owned_test_marked_trees("tests/test_broken.py") == ()
    assert sparse._owned_test_marked_trees("tests/test_missing.py") == ()
    # Only test files are read for marks.
    assert sparse._owned_test_marked_trees("scripts/test_reader.py") == ()


# Ported from tests/test_dispatch_checkout_size.py::test_cone_dirs_drop_nested_trees_and_keep_their_siblings.
def test_cone_dirs_drop_nested_trees_and_keep_their_siblings() -> None:
    from scripts.dispatcher import sparse
    tree = {
        "": ("data", "docs", "site"),
        "data": ("data/datasets", "data/raw"),
        "site": ("site/src", "site/tests"),
        "site/src": ("site/src/content", "site/src/data", "site/src/lib"),
    }

    cone, excluded = sparse._dispatch_sparse_cone_dirs(
        lambda parent: tree.get(parent, ()),
        {"data/datasets", "site/src/data", "site/src/content", "registry/projects", "docs/missing/deep"},
    )

    assert excluded == ["data/datasets", "site/src/content", "site/src/data"]
    # docs/ has no excluded tree at this ref, so it stays whole.
    assert sorted(cone) == ["data/raw", "docs", "site/src/lib", "site/tests"]


# Ported from tests/test_dispatch_checkout_size.py::test_apply_sparse_checkout_drops_nested_trees_real_git.
def test_apply_sparse_checkout_drops_nested_trees_real_git(tmp_path: Path) -> None:
    primary = tmp_path / "primary"
    files = {
        "README.md": "root\n",
        "site/package.json": "{}\n",
        "site/src/content.config.ts": "export {}\n",
        "site/src/data/stats.json": "{}\n",
        "site/src/content/docs/a1/index.mdx": "x\n",
        "site/src/lib/a.ts": "x\n",
        "registry/lexicon/f.txt": "x\n",
        "registry/lexicon/source-inventory/big.yaml": "x\n",
        "registry/lexicon/source-inventory/grade-01/g.yaml": "x\n",
        "registry/lexicon/source-inventory/oneshot/o.yaml": "x\n",
        "scripts/s.py": "x\n",
    }
    for relative, text in files.items():
        path = primary / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    env = {"GIT_CEILING_DIRECTORIES": str(tmp_path), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}

    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=primary, check=True, capture_output=True, env=env, timeout=30)

    git("init", "-q", "-b", "main")
    git("add", ".")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "init")
    worktree = tmp_path / "wt"
    from scripts.dispatcher.git import create_worktree

    meta = create_worktree(primary, worktree, "g0-nested", "HEAD")

    assert meta["excluded"] == ["registry/lexicon/source-inventory", "site/src/content", "site/src/data"]
    present = {relative for relative in files if (worktree / relative).is_file()}
    assert present == {
        "README.md",
        "site/package.json",
        "site/src/content.config.ts",
        "site/src/lib/a.ts",
        "registry/lexicon/f.txt",
        # The grade-01 anchor brings the inventories beside it, not oneshot/.
        "registry/lexicon/source-inventory/big.yaml",
        "registry/lexicon/source-inventory/grade-01/g.yaml",
        "scripts/s.py",
    }


# Ported from tests/test_delegate.py::test_apply_dispatch_sparse_checkout_keeps_curriculum_manifest.

def test_apply_dispatch_sparse_checkout_keeps_curriculum_manifest(tmp_path):
    """Default cone keeps curriculum.yaml via the evidence anchor, not the tree."""
    import os
    import subprocess

    primary = tmp_path / "primary"
    primary.mkdir()
    clean_env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR",
            "GIT_NAMESPACE",
        }
    }
    clean_env["GIT_CEILING_DIRECTORIES"] = str(tmp_path)

    def git(*args, cwd=primary):
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            env=clean_env,
            timeout=30,
        )

    git("init", "-b", "main")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test")
    manifest = primary / "curriculum" / "l2-uk-en" / "curriculum.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("levels: {}\n", encoding="utf-8")
    arc = primary / "curriculum" / "l2-uk-en" / "lesson-plans" / "a1" / "_arc.yaml"
    arc.parent.mkdir(parents=True)
    arc.write_text("level: a1\n", encoding="utf-8")
    plans = primary / "curriculum" / "l2-uk-en" / "plans" / "a2" / "x.yaml"
    plans.parent.mkdir(parents=True)
    plans.write_text("slug: x\n", encoding="utf-8")
    other = primary / "curriculum" / "l2-uk-direct" / "manifest.yaml"
    other.parent.mkdir(parents=True)
    other.write_text("tracks: []\n", encoding="utf-8")
    wiki = primary / "wiki" / "f.txt"
    wiki.parent.mkdir(parents=True)
    wiki.write_text("wiki\n", encoding="utf-8")
    scripts = primary / "scripts" / "f.txt"
    scripts.parent.mkdir(parents=True)
    scripts.write_text("scripts\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "init")

    worktree = tmp_path / "wt"
    from scripts.dispatcher.git import create_worktree

    meta = create_worktree(primary, worktree, "g0-manifest", "HEAD")
    assert meta["applied"] is True
    assert "curriculum" in meta["excluded"]
    assert "curriculum/l2-uk-en/lesson-plans" in meta["included_dirs"]
    assert (worktree / "curriculum" / "l2-uk-en" / "curriculum.yaml").is_file()
    assert (worktree / "curriculum" / "l2-uk-en" / "lesson-plans" / "a1" / "_arc.yaml").is_file()
    assert not (worktree / "curriculum" / "l2-uk-en" / "plans").exists()
    assert not (worktree / "curriculum" / "l2-uk-direct").exists()
    assert not (worktree / "wiki").exists()
    assert (worktree / "scripts" / "f.txt").is_file()


# Ported from tests/test_dispatch_checkout_size.py::test_worker_env_points_tool_caches_at_the_scratch_lease.
def test_worker_env_points_tool_caches_at_the_scratch_lease(tmp_path: Path) -> None:
    from scripts.dispatcher import worker_environment
    lease = tmp_path / "lease"

    env = worker_environment._build_worker_env(
        task_id="infra-10777-size",
        dispatch_agent="claude",
        runtime_tmp_root=lease,
        base_env={"PATH": "/usr/bin", "HOME": str(tmp_path)},
    )

    assert env["MYPY_CACHE_DIR"] == str(lease / "tool-cache" / "mypy")
    assert env["PYTHONPYCACHEPREFIX"] == str(lease / "tool-cache" / "pycache")
    assert env["RUFF_CACHE_DIR"] == str(lease / "tool-cache" / "ruff")


# Ported from tests/test_dispatch_checkout_size.py::test_worker_env_without_a_lease_leaves_tool_caches_alone.
def test_worker_env_without_a_lease_leaves_tool_caches_alone(tmp_path: Path) -> None:
    from scripts.dispatcher import worker_environment
    env = worker_environment._build_worker_env(
        task_id="infra-10777-size",
        dispatch_agent="claude",
        base_env={"PATH": "/usr/bin", "HOME": str(tmp_path)},
    )

    assert not {"MYPY_CACHE_DIR", "PYTHONPYCACHEPREFIX", "RUFF_CACHE_DIR"} & env.keys()


# Ported from tests/test_delegate.py::test_create_runtime_tmp_lease_sanitizes_task_id.
def test_create_runtime_tmp_lease_sanitizes_task_id(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))

    lease_root, namespace_root = runtime_tmp._create_runtime_tmp_lease(
        "codex/4956 tmp/../lease",
    )

    assert namespace_root == tmp_path / "learn-ukrainian"
    assert lease_root == namespace_root / "codex-4956-tmp-..-lease"
    assert lease_root.is_dir()


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_refuses_root_outside_namespace.
def test_runtime_tmp_reap_refuses_root_outside_namespace(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    namespace_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = outside / "keep.txt"
    payload.write_text("keep", encoding="utf-8")

    result = runtime_tmp._reap_runtime_tmp_lease(outside, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "not under $TMPDIR/learn-ukrainian" in str(result["tmp_reap_error"])
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_refuses_namespace_outside_tempdir.
def test_runtime_tmp_reap_refuses_namespace_outside_tempdir(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    os_tmp_root = tmp_path / "os-tmp"
    os_tmp_root.mkdir()
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(os_tmp_root))
    namespace_root = tmp_path / "repository" / "learn-ukrainian"
    lease_root = namespace_root / "scripts"
    lease_root.mkdir(parents=True)
    payload = lease_root / "keep.txt"
    payload.write_text("keep", encoding="utf-8")

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "not directly under an approved scratch root" in str(result["tmp_reap_error"])
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_refuses_wrong_namespace_name.
def test_runtime_tmp_reap_refuses_wrong_namespace_name(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "wrong-namespace"
    lease_root = namespace_root / "task"
    lease_root.mkdir(parents=True)
    payload = lease_root / "keep.txt"
    payload.write_text("keep", encoding="utf-8")

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "namespace has the wrong name" in str(result["tmp_reap_error"])
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_refuses_missing_symlink_protection.
def test_runtime_tmp_reap_refuses_missing_symlink_protection(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    lease_root = namespace_root / "task"
    lease_root.mkdir(parents=True)
    payload = lease_root / "keep.txt"
    payload.write_text("keep", encoding="utf-8")

    def unprotected_rmtree(*_args, **_kwargs):
        raise AssertionError("rmtree must not run without symlink protection")

    monkeypatch.setattr(runtime_tmp.shutil, "rmtree", unprotected_rmtree)

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "lacks symlink-attack protection" in str(result["tmp_reap_error"])
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_refuses_a_symlinked_lease_root.
def test_runtime_tmp_reap_refuses_a_symlinked_lease_root(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    namespace_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = outside / "keep.txt"
    payload.write_text("keep", encoding="utf-8")
    lease_root = namespace_root / "task"
    lease_root.symlink_to(outside, target_is_directory=True)

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "lease is a symlink" in str(result["tmp_reap_error"])
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_unlinks_child_symlinks_without_following_them.
def test_runtime_tmp_reap_unlinks_child_symlinks_without_following_them(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    lease_root = namespace_root / "task"
    lease_root.mkdir(parents=True)
    (lease_root / "payload.bin").write_bytes(b"lease")
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = outside / "keep.txt"
    payload.write_text("keep", encoding="utf-8")
    (lease_root / "outside-link").symlink_to(outside, target_is_directory=True)

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result == {"tmp_bytes_freed": 5 + len(str(outside)), "tmp_reap_error": None}
    assert not lease_root.exists()
    assert payload.read_text(encoding="utf-8") == "keep"


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_repairs_mode_zero_descendant.
def test_runtime_tmp_reap_repairs_mode_zero_descendant(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    lease_root = namespace_root / "task"
    blocked = lease_root / "lu-review-view-restrictive"
    blocked.mkdir(parents=True)
    (blocked / "evidence.txt").write_text("sealed", encoding="utf-8")
    blocked.chmod(0o000)

    try:
        result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

        assert result["tmp_reap_error"] is None
        assert not os.path.lexists(lease_root)
    finally:
        if blocked.exists():
            blocked.chmod(0o700)


# Ported from tests/test_delegate.py::test_runtime_tmp_remove_absent_lease_returns_cleanly.
def test_runtime_tmp_remove_absent_lease_returns_cleanly(tmp_path, monkeypatch):
    """A lease a concurrent sweep already removed is success, not a survived-cleanup raise."""
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    namespace_root.mkdir()
    lease_root = namespace_root / "task-already-gone"

    runtime_tmp._remove_runtime_tmp_lease(lease_root, namespace_root)

    assert not os.path.lexists(lease_root)


# Ported from tests/test_delegate.py::test_runtime_tmp_reap_records_cleanup_errors.
def test_runtime_tmp_reap_records_cleanup_errors(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    namespace_root = tmp_path / "learn-ukrainian"
    lease_root = namespace_root / "task"
    lease_root.mkdir(parents=True)

    def fail_rmtree(*_args, **_kwargs):
        raise OSError("permission denied")

    fail_rmtree.avoids_symlink_attacks = True
    monkeypatch.setattr(runtime_tmp.shutil, "rmtree", fail_rmtree)

    result = runtime_tmp._reap_runtime_tmp_lease(lease_root, namespace_root)

    assert result["tmp_bytes_freed"] == 0
    assert "permission denied" in str(result["tmp_reap_error"])
    assert lease_root.exists()


# Ported from tests/test_dispatch_xdist_cap.py::test_worker_env_resolves_cap_plugin_for_nested_pytest_outside_rootdir.
def test_worker_env_resolves_cap_plugin_for_nested_pytest_outside_rootdir(tmp_path: Path, spec) -> None:
    """#8795: a real dispatch-worker env must not break a nested pytest.

    ``PYTEST_PLUGINS=ci.pytest_dispatch_cap`` only resolves via pyproject.toml's
    rootdir-relative ``pythonpath = ["scripts"]``. A test like
    ``tests/test_pytest_tmp_guard.py`` spawns a nested pytest from ``tmp_path``
    with its own bare ini (no ``pythonpath`` entry), which used to fail with
    ``ImportError: No module named 'ci'`` once it inherited the worker's
    ``PYTEST_PLUGINS``. This builds a real worker env via
    ``scripts.delegate._build_worker_env`` (not a hand-rolled stand-in) and
    proves a pytest project with no local pythonpath config still loads the
    cap plugin cleanly.
    """
    worker_env = child_env(dataclasses.replace(
        spec, task_id="impl-8795-nested-pytest", agent="codex", worktree=SOURCE,
    ))
    assert worker_env["PYTEST_PLUGINS"] == "ci.pytest_dispatch_cap"
    assert worker_env["PYTHONPATH"] == str(SOURCE / "scripts")
    project = tmp_path / "nested-project"
    project.mkdir()
    (project / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "test_sample.py"],
        cwd=project,
        env=worker_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    combined = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined
    assert "No module named 'ci'" not in combined
    assert "1 passed" in completed.stdout


# Ported fixture from tests/test_delegate_held_work.py::lease.
@pytest.fixture
def g0_lease(tmp_path, monkeypatch):
    from scripts.dispatcher import runtime_tmp

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setenv("LU_SCRATCH_ROOT", str(tmp_path))
    monkeypatch.setattr(runtime_tmp, "scratch_scan_roots", lambda: [tmp_path])
    monkeypatch.setattr(runtime_tmp.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(runtime_tmp, "_main_checkout_root", lambda _root: tmp_path)
    root, namespace = runtime_tmp._create_runtime_tmp_lease("held-worker")
    record = {
        "task_id": "held-worker",
        "run_nonce": "attempt-1",
        "status": "done",
        "pid": None,
        "runtime_tmp_root": str(root),
        "runtime_tmp_namespace_root": str(namespace),
    }
    store.record_path(record["task_id"]).parent.mkdir(parents=True, exist_ok=True)
    store.replace(record)
    return root, namespace, record


# Ported from tests/test_delegate_held_work.py::test_supported_evidence_directory_is_preserved_before_lease_reap.
def test_supported_evidence_directory_is_preserved_before_lease_reap(g0_lease, tmp_path):
    from scripts.dispatcher import runtime_tmp
    from scripts.fleet import ignored_task_output as output
    from scripts.fleet import runtime_held_work as held

    root, namespace, record = g0_lease
    (root / "evidence" / "screenshots").mkdir(parents=True)
    (root / "evidence" / "publish-review.md").write_text("report\n")
    (root / "evidence" / "screenshots" / "card.png").write_bytes(b"png")
    result = runtime_tmp._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] is None
    assert not root.exists()
    saved = store.read(record["task_id"])
    receipt = saved["preserved_evidence"]
    assert receipt["schema"] == held.EVIDENCE_SCHEMA
    assert receipt["task_id"] == record["task_id"]
    assert receipt["run_nonce"] == record["run_nonce"]
    assert receipt["count"] == 2
    assert output.verify_retrieval(tmp_path, receipt) == receipt["retrieval_proof_sha256"]
    location = tmp_path / receipt["location"]
    assert (location / "publish-review.md").read_text() == "report\n"
    assert (location / "screenshots" / "card.png").read_bytes() == b"png"


# Ported from tests/test_delegate_held_work.py::test_evidence_over_cap_refuses_reap_and_keeps_the_lease.
def test_evidence_over_cap_refuses_reap_and_keeps_the_lease(g0_lease, monkeypatch):
    from scripts.dispatcher import runtime_tmp
    from scripts.fleet import runtime_held_work as held

    root, namespace, record = g0_lease
    (root / "evidence").mkdir()
    (root / "evidence" / "archive.tar.gz").write_bytes(b"x" * 64)
    monkeypatch.setattr(held.output, "MAX_PRESERVED_BYTES", 8)
    result = runtime_tmp._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] == held.EvidenceLimitExceeded.code
    assert root.exists()
    assert (root / "evidence" / "archive.tar.gz").read_bytes() == b"x" * 64
    assert "preserved_evidence" not in store.read(record["task_id"])


# Ported from tests/test_delegate_held_work.py::test_linked_evidence_refuses_reap_without_following_the_link.
def test_linked_evidence_refuses_reap_without_following_the_link(g0_lease, tmp_path):
    from scripts.dispatcher import runtime_tmp
    from scripts.fleet import runtime_held_work as held

    root, namespace, record = g0_lease
    (root / "evidence").mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    (root / "evidence" / "link.txt").symlink_to(outside)
    result = runtime_tmp._reap_runtime_tmp_lease(root, namespace, task_record=record)
    assert result["tmp_reap_error"] == held.EvidencePreservationError.code
    assert root.exists()
    assert outside.read_text() == "secret"


# Ported from tests/test_delegate_held_work.py::test_evidence_written_after_the_receipt_refuses_before_deletion.
def test_evidence_written_after_the_receipt_refuses_before_deletion(g0_lease, monkeypatch):
    """The pre-deletion recheck keeps a lease when a file appears after preservation returns."""
    from scripts.dispatcher import runtime_tmp
    from scripts.fleet import runtime_held_work as held

    root, namespace, record = g0_lease
    (root / "evidence").mkdir()
    (root / "evidence" / "report.md").write_text("report\n")
    original = held.preserve_evidence

    def preserve_then_write_again(*args, **kwargs):
        receipt = original(*args, **kwargs)
        (root / "evidence" / "after-receipt.md").write_text("written after the final enumeration")
        return receipt

    monkeypatch.setattr(held, "preserve_evidence", preserve_then_write_again)
    result = runtime_tmp._reap_runtime_tmp_lease(root, namespace, task_record=record)

    assert result["tmp_reap_error"] == held.EvidencePreservationError.code
    assert result["tmp_bytes_freed"] == 0
    assert root.exists()
    assert (root / "evidence" / "after-receipt.md").read_text() == "written after the final enumeration"


# Ported from tests/test_delegate_held_work.py::test_worker_env_exposes_the_supported_evidence_directory.
def test_worker_env_exposes_the_supported_evidence_directory(tmp_path):
    from scripts.dispatcher import worker_environment

    lease_root = tmp_path / "lease"
    env = worker_environment._build_worker_env(
        task_id="evidence-worker",
        dispatch_agent="codex",
        runtime_tmp_root=lease_root,
        runtime_tmp_namespace_root=tmp_path / "namespace",
    )
    assert env["LU_TASK_EVIDENCE_DIR"] == str(lease_root / "evidence")


# Ported from tests/audit/test_lint_agent_trailer.py::test_worker_env_carries_lu_x_agent_trailer.
def test_worker_env_carries_lu_x_agent_trailer(monkeypatch: pytest.MonkeyPatch) -> None:
    """worker_environment.py exports LU_X_AGENT_TRAILER into worker_env via _build_worker_env and _x_agent_trailer."""
    from scripts.dispatcher import worker_environment


    # Direct helper verification
    assert worker_environment._x_agent_trailer("codex", "dispatch-trailer-test") == "X-Agent: codex/dispatch-trailer-test"
    assert worker_environment._x_agent_trailer("codex", "codex-1472-foo") == "X-Agent: codex/1472-foo"

    env = worker_environment._build_worker_env(
        task_id="dispatch-trailer-test",
        dispatch_agent="codex",
        base_env={},
    )
    assert env["LU_X_AGENT_TRAILER"] == "X-Agent: codex/dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-trailer-test"
    assert env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == "codex"


# Ported from tests/test_delegate.py::test_dispatch_checks_out_the_excluded_trees_its_owned_paths_need.
def test_dispatch_checks_out_the_excluded_trees_its_owned_paths_need(sandbox, monkeypatch):
    """--owned-path keeps its excluded tree; research paths only add (#10777)."""
    from scripts.dispatcher import cli

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(git, "resolve_repo", lambda _key: (
        sandbox.repo, {"key": "public", "github": str(sandbox.remote), "transport": "file"},
    ))
    monkeypatch.setattr(worker, "start", Mock())
    create = git.create_worktree
    sparse_includes = {}

    def recording_create(repo, path, branch, sha, **kwargs):
        sparse_includes[path.name] = tuple(kwargs["sparse_include"])
        return create(repo, path, branch, sha, **kwargs)

    monkeypatch.setattr(git, "create_worktree", recording_create)
    for task_id, extra in (
        ("sparse-owned", ["--owned-path", "site/src/data/curriculum-stats.json"]),
        ("sparse-owned-alias", ["--owned-path", "./site/src/data/curriculum-stats.json"]),
        (
            "sparse-owned-and-research",
            ["--owned-path", "site/src/data/curriculum-stats.json",
             "--research-owned-path", "registry/projects/open_model_data/x.json"],
        ),
    ):
        assert cli.main([
            "dispatch", "--agent", "codex", "--model", "echo", "--task-id", task_id,
            "--prompt", "test", "--mode", "read-only", *extra,
        ]) == 0

    assert sparse_includes == {
        "sparse-owned": ("site/src/data",),
        "sparse-owned-alias": ("site/src/data",),
        "sparse-owned-and-research": ("site/src/data", "registry/projects"),
    }
