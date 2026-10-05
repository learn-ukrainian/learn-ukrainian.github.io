"""Each formerly bypassing remover preserves real ignored bytes (#9645)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _acp_execution
from scripts.ci import data_tier
from scripts.fleet import ignored_task_output, sibling_git
from scripts.orchestration import worktree_claims
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.orchestration.task_family import git_safety
from tests.orchestration.test_worktree_claims_cli import _git, _linked, _primary, _record

CALLERS = ["acp", "data-tier", "sibling", "task-family", "cli"]


def remove(caller, primary, checkout, capsys, monkeypatch):
    if caller == "acp":
        return (
            _acp_execution._remove_runtime_worktree(
                primary,
                checkout,
                owner_task_id="done-output",
                reason="ACP teardown",
                dirty_probe=_acp_execution._own_runtime_is_scratch,
            ).action
            == "removed"
        )
    if caller == "data-tier":
        try:
            data_tier.remove_test_worktree(primary, checkout)
        except data_tier.DataTierError as exc:
            assert "artifact preservation failed:" in str(exc)
            return False
        return True
    if caller == "task-family":
        try:
            git_safety.remove_unclaimed_worktree(primary, checkout)
        except git_safety.GitSafetyError as exc:
            assert "artifact preservation failed:" in str(exc)
            return False
        return True
    if caller == "sibling":
        public = primary.parent / "public"
        public.mkdir()
        _git(public, "init", "-b", "main")
        record = primary / "batch_state/tasks/done-output.json"
        if record.exists():
            public_tasks = public / "batch_state/tasks"
            public_tasks.mkdir(parents=True)
            (public_tasks / record.name).write_bytes(record.read_bytes())
        # Real independent metadata and the already-established dispatch lock.
        with worktree_claims.worktree_lock(checkout, lock_dir=public / ".git" / worktree_claims.LOCK_DIR_NAME):
            pass
        monkeypatch.setattr(
            sibling_git,
            "load_fleet_repos",
            lambda: {"fixture": FleetRepo("fixture", "fixture/sibling", primary.name, "private")},
        )
        monkeypatch.setattr(sibling_git, "_registry_transport", lambda _key: "ssh")
        _git(primary, "remote", "add", "origin", "git@github.com:fixture/sibling.git")
        with sibling_git.git_session() as git:
            repo = sibling_git.resolve_repository("fixture", public, git)
            try:
                sibling_git.worktree_remove(repo, public, git, str(checkout))
            except sibling_git.Refusal as exc:
                assert "local work preserved" in str(exc)
                return False
        return True
    code = worktree_claims.main(["remove", str(checkout), "--json"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    if code == worktree_claims.EXIT_REMOVED:
        assert "Preserved " in captured.err
    else:
        assert "artifact preservation failed:" in captured.err
    if code != worktree_claims.EXIT_REMOVED:
        assert result["action"] == "skipped"
        assert "artifact preservation failed:" in result["reason"]
    return code == worktree_claims.EXIT_REMOVED


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("failure", [None, "cap", "copy"])
@pytest.mark.parametrize("record_exists", [True, False])
def test_all_removers_preserve_output_or_retain_checkout(tmp_path, monkeypatch, capsys, caller, failure, record_exists):
    primary = _primary(tmp_path)
    # Exclude via shared Git metadata, covering no-checkout ACP runtimes too.
    with (primary / ".git/info/exclude").open("a") as handle:
        handle.write(".cache/\n")
    checkout = _linked(primary, "codex/done-output")
    payload = b"new ignored transcription\n"
    source = checkout / ".cache/transcriptions/page.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    if record_exists:
        _record(primary, "done-output", status="done", worktree_path=str(checkout), started_at="2000-01-01T00:00:00Z")
    assert _git(checkout, "status", "--porcelain") == ""
    if failure == "cap":
        monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", len(payload) - 1)
    if failure == "copy":

        def fail_copy(*_args):
            raise OSError("copy denied")

        monkeypatch.setattr(ignored_task_output.artifacts, "_copy_verified", fail_copy)

    calls = []
    original = ignored_task_output.preserve_worktree_artifacts

    def preserve_once(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", preserve_once)
    removed = remove(caller, primary, checkout, capsys, monkeypatch)
    assert calls == [checkout]
    if failure or not record_exists:
        assert not removed and checkout.exists()
        assert source.read_bytes() == payload
        return
    assert removed and not checkout.exists()
    destination = primary.parent / "public" if caller == "sibling" else primary
    copies = list((destination / "batch_state/preserved").glob("*/*/.cache/transcriptions/page.txt"))
    assert len(copies) == 1
    assert copies[0].read_bytes() == payload
    assert hashlib.sha256(copies[0].read_bytes()).digest() == hashlib.sha256(payload).digest()


def test_active_claim_prevents_preservation_and_removal(tmp_path, monkeypatch):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/active")
    _record(primary, "active", status="running", worktree_path=str(checkout))

    def forbidden(*_args, **_kwargs):
        pytest.fail("preservation ran before active-claim refusal")

    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", forbidden)
    result = worktree_claims.remove_unclaimed_worktree(
        checkout,
        repo_root=primary,
        reason="test",
        owner_task_id=None,
    )
    assert result.action == "skipped" and checkout.exists()
    assert "active task" in result.reason


def test_raw_removal_checks_preservation_without_adapter(tmp_path, monkeypatch):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/raw")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"raw remover output")
    _record(primary, "raw", status="done", worktree_path=str(checkout))
    receipt = {}
    with worktree_claims.worktree_lock(checkout, lock_dir=worktree_claims.repository_lock_dir(primary)):
        error = worktree_claims.git_worktree_remove(
            primary,
            checkout,
            force=True,
            preservation_receipt=receipt,
        )
    assert error is None and not checkout.exists()
    assert ((primary / receipt["location"]) / ".cache/report.txt").read_bytes() == b"raw remover output"
    assert receipt["retrieval_proof_sha256"] == receipt["content_sha256"]


@pytest.mark.parametrize("changed", [True, False])
def test_retry_after_git_refusal_reuses_identical_or_preserves_changed_output(tmp_path, changed):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/retry-9645")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"first")
    _record(primary, "retry-9645", status="done", worktree_path=str(checkout))
    first, second = {}, {}
    with worktree_claims.worktree_lock(checkout, lock_dir=worktree_claims.repository_lock_dir(primary)):
        error = worktree_claims.git_worktree_remove(
            primary,
            checkout,
            force=False,
            preservation_receipt=first,
            git_runner=lambda _root, argv: subprocess.CompletedProcess(argv, 1, "", "injected Git refusal"),
        )
        assert error and checkout.exists()
        if changed:
            source.write_bytes(b"second")
        error = worktree_claims.git_worktree_remove(
            primary,
            checkout,
            force=False,
            preservation_receipt=second,
        )
    assert error is None and not checkout.exists()
    assert (first["location"] != second["location"]) is changed
    assert second["reused"] is not changed
    assert ((primary / first["location"]) / ".cache/report.txt").read_bytes() == b"first"
    assert ((primary / second["location"]) / ".cache/report.txt").read_bytes() == (b"second" if changed else b"first")


def test_claims_remove_preserves_old_output_when_task_id_was_redispatched(tmp_path, monkeypatch, capsys):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/redispatched")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/out/page.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"old task output")
    other = primary / ".worktrees/dispatch/claude/redispatched"
    other.mkdir(parents=True)
    _record(primary, "redispatched", status="done", worktree_path=str(other), started_at="2999-01-01T00:00:00Z")
    record_path = primary / "batch_state/tasks/redispatched.json"
    before = record_path.read_bytes()
    monkeypatch.setenv("LU_TASKS_DIR", str(record_path.parent))
    assert worktree_claims.main(["remove", str(checkout), "--json"]) == worktree_claims.EXIT_REFUSED
    assert checkout.exists() and record_path.read_bytes() == before
    assert source.read_bytes() == b"old task output"
    result = json.loads(capsys.readouterr().out)
    assert result["action"] == "skipped"
    assert result["preserved_artifacts"]["owner"] == "infra lane"
    assert result["preserved_artifacts"]["next_condition"]
    assert not (primary / "batch_state/preserved").exists()


def test_claims_remove_preserves_earlier_attempt_output_in_reused_checkout(tmp_path, monkeypatch, capsys):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/reused-output")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/out/page.txt"
    source.parent.mkdir(parents=True)
    payload = b"earlier attempt output"
    source.write_bytes(payload)
    # Same id and checkout, but the re-dispatch replaces the creating record
    # with a later start. Both file clocks precede that start in the reproduction.
    later_start = max(source.stat().st_mtime, source.stat().st_ctime) + 2
    _record(
        primary,
        "reused-output",
        status="done",
        worktree_path=str(checkout),
        worktree_reused=True,
        started_at=datetime.fromtimestamp(later_start, UTC).isoformat(),
    )
    record_path = primary / "batch_state/tasks/reused-output.json"
    monkeypatch.setenv("LU_TASKS_DIR", str(record_path.parent))
    assert _git(checkout, "status", "--porcelain") == ""
    assert worktree_claims.main(["remove", str(checkout), "--json"]) == worktree_claims.EXIT_REMOVED
    result = json.loads(capsys.readouterr().out)
    assert result["action"] == "removed" and not checkout.exists()
    receipt = json.loads(record_path.read_text())["preserved_artifacts"]
    assert receipt["count"] == 1 and receipt["bytes"] == len(payload)
    assert result["preserved_artifacts"] == receipt
    assert ((primary / receipt["location"]) / ".cache/out/page.txt").read_bytes() == payload


# These fixtures execute production removal callers against disposable Git
# repositories. External PR/liveness observations are controlled; Git removal,
# inventory, copying, retrieval and task record writes are real.
BOUNDARIES = ["claims", "claims-force", "scheduled", "closeout", "post-task", "delegate", "delegate-force"]


@pytest.fixture
def boundary_tree(tmp_path, monkeypatch):
    from scripts.fleet import post_task_reap
    from tests.orchestration import test_merge_closeout as closeout

    repo = closeout.init_repo(tmp_path)
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write("ignored/\n.cache/\n.pytest_cache/\n.venv/\nnode_modules/\nbatch_state/\n")
    tree = repo / ".worktrees/dispatch/codex/boundary"
    tree.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "-b", "codex/boundary", str(tree), "main")
    _git(tree, "push", "-u", "origin", "codex/boundary")
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    monkeypatch.setenv("LU_TASKS_DIR", str(tasks))
    monkeypatch.setattr(post_task_reap, "_DISPATCH_WORKTREES_ROOT", repo / ".worktrees/dispatch")
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_live_cwd_paths", lambda _repo: set())
    monkeypatch.setattr(post_task_reap.reap_worktrees, "_active_task_ids", lambda: set())
    head = _git(tree, "rev-parse", "HEAD")
    closeout.patch_gh(
        monkeypatch,
        pr_number=9645,
        state="MERGED",
        head_ref_name="codex/boundary",
        head_sha=head,
        branch_prs={"codex/boundary": [{"number": 9645, "state": "MERGED", "headRefOid": head}]},
    )
    record = {
        "task_id": "boundary",
        "agent": "codex",
        "run_nonce": "creation-nonce",
        "status": "done",
        "worktree_reused": False,
        "worktree_path": str(tree),
        "keep_worktree": False,
    }
    (tasks / "boundary.json").write_text(json.dumps(record))
    return repo, tree, tasks, record


def boundary_remove(boundary, fixture, monkeypatch):
    from scripts import delegate
    from scripts.fleet import post_task_reap
    from scripts.orchestration import merge_closeout, reap_worktrees

    repo, tree, tasks, _record = fixture
    if boundary.startswith("claims"):
        return worktree_claims.remove_unclaimed_worktree(
            tree,
            repo_root=repo,
            reason="fixture",
            owner_task_id=None,
            force=boundary.endswith("force"),
        ).as_record()
    if boundary.startswith("delegate"):
        monkeypatch.setattr(delegate, "_REPO_ROOT", repo)
        monkeypatch.setattr(delegate, "tasks_dir", lambda: tasks)
        return delegate._remove_dispatch_worktree(
            tree,
            reason="fixture",
            owner_task_id=None,
            releasable=lambda: (True, "fixture"),
            force=boundary.endswith("force"),
        )
    if boundary == "scheduled":
        results = reap_worktrees.reap_worktrees(repo_root=repo, apply=True, live_cwds=set())
        return next(result for result in results if Path(result.path) == tree).__dict__
    if boundary == "closeout":
        return merge_closeout.run_merge_closeout(repo, 9645, apply=True, live_cwds=set()).reap_results[0]
    return post_task_reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True)["main_worktree"]


@pytest.mark.parametrize("boundary", BOUNDARIES)
@pytest.mark.parametrize(
    "scenario",
    [
        "transcript",
        "pre_existing",
        "modified",
        "cache",
        "missing_attribution",
        "missing_baseline",
        "oversized",
        "copy",
        "retrieval",
        "keep",
        "real_environment",
    ],
)
def test_actual_boundaries_preserve_or_retain(boundary_tree, monkeypatch, boundary, scenario):
    repo, tree, tasks, record = boundary_tree
    name = (
        ".pytest_cache/cache.bin"
        if scenario == "cache"
        else ("node_modules/work/report.jsonl" if scenario == "real_environment" else "ignored/deep/transcript.md")
    )
    source = tree / name
    payload = b"source-backed corpus bytes\x00\xff"
    if scenario in {"pre_existing", "modified"}:
        source.parent.mkdir(parents=True)
        source.write_bytes(payload)
    with worktree_claims.worktree_lock(tree, lock_dir=worktree_claims.repository_lock_dir(repo)):
        record["ignored_output_baseline"] = ignored_task_output.creation_inventory(
            tree,
            primary=repo,
            task_id="boundary",
            run_nonce=record["run_nonce"],
        )
    source.parent.mkdir(parents=True, exist_ok=True)
    if scenario == "modified":
        payload += b" modified"
    source.write_bytes(payload)
    if scenario == "missing_baseline":
        record.pop("ignored_output_baseline")
    record["keep_worktree"] = scenario == "keep"
    if scenario != "missing_attribution":
        (tasks / "boundary.json").write_text(json.dumps(record))
    else:
        (tasks / "boundary.json").unlink()
    if scenario == "oversized":
        monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", len(payload) - 1)
    elif scenario == "copy":
        monkeypatch.setattr(
            ignored_task_output.artifacts,
            "_copy_verified",
            lambda *_args: (_ for _ in ()).throw(OSError("injected copy failure")),
        )
    elif scenario == "retrieval":
        monkeypatch.setattr(
            ignored_task_output,
            "verify_retrieval",
            lambda *_args: (_ for _ in ()).throw(ValueError("injected retrieval failure")),
        )
    assert _git(tree, "status", "--porcelain") == ""
    result = boundary_remove(boundary, boundary_tree, monkeypatch)
    retained = scenario in {"missing_attribution", "oversized", "copy", "retrieval", "keep"}
    assert tree.exists() is retained, result
    receipt = result.get("preserved_artifacts")
    if retained:
        assert result["action"] in {"skipped", "retained"}, result
        assert source.read_bytes() == payload
        assert receipt["retention_disposition"] == "retained"
        assert receipt["owner"] and receipt["next_condition"] != "none"
    else:
        assert result["action"] == "removed", result
        if scenario == "cache":
            assert receipt is None
            assert not (repo / "batch_state/preserved").exists()
            return
        retrieved = repo / receipt["location"] / name
        assert hashlib.sha256(retrieved.read_bytes()).hexdigest() == hashlib.sha256(payload).hexdigest()
        assert receipt["retrieval_proof_sha256"] == ignored_task_output.verify_retrieval(repo, receipt)
        expected = (
            "pre_existing"
            if scenario == "pre_existing"
            else ("unknown_baseline" if scenario == "missing_baseline" else "task_created")
        )
        assert receipt["paths"][0]["class"] == expected
    assert str(repo) not in json.dumps(receipt)
    assert str(tree) not in json.dumps(receipt)


@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_existing_owner_release_after_retrieval_allows_removal(boundary_tree, monkeypatch, boundary):
    from scripts.fleet import post_task_reap

    repo, tree, tasks, record = boundary_tree
    source = tree / "ignored/corpus.yaml"
    source.parent.mkdir()
    source.write_bytes(b"retrieved corpus bytes")
    record["keep_worktree"] = True
    (tasks / "boundary.json").write_text(json.dumps(record))
    # Release cannot manufacture a passing receipt.
    refusal = post_task_reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True)
    assert "existing passing retrieval receipt" in refusal
    first = boundary_remove(boundary, boundary_tree, monkeypatch)
    assert first["action"] in {"retained", "skipped"} and tree.exists()
    saved = json.loads((tasks / "boundary.json").read_text())
    receipt = saved["preserved_artifacts"]
    assert (
        hashlib.sha256((repo / receipt["location"] / "ignored/corpus.yaml").read_bytes()).hexdigest()
        == hashlib.sha256(source.read_bytes()).hexdigest()
    )
    assert post_task_reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    released = json.loads((tasks / "boundary.json").read_text())
    assert released["keep_worktree"] is False
    assert released["preserved_artifacts"]["retention_release"]["owner"] == "boundary"
    result = boundary_remove(boundary, boundary_tree, monkeypatch)
    assert result["action"] == "removed" and not tree.exists(), result
    assert (
        result["preserved_artifacts"]["retention_release"]["retrieval_proof_sha256"]
        == receipt["retrieval_proof_sha256"]
    )


@pytest.mark.parametrize("caller", CALLERS)
def test_callers_without_record_argument_honor_keep_intent(tmp_path, monkeypatch, capsys, caller):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/done-output")
    _record(primary, "done-output", status="done", worktree_path=str(checkout), keep_worktree=True)
    # Non-forced Git removal would succeed even for this ignored file.
    (primary / ".git/info/exclude").write_text("ignored/\n")
    source = checkout / "ignored/corpus.txt"
    source.parent.mkdir()
    source.write_bytes(b"only corpus copy")
    assert _git(checkout, "status", "--porcelain") == ""
    assert remove(caller, primary, checkout, capsys, monkeypatch) is False
    assert checkout.exists() and source.read_bytes() == b"only corpus copy"


@pytest.mark.parametrize("suffix", ["md", "txt", "json", "jsonl", "yaml"])
@pytest.mark.parametrize(
    "parent", ["ignored", "ignored/deep/more", ".cache/transcripts", ".venv/cache", "node_modules/corpus"]
)
def test_transcript_extensions_outside_disposable_directories_are_output(boundary_tree, suffix, parent):
    repo, tree, tasks, record = boundary_tree
    source = tree / parent / ("corpus." + suffix)
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"unique output")
    assert not ignored_task_output.artifacts.is_disposable_path(source.relative_to(tree), worktree=tree, primary=repo)
    record["ignored_output_baseline"] = None
    (tasks / "boundary.json").write_text(json.dumps(record))
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "removed"
    receipt = result.preserved_artifacts
    assert receipt["paths"][0]["class"] == "unknown_baseline"
    assert (
        hashlib.sha256((repo / receipt["location"] / source.relative_to(tree)).read_bytes()).hexdigest()
        == hashlib.sha256(b"unique output").hexdigest()
    )


@pytest.mark.parametrize("failure", [None, "corrupt_copy", "changed_source", "reused", "wrong_nonce", "dry_run"])
def test_post_task_release_cli_requires_owner_and_current_retrieval(boundary_tree, monkeypatch, capsys, failure):
    from scripts.fleet import post_task_reap

    repo, tree, tasks, record = boundary_tree
    source = tree / "ignored/output.json"
    source.parent.mkdir()
    source.write_bytes(b"retrieval proof bytes")
    record["keep_worktree"] = True
    (tasks / "boundary.json").write_text(json.dumps(record))
    result = boundary_remove("scheduled", boundary_tree, monkeypatch)
    assert result["action"] == "skipped" and tree.exists()
    saved = json.loads((tasks / "boundary.json").read_text())
    receipt = saved["preserved_artifacts"]
    if failure == "corrupt_copy":
        (repo / receipt["location"] / "ignored/output.json").write_bytes(b"corrupt retrieval")
    elif failure == "changed_source":
        source.write_bytes(b"new unretrieved output")
    elif failure == "reused":
        saved["worktree_reused"] = True
    elif failure == "wrong_nonce":
        saved["run_nonce"] = "other-owner-run"
    (tasks / "boundary.json").write_text(json.dumps(saved))
    argv = ["--task-id", "boundary", "--tasks-dir", str(tasks), "--repo-root", str(repo), "--release-retention"]
    if failure != "dry_run":
        argv += ["--apply"]
    code = post_task_reap.main(argv)
    report = json.loads(capsys.readouterr().out)
    state = json.loads((tasks / "boundary.json").read_text())
    if failure is None:
        assert code == 0 and report["main_worktree"]["action"] == "removed", report
        assert not tree.exists() and state["keep_worktree"] is False
        assert (
            state["preserved_artifacts"]["retention_release"]["retrieval_proof_sha256"]
            == receipt["retrieval_proof_sha256"]
        )
        assert (
            hashlib.sha256((repo / receipt["location"] / "ignored/output.json").read_bytes()).hexdigest()
            == hashlib.sha256(b"retrieval proof bytes").hexdigest()
        )
    else:
        assert code == 1 and report["main_worktree"]["action"] == "retained"
        assert tree.exists() and state["keep_worktree"] is True
        assert "retention_release" not in state["preserved_artifacts"]


@pytest.mark.parametrize("untrusted", ["reused", "wrong_nonce", "wrong_inode", "malformed"])
def test_untrusted_creation_inventory_never_shrinks_preservation(boundary_tree, untrusted):
    repo, tree, tasks, record = boundary_tree
    source = tree / "ignored/preexisting.txt"
    source.parent.mkdir()
    source.write_bytes(b"old corpus bytes")
    with worktree_claims.worktree_lock(tree, lock_dir=worktree_claims.repository_lock_dir(repo)):
        record["ignored_output_baseline"] = ignored_task_output.creation_inventory(
            tree, primary=repo, task_id="boundary", run_nonce=record["run_nonce"]
        )
    if untrusted == "reused":
        record["worktree_reused"] = True
    elif untrusted == "wrong_nonce":
        record["ignored_output_baseline"]["run_nonce"] = "old"
    elif untrusted == "wrong_inode":
        record["ignored_output_baseline"]["directory_identity"] = [0, 0]
    else:
        record["ignored_output_baseline"]["paths"] = [{"path": "ignored/preexisting.txt"}]
    (tasks / "boundary.json").write_text(json.dumps(record))
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "removed"
    receipt = result.preserved_artifacts
    assert receipt["paths"][0]["class"] == "unknown_baseline"
    assert (repo / receipt["location"] / "ignored/preexisting.txt").read_bytes() == b"old corpus bytes"


def test_empty_kept_tree_still_requires_explicit_retrieved_owner_release(boundary_tree, monkeypatch):
    from scripts.fleet import post_task_reap

    repo, tree, tasks, record = boundary_tree
    record["keep_worktree"] = True
    (tasks / "boundary.json").write_text(json.dumps(record))
    first = boundary_remove("claims", boundary_tree, monkeypatch)
    assert first["action"] == "skipped" and tree.exists()
    assert first["preserved_artifacts"]["count"] == 0
    assert first["preserved_artifacts"]["retrieval_proof_sha256"]
    assert post_task_reap._release_retention("boundary", tasks_dir=tasks, repo_root=repo, apply=True) is None
    result = boundary_remove("claims", boundary_tree, monkeypatch)
    assert result["action"] == "removed" and not tree.exists()


@pytest.mark.parametrize("name", ["__pycache__", ".pytest_cache", ".entire/logs"])
def test_regular_files_with_cache_directory_names_are_preserved(boundary_tree, name):
    repo, tree, tasks, record = boundary_tree
    with (repo / ".git/info/exclude").open("a") as exclude:
        exclude.write(name + "\n")
    source = tree / name
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"only transcript copy")
    (tasks / "boundary.json").write_text(json.dumps(record))
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "removed"
    receipt = result.preserved_artifacts
    assert (repo / receipt["location"] / name).read_bytes() == b"only transcript copy"


@pytest.mark.parametrize("ambiguous", [False, True])
def test_retention_in_finished_reference_cannot_be_hidden_by_newer_record(boundary_tree, ambiguous):
    repo, tree, tasks, record = boundary_tree
    record["keep_worktree"] = ambiguous
    (tasks / "boundary.json").write_text(json.dumps(record))
    keeper = {"task_id": "original-owner", "status": "done", "keep_worktree": True, "worktree_path": str(tree)}
    (tasks / "original-owner.json").write_text(json.dumps(keeper))
    source = tree / "ignored/corpus.txt"
    source.parent.mkdir()
    source.write_bytes(b"retained corpus")
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "skipped" and tree.exists()
    assert source.read_bytes() == b"retained corpus"
    assert result.preserved_artifacts["retention_disposition"] == "retained"
    assert result.preserved_artifacts["owner"] and result.preserved_artifacts["next_condition"]


def test_ambiguous_non_kept_output_retains_unknown_attribution(boundary_tree):
    repo, tree, tasks, record = boundary_tree
    record.pop("worktree_reused")
    (tasks / "boundary.json").write_text(json.dumps(record))
    (tasks / "other.json").write_text(json.dumps({"task_id": "other", "status": "done", "worktree_path": str(tree)}))
    source = tree / "ignored/output.md"
    source.parent.mkdir()
    source.write_bytes(b"unknown owner")
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "skipped" and tree.exists()
    assert result.preserved_artifacts["owner"] == "infra lane"
    assert result.preserved_artifacts["next_condition"]
    assert not (repo / "batch_state/preserved").exists()


def test_malformed_worktree_field_cannot_hide_cwd_bound_retention(boundary_tree):
    repo, tree, tasks, record = boundary_tree
    record.update({"worktree_path": 7, "cwd": str(tree), "keep_worktree": True})
    (tasks / "boundary.json").write_text(json.dumps(record))
    with worktree_claims.worktree_lock(tree, lock_dir=worktree_claims.repository_lock_dir(repo)):
        error = worktree_claims.git_worktree_remove(repo, tree, force=False)
    assert "ambiguous retention task binding" in error
    assert tree.exists()
    assert json.loads((tasks / "boundary.json").read_text())["keep_worktree"] is True


@pytest.mark.parametrize("spelling", ["relative", "tilde"])
@pytest.mark.parametrize("field", ["worktree_path", "cwd"])
@pytest.mark.parametrize("archived", [False, True], ids=["hot", "archive"])
@pytest.mark.parametrize("has_output", [False, True], ids=["empty", "output"])
def test_kept_record_path_spellings_refuse_removal(boundary_tree, monkeypatch, spelling, field, archived, has_output):
    repo, tree, tasks, record = boundary_tree
    monkeypatch.setenv("HOME", str(repo.parent))
    # Neither matching nor receipt publication may depend on the caller's cwd.
    monkeypatch.chdir(tree)
    location = (
        tree.relative_to(repo).as_posix() if spelling == "relative" else "~/" + tree.relative_to(repo.parent).as_posix()
    )
    record.pop("worktree_path")
    record.update({field: location, "keep_worktree": True})
    path = tasks / "boundary.json"
    if archived:
        path.unlink()
        path = tasks / "archive/boundary.json"
        path.parent.mkdir()
    path.write_text(json.dumps(record))
    source = tree / "ignored/output.txt"
    if has_output:
        source.parent.mkdir()
        source.write_bytes(b"retained output")
    assert _git(tree, "status", "--porcelain") == ""
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "skipped" and tree.exists()
    assert "keep_worktree intent set" in result.reason
    receipt = result.preserved_artifacts
    assert receipt["owner"] == "boundary" and receipt["count"] == int(has_output)
    assert receipt["retention_disposition"] == "retained"
    assert receipt["retrieval_proof_sha256"] == ignored_task_output.verify_retrieval(repo, receipt)
    assert json.loads(path.read_text())["preserved_artifacts"] == receipt
    if has_output:
        assert (repo / receipt["location"] / "ignored/output.txt").read_bytes() == source.read_bytes()


@pytest.mark.parametrize("spelling", ["relative", "tilde"])
@pytest.mark.parametrize("has_output", [False, True], ids=["empty", "output"])
def test_release_retention_cli_matches_record_path_spellings(boundary_tree, monkeypatch, capsys, spelling, has_output):
    from scripts.fleet import post_task_reap

    repo, tree, tasks, record = boundary_tree
    monkeypatch.setenv("HOME", str(repo.parent))
    # The real CLI must remove the tree after release from an unrelated cwd.
    monkeypatch.chdir(repo.parent)
    location = (
        tree.relative_to(repo).as_posix() if spelling == "relative" else "~/" + tree.relative_to(repo.parent).as_posix()
    )
    record.update({"worktree_path": location, "keep_worktree": True})
    path = tasks / "boundary.json"
    path.write_text(json.dumps(record))
    if has_output:
        source = tree / "ignored/output.txt"
        source.parent.mkdir()
        source.write_bytes(b"released output")
    first = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert first.action == "skipped" and tree.exists()
    receipt = first.preserved_artifacts
    argv = [
        "--task-id",
        "boundary",
        "--tasks-dir",
        str(tasks),
        "--repo-root",
        str(repo),
        "--release-retention",
        "--apply",
    ]
    assert post_task_reap.main(argv) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["main_worktree"]["action"] == "removed", report
    assert not tree.exists()
    saved = json.loads(path.read_text())
    assert saved["keep_worktree"] is False
    release = saved["preserved_artifacts"]["retention_release"]
    assert release["owner"] == "boundary"
    assert release["retrieval_proof_sha256"] == receipt["retrieval_proof_sha256"]
    assert ignored_task_output.verify_retrieval(repo, receipt) == receipt["retrieval_proof_sha256"]
    if has_output:
        assert (repo / receipt["location"] / "ignored/output.txt").read_bytes() == b"released output"


@pytest.mark.parametrize("spelling", ["relative", "tilde"])
def test_record_path_spellings_publish_copy_failure(boundary_tree, monkeypatch, spelling):
    repo, tree, tasks, record = boundary_tree
    monkeypatch.setenv("HOME", str(repo.parent))
    monkeypatch.chdir(tree)
    location = (
        tree.relative_to(repo).as_posix() if spelling == "relative" else "~/" + tree.relative_to(repo.parent).as_posix()
    )
    record.update({"worktree_path": location, "keep_worktree": True})
    path = tasks / "boundary.json"
    path.write_text(json.dumps(record))
    source = tree / "ignored/output.txt"
    source.parent.mkdir()
    source.write_bytes(b"uncopied output")

    def fail_copy(*_args):
        raise OSError("injected copy failure")

    monkeypatch.setattr(ignored_task_output.artifacts, "_copy_verified", fail_copy)
    result = worktree_claims.remove_unclaimed_worktree(tree, repo_root=repo, reason="fixture", owner_task_id=None)
    assert result.action == "skipped" and tree.exists()
    saved = json.loads(path.read_text())
    assert "injected copy failure" in saved["artifact_preservation_error"]
    assert saved["keep_worktree"] is True
    assert saved["preserved_artifacts"] == result.preserved_artifacts
    assert result.preserved_artifacts["owner"] == "boundary"
    assert source.read_bytes() == b"uncopied output"
