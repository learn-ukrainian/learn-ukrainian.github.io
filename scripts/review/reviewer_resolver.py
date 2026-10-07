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
versioned ``scripts/config/model_catalog.yaml`` catalog at import time
(``REVIEW_CANDIDATES`` / ``REVIEW_LADDERS`` via ``_catalog_candidate`` /
``_catalog_ladder``). Policy changes belong in YAML: critical admits Sol / Opus / Grok;
Fable holds no review role (#9583); native and runtime-attested Cursor Grok are
regular code/infra reviewers at every risk (operator decision 2026-10-05, #9769).
A formal review at high or critical risk is performed only by the models
``review_scheduler.risk_reviewer_models`` lists; that is an
eligibility gate, so it binds explicit pins and custom ladders too.
``glm-5.3`` remains catalogued for an explicit ``--reviewer`` pin only.
Its separate freshness lint forces a provider/CLI/source review every 30 days
without making a stale catalog an operational outage at runtime.

Optional subject seats, subject families, and owned paths exclude the seat a
change governs (for example every Grok candidate when the diff edits
``scripts/agent_runtime/adapters/grok_build.py``). Omitting all three leaves
selection unchanged. Ambiguous path inference fails closed instead of guessing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from fnmatch import fnmatchcase
from typing import Literal

from scripts.agent_runtime.adapters.acpx import ACPX_PARTICIPANT_CATALOG_TRANSPORTS, ACPX_SUPPORTED_PARTICIPANTS
from scripts.agent_runtime.agent_identity import resolve_retired_agent_alias
from scripts.audit import model_families
from scripts.fleet import credit_lane
from scripts.review.model_catalog import (
    VALID_REVIEW_PROFILES,
    VALID_RISKS,
    invocation_model,
    load_model_catalog,
    resolve_catalog_model_id,
    retired_model_refusal,
    risk_reviewer_refusal,
)
from scripts.review.reviewer_scheduler import circuit_exclusion_reason, selection_key
from scripts.review.security_paths import effective_review_risk, is_security_sensitive_change
from scripts.review.subject_seat import prepare_subject_exclusion, subject_exclusion_reason

CandidateStatus = Literal["eligible", "selected", "advisory_only", "excluded"]
_SEALED_REVIEW_EXECUTABLE = "agent_runtime.runner:invoke_inter_agent"

# Operator 2026-09-27: "only claude, gpt and gemini should be involved in
# ukrainian content. no other models allowed if it is about ukrainian lang.
# culture, heritage."
UKRAINIAN_CONTENT_PATHS = (
    "curriculum/",
    "scripts/curriculum/",
    "scripts/data/stress_overrides.yaml",
    "scripts/verification/stress*",
    "scripts/pipeline/stress_annotator.py",
    "scripts/lexicon/",
    "site/src/lib/lexicon/",
    "scripts/review/prompts/",
    "scripts/build/phases/",
    "scripts/build/fresh/prompt*",
    "docs/epics/fresh-build-*",
    "schemas/activities-*",
)
_UKRAINIAN_CONTENT_FAMILIES = frozenset({"anthropic", "openai", "google"})


def is_ukrainian_content_change(inputs: ResolverInputs) -> bool:
    """Classify a review from its paths or explicit language routing signal."""
    if inputs.language_lane or inputs.review_profile.strip().casefold() == "ukrainian":
        return True
    return any(
        path == pattern or (pattern.endswith("/") and path.startswith(pattern)) or fnmatchcase(path, pattern)
        for path in (*inputs.changed_paths, *inputs.owned_paths)
        for pattern in UKRAINIAN_CONTENT_PATHS
    )


# --- family resolution -------------------------------------------------------


from learn_ukrainian_v4_runtime.identity import (
    _VALID_CONCRETE_FAMILIES as _VALID_CONCRETE_FAMILIES,
)
from learn_ukrainian_v4_runtime.identity import (
    AMBIGUOUS_AUTHOR_FAMILY as AMBIGUOUS_AUTHOR_FAMILY,
)
from learn_ukrainian_v4_runtime.identity import (
    AMBIGUOUS_HARNESS_SEATS as AMBIGUOUS_HARNESS_SEATS,
)
from learn_ukrainian_v4_runtime.identity import (
    CONFLICTING_AUTHOR_FAMILY as CONFLICTING_AUTHOR_FAMILY,
)
from learn_ukrainian_v4_runtime.identity import (
    CURSOR_AUTO_HARNESS_SEATS as CURSOR_AUTO_HARNESS_SEATS,
)
from learn_ukrainian_v4_runtime.identity import (
    CURSOR_AUTO_MODEL_TOKENS as CURSOR_AUTO_MODEL_TOKENS,
)
from learn_ukrainian_v4_runtime.identity import (
    CURSOR_AUTO_UNION_FAMILIES as CURSOR_AUTO_UNION_FAMILIES,
)
from learn_ukrainian_v4_runtime.identity import (
    CURSOR_AUTO_UNION_FAMILY as CURSOR_AUTO_UNION_FAMILY,
)
from learn_ukrainian_v4_runtime.identity import (
    UNATTESTED_AUTHOR_FAMILY as UNATTESTED_AUTHOR_FAMILY,
)
from learn_ukrainian_v4_runtime.identity import (
    UNATTESTED_HARNESS_SEATS as UNATTESTED_HARNESS_SEATS,
)
from learn_ukrainian_v4_runtime.identity import (
    UNATTESTED_MODEL_TOKENS as UNATTESTED_MODEL_TOKENS,
)
from learn_ukrainian_v4_runtime.identity import (
    UNKNOWN_AUTHOR_FAMILY as UNKNOWN_AUTHOR_FAMILY,
)
from learn_ukrainian_v4_runtime.identity import (
    UNRESOLVED_AUTHOR_FAMILIES as UNRESOLVED_AUTHOR_FAMILIES,
)
from learn_ukrainian_v4_runtime.identity import (
    resolve_author_family as resolve_author_family,
)
from learn_ukrainian_v4_runtime.identity import (
    resolve_family as resolve_family,
)

# --- candidates ---------------------------------------------------------------


@dataclass(frozen=True)
class ReviewerCandidate:
    name: str
    family: str
    concrete_model: str
    route: str
    transport: str
    invocation: str
    quality_tier: str
    last_resort: bool = False
    model_roles: frozenset[str] = field(default_factory=frozenset)
    # Optional subset for semantic ranking, never a grant of activity roles.
    suitability_roles: frozenset[str] = field(default_factory=frozenset)
    # Same-model route preference; other models retain their resource ranking.
    transport_fallback_for: str | None = None
    health_keys: frozenset[str] = field(default_factory=frozenset)
    requires_silence_timeout: bool = False
    # Fail-closed data-egress gate: eligible only when the caller's
    # data_egress_policy exactly matches this value. None = no egress gate.
    requires_data_egress_policy: str | None = None
    # Hard exclusion regardless of anything else (e.g. cost policy).
    always_excluded_reason: str | None = None
    review_profiles: frozenset[str] = field(default_factory=lambda: frozenset({"code"}))
    capabilities: frozenset[str] = field(default_factory=frozenset)
    # Domains (review_profile-adjacent, e.g. "folk_content") where this
    # candidate is a hard no per model-assignment.md carve-outs.
    domain_excluded_from: frozenset[str] = field(default_factory=frozenset)
    # Author families for which this candidate is advisory-only rather than
    # hard-excluded on a same-family match (e.g. openai_frontier for an
    # OpenAI-family author: still consulted, never the formal gate).
    advisory_only_for_author_families: frozenset[str] = field(default_factory=frozenset)
    endpoint: str = ""
    formal_review_eligible: bool = False
    formal_review_exclusion_reason: str = ""
    participant: str = ""
    adapter_transport: str = ""
    catalog_transport: str = ""
    sealed_executable: str = ""
    quota_bucket: str = ""
    credential_bucket: str = ""
    quota_limit: int = 0
    credential_limit: int = 0
    capacity_weight: float = 1.0


_MODEL_CATALOG = load_model_catalog()
_SCHEDULER_POLICY = _MODEL_CATALOG["review_scheduler"]
_SCHEDULER_POLICY_VERSION = _SCHEDULER_POLICY["policy_version"]


def _catalog_candidate(name: str) -> ReviewerCandidate:
    from scripts.review.role_resolution import resolve_routing_reference

    if "roles" in _MODEL_CATALOG:
        matches = [
            (seat_name, route_name)
            for seat_name, seat in _MODEL_CATALOG["seats"].items()
            for route_name, route in seat["routes"].items()
            if route.get("legacy_name") == name
        ]
        seat_name, route_name = matches[0]
        raw = resolve_routing_reference(
            {"role": "legacy_reviewers", "seat": seat_name, "route_name": route_name, "field": "candidate"},
            _MODEL_CATALOG,
        )
    else:
        raw = _MODEL_CATALOG["review_candidates"][name]
    model_id = raw["model_id"]
    model = _MODEL_CATALOG["models"][model_id]
    endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(raw["route"], {})
    endpoint_models = endpoint.get("models", [])
    endpoint_formal = bool(endpoint.get("formal_review_eligible", False))
    model_formal = isinstance(endpoint_models, list) and model_id in endpoint_models
    exclusion_reason = str(endpoint.get("formal_review_exclusion_reason", ""))
    if endpoint_formal and not model_formal:
        exclusion_reason = f"sealed endpoint {raw['route']!r} is not pinned for model {model_id!r}"
    return ReviewerCandidate(
        name=name,
        family=model["family"],
        concrete_model=model_id,
        route=raw["route"],
        transport=raw["transport"],
        invocation=raw["invocation"],
        quality_tier=model["tier"],
        last_resort=raw.get("last_resort", False),
        model_roles=frozenset(model["roles"]),
        suitability_roles=frozenset(raw.get("suitability_roles", [])),
        transport_fallback_for=raw.get("transport_fallback_for"),
        health_keys=frozenset(raw.get("health_keys", [])),
        requires_silence_timeout=bool(raw.get("requires_silence_timeout", False)),
        requires_data_egress_policy=raw.get("requires_data_egress_policy"),
        review_profiles=frozenset(raw.get("review_profiles", [])),
        capabilities=frozenset(raw.get("capabilities", [])),
        domain_excluded_from=frozenset(raw.get("domain_excluded_from", [])),
        advisory_only_for_author_families=frozenset(raw.get("advisory_only_for_author_families", [])),
        endpoint=raw["route"],
        formal_review_eligible=endpoint_formal and model_formal,
        formal_review_exclusion_reason=exclusion_reason,
        participant=endpoint.get("participant", ""),
        adapter_transport=endpoint.get("adapter_transport", ""),
        catalog_transport=endpoint.get("catalog_transport", ""),
        sealed_executable=endpoint.get("sealed_executable", ""),
        quota_bucket=endpoint.get("quota_bucket", ""),
        credential_bucket=endpoint.get("credential_bucket", ""),
        quota_limit=int(endpoint.get("quota_limit", 0)),
        credential_limit=int(endpoint.get("credential_limit", 0)),
        capacity_weight=float(endpoint.get("capacity_weight", 0)),
    )


REVIEW_CANDIDATES: dict[str, ReviewerCandidate] = {
    name: _catalog_candidate(name) for name in _MODEL_CATALOG["review_candidates"]
}


def candidate_dispatch_model(candidate: ReviewerCandidate) -> str:
    """The ``--model`` a review dispatch to ``candidate`` must send.

    A Cursor seat runs its exact Cursor slug (``grok-4.7-high``), because that
    slug is what the runtime then attests; other routes use the catalog id.
    """
    if candidate.transport == "cursor":
        return invocation_model(candidate.invocation) or candidate.concrete_model
    return candidate.concrete_model


# Catalog ids a Cursor review receipt may attest: the Cursor seats the resolver
# can select (pinned on the formal Cursor endpoint, #9488). Composer, Auto and
# Cursor-routed Claude are unpinned, so a verdict from them is never recorded.
FORMAL_CURSOR_REVIEW_MODELS: frozenset[str] = frozenset(
    candidate.concrete_model
    for candidate in REVIEW_CANDIDATES.values()
    if candidate.route == "cursor" and candidate.transport == "cursor" and candidate.formal_review_eligible
)


def _catalog_ladder(risk: str) -> tuple[tuple[ReviewerCandidate, ...], ...]:
    return tuple(tuple(REVIEW_CANDIDATES[name] for name in rung) for rung in _MODEL_CATALOG["review_ladders"][risk])


REVIEW_LADDERS: dict[str, tuple[tuple[ReviewerCandidate, ...], ...]] = {
    risk: _catalog_ladder(risk) for risk in sorted(VALID_RISKS)
}

# Compatibility constants for direct candidate evaluation and callers that
# explicitly imported the old default. Medium is the balanced default risk.
OPENAI_FRONTIER = REVIEW_CANDIDATES["openai_frontier"]
GROK_4_7 = REVIEW_CANDIDATES["grok-4.7"]
GROK_4_7_CURSOR_FALLBACK = REVIEW_CANDIDATES["grok-4.7-cursor-fallback"]
SONNET_5_5 = REVIEW_CANDIDATES["claude-sonnet-5-5"]
POOL = REVIEW_CANDIDATES["pool"]
GLM = REVIEW_CANDIDATES["glm-5.3"]
# Medium = practical formal CF default ladder (not authority-first).
DEFAULT_CODE_LADDER = REVIEW_LADDERS["medium"]
CRITICAL_CODE_LADDER = REVIEW_LADDERS["critical"]

# Known hard-filtered candidates outside the default ladder — kept here so the
# fail-closed exclusion logic is directly testable even where model-assignment.md
# doesn't route code review through them by default.
QWEN = ReviewerCandidate(
    name="qwen",
    family=model_families.Family.QWEN.value,
    concrete_model="qwen3-max",
    route="qwen",
    transport="hermes",
    invocation=".venv/bin/python scripts/delegate.py dispatch --agent qwen",
    quality_tier="specialist",
    always_excluded_reason="excluded from routine/automatic routing (cost) — model-assignment.md",
)

_HEALTH_RANK: dict[str, int] = {"healthy": 0, "degraded": 1, "near_cap": 2, "degraded_telemetry": 3, "unhealthy": 4}
_HEALTH_ALIASES: dict[str, str | None] = {
    "healthy": "healthy",
    "cool": "healthy",
    "pre_launch": "healthy",
    "degraded": "degraded",
    "warm": "degraded",
    "near_cap": "near_cap",
    "hot": "near_cap",
    "degraded_telemetry": "degraded_telemetry",
    # routing-budget emits this when CodexBar probe fails/times out. That is
    # missing capacity evidence, not a proven dead seat — fail-open like
    # "unknown" (operator 2026-08-03: red probe must not ban CF lanes).
    "unavailable": None,
    # The endpoint uses unknown when budget evidence is absent. Preserve the
    # module's fail-open convention by treating it exactly like a missing key.
    "unknown": None,
    "unhealthy": "unhealthy",
}


def _health_rank(status: str | None) -> int:
    # Fail-open: no signal for this lane is read as healthy, not unhealthy —
    # matches scripts/api/lane_health.py's fail-open convention.
    if status is None:
        return 0
    return _HEALTH_RANK[status]


def _normalize_health_status(value: object, *, label: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} health status must be a non-empty string")
    token = value.strip().lower()
    if token not in _HEALTH_ALIASES:
        raise ValueError(f"{label} has unsupported health status {value!r}; expected one of {sorted(_HEALTH_ALIASES)}")
    return _HEALTH_ALIASES[token]


def normalize_routing_snapshot(snapshot: Mapping[str, object] | None) -> dict[str, str]:
    """Accept either a flat route->status map or `/api/state/routing-budget`."""
    if not snapshot:
        return {}
    if not isinstance(snapshot, Mapping):
        raise ValueError("routing snapshot must be a mapping")
    if "agents" not in snapshot:
        normalized_flat: dict[str, str] = {}
        for route, status in snapshot.items():
            normalized_status = _normalize_health_status(status, label=str(route))
            if normalized_status is not None:
                normalized_flat[str(route)] = normalized_status
        return normalized_flat

    agents = snapshot.get("agents")
    if not isinstance(agents, Mapping):
        raise ValueError("routing snapshot agents must be a mapping")
    normalized: dict[str, str] = {}
    for route, raw in agents.items():
        if not isinstance(raw, Mapping):
            raise ValueError(f"routing snapshot agents.{route} must be a mapping")
        health = raw.get("health")
        status = raw.get("status")
        is_healthy = isinstance(health, Mapping) and health.get("healthy") is True
        if is_healthy and status == "unavailable":
            normalized[str(route)] = "degraded_telemetry"
            continue
        if isinstance(health, Mapping) and health.get("healthy") is False:
            normalized[str(route)] = "unhealthy"
            continue
        if status is None and is_healthy:
            normalized[str(route)] = "healthy"
            continue
        if status is None:
            # A transaction-local scheduler snapshot may carry only pressure
            # counters. Health remains fail-open when it is genuinely absent.
            continue
        normalized_status = _normalize_health_status(status, label=f"agents.{route}")
        if normalized_status is not None:
            normalized[str(route)] = normalized_status
    return normalized


@dataclass(frozen=True)
class ResolverInputs:
    # Concrete seat/model id, OR a "<ambiguous-harness>:<concrete-model>"
    # composite (e.g. "cursor:claude-opus-5-5") disambiguating a multi-model
    # harness session. See resolve_author_family for the exact contract.
    author_model: str
    review_profile: str = "code"
    risk: str = "medium"
    domain: str = "code"
    changed_paths: tuple[str, ...] = ()
    language_lane: bool = False
    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    # Optional exact catalog model role (for example ``security_review``).
    # When omitted, profile/risk role suitability comes from model_catalog.
    requested_role: str | None = None
    # Fail-closed: None/unrecognized means the strictest reading, not "anything goes."
    data_egress_policy: str | None = None
    isolation_required: bool = False
    # Fresh CodexBar/routing-budget snapshot: seat or family name -> health status
    # ("healthy" | "degraded" | "near_cap" | "unhealthy"). Optional — omit for a
    # snapshot-blind resolution (ladder order alone decides).
    routing_snapshot: Mapping[str, object] | None = None
    # Explicit, caller-asserted author model family (e.g. from session logs),
    # validated against _VALID_CONCRETE_FAMILIES. Required to disambiguate a
    # bare ambiguous-harness author_model; optional corroboration otherwise —
    # a mismatch against the resolved family is a fail-closed conflict.
    author_family: str | None = None
    # Exact PR head used solely for a stable final tie-break among equal
    # quality/pressure candidates. It never relaxes a hard policy gate.
    exact_head: str | None = None
    # Formal review is the resolver's normal mode. Advisory callers may opt
    # out only when they are not attempting to satisfy the cross-family gate.
    formal_review: bool = True
    # An explicit pin is an exceptional pressure override. It still receives
    # every safety, independence, egress, isolation, executable and circuit
    # gate; a missing reason fails closed.
    pinned_candidate: str | None = None
    pressure_override_reason: str | None = None
    # Seats whose own boundary this change governs. Empty means "no subject
    # information" and must leave selection byte-identical.
    subject_seats: frozenset[str] = field(default_factory=frozenset)
    subject_families: frozenset[str] = field(default_factory=frozenset)
    owned_paths: tuple[str, ...] = ()
    # Normalized paths that inferred a subject seat. Trace text only.
    subject_evidence: tuple[str, ...] = ()
    # Complete branch authorship (#9739): every committed author family plus an
    # incoming writer's (``record_cf_verdict.collect_branch_review_facts``).
    # Selection excludes the whole set. ``author_model``/``author_family`` may
    # add to it but never replace or shrink it. Empty keeps single-author mode.
    author_families: frozenset[str] = field(default_factory=frozenset)


def complete_author_families(inputs: ResolverInputs, single_family: str) -> frozenset[str] | None:
    """The author families selection excludes, or None for invalid/conflicting attribution.

    Without ``inputs.author_families`` this is just ``single_family``.
    Unknown committed authors are reviewable by any known reviewer family (#9944).
    """
    if not inputs.author_families:
        return frozenset({single_family})
    members = set(inputs.author_families)
    if inputs.author_model or inputs.author_family:
        members.add(single_family)
    if not all(
        member in _VALID_CONCRETE_FAMILIES or member in {CURSOR_AUTO_UNION_FAMILY, UNKNOWN_AUTHOR_FAMILY}
        for member in members
    ):
        return None
    return frozenset(members)


@dataclass(frozen=True)
class CandidateResult:
    name: str
    concrete_model: str
    family: str
    route: str
    transport: str
    invocation: str
    quality_tier: str
    requires_silence_timeout: bool
    status: CandidateStatus
    reason: str | None
    health: str | None
    suitability_rank: int | None = None
    # Pure deterministic balancing receipt for eligible candidates. The tuple
    # is deliberately opaque-but-stable so ledger callers can persist the
    # exact decision without this resolver acquiring storage authority.
    selection_score: tuple[object, ...] | None = None
    # Credit-period receipt (#9517) when a near-cap lane's published
    # ``credit_balance_present`` state decided this candidate's eligibility.
    credit: Mapping[str, object] | None = field(default=None, hash=False)

    @property
    def quota_bucket(self) -> str:
        """Canonical quota bucket for persistence with this pure receipt."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return str(endpoint.get("quota_bucket", ""))

    @property
    def credential_bucket(self) -> str:
        """Credential-sharing bucket bound to the sealed ACP participant."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return str(endpoint.get("credential_bucket", ""))

    @property
    def quota_limit(self) -> int:
        """Rolling-window accounting capacity supplied to ledger admission."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return int(endpoint.get("quota_limit", 0))

    @property
    def credential_limit(self) -> int:
        """Shared credential admission capacity supplied to the ledger."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return int(endpoint.get("credential_limit", 0))

    @property
    def participant(self) -> str:
        """Exact ACPX participant used by the sealed review executable."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return str(endpoint.get("participant", ""))

    @property
    def adapter_transport(self) -> str:
        """Runner-owned adapter transport, distinct from catalog model transport."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return str(endpoint.get("adapter_transport", ""))

    @property
    def sealed_executable(self) -> str:
        """Canonical sealed execution boundary that invokes the participant."""
        endpoint = _MODEL_CATALOG["review_scheduler"]["endpoints"].get(self.route, {})
        return str(endpoint.get("sealed_executable", ""))


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
    # Dual-family quorum plan for a generic unattested-harness author. ``selected`` stays None — there
    # is no single reviewer of record; BOTH quorum seats must independently
    # return an exact-head PASS verdict. Because the seats are from distinct
    # attested families and the hidden author is at most one family, at
    # least one quorum verdict is necessarily cross-family.
    quorum: tuple[CandidateResult, ...] = ()
    quorum_rule: str | None = None


_DUAL_FAMILY_QUORUM_RULE = (
    "unattested-harness author (harness attests no pinned model): the formal gate "
    "requires two independent exact-head PASS verdicts from distinct attested, "
    "formal-review-eligible families; whichever family the hidden author actually "
    "was, at least one verdict is necessarily cross-family"
)


def _health_of(candidate: ReviewerCandidate, snapshot: Mapping[str, str] | None) -> str | None:
    if not snapshot:
        return None
    return (
        snapshot.get(candidate.name)
        or snapshot.get(candidate.route)
        or snapshot.get(candidate.concrete_model)
        or snapshot.get(candidate.family)
        or next(
            (snapshot[key] for key in sorted(candidate.health_keys) if key in snapshot),
            None,
        )
    )


def _near_cap_credit(candidate: ReviewerCandidate, snapshot: Mapping[str, object] | None) -> dict[str, object] | None:
    """Credit receipt for a near-cap candidate from the snapshot's ``agents.<route>.credit`` (#9517).

    Only a full routing-budget snapshot carries the credit state its producer
    computed with :func:`credit_lane.lane_credit_state`; a flat health map has
    none. :func:`credit_lane.published_credit_relief` re-checks the published
    state against the complete lane record (snapshot staleness, probe
    freshness, age and stale flag; #9740 F6), the local policy, the clock and
    the current shared runtime rate-limit records.
    """
    agents = snapshot.get("agents") if isinstance(snapshot, Mapping) else None
    record = agents.get(candidate.route) if isinstance(agents, Mapping) else None
    if not isinstance(record, Mapping):
        return None
    diagnostics = snapshot.get("diagnostics") if isinstance(snapshot, Mapping) else None
    snapshot_stale = isinstance(diagnostics, Mapping) and diagnostics.get("stale") is True
    return credit_lane.published_credit_relief(
        candidate.route,
        record.get("credit"),
        candidate.concrete_model,
        record=record,
        snapshot_stale=snapshot_stale,
    )


def _hard_exclusion_reason(candidate: ReviewerCandidate, inputs: ResolverInputs) -> str | None:
    """Non-family exclusions: cost policy, domain carve-out, data-egress
    (fail-closed), missing required capability. Family/advisory handling is
    the caller's job — this only covers filters that apply regardless."""
    if candidate.always_excluded_reason:
        return candidate.always_excluded_reason
    if (
        inputs.review_profile.strip().casefold() in {"code", "infra"}
        and is_security_sensitive_change(inputs.changed_paths, inputs.owned_paths)
        and "critical_review" not in candidate.model_roles
    ):
        return "security-sensitive target requires the catalog critical_review role"
    if inputs.formal_review:
        if not candidate.formal_review_eligible:
            return candidate.formal_review_exclusion_reason or (
                "formal-review transport is not eligible for a sealed cross-family gate"
            )
        if not candidate.endpoint or candidate.endpoint != candidate.route:
            return "sealed endpoint identity is missing or does not match the candidate route"
        if not candidate.participant or not candidate.sealed_executable:
            return "sealed ACP participant or review executable identity is missing"
        if candidate.adapter_transport != "acp":
            return "formal-review candidate is not bound to the ACP adapter transport"
        if candidate.sealed_executable != _SEALED_REVIEW_EXECUTABLE:
            return "candidate is not bound to the sealed ACP executable"
        if candidate.participant not in ACPX_SUPPORTED_PARTICIPANTS:
            return "candidate ACP participant is not enabled by the runner-owned adapter registry"
        if ACPX_PARTICIPANT_CATALOG_TRANSPORTS.get(candidate.participant) != candidate.catalog_transport:
            return "candidate catalog transport does not match its runner-owned ACP participant"
        if candidate.transport != candidate.catalog_transport:
            return "candidate transport does not match its ACPX catalog transport"
        if (
            not candidate.quota_bucket
            or not candidate.credential_bucket
            or candidate.quota_limit < 1
            or candidate.credential_limit < 1
            or candidate.capacity_weight <= 0
        ):
            return "formal-review capacity configuration is invalid"
    review_profile = inputs.review_profile.strip().casefold()
    if review_profile not in candidate.review_profiles:
        return (
            f"review profile exclusion: {candidate.name} supports "
            f"{sorted(candidate.review_profiles)}, got {inputs.review_profile!r}"
        )
    if inputs.domain in candidate.domain_excluded_from:
        return f"hard domain exclusion: {candidate.name} is excluded from {inputs.domain!r} review"
    if (
        candidate.requires_data_egress_policy is not None
        and inputs.data_egress_policy != candidate.requires_data_egress_policy
    ):
        return (
            f"data-egress policy fail-closed: {candidate.name} requires "
            f"data_egress_policy={candidate.requires_data_egress_policy!r}, "
            f"got {inputs.data_egress_policy!r} (requires --data-egress-policy {candidate.requires_data_egress_policy})"
        )
    missing = inputs.required_capabilities - candidate.capabilities
    if missing:
        return f"missing required capabilities: {sorted(missing)}"
    if inputs.isolation_required and "isolation" not in candidate.capabilities:
        return "isolation required but candidate does not support process isolation"
    return None


def _suitability_rank(candidate: ReviewerCandidate, inputs: ResolverInputs) -> int | None:
    """Return catalog-backed semantic suitability, or fail closed.

    This intentionally precedes quality and all resource pressure. It is not a
    probabilistic score and has no rotation term: a lower integer means a
    better profile/risk role match among candidates that passed hard gates.

    A requested role narrows the profile/risk-qualified set to the candidates
    holding it (all ranked equal); it never admits a candidate the profile/risk
    order excludes, so it cannot lower the critical-risk floor (#9488).
    """
    profile = inputs.review_profile.strip().casefold()
    risk = inputs.risk.strip().casefold()
    try:
        ordered_roles = _SCHEDULER_POLICY["profile_risk_role_order"][profile][risk]
    except (KeyError, TypeError):
        return None
    roles = candidate.suitability_roles or candidate.model_roles
    rank = next((rank for rank, role in enumerate(ordered_roles) if role in roles), None)
    requested_role = (inputs.requested_role or "").strip()
    if requested_role:
        return 0 if rank is not None and requested_role in candidate.model_roles else None
    return rank


def _retired_alias_target(candidate: ReviewerCandidate) -> str | None:
    """Return the permanent substitute for a retired CLI seat, or None.

    Checks the candidate's route (dispatch agent), quota_bucket, participant,
    and name against ``RETIRED_AGENT_ALIASES`` (currently ``glm``→``cursor``,
    ``gemini``→``agy``). Catalogued candidates remain pin-eligible; automatic
    selection must not pick a retired seat.
    """
    for token in (candidate.route, candidate.quota_bucket, candidate.participant, candidate.name):
        target = resolve_retired_agent_alias(token)
        if target is not None:
            return target
    return None


def _author_family_exclusion(candidate: ReviewerCandidate, family: str, health: str | None) -> CandidateResult | None:
    """Independence of ``candidate`` from one author ``family``: an exclusion, an advisory-only result, or None."""

    def result(status: CandidateStatus, reason: str) -> CandidateResult:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status=status,
            reason=reason,
            health=health,
        )

    from scripts.review.family_exclusions import family_exclusion

    exclusion = family_exclusion(
        family=candidate.family,
        route=candidate.route,
        transport=candidate.transport,
        author_family=family,
        advisory_only_for_author_families=candidate.advisory_only_for_author_families,
        union_family=CURSOR_AUTO_UNION_FAMILY,
        union_families=CURSOR_AUTO_UNION_FAMILIES,
    )
    return result(*exclusion) if exclusion else None



def evaluate_candidate(
    candidate: ReviewerCandidate,
    inputs: ResolverInputs,
    *,
    author_family: str | None = None,
    review_mode: str = "cross_family",
) -> CandidateResult:
    """Evaluate one candidate against ``inputs`` independent of ladder position.

    Exposed directly (not just via :func:`resolve_reviewer`) so domain and
    data-egress fail-closed behavior is testable per-candidate, including for
    candidates that aren't in the default ladder (e.g. ``GLM``, ``QWEN``).
    ``red_team`` relaxes authorship independence only; callers must first
    validate an explicit adversarial prompt bound to the completed review.
    """
    if review_mode not in {"cross_family", "red_team"}:
        raise ValueError("unsupported review mode")
    # Direct dispatch admission calls this without walking a ladder. The floor
    # must bind here too, before suitability or explicit-pin evaluation.
    inputs = replace(
        inputs,
        risk=effective_review_risk(
            inputs.risk, inputs.changed_paths, inputs.owned_paths, profile=inputs.review_profile
        ),
    )
    family = (
        author_family if author_family is not None else resolve_author_family(inputs.author_model, inputs.author_family)
    )
    normalized_snapshot = normalize_routing_snapshot(inputs.routing_snapshot)
    health = _health_of(candidate, normalized_snapshot)
    snapshot = inputs.routing_snapshot
    agents = snapshot.get("agents") if isinstance(snapshot, Mapping) else None
    record = agents.get(candidate.route) if isinstance(agents, Mapping) else None
    if (
        isinstance(record, dict)
        and (record.get("status") == "hot" or isinstance(record.get("pace_deficit"), dict))
        and health
        in {
            "healthy",
            "degraded",
            "near_cap",
            None,
        }
    ):
        # The owner's pace and hot-label reading (#9740): a weekly-pace hot label it
        # clears (#9040) is cleared here too; one it keeps stays near cap.
        diagnostics = snapshot.get("diagnostics")
        facts = credit_lane.routing_facts(
            candidate.route,
            record,
            model=candidate.concrete_model,
            snapshot_metadata=diagnostics if isinstance(diagnostics, Mapping) else None,
        )
        if facts.uncovered is True:
            health = "near_cap"
        elif facts.status in {"cool", "warm"}:
            health = _normalize_health_status(facts.status, label=candidate.route)

    # Catalog validation protects the installed ladders; this independent gate
    # also protects explicit pins and custom candidates before any quality prior.
    refusal = retired_model_refusal(candidate.concrete_model, _MODEL_CATALOG)
    model_id = resolve_catalog_model_id(candidate.concrete_model, _MODEL_CATALOG)
    model_family = _MODEL_CATALOG["models"].get(model_id, {}).get("family")
    if candidate.family not in _VALID_CONCRETE_FAMILIES:
        refusal = "reviewer family unknown: a known concrete family is required"
    if candidate.family == "deepseek" or model_family == "deepseek" or candidate.route == "deepseek":
        refusal = "DeepSeek is excluded from dispatch and review by core.md P2"
    if inputs.risk.strip().casefold() == "critical" and (model_id or "").startswith("claude-sonnet-"):
        refusal = "Sonnet is excluded from security review by core.md P2"
    if refusal:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=refusal,
            health=health,
        )

    if is_ukrainian_content_change(inputs) and candidate.family not in _UKRAINIAN_CONTENT_FAMILIES:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason="Ukrainian-content language-lanes exclusion: reviewer model family must be Claude, GPT or Gemini",
            health=health,
        )
    if inputs.subject_seats or inputs.subject_families:
        # The Grok model governs both admitted transports (#9769).
        subject_families = inputs.subject_families
        if "cursor" in inputs.subject_seats:
            subject_families = frozenset((*subject_families, "xai"))
        subject_reason = subject_exclusion_reason(
            candidate,
            seats=inputs.subject_seats,
            families=subject_families,
            evidence=inputs.subject_evidence,
        )
        if subject_reason:
            return CandidateResult(
                name=candidate.name,
                concrete_model=candidate.concrete_model,
                family=candidate.family,
                route=candidate.route,
                transport=candidate.transport,
                invocation=candidate.invocation,
                quality_tier=candidate.quality_tier,
                requires_silence_timeout=candidate.requires_silence_timeout,
                status="excluded",
                reason=subject_reason,
                health=health,
            )

    # Operator 2026-09-25: Gemini reviews Ukrainian only, never code. Keep this
    # hard gate even for injected ladders and explicitly pinned candidates.
    if candidate.concrete_model.casefold().startswith("gemini-") or candidate.route == "agy":
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason="operator 2026-09-25: Gemini reviews Ukrainian only, never code — model-assignment.md",
            health=health,
        )

    retired_target = _retired_alias_target(candidate)
    if retired_target is not None and inputs.pinned_candidate != candidate.name:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=f"retired→{retired_target}",
            health=health,
        )

    authors = complete_author_families(inputs, family)
    if authors is None:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason="complete author family set holds an unresolved family — independence cannot be proven",
            health=health,
        )
    advisory: CandidateResult | None = None
    for author in sorted(authors):
        # Only the recorder's prompt-bound red-team path opts into this.
        # Qualification, risk, subject exclusions and runtime identity still bind.
        if review_mode == "red_team" and candidate.family not in {*UNRESOLVED_AUTHOR_FAMILIES, "unknown"}:
            continue
        result = _author_family_exclusion(candidate, author, health)
        if result is not None and result.status == "excluded":
            return result
        advisory = advisory or result
    if advisory is not None:
        return advisory

    reason = _hard_exclusion_reason(candidate, inputs)
    if not reason and inputs.formal_review:
        # Operator decision 2026-10-02 (#9538): the catalog names the only
        # models that perform a formal review at this risk, on any transport.
        reason = risk_reviewer_refusal(candidate.concrete_model, inputs.risk, _MODEL_CATALOG)
    if reason:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=reason,
            health=health,
        )
    circuit_reason = circuit_exclusion_reason(candidate, inputs.routing_snapshot)
    if circuit_reason:
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=circuit_reason,
            health=health,
        )
    if health == "degraded_telemetry":
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=f"degraded_telemetry: seat snapshot for {candidate.name!r} is self-contradictory (healthy=true, status=unavailable)",
            health=health,
        )
    if health == "unhealthy":
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason="lane health is unhealthy — route is operationally unavailable",
            health=health,
        )
    credit: dict[str, object] | None = None
    if health == "near_cap" and inputs.pinned_candidate != candidate.name:
        # A near-cap lane with a usable credit balance stays eligible for an
        # allowlisted model only (#9517); every other credit state keeps the cap.
        credit = _near_cap_credit(candidate, inputs.routing_snapshot)
        reason = "quota bucket is near cap — automatic assignments are prohibited"
        if credit is not None and credit["state"] != credit_lane.CREDIT_BALANCE_PRESENT:
            reason += f" ({credit['state']}: {credit['reason']})"
        elif credit is not None and not credit["model_allowed"]:
            reason += (
                f" (credit balance present, but {candidate.concrete_model} is outside the credit-period "
                f"allowlist [{', '.join(credit['allowed_models'])}])"
            )
        if credit is None or credit["state"] != credit_lane.CREDIT_BALANCE_PRESENT or not credit["model_allowed"]:
            return CandidateResult(
                name=candidate.name,
                concrete_model=candidate.concrete_model,
                family=candidate.family,
                route=candidate.route,
                transport=candidate.transport,
                invocation=candidate.invocation,
                quality_tier=candidate.quality_tier,
                requires_silence_timeout=candidate.requires_silence_timeout,
                status="excluded",
                reason=reason,
                health=health,
                credit=credit,
            )

    suitability_rank = _suitability_rank(candidate, inputs)
    if suitability_rank is None:
        requested_role = (inputs.requested_role or "").strip()
        requested = (
            requested_role
            if requested_role and requested_role not in candidate.model_roles
            else f"{inputs.review_profile}/{inputs.risk} catalog suitability"
        )
        return CandidateResult(
            name=candidate.name,
            concrete_model=candidate.concrete_model,
            family=candidate.family,
            route=candidate.route,
            transport=candidate.transport,
            invocation=candidate.invocation,
            quality_tier=candidate.quality_tier,
            requires_silence_timeout=candidate.requires_silence_timeout,
            status="excluded",
            reason=f"missing required review role suitability: {requested}",
            health=health,
            credit=credit,
        )

    return CandidateResult(
        name=candidate.name,
        concrete_model=candidate.concrete_model,
        family=candidate.family,
        route=candidate.route,
        transport=candidate.transport,
        invocation=candidate.invocation,
        quality_tier=candidate.quality_tier,
        requires_silence_timeout=candidate.requires_silence_timeout,
        status="eligible",
        reason=None,
        health=health,
        suitability_rank=suitability_rank,
        credit=credit,
    )


def _best_eligible(
    eligible_by_fit_and_tier: dict[tuple[bool, int, int, bool], list[tuple[ReviewerCandidate, CandidateResult, int]]],
    *,
    exclude_families: frozenset[str] = frozenset(),
) -> tuple[ReviewerCandidate, CandidateResult, int] | None:
    """Pick the best eligible entry: primary before last resort, then suitability and tier,
    plan-backed before credit-backed, deterministic selection_score inside it. ``exclude_families`` lets the
    dual-family quorum path pick a second seat outside the first seat's
    family without relaxing the fit-before-pressure ordering. An eligible
    same-model primary transport precedes its declared fallback."""
    filtered = {
        fit_key: kept
        for fit_key, entries in eligible_by_fit_and_tier.items()
        if (kept := [item for item in entries if item[0].family not in exclude_families])
    }
    # A same-model transport fallback cannot compete with its eligible primary
    # on resource scores or head hashes. Other candidates keep their exact order.
    primary_names = {candidate.name for entries in filtered.values() for candidate, _, _ in entries}
    filtered = {
        fit_key: kept
        for fit_key, entries in filtered.items()
        if (kept := [item for item in entries if item[0].transport_fallback_for not in primary_names])
    }
    if not filtered:
        return None
    best_fit_and_tier = min(filtered)
    return min(filtered[best_fit_and_tier], key=lambda item: item[1].selection_score or ())


def resolve_reviewer(
    inputs: ResolverInputs,
    ladder: tuple[tuple[ReviewerCandidate, ...], ...] | None = None,
    *,
    runtime_state: Mapping[str, object] | None = None,
    excluded_quota_buckets: frozenset[str] = frozenset(),
) -> ReviewerResolution:
    """Apply hard policy then balance the best eligible quality tier.

    Advisory-only candidates
    (e.g. ``openai_frontier`` for an OpenAI-family author) are always
    surfaced separately, regardless of which rung is selected.

    Fails closed — no candidate walked, ``selected`` stays ``None`` — when
    the author's model family cannot be resolved to a concrete family (an
    unrecognized identity, a bare ambiguous-model harness with no
    disambiguation, or a conflicting override). See
    :func:`resolve_author_family`.

    Cursor Auto authors use the Cursor family and a single cross-family
    reviewer outside Cursor. Quorum logic remains supported as fallback for
    generic unattested harnesses.
    """
    if runtime_state is not None:
        # The state owner injects a transaction-consistent snapshot. This
        # module never reads a database or service to fill it in.
        inputs = replace(inputs, routing_snapshot=runtime_state)
    inputs = replace(
        inputs,
        risk=effective_review_risk(
            inputs.risk, inputs.changed_paths, inputs.owned_paths, profile=inputs.review_profile
        ),
    )
    risk = (inputs.risk or "").strip().lower()
    review_profile = (inputs.review_profile or "").strip().casefold()
    if review_profile not in VALID_REVIEW_PROFILES:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=(
                f"unsupported local-code-review profile {inputs.review_profile!r}; "
                f"expected one of {sorted(VALID_REVIEW_PROFILES)}. Learner-content semantic "
                "review belongs to track-completion via post-build-review."
            ),
        )
    inputs = replace(inputs, review_profile=review_profile)
    if ladder is None and risk not in VALID_RISKS:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=(f"unsupported review risk {inputs.risk!r}; expected one of {sorted(VALID_RISKS)}"),
        )
    active_ladder = ladder if ladder is not None else REVIEW_LADDERS[risk]
    if inputs.pinned_candidate:
        pinned_definition = REVIEW_CANDIDATES.get(inputs.pinned_candidate)
        if pinned_definition is None:
            return ReviewerResolution(
                selected=None,
                advisory=(),
                trace=(),
                substitution_note=None,
                policy_version=_SCHEDULER_POLICY_VERSION,
                catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
                resolved_risk=risk,
                fail_closed_reason=f"unknown explicit reviewer pin {inputs.pinned_candidate!r}",
            )
        if all(candidate.name != pinned_definition.name for rung in active_ladder for candidate in rung):
            # Ladders express automatic preference, not an allowlist.  An
            # operator-requested canonical pin may name another catalogued
            # candidate, but it still goes through every hard eligibility,
            # suitability, isolation, capability, family, health, and circuit
            # gate below before it can be selected.
            active_ladder = (*active_ladder, (pinned_definition,))
    try:
        normalize_routing_snapshot(inputs.routing_snapshot)
    except ValueError as exc:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=f"invalid routing snapshot: {exc}",
        )

    if inputs.owned_paths or inputs.subject_seats or inputs.subject_families:
        prepared = prepare_subject_exclusion(
            subject_seats=inputs.subject_seats,
            subject_families=inputs.subject_families,
            owned_paths=inputs.owned_paths,
        )
        if prepared.fail_closed_reason:
            return ReviewerResolution(
                selected=None,
                advisory=(),
                trace=(),
                substitution_note=None,
                policy_version=_SCHEDULER_POLICY_VERSION,
                catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
                resolved_risk=risk,
                fail_closed_reason=prepared.fail_closed_reason,
            )
        inputs = replace(
            inputs,
            subject_seats=prepared.seats,
            subject_families=prepared.families,
            subject_evidence=prepared.evidence,
        )

    author_family = resolve_author_family(inputs.author_model, inputs.author_family)
    if inputs.author_families and complete_author_families(inputs, author_family) is None:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=(
                f"complete author family set {sorted(inputs.author_families)} (author_model="
                f"{inputs.author_model!r}) holds an unresolved family — independence cannot be proven"
            ),
        )
    # A complete author set is already concrete; the single-author fallbacks below do not apply.
    quorum_required = author_family == UNATTESTED_AUTHOR_FAMILY and not inputs.author_families
    if quorum_required and inputs.pinned_candidate:
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=(
                "explicit reviewer pin cannot satisfy the dual-family quorum required "
                "for an unattested-harness author — two distinct-family seats must be resolved"
            ),
        )
    if author_family in UNRESOLVED_AUTHOR_FAMILIES and not quorum_required and not inputs.author_families:
        reason = {
            UNKNOWN_AUTHOR_FAMILY: (
                f"author identity unknown — cannot resolve a model family from author_model={inputs.author_model!r}"
            ),
            AMBIGUOUS_AUTHOR_FAMILY: (
                f"author harness is multi-model and ambiguous (author_model={inputs.author_model!r}) — "
                "supply a concrete author model (e.g. 'cursor:claude-opus-5-5') or a validated author_family override"
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
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason=reason,
        )

    if inputs.pinned_candidate and not (inputs.pressure_override_reason or "").strip():
        return ReviewerResolution(
            selected=None,
            advisory=(),
            trace=(),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            fail_closed_reason="explicit reviewer pin requires a non-empty pressure_override_reason",
        )

    trace: list[CandidateResult] = []
    advisory: list[CandidateResult] = []
    selected: CandidateResult | None = None
    selected_rung_index: int | None = None
    # Last-resort candidates follow every eligible primary, after hard gates.
    # A ladder orders fallbacks, not traffic. Candidates in separate YAML
    # rungs with the same semantic suitability and catalog tier form one
    # balancing set, so insertion order cannot pin traffic or promote an idle
    # weaker model over a better task fit.
    # A credit-backed near-cap seat (#9517) ranks after every plan-backed seat
    # of equal standing (same last-resort flag, suitability and tier).
    eligible_by_fit_and_tier: dict[
        tuple[bool, int, int, bool], list[tuple[ReviewerCandidate, CandidateResult, int]]
    ] = {}
    tier_for_candidate = {
        name: _MODEL_CATALOG["quality_tiers"][candidate.quality_tier] for name, candidate in REVIEW_CANDIDATES.items()
    }

    for rung_index, rung in enumerate(active_ladder):
        for candidate in rung:
            result = evaluate_candidate(candidate, inputs, author_family=author_family)
            if result.status == "eligible" and candidate.quota_bucket in excluded_quota_buckets:
                result = replace(
                    result,
                    status="excluded",
                    reason=(f"quota bucket {candidate.quota_bucket!r} is already reserved by an active formal review"),
                )
            if result.status == "eligible":
                result = replace(
                    result,
                    selection_score=selection_key(
                        candidate,
                        snapshot=inputs.routing_snapshot,
                        exact_head=inputs.exact_head,
                        policy_version=_SCHEDULER_POLICY_VERSION,
                    ),
                )
            trace.append(result)
            if result.status == "advisory_only":
                advisory.append(result)
            elif result.status == "eligible":
                fit_key = (
                    candidate.last_resort,
                    result.suitability_rank or 0,
                    tier_for_candidate[candidate.name],
                    result.credit is not None,
                )
                eligible_by_fit_and_tier.setdefault(fit_key, []).append((candidate, result, rung_index))

    if quorum_required:
        first = _best_eligible(eligible_by_fit_and_tier)
        if first is None:
            quorum_failure = (
                "dual-family quorum unsatisfiable: no eligible formal-review candidate for an unattested-harness author"
            )
        else:
            second = _best_eligible(eligible_by_fit_and_tier, exclude_families=frozenset({first[0].family}))
            quorum_failure = (
                (
                    f"dual-family quorum unsatisfiable: only one eligible family ({first[0].family!r}) — "
                    "two distinct attested, formal-review-eligible families are required"
                )
                if second is None
                else None
            )
        if quorum_failure is not None:
            return ReviewerResolution(
                selected=None,
                advisory=tuple(advisory),
                trace=tuple(trace),
                substitution_note=None,
                policy_version=_SCHEDULER_POLICY_VERSION,
                catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
                resolved_risk=risk,
                fail_closed_reason=quorum_failure,
            )
        quorum_results: list[CandidateResult] = []
        for _, seat_result, _ in (first, second):
            promoted = replace(seat_result, status="selected")
            for i, entry in enumerate(trace):
                if entry is seat_result:
                    trace[i] = promoted
                    break
            quorum_results.append(promoted)
        return ReviewerResolution(
            selected=None,
            advisory=tuple(advisory),
            trace=tuple(trace),
            substitution_note=None,
            policy_version=_SCHEDULER_POLICY_VERSION,
            catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
            resolved_risk=risk,
            quorum=tuple(quorum_results),
            quorum_rule=_DUAL_FAMILY_QUORUM_RULE,
        )

    if inputs.pinned_candidate:
        pinned = [
            item
            for entries in eligible_by_fit_and_tier.values()
            for item in entries
            if item[0].name == inputs.pinned_candidate
        ]
        if not pinned:
            return ReviewerResolution(
                selected=None,
                advisory=tuple(advisory),
                trace=tuple(trace),
                substitution_note=None,
                policy_version=_SCHEDULER_POLICY_VERSION,
                catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
                resolved_risk=risk,
                fail_closed_reason=f"explicit reviewer pin {inputs.pinned_candidate!r} failed a hard eligibility gate",
            )
        candidate, best, selected_rung_index = pinned[0]
        selected = best
    elif eligible_by_fit_and_tier:
        candidate, best, selected_rung_index = _best_eligible(eligible_by_fit_and_tier)
        selected = best

    if selected is not None:
        promoted = CandidateResult(
            name=best.name,
            concrete_model=best.concrete_model,
            family=best.family,
            route=best.route,
            transport=best.transport,
            invocation=best.invocation,
            quality_tier=best.quality_tier,
            requires_silence_timeout=best.requires_silence_timeout,
            status="selected",
            reason=None,
            health=best.health,
            suitability_rank=best.suitability_rank,
            selection_score=best.selection_score,
            credit=best.credit,
        )
        for i, entry in enumerate(trace):
            if entry is best:
                trace[i] = promoted
                break
        selected = promoted

    substitution_notes: list[str] = []
    if selected is not None and candidate.last_resort:
        substitution_notes.append(
            f"last resort selected {selected.name}: no eligible primary remained or an explicit pin was requested"
        )
    if selected is not None and selected_rung_index is not None:
        higher_quality_tier_exists = any(
            _suitability_rank(candidate, inputs) == selected.suitability_rank
            and _MODEL_CATALOG["quality_tiers"][candidate.quality_tier]
            < _MODEL_CATALOG["quality_tiers"][selected.quality_tier]
            for rung in active_ladder
            for candidate in rung
        )
        if higher_quality_tier_exists:
            substitution_notes.append(
                f"fell back to {selected.name}: no eligible candidate remained in a higher-quality tier"
            )
        selected_tier = _MODEL_CATALOG["quality_tiers"][selected.quality_tier]
        selected_rung_names = {
            candidate.name
            for rung in active_ladder
            for candidate in rung
            if _MODEL_CATALOG["quality_tiers"][candidate.quality_tier] == selected_tier
        }
        rung_results = [entry for entry in trace if entry.name in selected_rung_names]
        unavailable = [
            entry.name
            for entry in rung_results
            if entry.status == "excluded"
            and entry.reason == "lane health is unhealthy — route is operationally unavailable"
        ]
        if unavailable:
            substitution_notes.append(
                f"selected {selected.name}: same-quality route(s) unavailable by health: {', '.join(unavailable)}"
            )
        if inputs.pinned_candidate:
            substitution_notes.append(
                f"explicit pressure override selected {selected.name}: {inputs.pressure_override_reason.strip()}"
            )
        if selected.credit is not None:
            substitution_notes.append(
                f"selected {selected.name} on lane {selected.route} past its plan cap: {credit_lane.DRAW_NOT_VERIFIED}; "
                f"credit-period allowlist [{', '.join(selected.credit['allowed_models'])}]"
            )

    return ReviewerResolution(
        selected=selected,
        advisory=tuple(advisory),
        trace=tuple(trace),
        substitution_note="; ".join(substitution_notes) or None,
        policy_version=_SCHEDULER_POLICY_VERSION,
        catalog_reviewed_on=_MODEL_CATALOG["reviewed_on"],
        resolved_risk=risk,
        fail_closed_reason=(
            "security-sensitive target: no eligible critical reviewer; see candidate exclusion reasons in trace"
            if selected is None and is_security_sensitive_change(inputs.changed_paths, inputs.owned_paths)
            else None
        ),
    )
