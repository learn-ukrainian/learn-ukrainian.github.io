"""ACPX bounded read-only transport (#6027, #6043, #6078, #6130, #6158).

Wraps the project-local ``acpx`` headless CLI
(https://www.npmjs.com/package/acpx) for the Agent Client Protocol (ACP).

Direct-only seats in this module cover the fixed participant registry:

- ``AcpxAdapter`` / ``acpx-codex-shadow`` (#6027) — fixed Codex participant
  via ``acpx … codex exec``
- ``AcpxGrokShadowAdapter`` / ``acpx-grok-shadow`` (#6043) — fixed Grok
  participant via a custom ``--agent`` command that forces native Grok
  ``agent … --agent-profile <hash-pinned-no-tool-profile> --no-leader stdio``
  (never the built-in ``grok-build`` name, which cannot place parent flags
  before ``stdio``)
- built-in ACP participants for Claude, Kimi, KimiCC K3, Cursor, and Pool
- source-blind project ACP wrappers for AGY and DeepSeek
- native OpenCode ACP for the Z.AI GLM subscription route

No seat is registered for model selection, catalog, review eligibility, or
failover (``cli_available: False``). They are not a second coordination plane:
fleet-comms remains the durable authority and shadow comparison stays optional.

Contract captured empirically from the local ``acpx@0.13.0`` install
(``node_modules/acpx``), not guessed:

- ``exec`` is always one-shot and never reuses a saved session or queue
  owner — confirmed by reading ``handleExec`` in ``dist/cli.js``, which calls
  ``runOnce()`` directly instead of the queue-owner path ``prompt`` uses.
  This is what makes ``codex exec`` / custom-agent ``exec`` structurally safe
  for a stateless, no-queue, non-persistent shadow call: we never need to
  reject "queue" or "session" behavior at our own layer because the CLI
  subcommand itself has none.
- Exit codes (``src/types.ts`` EXIT_CODES): SUCCESS=0, ERROR=1, USAGE=2,
  TIMEOUT=3, NO_SESSION=4, PERMISSION_DENIED=5, INTERRUPTED=130.
- ``--format json --json-strict`` streams the raw ACP JSON-RPC exchange as
  NDJSON on stdout, one message per line, and suppresses non-JSON noise on
  stderr. On failure the CLI's own top-level handler appends one final
  ``{"jsonrpc":"2.0","id":null,"error":{...,"data":{"acpxCode":...}}}`` line
  (verified live against the compatibility-probed binary: a ``--timeout`` breach produced
  exactly this shape with ``data.acpxCode == "TIMEOUT"``, exit code 3; a bad
  ``--agent`` path produced ``data.acpxCode == "RUNTIME"``, exit code 1).
  ``data.acpxCode``/``data.detailCode`` are drawn from
  ``OUTPUT_ERROR_CODES``/free-form detail codes in
  ``live-checkpoint-*.js`` (e.g. ``AUTH_REQUIRED``, ``AGENT_DISCONNECTED``,
  ``QUEUE_PROTOCOL_INVALID_JSON``).
- ACP wire shapes (``@agentclientprotocol/sdk`` schema, a direct acpx
  dependency): agent text arrives as ``session/update`` notifications with
  ``params.update.sessionUpdate == "agent_message_chunk"`` and
  ``params.update.content == {"type": "text", "text": "..."}``; the terminal
  ``session/prompt`` response carries ``result.stopReason`` in
  ``{"end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled"}``.
- Auth method selection under ``--auth-policy fail`` is explicit via non-secret
  per-process selectors such as ``ACPX_AUTH_CHAT_GPT=1`` (Codex ChatGPT login)
  and ``ACPX_AUTH_CACHED_TOKEN=1`` (Grok cached native login). Never invent
  additional selectors; never read/store/log credentials. The Grok selector
  was verified live against the fixed custom ``--agent`` command: the
  selector produced a successful one-shot response, while the same runtime
  path with the selector stripped failed closed as ``AUTH_REQUIRED``.

Confinement is structural, not probabilistic. Ordinary calls pass
``--deny-all --no-fs --no-terminal --allowed-tools ""``. The one formal-review
exception retains ``--no-fs`` and ``--no-terminal`` while admitting only five
exact ``mcp__sealed_review__*`` tools from a parent-owned config and a
content-verified helper; its permission policy defaults every other request to
deny. The adapter rejects any different config, helper, interpreter, snapshot
mode, or tool-config key before spawn.

Issues: #6027, #6043, #6078, #6130, #6158.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shlex
import shutil
import stat
import subprocess
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from ..result import ParseResult
from ..routes import deepseek_first_party_error, is_deepseek_first_party_forbidden_in_ci
from .base import InvocationPlan
from .glm import assert_glm_egress_allowed

try:
    from scripts.guardrails import worktree_containment as _worktree_containment
    from scripts.guardrails.worktree_containment import (
        NotAGitRepositoryError,
        resolve_main_root,
    )
except ImportError:  # pragma: no cover - stripped sys.path flavor
    from guardrails import worktree_containment as _worktree_containment  # type: ignore[import-not-found, no-redef]
    from guardrails.worktree_containment import (  # type: ignore[import-not-found, no-redef]
        NotAGitRepositoryError,
        resolve_main_root,
    )

_logger = logging.getLogger(__name__)

# Env var gating the transport. ``shadow`` is the comparison path; ``active``
# is accepted only inside the controller-owned context below. Unset, ``off``,
# and unrecognized values refuse to spawn.
TRANSPORT_ENV = "LU_ACPX_TRANSPORT"

# Rolling compatibility contracts. Versions are observed for telemetry only;
# every executable is admitted from the exact command/flag surface this module
# will invoke. A compatible in-place upgrade is accepted immediately, while a
# changed surface fails before prompt delivery.
ACPX_CLI_COMPATIBILITY_CONTRACT = "json-one-shot-v1"
CLAUDE_ACP_ADAPTER_COMPATIBILITY_CONTRACT = "installed>=0.64.2<1"
AGY_CLI_COMPATIBILITY_CONTRACT = "text-plan-sandbox-v1"
OPENCODE_CLI_COMPATIBILITY_CONTRACT = "native-acp-pure-v1"
HERMES_CLI_COMPATIBILITY_CONTRACT = "text-oneshot-isolated-v1"
ACPX_DEFAULT_MAX_TURNS = 1
_CLAUDE_ACP_SEALED_READ_CHUNK_BYTES = 64 * 1024
_CLAUDE_ACP_MAX_SEALED_READ_CHUNKS = 64
_CLAUDE_ACP_SEALED_REVIEW_TURN_OVERHEAD = 2

_ACPX_REQUIRED_GLOBAL_FLAGS: tuple[str, ...] = (
    "--agent",
    "--cwd",
    "--format",
    "--json-strict",
    "--auth-policy",
    "--deny-all",
    "--non-interactive-permissions",
    "--no-fs",
    "--no-terminal",
    "--allowed-tools",
    "--max-turns",
    "--prompt-retries",
    "--model",
)
_AGY_REQUIRED_FLAGS: tuple[str, ...] = (
    "--print",
    "--mode",
    "--sandbox",
    "--disable-slash-commands",
    "--print-timeout",
    "--output-format",
    "--model",
    "--log-file",
)
_OPENCODE_REQUIRED_ACP_FLAGS: tuple[str, ...] = ("--pure",)
_HERMES_REQUIRED_FLAGS: tuple[str, ...] = (
    "--ignore-rules",
    "--oneshot",
    "--model",
    "--provider",
)
AGY_ACP_MODEL = "gemini-3.6-flash-high"
CLAUDE_ACP_MODEL = "claude-sonnet-5"
CLAUDE_ACP_MODELS = frozenset({CLAUDE_ACP_MODEL, "claude-fable-5"})
GLM_ACP_MODEL = "glm-5.2"
GLM_ACP_INVOCATION_MODEL = "zai-coding-plan/glm-5.2"
DEEPSEEK_ACP_MODEL = "deepseek-v4-pro"
# OpenCode advertises its existing local login as ACP auth method
# ``opencode-login``. ACPX maps that method ID deterministically to this
# non-secret selector; the value is never a credential.
GLM_AUTH_OPENCODE_LOGIN_ENV = "ACPX_AUTH_OPENCODE_LOGIN"

# Project-local dependency binary. Deliberately NOT `shutil.which("acpx")`:
# global/PATH resolution would let an unrelated or unreviewed global acpx
# install silently take over. "No global binary authority" per the approved
# Stage 0/1 contract.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ACPX_BINARY = _REPO_ROOT / "node_modules" / ".bin" / "acpx"
# Keep this separately patchable for hermetic adapter tests.  An explicit
# override is authoritative and must never silently fall back to another tree.
_ACPX_BINARY = _DEFAULT_ACPX_BINARY
_CLAUDE_ACP_PACKAGE = "@agentclientprotocol/claude-agent-acp"
_CLAUDE_ACP_MIN_VERSION = (0, 64, 2)
_CLAUDE_ACP_MAX_VERSION = (1, 0, 0)
_CLAUDE_ACP_MANIFEST_LIMIT_BYTES = 64 * 1024
_STRICT_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)
_TEXT_AGENT_PATH = _REPO_ROOT / "scripts" / "agent_runtime" / "acp_text_agent.mjs"
_TEXT_AGENT_SHA256 = "42761e2bd9ab0e66f5e5779826777b46bd0761cc4673e13285e1fc37418ea679"
_OPENCODE_DENY_ALL_CONFIG = json.dumps(
    {"permission": {"*": "deny"}, "tools": {"*": False}},
    separators=(",", ":"),
    sort_keys=True,
)
_OPENCODE_SEALED_REVIEW_CONFIG = json.dumps(
    {
        # OpenCode normalizes MCP tools to <server>_<tool>. Keep every
        # built-in and every other MCP server denied while making only the
        # parent-pinned sealed reader visible to the provider.
        "permission": {"*": "deny", "sealed_review_*": "allow"},
        # OpenCode otherwise replaces tool results above 50 KiB with a path in
        # its local tool-output directory. The sealed reviewer cannot read
        # that directory by design, so keep each bounded required-read result
        # inline. The MCP itself still enforces the tighter 384 KiB streamed
        # response and 2 MiB complete-evidence ceilings; 3 MiB leaves bounded
        # room for the authenticated chunks' JSON envelope.
        "tool_output": {"max_bytes": 3 * 1024 * 1024, "max_lines": 100_000},
    },
    separators=(",", ":"),
    sort_keys=True,
)

# Rolling native Grok CLI compatibility contract for the Grok ACPX seat.
# Built-in acpx ``grok-build`` is intentionally unused: it expands to
# ``grok agent stdio`` without a place for the parent flags required by this
# adapter. The CLI version is observed for telemetry, but compatibility is
# decided from the command and flags we actually invoke rather than semver.
GROK_CLI_COMPATIBILITY_CONTRACT = "agent-stdio-v1"
_GROK_REQUIRED_AGENT_FLAGS: tuple[str, ...] = (
    "--model",
    "--reasoning-effort",
    "--agent-profile",
    "--no-leader",
)
GROK_SHADOW_MODEL = "grok-4.5"
GROK_SHADOW_EFFORT = "high"
_GROK_PROFILE_PATH = _REPO_ROOT / "scripts" / "agent_runtime" / "profiles" / "acpx-grok-read-only.md"
_GROK_PROFILE_SHA256 = "5831398f7204be279e908371b5f0990d5e5e725a323091232e184083649d7158"
_GROK_SEALED_REVIEW_PROFILE_PATH = (
    _REPO_ROOT / "scripts" / "agent_runtime" / "profiles" / "acpx-grok-sealed-review.md"
)
_GROK_SEALED_REVIEW_PROFILE_SHA256 = "e6527f1f0f4b67f8b52fed9f7ca74f7ecd35e0e76920c54f23639465ddac5605"
# Non-secret acpx 0.13.0 auth-method selector for a cached native Grok login.
GROK_AUTH_CACHED_TOKEN_ENV = "ACPX_AUTH_CACHED_TOKEN"
# Ambient XAI API-key selectors that would compete with cached_token under
# --auth-policy fail. Scrubbed from the child env so the only accepted path
# is the cached native login selector above. Never read as credential values.
_GROK_XAI_API_KEY_ENV_UNSETS: tuple[str, ...] = (
    "XAI_API_KEY",
    "GROK_API_KEY",
    "ACPX_AUTH_XAI_API_KEY",
    "ACPX_AUTH_API_KEY",
)

# tool_config allowlist. Anything outside this set is rejected before spawn
# — this is the enforcement point for "unsupported permission/tool config"
# in the approved reject-before-spawn list. No key here can loosen
# confinement; each seat re-affirms its own fixed target_agent.
# "correlation_id"/"idempotency_key" are local runtime metadata only
# (see _require_local_metadata_field): never forwarded to the ACP wire protocol.
_ALLOWED_TOOL_CONFIG_KEYS = frozenset(
    {
        "acpx_shadow",
        "acpx_discussion",
        "acpx_transport",
        "target_agent",
        "correlation_id",
        "idempotency_key",
        "sealed_review_mcp_config",
    }
)

_SEALED_REVIEW_TOOL_NAMES = (
    "mcp__sealed_review__list_files",
    "mcp__sealed_review__read_file",
    "mcp__sealed_review__read_required",
    "mcp__sealed_review__read_required_all",
    "mcp__sealed_review__search_text",
)
_GROK_NATIVE_SEALED_REVIEW_TOOL_NAMES = tuple(
    name.removeprefix("mcp__") for name in _SEALED_REVIEW_TOOL_NAMES
)


def _normalize_grok_sealed_result(result: object, *, tool_name: str) -> object:
    """Unwrap Grok's authenticated MCP envelope into the provider-neutral result."""
    if not tool_name.startswith("sealed_review__") or not isinstance(result, dict):
        return result
    if (
        result.get("type") != "MCP"
        or result.get("server_name") != "sealed_review"
        or result.get("tool_name") != tool_name.removeprefix("sealed_review__")
    ):
        return result
    output = result.get("output")
    if not isinstance(output, dict) or set(output) != {"OkayOutput"}:
        return result
    serialized = output.get("OkayOutput")
    if not isinstance(serialized, str):
        return result
    try:
        decoded = json.loads(serialized)
    except json.JSONDecodeError:
        return result
    return decoded if isinstance(decoded, dict) else result


def _validate_sealed_review_mcp_config(raw: object, *, adapter_label: str) -> str | None:
    """Validate the exact parent-owned MCP config before enabling any tool."""
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config must be an absolute path")
    config_path = Path(raw)
    try:
        config_stat = config_path.lstat()
        payload = config_path.read_bytes()
    except OSError as exc:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config is unreadable: {exc}") from exc
    if (
        not stat.S_ISREG(config_stat.st_mode)
        or config_stat.st_uid != os.getuid()
        or config_stat.st_mode & 0o077
        or len(payload) > 16 * 1024
    ):
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config ownership/mode/size is unsafe")
    try:
        config = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config is malformed") from exc
    if not isinstance(config, dict) or set(config) != {"mcpServers"}:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config has unsupported keys")
    servers = config.get("mcpServers")
    if not isinstance(servers, list) or len(servers) != 1 or not isinstance(servers[0], dict):
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP config must define exactly one server")
    server = servers[0]
    if set(server) != {"name", "command", "args", "env"} or server.get("name") != "sealed_review":
        raise AcpxShadowRefusalError(f"{adapter_label}: only the sealed_review server is permitted")
    expected_python = str(_REPO_ROOT / ".venv" / "bin" / "python")
    args = server.get("args")
    if server.get("command") != expected_python or server.get("env") != []:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP runtime is not parent-pinned")
    if not isinstance(args, list) or len(args) != 4 or args[:2] != ["-I", "-S"]:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP arguments are invalid")
    helper = Path(args[2]) if isinstance(args[2], str) else Path()
    snapshot = Path(args[3]) if isinstance(args[3], str) else Path()
    try:
        helper_stat = helper.lstat()
        snapshot_stat = snapshot.lstat()
        config_parent_stat = config_path.parent.lstat()
        helper_parent_stat = helper.parent.lstat()
        from scripts.review.isolation import _SEALED_READ_MCP_SOURCE, _has_review_temp_root_marker

        expected_helper = hashlib.sha256(_SEALED_READ_MCP_SOURCE.encode("utf-8")).hexdigest()
        observed_helper = hashlib.sha256(helper.read_bytes()).hexdigest()
    except (ImportError, OSError) as exc:
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP roots are invalid") from exc
    if (
        not helper.is_absolute()
        or not snapshot.is_absolute()
        or not stat.S_ISREG(helper_stat.st_mode)
        or not stat.S_ISDIR(snapshot_stat.st_mode)
        or not stat.S_ISDIR(config_parent_stat.st_mode)
        or not stat.S_ISDIR(helper_parent_stat.st_mode)
        or helper_stat.st_uid != os.getuid()
        or snapshot_stat.st_uid != os.getuid()
        or config_parent_stat.st_uid != os.getuid()
        or helper_parent_stat.st_uid != os.getuid()
        or helper_stat.st_mode & 0o022
        or snapshot_stat.st_mode & 0o022
        or config_parent_stat.st_mode & 0o022
        or helper_parent_stat.st_mode & 0o022
        or observed_helper != expected_helper
        or not config_path.parent.name.startswith("lu-review-write-")
        or not helper.parent.name.startswith("lu-review-exec-")
        or not snapshot.name.startswith("lu-review-view-")
        or not _has_review_temp_root_marker(config_path.parent)
        or not _has_review_temp_root_marker(helper.parent)
        or not _has_review_temp_root_marker(snapshot)
    ):
        raise AcpxShadowRefusalError(f"{adapter_label}: sealed review MCP helper/snapshot failed validation")
    return str(config_path)


def _claude_sealed_review_max_turns(config_path: str) -> int:
    """Derive Claude's exact sealed-read turn budget from parent-owned bytes.

    Claude Agent SDK defers MCP discovery behind one ToolSearch round-trip and
    externalizes large single tool results to a provider-private file.  The
    sealed protocol therefore streams one UTF-8 chunk per model round-trip;
    one final round-trip remains for the canonical verdict.  Refuse scopes
    above the helper's reviewed 64-chunk ceiling instead of granting an
    unbounded agent loop.
    """
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))
        server = config["mcpServers"][0]
        snapshot = Path(server["args"][3]).resolve(strict=True)
        manifest = json.loads(
            (snapshot / ".review-bundle" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        changed_paths = manifest["changed_paths"]
    except (IndexError, KeyError, OSError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcpxShadowRefusalError(
            "AcpxClaudeShadowAdapter: sealed review evidence manifest is invalid",
            failure_code="acp_review_evidence_invalid",
        ) from exc
    if not isinstance(changed_paths, list) or not all(
        isinstance(item, str) for item in changed_paths
    ):
        raise AcpxShadowRefusalError(
            "AcpxClaudeShadowAdapter: sealed review changed paths are invalid",
            failure_code="acp_review_evidence_invalid",
        )

    required = [".review-bundle/manifest.json", ".review-bundle/patch.diff"]
    seen = set(required)
    for raw in changed_paths:
        parsed = PurePosixPath(raw)
        if (
            not raw
            or "\\" in raw
            or parsed.is_absolute()
            or any(part in {"", ".", ".."} for part in parsed.parts)
        ):
            raise AcpxShadowRefusalError(
                "AcpxClaudeShadowAdapter: sealed review changed path is unsafe",
                failure_code="acp_review_evidence_invalid",
            )
        candidate = snapshot.joinpath(*parsed.parts)
        if candidate.is_symlink() or not candidate.exists():
            continue
        if not candidate.is_file() or raw in seen:
            raise AcpxShadowRefusalError(
                "AcpxClaudeShadowAdapter: sealed review changed path is invalid",
                failure_code="acp_review_evidence_invalid",
            )
        seen.add(raw)
        required.append(raw)

    chunk_count = 0
    effective_chunk_bytes = _CLAUDE_ACP_SEALED_READ_CHUNK_BYTES - 3
    try:
        for raw in required:
            target = snapshot.joinpath(*PurePosixPath(raw).parts)
            metadata = target.lstat()
            if not stat.S_ISREG(metadata.st_mode) or target.is_symlink():
                raise OSError("required evidence is not a regular file")
            chunk_count += max(
                1,
                (metadata.st_size + effective_chunk_bytes - 1)
                // effective_chunk_bytes,
            )
    except OSError as exc:
        raise AcpxShadowRefusalError(
            "AcpxClaudeShadowAdapter: sealed review evidence is unreadable",
            failure_code="acp_review_evidence_invalid",
        ) from exc
    if chunk_count > _CLAUDE_ACP_MAX_SEALED_READ_CHUNKS:
        raise AcpxShadowRefusalError(
            "AcpxClaudeShadowAdapter: sealed review evidence exceeds the bounded Claude ACP chunk budget",
            failure_code="acp_review_evidence_too_large",
        )
    return chunk_count + _CLAUDE_ACP_SEALED_REVIEW_TURN_OVERHEAD

# Fixed ACPX built-ins available only through the runner-owned inter-agent
# transport boundary (or its bounded discussion controller).  This is
# deliberately a small declarative registry, rather than a caller-selectable
# adapter: consumers can enumerate the proven participants without duplicating
# seat names, while each adapter below still hard-codes its one target.
ACPX_SUPPORTED_PARTICIPANTS: dict[str, dict[str, str | None]] = {
    "codex": {"seat": "acpx-codex-shadow", "agent": "codex", "model": None},
    "grok": {"seat": "acpx-grok-shadow", "agent": "grok", "model": GROK_SHADOW_MODEL},
    "claude": {
        "seat": "acpx-claude-shadow",
        "agent": "claude",
        "model": None,
    },
    "kimi": {"seat": "acpx-kimi-shadow", "agent": "kimi", "model": None},
    "kimicc": {"seat": "acpx-kimicc-shadow", "agent": "kimi", "model": "kimi-code/k3"},
    "cursor": {"seat": "acpx-cursor-shadow", "agent": "cursor", "model": None},
    "pool": {"seat": "acpx-pool-shadow", "agent": "pool", "model": None},
    "agy": {"seat": "acpx-agy-shadow", "agent": "agy", "model": AGY_ACP_MODEL},
    "glm": {"seat": "acpx-glm-shadow", "agent": "glm", "model": GLM_ACP_MODEL},
    "deepseek": {
        "seat": "acpx-deepseek-shadow",
        "agent": "deepseek",
        "model": DEEPSEEK_ACP_MODEL,
    },
}

# The adapter registry is the only source of ACP provider/model selection.
# These values describe routes that are already implemented above; they do
# not advertise an ACP route for a provider merely because it appears in the
# broader fleet catalog.  A caller may request only the exact pinned model or
# effort for a participant that has one.  Unpinned ACP built-ins intentionally
# retain their adapter-owned defaults and reject model/effort overrides.
ACPX_PARTICIPANT_CATALOG_TRANSPORTS: dict[str, str] = {
    "codex": "native_codex",
    "grok": "native_grok",
    "claude": "native_claude",
    "kimi": "native_kimi",
    "kimicc": "native_kimi",
    "cursor": "cursor",
    "pool": "opencode",
    "agy": "agy",
    "glm": "opencode",
    "deepseek": "hermes",
}
ACPX_PARTICIPANT_EFFORTS: dict[str, str] = {
    "claude": "high",
    "grok": GROK_SHADOW_EFFORT,
    "agy": "high",
    "glm": "high",
}

# Raw ACPX JSON-RPC traffic has a separate, larger bound in runner.py because
# provider protocol envelopes can be much larger than their final answer.
# Never let that envelope allowance become an answer/body allowance: this cap
# is applied after strict NDJSON parsing and before a Result can reach the
# fleet-authority receipt.
ACPX_PARSED_RESPONSE_LIMIT_BYTES = 512 * 1024
ACPX_TOOL_CALL_LIMIT = 2048


@dataclass(frozen=True)
class AcpxTransportProvenance:
    """Runner-sealed provenance for one ACP inter-agent invocation.

    It is intentionally held in a process-local context rather than caller
    supplied ``tool_config``.  The latter is adapter input and therefore must
    never be able to forge the Source/Agent/Via fields attached to the plan,
    result, or usage record.
    """

    source: str
    agent: str
    target_agent: str
    via: str = "acp"

    def metadata(self) -> dict[str, str]:
        return {"source": self.source, "agent": self.agent, "via": self.via}


# Active ACPX is deliberately not a generally selectable adapter mode.  The
# bounded discussion controller and the normal runner-owned communication
# boundary enter distinct process-local scopes immediately around a direct-only
# invocation; all ordinary runner routing continues to receive the refusal.
_ACTIVE_DISCUSSION_SCOPE: ContextVar[bool] = ContextVar("acpx_active_discussion", default=False)
_ACTIVE_COMMUNICATION_PROVENANCE: ContextVar[AcpxTransportProvenance | None] = ContextVar(
    "acpx_active_communication_provenance",
    default=None,
)


@contextmanager
def active_discussion_scope():
    """Permit exactly one controller-owned active ACPX call in this context."""
    token = _ACTIVE_DISCUSSION_SCOPE.set(True)
    try:
        yield
    finally:
        _ACTIVE_DISCUSSION_SCOPE.reset(token)


@contextmanager
def active_communication_scope(*, source: str, agent: str, target_agent: str):
    """Authorize one runner-owned normal ACP communication invocation.

    This scope does not grant filesystem, terminal, session, queue, or
    execution lifecycle access.  It only proves that the runner selected a
    fixed ACP participant and seals its provenance for the adapter plan.
    """
    validated_source = _require_local_metadata_field(
        "source",
        source,
        adapter_label="AcpxTransport",
        pattern=_SOURCE_METADATA_FIELD_RE,
    )
    if validated_source == "unknown":
        raise AcpxShadowRefusalError(
            "AcpxTransport: Source must resolve to a trusted non-unknown initiator"
        )
    validated_agent = _require_local_metadata_field(
        "agent", agent, adapter_label="AcpxTransport"
    )
    validated_target_agent = _require_local_metadata_field(
        "target_agent", target_agent, adapter_label="AcpxTransport"
    )
    token = _ACTIVE_COMMUNICATION_PROVENANCE.set(
        AcpxTransportProvenance(
            source=validated_source,
            agent=validated_agent,
            target_agent=validated_target_agent,
        )
    )
    try:
        yield
    finally:
        _ACTIVE_COMMUNICATION_PROVENANCE.reset(token)


def current_communication_provenance() -> AcpxTransportProvenance | None:
    """Return runner-sealed ACP provenance, never a caller-provided value."""
    return _ACTIVE_COMMUNICATION_PROVENANCE.get()

# Bounds for task_id/correlation_id/idempotency_key: opaque local identifiers
# used only for this adapter's own InvocationPlan.metadata (telemetry/dedup
# bookkeeping upstream of this seat). Never sent as ACP protocol flags, argv,
# or stdin, and never published to fleet-comms/dispatch authority/review
# evidence. Restricted to a safe identifier charset and a bounded length so
# a caller cannot smuggle newlines or oversized payloads into process
# metadata via these fields.
_METADATA_FIELD_MAX_LEN = 200
_METADATA_FIELD_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_SOURCE_METADATA_FIELD_RE = re.compile(r"^[A-Za-z0-9._:-]+(?:/[A-Za-z0-9._:-]+)*$")

# Real ACP `StopReason` values (agentclientprotocol/sdk schema.json
# `$defs.StopReason`). "cancelled" is recognized but handled as its own
# failure path.
_STOP_REASONS = frozenset(
    {"end_turn", "max_tokens", "max_turn_requests", "refusal", "cancelled"}
)
_STOP_REASON_CANCELLED = "cancelled"
_MISSING_STOP_REASON = object()

_USAGE_TOTAL_FIELDS = ("total_tokens", "totalTokens")
_USAGE_INPUT_FIELDS = ("input_tokens", "inputTokens")
_USAGE_OUTPUT_FIELDS = ("output_tokens", "outputTokens")
_USAGE_CONTEXT_FIELDS = ("used", "size")


def _usage_total_from_update(update: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return a usage total, or an error for an invalid exposed token field.

    ACPX exposes usage either under ``update._meta.usage`` or directly on
    the ``usage_update`` body. An explicit total is authoritative; when it
    is absent, both input and output token counts are required to calculate
    one. Standard ACP ``UsageUpdate`` instead carries ``used`` (tokens
    currently in context) and ``size`` (the total context-window capacity);
    report ``used`` and never mistake ``size`` for consumed tokens. Updates
    without any usable token count are ignored by the caller, while a present
    but non-integer or negative recognized field fails closed.
    """
    meta = update.get("_meta")
    usage: object = update
    if isinstance(meta, dict) and "usage" in meta:
        usage = meta["usage"]

    if not isinstance(usage, dict):
        return None, "usage_update carried a non-object usage payload"

    fields = (
        _USAGE_TOTAL_FIELDS
        + _USAGE_INPUT_FIELDS
        + _USAGE_OUTPUT_FIELDS
        + _USAGE_CONTEXT_FIELDS
    )
    for field in fields:
        if field not in usage:
            continue
        value = usage[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None, f"usage_update carried invalid {field}={value!r}"

    for field in _USAGE_TOTAL_FIELDS:
        if field in usage:
            return usage[field], None

    input_tokens = next((usage[field] for field in _USAGE_INPUT_FIELDS if field in usage), None)
    output_tokens = next((usage[field] for field in _USAGE_OUTPUT_FIELDS if field in usage), None)
    if input_tokens is not None and output_tokens is not None:
        return input_tokens + output_tokens, None

    has_used = "used" in usage
    has_size = "size" in usage
    if has_used or has_size:
        if not (has_used and has_size):
            return None, "usage_update must carry both used and size for standard ACP usage"
        return usage["used"], None

    return None, None


class AcpxShadowRefusalError(ValueError):
    """Raised when an ACPX shadow invocation is refused before spawn.

    Subclasses ValueError so it satisfies the AgentAdapter protocol's
    documented ``build_invocation`` contract (callers that only catch
    ValueError still work), while giving tests a precise type to assert on.
    """

    def __init__(self, message: str, *, failure_code: str = "adapter_refused") -> None:
        super().__init__(message)
        self.failure_code = failure_code


def _probe_acpx_version(binary: str) -> str:
    """Return ``<binary> --version`` output, or ``"unknown"`` on failure."""
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    observed = "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()
    return observed.splitlines()[0][:100] if proc.returncode == 0 and observed else "unknown"


def _probe_cli_help(binary: str, *args: str) -> str:
    """Return one exact command's help surface, or an empty string."""
    try:
        proc = subprocess.run(
            [binary, *args, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    return "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()


def _probe_acpx_cli_compatibility(
    binary: str,
    *,
    builtin_agent: str | None,
) -> tuple[str, tuple[str, ...]]:
    """Probe the ACPX flags and one-shot surface used by one adapter seat."""
    version = _probe_acpx_version(binary)
    root_help = _probe_cli_help(binary)
    exec_args = (builtin_agent, "exec") if builtin_agent else ("exec",)
    exec_help = _probe_cli_help(binary, *exec_args)
    missing: list[str] = []
    if not root_help:
        missing.append("root help")
    else:
        missing.extend(flag for flag in _ACPX_REQUIRED_GLOBAL_FLAGS if flag not in root_help)
        if builtin_agent and f"{builtin_agent} " not in root_help:
            missing.append(f"built-in {builtin_agent}")
    if not exec_help:
        missing.append(f"{builtin_agent + ' ' if builtin_agent else ''}exec")
    elif "--file" not in exec_help:
        missing.append("exec --file")
    return version, tuple(missing)


def _require_local_metadata_field(
    name: str,
    value: str | None,
    *,
    adapter_label: str = "AcpxAdapter",
    pattern: re.Pattern[str] = _METADATA_FIELD_RE,
) -> str:
    """Validate a local runtime-metadata identifier, or refuse before spawn.

    Applies to ``task_id``, ``correlation_id``, and ``idempotency_key``:
    each must be non-empty, bounded, and restricted to a safe local
    identifier charset. These values never leave this adapter as ACP
    protocol flags, argv, or stdin — see ``_ALLOWED_TOOL_CONFIG_KEYS``.
    """
    if value is None or not value.strip():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {name} must be a non-empty local identifier"
        )
    stripped = value.strip()
    if len(stripped) > _METADATA_FIELD_MAX_LEN:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {name} exceeds the {_METADATA_FIELD_MAX_LEN}-char "
            "bound for local metadata"
        )
    if not pattern.fullmatch(stripped):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {name}={stripped!r} must match a bounded local identifier "
            f"pattern ({pattern.pattern}); refusing to forward unsafe metadata"
        )
    return stripped


def _require_shadow_transport(*, adapter_label: str) -> None:
    transport = os.environ.get(TRANSPORT_ENV, "off").strip().lower()
    if transport != "shadow":
        raise AcpxShadowRefusalError(
            f"{adapter_label}: refusing to spawn ({TRANSPORT_ENV}={transport!r}); "
            f"set {TRANSPORT_ENV}=shadow to enable the experimental ACPX shadow seat "
            "(default is off)"
        )


def _require_discussion_transport(*, adapter_label: str) -> None:
    transport = os.environ.get(TRANSPORT_ENV, "off").strip().lower()
    if transport != "active" or not _ACTIVE_DISCUSSION_SCOPE.get():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: active ACPX is accepted only by the explicit discussion controller"
        )


def _require_shadow_tool_config(
    tool_config: dict | None,
    *,
    adapter_label: str,
    required_target: str,
) -> dict[str, Any]:
    tc = dict(tool_config or {})
    unsupported_keys = set(tc) - _ALLOWED_TOOL_CONFIG_KEYS
    if unsupported_keys:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: unsupported tool_config keys {sorted(unsupported_keys)!r}; "
            f"only {sorted(_ALLOWED_TOOL_CONFIG_KEYS)!r} are recognized"
        )
    discussion = tc.get("acpx_discussion") is True
    communication = tc.get("acpx_transport") is True
    if discussion and communication:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: acpx_discussion and acpx_transport are mutually exclusive"
        )
    if discussion:
        _require_discussion_transport(adapter_label=adapter_label)
    elif communication:
        _require_communication_transport(adapter_label=adapter_label)
    else:
        _require_shadow_transport(adapter_label=adapter_label)
        if tc.get("acpx_shadow") is not True:
            raise AcpxShadowRefusalError(
                f"{adapter_label}: tool_config must set acpx_shadow=True as an explicit "
                "per-call marker of shadow intent; the feature flag alone is not enough"
            )
    target_agent = tc.get("target_agent", required_target)
    if target_agent != required_target:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: target_agent={target_agent!r} rejected; this seat supports "
            f"exactly one ACP participant: {required_target}"
        )
    if communication:
        _require_communication_target(
            adapter_label=adapter_label,
            required_target=required_target,
        )
    return tc


def _require_active_discussion_tool_config(
    tool_config: dict | None,
    *,
    adapter_label: str,
    required_target: str,
) -> dict[str, Any]:
    """Require one controller-owned active ACP marker before spawn.

    ``acpx_discussion`` remains accepted for the existing durable discussion
    controller.  ``acpx_transport`` is the reusable normal communication
    route and additionally requires runner-sealed provenance.
    """
    tc = dict(tool_config or {})
    unsupported_keys = set(tc) - _ALLOWED_TOOL_CONFIG_KEYS
    if unsupported_keys:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: unsupported tool_config keys {sorted(unsupported_keys)!r}; "
            f"only {sorted(_ALLOWED_TOOL_CONFIG_KEYS)!r} are recognized"
        )
    discussion = tc.get("acpx_discussion") is True
    communication = tc.get("acpx_transport") is True
    if discussion == communication:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: this direct-only seat requires exactly one of "
            "acpx_discussion=True or acpx_transport=True"
        )
    if discussion:
        _require_discussion_transport(adapter_label=adapter_label)
    else:
        _require_communication_transport(adapter_label=adapter_label)
    target_agent = tc.get("target_agent", required_target)
    if target_agent != required_target:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: target_agent={target_agent!r} rejected; this seat supports "
            f"exactly one ACP participant: {required_target}"
        )
    if communication:
        _require_communication_target(
            adapter_label=adapter_label,
            required_target=required_target,
        )
    return tc


def _require_communication_transport(*, adapter_label: str) -> None:
    """Refuse normal ACP communication unless the runner sealed provenance."""
    transport = os.environ.get(TRANSPORT_ENV, "off").strip().lower()
    if transport != "active" or current_communication_provenance() is None:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: active ACPX communication requires the runner-owned "
            "transport selection boundary"
        )


def _require_communication_target(*, adapter_label: str, required_target: str) -> None:
    """Bind runner-sealed logical provenance to this adapter's fixed target."""
    provenance = current_communication_provenance()
    if provenance is None or provenance.target_agent != required_target:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: runner-sealed ACP target provenance does not match "
            f"required target {required_target!r}"
        )


def _communication_metadata() -> dict[str, str]:
    """Return immutable-by-construction provenance for plan metadata."""
    provenance = current_communication_provenance()
    return {} if provenance is None else provenance.metadata()


def _require_non_primary_worktree(cwd: Path, *, adapter_label: str) -> None:
    if _worktree_containment.classify_repo_path(cwd, cwd=cwd) == "primary_checkout":
        raise AcpxShadowRefusalError(
            f"{adapter_label}: refusing to spawn against the protected primary checkout "
            f"({cwd}); run ACPX calls from a worktree"
        )


def _require_compatible_acpx_binary(
    *,
    adapter_label: str,
    cwd: Path,
    builtin_agent: str | None,
) -> tuple[str, str]:
    """Resolve and capability-check local ACPX, sharing it with worktrees.

    A source worktree normally has no independent ``node_modules`` tree.  If
    this module's default local candidate is absent, resolve the canonical
    primary checkout from the invocation cwd and accept only that checkout's
    dependency binary. Never consult PATH or a global install.

    Tests may explicitly patch :data:`_ACPX_BINARY`; an override remains
    authoritative so an isolated test cannot accidentally borrow a developer
    checkout's installation.
    """
    candidate = _ACPX_BINARY
    main_root: Path | None = None
    if not candidate.is_file() and candidate == _DEFAULT_ACPX_BINARY:
        for discovery_root in (cwd, _REPO_ROOT):
            try:
                main_root = resolve_main_root(discovery_root)
                break
            except NotAGitRepositoryError:
                continue
        if main_root is not None:
            primary_candidate = main_root / "node_modules" / ".bin" / "acpx"
            if primary_candidate.is_file():
                candidate = primary_candidate

    if not candidate.is_file():
        primary_hint = ""
        if _ACPX_BINARY == _DEFAULT_ACPX_BINARY:
            if main_root is not None:
                primary_hint = (
                    f"; canonical primary candidate is "
                    f"{main_root / 'node_modules' / '.bin' / 'acpx'}"
                )
            else:
                primary_hint = "; cwd is not inside a Git checkout, so no canonical primary install is available"
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local acpx binary not found at {candidate}{primary_hint}; run "
            "`npm install` in the canonical primary checkout. "
            "A global/PATH acpx binary is never used as a substitute."
        )
    binary = str(candidate)
    observed_version, missing = _probe_acpx_cli_compatibility(
        binary,
        builtin_agent=builtin_agent,
    )
    if missing:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved acpx binary is incompatible with "
            f"{ACPX_CLI_COMPATIBILITY_CONTRACT!r}; missing capabilities: "
            f"{', '.join(missing)}; refusing to spawn"
        )
    return binary, observed_version


def _require_local_claude_acp_adapter(
    acpx_binary: str,
    *,
    adapter_label: str,
) -> dict[str, str]:
    """Require ACPX to resolve Claude from its installed dependency tree.

    ACPX otherwise falls back to ``npm exec --package=...`` for every Claude
    launch. The adapter is a direct project dependency so normal worktree
    calls borrow the canonical primary ``node_modules`` tree together with
    ACPX. Validate the exact package/bin surface before prompt delivery; never
    consult PATH or a package-exec cache as a substitute.
    """
    binary_path = Path(acpx_binary)
    if (
        binary_path.parent.name != ".bin"
        or binary_path.parent.parent.name != "node_modules"
    ):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: ACPX binary is not inside a project "
            "node_modules/.bin tree",
            failure_code="acp_adapter_missing",
        )
    node_modules = binary_path.parent.parent
    package_root = node_modules / "@agentclientprotocol" / "claude-agent-acp"
    manifest_path = package_root / "package.json"
    try:
        package_stat = package_root.lstat()
        manifest_stat = manifest_path.lstat()
        manifest_bytes = manifest_path.read_bytes()
    except OSError as exc:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local {_CLAUDE_ACP_PACKAGE} is missing",
            failure_code="acp_adapter_missing",
        ) from exc
    if (
        not stat.S_ISDIR(package_stat.st_mode)
        or not stat.S_ISREG(manifest_stat.st_mode)
        or package_stat.st_uid != os.getuid()
        or manifest_stat.st_uid != os.getuid()
        or package_stat.st_mode & 0o022
        or manifest_stat.st_mode & 0o022
        or len(manifest_bytes) > _CLAUDE_ACP_MANIFEST_LIMIT_BYTES
    ):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local {_CLAUDE_ACP_PACKAGE} "
            "ownership/mode/size is unsafe",
            failure_code="acp_adapter_incompatible",
        )
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local {_CLAUDE_ACP_PACKAGE} manifest is malformed",
            failure_code="acp_adapter_incompatible",
        ) from exc
    if not isinstance(manifest, dict) or manifest.get("name") != _CLAUDE_ACP_PACKAGE:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP package identity is incompatible",
            failure_code="acp_adapter_incompatible",
        )
    version = manifest.get("version")
    version_match = (
        _STRICT_SEMVER_RE.fullmatch(version) if isinstance(version, str) else None
    )
    if version_match is None:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP adapter version is not stable semver",
            failure_code="acp_adapter_incompatible",
        )
    version_tuple = tuple(int(part) for part in version_match.groups())
    if not (_CLAUDE_ACP_MIN_VERSION <= version_tuple < _CLAUDE_ACP_MAX_VERSION):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP adapter version {version!r} "
            f"is outside {CLAUDE_ACP_ADAPTER_COMPATIBILITY_CONTRACT}",
            failure_code="acp_adapter_incompatible",
        )
    package_bin = manifest.get("bin")
    relative_bin = (
        package_bin.get("claude-agent-acp") if isinstance(package_bin, dict) else None
    )
    if (
        not isinstance(relative_bin, str)
        or not relative_bin
        or Path(relative_bin).is_absolute()
        or ".." in Path(relative_bin).parts
    ):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP adapter bin mapping is incompatible",
            failure_code="acp_adapter_incompatible",
        )
    bin_path = package_root / relative_bin
    try:
        bin_stat = bin_path.lstat()
        resolved_bin = bin_path.resolve(strict=True)
        resolved_root = package_root.resolve(strict=True)
    except OSError as exc:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP adapter executable is missing",
            failure_code="acp_adapter_missing",
        ) from exc
    if (
        not stat.S_ISREG(bin_stat.st_mode)
        or bin_stat.st_uid != os.getuid()
        or bin_stat.st_mode & 0o022
        or not resolved_bin.is_relative_to(resolved_root)
    ):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: project-local Claude ACP adapter executable is unsafe",
            failure_code="acp_adapter_incompatible",
        )
    return {
        "claude_acp_adapter_version": version,
        "claude_acp_compatibility": CLAUDE_ACP_ADAPTER_COMPATIBILITY_CONTRACT,
        "claude_acp_launch_source": "installed",
    }


def _confinement_prefix_argv(
    binary: str,
    cwd: Path,
    *,
    sealed_review_mcp_config: str | None = None,
    max_turns: int = ACPX_DEFAULT_MAX_TURNS,
) -> list[str]:
    """Shared confinement, optionally admitting only sealed review tools."""
    permission_args = ["--deny-all", "--allowed-tools", ""]
    if sealed_review_mcp_config is not None:
        permission_policy = json.dumps(
            {
                # ACP agents do not agree on MCP tool spelling. Claude/Kimi
                # surface ``mcp__server__tool`` while native Grok reports
                # ``server__tool`` through its search_tool/use_tool wrapper.
                # Both spellings still name only the same parent-owned sealed
                # server; the explicit MCP config replaces ambient servers.
                "autoApprove": [
                    *_SEALED_REVIEW_TOOL_NAMES,
                    *_GROK_NATIVE_SEALED_REVIEW_TOOL_NAMES,
                ],
                "defaultAction": "deny",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        permission_args = [
            "--permission-policy",
            permission_policy,
            "--allowed-tools",
            ",".join(_SEALED_REVIEW_TOOL_NAMES),
            "--mcp-config",
            sealed_review_mcp_config,
        ]
    return [
        binary,
        "--cwd",
        str(cwd),
        "--format",
        "json",
        "--json-strict",
        "--auth-policy",
        "fail",
        "--non-interactive-permissions",
        "fail",
        "--no-fs",
        "--no-terminal",
        *permission_args,
        "--max-turns",
        str(max_turns),
        "--prompt-retries",
        "0",
    ]


_GROK_VERSION_RE = re.compile(r"\Agrok\s+(\d+\.\d+\.\d+)(?:\s|$)")


def _probe_grok_version(binary: str) -> str:
    """Return observed semver from ``<binary> --version``, or "" on failure.

    This value is telemetry only. Capability validation, not this version
    string, controls whether the adapter may spawn the CLI.
    """
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    text = (proc.stdout or "").strip()
    match = _GROK_VERSION_RE.match(text)
    return match.group(1) if match else ""


def _probe_grok_help(binary: str, *args: str) -> str:
    """Return help text for one Grok command, or "" when it is unavailable."""
    return _probe_cli_help(binary, *args)


def _probe_grok_cli_compatibility(binary: str) -> tuple[str, tuple[str, ...]]:
    """Return ``(observed_version, missing_capabilities)`` for the native CLI.

    The probe runs before every spawn so an in-place CLI upgrade is accepted
    immediately when it retains the command surface this adapter needs, and
    refused before prompt delivery when that surface changes incompatibly.
    """
    version = _probe_grok_version(binary) or "unknown"
    agent_help = _probe_grok_help(binary, "agent")
    stdio_help = _probe_grok_help(binary, "agent", "stdio")
    missing: list[str] = []
    if not agent_help:
        missing.append("agent")
    else:
        missing.extend(
            flag for flag in _GROK_REQUIRED_AGENT_FLAGS if flag not in agent_help
        )
    if not stdio_help:
        missing.append("agent stdio")
    return version, tuple(missing)


def _resolve_grok_binary() -> str:
    """Resolve the installed ``grok`` CLI to an absolute path, or refuse.

    Uses PATH lookup then ``Path.resolve()`` so the shell-safe ``--agent``
    command embeds an absolute binary. Does not fall back to inventing paths.
    """
    found = shutil.which("grok")
    if not found:
        raise AcpxShadowRefusalError(
            "AcpxGrokShadowAdapter: grok binary not found on PATH; install the "
            "native Grok CLI before using the acpx-grok-shadow seat"
        )
    resolved = Path(found).resolve()
    if not resolved.is_file():
        raise AcpxShadowRefusalError(
            f"AcpxGrokShadowAdapter: resolved grok path {resolved} is not a file"
        )
    return str(resolved)


def _require_grok_profile(*, sealed_review: bool = False) -> str:
    """Return the exact project-owned profile for this invocation."""
    profile_path = _GROK_SEALED_REVIEW_PROFILE_PATH if sealed_review else _GROK_PROFILE_PATH
    expected_sha256 = (
        _GROK_SEALED_REVIEW_PROFILE_SHA256 if sealed_review else _GROK_PROFILE_SHA256
    )
    profile_label = "sealed-review" if sealed_review else "no-tool"
    try:
        content = profile_path.read_bytes()
    except OSError as exc:
        raise AcpxShadowRefusalError(
            f"AcpxGrokShadowAdapter: required {profile_label} Grok profile unavailable at "
            f"{profile_path}: {exc}"
        ) from exc
    observed = hashlib.sha256(content).hexdigest()
    if observed != expected_sha256:
        raise AcpxShadowRefusalError(
            f"AcpxGrokShadowAdapter: {profile_label} Grok profile digest mismatch "
            f"(observed {observed!r}, expected {expected_sha256!r}); "
            "refusing to spawn with an unreviewed tool policy"
        )
    return str(profile_path)


def _build_grok_agent_command(abs_grok: str, profile_path: str) -> str:
    """Shell-safe single ``--agent`` value with required Grok argv order.

    Exact token order (parent flags before ``stdio``)::

        ABS_GROK agent --model grok-4.5 --reasoning-effort high
        --agent-profile ABS_PROFILE --no-leader stdio

    Never uses the ACPX built-in ``grok-build`` name.
    """
    return shlex.join(
        [
            abs_grok,
            "agent",
            "--model",
            GROK_SHADOW_MODEL,
            "--reasoning-effort",
            GROK_SHADOW_EFFORT,
            "--agent-profile",
            profile_path,
            "--no-leader",
            "stdio",
        ]
    )


_PROVIDER_VERSION_PATTERNS = {
    "agy": re.compile(r"^\s*(\d+\.\d+\.\d+)\s*$", re.MULTILINE),
    "opencode": re.compile(r"^\s*(\d+\.\d+\.\d+)\s*$", re.MULTILINE),
    "hermes": re.compile(r"^\s*Hermes Agent v(\d+\.\d+\.\d+)(?:\s|$)", re.MULTILINE),
}


def _probe_participant_cli_version(binary: str, executable: str) -> str:
    """Return a version anchored to the reviewed provider output format."""
    try:
        proc = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if proc.returncode != 0:
        return ""
    pattern = _PROVIDER_VERSION_PATTERNS.get(executable)
    if pattern is None:
        return ""
    match = pattern.search(f"{proc.stdout or ''}\n{proc.stderr or ''}")
    return match.group(1) if match else ""


def _probe_participant_cli_compatibility(
    binary: str,
    executable: str,
) -> tuple[str, tuple[str, ...]]:
    """Return version telemetry and missing exact command-surface features."""
    version = _probe_participant_cli_version(binary, executable) or "unknown"
    if executable == "agy":
        help_text = _probe_cli_help(binary)
        required = _AGY_REQUIRED_FLAGS
        label = "root help"
    elif executable == "opencode":
        help_text = _probe_cli_help(binary, "acp")
        required = _OPENCODE_REQUIRED_ACP_FLAGS
        label = "acp"
    elif executable == "hermes":
        help_text = _probe_cli_help(binary)
        required = _HERMES_REQUIRED_FLAGS
        label = "root help"
    else:  # pragma: no cover - internal callers pass the closed set above
        return version, ("unsupported executable",)
    if not help_text:
        return version, (label,)
    return version, tuple(flag for flag in required if flag not in help_text)


_PARTICIPANT_COMPATIBILITY_CONTRACTS = {
    "agy": AGY_CLI_COMPATIBILITY_CONTRACT,
    "opencode": OPENCODE_CLI_COMPATIBILITY_CONTRACT,
    "hermes": HERMES_CLI_COMPATIBILITY_CONTRACT,
}


def _resolve_participant_binary(
    executable: str,
    *,
    adapter_label: str,
) -> tuple[str, str]:
    """Resolve and capability-check one provider CLI before constructing argv."""
    contract = _PARTICIPANT_COMPATIBILITY_CONTRACTS[executable]
    found = shutil.which(executable)
    if not found:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {executable} binary not found on PATH; required for "
            f"compatibility contract {contract!r}"
        )
    resolved = Path(found).resolve()
    if not resolved.is_file():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved {executable} path {resolved} is not a file"
        )
    observed, missing = _probe_participant_cli_compatibility(str(resolved), executable)
    if missing:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved {executable} binary is incompatible with "
            f"{contract!r}; missing capabilities: {', '.join(missing)}; refusing to spawn"
        )
    return str(resolved), observed


def _require_text_agent(*, adapter_label: str) -> str:
    """Return the project-owned text ACP server path, or fail closed."""
    if not _TEXT_AGENT_PATH.is_file():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: required text-only ACP server missing at {_TEXT_AGENT_PATH}"
        )
    try:
        observed = hashlib.sha256(_TEXT_AGENT_PATH.read_bytes()).hexdigest()
    except OSError as exc:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: unable to read text-only ACP server at {_TEXT_AGENT_PATH}: {exc}"
        ) from exc
    if observed != _TEXT_AGENT_SHA256:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: text-only ACP server digest mismatch; refusing unreviewed "
            "confinement code"
        )
    return str(_TEXT_AGENT_PATH)


def _build_text_agent_command(
    *,
    adapter_label: str,
    provider: str,
    model: str,
    executable: str,
) -> tuple[str, str, str]:
    """Return shell-safe custom ACP command, binary, and version telemetry."""
    provider_binary, observed_version = _resolve_participant_binary(
        executable,
        adapter_label=adapter_label,
    )
    node_binary = shutil.which("node")
    if not node_binary:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: node binary not found on PATH; required by the text ACP server"
        )
    node_path = Path(node_binary).resolve()
    if not node_path.is_file():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved node path {node_path} is not a file"
        )
    command = shlex.join(
        [
            str(node_path),
            _require_text_agent(adapter_label=adapter_label),
            "--provider",
            provider,
            "--model",
            model,
            "--binary",
            provider_binary,
        ]
    )
    return command, provider_binary, observed_version


class AcpxAdapter:
    """Adapter for one read-only, stateless ``acpx codex exec`` request.

    Normal communication reaches this seat only through the runner-owned ACP
    boundary. It is not a general-purpose ACPX adapter: it only ever builds
    one invocation shape (``codex exec``, one Codex ACP participant, no tools,
    no arbitrary fs/terminal capability, no session, no queue). Every other ACPX
    capability (persistent sessions, other agents, flows, compare) is out of
    scope for this seat and structurally unreachable through this class.
    """

    name: str = "acpx-codex-shadow"
    # ACPX/codex-acp resolves its own default when --model is omitted; this
    # is a telemetry label, not a value ever passed on argv (see
    # build_invocation: --model is only emitted when the caller supplies one).
    default_model: str = "codex-acp-default"
    supported_modes: frozenset[str] = frozenset({"read-only"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        """Build the ``acpx codex exec`` invocation, or refuse before spawn.

        Refusal conditions (all raise ``AcpxShadowRefusalError``, a
        ``ValueError`` subclass), matching the approved Stage 0/1 contract's
        "reject before spawn" list:

        - the legacy shadow marker lacks ``LU_ACPX_TRANSPORT=shadow``, or the
          normal marker lacks active runner-sealed ACP provenance.
        - ``tool_config`` is missing an explicit ``acpx_shadow=True`` legacy
          marker or ``acpx_transport=True`` normal marker.
        - ``tool_config["target_agent"]`` names anything other than
          ``"codex"``.
        - ``tool_config`` carries any key outside ``_ALLOWED_TOOL_CONFIG_KEYS``.
        - ``session_id`` is not None (this seat never resumes a session).
        - ``mode`` is not ``"read-only"``.
        - ``cwd`` resolves to the protected primary checkout.
        - the resolved local binary is missing or lacks the exact ACPX
          command/flag surface used by this seat.
        - ``task_id``, ``tool_config["correlation_id"]``, or
          ``tool_config["idempotency_key"]`` is missing, blank, oversized, or
          contains characters outside the local-identifier charset (see
          ``_require_local_metadata_field``).

        ``task_id``, ``correlation_id``, and ``idempotency_key`` are local
        runtime metadata only: they are validated then stamped into
        ``InvocationPlan.metadata`` for this adapter's own bookkeeping. They
        are never turned into ACP protocol flags, never appear in ``cmd`` or
        ``stdin_payload``, and are never published to fleet-comms, dispatch
        authority, or review evidence.
        """
        if mode not in self.supported_modes:
            raise ValueError(
                f"AcpxAdapter: unsupported mode {mode!r}; only 'read-only' is permitted for the ACPX shadow seat"
            )

        tc = _require_shadow_tool_config(
            tool_config,
            adapter_label="AcpxAdapter",
            required_target="codex",
        )
        sealed_review_mcp_config = _validate_sealed_review_mcp_config(
            tc.get("sealed_review_mcp_config"),
            adapter_label="AcpxAdapter",
        )

        validated_task_id = _require_local_metadata_field("task_id", task_id)
        correlation_id = _require_local_metadata_field("correlation_id", tc.get("correlation_id"))
        idempotency_key = _require_local_metadata_field("idempotency_key", tc.get("idempotency_key"))

        if session_id is not None:
            raise AcpxShadowRefusalError(
                "AcpxAdapter: session_id must be None; the ACPX shadow seat is one-shot "
                "`exec` only and never resumes a named or persistent ACP session"
            )

        _require_non_primary_worktree(cwd, adapter_label="AcpxAdapter")
        binary, acpx_version = _require_compatible_acpx_binary(
            adapter_label="AcpxAdapter",
            cwd=cwd,
            builtin_agent="codex",
        )

        cmd: list[str] = _confinement_prefix_argv(
            binary,
            cwd,
            sealed_review_mcp_config=sealed_review_mcp_config,
        )
        if model:
            cmd.extend(["--model", model])
        if effort is not None:
            # ACPX has no reasoning-effort flag today. Per the AgentAdapter
            # protocol, adapters must warn and proceed rather than hard-fail
            # on an unsupported effort level.
            _logger.debug("AcpxAdapter: effort=%r has no ACPX flag equivalent; ignoring", effort)
        cmd.extend(["codex", "exec", "-f", "-"])

        metadata: dict[str, Any] = {
            "acpx_shadow": tc.get("acpx_transport") is not True,
            "acpx_cli_version": acpx_version,
            "acpx_cli_compatibility": ACPX_CLI_COMPATIBILITY_CONTRACT,
            "task_id": validated_task_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        }
        if tc.get("acpx_transport") is True:
            metadata["acpx_transport"] = True
            metadata.update(_communication_metadata())

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            # Non-secret selector for the existing Codex ChatGPT login. The
            # sanitizer allowlists only this literal route marker; no token is
            # read, stored, or forwarded by the controller.
            env_overrides={"ACPX_AUTH_CHAT_GPT": "1"},
            liveness_paths=(),
            metadata=metadata,
        )

    @classmethod
    def _resolve_acpx_binary(cls) -> str:
        """Resolve the project-local acpx binary path without probing.

        Kept for callers/tests that only need the path check. Compatibility
        enforcement lives in :func:`_require_compatible_acpx_binary`.
        """
        if not _ACPX_BINARY.is_file():
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: project-local acpx binary not found at {_ACPX_BINARY}; run "
                "`npm install` first. "
                "A global/PATH acpx binary is never used as a substitute."
            )
        return str(_ACPX_BINARY)

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Parse the ``--format json --json-strict`` NDJSON stream.

        Fails closed (``ok=False``) on any of: no output at all, a line that
        isn't valid JSON, a line that doesn't look like a JSON-RPC message, a
        duplicate terminal (``result``/``error``) message for the same
        request id, more than one terminal ``stopReason`` response, a
        terminal ``error`` object, a stream that ends without ever reaching
        a terminal ``stopReason``, or ``stopReason == "cancelled"``. There
        is no best-effort partial-success path — see module docstring and the
        approved contract's "must fail closed" requirement. The last valid
        ``usage_update`` token total is retained when ACPX exposes one;
        malformed token fields in such an update also fail closed.
        """
        _ = output_file, plan, call_start_time
        lines = [line for line in stdout.splitlines() if line.strip()]

        if not lines:
            return self._closed(f"acpx exec produced no NDJSON output (rc={returncode})", stderr)

        events: list[dict[str, Any]] = []
        for index, line in enumerate(lines):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                return self._closed(f"malformed NDJSON at line {index + 1}: {exc}", stderr)
            if not isinstance(event, dict) or not ({"method", "result", "error"} & event.keys()):
                return self._closed(f"unrecognized NDJSON schema at line {index + 1}", stderr)
            events.append(event)

        terminal_ids: set[Any] = set()
        duplicate = False
        message_chunks: list[str] = []
        final_error: dict[str, Any] | None = None
        final_stop_reason: object = _MISSING_STOP_REASON
        stop_reason_response_count = 0
        tokens: int | None = None
        tool_calls_by_id: dict[str, dict[str, Any]] = {}
        tool_call_order: list[str] = []

        for event in events:
            if "params" in event and not isinstance(event["params"], dict):
                return self._closed("unrecognized JSON-RPC params schema", stderr)

            if event.get("method") == "session/update":
                params = event.get("params")
                if not isinstance(params, dict):
                    return self._closed("unrecognized session/update params schema", stderr)
                update = params.get("update")
                if not isinstance(update, dict):
                    return self._closed("unrecognized session/update update schema", stderr)
                if update.get("sessionUpdate") == "agent_message_chunk":
                    content = update.get("content")
                    if not isinstance(content, dict):
                        return self._closed("unrecognized agent_message_chunk content schema", stderr)
                    text = content.get("text")
                    if isinstance(text, str):
                        message_chunks.append(text)
                elif update.get("sessionUpdate") == "usage_update":
                    usage_total, usage_error = _usage_total_from_update(update)
                    if usage_error is not None:
                        return self._closed(usage_error, stderr)
                    if usage_total is not None:
                        tokens = usage_total
                elif update.get("sessionUpdate") in {"tool_call", "tool_call_update"}:
                    tool_call_id = update.get("toolCallId")
                    if not isinstance(tool_call_id, str) or not tool_call_id:
                        return self._closed("unrecognized ACP toolCallId schema", stderr)
                    if tool_call_id not in tool_calls_by_id:
                        if len(tool_call_order) >= ACPX_TOOL_CALL_LIMIT:
                            return self._closed("ACPX tool-call trace exceeds bounded limit", stderr)
                        tool_call_order.append(tool_call_id)
                        tool_calls_by_id[tool_call_id] = {
                            "id": tool_call_id,
                            "name": "",
                            "title": "",
                            "arguments": {},
                            "result": None,
                            "status": "pending",
                        }
                    record = tool_calls_by_id[tool_call_id]
                    name = update.get("name")
                    if isinstance(name, str) and name:
                        record["name"] = name
                    title = update.get("title")
                    if isinstance(title, str) and title:
                        record["title"] = title
                    raw_input = update.get("rawInput")
                    if raw_input is not None:
                        if isinstance(raw_input, str):
                            try:
                                raw_input = json.loads(raw_input)
                            except json.JSONDecodeError:
                                raw_input = {"_raw": raw_input}
                        record["arguments"] = raw_input if isinstance(raw_input, dict) else {"_raw": raw_input}
                    status = update.get("status")
                    if isinstance(status, str) and status:
                        record["status"] = status
                    if "rawOutput" in update:
                        record["result"] = update.get("rawOutput")
                    elif "content" in update:
                        record["result"] = update.get("content")
                continue

            has_result = "result" in event
            has_error = "error" in event
            if not has_result and not has_error:
                # An echoed outgoing request (initialize, session/prompt, ...)
                # or a notification we don't track. Not a terminal marker.
                continue

            if has_result and not isinstance(event["result"], dict):
                return self._closed("unrecognized JSON-RPC result schema", stderr)
            if has_error and not isinstance(event["error"], dict):
                return self._closed("unrecognized JSON-RPC error schema", stderr)

            event_id = event.get("id")
            if event_id is not None:
                if isinstance(event_id, bool) or not isinstance(event_id, (str, int, float)):
                    return self._closed("unrecognized JSON-RPC response id schema", stderr)
                if event_id in terminal_ids:
                    duplicate = True
                terminal_ids.add(event_id)

            if has_error:
                final_error = event["error"]
            elif has_result:
                result = event["result"]
                if "stopReason" in result:
                    final_stop_reason = result["stopReason"]
                    stop_reason_response_count += 1

        if duplicate:
            return self._closed("duplicate terminal response replay detected for the same request id", stderr)

        if stop_reason_response_count > 1:
            return self._closed("multiple terminal stopReason responses detected in one-shot exec stream", stderr)

        if final_error is not None:
            if "data" in final_error and not isinstance(final_error["data"], dict):
                return self._closed("unrecognized ACPX error.data schema", stderr)
            data = final_error.get("data") or {}
            label = data.get("detailCode") or data.get("acpxCode") or "RUNTIME"
            message = final_error.get("message", "acpx error")
            if (
                label == "RUNTIME"
                and isinstance(message, str)
                and re.fullmatch(
                    r"Internal error: Reached maximum number of turns \([1-9][0-9]*\)",
                    message,
                )
            ):
                failure_code = "acp_turn_limit"
            else:
                failure_code = {
                    "AGENT_DISCONNECTED": "acp_agent_disconnected",
                    "AGENT_STARTUP_FAILED": "acp_agent_startup",
                    "AUTH_REQUIRED": "acp_auth_required",
                    "CLAUDE_ACP_SESSION_CREATE_TIMEOUT": "acp_session_create_timeout",
                    "PERMISSION_DENIED": "acp_permission_denied",
                    "PERMISSION_PROMPT_UNAVAILABLE": "acp_permission_unavailable",
                    "TIMEOUT": "timeout",
                }.get(label, "transport_error")
            return self._closed(
                f"acpx {label}: {message}",
                stderr,
                failure_code=failure_code,
            )

        if final_stop_reason is _MISSING_STOP_REASON:
            return self._closed(f"acpx exec stream ended without a terminal response (rc={returncode})", stderr)

        if not isinstance(final_stop_reason, str) or final_stop_reason not in _STOP_REASONS:
            return self._closed(
                f"unrecognized terminal stopReason schema: {final_stop_reason!r}",
                stderr,
            )

        if final_stop_reason == _STOP_REASON_CANCELLED:
            return self._closed(
                "acpx prompt turn cancelled (stopReason=cancelled)",
                stderr,
                failure_code="transport_error",
            )

        if returncode != 0:
            return self._closed(
                f"acpx exec exited rc={returncode} despite stopReason={final_stop_reason!r}",
                stderr,
                failure_code="transport_error",
            )

        response = "".join(message_chunks)
        response_bytes = len(response.encode("utf-8"))
        if response_bytes > ACPX_PARSED_RESPONSE_LIMIT_BYTES:
            return self._closed(
                "parsed ACP response exceeds "
                f"{ACPX_PARSED_RESPONSE_LIMIT_BYTES}-byte content limit "
                f"(observed={response_bytes})",
                stderr,
                failure_code="protocol_output_limit",
            )

        normalized_tool_calls: list[dict[str, Any]] = []
        for tool_call_id in tool_call_order:
            record = tool_calls_by_id[tool_call_id]
            arguments = record.get("arguments")
            if (
                isinstance(arguments, dict)
                and arguments.get("variant") == "UseTool"
                and isinstance(arguments.get("tool_name"), str)
                and arguments["tool_name"]
                and isinstance(arguments.get("tool_input"), dict)
            ):
                # Grok emits a generic ``use_tool`` ACP call whose raw input
                # contains the actual MCP operation. Normalize that wrapper
                # into the same trace shape produced by direct ACP tools so
                # sealed-evidence coverage remains provider-neutral.
                record = {
                    **record,
                    "name": arguments["tool_name"],
                    "arguments": arguments["tool_input"],
                    "result": _normalize_grok_sealed_result(
                        record.get("result"),
                        tool_name=arguments["tool_name"],
                    ),
                }
            normalized_tool_calls.append(record)

        return ParseResult(
            ok=True,
            response=response,
            stderr_excerpt=None,
            rate_limited=False,
            session_id=None,
            tokens=tokens,
            tool_calls=normalized_tool_calls,
        )

    @staticmethod
    def _closed(
        reason: str,
        stderr: str,
        *,
        failure_code: str = "result_invalid",
    ) -> ParseResult:
        """Build a fail-closed ``ParseResult`` with a bounded stderr excerpt."""
        tail = (stderr or "").strip()
        excerpt = reason if not tail else f"{reason}\n[acpx stderr]\n{tail}"
        return ParseResult(
            ok=False,
            response="",
            stderr_excerpt=excerpt[:500],
            rate_limited=False,
            session_id=None,
            tokens=None,
            tool_calls=[],
            failure_code=failure_code,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """No fallback liveness files — acpx streams NDJSON directly to stdout.

        Unlike Codex's ``-o <file>`` or Gemini's session file, ACPX's
        ``--format json`` writes every protocol event to stdout as it
        happens, so the runner's stdout streaming watchdog is a complete
        liveness signal on its own.
        """
        _ = plan
        return ()


class _AcpxDiscussionAdapter:
    """Shared implementation for one fixed ACPX discussion seat.

    A subclass either names one ACPX built-in or returns one reviewed custom
    ACP command. Callers cannot choose a participant, permissions, session,
    or pinned model through this base class.
    """

    name: str
    target_agent: str
    fixed_model: str | None = None
    allowed_models: frozenset[str] = frozenset()
    acpx_model: str | None = None
    fixed_effort: str | None = None
    forward_model_to_acpx: bool = True
    auth_env: str | None = None
    default_model: str = "acpx-built-in-default"
    supported_modes: frozenset[str] = frozenset({"read-only"})

    def _custom_agent_command(self, cwd: Path) -> tuple[str, dict[str, Any]] | None:
        _ = cwd
        return None

    def _env_overrides(
        self,
        *,
        sealed_review_mcp_config: str | None = None,
    ) -> dict[str, str]:
        _ = sealed_review_mcp_config
        return {} if self.auth_env is None else {self.auth_env: "1"}

    def _env_unsets(self) -> tuple[str, ...]:
        return ()

    def _extra_metadata(self) -> dict[str, Any]:
        return {}

    def _participant_runtime_metadata(self, acpx_binary: str) -> dict[str, str]:
        _ = acpx_binary
        return {}

    def _max_turns(self, sealed_review_mcp_config: str | None) -> int:
        _ = sealed_review_mcp_config
        return ACPX_DEFAULT_MAX_TURNS

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        if mode not in self.supported_modes:
            raise ValueError(
                f"{type(self).__name__}: unsupported mode {mode!r}; only 'read-only' is permitted"
            )
        tc = _require_active_discussion_tool_config(
            tool_config,
            adapter_label=type(self).__name__,
            required_target=self.target_agent,
        )
        sealed_review_mcp_config = _validate_sealed_review_mcp_config(
            tc.get("sealed_review_mcp_config"),
            adapter_label=type(self).__name__,
        )
        if self.fixed_model is not None and model not in {None, self.fixed_model}:
            raise AcpxShadowRefusalError(
                f"{type(self).__name__}: model={model!r} rejected; caller may only pass None "
                f"or {self.fixed_model!r}"
            )
        if self.allowed_models and model is not None and model not in self.allowed_models:
            raise AcpxShadowRefusalError(
                f"{type(self).__name__}: model={model!r} rejected; allowed pins are "
                f"{sorted(self.allowed_models)!r}"
            )
        if self.fixed_effort is not None and effort not in {None, self.fixed_effort}:
            raise AcpxShadowRefusalError(
                f"{type(self).__name__}: effort={effort!r} rejected; caller may only pass None "
                f"or {self.fixed_effort!r}"
            )
        if session_id is not None:
            raise AcpxShadowRefusalError(
                f"{type(self).__name__}: session_id must be None; this seat is one-shot `exec` only"
            )
        validated_task_id = _require_local_metadata_field(
            "task_id", task_id, adapter_label=type(self).__name__
        )
        correlation_id = _require_local_metadata_field(
            "correlation_id", tc.get("correlation_id"), adapter_label=type(self).__name__
        )
        idempotency_key = _require_local_metadata_field(
            "idempotency_key", tc.get("idempotency_key"), adapter_label=type(self).__name__
        )
        _require_non_primary_worktree(cwd, adapter_label=type(self).__name__)
        custom_agent = self._custom_agent_command(cwd)
        builtin_agent = self.target_agent if custom_agent is None else None
        binary, acpx_version = _require_compatible_acpx_binary(
            adapter_label=type(self).__name__,
            cwd=cwd,
            builtin_agent=builtin_agent,
        )
        participant_runtime_metadata = self._participant_runtime_metadata(binary)
        cmd = _confinement_prefix_argv(
            binary,
            cwd,
            sealed_review_mcp_config=sealed_review_mcp_config,
            max_turns=self._max_turns(sealed_review_mcp_config),
        )
        if self.fixed_model is not None and self.forward_model_to_acpx:
            cmd.extend(["--model", self.acpx_model or self.fixed_model])
        elif self.allowed_models:
            cmd.extend(["--model", model or self.default_model])
        if custom_agent is None:
            cmd.extend([self.target_agent, "exec", "-f", "-"])
            custom_metadata: dict[str, Any] = {}
        else:
            custom_command, custom_metadata = custom_agent
            cmd.extend(["--agent", custom_command, "exec", "-f", "-"])
        metadata: dict[str, Any] = {
            "acpx_discussion": True,
            "acpx_cli_version": acpx_version,
            "acpx_cli_compatibility": ACPX_CLI_COMPATIBILITY_CONTRACT,
            "target_agent": self.target_agent,
            "task_id": validated_task_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        }
        if tc.get("acpx_transport") is True:
            metadata["acpx_discussion"] = False
            metadata["acpx_transport"] = True
        if self.fixed_model is not None:
            metadata["model"] = self.fixed_model
        elif self.allowed_models:
            metadata["model"] = model or self.default_model
        if self.fixed_effort is not None:
            metadata["effort"] = self.fixed_effort
        metadata.update(custom_metadata)
        metadata.update(participant_runtime_metadata)
        if sealed_review_mcp_config is not None:
            metadata["tool_policy"] = "sealed-review-only"
        metadata.update(self._extra_metadata())
        if tc.get("acpx_transport") is True:
            # Keep the runner-sealed transport fields authoritative even if a
            # future adapter adds diagnostic metadata with a colliding key.
            metadata.update(_communication_metadata())
        if effort is not None and self.fixed_effort is None:
            _logger.debug("%s: effort=%r has no ACPX flag equivalent; ignoring", type(self).__name__, effort)

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            env_overrides=self._env_overrides(
                sealed_review_mcp_config=sealed_review_mcp_config,
            ),
            env_unsets=self._env_unsets(),
            liveness_paths=(),
            metadata=metadata,
        )

    def parse_response(self, **kwargs: Any) -> ParseResult:
        """Reuse the established fail-closed ACPX NDJSON parser."""
        return AcpxAdapter().parse_response(**kwargs)

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return ()


class AcpxClaudeShadowAdapter(_AcpxDiscussionAdapter):
    name = "acpx-claude-shadow"
    target_agent = "claude"
    allowed_models = CLAUDE_ACP_MODELS
    default_model = CLAUDE_ACP_MODEL
    fixed_effort = "high"

    def _max_turns(self, sealed_review_mcp_config: str | None) -> int:
        if sealed_review_mcp_config is None:
            return ACPX_DEFAULT_MAX_TURNS
        return _claude_sealed_review_max_turns(sealed_review_mcp_config)

    def _participant_runtime_metadata(self, acpx_binary: str) -> dict[str, str]:
        return _require_local_claude_acp_adapter(
            acpx_binary,
            adapter_label=type(self).__name__,
        )


class AcpxKimiShadowAdapter(_AcpxDiscussionAdapter):
    name = "acpx-kimi-shadow"
    target_agent = "kimi"
    auth_env = "ACPX_AUTH_LOGIN"


class AcpxKimiCcShadowAdapter(_AcpxDiscussionAdapter):
    name = "acpx-kimicc-shadow"
    target_agent = "kimi"
    fixed_model = "kimi-code/k3"
    default_model = fixed_model
    auth_env = "ACPX_AUTH_LOGIN"


class AcpxCursorShadowAdapter(_AcpxDiscussionAdapter):
    name = "acpx-cursor-shadow"
    target_agent = "cursor"
    auth_env = "ACPX_AUTH_CURSOR_LOGIN"


class AcpxPoolShadowAdapter(_AcpxDiscussionAdapter):
    name = "acpx-pool-shadow"
    target_agent = "pool"


class AcpxAgyShadowAdapter(_AcpxDiscussionAdapter):
    """Text-only AGY/Gemini-family ACP participant (#6158)."""

    name = "acpx-agy-shadow"
    target_agent = "agy"
    fixed_model = AGY_ACP_MODEL
    default_model = fixed_model
    fixed_effort = "high"
    forward_model_to_acpx = False

    def _custom_agent_command(self, cwd: Path) -> tuple[str, dict[str, Any]]:
        _ = cwd
        command, _binary, version = _build_text_agent_command(
            adapter_label=type(self).__name__,
            provider="agy",
            model=AGY_ACP_MODEL,
            executable="agy",
        )
        return command, {
            "provider_cli": "agy",
            "provider_cli_version": version,
            "provider_cli_compatibility": AGY_CLI_COMPATIBILITY_CONTRACT,
            "text_only_adapter": True,
        }


class AcpxGlmShadowAdapter(_AcpxDiscussionAdapter):
    """Native OpenCode ACP participant pinned to the Z.AI GLM subscription."""

    name = "acpx-glm-shadow"
    target_agent = "glm"
    fixed_model = GLM_ACP_MODEL
    acpx_model = GLM_ACP_INVOCATION_MODEL
    default_model = fixed_model
    fixed_effort = "high"

    def _custom_agent_command(self, cwd: Path) -> tuple[str, dict[str, Any]]:
        _ = cwd
        assert_glm_egress_allowed(type(self).__name__)
        binary, version = _resolve_participant_binary(
            "opencode",
            adapter_label=type(self).__name__,
        )
        return shlex.join([binary, "acp", "--pure"]), {
            "provider_cli": "opencode",
            "provider_cli_version": version,
            "provider_cli_compatibility": OPENCODE_CLI_COMPATIBILITY_CONTRACT,
            "provider_route": GLM_ACP_INVOCATION_MODEL,
            "tool_policy": "deny-all",
        }

    def _env_overrides(
        self,
        *,
        sealed_review_mcp_config: str | None = None,
    ) -> dict[str, str]:
        return {
            GLM_AUTH_OPENCODE_LOGIN_ENV: "1",
            "OPENCODE_CONFIG_CONTENT": (
                _OPENCODE_SEALED_REVIEW_CONFIG
                if sealed_review_mcp_config is not None
                else _OPENCODE_DENY_ALL_CONFIG
            ),
        }

class AcpxDeepSeekShadowAdapter(_AcpxDiscussionAdapter):
    """Text-only, first-party DeepSeek ACP participant via isolated Hermes."""

    name = "acpx-deepseek-shadow"
    target_agent = "deepseek"
    fixed_model = DEEPSEEK_ACP_MODEL
    default_model = fixed_model
    forward_model_to_acpx = False

    def _custom_agent_command(self, cwd: Path) -> tuple[str, dict[str, Any]]:
        _ = cwd
        if is_deepseek_first_party_forbidden_in_ci("deepseek", DEEPSEEK_ACP_MODEL):
            raise AcpxShadowRefusalError(
                deepseek_first_party_error(
                    provider="deepseek",
                    model=DEEPSEEK_ACP_MODEL,
                    source=type(self).__name__,
                )
            )
        command, _binary, version = _build_text_agent_command(
            adapter_label=type(self).__name__,
            provider="deepseek",
            model=DEEPSEEK_ACP_MODEL,
            executable="hermes",
        )
        return command, {
            "provider_cli": "hermes",
            "provider_cli_version": version,
            "provider_cli_compatibility": HERMES_CLI_COMPATIBILITY_CONTRACT,
            "provider_route": "deepseek",
            "text_only_adapter": True,
        }


class AcpxGrokShadowAdapter:
    """Adapter for a fixed Grok Build ACP participant via ACPX (#6043).

    Separate public class from :class:`AcpxAdapter` — not a generic
    caller-selectable multipurpose adapter. Canonical seat name is
    ``acpx-grok-shadow``; fixed per-call target is ``target_agent="grok"``.

    Builds one confined shape only:

    - project-local, compatibility-probed ``acpx``
    - custom ``--agent`` command from the absolute installed Grok binary after
      a fail-closed capability probe, never the built-in ``grok-build`` name
    - exact hash-pinned project profile with no tools plus an explicit
      write/shell/subagent/web/MCP/memory denylist
    - fixed model/effort ``grok-4.5`` / ``high`` inside that agent command
    - ``ACPX_AUTH_CACHED_TOKEN=1`` under ``--auth-policy fail``, with ambient
      XAI API-key auth selectors scrubbed
    - one-shot ``exec``, no session, deny-all / no-fs / no-terminal
    """

    name: str = "acpx-grok-shadow"
    # Fixed effective model baked into the --agent command. Telemetry must
    # report this value; callers may only pass None or the same string.
    default_model: str = GROK_SHADOW_MODEL
    supported_modes: frozenset[str] = frozenset({"read-only"})

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        """Build the confined Grok ACPX shadow invocation, or refuse before spawn.

        Refusal conditions (all raise :class:`AcpxShadowRefusalError` unless
        noted), matching the approved #6043 contract:

        - ``mode`` is not ``"read-only"`` (plain ``ValueError``)
        - the legacy shadow marker lacks ``LU_ACPX_TRANSPORT=shadow``, or the
          normal marker lacks active runner-sealed ACP provenance
        - missing ``acpx_shadow=True`` legacy marker or ``acpx_transport=True``
          normal marker, or unsupported ``tool_config`` keys
        - ``target_agent`` is not ``"grok"``
        - ``session_id`` is not None
        - ``cwd`` is the protected primary checkout
        - project-local acpx missing or lacking the required command surface
        - Grok binary missing or lacking the required command/flag surface
        - no-tool profile missing or changed from its reviewed digest
        - caller ``model`` is not ``None`` or ``grok-4.5``
        - caller ``effort`` is not ``None`` or ``high``
        - missing/blank/oversized/unsafe local metadata fields
        """
        if mode not in self.supported_modes:
            raise ValueError(
                f"AcpxGrokShadowAdapter: unsupported mode {mode!r}; only 'read-only' "
                "is permitted for the ACPX shadow seat"
            )

        tc = _require_shadow_tool_config(
            tool_config,
            adapter_label="AcpxGrokShadowAdapter",
            required_target="grok",
        )
        sealed_review_mcp_config = _validate_sealed_review_mcp_config(
            tc.get("sealed_review_mcp_config"),
            adapter_label="AcpxGrokShadowAdapter",
        )

        if model is not None and model != GROK_SHADOW_MODEL:
            raise AcpxShadowRefusalError(
                f"AcpxGrokShadowAdapter: model={model!r} rejected; caller may only pass "
                f"None or {GROK_SHADOW_MODEL!r} (effective model is always {GROK_SHADOW_MODEL!r})"
            )
        if effort is not None and effort != GROK_SHADOW_EFFORT:
            raise AcpxShadowRefusalError(
                f"AcpxGrokShadowAdapter: effort={effort!r} rejected; caller may only pass "
                f"None or {GROK_SHADOW_EFFORT!r} (effective effort is always {GROK_SHADOW_EFFORT!r})"
            )

        validated_task_id = _require_local_metadata_field(
            "task_id", task_id, adapter_label="AcpxGrokShadowAdapter"
        )
        correlation_id = _require_local_metadata_field(
            "correlation_id",
            tc.get("correlation_id"),
            adapter_label="AcpxGrokShadowAdapter",
        )
        idempotency_key = _require_local_metadata_field(
            "idempotency_key",
            tc.get("idempotency_key"),
            adapter_label="AcpxGrokShadowAdapter",
        )

        if session_id is not None:
            raise AcpxShadowRefusalError(
                "AcpxGrokShadowAdapter: session_id must be None; the ACPX shadow seat is "
                "one-shot `exec` only and never resumes a named or persistent ACP session"
            )

        _require_non_primary_worktree(cwd, adapter_label="AcpxGrokShadowAdapter")
        acpx_binary, acpx_version = _require_compatible_acpx_binary(
            adapter_label="AcpxGrokShadowAdapter",
            cwd=cwd,
            builtin_agent=None,
        )

        grok_binary = _resolve_grok_binary()
        observed_grok, missing_capabilities = _probe_grok_cli_compatibility(grok_binary)
        if missing_capabilities:
            raise AcpxShadowRefusalError(
                "AcpxGrokShadowAdapter: resolved grok binary is incompatible with "
                f"{GROK_CLI_COMPATIBILITY_CONTRACT!r}; missing capabilities: "
                f"{', '.join(missing_capabilities)}; refusing to spawn"
            )

        sealed_review = sealed_review_mcp_config is not None
        profile_path = _require_grok_profile(sealed_review=sealed_review)
        profile_sha256 = (
            _GROK_SEALED_REVIEW_PROFILE_SHA256 if sealed_review else _GROK_PROFILE_SHA256
        )
        agent_command = _build_grok_agent_command(grok_binary, profile_path)
        cmd: list[str] = _confinement_prefix_argv(
            acpx_binary,
            cwd,
            sealed_review_mcp_config=sealed_review_mcp_config,
        )
        # --agent is a single shell-safe command string. Do not combine with a
        # positional agent token (acpx grammar), and never emit built-in
        # "grok-build".
        cmd.extend(["--agent", agent_command, "exec", "-f", "-"])

        metadata: dict[str, Any] = {
            "acpx_shadow": tc.get("acpx_transport") is not True,
            "acpx_cli_version": acpx_version,
            "acpx_cli_compatibility": ACPX_CLI_COMPATIBILITY_CONTRACT,
            "grok_cli_version": observed_grok,
            "grok_cli_compatibility": GROK_CLI_COMPATIBILITY_CONTRACT,
            "grok_profile_sha256": profile_sha256,
            "target_agent": "grok",
            # Effective values are fixed; never fabricate caller-supplied
            # alternatives in telemetry.
            "model": GROK_SHADOW_MODEL,
            "effort": GROK_SHADOW_EFFORT,
            "task_id": validated_task_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        }
        if tc.get("acpx_transport") is True:
            metadata["acpx_transport"] = True
            metadata.update(_communication_metadata())
        if sealed_review:
            metadata["tool_policy"] = "sealed-review-only"

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            env_overrides={GROK_AUTH_CACHED_TOKEN_ENV: "1"},
            env_unsets=_GROK_XAI_API_KEY_ENV_UNSETS,
            liveness_paths=(),
            metadata=metadata,
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        """Parse ACPX NDJSON using the same fail-closed Codex shadow parser."""
        return AcpxAdapter().parse_response(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            output_file=output_file,
            plan=plan,
            call_start_time=call_start_time,
        )

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        """No fallback liveness files — acpx streams NDJSON directly to stdout."""
        _ = plan
        return ()
