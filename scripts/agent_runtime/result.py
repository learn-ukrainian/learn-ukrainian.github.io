"""Result dataclasses for the agent runtime.

Two dataclasses:

- ``ParseResult`` — returned by adapter.parse_response(). Rich typed
  result that replaces v0's separate protocol methods (detect_rate_limit,
  extract_session_id). One method returns one object; cleaner shape.
- ``Result`` — returned by runner.invoke() to callers. Carries everything
  a caller might want: response text, timing, session ID, error excerpt,
  outcome classification, and the full usage record written to disk.

Both are frozen dataclasses. Frozen = hashable, immutable, mypy-strict clean.

Issue: #1184
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from scripts.fleet_comms.contracts import ResponseEnvelope


@dataclass(frozen=True)
class AgyAttempt:
    """Body-free evidence from one invocation-bound AGY transcript (#8771)."""

    completion_reason: str | None = None
    failure_code: str | None = None
    runtime_stop_reason: str | None = None
    evidence_complete: bool = False
    kill_count: int | None = None
    excused_kill_count: int | None = None
    unexcused_kill_count: int | None = None
    unknown_command_count: int | None = None
    permission_profile_id: str | None = None
    denied_command_count: int | None = None
    denied_file_read_count: int | None = None
    denied_mcp_count: int | None = None
    executed_command_count: int | None = None
    sources_tool_names: tuple[str, ...] = ()
    cli_version: str = "unknown"


@dataclass(frozen=True)
class AgyTelemetry:
    """One shared, bounded launch history, projected at the terminal checkpoint."""

    attempts: tuple[AgyAttempt, ...] = ()
    retry_reason: str | None = None
    retry_disposition: str = "no_retry"
    accepted_attempt: int | None = None
    reroute_required: bool = False
    reroute_reason: str | None = None
    parent_task_id: str | None = None

    def __post_init__(self) -> None:
        if len(self.attempts) > 2 or any(not isinstance(attempt, AgyAttempt) for attempt in self.attempts):
            raise ValueError("agy_launch_cap_exceeded")
        if self.accepted_attempt is not None and not 1 <= self.accepted_attempt <= len(self.attempts):
            raise ValueError("agy_accepted_attempt_invalid")

    def task_fields(self) -> dict[str, Any]:
        """Keep command text, arguments and source results out of task records."""
        return {
            "agy_attempt_count": len(self.attempts),
            "agy_retry_reason": self.retry_reason,
            "agy_retry_disposition": self.retry_disposition,
            "agy_attempts": [
                {**asdict(attempt), "sources_tool_names": list(attempt.sources_tool_names)} for attempt in self.attempts
            ],
            "agy_accepted_attempt": self.accepted_attempt,
            "agy_reroute_required": self.reroute_required,
            "agy_reroute_reason": self.reroute_reason,
            "agy_parent_task_id": self.parent_task_id,
            "agy_replacement_task_id": f"{self.parent_task_id}-agy-reroute-1"
            if self.reroute_required and self.parent_task_id
            else None,
        }


@dataclass(frozen=True)
class ParseResult:
    """Adapter's interpretation of the raw subprocess output.

    Adapters return this from ``parse_response(stdout, stderr, returncode, output_file)``.
    The runner consumes it, writes a usage record, and builds the caller-facing Result.

    Fields:
        ok: True iff the adapter considers the invocation successful.
            An adapter may return ok=True with returncode != 0 if the CLI
            writes useful output despite a non-zero exit (rare but allowed).
        response: Clean text output, ready to forward to the caller.
            Empty string on failure.
        stderr_excerpt: First ~500 chars of stderr (or the output file's
            contents on error) for debugging. None if no diagnostic output.
        rate_limited: True iff the adapter's rate-limit pattern matched
            stderr or output_file contents. Drives runner's RateLimitedError.
        session_id: Provider session ID parsed from stdout, if the CLI
            exposes one. Claude and Codex do; Gemini doesn't. None otherwise.
        tokens: Prompt+completion token count if the CLI reports it. We
            deliberately leave this None when the CLI doesn't expose tokens,
            rather than invent numbers. Populated opportunistically.
        tool_calls: PII-bearing tool-call telemetry parsed from the CLI trace.
            Tool outputs include a capped summary and may include the raw
            in-memory result for downstream grounding checks. Callers must
            still treat names, arguments, and results as sensitive pipeline
            data. Arguments are source-shaped and may contain synthetic
            ``_raw`` / ``_value`` keys. Timestamps are provider strings or
            lenient ISO-8601 fallbacks.
        substitution: Non-secret route identity for harness-level fallback.
            Hermes adapters populate this with requested_provider/model and
            actual_provider/model so silent provider/model substitution cannot
            disappear between parse, usage telemetry, and delegate state.
        failure_code: Optional closed, body-free failure classification. ACP
            adapters use this to preserve diagnostics while privacy-limited
            usage records discard raw stderr and provider text. Codex sets it
            from its ``--json`` event stream: the classified terminal failure
            (``provider_policy_refusal``, ``provider_overloaded``,
            ``provider_auth``, ``provider_error``, ``rate_limited``) or
            ``provider_stream_incomplete`` when the stream proves no outcome.
            The failover classifier and delegate task records honor it.
        provider_error_text: Failure text the adapter attributes to the
            provider itself, isolated from its raw streams. None means the
            adapter makes no such claim and the failover classifier reads the
            excerpt and raw stdout/stderr. When set (even empty), the adapter's
            typed ``failure_code`` is the whole classification: the failover
            classifier reads no text at all. Codex sets it on every failure
            because its streams carry agent and tool text (#9532).
    """

    ok: bool
    response: str
    stderr_excerpt: str | None = None
    rate_limited: bool = False
    session_id: str | None = None
    tokens: int | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    substitution: dict[str, Any] | None = None
    response_envelope: ResponseEnvelope | None = None
    failure_code: str | None = None
    provider_error_text: str | None = None
    # Redacted, bounded command text for every model-owned AGY kill (#8771).
    agy_killed_commands: list[str] = field(default_factory=list)
    # Adapter-owned absence of prompt/model events; unknown is not retryable.
    agy_pre_model_failure: bool = False
    agy_attempt_count: int = 1
    agy_retry_reason: str | None = None
    agy_attempt: AgyAttempt | None = None
    agy_telemetry: AgyTelemetry | None = None


@dataclass(frozen=True)
class Result:
    """Caller-facing result from runner.invoke().

    Contains everything a caller might need, including the raw usage_record
    dict that was written to batch_state/api_usage/. Callers that want to
    make retry or backoff decisions can inspect ``rate_limited``, ``stalled``,
    and ``returncode`` directly.

    Fields:
        ok: True iff the invocation succeeded end-to-end (no exceptions,
            no stall, no hard timeout, adapter.parse_response returned ok).
        agent: Registry name of the agent that served this call.
        model: Resolved routing/accounting identity. For native Codex this is
            the configured request, not provider-observed model evidence.
        mode: Sandbox mode requested ("read-only", "workspace-write", "danger").
        response: Clean text output (empty on failure).
        stderr_excerpt: Diagnostic stderr tail on failure, None on success.
        duration_s: Wall-clock time from spawn to return, in seconds.
        session_id: Provider session ID (Claude/Codex) or None.
        rate_limited: True iff the failure was provider rate limiting.
            Mutually exclusive with stalled and hard_timeout as failure modes.
        stalled: True iff the failure was stall detection firing.
            Distinguishes "agent went silent" from "agent hit wall clock."
        returncode: Subprocess exit code, or None if killed before exit.
        effort: Resolved invocation effort / reasoning setting, or "unknown".
            Native Codex reads this from the request, not provider observation.
        cli_version: Version string from ``<agent> --version``, cached per
            process by the telemetry helpers. "unknown" on probe failure.
        usage_record: The exact dict written to batch_state/api_usage/. Callers
            can log or aggregate this. Follows the schema in design doc § 4.5.
        tool_calls: PII-bearing tool-call telemetry parsed from the CLI trace.
            Each entry has name, arguments, output_summary, timestamp, and
            may have result. Kept in memory only; do not persist or echo
            arguments or results to JSONL telemetry without redaction.
        tool_calls_total: Total tool calls surfaced by the provider trace.
            ``None`` means the provider/CLI did not expose telemetry, not
            "verified zero".
        substitution: Non-secret route identity for harness-level fallback.
            Present for adapters that can determine requested vs actual
            provider/model. When ``substituted`` is true, callers must treat
            the run as a different review/cost/egress lane.
    """

    ok: bool
    agent: str
    model: str
    mode: str
    response: str
    stderr_excerpt: str | None
    duration_s: float
    session_id: str | None
    rate_limited: bool
    stalled: bool
    returncode: int | None
    effort: str = "unknown"
    cli_version: str = "unknown"
    usage_record: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_calls_total: int | None = 0
    substitution: dict[str, Any] | None = None
    isolation_evidence: dict[str, Any] | None = None
    isolation_capability_digest: str | None = None
    isolation_prompt_digest: str | None = None
    isolation_prompt_transport: str | None = None
    response_envelope: ResponseEnvelope | None = None
    # Present only for runner-selected inter-agent ACP calls.  Source, Agent,
    # and Via are sealed by the runner, not accepted from caller metadata.
    transport_metadata: dict[str, str] | None = None
    transport_outcome: str | None = None
    # Optional provenance; absent historical records imply no provider observation.
    model_identity: dict[str, str | None] | None = None
    # The adapter's closed, body-free failure classification (ParseResult.failure_code),
    # e.g. ``provider_policy_refusal``; None on success or when unclassified.
    failure_code: str | None = None
    agy_killed_commands: list[str] = field(default_factory=list)
    agy_telemetry: AgyTelemetry | None = None
