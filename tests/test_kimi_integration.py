"""Closed-registry integration coverage for the native Kimi lane."""
from __future__ import annotations

import sys
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from scripts.ai_agent_bridge import _channels, _cli, _kimi
from scripts.ai_agent_bridge._channels_cli import _cli_available_agent
from scripts.ai_agent_bridge._model import _build_kimi_probe_plan


def test_delegate_accepts_kimi_and_does_not_create_a_fallback_mapping():
    import delegate

    args = delegate.build_parser().parse_args(
        ["dispatch", "--agent", "kimi", "--task-id", "kimi-probe", "--prompt", "noop", "--dry-run"]
    )
    assert args.agent == "kimi"
    assert "kimi" not in delegate._load_dispatch_fallbacks()


def test_valid_agents_and_cli_registry_include_kimi():
    assert "kimi" in _channels.VALID_AGENTS
    assert _cli_available_agent("kimi") is True


def test_ask_kimi_parser_defaults_to_k3_and_check_model_accepts_kimi():
    parser = _cli._build_parser()
    ask = parser.parse_args(["ask-kimi", "hello", "--task-id", "kimi-ask", "--from", "codex"])
    probe = parser.parse_args(["check-model", "k3", "--agent", "kimi"])

    assert ask.model == "k3"
    assert probe.agent == "kimi"
    assert probe.model == "k3"


def test_ask_kimi_handler_routes_all_arguments(monkeypatch, tmp_path):
    payload = tmp_path / "payload.md"
    payload.write_text("attached", encoding="utf-8")
    captured: dict[str, object] = {}
    monkeypatch.setattr(_cli, "ask_kimi", lambda *args, **kwargs: captured.update(args=args, kwargs=kwargs))

    _cli._handle_ask_kimi(
        Namespace(
            content="hello", task_id="kimi-ask", type="query", data=str(payload),
            new_session=True, from_llm="codex", from_model="gpt-5.6-terra",
            to_model="k2.7-coding", no_timeout=True, review=True, model="k3",
            branch=None, pr=None, background=False,
        )
    )

    assert captured["args"] == ("hello", "kimi-ask")
    kwargs = captured["kwargs"]
    assert kwargs["data"] == "attached"
    assert kwargs["to_model"] == "k2.7-coding"
    assert kwargs["model"] == "k3"
    assert kwargs["review"] is True


def test_ask_kimi_background_records_a_kimi_target(monkeypatch):
    launches: list[tuple] = []
    monkeypatch.setattr(_kimi, "send_message", lambda *_args, **_kwargs: 41)
    monkeypatch.setattr(_kimi, "register_ask", lambda *_args: None)
    monkeypatch.setattr(_kimi, "launch_background_ask", lambda *args: launches.append(args))

    assert _kimi.ask_kimi("review", task_id="task-1", background=True) == 41
    assert launches == [(41, "kimi", {"new_session": False, "no_timeout": False, "review": False})]


def test_kimi_background_worker_routes_to_kimi_processor(monkeypatch):
    from scripts.ai_agent_bridge import _ask_lifecycle

    calls: list[tuple] = []
    monkeypatch.setattr(_kimi, "process_for_kimi", lambda *args: calls.append(args))
    _ask_lifecycle._process_target(12, "kimi", {"new_session": True, "no_timeout": True, "review": True})

    assert calls == [(12, True, True, True)]


def test_kimi_timeout_and_metadata_helpers_cover_valid_and_invalid_values(monkeypatch, capsys):
    monkeypatch.setenv("KIMI_BRIDGE_TIMEOUT", "bogus")
    assert _kimi._resolve_kimi_bridge_timeout() == 900
    assert "Invalid KIMI_BRIDGE_TIMEOUT" in capsys.readouterr().out
    monkeypatch.setenv("KIMI_BRIDGE_TIMEOUT", "0")
    assert _kimi._resolve_kimi_bridge_timeout() == 24 * 60 * 60
    assert _kimi._extract_target_model({"data": '{"to_model": "k3"}'}) == "k3"
    assert _kimi._extract_target_model({"data": "not-json"}) is None


def test_kimi_prompt_and_error_handler_include_broker_context(monkeypatch):
    message = {"task_id": "task-1", "type": "review", "from": "codex", "content": "Inspect it.", "data": "notes"}
    prompt = _kimi._build_kimi_prompt(message, review=False)
    assert "Task ID: task-1" in prompt
    assert "Attached data:\nnotes" in prompt

    sent: list[dict] = []
    monkeypatch.setattr(_kimi, "send_message", lambda **kwargs: sent.append(kwargs) or 9)
    monkeypatch.setattr(_kimi, "acknowledge", lambda *_args: None)
    monkeypatch.setattr(_kimi, "record_ask_failure", lambda *_args, **_kwargs: None)
    _kimi._handle_kimi_error(message, 7, "timeout")
    assert sent[0]["from_llm"] == "kimi"
    assert sent[0]["msg_type"] == "error"


def test_process_kimi_invokes_runtime_with_read_only_mode(monkeypatch):
    message = {
        "id": 7, "task_id": "task-1", "from": "codex", "to": "kimi", "type": "query",
        "content": "Review this.", "data": '{"to_model": "k3"}', "timestamp": "now",
    }
    calls: list[tuple] = []

    @contextmanager
    def checkout(*_args, **_kwargs):
        yield None

    monkeypatch.setattr(_kimi, "_fetch_kimi_message", lambda _id: message)
    monkeypatch.setattr(_kimi, "provision_review_worktree", checkout)
    monkeypatch.setattr(_kimi, "send_message", lambda **_kwargs: 8)
    monkeypatch.setattr(_kimi, "acknowledge", lambda *_args: None)
    monkeypatch.setattr(_kimi, "record_ask_reply", lambda *_args: None)
    monkeypatch.setattr(_kimi, "set_session", lambda *_args: None)
    monkeypatch.setattr(
        _kimi.agent_runner,
        "invoke",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or SimpleNamespace(ok=True, response="done", session_id=None, model="k3"),
    )

    _kimi.process_for_kimi(7)

    assert calls[0][0][0] == "kimi"
    assert calls[0][1]["mode"] == "read-only"
    assert calls[0][1]["model"] == "k3"


def test_fetch_kimi_message_returns_none_for_an_unaddressed_row(monkeypatch, capsys):
    connection = SimpleNamespace(execute=lambda *_args: SimpleNamespace(fetchone=lambda: None), close=lambda: None)
    monkeypatch.setattr(_kimi, "get_db", lambda: connection)

    assert _kimi._fetch_kimi_message(99) is None
    assert "not addressed to kimi" in capsys.readouterr().out


def test_check_model_refuses_read_only_native_kimi_probe():
    with pytest.raises(
        ValueError,
        match=r"kimi headless auto-approves mutations; read-only cannot be guaranteed on CLI 0.27",
    ):
        _build_kimi_probe_plan("k3")


def test_kimi_trailer_is_accepted():
    from scripts.audit.lint_agent_trailer import _TRAILER_RE

    assert _TRAILER_RE.search("X-Agent: kimi/5326-kimi-lane-onboard\n")
