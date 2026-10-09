"""Contract tests for the canonical, freshness-gated fleet model catalog."""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from scripts.agent_runtime.registry import AGENTS
from scripts.audit import model_families
from scripts.review.model_catalog import (
    VALID_REVIEW_PROFILES,
    ModelCatalogError,
    bounded_execution_policy,
    canonical_model_id,
    catalog_age_days,
    catalog_is_stale,
    cursor_non_dispatch_model_refusal,
    cursor_pinned_models,
    glm_model_aliases,
    is_cursor_auto_selector,
    kimi_model_aliases,
    load_model_catalog,
    model_aliases,
    require_execution_model,
    resolve_catalog_model_id,
    resolve_glm_model,
    resolve_kimi_model,
    retired_model_refusal,
    risk_reviewer_refusal,
    runtime_model_matches_requested,
    validate_catalog,
    validate_glm_alias_consumers,
    validate_kimi_alias_consumers,
)


def test_committed_catalog_is_structurally_valid_and_current():
    catalog = load_model_catalog()
    assert catalog["schema_version"] == "model-catalog.v1"
    assert catalog["reviewed_on"] == "2026-09-24"
    assert catalog_age_days(catalog, as_of=date(2026, 9, 24)) == 0
    assert not catalog_is_stale(catalog, as_of=date(2026, 10, 23))
    assert catalog_is_stale(catalog, as_of=date(2026, 10, 25))


@pytest.mark.parametrize("value", [None, "grok-4.7-build", [], [""], [" "], [1], ["grok-4.7-build", None]])
def test_runtime_model_ids_require_nonempty_strings(value):
    catalog = deepcopy(load_model_catalog())
    catalog["models"]["grok-4.7"]["runtime_model_ids"] = value
    with pytest.raises(ModelCatalogError, match="runtime_model_ids"):
        validate_catalog(catalog)


@pytest.mark.parametrize("runtime", ["grok-4.7-build-fast", "grok-4.7-build-FAST", "grok-4.7-fast-high", "grok-4.7_build_fast"])
def test_review_runtime_model_ids_reject_fast_variants(runtime):
    catalog = deepcopy(load_model_catalog())
    catalog["models"]["grok-4.7"]["runtime_model_ids"] = [runtime]
    with pytest.raises(ModelCatalogError, match="must not admit fast review variants"):
        validate_catalog(catalog)


@pytest.mark.parametrize("requested,runtime,expected", [
    ("grok-4.7", "grok-4.7-build", True),
    ("grok-4.7-high", "grok-4.7-build", True),
    ("grok-4.7", "grok-4.7", True),
    ("grok-4.7", "grok-4.7-build-fast", False),
    ("grok-4.7", "grok-4.6", False),
    ("grok-4.7", "grok-4.7-build-extra", False),
    ("unknown", "grok-4.7-build", False),
    ("gpt-6.1-sol", "grok-4.7-build", False),
])
def test_runtime_substitution_matches_only_requested_model_ids(requested, runtime, expected):
    assert runtime_model_matches_requested(requested, runtime) is expected


@pytest.mark.parametrize("roles", [[], ["not-a-role"], ["standard_review"]])
def test_candidate_suitability_roles_must_be_nonempty_and_held(roles):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["grok-4.7"]["suitability_roles"] = roles
    with pytest.raises(ModelCatalogError, match="suitability_roles"):
        validate_catalog(catalog)


@pytest.mark.parametrize("primary", ["unknown", "openai_frontier", "grok-4.7-cursor-fallback"])
def test_transport_fallback_must_reference_primary_of_same_model(primary):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["grok-4.7-cursor-fallback"]["transport_fallback_for"] = primary
    with pytest.raises(ModelCatalogError, match="transport_fallback_for"):
        validate_catalog(catalog)


@pytest.mark.parametrize("model_id", [
    model_id for model_id, entry in load_model_catalog()["models"].items()
    if entry["lifecycle"] == "retired"
])
def test_retired_models_cannot_retain_any_transport(model_id):
    catalog = deepcopy(load_model_catalog())
    catalog["models"][model_id]["transports"] = ["native_grok"]
    with pytest.raises(ModelCatalogError, match="transports must be empty for retired models"):
        validate_catalog(catalog)


@pytest.mark.parametrize(("model", "transport", "message"), [
    ("cursor:grok-4.5-high", "cursor", "is retired"),
    ("claude-opus-4.6", "native_claude", "not in the model catalog"),
    ("claude-opus-5-5", "hermes", "no admitted hermes transport"),
    ("gemini-3.8-flash-high", "native_gemini", "no admitted native_gemini transport"),
])
def test_execution_defaults_refused_by_catalog_identity_and_transport(model, transport, message):
    with pytest.raises(ModelCatalogError, match=message):
        require_execution_model(model, transport=transport)


def test_execution_default_resolves_active_alias_and_rejects_hold():
    catalog = deepcopy(load_model_catalog())
    assert require_execution_model("gemini-3.8-flash-low", transport="agy", catalog=catalog) == "gemini-3.8-flash-high"
    catalog["models"]["gemini-3.8-flash-high"]["lifecycle"] = "hold"
    with pytest.raises(ModelCatalogError, match="not admitted for execution"):
        require_execution_model("gemini-3.8-flash-low", transport="agy", catalog=catalog)


def test_catalog_covers_current_preferred_frontier_and_efficient_models():
    models = load_model_catalog()["models"]
    required = {
        "gpt-6.1-sol",
        "gpt-6-luna",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "claude-fable-5",
        "claude-fable-5-1",
        "claude-opus-5-5",
        "claude-opus-5",
        "claude-sonnet-5",
        "claude-sonnet-5-5",
        "gemini-3.1-pro-high",
        "gemini-3.8-flash-high",
        "gemini-3.7-flash-high",
        "gemini-3.6-flash-high",
        "gemini-3.5-flash-high",
        "grok-4.7",
        "grok-4.6",
        "kimi-code/k3",
        "kimi-k3-max",
        "glm-5.3",
        "deepseek-v4-pro",
        "deepseek-v4.1-flash",
        "poolside/laguna-s-2.1",
        "poolside/laguna-xs-2.1",
        "poolside/laguna-m.1",
        "composer-2.5",
    }
    assert required <= set(models)
    assert models["claude-sonnet-5-5"]["lifecycle"] == "active"
    assert models["claude-sonnet-5"]["lifecycle"] == "retired"
    for risk, ladder in load_model_catalog()["review_ladders"].items():
        names = {candidate for rung in ladder for candidate in rung}
        assert ("claude-sonnet-5-5" in names) == (risk in {"medium", "low"})
        assert "claude-sonnet-5" not in names
    assert models["poolside/laguna-s-2.1"]["lifecycle"] == "active"
    assert models["poolside/laguna-xs-2.1"]["lifecycle"] == "active"
    assert models["poolside/laguna-m.1"]["lifecycle"] == "fallback"
    assert "pool" in models["poolside/laguna-s-2.1"].get("aliases", [])


def test_fallback_sonnet_candidate_cannot_reenter_automatic_ladder():
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["medium"][3] = ["claude-sonnet-5"]
    with pytest.raises(ModelCatalogError, match=r"unknown candidate|must reference an active model"):
        validate_catalog(broken)


def test_sonnet_5_5_english_authoring_and_routing_boundaries():
    catalog = load_model_catalog()
    sonnet = catalog["models"]["claude-sonnet-5-5"]
    strengths = set(sonnet["strengths"])
    assert "document_authoring" in sonnet["roles"]
    assert {"polished_english_documents_slides_spreadsheets", "design_eye"} <= strengths
    assert {
        "weaker_than_opus_on_complex_open_ended_work",
        "not_for_security_sensitive_code",
        "not_for_ukrainian_curriculum_content",
    } <= set(sonnet["weaknesses"])
    assert "security_review" not in sonnet["roles"]
    assert "polished_documents_slides_spreadsheets" not in strengths
    assert all(route in sonnet["notes"] for route in ("English", "Opus 5.5", "Codex Sol"))
    assert "Fable" not in sonnet["notes"]
    validate_catalog(catalog)


def test_glm_53_flash_is_active_workhorse_catalog_entry() -> None:
    """GLM-5.3-Flash replaces retired ox-alpha as the LOCAL-ONLY workhorse seat."""
    catalog = load_model_catalog()
    assert "openrouter/stealth/ox-alpha" not in catalog["models"]
    flash = catalog["models"]["glm-5.3-flash"]
    assert flash["tier"] == "frontier_practical"
    assert flash["lifecycle"] == "active"
    assert flash["transports"] == ["opencode"]
    assert flash["family"] == "zhipu"
    assert set(flash["aliases"]) == {
        "ox-alpha",
        "0x-alpha",
        "stealth/ox-alpha",
        "openrouter/stealth/ox-alpha",
        "glm53-flash",
    }
    assert "glm-5.3-flash" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        candidates = {candidate for rung in ladder for candidate in rung}
        assert "glm-5.3-flash" not in candidates
    aliases = model_aliases()
    assert aliases["ox-alpha"] == "glm-5.3-flash"
    assert aliases["0x-alpha"] == "glm-5.3-flash"
    assert aliases["stealth/ox-alpha"] == "glm-5.3-flash"
    assert model_families.normalize_family("glm-5.3-flash") is model_families.Family.ZHIPU


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


def test_kimi_is_absent_from_review_candidates_and_every_ladder() -> None:
    """Kimi seats admit web, UI and backend coding only (formerly a rung on every ladder); glm is pin-only."""
    catalog = load_model_catalog()
    assert "kimi-k3" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        candidates = {candidate for rung in ladder for candidate in rung}
        assert "kimi-k3" not in candidates
        assert "glm-5.3" not in candidates


def test_kimi_models_carry_coding_roles_only() -> None:
    """No Kimi model carries a review, consult, advisor, or architecture role."""
    catalog = load_model_catalog()
    kimi_models = {mid: model for mid, model in catalog["models"].items() if "native_kimi" in model["transports"]}
    assert kimi_models
    for model_id, model in kimi_models.items():
        roles = set(model["roles"])
        assert roles, model_id
        assert all(role.endswith(("_coding", "_implementation", "_debugging")) for role in roles), (model_id, roles)
    for endpoint in ("kimi", "kimicc"):
        scheduler = catalog["review_scheduler"]["endpoints"][endpoint]
        assert scheduler["formal_review_eligible"] is False
        assert "web, UI and backend coding only" in scheduler["formal_review_exclusion_reason"]


def test_glm_is_absent_from_automatic_review_ladders() -> None:
    """z.ai retired: glm-5.3 stays catalogued for explicit pins, never auto-rung."""
    catalog = load_model_catalog()
    assert "glm-5.3" in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        assert "glm-5.3" not in {candidate for rung in ladder for candidate in rung}


def test_deepseek_metadata_is_preserved_without_review_seats() -> None:
    catalog = load_model_catalog()
    flash = catalog["models"]["deepseek-v4.1-flash"]

    legacy = catalog["models"]["deepseek-v4-flash"]
    assert legacy["lifecycle"] == "retired"
    assert legacy["transports"] == []
    assert flash["tier"] == legacy["tier"]
    assert model_aliases()["deepseek-v4-flash-legacy"] == "deepseek-v4-flash"
    assert "deepseek-v4-flash" not in catalog["review_candidates"]
    assert flash["lifecycle"] == "active"
    assert flash["provider_alias"] == "deepseek/deepseek-flash"
    assert flash["provider_alias_expected_name"] == "DeepSeek V4.1 Flash"
    assert "models.json" in flash["provider_alias_drift_check"]

    assert flash["tier"] == "frontier_practical"
    assert {"frontend_agentic_coding", "strong_code_review"} <= set(flash["roles"])
    assert "not_critical_authority" in flash["weaknesses"]
    assert "https://arena.ai/leaderboard/code" in flash["sources"]
    # Metadata is retained per #9301's non-goals; it confers no review eligibility.
    for model in ("deepseek-v4.1-flash", "deepseek-v4-pro"):
        assert model not in catalog["review_candidates"]
        for ladder in catalog["review_ladders"].values():
            assert model not in {name for rung in ladder for name in rung}
    pro = catalog["models"]["deepseek-v4-pro"]
    assert pro["lifecycle"] == "retired"
    assert "temporary_operator_hold_prefer_flash" not in pro["weaknesses"]
    assert pro["roles"] == ["historical_record_resolution"]


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


def test_generic_model_aliases_resolve_k3_256k_but_kimicc_does_not_route_it() -> None:
    """k3-256k stays a native alias. The coding endpoint rejects it, so kimicc omits it (#8745)."""
    aliases = model_aliases()
    assert aliases["kimi-code/k3-256k"] == "kimi-code/k3-256k"
    assert aliases["k3-256k"] == "kimi-code/k3-256k"
    assert aliases["kimi-k3-256k"] == "kimi-code/k3-256k"
    endpoints = load_model_catalog()["review_scheduler"]["endpoints"]
    assert "kimi-code/k3-256k" not in endpoints["kimicc"]["models"]
    assert endpoints["kimicc"]["models"][0] == "kimi-code/k3"


def test_every_kimicc_routable_alias_has_coding_model_id() -> None:
    catalog = load_model_catalog()
    endpoint_ids = catalog["review_scheduler"]["endpoints"]["kimicc"]["models"]
    aliases = kimi_model_aliases(catalog)
    assert endpoint_ids
    seen: set[str] = set()
    for model_id in endpoint_ids:
        coding_model_id = catalog["models"][model_id]["kimi_routes"]["coding_model_id"]
        assert isinstance(coding_model_id, str) and coding_model_id.strip()
        for alias, owner in aliases.items():
            if owner != model_id:
                continue
            seen.add(alias)
            _, route = resolve_kimi_model(alias, catalog)
            assert isinstance(route["coding_model_id"], str) and route["coding_model_id"].strip()
    assert "k3-256k" not in seen
    assert "k3" in seen


def test_glm_model_aliases_and_consumer_lint() -> None:
    aliases = glm_model_aliases()
    assert "glm-5.3" in aliases
    assert aliases["glm-5.3"] == "glm-5.3"
    assert "glm52" not in aliases
    assert model_aliases()["glm52"] == "glm-5.2"  # historical identity
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
    # Routine ladders include both gen-2 seats; high/critical admit only Sol, Opus and Grok.
    for risk in ("medium", "low"):
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
    assert "gpt-5.6-terra" not in candidates
    assert candidates["grok-4.7"]["transport"] == "native_grok"
    # #9769: the regular Cursor seat pins the exact runtime-attestable slug, never Auto.
    assert candidates["grok-4.7-cursor-fallback"]["transport"] == "cursor"
    assert candidates["grok-4.7-cursor-fallback"]["model_id"] == "grok-4.7"
    assert candidates["grok-4.7-cursor-fallback"].get("last_resort", False) is False
    assert candidates["grok-4.7-cursor-fallback"]["invocation"].endswith(
        "--agent cursor --model grok-4.7-high"
    )


def test_fable_holds_no_review_or_advisory_role():
    """#9583: Opus 5.5 and Sol 6.1 replace Fable as advisors, approvers and reviewers."""
    catalog = load_model_catalog()
    fable = catalog["models"]["claude-fable-5-1"]
    assert fable["lifecycle"] == "active"
    assert not {"architecture", "critical_review", "consequential_advisory", "bounded_advisory_envelope"} & set(
        fable["roles"]
    )
    assert all(c["model_id"] != "claude-fable-5-1" for c in catalog["review_candidates"].values())
    for risk, ladder in catalog["review_ladders"].items():
        assert not any(name.startswith("claude-fable") for rung in ladder for name in rung), risk
    assert "claude-fable-5-1" not in catalog["review_scheduler"]["endpoints"]["claude"]["models"]
    assert "claude-fable-5-1" not in catalog["formal_cf_defaults"]["claude"]["family_models"]
    # A non-review Cursor dispatch of the launchable model still has an admitted slug.
    assert catalog["budget_substitution_models"]["cursor"]["claude-fable-5-1"] in fable["aliases"]


@pytest.mark.parametrize("model", ["claude-fable-5-1", "claude-fable-5-1[1m]", "claude-fable-5-1-thinking-high"])
@pytest.mark.parametrize("activity", ["review", "consult"])
def test_fable_is_refused_every_review_and_consult_activity(model, activity):
    """#9583: activity admission reads the catalog roles, so every Fable spelling is refused."""
    from scripts.review.model_catalog import activity_role_refusal

    refusal = activity_role_refusal(model, activity)
    assert refusal and "(claude-fable-5-1) holds no" in refusal


@pytest.mark.parametrize("activity", ["review", "consult"])
def test_retired_astra_holds_no_activity_role(activity):
    from scripts.review.model_catalog import activity_role_refusal

    assert "retired in the model catalog" in activity_role_refusal("gpt-6-astra", activity)


@pytest.mark.parametrize("model", ["claude-opus-5-5", "gpt-6.1-sol", "gemini-3.8-flash-high", "claude-sonnet-5-5"])
@pytest.mark.parametrize("activity", ["review", "consult"])
def test_opus_sol_and_reviewers_are_admitted_every_activity(model, activity):
    from scripts.review.model_catalog import activity_role_refusal

    assert activity_role_refusal(model, activity) is None


def test_recon_models_consult_but_never_review():
    from scripts.review.model_catalog import activity_role_refusal

    assert activity_role_refusal("gpt-6-luna", "consult") is None
    assert "holds no review" in activity_role_refusal("gpt-6-luna", "review")


def test_unknown_activity_and_unknown_model():
    from scripts.review.model_catalog import activity_role_refusal

    assert activity_role_refusal("not-a-catalog-model", "review") is None
    with pytest.raises(ValueError, match="unknown activity"):
        activity_role_refusal("claude-opus-5-5", "approve")


@pytest.mark.parametrize(
    "mutate,message",
    [
        (lambda c: c["review_scheduler"].pop("activity_roles"), "activity_roles must be a mapping"),
        (lambda c: c["review_scheduler"]["activity_roles"].pop("consult"), "must define exactly"),
        (lambda c: c["review_scheduler"]["activity_roles"]["review"].append("typo_review"), "which no model holds"),
        (
            lambda c: c["review_candidates"]["claude-opus-5-5"].update(
                model_id="claude-fable-5-1",
                invocation=c["review_candidates"]["claude-opus-5-5"]["invocation"].replace(
                    "claude-opus-5-5", "claude-fable-5-1"
                ),
            ),
            r"review_candidates\.claude-opus-5-5: .*holds no review",
        ),
        (
            lambda c: c["review_scheduler"]["endpoints"]["claude"]["models"].append("claude-fable-5-1"),
            r"endpoints\.claude\.models: .*holds no review",
        ),
        (
            lambda c: c["review_scheduler"]["risk_reviewer_models"]["high"].append("claude-fable-5-1"),
            r"risk_reviewer_models\.high: .*holds no review",
        ),
        (
            lambda c: c["models"]["gpt-6.1-sol"]["roles"].remove("bounded_advisory_envelope"),
            r"advisor\.model_id 'gpt-6\.1-sol' does not hold the 'bounded_advisory_envelope' role",
        ),
    ],
    ids=["missing", "missing-activity", "unheld-role", "candidate", "endpoint", "risk-model", "advisor"],
)
def test_catalog_requires_activity_roles_for_reviewers_and_the_advisor(mutate, message):
    catalog = deepcopy(load_model_catalog())
    mutate(catalog)
    with pytest.raises(ModelCatalogError, match=message):
        validate_catalog(catalog)


def test_formal_cf_defaults_pin_role_specific_efforts():
    defaults = load_model_catalog()["formal_cf_defaults"]
    assert defaults["codex"]["model_id"] == "gpt-6.1-sol"
    assert defaults["codex"]["effort"] == "high"
    assert defaults["claude"]["model_id"] == "claude-sonnet-5-5"
    assert defaults["claude"]["effort"] == "high"
    assert set(defaults["claude"].get("family_models", [])) >= {
        "claude-sonnet-5-5",
        "claude-opus-5-5",
    }
    assert "claude-fable-5-1" not in defaults["claude"]["family_models"]
    assert defaults["glm"]["model_id"] == "glm-5.3"
    assert defaults["glm"]["effort"] == "high"
    assert defaults["glm"]["escalate_effort"] == "max"
    assert defaults["glm"]["escalate_model_id"] == "glm-5.3"
    assert defaults["pool"]["model_id"] == "poolside/laguna-s-2.1"
    assert defaults["grok"]["fallback_transport"] == "cursor"
    assert defaults["grok"]["fallback_model_id"] == "grok-4.7"
    assert defaults["agy"]["model_id"] == "gemini-3.8-flash-high"
    assert defaults["agy"]["effort"] == "high"
    assert defaults["agy"]["formal_review_eligible"] is True


def test_orchestrator_seats_include_agy_flash_38_high():
    seats = load_model_catalog()["orchestrator_seats"]
    assert set(seats) >= {"claude", "grok", "agy", "codex", "cursor"}
    # codex was dropped as a DRIVER 2026-07-22 (272K window not worth session rollover
    # overhead), then re-added 2026-07-23 as the named harness/infra/devops alternate:
    # HydrationCapsuleV1's score-from-memory + bounded capsule hydration changed that
    # calculus. It remains a formal-CF review seat + coding lane too.
    assert seats["codex"]["model_id"] == "gpt-6.1-sol"
    assert seats["codex"]["effort"] == "high"
    assert seats["codex"]["escalate_model_id"] == "gpt-6.1-sol"
    assert seats["agy"]["model_id"] == "gemini-3.8-flash-high"
    assert seats["agy"]["effort"] == "high"
    assert seats["agy"]["escalate_model_id"] == "gemini-3.8-flash-high"
    # Operator 2026-09-22: Opus 5.5 drives; #9583: Opus 5.5 and Sol 6.1 are the advisors.
    assert seats["claude"]["model_id"] == "claude-opus-5-5"
    assert seats["claude"]["effort"] == "high"
    assert seats["grok"]["fallback_model_id"] == "grok-4.7"
    # Operator decision 2026-09-30 (#9274): the seat runs a concrete pin; Auto is coding-dispatch only.
    assert seats["cursor"]["model_id"] == "grok-4.7"
    assert seats["cursor"]["auto_scope"] == "write_implementation_dispatch_with_green_dor"
    assert seats["cursor"]["effort"] == "high"
    assert seats["cursor"]["escalate_model_id"] == "gpt-6.1-sol"
    assert seats["cursor"]["escalate_effort"] == "high"
    assert seats["cursor"]["auto_allowlist"] == ["grok-4.7", "composer-2.5"]
    assert seats["cursor"]["attestation_rule"] == "driver_of_record_requires_attested_resolved_model"
    assert seats["cursor"]["unknown_auto_family_resolution"] == "cursor_family"
    assert seats["cursor"]["unknown_auto_union_families"] == ["xai", "moonshot"]


def test_orchestrator_escalate_pins_astra_high_and_agy_flash():
    """Each seat has default + escalate like AGY Flash, same-SKU escalation, operator 2026-09-22."""
    seats = load_model_catalog()["orchestrator_seats"]
    assert seats["claude"]["escalate_model_id"] == "gpt-6.1-sol"
    assert seats["claude"]["escalate_effort"] == "high"
    assert seats["agy"]["escalate_model_id"] == "gemini-3.8-flash-high"
    assert seats["agy"]["escalate_effort"] == "high"
    # Codex reviewer escalation uses the same Sol high advisor pin.
    fc = load_model_catalog()["formal_cf_defaults"]
    assert fc["codex"]["escalate_model_id"] == "gpt-6.1-sol"
    assert fc["claude"]["escalate_model_id"] == "claude-opus-5-5"


def test_high_ladder_admits_sol_opus_and_grok():
    """#9769: high-risk review admits both Grok transports alongside Opus and Sol."""
    ladders = load_model_catalog()["review_ladders"]
    assert ladders["high"] == [
        ["openai_frontier"],
        ["claude-opus-5-5"],
        ["grok-4.7"],
        ["grok-4.7-cursor-fallback"],
        ["claude-opus-5-5-cursor-fallback"],
    ]
    assert ladders["medium"] == ladders["low"]
    assert ladders["medium"][:5] == ladders["high"]
    assert len(ladders["medium"]) > len(ladders["high"])


@pytest.mark.parametrize("candidate", ["claude-sonnet-5-5", "composer-2.5"])
def test_catalog_rejects_a_high_ladder_seat_outside_risk_reviewer_models(candidate):
    """#9538: the high ladder can list only the models risk_reviewer_models.high names."""
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["high"].append([candidate])
    with pytest.raises(ModelCatalogError, match=r"review_ladders\.high candidate .*performed only by gpt-6\.1-sol, claude-opus-5-5"):
        validate_catalog(broken)


def test_risk_reviewer_models_names_sol_opus_grok_at_high():
    """Critical eligibility uses critical_review without another allowlist."""
    catalog = load_model_catalog()
    assert catalog["review_scheduler"]["risk_reviewer_models"] == {"high": ["gpt-6.1-sol", "claude-opus-5-5", "grok-4.7"]}
    assert risk_reviewer_refusal("claude-opus-5-5-high", "high", catalog) is None
    assert risk_reviewer_refusal("gpt-6.1-sol", "HIGH", catalog) is None
    assert "performed only by" in risk_reviewer_refusal("claude-sonnet-5-5", "high", catalog)
    for risk in ("medium", "low"):
        assert risk_reviewer_refusal("claude-sonnet-5-5", risk, catalog) is None


@pytest.mark.parametrize(
    "value,match",
    [
        ({"urgent": ["gpt-6.1-sol"]}, "unknown risk"),
        ({"high": []}, "non-empty list"),
        ({"high": ["no-such-model"]}, "unknown model"),
        ({"high": ["deepseek-v4-pro"]}, "retired model|DeepSeek"),
    ],
)
def test_catalog_rejects_malformed_risk_reviewer_models(value, match):
    broken = deepcopy(load_model_catalog())
    broken["review_scheduler"]["risk_reviewer_models"] = value
    with pytest.raises(ModelCatalogError, match=match):
        validate_catalog(broken)


def test_practical_ladders_exclude_advisory_roles():
    ladders = load_model_catalog()["review_ladders"]
    for risk in ("medium", "low"):
        names = {name for rung in ladders[risk] for name in rung}
        assert "openai_frontier" in names
        assert "claude-fable-5-1" not in names
        assert "claude-opus-4-8" not in names
        assert "gpt-5.6-terra" not in names
        assert "claude-sonnet-5-5" in names
        assert "pool" in names
        # #9769: native Grok and its attested Cursor fallback are regular reviewers.
        assert "grok-4.7-cursor-fallback" in names
        assert "grok-4.7" in names
    critical = {name for rung in ladders["critical"] for name in rung}
    assert "openai_frontier" in critical
    assert "claude-fable-5-1" not in critical


def test_bridge_only_reviewers_expose_executable_invocations():
    candidates = load_model_catalog()["review_candidates"]
    assert candidates["pool"]["invocation"].endswith("ask-pool")
    assert candidates["glm-5.3"]["invocation"].endswith("ask-glm")


def test_gemini_native_review_catalog_and_risk_ladders():
    catalog = load_model_catalog()
    candidate = catalog["review_candidates"]["gemini-3.8-flash-high"]
    assert candidate["route"] == candidate["transport"] == "agy"
    assert "ukrainian_review" in catalog["models"][candidate["model_id"]]["roles"]
    assert catalog["review_scheduler"]["endpoints"]["agy"]["adapter_transport"] == "native_agy"
    for risk in ("low", "medium", "high", "critical"):
        names = {name for rung in catalog["review_ladders"][risk] for name in rung}
        assert ("gemini-3.8-flash-high" in names) == (risk in {"low", "medium"})


def test_catalog_refuses_gemini_on_other_review_transport():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["google_review"] = {
        **broken["review_candidates"]["openai_frontier"],
        "model_id": "gemini-3.8-flash-high",
    }
    with pytest.raises(ModelCatalogError, match="requires the native AGY route"):
        validate_catalog(broken)


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
    broken["review_candidates"]["grok-4.7"]["transport"] = "hermes"
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


def test_catalog_rejects_cursor_orchestrator_foreign_allowlist_entry():
    # Reviewer mutation (a): adding kimi-code/k3 to allowlist must fail
    broken = deepcopy(load_model_catalog())
    broken["orchestrator_seats"]["cursor"]["auto_allowlist"].append("kimi-code/k3")
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.auto_allowlist must equal exactly"):
        validate_catalog(broken)

    broken_foreign = deepcopy(load_model_catalog())
    broken_foreign["orchestrator_seats"]["cursor"]["auto_allowlist"] = ["grok-4.6", "claude-sonnet-5"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.auto_allowlist must equal exactly"):
        validate_catalog(broken_foreign)


def test_catalog_rejects_cursor_orchestrator_without_or_weakened_attestation_rule():
    broken = deepcopy(load_model_catalog())
    del broken["orchestrator_seats"]["cursor"]["attestation_rule"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.attestation_rule"):
        validate_catalog(broken)

    # Reviewer mutation (b): replacing attestation_rule with driver_of_record_allows_unknown must fail
    broken_weak = deepcopy(load_model_catalog())
    broken_weak["orchestrator_seats"]["cursor"]["attestation_rule"] = "driver_of_record_allows_unknown"
    with pytest.raises(
        ModelCatalogError,
        match=r"orchestrator_seats\.cursor\.attestation_rule must be 'driver_of_record_requires_attested_resolved_model'",
    ):
        validate_catalog(broken_weak)


def test_cursor_orchestrator_auto_resolves_to_cursor_family():
    catalog = load_model_catalog()
    cursor_seat = catalog["orchestrator_seats"]["cursor"]
    assert cursor_seat["unknown_auto_family_resolution"] == "cursor_family"
    assert cursor_seat["unknown_auto_union_families"] == ["xai", "moonshot"]
    assert cursor_seat["auto_allowlist"] == ["grok-4.7", "composer-2.5"]
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
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_family_resolution must be 'cursor_family'"):
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


@pytest.mark.parametrize("model_id", ["auto", "Auto", "cursor:auto", "grok-4.7-fast", "grok-4.6", "kimi-code/k3"])
def test_catalog_rejects_cursor_orchestrator_without_concrete_allowlisted_pin(model_id: str):
    broken = deepcopy(load_model_catalog())
    broken["orchestrator_seats"]["cursor"]["model_id"] = model_id
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.model_id must be a concrete pin"):
        validate_catalog(broken)


def test_catalog_accepts_each_allowlisted_cursor_orchestrator_pin():
    for model_id in ("grok-4.7", "composer-2.5"):
        catalog = deepcopy(load_model_catalog())
        catalog["orchestrator_seats"]["cursor"]["model_id"] = model_id
        validate_catalog(catalog)


@pytest.mark.parametrize("scope", [None, "any", "driver_seat"])
def test_catalog_rejects_cursor_orchestrator_missing_or_widened_auto_scope(scope: str | None):
    broken = deepcopy(load_model_catalog())
    if scope is None:
        del broken["orchestrator_seats"]["cursor"]["auto_scope"]
    else:
        broken["orchestrator_seats"]["cursor"]["auto_scope"] = scope
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.auto_scope"):
        validate_catalog(broken)


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("auto", True),
        ("Auto", True),
        (" AUTO ", True),
        ("cursor:auto", True),
        ("cursor/Auto", True),
        ("default", True),
        (None, False),
        ("", False),
        ("grok-4.7", False),
        ("grok-4.7-high", False),
        ("composer-2.5", False),
        ("autonomous", False),
    ],
)
def test_is_cursor_auto_selector(model: str | None, expected: bool):
    assert is_cursor_auto_selector(model) is expected


def test_cursor_pinned_models_lead_with_the_seat_pin():
    assert cursor_pinned_models() == ("grok-4.7", "composer-2.5")
    catalog = deepcopy(load_model_catalog())
    catalog["orchestrator_seats"]["cursor"]["model_id"] = "composer-2.5"
    assert cursor_pinned_models(catalog) == ("composer-2.5", "grok-4.7")


@pytest.mark.parametrize(
    ("model", "code"),
    [
        (None, "cursor_model_unpinned"),
        ("  ", "cursor_model_unpinned"),
        ("auto", "cursor_auto_outside_coding_task"),
        ("Cursor:Auto", "cursor_auto_outside_coding_task"),
        ("default", "cursor_auto_outside_coding_task"),
        ("composer-2.5-fast", "cursor_model_not_approved"),
        ("grok-4.7-high", "cursor_model_not_approved"),
        ("claude-opus-5-5", "cursor_model_not_approved"),
    ],
)
def test_cursor_non_dispatch_model_refusal_is_typed(model: str | None, code: str):
    refusal = cursor_non_dispatch_model_refusal(model)
    assert refusal is not None
    assert f"({code})" in refusal
    assert "pin grok-4.7 or composer-2.5" in refusal


@pytest.mark.parametrize("model", ["grok-4.7", "composer-2.5"])
def test_cursor_non_dispatch_model_refusal_admits_the_concrete_pins(model: str):
    assert cursor_non_dispatch_model_refusal(model) is None


def test_catalog_rejects_cursor_auto_as_formal_review_identity():
    # In review_scheduler.endpoints
    # #9488: the Cursor endpoint is formal only for an explicit, policy-admitted
    # pin; Composer (Kimi lineage) stays non-eligible.
    broken_ep = deepcopy(load_model_catalog())
    broken_ep["review_scheduler"]["endpoints"]["cursor"]["models"] = ["composer-2.5"]
    with pytest.raises(ModelCatalogError, match=r"review_scheduler\.endpoints\.cursor\.models cannot pin 'composer-2\.5'"):
        validate_catalog(broken_ep)
    unpinned_ep = deepcopy(load_model_catalog())
    unpinned_ep["review_scheduler"]["endpoints"]["cursor"]["models"] = []
    with pytest.raises(ModelCatalogError, match=r"review_scheduler\.endpoints\.cursor needs an explicit models pin"):
        validate_catalog(unpinned_ep)

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
    broken["models"]["grok-4.7"]["transports"].append("hermes")
    with pytest.raises(ModelCatalogError, match="must not route"):
        validate_catalog(broken)


def test_catalog_enforces_quality_floor_and_homogeneous_rungs():
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["medium"][0].append("pool-xs")
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


def test_critical_ladder_anthropic_authority_is_opus_without_fable():
    catalog = load_model_catalog()
    flat = [name for rung in catalog["review_ladders"]["critical"] for name in rung]
    assert flat[:4] == ["openai_frontier", "claude-opus-5-5", "grok-4.7", "grok-4.7-cursor-fallback"]
    assert flat[4:] == ["claude-opus-5-5-cursor-fallback", "composer-2.5", "pool", "pool-xs"]
    # #9583: Fable is no longer a critical last resort.
    assert not any(name.startswith("claude-fable-") for name in flat)
    assert "claude-opus-5" not in flat
    assert "claude-sonnet-5-5" not in flat
    for name in flat:
        assert catalog["review_candidates"][name].get("last_resort", False) is False


def test_opus_advisory_capability_does_not_grant_orchestration() -> None:
    """Model capability metadata must preserve the routing/authority boundary."""
    roles = set(load_model_catalog()["models"]["claude-opus-5"]["roles"])
    assert roles == {"historical_record_resolution"}


def test_opus_5_5_is_the_claude_orchestrator_and_formal_cf_pin() -> None:
    catalog = load_model_catalog()
    roles = set(catalog["models"]["claude-opus-5-5"]["roles"])
    assert "orchestration" in roles
    assert "advisory_consultation" not in roles
    assert "claude-opus-5-5" in catalog["review_scheduler"]["endpoints"]["claude"]["models"]
    assert "claude-opus-5-5" in catalog["formal_cf_defaults"]["claude"]["family_models"]


def test_sol_advised_luna_execution_route_is_bounded_and_machine_readable():
    """The Sol→Luna lane must be explicit, bounded, and source-blind testable."""
    catalog = load_model_catalog()
    route = catalog["execution_routing"]["sol_advised_bounded"]

    advisor = route["advisor"]
    assert advisor["model_id"] == "gpt-6.1-sol"
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
    assert preferred["model_id"] == "gpt-6-luna"
    assert preferred["effort"] == "high"
    assert {
        "bounded_implementation",
        "bounded_investigation",
    } <= set(catalog["models"][preferred["model_id"]]["roles"])
    assert preferred["requires"] == ["complete_advisory_envelope", "objective_scope_ceiling"]
    assert preferred["task_types"] == ["bounded_implementation", "bounded_investigation"]
    assert preferred["escalate_to"] == "gpt-6.1-sol"
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

    # Operator decision 2026-09-30 (#9275): no direct bounded dispatch route.
    assert "direct_worker" not in route
    assert route["bounded_fallback_worker"] == {
        "model_id": "gemini-3.8-flash-high",
        "effort": "high",
        "requires": ["complete_advisory_envelope", "objective_scope_ceiling"],
        "non_bounded_task_families": ["ukrainian-authoring", "ukrainian-review"],
    }
    assert route["autonomous_fallback"] == {
        "model_id": "gpt-6.1-sol",
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
        (
            "bounded_fallback_worker",
            "model_id",
            "set",
            "missing-model",
            "bounded_fallback_worker.model_id references unknown model",
        ),
        ("bounded_fallback_worker", "model_id", "set", "gpt-6.1-sol", "must not be a bounded worker model"),
        (
            "bounded_fallback_worker",
            "requires",
            "set",
            ["objective_scope_ceiling"],
            "bounded_fallback_worker.requires must bind",
        ),
        (
            "bounded_fallback_worker",
            "non_bounded_task_families",
            "set",
            [],
            "non_bounded_task_families must be a non-empty list",
        ),
        ("bounded_fallback_worker", "requires", "delete", None, "bounded_fallback_worker must define exactly"),
        ("autonomous_fallback", "model_id", "set", "missing-model", "autonomous_fallback.model_id references unknown model"),
        ("preferred_worker", "escalate_to", "set", "missing-model", "preferred_worker.escalate_to references unknown model"),
        ("advisor", "effort", "set", "ultra", "advisor.effort must be one of"),
        ("preferred_worker", "effort", "set", "ultra", "preferred_worker.effort must be one of"),
        ("bounded_fallback_worker", "effort", "set", "ultra", "bounded_fallback_worker.effort must be one of"),
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


def test_catalog_refuses_a_direct_bounded_worker_route():
    """#9275: a restored ``direct_worker`` route fails validation (operator decision 2026-09-30)."""
    broken = deepcopy(load_model_catalog())
    broken["execution_routing"]["sol_advised_bounded"]["direct_worker"] = {
        "model_id": "gpt-6-luna",
        "effort": "high",
        "task_types": ["recon"],
        "constraints": ["objective_scope_ceiling"],
    }
    with pytest.raises(ModelCatalogError, match="sol_advised_bounded must define exactly"):
        validate_catalog(broken)


def test_bounded_execution_policy_names_the_envelope_population():
    policy = bounded_execution_policy()
    assert policy.advisor_model_id == "gpt-6.1-sol"
    assert policy.advisor_role == "bounded_advisory_envelope"
    assert policy.bounded_worker_model_id == "gpt-6-luna"
    assert policy.bounded_fallback_model_id == "gemini-3.8-flash-high"
    assert policy.non_bounded_task_families == {"ukrainian-authoring", "ukrainian-review"}


@pytest.mark.parametrize(
    ("spelling", "expected"),
    [
        ("gpt-6-luna", "gpt-6-luna"),
        ("GPT-6-Luna", "gpt-6-luna"),
        ("codex:gpt-6-luna", "gpt-6-luna"),
        ("openai/gpt-6-luna", "gpt-6-luna"),
        ("gpt-6-luna-high", "gpt-6-luna"),
        ("gemini-3.8-flash", "gemini-3.8-flash-high"),
        ("gemini-3.8-flash-low", "gemini-3.8-flash-high"),
        ("claude-opus-5-5[1m]", "claude-opus-5-5"),
        ("not-a-model", None),
        (None, None),
    ],
)
def test_canonical_model_id_resolves_aliases_prefixes_and_variants(spelling, expected):
    assert canonical_model_id(spelling) == expected


def test_budget_substitution_table_admits_cursor_slugs_and_rejects_gpt6():
    """#8855: GPT-6 stays native Codex; the Opus cursor slug is the review-candidate invocation."""
    catalog = load_model_catalog()
    table = catalog["budget_substitution_models"]
    assert "gpt-6.1-sol" not in table["cursor"]
    assert table["cursor"]["claude-opus-5-5"] == "claude-opus-5-5-high"
    assert table["codex"]["gpt-6.1-sol"] == "gpt-6.1-sol"
    broken = deepcopy(catalog)
    broken["budget_substitution_models"]["cursor"]["gpt-6.1-sol"] = "gpt-6.1-sol"
    with pytest.raises(ModelCatalogError, match=r"gpt-6\.1-sol"):
        validate_catalog(broken)


def test_sol_holds_the_astra_advisor_seat_and_runtime_review_pins():
    # Operator 2026-09-29 (#9230): GPT-6.1 Sol is the only Sol and took Astra's seat.
    catalog = load_model_catalog()
    sol = catalog["models"]["gpt-6.1-sol"]
    assert sol["family"] == "openai"
    assert sol["tier"] == "frontier_authority"
    assert {"architecture", "consequential_advisory", "bounded_advisory_envelope"} <= set(sol["roles"])
    assert {"implementation", "standard_review", "critical_review"} <= set(sol["roles"])
    assert "https://developers.openai.com/api/docs/models/gpt-6.1-sol" in sol["sources"]
    assert AGENTS["codex"]["default_model"] == "gpt-6.1-sol"
    assert AGENTS["codex"]["default_effort"] == "high"
    assert catalog["review_candidates"]["openai_frontier"]["invocation"].endswith("--model gpt-6.1-sol --effort high")
    assert catalog["orchestrator_seats"]["codex"]["escalate_effort"] == "high"
    for risk in ("low", "medium", "high"):
        assert catalog["review_ladders"][risk][0] == ["openai_frontier"]


def test_active_codex_routes_are_gpt6_only():
    catalog = load_model_catalog()
    assert catalog["review_scheduler"]["endpoints"]["codex"]["models"] == ["gpt-6.1-sol"]
    native = {
        model_id
        for model_id, model in catalog["models"].items()
        if "native_codex" in model["transports"] and model["lifecycle"] == "active"
    }
    assert native == {"gpt-6-luna", "gpt-6.1-sol"}
    for candidate in catalog["review_candidates"].values():
        if candidate["route"] == "codex":
            assert candidate["model_id"] == "gpt-6.1-sol"


def test_gpt56_routes_are_not_selected():
    catalog = load_model_catalog()
    models = catalog["models"]
    for model_id in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        assert models[model_id]["lifecycle"] == "retired"
        assert models[model_id]["transports"] == []

    # Historical model records may remain, but no executable selector may
    # resolve to the retired generation, including indirect review ladders.
    for section in (
        "execution_routing",
        "review_candidates",
        "review_scheduler",
        "orchestrator_seats",
        "formal_cf_defaults",
        "review_ladders",
    ):
        assert "gpt-5.6-" not in json.dumps(catalog[section], sort_keys=True), section
    assert not AGENTS["codex"]["default_model"].startswith("gpt-5.6-")
    for model_id in ("gpt-6-luna", "gpt-6.1-sol"):
        assert models[model_id]["transports"] == ["native_codex"]


def test_gpt6_sol_and_astra_are_retired_and_unroutable():
    catalog = load_model_catalog()
    for model_id in ("gpt-6-sol", "gpt-6-astra"):
        assert catalog["models"][model_id]["lifecycle"] == "retired"
        assert catalog["models"][model_id]["transports"] == []
    for section in (
        "execution_routing",
        "review_candidates",
        "review_scheduler",
        "orchestrator_seats",
        "formal_cf_defaults",
        "review_ladders",
        "budget_substitution_models",
    ):
        dumped = json.dumps(catalog[section], sort_keys=True)
        assert "gpt-6-sol" not in dumped and "gpt-6-astra" not in dumped, section


@pytest.mark.parametrize(
    ("model", "retired_id"),
    [
        ("gpt-6-sol", "gpt-6-sol"),
        ("gpt-6-astra", "gpt-6-astra"),
        ("cursor:openai/GPT-6-Astra", "gpt-6-astra"),
        ("gpt-6-sol-high", "gpt-6-sol"),
    ],
)
def test_retired_model_refusal_names_id_and_replacement(model, retired_id):
    refusal = retired_model_refusal(model)
    assert refusal == f"model {model!r} is retired in the model catalog ({retired_id}); use gpt-6.1-sol"


@pytest.mark.parametrize(
    "model", [None, "", "gpt-6.1-sol", "gpt-6.1-sol-high", "gpt-6-luna", "kimi-code/k3", "composer-2.5", "auto"]
)
def test_retired_model_refusal_admits_non_retired_ids(model):
    assert retired_model_refusal(model) is None


def test_replaced_by_must_sit_on_retired_model_and_name_active_model():
    broken = deepcopy(load_model_catalog())
    broken["models"]["gpt-6-luna"]["replaced_by"] = "gpt-6.1-sol"
    with pytest.raises(ModelCatalogError, match="replaced_by is only valid on retired models"):
        validate_catalog(broken)
    broken = deepcopy(load_model_catalog())
    broken["models"]["gpt-6-sol"]["replaced_by"] = "gpt-6-astra"
    with pytest.raises(ModelCatalogError, match="replaced_by must reference an active model"):
        validate_catalog(broken)


@pytest.mark.parametrize(
    ("retired", "successor"), [
        ("claude-fable-5", "claude-fable-5-1"),
        ("grok-4.6", "grok-4.7"),
        ("claude-opus-5", "claude-opus-5-5"),
        ("claude-opus-4-8", "claude-opus-5-5"),
        ("claude-sonnet-5", "claude-sonnet-5-5"),
        ("gemini-3.7-flash-high", "gemini-3.8-flash-high"),
        ("gemini-3.6-flash-high", "gemini-3.8-flash-high"),
        ("gemini-3.5-flash-high", "gemini-3.8-flash-high"),
        ("glm-5.2", "glm-5.3"),
        ("deepseek-v4-pro", "deepseek-v4.1-flash"),
        ("claude-sonnet-4.6-thinking", "claude-sonnet-5-5"),
        ("claude-opus-4.6-thinking", "claude-opus-5-5"),
        ("gpt-oss-120b", "gpt-6-luna"),
    ]
)
def test_issue_9301_retired_ids_remain_historical_only(retired, successor):
    catalog = load_model_catalog()
    assert catalog["models"][retired]["lifecycle"] == "retired"
    assert catalog["models"][retired]["replaced_by"] == successor
    assert catalog["models"][retired]["transports"] == []
    for section in ("execution_routing", "review_candidates", "review_scheduler", "orchestrator_seats", "formal_cf_defaults",
                    "review_ladders", "budget_substitution_models"):
        assert retired not in json.dumps(catalog[section]).replace(successor, "successor"), section
    for model in (retired, f"cursor:{retired.upper()}-thinking-high", f"{retired}[1m]"):
        assert f"use {successor}" in retired_model_refusal(model)
    assert retired_model_refusal(successor) is None


@pytest.mark.parametrize(
    ("model", "canonical"),
    [(None, None), ("unknown", None), ("cursor:claude-fable-5-1-thinking-high", "claude-fable-5-1"),
     ("claude-fable-5[1m]", "claude-fable-5"), ("k3", "kimi-code/k3")]
)
def test_catalog_identity_resolves_longest_id_and_preserves_retirement(model, canonical):
    assert resolve_catalog_model_id(model) == canonical


@pytest.mark.parametrize("flag", ["--model {}", "--model={}", "-m {}", "--to-model {}", "--to-model={}"])
@pytest.mark.parametrize("model", ["claude-fable-5", "claude-sonnet-5-5", "unknown-model"])
def test_reviewer_invocation_cannot_hide_a_retired_pin_behind_active_metadata(flag, model):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "delegate.py " + flag.format(model)
    with pytest.raises(ModelCatalogError, match="invocation model does not match"):
        validate_catalog(catalog)


@pytest.mark.parametrize("invocation", [
    "delegate.py --model claude-opus-5-5 --to-model=claude-fable-5",
    "delegate.py -m claude-fable-5 --model=claude-opus-5-5",
    "delegate.py --model",
    "delegate.py --model=",
])
def test_reviewer_invocation_checks_every_model_token(invocation):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = invocation
    with pytest.raises(ModelCatalogError, match="invocation model does not match"):
        validate_catalog(catalog)


@pytest.mark.parametrize("flag", ["--model '{}'", "--model={}", "-m {}", "--to-model {}", "--to-model={}"])
def test_reviewer_invocation_accepts_matching_catalog_aliases(flag):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "delegate.py " + flag.format(
        "claude-opus-5-5-high"
    )
    validate_catalog(catalog)


@pytest.mark.parametrize("prefix", [
    ".venv/bin/python -m scripts.delegate dispatch",
    ".venv/bin/python -u -m scripts.delegate dispatch",
    ".venv/bin/python scripts/delegate.py dispatch",
])
@pytest.mark.parametrize("flag", ["--model", "-m"])
@pytest.mark.parametrize("model", ["claude-opus-5-5", "claude-fable-5"])
def test_python_module_selection_is_not_a_model_pin(prefix, flag, model):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = (
        f"{prefix} --agent claude {flag} {model}"
    )
    if model == "claude-opus-5-5":
        validate_catalog(catalog)
    else:
        with pytest.raises(ModelCatalogError, match="invocation model does not match"):
            validate_catalog(catalog)


def test_reviewer_invocation_rejects_malformed_shell_quoting():
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "delegate.py --model 'claude-opus-5-5"
    with pytest.raises(ModelCatalogError, match="invocation is malformed"):
        validate_catalog(catalog)


@pytest.mark.parametrize("model", ["grok-4.6", "unknown-model", ""])
def test_orchestrator_seat_rejects_unroutable_fallback_model(model):
    catalog = deepcopy(load_model_catalog())
    catalog["orchestrator_seats"]["grok"]["fallback_model_id"] = model
    with pytest.raises(ModelCatalogError, match="fallback_model_id"):
        validate_catalog(catalog)


def test_catalog_cli_help_explains_lookup_and_side_effects(monkeypatch, capsys):
    from scripts.review.model_catalog import _main

    monkeypatch.setattr("sys.argv", ["model_catalog", "--help"])
    with pytest.raises(SystemExit) as exc:
        _main()
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for text in ("--resolve-kimi-model", "--resolve-glm-model", "default", "Examples:", "no writes", "Exit codes:", "Related:"):
        assert text in output


@pytest.mark.parametrize(("model", "retired_id", "successor"), [
    ("gpt-6-sol", "gpt-6-sol", "gpt-6.1-sol"),
    ("gpt-5.6-sol", "gpt-5.6-sol", "gpt-6.1-sol"),
    ("claude-fable-5", "claude-fable-5", "claude-fable-5-1"),
    ("claude-fable-5[1m]", "claude-fable-5", "claude-fable-5-1"),
])
def test_catalog_cli_retired_model_prints_only_refusal(model, retired_id, successor):
    result = subprocess.run(
        [sys.executable, "-m", "scripts.review.model_catalog", "--check-retired-model", model],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        f"model {model!r} is retired in the model catalog ({retired_id}); use {successor}\n"
    )


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "claude-fable-5-1", "unknown-model"])
def test_catalog_cli_non_retired_model_exits_silently(model):
    result = subprocess.run(
        [sys.executable, "-m", "scripts.review.model_catalog", "--check-retired-model", model],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""


@pytest.mark.parametrize("model", [
    "claude-fable-5",
    "grok-4.6",
    "claude-opus-5",
    "claude-opus-4-8",
    "claude-sonnet-5",
    "gemini-3.7-flash-high",
    "gemini-3.6-flash-high",
    "gemini-3.5-flash-high",
    "glm-5.2",
    "deepseek-v4-pro",
    "claude-sonnet-4.6-thinking",
    "claude-opus-4.6-thinking",
    "gpt-oss-120b",
    "deepseek-v4.1-flash",
])
@pytest.mark.parametrize("reference", ["candidate", "endpoint", "default", "escalation", "family", "substitution_source", "substitution_target"])
def test_catalog_rejects_retired_and_rule_excluded_executable_references(model, reference):
    catalog = deepcopy(load_model_catalog())
    if reference == "candidate":
        catalog["review_candidates"]["claude-opus-5-5"]["model_id"] = model
    elif reference == "endpoint":
        catalog["review_scheduler"]["endpoints"]["claude"]["models"].append(model)
    elif reference == "default":
        catalog["formal_cf_defaults"]["claude"]["model_id"] = model
    elif reference == "escalation":
        catalog["formal_cf_defaults"]["claude"]["escalate_model_id"] = model
    elif reference == "family":
        catalog["formal_cf_defaults"]["claude"]["family_models"].append(model)
    elif reference == "substitution_source":
        catalog["budget_substitution_models"]["cursor"][model] = "grok-4.7"
    else:
        catalog["budget_substitution_models"]["cursor"]["grok-4.7"] = model
    with pytest.raises(ModelCatalogError):
        validate_catalog(catalog)


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", "claude-sonnet-5"])
def test_catalog_rejects_sonnet_on_critical_security_ladder(model):
    catalog = deepcopy(load_model_catalog())
    catalog["review_ladders"]["critical"].append([model])
    with pytest.raises(ModelCatalogError, match=r"Sonnet is excluded from security review|unknown candidate"):
        validate_catalog(catalog)


def test_issue_9301_active_exceptions_and_advisory_effort():
    catalog = load_model_catalog()
    for model in ("deepseek-v4.1-flash", "gemini-3.1-pro-high"):
        assert catalog["models"][model]["lifecycle"] == "active"
    assert {model for model, spec in catalog["models"].items()
            if spec["family"] == "openai" and spec["lifecycle"] != "retired"} == {"gpt-6.1-sol", "gpt-6-luna"}
    for section in ("orchestrator_seats", "formal_cf_defaults"):
        for spec in catalog[section].values():
            if spec.get("escalate_model_id") == "gpt-6.1-sol":
                assert spec["escalate_effort"] == "high"
    assert catalog["orchestrator_seats"]["codex"]["effort"] == "high"
    assert catalog["formal_cf_defaults"]["codex"]["effort"] == "high"


def test_sol_defaults_and_escalations_use_high_across_catalog():
    bindings = []

    def visit(value, path):
        if isinstance(value, dict):
            for model_key, effort_key in (("model_id", "effort"), ("escalate_model_id", "escalate_effort")):
                if value.get(model_key) == "gpt-6.1-sol" and effort_key in value:
                    assert value[effort_key] == "high", f"{path}.{effort_key}"
                    bindings.append(f"{path}.{effort_key}")
            for key, child in value.items():
                visit(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(load_model_catalog(), "catalog")
    assert len(bindings) == 8


def test_live_claude_caller_defaults_are_active_catalog_models():
    from scripts.ai_agent_bridge._claude import CLAUDE_ADVISORY_MODEL, CLAUDE_DEFAULT_ASK_MODEL
    from scripts.ai_llm.claude_call import CLAUDE_MODEL_LADDER
    catalog = load_model_catalog()
    for model in (CLAUDE_DEFAULT_ASK_MODEL, CLAUDE_ADVISORY_MODEL, *CLAUDE_MODEL_LADDER):
        assert catalog["models"][model]["lifecycle"] == "active"
    assert CLAUDE_ADVISORY_MODEL == "claude-opus-5-5"


@pytest.mark.parametrize("value", ["true", 1, None])
def test_last_resort_marker_must_be_boolean(value):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["last_resort"] = value
    with pytest.raises(ModelCatalogError, match="last_resort must be a boolean"):
        validate_catalog(catalog)


def test_primary_cannot_follow_last_resort_even_if_quality_is_equal():
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["grok-4.7-cursor-fallback"]["last_resort"] = True
    catalog["review_ladders"]["critical"] = [["grok-4.7-cursor-fallback"], ["claude-opus-5-5"]]
    with pytest.raises(ModelCatalogError, match="improves quality in a later rung"):
        validate_catalog(catalog)


@pytest.mark.parametrize("risk", ["critical", "high", "medium", "low"])
def test_grok_cannot_repeat_in_any_code_review_ladder(risk):
    catalog = deepcopy(load_model_catalog())
    catalog["review_ladders"][risk].append(["grok-4.7"])
    with pytest.raises(ModelCatalogError, match="repeats candidate"):
        validate_catalog(catalog)


def test_catalog_selection_order_matches_last_resort_and_suitability_policy():
    assert load_model_catalog()["policy"]["selection_order"] == [
        "independence_and_hard_gates", "primary_before_last_resort",
        "profile_risk_suitability", "review_quality_tier",
        "health_and_quota_within_tier", "cost_within_equivalent_fit",
    ]


def test_native_grok_runtime_attestation_allowlist_is_exact():
    model = load_model_catalog()["models"]["grok-4.7"]
    assert model["runtime_model_ids"] == ["grok-4.7-build"]
    assert "grok-4.7-build-fast" not in model["runtime_model_ids"]
