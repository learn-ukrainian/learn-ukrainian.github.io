"""
Tests for API endpoints and router mounting.

Validates:
  1. GET /api/health — returns 200 with status/version/uptime
  2. GET /api/config — returns levels and pipeline info
  3. GET /api/state/summary — returns 200 with track data
  4. GET /api/state/pipeline-versions — returns 200 with counts
  5. GET /api/dashboard/overview — returns 200 with tracks
  6. All routers are mounted (check app.routes)
  7. Extracted helpers: _read_yaml_file, _extract_word_count_from_status,
     _compute_track_stats, _extract_review_info, _get_orchestration_info,
     _classify_module_queue, _fetch_broker_messages, _default_research_info
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from scripts.api.main import app

client = TestClient(app, raise_server_exceptions=False)


# ==================== Endpoint tests ====================


class TestHealthEndpoint:
    """GET /api/health returns server status."""

    def test_returns_200(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_has_required_fields(self):
        data = client.get("/api/health").json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], int)

    def test_version_matches_app(self):
        data = client.get("/api/health").json()
        assert data["version"] == app.version


class TestConfigEndpoint:
    """GET /api/config returns levels and pipeline info."""

    def test_returns_200(self):
        resp = client.get("/api/config")
        assert resp.status_code == 200

    def test_has_levels(self):
        data = client.get("/api/config").json()
        assert "levels" in data
        assert isinstance(data["levels"], list)
        assert len(data["levels"]) > 0

    def test_has_api_version(self):
        data = client.get("/api/config").json()
        assert "api_version" in data

    def test_has_pipeline_info(self):
        data = client.get("/api/config").json()
        assert "pipeline" in data

    def test_uses_v6_pipeline_constants(self):
        from scripts.build.v6_build import PHASE_LABELS, PHASES

        data = client.get("/api/config").json()
        assert data["pipeline"]["phases"] == PHASES
        assert data["pipeline"]["phase_labels"] == PHASE_LABELS


class TestDispatcherScanEndpoint:
    """POST /api/batch/dispatcher/scan uses the project venv and checks failures."""

    def test_returns_200_on_success(self):
        with patch(
            "scripts.api.main.subprocess.run",
            return_value=subprocess.CompletedProcess(["scan"], 0),
        ) as mock_run:
            resp = client.post("/api/batch/dispatcher/scan")

        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        cmd = mock_run.call_args.args[0]
        assert cmd[0].endswith("/.venv/bin/python")

    def test_returns_500_on_subprocess_failure(self):
        with patch(
            "scripts.api.main.subprocess.run",
            return_value=subprocess.CompletedProcess(["scan"], 1),
        ):
            resp = client.post("/api/batch/dispatcher/scan")

        assert resp.status_code == 500
        assert resp.json()["detail"] == "Dispatcher scan failed"


class TestStateSummaryEndpoint:
    """GET /api/state/summary returns track data."""

    def test_returns_200(self):
        resp = client.get("/api/state/summary")
        assert resp.status_code == 200

    def test_has_tracks(self):
        data = client.get("/api/state/summary").json()
        assert "tracks" in data
        assert isinstance(data["tracks"], dict)


class TestPipelineVersionsEndpoint:
    """GET /api/state/pipeline-versions returns version counts."""

    def test_returns_200(self):
        resp = client.get("/api/state/pipeline-versions")
        assert resp.status_code == 200

    def test_has_counts(self):
        data = client.get("/api/state/pipeline-versions").json()
        assert "counts" in data


class TestDashboardOverviewEndpoint:
    """GET /api/dashboard/overview returns tracks."""

    def test_returns_200(self):
        resp = client.get("/api/dashboard/overview")
        assert resp.status_code == 200

    def test_has_tracks_and_totals(self):
        data = client.get("/api/dashboard/overview").json()
        assert "tracks" in data
        assert "totals" in data
        assert "timestamp" in data

    def test_totals_have_status_keys(self):
        data = client.get("/api/dashboard/overview").json()
        totals = data["totals"]
        for key in ["pass", "fail", "missing", "unaudited", "total"]:
            assert key in totals


# ==================== Router mounting tests ====================


class TestRouterMounting:
    """All routers are properly mounted in the app."""

    def _route_paths(self) -> set[str]:
        return {r.path for r in app.routes if hasattr(r, "path")}

    def test_dashboard_router_mounted(self):
        paths = self._route_paths()
        assert "/api/dashboard/overview" in paths

    def test_state_router_mounted(self):
        paths = self._route_paths()
        assert "/api/state/summary" in paths

    def test_health_endpoint_mounted(self):
        paths = self._route_paths()
        assert "/api/health" in paths

    def test_config_endpoint_mounted(self):
        paths = self._route_paths()
        assert "/api/config" in paths

    def test_comms_router_mounted(self):
        paths = self._route_paths()
        assert any("/api/comms" in p for p in paths)

    def test_blue_router_mounted(self):
        paths = self._route_paths()
        assert any("/api/blue" in p for p in paths)

    def test_gold_router_mounted(self):
        paths = self._route_paths()
        assert any("/api/gold" in p for p in paths)

    def test_admin_router_mounted(self):
        paths = self._route_paths()
        assert any("/api/admin" in p for p in paths)


# ==================== Helper function tests ====================


class TestReadYamlFile:
    """_read_yaml_file safely reads YAML files."""

    def test_reads_valid_yaml(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        f = tmp_path / "test.yaml"
        f.write_text("key: value\nnum: 42")
        result = read_yaml_file(f)
        assert result == {"key": "value", "num": 42}

    def test_returns_none_for_missing_file(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        result = read_yaml_file(tmp_path / "nonexistent.yaml")
        assert result is None

    def test_returns_none_for_invalid_yaml(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        f = tmp_path / "bad.yaml"
        f.write_text(":\n  - :\n    [invalid")
        result = read_yaml_file(f)
        assert result is None


class TestExtractWordCountFromStatus:
    """_extract_word_count_from_status parses lesson gate message."""

    def test_parses_word_count_and_target(self):
        from scripts.api.dashboard_helpers import extract_word_count_from_status as _extract_word_count_from_status

        class FakeResult:
            def __init__(self):
                self.data = {
                    "overall": {"status": "pass", "deferred_count": 0},
                    "gates": {"lesson": {"message": "1200 / 1500 words"}},
                    "timestamp": "2026-03-01T00:00:00Z",
                }

        wc, wt, dc, la = _extract_word_count_from_status(FakeResult())
        assert wc == 1200
        assert wt == 1500
        assert dc == 0
        assert la == "2026-03-01T00:00:00Z"

    def test_returns_zeros_for_none(self):
        from scripts.api.dashboard_helpers import extract_word_count_from_status as _extract_word_count_from_status

        wc, wt, dc, la = _extract_word_count_from_status(None)
        assert wc == 0
        assert wt == 0
        assert dc == 0
        assert la is None

    def test_returns_zeros_for_empty_data(self):
        from scripts.api.dashboard_helpers import extract_word_count_from_status as _extract_word_count_from_status

        class FakeResult:
            def __init__(self):
                self.data = None

        wc, _wt, _dc, _la = _extract_word_count_from_status(FakeResult())
        assert wc == 0

    def test_handles_deferred_count(self):
        from scripts.api.dashboard_helpers import extract_word_count_from_status as _extract_word_count_from_status

        class FakeResult:
            def __init__(self):
                self.data = {
                    "overall": {"status": "pass", "deferred_count": 3},
                    "gates": {"lesson": {"message": "500 / 1000 words"}},
                    "timestamp": None,
                }

        _, _, dc, _ = _extract_word_count_from_status(FakeResult())
        assert dc == 3


class TestComputeTrackStats:
    """_compute_track_stats aggregates module data."""

    def test_counts_statuses(self):
        from scripts.api.dashboard_helpers import compute_track_stats as _compute_track_stats

        modules = [
            {"status": "pass", "has_review": True, "has_final_review": False,
             "has_plan_review": False, "plan_review_verdict": None, "research": {}},
            {"status": "fail", "has_review": False, "has_final_review": False,
             "has_plan_review": True, "plan_review_verdict": "PASS", "research": {}},
            {"status": "missing", "has_review": False, "has_final_review": False,
             "has_plan_review": False, "plan_review_verdict": None, "research": {}},
        ]
        stats = _compute_track_stats(modules, "a1")
        assert stats["pass"] == 1
        assert stats["fail"] == 1
        assert stats["missing"] == 1
        assert stats["reviewed"] == 1
        assert stats["plan_pass"] == 1

    def test_empty_modules(self):
        from scripts.api.dashboard_helpers import compute_track_stats as _compute_track_stats

        stats = _compute_track_stats([], "a1")
        assert stats["pass"] == 0
        assert stats["missing"] == 0


class TestDefaultResearchInfo:
    """_default_research_info returns correct structure."""

    def test_has_required_keys(self):
        from scripts.api.dashboard_helpers import default_research_info as _default_research_info

        info = _default_research_info("a1")
        assert info["exists"] is False
        assert info["words"] == 0
        assert "quality" in info
        assert "profile" in info


class TestExtractReviewInfo:
    """_extract_review_info reads review files."""

    def test_no_reviews_exist(self, tmp_path):
        from scripts.api.dashboard_helpers import extract_review_info as _extract_review_info

        (tmp_path / "review").mkdir()
        (tmp_path / "audit").mkdir()
        info = _extract_review_info(tmp_path, "test-slug")
        assert info["has_review"] is False
        assert info["has_final_review"] is False
        assert info["review_score"] is None

    def test_review_exists_but_empty(self, tmp_path):
        from scripts.api.dashboard_helpers import extract_review_info as _extract_review_info

        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-slug-review.md").write_text("")
        (tmp_path / "audit").mkdir()
        info = _extract_review_info(tmp_path, "test-slug")
        assert info["has_review"] is True


class TestGetOrchestrationInfo:
    """_get_orchestration_info collects phase data."""

    def test_missing_dir(self, tmp_path):
        from scripts.api.dashboard_helpers import get_orchestration_info as _get_orchestration_info

        info = _get_orchestration_info(tmp_path / "nonexistent")
        assert info["orchestration"] == []
        assert info["pipeline_version"] == "unbuilt"
        assert info["needs_rebuild"] is True
        assert info["friction_count"] == 0

    def test_existing_dir_with_files(self, tmp_path):
        from scripts.api.dashboard_helpers import get_orchestration_info as _get_orchestration_info

        orch = tmp_path / "orch"
        orch.mkdir()
        (orch / "research-output.json").write_text("{}")
        (orch / "content-output.json").write_text("{}")
        info = _get_orchestration_info(orch)
        assert len(info["orchestration"]) == 2
        assert info["friction_count"] == 0

    def test_friction_files_counted(self, tmp_path):
        from scripts.api.dashboard_helpers import get_orchestration_info as _get_orchestration_info

        orch = tmp_path / "orch"
        orch.mkdir()
        (orch / "friction-1.json").write_text("{}")
        (orch / "friction-2.json").write_text("{}")
        (orch / "phase-1.json").write_text("{}")
        info = _get_orchestration_info(orch)
        assert info["friction_count"] == 2

    def test_v6_not_needs_rebuild(self, tmp_path):
        from scripts.api.dashboard_helpers import get_orchestration_info as _get_orchestration_info

        orch = tmp_path / "orch"
        orch.mkdir()
        (orch / "state.json").write_text('{"mode":"v6","phases":{}}')
        info = _get_orchestration_info(orch)
        assert info["pipeline_version"] == "v6"
        assert info["needs_rebuild"] is False


class TestBuildModuleInfo:
    """build_module_info keeps only v6 as current."""

    def test_v5_marks_needs_rebuild(self, tmp_path):
        from scripts.api.dashboard_helpers import build_module_info

        track_dir = tmp_path / "track"
        plans_dir = tmp_path / "plans"
        orch_dir = track_dir / "orchestration" / "test-slug"
        orch_dir.mkdir(parents=True)
        plans_dir.mkdir()

        with (
            patch("scripts.api.dashboard_helpers.get_source_paths", return_value={}),
            patch("scripts.api.dashboard_helpers.find_research_path", return_value=None),
            patch(
                "scripts.api.dashboard_helpers.extract_review_info",
                return_value={
                    "has_review": False,
                    "has_final_review": False,
                    "review_score": None,
                    "review_verdict": None,
                    "has_plan_review": False,
                    "plan_review_verdict": None,
                },
            ),
            patch("scripts.api.dashboard_helpers.detect_pipeline_version", return_value="v5"),
        ):
            result = build_module_info(track_dir, plans_dir, "a1", "test-slug", 0)

        assert result["pipeline_version"] == "v5"
        assert result["needs_rebuild"] is True


class TestWeakPointsEndpoint:
    """Weak points should compute research scores even for all-tracks queries."""

    def test_all_tracks_includes_research_scores(self, monkeypatch):
        import scripts.api.state_router as state_router

        monkeypatch.setattr(state_router, "LEVELS", [{"id": "a1", "path": "l2-uk-en/a1"}])
        monkeypatch.setattr(state_router, "CURRICULUM_ROOT", Path("/tmp/curriculum"))
        monkeypatch.setattr(state_router, "get_plan_slugs", lambda track_id: [(1, "test-slug")])
        monkeypatch.setattr(
            state_router,
            "get_audit_status",
            lambda _track_dir, _slug: {"status": "pass", "word_count": 100, "word_target": 200, "blocking_issues": []},
        )
        monkeypatch.setattr(state_router, "get_research_score", lambda *_args, **_kwargs: 6)
        monkeypatch.setattr(state_router, "get_word_target_from_plan", lambda *_args, **_kwargs: 200)
        monkeypatch.setattr(state_router, "detect_pipeline_version", lambda *_args, **_kwargs: "v6")

        response = client.get("/api/state/weak-points?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["modules"][0]["research_score"] == 6
        assert "research_score_6" in data["modules"][0]["issues"]


class TestClassifyModuleQueue:
    """_classify_module_queue routes modules to the right queue."""

    def test_missing_status_no_md_returns_otaman(self, tmp_path):
        from scripts.api.dashboard_helpers import classify_module_queue as _classify_module_queue

        status_file = tmp_path / "status" / "test.json"
        result = _classify_module_queue("a1", tmp_path, "test", 0, status_file)
        assert result == "otaman"

    def test_missing_status_with_md_returns_none(self, tmp_path):
        from scripts.api.dashboard_helpers import classify_module_queue as _classify_module_queue

        (tmp_path / "test.md").write_text("content")
        status_file = tmp_path / "nonexistent.json"
        result = _classify_module_queue("a1", tmp_path, "test", 0, status_file)
        assert result is None

    def test_content_complete_returns_hetman(self, tmp_path):
        from scripts.api.dashboard_helpers import classify_module_queue as _classify_module_queue

        sf = tmp_path / "status.json"
        sf.write_text(json.dumps({"overall": {"status": "content-complete", "deferred_count": 0}}))
        result = _classify_module_queue("a1", tmp_path, "test", 0, sf)
        assert result == "hetman"

    def test_pass_without_final_review_returns_final_review(self, tmp_path):
        from scripts.api.dashboard_helpers import classify_module_queue as _classify_module_queue

        sf = tmp_path / "status.json"
        sf.write_text(json.dumps({"overall": {"status": "pass", "deferred_count": 0}}))
        result = _classify_module_queue("a1", tmp_path, "test", 0, sf)
        assert result == "final_review"

    def test_pass_with_final_review_returns_none(self, tmp_path):
        from scripts.api.dashboard_helpers import classify_module_queue as _classify_module_queue

        sf = tmp_path / "status.json"
        sf.write_text(json.dumps({"overall": {"status": "pass", "deferred_count": 0}}))
        review_dir = tmp_path / "review"
        review_dir.mkdir()
        (review_dir / "test-final-review.md").write_text("ok")
        result = _classify_module_queue("a1", tmp_path, "test", 0, sf)
        assert result is None
