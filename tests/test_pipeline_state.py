"""Tests for pipeline/state.py — state management.

Covers:
- is_complete (pure function)
- _fresh_state (pure function, needs mock ctx)
- _migrate_v4_to_v5 (pure logic with mock ctx)
- load_state (file-based, uses tmp_path)
- save_state (file-based, uses tmp_path)

Issue: #783
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pipeline.state import (
    _fresh_state,
    _migrate_v4_to_v5,
    _state_file,
    is_complete,
    load_state,
    save_state,
)


@dataclass
class MockContext:
    """Minimal ModuleContext mock for state tests."""
    track: str = "a1"
    slug: str = "test-module"
    orch_dir: Path = field(default_factory=lambda: Path("/tmp"))


# =============================================================================
# is_complete
# =============================================================================

class TestIsComplete:
    def test_complete_phase(self):
        state = {"phases": {"content": {"status": "complete"}}}
        assert is_complete(state, "content") is True

    def test_failed_phase(self):
        state = {"phases": {"content": {"status": "failed"}}}
        assert is_complete(state, "content") is False

    def test_missing_phase(self):
        state = {"phases": {}}
        assert is_complete(state, "content") is False

    def test_no_phases_key(self):
        state = {}
        assert is_complete(state, "content") is False

    def test_in_progress_phase(self):
        state = {"phases": {"content": {"status": "in_progress"}}}
        assert is_complete(state, "content") is False

    def test_multiple_phases(self):
        state = {"phases": {
            "research": {"status": "complete"},
            "content": {"status": "failed"},
            "activities": {"status": "complete"},
        }}
        assert is_complete(state, "research") is True
        assert is_complete(state, "content") is False
        assert is_complete(state, "activities") is True


# =============================================================================
# _fresh_state
# =============================================================================

class TestFreshState:
    def test_basic(self):
        ctx = MockContext()
        state = _fresh_state(ctx)
        assert state["track"] == "a1"
        assert state["slug"] == "test-module"
        assert state["mode"] == "v5"
        assert state["phases"] == {}

    def test_different_track(self):
        ctx = MockContext(track="b2-hist", slug="my-module")
        state = _fresh_state(ctx)
        assert state["track"] == "b2-hist"
        assert state["slug"] == "my-module"


# =============================================================================
# _state_file
# =============================================================================

class TestStateFile:
    def test_returns_path(self):
        ctx = MockContext(orch_dir=Path("/some/dir"))
        assert _state_file(ctx) == Path("/some/dir/state.json")


# =============================================================================
# _migrate_v4_to_v5
# =============================================================================

class TestMigrateV4ToV5:
    def test_strips_v4_prefix(self):
        v4_data = {
            "track": "a1",
            "slug": "test",
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-content": {"status": "complete"},
            }
        }
        ctx = MockContext()
        result = _migrate_v4_to_v5(v4_data, ctx)
        assert result["mode"] == "v5"
        assert "research" in result["phases"]
        assert "content" in result["phases"]
        assert "v4-research" not in result["phases"]

    def test_keeps_unprefixed_keys(self):
        v4_data = {
            "track": "a1",
            "slug": "test",
            "phases": {"research": {"status": "complete"}}
        }
        ctx = MockContext()
        result = _migrate_v4_to_v5(v4_data, ctx)
        assert "research" in result["phases"]

    def test_empty_phases(self):
        v4_data = {"track": "a1", "slug": "test", "phases": {}}
        ctx = MockContext()
        result = _migrate_v4_to_v5(v4_data, ctx)
        assert result["phases"] == {}

    def test_uses_ctx_defaults(self):
        v4_data = {"phases": {}}
        ctx = MockContext(track="b1", slug="verbs")
        result = _migrate_v4_to_v5(v4_data, ctx)
        assert result["track"] == "b1"
        assert result["slug"] == "verbs"


# =============================================================================
# save_state + load_state (integration with tmp files)
# =============================================================================

class TestSaveLoadState:
    def test_round_trip(self, tmp_path):
        orch_dir = tmp_path / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        ctx = MockContext(orch_dir=orch_dir)

        state = _fresh_state(ctx)
        state["phases"]["research"] = {"status": "complete"}
        save_state(ctx, state)

        # Verify file exists
        sf = orch_dir / "state.json"
        assert sf.exists()

        # Verify JSON content
        data = json.loads(sf.read_text("utf-8"))
        assert data["mode"] == "v5"
        assert data["phases"]["research"]["status"] == "complete"

    def test_save_creates_directory(self, tmp_path):
        orch_dir = tmp_path / "new" / "nested" / "dir"
        ctx = MockContext(orch_dir=orch_dir)
        state = _fresh_state(ctx)
        save_state(ctx, state)
        assert (orch_dir / "state.json").exists()

    def test_load_fresh_when_no_state(self, tmp_path):
        orch_dir = tmp_path / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        ctx = MockContext(orch_dir=orch_dir)

        state = load_state(ctx)
        assert state["mode"] == "v5"
        assert state["phases"] == {}

    def test_load_existing_v5_state(self, tmp_path):
        orch_dir = tmp_path / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        ctx = MockContext(orch_dir=orch_dir)

        # Write a v5 state
        existing = {"track": "a1", "slug": "test-module", "mode": "v5",
                     "phases": {"research": {"status": "complete"}}}
        (orch_dir / "state.json").write_text(json.dumps(existing), "utf-8")

        state = load_state(ctx)
        assert state["mode"] == "v5"
        assert is_complete(state, "research")

    def test_load_migrates_v4_state(self, tmp_path):
        orch_dir = tmp_path / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        ctx = MockContext(orch_dir=orch_dir)

        # Write a v4 state
        v4 = {"track": "a1", "slug": "test-module", "mode": "v4",
               "phases": {"v4-research": {"status": "complete"}}}
        (orch_dir / "state-v4.json").write_text(json.dumps(v4), "utf-8")

        state = load_state(ctx)
        assert state["mode"] == "v5"
        assert "research" in state["phases"]
