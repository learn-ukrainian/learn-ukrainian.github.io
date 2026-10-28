"""Creator ownership and fail-closed cohort attribution for #9934."""

import json

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import worktree_claims as claims
from tests.orchestration.test_worktree_artifacts import assert_record_only
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
    expected = {"ignored/output.txt": b"current output"}
    if (tree / "ignored/report.txt").exists():
        expected["ignored/report.txt"] = b"successor output"
    assert_record_only(receipt, expected)
    assert not (repo / "batch_state/preserved").exists()
    return receipt


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
def test_ambiguous_cohort_refuses_attribution(cohort, failure):
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
    assert {p: p.read_bytes() for p in before} == before
    assert tree.exists()


def test_successor_keep_intent_retains_creator(cohort):
    _, tree, tasks, creator, _, _ = cohort
    creator["keep_worktree"] = False
    save(tasks, creator)
    receipt = retrieve(cohort)
    assert receipt["retention_disposition"] == "retained" and tree.exists()


def test_successor_ignored_output_is_retrieved_with_creator_output(cohort):
    _, tree, tasks, _, successor, _ = cohort
    named = tree / "ignored/report.txt"
    named.write_bytes(b"successor output")
    successor["response"] = "Output `ignored/report.txt`."
    save(tasks, successor)
    receipt = retrieve(cohort)
    assert {entry["path"] for entry in receipt["paths"]} == {"ignored/output.txt", "ignored/report.txt"}


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
