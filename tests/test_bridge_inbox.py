from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from lu_machinery.agent_runtime.adapters import agy
from lu_machinery.agent_runtime.adapters.base import InvocationPlan
from lu_machinery.agent_runtime.errors import RateLimitedError
from lu_machinery.agent_runtime.result import Result
from lu_machinery.ai_agent_bridge import _channels, _config, _db, _inbox

from batch_gemini_config import FLASH_MODEL, PRO_MODEL

# Product fixtures retained from the machinery test consumers (C-5048).


def _agy_consistency_stream(slug, case):
    """Frozen author inputs; expectations live in the consuming tests."""
    other = "claude-opus-5-5-high" if "sonnet" in slug else "claude-sonnet-5-5-high"
    init = {"event": "init", "model": slug, "session_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419"}
    terminal = {
        "event": "result",
        "result": {"status": "SUCCESS", "response": "READY", "conversation_id": "7cd3ba85-817f-4a03-8223-1ff39ca42419"},
    }
    events = [init]
    if case == "display":
        init["model"] = "Claude Sonnet 5.5 (High)" if "sonnet" in slug else "Claude Opus 5.5 (High)"
    elif case in {"other-pin", "mismatch-then-duplicate", "mismatch-then-session"}:
        init["model"] = other
    elif case == "other-family":
        init["model"] = "gemini-3.8-flash-high"
    elif case == "nested-model":
        init["init"] = {"model": other}
    elif case == "nested-session":
        init["init"] = {"session_id": "different-session"}
    elif case == "terminal-session":
        terminal["result"]["conversation_id"] = "different-session"
    elif case.startswith("repeated"):
        repeated = dict(init)
        if case == "repeated-model":
            repeated["model"] = other
        elif case == "repeated-session":
            repeated["session_id"] = "different-session"
        elif case == "repeated-source":
            repeated["source"] = "configuration"
        events.append(repeated)
    elif case in {"unknown", "retired", "non-string"}:
        init["model"] = {"unknown": "unrecognized", "retired": "Claude Opus 4.6 (Thinking)", "non-string": 7}[case]
    elif case == "configuration":
        init["source"] = "requested"
    elif case == "missing":
        events = []
    elif case == "late":
        events.insert(0, {"event": "step_update"})
    elif case == "provider-failure":
        terminal["result"].update(status="ERROR", error="synthetic provider failure")
    if case == "mismatch-then-session":
        events.append({**init, "session_id": "different-session"})
    lines = list(map(json.dumps, events))
    if case in {"duplicate-after", "mismatch-then-duplicate"}:
        lines.append('{"event":"step_update","metadata":[{"model":"one","\\u006dodel":"two"}]}')
    lines.append(json.dumps(terminal))
    return "\n".join(lines) + "\n"


def _agy_identity_stream_plan(tmp_path, slug):
    conversation_id = "7cd3ba85-817f-4a03-8223-1ff39ca42419"
    app_data = tmp_path / "agy-data"
    transcript = app_data / "brain" / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
    transcript.parent.mkdir(parents=True)
    fixture = Path(__file__).resolve().parent / "fixtures" / "agy" / "verify_words_transcript.jsonl"
    transcript.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    log_file = tmp_path / "agy.log"
    log_file.write_text(f"Print mode: conversation={conversation_id}, sending message\n", encoding="utf-8")
    plan = InvocationPlan(
        cmd=["agy", "--output-format", "stream-json", "--model", slug],
        cwd=tmp_path,
        env_overrides={"AGY_RUNTIME_LOG_FILE": str(log_file), "AGY_APP_DATA_DIR": str(app_data)},
        metadata={"entire_fleet": {"requested_model": slug}},
    )
    terminal = {
        "event": "result",
        "result": {"status": "SUCCESS", "conversation_id": conversation_id, "response": "READY"},
    }
    return (plan, terminal)


_agy_SLUGS = ("claude-sonnet-5-5-high", "claude-opus-5-5-high")


def _agy_mock_agy_provider(monkeypatch, tmp_path, runner, *, stdout, exit_kind="complete", version="1.4.0"):
    """Mock only the process boundary, keeping adapter planning/parsing and runner custody."""
    from types import SimpleNamespace

    monkeypatch.setattr(agy, "require_hook_config", lambda *a, **k: None)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    plan, _ = _agy_identity_stream_plan(tmp_path, _agy_SLUGS[1])
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(tmp_path / "agy-data"))
    monkeypatch.setattr(agy, "_agy_app_data", lambda overrides: tmp_path / "agy-data")
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    binary = tmp_path / "agy-cli-fixture"
    binary.write_bytes(b"synthetic CLI artifact, never executed\n")
    original_which = agy.shutil.which
    monkeypatch.setattr(agy.shutil, "which", lambda name: str(binary) if name == "agy" else original_which(name))
    monkeypatch.setattr(runner, "has_headroom", lambda *a: (True, "fixture"))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: None)
    monkeypatch.setattr(runner, "write_record", lambda *a: None)
    monkeypatch.setattr(
        runner,
        "resolve_invocation_telemetry",
        lambda **k: SimpleNamespace(model=k["requested_model"], effort="high", cli_version=version),
    )
    monkeypatch.setattr(runner.PrimaryTreeWatch, "start", lambda **k: None)
    monkeypatch.setattr(runner._ChildCwdPin, "start", lambda **k: None)
    monkeypatch.setattr(runner, "_prepare_spawn_command", lambda cmd, env: (cmd, env))
    launches = []

    class Process:
        pid = 999999991
        returncode = None

        def poll(self):
            if self.returncode is not None:
                return self.returncode
            if exit_kind == "timeout":
                return None
            if exit_kind == "cancel":
                raise KeyboardInterrupt("synthetic cancellation")
            if exit_kind == "exception":
                raise RuntimeError("synthetic runtime failure")
            self.returncode = 0
            return self.returncode

        def wait(self, **kwargs):
            return self.returncode

    proc = Process()

    def spawn(cmd, **kwargs):
        launches.append((cmd, kwargs))
        return (proc, None, None)

    monkeypatch.setattr(runner, "_spawn_subprocess", spawn)
    monkeypatch.setattr(runner, "_kill_process_tree", lambda proc: setattr(proc, "returncode", -15))
    monkeypatch.setattr(runner, "_agy_process_group_exited", lambda pid: True)
    state = SimpleNamespace(stdout_lines=stdout.splitlines(keepends=True), stderr_lines=[])
    monkeypatch.setattr(runner, "start_watchdog", lambda *a, **k: (state, []))
    monkeypatch.setattr(runner, "stop_watchdog", lambda *a, **k: None)
    if exit_kind == "timeout":
        monkeypatch.setattr(runner, "should_kill", lambda *a, **k: "hard_timeout")
    return (launches, plan, binary)

@pytest.fixture(autouse=True)
def isolate_db(tmp_path):
    db_file = tmp_path / "messages.db"
    with patch("lu_machinery.ai_agent_bridge._config.DB_PATH", db_file):
        _db.init_db()
        yield db_file


def _delivery_rows(message_id: str) -> list[sqlite3.Row]:
    conn = _db.get_db()
    try:
        return conn.execute(
            """
            SELECT delivery_id, status, attempt_count, retry_after, last_error_kind
            FROM deliveries
            WHERE message_id = ?
            ORDER BY delivery_id
            """,
            (message_id,),
        ).fetchall()
    finally:
        conn.close()


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


def _set_delivery_model(message_id: str, model: str) -> None:
    conn = _db.get_db()
    try:
        conn.execute(
            "UPDATE deliveries SET to_model = ? WHERE message_id = ?",
            (model, message_id),
        )
        conn.commit()
    finally:
        conn.close()


def _ok_result(
    agent: str,
    *,
    model: str = "test-model",
    ok: bool = True,
    response: str = "bridge reply",
    stderr_excerpt: str | None = None,
    rate_limited: bool = False,
    returncode: int | None = 0,
    session_id: str | None = None,
) -> Result:
    return Result(
        ok=ok,
        agent=agent,
        model=model,
        mode="read-only",
        response=response,
        stderr_excerpt=stderr_excerpt,
        duration_s=0.1,
        session_id=session_id,
        rate_limited=rate_limited,
        stalled=False,
        returncode=returncode,
        usage_record={},
    )


@pytest.mark.parametrize("pin", ["claude-sonnet-5-5-high", "claude-opus-5-5-high"])
@pytest.mark.parametrize("case,ok", [
    ("exact", True), ("display", True), ("other-pin", False), ("other-family", False),
    ("repeated", False), ("nested-model", False), ("nested-session", False),
    ("terminal-session", False), ("duplicate-after", False), ("missing", False),
    ("configuration", False), ("provider-failure", False),
])
def test_native_agy_inbox_uses_observation_not_requested_identity(monkeypatch, tmp_path, pin, case, ok):
    from lu_machinery.agent_runtime import runner
    from lu_machinery.fleet_comms import bottleneck_alerts
    consistency_stream = _agy_consistency_stream
    mock_agy_provider = _agy_mock_agy_provider

    monkeypatch.setattr(bottleneck_alerts, "scan_bottlenecks_at_inbox_checkpoint", lambda **k: None)
    thread = _make_thread("agy")
    _set_delivery_model(str(thread[0]["message_id"]), pin)
    with patch.object(_config, "REPO_ROOT", tmp_path):
        launches, _, _ = mock_agy_provider(monkeypatch, tmp_path, runner, stdout=consistency_stream(pin, case))
        results = []

        def invoke(*args, **kwargs):
            assert not (kwargs.get("tool_config") or {}).get("run_nonce")
            result = runner.invoke(*args, **kwargs)
            results.append(result)
            return result

        monkeypatch.setattr(_inbox, "runtime_invoke", invoke)
        summary = _inbox.run_inbox("agy", max_messages=1, until_idle=False)

        assert len(launches) == len(results) == 1
        assert results[0].ok is ok
        assert results[0].model_identity is None
        assert results[0].model == pin
        assert summary.deliveries_failed == (0 if ok else 1)
        assert summary.deliveries_delivered == summary.replies_posted == (1 if ok else 0)
        messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
        assert len(messages) == (2 if ok else 1)
        if ok:
            assert messages[-1]["from_model"] == "unattested-harness"
            assert messages[-1]["body"] == "READY"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_single_thread_single_delivery(mock_invoke):
    thread = _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_delivered == 1
    assert summary.replies_posted == 1
    assert mock_invoke.call_count == 1
    assert mock_invoke.call_args.kwargs["mode"] == "read-only"
    assert mock_invoke.call_args.kwargs["initiator"] == "user"
    assert mock_invoke.call_args.kwargs["tool_config"]["discussion_readonly"] is True
    delivered = _delivery_rows(str(thread[0]["message_id"]))[0]
    assert delivered["status"] == "delivered"
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 2
    assert messages[-1]["from_agent"] == "claude"
    assert messages[-1]["parent_id"] == thread[0]["message_id"]


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_cold_call_persists_runtime_session(mock_invoke):
    thread = _make_thread("codex", count=1)
    mock_invoke.return_value = _ok_result(
        "codex",
        session_id="codex-session-one",
    )

    summary = _inbox.run_inbox("codex")

    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_args.kwargs["session_id"] is None
    task_id = _inbox._thread_session_key("topic", str(thread[0]["thread_id"]))
    assert _inbox._get_session_id(task_id, "codex") == "codex-session-one"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_same_thread_resumes_with_unseen_only_prompt(mock_invoke):
    thread = _make_thread("codex", count=1)
    mock_invoke.return_value = _ok_result(
        "codex",
        session_id="codex-session-one",
    )
    _inbox.run_inbox("codex")

    follow_up = _channels.post(
        "topic",
        "user",
        "message-2",
        to_agents=["codex"],
        parent_id=str(thread[0]["message_id"]),
        auto_snapshot=False,
    )
    mock_invoke.reset_mock()
    mock_invoke.return_value = _ok_result("codex", session_id="codex-session-one")

    summary = _inbox.run_inbox("codex")

    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_args.kwargs["session_id"] == "codex-session-one"
    prompt = mock_invoke.call_args.args[1]
    assert "Continue the existing bridge session" in prompt
    assert "message-2" in prompt
    assert "message-1" not in prompt
    assert str(follow_up["message_id"]) not in prompt


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_codex_sessions_are_isolated_by_thread(mock_invoke):
    first = _make_thread("codex", channel="first", count=1)
    second = _make_thread("codex", channel="second", count=1)
    first_task_id = _inbox._thread_session_key("first", str(first[0]["thread_id"]))
    _inbox._set_session_id(first_task_id, "codex", "first-session")
    mock_invoke.return_value = _ok_result("codex", session_id="second-session")

    summary = _inbox.run_inbox("codex")

    assert summary.threads_processed == 2
    calls_by_channel = {
        "first" if "#first" in call.args[1] else "second": call
        for call in mock_invoke.call_args_list
    }
    assert calls_by_channel["first"].kwargs["session_id"] == "first-session"
    assert calls_by_channel["second"].kwargs["session_id"] is None
    second_task_id = _inbox._thread_session_key("second", str(second[0]["thread_id"]))
    assert _inbox._get_session_id(second_task_id, "codex") == "second-session"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_failed_codex_result_does_not_overwrite_session(mock_invoke):
    thread = _make_thread("codex", count=1)
    task_id = _inbox._thread_session_key("topic", str(thread[0]["thread_id"]))
    _inbox._set_session_id(task_id, "codex", "existing-session")
    mock_invoke.return_value = _ok_result(
        "codex",
        ok=False,
        response="",
        stderr_excerpt="backend failed",
        session_id="unexpected-session",
        returncode=1,
    )

    _inbox.run_inbox("codex")

    assert mock_invoke.call_args.kwargs["session_id"] == "existing-session"
    assert _inbox._get_session_id(task_id, "codex") == "existing-session"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_single_thread_three_deliveries_coalesces(mock_invoke):
    thread = _make_thread("claude", count=3)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_delivered == 3
    assert summary.replies_posted == 1
    assert mock_invoke.call_count == 1
    rows = []
    for message in thread:
        rows.extend(_delivery_rows(str(message["message_id"])))
    assert all(row["status"] == "delivered" for row in rows)
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 4
    assert messages[-1]["parent_id"] == thread[-1]["message_id"]


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_thread_tool_error_fails_only_that_thread(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.side_effect = [RuntimeError("tool exploded"), _ok_result("claude")]

    summary = _inbox.run_inbox("claude")

    assert summary.deliveries_failed == 1
    assert summary.deliveries_delivered == 1
    assert summary.aborted is False
    assert mock_invoke.call_count == 2
    first_row = _delivery_rows(str(first[0]["message_id"]))[0]
    second_row = _delivery_rows(str(second[0]["message_id"]))[0]
    assert first_row["status"] == "failed"
    assert first_row["last_error_kind"] == "tool_error"
    assert second_row["status"] == "delivered"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_rate_limit_releases_and_aborts(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.side_effect = RateLimitedError("claude", "test-model", "quota hit")

    summary = _inbox.run_inbox("claude")

    assert summary.aborted is True
    assert summary.deliveries_released == 1
    assert mock_invoke.call_count == 1
    first_row = _delivery_rows(str(first[0]["message_id"]))[0]
    second_row = _delivery_rows(str(second[0]["message_id"]))[0]
    assert first_row["status"] == "pending"
    assert first_row["retry_after"] is not None
    assert first_row["last_error_kind"] == "rate_limited"
    # attempt_count stays at 1 (not decremented) — Gemini c2-review r1 BLOCKER:
    # net-zero attempts (claim +1, release -1) creates an infinite retry loop
    # if the provider stays down. The agent WAS attempted (it just hit a
    # provider-side fault), so the attempt is real. Eventually a genuinely-
    # broken provider exhausts DEFAULT_MAX_DELIVERY_ATTEMPTS and the delivery
    # reaches terminal `failed`, which is correct.
    assert first_row["attempt_count"] == 1
    assert second_row["status"] == "pending"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_until_idle_false_stops_after_one_thread(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=1)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", until_idle=False)

    assert summary.threads_processed == 1
    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_count == 1
    assert _delivery_rows(str(first[0]["message_id"]))[0]["status"] == "delivered"
    assert _delivery_rows(str(second[0]["message_id"]))[0]["status"] == "pending"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_max_messages_caps_deliveries(mock_invoke):
    first = _make_thread("claude", count=1)
    second = _make_thread("claude", count=2)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", max_messages=1)

    assert summary.deliveries_claimed == 1
    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_count == 1
    assert _delivery_rows(str(first[0]["message_id"]))[0]["status"] == "delivered"
    second_rows = []
    for message in second:
        second_rows.extend(_delivery_rows(str(message["message_id"])))
    assert all(row["status"] == "pending" for row in second_rows)


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_max_messages_soft_cap_first_thread(mock_invoke):
    """Regression: Gemini c2-review r1 BLOCKER — queue deadlock.

    If the oldest pending thread has MORE deliveries than max_messages, the
    original code returned (None, True) and broke the loop without processing
    anything. Same thread blocked every subsequent run forever.

    Fix: max_messages is a SOFT cap that never applies to the FIRST claim
    of a run. Subsequent claims still respect the budget so a single run
    can't blow past max_messages by an unbounded amount.
    """
    thread = _make_thread("claude", count=3)
    mock_invoke.return_value = _ok_result("claude")

    summary = _inbox.run_inbox("claude", max_messages=1)

    # All 3 deliveries from the oldest thread processed despite max_messages=1.
    assert summary.threads_processed == 1
    assert summary.deliveries_claimed == 3
    assert summary.deliveries_delivered == 3
    assert mock_invoke.call_count == 1
    for message in thread:
        assert _delivery_rows(str(message["message_id"]))[0]["status"] == "delivered"


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_429_falls_back_pro_to_flash_and_persists_model(mock_invoke):
    """Retired Pro's alias equals Flash and must not create a self-retry cycle."""
    assert PRO_MODEL == FLASH_MODEL
    thread = _make_thread("gemini", count=1)
    message_id = str(thread[0]["message_id"])
    _set_delivery_model(message_id, PRO_MODEL)
    mock_invoke.return_value = _ok_result(
        "gemini", model=FLASH_MODEL, ok=False, response="",
        stderr_excerpt="HTTP 429 Too Many Requests", returncode=1,
    )
    summary = _inbox.run_inbox("gemini")
    assert summary.deliveries_failed == 1
    mock_invoke.assert_called_once()
    assert mock_invoke.call_args.kwargs["model"] == FLASH_MODEL
    delivered = _channels.deliveries_for_message(message_id)[0]
    assert delivered["status"] == "failed"
    assert delivered["to_model"] == FLASH_MODEL
    assert len(_channels.read("topic", thread_id=str(thread[0]["thread_id"]))) == 1


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_passes_auth_mode_to_runtime(mock_invoke):
    thread = _make_thread("gemini", count=1)
    _set_delivery_model(str(thread[0]["message_id"]), PRO_MODEL)
    mock_invoke.return_value = _ok_result("gemini", model=PRO_MODEL, response="bridge reply")

    summary = _inbox.run_inbox("gemini", gemini_auth_mode="subscription")

    assert summary.deliveries_delivered == 1
    assert mock_invoke.call_args.kwargs["tool_config"] == {
        "auth_mode": "subscription",
        "discussion_readonly": True,
    }


@pytest.mark.parametrize("raises", [False, True])
@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_flash_capacity_exhaustion_does_not_retry_alias(mock_invoke, raises):
    thread = _make_thread("gemini", count=1)
    message_id = str(thread[0]["message_id"])
    _set_delivery_model(message_id, FLASH_MODEL)
    if raises:
        mock_invoke.side_effect = _inbox.RateLimitedError("gemini", FLASH_MODEL, "429 quota")
    else:
        mock_invoke.return_value = _ok_result(
            "gemini", model=FLASH_MODEL, ok=False, response="",
            stderr_excerpt="HTTP 429 Too Many Requests", returncode=1,
        )

    summary = _inbox.run_inbox("gemini")

    assert summary.deliveries_failed == (0 if raises else 1)
    assert summary.deliveries_released == (1 if raises else 0)
    assert summary.aborted is raises
    assert mock_invoke.call_count == 1
    assert mock_invoke.call_args.kwargs["model"] == FLASH_MODEL
    delivered = _channels.deliveries_for_message(message_id)[0]
    assert delivered["status"] == ("pending" if raises else "failed")
    assert delivered["to_model"] == FLASH_MODEL
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 1


@patch("lu_machinery.ai_agent_bridge._inbox.runtime_invoke")
def test_run_inbox_gemini_429_exhausts_cascade_and_fails(mock_invoke):
    thread = _make_thread("gemini", count=1)
    message_id = str(thread[0]["message_id"])
    _set_delivery_model(message_id, PRO_MODEL)
    mock_invoke.side_effect = [
        _ok_result(
            "gemini",
            model=PRO_MODEL,
            ok=False,
            response="",
            stderr_excerpt="HTTP 429 Too Many Requests",
            returncode=1,
        ),
        _ok_result(
            "gemini",
            model=FLASH_MODEL,
            ok=False,
            response="",
            stderr_excerpt="HTTP 429 Too Many Requests",
            returncode=1,
        ),
    ]

    summary = _inbox.run_inbox("gemini")

    assert summary.deliveries_failed == 1
    assert mock_invoke.call_count == 1
    delivered = _channels.deliveries_for_message(message_id)[0]
    assert delivered["status"] == "failed"
    assert delivered["to_model"] == FLASH_MODEL
    messages = _channels.read("topic", thread_id=str(thread[0]["thread_id"]))
    assert len(messages) == 1
