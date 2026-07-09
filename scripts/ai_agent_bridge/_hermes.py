"""Hermes adapter for ai_agent_bridge ask-hermes subcommand.

Mirrors ask-codex / ask-gemini pattern. Hermes is the underlying runtime for
several already-supported model adapters (hermes_grok, hermes_deepseek,
hermes_qwen). This bridge subcommand exposes ad-hoc one-shot Hermes calls
with arbitrary models so cross-model adversarial reviews can route through
hermes the same way they route through codex/gemini.

Invocation pattern:
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-hermes <content> \\
      --task-id <task> --model deepseek-v4-flash

Under the hood: hermes -z "<content>" -m <model>
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
from .routing_guard import assert_model_routing_allowed

# deepseek-flash is the dominant real usage of this lane (off-seat code review,
# "dirt cheap" API). The previous default (qwen/qwen3.6-plus) violated the
# standing qwen exclusion — every bare ask-hermes silently burned the banned
# model (deepseek review 2026-07-05, PR #4473 finding 1).
HERMES_DEFAULT_MODEL = "deepseek-v4-flash"
HERMES_DEFAULT_TIMEOUT_S = 900  # 15 min — adversarial reviews can be long


def ask_hermes(
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
    """Send message to Hermes AND invoke Hermes one-shot to process it."""
    effective_model = model or HERMES_DEFAULT_MODEL
    # Guard BEFORE send_message so a refused model leaves no orphaned bridge
    # message behind (hermes is a non-opencode transport; _run_opencode's
    # guard never sees this path).
    assert_model_routing_allowed(effective_model, context="ask-hermes transport")
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="hermes",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    register_ask(msg_id)
    if background:
        launch_background_ask(msg_id, "hermes", {"no_timeout": no_timeout})
        return msg_id
    print(f"\n🚀 Invoking Hermes ({effective_model}) to process message #{msg_id}...")
    response = _invoke_hermes(content, effective_model, data=data, no_timeout=no_timeout)
    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="hermes",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)
    record_ask_reply(msg_id, reply_id)
    return msg_id


def process_for_hermes(message_id: int, *, no_timeout: bool = False) -> None:
    """Process an existing Hermes ask, shared by sync and detached paths."""
    msg = fetch_ask_message(message_id, "hermes")
    if not msg:
        return
    model = ask_target_model(msg) or HERMES_DEFAULT_MODEL
    response = _invoke_hermes(msg["content"], model, data=ask_attachment(msg), no_timeout=no_timeout)
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="hermes",
        to_llm=msg["from"],
        to_model=ask_sender_model(msg),
    )
    acknowledge(message_id)
    acknowledge(reply_id)
    record_ask_reply(message_id, reply_id)


def _invoke_hermes(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
) -> str:
    """Run hermes -z PROMPT -m MODEL; return captured stdout."""
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        raise SystemExit("ask-hermes: hermes CLI not found in PATH")

    # If data file attached, prepend its content to the prompt under a fenced block.
    prompt = content
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-hermes: --data file does not exist: {data}")
        attached = data_path.read_text(encoding="utf-8", errors="replace")
        prompt = f"{content}\n\n## Attached data: {data_path.name}\n\n```\n{attached}\n```"

    timeout = None if no_timeout else HERMES_DEFAULT_TIMEOUT_S
    try:
        result = subprocess.run(
            [hermes_bin, "-z", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-hermes: hermes timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-hermes: hermes exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    return result.stdout.strip()
