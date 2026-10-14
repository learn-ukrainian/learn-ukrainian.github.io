"""Supported owner writes, using disposable Git trees and canonical readers."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.fleet import ignored_task_output as output
from scripts.orchestration import reap_worktrees as rw
from tests.orchestration.test_worktree_output_chokepoint import boundary_tree as boundary_tree
from tests.test_continuation_worktree_reap import abandon_cohort as abandon_cohort
from tests.test_continuation_worktree_reap import same_branch_pending_cohort as same_branch_pending_cohort
from tests.test_reused_worktree_retention import cohort as cohort
from tests.test_reused_worktree_retention import save


@pytest.mark.parametrize("mode", ["file", "module"])
def test_cli_help_imports(mode, tmp_path):
    root = Path(__file__).resolve().parents[2]
    args = (
        [str(root / "scripts/fleet/terminal_abandon.py")]
        if mode == "file"
        else ["-m", "scripts.fleet.terminal_abandon"]
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, *args, "--help"],
        cwd=tmp_path if mode == "file" else root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--preservation-bundle" in result.stdout


@pytest.fixture
def writer_fixture(abandon_cohort, monkeypatch):
    repo, tree, tasks, creator, successor, _ = abandon_cohort
    receipt = creator.pop("worktree_abandon")
    creator["initiator"] = "claude-data"
    save(tasks, creator)
    monkeypatch.setenv("LU_RUNTIME_INITIATOR", "claude-data")
    monkeypatch.setenv("LU_RUNTIME_INITIATOR_SOURCE", "session_env")
    monkeypatch.setattr(rw.worktree_claims, "control_plane_root", lambda _: repo)
    monkeypatch.setattr(rw, "_has_active_ownership_claim", lambda *_: None)
    return repo, tree, tasks, creator, successor, repo / receipt["preservation"]["path"], receipt["head_sha"]


def invoke(fixture, **overrides):
    from scripts.fleet import terminal_abandon

    _, _, _, creator, _, bundle, head = fixture
    values = dict(task_id=creator["task_id"], head_sha=head, reason="superseded implementation", bundle=bundle)
    values.update(overrides)
    return terminal_abandon.main(
        [
            "--task-id",
            values["task_id"],
            "--head",
            values["head_sha"],
            "--reason",
            values["reason"],
            "--preservation-bundle",
            str(values["bundle"]),
        ]
    )


def test_written_record_passes_both_existing_readers(writer_fixture, capsys):
    repo, tree, tasks, creator, _, _, head = writer_fixture
    assert invoke(writer_fixture) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "recorded" and result["head_sha"] == head
    matches = output.matching_worktree_records(tree, tasks, repo_root=repo, publish_cache=False)
    path, record = output.terminal_abandon_creator(matches, tree, primary=repo, tasks_dir=tasks)
    assert path == tasks / "boundary.json"
    assert record == dict(creator, worktree_abandon=record["worktree_abandon"])
    assert record["worktree_abandon"]["schema"] == "terminal-abandon.v1"
    assert rw._terminal_abandon_matches(repo, tree) == matches
    preservation = record["worktree_abandon"]["preservation"]
    manifest_bytes = (repo / preservation["path"]).read_bytes()
    assert hashlib.sha256(manifest_bytes).hexdigest() == preservation["sha256"]
    assert json.loads(manifest_bytes)["schema"] == "terminal-abandon-preservation.v1"


@pytest.mark.parametrize(
    "failure,code",
    [
        ("bundle_hash", "PRESERVATION_INVALID"),
        ("caller", "NOT_CREATOR"),
        ("unknown_caller", "NOT_CREATOR"),
        ("head", "HEAD_MISMATCH"),
        ("no_creator", "CREATOR_RECOVERY_REQUIRED"),
        ("no_record", "CREATOR_RECOVERY_REQUIRED"),
        ("running", "LIVE_OR_WANTED"),
        ("keep", "LIVE_OR_WANTED"),
        ("pid", "LIVE_OR_WANTED"),
        ("lease", "LIVE_OR_WANTED"),
        ("active", "LIVE_OR_WANTED"),
        ("monitor_unknown", "ACTIVITY_UNKNOWN"),
        ("cwd", "LIVE_OR_WANTED"),
        ("cwd_unknown", "ACTIVITY_UNKNOWN"),
        ("rollover", "LIVE_OR_WANTED"),
        ("patch_changed", "PRESERVATION_INVALID"),
        ("open_pr", "LIVE_OR_WANTED"),
        ("pr_unknown", "ACTIVITY_UNKNOWN"),
        ("blank_reason", "INVALID_INPUT"),
        ("short_head", "INVALID_INPUT"),
        ("path_task_id", "INVALID_INPUT"),
        ("missing_bundle", "INVALID_INPUT"),
        ("symlink_bundle", "INVALID_INPUT"),
        ("fifo_bundle", "INVALID_INPUT"),
        ("task_lock_symlink", "INVALID_INPUT"),
        ("bundle_not_object", "PRESERVATION_INVALID"),
        ("bundle_in_tasks", "INVALID_INPUT"),
        ("unmerged_index", "PRESERVATION_INVALID"),
        ("index_lock", "PRESERVATION_INVALID"),
        ("no_initiator", "NOT_CREATOR"),
        ("no_nonce", "PRESERVATION_INVALID"),
        ("manifest_collision", "PRESERVATION_INVALID"),
    ],
)
def test_refusal_writes_no_record_or_manifest(writer_fixture, monkeypatch, capsys, failure, code):
    repo, tree, tasks, creator, successor, bundle, _ = writer_fixture
    overrides = {}
    if failure == "bundle_hash":
        manifest = json.loads(bundle.read_bytes())
        (repo / manifest["head_patch"]["path"]).write_bytes(b"corrupt patch")
    elif failure == "caller":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "claude-harness")
    elif failure == "unknown_caller":
        monkeypatch.setenv("LU_RUNTIME_INITIATOR", "unknown")
    elif failure == "head":
        overrides["head_sha"] = "0" * 40
    elif failure == "no_record":
        (tasks / "boundary.json").unlink()
    elif failure == "no_creator":
        creator.pop("ignored_output_baseline")
        save(tasks, creator)
    elif failure in {"running", "keep", "pid", "lease"}:
        successor.update(
            {
                "running": {"status": "running"},
                "keep": {"keep_worktree": True},
                "pid": {"pid": os.getpid()},
                "lease": {"lease_state": "active"},
            }[failure]
        )
        save(tasks, successor)
    elif failure == "active":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: {successor["task_id"]})
    elif failure == "monitor_unknown":
        monkeypatch.setattr(rw, "_active_task_ids", lambda: None)
    elif failure == "cwd":
        monkeypatch.setattr(rw, "_live_cwd_paths", lambda _: {tree / "ignored"})
    elif failure == "cwd_unknown":
        monkeypatch.setattr(rw, "_live_cwd_paths", lambda _: None)
    elif failure == "rollover":
        monkeypatch.setattr(rw, "_has_active_rollover_lease", lambda *_: "active rollover")
    elif failure == "patch_changed":
        (tree / "README.md").write_bytes(b"new work since preservation")
    elif failure == "open_pr":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([rw.PullRequestState(1, "OPEN", "0" * 40)], None))
    elif failure == "pr_unknown":
        monkeypatch.setattr(rw, "_query_pr_states", lambda *_: ([], "unavailable"))
    elif failure == "blank_reason":
        overrides["reason"] = " "
    elif failure == "short_head":
        overrides["head_sha"] = "abc"
    elif failure == "path_task_id":
        overrides["task_id"] = "../boundary"
    elif failure == "missing_bundle":
        overrides["bundle"] = bundle.with_name("missing.json")
    elif failure in {"symlink_bundle", "fifo_bundle"}:
        bad = bundle.with_name("bad-bundle")
        if failure == "symlink_bundle":
            bad.symlink_to(bundle)
        else:
            os.mkfifo(bad)
        overrides["bundle"] = bad
    elif failure == "task_lock_symlink":
        (tasks / "boundary.json.lock").symlink_to(bundle)
    elif failure == "bundle_not_object":
        bundle.write_text("[]")
    elif failure == "bundle_in_tasks":
        bad = tasks / "bundle.json"
        bad.write_bytes(bundle.read_bytes())
        overrides["bundle"] = bad
    elif failure == "unmerged_index":
        monkeypatch.setattr(output.artifacts, "_git_paths", lambda *_: ["unmerged"])
    elif failure == "index_lock":
        from tests.orchestration.test_worktree_claims_cli import _git

        index_lock = _git(tree, "rev-parse", "--path-format=absolute", "--git-path", "index.lock")
        from pathlib import Path

        Path(index_lock).write_bytes(b"")
    elif failure == "no_initiator":
        creator.pop("initiator")
        save(tasks, creator)
    elif failure == "no_nonce":
        creator.pop("run_nonce")
        save(tasks, creator)
    elif failure == "manifest_collision":
        manifest = json.loads(bundle.read_bytes())
        encoded = (json.dumps(manifest, sort_keys=True) + "\n").encode()
        digest = hashlib.sha256(encoded).hexdigest()
        bundle.with_name(f"terminal-abandon-boundary-{digest}.json").write_bytes(b"collision")
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture, **overrides) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "refused" and result["code"] == code
    if failure in {"no_creator", "no_record"}:
        assert "recover authentic dispatch creator" in result["reason"]
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before
    assert tree.exists()


def test_repeat_is_idempotent(writer_fixture, capsys):
    repo, *_ = writer_fixture
    assert invoke(writer_fixture) == 0
    capsys.readouterr()
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "already_recorded"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before


def test_existing_record_cannot_be_overwritten(writer_fixture, capsys):
    repo, *_ = writer_fixture
    assert invoke(writer_fixture) == 0
    capsys.readouterr()
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture, reason="different disposition") == 2
    assert json.loads(capsys.readouterr().out)["code"] == "ALREADY_RECORDED"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before


def test_patch_mutation_during_final_activity_probe_refuses(writer_fixture, monkeypatch, capsys):
    repo, tree, tasks, *_ = writer_fixture
    calls = 0

    def active():
        nonlocal calls
        calls += 1
        if calls == 2:
            (tree / "README.md").write_bytes(b"arrived during activity probe")
        return set()

    monkeypatch.setattr(rw, "_active_task_ids", active)
    before = {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")}
    assert invoke(writer_fixture) == 2
    assert json.loads(capsys.readouterr().out)["code"] == "PRESERVATION_INVALID"
    assert {p: p.read_bytes() for p in (repo / "batch_state").rglob("*.json")} == before
    assert not list((repo / "batch_state/abandon/boundary").glob(".terminal-abandon-*"))
    assert "worktree_abandon" not in json.loads((tasks / "boundary.json").read_bytes())


def test_bundle_can_contain_only_patch_metadata(writer_fixture, capsys):
    *_, bundle, _ = writer_fixture
    manifest = json.loads(bundle.read_bytes())
    bundle.write_text(
        json.dumps({key: manifest[key] for key in ("base_sha", "head_patch", "index_patch", "working_patch")})
    )
    assert invoke(writer_fixture) == 0
    assert json.loads(capsys.readouterr().out)["outcome"] == "recorded"
