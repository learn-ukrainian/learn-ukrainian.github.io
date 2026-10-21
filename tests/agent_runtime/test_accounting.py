"""Selector, accounting label, and observation remain distinct (#10954)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from scripts.agent_runtime.accounting import model_accounting_fields, recorded_model_accounting_fields


def test_non_agy_plain_failure_matches_frozen_accounting_control(tmp_path, monkeypatch):
    from agent_runtime import runner
    from agent_runtime.result import ParseResult
    from tests.agent_runtime.test_runner_failover import _install_fake_runtime

    expected_row, = [row for row in json.loads(
        (Path(__file__).resolve().parents[1] / "fixtures" / "accounting_10954.json").read_text()
    ) if row["case"] == "plain-failure"]
    adapter, records, events = _install_fake_runtime(monkeypatch, tmp_path, {})
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: None)
    monkeypatch.setattr(runner, "_execute_invocation_plan", lambda **k: runner._ExecutionOutcome(
        parse=ParseResult(ok=False, response="", stderr_excerpt="provider failed"),
        duration_s=0.1, returncode=1, kill_reason=None, stdout_text="", stderr_text="provider failed", liveness_paths=(),
    ))

    result = runner.invoke(expected_row["agent"], "hello", model=expected_row["pin"], cwd=tmp_path)

    assert result.ok is False
    assert result.substitution is None
    assert adapter.attempts == ["primary-model"]
    assert events == []
    record, = records
    assert record["outcome"] == "error"
    saved = json.loads(json.dumps(asdict(result)))
    for row in (saved, saved["usage_record"], record, recorded_model_accounting_fields(record)):
        assert {key: row[key] for key in expected_row["expected"]} == expected_row["expected"]
        assert row["observed_model_provenance"] == expected_row["expected_provenance"]
    assert saved["model"] == record["model"] == expected_row["model"]
    assert bool(record.get("substitution")) is expected_row["substituted"]


@pytest.mark.parametrize("identity", [None, {
    "actual_model": "primary-model", "actual_model_known": True, "source": "provider-init",
}])
def test_selector_and_plain_mapping_cannot_create_observation(identity):
    assert model_accounting_fields(requested_selector="primary-model", identity=identity) == {
        "requested_selector": "primary-model", "observed_model": None,
        "identity_state": "unknown", "observed_model_source": None, "observed_model_provenance": None,
    }


@pytest.mark.parametrize("legacy", [
    {"model": "primary-model"},
    {"model": "primary-model", "resolved_model": "primary-model", "resolved_model_known": True},
    {"substitution": {"actual_model": "primary-model", "actual_model_known": True}},
    {"model_identity": {"actual_model": "primary-model", "actual_model_known": True}},
])
def test_historical_labels_cannot_acquire_identity(legacy):
    assert recorded_model_accounting_fields(legacy) == {
        "requested_selector": None, "observed_model": None,
        "identity_state": "unknown", "observed_model_source": None, "observed_model_provenance": None,
    }


@pytest.mark.parametrize("override", [
    {"identity_state": "unknown"}, {"observed_model": None}, {"observed_model": 1},
    {"observed_model_source": "configured_request"},
    {"observed_model_provenance": None}, {"observed_model_provenance": {}},
    {"observed_model_provenance": {"requested_model": "primary-model", "invocation_id": "wrong"}},
    {"model_identity": {"actual_model_known": False}},
    {"model_identity": {"actual_model": "primary-model", "actual_model_known": True, "source": "provider-init",
                        "provenance": {"requested_model": "other-model", "invocation_id": "a" * 32}}},
    {"model_identity": {"actual_model": "primary-model", "actual_model_known": True, "source": "provider-init",
                        "provenance": {"requested_model": "primary-model", "invocation_id": "b" * 32}}},
    {"model_identity": {"actual_model": "other-model", "actual_model_known": True, "source": "provider-init"}},
])
def test_conflicting_serialized_projection_is_unknown(override):
    record = {
        "requested_selector": "primary-model", "observed_model": "primary-model",
        "identity_state": "observed", "observed_model_source": "provider-init",
        "observed_model_provenance": {"requested_model": "primary-model", "invocation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}, **override,
    }
    assert recorded_model_accounting_fields(record) == {
        "requested_selector": "primary-model", "observed_model": None,
        "identity_state": "unknown", "observed_model_source": None, "observed_model_provenance": None,
    }


@pytest.mark.parametrize("substituted", [False, True])
@pytest.mark.parametrize("agent", ["failover-test", "codex"])
def test_non_agy_normal_execution_serializes_unknown_observation(tmp_path, monkeypatch, substituted, agent):
    from agent_runtime import runner
    from agent_runtime.result import ParseResult
    from tests.agent_runtime.test_runner_failover import _install_fake_runtime

    adapter, _, _ = _install_fake_runtime(monkeypatch, tmp_path, {})
    monkeypatch.setattr(runner, "_load_adapter", lambda *a: adapter)
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: None)
    monkeypatch.setattr(runner, "_execute_invocation_plan", lambda **k: runner._ExecutionOutcome(
        parse=ParseResult(ok=True, response="ok", substitution={
            "requested_model": "primary-model", "actual_model": "fallback-model", "substituted": True,
        } if substituted else None),
        duration_s=0.1, returncode=0, kill_reason=None, stdout_text="", stderr_text="", liveness_paths=(),
    ))
    result = runner.invoke(agent, "hello", model="primary-model", cwd=tmp_path)
    saved = json.loads(json.dumps(asdict(result)))
    if agent == "codex":
        assert saved["model_identity"]["provider_observed_model"] is None
    assert saved["model"] == ("fallback-model" if substituted else "primary-model")
    expected = {
        "requested_selector": "primary-model", "observed_model": None,
        "identity_state": "unknown", "observed_model_source": None, "observed_model_provenance": None,
    }
    for row in (saved, saved["usage_record"]):
        assert {key: row[key] for key in expected} == expected


@pytest.mark.parametrize("pin", ["claude-sonnet-5-5-high", "claude-opus-5-5-high"])
def test_observation_requires_current_task_and_nonce(tmp_path, pin):
    from scripts.agent_runtime import runner
    from scripts.agent_runtime.adapters.base import InvocationPlan
    from tests.agent_runtime.adapters.test_agy_claude_routes import consistency_stream

    token = runner._AGY_OBSERVED_IDENTITY.set(None)
    try:
        identity = runner._observe_agy_identity(
            stdout=consistency_stream(pin, "matched"),
            plan=InvocationPlan(cmd=["fixture", "--model", pin], cwd=tmp_path),
            task_id="accounting-task", run_nonce="accounting-run", invocation_id="a" * 32,
            cli_sha256="b" * 64, cli_version="fixture",
        )
    finally:
        runner._AGY_OBSERVED_IDENTITY.reset(token)
    assert identity is not None
    for task_id, nonce, expected_model in [
        ("accounting-task", "accounting-run", pin),
        ("another-task", "accounting-run", None),
        ("accounting-task", "another-run", None),
    ]:
        fields = model_accounting_fields(
            requested_selector="outer-selector", identity=identity, task_id=task_id, run_nonce=nonce,
        )
        assert fields == {
            "requested_selector": "outer-selector", "observed_model": expected_model,
            "identity_state": "observed" if expected_model else "unknown",
            "observed_model_source": "provider-init" if expected_model else None,
            "observed_model_provenance": {"requested_model": pin, "invocation_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"} if expected_model else None,
        }


@pytest.mark.parametrize("pin,other", [
    ("claude-sonnet-5-5-high", "claude-opus-5-5-high"),
    ("claude-opus-5-5-high", "claude-sonnet-5-5-high"),
])
def test_agy_real_route_failover_keeps_original_selector_and_attempt_provenance(tmp_path, monkeypatch, pin, other):
    from dataclasses import replace

    from agent_runtime import runner
    from agent_runtime.failover import FAILOVER_COOLDOWN_DB_ENV, FailoverChain, FailoverRoute
    from agent_runtime.result import ParseResult
    from tests.agent_runtime.adapters.test_agy_claude_routes import consistency_stream, mock_agy_provider

    mock_agy_provider(monkeypatch, tmp_path, runner, stdout=consistency_stream(pin, "matched"))
    chain = FailoverChain(agent_name="agy", routes=(
        FailoverRoute(provider="agy", model=pin), FailoverRoute(provider="agy", model=other),
    ), cooldown_ttl_s=600)
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **k: chain)
    monkeypatch.setenv(FAILOVER_COOLDOWN_DB_ENV, str(tmp_path / "cooldowns.sqlite3"))
    records, events, attempts = [], [], []
    monkeypatch.setattr(runner, "write_record", records.append)

    def execute(**kwargs):
        model = kwargs["model"]
        attempts.append(model)
        identity = runner._observe_agy_identity(
            stdout=consistency_stream(model, "matched"), plan=kwargs["plan"], task_id="route-task",
            run_nonce="route-run", invocation_id=("a" if model == pin else "b") * 32,
            cli_sha256="c" * 64, cli_version="fixture",
        )
        parsed = ParseResult(ok=model == other, response="READY" if model == other else "",
                             rate_limited=model == pin, failure_code="rate_limited" if model == pin else None)
        return runner._ExecutionOutcome(
            parse=replace(parsed, model_identity=identity), duration_s=0.1,
            returncode=0 if model == other else 1, kill_reason=None, stdout_text="", stderr_text="",
            liveness_paths=(),
        )

    monkeypatch.setattr(runner, "_execute_invocation_plan", execute)
    result = runner.invoke("agy", "Implement.", model=pin, mode="workspace-write", cwd=tmp_path,
                           task_id="route-task", tool_config={"run_nonce": "route-run"},
                           event_sink=lambda name, **fields: events.append((name, fields)))
    assert attempts == [pin, other]
    assert result.ok is True
    assert result.model == other
    assert result.model_identity["provenance"]["requested_model"] == other
    assert result.model_identity["provenance"]["invocation_id"] == "b" * 32
    expected = {"requested_selector": pin, "observed_model": other,
                "identity_state": "observed", "observed_model_source": "provider-init",
                "observed_model_provenance": {"requested_model": other, "invocation_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}}
    saved = json.loads(json.dumps(asdict(result)))
    for row in (saved, records[0], events[0][1]):
        assert {key: row[key] for key in expected} == expected
    assert saved["usage_record"]["model_identity"]["provenance"]["requested_model"] == other
