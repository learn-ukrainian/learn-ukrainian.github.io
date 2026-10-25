"""Muse exec JSONL transport, without model or role restrictions.

Native help exposes permission profiles independently of shell sandboxing.
Write mode uses --permission-profile :unrestricted for file edits, native
shell commands, commits and network pushes without approval prompts. Native
profiles cannot combine with --sandbox-network. Read-only uses :read-only,
--disable-write and --disable-shell. No toolset override removes shell tools.
"""

from __future__ import annotations

import json

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["muse", "exec", "--json", "--model", spec.model]
    argv += ["--workspace", str(spec.worktree), "--worktree", "off", "--prompt-file", str(spec.prompt_file)]
    argv += ["--contributor-mode", spec.options.get("contributor_mode", "off")]
    if spec.effort:
        argv += ["--reasoning-effort", spec.effort]
    if spec.mode == "workspace-write":
        argv += ["--permission-profile", ":unrestricted"]
    else:
        argv += ["--permission-profile", ":read-only", "--disable-write", "--disable-shell"]
    return Invocation(argv, None, {**env, "MUSE_NO_AUTO_UPDATE": "1"}, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text = usage = None
    error = f"muse exited with code {returncode}" if returncode else None
    for line in jsonl_lines(stdout):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind, payload = event.get("payload_type", ""), event.get("payload")
        if not isinstance(kind, str):
            continue
        if kind == "run.usage" and isinstance(payload, dict):
            usage = payload
        elif kind.startswith("run.terminal."):
            if (
                kind != "run.terminal.completed"
                or not isinstance(payload, dict)
                or payload.get("terminal", "completed") != "completed"
                or payload.get("reason") is not None
            ):
                error = error or "muse terminal failure"
            else:
                text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        text = None
        error = error or "muse missing final response"
    return ParsedResult(text, usage, error)
