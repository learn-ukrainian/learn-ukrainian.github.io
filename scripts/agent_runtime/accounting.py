"""Additive accounting labels. These projections never grant identity eligibility."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any
from uuid import UUID


def model_accounting_fields(
    *, requested_selector: str | None, identity: Any = None,
    task_id: str | None = None, run_nonce: str | None = None,
) -> dict[str, Any]:
    """Project a same-run observation independently of the accounting model.

    The observation keeps its attempt's selector in its provenance. The outer
    selector records caller intent across failover. Reuse the existing validator
    without changing matching, admission, or eligibility decisions.
    """
    from scripts.agent_runtime.adapters.agy import AgyRuntimeIdentity, agy_model_state

    observed = None
    observed_provenance = None
    if isinstance(identity, AgyRuntimeIdentity):
        provenance = identity.get("provenance")
        if isinstance(provenance, dict):
            state = agy_model_state(
                agent="agy", model=provenance.get("requested_model"), identity=identity,
                task_id=task_id, run_nonce=run_nonce,
            )
            if state.get("resolved_model_known"):
                observed = state["resolved_model"]
                observed_provenance = {
                    "requested_model": provenance["requested_model"],
                    "invocation_id": str(UUID(hex=provenance["invocation_id"])),
                }
    return {
        "requested_selector": requested_selector,
        "observed_model": observed,
        "identity_state": "observed" if observed is not None else "unknown",
        "observed_model_source": "provider-init" if observed is not None else None,
        "observed_model_provenance": observed_provenance,
    }


def recorded_model_accounting_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    """Read explicit serialized projections; historical model labels prove nothing."""
    requested = record.get("requested_selector")
    observed = record.get("observed_model")
    source = record.get("observed_model_source")
    provenance = record.get("observed_model_provenance")
    known = (
        record.get("identity_state") == "observed"
        and isinstance(observed, str) and 0 < len(observed.strip()) <= 200
        and source == "provider-init"
        and isinstance(provenance, Mapping)
        and isinstance(provenance.get("requested_model"), str)
        and 0 < len(provenance["requested_model"]) <= 200
        and isinstance(provenance.get("invocation_id"), str)
        and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", provenance["invocation_id"]) is not None
    )
    identity = record.get("model_identity")
    if isinstance(identity, Mapping):
        known = known and (
            identity.get("actual_model_known") is True
            and identity.get("actual_model") == observed
            and identity.get("source") == source
        )
    if known and isinstance(identity, Mapping) and isinstance(identity.get("provenance"), Mapping):
        original = identity["provenance"]
        known = original.get("requested_model") == provenance["requested_model"]
        original_id = original.get("invocation_id")
        # The secret redactor may remove the legacy hex token from serialized
        # receipts. The UUID-form projection retains the same public call ID.
        if isinstance(original_id, str) and re.fullmatch(r"[0-9a-f]{32}", original_id):
            known = known and original_id == UUID(provenance["invocation_id"]).hex
    return {
        "requested_selector": requested if isinstance(requested, str) else None,
        "observed_model": observed if known else None,
        "identity_state": "observed" if known else "unknown",
        "observed_model_source": source if known else None,
        "observed_model_provenance": {
            "requested_model": provenance["requested_model"], "invocation_id": provenance["invocation_id"],
        } if known else None,
    }
