"""Current policy checks for stage validation and every positive projection."""

from __future__ import annotations

from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.provenance import ProvenanceError


def validate_stage_policy(receipt: dict) -> str:
    """Resolve live policy even for preserved, frozen zero-completion receipts.

    Frozen public receipts retain their bytes and historical absence of the
    field. They cannot carry a positive completion. Every current positive
    receipt and every nested completion must explicitly bind the active policy.
    """
    _, active = trust.load_production_trust_policy()
    completions = []
    for name, value in receipt.items():
        if name.endswith("_completions") and isinstance(value, list):
            completions.extend(value)
    if (completions or "trust_policy_sha256" in receipt) and receipt.get("trust_policy_sha256") != active:
        raise ProvenanceError("stage trust policy is not active")
    for completion in completions:
        if completion.get("trust_policy_sha256") != active:
            raise ProvenanceError("completion trust policy is not active")
    return active


def validate_completion_policy(completions) -> str:
    _, active = trust.load_production_trust_policy()
    if any(completion.get("trust_policy_sha256") != active for completion in completions):
        raise ProvenanceError("completion trust policy is not active")
    return active


def current_stage_schema(frozen_schema: dict) -> dict:
    """Strict current envelope extension; the sealed schema resource stays exact.

    The only added field binds the current active policy. All historical shape
    constraints remain, including additionalProperties=false. Positive records
    require this field through validate_stage_policy; frozen empty receipts do not.
    """
    from copy import deepcopy

    schema = deepcopy(frozen_schema)
    schema["properties"]["trust_policy_sha256"] = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    return schema


def bind_constructed_stage(function):
    """Preserve frozen empty output; bind every constructed positive envelope."""
    from functools import wraps

    @wraps(function)
    def construct(*args, **kwargs):
        receipt = function(*args, **kwargs)
        completions = [
            item
            for name, value in receipt.items()
            if name.endswith("_completions") and isinstance(value, list)
            for item in value
        ]
        if completions:
            receipt["trust_policy_sha256"] = validate_completion_policy(completions)
        validate_stage_policy(receipt)
        return receipt

    return construct
