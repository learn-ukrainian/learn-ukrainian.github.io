from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.result import Result
from ai_agent_bridge import _channels, _channels_cli, _cli, _db


def test_post_preflight_warns_for_large_body():
    warning = _channels_cli._post_preflight_warning(body="x" * 8001, mode="workspace-write")

    assert warning == (
        "[PREFLIGHT] brief looks large (8001 chars, 0 files mentioned). Consider --deadline 1800 or splitting."
    )


def test_post_preflight_warns_for_many_file_mentions():
    body = "\n".join(
        [
            "scripts/a.py",
            "tests/test_a.py",
            "pkg/worker.py",
            "app/api/router.py",
            "foo/bar.py",
        ]
    )

    warning = _channels_cli._post_preflight_warning(body=body, mode="workspace-write")

    assert warning == (
        f"[PREFLIGHT] brief looks large ({len(body)} chars, 5 files mentioned). Consider --deadline 1800 or splitting."
    )


def test_post_preflight_warns_for_multi_step_markers():
    body = "Fix this and then update that."
    warning = _channels_cli._post_preflight_warning(body=body, mode="workspace-write")

    assert warning == (
        f"[PREFLIGHT] brief looks large ({len(body)} chars, 0 files mentioned). Consider --deadline 1800 or splitting."
    )


def test_post_preflight_skips_non_workspace_write_mode():
    warning = _channels_cli._post_preflight_warning(
        body="scripts/a.py\ntests/test_a.py\npkg/worker.py\napp/api/router.py\nfoo/bar.py",
        mode="read-only",
    )

    assert warning is None


@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("ai_agent_bridge._config.DB_PATH", db_file), patch("ai_agent_bridge._db.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _run_cli(argv: list[str]) -> int:
    with patch.object(sys, "argv", ["ab", *argv]):
        try:
            _cli.main()
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 0
    return 0


def _make_thread(
    agent: str,
    *,
    channel: str = "topic",
    count: int = 1,
) -> list[dict[str, object]]:
    if _channels.get_channel(channel) is None:
        _channels.create_channel(channel)

    messages: list[dict[str, object]] = []
    parent_id: str | None = None
    for index in range(count):
        post = _channels.post(
            channel,
            "user",
            f"message-{index + 1}",
            to_agents=[agent],
            parent_id=parent_id,
            auto_snapshot=False,
        )
        messages.append(post)
        parent_id = str(post["message_id"])
    return messages


def _set_message_created_at(message_id: str, created_at: str) -> None:
    conn = _db.get_db()
    try:
        conn.execute(
            "UPDATE channel_messages SET created_at = ? WHERE message_id = ?",
            (created_at, message_id),
        )
        conn.commit()
    finally:
        conn.close()


def _delivery_statuses() -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT d.status, d.to_agent, cm.body
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            """
        ).fetchall()
    finally:
        conn.close()


def _oldest_pending_delivery_id(agent: str) -> str | None:
    conn = _db.get_db()
    try:
        row = conn.execute(
            """
            SELECT d.delivery_id
            FROM deliveries d
            JOIN channel_messages cm ON cm.message_id = d.message_id
            WHERE d.to_agent = ? AND d.status = 'pending'
            ORDER BY cm.created_at ASC, d.delivery_id ASC
            LIMIT 1
            """,
            (agent,),
        ).fetchone()
    finally:
        conn.close()
    return str(row["delivery_id"]) if row is not None else None


def _delivery_detail(delivery_id: str) -> sqlite3.Row:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT delivery_id, status, error, delivered_at
            FROM deliveries
            WHERE delivery_id = ?
            """,
            (delivery_id,),
        ).fetchone()
    finally:
        conn.close()


def _install_fake_inbox_module(monkeypatch, run_inbox) -> None:
    fake_inbox_module = ModuleType("ai_agent_bridge._inbox")
    fake_inbox_module.run_inbox = run_inbox
    monkeypatch.setitem(sys.modules, "ai_agent_bridge._inbox", fake_inbox_module)


def _reply_deliveries() -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT cm.from_agent, cm.parent_id, d.to_agent, d.status, d.delivered_at
            FROM channel_messages cm
            JOIN deliveries d ON d.message_id = cm.message_id
            WHERE cm.kind = 'reply'
            ORDER BY cm.from_agent ASC, d.to_agent ASC
            """
        ).fetchall()
    finally:
        conn.close()


def _ok_result(agent: str) -> Result:
    return Result(
        ok=True,
        agent=agent,
        model="test-model",
        mode="read-only",
        response=f"{agent} reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )


def test_inbox_show_empty(capsys):
    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "claude inbox:" in captured.out
    assert "pending:    0" in captured.out
    assert "processing: 0" in captured.out
    assert "failed (last 24h): 0" in captured.out
    assert "    (none)" in captured.out


def test_inbox_show_accepts_codex_desktop(capsys):
    exit_code = _run_cli(["inbox", "show", "codex-desktop"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "codex-desktop inbox:" in captured.out
    assert "pending:    0" in captured.out


def test_inbox_ack_marks_delivery_delivered(capsys):
    thread = _make_thread("claude", count=1)
    delivery_id = _channels.deliveries_for_message(str(thread[0]["message_id"]))[0]["delivery_id"]

    exit_code = _run_cli(
        [
            "inbox",
            "ack",
            delivery_id,
            "--error",
            "processed by codex-desktop automation",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"✅ delivery {delivery_id} → delivered" in captured.out
    detail = _delivery_detail(delivery_id)
    assert detail["status"] == "delivered"
    assert detail["error"] == "processed by codex-desktop automation"
    assert detail["delivered_at"] is not None


def test_inbox_ack_unknown_delivery_id_errors(capsys):
    exit_code = _run_cli(["inbox", "ack", "missing-delivery-id"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "delivery_id 'missing-delivery-id' not found" in captured.err


def test_inbox_ack_already_delivered_is_noop(capsys):
    thread = _make_thread("claude", count=1)
    delivery_id = _channels.deliveries_for_message(str(thread[0]["message_id"]))[0]["delivery_id"]
    assert _run_cli(["inbox", "ack", delivery_id]) == 0
    capsys.readouterr()

    exit_code = _run_cli(["inbox", "ack", delivery_id])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert f"delivery {delivery_id} is already 'delivered' (no-op)" in captured.out


def test_post_from_codex_desktop_is_accepted(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(
        [
            "post",
            "topic",
            "desktop status",
            "--from-agent",
            "codex-desktop",
            "--no-snapshot",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "✅ posted to #topic" in captured.out
    assert _channels.read("topic")[0]["from_agent"] == "codex-desktop"


def test_post_to_codex_desktop_routes_delivery(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(
        [
            "post",
            "topic",
            "desktop brief",
            "--to",
            "codex-desktop",
            "--from-agent",
            "claude",
            "--no-snapshot",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "→ codex-desktop  (1 deliveries)" in captured.out
    delivery = _channels.deliveries_for_message(_channels.read("topic")[0]["message_id"])[0]
    assert delivery["to_agent"] == "codex-desktop"


def test_post_from_existing_codex_path_still_works(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(
        [
            "post",
            "topic",
            "codex status",
            "--from-agent",
            "codex",
            "--no-snapshot",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert _channels.read("topic")[0]["from_agent"] == "codex"


def test_channel_set_ttl_persists(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(["channel", "set-ttl", "topic", "6"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "TTL set to 6h" in captured.out
    assert _channels.get_channel("topic")["max_age_hours"] == 6


@patch("agent_runtime.runner.invoke")
def test_discuss_replies_create_delivered_reply_deliveries(mock_invoke, monkeypatch, capsys):
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)

    def _discuss_result(agent: str, *_args, **_kwargs) -> Result:
        return Result(
            ok=True,
            agent=agent,
            model="test-model",
            mode="read-only",
            response=f"{agent} discuss reply [AGREE]",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    mock_invoke.side_effect = _discuss_result

    # Round 1 cannot short-circuit (per `_channels_cli.py:1290-1304` — round 1
    # is parallel fan-out, agents haven't seen each other's replies yet, so
    # [AGREE] in round 1 means "I'm done with my answer" not cross-agent
    # assent). Convergence requires ≥ round 2, so use --max-rounds 2 here.
    # Pre-protocol-fix this test passed with --max-rounds 1; updated 2026-05-05
    # to match the round-1 short-circuit block (commit 872d8791).
    exit_code = _run_cli(["discuss", "shared", "topic", "--with", "claude,codex", "--max-rounds", "2"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ converged at round 2" in captured.out

    # Each round produces N*(N-1) reply deliveries (each agent's reply is
    # delivered to every OTHER agent). With 2 agents × 2 rounds = 4 deliveries.
    reply_deliveries = _reply_deliveries()
    assert len(reply_deliveries) == 4
    # Set collapses duplicates across rounds — still just 2 distinct
    # (from, to, status) tuples for the 2-agent case.
    assert {(row["from_agent"], row["to_agent"], row["status"]) for row in reply_deliveries} == {
        ("claude", "codex", "delivered"),
        ("codex", "claude", "delivered"),
    }
    assert all(row["delivered_at"] is not None for row in reply_deliveries)
    assert all(row["parent_id"] is not None for row in reply_deliveries)


@patch("agent_runtime.runner.invoke")
def test_discuss_fails_and_warns_when_agent_writes_worktree(
    mock_invoke,
    monkeypatch,
    tmp_path,
    capsys,
):
    _channels.create_channel("shared")
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels_cli, "REPO_ROOT", tmp_path)
    git_env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        env=git_env,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        env=git_env,
    )
    (tmp_path / "README.md").write_text("clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True, env=git_env)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        env=git_env,
    )

    def _write_attempt(agent: str, *_args, **kwargs) -> Result:
        assert kwargs["mode"] == "read-only"
        # tool_config now also carries `is_new_session: True` on round 1 for
        # resumable agents (#1782 tier-2 warm-cache fix). Test the load-bearing
        # contract — that discuss participants run in read-only — not the
        # exact dict shape.
        assert kwargs["tool_config"].get("discussion_readonly") is True
        (tmp_path / "unauthorized.txt").write_text("write attempt\n", encoding="utf-8")
        return Result(
            ok=True,
            agent=agent,
            model="test-model",
            mode="read-only",
            response=f"{agent} reply [AGREE]",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        )

    mock_invoke.side_effect = _write_attempt

    exit_code = _run_cli(["discuss", "shared", "topic", "--with", "claude", "--max-rounds", "1"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "READ-ONLY DISCUSSION VIOLATION" in captured.err
    assert "unauthorized.txt" in captured.err

    messages = _channels.read("shared", tail=10)
    assert any("READ-ONLY DISCUSSION VIOLATION" in msg["body"] for msg in messages)
    assert not any(msg["from_agent"] == "claude" for msg in messages)
    rev_count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
        env=git_env,
    ).stdout.strip()
    assert rev_count == "1"


def test_inbox_show_with_pending_and_failed(capsys):
    _channels.create_channel("topic")
    first = _channels.post("topic", "user", "first pending", to_agents=["claude"], auto_snapshot=False)
    second = _channels.post("topic", "user", "second pending", to_agents=["claude"], auto_snapshot=False)
    third = _channels.post("topic", "user", "third pending", to_agents=["claude"], auto_snapshot=False)
    failed = _channels.post("topic", "user", "failed message", to_agents=["claude"], auto_snapshot=False)
    _channels.mark_delivery(failed["delivery_ids"][0], "failed", error="boom")
    old_ts = (datetime.now(UTC) - timedelta(minutes=12)).isoformat()
    _set_message_created_at(str(first["message_id"]), old_ts)

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "pending:    3 (oldest 12m ago)" in captured.out
    assert "failed (last 24h): 1" in captured.out
    assert "[topic/" in captured.out
    assert 'user → "first pending"' in captured.out
    assert second["message_id"] != third["message_id"]


def test_inbox_run_once_processes_one_thread(monkeypatch, capsys):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)

    calls: list[tuple[str, dict[str, object]]] = []

    def _fake_run_inbox(agent: str, **kwargs):
        calls.append((agent, kwargs))
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["inbox", "run", "claude", "--once"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "processed: 1 deliveries | 1 threads | 0 failed | duration:" in captured.out
    statuses = _delivery_statuses()
    assert statuses[0]["status"] == "delivered"
    assert statuses[1]["status"] == "pending"
    assert calls == [
        (
            "claude",
            {
                "max_messages": None,
                "until_idle": False,
                "stop_after_seconds": None,
                "hard_timeout": 900,
            },
        )
    ]
    assert first[0]["thread_id"] != second[0]["thread_id"]


def test_sync_all_iterates_known_agents(monkeypatch, capsys):
    for agent in _channels.VALID_AGENTS:
        _make_thread(agent, channel=f"{agent}-topic", count=1)
    # Mirrors the live `cmd_sync --all` iteration order, which is
    # `[agent for agent in _channels.VALID_AGENTS if _cli_available_agent(agent)]`.
    # When a new CLI agent is registered (e.g. grok via #1934, deepseek
    # via #2107, cursor via Phase 2 PR), this list tracks the registry —
    # the test guards the iteration order, not a frozen subset.
    cli_agents = [
        "agy",
        "claude",
        "codex",
        "grok",
        "grok-build",
        "glm",
        "kimi",
        "deepseek",
        "cursor",
    ]

    calls: list[tuple[str, dict[str, object]]] = []

    def _fake_run_inbox(agent: str, **kwargs):
        calls.append((agent, kwargs))
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["sync", "--all"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert [call[0] for call in calls] == cli_agents
    assert captured.out.count("processed: 1 deliveries | 1 threads | 0 failed | duration:") == len(cli_agents)


def test_inbox_run_rejects_codex_desktop(capsys):
    exit_code = _run_cli(["inbox", "run", "codex-desktop", "--once"])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "cli_available=False" in captured.err
    assert "ab inbox show" in captured.err


def test_backlog_banner_triggers_for_old_pending_delivery(monkeypatch, capsys):
    thread = _make_thread("codex", count=1)
    monkeypatch.setenv("AB_BACKLOG_WARN_HOURS", "2")
    old_ts = (datetime.now(UTC) - timedelta(hours=6, minutes=12)).isoformat()
    _set_message_created_at(str(thread[0]["message_id"]), old_ts)

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "⚠️  codex has 1 pending deliveries (oldest 6h12m)." in captured.err
    assert "Run 'ab inbox run codex' to drain." in captured.err


def test_backlog_banner_does_not_trigger_for_fresh_pending_delivery(monkeypatch, capsys):
    _make_thread("codex", count=1)
    monkeypatch.setenv("AB_BACKLOG_WARN_HOURS", "2")

    exit_code = _run_cli(["inbox", "show", "claude"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""


def test_post_model_flag_stores_delivery_target_model(capsys):
    _channels.create_channel("topic")

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello gemini",
            "--to",
            "gemini",
            "--model",
            "gemini-3-flash-preview",
            "--no-snapshot",
        ]
    )
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]

    assert post_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert delivery["to_model"] == "gemini-3-flash-preview"


def test_post_model_flag_applies_to_default_channel_subscribers(capsys):
    _channels.create_channel("topic", subscribers=["gemini"])

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello subscriber",
            "--model",
            "gemini-3-pro-preview",
            "--no-snapshot",
        ]
    )
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]

    assert post_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert delivery["to_model"] == "gemini-3-pro-preview"


def test_post_workspace_write_large_body_preflight_warns_to_stderr_and_still_posts(capsys):
    _channels.create_channel("topic")
    body = "x" * 8001

    exit_code = _run_cli(["post", "topic", body, "--mode", "workspace-write", "--no-snapshot"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "✅ posted to #topic" in captured.out
    assert (
        "[PREFLIGHT] brief looks large (8001 chars, 0 files mentioned). Consider --deadline 1800 or splitting."
    ) in captured.err
    assert _channels.read("topic")[0]["body"] == body


def test_inbox_run_deadline_flag_overrides_worker_timeout(monkeypatch, capsys):
    captured_run: dict[str, object] = {}

    def _fake_run_inbox(agent: str, **kwargs):
        captured_run["agent"] = agent
        captured_run.update(kwargs)
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    exit_code = _run_cli(["inbox", "run", "claude", "--once", "--deadline", "1800"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured_run == {
        "agent": "claude",
        "max_messages": None,
        "until_idle": False,
        "stop_after_seconds": None,
        "hard_timeout": 1800,
    }


def test_post_deadline_flag_stores_delivery_override_and_worker_uses_it(monkeypatch, capsys):
    _channels.create_channel("topic")

    captured_run: dict[str, object] = {}

    def _fake_run_inbox(agent: str, **kwargs):
        delivery_id = _oldest_pending_delivery_id(agent)
        assert delivery_id is not None
        message = _channels.read("topic")[0]
        delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
        captured_run["hard_timeout"] = max(
            int(kwargs["hard_timeout"]),
            int(delivery["deadline_seconds"] or 0),
        )
        _channels.mark_delivery(delivery_id, "delivered")
        return SimpleNamespace(
            deliveries_claimed=1,
            threads_processed=1,
            deliveries_failed=0,
            aborted=False,
        )

    _install_fake_inbox_module(monkeypatch, _fake_run_inbox)

    post_exit = _run_cli(
        [
            "post",
            "topic",
            "hello codex",
            "--to",
            "codex",
            "--deadline",
            "1200",
            "--no-snapshot",
        ]
    )
    run_exit = _run_cli(["inbox", "run", "codex", "--once"])

    assert post_exit == 0
    assert run_exit == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
    assert delivery["deadline_seconds"] == 1200
    assert captured_run["hard_timeout"] == 1200


def test_deadline_whitelist_accepts_1800(capsys):
    _channels.create_channel("topic")

    exit_code = _run_cli(["post", "topic", "hello", "--to", "claude", "--deadline", "1800", "--no-snapshot"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    message = _channels.read("topic")[0]
    delivery = _channels.deliveries_for_message(str(message["message_id"]))[0]
    assert delivery["deadline_seconds"] == 1800


def test_invalid_deadline_value_is_rejected_with_helpful_error(capsys):
    exit_code = _run_cli(["post", "topic", "hello", "--deadline", "999"])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert "deadline must be one of: 300, 600, 900, 1200, 1800, 2400, 3000" in captured.err


def test_help_includes_model_and_deadline_flags(capsys):
    parser = _cli._build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["post", "--help"])
    post_help = capsys.readouterr()
    assert "--model" in post_help.out
    assert "--deadline" in post_help.out

    with pytest.raises(SystemExit):
        parser.parse_args(["inbox", "run", "--help"])
    inbox_help = capsys.readouterr()
    assert "--deadline" in inbox_help.out
    assert "--auth" in inbox_help.out

    with pytest.raises(SystemExit):
        parser.parse_args(["ask-gemini", "--help"])
    ask_gemini_help = capsys.readouterr()
    assert "--auth" in ask_gemini_help.out


def test_detect_caller_identity_honors_session_handoff_agent(monkeypatch):
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "claude-infra")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-project")

    assert _cli._detect_caller_identity_from_env() == "claude-infra"


def test_explicit_from_mismatch_with_handoff_agent_is_warning_tagged(monkeypatch, capsys):
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "claude-folk")

    sender = _cli._resolve_from_llm(SimpleNamespace(from_llm="claude-infra"))

    assert sender == "claude-infra"
    assert "[SENDER_IDENTITY_MISMATCH]" in capsys.readouterr().err


def test_detect_caller_identity_unknown_handoff_falls_through(monkeypatch):
    # Clear GROK_AGENT etc. first: when this suite runs under the native grok
    # CLI (export GROK_AGENT=1), the sentinel would otherwise win over the soft
    # CLAUDE_PROJECT_DIR heuristic and false-fail the fall-through assertion.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "not-a-real-agent")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-project")

    assert _cli._detect_caller_identity_from_env() == "claude"


def _clear_identity_env(monkeypatch) -> None:
    for var in (
        "SESSION_HANDOFF_AGENT",
        "CLAUDE_AGENT_NAME",
        "CODEX_SESSION",
        "GROK_AGENT",
        "CLAUDE_PROJECT_DIR",
        "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(var, raising=False)


def test_detect_caller_identity_grok_agent_maps_to_canonical_grok(monkeypatch):
    # The native grok CLI exports GROK_AGENT for every tool shell it spawns
    # (model-independent). It must auto-detect as the canonical `grok` seat
    # (historical alias: grok-build) so a grok session can `ab ask-claude`
    # without --from and get the reply back.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("GROK_AGENT", "1")

    assert _cli._detect_caller_identity_from_env() == "grok"


def test_detect_caller_identity_grok_agent_beats_soft_claude_heuristic(monkeypatch):
    # A grok session that inherited a stray CLAUDE_* var must still resolve to
    # the canonical `grok` seat, never misroute to the claude inbox.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("GROK_AGENT", "1")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/tmp/claude-project")

    assert _cli._detect_caller_identity_from_env() == "grok"


def test_detect_caller_identity_grok_agent_profile_name_is_not_a_false_positive(monkeypatch):
    # GROK_AGENT doubles as an agent-profile *name* selector; only the tool-shell
    # sentinel value "1" means "spawned by a grok CLI shell". A profile name must
    # NOT be mistaken for the grok-build lane — it falls through to normal detect.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("GROK_AGENT", "my-custom-agent")

    assert _cli._detect_caller_identity_from_env() is None


def test_detect_caller_identity_explicit_handoff_still_wins_over_grok_agent(monkeypatch):
    # An explicit, validated SESSION_HANDOFF_AGENT is authoritative over the
    # weaker GROK_AGENT marker.
    _clear_identity_env(monkeypatch)
    monkeypatch.setenv("GROK_AGENT", "1")
    monkeypatch.setenv("SESSION_HANDOFF_AGENT", "codex")

    assert _cli._detect_caller_identity_from_env() == "codex"


def test_grok_build_is_valid_agent():
    assert "grok-build" in _channels.VALID_AGENTS


def test_claude_infra_is_valid_agent():
    assert "claude-infra" in _channels.VALID_AGENTS


def test_ask_claude_reads_body_from_stdin_on_dash(monkeypatch):
    # Regression for the grok "empty result" bug: ask-claude used args.content
    # directly, so `ask-claude - < prompt.md` sent the literal "-" as the body.
    # Every other ask-* handler resolves "-" to stdin; ask-claude must too.
    captured: dict[str, object] = {}

    def _fake_ask_claude(content, *_args, **_kwargs):
        captured["content"] = content

    monkeypatch.setattr(_cli, "ask_claude", _fake_ask_claude)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(read=lambda: "the real question body"))

    exit_code = _run_cli(["ask-claude", "-", "--task-id", "t-stdin", "--from", "grok-build"])

    assert exit_code == 0
    assert captured["content"] == "the real question body"


def test_ask_claude_literal_content_is_not_treated_as_stdin(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_ask_claude(content, *_args, **_kwargs):
        captured["content"] = content

    monkeypatch.setattr(_cli, "ask_claude", _fake_ask_claude)
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(read=lambda: "SHOULD-NOT-BE-USED"))

    exit_code = _run_cli(["ask-claude", "a literal question", "--task-id", "t-lit", "--from", "grok-build"])

    assert exit_code == 0
    assert captured["content"] == "a literal question"


def test_recipient_choices_cover_every_valid_agent():
    # Regression: inbox --for / send --to / ack-all hardcoded {claude,gemini,codex},
    # silently second-classing grok-build, grok, kimi, agy, and cursor.
    parser = _cli._build_parser()
    for agent in ("grok-build", "grok", "kimi", "agy", "cursor"):
        assert parser.parse_args(["inbox", "--for", agent]).for_llm == agent
        assert parser.parse_args(["ack-all", agent]).agent == agent
        assert parser.parse_args(["send", "hi", "--to", agent]).to_llm == agent
