"""Codex exec flags and JSONL output, extracted from the existing adapter."""

import json

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["codex", "exec", "--json", "-C", str(spec.worktree), "-m", spec.model, "-o", str(spec.final_file)]
    if spec.effort is not None:
        argv += ["-c", f"model_reasoning_effort={spec.effort}"]
    if spec.mode == "read-only":
        argv += ["-s", "read-only"]
    elif spec.mode == "workspace-write":
        argv += ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        raise ValueError(f"codex: unsupported mode {spec.mode!r}")
    return Invocation(argv, spec.prompt_file.read_bytes(), env, spec.final_file)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    usage, error, completed = None, None, False
    terminal_seen = False
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = error or "codex: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = error or "codex: invalid event"
            continue
        if terminal_seen:
            error = error or "codex: event after terminal outcome"
            continue
        kind = event.get("type", "")
        if kind == "turn.completed":
            terminal_seen = True
            completed = True
            if isinstance(event.get("usage"), dict):
                usage = event["usage"]
            continue
        elif kind == "turn.failed":
            terminal_seen = True
            error = error or "codex: terminal error"
        elif isinstance(kind, str) and kind.startswith("turn.") and kind != "turn.started":
            terminal_seen = True
            error = error or "codex: unknown terminal outcome"
        payload = event.get("payload", event)
        if isinstance(payload, dict) and payload.get("type") == "token_count":
            info = payload.get("info")
            tokens = info.get("total_token_usage") if isinstance(info, dict) else None
            if isinstance(tokens, dict):
                usage = tokens
    text = final_text if isinstance(final_text, str) and final_text.strip() else None
    if returncode:
        error = f"codex: exited with status {returncode}"
    return ParsedResult(
        text, usage, error or (None if completed and text else "codex: missing completion or final text")
    )
