"""Agy (Antigravity CLI) interaction: ask_agy and process_for_agy.

Mirrors the codex bridge shape (one-shot send + runtime invoke + response
write-back via the broker). Agy is the Gemini-3.5-Flash-High Antigravity
CLI; docs at https://antigravity.google/docs/cli-overview. Agy is used
for cheap, fast Q&A and short coordination — NOT long-running task
execution. Long-running V7 writer-phase work goes through
``delegate.py dispatch --agent agy`` instead.
"""

import json
import os

from agent_runtime import runner as agent_runner
from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)

from ._config import REPO_ROOT
from ._db import get_db, set_session
from ._messaging import acknowledge, send_message
from ._prompts import build_agy_prompt

_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS = 900
_NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS = 24 * 60 * 60
_DEFAULT_AGY_MODEL = "gemini-3.5-flash-high"


def _resolve_agy_bridge_timeout(no_timeout: bool = False) -> int:
    """Resolve Agy hard timeout from CLI flag/env with a safe fallback.

    ``agent_runtime.runner.invoke()`` requires an integer hard timeout, so
    "no timeout" mode maps to a 24h ceiling rather than ``None``.
    """
    if no_timeout:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS

    raw = os.environ.get("AGY_BRIDGE_TIMEOUT")
    if raw is None:
        return _DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS

    value = raw.strip().lower()
    if value in {"0", "none", "off", "false", "no"}:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS

    try:
        timeout = int(value)
    except ValueError:
        print(
            f"⚠️  Invalid AGY_BRIDGE_TIMEOUT={raw!r} "
            f"— falling back to {_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS}s"
        )
        return _DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS

    if timeout <= 0:
        return _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS
    return timeout


def ask_agy(
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
):
    """Send message to Agy AND invoke Agy to process it (one-shot)."""
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="agy",
        from_model=from_model,
        to_model=to_model,
    )
    print(f"\n🚀 Invoking Agy to process message #{msg_id}...")
    process_for_agy(msg_id, new_session, no_timeout, review=review)
    return msg_id


def process_for_agy(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
):
    """Read message addressed to Agy, invoke via agent_runtime, send response.

    ``new_session`` is accepted for API parity with the codex bridge but
    is currently a no-op for Agy — the runtime starts a fresh ``agy -p``
    process per invocation. A future revision could pass
    ``--conversation=<session_id>`` to resume a prior turn; today the
    bridge is single-shot.
    """
    msg = _fetch_agy_message(message_id)
    if not msg:
        return

    _ = new_session  # No-op for now; Agy bridge calls are always fresh.
    timeout_val = _resolve_agy_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or _DEFAULT_AGY_MODEL

    prompt = build_agy_prompt(msg, review)

    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print(f"   Model: {model}")
    if timeout_val == _NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS:
        print("   Hard timeout: no-timeout requested (24h ceiling)")
    else:
        print(f"   Hard timeout: {timeout_val}s")

    try:
        result = agent_runner.invoke(
            "agy",
            prompt,
            mode="read-only",  # Bridge Q&A is read-only by default.
            cwd=REPO_ROOT,
            model=model,
            task_id=msg["task_id"],
            session_id=None,
            tool_config=None,
            entrypoint="bridge",
            hard_timeout=timeout_val,
            stall_timeout=min(600, timeout_val),
        )
    except RateLimitedError as exc:
        _handle_agy_error(msg, message_id, f"Agy rate limited: {exc}")
        return
    except AgentStalledError as exc:
        _handle_agy_error(msg, message_id, f"Agy stalled: {exc}")
        return
    except AgentTimeoutError as exc:
        _handle_agy_error(msg, message_id, f"Agy hard timeout: {exc}")
        return
    except AgentUnavailableError as exc:
        _handle_agy_error(msg, message_id, f"Agy unavailable: {exc}")
        return

    if not result.ok:
        _handle_agy_error(
            msg,
            message_id,
            result.stderr_excerpt or "Agy returned no final message",
        )
        return

    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "agy", result.session_id)

    response = result.response
    if not response:
        _handle_agy_error(msg, message_id, "Agy returned no final message")
        return

    print(f"\n✅ Agy finished ({len(response)} chars)")
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="agy",
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)


def _fetch_agy_message(message_id: int) -> dict | None:
    """Fetch a message addressed to Agy from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'agy'
        """,
        (message_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found or not addressed to Agy")
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
    """Read optional ``to_model`` from the message's ``data`` JSON blob.

    ``send_message`` serializes ``--to-model`` into the ``data`` JSON column
    (NOT a dedicated ``to_model`` column — that column never existed in the
    ``messages`` schema, which is why the old PRAGMA-based lookup always
    returned None and every invocation silently fell back to flash). The
    adapter's ``_resolve_model_flag`` maps the returned slug
    (e.g. ``gemini-3.1-pro-high``) or display label to agy's ``--model``.
    Ported from kubedojo's fixed bridge. Returns None when absent.
    """
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


def _handle_agy_error(msg: dict, message_id: int, reason: str) -> None:
    """Record an Agy failure as a response message and acknowledge."""
    print(f"\n❌ Agy error for message #{message_id}: {reason}")
    reply_id = send_message(
        content=f"[Agy error] {reason}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="agy",
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)
