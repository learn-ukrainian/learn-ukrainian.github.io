"""Unit tests for CI-advisory latency budgets (#5360)."""

from __future__ import annotations

import pytest

from tests.latency_budget import assert_under_budget, latency_assertions_enforce


def test_under_budget_is_always_ok(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("ENFORCE_LATENCY_ASSERTIONS", raising=False)

    assert_under_budget(0.05, 0.1, "should not fire")

    assert capsys.readouterr().out == ""


def test_over_budget_hard_fails_locally(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("ENFORCE_LATENCY_ASSERTIONS", raising=False)

    assert latency_assertions_enforce() is True
    with pytest.raises(AssertionError, match=r"orient\.html /api/orient"):
        assert_under_budget(
            3.69,
            1.5,
            "orient.html /api/orient p95-of-3 took 3.690s",
        )


def test_over_budget_advisory_on_ci(monkeypatch, capsys):
    monkeypatch.setenv("CI", "true")
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("ENFORCE_LATENCY_ASSERTIONS", raising=False)

    assert latency_assertions_enforce() is False
    assert_under_budget(
        3.69,
        1.5,
        "orient.html /api/orient p95-of-3 took 3.690s "
        "(runs: 5.010s, 3.690s, 0.903s)",
    )

    out = capsys.readouterr().out
    assert out.startswith("::warning::")
    assert "orient.html /api/orient p95-of-3 took 3.690s" in out
    assert "5.010s, 3.690s, 0.903s" in out


def test_enforce_flag_hard_fails_on_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("ENFORCE_LATENCY_ASSERTIONS", "1")

    assert latency_assertions_enforce() is True
    with pytest.raises(AssertionError, match="health"):
        assert_under_budget(0.2, 0.1, "/api/health p95-of-3 took 0.200s")


def test_github_actions_alone_is_advisory(monkeypatch, capsys):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("ENFORCE_LATENCY_ASSERTIONS", raising=False)

    assert_under_budget(2.0, 1.0, "slow sibling")
    assert "::warning::slow sibling" in capsys.readouterr().out
