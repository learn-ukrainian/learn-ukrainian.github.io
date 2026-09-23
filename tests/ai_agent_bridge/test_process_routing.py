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
        return conn.execute("SELECT acknowledged, status FROM messages WHERE id = ?", (message_id,)).fetchone()
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
        ok=True,
        response=response,
        model=model,
        stderr_excerpt=None,
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
        lambda target, content, **kwargs: captured.update(target=target, content=content, **kwargs) or _ok_result(),
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
            ok=False,
            response="",
            model="agy",
            stderr_excerpt="provider exploded",
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
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
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
        ACPX_SUPPORTED_PARTICIPANTS,
        "agy",
        {"seat": "acpx-agy-shadow", "agent": "agy", "model": "gemini-9.9-flash-high"},
    )
    captured: dict[str, object] = {}

    def _fake_ask_gemini(*_a, **kwargs):
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


def test_ask_gemini_preserves_env_model_override_through_process_and_respond(bridge_db, monkeypatch) -> None:
    """#6959: AB_GEMINI_MODEL override survives through ask_gemini -> process_and_respond -> _run_gemini_sync."""
    from scripts.ai_agent_bridge._gemini import ask_gemini

    monkeypatch.setenv("AB_GEMINI_MODEL", "gemini-3.1-pro-high")
    captured: dict[str, object] = {}

    def _fake_run_sync(msg, msg_id, model, *args, **kwargs):
        captured["model"] = model
        return "response text"

    monkeypatch.setattr("scripts.ai_agent_bridge._gemini._run_gemini_sync", _fake_run_sync)

    ask_gemini("hello", task_id="issue-6959")
    assert captured["model"] == "gemini-3.1-pro-high"


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
    _gemini._send_gemini_error({"task_id": "task-6915", "from": "qa-engineer"}, message_id)
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
    _claude._send_claude_fallback_error({"task_id": "task-6915", "from": "qa-engineer"}, message_id)
    acked, status = _row(message_id)
    assert acked == 0
    assert status.startswith("failed:")


def test_grok_incomplete_turn_never_acks(bridge_db):
    from scripts.ai_agent_bridge import _grok_build

    message_id = _send("grok")
    msg = {
        "id": message_id,
        "task_id": "task-6915",
        "from": "qa-engineer",
        "to": "grok",
        "type": "advisory",
        "content": "x",
        "data": None,
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
        "id": message_id,
        "task_id": "task-6915",
        "from": "qa-engineer",
        "to": "glm",
        "type": "advisory",
        "content": "x",
        "data": None,
    }
    _opencode._handle_opencode_incomplete_turn(
        msg,
        message_id,
        "glm",
        "",
        SimpleNamespace(outcome="timeout", cancellation_category=None, reason="hard timeout"),
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


@pytest.fixture
def forbid_legacy_processors(monkeypatch):
    from unittest.mock import Mock

    for module, name in [
        ("_claude", "process_for_claude"), ("_codex", "process_for_codex"),
        ("_agy", "process_for_agy"), ("_grok_build", "process_for_grok_build"),
        ("_kimi", "process_for_kimi"), ("_hermes", "process_for_hermes"),
        ("_opencode", "process_for_opencode"),
    ]:
        monkeypatch.setattr(
            f"scripts.ai_agent_bridge.{module}.{name}",
            Mock(side_effect=AssertionError("ordinary ask reached legacy provider processor")),
        )


@pytest.mark.parametrize("command", [
    "process-claude", "process-codex", "process-grok", "process-grok-build", "process-kimi",
])
def test_ordinary_seat_process_commands_use_acp(bridge_db, monkeypatch, command, forbid_legacy_processors):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _cli

    target = command.removeprefix("process-")
    message_id = _send(target, sender="agy")
    acp = Mock(return_value=_ok_result())
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    _cli._dispatch_command(_cli._build_parser().parse_args([command, str(message_id)]))

    acp.assert_called_once()
    assert acp.call_args.args[0] == target
    assert acp.call_args.kwargs["source"] == "agy"
    assert _row(message_id)[0] == 1


@pytest.mark.parametrize("target", ["claude", "codex", "agy", "grok", "kimi", "pool", "glm", "hermes"])
def test_detached_ordinary_worker_uses_acp_without_provider_fallback(bridge_db, monkeypatch, target, forbid_legacy_processors):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _ask_lifecycle

    message_id = _send(target, sender="agy" if target != "agy" else "codex")
    acp = Mock(side_effect=RuntimeError("ACP unavailable"))
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    _ask_lifecycle._process_target(message_id, target, {"no_timeout": True})

    acp.assert_called_once()
    assert acp.call_args.kwargs["hard_timeout"] == 86400
    assert _row(message_id)[0] == 0
    assert _row(message_id)[1].startswith("failed:")
    assert len(_replies(message_id)) == 1
    assert _replies(message_id)[0][2] == "error"


@pytest.mark.parametrize("review_intent", ["flag", "type", "target"])
def test_queued_review_keeps_toolful_processor(bridge_db, monkeypatch, review_intent):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _ask_lifecycle, _claude

    message_id = send_message(
        "Review the exact branch head.", task_id="review-6106",
        from_llm="codex", to_llm="claude", quiet=True,
        msg_type="review" if review_intent == "type" else "query",
        review_target={"pr": 6106} if review_intent == "target" else None,
    )
    native = Mock()
    acp = Mock(side_effect=AssertionError("review must not enter ACP"))
    monkeypatch.setattr(_claude, "process_for_claude", native)
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    _ask_lifecycle._process_target(message_id, "claude", {"review": review_intent == "flag"})

    native.assert_called_once_with(message_id, False, no_timeout=False, review=True)
    acp.assert_not_called()


def test_queued_ask_preserves_effort_and_model(bridge_db, monkeypatch):
    from unittest.mock import Mock

    message_id = send_message(
        "State transfer.", task_id="task-6106", from_llm="claude", to_llm="codex",
        to_model="registry-model", effort="high", quiet=True,
    )
    acp = Mock(return_value=_ok_result())
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    assert _process.process_message_for_recipient(message_id)
    assert acp.call_args.kwargs["effort"] == "high"
    assert acp.call_args.kwargs["model"] == "registry-model"


@pytest.mark.parametrize("target", ["claude", "codex"])
def test_batch_ordinary_drains_use_acp_and_report_failures(bridge_db, monkeypatch, capsys, target, forbid_legacy_processors):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _cli, _codex

    message_id = _send(target, sender="agy")
    acp = Mock(return_value=_ok_result(response=""))
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    batch = _cli.process_all_claude if target == "claude" else _codex.process_all_codex
    batch()
    acp.assert_called_once()
    assert _row(message_id)[0] == 0
    assert "0 succeeded, 1 failed" in capsys.readouterr().out


def test_ordinary_process_failure_is_nonzero(bridge_db, monkeypatch):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _cli

    message_id = _send("codex", sender="agy")
    monkeypatch.setattr(_process, "run_compat_ask", Mock(return_value=_ok_result(response="")))
    args = _cli._build_parser().parse_args(["process-codex", str(message_id)])
    with pytest.raises(SystemExit, match="message left unconsumed"):
        _cli._dispatch_command(args)
    assert _row(message_id)[0] == 0


def test_ordinary_async_process_refuses_before_acp(bridge_db, monkeypatch):
    from unittest.mock import Mock

    from scripts.ai_agent_bridge import _cli

    message_id = _send("claude", sender="agy")
    acp = Mock(side_effect=AssertionError("async must fail before provider execution"))
    monkeypatch.setattr(_process, "run_compat_ask", acp)
    args = _cli._build_parser().parse_args(["process-claude", str(message_id), "--async"])
    with pytest.raises(ValueError, match="enqueue through fleet-comms"):
        _cli._dispatch_command(args)
    acp.assert_not_called()
    assert _row(message_id)[0] == 0
