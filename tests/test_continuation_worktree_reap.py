"""Continuation cohorts from #10008, using disposable records and Git trees.

The cohort fixtures here are shared by the ignored-output and terminal-abandon
suites; the tests cover creator attribution for reused checkouts.
"""

import hashlib
import json
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import worktree_claims as claims
from scripts.orchestration import worktree_git as wg
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


@pytest.fixture
def earlier_cohort(cohort, monkeypatch):
    """Three real commits: creator, settled successor, and later reviewed PR head."""
    from tests.orchestration.test_merge_closeout import git, patch_gh

    repo, tree, tasks, creator, successor, source = cohort
    creator.update(
        keep_worktree=False, status="needs_finalize", final_branch_head_commit=_git(tree, "rev-parse", "HEAD")
    )
    _git(tree, "commit", "--allow-empty", "-m", "successor")
    head = _git(tree, "rev-parse", "HEAD")
    successor.update(keep_worktree=False, final_branch_head_commit=head)
    _git(tree, "commit", "--allow-empty", "-m", "review fixes")
    reviewed = _git(tree, "rev-parse", "HEAD")
    _git(tree, "push", "origin", "codex/boundary")
    _git(repo, "merge", "--no-ff", "codex/boundary", "-m", "merge reviewed PR")
    git(repo, "push", "origin", "main")
    _git(tree, "checkout", "--detach", head)
    for record in (creator, successor):
        save(tasks, record)
    patch_gh(
        monkeypatch,
        pr_number=9645,
        state="MERGED",
        head_ref_name="codex/boundary",
        head_sha=reviewed,
        branch_prs={"codex/boundary": [{"number": 9645, "state": "MERGED", "headRefOid": reviewed}]},
    )
    return repo, tree, tasks, creator, successor, source, reviewed


@pytest.mark.parametrize("probe", [None, "error", "empty", "attached"])
def test_detached_attribution_requires_positive_branch_probe(earlier_cohort, monkeypatch, probe):
    import subprocess

    repo, tree, tasks, *_ = earlier_cohort
    result = (
        None
        if probe is None
        else subprocess.CompletedProcess(
            [], 128 if probe == "error" else 0, "codex/boundary" if probe == "attached" else "", ""
        )
    )
    monkeypatch.setattr(claims, "checked_out_branch", lambda _tree: None)
    monkeypatch.setattr(claims, "_git_probe", lambda *_args, **_kwargs: result)
    with pytest.raises(ValueError, match="ambiguous"):
        output.reused_worktree_creator(
            output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False),
            tree,
            repo_root=repo,
            tasks_dir=tasks,
        )


@pytest.mark.parametrize("failure", ["ordinary_archive", "no_replacement", "same_nonce", "active", "missing_nonce"])
def test_unproven_archive_stays_ambiguous(cohort, failure):
    repo, tree, tasks, _, successor, _ = cohort
    archive = tasks / "successor.20261007T130120593046Z.archived.json"
    old = dict(successor, worktree_reused=False, status="failed", run_nonce="old-run")
    if failure == "ordinary_archive":
        archive = tasks / "archive/successor.json"
        archive.parent.mkdir()
    elif failure == "no_replacement":
        old["task_id"] = "other"
        archive = tasks / "other.20261007T130120593046Z.archived.json"
    elif failure == "same_nonce":
        old["run_nonce"] = successor["run_nonce"]
    elif failure == "active":
        old["status"] = "running"
    else:
        old.pop("run_nonce")
    archive.write_text(json.dumps(old))
    with pytest.raises(ValueError, match="ambiguous"):
        output.resolve_worktree_record(tree, tasks, repo_root=repo)


@pytest.mark.parametrize("created_evidence", [False, True])
def test_failed_preparation_without_no_checkout_proof_stays_ambiguous(cohort, created_evidence):
    repo, tree, tasks, _, _, source = cohort
    record = {
        "task_id": "failed-validation",
        "run_nonce": "validation-run",
        "status": "failed",
        "last_error": "worktree_preparation_failed",
        "returncode_reason": "worktree preparation failed",
        "worktree_path": str(tree),
        "worktree_reused": False,
        "keep_worktree": True,
        "pid": None,
        "worktree_base_sha": None,
        "worktree_branch": None,
        # The failure writer snapshots existing HEAD too; this is not creation proof.
        "final_branch_head_commit": _git(tree, "rev-parse", "HEAD"),
    }
    if created_evidence:
        record.update(
            worktree_base_sha=record["final_branch_head_commit"],
            worktree_branch="codex/boundary",
            worktree_prep={"reserved_by_mkdir": True, "git_pid": 999_999_999},
        )
    save(tasks, record)
    with pytest.raises(ValueError, match="ambiguous"):
        output.resolve_worktree_record(tree, tasks, repo_root=repo)
    assert tree.exists() and source.read_bytes() == b"current output"
    assert json.loads((tasks / "failed-validation.json").read_text()) == record


@pytest.fixture
def same_branch_pending_cohort(cohort):
    repo, tree, tasks, creator, successor, source = cohort
    head = _git(tree, "rev-parse", "HEAD")
    for member in (creator, successor):
        member.update(keep_worktree=False, status="needs_finalize", final_branch_head_commit=head)
        save(tasks, member)
    return repo, tree, tasks, creator, successor, source


def _write_abandon_receipt(repo, tree, tasks, creator):
    """Owner-authored, hash-bound real binary patches, including both dirty states."""
    head = _git(tree, "rev-parse", "HEAD")
    base = _git(tree, "rev-parse", "main")
    destination = repo / "batch_state/abandon/boundary"
    destination.mkdir(parents=True, exist_ok=True)

    def entry(name, payload):
        path = destination / name
        path.write_bytes(payload)
        return {"path": path.relative_to(repo).as_posix(), "sha256": hashlib.sha256(payload).hexdigest()}

    manifest = {
        "schema": "terminal-abandon-preservation.v1",
        "owner": creator["task_id"],
        "run_nonce": creator["run_nonce"],
        "head_sha": head,
        "base_sha": base,
    }
    for key, revisions in (
        ("head_patch", [base, head]),
        ("index_patch", ["--cached", head]),
        ("working_patch", []),
    ):
        patch = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--no-ext-diff", "--no-textconv", *revisions, "--"],
            cwd=tree,
            check=True,
            capture_output=True,
            timeout=30,
        ).stdout
        manifest[key] = entry(key + ".patch", patch)
    creator["worktree_abandon"] = {
        "schema": "terminal-abandon.v1",
        "disposition": "ABANDON",
        "owner": creator["task_id"],
        "run_nonce": creator["run_nonce"],
        "head_sha": head,
        "reason": "superseded implementation",
        "preservation": entry("manifest.json", json.dumps(manifest, sort_keys=True).encode()),
    }
    save(tasks, creator)


@pytest.fixture
def abandon_cohort(same_branch_pending_cohort, monkeypatch):
    repo, tree, tasks, creator, successor, source = same_branch_pending_cohort
    (tree / "README.md").write_bytes(b"unpublished abandoned implementation\n")
    _git(tree, "add", "README.md")
    _git(tree, "commit", "-m", "unpublished abandoned work")
    head = _git(tree, "rev-parse", "HEAD")
    for member in (creator, successor):
        member["final_branch_head_commit"] = head
        save(tasks, member)
    _write_abandon_receipt(repo, tree, tasks, creator)
    monkeypatch.setattr(wg, "_query_pr_states", lambda *_: ([], None))
    return repo, tree, tasks, creator, successor, source
