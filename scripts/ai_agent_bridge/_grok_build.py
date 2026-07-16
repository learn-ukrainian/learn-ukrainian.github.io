"""Native ``grok`` CLI bridge integration (canonical seat id: ``grok``).

Historical registry/bridge key was ``grok-build`` (permanent alias). Prefer
WRITE of the canonical seat ``grok``; dual-READ accepts messages addressed
to either id. Distinct from the demoted Hermes path ``grok-hermes``.
Bridge calls use ``agent_runtime.runner.invoke`` so process management,
telemetry, timeouts, and parsing stay centralized.
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
from ._review_worktree import (
    ReviewWorktreeError,
    append_review_prompt_evidence,
    provision_review_worktree,
    review_target_from_message,
    review_target_payload,
)

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
    review_branch: str | None = None,
    review_pr_number: int | None = None,
) -> int:
    """Send message to the native grok seat and invoke it to process the message."""
    effective_model = to_model or model or GROK_BUILD_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="grok",  # prefer-WRITE canonical seat
        from_model=from_model,
        to_model=effective_model,
        review_target=review_target_payload(review_branch, review_pr_number),
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "grok",
            {"new_session": new_session, "no_timeout": no_timeout, "review": review},
        )
        return msg_id
    print(f"\nInvoking grok ({effective_model}) to process message #{msg_id}...")
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
    """Read a native-grok message, invoke the adapter, and send a reply.

    Dual-READ: accepts messages addressed to ``grok`` or the permanent alias
    ``grok-build``. Prefer-WRITE replies as ``from_llm="grok"``.
    """
    msg = _fetch_grok_build_message(message_id)
    if not msg:
        return

    _ = new_session  # grok resume_policy="never"; bridge calls are fresh.
    timeout_val = _resolve_grok_build_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or GROK_BUILD_DEFAULT_MODEL

    print(f"Message #{msg['id']}")
    print(f"   From: {msg['from']} -> To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print("   Session: NEW (grok runtime always fresh)")
    print(f"   Model: {model}")
    print(f"   Effort: {GROK_BUILD_DEFAULT_EFFORT}")
    if timeout_val == _NO_TIMEOUT_GROK_BUILD_BRIDGE_TIMEOUT_SECONDS:
        print("   Hard timeout: no-timeout requested (24h ceiling)")
    else:
        print(f"   Hard timeout: {timeout_val}s")

    try:
        review_target = review_target_from_message(msg) if review else None
        with provision_review_worktree(
            review_target,
            repo_root=REPO_ROOT,
            allow_local_fallback=bool(review),
        ) as checkout:
            if review:
                if checkout is None:
                    raise ReviewWorktreeError(
                        "exact-target-required: review requires a sealed neutral "
                        "snapshot; refusing primary checkout fallback"
                    )
                review_tool_config = checkout.isolation_tool_config("grok")
            else:
                review_tool_config = None
            prompt = append_review_prompt_evidence(
                _build_grok_build_prompt(
                    msg,
                    review,
                    review_branch=checkout.branch if checkout else None,
                    review_pr_number=checkout.pr_number if checkout else None,
                    review_worktree_provisioned=checkout is not None,
                ),
                review=review,
                checkout=checkout,
                engine="grok",
            )
            result = agent_runner.invoke(
                "grok",
                prompt,
                mode="read-only",
                cwd=checkout.path if checkout is not None else REPO_ROOT,
                model=model,
                task_id=msg["task_id"],
                session_id=None,
                tool_config=review_tool_config,
                entrypoint="bridge",
                hard_timeout=timeout_val,
                stall_timeout=min(600, timeout_val),
                effort=GROK_BUILD_DEFAULT_EFFORT,
            )
            if review and checkout is not None:
                checkout.bind_review_result(result, engine="grok")
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
    except ReviewWorktreeError as exc:
        _handle_grok_build_error(msg, message_id, f"Grok Build review checkout failed: {exc}")
        return

    if not result.ok:
        _handle_grok_build_error(
            msg,
            message_id,
            result.stderr_excerpt or "Grok Build returned no final message",
        )
        return

    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "grok", result.session_id)

    response = result.response
    if not response:
        _handle_grok_build_error(msg, message_id, "Grok Build returned no final message")
        return

    print(f"\nGrok finished ({len(response)} chars)")
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="grok",
        to_llm=msg["from"],
        from_model=getattr(result, "model", None) or model,
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _fetch_grok_build_message(message_id: int) -> dict | None:
    """Fetch a message addressed to the native grok seat (or permanent alias)."""
    from agent_runtime.agent_identity import seat_read_aliases

    aliases = seat_read_aliases("grok")
    placeholders = ", ".join("?" for _ in aliases)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm IN ({placeholders})
        """,
        (message_id, *aliases),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"Message {message_id} not found or not addressed to grok")
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


def _build_grok_build_prompt(
    msg: dict,
    review: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
    review_worktree_provisioned: bool = False,
) -> str:
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
    return _prepend_review_protocol(
        prompt,
        review,
        review_branch=review_branch,
        review_pr_number=review_pr_number,
        review_worktree_provisioned=review_worktree_provisioned,
    )


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
