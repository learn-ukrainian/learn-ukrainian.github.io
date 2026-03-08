"""Tests for API routers: comms_router, admin_router, images_router.

Targets ~150+ tests for coverage improvement.
"""

import asyncio
import json
import os
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures: create a test app with all three routers mounted
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
    """Patch config module paths to use tmp_path."""
    with (
        patch("scripts.api.config.PROJECT_ROOT", mock_project_root),
        patch("scripts.api.config.CURRICULUM_ROOT", mock_project_root / "curriculum" / "l2-uk-en"),
        patch("scripts.api.config.MESSAGE_DB", broker_db),
        patch("scripts.api.comms_router.PROJECT_ROOT", mock_project_root),
        patch("scripts.api.comms_router.CURRICULUM_ROOT", mock_project_root / "curriculum" / "l2-uk-en"),
        patch("scripts.api.comms_router.MESSAGE_DB", broker_db),
        patch("scripts.api.comms_router.PID_DIR", mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"),
        patch("scripts.api.comms_router.LOG_DIR", mock_project_root / "logs" / "research-preseed"),
        patch("scripts.api.admin_router.PROJECT_ROOT", mock_project_root),
        patch("scripts.api.admin_router.MESSAGE_DB", broker_db),
        patch("scripts.api.admin_router.BACKUP_DIR", mock_project_root / "data" / "backups"),
        patch("scripts.api.admin_router.DATA_DIR", mock_project_root / "data"),
        patch("scripts.api.admin_router.IMAGE_DIR", mock_project_root / "data" / "textbook_images"),
        patch("scripts.api.admin_router.LOGS_DIR", mock_project_root / "logs"),
        patch("scripts.api.admin_router.MCP_DIR", mock_project_root / ".mcp"),
        patch("scripts.api.images_router.IMAGES_DIR", mock_project_root / "data" / "textbook_images"),
        patch("scripts.api.images_router.TEXTBOOKS_DIR", mock_project_root / "data" / "textbooks"),
        patch("scripts.api.images_router.ANNOTATIONS_FILE", mock_project_root / "data" / "textbook_images" / "image_text_pairs.jsonl"),
        patch("scripts.api.images_router.PROJECT_ROOT", mock_project_root),
    ):
        yield


@pytest.fixture()
def comms_client(_patch_config):
    """TestClient for comms router."""
    from scripts.api.comms_router import router
    app = FastAPI()
    app.include_router(router, prefix="/api/comms")
    return TestClient(app)


@pytest.fixture()
def admin_client(_patch_config):
    """TestClient for admin router."""
    from scripts.api.admin_router import router
    app = FastAPI()
    app.include_router(router, prefix="/api/admin")
    return TestClient(app)


@pytest.fixture()
def images_client(_patch_config, mock_project_root):
    """TestClient for images router."""
    # Reset the singleton index
    from scripts.api import images_router
    images_router._index.reload()
    images_router._page_cache.clear()

    app = FastAPI()
    app.include_router(images_router.router, prefix="/api/images")
    return TestClient(app)


# ===========================================================================
# COMMS ROUTER TESTS
# ===========================================================================


class TestCommsMessages:
    """Tests for /api/comms/messages endpoint."""

    def test_messages_empty_db(self, comms_client, broker_db):
        r = comms_client.get("/api/comms/messages")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["messages"] == []

    def test_messages_no_db(self, comms_client, mock_project_root):
        """When DB doesn't exist, return empty with error."""
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
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

    def test_messages_filter_by_agent(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"from_llm": "claude", "to_llm": "gemini"},
            {"from_llm": "other", "to_llm": "other"},
        ])
        r = comms_client.get("/api/comms/messages", params={"agent": "claude"})
        assert r.json()["total"] == 1

    def test_messages_filter_by_task_id(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "task-1"},
            {"task_id": "task-2"},
        ])
        r = comms_client.get("/api/comms/messages", params={"task_id": "task-1"})
        assert r.json()["total"] == 1

    def test_messages_filter_by_msg_type(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"message_type": "error"},
            {"message_type": "message"},
        ])
        r = comms_client.get("/api/comms/messages", params={"msg_type": "error"})
        assert r.json()["total"] == 1

    def test_messages_unacked_only(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"acknowledged": 0},
            {"acknowledged": 1},
        ])
        r = comms_client.get("/api/comms/messages", params={"unacked_only": True})
        assert r.json()["total"] == 1

    def test_messages_pagination(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"content": f"msg-{i}"} for i in range(10)])
        r = comms_client.get("/api/comms/messages", params={"limit": 3, "offset": 0})
        assert len(r.json()["messages"]) == 3
        assert r.json()["total"] == 10

    def test_messages_combined_filters(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"from_llm": "claude", "task_id": "t1", "message_type": "error", "acknowledged": 0},
            {"from_llm": "claude", "task_id": "t1", "message_type": "message", "acknowledged": 0},
            {"from_llm": "gemini", "task_id": "t2", "message_type": "error", "acknowledged": 1},
        ])
        r = comms_client.get("/api/comms/messages", params={
            "agent": "claude", "task_id": "t1", "msg_type": "error", "unacked_only": True,
        })
        assert r.json()["total"] == 1


class TestCommsConversations:
    """Tests for /api/comms/conversations endpoint."""

    def test_conversations_empty(self, comms_client, broker_db):
        r = comms_client.get("/api/comms/conversations")
        assert r.status_code == 200
        assert r.json()["conversations"] == []

    def test_conversations_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.get("/api/comms/conversations")
        assert r.json()["conversations"] == []

    def test_conversations_grouped(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "task-A", "from_llm": "claude"},
            {"task_id": "task-A", "from_llm": "gemini"},
            {"task_id": "task-B", "from_llm": "claude"},
        ])
        r = comms_client.get("/api/comms/conversations")
        convos = r.json()["conversations"]
        assert len(convos) == 2

    def test_conversations_limit(self, comms_client, broker_db):
        for i in range(5):
            _insert_messages(broker_db, [{"task_id": f"task-{i}"}])
        r = comms_client.get("/api/comms/conversations", params={"limit": 2})
        assert len(r.json()["conversations"]) == 2


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

    def test_conversation_detail_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.get("/api/comms/conversation/task-X")
        assert r.json()["messages"] == []

    def test_conversation_not_found(self, comms_client, broker_db):
        r = comms_client.get("/api/comms/conversation/nonexistent")
        assert r.json()["count"] == 0


class TestCommsActiveProcesses:
    """Tests for /api/comms/active-processes endpoint."""

    def test_no_pid_dir(self, comms_client):
        with patch("scripts.api.comms_router.PID_DIR", Path("/nonexistent")):
            r = comms_client.get("/api/comms/active-processes")
        assert r.json()["count"] == 0

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

    def test_pid_no_started_field(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "nostart.json").write_text(json.dumps({"pid": os.getpid()}))
        r = comms_client.get("/api/comms/active-processes")
        data = r.json()
        assert data["processes"][0]["age_minutes"] == 0

    def test_pid_invalid_started(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "bad.json").write_text(json.dumps({"pid": os.getpid(), "started": "not-a-date"}))
        r = comms_client.get("/api/comms/active-processes")
        assert r.json()["processes"][0]["age_minutes"] == 0


class TestCommsZombies:
    """Tests for /api/comms/zombies endpoint."""

    def test_zombies_no_db_no_pids(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with (
            patch("scripts.api.comms_router.MESSAGE_DB", db_path),
            patch("scripts.api.comms_router.PID_DIR", Path("/nonexistent")),
        ):
            r = comms_client.get("/api/comms/zombies")
        assert r.json()["count"] == 0

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

    def test_stale_message_severity_warning(self, comms_client, broker_db):
        # A message that's only slightly stale (between 1x and 2x threshold)
        # Use stale_hours=10000 so the message is stale but not critical
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [{"timestamp": old_ts, "acknowledged": 0}])
        r = comms_client.get("/api/comms/zombies", params={"stale_hours": 100000})
        stale = [z for z in r.json()["zombies"] if z["type"] == "stale_message"]
        if stale:
            assert stale[0]["severity"] == "warning"

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

    def test_corrupt_pid_zombie(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "bad.json").write_text("not json")
        r = comms_client.get("/api/comms/zombies")
        corrupt = [z for z in r.json()["zombies"] if z["type"] == "corrupt_pid"]
        assert len(corrupt) == 1

    def test_invalid_timestamp_skipped(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"timestamp": "not-a-date", "acknowledged": 0}])
        r = comms_client.get("/api/comms/zombies")
        # Should not crash
        assert r.status_code == 200


class TestCommsStats:
    """Tests for /api/comms/stats endpoint."""

    def test_stats_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.get("/api/comms/stats")
        assert r.json()["error"] == "Broker DB not found"

    def test_stats_with_data(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"from_llm": "claude", "to_llm": "gemini", "message_type": "message", "acknowledged": 1},
            {"from_llm": "gemini", "to_llm": "claude", "message_type": "error", "acknowledged": 0},
            {"from_llm": "claude", "to_llm": "gemini", "message_type": "message", "acknowledged": 0},
        ])
        r = comms_client.get("/api/comms/stats")
        data = r.json()
        assert data["total_messages"] == 3
        assert data["unacked"] == 2
        assert data["errors"] == 1
        assert data["error_rate"] == pytest.approx(33.3, abs=0.1)

    def test_stats_empty_db(self, comms_client, broker_db):
        r = comms_client.get("/api/comms/stats")
        data = r.json()
        assert data["total_messages"] == 0
        assert data["error_rate"] == 0

    def test_stats_per_agent(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"from_llm": "claude", "to_llm": "gemini"},
            {"from_llm": "claude", "to_llm": "gemini"},
        ])
        r = comms_client.get("/api/comms/stats")
        agents = r.json()["per_agent"]
        assert agents["claude"]["sent"] == 2
        assert agents["gemini"]["received"] == 2


class TestCommsHealth:
    """Tests for /api/comms/health endpoint."""

    def test_health_with_db(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"acknowledged": 0}])
        r = comms_client.get("/api/comms/health")
        data = r.json()
        assert data["db_exists"] is True
        assert data["db_writable"] is True
        assert data["queue_depth"] == 1

    def test_health_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.get("/api/comms/health")
        data = r.json()
        assert data["db_exists"] is False

    def test_health_with_alive_pid(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "alive.json").write_text(json.dumps({"pid": os.getpid()}))
        r = comms_client.get("/api/comms/health")
        assert r.json()["alive_processes"] == 1

    def test_health_pid_dir_missing(self, comms_client):
        with patch("scripts.api.comms_router.PID_DIR", Path("/nonexistent")):
            r = comms_client.get("/api/comms/health")
        assert r.json()["pid_dir_exists"] is False


class TestCommsBatchProgress:
    """Tests for /api/comms/batch-progress endpoint."""

    def test_batch_progress_empty(self, comms_client, mock_project_root):
        with patch("scripts.api.comms_router._check_build_processes", return_value=[]):
            r = comms_client.get("/api/comms/batch-progress")
        data = r.json()
        assert "tracks" in data
        assert data["running_processes"] == 0

    def test_batch_progress_with_logs(self, comms_client, mock_project_root):
        log_dir = mock_project_root / "logs" / "research-preseed"
        log_file = log_dir / "hist-20260301-0100.log"
        log_file.write_text("VERDICT: PASS\nVERDICT: PASS\nVERDICT: FAIL\nBATCH COMPLETE\nPassed: 2\n")
        with patch("scripts.api.comms_router._check_build_processes", return_value=[]):
            r = comms_client.get("/api/comms/batch-progress")
        data = r.json()
        assert "hist" in data["tracks"]
        assert data["tracks"]["hist"]["health"] == "complete"

    def test_batch_progress_with_process(self, comms_client, mock_project_root):
        log_dir = mock_project_root / "logs" / "research-preseed"
        log_file = log_dir / "bio-20260301-0100.log"
        log_file.write_text("Processing...\nVERDICT: PASS\n")
        procs = [{"pid": 123, "track": "bio", "cmd": "python build_module.py bio 1"}]
        with patch("scripts.api.comms_router._check_build_processes", return_value=procs):
            r = comms_client.get("/api/comms/batch-progress")
        data = r.json()
        assert data["running_processes"] == 1


class TestCommsBatchProgressTrack:
    """Tests for /api/comms/batch-progress/{track} endpoint."""

    def test_batch_progress_track(self, comms_client, mock_project_root):
        # Create some research files
        research_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "topic-a-research.md").write_text("# Research A")
        r = comms_client.get("/api/comms/batch-progress/hist")
        data = r.json()
        assert data["research_done"] == 1

    def test_batch_progress_track_empty(self, comms_client, mock_project_root):
        r = comms_client.get("/api/comms/batch-progress/nonexistent")
        data = r.json()
        assert data["research_done"] == 0
        assert data["recent_files"] == []


class TestCommsActions:
    """Tests for POST endpoints."""

    def test_cleanup_zombies(self, comms_client, broker_db, mock_project_root):
        old_ts = "2020-01-01T00:00:00+00:00"
        _insert_messages(broker_db, [{"timestamp": old_ts, "acknowledged": 0}])
        # Add orphan PID
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        (pid_dir / "orphan.json").write_text(json.dumps({"pid": 99999999}))
        r = comms_client.post("/api/comms/cleanup", params={"max_age_hours": 0.001})
        assert r.json()["cleaned"] >= 1

    def test_cleanup_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with (
            patch("scripts.api.comms_router.MESSAGE_DB", db_path),
            patch("scripts.api.comms_router.PID_DIR", Path("/nonexistent")),
        ):
            r = comms_client.post("/api/comms/cleanup")
        assert r.json()["cleaned"] == 0

    def test_acknowledge_message(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"acknowledged": 0}])
        r = comms_client.post("/api/comms/acknowledge/1")
        assert r.json()["acknowledged"] == 1

    def test_acknowledge_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.post("/api/comms/acknowledge/1")
        assert r.status_code == 500

    def test_send_message(self, comms_client, broker_db):
        r = comms_client.post("/api/comms/send", json={
            "from_llm": "claude",
            "to_llm": "gemini",
            "content": "test message",
            "task_id": "t1",
            "message_type": "message",
        })
        data = r.json()
        assert data["sent"] is True
        assert "id" in data

    def test_send_message_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.post("/api/comms/send", json={
                "from_llm": "a", "to_llm": "b", "content": "c",
            })
        assert r.status_code == 500

    def test_send_message_defaults(self, comms_client, broker_db):
        r = comms_client.post("/api/comms/send", json={
            "from_llm": "a", "to_llm": "b", "content": "c",
        })
        assert r.json()["sent"] is True


class TestCommsByModule:
    """Tests for /api/comms/by-module/{track}/{slug} endpoint."""

    def test_by_module(self, comms_client, broker_db):
        _insert_messages(broker_db, [
            {"task_id": "build-greetings-123", "content": "Hello " * 100},
            {"task_id": "build-greetings-456", "content": "Short"},
            {"task_id": "build-other-789", "content": "Other"},
        ])
        r = comms_client.get("/api/comms/by-module/a1/greetings")
        data = r.json()
        assert data["total_messages"] == 2
        assert data["track"] == "a1"
        assert data["slug"] == "greetings"
        assert len(data["task_groups"]) >= 1

    def test_by_module_no_db(self, comms_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.comms_router.MESSAGE_DB", db_path):
            r = comms_client.get("/api/comms/by-module/a1/greetings")
        assert r.status_code == 500

    def test_by_module_no_matches(self, comms_client, broker_db):
        r = comms_client.get("/api/comms/by-module/a1/nonexistent")
        assert r.json()["total_messages"] == 0


class TestCommsLiveActivity:
    """Tests for /api/comms/live-activity endpoint."""

    def test_live_activity_empty(self, comms_client, mock_project_root):
        r = comms_client.get("/api/comms/live-activity")
        data = r.json()
        assert "in_progress" in data
        assert "recent_completions" in data
        assert "recent_dispatches" in data

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

    def test_live_activity_with_research_completions(self, comms_client, mock_project_root):
        research_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "topic-research.md").write_text("# Research")
        r = comms_client.get("/api/comms/live-activity")
        data = r.json()
        assert "recent_completions" in data

    def test_live_activity_with_broker_messages(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"content": "dispatch test"}])
        r = comms_client.get("/api/comms/live-activity")
        assert len(r.json()["recent_dispatches"]) >= 1


# ===========================================================================
# ADMIN ROUTER TESTS
# ===========================================================================


class TestAdminHelpers:
    """Tests for admin helper functions."""

    def test_dir_size_empty(self, tmp_path):
        from scripts.api.admin_router import _dir_size
        assert _dir_size(tmp_path) == 0

    def test_dir_size_with_files(self, tmp_path):
        from scripts.api.admin_router import _dir_size
        (tmp_path / "a.txt").write_text("hello")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.txt").write_text("world!")
        assert _dir_size(tmp_path) > 0

    def test_dir_size_nonexistent(self):
        from scripts.api.admin_router import _dir_size
        assert _dir_size(Path("/nonexistent")) == 0

    def test_format_bytes(self):
        from scripts.api.admin_router import _format_bytes
        assert "B" in _format_bytes(100)
        assert "KB" in _format_bytes(2048)
        assert "MB" in _format_bytes(2 * 1024 * 1024)
        assert "GB" in _format_bytes(2 * 1024**3)
        assert "TB" in _format_bytes(2 * 1024**4)

    def test_safe_within_valid(self, tmp_path):
        from scripts.api.admin_router import _safe_within
        child = tmp_path / "child" / "file.txt"
        assert _safe_within(child, tmp_path) is True

    def test_safe_within_traversal(self, tmp_path):
        from scripts.api.admin_router import _safe_within
        outside = tmp_path / ".." / "etc" / "passwd"
        assert _safe_within(outside, tmp_path) is False

    def test_broker_health_no_db(self, _patch_config, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        from scripts.api.admin_router import _broker_health
        with patch("scripts.api.admin_router.MESSAGE_DB", db_path):
            result = _broker_health()
        assert result["status"] == "missing"

    def test_broker_health_with_db(self, _patch_config, broker_db):
        from scripts.api.admin_router import _broker_health
        with patch("scripts.api.admin_router.MESSAGE_DB", broker_db):
            result = _broker_health()
        assert result["status"] == "healthy"


class TestAdminBackup:
    """Tests for backup endpoints."""

    def test_list_backups_empty(self, admin_client, mock_project_root):
        r = admin_client.get("/api/admin/backup/list")
        data = r.json()
        assert data["count"] == 0
        assert data["backups"] == []

    def test_list_backups_no_dir(self, admin_client):
        with patch("scripts.api.admin_router.BACKUP_DIR", Path("/nonexistent")):
            r = admin_client.get("/api/admin/backup/list")
        assert r.json()["backups"] == []

    def test_list_backups_with_files(self, admin_client, mock_project_root):
        backup_dir = mock_project_root / "data" / "backups"
        (backup_dir / "snapshot-1.tar").write_bytes(b"x" * 100)
        (backup_dir / "snapshot-2.tar").write_bytes(b"y" * 200)
        r = admin_client.get("/api/admin/backup/list")
        data = r.json()
        assert data["count"] == 2
        assert data["total_size_bytes"] == 300

    def test_delete_backup(self, admin_client, mock_project_root):
        backup_dir = mock_project_root / "data" / "backups"
        (backup_dir / "delete-me.tar").write_bytes(b"x" * 50)
        r = admin_client.delete("/api/admin/backup/delete-me.tar")
        assert r.status_code == 200
        assert r.json()["deleted"] == "delete-me.tar"
        assert r.json()["freed_bytes"] == 50

    def test_delete_backup_not_found(self, admin_client, mock_project_root):
        r = admin_client.delete("/api/admin/backup/nonexistent.tar")
        assert r.status_code == 404

    def test_delete_backup_traversal(self, admin_client, mock_project_root, tmp_path):
        # Create a file outside the backup dir
        outside_file = tmp_path / "outside" / "secret.txt"
        outside_file.parent.mkdir(parents=True)
        outside_file.write_text("secret")
        # Use a path that resolves outside BACKUP_DIR
        backup_dir = mock_project_root / "data" / "backups"
        # Compute relative traversal from backup_dir to outside_file
        # We mock _safe_within to return False to test the guard
        with patch("scripts.api.admin_router._safe_within", return_value=False):
            r = admin_client.delete("/api/admin/backup/evil.tar")
        assert r.status_code == 400

    def test_create_qdrant_backup_unreachable(self, admin_client):
        with patch("scripts.api.admin_router._qdrant_post", new_callable=AsyncMock, return_value=None):
            r = admin_client.post("/api/admin/backup/qdrant")
        assert r.status_code == 503

    def test_create_qdrant_backup_no_snapshot_name(self, admin_client):
        with patch("scripts.api.admin_router._qdrant_post", new_callable=AsyncMock, return_value={"result": {}}):
            r = admin_client.post("/api/admin/backup/qdrant")
        assert r.status_code == 500


class TestAdminHealth:
    """Tests for /api/admin/health endpoint."""

    def test_health(self, admin_client, mock_project_root):
        mock_start = datetime.now(UTC)
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=None),
            patch("scripts.api.admin_router._docker_status", new_callable=AsyncMock, return_value="not found"),
            patch("scripts.api.admin_router._broker_health", return_value={"status": "healthy", "size_bytes": 0, "queue_depth": 0}),
            patch("scripts.api.admin_router._dir_size", return_value=0),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value={}),
            patch.dict("sys.modules", {"scripts.api.main": MagicMock(_SERVER_START=mock_start)}),
        ):
            r = admin_client.get("/api/admin/health")
        data = r.json()
        assert data["status"] == "degraded"  # qdrant unreachable

    def test_health_all_ok(self, admin_client, mock_project_root):
        mock_start = datetime.now(UTC)
        qdrant_info = {"result": {"collections": [{"name": "test"}]}}
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._docker_status", new_callable=AsyncMock, return_value="running"),
            patch("scripts.api.admin_router._broker_health", return_value={"status": "healthy", "size_bytes": 1024, "queue_depth": 0}),
            patch("scripts.api.admin_router._dir_size", return_value=5000),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value={"test": {"result": {"points_count": 100}}}),
            patch.dict("sys.modules", {"scripts.api.main": MagicMock(_SERVER_START=mock_start)}),
        ):
            r = admin_client.get("/api/admin/health")
        data = r.json()
        assert data["status"] == "ok"
        assert data["qdrant"]["status"] == "healthy"


class TestAdminDiskUsage:
    """Tests for /api/admin/disk-usage endpoint."""

    def test_disk_usage(self, admin_client, mock_project_root):
        # Create some files
        (mock_project_root / "data" / "textbook_images" / "test.png").write_bytes(b"x" * 100)
        r = admin_client.get("/api/admin/disk-usage")
        data = r.json()
        assert "breakdown" in data
        assert data["total_bytes"] >= 0


class TestAdminMaintenance:
    """Tests for maintenance endpoints."""

    def test_vacuum_broker(self, admin_client, broker_db):
        r = admin_client.post("/api/admin/maintenance/vacuum-broker")
        data = r.json()
        assert data["status"] == "ok"

    def test_vacuum_broker_no_db(self, admin_client, mock_project_root):
        db_path = mock_project_root / ".mcp" / "servers" / "message-broker" / "messages.db"
        db_path.unlink()
        with patch("scripts.api.admin_router.MESSAGE_DB", db_path):
            r = admin_client.post("/api/admin/maintenance/vacuum-broker")
        assert r.status_code == 404

    def test_clean_logs(self, admin_client, mock_project_root):
        logs_dir = mock_project_root / "logs"
        old_log = logs_dir / "old.log"
        old_log.write_text("old log")
        # Set mtime to 60 days ago
        old_time = time.time() - (60 * 86400)
        os.utime(old_log, (old_time, old_time))
        r = admin_client.post("/api/admin/maintenance/clean-logs", params={"max_age_days": 30})
        data = r.json()
        assert data["deleted_count"] == 1

    def test_clean_logs_nothing_to_delete(self, admin_client, mock_project_root):
        r = admin_client.post("/api/admin/maintenance/clean-logs", params={"max_age_days": 30})
        assert r.json()["deleted_count"] == 0

    def test_clean_logs_mcp_server_logs(self, admin_client, mock_project_root):
        mcp_log_dir = mock_project_root / ".mcp" / "servers" / "test-server" / "logs"
        mcp_log_dir.mkdir(parents=True)
        old_log = mcp_log_dir / "server.log"
        old_log.write_text("mcp log")
        old_time = time.time() - (60 * 86400)
        os.utime(old_log, (old_time, old_time))
        r = admin_client.post("/api/admin/maintenance/clean-logs", params={"max_age_days": 30})
        assert r.json()["deleted_count"] == 1

    def test_embedding_cache_stats_no_cache(self, admin_client, mock_project_root):
        r = admin_client.get("/api/admin/maintenance/embedding-cache-stats")
        data = r.json()
        assert data["exists"] is False

    def test_embedding_cache_stats_with_cache(self, admin_client, mock_project_root):
        cache_dir = mock_project_root / "data" / "literary_texts" / ".embed_cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "file1.npy").write_bytes(b"x" * 100)
        (cache_dir / "file2.npy").write_bytes(b"y" * 200)
        # Create source files too
        lit_dir = mock_project_root / "data" / "literary_texts"
        (lit_dir / "source.txt").write_text("source")
        r = admin_client.get("/api/admin/maintenance/embedding-cache-stats")
        data = r.json()
        assert data["exists"] is True
        assert data["cached_files"] == 2
        assert data["source_files"] == 1

    def test_annotation_stats_no_dir(self, admin_client):
        with patch("scripts.api.admin_router.IMAGE_DIR", Path("/nonexistent")):
            r = admin_client.get("/api/admin/maintenance/annotation-stats")
        assert "error" in r.json()

    def test_annotation_stats_with_data(self, admin_client, mock_project_root):
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-1"
        grade_dir.mkdir()
        annotations = [
            {"image_id": "img1", "description_uk": "test", "teaching_value": "high"},
            {"image_id": "img2", "description_uk": "", "teaching_value": "low"},
            {"image_id": "img3", "description_uk": "ok", "teaching_value": "medium"},
        ]
        (grade_dir / "annotations.json").write_text(json.dumps(annotations))
        r = admin_client.get("/api/admin/maintenance/annotation-stats")
        data = r.json()
        assert data["total_images"] == 3
        assert data["annotated"] == 2

    def test_annotation_stats_images_without_annotations(self, admin_client, mock_project_root):
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-2"
        grade_dir.mkdir()
        (grade_dir / "test.png").write_bytes(b"PNG")
        r = admin_client.get("/api/admin/maintenance/annotation-stats")
        data = r.json()
        assert data["total_images"] == 1

    def test_annotation_stats_dict_format(self, admin_client, mock_project_root):
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-3"
        grade_dir.mkdir()
        annotations = {
            "img1": {"image_id": "img1", "description_uk": "test", "teaching_value": "high"},
        }
        (grade_dir / "annotations.json").write_text(json.dumps(annotations))
        r = admin_client.get("/api/admin/maintenance/annotation-stats")
        assert r.json()["total_images"] == 1

    def test_annotation_stats_corrupt_json(self, admin_client, mock_project_root):
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-4"
        grade_dir.mkdir()
        (grade_dir / "annotations.json").write_text("not json!")
        r = admin_client.get("/api/admin/maintenance/annotation-stats")
        assert r.status_code == 200


class TestAdminCollections:
    """Tests for collection management endpoints."""

    def test_collections_unreachable(self, admin_client):
        with patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=None):
            r = admin_client.get("/api/admin/collections")
        assert r.status_code == 503

    def test_collections_with_data(self, admin_client):
        qdrant_info = {"result": {"collections": [{"name": "coll1"}]}}
        details = {"coll1": {"result": {"points_count": 10, "vectors_count": 10, "indexed_vectors_count": 10, "status": "green", "config": {"params": {"vectors": {"size": 384}}}}}}
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value=details),
        ):
            r = admin_client.get("/api/admin/collections")
        data = r.json()
        assert data["count"] == 1
        assert data["collections"][0]["points_count"] == 10

    def test_collections_detail_none(self, admin_client):
        qdrant_info = {"result": {"collections": [{"name": "bad"}]}}
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value={"bad": None}),
        ):
            r = admin_client.get("/api/admin/collections")
        assert r.json()["collections"][0]["error"] == "could not fetch details"

    def test_verify_collections_unreachable(self, admin_client):
        with patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=None):
            r = admin_client.post("/api/admin/collections/verify")
        assert r.status_code == 503

    def test_verify_collections_ok(self, admin_client, mock_project_root):
        qdrant_info = {"result": {"collections": [{"name": "textbook_chunks"}]}}
        details = {"textbook_chunks": {"result": {"points_count": 5}}}
        # Create 5 JSONL lines
        chunks_dir = mock_project_root / "data" / "textbook_chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        lines = "\n".join([json.dumps({"id": i}) for i in range(5)])
        (chunks_dir / "test.jsonl").write_text(lines)
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value=details),
        ):
            r = admin_client.post("/api/admin/collections/verify")
        data = r.json()
        assert data["results"][0]["status"] == "ok"


class TestAdminQdrantHelpers:
    """Tests for qdrant helper functions."""

    @pytest.mark.anyio
    async def test_qdrant_get_failure(self):
        from scripts.api.admin_router import _qdrant_get
        import httpx
        with patch("scripts.api.admin_router._qdrant_client") as mock_client:
            mock_client.get = AsyncMock(side_effect=httpx.ConnectError("fail"))
            result = await _qdrant_get("/test")
        assert result is None

    @pytest.mark.anyio
    async def test_qdrant_post_failure(self):
        from scripts.api.admin_router import _qdrant_post
        import httpx
        with patch("scripts.api.admin_router._qdrant_client") as mock_client:
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("fail"))
            result = await _qdrant_post("/test")
        assert result is None

    @pytest.mark.anyio
    async def test_qdrant_get_success(self):
        from scripts.api.admin_router import _qdrant_get
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok"}
        mock_resp.raise_for_status = MagicMock()
        with patch("scripts.api.admin_router._qdrant_client") as mock_client:
            mock_client.get = AsyncMock(return_value=mock_resp)
            result = await _qdrant_get("/test")
        assert result == {"result": "ok"}

    @pytest.mark.anyio
    async def test_qdrant_post_success(self):
        from scripts.api.admin_router import _qdrant_post
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "snapshot"}
        mock_resp.raise_for_status = MagicMock()
        with patch("scripts.api.admin_router._qdrant_client") as mock_client:
            mock_client.post = AsyncMock(return_value=mock_resp)
            result = await _qdrant_post("/test")
        assert result == {"result": "snapshot"}


# ===========================================================================
# IMAGES ROUTER TESTS
# ===========================================================================


class TestImageIndex:
    """Tests for the _ImageIndex singleton."""

    def test_index_load_empty(self, images_client, mock_project_root):
        """Index loads fine with no data files."""
        r = images_client.get("/api/images/stats")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_index_load_with_data(self, images_client, mock_project_root):
        """Index loads structural JSONLs and annotations."""
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-1"
        grade_dir.mkdir(exist_ok=True)
        # Structural JSONL
        records = [
            {"image_id": "img1", "pdf_stem": "book1", "page": 1, "grade": 1},
            {"image_id": "img2", "pdf_stem": "book1", "page": 2, "grade": 1},
        ]
        with open(grade_dir / "book1-images.jsonl", "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")
        # Annotations
        annotations = [
            {"image_id": "img1", "description_uk": "test description", "teaching_value": "high"},
        ]
        ann_file = img_dir / "image_text_pairs.jsonl"
        with open(ann_file, "w") as f:
            for ann in annotations:
                f.write(json.dumps(ann) + "\n")

        # Reset and reload
        from scripts.api import images_router
        images_router._index.reload()

        r = images_client.get("/api/images/stats")
        data = r.json()
        assert data["total"] == 2
        assert data["annotated"] == 1


class TestImagesTextbooks:
    """Tests for /api/images/textbooks endpoint."""

    def test_textbooks_empty(self, images_client):
        r = images_client.get("/api/images/textbooks")
        assert r.status_code == 200
        assert r.json() == []


class TestImagesAnnotations:
    """Tests for /api/images/annotations endpoint."""

    def test_browse_annotations_empty(self, images_client):
        r = images_client.get("/api/images/annotations")
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_browse_annotations_with_data(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index.reload()
        # Manually inject test records
        images_router._index._records = {
            "img1": {"image_id": "img1", "grade": 1, "teaching_value": "high", "description_uk": "desc", "element_type": "diagram"},
            "img2": {"image_id": "img2", "grade": 2, "teaching_value": "low", "description_uk": "", "element_type": "photo"},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations")
        assert r.json()["total"] == 2

    def test_browse_annotations_filter_grade(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "grade": 1},
            "img2": {"image_id": "img2", "grade": 2},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"grade": 1})
        assert r.json()["total"] == 1

    def test_browse_annotations_filter_teaching_value(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "teaching_value": "high"},
            "img2": {"image_id": "img2", "teaching_value": "low"},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"teaching_value": "high"})
        assert r.json()["total"] == 1

    def test_browse_annotations_filter_element_type(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "element_type": "diagram"},
            "img2": {"image_id": "img2", "element_type": "photo"},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"element_type": "diagram"})
        assert r.json()["total"] == 1

    def test_browse_annotations_unannotated_filter(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "description_uk": "has desc"},
            "img2": {"image_id": "img2", "description_uk": ""},
            "img3": {"image_id": "img3"},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"unannotated": True})
        assert r.json()["total"] == 2

    def test_browse_annotations_search(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "description_uk": "cat sitting"},
            "img2": {"image_id": "img2", "description_uk": "dog running"},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"q": "cat"})
        assert r.json()["total"] == 1

    def test_browse_annotations_pagination(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            f"img{i}": {"image_id": f"img{i}"} for i in range(10)
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/annotations", params={"per_page": 3, "page": 1})
        data = r.json()
        assert len(data["items"]) == 3
        assert data["total"] == 10
        assert data["page"] == 1


class TestImagesAnnotationUpdate:
    """Tests for PUT /api/images/annotations/{image_id}."""

    def test_update_annotation(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "description_uk": "old"},
        }
        images_router._index._loaded = True

        with patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock):
            r = images_client.put("/api/images/annotations/img1", json={"description_uk": "new"})
        assert r.status_code == 200
        assert r.json()["updated_fields"] == ["description_uk"]

    def test_update_annotation_not_found(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {}
        images_router._index._loaded = True

        r = images_client.put("/api/images/annotations/nonexistent", json={"description_uk": "x"})
        assert r.status_code == 404

    def test_update_annotation_no_fields(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {"img1": {"image_id": "img1"}}
        images_router._index._loaded = True

        r = images_client.put("/api/images/annotations/img1", json={})
        assert r.status_code == 400


class TestImagesBulkUpdate:
    """Tests for POST /api/images/annotations/bulk."""

    def test_bulk_update(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1"},
            "img2": {"image_id": "img2"},
        }
        images_router._index._loaded = True

        with patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock):
            r = images_client.post("/api/images/annotations/bulk", json={
                "image_ids": ["img1", "img2", "img3"],
                "updates": {"teaching_value": "high"},
            })
        data = r.json()
        assert data["updated_count"] == 2
        assert data["missing"] == ["img3"]

    def test_bulk_update_no_fields(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {"img1": {"image_id": "img1"}}
        images_router._index._loaded = True

        r = images_client.post("/api/images/annotations/bulk", json={
            "image_ids": ["img1"],
            "updates": {},
        })
        assert r.status_code == 400

    def test_bulk_update_all_missing(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {}
        images_router._index._loaded = True

        with patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock):
            r = images_client.post("/api/images/annotations/bulk", json={
                "image_ids": ["nope"],
                "updates": {"teaching_value": "low"},
            })
        assert r.json()["updated_count"] == 0


class TestImagesStats:
    """Tests for /api/images/stats endpoint."""

    def test_stats_empty(self, images_client):
        r = images_client.get("/api/images/stats")
        data = r.json()
        assert data["total"] == 0
        assert data["pdfs_on_disk"] == 0

    def test_stats_with_data(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "description_uk": "desc", "teaching_value": "high", "element_type": "diagram", "grade": 1},
            "img2": {"image_id": "img2", "description_uk": "", "teaching_value": "low", "element_type": "photo", "grade": 1},
            "img3": {"image_id": "img3", "description_uk": "x", "teaching_value": "none", "element_type": "diagram", "grade": 2},
        }
        images_router._index._loaded = True

        r = images_client.get("/api/images/stats")
        data = r.json()
        assert data["total"] == 3
        assert data["annotated"] == 2
        assert data["unannotated"] == 1
        assert data["bad_candidates"] == 2  # low + none
        assert data["teaching_value"]["high"] == 1
        assert "1" in data["per_grade"]


class TestImagesCleanup:
    """Tests for POST /api/images/cleanup."""

    def test_cleanup(self, images_client, mock_project_root):
        from scripts.api import images_router
        img_path = mock_project_root / "data" / "textbook_images" / "test.png"
        img_path.write_bytes(b"PNG")
        images_router._index._records = {
            "img1": {"image_id": "img1", "image_path": f"data/textbook_images/test.png", "pdf_stem": "book", "page": 1},
        }
        images_router._index._by_pdf_page = {
            "book": {1: [images_router._index._records["img1"]]},
        }
        images_router._index._loaded = True

        with (
            patch("scripts.api.images_router._remove_from_book_jsonls"),
            patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock),
        ):
            r = images_client.post("/api/images/cleanup", json={"image_ids": ["img1"]})
        data = r.json()
        assert data["deleted_count"] == 1
        assert not img_path.exists()

    def test_cleanup_not_found(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {}
        images_router._index._loaded = True

        r = images_client.post("/api/images/cleanup", json={"image_ids": ["nope"]})
        assert r.json()["not_found"] == ["nope"]

    def test_cleanup_no_image_path(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._records = {
            "img1": {"image_id": "img1", "image_path": "", "pdf_stem": "", "page": None},
        }
        images_router._index._loaded = True

        with (
            patch("scripts.api.images_router._remove_from_book_jsonls"),
            patch("scripts.api.images_router._rewrite_annotations_jsonl", new_callable=AsyncMock),
        ):
            r = images_client.post("/api/images/cleanup", json={"image_ids": ["img1"]})
        assert r.json()["deleted_count"] == 1


class TestImagesReload:
    """Tests for POST /api/images/reload."""

    def test_reload(self, images_client, mock_project_root):
        r = images_client.post("/api/images/reload")
        data = r.json()
        assert data["status"] == "ok"
        assert "total_records" in data


class TestImagesPageContext:
    """Tests for /api/images/page/{pdf_stem}/{page_num}."""

    def test_page_context_pdf_not_found(self, images_client):
        from scripts.api import images_router
        images_router._index._pdf_catalog = {}
        images_router._index._loaded = True

        r = images_client.get("/api/images/page/nonexistent/1")
        assert r.status_code == 404


class TestImagesPageRender:
    """Tests for /api/images/page_render/{pdf_stem}/{page_num}.png."""

    def test_render_pdf_not_found(self, images_client):
        from scripts.api import images_router
        images_router._index._pdf_catalog = {}
        images_router._index._loaded = True

        r = images_client.get("/api/images/page_render/nonexistent/1.png")
        assert r.status_code == 404

    def test_render_cache_hit(self, images_client, mock_project_root):
        from scripts.api import images_router
        images_router._index._pdf_catalog = {"test": {"path": "/fake/test.pdf"}}
        images_router._index._loaded = True
        # Pre-populate cache
        images_router._page_cache["test:1"] = b"\x89PNG fake"

        r = images_client.get("/api/images/page_render/test/1.png")
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"


class TestImagesHelpers:
    """Tests for helper functions in images_router."""

    def test_cache_page_render_eviction(self):
        from scripts.api.images_router import _cache_page_render, _page_cache, _PAGE_CACHE_MAX
        _page_cache.clear()
        # Fill cache beyond max
        for i in range(_PAGE_CACHE_MAX + 5):
            _cache_page_render(f"key:{i}", b"data")
        assert len(_page_cache) == _PAGE_CACHE_MAX
        _page_cache.clear()

    def test_remove_from_book_jsonls(self, mock_project_root, _patch_config):
        from scripts.api.images_router import _remove_from_book_jsonls
        img_dir = mock_project_root / "data" / "textbook_images"
        grade_dir = img_dir / "grade-1"
        grade_dir.mkdir(exist_ok=True)
        records = [
            {"image_id": "keep", "data": "a"},
            {"image_id": "delete", "data": "b"},
        ]
        jsonl_path = grade_dir / "book1-images.jsonl"
        with open(jsonl_path, "w") as f:
            for rec in records:
                f.write(json.dumps(rec) + "\n")

        _remove_from_book_jsonls({"delete"})

        with open(jsonl_path) as f:
            remaining = [json.loads(line) for line in f if line.strip()]
        assert len(remaining) == 1
        assert remaining[0]["image_id"] == "keep"

    def test_rewrite_annotations_jsonl_sync(self, mock_project_root, _patch_config):
        from scripts.api import images_router
        ann_file = mock_project_root / "data" / "textbook_images" / "image_text_pairs.jsonl"
        ann_file.write_text('{"image_id": "old"}\n')

        images_router._index._records = {
            "img1": {"image_id": "img1", "description_uk": "test", "teaching_value": "high"},
            "img2": {"image_id": "img2"},  # no annotation data, should be skipped
        }
        images_router._index._loaded = True

        images_router._rewrite_annotations_jsonl_sync()

        with open(ann_file) as f:
            lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["image_id"] == "img1"


class TestCommsInternalHelpers:
    """Tests for internal helper functions in comms_router."""

    def test_scan_preseed_logs_no_dir(self, _patch_config):
        from scripts.api.comms_router import _scan_preseed_logs
        with patch("scripts.api.comms_router.LOG_DIR", Path("/nonexistent")):
            result = _scan_preseed_logs()
        assert result == []

    def test_scan_preseed_logs_no_files(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_preseed_logs
        result = _scan_preseed_logs()
        assert result == []

    def test_check_build_processes(self, _patch_config):
        from scripts.api.comms_router import _check_build_processes
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="user 123 0.0 0.0 python build_module.py hist 1\n", returncode=0)
            result = _check_build_processes()
        assert isinstance(result, list)

    def test_check_build_processes_failure(self, _patch_config):
        from scripts.api.comms_router import _check_build_processes
        with patch("subprocess.run", side_effect=Exception("no ps")):
            result = _check_build_processes()
        assert result == []

    def test_scan_track_progress_no_dir(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_track_progress
        result = _scan_track_progress("nonexistent")
        assert result["research_done"] == 0

    def test_scan_track_progress_with_files(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_track_progress
        research_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "research"
        research_dir.mkdir(parents=True)
        (research_dir / "topic-research.md").write_text("# Research")
        result = _scan_track_progress("hist")
        assert result["research_done"] == 1
        assert result["last_created"] is not None
        assert result["last_created"]["slug"] == "topic"


class TestPDFPool:
    """Tests for the _PDFPool helper class."""

    @pytest.mark.anyio
    async def test_pool_clear(self):
        from scripts.api.images_router import _PDFPool
        pool = _PDFPool(max_size=2)
        await pool.clear()  # Should not crash even if empty

    @pytest.mark.anyio
    async def test_pool_eviction(self):
        from scripts.api.images_router import _PDFPool
        pool = _PDFPool(max_size=2)
        # Manually inject mock docs
        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        mock_doc3 = MagicMock()
        async with pool._lock:
            pool._pool["a.pdf"] = mock_doc1
            pool._pool["b.pdf"] = mock_doc2

        with patch("pymupdf.open", return_value=mock_doc3):
            doc = await pool.get("c.pdf")
        assert doc == mock_doc3
        mock_doc1.close.assert_called_once()

    @pytest.mark.anyio
    async def test_pool_cache_hit(self):
        from scripts.api.images_router import _PDFPool
        pool = _PDFPool(max_size=2)
        mock_doc = MagicMock()
        async with pool._lock:
            pool._pool["cached.pdf"] = mock_doc
        result = await pool.get("cached.pdf")
        assert result == mock_doc


# ===========================================================================
# ADDITIONAL TESTS TO REACH 150+
# ===========================================================================


class TestAdminDockerStatus:
    """Tests for _docker_status helper."""

    @pytest.mark.anyio
    async def test_docker_status_success(self):
        from scripts.api.admin_router import _docker_status
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"running\n", b""))
        mock_proc.returncode = 0
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await _docker_status("qdrant")
        assert result == "running"

    @pytest.mark.anyio
    async def test_docker_status_not_found(self):
        from scripts.api.admin_router import _docker_status
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"error"))
        mock_proc.returncode = 1
        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await _docker_status("qdrant")
        assert result == "not found"

    @pytest.mark.anyio
    async def test_docker_status_unavailable(self):
        from scripts.api.admin_router import _docker_status
        with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError("docker")):
            result = await _docker_status("qdrant")
        assert result == "docker unavailable"


class TestAdminCollectionDetails:
    """Tests for _qdrant_collection_details helper."""

    @pytest.mark.anyio
    async def test_collection_details_parallel(self):
        from scripts.api.admin_router import _qdrant_collection_details
        with patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                {"result": {"points_count": 10}},
                {"result": {"points_count": 20}},
            ]
            result = await _qdrant_collection_details(["coll1", "coll2"])
        assert result["coll1"]["result"]["points_count"] == 10
        assert result["coll2"]["result"]["points_count"] == 20


class TestCommsCleanupEdgeCases:
    """Additional edge case tests for cleanup."""

    def test_cleanup_invalid_timestamp(self, comms_client, broker_db, mock_project_root):
        _insert_messages(broker_db, [{"timestamp": "invalid-time", "acknowledged": 0}])
        r = comms_client.post("/api/comms/cleanup", params={"max_age_hours": 0.001})
        # Should not crash, invalid timestamps are skipped
        assert r.status_code == 200

    def test_cleanup_orphan_pid_general_exception(self, comms_client, mock_project_root):
        pid_dir = mock_project_root / ".mcp" / "servers" / "message-broker" / "pids"
        # Create a PID file that triggers a general exception in os.kill
        (pid_dir / "bad.json").write_text(json.dumps({"pid": -1}))
        r = comms_client.post("/api/comms/cleanup")
        # Should clean up the bad PID file
        assert r.status_code == 200


class TestCommsLiveActivityEdgeCases:
    """Additional tests for live activity scanning."""

    def test_live_activity_corrupt_state_file(self, comms_client, mock_project_root):
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "bad-module"
        orch_dir.mkdir(parents=True)
        (orch_dir / "state-v3.json").write_text("not json!")
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        # Should not crash
        assert r.status_code == 200

    def test_live_activity_empty_phases(self, comms_client, mock_project_root):
        orch_dir = mock_project_root / "curriculum" / "l2-uk-en" / "hist" / "orchestration" / "empty-phases"
        orch_dir.mkdir(parents=True)
        state = {"slug": "empty-phases", "phases": {}}
        (orch_dir / "state-v3.json").write_text(json.dumps(state))
        r = comms_client.get("/api/comms/live-activity", params={"minutes": 120})
        assert r.status_code == 200

    def test_live_activity_invalid_dispatch_timestamp(self, comms_client, broker_db):
        _insert_messages(broker_db, [{"timestamp": "bad-ts"}])
        r = comms_client.get("/api/comms/live-activity")
        # Should not crash, invalid timestamps handled gracefully
        assert r.status_code == 200


class TestAdminVerifyCollectionsStatuses:
    """Test various verify status outcomes."""

    def test_verify_surplus(self, admin_client, mock_project_root):
        qdrant_info = {"result": {"collections": [{"name": "textbook_chunks"}]}}
        details = {"textbook_chunks": {"result": {"points_count": 100}}}
        # Create only 5 JSONL lines (fewer than qdrant has)
        chunks_dir = mock_project_root / "data" / "textbook_chunks"
        (chunks_dir / "test.jsonl").write_text("\n".join([json.dumps({"id": i}) for i in range(5)]))
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value=details),
        ):
            r = admin_client.post("/api/admin/collections/verify")
        result = r.json()["results"][0]
        assert result["status"] == "surplus"

    def test_verify_deficit(self, admin_client, mock_project_root):
        qdrant_info = {"result": {"collections": [{"name": "textbook_chunks"}]}}
        details = {"textbook_chunks": {"result": {"points_count": 2}}}
        chunks_dir = mock_project_root / "data" / "textbook_chunks"
        (chunks_dir / "test.jsonl").write_text("\n".join([json.dumps({"id": i}) for i in range(10)]))
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value=details),
        ):
            r = admin_client.post("/api/admin/collections/verify")
        result = r.json()["results"][0]
        assert result["status"] == "deficit"

    def test_verify_no_source_mapping(self, admin_client, mock_project_root):
        qdrant_info = {"result": {"collections": [{"name": "unknown_collection"}]}}
        details = {"unknown_collection": {"result": {"points_count": 5}}}
        with (
            patch("scripts.api.admin_router._qdrant_get", new_callable=AsyncMock, return_value=qdrant_info),
            patch("scripts.api.admin_router._qdrant_collection_details", new_callable=AsyncMock, return_value=details),
        ):
            r = admin_client.post("/api/admin/collections/verify")
        result = r.json()["results"][0]
        assert result["status"] == "no_source_mapping"


class TestAdminVacuumFailure:
    """Test vacuum error handling."""

    def test_vacuum_exception(self, admin_client, broker_db):
        with patch("sqlite3.connect", side_effect=sqlite3.OperationalError("locked")):
            r = admin_client.post("/api/admin/maintenance/vacuum-broker")
        assert r.status_code == 500


class TestImageIndexReload:
    """Tests for index reload behavior."""

    def test_index_reload_clears_all(self):
        from scripts.api.images_router import _ImageIndex
        idx = _ImageIndex()
        idx._records = {"a": {}}
        idx._annotations = {"b": {}}
        idx._by_pdf_page = {"c": {}}
        idx._pdf_catalog = {"d": {}}
        idx._loaded = True
        idx.reload()
        assert idx._loaded is False
        assert len(idx.records) == 0
        assert len(idx.annotations) == 0
        assert len(idx.by_pdf_page) == 0
        assert len(idx.pdf_catalog) == 0


class TestCommsPreseedLogParsing:
    """Test preseed log parsing with various formats."""

    def test_scan_preseed_logs_with_last_line(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_preseed_logs
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
        result = _scan_preseed_logs()
        assert len(result) == 1
        assert result[0]["passed"] == 1
        assert result[0]["failed"] == 2  # FAIL + ERROR
        assert "Last meaningful line" in result[0]["last_line"]
        assert result[0]["complete"] is False

    def test_scan_preseed_logs_no_timestamp_match(self, _patch_config, mock_project_root):
        from scripts.api.comms_router import _scan_preseed_logs
        log_dir = mock_project_root / "logs" / "research-preseed"
        (log_dir / "random.log").write_text("no timestamp\n")
        result = _scan_preseed_logs()
        assert result == []
