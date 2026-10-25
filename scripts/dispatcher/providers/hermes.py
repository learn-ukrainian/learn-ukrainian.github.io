"""Hermes through OpenRouter with an explicit model, never a default Qwen route."""

from __future__ import annotations

import re

from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    if not spec.model.strip():
        raise ValueError("Hermes requires an explicit model")
    argv = ["hermes", "-z", spec.prompt_file.read_text(encoding="utf-8"), "-m", spec.model]
    argv.extend(["--provider", "openrouter"])
    return Invocation(argv, None, env.copy(), None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text = _ANSI.sub("", stdout).strip()
    error = None
    if returncode:
        error = f"Hermes exited with code {returncode}"
    elif not text:
        error = "Hermes final response missing"
    elif "\n" not in text and len(text) <= 600 and re.match(r"^HTTP\s+[45]\d{2}\b", text):
        error = "Hermes provider HTTP error"
    return ParsedResult(None if error else text, None, error)
