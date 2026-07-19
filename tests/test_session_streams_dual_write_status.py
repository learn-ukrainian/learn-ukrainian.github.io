"""dual-write-status / registry inventory for session streams."""

from __future__ import annotations

from pathlib import Path

from agents_extensions.shared.session_streams.dual_write import (
    EPIC_HANDOFF_CANDIDATES,
    list_handoff_candidates,
    resolve_handoff_path,
)


def test_registry_includes_atlas_and_infra():
    assert "epic:4387" in EPIC_HANDOFF_CANDIDATES
    assert "epic:4707" in EPIC_HANDOFF_CANDIDATES


def test_list_handoff_candidates_marks_missing(tmp_path: Path):
    rows = list_handoff_candidates(tmp_path)
    assert rows
    assert all(r.exists is False for r in rows)


def test_resolve_handoff_path_first_existing(tmp_path: Path):
    stream = "epic:4387"
    candidates = EPIC_HANDOFF_CANDIDATES[stream]
    # Create second candidate only
    second = tmp_path / candidates[1]
    second.parent.mkdir(parents=True, exist_ok=True)
    second.write_text("handoff\n", encoding="utf-8")
    resolved = resolve_handoff_path(stream, tmp_path)
    assert resolved == second.resolve()
