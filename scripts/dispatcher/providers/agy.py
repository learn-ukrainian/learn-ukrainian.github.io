"""AGY headless user-event envelope and terminal result extraction."""

import json
import re

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher import agy_sandbox
from scripts.dispatcher.providers import read_only_refusal
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

_BACKGROUND_TERMINATED_RE = re.compile(r"terminating (?P<count>\d+) background task\(s\)")
_PRINT_TIMEOUT_PARTIAL_RE = re.compile(r"print timeout after \S+ with turn in progress")


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["agy", "--mode", "auto", "--input-format", "stream-json", "--output-format", "stream-json"]
    argv += ["--model", spec.model]
    argv += ["--dangerously-skip-permissions", "--print-timeout", "120m"]
    if spec.mode == "workspace-write":
        argv += ["--log-file", str(spec.final_file.with_suffix(".log"))]
    elif spec.mode == "read-only":
        # AGY has no write lock of its own: read-only runs only inside the dispatcher's bubblewrap
        # boundary, which is the argv returned here, so no caller can launch it unwrapped (C-3027).
        if refusal := read_only_refusal("agy"):
            raise ValueError(refusal)
        argv += ["--add-dir", str(spec.worktree), "--log-file", str(agy_sandbox.log_file(spec.task_id))]
        argv = agy_sandbox.launcher(spec, argv)
    else:
        raise ValueError(f"agy: unsupported mode {spec.mode!r}")
    message = {"role": "user", "content": [{"type": "text", "text": spec.prompt_file.read_bytes().decode("utf-8")}]}
    stdin = (json.dumps({"event": "user", "message": message}) + "\n").encode("utf-8")
    return Invocation(argv, stdin, env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    result, error = {}, None
    terminal_seen = False
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = error or "agy: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = error or "agy: invalid event"
        elif event.get("event") == "result":
            if terminal_seen:
                error = error or "agy: duplicate terminal result"
                continue
            terminal_seen = True
            terminal = event.get("result")
            if not isinstance(terminal, dict):
                error = error or "agy: invalid terminal result"
                continue
            result = terminal
            if result.get("status") != "SUCCESS" or result.get("error"):
                error = error or "agy: terminal result unsuccessful"
        elif event.get("event") == "error":
            error = error or "agy: terminal error"
    text = result.get("response")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    if _PRINT_TIMEOUT_PARTIAL_RE.search(stderr) or any(
        int(match["count"]) > 0 for match in _BACKGROUND_TERMINATED_RE.finditer(stderr)
    ):
        error = error or "agy: incomplete run"
    if returncode:
        error = f"agy: exited with status {returncode}"
    return ParsedResult(
        text, usage if isinstance(usage, dict) else None, error or (None if text else "agy: missing final text")
    )
