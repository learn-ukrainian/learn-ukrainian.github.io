"""Each formerly bypassing remover preserves real ignored bytes (#9645)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from scripts.ai_agent_bridge import _acp_execution
from scripts.ci import data_tier
from scripts.fleet import ignored_task_output, sibling_git
from scripts.orchestration import worktree_claims
from scripts.orchestration.fleet_repos import FleetRepo
from scripts.orchestration.task_family import git_safety
from tests.orchestration.test_worktree_claims_cli import _git, _linked, _primary, _record

CALLERS = ["acp", "data-tier", "sibling", "task-family", "cli"]


def remove(caller, primary, checkout, capsys, monkeypatch):
    if caller == "acp":
        return (
            _acp_execution._remove_runtime_worktree(
                primary,
                checkout,
                owner_task_id="done-output",
                reason="ACP teardown",
                dirty_probe=_acp_execution._own_runtime_is_scratch,
            ).action
            == "removed"
        )
    if caller == "data-tier":
        try:
            data_tier.remove_test_worktree(primary, checkout)
        except data_tier.DataTierError as exc:
            assert "artifact preservation failed:" in str(exc)
            return False
        return True
    if caller == "task-family":
        try:
            git_safety.remove_unclaimed_worktree(primary, checkout)
        except git_safety.GitSafetyError as exc:
            assert "artifact preservation failed:" in str(exc)
            return False
        return True
    if caller == "sibling":
        public = primary.parent / "public"
        public.mkdir()
        _git(public, "init", "-b", "main")
        record = primary / "batch_state/tasks/done-output.json"
        if record.exists():
            public_tasks = public / "batch_state/tasks"
            public_tasks.mkdir(parents=True)
            (public_tasks / record.name).write_bytes(record.read_bytes())
        # Real independent metadata and the already-established dispatch lock.
        with worktree_claims.worktree_lock(checkout, lock_dir=public / ".git" / worktree_claims.LOCK_DIR_NAME):
            pass
        monkeypatch.setattr(
            sibling_git,
            "load_fleet_repos",
            lambda: {"fixture": FleetRepo("fixture", "fixture/sibling", primary.name, "private")},
        )
        monkeypatch.setattr(sibling_git, "_registry_transport", lambda _key: "ssh")
        _git(primary, "remote", "add", "origin", "git@github.com:fixture/sibling.git")
        with sibling_git.git_session() as git:
            repo = sibling_git.resolve_repository("fixture", public, git)
            try:
                sibling_git.worktree_remove(repo, public, git, str(checkout))
            except sibling_git.Refusal as exc:
                assert "local work preserved" in str(exc)
                return False
        return True
    code = worktree_claims.main(["remove", str(checkout), "--json"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    if code == worktree_claims.EXIT_REMOVED:
        assert "Preserved " in captured.err
    else:
        assert "artifact preservation failed:" in captured.err
    if code != worktree_claims.EXIT_REMOVED:
        assert result["action"] == "skipped"
        assert "artifact preservation failed:" in result["reason"]
    return code == worktree_claims.EXIT_REMOVED


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("failure", [None, "cap", "copy"])
@pytest.mark.parametrize("record_exists", [True, False])
def test_all_removers_preserve_output_or_retain_checkout(tmp_path, monkeypatch, capsys, caller, failure, record_exists):
    primary = _primary(tmp_path)
    # Exclude via shared Git metadata, covering no-checkout ACP runtimes too.
    with (primary / ".git/info/exclude").open("a") as handle:
        handle.write(".cache/\n")
    checkout = _linked(primary, "codex/done-output")
    payload = b"new ignored transcription\n"
    source = checkout / ".cache/transcriptions/page.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(payload)
    if record_exists:
        _record(primary, "done-output", status="done", worktree_path=str(checkout), started_at="2000-01-01T00:00:00Z")
    assert _git(checkout, "status", "--porcelain") == ""
    if failure == "cap":
        monkeypatch.setattr(ignored_task_output, "MAX_PRESERVED_BYTES", len(payload) - 1)
    if failure == "copy":

        def fail_copy(*_args):
            raise OSError("copy denied")

        monkeypatch.setattr(ignored_task_output.artifacts, "_copy_verified", fail_copy)

    calls = []
    original = ignored_task_output.preserve_worktree_artifacts

    def preserve_once(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", preserve_once)
    removed = remove(caller, primary, checkout, capsys, monkeypatch)
    assert calls == [checkout]
    if failure:
        assert not removed and checkout.exists()
        assert source.read_bytes() == payload
        return
    assert removed and not checkout.exists()
    destination = primary.parent / "public" if caller == "sibling" else primary
    copies = list((destination / "batch_state/preserved").glob("*/*/.cache/transcriptions/page.txt"))
    assert len(copies) == 1
    assert copies[0].read_bytes() == payload
    assert hashlib.sha256(copies[0].read_bytes()).digest() == hashlib.sha256(payload).digest()


def test_active_claim_prevents_preservation_and_removal(tmp_path, monkeypatch):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/active")
    _record(primary, "active", status="running", worktree_path=str(checkout))

    def forbidden(*_args, **_kwargs):
        pytest.fail("preservation ran before active-claim refusal")

    monkeypatch.setattr(ignored_task_output, "preserve_worktree_artifacts", forbidden)
    result = worktree_claims.remove_unclaimed_worktree(
        checkout,
        repo_root=primary,
        reason="test",
        owner_task_id=None,
    )
    assert result.action == "skipped" and checkout.exists()
    assert "active task" in result.reason


def test_raw_removal_checks_preservation_without_adapter(tmp_path, monkeypatch):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/raw")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"raw remover output")
    receipt = {}
    with worktree_claims.worktree_lock(checkout, lock_dir=worktree_claims.repository_lock_dir(primary)):
        error = worktree_claims.git_worktree_remove(
            primary,
            checkout,
            force=True,
            preservation_receipt=receipt,
        )
    assert error is None and not checkout.exists()
    assert (Path(receipt["location"]) / ".cache/report.txt").read_bytes() == b"raw remover output"
    assert receipt["record_update"] == "skipped_missing_record"


def test_retry_after_git_refusal_preserves_both_versions_and_removes(tmp_path):
    primary = _primary(tmp_path)
    checkout = _linked(primary, "codex/retry-9645")
    (primary / ".git/info/exclude").write_text(".cache/\n")
    source = checkout / ".cache/report.txt"
    source.parent.mkdir()
    source.write_bytes(b"first")
    first, second = {}, {}
    with worktree_claims.worktree_lock(checkout, lock_dir=worktree_claims.repository_lock_dir(primary)):
        error = worktree_claims.git_worktree_remove(
            primary, checkout, force=False, preservation_receipt=first,
            git_runner=lambda _root, argv: subprocess.CompletedProcess(argv, 1, "", "injected Git refusal"),
        )
        assert error and checkout.exists()
        source.write_bytes(b"second")
        error = worktree_claims.git_worktree_remove(
            primary, checkout, force=False, preservation_receipt=second,
        )
    assert error is None and not checkout.exists()
    assert first["location"] != second["location"]
    assert (Path(first["location"]) / ".cache/report.txt").read_bytes() == b"first"
    assert (Path(second["location"]) / ".cache/report.txt").read_bytes() == b"second"
