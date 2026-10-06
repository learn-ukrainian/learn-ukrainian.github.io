"""Load and structurally validate the canonical fleet model catalog."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from shlex import split as shell_split
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from scripts.review.role_resolution import RoleResolution

CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "model_catalog.yaml"
PROJECT_ROOT = CATALOG_PATH.parents[2]
EXPECTED_SCHEMA_VERSION = "model-catalog.v1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({EXPECTED_SCHEMA_VERSION, "model-catalog.v1.1"})
VALID_LIFECYCLES = frozenset({"active", "fallback", "hold", "retired"})
VALID_RISKS = frozenset({"low", "medium", "high", "critical"})
VALID_REVIEW_PROFILES = frozenset({"code", "infra"})
# ``review_scheduler.activity_roles`` keys (#9583): ``review`` admits a review,
# critique or approval of record; ``consult`` admits an ACP ask, consult or
# discussion together with the ``review`` roles.
REVIEW_ACTIVITY = "review"
CONSULT_ACTIVITY = "consult"
ACTIVITIES = frozenset({REVIEW_ACTIVITY, CONSULT_ACTIVITY})
EXPECTED_SELECTION_ORDER = [
    "independence_and_hard_gates",
    "primary_before_last_resort",
    "profile_risk_suitability",
    "review_quality_tier",
    "health_and_quota_within_tier",
    "cost_within_equivalent_fit",
]
KIMI_ROUTE_FIELDS = (
    "kimicc_alias",
    "platform_model_id",
    "coding_model_id",
    "context_profile",
)
GLM_ROUTE_FIELDS = (
    "glmcc_alias",
    "platform_model_id",
    "coding_model_id",
    "context_profile",
)
VALID_CODEX_EFFORTS = frozenset({"low", "medium", "high", "xhigh", "max"})
EXECUTION_ROUTE_KEYS = frozenset(
    {"advisor", "preferred_worker", "bounded_fallback_worker", "autonomous_fallback", "review_boundary"}
)
ADVISOR_KEYS = frozenset({"model_id", "effort", "role", "output_fields"})
PREFERRED_WORKER_KEYS = frozenset(
    {"model_id", "effort", "requires", "task_types", "escalate_to", "prohibited_decisions", "escalation_triggers"}
)
BOUNDED_FALLBACK_WORKER_KEYS = frozenset({"model_id", "effort", "requires", "non_bounded_task_families"})
BOUNDED_WORKER_REQUIRES = frozenset({"complete_advisory_envelope", "objective_scope_ceiling"})
FALLBACK_KEYS = frozenset({"model_id", "effort", "when"})
REVIEW_BOUNDARY_KEYS = frozenset(
    {"advisory_family", "advisory_satisfies_cross_family_review", "independent_cross_family_review_required"}
)
ADVISOR_OUTPUT_FIELDS = [
    "task_contract",
    "owned_paths",
    "max_changed_files",
    "max_non_test_loc",
    "constraints",
    "risk_boundaries",
    "acceptance_evidence",
    "escalation_triggers",
]
LUNA_TASK_TYPES = frozenset({"bounded_implementation", "bounded_investigation"})
LUNA_PROHIBITED_DECISIONS = frozenset(
    {"consequential_architecture", "security", "release", "high_risk_go_no_go"}
)
LUNA_ESCALATION_TRIGGERS = frozenset(
    {
        "scope_ceiling_exceeded",
        "unresolved_consequential_ambiguity",
        "broader_integration",
        "final_disposition",
    }
)
CURSOR_AUTO_EXPECTED_ALLOWLIST: tuple[str, ...] = ("grok-4.7", "composer-2.5")
CURSOR_AUTO_EXPECTED_ATTESTATION_RULE: str = "driver_of_record_requires_attested_resolved_model"
CURSOR_AUTO_EXPECTED_RESOLUTION: str = "union_family"
# Operator decision 2026-09-30 (#9274): Cursor Auto runs only a well-defined coding
# task; every other Cursor use runs the seat's concrete pin or another allowlisted pin.
CURSOR_AUTO_EXPECTED_SCOPE: str = "write_implementation_dispatch_with_green_dor"
# Values that ask Cursor to choose the model instead of naming one.
_CURSOR_SELECTOR_MODELS = frozenset({"auto", "default"})
# Typed refusal reasons for Cursor model selection.
CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE = "cursor_auto_outside_coding_task"
CURSOR_MODEL_UNPINNED_CODE = "cursor_model_unpinned"
CURSOR_MODEL_NOT_APPROVED_CODE = "cursor_model_not_approved"
# Families never pinned as formal reviewers on the Cursor endpoint (#9488):
# Composer shares the Kimi lineage (never a reviewer), Gemini never reviews
# code, DeepSeek is excluded, and the decision admits non-Anthropic models only.
CURSOR_FORMAL_REVIEW_EXCLUDED_FAMILIES = frozenset({"moonshot", "google", "deepseek", "anthropic"})



class ModelCatalogError(ValueError):
    """The model catalog is missing or violates its structural contract."""


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelCatalogError(f"{label} must be a mapping")
    return value


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelCatalogError(f"{label} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if (
        not isinstance(value, list)
        or (not value and not allow_empty)
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        qualifier = "a list" if allow_empty else "a non-empty list"
        raise ModelCatalogError(f"{label} must be {qualifier} of strings")
    return [item.strip() for item in value]


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], label: str) -> None:
    if set(value) != expected:
        raise ModelCatalogError(f"{label} must define exactly {sorted(expected)}")


def _require_active_execution_model(models: dict[str, Any], value: Any, label: str) -> str:
    model_id = _require_string(value, label)
    if model_id not in models:
        raise ModelCatalogError(f"{label} references unknown model {model_id!r}")
    if models[model_id]["lifecycle"] != "active":
        raise ModelCatalogError(f"{label} must reference an active model")
    _require_routable_model(models, model_id, label)
    return model_id


def _require_routable_model(models: dict[str, Any], value: Any, label: str) -> str:
    """Validate an executable reference while preserving historical model records."""
    model_id = _require_string(value, label)
    if model_id not in models:
        raise ModelCatalogError(f"{label} references unknown model {model_id!r}")
    model = models[model_id]
    if model["lifecycle"] == "retired":
        raise ModelCatalogError(f"{label} references retired model {model_id!r}")
    if model["family"] == "deepseek":
        raise ModelCatalogError(f"{label}: DeepSeek is excluded from dispatch and review by core.md P2")
    return model_id


def _require_execution_effort(value: Any, label: str) -> None:
    effort = _require_string(value, label)
    if effort not in VALID_CODEX_EFFORTS:
        raise ModelCatalogError(f"{label} must be one of {sorted(VALID_CODEX_EFFORTS)}")


def _validate_execution_routing(raw: Any, models: dict[str, Any]) -> None:
    execution_routing = _require_mapping(raw, "execution_routing")
    route = _require_mapping(execution_routing.get("sol_advised_bounded"), "execution_routing.sol_advised_bounded")
    _require_exact_keys(route, EXECUTION_ROUTE_KEYS, "execution_routing.sol_advised_bounded")

    advisor = _require_mapping(route["advisor"], "execution_routing.sol_advised_bounded.advisor")
    _require_exact_keys(advisor, ADVISOR_KEYS, "execution_routing.sol_advised_bounded.advisor")
    advisor_model_id = _require_active_execution_model(
        models,
        advisor["model_id"],
        "execution_routing.sol_advised_bounded.advisor.model_id",
    )
    _require_execution_effort(advisor["effort"], "execution_routing.sol_advised_bounded.advisor.effort")
    if advisor["role"] != "bounded_advisory_envelope":
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.advisor.role must be 'bounded_advisory_envelope'"
        )
    if advisor["role"] not in models[advisor_model_id]["roles"]:
        # #9583: the advisor seat reads the advisor model's catalog roles.
        raise ModelCatalogError(
            f"execution_routing.sol_advised_bounded.advisor.model_id {advisor_model_id!r} does not hold "
            f"the {advisor['role']!r} role"
        )
    if advisor["output_fields"] != ADVISOR_OUTPUT_FIELDS:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.advisor.output_fields must be exactly "
            f"{ADVISOR_OUTPUT_FIELDS!r}"
        )

    preferred = _require_mapping(route["preferred_worker"], "execution_routing.sol_advised_bounded.preferred_worker")
    _require_exact_keys(preferred, PREFERRED_WORKER_KEYS, "execution_routing.sol_advised_bounded.preferred_worker")
    _require_active_execution_model(
        models,
        preferred["model_id"],
        "execution_routing.sol_advised_bounded.preferred_worker.model_id",
    )
    _require_execution_effort(preferred["effort"], "execution_routing.sol_advised_bounded.preferred_worker.effort")
    for field in ("requires", "task_types", "prohibited_decisions", "escalation_triggers"):
        _require_string_list(preferred[field], f"execution_routing.sol_advised_bounded.preferred_worker.{field}")
    if set(preferred["requires"]) != BOUNDED_WORKER_REQUIRES:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.preferred_worker.requires must bind a complete envelope "
            "and objective scope ceiling"
        )
    expected_luna_sets = {
        "task_types": LUNA_TASK_TYPES,
        "prohibited_decisions": LUNA_PROHIBITED_DECISIONS,
        "escalation_triggers": LUNA_ESCALATION_TRIGGERS,
    }
    for field, expected in expected_luna_sets.items():
        if set(preferred[field]) != expected:
            raise ModelCatalogError(
                f"execution_routing.sol_advised_bounded.preferred_worker.{field} must include exactly "
                f"{sorted(expected)}"
            )
    _require_active_execution_model(
        models,
        preferred["escalate_to"],
        "execution_routing.sol_advised_bounded.preferred_worker.escalate_to",
    )

    # Operator decision 2026-09-30 (#9275): no bounded worker is dispatched without
    # a complete advisory envelope, so the catalog carries no direct-worker route.
    bounded_fallback = _require_mapping(
        route["bounded_fallback_worker"],
        "execution_routing.sol_advised_bounded.bounded_fallback_worker",
    )
    _require_exact_keys(
        bounded_fallback,
        BOUNDED_FALLBACK_WORKER_KEYS,
        "execution_routing.sol_advised_bounded.bounded_fallback_worker",
    )
    bounded_fallback_model_id = _require_active_execution_model(
        models,
        bounded_fallback["model_id"],
        "execution_routing.sol_advised_bounded.bounded_fallback_worker.model_id",
    )
    _require_execution_effort(
        bounded_fallback["effort"],
        "execution_routing.sol_advised_bounded.bounded_fallback_worker.effort",
    )
    for field in ("requires", "non_bounded_task_families"):
        _require_string_list(
            bounded_fallback[field],
            f"execution_routing.sol_advised_bounded.bounded_fallback_worker.{field}",
        )
    if set(bounded_fallback["requires"]) != BOUNDED_WORKER_REQUIRES:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.bounded_fallback_worker.requires must bind a complete "
            "envelope and objective scope ceiling"
        )
    if advisor_model_id in {preferred["model_id"], bounded_fallback_model_id}:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.advisor.model_id must not be a bounded worker model"
        )

    fallback = _require_mapping(
        route["autonomous_fallback"],
        "execution_routing.sol_advised_bounded.autonomous_fallback",
    )
    _require_exact_keys(fallback, FALLBACK_KEYS, "execution_routing.sol_advised_bounded.autonomous_fallback")
    _require_active_execution_model(
        models,
        fallback["model_id"],
        "execution_routing.sol_advised_bounded.autonomous_fallback.model_id",
    )
    _require_execution_effort(fallback["effort"], "execution_routing.sol_advised_bounded.autonomous_fallback.effort")
    _require_string_list(fallback["when"], "execution_routing.sol_advised_bounded.autonomous_fallback.when")

    boundary = _require_mapping(route["review_boundary"], "execution_routing.sol_advised_bounded.review_boundary")
    _require_exact_keys(boundary, REVIEW_BOUNDARY_KEYS, "execution_routing.sol_advised_bounded.review_boundary")
    advisory_family = _require_string(
        boundary["advisory_family"],
        "execution_routing.sol_advised_bounded.review_boundary.advisory_family",
    )
    if advisory_family != models[advisor_model_id]["family"]:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.review_boundary.advisory_family must match the advisor model family"
        )
    if boundary["advisory_satisfies_cross_family_review"] is not False:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.review_boundary.advisory_satisfies_cross_family_review must remain false"
        )
    if boundary["independent_cross_family_review_required"] is not True:
        raise ModelCatalogError(
            "execution_routing.sol_advised_bounded.review_boundary.independent_cross_family_review_required must remain true"
        )


def _validate_orchestrator_seats(raw: Any, models: dict[str, Any]) -> None:
    seats = _require_mapping(raw, "orchestrator_seats")
    for seat_name, raw_seat in seats.items():
        _require_string(seat_name, "orchestrator seat name")
        seat = _require_mapping(raw_seat, f"orchestrator_seats.{seat_name}")
        for field in ("model_id", "effort", "escalate_model_id", "escalate_effort"):
            _require_string(seat.get(field), f"orchestrator_seats.{seat_name}.{field}")
        esc_model = seat["escalate_model_id"]
        if esc_model not in models:
            raise ModelCatalogError(
                f"orchestrator_seats.{seat_name}.escalate_model_id references unknown model {esc_model!r}"
            )
        if models[esc_model]["lifecycle"] != "active":
            raise ModelCatalogError(
                f"orchestrator_seats.{seat_name}.escalate_model_id must reference an active model"
            )
        _require_routable_model(models, esc_model, f"orchestrator_seats.{seat_name}.escalate_model_id")
        if "fallback_model_id" in seat:
            fallback = _require_string(seat["fallback_model_id"], f"orchestrator_seats.{seat_name}.fallback_model_id")
            _require_routable_model(models, fallback, f"orchestrator_seats.{seat_name}.fallback_model_id")

        if seat_name == "cursor":
            model_id = seat["model_id"]
            allowlist = _require_string_list(
                seat.get("auto_allowlist"),
                "orchestrator_seats.cursor.auto_allowlist",
            )
            if tuple(allowlist) != CURSOR_AUTO_EXPECTED_ALLOWLIST:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.auto_allowlist must equal exactly {list(CURSOR_AUTO_EXPECTED_ALLOWLIST)}, got {allowlist}"
                )
            if model_id not in allowlist:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.model_id must be a concrete pin from auto_allowlist {allowlist}, got {model_id!r}"
                )
            auto_scope = _require_string(seat.get("auto_scope"), "orchestrator_seats.cursor.auto_scope")
            if auto_scope != CURSOR_AUTO_EXPECTED_SCOPE:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.auto_scope must be {CURSOR_AUTO_EXPECTED_SCOPE!r}, got {auto_scope!r}"
                )
            for allowed in allowlist:
                if allowed not in models:
                    raise ModelCatalogError(
                        f"orchestrator_seats.cursor.auto_allowlist references unknown model {allowed!r}"
                    )
                if models[allowed]["lifecycle"] != "active":
                    raise ModelCatalogError(
                        f"orchestrator_seats.cursor.auto_allowlist must reference active models, got {allowed!r}"
                    )
            attestation_rule = _require_string(
                seat.get("attestation_rule"),
                "orchestrator_seats.cursor.attestation_rule",
            )
            if attestation_rule != CURSOR_AUTO_EXPECTED_ATTESTATION_RULE:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.attestation_rule must be {CURSOR_AUTO_EXPECTED_ATTESTATION_RULE!r}, got {attestation_rule!r}"
                )
            resolution = _require_string(
                seat.get("unknown_auto_family_resolution"),
                "orchestrator_seats.cursor.unknown_auto_family_resolution",
            )
            if resolution != CURSOR_AUTO_EXPECTED_RESOLUTION:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.unknown_auto_family_resolution must be {CURSOR_AUTO_EXPECTED_RESOLUTION!r}, got {resolution!r}"
                )
            union_families = _require_string_list(
                seat.get("unknown_auto_union_families"),
                "orchestrator_seats.cursor.unknown_auto_union_families",
            )
            expected_families = sorted({models[m]["family"] for m in allowlist})
            if sorted(union_families) != expected_families:
                raise ModelCatalogError(
                    f"orchestrator_seats.cursor.unknown_auto_union_families must match allowlist model families {expected_families}, got {sorted(union_families)}"
                )
        else:
            model_id = seat["model_id"]
            if model_id not in models:
                raise ModelCatalogError(f"orchestrator_seats.{seat_name}.model_id references unknown model {model_id!r}")
            if models[model_id]["lifecycle"] != "active":
                raise ModelCatalogError(f"orchestrator_seats.{seat_name}.model_id must reference an active model")
            _require_routable_model(models, model_id, f"orchestrator_seats.{seat_name}.model_id")


def _validate_review_scheduler(raw: Any, models: dict[str, Any]) -> None:
    if raw is None:
        return
    scheduler = _require_mapping(raw, "review_scheduler")
    endpoints = _require_mapping(scheduler.get("endpoints"), "review_scheduler.endpoints")
    for name, raw_ep in endpoints.items():
        ep = _require_mapping(raw_ep, f"review_scheduler.endpoints.{name}")
        ep_models = ep.get("models", [])
        if not isinstance(ep_models, list):
            raise ModelCatalogError(f"review_scheduler.endpoints.{name}.models must be a list")
        for m in ep_models:
            if not isinstance(m, str) or not m.strip():
                raise ModelCatalogError(f"review_scheduler.endpoints.{name}.models contains invalid model id")
            if m.casefold() in {"auto", "cursor:auto"}:
                raise ModelCatalogError(
                    f"review_scheduler.endpoints.{name}.models cannot treat {m!r} as a formal review identity"
                )
            _require_routable_model(models, m, f"review_scheduler.endpoints.{name}.models")
        if name == "cursor" and ep.get("formal_review_eligible") is True:
            # Operator decision 2026-10-02 (#9488): the multi-model harness is a
            # formal reviewer only for the concrete models it pins.
            if not ep_models:
                raise ModelCatalogError(
                    "review_scheduler.endpoints.cursor needs an explicit models pin to be formal_review_eligible"
                )
            for m in ep_models:
                family = models[resolve_catalog_model_id(m, {"models": models})]["family"]
                if family in CURSOR_FORMAL_REVIEW_EXCLUDED_FAMILIES:
                    raise ModelCatalogError(
                        f"review_scheduler.endpoints.cursor.models cannot pin {m!r}: "
                        f"{family} models are not formal reviewers through Cursor"
                    )
    risk_models = scheduler.get("risk_reviewer_models", {})
    _require_mapping(risk_models, "review_scheduler.risk_reviewer_models")
    for risk, allowed in risk_models.items():
        label = f"review_scheduler.risk_reviewer_models.{risk}"
        if risk not in VALID_RISKS:
            raise ModelCatalogError(f"{label}: unknown risk; expected one of {sorted(VALID_RISKS)}")
        if not isinstance(allowed, list) or not allowed:
            raise ModelCatalogError(f"{label} must be a non-empty list of model ids")
        for model_id in allowed:
            _require_routable_model(models, model_id, label)
    activity_roles = _require_mapping(scheduler.get("activity_roles"), "review_scheduler.activity_roles")
    if set(activity_roles) != ACTIVITIES:
        raise ModelCatalogError(f"review_scheduler.activity_roles must define exactly {sorted(ACTIVITIES)}")
    held = {role for model in models.values() for role in model.get("roles", [])}
    for activity, roles in activity_roles.items():
        for role in _require_string_list(roles, f"review_scheduler.activity_roles.{activity}"):
            if role not in held:
                raise ModelCatalogError(f"review_scheduler.activity_roles.{activity} names {role!r}, which no model holds")


def _validate_activity_role_holders(catalog: dict[str, Any]) -> None:
    """Every formal reviewer holds a role the review activity admits (#9583)."""
    scheduler = catalog.get("review_scheduler")
    if scheduler is None:
        return
    references = [(f"review_candidates.{name}", entry["model_id"]) for name, entry in catalog["review_candidates"].items()]
    references += [
        (f"review_scheduler.endpoints.{name}.models", model_id)
        for name, endpoint in scheduler["endpoints"].items()
        if endpoint.get("formal_review_eligible") is True
        for model_id in endpoint.get("models") or []
    ]
    references += [
        (f"review_scheduler.risk_reviewer_models.{risk}", model_id)
        for risk, allowed in scheduler.get("risk_reviewer_models", {}).items()
        for model_id in allowed
    ]
    for label, model_id in references:
        if refusal := activity_role_refusal(model_id, REVIEW_ACTIVITY, catalog):
            raise ModelCatalogError(f"{label}: {refusal}")


def invocation_model(invocation: str) -> str | None:
    """The value of the first ``--model`` flag in ``invocation``, or None."""
    parts = shell_split(invocation)
    for index, part in enumerate(parts):
        flag, separator, value = part.partition("=")
        if flag == "--model":
            return value if separator else (parts[index + 1] if index + 1 < len(parts) else None)
    return None


def _validate_cursor_review_seats(catalog: dict[str, Any]) -> None:
    """A formal Cursor seat dispatches its runtime-attestable high-effort slug.

    Cursor reports the model the run actually used; ``record_cf_verdict`` maps
    only that high-effort report back to the catalog id, so the seat must
    dispatch ``<model>-high`` (a bare id runs a different variant).
    Operator decision 2026-10-05 (#9769) admits Grok as a regular reviewer.
    """
    endpoint = (catalog.get("review_scheduler") or {}).get("endpoints", {}).get("cursor") or {}
    if endpoint.get("formal_review_eligible") is not True:
        return
    pinned = set(endpoint.get("models", []))
    for name, candidate in catalog["review_candidates"].items():
        if candidate.get("route") != "cursor" or candidate["model_id"] not in pinned:
            continue
        slug = f"{candidate['model_id']}-high"
        if invocation_model(candidate["invocation"]) != slug:
            raise ModelCatalogError(
                f"review_candidates.{name}.invocation must dispatch the runtime-attestable Cursor slug {slug!r}"
            )


def _validate_formal_cf_defaults(raw: Any, models: dict[str, Any]) -> None:
    if raw is None:
        return
    defaults = _require_mapping(raw, "formal_cf_defaults")
    for name, raw_def in defaults.items():
        entry = _require_mapping(raw_def, f"formal_cf_defaults.{name}")
        model_id = entry.get("model_id")
        if isinstance(model_id, str) and model_id.casefold() in {"auto", "cursor:auto"}:
            raise ModelCatalogError(f"formal_cf_defaults.{name}.model_id cannot use {model_id!r} as formal CF default")
        for field in ("model_id", "escalate_model_id", "fallback_model_id"):
            if field in entry:
                _require_routable_model(models, entry[field], f"formal_cf_defaults.{name}.{field}")
        for member in _require_string_list(
            entry.get("family_models", []), f"formal_cf_defaults.{name}.family_models", allow_empty=True
        ):
            _require_routable_model(models, member, f"formal_cf_defaults.{name}.family_models")



def _lane_catalog_transport(catalog: dict[str, Any], lane: str) -> str | None:
    endpoints = (catalog.get("review_scheduler") or {}).get("endpoints") or {}
    endpoint = endpoints.get(lane) if isinstance(endpoints, dict) else None
    if not isinstance(endpoint, dict):
        return None
    transport = endpoint.get("catalog_transport")
    if isinstance(transport, str) and transport.strip():
        return transport.strip()
    return None


def _invocation_uses_model(invocation: str, model: str) -> bool:
    parts = invocation.split()
    return any(
        part == "--model" and index + 1 < len(parts) and parts[index + 1] == model for index, part in enumerate(parts)
    )


def substitution_model_admitted(catalog: dict[str, Any], lane: str, model: str) -> bool:
    """True when ``lane`` may be invoked with ``model``.

    A catalog model is admitted when its transports include the lane's
    ``catalog_transport`` and it is not retired. A Cursor CLI slug that is not
    itself a catalog id is admitted when a review candidate for that route
    invokes it with ``--model``.
    """
    if retired_model_refusal(model, catalog):
        return False
    canonical_id = resolve_catalog_model_id(model, catalog)
    if canonical_id and catalog["models"][canonical_id]["family"] == "deepseek":
        return False
    transport = _lane_catalog_transport(catalog, lane)
    models = catalog.get("models") or {}
    if transport and isinstance(models, dict):
        entry = models.get(model)
        if not isinstance(entry, dict):
            for candidate in models.values():
                aliases = candidate.get("aliases") if isinstance(candidate, dict) else None
                if isinstance(aliases, list) and model in aliases:
                    entry = candidate
                    break
        if (
            isinstance(entry, dict)
            and entry.get("lifecycle") != "retired"
            and entry.get("family") != "deepseek"
            and transport in (entry.get("transports") or [])
        ):
            return True
    candidates = catalog.get("review_candidates") or {}
    if isinstance(candidates, dict):
        for candidate in candidates.values():
            if not isinstance(candidate, dict) or candidate.get("route") != lane:
                continue
            invocation = candidate.get("invocation")
            if isinstance(invocation, str) and _invocation_uses_model(invocation, model):
                return True
    return False


def budget_substitution_table(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    """Return ``budget_substitution_models`` as lane → {source model: target model}."""
    source = catalog if catalog is not None else load_model_catalog()
    raw = source.get("budget_substitution_models") or {}
    if not isinstance(raw, dict):
        raise ModelCatalogError("budget_substitution_models must be a mapping")
    table: dict[str, dict[str, str]] = {}
    for lane, rows in raw.items():
        if not isinstance(lane, str) or not lane.strip():
            raise ModelCatalogError("budget_substitution_models lane must be a non-empty string")
        if not isinstance(rows, dict):
            raise ModelCatalogError(f"budget_substitution_models.{lane} must be a mapping")
        mapped: dict[str, str] = {}
        for source_model, target_model in rows.items():
            if not isinstance(source_model, str) or not source_model.strip():
                raise ModelCatalogError(f"budget_substitution_models.{lane} has an empty source model")
            if not isinstance(target_model, str) or not target_model.strip():
                raise ModelCatalogError(
                    f"budget_substitution_models.{lane}.{source_model} must be a non-empty string"
                )
            mapped[source_model.strip()] = target_model.strip()
        table[lane.strip()] = mapped
    return table


def _validate_budget_substitution_models(raw: Any, catalog: dict[str, Any]) -> None:
    if raw is None:
        return
    table = _require_mapping(raw, "budget_substitution_models")
    models = catalog["models"]
    for lane, rows in table.items():
        _require_string(lane, "budget_substitution_models lane")
        mapping = _require_mapping(rows, f"budget_substitution_models.{lane}")
        for source_model, target_model in mapping.items():
            _require_string(source_model, f"budget_substitution_models.{lane} source")
            target = _require_string(target_model, f"budget_substitution_models.{lane}.{source_model}")
            _require_routable_model(models, source_model, f"budget_substitution_models.{lane}.{source_model}")
            if not substitution_model_admitted(catalog, lane, target):
                raise ModelCatalogError(
                    f"budget_substitution_models.{lane} maps {source_model} to {target}, "
                    f"which {lane} does not admit"
                )


def validate_catalog(data: Any) -> dict[str, Any]:
    """Validate the catalog structure without enforcing wall-clock freshness."""
    # Normalize the top-level date without mutating the caller's object. This
    # matters to tests and tooling that compare the parsed YAML before/after
    # validation.
    catalog = _require_mapping(data, "catalog").copy()
    if not isinstance(catalog.get("schema_version"), str) or catalog["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS:
        raise ModelCatalogError(
            f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)!r}, got {catalog.get('schema_version')!r}"
        )

    reviewed_on = catalog.get("reviewed_on")
    if isinstance(reviewed_on, date):
        reviewed_date = reviewed_on
    elif isinstance(reviewed_on, str):
        try:
            reviewed_date = date.fromisoformat(reviewed_on)
        except ValueError as exc:
            raise ModelCatalogError("reviewed_on must be an ISO date") from exc
    else:
        raise ModelCatalogError("reviewed_on must be an ISO date")
    catalog["reviewed_on"] = reviewed_date.isoformat()

    refresh_after_days = catalog.get("refresh_after_days")
    if (
        not isinstance(refresh_after_days, int)
        or isinstance(refresh_after_days, bool)
        or not 1 <= refresh_after_days <= 30
    ):
        raise ModelCatalogError("refresh_after_days must be an integer from 1 through 30")

    tiers = _require_mapping(catalog.get("quality_tiers"), "quality_tiers")
    if not tiers or not all(
        isinstance(rank, int) and not isinstance(rank, bool) and rank > 0 for rank in tiers.values()
    ):
        raise ModelCatalogError("quality_tiers must map names to positive integer ranks")
    if len(set(tiers.values())) != len(tiers):
        raise ModelCatalogError("quality_tiers ranks must be unique")

    policy = _require_mapping(catalog.get("policy"), "policy")
    if policy.get("quality_first") is not True:
        raise ModelCatalogError("policy.quality_first must be true")
    if policy.get("selection_order") != EXPECTED_SELECTION_ORDER:
        raise ModelCatalogError(f"policy.selection_order must be exactly {EXPECTED_SELECTION_ORDER!r}")
    risk_floor = _require_mapping(policy.get("risk_quality_floor"), "policy.risk_quality_floor")
    if set(risk_floor) != VALID_RISKS:
        raise ModelCatalogError(f"policy.risk_quality_floor must define exactly {sorted(VALID_RISKS)}")
    for risk, tier in risk_floor.items():
        if tier not in tiers:
            raise ModelCatalogError(f"policy.risk_quality_floor.{risk} references unknown tier {tier!r}")

    models = _require_mapping(catalog.get("models"), "models")
    if not models:
        raise ModelCatalogError("models must not be empty")
    alias_owner: dict[str, str] = {}
    for model_id, raw in models.items():
        _require_string(model_id, "model id")
        model = _require_mapping(raw, f"models.{model_id}")
        _require_string(model.get("family"), f"models.{model_id}.family")
        tier = _require_string(model.get("tier"), f"models.{model_id}.tier")
        if tier not in tiers:
            raise ModelCatalogError(f"models.{model_id}.tier references unknown tier {tier!r}")
        lifecycle = _require_string(model.get("lifecycle"), f"models.{model_id}.lifecycle")
        if lifecycle not in VALID_LIFECYCLES:
            raise ModelCatalogError(f"models.{model_id}.lifecycle must be one of {sorted(VALID_LIFECYCLES)}")
        for field in ("roles", "transports", "strengths", "weaknesses", "sources"):
            values = _require_string_list(
                model.get(field), f"models.{model_id}.{field}",
                allow_empty=field == "transports" and lifecycle == "retired",
            )
            if field == "sources" and any(not source.startswith("https://") for source in values):
                raise ModelCatalogError(f"models.{model_id}.sources must use https URLs")
        if lifecycle == "retired" and model["transports"]:
            raise ModelCatalogError(f"models.{model_id}.transports must be empty for retired models")
        if model["family"] in {"openai", "xai"} and "hermes" in model["transports"]:
            raise ModelCatalogError(f"models.{model_id}.transports must not route GPT/Grok families through Hermes")
        aliases = model.get("aliases", [])
        if "runtime_model_ids" in model:
            _require_string_list(model["runtime_model_ids"], f"models.{model_id}.runtime_model_ids")
        if not isinstance(aliases, list) or not all(isinstance(alias, str) and alias.strip() for alias in aliases):
            raise ModelCatalogError(f"models.{model_id}.aliases must be a list of strings")
        for alias in aliases:
            if alias in models or alias in alias_owner:
                raise ModelCatalogError(f"duplicate model alias {alias!r}")
            alias_owner[alias] = model_id
        if "replaced_by" in model and lifecycle != "retired":
            raise ModelCatalogError(f"models.{model_id}.replaced_by is only valid on retired models")
        if "native_kimi" in model["transports"]:
            routes = _require_mapping(model.get("kimi_routes"), f"models.{model_id}.kimi_routes")
            for field in KIMI_ROUTE_FIELDS:
                _require_string(routes.get(field), f"models.{model_id}.kimi_routes.{field}")
            if routes["kimicc_alias"] not in aliases:
                raise ModelCatalogError(
                    f"models.{model_id}.kimi_routes.kimicc_alias must be listed in models.{model_id}.aliases"
                )
        if "glmcc" in model["transports"]:
            routes = _require_mapping(model.get("glm_routes"), f"models.{model_id}.glm_routes")
            for field in GLM_ROUTE_FIELDS:
                _require_string(routes.get(field), f"models.{model_id}.glm_routes.{field}")
            if routes["glmcc_alias"] != model_id and routes["glmcc_alias"] not in aliases:
                raise ModelCatalogError(
                    f"models.{model_id}.glm_routes.glmcc_alias must be model id or listed in models.{model_id}.aliases"
                )
    for model_id, model in models.items():
        if "replaced_by" in model:
            # Successor identity is metadata, not dispatch/review admission.
            replacement = _require_string(model["replaced_by"], f"models.{model_id}.replaced_by")
            if replacement not in models or models[replacement]["lifecycle"] != "active":
                raise ModelCatalogError(f"models.{model_id}.replaced_by must reference an active model")

    _validate_execution_routing(catalog.get("execution_routing"), models)

    candidates = _require_mapping(catalog.get("review_candidates"), "review_candidates")
    for name, raw in candidates.items():
        candidate = _require_mapping(raw, f"review_candidates.{name}")
        model_id = _require_string(candidate.get("model_id"), f"review_candidates.{name}.model_id")
        transport_raw = candidate.get("transport")
        if isinstance(transport_raw, str) and transport_raw == "cursor" and model_id.casefold() in {"auto", "cursor", "composer"}:
            raise ModelCatalogError(f"review_candidates.{name} requires a concrete Cursor model id, not {model_id!r}")
        if model_id.casefold() in {"auto", "cursor:auto"}:
            raise ModelCatalogError(f"review_candidates.{name} cannot use {model_id!r} as a formal review candidate")
        if model_id not in models:
            raise ModelCatalogError(f"review_candidates.{name}.model_id references unknown model {model_id!r}")
        _require_routable_model(models, model_id, f"review_candidates.{name}.model_id")
        runtime_ids = models[model_id].get("runtime_model_ids", [])
        if any("fast" in runtime_id.casefold().replace("_", "-").split("-") for runtime_id in runtime_ids):
            raise ModelCatalogError(f"models.{model_id}.runtime_model_ids must not admit fast review variants")
        if "suitability_roles" in candidate:
            suitability_roles = _require_string_list(
                candidate["suitability_roles"], f"review_candidates.{name}.suitability_roles"
            )
            if not set(suitability_roles) <= set(models[model_id]["roles"]):
                raise ModelCatalogError(f"review_candidates.{name}.suitability_roles must be held by its model")
        if "transport_fallback_for" in candidate:
            primary_name = _require_string(
                candidate["transport_fallback_for"], f"review_candidates.{name}.transport_fallback_for"
            )
            primary = candidates.get(primary_name)
            if (
                not isinstance(primary, dict)
                or primary.get("model_id") != model_id
                or primary.get("transport") == transport_raw
                or "transport_fallback_for" in primary
            ):
                raise ModelCatalogError(
                    f"review_candidates.{name}.transport_fallback_for must reference a primary transport of the same model"
                )
        if model_id.casefold().startswith("gemini-") or candidate.get("route") == "agy":
            raise ModelCatalogError(
                f"review_candidates.{name} violates operator 2026-09-25: "
                "Gemini reviews Ukrainian only, never code (model-assignment.md)"
            )
        if models[model_id]["lifecycle"] not in {"active", "fallback"}:
            raise ModelCatalogError(f"review candidate {name!r} must reference an active or fallback model")
        _require_string(candidate.get("route"), f"review_candidates.{name}.route")
        transport = _require_string(transport_raw, f"review_candidates.{name}.transport")
        if transport not in models[model_id]["transports"]:
            raise ModelCatalogError(
                f"review_candidates.{name}.transport {transport!r} is not listed in models.{model_id}.transports"
            )
        invocation = _require_string(candidate.get("invocation"), f"review_candidates.{name}.invocation")
        try:
            parts = shell_split(invocation)
        except ValueError as exc:
            raise ModelCatalogError(f"review_candidates.{name}.invocation is malformed: {exc}") from exc
        # Python's -m selects the executable module before application flags.
        # Start after that module (or the script), so a later -m is a model pin.
        argument_start = 1
        if parts and Path(parts[0]).name.startswith("python"):
            for index, part in enumerate(parts[1:], start=1):
                if part == "-m":
                    argument_start = index + 2
                    break
                if not part.startswith("-"):
                    argument_start = index + 1
                    break
        for index in range(argument_start, len(parts)):
            part = parts[index]
            flag, separator, value = part.partition("=")
            if flag in {"--model", "-m", "--to-model"}:
                if not separator:
                    value = parts[index + 1] if index + 1 < len(parts) else ""
                invoked = resolve_catalog_model_id(value, catalog)
                if invoked != model_id:
                    raise ModelCatalogError(
                        f"review_candidates.{name}.invocation model does not match {model_id!r}"
                    )
        profiles = _require_string_list(candidate.get("review_profiles"), f"review_candidates.{name}.review_profiles")
        if any(profile != profile.casefold() for profile in profiles):
            raise ModelCatalogError(f"review_candidates.{name}.review_profiles must use lowercase profile names")
        unsupported_profiles = sorted(set(profiles) - VALID_REVIEW_PROFILES)
        if unsupported_profiles:
            raise ModelCatalogError(
                f"review_candidates.{name}.review_profiles contains unsupported code-closeout "
                f"profiles {unsupported_profiles}; expected only {sorted(VALID_REVIEW_PROFILES)}"
            )
        if not isinstance(candidate.get("last_resort", False), bool):
            raise ModelCatalogError(f"review_candidates.{name}.last_resort must be a boolean")
        health_keys = candidate.get("health_keys", [])
        if not isinstance(health_keys, list) or not all(isinstance(item, str) and item.strip() for item in health_keys):
            raise ModelCatalogError(f"review_candidates.{name}.health_keys must be a list of strings")
        _require_string_list(candidate.get("capabilities"), f"review_candidates.{name}.capabilities")
        silence_timeout = candidate.get("requires_silence_timeout", False)
        if not isinstance(silence_timeout, bool):
            raise ModelCatalogError(f"review_candidates.{name}.requires_silence_timeout must be a boolean")
        egress_policy = candidate.get("requires_data_egress_policy")
        if egress_policy is not None:
            _require_string(
                egress_policy,
                f"review_candidates.{name}.requires_data_egress_policy",
            )
        for field in ("domain_excluded_from", "advisory_only_for_author_families"):
            values = candidate.get(field, [])
            if not isinstance(values, list) or not all(isinstance(item, str) and item.strip() for item in values):
                raise ModelCatalogError(f"review_candidates.{name}.{field} must be a list of strings")

    _validate_orchestrator_seats(catalog.get("orchestrator_seats"), models)
    _validate_review_scheduler(catalog.get("review_scheduler"), models)
    _validate_activity_role_holders(catalog)
    _validate_cursor_review_seats(catalog)
    _validate_formal_cf_defaults(catalog.get("formal_cf_defaults"), models)

    ladders = _require_mapping(catalog.get("review_ladders"), "review_ladders")
    if set(ladders) != VALID_RISKS:
        raise ModelCatalogError(f"review_ladders must define exactly {sorted(VALID_RISKS)}, got {sorted(ladders)}")
    for risk, rungs in ladders.items():
        if not isinstance(rungs, list) or not rungs:
            raise ModelCatalogError(f"review_ladders.{risk} must be a non-empty list")
        seen: set[str] = set()
        seen_models: set[str] = set()
        previous_rank = (False, 0)
        floor_rank = tiers[risk_floor[risk]]
        for rung in rungs:
            if not isinstance(rung, list) or not rung:
                raise ModelCatalogError(f"review_ladders.{risk} rungs must be non-empty lists")
            rung_ranks: set[tuple[bool, int]] = set()
            rung_models: set[str] = set()
            for candidate_name in rung:
                if candidate_name not in candidates:
                    raise ModelCatalogError(f"review_ladders.{risk} references unknown candidate {candidate_name!r}")
                if candidate_name in seen:
                    raise ModelCatalogError(f"review_ladders.{risk} repeats candidate {candidate_name!r}")
                seen.add(candidate_name)
                model_id = candidates[candidate_name]["model_id"]
                rung_models.add(model_id)
                if risk == "critical" and model_id.startswith("claude-sonnet-"):
                    raise ModelCatalogError(
                        f"review_ladders.{risk}: Sonnet is excluded from security review by core.md P2"
                    )
                if refusal := risk_reviewer_refusal(model_id, risk, catalog):
                    raise ModelCatalogError(f"review_ladders.{risk} candidate {candidate_name!r}: {refusal}")
                if models[model_id]["lifecycle"] != "active":
                    raise ModelCatalogError(
                        f"review_ladders.{risk} candidate {candidate_name!r} must reference an active model"
                    )
                rung_ranks.add((candidates[candidate_name].get("last_resort", False), tiers[models[model_id]["tier"]]))
            if len(rung_ranks) != 1:
                raise ModelCatalogError(f"review_ladders.{risk} mixes quality tiers in one rung")
            rung_rank = next(iter(rung_ranks))
            # Transport fallbacks may follow another model's primary (#9769).
            # Keep primary-model quality monotonic and check every rung's floor.
            transport_fallback = rung_models <= seen_models
            if rung_rank[0] < previous_rank[0] or (not transport_fallback and rung_rank < previous_rank):
                raise ModelCatalogError(f"review_ladders.{risk} improves quality in a later rung")
            if rung_rank[1] > floor_rank:
                raise ModelCatalogError(f"review_ladders.{risk} falls below its {risk_floor[risk]!r} quality floor")
            if not transport_fallback:
                previous_rank = rung_rank
            seen_models.update(rung_models)
    _validate_budget_substitution_models(catalog.get("budget_substitution_models"), catalog)
    from scripts.review.role_resolution import validate_role_catalog

    validate_role_catalog(catalog)
    return catalog


def resolve_role(
    role: str, *, catalog: dict[str, Any] | None = None, purpose: str,
    transport: str | None = None, family: str | None = None,
    context: dict[str, Any] | None = None, health: dict[str, Any] | None = None,
) -> RoleResolution:
    """Shared Python/shell API for additive routing roles; never launch a process."""
    from scripts.review.role_resolution import resolve_role as resolve

    return resolve(role, catalog=catalog, purpose=purpose, transport=transport,
                   family=family, context=context, health=health)


@lru_cache(maxsize=1)
def load_model_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    """Load the canonical catalog. Structural failures are fatal; staleness is linted."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ModelCatalogError(f"cannot read model catalog {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ModelCatalogError(f"invalid YAML in model catalog {path}: {exc}") from exc
    return validate_catalog(raw)


def model_aliases(catalog: dict[str, Any] | None = None) -> dict[str, str]:
    """Return every supported model input alias mapped to its canonical catalog id.

    Unlike the transport-specific alias helpers below, this covers *all* models
    so that a transport-agnostic validator (e.g. the ACP catalog gate) can
    resolve any caller-supplied alias before the catalog dict lookup.
    """
    models = (catalog or load_model_catalog())["models"]
    aliases: dict[str, str] = {}
    for model_id, model in models.items():
        aliases[model_id] = model_id
        aliases.update({alias: model_id for alias in model.get("aliases", [])})
    return aliases


def _model_id_candidates(model: str) -> list[str]:
    """Return ``model`` plus each harness-qualified suffix, most specific first.

    ``cursor:openai/gpt-6-sol`` yields itself, ``openai/gpt-6-sol`` and
    ``gpt-6-sol``; ``kimi-code/k3`` still matches its own catalog id first.
    """
    candidates = [model]
    for index, char in enumerate(model):
        if char in "/:" and model[index + 1 :]:
            candidates.append(model[index + 1 :])
    return candidates


def canonical_model_id(model: Any, catalog: dict[str, Any] | None = None) -> str | None:
    """The catalog id ``model`` names, or None when it names no catalog model.

    Matches case-insensitively through catalog aliases and harness prefixes
    (``codex:gpt-6-luna``, ``openai/gpt-6-luna``), drops a bracketed context
    suffix (``claude-opus-5-5[1m]``), and resolves a provider variant such as
    ``gpt-6-luna-high`` to the longest catalog id it extends.
    """
    text = str(model or "").strip().split("[", 1)[0].strip()
    if not text:
        return None
    catalog = catalog or load_model_catalog()
    lookup = {alias.casefold(): model_id for alias, model_id in model_aliases(catalog).items()}
    candidates = [candidate.casefold() for candidate in _model_id_candidates(text)]
    model_id = next((lookup[candidate] for candidate in candidates if candidate in lookup), None)
    if model_id is None:
        extended = [
            (len(alias), owner)
            for candidate in candidates
            for alias, owner in lookup.items()
            if candidate.startswith(f"{alias}-")
        ]
        model_id = max(extended)[1] if extended else None
    return model_id


@dataclass(frozen=True)
class BoundedExecutionPolicy:
    """The catalog's bounded-worker admission facts (``execution_routing.sol_advised_bounded``)."""

    advisor_model_id: str
    advisor_role: str
    advisor_output_fields: tuple[str, ...]
    bounded_worker_model_id: str
    bounded_fallback_model_id: str
    non_bounded_task_families: frozenset[str]


ADVISOR_ROUTE = "execution_routing.sol_advised_bounded.advisor"


def bounded_execution_policy(catalog: dict[str, Any] | None = None) -> BoundedExecutionPolicy:
    """The validated bounded-worker policy: who advises, which models need an envelope, and what it holds."""
    route = (catalog or load_model_catalog())["execution_routing"]["sol_advised_bounded"]
    fallback = route["bounded_fallback_worker"]
    return BoundedExecutionPolicy(
        advisor_model_id=route["advisor"]["model_id"],
        advisor_role=route["advisor"]["role"],
        advisor_output_fields=tuple(route["advisor"]["output_fields"]),
        bounded_worker_model_id=route["preferred_worker"]["model_id"],
        bounded_fallback_model_id=fallback["model_id"],
        non_bounded_task_families=frozenset(family.strip() for family in fallback["non_bounded_task_families"]),
    )


def is_cursor_auto_selector(model: Any) -> bool:
    """True when ``model`` asks Cursor to choose the model (Auto) instead of naming one.

    Matches case-insensitively, with or without a ``cursor:`` or ``cursor/`` prefix.
    ``None`` and an empty value are not selectors: the Cursor adapter pins its
    default model when none is given.
    """
    text = str(model or "").strip().casefold()
    for prefix in ("cursor:", "cursor/"):
        if text.startswith(prefix):
            text = text[len(prefix) :]
    return text in _CURSOR_SELECTOR_MODELS


def cursor_pinned_models(catalog: dict[str, Any] | None = None) -> tuple[str, ...]:
    """The concrete Cursor pins that replace Auto: the seat pin first, then the rest of the allowlist."""
    seat = (catalog or load_model_catalog())["orchestrator_seats"]["cursor"]
    pin = seat["model_id"]
    return (pin, *(model for model in seat["auto_allowlist"] if model != pin))


def cursor_non_dispatch_model_refusal(model: Any, catalog: dict[str, Any] | None = None) -> str | None:
    """Return a typed refusal unless ``model`` is a concrete approved Cursor pin.

    For Cursor paths outside delegate's admitted implementation dispatch (bridge
    review, consult, discuss and queued-ask drains): Auto is never admitted there,
    and a missing model is refused rather than defaulted, because the legacy
    default was Auto (operator decision 2026-09-30, #9274).
    """
    pins = cursor_pinned_models(catalog)
    fix = f"pin {' or '.join(pins)} (operator decision 2026-09-30, #9274)"
    text = str(model or "").strip()
    if not text:
        return f"no concrete Cursor model is pinned ({CURSOR_MODEL_UNPINNED_CODE}); {fix}"
    if is_cursor_auto_selector(text):
        return (
            f"model {text!r} runs only a delegate-admitted write implementation dispatch "
            f"({CURSOR_AUTO_OUTSIDE_CODING_TASK_CODE}); {fix}"
        )
    if text not in pins:
        return f"model {text!r} is not an approved Cursor pin ({CURSOR_MODEL_NOT_APPROVED_CODE}); {fix}"
    return None


def resolve_catalog_model_id(model: Any, catalog: dict[str, Any] | None = None) -> str | None:
    """Resolve aliases, harness prefixes, effort suffixes and bracket overrides (one identity: ``canonical_model_id``)."""
    return canonical_model_id(model, catalog)


def runtime_model_matches_requested(
    requested_model: str, runtime_model: str, catalog: dict[str, Any] | None = None,
) -> bool:
    """Compare runtime attribution to an exact pin or its catalogued runtime IDs.

    This classifies substitution telemetry only; it does not grant review
    admission or replace the recorder's source-bound runtime attestation.
    """
    if requested_model == runtime_model:
        return True
    catalog = catalog or load_model_catalog()
    model_id = resolve_catalog_model_id(requested_model, catalog)
    return bool(model_id and runtime_model in catalog["models"][model_id].get("runtime_model_ids", []))


def retired_model_refusal(model: Any, catalog: dict[str, Any] | None = None) -> str | None:
    """Refuse retired ids using the same canonical identity as review admission.

    Delegate, the runner and adapter model guards call this before side effects.
    Unknown ids return None; transport gates own them.
    """
    text = str(model or "").strip()
    if not text:
        return None
    catalog = catalog or load_model_catalog()
    models = catalog["models"]
    model_id = resolve_catalog_model_id(text, catalog)
    if model_id is None or models[model_id]["lifecycle"] != "retired":
        return None
    replacement = models[model_id].get("replaced_by")
    advice = f"use {replacement}" if replacement else "use an active catalog model"
    return f"model {text!r} is retired in the model catalog ({model_id}); {advice}"


def activity_role_refusal(model: Any, activity: str, catalog: dict[str, Any] | None = None) -> str | None:
    """Refuse a model pin whose catalog ``roles`` admit no ``activity`` (#9583).

    ``activity`` is ``review`` (a review, critique or approval of record) or
    ``consult`` (an ACP ask, consult or discussion, which the review roles also
    admit); ``review_scheduler.activity_roles`` names the roles each admits. A
    retired model holds no role. Unknown ids return None; transport and
    resolver gates own them.
    """
    text = str(model or "").strip()
    if not text:
        return None
    catalog = catalog or load_model_catalog()
    model_id = resolve_catalog_model_id(text, catalog)
    if model_id is None:
        return None
    if refusal := retired_model_refusal(model_id, catalog):
        return refusal
    activity_roles = catalog["review_scheduler"]["activity_roles"]
    admitted = set(activity_roles[REVIEW_ACTIVITY])
    if activity == CONSULT_ACTIVITY:
        admitted |= set(activity_roles[CONSULT_ACTIVITY])
    elif activity != REVIEW_ACTIVITY:
        raise ValueError(f"unknown activity {activity!r}; expected one of {sorted(ACTIVITIES)}")
    roles = catalog["models"][model_id]["roles"]
    if admitted.intersection(roles):
        return None
    work = "review, critique or approval" if activity == REVIEW_ACTIVITY else "ACP ask, consult or discussion"
    return (
        f"model {text!r} ({model_id}) holds no {work} role in the model catalog (roles: {', '.join(roles)}; "
        f"review_scheduler.activity_roles.{activity}, #9583)"
    )


def risk_reviewer_refusal(model: Any, risk: Any, catalog: dict[str, Any] | None = None) -> str | None:
    """Refuse a formal reviewer outside ``review_scheduler.risk_reviewer_models`` for ``risk`` (#9538, #9769).

    A risk with no listed models admits every model; this gate only narrows.
    """
    catalog = catalog or load_model_catalog()
    risk_key = str(risk or "").strip().casefold()
    allowed = ((catalog.get("review_scheduler") or {}).get("risk_reviewer_models") or {}).get(risk_key)
    if not allowed:
        return None
    model_id = resolve_catalog_model_id(str(model or "").strip(), catalog)
    if model_id in allowed:
        return None
    return (
        f"a formal review at {risk_key} risk is performed only by {', '.join(allowed)} "
        f"(operator decisions #9538, #9769); got {model_id or model!r}"
    )


def require_execution_model(
    model: str, *, transport: str, catalog: dict[str, Any] | None = None,
) -> str:
    """Reject frozen audit defaults before provider or configuration side effects.

    Historical model palettes remain readable; they do not authorize new runs.
    Retirement uses the canonical refusal path shared with fleet admission.
    """
    catalog = catalog or load_model_catalog()
    refusal = retired_model_refusal(model, catalog)
    if refusal:
        raise ModelCatalogError(refusal)
    model_id = resolve_catalog_model_id(model, catalog)
    if model_id is None:
        raise ModelCatalogError(f"model {model!r} is not in the model catalog")
    entry = catalog["models"][model_id]
    if entry["lifecycle"] not in {"active", "fallback"}:
        raise ModelCatalogError(f"model {model!r} is not admitted for execution")
    if transport not in entry["transports"]:
        raise ModelCatalogError(f"model {model!r} has no admitted {transport} transport")
    return model_id


def kimi_model_aliases(catalog: dict[str, Any] | None = None) -> dict[str, str]:
    """Return every supported Kimi input alias mapped to its native CLI model id."""
    models = (catalog or load_model_catalog())["models"]
    aliases: dict[str, str] = {}
    for model_id, model in models.items():
        if "native_kimi" not in model["transports"]:
            continue
        aliases[model_id] = model_id
        aliases.update({alias: model_id for alias in model.get("aliases", [])})
    return aliases


def resolve_kimi_model(model: str, catalog: dict[str, Any] | None = None) -> tuple[str, dict[str, str]]:
    """Resolve one Kimi input alias to native and KimiCC route metadata."""
    source = catalog or load_model_catalog()
    aliases = kimi_model_aliases(source)
    try:
        model_id = aliases[model]
    except KeyError as exc:
        raise ModelCatalogError(f"unsupported Kimi model {model!r}; allowed: {sorted(aliases)}") from exc
    return model_id, source["models"][model_id]["kimi_routes"]


def glm_model_aliases(catalog: dict[str, Any] | None = None) -> dict[str, str]:
    """Return every supported GLM input alias mapped to its catalog model id."""
    models = (catalog or load_model_catalog())["models"]
    aliases: dict[str, str] = {}
    for model_id, model in models.items():
        if "glmcc" not in model.get("transports", []):
            continue
        aliases[model_id] = model_id
        aliases.update({alias: model_id for alias in model.get("aliases", [])})
    return aliases


def resolve_glm_model(model: str, catalog: dict[str, Any] | None = None) -> tuple[str, dict[str, str]]:
    """Resolve one GLM input alias to native and GLMCC route metadata."""
    source = catalog or load_model_catalog()
    aliases = glm_model_aliases(source)
    try:
        model_id = aliases[model]
    except KeyError as exc:
        raise ModelCatalogError(f"unsupported GLM model {model!r}; allowed: {sorted(aliases)}") from exc
    return model_id, source["models"][model_id]["glm_routes"]


def validate_kimi_alias_consumers(project_root: Path = PROJECT_ROOT) -> None:
    """Reject local alias maps so all Kimi surfaces stay catalog-backed."""
    consumers = {
        # BOTH kimi harness branches must resolve aliases through the catalog:
        # the native branch via --resolve-kimi-model --format native (review
        # finding on #5958 r3 — this requirement was narrowed away in the
        # cutover, blinding the guard while the native branch regressed), the
        # claude-code branch via kimicc_configure_route.
        "scripts/launchers/kimi.sh": (
            "kimicc_configure_route",
            "--resolve-kimi-model",
            "--format native",
        ),
        "scripts/lib/kimicc_route.sh": ("--resolve-kimi-model", "--format kimicc"),
        "scripts/agent_runtime/adapters/kimi.py": ("kimi_model_aliases()",),
    }
    for relative_path, required_snippets in consumers.items():
        path = project_root / relative_path
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ModelCatalogError(f"cannot read Kimi alias consumer {relative_path}: {exc}") from exc
        missing = [snippet for snippet in required_snippets if snippet not in source]
        if missing:
            raise ModelCatalogError(
                f"{relative_path} must resolve Kimi aliases through model_catalog.yaml; missing {missing}"
            )

    kimi_adapter = (project_root / "scripts" / "launchers" / "kimi.sh").read_text(encoding="utf-8")
    if "resolve_kimi_model() {\n  case" in kimi_adapter:
        raise ModelCatalogError("Kimi launcher adapter contains a local Kimi alias case map")
    adapter = (project_root / "scripts/agent_runtime/adapters/kimi.py").read_text(encoding="utf-8")
    if "KIMI_MODEL_ALIASES: dict[str, str] = {" in adapter:
        raise ModelCatalogError("KimiAdapter contains a local Kimi alias map")
    kimicc_helper = (project_root / "scripts" / "lib" / "kimicc_route.sh").read_text(encoding="utf-8")
    if 'case "$MODEL_ALIAS"' in kimicc_helper:
        raise ModelCatalogError("KimiCC route helper contains a local Kimi alias case map")


def validate_glm_alias_consumers(project_root: Path = PROJECT_ROOT) -> None:
    """Reject local alias maps so all GLM surfaces stay catalog-backed."""
    consumers = {
        "scripts/lib/glmcc_route.sh": ("--resolve-glm-model", "--format glmcc"),
    }
    for relative_path, required_snippets in consumers.items():
        path = project_root / relative_path
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ModelCatalogError(f"cannot read GLM alias consumer {relative_path}: {exc}") from exc
        missing = [snippet for snippet in required_snippets if snippet not in source]
        if missing:
            raise ModelCatalogError(
                f"{relative_path} must resolve GLM aliases through model_catalog.yaml; missing {missing}"
            )


def _main() -> int:
    """Expose catalog-backed model resolution for shell launchers."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Resolve routing roles or Kimi/GLM aliases and refuse retired models for shell launchers.\n"
            "Use for catalog admission and route lookup, not provider-health or quota probing."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.review.model_catalog --resolve-kimi-model k3\n"
            "  .venv/bin/python -m scripts.review.model_catalog --resolve-glm-model glm --format glmcc\n"
            "  .venv/bin/python -m scripts.review.model_catalog --check-retired-model claude-fable-5\n"
            "  .venv/bin/python -m scripts.review.model_catalog --resolve-role bounded_advisor\n"
            "Outputs: model id, tab-separated alias route fields, or role-resolution JSON on stdout; no writes.\n"
            "Exit codes: 0 resolved or not retired; 2 retired model, invalid arguments or unknown route.\n"
            "Related: scripts/config/model_catalog.yaml; scripts/lib/kimicc_route.sh."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--resolve-kimi-model", metavar="ALIAS", help="Kimi catalog alias to resolve, e.g. k3")
    group.add_argument("--resolve-glm-model", metavar="ALIAS", help="GLM catalog alias to resolve, e.g. glm")
    group.add_argument("--resolve-role", metavar="ROLE", help="Stable routing role to inspect as JSON, e.g. bounded_advisor")
    group.add_argument(
        "--check-retired-model", metavar="MODEL",
        help="Refuse a retired catalog identity, including aliases and context suffixes; e.g. claude-fable-5",
    )
    parser.add_argument(
        "--format", choices=("native", "kimicc", "glmcc"), default="native",
        help="Alias output: model id (native, default) or route fields (kimicc/glmcc); roles always emit JSON",
    )
    parser.add_argument("--purpose", choices=("inspect", "launch"), default="inspect",
                        help="Role inspection or explicit launch argv construction (default: inspect; never executes)")
    parser.add_argument("--transport", help="Optional role transport filter, e.g. native_codex; default: all")
    parser.add_argument("--family", help="Optional role independence-family filter, e.g. openai; default: all")
    parser.add_argument("--role-context-file", type=Path, help="Optional role context JSON path; default: no requirements")
    parser.add_argument("--role-health-file", type=Path, help="Optional role health JSON path; default: unknown observation, v1 ranking")
    args = parser.parse_args()

    if args.resolve_role:
        import json

        try:
            context = json.loads(args.role_context_file.read_text()) if args.role_context_file else None
            health = json.loads(args.role_health_file.read_text()) if args.role_health_file else None
            resolution = resolve_role(args.resolve_role, purpose=args.purpose, transport=args.transport,
                                      family=args.family, context=context, health=health)
        except (ModelCatalogError, ValueError, OSError) as exc:
            parser.error(str(exc))
        print(json.dumps(resolution.to_dict(), indent=2))
    elif args.check_retired_model:
        try:
            refusal = retired_model_refusal(args.check_retired_model)
        except ModelCatalogError as exc:
            parser.error(str(exc))
        if refusal:
            print(refusal, file=sys.stderr)
            return 2
    elif args.resolve_kimi_model:
        try:
            model_id, routes = resolve_kimi_model(args.resolve_kimi_model)
        except ModelCatalogError as exc:
            parser.error(str(exc))
        if args.format == "native":
            print(model_id)
        else:
            print(
                "\t".join(
                    (
                        routes["kimicc_alias"],
                        routes["platform_model_id"],
                        routes["coding_model_id"],
                        routes["context_profile"],
                    )
                )
            )
    elif args.resolve_glm_model:
        try:
            model_id, routes = resolve_glm_model(args.resolve_glm_model)
        except ModelCatalogError as exc:
            parser.error(str(exc))
        if args.format == "native":
            print(model_id)
        else:
            print(
                "\t".join(
                    (
                        routes["glmcc_alias"],
                        routes["platform_model_id"],
                        routes["coding_model_id"],
                        routes["context_profile"],
                    )
                )
            )
    return 0


def catalog_age_days(catalog: dict[str, Any], *, as_of: date | None = None) -> int:
    """Return non-negative catalog age; future review dates fail structurally."""
    today = as_of or date.today()
    reviewed = date.fromisoformat(str(catalog["reviewed_on"]))
    age = (today - reviewed).days
    if age < 0:
        raise ModelCatalogError(f"reviewed_on {reviewed.isoformat()} is in the future relative to {today.isoformat()}")
    return age


def catalog_is_stale(catalog: dict[str, Any], *, as_of: date | None = None) -> bool:
    return catalog_age_days(catalog, as_of=as_of) > int(catalog["refresh_after_days"])


if __name__ == "__main__":
    raise SystemExit(_main())
