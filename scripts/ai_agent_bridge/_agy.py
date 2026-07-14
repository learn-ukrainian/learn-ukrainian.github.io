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
import tempfile
from pathlib import Path

from agent_runtime import runner as agent_runner
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
from ._prompts import build_agy_prompt
from ._review_worktree import (
    ReviewWorktreeError,
    provision_review_worktree,
    review_target_from_message,
    review_target_payload,
)

_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS = 900
_NO_TIMEOUT_AGY_BRIDGE_TIMEOUT_SECONDS = 24 * 60 * 60
_DEFAULT_AGY_MODEL = "gemini-3.5-flash-high"


def _agy_ask_scratch_cwd() -> Path:
    """Out-of-tree scratch cwd for unsandboxed agy bridge asks.

    Must live OUTSIDE the repository tree: the runner's worktree containment
    guard (#4444) refuses write-capable spawns from the protected primary
    checkout, and any in-tree path classifies against it. Out-of-tree cwds
    are isolated by definition and skip the git classify entirely.
    """
    scratch = Path(tempfile.gettempdir()) / "learn-ukrainian-bridge-asks" / "agy"
    scratch.mkdir(parents=True, exist_ok=True)
    return scratch


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
        print(f"⚠️  Invalid AGY_BRIDGE_TIMEOUT={raw!r} — falling back to {_DEFAULT_AGY_BRIDGE_TIMEOUT_SECONDS}s")
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
    stdout_only: bool = False,
    output_path: str | None = None,
    background: bool = False,
    review_branch: str | None = None,
    review_pr_number: int | None = None,
):
    """Send message to Agy AND invoke Agy to process it (one-shot)."""
    if background and (stdout_only or output_path):
        raise ValueError("ask-agy --background cannot be combined with --stdout-only or --output-path")
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="agy",
        from_model=from_model,
        to_model=to_model,
        review_target=review_target_payload(review_branch, review_pr_number),
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(
            msg_id,
            "agy",
            {"new_session": new_session, "no_timeout": no_timeout, "review": review},
        )
        return msg_id
    if not stdout_only:
        print(f"\n🚀 Invoking Agy to process message #{msg_id}...")
    response = process_for_agy(
        msg_id,
        new_session,
        no_timeout,
        review=review,
        stdout_only=stdout_only,
        output_path=output_path,
    )
    if stdout_only and response:
        print(response)
    return msg_id


def process_for_agy(
    message_id: int,
    new_session: bool = False,
    no_timeout: bool = False,
    review: bool = False,
    stdout_only: bool = False,
    output_path: str | None = None,
) -> str | None:
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

    review_target = review_target_from_message(msg) if review else None

    if not stdout_only:
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
        with provision_review_worktree(review_target, repo_root=REPO_ROOT) as checkout:
            prompt = build_agy_prompt(
                msg,
                review,
                review_branch=checkout.branch if checkout else None,
                review_pr_number=checkout.pr_number if checkout else None,
                review_worktree_provisioned=checkout is not None,
            )
            result = agent_runner.invoke(
                "agy",
                prompt,
                # AGY's only sandbox switch is the opt-in ``--sandbox`` flag;
                # there is no ``--no-sandbox`` counterpart. Bridge Q&A must run
                # without that sandbox so it can read the named review checkout.
                mode="danger",
                # Keep AGY in its out-of-tree scratch cwd. The runner rejects a
                # danger-mode spawn inside the protected primary checkout; the
                # branch-pinned worktree is granted only through ``--add-dir``.
                cwd=_agy_ask_scratch_cwd(),
                model=model,
                task_id=msg["task_id"],
                session_id=None,
                tool_config={
                    "bridge_repo_read": True,
                    "repo_read_root": str(checkout.path if checkout else REPO_ROOT),
                },
                entrypoint="bridge",
                hard_timeout=timeout_val,
                stall_timeout=min(600, timeout_val),
            )
    except ReviewWorktreeError as exc:
        _handle_agy_error(msg, message_id, f"Agy review checkout failed: {exc}")
        return None
    except RateLimitedError as exc:
        _handle_agy_error(msg, message_id, f"Agy rate limited: {exc}")
        return None
    except AgentStalledError as exc:
        _handle_agy_error(msg, message_id, f"Agy stalled: {exc}")
        return None
    except AgentTimeoutError as exc:
        _handle_agy_error(msg, message_id, f"Agy hard timeout: {exc}")
        return None
    except AgentUnavailableError as exc:
        _handle_agy_error(msg, message_id, f"Agy unavailable: {exc}")
        return None

    if not result.ok:
        _handle_agy_error(
            msg,
            message_id,
            result.stderr_excerpt or "Agy returned no final message",
        )
        return None

    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "agy", result.session_id)

    response = result.response
    if not response:
        _handle_agy_error(msg, message_id, "Agy returned no final message")
        return None

    if output_path:
        from pathlib import Path

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(response, encoding="utf-8")

    if not stdout_only:
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
    record_ask_reply(message_id, reply_id)
    return response


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
    record_ask_failure(
        message_id,
        reason,
        timed_out="timeout" in reason.lower() or "stalled" in reason.lower(),
    )
