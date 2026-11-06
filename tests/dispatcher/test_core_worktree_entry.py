"""Dispatch start-up: supervisor cleanup, sparse checkout, linked-worktree entry."""

import contextlib
import json
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.dispatcher import agy_sandbox, git, store, worker
from scripts.dispatcher.types import TaskSpec
from tests.dispatcher.conftest import await_file, prior_worktree, run_git


def test_supervise_restores_signal_handlers_after_cleanup(sandbox, monkeypatch):
    """Defect class: leaked signal disposition after in-process supervision."""
    from tests.dispatcher import stub_provider

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker.providers, "load", lambda _agent: stub_provider)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    spec = TaskSpec("signal-cleanup", "codex", "echo", None, "read-only", sandbox.repo,
                    sandbox.repo / "signal-cleanup.prompt", sandbox.tasks / "signal-cleanup.result")
    spec.prompt_file.write_bytes(b"literal final response")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main",
                              run_git(sandbox.repo, "rev-parse", "HEAD"), {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "signal-cleanup.prompt")
    path = store.create(record, b"literal final response")
    (sandbox.tasks / "logs").mkdir()
    original_term, original_int = signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)

    def previous_term(_signum, _frame):
        pass

    try:
        signal.signal(signal.SIGTERM, previous_term)
        worker.supervise(path, {}, 10)
        assert json.loads(path.read_text())["status"] == "done"
        assert signal.getsignal(signal.SIGTERM) is previous_term
        assert signal.getsignal(signal.SIGINT) is original_int
    finally:
        signal.signal(signal.SIGTERM, original_term)
        signal.signal(signal.SIGINT, original_int)


def test_cancel_during_a_callee_that_absorbs_exceptions_still_cancels_before_launch(sandbox, monkeypatch):
    """#11994: the handler raised at an arbitrary bytecode, so a callee's broad handler absorbed the cancel."""
    from tests.dispatcher import stub_provider

    def absorbing_check(*_args, **_kwargs):
        with contextlib.suppress(Exception):  # a callee's broad handler
            signal.raise_signal(signal.SIGTERM)  # the handler runs before this call returns

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker.providers, "load", lambda _agent: stub_provider)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", absorbing_check)
    spec = TaskSpec("absorbed-cancel", "codex", "echo", None, "read-only", sandbox.repo,
                    sandbox.repo / "absorbed-cancel.prompt", sandbox.tasks / "absorbed-cancel.result")
    spec.prompt_file.write_bytes(b"literal final response")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main",
                              run_git(sandbox.repo, "rev-parse", "HEAD"), {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "absorbed-cancel.prompt")
    path = store.create(record, b"literal final response")
    (sandbox.tasks / "logs").mkdir()
    original_term, original_int = signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)
    try:
        worker.supervise(path, {}, 10)
    finally:
        signal.signal(signal.SIGTERM, original_term)
        signal.signal(signal.SIGINT, original_int)
    result = json.loads(path.read_text())
    assert (result["status"], result["error"], result["provider_pgid"]) == ("cancelled", "cancelled by client", None)
    assert not (sandbox.tasks / "absorbed-cancel.started").exists()


@pytest.mark.parametrize("receipt", [None, "refused", "ran"])
def test_read_only_agy_run_needs_a_verified_boundary_receipt(sandbox, monkeypatch, receipt):
    """C-3027: the receipt, never the provider's output, decides a read-only AGY run and its Sources count."""
    from tests.dispatcher import stub_provider

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker.providers, "load", lambda _agent: stub_provider)
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(agy_sandbox, "unavailable", lambda: None)
    monkeypatch.setattr(worker.headroom, "check_plan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(worker.headroom, "check_runtime", lambda *_args, **_kwargs: None)
    discarded = []
    monkeypatch.setattr(agy_sandbox, "discard", discarded.append)
    spec = TaskSpec("agy-ro", "agy", "echo", None, "read-only", sandbox.repo,
                    sandbox.repo / "agy-ro.prompt", sandbox.tasks / "agy-ro.result")
    spec.prompt_file.write_bytes(b"VERDICT: APPROVE")
    head = run_git(sandbox.repo, "rev-parse", "HEAD")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main", head,
                              {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "agy-ro.prompt")
    path = store.create(record, b"VERDICT: APPROVE")
    (sandbox.tasks / "logs").mkdir()
    if receipt is not None:
        state = {"head": head, "clean": True}
        agy_sandbox.receipt_file(spec.final_file).write_text(json.dumps({
            "schema": agy_sandbox.SCHEMA, "task_id": "agy-ro", "status": receipt, "reason": "the sandbox canary failed",
            "canary": {"passed": receipt == "ran"}, "input": {"start": state, "end": state},
            "sources": {"completed": 4},
        }))
    worker.supervise(path, {}, 10)
    result = json.loads(path.read_text())
    assert discarded == ["agy-ro"]
    if receipt == "ran":
        assert (result["status"], result["sources_mcp_call_count"]) == ("done", 4)
        assert result["read_only_boundary"]["canary"] == {"passed": True}
    else:
        assert result["status"] == "failed" and "sources_mcp_call_count" not in result
        assert result["error"].startswith("agy_read_only_boundary: ")


@pytest.mark.parametrize("flags,restored", [
    ([], set()), (["--full-checkout"], {"curriculum", "site/src/data"}),
    (["--sparse-include", "/curriculum/"], {"curriculum"}),
    (["--sparse-include", "curriculum", "--sparse-include", "site/src/data"], {"curriculum", "site/src/data"}),
    (["--owned-path", "data/projects/fixture.txt"], {"data/projects"}),
    (["--research-owned-path", "./data//projects/./**/*.json"], {"data/projects"}),
    (["--owned-path", "tests/projects/open_model_data/test_mine.py"], {"data/projects"}),
    (["--research-owned-path", "scripts/projects/open_model_data/**"], {"data/projects"}),
    (["--owned-path", "site"], {"site/src/content", "site/src/data"}),
    (["--owned-path", "curriculum/**", "--sparse-include", "data/projects"],
     {"curriculum", "data/projects", "registry/lexicon/source-inventory", "site/src/content"}),
    (["--owned-path", "data/projects-other", "--research-owned-path", "scripts/projects/open_model_database"], set()),
    (["--owned-path", "../data/projects", "--research-owned-path", "/data/projects"], set()),
])
def test_sparse_dispatch_never_turns_on_sparse_checkout_in_primary_or_sibling_worktrees(sandbox, flags, restored):
    """Owned paths must restore required trees without changing another checkout's sparse settings."""
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
    mode = ["--mode", "workspace-write"] if "--owned-path" in flags else []
    task = sandbox.dispatch("blocked", *mode, *flags)
    worktree = Path(json.loads((sandbox.tasks / f"{task[0]}.json").read_text())["cwd"])
    await_file(sandbox.tasks / f"{task[0]}.started")
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
    (sandbox.tasks / f"{task[0]}.release").touch()
    # A write task that commits nothing settles as undelivered; the sparse checkout is what this test covers.
    assert sandbox.settle(task, expected=1 if mode else 0)["worktree_disposition"] == "removed"


def test_dispatch_without_a_curriculum_path_keeps_curriculum_inputs_excluded(sandbox):
    """A dispatch that owns no curriculum path does not gain the curriculum input trees."""
    owned = sandbox.repo / "docs/owned.md"
    owned.parent.mkdir()
    owned.write_text("owned")
    for directory in ("registry/lexicon/source-inventory", "site/src/content"):
        path = sandbox.repo / directory / "fixture.txt"
        path.parent.mkdir(parents=True)
        path.write_text("tracked fixture")
    run_git(sandbox.repo, "add", ".")
    run_git(sandbox.repo, "commit", "-m", "non-curriculum owned path")
    run_git(sandbox.repo, "push", "origin", "main")
    task = sandbox.dispatch("blocked", "--mode", "workspace-write", "--owned-path", "docs/owned.md")
    worktree = Path(json.loads((sandbox.tasks / f"{task[0]}.json").read_text())["cwd"])
    await_file(sandbox.tasks / f"{task[0]}.started")
    assert (worktree / "docs/owned.md").read_text() == "owned"
    assert not (worktree / "registry/lexicon/source-inventory/fixture.txt").exists()
    assert not (worktree / "site/src/content/fixture.txt").exists()
    (sandbox.tasks / f"{task[0]}.release").touch()
    assert sandbox.settle(task, expected=1)["worktree_disposition"] == "removed"


@pytest.mark.parametrize("owned,gains", [
    ("scripts/lexicon", True), ("scripts/lexicon/x.py", True), ("scripts/**", True),
    ("scripts/dispatcher/cli.py", False),
])
def test_owning_a_lexicon_path_also_owns_the_fingerprint_its_gate_regenerates(sandbox, owned, gains):
    """The fingerprint is added once, so the record, the sparse checkout and the advisory binding agree (#12169)."""
    fingerprint = "site/src/data/lexicon-manifest.fingerprint.json"
    for relative in ("scripts/lexicon/x.py", fingerprint):
        (sandbox.repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (sandbox.repo / relative).write_text("tracked fixture")
    run_git(sandbox.repo, "add", ".")
    run_git(sandbox.repo, "commit", "-m", "lexicon fixture")
    run_git(sandbox.repo, "push", "origin", "main")

    def binding(*paths):
        flags = [flag for path in paths for flag in ("--owned-path", path)]
        return sandbox.cli("dispatch", "--agent", "sol", "--model", "echo", "--mode", "workspace-write",
                           "--task-id", "binding", "--prompt", "literal final response",
                           "--print-advisory-binding", *flags).stdout

    assert (binding(owned) == binding(owned, fingerprint)) is gains
    result = sandbox.cli("dispatch", "--agent", "sol", "--model", "blocked", "--prompt", "literal final response",
                         "--mode", "workspace-write", "--owned-path", owned)
    task = tuple(result.stdout.splitlines())
    assert (fingerprint in result.stderr) is gains
    record = json.loads((sandbox.tasks / f"{task[0]}.json").read_text())
    assert record["owned_paths"] == ([owned, fingerprint] if gains else [owned])
    await_file(sandbox.tasks / f"{task[0]}.started")
    assert (Path(record["cwd"]) / fingerprint).exists() is gains
    (sandbox.tasks / f"{task[0]}.release").touch()
    assert sandbox.settle(task, expected=1)["worktree_disposition"] == "removed"


@pytest.mark.parametrize("redirected", [False, True])
def test_sparse_dispatch_never_turns_on_sparse_checkout_in_primary_with_git_redirects(sandbox, monkeypatch, redirected):
    tracked = sandbox.repo / "curriculum/tracked.txt"
    tracked.parent.mkdir(exist_ok=True)
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


def linked_entry(sandbox, tree, *command):
    return subprocess.run([sys.executable, *command], cwd=tree, env=sandbox.env, text=True,
                          capture_output=True, timeout=30)


@pytest.mark.parametrize("entry", [("scripts/dispatch.py",), ("-m", "scripts.dispatcher.cli")])
def test_linked_worktree_entry_runs_the_primary_checkout_dispatcher(sandbox, entry):
    """Defect: a worktree on an older branch supervised its tasks with its own stale dispatcher (FR-43)."""
    tree = prior_worktree(sandbox, "older-branch")
    primary_entry = sandbox.repo.resolve() / "scripts/dispatch.py"
    primary_entry.write_text("import json, os, sys\nprint(json.dumps([sys.argv, os.getcwd()]))\n")
    result = linked_entry(sandbox, tree, *entry, "list", "--status", "running")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [[str(primary_entry), "list", "--status", "running"], str(tree.resolve())]


@pytest.mark.parametrize("metadata", [b"gitdir: /nonexistent/metadata\n", b"gitdir: \xff\n", b"gitdir: /a\0b\n"])
def test_linked_worktree_entry_refuses_an_unresolvable_primary(sandbox, metadata):
    tree = prior_worktree(sandbox, "detached-metadata")
    (tree / ".git").write_bytes(metadata)
    result = linked_entry(sandbox, tree, "scripts/dispatch.py", "list")
    assert result.returncode == 2
    assert "cannot resolve the primary checkout of linked worktree" in result.stderr


def test_sandbox_dispatch_never_starts_a_host_systemd_scope(sandbox):
    """Defect class: test sandbox escape. The dispatcher subprocess probed the host user manager and ran
    the stub worker in a real ``lu-worker-*`` scope, outside the in-process probe stub."""
    record = sandbox.settle(sandbox.dispatch())
    assert record["status"] == "done"
    assert record["launch_mode"] == "popen-fallback" and "launch_unit" not in record
    assert record["launch_fallback_reason"] == "forced: LU_DISPATCH_ISOLATION=fallback"
