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
