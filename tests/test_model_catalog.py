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
    glm_model_aliases,
    kimi_model_aliases,
    load_model_catalog,
    model_aliases,
    resolve_glm_model,
    resolve_kimi_model,
    validate_catalog,
    validate_glm_alias_consumers,
    validate_kimi_alias_consumers,
)


def test_committed_catalog_is_structurally_valid_and_current():
    catalog = load_model_catalog()
    assert catalog["schema_version"] == "model-catalog.v1"
    assert catalog["reviewed_on"] == "2026-08-16"
    assert catalog_age_days(catalog, as_of=date(2026, 8, 16)) == 0
    assert not catalog_is_stale(catalog, as_of=date(2026, 9, 14))
    assert catalog_is_stale(catalog, as_of=date(2026, 9, 16))


def test_catalog_covers_current_preferred_frontier_and_efficient_models():
    models = load_model_catalog()["models"]
    required = {
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "claude-fable-5",
        "claude-opus-5",
        "claude-sonnet-5",
        "gemini-3.1-pro-high",
        "gemini-3.7-flash-high",
        "gemini-3.6-flash-high",
        "gemini-3.5-flash-high",
        "grok-4.6",
        "kimi-code/k3",
        "kimi-k3-max",
        "glm-5.3",
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


def test_luna_worker_does_not_enter_formal_review_ladders() -> None:
    """Same-family bounded execution must never become its own formal gate."""
    catalog = load_model_catalog()
    assert "gpt-5.6-luna" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        assert "gpt-5.6-luna" not in {candidate for rung in ladder for candidate in rung}


def test_luna_economics_use_model_specific_openai_sources() -> None:
    sources = set(load_model_catalog()["models"]["gpt-5.6-luna"]["sources"])
    assert {
        "https://developers.openai.com/api/docs/models/gpt-5.6-luna",
        "https://developers.openai.com/api/docs/models/gpt-5.6-terra",
    } <= sources


def test_kimi_k3_and_glm_5_2_remain_on_every_code_review_ladder() -> None:
    """The two operator-requested cross-family seats must not silently disappear."""
    for ladder in load_model_catalog()["review_ladders"].values():
        candidates = {candidate for rung in ladder for candidate in rung}
        assert {"kimi-k3", "glm-5.3"} <= candidates


def test_deepseek_v4_flash_high_is_a_practical_code_seat_without_critical_priority() -> None:
    catalog = load_model_catalog()
    flash = catalog["models"]["deepseek-v4-flash"]
    candidate = catalog["review_candidates"]["deepseek-v4-flash"]

    assert flash["tier"] == "frontier_practical"
    assert {"frontend_agentic_coding", "strong_code_review"} <= set(flash["roles"])
    assert "not_critical_authority" in flash["weaknesses"]
    assert "https://arena.ai/leaderboard/code" in flash["sources"]
    assert candidate["transport"] == "opencode"
    assert candidate["invocation"].endswith(
        "opencode run --model deepseek-direct/deepseek-v4-flash --variant high"
    )

    practical = [rung[0] for rung in catalog["review_ladders"]["high"] if len(rung) == 1]
    assert practical.index("glm-5.3") < practical.index("deepseek-v4-flash")
    # Operator 2026-08-13: Pro hold lifted for hard implement only; Flash stays
    # the only DeepSeek review-ladder rung (volume) — Pro never joins ladders.
    assert "deepseek-v4-flash" in practical
    assert "deepseek-v4-pro" not in practical

    critical = [rung[0] for rung in catalog["review_ladders"]["critical"] if len(rung) == 1]
    assert "deepseek-v4-flash" in critical
    assert "deepseek-v4-pro" not in critical
    # Pro is an active hard-implement seat (complex multi-file, hard lookup) —
    # not the default, not a routine review rung (operator GO 2026-08-13, canary #6703).
    pro = catalog["models"]["deepseek-v4-pro"]
    assert pro["lifecycle"] == "active"
    assert "temporary_operator_hold_prefer_flash" not in pro["weaknesses"]
    assert {"hard_implement", "complex_coding"} <= set(pro["roles"])
    pro_candidate = catalog["review_candidates"]["deepseek-v4-pro"]
    assert pro_candidate["transport"] == "opencode"
    assert pro_candidate["invocation"].endswith(
        "opencode run --model deepseek-direct/deepseek-v4-pro --variant high"
    )


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


def test_generic_model_aliases_resolve_k3_256k_and_kimicc_endpoint_lists_it() -> None:
    """The transport-agnostic alias map must resolve every Kimi alias, including 256k."""
    aliases = model_aliases()
    assert aliases["kimi-code/k3-256k"] == "kimi-code/k3-256k"
    assert aliases["k3-256k"] == "kimi-code/k3-256k"
    assert aliases["kimi-k3-256k"] == "kimi-code/k3-256k"
    endpoints = load_model_catalog()["review_scheduler"]["endpoints"]
    assert "kimi-code/k3-256k" in endpoints["kimicc"]["models"]


def test_glm_model_aliases_and_consumer_lint() -> None:
    aliases = glm_model_aliases()
    assert "glm-5.3" in aliases
    assert aliases["glm-5.3"] == "glm-5.3"
    assert aliases["glm52"] == "glm-5.2"  # prior pin
    assert aliases["glm53"] == "glm-5.3"
    assert aliases["glm"] == "glm-5.3"

    model_id, routes = resolve_glm_model("glm")
    assert model_id == "glm-5.3"
    assert routes == {
        "glmcc_alias": "glm-5.3",
        "platform_model_id": "glm-5.3",
        "coding_model_id": "glm-5.3",
        "context_profile": "glmcc_glm53",
    }
    validate_glm_alias_consumers()


def test_catalog_rejects_kimi_route_without_its_friendly_alias():
    broken = deepcopy(load_model_catalog())
    broken["models"]["kimi-code/k3"]["aliases"].remove("k3")
    with pytest.raises(ModelCatalogError, match="kimicc_alias must be listed"):
        validate_catalog(broken)


def test_kimi_alias_lint_rejects_a_reintroduced_local_adapter_map(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    (project_root / "scripts" / "agent_runtime" / "adapters").mkdir(parents=True)
    for relative_path in (
        "scripts/launchers/kimi.sh",
        "scripts/lib/kimicc_route.sh",
        "scripts/agent_runtime/adapters/kimi.py",
    ):
        source = (Path(__file__).resolve().parents[1] / relative_path).read_text(encoding="utf-8")
        destination = project_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
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
    assert candidates["grok-4.6"]["transport"] == "native_grok"
    # Explicit Cursor pin when native grok is dark — never Cursor auto.
    assert candidates["grok-4.6-cursor-fallback"]["transport"] == "cursor"
    assert candidates["grok-4.6-cursor-fallback"]["model_id"] == "grok-4.6"
    assert candidates["grok-4.6-cursor-fallback"]["invocation"].endswith(
        "--agent cursor --model grok-4.6"
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
    assert set(defaults["claude"].get("family_models", [])) >= {
        "claude-sonnet-5",
        "claude-fable-5",
        "claude-opus-5",
        "claude-opus-4-8",
    }
    assert defaults["glm"]["model_id"] == "glm-5.3"
    assert defaults["glm"]["effort"] == "high"
    assert defaults["glm"]["escalate_effort"] == "max"
    assert defaults["glm"]["escalate_model_id"] == "glm-5.3"
    assert defaults["pool"]["model_id"] == "poolside/laguna-s-2.1"
    assert defaults["grok"]["fallback_transport"] == "cursor"
    assert defaults["grok"]["fallback_model_id"] == "grok-4.6"
    assert defaults["agy"]["model_id"] == "gemini-3.7-flash-high"
    assert defaults["agy"]["effort"] == "high"
    assert defaults["agy"]["formal_review_eligible"] is False


def test_orchestrator_seats_include_agy_flash_37_high():
    seats = load_model_catalog()["orchestrator_seats"]
    assert set(seats) >= {"claude", "grok", "agy", "codex", "cursor"}
    # codex was dropped as a DRIVER 2026-07-22 (272K window not worth session rollover
    # overhead), then re-added 2026-07-23 as the named harness/infra/devops alternate:
    # HydrationCapsuleV1's score-from-memory + ~100ms capsule hydrate changed that
    # calculus. It remains a formal-CF review seat + coding lane too.
    assert seats["codex"]["model_id"] == "gpt-5.6-terra"
    assert seats["codex"]["effort"] == "high"
    assert seats["codex"]["escalate_model_id"] == "gpt-5.6-sol"
    assert seats["agy"]["model_id"] == "gemini-3.7-flash-high"
    assert seats["agy"]["effort"] == "high"
    assert seats["agy"]["escalate_model_id"] == "gemini-3.1-pro-high"
    assert seats["claude"]["model_id"] == "claude-fable-5"
    assert seats["grok"]["fallback_model_id"] == "grok-4.6"
    assert seats["cursor"]["model_id"] == "auto"
    assert seats["cursor"]["effort"] == "high"
    assert seats["cursor"]["escalate_model_id"] == "gpt-5.6-sol"
    assert seats["cursor"]["escalate_effort"] == "xhigh"
    assert seats["cursor"]["auto_allowlist"] == ["grok-4.6", "composer-2.5"]
    assert seats["cursor"]["attestation_rule"] == "driver_of_record_requires_attested_resolved_model"
    assert seats["cursor"]["unknown_auto_family_resolution"] == "union_family"
    assert seats["cursor"]["unknown_auto_union_families"] == ["xai", "moonshot"]


def test_orchestrator_escalate_pins_parallel_sol_fable_pro():
    """Each seat has default + escalate like AGY Flash→Pro (user 2026-07-22)."""
    seats = load_model_catalog()["orchestrator_seats"]
    assert seats["claude"]["escalate_model_id"] == "gpt-5.6-sol"
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
        assert "grok-4.6-cursor-fallback" in names
    critical = {name for rung in ladders["critical"] for name in rung}
    assert "openai_frontier" in critical
    assert "claude-fable-5" in critical


def test_bridge_only_reviewers_expose_executable_invocations():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["pool"]["invocation"].endswith("ask-pool")
    assert candidates["glm-5.3"]["invocation"].endswith("ask-glm")
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
    broken["review_candidates"]["grok-4.6"]["transport"] = "hermes"
    with pytest.raises(ModelCatalogError, match="is not listed"):
        validate_catalog(broken)


def test_catalog_rejects_bare_cursor_model_identity():
    broken = deepcopy(load_model_catalog())
    broken["models"]["auto"] = deepcopy(broken["models"]["composer-2.5"])
    broken["review_candidates"]["composer-2.5"]["model_id"] = "auto"
    with pytest.raises(ModelCatalogError, match="concrete Cursor model id"):
        validate_catalog(broken)


def test_catalog_rejects_cursor_orchestrator_without_allowlist():
    broken = deepcopy(load_model_catalog())
    del broken["orchestrator_seats"]["cursor"]["auto_allowlist"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.auto_allowlist"):
        validate_catalog(broken)


def test_catalog_rejects_cursor_orchestrator_with_unknown_or_retired_allowlist_model():
    broken = deepcopy(load_model_catalog())
    broken["orchestrator_seats"]["cursor"]["auto_allowlist"].append("unknown-model")
    with pytest.raises(ModelCatalogError, match=r"unknown model 'unknown-model'"):
        validate_catalog(broken)

    broken_retired = deepcopy(load_model_catalog())
    broken_retired["orchestrator_seats"]["cursor"]["auto_allowlist"].append("grok-4.5")
    with pytest.raises(ModelCatalogError, match=r"must reference active models, got 'grok-4\.5'"):
        validate_catalog(broken_retired)


def test_catalog_rejects_cursor_orchestrator_without_attestation_rule():
    broken = deepcopy(load_model_catalog())
    del broken["orchestrator_seats"]["cursor"]["attestation_rule"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.attestation_rule"):
        validate_catalog(broken)


def test_cursor_orchestrator_unknown_auto_resolves_to_union_family():
    catalog = load_model_catalog()
    cursor_seat = catalog["orchestrator_seats"]["cursor"]
    assert cursor_seat["unknown_auto_family_resolution"] == "union_family"
    assert cursor_seat["unknown_auto_union_families"] == ["xai", "moonshot"]
    assert cursor_seat["auto_allowlist"] == ["grok-4.6", "composer-2.5"]
    models = catalog["models"]
    assert models["grok-4.6"]["family"] == "xai"
    assert models["composer-2.5"]["family"] == "moonshot"

    # Reject missing unknown_auto_family_resolution
    broken_missing_res = deepcopy(catalog)
    del broken_missing_res["orchestrator_seats"]["cursor"]["unknown_auto_family_resolution"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_family_resolution"):
        validate_catalog(broken_missing_res)

    # Reject invalid unknown_auto_family_resolution
    broken_invalid_res = deepcopy(catalog)
    broken_invalid_res["orchestrator_seats"]["cursor"]["unknown_auto_family_resolution"] = "single_family"
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_family_resolution must be 'union_family'"):
        validate_catalog(broken_invalid_res)

    # Reject missing unknown_auto_union_families
    broken_missing_fams = deepcopy(catalog)
    del broken_missing_fams["orchestrator_seats"]["cursor"]["unknown_auto_union_families"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_union_families"):
        validate_catalog(broken_missing_fams)

    # Reject mismatched unknown_auto_union_families (e.g. wrong family or missing family)
    broken_mismatched_fams = deepcopy(catalog)
    broken_mismatched_fams["orchestrator_seats"]["cursor"]["unknown_auto_union_families"] = ["openai", "moonshot"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_union_families must match allowlist model families"):
        validate_catalog(broken_mismatched_fams)


def test_catalog_rejects_cursor_orchestrator_non_auto_model_id():
    broken = deepcopy(load_model_catalog())
    broken["orchestrator_seats"]["cursor"]["model_id"] = "composer-2.5"
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.model_id must be 'auto'"):
        validate_catalog(broken)


def test_catalog_rejects_cursor_auto_as_formal_review_identity():
    # In review_scheduler.endpoints
    broken_ep = deepcopy(load_model_catalog())
    broken_ep["review_scheduler"]["endpoints"]["cursor"]["formal_review_eligible"] = True
    with pytest.raises(ModelCatalogError, match=r"review_scheduler\.endpoints\.cursor must remain formal_review_eligible: false"):
        validate_catalog(broken_ep)

    broken_ep_models = deepcopy(load_model_catalog())
    broken_ep_models["review_scheduler"]["endpoints"]["cursor"]["models"] = ["auto"]
    with pytest.raises(ModelCatalogError, match=r"cannot treat 'auto' as a formal review identity"):
        validate_catalog(broken_ep_models)

    # In formal_cf_defaults
    broken_cf = deepcopy(load_model_catalog())
    broken_cf["formal_cf_defaults"]["cursor"] = {"model_id": "auto", "effort": "high"}
    with pytest.raises(ModelCatalogError, match=r"cannot use 'auto' as formal CF default"):
        validate_catalog(broken_cf)

    # In review_candidates (cursor transport)
    broken_rc = deepcopy(load_model_catalog())
    broken_rc["review_candidates"]["cursor-auto"] = {
        "model_id": "auto",
        "route": "cursor",
        "transport": "cursor",
        "invocation": ".venv/bin/python scripts/delegate.py dispatch --agent cursor",
        "review_profiles": ["code", "infra"],
        "capabilities": ["code_review"],
    }
    with pytest.raises(ModelCatalogError, match=r"requires a concrete Cursor model id, not 'auto'"):
        validate_catalog(broken_rc)

    # In review_candidates (generic transport)
    broken_rc_gen = deepcopy(load_model_catalog())
    broken_rc_gen["review_candidates"]["grok-auto"] = {
        "model_id": "auto",
        "route": "grok",
        "transport": "native_grok",
        "invocation": ".venv/bin/python scripts/delegate.py dispatch --agent grok",
        "review_profiles": ["code", "infra"],
        "capabilities": ["code_review"],
    }
    with pytest.raises(ModelCatalogError, match=r"cannot use 'auto' as a formal review candidate"):
        validate_catalog(broken_rc_gen)


def test_catalog_rejects_hermes_for_gpt_or_grok_even_if_model_lists_it():
    broken = deepcopy(load_model_catalog())
    broken["models"]["grok-4.6"]["transports"].append("hermes")
    with pytest.raises(ModelCatalogError, match="must not route"):
        validate_catalog(broken)


def test_catalog_enforces_quality_floor_and_homogeneous_rungs():
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["high"][0].append("pool-xs")
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


def test_critical_ladder_anthropic_authority_is_fable_not_opus():
    """Advisory consultation must not silently become approval authority.

    The critical authority ladder routes Anthropic approval reviews to Fable.
    Opus remains the separate, non-binding advisory-consultation seat.
    """
    ladder = load_model_catalog()["review_ladders"]["critical"]
    flat = [model for rung in ladder for model in rung]
    assert "claude-fable-5" in flat
    assert "claude-opus-5" not in flat
    assert flat.index("claude-fable-5") < flat.index("claude-sonnet-5")


def test_opus_advisory_capability_does_not_grant_orchestration() -> None:
    """Model capability metadata must preserve the routing/authority boundary."""
    roles = set(load_model_catalog()["models"]["claude-opus-5"]["roles"])
    assert "advisory_consultation" in roles
    assert "orchestration" not in roles


def test_sol_advised_luna_execution_route_is_bounded_and_machine_readable():
    """The Sol→Luna lane must be explicit, bounded, and source-blind testable."""
    catalog = load_model_catalog()
    route = catalog["execution_routing"]["sol_advised_bounded"]

    advisor = route["advisor"]
    assert advisor["model_id"] == "gpt-5.6-sol"
    assert advisor["effort"] == "high"
    assert "bounded_advisory_envelope" in catalog["models"][advisor["model_id"]]["roles"]
    assert advisor["output_fields"] == [
        "task_contract",
        "owned_paths",
        "max_changed_files",
        "max_non_test_loc",
        "constraints",
        "risk_boundaries",
        "acceptance_evidence",
        "escalation_triggers",
    ]

    preferred = route["preferred_worker"]
    assert preferred["model_id"] == "gpt-5.6-luna"
    assert preferred["effort"] == "max"
    assert {
        "bounded_implementation",
        "bounded_investigation",
    } <= set(catalog["models"][preferred["model_id"]]["roles"])
    assert preferred["requires"] == ["complete_advisory_envelope", "objective_scope_ceiling"]
    assert preferred["task_types"] == ["bounded_implementation", "bounded_investigation"]
    assert preferred["escalate_to"] == "gpt-5.6-sol"
    assert set(preferred["prohibited_decisions"]) == {
        "consequential_architecture",
        "security",
        "release",
        "high_risk_go_no_go",
    }
    assert set(preferred["escalation_triggers"]) == {
        "scope_ceiling_exceeded",
        "unresolved_consequential_ambiguity",
        "broader_integration",
        "final_disposition",
    }

    direct = route["direct_worker"]
    assert direct == {
        "model_id": "gpt-5.6-luna",
        "effort": "max",
        "task_types": [
            "bounded_implementation",
            "bounded_investigation",
            "recon",
            "bounded_checks",
            "log_triage",
        ],
        "constraints": [
            "objective_scope_ceiling",
            "no_consequential_decisions",
            "no_final_disposition",
        ],
    }
    assert route["autonomous_fallback"] == {
        "model_id": "gpt-5.6-terra",
        "effort": "high",
        "when": [
            "missing_objective_scope_ceiling",
            "broader_autonomous_integration",
            "unresolved_consequential_ambiguity",
        ],
    }

    models = catalog["models"]
    assert models[advisor["model_id"]]["family"] == "openai"
    assert models[preferred["model_id"]]["family"] == "openai"
    assert route["review_boundary"] == {
        "advisory_family": "openai",
        "advisory_satisfies_cross_family_review": False,
        "independent_cross_family_review_required": True,
    }


@pytest.mark.parametrize(
    ("field", "member"),
    [
        ("task_types", "bounded_investigation"),
        ("prohibited_decisions", "security"),
        ("escalation_triggers", "final_disposition"),
    ],
)
def test_catalog_rejects_luna_safety_set_member_removal(field, member):
    broken = deepcopy(load_model_catalog())
    broken["execution_routing"]["sol_advised_bounded"]["preferred_worker"][field].remove(member)

    with pytest.raises(ModelCatalogError, match=rf"preferred_worker\.{field} must include exactly"):
        validate_catalog(broken)


@pytest.mark.parametrize(
    ("section", "field", "operation", "value", "message"),
    [
        ("advisor", "model_id", "set", "missing-model", "advisor.model_id references unknown model"),
        ("preferred_worker", "model_id", "set", "poolside/laguna-m.1", "preferred_worker.model_id must reference an active model"),
        ("direct_worker", "model_id", "set", "missing-model", "direct_worker.model_id references unknown model"),
        ("autonomous_fallback", "model_id", "set", "missing-model", "autonomous_fallback.model_id references unknown model"),
        ("preferred_worker", "escalate_to", "set", "missing-model", "preferred_worker.escalate_to references unknown model"),
        ("advisor", "effort", "set", "ultra", "advisor.effort must be one of"),
        ("preferred_worker", "effort", "set", "ultra", "preferred_worker.effort must be one of"),
        ("direct_worker", "effort", "set", "ultra", "direct_worker.effort must be one of"),
        ("autonomous_fallback", "effort", "set", "ultra", "autonomous_fallback.effort must be one of"),
        ("advisor", "role", "set", "unbounded", "advisor.role must be"),
        (
            "advisor",
            "output_fields",
            "set",
            ["task_contract", "constraints", "risk_boundaries", "acceptance_evidence", "escalation_triggers"],
            "output_fields must be exactly",
        ),
        ("advisor", "output_fields", "delete", None, "advisor must define exactly"),
        (
            "preferred_worker",
            "requires",
            "set",
            ["complete_advisory_envelope"],
            "requires must bind",
        ),
        (
            "preferred_worker",
            "escalation_triggers",
            "set",
            ["unresolved_consequential_ambiguity", "broader_integration", "final_disposition"],
            "must include",
        ),
        ("preferred_worker", "prohibited_decisions", "delete", None, "preferred_worker must define exactly"),
        ("review_boundary", "advisory_family", "set", "anthropic", "must match the advisor model family"),
        ("review_boundary", "advisory_satisfies_cross_family_review", "set", True, "must remain false"),
        ("review_boundary", "independent_cross_family_review_required", "set", False, "must remain true"),
    ],
)
def test_catalog_rejects_malformed_sol_advised_route(
    section, field, operation, value, message
):
    broken = deepcopy(load_model_catalog())
    target = broken["execution_routing"]["sol_advised_bounded"][section]
    if operation == "delete":
        del target[field]
    else:
        target[field] = value

    with pytest.raises(ModelCatalogError, match=message):
        validate_catalog(broken)
