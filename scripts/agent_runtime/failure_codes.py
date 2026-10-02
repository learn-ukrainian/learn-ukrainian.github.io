"""Closed, body-free failure codes the agent runtime persists in usage records.

The runner admits only these codes into ``failure_code``; the runtime API
reads the same set, so every code the runtime emits stays visible (#9532).
"""

from __future__ import annotations

RUNTIME_FAILURE_CODES = frozenset(
    {
        "acp_adapter_incompatible",
        "acp_adapter_missing",
        "acp_agent_disconnected",
        "acp_agent_startup",
        "acp_auth_required",
        "acp_permission_denied",
        "acp_permission_unavailable",
        "acp_review_evidence_invalid",
        "acp_review_evidence_too_large",
        "acp_session_create_timeout",
        "acp_turn_limit",
        "github_secondary_rate_limited",
        "adapter_refused",
        "cwd_unpinned",
        "primary_tree_write",
        "protocol_output_limit",
        "provider_auth",
        "provider_overloaded",
        "provider_policy_refusal",
        "provider_unavailable",
        "provider_error",
        "rate_limited",
        "result_invalid",
        "timeout",
        "transport_error",
        "unknown",
    }
)
