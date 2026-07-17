"""Load and structurally validate the canonical fleet model catalog."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

CATALOG_PATH = Path(__file__).resolve().parents[1] / "config" / "model_catalog.yaml"
EXPECTED_SCHEMA_VERSION = "model-catalog.v1"
VALID_LIFECYCLES = frozenset({"active", "fallback", "hold", "retired"})
VALID_RISKS = frozenset({"low", "medium", "high", "critical"})
EXPECTED_SELECTION_ORDER = [
    "independence_and_hard_gates",
    "task_risk_quality_tier",
    "health_and_quota_within_tier",
    "cost_within_equivalent_fit",
]


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


def _require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ModelCatalogError(f"{label} must be a non-empty list of strings")
    return [item.strip() for item in value]


def validate_catalog(data: Any) -> dict[str, Any]:
    """Validate the catalog structure without enforcing wall-clock freshness."""
    # Normalize the top-level date without mutating the caller's object. This
    # matters to tests and tooling that compare the parsed YAML before/after
    # validation.
    catalog = _require_mapping(data, "catalog").copy()
    if catalog.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ModelCatalogError(
            f"schema_version must be {EXPECTED_SCHEMA_VERSION!r}, "
            f"got {catalog.get('schema_version')!r}"
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
        isinstance(rank, int) and not isinstance(rank, bool) and rank > 0
        for rank in tiers.values()
    ):
        raise ModelCatalogError("quality_tiers must map names to positive integer ranks")
    if len(set(tiers.values())) != len(tiers):
        raise ModelCatalogError("quality_tiers ranks must be unique")

    policy = _require_mapping(catalog.get("policy"), "policy")
    if policy.get("quality_first") is not True:
        raise ModelCatalogError("policy.quality_first must be true")
    if policy.get("selection_order") != EXPECTED_SELECTION_ORDER:
        raise ModelCatalogError(
            f"policy.selection_order must be exactly {EXPECTED_SELECTION_ORDER!r}"
        )
    risk_floor = _require_mapping(
        policy.get("risk_quality_floor"), "policy.risk_quality_floor"
    )
    if set(risk_floor) != VALID_RISKS:
        raise ModelCatalogError(
            f"policy.risk_quality_floor must define exactly {sorted(VALID_RISKS)}"
        )
    for risk, tier in risk_floor.items():
        if tier not in tiers:
            raise ModelCatalogError(
                f"policy.risk_quality_floor.{risk} references unknown tier {tier!r}"
            )

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
        lifecycle = _require_string(
            model.get("lifecycle"), f"models.{model_id}.lifecycle"
        )
        if lifecycle not in VALID_LIFECYCLES:
            raise ModelCatalogError(
                f"models.{model_id}.lifecycle must be one of {sorted(VALID_LIFECYCLES)}"
            )
        for field in ("roles", "transports", "strengths", "weaknesses", "sources"):
            values = _require_string_list(model.get(field), f"models.{model_id}.{field}")
            if field == "sources" and any(not source.startswith("https://") for source in values):
                raise ModelCatalogError(f"models.{model_id}.sources must use https URLs")
        if model["family"] in {"openai", "xai"} and "hermes" in model["transports"]:
            raise ModelCatalogError(
                f"models.{model_id}.transports must not route GPT/Grok families through Hermes"
            )
        aliases = model.get("aliases", [])
        if not isinstance(aliases, list) or not all(
            isinstance(alias, str) and alias.strip() for alias in aliases
        ):
            raise ModelCatalogError(f"models.{model_id}.aliases must be a list of strings")
        for alias in aliases:
            if alias in models or alias in alias_owner:
                raise ModelCatalogError(f"duplicate model alias {alias!r}")
            alias_owner[alias] = model_id

    candidates = _require_mapping(catalog.get("review_candidates"), "review_candidates")
    for name, raw in candidates.items():
        candidate = _require_mapping(raw, f"review_candidates.{name}")
        model_id = _require_string(
            candidate.get("model_id"), f"review_candidates.{name}.model_id"
        )
        if model_id not in models:
            raise ModelCatalogError(
                f"review_candidates.{name}.model_id references unknown model {model_id!r}"
            )
        if models[model_id]["lifecycle"] != "active":
            raise ModelCatalogError(
                f"review candidate {name!r} must reference an active model"
            )
        _require_string(candidate.get("route"), f"review_candidates.{name}.route")
        transport = _require_string(
            candidate.get("transport"), f"review_candidates.{name}.transport"
        )
        if transport not in models[model_id]["transports"]:
            raise ModelCatalogError(
                f"review_candidates.{name}.transport {transport!r} is not listed in "
                f"models.{model_id}.transports"
            )
        _require_string_list(
            candidate.get("capabilities"), f"review_candidates.{name}.capabilities"
        )
        silence_timeout = candidate.get("requires_silence_timeout", False)
        if not isinstance(silence_timeout, bool):
            raise ModelCatalogError(
                f"review_candidates.{name}.requires_silence_timeout must be a boolean"
            )
        egress_policy = candidate.get("requires_data_egress_policy")
        if egress_policy is not None:
            _require_string(
                egress_policy,
                f"review_candidates.{name}.requires_data_egress_policy",
            )
        for field in ("domain_excluded_from", "advisory_only_for_author_families"):
            values = candidate.get(field, [])
            if not isinstance(values, list) or not all(
                isinstance(item, str) and item.strip() for item in values
            ):
                raise ModelCatalogError(
                    f"review_candidates.{name}.{field} must be a list of strings"
                )

    ladders = _require_mapping(catalog.get("review_ladders"), "review_ladders")
    if set(ladders) != VALID_RISKS:
        raise ModelCatalogError(
            f"review_ladders must define exactly {sorted(VALID_RISKS)}, got {sorted(ladders)}"
        )
    for risk, rungs in ladders.items():
        if not isinstance(rungs, list) or not rungs:
            raise ModelCatalogError(f"review_ladders.{risk} must be a non-empty list")
        seen: set[str] = set()
        previous_rank = 0
        floor_rank = tiers[risk_floor[risk]]
        for rung in rungs:
            if not isinstance(rung, list) or not rung:
                raise ModelCatalogError(
                    f"review_ladders.{risk} rungs must be non-empty lists"
                )
            rung_ranks: set[int] = set()
            for candidate_name in rung:
                if candidate_name not in candidates:
                    raise ModelCatalogError(
                        f"review_ladders.{risk} references unknown candidate {candidate_name!r}"
                    )
                if candidate_name in seen:
                    raise ModelCatalogError(
                        f"review_ladders.{risk} repeats candidate {candidate_name!r}"
                    )
                seen.add(candidate_name)
                model_id = candidates[candidate_name]["model_id"]
                rung_ranks.add(tiers[models[model_id]["tier"]])
            if len(rung_ranks) != 1:
                raise ModelCatalogError(
                    f"review_ladders.{risk} mixes quality tiers in one rung"
                )
            rung_rank = next(iter(rung_ranks))
            if rung_rank < previous_rank:
                raise ModelCatalogError(
                    f"review_ladders.{risk} improves quality in a later rung"
                )
            if rung_rank > floor_rank:
                raise ModelCatalogError(
                    f"review_ladders.{risk} falls below its {risk_floor[risk]!r} quality floor"
                )
            previous_rank = rung_rank
    return catalog


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


def catalog_age_days(catalog: dict[str, Any], *, as_of: date | None = None) -> int:
    """Return non-negative catalog age; future review dates fail structurally."""
    today = as_of or date.today()
    reviewed = date.fromisoformat(str(catalog["reviewed_on"]))
    age = (today - reviewed).days
    if age < 0:
        raise ModelCatalogError(
            f"reviewed_on {reviewed.isoformat()} is in the future relative to {today.isoformat()}"
        )
    return age


def catalog_is_stale(catalog: dict[str, Any], *, as_of: date | None = None) -> bool:
    return catalog_age_days(catalog, as_of=as_of) > int(catalog["refresh_after_days"])
