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


def _result_receipt(result: object) -> bytes:
    payload = {
        "ok": bool(getattr(result, "ok", False)),
        "agent": str(getattr(result, "agent", "")),
        "model": str(getattr(result, "model", "")),
        "response": str(getattr(result, "response", "")),
        "stderr_excerpt": getattr(result, "stderr_excerpt", None),
        "duration_s": float(getattr(result, "duration_s", 0.0)),
        "returncode": getattr(result, "returncode", None),
        "effort": str(getattr(result, "effort", "unknown")),
        "transport_metadata": getattr(result, "transport_metadata", None),
        "transport_outcome": getattr(result, "transport_outcome", None),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _replay_result(raw: bytes) -> object:
    from agent_runtime.result import Result

    payload = json.loads(raw)
    return Result(
        ok=bool(payload["ok"]),
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
        usage_record={"replayed": True, "transport": "acp"},
        transport_metadata=payload.get("transport_metadata"),
        transport_outcome=payload.get("transport_outcome"),
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
    hard_timeout: int = 300,
) -> object:
    """Execute one normal ACP ask and return the runner result.

    ``review=True`` is refused: formal review must enter through ``review-pr``
    so exact PR identity and a sealed snapshot are mandatory.
    """
    if review:
        raise ValueError("formal_review_requires_review_pr_acp_sealed_snapshot")
    participant = require_compat_target(command_target)
    if not task_id or not task_id.strip():
        raise ValueError("ACP ask requires a non-empty task_id")
    prompt = content
    if data:
        prompt += "\n\n--- attached inert text ---\n" + data

    from agent_runtime.runner import invoke_inter_agent

    from scripts.fleet_comms.authority import AuthorityService

    key = _idempotency_key(
        participant=participant,
        task_id=task_id,
        content=prompt,
        model=model,
        effort=effort,
    )
    worker_id = f"acp-compat:{os.getpid()}"
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
        if job.state in {"complete", "failed", "expired", "dead_lettered"}:
            replay = authority.read_job_result(job.job_id)
            if replay is None:
                raise RuntimeError(f"terminal ACP job {job.job_id} has no result receipt")
            result = _replay_result(replay)
        else:
            lease = authority.claim_job(job.job_id, worker_id, lease_seconds=hard_timeout + 30)
            previous_transport = os.environ.get("LU_ACPX_TRANSPORT")
            os.environ["LU_ACPX_TRANSPORT"] = "active"
            try:
                result = invoke_inter_agent(
                    participant,
                    prompt,
                    cwd=REPO_ROOT,
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
                        {"error": type(exc).__name__, "transport": "acp"},
                        sort_keys=True,
                    ).encode("utf-8"),
                )
                raise
            finally:
                if previous_transport is None:
                    os.environ.pop("LU_ACPX_TRANSPORT", None)
                else:
                    os.environ["LU_ACPX_TRANSPORT"] = previous_transport
            authority.finish_job(
                job.job_id,
                worker_id=worker_id,
                fence_token=lease.fence_token,
                state="complete" if bool(getattr(result, "ok", False)) else "failed",
                result=_result_receipt(result),
            )
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
    return result
