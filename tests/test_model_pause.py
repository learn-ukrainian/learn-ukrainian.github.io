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
