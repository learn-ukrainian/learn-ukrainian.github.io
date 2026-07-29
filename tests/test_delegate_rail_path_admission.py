"""P6 dispatch-admission coverage for the shared rail-path decision module."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate

from scripts.orchestration import rail_approval
from scripts.orchestration import rail_path_guard as guard


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
