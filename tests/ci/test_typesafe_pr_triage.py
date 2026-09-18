"""Tests for the cheap TypeSafe/Jev PR triage CI job (#8232).

Covers: missing TYPESAFE_API_KEY skips (exit 0); a mocked high-confidence
`broken` verdict fails; a mocked `ready` verdict passes; diff truncation.
Never talks to the live API — `system_one` is always a fake/mock here.
"""

from __future__ import annotations

import pytest

from scripts.ci.typesafe_pr_triage import (
    MAX_DIFF_CHARS,
    evaluate,
    main,
    triage,
    truncate_diff,
)


def _answers(choice: str, confidence: float, high_risk: float) -> dict:
    return {
        "readiness": {"choice": choice, "confidence": confidence},
        "high_risk": {"noul": high_risk},
    }


def test_main_skips_without_api_key(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    assert main() == 0
    assert "skipping" in capsys.readouterr().out


def test_main_skips_without_base_sha(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setenv("TYPESAFE_API_KEY", "secret-value-not-real")
    monkeypatch.delenv("BASE_SHA", raising=False)
    monkeypatch.delenv("HEAD_SHA", raising=False)
    assert main() == 0
    assert "skipping" in capsys.readouterr().out


def test_triage_broken_high_confidence_fails() -> None:
    def fake_system_one(state, questions, api_key):
        assert api_key == "fake-key"
        return {"answers": _answers("broken", 0.95, 0.1)}

    exit_code, summary = triage(
        ["scripts/foo.py"], "diff --git a/scripts/foo.py", "pull_request", "fake-key",
        system_one=fake_system_one,
    )
    assert exit_code == 1
    assert "FAIL" in summary


def test_triage_broken_high_risk_without_confidence_fails() -> None:
    """Low Choice confidence but a confident high_risk Noul still fails (§ compose-in-code OR)."""

    def fake_system_one(state, questions, api_key):
        return {"answers": _answers("broken", 0.4, 0.9)}

    exit_code, _summary = triage(
        ["scripts/foo.py"], "diff", "pull_request", "fake-key", system_one=fake_system_one
    )
    assert exit_code == 1


def test_triage_ready_passes() -> None:
    def fake_system_one(state, questions, api_key):
        return {"answers": _answers("ready", 0.99, 0.0)}

    exit_code, summary = triage(
        ["scripts/foo.py"], "diff --git a/scripts/foo.py", "pull_request", "fake-key",
        system_one=fake_system_one,
    )
    assert exit_code == 0
    assert "pass" in summary


def test_triage_broken_low_confidence_passes() -> None:
    """Low-confidence `broken` must not fail the job (advisory, not a hard gate)."""

    def fake_system_one(state, questions, api_key):
        return {"answers": _answers("broken", 0.5, 0.2)}

    exit_code, _summary = triage(
        ["scripts/foo.py"], "diff", "pull_request", "fake-key", system_one=fake_system_one
    )
    assert exit_code == 0


def test_triage_no_changed_paths_skips() -> None:
    def fake_system_one(state, questions, api_key):
        raise AssertionError("system_one must not be called with no changed paths")

    exit_code, summary = triage([], "", "pull_request", "fake-key", system_one=fake_system_one)
    assert exit_code == 0
    assert "skipping" in summary


def test_triage_api_failure_skips_without_raising() -> None:
    def fake_system_one(state, questions, api_key):
        raise OSError("connection reset")

    exit_code, summary = triage(
        ["scripts/foo.py"], "diff", "pull_request", "fake-key", system_one=fake_system_one
    )
    assert exit_code == 0
    assert "not blocking" in summary


def test_evaluate_never_logs_api_key() -> None:
    # `evaluate` only ever sees the already-decoded response body, never the
    # key. Sanity check that its summary line contains none of the request
    # ingredients that would carry a secret.
    _should_fail, summary = evaluate(_answers("ready", 0.7, 0.1))
    assert "TYPESAFE_API_KEY" not in summary
    assert "Bearer" not in summary


def test_truncate_diff_under_limit_unchanged() -> None:
    small = "diff --git a/x b/x\n+line\n"
    assert truncate_diff(small) == small


def test_truncate_diff_over_limit_truncates_and_marks() -> None:
    big = "x" * (MAX_DIFF_CHARS + 500)
    out = truncate_diff(big, limit=MAX_DIFF_CHARS)
    assert len(out) > MAX_DIFF_CHARS  # truncation marker adds length back
    assert out.startswith("x" * 100)
    assert "truncated" in out
    assert out.count("x") == MAX_DIFF_CHARS


_KEY = "sk-live-SECRET-KEY-123"


def test_triage_never_prints_api_key_from_value_error() -> None:
    def boom(state, questions, api_key):
        raise ValueError(f"Invalid header value: 'Bearer {api_key}'")

    code, msg = triage(["a.py"], "diff", "pull_request", _KEY, system_one=boom)
    assert code == 0
    assert _KEY not in msg
    assert "ValueError" in msg


def test_triage_skips_on_incomplete_read() -> None:
    import http.client

    def boom(state, questions, api_key):
        raise http.client.IncompleteRead(b"par", 10)

    code, msg = triage(["a.py"], "diff", "pull_request", _KEY, system_one=boom)
    assert code == 0
    assert "IncompleteRead" in msg


@pytest.mark.parametrize(
    "response",
    [
        {"answers": None},
        {},
        None,
        {"answers": {"readiness": None, "high_risk": {"noul": 0.1}}},
        {"answers": _answers("broken", 1.7, 0.0)},
        {"answers": _answers("broken", float("nan"), 0.0)},
        {"answers": _answers("broken", "high", 0.0)},
        {"answers": _answers("broken", 0.9, None)},
        {"answers": _answers("broken", 10**400, 0.0)},
        {"answers": _answers("broken", 0.9, 10**400)},
        {"answers": _answers("broken", -(10**400), 0.0)},
    ],
)
def test_triage_skips_on_malformed_response(response) -> None:
    code, msg = triage(
        ["a.py"], "diff", "pull_request", _KEY, system_one=lambda s, q, k: response
    )
    assert code == 0
    assert "unexpected API response shape" in msg


def test_triage_still_fails_on_confident_broken() -> None:
    code, _ = triage(
        ["a.py"], "diff", "pull_request", _KEY,
        system_one=lambda s, q, k: {"answers": _answers("broken", 0.9, 0.0)},
    )
    assert code == 1
