"""Narrow, fail-closed provider adapters for the ZNO/NMT evaluator.

These adapters intentionally expose only an exam-response contract.  They do
not accept a grading key, execute model supplied commands, or retain provider
transcripts in the returned receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .mcp_proxy import REFERENCE_TOOLS


class AdapterError(ValueError):
    """A provider transport or its isolation evidence violated this contract."""


_TOOL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")
_PROJECT_PYTHON = (Path(__file__).resolve().parents[3] / ".venv" / "bin" / "python").resolve()
_SERVER_IDENTITY_TOOL = "mcp_server_identity"
_SERVER_IDENTITY_HASH_KEYS = frozenset({"server_code_sha256", "sources_db_sha256", "vesum_db_sha256"})
_SERVER_IDENTITY_SAFE_KEYS = _SERVER_IDENTITY_HASH_KEYS | frozenset({"sources_db_bytes", "vesum_db_bytes"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CLAUDE_FLAGS = frozenset(
    {
        "--restricted",
        "--tools",
        "--setting-sources",
        "--disable-slash-commands",
        "--strict-mcp-config",
        "--mcp-config",
        "--permission-mode",
        "--no-session-persistence",
        "--output-format",
        "--verbose",
        "--model",
        "--effort",
        "--json-schema",
        "--settings",
    }
)


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: Any) -> str:
    raw = value if isinstance(value, bytes) else canonical(value).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _tool_ref(name: str) -> str:
    return "mcp__sources__" + name


def normalized_reason(exc: BaseException) -> str:
    """Keep failures useful without exporting command output or credentials."""
    if isinstance(exc, subprocess.TimeoutExpired):
        return "timeout"
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_status_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "network_error"
    text = str(exc).replace("\n", " ").strip().lower()
    for token in (
        "configuration",
        "auth",
        "capability",
        "model",
        "tool",
        "response",
        "timeout",
        "mcp",
        "schema",
        "endpoint",
        "output",
    ):
        if token in text:
            return token + "_error"
    return "adapter_error"


def _require_exact_keys(value: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise AdapterError(f"{label} contains unsupported fields")


def validate_config(config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the public, serialisable evaluator configuration.

    Runtime endpoint and key *values* are read from environment variables.  A
    configuration therefore remains safe to fingerprint or persist.
    """
    if not isinstance(config, Mapping):
        raise AdapterError("configuration must be an object")
    adapter = config.get("adapter")
    base = {
        "schema",
        "adapter",
        "model",
        "effort",
        "timeout_seconds",
        "max_output_tokens",
        "max_tool_calls",
        "repeats",
        "tools",
        "corpus_id",
        "provider",
    }
    by_adapter = {
        "claude": base | {"claude_bin"},
        "chat-http": base | {"endpoint_env", "key_env"},
    }
    if adapter not in by_adapter:
        raise AdapterError("configuration adapter is unsupported")
    _require_exact_keys(config, by_adapter[adapter], "configuration")
    if config.get("schema") != "zno-nmt.config.v1":
        raise AdapterError("configuration schema mismatch")
    if not isinstance(config.get("model"), str) or not config["model"].strip():
        raise AdapterError("configuration model must be a nonempty string")
    effort = config.get("effort")
    if effort is not None and (not isinstance(effort, str) or not effort.strip()):
        raise AdapterError("configuration effort must be string or null")
    for field in ("timeout_seconds", "max_output_tokens", "max_tool_calls", "repeats"):
        value = config.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise AdapterError(f"configuration {field} must be positive")
    tools = config.get("tools")
    if not isinstance(tools, list) or any(
        not isinstance(item, str) or not _TOOL_RE.fullmatch(item) or item not in REFERENCE_TOOLS for item in tools
    ):
        raise AdapterError("configuration tools must be allowlisted Sources MCP references")
    if len(tools) != len(set(tools)):
        raise AdapterError("configuration tools contains duplicates")
    corpus_id = config.get("corpus_id")
    if corpus_id is not None and (not isinstance(corpus_id, str) or not corpus_id.strip()):
        raise AdapterError("configuration corpus_id must be string or null")
    provider = config.get("provider")
    if provider is not None and (not isinstance(provider, str) or not provider.strip()):
        raise AdapterError("configuration provider must be string or null")
    if adapter == "claude":
        binary = config.get("claude_bin", "claude")
        if not isinstance(binary, str) or not binary.strip():
            raise AdapterError("configuration claude_bin must be a nonempty path")
    else:
        endpoint_env = config.get("endpoint_env")
        if not isinstance(endpoint_env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", endpoint_env):
            raise AdapterError("configuration endpoint_env must be an environment variable name")
        key_env = config.get("key_env")
        if key_env is not None and (not isinstance(key_env, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key_env)):
            raise AdapterError("configuration key_env must be an environment variable name or null")
    return dict(config)


def _condition_policy(config: Mapping[str, Any], condition: str, sources_url: str | None) -> None:
    if condition not in {"closed-book", "sources"}:
        raise AdapterError("condition must be closed-book or sources")
    if condition == "sources" and (
        not config["tools"] or not isinstance(sources_url, str) or not sources_url.strip()
    ):
        raise AdapterError("sources condition requires nonempty sources URL and tools")


def _run_checked(argv: list[str], *, timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(argv, capture_output=True, text=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AdapterError("CLI capability probe failed") from exc


def _claude_capabilities(config: Mapping[str, Any], *, needs_sources: bool = False) -> tuple[str, str]:
    binary = str(config.get("claude_bin", "claude"))
    help_result = _run_checked([binary, "--help"], timeout=min(15, int(config["timeout_seconds"])))
    if help_result.returncode != 0:
        raise AdapterError("CLI capability probe failed")
    help_text = (help_result.stdout or "") + "\n" + (help_result.stderr or "")
    missing = [flag for flag in _CLAUDE_FLAGS if flag.lower() not in help_text.lower()]
    if missing:
        raise AdapterError("CLI isolation capability unavailable")
    if needs_sources and "--allowedtools" not in help_text.lower():
        raise AdapterError("CLI Sources tool capability unavailable")
    version_result = _run_checked([binary, "--version"], timeout=min(15, int(config["timeout_seconds"])))
    if version_result.returncode != 0:
        raise AdapterError("CLI version unavailable")
    version = (version_result.stdout or "").strip().splitlines()[0] if version_result.stdout else "unknown"
    return binary, version[:160]


def preflight(config: Mapping[str, Any], condition: str, sources_url: str | None = None) -> dict[str, Any]:
    """Check only capability and boundaries, returning no endpoint/key values."""
    checked = validate_config(config)
    _condition_policy(checked, condition, sources_url)
    capability: dict[str, Any] = {
        "schema": "zno-nmt.capability.v1",
        "adapter": checked["adapter"],
        "condition": condition,
        "requested_model": checked["model"],
        "requested_effort": checked["effort"],
        "tools_sha256": digest(checked["tools"]),
        "corpus_id_sha256": digest(checked["corpus_id"]) if checked["corpus_id"] is not None else None,
        "capability": "unverified",
    }
    if checked["adapter"] == "claude":
        _binary, version = _claude_capabilities(checked, needs_sources=condition == "sources")
        capability.update(capability="native-claude-restricted", cli_version=version)
    else:
        endpoint = os.environ.get(str(checked["endpoint_env"]), "")
        if not endpoint:
            raise AdapterError("HTTP endpoint is unavailable")
        capability.update(capability="chat-http-controller-mediated", cli_version=None)
    if condition == "sources":
        tools, identity = _mcp_list_tools(str(sources_url), int(checked["timeout_seconds"]))
        expected = set(checked["tools"])
        available = {str(item.get("name", "")) for item in tools}
        if not expected.issubset(available):
            raise AdapterError("Sources MCP does not expose configured tools")
        capability["tool_schema_sha256"] = digest(tools)
        capability["mcp_server_identity_sha256"] = identity
    else:
        capability["tool_schema_sha256"] = digest([])
        capability["mcp_server_identity_sha256"] = None
    return capability


def build_prompt(packet: Mapping[str, Any], condition: str) -> str:
    """Create the shared, gold-free exam prompt used by each fresh trial."""
    policy = "No tools are available. Answer from your own knowledge." if condition == "closed-book" else (
        "Only the explicitly provided Sources reference tools may be used. Do not use a tool to find answers outside that reference corpus."
    )
    return (
        "You are taking a Ukrainian exam. Answer every opaque item id exactly once. "
        "Do not explain your reasoning. Return only JSON matching the response schema: "
        "{\"responses\":{\"id\": string | object | null}}. "
        + policy
        + "\n\nQUESTION PACKET (contains no answers or scoring key):\n"
        + canonical(packet)
    )


def response_schema(packet: Mapping[str, Any]) -> dict[str, Any]:
    items = [item for item in packet.get("items", []) if isinstance(item, Mapping) and "id" in item]
    ids = [str(item["id"]) for item in items]
    answers: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = str(item["id"])
        if item.get("kind") == "matching":
            row_ids = [str(row["id"]) for row in item.get("rows", []) if isinstance(row, Mapping) and "id" in row]
            answers[item_id] = {
                "anyOf": [
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": row_ids,
                        "properties": {row_id: {"type": "string"} for row_id in row_ids},
                    },
                    {"type": "null"},
                ]
            }
        else:
            answers[item_id] = {"anyOf": [{"type": "string"}, {"type": "null"}]}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["responses"],
        "properties": {
            "responses": {
                "type": "object",
                "additionalProperties": False,
                "required": ids,
                "properties": answers,
            }
        },
    }


def _child_env(max_output_tokens: int) -> dict[str, str]:
    allowed = {"PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "SHELL", "TERM", "LANG", "LC_ALL", "SSL_CERT_FILE", "SSL_CERT_DIR"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    # Claude's native limit is an environment control.  The version probe
    # cannot attest that a particular CLI build honored it, so receipts retain
    # that distinction as configured rather than observed.
    env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(max_output_tokens)
    return env


def _parse_sse_or_json(raw: bytes) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="strict")
    candidates = [text]
    candidates.extend(line[5:].strip() for line in text.splitlines() if line.startswith("data:"))
    for candidate in reversed(candidates):
        try:
            value = _strict_json_loads(candidate)
        except (AdapterError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            return value
    raise AdapterError("MCP response is invalid")


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdapterError("provider JSON has duplicate keys")
        result[key] = value
    return result


def _reject_constant(_value: str) -> None:
    raise AdapterError("provider JSON contains non-finite number")


def _strict_json_loads(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_pairs, parse_constant=_reject_constant)
    except AdapterError:
        raise
    except json.JSONDecodeError as exc:
        raise AdapterError("provider JSON is invalid") from exc


def _mcp_request(url: str, payload: Mapping[str, Any], timeout: int, session_id: str | None = None) -> tuple[dict[str, Any], str | None]:
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    request = urllib.request.Request(url, data=canonical(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 -- operator-configured endpoint
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise AdapterError("MCP response exceeds limit")
            if not raw:
                return {}, response.headers.get("Mcp-Session-Id") or session_id
            return _parse_sse_or_json(raw), response.headers.get("Mcp-Session-Id") or session_id
    except AdapterError:
        raise
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise AdapterError("MCP request failed") from exc


def _safe_mcp_server_identity(response: Mapping[str, Any]) -> str | None:
    """Hash only the server's public identity fields, never endpoint metadata."""
    result = response.get("result")
    if not isinstance(result, Mapping) or result.get("isError") is True:
        return None
    content = result.get("content")
    if not isinstance(content, list):
        return None
    text = next(
        (block.get("text") for block in content if isinstance(block, Mapping) and block.get("type") == "text" and isinstance(block.get("text"), str)),
        None,
    )
    if not isinstance(text, str):
        return None
    try:
        value = _strict_json_loads(text)
    except AdapterError:
        return None
    if not isinstance(value, Mapping) or not _SERVER_IDENTITY_HASH_KEYS.issubset(value) or not set(value).issubset(_SERVER_IDENTITY_SAFE_KEYS):
        return None
    identity: dict[str, Any] = {}
    for key in _SERVER_IDENTITY_HASH_KEYS:
        candidate = value.get(key)
        if not isinstance(candidate, str) or not _SHA256_RE.fullmatch(candidate):
            return None
        identity[key] = candidate
    for key in ("sources_db_bytes", "vesum_db_bytes"):
        candidate = value.get(key)
        if candidate is not None:
            if not isinstance(candidate, int) or isinstance(candidate, bool) or candidate < 0:
                return None
            identity[key] = candidate
    return digest(identity)


def _mcp_list_tools(url: str, timeout: int) -> tuple[list[dict[str, Any]], str | None]:
    session: str | None = None
    initialized, session = _mcp_request(
        url,
        {"jsonrpc": "2.0", "id": "zno-nmt-init", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "zno-nmt-eval", "version": "1"}}},
        timeout,
    )
    result = initialized.get("result")
    if not isinstance(result, Mapping):
        raise AdapterError("MCP initialize failed")
    _mcp_request(url, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, timeout, session)
    listed, session = _mcp_request(url, {"jsonrpc": "2.0", "id": "zno-nmt-tools", "method": "tools/list", "params": {}}, timeout, session)
    body = listed.get("result")
    tools = body.get("tools") if isinstance(body, Mapping) else None
    if not isinstance(tools, list):
        raise AdapterError("MCP tools/list failed")
    normalized: list[dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, Mapping) or not isinstance(tool.get("name"), str) or not isinstance(tool.get("inputSchema"), Mapping):
            raise AdapterError("MCP tool schema is invalid")
        normalized.append({"name": tool["name"], "inputSchema": dict(tool["inputSchema"])})
    identity = None
    if _SERVER_IDENTITY_TOOL in {tool["name"] for tool in normalized}:
        try:
            identity_response, _session = _mcp_request(
                url,
                {"jsonrpc": "2.0", "id": "zno-nmt-server-identity", "method": "tools/call", "params": {"name": _SERVER_IDENTITY_TOOL, "arguments": {}}},
                timeout,
                session,
            )
            identity = _safe_mcp_server_identity(identity_response)
        except AdapterError:
            # Identity is supplemental capability evidence. A standards-valid
            # server without this tool stays explicitly unknown.
            identity = None
    return normalized, identity


def _mcp_call(url: str, tool_name: str, arguments: Mapping[str, Any], timeout: int) -> Any:
    if not tool_name.startswith("mcp__sources__"):
        raise AdapterError("model requested invalid tool")
    upstream = tool_name.removeprefix("mcp__sources__")
    if not _TOOL_RE.fullmatch(upstream) or upstream not in REFERENCE_TOOLS:
        raise AdapterError("model requested invalid tool")
    initialized, session = _mcp_request(url, {"jsonrpc": "2.0", "id": "zno-nmt-init", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "zno-nmt-eval", "version": "1"}}}, timeout)
    if not isinstance(initialized.get("result"), Mapping):
        raise AdapterError("MCP initialize failed")
    _mcp_request(url, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, timeout, session)
    result, _session = _mcp_request(url, {"jsonrpc": "2.0", "id": "zno-nmt-call", "method": "tools/call", "params": {"name": upstream, "arguments": dict(arguments)}}, timeout, session)
    if "error" in result or not isinstance(result.get("result"), Mapping):
        raise AdapterError("MCP tool call failed")
    return result["result"]


def _extract_responses(value: Any, packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"responses"} or not isinstance(value.get("responses"), Mapping):
        raise AdapterError("provider response schema mismatch")
    expected = [str(item["id"]) for item in packet.get("items", [])]
    responses = value["responses"]
    if set(responses) != set(expected):
        raise AdapterError("provider response IDs mismatch")
    normalized: dict[str, Any] = {}
    for item_id in expected:
        answer = responses[item_id]
        if answer is not None and not isinstance(answer, (str, Mapping)):
            raise AdapterError("provider response value is invalid")
        normalized[item_id] = dict(answer) if isinstance(answer, Mapping) else answer
    return normalized


def _parse_stream_json(
    stdout: str, packet: Mapping[str, Any], tools: set[str], max_tools: int
) -> tuple[dict[str, Any], str, int, dict[str, int | float | None]]:
    result_text: str | None = None
    structured_output: Mapping[str, Any] | None = None
    observed_models: set[str] = set()
    observed_tools: list[str] = []
    init_seen = False
    usage: dict[str, int | float | None] = {"input_tokens": None, "output_tokens": None, "total_tokens": None, "cost_usd": None}
    for line in stdout.splitlines():
        try:
            event = _strict_json_loads(line)
        except AdapterError as exc:
            raise AdapterError("CLI emitted invalid stream JSON") from exc
        if not isinstance(event, Mapping):
            raise AdapterError("CLI emitted invalid stream event")
        structured = event.get("structured_output")
        if isinstance(structured, Mapping):
            structured_output = structured
        model = event.get("model")
        if model is None and isinstance(event.get("message"), Mapping):
            model = event["message"].get("model")
        if isinstance(model, str) and model:
            observed_models.add(model)
        if event.get("type") == "system" and event.get("subtype") == "init":
            init_seen = True
            raw_tools = event.get("tools", [])
            if not isinstance(raw_tools, list):
                raise AdapterError("CLI init tool surface is malformed")
            announced = {item if isinstance(item, str) else item.get("name") for item in raw_tools if isinstance(item, (str, Mapping))}
            if None in announced or not announced.issubset(tools | {"StructuredOutput"}):
                raise AdapterError("CLI init tool boundary violation")
            if not tools and announced - {"StructuredOutput"}:
                raise AdapterError("CLI closed-book tool boundary violation")
            if tools and not tools.issubset(announced):
                raise AdapterError("CLI Sources tool surface incomplete")
        content = event.get("message", {}).get("content", []) if isinstance(event.get("message"), Mapping) else []
        if isinstance(content, list):
            for block in content:
                if isinstance(block, Mapping) and block.get("type") == "tool_use":
                    name = block.get("name")
                    if not isinstance(name, str):
                        raise AdapterError("CLI emitted malformed tool call")
                    if name == "StructuredOutput":
                        continue
                    observed_tools.append(name)
        if event.get("type") == "tool_use":
            name = event.get("name")
            if not isinstance(name, str):
                raise AdapterError("CLI emitted malformed tool call")
            if name == "StructuredOutput":
                continue
            observed_tools.append(name)
        if event.get("type") == "result" and isinstance(event.get("result"), str):
            if event.get("is_error") is True:
                raise AdapterError("CLI result is error")
            result_text = event["result"]
            event_usage = event.get("usage")
            if isinstance(event_usage, Mapping):
                usage["input_tokens"] = _nonnegative_int(event_usage.get("input_tokens", event_usage.get("prompt_tokens")))
                usage["output_tokens"] = _nonnegative_int(event_usage.get("output_tokens", event_usage.get("completion_tokens")))
                usage["total_tokens"] = _nonnegative_int(event_usage.get("total_tokens"))
            usage["cost_usd"] = _nonnegative_number(event.get("total_cost_usd", event.get("cost_usd")))
        elif event.get("type") == "result" and event.get("is_error") is True:
            raise AdapterError("CLI result is error")
    if any(name not in tools for name in observed_tools) or len(observed_tools) > max_tools:
        raise AdapterError("CLI tool boundary violation")
    if not init_seen:
        raise AdapterError("CLI init evidence missing")
    if len(observed_models) > 1:
        raise AdapterError("CLI model drift")
    if result_text is None and structured_output is None:
        raise AdapterError("CLI response missing result")
    if structured_output is not None:
        payload: Any = dict(structured_output)
    else:
        try:
            payload = _strict_json_loads(result_text or "")
        except AdapterError as exc:
            raise AdapterError("CLI response is not JSON") from exc
    return _extract_responses(payload, packet), next(iter(observed_models), "unknown"), len(observed_tools), usage


def _nonnegative_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _nonnegative_number(value: Any) -> int | float | None:
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0 else None


def _run_claude_process(argv: list[str], *, cwd: Path, env: Mapping[str, str], prompt: str, timeout: int) -> subprocess.CompletedProcess[str]:
    """Kill the whole CLI process group so an MCP proxy cannot survive a timeout."""
    try:
        process = subprocess.Popen(argv, cwd=str(cwd), env=dict(env), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        stdout, stderr = process.communicate(prompt, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (NameError, ProcessLookupError, OSError):
            if "process" in locals():
                process.kill()
        if "process" in locals():
            process.communicate()
        raise AdapterError("CLI timeout") from exc
    except OSError as exc:
        raise AdapterError("CLI invocation failed") from exc
    return subprocess.CompletedProcess(argv, process.returncode, stdout=stdout, stderr=stderr)


def run_claude(packet: Mapping[str, Any], config: Mapping[str, Any], condition: str, *, sources_url: str | None, prompt: str) -> dict[str, Any]:
    """Run one fresh restricted Claude CLI session and return sanitized evidence."""
    checked = validate_config(config)
    if checked["adapter"] != "claude":
        raise AdapterError("wrong adapter")
    _condition_policy(checked, condition, sources_url)
    binary, cli_version = _claude_capabilities(checked, needs_sources=condition == "sources")
    session_id = str(uuid.uuid4())
    schema = response_schema(packet)
    with tempfile.TemporaryDirectory(prefix="zno-nmt-claude-") as temp:
        root = Path(temp)
        mcp_config = root / "mcp.json"
        if condition == "closed-book":
            mcp = {"mcpServers": {}}
        else:
            proxy = Path(__file__).with_name("mcp_proxy.py").resolve()
            if not proxy.is_file():
                raise AdapterError("Sources MCP proxy unavailable")
            if not _PROJECT_PYTHON.is_file():
                raise AdapterError("project interpreter unavailable")
            mcp = {"mcpServers": {"sources": {"command": str(_PROJECT_PYTHON), "args": [str(proxy), "--url-env", "ZNO_NMT_SOURCES_URL", "--tools", canonical(checked["tools"]), "--max-tool-calls", str(checked["max_tool_calls"])], "env": {"ZNO_NMT_SOURCES_URL": str(sources_url)}}}}
        mcp_config.write_text(canonical(mcp) + "\n", encoding="utf-8")
        mcp_config.chmod(0o600)
        argv = [
            binary,
            "-p",
            "--restricted",
            "--settings",
            canonical({"claudeMdExcludes": ["**"], "disableAllHooks": True}),
            "--setting-sources",
            "",
            "--tools",
            "",
            "--disable-slash-commands",
            "--strict-mcp-config",
            "--mcp-config",
            str(mcp_config),
            "--permission-mode",
            "dontAsk",
            "--no-session-persistence",
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            checked["model"],
            "--json-schema",
            canonical(schema),
        ]
        if checked["effort"] is not None:
            argv.extend(["--effort", checked["effort"]])
        if condition == "sources":
            argv.extend(["--allowedTools", ",".join(_tool_ref(tool) for tool in checked["tools"])])
        started = time.monotonic()
        completed = _run_claude_process(argv, cwd=root, env=_child_env(checked["max_output_tokens"]), prompt=prompt, timeout=checked["timeout_seconds"])
        elapsed = time.monotonic() - started
        if completed.returncode != 0:
            failure_text = (completed.stdout or "") + "\n" + (completed.stderr or "")
            if any(marker in failure_text.casefold() for marker in ("not logged in", "login", "authentication", "oauth", "keychain")):
                raise AdapterError("CLI authentication unavailable")
            raise AdapterError("CLI invocation failed")
        observed_tools = {_tool_ref(tool) for tool in checked["tools"]} if condition == "sources" else set()
        responses, effective_model, tool_calls, usage = _parse_stream_json(completed.stdout, packet, observed_tools, checked["max_tool_calls"])
    if effective_model != "unknown" and effective_model != checked["model"]:
        raise AdapterError("CLI model drift")
    return {
        "responses": responses,
        "identity": {"adapter": "claude", "harness": "claude-cli", "model": checked["model"], "provider": checked.get("provider") or "claude-cli", "session_id": session_id, "requested_model": checked["model"], "effective_model": effective_model, "requested_effort": checked["effort"], "effective_effort": "unknown", "cli_version": cli_version, "tool_schema_sha256": digest(checked["tools"] if condition == "sources" else []), "corpus_id_sha256": digest(checked["corpus_id"]) if checked["corpus_id"] is not None else None, "max_output_tokens_configured": checked["max_output_tokens"], "max_output_tokens_effective": "unknown"},
        "metrics": {"elapsed_seconds": elapsed, "input_tokens": usage["input_tokens"], "output_tokens": usage["output_tokens"], "total_tokens": usage["total_tokens"], "cost_usd": usage["cost_usd"], "tool_calls": tool_calls},
    }


class _RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def _http_json(url: str, payload: Mapping[str, Any], *, key: str | None, timeout: int, max_bytes: int) -> dict[str, Any]:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AdapterError("HTTP endpoint scheme invalid")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    request = urllib.request.Request(url, data=canonical(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        opener = urllib.request.build_opener(_RejectRedirects())
        with opener.open(request, timeout=timeout) as response:  # nosec B310 -- operator-configured endpoint
            raw = response.read(max_bytes + 1)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
        raise AdapterError("HTTP completion failed") from exc
    if len(raw) > max_bytes:
        raise AdapterError("HTTP completion exceeds limit")
    try:
        value = _strict_json_loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, AdapterError) as exc:
        raise AdapterError("HTTP completion response invalid") from exc
    if not isinstance(value, dict):
        raise AdapterError("HTTP completion response invalid")
    return value


def run_chat_http(packet: Mapping[str, Any], config: Mapping[str, Any], condition: str, *, sources_url: str | None, prompt: str) -> dict[str, Any]:
    """Run one controller-mediated chat-completions session.

    Tool calls are checked before the MCP broker receives them; model text can
    never become a shell command or an unrestricted MCP request.
    """
    checked = validate_config(config)
    if checked["adapter"] != "chat-http":
        raise AdapterError("wrong adapter")
    _condition_policy(checked, condition, sources_url)
    endpoint = os.environ.get(str(checked["endpoint_env"]), "")
    key = os.environ.get(str(checked["key_env"]), "") if checked.get("key_env") else None
    if not endpoint:
        raise AdapterError("HTTP runtime endpoint unavailable")
    started = time.monotonic()
    deadline = started + checked["timeout_seconds"]
    mcp_tools: list[dict[str, Any]] = []
    identity: str | None = None
    if condition == "sources":
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError("HTTP total timeout")
        mcp_tools, identity = _mcp_list_tools(str(sources_url), max(1, int(remaining)))
    available = {tool["name"]: tool for tool in mcp_tools}
    if condition == "sources" and not set(checked["tools"]).issubset(available):
        raise AdapterError("Sources MCP does not expose configured tools")
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    max_bytes = min(2_000_000, max(65_536, checked["max_output_tokens"] * 64))
    request_base: dict[str, Any] = {"model": checked["model"], "messages": messages, "max_tokens": checked["max_output_tokens"], "response_format": {"type": "json_schema", "json_schema": {"name": "zno_nmt_responses", "strict": True, "schema": response_schema(packet)}}}
    if checked["effort"] is not None:
        request_base["reasoning_effort"] = checked["effort"]
    if condition == "sources":
        request_base["tools"] = [{"type": "function", "function": {"name": _tool_ref(name), "description": "Approved Sources reference tool", "parameters": tool["inputSchema"]}} for name, tool in available.items() if name in checked["tools"]]
        request_base["tool_choice"] = "auto"
    tool_calls = 0
    retrieval_digests: list[str] = []
    usage_totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    usage_known = {key: False for key in usage_totals}
    response: dict[str, Any] | None = None
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AdapterError("HTTP total timeout")
        body = _http_json(endpoint, request_base, key=key, timeout=max(1, int(remaining)), max_bytes=max_bytes)
        if body.get("model") != checked["model"]:
            raise AdapterError("HTTP model drift")
        choices = body.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], Mapping):
            raise AdapterError("HTTP completion choices invalid")
        message = choices[0].get("message")
        if not isinstance(message, Mapping):
            raise AdapterError("HTTP completion message invalid")
        calls = message.get("tool_calls")
        finish_reason = choices[0].get("finish_reason")
        if finish_reason == "length":
            raise AdapterError("HTTP completion output limit")
        body_usage = body.get("usage")
        if isinstance(body_usage, Mapping):
            for usage_key, provider_key in (("input_tokens", "prompt_tokens"), ("output_tokens", "completion_tokens"), ("total_tokens", "total_tokens")):
                value = _nonnegative_int(body_usage.get(provider_key))
                if value is not None:
                    usage_totals[usage_key] += value
                    usage_known[usage_key] = True
        if not calls:
            response = body
            content = message.get("content")
            if not isinstance(content, str):
                raise AdapterError("HTTP completion content invalid")
            try:
                responses = _extract_responses(_strict_json_loads(content), packet)
            except AdapterError as exc:
                raise AdapterError("HTTP completion is not JSON") from exc
            break
        if condition != "sources" or not isinstance(calls, list):
            raise AdapterError("HTTP tool boundary violation")
        messages.append(dict(message))
        for call in calls:
            tool_calls += 1
            if tool_calls > checked["max_tool_calls"] or not isinstance(call, Mapping):
                raise AdapterError("HTTP tool boundary violation")
            function = call.get("function")
            name = function.get("name") if isinstance(function, Mapping) else None
            raw_args = function.get("arguments") if isinstance(function, Mapping) else None
            if not isinstance(name, str) or name not in {_tool_ref(tool) for tool in checked["tools"]} or not isinstance(raw_args, str):
                raise AdapterError("HTTP tool boundary violation")
            try:
                arguments = _strict_json_loads(raw_args)
            except AdapterError as exc:
                raise AdapterError("HTTP tool arguments invalid") from exc
            if not isinstance(arguments, Mapping):
                raise AdapterError("HTTP tool arguments invalid")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AdapterError("HTTP total timeout")
            broker_result = _mcp_call(str(sources_url), name, arguments, max(1, int(remaining)))
            retrieval_digests.append(digest(broker_result))
            call_id = call.get("id")
            if not isinstance(call_id, str) or not call_id:
                raise AdapterError("HTTP tool call id invalid")
            messages.append({"role": "tool", "tool_call_id": call_id, "content": canonical(broker_result)})
    assert response is not None
    return {
        "responses": responses,
        "identity": {"adapter": "chat-http", "harness": "chat-http", "model": checked["model"], "provider": checked.get("provider") or "chat-http", "session_id": str(uuid.uuid4()), "requested_model": checked["model"], "effective_model": checked["model"], "requested_effort": checked["effort"], "effective_effort": "unknown", "cli_version": None, "tool_schema_sha256": digest(mcp_tools), "mcp_server_identity_sha256": identity, "corpus_id_sha256": digest(checked["corpus_id"]) if checked["corpus_id"] is not None else None, "retrieval_receipt_sha256": digest(retrieval_digests) if retrieval_digests else None},
        "metrics": {"elapsed_seconds": time.monotonic() - started, "input_tokens": usage_totals["input_tokens"] if usage_known["input_tokens"] else None, "output_tokens": usage_totals["output_tokens"] if usage_known["output_tokens"] else None, "total_tokens": usage_totals["total_tokens"] if usage_known["total_tokens"] else None, "cost_usd": None, "tool_calls": tool_calls},
    }
