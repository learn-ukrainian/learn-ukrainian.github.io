"""Codex exec flags and JSONL output, extracted from the existing adapter."""

import json

from scripts.agent_runtime.adapters.codex import _read_only_tmp_flags, _sources_read_only_flags
from scripts.agent_runtime.adapters.codex_events import classify_provider_message
from scripts.agent_runtime.read_only_tmp import dispatch_lease
from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.review_tools import hooks, native_sources, toml
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

# Failure codes (agent_runtime) for a provider that cannot take the run now: usage limits and no capacity.
_OUT_OF_CAPACITY = frozenset({"rate_limited", "provider_overloaded"})


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    from scripts.dispatcher.checks import check_model_admission

    check_model_admission(spec.agent, spec.model, spec.mode, spec.options, spec.prompt_file.read_bytes())
    argv = ["codex", "exec", "--json", "-C", str(spec.worktree), "-m", spec.model, "-o", str(spec.final_file),
            "--ignore-user-config"]
    if spec.options.get("output_schema_path") is not None:
        from scripts.dispatcher.output_schema import load

        load(spec.options)
        argv += ["--output-schema", spec.options["output_schema_path"]]
    if spec.effort is not None:
        argv += ["-c", f"model_reasoning_effort={spec.effort}"]
    if spec.mode == "read-only":
        # The checkout stays read-only; the task's own lease is the only other writable root (and TMPDIR).
        argv += _read_only_tmp_flags(dispatch_lease(spec.task_id))
    elif spec.mode == "workspace-write":
        argv += ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        raise ValueError(f"codex: unsupported mode {spec.mode!r}")
    argv += ["-c", "mcp_servers.sources=" + toml(native_sources("codex")), *_sources_read_only_flags()]
    argv += ["-c", "hooks=" + toml(hooks(harness="codex", review=spec.mode == "read-only")),
             "-c", "features.hooks=true", "--dangerously-bypass-hook-trust"]
    if spec.mode == "read-only":
        argv += ["-c", 'permissions.lu_review.network.domains={"*"="allow"}']
    return Invocation(argv, spec.prompt_file.read_bytes(), env, spec.final_file)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    usage, error, completed = None, None, False
    terminal_seen, capacity, stream_clean = False, None, True
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = error or "codex: invalid JSON stream"
            stream_clean = False
            continue
        if not isinstance(event, dict):
            error = error or "codex: invalid event"
            stream_clean = False
            continue
        if terminal_seen:
            error = error or "codex: event after terminal outcome"
            stream_clean = False
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
            # Only the terminal event's own message classifies the run, never agent text or notices.
            failure = event.get("error")
            message = failure.get("message") if isinstance(failure, dict) else None
            if isinstance(message, str) and classify_provider_message(message) in _OUT_OF_CAPACITY:
                capacity = message
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
    if capacity is not None and stream_clean:
        return ParsedResult(text, usage, f"codex: {capacity}", rate_limited=True)
    if returncode:
        error = f"codex: exited with status {returncode}"
    return ParsedResult(
        text, usage, error or (None if completed and text else "codex: missing completion or final text")
    )
