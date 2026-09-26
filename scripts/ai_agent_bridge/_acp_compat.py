"""Thin compatibility shims from legacy ``ask-*`` names to ACP transport.

Provider execution is deliberately absent.  The command name selects only a
registered ACP participant; the runner seals Source/Agent/Via and refuses any
unknown route before spawning.  Fleet-comms persistence is layered by the
authority controller, never by a provider-specific bridge module.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

from ._config import REPO_ROOT

_TARGETS = {
    "claude": "claude",
    "codex": "codex",
    "agy": "agy",
    "gemini": "agy",
    "hermes": "deepseek",
    "deepseek": "deepseek",
    "pool": "pool",
    "glm": "glm",
    "gemma": "gemma",
    "cursor": "cursor",
    "grok": "grok",
    "grok-build": "grok",
    "kimi": "kimi",
}


def require_compat_target(command_target: str) -> str:
    """Resolve a legacy command name before any sender or payload work."""
    try:
        return _TARGETS[command_target]
    except KeyError as exc:
        raise ValueError(
            f"legacy ask target {command_target!r} has no enabled ACP route"
        ) from exc


def registered_participant_model(participant: str) -> str | None:
    """Return the live model pin for an ACP participant from the adapter registry.

    The registry (``ACPX_SUPPORTED_PARTICIPANTS``) is the single source of
    truth the route resolver enforces; consumers must read it instead of
    carrying an independently hardcoded slug that goes stale on every model
    rotation (#6894). Returns None for unknown or deliberately unpinned seats.
    """
    from agent_runtime.adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    entry = ACPX_SUPPORTED_PARTICIPANTS.get(participant)
    if not entry:
        return None
    model = entry.get("model")
    return str(model) if model else None


def resolve_compat_model(command_target: str, model: str | None) -> str | None:
    """Resolve a legacy ``--model`` value against the live participant registry.

    ``None`` stays ``None`` so the route resolver applies the participant's
    registered pin — a default can never drift from the registry (#6894).
    Display spellings of the registered pin are accepted. An explicit Gemini
    model that is not that pin cannot be honored on the AGY ACP seat, so fail
    with the supported headless dispatch route instead of silently downgrading.
    """
    participant = require_compat_target(command_target)
    if not model:
        return None
    if participant == "agy":
        pin = registered_participant_model("agy")
        if model.strip().lower().startswith("gemini"):
            from agent_runtime.adapters.agy import AgyAdapter, unknown_model_suggestion

            accepted_model = AgyAdapter.resolve_model_slug(model)
            if not pin:
                raise ValueError(
                    "AGY ACP has no registered model pin; cannot honor explicit "
                    f"model {model!r}. A model accepted by AGY is "
                    f"`{accepted_model or AgyAdapter.default_model}`."
                )
            if AgyAdapter.model_ids_match(model, pin) or (
                accepted_model
                and "flash" in accepted_model
                and AgyAdapter.is_legacy_model_alias(model)
            ):
                return pin
            if accepted_model is None:
                message = f"Unknown AGY model {model!r}; cannot honor the explicit request."
                message += f" {unknown_model_suggestion(model)}"
                raise ValueError(message)
            raise ValueError(
                f"AGY ACP supports only its registered model pin {pin!r}; "
                f"cannot honor explicit model {model!r}. Use "
                f"`delegate.py dispatch --agent agy --model {accepted_model}` "
                "to run a model accepted by AGY."
            )
    return model


# Per-seat default hard timeouts for compat asks (#6877). The generic 300s
# ceiling is mis-sized for Kimi: K3 is a max-effort-only model whose long
# deliberation before first output is designed behavior, and the fleet routes
# hard reviews to this seat — a live CF review was killed at exactly 300.0s
# and completed in ~10+ min only when retried with --no-timeout. Kimi gets a
# 1800s profile aligned with that review workload; every other seat keeps the
# generic default (none of the remaining compat seats is max-effort-only —
# claude/grok/agy/glm/deepseek are pinned at "high"). ``--no-timeout``
# (86400s) is unchanged and bypasses every profile.
ASK_HARD_TIMEOUT_DEFAULT_S = 300
ASK_HARD_TIMEOUT_PROFILES: dict[str, int] = {
    "kimi": 1800,
}


def ask_hard_timeout(command_target: str) -> int:
    """Default hard timeout in seconds for one compat ask to this seat (#6877)."""
    return ASK_HARD_TIMEOUT_PROFILES.get(command_target, ASK_HARD_TIMEOUT_DEFAULT_S)


_FALLBACK_SUBS_PATH = REPO_ROOT / "scripts" / "config" / "agent_fallback_substitutions.yaml"

# Post-#8655 a provider quota/rate-limit refusal arrives as a parsed ACP error
# whose bounded diagnostic keeps the provider's own words (e.g. "acpx RUNTIME:
# provider quota exhausted"); the acpx parser deliberately stays schema-only,
# so its typed failure code for such a refusal is the generic transport
# bucket. The capacity decision here is therefore typed-first (#8499): a
# specific parser code (auth, schema, network, permission, ...) decides the
# class on its own and never falls back to message text — the parser may
# append acpx stderr to the excerpt, and stderr can mention "quota" for
# unrelated reasons. Only when there is no typed code at all, or the code is
# the parser's untyped catch-all, does the provider's own capacity wording
# decide, matched on the exact phrasings the adapter rate-limit regexes and
# the runner failover classifier emit — never a bare "quota" substring.
_PROVIDER_CAPACITY_RE = re.compile(
    r"rate[ _-]?limit|usage limit|quota (?:exceeded|exhausted)|too many requests|"
    r"resource[_ ]?exhausted|\b429\b",
    re.IGNORECASE,
)

# Closed failure-code vocabulary (runner._SAFE_ACP_FAILURE_CODES). Only
# "rate_limited" is a provider-capacity class; the generic buckets carry no
# class information, so only they may fall back to the provider's wording.
_CAPACITY_FAILURE_CODES = frozenset({"rate_limited"})
_GENERIC_FAILURE_CODES = frozenset({"transport_error", "unknown"})


def _result_failure_code(result: object) -> str | None:
    usage_record = getattr(result, "usage_record", None)
    code = usage_record.get("failure_code") if isinstance(usage_record, dict) else None
    return str(code) if code else None


def _quota_failure_reason(*, error: BaseException | None = None, result: object | None = None) -> str | None:
    """Return the quota/rate-limit class of one failed ask, or None.

    Only provider-capacity failures count, decided typed-first: the runner's
    rate-limit classification (exception, result flag, transport outcome) or
    a typed capacity failure code from the parser. A specific non-capacity
    code (auth, schema, network, ...) is authoritative — such failures keep
    their original behavior even when the bounded excerpt mentions quota.
    Only with no typed code at all, or the parser's untyped catch-all bucket,
    does the provider's own capacity wording in the excerpt decide. Timeouts,
    admission refusals, and parse failures never substitute.
    """
    if error is not None:
        if type(error).__name__ == "RateLimitedError":
            return "rate_limited"
        return None
    if result is None:
        return None
    if bool(getattr(result, "rate_limited", False)):
        return "rate_limited"
    outcome = str(getattr(result, "transport_outcome", "") or "").casefold()
    if outcome == "rate_limited":
        return "rate_limited"
    code = _result_failure_code(result)
    if code is not None and code not in _GENERIC_FAILURE_CODES:
        return "rate_limited" if code in _CAPACITY_FAILURE_CODES else None
    if _PROVIDER_CAPACITY_RE.search(str(getattr(result, "stderr_excerpt", "") or "")):
        return "provider_quota"
    return None


def _resolve_quota_substitution(seat: str, reason: str, *, already_substituted: bool) -> str | None:
    """Return the mapped ACP substitute seat, or None with a loud stderr note.

    At most one substitution per ask (#8499): a substitute that is itself out
    of quota fails loudly — no second hop, and never a bridge or provider
    fallback (fleet-comms-coordination ACP-only route policy).
    """
    if already_substituted:
        print(
            f"ACP substitution exhausted: substitute seat '{seat}' is also over "
            f"quota/rate-limited (reason: {reason}); refusing a second substitution "
            "and any bridge/provider fallback.",
            file=sys.stderr,
        )
        return None
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    substitute = load_dispatch_fallbacks(_FALLBACK_SUBS_PATH).get(seat)
    if not substitute or substitute == seat:
        print(
            f"ACP seat '{seat}' is over quota/rate-limited (reason: {reason}) and "
            "agent_fallback_substitutions.yaml dispatch_fallbacks has no substitute "
            "for it; failing without bridge/provider fallback.",
            file=sys.stderr,
        )
        return None
    if substitute not in set(_TARGETS.values()):
        print(
            f"ACP seat '{seat}' is over quota/rate-limited (reason: {reason}) but "
            f"dispatch_fallbacks maps it to '{substitute}', which is not an enabled "
            "ACP ask seat; failing without bridge/provider fallback.",
            file=sys.stderr,
        )
        return None
    return substitute


def _announce_substitution(
    from_seat: str,
    to_seat: str,
    reason: str,
    *,
    model: str | None,
    effort: str | None,
) -> dict[str, str]:
    """Emit the operator-visible substitution line and return the record."""
    note = f"ACP substitution: {from_seat} -> {to_seat} (reason: {reason})"
    if model or effort:
        note += "; explicit model/effort overrides dropped — the substitute's registered pins apply"
    print(note, file=sys.stderr)
    return {"from": from_seat, "to": to_seat, "reason": reason}


def _with_substitution_record(result: object, substitution: dict[str, str]) -> object:
    """Stamp the seat substitution on a returned Result; other shapes pass through."""
    from dataclasses import replace

    try:
        return replace(result, substitution=substitution)
    except TypeError:
        return result


def _result_receipt(
    result: object,
    *,
    model_requested: str | None = None,
    effort_requested: str | None = None,
    substitution: dict[str, str] | None = None,
) -> bytes:
    actual_model = str(getattr(result, "model", ""))
    raw_effort = getattr(result, "effort", None)
    if raw_effort is None or raw_effort == "unknown":
        effort_applied = None
        effort_str = "unknown"
    else:
        effort_applied = str(raw_effort)
        effort_str = effort_applied
    payload = {
        "ok": bool(getattr(result, "ok", False)),
        "agent": str(getattr(result, "agent", "")),
        "model": actual_model,
        "response": str(getattr(result, "response", "")),
        "stderr_excerpt": getattr(result, "stderr_excerpt", None),
        "duration_s": float(getattr(result, "duration_s", 0.0)),
        "returncode": getattr(result, "returncode", None),
        "effort": effort_str,
        "from_model": actual_model,
        "model_requested": model_requested or actual_model,
        "effort_requested": effort_requested,
        "effort_applied": effort_applied,
        "harness": "acp",
        "transport_metadata": getattr(result, "transport_metadata", None),
        "transport_outcome": getattr(result, "transport_outcome", None),
    }
    if substitution is not None:
        payload["substitution"] = substitution
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _replay_result(raw: bytes) -> object:
    from agent_runtime.result import Result

    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("terminal ACP result receipt is not an object")
    if "ok" not in payload:
        error_type = str(payload.get("error") or "unknown_error")
        payload = {
            "ok": False,
            "agent": payload.get("agent", ""),
            "model": payload.get("model", ""),
            "response": "",
            "stderr_excerpt": f"replayed ACP terminal failure: {error_type}",
            "duration_s": payload.get("duration_s", 0.0),
            "returncode": payload.get("returncode", 1),
            "effort": payload.get("effort", "unknown"),
            "transport_metadata": payload.get("transport_metadata"),
            "transport_outcome": payload.get("transport_outcome", "error"),
        }
    actual_model = str(payload.get("from_model") or payload.get("model") or "acp-bridge-error")
    if "effort_applied" in payload:
        applied_effort = payload["effort_applied"]
    elif payload.get("effort") not in {None, "unknown"}:
        applied_effort = payload["effort"]
    else:
        applied_effort = None
    provenance = {
        "from_model": actual_model,
        "model_requested": payload.get("model_requested") or actual_model,
        "effort_requested": payload.get("effort_requested"),
        "effort_applied": applied_effort,
        "harness": payload.get("harness") or "acp",
    }
    provenance.update({"replayed": True, "transport": "acp"})
    substitution = payload.get("substitution")
    if not isinstance(substitution, dict):
        substitution = None
    if substitution is not None:
        provenance["substitution"] = substitution
    if not payload["ok"]:
        return Result(
            ok=False,
            agent=str(payload["agent"]),
            model=str(payload["model"]),
            mode="read-only",
            response=str(payload["response"]),
            stderr_excerpt=payload.get("stderr_excerpt"),
            duration_s=float(payload["duration_s"]),
            session_id=None,
            rate_limited=payload.get("transport_outcome") == "rate_limited",
            stalled=False,
            returncode=payload.get("returncode"),
            effort=str(payload["effort"]),
            usage_record=provenance,
            substitution=substitution,
            transport_metadata=payload.get("transport_metadata"),
            transport_outcome=payload.get("transport_outcome"),
        )
    return Result(
        ok=True,
        agent=str(payload["agent"]),
        model=str(payload["model"]),
        mode="read-only",
        response=str(payload["response"]),
        stderr_excerpt=payload.get("stderr_excerpt"),
        duration_s=float(payload["duration_s"]),
        session_id=None,
        rate_limited=payload.get("transport_outcome") == "rate_limited",
        stalled=False,
        returncode=payload.get("returncode"),
        effort=str(payload["effort"]),
        usage_record=provenance,
        substitution=substitution,
        transport_metadata=payload.get("transport_metadata"),
        transport_outcome=payload.get("transport_outcome"),
    )


def _failure_metadata(
    *, error: BaseException | None = None, result: object | None = None
) -> dict[str, object]:
    """Classify a terminal ACP failure without persisting free text."""
    if error is not None:
        error_name = type(error).__name__
        error_text = str(error).casefold()
        if error_name in {"AgentTimeoutError", "AgentStalledError"}:
            return {"phase": "transport", "code": "timeout", "retryable": True}
        if error_name == "RateLimitedError":
            return {"phase": "provider", "code": "rate_limited", "retryable": True}
        if error_name == "AgentUnavailableError":
            return {
                "phase": "provider",
                "code": "provider_unavailable",
                "retryable": True,
            }
        if error_name == "AgentOutputLimitError":
            return {
                "phase": "transport",
                "code": "protocol_output_limit",
                "retryable": False,
            }
        if "protected primary checkout" in error_text:
            return {
                "phase": "admission",
                "code": "primary_cwd_rejected",
                "retryable": False,
            }
        if "model pin" in error_text or "registered model" in error_text:
            return {
                "phase": "admission",
                "code": "route_model_conflict",
                "retryable": False,
            }
        if "effort pin" in error_text or "registered effort" in error_text:
            return {
                "phase": "admission",
                "code": "route_effort_conflict",
                "retryable": False,
            }
        if "state event" in error_text or "initial state" in error_text:
            return {
                "phase": "admission",
                "code": "conversation_state_missing",
                "retryable": False,
            }
        if error_name in {"AcpxShadowRefusalError", "AcpExecutionWorkspaceError"}:
            return {
                "phase": "admission",
                "code": "adapter_refused",
                "retryable": False,
            }
        return {"phase": "transport", "code": "transport_error", "retryable": False}

    outcome = str(getattr(result, "transport_outcome", "") or "").casefold()
    if outcome == "non_evidentiary":
        # Review-ask outcome validation (#6805): the provider replied, but the
        # reply carries no verdict grounded in evidence. Not retryable in
        # place — the idempotency key would replay the same garbage; re-ask
        # with a fresh task-id or reroute the seat.
        return {"phase": "postprocess", "code": "non_evidentiary", "retryable": False}
    if outcome == "rate_limited" or bool(getattr(result, "rate_limited", False)):
        return {"phase": "provider", "code": "rate_limited", "retryable": True}
    code = _result_failure_code(result)
    if code in _CAPACITY_FAILURE_CODES:
        return {"phase": "provider", "code": "rate_limited", "retryable": True}
    # Post-#8655 a provider quota refusal parses into the parser's untyped
    # catch-all whose excerpt keeps the provider's words; record the durable
    # failure under the capacity class the substitution decision used. A
    # specific typed code below is authoritative on its own — acpx stderr
    # appended to the excerpt mentioning quota never reclassifies an
    # auth/schema/network failure.
    if (code is None or code in _GENERIC_FAILURE_CODES) and _PROVIDER_CAPACITY_RE.search(
        str(getattr(result, "stderr_excerpt", "") or "")
    ):
        return {"phase": "provider", "code": "rate_limited", "retryable": True}
    if code == "protocol_output_limit":
        return {"phase": "transport", "code": code, "retryable": False}
    if code == "timeout":
        return {"phase": "transport", "code": code, "retryable": True}
    if code == "provider_unavailable":
        return {"phase": "provider", "code": code, "retryable": True}
    if code == "adapter_refused":
        return {"phase": "admission", "code": code, "retryable": False}
    if code == "transport_error":
        return {"phase": "transport", "code": code, "retryable": False}
    return {"phase": "result_parse", "code": "result_invalid", "retryable": False}


def _discussion_failure_metadata(payload: object) -> dict[str, object]:
    """Classify a non-complete discussion from its bounded outcome vocabulary."""
    outcomes: set[str] = set()
    if isinstance(payload, dict):
        rows = payload.get("participant_outcomes")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("outcome"), str):
                    outcomes.add(row["outcome"].casefold())
    if "timeout" in outcomes or "stalled" in outcomes:
        return {"phase": "transport", "code": "timeout", "retryable": True}
    if "rate_limited" in outcomes:
        return {"phase": "provider", "code": "rate_limited", "retryable": True}
    if "error" in outcomes:
        return {"phase": "provider", "code": "unknown", "retryable": False}
    return {"phase": "postprocess", "code": "result_invalid", "retryable": False}


# Review-ask outcome validation (#6805): transport-ok must not mask an
# unusable review reply (the ask-glm garble and the phantom AGY findings on
# the issue both terminalized as outcome=ok). Cheap and deterministic — no
# LLM judge in the transport layer: a review reply must name a VERDICT and
# ground it in at least one concrete artifact reference (a finding/evidence
# line, a path[:line], a #PR/issue, or a commit SHA), else the ask
# terminalizes as failed:non_evidentiary rather than a silent "replied".
_REVIEW_VERDICT_RE = re.compile(r"\bverdict\b", re.IGNORECASE)
_REVIEW_EVIDENCE_RE = re.compile(
    r"(?:\bfindings?\b"  # an explicit finding statement
    r"|\bevidence\b"  # an explicit evidence statement
    r"|[\w.-]+/[\w./-]*\.\w{1,6}(?::\d+)?"  # path/to/file.ext[:line]
    r"|\b[\w.-]+\.\w{1,6}:\d+"  # file.ext:line
    r"|#\d{2,}"  # PR/issue reference
    r"|\b(?=[0-9a-f]*\d)[0-9a-f]{7,40}\b)",  # commit SHA (must contain a digit)
    re.IGNORECASE,
)


def review_outcome_failure(response: str) -> str | None:
    """Return the failure reason when a review-type reply is non-evidentiary."""
    if not _REVIEW_VERDICT_RE.search(response):
        return (
            "non-evidentiary review reply: no VERDICT token; transport-ok does "
            "not count as a completed review (#6805)"
        )
    if not _REVIEW_EVIDENCE_RE.search(response):
        return (
            "non-evidentiary review reply: no finding/evidence line or concrete "
            "artifact reference (path[:line], #PR, or commit SHA) grounding the "
            "verdict (#6805)"
        )
    return None


def _non_evidentiary_result(result: object, reason: str) -> object:
    """Downgrade a transport-ok review reply to a durable failure receipt.

    The reply body is preserved on the result for forensics; only the outcome
    changes so the authority job terminalizes as failed:non_evidentiary.
    """
    from dataclasses import replace

    return replace(
        result,
        ok=False,
        stderr_excerpt=reason,
        transport_outcome="non_evidentiary",
    )


def _idempotency_key(
    *, participant: str, task_id: str, content: str, model: str | None, effort: str | None
) -> str:
    payload = json.dumps(
        {
            "participant": participant,
            "task_id": task_id,
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "model": model or "",
            "effort": effort or "",
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "ask-acp:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_compat_ask(
    command_target: str,
    content: str,
    *,
    task_id: str,
    source: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    data: str | None = None,
    review: bool = False,
    output_path: str | None = None,
    stdout_only: bool = False,
    hard_timeout: int | None = None,
) -> object:
    """Execute one normal ACP ask with fail-open body-free usage telemetry."""
    participant = require_compat_target(command_target)
    if not task_id or not task_id.strip():
        raise ValueError("ACP ask requires a non-empty task_id")

    from scripts.telemetry.legacy_bridge import (
        finish_bridge_invocation_safely,
        start_bridge_invocation_safely,
    )

    telemetry_token = start_bridge_invocation_safely(participant, source)
    try:
        result = _run_compat_ask_impl(
            command_target,
            content,
            task_id=task_id,
            source=source,
            model=model,
            effort=effort,
            data=data,
            review=review,
            output_path=output_path,
            stdout_only=stdout_only,
            hard_timeout=hard_timeout,
        )
    except BaseException:
        finish_bridge_invocation_safely(telemetry_token, succeeded=False)
        raise
    finish_bridge_invocation_safely(
        telemetry_token,
        succeeded=bool(getattr(result, "ok", False)),
    )
    return result


def _run_compat_ask_impl(
    command_target: str,
    content: str,
    *,
    task_id: str,
    source: str | None = None,
    model: str | None = None,
    effort: str | None = None,
    data: str | None = None,
    review: bool = False,
    output_path: str | None = None,
    stdout_only: bool = False,
    hard_timeout: int | None = None,
) -> object:
    """Execute the authority/ACP path after telemetry admission.

    ``review=True`` runs as a normal ask: the review of record is one direct
    cross-family round with the verdict posted on the PR by the requester
    (operator order 2026-08-06). The sealed ``review-pr`` path is opt-in for
    high-risk code only.

    ``hard_timeout=None`` resolves the seat's profile default (#6877); an
    explicit value always wins.

    On a notebook whose local plane is retired (#7172), ordinary asks forward
    over SSH to the job-host plane instead of opening local sqlite.

    Quota substitution (#8499): when the targeted ACP seat fails with a
    quota/rate-limit class, the ask retries once on the seat mapped by
    ``agent_fallback_substitutions.yaml`` ``dispatch_fallbacks`` — ACP to ACP
    only, never the bridge or provider execution. The failed seat's job is
    terminalized durably before the substitute runs; a substitute that is
    itself out of quota fails loudly with no second hop. Every other failure
    class is unchanged.
    """
    participant = require_compat_target(command_target)
    if not task_id or not task_id.strip():
        raise ValueError("ACP ask requires a non-empty task_id")
    if hard_timeout is None:
        hard_timeout = ask_hard_timeout(command_target)

    # #7172: Mac/notebook is a client. Forward before AuthorityService so a
    # retired local marker never surfaces as PlaneRootAnchorError on ask-*.
    from ._job_host_forward import AskForwardError, maybe_forward_compat_ask

    try:
        forwarded = maybe_forward_compat_ask(
            command_target,
            content,
            task_id=task_id,
            source=source,
            model=model,
            effort=effort,
            data=data,
            output_path=output_path,
            stdout_only=stdout_only,
            hard_timeout=hard_timeout,
            participant=participant,
            repo_root=REPO_ROOT,
        )
    except AskForwardError:
        raise
    if forwarded is not None:
        return forwarded

    prompt = content
    if data:
        prompt += "\n\n--- attached inert text ---\n" + data

    seat = participant
    seat_model = model
    seat_effort = effort
    substitution: dict[str, str] | None = None
    while True:
        try:
            result, terminalization_error = _run_single_acp_job(
                seat,
                prompt,
                task_id=task_id,
                source=source,
                model=seat_model,
                effort=seat_effort,
                review=review,
                hard_timeout=hard_timeout,
                substitution=substitution,
            )
        except BaseException as exc:
            reason = _quota_failure_reason(error=exc)
            substitute = (
                None
                if reason is None
                else _resolve_quota_substitution(seat, reason, already_substituted=substitution is not None)
            )
            if substitute is None:
                raise
            substitution = _announce_substitution(seat, substitute, reason, model=seat_model, effort=seat_effort)
            seat, seat_model, seat_effort = substitute, None, None
            continue
        reason = (
            None
            if terminalization_error is not None or bool(getattr(result, "ok", False))
            else _quota_failure_reason(result=result)
        )
        substitute = (
            None
            if reason is None
            else _resolve_quota_substitution(seat, reason, already_substituted=substitution is not None)
        )
        if substitute is None:
            break
        substitution = _announce_substitution(seat, substitute, reason, model=seat_model, effort=seat_effort)
        seat, seat_model, seat_effort = substitute, None, None

    if substitution is not None:
        result = _with_substitution_record(result, substitution)
    response = str(getattr(result, "response", ""))
    if output_path:
        Path(output_path).write_text(response, encoding="utf-8")
    if stdout_only or response:
        print(response)
    print(
        f"deprecated ask-{command_target}: ACP transport; "
        f"outcome={getattr(result, 'transport_outcome', None) or 'error'}",
        file=sys.stderr,
    )
    if terminalization_error is not None:
        message = (
            "ACP terminal bookkeeping failed after provider response: "
            f"{terminalization_error}"
        )
        print(message, file=sys.stderr)
        raise RuntimeError(message) from terminalization_error
    return result


def _run_single_acp_job(
    participant: str,
    prompt: str,
    *,
    task_id: str,
    source: str | None,
    model: str | None,
    effort: str | None,
    review: bool,
    hard_timeout: int,
    substitution: dict[str, str] | None = None,
) -> tuple[object, Exception | None]:
    """Run one authority-job ACP attempt against ``participant``.

    Returns ``(result, terminalization_error)``. The job is terminalized
    durably before this returns or raises, so a quota failure is recorded
    against the seat that actually failed before any substitution is
    attempted (#8499). When ``substitution`` is set this attempt is the
    substitute seat: its job metadata and result receipt carry the record.
    """
    from agent_runtime.runner import invoke_inter_agent

    from scripts.fleet_comms.authority import AuthorityService, AuthorityServiceError

    key = _idempotency_key(
        participant=participant,
        task_id=task_id,
        content=prompt,
        model=model,
        effort=effort,
    )
    worker_id = f"acp-compat:{os.getpid()}"
    terminalization_error: Exception | None = None
    metadata: dict[str, object] = {
        "task_id": task_id,
        "requested_model": model,
        "requested_effort": effort,
        "transport": "acp",
    }
    if substitution is not None:
        metadata["substitution"] = substitution
    with AuthorityService() as authority:
        job = authority.enqueue_request(
            recipient=participant,
            body=prompt,
            sender=source or "operator",
            metadata=metadata,
            idempotency_key=key,
        )
        terminal_states = {"complete", "failed", "expired", "dead_lettered"}
        if job.state not in terminal_states:
            try:
                lease = authority.claim_job(
                    job.job_id, worker_id, lease_seconds=hard_timeout + 30
                )
            except AuthorityServiceError:
                # A concurrent terminalizer may win after enqueue_request() returns.
                # Re-read before invoking a provider so an already-durable result is
                # replayed instead of spending another provider invocation.
                job = authority.get_job(job.job_id)
                if job.state not in terminal_states:
                    raise
        if job.state in terminal_states:
            replay = authority.read_job_result(job.job_id)
            if replay is None:
                raise RuntimeError(f"terminal ACP job {job.job_id} has no result receipt")
            result = _replay_result(replay)
        else:
            previous_transport = os.environ.get("LU_ACPX_TRANSPORT")
            os.environ["LU_ACPX_TRANSPORT"] = "active"
            try:
                # Reachability preflight (#6805): probe only now that a real
                # provider invocation is about to occur. Terminal-replay paths
                # above never reach this probe, so a provider CLI missing from
                # the host cannot fail the replay of an already-durable
                # result. A refusal here is terminalized as a durable failure
                # by the except below. The adapter's own compatibility probe
                # still enforces the full contract immediately before spawn.
                from scripts.agent_runtime.adapters.acpx import (
                    probe_participant_reachability,
                )

                reachability_error = probe_participant_reachability(participant)
                if reachability_error is not None:
                    raise ValueError(reachability_error)
                from ._acp_execution import acp_execution_cwd

                with acp_execution_cwd(REPO_ROOT, task_id=task_id) as execution_cwd:
                    result = invoke_inter_agent(
                        participant,
                        prompt,
                        cwd=execution_cwd,
                        task_id=task_id,
                        correlation_id=task_id,
                        idempotency_key=key,
                        source=source,
                        model=model,
                        effort=effort,
                        hard_timeout=hard_timeout,
                    )
            except BaseException as exc:
                # Persist the canonical capacity reason on the receipt (#8499):
                # a post-crash retry replays this receipt instead of seeing the
                # live exception, and the replayed reason must classify
                # identically — otherwise the substitute's re-enqueue under the
                # same idempotency key carries different substitution metadata
                # and the authority rejects it, stranding the job.
                capacity_reason = _quota_failure_reason(error=exc)
                failure_receipt: dict[str, object] = {
                    "ok": False,
                    "agent": participant,
                    "model": model or f"{participant}-bridge-error",
                    "response": "",
                    "stderr_excerpt": (f"{type(exc).__name__}: terminal ACP invocation failed"),
                    "duration_s": 0.0,
                    "returncode": 1,
                    "effort": effort or "unknown",
                    "from_model": model or f"{participant}-bridge-error",
                    "model_requested": model or f"{participant}-bridge-error",
                    "effort_requested": effort,
                    "effort_applied": None,
                    "harness": "acp",
                    "transport_metadata": None,
                    "transport_outcome": "rate_limited" if capacity_reason is not None else "error",
                }
                if substitution is not None:
                    failure_receipt["substitution"] = substitution
                authority.finish_job(
                    job.job_id,
                    worker_id=worker_id,
                    fence_token=lease.fence_token,
                    state="failed",
                    result=json.dumps(failure_receipt, sort_keys=True).encode("utf-8"),
                    failure=_failure_metadata(error=exc),
                )
                raise
            finally:
                if previous_transport is None:
                    os.environ.pop("LU_ACPX_TRANSPORT", None)
                else:
                    os.environ["LU_ACPX_TRANSPORT"] = previous_transport
            if review and bool(getattr(result, "ok", False)):
                # Outcome validation for review asks (#6805): a transport-ok
                # reply without a verdict grounded in evidence terminalizes as
                # failed:non_evidentiary — never a silent "replied".
                review_failure = review_outcome_failure(
                    str(getattr(result, "response", ""))
                )
                if review_failure is not None:
                    result = _non_evidentiary_result(result, review_failure)
            try:
                authority.finish_job(
                    job.job_id,
                    worker_id=worker_id,
                    fence_token=lease.fence_token,
                    state="complete" if bool(getattr(result, "ok", False)) else "failed",
                    result=_result_receipt(
                        result,
                        model_requested=model,
                        effort_requested=effort,
                        substitution=substitution,
                    ),
                    failure=(
                        None
                        if bool(getattr(result, "ok", False))
                        else _failure_metadata(result=result)
                    ),
                )
            except Exception as exc:
                # Provider output is the user-visible result.  Do not lose it when
                # a concurrent terminalizer or another authority failure rejects
                # bookkeeping after a completed invocation.
                terminalization_error = exc
    return result, terminalization_error
