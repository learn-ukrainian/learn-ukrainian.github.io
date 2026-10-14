"""Four terminal-abandon coverage classes, using disposable checkout proofs."""

import hashlib
import json
import tarfile

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.fleet import terminal_abandon
from scripts.orchestration import reap_worktrees as rw
from tests.fleet.test_terminal_abandon import _recorded, _refused_removal, invoke
from tests.fleet.test_terminal_abandon import succession as succession
from tests.fleet.test_terminal_abandon import writer_fixture as writer_fixture
from tests.orchestration.test_worktree_claims_cli import _git
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


def _remove(fixture):
    repo, tree, *_ = fixture
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


def test_detached_head_bundle_restores_after_removal(succession, tmp_path, capsys):
    fixture, _ = succession
    repo, tree, _, _, _, _, head = fixture
    _git(tree, "checkout", "--detach", head)
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, receipt, manifest = _recorded(fixture)
    assert receipt["succession"]["branch"] is None
    bundle = manifest["detached_bundle"]
    payload = (repo / bundle["path"]).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == bundle["sha256"]
    _remove(fixture)
    restored = tmp_path / "restored"
    _git(repo, "clone", str(repo / bundle["path"]), str(restored))
    assert _git(restored, "rev-parse", "HEAD") == head


def test_detached_dirty_tracked_refuses(succession, capsys):
    fixture, _ = succession
    _, tree, *_ = fixture
    _git(tree, "checkout", "--detach")
    (tree / "README.md").write_bytes(b"dirty tracked data")
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_detached_concealed_tracked_change_refuses(succession, capsys, flag):
    fixture, _ = succession
    _, tree, *_ = fixture
    _git(tree, "checkout", "--detach")
    _git(tree, "update-index", flag, "README.md")
    (tree / "README.md").write_bytes(b"concealed tracked data")
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"


def test_detached_bundle_corruption_refuses_removal(succession, capsys):
    fixture, _ = succession
    repo, tree, *_ = fixture
    _git(tree, "checkout", "--detach")
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    (repo / manifest["detached_bundle"]["path"]).write_bytes(b"corrupt bundle")
    _refused_removal(fixture, "digest")


@pytest.mark.parametrize("status", ["done", "needs_finalize"])
def test_retained_merged_head_records_and_removes(succession, monkeypatch, capsys, status):
    fixture, _ = succession
    _, _, tasks, creator, successor, _, head = fixture
    for record in (creator, successor):
        record.update(status=status, keep_worktree=True)
        save(tasks, record)
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(10614, "MERGED", head)], None))
    assert invoke(fixture) == 0
    capsys.readouterr()
    record, receipt, _ = _recorded(fixture)
    assert record["keep_worktree"] is True
    assert receipt["merged_pr"]["head_sha"] == head
    _remove(fixture)


@pytest.mark.parametrize("bad", ["unmerged_head", "open_pr", "live_pid", "live_lease", "unknown"])
def test_merged_retention_still_refuses_unproved_or_live(succession, monkeypatch, capsys, bad):
    fixture, _ = succession
    repo, _, tasks, creator, successor, _, head = fixture
    creator.update(keep_worktree=True, status="needs_finalize")
    if bad == "live_pid":
        import os

        successor["pid"] = os.getpid()
    if bad == "live_lease":
        successor["lease_state"] = "active"
    save(tasks, creator)
    save(tasks, successor)
    pr_head = _git(repo, "rev-parse", "main") if bad == "unmerged_head" else head
    state = "OPEN" if bad == "open_pr" else "MERGED"
    monkeypatch.setattr(
        rw,
        "_query_pr_states",
        lambda *_: ([rw.PullRequestState(10614, state, pr_head)], "unknown" if bad == "unknown" else None),
    )
    assert invoke(fixture) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["code"] in {"LIVE_OR_WANTED", "ACTIVITY_UNKNOWN"}
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())


def test_merged_proof_rechecked_at_removal(succession, monkeypatch, capsys):
    fixture, _ = succession
    repo, _, tasks, creator, _, _, head = fixture
    creator["keep_worktree"] = True
    save(tasks, creator)
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(10614, "MERGED", head)], None))
    assert invoke(fixture) == 0
    capsys.readouterr()
    other = _git(repo, "rev-parse", "main")
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(10614, "MERGED", other)], None))
    _refused_removal(fixture, "merged")


@pytest.mark.parametrize("relation", ["ancestor", "patch-equivalent"])
def test_merged_containment_or_patch_equivalence_with_output(succession, monkeypatch, capsys, relation):
    fixture, _ = succession
    repo, tree, tasks, creator, _, _, head = fixture
    creator.update(keep_worktree=True, status="needs_finalize")
    save(tasks, creator)
    if relation == "patch-equivalent":
        _git(repo, "cherry-pick", head)
        # The same patch has a distinct commit because its parent is rewritten.
        _git(repo, "commit", "--amend", "-m", "equivalent merge")
    else:
        _git(repo, "merge", "--ff-only", head)
        (repo / "additional.txt").write_text("merged successor")
        _git(repo, "add", "additional.txt")
        _git(repo, "commit", "-m", "merged successor")
    merged = _git(repo, "rev-parse", "HEAD")
    assert merged != head
    monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(10614, "MERGED", merged)], None))
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, receipt, _ = _recorded(fixture)
    assert receipt["merged_pr"]["relation"] == relation
    assert (tree / "untracked.txt").exists()
    _remove(fixture)


def test_merged_proof_changes_before_publication_refuses(succession, monkeypatch, capsys):
    fixture, _ = succession
    repo, _, tasks, creator, _, _, head = fixture
    creator["keep_worktree"] = True
    save(tasks, creator)
    calls = 0

    def query(*_):
        nonlocal calls
        calls += 1
        sha = head if calls <= 2 else _git(repo, "rev-parse", "main")
        return [rw.PullRequestState(10614, "MERGED", sha)], None

    monkeypatch.setattr(rw, "_query_pr_states", query)
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())


def test_output_tar_is_independently_retrievable(succession, capsys):
    fixture, _ = succession
    repo, tree, *_ = fixture
    (tree / "ignored/link").symlink_to("missing-target")
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    archive = manifest["output"]["archive"]
    payload = (repo / archive["path"]).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == archive["sha256"]
    _remove(fixture)
    with tarfile.open(repo / archive["path"], "r:") as saved:
        assert saved.extractfile("untracked.txt").read() == b"untracked unique bytes"
        assert saved.extractfile("ignored/output.txt").read() == b"current output"
        assert saved.extractfile("ignored/link").read() == b"symlink\nmissing-target"
    assert output.verify_retrieval(repo, manifest["output"]) == manifest["output"]["content_sha256"]


def test_sparse_absent_index_entries_do_not_refuse_output_archive(succession, capsys):
    fixture, _ = succession
    repo, tree, *_ = fixture
    _git(tree, "update-index", "--skip-worktree", "README.md")
    (tree / "README.md").unlink()
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    assert [entry["path"] for entry in manifest["output"]["paths"]] == ["ignored/output.txt", "untracked.txt"]
    _remove(fixture)
    assert output.verify_retrieval(repo, manifest["output"]) == manifest["output"]["content_sha256"]


def test_sparse_path_materialized_after_capture_refuses(succession, monkeypatch, capsys):
    fixture, _ = succession
    _, tree, *_ = fixture
    _git(tree, "update-index", "--skip-worktree", "README.md")
    (tree / "README.md").unlink()
    calls = 0

    def active():
        nonlocal calls
        calls += 1
        if calls == 2:
            (tree / "README.md").write_bytes(b"new hidden output")
        return set()

    monkeypatch.setattr(rw, "_active_task_ids", active)
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"


def test_source_pr_opened_during_preservation_refuses(succession, monkeypatch, capsys):
    fixture, _ = succession
    _, _, tasks, *_ = fixture
    calls = 0

    def query(*_):
        nonlocal calls
        calls += 1
        return ([rw.PullRequestState(10614, "OPEN", fixture[-1])] if calls > 1 else []), None

    monkeypatch.setattr(rw, "_query_pr_states", query)
    assert invoke(fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "LIVE_OR_WANTED"
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())


def test_output_over_cap_names_limit(succession, monkeypatch, capsys):
    fixture, _ = succession
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", 1)
    assert invoke(fixture) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["code"] == "PRESERVATION_LIMIT"
    assert "1 bytes" in result["reason"]


def test_output_at_cap_succeeds_and_archive_corruption_refuses(succession, monkeypatch, capsys):
    fixture, _ = succession
    repo, tree, _, creator, *_ = fixture
    size = sum(entry["size"] for entry in output._abandon_output_inventory(tree, primary=repo, record=creator))
    monkeypatch.setattr(output, "MAX_PRESERVED_BYTES", size)
    assert invoke(fixture) == 0
    capsys.readouterr()
    _, _, manifest = _recorded(fixture)
    archive = repo / manifest["output"]["archive"]["path"]
    archive.write_bytes(b"corrupt archive")
    _refused_removal(fixture, "not retrievable")


def _archived_creator(fixture):
    _, _, tasks, creator, *_ = fixture
    archive = tasks / "archive"
    archive.mkdir()
    source = archive / "boundary.json"
    source.write_text(json.dumps(creator))
    creator.pop("ignored_output_baseline")
    save(tasks, creator)
    return source


def _recover(fixture):
    _, _, _, creator, _, bundle, head = fixture
    return terminal_abandon.main(
        [
            "--task-id",
            creator["task_id"],
            "--head",
            head,
            "--reason",
            "superseded implementation",
            "--preservation-bundle",
            str(bundle),
            "--recover-creator",
        ]
    )


def test_creator_recovery_uses_verified_archived_attempt(succession, capsys):
    fixture, _ = succession
    source = _archived_creator(fixture)
    assert _recover(fixture) == 0
    capsys.readouterr()
    repo, *_ = fixture
    record, receipt, _ = _recorded(fixture)
    assert record["run_nonce"] == "creation-nonce"
    assert receipt["creator_recovery"] == {
        "path": source.relative_to(repo).as_posix(),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    before = source.read_bytes()
    assert _recover(fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "already_recorded"
    assert source.read_bytes() == before
    _remove(fixture)


@pytest.mark.parametrize("bad", ["nonce", "directory", "initiator", "missing", "missing_task"])
def test_creator_recovery_unverifiable_archive_refuses_typed(succession, capsys, bad):
    fixture, _ = succession
    source = _archived_creator(fixture)
    saved = json.loads(source.read_bytes())
    if bad == "nonce":
        saved["run_nonce"] = "different-run"
    elif bad == "directory":
        saved["ignored_output_baseline"]["directory_identity"] = [0, 0]
    elif bad == "initiator":
        saved["initiator"] = "unknown-seat"
    if bad in {"missing", "missing_task"}:
        source.unlink()
        if bad == "missing_task":
            (fixture[2] / "boundary.json").unlink()
    else:
        source.write_text(json.dumps(saved))
    assert _recover(fixture) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["code"] == "CREATOR_RECOVERY_REQUIRED"
    assert "manual item boundary" in result["reason"]


def test_creator_recovery_archive_drift_refuses_removal(succession, capsys):
    fixture, _ = succession
    source = _archived_creator(fixture)
    assert _recover(fixture) == 0
    capsys.readouterr()
    source.write_bytes(source.read_bytes() + b"\n")
    _refused_removal(fixture, "recovery")
