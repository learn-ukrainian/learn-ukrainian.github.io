from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.errors import RateLimitedError
from agent_runtime.result import Result
from batch_gemini_config import FALLBACK_MODEL, PRO_MODEL

from scripts.ai_agent_bridge._acp_compat import registered_participant_model
from scripts.ai_agent_bridge._cli import _handle_ask_gemini
from scripts.ai_agent_bridge._db import get_db, init_db
from scripts.ai_agent_bridge._gemini import _run_gemini_sync
from scripts.ai_agent_bridge._messaging import send_message


@pytest.fixture
def bridge_db(tmp_path):
    db_path = tmp_path / "messages.db"
    with (
        patch("scripts.ai_agent_bridge._config.DB_PATH", db_path),
        patch("scripts.ai_agent_bridge._db.DB_PATH", db_path),
    ):
        conn = init_db()
        conn.close()
        yield db_path


def _message_to_model(message_id: int) -> str | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT json_extract(data, '$.to_model') FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        assert row is not None
        return row[0]
    finally:
        conn.close()


@patch("scripts.ai_agent_bridge._gemini._route_gemini_response")
@patch("scripts.ai_agent_bridge._gemini.acknowledge")
@patch("scripts.ai_agent_bridge._gemini.runtime_invoke")
def test_run_gemini_sync_429_retries_same_model_then_falls_back_to_auto(
    mock_invoke,
    mock_acknowledge,
    mock_route_response,
    bridge_db,
):
    message_id = send_message(
        "Please review this",
        task_id="issue-1234",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        to_model=PRO_MODEL,
        quiet=True,
    )
    msg = {
        "id": message_id,
        "task_id": "issue-1234",
        "from": "claude",
        "to": "gemini",
        "type": "query",
        "content": "Please review this",
        "data": None,
    }

    mock_invoke.side_effect = [
        RateLimitedError("gemini", PRO_MODEL, "HTTP 429 No capacity available"),
        RateLimitedError("gemini", PRO_MODEL, "HTTP 429 No capacity available"),
        Result(
            ok=True,
            agent="gemini",
            model=FALLBACK_MODEL,
            mode="workspace-write",
            response="bridge reply",
            stderr_excerpt=None,
            duration_s=0.1,
            session_id=None,
            rate_limited=False,
            stalled=False,
            returncode=0,
            usage_record={},
        ),
    ]

    with (
        patch("scripts.ai_agent_bridge._gemini._is_task_locked", return_value=False),
        patch("scripts.ai_agent_bridge._gemini._write_pid_file"),
        patch("scripts.ai_agent_bridge._gemini._remove_pid_file"),
        patch("scripts.ai_agent_bridge._gemini.atexit.register"),
    ):
        response = _run_gemini_sync(
            msg,
            message_id,
            PRO_MODEL,
            "bridge prompt",
            no_timeout=False,
            stdout_only=True,
            output_path=None,
            allow_write=False,
            skip_github=True,
            auth_mode=None,
        )

    invoked_models = [call.kwargs["model"] for call in mock_invoke.call_args_list]
    assert invoked_models == [PRO_MODEL, PRO_MODEL, FALLBACK_MODEL]
    assert _message_to_model(message_id) == FALLBACK_MODEL
    assert response == "[model=auto, pro-capacity-unavailable]\n\nbridge reply"
    mock_route_response.assert_called_once()
    assert mock_route_response.call_args.args[2] == FALLBACK_MODEL
    mock_acknowledge.assert_called_once_with(message_id, quiet=True)


@patch("scripts.ai_agent_bridge._gemini._route_gemini_response")
@patch("scripts.ai_agent_bridge._gemini.acknowledge")
@patch("scripts.ai_agent_bridge._gemini.runtime_invoke")
def test_run_gemini_sync_passes_auth_mode_to_runtime(
    mock_invoke,
    _mock_acknowledge,
    _mock_route_response,
    bridge_db,
):
    message_id = send_message(
        "Please review this",
        task_id="issue-1235",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        quiet=True,
    )
    msg = {
        "id": message_id,
        "task_id": "issue-1235",
        "from": "claude",
        "to": "gemini",
        "type": "query",
        "content": "Please review this",
        "data": None,
    }

    mock_invoke.return_value = Result(
        ok=True,
        agent="gemini",
        model=PRO_MODEL,
        mode="workspace-write",
        response="bridge reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )

    with (
        patch("scripts.ai_agent_bridge._gemini._is_task_locked", return_value=False),
        patch("scripts.ai_agent_bridge._gemini._write_pid_file"),
        patch("scripts.ai_agent_bridge._gemini._remove_pid_file"),
        patch("scripts.ai_agent_bridge._gemini.atexit.register"),
    ):
        _run_gemini_sync(
            msg,
            message_id,
            PRO_MODEL,
            "bridge prompt",
            no_timeout=False,
            stdout_only=True,
            output_path=None,
            allow_write=False,
            skip_github=True,
            auth_mode="subscription",
        )

    assert mock_invoke.call_args.kwargs["tool_config"] == {"auth_mode": "subscription"}


def _ok_result() -> Result:
    return Result(
        ok=True,
        agent="gemini",
        model=PRO_MODEL,
        mode="read-only",
        response="reply",
        stderr_excerpt=None,
        duration_s=0.1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={},
    )


@pytest.mark.parametrize(
    "allow_write, expected_mode",
    [(False, "read-only"), (True, "workspace-write")],
)
@patch("scripts.ai_agent_bridge._gemini._route_gemini_response")
@patch("scripts.ai_agent_bridge._gemini.acknowledge")
@patch("scripts.ai_agent_bridge._gemini.runtime_invoke")
def test_run_gemini_sync_derives_runtime_mode_from_allow_write(
    mock_invoke,
    _ack,
    _route,
    bridge_db,
    allow_write,
    expected_mode,
):
    """#4446: the runtime write-mode tracks write *intent* (``--allow-write``),
    not the CLI approval flag — plain Q&A runs ``read-only`` so an ``ask-gemini``
    query can no longer silently mutate the primary checkout."""
    message_id = send_message(
        "Please review this",
        task_id="issue-4446",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        to_model=PRO_MODEL,
        quiet=True,
    )
    msg = {
        "id": message_id,
        "task_id": "issue-4446",
        "from": "claude",
        "to": "gemini",
        "type": "query",
        "content": "x",
        "data": None,
    }
    mock_invoke.return_value = _ok_result()

    with (
        patch("scripts.ai_agent_bridge._gemini._is_task_locked", return_value=False),
        patch("scripts.ai_agent_bridge._gemini._write_pid_file"),
        patch("scripts.ai_agent_bridge._gemini._remove_pid_file"),
        patch("scripts.ai_agent_bridge._gemini.atexit.register"),
    ):
        _run_gemini_sync(
            msg,
            message_id,
            PRO_MODEL,
            "bridge prompt",
            no_timeout=False,
            stdout_only=True,
            output_path=None,
            allow_write=allow_write,
            skip_github=True,
            auth_mode=None,
        )

    assert mock_invoke.call_args.kwargs["mode"] == expected_mode
    assert mock_invoke.call_args.kwargs["initiator"] == "claude"


def test_handle_ask_gemini_routes_to_agy(monkeypatch):
    captured: dict[str, object] = {}

    def _fake_ask_agy(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return SimpleNamespace(ok=True)

    monkeypatch.setattr("scripts.ai_agent_bridge._acp_compat.run_compat_ask", _fake_ask_agy)

    class _Args:
        content = "hello"
        task_id = "task-1"
        type = "query"
        data = None
        model = "gemini-3.6-flash"
        from_llm = "claude"
        from_model = None
        async_mode = False
        stdout_only = False
        output_path = None
        extract = None
        skip_model_check = False
        allow_write = False
        delimiters = None
        no_github = True
        auth = "api-key"

    _handle_ask_gemini(_Args())
    assert captured["args"] == ("gemini", "hello")
    assert captured["kwargs"]["task_id"] == "task-1"
    # #6894: legacy gemini* slugs map to the live registry pin, so assert
    # against that pin — never a literal slug that goes stale on rotation.
    assert captured["kwargs"]["model"] == registered_participant_model("agy")
    assert captured["kwargs"]["stdout_only"] is False
    assert captured["kwargs"]["output_path"] is None


def test_converse_default_model_is_none_so_registry_pin_applies() -> None:
    """#6929: a bare converse carries no independently hardcoded slug."""
    import inspect

    from scripts.ai_agent_bridge import _cli
    from scripts.ai_agent_bridge._acp_compat import resolve_compat_model
    from scripts.ai_agent_bridge._gemini import converse_gemini

    parser = _cli._build_parser()
    args = parser.parse_args(["converse", "hello", "--task-id", "t-1"])
    assert args.model is None
    assert resolve_compat_model("gemini", args.model) is None
    assert inspect.signature(converse_gemini).parameters["model"].default is None
    assert registered_participant_model("agy") is not None


def test_converse_gemini_default_tracks_pin_rotation(monkeypatch) -> None:
    """#6929: rotating the AGY pin moves converse's default with it."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    from scripts.ai_agent_bridge._gemini import converse_gemini

    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    captured: dict[str, object] = {}

    def _fake_ask_gemini(*_args, **kwargs):
        captured.update(kwargs)
        return 1

    monkeypatch.setattr("scripts.ai_agent_bridge._gemini.ask_gemini", _fake_ask_gemini)
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._gemini.get_conversation_context",
        lambda _task_id: ("", 0),
    )

    converse_gemini("hello", "t-1")
    assert captured["model"] == "gemini-9.9-flash-high"

    converse_gemini("hello", "t-1", model="gemini-3.1-pro-preview")
    assert captured["model"] == "gemini-9.9-flash-high"

    converse_gemini("hello", "t-1", model="not-a-gemini-model")
    assert captured["model"] == "not-a-gemini-model"


def test_default_gemini_model_resolves_from_registry_and_tracks_rotation(monkeypatch) -> None:
    """#6959: default_gemini_model resolves from the live ACP registry pin."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    import scripts.ai_agent_bridge as bridge
    from scripts.ai_agent_bridge._config import default_gemini_model

    monkeypatch.delenv("AB_GEMINI_MODEL", raising=False)
    assert default_gemini_model() == registered_participant_model("agy")
    assert registered_participant_model("agy") == bridge.GEMINI_DEFAULT_MODEL

    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    assert default_gemini_model() == "gemini-9.9-flash-high"
    assert bridge.GEMINI_DEFAULT_MODEL == "gemini-9.9-flash-high"


def test_default_gemini_model_respects_env_override(monkeypatch) -> None:
    """#6959: AB_GEMINI_MODEL environment override takes precedence."""
    import scripts.ai_agent_bridge as bridge
    from scripts.ai_agent_bridge._config import default_gemini_model

    monkeypatch.setenv("AB_GEMINI_MODEL", "gemini-custom-override")
    assert default_gemini_model() == "gemini-custom-override"
    assert bridge.GEMINI_DEFAULT_MODEL == "gemini-custom-override"


def test_default_gemini_model_missing_registry_pin_fails_loudly(monkeypatch) -> None:
    """#6959: missing registry pin fails loudly instead of falling back to stale literal."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    from scripts.ai_agent_bridge._config import default_gemini_model

    monkeypatch.delenv("AB_GEMINI_MODEL", raising=False)
    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": None},
    )
    with pytest.raises(RuntimeError, match="No default Gemini model configured"):
        default_gemini_model()


def test_ask_gemini_and_process_and_respond_signatures_default_to_none() -> None:
    """#6959: ask_gemini and process_and_respond signatures default model to None."""
    import inspect

    from scripts.ai_agent_bridge._gemini import ask_gemini, process_and_respond

    assert inspect.signature(ask_gemini).parameters["model"].default is None
    assert inspect.signature(process_and_respond).parameters["model"].default is None


def test_ask_gemini_resolves_registry_pin_and_tracks_rotation(monkeypatch) -> None:
    """#6959: ask_gemini resolves default from registry and remaps legacy slugs."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    from scripts.ai_agent_bridge._gemini import ask_gemini

    monkeypatch.delenv("AB_GEMINI_MODEL", raising=False)
    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        "scripts.ai_agent_bridge._gemini._send_gemini_message",
        lambda *args: 101,
    )
    monkeypatch.setattr(
        "scripts.ai_agent_bridge._gemini.process_and_respond",
        lambda _msg_id, model=None, **kwargs: captured.update(model=model) or "resp",
    )

    # 1. Bare call (model=None) resolves to rotated pin
    ask_gemini("hello", task_id="t-1")
    assert captured["model"] == "gemini-9.9-flash-high"

    # 2. Legacy slug remaps to rotated pin
    ask_gemini("hello", task_id="t-1", model="gemini-2.0-flash")
    assert captured["model"] == "gemini-9.9-flash-high"

    # 3. Non-gemini model passes through
    ask_gemini("hello", task_id="t-1", model="custom-provider/model-x")
    assert captured["model"] == "custom-provider/model-x"

    # 4. Env override takes precedence
    monkeypatch.setenv("AB_GEMINI_MODEL", "env-model-override")
    ask_gemini("hello", task_id="t-1")
    assert captured["model"] == "env-model-override"


def test_process_and_respond_resolves_registry_pin(bridge_db, monkeypatch) -> None:
    """#6959: process_and_respond resolves default model from registry."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    from scripts.ai_agent_bridge._gemini import process_and_respond

    message_id = send_message(
        "Test content",
        task_id="issue-6959",
        msg_type="query",
        from_llm="claude",
        to_llm="gemini",
        quiet=True,
    )

    monkeypatch.delenv("AB_GEMINI_MODEL", raising=False)
    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    captured: dict[str, object] = {}

    def _fake_run_sync(msg, msg_id, model, *args, **kwargs):
        captured["model"] = model
        return "response text"

    monkeypatch.setattr("scripts.ai_agent_bridge._gemini._run_gemini_sync", _fake_run_sync)

    process_and_respond(message_id)
    assert captured["model"] == "gemini-9.9-flash-high"
