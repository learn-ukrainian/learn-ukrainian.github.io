"""ACPX bounded read-only transport (#6027, #6043, #6078, #6130, #6158).

Wraps the project-local ``acpx@0.13.0`` headless CLI
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

Contract captured empirically from the pinned local ``acpx@0.13.0`` install
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
  (verified live against the pinned binary: a ``--timeout`` breach produced
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
  was verified live against the pinned custom ``--agent`` command: the
  selector produced a successful one-shot response, while the same runtime
  path with the selector stripped failed closed as ``AUTH_REQUIRED``.

Confinement is structural, not probabilistic: every invocation either adapter
builds passes ``--deny-all --no-fs --no-terminal --allowed-tools ""
--auth-policy fail --non-interactive-permissions fail --max-turns 1
--prompt-retries 0`` unconditionally. There is no code path that can loosen
any of these — a caller cannot pass permission/tool overrides through
``tool_config`` (the adapter allowlists a fixed set of keys — shadow/target
markers plus local correlation/idempotency metadata — and rejects anything
else before spawn).

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
import subprocess
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from pathlib import Path
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

# Exact reviewed version. AC-PIN requires resolving ACPX at one exact
# version with a deterministic preflight — never a floating "latest".
PINNED_VERSION = "0.13.0"

# Provider CLI versions validated with the text-only/native ACP participant
# recipes introduced in #6158. These custom commands are part of the protocol
# boundary, so an unreviewed CLI update fails before the prompt leaves ACPX.
PINNED_AGY_VERSION = "1.1.9"
PINNED_OPENCODE_VERSION = "1.17.13"
PINNED_HERMES_VERSION = "0.18.2"
AGY_ACP_MODEL = "gemini-3.6-flash-high"
GLM_ACP_MODEL = "glm-5.2"
GLM_ACP_INVOCATION_MODEL = "zai-coding-plan/glm-5.2"
DEEPSEEK_ACP_MODEL = "deepseek-v4-pro"
# OpenCode advertises its existing local login as ACP auth method
# ``opencode-login``. ACPX maps that method ID deterministically to this
# non-secret selector; the value is never a credential.
GLM_AUTH_OPENCODE_LOGIN_ENV = "ACPX_AUTH_OPENCODE_LOGIN"

# Project-local pinned binary. Deliberately NOT `shutil.which("acpx")`:
# global/PATH resolution would let an unrelated or unreviewed global acpx
# install silently take over. "No global binary authority" per the approved
# Stage 0/1 contract.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_PINNED_BINARY = _REPO_ROOT / "node_modules" / ".bin" / "acpx"
# Keep this separately patchable for hermetic adapter tests.  An explicit
# override is authoritative and must never silently fall back to another tree.
_PINNED_BINARY = _DEFAULT_PINNED_BINARY
_TEXT_AGENT_PATH = _REPO_ROOT / "scripts" / "agent_runtime" / "acp_text_agent.mjs"
_TEXT_AGENT_SHA256 = "42761e2bd9ab0e66f5e5779826777b46bd0761cc4673e13285e1fc37418ea679"
_OPENCODE_DENY_ALL_CONFIG = json.dumps(
    {"permission": {"*": "deny"}, "tools": {"*": False}},
    separators=(",", ":"),
    sort_keys=True,
)

# Exact reviewed native Grok CLI semver for the Grok ACPX shadow seat (#6043).
# Built-in acpx ``grok-build`` is intentionally unused: it expands to
# ``grok agent stdio`` without a place for parent flags required by Grok
# 0.2.117 (``--model`` / ``--reasoning-effort`` / ``--no-leader`` must appear
# before ``stdio``).
PINNED_GROK_VERSION = "0.2.117"
GROK_SHADOW_MODEL = "grok-4.5"
GROK_SHADOW_EFFORT = "high"
_GROK_PROFILE_PATH = _REPO_ROOT / "scripts" / "agent_runtime" / "profiles" / "acpx-grok-read-only.md"
_GROK_PROFILE_SHA256 = "5831398f7204be279e908371b5f0990d5e5e725a323091232e184083649d7158"
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
    {"acpx_shadow", "acpx_discussion", "target_agent", "correlation_id", "idempotency_key"}
)

# Fixed ACPX built-ins that are safe to expose only through the bounded
# discussion controller.  This is deliberately a small declarative registry,
# rather than a caller-selectable adapter: consumers can enumerate the proven
# participants without duplicating seat names, while each adapter below still
# hard-codes its one target.
ACPX_SUPPORTED_PARTICIPANTS: dict[str, dict[str, str | None]] = {
    "codex": {"seat": "acpx-codex-shadow", "agent": "codex", "model": None},
    "grok": {"seat": "acpx-grok-shadow", "agent": "grok", "model": GROK_SHADOW_MODEL},
    "claude": {"seat": "acpx-claude-shadow", "agent": "claude", "model": None},
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

# Active ACPX is deliberately not a generally selectable adapter mode.  The
# discussion controller enters this process-local scope immediately around a
# direct-only invocation; all other callers, including normal runner routing,
# continue to receive the shadow-only refusal.
_ACTIVE_DISCUSSION_SCOPE: ContextVar[bool] = ContextVar("acpx_active_discussion", default=False)


@contextmanager
def active_discussion_scope():
    """Permit exactly one controller-owned active ACPX call in this context."""
    token = _ACTIVE_DISCUSSION_SCOPE.set(True)
    try:
        yield
    finally:
        _ACTIVE_DISCUSSION_SCOPE.reset(token)

# Bounds for task_id/correlation_id/idempotency_key: opaque local identifiers
# used only for this adapter's own InvocationPlan.metadata (telemetry/dedup
# bookkeeping upstream of this seat). Never sent as ACP protocol flags, argv,
# or stdin, and never published to fleet-comms/dispatch authority/review
# evidence. Restricted to a safe identifier charset and a bounded length so
# a caller cannot smuggle newlines or oversized payloads into process
# metadata via these fields.
_METADATA_FIELD_MAX_LEN = 200
_METADATA_FIELD_RE = re.compile(r"^[A-Za-z0-9._:-]+$")

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


@lru_cache(maxsize=4)
def _probe_acpx_version(binary: str) -> str:
    """Return ``<binary> --version`` output, or "" on any probe failure.

    Cached per binary path (mirrors ``ClaudeAdapter._probe_claude_cli_version``)
    since every shadow invocation re-checks the pin. Returning "" on failure
    (rather than raising) lets the single version-mismatch branch in
    ``build_invocation`` handle "binary missing", "binary crashed", and
    "wrong version" uniformly — all three must fail closed the same way.
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
    return (proc.stdout or "").strip()


def _require_local_metadata_field(
    name: str,
    value: str | None,
    *,
    adapter_label: str = "AcpxAdapter",
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
    if not _METADATA_FIELD_RE.match(stripped):
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {name}={stripped!r} must match a bounded local identifier "
            f"pattern ({_METADATA_FIELD_RE.pattern}); refusing to forward unsafe metadata"
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
    active = tc.get("acpx_discussion") is True
    if active:
        _require_discussion_transport(adapter_label=adapter_label)
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
    return tc


def _require_active_discussion_tool_config(
    tool_config: dict | None,
    *,
    adapter_label: str,
    required_target: str,
) -> dict[str, Any]:
    """Require the controller-owned active discussion marker before spawn."""
    tc = dict(tool_config or {})
    unsupported_keys = set(tc) - _ALLOWED_TOOL_CONFIG_KEYS
    if unsupported_keys:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: unsupported tool_config keys {sorted(unsupported_keys)!r}; "
            f"only {sorted(_ALLOWED_TOOL_CONFIG_KEYS)!r} are recognized"
        )
    if tc.get("acpx_discussion") is not True:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: this direct-only seat requires acpx_discussion=True "
            "from the active discussion controller"
        )
    _require_discussion_transport(adapter_label=adapter_label)
    target_agent = tc.get("target_agent", required_target)
    if target_agent != required_target:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: target_agent={target_agent!r} rejected; this seat supports "
            f"exactly one ACP participant: {required_target}"
        )
    return tc


def _require_non_primary_worktree(cwd: Path, *, adapter_label: str) -> None:
    if _worktree_containment.classify_repo_path(cwd, cwd=cwd) == "primary_checkout":
        raise AcpxShadowRefusalError(
            f"{adapter_label}: refusing to spawn against the protected primary checkout "
            f"({cwd}); run ACPX shadow calls from a worktree"
        )


def _require_pinned_acpx_binary(*, adapter_label: str, cwd: Path) -> str:
    """Resolve the exact local ACPX pin, sharing the primary install with worktrees.

    A source worktree normally has no independent ``node_modules`` tree.  If
    this module's default local candidate is absent, resolve the canonical
    primary checkout from the invocation cwd and accept only that checkout's
    identically pinned binary.  Never consult PATH or a global install.

    Tests may explicitly patch :data:`_PINNED_BINARY`; an override remains
    authoritative so an isolated test cannot accidentally borrow a developer
    checkout's installation.
    """
    candidate = _PINNED_BINARY
    if not candidate.is_file() and candidate == _DEFAULT_PINNED_BINARY:
        try:
            main_root = resolve_main_root(cwd)
        except NotAGitRepositoryError:
            main_root = None
        if main_root is not None:
            primary_candidate = main_root / "node_modules" / ".bin" / "acpx"
            if primary_candidate.is_file():
                candidate = primary_candidate

    if not candidate.is_file():
        primary_hint = ""
        if _PINNED_BINARY == _DEFAULT_PINNED_BINARY:
            try:
                primary_hint = (
                    f"; canonical primary candidate is "
                    f"{resolve_main_root(cwd) / 'node_modules' / '.bin' / 'acpx'}"
                )
            except NotAGitRepositoryError:
                primary_hint = "; cwd is not inside a Git checkout, so no canonical primary install is available"
        raise AcpxShadowRefusalError(
            f"{adapter_label}: pinned binary not found at {candidate}{primary_hint}; run "
            f"`npm install acpx@{PINNED_VERSION} --save-exact --save-dev` in the canonical primary checkout. "
            "A global/PATH acpx binary is never used as a substitute."
        )
    binary = str(candidate)
    observed_version = _probe_acpx_version(binary)
    if observed_version != PINNED_VERSION:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved acpx binary reports version {observed_version!r} "
            f"(expected pinned {PINNED_VERSION!r}); refusing to spawn on a version mismatch"
        )
    return binary


def _confinement_prefix_argv(binary: str, cwd: Path) -> list[str]:
    """Shared structural confinement flags for every ACPX shadow seat."""
    return [
        binary,
        "--cwd",
        str(cwd),
        "--format",
        "json",
        "--json-strict",
        "--auth-policy",
        "fail",
        "--deny-all",
        "--non-interactive-permissions",
        "fail",
        "--no-fs",
        "--no-terminal",
        "--allowed-tools",
        "",
        "--max-turns",
        "1",
        "--prompt-retries",
        "0",
    ]


_GROK_VERSION_RE = re.compile(r"\Agrok\s+(\d+\.\d+\.\d+)(?:\s|$)")


@lru_cache(maxsize=4)
def _probe_grok_version(binary: str) -> str:
    """Return exact semver from ``<binary> --version``, or "" on any failure.

    Native Grok 0.2.117 prints ``grok 0.2.117 (<sha>)``. Wrong,
    missing, or unparseable output fails closed before prompt.
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


def _resolve_grok_binary() -> str:
    """Resolve the installed ``grok`` CLI to an absolute path, or refuse.

    Uses PATH lookup then ``Path.resolve()`` so the shell-safe ``--agent``
    command embeds an absolute binary. Does not fall back to inventing paths.
    """
    found = shutil.which("grok")
    if not found:
        raise AcpxShadowRefusalError(
            "AcpxGrokShadowAdapter: grok binary not found on PATH; install the "
            f"native Grok CLI at exact semver {PINNED_GROK_VERSION} before using "
            "the acpx-grok-shadow seat"
        )
    resolved = Path(found).resolve()
    if not resolved.is_file():
        raise AcpxShadowRefusalError(
            f"AcpxGrokShadowAdapter: resolved grok path {resolved} is not a file"
        )
    return str(resolved)


def _require_grok_profile() -> str:
    """Return the exact project-owned no-tool profile, or refuse before spawn."""
    try:
        content = _GROK_PROFILE_PATH.read_bytes()
    except OSError as exc:
        raise AcpxShadowRefusalError(
            f"AcpxGrokShadowAdapter: required no-tool Grok profile unavailable at "
            f"{_GROK_PROFILE_PATH}: {exc}"
        ) from exc
    observed = hashlib.sha256(content).hexdigest()
    if observed != _GROK_PROFILE_SHA256:
        raise AcpxShadowRefusalError(
            "AcpxGrokShadowAdapter: no-tool Grok profile digest mismatch "
            f"(observed {observed!r}, expected {_GROK_PROFILE_SHA256!r}); "
            "refusing to spawn with an unreviewed tool policy"
        )
    return str(_GROK_PROFILE_PATH)


def _build_grok_agent_command(abs_grok: str, profile_path: str) -> str:
    """Shell-safe single ``--agent`` value with required Grok 0.2.117 argv order.

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


@lru_cache(maxsize=16)
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


def _resolve_participant_binary(
    executable: str,
    *,
    adapter_label: str,
    expected_version: str,
) -> str:
    """Resolve and version-check one provider CLI before constructing argv."""
    found = shutil.which(executable)
    if not found:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: {executable} binary not found on PATH; expected exact "
            f"version {expected_version!r}"
        )
    resolved = Path(found).resolve()
    if not resolved.is_file():
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved {executable} path {resolved} is not a file"
        )
    observed = _probe_participant_cli_version(str(resolved), executable)
    if observed != expected_version:
        raise AcpxShadowRefusalError(
            f"{adapter_label}: resolved {executable} binary reports version {observed!r} "
            f"(expected pinned {expected_version!r}); refusing to spawn on a version mismatch"
        )
    return str(resolved)


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
    expected_version: str,
) -> tuple[str, str]:
    """Return shell-safe custom ACP command plus observed provider binary."""
    provider_binary = _resolve_participant_binary(
        executable,
        adapter_label=adapter_label,
        expected_version=expected_version,
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
    return command, provider_binary


class AcpxAdapter:
    """Adapter for ``acpx codex exec`` — read-only, stateless, shadow-only.

    Not a general-purpose ACPX adapter: it only ever builds one invocation
    shape (``codex exec``, one Codex ACP participant, no tools, no fs/
    terminal capability, no session, no queue). Every other ACPX capability
    (persistent sessions, other agents, flows, compare) is out of scope for
    this seat and structurally unreachable through this class.
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

        - ``LU_ACPX_TRANSPORT`` is not exactly ``"shadow"`` (unset, "off", or
          unrecognized all refuse — the flag-off rollback path).
        - ``tool_config`` is missing the explicit ``acpx_shadow=True`` marker
          (the env var alone is not sufficient per-call proof of intent).
        - ``tool_config["target_agent"]`` names anything other than
          ``"codex"``.
        - ``tool_config`` carries any key outside ``_ALLOWED_TOOL_CONFIG_KEYS``.
        - ``session_id`` is not None (this seat never resumes a session).
        - ``mode`` is not ``"read-only"``.
        - ``cwd`` resolves to the protected primary checkout.
        - the resolved local binary is missing, unversionable, or reports a
          version other than :data:`PINNED_VERSION`.
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

        validated_task_id = _require_local_metadata_field("task_id", task_id)
        correlation_id = _require_local_metadata_field("correlation_id", tc.get("correlation_id"))
        idempotency_key = _require_local_metadata_field("idempotency_key", tc.get("idempotency_key"))

        if session_id is not None:
            raise AcpxShadowRefusalError(
                "AcpxAdapter: session_id must be None; the ACPX shadow seat is one-shot "
                "`exec` only and never resumes a named or persistent ACP session"
            )

        _require_non_primary_worktree(cwd, adapter_label="AcpxAdapter")
        binary = _require_pinned_acpx_binary(adapter_label="AcpxAdapter", cwd=cwd)

        cmd: list[str] = _confinement_prefix_argv(binary, cwd)
        if model:
            cmd.extend(["--model", model])
        if effort is not None:
            # ACPX has no reasoning-effort flag today. Per the AgentAdapter
            # protocol, adapters must warn and proceed rather than hard-fail
            # on an unsupported effort level.
            _logger.debug("AcpxAdapter: effort=%r has no ACPX flag equivalent; ignoring", effort)
        cmd.extend(["codex", "exec", "-f", "-"])

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
            metadata={
                "acpx_shadow": True,
                "acpx_pinned_version": PINNED_VERSION,
                "task_id": validated_task_id,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
            },
        )

    @classmethod
    def _resolve_pinned_binary(cls) -> str:
        """Resolve the project-local acpx binary path without version probing.

        Kept for callers/tests that only need the path check. Version pin
        enforcement lives in :func:`_require_pinned_acpx_binary`.
        """
        if not _PINNED_BINARY.is_file():
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: pinned binary not found at {_PINNED_BINARY}; run "
                f"`npm install acpx@{PINNED_VERSION} --save-exact --save-dev` first. "
                "A global/PATH acpx binary is never used as a substitute."
            )
        return str(_PINNED_BINARY)

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
            return self._closed(f"acpx {label}: {message}", stderr)

        if final_stop_reason is _MISSING_STOP_REASON:
            return self._closed(f"acpx exec stream ended without a terminal response (rc={returncode})", stderr)

        if not isinstance(final_stop_reason, str) or final_stop_reason not in _STOP_REASONS:
            return self._closed(
                f"unrecognized terminal stopReason schema: {final_stop_reason!r}",
                stderr,
            )

        if final_stop_reason == _STOP_REASON_CANCELLED:
            return self._closed("acpx prompt turn cancelled (stopReason=cancelled)", stderr)

        if returncode != 0:
            return self._closed(
                f"acpx exec exited rc={returncode} despite stopReason={final_stop_reason!r}", stderr
            )

        return ParseResult(
            ok=True,
            response="".join(message_chunks),
            stderr_excerpt=None,
            rate_limited=False,
            session_id=None,
            tokens=tokens,
            tool_calls=[],
        )

    @staticmethod
    def _closed(reason: str, stderr: str) -> ParseResult:
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
    acpx_model: str | None = None
    fixed_effort: str | None = None
    forward_model_to_acpx: bool = True
    auth_env: str | None = None
    default_model: str = "acpx-built-in-default"
    supported_modes: frozenset[str] = frozenset({"read-only"})

    def _custom_agent_command(self, cwd: Path) -> str | None:
        _ = cwd
        return None

    def _env_overrides(self) -> dict[str, str]:
        return {} if self.auth_env is None else {self.auth_env: "1"}

    def _env_unsets(self) -> tuple[str, ...]:
        return ()

    def _extra_metadata(self) -> dict[str, Any]:
        return {}

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
        if self.fixed_model is not None and model not in {None, self.fixed_model}:
            raise AcpxShadowRefusalError(
                f"{type(self).__name__}: model={model!r} rejected; caller may only pass None "
                f"or {self.fixed_model!r}"
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
        binary = _require_pinned_acpx_binary(adapter_label=type(self).__name__, cwd=cwd)
        cmd = _confinement_prefix_argv(binary, cwd)
        if self.fixed_model is not None and self.forward_model_to_acpx:
            cmd.extend(["--model", self.acpx_model or self.fixed_model])
        custom_agent = self._custom_agent_command(cwd)
        if custom_agent is None:
            cmd.extend([self.target_agent, "exec", "-f", "-"])
        else:
            cmd.extend(["--agent", custom_agent, "exec", "-f", "-"])
        metadata: dict[str, Any] = {
            "acpx_discussion": True,
            "acpx_pinned_version": PINNED_VERSION,
            "target_agent": self.target_agent,
            "task_id": validated_task_id,
            "correlation_id": correlation_id,
            "idempotency_key": idempotency_key,
        }
        if self.fixed_model is not None:
            metadata["model"] = self.fixed_model
        if self.fixed_effort is not None:
            metadata["effort"] = self.fixed_effort
        metadata.update(self._extra_metadata())
        if effort is not None and self.fixed_effort is None:
            _logger.debug("%s: effort=%r has no ACPX flag equivalent; ignoring", type(self).__name__, effort)
        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            env_overrides=self._env_overrides(),
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

    def _custom_agent_command(self, cwd: Path) -> str:
        _ = cwd
        command, _binary = _build_text_agent_command(
            adapter_label=type(self).__name__,
            provider="agy",
            model=AGY_ACP_MODEL,
            executable="agy",
            expected_version=PINNED_AGY_VERSION,
        )
        return command

    def _extra_metadata(self) -> dict[str, Any]:
        return {
            "provider_cli": "agy",
            "provider_cli_pinned_version": PINNED_AGY_VERSION,
            "text_only_adapter": True,
        }


class AcpxGlmShadowAdapter(_AcpxDiscussionAdapter):
    """Native OpenCode ACP participant pinned to the Z.AI GLM subscription."""

    name = "acpx-glm-shadow"
    target_agent = "glm"
    fixed_model = GLM_ACP_MODEL
    acpx_model = GLM_ACP_INVOCATION_MODEL
    default_model = fixed_model

    def _custom_agent_command(self, cwd: Path) -> str:
        _ = cwd
        assert_glm_egress_allowed(type(self).__name__)
        binary = _resolve_participant_binary(
            "opencode",
            adapter_label=type(self).__name__,
            expected_version=PINNED_OPENCODE_VERSION,
        )
        return shlex.join([binary, "acp", "--pure"])

    def _env_overrides(self) -> dict[str, str]:
        return {
            GLM_AUTH_OPENCODE_LOGIN_ENV: "1",
            "OPENCODE_CONFIG_CONTENT": _OPENCODE_DENY_ALL_CONFIG,
        }

    def _extra_metadata(self) -> dict[str, Any]:
        return {
            "provider_cli": "opencode",
            "provider_cli_pinned_version": PINNED_OPENCODE_VERSION,
            "provider_route": GLM_ACP_INVOCATION_MODEL,
            "tool_policy": "deny-all",
        }


class AcpxDeepSeekShadowAdapter(_AcpxDiscussionAdapter):
    """Text-only, first-party DeepSeek ACP participant via isolated Hermes."""

    name = "acpx-deepseek-shadow"
    target_agent = "deepseek"
    fixed_model = DEEPSEEK_ACP_MODEL
    default_model = fixed_model
    forward_model_to_acpx = False

    def _custom_agent_command(self, cwd: Path) -> str:
        _ = cwd
        if is_deepseek_first_party_forbidden_in_ci("deepseek", DEEPSEEK_ACP_MODEL):
            raise AcpxShadowRefusalError(
                deepseek_first_party_error(
                    provider="deepseek",
                    model=DEEPSEEK_ACP_MODEL,
                    source=type(self).__name__,
                )
            )
        command, _binary = _build_text_agent_command(
            adapter_label=type(self).__name__,
            provider="deepseek",
            model=DEEPSEEK_ACP_MODEL,
            executable="hermes",
            expected_version=PINNED_HERMES_VERSION,
        )
        return command

    def _extra_metadata(self) -> dict[str, Any]:
        return {
            "provider_cli": "hermes",
            "provider_cli_pinned_version": PINNED_HERMES_VERSION,
            "provider_route": "deepseek",
            "text_only_adapter": True,
        }


class AcpxGrokShadowAdapter:
    """Adapter for a fixed Grok Build ACP participant via ACPX (#6043).

    Separate public class from :class:`AcpxAdapter` — not a generic
    caller-selectable multipurpose adapter. Canonical seat name is
    ``acpx-grok-shadow``; fixed per-call target is ``target_agent="grok"``.

    Builds one confined shape only:

    - project-local ``acpx@0.13.0``
    - custom ``--agent`` command from the absolute installed Grok binary at
      exact semver :data:`PINNED_GROK_VERSION`, never the built-in
      ``grok-build`` name
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
        - ``LU_ACPX_TRANSPORT`` is not exactly ``"shadow"``
        - missing ``acpx_shadow=True`` or unsupported ``tool_config`` keys
        - ``target_agent`` is not ``"grok"``
        - ``session_id`` is not None
        - ``cwd`` is the protected primary checkout
        - project-local acpx missing / wrong version
        - Grok binary missing / wrong / unparseable version
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
        acpx_binary = _require_pinned_acpx_binary(adapter_label="AcpxGrokShadowAdapter", cwd=cwd)

        grok_binary = _resolve_grok_binary()
        observed_grok = _probe_grok_version(grok_binary)
        if observed_grok != PINNED_GROK_VERSION:
            raise AcpxShadowRefusalError(
                f"AcpxGrokShadowAdapter: resolved grok binary reports version "
                f"{observed_grok!r} (expected pinned {PINNED_GROK_VERSION!r}); "
                "refusing to spawn on a version mismatch"
            )

        profile_path = _require_grok_profile()
        agent_command = _build_grok_agent_command(grok_binary, profile_path)
        cmd: list[str] = _confinement_prefix_argv(acpx_binary, cwd)
        # --agent is a single shell-safe command string. Do not combine with a
        # positional agent token (acpx grammar), and never emit built-in
        # "grok-build".
        cmd.extend(["--agent", agent_command, "exec", "-f", "-"])

        return InvocationPlan(
            cmd=cmd,
            cwd=cwd,
            stdin_payload=prompt,
            output_file=None,
            env_overrides={GROK_AUTH_CACHED_TOKEN_ENV: "1"},
            env_unsets=_GROK_XAI_API_KEY_ENV_UNSETS,
            liveness_paths=(),
            metadata={
                "acpx_shadow": True,
                "acpx_pinned_version": PINNED_VERSION,
                "grok_pinned_version": PINNED_GROK_VERSION,
                "grok_profile_sha256": _GROK_PROFILE_SHA256,
                "target_agent": "grok",
                # Effective values are fixed; never fabricate caller-supplied
                # alternatives in telemetry.
                "model": GROK_SHADOW_MODEL,
                "effort": GROK_SHADOW_EFFORT,
                "task_id": validated_task_id,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
            },
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
