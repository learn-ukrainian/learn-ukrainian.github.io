"""#10637: a merged continuation cohort re-reads the forge before its locked section, never under it or unbounded."""

import json

from scripts.orchestration import merge_closeout
from tests.orchestration._reaper_lock_probe import probe_reaper_lock
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import _switched_branch_cohort
from tests.test_reused_worktree_retention import cohort as cohort


def test_10637_switched_branch_continuation_rereads_the_forge_before_the_lock(cohort, monkeypatch):
    repo, tree, tasks, creator, _rounds, source, _branch, merged_head = _switched_branch_cohort(cohort, monkeypatch)
    source.unlink()
    probe = probe_reaper_lock(monkeypatch)

    result = merge_closeout.run_merge_closeout(repo, 10548, apply=True, live_cwds=set())

    row = result.reap_results[0]
    assert row["action"] == "removed", result
    assert not tree.exists()
    # The merged head is re-proven from forge answers read afresh in the
    # candidate's bounded section before its cleanup-wide lock; proof
    # publication under the lock uses those answers, and preservation after
    # the lock reads the forge again. Task-record locks are taken with a
    # bounded wait.
    assert probe.before_lock("_run_gh"), "the continuation's PR state was not read in the candidate's section"
    assert probe.violations() == [], probe.violations()
    proof = json.loads((tasks / "boundary.json").read_text())["worktree_reap_proof"]
    assert (proof["owner"], proof["head_sha"], proof["pr_head_sha"]) == (creator["task_id"], merged_head, merged_head)
