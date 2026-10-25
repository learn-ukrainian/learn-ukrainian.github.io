"""AGY headless user-event envelope and terminal result extraction."""

import json

from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["agy", "--mode", "auto", "--input-format", "stream-json", "--output-format", "stream-json"]
    argv += ["--model", spec.model]
    argv += ["--sandbox"] if spec.mode == "read-only" else ["--dangerously-skip-permissions"]
    argv += ["--print-timeout", "120m", "--log-file", str(spec.final_file.with_suffix(".log"))]
    if spec.mode == "read-only":
        argv += ["--add-dir", str(spec.worktree)]
    message = {"role": "user", "content": [{"type": "text", "text": spec.prompt_file.read_bytes().decode("utf-8")}]}
    stdin = (json.dumps({"event": "user", "message": message}) + "\n").encode("utf-8")
    return Invocation(argv, stdin, env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    result, error = {}, None
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = "agy: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = "agy: invalid event"
        elif event.get("event") == "result":
            terminal = event.get("result")
            if not isinstance(terminal, dict):
                error = "agy: invalid terminal result"
                continue
            result = terminal
            if result.get("status") != "SUCCESS" or result.get("error"):
                error = "agy: terminal result unsuccessful"
        elif event.get("event") == "error":
            error = "agy: terminal error"
    text = result.get("response")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    if returncode:
        error = f"agy: exited with status {returncode}"
    return ParsedResult(
        text, usage if isinstance(usage, dict) else None, error or (None if text else "agy: missing final text")
    )
