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


def test_ownership_walk_does_not_fetch_full_history(tmp_path, monkeypatch):
    """A multi-gigabyte remote must not be fetched whole: only blob-less history since the task base."""
    remote, tree = tmp_path / "remote.git", tmp_path / "tree"
    run_git(tmp_path, "init", "--bare", str(remote))
    run_git(remote, "config", "uploadpack.allowFilter", "true")
    run_git(tmp_path, "init", "-b", "main", str(tree))
    run_git(tree, "config", "user.email", "stub@example.invalid")
    run_git(tree, "config", "user.name", "Stub")
    run_git(tree, "remote", "add", "origin", str(remote))
    old = set()
    for n in range(20):
        monkeypatch.setenv("GIT_COMMITTER_DATE", f"2020-01-{n + 1:02d}T00:00:00Z")
        (tree / f"old-{n}.txt").write_text(f"old history {n}\n")
        run_git(tree, "add", ".")
        run_git(tree, "commit", "-m", f"old history {n}")
        old.update(run_git(tree, "rev-parse", "HEAD", f"HEAD:old-{n}.txt").split())
    monkeypatch.delenv("GIT_COMMITTER_DATE")
    run_git(tree, "commit", "--allow-empty", "-m", "task base")
    run_git(tree, "push", "origin", "main")
    run_git(tree, "checkout", "-b", "sol/fetch")
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
    assert {base, head} <= present
    assert old.isdisjoint(present)
    assert run_git(tree, "rev-parse", "HEAD:delivered.txt") not in present
    worker._enforce_delivery(record)
    assert (record["status"], record.get("error")) == ("done", None)


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
