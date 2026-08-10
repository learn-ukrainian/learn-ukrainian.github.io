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
import sys
from pathlib import Path

from ._config import REPO_ROOT

_TARGETS = {
    "claude": "claude",
    "codex": "codex",
    "agy": "agy",
    "gemini": "agy",
    "hermes": "deepseek",
    "pool": "pool",
    "glm": "glm",
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


def _result_receipt(
    result: object,
    *,
    model_requested: str | None = None,
    effort_requested: str | None = None,
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
    if outcome == "rate_limited" or bool(getattr(result, "rate_limited", False)):
        return {"phase": "provider", "code": "rate_limited", "retryable": True}
    usage_record = getattr(result, "usage_record", None)
    code = usage_record.get("failure_code") if isinstance(usage_record, dict) else None
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
    hard_timeout: int = 300,
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
    hard_timeout: int = 300,
) -> object:
    """Execute the authority/ACP path after telemetry admission.

    ``review=True`` runs as a normal ask: the review of record is one direct
    cross-family round with the verdict posted on the PR by the requester
    (operator order 2026-08-06). The sealed ``review-pr`` path is opt-in for
    high-risk code only.
    """
    participant = require_compat_target(command_target)
    if not task_id or not task_id.strip():
        raise ValueError("ACP ask requires a non-empty task_id")
    prompt = content
    if data:
        prompt += "\n\n--- attached inert text ---\n" + data

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
    with AuthorityService() as authority:
        job = authority.enqueue_request(
            recipient=participant,
            body=prompt,
            sender=source or "operator",
            metadata={
                "task_id": task_id,
                "requested_model": model,
                "requested_effort": effort,
                "transport": "acp",
            },
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
                authority.finish_job(
                    job.job_id,
                    worker_id=worker_id,
                    fence_token=lease.fence_token,
                    state="failed",
                    result=json.dumps(
                        {
                            "ok": False,
                            "agent": participant,
                            "model": model or f"{participant}-bridge-error",
                            "response": "",
                            "stderr_excerpt": (
                                f"{type(exc).__name__}: terminal ACP invocation failed"
                            ),
                            "duration_s": 0.0,
                            "returncode": 1,
                            "effort": effort or "unknown",
                            "from_model": model or f"{participant}-bridge-error",
                            "model_requested": model or f"{participant}-bridge-error",
                            "effort_requested": effort,
                            "effort_applied": None,
                            "harness": "acp",
                            "transport_metadata": None,
                            "transport_outcome": "error",
                        },
                        sort_keys=True,
                    ).encode("utf-8"),
                    failure=_failure_metadata(error=exc),
                )
                raise
            finally:
                if previous_transport is None:
                    os.environ.pop("LU_ACPX_TRANSPORT", None)
                else:
                    os.environ["LU_ACPX_TRANSPORT"] = previous_transport
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
