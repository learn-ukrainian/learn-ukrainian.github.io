"""Runner-level failover tests for agent_runtime."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime import runner as runner_mod
from agent_runtime.adapters.base import InvocationPlan
from agent_runtime.errors import AgentStalledError, RateLimitedError
from agent_runtime.failover import (
    FAILOVER_CONFIG_ENV,
    FAILOVER_COOLDOWN_DB_ENV,
    RUNNER_FAILOVER_MARKER,
)
from agent_runtime.result import ParseResult
from agent_runtime.routes import RUNTIME_ROUTE_TOOL_CONFIG_KEY


class _FailoverTestAdapter:
    name = "failover-test"
    default_model = "primary-model"
    supported_modes = frozenset({"read-only", "workspace-write", "danger"})

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def build_invocation(
        self,
        *,
        prompt: str,
        mode: str,
        cwd: Path,
        model: str | None,
        task_id: str | None,
        session_id: str | None,
        tool_config: dict | None,
        effort: str | None = None,
    ) -> InvocationPlan:
        _ = prompt
        _ = mode
        _ = task_id
        _ = session_id
        _ = effort
        route = dict((tool_config or {}).get(RUNTIME_ROUTE_TOOL_CONFIG_KEY) or {})
        route_model = str(route.get("model") or model or self.default_model)
        self.attempts.append(route_model)
        return InvocationPlan(
            cmd=["fake-agent", route_model],
            cwd=cwd,
            metadata={"route": route},
        )

    def parse_response(
        self,
        *,
        stdout: str,
        stderr: str,
        returncode: int,
        output_file: Path | None,
        plan: InvocationPlan | None = None,
        call_start_time: float | None = None,
    ) -> ParseResult:
        _ = stdout
        _ = stderr
        _ = returncode
        _ = output_file
        _ = plan
        _ = call_start_time
        raise AssertionError("_execute_invocation_plan is stubbed in these tests")

    def liveness_signal_paths(self, plan: InvocationPlan) -> tuple[Path, ...]:
        _ = plan
        return ()


@pytest.fixture(autouse=True)
def _clear_adapter_cache():
    runner_mod._ADAPTER_CACHE.clear()
    yield
    runner_mod._ADAPTER_CACHE.clear()


def _write_failover_config(tmp_path: Path, *, forbidden: bool = False) -> Path:
    fallback_provider = "zai" if forbidden else "fallback-provider"
    fallback_model = "glm-4.6" if forbidden else "fallback-model"
    config_path = tmp_path / "agent_runtime_failover.yaml"
    config_path.write_text(
        "\n".join(
            [
                "chains:",
                "  failover-test:",
                "    cooldown_ttl_s: 600",
                "    routes:",
                "      - provider: primary-provider",
                "        model: primary-model",
                f"      - provider: {fallback_provider}",
                f"        model: {fallback_model}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return config_path


def _install_fake_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    outcomes_by_model: dict[str, dict[str, Any]],
    *,
    forbidden_config: bool = False,
) -> tuple[_FailoverTestAdapter, list[dict[str, Any]], list[tuple[str, dict[str, Any]]]]:
    config_path = _write_failover_config(tmp_path, forbidden=forbidden_config)
    monkeypatch.setenv(FAILOVER_CONFIG_ENV, str(config_path))
    monkeypatch.setenv(
        FAILOVER_COOLDOWN_DB_ENV,
        str(tmp_path / "cooldowns.sqlite3"),
    )

    adapter = _FailoverTestAdapter()
    runner_mod._ADAPTER_CACHE["failover-test"] = adapter

    records: list[dict[str, Any]] = []
    emitted_events: list[tuple[str, dict[str, Any]]] = []
    fake_emit = types.ModuleType("telemetry.emit")
    fake_emit.emit_event = (
        lambda event_name, payload: emitted_events.append((event_name, payload))
    )
    monkeypatch.setitem(sys.modules, "telemetry.emit", fake_emit)
    monkeypatch.setattr(runner_mod, "write_record", records.append)
    monkeypatch.setattr(runner_mod, "has_headroom", lambda _agent, _model: (True, ""))
    monkeypatch.setattr(
        runner_mod,
        "resolve_invocation_telemetry",
        lambda agent_name, plan, requested_model, requested_effort: SimpleNamespace(
            model=requested_model,
            effort=requested_effort or "unknown",
            cli_version=f"{agent_name}-test",
        ),
    )

    def fake_execute(*, plan: InvocationPlan, **_kwargs: Any) -> runner_mod._ExecutionOutcome:
        route = plan.metadata["route"]
        outcome = outcomes_by_model[str(route["model"])]
        return runner_mod._ExecutionOutcome(
            parse=outcome["parse"],
            duration_s=0.01,
            returncode=outcome.get("returncode", 1),
            kill_reason=outcome.get("kill_reason"),
            stdout_text=outcome.get("stdout_text", ""),
            stderr_text=outcome.get("stderr_text", ""),
            liveness_paths=(),
        )

    monkeypatch.setattr(runner_mod, "_execute_invocation_plan", fake_execute)
    return adapter, records, emitted_events


_TRIGGER_CASES = [
    (
        "auth",
        {
            "parse": ParseResult(
                ok=False,
                response="",
                stderr_excerpt="401 unauthorized after refresh attempt failed",
            ),
            "returncode": 1,
            "stderr_text": "401 unauthorized after refresh attempt failed",
        },
    ),
    (
        "rate_limited",
        {
            "parse": ParseResult(
                ok=False,
                response="",
                stderr_excerpt="quota exceeded",
                rate_limited=True,
            ),
            "returncode": 1,
            "stderr_text": "quota exceeded",
        },
    ),
    (
        "overloaded",
        {
            "parse": ParseResult(
                ok=False,
                response="",
                stderr_excerpt="HTTP 503 overloaded",
            ),
            "returncode": 1,
            "stderr_text": "HTTP 503 overloaded",
        },
    ),
    (
        "transport",
        {
            "parse": ParseResult(
                ok=False,
                response="",
                stderr_excerpt="connection refused",
            ),
            "returncode": 1,
            "stderr_text": "connection refused",
        },
    ),
    (
        "transport",
        {
            "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
            "returncode": -9,
            "kill_reason": "initial_response_timeout",
            "stdout_text": "",
            "stderr_text": "",
        },
    ),
    (
        "transport",
        {
            "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
            "returncode": -9,
            "kill_reason": "stdout_silence_timeout",
            "stdout_text": "",
            "stderr_text": "",
        },
    ),
    (
        "empty_response",
        {
            "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
            "returncode": 0,
            "stderr_text": "",
        },
    ),
]


@pytest.mark.parametrize(("trigger_name", "primary_failure"), _TRIGGER_CASES)
def test_runner_failover_switches_for_eligible_trigger_classes(
    tmp_path,
    monkeypatch,
    capsys,
    trigger_name,
    primary_failure,
):
    sink_events: list[tuple[str, dict[str, Any]]] = []
    adapter, records, emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": primary_failure,
            "fallback-model": {
                "parse": ParseResult(ok=True, response="fallback ok"),
                "returncode": 0,
            },
        },
    )

    result = runner_mod.invoke(
        "failover-test",
        "hello",
        mode="read-only",
        cwd=tmp_path,
        event_sink=lambda name, **fields: sink_events.append((name, fields)),
    )

    assert adapter.attempts == ["primary-model", "fallback-model"]
    assert result.ok is True
    assert result.response == "fallback ok"
    assert result.substitution is not None
    assert result.substitution["requested_provider"] == "primary-provider"
    assert result.substitution["actual_provider"] == "fallback-provider"
    assert result.substitution["marker"] == RUNNER_FAILOVER_MARKER
    assert result.substitution["source"] == f"agent-runtime-failover:{trigger_name}"
    assert records[0]["substitution"]["substituted"] is True
    assert sink_events[0][0] == "agent_runtime_substitution"
    assert emitted_events[0][0] == "agent_runtime_substitution"
    assert RUNNER_FAILOVER_MARKER in capsys.readouterr().err


def test_runner_failover_does_not_switch_for_content_policy(
    tmp_path,
    monkeypatch,
    capsys,
):
    adapter, records, _emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(
                    ok=False,
                    response="",
                    stderr_excerpt="content policy refusal",
                ),
                "returncode": 1,
                "stderr_text": "content policy refusal",
            },
            "fallback-model": {
                "parse": ParseResult(ok=True, response="fallback ok"),
                "returncode": 0,
            },
        },
    )

    result = runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)

    assert adapter.attempts == ["primary-model"]
    assert result.ok is False
    assert result.substitution is None
    assert records[0]["outcome"] == "error"
    assert "substitution" not in records[0]
    assert RUNNER_FAILOVER_MARKER not in capsys.readouterr().err


def test_runner_failover_does_not_switch_for_streaming_silence_timeout(
    tmp_path,
    monkeypatch,
):
    adapter, records, _emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
                "returncode": -9,
                "kill_reason": "stdout_silence_timeout",
                "stdout_text": "partial output\n",
                "stderr_text": "",
            },
            "fallback-model": {
                "parse": ParseResult(ok=True, response="fallback ok"),
                "returncode": 0,
            },
        },
    )

    with pytest.raises(AgentStalledError) as exc_info:
        runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)

    assert exc_info.value.kind == "stdout_silence_timeout"
    assert adapter.attempts == ["primary-model"]
    assert records[0]["outcome"] == "stalled"
    assert "substitution" not in records[0]


def test_runner_failover_surfaces_substitution_when_final_route_times_out(
    tmp_path,
    monkeypatch,
    capsys,
):
    adapter, records, emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
                "returncode": -9,
                "kill_reason": "initial_response_timeout",
                "stdout_text": "",
                "stderr_text": "",
            },
            "fallback-model": {
                "parse": ParseResult(ok=False, response="", stderr_excerpt=None),
                "returncode": -9,
                "kill_reason": "initial_response_timeout",
                "stdout_text": "",
                "stderr_text": "",
            },
        },
    )

    with pytest.raises(AgentStalledError) as exc_info:
        runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)

    assert exc_info.value.kind == "initial_response_timeout"
    assert adapter.attempts == ["primary-model", "fallback-model"]
    assert exc_info.value.substitution is not None
    assert exc_info.value.substitution["requested_provider"] == "primary-provider"
    assert exc_info.value.substitution["actual_provider"] == "fallback-provider"
    assert exc_info.value.substitution["source"] == "agent-runtime-failover:transport"
    assert records[0]["outcome"] == "stalled"
    assert records[0]["substitution"]["substituted"] is True
    assert emitted_events[0][0] == "agent_runtime_substitution"
    assert RUNNER_FAILOVER_MARKER in capsys.readouterr().err


def test_runner_failover_cooldown_routes_next_dispatch_directly_to_fallback(
    tmp_path,
    monkeypatch,
):
    adapter, records, _emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(
                    ok=False,
                    response="",
                    stderr_excerpt="connection refused",
                ),
                "returncode": 1,
                "stderr_text": "connection refused",
            },
            "fallback-model": {
                "parse": ParseResult(ok=True, response="fallback ok"),
                "returncode": 0,
            },
        },
    )

    first = runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)
    first_attempts = list(adapter.attempts)
    adapter.attempts.clear()
    second = runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)

    assert first.ok is True
    assert first_attempts == ["primary-model", "fallback-model"]
    assert second.ok is True
    assert adapter.attempts == ["fallback-model"]
    assert second.substitution is not None
    assert second.substitution["source"] == "agent-runtime-failover:cooldown"
    assert len(records) == 2


def test_runner_failover_cools_final_failed_route_and_short_circuits_all_cooling(
    tmp_path,
    monkeypatch,
):
    adapter, records, _emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(
                    ok=False,
                    response="",
                    stderr_excerpt="connection refused",
                ),
                "returncode": 1,
                "stderr_text": "connection refused",
            },
            "fallback-model": {
                "parse": ParseResult(
                    ok=False,
                    response="",
                    stderr_excerpt="HTTP 503 overloaded",
                ),
                "returncode": 1,
                "stderr_text": "HTTP 503 overloaded",
            },
        },
    )

    first = runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)
    first_attempts = list(adapter.attempts)
    adapter.attempts.clear()

    with pytest.raises(RateLimitedError, match=r"all configured.*cooling"):
        runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)

    assert first.ok is False
    assert first_attempts == ["primary-model", "fallback-model"]
    assert adapter.attempts == []
    assert records[-1]["outcome"] == "rate_limited"


def test_runner_failover_rejects_forbidden_glm_target(tmp_path, monkeypatch):
    _adapter, _records, _emitted_events = _install_fake_runtime(
        monkeypatch,
        tmp_path,
        {
            "primary-model": {
                "parse": ParseResult(ok=True, response="primary ok"),
                "returncode": 0,
            },
        },
        forbidden_config=True,
    )

    with pytest.raises(ValueError, match="HERMES_GLM_FORBIDDEN"):
        runner_mod.invoke("failover-test", "hello", mode="read-only", cwd=tmp_path)


def test_shipped_config_declares_no_deepseek_chain():
    """Pin the shipped config: deepseek runs FIRST-PARTY ONLY (user order
    2026-07-07) — NO failover chain exists for it. `openrouter/deepseek/*`
    is guard-REFUSED for direct routing, and the old OR fallback routes in
    this chain BYPASSED the guard and leeched a fresh OpenRouter top-up
    (2026-07-07 burn). A deepseek fault is rerouted BY SEAT by the
    orchestrator (grok-build/codex), never by burning API credit. Any future
    chain must be explicitly user-approved and must not contain openrouter.
    """
    from agent_runtime.failover import (
        default_failover_config_path,
        load_failover_chain,
    )

    chain = load_failover_chain(
        "deepseek",
        effective_model="deepseek-v4-flash",
        path=default_failover_config_path(),
    )

    assert chain is None, (
        "deepseek must have NO failover chain (first-party only, user order "
        f"2026-07-07); got routes: {[r.provider for r in chain.routes]}"
        if chain is not None
        else ""
    )


def test_classifier_routes_hermes_credential_startup_failure_to_auth():
    """Live-captured 2026-07-06: a dead/missing credential fails hermes at
    startup with prose that previously matched NO trigger class, so the chain
    never rotated. Credential rotation is the point — must classify as auth."""
    from agent_runtime.failover import classify_failover_trigger

    stderr = (
        "hermes -z: agent failed: Provider 'deepseek' is set in config.yaml "
        "but no API key was found. Set the DEEPSEEK_API_KEY environment "
        "variable, or switch to a different provider with `hermes model`."
    )
    trigger = classify_failover_trigger(
        parse=ParseResult(ok=False, response="", stderr_excerpt=stderr[:500]),
        returncode=1,
        kill_reason=None,
        stdout_text="",
        stderr_text=stderr,
    )

    assert trigger == "auth"


def test_classifier_routes_inband_http_401_stdout_to_auth():
    """Companion to the hermes_common in-band fix: once parse marks the
    single-line 'HTTP 401: ...' stdout as not-ok, the classifier must see
    auth in the excerpt."""
    from agent_runtime.failover import classify_failover_trigger

    excerpt = "HTTP 401: Authentication Fails, Your api key: ****robe is invalid"
    trigger = classify_failover_trigger(
        parse=ParseResult(ok=False, response="", stderr_excerpt=excerpt),
        returncode=0,
        kill_reason=None,
        stdout_text="",
        stderr_text="",
    )

    assert trigger == "auth"


def test_classifier_refuses_to_rotate_on_inband_400():
    """Review D2 (PR #4580): a request-format error would fail identically on
    every route — the gate must return None so the chain is not burned."""
    from agent_runtime.failover import classify_failover_trigger

    trigger = classify_failover_trigger(
        parse=ParseResult(
            ok=False,
            response="",
            stderr_excerpt="HTTP 400: Invalid request: unknown parameter 'foo'",
        ),
        returncode=0,
        kill_reason=None,
        stdout_text="",
        stderr_text="",
    )

    assert trigger is None


def test_classifier_routes_initial_response_timeout_to_transport():
    from agent_runtime.failover import classify_failover_trigger

    trigger = classify_failover_trigger(
        parse=ParseResult(ok=False, response="", stderr_excerpt=None),
        returncode=-9,
        kill_reason="initial_response_timeout",
        stdout_text="",
        stderr_text="",
    )

    assert trigger == "transport"


def test_classifier_refuses_to_rotate_on_streaming_silence_timeout():
    from agent_runtime.failover import classify_failover_trigger

    trigger = classify_failover_trigger(
        parse=ParseResult(ok=False, response="", stderr_excerpt=None),
        returncode=-9,
        kill_reason="stdout_silence_timeout",
        stdout_text="partial output\n",
        stderr_text="",
    )

    assert trigger is None


def test_chain_route_missing_model_after_index_zero_warns_and_drops(
    tmp_path, caplog
):
    """Review D4 (PR #4580): fail-safe stays (no raise), but loudly."""
    import logging

    from agent_runtime.failover import load_failover_chain

    config = tmp_path / "failover.yaml"
    config.write_text(
        "chains:\n"
        "  deepseek:\n"
        "    routes:\n"
        "      - provider: deepseek\n"
        "      - provider: openrouter\n",  # missing model -> dropped
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING):
        chain = load_failover_chain(
            "deepseek", effective_model="deepseek-v4-pro", path=config
        )

    assert chain is None  # single usable route -> feature disabled
    assert any("deepseek[1] dropped" in rec.getMessage() for rec in caplog.records)


def test_shipped_config_declares_no_grok_chain():
    """Pin the shipped config: grok has NO failover chain (user order
    2026-07-07 — grok work belongs on the grok-build native-app seat;
    grok-4.* via OpenRouter has no measured niche and 402-drained the OR
    balance). Supersedes the #4583 in-family-via-openrouter pin. The hermes
    xai seat stays reachable as a plain single route without a chain."""
    from agent_runtime.failover import (
        default_failover_config_path,
        load_failover_chain,
    )

    chain = load_failover_chain(
        "grok",
        effective_model="grok-4.5",
        path=default_failover_config_path(),
    )

    assert chain is None, (
        "grok must have NO failover chain (grok-build is the seat, user "
        f"order 2026-07-07); got routes: {[r.provider for r in chain.routes]}"
        if chain is not None
        else ""
    )
