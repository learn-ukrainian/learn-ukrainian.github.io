"""Exercise the real dispatcher with stub processes and real disposable Git remotes."""

import concurrent.futures
import contextlib
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

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.cli import ALIASES, build_parser
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.providers import muse
from scripts.dispatcher.types import TaskSpec
from scripts.lib import rules_core
from scripts.review.record_cf_verdict import _review_branch

SOURCE = Path(__file__).resolve().parents[2]


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()


@pytest.fixture
def sandbox(tmp_path, hermetic_monitor):
    repo, tasks = tmp_path / "public", tmp_path / "tasks"
    remote = tmp_path / "remote.git"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "stub@example.invalid")
    run_git(repo, "config", "user.name", "Stub")
    for relative in ("scripts/dispatcher", "scripts/common", "scripts/review", "scripts/storage", "scripts/lib",
                     "agents_extensions/shared/rules"):
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
    # D5: expose only the credit reader, keeping the common reaper stub isolated.
    for name in ("credit_lane.py", "claude_account_lane.py"):
        shutil.copy(SOURCE / "scripts/fleet" / name, repo / "scripts/fleet" / name)
    (repo / "scripts/fleet/__init__.py").write_text(f"__path__.append({str(SOURCE / 'scripts/fleet')!r})\n")
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
    shutil.copy(SOURCE / "scripts/config/credit_lanes.yaml", config / "credit_lanes.yaml")
    shutil.copy(Path(__file__).with_name("stub_provider.py"), repo / "scripts/dispatcher/providers/codex.py")
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "fixture")
    run_git(repo, "init", "--bare", "-b", "main", str(remote))
    run_git(repo, "remote", "add", "origin", str(remote))
    run_git(repo, "push", "-u", "origin", "main")
    env = {**os.environ, "LU_TASKS_DIR": str(tasks)}
    env.pop("PYTHONPATH", None)
    # Admission observes a disposable remote and an empty PR registry, never GitHub.
    binary_dir = tmp_path / "admission-bin"
    binary_dir.mkdir()
    gh = binary_dir / "gh"
    gh.write_text(f"#!{sys.executable}\nimport sys\n"
                  "assert sys.argv[1:3] == ['pr', 'list'], sys.argv\nprint('[]')\n")
    gh.chmod(0o755)
    env["PATH"] = str(binary_dir) + os.pathsep + env.get("PATH", os.defpath)

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
        if "workspace-write" in args and "--owned-path" not in args:
            args = (*args, "--owned-path", "delivered.txt", "--owned-path", "fix.txt")
        result = cli("dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--provider", model,
                     "--prompt", "literal final response", *args)
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


@pytest.mark.parametrize("flags", [(), ("--worktree",)], ids=["automatic", "worktree"])
def test_held_worktree_lock_exits_one_without_traceback(sandbox, flags):
    """A contended worktree lock must produce the legacy one-line dispatch failure."""
    from scripts.orchestration import worktree_claims

    task_id = "held-lock"
    worktree = sandbox.repo / ".worktrees/dispatch/codex" / task_id
    with worktree_claims.worktree_lock(worktree, lock_dir=sandbox.repo / ".git" / worktree_claims.LOCK_DIR_NAME):
        result = subprocess.run(
            [sys.executable, "-c",
             "from scripts.orchestration import worktree_claims; "
             "worktree_claims.DEFAULT_LOCK_TIMEOUT_S = 0.01; "
             "from scripts.dispatcher import cli; raise SystemExit(cli.main())",
             "dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--task-id", task_id,
             "--prompt", "Inspect the parser.", *flags],
            cwd=sandbox.repo, env=sandbox.env, text=True, capture_output=True, timeout=10,
        )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == (
        f"❌ failed to lock worktree for '{task_id}': worktree lock for {worktree.resolve()} "
        "still held by another process after 0.01s\n"
    )
    assert "Traceback" not in result.stderr
    assert not list(sandbox.tasks.glob("*.json"))
    assert not worktree.exists()


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
    sandbox.env["PATH"] = str(binary_dir) + os.pathsep + sandbox.env["PATH"]
    sandbox.env["CURSOR_API_KEY"] = "stub-process-key"
    run_git(sandbox.repo, "branch", "review-source")
    run_git(sandbox.repo, "push", "origin", "review-source")
    dispatched = sandbox.cli(
        "dispatch",
        "--agent",
        "grok",
        "--model",
        "grok-4.7-high",
        "--prompt",
        "The prompt claims Grok 4.7 256K High",
        "--mode",
        mode,
        "--branch",
        "review-source",
        "--owned-path", "delivered.txt",
    )
    record = sandbox.settle(dispatched.stdout.splitlines(), expected=0 if mode == "read-only" else 1)
    known = len(models) == 1
    assert record["schema_version"] == 2
    assert record["model"] == "grok-4.7-high"
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
    original = b"exact\nbytes\n"
    injected = rules_core.with_core(original.decode()).encode()
    assert injected.startswith(rules_core.core_block('core').encode() + b'\n\n')
    assert injected.endswith(original)
    assert Path(record['prompt_file']).read_bytes() == original
    assert Path(record['effective_prompt_file']).read_bytes() == injected
    assert Path(record["prompt_file"]).with_suffix(".stdin").read_bytes() == injected
    assert Path(record["result_file"]).read_bytes() == b"exact\nbytes\n"
    assert record['effective_prompt_sha256'] == hashlib.sha256(injected).hexdigest()
    assert record["prompt_sha256"] == hashlib.sha256(b"exact\nbytes\n").hexdigest()


def test_prompt_over_pipe_buffer_reaches_late_reading_child_complete(sandbox):
    stub = sandbox.repo / "scripts/dispatcher/providers/codex.py"
    stub.write_text(stub.read_text().replace(
        '    text = sys.stdin.buffer.read().decode()',
        '    time.sleep(0.5)\n    text = sys.stdin.buffer.read().decode()',
    ))
    prompt = ("0123456789abcdef" * 65536).encode()
    result = sandbox.cli(
        "dispatch", "--agent", "codex", "--model", "file", "--prompt-file", "-",
        stdin=prompt.decode(),
    )
    record = sandbox.settle(result.stdout.splitlines())
    received = Path(record["result_file"]).read_bytes()
    assert record["status"] == "done"
    assert len(received) == len(prompt)
    assert received == prompt
    assert hashlib.sha256(received).hexdigest() == hashlib.sha256(prompt).hexdigest()
    assert record["result_sha256"] == hashlib.sha256(prompt).hexdigest()


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


def _killed_review_supervisor(sandbox, tmp_path, model):
    """Dispatch a held Codex read-only review on ``model``, SIGKILL its supervisor once gone; the provider pid."""
    from scripts.common import test_slots

    for name in (test_slots.HOLDER_ENV, test_slots.SESSION_ENV, "CI"):
        sandbox.env.pop(name, None)
    sandbox.env.update({test_slots.ENABLE_ENV: "on", test_slots.DIR_ENV: str(tmp_path / "pool"),
                        test_slots.COUNT_ENV: "4", test_slots.WAIT_ENV: "5"})
    task = sandbox.dispatch(model, "--require-review-verdict")
    child = int(await_file(sandbox.tasks / f"{task[0]}.started"))
    if model == "governed":
        assert await_file(sandbox.tasks / f"{task[0]}.joined") == "joined"
    record = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert record["review_test_slots"]["outcome"] == "held"
    os.kill(record["pid"], signal.SIGKILL)
    deadline = time.monotonic() + 10
    while worker._identity(record["pid"]) == record["process_start"]:
        assert time.monotonic() < deadline, "supervisor survived SIGKILL"
        time.sleep(0.02)
    assert worker._identity(child) is not None, "the provider must outlive its supervisor here"
    return task, child


def _pool_report(sandbox):
    from scripts.common import test_slots

    report = test_slots.status(sandbox.env)
    assert report["error"] is None, report
    return report


def _provider_environment(pid, sandbox):
    """The provider's own environment, on the test's pool (the provider environment carries no override)."""
    from scripts.common import test_slots

    entries = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
    environment = dict(entry.decode().split("=", 1) for entry in entries if b"=" in entry)
    return {**environment, test_slots.DIR_ENV: sandbox.env[test_slots.DIR_ENV]}


def test_a_killed_supervisors_review_hold_ends_with_it_and_its_provider_holds_no_pool_descriptor(sandbox, tmp_path):
    """Defect class: a provider that outlives its supervisor keeps the review hold, so slots strand without bound."""
    from scripts.common import test_slots

    task, child = _killed_review_supervisor(sandbox, tmp_path, "blocked")
    try:
        pool = os.path.realpath(tmp_path / "pool")
        links = [os.readlink(entry) for entry in Path(f"/proc/{child}/fd").iterdir()]
        assert not [link for link in links if link == pool or link.startswith(pool + os.sep)]
        report = _pool_report(sandbox)
        assert report["slots_in_use"] + report["slots_draining"] == 0
        environment = _provider_environment(child, sandbox)
        assert environment[test_slots.HOLDER_ENV]
        assert test_slots.inherited_hold(environment) is None
        assert worker._identity(child) is not None
        assert sandbox.settle(task, expected=1)["status"] == "crashed"
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(child, signal.SIGKILL)


def test_a_governed_turn_in_flight_keeps_its_slots_past_a_killed_supervisor_and_nothing_new_joins(sandbox, tmp_path):
    """Defect class: a killed supervisor frees slots a running test still uses, or lets a new run join its hold."""
    from scripts.common import test_slots

    task, child = _killed_review_supervisor(sandbox, tmp_path, "governed")
    try:
        governed = int(await_file(sandbox.tasks / f"{task[0]}.grandchild"))
        report = _pool_report(sandbox)
        assert (report["slots_in_use"], report["slots_draining"]) == (0, worker.admission.REVIEW_TEST_SLOTS)
        assert test_slots.join_inherited(_provider_environment(child, sandbox), wait_s=0.3) is None
        (sandbox.tasks / f"{task[0]}.child-release").touch()
        deadline = time.monotonic() + 10
        while worker._identity(governed) is not None:
            assert time.monotonic() < deadline, "the governed run did not end once released"
            time.sleep(0.02)
        report = _pool_report(sandbox)
        assert report["slots_in_use"] + report["slots_draining"] == 0
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(child, signal.SIGKILL)


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
    ("pushed-dirty", "workspace-write", ["delivered.txt"], "no_deliverable", "worktree_dirty_or_unknown"),
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
        record.update(mode="workspace-write", provider=model, status="running", owned_paths=list(owned or []))
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
    run_git(tree, "commit", "-m", "preexisting outside scope\n\nX-Agent: codex/gpt-6.1-sol")
    run_git(tree, "push", "origin", "HEAD")
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
        "dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--provider", "pushed", "--prompt", "deliver",
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


def test_isolated_private_https_fetch_credentials_never_escape_exact_registered_remote(
    sandbox, delivery_settle, monkeypatch, tmp_path,
):
    """Missing private HTTPS auth rejected pushed work; host-wide auth could leak to another repo.

    Real Git and a fake gh helper exercise credential selection on both production
    fetch paths. Only the network transport is replaced by the disposable remote
    after credential fill succeeds. No live credentials or network are used.
    """
    import shlex

    from scripts.common import git_credentials
    from scripts.orchestration import merge_closeout

    record, settle = delivery_settle
    record = settle("pushed")
    tree = Path(record["cwd"])
    remote = "https://github.com/fixture/private.git"
    run_git(sandbox.repo, "update-ref", "refs/pull/42/head", record["head_sha"])
    run_git(tree, "push", "origin", "HEAD:refs/pull/42/head")
    run_git(tree, "config", "remote.origin.url", remote)
    record["worktree_remote_url"] = remote
    registry = tmp_path / "registry.yaml"
    registry.write_text(yaml.safe_dump({"repos": {"fixture": {"github": "fixture/private", "transport": "https"}}}))
    monkeypatch.setattr(git_credentials, "CONFIG", registry)
    log = tmp_path / "helper-contexts"
    marker = tmp_path / "untrusted-helper-ran"
    fake_gh = tmp_path / "fake gh"
    fake_gh.write_text(
        '#!/bin/sh\n[ "$*" = "auth git-credential get" ] || exit 1\n'
        f"cat >> {shlex.quote(str(log))}\n"
        "printf 'username=fixture-user\\npassword=fixture-password\\n'\n"
    )
    fake_gh.chmod(0o700)
    monkeypatch.setenv("AGENT_REAL_GH", str(fake_gh))
    home = tmp_path / "home"
    home.mkdir()
    included = tmp_path / "untrusted.config"
    included.write_text(f"[credential]\n helper = !touch {shlex.quote(str(marker))}\n[worker]\n global = consulted\n")
    (home / ".gitconfig").write_text(f"[include]\n path = {included}\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(included))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(included))
    # The cleanup runner also has to reset URL-scoped primary-repo helpers.
    run_git(tree, "config", f"credential.{remote}.helper", f"!touch {shlex.quote(str(marker))}")
    real_run = subprocess.run
    prefixes = []
    local_imports = []

    def local_transport(argv, **kwargs):
        if "fetch" not in argv:
            return real_run(argv, **kwargs)
        index = argv.index("fetch")
        prefix = argv[:index]
        env = kwargs["env"]
        assert env["GIT_CONFIG_GLOBAL"] == env["GIT_CONFIG_SYSTEM"] == os.devnull
        assert env["GIT_TERMINAL_PROMPT"] == "0" and env["PATH"] == os.defpath
        credentials = real_run(
            [*prefix, "credential", "fill"], cwd=kwargs.get("cwd"), env=env,
            input=f"url={remote}\n\n", capture_output=True, text=True, check=False, timeout=10,
        )
        if any(arg.startswith("file://") for arg in argv[index:]):
            assert env["GIT_ALLOW_PROTOCOL"] == "file"
            assert credentials.returncode != 0
            assert "fixture-password" not in credentials.stdout
            assert not any(".helper=!" in arg for arg in prefix)
            local_imports.append(argv)
            return real_run(argv, **kwargs)
        assert Path(kwargs.get("cwd") or argv[argv.index("-C") + 1]) != sandbox.repo
        assert credentials.returncode == 0
        assert "username=fixture-user\npassword=fixture-password\n" in credentials.stdout
        before = log.read_text()
        config = real_run([*prefix, "config", "--list", "--includes"], cwd=kwargs.get("cwd"), env=env,
                          capture_output=True, text=True, check=True, timeout=10).stdout
        assert "worker.global" not in config
        for other in (
            "https://github.com/fixture/other.git", "https://github.com/other/private.git",
            remote + "/child", remote + "-suffix", remote.removesuffix(".git"),
            "https://other.invalid/fixture/private.git", "http://github.com/fixture/private.git",
        ):
            result = real_run([*prefix, "credential", "fill"], cwd=kwargs.get("cwd"), env=env,
                              input=f"url={other}\n\n", capture_output=True, text=True, check=False, timeout=10)
            assert result.returncode != 0 and "fixture-password" not in result.stdout
        assert log.read_text() == before
        prefixes.append((prefix, kwargs.get("cwd"), env))
        fetch_args = [str(sandbox.remote) if arg == "origin" else arg for arg in argv[index:]]
        return real_run([*prefix, *fetch_args], **kwargs)

    monkeypatch.setattr(subprocess, "run", local_transport)
    worker._enforce_delivery(record)
    assert (record["status"], record["error"]) == ("done", None)
    assert merge_closeout._fetch_live_pr_head(sandbox.repo, 42) == (record["head_sha"], None)
    assert len(prefixes) >= 3  # ownership's bounded fetches and closeout's live PR fetch
    assert len(local_imports) == 1
    expected_contexts = log.read_text()
    assert expected_contexts.count("protocol=https\nhost=github.com\npath=fixture/private.git\n") == len(prefixes)
    assert not marker.exists()
    for other in ("https://github.com/fixture/other.git", "https://user@github.com/fixture/private.git",
                  "git@github.com:fixture/private.git", str(sandbox.remote)):
        assert git_credentials.verification_credentials(other) == []


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
    run_git(sandbox.repo, "push", "origin", pinned)
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--branch", pinned)
    if target in {None, "prefix"}:
        run_git(sandbox.remote, "update-ref", "-d", f"refs/heads/{pinned}")
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
        "owned_paths_verification_failed" if target in {None, "prefix", "unrelated"}
        else "worktree_dirty_or_unknown" if dirty else "no_commits_or_unknown" if not commits
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


@pytest.mark.parametrize("source", ["private-root", "symlink", "carrier-text"])
def test_lifecycle_input_cannot_bypass_private_policy(sandbox, source):
    """Lifecycle sources and effective carrier text must pass dispatch admission."""
    from tests.dispatcher.test_advisory import _lifecycle_file

    shutil.copy(Path(__file__).with_name("stub_provider.py"), sandbox.repo / "scripts/dispatcher/providers/opencode.py")
    private = sandbox.repo.parent / "private"
    private.mkdir()
    if source == "carrier-text":
        lifecycle = _lifecycle_file(sandbox.repo)
        config = sandbox.repo / "scripts/config/fleet_repos.yaml"
        repos = yaml.safe_load(config.read_text())
        repos["repos"]["private"]["github"] = "org/repo"
        config.write_text(yaml.safe_dump(repos))
        expected = "private path input"
    else:
        lifecycle = _lifecycle_file(private)
        if source == "symlink":
            alias = sandbox.repo / "carrier.json"
            alias.symlink_to(lifecycle)
            lifecycle = alias
        expected = "private lifecycle file"

    result = sandbox.cli(
        "dispatch", "--agent", "opencode", "--model", "deepseek-v4.1-flash",
        "--prompt", "Inspect the task", "--task-id", "lifecycle-refused",
        "--lifecycle-file", str(lifecycle), expected=2,
    )

    assert expected in result.stderr
    assert not list(sandbox.tasks.glob("*.json"))
    assert not (sandbox.repo / ".worktrees").exists()


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


def test_delegate_dispatch_leads_with_the_core(sandbox):
    """Ported from tests/test_rules_core_loading.py::test_delegate_dispatch_leads_with_the_core."""
    record = sandbox.settle(sandbox.dispatch('file'))
    prompt = Path(record['effective_prompt_file']).read_text()
    assert record['prompt_blocks'] == ['rules_core']
    assert record['effective_prompt_sha256'] == hashlib.sha256(prompt.encode()).hexdigest()
    assert prompt.startswith(rules_core.core_block('core') + '\n\n')
    assert 'literal final response' in prompt
    assert prompt.count(rules_core.core_block('core')) == 1


def test_delegate_rules_seat_flag_and_env(sandbox):
    """Ported from tests/test_rules_core_loading.py::test_delegate_rules_seat_flag_and_env."""
    for flags in [('--rules-seat', 'content'), ()]:
        sandbox.env['LU_RULES_SEAT'] = 'content' if not flags else 'core'
        record = sandbox.settle(sandbox.dispatch('file', *flags))
        prompt = Path(record['effective_prompt_file']).read_text()
        assert prompt.startswith(rules_core.core_block('content') + '\n\n')

def test_initial_response_timeout_default_is_600():
    """Ported from tests/test_delegate.py::test_initial_response_timeout_default_is_600."""
    args = build_parser().parse_args(["dispatch", "--agent", "codex", "--model", "gpt-6.1-sol", "--prompt", "hi"])
    assert args.initial_response_timeout == 600
    assert args.silence_timeout == 3600


def test_run_worker_silence_timeout_kills_silent_subprocess(sandbox):
    """Ported from tests/test_delegate.py with the same test name, including process-tree cleanup."""
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "30", "--silence-timeout", "1")
    record = sandbox.settle(task, expected=1)
    assert time.monotonic() - started < 6
    assert record["returncode"] == -signal.SIGKILL
    assert record["status"] == "timeout"
    assert "stdout_silence_timeout" in record["stderr_excerpt"]
    assert record["silence_timeout"] == 1
    grandchild = int(Path(record["prompt_file"]).with_suffix(".grandchild").read_text())
    assert worker._identity(grandchild) is None


def test_run_worker_initial_response_timeout_still_reaps_silent_startup(sandbox):
    """Ported from tests/test_delegate.py with the same test name."""
    started = time.monotonic()
    task = sandbox.dispatch("tree", "--hard-timeout", "30", "--silence-timeout", "30",
                            "--initial-response-timeout", "1")
    record = sandbox.settle(task, expected=1)
    assert time.monotonic() - started < 6
    assert record["returncode"] == -signal.SIGKILL
    assert record["status"] == "timeout"
    excerpt = record["stderr_excerpt"]
    assert "initial_response_timeout" in excerpt
    assert "fired after 1s" in excerpt
    assert "no first observable startup activity" in excerpt
    assert "--initial-response-timeout" in excerpt


@pytest.mark.parametrize("output", ["sys.stdout", "sys.stderr"])
def test_run_worker_periodic_stdout_avoids_silence_timeout(sandbox, output):
    """Ported from tests/test_delegate.py with the same test name, observing both output streams."""
    stub = sandbox.repo / "scripts/dispatcher/providers/codex.py"
    stub.write_text(stub.read_text().replace(
        '    model, prompt, final = sys.argv[1:]',
        f"    for i in range(5):\n        print('tick', file={output}, flush=True)\n        time.sleep(0.2)\n"
        '    model, prompt, final = sys.argv[1:]',
    ))
    task = sandbox.dispatch("echo", "--hard-timeout", "10", "--silence-timeout", "1",
                            "--initial-response-timeout", "1")
    record = sandbox.settle(task)
    assert record["status"] == "done"
    expected = "tick\n" * 5 + "literal final response" if output == "sys.stdout" else "literal final response"
    assert Path(record["result_file"]).read_text() == expected
    assert record["silence_timeout"] == 1
    assert record["initial_response_timeout"] == 1


# Ports of the legacy status-or-fail and child identity contracts in tests/test_delegate.py.
def test_status_or_fail_running_task_exits_zero_quiet(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_running_task_exits_zero_quiet."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "sleep-task.json").write_text(json.dumps(dict(
        task_id="sleep-task", status="running", started_at=store.now(),
        pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize("case, expected_status, nonce", [
    ("dead-pid", "stale", "record-nonce"),
    ("mismatched-process-start", "stale", "record-nonce"),
    ("missing-process-start", "stale", "record-nonce"),
    ("nonce-mismatch", "stale_run_nonce", "wrong-nonce"),
])
def test_status_or_fail_dead_supervisor_never_reported_alive(
    tmp_path, monkeypatch, capsys, case, expected_status, nonce,
):
    """Reject stale supervisor identities and nonces without rewriting the record."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    record = dict(
        task_id="sleep-task", status="running", started_at=store.now(),
        run_nonce="record-nonce", pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )
    if case == "dead-pid":
        with subprocess.Popen([sys.executable, "-c", "pass"]) as process:
            process.wait(timeout=10)
        record["pid"] = process.pid
    elif case == "mismatched-process-start":
        record["process_start"] = "different-process-start"
    elif case == "missing-process-start":
        record.pop("process_start")
    path = tmp_path / "sleep-task.json"
    original = json.dumps(record).encode()
    path.write_bytes(original)

    rc = cli.main(["status-or-fail", "sleep-task", "--verbose", "--run-nonce", nonce])

    assert rc == 1
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["status"] == expected_status
    assert payload["alive"] is False
    assert payload["run_nonce"] == (None if case == "nonce-mismatch" else "record-nonce")
    assert f"task sleep-task is not running (status={expected_status}, age=" in captured.err
    assert path.read_bytes() == original


@pytest.mark.parametrize("status", [
    "done", "failed", "timeout", "rate_limited", "cancelled", "crashed", "dry_run",
    "needs_finalize", "no_deliverable",
])
def test_status_or_fail_completed_task_exits_one(tmp_path, monkeypatch, capsys, status):
    """Ported from tests/test_delegate.py::test_status_or_fail_completed_task_exits_one."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "sleep-task.json").write_text(json.dumps(dict(
        task_id="sleep-task", status=status, started_at=store.now(),
    )))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 1
    captured = capsys.readouterr()
    assert f"task sleep-task is not running (status={status}, age=" in captured.err
    assert captured.err.rstrip().endswith("s)")


def test_status_or_fail_unknown_task_exits_one(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_unknown_task_exits_one."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))

    rc = cli.main(["status-or-fail", "missing"])

    assert rc == 1
    captured = capsys.readouterr()
    assert "task missing is not running" in captured.err
    assert "task not found" in captured.err


def test_status_or_fail_monitor_api_down_exits_two(monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_monitor_api_down_exits_two.

    V2's unavailable authority is its task store, rather than the Monitor API.
    """
    monkeypatch.setattr(store, "read", Mock(side_effect=OSError("unavailable")))

    rc = cli.main(["status-or-fail", "sleep-task"])

    assert rc == 2
    captured = capsys.readouterr()
    assert "Dispatcher state unavailable" in captured.err


def test_status_or_fail_verbose_byte_compatible_without_run_nonce(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_status_or_fail_verbose_byte_compatible_without_run_nonce."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    (tmp_path / "test-sof-task.json").write_text(json.dumps(dict(
        task_id="test-sof-task", status="running", started_at="2026-08-20T10:00:00Z",
        run_nonce="sof-nonce-12345", pid=os.getpid(), process_start=worker._identity(os.getpid()),
    )))

    rc = cli.main(["status-or-fail", "test-sof-task", "--verbose"])
    assert rc == 0
    data_no_nonce = json.loads(capsys.readouterr().out)
    assert list(data_no_nonce.keys()) == ["task_id", "status", "age_s", "alive"]
    assert "run_nonce" not in data_no_nonce

    rc2 = cli.main(["status-or-fail", "test-sof-task", "--verbose", "--run-nonce", "sof-nonce-12345"])
    assert rc2 == 0
    data_with_nonce = json.loads(capsys.readouterr().out)
    assert data_with_nonce["run_nonce"] == "sof-nonce-12345"


@pytest.mark.parametrize("agent", ["codex", "claude", "cursor", "agy", "muse", "opencode", "hermes"])
def test_dispatch_worker_env_carries_dispatch_identity_markers(spec, monkeypatch, agent):
    """Ported from tests/test_delegate.py::test_dispatch_worker_env_carries_dispatch_identity_markers."""
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", "parent-task")
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_AGENT", "parent-agent")

    env = child_env(dataclasses.replace(spec, task_id="dispatch-marker-check", agent=agent))

    assert env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-marker-check"
    assert env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == agent
    assert os.environ["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "parent-task"
    assert os.environ["LEARN_UKRAINIAN_DISPATCH_AGENT"] == "parent-agent"

    process = SimpleNamespace(pid=os.getpid(), stdin=SimpleNamespace(write=Mock(), close=Mock()))
    launch = Mock(return_value=process)
    monkeypatch.setattr(worker.subprocess, "Popen", launch)
    monkeypatch.setenv("LU_DISPATCH_ISOLATION", "fallback")
    monkeypatch.setattr(worker.admission.dispatch_isolation, "_caller_in_driver_scope", lambda: False)
    monkeypatch.setattr(worker, "project_interpreter", Mock(return_value=Path(sys.executable)))
    monkeypatch.setattr(store, "create", Mock(return_value=spec.worktree / "record.json"))
    monkeypatch.setattr(store, "replace", Mock())

    worker.start(dataclasses.replace(spec, task_id="dispatch-marker-check", agent=agent),
                 {"run_nonce": "n" * 32}, b"test", 3600)

    supervisor_env = launch.call_args.kwargs["env"]
    assert supervisor_env["LEARN_UKRAINIAN_DISPATCH_TASK_ID"] == "dispatch-marker-check"
    assert supervisor_env["LEARN_UKRAINIAN_DISPATCH_AGENT"] == agent


# ---- ported from tests/test_delegate_review_test_slots.py and tests/test_delegate.py (C-2188 unit D) ----


def _slot_pool(tmp_path, monkeypatch):
    from scripts.common import test_slots

    path = tmp_path / "pool"
    monkeypatch.setenv(test_slots.ENABLE_ENV, "on")
    monkeypatch.setenv(test_slots.DIR_ENV, str(path))
    monkeypatch.setenv(test_slots.COUNT_ENV, "4")
    monkeypatch.setenv(test_slots.WAIT_ENV, "5")
    monkeypatch.delenv(test_slots.HOLDER_ENV, raising=False)
    monkeypatch.delenv(test_slots.SESSION_ENV, raising=False)
    monkeypatch.delenv("CI", raising=False)
    return path


def _review_slot_hold(**overrides):
    from scripts.dispatcher import admission

    arguments = {"agent": "codex", "mode": "read-only", "review_typed": True, "sealed_attempt": False,
                 "task_id": "review-11230-worker-fixture"}
    arguments.update(overrides)
    return admission.hold_review_test_slots(**arguments)


def test_a_codex_read_only_review_holds_review_slots_for_its_task(tmp_path, monkeypatch) -> None:
    from scripts.common import test_slots
    from scripts.dispatcher import admission

    _slot_pool(tmp_path, monkeypatch)
    hold, record = _review_slot_hold()
    try:
        assert hold is not None and record == {"outcome": "held", "slots": 2, "waited_s": record["waited_s"]}
        holders = test_slots.status()["holders"]
        assert [(entry["task_id"], entry["kind"], entry["slots"]) for entry in holders] == [
            ("review-11230-worker-fixture", "review", 2)
        ]
        env = {**os.environ, **hold.environment(), test_slots.TASK_ENV: "review-11230-worker-fixture"}
        assert test_slots.inherited_hold(env) == admission.REVIEW_TEST_SLOTS
    finally:
        if hold is not None:
            hold.release()
    assert test_slots.status()["slots_in_use"] == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"agent": "claude"},
        {"agent": "agy"},
        {"mode": "workspace-write"},
        {"review_typed": False},
        {"sealed_attempt": True},
    ],
    ids=["claude", "agy", "workspace-write", "not-a-review", "sealed-attempt"],
)
def test_every_other_route_takes_its_own_slots_or_none(tmp_path, monkeypatch, overrides) -> None:
    """No double counting: a seat that can prepare the pool, or runs no tests, holds nothing up front."""
    pool = _slot_pool(tmp_path, monkeypatch)
    assert _review_slot_hold(**overrides) == (None, None)
    assert not pool.exists()


def test_a_disabled_pool_holds_nothing(tmp_path, monkeypatch) -> None:
    from scripts.common import test_slots

    pool = _slot_pool(tmp_path, monkeypatch)
    monkeypatch.setenv(test_slots.ENABLE_ENV, "off")
    assert _review_slot_hold() == (None, {"outcome": "disabled"})
    assert not pool.exists()


def test_a_refused_hold_is_recorded_and_the_review_runs_on(tmp_path, monkeypatch, capsys) -> None:
    from scripts.common import test_slots

    _slot_pool(tmp_path, monkeypatch)
    shared = tmp_path / "shared"
    shared.mkdir(mode=0o777)
    shared.chmod(0o777)  # another user could redirect a pool below it
    monkeypatch.setenv(test_slots.DIR_ENV, str(shared / "pool"))

    assert _review_slot_hold() == (None, {"outcome": "refused", "reason": "pool_unavailable"})
    assert "review test slots refused" in capsys.readouterr().err
    assert not (shared / "pool").exists()


def test_a_dispatched_worker_never_inherits_its_dispatchers_marker(spec, monkeypatch) -> None:
    from scripts.common import test_slots

    monkeypatch.setenv(test_slots.HOLDER_ENV, "2:/elsewhere/holders/x.ticket")
    monkeypatch.setenv(test_slots.SESSION_ENV, "/s")
    env = child_env(dataclasses.replace(spec, agent="codex"))
    assert test_slots.HOLDER_ENV not in env and test_slots.SESSION_ENV not in env


@pytest.mark.parametrize(
    "extra,code",
    [
        # Ported from tests/test_delegate.py (the claude_account refusal table): unknown labels.
        (["--agent", "claude", "--claude-account", "c"], "claude_account_unknown"),
        (["--agent", "claude", "--claude-account", "B"], "claude_account_unknown"),
        (["--agent", "codex", "--claude-account", "b"], "claude_account_seat_unsupported"),
        (["--agent", "claude", "--claude-account", "b"], "claude_account_ambient_conflict"),
        # Ported from test_delegate_review_admission.py::test_bare_pinned_head_refuses_before_probes_worktree_or_task_record.
        *[(list(("--agent", "codex", "--mode", "workspace-write", "--pinned-head", "a" * 40, *flags)),
           "PINNED_HEAD_TARGET_REQUIRED: --pinned-head requires --branch or --pr")
          for flags in ((), ("--worktree",), ("--worktree", "--dry-run"))],
    ],
)
def test_dispatch_refuses_claude_account_before_any_side_effect(tmp_path, monkeypatch, capsys, extra, code):
    from scripts.dispatcher import cli

    tasks = tmp_path / "tasks"
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "e" * 30)
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(tmp_path / "absent.json"))
    for target, name in ((git, "create_worktree"), (git, "resolve_repo"), (worker, "start")):
        monkeypatch.setattr(target, name, lambda *_a, _name=name, **_k: pytest.fail(f"{_name} ran before refusal"))

    assert cli.main(["dispatch", "--task-id", "claude-account-refused", "--prompt", "test", "--model", "m", *extra]) == 2

    err = capsys.readouterr().err
    expected = code if code.startswith("PINNED_HEAD_TARGET_REQUIRED") else f"CLAUDE_ACCOUNT_REFUSED: {code}"
    assert expected + "\n" in err
    assert "fixture-ambient" not in err
    assert not tasks.exists()


def _spawn_refused_record(tmp_path, monkeypatch, task_id):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    path = store.record_path(task_id)
    record = {"task_id": task_id, "run_nonce": "n" * 32, "status": "spawning", "pid": None,
              "prompt_file": str(path.with_suffix(".prompt"))}
    spec = TaskSpec(task_id, "codex", "m", None, "read-only", tmp_path, path.with_suffix(".prompt"),
                    path.with_suffix(".result"))
    return spec, record, path


def test_dispatch_ambiguous_scope_start_marks_task_failed(tmp_path, monkeypatch) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "ambiguous-scope")

    def explode(*_args, **_kwargs):
        raise dispatch_isolation.DispatchIsolationError(
            "systemd-run: worker start marker arrived after the startup timeout (2s) "
            "for unit lu-worker-ambiguous-scope; the scope was stopped and will not be relaunched"
        )

    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", explode)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_isolation_failed: ")
    assert "will not be relaunched" in state["error"]


@pytest.mark.parametrize(
    "reason",
    ["inside-driver-scope; systemd-run unavailable", "caller-cgroup-unavailable", "caller-cgroup-unverifiable"],
)
def test_dispatch_fallback_refusal_records_no_worker_started(tmp_path, monkeypatch, reason) -> None:
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "fallback-refusal")
    refusal = f"fallback-refused: {reason}"
    spawn = Mock(side_effect=dispatch_isolation.DispatchIsolationError(refusal))
    popen = Mock()
    monkeypatch.setattr(dispatch_isolation, "spawn_detached_worker", spawn)
    monkeypatch.setattr(subprocess, "Popen", popen)
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    spawn.assert_called_once()
    popen.assert_not_called()
    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"].startswith("dispatch_fallback_refused: ")
    assert refusal in state["error"]
    assert "ambiguous" not in state["error"]


def test_dispatch_popen_failure_records_worktree_head(tmp_path, monkeypatch) -> None:
    """Ported from tests/test_delegate.py::test_dispatch_popen_failure_records_worktree_head.

    v2 records the worktree head (``head_sha``) when the record is created; a failed spawn keeps it.
    """
    from scripts.dispatcher import admission
    from scripts.orchestration import dispatch_isolation

    spec, record, path = _spawn_refused_record(tmp_path, monkeypatch, "popen-head")
    record["head_sha"] = "a" * 40
    monkeypatch.setattr(
        dispatch_isolation, "spawn_detached_worker", Mock(side_effect=FileNotFoundError("no such file"))
    )
    with pytest.raises(admission.LaunchRefused):
        worker.start(spec, record, b"prompt", 60)

    state = json.loads(path.read_text())
    assert state["status"] == "failed"
    assert state["pid"] is None
    assert state["error"] == "worker_spawn_failed: Popen failed: FileNotFoundError: no such file"
    assert state["head_sha"] == "a" * 40


def _fake_pool(directory, *, current, file_cache, high=21 * 1024**3):
    """Ported from tests/test_dispatch_admission.py::_fake_pool."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "memory.current").write_text(f"{current}\n", encoding="ascii")
    (directory / "memory.high").write_text(f"{high}\n", encoding="ascii")
    (directory / "memory.max").write_text(f"{23 * 1024**3}\n", encoding="ascii")
    (directory / "memory.stat").write_text(f"active_file {file_cache}\ninactive_file 0\n", encoding="ascii")
    return directory


def _full_disk(monkeypatch, *readings):
    """Ported from tests/test_delegate_admission.py::_full_disk."""
    from scripts.orchestration import dispatch_admission

    seen = {"readings": list(readings), "reaper": [], "alerts": []}

    def probe():
        values = seen["readings"]
        used = values.pop(0) if len(values) > 1 else values[0]
        used_bytes = int(400 * 1024**3 * used / 100)
        return dispatch_admission.DiskProbe(used_bytes=used_bytes, free_bytes=400 * 1024**3 - used_bytes)

    def reaper(repo_root, _timeout_s=None):
        seen["reaper"].append(repo_root)
        return dispatch_admission.ReaperOutcome(ran=True, detail="reaper removed 0 worktree(s)")

    monkeypatch.setattr(dispatch_admission, "probe_disk", probe)
    monkeypatch.setattr(dispatch_admission, "run_disk_reaper", reaper)
    monkeypatch.setattr(dispatch_admission, "post_disk_alert", lambda body, _key: seen["alerts"].append(body))
    return seen


def _credit_balance_snapshot():
    """Inlined ports of test_credit_lane::_credit_balance_snapshot, _budget, _live and _codex."""
    from datetime import UTC, datetime

    codex = {
        "status": "near_cap", "remaining_pct": 1.0, "burn_pct_7d": 99.0,
        "freshness": "fresh", "age_s": 60.0, "eligible": True, "health": {"healthy": True},
        "credit_balance": 62500.0, "reset_credits": None,
        "runtime": {"headroom_blocked": False, "rate_limited": 0},
        "codexbar": {
            "weekly_used_pct": 99.0, "weekly_remaining_pct": 1.0,
            "weekly_resets_at": "2026-10-03T17:00:00+00:00", "will_last_to_reset": False,
            "pace_summary": "13% in deficit", "freshness": "fresh", "age_s": 60.0, "stale": False,
            "fetched_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        },
    }
    return {
        "agents": {"codex": codex}, "api_accounts": {}, "diagnostics": {"stale": False},
        "recommendation": {"primary_agent_for_code": "codex", "rationale": "", "warnings": []},
    }


# D5 ports of legacy admission contracts; originals remain untouched.
@pytest.fixture
def admission_dispatch(sandbox, monkeypatch):
    """Ported setup from test_delegate_admission::_stub_worktree and credit_lane::dispatch_env."""
    from scripts.dispatcher import cli

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(git, "ROOT", sandbox.repo)
    monkeypatch.setattr(git, "CONFIG", sandbox.repo / "scripts/config/fleet_repos.yaml")
    monkeypatch.setenv("PATH", sandbox.env["PATH"])
    spawned = []

    def start(spec, record, prompt, hard_timeout):
        store.create(record, prompt)
        record.update(pid=os.getpid(), process_start=worker._identity(os.getpid()))
        store.replace(record)
        spawned.append(record)

    monkeypatch.setattr(worker, "start", start)

    def dispatch(*flags, model="gpt-6.1-sol", mode="workspace-write", task_id="adm-worker"):
        if mode == "workspace-write" and "--owned-path" not in flags:
            flags = (*flags, "--owned-path", "docs/review.md")
        return cli.main(["dispatch", "--agent", "sol", "--model", model, "--mode", mode,
                         "--task-id", task_id, "--prompt", "Map the parser flags.", *flags])

    yield SimpleNamespace(dispatch=dispatch, box=sandbox, spawned=spawned)
    # The fake supervisor is this test process; release its records before sandbox cancellation.
    for path in sandbox.tasks.glob("*.json"):
        record = json.loads(path.read_text())
        if record.get("pid") == os.getpid():
            record["status"] = "done"
            store.replace(record, path)


def test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_refuses_a_write_worker_at_the_cap_with_one_line."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--dry-run") == 3
    refusal = [line for line in capsys.readouterr().err.splitlines() if "admission" in line]
    assert refusal == [
        "❌ dispatch admission refused for a workspace-write worker: live write workers 0/0 reached the cap "
        "(DISPATCH_MAX_LIVE_WRITE_WORKERS=0). Wait for a worker to finish or for the host to recover, raise the "
        'threshold through the named environment variable, or pass --force-admission "<reason>" to override.'
    ]
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_read_only_dispatch_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_is_exempt."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err
    assert "admission" not in store.read("adm-worker")


def test_full_shared_pool_refuses_a_write_worker(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_full_shared_pool_refuses_a_write_worker."""

    pool = _fake_pool(tmp_path / "lu.slice", current=21 * 1024**3, file_cache=1024**3 // 2)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 3
    assert ("lu.slice non-cache use 20.5 GiB plus a 2.5 GiB worker reserve exceeds MemoryHigh 21.0 GiB "
            "(DISPATCH_WORKER_MEM_RESERVE_GIB=2.5)") in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_file_cache_does_not_count_against_the_pool(admission_dispatch, tmp_path, monkeypatch, capsys):
    """Ported from tests/test_dispatch_admission.py::test_file_cache_does_not_count_against_the_pool."""

    pool = _fake_pool(tmp_path / "lu.slice", current=28 * 1024**3, file_cache=14 * 1024**3)
    monkeypatch.setenv("LU_SLICE_CGROUP", str(pool))
    assert admission_dispatch.dispatch() == 0
    assert "lu.slice 14.0/21.0 GiB non-cache (+14.0 GiB file cache; worker reserve 2.5 GiB)" in capsys.readouterr().err
    record = store.read("adm-worker")
    assert record["admission"]["pool_nonreclaimable_gib"] == 14.0
    assert record["admission"]["pool_file_cache_gib"] == 14.0
    assert record["admission"]["pool_limit_gib"] == 21.0


def test_locked_recheck_refuses_a_dispatch_that_lost_the_race(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_refuses_a_dispatch_that_lost_the_race."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission

    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "1")
    real_evaluate = admission.evaluate
    calls = []

    def evaluate_after_competitor(mode, **kwargs):
        calls.append(kwargs)
        if len(calls) == 2:
            record = dict(schema_version=2, task_id="competitor", status="running", mode="workspace-write",
                          pid=os.getpid(), process_start=worker._identity(os.getpid()))
            store.replace(record)
        return real_evaluate(mode, **kwargs)

    monkeypatch.setattr(admission, "evaluate", evaluate_after_competitor)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch() == 3
    assert len(calls) == 2
    assert "live write workers 1/1 reached the cap" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids == ("competitor",)


def test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created(admission_dispatch, monkeypatch):
    """Ported from tests/test_delegate_admission.py::test_admitted_dispatch_holds_its_slot_while_the_worktree_is_created."""
    from scripts.guardrails.delegate_ownership import _task_still_active
    from scripts.orchestration import dispatch_admission

    seen = {}
    create = git.create_worktree

    def create_worktree(*args, **kwargs):
        held = store.read("adm-worker")
        seen["record"] = held
        seen["live"] = dispatch_admission.scan_task_records(admission_dispatch.box.tasks).live_task_ids
        assert _task_still_active("adm-worker", os.getpid(), admission_dispatch.box.tasks, created_at=0)
        assert [state["task_id"] for _, state in dispatch_admission.iter_active_records(
            admission_dispatch.box.tasks)] == ["adm-worker"]
        return create(*args, **kwargs)

    monkeypatch.setattr(git, "create_worktree", create_worktree)
    assert admission_dispatch.dispatch() == 0
    held = seen["record"]
    assert held["status"] == "spawning" and held["pid"] is None and held["mode"] == "workspace-write"
    assert held[dispatch_admission.ADMISSION_HOLD_KEY]["owner_pid"] == os.getpid()
    assert seen["live"] == ("adm-worker",)
    final = store.read("adm-worker")
    assert dispatch_admission.ADMISSION_HOLD_KEY not in final
    assert final["run_nonce"] == held["run_nonce"]
    assert final["admission"] == held["admission"]


def test_dispatch_that_stops_after_admission_drops_its_hold(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_dispatch_that_stops_after_admission_drops_its_hold."""
    def disappear(*_args, **_kwargs):
        assert store.read("adm-worker")["admission_hold"]
        raise ValueError("worktree disappeared before its task record was published")

    monkeypatch.setattr(git, "create_worktree", disappear)
    assert admission_dispatch.dispatch() == 2
    assert "disappeared before its task record was published" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_admission_marks_a_record_whose_dispatcher_died_crashed(admission_dispatch):
    """Ported from tests/test_delegate_admission.py::test_admission_marks_a_record_whose_dispatcher_died_crashed."""
    from scripts.dispatcher import host_admission as admission
    from scripts.orchestration import dispatch_admission
    from tests.worktree_prep_helpers import exited_process_identity

    pid, start = exited_process_identity()
    record = dict(schema_version=2, task_id="orphan", run_nonce="nonce-orphan", status="spawning", pid=None,
                  mode="workspace-write", started_at=store.now(),
                  admission_hold=dict(run_nonce="nonce-orphan", owner_pid=pid, owner_start=start))
    admission_dispatch.box.tasks.mkdir(exist_ok=True)
    store.replace(record)
    decision = admission.evaluate("workspace-write", sweep=True)
    assert decision.live_task_ids == ()
    assert decision.dead_task_ids == ("orphan",)
    healed = store.read("orphan")
    assert healed["status"] == "crashed"
    assert healed["returncode_reason"] == dispatch_admission.ORPHANED_HOLD_REASON
    assert "marked crashed by admission probe" in healed["stderr_excerpt"]
    assert "admission_hold" not in healed


@pytest.mark.parametrize("model", ["gpt-6-astra", "gpt-5-codex", "claude-opus-5-5"])
def test_admission_refuses_off_allowlist_model_on_credit_balance_lane(admission_dispatch, monkeypatch, capsys, model):
    """Ported from tests/test_credit_lane.py::test_admission_refuses_off_allowlist_model_on_credit_balance_lane."""
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", _credit_balance_snapshot)
    assert admission_dispatch.dispatch(model=model, mode="read-only") == 2
    err = capsys.readouterr().err
    assert "❌ dispatch refused: CREDIT_PERIOD_MODEL_REFUSED: lane codex is credit_balance_present" in err
    assert f"model {model} is outside the credit-period allowlist [gpt-6.1-sol, gpt-6-luna]" in err
    assert "credit_lanes.yaml" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.repo / ".worktrees").exists()
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "gpt-6-luna", "codex:gpt-6-luna", "GPT-6.1-Sol", None])
def test_admission_accepts_allowlisted_and_default_models_without_reading_state(monkeypatch, model):
    """Ported from tests/test_credit_lane.py::test_admission_accepts_allowlisted_and_default_models_without_reading_state."""
    from scripts.dispatcher import host_admission as admission
    from scripts.fleet import credit_lane

    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda **_k: pytest.fail("must not read state"))
    assert admission.credit_period_refusal("codex", model) is None


def test_force_admission_records_the_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_records_the_reason."""
    monkeypatch.setenv("DISPATCH_MAX_LIVE_WRITE_WORKERS", "0")
    assert admission_dispatch.dispatch("--force-admission", "hotfix #1234 while one worker drains") == 0
    assert "overridden by --force-admission ('hotfix #1234 while one worker drains')" in capsys.readouterr().err
    decision = store.read("adm-worker")["admission"]
    assert decision["admitted"] is False
    assert decision["forced"] is True
    assert decision["force_reason"] == "hotfix #1234 while one worker drains"
    assert decision["max_live_write_workers"] == 0


def test_force_admission_requires_a_reason(admission_dispatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_requires_a_reason."""
    assert admission_dispatch.dispatch("--force-admission", "   ") == 2
    assert "--force-admission requires a non-empty reason" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_live_forced_dispatch_on_a_full_disk_stops_at_the_first_gate."""

    disk = _full_disk(monkeypatch, 90.0)
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    assert len(disk["reaper"]) == 1
    assert "--force-admission cannot override a full disk" in capsys.readouterr().err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()
    assert not (admission_dispatch.box.repo / ".worktrees").exists()


def test_locked_recheck_holds_a_disk_refusal_against_a_force_reason(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_locked_recheck_holds_a_disk_refusal_against_a_force_reason."""

    disk = _full_disk(monkeypatch, 60.0, 90.0)
    monkeypatch.setattr(git, "create_worktree", lambda *_a, **_k: pytest.fail("must not create a worktree"))
    assert admission_dispatch.dispatch("--force-admission", "hotfix while the disk drains") == 4
    assert disk["reaper"] == []
    err = capsys.readouterr().err
    assert "disk 90.0% used" in err and "--force-admission cannot override a full disk" in err
    assert not admission_dispatch.spawned
    assert not (admission_dispatch.box.tasks / "adm-worker.json").exists()


def test_force_admission_skips_the_early_refusal(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_force_admission_skips_the_early_refusal."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch("--force-admission", "drain one worker") == 0
    assert "overridden by --force-admission ('drain one worker'): MemAvailable 1.0 GiB" in capsys.readouterr().err
    assert store.read("adm-worker")["admission"]["forced"] is True


def test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_early_refusal_reports_an_invalid_threshold_as_an_invalid_request."""
    monkeypatch.setenv("DISPATCH_MIN_MEM_AVAILABLE_GIB", "-1")
    assert admission_dispatch.dispatch() == 2
    assert "invalid dispatch admission threshold: DISPATCH_MIN_MEM_AVAILABLE_GIB='-1' must be zero or more" in capsys.readouterr().err
    assert not admission_dispatch.spawned


def test_read_only_dispatch_on_an_overloaded_host_is_exempt(admission_dispatch, monkeypatch, capsys):
    """Ported from tests/test_delegate_admission.py::test_read_only_dispatch_on_an_overloaded_host_is_exempt."""
    from scripts.orchestration import dispatch_admission

    overloaded = dispatch_admission.HostProbe(mem_available_bytes=1024**3, load1=40.0, cpu_count=8, proc_available=True)
    monkeypatch.setattr(dispatch_admission, "probe_host", lambda: overloaded)
    assert admission_dispatch.dispatch(mode="read-only") == 0
    assert "admission" not in capsys.readouterr().err
