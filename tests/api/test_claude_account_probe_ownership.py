"""Only the Monitor API's claude-account scheduler probes Claude accounts or writes the samples file (#12542)."""

from __future__ import annotations

import threading

import pytest
from lu_machinery.api import claude_account_usage as cau
from lu_machinery.api import subscription_usage


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(cau, "_routing_budget_state_dir", lambda: tmp_path)
    # The scheduler gate in force outside pytest, so only ownership decides.
    monkeypatch.setenv("CODEXBAR_PERIODIC_REFRESH", "1")
    return tmp_path


@pytest.fixture
def probes(monkeypatch):
    calls: list[str] = []

    def probe(label, *, timeout_s):
        calls.append(label)
        raise cau._ProbeFailed("probe_error")

    monkeypatch.setattr(cau, "probe_account", probe)
    return calls


def test_non_scheduler_caller_never_probes_or_writes_samples(state_dir, probes, monkeypatch):
    # An exporter or one-liner process: no scheduler thread here.
    monkeypatch.setattr(subscription_usage, "_claude_account_scheduler_thread", None)

    cau.refresh_claude_account_usage()

    assert probes == []
    assert not (state_dir / cau._SAMPLES_FILE).exists()
    assert list(state_dir.iterdir()) == []


def test_non_scheduler_caller_never_persists_a_sample(state_dir, monkeypatch):
    monkeypatch.setattr(subscription_usage, "_claude_account_scheduler_thread", None)

    cau._persist_sample("claude:a", object())  # refused before the sample is read

    assert list(state_dir.iterdir()) == []


def test_scheduler_process_probes_every_label(state_dir, probes, monkeypatch):
    stop = threading.Event()
    owner = threading.Thread(target=stop.wait, daemon=True)
    owner.start()
    monkeypatch.setattr(subscription_usage, "_claude_account_scheduler_thread", owner)
    try:
        cau.refresh_claude_account_usage()
    finally:
        stop.set()
        owner.join(timeout=5)

    assert sorted(probes) == sorted(cau.CLAUDE_SUBSCRIPTION_ACCOUNT_LABELS)
