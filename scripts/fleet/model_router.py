"""Pure subscription selector for #10154; never an execution authorization.

Public API: select_route(request, *, trusted_facts, catalog, snapshot, policy,
now). Request/decision use the closed schemas in schemas/. All other mappings
are admission/collector-owned, never accepted from a driver's request.

Trusted target facts (TARGET_SCHEMA) include the complete changed/renamed/deleted
paths, historical and incoming author families, subject scope, and the routes
that the existing admission collector qualified for this exact target/prompt.
An admitted_routes entry is a seat/route_name pair from that collector, not an
operator override. This module intersects it with resolve_role and, for code/
infra review, the existing pure reviewer hard gates. Sinks must re-collect and
re-admit everything before effects; neither this input nor a decision receipt
is a capability. Missing facts refuse. No filesystem, quota, provider, spend,
reset, reservation or delivery operations occur in select_route.

Snapshot: agents.<lane> is the existing routing-budget record; applicability
is a list of credit_lane.SubscriptionFacts declarations under
subscription_applicability. Unsupported producers remain unknown. Policy is
the private loader's validated router-policy.v1 mapping (closed below). Source
pins are component compatibility bounds, not global provider-health facts.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from jsonschema import Draft202012Validator

from scripts.fleet import credit_lane
from scripts.review import reviewer_resolver as reviewers
from scripts.review.model_catalog import ModelCatalogError, activity_role_refusal, validate_catalog
from scripts.review.role_resolution import resolve_role
from scripts.review.security_paths import effective_review_risk
from scripts.review.subject_seat import prepare_subject_exclusion, subject_exclusion_reason

DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$", "minLength": 64, "maxLength": 64}
STRINGS = {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True}
NAME = {
    "type": "string",
    "pattern": "^[a-zA-Z0-9][a-zA-Z0-9_./:-]{0,127}$",
    "not": {"pattern": "[\\s\\u0000-\\u001f\\u007f]"},
}
REFUSAL_CODES = (
    "CLOCK_INVALID",
    "REQUEST_INVALID",
    "TARGET_FACTS_MISSING",
    "POLICY_INVALID",
    "CATALOG_RESOLVER_MISMATCH",
    "INPUT_INVALID",
    "TARGET_BINDING_MISMATCH",
    "DATA_EGRESS_REFUSED",
    "AUTHOR_IDENTITY_UNRESOLVED",
    "AUTHOR_IDENTITY_CONFLICT",
    "REVIEW_PROFILE_UNSUPPORTED",
    "SUBJECT_SCOPE_AMBIGUOUS",
    "ROLE_UNSUPPORTED",
    "SNAPSHOT_INVALID",
    "CAPACITY_UNKNOWN",
    "NO_ELIGIBLE_ROUTE",
)
DECISION_RULES = ("CATALOG_HARD_GATES", "SUBSCRIPTION_ONLY", "LEXICOGRAPHIC_SELECTION")
TIMESTAMP = {
    "type": "string",
    "format": "date-time",
    "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\\.[0-9]+)?Z$",
    "not": {"pattern": "[\\s]"},
}


def _closed(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties) if required is None else required,
    }


REQUEST_SCHEMA = _closed(
    {
        "schema_version": {"const": "model-router-request.v1"},
        "role": NAME,
        "purpose": {"enum": ["inspect", "launch"]},
        "task_id": NAME,
        "prompt_sha256": DIGEST,
        "restrictions": _closed(
            {
                "required_capabilities": STRINGS,
                "excluded_seats": STRINGS,
                "excluded_families": STRINGS,
                "isolation_required": {"type": "boolean"},
                "model": NAME,
                "transport": NAME,
                "risk": {"enum": ["low", "medium", "high", "critical"]},
            },
            [],
        ),
    }
)
TARGET_SCHEMA = _closed(
    {
        "schema_version": {"const": "router-target.v1"},
        "role": NAME,
        "purpose": {"enum": ["inspect", "launch"]},
        "task_id": NAME,
        "prompt_sha256": DIGEST,
        "target_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$", "minLength": 40, "maxLength": 40},
        "activity": {"enum": ["dispatch", "review", "consult"]},
        "risk": {"enum": ["low", "medium", "high", "critical"]},
        "review_profile": {"enum": ["code", "infra", "ukrainian", "none"]},
        "domain": NAME,
        "data_classification": {"enum": ["public", "private", "local_only", "secret"]},
        "data_egress_policy": {"type": ["string", "null"]},
        "required_capabilities": STRINGS,
        "isolation_required": {"type": "boolean"},
        "author_model": {"type": ["string", "null"]},
        "author_family": {"type": ["string", "null"]},
        "author_families": STRINGS,
        "subject_seats": STRINGS,
        "subject_families": STRINGS,
        "changed_paths": STRINGS,
        "admitted_routes": {"type": "array", "uniqueItems": True, "items": _closed({"seat": NAME, "route_name": NAME})},
    }
)
POLICY_SCHEMA = _closed(
    {
        "schema_version": {"const": "router-policy.v1"},
        "policy_epoch": NAME,
        "manual_spend_authorization": _closed({"enabled": {"type": "boolean"}}),
        "campaigns": {
            "type": "array",
            "items": _closed(
                {
                    "id": NAME,
                    "models": STRINGS,
                    "lanes": STRINGS,
                    "starts_at": {"type": "string"},
                    "expires_at": {"type": "string"},
                }
            ),
        },
        "window_metadata": _closed({"producer_digest": DIGEST, "catalog_digest": DIGEST}, []),
    }
)
DECISION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        _closed(
            {
                "schema_version": {"const": "model-router-decision.v1"},
                "status": {"const": "refused"},
                "rule_ids": {
                    "type": "array",
                    "items": {"enum": list(REFUSAL_CODES)},
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "code": {"enum": list(REFUSAL_CODES)},
            }
        ),
        _closed(
            {
                "schema_version": {"const": "model-router-decision.v1"},
                "status": {"const": "selected"},
                "rule_ids": {
                    "type": "array",
                    "items": {"enum": list(DECISION_RULES)},
                    "minItems": 1,
                    "uniqueItems": True,
                },
                "task_id": NAME,
                "role": NAME,
                "purpose": {"enum": ["inspect", "launch"]},
                "model": NAME,
                "family": NAME,
                "lane": NAME,
                "harness": NAME,
                "transport": NAME,
                "effort": {"const": "high"},
                "target_sha": TARGET_SCHEMA["properties"]["target_sha"],
                "prompt_sha256": DIGEST,
                "catalog_sha256": DIGEST,
                "policy_sha256": DIGEST,
                "snapshot_sha256": DIGEST,
                "trusted_facts_sha256": DIGEST,
                "observed_at": TIMESTAMP,
                "expires_at": TIMESTAMP,
            }
        ),
    ],
}
REQUEST_SCHEMA["$schema"] = DECISION_SCHEMA["$schema"]
_VALIDATORS = {
    "request": Draft202012Validator(REQUEST_SCHEMA),
    "target": Draft202012Validator(TARGET_SCHEMA),
    "policy": Draft202012Validator(POLICY_SCHEMA),
}
_RISKS = ["low", "medium", "high", "critical"]
_HARNESSES = {
    "native_codex": "codex",
    "native_claude": "claude-code",
    "native_grok": "grok",
    "native_kimi": "kimi",
    "agy": "agy",
    "cursor": "cursor",
}


def canonical_digest(value: Any, *, capacity_snapshot: bool = False) -> str:
    """Hash mappings without repr fallback.

    Capacity fingerprints retain deterministic NaN/Infinity tokens for invalid
    readings so one bad candidate cannot poison a healthy alternative. Those
    tokens never qualify as allowance or enter the public decision. All other
    inputs require finite JSON numbers.
    """
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=capacity_snapshot).encode()
    return hashlib.sha256(encoded).hexdigest()


def _refuse(code: str) -> dict[str, Any]:
    return {"schema_version": "model-router-decision.v1", "status": "refused", "rule_ids": [code], "code": code}


def _campaigns(
    policy: Mapping[str, Any],
    now: datetime,
    *,
    catalog: Mapping[str, Any],
) -> dict[tuple[str, str], datetime]:
    """Validate all campaigns, including inactive ones, before ranking any route."""
    active: dict[tuple[str, str], datetime] = {}
    seen = set()
    qualified = {
        (seat["model_id"], route["route"])
        for seat in catalog["seats"].values()
        for route in seat["routes"].values()
        if route["transport"] in _HARNESSES
    }
    for campaign in policy["campaigns"]:
        start = credit_lane.subscription_timestamp(campaign["starts_at"])
        end = credit_lane.subscription_timestamp(campaign["expires_at"])
        if start is None or end is None or start >= end or campaign["id"] in seen:
            raise ValueError("campaign_invalid")
        if not campaign["models"] or not campaign["lanes"]:
            raise ValueError("campaign_scope_missing")
        if any((model, lane) not in qualified for model in campaign["models"] for lane in campaign["lanes"]):
            raise ValueError("campaign_scope_unqualified")
        seen.add(campaign["id"])
        if start <= now < end:
            for model in campaign["models"]:
                for lane in campaign["lanes"]:
                    key = model, lane
                    active[key] = min(active.get(key, end), end)
    return active


def _review_gate(candidate: Any, target: Mapping[str, Any], context: dict[str, Any], risk: str) -> int | None:
    """Reuse the resolver's side-effect-free filters, never its quota/file probes.

    Its installed catalog is digest-checked by select_route before these helpers
    are used. No global monkeypatch, rival family policy or injected ladder.
    Existing collector admission still supplies the execution-dependent gates.
    """
    if candidate.legacy_label not in reviewers.REVIEW_CANDIDATES:
        return None
    reviewer = reviewers.REVIEW_CANDIDATES[candidate.legacy_label]
    inputs = reviewers.ResolverInputs(
        author_model=target["author_model"] or "",
        author_family=target["author_family"],
        author_families=frozenset(target["author_families"]),
        risk=risk,
        review_profile=target["review_profile"],
        domain=target["domain"],
        changed_paths=tuple(target["changed_paths"]),
        required_capabilities=frozenset(context["required_capabilities"]),
        isolation_required=context["isolation_required"],
        data_egress_policy=target["data_egress_policy"],
    )
    if reviewers._hard_exclusion_reason(reviewer, inputs):
        return None
    if reviewers.risk_reviewer_refusal(candidate.model_id, risk, reviewers._MODEL_CATALOG):
        return None
    if reviewers._retired_alias_target(reviewer):
        return None
    if reviewers.is_ukrainian_content_change(inputs) and candidate.family not in reviewers._UKRAINIAN_CONTENT_FAMILIES:
        return None
    for family in target["author_families"]:
        if reviewers._author_family_exclusion(reviewer, family, None):
            return None
    subject_families = set(target["subject_families"])
    if "cursor" in target["subject_seats"]:
        subject_families.add("xai")
    if subject_exclusion_reason(
        reviewer,
        seats=frozenset(target["subject_seats"]),
        families=frozenset(subject_families),
    ):
        return None
    return reviewers._suitability_rank(reviewer, inputs)


def _candidate_key(
    candidate: Any,
    *,
    catalog: Mapping[str, Any],
    suitability: int,
    facts: credit_lane.SubscriptionFacts,
    campaign: datetime | None,
) -> tuple[Any, ...]:
    """Catalog hard-fit prefix, campaign/resource layer, lexical final tie."""
    route = catalog["seats"][candidate.seat]["routes"][candidate.route_name]
    model = catalog["models"][candidate.model_id]
    return (
        bool(route.get("last_resort", False)),
        suitability,
        catalog["quality_tiers"][model["tier"]],
        campaign is None,
        campaign or datetime.max.replace(tzinfo=UTC),
        -facts.limiting_pace,
        -facts.remaining_pct,
        candidate.route,
        candidate.model_id,
        _HARNESSES[candidate.transport],
        candidate.seat,
        candidate.route_name,
    )


def select_route(
    request: Mapping[str, Any],
    *,
    trusted_facts: Mapping[str, Any],
    catalog: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    policy: Mapping[str, Any],
    now: datetime,
) -> dict[str, Any]:
    """Return a closed selected/refused mapping with no external effects.

    Every error code is allowlisted here, never exception text or private data.
    Caller restrictions union with trusted restrictions; they cannot overwrite
    role, risk, target, author, subject, data, tool or isolation facts. Invalid
    evidence on one candidate never poisons another qualified fresh candidate.
    Inventory is included in the snapshot fingerprint but never ranked/read as
    allowance. Manual spend authorization has no effect on automatic selection.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        return _refuse("CLOCK_INVALID")
    try:
        for label, payload in (("request", request), ("target", trusted_facts), ("policy", policy)):
            if not isinstance(payload, dict) or not _VALIDATORS[label].is_valid(payload):
                return _refuse(
                    {"request": "REQUEST_INVALID", "target": "TARGET_FACTS_MISSING", "policy": "POLICY_INVALID"}[label]
                )
        validate_catalog(catalog)
        catalog_digest = canonical_digest(catalog)
        # Existing reviewer helpers have catalog globals. Refuse drift rather
        # than silently evaluating a different catalog or mutating those globals.
        if catalog_digest != canonical_digest(reviewers._MODEL_CATALOG):
            return _refuse("CATALOG_RESOLVER_MISMATCH")
        snapshot_digest = canonical_digest(snapshot, capacity_snapshot=True)
        policy_digest = canonical_digest(policy)
        campaigns = _campaigns(policy, now, catalog=catalog)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return _refuse("INPUT_INVALID")
    if any(request[key] != trusted_facts[key] for key in ("task_id", "prompt_sha256", "role", "purpose")):
        return _refuse("TARGET_BINDING_MISMATCH")
    target = dict(trusted_facts)
    restrictions = request["restrictions"]
    # This pure component cannot qualify secret or local-only external egress.
    if target["data_classification"] in {"secret", "local_only"}:
        return _refuse("DATA_EGRESS_REFUSED")
    authors = set(target["author_families"])
    if target["activity"] == "review":
        if not authors or not authors <= reviewers._VALID_CONCRETE_FAMILIES:
            return _refuse("AUTHOR_IDENTITY_UNRESOLVED")
        family = reviewers.resolve_author_family(target["author_model"], target["author_family"])
        if family not in authors:
            return _refuse("AUTHOR_IDENTITY_CONFLICT")
        if target["review_profile"] not in {"code", "infra"}:
            return _refuse("REVIEW_PROFILE_UNSUPPORTED")
    subjects = prepare_subject_exclusion(
        subject_seats=frozenset(target["subject_seats"]),
        subject_families=frozenset(target["subject_families"]),
        owned_paths=tuple(target["changed_paths"]),
    )
    if subjects.fail_closed_reason:
        return _refuse("SUBJECT_SCOPE_AMBIGUOUS")
    target["subject_seats"] = sorted(subjects.seats)
    target["subject_families"] = sorted(subjects.families)
    risk = max(target["risk"], restrictions.get("risk", target["risk"]), key=_RISKS.index)
    risk = effective_review_risk(risk, target["changed_paths"], profile=target["review_profile"])
    context = {
        "required_capabilities": sorted(
            set(target["required_capabilities"]) | set(restrictions.get("required_capabilities", []))
        ),
        "excluded_seats": restrictions.get("excluded_seats", []),
        "excluded_families": sorted(
            set(restrictions.get("excluded_families", [])) | (authors if target["activity"] == "review" else set())
        ),
        "isolation_required": target["isolation_required"] or restrictions.get("isolation_required", False),
    }
    if target["data_egress_policy"] is not None:
        context["data_egress_policy"] = target["data_egress_policy"]
    if "model" in restrictions:
        context["pinned_model"] = restrictions["model"]
    try:
        resolution = resolve_role(
            request["role"],
            catalog=catalog,
            purpose=request["purpose"],
            transport=restrictions.get("transport"),
            context=context,
        )
    except ModelCatalogError:
        return _refuse("ROLE_UNSUPPORTED")
    if (
        not isinstance(snapshot, dict)
        or set(snapshot)
        - {
            "agents",
            "diagnostics",
            "subscription_applicability",
            "api_accounts",
            "recommendation",
        }
        or not isinstance(snapshot.get("agents"), dict)
        or not isinstance(snapshot.get("subscription_applicability"), list)
    ):
        return _refuse("SNAPSHOT_INVALID")
    admitted = {(r["seat"], r["route_name"]) for r in target["admitted_routes"]}
    eligible = []
    unknown = False
    for candidate in resolution.candidates:
        if candidate.exclusion_reasons or (candidate.seat, candidate.route_name) not in admitted:
            continue
        if candidate.transport not in _HARNESSES or candidate.effort != "high":
            continue
        if target["activity"] == "consult" and activity_role_refusal(candidate.model_id, "consult", catalog):
            continue
        suitability = 0
        if target["activity"] == "review":
            suitability = _review_gate(candidate, target, context, risk)
            if suitability is None:
                continue
        model = catalog["models"][candidate.model_id]
        floor = catalog["policy"]["risk_quality_floor"][risk]
        if catalog["quality_tiers"][model["tier"]] > catalog["quality_tiers"][floor]:
            continue
        record = snapshot["agents"].get(candidate.route)
        if not isinstance(record, dict):
            unknown = True
            continue
        runtime = record.get("runtime", {})
        scheduler = record.get("scheduler", {})
        if not isinstance(runtime, dict) or not isinstance(scheduler, dict):
            unknown = True
            continue
        health, _ = credit_lane.health_fact(record)
        if health != credit_lane.HEALTHY:
            unknown |= health == credit_lane.UNKNOWN
            continue
        try:
            qualified_health = reviewers.normalize_routing_snapshot({"agents": {candidate.route: record}}).get(
                candidate.route
            )
        except ValueError:
            unknown = True
            continue
        if qualified_health in {None, "unhealthy", "degraded_telemetry"}:
            unknown = True
            continue
        if record.get("status") == "near_cap":
            continue
        if (
            record.get("eligible") is False
            or credit_lane._need_login(record)
            or record.get("circuit_open")
            or runtime.get("headroom_blocked")
            or runtime.get("circuit_open")
            or runtime.get("rate_limited")
            or scheduler.get("capacity_exhausted")
            or scheduler.get("circuit_open")
        ):
            continue
        declarations = [
            entry
            for entry in snapshot["subscription_applicability"]
            if isinstance(entry, dict)
            and (entry.get("lane"), entry.get("model"), entry.get("transport"))
            == (candidate.route, candidate.model_id, candidate.transport)
        ]
        if len(declarations) != 1:
            unknown = True
            continue
        facts = credit_lane.routing_facts(
            candidate.route,
            record,
            model=candidate.model_id,
            transport=candidate.transport,
            applicability=declarations[0],
            snapshot_metadata=snapshot.get("diagnostics"),
            now=now,
            subscription_only=True,
        )
        if facts.capacity != credit_lane.CAPACITY_VERIFIED:
            unknown |= facts.capacity in {credit_lane.CAPACITY_UNKNOWN, credit_lane.CAPACITY_UNKNOWN_STALE}
            continue
        if facts.remaining_pct <= credit_lane._NEAR_CAP_REMAINING_PCT:
            continue
        # Pace slack ranks capacity; it never invents a new admission threshold.
        # The existing writer hot-status gate binds. Reviews retain pace debt
        # for ordering only, while non-pace hot labels remain hard restrictions.
        if record.get("status") == "hot" and (
            target["activity"] != "review" or record.get("status_source") != "weekly_pace"
        ):
            continue
        campaign = campaigns.get((candidate.model_id, candidate.route))
        key = _candidate_key(candidate, catalog=catalog, suitability=suitability, facts=facts, campaign=campaign)
        eligible.append((key, candidate, facts, campaign))
    if not eligible:
        return _refuse("CAPACITY_UNKNOWN" if unknown else "NO_ELIGIBLE_ROUTE")
    # Reuse the catalog resolver's ordered fit groups and same-model native-
    # before-fallback rule. Only its resource score is the subscription score.
    groups: dict[tuple[bool, int, int, bool], list[Any]] = {}
    for index, (key, candidate, _, _) in enumerate(eligible):
        route = catalog["seats"][candidate.seat]["routes"][candidate.route_name]
        identity = SimpleNamespace(
            name=candidate.legacy_label or f"{candidate.seat}/{candidate.route_name}",
            family=candidate.family,
            transport_fallback_for=route.get("transport_fallback_for"),
        )
        groups.setdefault((*key[:3], False), []).append((identity, SimpleNamespace(selection_score=key[3:]), index))
    best = reviewers._best_eligible(groups)
    _, selected, facts, campaign = eligible[best[2]]
    expiry = credit_lane.subscription_timestamp(facts.expires_at)
    if campaign is not None:
        expiry = min(expiry, campaign)
    return {
        "schema_version": "model-router-decision.v1",
        "status": "selected",
        "rule_ids": ["CATALOG_HARD_GATES", "SUBSCRIPTION_ONLY", "LEXICOGRAPHIC_SELECTION"],
        "task_id": request["task_id"],
        "role": request["role"],
        "purpose": request["purpose"],
        "model": selected.model_id,
        "family": selected.family,
        "lane": selected.route,
        "harness": _HARNESSES[selected.transport],
        "transport": selected.transport,
        "effort": selected.effort,
        "target_sha": target["target_sha"],
        "prompt_sha256": request["prompt_sha256"],
        "catalog_sha256": catalog_digest,
        "policy_sha256": policy_digest,
        "snapshot_sha256": snapshot_digest,
        "trusted_facts_sha256": canonical_digest(trusted_facts),
        "observed_at": facts.observed_at,
        "expires_at": expiry.isoformat().replace("+00:00", "Z"),
    }
