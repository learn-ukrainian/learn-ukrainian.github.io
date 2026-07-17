"""Canonical cross-family reviewer resolver for code-review closeout.

Family follows the MODEL, not the harness or CLI name — the same underlying
model reachable through different tooling (native CLI, hermes, a `-tools`
V7 seat) always resolves to the same family, so an author can't dodge the
cross-family requirement by switching harness. Domain and data-egress
exclusions are fail-closed: an unspecified or non-matching policy excludes
a gated candidate, it does not admit it. Missing lane-health data is fail-open
(no signal ≠ unhealthy, matching ``scripts/api/lane_health.py``'s convention),
but an explicitly unhealthy route is unavailable. Degraded and near-capacity
signals only break ties among candidates in the same quality rung; they never
demote a model into a lower-quality rung.

The model inventory, candidate routes, and risk ladders are loaded from the
versioned ``scripts/config/model_catalog.yaml`` catalog. Its separate freshness
lint forces a provider/CLI/source review every 30 days without making a stale
catalog an operational outage at runtime.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from scripts.agent_runtime.agent_identity import normalize_seat, tools_writer_runtime_agent
from scripts.review.model_catalog import VALID_RISKS, load_model_catalog

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
    "pool": "poolside",
    "glm": "zhipu",
    "qwen": "alibaba",
    "qwen-tools": "alibaba",
    "kimi": "moonshot",
    "composer": "moonshot",
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
    ("kimi-code/", "moonshot"),
    ("kimi-", "moonshot"),
    ("composer-", "moonshot"),
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


# --- ambiguous-harness / fail-closed author identity --------------------------

# Harnesses that route to more than one underlying model family depending on
# per-session configuration — the harness name alone is NOT a model family.
# Cursor is multi-model (a session may run GPT, Claude, or another model
# underneath); resolving it to a synthetic "cursor" family would let an
# author dodge the cross-family requirement whenever the real underlying
# model happens to collide with whatever the ladder picks.
AMBIGUOUS_HARNESS_SEATS: frozenset[str] = frozenset({"cursor", "cursor-tools"})

# Concrete model-vendor families a caller may assert via an explicit
# ``author_family`` override. Deliberately excludes harness pseudo-families
# (nothing routes to "cursor" as if it were a vendor) and the fail-closed
# sentinels below — an override must name a real family or be rejected.
_VALID_CONCRETE_FAMILIES: frozenset[str] = frozenset(
    {
        "anthropic",
        "openai",
        "google",
        "xai",
        "deepseek",
        "poolside",
        "zhipu",
        "alibaba",
        "moonshot",
    }
)

# Fail-closed author-identity outcomes: none of these is a real model family,
# and a caller must never treat one as matching (or not matching) any
# candidate's family — resolve_reviewer refuses to select a formal reviewer
# for any of them.
UNKNOWN_AUTHOR_FAMILY = "unknown"
AMBIGUOUS_AUTHOR_FAMILY = "ambiguous"
CONFLICTING_AUTHOR_FAMILY = "conflict"
UNRESOLVED_AUTHOR_FAMILIES: frozenset[str] = frozenset(
    {UNKNOWN_AUTHOR_FAMILY, AMBIGUOUS_AUTHOR_FAMILY, CONFLICTING_AUTHOR_FAMILY}
)


def resolve_author_family(author_model: str, author_family: str | None = None) -> str:
    """Resolve the author's model family, failing closed for ambiguous harnesses.

    ``author_model`` is either a concrete seat/model id (resolved exactly as
    :func:`resolve_family` always has), or a ``"<harness>:<concrete-model>"``
    composite for a multi-model harness (e.g. ``"cursor:gpt-5.6-sol"``,
    ``"cursor:claude-opus-4-8"``) that disambiguates which model that harness
    session actually ran. ``author_family`` is an optional explicit,
    caller-asserted family (e.g. from session logs) used to corroborate or,
    for a bare ambiguous-harness identity with no embedded model, to supply
    the disambiguation on its own.

    Returns a concrete family string, or one of the fail-closed sentinels:

    - ``"unknown"`` — no usable identity signal at all.
    - ``"ambiguous"`` — a multi-model harness with no concrete model and no
      valid override to disambiguate it.
    - ``"conflict"`` — the embedded/resolved model family and an explicit
      ``author_family`` override disagree.

    Callers (:func:`resolve_reviewer`) must never select a formal reviewer
    against a fail-closed sentinel — an unresolved author identity is not
    evidence that a candidate is (or isn't) the same family.
    """
    normalized = (author_model or "").strip().lower()
    override = (author_family or "").strip().lower() or None
    if override is not None and override not in _VALID_CONCRETE_FAMILIES:
        override = None  # an invalid/unrecognized override does not count as validated

    harness_token, sep, embedded = normalized.partition(":")
    if sep and harness_token in AMBIGUOUS_HARNESS_SEATS and embedded.strip():
        resolved = resolve_family(embedded.strip())
    elif normalized in AMBIGUOUS_HARNESS_SEATS or (normalize_seat(normalized) or "") in AMBIGUOUS_HARNESS_SEATS:
        resolved = None  # bare ambiguous harness, no embedded concrete model
    else:
        resolved = resolve_family(normalized)

    if resolved is None:
        # Bare ambiguous harness: only a validated override can disambiguate it.
        return override if override else AMBIGUOUS_AUTHOR_FAMILY
    if resolved == "unknown":
        return override if override else UNKNOWN_AUTHOR_FAMILY
    if override and override != resolved:
        return CONFLICTING_AUTHOR_FAMILY
    return resolved


# --- candidates ---------------------------------------------------------------

@dataclass(frozen=True)
class ReviewerCandidate:
    name: str
    family: str
    concrete_model: str
    route: str
    transport: str
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


_MODEL_CATALOG = load_model_catalog()


def _catalog_candidate(name: str) -> ReviewerCandidate:
    raw = _MODEL_CATALOG["review_candidates"][name]
    model_id = raw["model_id"]
    model = _MODEL_CATALOG["models"][model_id]
    return ReviewerCandidate(
        name=name,
        family=model["family"],
        concrete_model=model_id,
        route=raw["route"],
        transport=raw["transport"],
        requires_silence_timeout=bool(raw.get("requires_silence_timeout", False)),
        requires_data_egress_policy=raw.get("requires_data_egress_policy"),
        capabilities=frozenset(raw.get("capabilities", [])),
        domain_excluded_from=frozenset(raw.get("domain_excluded_from", [])),
        advisory_only_for_author_families=frozenset(
            raw.get("advisory_only_for_author_families", [])
        ),
    )


REVIEW_CANDIDATES: dict[str, ReviewerCandidate] = {
    name: _catalog_candidate(name) for name in _MODEL_CATALOG["review_candidates"]
}


def _catalog_ladder(risk: str) -> tuple[tuple[ReviewerCandidate, ...], ...]:
    return tuple(
        tuple(REVIEW_CANDIDATES[name] for name in rung)
        for rung in _MODEL_CATALOG["review_ladders"][risk]
    )


REVIEW_LADDERS: dict[str, tuple[tuple[ReviewerCandidate, ...], ...]] = {
    risk: _catalog_ladder(risk) for risk in sorted(VALID_RISKS)
}

# Compatibility constants for direct candidate evaluation and callers that
# explicitly imported the old default. Medium is the balanced default risk.
CLAUDE_OPUS_4_8 = REVIEW_CANDIDATES["claude-opus-4-8"]
OPENAI_FRONTIER = REVIEW_CANDIDATES["openai_frontier"]
GROK_4_5 = REVIEW_CANDIDATES["grok-4.5"]
KIMI_K3 = REVIEW_CANDIDATES["kimi-k3"]
DEEPSEEK_V4_PRO = REVIEW_CANDIDATES["deepseek-v4-pro"]
DEEPSEEK_V4_FLASH = REVIEW_CANDIDATES["deepseek-v4-flash"]
POOL = REVIEW_CANDIDATES["pool"]
GLM = REVIEW_CANDIDATES["glm-5.2"]
DEFAULT_CODE_LADDER = REVIEW_LADDERS["medium"]

# Known hard-filtered candidates outside the default ladder — kept here so the
# fail-closed exclusion logic is directly testable even where model-assignment.md
# doesn't route code review through them by default.
QWEN = ReviewerCandidate(
    name="qwen",
    family="alibaba",
    concrete_model="qwen3-max",
    route="qwen",
    transport="hermes",
    always_excluded_reason="excluded from routine/automatic routing (cost) — model-assignment.md",
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
    # Concrete seat/model id, OR a "<ambiguous-harness>:<concrete-model>"
    # composite (e.g. "cursor:gpt-5.6-sol") disambiguating a multi-model
    # harness session. See resolve_author_family for the exact contract.
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
    # Explicit, caller-asserted author model family (e.g. from session logs),
    # validated against _VALID_CONCRETE_FAMILIES. Required to disambiguate a
    # bare ambiguous-harness author_model; optional corroboration otherwise —
    # a mismatch against the resolved family is a fail-closed conflict.
    author_family: str | None = None


@dataclass(frozen=True)
class CandidateResult:
    name: str
    concrete_model: str
    family: str
    route: str
    transport: str
    status: CandidateStatus
    reason: str | None
    health: str | None


@dataclass(frozen=True)
class ReviewerResolution:
    selected: CandidateResult | None
    advisory: tuple[CandidateResult, ...]
    trace: tuple[CandidateResult, ...]
    substitution_note: str | None
    policy_version: str
    catalog_reviewed_on: str
    resolved_risk: str
    # Set (non-None) instead of walking the ladder at all when the author's
    # model family could not be resolved to a concrete family — unknown,
    # ambiguous-harness, or conflicting-signal identities never get a formal
    # reviewer selected, since there is nothing reliable to diff a
    # candidate's family against.
    fail_closed_reason: str | None = None


def _health_of(candidate: ReviewerCandidate, snapshot: Mapping[str, str] | None) -> str | None:
    if not snapshot:
        return None
    return (
        snapshot.get(candidate.name)
        or snapshot.get(candidate.route)
        or snapshot.get(candidate.concrete_model)
        or snapshot.get(candidate.family)
    )


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
    family = (
        author_family
        if author_family is not None
        else resolve_author_family(inputs.author_model, inputs.author_family)
    )
    health = _health_of(candidate, inputs.routing_snapshot)
    same_family = candidate.family == family

    if same_family and family in candidate.advisory_only_for_author_families:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            status="advisory_only",
            reason=f"same family as author ({family}) — advisory-only, not a formal cross-family gate",
            health=health,
        )
    if same_family:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            status="excluded",
            reason=f"same family as author ({family}) — cross-family review requires a different family",
            health=health,
        )

    reason = _hard_exclusion_reason(candidate, inputs)
    if reason:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            status="excluded",
            reason=reason,
            health=health,
        )
    if health == "unhealthy":
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            status="excluded",
            reason="lane health is unhealthy — route is operationally unavailable",
            health=health,
        )

    return CandidateResult(
        name=candidate.name,
        concrete_model=candidate.concrete_model,
        family=candidate.family,
        route=candidate.route,
        transport=candidate.transport,
        status="eligible",
        reason=None,
        health=health,
    )


def resolve_reviewer(
    inputs: ResolverInputs,
    ladder: tuple[tuple[ReviewerCandidate, ...], ...] | None = None,
) -> ReviewerResolution:
    """Walk the ladder in order; the first rung with an eligible candidate
    wins (health breaks ties within that rung). Advisory-only candidates
    (e.g. ``openai_frontier`` for an OpenAI-family author) are always
    surfaced separately, regardless of which rung is selected.

    Fails closed — no candidate walked, ``selected`` stays ``None`` — when
    the author's model family cannot be resolved to a concrete family (an
    unrecognized identity, a bare ambiguous-model harness with no
    disambiguation, or a conflicting override). See
    :func:`resolve_author_family`.
    """
    risk = (inputs.risk or "").strip().lower()
    if ladder is None and risk not in VALID_RISKS:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_MODEL_CATALOG["schema_version"],
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=(
                f"unsupported review risk {inputs.risk!r}; expected one of {sorted(VALID_RISKS)}"
            ),
        )
    active_ladder = ladder if ladder is not None else REVIEW_LADDERS[risk]

    author_family = resolve_author_family(inputs.author_model, inputs.author_family)
    if author_family in UNRESOLVED_AUTHOR_FAMILIES:
        reason = {
            UNKNOWN_AUTHOR_FAMILY: (
                f"author identity unknown — cannot resolve a model family from "
                f"author_model={inputs.author_model!r}"
            ),
            AMBIGUOUS_AUTHOR_FAMILY: (
                f"author harness is multi-model and ambiguous (author_model={inputs.author_model!r}) — "
                "supply a concrete author model (e.g. 'cursor:gpt-5.6-sol') or a validated author_family override"
            ),
            CONFLICTING_AUTHOR_FAMILY: (
                f"author identity conflict — the model embedded in author_model={inputs.author_model!r} "
                f"disagrees with the declared author_family={inputs.author_family!r} override"
            ),
        }[author_family]
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_MODEL_CATALOG["schema_version"],
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=reason,
        )

    trace: list[CandidateResult] = []
    advisory: list[CandidateResult] = []
    selected: CandidateResult | None = None

    for rung in active_ladder:
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
            promoted = CandidateResult(
                name=best.name,
                concrete_model=best.concrete_model,
                family=best.family,
                route=best.route,
                transport=best.transport,
                status="selected",
                reason=None,
                health=best.health,
            )
            for i, entry in enumerate(trace):
                if entry is best:
                    trace[i] = promoted
                    break
            selected = promoted

    substitution_note = None
    if selected is not None:
        default_first = active_ladder[0][0] if active_ladder and active_ladder[0] else None
        if default_first is not None and selected.name != default_first.name:
            substitution_note = f"substituted {selected.name} for default first pick {default_first.name}"

    return ReviewerResolution(
        selected=selected,
        advisory=tuple(advisory),
        trace=tuple(trace),
        substitution_note=substitution_note,
        policy_version=_MODEL_CATALOG["schema_version"],
        catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
        resolved_risk=risk,
    )
