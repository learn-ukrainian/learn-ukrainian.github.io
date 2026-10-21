from __future__ import annotations

import fcntl
import importlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime import acpx_pilot
from scripts.agent_runtime.errors import AgentUnavailableError
from scripts.agent_runtime.result import Result

PILOT_ENTRYPOINT = acpx_pilot.PILOT_ENTRYPOINT
PilotResult = acpx_pilot.PilotResult
run_pilot = acpx_pilot.run_pilot
runner = importlib.import_module("scripts.agent_runtime.runner")


def _result(agent: str, *, ok: bool = True, response: str = "READY", tokens: int = 7) -> Result:
    outcome = "ok" if ok else "error"
    return Result(
        ok=ok,
        agent=agent,
        model="test-model",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=1.25,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0 if ok else 1,
        usage_record={"outcome": outcome, "tokens": tokens},
    )


def _recording_sink(evidence_dir: Path, records: list[dict[str, Any]]):
    path = evidence_dir / f"usage_acpx-shadow-pilot-{PILOT_ENTRYPOINT}_2026-07-31.jsonl"

    def sink(record: dict[str, Any]) -> None:
        evidence_dir.mkdir(parents=True, exist_ok=True)
        records.append(record)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    return sink


def _run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    native_call,
    shadow_call,
    key: str = "idem-1",
    records: list[dict[str, Any]] | None = None,
) -> PilotResult:
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    monkeypatch.setattr(
        acpx_pilot,
        "classify_repo_path",
        lambda *_args, **_kwargs: "dispatch_worktree",
    )
    evidence = tmp_path / "evidence"
    captured = records if records is not None else []
    return run_pilot(
        target="codex",
        prompt="Return READY",
        cwd=Path.cwd(),
        task_id="task-6063",
        correlation_id="corr-secret",
        idempotency_key=key,
        evidence_dir=evidence,
        lock_path=tmp_path / "pilot.lock",
        native_call=native_call,
        shadow_call=shadow_call,
        record_sink=_recording_sink(evidence, captured),
    )


def test_pilot_runs_native_then_one_shadow_and_persists_sanitized_evidence(
    tmp_path,
    monkeypatch,
):
    order: list[str] = []
    calls: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    def native(agent, prompt, **kwargs):
        order.append("native")
        calls.append({"agent": agent, "prompt": prompt, **kwargs})
        return _result(agent, response="native-private")

    def shadow(agent, prompt, **kwargs):
        order.append("shadow")
        calls.append({"agent": agent, "prompt": prompt, **kwargs})
        return _result(agent, response="shadow-private", tokens=9)

    result = _run(
        tmp_path,
        monkeypatch,
        native_call=native,
        shadow_call=shadow,
        records=records,
    )

    assert order == ["native", "shadow"]
    assert result.native_outcome == "ok"
    assert result.shadow_outcome == "ok"
    assert result.classification_parity is True
    assert calls[0]["agent"] == "codex"
    assert calls[0]["entrypoint"] == "acpx-pilot-native"
    assert calls[1]["agent"] == "acpx-codex-shadow"
    assert calls[1]["tool_config"] == {
        "acpx_shadow": True,
        "target_agent": "codex",
        "correlation_id": "corr-secret",
        "idempotency_key": "idem-1",
    }

    evidence = records[-1]
    assert evidence["executed"] is True
    assert evidence["classification_parity"] is True
    assert evidence["native_tokens"] == 7
    assert evidence["shadow_tokens"] == 9
    serialized = json.dumps(evidence)
    for private in ("Return READY", "native-private", "shadow-private", "corr-secret", "idem-1"):
        assert private not in serialized


def test_shadow_failure_never_overrides_successful_native_result(tmp_path, monkeypatch):
    def shadow(*_args, **_kwargs):
        raise RuntimeError("shadow failed")

    result = _run(
        tmp_path,
        monkeypatch,
        native_call=lambda agent, *_args, **_kwargs: _result(agent, response="authority"),
        shadow_call=shadow,
    )

    assert result.native is not None
    assert result.native.response == "authority"
    assert result.native_outcome == "ok"
    assert result.shadow is None
    assert result.shadow_outcome == "error"
    assert result.classification_parity is False


def test_duplicate_idempotency_key_suppresses_both_model_calls(tmp_path, monkeypatch):
    calls = {"count": 0}

    def call(agent, *_args, **_kwargs):
        calls["count"] += 1
        return _result(agent)

    first = _run(tmp_path, monkeypatch, native_call=call, shadow_call=call)
    second = _run(tmp_path, monkeypatch, native_call=call, shadow_call=call)

    assert first.executed is True
    assert second.executed is False
    assert second.duplicate_suppressed is True
    assert calls["count"] == 2


def test_busy_lock_refuses_without_queueing_or_model_calls(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    monkeypatch.setattr(
        acpx_pilot,
        "classify_repo_path",
        lambda *_args, **_kwargs: "dispatch_worktree",
    )
    lock_path = tmp_path / "pilot.lock"
    lock_path.touch()
    handle = open(lock_path, "a+", encoding="utf-8")  # noqa: SIM115
    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    called = False

    def call(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("must not invoke")

    try:
        result = run_pilot(
            target="codex",
            prompt="Return READY",
            cwd=Path.cwd(),
            task_id="task-6063",
            correlation_id="corr-2",
            idempotency_key="idem-2",
            evidence_dir=tmp_path / "evidence",
            lock_path=lock_path,
            native_call=call,
            shadow_call=call,
            record_sink=lambda _record: None,
        )
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()

    assert result.busy is True
    assert result.executed is False
    assert called is False


def test_pilot_refuses_primary_checkout_before_any_model_call(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    monkeypatch.setattr(
        acpx_pilot,
        "classify_repo_path",
        lambda *_args, **_kwargs: "primary_checkout",
    )
    called = False

    def call(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("must not invoke")

    with pytest.raises(ValueError, match="worktree"):
        run_pilot(
            target="codex",
            prompt="Return READY",
            cwd=tmp_path,
            task_id="task-6063",
            correlation_id="corr-3",
            idempotency_key="idem-3",
            evidence_dir=tmp_path,
            native_call=call,
            shadow_call=call,
        )
    assert called is False


def test_normal_loader_still_refuses_cached_direct_only_adapter():
    runner._ADAPTER_CACHE.pop("acpx-codex-shadow", None)
    try:
        adapter = runner._load_adapter("acpx-codex-shadow", allow_direct_only=True)
        assert adapter.name == "acpx-codex-shadow"
        with pytest.raises(AgentUnavailableError, match="Direct-only"):
            runner._load_adapter("acpx-codex-shadow")
    finally:
        runner._ADAPTER_CACHE.pop("acpx-codex-shadow", None)


def test_direct_only_surface_rejects_normal_available_agent():
    with pytest.raises(AgentUnavailableError, match="not an unavailable direct-only seat"):
        runner._invoke_direct_only(
            "codex",
            "prompt",
            cwd=Path.cwd(),
            task_id="task-6063",
            tool_config={},
        )


def test_direct_only_surface_preserves_omitted_model_and_fixed_entrypoint(monkeypatch):
    captured: dict[str, Any] = {}
    sentinel = _result("acpx-codex-shadow")

    def fake_invoke_impl(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(runner, "_invoke_impl", fake_invoke_impl)

    result = runner._invoke_direct_only(
        "acpx-codex-shadow",
        "prompt",
        cwd=Path.cwd(),
        model=None,
        task_id="task-6063",
        tool_config={"acpx_shadow": True},
    )

    assert result is sentinel
    assert captured["model"] is None
    assert captured["mode"] == "read-only"
    assert captured["session_id"] is None
    assert captured["entrypoint"] == "acpx-pilot-shadow"
    assert captured["allow_direct_only"] is True
    assert captured["allow_runner_failover"] is False


def test_native_once_surface_disables_runner_failover(monkeypatch):
    captured: dict[str, Any] = {}
    sentinel = _result("codex")

    def fake_invoke_impl(*args, **kwargs):
        captured["args"] = args
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(runner, "_invoke_impl", fake_invoke_impl)

    result = runner._invoke_native_once(
        "codex",
        "prompt",
        cwd=Path.cwd(),
        task_id="task-6063",
    )

    assert result is sentinel
    assert captured["entrypoint"] == "acpx-pilot-native"
    assert captured["allow_runner_failover"] is False


def test_cli_exit_disposition_follows_native_not_failed_shadow(monkeypatch, capsys):
    authoritative = _result("codex", response="authority")
    result = PilotResult(
        target="codex",
        executed=True,
        duplicate_suppressed=False,
        busy=False,
        native_outcome="ok",
        shadow_outcome="error",
        classification_parity=False,
        native=authoritative,
        shadow=None,
    )
    monkeypatch.setattr(acpx_pilot, "run_pilot", lambda **_kwargs: result)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acpx_pilot.py",
            "--target",
            "codex",
            "--cwd",
            ".",
            "--task-id",
            "task-6063",
            "--correlation-id",
            "corr-4",
            "--idempotency-key",
            "idem-4",
        ],
    )
    monkeypatch.setattr(acpx_pilot, "_read_prompt", lambda _path: "prompt")

    assert acpx_pilot.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["authority"] == "native"
    assert payload["native"]["response"] == "authority"
    assert payload["shadow"]["outcome"] == "error"
