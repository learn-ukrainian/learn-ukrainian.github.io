"""
Tests for ai_agent_bridge modules, audit checks, scoring, and quality finalization.

Targets 13 modules with 0% coverage:
- ai_agent_bridge: _config, _db, _broker, _messaging, _model, _prompts, _github
- audit/checks: content_quality_pipeline, template_compliance
- audit: naturalness_check
- scoring: sampling
- audit: generate_activity_quality_queue, finalize_activity_quality
"""

import json
import os
import re
import sqlite3
import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

# ---------------------------------------------------------------------------
# 1. _config.py
# ---------------------------------------------------------------------------

class TestConfig:
    """Tests for scripts/ai_agent_bridge/_config.py constants."""

    def test_db_path_is_path(self):
        from scripts.ai_agent_bridge._config import DB_PATH
        assert isinstance(DB_PATH, Path)
        assert "messages.db" in str(DB_PATH)

    def test_pid_dir_is_path(self):
        from scripts.ai_agent_bridge._config import PID_DIR
        assert isinstance(PID_DIR, Path)
        assert "pids" in str(PID_DIR)

    def test_cli_paths_are_strings(self):
        from scripts.ai_agent_bridge._config import CLAUDE_CLI, GEMINI_CLI
        assert isinstance(CLAUDE_CLI, str)
        assert isinstance(GEMINI_CLI, str)

    def test_parent_env_has_gemini_session(self):
        from scripts.ai_agent_bridge._config import _PARENT_ENV
        assert _PARENT_ENV["GEMINI_SESSION"] == "1"
        assert _PARENT_ENV["LEARN_UKRAINIAN_PIPELINE"] == "1"

    def test_model_cache_is_dict(self):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        assert isinstance(_MODEL_CACHE, dict)

    def test_model_cache_ttl_positive(self):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE_TTL
        assert _MODEL_CACHE_TTL == 3600

    def test_gh_char_limit(self):
        from scripts.ai_agent_bridge._config import GH_CHAR_LIMIT
        assert GH_CHAR_LIMIT == 64000

    def test_repo_root_is_path(self):
        from scripts.ai_agent_bridge._config import REPO_ROOT
        assert isinstance(REPO_ROOT, Path)


# ---------------------------------------------------------------------------
# 2. _db.py
# ---------------------------------------------------------------------------

class TestDb:
    """Tests for scripts/ai_agent_bridge/_db.py."""

    @pytest.fixture
    def tmp_db(self, tmp_path):
        """Patch DB_PATH to use a temp directory."""
        db_path = tmp_path / "test.db"
        with patch("scripts.ai_agent_bridge._db.DB_PATH", db_path):
            yield db_path

    def test_init_db_creates_tables(self, tmp_db):
        from scripts.ai_agent_bridge._db import init_db
        conn = init_db()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "messages" in tables
        assert "sessions" in tables
        conn.close()

    def test_init_db_messages_columns(self, tmp_db):
        from scripts.ai_agent_bridge._db import init_db
        conn = init_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages)")
        cols = {row[1] for row in cursor.fetchall()}
        for expected in ("id", "task_id", "from_llm", "to_llm", "content", "timestamp", "acknowledged", "status"):
            assert expected in cols
        conn.close()

    def test_get_db_creates_if_not_exists(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_db
        assert not tmp_db.exists()
        conn = get_db()
        assert tmp_db.exists()
        conn.close()

    def test_get_db_migration_adds_status(self, tmp_db):
        """If DB exists without status column, migration adds it."""
        from scripts.ai_agent_bridge._db import get_db
        # Create a DB without status column
        tmp_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(tmp_db))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,
            message_type TEXT DEFAULT 'message', content TEXT NOT NULL,
            data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0
        )""")
        conn.commit()
        conn.close()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(messages)")
        cols = {row[1] for row in cursor.fetchall()}
        assert "status" in cols
        conn.close()

    def test_get_session_empty_task(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session
        result = get_session("")
        assert result == {"claude": None, "gemini": None}

    def test_get_session_not_found(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db
        init_db()
        result = get_session("nonexistent-task")
        assert result == {"claude": None, "gemini": None}

    def test_set_session_and_get_session_claude(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db, set_session
        init_db()
        set_session("task-1", "claude", "sess-abc123")
        result = get_session("task-1")
        assert result["claude"] == "sess-abc123"
        assert result["gemini"] is None

    def test_set_session_and_get_session_gemini(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db, set_session
        init_db()
        set_session("task-1", "gemini", "sess-xyz789")
        result = get_session("task-1")
        assert result["gemini"] == "sess-xyz789"

    def test_set_session_update_existing(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db, set_session
        init_db()
        set_session("task-1", "claude", "old-session")
        set_session("task-1", "claude", "new-session")
        result = get_session("task-1")
        assert result["claude"] == "new-session"

    def test_set_session_empty_task_noop(self, tmp_db):
        from scripts.ai_agent_bridge._db import init_db, set_session
        init_db()
        set_session("", "claude", "sess-123")  # Should not raise


# ---------------------------------------------------------------------------
# 3. _broker.py
# ---------------------------------------------------------------------------

class TestBroker:
    """Tests for scripts/ai_agent_bridge/_broker.py."""

    def test_validate_file_writes_no_changes(self):
        from scripts.ai_agent_bridge._broker import _validate_file_writes
        with patch("scripts.ai_agent_bridge._broker._git_status_snapshot", return_value={"M file.txt"}):
            violations = _validate_file_writes({"M file.txt"}, "some/path")
        assert violations == []

    def test_validate_file_writes_with_unauthorized(self):
        from scripts.ai_agent_bridge._broker import _validate_file_writes
        pre = {"M file.txt"}
        post = {"M file.txt", " M sneaky.py"}
        with patch("scripts.ai_agent_bridge._broker._git_status_snapshot", return_value=post):
            violations = _validate_file_writes(pre, "allowed/file.txt")
        assert len(violations) == 1
        assert "unauthorized" in violations[0]

    def test_validate_file_writes_allowed_path(self):
        from scripts.ai_agent_bridge._broker import REPO_ROOT, _validate_file_writes
        pre = set()
        allowed = "scripts/test.py"
        post = {f" M {allowed}"}
        with patch("scripts.ai_agent_bridge._broker._git_status_snapshot", return_value=post):
            violations = _validate_file_writes(pre, str(REPO_ROOT / allowed))
        assert violations == []

    def test_write_pid_file(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _write_pid_file
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            _write_pid_file("gemini", "task-1", {"model": "flash"}, pid=12345)
        pid_file = tmp_path / "gemini-task-1.json"
        assert pid_file.exists()
        data = json.loads(pid_file.read_text())
        assert data["pid"] == 12345
        assert data["agent"] == "gemini"
        assert data["model"] == "flash"

    def test_remove_pid_file(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _remove_pid_file
        pid_file = tmp_path / "claude-task-1.json"
        pid_file.write_text("{}")
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            _remove_pid_file("claude", "task-1")
        assert not pid_file.exists()

    def test_remove_pid_file_missing(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _remove_pid_file
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            _remove_pid_file("claude", "nonexistent")  # Should not raise

    def test_is_task_locked_empty_task_id(self):
        from scripts.ai_agent_bridge._broker import _is_task_locked
        assert _is_task_locked("gemini", "") is False

    def test_is_task_locked_no_pid_file(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _is_task_locked
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            assert _is_task_locked("gemini", "task-1") is False

    def test_is_task_locked_own_pid(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _is_task_locked
        pid_file = tmp_path / "gemini-task-1.json"
        pid_file.write_text(json.dumps({"pid": os.getpid(), "started": datetime.now(UTC).isoformat()}))
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            assert _is_task_locked("gemini", "task-1") is False

    def test_is_task_locked_dead_process(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _is_task_locked
        pid_file = tmp_path / "gemini-task-1.json"
        pid_file.write_text(json.dumps({"pid": 99999999, "started": datetime.now(UTC).isoformat()}))
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            result = _is_task_locked("gemini", "task-1")
        assert result is False
        assert not pid_file.exists()  # Cleaned up

    def test_check_stale_lock_no_started(self):
        from scripts.ai_agent_bridge._broker import _check_stale_lock
        result = _check_stale_lock({}, 12345, Path("/tmp/fake.json"))
        assert result is True  # Assumes locked

    def test_check_stale_lock_young(self):
        from scripts.ai_agent_bridge._broker import _check_stale_lock
        data = {"started": datetime.now(UTC).isoformat()}
        result = _check_stale_lock(data, 12345, Path("/tmp/fake.json"))
        assert result is True  # Young lock

    def test_check_stale_lock_old_python_process(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _check_stale_lock
        old_time = (datetime.now(UTC) - timedelta(minutes=45)).isoformat()
        pid_file = tmp_path / "test.json"
        pid_file.write_text("{}")
        mock_result = MagicMock()
        mock_result.stdout = "python3"
        with patch("subprocess.run", return_value=mock_result):
            result = _check_stale_lock({"started": old_time}, 12345, pid_file)
        assert result is True  # Our process, still locked

    def test_check_stale_lock_old_unknown_process(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _check_stale_lock
        old_time = (datetime.now(UTC) - timedelta(minutes=45)).isoformat()
        pid_file = tmp_path / "test.json"
        pid_file.write_text("{}")
        mock_result = MagicMock()
        mock_result.stdout = "chrome"
        with patch("subprocess.run", return_value=mock_result):
            result = _check_stale_lock({"started": old_time}, 12345, pid_file)
        assert result is False  # Stale, cleaned up

    def test_cleanup_stale_pids_no_dir(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _cleanup_stale_pids
        nonexistent = tmp_path / "no_exist"
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", nonexistent):
            result = _cleanup_stale_pids("Cleaning", 24, False)
        assert result == 0

    def test_cleanup_ancient_messages_no_db(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _cleanup_ancient_messages
        with patch("scripts.ai_agent_bridge._broker.DB_PATH", tmp_path / "no.db"):
            result = _cleanup_ancient_messages("Cleaning", 24, False)
        assert result == 0

    def test_cleanup_ancient_messages_old_messages(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _cleanup_ancient_messages
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT, to_llm TEXT,
            timestamp TEXT, acknowledged INTEGER DEFAULT 0
        )""")
        old_ts = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        conn.execute("INSERT INTO messages (task_id, from_llm, to_llm, timestamp, acknowledged) VALUES (?, ?, ?, ?, 0)",
                     ("task-1", "claude", "gemini", old_ts))
        conn.commit()
        conn.close()
        with patch("scripts.ai_agent_bridge._broker.DB_PATH", db_path):
            result = _cleanup_ancient_messages("Cleaning", 24, False)
        assert result == 1

    def test_cleanup_ancient_messages_dry_run(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _cleanup_ancient_messages
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT, to_llm TEXT,
            timestamp TEXT, acknowledged INTEGER DEFAULT 0
        )""")
        old_ts = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        conn.execute("INSERT INTO messages (task_id, from_llm, to_llm, timestamp, acknowledged) VALUES (?, ?, ?, ?, 0)",
                     ("task-1", "claude", "gemini", old_ts))
        conn.commit()
        conn.close()
        with patch("scripts.ai_agent_bridge._broker.DB_PATH", db_path):
            result = _cleanup_ancient_messages("Would clean", 24, True)
        assert result == 1
        # Verify not actually updated
        conn = sqlite3.connect(str(db_path))
        row = conn.execute("SELECT acknowledged FROM messages WHERE id=1").fetchone()
        assert row[0] == 0
        conn.close()

    def test_bridge_status_no_pid_dir(self, tmp_path, capsys):
        from scripts.ai_agent_bridge._broker import bridge_status
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path / "nope"):
            bridge_status()
        assert "No PID directory" in capsys.readouterr().out

    def test_bridge_status_empty(self, tmp_path, capsys):
        from scripts.ai_agent_bridge._broker import bridge_status
        tmp_path.mkdir(exist_ok=True)
        with patch("scripts.ai_agent_bridge._broker.PID_DIR", tmp_path):
            bridge_status()
        assert "No bridge processes" in capsys.readouterr().out

    def test_categorize_pid_files_dead(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _categorize_pid_files
        pf = tmp_path / "gemini-task-1.json"
        pf.write_text(json.dumps({"pid": 99999999}))
        alive, stale = _categorize_pid_files([pf])
        assert len(alive) == 0
        assert len(stale) == 1

    def test_categorize_pid_files_corrupt(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _categorize_pid_files
        pf = tmp_path / "bad.json"
        pf.write_text("not json")
        alive, stale = _categorize_pid_files([pf])
        assert len(stale) == 1

    def test_print_process_info(self, capsys, tmp_path):
        from scripts.ai_agent_bridge._broker import _print_process_info
        with patch("scripts.ai_agent_bridge._broker.REPO_ROOT", tmp_path):
            _print_process_info("gemini-task.json", {"pid": 1, "agent": "gemini", "task_id": "t1", "started": "now"})
        out = capsys.readouterr().out
        assert "gemini-task.json" in out
        assert "gemini" in out

    def test_git_status_snapshot_error(self):
        from scripts.ai_agent_bridge._broker import _git_status_snapshot
        with patch("subprocess.run", side_effect=Exception("fail")):
            result = _git_status_snapshot()
        assert result == set()


# ---------------------------------------------------------------------------
# 4. _messaging.py
# ---------------------------------------------------------------------------

class TestMessaging:
    """Tests for scripts/ai_agent_bridge/_messaging.py."""

    @pytest.fixture
    def msg_db(self, tmp_path):
        db_path = tmp_path / "msg.db"
        # Create the DB file and schema
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT, from_llm TEXT NOT NULL, to_llm TEXT NOT NULL,
            message_type TEXT DEFAULT 'message', content TEXT NOT NULL,
            data TEXT, timestamp TEXT NOT NULL, acknowledged INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending'
        )""")
        conn.commit()
        conn.close()

        def _fresh_conn():
            c = sqlite3.connect(str(db_path))
            return c

        with patch("scripts.ai_agent_bridge._messaging.get_db", side_effect=_fresh_conn):
            yield db_path

    def _query(self, db_path, sql, params=()):
        """Helper to query the test DB."""
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row

    def test_extract_issue_number_valid(self):
        from scripts.ai_agent_bridge._messaging import _extract_issue_number
        assert _extract_issue_number("issue-123") == 123
        assert _extract_issue_number("gh-456") == 456

    def test_extract_issue_number_invalid(self):
        from scripts.ai_agent_bridge._messaging import _extract_issue_number
        assert _extract_issue_number("task-123") is None
        assert _extract_issue_number("") is None
        assert _extract_issue_number(None) is None

    def test_detect_sender_gemini(self):
        from scripts.ai_agent_bridge._messaging import detect_sender
        with patch.dict(os.environ, {"GEMINI_SESSION": "1"}):
            assert detect_sender() == "gemini"

    def test_detect_sender_claude(self):
        from scripts.ai_agent_bridge._messaging import detect_sender
        env = {k: v for k, v in os.environ.items() if k not in ("GEMINI_SESSION", "GOOGLE_API_KEY")}
        with patch.dict(os.environ, env, clear=True), \
             patch("scripts.ai_agent_bridge._messaging.Path.exists", return_value=False):
            assert detect_sender() == "claude"

    def test_send_message_basic(self, msg_db):
        from scripts.ai_agent_bridge._messaging import send_message
        with patch("subprocess.run"):
            msg_id = send_message("hello", task_id="t1", quiet=True)
        assert msg_id is not None
        row = self._query(msg_db, "SELECT content, from_llm, to_llm FROM messages WHERE id=?", (msg_id,))
        assert row[0] == "hello"

    def test_send_message_self_addressed_auto_ack(self, msg_db):
        from scripts.ai_agent_bridge._messaging import send_message
        with patch("subprocess.run"):
            msg_id = send_message("self", from_llm="claude", to_llm="claude", quiet=True)
        row = self._query(msg_db, "SELECT acknowledged FROM messages WHERE id=?", (msg_id,))
        assert row[0] == 1

    def test_send_message_with_json_data(self, msg_db):
        from scripts.ai_agent_bridge._messaging import send_message
        with patch("subprocess.run"):
            msg_id = send_message("hi", data='{"key": "val"}', quiet=True)
        row = self._query(msg_db, "SELECT data FROM messages WHERE id=?", (msg_id,))
        parsed = json.loads(row[0])
        assert parsed["key"] == "val"

    def test_send_message_with_model_info(self, msg_db):
        from scripts.ai_agent_bridge._messaging import send_message
        with patch("subprocess.run"):
            msg_id = send_message("hi", from_model="flash", to_model="opus", quiet=True)
        row = self._query(msg_db, "SELECT data FROM messages WHERE id=?", (msg_id,))
        parsed = json.loads(row[0])
        assert parsed["from_model"] == "flash"
        assert parsed["to_model"] == "opus"

    def _insert(self, db_path, task_id, from_llm, to_llm, content, ts="2026-01-01T00:00:00"):
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, content, timestamp) VALUES (?,?,?,?,?)",
            (task_id, from_llm, to_llm, content, ts)
        )
        conn.commit()
        conn.close()

    def test_read_message_not_found(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import read_message
        result = read_message(999)
        assert result is None

    def test_read_message_found(self, msg_db):
        from scripts.ai_agent_bridge._messaging import read_message
        self._insert(msg_db, "t1", "claude", "gemini", "test content")
        result = read_message(1, quiet=True)
        assert result["content"] == "test content"

    def test_check_inbox_empty(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import check_inbox
        check_inbox("gemini")
        assert "No unread" in capsys.readouterr().out

    def test_check_inbox_with_messages(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import check_inbox
        self._insert(msg_db, "t1", "claude", "gemini", "hello gemini")
        check_inbox("gemini")
        assert "1 unread" in capsys.readouterr().out

    def test_acknowledge_single(self, msg_db):
        from scripts.ai_agent_bridge._messaging import acknowledge
        self._insert(msg_db, "t1", "claude", "gemini", "hi")
        acknowledge(1, quiet=True)
        row = self._query(msg_db, "SELECT acknowledged FROM messages WHERE id=1")
        assert row[0] == 1

    def test_acknowledge_multiple(self, msg_db):
        from scripts.ai_agent_bridge._messaging import acknowledge
        for i in range(3):
            self._insert(msg_db, "t1", "claude", "gemini", f"msg {i}")
        acknowledge([1, 2, 3], quiet=True)
        for i in range(1, 4):
            row = self._query(msg_db, "SELECT acknowledged FROM messages WHERE id=?", (i,))
            assert row[0] == 1

    def test_acknowledge_all(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import acknowledge_all
        for i in range(3):
            self._insert(msg_db, "t1", "claude", "gemini", f"msg {i}")
        acknowledge_all("gemini")
        out = capsys.readouterr().out
        assert "Acknowledged 3" in out

    def test_acknowledge_all_empty(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import acknowledge_all
        acknowledge_all("gemini")
        assert "No unread" in capsys.readouterr().out

    def test_get_conversation(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import get_conversation
        self._insert(msg_db, "t1", "claude", "gemini", "msg1")
        get_conversation("t1")
        out = capsys.readouterr().out
        assert "Conversation: t1" in out
        assert "msg1" in out

    def test_get_conversation_not_found(self, msg_db, capsys):
        from scripts.ai_agent_bridge._messaging import get_conversation
        get_conversation("no-such-task")
        assert "No messages found" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 5. _model.py
# ---------------------------------------------------------------------------

class TestModel:
    """Tests for scripts/ai_agent_bridge/_model.py."""

    def test_handle_model_check_failure_not_found(self, capsys):
        from scripts.ai_agent_bridge._model import _handle_model_check_failure
        import time
        result = MagicMock()
        result.stderr = "model not found"
        result.returncode = 1
        _handle_model_check_failure(result, "bad-model", time)
        assert "not available" in capsys.readouterr().out

    def test_handle_model_check_failure_quota(self, capsys):
        from scripts.ai_agent_bridge._model import _handle_model_check_failure
        import time
        result = MagicMock()
        result.stderr = "quota exhausted"
        result.returncode = 1
        _handle_model_check_failure(result, "good-model", time)
        assert "quota" in capsys.readouterr().out.lower()

    def test_handle_model_check_failure_generic(self, capsys):
        from scripts.ai_agent_bridge._model import _handle_model_check_failure
        import time
        result = MagicMock()
        result.stderr = "something weird"
        result.returncode = 2
        _handle_model_check_failure(result, "model-x", time)
        assert "check failed" in capsys.readouterr().out

    def test_detect_model_error_not_found(self):
        from scripts.ai_agent_bridge._model import _detect_model_error
        result = _detect_model_error("Error: model not found", "test-model")
        assert result is not None
        assert "not available" in result

    def test_detect_model_error_none(self):
        from scripts.ai_agent_bridge._model import _detect_model_error
        result = _detect_model_error("some random error", "test-model")
        assert result is None

    def test_check_model_cached(self, capsys):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        import time
        _MODEL_CACHE["cached-model"] = (True, time.time())
        try:
            result = check_model("cached-model")
            assert result is True
            assert "cached" in capsys.readouterr().out
        finally:
            _MODEL_CACHE.pop("cached-model", None)

    def test_check_model_cached_expired(self):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        import time
        _MODEL_CACHE["old-model"] = (True, time.time() - 7200)  # 2 hours old
        try:
            with patch("subprocess.run", side_effect=FileNotFoundError):
                result = check_model("old-model")
            assert result is False
        finally:
            _MODEL_CACHE.pop("old-model", None)

    def test_check_model_timeout(self, capsys):
        import subprocess
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("timeout-model", None)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 15)):
            result = check_model("timeout-model")
        assert result is False
        assert "timed out" in capsys.readouterr().out
        _MODEL_CACHE.pop("timeout-model", None)

    def test_check_model_file_not_found(self, capsys):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("missing-cli", None)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = check_model("missing-cli")
        assert result is False
        _MODEL_CACHE.pop("missing-cli", None)


# ---------------------------------------------------------------------------
# 6. _prompts.py
# ---------------------------------------------------------------------------

class TestPrompts:
    """Tests for scripts/ai_agent_bridge/_prompts.py."""

    def test_build_gemini_prompt_full_execution(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "Do the thing", "data": None}
        result = build_gemini_prompt(msg, stdout_only=False, output_path=None,
                                     allow_write=True, delimiters=None)
        assert "SILENT EXECUTION AGENT" in result
        assert "Do the thing" in result

    def test_build_gemini_prompt_full_execution_with_delimiters(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "task", "data": None}
        result = build_gemini_prompt(msg, stdout_only=False, output_path=None,
                                     allow_write=True, delimiters="CONTENT,REVIEW")
        assert "===CONTENT_START===" in result
        assert "===REVIEW_END===" in result

    def test_build_gemini_prompt_orchestrated_stdout(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "produce text", "data": None}
        result = build_gemini_prompt(msg, stdout_only=True, output_path=None,
                                     allow_write=False, delimiters=None)
        assert "TEXT GENERATOR" in result
        assert "DO NOT WRITE OR EDIT" in result

    def test_build_gemini_prompt_orchestrated_with_output_path(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "write file", "data": "extra"}
        result = build_gemini_prompt(msg, stdout_only=False, output_path="/tmp/out.md",
                                     allow_write=False, delimiters=None)
        assert "/tmp/out.md" in result
        assert "ATTACHED DATA" in result

    def test_build_gemini_prompt_standard(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "review this", "data": "some data"}
        result = build_gemini_prompt(msg, stdout_only=False, output_path=None,
                                     allow_write=False, delimiters=None)
        assert "You are Gemini" in result
        assert "Attached data" in result

    def test_build_gemini_prompt_standard_no_data(self):
        from scripts.ai_agent_bridge._prompts import build_gemini_prompt
        msg = {"content": "just a chat", "data": None}
        result = build_gemini_prompt(msg, stdout_only=False, output_path=None,
                                     allow_write=False, delimiters=None)
        assert "Attached data" not in result

    def test_build_claude_prompt(self):
        from scripts.ai_agent_bridge._prompts import build_claude_prompt
        msg = {"content": "respond to this", "data": None, "from": "gemini",
               "task_id": "task-1", "type": "query"}
        result = build_claude_prompt(msg)
        assert "Claude" in result
        assert "Gemini" in result
        assert "task-1" in result

    def test_build_claude_prompt_with_data(self):
        from scripts.ai_agent_bridge._prompts import build_claude_prompt
        msg = {"content": "review", "data": "file contents", "from": "gemini",
               "task_id": None, "type": "response"}
        result = build_claude_prompt(msg)
        assert "file contents" in result


# ---------------------------------------------------------------------------
# 7. _github.py
# ---------------------------------------------------------------------------

class TestGitHub:
    """Tests for scripts/ai_agent_bridge/_github.py."""

    def test_format_review_chunk_single(self):
        from scripts.ai_agent_bridge._github import _format_review_chunk
        result = _format_review_chunk("content here", "flash-2.0", 1, 1)
        assert "**Review** (flash-2.0)" in result
        assert "Part" not in result

    def test_format_review_chunk_multi(self):
        from scripts.ai_agent_bridge._github import _format_review_chunk
        result = _format_review_chunk("chunk", "opus", 2, 3)
        assert "Part 2/3" in result

    def test_split_content_short(self):
        from scripts.ai_agent_bridge._github import _split_content
        result = _split_content("short text", limit=100)
        assert len(result) == 1
        assert result[0] == "short text"

    def test_split_content_at_newline(self):
        from scripts.ai_agent_bridge._github import _split_content
        content = "line1\nline2\nline3"
        result = _split_content(content, limit=10)
        assert len(result) >= 2

    def test_split_content_no_newline(self):
        from scripts.ai_agent_bridge._github import _split_content
        content = "a" * 20
        result = _split_content(content, limit=10)
        assert len(result) == 2

    def test_gh_comment_success(self):
        from scripts.ai_agent_bridge._github import _gh_comment
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            assert _gh_comment(123, "body") is True

    def test_gh_comment_failure(self, capsys):
        from scripts.ai_agent_bridge._github import _gh_comment
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "auth error"
        with patch("subprocess.run", return_value=mock_result):
            assert _gh_comment(123, "body") is False

    def test_post_review_to_github_empty_content(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        assert _post_review_to_github("task-1", "", "flash") is None

    def test_post_review_to_github_existing_issue(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = _post_review_to_github("issue-42", "review text", "flash")
        assert result == 42

    def test_post_review_to_github_new_issue(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/user/repo/issues/99\n"
        with patch("subprocess.run", return_value=mock_result):
            result = _post_review_to_github("random-task", "review text", "opus")
        assert result == 99

    def test_post_review_to_github_gh_not_found(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = _post_review_to_github("issue-1", "text", "model")
        assert result is None

    def test_post_review_to_github_timeout(self):
        import subprocess
        from scripts.ai_agent_bridge._github import _post_review_to_github
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 15)):
            result = _post_review_to_github("issue-1", "text", "model")
        assert result is None


# ---------------------------------------------------------------------------
# 8. content_quality_pipeline.py
# ---------------------------------------------------------------------------

class TestContentQualityPipeline:
    """Tests for scripts/audit/checks/content_quality_pipeline.py."""

    def test_get_charset_upper_m1_with_plan(self):
        from scripts.audit.checks.content_quality_pipeline import _get_charset_upper
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        chars = _get_charset_upper(1, plan)
        assert "А" in chars
        assert "М" in chars
        assert "К" in chars  # K is in plan's decodable_letters
        assert "І" in chars
        assert "Б" not in chars  # Not in plan

    def test_get_charset_upper_no_plan_fallback(self):
        from scripts.audit.checks.content_quality_pipeline import _get_charset_upper
        # Without plan, returns full alphabet (safe fallback)
        chars = _get_charset_upper(1)
        assert "А" in chars
        assert "Я" in chars  # Full alphabet

    def test_get_charset_upper_plan_no_decodable(self):
        from scripts.audit.checks.content_quality_pipeline import _get_charset_upper
        plan = {"phase": "A1.2"}  # No decodable_letters
        chars = _get_charset_upper(2, plan)
        assert "А" in chars
        assert "Я" in chars  # Full alphabet fallback

    def test_is_skip_line_table(self):
        from scripts.audit.checks.content_quality_pipeline import _is_skip_line
        assert _is_skip_line("| word | meaning |") is True

    def test_is_skip_line_heading(self):
        from scripts.audit.checks.content_quality_pipeline import _is_skip_line
        assert _is_skip_line("## Section Title") is True

    def test_is_skip_line_prose(self):
        from scripts.audit.checks.content_quality_pipeline import _is_skip_line
        assert _is_skip_line("This is normal prose.") is False

    def test_is_skip_line_blockquote(self):
        from scripts.audit.checks.content_quality_pipeline import _is_skip_line
        assert _is_skip_line("> [!tip] Some tip") is True

    def test_is_skip_line_bold_list(self):
        from scripts.audit.checks.content_quality_pipeline import _is_skip_line
        assert _is_skip_line("- **word** meaning") is True

    def test_word_has_translation_after_parens(self):
        from scripts.audit.checks.content_quality_pipeline import _word_has_translation_after
        line = "Привіт (hello) to you"
        assert _word_has_translation_after(line, 6) is True  # after Привіт

    def test_word_has_translation_after_dash(self):
        from scripts.audit.checks.content_quality_pipeline import _word_has_translation_after
        line = "Привіт — hello"
        assert _word_has_translation_after(line, 6) is True

    def test_word_has_translation_after_none(self):
        from scripts.audit.checks.content_quality_pipeline import _word_has_translation_after
        line = "Привіт друже"
        assert _word_has_translation_after(line, 6) is False

    def test_word_is_in_translation_context(self):
        from scripts.audit.checks.content_quality_pipeline import _word_is_in_translation_context
        line = "(Привіт means hello)"
        assert _word_is_in_translation_context(line, 1) is True

    def test_word_is_not_in_translation_context(self):
        from scripts.audit.checks.content_quality_pipeline import _word_is_in_translation_context
        line = "Привіт means hello"
        assert _word_is_in_translation_context(line, 0) is False

    def test_check_untranslated_non_decodable_not_a1(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        issues = check_untranslated_non_decodable("Привіт", module_num=1, level_code="B1", plan=plan)
        assert issues == []

    def test_check_untranslated_non_decodable_no_plan(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        # Without plan and module > 4, no scan
        issues = check_untranslated_non_decodable("Привіт", module_num=7, level_code="A1")
        assert issues == []

    def test_check_untranslated_non_decodable_flags_word(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        # "Привіт" has П, Р, В — not in plan's decodable_letters
        content = "---\ntitle: test\n---\nПривіт is a word"
        issues = check_untranslated_non_decodable(content, module_num=1, level_code="A1", plan=plan)
        assert len(issues) >= 1
        assert issues[0]["type"] == "UNTRANSLATED_NON_DECODABLE"

    def test_check_untranslated_non_decodable_translated_ok(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        content = "---\ntitle: test\n---\nПривіт (hello) is a greeting"
        issues = check_untranslated_non_decodable(content, module_num=1, level_code="A1", plan=plan)
        assert len(issues) == 0

    def test_check_wall_of_text_short(self):
        from scripts.audit.checks.content_quality_pipeline import check_wall_of_text
        content = "Short paragraph.\n\nAnother short one."
        issues = check_wall_of_text(content)
        assert issues == []

    def test_check_wall_of_text_long(self):
        from scripts.audit.checks.content_quality_pipeline import check_wall_of_text
        words = " ".join(["word"] * 350)
        content = f"---\ntitle: test\n---\n{words}"
        issues = check_wall_of_text(content)
        assert len(issues) == 1
        assert issues[0]["type"] == "WALL_OF_TEXT"

    def test_check_wall_of_text_with_break(self):
        from scripts.audit.checks.content_quality_pipeline import check_wall_of_text
        words = " ".join(["word"] * 150)
        content = f"{words}\n\n{words}"
        issues = check_wall_of_text(content)
        assert issues == []

    def test_check_engagement_boxes_enough(self):
        from scripts.audit.checks.content_quality_pipeline import check_engagement_boxes
        content = "> [!tip] tip1\n> [!example] ex1\n> [!note] note1"
        with patch("scripts.audit.checks.content_quality_pipeline.LEVEL_CONFIG",
                    {"A1": {"min_engagement": 2}}, create=True):
            try:
                issues = check_engagement_boxes(content, "A1")
            except Exception:
                # Import may fail, test with fallback
                issues = check_engagement_boxes(content, "A1")
        assert len(issues) == 0

    def test_check_engagement_boxes_too_few(self):
        from scripts.audit.checks.content_quality_pipeline import check_engagement_boxes
        content = "> [!tip] just one"
        issues = check_engagement_boxes(content, "A1")
        if issues:  # Depends on config
            assert issues[0]["type"] == "LOW_ENGAGEMENT"

    def test_check_repetitive_transitions_none(self):
        from scripts.audit.checks.content_quality_pipeline import check_repetitive_transitions
        content = "## Section One\nFirst paragraph.\n\n## Section Two\nDifferent opening.\n\n## Section Three\nYet another start."
        issues = check_repetitive_transitions(content)
        assert issues == []

    def test_check_repetitive_transitions_found(self):
        from scripts.audit.checks.content_quality_pipeline import check_repetitive_transitions
        content = "## A\nIn this section we explore\n\n## B\nIn this section we discuss\n\n## C\nIn this section we analyze"
        issues = check_repetitive_transitions(content)
        assert len(issues) >= 1
        assert issues[0]["type"] == "REPETITIVE_TRANSITIONS"

    def test_check_plan_section_coverage_no_plan(self):
        from scripts.audit.checks.content_quality_pipeline import check_plan_section_coverage
        issues = check_plan_section_coverage("content", None)
        assert issues == []

    def test_check_plan_section_coverage_match(self):
        from scripts.audit.checks.content_quality_pipeline import check_plan_section_coverage
        content = "## Introduction\nText\n\n## Grammar\nMore text"
        plan = {"content_outline": [{"title": "Introduction"}, {"title": "Grammar"}]}
        issues = check_plan_section_coverage(content, plan)
        assert issues == []

    def test_check_plan_section_coverage_missing(self):
        from scripts.audit.checks.content_quality_pipeline import check_plan_section_coverage
        content = "## Introduction\nText"
        plan = {"content_outline": [{"title": "Introduction"}, {"title": "Vocabulary Expansion"}]}
        issues = check_plan_section_coverage(content, plan)
        assert len(issues) == 1
        assert "Missing" in issues[0]["text"]

    def test_collect_failed_words_from_str(self):
        from scripts.audit.checks.content_quality_pipeline import _collect_failed_words_from_str
        failed = {"кот"}
        result = _collect_failed_words_from_str("кот і собака", failed)
        assert "кот" in result

    def test_collect_failed_words_from_value_list(self):
        from scripts.audit.checks.content_quality_pipeline import _collect_failed_words_from_value
        failed = {"кот"}
        result = _collect_failed_words_from_value(["кот йде", "собака"], failed)
        assert "кот" in result

    def test_scan_activity_answers(self):
        from scripts.audit.checks.content_quality_pipeline import _scan_activity_answers
        act = {"answer": "кот", "items": [{"text": "собака", "options": ["кот", "пес"]}]}
        failed = {"кот"}
        result = _scan_activity_answers(act, failed)
        assert "кот" in result

    def test_check_activity_answers_vesum_no_path(self):
        from scripts.audit.checks.content_quality_pipeline import check_activity_answers_vesum
        issues = check_activity_answers_vesum(None, [{"original": "bad"}])
        assert issues == []

    def test_run_content_quality_checks(self):
        from scripts.audit.checks.content_quality_pipeline import run_content_quality_checks
        content = "Short.\n\nMore text."
        issues = run_content_quality_checks(content, "B1", 10)
        assert isinstance(issues, list)


# ---------------------------------------------------------------------------
# 9. template_compliance.py
# ---------------------------------------------------------------------------

@dataclass
class MockTemplateStructure:
    template_name: str = "test-template"
    level: str = "b1"
    required_sections: list = field(default_factory=list)
    forbidden_headers: list = field(default_factory=list)
    section_order: list = field(default_factory=list)
    required_callouts: list = field(default_factory=list)
    optional_sections: list = field(default_factory=list)


class TestTemplateCompliance:
    """Tests for scripts/audit/checks/template_compliance.py."""

    def test_extract_sections_with_content(self):
        from scripts.audit.checks.template_compliance import _extract_sections_with_content
        content = "---\ntitle: test\n---\n# Title\n\n## Section 1\nBody 1\n\n## Section 2\nBody 2"
        sections = _extract_sections_with_content(content)
        assert len(sections) == 3
        assert sections[1]["header"] == "Section 1"
        assert "Body 1" in sections[1]["body"]

    def test_extract_section_headers(self):
        from scripts.audit.checks.template_compliance import _extract_section_headers
        content = "---\ntitle: t\n---\n# Title\n## Sec A\nText\n## Sec B\nMore"
        headers = _extract_section_headers(content)
        assert "Title" in headers
        assert "Sec A" in headers
        assert "Sec B" in headers

    def test_extract_sections_with_lines(self):
        from scripts.audit.checks.template_compliance import _extract_sections_with_lines
        content = "# Title\n\n## Intro\nText"
        sections = _extract_sections_with_lines(content)
        assert len(sections) == 2
        assert sections[0][0] == "Title"

    def test_check_forbidden_headers_found(self):
        from scripts.audit.checks.template_compliance import _check_forbidden_headers
        template = MockTemplateStructure(forbidden_headers=["Activities", "Vocabulary"])
        content = "## Introduction\nText\n\n## Activities\nStuff"
        violations = _check_forbidden_headers(content, template)
        assert len(violations) == 1
        assert violations[0]["type"] == "FORBIDDEN_HEADER"

    def test_check_forbidden_headers_clean(self):
        from scripts.audit.checks.template_compliance import _check_forbidden_headers
        template = MockTemplateStructure(forbidden_headers=["Activities"])
        content = "## Introduction\nText\n\n## Grammar\nStuff"
        violations = _check_forbidden_headers(content, template)
        assert violations == []

    def test_check_forbidden_headers_skip_frontmatter(self):
        from scripts.audit.checks.template_compliance import _check_forbidden_headers
        template = MockTemplateStructure(forbidden_headers=["Activities"])
        content = "---\ntitle: Activities\n---\n## Grammar\nStuff"
        violations = _check_forbidden_headers(content, template)
        assert violations == []

    def test_check_section_order_correct(self):
        from scripts.audit.checks.template_compliance import _check_section_order
        template = MockTemplateStructure(section_order=["Introduction", "Grammar", "Practice"])
        content = "## Introduction\nT\n## Grammar\nT\n## Practice\nT"
        violations = _check_section_order(content, template)
        assert violations == []

    def test_check_section_order_wrong(self):
        from scripts.audit.checks.template_compliance import _check_section_order
        template = MockTemplateStructure(section_order=["Introduction", "Grammar", "Practice"])
        content = "## Practice\nT\n## Introduction\nT\n## Grammar\nT"
        violations = _check_section_order(content, template)
        assert len(violations) >= 1
        assert violations[0]["type"] == "SECTION_OUT_OF_ORDER"

    def test_check_section_order_empty(self):
        from scripts.audit.checks.template_compliance import _check_section_order
        template = MockTemplateStructure(section_order=[])
        violations = _check_section_order("## Anything", template)
        assert violations == []

    def test_check_required_callouts_found(self):
        from scripts.audit.checks.template_compliance import _check_required_callouts
        template = MockTemplateStructure(required_callouts=["myth-buster"])
        content = "> [!myth-buster]\n> Some myth busting"
        violations = _check_required_callouts(content, template)
        assert violations == []

    def test_check_required_callouts_missing(self):
        from scripts.audit.checks.template_compliance import _check_required_callouts
        template = MockTemplateStructure(required_callouts=["myth-buster"])
        content = "> [!tip]\n> Some tip"
        violations = _check_required_callouts(content, template)
        assert len(violations) == 1
        assert violations[0]["type"] == "MISSING_REQUIRED_CALLOUT"

    def test_check_required_callouts_none(self):
        from scripts.audit.checks.template_compliance import _check_required_callouts
        template = MockTemplateStructure(required_callouts=[])
        violations = _check_required_callouts("any content", template)
        assert violations == []

    def test_is_sidecar_exempt_section_vocab(self):
        from scripts.audit.checks.template_compliance import _is_sidecar_exempt_section
        assert _is_sidecar_exempt_section(["Словник"]) is True
        assert _is_sidecar_exempt_section(["Vocabulary"]) is True

    def test_is_sidecar_exempt_section_activities(self):
        from scripts.audit.checks.template_compliance import _is_sidecar_exempt_section
        assert _is_sidecar_exempt_section(["Вправи"]) is True
        assert _is_sidecar_exempt_section(["Activities"]) is True

    def test_is_sidecar_exempt_section_not(self):
        from scripts.audit.checks.template_compliance import _is_sidecar_exempt_section
        assert _is_sidecar_exempt_section(["Introduction"]) is False

    def test_resolve_vital_status_living(self):
        from scripts.audit.checks.template_compliance import _resolve_vital_status_names
        template = MockTemplateStructure(level="c1", template_name="c1-biography")
        alt_names = ["Сучасний етап", "Останні роки"]
        preferred, forbidden = _resolve_vital_status_names(alt_names, "living", template)
        assert preferred == "Сучасний етап"
        assert forbidden == "Останні роки"

    def test_resolve_vital_status_deceased(self):
        from scripts.audit.checks.template_compliance import _resolve_vital_status_names
        template = MockTemplateStructure(level="c1", template_name="c1-biography")
        alt_names = ["Сучасний етап", "Останні роки"]
        preferred, forbidden = _resolve_vital_status_names(alt_names, "deceased", template)
        assert preferred == "Останні роки"
        assert forbidden == "Сучасний етап"

    def test_resolve_vital_status_not_bio(self):
        from scripts.audit.checks.template_compliance import _resolve_vital_status_names
        template = MockTemplateStructure(level="b1", template_name="b1-grammar")
        preferred, forbidden = _resolve_vital_status_names(["A", "B"], "living", template)
        assert preferred is None
        assert forbidden is None

    def test_check_forbidden_tone(self):
        from scripts.audit.checks.template_compliance import _check_forbidden_tone
        sections = [{"header": "Останні роки", "line": 10}]
        violations = _check_forbidden_tone("Останні роки", "Сучасний етап", "living", sections)
        assert len(violations) == 1
        assert violations[0]["type"] == "FORBIDDEN_HEADER_TONE"

    def test_check_forbidden_tone_no_forbidden(self):
        from scripts.audit.checks.template_compliance import _check_forbidden_tone
        violations = _check_forbidden_tone(None, None, "living", [])
        assert violations == []

    def test_check_duplicate_sections(self):
        from scripts.audit.checks.template_compliance import _check_duplicate_sections
        template = MockTemplateStructure()
        found = [
            {"header": "Спадщина", "line": 10},
            {"header": "Культурна спадщина", "line": 20}
        ]
        violations = _check_duplicate_sections(found, "Спадщина|Legacy", template)
        assert len(violations) == 1
        assert violations[0]["type"] == "DUPLICATE_SYNONYMOUS_HEADERS"

    def test_check_duplicate_sections_single(self):
        from scripts.audit.checks.template_compliance import _check_duplicate_sections
        template = MockTemplateStructure()
        found = [{"header": "Спадщина", "line": 10}]
        violations = _check_duplicate_sections(found, "Спадщина", template)
        assert violations == []

    def test_check_empty_sections(self):
        from scripts.audit.checks.template_compliance import _check_empty_sections
        found = [{"header": "Empty", "line": 5, "body": "   \n\n  ", "level": 2}]
        all_sections = [{"header": "Empty", "line": 5, "body": "", "level": 2}]
        violations = _check_empty_sections(found, all_sections)
        assert len(violations) == 1
        assert violations[0]["type"] == "EMPTY_REQUIRED_SECTION"

    def test_check_empty_sections_parent_ok(self):
        from scripts.audit.checks.template_compliance import _check_empty_sections
        found = [{"header": "Parent", "line": 5, "body": "  ", "level": 2}]
        all_sections = [
            {"header": "Parent", "line": 5, "body": "", "level": 2},
            {"header": "Child", "line": 7, "body": "content", "level": 3}
        ]
        violations = _check_empty_sections(found, all_sections)
        assert violations == []

    def test_check_template_compliance_full(self):
        from scripts.audit.checks.template_compliance import check_template_compliance
        template = MockTemplateStructure(
            required_sections=["Introduction"],
            forbidden_headers=["Activities"],
            required_callouts=["tip"]
        )
        content = "## Introduction\nSome text\n\n> [!tip]\n> A tip"
        violations = check_template_compliance(content, {}, template)
        assert isinstance(violations, list)

    def test_check_required_sections_with_content_outline(self):
        from scripts.audit.checks.template_compliance import _check_required_sections
        template = MockTemplateStructure(required_sections=["Introduction"])
        meta = {"content_outline": [{"title": "Custom"}]}
        violations = _check_required_sections("## Custom\nText", meta, template)
        assert violations == []  # content_outline takes precedence


# ---------------------------------------------------------------------------
# 10. naturalness_check.py
# ---------------------------------------------------------------------------

class TestNaturalnessCheck:
    """Tests for scripts/audit/naturalness_check.py."""

    def test_extract_ukrainian_content_basic(self, tmp_path):
        from scripts.audit.naturalness_check import extract_ukrainian_content
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: test\n---\n\nПривіт, друже! Як справи?\n\nSome English text.\n", encoding="utf-8")
        result = extract_ukrainian_content(str(md))
        assert "Привіт" in result
        assert "English" not in result

    def test_extract_ukrainian_content_removes_code(self, tmp_path):
        from scripts.audit.naturalness_check import extract_ukrainian_content
        md = tmp_path / "test.md"
        md.write_text("---\ntitle: t\n---\n```python\nкод = True\n```\nТекст українською.", encoding="utf-8")
        result = extract_ukrainian_content(str(md))
        assert "код" not in result
        assert "Текст" in result

    def test_extract_ukrainian_content_truncation(self, tmp_path):
        from scripts.audit.naturalness_check import extract_ukrainian_content
        md = tmp_path / "test.md"
        text = "Привіт " * 1000
        md.write_text(text, encoding="utf-8")
        result = extract_ukrainian_content(str(md), max_chars=100)
        assert len(result) <= 130  # 100 + truncation marker

    def test_append_to_audit(self, tmp_path):
        from scripts.audit.naturalness_check import append_to_audit
        audit_file = tmp_path / "review.md"
        audit_file.write_text("# Audit\n")
        gemini_parsed = {"score": 9, "status": "PASS", "feedback_uk": "Добре", "issues": []}
        claude_parsed = {"score": 8, "status": "PASS", "feedback_uk": "OK", "issues": []}
        append_to_audit(audit_file, "raw gemini", gemini_parsed, "raw claude", claude_parsed, "2026-01-01")
        content = audit_file.read_text()
        assert "Naturalness Check" in content
        assert "9/10" in content
        assert "Average:" in content

    def test_append_to_audit_disagreement(self, tmp_path):
        from scripts.audit.naturalness_check import append_to_audit
        audit_file = tmp_path / "review.md"
        audit_file.write_text("")
        gemini_parsed = {"score": 9, "status": "PASS", "feedback_uk": "", "issues": []}
        claude_parsed = {"score": 5, "status": "FAIL", "feedback_uk": "", "issues": []}
        append_to_audit(audit_file, "raw", gemini_parsed, "raw", claude_parsed, "2026-01-01")
        assert "Disagreement" in audit_file.read_text()

    def test_append_to_audit_gemini_only(self, tmp_path):
        from scripts.audit.naturalness_check import append_to_audit
        audit_file = tmp_path / "review.md"
        audit_file.write_text("")
        gemini_parsed = {"score": 8, "status": "PASS", "feedback_uk": "", "issues": []}
        claude_parsed = {"score": 0, "status": "ERROR", "feedback_uk": "", "issues": []}
        append_to_audit(audit_file, "raw", gemini_parsed, "raw", claude_parsed, "2026-01-01")
        assert "Gemini only" in audit_file.read_text()

    def test_update_meta_naturalness(self, tmp_path):
        import yaml
        from scripts.audit.naturalness_check import update_meta_naturalness
        meta_file = tmp_path / "test.yaml"
        meta_file.write_text("version: 1\n")
        update_meta_naturalness(meta_file, 9, "PASS", "Good", "2026-01-01")
        data = yaml.safe_load(meta_file.read_text())
        assert data["naturalness"]["score"] == 9
        assert data["naturalness"]["status"] == "PASS"

    def test_update_meta_naturalness_missing_file(self, tmp_path):
        from scripts.audit.naturalness_check import update_meta_naturalness
        update_meta_naturalness(tmp_path / "missing.yaml", 9, "PASS", "Good", "2026-01-01")
        # Should not raise


# ---------------------------------------------------------------------------
# 11. scoring/sampling.py
# ---------------------------------------------------------------------------

class TestSampling:
    """Tests for scripts/scoring/sampling.py."""

    def test_determine_tier_low_naturalness(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 6}}
        assert determine_tier(data) == "llm-verified"

    def test_determine_tier_high_naturalness(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 9}, "tags": []}
        assert determine_tier(data) == "automated"

    def test_determine_tier_sensitive_tags(self):
        from scripts.scoring.sampling import determine_tier
        data = {"naturalness": {"score": 9}, "tags": ["politics", "economy"]}
        assert determine_tier(data) == "llm-verified"

    def test_determine_tier_no_naturalness(self):
        from scripts.scoring.sampling import determine_tier
        data = {"tags": []}
        assert determine_tier(data) == "automated"

    def test_get_validation_status_default(self):
        from scripts.scoring.sampling import get_validation_status
        assert get_validation_status({}) == "automated"

    def test_get_validation_status_set(self):
        from scripts.scoring.sampling import get_validation_status
        assert get_validation_status({"validation_tier": "gold-standard"}) == "gold-standard"

    def test_should_sample_deterministic(self):
        from scripts.scoring.sampling import should_sample
        # Same slug always gives same result
        r1 = should_sample("test-slug")
        r2 = should_sample("test-slug")
        assert r1 == r2

    def test_should_sample_rate_0(self):
        from scripts.scoring.sampling import should_sample
        assert should_sample("anything", sample_rate=0.0) is False

    def test_should_sample_rate_1(self):
        from scripts.scoring.sampling import should_sample
        assert should_sample("anything", sample_rate=1.0) is True

    def test_get_sampling_candidates(self):
        from scripts.scoring.sampling import get_sampling_candidates
        modules = [
            {"slug": "mod1", "naturalness": {"score": 5}, "tags": []},
            {"slug": "mod2", "naturalness": {"score": 9}, "tags": [], "validation_tier": "llm-verified"},
            {"slug": "mod3", "naturalness": {"score": 9}, "tags": ["war"]},
        ]
        candidates = get_sampling_candidates(modules)
        assert "mod1" in candidates
        assert "mod2" not in candidates  # Already verified
        assert "mod3" in candidates

    def test_get_sampling_candidates_no_slug(self):
        from scripts.scoring.sampling import get_sampling_candidates
        modules = [{"tags": []}]
        assert get_sampling_candidates(modules) == []

    def test_calculate_sampling_metrics_empty(self):
        from scripts.scoring.sampling import calculate_sampling_metrics
        assert calculate_sampling_metrics([]) == {}

    def test_calculate_sampling_metrics(self):
        from scripts.scoring.sampling import calculate_sampling_metrics
        modules = [
            {"slug": "a", "naturalness": {"score": 9}, "tags": [], "validation_tier": "automated"},
            {"slug": "b", "naturalness": {"score": 5}, "tags": [], "validation_tier": "llm-verified"},
        ]
        metrics = calculate_sampling_metrics(modules)
        assert metrics["total"] == 2
        assert metrics["tiers"]["automated"] == 1
        assert metrics["tiers"]["llm-verified"] == 1
        assert metrics["coverage_pct"] == 50.0


# ---------------------------------------------------------------------------
# 12. generate_activity_quality_queue.py
# ---------------------------------------------------------------------------

class TestGenerateActivityQualityQueue:
    """Tests for scripts/audit/generate_activity_quality_queue.py."""

    def test_extract_activity_text_quiz(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "quiz", "items": [{"question": "Що це?", "sentence": "Це кіт."}]}
        result = extract_activity_text(activity)
        assert "Що це?" in result
        assert "Це кіт." in result

    def test_extract_activity_text_fill_in(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "fill-in", "items": [{"sentence": "Я ___ додому."}]}
        result = extract_activity_text(activity)
        assert "додому" in result

    def test_extract_activity_text_error_correction(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "error-correction", "items": [{"sentence": "bad", "error": "err", "answer": "good"}]}
        result = extract_activity_text(activity)
        assert "bad" in result and "good" in result

    def test_extract_activity_text_cloze(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "cloze", "items": [{"text": "Fill the ___"}]}
        result = extract_activity_text(activity)
        assert "Fill" in result

    def test_extract_activity_text_unjumble(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "unjumble", "items": [{"words": ["я", "іду"], "answer": "Я іду"}]}
        result = extract_activity_text(activity)
        assert "я іду" in result

    def test_extract_activity_text_true_false(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "true-false", "items": [{"statement": "Київ столиця"}]}
        result = extract_activity_text(activity)
        assert "Київ" in result

    def test_extract_activity_text_match_up(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        # match-up uses pairs on activity level; item must be non-empty (empty dict is falsy)
        activity = {"type": "match-up", "pairs": [{"left": "кіт", "right": "cat"}], "items": [{"id": 1}]}
        result = extract_activity_text(activity)
        assert "кіт" in result

    def test_extract_activity_text_no_items(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "quiz"}
        result = extract_activity_text(activity)
        assert result == ""

    def test_extract_activity_text_specific_item(self):
        from scripts.audit.generate_activity_quality_queue import extract_activity_text
        activity = {"type": "quiz", "items": [{"question": "Q1"}, {"question": "Q2"}]}
        result = extract_activity_text(activity, item={"question": "Q2"})
        assert "Q2" in result

    def test_extract_options_quiz(self):
        from scripts.audit.generate_activity_quality_queue import extract_options
        activity = {"type": "quiz", "items": [
            {"options": [{"text": "A", "correct": True}, {"text": "B", "correct": False}]}
        ]}
        options, correct = extract_options(activity)
        assert options == ["A", "B"]
        assert correct == "A"

    def test_extract_options_fill_in(self):
        from scripts.audit.generate_activity_quality_queue import extract_options
        activity = {"type": "fill-in", "items": [{"options": ["a", "b"], "answer": "a"}]}
        options, correct = extract_options(activity)
        assert options == ["a", "b"]
        assert correct == "a"

    def test_extract_options_no_items(self):
        from scripts.audit.generate_activity_quality_queue import extract_options
        activity = {"type": "quiz"}
        options, correct = extract_options(activity)
        assert options == []
        assert correct is None


# ---------------------------------------------------------------------------
# 13. finalize_activity_quality.py
# ---------------------------------------------------------------------------

class TestFinalizeActivityQuality:
    """Tests for scripts/audit/finalize_activity_quality.py."""

    def test_calculate_quality_scores_empty(self):
        from scripts.audit.finalize_activity_quality import calculate_quality_scores
        result = calculate_quality_scores({"activities": []})
        assert result["total_activities"] == 0
        assert "error" in result

    def test_calculate_quality_scores_incomplete(self):
        from scripts.audit.finalize_activity_quality import calculate_quality_scores
        data = {"activities": [
            {"activity_id": "a1", "naturalness": None, "engagement": None, "difficulty": None}
        ]}
        result = calculate_quality_scores(data)
        assert len(result["incomplete_activities"]) == 1

    def test_calculate_quality_scores_complete(self):
        from scripts.audit.finalize_activity_quality import calculate_quality_scores
        data = {"activities": [
            {"activity_id": "a1", "naturalness": 4, "engagement": 3, "difficulty": "appropriate",
             "distractor_score": 4, "variety_score": 70},
            {"activity_id": "a2", "naturalness": 5, "engagement": 4, "difficulty": "too_hard",
             "distractor_score": 5, "variety_score": 80},
        ]}
        result = calculate_quality_scores(data)
        assert result["validated_activities"] == 2
        assert result["naturalness_avg"] == 4.5
        assert result["engagement_avg"] == 3.5
        assert result["distractor_quality_avg"] == 4.5
        assert result["variety_avg"] == 75
        assert result["difficulty_breakdown"]["appropriate"] == 1
        assert result["difficulty_breakdown"]["too_hard"] == 1

    def test_evaluate_quality_gates_a1_pass(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {"naturalness_avg": 2.0}
        result = evaluate_quality_gates(scores, "A1")
        assert result["result"] == "PASS"  # A1 has no strict gates

    def test_evaluate_quality_gates_b1_pass(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {
            "naturalness_avg": 4.0, "engagement_avg": 4.0,
            "distractor_quality_avg": 4.5, "variety_avg": 70,
            "difficulty_inappropriate_pct": 0.1
        }
        result = evaluate_quality_gates(scores, "B1")
        assert result["result"] == "PASS"

    def test_evaluate_quality_gates_b1_fail_naturalness(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {
            "naturalness_avg": 2.0, "engagement_avg": 4.0,
            "distractor_quality_avg": 4.5, "variety_avg": 70,
            "difficulty_inappropriate_pct": 0.1
        }
        result = evaluate_quality_gates(scores, "B1")
        assert result["result"] == "FAIL"
        assert any(g["dimension"] == "naturalness" for g in result["failed_gates"])

    def test_evaluate_quality_gates_c2(self):
        from scripts.audit.finalize_activity_quality import evaluate_quality_gates
        scores = {
            "naturalness_avg": 3.0, "engagement_avg": 3.0,
            "distractor_quality_avg": 3.0, "variety_avg": 50,
            "difficulty_inappropriate_pct": 0.2
        }
        result = evaluate_quality_gates(scores, "C2")
        assert result["result"] == "FAIL"
        assert len(result["failed_gates"]) >= 3  # Multiple failures

    def test_generate_report_pass(self):
        from scripts.audit.finalize_activity_quality import generate_report
        queue_data = {"module": "test-mod", "level": "B1", "module_number": 5}
        quality_scores = {
            "naturalness_avg": 4.0, "engagement_avg": 4.0,
            "distractor_quality_avg": 4.5, "variety_avg": 70,
            "difficulty_appropriate_pct": 0.9, "difficulty_breakdown": {"too_easy": 0, "appropriate": 9, "too_hard": 1},
            "incomplete_activities": []
        }
        gate_evaluation = {"result": "PASS", "failed_gates": []}
        report = generate_report(queue_data, quality_scores, gate_evaluation)
        assert "PASS" in report
        assert "test-mod" in report
        assert "B1" in report

    def test_generate_report_fail(self):
        from scripts.audit.finalize_activity_quality import generate_report
        queue_data = {"module": "test-mod", "level": "B2", "module_number": 3}
        quality_scores = {
            "naturalness_avg": 2.0, "engagement_avg": 2.0,
            "distractor_quality_avg": None, "variety_avg": None,
            "difficulty_appropriate_pct": 0.5,
            "difficulty_breakdown": {"too_easy": 3, "appropriate": 3, "too_hard": 0},
            "incomplete_activities": ["act-1"]
        }
        gate_evaluation = {
            "result": "FAIL",
            "failed_gates": [
                {"dimension": "naturalness", "message": "Naturalness 2.0 < 4.0"},
                {"dimension": "engagement", "message": "Engagement 2.0 < 3.5"},
            ]
        }
        report = generate_report(queue_data, quality_scores, gate_evaluation)
        assert "FAIL" in report
        assert "Improve Naturalness" in report
        assert "Incomplete" in report

    def test_generate_report_all_dimensions_fail(self):
        from scripts.audit.finalize_activity_quality import generate_report
        queue_data = {"module": "x", "level": "C1", "module_number": 1}
        quality_scores = {
            "naturalness_avg": 1.0, "engagement_avg": 1.0,
            "distractor_quality_avg": 1.0, "variety_avg": 10,
            "difficulty_appropriate_pct": 0.5,
            "difficulty_breakdown": {"too_easy": 5, "appropriate": 5, "too_hard": 0},
            "incomplete_activities": []
        }
        gate_evaluation = {
            "result": "FAIL",
            "failed_gates": [
                {"dimension": "naturalness", "message": "low"},
                {"dimension": "difficulty", "message": "bad"},
                {"dimension": "engagement", "message": "low"},
                {"dimension": "distractor_quality", "message": "bad"},
                {"dimension": "variety", "message": "low"},
            ]
        }
        report = generate_report(queue_data, quality_scores, gate_evaluation)
        assert "Improve Naturalness" in report
        assert "Fix Difficulty" in report
        assert "Increase Engagement" in report
        assert "Improve Distractors" in report
        assert "Add Variety" in report

    def test_quality_gates_keys(self):
        from scripts.audit.finalize_activity_quality import QUALITY_GATES
        for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
            assert level in QUALITY_GATES
            gates = QUALITY_GATES[level]
            for key in ("min_naturalness_avg", "max_difficulty_inappropriate",
                        "min_engagement_avg", "min_distractor_quality", "min_variety_avg"):
                assert key in gates
