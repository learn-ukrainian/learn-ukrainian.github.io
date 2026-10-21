"""Mutation pins for the #11277 continuation proof (#11313).

Each test must fail when exactly one check is removed from the continuation
proof: the cohort predicate inside the numbered-record inactive-claim block,
the MERGED-state check in the by-number refresh, or the exact-head check in the
same refresh.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from tests.orchestration import test_merge_closeout as closeout
from tests.orchestration.test_reap_worktrees_superseded_creator import (
    merged_cohort as merged_cohort,
)
from tests.orchestration.test_reap_worktrees_superseded_creator import (
    queue_merged_cohort as queue_merged_cohort,
)
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree


def _result(repo, tree, *, apply):
    return next(r for r in rw.reap_worktrees(repo_root=repo, apply=apply, live_cwds=set()) if r.path == str(tree))


def test_inactive_claim_release_requires_same_branch_merged_cohort(queue_merged_cohort):
    """Defect class: dropping the cohort predicate from the numbered-record
    inactive-claim block would release a needs_finalize claim whose creator head
    is not contained in the merged checkout head (#11313).

    The branch query and the done-successor path cannot prove this cohort, so
    the cohort predicate inside the new guard is the only refusal.
    """
    repo, tree, tasks, creator_path, creator, current_path, current, head, _ = queue_merged_cohort
    foreign = closeout.git(tree, "commit-tree", f"{head}^{{tree}}", "-m", "uncontained creator history")
    assert foreign != head
    assert not rw._sha_is_ancestor(tree, foreign, head)
    creator["final_branch_head_commit"] = foreign
    creator_path.write_text(json.dumps(creator))
    current["status"] = "needs_finalize"
    current_path.write_text(json.dumps(current))
    record = json.loads(current_path.read_text())

    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    cohort = output._current_reuse_records(matches, tasks)
    info = rw.WorktreeInfo(tree, "codex/boundary", head)
    pr = rw.PullRequestState(9645, "MERGED", head)
    assert rw._same_branch_merged_cohort(info, pr, cohort) is False
    assert rw._merged_reuse_claim_proven_settled(repo, tree, record, tasks_dir=tasks, merged_pr=pr) is None
    assert tree.exists()


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("state", ["open", "closed"])
def test_by_number_refresh_refuses_non_merged_state(queue_merged_cohort, monkeypatch, apply, state):
    """Defect class: dropping the MERGED-state check in the by-number refresh
    would let an OPEN or CLOSED record for the same number fall through to a
    different, later refusal instead of the typed commit-search refusal (#11313).
    """
    repo, tree, tasks, _creator_path, _creator, _current_path, _current, head, _ = queue_merged_cohort
    original = rw._run_gh

    def numbered(args, **kwargs):
        if args[1:3] == ["api", "-X"] and args[-1].endswith("/pulls/9645"):
            payload = {
                "number": 9645,
                "state": state,
                "merged_at": None,
                "head": {"ref": "codex/boundary", "sha": head},
            }
            return subprocess.CompletedProcess(args, 0, json.dumps(payload), "")
        return original(args, **kwargs)

    monkeypatch.setattr(rw, "_run_gh", numbered)
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}

    result = _result(repo, tree, apply=apply)

    assert result.action == "skipped", result
    assert result.reason == "commit-search PR head unavailable"
    assert tree.exists()
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize("apply", [False, True])
@pytest.mark.parametrize("case", ["earlier", "sibling"])
def test_by_number_refresh_requires_exact_checkout_head(queue_merged_cohort, monkeypatch, apply, case):
    """Defect class: dropping the exact-head check in the by-number refresh
    would let a PR record whose head is not the checkout HEAD (an earlier
    commit of that head, or a sibling commit) be treated as exact proof (#11313).

    Decided (#11313): an earlier commit of the merged PR head is not the exact
    merged head, so its commit-search cohort stays unreaped rather than reaped
    as a continuation.
    """
    repo, tree, tasks, _creator_path, _creator, _current_path, _current, head, _ = queue_merged_cohort
    if case == "earlier":
        closeout.git(tree, "reset", "--hard", f"{head}^")
    else:
        sibling = closeout.git(tree, "commit-tree", f"{head}^{{tree}}", "-m", "sibling checkout head")
        closeout.git(tree, "reset", "--hard", sibling)
    local = closeout.git(tree, "rev-parse", "HEAD")
    assert local != head
    if case == "earlier":
        assert rw._sha_is_ancestor(tree, local, head)
    else:
        assert not rw._sha_is_ancestor(tree, local, head)
    closeout.patch_gh(
        monkeypatch,
        pr_number=9645,
        state="MERGED",
        head_ref_name="codex/boundary",
        head_sha=head,
        sha_prs={local: [{"number": 9645, "state": "MERGED"}]},
    )
    before = {p: p.read_bytes() for p in tasks.glob("*.json")}

    result = _result(repo, tree, apply=apply)

    assert result.action == "skipped", result
    assert result.reason == "commit-search PR head unavailable"
    assert tree.exists()
    assert closeout.git(tree, "rev-parse", "HEAD") == local
    assert {p: p.read_bytes() for p in before} == before
