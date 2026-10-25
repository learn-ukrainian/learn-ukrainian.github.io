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

import pytest
import yaml

from scripts.dispatcher import checks, git, store, worker
from scripts.dispatcher.cli import ALIASES, build_parser
from scripts.dispatcher.environment import child_env
from scripts.dispatcher.types import TaskSpec

SOURCE = Path(__file__).resolve().parents[2]


def run_git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True, timeout=30
    ).stdout.strip()


@pytest.fixture
def sandbox(tmp_path):
    repo, tasks = tmp_path / "public", tmp_path / "tasks"
    repo.mkdir()
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "stub@example.invalid")
    run_git(repo, "config", "user.name", "Stub")
    for relative in ("scripts/dispatcher", "scripts/common"):
        shutil.copytree(SOURCE / relative, repo / relative, ignore=shutil.ignore_patterns("__pycache__"))
    # Disposable repositories share the test interpreter; they own no project environment.
    resolver = repo / "scripts/common/repo_root.py"
    with resolver.open("a") as stream:
        stream.write(f"\n\ndef project_interpreter(root=None):\n    return Path({sys.executable!r})\n")
    shutil.copy(SOURCE / "scripts/dispatch.py", repo / "scripts/dispatch.py")
    (repo / "scripts/__init__.py").touch()
    config = repo / "scripts/config"
    config.mkdir()
    (config / "fleet_repos.yaml").write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {
                        "default": True,
                        "local_name": "public",
                        "github": "example/public",
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
    remote = tmp_path / "remote.git"
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

    box = SimpleNamespace(repo=repo, tasks=tasks, remote=remote, cli=cli, dispatch=dispatch, settle=settle)
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
    assert record["started_at"] <= record["finished_at"]
    assert record["duration_s"] > 0
    assert record["usage"] == {"tokens": 7}
    assert record["result_sha256"] == hashlib.sha256(b"literal final response").hexdigest()
    assert (sandbox.tasks / "logs" / f"{task[0]}.stderr.log").read_text() == "stub stderr\n"
    assert (sandbox.tasks / f"{task[0]}.json").stat().st_mode & 0o777 == 0o600
    assert Path(record["prompt_file"]).stat().st_mode & 0o777 == 0o600


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
    record = sandbox.settle(sandbox.dispatch(model, "--mode", "workspace-write"))
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
        observed = git.snapshot_delivery(probe, record["worktree_base_sha"], record["worktree_branch"])
        assert observed["push_state"] == "unpushed"
        run_git(probe.worktree, "remote", "set-url", "origin", str(sandbox.tasks / "missing-remote"))
        assert (
            git.snapshot_delivery(probe, record["worktree_base_sha"], record["worktree_branch"])["push_state"]
            == "unknown"
        )


def test_review_uses_exact_commit_on_fresh_branch_and_cwd_reuses(sandbox):
    task = sandbox.dispatch("unpushed", "--mode", "workspace-write")
    first = sandbox.settle(task)
    result = sandbox.cli(
        "dispatch",
        "--agent",
        "sol",
        "--model",
        "echo",
        "--prompt",
        "review",
        "--branch",
        first["worktree_branch"],
        "--pinned-head",
        first["head_sha"],
    )
    review = sandbox.settle(result.stdout.splitlines())
    assert review["worktree_base_sha"] == first["head_sha"]
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


def test_dry_run_and_invalid_flags_create_nothing(sandbox):
    before = run_git(sandbox.repo, "branch", "--list")
    result = sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "preview", "--dry-run")
    plan = json.loads(result.stdout)
    assert plan["argv"][2] == "echo"
    assert not Path(plan["worktree"]).exists()
    assert not sandbox.tasks.exists()
    assert run_git(sandbox.repo, "branch", "--list") == before
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--force-new", expected=2)
    sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--prompt", "x", "--prompt-file", "y", expected=2)


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


@pytest.mark.parametrize("agent", ["muse", "opencode", "hermes"])
def test_private_repo_and_symlink_paths_are_refused(spec, tmp_path, monkeypatch, agent):
    config = tmp_path / "repos.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "repos": {
                    "public": {"default": True, "local_name": "public", "role": "public-monorepo"},
                    "private": {"local_name": "private", "role": "private-product"},
                }
            }
        )
    )
    monkeypatch.setattr(git, "CONFIG", config)
    monkeypatch.setattr(git, "ROOT", tmp_path / "public")
    private = tmp_path / "private"
    private.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(private, target_is_directory=True)
    spec = dataclasses.replace(spec, agent=agent)
    with pytest.raises(ValueError, match="private input"):
        checks.check_private_input(spec, "private")
    for reference in (
        str(private / "secret.txt"),
        "./alias/secret.txt",
        "'alias/a file.txt'",
        "--input=alias/secret.txt",
    ):
        spec.prompt_file.write_text(f"Read {reference}.")
        with pytest.raises(ValueError, match="private path"):
            checks.check_private_input(spec, "public")
    checks.check_private_input(dataclasses.replace(spec, agent="codex"), "private")


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
