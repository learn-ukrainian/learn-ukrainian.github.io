"""``python -m scripts.orchestration.worktree_claims remove`` and its shell callers (#8610 r5)."""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.orchestration import worktree_claims

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=30
    ).stdout.strip()


def _primary(tmp_path: Path) -> Path:
    primary = tmp_path / "primary"
    primary.mkdir()
    _git(primary, "init", "-b", "main")
    _git(primary, "config", "user.email", "claims@example.invalid")
    _git(primary, "config", "user.name", "Claims Test")
    (primary / ".gitignore").write_text(".venv/\n.worktrees/\nbatch_state/\n", encoding="utf-8")
    _git(primary, "add", ".gitignore")
    _git(primary, "commit", "-m", "base")
    return primary


def _linked(primary: Path, branch: str, path: Path | None = None) -> Path:
    worktree = path or primary / ".worktrees" / "dispatch" / branch
    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(primary, "worktree", "add", "-b", branch, str(worktree))
    return worktree


def _record(primary: Path, task_id: str, **fields: object) -> None:
    tasks = primary / "batch_state" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    (tasks / f"{task_id}.json").write_text(json.dumps({"task_id": task_id, **fields}), encoding="utf-8")


def _remove(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = worktree_claims.main(["remove", *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_removes_an_unclaimed_linked_worktree_and_keeps_its_branch(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-1")
    _record(primary, "impl-1", status="done", worktree_path=str(worktree))

    code, out, err = _remove(capsys, str(worktree))

    assert (code, err) == (worktree_claims.EXIT_REMOVED, "")
    assert out == f"removed: {worktree} (operator cleanup)\n"
    assert not worktree.exists()
    assert _git(primary, "branch", "--list", "codex/impl-1")


@pytest.mark.parametrize("force", [False, True])
def test_sibling_removal_without_tmpdir_guards_only_force(tmp_path, monkeypatch, force):
    monkeypatch.delenv("TMPDIR", raising=False)
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/sibling", tmp_path / "sibling")

    result = worktree_claims.remove_unclaimed_worktree(
        worktree, repo_root=primary, reason="sibling regression", owner_task_id=None, force=force
    )

    if force:
        assert result.action == "error"
        assert "delete guard refused" in result.error
        assert worktree.exists()
    else:
        assert result.action == "removed", result
        assert not worktree.exists()


def test_refuses_while_an_unfinished_task_claims_the_worktree(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-2")
    _record(primary, "review-2", status="spawning", worktree_path=str(worktree))

    code, out, err = _remove(capsys, str(worktree), "--reason", "wt.sh clean 2")

    assert (code, out) == (worktree_claims.EXIT_REFUSED, "")
    assert err == f"refused: {worktree}: worktree claimed by active task review-2\n"
    assert worktree.exists()


def _fleet(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    """Public primary and its ``infra-private`` sibling checkout beside it (#8624)."""
    public = _primary(tmp_path)
    sibling = tmp_path / "learn-ukrainian-infra-private"
    sibling.mkdir()
    _git(sibling, "init", "-b", "main")
    _git(sibling, "config", "user.email", "claims@example.invalid")
    _git(sibling, "config", "user.name", "Claims Test")
    (sibling / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    _git(sibling, "add", ".gitignore")
    _git(sibling, "commit", "-m", "base")
    monkeypatch.setattr(worktree_claims, "public_primary_root", lambda: public)
    return public, sibling


def test_control_plane_root_is_the_public_primary_only_for_fleet_siblings(tmp_path, monkeypatch):
    public, sibling = _fleet(tmp_path, monkeypatch)
    linked = _linked(sibling, "codex/impl-cp")
    stranger = tmp_path / "stranger"
    stranger.mkdir()
    _git(stranger, "init", "-b", "main")

    assert worktree_claims.control_plane_root(public) == public.resolve()
    assert worktree_claims.control_plane_root(sibling) == public.resolve()
    assert worktree_claims.control_plane_root(linked) == public.resolve()
    assert worktree_claims.control_plane_root(stranger) == stranger.resolve()


def _malformed_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the real loader at a syntactically invalid ``fleet_repos.yaml`` (no mock of the loader)."""
    from scripts.orchestration import fleet_repos

    bad = tmp_path / "malformed_fleet_repos.yaml"
    bad.write_text("repos: {infra-private: [unclosed\n", encoding="utf-8")
    monkeypatch.setattr(fleet_repos, "_CONFIG_PATH", bad)


def test_control_plane_root_raises_control_plane_error_on_malformed_catalog_yaml(tmp_path, monkeypatch):
    _fleet(tmp_path, monkeypatch)
    _malformed_catalog(tmp_path, monkeypatch)

    with pytest.raises(worktree_claims.ControlPlaneError, match="catalog unreadable"):
        worktree_claims.control_plane_root(tmp_path / "learn-ukrainian-infra-private")


def test_remove_unclaimed_worktree_never_raises_on_malformed_catalog_yaml(tmp_path, monkeypatch):
    _public, sibling = _fleet(tmp_path, monkeypatch)
    worktree = _linked(sibling, "codex/impl-sib-badyaml")
    _malformed_catalog(tmp_path, monkeypatch)

    result = worktree_claims.remove_unclaimed_worktree(
        worktree, repo_root=sibling, reason="test", owner_task_id=None
    )

    assert result.action == "skipped"
    assert result.reason == worktree_claims.LOCK_UNAVAILABLE
    assert worktree.exists()


def test_owning_repo_root_follows_the_worktree_pointer_and_defaults_otherwise(tmp_path, monkeypatch):
    public, sibling = _fleet(tmp_path, monkeypatch)
    linked = _linked(sibling, "codex/impl-own")

    assert worktree_claims.owning_repo_root(linked, default=public) == sibling.resolve()
    assert worktree_claims.owning_repo_root(sibling, default=public) == public
    assert worktree_claims.owning_repo_root(tmp_path / "missing", default=public) == public


def test_sibling_repo_worktree_with_a_live_public_claim_is_not_removed(tmp_path, capsys, monkeypatch):
    """#8624: the CLI reads the claim dispatch wrote on the public primary, not the sibling's own batch_state."""
    public, sibling = _fleet(tmp_path, monkeypatch)
    worktree = _linked(sibling, "codex/impl-sib")
    _record(public, "review-sib", status="spawning", worktree_path=str(worktree))

    code, out, err = _remove(capsys, str(worktree))

    assert (code, out) == (worktree_claims.EXIT_REFUSED, "")
    assert err == f"refused: {worktree}: worktree claimed by active task review-sib\n"
    assert worktree.exists()


def test_sibling_repo_worktree_is_removed_once_the_public_claim_is_finished(tmp_path, capsys, monkeypatch):
    public, sibling = _fleet(tmp_path, monkeypatch)
    worktree = _linked(sibling, "codex/impl-sib-free")
    _record(public, "impl-sib-free", status="done", worktree_path=str(worktree))

    code, _out, err = _remove(capsys, str(worktree))

    assert (code, err) == (worktree_claims.EXIT_REMOVED, "")
    assert not worktree.exists()
    assert _git(sibling, "branch", "--list", "codex/impl-sib-free")


def test_unreadable_fleet_catalog_refuses_removal(tmp_path, capsys, monkeypatch):
    _public, sibling = _fleet(tmp_path, monkeypatch)
    worktree = _linked(sibling, "codex/impl-sib-nocat")

    def unreadable():
        raise worktree_claims.FleetRepoError("catalog missing")

    monkeypatch.setattr(worktree_claims, "load_fleet_repos", unreadable)

    code, _out, err = _remove(capsys, str(worktree))

    assert code == worktree_claims.EXIT_REFUSED
    assert "worktree lock unavailable" in err
    assert worktree.exists()


def test_owner_exemption_covers_only_the_owner_record(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-3")
    _record(primary, "impl-3", status="failed", run_nonce="owner-run-3", worktree_path=str(worktree), worktree_reused=False)

    code, out, _err = _remove(capsys, str(worktree), "--owner-task-id", "impl-3", "--reason", "rb2 cleanup")

    assert code == worktree_claims.EXIT_REMOVED
    assert out == f"removed: {worktree} (rb2 cleanup (owner task impl-3))\n"
    assert not worktree.exists()


_DISPATCHER_RECORD = {"schema_version": 2, "worktree_start_sha": "a" * 40, "options": {}, "provider_pgid": None}


def test_dispatcher_record_proves_creation_without_the_reused_flag(tmp_path, capsys):
    """A dispatcher (schema 2) record never writes ``worktree_reused``; its start sha is the proof."""
    primary = _primary(tmp_path)
    worktree = _linked(primary, "claude/impl-5")
    (worktree / ".venv").mkdir()
    (worktree / ".venv" / "ignored").write_text("ignored", encoding="utf-8")
    _record(
        primary, "impl-5", status="timeout", run_nonce="owner-run-5", worktree_path=str(worktree),
        worktree_branch="claude/impl-5", **_DISPATCHER_RECORD,
    )

    code, out, _err = _remove(capsys, str(worktree), "--owner-task-id", "impl-5")

    assert code == worktree_claims.EXIT_REMOVED
    assert out.startswith(f"removed: {worktree}")
    assert not worktree.exists()
    assert _git(primary, "branch", "--list", "claude/impl-5")


@pytest.mark.parametrize(
    "overrides",
    [
        {"options": {"cwd": "/borrowed"}},
        {"worktree_start_sha": None},
        {"schema_version": 1},
        {"worktree_reused": True},
    ],
)
def test_dispatcher_record_proof_refuses_a_borrowed_or_unproven_checkout(tmp_path, capsys, overrides):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "claude/impl-6")
    _record(
        primary, "impl-6", status="timeout", run_nonce="owner-run-6", worktree_path=str(worktree),
        **{**_DISPATCHER_RECORD, **overrides},
    )

    code, _out, err = _remove(capsys, str(worktree), "--owner-task-id", "impl-6")

    assert code == worktree_claims.EXIT_REFUSED
    assert "did not create this worktree" in err
    assert worktree.exists()


@pytest.mark.parametrize("provider", [{"provider_pgid": os.getpgrp()}, {"provider_pgid": ...}])
def test_dispatcher_record_removal_waits_for_the_provider_tree_to_end(tmp_path, capsys, provider):
    """Live provider processes, or none recorded either way, keep the checkout (#11865 F1)."""
    primary = _primary(tmp_path)
    worktree = _linked(primary, "claude/impl-7")
    record = {**_DISPATCHER_RECORD, **provider}
    if provider["provider_pgid"] is ...:
        del record["provider_pgid"]
    _record(primary, "impl-7", status="timeout", run_nonce="owner-run-7", worktree_path=str(worktree), **record)

    code, _out, err = _remove(capsys, str(worktree), "--owner-task-id", "impl-7")

    assert code == worktree_claims.EXIT_REFUSED
    assert "provider processes are live or unknown" in err
    assert worktree.exists()


@pytest.mark.parametrize(
    ("owner", "refusal"),
    [
        (None, "owner task impl-4 has no task record; refusing worktree removal"),
        ({"status": "needs_finalize", "worktree_reused": False}, "owner task impl-4 is not finished"),
        ({"status": "done", "worktree_reused": None}, "owner task impl-4 did not create this worktree"),
        ({"status": "done", "worktree_reused": False, "worktree_path": "/elsewhere"}, "a different worktree_path"),
    ],
)
def test_owner_proof_refuses_a_missing_live_reused_or_foreign_record(tmp_path, capsys, owner, refusal):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-4")
    if owner is not None:
        _record(
            primary,
            "impl-4",
            **{"run_nonce": "owner-run-4", "worktree_path": str(worktree), **owner},
        )

    code, _out, err = _remove(capsys, str(worktree), "--owner-task-id", "impl-4")

    assert code == worktree_claims.EXIT_REFUSED
    assert refusal in err
    assert worktree.exists()


def test_owner_exemption_uses_run_nonce_and_keeps_duplicate_task_id_claim(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-4-duplicate")
    _record(
        primary,
        "impl-4",
        status="failed",
        run_nonce="owner-run-4",
        worktree_path=str(worktree),
        worktree_reused=False,
    )
    duplicate = primary / "batch_state" / "tasks" / "duplicate-record.json"
    duplicate.write_text(
        json.dumps(
            {
                "task_id": "impl-4",
                "status": "running",
                "run_nonce": "different-run-4",
                "worktree_path": str(worktree),
            }
        ),
        encoding="utf-8",
    )

    code, _out, err = _remove(capsys, str(worktree), "--owner-task-id", "impl-4")

    assert code == worktree_claims.EXIT_REFUSED
    assert "worktree claimed by active task impl-4" in err
    assert worktree.exists()


def test_owner_exemption_fails_closed_without_run_nonce(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-4-no-nonce")
    _record(primary, "impl-4", status="failed", worktree_path=str(worktree), worktree_reused=False)

    code, _out, err = _remove(capsys, str(worktree), "--owner-task-id", "impl-4")

    assert code == worktree_claims.EXIT_REFUSED
    assert "owner task impl-4 has no valid run_nonce" in err
    assert worktree.exists()


def test_refuses_the_primary_checkout_and_unregistered_directories(tmp_path, capsys, monkeypatch):
    primary = _primary(tmp_path)
    bare_dir = primary / ".worktrees" / "dispatch" / "codex" / "never-added"
    bare_dir.mkdir(parents=True)
    monkeypatch.chdir(primary)

    primary_code, _out, primary_err = _remove(capsys, ".")
    bare_code, _out, bare_err = _remove(capsys, ".worktrees/dispatch/codex/never-added")

    assert primary_code == bare_code == worktree_claims.EXIT_REFUSED
    assert "PATH is the primary checkout" in primary_err
    assert "not a registered linked worktree" in bare_err
    assert bare_dir.exists()


def test_never_forces_a_dirty_worktree(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-5")
    (worktree / "uncommitted.txt").write_text("work in progress\n", encoding="utf-8")

    code, _out, err = _remove(capsys, str(worktree))

    assert code == worktree_claims.EXIT_ERROR
    assert err.startswith(f"error: {worktree}: worktree removal failed: ")
    assert (worktree / "uncommitted.txt").read_text(encoding="utf-8") == "work in progress\n"


def test_a_timed_out_removal_is_an_error_never_removed(tmp_path, capsys, monkeypatch):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-8")
    real_run = worktree_claims.safe_git
    timeouts: list[object] = []

    def fake_run(argv, *args, **kwargs):
        if list(argv[:2]) == ["worktree", "remove"]:
            timeouts.append(kwargs.get("timeout"))
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(worktree_claims, "safe_git", fake_run)
    code, out, _err = _remove(capsys, str(worktree), "--json")

    assert timeouts == [worktree_claims.GIT_WORKTREE_REMOVE_TIMEOUT_S]
    assert code == worktree_claims.EXIT_ERROR
    result = json.loads(out)
    assert result["action"] == "error"
    assert result["error"] == "git worktree remove timed out after 120s"
    assert worktree.exists()


def test_refuses_while_dispatch_holds_the_worktree_lock(tmp_path, capsys, monkeypatch):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-6")
    monkeypatch.setattr(worktree_claims, "DEFAULT_LOCK_TIMEOUT_S", 0.2)
    _canonical, lock_file = worktree_claims.lock_path(worktree, lock_dir=worktree_claims.repository_lock_dir(primary))
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        code, _out, err = _remove(capsys, str(worktree))
    finally:
        os.close(fd)

    assert code == worktree_claims.EXIT_REFUSED
    assert err == f"refused: {worktree}: worktree lock busy\n"
    assert worktree.exists()


def test_json_output_reports_every_outcome(tmp_path, capsys):
    primary = _primary(tmp_path)
    worktree = _linked(primary, "codex/impl-7")
    _record(primary, "review-7", status="running", worktree_path=str(worktree))

    refused_code, refused_out, _err = _remove(capsys, str(worktree), "--json")
    _record(primary, "review-7", status="done", worktree_path=str(worktree))
    removed_code, removed_out, _err = _remove(capsys, str(worktree), "--json")

    assert refused_code == worktree_claims.EXIT_REFUSED
    assert json.loads(refused_out) == {
        "action": "skipped",
        "branch": "codex/impl-7",
        "dirty": None,
        "error": None,
        "path": str(worktree),
        "reason": "worktree claimed by active task review-7",
    }
    assert removed_code == worktree_claims.EXIT_REMOVED
    assert json.loads(removed_out)["action"] == "removed"


def test_module_help_documents_exit_codes():
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.orchestration.worktree_claims", "remove", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert proc.returncode == 0
    for needle in ("--owner-task-id", "Exit codes:", "3  refused", "Outputs:", "Examples:"):
        assert needle in proc.stdout


def _wt_sh_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """A primary carrying scripts/wt.sh and a shim for its project interpreter."""
    primary = _primary(tmp_path)
    (primary / "scripts").mkdir()
    shutil.copy2(PROJECT_ROOT / "scripts" / "wt.sh", primary / "scripts" / "wt.sh")
    python = primary / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nPYTHONPATH="{PROJECT_ROOT}" exec "{sys.executable}" "$@"\n', encoding="utf-8")
    python.chmod(0o755)
    worktree = _linked(primary, "fix/817-issue-817", tmp_path / "learn-ukrainian-wt-817")
    return primary, worktree


def _wt_clean(primary: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(primary / "scripts" / "wt.sh"), "clean", "817"],
        cwd=primary,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_wt_sh_clean_removes_through_the_guarded_cli(tmp_path, monkeypatch):
    monkeypatch.delenv("TMPDIR", raising=False)
    primary, worktree = _wt_sh_fixture(tmp_path)

    proc = _wt_clean(primary)

    assert proc.returncode == 0, proc.stderr
    assert f"removed: {worktree} (wt.sh clean 817)" in proc.stdout
    assert not worktree.exists()


def test_wt_sh_create_from_linked_worktree_targets_primary_sibling(tmp_path):
    primary = _primary(tmp_path)
    worktree = _linked(
        primary,
        "codex/linked-wt-helper",
        primary / ".worktrees" / "dispatch" / "codex" / "linked",
    )
    python = primary / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nPYTHONPATH="{PROJECT_ROOT}" exec "{sys.executable}" "$@"\n', encoding="utf-8")
    python.chmod(0o755)
    linked_script = worktree / "scripts" / "wt.sh"
    linked_script.parent.mkdir()
    shutil.copy2(PROJECT_ROOT / "scripts" / "wt.sh", linked_script)

    proc = subprocess.run(
        ["bash", str(linked_script), "create", "818", "linked invocation"],
        cwd=worktree,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    target = primary.parent / "learn-ukrainian-wt-818"
    assert proc.returncode == 0, proc.stderr
    assert target.is_dir()
    assert not (worktree / "learn-ukrainian-wt-818").exists()


def test_claim_prefilter_skips_terminal_legacy_pid_records():
    raw = json.dumps({"status": "done", "pid": 123, "worktree_path": "other"}).encode()
    assert worktree_claims.record_may_claim_worktree(raw, frozenset({b"checkout"})) is False
    identity_record = json.dumps({"status": "done", "pid": 123, "worker_identity": {}}).encode()
    assert worktree_claims.record_may_claim_worktree(identity_record, frozenset({b"checkout"})) is True


@pytest.mark.parametrize("status", ["crashed", "done", "failed"])
def test_namespace_unknown_worker_keeps_terminal_worktree_claim(tmp_path, status):
    from scripts.orchestration import worktree_claims

    target = tmp_path / "checkout"
    target.mkdir()
    alias = tmp_path / "other-name"
    alias.symlink_to(target, target_is_directory=True)
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    record = {
        "task_id": "worker", "status": status, "run_nonce": "run",
        "worktree_path": str(alias), "worktree_reused": False, "pid": 999_999_998,
        "worker_identity": {
            "pid": 999_999_998, "host_pid": None, "start_time": 100,
            "pid_namespace": "pid:[999999]", "recorder_pid_namespace": "pid:[999999]",
        },
    }
    (tasks / "worker.json").write_text(json.dumps(record))
    refusal = worktree_claims.active_worktree_claim_refusal(target, tasks_dir=tasks, repo_root=tmp_path)
    assert refusal == "worktree claimed by active task worker"
    refusal = worktree_claims.owner_release_refusal(target, owner_task_id="worker", tasks_dir=tasks, repo_root=tmp_path)
    assert refusal == "owner task worker worker is live or unknown; refusing worktree removal"


def test_namespace_owner_exemption_does_not_release_unknown_worker(tmp_path):
    from scripts.orchestration import worktree_claims

    target = tmp_path / "checkout"
    target.mkdir()
    tasks = tmp_path / "tasks"
    tasks.mkdir()
    record = {
        "task_id": "worker", "status": "crashed", "run_nonce": "run",
        "worktree_path": str(target), "pid": 999_999_998,
        "worker_identity": {"pid": 999_999_998, "start_time": 100, "pid_namespace": "pid:[999999]"},
    }
    (tasks / "worker.json").write_text(json.dumps(record))
    assert worktree_claims.active_worktree_claim_refusal(
        target, tasks_dir=tasks, repo_root=tmp_path, owner_task_id="worker"
    ) == "worktree claimed by active task worker"


def test_namespace_other_live_worker_keeps_terminal_claim(tmp_path):
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        record = {"pid": process.pid, "status": "done"}
        assert worktree_claims._worker_blocks_release(record) is True
        assert worktree_claims._worker_blocks_release({"pid": os.getpid(), "status": "done"}) is False
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_archived_needs_finalize_record_never_claims_even_for_another_task(tmp_path):
    repo = _primary(tmp_path)
    worktree = _linked(repo, "codex/archived-claim")
    tasks = repo / "batch_state" / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "old.20260930T022748759089Z.archived.json").write_text(
        json.dumps({"task_id": "old", "status": "running", "worktree_path": str(worktree)}), encoding="utf-8"
    )
    (tasks / "live.json").write_text(
        json.dumps({"task_id": "live", "status": "running", "worktree_path": str(worktree)}), encoding="utf-8"
    )

    assert worktree_claims.active_worktree_claim_refusal(worktree, tasks_dir=tasks, repo_root=repo) == (
        "worktree claimed by active task live"
    )
    (tasks / "live.json").unlink()
    assert worktree_claims.active_worktree_claim_refusal(worktree, tasks_dir=tasks, repo_root=repo) is None


@pytest.mark.parametrize("record_task_id", ["owner", "different-task"])
def test_unfinished_owner_record_without_proven_identity_still_claims_worktree(tmp_path, record_task_id):
    """An unfinished owner or mislabelled record still claims without a valid nonce."""
    repo = _primary(tmp_path)
    worktree = _linked(repo, "codex/mislabelled")
    _record(repo, "owner", status="running", worktree_path=str(worktree))
    record = repo / "batch_state" / "tasks" / "owner.json"
    record.write_text(
        json.dumps({"task_id": record_task_id, "status": "running", "worktree_path": str(worktree)}),
        encoding="utf-8",
    )

    refusal = worktree_claims.active_worktree_claim_refusal(
        worktree, tasks_dir=record.parent, repo_root=repo, owner_task_id="owner"
    )

    assert refusal == f"worktree claimed by active task {record_task_id}"


def test_final_worktree_delete_hand_refuses_the_repository_root(tmp_path):
    """The last deletion boundary cannot turn a bad path into a root removal."""
    repo = _primary(tmp_path)

    error = worktree_claims.git_worktree_remove(repo, repo, force=True)

    assert error == "delete guard refused worktree target: delete target is the repository root"
