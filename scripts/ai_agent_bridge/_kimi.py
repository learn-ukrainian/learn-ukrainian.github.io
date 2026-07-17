"""Native Kimi Code bridge integration for one-shot asks and reviews."""
from __future__ import annotations

import json
import os

from agent_runtime import runner as agent_runner
from agent_runtime.adapters.kimi import KIMI_BRIDGE_DEFAULT_MODEL
from agent_runtime.errors import AgentStalledError, AgentTimeoutError, AgentUnavailableError, RateLimitedError

from ._ask_lifecycle import launch_background_ask, record_ask_failure, record_ask_reply, register_ask
from ._config import REPO_ROOT
from ._db import get_db, set_session
from ._messaging import acknowledge, send_message
from ._prompts import _prepend_review_protocol
from ._review_worktree import (
    ReviewWorktreeError,
    provision_review_worktree,
    review_target_from_message,
    review_target_payload,
)

_DEFAULT_TIMEOUT = 900
_NO_TIMEOUT = 24 * 60 * 60


def _resolve_kimi_bridge_timeout(no_timeout: bool = False) -> int:
    """Resolve Kimi's hard timeout while retaining a finite safety ceiling."""
    if no_timeout:
        return _NO_TIMEOUT
    raw = os.environ.get("KIMI_BRIDGE_TIMEOUT")
    if raw is None:
        return _DEFAULT_TIMEOUT
    try:
        value = int(raw)
    except ValueError:
        print(f"Invalid KIMI_BRIDGE_TIMEOUT={raw!r}; falling back to {_DEFAULT_TIMEOUT}s")
        return _DEFAULT_TIMEOUT
    return _NO_TIMEOUT if value <= 0 else value


def ask_kimi(
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
    """Send a broker message and invoke the native Kimi CLI to answer it."""
    effective_model = to_model or model or KIMI_BRIDGE_DEFAULT_MODEL
    message_id = send_message(
        content, task_id, msg_type, data, from_llm=from_llm, to_llm="kimi",
        from_model=from_model, to_model=effective_model,
        review_target=review_target_payload(review_branch, review_pr_number),
    )
    register_ask(message_id)
    if background:
        launch_background_ask(
            message_id, "kimi",
            {"new_session": new_session, "no_timeout": no_timeout, "review": review},
        )
        return message_id
    print(f"\nInvoking kimi ({effective_model}) to process message #{message_id}...")
    process_for_kimi(message_id, new_session, no_timeout, review)
    return message_id


def process_for_kimi(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
) -> None:
    """Process a Kimi-targeted message through the always-fresh runtime lane."""
    msg = _fetch_kimi_message(message_id)
    if not msg:
        return
    _ = new_session  # v1 registry policy is resume_policy="never".
    timeout = _resolve_kimi_bridge_timeout(no_timeout)
    model = _extract_target_model(msg) or KIMI_BRIDGE_DEFAULT_MODEL
    try:
        review_target = review_target_from_message(msg) if review else None
        with provision_review_worktree(review_target, repo_root=REPO_ROOT) as checkout:
            result = agent_runner.invoke(
                "kimi",
                _build_kimi_prompt(
                    msg, review=review,
                    review_branch=checkout.branch if checkout else None,
                    review_pr_number=checkout.pr_number if checkout else None,
                    review_worktree_provisioned=checkout is not None,
                ),
                mode="read-only", cwd=checkout.path if checkout else REPO_ROOT,
                model=model, task_id=msg["task_id"], session_id=None, tool_config=None,
                entrypoint="bridge", hard_timeout=timeout, stall_timeout=min(600, timeout),
            )
    except (RateLimitedError, AgentStalledError, AgentTimeoutError, AgentUnavailableError, ReviewWorktreeError) as exc:
        _handle_kimi_error(msg, message_id, f"Kimi unavailable: {exc}")
        return
    if not result.ok or not result.response:
        _handle_kimi_error(msg, message_id, result.stderr_excerpt or "Kimi returned no final message")
        return
    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "kimi", result.session_id)
    reply_id = send_message(
        content=result.response, task_id=msg["task_id"], msg_type="response",
        from_llm="kimi", to_llm=msg["from"],
        from_model=getattr(result, "model", None) or model,
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _fetch_kimi_message(message_id: int) -> dict | None:
    """Fetch exactly one message addressed to the Kimi lane."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp "
            "FROM messages WHERE id = ? AND to_llm = 'kimi'", (message_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        print(f"Message {message_id} not found or not addressed to kimi")
        return None
    return {"id": row[0], "task_id": row[1], "from": row[2], "to": row[3], "type": row[4], "content": row[5], "data": row[6], "timestamp": row[7]}


def _extract_target_model(msg: dict) -> str | None:
    """Recover the selected short model name stored in message metadata."""
    try:
        data = json.loads(msg.get("data") or "{}")
    except (json.JSONDecodeError, TypeError):
        return None
    model = data.get("to_model") if isinstance(data, dict) else None
    return str(model) if model else None


def _build_kimi_prompt(
    msg: dict, *, review: bool = False, review_branch: str | None = None,
    review_pr_number: int | None = None, review_worktree_provisioned: bool = False,
) -> str:
    """Construct the native Kimi prompt and optionally prepend review rules."""
    prompt = (
        "You are Kimi Code, receiving a message through the project broker.\n\n"
        f"Task ID: {msg['task_id'] or 'none'}\nType: {msg['type']}\nFrom: {msg['from']}\n\n{msg['content']}\n"
    )
    if msg.get("data"):
        prompt += f"\nAttached data:\n{msg['data']}\n"
    prompt += "\nRespond directly. Do not send broker messages; output the final response.\n"
    return _prepend_review_protocol(
        prompt, review, review_branch=review_branch, review_pr_number=review_pr_number,
        review_worktree_provisioned=review_worktree_provisioned,
    )


def _handle_kimi_error(msg: dict, message_id: int, reason: str) -> None:
    """Persist a terminal Kimi failure and unblock the original ask."""
    reply_id = send_message(
        content=f"[Kimi error] {reason}", task_id=msg["task_id"], msg_type="error",
        from_llm="kimi", to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_failure(message_id, reason, timed_out="timeout" in reason.lower() or "stalled" in reason.lower())
