"""Cursor adapter for ai_agent_bridge ask-cursor subcommand.

Exposes ad-hoc one-shot Cursor Agent calls. Useful for Q&A, discussions,
and single-shot reads through Cursor's Composer or other models.

Invocation pattern:
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-cursor <content> \
      --task-id <task> [--model composer-2.5] [--data FILE]

Default model is ``auto`` so cursor-agent picks the best available model from
the user's plan without burning the per-model composer-2.5 quota. Pass
``--model composer-2.5`` explicitly only when you specifically need that model
(e.g. judge-calibration runs or A/B comparisons).

Under the hood: agent -p PROMPT --model MODEL --output-format text --trust
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._ask_lifecycle import (
    ask_attachment,
    ask_sender_model,
    ask_target_model,
    fetch_ask_message,
    launch_background_ask,
    record_ask_reply,
    register_ask,
)
from ._messaging import acknowledge, send_message

CURSOR_DEFAULT_MODEL = "auto"
CURSOR_DEFAULT_TIMEOUT_S = 900


def ask_cursor(
    content: str,
    task_id: str,
    msg_type: str = "query",
    data: str | None = None,
    model: str | None = None,
    from_llm: str = "claude",
    from_model: str | None = None,
    to_model: str | None = None,
    no_timeout: bool = False,
    background: bool = False,
) -> int:
    """Send message to Cursor Agent AND invoke Cursor one-shot to process it."""
    effective_model = model or CURSOR_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="cursor",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "cursor", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking cursor ({effective_model}) to process message #{msg_id}...")
    response = _invoke_cursor(content, effective_model, data=data, no_timeout=no_timeout)
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="cursor",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def process_for_cursor(message_id: int, *, no_timeout: bool = False) -> None:
    """Process an existing Cursor ask, shared by sync and detached paths."""
    msg = fetch_ask_message(message_id, "cursor")
    if not msg:
        return
    model = ask_target_model(msg) or CURSOR_DEFAULT_MODEL
    response = _invoke_cursor(msg["content"], model, data=ask_attachment(msg), no_timeout=no_timeout)
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="cursor",
        to_llm=msg["from"],
        to_model=ask_sender_model(msg),
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _invoke_cursor(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
) -> str:
    """Run agent -p PROMPT --model MODEL --output-format text --trust; return captured stdout."""
    agent_bin = shutil.which("agent")
    if not agent_bin:
        # Fallback to cursor-agent if 'agent' is not found
        agent_bin = shutil.which("cursor-agent")

    if not agent_bin:
        raise SystemExit("ask-cursor: cursor-agent CLI not found in PATH")

    # If data file attached, prepend its content to the prompt under a fenced block.
    # Cursor agent doesn't have a direct --file flag for one-shot prompts that
    # behaves exactly like opencode's. Prepending to prompt is the safest pattern.
    prompt = content
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-cursor: --data file does not exist: {data}")
        attached = data_path.read_text(encoding="utf-8", errors="replace")
        prompt = f"{content}\n\n## Attached data: {data_path.name}\n\n```\n{attached}\n```"

    argv = [
        agent_bin,
        "-p", prompt,
        "--model", model,
        "--output-format", "text",
        "--trust"
    ]

    timeout = None if no_timeout else CURSOR_DEFAULT_TIMEOUT_S
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-cursor: cursor-agent timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-cursor: cursor-agent exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    return result.stdout.strip()
