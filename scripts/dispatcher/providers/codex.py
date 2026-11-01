"""Codex exec flags and JSONL output, extracted from the existing adapter."""

import copy
import hashlib
import json
import os
import time
from collections.abc import Mapping

from scripts.agent_runtime.adapters.codex import _read_only_tmp_flags, _sources_read_only_flags
from scripts.agent_runtime.adapters.codex_events import classify_provider_message
from scripts.agent_runtime.attempt_safe_read import safe_read_attempt_file
from scripts.agent_runtime.read_only_tmp import dispatch_lease
from scripts.audit.post_build_review import (
    OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS as _POST_BUILD_FORBIDDEN_KEYWORDS,
)
from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.review_tools import hooks, native_sources, toml
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec

OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS = _POST_BUILD_FORBIDDEN_KEYWORDS | frozenset({"$schema", "$id"})

# Failure codes (agent_runtime) for a provider that cannot take the run now: usage limits and no capacity.
_OUT_OF_CAPACITY = frozenset({"rate_limited", "provider_overloaded"})



def _provider_literal_type(value: object) -> str:
    """Return the JSON Schema scalar type required by OpenAI strict mode."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    raise ValueError("Codex structured-output const/enum values must be JSON scalars")


def _normalize_provider_schema_types(value: object) -> None:
    """Add strict-validator type annotations without changing constraints."""
    if isinstance(value, list):
        for item in value:
            _normalize_provider_schema_types(item)
        return
    if not isinstance(value, dict):
        return
    for key, item in list(value.items()):
        if key in {"properties", "$defs"} and isinstance(item, Mapping):
            for subschema in item.values():
                _normalize_provider_schema_types(subschema)
            continue
        _normalize_provider_schema_types(item)
    if "type" in value:
        return
    if "const" in value:
        value["type"] = _provider_literal_type(value["const"])
    elif "enum" in value:
        enum_types = {_provider_literal_type(item) for item in value["enum"]}
        value["type"] = next(iter(enum_types)) if len(enum_types) == 1 else sorted(enum_types)
    elif {"properties", "required"}.intersection(value):
        value["type"] = "object"
    elif {"items", "minItems", "maxItems"}.intersection(value):
        value["type"] = "array"


def _normalize_codex_strict_node(value: object) -> None:
    """Translate schema keywords to OpenAI strict mode without mangling property names."""
    if isinstance(value, list):
        for item in value:
            _normalize_codex_strict_node(item)
        return
    if not isinstance(value, dict):
        return
    if "oneOf" in value and "anyOf" not in value:
        value["anyOf"] = value.pop("oneOf")
    for keyword in OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS:
        value.pop(keyword, None)
    if "$ref" in value:
        reference = value["$ref"]
        value.clear()
        value["$ref"] = reference
        return
    if value.get("type") == "object":
        properties = value.get("properties")
        if isinstance(properties, Mapping):
            value["additionalProperties"] = False
            value["required"] = list(properties)
    for key, item in list(value.items()):
        if key in {"properties", "$defs"} and isinstance(item, Mapping):
            for subschema in item.values():
                _normalize_codex_strict_node(subschema)
            continue
        _normalize_codex_strict_node(item)


def _needs_openai_strict(node: object) -> bool:
    if isinstance(node, dict):
        if bool(OPENAI_STRUCTURED_OUTPUT_FORBIDDEN_KEYWORDS & node.keys()):
            return True
        for key, value in node.items():
            if key in {"properties", "$defs"} and isinstance(value, Mapping):
                if any(_needs_openai_strict(subschema) for subschema in value.values()):
                    return True
                continue
            if _needs_openai_strict(value):
                return True
        return False
    if isinstance(node, list):
        return any(_needs_openai_strict(value) for value in node)
    return False


def openai_strict_schema(document: dict) -> dict:
    """The schema Codex can bind. The receipt schema is unchanged.

    Strict mode rejects ``if``, unrequired properties, and forbidden keywords.
    ``missing_capabilities`` is legal on the receipt only when correctness is
    uncertain, so the bound schema omits it. A Codex reply never carries the field,
    which the receipt already accepts, and a correct reply still cannot smuggle one in.
    """
    schema = copy.deepcopy(document)
    properties = schema.get("properties")
    if isinstance(properties, dict):
        properties.pop("missing_capabilities", None)
    _normalize_provider_schema_types(schema)
    _normalize_codex_strict_node(schema)
    if not isinstance(schema, dict):
        raise ValueError("codex: output schema is not an object")
    return schema


def _strict_schema_path(spec: TaskSpec, document: dict) -> str:
    directory = spec.final_file.parent / ".codex-schemas"
    path = directory / f"{spec.task_id}.json"
    content = json.dumps(openai_strict_schema(document), separators=(",", ":")).encode("utf-8")
    derived_digest = hashlib.sha256(content).hexdigest()
    spec.options["provider_output_schema_sha256"] = derived_digest
    if spec.options.get("dry_run") == "True":
        return str(path)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags, 0o600)
    except FileExistsError:
        path.unlink(missing_ok=True)
        fd = os.open(str(path), flags, 0o600)
    try:
        os.write(fd, content)
    finally:
        os.close(fd)
    verified = safe_read_attempt_file(path, trusted_root=directory)
    if hashlib.sha256(verified).hexdigest() != derived_digest:
        raise ValueError("codex strict output schema verification failed")
    try:
        now = time.time()
        for stale in directory.glob("*.json"):
            if stale != path and stale.stat().st_mtime < now - 3600:
                stale.unlink(missing_ok=True)
    except OSError:
        pass
    return str(path)


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    from scripts.dispatcher.checks import check_model_admission

    check_model_admission(spec.agent, spec.model, spec.mode, spec.options, spec.prompt_file.read_bytes())
    argv = ["codex", "exec", "--json", "-C", str(spec.worktree), "-m", spec.model, "-o", str(spec.final_file),
            "--ignore-user-config"]
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
