"""Tests for API routers: comms batch progress and live activity, and sources.

Targets ~150+ tests for coverage improvement.
"""

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.reads_content

# ---------------------------------------------------------------------------
# Fixtures: test apps with one router mounted each
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_project_root(tmp_path):
    """Set up a fake project root with required directory structure."""
    # Create directory structure
    (tmp_path / "data" / "backups").mkdir(parents=True)
    (tmp_path / "data" / "textbook_images").mkdir(parents=True)
    (tmp_path / "data" / "textbooks").mkdir(parents=True)
    (tmp_path / "data" / "textbook_chunks").mkdir(parents=True)
    (tmp_path / "data" / "literary_texts").mkdir(parents=True)
    (tmp_path / "logs").mkdir(parents=True)
    (tmp_path / "logs" / "research-preseed").mkdir(parents=True)
    (tmp_path / "curriculum" / "l2-uk-en").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def _patch_config(mock_project_root):
    """Patch config module paths to use tmp_path.

    comms_router itself keeps no path globals since #7269 step 5 — it
    resolves everything from the app's MonitorContext — so steering comms
    routes at the fixture root happens via ``app.state.ctx`` (see
    ``comms_client`` and ``_comms_ctx``). The config patches below remain
    for helpers that read ``lu_machinery.api.config``.
    """
    with (
        patch("lu_machinery.api.config.PROJECT_ROOT", mock_project_root),
        patch("lu_machinery.api.config.CURRICULUM_ROOT", mock_project_root / "curriculum" / "l2-uk-en"),
    ):
        yield


def _comms_ctx(project_root):
    """Build the comms app context for the fixture root (#7269 step 5).

    Same pattern as ``tests/test_comms_router_expiry_sweep.py``: a fixture
    context whose roots all live under the test's project root.
    """

    from lu_machinery.api.monitor_context import fixture_context

    return fixture_context(project_root)


@pytest.fixture()
def comms_client(_patch_config, mock_project_root):
    """TestClient for the comms router and the product batch-progress routes under its prefix."""
    from lu_machinery.api.comms_router import router

    from scripts.project_api.batch_progress import router as batch_progress_router
    app = FastAPI()
    app.state.ctx = _comms_ctx(mock_project_root)
    app.include_router(batch_progress_router, prefix="/api/comms")
    app.include_router(router, prefix="/api/comms")
    return TestClient(app)


@pytest.fixture()
def rag_client(mock_project_root):
    """TestClient for sources router."""
    from lu_machinery.api.monitor_context import fixture_context

    from scripts.project_api.sources_router import router

    app = FastAPI()
    app.state.ctx = fixture_context(mock_project_root)
    app.include_router(router, prefix="/api/sources")
    yield TestClient(app)


# ===========================================================================
# COMMS ROUTER TESTS
# ===========================================================================


class TestCommsBatchProgress:
    """Tests for /api/comms/batch-progress endpoint."""

    def test_batch_progress_with_logs(self, comms_client, mock_project_root):
        log_dir = mock_project_root / "logs" / "research-preseed"
        log_file = log_dir / "hist-20260301-0100.log"
        log_file.write_text("VERDICT: PASS\nVERDICT: PASS\nVERDICT: FAIL\nBATCH COMPLETE\nPassed: 2\n")
        with patch("scripts.project_api.batch_progress._check_build_processes", return_value=([], None)):
            r = comms_client.get("/api/comms/batch-progress")
        data = r.json()
        assert "hist" in data["tracks"]
        assert data["tracks"]["hist"]["health"] == "complete"


class TestCommsLiveActivity:
    """Tests for /api/comms/live-activity endpoint."""

    def test_live_activity_with_state_file(self, comms_client, mock_project_root):
        # Create a recently-modified state-v3.json
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "test-module"
        orch_dir.mkdir(parents=True)
        state = {
            "slug": "test-module",
            "phases": {
                "v3-content": {
                    "status": "running",
                    "ts": datetime.now(UTC).isoformat(),
                    "task_id": "task-1",
                    "mode": "build",
                },
            },
        }
        (orch_dir / "state-v3.json").write_text(json.dumps(state))
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        data = r.json()
        assert len(data["in_progress"]) >= 1

    def test_live_activity_with_v6_state_file(self, comms_client, mock_project_root):
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "v6-module"
        orch_dir.mkdir(parents=True)
        state = {
            "mode": "v6",
            "slug": "v6-module",
            "phases": {
                "write": {
                    "status": "running",
                    "ts": datetime.now(UTC).isoformat(),
                    "task_id": "task-v6",
                    "mode": "build",
                },
            },
        }
        (orch_dir / "state.json").write_text(json.dumps(state))
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        data = r.json()
        assert any(item["slug"] == "v6-module" and item["phase"] == "write" for item in data["in_progress"])


# ===========================================================================
# PATH SAFETY TESTS
# ===========================================================================


class TestPathSafety:
    """Tests for path_safety.safe_join."""

    def test_safe_join_valid(self, tmp_path):
        # _safe_within was replaced by path_safety.safe_join in commit
        # 9fe99a00a7. Same guarantee, raises ValueError instead of bool.
        from lu_machinery.path_safety import safe_join
        result = safe_join(tmp_path, "child", "file.txt")
        assert result.name == "file.txt"

    def test_safe_join_traversal(self, tmp_path):
        from lu_machinery.path_safety import safe_join
        with pytest.raises(ValueError):
            safe_join(tmp_path, "..", "etc", "passwd")


class TestRagBrowseImages:
    """Tests for /api/sources/browse_images and /api/sources/stats."""

    def test_browse_images_rejects_invalid_grade(self, rag_client):
        r = rag_client.get("/api/sources/browse_images", params={"grade": "../etc"})
        assert r.status_code == 400
        assert r.json()["error"] == "Invalid grade format: ../etc"

    def test_stats_missing_corpus_keeps_documented_envelope(self, rag_client):
        r = rag_client.get("/api/sources/stats")
        assert r.status_code == 200
        assert r.json() == {"sources_db": {"error": "data/sources.db not found"}}


class TestCommsInternalHelpers:
    """Tests for internal helper functions in comms_router."""

    def test_check_build_processes_failure(self, _patch_config):
        from scripts.project_api.batch_progress import _check_build_processes
        with patch("subprocess.run", side_effect=Exception("no ps")):
            processes, error = _check_build_processes()
        assert processes == []
        assert error == "ps: Exception"


# ===========================================================================
# ADDITIONAL TESTS TO REACH 150+
# ===========================================================================


class TestCommsPreseedLogParsing:
    """Test preseed log parsing with various formats."""

    def test_scan_preseed_logs_with_last_line(self, _patch_config, mock_project_root):
        from scripts.project_api.batch_progress import _scan_preseed_logs
        log_dir = mock_project_root / "logs" / "research-preseed"
        log_content = (
            "Starting batch...\n"
            "VERDICT: PASS\n"
            "VERDICT: FAIL\n"
            "ERROR: something went wrong\n"
            "=====\n"
            "Last meaningful line here\n"
        )
        (log_dir / "hist-20260301-0100.log").write_text(log_content)
        result = _scan_preseed_logs(_comms_ctx(mock_project_root))
        assert len(result) == 1
        assert result[0]["passed"] == 1
        assert result[0]["failed"] == 2  # FAIL + ERROR
        assert "Last meaningful line" in result[0]["last_line"]
        assert result[0]["complete"] is False

    def test_scan_preseed_logs_no_timestamp_match(self, _patch_config, mock_project_root):
        from scripts.project_api.batch_progress import _scan_preseed_logs
        log_dir = mock_project_root / "logs" / "research-preseed"
        (log_dir / "random.log").write_text("no timestamp\n")
        result = _scan_preseed_logs(_comms_ctx(mock_project_root))
        assert result == []
