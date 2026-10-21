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

import asyncio
import json
import os
import subprocess
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import scripts.api.dashboard_router as dashboard_router
from scripts.api.main import app

pytestmark = pytest.mark.reads_content

client = TestClient(app, raise_server_exceptions=False)


# ==================== Endpoint tests ====================


class TestHealthEndpoint:
    """GET /api/health returns server status."""

    @pytest.mark.parametrize("non_opaque_host_id", ["teacher.example.org", "host-job"])
    def test_health_never_echoes_a_non_opaque_lu_monitor_host_id(self, monkeypatch, non_opaque_host_id):
        # A real host name (a live FQDN) or a retired batch-host role
        # (RETIRED_HOST_IDS) must never leave /api/health verbatim, unlike a
        # freshly minted opaque id, which dashboards are designed to show.
        monkeypatch.setenv("LU_MONITOR_HOST_ID", non_opaque_host_id)
        data = client.get("/api/health").json()
        assert data["instance"]["host"] == "local"


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


class TestBuildStatusEndpoint:
    """GET /api/state/build-status agrees with per-track build status."""

    def test_per_track_counts_failed_audit_before_running_phase(self, tmp_path, monkeypatch):
        from scripts.api import state_build

        monkeypatch.setattr(state_build, "get_plan_slugs", lambda _track_id, *args, **kwargs: [(1, "failed-module")])
        monkeypatch.setattr(state_build, "detect_pipeline_version", lambda _orch_dir: "v6")
        monkeypatch.setattr(
            state_build,
            "scan_module_phases",
            lambda _orch_dir, _version: ("write", "audit(FAIL)", "2026-06-07T00:00:00Z", "failed"),
        )

        result = state_build.compute_build_status_track(
            "folk", {"path": "folk"}, curriculum_root=tmp_path
        )

        assert result["failed"] == 1
        assert result["building"] == 0
        assert result["queued"] == 0


class TestDashboardOverviewEndpoint:
    """GET /api/dashboard/overview returns tracks."""

    def test_track_counts_match_state_summary(self):
        summary = client.get("/api/state/summary?fresh=true").json()
        overview = client.get("/api/dashboard/overview").json()

        overview_counts = {track["id"]: track["module_count"] for track in overview["tracks"]}
        summary_counts = {track: stats["total"] for track, stats in summary["tracks"].items()}

        assert overview_counts == summary_counts
        # Retired aliases must not reappear once roster is manifest-derived (#5245).
        assert "lit-doc" not in overview_counts
        assert "lit-crimea" not in overview_counts
        assert "hist" in overview_counts
        assert overview_counts["hist"] == summary_counts["hist"]


# ==================== Router mounting tests ====================


class TestPublicMonitorSurfacesAndBoundaries:
    """Validate status codes for public Monitor surfaces, legacy aliases, and service boundaries."""

    def test_hramatka_readyz_returns_404(self):
        resp = client.get("/api/hramatka/readyz")
        assert resp.status_code == 404


# ==================== Helper function tests ====================


class TestReadYamlFile:
    """_read_yaml_file safely reads YAML files."""

    def test_reads_valid_yaml(self, tmp_path):
        from scripts.api.dashboard_helpers import read_yaml_file

        f = tmp_path / "test.yaml"
        f.write_text("key: value\nnum: 42")
        result = read_yaml_file(f)
        assert result == {"key": "value", "num": 42}

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


class TestDashboardModuleDetail:
    """module_detail should expose freshness-aware status metadata."""

    def test_status_uses_read_status(self, tmp_path, monkeypatch):

        track_dir = tmp_path / "curriculum" / "a1"
        status_dir = track_dir / "status"
        meta_dir = track_dir / "meta"
        status_dir.mkdir(parents=True)
        meta_dir.mkdir(parents=True)
        status_file = status_dir / "test-slug.json"
        meta_file = meta_dir / "test-slug.yaml"
        status_file.write_text(json.dumps({"overall": {"status": "pass"}}))
        meta_file.write_text("title: Test\n")
        newer = status_file.stat().st_mtime + 2
        os.utime(meta_file, (newer, newer))

        monkeypatch.setattr(dashboard_router, "LEVELS", [{"id": "a1", "path": "a1"}])
        monkeypatch.setattr(dashboard_router, "read_yaml_file", lambda _path: None)
        monkeypatch.setattr(dashboard_router, "find_research_path", lambda _track_dir, _slug: None)
        monkeypatch.setattr(dashboard_router, "default_research_info", lambda _track: {"exists": False})
        monkeypatch.setattr(
            dashboard_router,
            "extract_review_info",
            lambda _track_dir, _slug: {
                "review_score": None,
                "review_verdict": None,
                "plan_review_verdict": None,
            },
        )
        monkeypatch.setattr(dashboard_router, "get_orchestration_info", lambda _orch_dir: {})


        from scripts.api.monitor_context import fixture_context

        ctx = fixture_context(tmp_path)
        ctx = ctx.with_roots(curriculum_root=tmp_path / "curriculum")
        result = asyncio.run(dashboard_router.module_detail("a1", "test-slug", ctx=ctx))
        assert result["status"] == {"overall": {"status": "pass"}}
        assert result["status_is_fresh"] is False
        assert result["status_stale_sources"] == ["meta"]


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
