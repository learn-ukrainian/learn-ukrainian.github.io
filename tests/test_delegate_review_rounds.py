"""Settle-time reap policy for read-only review dispatches (#8536).

``ask-codex --review`` and ``ask-agy --review`` create their checkouts
through ``delegate.py dispatch --mode read-only --worktree``
(``scripts/ai_agent_bridge/_dispatch_wrappers.py``). They settle in
``_run_worker``. The sealed snapshot helper tears its temp root down in
``finally`` and is not a second worktree owner.

Removal itself (worktree gone, branch ref kept, dirty trees kept) is
covered in ``tests/test_delegate.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import delegate


@pytest.mark.parametrize(
    ("mode", "status", "returncode", "dirty", "keep", "expected"),
    [
        ("read-only", "done", 0, False, False, True),
        ("read-only", "failed", 1, False, False, True),
        ("read-only", "no_deliverable", 0, False, False, True),
        ("read-only", "timeout", None, False, False, True),
        ("read-only", "done", 0, True, False, False),
        ("read-only", "done", 0, None, False, False),
        ("read-only", "done", 0, False, True, False),
        ("workspace-write", "done", 0, False, False, True),
        ("workspace-write", "failed", 1, False, False, False),
        ("workspace-write", "done", 0, True, False, False),
        ("workspace-write", "done", 0, False, True, False),
        ("danger", "done", 0, False, False, True),
        ("danger", "failed", 1, False, False, False),
        ("danger", "done", 0, True, False, False),
        ("danger", "done", 0, False, True, False),
    ],
)
def test_settled_worktree_reap_policy(mode, status, returncode, dirty, keep, expected):
    assert (
        delegate._should_reap_settled_worktree(
            mode=mode,
            keep_worktree=keep,
            final_status=status,
            returncode=returncode,
            dirty_on_exit=dirty,
        )
        is expected
    )
