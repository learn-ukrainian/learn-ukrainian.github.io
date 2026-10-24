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
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests.agent_runtime.agy_hook_helpers import register_agy_hooks


@pytest.fixture(autouse=True)
def _synthetic_publishing_rules(synthetic_opsec, publisher_transport, monkeypatch):
    """Public writes use synthetic policy, independently of host tooling."""
    monkeypatch.setenv("GH_REPO", "unit/public")

# ---------------------------------------------------------------------------
# 1. _config.py
# ---------------------------------------------------------------------------

class TestConfig:
    """Tests for scripts/ai_agent_bridge/_config.py constants."""

    def test_cli_paths_are_correct_types(self):
        from scripts.ai_agent_bridge._config import AGY_CLI, CLAUDE_CMD, GEMINI_CLI
        assert isinstance(CLAUDE_CMD, list)
        # #4875: prefers a native `claude` binary on PATH (single-element
        # command) and only falls back to the npx shim when none is found —
        # both are correct depending on the machine running the test.
        if CLAUDE_CMD[0] == "npx":
            assert "@anthropic-ai/claude-code" in CLAUDE_CMD[1]
        else:
            assert len(CLAUDE_CMD) == 1
            assert CLAUDE_CMD[0].endswith("claude")
        assert isinstance(AGY_CLI, str)
        assert isinstance(GEMINI_CLI, str)


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

    def test_set_session_and_get_session_claude(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db, set_session
        init_db()
        set_session("task-1", "claude", "sess-abc123")
        result = get_session("task-1")
        assert result["claude"] == "sess-abc123"
        assert result["gemini"] is None

    def test_set_session_update_existing(self, tmp_db):
        from scripts.ai_agent_bridge._db import get_session, init_db, set_session
        init_db()
        set_session("task-1", "claude", "old-session")
        set_session("task-1", "claude", "new-session")
        result = get_session("task-1")
        assert result["claude"] == "new-session"


# ---------------------------------------------------------------------------
# 3. _broker.py
# ---------------------------------------------------------------------------

class TestBroker:
    """Tests for scripts/ai_agent_bridge/_broker.py."""

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

    def test_cleanup_ancient_messages_old_messages(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _cleanup_ancient_messages
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT, to_llm TEXT,
            data TEXT, timestamp TEXT, acknowledged INTEGER DEFAULT 0
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
            data TEXT, timestamp TEXT, acknowledged INTEGER DEFAULT 0
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

    def test_broker_retention_cleanup_deletes_acknowledged_rows(self, tmp_path):
        from scripts.ai_agent_bridge._broker import broker_retention_cleanup
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.executescript("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY, task_id TEXT, from_llm TEXT, to_llm TEXT,
                data TEXT, timestamp TEXT, acknowledged INTEGER DEFAULT 0
            );
            CREATE TABLE channel_messages (
                message_id TEXT PRIMARY KEY, created_at TEXT, parent_id TEXT
            );
            CREATE TABLE deliveries (
                delivery_id TEXT PRIMARY KEY, message_id TEXT, to_agent TEXT, to_model TEXT, status TEXT
            );
        """)
        old_ts = (datetime.now(UTC) - timedelta(days=45)).isoformat()
        conn.execute(
            "INSERT INTO messages (id, task_id, from_llm, to_llm, timestamp, acknowledged) VALUES (?, ?, ?, ?, ?, 1)",
            (1, "task-1", "claude", "gemini", old_ts),
        )
        conn.execute(
            "INSERT INTO messages (id, task_id, from_llm, to_llm, timestamp, acknowledged) VALUES (?, ?, ?, ?, ?, 0)",
            (2, "task-2", "claude", "gemini", old_ts),
        )
        conn.execute(
            "INSERT INTO channel_messages (message_id, created_at, parent_id) VALUES (?, ?, NULL)",
            ("m1", old_ts),
        )
        conn.execute(
            "INSERT INTO deliveries (delivery_id, message_id, status) VALUES (?, ?, ?)",
            ("d1", "m1", "delivered"),
        )
        conn.commit()
        conn.close()
        with patch("scripts.ai_agent_bridge._broker.DB_PATH", db_path):
            result = broker_retention_cleanup("30d", False)
        assert result == 3
        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM channel_messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM deliveries").fetchone()[0] == 0
        conn.close()

    def test_broker_retention_cleanup_dry_run(self, tmp_path):
        from scripts.ai_agent_bridge._broker import broker_retention_cleanup
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""CREATE TABLE messages (
            id INTEGER PRIMARY KEY, to_llm TEXT, data TEXT, timestamp TEXT, acknowledged INTEGER DEFAULT 0
        )""")
        old_ts = (datetime.now(UTC) - timedelta(days=45)).isoformat()
        conn.execute(
            "INSERT INTO messages (id, timestamp, acknowledged) VALUES (?, ?, 1)",
            (1, old_ts),
        )
        conn.commit()
        conn.close()
        with patch("scripts.ai_agent_bridge._broker.DB_PATH", db_path):
            result = broker_retention_cleanup("30d", True)
        assert result == 1
        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
        conn.close()

    def test_categorize_pid_files_dead(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _categorize_pid_files
        pf = tmp_path / "gemini-task-1.json"
        pf.write_text(json.dumps({"pid": 99999999}))
        _alive, stale = _categorize_pid_files([pf])
        assert len(_alive) == 0
        assert len(stale) == 1

    def test_categorize_pid_files_corrupt(self, tmp_path):
        from scripts.ai_agent_bridge._broker import _categorize_pid_files
        pf = tmp_path / "bad.json"
        pf.write_text("not json")
        _alive, stale = _categorize_pid_files([pf])
        assert len(stale) == 1

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
            consumed_by_live_driver INTEGER DEFAULT 0, consumed_at TEXT,
            status TEXT DEFAULT 'pending'
        )""")
        conn.commit()
        conn.close()

        def _fresh_conn():
            from scripts.ai_agent_bridge._db import register_kimi_row_functions

            c = sqlite3.connect(str(db_path))
            register_kimi_row_functions(c)  # as get_db does
            return c

        with patch("scripts.ai_agent_bridge._messaging.get_db", side_effect=_fresh_conn):
            yield db_path

    def _query(self, db_path, sql, params=()):
        """Helper to query the test DB."""
        conn = sqlite3.connect(str(db_path))
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row

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


    def _insert(self, db_path, task_id, from_llm, to_llm, content, ts="2026-01-01T00:00:00"):
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "INSERT INTO messages (task_id, from_llm, to_llm, content, timestamp) VALUES (?,?,?,?,?)",
            (task_id, from_llm, to_llm, content, ts)
        )
        conn.commit()
        conn.close()

    def test_acknowledge_single(self, msg_db):
        from scripts.ai_agent_bridge._messaging import acknowledge
        self._insert(msg_db, "t1", "claude", "gemini", "hi")
        acknowledge(1, quiet=True)
        row = self._query(msg_db, "SELECT acknowledged FROM messages WHERE id=1")
        assert row[0] == 1

    # -- resolve_thread (#4837 item 5: unified `ab thread <task-id|msg-id>`) --


# ---------------------------------------------------------------------------
# 5. _model.py
# ---------------------------------------------------------------------------

class TestModel:
    """Tests for scripts/ai_agent_bridge/_model.py."""

    @pytest.fixture(autouse=True)
    def supported_agy_version(self, monkeypatch):
        # Probe-result mocks must not also replace the adapter's version check.
        monkeypatch.setattr("agent_runtime.adapters.agy._agy_version", lambda _binary: (1, 2, 9))

    def test_detect_model_error_not_found(self):
        from scripts.ai_agent_bridge._model import _detect_model_error
        result = _detect_model_error("Error: model not found", "test-model")
        assert result is not None
        assert "not available" in result

    def test_check_model_cached(self, capsys):
        import time

        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE["cached-model"] = (True, time.time())
        try:
            result = check_model("cached-model")
            assert result is True
            assert "cached" in capsys.readouterr().out
        finally:
            _MODEL_CACHE.pop("cached-model", None)

    def test_check_model_timeout(self, capsys, tmp_path, monkeypatch):
        home = tmp_path / "home"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home))
        register_agy_hooks(tmp_path, home=home)
        monkeypatch.setattr("scripts.ai_agent_bridge._model._REPO_ROOT", tmp_path)
        import subprocess

        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 90)):
            result = check_model("gemini-3.8-flash-high")
        assert result is False
        assert "timed out" in capsys.readouterr().out
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)

    def test_check_model_file_not_found(self, capsys, tmp_path, monkeypatch):
        home = tmp_path / "home"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home))
        register_agy_hooks(tmp_path, home=home)
        monkeypatch.setattr("scripts.ai_agent_bridge._model._REPO_ROOT", tmp_path)
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = check_model("gemini-3.8-flash-high")
        assert result is False
        assert "AGY CLI not found" in capsys.readouterr().out
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)

    def test_check_model_unknown_slug(self, capsys):
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("not-a-real-model", None)
        result = check_model("not-a-real-model")
        assert result is False
        assert "not a recognized AGY model" in capsys.readouterr().out
        _MODEL_CACHE.pop("not-a-real-model", None)

    def test_check_model_success(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home))
        register_agy_hooks(tmp_path, home=home)
        monkeypatch.setattr("scripts.ai_agent_bridge._model._REPO_ROOT", tmp_path)
        from scripts.ai_agent_bridge._config import _MODEL_CACHE
        from scripts.ai_agent_bridge._model import check_model
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)
        mock_result = MagicMock(returncode=0, stdout="MODEL_OK", stderr="")
        with patch("subprocess.run", return_value=mock_result) as run:
            assert check_model("gemini-3.8-flash-high") is True
        cmd = run.call_args.args[0]
        assert "agy" in cmd[0] or cmd[0].endswith("/agy")
        assert "--model" in cmd
        # Active 3.8 slug is preserved in the probe invocation.
        assert "gemini-3.8-flash-high" in cmd or "Gemini 3.8 Flash (High)" in cmd
        _MODEL_CACHE.pop("gemini-3.8-flash-high", None)


# ---------------------------------------------------------------------------
# 6. _prompts.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 7. _github.py
# ---------------------------------------------------------------------------

class TestGitHub:
    """Tests for scripts/ai_agent_bridge/_github.py."""

    def test_gh_comment_refuses_missing_matcher_before_transport(self, tmp_path, monkeypatch, capsys):
        from scripts.ai_agent_bridge._github import _gh_comment
        from scripts.opsec import prepublish

        monkeypatch.setattr(prepublish, "private_tooling", lambda: tmp_path / "missing-tooling")
        with patch("subprocess.run") as transport:
            assert _gh_comment(123, "body") is False
        transport.assert_not_called()
        assert "private matcher or rules unavailable/incompatible; write refused" in capsys.readouterr().out

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

    def test_post_review_to_github_existing_issue(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            result = _post_review_to_github("issue-42", "review text", "flash")
        assert result == 42

    def test_post_review_to_github_no_issue_skips(self):
        """When task_id doesn't map to an issue, don't create a new one (#970)."""
        from scripts.ai_agent_bridge._github import _post_review_to_github
        # No subprocess should be called — we skip GH posting entirely
        with patch("subprocess.run") as mock_run:
            result = _post_review_to_github("random-task", "review text", "opus")
        assert result is None
        mock_run.assert_not_called()

    def test_post_review_to_github_gh_not_found(self):
        from scripts.ai_agent_bridge._github import _post_review_to_github
        with patch("subprocess.run", side_effect=FileNotFoundError):
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

    def test_word_has_translation_after_parens(self):
        from scripts.audit.checks.content_quality_pipeline import _word_has_translation_after
        line = "Привіт (hello) to you"
        assert _word_has_translation_after(line, 6) is True  # after Привіт

    def test_word_is_in_translation_context(self):
        from scripts.audit.checks.content_quality_pipeline import _word_is_in_translation_context
        line = "(Привіт means hello)"
        assert _word_is_in_translation_context(line, 1) is True

    def test_check_untranslated_non_decodable_not_a1(self):
        from scripts.audit.checks.content_quality_pipeline import check_untranslated_non_decodable
        plan = {"decodable_letters": "А О У І М Н Т К С Л"}
        issues = check_untranslated_non_decodable("Привіт", module_num=1, level_code="B1", plan=plan)
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

    def test_collect_failed_words_from_str(self):
        from scripts.audit.checks.content_quality_pipeline import _collect_failed_words_from_str
        failed = {"кот"}
        result = _collect_failed_words_from_str("кот і собака", failed)
        assert "кот" in result

    def test_scan_activity_answers(self):
        from scripts.audit.checks.content_quality_pipeline import _scan_activity_answers
        act = {"answer": "кот", "items": [{"text": "собака", "options": ["кот", "пес"]}]}
        failed = {"кот"}
        result = _scan_activity_answers(act, failed)
        assert "кот" in result


# ---------------------------------------------------------------------------
# 9. template_compliance.py
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 10. naturalness_check.py
# ---------------------------------------------------------------------------

class TestNaturalnessCheck:
    """Tests for scripts/audit/naturalness_check.py."""

    @pytest.fixture(autouse=True)
    def _unit_test_interpreter(self, monkeypatch):
        """These file helpers do not spawn providers or require a checkout venv."""
        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
        from common import repo_root

        monkeypatch.setattr(repo_root, "project_interpreter", lambda root=None: Path(sys.executable))

    def test_update_meta_naturalness(self, tmp_path):
        import yaml

        from scripts.audit.naturalness_check import update_meta_naturalness
        meta_file = tmp_path / "test.yaml"
        meta_file.write_text("version: 1\n")
        update_meta_naturalness(meta_file, 9, "PASS", "Good", "2026-01-01")
        data = yaml.safe_load(meta_file.read_text())
        assert data["naturalness"]["score"] == 9
        assert data["naturalness"]["status"] == "PASS"
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

    def test_should_sample_deterministic(self):
        from scripts.scoring.sampling import should_sample
        # Same slug always gives same result
        r1 = should_sample("test-slug")
        r2 = should_sample("test-slug")
        assert r1 == r2

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


# ---------------------------------------------------------------------------
# 12. generate_activity_quality_queue.py
# ---------------------------------------------------------------------------

class TestGenerateActivityQualityQueue:
    """Tests for scripts/audit/generate_activity_quality_queue.py."""

    def test_extract_options_quiz(self):
        from scripts.audit.generate_activity_quality_queue import extract_options
        activity = {"type": "quiz", "items": [
            {"options": [{"text": "A", "correct": True}, {"text": "B", "correct": False}]}
        ]}
        options, correct = extract_options(activity)
        assert options == ["A", "B"]
        assert correct == "A"


# ---------------------------------------------------------------------------
# 13. finalize_activity_quality.py
# ---------------------------------------------------------------------------

class TestFinalizeActivityQuality:
    """Tests for scripts/audit/finalize_activity_quality.py."""

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
