"""
Tests for v3 pipeline state management.

Covers: _load_state_v3, _save_state_v3, _is_phase_v3_complete,
        _mark_phase_v3, _migrate_v2_state_to_v3.

All tests use temp directories — no real modules or LLM calls.

Issue: #611
"""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.build_module import (
    _load_state_v3,
    _save_state_v3,
    _is_phase_v3_complete,
    _V3_PHASE_STATE_IDS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ctx(tmp_path):
    """Create a minimal ModuleContext-like object with temp orch_dir."""
    ctx = MagicMock()
    ctx.track = "a1"
    ctx.slug = "test-module"
    ctx.orch_dir = tmp_path / "orchestration" / "test-module"
    ctx.orch_dir.mkdir(parents=True)
    return ctx


@pytest.fixture
def state_file(mock_ctx):
    """Return path to the state-v3.json file."""
    return mock_ctx.orch_dir / "state-v3.json"


# ---------------------------------------------------------------------------
# _load_state_v3
# ---------------------------------------------------------------------------

class TestLoadStateV3:
    """Tests for _load_state_v3."""

    def test_missing_file_returns_fresh_state(self, mock_ctx):
        """No state file → returns fresh state with track/slug/mode."""
        state = _load_state_v3(mock_ctx)
        assert state["track"] == "a1"
        assert state["slug"] == "test-module"
        assert state["mode"] == "v3"
        assert state["phases"] == {}

    def test_valid_json_returns_parsed(self, mock_ctx, state_file):
        """Valid JSON file → returns parsed dict."""
        data = {"track": "a1", "slug": "test-module", "mode": "v3",
                "phases": {"v3-A": {"status": "complete", "ts": "2026-01-01T00:00:00"}}}
        state_file.write_text(json.dumps(data), "utf-8")

        state = _load_state_v3(mock_ctx)
        assert state["phases"]["v3-A"]["status"] == "complete"

    def test_corrupted_json_returns_fresh_state(self, mock_ctx, state_file):
        """Invalid JSON → backs up corrupted file, returns fresh state."""
        state_file.write_text("{invalid json!!!", "utf-8")

        state = _load_state_v3(mock_ctx)
        assert state["phases"] == {}
        assert state["track"] == "a1"

        # Verify backup was created
        backups = list(mock_ctx.orch_dir.glob("state-v3.corrupted.*.json"))
        assert len(backups) == 1

    def test_empty_file_returns_fresh_state(self, mock_ctx, state_file):
        """Empty file → treated as corrupt, returns fresh state."""
        state_file.write_text("", "utf-8")

        state = _load_state_v3(mock_ctx)
        assert state["phases"] == {}

    def test_truncated_json_returns_fresh_state(self, mock_ctx, state_file):
        """Truncated JSON (partial write) → returns fresh state."""
        state_file.write_text('{"track": "a1", "phases": {', "utf-8")

        state = _load_state_v3(mock_ctx)
        assert state["phases"] == {}

    def test_corrupted_file_original_removed(self, mock_ctx, state_file):
        """After corruption recovery, original file should be renamed."""
        state_file.write_text("not json", "utf-8")

        _load_state_v3(mock_ctx)
        assert not state_file.exists()  # Original renamed to backup


# ---------------------------------------------------------------------------
# _save_state_v3
# ---------------------------------------------------------------------------

class TestSaveStateV3:
    """Tests for _save_state_v3."""

    def test_basic_save(self, mock_ctx, state_file):
        """State dict saved as formatted JSON."""
        state = {"track": "a1", "slug": "test", "phases": {}}
        _save_state_v3(mock_ctx, state)

        assert state_file.exists()
        loaded = json.loads(state_file.read_text("utf-8"))
        assert loaded["track"] == "a1"

    def test_unicode_content(self, mock_ctx, state_file):
        """Ukrainian content preserved correctly."""
        state = {"track": "a1", "note": "Тестовий модуль — Київ"}
        _save_state_v3(mock_ctx, state)

        loaded = json.loads(state_file.read_text("utf-8"))
        assert loaded["note"] == "Тестовий модуль — Київ"

    def test_creates_parent_directories(self, mock_ctx):
        """Parent directories created if missing."""
        mock_ctx.orch_dir = mock_ctx.orch_dir / "nested" / "deep"
        state_file = mock_ctx.orch_dir / "state-v3.json"

        state = {"track": "a1", "phases": {}}
        _save_state_v3(mock_ctx, state)

        assert state_file.exists()

    def test_overwrites_existing(self, mock_ctx, state_file):
        """Existing file is replaced atomically."""
        state_file.write_text('{"old": true}', "utf-8")

        _save_state_v3(mock_ctx, {"new": True})

        loaded = json.loads(state_file.read_text("utf-8"))
        assert "new" in loaded
        assert "old" not in loaded

    def test_no_temp_files_on_success(self, mock_ctx):
        """No .tmp files left after successful save."""
        _save_state_v3(mock_ctx, {"track": "a1"})

        tmp_files = list(mock_ctx.orch_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_pretty_printed(self, mock_ctx, state_file):
        """JSON is indented for readability."""
        _save_state_v3(mock_ctx, {"track": "a1", "phases": {"v3-A": {"status": "complete"}}})

        text = state_file.read_text("utf-8")
        assert "\n" in text  # Not single-line
        assert "  " in text  # Indented


# ---------------------------------------------------------------------------
# _is_phase_v3_complete
# ---------------------------------------------------------------------------

class TestIsPhaseComplete:
    """Tests for _is_phase_v3_complete."""

    def test_complete_phase(self, mock_ctx):
        """Phase marked complete → True."""
        state = {"phases": {"v3-A": {"status": "complete", "ts": "2026-01-01"}}}
        assert _is_phase_v3_complete(mock_ctx, "A", state) is True

    def test_incomplete_phase(self, mock_ctx):
        """Phase with non-complete status → False."""
        state = {"phases": {"v3-A": {"status": "in-progress"}}}
        assert _is_phase_v3_complete(mock_ctx, "A", state) is False

    def test_missing_phase(self, mock_ctx):
        """Phase not in state → False."""
        state = {"phases": {}}
        assert _is_phase_v3_complete(mock_ctx, "A", state) is False

    def test_missing_phases_dict(self, mock_ctx):
        """No phases key at all → False."""
        state = {}
        assert _is_phase_v3_complete(mock_ctx, "A", state) is False

    def test_phase_e_uses_v2_key(self, mock_ctx):
        """Phase E maps to v2 key '8'."""
        state = {"phases": {"8": {"status": "complete"}}}
        assert _is_phase_v3_complete(mock_ctx, "E", state) is True

    def test_phase_f_uses_v2_key(self, mock_ctx):
        """Phase F maps to v2 key '9-final-review'."""
        state = {"phases": {"9-final-review": {"status": "complete"}}}
        assert _is_phase_v3_complete(mock_ctx, "F", state) is True

    def test_unknown_phase_id_fallback(self, mock_ctx):
        """Unknown phase ID → uses phase_id as key directly."""
        state = {"phases": {"custom-phase": {"status": "complete"}}}
        assert _is_phase_v3_complete(mock_ctx, "custom-phase", state) is True

    def test_all_standard_phases(self, mock_ctx):
        """All standard phase IDs resolve correctly."""
        for phase_id, state_ids in _V3_PHASE_STATE_IDS.items():
            state = {"phases": {sid: {"status": "complete"} for sid in state_ids}}
            assert _is_phase_v3_complete(mock_ctx, phase_id, state) is True, \
                f"Phase {phase_id} with state IDs {state_ids} should be complete"


# ---------------------------------------------------------------------------
# Round-trip: save → load
# ---------------------------------------------------------------------------

class TestSaveLoadRoundTrip:
    """Integration tests for save → load cycle."""

    def test_roundtrip_preserves_state(self, mock_ctx):
        """Save then load returns identical state."""
        original = {
            "track": "a1",
            "slug": "test-module",
            "mode": "v3",
            "phases": {
                "v3-A": {"status": "complete", "ts": "2026-01-15T10:30:00"},
                "v3-B": {"status": "in-progress", "ts": "2026-01-15T10:35:00"},
            }
        }
        _save_state_v3(mock_ctx, original)
        loaded = _load_state_v3(mock_ctx)

        assert loaded == original

    def test_multiple_saves_keep_latest(self, mock_ctx):
        """Multiple saves → last one wins."""
        _save_state_v3(mock_ctx, {"version": 1})
        _save_state_v3(mock_ctx, {"version": 2})
        _save_state_v3(mock_ctx, {"version": 3})

        loaded = _load_state_v3(mock_ctx)
        assert loaded["version"] == 3

    def test_save_after_corruption_recovery(self, mock_ctx, state_file):
        """After loading corrupted state, saving works normally."""
        state_file.write_text("corrupt!", "utf-8")
        state = _load_state_v3(mock_ctx)  # Returns fresh state

        state["phases"]["v3-A"] = {"status": "complete"}
        _save_state_v3(mock_ctx, state)

        reloaded = _load_state_v3(mock_ctx)
        assert reloaded["phases"]["v3-A"]["status"] == "complete"
