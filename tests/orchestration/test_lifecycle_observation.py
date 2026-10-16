from __future__ import annotations

import hashlib
import json

import pytest

from scripts.orchestration import merge_closeout as mc
from scripts.orchestration import reap_worktrees as rw
from scripts.orchestration import task_lifecycle as tl
from tests.orchestration.test_merge_closeout import add_worktree, git, init_repo
from tests.orchestration.test_task_lifecycle import NOW, _body, _ledger, _observation


@pytest.fixture
def observation_case(tmp_path, monkeypatch):
    repo = init_repo(tmp_path)
    monkeypatch.chdir(repo)
    git(repo, "config", "core.excludesFile", str(tmp_path / "excludes"))
    (tmp_path / "excludes").write_text(".agent/\nbatch_state/\n")
    worktree = add_worktree(repo, "codex/42-closeout")
    base = git(repo, "rev-parse", "HEAD")
    (worktree / "change").write_text("implementation\n")
    git(worktree, "add", "change")
    git(worktree, "commit", "-m", "implementation\n\nX-Agent: codex/example")
    head = git(worktree, "rev-parse", "HEAD")
    ledger = _ledger()
    state_file = tl.lifecycle_path(repo, ledger["identity"])
    tl.write_lifecycle(state_file, ledger)
    task = {
        "task_id": "example",
        "run_nonce": "attempt",
        "agent": "codex",
        "worktree_path": str(worktree),
        "worktree_branch": "codex/42-closeout",
        "worktree_base_sha": base,
        "final_branch_head_commit": head,
        "task_lifecycle": tl.carrier_projection(ledger, state_file=str(state_file)),
        "worktree_reap_proof": {
            "pr_state": "MERGED",
            "pr_number": 77,
            "pr_head_sha": head,
            "members": [{"task_id": "example", "branch": "codex/42-closeout", "head_sha": head}],
        },
    }
    location = "batch_state/preserved/example/attempt"
    bundle = repo / location
    bundle.mkdir(parents=True)
    (bundle / "proof.txt").write_text("preserved output\n")
    size = (bundle / "proof.txt").stat().st_size
    sha = hashlib.sha256((bundle / "proof.txt").read_bytes()).hexdigest()
    content = hashlib.sha256(json.dumps([("proof.txt", size, sha)]).encode()).hexdigest()
    manifest = {
        "task_id": "example",
        "owner": "example",
        "run_nonce": "attempt",
        "location": location,
        "paths": [{"path": "proof.txt", "size": size, "sha256": sha}],
        "content_sha256": content,
        "worktree_sha256": hashlib.sha256(str(worktree).encode()).hexdigest(),
    }
    manifest_file = bundle.with_suffix(".manifest.json")
    manifest_file.write_text(json.dumps(manifest))
    task["preserved_artifacts"] = {**manifest, "manifest_path": str(manifest_file.relative_to(repo))}
    tasks = repo / "batch_state/tasks"
    tasks.mkdir(parents=True)
    task_file = tasks / "example.json"
    task_file.write_text(json.dumps(task))
    push_file = repo / "push.json"
    push_file.write_text(
        json.dumps(
            {
                "head": head,
                "cwd": str(worktree),
                "remote_head": head,
                "status": "pushed_exact_head",
                "tracked_status": "",
                "steps": [{"name": "push", "exit_code": 0}],
            }
        )
    )
    # The primary must be clean; this source record is ignored in production too.
    with (tmp_path / "excludes").open("a") as f:
        f.write("push.json\n")
    return repo, worktree, state_file, task_file, manifest_file, push_file, head


def test_closeout_records_local_before_first_removal(observation_case, monkeypatch):
    repo, worktree, state_file, _, _, _, head = observation_case
    monkeypatch.setattr(
        mc, "fetch_pr_info", lambda *a, **k: mc.PullRequestInfo(77, "MERGED", "codex/42-closeout", head)
    )
    monkeypatch.setattr(mc, "verify_branch_gone", lambda *a, **k: None)

    def remove(**kwargs):
        local = tl._latest_premerge_local(tl.load_lifecycle(state_file))
        assert local is not None, "AC-01: lifecycle observation must precede reaping"
        assert local["commits"][0]["sha"] == head
        assert worktree.exists()
        return []

    monkeypatch.setattr(rw, "reap_worktrees", remove)
    mc.run_merge_closeout(repo, 77, apply=True)


def test_recovery_appends_and_is_idempotent(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, state_file, task, manifest, push, head = observation_case
    git(repo, "worktree", "remove", str(worktree))
    before = tl.load_lifecycle(state_file)
    receipt, replayed = lo.recover(
        repo, state_file=state_file, task_file=task, manifest_file=manifest, push_file=push, now=NOW
    )
    after = tl.load_lifecycle(state_file)
    assert replayed is False
    assert len(after["observation_receipts"]) == len(before["observation_receipts"]) + 1
    assert after["evidence"] == before["evidence"]
    local = tl._latest_premerge_local(after)
    assert local["recovered_from_preserved"]["task_id"] == "example"
    assert local["commits"][0]["sha"] == head
    assert not worktree.exists()
    again, replayed = lo.recover(
        repo, state_file=state_file, task_file=task, manifest_file=manifest, push_file=push, now=NOW
    )
    assert replayed is True
    assert again["id"] == receipt["id"]
    assert len(tl.load_lifecycle(state_file)["observation_receipts"]) == 1


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing_bundle", "RECOVERY_INPUT_UNAVAILABLE"),
        ("bundle_bytes", "RECOVERY_BUNDLE_DIGEST_MISMATCH"),
        ("different_task", "RECOVERY_TASK_MISMATCH"),
        ("different_branch", "RECOVERY_BRANCH_MISMATCH"),
        ("missing_commits", "RECOVERY_COMMITS_MISSING"),
        ("absent_commit_object", "RECOVERY_COMMIT_ANCESTRY_MISMATCH"),
        ("failed_push", "RECOVERY_PUSH_UNPROVEN"),
        ("different_push_head", "RECOVERY_PUSH_UNPROVEN"),
        ("different_lifecycle", "RECOVERY_LIFECYCLE_MISMATCH"),
        ("unmerged", "RECOVERY_MERGED_PR_UNPROVEN"),
        ("worktree_hash", "RECOVERY_WORKTREE_MISMATCH"),
        ("missing_preservation", "RECOVERY_BUNDLE_MISMATCH"),
        ("present_worktree", "RECOVERY_WORKTREE_STILL_PRESENT"),
        ("malformed_push", "RECOVERY_INPUT_INVALID"),
        ("missing_task_id", "RECOVERY_TASK_MISMATCH"),
        ("empty_commit_range", "RECOVERY_COMMITS_MISSING"),
    ],
)
def test_recovery_refuses_without_append(observation_case, mutation, reason):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task_file, manifest, push_file, _ = observation_case
    if mutation != "present_worktree":
        git(repo, "worktree", "remove", str(worktree))
    task = json.loads(task_file.read_text())
    push = json.loads(push_file.read_text())
    if mutation == "missing_bundle":
        manifest.unlink()
    elif mutation == "bundle_bytes":
        (manifest.with_suffix("").with_suffix("") / "proof.txt").write_text("tampered")
    elif mutation == "different_task":
        task["task_id"] = "other"
    elif mutation == "different_branch":
        task["worktree_branch"] = "codex/other"
    elif mutation == "missing_commits":
        task["worktree_base_sha"] = None
    elif mutation == "absent_commit_object":
        task["worktree_base_sha"] = "f" * 40
    elif mutation == "failed_push":
        push["steps"][0]["exit_code"] = 1
    elif mutation == "different_push_head":
        push["remote_head"] = "f" * 40
    elif mutation == "different_lifecycle":
        task["task_lifecycle"]["lifecycle_id"] = "sha256:" + "f" * 64
    elif mutation == "unmerged":
        task["worktree_reap_proof"]["pr_state"] = "OPEN"
    elif mutation == "worktree_hash":
        task["worktree_path"] += "-other"
        push["cwd"] = task["worktree_path"]
    elif mutation == "missing_preservation":
        task.pop("preserved_artifacts")
    elif mutation == "malformed_push":
        push["steps"] = [None]
    elif mutation == "missing_task_id":
        task.pop("task_id")
    elif mutation == "empty_commit_range":
        task["worktree_base_sha"] = task["final_branch_head_commit"]
        git(repo, "update-ref", "refs/remotes/origin/main", task["final_branch_head_commit"])
    task_file.write_text(json.dumps(task))
    push_file.write_text(json.dumps(push))
    before = ledger.read_bytes()
    with pytest.raises(lo.ObservationRefusal, match=reason):
        lo.recover(repo, state_file=ledger, task_file=task_file, manifest_file=manifest, push_file=push_file, now=NOW)
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("source", ["task", "manifest", "push", "bundle"])
def test_recovered_receipt_rechecks_all_digests(observation_case, source):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    lo.recover(repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW)
    path = {
        "task": task,
        "manifest": manifest,
        "push": push,
        "bundle": manifest.with_suffix("").with_suffix("") / "proof.txt",
    }[source]
    path.write_bytes(path.read_bytes() + b" ")
    data = tl.load_lifecycle(ledger)
    assert tl._latest_premerge_local(data) is None
    local = data["observation_receipts"][-1]["observation"]["local"]
    expected = "RECOVERY_BUNDLE_DIGEST_MISMATCH" if source == "bundle" else "RECOVERY_DIGEST_MISMATCH"
    assert lo.recovery_refusal(data, local) == expected
    with pytest.raises(lo.ObservationRefusal, match=expected):
        lo.recover(repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW)


def test_recovered_receipt_checks_authoritative_pr_branch_and_ancestry(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task, manifest, push, head = observation_case
    git(repo, "worktree", "remove", str(worktree))
    lo.recover(repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW)
    data = tl.load_lifecycle(ledger)
    assert tl._latest_premerge_local(data, branch="codex/other", head_sha=head) is None
    assert tl._latest_premerge_local(data, branch="codex/42-closeout", head_sha=git(repo, "rev-parse", "main")) is None
    observation = _observation(_body(), pr_state="MERGED", clean=True)
    observation["github"]["pr"]["head_sha"] = head
    observation["github"]["pr"]["head_branch"] = "codex/other"
    assert "RECOVERY_BRANCH_MISMATCH" in tl.evaluate(data, observation)["hard_blockers"]


def test_closeout_retains_everything_when_observation_write_fails(observation_case, monkeypatch):
    repo, worktree, _, _, _, _, head = observation_case
    monkeypatch.setattr(
        mc, "fetch_pr_info", lambda *a, **k: mc.PullRequestInfo(77, "MERGED", "codex/42-closeout", head)
    )
    monkeypatch.setattr(tl, "write_lifecycle", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    monkeypatch.setattr(mc, "reap_matched_worktrees", lambda *a, **k: pytest.fail("must not reap"))
    monkeypatch.setattr(mc, "verify_branch_gone", lambda *a, **k: pytest.fail("must not remove branches"))
    result = mc.run_merge_closeout(repo, 77, apply=True)
    assert not result.ok
    assert result.errors == ["lifecycle observation refused: disk full"]
    assert worktree.exists()


def test_capture_replays_without_changing_ledger(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, *_ = observation_case
    assert lo.before_reap(repo, worktree)[0]["status"] == "recorded"
    before = ledger.read_bytes()
    assert lo.before_reap(repo, worktree) == []
    assert ledger.read_bytes() == before


def test_capture_after_fast_forward_merge_keeps_commits(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, *_, head = observation_case
    git(repo, "merge", "--ff-only", head)
    git(repo, "update-ref", "refs/remotes/origin/main", head)
    lo.before_reap(repo, worktree)
    assert tl._latest_premerge_local(tl.load_lifecycle(ledger))["commits"][0]["sha"] == head


def test_post_task_reap_capture_failure_and_explicit_bypass(observation_case, monkeypatch):
    from scripts.fleet import post_task_reap as post

    repo, worktree, _, task, _, _, _ = observation_case
    monkeypatch.setattr(tl, "write_lifecycle", lambda *a, **k: (_ for _ in ()).throw(OSError("disk full")))
    calls = []
    monkeypatch.setattr(
        rw,
        "reap_worktrees",
        lambda **k: calls.append(k) or [rw.ReapResult(str(worktree), "codex/42-closeout", "removed", "merged", False)],
    )
    kwargs = dict(
        repo_root=repo, bound_path=worktree, apply=True, include_terminal_dispatches=True, tasks_dir=task.parent
    )
    result = post._reap_via_canonical(**kwargs)
    assert result["action"] == "retained"
    assert result["error"] == "disk full"
    assert calls == []
    result = post._reap_via_canonical(**kwargs, no_lifecycle_observation="operator recovery")
    assert len(calls) == 1
    assert result["lifecycle_observations"] == [{"status": "bypassed", "reason": "operator recovery"}]


def test_recovery_cli_appends_without_network(observation_case, capsys):
    from scripts.orchestration import task_closeout

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    args = [
        "--repo-root",
        str(repo),
        "recover-local",
        "--state-file",
        str(ledger),
        "--task-record",
        str(task),
        "--preserved-manifest",
        str(manifest),
        "--push-record",
        str(push),
    ]
    assert task_closeout.main(args) == 0
    assert json.loads(capsys.readouterr().out)["replayed"] is False
    assert task_closeout.main(args) == 0
    assert json.loads(capsys.readouterr().out)["replayed"] is True


def test_no_ledger_keeps_existing_reap_path(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, _, task_file, *_ = observation_case
    task = json.loads(task_file.read_bytes())
    task.pop("task_lifecycle")
    task_file.write_text(json.dumps(task))
    assert lo.before_reap(repo, worktree) == []


def test_missing_claimed_ledger_refuses_reap(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, *_ = observation_case
    ledger.unlink()
    with pytest.raises(lo.ObservationRefusal, match="LIFECYCLE_LEDGER_MISSING"):
        lo.before_reap(repo, worktree)


def test_capture_wrong_branch_refuses_reap(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, _, task_file, *_ = observation_case
    task = json.loads(task_file.read_bytes())
    task["worktree_branch"] = "codex/other"
    task_file.write_text(json.dumps(task))
    with pytest.raises(lo.ObservationRefusal, match="LIFECYCLE_LOCAL_OBSERVATION_INCOMPLETE"):
        lo.before_reap(repo, worktree)


def test_blank_bypass_reason_refuses(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, *_ = observation_case
    with pytest.raises(lo.ObservationRefusal, match="LIFECYCLE_OBSERVATION_BYPASS_REASON_REQUIRED"):
        lo.before_reap(repo, worktree, no_lifecycle_observation=" ")


def test_missing_bundle_cli_returns_typed_refusal(observation_case, capsys):
    from scripts.orchestration import task_closeout

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    manifest.unlink()
    assert (
        task_closeout.main(
            [
                "--repo-root",
                str(repo),
                "recover-local",
                "--state-file",
                str(ledger),
                "--task-record",
                str(task),
                "--preserved-manifest",
                str(manifest),
                "--push-record",
                str(push),
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().err) == {"error": "RECOVERY_INPUT_UNAVAILABLE"}


def test_capture_uses_explicit_lifecycle_locator(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task_file, *_ = observation_case
    custom = repo / ".agent/custom-ledger.json"
    ledger.rename(custom)
    task = json.loads(task_file.read_bytes())
    task["task_lifecycle"]["state_file"] = str(custom)
    task_file.write_text(json.dumps(task))
    assert lo.before_reap(repo, worktree)[0]["status"] == "recorded"
    assert tl._latest_premerge_local(tl.load_lifecycle(custom)) is not None


def _assert_no_host_paths(value, repo):
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_host_paths(item, repo)
    elif isinstance(value, list):
        for item in value:
            _assert_no_host_paths(item, repo)
    elif isinstance(value, str):
        assert not value.startswith("/"), value
        assert str(repo) not in value, value


def test_capture_receipt_has_no_host_paths(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, *_ = observation_case
    lo.before_reap(repo, worktree)
    _assert_no_host_paths(tl.load_lifecycle(ledger)["observation_receipts"], repo)
    local = tl._latest_premerge_local(tl.load_lifecycle(ledger))
    assert local["primary_checkout"] == "."
    assert local["worktree"] == ".worktrees/dispatch/codex-42-closeout"


def test_recovery_receipt_and_cli_have_no_host_paths(observation_case, capsys, monkeypatch):
    from scripts.orchestration import task_closeout

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    # --repo-root must supply validation context even from another directory.
    monkeypatch.chdir(repo.parent)
    assert task_closeout.main([
        "--repo-root", str(repo), "recover-local", "--state-file", str(ledger),
        "--task-record", str(task), "--preserved-manifest", str(manifest), "--push-record", str(push),
    ]) == 0
    _assert_no_host_paths(json.loads(capsys.readouterr().out), repo)
    _assert_no_host_paths(tl.load_lifecycle(ledger)["observation_receipts"], repo)


@pytest.mark.parametrize("name", ["manifest", "task", "push"])
@pytest.mark.parametrize("locator", ["../outside.json", "/outside.json", "link/outside.json"])
def test_recovery_refuses_escaping_locators(observation_case, tmp_path, name, locator):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    lo.recover(repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW)
    (repo / "link").symlink_to(tmp_path, target_is_directory=True)
    data = tl.load_lifecycle(ledger)
    local = data["observation_receipts"][-1]["observation"]["local"]
    local["recovered_from_preserved"]["inputs"][name]["path"] = locator
    assert lo.recovery_refusal(data, local) == "RECOVERY_LOCATOR_INVALID"


def test_relocated_recovery_receipt_still_verifies(observation_case, tmp_path, monkeypatch):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task, manifest, push, head = observation_case
    git(repo, "worktree", "remove", str(worktree))
    receipt, _ = lo.recover(
        repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW
    )
    relocated = tmp_path / "relocated"
    repo.rename(relocated)
    monkeypatch.chdir(relocated)
    data = tl.load_lifecycle(relocated / ledger.relative_to(repo))
    local = data["observation_receipts"][-1]["observation"]["local"]
    assert lo.recovery_refusal(data, local, head_sha=head, branch="codex/42-closeout") is None
    assert tl._latest_premerge_local(data) == local
    again, replayed = lo.recover(
        relocated, state_file=relocated / ledger.relative_to(repo), task_file=relocated / task.relative_to(repo),
        manifest_file=relocated / manifest.relative_to(repo), push_file=relocated / push.relative_to(repo), now=NOW,
    )
    assert replayed is True
    assert again == receipt
    _assert_no_host_paths(again, repo)


@pytest.mark.parametrize("locator", ["..", "/", "link"])
def test_recovery_refuses_escaping_repository_locator(observation_case, locator):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, task, manifest, push, _ = observation_case
    git(repo, "worktree", "remove", str(worktree))
    lo.recover(repo, state_file=ledger, task_file=task, manifest_file=manifest, push_file=push, now=NOW)
    (repo / "link").symlink_to(repo.parent, target_is_directory=True)
    data = tl.load_lifecycle(ledger)
    local = data["observation_receipts"][-1]["observation"]["local"]
    local["recovered_from_preserved"]["repo_root"] = locator
    assert lo.recovery_refusal(data, local) == "RECOVERY_LOCATOR_INVALID"


def test_existing_absolute_observation_still_reads_without_rewrite(observation_case):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, ledger, *_, head = observation_case
    local = tl.observe_local_git(repo, head_sha=head, branch="codex/42-closeout", worktree=str(worktree))
    assert local["primary_checkout"] == str(repo)
    assert local["worktree"] == str(worktree)
    observation = _observation(_body())
    observation["local"] = local
    updated, _, _ = tl.reconcile(tl.load_lifecycle(ledger), observation, now=NOW)
    tl.write_lifecycle(ledger, updated)
    before = ledger.read_bytes()
    assert lo.before_reap(repo, worktree) == []
    assert ledger.read_bytes() == before
    assert tl._latest_premerge_local(tl.load_lifecycle(ledger)) == local


@pytest.mark.parametrize("operation", ["capture", "recover"])
@pytest.mark.parametrize("history", ["unchanged_main", "advanced_main", "merged_main", "fast_forward"])
def test_observation_counts_only_task_history(observation_case, operation, history):
    from scripts.orchestration import lifecycle_observation as lo

    repo, worktree, state_file, task_file, manifest, push_file, first = observation_case
    if history in {"advanced_main", "merged_main"}:
        for count in (2, 4):
            name = f"main-only-{count}"
            (repo / name).write_text("unrelated PR\n")
            git(repo, "add", name)
            git(repo, "commit", "-m", "squashed PR\n\n" + "\n".join(
                f"X-Agent: claude/unrelated-{i}" for i in range(count)
            ))
        git(repo, "push", "origin", "main")
    if history == "merged_main":
        # This task's second commit includes the main integration. Its own
        # change and trailer must still be observed and validated.
        git(worktree, "merge", "--no-ff", "--no-commit", "origin/main")
    (worktree / "second-change").write_text("second task change\n")
    git(worktree, "add", "second-change")
    git(worktree, "commit", "-m", "second implementation\n\nX-Agent: codex/example")
    head = git(worktree, "rev-parse", "HEAD")
    if history == "fast_forward":
        git(repo, "merge", "--ff-only", head)
        git(repo, "update-ref", "refs/remotes/origin/main", head)
    task = json.loads(task_file.read_bytes())
    task["final_branch_head_commit"] = head
    task["worktree_reap_proof"]["pr_head_sha"] = head
    task["worktree_reap_proof"]["members"][0]["head_sha"] = head
    task_file.write_text(json.dumps(task))
    push = json.loads(push_file.read_bytes())
    push.update(head=head, remote_head=head)
    push_file.write_text(json.dumps(push))

    if operation == "capture":
        assert lo.before_reap(repo, worktree)[0]["status"] == "recorded"
    else:
        git(repo, "worktree", "remove", str(worktree))
        lo.recover(repo, state_file=state_file, task_file=task_file, manifest_file=manifest, push_file=push_file, now=NOW)
    local = tl._latest_premerge_local(tl.load_lifecycle(state_file))
    assert [commit["sha"] for commit in local["commits"]] == [head, first]
    assert local["changed_paths"] == ["change", "second-change"]
    assert tl._local_readiness(local) == []


def test_task_commit_range_refuses_ambiguous_absorbed_merge(observation_case):
    repo, worktree, _, task_file, *_ = observation_case
    base = json.loads(task_file.read_bytes())["worktree_base_sha"]
    (repo / "main-only").write_text("unrelated PR\n")
    git(repo, "add", "main-only")
    git(repo, "commit", "-m", "main update\n\nX-Agent: claude/unrelated")
    git(repo, "push", "origin", "main")
    git(worktree, "merge", "--no-ff", "origin/main", "-m", "integration\n\nX-Agent: codex/example")
    head = git(worktree, "rev-parse", "HEAD")
    git(repo, "merge", "--ff-only", head)
    git(repo, "update-ref", "refs/remotes/origin/main", head)

    with pytest.raises(tl.LifecycleError, match="task range is ambiguous"):
        tl.task_commit_range(repo, head, base)
    local = tl.observe_local_git(repo, head_sha=head, branch="codex/42-closeout", worktree=str(worktree), base_sha=base)
    assert local["commits"] == []
    assert local["changed_paths"] == []
    assert tl._local_readiness(local) == ["no task commits were available for X-Agent validation"]
