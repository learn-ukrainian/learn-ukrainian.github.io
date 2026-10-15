"""Owner-attested terminal abandonment (#10657), on disposable Git trees.

Each fixture shape mirrors one refused class from the #10629 run, built from
synthetic task records and repositories: a creatorless reused tree
(CREATOR_RECOVERY_REQUIRED), a detached tree, a ``needs_finalize`` tree on its
recorded branch, a ``needs_finalize`` tree whose checked-out branch moved, and a
tree whose caller-supplied preservation bundle fails the validator.
"""

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from tests.fleet.test_terminal_abandon import (
    _LEASE_ENV,
    FOREIGN_PID,
    INFRA,
    MONITOR,
    _files,
    _preserved_files,
    _recorded,
    _refused_removal,
    _set_lease_env,
    invoke,
    monitor_lease,
)
from tests.fleet.test_terminal_abandon import writer_fixture as writer_fixture
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save

ARCHIVE = "boundary.20261012T190957827067Z.archived.json"
SHAPES = ["creatorless", "detached", "needs_finalize", "branch_moved", "preservation_invalid"]
REPLACES = {
    "creatorless": ["CREATOR_RECOVERY_REQUIRED", "LIVE_OR_WANTED"],
    "detached": ["LIVE_OR_WANTED"],
    "needs_finalize": ["LIVE_OR_WANTED"],
    "branch_moved": ["LIVE_OR_WANTED"],
    "preservation_invalid": ["LIVE_OR_WANTED"],
}
REASON = "owner retired superseded implementation"


@pytest.fixture
def attest(writer_fixture, monkeypatch):
    """A retired monitor seat's settled-but-unfinalized tree; Muse holds monitor custody."""
    from scripts.session_supervisor import remote

    repo, tree, tasks, creator, successor, bundle, head = writer_fixture
    for member in (creator, successor):
        member["initiator"] = "claude-monitor"
        assert member["status"] == "needs_finalize" and member["keep_worktree"] is False
        save(tasks, member)
    monkeypatch.setenv("LU_RUNTIME_INITIATOR", "muse-monitor")
    _set_lease_env(monkeypatch)
    (tree / "untracked.txt").write_bytes(b"untracked unique bytes")
    monitor = {"streams": {MONITOR: monitor_lease()}, "calls": 0, "error": None, "bases": set()}

    def stream(self, stream_id, *, digest_limit=20):
        monitor["calls"] += 1
        monitor["bases"].add(self.base)
        if monitor["error"] is not None:
            raise monitor["error"]
        return {"stream_id": stream_id, "lease": json.loads(json.dumps(monitor["streams"].get(stream_id)))}

    monkeypatch.setattr(remote.RemoteEpicClient, "stream", stream)
    return {
        "repo": repo,
        "tree": tree,
        "tasks": tasks,
        "creator": creator,
        "successor": successor,
        "bundle": bundle,
        "head": head,
        "monitor": monitor,
        "fixture": writer_fixture,
    }


def _shape(name, fx):
    """Turn the base cohort into one refused shape; return the host task id."""
    tree, tasks, creator = fx["tree"], fx["tasks"], fx["creator"]
    if name == "creatorless":
        # The original creator survives only as a force-new archive of another
        # attempt; the current run reused the tree and carries no creation proof.
        (tasks / ARCHIVE).write_text(json.dumps(creator))
        creator.update(worktree_reused=True, run_nonce="current-run")
        creator.pop("ignored_output_baseline")
        save(tasks, creator)
        (tasks / "successor.json").unlink()
    elif name == "detached":
        _git(tree, "checkout", "--detach", fx["head"])
    elif name == "branch_moved":
        _git(tree, "checkout", "-b", "codex/boundary-r3b")
    elif name == "preservation_invalid":
        manifest = json.loads(fx["bundle"].read_bytes())
        (fx["repo"] / manifest["head_patch"]["path"]).write_bytes(b"corrupt patch")
    return creator["task_id"]


def attest_cli(fx, *, apply=False, task_id="boundary", head=None, reason=REASON, tree=None, extra=()):
    from scripts.fleet import terminal_abandon

    argv = [
        "--owner-attest",
        "--tree",
        str(fx["tree"] if tree is None else tree),
        "--task-id",
        task_id,
        "--head",
        fx["head"] if head is None else head,
        "--reason",
        reason,
        *extra,
    ]
    return terminal_abandon.main([*argv, "--apply"] if apply else argv)


def _out(capsys):
    return json.loads(capsys.readouterr().out)


def _remove(fx):
    repo, tree = fx["repo"], fx["tree"]
    row = next(
        r
        for r in rw.reap_worktrees(
            repo_root=repo, apply=True, live_cwds=set(), preserve_then_reap=True, merged_pr_only=False
        )
        if r.path == str(tree)
    )
    assert row.action in {"removed", "preserved_then_removed"}, row
    assert not tree.exists()
    return row


def _no_writes(fx, before):
    assert _files(fx["repo"]) == before
    assert not _preserved_files(fx["repo"])
    assert fx["tree"].exists()
    for path in fx["tasks"].glob("*.json"):
        assert "worktree_abandon" not in json.loads(path.read_bytes())


# --- The strict writer's refusals that the attestation exists to replace ---


@pytest.mark.parametrize(
    "shape,code", [("creatorless", "CREATOR_RECOVERY_REQUIRED"), ("needs_finalize", "LIVE_OR_WANTED")]
)
def test_strict_writer_still_refuses_the_shapes(attest, capsys, shape, code):
    _shape(shape, attest)
    assert invoke(attest["fixture"]) == 2
    assert _out(capsys)["code"] == code


# --- Accepted under a verified owner attestation ---


@pytest.mark.parametrize("shape", SHAPES)
def test_dry_run_is_default_and_writes_nothing(attest, capsys, shape):
    task_id = _shape(shape, attest)
    before = _files(attest["repo"])
    assert attest_cli(attest, task_id=task_id) == 0
    result = _out(capsys)
    assert result["outcome"] == "would_record", result
    assert [entry["code"] for entry in result["replaces"]] == REPLACES[shape]
    assert result["owner"]["seat"] == "muse-monitor" and result["owner"]["stream_id"] == MONITOR
    assert result["branch"] == {"detached": None, "branch_moved": "codex/boundary-r3b"}.get(shape, "codex/boundary")
    assert result["preservation_plan"]["commits"] == 1
    assert result["preservation_plan"]["output_files"] == 2
    _no_writes(attest, before)


@pytest.mark.parametrize("shape", SHAPES)
def test_attested_record_is_consumed_by_reaper_and_restores(attest, monkeypatch, tmp_path, capsys, shape):
    repo, tree, head = attest["repo"], attest["tree"], attest["head"]
    task_id = _shape(shape, attest)
    branch = {"detached": None, "branch_moved": "codex/boundary-r3b"}.get(shape, "codex/boundary")
    identity = [tree.stat().st_dev, tree.stat().st_ino]
    assert attest_cli(attest, apply=True, task_id=task_id) == 0
    result = _out(capsys)
    assert result["outcome"] == "recorded", result
    record, receipt, manifest = _recorded(attest["fixture"])
    assert record["task_id"] == task_id and receipt["owner"] == task_id
    assert receipt["head_sha"] == head and receipt["reason"] == REASON
    attestation = receipt["attestation"]
    assert attestation["schema"] == "terminal-abandon-attestation.v1"
    assert attestation["tree"] == tree.relative_to(repo).as_posix()
    assert attestation["directory_identity"] == identity
    assert attestation["branch"] == branch and attestation["head_sha"] == head
    assert attestation["reason"] == REASON and attestation["attested_at"].endswith("Z")
    assert [entry["code"] for entry in attestation["replaces"]] == REPLACES[shape]
    assert attestation["preservation_sha256"] == receipt["preservation"]["sha256"]
    owner = attestation["owner"]
    assert owner["seat"] == "muse-monitor" and owner["area"] == "monitor" and owner["stream_id"] == MONITOR
    assert owner["task_initiator"] == "claude-monitor"
    assert owner["authority"] == {
        "stream_id": MONITOR,
        "session_id": "session-current",
        "lease_id": "lease-current",
        "generation": 4,
        "fencing_token": 17,
        "holder": {"agent": "muse", "harness": "muse-cli", "instance_id": "muse-monitor-1"},
    }
    assert sorted(entry["task_id"] for entry in attestation["cohort"]) == (
        ["boundary", "boundary"] if shape == "creatorless" else ["boundary", "successor"]
    )
    # Preservation is the tool's own: hashes, identity and base are bound.
    assert manifest["owner"] == task_id and manifest["head_sha"] == head
    assert manifest["base_sha"] == _git(repo, "rev-parse", "main")
    for key in ("head_patch", "index_patch", "working_patch", "commit_bundle"):
        payload = (repo / manifest[key]["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == manifest[key]["sha256"]
        assert not (repo / manifest[key]["path"]).is_relative_to(tree)
    assert manifest["index_patch"]["sha256"] == manifest["working_patch"]["sha256"] == hashlib.sha256(b"").hexdigest()
    # The reaper's existing reader accepts it and still runs its removal proofs.
    plan = next(
        r
        for r in rw.reap_worktrees(
            repo_root=repo, apply=False, live_cwds=set(), preserve_then_reap=True, merged_pr_only=False
        )
        if r.path == str(tree)
    )
    assert plan.reason == "terminal-abandon.v1 verified owner ABANDON and preservation", plan
    row = _remove(attest)
    assert row.preserved_artifacts["abandon_proof"]["attestation"] == attestation
    # No data loss: the commits, the tree bytes and the output all restore.
    restored = tmp_path / "restored"
    _git(repo, "clone", "--no-local", "--single-branch", "--branch", "main", str(repo), str(restored))
    _git(restored, "fetch", str(repo / manifest["commit_bundle"]["path"]), "HEAD")
    _git(restored, "checkout", "--detach", "FETCH_HEAD")
    assert _git(restored, "rev-parse", "HEAD") == head
    assert (restored / "README.md").read_bytes() == b"unpublished abandoned implementation\n"
    environment = dict(os.environ, GIT_INDEX_FILE=str(tmp_path / "restore.index"))
    subprocess.run(["git", "read-tree", manifest["base_sha"]], cwd=repo, env=environment, check=True, timeout=30)
    subprocess.run(
        ["git", "apply", "--cached", str(repo / manifest["head_patch"]["path"])],
        cwd=repo,
        env=environment,
        check=True,
        timeout=30,
    )
    rebuilt = subprocess.run(
        ["git", "write-tree"], cwd=repo, env=environment, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()
    assert rebuilt == _git(repo, "rev-parse", f"{head}^{{tree}}")
    located = manifest["output"]
    assert output.verify_retrieval(repo, located) == located["content_sha256"]
    copy = repo / located["location"]
    assert (copy / "ignored/output.txt").read_bytes() == b"current output"
    assert (copy / "untracked.txt").read_bytes() == b"untracked unique bytes"
    with tarfile.open(fileobj=io.BytesIO((repo / located["archive"]["path"]).read_bytes())) as tar:
        members = {member.name: tar.extractfile(member).read() for member in tar.getmembers()}
    assert members == {"ignored/output.txt": b"current output", "untracked.txt": b"untracked unique bytes"}


@pytest.mark.parametrize("shape", SHAPES)
def test_second_run_is_idempotent(attest, capsys, shape):
    task_id = _shape(shape, attest)
    assert attest_cli(attest, apply=True, task_id=task_id) == 0
    capsys.readouterr()
    before = _files(attest["repo"])
    preserved = _preserved_files(attest["repo"])
    for apply in (True, False):
        assert attest_cli(attest, apply=apply, task_id=task_id) == 0
        assert _out(capsys)["outcome"] == "already_recorded"
    assert _files(attest["repo"]) == before
    assert _preserved_files(attest["repo"]) == preserved


@pytest.mark.parametrize("shape", ["detached", "needs_finalize"])
def test_tree_without_output_records_and_removes(attest, capsys, shape):
    """Real-tree shape: two of the refused trees carry no untracked or ignored output."""
    tree = attest["tree"]
    (tree / "untracked.txt").unlink()
    (tree / "ignored/output.txt").unlink()
    _shape(shape, attest)
    assert attest_cli(attest) == 0
    assert _out(capsys)["preservation_plan"]["output_files"] == 0
    assert attest_cli(attest, apply=True) == 0
    assert _out(capsys)["outcome"] == "recorded"
    _, _, manifest = _recorded(attest["fixture"])
    assert manifest["output"]["paths"] == []
    assert output.verify_retrieval(attest["repo"], manifest["output"]) == manifest["output"]["content_sha256"]
    _remove(attest)


def test_retention_intent_is_replaced_and_released_at_removal(attest, capsys):
    for member in (attest["creator"], attest["successor"]):
        member["keep_worktree"] = True
        save(attest["tasks"], member)
    assert attest_cli(attest, apply=True) == 0
    assert _out(capsys)["outcome"] == "recorded"
    record, receipt, _ = _recorded(attest["fixture"])
    assert record["keep_worktree"] is True
    assert [entry["code"] for entry in receipt["attestation"]["replaces"]] == ["LIVE_OR_WANTED"]
    _remove(attest)


# --- The owner must be authenticated custody of the lane that owns the task ---


def _owner_defect(defect, fx, monkeypatch):
    monitor, tasks = fx["monitor"], fx["tasks"]
    lease = monitor["streams"][MONITOR]
    if defect == "no_lease":
        for key in _LEASE_ENV:
            monkeypatch.delenv(f"SESSION_STREAM_{key}")
    elif defect == "unknown_attribution":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "unknown")
    elif defect == "forged_lease":
        # Lease env names a lease Monitor does not hold for the stream.
        lease["lease_id"] = "lease-actually-current"
    elif defect == "expired":
        lease["expires_at"] = "2000-01-01T00:00:00Z"
    elif defect == "monitor_down":
        from scripts.session_supervisor.remote import RemoteUnreachableError

        monitor["error"] = RemoteUnreachableError("unreachable")
    elif defect == "foreign_stream":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "claude-infra")
        _set_lease_env(monkeypatch, ID=INFRA, AGENT="claude", HARNESS="claude-code", INSTANCE_ID="claude-infra-1")
        monitor["streams"][INFRA] = dict(
            lease,
            stream_id=INFRA,
            holder={"agent": "claude", "harness": "claude-code", "instance_id": "claude-infra-1"},
        )
    elif defect == "foreign_member":
        fx["successor"]["initiator"] = "claude-infra"
        save(tasks, fx["successor"])
    elif defect == "seat_provider_mismatch":
        # Attribution claims the Muse seat; the Monitor-verified holder is Claude.
        _set_lease_env(monkeypatch, AGENT="claude", HARNESS="claude-code")
        lease["holder"] = dict(lease["holder"], agent="claude", harness="claude-code")
    elif defect == "unregistered_seat":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "muse-folk")
    elif defect == "unmapped_initiator":
        for member in (fx["creator"], fx["successor"]):
            member["initiator"] = "claude-core"
            save(tasks, member)
    else:
        raise AssertionError(defect)


@pytest.mark.parametrize(
    "defect,code",
    [
        ("no_lease", "OWNER_UNAUTHENTICATED"),
        ("unknown_attribution", "OWNER_UNAUTHENTICATED"),
        ("forged_lease", "STALE_AUTHORITY"),
        ("expired", "STALE_AUTHORITY"),
        ("monitor_down", "AUTHORITY_UNKNOWN"),
        ("foreign_stream", "FOREIGN_OWNER"),
        ("foreign_member", "FOREIGN_OWNER"),
        ("seat_provider_mismatch", "FOREIGN_OWNER"),
        ("unregistered_seat", "FOREIGN_OWNER"),
        ("unmapped_initiator", "OWNER_UNMAPPED"),
    ],
)
@pytest.mark.parametrize("apply", [False, True])
def test_unverified_owner_is_refused(attest, monkeypatch, capsys, defect, code, apply):
    _owner_defect(defect, attest, monkeypatch)
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=apply) == 2
    result = _out(capsys)
    assert (result["outcome"], result["code"]) == ("refused", code), result
    assert [entry["code"] for entry in result["replaces"]] == ["LIVE_OR_WANTED"]
    _no_writes(attest, before)


def test_owner_cannot_be_named_by_argument(attest, monkeypatch, capsys):
    with pytest.raises(SystemExit):
        attest_cli(attest, apply=True, extra=("--owner", "muse-monitor"))
    for key in _LEASE_ENV:
        monkeypatch.delenv(f"SESSION_STREAM_{key}")
    # The attributed seat alone, without launcher-issued custody, is not an owner.
    assert attest_cli(attest, apply=True) == 2
    assert _out(capsys)["code"] == "OWNER_UNAUTHENTICATED"


# --- What an attestation can never replace ---


def _blocker(blocker, fx, monkeypatch):
    tree, tasks, successor = fx["tree"], fx["tasks"], fx["successor"]
    if blocker == "live_pid":
        successor["pid"] = os.getpid()
        save(tasks, successor)
    elif blocker == "live_pid_host":
        fx["creator"]["pid"] = os.getpid()
        save(tasks, fx["creator"])
    elif blocker == "live_cwd":
        monkeypatch.setattr(rw, "_live_cwd_paths", lambda _: {tree / "ignored"})
    elif blocker == "activity_unknown":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: None)
    elif blocker == "active_task":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: {fx["creator"]["task_id"]})
    elif blocker == "worker_lease":
        fx["creator"]["lease_state"] = "active"
        save(tasks, fx["creator"])
    elif blocker == "rollover":
        monkeypatch.setattr(rw, "_has_active_rollover_lease", lambda *_: "active rollover")
    elif blocker == "running_status":
        fx["creator"]["status"] = "running"
        save(tasks, fx["creator"])
    elif blocker == "open_pr":
        # Only the recorded dispatch branch has the open PR, so a detached or
        # moved checkout cannot hide it.
        monkeypatch.setattr(
            rw,
            "_query_pr_states",
            lambda _root, branch: (
                ([rw.PullRequestState(10657, "OPEN", "0" * 40)], None) if branch == "codex/boundary" else ([], None)
            ),
        )
    elif blocker == "pr_unknown":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([], "unavailable"))
    elif blocker == "dirty_tracked":
        (tree / "README.md").write_bytes(b"unpreserved tracked edit")
    elif blocker == "dirty_staged":
        (tree / "README.md").write_bytes(b"unpreserved staged edit")
        _git(tree, "add", "README.md")
    elif blocker == "dirty_concealed":
        _git(tree, "update-index", "--assume-unchanged", "README.md")
        (tree / "README.md").write_bytes(b"concealed tracked edit")
    elif blocker == "index_lock":
        lock = _git(tree, "rev-parse", "--path-format=absolute", "--git-path", "index.lock")
        open(lock, "wb").close()
    else:
        raise AssertionError(blocker)


BLOCKER_CODES = {
    "live_pid": "LIVE_OR_WANTED",
    "live_pid_host": "LIVE_OR_WANTED",
    "live_cwd": "LIVE_OR_WANTED",
    "activity_unknown": "ACTIVITY_UNKNOWN",
    "active_task": "LIVE_OR_WANTED",
    "worker_lease": "LIVE_OR_WANTED",
    "rollover": "LIVE_OR_WANTED",
    "running_status": "LIVE_OR_WANTED",
    "open_pr": "LIVE_OR_WANTED",
    "pr_unknown": "ACTIVITY_UNKNOWN",
    "dirty_tracked": "DIRTY_TREE",
    "dirty_staged": "DIRTY_TREE",
    "dirty_concealed": "DIRTY_TREE",
    "index_lock": "DIRTY_TREE",
}


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("blocker", ["live_pid_host", "active_task", "open_pr", "dirty_tracked"])
def test_attestation_never_replaces_liveness_pr_or_dirt(attest, monkeypatch, capsys, shape, blocker):
    task_id = _shape(shape, attest)
    _blocker(blocker, attest, monkeypatch)
    before = _files(attest["repo"])
    for apply in (False, True):
        assert attest_cli(attest, apply=apply, task_id=task_id) == 2
        result = _out(capsys)
        assert result["code"] == BLOCKER_CODES[blocker], result
    _no_writes(attest, before)


@pytest.mark.parametrize("blocker", sorted(BLOCKER_CODES))
def test_each_blocker_refuses_a_valid_attestation(attest, monkeypatch, capsys, blocker):
    _blocker(blocker, attest, monkeypatch)
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True) == 2
    assert _out(capsys)["code"] == BLOCKER_CODES[blocker]
    _no_writes(attest, before)


@pytest.mark.parametrize("status", ["failed", "dry_run"])
def test_pidless_bound_record_is_named_as_the_remaining_blocker(attest, capsys, status):
    """Real-tree shape: a never-launched attempt bound to the tree recorded no PID.

    The PID proof is a liveness check the attestation may not replace, so the
    refusal names the exact record and condition that remain.
    """
    attempt = dict(attest["successor"], task_id="prep-failed", run_nonce="prep-run", status=status, pid=None)
    save(attest["tasks"], attempt)
    before = _files(attest["repo"])
    for apply in (False, True):
        assert attest_cli(attest, apply=apply) == 2
        result = _out(capsys)
        assert result["code"] == "LIVE_OR_WANTED", result
        assert result["reason"] == (
            "bound record prep-failed.json has no valid recorded PID, so its worker's exit cannot be proven; "
            "an attestation never replaces liveness"
        )
    _no_writes(attest, before)


def test_live_pid_refusal_names_the_record(attest, monkeypatch, capsys):
    _blocker("live_pid", attest, monkeypatch)
    assert attest_cli(attest, apply=True) == 2
    assert f"successor.json PID {os.getpid()} is held by a live process" in _out(capsys)["reason"]


# --- Preservation is produced by the tool, or the one blocker is named ---


def test_caller_bundle_is_never_trusted_in_attested_mode(attest, capsys):
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True, extra=("--preservation-bundle", str(attest["bundle"]))) == 2
    result = _out(capsys)
    assert result["code"] == "INVALID_INPUT" and "regenerates" in result["reason"]
    _no_writes(attest, before)


@pytest.mark.parametrize("limit", ["output_cap", "bundle_cap", "orphan_head"])
def test_unpreservable_tree_names_the_remaining_blocker(attest, monkeypatch, capsys, limit):
    tree = attest["tree"]
    if limit == "output_cap":
        monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
        code, text = "PRESERVATION_LIMIT", "preservation cap"
    elif limit == "bundle_cap":
        monkeypatch.setattr(output, "MAX_DETACHED_BUNDLE_BYTES", 1)
        code, text = "PRESERVATION_LIMIT", "MAX_DETACHED_BUNDLE_BYTES"
    else:
        _git(tree, "checkout", "--orphan", "codex/orphan")
        _git(tree, "commit", "-m", "history unrelated to main")
        attest["head"] = _git(tree, "rev-parse", "HEAD")
        code, text = "PRESERVATION_INVALID", "origin/main"
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True) == 2
    result = _out(capsys)
    assert result["code"] == code and text in result["reason"], result
    _no_writes(attest, before)


def test_bundle_timeout_is_a_typed_refusal_and_leaves_no_scratch(attest, monkeypatch, capsys):
    from scripts.fleet import terminal_abandon

    real = terminal_abandon.artifacts.safe_git

    def slow_bundle(args, **kwargs):
        if args[:2] == ["bundle", "create"]:
            # Git holds <target>.lock while it writes; an interrupted create leaves it.
            open(args[2] + ".lock", "wb").close()
            raise subprocess.TimeoutExpired(args, 30)
        return real(args, **kwargs)

    monkeypatch.setattr(terminal_abandon.artifacts, "safe_git", slow_bundle)
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True) == 2
    result = _out(capsys)
    assert result["code"] == "PRESERVATION_INVALID" and "bundle" in result["reason"], result
    _no_writes(attest, before)
    assert not list((attest["repo"] / "batch_state/abandon/boundary").glob(".head-bundle-*"))


def test_help_documents_the_attested_mode():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    shown = subprocess.run(
        [sys.executable, "-m", "scripts.fleet.terminal_abandon", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    ).stdout
    for text in ("--owner-attest", "--tree", "--apply", "OWNER_UNAUTHENTICATED", "FOREIGN_OWNER", "DIRTY_TREE"):
        assert text in shown
    assert "area_assignments.yaml" in shown and "reap_worktrees.py --legacy-classes" in shown


# --- Inputs, one record per tree, and identity bound at removal ---


@pytest.mark.parametrize("bad", ["apply_without_attest", "tree_without_attest", "recover_with_attest", "wrong_tree"])
def test_invalid_mode_inputs_refuse(attest, capsys, bad):
    from scripts.fleet import terminal_abandon

    before = _files(attest["repo"])
    if bad == "wrong_tree":
        other = attest["repo"] / ".worktrees/dispatch/codex/other"
        _git(attest["repo"], "worktree", "add", "-b", "codex/other", str(other), "main")
        assert attest_cli(attest, apply=True, tree=other) == 2
    else:
        extra = {
            "apply_without_attest": ["--apply"],
            "tree_without_attest": ["--tree", str(attest["tree"])],
            "recover_with_attest": None,
        }[bad]
        if extra is None:
            assert attest_cli(attest, apply=True, extra=("--recover-creator",)) == 2
        else:
            argv = ["--task-id", "boundary", "--head", attest["head"], "--reason", REASON]
            argv += ["--preservation-bundle", str(attest["bundle"]), *extra]
            assert terminal_abandon.main(argv) == 2
    assert _out(capsys)["code"] == "INVALID_INPUT"
    _no_writes(attest, before)


def test_stale_head_is_refused_at_write(attest, capsys):
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True, head=_git(attest["repo"], "rev-parse", "main")) == 2
    assert _out(capsys)["code"] == "HEAD_MISMATCH"
    _no_writes(attest, before)


def test_one_record_per_tree(attest, capsys):
    assert attest_cli(attest, apply=True) == 0
    capsys.readouterr()
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True, reason="a different disposition") == 2
    assert _out(capsys)["code"] == "ALREADY_RECORDED"
    assert _files(attest["repo"]) == before


def test_existing_creator_record_is_never_overwritten(attest, capsys):
    from tests.test_continuation_worktree_reap import _write_abandon_receipt

    _write_abandon_receipt(attest["repo"], attest["tree"], attest["tasks"], attest["creator"])
    save(attest["tasks"], attest["creator"])
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True) == 2
    assert _out(capsys)["code"] == "ALREADY_RECORDED"
    assert _files(attest["repo"]) == before


def _drift(drift, fx):
    repo, tree, tasks = fx["repo"], fx["tree"], fx["tasks"]
    if drift == "head":
        (tree / "README.md").write_bytes(b"later work after attestation\n")
        _git(tree, "commit", "-am", "later work")
        return "HEAD"
    if drift == "branch":
        _git(tree, "checkout", "-b", "codex/after-attestation")
        return "branch"
    if drift == "detached":
        _git(tree, "checkout", "--detach")
        return "branch"
    if drift == "directory":
        # Same path, branch and HEAD, but a different checkout directory.
        _git(repo, "worktree", "remove", "--force", str(tree))
        _git(repo, "worktree", "add", str(tree), "codex/boundary")
        (tree / "ignored").mkdir()
        (tree / "ignored/output.txt").write_bytes(b"current output")
        (tree / "untracked.txt").write_bytes(b"untracked unique bytes")
        return "directory identity"
    if drift == "cohort":
        late = dict(fx["successor"], task_id="late-arrival", run_nonce="late-run")
        save(tasks, late)
        return "cohort"
    if drift == "dirty":
        (tree / "README.md").write_bytes(b"tracked edit after attestation")
        return "tracked"
    if drift == "output":
        (tree / "untracked.txt").write_bytes(b"changed after attestation")
        return "output"
    raise AssertionError(drift)


@pytest.mark.parametrize("drift", ["head", "branch", "detached", "directory", "cohort", "dirty", "output"])
def test_record_never_authorises_a_changed_tree(attest, capsys, drift):
    assert attest_cli(attest, apply=True) == 0
    capsys.readouterr()
    text = _drift(drift, attest)
    matches = output.matching_worktree_records(
        attest["tree"], attest["tasks"], repo_root=attest["repo"], publish_cache=False
    )
    with pytest.raises(ValueError, match=text):
        output.terminal_abandon_creator(matches, attest["tree"], primary=attest["repo"], tasks_dir=attest["tasks"])
    _refused_removal(attest["fixture"], "terminal-abandon refused")


@pytest.mark.parametrize("shape", SHAPES)
def test_head_moved_after_attestation_refuses_removal_for_every_shape(attest, capsys, shape):
    task_id = _shape(shape, attest)
    assert attest_cli(attest, apply=True, task_id=task_id) == 0
    capsys.readouterr()
    tree = attest["tree"]
    (tree / "README.md").write_bytes(b"later work after attestation\n")
    _git(tree, "commit", "-am", "later work")
    _refused_removal(attest["fixture"], "terminal-abandon refused")


@pytest.mark.parametrize(
    "tamper",
    ["replaces_code", "owner_missing", "authority_type", "preservation_digest", "extra_key", "two_records"],
)
def test_reader_refuses_a_malformed_attestation(attest, capsys, tamper):
    tasks = attest["tasks"]
    assert attest_cli(attest, apply=True) == 0
    capsys.readouterr()
    record, receipt, _ = _recorded(attest["fixture"])
    attestation = receipt["attestation"]
    if tamper == "replaces_code":
        attestation["replaces"] = [{"code": "DIRTY_TREE", "reason": "never replaceable"}]
    elif tamper == "owner_missing":
        attestation.pop("owner")
    elif tamper == "authority_type":
        attestation["owner"]["authority"]["generation"] = "4"
    elif tamper == "preservation_digest":
        attestation["preservation_sha256"] = "0" * 64
    elif tamper == "extra_key":
        receipt["succession"] = {"schema": "terminal-abandon-succession.v1"}
    else:
        attest["successor"]["worktree_abandon"] = receipt
        save(tasks, attest["successor"])
    save(tasks, record)
    matches = output.matching_worktree_records(attest["tree"], tasks, repo_root=attest["repo"], publish_cache=False)
    with pytest.raises(ValueError, match="attestation"):
        output.terminal_abandon_creator(matches, attest["tree"], primary=attest["repo"], tasks_dir=tasks)
    _refused_removal(attest["fixture"], "terminal-abandon refused")


# --- #10657 review round 1: the four blockers, each from its reproduction ---


def _holder_defect(defect, fx, monkeypatch):
    """Make the session's custody unprovable while every envelope field still matches Monitor."""
    from scripts.api import occupancy_local
    from scripts.fleet import terminal_abandon

    lease = fx["monitor"]["streams"][MONITOR]
    if defect == "copied_envelope":
        # The reviewer's probe: the stream response copied into the environment.
        _set_lease_env(monkeypatch, PROCESS_ID=str(FOREIGN_PID))
        lease["holder"] = dict(lease["holder"], process_id=FOREIGN_PID)
    elif defect == "app_thread":
        task = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
        _set_lease_env(monkeypatch, HOLDER_KIND="app_thread", TASK_ID=task)
        monkeypatch.delenv("SESSION_STREAM_PROCESS_ID")
        lease["holder"] = dict(lease["holder"], holder_kind="app_thread", process_id=None, task_id=task)
    elif defect == "other_host":
        monkeypatch.setattr(occupancy_local, "resolve_launcher_host_id", lambda: "host-elsewhere")
    elif defect == "reused_pid":
        # This process started long after the lease's last heartbeat.
        lease["heartbeat_at"] = "2000-01-01T00:00:00Z"
    elif defect == "ancestry_unavailable":

        def unavailable():
            raise OSError("no /proc")

        monkeypatch.setattr(terminal_abandon, "_process_lineage", unavailable, raising=False)
    else:
        raise AssertionError(defect)


@pytest.mark.parametrize(
    "defect", ["copied_envelope", "app_thread", "other_host", "reused_pid", "ancestry_unavailable"]
)
@pytest.mark.parametrize("apply", [False, True])
def test_owner_must_run_beneath_the_recorded_holder_process(attest, monkeypatch, capsys, defect, apply):
    """Blocker 1: a lease envelope is bearer data; only the holder's process tree is the owner."""
    _holder_defect(defect, attest, monkeypatch)
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=apply) == 2
    result = _out(capsys)
    assert (result["outcome"], result["code"]) == ("refused", "HOLDER_UNPROVEN"), result
    _no_writes(attest, before)


def test_holder_may_be_an_ancestor_not_only_this_process(attest, monkeypatch, capsys):
    parent = os.getppid()
    _set_lease_env(monkeypatch, PROCESS_ID=str(parent))
    lease = attest["monitor"]["streams"][MONITOR]
    lease["holder"] = dict(lease["holder"], process_id=parent)
    assert attest_cli(attest, apply=True) == 0
    assert _out(capsys)["outcome"] == "recorded"
    _remove(attest)


def test_environment_never_selects_the_authority_endpoint(attest, monkeypatch, capsys):
    monkeypatch.setenv("LU_MONITOR_LOOPBACK", "http://127.0.0.1:9")
    assert attest_cli(attest) == 0
    assert _out(capsys)["outcome"] == "would_record"
    assert attest["monitor"]["bases"] == {"http://127.0.0.1:8765"}


def _attested(fx, capsys):
    assert attest_cli(fx, apply=True) == 0
    assert _out(capsys)["outcome"] == "recorded"
    return _recorded(fx["fixture"])


def _reader_refuses(fx, code):
    matches = output.matching_worktree_records(fx["tree"], fx["tasks"], repo_root=fx["repo"], publish_cache=False)
    with pytest.raises(ValueError, match=code):
        output.terminal_abandon_creator(matches, fx["tree"], primary=fx["repo"], tasks_dir=fx["tasks"])
    _refused_removal(fx["fixture"], code)


@pytest.mark.parametrize(
    "tamper,code",
    [
        ("reviewer_probe", "FOREIGN_OWNER"),
        ("foreign_seat", "FOREIGN_OWNER"),
        ("area", "FOREIGN_OWNER"),
        ("lane", "FOREIGN_OWNER"),
        ("task_initiator", "FOREIGN_OWNER"),
        ("invented_session", "STALE_AUTHORITY"),
        ("invented_lease", "STALE_AUTHORITY"),
        ("invented_fence", "STALE_AUTHORITY"),
        ("mapping_hash", "MAPPING_CHANGED"),
        ("assignments_hash", "MAPPING_CHANGED"),
    ],
)
def test_reader_refuses_fabricated_authorization(attest, capsys, tamper, code):
    """Blocker 2: no self-described owner field authorizes removal."""
    record, receipt, _ = _attested(attest, capsys)
    owner = receipt["attestation"]["owner"]
    authority = owner["authority"]
    if tamper == "reviewer_probe":
        owner.update(seat="claude-infra", area="infra-harness", stream_id=INFRA)
        owner.update(mapping_sha256="a" * 64, assignments_sha256="b" * 64)
        authority.update(stream_id=INFRA, session_id="session-invented", lease_id="lease-invented")
        authority["holder"] = {"agent": "claude", "harness": "claude-code", "instance_id": "claude-infra-1"}
    elif tamper == "foreign_seat":
        owner["seat"] = "muse-folk"
    elif tamper == "area":
        owner["area"] = "infra-harness"
    elif tamper == "lane":
        owner["stream_id"] = authority["stream_id"] = INFRA
    elif tamper == "task_initiator":
        owner["task_initiator"] = "muse-monitor"
    elif tamper == "invented_session":
        authority["session_id"] = "session-invented"
    elif tamper == "invented_lease":
        authority["lease_id"] = "lease-invented"
    elif tamper == "invented_fence":
        authority["fencing_token"] += 1
    else:
        owner[tamper.replace("_hash", "_sha256")] = "0" * 64
    save(attest["tasks"], record)
    _reader_refuses(attest, code)


@pytest.mark.parametrize("consistent", [False, True])
def test_changed_bound_initiator_refuses_removal(attest, capsys, consistent):
    """Blocker 2: the cohort pins initiators, and the lane is recomputed from them."""
    record, receipt, _ = _attested(attest, capsys)
    attest["successor"]["initiator"] = "claude-infra"
    save(attest["tasks"], attest["successor"])
    if consistent:
        # A forger who also rewrites the pinned cohort still fails the lane recomputation.
        for entry in receipt["attestation"]["cohort"]:
            if entry["task_id"] == "successor":
                entry["initiator"] = "claude-infra"
        save(attest["tasks"], record)
    _reader_refuses(attest, "FOREIGN_OWNER" if consistent else "cohort")


def test_remover_must_run_beneath_the_attested_holder(attest, capsys):
    """Blocker 2: an attestation is consumed only by the owning session's own process tree."""
    _attested(attest, capsys)
    lease = attest["monitor"]["streams"][MONITOR]
    lease["holder"] = dict(lease["holder"], process_id=FOREIGN_PID)
    _reader_refuses(attest, "HOLDER_UNPROVEN")


def _rollover(fx, monkeypatch):
    _set_lease_env(monkeypatch, SESSION_ID="session-next", LEASE_ID="lease-next", GENERATION="5", FENCING_TOKEN="18")
    fx["monitor"]["streams"][MONITOR] = monitor_lease()


def _map_revision(fx, monkeypatch, tmp_path):
    from scripts.fleet import terminal_abandon

    revised = tmp_path / "area_assignments.yaml"
    revised.write_bytes(terminal_abandon.AREA_ASSIGNMENTS.read_bytes() + b"\n# roster revision\n")
    monkeypatch.setattr(terminal_abandon, "AREA_ASSIGNMENTS", revised)


@pytest.mark.parametrize("change,code", [("rollover", "STALE_AUTHORITY"), ("map", "MAPPING_CHANGED")])
def test_stale_attestation_refuses_removal_until_the_owner_reissues(
    attest, monkeypatch, tmp_path, capsys, change, code
):
    _, first, _ = _attested(attest, capsys)
    if change == "rollover":
        _rollover(attest, monkeypatch)
    else:
        _map_revision(attest, monkeypatch, tmp_path)
    _reader_refuses(attest, code)
    assert attest_cli(attest) == 0
    dry = _out(capsys)
    assert dry["outcome"] == "would_record" and code in dry["reissues"], dry
    assert attest_cli(attest, apply=True) == 0
    result = _out(capsys)
    assert result["outcome"] == "recorded" and code in result["reissues"], result
    _, second, _ = _recorded(attest["fixture"])
    if change == "rollover":
        assert second["attestation"]["owner"]["authority"]["session_id"] == "session-next"
    else:
        assert (
            second["attestation"]["owner"]["assignments_sha256"] != first["attestation"]["owner"]["assignments_sha256"]
        )
    assert attest_cli(attest, apply=True) == 0
    assert _out(capsys)["outcome"] == "already_recorded"
    _remove(attest)


def test_reissue_still_refuses_a_different_decision(attest, monkeypatch, capsys):
    _attested(attest, capsys)
    _rollover(attest, monkeypatch)
    before = _files(attest["repo"])
    assert attest_cli(attest, apply=True, reason="a different disposition") == 2
    assert _out(capsys)["code"] == "ALREADY_RECORDED"
    assert _files(attest["repo"]) == before


def _pr_states(states):
    return lambda _root, branch: states.get(branch, ([], None))


@pytest.mark.parametrize(
    "state,code",
    [
        (([rw.PullRequestState(10700, "OPEN", "0" * 40)], None), "LIVE_OR_WANTED"),
        (([], "unavailable"), "ACTIVITY_UNKNOWN"),
    ],
)
def test_open_pr_on_another_bound_branch_refuses_removal(attest, monkeypatch, capsys, state, code):
    """Blocker 3: a successor bound to another branch gains a PR after the attestation."""
    attest["successor"]["worktree_branch"] = "codex/other-bound"
    save(attest["tasks"], attest["successor"])
    _attested(attest, capsys)
    queried = []

    def states(root, branch):
        queried.append(branch)
        return state if branch == "codex/other-bound" else ([], None)

    monkeypatch.setattr(rw, "_query_pr_states", states)
    _reader_refuses(attest, code)
    assert "codex/other-bound" in queried and "codex/boundary" in queried


def _reflog_only_commit(tree, head, name="lost.txt", text=b"work only the reflog still reaches\n"):
    """Commit unique work, then reset back: the commit stays reachable only from the tree's HEAD reflog."""
    (tree / name).write_bytes(text)
    _git(tree, "add", name)
    _git(tree, "commit", "-m", f"unique {name}")
    lost = _git(tree, "rev-parse", "HEAD")
    _git(tree, "reset", "--hard", head)
    return lost


@pytest.mark.parametrize("shape", ["needs_finalize", "detached", "reset_to_main"])
def test_reflog_only_commits_restore_from_a_clean_clone(attest, tmp_path, capsys, shape):
    """Blocker 4: restoring from the bundle gives back every commit the tree's own reflog reaches."""
    repo, tree = attest["repo"], attest["tree"]
    lost = _reflog_only_commit(tree, attest["head"])
    expected = {lost}
    if shape == "detached":
        _shape("detached", attest)
    elif shape == "reset_to_main":
        # The tree's own commit becomes reflog-only too; HEAD carries nothing new.
        expected.add(attest["head"])
        attest["head"] = _git(repo, "rev-parse", "main")
        _git(tree, "reset", "--hard", attest["head"])
    assert attest_cli(attest) == 0
    plan = _out(capsys)["preservation_plan"]
    assert plan["reflog_commits"] == len(expected) and plan["commit_bundle"] is True
    assert attest_cli(attest, apply=True) == 0
    assert _out(capsys)["outcome"] == "recorded"
    _, _, manifest = _recorded(attest["fixture"])
    bundle = repo / manifest["commit_bundle"]["path"]
    heads = _git(repo, "bundle", "list-heads", str(bundle)).splitlines()
    # A HEAD that main already contains needs no bundle ref of its own.
    assert (f"{attest['head']} HEAD" in heads) is (shape != "reset_to_main")
    assert {f"{oid} {output.REFLOG_BUNDLE_REF}{oid}" for oid in expected} <= set(heads)
    _remove(attest)
    restored = tmp_path / "restored"
    _git(repo, "clone", "--no-local", "--single-branch", "--branch", "main", str(repo), str(restored))
    for oid in expected:
        assert subprocess.run(["git", "cat-file", "-e", oid], cwd=restored, timeout=30).returncode != 0
    _git(restored, "fetch", str(bundle), f"{output.REFLOG_BUNDLE_REF}*:refs/restored/*")
    for oid in expected:
        assert _git(restored, "cat-file", "-t", oid) == "commit"
    assert _git(restored, "show", f"{lost}:lost.txt") == "work only the reflog still reaches"


def test_reflog_growth_after_attestation_refuses_removal_until_reissued(attest, capsys):
    _attested(attest, capsys)
    _reflog_only_commit(attest["tree"], attest["head"], name="later.txt", text=b"after the attestation\n")
    _reader_refuses(attest, "REFLOG_UNPRESERVED")
    assert attest_cli(attest, apply=True) == 0
    assert "REFLOG_UNPRESERVED" in _out(capsys)["reissues"]
    _remove(attest)


def test_unwalkable_reflog_is_a_typed_refusal(attest, capsys):
    """Completeness that cannot be established refuses instead of losing a commit."""
    tree = attest["tree"]
    log = _git(tree, "rev-parse", "--path-format=absolute", "--git-path", "logs/HEAD")
    with open(log, "ab") as handle:
        handle.write(f"{attest['head']} {'1' * 40} T <t@example.invalid> 1 +0000\treset: lost object\n".encode())
    before = _files(attest["repo"])
    for apply in (False, True):
        assert attest_cli(attest, apply=apply) == 2
        result = _out(capsys)
        assert result["code"] == "PRESERVATION_INVALID" and "completeness" in result["reason"], result
    _no_writes(attest, before)
