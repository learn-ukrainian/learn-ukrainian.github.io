"""V2 custody of AGY provider-init identity, copied from the retained runner."""

import re
from typing import Any

from scripts.agent_runtime.adapters.agy import AgyAdapter, AgyRuntimeIdentity, _stream_result, agy_model_state


def observe_agy_identity(
    *, stdout: str, plan: Any, task_id: str | None, run_nonce: str | None,
    invocation_id: str, cli_sha256: str | None, cli_version: str,
) -> AgyRuntimeIdentity | None:
    """Seal identity from this invocation's stdout, never plan metadata or prose."""
    requested = plan.cmd[plan.cmd.index("--model") + 1] if "--model" in plan.cmd else None
    if requested not in AgyAdapter.claude_model_slugs:
        return None
    identity: dict[str, Any] = {}
    events: list[dict[str, Any]] = []
    terminal, _problem = _stream_result(stdout, plan=plan, model_identity=identity, identity_events=events)
    if not events or identity.get("source") != "provider-init" or not cli_sha256 or cli_version == "unknown":
        return None
    observed = identity.get("actual_model")
    try:
        observed_slug = AgyAdapter.resolve_model_slug(observed) if isinstance(observed, str) else None
    except ValueError:
        observed_slug = None
    from scripts.review.model_catalog import load_model_catalog

    family = next((
        spec["family"] for key, spec in load_model_catalog()["models"].items()
        if key == observed_slug or spec.get("routing_wire_ids", {}).get("agy") == observed_slug
    ), None) if observed_slug else None
    provider_session = events[0].get("provider_session_id")
    if provider_session is None and terminal:
        candidate = terminal.get("conversation_id")
        if isinstance(candidate, str) and 0 < len(candidate) <= 200:
            provider_session = candidate
    if observed_slug is None:
        identity.update(actual_model=None, actual_model_known=False)
    receipt = AgyRuntimeIdentity({
        **identity,
        "actual_family": family,
        "harness": "agy",
        "provenance": {
            "origin": "subprocess.stdout",
            "init_events": events,
            "provider_session_id": provider_session,
            "cli_sha256": cli_sha256,
            "cli_version": cli_version,
            "invocation_id": invocation_id,
            "task_id": task_id,
            "run_nonce": run_nonce,
            "requested_model": requested,
        },
    })
    state = agy_model_state(agent="agy", model=requested, identity=receipt, task_id=task_id,
                            run_nonce=run_nonce, invocation_id=invocation_id)
    receipt = state["model_identity"]
    return receipt


def boundary_refusal(exc: Exception, *, stage: str) -> str:
    """Keep the refusal identifier, never isolation diagnostics or exception text."""
    from scripts.review.isolation import ReviewIsolationError

    detail = type(exc).__name__
    if isinstance(exc, ReviewIsolationError):
        code = str(exc).partition(":")[0]
        if re.fullmatch(r"[a-z][a-z0-9_]*", code):
            detail = code
    return f"formal attempt filesystem boundary refused: {stage}: {detail}"
