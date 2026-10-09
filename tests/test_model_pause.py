"""Operator model pauses and plan-headroom stops for new dispatches."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from scripts.agent_runtime import model_pause as mp

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=UTC)
POLICY = {
    "pauses": [{"pattern": "claude-opus-*", "until": "2026-10-12T07:00:00Z", "reason": "operator pause"}],
    "headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 87}],
}


def test_paused_model_is_refused_until_the_reset() -> None:
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_PAUSED"):
        mp.refuse_paused_models(["claude-opus-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: 10.0)


def test_pause_lifts_by_itself_after_until() -> None:
    later = datetime(2026, 10, 12, 7, 0, tzinfo=UTC) + timedelta(seconds=1)
    mp.refuse_paused_models(["claude-opus-5-5"], policy=POLICY, now=later, used_pct=lambda _l: 10.0)


def test_other_models_pass_while_headroom_remains() -> None:
    mp.refuse_paused_models(
        ["claude-sonnet-5-5", "gpt-6.1-sol", None], policy=POLICY, now=NOW, used_pct=lambda _l: 84.0
    )


def test_headroom_stop_refuses_matching_models_only() -> None:
    with pytest.raises(mp.ModelPausedRefused, match="MODEL_HEADROOM"):
        mp.refuse_paused_models(["claude-sonnet-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: 87.0)
    mp.refuse_paused_models(["gpt-6.1-sol"], policy=POLICY, now=NOW, used_pct=lambda _l: 99.0)


def test_unreadable_usage_does_not_block() -> None:
    mp.refuse_paused_models(["claude-sonnet-5-5"], policy=POLICY, now=NOW, used_pct=lambda _l: None)


def test_naive_or_invalid_until_is_inert() -> None:
    policy = {"pauses": [{"pattern": "claude-opus-*", "until": "2026-10-12T07:00:00"}]}
    mp.refuse_paused_models(["claude-opus-5-5"], policy=policy, now=NOW)


def test_missing_policy_file_means_no_pauses(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(tmp_path / "absent.json"))
    assert mp.load_policy() == {}
    mp.refuse_paused_models(["claude-opus-5-5"])


def test_policy_file_is_read(tmp_path, monkeypatch) -> None:
    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": "claude-opus-*", "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    with pytest.raises(mp.ModelPausedRefused):
        mp.refuse_paused_models(["claude-opus-5-5"])


def test_admission_refuses_a_paused_seat_default(tmp_path, monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta

    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": "paused-model-*", "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    monkeypatch.setattr(ta, "_seat_default_model", lambda seat: "paused-model-1")
    with pytest.raises(mp.ModelPausedRefused):
        ta._refuse_paused([None, ta._seat_default_model("claude")])


def test_reviewer_resolver_excludes_a_paused_candidate(tmp_path, monkeypatch) -> None:
    from scripts.review import reviewer_resolver as rr

    candidate = next(iter(rr.REVIEW_CANDIDATES.values()))
    model = rr.candidate_dispatch_model(candidate)
    path = tmp_path / "pause.json"
    future = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    path.write_text(json.dumps({"pauses": [{"pattern": model, "until": future}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(path))
    reason = rr._hard_exclusion_reason(candidate, None)  # type: ignore[arg-type]
    assert reason and "MODEL_PAUSED" in reason


def test_invalid_policy_shapes_are_inert() -> None:
    for policy in ({"pauses": 1}, {"headroom": 1}, {"pauses": [1, "x"]}, {"headroom": [None]}):
        mp.refuse_paused_models(["claude-opus-5-5"], policy=policy, now=NOW, used_pct=lambda _l: 99.0)


def test_malformed_usage_is_unreadable(monkeypatch) -> None:
    import io

    for payload in ("[1, 2]", '{"agents": {"claude": {"codexbar": [1]}}}', '{"agents": 3}'):
        monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, _p=payload, **k: io.StringIO(_p))
        assert mp.routing_budget_used_pct("claude") is None


def test_refusals_are_public_safe() -> None:
    policy = {
        "pauses": [{"pattern": "claude-opus-*", "until": "2026-10-12T07:00:00Z", "reason": "private note"}],
        "headroom": [{"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 87}],
    }
    paused = mp.refusal_reason("claude-opus-5-5", policy=policy, now=NOW, used_pct=lambda _l: 10.0)
    held = mp.refusal_reason("claude-sonnet-5-5", policy=policy, now=NOW, used_pct=lambda _l: 91.0)
    for text in (paused, held):
        assert (
            text
            and "private" not in text
            and "2026" not in text
            and "9" not in text.split(":", 1)[1].replace("claude-sonnet-5-5", "").replace("claude-opus-5-5", "")
        )


def test_messaging_admission_ignores_pauses(tmp_path, monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta

    called: list = []
    monkeypatch.setattr(ta, "_refuse_paused", lambda models: called.append(list(models)))
    with contextlib.suppress(Exception):  # other gates may refuse; the pause gate must not
        ta.resolve_and_admit(["claude"], mode="bridge")
    assert called == []


def test_every_dispatch_admission_caller_opts_in() -> None:
    import ast
    from pathlib import Path

    tree = ast.parse(Path("scripts/delegate.py").read_text(encoding="utf-8"))
    funcs = {"_admit_dispatch_target": 0, "_admit_kimi_worker": 0, "_admit_worker": 0}
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for call in ast.walk(node):
                if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "resolve_and_admit":
                    flag = any(k.arg == "new_dispatch" for k in call.keywords)
                    hits.append((node.name, flag))
    assert hits and all(flag for _name, flag in hits), hits
    del funcs


def test_dispatch_admission_refuses_a_paused_model(tmp_path, monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta

    policy = tmp_path / "p.json"
    policy.write_text(json.dumps({"pauses": [{"pattern": "claude-opus-*", "until": "2999-01-01T00:00:00Z"}]}))
    monkeypatch.setenv("LU_MODEL_PAUSE_FILE", str(policy))
    with pytest.raises(mp.ModelPausedRefused):
        ta._refuse_paused(["claude-opus-5-5"])


def test_pause_inputs_by_dispatch_kind() -> None:
    import inspect

    from scripts.agent_runtime import target_admission as ta

    src = inspect.getsource(ta.resolve_and_admit)
    assert "selected if review_dispatch else [*models, *selected]" in src


def test_withdrawn_reading_is_unavailable(monkeypatch) -> None:
    import io

    payload = '{"agents": {"claude": {"status": "unknown", "weekly_used_pct": 95}}}'
    monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, **k: io.StringIO(payload))
    assert mp.routing_budget_used_pct("claude") is None


def test_public_source_has_no_endpoint_literal() -> None:
    from pathlib import Path

    text = Path("scripts/agent_runtime/model_pause.py").read_text(encoding="utf-8")
    assert "http://" not in text and "https://" not in text


def _budget(monkeypatch, payload: dict) -> float | None:
    import io

    monkeypatch.setattr(mp.urllib.request, "urlopen", lambda *a, **k: io.StringIO(json.dumps(payload)))
    return mp.routing_budget_used_pct("claude")


def test_only_fresh_probe_readings_count(monkeypatch) -> None:
    fresh = {"stale": False, "freshness": "fresh", "weekly_used_pct": 91}
    ok = {"diagnostics": {"stale": False}, "agents": {"claude": {"status": "hot", "codexbar": fresh}}}
    assert _budget(monkeypatch, ok) == 91.0
    for bad in (
        {**ok, "agents": {"claude": {"status": "near_cap", "codexbar": {**fresh, "stale": True}}}},
        {**ok, "agents": {"claude": {"status": "near_cap", "codexbar": {**fresh, "freshness": "stale_last_good"}}}},
        {**ok, "agents": {"claude": {"status": "unknown", "codexbar": fresh}}},
    ):
        assert _budget(monkeypatch, bad) is None


def test_aggregate_snapshot_staleness_does_not_hide_a_fresh_lane(monkeypatch) -> None:
    fresh = {"stale": False, "freshness": "fresh", "weekly_used_pct": 91}
    payload = {"diagnostics": {"stale": True}, "agents": {"claude": {"status": "hot", "codexbar": fresh}}}
    assert _budget(monkeypatch, payload) == 91.0


def test_truncated_response_is_unavailable(monkeypatch) -> None:
    import http.client

    def boom(*_a, **_k):
        raise http.client.IncompleteRead(b"{")

    monkeypatch.setattr(mp.urllib.request, "urlopen", boom)
    assert mp.routing_budget_used_pct("claude") is None


def test_endpoint_resolves_under_plain_package_import() -> None:
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-c", "import scripts.agent_runtime.model_pause as m; print(m._monitor_base())"],
        capture_output=True,
        text=True,
        timeout=60,
        env={k: v for k, v in __import__("os").environ.items() if k != "DELEGATE_MONITOR_API"},
    )
    assert out.returncode == 0, out.stderr[-400:]
    assert out.stdout.strip().startswith("http")


def test_kimi_worker_pause_settles_the_existing_task(tmp_path, monkeypatch) -> None:
    import importlib

    from scripts import delegate

    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path / "tasks"))
    task_id = "kimi-pause-race"
    state = delegate._state_path_no_create(task_id)
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"task_id": task_id, "status": "spawning"}))

    def paused(*_a, **_k):
        raise mp.ModelPausedRefused("MODEL_PAUSED: kimi-x is paused by operator policy")

    for name in ("scripts.agent_runtime.target_admission", "agent_runtime.target_admission"):
        with contextlib.suppress(ImportError):
            monkeypatch.setattr(importlib.import_module(name), "resolve_and_admit", paused)
    refusal, target = delegate._kimi_worker_refusal(
        task_id, agent="kimi", model=None, mode="read-only", cwd=tmp_path, review=False
    )
    assert refusal and target is None
    assert json.loads(state.read_text())["status"] == "failed"


def test_native_claude_alias_is_paused_with_its_family() -> None:
    policy = {"pauses": [{"pattern": "claude-opus-*", "until": "2999-01-01T00:00:00Z"}]}
    for alias in ("opus", "Opus", "opus[1m]"):
        assert mp.refusal_reason(alias, policy=policy, now=NOW, used_pct=lambda _l: None)
    assert mp.refusal_reason("sonnet", policy=policy, now=NOW, used_pct=lambda _l: None) is None


def test_kimicc_default_is_the_harness_default(monkeypatch) -> None:
    from scripts.agent_runtime import target_admission as ta
    from scripts.agent_runtime.adapters import kimicc

    monkeypatch.setattr(kimicc, "kimicc_default_model", lambda *a, **k: "kimi-code/k3")
    assert ta._seat_default_model("kimi", "kimicc") == "kimi-code/k3"
