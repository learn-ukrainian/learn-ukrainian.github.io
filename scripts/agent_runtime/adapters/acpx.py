"""AcpxAdapter — experimental read-only shadow transport for ACPX (#6027).

Wraps ``acpx codex exec`` (https://www.npmjs.com/package/acpx), a headless CLI
client for the Agent Client Protocol (ACP). This adapter is Stage 0/1 scaffolding
only: a feature-flagged, direct-only, observability seat for exactly one
read-only/stateless Codex ACP participant. It is never registered for model
selection, catalog, review eligibility, or failover (see registry.py entry
``cli_available: False``).

Contract captured empirically from the pinned local ``acpx@0.13.0`` install
(``node_modules/acpx``), not guessed:

- ``exec`` is always one-shot and never reuses a saved session or queue
  owner — confirmed by reading ``handleExec`` in ``dist/cli.js``, which calls
  ``runOnce()`` directly instead of the queue-owner path ``prompt`` uses.
  This is what makes ``codex exec`` structurally safe for a stateless,
  no-queue, non-persistent shadow call: we never need to reject "queue" or
  "session" behavior at our own layer because the CLI subcommand itself has
  none.
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

Confinement is structural, not probabilistic: every invocation this adapter
builds passes ``--deny-all --no-fs --no-terminal --allowed-tools ""
--auth-policy fail --non-interactive-permissions fail --max-turns 1
--prompt-retries 0`` unconditionally. There is no code path that can loosen
any of these — a caller cannot pass permission/tool overrides through
``tool_config`` (the adapter allowlists a fixed set of keys — shadow/target
markers plus local correlation/idempotency metadata — and rejects anything
else before spawn).

Issue: #6027
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..result import ParseResult
from .base import InvocationPlan

try:
    from scripts.guardrails import worktree_containment as _worktree_containment
except ImportError:  # pragma: no cover - stripped sys.path flavor
    from guardrails import worktree_containment as _worktree_containment  # type: ignore[import-not-found, no-redef]

_logger = logging.getLogger(__name__)

# Env var gating the experimental transport. Anything other than exactly
# "shadow" (including unset, "off", or an unrecognized value) refuses to
# spawn. There is deliberately no "on"/"live" value in Stage 0/1 — this seat
# is observability-only.
TRANSPORT_ENV = "LU_ACPX_TRANSPORT"

# Exact reviewed version. AC-PIN requires resolving ACPX at one exact
# version with a deterministic preflight — never a floating "latest".
PINNED_VERSION = "0.13.0"

# Project-local pinned binary. Deliberately NOT `shutil.which("acpx")`:
# global/PATH resolution would let an unrelated or unreviewed global acpx
# install silently take over. "No global binary authority" per the approved
# Stage 0/1 contract.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PINNED_BINARY = _REPO_ROOT / "node_modules" / ".bin" / "acpx"

# tool_config allowlist. Anything outside this set is rejected before spawn
# — this is the enforcement point for "unsupported permission/tool config"
# in the approved reject-before-spawn list. No key here can loosen
# confinement; "target_agent" can only ever be re-affirmed as "codex".
# "correlation_id"/"idempotency_key" are local runtime metadata only (see
# _require_local_metadata_field): never forwarded to the ACP wire protocol.
_ALLOWED_TOOL_CONFIG_KEYS = frozenset(
    {"acpx_shadow", "target_agent", "correlation_id", "idempotency_key"}
)

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

_USAGE_TOTAL_FIELDS = ("total_tokens", "totalTokens", "size", "used")
_USAGE_INPUT_FIELDS = ("input_tokens", "inputTokens")
_USAGE_OUTPUT_FIELDS = ("output_tokens", "outputTokens")


def _usage_total_from_update(update: dict[str, Any]) -> tuple[int | None, str | None]:
    """Return a usage total, or an error for an invalid exposed token field.

    ACPX exposes usage either under ``update._meta.usage`` or directly on
    the ``usage_update`` body. An explicit total is authoritative; when it
    is absent, both input and output token counts are required to calculate
    one. Updates without any usable total are ignored by the caller, while a
    present but non-integer or negative recognized field fails closed.
    """
    meta = update.get("_meta")
    usage: object = update
    if isinstance(meta, dict) and "usage" in meta:
        usage = meta["usage"]

    if not isinstance(usage, dict):
        return None, "usage_update carried a non-object usage payload"

    fields = _USAGE_TOTAL_FIELDS + _USAGE_INPUT_FIELDS + _USAGE_OUTPUT_FIELDS
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


def _require_local_metadata_field(name: str, value: str | None) -> str:
    """Validate a local runtime-metadata identifier, or refuse before spawn.

    Applies to ``task_id``, ``correlation_id``, and ``idempotency_key``:
    each must be non-empty, bounded, and restricted to a safe local
    identifier charset. These values never leave this adapter as ACP
    protocol flags, argv, or stdin — see ``_ALLOWED_TOOL_CONFIG_KEYS``.
    """
    if value is None or not value.strip():
        raise AcpxShadowRefusalError(f"AcpxAdapter: {name} must be a non-empty local identifier")
    stripped = value.strip()
    if len(stripped) > _METADATA_FIELD_MAX_LEN:
        raise AcpxShadowRefusalError(
            f"AcpxAdapter: {name} exceeds the {_METADATA_FIELD_MAX_LEN}-char bound for local metadata"
        )
    if not _METADATA_FIELD_RE.match(stripped):
        raise AcpxShadowRefusalError(
            f"AcpxAdapter: {name}={stripped!r} must match a bounded local identifier "
            f"pattern ({_METADATA_FIELD_RE.pattern}); refusing to forward unsafe metadata"
        )
    return stripped


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

        transport = os.environ.get(TRANSPORT_ENV, "off").strip().lower()
        if transport != "shadow":
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: refusing to spawn ({TRANSPORT_ENV}={transport!r}); "
                f"set {TRANSPORT_ENV}=shadow to enable the experimental ACPX shadow seat "
                "(default is off)"
            )

        tc = dict(tool_config or {})
        unsupported_keys = set(tc) - _ALLOWED_TOOL_CONFIG_KEYS
        if unsupported_keys:
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: unsupported tool_config keys {sorted(unsupported_keys)!r}; "
                f"only {sorted(_ALLOWED_TOOL_CONFIG_KEYS)!r} are recognized"
            )
        if tc.get("acpx_shadow") is not True:
            raise AcpxShadowRefusalError(
                "AcpxAdapter: tool_config must set acpx_shadow=True as an explicit "
                "per-call marker of shadow intent; the feature flag alone is not enough"
            )
        target_agent = tc.get("target_agent", "codex")
        if target_agent != "codex":
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: target_agent={target_agent!r} rejected; this seat supports "
                "exactly one ACP participant: codex"
            )

        validated_task_id = _require_local_metadata_field("task_id", task_id)
        correlation_id = _require_local_metadata_field("correlation_id", tc.get("correlation_id"))
        idempotency_key = _require_local_metadata_field("idempotency_key", tc.get("idempotency_key"))

        if session_id is not None:
            raise AcpxShadowRefusalError(
                "AcpxAdapter: session_id must be None; the ACPX shadow seat is one-shot "
                "`exec` only and never resumes a named or persistent ACP session"
            )

        if _worktree_containment.classify_repo_path(cwd, cwd=cwd) == "primary_checkout":
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: refusing to spawn against the protected primary checkout "
                f"({cwd}); run ACPX shadow calls from a worktree"
            )

        binary = self._resolve_pinned_binary()
        observed_version = _probe_acpx_version(binary)
        if observed_version != PINNED_VERSION:
            raise AcpxShadowRefusalError(
                f"AcpxAdapter: resolved acpx binary reports version {observed_version!r} "
                f"(expected pinned {PINNED_VERSION!r}); refusing to spawn on a version mismatch"
            )

        cmd: list[str] = [
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
            env_overrides={},
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
