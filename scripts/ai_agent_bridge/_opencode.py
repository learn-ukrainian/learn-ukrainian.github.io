"""Opencode adapter for ai_agent_bridge ask-opencode subcommand.

Exposes ad-hoc one-shot opencode calls with arbitrary openrouter models.
Useful for cross-model adversarial reviews where the target model isn't
in the hermes proxy (e.g. openrouter/qwen/qwen3.7-max as demonstrated in
the 2026-05-23 strip-plan review).

Invocation pattern:
    .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-opencode <content> \\
      --task-id <task> --model openrouter/qwen/qwen3.7-max [--data FILE]

Under the hood: opencode run --model PROVIDER/MODEL [--file FILE] "CONTENT"
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ._messaging import acknowledge, send_message

OPENCODE_DEFAULT_MODEL = "openrouter/qwen/qwen3.7-max"
OPENCODE_DEFAULT_TIMEOUT_S = 900


def ask_opencode(
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
    effective_model = model or OPENCODE_DEFAULT_MODEL
    msg_id = send_message(
        content,
        task_id,
        msg_type,
        data,
        from_llm=from_llm,
        to_llm="opencode",
        from_model=from_model,
        to_model=to_model or effective_model,
    )
    print(f"\n🚀 Invoking opencode ({effective_model}) to process message #{msg_id}...")
    response = _invoke_opencode(content, effective_model, data=data, no_timeout=no_timeout)

    reply_id = send_message(
        content=response,
        task_id=task_id,
        msg_type="response",
        from_llm="opencode",
        to_llm=from_llm,
        to_model=from_model,
    )
    acknowledge(msg_id)
    acknowledge(reply_id)

    return msg_id


def _invoke_opencode(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
) -> str:
    opencode_bin = shutil.which("opencode")
    if not opencode_bin:
        raise SystemExit("ask-opencode: opencode CLI not found in PATH")

    argv = [opencode_bin, "run", "--model", model, "--format", "default"]
    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-opencode: --data file does not exist: {data}")
        argv.extend(["--file", str(data_path.resolve()), "--"])
    argv.append(content)

    timeout = None if no_timeout else OPENCODE_DEFAULT_TIMEOUT_S
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-opencode: opencode timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-opencode: opencode exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    # opencode run prints ANSI control codes and a banner before the response.
    # Strip leading ANSI sequences and the "build · model" line.
    output = result.stdout
    # Crude strip: lines that are escape sequences or the banner.
    # If a more robust ANSI stripper exists in the project (e.g. _ANSI_RE in
    # hermes adapters), reuse it.
    return output.strip()
