"""Real local-remote pushes exercise both dispatch boundaries (#10033)."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci import push_gate as gate
from scripts.ci.push_shadow import selection


def git(root: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run([shutil.which("git"), *args], cwd=root, env=env, capture_output=True,
                          text=True, check=True, timeout=30).stdout.strip()


@pytest.fixture
def repository(tmp_path, monkeypatch):
    # The production dispatch env has extra Git config and Python plugins;
    # nested probes must not inherit a different repository identity.
    for key in list(os.environ):
        if key.startswith("GIT_") or key in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}:
            monkeypatch.delenv(key, raising=False)
    # System Git only; commit prose must not resolve to installed agent aliases
    # through the nested-execution tripwire.
    monkeypatch.setenv("PATH", os.defpath)
    remote = tmp_path / "remote.git"
    root = tmp_path / ".worktrees/dispatch/codex/packet"
    root.mkdir(parents=True)
    git(tmp_path, "init", "--bare", str(remote))
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "core.hooksPath", str(tmp_path / "empty-hooks"))
    git(root, "remote", "add", "origin", str(remote))
    (root / "tests").mkdir()
    (root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    (root / "scripts/ci").mkdir(parents=True)
    (root / gate.REGISTRY).write_text(json.dumps({"schema_version": 1, "modules": ["tests/test_invariant.py"],
                                                "node_ids": ["tests/test_invariant.py::test_invariant"]}))
    (root / "tests/test_invariant.py").write_text("def test_invariant():\n    assert True\n")
    (root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n      - id: committed-test\n"
        "        name: committed test\n        entry: git diff --exit-code\n"
        "        language: system\n        pass_filenames: false\n        stages: [pre-push]\n"
    )
    git(root, "add", ".")
    git(root, "commit", "-m", "initial")
    git(root, "push", "origin", "main")
    git(root, "switch", "-c", "codex/packet")
    (root / "tests/test_changed.py").write_text("def test_changed():\n    assert True\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "change")
    ctx = gate.context(root, interpreter=sys.executable)
    return ctx, remote


def test_dedup_registry_and_changed_tests(repository):
    ctx, _ = repository
    targets, digest = gate.invariant_targets(ctx.root, ["tests/test_changed.py", "tests/test_invariant.py"])
    assert targets == ["tests/test_changed.py", "tests/test_invariant.py"]
    assert len(digest) == 64


@pytest.mark.parametrize("path", ["worker", "auto_finalize"])
@pytest.mark.parametrize("green", [True, False])
def test_exact_outgoing_push_paths(repository, monkeypatch, path, green):
    ctx, remote = repository
    if not green:
        (ctx.root / "tests/test_changed.py").write_text("def test_changed():\n    assert False\n")
        git(ctx.root, "add", ".")
        git(ctx.root, "commit", "-m", "red")
    head = git(ctx.root, "rev-parse", "HEAD")
    if path == "worker":
        env = gate.install(ctx.root, dict(os.environ), interpreter=sys.executable)
        result = subprocess.run(["git", "push", "--no-verify", "-u", "origin", "HEAD"], cwd=ctx.root,
                                env=env, text=True, capture_output=True, timeout=45)
        assert (result.returncode == 0) is green, result.stderr
        if not green:
            assert '"reason": "validation_failed"' in result.stderr
            assert "tests/test_changed.py::test_changed" in result.stderr
    else:
        from scripts import delegate

        # This is the production auto-finalize function, with only its interpreter pinned to the test's.
        original = gate.context
        monkeypatch.setattr(gate, "context", lambda root, **kw: original(root, interpreter=sys.executable))
        if green:
            delegate._push_auto_finalize_branch(ctx.root, "codex/packet")
        else:
            with pytest.raises(delegate._TypedFailure) as failure:
                delegate._push_auto_finalize_branch(ctx.root, "codex/packet")
            assert failure.value.cause.code == "validation_failed"
    receipt = json.loads((ctx.state / "receipt.json").read_text())
    assert receipt["head"] == head
    assert receipt["status"] == ("passed" if green else "validation_failed")
    assert receipt["selected_tests"] == ["tests/test_changed.py", "tests/test_invariant.py"]
    assert receipt["shadow"]["status"] == "unavailable"  # fixture has no shadow module; never blocks
    assert git(ctx.root, "rev-parse", "HEAD") == head  # refusals preserve branch
    published = git(ctx.root, "ls-remote", str(remote), "refs/heads/codex/packet")
    assert (published.startswith(head)) is green
    if not green:
        assert receipt["failing_node_ids"] == ["tests/test_changed.py::test_changed"]
    else:
        assert git(ctx.root, "rev-parse", "--abbrev-ref", "@{upstream}") == "origin/codex/packet"


@pytest.mark.parametrize("mutation", ["dirty", "commit", "registry", "range"])
def test_stale_receipt_rejected(repository, mutation):
    ctx, _ = repository
    base, head = git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD")
    receipt = gate.validate(ctx, base, head)
    assert gate.receipt_current(ctx, receipt, base, head)
    if mutation == "range":
        base = head
    elif mutation == "registry":
        (ctx.root / gate.REGISTRY).write_text("{}")
    else:
        (ctx.root / "tests/test_changed.py").write_text("def test_changed():\n    assert False\n")
        if mutation == "commit":
            git(ctx.root, "add", ".")
            git(ctx.root, "commit", "-m", "changed again")
    assert not gate.receipt_current(ctx, receipt, base, head)


def test_budget_exhaustion_kills_children_and_preserves_commit(repository):
    ctx, _ = repository
    pid_file = ctx.state / "child.pid"
    ctx.state.mkdir(parents=True)
    test = ctx.root / "tests/test_changed.py"
    test.write_text(
        "import subprocess, sys, time\n"
        "def test_changed():\n"
        "    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        f"    open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
        "    time.sleep(60)\n"
    )
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "slow")
    head = git(ctx.root, "rev-parse", "HEAD")
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), head, budget=8)
    assert failure.value.reason == "validation_incomplete"
    receipt = json.loads((ctx.state / "receipt.json").read_text())
    assert receipt["status"] == "validation_incomplete"
    assert receipt["execution_seconds"] < 11
    assert git(ctx.root, "rev-parse", "HEAD") == head
    assert pid_file.exists(), "prove timeout reached the running test and its child"
    pid = int(pid_file.read_text())
    stat = Path(f"/proc/{pid}/stat")
    assert not stat.exists() or stat.read_text().split()[2] == "Z"


def test_admission_busy_is_incomplete_without_running_checks(repository, monkeypatch):
    ctx, _ = repository
    calls = []
    original = gate.run

    def record(ctx, command, *args, **kwargs):
        calls.append(command)
        return original(ctx, command, *args, **kwargs)

    monkeypatch.setattr(gate, "run", record)
    with ctx.lock.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with pytest.raises(gate.GateFailure) as failure:
            gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert failure.value.receipt["detail"] == "admission_busy"
    assert all("scripts.ci.push_shadow" in command for command in calls)


def test_precommit_receives_committed_range_and_cannot_be_skipped(repository, monkeypatch):
    ctx, _ = repository
    marker = ctx.state / "hook.txt"
    ctx.state.mkdir(parents=True)
    (ctx.root / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: local\n    hooks:\n      - id: refuse\n        name: refuse\n"
        f"        entry: {sys.executable} -c \"import os,pathlib,sys; "
        f"pathlib.Path('{marker}').write_text(os.environ['PRE_COMMIT_FROM_REF'] + ' ' + "
        "os.environ['PRE_COMMIT_TO_REF']); sys.exit(1)\"\n"
        "        language: system\n        pass_filenames: false\n        stages: [pre-push]\n"
    )
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "hook red")
    monkeypatch.setenv("SKIP", "refuse")
    with pytest.raises(gate.GateFailure) as failure:
        gate.push(ctx, "codex/packet")
    assert failure.value.receipt["detail"] == "pre_push_failed"
    assert marker.read_text().split() == [git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD")]


def test_shadow_closure_transitive_and_unresolved_fallback(repository):
    ctx, _ = repository
    (ctx.root / "scripts/producer.py").write_text("VALUE = 1\n")
    (ctx.root / "scripts/consumer.py").write_text("from scripts.producer import VALUE\n")
    (ctx.root / "tests/test_changed.py").write_text("from scripts.consumer import VALUE\n")
    git(ctx.root, "add", ".")
    report = selection(ctx.root, ["scripts/producer.py"])
    assert report["closure_tests"] == ["tests/test_changed.py"]
    assert not report["full_fallback"]
    (ctx.root / "scripts/consumer.py").write_text("import importlib\nimportlib.import_module(name)\n")
    report = selection(ctx.root, ["scripts/producer.py"])
    assert report["unresolved_dependencies"]
    assert report["full_fallback"]
    assert report["selected_tests"] == ["tests/test_changed.py", "tests/test_invariant.py"]


def test_merge_needs_driver_evidence_and_is_recorded(repository):
    ctx, _ = repository
    git(ctx.root, "switch", "-c", "side", "origin/main")
    (ctx.root / "side.txt").write_text("side\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "side")
    git(ctx.root, "switch", "codex/packet")
    git(ctx.root, "merge", "--no-ff", "side", "-m", "merge")
    head, base = git(ctx.root, "rev-parse", "HEAD"), git(ctx.root, "rev-parse", "origin/main")
    with pytest.raises(gate.GateFailure):
        gate.validate(ctx, base, head)
    (ctx.state / "merge-reasons.json").write_text(json.dumps({head: {
        "reason": "driver_order", "evidence": "fixture-driver-disposition",
    }}))
    receipt = gate.validate(ctx, base, head)
    assert receipt["merge_records"][0]["merge_sha"] == head


@pytest.mark.parametrize("arguments", [
    ["push", "--all"], ["push", "origin", "HEAD:main"], ["-c", "alias.ship=push", "push"],
])
def test_unsupported_push_is_refused(repository, arguments):
    ctx, remote = repository
    assert gate.wrapper_main(ctx, arguments) == 1
    assert git(ctx.root, "ls-remote", str(remote), "refs/heads/codex/packet") == ""


@pytest.mark.parametrize("green", [True, False])
def test_launcher_git_shim_chain_keeps_gate_and_push_scanner(repository, green):
    from scripts.agent_runtime.runner import _apply_merge_guard

    ctx, remote = repository
    if not green:
        (ctx.root / "tests/test_changed.py").write_text("def test_changed():\n    assert False\n")
        git(ctx.root, "add", ".")
        git(ctx.root, "commit", "-m", "red")
    env = gate.install(ctx.root, dict(os.environ), interpreter=sys.executable)
    env = _apply_merge_guard(mode="danger", env=env)
    result = subprocess.run(["git", "-C", str(ctx.root), "push", "-u", "origin", "HEAD"],
                            cwd=ctx.root, env=env, text=True, capture_output=True, timeout=45)
    assert (result.returncode == 0) is green, result.stderr
    if not green:
        assert "validation_failed" in result.stderr
    else:
        assert git(ctx.root, "ls-remote", str(remote), "refs/heads/codex/packet").startswith(git(ctx.root, "rev-parse", "HEAD"))


def test_gate_preserves_auto_finalize_commit_on_refusal(repository, monkeypatch):
    from scripts import delegate

    ctx, _ = repository
    (ctx.root / "artifact.txt").write_text("owned\n")
    tasks = ctx.root.parent / "task-state"
    tasks.mkdir()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    causes = []
    original_publish = delegate._publish_cause

    def record_cause(task_id, cause, **kwargs):
        causes.append(cause)
        return original_publish(task_id, cause, **kwargs)

    monkeypatch.setattr(delegate, "_publish_cause", record_cause)

    def refusal(*_args):
        raise delegate._TypedFailure("validation_incomplete", delegate._TypedCause("validation_incomplete"))

    monkeypatch.setattr(delegate, "_push_auto_finalize_branch", refusal)
    before = git(ctx.root, "rev-parse", "HEAD")
    result = delegate._auto_finalize_dirty_worktree(
        worktree=ctx.root, task_id="fixture", agent="claude", branch="codex/packet", base_branch="main",
        owned_paths=["artifact.txt"],
    )
    assert not result.ok
    assert result.error == "validation_incomplete", [cause.diagnostic for cause in causes]
    assert result.commit_sha == git(ctx.root, "rev-parse", "HEAD") != before
    assert not git(ctx.root, "status", "--porcelain")


@pytest.mark.parametrize("arguments", [["push", "origin", "HEAD"], ["-C", "ROOT", "push", "origin", "HEAD"],
                                      ["-c", "core.hooksPath=unused", "push", "origin", "HEAD"]])
def test_wrapper_dispatches_supported_forms(repository, monkeypatch, arguments):
    ctx, _ = repository
    monkeypatch.chdir(ctx.root)
    arguments = [str(ctx.root) if arg == "ROOT" else arg for arg in arguments]
    assert gate.wrapper_main(ctx, arguments) == 0


def test_wrapper_does_not_redirect_another_repository(repository, tmp_path, monkeypatch):
    ctx, _ = repository
    monkeypatch.chdir(tmp_path)
    assert gate.wrapper_main(ctx, ["push", "origin", "HEAD"]) == 1


def test_inherited_git_directory_cannot_substitute_tree(repository, monkeypatch):
    ctx, _ = repository
    monkeypatch.setenv("GIT_DIR", str(ctx.root / "absent.git"))
    assert gate.git(ctx, "rev-parse", "HEAD") == git(ctx.root, "rev-parse", "HEAD", env=gate.git_env())


def test_shadow_success_is_recorded_and_never_selects_blocking_tests(repository, monkeypatch):
    ctx, _ = repository
    original = gate.run
    shadow = {"mode": "shadow", "status": "recorded", "selected_tests": ["tests/test_missing.py"],
              "unresolved_dependencies": [{"reason": "dynamic-import"}], "full_fallback": True}

    def runner(context, command, *args, **kwargs):
        if "scripts.ci.push_shadow" in command:
            return 0, json.dumps(shadow)
        return original(context, command, *args, **kwargs)

    monkeypatch.setattr(gate, "run", runner)
    receipt = gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert receipt["status"] == "passed"
    assert receipt["shadow"] == shadow
    assert "tests/test_missing.py" not in receipt["selected_tests"]


def test_green_receipt_is_rejected_when_checks_mutate_tree(repository, monkeypatch):
    ctx, _ = repository
    original = gate.run

    def runner(context, command, *args, **kwargs):
        result = original(context, command, *args, **kwargs)
        if "pytest" in command:
            (context.root / "tests/test_changed.py").write_text("def test_changed():\n    assert False\n")
        return result

    monkeypatch.setattr(gate, "run", runner)
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert failure.value.receipt["status"] == "validation_incomplete"
    assert failure.value.receipt["detail"] == "stale_receipt"


def test_unknown_registry_version_is_incomplete(repository):
    ctx, _ = repository
    path = ctx.root / gate.REGISTRY
    data = json.loads(path.read_text())
    data["schema_version"] = 2
    path.write_text(json.dumps(data))
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "unknown registry")
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert failure.value.reason == "validation_incomplete"


def test_merge_conflict_reason_requires_actual_conflict(repository):
    ctx, _ = repository
    git(ctx.root, "switch", "main")
    (ctx.root / "base.txt").write_text("advance\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "advance")
    git(ctx.root, "push", "origin", "main")
    main = git(ctx.root, "rev-parse", "HEAD")
    git(ctx.root, "switch", "codex/packet")
    git(ctx.root, "merge", "--no-ff", main, "-m", "clean merge")
    head = git(ctx.root, "rev-parse", "HEAD")
    ctx.state.mkdir(parents=True)
    (ctx.state / "merge-reasons.json").write_text(json.dumps({head: {"reason": "conflict", "base": main}}))
    with pytest.raises(ValueError, match="clean or unknown"):
        gate.merge_records(ctx, git(ctx.root, "rev-parse", "HEAD~1"), head)


def test_merge_conflict_reason_accepts_fresh_conflict_evidence(repository):
    ctx, _ = repository
    original_base = git(ctx.root, "rev-parse", "origin/main")
    path = ctx.root / "tests/test_invariant.py"
    path.write_text("def test_invariant():\n    assert 1 == 1\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "head edit")
    branch_head = git(ctx.root, "rev-parse", "HEAD")
    git(ctx.root, "switch", "main")
    path.write_text("def test_invariant():\n    assert 2 == 2\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "base edit")
    main = git(ctx.root, "rev-parse", "HEAD")
    git(ctx.root, "push", "origin", "main")
    git(ctx.root, "switch", "codex/packet")
    with pytest.raises(subprocess.CalledProcessError):
        git(ctx.root, "merge", main)
    path.write_text("def test_invariant():\n    assert True\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "resolve conflict")
    head = git(ctx.root, "rev-parse", "HEAD")
    ctx.state.mkdir(parents=True)
    records = {head: {"reason": "conflict", "base": main}}
    (ctx.state / "merge-reasons.json").write_text(json.dumps(records))
    evidence = gate.merge_records(ctx, original_base, head)
    assert evidence[0]["head"] == branch_head
    assert evidence[0]["base"] == main
    assert evidence[0]["merge_tree_exit"] == 1
    records[head]["base"] = original_base
    (ctx.state / "merge-reasons.json").write_text(json.dumps(records))
    with pytest.raises(ValueError, match="stale"):
        gate.merge_records(ctx, original_base, head)


def test_deadline_before_first_check_stays_incomplete(repository):
    ctx, _ = repository
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"), budget=0)
    assert failure.value.receipt["status"] == "validation_incomplete"


def test_nonpush_commands_delegate_to_real_git(repository, monkeypatch):
    ctx, _ = repository
    calls = []
    # A real exec never returns. Model that boundary explicitly.
    def transfer(executable, arguments):
        calls.append((executable, arguments))
        raise SystemExit(0)

    monkeypatch.setattr(gate.os, "execv", transfer)
    with pytest.raises(SystemExit):
        gate.wrapper_main(ctx, ["status", "--porcelain"])
    assert calls == [(ctx.git, [ctx.git, "status", "--porcelain"])]


@pytest.mark.parametrize("stage", ["pre_commit", "pytest"])
def test_runner_internal_error_is_incomplete(repository, monkeypatch, stage):
    ctx, _ = repository
    original = gate.run

    def runner(context, command, *args, **kwargs):
        if stage in command:
            return 3, "runner internal error"
        return original(context, command, *args, **kwargs)

    monkeypatch.setattr(gate, "run", runner)
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert failure.value.receipt["status"] == "validation_incomplete"


def test_push_transport_has_network_timeout_and_runs_once(repository, monkeypatch):
    ctx, _ = repository
    original = subprocess.run
    attempts = []

    def timed_transport(command, *args, **kwargs):
        if "push" in command:
            attempts.append(kwargs["timeout"])
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return original(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", timed_transport)
    with pytest.raises(subprocess.TimeoutExpired):
        gate.push(ctx, "codex/packet")
    assert attempts == [gate.NETWORK_SECONDS]


def test_collection_error_keeps_actual_file_node_id(repository):
    ctx, _ = repository
    (ctx.root / "tests/test_changed.py").write_text("def broken(\n")
    git(ctx.root, "add", ".")
    git(ctx.root, "commit", "-m", "syntax error")
    with pytest.raises(gate.GateFailure) as failure:
        gate.validate(ctx, git(ctx.root, "rev-parse", "origin/main"), git(ctx.root, "rev-parse", "HEAD"))
    assert failure.value.reason == "validation_failed"
    assert failure.value.receipt["failing_node_ids"] == ["tests/test_changed.py"]


def test_worker_launch_installs_gate_with_pinned_interpreter(repository, monkeypatch):
    from scripts import delegate

    ctx, _ = repository
    monkeypatch.setattr(delegate, "_inject_gh_token_for_agent", lambda *_args: None)
    env = delegate._build_worker_env(task_id="fixture", dispatch_agent="codex", worktree_path=ctx.root)
    assert Path(env["PATH"].split(os.pathsep)[0]) == ctx.state / "bin"
    config = json.loads((ctx.state / "context.json").read_text())
    assert config["python"] == str(delegate._REPO_ROOT / ".venv/bin/python")
    assert config["git"] == ctx.git
    again = gate.install(ctx.root, env, interpreter=sys.executable)
    assert Path(again["PATH"].split(os.pathsep)[0]) == ctx.state / "bin"


def test_merge_rule_in_worker_preamble():
    from scripts import delegate

    prompt = delegate._augment_prompt_with_worktree("brief", Path("/repo/.worktrees/dispatch/codex/packet"), mode="danger")
    assert "base/head/combined-tree evidence" in prompt
    assert "merge-reasons.json" in prompt
    assert "merge-group CI proves semantic combinations" in prompt
