"""Later child recovery keeps the earlier author carrier immutable."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest

from scripts.orchestration import lifecycle_observation as lo
from scripts.orchestration import task_identity
from scripts.orchestration import task_lifecycle as tl
from tests.orchestration.test_lifecycle_observation import observation_case  # noqa: F401
from tests.orchestration.test_merge_closeout import git
from tests.orchestration.test_task_lifecycle import NOW


@pytest.fixture
def child_case(observation_case):  # noqa: F811
    repo, worktree, child_file, task_file, manifest, push_file, first_head = observation_case
    child = tl.load_lifecycle(child_file)
    identity = deepcopy(child["identity"])
    identity["github_issue_number"] = 41
    identity["github_issue_url"] = "https://github.com/org/repo/issues/41"
    identity["visible_title"] = task_identity.visible_title(
        semantic_title=identity["semantic_title"], github_issue_number=41, task_family=identity["task_family"],
    )
    identity["carriers"] = dict.fromkeys(identity["carriers"], identity["visible_title"])
    earlier = tl.build_lifecycle(
        identity, author_family="codex", ac_snapshot=child["ac_snapshot"],
        required_checks=["CI Gate"], now=NOW, pr_number=76,
    )
    earlier_file = tl.lifecycle_path(repo, identity)
    tl.write_lifecycle(earlier_file, earlier)
    (worktree / "later").write_text("later child implementation\n")
    git(worktree, "add", "later")
    git(worktree, "commit", "-m", "later child\n\nX-Agent: codex/example")
    head = git(worktree, "rev-parse", "HEAD")
    task = json.loads(task_file.read_text())
    task["task_lifecycle"] = tl.carrier_projection(earlier, state_file=str(earlier_file))
    task["final_branch_head_commit"] = head
    task["worktree_reap_proof"]["pr_head_sha"] = head
    task["worktree_reap_proof"]["members"][0]["head_sha"] = head
    task_file.write_text(json.dumps(task))
    push = json.loads(push_file.read_text())
    push.update(head=head, remote_head=head)
    push_file.write_text(json.dumps(push))
    git(repo, "worktree", "remove", str(worktree))
    pr = {"number": 77, "url": "https://github.com/org/repo/pull/77", "state": "MERGED",
          "head_sha": head, "head_branch": task["worktree_branch"]}
    kwargs = dict(state_file=child_file, task_file=task_file, manifest_file=manifest, push_file=push_file, now=NOW)
    return repo, kwargs, pr, earlier_file, first_head


def test_later_child_recovery_and_replay_preserve_author(child_case):
    repo, kwargs, pr, earlier_file, first_head = child_case
    before = {path: path.read_bytes() for path in (earlier_file, kwargs["task_file"])}
    with pytest.raises(lo.ObservationRefusal, match="RECOVERY_LIFECYCLE_MISMATCH"):
        lo.recover(repo, **kwargs)
    receipt, replayed = lo.recover(repo, **kwargs, child_pr=pr)
    assert not replayed
    data = tl.load_lifecycle(kwargs["state_file"])
    local = tl._latest_premerge_local(data, head_sha=pr["head_sha"], branch=pr["head_branch"])
    assert {c["sha"] for c in local["commits"]} == {first_head, pr["head_sha"]}
    recovery = local["recovered_from_preserved"]
    association = recovery["association"]
    assert association == {
        "schema_version": "local-recovery-association.v1", "task_id": "example", "run_nonce": "attempt",
        "source": {"lifecycle_id": tl.load_lifecycle(earlier_file)["lifecycle_id"],
                   "identity": tl.load_lifecycle(earlier_file)["identity"]},
        "target": {"lifecycle_id": data["lifecycle_id"], "identity": data["identity"]},
        "child_pr": pr,
    }
    assert data["evidence"] == []
    assert lo.recovery_refusal(data, local) is None
    again, replayed = lo.recover(repo, **kwargs)
    assert replayed and again == receipt
    assert len(tl.load_lifecycle(kwargs["state_file"])["observation_receipts"]) == 1
    for path, raw in before.items():
        assert path.read_bytes() == raw


@pytest.mark.parametrize(("mutation", "reason"), [
    ("child_number", "RECOVERY_CHILD_PR_MISMATCH"),
    ("child_head", "RECOVERY_CHILD_PR_MISMATCH"),
    ("child_branch", "RECOVERY_CHILD_PR_MISMATCH"),
    ("child_url", "RECOVERY_CHILD_PR_MISMATCH"),
    ("child_open", "RECOVERY_CHILD_PR_MISMATCH"),
    ("proof_number", "RECOVERY_MERGED_PR_UNPROVEN"),
    ("proof_head", "RECOVERY_CHILD_PR_MISMATCH"),
    ("proof_missing", "RECOVERY_MERGED_PR_UNPROVEN"),
    ("carrier_missing", "RECOVERY_LIFECYCLE_MISMATCH"),
    ("carrier_id", "RECOVERY_LIFECYCLE_MISMATCH"),
    ("foreign_repository", "RECOVERY_LIFECYCLE_MISMATCH"),
    ("foreign_stream", "RECOVERY_LIFECYCLE_MISMATCH"),
    ("nonce_missing", "RECOVERY_ASSOCIATION_INVALID"),
    ("ancestry", "RECOVERY_COMMIT_ANCESTRY_MISMATCH"),
    ("member", "RECOVERY_BRANCH_MISMATCH"),
    ("push", "RECOVERY_PUSH_UNPROVEN"),
])
def test_child_refusals_do_not_append(child_case, mutation, reason):
    repo, kwargs, pr, _, first_head = child_case
    task_file = kwargs["task_file"]
    task = json.loads(task_file.read_text())
    if mutation.startswith("child_"):
        field, value = {
            "child_number": ("number", 78), "child_head": ("head_sha", first_head),
            "child_branch": ("head_branch", "codex/other"),
            "child_url": ("url", "https://github.com/foreign/repo/pull/77"),
            "child_open": ("state", "OPEN"),
        }[mutation]
        pr[field] = value
    elif mutation == "proof_number":
        task["worktree_reap_proof"]["pr_number"] = 76
    elif mutation == "proof_head":
        task["worktree_reap_proof"]["pr_head_sha"] = first_head
    elif mutation == "proof_missing":
        task.pop("worktree_reap_proof")
    elif mutation == "carrier_missing":
        task.pop("task_lifecycle")
    elif mutation == "carrier_id":
        task["task_lifecycle"]["lifecycle_id"] = "sha256:" + "f" * 64
    elif mutation.startswith("foreign_"):
        identity = task["task_lifecycle"]["identity"]
        if mutation == "foreign_repository":
            identity.update(repository="foreign/repo", github_issue_url="https://github.com/foreign/repo/issues/41",
                            stream_epic_url="https://github.com/foreign/repo/issues/10")
        else:
            identity.update(stream_epic=11, stream_epic_url="https://github.com/org/repo/issues/11")
        task["task_lifecycle"]["lifecycle_id"] = tl.lifecycle_id(identity)
    elif mutation == "nonce_missing":
        task.pop("run_nonce")
    elif mutation == "ancestry":
        task["worktree_reap_proof"]["pr_head_sha"] = first_head
        pr["head_sha"] = first_head
    elif mutation == "member":
        task["worktree_reap_proof"]["members"] = []
    elif mutation == "push":
        push = json.loads(kwargs["push_file"].read_text())
        push["steps"][0]["exit_code"] = 1
        kwargs["push_file"].write_text(json.dumps(push))
    task_file.write_text(json.dumps(task))
    before = kwargs["state_file"].read_bytes()
    with pytest.raises(lo.ObservationRefusal, match=reason):
        lo.recover(repo, **kwargs, child_pr=pr)
    assert kwargs["state_file"].read_bytes() == before


@pytest.mark.parametrize("source", ["task_file", "manifest_file", "push_file"])
def test_child_replay_rechecks_digests(child_case, source):
    repo, kwargs, pr, _, _ = child_case
    lo.recover(repo, **kwargs, child_pr=pr)
    path = kwargs[source]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(lo.ObservationRefusal, match="RECOVERY_DIGEST_MISMATCH"):
        lo.recover(repo, **kwargs)


def test_child_receipt_cannot_change_identity_attempt_or_head(child_case):
    repo, kwargs, pr, _, first_head = child_case
    lo.recover(repo, **kwargs, child_pr=pr)
    data = tl.load_lifecycle(kwargs["state_file"])
    local = data["observation_receipts"][-1]["observation"]["local"]
    # Even a descendant is a different exact child head, despite valid ancestry.
    descendant = git(repo, "commit-tree", pr["head_sha"] + "^{tree}", "-p", pr["head_sha"], "-m", "later head")
    assert lo.recovery_refusal(data, local, head_sha=descendant) == "RECOVERY_CHILD_PR_MISMATCH"
    assert lo.recovery_refusal(data, local, head_sha=first_head) == "RECOVERY_CHILD_PR_MISMATCH"
    for field in ("source", "target", "task_id", "run_nonce", "schema_version"):
        changed = deepcopy(local)
        changed["recovered_from_preserved"]["association"][field] = "forged"
        assert lo.recovery_refusal(data, changed) == "RECOVERY_ASSOCIATION_INVALID"


def _cli_args(repo, kwargs):
    return [
        "--repo-root", str(repo), "recover-local", "--associate-child",
        "--state-file", str(kwargs["state_file"]), "--task-record", str(kwargs["task_file"]),
        "--preserved-manifest", str(kwargs["manifest_file"]), "--push-record", str(kwargs["push_file"]),
    ]


def test_child_cli_reads_exact_authoritative_pr(child_case, monkeypatch, capsys):
    from scripts.orchestration import task_closeout as tc

    repo, kwargs, pr, _, _ = child_case
    calls = []

    def read_pr(self, repository, number):
        calls.append((repository, number))
        return pr

    monkeypatch.setattr(tc.GhGitHubAdapter, "_read_pr", read_pr)
    args = _cli_args(repo, kwargs)
    assert tc.main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["replayed"] is False
    assert tc.main(args) == 0
    second = json.loads(capsys.readouterr().out)
    assert second["replayed"] is True
    assert first["receipt"] == second["receipt"]
    assert calls == [("org/repo", 77), ("org/repo", 77)]


def test_child_cli_authority_failure_does_not_append(child_case, monkeypatch, capsys):
    from scripts.orchestration import task_closeout as tc

    repo, kwargs, _, _, _ = child_case

    def unavailable(*args):
        raise tl.LifecycleError("unavailable")

    monkeypatch.setattr(tc.GhGitHubAdapter, "_read_pr", unavailable)
    before = kwargs["state_file"].read_bytes()
    assert tc.main(_cli_args(repo, kwargs)) == 2
    assert json.loads(capsys.readouterr().err) == {"error": "RECOVERY_CHILD_PR_UNAVAILABLE"}
    assert kwargs["state_file"].read_bytes() == before


def test_child_replay_refuses_different_inputs_and_authority(child_case):
    repo, kwargs, pr, _, first_head = child_case
    lo.recover(repo, **kwargs, child_pr=pr)
    wrong = {**pr, "head_sha": first_head}
    with pytest.raises(lo.ObservationRefusal, match="RECOVERY_CHILD_PR_MISMATCH"):
        lo.recover(repo, **kwargs, child_pr=wrong)
    other_push = kwargs["push_file"].with_name("other-push.json")
    other_push.write_bytes(kwargs["push_file"].read_bytes())
    kwargs["push_file"] = other_push
    with pytest.raises(lo.ObservationRefusal, match="RECOVERY_DIGEST_MISMATCH"):
        lo.recover(repo, **kwargs)
