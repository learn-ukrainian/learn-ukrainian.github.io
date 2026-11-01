"""Codex exec flags and JSONL output, extracted from the existing adapter."""

import copy
import json
from pathlib import Path

from scripts.agent_runtime.adapters.codex import _read_only_tmp_flags
from scripts.agent_runtime.adapters.codex_events import classify_provider_message
from scripts.agent_runtime.read_only_tmp import dispatch_lease
from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

# Failure codes (agent_runtime) for a provider that cannot take the run now: usage limits and no capacity.
_OUT_OF_CAPACITY = frozenset({"rate_limited", "provider_overloaded"})
# OpenAI strict structured outputs reject these. `anyOf` is allowed only below the root.
_STRICT_DROP = frozenset({
    "$schema", "$id", "if", "then", "else", "allOf", "not", "oneOf",
    "dependentRequired", "dependentSchemas", "uniqueItems",
})
_STDERR_EXCERPT = 500


def _needs_openai_strict(node: object) -> bool:
    if isinstance(node, dict):
        return bool(_STRICT_DROP & node.keys()) or any(_needs_openai_strict(value) for value in node.values())
    if isinstance(node, list):
        return any(_needs_openai_strict(value) for value in node)
    return False


def _strict_node(node: object) -> object:
    """A copy OpenAI strict mode accepts, without the receipt schema's conditional."""
    if isinstance(node, list):
        return [_strict_node(value) for value in node]
    if not isinstance(node, dict):
        return node
    if "oneOf" in node:
        # The findings schema uses oneOf only for sources. A string array still
        # has to satisfy the receipt schema, which keeps the original oneOf.
        return {"type": "array", "minItems": 1, "items": {"type": "string"}}
    return {
        key: _strict_node(value)
        for key, value in node.items()
        if key not in _STRICT_DROP
    }


def openai_strict_schema(document: dict) -> dict:
    """The schema Codex can bind. The receipt schema is unchanged.

    Strict mode rejects ``if`` and a root ``anyOf``. ``missing_capabilities`` is
    legal on the receipt only when correctness is uncertain, so the bound schema
    omits it. A Codex reply never carries the field, which the receipt already
    accepts, and a correct reply still cannot smuggle one in.
    """
    schema = copy.deepcopy(document)
    properties = schema.get("properties")
    if isinstance(properties, dict):
        properties.pop("missing_capabilities", None)
    strict = _strict_node(schema)
    if not isinstance(strict, dict):
        raise ValueError("codex: output schema is not an object")
    return strict


def _strict_schema_path(spec: TaskSpec, document: dict) -> str:
    from scripts.common.scratch import resolve_scratch_root

    directory = Path(resolve_scratch_root()) / "learn-ukrainian" / "codex-schemas"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{spec.task_id}.json"
    path.write_text(json.dumps(openai_strict_schema(document)), encoding="utf-8")
    return str(path)


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    from scripts.dispatcher.checks import check_model_admission

    check_model_admission(spec.agent, spec.model, spec.mode, spec.options, spec.prompt_file.read_bytes())
    argv = ["codex", "exec", "--json", "-C", str(spec.worktree), "-m", spec.model, "-o", str(spec.final_file)]
    if spec.options.get("output_schema_path") is not None:
        from scripts.dispatcher.output_schema import load

        document = load(spec.options)
        schema_path = spec.options["output_schema_path"]
        if isinstance(document, dict) and _needs_openai_strict(document):
            schema_path = _strict_schema_path(spec, document)
        argv += ["--output-schema", schema_path]
    if spec.effort is not None:
        argv += ["-c", f"model_reasoning_effort={spec.effort}"]
    if spec.mode == "read-only":
        # The checkout stays read-only; the task's own lease is the only other writable root (and TMPDIR).
        argv += _read_only_tmp_flags(dispatch_lease(spec.task_id))
    elif spec.mode == "workspace-write":
        argv += ["--dangerously-bypass-approvals-and-sandbox"]
    else:
        raise ValueError(f"codex: unsupported mode {spec.mode!r}")
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
        excerpt = " ".join(stderr.split())
        if excerpt:
            error = f"{error}: {excerpt[:_STDERR_EXCERPT]}"
    return ParsedResult(
        text, usage, error or (None if completed and text else "codex: missing completion or final text")
    )
