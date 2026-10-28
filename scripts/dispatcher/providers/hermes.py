"""Hermes transport for explicit OpenRouter models, with no default Qwen route."""

from __future__ import annotations

import re

from scripts.dispatcher.providers import read_only_refusal
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    if spec.mode != "workspace-write":
        raise ValueError(
            read_only_refusal("hermes") if spec.mode == "read-only" else f"hermes: unsupported mode {spec.mode!r}"
        )
    if not spec.model.strip():
        raise ValueError("hermes requires an explicit model")
    argv = ["hermes", "-z", spec.prompt_file.read_text(encoding="utf-8"), "-m", spec.model, "--provider", "openrouter"]
    return Invocation(argv, None, env.copy(), None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text = _ANSI.sub("", stdout).strip()
    error = f"hermes exited with code {returncode}" if returncode else None
    if len(text) <= 600 and "\n" not in text and re.match(r"HTTP [45]\d\d\b", text):
        error = error or "hermes provider HTTP error"
    return ParsedResult(text or None, None, error or (None if text else "hermes missing final response"))
