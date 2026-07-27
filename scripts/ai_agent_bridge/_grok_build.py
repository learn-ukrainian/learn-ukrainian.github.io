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
import sys
from pathlib import Path
from typing import Any

from agent_runtime import runner as agent_runner
from agent_runtime.adapters.grok_build import (
    GROK_BUILD_DEFAULT_EFFORT,
    GROK_BUILD_DEFAULT_MODEL,
    grok_session_dir,
)
from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)

from ._ask_contract import (
    MAX_TOTAL_ASK_RETRIES,
    NATIVE_ASK_TOOL_CONTRACT,
    requested_effort,
    resolve_model_selection,
    response_provenance,
)
from ._ask_lifecycle import (
    _ask_metadata,
    launch_background_ask,
    record_ask_failure,
    record_ask_reply,
    register_ask,
)
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
    effort: str | None = None,
    no_timeout: bool = False,
    review: bool = False,
    model: str | None = None,
    background: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
) -> int:
    """Send message to the native grok seat and invoke it to process the message."""
    effective_model = resolve_model_selection(
        lane="ask-grok", to_model=to_model, model=model, default=GROK_BUILD_DEFAULT_MODEL
    )
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="grok",  # prefer-WRITE canonical seat
        from_model=from_model,
        to_model=effective_model,
        effort=effort,
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

    from ._ask_lifecycle import assert_ask_content_present

    # #4915: background workers must use the DB-stored body, never empty stdin.
    assert_ask_content_present(msg, message_id=message_id, target="grok")

    _ = new_session  # grok resume_policy="never"; bridge calls are fresh.
    timeout_val = _resolve_grok_build_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or GROK_BUILD_DEFAULT_MODEL
    effort = requested_effort(msg) or GROK_BUILD_DEFAULT_EFFORT

    print(f"Message #{msg['id']}")
    print(f"   From: {msg['from']} -> To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print("   Session: NEW (grok runtime always fresh)")
    print(f"   Model: {model}")
    print(f"   Effort: {effort or GROK_BUILD_DEFAULT_EFFORT}")
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
                effort=effort,
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

    turn_status = _native_grok_turn_status(
        session_id=getattr(result, "session_id", None),
        cwd=checkout.path if checkout is not None else REPO_ROOT,
    )
    if turn_status["outcome"] != "completed":
        if (
            turn_status.get("cancellation_category") == "permission_cancelled"
            and _can_cancel_retry(msg)
        ):
            print(
                f"⚠️ Ask #{message_id}: native Grok turn ended in permission_cancelled; "
                f"auto-retrying ONCE with refusal reason appended...",
                file=sys.stderr,
            )
            if _attempt_cancel_and_retell_retry(
                msg=msg,
                message_id=message_id,
                checkout=checkout,
                model=model,
                effort=effort or GROK_BUILD_DEFAULT_EFFORT,
                timeout_val=timeout_val,
                review=review,
                turn_status=turn_status,
            ):
                return
        _handle_grok_build_incomplete_turn(
            msg,
            message_id,
            response,
            turn_status,
            actual_model=getattr(result, "model", None) or model,
            effort=effort or GROK_BUILD_DEFAULT_EFFORT,
        )
        return

    print(f"\nGrok finished ({len(response)} chars)")
    provenance_data, actual_model = response_provenance(
        msg,
        actual_model=getattr(result, "model", None) or model,
        harness="grok",
        effort_applied=getattr(result, "effort", None) or effort or GROK_BUILD_DEFAULT_EFFORT,
    )
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="grok",
        to_llm=msg["from"],
        data=provenance_data,
        from_model=actual_model,
    )
    acknowledge(message_id)
    record_ask_reply(message_id, reply_id)


def _can_cancel_retry(msg: dict) -> bool:
    """Check whether a permission_cancelled turn can be auto-retried once."""
    meta = _ask_metadata(msg)
    if meta.get("cancel_retried") or meta.get("cancel-retried"):
        return False
    total_retries = int(meta.get("total_retry_count") or 0)
    return total_retries < MAX_TOTAL_ASK_RETRIES


def _attempt_cancel_and_retell_retry(
    *,
    msg: dict,
    message_id: int,
    checkout: Any,
    model: str,
    effort: str,
    timeout_val: int,
    review: bool,
    turn_status: dict[str, str | None],
) -> bool:
    """Auto-retry ONCE with refusal reason appended to prompt (#5893 item 3)."""
    meta = _ask_metadata(msg)
    meta["cancel_retried"] = True
    current_count = int(meta.get("total_retry_count") or 0)
    meta["total_retry_count"] = current_count + 1
    msg["data"] = json.dumps(meta, sort_keys=True)

    conn = get_db()
    try:
        conn.execute(
            "UPDATE messages SET data = ? WHERE id = ?",
            (msg["data"], message_id),
        )
        conn.commit()
    finally:
        conn.close()

    cat = turn_status.get("cancellation_category") or "permission_cancelled"
    refusal_reason = (
        f"Tool call permission cancelled: shell commands are unavailable in this mode ({cat}); "
        "answer from attached material and file reads."
    )

    base_prompt = _build_grok_build_prompt(
        msg,
        review,
        review_branch=checkout.branch if checkout else None,
        review_pr_number=checkout.pr_number if checkout else None,
        review_worktree_provisioned=checkout is not None,
    )
    retry_prompt = append_review_prompt_evidence(
        f"{base_prompt}\n\n[Previous turn cancelled by permission policy]: {refusal_reason}\n",
        review=review,
        checkout=checkout,
        engine="grok",
    )
    review_tool_config = checkout.isolation_tool_config("grok") if (review and checkout) else None

    try:
        result = agent_runner.invoke(
            "grok",
            retry_prompt,
            mode="read-only",
            cwd=checkout.path if checkout is not None else REPO_ROOT,
            model=model,
            task_id=msg["task_id"],
            session_id=None,
            tool_config=review_tool_config,
            entrypoint="bridge",
            hard_timeout=timeout_val,
            stall_timeout=min(600, timeout_val),
            effort=effort,
        )
    except Exception as exc:
        _handle_grok_build_error(msg, message_id, f"Cancel-and-retell retry failed: {exc}")
        return True

    if not result.ok:
        _handle_grok_build_error(
            msg,
            message_id,
            result.stderr_excerpt or "Grok Build retry returned no final message",
        )
        return True

    response = result.response
    if not response:
        _handle_grok_build_error(msg, message_id, "Grok Build retry returned no final message")
        return True

    new_turn_status = _native_grok_turn_status(
        session_id=getattr(result, "session_id", None),
        cwd=checkout.path if checkout is not None else REPO_ROOT,
    )
    if new_turn_status["outcome"] != "completed":
        _handle_grok_build_incomplete_turn(
            msg,
            message_id,
            response,
            new_turn_status,
            actual_model=getattr(result, "model", None) or model,
            effort=effort or GROK_BUILD_DEFAULT_EFFORT,
        )
        return True

    print(f"\nGrok finished retried turn ({len(response)} chars)")
    provenance_data, actual_model = response_provenance(
        msg,
        actual_model=getattr(result, "model", None) or model,
        harness="grok",
        effort_applied=getattr(result, "effort", None) or effort or GROK_BUILD_DEFAULT_EFFORT,
    )
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="grok",
        to_llm=msg["from"],
        data=provenance_data,
        from_model=actual_model,
    )
    acknowledge(message_id)
    record_ask_reply(message_id, reply_id)
    return True


def _native_grok_turn_status(*, session_id: str | None, cwd: Path) -> dict[str, str | None]:
    """Read Grok's authoritative last terminal event, failing closed on traces."""
    if not session_id:
        return {"outcome": "trace_unavailable", "cancellation_category": None}
    grok_home = Path(os.environ.get("GROK_HOME", str(Path.home() / ".grok")))
    events_path = grok_session_dir(grok_home, cwd, session_id) / "events.jsonl"
    try:
        events = []
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                event = json.loads(line)
                if not isinstance(event, dict):
                    raise ValueError("non-object event")
                events.append(event)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"outcome": "trace_unavailable", "cancellation_category": None}
    terminal_events = [event for event in events if event.get("type") == "turn_ended"]
    if not terminal_events:
        return {"outcome": "trace_unavailable", "cancellation_category": None}
    terminal = terminal_events[-1]
    outcome = terminal.get("outcome")
    if not isinstance(outcome, str) or not outcome:
        return {"outcome": "trace_unavailable", "cancellation_category": None}
    category = terminal.get("cancellation_category")
    return {
        "outcome": outcome,
        "cancellation_category": str(category) if category is not None else None,
    }


def _handle_grok_build_incomplete_turn(
    msg: dict,
    message_id: int,
    response: str,
    turn_status: dict[str, str | None],
    *,
    actual_model: str,
    effort: str,
) -> None:
    """Deliver captured native text only as an explicitly typed failed turn."""
    outcome = str(turn_status["outcome"])
    category = turn_status.get("cancellation_category")
    detail = outcome if outcome == "trace_unavailable" else f"{outcome}/{category or 'none'}"
    banner = f"⚠️ TURN NOT COMPLETED ({detail})"
    provenance_data, _ = response_provenance(
        msg,
        actual_model=actual_model,
        harness="grok",
        effort_applied=effort,
    )
    metadata = json.loads(provenance_data)
    metadata.update(
        {
            "turn_outcome": outcome,
            "cancellation_category": category,
            "trace_status": "unavailable" if outcome == "trace_unavailable" else "terminal_failure",
            "partial_response": True,
        }
    )
    send_message(
        content=f"{banner}\n\n{response}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="grok",
        to_llm=msg["from"],
        data=json.dumps(metadata, sort_keys=True),
        from_model=actual_model,
    )
    acknowledge(message_id)
    record_ask_failure(message_id, f"native Grok turn not completed: {detail}")


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
    contract = f"{NATIVE_ASK_TOOL_CONTRACT}\n\n" if not review_worktree_provisioned else ""
    prompt = f"""{contract}You are Grok Build (native grok CLI), receiving a message from {msg['from'].title()} via the message broker.

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
    send_message(
        content=f"[Grok Build error] {reason}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="grok-build",
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    record_ask_failure(
        message_id,
        reason,
        timed_out="timeout" in reason.lower() or "stalled" in reason.lower(),
    )
