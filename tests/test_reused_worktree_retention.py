"""Creator ownership and fail-closed cohort release for #9934."""

import contextlib
import json
import os

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import post_task_reap as reap
from scripts.orchestration import worktree_claims as claims
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree


@pytest.fixture
def cohort(boundary_tree):
    repo, tree, tasks, creator = boundary_tree
    head = _git(tree, "rev-parse", "HEAD")
    creator.update(keep_worktree=True, worktree_branch="codex/boundary", pid=999_999_999)
    successor = dict(
        creator, task_id="successor", run_nonce="successor-run", worktree_reused=True, final_branch_head_commit=head
    )
    for record in (creator, successor):
        save(tasks, record)
    source = tree / "ignored/output.txt"
    source.parent.mkdir()
    source.write_bytes(b"current output")
    return repo, tree, tasks, creator, successor, source


def save(tasks, record):
    path = tasks / f"{record['task_id']}.json"
    path.write_text(json.dumps(record))
    return path


def retrieve(cohort):
    repo, tree, tasks, *_ = cohort
    ok, reason, receipt = output.preserve_worktree_artifacts(
        tree, primary=repo, tasks_dir=tasks, task_id=None, repo_root=repo
    )
    assert not ok and "keep_worktree" in reason
    assert receipt["owner"] == "boundary"
    assert receipt["content_sha256"] == receipt["retrieval_proof_sha256"]
    return receipt


def release(cohort, task_id="boundary", apply=True):
    repo, _, tasks, *_ = cohort
    return reap._release_retention(task_id, tasks_dir=tasks, repo_root=repo, apply=apply)


@pytest.mark.parametrize("cached", [False, True])
@pytest.mark.parametrize("creator_kept", [False, True])
def test_creator_attribution(cohort, cached, creator_kept):
    repo, tree, tasks, creator, _, _ = cohort
    creator["keep_worktree"] = creator_kept
    save(tasks, creator)
    for _ in range(2 if cached else 1):
        path, record = output.resolve_worktree_record(tree, tasks, repo_root=repo, publish_cache=cached)
        assert path == tasks / "boundary.json" and record == creator


@pytest.mark.parametrize("failure", ["two_creators", "branch", "path", "running", "unknown_reuse", "unknown_status"])
def test_ambiguous_cohort_refuses_attribution_and_release(cohort, failure):
    repo, tree, tasks, _, successor, _ = cohort
    if failure == "two_creators":
        successor["worktree_reused"] = False
    elif failure == "branch":
        successor["worktree_branch"] = "codex/other"
    elif failure == "path":
        other = repo / "other"
        other.mkdir()
        successor.update(worktree_path=str(other), cwd=str(tree))
    elif failure == "running":
        successor["status"] = "running"
    elif failure == "unknown_reuse":
        successor.pop("worktree_reused")
    else:
        successor.pop("status")
    save(tasks, successor)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    with pytest.raises(ValueError, match="ambiguous"):
        output.resolve_worktree_record(tree, tasks, repo_root=repo)
    assert release(cohort) is not None
    assert {p: p.read_bytes() for p in before} == before
    assert tree.exists()


def test_release_all_successors_under_locks_and_atomic_writes(cohort, monkeypatch):
    _, _, tasks, _, successor, _ = cohort
    save(tasks, dict(successor, task_id="second", run_nonce="second-run"))
    receipt = retrieve(cohort)
    events, held = [], set()
    wt_lock, task_lock, atomic = (
        claims.worktree_lock,
        output.artifacts.task_state_lock,
        reap.reaper_lifecycle._atomic_write,
    )

    @contextlib.contextmanager
    def worktree_lock(*args, **kwargs):
        with wt_lock(*args, **kwargs):
            held.add("worktree")
            events.append("worktree")
            yield
            held.remove("worktree")

    @contextlib.contextmanager
    def state_lock(path):
        assert "worktree" in held
        with task_lock(path):
            held.add(path)
            events.append(path.name)
            yield
            held.remove(path)

    def write(path, record):
        assert {"worktree", *(tasks / f"{task}.json" for task in ("boundary", "successor", "second"))} <= held
        events.append("write:" + path.name)
        atomic(path, record)

    monkeypatch.setattr(claims, "worktree_lock", worktree_lock)
    monkeypatch.setattr(output.artifacts, "task_state_lock", state_lock)
    monkeypatch.setattr(reap.reaper_lifecycle, "_atomic_write", write)
    assert release(cohort) is None
    assert events[0] == "worktree" and events[-1] == "write:boundary.json"
    for task in ("boundary", "successor", "second"):
        record = json.loads((tasks / f"{task}.json").read_text())
        assert record["keep_worktree"] is False
        proof = record["preserved_artifacts"]["retention_release"]
        assert proof == {
            "owner": "boundary",
            "run_nonce": "creation-nonce",
            "retrieval_proof_sha256": receipt["retrieval_proof_sha256"],
        }


@pytest.mark.parametrize(
    "failure", ["missing_receipt", "changed_bytes", "corrupt_copy", "wrong_nonce", "successor_owner", "dry_run"]
)
def test_release_requires_creator_and_current_retrieval(cohort, failure):
    repo, _, tasks, _, _, source = cohort
    receipt = retrieve(cohort)
    owner = json.loads((tasks / "boundary.json").read_text())
    if failure == "missing_receipt":
        owner.pop("preserved_artifacts")
    elif failure == "changed_bytes":
        source.write_bytes(b"changed output")
    elif failure == "corrupt_copy":
        (repo / receipt["location"] / "ignored/output.txt").write_bytes(b"bad")
    elif failure == "wrong_nonce":
        owner["run_nonce"] = "changed-run"
    save(tasks, owner)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    assert (
        release(cohort, task_id="successor" if failure == "successor_owner" else "boundary", apply=failure != "dry_run")
        is not None
    )
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize(
    "failure",
    [
        None,
        "no_merge",
        "wrong_merged_head",
        "wrong_current_head",
        "failed_successor",
        "live_creator",
        "live_successor",
        "missing_pid",
        "unknown_pid",
        "missing_head",
        "running_creator",
    ],
)
def test_needs_finalize_requires_exact_merged_successor_and_absent_workers(cohort, monkeypatch, failure):
    repo, tree, tasks, creator, successor, _ = cohort
    creator["status"] = "running" if failure == "running_creator" else "needs_finalize"
    if failure == "failed_successor":
        successor["status"] = "failed"
    elif failure == "wrong_current_head":
        successor["final_branch_head_commit"] = "1" * 40
    elif failure == "live_creator":
        creator["pid"] = os.getpid()
    elif failure == "live_successor":
        successor["pid"] = os.getpid()
    elif failure == "missing_pid":
        successor.pop("pid")
    elif failure == "missing_head":
        successor.pop("final_branch_head_commit")
    elif failure == "unknown_pid":
        monkeypatch.setattr(reap.reap_worktrees, "_pid_proven_absent", lambda _record: False)
    if failure == "no_merge":
        monkeypatch.setattr(reap.reap_worktrees, "_query_pr_states", lambda *_args: ([], None))
    elif failure == "wrong_merged_head":
        original = reap.reap_worktrees._query_pr_states

        def wrong_head(*args):
            states, error = original(*args)
            from dataclasses import replace

            return [replace(state, head_sha="1" * 40) for state in states], error

        monkeypatch.setattr(reap.reap_worktrees, "_query_pr_states", wrong_head)
    save(tasks, creator)
    save(tasks, successor)
    retrieve(cohort)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    refusal = release(cohort)
    if failure:
        assert refusal is not None
        assert {p: p.read_bytes() for p in before} == before
    else:
        assert refusal is None
        saved = json.loads((tasks / "boundary.json").read_text())
        assert saved["status"] == "needs_finalize" and saved["keep_worktree"] is False
        proof = saved["preserved_artifacts"]["retention_release"]["finalized_by"]
        assert proof == {
            "task_id": "successor",
            "run_nonce": "successor-run",
            "head_sha": _git(tree, "rev-parse", "HEAD"),
        }
        result = reap.post_task_reap("boundary", tasks_dir=tasks, repo_root=repo, apply=True, include_acp_runtime=False)
        assert result["main_worktree"]["action"] == "removed", result
        assert not tree.exists()


@pytest.mark.parametrize("creator_kept", [False, True])
def test_interrupted_release_retains_creator_and_retry_finishes(cohort, monkeypatch, creator_kept):
    _, _, tasks, creator, successor, _ = cohort
    creator["keep_worktree"] = creator_kept
    save(tasks, creator)
    save(tasks, dict(successor, task_id="second", run_nonce="second-run"))
    retrieve(cohort)
    atomic = reap.reaper_lifecycle._atomic_write

    def fail_owner(path, record):
        if path.name == "boundary.json" and record["keep_worktree"] is False:
            raise OSError("injected publication failure")
        atomic(path, record)

    monkeypatch.setattr(reap.reaper_lifecycle, "_atomic_write", fail_owner)
    assert release(cohort) is not None
    assert json.loads((tasks / "boundary.json").read_text())["keep_worktree"] is True
    monkeypatch.setattr(reap.reaper_lifecycle, "_atomic_write", atomic)
    assert release(cohort) is None
    assert all(not json.loads(p.read_text())["keep_worktree"] for p in tasks.glob("*.json"))


def test_record_change_during_lock_acquisition_refuses_without_writes(cohort, monkeypatch):
    _, _, tasks, _, successor, _ = cohort
    retrieve(cohort)
    lock = output.artifacts.task_state_lock

    @contextlib.contextmanager
    def change(path):
        with lock(path):
            if path.name == "successor.json":
                save(tasks, dict(successor, status="running"))
            yield

    monkeypatch.setattr(output.artifacts, "task_state_lock", change)
    assert release(cohort) is not None
    assert json.loads((tasks / "boundary.json").read_text())["keep_worktree"] is True


def test_successor_keep_intent_retains_creator_with_cleared_flag(cohort):
    _, tree, tasks, creator, _, _ = cohort
    creator["keep_worktree"] = False
    save(tasks, creator)
    receipt = retrieve(cohort)
    assert receipt["retention_disposition"] == "retained" and tree.exists()
    assert release(cohort) is None
    assert json.loads((tasks / "successor.json").read_text())["keep_worktree"] is False


def test_successor_ignored_output_is_retrieved_with_creator_output(cohort):
    _, tree, tasks, _, successor, _ = cohort
    named = tree / "ignored/report.txt"
    named.write_bytes(b"successor output")
    successor["response"] = "Output `ignored/report.txt`."
    save(tasks, successor)
    receipt = retrieve(cohort)
    assert {entry["path"] for entry in receipt["paths"]} == {"ignored/output.txt", "ignored/report.txt"}
    assert release(cohort) is None


def test_missing_successor_run_identity_refuses_before_writing(cohort):
    _, _, tasks, _, successor, _ = cohort
    retrieve(cohort)
    successor.pop("task_id")
    (tasks / "successor.json").write_text(json.dumps(successor))
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}
    assert release(cohort) == "retention release refused: task run identity unavailable"
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize(
    "failure",
    [
        "missing_record",
        "corrupt_record",
        "non_object",
        "wrong_id",
        "missing_nonce",
        "missing_path",
        "wrong_path",
        "bad_path",
        "unknown_status",
        "reused_owner",
    ],
)
def test_owner_release_guard_refuses_unproven_identity(cohort, failure, monkeypatch):
    repo, tree, tasks, creator, _, _ = cohort
    path = tasks / "boundary.json"
    if failure == "missing_record":
        path.unlink()
    elif failure == "corrupt_record":
        path.write_text("{")
    elif failure == "non_object":
        path.write_text("[]")
    else:
        if failure == "wrong_id":
            creator["task_id"] = "different"
        elif failure == "missing_nonce":
            creator.pop("run_nonce")
        elif failure == "missing_path":
            creator.pop("worktree_path")
        elif failure == "wrong_path":
            creator["worktree_path"] = str(repo)
        elif failure == "bad_path":

            def unresolved(*_args, **_kwargs):
                raise ValueError("unresolvable fixture path")

            monkeypatch.setattr(claims, "resolve_claim_path", unresolved)
        elif failure == "unknown_status":
            creator["status"] = []
        else:
            creator["worktree_reused"] = True
        path.write_text(json.dumps(creator))
    assert claims.owner_release_refusal(tree, owner_task_id="boundary", tasks_dir=tasks, repo_root=repo) is not None
    assert tree.exists()
