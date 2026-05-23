"""Hermes adapter for ai_agent_bridge ask-hermes subcommand.

Mirrors ask-codex / ask-gemini pattern. Hermes is the underlying runtime for
several already-supported model adapters (hermes_grok, hermes_deepseek,
hermes_qwen). This bridge subcommand exposes ad-hoc one-shot Hermes calls
with arbitrary models so cross-model adversarial reviews can route through
hermes the same way they route through codex/gemini.

Invocation pattern:
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-hermes <content> \\
      --task-id <task> --model qwen/qwen3.6-plus

Under the hood: hermes -z "<content>" -m <model>
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._messaging import acknowledge, send_message

HERMES_DEFAULT_MODEL = "qwen/qwen3.6-plus"
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
) -> int:
    """Send message to Hermes AND invoke Hermes one-shot to process it."""
    effective_model = model or HERMES_DEFAULT_MODEL
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

    return msg_id


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
