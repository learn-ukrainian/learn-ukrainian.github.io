"""DeepSeek V4.1 Flash through the explicit OpenCode provider route."""

from __future__ import annotations

import json

from scripts.agent_runtime.sources_read_only import sources_tool_sets
from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.review_tools import native_sources, shell_denies
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

# OpenCode allows edits and every shell command by default and has no OS sandbox, so read-only
# carries its own permission rules (https://opencode.ai/docs/permissions/): ``edit`` covers the
# edit, write and patch tools, and for bash the last matching pattern wins. Reviews retain shell
# execution with the shared deny patterns and worker guards. OpenCode merges
# ``OPENCODE_PERMISSION`` over the loaded config's ``permission``.
_READ_ONLY_PERMISSION = json.dumps(
    {
        "edit": "deny",
        "task": "deny",
        "bash": {
            "*": "allow",
            **{pattern: "deny" for pattern in shell_denies()},
        },
    },
    separators=(",", ":"),
)


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["opencode", "run", "--model", "deepseek/deepseek-flash", "--format", "json", "--variant", "high"]
    child_env = env.copy()
    config = {"mcp": {"sources": native_sources("opencode")},
              "tools": {f"sources_{name}": False for name in sources_tool_sets()[1]}}
    if spec.mode == "workspace-write":
        argv.append("--auto")
    elif spec.mode == "read-only":
        child_env["OPENCODE_PERMISSION"] = _READ_ONLY_PERMISSION
        argv.append("--auto")
        config["plugin"] = [(spec.worktree / ".agent/dispatch-tools/review-guards.mjs").as_uri()]
    else:
        raise ValueError(f"opencode: unsupported mode {spec.mode!r}")
    child_env["OPENCODE_CONFIG_CONTENT"] = json.dumps(config, separators=(",", ":"))
    argv += ["--", spec.prompt_file.read_text(encoding="utf-8")]
    return Invocation(argv, None, child_env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    text, chunks, usage, reason = None, [], None, None
    error = f"opencode exited with code {returncode}" if returncode else None
    for line in jsonl_lines(stdout):
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        part = event.get("part") or {}
        if not isinstance(part, dict):
            part = {}
        if kind == "error" or event.get("error") is not None:
            error = error or "opencode terminal error"
        if kind == "text" and isinstance(part.get("text"), str):
            chunks.append(part["text"])
        elif chunks and kind in ("tool", "tool_use", "step_start", "step_finish", "step-start", "step-finish"):
            text, chunks = "".join(chunks).strip(), []
        if kind in ("step_finish", "step-finish") or part.get("type") in ("step_finish", "step-finish"):
            reason = part.get("reason") or event.get("reason")
            if reason not in ("stop", "completed", "tool-calls"):
                error = error or "opencode terminal failure"
            if isinstance(part.get("tokens"), dict):
                usage = part["tokens"]
        state = part.get("state")
        rejected = ("rejected", "cancelled", "permission_denied", "permission_rejected")
        if kind in ("tool", "tool_use") and isinstance(state, dict) and state.get("status") in rejected:
            error = error or "opencode tool permission rejected"
    text = "".join(chunks).strip() if chunks else text
    if reason is not None and reason not in ("stop", "completed"):
        error = error or "opencode incomplete terminal outcome"
    return ParsedResult(text or None, usage, error or (None if text else "opencode missing final response"))
