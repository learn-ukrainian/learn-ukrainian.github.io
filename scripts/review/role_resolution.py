"""Shared seat/role resolution with a migration-only v1 consumer projection.

The expansion adapter is migration-only and is removed in #9302 PR 4. Model
identity metadata lives solely in ``models``. Legacy receipt labels are never
identity aliases. Resolution produces data and has no launch/storage authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from shlex import join as shell_join
from shlex import split as shell_split
from typing import Any

from scripts.review.model_catalog import (
    CATALOG_SCHEMA_VERSIONS,
    VALID_CODEX_EFFORTS,
    VALID_RISKS,
    ModelCatalogError,
    canonical_model_id,
    invocation_model,
    load_model_catalog,
    risk_reviewer_refusal,
)

ROUTING_SCHEMA_VERSION = CATALOG_SCHEMA_VERSIONS["routing"]
_STABLE_NAME = re.compile(r"[a-z][a-z0-9_]*\Z")
_SELECTORS = frozenset({"seat", "role", "select_binding", "routes"})
_ROLE_FIELDS = _SELECTORS | {"cardinality", "order_by", "required_model_roles", "risk"}
_ROUTE_FIELDS = frozenset({
    "legacy_name", "effort", "route", "transport", "invocation", "review_profiles", "capabilities",
    "suitability_roles", "transport_fallback_for", "last_resort", "health_keys", "requires_silence_timeout",
    "requires_data_egress_policy", "domain_excluded_from", "advisory_only_for_author_families",
})


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        raise ModelCatalogError(f"{label} must be a non-empty mapping")
    return value


def _strings(value: Any, label: str, *, empty: bool = False) -> list[str]:
    if (not isinstance(value, list) or (not value and not empty)
            or any(not isinstance(item, str) or not item.strip() for item in value)
            or len(set(value)) != len(value)):
        raise ModelCatalogError(f"{label} must be a list of unique non-empty strings")
    return value


def _select_routes(role: str, catalog: dict[str, Any], stack: tuple[str, ...] = ()) -> list[tuple[str, str]]:
    if role in stack:
        raise ModelCatalogError(f"roles contain a cycle: {' -> '.join((*stack, role))}")
    roles = _mapping(catalog.get("roles"), "roles")
    seats = _mapping(catalog.get("seats"), "seats")
    if role not in roles:
        raise ModelCatalogError(f"unknown routing role {role!r}")
    spec = _mapping(roles[role], f"roles.{role}")
    if set(spec) - _ROLE_FIELDS or len(set(spec) & _SELECTORS) != 1:
        raise ModelCatalogError(f"roles.{role} requires exactly one supported selector")
    if "role" in spec:
        if set(spec) != {"role"}:
            raise ModelCatalogError(f"roles.{role} aliases inherit constraints and cannot override them")
        if not isinstance(spec["role"], str) or not spec["role"]:
            raise ModelCatalogError(f"roles.{role}.role must be a routing role name")
        return _select_routes(spec["role"], catalog, (*stack, role))
    if "routes" in spec:
        references = _strings(spec["routes"], f"roles.{role}.routes")
        result = []
        for ref in references:
            parts = ref.split("/")
            if len(parts) != 2 or parts[0] not in seats or parts[1] not in seats[parts[0]]["routes"]:
                raise ModelCatalogError(f"roles.{role} references unknown seat route {ref!r}")
            result.append((parts[0], parts[1]))
        return result
    if "seat" in spec:
        selected = [spec["seat"]]
        if not isinstance(selected[0], str) or selected[0] not in seats:
            raise ModelCatalogError(f"roles.{role} references unknown seat {selected[0]!r}")
    else:
        binding = spec["select_binding"]
        if not isinstance(binding, str) or not binding:
            raise ModelCatalogError(f"roles.{role}.select_binding must be a non-empty string")
        if spec.get("order_by") != "priority":
            raise ModelCatalogError(f"roles.{role}.order_by must be priority")
        selected = sorted(
            (
                name
                for name, seat in seats.items()
                if binding in _strings(seat.get("bindings"), f"seats.{name}.bindings")
            ),
            key=lambda name: (seats[name]["priority"], name),
        )
        if not selected:
            raise ModelCatalogError(f"roles.{role} references an unheld binding {binding!r}")
    return [(seat, route) for seat in selected for route in seats[seat]["routes"]]


def _expanded_route(seat: dict[str, Any], route: dict[str, Any], models: dict[str, Any]) -> dict[str, Any]:
    mapping = models[seat["model_id"]].get("routing_wire_ids", {})
    if route["transport"] not in mapping:
        raise ModelCatalogError("seat route requires its holder's own transport wire mapping")
    wire_id = mapping[route["transport"]]
    result = {key: deepcopy(value) for key, value in route.items() if key not in {"legacy_name", "effort"}}
    result["model_id"] = seat["model_id"]
    try:
        result["invocation"] = route["invocation"].format(wire_id=wire_id)
    except (KeyError, ValueError, IndexError) as exc:
        raise ModelCatalogError("seat invocation may interpolate only {wire_id}") from exc
    return result


def expanded_legacy_view(catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an independent v1 view, expanding receipt labels from stable seats."""
    from scripts.review.model_catalog import validate_catalog

    catalog = validate_catalog(catalog if catalog is not None else load_model_catalog())
    result = deepcopy(catalog)
    if "seats" not in catalog:
        return result
    candidates = {}
    for seat in catalog["seats"].values():
        for route in seat["routes"].values():
            if "legacy_name" in route:
                candidates[route["legacy_name"]] = _expanded_route(seat, route, catalog["models"])
    result["review_candidates"] = candidates
    for model in result["models"].values():
        model.pop("routing_wire_ids", None)
    for key in ("seats", "roles", "routing_schema_version"):
        result.pop(key, None)
    result["schema_version"] = CATALOG_SCHEMA_VERSIONS["legacy"]
    return result


def validate_role_catalog(catalog: dict[str, Any]) -> None:
    """Validate references and eligibility without mutating the legacy catalog."""
    extension = {"seats", "roles", "routing_schema_version"} & catalog.keys()
    if not extension and catalog["schema_version"] == CATALOG_SCHEMA_VERSIONS["legacy"]:
        return
    if catalog.get("routing_schema_version") != ROUTING_SCHEMA_VERSION:
        raise ModelCatalogError(f"routing_schema_version must be {ROUTING_SCHEMA_VERSION}")
    seats = _mapping(catalog.get("seats"), "seats")
    roles = _mapping(catalog.get("roles"), "roles")
    models = catalog["models"]
    for model_id, model in models.items():
        if "routing_wire_ids" not in model:
            continue
        for transport, wire in _mapping(model["routing_wire_ids"], f"models.{model_id}.routing_wire_ids").items():
            if (
                transport not in model["transports"]
                or not isinstance(wire, str)
                or canonical_model_id(wire, catalog) != model_id
            ):
                raise ModelCatalogError(
                    f"models.{model_id}.routing_wire_ids contains an unsupported transport or mismatched identity"
                )
    legacy_names: set[str] = set()
    identities: set[tuple[str, str, str]] = set()
    for name, raw in seats.items():
        if not isinstance(name, str) or not _STABLE_NAME.fullmatch(name):
            raise ModelCatalogError("seat names must be stable functional identifiers")
        seat = _mapping(raw, f"seats.{name}")
        if set(seat) - {"model_id", "bindings", "priority", "routes", "decision_reference", "qualification"}:
            raise ModelCatalogError(f"seats.{name} contains unsupported fields")
        model_id = seat.get("model_id")
        if not isinstance(model_id, str) or model_id not in models:
            raise ModelCatalogError(f"seats.{name} references unknown concrete model")
        model = models[model_id]
        if model["lifecycle"] not in {"active", "fallback"} or not model["transports"] or model["family"] == "deepseek":
            raise ModelCatalogError(f"seats.{name} has a retired or unroutable holder")
        _strings(seat.get("bindings"), f"seats.{name}.bindings")
        if not isinstance(seat.get("priority"), int) or isinstance(seat["priority"], bool) or seat["priority"] < 0:
            raise ModelCatalogError(f"seats.{name}.priority must be a non-negative integer")
        if not isinstance(seat.get("decision_reference"), str) or not seat["decision_reference"].strip():
            raise ModelCatalogError(f"seats.{name} requires a decision_reference; tier grants no authority")
        if "qualification" in seat:
            evidence = _mapping(seat["qualification"], f"seats.{name}.qualification")
            if (
                set(evidence) != {"model_id", "bindings", "reference"}
                or evidence["model_id"] != model_id
                or not isinstance(evidence["reference"], str)
                or not evidence["reference"].strip()
                or not set(_strings(evidence["bindings"], f"seats.{name}.qualification.bindings"))
                >= set(seat["bindings"])
            ):
                raise ModelCatalogError(f"seats.{name} qualification mismatches holder or bindings")
        for route_name, route_raw in _mapping(seat.get("routes"), f"seats.{name}.routes").items():
            if not isinstance(route_name, str) or not _STABLE_NAME.fullmatch(route_name):
                raise ModelCatalogError(f"seats.{name} route names must be stable")
            route = _mapping(route_raw, f"seats.{name}.routes.{route_name}")
            if set(route) - _ROUTE_FIELDS:
                raise ModelCatalogError(f"seats.{name}.{route_name} contains unsupported route fields")
            transport = route.get("transport")
            if not isinstance(transport, str) or transport not in model.get("routing_wire_ids", {}):
                raise ModelCatalogError(f"seats.{name}.{route_name} requires the holder's own transport wire mapping")
            if not isinstance(route.get("effort"), str) or route["effort"] not in VALID_CODEX_EFFORTS:
                raise ModelCatalogError(f"seats.{name}.{route_name} has unsupported effort")
            if not isinstance(route.get("route"), str) or not route["route"].strip():
                raise ModelCatalogError(f"seats.{name}.{route_name}.route must be a non-empty string")
            if not isinstance(route.get("invocation"), str) or not route["invocation"].strip():
                raise ModelCatalogError(f"seats.{name}.{route_name}.invocation must be a template")
            if invocation_model(route["invocation"]) and "{wire_id}" not in route["invocation"]:
                raise ModelCatalogError(f"seats.{name}.{route_name} must interpolate the holder's wire id")
            expanded = _expanded_route(seat, route, models)
            pinned = invocation_model(expanded["invocation"])
            if pinned and canonical_model_id(pinned, catalog) != model_id:
                raise ModelCatalogError(f"seats.{name}.{route_name} invocation mismatches holder")
            identity = (model_id, route["route"], transport)
            if identity in identities:
                raise ModelCatalogError("seats contain duplicate expanded routes")
            identities.add(identity)
            if "legacy_name" in route:
                label = route["legacy_name"]
                if not isinstance(label, str) or label not in catalog["review_candidates"] or label in legacy_names:
                    raise ModelCatalogError("seats contain duplicate or unknown legacy receipt labels")
                legacy_names.add(label)
                # Existing callers may supply an equivalent invocation with a
                # catalog alias, another pin flag or Python -m. The v1 validator
                # already checks that identity. Byte equivalence of committed
                # invocations is enforced by the frozen fixture, not by refusing
                # formerly valid v1 input syntax.
                legacy = catalog["review_candidates"][label]
                if {key: value for key, value in expanded.items() if key != "invocation"} != {
                    key: value for key, value in legacy.items() if key != "invocation"
                }:
                    raise ModelCatalogError(f"seats.{name}.{route_name} changes the legacy candidate {label!r}")
    if legacy_names != set(catalog["review_candidates"]):
        raise ModelCatalogError("seats must cover every legacy review candidate")
    for role, spec in roles.items():
        if not isinstance(role, str) or not _STABLE_NAME.fullmatch(role):
            raise ModelCatalogError("routing role names must be stable functional identifiers")
        selected = _select_routes(role, catalog)
        while "role" in spec:
            spec = roles[spec["role"]]
        holders = {seat for seat, _ in selected}
        cardinality = spec.get("cardinality", "one" if "seat" in spec else "many")
        if not isinstance(cardinality, str) or cardinality not in {"one", "many", "per_family"}:
            raise ModelCatalogError(f"roles.{role} has unsupported cardinality")
        if cardinality == "one" and len(holders) != 1:
            raise ModelCatalogError(f"roles.{role} is an ambiguous singleton")
        families = [models[seats[seat]["model_id"]]["family"] for seat in sorted(holders)]
        if cardinality == "per_family" and len(set(families)) != len(families):
            raise ModelCatalogError(f"roles.{role} must have one holder per independence family")
        requirements = _strings(spec.get("required_model_roles", []), f"roles.{role}.required_model_roles", empty=True)
        risk = spec.get("risk")
        if risk is not None and (not isinstance(risk, str) or risk not in VALID_RISKS):
            raise ModelCatalogError(f"roles.{role} has unsupported risk")
        for seat_name, route_name in selected:
            seat = seats[seat_name]
            model_id = seat["model_id"]
            model = models[model_id]
            if not set(requirements) <= set(model["roles"]):
                raise ModelCatalogError(f"roles.{role} holder lacks required model roles")
            if risk is not None:
                route = seat["routes"][route_name]
                allowed_labels = {label for rung in catalog["review_ladders"][risk] for label in rung}
                if route.get("legacy_name") not in allowed_labels:
                    raise ModelCatalogError(f"roles.{role} introduces a route outside the existing risk ladder")
                from scripts.review.family_exclusions import family_exclusion

                if family_exclusion(family=model["family"], route=route["route"], transport=route["transport"], risk=risk):
                    raise ModelCatalogError(f"roles.{role} violates code-review family exclusions")
                if refusal := risk_reviewer_refusal(model_id, risk, catalog):
                    raise ModelCatalogError(f"roles.{role}: {refusal}")
                floor = catalog["policy"]["risk_quality_floor"][risk]
                if catalog["quality_tiers"][model["tier"]] > catalog["quality_tiers"][floor]:
                    raise ModelCatalogError(f"roles.{role} falls below the risk quality floor")


@dataclass(frozen=True)
class RoleCandidate:
    seat: str
    route_name: str
    model_id: str
    family: str
    route: str
    transport: str
    wire_id: str
    effort: str
    argv: tuple[str, ...]
    legacy_label: str | None
    decision_reference: str
    qualification_reference: str | None
    health: str
    health_rank: int
    health_provenance: dict[str, Any]
    exclusion_reasons: tuple[str, ...]


@dataclass(frozen=True)
class RoleResolution:
    schema_version: str
    role: str
    purpose: str
    catalog_digest: str
    candidates: tuple[RoleCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        """Structured shell output; no YAML parsing or shell eval required."""
        return asdict(self)


def resolve_role(
    role: str,
    *,
    catalog: dict[str, Any] | None = None,
    purpose: str,
    transport: str | None = None,
    family: str | None = None,
    context: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
) -> RoleResolution:
    """Resolve stable roles to concrete pins and evidence, without side effects.

    ``launch`` constructs explicit model argv, never launching it. Health is an
    observation, not a new launch prerequisite; missing/unknown ranks as v1.
    Context permits capability/isolation requirements and seat/family exclusions.
    This envelope does not replace runtime admission or formal-review receipts.
    """
    from scripts.review.model_catalog import validate_catalog

    catalog = validate_catalog(catalog if catalog is not None else load_model_catalog())
    return _resolve_role(
        role, catalog=catalog, purpose=purpose, transport=transport, family=family, context=context, health=health
    )


def _resolve_role(
    role: str,
    *,
    catalog: dict[str, Any],
    purpose: str,
    transport: str | None = None,
    family: str | None = None,
    context: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
) -> RoleResolution:
    """The shared resolver implementation, also used while validating authored references.

    The catalog validator validates the resolved view immediately afterwards.
    This private entry avoids recursively loading/validating the same catalog.
    It has no launch authority and never imports a partially initialized reviewer.
    """

    if not isinstance(purpose, str) or purpose not in {"inspect", "launch"}:
        raise ModelCatalogError("purpose must be inspect or launch")
    if "roles" not in catalog:
        raise ModelCatalogError("catalog has no routing roles")
    if not isinstance(role, str):
        raise ModelCatalogError("role must be a stable routing role name")
    context = {} if context is None else context
    if not isinstance(context, dict) or set(context) - {
        "required_capabilities",
        "isolation_required",
        "excluded_seats",
        "excluded_families",
        "pinned_model",
        "data_egress_policy",
    }:
        raise ModelCatalogError("unsupported role context")
    for key in ("required_capabilities", "excluded_seats", "excluded_families"):
        if key in context:
            _strings(context[key], f"context.{key}", empty=True)
    if "isolation_required" in context and not isinstance(context["isolation_required"], bool):
        raise ModelCatalogError("context.isolation_required must be boolean")
    if "data_egress_policy" in context and not isinstance(context["data_egress_policy"], str):
        raise ModelCatalogError("context.data_egress_policy must be a string")
    pinned = context.get("pinned_model")
    if pinned is not None and canonical_model_id(pinned, catalog) is None:
        raise ModelCatalogError("context.pinned_model must name a concrete catalog identity")
    if health is None:
        normalized = {}
    else:
        from scripts.review.reviewer_resolver import normalize_routing_snapshot

        normalized = normalize_routing_snapshot(health)
    spec = catalog["roles"].get(role, {})
    while "role" in spec:
        spec = catalog["roles"][spec["role"]]
    candidates = []
    for seat_name, route_name in _select_routes(role, catalog):
        seat = catalog["seats"][seat_name]
        route = seat["routes"][route_name]
        model_id = seat["model_id"]
        model = catalog["models"][model_id]
        exclusions = []
        if transport is not None and transport != route["transport"]:
            exclusions.append("transport_mismatch")
        if family is not None and family != model["family"]:
            exclusions.append("family_mismatch")
        if seat_name in context.get("excluded_seats", []):
            exclusions.append("subject_seat_excluded")
        if model["family"] in context.get("excluded_families", []):
            exclusions.append("subject_family_excluded")
        if not set(context.get("required_capabilities", [])) <= set(route.get("capabilities", [])):
            exclusions.append("required_capability_missing")
        if context.get("isolation_required") and "isolation" not in route.get("capabilities", []):
            exclusions.append("isolation_required")
        if pinned is not None and canonical_model_id(pinned, catalog) != model_id:
            exclusions.append("explicit_pin_mismatch")
        if (
            route.get("requires_data_egress_policy")
            and context.get("data_egress_policy") != route["requires_data_egress_policy"]
        ):
            exclusions.append("data_egress_policy_required")
        if "risk" in spec:
            # Catalog evidence only: use the supplied snapshot, not a module's
            # independently loaded global catalog. Author attestation and the
            # full runtime/reviewer gates remain the caller's responsibility.
            scheduler = catalog["review_scheduler"]
            endpoint = scheduler["endpoints"].get(route["route"], {})
            if not endpoint.get("formal_review_eligible") or model_id not in endpoint.get("models", []):
                exclusions.append("formal_endpoint_not_eligible")
            suitability = route.get("suitability_roles") or model["roles"]
            required_roles = scheduler["profile_risk_role_order"]["code"][spec["risk"]]
            if not set(suitability) & set(required_roles):
                exclusions.append("review_role_suitability_missing")
        keys = [
            route.get("legacy_name"),
            route["route"],
            model_id,
            model["family"],
            *sorted(route.get("health_keys", [])),
        ]
        health_key = next((key for key in keys if key in normalized), None)
        observed = normalized.get(health_key)
        wire_id = model["routing_wire_ids"][route["transport"]]
        argv = shell_split(_expanded_route(seat, route, catalog["models"])["invocation"])
        if purpose == "launch" and invocation_model(shell_join(argv)) is None:
            argv.extend(["--model", wire_id])
        qualification = seat.get("qualification", {})
        candidates.append(
            RoleCandidate(
                seat=seat_name,
                route_name=route_name,
                model_id=model_id,
                family=model["family"],
                route=route["route"],
                transport=route["transport"],
                wire_id=wire_id,
                effort=route["effort"],
                argv=tuple(argv),
                legacy_label=route.get("legacy_name"),
                decision_reference=seat["decision_reference"],
                qualification_reference=qualification.get("reference"),
                health=observed or "unknown",
                health_rank=_role_health_rank(observed),
                health_provenance={
                    "snapshot_supplied": health is not None,
                    "normalized_key": health_key,
                    "diagnostic": "HEALTH_UNKNOWN" if observed is None else None,
                },
                exclusion_reasons=tuple(exclusions),
            )
        )
    digest = hashlib.sha256(
        json.dumps(catalog, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return RoleResolution("role-resolution.v1", role, purpose, digest, tuple(candidates))


def _role_health_rank(observed: str | None) -> int:
    if observed is None:
        return 0  # Existing fail-open rank; avoids reviewer import during catalog bootstrap.
    from scripts.review.reviewer_resolver import _health_rank

    return _health_rank(observed)


def resolve_routing_reference(reference: dict[str, Any], catalog: dict[str, Any]) -> Any:
    """Resolve an authored catalog reference with the shared role implementation.

    Seat/route filters distinguish alternate transports without creating moving
    identity aliases. Concrete explicit pins never enter this path.
    """
    if set(reference) - {"role", "seat", "route_name", "transport", "field"}:
        raise ModelCatalogError("routing reference contains unsupported fields")
    role = reference.get("role")
    result = _resolve_role(role, catalog=catalog, purpose="inspect", transport=reference.get("transport"))
    candidates = [
        c
        for c in result.candidates
        if ("seat" not in reference or c.seat == reference["seat"])
        and ("route_name" not in reference or c.route_name == reference["route_name"])
        and ("transport" not in reference or c.transport == reference["transport"])
    ]
    field = reference.get("field", "model_id")
    if field not in {"model_id", "wire_id", "legacy_label", "candidate"}:
        raise ModelCatalogError("routing reference has unsupported result field")
    if field == "candidate":
        if len(candidates) != 1:
            raise ModelCatalogError("candidate reference must resolve to exactly one seat route")
        c = candidates[0]
        return _expanded_route(
            catalog["seats"][c.seat], catalog["seats"][c.seat]["routes"][c.route_name], catalog["models"]
        )
    values = {getattr(c, field) for c in candidates}
    if len(values) != 1 or None in values:
        raise ModelCatalogError(f"routing reference must resolve to exactly one {field}")
    return next(iter(values))


def expand_routing_references(catalog: dict[str, Any]) -> dict[str, Any]:
    """Build the validated v1 consumer view from role references until PR 4.

    Only routing sections are expanded. Models, seats, role definitions, explicit
    source-pin keys and historical provenance remain authored identity metadata.
    Existing concrete v1 fixtures are accepted without rewriting or weakening gates.
    """
    sections = (
        "execution_routing",
        "review_candidates",
        "review_ladders",
        "review_scheduler",
        "orchestrator_seats",
        "formal_cf_defaults",
        "budget_substitution_models",
    )

    def expand(value):
        if isinstance(value, dict):
            if "role" in value and set(value) <= {"role", "seat", "route_name", "transport", "field"}:
                return resolve_routing_reference(value, catalog)
            return {key: expand(item) for key, item in value.items()}
        if isinstance(value, list):
            return [expand(item) for item in value]
        return value

    # Preserve references while resolving every section against one snapshot.
    result = catalog.copy()
    try:
        for section in sections:
            if section in catalog:
                result[section] = expand(catalog[section])
    except (KeyError, TypeError, AttributeError) as exc:
        raise ModelCatalogError(f"invalid routing reference: {exc}") from exc
    return result
