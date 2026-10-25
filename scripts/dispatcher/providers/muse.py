"""Native Muse JSONL execution, with no model or role restrictions.

``muse exec --help`` and ``muse --help`` expose ``--yolo`` for unattended
write access, shell execution and network access. Write mode needs it because
the default sandbox protects .git, preventing commit and push. Read mode uses
the built-in :read-only profile and disables shell execution. These are per-run
settings; no saved permission settings are changed. See
https://dev.meta.ai/docs/muse-code/permissions for the native permission model.
"""

from __future__ import annotations

import json

from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["muse", "exec", "--json", "--model", spec.model]
    argv.extend(["--workspace", str(spec.worktree), "--worktree", "off", "--prompt-file", str(spec.prompt_file)])
    argv.extend(["--contributor-mode", spec.options.get("contributor_mode", "off"), "--no-foreign-personal-context"])
    if spec.effort:
        argv.extend(["--reasoning-effort", spec.effort])
    if spec.mode == "workspace-write":
        argv.append("--yolo")
    else:
        argv.extend(["--permission-profile", ":read-only", "--disable-shell"])
    return Invocation(argv, None, env.copy(), None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text = usage = error = None
    terminal_seen = False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        kind, payload = event.get("payload_type", ""), event.get("payload")
        if kind == "run.usage" and isinstance(payload, dict):
            usage = payload
        elif isinstance(kind, str) and kind.startswith("run.terminal."):
            if (
                terminal_seen
                or kind != "run.terminal.completed"
                or not isinstance(payload, dict)
                or payload.get("terminal", "completed") != "completed"
                or payload.get("reason")
            ):
                error = "Muse terminal failure"
            elif isinstance(payload.get("text"), str):
                text = payload["text"].strip() or None
            terminal_seen = True
    if returncode:
        error = f"Muse exited with code {returncode}"
    elif not terminal_seen or not text:
        error = error or "Muse final response missing"
    return ParsedResult(None if error else text, usage, error)
