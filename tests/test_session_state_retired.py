"""Dated session-state handoffs stay out of the tree (#8457)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "docs" / "session-state"
KEPT = {
    "README.md",
    "codex-orchestrator-handoff.md",
    "current.claude-atlas.md",
    "current.claude-infra.md",
    "current.claude.md",
    "current.gemini.md",
    "current.orchestrator.md",
}


def test_dated_session_handoffs_are_gone() -> None:
    assert SESSION.is_dir()
    names = {path.name for path in SESSION.iterdir() if path.is_file()}
    assert names == KEPT
    assert not (SESSION / "pending-dispatches").exists()
    assert list(SESSION.rglob("*.html")) == []
    assert list(SESSION.rglob("*.txt")) == []
