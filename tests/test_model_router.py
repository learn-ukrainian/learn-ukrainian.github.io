"""Author controls for #10154, not the independent 40-case integration oracle.

Pre-edit controls: 8dbf00dfccf842c26e1df54fc7da5699b4f089f1de90ea5897cdb2658e30d318.
Catalog/producer/resolver sources pinned in credit_lane and frozen before edits.
Fixtures inject collector-qualified routes; they never claim end-to-end admission.
"""

from __future__ import annotations

import copy
import itertools
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from scripts.fleet import credit_lane
from scripts.fleet import model_router as router
from scripts.review.model_catalog import load_model_catalog

NOW = datetime(2026, 10, 8, 14, tzinfo=UTC)
CATALOG = load_model_catalog()


def fixture():
    request = {
        "schema_version": "model-router-request.v1",
        "role": "designated_authorities",
        "purpose": "launch",
        "task_id": "fixture-10154",
        "prompt_sha256": "a" * 64,
        "restrictions": {},
    }
    target = {
        "schema_version": "router-target.v1",
        "role": request["role"],
        "purpose": request["purpose"],
        "task_id": request["task_id"],
        "prompt_sha256": request["prompt_sha256"],
        "target_sha": "b" * 40,
        "activity": "dispatch",
        "risk": "high",
        "review_profile": "none",
        "domain": "code",
        "data_classification": "public",
        "data_egress_policy": None,
        "required_capabilities": [],
        "isolation_required": False,
        "author_model": "gpt-6.1-sol",
        "author_family": "openai",
        "author_families": ["openai"],
        "subject_seats": [],
        "subject_families": [],
        "changed_paths": ["tests/example.py"],
        "admitted_routes": [
            {"seat": seat, "route_name": route} for seat, value in CATALOG["seats"].items() for route in value["routes"]
        ],
    }
    snapshot = {"agents": {}, "diagnostics": {"stale": False}, "subscription_applicability": []}
    for seat in CATALOG["seats"].values():
        for route in seat["routes"].values():
            lane = route["route"]
            transport = route["transport"]
            if (lane, transport) not in credit_lane.SUBSCRIPTION_SOURCES:
                continue
            sources = ["provider_windows.auto"] if lane == "cursor" else ["windows.primary", "windows.secondary"]
            if lane == "cursor" and seat["model_id"].startswith("claude-"):
                sources = ["claude_gpt_windows.five_hour", "claude_gpt_windows.weekly"]
            record = snapshot["agents"].setdefault(
                lane,
                {
                    "health": {"healthy": True},
                    "status": "cool",
                    "eligible": True,
                    "runtime": {"rate_limited": 0},
                    "scheduler": {},
                    "codexbar": {"fetched_at": (NOW - timedelta(seconds=30)).isoformat(), "stale": False},
                },
            )
            declarations = []
            for source in sources:
                group, key = source.split(".")
                # Half the actual declared window has elapsed; 80% allowance is
                # positive slack. No production 5h/week duration assumption.
                record["codexbar"].setdefault(group, {})[key] = {
                    "remaining_pct": 80.0,
                    "used_pct": 20.0,
                    "resets_at": (NOW + timedelta(hours=2)).isoformat(),
                    "window_minutes": 240,
                }
                declarations.append(
                    {
                        "source": source,
                        "bucket": f"{lane}.{source}",
                        "scope": "shared",
                        "model": None,
                        "pool": "subscription",
                        "applicable": True,
                        "required": True,
                    }
                )
            snapshot["subscription_applicability"].append(
                {
                    "lane": lane,
                    "model": seat["model_id"],
                    "transport": transport,
                    "producer_digest": credit_lane.SUBSCRIPTION_SOURCE_DIGEST,
                    "catalog_digest": credit_lane.SUBSCRIPTION_CATALOG_DIGEST,
                    "max_age_s": 900,
                    "windows": declarations,
                }
            )
    policy = {
        "schema_version": "router-policy.v1",
        "policy_epoch": "fixture",
        "campaigns": [],
        "manual_spend_authorization": {"enabled": False},
        "window_metadata": {},
    }
    return request, target, snapshot, policy


def select(data, *, catalog=CATALOG, now=NOW):
    request, target, snapshot, policy = copy.deepcopy(data)
    if "role" in target and "role" in request:
        target["role"] = request["role"]
    if "purpose" in target and "purpose" in request:
        target["purpose"] = request["purpose"]
    return router.select_route(
        request, trusted_facts=target, catalog=catalog, snapshot=snapshot, policy=policy, now=now
    )


def subscription(data, lane="codex", model="gpt-6.1-sol", transport="native_codex"):
    snapshot = data[2]
    declaration = next(
        entry
        for entry in snapshot["subscription_applicability"]
        if (entry["lane"], entry["model"], entry["transport"]) == (lane, model, transport)
    )
    return snapshot["agents"][lane], declaration


def review_fixture():
    data = fixture()
    data[0]["role"] = "code_review_critical"
    data[1].update(activity="review", risk="critical", review_profile="code", required_capabilities=["code_review"])
    return data


def test_closed_schema_exports_and_selected_binding():
    data = fixture()
    before = copy.deepcopy(data)
    decision = select(data)
    assert decision["status"] == "selected", decision
    assert decision["model"] == "claude-opus-5-5"  # equal tier/slack; lexical claude before codex
    assert decision["target_sha"] == data[1]["target_sha"]
    assert decision["trusted_facts_sha256"] == router.canonical_digest(data[1])
    assert decision["snapshot_sha256"] == router.canonical_digest(data[2])
    assert data == before
    for name, expected in [("request", router.REQUEST_SCHEMA), ("decision", router.DECISION_SCHEMA)]:
        stored = json.loads(
            (Path(__file__).resolve().parents[1] / f"schemas/model-router-{name}.schema.json").read_text()
        )
        assert stored == expected
        Draft202012Validator.check_schema(stored)
    Draft202012Validator(router.DECISION_SCHEMA, format_checker=FormatChecker()).validate(decision)


@pytest.mark.parametrize("key", ["schema_version", "role", "purpose", "task_id", "prompt_sha256", "restrictions"])
def test_request_missing_required(key):
    data = fixture()
    del data[0][key]
    assert select(data)["code"] == "REQUEST_INVALID"


@pytest.mark.parametrize(
    "change",
    [
        {"authority": True},
        {"target_sha": "c" * 40},
        {"role": "unknown"},
        {"purpose": "spend"},
        {"restrictions": {"spend_authorized": True}},
        {"restrictions": {"required_capabilities": "Sources"}},
    ],
)
def test_request_negative_controls(change):
    data = fixture()
    data[0].update(change)
    assert select(data)["status"] == "refused"


@pytest.mark.parametrize("key", list(router.TARGET_SCHEMA["properties"]))
def test_target_missing_required(key):
    data = fixture()
    del data[1][key]
    assert select(data)["code"] == "TARGET_FACTS_MISSING"


@pytest.mark.parametrize(
    "change,code",
    [
        ({"task_id": "other"}, "TARGET_BINDING_MISMATCH"),
        ({"prompt_sha256": "f" * 64}, "TARGET_BINDING_MISMATCH"),
        ({"data_classification": "secret"}, "DATA_EGRESS_REFUSED"),
        ({"data_classification": "local_only"}, "DATA_EGRESS_REFUSED"),
        ({"admitted_routes": []}, "NO_ELIGIBLE_ROUTE"),
        ({"changed_paths": ["agents_extensions/shared/hooks/guard-reviewer-publish.py"]}, "SUBJECT_SCOPE_AMBIGUOUS"),
        ({"subject_seats": ["not-a-seat"]}, "SUBJECT_SCOPE_AMBIGUOUS"),
    ],
)
def test_target_negative_controls(change, code):
    data = fixture()
    data[1].update(change)
    assert select(data)["code"] == code


@pytest.mark.parametrize("families", [[], ["unknown"], ["cursor_auto_union"], ["openai", "ambiguous"], ["anthropic"]])
def test_unknown_conflicting_author_refuses_review(families):
    data = review_fixture()
    data[1]["author_families"] = families
    assert select(data)["status"] == "refused"


def test_all_authors_excluded_alias_cannot_bypass_review():
    data = review_fixture()
    data[0]["role"] = "legacy_reviewers"
    data[1]["author_families"] = ["openai", "anthropic", "xai"]
    assert select(data)["code"] == "NO_ELIGIBLE_ROUTE"
    data[0]["role"] = "bounded_fallback"  # Gemini cannot code-review through an alias
    assert select(data)["code"] == "NO_ELIGIBLE_ROUTE"


def test_review_independence_subject_and_security_risk():
    data = review_fixture()
    data[1]["risk"] = "low"
    data[1]["changed_paths"] = ["start-worker.sh", "tests/example.py"]
    data[1]["subject_seats"] = ["grok"]
    decision = select(data)
    assert decision["model"] == "claude-opus-5-5"
    data[1]["subject_families"] = ["anthropic"]
    assert select(data)["status"] == "refused"


@pytest.mark.parametrize(
    "restrictions",
    [
        {"required_capabilities": ["sources_mcp"]},
        {"excluded_families": ["openai", "anthropic"]},
        {"excluded_seats": ["openai_frontier", "anthropic_authority"]},
        {"model": "gpt-6-luna"},
        {"transport": "proxy"},
    ],
)
def test_caller_restrictions_can_only_narrow(restrictions):
    data = fixture()
    data[0]["restrictions"] = restrictions
    assert select(data)["status"] == "refused"


def test_isolation_union_and_pin():
    data = fixture()
    data[1]["isolation_required"] = True
    data[0]["restrictions"] = {"isolation_required": False, "model": "claude-opus-5-5", "risk": "low"}
    decision = select(data)
    assert decision["model"] == "claude-opus-5-5"
    assert decision["transport"] == "native_claude"


@pytest.mark.parametrize("fault", ["stale", "missing", "exhausted", "no_duration", "bad_applicability", "unhealthy"])
def test_bad_candidate_does_not_poison_fresh_alternative(fault):
    data = fixture()
    record, declaration = subscription(data)
    if fault == "stale":
        record["codexbar"]["fetched_at"] = (NOW - timedelta(hours=1)).isoformat()
    elif fault == "missing":
        del data[2]["agents"]["codex"]
    elif fault == "exhausted":
        record["codexbar"]["windows"]["primary"].update(remaining_pct=0, used_pct=100)
    elif fault == "no_duration":
        del record["codexbar"]["windows"]["primary"]["window_minutes"]
    elif fault == "bad_applicability":
        declaration["producer_digest"] = "0" * 64
    else:
        record["health"]["healthy"] = False
    assert select(data)["model"] == "claude-opus-5-5"


@pytest.mark.parametrize(
    "fault",
    [
        {"eligible": False},
        {"login_state": "NEED_LOGIN"},
        {"health": {}},
        {"runtime": {"headroom_blocked": True}},
        {"runtime": {"rate_limited": 1}},
        {"runtime": {"circuit_open": True}},
        {"scheduler": {"capacity_exhausted": True}},
        {"scheduler": {"circuit_open": True}},
        {"circuit_open": True},
        {"runtime": None},
        {"status": "hot", "status_source": "cursor_auto"},
    ],
)
def test_runtime_health_throttle_restrictions(fault):
    data = fixture()
    for lane in ("claude", "codex", "cursor"):
        data[2]["agents"][lane].update(fault)
    assert select(data)["status"] == "refused"


@pytest.mark.parametrize("inventory", list(itertools.product([None, 0, 1000000, "unreadable"], [None, 0, 99])))
@pytest.mark.parametrize("remaining", [80, 10, 0])
def test_inventory_never_changes_selection_or_refusal(inventory, remaining):
    data = fixture()
    for record in data[2]["agents"].values():
        for group in ("windows", "provider_windows", "claude_gpt_windows"):
            for window in record["codexbar"].get(group, {}).values():
                window.update(remaining_pct=remaining, used_pct=100 - remaining)
    expected = select(data)
    for record in data[2]["agents"].values():
        record["credit_balance"], record["reset_credits"] = inventory
        record["credit"] = {"state": "credit_balance_present", "private": "SENTINEL"}
        record["reset_advice"] = {"action": "use_reset_now"}
    data[3]["manual_spend_authorization"]["enabled"] = True
    actual = select(data)
    assert (actual["status"], actual.get("model"), actual.get("code")) == (
        expected["status"],
        expected.get("model"),
        expected.get("code"),
    )
    assert "SENTINEL" not in json.dumps(actual)


def test_campaign_active_boundary_and_equivalent_fit_priority():
    data = fixture()
    data[3]["campaigns"] = [
        {
            "id": "expiring",
            "models": ["gpt-6.1-sol"],
            "lanes": ["codex"],
            "starts_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(seconds=90)).isoformat(),
        }
    ]
    selected = select(data)
    assert selected["model"] == "gpt-6.1-sol"
    assert selected["expires_at"] == "2026-10-08T14:01:30Z"
    assert select(data, now=NOW + timedelta(seconds=90))["model"] == "claude-opus-5-5"
    data[3]["campaigns"][0]["starts_at"] = (NOW + timedelta(seconds=1)).isoformat()
    assert select(data)["model"] == "claude-opus-5-5"


def test_campaign_cannot_rescue_exhaustion_or_quality():
    data = fixture()
    data[0]["role"] = "legacy_reviewers"
    data[3]["campaigns"] = [
        {
            "id": "expiring",
            "models": ["claude-sonnet-5-5"],
            "lanes": ["claude"],
            "starts_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(seconds=90)).isoformat(),
        }
    ]
    assert select(data)["model"] in {"gpt-6.1-sol", "claude-opus-5-5"}
    record, _ = subscription(data)
    record["codexbar"]["windows"]["primary"].update(remaining_pct=0, used_pct=100)
    data[3]["campaigns"][0]["models"] = ["gpt-6.1-sol"]
    data[3]["campaigns"][0]["lanes"] = ["codex"]
    assert select(data)["model"] != "gpt-6.1-sol"


def test_earliest_campaign_expiry_and_input_order_invariance():
    data = fixture()
    for model, lane, seconds in [("gpt-6.1-sol", "codex", 90), ("claude-opus-5-5", "claude", 60)]:
        data[3]["campaigns"].append(
            {
                "id": lane,
                "models": [model],
                "lanes": [lane],
                "starts_at": NOW.isoformat(),
                "expires_at": (NOW + timedelta(seconds=seconds)).isoformat(),
            }
        )
    assert select(data)["model"] == "claude-opus-5-5"
    data[3]["campaigns"].reverse()
    data[2]["subscription_applicability"].reverse()
    data[1]["admitted_routes"].reverse()
    assert select(data)["model"] == "claude-opus-5-5"


def test_pace_owned_by_normalizer_and_review_retention():
    data = fixture()
    record, _ = subscription(data, "claude", "claude-opus-5-5", "native_claude")
    # Lower percent can have greater slack: the allowance percentage alone is
    # not worst pace. Codex 80%-50%=30%; Claude 60%-10%=50%.
    for window in record["codexbar"]["windows"].values():
        window.update(remaining_pct=60, used_pct=40, window_minutes=1200)
    assert select(data)["model"] == "claude-opus-5-5"
    data = review_fixture()
    for record in data[2]["agents"].values():
        record.update(status="hot", status_source="weekly_pace")
        for group in ("windows", "provider_windows", "claude_gpt_windows"):
            for window in record["codexbar"].get(group, {}).values():
                window.update(remaining_pct=20, used_pct=80)
    assert select(data)["status"] == "selected"  # review debt is ordering-only
    data[1]["activity"] = "dispatch"
    assert select(data)["status"] == "refused"  # writer throttling retained


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d[3].update(private="SENTINEL"),
        lambda d: d[3]["campaigns"].append(
            {"id": "bad", "models": [], "lanes": ["codex"], "starts_at": NOW.isoformat(), "expires_at": NOW.isoformat()}
        ),
        lambda d: d[2].update(raw_private="SENTINEL"),
        lambda d: d[2].update(subscription_applicability=None),
        lambda d: d[3]["window_metadata"].update(credit_balance=float("nan")),
    ],
)
def test_invalid_private_inputs_safe_closed_refusal(mutate):
    data = fixture()
    mutate(data)
    decision = select(data)
    assert decision["status"] == "refused"
    assert "SENTINEL" not in json.dumps(decision)
    Draft202012Validator(router.DECISION_SCHEMA).validate(decision)


def test_clock_catalog_drift_and_digest_validation():
    assert select(fixture(), now=NOW.replace(tzinfo=None))["code"] == "CLOCK_INVALID"
    catalog = copy.deepcopy(CATALOG)
    catalog["reviewed_on"] = "2026-10-07"
    assert select(fixture(), catalog=catalog)["code"] == "CATALOG_RESOLVER_MISMATCH"
    with pytest.raises(ValueError):
        router.canonical_digest({"bad": float("nan")})


def test_effects_intercepted(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("pure selector attempted external effect")

    monkeypatch.setattr(credit_lane, "load_policy", forbidden)
    monkeypatch.setattr(credit_lane, "read_recent_rate_limits", forbidden)
    monkeypatch.setattr(credit_lane, "read_routing_budget", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    assert select(fixture())["status"] == "selected"


def test_decision_schema_negative_controls():
    validator = Draft202012Validator(router.DECISION_SCHEMA, format_checker=FormatChecker())
    decision = select(fixture())
    for key in decision:
        altered = dict(decision)
        del altered[key]
        assert not validator.is_valid(altered), key
    for change in [
        {"private": "SENTINEL"},
        {"effort": "low"},
        {"model": "bad\nmodel"},
        {"status": "done"},
        {"snapshot_sha256": "bad"},
        {"expires_at": "tomorrow"},
    ]:
        assert not validator.is_valid({**decision, **change})


def test_primary_transport_precedes_same_model_boosted_fallback():
    data = review_fixture()
    data[1]["subject_families"] = ["anthropic"]
    data[2]["agents"]["cursor"]["codexbar"].pop("claude_gpt_windows")
    data[3]["campaigns"] = [
        {
            "id": "cursor-boost",
            "models": ["grok-4.7"],
            "lanes": ["cursor"],
            "starts_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(seconds=60)).isoformat(),
        }
    ]
    assert select(data)["transport"] == "native_grok"
    data[2]["agents"]["grok"]["health"]["healthy"] = False
    assert select(data)["transport"] == "cursor"


def test_candidate_key_hard_fit_quality_before_resources():
    from types import SimpleNamespace

    facts = credit_lane.SubscriptionFacts("verified", "SUBSCRIPTION_FRESH", 0.2, 80)
    candidates = router.resolve_role("legacy_reviewers", catalog=CATALOG, purpose="inspect").candidates
    practical = next(candidate for candidate in candidates if candidate.model_id == "claude-sonnet-5-5")
    authority = next(candidate for candidate in candidates if candidate.model_id == "claude-opus-5-5")
    good = router._candidate_key(authority, catalog=CATALOG, suitability=0, facts=facts, campaign=None)
    boosted = router._candidate_key(practical, catalog=CATALOG, suitability=0, facts=facts, campaign=NOW)
    assert good < boosted
    groups = {
        (False, 1, 2, False): [
            (
                SimpleNamespace(name="primary", family="anthropic", transport_fallback_for=None),
                SimpleNamespace(selection_score=(999,)),
                0,
            )
        ],
        (True, 0, 1, False): [
            (
                SimpleNamespace(name="fallback", family="openai", transport_fallback_for=None),
                SimpleNamespace(selection_score=(0,)),
                1,
            )
        ],
    }
    assert router.reviewers._best_eligible(groups)[2] == 0


def test_immutable_injected_inputs():
    class FrozenDict(dict):
        def __deepcopy__(self, memo):
            return {key: copy.deepcopy(value, memo) for key, value in self.items()}

        def __setitem__(self, key, value):
            raise AssertionError("mutated input mapping")

        def update(self, *args, **kwargs):
            raise AssertionError("mutated input mapping")

    class FrozenList(list):
        def __deepcopy__(self, memo):
            return [copy.deepcopy(value, memo) for value in self]

        def __setitem__(self, key, value):
            raise AssertionError("mutated input list")

        def append(self, value):
            raise AssertionError("mutated input list")

        def sort(self, *args, **kwargs):
            raise AssertionError("mutated input list")

    def freeze(value):
        if isinstance(value, dict):
            return FrozenDict({key: freeze(item) for key, item in value.items()})
        if isinstance(value, list):
            return FrozenList(freeze(item) for item in value)
        return value

    inputs = tuple(freeze(value) for value in fixture())
    assert (
        router.select_route(
            inputs[0], trusted_facts=inputs[1], catalog=freeze(CATALOG), snapshot=inputs[2], policy=inputs[3], now=NOW
        )["status"]
        == "selected"
    )


@pytest.mark.parametrize(
    "change",
    [
        {"id": "repeat"},
        {"starts_at": "tomorrow"},
        {"expires_at": "yesterday"},
        {"models": []},
        {"lanes": []},
    ],
)
def test_campaign_malformed_or_duplicate_refuses_without_private_reason(change):
    data = fixture()
    campaign = {
        "id": "repeat",
        "models": ["gpt-6.1-sol"],
        "lanes": ["codex"],
        "starts_at": NOW.isoformat(),
        "expires_at": (NOW + timedelta(seconds=60)).isoformat(),
    }
    data[3]["campaigns"] = [campaign, {**campaign, "id": "second", **change}]
    assert select(data)["code"] == "INPUT_INVALID"


def test_snapshot_missing_declaration_duplicate_or_nonobject():
    for change in [
        lambda d: d[2]["subscription_applicability"].clear(),
        lambda d: d[2]["subscription_applicability"].extend(copy.deepcopy(d[2]["subscription_applicability"])),
        lambda d: d[2].update(agents=None),
        lambda d: d[2]["agents"].update(claude=None, codex=None, cursor=None),
    ]:
        data = fixture()
        change(data)
        assert select(data)["status"] == "refused"


def test_unsupported_review_profile_is_explicit():
    data = review_fixture()
    data[1]["review_profile"] = "ukrainian"
    assert select(data)["code"] == "REVIEW_PROFILE_UNSUPPORTED"


def test_consult_reuses_actual_catalog_activity_roles():
    for role in ["bounded_recon", "routine_mechanical", "readonly_recon"]:
        data = fixture()
        data[0]["role"] = role
        data[1]["activity"] = "consult"
        decision = select(data)
        assert decision["status"] == "selected"
        assert router.activity_role_refusal(decision["model"], "consult", CATALOG) is None
        assert decision["model"] != "claude-haiku-5-5"
    data[0]["restrictions"] = {"model": "claude-haiku-5-5"}
    assert select(data)["status"] == "refused"


@pytest.mark.parametrize("field", ["role", "purpose"])
def test_request_cannot_replace_trusted_role_or_purpose(field):
    request, target, snapshot, policy = fixture()
    target[field] = "bounded_recon" if field == "role" else "inspect"
    result = router.select_route(
        request, trusted_facts=target, catalog=CATALOG, snapshot=snapshot, policy=policy, now=NOW
    )
    assert result["code"] == "TARGET_BINDING_MISMATCH"


@pytest.mark.parametrize("status", ["unavailable", "unknown", "unhealthy", "near_cap", "unsupported"])
def test_contradictory_usage_status_never_creates_capacity(status):
    data = fixture()
    for record in data[2]["agents"].values():
        record["status"] = status
    assert select(data)["status"] == "refused"


def test_pure_existing_review_gate_negative_controls():
    from types import SimpleNamespace

    _, target, _, _ = review_fixture()
    context = {"required_capabilities": [], "isolation_required": False}
    candidates = router.resolve_role("legacy_reviewers", catalog=CATALOG, purpose="inspect").candidates
    native = {candidate.model_id: candidate for candidate in candidates if candidate.transport != "cursor"}
    assert router._review_gate(SimpleNamespace(legacy_label=None), target, context, "critical") is None
    assert router._review_gate(native["gpt-6.1-sol"], target, context, "critical") is None  # same family
    assert router._review_gate(native["claude-sonnet-5-5"], target, context, "high") is None
    target["subject_seats"] = ["cursor"]
    assert router._review_gate(native["grok-4.7"], target, context, "critical") is None
    target["subject_seats"] = []
    target["changed_paths"] = ["curriculum/a1/example.yaml"]
    assert router._review_gate(native["grok-4.7"], target, context, "critical") is None
    target["required_capabilities"] = ["shell_execution"]
    context["required_capabilities"] = ["shell_execution"]
    assert router._review_gate(native["grok-4.7"], target, context, "critical") is None


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -1, 101, True, "bad", 10**400])
def test_invalid_numeric_candidate_does_not_poison_fresh_alternative(invalid):
    data = fixture()
    record, _ = subscription(data)
    record["codexbar"]["windows"]["primary"]["remaining_pct"] = invalid
    assert select(data)["model"] == "claude-opus-5-5"


def test_invalid_inventory_is_never_allowance():
    data = fixture()
    expected = select(data)["model"]
    for record in data[2]["agents"].values():
        record["credit_balance"] = float("nan")
        record["reset_credits"] = float("inf")
    assert select(data)["model"] == expected


@pytest.mark.parametrize("model,lane", [("unknown", "codex"), ("gpt-6.1-sol", "proxy"), ("gpt-6.1-sol", "claude")])
def test_campaign_requires_catalog_qualified_model_lane_scope(model, lane):
    data = fixture()
    data[3]["campaigns"] = [
        {
            "id": "bad-scope",
            "models": [model],
            "lanes": [lane],
            "starts_at": NOW.isoformat(),
            "expires_at": (NOW + timedelta(seconds=90)).isoformat(),
        }
    ]
    assert select(data)["code"] == "INPUT_INVALID"


def test_pace_slack_ranks_without_inventing_an_admission_threshold():
    data = fixture()
    for record in data[2]["agents"].values():
        for group in ("windows", "provider_windows", "claude_gpt_windows"):
            for window in record["codexbar"].get(group, {}).values():
                window.update(remaining_pct=20, used_pct=80)
    assert select(data)["status"] == "selected"
    # An actual writer throttle still refuses; campaign preference cannot lift it.
    for record in data[2]["agents"].values():
        record.update(status="hot", status_source="weekly_pace")
    assert select(data)["status"] == "refused"
