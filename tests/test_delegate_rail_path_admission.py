"""P6 dispatch-admission coverage for the shared rail-path decision module."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

from scripts.orchestration import rail_approval
from scripts.orchestration import rail_path_guard as guard

RAIL_PATH = "agents_extensions/shared/hooks/guard-pr-merge.py"


def _git(cwd: Path, *args: str) -> str:
    # The agent-runtime Git shim rejects pushes to `main` when its
    # AGENT_NO_MERGE guard is inherited. These fixtures push disposable
    # scratch repos and must not inherit that ambient policy.
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.pop("AGENT_NO_MERGE", None)
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, env=environment
    ).stdout.strip()


def _make_remote_fixture(tmp_path: Path) -> tuple[Path, Path, str, str]:
    """Return a primary clone whose HEAD lags the canonical origin/main."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
    primary = tmp_path / "primary"
    subprocess.run(["git", "clone", str(origin), str(primary)], check=True, capture_output=True)
    _git(primary, "config", "user.email", "test@example.com")
    _git(primary, "config", "user.name", "Test")
    (primary / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(primary, "add", "tracked.txt")
    _git(primary, "commit", "-m", "initial")
    _git(primary, "branch", "-M", "main")
    _git(primary, "push", "-u", "origin", "main")
    old_sha = _git(primary, "rev-parse", "HEAD")

    writer = tmp_path / "writer"
    subprocess.run(["git", "clone", str(origin), str(writer)], check=True, capture_output=True)
    _git(writer, "config", "user.email", "test@example.com")
    _git(writer, "config", "user.name", "Test")
    _git(writer, "checkout", "main")
    (writer / "tracked.txt").write_text("remote advance\n", encoding="utf-8")
    _git(writer, "commit", "-am", "remote advance")
    _git(writer, "push", "origin", "main")
    return primary, writer, old_sha, _git(writer, "rev-parse", "HEAD")


class _FakeStdin:
    def write(self, _data: bytes) -> None:
        pass

    def close(self) -> None:
        pass


class _FakeWorker:
    pid = 424242
    stdin = _FakeStdin()


def _patch_worker_spawn(monkeypatch) -> list[list[str]]:
    """Record workers while retaining the real subprocess path for git."""
    spawned: list[list[str]] = []
    real_popen = delegate.subprocess.Popen

    def fake_popen(cmd, *args, **kwargs):
        if cmd and str(cmd[0]) == "git":
            return real_popen(cmd, *args, **kwargs)
        spawned.append(list(cmd))
        return _FakeWorker()

    monkeypatch.setattr(delegate.subprocess, "Popen", fake_popen)
    return spawned


def _dispatch_args(
    *, task_id: str, worktree: Path, receipt_id: str | None = None, branch: str | None = None
):
    command = [
        "dispatch",
        "--agent",
        "codex",
        "--task-id",
        task_id,
        "--prompt",
        "fixture",
        "--mode",
        "workspace-write",
        "--worktree",
        str(worktree),
        "--research-owned-path",
        RAIL_PATH,
    ]
    if receipt_id:
        command.extend(["--rail-approval-receipt", receipt_id])
    if branch:
        command.extend(["--branch", branch])
    return delegate.build_parser().parse_args(command)


def _prepare_dispatch_fixture(monkeypatch, tmp_path: Path, primary: Path) -> None:
    monkeypatch.setattr(delegate, "_REPO_ROOT", primary)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate, "_warn_if_monitor_api_unreachable", lambda: None)
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_args, **_kwargs: None)
    for key in tuple(os.environ):
        if key.startswith(("GIT_", "PRE_COMMIT")):
            monkeypatch.delenv(key, raising=False)


def _receipt(task_id: str, head_sha: str) -> dict[str, object]:
    return rail_approval.create_rail_approval_receipt(
        task_id=task_id,
        head_sha=head_sha,
        owned_paths=[RAIL_PATH],
        issuer="operator",
        ttl_hours=1,
    )


def test_dispatch_admission_refuses_rail_claim_before_ownership_ledger() -> None:
    error = delegate._rail_path_admission_error(
        task_id="rail-p6-test",
        mode="workspace-write",
        owned_paths=["agents_extensions/shared/hooks/guard-pr-merge.py"],
    )

    assert error is not None
    assert "rail_approval_receipt_required" in error


def test_dispatch_admission_leaves_non_rail_claim_unaffected() -> None:
    error = delegate._rail_path_admission_error(
        task_id="rail-p6-test",
        mode="workspace-write",
        owned_paths=["docs/projects/fleet-trails/rail-system-completion-memo.md"],
    )

    assert error is None


def test_write_dispatch_without_paths_emits_and_persists_deferred_rail_advisory() -> None:
    """F002 is honest about the hook/CI/merge layers that still enforce rails."""
    advisory = delegate._rail_path_admission_advisory(
        mode="workspace-write",
        owned_paths=None,
    )
    assert advisory == (
        "rail admission: no path declaration — rail enforcement deferred to hook/CI/merge layers"
    )
    state = delegate._with_rail_admission_state({}, advisory=advisory, receipt_id=None)
    assert state["rail_admission_advisory"] == advisory


def test_dry_write_dispatch_records_the_same_no_path_advisory(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The dispatched task state retains exactly the stderr F002 advisory."""
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate, "_resolve_write_cwd_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_resolve_dirty_primary_checkout_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_resolve_primary_integrity_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_warn_if_monitor_api_unreachable", lambda: None)
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_args, **_kwargs: None)
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "rail-no-path-advisory",
            "--prompt",
            "fixture",
            "--mode",
            "workspace-write",
            "--cwd",
            str(tmp_path),
            "--dry-run",
        ]
    )

    assert delegate.cmd_dispatch(args) == 0

    advisory = delegate.RAIL_ADMISSION_NO_PATH_ADVISORY
    state = delegate._read_state(delegate._state_path("rail-no-path-advisory"))
    assert state is not None
    assert state["rail_admission_advisory"] == advisory
    assert advisory in capsys.readouterr().err


def test_declared_rail_path_still_denies_without_receipt_and_has_no_advisory() -> None:
    error = delegate._rail_path_admission_error(
        task_id="rail-p6-test",
        mode="workspace-write",
        owned_paths=["agents_extensions/shared/hooks/guard-pr-merge.py"],
    )
    advisory = delegate._rail_path_admission_advisory(
        mode="workspace-write",
        owned_paths=["agents_extensions/shared/hooks/guard-pr-merge.py"],
    )

    assert error is not None
    assert "rail_approval_receipt_required" in error
    assert advisory is None


def test_dispatch_admission_refetches_a_valid_production_receipt(
    monkeypatch
) -> None:
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=delegate._REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    receipt = rail_approval.create_rail_approval_receipt(
        task_id="rail-p6-test",
        head_sha=head_sha,
        owned_paths=["agents_extensions/shared/hooks/guard-pr-merge.py"],
        issuer="operator",
        ttl_hours=1,
    )
    monkeypatch.setattr(
        guard,
        "_monitor_api_get",
        lambda _path: (200, json.dumps(receipt), {}),
    )

    error = delegate._rail_path_admission_error(
        task_id="rail-p6-test",
        mode="workspace-write",
        owned_paths=["agents_extensions/shared/hooks/guard-pr-merge.py"],
        receipt_id=receipt["receipt_id"],
    )

    assert error is None


def test_dispatch_fresh_worktree_admits_receipt_bound_to_fetched_origin_tip(
    tmp_path: Path, monkeypatch
) -> None:
    """cmd_dispatch admits the fetched origin/main SHA, not primary HEAD."""
    primary, _writer, primary_sha, origin_sha = _make_remote_fixture(tmp_path)
    _prepare_dispatch_fixture(monkeypatch, tmp_path, primary)
    spawned = _patch_worker_spawn(monkeypatch)
    task_id = "rail-fresh-origin-tip"
    receipt = _receipt(task_id, origin_sha)
    monkeypatch.setattr(guard, "_monitor_api_get", lambda _path: (200, json.dumps(receipt), {}))

    worktree = primary / ".worktrees" / "dispatch" / "codex" / task_id
    assert (
        delegate.cmd_dispatch(
            _dispatch_args(task_id=task_id, worktree=worktree, receipt_id=receipt["receipt_id"])
        )
        == 0
    )

    assert primary_sha != origin_sha
    assert _git(worktree, "rev-parse", "HEAD") == origin_sha
    assert len(spawned) == 1


def test_dispatch_branch_admits_receipt_bound_to_branch_tip_not_primary(
    tmp_path: Path, monkeypatch
) -> None:
    """Follow-up admission binds the fetched branch tip despite a different primary."""
    primary, writer, primary_sha, _origin_sha = _make_remote_fixture(tmp_path)
    branch = "codex/rail-follow-up"
    _git(writer, "checkout", "-b", branch)
    (writer / "branch.txt").write_text("branch tip\n", encoding="utf-8")
    _git(writer, "add", "branch.txt")
    _git(writer, "commit", "-m", "branch tip")
    _git(writer, "push", "-u", "origin", branch)
    branch_sha = _git(writer, "rev-parse", "HEAD")

    _prepare_dispatch_fixture(monkeypatch, tmp_path, primary)
    spawned = _patch_worker_spawn(monkeypatch)
    task_id = "rail-branch-tip"
    receipt = _receipt(task_id, branch_sha)
    monkeypatch.setattr(guard, "_monitor_api_get", lambda _path: (200, json.dumps(receipt), {}))

    worktree = primary / ".worktrees" / "dispatch" / "codex" / task_id
    assert (
        delegate.cmd_dispatch(
            _dispatch_args(
                task_id=task_id,
                worktree=worktree,
                receipt_id=receipt["receipt_id"],
                branch=branch,
            )
        )
        == 0
    )

    assert primary_sha != branch_sha
    assert _git(worktree, "rev-parse", "HEAD") == branch_sha
    assert len(spawned) == 1


def test_dispatch_refuses_receipt_bound_to_wrong_base_before_worker_spawn(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    primary, _writer, primary_sha, _origin_sha = _make_remote_fixture(tmp_path)
    _prepare_dispatch_fixture(monkeypatch, tmp_path, primary)
    spawned = _patch_worker_spawn(monkeypatch)
    task_id = "rail-wrong-base"
    receipt = _receipt(task_id, primary_sha)
    monkeypatch.setattr(guard, "_monitor_api_get", lambda _path: (200, json.dumps(receipt), {}))
    worktree = primary / ".worktrees" / "dispatch" / "codex" / task_id

    assert (
        delegate.cmd_dispatch(
            _dispatch_args(task_id=task_id, worktree=worktree, receipt_id=receipt["receipt_id"])
        )
        == 2
    )

    assert "rail_approval_head_mismatch" in capsys.readouterr().err
    assert spawned == []
    assert not worktree.exists()


def test_dispatch_refuses_worker_spawn_when_created_head_differs_from_resolved_base(
    tmp_path: Path, monkeypatch
) -> None:
    """Post-create verification fails before sparse provisioning or Popen."""
    calls: list[list[str]] = []
    resolved_sha = "a" * 40
    created_sha = "b" * 40

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:2] == ["git", "fetch"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rev-parse"]:
            ref = cmd[-1]
            if ref == "origin/main" or "--verify" in cmd:
                return subprocess.CompletedProcess(cmd, 0, resolved_sha, "")
            return subprocess.CompletedProcess(cmd, 0, created_sha, "")
        if cmd[:3] == ["git", "worktree", "add"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)
    monkeypatch.setattr(delegate, "_TASKS_DIR", tmp_path / "tasks")
    monkeypatch.setattr(delegate, "_resolve_write_cwd_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_resolve_dirty_primary_checkout_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_resolve_primary_integrity_error", lambda **_kwargs: None)
    monkeypatch.setattr(delegate, "_warn_if_monitor_api_unreachable", lambda: None)
    monkeypatch.setattr(delegate, "_check_capacity_hint", lambda *_args, **_kwargs: None)
    spawned = _patch_worker_spawn(monkeypatch)
    worktree = tmp_path / "worktree"
    args = delegate.build_parser().parse_args(
        [
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "head-verify",
            "--prompt",
            "fixture",
            "--mode",
            "workspace-write",
            "--worktree",
            str(worktree),
        ]
    )

    assert delegate.cmd_dispatch(args) == 1

    assert spawned == []
    assert not any(cmd[:2] == ["git", "sparse-checkout"] for cmd in calls)


def test_reused_stale_worktree_refuses_without_rebase_before_admission(
    tmp_path: Path, monkeypatch
) -> None:
    """Receipt rejection cannot be preceded by a reuse-rebase side effect."""
    worktree = tmp_path / "existing"
    worktree.mkdir()
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:2] == ["git", "rev-parse"]:
            if "--abbrev-ref" in cmd:
                return subprocess.CompletedProcess(cmd, 0, "codex/stale\n", "")
            return subprocess.CompletedProcess(cmd, 0, "a" * 40, "")
        if cmd[:2] == ["git", "status"]:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "fetch"] or "--verify" in cmd:
            return subprocess.CompletedProcess(cmd, 0, "", "")
        if cmd[:2] == ["git", "rev-list"]:
            return subprocess.CompletedProcess(cmd, 0, "1\n", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(delegate.subprocess, "run", fake_run)

    with pytest.raises(delegate.WorktreeStaleBase):
        delegate._resolve_worktree_base_sha(
            agent="codex",
            task_id="stale",
            raw_path=str(worktree),
            base="main",
            branch=None,
        )

    assert not any(cmd[:2] == ["git", "rebase"] for cmd in calls)


def test_worktree_creation_uses_resolved_sha_after_remote_ref_moves(
    tmp_path: Path, monkeypatch
) -> None:
    """A remote push after resolution cannot change the created worktree base."""
    primary, writer, _primary_sha, initial_origin_sha = _make_remote_fixture(tmp_path)
    _prepare_dispatch_fixture(monkeypatch, tmp_path, primary)
    worktree = primary / ".worktrees" / "dispatch" / "codex" / "frozen-base"
    resolved_sha = delegate._resolve_worktree_base_sha(
        agent="codex",
        task_id="frozen-base",
        raw_path=str(worktree),
        base="main",
        branch=None,
    )
    assert resolved_sha == initial_origin_sha

    _git(writer, "checkout", "main")
    (writer / "tracked.txt").write_text("moves again\n", encoding="utf-8")
    _git(writer, "commit", "-am", "move remote after resolution")
    _git(writer, "push", "origin", "main")
    moved_sha = _git(writer, "rev-parse", "HEAD")

    created, _branch, telemetry = delegate._ensure_worktree(
        agent="codex",
        task_id="frozen-base",
        raw_path=str(worktree),
        base="main",
        resolved_base_sha=resolved_sha,
    )

    assert moved_sha != resolved_sha
    assert _git(created, "rev-parse", "HEAD") == resolved_sha
    assert telemetry["base_sha"] == resolved_sha


def test_dispatch_branch_occupancy_refuses_with_pre_resolved_sha(
    tmp_path: Path, monkeypatch
) -> None:
    """cmd_dispatch reaches the unconditional #5340 occupancy guard."""
    primary, writer, _primary_sha, _origin_sha = _make_remote_fixture(tmp_path)
    branch = "codex/occupied-follow-up"
    _git(writer, "checkout", "-b", branch)
    _git(writer, "push", "-u", "origin", branch)
    branch_sha = _git(writer, "rev-parse", "HEAD")
    _prepare_dispatch_fixture(monkeypatch, tmp_path, primary)
    spawned = _patch_worker_spawn(monkeypatch)
    task_id = "rail-occupied-branch"
    receipt = _receipt(task_id, branch_sha)
    monkeypatch.setattr(guard, "_monitor_api_get", lambda _path: (200, json.dumps(receipt), {}))
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    monkeypatch.setattr(delegate, "_branch_worktree_paths", lambda _branch: [occupied])
    monkeypatch.setattr(delegate, "_release_stale_branch_holders", lambda **_kwargs: [])

    worktree = primary / ".worktrees" / "dispatch" / "codex" / task_id
    assert (
        delegate.cmd_dispatch(
            _dispatch_args(
                task_id=task_id,
                worktree=worktree,
                receipt_id=receipt["receipt_id"],
                branch=branch,
            )
        )
        == 1
    )

    assert spawned == []
    assert not worktree.exists()
