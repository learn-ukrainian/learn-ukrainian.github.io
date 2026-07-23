"""Contract tests for the canonical, freshness-gated fleet model catalog."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from scripts.agent_runtime.registry import AGENTS
from scripts.review.model_catalog import (
    VALID_REVIEW_PROFILES,
    ModelCatalogError,
    catalog_age_days,
    catalog_is_stale,
    kimi_model_aliases,
    load_model_catalog,
    resolve_kimi_model,
    validate_catalog,
    validate_kimi_alias_consumers,
)


def test_committed_catalog_is_structurally_valid_and_current():
    catalog = load_model_catalog()
    assert catalog["schema_version"] == "model-catalog.v1"
    assert catalog["reviewed_on"] == "2026-07-21"
    assert catalog_age_days(catalog, as_of=date(2026, 7, 21)) == 0
    assert not catalog_is_stale(catalog, as_of=date(2026, 8, 20))
    assert catalog_is_stale(catalog, as_of=date(2026, 8, 21))


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
        "gemini-3.6-flash-high",
        "gemini-3.5-flash-high",
        "grok-4.5",
        "kimi-code/k3",
        "glm-5.2",
        "deepseek-v4-pro",
        "deepseek-v4-flash",
        "poolside/laguna-s-2.1",
        "poolside/laguna-xs-2.1",
        "poolside/laguna-m.1",
        "composer-2.5",
    }
    assert required <= set(models)
    assert models["poolside/laguna-s-2.1"]["lifecycle"] == "active"
    assert models["poolside/laguna-xs-2.1"]["lifecycle"] == "active"
    assert models["poolside/laguna-m.1"]["lifecycle"] == "fallback"
    assert "pool" in models["poolside/laguna-s-2.1"].get("aliases", [])


def test_kimi_aliases_and_routes_are_catalog_backed() -> None:
    aliases = kimi_model_aliases()
    expected = {
        "k3": "kimi-code/k3",
        "kimi-k3": "kimi-code/k3",
        "kimi-k3[1m]": "kimi-code/k3",
        "k2.7": "kimi-code/kimi-for-coding",
        "k2.7-coding": "kimi-code/kimi-for-coding",
        "kimi-for-coding": "kimi-code/kimi-for-coding",
        "kimi-k2.7-code": "kimi-code/kimi-for-coding",
        "k2.7-highspeed": "kimi-code/kimi-for-coding-highspeed",
        "k2.7-coding-highspeed": "kimi-code/kimi-for-coding-highspeed",
        "kimi-for-coding-highspeed": "kimi-code/kimi-for-coding-highspeed",
        "kimi-k2.7-code-highspeed": "kimi-code/kimi-for-coding-highspeed",
    }
    assert expected.items() <= aliases.items()
    model_id, routes = resolve_kimi_model("kimi-k3[1m]")
    assert model_id == "kimi-code/k3"
    assert routes == {
        "kimicc_alias": "k3",
        "platform_model_id": "kimi-k3[1m]",
        "coding_model_id": "k3",
        "context_profile": "kimicc_k3",
    }
    validate_kimi_alias_consumers()


def test_catalog_rejects_kimi_route_without_its_friendly_alias():
    broken = deepcopy(load_model_catalog())
    broken["models"]["kimi-code/k3"]["aliases"].remove("k3")
    with pytest.raises(ModelCatalogError, match="kimicc_alias must be listed"):
        validate_catalog(broken)


def test_kimi_alias_lint_rejects_a_reintroduced_local_adapter_map(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    (project_root / "scripts" / "agent_runtime" / "adapters").mkdir(parents=True)
    for relative_path in ("start-kimi.sh", "start-kimicc.sh", "scripts/agent_runtime/adapters/kimi.py"):
        source = (Path(__file__).resolve().parents[1] / relative_path).read_text(encoding="utf-8")
        destination = project_root / relative_path
        destination.write_text(source, encoding="utf-8")
    adapter_path = project_root / "scripts" / "agent_runtime" / "adapters" / "kimi.py"
    adapter_path.write_text(
        adapter_path.read_text(encoding="utf-8").replace("kimi_model_aliases()", "{}", 1),
        encoding="utf-8",
    )

    with pytest.raises(ModelCatalogError, match=r"must resolve Kimi aliases through model_catalog\.yaml"):
        validate_kimi_alias_consumers(project_root)


def test_poolside_laguna_family_exact_ids_and_roles():
    """Vendor IDs are laguna-{s,xs}-2.1 and laguna-m.1 — not s2/m2 orthography."""
    catalog = load_model_catalog()
    models = catalog["models"]
    candidates = catalog["review_candidates"]
    assert set(models) >= {
        "poolside/laguna-s-2.1",
        "poolside/laguna-xs-2.1",
        "poolside/laguna-m.1",
    }
    assert candidates["pool"]["model_id"] == "poolside/laguna-s-2.1"
    assert candidates["pool-xs"]["model_id"] == "poolside/laguna-xs-2.1"
    # Gen-1 must not be the formal default pin.
    assert catalog["formal_cf_defaults"]["pool"]["model_id"] == "poolside/laguna-s-2.1"
    family = catalog["formal_cf_defaults"]["pool"]["family_models"]
    assert family == [
        "poolside/laguna-s-2.1",
        "poolside/laguna-xs-2.1",
        "poolside/laguna-m.1",
    ]
    # Ladder includes both gen-2 seats.
    for risk in ("high", "medium", "low", "critical"):
        names = {n for rung in catalog["review_ladders"][risk] for n in rung}
        assert "pool" in names
        assert "pool-xs" in names


def test_runtime_registry_defaults_resolve_to_catalog_model_or_alias():
    catalog = load_model_catalog()
    known = set(catalog["models"])
    for model_id, model in catalog["models"].items():
        known.update(model.get("aliases", []))
        known.add(model_id)

    unresolved = {
        agent: entry["default_model"]
        for agent, entry in AGENTS.items()
        if entry["default_model"] not in {None, "auto"} and entry["default_model"] not in known
    }
    assert unresolved == {}


def test_composer_is_conservatively_moonshot_for_independence():
    composer = load_model_catalog()["models"]["composer-2.5"]
    assert composer["family"] == "moonshot"
    assert composer["lab"] == "cursor"


def test_gpt_and_grok_primary_formal_routes_are_native():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["openai_frontier"]["transport"] == "native_codex"
    assert candidates["gpt-5.6-terra"]["transport"] == "native_codex"
    assert candidates["grok-4.5"]["transport"] == "native_grok"
    # Explicit Cursor pin when native grok is dark — never Cursor auto.
    assert candidates["grok-4.5-cursor-fallback"]["transport"] == "cursor"
    assert candidates["grok-4.5-cursor-fallback"]["model_id"] == "grok-4.5"
    assert candidates["grok-4.5-cursor-fallback"]["invocation"].endswith(
        "--agent cursor --model grok-4.5"
    )


def test_fable_routes_native_claude_before_pinned_cursor_fallback():
    catalog = load_model_catalog()
    candidates = catalog["review_candidates"]
    # Authority seats live on the critical ladder only.
    ladder = catalog["review_ladders"]["critical"]

    assert candidates["claude-fable-5"]["transport"] == "native_claude"
    assert candidates["claude-fable-5"]["invocation"].endswith(
        "--agent claude --model claude-fable-5"
    )
    assert candidates["claude-fable-5-cursor-fallback"]["transport"] == "cursor"
    assert candidates["claude-fable-5-cursor-fallback"]["invocation"].endswith(
        "--agent cursor --model claude-fable-5"
    )
    assert ladder.index(["claude-fable-5"]) < ladder.index(
        ["claude-fable-5-cursor-fallback"]
    )


def test_formal_cf_defaults_pin_practical_seats_at_high_effort():
    defaults = load_model_catalog()["formal_cf_defaults"]
    assert defaults["codex"]["model_id"] == "gpt-5.6-terra"
    assert defaults["codex"]["effort"] == "high"
    assert defaults["claude"]["model_id"] == "claude-sonnet-5"
    assert defaults["claude"]["effort"] == "high"
    assert defaults["glm"]["model_id"] == "glm-5.2"
    assert defaults["pool"]["model_id"] == "poolside/laguna-s-2.1"
    assert defaults["grok"]["fallback_transport"] == "cursor"
    assert defaults["grok"]["fallback_model_id"] == "grok-4.5"
    assert defaults["agy"]["model_id"] == "gemini-3.6-flash-high"
    assert defaults["agy"]["effort"] == "high"
    assert defaults["agy"]["formal_review_eligible"] is False


def test_orchestrator_seats_include_agy_flash_36_high():
    seats = load_model_catalog()["orchestrator_seats"]
    assert set(seats) >= {"claude", "grok", "agy"}
    # codex dropped as a DRIVER 2026-07-22 (272K window not worth session rollover
    # overhead); it stays a formal-CF review seat + coding lane, not an orchestrator seat.
    assert "codex" not in seats
    assert seats["agy"]["model_id"] == "gemini-3.6-flash-high"
    assert seats["agy"]["effort"] == "high"
    assert seats["agy"]["escalate_model_id"] == "gemini-3.1-pro-high"
    assert seats["claude"]["model_id"] == "claude-sonnet-5"
    assert seats["grok"]["fallback_model_id"] == "grok-4.5"


def test_orchestrator_escalate_pins_parallel_sol_fable_pro():
    """Each seat has default + escalate like AGY Flash→Pro (user 2026-07-22)."""
    seats = load_model_catalog()["orchestrator_seats"]
    assert seats["claude"]["escalate_model_id"] == "claude-fable-5"
    assert seats["claude"]["escalate_effort"] == "xhigh"
    assert seats["agy"]["escalate_model_id"] == "gemini-3.1-pro-high"
    assert seats["agy"]["escalate_effort"] == "high"
    # codex is no longer an orchestrator seat (dropped 2026-07-22) but remains the
    # formal-CF review seat whose authority escalate is still Sol.
    fc = load_model_catalog()["formal_cf_defaults"]
    assert fc["codex"]["escalate_model_id"] == "gpt-5.6-sol"
    assert fc["claude"]["escalate_model_id"] == "claude-fable-5"


def test_practical_ladders_exclude_authority_seats():
    ladders = load_model_catalog()["review_ladders"]
    for risk in ("high", "medium", "low"):
        names = {name for rung in ladders[risk] for name in rung}
        assert "openai_frontier" not in names
        assert "claude-fable-5" not in names
        assert "claude-opus-4-8" not in names
        assert "gpt-5.6-terra" in names
        assert "claude-sonnet-5" in names
        assert "pool" in names
        assert "grok-4.5-cursor-fallback" in names
    critical = {name for rung in ladders["critical"] for name in rung}
    assert "openai_frontier" in critical
    assert "claude-fable-5" in critical


def test_bridge_only_reviewers_expose_executable_invocations():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["pool"]["invocation"].endswith("ask-pool")
    assert candidates["glm-5.2"]["invocation"].endswith("ask-glm")
    assert candidates["gemini-3.1-pro"]["health_keys"] == ["gemini"]


def test_formal_review_candidates_declare_supported_profiles_and_concrete_cursor_model():
    candidates = load_model_catalog()["review_candidates"]
    assert {"code", "infra"} == VALID_REVIEW_PROFILES
    assert all(set(candidate["review_profiles"]) == VALID_REVIEW_PROFILES for candidate in candidates.values())
    assert candidates["composer-2.5"]["model_id"] == "composer-2.5"


def test_catalog_rejects_learner_content_as_a_code_closeout_profile():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["openai_frontier"]["review_profiles"].append("content")
    with pytest.raises(ModelCatalogError, match="unsupported code-closeout profiles"):
        validate_catalog(broken)


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
