"""Runtime rules delivery at the process-input boundary, including confined entrances."""

from __future__ import annotations

import hashlib
import inspect
import json
from types import SimpleNamespace

import pytest

from scripts.agent_runtime import acpx_discuss, runner
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.errors import AgentRuntimeError
from scripts.agent_runtime.failover import FailoverChain, FailoverRoute
from scripts.lib import rules_core
from scripts.review.render_contract import trusted_core_context


class SpawnObserved(Exception):
    """Stop at the actual spawn boundary without executing a provider."""


@pytest.fixture
def boundary(tmp_path, monkeypatch):
    captured = []
    from scripts.agent_runtime import attempt_boundary
    monkeypatch.setattr(attempt_boundary, "prepare_attempt_boundary", lambda *a, **kw: None)

    class Adapter:
        name = "codex"
        default_model = "gpt-6.1-sol"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, *, prompt, cwd, **kwargs):
            return InvocationPlan(cmd=["rules-test-agent"], cwd=cwd, stdin_payload=prompt)

        def liveness_signal_paths(self, plan):
            return ()

    def spawn(cmd, *, stdin, **kwargs):
        captured.append(stdin.read())
        raise SpawnObserved

    monkeypatch.setattr(runner, "_load_adapter", lambda *a, **kw: Adapter())
    monkeypatch.setattr(runner, "_spawn_subprocess", spawn)
    monkeypatch.setattr(runner, "_prepare_spawn_command", lambda cmd, env: (cmd, env))
    monkeypatch.setattr(runner, "_resolve_plan_telemetry", lambda **kw: SimpleNamespace(
        model=kw["requested_model"], effort="high", cli_version="fixture"))
    monkeypatch.setattr(runner, "has_headroom", lambda *a: (True, ""))
    monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **kw: None)
    monkeypatch.setattr(runner, "write_record", lambda *a, **kw: None)
    monkeypatch.setattr(runner, "build_agent_env", lambda **kw: {})
    monkeypatch.setattr(runner, "_apply_merge_guard", lambda **kw: kw["env"])
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    monkeypatch.delenv("LU_RULES_SEAT", raising=False)
    return captured


@pytest.fixture(params=[("core", "content", "core"), (None, "content", "content"), (None, None, "core")],
                ids=["explicit-over-env", "environment", "default"])
def seat(request, monkeypatch):
    explicit, environment, expected = request.param
    if environment is not None:
        monkeypatch.setenv("LU_RULES_SEAT", environment)
    else:
        monkeypatch.delenv("LU_RULES_SEAT", raising=False)
    return explicit, expected


def _kwargs(call, seat, monkeypatch):
    """Baseline has no seat keyword. Exercise its existing environmental seat selection."""
    explicit, _expected = seat
    if "rules_seat" in inspect.signature(call).parameters:
        return {"rules_seat": explicit}
    if explicit:
        monkeypatch.setenv("LU_RULES_SEAT", explicit)
    return {}


def _one_core(captured, expected):
    assert len(captured) == 1
    assert captured[0].startswith(rules_core.core_block(expected))
    assert captured[0].count(rules_core.BLOCK_OPEN) == 1


@pytest.mark.parametrize("route", ["ordinary", "runner-failover", "gemini-fallback"])
def test_ordinary_invoke_cannot_spawn_without_exactly_one_core(boundary, seat, tmp_path, monkeypatch, route):
    """Defect class: ordinary, failover or Gemini planning receives an unprepared prompt."""
    agent = "codex"
    if route == "runner-failover":
        chain = FailoverChain("codex", (FailoverRoute("fixture", "gpt-6.1-sol"),))
        monkeypatch.setattr(runner, "load_failover_chain", lambda *a, **kw: chain)
        monkeypatch.setattr(runner, "FailoverCooldownStore", lambda: object())
        monkeypatch.setattr(runner, "ordered_available_routes", lambda *a: chain.routes)
    elif route == "gemini-fallback":
        agent = "gemini"
        # Select one deterministic rung while retaining the real Gemini fallback invocation path.
        def ladder(**kwargs):
            return kwargs["attempt_runner"](SimpleNamespace(cli="gemini-cli", model="gpt-6.1-sol",
                                                           auth_mode="oauth", index=0), 0, 30)
        monkeypatch.setattr(runner, "run_gemini_fallback_ladder", ladder)
    with pytest.raises(SpawnObserved):
        runner.invoke(agent, "Return READY", cwd=tmp_path, task_id="rules-test", initiator="claude-cto",
                      **_kwargs(runner.invoke, seat, monkeypatch))
    _one_core(boundary, seat[1])


def test_acp_inter_agent_preserves_exactly_one_core(boundary, seat, tmp_path, monkeypatch):
    """Defect class: ACP loses its core or prepends it twice after forwarding."""
    with pytest.raises(SpawnObserved):
        runner.invoke_inter_agent("codex", "Return READY", cwd=tmp_path, task_id="rules-test",
                                  correlation_id="corr", idempotency_key="key", source="claude-cto",
                                  **_kwargs(runner.invoke_inter_agent, seat, monkeypatch))
    _one_core(boundary, seat[1])


def test_direct_only_pilot_cannot_spawn_without_exactly_one_core(boundary, seat, tmp_path, monkeypatch):
    """Defect class: the pilot's direct callback bypasses runtime rules delivery."""
    with pytest.raises(SpawnObserved):
        runner._invoke_direct_only("acpx-codex-shadow", "Return READY", cwd=tmp_path, task_id="rules-test",
                                   tool_config={}, initiator="claude-cto",
                                   **_kwargs(runner._invoke_direct_only, seat, monkeypatch))
    _one_core(boundary, seat[1])


def test_native_once_cannot_spawn_without_exactly_one_core(boundary, seat, tmp_path, monkeypatch):
    """Defect class: a native one-shot bypasses runtime rules delivery."""
    with pytest.raises(SpawnObserved):
        runner._invoke_native_once("codex", "Return READY", cwd=tmp_path, task_id="rules-test",
                                   initiator="claude-cto", **_kwargs(runner._invoke_native_once, seat, monkeypatch))
    _one_core(boundary, seat[1])


def test_real_controller_synthesis_cannot_spawn_without_exactly_one_core(boundary, seat, tmp_path, monkeypatch):
    """Defect class: the real controller synthesizes with its default, unprefixed native callback."""
    from tests.agent_runtime.test_acpx_discuss import _result

    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *a, **kw: "dispatch_worktree")
    kwargs = _kwargs(acpx_discuss.AcpxDiscussionController, seat, monkeypatch)
    if seat[0] == "core":
        # A missing source for the non-selected environment seat must not block
        # explicit core admission or synthesis.
        source_path = rules_core.source_path

        def selected_source(relative, *args, **kwargs):
            if relative == rules_core.CONTENT_ADDENDUM_REL:
                return tmp_path / "unavailable-content-addendum.md"
            return source_path(relative, *args, **kwargs)

        monkeypatch.setattr(rules_core, "source_path", selected_source)
    controller = acpx_discuss.AcpxDiscussionController(
        root=tmp_path / "plane", participant_call=lambda agent, *a, **kw: _result(agent, "Evidence"), **kwargs)
    try:
        controller.run(prompt="Solve the fixture", cwd=tmp_path, task_id="rules-test", correlation_id="corr",
                       idempotency_key="key", rounds=1, source="claude-cto")
    finally:
        controller.close()
    _one_core(boundary, seat[1])
    assert "Synthesize only the available evidence" in boundary[0]


def _admitted(tmp_path):
    from scripts.dispatcher import store

    prefix, dependency = trusted_core_context()
    prompt = prefix + "Review the admitted task body.\n"
    digest = hashlib.sha256(prompt.encode()).hexdigest()
    record = dict(task_id="rules-bound", review_attempt=dict(review_id="review", attempt_id="attempt"),
                  review_contract=dict(machinery_dependencies=dict(rules_core=dependency), prompt_sha256=digest),
                  prompt_sha256=digest)
    store.record_path("rules-bound").parent.mkdir(parents=True, exist_ok=True)
    store.record_path("rules-bound").write_text(json.dumps(record))
    return prompt, record


def _bound_kwargs():
    return {"rules_core_delivery": runner.RulesCoreDelivery.BOUND} if hasattr(runner, "RulesCoreDelivery") else {}


def test_admitted_bound_prompt_bytes_are_unchanged(boundary, tmp_path, monkeypatch):
    """Defect class: runtime reconstructs or replaces the admitted review bytes."""
    prompt, record = _admitted(tmp_path)
    monkeypatch.setenv("LU_RULES_SEAT", "content")
    seat_kwargs = _kwargs(runner.invoke, ("core", "core"), monkeypatch)
    with pytest.raises(SpawnObserved):
        runner.invoke("codex", prompt, cwd=tmp_path, task_id="rules-bound", initiator="claude-cto",
                      tool_config=record["review_attempt"], **_bound_kwargs(), **seat_kwargs)
    assert len(boundary) == 1
    assert hashlib.sha256(boundary[0].encode()).hexdigest() == record["prompt_sha256"]
    assert boundary[0] == prompt


@pytest.mark.parametrize("prefix", ["current", "stale", "other-seat"])
def test_existing_prefix_is_never_doubled(boundary, tmp_path, prefix):
    """Defect class: stale or other-seat prefixes produce a second core block."""
    block = rules_core.core_block("content" if prefix == "other-seat" else "core")
    if prefix == "stale":
        block = block.replace('sha256="', 'sha256="stale-', 1)
    prompt = block + "\n\nReturn READY"
    if prefix == "current":
        with pytest.raises(SpawnObserved):
            runner.invoke("codex", prompt, cwd=tmp_path, task_id="rules-test", initiator="claude-cto")
        assert boundary == [prompt]
    else:
        with pytest.raises(AgentRuntimeError, match="prefix"):
            runner.invoke("codex", prompt, cwd=tmp_path, task_id="rules-test", initiator="claude-cto")
        assert boundary == []


def test_missing_core_refuses_with_typed_runtime_error_before_spawn(boundary, tmp_path, monkeypatch):
    """Defect class: missing rules launch an agent or escape the runtime exception hierarchy."""
    def missing(*a, **kw):
        raise rules_core.RulesCoreMissing("rules source unavailable: core.md")
    monkeypatch.setattr(rules_core, "core_block", missing)
    with pytest.raises(AgentRuntimeError, match="rules source unavailable") as error:
        runner.invoke("codex", "Return READY", cwd=tmp_path, task_id="rules-test", initiator="claude-cto")
    assert type(error.value).__name__ == "RulesCoreMissingError"
    assert boundary == []


@pytest.mark.parametrize("tampering", ["framed-block", "provenance", "complete-body", "unadmitted-hash"])
def test_invalid_bound_refuses_with_typed_runtime_error_before_spawn(boundary, tmp_path, tampering):
    """Defect class: hash-only BOUND bypass accepts a substituted block, provenance or task body."""
    from scripts.dispatcher import store

    prompt, record = _admitted(tmp_path)
    task_id = "rules-bound"
    if tampering == "framed-block":
        prompt = prompt.replace('sha256="', 'sha256="altered-', 1)
    elif tampering == "provenance":
        record["review_contract"]["machinery_dependencies"]["rules_core"]["sources"][0]["sha256"] = "0" * 64
        store.record_path(task_id).write_text(json.dumps(record))
    elif tampering == "complete-body":
        prompt += "Substituted instructions.\n"
    else:
        task_id = "unadmitted"
    config = dict(record["review_attempt"], block_sha256=hashlib.sha256(prompt.encode()).hexdigest())
    with pytest.raises(AgentRuntimeError, match="BOUND") as error:
        runner.invoke("codex", prompt, cwd=tmp_path, task_id=task_id, initiator="claude-cto",
                      tool_config=config, **_bound_kwargs())
    assert type(error.value).__name__ == "RulesCoreDeliveryError"
    assert boundary == []
