"""Protected review execution retains the Sources and filesystem boundaries."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import Mock

import pytest

from scripts.dispatcher import checks, cli, git, store, worker
from scripts.dispatcher.types import TaskSpec
from scripts.review.record import attested_return, dispatch_prompt_sha256
from tests.agent_runtime import test_attempt_boundary as boundary_tests

world = boundary_tests.world


@pytest.mark.parametrize("agent,model,admitted", [
    ("claude", "claude-opus-5-5", False), ("codex", "gpt-6.1-sol", False),
    ("cursor", "grok-4.7-high", True),
])
def test_trusted_review_admission_excludes_every_author_of_the_branch(tmp_path, monkeypatch, agent, model, admitted):
    """Ported from tests/test_delegate_review_admission.py::test_trusted_review_admission_excludes_every_author_of_the_branch."""
    from scripts.review import dispatch_execution as execution
    from tests.test_authoring_review_feasibility import OPUS, SOL, mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    repo.commit(OPUS, message="first author")
    repo.commit(SOL, message="latest author")
    repo.publish()
    monkeypatch.setattr(execution, "_local_repo_root", repo.root)
    args = cli.build_parser().parse_args([
        "dispatch", "--agent", agent, "--model", model, "--branch", "feature",
        "--review-author-model", "gpt-6.1-sol", "--risk", "medium",
    ])
    if admitted:
        assert execution.admit(args, b"Review", agent) == {}
    else:
        with pytest.raises(ValueError, match="REVIEW_ROUTE_REFUSED"):
            execution.admit(args, b"Review", agent)


@pytest.mark.parametrize("author_id,archived", [("author-one", False), ("gpt-6.1-sol", False), ("gpt-6.1-sol", True)])
@pytest.mark.parametrize("same_task,outside_available", [(True, False), (True, True), (False, True), (False, False)])
def test_red_team_branch_task_and_preference_gate(tmp_path, monkeypatch, author_id, archived, same_task, outside_available):
    """Ported from tests/test_delegate_review_admission.py::test_red_team_branch_task_and_preference_gate.

    V2 has no --force-agent flag; both legacy force variants share this admission.
    """
    from scripts.fleet import credit_lane
    from scripts.review import dispatch_execution as execution
    from tests.test_authoring_review_feasibility import mini_repo

    repo = mini_repo(tmp_path, monkeypatch)
    tasks = tmp_path / "tasks"
    records = tasks / "archive" if archived else tasks
    records.mkdir(parents=True)
    (records / f"{author_id}.json").write_text(json.dumps({
        "repository": "learn-ukrainian/learn-ukrainian.github.io", "agent": "codex",
        "model": "gpt-6.1-sol", "task_id": f"codex/{author_id.upper()}",
    }))
    repo.commit(f"codex/{author_id}")
    repo.publish()
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(execution, "_local_repo_root", repo.root)
    monkeypatch.setattr(credit_lane, "read_routing_budget", lambda: {
        "claude": "healthy" if outside_available else "unhealthy", "grok": "unhealthy",
        "cursor": "unhealthy", "agy": "unhealthy",
    })
    args = cli.build_parser().parse_args([
        "dispatch", "--agent", "codex", "--model", "gpt-6.1-sol", "--branch", "feature",
        "--review-author-model", "gpt-6.1-sol", "--risk", "critical", "--review-mode", "red_team",
        "--task-id", author_id if same_task else "review-one",
    ])
    refusal = "SELF_REVIEW_DETECTED" if same_task else "RED_TEAM_REFUSED: reviewer model equals a branch author model"
    with pytest.raises(ValueError, match=refusal):
        execution.admit(args, b"Adversarial red-team review", "codex")
    assert args._red_team_branch_facts["author_task_ids"] == [author_id]


@pytest.mark.parametrize("profile", ["code", "infra"])
def test_attempt_record_paths_reach_immutable_review_admission(tmp_path, monkeypatch, profile):
    """Ported from tests/test_ask_review_admission_floor.py::test_attempt_record_paths_reach_immutable_review_admission."""
    from scripts.review import dispatch_execution as execution

    manifest = tmp_path / "attempt.json"
    manifest.write_text(json.dumps({"target": {"changed_paths": ["scripts/delegate.py"]}}))
    args = cli.build_parser().parse_args([
        "dispatch", "--agent", "claude", "--model", "claude-sonnet-5-5", "--task-id", "immutable",
        "--review-id", "review", "--attempt-id", "attempt", "--review-attempt", str(manifest),
        "--review-profile", profile,
    ])
    # A route refusal must precede prompt rendering, reservation and provisioning.
    monkeypatch.setattr(execution, "_review_attempt_prompt_admission",
                        lambda *a: pytest.fail("ineligible reviewer reached prompt preparation"))
    with pytest.raises(ValueError, match="REVIEW_ATTEMPT_IDENTITY_REFUSED"):
        execution.admit(args, b"Review", "claude")


@pytest.mark.parametrize("explicit", [False, True])
def test_default_label_ignores_ambient_other_config_directory(world, monkeypatch, explicit):
    """Account a must never run on another account's inherited config directory."""
    from dataclasses import replace

    from scripts.agent_runtime.attempt_boundary import linux_claude_auth
    from scripts.dispatcher.environment import child_env

    root, home = world
    for directory, token in ((".claude", "fixture-default-token"), (".claude-b", "fixture-other-token")):
        config = home / directory
        config.mkdir()
        credential = config / ".credentials.json"
        credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": token, "expiresAt": 4102444800000}}))
        credential.chmod(0o600)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home / ".claude-b"))
    spec = TaskSpec("default-a", "claude", "claude-opus-5-5", None, "read-only", root,
                    root / "prompt", root / "result", claude_account="a" if explicit else None,
                    options={"review_attempt": "fixture-manifest"})
    env = child_env(spec)
    assert env["CLAUDE_CONFIG_DIR"] == str(home / ".claude")
    assert linux_claude_auth(spec.claude_account, environ=env) == {"CLAUDE_CODE_OAUTH_TOKEN": "fixture-default-token"}
    # Account resolution also records a built-in a for an ordinary unlabelled run.
    spec = replace(spec, claude_account="a", options={
        "claude_account_source": "explicit" if explicit else "builtin",
    })
    ordinary = child_env(spec)
    assert ordinary["CLAUDE_CONFIG_DIR"] == str(home / ".claude")


@pytest.mark.parametrize("label,source,verify,method,credential", [
    ("a", "builtin", False, "host_login", "api_key"),
    ("b", "default-file", True, "bound_account_token", "oauth_token"),
    ("b", "default-file", True, "subscription_login", "subscription_login"),
    ("b", "explicit", False, "unverified", "oauth_token"),
])
@pytest.mark.parametrize("launch_error", [None, "CLAUDE_ACCOUNT_REFUSED: claude_account_auth_method_conflict",
                                         "sensitive diagnostic /private/path"])
def test_worker_records_this_runs_claude_auth_receipt(
    tmp_path, monkeypatch, label, source, verify, method, credential, launch_error,
):
    """Ported from tests/test_delegate.py::test_worker_records_a_verified_value_free_auth_receipt,
    tests/test_delegate.py::test_worker_receipt_is_unverified_without_this_runs_verification,
    tests/test_delegate.py::test_worker_receipt_for_the_default_label_names_the_host_login.
    """
    import sys
    from types import SimpleNamespace

    from scripts.agent_runtime.attempt_boundary import note_claude_account_verified
    from scripts.dispatcher.types import Invocation, ParsedResult

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    prompt = tmp_path / "prompt"
    spec = TaskSpec("receipt", "claude", "claude-opus-5-5", None, "read-only", tmp_path,
                    prompt, tmp_path / "result", claude_account=label)
    prompt.write_bytes(b"Review")
    record = store.new_record(spec, dict(key="public", github="example/public"), "claude/receipt", "a" * 40,
                              dict(research_owned_path=[]))
    prompt.unlink()  # store.create exclusively owns prompt creation.
    record["claude_account_source"] = source
    path = store.create(record, b"Review")
    (path.parent / "logs").mkdir()
    note_claude_account_verified("b", "subscription_login")  # stale receipt must never survive.
    env = ({"ANTHROPIC_API_KEY" if credential == "api_key" else "CLAUDE_CODE_OAUTH_TOKEN": "fixture-value"}
           if credential in {"api_key", "oauth_token"} else {})

    def build(spec, env):
        if verify:
            note_claude_account_verified(label, method)
        return Invocation([sys.executable, "-c", "print('reviewed')"], None, env, None)

    monkeypatch.setattr(worker, "child_env", lambda spec: dict(env))
    # This fixture supplies auth observations; test_admission_ports covers the launch guard.
    def launch(spec, invocation):
        if launch_error:
            raise ValueError(launch_error)
        return invocation

    monkeypatch.setattr(worker.admission, "claude_launch", launch)
    monkeypatch.setattr(worker.providers, "load", lambda _: SimpleNamespace(
        build=build, parse=lambda *a: ParsedResult("reviewed", None, None)))
    monkeypatch.setattr(worker.git, "snapshot_delivery", lambda *a: {})
    monkeypatch.setattr(worker, "_reap_settled", lambda *a: None)
    worker.supervise(path, {}, 30)
    saved = json.loads(path.read_bytes())
    if launch_error:
        assert saved["status"] == "failed"
        assert saved["error"] == (launch_error if launch_error.startswith("CLAUDE_ACCOUNT_REFUSED:") else "ValueError")
        assert "sensitive diagnostic" not in json.dumps(saved)
        return
    assert saved["status"] == "done", saved["error"]
    assert saved["claude_account_auth"] == dict(label=label, source=source, method=method,
                                               verified=verify, credential_class=credential)


@pytest.fixture
def attempt(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("inputs: []\ntarget:\n  changed_paths: [ordinary.py]\n")
    return ["--review-id", "review", "--attempt-id", "attempt", "--review-attempt", str(manifest)]


def invoke(attempt, *flags):
    return cli.main(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", "--prompt", "Review", *attempt, *flags])


@pytest.mark.parametrize("flags", [("--mode", "workspace-write"), ("--cwd", "existing")])
def test_attempt_cannot_write_or_reuse_a_worktree(attempt, monkeypatch, capsys, flags):
    launch = Mock()
    monkeypatch.setattr(worker, "start", launch)
    assert invoke(attempt, *flags) == 2
    assert "review attempt requires" in capsys.readouterr().err
    launch.assert_not_called()


def test_bound_launch_refuses_until_runtime_isolation_is_wired(attempt, monkeypatch, capsys):
    """An unrendered prompt is still refused before worktree creation."""
    create = Mock()
    monkeypatch.setattr(git, "create_worktree", create)
    assert invoke(attempt) == 2
    assert "review_render_record_missing" in capsys.readouterr().err
    create.assert_not_called()


@pytest.mark.parametrize("low_memory", [False, True])
def test_dry_run_reports_binding_without_spending_attempt(attempt, tmp_path, monkeypatch, capsys, low_memory):
    """Resource refusal precedes dry-run output, reservation and checkout creation."""
    from types import SimpleNamespace

    real_read = Path.read_text
    available = 8.5 * 1024**3 - (1024 if low_memory else 0)
    monkeypatch.setattr(Path, "read_text", lambda path, *a, **kw: (
        f"MemAvailable: {int(available / 1024)} kB\n" if path == Path("/proc/meminfo")
        else real_read(path, *a, **kw)
    ))
    monkeypatch.setattr(checks.shutil, "disk_usage", lambda _: SimpleNamespace(used=89, total=100))
    resources = Mock(wraps=checks.check_resources)
    create = Mock()
    reserve = Mock()
    worktree = tmp_path / "checkout"
    monkeypatch.setattr(git, "resolve_repo", lambda _: (tmp_path, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (worktree, "codex/review", "a" * 40))
    monkeypatch.setattr(checks, "check_resources", resources)
    monkeypatch.setattr(git, "create_worktree", create)
    monkeypatch.setattr(cli.host_admission, "reserve", reserve)
    for _ in range(2):
        if low_memory:
            assert invoke(attempt, "--dry-run") == 2
            output = capsys.readouterr()
            assert "insufficient memory" in output.err
            assert not output.out
            continue
        assert invoke(attempt, "--dry-run") == 0
        plan = json.loads(capsys.readouterr().out)
        assert plan["review_attempt"] == dict(review_id="review", attempt_id="attempt",
                                             manifest_sha256=store.digest(b"inputs: []\ntarget:\n  changed_paths: [ordinary.py]\n"))
        assert plan["review_access"] == "isolated"
    assert resources.call_count == 2
    resources.assert_called_with((worktree, tmp_path / "tasks"))
    if low_memory:
        for flags in ((), ("--mode", "workspace-write", "--force-admission", "resource regression")):
            assert invoke([], *flags) == 2
            assert "insufficient memory" in capsys.readouterr().err
        assert resources.call_count == 4
    create.assert_not_called()
    reserve.assert_not_called()
    assert not worktree.exists()
    assert not (tmp_path / "tasks").exists()


@pytest.mark.parametrize("suffix", [".jsonl", ".jsonl.sha256", ".mcp.json", ".codex-home", ".agy-home"])
def test_legacy_artifact_spends_attempt_even_without_task_record(attempt, tmp_path, suffix, capsys):
    receipts = tmp_path / "review-receipts" / "review"
    receipts.mkdir(parents=True)
    (receipts / f"attempt{suffix}").symlink_to("missing")
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("schema", [1, 2])
def test_archived_record_spends_attempt_across_manifest_changes(attempt, tmp_path, schema, capsys):
    archive = tmp_path / "tasks" / "archive"
    archive.mkdir(parents=True)
    (archive / "prior.json").write_text(json.dumps(dict(schema_version=schema, status="failed", review_attempt={
        "review_id": "review", "attempt_id": "attempt", "manifest_sha256": "b" * 64})))
    assert invoke(attempt, "--dry-run") == 2
    assert "already spent" in capsys.readouterr().err


@pytest.mark.parametrize("access", [None, "isolated", "full"])
def test_binding_snapshot_attests_v2_return_and_survives_record_corruption(attempt, tmp_path, access):
    if access:
        attempt += ["--review-access", access]
    args = cli.build_parser().parse_args(["dispatch", "--agent", "sol", "--model", "gpt-6.1-sol", *attempt])
    binding = store.review_binding(vars(args))
    store.check_review_attempt(binding, claim=True)
    # Admission's snapshot must survive a subsequent manifest edit.
    (tmp_path / "manifest.yaml").write_text("changed\n")
    prompt = cli._PromptPath(tmp_path / "tasks" / "task.prompt")
    prompt.content = b"Review\n"
    spec = TaskSpec("task", "codex", "gpt-6.1-sol", None, "read-only", tmp_path, prompt, prompt.with_suffix(".result"))
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/task", "a" * 40,
                              dict(vars(args), research_owned_path=[]), binding=binding)
    store.create(record, b"Review\n")
    record = store.read("task")
    assert record["schema_version"] == 2 and record["review_attempt"] == binding
    assert binding == dict(review_id="review", attempt_id="attempt", manifest_sha256=store.digest(b"inputs: []\ntarget:\n  changed_paths: [ordinary.py]\n"))
    assert record["prompt_sha256"] == store.digest(b"Review\n") and record["review_access"] == (access or "isolated")
    data = f"reviewer:\n  prompt_sha256: '{record['prompt_sha256']}'\n".encode()
    spec.final_file.write_bytes(data)
    record.update(status="done", result_sha256=store.digest(data))
    store.replace(record)
    assert dispatch_prompt_sha256("task", prompt.parent, **binding) == store.digest(b"Review\n")
    assert attested_return(data, task_id="task", tasks_dir=prompt.parent, manifest_path=tmp_path / "manifest.yaml",
                           root=tmp_path, **binding) == data
    store.record_path("task").write_text("{")
    with pytest.raises(ValueError, match="unreadable task record"):
        store.check_review_attempt(binding, claim=True)
    assert (tmp_path / "review-receipts/review/attempt.jsonl").is_file()


@pytest.mark.parametrize("flags", [["--review-access", "isolated"], ["--attempt-id", "attempt"],
                                  ["--review-id", "../review", "--attempt-id", "attempt", "--review-attempt", "a" * 64]])
def test_partial_or_unsafe_binding_refused_without_launch(flags, capsys):
    assert invoke(flags) == 2
    expected = "must be used together" if len(flags) == 2 else "invalid review"
    assert expected in capsys.readouterr().err


@pytest.mark.parametrize("manifest", ["a" * 64, "."])
def test_manifest_must_be_a_file(attempt, manifest, capsys):
    attempt[-1] = manifest
    assert invoke(attempt, "--dry-run") == 2
    assert "must name a manifest file" in capsys.readouterr().err


def test_concurrent_admissions_claim_one_pair_for_different_tasks(attempt, tmp_path, monkeypatch):
    from scripts.agent_runtime import review_mcp

    binding = dict(review_id="review", attempt_id="attempt", manifest_sha256="a" * 64)
    barrier, create = Barrier(2), review_mcp._create_file

    def exclusive(*args):
        if args[0].endswith(".jsonl"):
            barrier.wait(timeout=10)  # Force both preparations past the artifact scan.
        create(*args)

    monkeypatch.setattr(review_mcp, "_create_file", exclusive)

    def admit(task_id):
        try:
            review_mcp.prepare_review_attempt("review", "attempt", Path(attempt[-1]), "claude",
                                              receipts_root=tmp_path / "review-receipts")
        except FileExistsError:
            return "spent"
        store.create(dict(task_id=task_id, prompt_file=str(tmp_path / f"{task_id}.prompt"),
                          review_attempt=binding), b"Review")
        return "admitted"

    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(admit, ["first", "second"])) == ["admitted", "spent"]
    assert len(store.list_tasks()) == 1


@pytest.mark.parametrize("refusal", ["concurrent_pair_taken", "worktree_lock_error"])
def test_refusal_after_creation_leaves_no_orphan_worktree_or_branch_and_exits_2(
    attempt, tmp_path, monkeypatch, capsys, refusal,
):
    from scripts.agent_runtime import review_mcp
    from scripts.orchestration import worktree_claims
    from scripts.review import dispatch_execution as execution

    repo = tmp_path / "repo"
    repo.mkdir()
    git._git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".worktrees/\nnode_modules\nsite/node_modules\ndata/*.db\n")
    (repo / "node_modules").mkdir()
    (repo / "data").mkdir()
    (repo / "data/sources.db").write_bytes(b"fixture")
    git._git(repo, "add", ".gitignore")
    git._git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "--allow-empty", "-m", "fixture")
    monkeypatch.setattr(git, "resolve_repo", lambda _: (repo, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "ROOT", repo)
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    monkeypatch.setattr(execution, "_REPO_ROOT", repo)
    monkeypatch.setattr(execution, "_worktree_lock_dir", lambda: tmp_path / "locks")
    monkeypatch.setattr(execution, "admit", lambda *a: dict(
        review_contract={}, review_input_root=str(repo), review_input_paths=[]))
    monkeypatch.setattr(review_mcp, "review_server_checkout", lambda: tmp_path)
    monkeypatch.setattr(review_mcp, "check_launch_contract", lambda *a: None)
    worktree = repo / ".worktrees/dispatch/codex/refused"

    def refuse_after_creation(*args, **kwargs):
        assert worktree.is_dir()
        assert git._git(worktree, "branch", "--show-current") == "codex/refused"
        if refusal == "worktree_lock_error":
            raise worktree_claims.WorktreeLockError(f"private lock directory: {tmp_path / 'locks'}")
        # Another dispatcher spends the pair between admission and preparation.
        receipts = tmp_path / "batch_state/review-receipts/review"
        receipts.mkdir(parents=True)
        (receipts / "attempt.jsonl").write_bytes(b"")

    monkeypatch.setattr(execution, "_lock_review_input_root", refuse_after_creation)
    monkeypatch.setattr(worker, "start", lambda *a: pytest.fail("refused review launched a worker"))
    assert invoke(attempt, "--task-id", "refused", "--base", "main") == 2
    output = capsys.readouterr()
    assert "Traceback" not in output.err
    assert str(tmp_path) not in output.err
    assert not worktree.exists()
    assert str(worktree) not in git._git(repo, "worktree", "list", "--porcelain")
    assert "refs/heads/codex/refused" not in git._git(repo, "for-each-ref", "--format=%(refname)")
    assert store.read("refused", missing_ok=True) is None


@pytest.mark.parametrize("failure", ["launch_refused", "fallback_refused", "popen_failed", "pid_exists"])
def test_post_record_spawn_failure_leaks_unstarted_checkout_and_reservation(
    attempt, tmp_path, monkeypatch, failure,
):
    from types import SimpleNamespace

    from scripts.agent_runtime import review_mcp
    from scripts.dispatcher import admission
    from scripts.review import dispatch_execution as execution

    repo = tmp_path / "repo"
    repo.mkdir()
    git._git(repo, "init", "-b", "main")
    (repo / ".gitignore").write_text(".worktrees/\n")
    git._git(repo, "add", ".gitignore")
    git._git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "commit", "-m", "fixture")
    monkeypatch.setattr(git, "resolve_repo", lambda _: (repo, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "ROOT", repo)
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    monkeypatch.setattr(execution, "_REPO_ROOT", repo)
    monkeypatch.setattr(execution, "_worktree_lock_dir", lambda: repo / ".git/lu-worktree-locks")
    monkeypatch.setattr(execution, "admit", lambda *a: dict(
        review_contract={}, review_input_root=str(repo), review_input_paths=[]))
    monkeypatch.setattr(execution, "_lock_review_input_root", lambda *a, **kw: None)
    server_launch = review_mcp.sources_server_launch()
    monkeypatch.setattr(review_mcp, "sources_server_launch", lambda: server_launch)
    monkeypatch.setattr(review_mcp, "review_server_checkout", lambda: tmp_path)
    monkeypatch.setattr(review_mcp, "check_launch_contract", lambda *a: None)
    monkeypatch.setattr(review_mcp, "review_attempt_tool_config", lambda *a, **kw: {})
    error = (OSError("sensitive /private/credential") if failure == "popen_failed" else
             admission.LaunchRefused("private diagnostic", dict(status="failed", error=(
                 "dispatch_fallback_refused" if failure == "fallback_refused" else "worker_spawn_failed"))))

    def spawn(*a, **kw):
        if failure == "pid_exists":
            return SimpleNamespace(pid=12345, stdin=SimpleNamespace(write=Mock(side_effect=error))), {}
        raise error

    monkeypatch.setattr(admission, "spawn_supervisor", spawn)
    monkeypatch.setattr(worker, "_identity", lambda pid: "fixture-start")
    assert invoke(attempt, "--task-id", "spawn-refused", "--base", "main") in {1, 2}
    state = store.read("spawn-refused")
    worktree = repo / ".worktrees/dispatch/codex/spawn-refused"
    if failure == "pid_exists":
        assert state["pid"] == 12345
        assert worktree.is_dir()
        assert state.get("review_attempt_reservation") != "released"
        return
    assert state["pid"] is None
    assert state["status"] == "failed"
    assert "sensitive" not in state["error"] and "/private" not in state["error"]
    assert not worktree.exists()
    assert str(worktree) not in git._git(repo, "worktree", "list", "--porcelain")
    assert "refs/heads/codex/spawn-refused" not in git._git(repo, "for-each-ref", "--format=%(refname)")
    assert state["review_attempt_reservation"] == "released"


def test_review_attempt_input_paths_cover_manifest_and_code(tmp_path, monkeypatch):
    """Ported from tests/test_delegate_review_admission.py::test_review_attempt_input_paths_cover_manifest_and_code."""
    from scripts.review import dispatch_execution

    monkeypatch.setattr(dispatch_execution, "_local_repo_root", tmp_path / "code")
    manifest = tmp_path / "review.yaml"
    assert dispatch_execution._review_attempt_input_paths(str(manifest)) == [manifest.resolve(), tmp_path / "code"]


def test_review_input_lock_covers_extra_inputs_and_refuses_missing_one(tmp_path, monkeypatch):
    """Ported from tests/test_delegate_review_admission.py::test_review_input_lock_covers_extra_inputs_and_refuses_missing_one."""
    import contextlib

    from scripts.orchestration import worktree_claims
    from scripts.review import dispatch_execution as execution

    root_tree, manifest_tree = tmp_path / "root-tree", tmp_path / "manifest-tree"
    (root_tree / "inputs").mkdir(parents=True)
    manifest_tree.mkdir()
    manifest = manifest_tree / "review.yaml"
    manifest.write_text("review: test\ntarget:\n  changed_paths: [ordinary.py]\n")
    wc = execution._load_worktree_containment()
    monkeypatch.setattr(wc, "resolve_main_root", lambda _path: tmp_path)
    monkeypatch.setattr(wc, "registered_worktrees", lambda _path: [tmp_path, root_tree, manifest_tree])
    monkeypatch.setattr(execution, "_worktree_lock_dir", lambda: tmp_path / "locks")
    contract = {"input_root": str(root_tree / "inputs")}
    with contextlib.ExitStack() as locks:
        execution._lock_review_input_root(contract, locks, inputs=[manifest, tmp_path])
        for tree in (root_tree, manifest_tree):
            with pytest.raises(worktree_claims.WorktreeLockReentry):
                with execution.worktree_lock(tree):
                    pass
    with execution.worktree_lock(manifest_tree):
        pass
    with (
        contextlib.ExitStack() as locks,
        pytest.raises(ValueError, match="review attempt input disappeared before preparation"),
    ):
        execution._lock_review_input_root(contract, locks, inputs=[manifest_tree / "gone.yaml"])


def test_runner_reports_real_input_hash_refusal_before_provider_launch(world, tmp_path, monkeypatch):
    """Ported from tests/agent_runtime/test_attempt_boundary.py::test_runner_reports_real_input_hash_refusal_before_provider_launch."""
    from scripts.review.dispatch_execution import Execution
    from scripts.review.isolation import ReviewIsolationError
    from tests.agent_runtime.test_attempt_boundary import attempt_config, manifest_world

    root, _ = world
    manifest = manifest_world(root, "plan")
    tc = attempt_config(root, tmp_path, manifest, "agy")
    (root / manifest["inputs"]["plan"]["path"]).write_text("Changed after the manifest was pinned.\n")
    prompt = tmp_path / "prompt"
    prompt.write_text("probe")
    spec = TaskSpec("probe", "agy", "gemini-3.8-flash-high", None, "read-only", root, prompt,
                    tmp_path / "result", options={"review_tool_config": tc})
    record = dict(review_attempt={"manifest_sha256": store.digest(Path(tc["review_manifest"]).read_bytes())},
                  prompt_sha256=store.digest(prompt.read_bytes()))
    with pytest.raises(ValueError) as caught:
        Execution(spec, record, {})
    assert str(caught.value) == "formal attempt filesystem boundary refused: prepare: attempt_input_hash_mismatch"
    assert isinstance(caught.value.__cause__, ReviewIsolationError)


@pytest.mark.parametrize("agent", ["agy", "codex"])
@pytest.mark.parametrize("evidence_error", [None, "review_model_mismatch", "attempt_identity_mismatch",
    "agy_model_identity_unverified", "formal attempt filesystem boundary refused: wrap: attempt_input_hash_mismatch",
    "sensitive diagnostic /private/path"])
def test_runner_executes_attempt_boundary_and_cleans_after_parse(world, tmp_path, monkeypatch, agent, evidence_error):
    """Ported from tests/agent_runtime/test_attempt_boundary.py::test_runner_executes_attempt_boundary_and_cleans_after_parse."""
    import sys
    from types import SimpleNamespace

    from scripts.agent_runtime.adapters.base import InvocationPlan
    from scripts.dispatcher.types import Invocation, ParsedResult
    from tests.agent_runtime.test_attempt_boundary import attempt_config, manifest_world

    root, home = world
    forbidden = home / "previous-session.txt"
    forbidden.write_text("Forbidden")
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    observed = []
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    prompt = tmp_path / "probe.prompt"
    spec = TaskSpec("probe", agent, "gemini-3.8-flash-high" if agent == "agy" else "gpt-6.1-sol",
                    None, "read-only", root, prompt, tmp_path / "result")
    metadata = dict(research_owned_path=[])
    prompt.write_bytes(b"probe")
    record = store.new_record(spec, dict(key="public", github="example/public"), "codex/probe", "a" * 40, metadata,
                              binding=dict(review_id="review", attempt_id="current",
                                           manifest_sha256=store.digest(Path(tc["review_manifest"]).read_bytes())))
    record["review_ledger_path"] = str(tmp_path / "receipts/review/current.jsonl")
    path = store.record_path("probe")
    path.parent.mkdir()
    (path.parent / "logs").mkdir()
    path.write_text(json.dumps(record))

    def build(spec, env):
        boundary = spec.options["review_tool_config"]["review_attempt_boundary"]
        observed.append(boundary)
        script = (
            "import pathlib,sys\n"
            f"assert not pathlib.Path({str(forbidden)!r}).exists()\n"
            "assert pathlib.Path('curriculum/l2-uk-en/lesson-plans/a1/sample.yaml').read_bytes()\n"
            "print(sys.stdin.read(),flush=True)\n"
        )
        argv = [sys.executable, "-c", script]
        spec.options["review_plan"] = InvocationPlan(cmd=argv, cwd=boundary.workspace)
        return Invocation(argv, b"own return", {}, None)

    def parse(stdout, stderr, returncode, final):
        assert observed[0].workspace.exists()
        return ParsedResult(stdout.strip(), None, None if returncode == 0 else stderr)

    monkeypatch.setattr(worker.providers, "load", lambda _: SimpleNamespace(build=build, parse=parse))
    monkeypatch.setattr(worker.git, "snapshot_delivery", lambda *a: {})
    monkeypatch.setattr(worker, "_reap_settled", lambda *a: None)
    # The fixture provider uses Python, so no AGY binary identity probe is needed.
    from scripts.review import dispatch_execution

    original_wrap = dispatch_execution.Execution.wrap
    if agent == "agy":
        def wrap(self, inv):
            from dataclasses import replace
            argv, env = self.boundary.wrap(inv.argv, inv.env)
            return replace(inv, argv=argv, env=env)
        monkeypatch.setattr(dispatch_execution.Execution, "wrap", wrap)
    else:
        monkeypatch.setattr(dispatch_execution.Execution, "wrap", original_wrap)
    if evidence_error:
        def refuse_evidence(self, stdout):
            raise ValueError(evidence_error)

        monkeypatch.setattr(dispatch_execution.Execution, "evidence", refuse_evidence)
    worker.supervise(path, {"review_tool_config": tc}, 30)
    saved = json.loads(path.read_bytes())
    assert saved["status"] == ("failed" if evidence_error else "done"), saved["error"]
    if evidence_error:
        assert saved["error"] == ("ValueError" if evidence_error.startswith("sensitive") else evidence_error)
        assert "sensitive diagnostic" not in json.dumps(saved)
    assert spec.final_file.read_text() == "own return"
    assert observed and not observed[0].workspace.exists()


def test_linux_claude_auth_selects_only_fresh_token(world, monkeypatch):
    """Ported from tests/agent_runtime/test_attempt_boundary.py::test_linux_claude_auth_selects_only_fresh_token."""
    from scripts.agent_runtime import attempt_boundary
    from scripts.review.isolation import ReviewIsolationError

    monkeypatch.setattr(attempt_boundary, "_run_claude_renewal", lambda _directory: pytest.fail("renewed"))
    _, home = world
    credential = home / ".claude" / ".credentials.json"
    credential.parent.mkdir()
    settings = credential.parent / "settings.json"
    settings.write_text("{}")
    settings.chmod(0o644)
    selected = {"CLAUDE_CONFIG_DIR": str(credential.parent)}
    access = "fixture-access-" + "x" * 30
    refresh = "fixture-refresh-" + "y" * 30
    credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": access, "refreshToken": refresh,
                                                      "expiresAt": 4_102_444_800_000}}))
    credential.chmod(0o600)
    assert attempt_boundary.linux_claude_auth(environ=selected) == {"CLAUDE_CODE_OAUTH_TOKEN": access}
    assert attempt_boundary.linux_claude_auth(environ={**selected, "ANTHROPIC_API_KEY": "fixture-key"}) == {
        "ANTHROPIC_API_KEY": "fixture-key"}
    credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": access, "refreshToken": refresh, "expiresAt": 0}}))
    with pytest.raises(ReviewIsolationError, match="expired"):
        attempt_boundary.linux_claude_auth(environ=selected)
    credential.chmod(0o644)
    with pytest.raises(ReviewIsolationError, match="not_private"):
        attempt_boundary.linux_claude_auth(environ=selected)


@pytest.mark.parametrize("agent", ["agy", "codex"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
@pytest.mark.parametrize("review_access", ["isolated", "full"])
def test_real_adapter_uses_fresh_home_and_attempt_outputs(world, tmp_path, monkeypatch, agent, kind, review_access):
    """Ported from tests/agent_runtime/test_attempt_boundary.py::test_real_adapter_uses_fresh_home_and_attempt_outputs."""
    import os
    import shutil
    import subprocess
    import tomllib

    from scripts.agent_runtime.attempt_boundary import AttemptBoundary
    from scripts.dispatcher.providers import load
    from tests.agent_runtime.test_attempt_boundary import attempt_config, manifest_world

    root, home = world
    tc = attempt_config(root, tmp_path, manifest_world(root, kind), agent, review_access=review_access)
    if review_access == "full":
        subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
        tc["review_cwd"] = str(root)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    try:
        if os.environ.get("LU_REVIEW_HOST_PROBES") != "1":
            monkeypatch.setattr(shutil, "which", lambda name: "/bin/true")
            monkeypatch.setattr("scripts.agent_runtime.adapters.agy._require_background_wait_support", lambda binary: None)
        if agent == "agy":
            from scripts.agent_runtime.adapters.agy import AgyAdapter
            monkeypatch.setattr(AgyAdapter, "_resolve_model_flag", lambda self, model: "gemini-3.8-flash-high")
            settings = json.loads((Path(boundary.tool_config["agy_home_override"]) /
                                   ".gemini/antigravity-cli/settings.json").read_text())["permissions"]
            assert [r for r in settings["allow"] if r.startswith("read_file(")] == [f"read_file({boundary.workspace})"]
            assert not any(r.startswith(("command(", "write_file(")) for r in settings["allow"])
            assert "command(*)" in settings["deny"] and "write_file(*)" in settings["deny"]
        prompt = tmp_path / "probe.prompt"
        prompt.write_text("probe")
        spec = TaskSpec("boundary-probe", agent, "gemini-3.8-flash-high" if agent == "agy" else "gpt-6.1-sol",
                        "high", "read-only", root, prompt, tmp_path / "result",
                        options={"review_tool_config": boundary.tool_config})
        invocation = load(agent).build(spec, {})
        plan = spec.options["review_plan"]
        assert plan.cwd == boundary.workspace
        if agent == "agy":
            assert Path(invocation.env["HOME"]).is_relative_to(boundary.write_root)
            assert plan.liveness_paths[0].is_relative_to(boundary.write_root)
        else:
            assert Path(invocation.env["CODEX_HOME"]).is_relative_to(boundary.write_root)
            assert invocation.final_file.is_relative_to(boundary.write_root)
            assert "--dangerously-bypass-approvals-and-sandbox" in invocation.argv
            from scripts.agent_runtime.sources_read_only import sources_tool_sets
            from scripts.review.receipts.ledger import review_tools
            from tests.agent_runtime.test_sources_read_only import _server_config
            sources = tomllib.loads((Path(invocation.env["CODEX_HOME"]) / "config.toml").read_text())["mcp_servers"]["sources"]
            sources.update(_server_config(invocation.argv))
            assert set(sources["enabled_tools"]) == review_tools(review_access)
            assert set(sources["tools"]) == review_tools(review_access)
            assert "verify_words" in sources["enabled_tools"]
            assert not set(sources_tool_sets()[1]) & set(sources["enabled_tools"])
        cmd, env = boundary.wrap([invocation.argv[0], "--version"], plan.env_overrides)
        probe = subprocess.run(cmd, cwd=plan.cwd, env=env, capture_output=True, text=True, timeout=30)
        assert probe.returncode == 0, probe.stderr
        assert probe.stdout.strip()
        assert env["HOME"] != str(home)
    finally:
        boundary.cleanup()


def test_review_attempt_marker_blocks_reuse_but_unmarked_worktree_reuses(tmp_path, monkeypatch, capsys):
    """Ported from tests/test_delegate.py::test_review_attempt_marker_blocks_reuse_but_unmarked_worktree_reuses."""
    from scripts.review import dispatch_execution as execution
    from tests.test_delegate import _init_repo_with_worktree

    main, dispatch_wt = _init_repo_with_worktree(tmp_path)
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.setattr(git, "resolve_repo", lambda _: (main, dict(key="public", github="example/public")))
    monkeypatch.setattr(git, "worktree_plan", lambda *a: (dispatch_wt, "codex/review", "a" * 40))
    monkeypatch.setattr(checks, "check_resources", lambda _: None)
    monkeypatch.setattr(worker, "start", lambda spec, record, prompt, timeout: store.create(record, prompt))
    marker = execution._review_attempt_marker_path(dispatch_wt)
    assert not marker.exists()
    assert invoke([], "--task-id", "unmarked", "--cwd", str(dispatch_wt)) == 0
    assert store.read("unmarked")["worktree_path"] == str(dispatch_wt)
    execution._mark_review_attempt_worktree(dispatch_wt, "review-original")
    assert marker.read_text() == "review-original\n"
    with pytest.raises(ValueError, match=r"review-original.*#8517"):
        execution._refuse_review_attempt_worktree_reuse(dispatch_wt)
    assert invoke([], "--task-id", "marked", "--cwd", str(dispatch_wt)) == 1
    assert "review-original" in capsys.readouterr().err


def test_manifest_prompt_admission_refuses_missing_input_root(tmp_path, monkeypatch):
    """Ported from tests/test_delegate_review_admission.py::test_manifest_prompt_admission_refuses_missing_input_root."""
    from types import SimpleNamespace

    from scripts.review import dispatch_execution as execution
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("manifest_schema: 1\n")
    monkeypatch.setattr("scripts.agent_runtime.review_mcp.check_review_contract", lambda *_args, **_kwargs: {})
    args = SimpleNamespace(review_attempt=str(manifest), prompt_file=None, review_access="isolated")
    refusal, contract = execution._review_attempt_prompt_admission(args, "prompt", "review", "attempt")
    assert "review_input_root_invalid" in refusal
    assert contract is None


@pytest.mark.parametrize("root", [None, "", " ", 7, "\x00"])
def test_review_input_lock_refuses_invalid_explicit_root(root):
    """Ported from tests/test_delegate_review_admission.py::test_review_input_lock_refuses_invalid_explicit_root."""
    import contextlib

    from scripts.review import dispatch_execution as execution
    with contextlib.ExitStack() as locks, pytest.raises(ValueError, match="review_input_root_invalid"):
        execution._lock_review_input_root({"input_root": root}, locks)


def test_default_file_b_records_and_launches_b(tmp_path, monkeypatch):
    """Ported from tests/test_delegate.py::test_default_file_b_records_and_launches_b."""
    from contextlib import nullcontext
    from types import SimpleNamespace

    from scripts.agent_runtime import review_mcp
    from scripts.review import dispatch_execution as execution
    from tests.test_delegate import _bind_claude_account_b, _default_account_file

    selected = _bind_claude_account_b(tmp_path, monkeypatch)
    _default_account_file(tmp_path, monkeypatch, b"b\n")
    root = tmp_path / "checkout"
    root.mkdir()
    manifest = root / "manifest.yaml"
    manifest.write_text("inputs: []\n")
    prompt = tmp_path / "prompt"
    prompt.write_bytes(b"Review")
    args = cli.build_parser().parse_args([
        "dispatch", "--agent", "claude", "--model", "claude-opus-5-5", "--task-id", "default-b",
        "--review-id", "review", "--attempt-id", "current", "--review-attempt", str(manifest),
        "--prompt-file", str(prompt),
    ])
    monkeypatch.setattr("scripts.agent_runtime.target_admission.resolve_and_admit", lambda *a, **kw: (
        SimpleNamespace(recipient="claude", model="claude-opus-5-5"),))
    monkeypatch.setattr(execution, "_review_attempt_prompt_admission",
                        lambda *a: (None, {"input_root": str(root)}))
    admitted = execution.admit(args, b"Review", "claude")
    spec = TaskSpec("default-b", "claude", "claude-opus-5-5", None, "read-only", root, prompt,
                    tmp_path / "result", options={"review_attempt": str(manifest)})
    record = store.new_record(spec, dict(key="public", github="example/public"), "claude/default-b", "a" * 40,
                              dict(research_owned_path=[]), binding=dict(review_id="review", attempt_id="current",
                                manifest_sha256=store.digest(manifest.read_bytes())))
    monkeypatch.setattr(execution, "worktree_lock", lambda *a: nullcontext())
    monkeypatch.setattr(execution, "_lock_review_input_root", lambda *a, **kw: None)
    monkeypatch.setattr(execution, "_mark_review_attempt_worktree", lambda *a: None)
    monkeypatch.setattr(review_mcp, "prepare_review_attempt",
                        lambda *a, **kw: SimpleNamespace(ledger_path=tmp_path / "ledger"))
    monkeypatch.setattr(review_mcp, "review_attempt_tool_config", lambda *a, **kw: {})
    with execution.prepare(spec, record, admitted):
        assert (record["claude_account"], record["claude_account_source"]) == ("b", "default-file")
        assert selected not in json.dumps(record)
        assert spec.options["review_tool_config"]["claude_account"] == "b"
        assert worker._spec(record, spec.options).claude_account == "b"

    # Native bound-account custody is also ported from
    # tests/agent_runtime/test_attempt_boundary.py::test_attempt_boundary_authenticates_claude_seat_as_the_labelled_account.
    import subprocess

    from scripts.dispatcher.environment import child_env
    from tests.agent_runtime.test_attempt_boundary import attempt_config, manifest_world

    config = attempt_config(root, tmp_path, manifest_world(root, "plan"), "claude", review_access="full")
    config.update(review_access="full", review_cwd=str(root), claude_account="b",
                  review_claude_config_dir=spec.options["review_tool_config"]["review_claude_config_dir"])
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    record["review_attempt"]["manifest_sha256"] = store.digest(Path(config["review_manifest"]).read_bytes())
    record["review_access"] = "full"
    run_spec = worker._spec(record, {"review_tool_config": config})
    running = execution.Execution(run_spec, record, child_env(run_spec))
    try:
        assert running.boundary.env["CLAUDE_CODE_OAUTH_TOKEN"] == "fixture-bound-" + "b" * 30
        assert selected not in json.dumps(running.boundary.env)
    finally:
        running.cleanup()

    # Verdict-only reviews must pass the frozen label to the retained adapter too.
    seen = {}
    adapter = SimpleNamespace(build_invocation=lambda **kw: (seen.update(kw) or SimpleNamespace(
        cmd=["claude"], stdin_payload=None, env_overrides={}, env_unsets=(), output_file=None)))
    verdict_spec = worker._spec(record, {"require_review_verdict": "True"})
    execution.build_invocation(verdict_spec, child_env(verdict_spec), adapter)
    assert seen["tool_config"]["claude_account"] == "b"
