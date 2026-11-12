"""Tests for API routers: comms, batch progress, sources and route contracts.

Targets ~150+ tests for coverage improvement.
"""

import json
import os
import sqlite3
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
    (tmp_path / ".mcp" / "servers" / "message-broker" / "pids").mkdir(parents=True)
    (tmp_path / "curriculum" / "l2-uk-en").mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def broker_db(mock_project_root):
    """Create a SQLite broker DB with the messages table."""
    db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            from_llm TEXT,
            to_llm TEXT,
            message_type TEXT,
            content TEXT,
            data TEXT,
            timestamp TEXT,
            acknowledged INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    return db_path


def _insert_messages(db_path, messages):
    """Helper to insert test messages into broker DB."""
    conn = sqlite3.connect(str(db_path))
    for msg in messages:
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, message_type, content, data, timestamp, acknowledged) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg.get("task_id", "test-task"),
                msg.get("from_llm", "claude"),
                msg.get("to_llm", "gemini"),
                msg.get("message_type", "message"),
                msg.get("content", "test content"),
                msg.get("data", ""),
                msg.get("timestamp", datetime.now(UTC).isoformat()),
                msg.get("acknowledged", 0),
            ),
        )
    conn.commit()
    conn.close()


@pytest.fixture()
def _patch_config(mock_project_root, broker_db):
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
        patch("lu_machinery.api.config.MESSAGE_DB", broker_db),
    ):
        yield


def _comms_ctx(project_root, **root_overrides):
    """Build the comms app context for the fixture root (#7269 step 5).

    Same pattern as ``tests/test_comms_router_expiry_sweep.py``: a fixture
    context whose roots all live under the test's project root.
    ``root_overrides`` replace individual ``MonitorRoots`` fields (e.g.
    ``pid_dir=Path("/nonexistent")``).
    """

    from lu_machinery.api.monitor_context import fixture_context

    ctx = fixture_context(project_root)
    if root_overrides:
        ctx = ctx.with_roots(**root_overrides)
    return ctx


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


@pytest.fixture()
def contracts_client(mock_project_root):
    """TestClient for contracts router."""
    from lu_machinery.api.monitor_context import fixture_context
    from lu_machinery.api.route_contracts import router

    app = FastAPI()
    app.state.ctx = fixture_context(mock_project_root)
    app.include_router(router, prefix="/api/contracts")
    yield TestClient(app)


# ===========================================================================
# COMMS ROUTER TESTS
# ===========================================================================


class TestCommsMessages:
    """Tests for /api/comms/messages endpoint."""

    def test_messages_no_db(self, comms_client, mock_project_root):
        """When DB doesn't exist, return empty with error."""
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        r = comms_client.get("/api/comms/messages")
        assert r.status_code == 200
        assert r.json()["error"] == "Broker DB not found"

    def test_messages_with_data(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"content": "hello", "from_llm": "claude", "to_llm": "gemini"},
            {"content": "world", "from_llm": "gemini", "to_llm": "claude"},
        ])
        r = comms_client.get("/api/comms/messages")
        assert r.json()["total"] == 2

    def test_messages_unacked_only(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"acknowledged": 0},
            {"acknowledged": 1},
        ])
        r = comms_client.get("/api/comms/messages", params={"unacked_only": True})
        assert r.json()["total"] == 1


class TestCommsConversations:
    """Tests for /api/comms/conversations endpoint."""

    def test_conversations_grouped(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "task-A", "from_llm": "claude"},
            {"task_id": "task-A", "from_llm": "gemini"},
            {"task_id": "task-B", "from_llm": "claude"},
        ])
        r = comms_client.get("/api/comms/conversations")
        convos = r.json()["conversations"]
        assert len(convos) == 2


class TestCommsConversationDetail:
    """Tests for /api/comms/conversation/{task_id} endpoint."""

    def test_conversation_detail(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "task-X", "content": "msg1"},
            {"task_id": "task-X", "content": "msg2"},
            {"task_id": "task-Y", "content": "msg3"},
        ])
        r = comms_client.get("/api/comms/conversation/task-X")
        data = r.json()
        assert data["task_id"] == "task-X"
        assert data["count"] == 2

    def test_conversation_detail_limited_with_cursor(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "task-X", "content": f"msg{i}"}
            for i in range(5)
        ])
        r = comms_client.get("/api/comms/conversation/task-X", params={"limit": 2})
        data = r.json()
        assert data["count"] == 2
        assert data["total"] == 5
        assert data["next_cursor"] == 4

        r2 = comms_client.get(
            "/api/comms/conversation/task-X",
            params={"limit": 2, "cursor": data["next_cursor"]},
        )
        assert [m["id"] for m in r2.json()["messages"]] == [2, 3]


class TestCommsActiveProcesses:
    """Tests for /api/comms/active-processes endpoint."""

    def test_with_pid_files(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        pid_data = {
            "pid": os.getpid(),  # current process, should be alive
            "agent": "claude",
            "task_id": "t1",
            "model": "gpt-4",
            "mode": "review",
            "started": datetime.now(UTC).isoformat(),
        }
        (pid_dir / "proc1.json").write_text(json.dumps(pid_data))
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["alive"] == 1
        assert data["processes"][0]["alive"] is True

    def test_with_dead_pid(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "dead.json").write_text(json.dumps({
            "pid": 99999999,  # almost certainly not running
            "started": datetime.now(UTC).isoformat(),
        }))
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["alive"] == 0

    def test_corrupt_pid_file(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "corrupt.json").write_text("not json!")
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["count"] == 1
        assert data["processes"][0]["error"] == "corrupt"


class TestCommsZombies:
    """Tests for /api/comms/zombies endpoint."""

    def test_stale_messages(self, comms_client, broker_db):
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [
            {"timestamp": old_ts, "acknowledged": 0, "task_id": "stale-task"},
        ])
        r = comms_client.get("/api/comms/zombies", params={"stale_hours": 0.001})
        zombies = r.json()["zombies"]
        stale = [z for z in zombies if z["type"] == "stale_message"]
        assert len(stale) >= 1

    def test_stale_message_severity_critical(self, comms_client, broker_db):
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [
            {"timestamp": old_ts, "acknowledged": 0},
        ])
        r = comms_client.get("/api/comms/zombies", params={"stale_hours": 0.001})
        stale = [z for z in r.json()["zombies"] if z["type"] == "stale_message"]
        # Old enough to be critical (> 2x stale_hours)
        assert stale[0]["severity"] == "critical"

    def test_error_loops(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "err-task", "message_type": "error"},
            {"task_id": "err-task", "message_type": "error"},
            {"task_id": "err-task", "message_type": "error"},
        ])
        r = comms_client.get("/api/comms/zombies")
        error_loops = [z for z in r.json()["zombies"] if z["type"] == "error_loop"]
        assert len(error_loops) == 1
        assert error_loops[0]["error_count"] == 3

    def test_orphan_pid(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "orphan.json").write_text(json.dumps({"pid": 99999999, "task_id": "orphan-task"}))
        r = comms_client.get("/api/comms/zombies")
        orphans = [z for z in r.json()["zombies"] if z["type"] == "orphan_pid"]
        assert len(orphans) == 1


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


class TestContractsRoutes:
    """Tests for /api/contracts routes (#7329)."""

    def test_get_routes_returns_200(self, contracts_client):
        r = contracts_client.get("/api/contracts/routes")
        assert r.status_code == 200
        data = r.json()
        assert "generated_at" in data
        assert "route_contracts" in data
        assert "page_contracts" in data
        assert len(data["route_contracts"]) > 0
        assert len(data["page_contracts"]) > 0
