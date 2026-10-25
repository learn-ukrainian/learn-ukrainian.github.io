"""DeepSeek V4.1 Flash through OpenCode's explicit Flash model route."""

from __future__ import annotations

import json

from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["opencode", "run", "--model", "deepseek/deepseek-flash", "--format", "json", "--variant", "high"]
    if spec.mode == "workspace-write":
        argv.append("--auto")
    argv.extend(["--", spec.prompt_file.read_text(encoding="utf-8")])
    return Invocation(argv, None, env.copy(), None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text = reason = usage = error = None
    chunks = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        part = event.get("part") if isinstance(event.get("part"), dict) else {}
        if kind == "text" and isinstance(part.get("text"), str):
            chunks.append(part["text"])
        if kind in ("tool", "tool_use", "step_start", "step_finish", "step-start", "step-finish"):
            if chunks:
                text, chunks = "".join(chunks).strip(), []
            if kind in ("step_finish", "step-finish"):
                reason = part.get("reason") or event.get("reason")
                if reason not in ("stop", "completed", "tool-calls"):
                    error = "OpenCode terminal failure"
                usage = part.get("tokens") if isinstance(part.get("tokens"), dict) else usage
            state = part.get("state") if isinstance(part.get("state"), dict) else {}
            status = state.get("status") or part.get("status") or event.get("status")
            if status in ("rejected", "cancelled", "permission_denied", "permission_rejected", "error"):
                error = "OpenCode tool failure"
        if kind == "error" or event.get("error") is not None:
            error = "OpenCode terminal error"
    text = "".join(chunks).strip() if chunks else text
    if returncode:
        error = f"OpenCode exited with code {returncode}"
    elif reason not in ("stop", "completed") or not text:
        error = error or "OpenCode final response incomplete"
    return ParsedResult(None if error else text, usage, error)
