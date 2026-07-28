"""P6 dispatch-admission coverage for the shared rail-path decision module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


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
