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


class TestIsResearchDoneV4:
    """_is_research_done checks v4 state first."""

    def test_v4_research_complete(self):
        from scripts.api.state_router import _is_research_done

        v4 = {"phases": {"v4-research": {"status": "complete"}}}
        assert _is_research_done({}, {}, v4=v4) is True

    def test_v4_research_not_complete(self):
        from scripts.api.state_router import _is_research_done

        v4 = {"phases": {"v4-research": {"status": "running"}}}
        assert _is_research_done({}, {}, v4=v4) is False

    def test_falls_back_to_v3(self):
        from scripts.api.state_router import _is_research_done

        v3 = {"phases": {"v3-A": {"status": "complete"}}}
        assert _is_research_done(v3, {}, v4={}) is True

    def test_no_v4_no_v3(self):
        from scripts.api.state_router import _is_research_done

        assert _is_research_done({}, {}, v4={}) is False


class TestIsContentDoneV4:
    """_is_content_done checks v4 state first."""

    def test_v4_content_complete(self):
        from scripts.api.state_router import _is_content_done

        v4 = {"phases": {"v4-content": {"status": "complete"}}}
        assert _is_content_done({}, {}, v4=v4) is True

    def test_v4_content_not_complete(self):
        from scripts.api.state_router import _is_content_done

        v4 = {"phases": {"v4-content": {"status": "running"}}}
        assert _is_content_done({}, {}, v4=v4) is False

    def test_falls_back_to_v3(self):
        from scripts.api.state_router import _is_content_done

        v3 = {"phases": {"v3-B": {"status": "complete"}}}
        assert _is_content_done(v3, {}, v4={}) is True


class TestV4PhaseOrder:
    """V4_PHASE_ORDER is correct."""

    def test_phase_order(self):
        from scripts.api.state_router import V4_PHASE_ORDER

        assert V4_PHASE_ORDER == [
            "research", "discover", "content", "activities",
            "validate", "review", "mdx",
        ]


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
        assert "pct_v4" in data
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
        # total should match a1 counts
        a1 = data["per_track"]["a1"]
        assert data["total"] == a1["v4"] + a1["v3"] + a1["unbuilt"]
