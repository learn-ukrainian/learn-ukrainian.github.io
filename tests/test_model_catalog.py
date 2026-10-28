"""Contract tests for the canonical, freshness-gated fleet model catalog."""

from __future__ import annotations

import shlex
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.agent_runtime.registry import AGENTS
from scripts.review.model_catalog import (
    ModelCatalogError,
    activity_role_refusal,
    canonical_model_id,
    cursor_non_dispatch_model_refusal,
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
from tests.claude_route_accounts import HOST_ACCOUNT


@pytest.mark.parametrize("seat,route,launcher,agent,model,effort", [
    ("openai_frontier", "native", "dispatch.py", "codex", "gpt-6.1-sol", "high"),
    ("xai_reviewer", "cursor_fallback", "dispatch.py", "cursor", "grok-4.7-high", None),
    ("anthropic_authority", "native", "dispatch.py", "claude", "claude-opus-5-5", None),
    ("anthropic_practical", "native", "dispatch.py", "claude", "claude-sonnet-5-5", None),
    ("mechanical_worker", "native", "dispatch.py", "claude", "claude-haiku-5-5", "high"),
    ("bounded_worker", "native", "dispatch.py", "codex", "gpt-6-luna", "high"),
    ("google_bounded", "native", "dispatch.py", "agy", "gemini-3.8-flash-high", "high"),
])
def test_catalog_invocations_pin_supported_launchers_and_flags(seat, route, launcher, agent, model, effort):
    from scripts.review.role_resolution import resolve_role

    catalog = load_model_catalog()
    template = catalog["seats"][seat]["routes"][route]["invocation"]
    argv = shlex.split(template.format(wire_id=model))
    expected = [".venv/bin/python", f"scripts/{launcher}", "dispatch", "--agent", agent, "--model", model]
    if effort:
        expected += ["--effort", effort]
    assert argv == expected
    from scripts.dispatcher.cli import build_parser

    mode = "workspace-write" if seat == "google_bounded" else "read-only"  # dispatch refuses read-only AGY (C-2970)
    args = build_parser().parse_args([*argv[2:],
        "--worktree", "--mode", mode, "--task-id", "catalog-review", "--prompt-file", "prompt.md",
    ])
    assert (args.agent, args.model, args.effort, args.task_id) == (agent, model, effort, "catalog-review")
    if seat == "google_bounded":
        candidate = resolve_role("bounded_fallback", purpose="inspect").candidates[0]
        assert list(candidate.argv) == expected


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
    catalog["review_candidates"]["grok-4.7-cursor-fallback"]["suitability_roles"] = roles
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
    assert require_execution_model("gpt-6.1-terra", transport="native_codex", catalog=catalog) == "gpt-6.1-terra"
    terra = catalog["models"]["gpt-6.1-terra"]
    assert terra["family"] == "openai"
    assert terra["tier"] == "frontier_practical"
    assert terra["routing_wire_ids"] == {"native_codex": "gpt-6.1-terra"}
    assert set(terra["roles"]) == {"implementation", "agentic_coding", "bounded_checks"}
    for activity in ("review", "consult"):
        assert activity_role_refusal("gpt-6.1-terra", activity, catalog=catalog)
    assert all(row["model_id"] != "gpt-6.1-terra" for row in catalog["review_candidates"].values())
    assert catalog["review_scheduler"]["endpoints"]["codex"]["models"] == ["gpt-6.1-sol"]
    assert catalog["orchestrator_seats"]["codex"]["model_id"] == "gpt-6.1-sol"
    assert require_execution_model("gemini-3.8-flash-low", transport="agy", catalog=catalog) == "gemini-3.8-flash-high"
    catalog["models"]["gemini-3.8-flash-high"]["lifecycle"] = "hold"
    with pytest.raises(ModelCatalogError, match="not admitted for execution"):
        require_execution_model("gemini-3.8-flash-low", transport="agy", catalog=catalog)


def test_fallback_sonnet_candidate_cannot_reenter_automatic_ladder():
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["medium"][3] = ["claude-sonnet-5"]
    with pytest.raises(ModelCatalogError, match=r"unknown candidate|must reference an active model"):
        validate_catalog(broken)


def test_luna_worker_does_not_enter_formal_review_ladders() -> None:
    """Same-family bounded execution must never become its own formal gate."""
    catalog = load_model_catalog()
    assert "gpt-5.6-luna" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        assert "gpt-5.6-luna" not in {candidate for rung in ladder for candidate in rung}


def test_kimi_is_absent_from_review_candidates_and_every_ladder() -> None:
    """Kimi seats admit web, UI and backend coding only (formerly a rung on every ladder); glm is pin-only."""
    catalog = load_model_catalog()
    assert "kimi-k3" not in catalog["review_candidates"]
    for ladder in catalog["review_ladders"].values():
        candidates = {candidate for rung in ladder for candidate in rung}
        assert "kimi-k3" not in candidates
        assert "glm-5.3" not in candidates


def test_kimi_aliases_and_routes_are_catalog_backed() -> None:
    """OO-58: empty transports yield no executable alias. Historical routes stay on the record."""
    assert kimi_model_aliases() == {}
    with pytest.raises(ModelCatalogError, match="is retired in the model catalog"):
        resolve_kimi_model("kimi-k3[1m]")
    routes = load_model_catalog()["models"]["kimi-code/k3"]["kimi_routes"]
    assert routes == {
        "kimicc_alias": "k3",
        "platform_model_id": "kimi-k3[1m]",
        "coding_model_id": "k3",
        "context_profile": "kimicc_k3",
    }
    validate_kimi_alias_consumers()


def test_generic_model_aliases_resolve_k3_256k_but_kimicc_does_not_route_it() -> None:
    """k3-256k stays a historical alias. OO-58 leaves the kimicc endpoint with no routable model."""
    aliases = model_aliases()
    assert aliases["kimi-code/k3-256k"] == "kimi-code/k3-256k"
    assert aliases["k3-256k"] == "kimi-code/k3-256k"
    assert aliases["kimi-k3-256k"] == "kimi-code/k3-256k"
    endpoints = load_model_catalog()["review_scheduler"]["endpoints"]
    assert endpoints["kimicc"]["models"] == []


def test_every_kimicc_routable_alias_has_coding_model_id() -> None:
    """OO-58: the endpoint lists no model, so resolve refuses the historical alias."""
    catalog = load_model_catalog()
    endpoint_ids = catalog["review_scheduler"]["endpoints"]["kimicc"]["models"]
    assert endpoint_ids == []
    assert kimi_model_aliases(catalog) == {}
    with pytest.raises(ModelCatalogError, match="is retired in the model catalog"):
        resolve_kimi_model("k3", catalog)


def test_glm_retirement_refuses_aliases_and_keeps_historical_identity() -> None:
    assert glm_model_aliases() == {}
    for alias in ("glm-5.3", "glm53", "glm"):
        assert model_aliases()[alias] == "glm-5.3"
        with pytest.raises(ModelCatalogError, match="is retired in the model catalog"):
            resolve_glm_model(alias)
    assert model_aliases()["glm52"] == "glm-5.2"
    validate_glm_alias_consumers()


def test_catalog_rejects_kimi_route_without_its_friendly_alias():
    """The alias rule still binds if a Kimi transport is put back. The live row stays retired."""
    broken = deepcopy(load_model_catalog())
    model = broken["models"]["kimi-code/k3"]
    model["lifecycle"] = "active"
    model["transports"] = ["native_kimi"]
    model["aliases"].remove("k3")
    with pytest.raises(ModelCatalogError, match="kimicc_alias must be listed"):
        validate_catalog(broken)


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


def test_fable_holds_no_review_or_advisory_role():
    """#9583 roles still bar review/advice while OO-58 parks the active model."""
    catalog = load_model_catalog()
    fable = catalog["models"]["claude-fable-5-1"]
    assert fable["lifecycle"] == "active"
    assert fable["transports"] == ["native_claude"]
    assert "replaced_by" not in fable
    assert not {"architecture", "critical_review", "consequential_advisory", "bounded_advisory_envelope"} & set(
        fable["roles"]
    )
    assert all(c["model_id"] != "claude-fable-5-1" for c in catalog["review_candidates"].values())
    for risk, ladder in catalog["review_ladders"].items():
        assert not any(name.startswith("claude-fable") for rung in ladder for name in rung), risk
    assert "claude-fable-5-1" not in catalog["review_scheduler"]["endpoints"]["claude"]["models"]
    assert "claude-fable-5-1" not in catalog["formal_cf_defaults"]["claude"]["family_models"]
    assert "claude-fable-5-1" not in catalog["budget_substitution_models"]["cursor"]


@pytest.mark.parametrize("model", ["claude-fable-5-1", "claude-fable-5-1[1m]", "claude-fable-5-1-thinking-high"])
@pytest.mark.parametrize("activity", ["review", "consult"])
def test_fable_is_refused_every_review_and_consult_activity(model, activity):
    """#9583: activity admission reads the catalog roles, so every Fable spelling is refused."""

    refusal = activity_role_refusal(model, activity)
    expected = "holds no review, critique or approval role" if activity == "review" else "holds no ACP ask, consult or discussion role"
    assert refusal and expected in refusal
    assert f"review_scheduler.activity_roles.{activity}" in refusal


@pytest.mark.parametrize("activity", ["review", "consult"])
def test_retired_astra_holds_no_activity_role(activity):

    assert "retired in the model catalog" in activity_role_refusal("gpt-6-astra", activity)


@pytest.mark.parametrize("model", ["claude-opus-5-5", "gpt-6.1-sol", "gemini-3.8-flash-high", "claude-sonnet-5-5"])
@pytest.mark.parametrize("activity", ["review", "consult"])
def test_opus_sol_and_reviewers_are_admitted_every_activity(model, activity):

    assert activity_role_refusal(model, activity) is None


def test_recon_models_consult_but_never_review():

    assert activity_role_refusal("gpt-6-luna", "consult") is None
    assert "holds no review" in activity_role_refusal("gpt-6-luna", "review")


def test_unknown_activity_and_unknown_model():

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
            r"review_candidates\.claude-opus-5-5: model 'claude-fable-5-1'.*holds no review",
        ),
        (
            lambda c: c["review_scheduler"]["endpoints"]["claude"]["models"].append("claude-fable-5-1"),
            r"review_scheduler\.endpoints\.claude\.models: model 'claude-fable-5-1'.*holds no review",
        ),
        (
            lambda c: c["review_scheduler"]["risk_reviewer_models"]["high"].append("claude-fable-5-1"),
            r"review_scheduler\.risk_reviewer_models\.high: model 'claude-fable-5-1'.*holds no review",
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


@pytest.mark.parametrize("candidate", ["claude-sonnet-5-5"])
def test_catalog_rejects_a_high_ladder_seat_outside_risk_reviewer_models(candidate):
    """#9538: the high ladder can list only the models risk_reviewer_models.high names."""
    broken = deepcopy(load_model_catalog())
    broken["review_ladders"]["high"].append([candidate])
    with pytest.raises(
        ModelCatalogError, match=r"review_ladders\.high candidate .*performed only by gpt-6\.1-sol, claude-opus-5-5"
    ):
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


def test_catalog_refuses_gemini_on_other_review_transport():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["google_review"] = {
        **broken["review_candidates"]["openai_frontier"],
        "model_id": "gemini-3.8-flash-high",
    }
    with pytest.raises(ModelCatalogError, match="requires the native AGY route"):
        validate_catalog(broken)


def test_catalog_rejects_learner_content_as_a_code_closeout_profile():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["openai_frontier"]["review_profiles"].append("content")
    with pytest.raises(ModelCatalogError, match="unsupported code-closeout profiles"):
        validate_catalog(broken)


def test_catalog_rejects_unknown_candidate_model_reference():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["claude-sonnet-5-5"]["model_id"] = "missing-model"
    with pytest.raises(ModelCatalogError, match="unknown model"):
        validate_catalog(broken)


def test_catalog_rejects_missing_risk_ladder():
    broken = deepcopy(load_model_catalog())
    del broken["review_ladders"]["critical"]
    with pytest.raises(ModelCatalogError, match="define exactly"):
        validate_catalog(broken)


def test_catalog_rejects_candidate_transport_not_supported_by_model():
    broken = deepcopy(load_model_catalog())
    broken["review_candidates"]["grok-4.7-cursor-fallback"]["transport"] = "hermes"
    with pytest.raises(ModelCatalogError, match="is not listed"):
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
    assert cursor_seat["unknown_auto_union_families"] == ["xai"]
    assert cursor_seat["auto_allowlist"] == ["grok-4.7"]
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
    with pytest.raises(
        ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_family_resolution must be 'cursor_family'"
    ):
        validate_catalog(broken_invalid_res)

    # Reject missing unknown_auto_union_families
    broken_missing_fams = deepcopy(catalog)
    del broken_missing_fams["orchestrator_seats"]["cursor"]["unknown_auto_union_families"]
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.unknown_auto_union_families"):
        validate_catalog(broken_missing_fams)

    # Reject mismatched unknown_auto_union_families (e.g. wrong family or missing family)
    broken_mismatched_fams = deepcopy(catalog)
    broken_mismatched_fams["orchestrator_seats"]["cursor"]["unknown_auto_union_families"] = ["openai", "moonshot"]
    with pytest.raises(
        ModelCatalogError,
        match=r"orchestrator_seats\.cursor\.unknown_auto_union_families must match allowlist model families",
    ):
        validate_catalog(broken_mismatched_fams)


@pytest.mark.parametrize("model_id", ["auto", "Auto", "cursor:auto", "grok-4.7-fast", "grok-4.6", "kimi-code/k3"])
def test_catalog_rejects_cursor_orchestrator_without_concrete_allowlisted_pin(model_id: str):
    broken = deepcopy(load_model_catalog())
    broken["orchestrator_seats"]["cursor"]["model_id"] = model_id
    with pytest.raises(ModelCatalogError, match=r"orchestrator_seats\.cursor\.model_id must be a concrete pin"):
        validate_catalog(broken)


def test_catalog_accepts_each_allowlisted_cursor_orchestrator_pin():
    for model_id in ("grok-4.7",):
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


@pytest.mark.parametrize(
    ("model", "code"),
    [
        (None, "cursor_model_unpinned"),
        ("  ", "cursor_model_unpinned"),
        ("auto", "cursor_auto_outside_coding_task"),
        ("Cursor:Auto", "cursor_auto_outside_coding_task"),
        ("default", "cursor_auto_outside_coding_task"),
        ("composer-2.5-fast", "cursor_model_not_approved"),
        ("composer-2.5[fast=true]", "cursor_model_not_approved"),
        ("composer-2.5[arbitrary=value]", "cursor_model_not_approved"),
        ("grok-4.7-fast", "cursor_model_not_approved"),
        ("claude-opus-5-5", "cursor_model_not_approved"),
    ],
)
def test_cursor_non_dispatch_model_refusal_is_typed(model: str | None, code: str):
    refusal = cursor_non_dispatch_model_refusal(model)
    assert refusal is not None
    assert f"({code})" in refusal
    assert "pin grok-4.7" in refusal


@pytest.mark.parametrize("model", ["grok-4.7", "grok-4.7-high"])
def test_cursor_non_dispatch_model_refusal_admits_the_concrete_pins(model: str):
    assert cursor_non_dispatch_model_refusal(model) is None


def test_catalog_rejects_cursor_auto_as_formal_review_identity():
    # In review_scheduler.endpoints
    # #9488: the Cursor endpoint is formal only for an explicit, policy-admitted
    # pin; Composer (Kimi lineage) stays non-eligible.
    broken_ep = deepcopy(load_model_catalog())
    broken_ep["review_scheduler"]["endpoints"]["cursor"]["models"] = ["composer-2.5"]
    with pytest.raises(ModelCatalogError, match="references retired model"):
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
        "invocation": ".venv/bin/python scripts/dispatch.py dispatch --agent cursor",
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
        "invocation": ".venv/bin/python scripts/dispatch.py dispatch --agent cursor",
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
    broken["review_ladders"]["medium"][0].append("claude-sonnet-5-5")
    with pytest.raises(ModelCatalogError, match="mixes quality tiers"):
        validate_catalog(broken)


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
    """#8855: GPT-6 stays native Codex. D-129 (#10464): Opus has no Cursor substitution row."""
    catalog = load_model_catalog()
    table = catalog["budget_substitution_models"]
    assert "gpt-6.1-sol" not in table["cursor"]
    assert "claude-opus-5-5" not in table["cursor"]
    assert "claude-fable-5-1" not in table["cursor"]
    assert table["codex"]["gpt-6.1-sol"] == "gpt-6.1-sol"
    broken = deepcopy(catalog)
    broken["budget_substitution_models"]["cursor"]["gpt-6.1-sol"] = "gpt-6.1-sol"
    with pytest.raises(ModelCatalogError, match=r"gpt-6\.1-sol"):
        validate_catalog(broken)


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


@pytest.mark.parametrize("model", [None, "", "gpt-6.1-sol", "gpt-6.1-sol-high", "gpt-6-luna", "grok-4.7", "auto"])
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
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "dispatch.py " + flag.format(model)
    with pytest.raises(ModelCatalogError, match="invocation model does not match"):
        validate_catalog(catalog)


@pytest.mark.parametrize("invocation", [
    "dispatch.py --model claude-opus-5-5 --to-model=claude-fable-5",
    "dispatch.py -m claude-fable-5 --model=claude-opus-5-5",
    "dispatch.py --model",
    "dispatch.py --model=",
])
def test_reviewer_invocation_checks_every_model_token(invocation):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = invocation
    with pytest.raises(ModelCatalogError, match="invocation model does not match"):
        validate_catalog(catalog)


@pytest.mark.parametrize("flag", ["--model '{}'", "--model={}", "-m {}", "--to-model {}", "--to-model={}"])
def test_reviewer_invocation_accepts_matching_catalog_aliases(flag):
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "dispatch.py " + flag.format(
        "claude-opus-5-5-high"
    )
    validate_catalog(catalog)


@pytest.mark.parametrize("prefix", [
    ".venv/bin/python -m scripts.dispatcher.cli dispatch",
    ".venv/bin/python -u -m scripts.dispatcher.cli dispatch",
    ".venv/bin/python scripts/dispatch.py dispatch",
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
    catalog["review_candidates"]["claude-opus-5-5"]["invocation"] = "dispatch.py --model 'claude-opus-5-5"
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


@pytest.mark.parametrize("model", ["gpt-6.1-sol", "claude-opus-5-5", "unknown-model"])
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


def test_deepseek_flash_catalog_class_is_opencode_execution_only():
    model = "deepseek-v4.1-flash"
    assert require_execution_model(model, transport="opencode") == model
    for transport in ("hermes", "cursor", "codex"):
        with pytest.raises(ModelCatalogError, match="requires the opencode transport"):
            require_execution_model(model, transport=transport)

    catalog = load_model_catalog()
    for reference in ("candidate", "default", "escalation", "family", "endpoint", "substitution_source", "substitution_target"):
        changed = deepcopy(catalog)
        if reference == "candidate":
            changed["review_candidates"]["claude-opus-5-5"]["model_id"] = model
        elif reference == "default":
            changed["formal_cf_defaults"]["claude"]["model_id"] = model
        elif reference == "escalation":
            changed["formal_cf_defaults"]["claude"]["escalate_model_id"] = model
        elif reference == "family":
            changed["formal_cf_defaults"]["claude"]["family_models"].append(model)
        elif reference == "endpoint":
            changed["review_scheduler"]["endpoints"]["claude"]["models"].append(model)
        elif reference == "substitution_source":
            changed["budget_substitution_models"]["cursor"][model] = "grok-4.7"
        else:
            changed["budget_substitution_models"]["cursor"]["grok-4.7"] = model
        with pytest.raises(ModelCatalogError, match=r"DeepSeek|does not admit"):
            validate_catalog(changed)


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", "claude-sonnet-5"])
def test_catalog_rejects_sonnet_on_critical_security_ladder(model):
    catalog = deepcopy(load_model_catalog())
    catalog["review_ladders"]["critical"].append([model])
    with pytest.raises(ModelCatalogError, match=r"Sonnet is excluded from security review|unknown candidate"):
        validate_catalog(catalog)


@pytest.mark.parametrize("tier", ["low", "medium", "high"])
@pytest.mark.parametrize("risk", ["low", "medium", "high", "critical"])
def test_argon_formal_code_review_is_refused_before_routing_or_launch(monkeypatch, tier, risk):
    from scripts.agent_runtime import target_admission

    def forbidden(*args, **kwargs):
        pytest.fail("Argon formal review must refuse before routing or provider launch")

    monkeypatch.setattr("subprocess.run", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    with pytest.raises(target_admission.ReviewAdmissionRefused, match="is retired in the model catalog"):
        target_admission.resolve_and_admit(
            ("agy",),
            mode="read-only",
            model=f"gemini-4-argon-{tier}",
            review_dispatch=True,
            review_profile="code",
            review_risk=risk,
            review_author_model="gpt-6.1-sol",
            route=forbidden,
            claude_account=HOST_ACCOUNT,
        )


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


def test_primary_cannot_follow_last_resort_even_if_quality_is_equal():
    catalog = deepcopy(load_model_catalog())
    catalog["review_candidates"]["grok-4.7-cursor-fallback"]["last_resort"] = True
    catalog["review_ladders"]["critical"] = [["grok-4.7-cursor-fallback"], ["claude-opus-5-5"]]
    with pytest.raises(ModelCatalogError, match="improves quality in a later rung"):
        validate_catalog(catalog)


@pytest.mark.parametrize("risk", ["critical", "high", "medium", "low"])
def test_grok_cannot_repeat_in_any_code_review_ladder(risk):
    catalog = deepcopy(load_model_catalog())
    catalog["review_ladders"][risk].append(["grok-4.7-cursor-fallback"])
    with pytest.raises(ModelCatalogError, match="repeats candidate"):
        validate_catalog(catalog)


def test_driver_brief_population_follows_catalog_capabilities():
    from scripts.review.model_catalog import driver_brief_models

    catalog = deepcopy(load_model_catalog())
    assert driver_brief_models(catalog) == {"gpt-6-luna", "claude-haiku-5-5"}
    catalog["models"]["claude-haiku-5-5"]["roles"].remove("bounded_implementation")
    assert driver_brief_models(catalog) == {"gpt-6-luna"}
    catalog["models"]["claude-haiku-5-5"]["roles"].append("bounded_implementation")
    catalog["models"]["claude-haiku-5-5"]["lifecycle"] = "hold"
    assert driver_brief_models(catalog) == {"gpt-6-luna"}
