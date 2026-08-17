"""Recipient-derived message processing over the ACP participant registry.

This is the generic ``process <id>`` / ``process-all`` drain path. Routing and
model selection derive from the message's ``To:`` seat through the same ACP
compatibility layer the ask-* commands use (#6915): no per-command hardcoded
model slugs and no retired provider CLIs. The inbound message is acknowledged
only after a successful routed reply; a failed processing attempt notifies the
sender with a typed error but leaves the original message unconsumed and
retryable — the queue must never look drained when no analysis happened.
"""

from __future__ import annotations

import contextlib

from ._acp_compat import require_compat_target, resolve_compat_model, run_compat_ask
from ._ask_lifecycle import ask_target_model, record_ask_failure, record_ask_reply
from ._db import get_db
from ._messaging import acknowledge, read_message, send_message

_NO_TIMEOUT_CEILING_S = 86400


def recipient_has_acp_route(recipient: str) -> bool:
    """Return True when a broker recipient seat resolves to an ACP participant."""
    try:
        require_compat_target(recipient.strip().lower())
    except (ValueError, AttributeError):
        return False
    return True


def _message_acknowledged(message_id: int) -> bool:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT acknowledged FROM messages WHERE id = ?", (message_id,)
        ).fetchone()
        return bool(row and row[0])
    finally:
        conn.close()


def _build_routed_prompt(msg: dict) -> str:
    """Construct the recipient-seat prompt for a drained broker message."""
    prompt = (
        f"You are {str(msg['to']).title()}, receiving a message from "
        f"{str(msg['from']).title()} via the message broker.\n\n"
        f"---\nTask ID: {msg['task_id'] or 'none'}\nType: {msg['type']}\n"
        f"From: {msg['from']}\n\n{msg['content']}\n"
    )
    if msg.get("data"):
        prompt += f"\n---\nAttached data:\n{msg['data']}\n"
    prompt += (
        "\n---\n\nStanding rules for bridge Q&A:\n"
        "- Respond directly and concisely.\n"
        "- Do NOT use broker or MCP messaging tools to send your response; "
        "output it directly.\n"
    )
    return prompt


def _notify_processing_failure(
    msg: dict, message_id: int, participant: str, reason: str
) -> None:
    """Notify the sender of a failed processing attempt WITHOUT consuming.

    The honest typed-error reply is preserved, but the original message is
    never acknowledged here: it must remain unconsumed/retryable (#6915).
    """
    with contextlib.suppress(Exception):
        send_message(
            content=(
                f"[Bridge Error] Processing message #{message_id} via "
                f"{participant} failed: {reason}. The original message was "
                "NOT acknowledged and remains in the recipient's inbox."
            ),
            task_id=msg.get("task_id"),
            msg_type="error",
            from_llm=str(msg.get("to") or "bridge"),
            to_llm=str(msg.get("from") or "user"),
            from_model=f"{participant}-bridge-error",
        )
    record_ask_failure(message_id, reason)


def process_message_for_recipient(
    message_id: int,
    *,
    model: str | None = None,
    no_timeout: bool = False,
) -> str | None:
    """Process one broker message via the route its ``To:`` seat registers.

    Returns the routed seat's response on success (after replying to the
    sender and acknowledging the inbound message); returns None on any
    failure, leaving the message unacknowledged and retryable.
    """
    msg = read_message(message_id)
    if not msg:
        return None
    if _message_acknowledged(message_id):
        print(f"⏭️  Message {message_id} is already acknowledged; skipping.")
        return None

    recipient = str(msg.get("to") or "").strip().lower()
    try:
        participant = require_compat_target(recipient)
    except ValueError:
        reason = f"recipient seat {recipient!r} has no enabled ACP route"
        print(f"❌ {reason}; message left unconsumed")
        _notify_processing_failure(msg, message_id, recipient or "unknown", reason)
        return None

    selected_model = resolve_compat_model(recipient, model or ask_target_model(msg))
    task_id = msg.get("task_id") or f"process-{message_id}"
    print(
        f"🤖 Routing message #{message_id} to ACP participant "
        f"{participant!r} (recipient seat {recipient!r}, "
        f"model={selected_model or 'registry pin'})..."
    )
    try:
        result = run_compat_ask(
            recipient,
            _build_routed_prompt(msg),
            task_id=task_id,
            source=msg.get("from"),
            model=selected_model,
            hard_timeout=_NO_TIMEOUT_CEILING_S if no_timeout else None,
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        print(f"❌ Processing failed: {reason}")
        _notify_processing_failure(msg, message_id, participant, reason)
        return None

    response = str(getattr(result, "response", "") or "").strip()
    if not getattr(result, "ok", False) or not response:
        reason = str(
            getattr(result, "stderr_excerpt", None)
            or "empty response from routed seat"
        )
        print(f"❌ Processing failed: {reason}")
        _notify_processing_failure(msg, message_id, participant, reason)
        return None

    reply_id = send_message(
        content=response,
        task_id=msg.get("task_id"),
        msg_type="response",
        from_llm=msg["to"],
        to_llm=msg["from"],
        from_model=getattr(result, "model", None),
    )
    acknowledge(message_id)
    record_ask_reply(message_id, reply_id)
    print(f"✅ Message {message_id} processed by {participant} and acknowledged")
    return response
