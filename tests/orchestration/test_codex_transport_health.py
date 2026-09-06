"""Native health requires invocation-bound completion and exact final output."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.agent_runtime.errors import (
    AgentRuntimeError,
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from scripts.agent_runtime.result import Result
from scripts.orchestration.codex_transport_health import (
    DEFAULT_EFFORT,
    DEFAULT_MODEL,
    DEGRADED,
    HEALTHY,
    RESERVED_SCHEMA_FAILURE,
    SCHEMA_VERSION,
    UNKNOWN,
    current_transport_health,
    probe_codex_transport,
)


def _write_config(path: Path, namespace: str = "agents") -> None:
    path.write_text(f'[features.multi_agent_v2]\ntool_namespace = "{namespace}"\n')


def _result(prompt: str, **changes) -> Result:
    result = Result(
        ok=True,
        agent="codex",
        model=DEFAULT_MODEL,
        mode="read-only",
        response=prompt.rsplit(" ", 1)[-1],
        stderr_excerpt=None,
        duration_s=1,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        effort=DEFAULT_EFFORT,
    )
    return replace(result, **changes)


@pytest.fixture
def probe_args(tmp_path):
    config = tmp_path / "config.toml"
    _write_config(config)
    return {"config_path": config, "receipt_path": tmp_path / "health.json", "runtime_repo_root": tmp_path}


def test_probe_uses_fresh_native_read_only_invocation(probe_args):
    observed = {}

    def invoker(agent, prompt, **kwargs):
        observed.update(agent=agent, prompt=prompt, **kwargs)
        return _result(prompt)

    result = probe_codex_transport(**probe_args, force_fresh=True, invoker=invoker)
    assert result["status"] == HEALTHY
    assert result["fresh"] is True
    assert result["failure_class"] is None
    assert observed["agent"] == "codex"
    assert observed["mode"] == "read-only"
    assert observed["session_id"] is None
    assert observed["tool_config"] is None
    assert observed["entrypoint"] == "codex-transport-health"
    assert observed["hard_timeout"] == 120
    assert observed["model"] == DEFAULT_MODEL
    assert observed["effort"] == DEFAULT_EFFORT
    stored_text = probe_args["receipt_path"].read_text()
    stored = json.loads(stored_text)
    assert stored["source"] == "fresh_native_probe"
    assert stored["schema_version"] == SCHEMA_VERSION
    assert "prompt" not in stored and "response" not in stored
    assert observed["prompt"].rsplit(" ", 1)[-1] not in stored_text


@pytest.mark.parametrize("kind", ["echo", "substring", "wrong", "partial", "nonzero_partial"])
def test_non_final_or_partial_output_is_not_healthy(probe_args, kind):
    def invoker(_agent, prompt, **_kwargs):
        sentinel = prompt.rsplit(" ", 1)[-1]
        if kind == "echo":
            return _result(prompt, response=prompt)
        if kind == "substring":
            return _result(prompt, response=f"answer: {sentinel}")
        if kind == "wrong":
            return _result(prompt, response="another nonce")
        return _result(prompt, ok=False, returncode=-9 if kind == "nonzero_partial" else 0)

    result = probe_codex_transport(**probe_args, invoker=invoker)
    assert result["status"] == DEGRADED
    assert result["failure_class"] == "fresh_codex_probe_failed"


def test_proven_native_recovery_is_healthy(probe_args):
    # Native adapter tests separately prove that ok=True on -9 requires an
    # invocation-bound task_complete event. Health preserves that guarantee.
    result = probe_codex_transport(
        **probe_args, invoker=lambda _agent, prompt, **_kwargs: _result(prompt, returncode=-9)
    )
    assert result["status"] == HEALTHY


@pytest.mark.parametrize(
    "changes",
    [
        {"agent": "other"},
        {"model": "other"},
        {"effort": "high"},
        {"substitution": {"substituted": True}},
    ],
)
def test_native_identity_must_match(probe_args, changes):
    result = probe_codex_transport(**probe_args, invoker=lambda _agent, prompt, **_kwargs: _result(prompt, **changes))
    assert result["status"] == DEGRADED
    assert result["failure_class"] == "native_probe_identity_mismatch"


def test_reserved_schema_failure_is_sanitized(probe_args):
    error = "Invalid tools: collaboration.spawn_agent is reserved for use by this model; private-detail"
    result = probe_codex_transport(
        **probe_args,
        invoker=lambda _agent, prompt, **_kwargs: _result(prompt, ok=False, response="", stderr_excerpt=error),
    )
    assert result["status"] == DEGRADED
    assert result["failure_class"] == RESERVED_SCHEMA_FAILURE
    assert "private-detail" not in probe_args["receipt_path"].read_text()


@pytest.mark.parametrize(
    "error,failure",
    [
        (AgentTimeoutError("codex", 1), "fresh_codex_probe_timeout"),
        (AgentStalledError("codex", 1, 2), "fresh_codex_probe_timeout"),
        (RateLimitedError("codex", DEFAULT_MODEL, "private-detail"), "codex_rate_limited"),
        (AgentUnavailableError("private-detail"), "codex_cli_unavailable"),
        (FileNotFoundError("private-detail"), "codex_cli_unavailable"),
        (ValueError("private-detail"), "invalid_native_probe_configuration"),
        (AgentRuntimeError("private-detail"), "fresh_codex_probe_failed"),
    ],
)
def test_runtime_errors_are_classified_without_bodies(probe_args, error, failure):
    def invoker(*_args, **_kwargs):
        raise error

    result = probe_codex_transport(**probe_args, invoker=invoker)
    assert result["status"] == DEGRADED
    assert result["failure_class"] == failure
    assert "private-detail" not in probe_args["receipt_path"].read_text()


def _cache(probe_args, now, **changes):
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": HEALTHY,
        "checked_at": (now - timedelta(seconds=30)).isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "model": DEFAULT_MODEL,
        "effort": DEFAULT_EFFORT,
        "task_id": "cached",
        "failure_class": None,
        "source": "fresh_native_probe",
    }
    payload.update(changes)
    probe_args["receipt_path"].write_text(json.dumps(payload))


def test_valid_cache_does_not_invoke(probe_args):
    now = datetime(2026, 9, 6, tzinfo=UTC)
    _cache(probe_args, now)

    def unexpected(*_args, **_kwargs):
        raise AssertionError("valid cache should prevent paid invocation")

    result = probe_codex_transport(**probe_args, now=now, invoker=unexpected)
    assert result["status"] == HEALTHY
    assert result["fresh"] is True
    assert result["age_seconds"] == 30


@pytest.mark.parametrize(
    "changes",
    [
        {"model": "old-model"},
        {"effort": "high"},
        {"schema_version": "codex-transport-health.v1", "source": "fresh_bridge_probe"},
    ],
)
def test_cache_identity_and_legacy_receipts_require_new_invocation(probe_args, changes):
    now = datetime(2026, 9, 6, tzinfo=UTC)
    _cache(probe_args, now, **changes)
    observed = []

    def invoker(_agent, prompt, **_kwargs):
        observed.append(prompt)
        return _result(prompt)

    result = probe_codex_transport(**probe_args, now=now, invoker=invoker)
    assert result["status"] == HEALTHY
    assert len(observed) == 1


def test_stale_receipt_is_unknown(probe_args):
    now = datetime(2026, 9, 6, tzinfo=UTC)
    _cache(probe_args, now, expires_at=(now - timedelta(seconds=1)).isoformat())
    result = current_transport_health(
        receipt_path=probe_args["receipt_path"], config_path=probe_args["config_path"], now=now
    )
    assert result["status"] == UNKNOWN
    assert result["fresh"] is False
    assert result["failure_class"] == "stale_probe_receipt"


def test_invalid_namespace_refuses_before_invocation(probe_args):
    _write_config(probe_args["config_path"], "collaboration")

    def unexpected(*_args, **_kwargs):
        raise AssertionError("invalid namespace must fail before paid invocation")

    result = probe_codex_transport(**probe_args, invoker=unexpected)
    assert result["status"] == DEGRADED
    assert result["failure_class"] == "invalid_tool_namespace"
    assert result["namespace_valid"] is False
