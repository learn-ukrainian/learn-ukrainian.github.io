from __future__ import annotations

import json
from argparse import Namespace
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

from scripts.agent_runtime.registry import get_agent_entry
from scripts.ai_agent_bridge import _cli, _grok_build
from scripts.ai_agent_bridge._review_worktree import ProvisionedReviewWorktree


def test_ask_grok_build_parser_accepts_first_class_args():
    parser = _cli._build_parser()

    args = parser.parse_args(
        [
            "ask-grok-build",
            "hello",
            "--task-id",
            "task-1",
            "--type",
            "query",
            "--data",
            "payload.md",
            "--new-session",
            "--from",
            "codex",
            "--from-model",
            "gpt-5.5",
            "--to-model",
            "grok-build",
            "--no-timeout",
            "--review",
        ]
    )

    assert args.command == "ask-grok-build"
    assert args.task_id == "task-1"
    assert args.new_session is True
    assert args.from_llm == "codex"
    assert args.from_model == "gpt-5.5"
    assert args.to_model == "grok-build"
    assert args.no_timeout is True
    assert args.review is True


def test_ask_grok_build_cli_handler_routes_to_bridge(monkeypatch, tmp_path):
    data_file = tmp_path / "payload.md"
    data_file.write_text("attached", encoding="utf-8")
    calls = []

    def fake_ask(*args, **kwargs):
        calls.append((args, kwargs))
        return 42

    monkeypatch.setattr(_cli, "ask_grok_build", fake_ask)

    _cli._handle_ask_grok_build(
        Namespace(
            content="hello",
            task_id="task-1",
            type="query",
            data=str(data_file),
            new_session=True,
            from_llm="codex",
            from_model="gpt-5.5",
            to_model="grok-build",
            no_timeout=True,
            review=True,
            model="grok-build",
        )
    )

    args, kwargs = calls[0]
    assert args[:3] == ("hello", "task-1",)
    assert kwargs["msg_type"] == "query"
    assert kwargs["data"] == "attached"
    assert kwargs["new_session"] is True
    assert kwargs["from_llm"] == "codex"
    assert kwargs["from_model"] == "gpt-5.5"
    assert kwargs["to_model"] == "grok-build"
    assert kwargs["no_timeout"] is True
    assert kwargs["review"] is True
    assert kwargs["model"] == "grok-build"


def test_process_grok_build_invokes_native_registry_key(monkeypatch):
    invoke_calls = []

    monkeypatch.setattr(
        _grok_build,
        "_fetch_grok_build_message",
        lambda _message_id: {
            "id": 7,
            "task_id": "task-1",
            "from": "codex",
            "to": "grok-build",
            "type": "query",
            "content": "answer this",
            "data": '{"to_model": "grok-build"}',
            "timestamp": "now",
        },
    )
    monkeypatch.setattr(_grok_build, "send_message", lambda *args, **kwargs: 8)
    monkeypatch.setattr(_grok_build, "acknowledge", lambda *_args: None)
    monkeypatch.setattr(_grok_build, "set_session", lambda *_args: None)

    def fake_invoke(*args, **kwargs):
        invoke_calls.append((args, kwargs))
        return SimpleNamespace(ok=True, response="native reply", session_id="sid-1", model="grok-build")

    monkeypatch.setattr(_grok_build.agent_runner, "invoke", fake_invoke)

    _grok_build.process_for_grok_build(7)

    args, kwargs = invoke_calls[0]
    assert args[0] == "grok-build"
    assert kwargs["model"] == "grok-build"
    assert kwargs["effort"] == _grok_build.GROK_BUILD_DEFAULT_EFFORT
    assert kwargs["entrypoint"] == "bridge"


def test_grok_build_branch_review_uses_provisioned_checkout(monkeypatch, tmp_path):
    checkout = ProvisionedReviewWorktree(
        path=tmp_path / "review-checkout",
        branch="feature/review",
        sha="a" * 40,
    )
    checkout.path.mkdir()
    captured: dict[str, object] = {}

    @contextmanager
    def fake_checkout(*_args, **_kwargs):
        yield checkout

    monkeypatch.setattr(
        _grok_build,
        "_fetch_grok_build_message",
        lambda _message_id: {
            "id": 9,
            "task_id": "branch-review",
            "from": "codex",
            "to": "grok-build",
            "type": "query",
            "content": "Review the branch.",
            "data": json.dumps({"review_target": {"branch": "feature/review"}}),
        },
    )
    monkeypatch.setattr(_grok_build, "provision_review_worktree", fake_checkout)
    monkeypatch.setattr(_grok_build, "send_message", lambda **_kwargs: 10)
    monkeypatch.setattr(_grok_build, "acknowledge", lambda *_args: None)
    monkeypatch.setattr(_grok_build, "record_ask_reply", lambda *_args: None)
    monkeypatch.setattr(_grok_build, "set_session", lambda *_args: None)
    monkeypatch.setattr(
        _grok_build.agent_runner,
        "invoke",
        lambda *_args, **kwargs: captured.update(kwargs)
        or SimpleNamespace(ok=True, response="reply", session_id=None, model="grok-build"),
    )

    _grok_build.process_for_grok_build(9, review=True)

    assert captured["cwd"] == checkout.path


def test_grok_build_registry_key_resolves_native_adapter():
    entry = get_agent_entry("grok-build")
    assert entry["adapter"] == "scripts.agent_runtime.adapters.grok_build:GrokBuildAdapter"
    assert entry["default_model"] == "grok-build"
    assert entry["default_effort"] == "high"


def test_grok_build_dispatch_start_telemetry_has_defaults():
    with patch(
        "scripts.agent_runtime.telemetry._resolve_cli_version",
        return_value="grok 0.0.test",
    ):
        from scripts.agent_runtime.telemetry import resolve_dispatch_start_telemetry

        telemetry = resolve_dispatch_start_telemetry(
            agent_name="grok-build",
            requested_model=None,
            requested_effort=None,
        )

    assert telemetry.model == "grok-build"
    assert telemetry.effort == "high"
