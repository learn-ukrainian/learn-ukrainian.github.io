"""Regression coverage for #6915 and #6894.

#6915: the generic ``process <id>`` path must derive its route from the
message's ``To:`` seat via the live ACP participant registry (never the
retired gemini CLI, never a hardcoded recipient), and must acknowledge the
inbound message ONLY after a successful routed reply — a failed processing
attempt leaves the message unconsumed/retryable.

#6894: bridge model defaults derive from the live ACP participant registry
pin, so a bare ``ask-gemini`` can never drift stale against the agy pin.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.runner import InterAgentTransportError, resolve_inter_agent_route

from scripts.ai_agent_bridge import _process
from scripts.ai_agent_bridge._acp_compat import (
    registered_participant_model,
    require_compat_target,
    resolve_compat_model,
)
from scripts.ai_agent_bridge._db import get_db, init_db
from scripts.ai_agent_bridge._messaging import acknowledge, send_message


@pytest.fixture
def bridge_db(tmp_path, monkeypatch):
    db_path = tmp_path / "messages.db"
    monkeypatch.setattr("scripts.ai_agent_bridge._config.DB_PATH", db_path)
    monkeypatch.setattr("scripts.ai_agent_bridge._db.DB_PATH", db_path)
    conn = init_db()
    conn.close()
    return db_path


def _send(to: str, *, task_id: str = "task-6915", sender: str = "qa-engineer") -> int:
    return send_message(
        "Advisor note: please analyze.",
        task_id=task_id,
        msg_type="advisory",
        from_llm=sender,
        to_llm=to,
        quiet=True,
    )


def _row(message_id: int):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT acknowledged, status FROM messages WHERE id = ?", (message_id,)
        ).fetchone()
    finally:
        conn.close()


def _replies(message_id: int, task_id: str = "task-6915"):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT from_llm, to_llm, message_type, content FROM messages "
            "WHERE task_id = ? AND id != ? ORDER BY id ASC",
            (task_id, message_id),
        ).fetchall()
    finally:
        conn.close()


def _ok_result(response: str = "routed analysis", model: str = "registry-model"):
    return SimpleNamespace(
        ok=True, response=response, model=model, stderr_excerpt=None,
        transport_outcome="ok",
    )


# ── #6915: recipient-derived routing ────────────────────────────────────


def test_process_routes_by_recipient_seat(bridge_db, monkeypatch, capsys):
    """A message addressed to cursor is routed to the cursor ACP seat (#6915)."""
    message_id = _send("cursor")
    captured: dict[str, object] = {}

    def fake_ask(target, content, **kwargs):
        captured.update(target=target, content=content, **kwargs)
        return _ok_result()

    monkeypatch.setattr(_process, "run_compat_ask", fake_ask)

    response = _process.process_message_for_recipient(message_id)

    assert response == "routed analysis"
    assert captured["target"] == "cursor"
    assert captured["source"] == "qa-engineer"
    # No per-command model slug: the registry pin applies downstream.
    assert captured["model"] is None
    assert "Cursor" in captured["content"]

    acked, _status = _row(message_id)
    assert acked == 1
    replies = _replies(message_id)
    assert len(replies) == 1
    assert (replies[0][0], replies[0][1], replies[0][2]) == (
        "cursor",
        "qa-engineer",
        "response",
    )
    assert replies[0][3] == "routed analysis"


def test_process_gemini_recipient_resolves_to_agy_participant(bridge_db, monkeypatch):
    """Legacy gemini-addressed mail routes to the agy participant (#6915)."""
    message_id = _send("gemini")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        _process,
        "run_compat_ask",
        lambda target, content, **kwargs: captured.update(target=target, content=content, **kwargs)
        or _ok_result(),
    )

    assert _process.process_message_for_recipient(message_id) is not None
    assert captured["target"] == "gemini"
    assert require_compat_target(captured["target"]) == "agy"


def test_process_success_acks_only_after_routed_reply(bridge_db, monkeypatch):
    """Mutation check: ack must follow the routed reply, never precede it."""
    message_id = _send("kimi")
    events: list[str] = []
    monkeypatch.setattr(
        _process,
        "run_compat_ask",
        lambda *a, **k: events.append("ask") or _ok_result(),
    )
    monkeypatch.setattr(
        _process,
        "acknowledge",
        lambda *a, **k: events.append("ack"),
    )

    assert _process.process_message_for_recipient(message_id) is not None
    assert events == ["ask", "ack"]


# ── #6915: ack strictly conditional on success ──────────────────────────


def test_process_failed_result_leaves_message_unconsumed(bridge_db, monkeypatch):
    message_id = _send("cursor")
    monkeypatch.setattr(
        _process,
        "run_compat_ask",
        lambda *a, **k: SimpleNamespace(
            ok=False, response="", model="agy", stderr_excerpt="provider exploded",
            transport_outcome="error",
        ),
    )

    assert _process.process_message_for_recipient(message_id) is None
    acked, status = _row(message_id)
    assert acked == 0  # never consumed on failure
    assert status.startswith("failed:")
    # Honest typed-error reply is preserved.
    replies = _replies(message_id)
    assert len(replies) == 1
    assert replies[0][2] == "error"
    assert replies[0][1] == "qa-engineer"
    assert "NOT acknowledged" in replies[0][3]


def test_process_transport_error_leaves_message_unconsumed(bridge_db, monkeypatch):
    message_id = _send("agy")

    def boom(*a, **k):
        raise InterAgentTransportError("ACP participant 'agy' is unsupported")

    monkeypatch.setattr(_process, "run_compat_ask", boom)

    assert _process.process_message_for_recipient(message_id) is None
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")
    assert _replies(message_id)[0][2] == "error"


def test_process_empty_response_leaves_message_unconsumed(bridge_db, monkeypatch):
    message_id = _send("cursor")
    monkeypatch.setattr(
        _process,
        "run_compat_ask",
        lambda *a, **k: _ok_result(response="   "),
    )

    assert _process.process_message_for_recipient(message_id) is None
    acked, _status = _row(message_id)
    assert acked == 0


def test_process_unroutable_recipient_never_invokes(bridge_db, monkeypatch):
    """A recipient seat with no ACP route fails loudly and stays unconsumed."""
    message_id = _send("qwen")
    called = False

    def spy(*a, **k):
        nonlocal called
        called = True
        return _ok_result()

    monkeypatch.setattr(_process, "run_compat_ask", spy)

    assert _process.process_message_for_recipient(message_id) is None
    assert called is False
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")
    assert _replies(message_id)[0][2] == "error"


def test_process_already_acknowledged_message_skips(bridge_db, monkeypatch):
    message_id = _send("cursor")
    acknowledge(message_id, quiet=True)
    spy_called = False

    def spy(*a, **k):
        nonlocal spy_called
        spy_called = True
        return _ok_result()

    monkeypatch.setattr(_process, "run_compat_ask", spy)

    assert _process.process_message_for_recipient(message_id) is None
    assert spy_called is False


# ── #6894: model defaults derive from the live registry pin ─────────────


def test_ask_gemini_default_model_is_none_so_registry_pin_applies() -> None:
    """A bare ask-gemini carries no model slug; the route applies the pin."""
    from scripts.ai_agent_bridge import _cli

    parser = _cli._build_parser()
    args = parser.parse_args(["ask-gemini", "hello", "--task-id", "t-1"])
    assert args.model is None
    assert resolve_compat_model("gemini", args.model) is None
    # The route resolver then applies the live pin — and accepts it.
    route = resolve_inter_agent_route("agy")
    assert route.model == registered_participant_model("agy")


def test_resolve_compat_model_tracks_pin_rotation(monkeypatch) -> None:
    """Rotating the registry pin moves every legacy default with it (#6894)."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS, "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    assert registered_participant_model("agy") == "gemini-9.9-flash-high"
    assert resolve_compat_model("gemini", "gemini-3-flash-preview") == "gemini-9.9-flash-high"
    assert resolve_compat_model("gemini", "gemini-3.7-flash") == "gemini-9.9-flash-high"
    # Non-legacy slugs pass through for the route resolver to judge loudly.
    assert resolve_compat_model("gemini", "not-a-gemini-model") == "not-a-gemini-model"
    # Non-agy seats never get rewritten.
    assert resolve_compat_model("cursor", "composer-2") == "composer-2"


def test_converse_default_model_is_none_so_registry_pin_applies() -> None:
    """A bare converse carries no model slug; converse_gemini applies the pin."""
    import inspect

    from scripts.ai_agent_bridge import _cli
    from scripts.ai_agent_bridge._gemini import converse_gemini

    parser = _cli._build_parser()
    args = parser.parse_args(["converse", "hello", "--task-id", "t-1"])
    assert args.model is None
    assert resolve_compat_model("gemini", args.model) is None
    # Mutation-check: a restored hardcoded slug on either surface is a miss.
    assert inspect.signature(converse_gemini).parameters["model"].default is None
    route = resolve_inter_agent_route("agy")
    assert route.model == registered_participant_model("agy")


def test_converse_default_tracks_pin_rotation(monkeypatch) -> None:
    """Rotating the registry pin moves converse's default with it (#6929)."""
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    from scripts.ai_agent_bridge._gemini import converse_gemini

    monkeypatch.setitem(
        ACPX_SUPPORTED_PARTICIPANTS, "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    captured: dict[str, object] = {}

    def _fake_ask_gemini(*_a, **kwargs):
        captured.update(kwargs)
        return 1

    monkeypatch.setattr(
        "scripts.ai_agent_bridge._gemini.ask_gemini", _fake_ask_gemini
    )
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


def test_process_model_override_must_match_registry(bridge_db, monkeypatch):
    """Explicit overrides pass through to registry validation (loud mismatch)."""
    message_id = _send("cursor")
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        _process,
        "run_compat_ask",
        lambda target, content, **kwargs: captured.update(**kwargs) or _ok_result(),
    )

    assert _process.process_message_for_recipient(message_id, model="composer-2") is not None
    assert captured["model"] == "composer-2"


# ── #6915 sibling sweep: every process-* error handler is ack-free ──────


def test_legacy_gemini_error_handler_never_acks(bridge_db):
    from scripts.ai_agent_bridge import _gemini

    message_id = _send("gemini")
    _gemini._send_gemini_error(
        {"task_id": "task-6915", "from": "qa-engineer"}, message_id
    )
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")
    assert _replies(message_id)[0][2] == "error"


@pytest.mark.parametrize("seat", ["claude", "codex", "grok", "kimi", "agy"])
def test_native_error_handlers_never_ack(bridge_db, seat):
    """Mutation check: removing the no-ack guard turns every one of these red."""
    from scripts.ai_agent_bridge import _agy, _claude, _codex, _grok_build, _kimi

    message_id = _send(seat)
    msg = {
        "id": message_id,
        "task_id": "task-6915",
        "from": "qa-engineer",
        "to": seat,
        "type": "advisory",
        "content": "x",
        "data": None,
    }
    if seat == "claude":
        _claude._handle_claude_error(msg, message_id, "boom")
    elif seat == "codex":
        _codex._handle_codex_error(msg, message_id, "boom")
    elif seat == "grok":
        _grok_build._handle_grok_build_error(msg, message_id, "boom")
    elif seat == "kimi":
        _kimi._handle_kimi_error(msg, message_id, "boom")
    elif seat == "agy":
        _agy._handle_agy_error(msg, message_id, "boom")

    acked, status = _row(message_id)
    assert acked == 0, f"{seat} error handler consumed a failed message"
    assert status.startswith("failed:")
    assert _replies(message_id)[0][2] == "error"


def test_claude_fallback_error_never_acks(bridge_db):
    from scripts.ai_agent_bridge import _claude

    message_id = _send("claude")
    _claude._send_claude_fallback_error(
        {"task_id": "task-6915", "from": "qa-engineer"}, message_id
    )
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")


def test_grok_incomplete_turn_never_acks(bridge_db):
    from scripts.ai_agent_bridge import _grok_build

    message_id = _send("grok")
    msg = {
        "id": message_id, "task_id": "task-6915", "from": "qa-engineer",
        "to": "grok", "type": "advisory", "content": "x", "data": None,
    }
    _grok_build._handle_grok_build_incomplete_turn(
        msg,
        message_id,
        "partial text",
        {"outcome": "cancelled", "cancellation_category": "timeout"},
        actual_model="grok-4.6",
        effort="high",
    )
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")


def test_opencode_incomplete_turn_never_acks(bridge_db):
    from scripts.ai_agent_bridge import _opencode

    message_id = _send("glm")
    msg = {
        "id": message_id, "task_id": "task-6915", "from": "qa-engineer",
        "to": "glm", "type": "advisory", "content": "x", "data": None,
    }
    _opencode._handle_opencode_incomplete_turn(
        msg,
        message_id,
        "glm",
        "",
        SimpleNamespace(
            outcome="timeout", cancellation_category=None, reason="hard timeout"
        ),
        actual_model="glm-5.3",
        effort="high",
    )
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")


def test_process_all_gemini_counts_failures_without_consuming(bridge_db, monkeypatch, capsys):
    """Batch drain: a failed message stays in the inbox and is counted failed."""
    from scripts.ai_agent_bridge import _cli

    ok_id = _send("gemini", task_id="task-ok")
    bad_id = _send("gemini", task_id="task-bad")

    def fake_process(message_id, *, model=None):
        return "done" if message_id == ok_id else None

    monkeypatch.setattr(_cli, "process_message_for_recipient", fake_process)
    _cli.process_all_gemini()

    assert _row(bad_id)[0] == 0
    out = capsys.readouterr().out
    assert "1 succeeded, 1 failed" in out
