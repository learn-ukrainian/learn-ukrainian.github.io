"""OpenAI-compatible HTTP proxy for local agent CLIs.

Phase 1 intentionally exposes only the narrow chat-completions surface:
model listing, non-streaming chat completions, and a cheap health probe.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ._config import _PARENT_ENV, CLAUDE_CMD, CODEX_CLI, GEMINI_CLI, REPO_ROOT

_DEFAULT_BACKEND_TIMEOUT_S = 120


class Message(BaseModel):
    """Minimal OpenAI chat message shape accepted by the proxy."""

    role: str = Field(min_length=1)
    content: str | list[dict[str, Any]] | None = ""


class ChatCompletionRequest(BaseModel):
    """Subset of the OpenAI chat completion request envelope used in v1."""

    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1)
    messages: list[Message] = Field(min_length=1)
    user: str | None = None


@dataclass(frozen=True)
class CompletionResponse:
    """Normalized backend response before wrapping in OpenAI JSON."""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


Backend = Callable[..., CompletionResponse]


@dataclass(frozen=True)
class ModelRoute:
    """Routing metadata for a public model id."""

    family: str
    backend: Backend


def _backend_timeout_s() -> int:
    raw = os.environ.get("BRIDGE_PROXY_BACKEND_TIMEOUT_S")
    if raw is None:
        return _DEFAULT_BACKEND_TIMEOUT_S
    try:
        timeout = int(raw)
    except ValueError:
        return _DEFAULT_BACKEND_TIMEOUT_S
    return timeout if timeout > 0 else _DEFAULT_BACKEND_TIMEOUT_S


def _message_content_to_text(content: str | list[dict[str, Any]] | None) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in {None, "text", "input_text", "output_text"}:
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)


def _flatten_messages(messages: list[Message]) -> str:
    """Flatten OpenAI role messages into a deterministic CLI prompt."""

    system_blocks: list[str] = []
    turns: list[Message] = []
    for message in messages:
        if message.role in {"system", "developer"}:
            system_blocks.append(_message_content_to_text(message.content))
        else:
            turns.append(message)

    sections: list[str] = []
    if system_blocks:
        sections.append("[system]: " + "\n\n".join(block for block in system_blocks if block))

    for index, message in enumerate(turns, start=1):
        content = _message_content_to_text(message.content)
        sections.append(f"--- Round {index} ---\n[{message.role}]: {content}")

    return "\n\n".join(sections)


def _run_backend_command(
    backend_name: str,
    argv: list[str],
    *,
    prompt: str | None = None,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    env = dict(_PARENT_ENV)
    env["TERM"] = "xterm-256color"
    env["COLORTERM"] = "truecolor"
    result = subprocess.run(
        argv,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=_backend_timeout_s(),
        cwd=str(cwd),
        env=env,
        check=False,
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            argv,
            output=result.stdout,
            stderr=result.stderr or result.stdout or f"{backend_name} exited with {result.returncode}",
        )
    return result


def _codex_backend(model: str, messages: list[Message], **kwargs: Any) -> CompletionResponse:
    prompt = str(kwargs.get("prompt") or _flatten_messages(messages))
    codex_model = os.environ.get("BRIDGE_PROXY_CODEX_MODEL", "gpt-5.5")

    with tempfile.NamedTemporaryFile(prefix="openai-proxy-codex-", suffix=".txt", delete=False) as handle:
        output_path = Path(handle.name)

    try:
        argv = [
            CODEX_CLI,
            "exec",
            "--json",
            "--skip-git-repo-check",
            "-C",
            str(REPO_ROOT),
            "--color",
            "never",
            "-s",
            "read-only",
            "-o",
            str(output_path),
            "-m",
            codex_model,
            "-",
        ]
        result = _run_backend_command("codex", argv, prompt=prompt)
        content = ""
        if output_path.exists():
            content = output_path.read_text(encoding="utf-8", errors="replace").strip()
        if not content:
            content = result.stdout.strip()
        return CompletionResponse(content=content)
    finally:
        output_path.unlink(missing_ok=True)


def _gemini_backend(model: str, messages: list[Message], **kwargs: Any) -> CompletionResponse:
    prompt = str(kwargs.get("prompt") or _flatten_messages(messages))
    argv = [
        GEMINI_CLI,
        "-m",
        model,
        f"--prompt={prompt}",
        "--approval-mode",
        "plan",
    ]
    result = _run_backend_command("gemini", argv)
    return CompletionResponse(content=result.stdout.strip())


def _claude_backend(model: str, messages: list[Message], **kwargs: Any) -> CompletionResponse:
    prompt = str(kwargs.get("prompt") or _flatten_messages(messages))
    argv = [
        *CLAUDE_CMD,
        "--print",
        "--bare",
        "--model",
        model,
        "--",
        prompt,
    ]
    result = _run_backend_command("claude", argv)
    return CompletionResponse(content=result.stdout.strip())


def _hermes_backend(model: str, messages: list[Message], **kwargs: Any) -> CompletionResponse:
    prompt = str(kwargs.get("prompt") or _flatten_messages(messages))
    argv = [
        shutil.which("hermes") or "hermes",
        f"--oneshot={prompt}",
        "-m",
        model,
    ]
    result = _run_backend_command("hermes", argv)
    return CompletionResponse(content=result.stdout.strip())


_ROUTABLE_MODELS: dict[str, ModelRoute] = {
    "codex": ModelRoute(family="openai-codex", backend=_codex_backend),
    "gemini-3.0-flash-preview": ModelRoute(family="google-gemini", backend=_gemini_backend),
    "gemini-3.1-pro-preview": ModelRoute(family="google-gemini", backend=_gemini_backend),
    "claude-opus-4-7": ModelRoute(family="anthropic", backend=_claude_backend),
    "claude-sonnet-4-7": ModelRoute(family="anthropic", backend=_claude_backend),
    "grok-4.3": ModelRoute(family="xai", backend=_hermes_backend),
}


def _probe_cli(argv: list[str]) -> bool:
    try:
        result = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=1,
            cwd=str(REPO_ROOT),
            env=_PARENT_ENV,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _probe_codex() -> bool:
    return _probe_cli([CODEX_CLI, "--version"])


def _probe_gemini() -> bool:
    return _probe_cli([GEMINI_CLI, "--version"])


def _probe_claude() -> bool:
    return _probe_cli([*CLAUDE_CMD, "--version"])


def _probe_hermes() -> bool:
    return _probe_cli([shutil.which("hermes") or "hermes", "--version"])


_BACKEND_PROBES: dict[str, Callable[[], bool]] = {
    "codex": _probe_codex,
    "gemini": _probe_gemini,
    "claude": _probe_claude,
    "hermes": _probe_hermes,
}


def _openai_error(status_code: int, message: str, error_type: str, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type, "code": code}},
    )


def _first_error_line(value: object) -> str:
    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value or "")
    first = text.strip().splitlines()
    return first[0] if first else "unknown error"


app = FastAPI(title="AI Agent Bridge OpenAI Proxy", version="1.0")


@app.get("/healthz")
def healthz() -> dict[str, object]:
    return {
        "ok": True,
        "backends": {name: probe() for name, probe in _BACKEND_PROBES.items()},
    }


@app.get("/v1/models")
def list_models() -> dict[str, object]:
    created = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": created,
                "owned_by": route.family,
            }
            for model_id, route in _ROUTABLE_MODELS.items()
        ],
    }


@app.post("/v1/chat/completions", response_model=None)
def chat_completions(request: ChatCompletionRequest) -> dict[str, object] | JSONResponse:
    route = _ROUTABLE_MODELS.get(request.model)
    if route is None:
        return _openai_error(
            404,
            f"model '{request.model}' not found",
            "invalid_request_error",
            "model_not_found",
        )

    prompt = _flatten_messages(request.messages)
    try:
        completion = route.backend(
            request.model,
            request.messages,
            prompt=prompt,
            user=request.user,
        )
    except subprocess.TimeoutExpired as exc:
        return _openai_error(
            504,
            f"{route.family} backend timed out: {_first_error_line(exc.stderr)}",
            "upstream_error",
            "backend_timeout",
        )
    except subprocess.CalledProcessError as exc:
        return _openai_error(
            502,
            f"{route.family} backend failed: {_first_error_line(exc.stderr)}",
            "upstream_error",
            "backend_failed",
        )
    except OSError as exc:
        return _openai_error(
            502,
            f"{route.family} backend failed: {_first_error_line(exc)}",
            "upstream_error",
            "backend_failed",
        )

    # Backends do not expose consistent token accounting yet; keep zeroes
    # instead of fabricating approximate usage.
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": completion.content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
            "total_tokens": completion.total_tokens,
        },
    }
