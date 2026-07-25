"""A background ask worker that dies at startup must fail LOUDLY.

Observed live on the kimi lane, 2026-07-25: `ask-kimi` returned a message id and
"✅ Ask sent; processing in background", the worker exited immediately, its log file
was **0 bytes**, and no usage record was written. The ask reported success and
produced nothing.

That is the worst possible shape for a review gate. Silence is indistinguishable
from "still thinking", so the driver waits, then eventually records whatever they
remember — which is how a CHANGES REQUIRED verdict became "ADVISOR PASS" in a
handoff earlier the same day (#5773).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai_agent_bridge import _ask_lifecycle as lifecycle


class _FakeProc:
    """A worker that has already exited with the given return code."""

    def __init__(self, rc: int, pid: int = 424242) -> None:
        self._rc = rc
        self.pid = pid

    def poll(self) -> int:
        return self._rc


@pytest.fixture
def recorded(monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, str]]:
    calls: list[tuple[int, str]] = []
    monkeypatch.setattr(lifecycle, "record_ask_failure", lambda mid, reason, **kw: calls.append((mid, reason)))
    monkeypatch.setattr(lifecycle, "_remove_pid_file", lambda *a, **k: None)
    return calls


def test_worker_dead_with_empty_log_is_recorded_as_failure(tmp_path, monkeypatch, capsys, recorded):
    """The exact kimi shape: exited, wrote nothing, nothing recorded."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "sent")
    log = tmp_path / "ask-5010.log"
    log.write_text("", encoding="utf-8")  # 0 bytes, as observed

    lifecycle._confirm_worker_started(5010, "kimi", _FakeProc(rc=1), log)

    assert recorded, "a worker that died writing nothing must record a terminal failure"
    mid, reason = recorded[0]
    assert mid == 5010
    assert "died at startup" in reason
    err = capsys.readouterr().err
    assert "DIED AT STARTUP" in err
    assert "no answer is coming" in err, "the operator must be told not to wait"


def test_log_tail_is_surfaced_when_present(tmp_path, monkeypatch, capsys, recorded):
    """If the worker managed to say anything, that text is the diagnosis — show it."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "sent")
    log = tmp_path / "ask-1.log"
    log.write_text("ModuleNotFoundError: no adapter for kimi\n", encoding="utf-8")

    lifecycle._confirm_worker_started(1, "kimi", _FakeProc(rc=1), log)

    assert "ModuleNotFoundError" in recorded[0][1]
    assert "ModuleNotFoundError" in capsys.readouterr().err


def test_clean_exit_with_recorded_status_is_not_flagged(tmp_path, monkeypatch, recorded):
    """A worker that finished properly must NOT be reported as a startup death."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "replied:42")
    log = tmp_path / "ask-2.log"
    log.write_text("done\n", encoding="utf-8")

    lifecycle._confirm_worker_started(2, "codex", _FakeProc(rc=0), log)

    assert not recorded, "a completed ask must not be mislabelled a startup death"


def test_zero_exit_without_a_recorded_result_still_fails(tmp_path, monkeypatch, recorded):
    """rc=0 is not success. A finished ask always leaves a reply or a failure."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "processing")
    log = tmp_path / "ask-3.log"
    log.write_text("", encoding="utf-8")

    lifecycle._confirm_worker_started(3, "glm", _FakeProc(rc=0), log)

    assert recorded, "exit 0 with no recorded result is still a silent death"


def test_live_worker_is_left_alone(tmp_path, monkeypatch, recorded):
    """A normal long-running ask must not be disturbed or mislabelled."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "processing")
    log = tmp_path / "ask-4.log"
    log.write_text("📨 Message #4\n", encoding="utf-8")

    class _Alive:
        pid = 999

        def poll(self):
            return None

    lifecycle._confirm_worker_started(4, "codex", _Alive(), log)

    assert not recorded


def test_grace_window_is_short_enough_not_to_stall_the_caller():
    """`ask-*` is interactive; the check must not add a visible delay."""
    assert lifecycle._WORKER_START_GRACE_S <= 10.0


def test_real_subprocess_that_exits_immediately_is_caught(tmp_path, monkeypatch, recorded):
    """End-to-end with a genuine process, not a stub."""
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "sent")
    log = tmp_path / "ask-real.log"
    with log.open("w", encoding="utf-8") as handle:
        proc = subprocess.Popen([sys.executable, "-c", "raise SystemExit(3)"], stdout=handle, stderr=handle)
    proc.wait(timeout=30)

    lifecycle._confirm_worker_started(99, "kimi", proc, log)

    assert recorded, "a real instantly-exiting worker must be reported"


def test_launch_background_ask_is_actually_wired_to_the_check(tmp_path, monkeypatch, recorded):
    """The WIRING, not just the helper.

    Every test above calls `_confirm_worker_started` directly, so deleting its call
    site leaves them all green while the fix does nothing in production. That is the
    precise failure mode a cross-family reviewer flagged on the lease PR earlier the
    same day: "test the SessionStart wiring, not just the function — the pid can be
    wrong while every unit test passes."
    """
    monkeypatch.setattr(lifecycle, "_ask_status", lambda _mid: "sent")
    monkeypatch.setattr(lifecycle, "_write_pid_file", lambda *a, **k: None)
    monkeypatch.setattr(lifecycle, "REPO_ROOT", tmp_path)

    class _DeadOnArrival:
        pid = 4242

        def poll(self):
            return 1

    monkeypatch.setattr(lifecycle.subprocess, "Popen", lambda *a, **k: _DeadOnArrival())

    lifecycle.launch_background_ask(777, "kimi", {"content": "x"})

    assert recorded, (
        "launch_background_ask did not run the startup check — a worker that dies "
        "instantly would still be reported to the caller as a successful dispatch"
    )
    assert recorded[0][0] == 777
