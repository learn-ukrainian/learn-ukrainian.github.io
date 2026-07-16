"""Canonical cross-family reviewer resolver for code-review closeout.

Family follows the MODEL, not the harness or CLI name — the same underlying
model reachable through different tooling (native CLI, hermes, a `-tools`
V7 seat) always resolves to the same family, so an author can't dodge the
cross-family requirement by switching harness. Domain and data-egress
exclusions are fail-closed: an unspecified or non-matching policy excludes
a gated candidate, it does not admit it. Lane *health* is fail-open (no
signal ≠ unhealthy, matching ``scripts/api/lane_health.py``'s convention)
and used only as a tie-breaker among candidates that already passed every
hard filter.

This module intentionally does not duplicate the full routing table from
``agents_extensions/shared/rules/model-assignment.md`` — it owns a small,
tested policy layer (the default code-review ladder + the family/exclusion
tables below) and documents its provenance inline. Update both together if
the canonical routing doc changes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from scripts.agent_runtime.agent_identity import normalize_seat, tools_writer_runtime_agent

CandidateStatus = Literal["eligible", "selected", "advisory_only", "excluded"]

# --- family resolution -------------------------------------------------------

# Exact seat/model id -> family. Includes native-CLI names, `-tools` V7 writer/
# reviewer seat aliases, and Hermes-hosted aliases so the SAME model resolves
# to the SAME family everywhere it's reachable.
_FAMILY_BY_EXACT_SEAT: dict[str, str] = {
    "claude": "anthropic",
    "claude-tools": "anthropic",
    "sonnet": "anthropic",
    "opus": "anthropic",
    "haiku": "anthropic",
    "fable": "anthropic",
    "codex": "openai",
    "codex-tools": "openai",
    "openai_frontier": "openai",
    "gemini": "google",
    "gemini-tools": "google",
    "agy": "google",
    "agy-tools": "google",
    "gemma": "google",
    "grok": "xai",
    "grok-build": "xai",
    "grok-hermes": "xai",
    "grok-tools": "xai",
    "deepseek": "deepseek",
    "deepseek-tools": "deepseek",
    "cursor": "cursor",
    "cursor-tools": "cursor",
    "pool": "poolside",
    "glm": "zhipu",
    "qwen": "alibaba",
    "qwen-tools": "alibaba",
}

# Model-id prefixes, for concrete model strings not covered by the seat table
# above (e.g. "gpt-5.6-sol", "deepseek-v4-flash", "grok-4.5").
_FAMILY_BY_MODEL_PREFIX: tuple[tuple[str, str], ...] = (
    ("claude-", "anthropic"),
    ("sonnet-", "anthropic"),
    ("opus-", "anthropic"),
    ("haiku-", "anthropic"),
    ("fable-", "anthropic"),
    ("gpt-", "openai"),
    ("o1", "openai"),
    ("o3", "openai"),
    ("gemini-", "google"),
    ("gemma-", "google"),
    ("grok-", "xai"),
    ("deepseek-", "deepseek"),
    ("qwen", "alibaba"),
    ("glm-", "zhipu"),
)


def resolve_family(seat_or_model: str) -> str:
    """Resolve a seat/CLI-alias/model-id string to its model family.

    Returns ``"unknown"`` for anything unrecognized — callers must not treat
    unknown as any specific family (including the author's own), since that
    would either wrongly admit or wrongly exclude a candidate.
    """
    normalized = (seat_or_model or "").strip().lower()
    if not normalized:
        return "unknown"

    canonical = normalize_seat(normalized) or normalized
    if canonical in _FAMILY_BY_EXACT_SEAT:
        return _FAMILY_BY_EXACT_SEAT[canonical]

    if canonical.endswith("-tools"):
        base = tools_writer_runtime_agent(canonical)
        if base in _FAMILY_BY_EXACT_SEAT:
            return _FAMILY_BY_EXACT_SEAT[base]
        canonical = base

    for prefix, family in _FAMILY_BY_MODEL_PREFIX:
        if canonical.startswith(prefix):
            return family
    return "unknown"


# --- candidates ---------------------------------------------------------------

@dataclass(frozen=True)
class ReviewerCandidate:
    name: str
    family: str
    concrete_model: str
    requires_silence_timeout: bool = False
    # Fail-closed data-egress gate: eligible only when the caller's
    # data_egress_policy exactly matches this value. None = no egress gate.
    requires_data_egress_policy: str | None = None
    # Hard exclusion regardless of anything else (e.g. cost policy).
    always_excluded_reason: str | None = None
    capabilities: frozenset[str] = field(default_factory=frozenset)
    # Domains (review_profile-adjacent, e.g. "folk_content") where this
    # candidate is a hard no per model-assignment.md carve-outs.
    domain_excluded_from: frozenset[str] = field(default_factory=frozenset)
    # Author families for which this candidate is advisory-only rather than
    # hard-excluded on a same-family match (e.g. openai_frontier for an
    # OpenAI-family author: still consulted, never the formal gate).
    advisory_only_for_author_families: frozenset[str] = field(default_factory=frozenset)


DEEPSEEK_V4_FLASH = ReviewerCandidate(
    name="deepseek-v4-flash",
    family="deepseek",
    concrete_model="deepseek-v4-flash",
    requires_silence_timeout=True,
    domain_excluded_from=frozenset({"folk_content"}),
)
GROK_4_5 = ReviewerCandidate(name="grok-4.5", family="xai", concrete_model="grok-4.5")
POOL = ReviewerCandidate(name="pool", family="poolside", concrete_model="laguna-m.1")
OPENAI_FRONTIER = ReviewerCandidate(
    name="openai_frontier",
    family="openai",
    concrete_model="gpt-5.6-sol",
    advisory_only_for_author_families=frozenset({"openai"}),
)

# Rungs in priority order; each rung is itself an ordered list of candidates
# (health breaks ties within a rung; the first rung with any eligible
# candidate wins over later rungs regardless of health).
DEFAULT_CODE_LADDER: tuple[tuple[ReviewerCandidate, ...], ...] = (
    (DEEPSEEK_V4_FLASH,),
    (GROK_4_5,),
    (POOL,),
    (OPENAI_FRONTIER,),
)

# Known hard-filtered candidates outside the default ladder — kept here so the
# fail-closed exclusion logic is directly testable even where model-assignment.md
# doesn't route code review through them by default.
QWEN = ReviewerCandidate(
    name="qwen",
    family="alibaba",
    concrete_model="qwen3-max",
    always_excluded_reason="excluded from routine/automatic routing (cost) — model-assignment.md",
)
GLM = ReviewerCandidate(
    name="glm",
    family="zhipu",
    concrete_model="glm-5.2",
    requires_data_egress_policy="local_interactive",
)

_HEALTH_RANK: dict[str, int] = {"healthy": 0, "degraded": 1, "near_cap": 2, "unhealthy": 3}


def _health_rank(status: str | None) -> int:
    # Fail-open: no signal for this lane is read as healthy, not unhealthy —
    # matches scripts/api/lane_health.py's fail-open convention.
    if status is None:
        return 0
    return _HEALTH_RANK.get(status, 0)


@dataclass(frozen=True)
class ResolverInputs:
    author_model: str
    review_profile: str = "code"
    risk: str = "medium"
    domain: str = "code"
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    # Fail-closed: None/unrecognized means the strictest reading, not "anything goes."
    data_egress_policy: str | None = None
    isolation_required: bool = False
    # Fresh CodexBar/routing-budget snapshot: seat or family name -> health status
    # ("healthy" | "degraded" | "near_cap" | "unhealthy"). Optional — omit for a
    # snapshot-blind resolution (ladder order alone decides).
    routing_snapshot: Mapping[str, str] | None = None


@dataclass(frozen=True)
class CandidateResult:
    name: str
    concrete_model: str
    family: str
    status: CandidateStatus
    reason: str | None
    health: str | None


@dataclass(frozen=True)
class ReviewerResolution:
    selected: CandidateResult | None
    advisory: tuple[CandidateResult, ...]
    trace: tuple[CandidateResult, ...]
    substitution_note: str | None


def _health_of(candidate: ReviewerCandidate, snapshot: Mapping[str, str] | None) -> str | None:
    if not snapshot:
        return None
    return snapshot.get(candidate.name) or snapshot.get(candidate.family)


def _hard_exclusion_reason(candidate: ReviewerCandidate, inputs: ResolverInputs) -> str | None:
    """Non-family exclusions: cost policy, domain carve-out, data-egress
    (fail-closed), missing required capability. Family/advisory handling is
    the caller's job — this only covers filters that apply regardless."""
    if candidate.always_excluded_reason:
        return candidate.always_excluded_reason
    if inputs.domain in candidate.domain_excluded_from:
        return f"hard domain exclusion: {candidate.name} is excluded from {inputs.domain!r} review"
    if (
        candidate.requires_data_egress_policy is not None
        and inputs.data_egress_policy != candidate.requires_data_egress_policy
    ):
        return (
            f"data-egress policy fail-closed: {candidate.name} requires "
            f"data_egress_policy={candidate.requires_data_egress_policy!r}, "
            f"got {inputs.data_egress_policy!r}"
        )
    missing = inputs.required_capabilities - candidate.capabilities
    if missing:
        return f"missing required capabilities: {sorted(missing)}"
    if inputs.isolation_required and "isolation" not in candidate.capabilities:
        return "isolation required but candidate does not support process isolation"
    return None


def evaluate_candidate(
    candidate: ReviewerCandidate,
    inputs: ResolverInputs,
    *,
    author_family: str | None = None,
) -> CandidateResult:
    """Evaluate one candidate against ``inputs`` independent of ladder position.

    Exposed directly (not just via :func:`resolve_reviewer`) so domain and
    data-egress fail-closed behavior is testable per-candidate, including for
    candidates that aren't in the default ladder (e.g. ``GLM``, ``QWEN``).
    """
    family = author_family if author_family is not None else resolve_family(inputs.author_model)
    health = _health_of(candidate, inputs.routing_snapshot)
    same_family = candidate.family == family

    if same_family and family in candidate.advisory_only_for_author_families:
        return CandidateResult(
            candidate.name,
            candidate.concrete_model,
            candidate.family,
            "advisory_only",
            f"same family as author ({family}) — advisory-only, not a formal cross-family gate",
            health,
        )
    if same_family:
        return CandidateResult(
            candidate.name,
            candidate.concrete_model,
            candidate.family,
            "excluded",
            f"same family as author ({family}) — cross-family review requires a different family",
            health,
        )

    reason = _hard_exclusion_reason(candidate, inputs)
    if reason:
        return CandidateResult(candidate.name, candidate.concrete_model, candidate.family, "excluded", reason, health)

    return CandidateResult(candidate.name, candidate.concrete_model, candidate.family, "eligible", None, health)


def resolve_reviewer(
    inputs: ResolverInputs,
    ladder: tuple[tuple[ReviewerCandidate, ...], ...] = DEFAULT_CODE_LADDER,
) -> ReviewerResolution:
    """Walk the ladder in order; the first rung with an eligible candidate
    wins (health breaks ties within that rung). Advisory-only candidates
    (e.g. ``openai_frontier`` for an OpenAI-family author) are always
    surfaced separately, regardless of which rung is selected."""
    author_family = resolve_family(inputs.author_model)
    trace: list[CandidateResult] = []
    advisory: list[CandidateResult] = []
    selected: CandidateResult | None = None

    for rung in ladder:
        rung_eligible: list[CandidateResult] = []
        for candidate in rung:
            result = evaluate_candidate(candidate, inputs, author_family=author_family)
            trace.append(result)
            if result.status == "advisory_only":
                advisory.append(result)
            elif result.status == "eligible":
                rung_eligible.append(result)

        if selected is None and rung_eligible:
            best = min(rung_eligible, key=lambda r: _health_rank(r.health))
            promoted = CandidateResult(best.name, best.concrete_model, best.family, "selected", None, best.health)
            for i, entry in enumerate(trace):
                if entry is best:
                    trace[i] = promoted
                    break
            selected = promoted

    substitution_note = None
    if selected is not None:
        default_first = ladder[0][0] if ladder and ladder[0] else None
        if default_first is not None and selected.name != default_first.name:
            substitution_note = f"substituted {selected.name} for default first pick {default_first.name}"

    return ReviewerResolution(
        selected=selected,
        advisory=tuple(advisory),
        trace=tuple(trace),
        substitution_note=substitution_note,
    )
