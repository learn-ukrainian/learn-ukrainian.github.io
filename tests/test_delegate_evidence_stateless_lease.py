"""#11342: stateless dispatch evidence must neither disappear nor wedge cleanup."""

from __future__ import annotations

from pathlib import Path


def test_refusal_runbook_has_a_non_destructive_receipt_recovery_path():
    """A refusal without retrieval and a retry path leaves evidence retained forever."""
    runbook = Path("docs/runbooks/worktree-cleanup.md").read_text()
    section = runbook.split("### Reusing a worktree with evidence (#11342)", 1)[1].split("\n## ", 1)[0]
    assert "Retrieve the evidence" in section
    assert "original task record" in section
    assert "Retry the same cleanup path" in section
    assert "verified retrieval receipt" in section
    assert "never delete" in section
