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

Isolation (Sol #213 / fleet-comms Phase 0):
    Tool-capable Hermes must not inherit the operator primary checkout as cwd.
    Review-class asks always: neutral scratch cwd + read-only contract + size caps.
    Non-review asks also default to neutral cwd (escape: BRIDGE_ALLOW_PRIMARY_HERMES=1).
"""

from __future__ import annotations

import os
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
from ._config import REPO_ROOT
from ._messaging import acknowledge, send_message
from ._review_safety import (
    MAX_ASK_ATTACHMENT_BYTES,
    MAX_ASK_CONTENT_BYTES,
    MAX_REVIEW_REQUEST_BYTES,
    ReviewSafetyError,
    assert_attachment_size,
    assert_content_size,
    assert_formal_review_ask_payload,
    assert_review_cwd_safe,
    hermes_must_use_neutral_cwd,
    is_review_class_ask,
    neutral_review_scratch,
    prepend_read_only_contract,
    warn_missing_review_target,
)
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
    review = is_review_class_ask(msg_type=msg_type, task_id=task_id, content=content)
    try:
        _preflight_hermes_payload(
            content,
            data=data,
            review=review,
        )
    except ReviewSafetyError as exc:
        raise SystemExit(f"ask-hermes: {exc}") from exc

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
    try:
        response = _invoke_hermes(
            content,
            effective_model,
            data=data,
            no_timeout=no_timeout,
            review=review,
            task_id=task_id,
            msg_type=msg_type,
        )
    except ReviewSafetyError as exc:
        raise SystemExit(f"ask-hermes: {exc}") from exc
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
    content = msg["content"]
    task_id = msg.get("task_id") or ""
    msg_type = msg.get("type") or "query"
    review = is_review_class_ask(msg_type=msg_type, task_id=task_id, content=content)
    data = ask_attachment(msg)
    try:
        _preflight_hermes_payload(content, data=data, review=review)
        response = _invoke_hermes(
            content,
            model,
            data=data,
            no_timeout=no_timeout,
            review=review,
            task_id=task_id,
            msg_type=msg_type,
        )
    except ReviewSafetyError as exc:
        # Surface as exit for process-ask workers; lifecycle records failure upstream.
        raise SystemExit(f"ask-hermes: {exc}") from exc
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


def _preflight_hermes_payload(
    content: str,
    *,
    data: str | None,
    review: bool,
) -> None:
    formal_review = assert_formal_review_ask_payload(
        content,
        msg_type="review" if review else None,
        task_id=None,
        attachment=data,
        review=review,
        has_target=False,
    )
    warn_missing_review_target(formal_review=formal_review, has_target=False)
    limit = MAX_REVIEW_REQUEST_BYTES if review else MAX_ASK_CONTENT_BYTES
    assert_content_size(content, limit=limit, label="ask_content")
    if data:
        assert_attachment_size(Path(data))


def _invoke_hermes(
    content: str,
    model: str,
    *,
    data: str | None = None,
    no_timeout: bool = False,
    review: bool = False,
    task_id: str | None = None,
    msg_type: str | None = None,
) -> str:
    """Run hermes -z PROMPT -m MODEL from a safe cwd; return captured stdout."""
    del task_id, msg_type  # reserved for future sealed PR target wiring
    hermes_bin = shutil.which("hermes")
    if not hermes_bin:
        raise SystemExit("ask-hermes: hermes CLI not found in PATH")

    prompt = content
    if review or is_review_class_ask(content=content):
        review = True
        prompt = prepend_read_only_contract(prompt)

    if data:
        data_path = Path(data)
        if not data_path.exists():
            raise SystemExit(f"ask-hermes: --data file does not exist: {data}")
        assert_attachment_size(data_path)
        attached = data_path.read_text(encoding="utf-8", errors="replace")
        # Cap inlined attachment body again after read (defense in depth).
        if len(attached.encode("utf-8")) > MAX_ASK_ATTACHMENT_BYTES:
            raise ReviewSafetyError(
                f"attachment_exceeds_cap: bytes limit={MAX_ASK_ATTACHMENT_BYTES}"
            )
        prompt = f"{prompt}\n\n## Attached data: {data_path.name}\n\n```\n{attached}\n```"

    timeout = None if no_timeout else HERMES_DEFAULT_TIMEOUT_S
    use_neutral = hermes_must_use_neutral_cwd(review=review)

    if use_neutral:
        with neutral_review_scratch() as scratch:
            cwd = assert_review_cwd_safe(scratch, repo_root=REPO_ROOT)
            return _run_hermes_subprocess(
                hermes_bin,
                prompt,
                model,
                cwd=cwd,
                timeout=timeout,
            )

    # Escape hatch only for non-review consults.
    cwd = Path.cwd()
    print(
        "⚠️  ask-hermes: BRIDGE_ALLOW_PRIMARY_HERMES set — using process cwd "
        f"{cwd} (forbidden for review-class asks)"
    )
    return _run_hermes_subprocess(
        hermes_bin,
        prompt,
        model,
        cwd=cwd,
        timeout=timeout,
    )


def _run_hermes_subprocess(
    hermes_bin: str,
    prompt: str,
    model: str,
    *,
    cwd: Path,
    timeout: int | None,
) -> str:
    env = os.environ.copy()
    # Discourage git from walking into the operator repo via accidental discovery.
    env.setdefault("GIT_CEILING_DIRECTORIES", str(REPO_ROOT.parent))
    try:
        result = subprocess.run(
            [hermes_bin, "-z", prompt, "-m", model],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cwd),
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"ask-hermes: hermes timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise SystemExit(
            f"ask-hermes: hermes exited {result.returncode}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    return result.stdout.strip()
