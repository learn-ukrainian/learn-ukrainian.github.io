"""Seat/role schema, transport provenance and frozen-routing equivalence."""

from __future__ import annotations

import ast
import gzip
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from functools import partial
from pathlib import Path

import pytest

from scripts.fleet import credit_lane
from scripts.review.model_catalog import (
    ModelCatalogError,
    canonical_model_id,
    load_model_catalog,
    resolve_role,
    validate_catalog,
)
from scripts.review.reviewer_resolver import ResolverInputs, resolve_reviewer
from scripts.review.role_resolution import expanded_legacy_view
from tests.review.test_model_catalog import APPROVED_BASELINE, APPROVED_INPUTS, BASELINE, CAPTURE, FIXTURE, INPUTS


@pytest.fixture
def catalog():
    return deepcopy(load_model_catalog())


def test_v1_without_extension_and_v11_with_extension_are_accepted(catalog):
    assert validate_catalog(deepcopy(BASELINE["catalog"])) == BASELINE["catalog"]
    catalog["schema_version"] = "model-catalog.v1.1"
    assert validate_catalog(catalog)["schema_version"] == "model-catalog.v1.1"
    assert expanded_legacy_view(catalog) == APPROVED_BASELINE["catalog"]


def test_expansion_is_independent_and_does_not_mutate_catalog(catalog):
    before = deepcopy(catalog)
    expanded = expanded_legacy_view(catalog)
    assert expanded == APPROVED_BASELINE["catalog"]
    expanded["models"]["gpt-6.1-sol"]["roles"].clear()
    assert catalog == before
    assert expanded_legacy_view(BASELINE["catalog"]) == BASELINE["catalog"]


def test_roles_and_identity_aliases_remain_distinct():
    assert canonical_model_id("bounded_advisor") is None
    assert canonical_model_id("anthropic_authority") is None
    assert canonical_model_id("claude-opus-5-5[1m]") == "claude-opus-5-5"
    with pytest.raises(ModelCatalogError, match="unknown routing role"):
        resolve_role("gpt-6.1-sol", purpose="inspect")
    with pytest.raises(ModelCatalogError, match="stable routing role"):
        resolve_role([], purpose="inspect")


def test_authorities_have_one_holder_per_family_and_multiple_transports():
    result = resolve_role("designated_authorities", purpose="inspect")
    assert [(row.model_id, row.family, row.transport) for row in result.candidates] == [
        ("gpt-6.1-sol", "openai", "native_codex"),
        ("claude-opus-5-5", "anthropic", "native_claude"),
        ("claude-opus-5-5", "anthropic", "cursor"),
    ]
    assert all(row.decision_reference and row.qualification_reference is None for row in result.candidates)


def test_wire_ids_belong_to_identity_and_transport_and_opus_is_primary(catalog):
    result = resolve_role("anthropic_authority_reviewer", purpose="launch", transport="cursor")
    native, cursor = result.candidates
    assert native.wire_id == "claude-opus-5-5"
    assert cursor.wire_id == "claude-opus-5-5-high"
    assert native.exclusion_reasons == ("transport_mismatch",)
    assert not cursor.exclusion_reasons
    assert cursor.argv[-1] == cursor.wire_id
    assert catalog["seats"]["anthropic_authority"]["routes"]["cursor_fallback"].get("last_resort", False) is False
    assert expanded_legacy_view(catalog)["review_candidates"] == APPROVED_BASELINE["catalog"]["review_candidates"]


def test_launch_explicitly_pins_implicit_bridge_defaults():
    inspected = resolve_role("legacy_reviewers", purpose="inspect")
    launched = resolve_role("legacy_reviewers", purpose="launch")
    old = next(row for row in inspected.candidates if row.seat == "volume_reviewer")
    new = next(row for row in launched.candidates if row.seat == "volume_reviewer")
    assert "--model" not in old.argv
    assert new.argv[-2:] == ("--model", new.wire_id)
    assert canonical_model_id(new.wire_id) == new.model_id


def test_implicit_bridge_wire_ids_match_existing_provider_defaults():
    source = Path(__file__).resolve().parents[2] / "scripts/ai_agent_bridge/_opencode.py"
    defaults = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(source.read_text()).body
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"POOL_MODEL", "GLM_MODEL"}
    }
    result = resolve_role("legacy_reviewers", purpose="launch")
    assert next(row for row in result.candidates if row.seat == "volume_reviewer").wire_id == defaults["POOL_MODEL"]
    assert next(row for row in result.candidates if row.seat == "local_reviewer").wire_id == defaults["GLM_MODEL"]


def test_role_aliases_preserve_holder_and_constraints():
    assert resolve_role("autonomous_fallback", purpose="inspect").candidates == resolve_role(
        "openai_frontier_coder", purpose="inspect").candidates


@pytest.mark.parametrize("health,observation,rank,diagnostic", [
    (None, "unknown", 0, "HEALTH_UNKNOWN"), ({}, "unknown", 0, "HEALTH_UNKNOWN"),
    ({"absent": "healthy"}, "unknown", 0, "HEALTH_UNKNOWN"),
    ({"codex": "unknown"}, "unknown", 0, "HEALTH_UNKNOWN"),
    ({"codex": "unavailable"}, "unknown", 0, "HEALTH_UNKNOWN"),
    ({"codex": "healthy"}, "healthy", 0, None),
    ({"codex": "degraded"}, "degraded", 1, None),
    ({"codex": "near_cap"}, "near_cap", 2, None),
    ({"codex": "degraded_telemetry"}, "degraded_telemetry", 3, None),
    ({"codex": "unhealthy"}, "unhealthy", 4, None),
    ({"agents": {"codex": {"status": "unavailable", "health": {"healthy": True}}}}, "degraded_telemetry", 3, None),
])
def test_health_observation_is_separate_from_baseline_rank(health, observation, rank, diagnostic):
    for purpose in ("inspect", "launch"):
        row = resolve_role("bounded_advisor", purpose=purpose, health=health).candidates[0]
        assert (row.health, row.health_rank, row.health_provenance["diagnostic"]) == (observation, rank, diagnostic)
        assert not row.exclusion_reasons  # no new universal health prerequisite


def test_health_evidence_does_not_echo_unrelated_account_fields():
    row = resolve_role("bounded_advisor", purpose="inspect", health={
        "agents": {"codex": {"status": "cool", "account": "private-account", "credit_balance": 9}},
    }).candidates[0]
    assert row.health == "healthy"
    assert "private-account" not in json.dumps(row.health_provenance)


def test_family_capability_isolation_subject_and_explicit_pin_exclusions():
    result = resolve_role("anthropic_authority_reviewer", purpose="inspect", family="openai", context={
        "required_capabilities": ["unsupported"], "isolation_required": True,
        "excluded_seats": ["anthropic_authority"], "excluded_families": ["anthropic"],
        "pinned_model": "gpt-6.1-sol",
    })
    for row in result.candidates:
        assert {"family_mismatch", "subject_seat_excluded", "subject_family_excluded",
                "required_capability_missing", "explicit_pin_mismatch"} <= set(row.exclusion_reasons)
    assert "isolation_required" not in result.candidates[0].exclusion_reasons
    assert "isolation_required" in result.candidates[1].exclusion_reasons


def test_risk_roles_use_existing_hard_gate_evidence():
    result = resolve_role("code_review_critical", purpose="inspect", context={"isolation_required": True})
    for row in result.candidates:
        if row.transport == "cursor":
            assert row.exclusion_reasons
    low = resolve_role("code_review_low", purpose="inspect")
    assert next(row for row in low.candidates if row.seat == "volume_reviewer").exclusion_reasons


def test_role_evidence_uses_supplied_catalog_and_egress_policy(catalog):
    catalog["review_scheduler"]["profile_risk_role_order"]["code"]["low"] = ["critical_review"]
    result = resolve_role("code_review_low", catalog=catalog, purpose="inspect")
    practical = next(row for row in result.candidates if row.seat == "anthropic_practical")
    assert "review_role_suitability_missing" in practical.exclusion_reasons
    unknown = resolve_role("legacy_reviewers", purpose="inspect")
    admitted = resolve_role("legacy_reviewers", purpose="inspect", context={"data_egress_policy": "local_interactive"})
    assert "data_egress_policy_required" in next(row for row in unknown.candidates if row.seat == "local_reviewer").exclusion_reasons
    assert "data_egress_policy_required" not in next(row for row in admitted.candidates if row.seat == "local_reviewer").exclusion_reasons


def test_catalog_digest_is_exact_and_evidence_is_serializable(catalog):
    result = resolve_role("bounded_advisor", catalog=catalog, purpose="inspect")
    digest = hashlib.sha256(json.dumps(validate_catalog(catalog), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert result.catalog_digest == digest
    assert json.loads(json.dumps(result.to_dict()))["schema_version"] == "role-resolution.v1"


@pytest.mark.parametrize("context", [{"unsafe_override": True}, [], {"isolation_required": "yes"},
    {"required_capabilities": [1]}, {"excluded_families": ["openai", "openai"]}, {"pinned_model": "bounded_advisor"}])
def test_context_refuses_unsupported_or_ambiguous_inputs(context):
    with pytest.raises(ModelCatalogError):
        resolve_role("bounded_advisor", purpose="launch", context=context)


def test_invalid_purpose_and_legacy_catalog_without_roles():
    with pytest.raises(ModelCatalogError, match="purpose"):
        resolve_role("bounded_advisor", purpose="execute")
    with pytest.raises(ModelCatalogError, match="no routing roles"):
        resolve_role("bounded_advisor", catalog=BASELINE["catalog"], purpose="inspect")
    with pytest.raises(ValueError, match="unsupported health status"):
        resolve_role("bounded_advisor", purpose="inspect", health={"codex": "stale"})


@pytest.mark.parametrize("field,value", [("schema_version", []), ("schema_version", "model-catalog.v2"),
    ("routing_schema_version", "model-catalog.v1.2"), ("roles", {}), ("seats", None)])
def test_invalid_extension_versions_or_empty_sections(catalog, field, value):
    catalog[field] = value
    with pytest.raises(ModelCatalogError):
        validate_catalog(catalog)


@pytest.mark.parametrize("model", ["unregistered", "gpt-6-astra", "qwen/qwen3.6-plus", "gpt-6.1-sol-high"])
def test_holder_requires_concrete_registered_routable_identity(catalog, model):
    catalog["seats"]["bounded_worker"]["model_id"] = model
    with pytest.raises(ModelCatalogError, match=r"unknown concrete|unroutable"):
        validate_catalog(catalog)


@pytest.mark.parametrize("value", [[], [1], ["design_approval", "design_approval"], None])
def test_bindings_must_be_explicit_unique_strings(catalog, value):
    catalog["seats"]["bounded_worker"]["bindings"] = value
    with pytest.raises(ModelCatalogError, match="bindings"):
        validate_catalog(catalog)


@pytest.mark.parametrize("value", [True, -1, "high"])
def test_priority_requires_nonnegative_integer(catalog, value):
    catalog["seats"]["bounded_worker"]["priority"] = value
    with pytest.raises(ModelCatalogError, match="priority"):
        validate_catalog(catalog)


@pytest.mark.parametrize("spec,match", [
    ({"seat": "missing"}, "unknown seat"), ({"role": "missing"}, "unknown routing role"),
    ({"role": []}, "routing role name"), ({"seat": "bounded_worker", "role": "bounded_advisor"}, "selector"),
    ({"routes": ["bounded_worker/missing"]}, "unknown seat route"),
    ({"select_binding": "missing", "order_by": "priority"}, "unheld binding"),
    ({"select_binding": "legacy_review_candidate"}, "order_by"),
    ({"select_binding": "legacy_review_candidate", "order_by": "priority", "cardinality": "one"}, "ambiguous singleton"),
    ({"seat": "bounded_worker", "cardinality": []}, "cardinality"),
    ({"seat": "bounded_worker", "risk": []}, "unsupported risk"),
    ({"seat": "bounded_worker", "required_model_roles": ["architecture"]}, "lacks required"),
    ({"role": "code_review_critical", "required_model_roles": []}, "inherit constraints"),
])
def test_invalid_role_references_and_constraints(catalog, spec, match):
    catalog["roles"]["invalid_role"] = spec
    with pytest.raises(ModelCatalogError, match=match):
        validate_catalog(catalog)


def test_role_cycle_fails_closed(catalog):
    catalog["roles"].update({"first": {"role": "second"}, "second": {"role": "first"}})
    with pytest.raises(ModelCatalogError, match="cycle"):
        validate_catalog(catalog)


def test_authority_family_cannot_have_two_logical_holders(catalog):
    catalog["seats"]["anthropic_practical"]["bindings"].append("design_approval")
    with pytest.raises(ModelCatalogError, match="one holder per independence family"):
        validate_catalog(catalog)


def test_tier_alone_does_not_grant_design_authority(catalog):
    catalog["roles"]["wrong_authority"] = {"seat": "bounded_worker", "required_model_roles": ["architecture"]}
    with pytest.raises(ModelCatalogError, match="lacks required model roles"):
        validate_catalog(catalog)


@pytest.mark.parametrize("seat", ["google_bounded", "cursor_coder", "anthropic_practical"])
def test_review_role_does_not_relax_family_or_risk_exclusions(catalog, seat):
    catalog["roles"]["forbidden_review"] = {"seat": seat, "risk": "critical"}
    with pytest.raises(ModelCatalogError, match=r"outside the existing risk ladder|family exclusions"):
        validate_catalog(catalog)


def test_wire_mapping_cannot_come_from_predecessor(catalog):
    catalog["models"]["gpt-6-luna"]["routing_wire_ids"]["native_codex"] = "gpt-6.1-sol"
    with pytest.raises(ModelCatalogError, match="mismatched identity"):
        validate_catalog(catalog)
    catalog = deepcopy(load_model_catalog())
    del catalog["models"]["gpt-6-luna"]["routing_wire_ids"]
    with pytest.raises(ModelCatalogError, match="holder's own"):
        validate_catalog(catalog)


@pytest.mark.parametrize("field,value", [("effort", "ultra"), ("effort", []), ("transport", "unknown"),
    ("invocation", "dispatch --model {predecessor}"), ("invocation", "dispatch --model gpt-6-luna"),
    ("route", None), ("unapproved_flag", True)])
def test_route_errors_are_typed(catalog, field, value):
    catalog["seats"]["bounded_worker"]["routes"]["native"][field] = value
    with pytest.raises(ModelCatalogError):
        validate_catalog(catalog)


def test_duplicate_routes_labels_and_missing_legacy_coverage(catalog):
    catalog["seats"]["bounded_worker"]["routes"]["duplicate"] = deepcopy(catalog["seats"]["bounded_worker"]["routes"]["native"])
    with pytest.raises(ModelCatalogError, match="duplicate expanded routes"):
        validate_catalog(catalog)
    catalog = deepcopy(load_model_catalog())
    catalog["seats"]["xai_reviewer"]["routes"]["cursor_fallback"]["legacy_name"] = "openai_frontier"
    with pytest.raises(ModelCatalogError, match="legacy receipt labels"):
        validate_catalog(catalog)
    catalog = deepcopy(load_model_catalog())
    del catalog["seats"]["anthropic_authority"]["routes"]["cursor_fallback"]
    with pytest.raises(ModelCatalogError, match="cover every legacy"):
        validate_catalog(catalog)


def test_moving_last_resort_or_any_legacy_routing_value_is_rejected(catalog):
    catalog["seats"]["anthropic_authority"]["routes"]["cursor_fallback"]["last_resort"] = True
    with pytest.raises(ModelCatalogError, match="changes the legacy candidate"):
        validate_catalog(catalog)


def test_qualification_is_identity_and_capability_bound(catalog):
    seat = catalog["seats"]["bounded_worker"]
    seat["qualification"] = {"model_id": seat["model_id"], "bindings": seat["bindings"], "reference": "fixture:qualified"}
    assert validate_catalog(catalog)
    assert resolve_role("bounded_recon", catalog=catalog, purpose="inspect").candidates[0].qualification_reference == "fixture:qualified"
    seat["qualification"]["model_id"] = "gpt-6.1-sol"
    with pytest.raises(ModelCatalogError, match="qualification mismatches"):
        validate_catalog(catalog)


@pytest.mark.parametrize("name", ["claude-opus-5-5", "InvalidName"])
def test_seat_and_role_names_are_functional_not_versioned(catalog, name):
    catalog["roles"][name] = {"seat": "bounded_worker"}
    with pytest.raises(ModelCatalogError, match="stable functional"):
        validate_catalog(catalog)


def test_shell_api_returns_structured_evidence_and_typed_refusal(tmp_path):
    argv = [sys.executable, "-m", "scripts.review.model_catalog"]
    result = subprocess.run([*argv, "--resolve-role", "bounded_advisor"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["candidates"][0]["model_id"] == "gpt-6.1-sol"
    context = tmp_path / "context.json"
    health = tmp_path / "health.json"
    context.write_text(json.dumps({"required_capabilities": ["missing"]}))
    health.write_text(json.dumps({"codex": "unknown"}))
    result = subprocess.run([*argv, "--resolve-role", "bounded_advisor", "--purpose", "launch", "--transport", "native_codex",
        "--family", "openai", "--role-context-file", str(context), "--role-health-file", str(health)],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    row = json.loads(result.stdout)["candidates"][0]
    assert row["health"] == "unknown" and row["exclusion_reasons"] == ["required_capability_missing"]
    result = subprocess.run([*argv, "--resolve-role", "unregistered"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 2 and "unknown routing role" in result.stderr


@pytest.mark.parametrize("args,expected_status,expected_output", [
    (["--check-retired-model", "claude-opus-5-5"], 0, ""),
    (["--check-retired-model", "claude-fable-5"], 2, ""),
    (["--resolve-kimi-model", "k3"], 0, "kimi-code/k3\n"),
    (["--resolve-kimi-model", "k3", "--format", "kimicc"], 0,
     "k3\tkimi-k3[1m]\tk3\tkimicc_k3\n"),
    (["--resolve-role", "bounded_advisor"], 0, None),
    (["--resolve-role", "bounded_advisor", "--purpose", "launch"], 0, None),
    (["--resolve-role", "unregistered"], 2, ""),
])
def test_catalog_file_path_cli_in_clean_environment(tmp_path, args, expected_status, expected_output):
    script = Path(__file__).resolve().parents[2] / "scripts/review/model_catalog.py"
    result = subprocess.run(
        [sys.executable, str(script), *args], cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"}, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == expected_status, result.stderr
    assert "Traceback" not in result.stderr
    if expected_output is not None:
        assert result.stdout == expected_output
    else:
        row = json.loads(result.stdout)["candidates"][0]
        assert (row["model_id"], row["family"], row["transport"]) == (
            "gpt-6.1-sol", "openai", "native_codex",
        )
        if "launch" in args:
            assert row["argv"][row["argv"].index("--model") + 1] == row["wire_id"]
    if expected_status == 2:
        assert ("is retired" if "--check-retired-model" in args else "unknown routing role") in result.stderr
    else:
        assert result.stderr == ""


@pytest.mark.parametrize("index", range(len(APPROVED_INPUTS["reviewer"])))
def test_frozen_complete_reviewer_receipts(index, tmp_path, monkeypatch):
    case = deepcopy(APPROVED_INPUTS["reviewer"][index])
    for key in ("required_capabilities", "subject_seats", "subject_families", "author_families"):
        if key in case:
            case[key] = frozenset(case[key])
    if "owned_paths" in case:
        case["owned_paths"] = tuple(case["owned_paths"])
    monkeypatch.setattr(credit_lane, "routing_facts", partial(credit_lane.routing_facts,
                        now=CAPTURE["FIXED_NOW"], usage_dir=tmp_path / "usage"))
    monkeypatch.setattr(credit_lane, "published_credit_relief", partial(credit_lane.published_credit_relief,
                        now=CAPTURE["FIXED_NOW"]))
    actual = CAPTURE["observed"](lambda: resolve_reviewer(ResolverInputs(**case)))
    assert json.loads(CAPTURE["encode"](actual)) == APPROVED_BASELINE["reviewer"][index]


def test_fixture_bytes_remain_frozen():
    raw = gzip.decompress((FIXTURE / "baseline.json.gz").read_bytes())
    assert json.loads(raw) == BASELINE
    assert INPUTS["base_sha"] == "dae3d752426d6c11c5dc82260ec07ae8164e7730"


def test_frozen_cursor_revision_has_independent_routes_at_every_risk():
    """The approved eight-row change permits native Grok and refuses Cursor."""
    indices = {index for index, case in enumerate(INPUTS["reviewer"]) if case["author_model"] == "cursor:auto"}
    assert indices == {22, 207, 392, 577, 762, 947, 1132, 1317}
    assert {(INPUTS["reviewer"][index]["review_profile"], INPUTS["reviewer"][index]["risk"]) for index in indices} == {
        (profile, risk) for profile in ("code", "infra") for risk in ("low", "medium", "high", "critical")
    }
    for index in indices:
        trace = BASELINE["reviewer"][index]["value"]["trace"]
        native_grok = next(row for row in trace if row["name"] == "grok-4.7")
        assert native_grok["status"] in {"eligible", "selected"}
        cursor = [row for row in trace if row["transport"] == "cursor"]
        catalog = BASELINE["catalog"]
        ladder = catalog["review_ladders"][INPUTS["reviewer"][index]["risk"]]
        expected_cursor = {name for rung in ladder for name in rung
            if catalog["review_candidates"][name]["transport"] == "cursor"}
        assert {row["name"] for row in cursor} == expected_cursor
        assert all(row["status"] == "excluded" and "Cursor-authored" in row["reason"] for row in cursor)
