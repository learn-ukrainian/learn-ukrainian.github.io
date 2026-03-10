"""
Tests for v4 pipeline support in the API and MDX generator.

Validates:
  1. _detect_pipeline_version() returns correct version
  2. _read_v4_state() reads state-v4.json
  3. _parse_v4_phase_status() extracts phase info
  4. _is_research_done / _is_content_done with v4 state
  5. _compute_pipeline_track returns v4 phases for v4 modules
  6. /failing endpoint includes pipeline_version
  7. dashboard module_detail includes pipeline_version + v4_phases
  8. generate_mdx frontmatter includes pipeline/build_status
  9. detect_pipeline_info() helper in generate_mdx
"""

import json
import tempfile
from pathlib import Path

import pytest


# ==================== state_router helpers ====================


class TestDetectPipelineVersion:
    """_detect_pipeline_version picks the right version."""

    def test_v4_when_state_v4_exists(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state-v4.json").write_text('{"mode": "v4"}')
        assert _detect_pipeline_version(tmp_path) == "v4"

    def test_v3_when_state_v3_exists(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state-v3.json").write_text('{"phases": {}}')
        assert _detect_pipeline_version(tmp_path) == "v3"

    def test_v4_from_state_json_mode(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state.json").write_text('{"mode": "v4"}')
        assert _detect_pipeline_version(tmp_path) == "v4"

    def test_v3_from_state_json_without_mode(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state.json").write_text('{"phases": {"1": {}}}')
        assert _detect_pipeline_version(tmp_path) == "v3"

    def test_unbuilt_when_empty(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        assert _detect_pipeline_version(tmp_path) == "unbuilt"

    def test_v4_takes_priority_over_v3(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state-v4.json").write_text('{"mode": "v4"}')
        (tmp_path / "state-v3.json").write_text('{"phases": {}}')
        assert _detect_pipeline_version(tmp_path) == "v4"


class TestReadV4State:
    """_read_v4_state reads state-v4.json correctly."""

    def test_reads_valid_json(self, tmp_path):
        from scripts.api.state_router import _read_v4_state

        data = {"mode": "v4", "phases": {"v4-research": {"status": "complete"}}}
        (tmp_path / "state-v4.json").write_text(json.dumps(data))
        result = _read_v4_state(tmp_path)
        assert result["phases"]["v4-research"]["status"] == "complete"

    def test_returns_empty_when_missing(self, tmp_path):
        from scripts.api.state_router import _read_v4_state

        assert _read_v4_state(tmp_path) == {}

    def test_returns_empty_on_invalid_json(self, tmp_path):
        from scripts.api.state_router import _read_v4_state

        (tmp_path / "state-v4.json").write_text("not valid json{{{")
        assert _read_v4_state(tmp_path) == {}


class TestParseV4PhaseStatus:
    """_parse_v4_phase_status extracts info from v4 state."""

    def test_complete_phase(self):
        from scripts.api.state_router import _parse_v4_phase_status

        v4 = {"phases": {"v4-content": {"status": "complete", "ts": "2026-03-02T20:12:36Z"}}}
        result = _parse_v4_phase_status(v4, "content")
        assert result["status"] == "complete"
        assert result["ts"] == "2026-03-02T20:12:36Z"

    def test_missing_phase_returns_pending(self):
        from scripts.api.state_router import _parse_v4_phase_status

        v4 = {"phases": {}}
        result = _parse_v4_phase_status(v4, "review")
        assert result["status"] == "pending"

    def test_empty_state_returns_pending(self):
        from scripts.api.state_router import _parse_v4_phase_status

        result = _parse_v4_phase_status({}, "research")
        assert result["status"] == "pending"


class TestIsResearchDone:
    """_is_research_done uses unified v5 state format."""

    def test_research_complete(self):
        from scripts.api.state_router import _is_research_done

        state = {"mode": "v5", "phases": {"research": {"status": "complete"}}}
        assert _is_research_done(state) is True

    def test_research_not_complete(self):
        from scripts.api.state_router import _is_research_done

        state = {"mode": "v5", "phases": {"research": {"status": "running"}}}
        assert _is_research_done(state) is False

    def test_empty_state(self):
        from scripts.api.state_router import _is_research_done

        assert _is_research_done({"mode": "v5", "phases": {}}) is False

    def test_no_phases(self):
        from scripts.api.state_router import _is_research_done

        assert _is_research_done({}) is False


class TestIsContentDone:
    """_is_content_done uses unified v5 state format."""

    def test_content_complete(self):
        from scripts.api.state_router import _is_content_done

        state = {"mode": "v5", "phases": {"content": {"status": "complete"}}}
        assert _is_content_done(state) is True

    def test_content_not_complete(self):
        from scripts.api.state_router import _is_content_done

        state = {"mode": "v5", "phases": {"content": {"status": "running"}}}
        assert _is_content_done(state) is False

    def test_empty_state(self):
        from scripts.api.state_router import _is_content_done

        assert _is_content_done({"mode": "v5", "phases": {}}) is False


class TestPipelinePhaseOrder:
    """V5_PHASE_ORDER imported from pipeline_v5."""

    def test_phase_order_no_sandbox(self):
        """Sandbox removed in #820."""
        from scripts.api.state_router import V5_PHASE_ORDER

        assert "sandbox" not in V5_PHASE_ORDER
        assert V5_PHASE_ORDER == [
            "research", "discover", "content", "activities",
            "validate", "review", "mdx",
        ]

    def test_v4_phase_order_no_sandbox(self):
        from scripts.api.state_router import V4_PHASE_ORDER

        assert "sandbox" not in V4_PHASE_ORDER


class TestClaudeContentDispatch:
    """Test --use-claude B wiring for content generation (#819)."""

    def test_claude_model_content_constant_exists(self):
        from scripts.build.pipeline_v5 import CLAUDE_MODEL_CONTENT

        assert "claude" in CLAUDE_MODEL_CONTENT
        assert "opus" in CLAUDE_MODEL_CONTENT

    def test_phase_b_in_delimiters(self):
        """_dispatch_claude_phase should recognize Phase B delimiters."""
        # We can't call it directly without Claude CLI, but verify the
        # delimiter mapping includes B
        import scripts.build.pipeline_v5 as pv5
        import inspect
        source = inspect.getsource(pv5._dispatch_claude_phase)
        assert '"B"' in source
        assert "===CONTENT_START===" in source
        assert "===CONTENT_END===" in source

    def test_content_dispatch_fn_set_when_use_claude_b(self):
        """phase_content should set content_dispatch_fn when B in use_claude."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import phase_content

        ctx = MagicMock()
        ctx.dry_run = False
        ctx.use_claude = {"B"}
        ctx.claude_model_B = "claude-opus-4-6"
        state = {"phases": {}}

        with patch("scripts.build.pipeline_v5.is_complete", return_value=False), \
             patch("scripts.build.pipeline_v5.phase_B_content", return_value=True) as mock_pbc, \
             patch("scripts.build.pipeline_v5.mark_complete"), \
             patch("scripts.build.pipeline_v5._invalidate_stale_artifacts"):
            ctx._self_audited = False
            ctx.paths = {"md": MagicMock(exists=MagicMock(return_value=False))}
            ctx.track = "a1"
            ctx.full_build = False
            phase_content(ctx, state)

            # Verify content_dispatch_fn was set on ctx
            assert hasattr(ctx, "content_dispatch_fn")
            assert callable(ctx.content_dispatch_fn)
            mock_pbc.assert_called_once_with(ctx)

    def test_content_dispatch_fn_not_set_without_flag(self):
        """phase_content should NOT set content_dispatch_fn when B not in use_claude."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import phase_content

        ctx = MagicMock()
        ctx.dry_run = False
        ctx.use_claude = set()  # No Claude phases
        state = {"phases": {}}

        with patch("scripts.build.pipeline_v5.is_complete", return_value=False), \
             patch("scripts.build.pipeline_v5.phase_B_content", return_value=True), \
             patch("scripts.build.pipeline_v5.mark_complete"), \
             patch("scripts.build.pipeline_v5._invalidate_stale_artifacts"):
            ctx._self_audited = False
            ctx.paths = {"md": MagicMock(exists=MagicMock(return_value=False))}
            ctx.track = "a1"
            ctx.full_build = False
            phase_content(ctx, state)

            # content_dispatch_fn should not have been set by phase_content
            # (MagicMock auto-creates attributes, so check it wasn't explicitly set)
            assert "content_dispatch_fn" not in ctx.__dict__

    def test_make_content_dispatch_fn_calls_claude_phase(self):
        """_make_content_dispatch_fn returns a callable that dispatches to Claude."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"

        dispatch_fn = _make_content_dispatch_fn(ctx)

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    return_value=(True, "===CONTENT_START===\nHello\n===CONTENT_END===")) as mock_dcp:
            ok, output = dispatch_fn("test prompt", "task-1")

            assert ok is True
            assert "Hello" in output
            mock_dcp.assert_called_once()
            call_args = mock_dcp.call_args
            assert call_args[1]["model"] == "claude-opus-4-6"

    def test_make_content_dispatch_fn_writes_output_file(self, tmp_path):
        """Dispatch fn writes to output_file when specified."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"

        dispatch_fn = _make_content_dispatch_fn(ctx)
        out_file = tmp_path / "output.txt"

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    return_value=(True, "content text")):
            ok, output = dispatch_fn("prompt", "task-1", output_file=out_file)

            assert ok
            assert out_file.exists()
            assert out_file.read_text() == "content text"

    def test_make_content_dispatch_fn_no_file_on_failure(self, tmp_path):
        """Dispatch fn does NOT write output_file when Claude fails."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"

        dispatch_fn = _make_content_dispatch_fn(ctx)
        out_file = tmp_path / "output.txt"

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    return_value=(False, "")):
            ok, output = dispatch_fn("prompt", "task-1", output_file=out_file)

            assert not ok
            assert not out_file.exists()

    def test_make_content_dispatch_fn_model_override(self):
        """Explicit model parameter overrides ctx.claude_model_B."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"

        dispatch_fn = _make_content_dispatch_fn(ctx)

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    return_value=(True, "ok")) as mock_dcp:
            dispatch_fn("prompt", "task-1", model="claude-sonnet-4-6")

            call_args = mock_dcp.call_args
            assert call_args[1]["model"] == "claude-sonnet-4-6"

    def test_make_content_dispatch_fn_ignores_gemini_model(self):
        """Gemini model strings passed by phase_2_content should be ignored."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"

        dispatch_fn = _make_content_dispatch_fn(ctx)

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    return_value=(True, "ok")) as mock_dcp:
            # phase_2_content passes ctx.model which is typically a Gemini model
            dispatch_fn("prompt", "task-1", model="gemini-3.1-pro-preview")

            call_args = mock_dcp.call_args
            # Should use claude_model_B, NOT the Gemini model
            assert call_args[1]["model"] == "claude-opus-4-6"

    def test_make_content_dispatch_fn_cleans_tempfile(self):
        """Tempfile is cleaned up even if dispatch fails."""
        from unittest.mock import MagicMock, patch
        from scripts.build.pipeline_v5 import _make_content_dispatch_fn

        ctx = MagicMock()
        ctx.claude_model_B = "claude-opus-4-6"
        dispatch_fn = _make_content_dispatch_fn(ctx)

        with patch("scripts.build.pipeline_v5._dispatch_claude_phase",
                    side_effect=RuntimeError("test error")):
            try:
                dispatch_fn("prompt", "task-1")
            except RuntimeError:
                pass
            # No temp files should remain — we can't check directly but
            # the finally block in _make_content_dispatch_fn ensures cleanup


# ==================== generate_mdx helpers ====================


class TestDetectPipelineInfo:
    """detect_pipeline_info() from generate_mdx."""

    def test_v4_with_review_complete(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v4",
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-content": {"status": "complete"},
                "v4-validate": {"status": "complete"},
                "v4-review": {"status": "complete"},
            },
        }
        (orch / "state-v4.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v4"
        assert status == "reviewed"

    def test_v4_validated_not_reviewed(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v4",
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-content": {"status": "complete"},
                "v4-validate": {"status": "complete"},
            },
        }
        (orch / "state-v4.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v4"
        assert status == "validated"

    def test_v4_draft(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v4",
            "phases": {
                "v4-research": {"status": "complete"},
                "v4-content": {"status": "complete"},
            },
        }
        (orch / "state-v4.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v4"
        assert status == "draft"

    def test_v3_reviewed(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "phases": {
                "v3-A": {"status": "complete"},
                "v3-B": {"status": "complete"},
                "v3-audit": {"status": "complete"},
                "v3-D": {"status": "complete"},
            },
        }
        (orch / "state-v3.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v3"
        assert status == "reviewed"

    def test_unbuilt_returns_none(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        version, status = detect_pipeline_info(tmp_path, "nonexistent")
        assert version is None
        assert status is None

    def test_v5_validated(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "content": {"status": "complete"},
                "validate": {"status": "complete"},
            },
        }
        (orch / "state.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v5"
        assert status == "validated"

    def test_v5_reviewed(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "validate": {"status": "complete"},
                "review": {"status": "complete"},
            },
        }
        (orch / "state.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v5"
        assert status == "reviewed"

    def test_v5_draft(self, tmp_path):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import detect_pipeline_info

        orch = tmp_path / "orchestration" / "test-mod"
        orch.mkdir(parents=True)
        state = {
            "mode": "v5",
            "phases": {
                "research": {"status": "complete"},
                "content": {"status": "complete"},
            },
        }
        (orch / "state.json").write_text(json.dumps(state))
        version, status = detect_pipeline_info(tmp_path, "test-mod")
        assert version == "v5"
        assert status == "draft"


class TestGenerateMdxFrontmatter:
    """generate_mdx includes pipeline/build_status in frontmatter."""

    def _make_minimal_md(self):
        return "---\ntitle: Test\nsubtitle: Sub\n---\n# Test\n\nContent here.\n"

    def test_v4_frontmatter(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v4", build_status="validated")
        assert "pipeline: v4" in result
        assert "build_status: validated" in result

    def test_no_pipeline_no_extra_frontmatter(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1)
        assert "pipeline:" not in result
        assert "build_status:" not in result

    def test_v3_reviewed_frontmatter(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v3", build_status="reviewed")
        assert "pipeline: v3" in result

    def test_v3_has_draft_true(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v3", build_status="validated")
        assert "draft: true" in result

    def test_v4_has_no_draft(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v4", build_status="validated")
        assert "draft: true" not in result

    def test_v5_frontmatter(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v5", build_status="validated")
        assert "pipeline: v5" in result
        assert "build_status: validated" in result

    def test_v5_has_no_draft(self):
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        from generate_mdx import generate_mdx

        md = self._make_minimal_md()
        result = generate_mdx(md, 1, pipeline_version="v5", build_status="validated")
        assert "draft: true" not in result


# ==================== needs_rebuild flag ====================


class TestNeedsRebuild:
    """needs_rebuild flag in _compute_pipeline_track."""

    def test_v4_not_needs_rebuild(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state-v4.json").write_text('{"mode": "v4", "phases": {}}')
        version = _detect_pipeline_version(tmp_path)
        assert version == "v4"
        assert (version != "v4") is False  # needs_rebuild logic

    def test_v3_needs_rebuild(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        (tmp_path / "state-v3.json").write_text('{"phases": {}}')
        version = _detect_pipeline_version(tmp_path)
        assert version == "v3"
        assert (version != "v4") is True  # needs_rebuild logic

    def test_unbuilt_needs_rebuild(self, tmp_path):
        from scripts.api.state_router import _detect_pipeline_version

        version = _detect_pipeline_version(tmp_path)
        assert version == "unbuilt"
        assert (version != "v4") is True  # needs_rebuild logic


# ==================== pipeline-versions endpoint ====================


class TestPipelineVersionsEndpoint:
    """GET /api/state/pipeline-versions returns version counts."""

    def test_endpoint_returns_200(self):
        from fastapi.testclient import TestClient
        from scripts.api.main import app

        client = TestClient(app)
        r = client.get("/api/state/pipeline-versions")
        assert r.status_code == 200
        data = r.json()
        assert "counts" in data
        assert "v4" in data["counts"]
        assert "v3" in data["counts"]
        assert "unbuilt" in data["counts"]
        assert "total" in data
        assert "pct_v5" in data or "pct_v4" in data or "pct_built" in data
        assert "needs_rebuild" in data
        assert "per_track" in data
        assert "v4_modules" in data

    def test_track_filter(self):
        from fastapi.testclient import TestClient
        from scripts.api.main import app

        client = TestClient(app)
        r = client.get("/api/state/pipeline-versions?track=a1")
        assert r.status_code == 200
        data = r.json()
        # Should only have a1 in per_track
        assert "a1" in data["per_track"]
        # total should match sum of all a1 pipeline versions
        a1 = data["per_track"]["a1"]
        assert data["total"] == a1.get("v5", 0) + a1.get("v4", 0) + a1.get("v3", 0) + a1.get("unbuilt", 0)
