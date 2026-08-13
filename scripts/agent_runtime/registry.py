"""Agent registry — catalog of all agents known to the runtime.

Each entry describes how to reach an agent's adapter, its default model, cost
tier (for budgeting), capability tags (informational only; benchmark harness
will populate real scores later), and its resume_policy.

Resume policy is data-driven (see docs/design/agent-runtime.md § 6.3):

- ``bridge_only`` — Session resume allowed ONLY when caller is the bridge
  (multi-turn task_id messaging). Forbidden for delegate/dispatch. Claude
  and Gemini use it for cache warmth; Codex uses it to preserve its native
  conversation reasoning and compaction without exposing sessions to worktrees.
- ``never`` — No resume ever. Use this for agents whose sessions cannot be
  safely continued by the runtime.
- The runner enforces resume policy at its invocation boundary. This keeps
  bridge-only continuity out of delegate, dispatch, and consult worktrees.

Issue: #1184
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class AgentEntry(TypedDict):
    """Registry row shape."""

    adapter: str  # fully-qualified "module:ClassName" import path
    default_model: str | None
    default_effort: NotRequired[str | None]
    cost_tier: str  # "low" | "medium" | "high" | "unknown"
    capabilities: frozenset[str]
    cli_available: bool
    bridge_spawnable: NotRequired[bool]
    direct_only: NotRequired[bool]
    resume_policy: str  # "bridge_only" | "never"


AGENTS: dict[str, AgentEntry] = {
    "codex": {
        "adapter": "scripts.agent_runtime.adapters.codex:CodexAdapter",
        # Operator 2026-08-13: dispatch default is Luna @ max; explicit
        # --model gpt-5.6-terra|gpt-5.6-sol / --effort always win.
        "default_model": "gpt-5.6-luna",
        "default_effort": "max",
        "cost_tier": "medium",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "debugging",
                "adversarial_review",
            }
        ),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "codex-desktop": {
        "adapter": "scripts.agent_runtime.adapters.codex:CodexAdapter",
        "default_model": "gpt-5.6-terra",
        "cost_tier": "high",
        "capabilities": frozenset(
            {
                "frontend_design",
                "ui_review",
                "multimodal",
                "visual_inspection",
            }
        ),
        "cli_available": False,
        "resume_policy": "never",
    },
    "claude": {
        "adapter": "scripts.agent_runtime.adapters.claude:ClaudeAdapter",
        "default_model": "claude-sonnet-5",
        "cost_tier": "high",
        "capabilities": frozenset(
            {
                "architecture",
                "review",
                "content_a1",
                "planning",
            }
        ),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "claude-desktop": {
        "adapter": "scripts.agent_runtime.adapters.claude:ClaudeAdapter",
        "default_model": "claude-sonnet-5",
        "cost_tier": "high",
        "capabilities": frozenset(
            {
                "frontend_design",
                "ui_review",
                "multimodal",
                "visual_inspection",
            }
        ),
        "cli_available": False,
        "resume_policy": "never",
    },
    "claude-infra": {
        "adapter": "scripts.agent_runtime.adapters.claude:ClaudeAdapter",
        "default_model": "claude-sonnet-5",
        "cost_tier": "high",
        "capabilities": frozenset(
            {
                "architecture",
                "review",
                "planning",
            }
        ),
        "cli_available": False,
        "resume_policy": "never",
    },
    "gemini": {
        "adapter": "scripts.agent_runtime.adapters.gemini:GeminiAdapter",
        "default_model": "gemini-3.1-pro-high",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "content_writing",
                "content_review",
                "adversarial_review",
            }
        ),
        # V7 batch runner still invokes gemini-tools via runner; bridge discuss/inbox
        # routes gemini-family work through agy (model-assignment.md).
        "cli_available": True,
        "bridge_spawnable": False,
        "resume_policy": "bridge_only",
    },
    "grok": {
        # Native `grok` CLI seat (preferred Grok transport). Named by role
        # (native CLI), not model version — model is a swappable attribute
        # (currently grok-4.5). Historical alias: "grok-build" (see
        # agent_identity.SEAT_ALIASES); dual-READ only, prefer-WRITE "grok".
        # DISTINCT from "grok-hermes" below (disfavored Hermes/OpenRouter path).
        "adapter": "scripts.agent_runtime.adapters.grok_build:GrokBuildAdapter",
        "default_model": "grok-4.5",
        "default_effort": "high",
        "cost_tier": "medium",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "debugging",
            }
        ),
        "cli_available": True,
        "resume_policy": "never",
    },
    "grok-build": {
        # PERMANENT alias for the native "grok" seat. Keep forever so old
        # X-Agent trailers, inbox rows, budget usage, and `--agent grok-build`
        # keep resolving. Prefer-WRITE is "grok"; this entry exists so bare
        # registry lookups of the historical key still succeed without every
        # caller remembering to normalize first.
        "adapter": "scripts.agent_runtime.adapters.grok_build:GrokBuildAdapter",
        "default_model": "grok-4.5",
        "default_effort": "high",
        "cost_tier": "medium",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "debugging",
            }
        ),
        "cli_available": True,
        "resume_policy": "never",
    },
    "deepseek": {
        # OpenCode → first-party api.deepseek.com (deepseek-direct/*) is the
        # dispatch default (operator 2026-08-13): Flash only, --variant high,
        # native Entire capture. Pro stays DO NOT USE; the Hermes adapter
        # (hermes_deepseek.py) remains for ask-hermes only. First-party
        # DeepSeek is China-hosted → CI runs are refused by the adapter.
        "adapter": "scripts.agent_runtime.adapters.deepseek:DeepSeekAdapter",
        "default_model": "deepseek-v4-flash",
        "default_effort": "high",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "content_writing",
                "content_review",
                "adversarial_review",
            }
        ),
        "cli_available": True,
        "resume_policy": "never",
    },
    "grok-hermes": {
        # Hermes-backed Grok path (DISABLED per user directive 2026-07-22:
        # "not routing grok towards hermes anymore"). Kept in registry for
        # backwards-compatibility lookups, but cli_available is False.
        "adapter": "scripts.agent_runtime.adapters.hermes_grok:HermesGrokAdapter",
        "default_model": "grok-4.5",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "content_writing",
                "content_review",
                "adversarial_review",
            }
        ),
        "cli_available": False,
        "resume_policy": "never",
    },
    "qwen": {
        # Qwen path (DISABLED per user directive 2026-07-22: "we dont use qwen,
        # but we use glm-5.2"). Kept in registry for historical lookups, but
        # cli_available is False.
        "adapter": "scripts.agent_runtime.adapters.hermes_qwen:HermesQwenAdapter",
        "default_model": "qwen/qwen3.6-plus",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "content_writing",
                "content_review",
                "adversarial_review",
            }
        ),
        "cli_available": False,
        "resume_policy": "never",
    },
    "glm": {
        "adapter": "scripts.agent_runtime.adapters.glm:GlmAdapter",
        # Catalog model id; the Z.AI Coding Plan provider pin is applied at
        # invocation time by the adapter (_OPENCODE_MODEL_ROUTES).
        "default_model": "glm-5.2",
        "default_effort": "high",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "adversarial_review",
            }
        ),
        "cli_available": True,
        "resume_policy": "never",
    },
    "cursor": {
        "adapter": "scripts.agent_runtime.adapters.cursor:CursorAdapter",
        "default_model": "auto",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "content_writing",
                "content_review",
                "adversarial_review",
            }
        ),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "kimi": {
        # Native Kimi Code OAuth subscription lane (no proxy-provider route).
        # Operator 2026-08-13: dispatch/native default is k3-256k (everyday
        # coding) with no forced effort; full K3 (high/max, 1M window) is the
        # advisor/complex seat selected via --model k3 --effort high|max.
        # Ukrainian content capabilities remain separately gated.
        "adapter": "scripts.agent_runtime.adapters.kimi:KimiAdapter",
        "default_model": "k3-256k",
        "cost_tier": "medium",
        "capabilities": frozenset(
            {
                "code_writing",
                "code_review",
                "adversarial_review",
                "debugging",
                "multimodal",
            }
        ),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
    "acpx-codex-shadow": {
        # Direct-only ACP transport (#6027): never returned by
        # ``available_agents()`` and never a general dispatch or failover
        # candidate. Only the runner-owned communication controller and its
        # parent-sealed formal-review executable may invoke this seat.
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxAdapter",
        # ACPX resolves its own agent default when no --model is supplied;
        # this direct-only seat must not advertise an invented catalog model.
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-grok-shadow": {
        # Direct-only ACP transport (#6043): never returned by
        # ``available_agents()`` and never a general dispatch or failover
        # candidate. Only the runner-owned communication controller and its
        # hash-pinned, parent-sealed formal-review executable may invoke it.
        # Fixed effective model/effort live inside the custom --agent command;
        # do not advertise a catalog model here. Native Grok remains the
        # provider authority; this registry name is not a coordination plane.
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxGrokShadowAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-claude-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxClaudeShadowAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-kimi-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxKimiShadowAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-kimicc-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxKimiCcShadowAdapter",
        "default_model": "kimi-code/k3",
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-cursor-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxCursorShadowAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-pool-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxPoolShadowAdapter",
        "default_model": None,
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-agy-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxAgyShadowAdapter",
        "default_model": "gemini-3.6-flash-high",
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-glm-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxGlmShadowAdapter",
        "default_model": "glm-5.2",
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "acpx-deepseek-shadow": {
        "adapter": "scripts.agent_runtime.adapters.acpx:AcpxDeepSeekShadowAdapter",
        "default_model": "deepseek-v4-pro",
        "cost_tier": "unknown",
        "capabilities": frozenset(),
        "cli_available": False,
        "direct_only": True,
        "resume_policy": "never",
    },
    "agy": {
        # Antigravity CLI shipping Gemini Flash 3.6 (was 3.5) on a separate meter from
        # gemini-cli. Added 2026-05-20 for the seminar-writer ADR bakeoff
        # (`docs/decisions/pending/2026-05-20-seminar-track-writer-assignment.md`).
        # MCP plugin wiring is a Phase-2 follow-up — until then `-tools`
        # writer mode will trip MCP_TOOLS_NEVER_INVOKED, which is the
        # expected signal in the bakeoff.
        "adapter": "scripts.agent_runtime.adapters.agy:AgyAdapter",
        "default_model": "gemini-3.6-flash-high",
        "cost_tier": "low",
        "capabilities": frozenset(
            {
                "content_writing",
                "content_review",
            }
        ),
        "cli_available": True,
        "resume_policy": "bridge_only",
    },
}


def get_agent_entry(name: str) -> AgentEntry:
    """Look up an agent entry by name.

    Permanent aliases (e.g. ``grok-build`` → ``grok``) resolve to the
    canonical seat when the alias key is absent, but both keys are kept in
    ``AGENTS`` so historical callers that look up the alias string directly
    still succeed.

    Raises:
        KeyError: If ``name`` is not in AGENTS. Runner catches this and
            converts to AgentUnavailableError with a friendlier message.
    """
    from .agent_identity import normalize_seat

    if name in AGENTS:
        return AGENTS[name]
    canonical = normalize_seat(name)
    if canonical is not None and canonical in AGENTS:
        return AGENTS[canonical]
    raise KeyError(name)


def available_agents() -> list[str]:
    """Return names of agents whose cli_available is True.

    Used by consult.py (future) and introspection / debugging. Does not
    check whether the CLI is actually installed on PATH — that's the
    adapter's responsibility at invocation time.
    """
    return [name for name, entry in AGENTS.items() if entry["cli_available"]]
