"""Contract tests for the canonical, freshness-gated fleet model catalog."""

from __future__ import annotations

from copy import deepcopy
from datetime import date

import pytest

from scripts.agent_runtime.registry import AGENTS
from scripts.review.model_catalog import (
    ModelCatalogError,
    catalog_age_days,
    catalog_is_stale,
    load_model_catalog,
    validate_catalog,
)


def test_committed_catalog_is_structurally_valid_and_current():
    catalog = load_model_catalog()
    assert catalog["schema_version"] == "model-catalog.v1"
    assert catalog["reviewed_on"] == "2026-07-17"
    assert catalog_age_days(catalog, as_of=date(2026, 7, 17)) == 0
    assert not catalog_is_stale(catalog, as_of=date(2026, 8, 16))
    assert catalog_is_stale(catalog, as_of=date(2026, 8, 17))


def test_catalog_covers_current_preferred_frontier_and_efficient_models():
    models = load_model_catalog()["models"]
    required = {
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "claude-fable-5",
        "claude-opus-4-8",
        "claude-sonnet-5",
        "gemini-3.1-pro-high",
        "gemini-3.5-flash-high",
        "grok-4.5",
        "kimi-code/k3",
        "glm-5.2",
        "deepseek-v4-pro",
        "deepseek-v4-flash",
        "poolside/laguna-m.1",
        "composer-2.5",
    }
    assert required <= set(models)


def test_runtime_registry_defaults_resolve_to_catalog_model_or_alias():
    catalog = load_model_catalog()
    known = set(catalog["models"])
    for model_id, model in catalog["models"].items():
        known.update(model.get("aliases", []))
        known.add(model_id)

    unresolved = {
        agent: entry["default_model"]
        for agent, entry in AGENTS.items()
        if entry["default_model"] not in {None, "auto"}
        and entry["default_model"] not in known
    }
    assert unresolved == {}


def test_composer_is_conservatively_moonshot_for_independence():
    composer = load_model_catalog()["models"]["composer-2.5"]
    assert composer["family"] == "moonshot"
    assert composer["lab"] == "cursor"


def test_gpt_and_grok_formal_routes_are_native_only():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["openai_frontier"]["transport"] == "native_codex"
    assert candidates["gpt-5.6-terra"]["transport"] == "native_codex"
    assert candidates["grok-4.5"]["transport"] == "native_grok"


def test_bridge_only_reviewers_expose_executable_invocations():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["pool"]["invocation"].endswith("ask-pool")
    assert candidates["glm-5.2"]["invocation"].endswith("ask-glm")
    assert candidates["gemini-3.1-pro"]["health_keys"] == ["gemini"]


def test_formal_review_candidates_declare_supported_profiles_and_concrete_cursor_model():
    candidates = load_model_catalog()["review_candidates"]
    assert all(candidate["review_profiles"] == ["code", "infra"] for candidate in candidates.values())
    assert candidates["composer-2.5"]["model_id"] == "composer-2.5"


def test_catalog_rejects_unknown_candidate_model_reference():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["pool"]["model_id"] = "missing-model"
    with pytest.raises(ModelCatalogError, match="unknown model"):
        validate_catalog(broken)


def test_catalog_rejects_missing_risk_ladder():
    broken = deepcopy(load_model_catalog())
    del broken["review_ladders"]["critical"]
    with pytest.raises(ModelCatalogError, match="define exactly"):
        validate_catalog(broken)


def test_catalog_rejects_candidate_transport_not_supported_by_model():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["grok-4.5"]["transport"] = "hermes"
    with pytest.raises(ModelCatalogError, match="is not listed"):
        validate_catalog(broken)


def test_catalog_rejects_bare_cursor_model_identity():
    broken = deepcopy(load_model_catalog())
    broken["models"]["auto"] = deepcopy(broken["models"]["composer-2.5"])
    broken["review_candidates"]["composer-2.5"]["model_id"] = "auto"
    with pytest.raises(ModelCatalogError, match="concrete Cursor model id"):
        validate_catalog(broken)


def test_catalog_rejects_hermes_for_gpt_or_grok_even_if_model_lists_it():
    broken = deepcopy(load_model_catalog())
    broken["models"]["grok-4.5"]["transports"].append("hermes")
    with pytest.raises(ModelCatalogError, match="must not route"):
        validate_catalog(broken)


def test_catalog_enforces_quality_floor_and_homogeneous_rungs():
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["high"][0].append("deepseek-v4-flash")
    with pytest.raises(ModelCatalogError, match="mixes quality tiers"):
        validate_catalog(broken)


def test_catalog_rejects_refresh_window_over_30_days():
    broken = deepcopy(load_model_catalog())
    broken["refresh_after_days"] = 31
    with pytest.raises(ModelCatalogError, match="1 through 30"):
        validate_catalog(broken)


def test_catalog_validation_does_not_mutate_input():
    raw = deepcopy(load_model_catalog())
    raw["reviewed_on"] = date(2026, 7, 17)
    validate_catalog(raw)
    assert raw["reviewed_on"] == date(2026, 7, 17)


def test_catalog_rejects_future_review_date():
    catalog = deepcopy(load_model_catalog())
    catalog["reviewed_on"] = "2026-07-18"
    validated = validate_catalog(catalog)
    with pytest.raises(ModelCatalogError, match="future"):
        catalog_age_days(validated, as_of=date(2026, 7, 17))
