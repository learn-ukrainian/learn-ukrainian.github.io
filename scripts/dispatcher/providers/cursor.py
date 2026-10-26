"""Cursor print-mode execution and assistant stream extraction."""

import json

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["cursor-agent", "-p", "--model", spec.model, "--output-format", "stream-json", "--trust"]
    argv += ["--workspace", str(spec.worktree)]
    if spec.mode == "read-only":
        argv += ["--mode", "ask"]
    elif spec.mode == "workspace-write":
        argv += ["--approve-mcps", "--sandbox", "disabled", "--force"]
    else:
        raise ValueError(f"cursor: unsupported mode {spec.mode!r}")
    return Invocation(argv, spec.prompt_file.read_bytes(), env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    parts, result, error = [""], {}, None
    models = set()
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = "cursor: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = "cursor: invalid event"
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            model = event.get("model")
            if isinstance(model, str) and model.strip():
                models.add(model)
        elif event.get("type") == "result":
            result = event
            if event.get("is_error") or event.get("subtype") != "success":
                error = "cursor: terminal result unsuccessful"
        elif event.get("type") == "error":
            error = "cursor: terminal error"
        elif event.get("type") == "text" and isinstance(event.get("content"), str):
            parts[-1] += event["content"]
        elif event.get("role") == "assistant" or event.get("type") == "assistant":
            content = event.get("message", event)
            content = content.get("content") if isinstance(content, dict) else None
            if isinstance(content, list):
                content = "".join(
                    p["text"]
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str)
                )
            if isinstance(content, str) and content.strip():
                parts.extend([content, ""])
    text = ""
    for part in parts:
        if not part.strip():
            continue
        if text and not text.endswith(("\n", "\r")) and not part.lstrip(" \t").startswith(("\n", "\r")):
            text += "\n"
        text += part.rstrip(" \t")
    text = text.rstrip() or None
    if text is None:
        fallback = result.get("result")
        text = fallback if isinstance(fallback, str) and fallback.strip() else None
    usage = result.get("usage")
    usage = usage if isinstance(usage, dict) else None
    if returncode:
        error = f"cursor: exited with status {returncode}"
    return ParsedResult(
        text,
        usage,
        error or (None if result and text else "cursor: missing result"),
        next(iter(models)) if len(models) == 1 else None,
    )
