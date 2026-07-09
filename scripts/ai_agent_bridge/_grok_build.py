"""Grok Build bridge integration for the native ``grok`` CLI.

This is the native Grok Build lane (registry key ``grok-build``), not the
Hermes-routed ``grok`` agent. Bridge calls use ``agent_runtime.runner.invoke``
so process management, telemetry, timeouts, and parsing stay centralized.
"""

from __future__ import annotations

import json
import os

from agent_runtime import runner as agent_runner
from agent_runtime.adapters.grok_build import (
    GROK_BUILD_DEFAULT_EFFORT,
    GROK_BUILD_DEFAULT_MODEL,
)
from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)

from ._ask_lifecycle import launch_background_ask, record_ask_failure, record_ask_reply, register_ask
from ._config import REPO_ROOT
from ._db import get_db, set_session
from ._messaging import acknowledge, send_message
from ._prompts import _prepend_review_protocol

_DEFAULT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS = 900
_NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS = 24 * 60 * 60


def _resolve_grok_build_bridge_timeout(no_timeout: bool = False) -> int:
    """Resolve Grok Build hard timeout from CLI flag/env with a safe fallback."""
    if no_timeout:
        return _NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS

    raw = os.environ.get("GROK_BUILD_BRIDGE_TIMEOUT")
    if raw is None:
        return _DEFAULT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS

    value = raw.strip().lower()
    if value in {"0", "none", "off", "false", "no"}:
        return _NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS

    try:
        timeout = int(value)
    except ValueError:
        print(
            f"Invalid GROK_BUILD_BRIDGE_TIMEOUT={raw!r}; "
            f"falling back to {_DEFAULT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS}s"
        )
        return _DEFAULT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS

    if timeout <= 0:
        return _NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS
    return timeout


def ask_grok_build(
    content: str,
    task_id: str | None = None,
    msg_type: str = "query",
    data: str | None = None,
    new_session: bool = False,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
    review: bool = False,
    model: str | None = None,
    background: bool = False,
) -> int:
    """Send message to native Grok Build and invoke it to process the message."""
    effective_model = to_model or model or GROK_BUILD_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="grok-build",
        from_model=from_model,
        to_model=effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "grok-build",
            {"new_session": new_session, "no_timeout": no_timeout, "review": review},
        )
        return msg_id
    print(f"\nInvoking grok-build ({effective_model}) to process message #{msg_id}...")
    process_for_grok_build(
        msg_id,
        new_session=new_session,
        no_timeout=no_timeout,
        review=review,
    )
    return msg_id


def process_for_grok_build(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
) -> None:
    """Read a grok-build message, invoke the native adapter, and send a reply."""
    msg = _fetch_grok_build_message(message_id)
    if not msg:
        return

    _ = new_session  # grok-build resume_policy="never"; bridge calls are fresh.
    timeout_val = _resolve_grok_build_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or GROK_BUILD_DEFAULT_MODEL
    prompt = _build_grok_build_prompt(msg, review)

    print(f"Message #{msg['id']}")
    print(f"   From: {msg['from']} -> To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print("   Session: NEW (grok-build runtime always fresh)")
    print(f"   Model: {model}")
    print(f"   Effort: {GROK_BUILD_DEFAULT_EFFORT}")
    if timeout_val == _NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS:
        print("   Hard timeout: no-timeout requested (24h ceiling)")
    else:
        print(f"   Hard timeout: {timeout_val}s")

    try:
        result = agent_runner.invoke(
            "grok-build",
            prompt,
            mode="read-only",
            cwd=REPO_ROOT,
            model=model,
            task_id=msg["task_id"],
            session_id=None,
            tool_config=None,
            entrypoint="bridge",
            hard_timeout=timeout_val,
            stall_timeout=min(600, timeout_val),
            effort=GROK_BUILD_DEFAULT_EFFORT,
        )
    except RateLimitedError as exc:
        _handle_grok_build_error(msg, message_id, f"Grok Build rate limited: {exc}")
        return
    except AgentStalledError as exc:
        _handle_grok_build_error(msg, message_id, f"Grok Build stalled: {exc}")
        return
    except AgentTimeoutError as exc:
        _handle_grok_build_error(msg, message_id, f"Grok Build hard timeout: {exc}")
        return
    except AgentUnavailableError as exc:
        _handle_grok_build_error(msg, message_id, f"Grok Build unavailable: {exc}")
        return

    if not result.ok:
        _handle_grok_build_error(
            msg,
            message_id,
            result.stderr_excerpt or "Grok Build returned no final message",
        )
        return

    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "grok-build", result.session_id)

    response = result.response
    if not response:
        _handle_grok_build_error(msg, message_id, "Grok Build returned no final message")
        return

    print(f"\nGrok Build finished ({len(response)} chars)")
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="grok-build",
        to_llm=msg["from"],
        from_model=getattr(result, "model", None) or model,
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _fetch_grok_build_message(message_id: int) -> dict | None:
    """Fetch a message addressed to native Grok Build from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'grok-build'
        """,
        (message_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Message {message_id} not found or not addressed to Grok Build")
        return None

    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7],
    }


def _extract_target_model(msg: dict) -> str | None:
    """Read optional ``to_model`` metadata written by ``send_message``."""
    data = msg.get("data")
    if not data:
        return None
    try:
        payload = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    model = payload.get("to_model")
    return str(model) if model else None


def _build_grok_build_prompt(msg: dict, review: bool = False) -> str:
    """Build the native Grok Build bridge prompt."""
    prompt = f"""You are Grok Build (native grok CLI), receiving a message from {msg['from'].title()} via the message broker.

---
Task ID: {msg['task_id'] or 'none'}
Type: {msg['type']}
From: {msg['from']}

{msg['content']}
"""
    if msg["data"]:
        prompt += f"""
---
Attached data:
{msg['data']}
"""
    prompt += """

---

Standing rules for bridge Q&A:
- Respond directly and concisely.
- Do NOT use broker or MCP messaging tools to send your response; output it directly.
- This is the native grok-build lane. Do not route through Hermes/OpenRouter.
"""
    return _prepend_review_protocol(prompt, review)


def _handle_grok_build_error(msg: dict, message_id: int, reason: str) -> None:
    """Record a Grok Build failure as a response message and acknowledge."""
    print(f"\nGrok Build error for message #{message_id}: {reason}")
    reply_id = send_message(
        content=f"[Grok Build error] {reason}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="grok-build",
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_failure(
        message_id,
        reason,
        timed_out="timeout" in reason.lower() or "stalled" in reason.lower(),
    )
