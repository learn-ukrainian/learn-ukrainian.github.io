"""Deterministic controller tests for the bounded active ACPX discussion."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from scripts.agent_runtime import acpx_discuss
from scripts.agent_runtime.errors import AgentTimeoutError
from scripts.agent_runtime.result import Result


def _result(agent: str, response: str, *, tokens: int = 5) -> Result:
    return Result(
        ok=True,
        agent=agent,
        model="fixture",
        mode="read-only",
        response=response,
        stderr_excerpt=None,
        duration_s=0.01,
        session_id=None,
        rate_limited=False,
        stalled=False,
        returncode=0,
        usage_record={"outcome": "ok", "tokens": tokens},
    )


def _controller(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, participant, synthesis):
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    return acpx_discuss.AcpxDiscussionController(
        root=tmp_path / "plane", participant_call=participant, synthesis_call=synthesis
    )


def _run(controller: acpx_discuss.AcpxDiscussionController, *, key: str = "idem-1", rounds: int = 2):
    return controller.run(
        prompt="Solve the bounded fixture.",
        cwd=Path.cwd(),
        task_id="task-6078",
        correlation_id="corr-6078",
        idempotency_key=key,
        rounds=rounds,
    )


def test_two_participants_are_parallel_and_completed_replay_makes_no_calls(tmp_path, monkeypatch):
    calls: list[str] = []
    entered = threading.Barrier(2)

    def participant(agent: str, _prompt: str, **_kwargs):
        entered.wait(timeout=2)
        calls.append(agent)
        return _result(agent, f"{agent} evidence")

    def synthesis(agent: str, _prompt: str, **_kwargs):
        return _result(agent, "authoritative synthesis", tokens=7)

    controller = _controller(tmp_path, monkeypatch, participant, synthesis)
    try:
        first = _run(controller)
        second = _run(controller)
        rows = controller.conn.execute(
            "SELECT sender, recipient, in_reply_to FROM comms_messages WHERE conversation_id = ?",
            (first["conversation_id"],),
        ).fetchall()
        duplicate_events = controller.conn.execute(
            """SELECT COUNT(*) FROM acp_conversation_events
               WHERE conversation_id = ? AND event_type = 'DUPLICATE_SUPPRESSED'""",
            (first["conversation_id"],),
        ).fetchone()[0]
    finally:
        controller.close()

    assert first["state"] == "COMPLETE"
    assert first["rounds_completed"] == 2
    assert sorted(calls) == ["acpx-codex-shadow", "acpx-codex-shadow", "acpx-grok-shadow", "acpx-grok-shadow"]
    assert second["duplicate_suppressed"] is True
    assert second["synthesis"] == "authoritative synthesis"
    assert second["participant_outcomes"] == first["participant_outcomes"]
    assert second["rounds_completed"] == first["rounds_completed"]
    assert second["duration_ms"] == first["duration_ms"]
    assert second["tokens"] == first["tokens"]
    assert duplicate_events == 1
    edges = {(str(row[0]), str(row[1])) for row in rows}
    assert {("root", "codex"), ("root", "grok"), ("codex", "root"), ("grok", "root"), ("codex", "grok"), ("grok", "codex")} <= edges
    assert any(row[2] is not None for row in rows)


def test_three_rounds_repeat_cross_exchange_and_complete(tmp_path, monkeypatch):
    calls: list[str] = []

    def participant(agent: str, _prompt: str, **_kwargs):
        calls.append(agent)
        return _result(agent, f"{agent} evidence {len(calls)}")

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "three-round synthesis"),
    )
    try:
        payload = _run(controller, rounds=3)
    finally:
        controller.close()

    assert payload["state"] == "COMPLETE"
    assert payload["rounds_completed"] == 3
    assert len(calls) == 6
    assert len(payload["participant_outcomes"]) == 6


def test_cancellation_settles_current_wave_and_persists_terminal_state(tmp_path, monkeypatch):
    cancelled = threading.Event()
    synthesis_called = False

    def participant(agent: str, _prompt: str, **_kwargs):
        cancelled.set()
        return _result(agent, f"{agent} evidence")

    def synthesis(*_args, **_kwargs):
        nonlocal synthesis_called
        synthesis_called = True
        return _result("codex", "must not run")

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    controller = acpx_discuss.AcpxDiscussionController(
        root=tmp_path / "plane",
        participant_call=participant,
        synthesis_call=synthesis,
        cancelled=cancelled.is_set,
    )
    try:
        payload = _run(controller)
        replay = _run(controller)
    finally:
        controller.close()

    assert payload["state"] == "CANCELLED"
    assert payload["classification"] == "cancelled"
    assert payload["rounds_completed"] == 1
    assert len(payload["participant_outcomes"]) == 2
    assert payload["synthesis"] is None
    assert synthesis_called is False
    assert replay["state"] == "CANCELLED"
    assert replay["classification"] == "cancelled"
    assert replay["duplicate_suppressed"] is True


def test_one_participant_failure_is_partial_and_synthesis_uses_available_evidence(tmp_path, monkeypatch):
    def participant(agent: str, _prompt: str, **_kwargs):
        if agent.endswith("grok-shadow"):
            raise AgentTimeoutError("fixture timeout")
        return _result(agent, "codex-only evidence")

    received: list[str] = []

    def synthesis(agent: str, prompt: str, **_kwargs):
        received.append(prompt)
        return _result(agent, "partial synthesis")

    controller = _controller(tmp_path, monkeypatch, participant, synthesis)
    try:
        payload = _run(controller, rounds=1)
    finally:
        controller.close()

    assert payload["state"] == "PARTIAL_COMPLETE"
    assert payload["classification"] == "partial"
    assert "codex-only evidence" in received[0]
    assert "[none]" not in received[0]


def test_orphan_reservation_is_terminal_partial_without_model_retry(tmp_path, monkeypatch):
    called = False

    def participant(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("orphan must not be retried")

    controller = _controller(tmp_path, monkeypatch, participant, participant)
    try:
        _conversation, replay = controller._reserve(
            task_digest="a", correlation_digest="b", idempotency_digest=acpx_discuss._digest("idem-1"),
            rounds=1, deadline_at="2000-01-01T00:00:00Z",
        )
        assert replay is None
        replay_payload = _run(controller, rounds=1)
    finally:
        controller.close()

    assert replay_payload["state"] == "PARTIAL_COMPLETE"
    assert replay_payload["duplicate_suppressed"] is True
    assert called is False


@pytest.mark.parametrize(
    ("crash_state", "progression"),
    [
        ("INITIAL_FANOUT", ["INITIAL_FANOUT"]),
        ("INITIAL_COMPLETE", ["INITIAL_FANOUT", "INITIAL_COMPLETE"]),
        ("PARTIAL", ["INITIAL_FANOUT", "PARTIAL"]),
        (
            "CROSS_EXCHANGE",
            ["INITIAL_FANOUT", "INITIAL_COMPLETE", "CROSS_EXCHANGE"],
        ),
        (
            "CROSS_EXCHANGE_COMPLETE",
            [
                "INITIAL_FANOUT",
                "INITIAL_COMPLETE",
                "CROSS_EXCHANGE",
                "CROSS_EXCHANGE_COMPLETE",
            ],
        ),
        (
            "SYNTHESIS",
            ["INITIAL_FANOUT", "INITIAL_COMPLETE", "SYNTHESIS"],
        ),
    ],
)
def test_orphan_recovery_is_terminal_from_every_midflight_state(
    tmp_path, monkeypatch, crash_state, progression
):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: pytest.fail("orphan must not invoke participants"),
        lambda *_a, **_k: pytest.fail("orphan must not invoke synthesis"),
    )
    key = f"orphan-{crash_state}"
    try:
        conversation_id, replay = controller._reserve(
            task_digest="a",
            correlation_digest="b",
            idempotency_digest=acpx_discuss._digest(key),
            rounds=2,
            deadline_at="2000-01-01T00:00:00Z",
        )
        assert replay is None
        for state in progression:
            controller._append(
                conversation_id,
                event_type="STATE",
                state=state,
                transition=True,
            )

        replay_payload = _run(controller, key=key)
        terminal = controller.conn.execute(
            """SELECT event_type, state, outcome
               FROM acp_conversation_events
               WHERE conversation_id = ?
               ORDER BY sequence DESC LIMIT 1""",
            (conversation_id,),
        ).fetchone()
    finally:
        controller.close()

    assert replay_payload["state"] == "PARTIAL_COMPLETE"
    assert replay_payload["duplicate_suppressed"] is True
    assert tuple(terminal) == ("ORPHAN_RESERVATION", "PARTIAL_COMPLETE", "orphan")


def test_live_duplicate_refuses_without_mutating_original_reservation(tmp_path, monkeypatch):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: pytest.fail("duplicate must not invoke participants"),
        lambda *_a, **_k: pytest.fail("duplicate must not invoke synthesis"),
    )
    digest = acpx_discuss._digest("live-duplicate")
    try:
        conversation_id, replay = controller._reserve(
            task_digest="a",
            correlation_digest="b",
            idempotency_digest=digest,
            rounds=2,
            deadline_at="2099-01-01T00:00:00Z",
        )
        assert replay is None
        controller._append(
            conversation_id,
            event_type="STATE",
            state="INITIAL_FANOUT",
            transition=True,
        )

        with pytest.raises(acpx_discuss.AcpxDiscussionError, match="still in progress"):
            controller._reserve(
                task_digest="a",
                correlation_digest="b",
                idempotency_digest=digest,
                rounds=2,
                deadline_at="2099-01-01T00:00:00Z",
            )

        assert controller._state(conversation_id) == "INITIAL_FANOUT"
        controller._append(
            conversation_id,
            event_type="STATE",
            state="INITIAL_COMPLETE",
            transition=True,
        )
        assert controller._state(conversation_id) == "INITIAL_COMPLETE"
    finally:
        controller.close()


def test_active_mode_refuses_primary_checkout_and_shadow_stays_shadow_only(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "primary_checkout")
    controller = acpx_discuss.AcpxDiscussionController(root=tmp_path / "plane")
    try:
        with pytest.raises(acpx_discuss.AcpxDiscussionError, match="worktree"):
            _run(controller, rounds=1)
    finally:
        controller.close()


def test_invalid_transition_fails_closed_and_created_reservation_is_atomic(tmp_path, monkeypatch):
    controller = _controller(tmp_path, monkeypatch, lambda *_a, **_k: _result("codex", "x"), lambda *_a, **_k: _result("codex", "x"))
    try:
        conversation_id, replay = controller._reserve(
            task_digest="a", correlation_digest="b", idempotency_digest="c", rounds=1,
            deadline_at="2099-01-01T00:00:00Z",
        )
        assert replay is None
        assert controller.conn.execute(
            "SELECT state FROM acp_conversation_events WHERE conversation_id = ?", (conversation_id,)
        ).fetchone()[0] == "CREATED"
        with pytest.raises(acpx_discuss.AcpxDiscussionError, match="invalid ACPX transition"):
            controller._append(conversation_id, event_type="STATE", state="SYNTHESIS", transition=True)
    finally:
        controller.close()


def test_content_budget_exhaustion_is_partial_and_never_calls_synthesis(tmp_path, monkeypatch):
    monkeypatch.setattr(acpx_discuss, "CONTENT_BUDGET_BYTES", 100)
    synthesis_called = False

    def participant(agent: str, _prompt: str, **_kwargs):
        return _result(agent, "x" * 40)

    def synthesis(*_args, **_kwargs):
        nonlocal synthesis_called
        synthesis_called = True
        return _result("codex", "must not run")

    controller = _controller(tmp_path, monkeypatch, participant, synthesis)
    try:
        payload = _run(controller, rounds=1)
        events = controller.conn.execute(
            "SELECT event_type, outcome FROM acp_conversation_events WHERE conversation_id = ?",
            (payload["conversation_id"],),
        ).fetchall()
    finally:
        controller.close()

    assert payload["state"] == "PARTIAL_COMPLETE"
    assert synthesis_called is False
    assert ("BUDGET_EXHAUSTED", "content") in {(row[0], row[1]) for row in events}


def test_deadline_exceeded_is_partial_without_synthesis(tmp_path, monkeypatch):
    monkeypatch.setattr(acpx_discuss, "WHOLE_TIMEOUT_SECONDS", 0)
    release = threading.Event()
    synthesis_called = False

    def participant(*_args, **_kwargs):
        release.wait(timeout=2)
        return _result("codex", "late")

    def synthesis(*_args, **_kwargs):
        nonlocal synthesis_called
        synthesis_called = True
        return _result("codex", "must not run")

    controller = _controller(tmp_path, monkeypatch, participant, synthesis)
    try:
        payload = _run(controller, rounds=1)
        event_types = {
            row[0]
            for row in controller.conn.execute(
                "SELECT event_type FROM acp_conversation_events WHERE conversation_id = ?",
                (payload["conversation_id"],),
            )
        }
    finally:
        release.set()
        controller.close()

    assert payload["state"] == "PARTIAL_COMPLETE"
    assert "DEADLINE_EXCEEDED" in event_types
    assert synthesis_called is False


def test_process_wide_busy_rejects_without_queueing_or_retries(tmp_path, monkeypatch):
    calls = 0

    def participant(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("global capacity refusal must not invoke a participant")

    controller = _controller(tmp_path, monkeypatch, participant, lambda *_a, **_k: _result("codex", "partial"))
    assert acpx_discuss._PARTICIPANT_SLOTS.acquire(blocking=False)
    assert acpx_discuss._PARTICIPANT_SLOTS.acquire(blocking=False)
    try:
        payload = _run(controller, rounds=1)
    finally:
        acpx_discuss._PARTICIPANT_SLOTS.release()
        acpx_discuss._PARTICIPANT_SLOTS.release()
        controller.close()

    assert payload["state"] == "PARTIAL_COMPLETE"
    assert calls == 0
    assert {item["outcome"] for item in payload["participant_outcomes"]} == {"busy"}


def test_errors_are_terminal_once_per_leg_without_retry_or_failover(tmp_path, monkeypatch):
    calls: list[str] = []

    def participant(agent: str, _prompt: str, **_kwargs):
        calls.append(agent)
        if agent.endswith("codex-shadow"):
            raise ValueError("malformed ACP output")
        raise PermissionError("AUTH_REQUIRED")

    controller = _controller(tmp_path, monkeypatch, participant, lambda *_a, **_k: _result("codex", "partial"))
    try:
        payload = _run(controller, rounds=1)
    finally:
        controller.close()

    assert sorted(calls) == ["acpx-codex-shadow", "acpx-grok-shadow"]
    assert payload["state"] == "PARTIAL_COMPLETE"
    assert {item["outcome"] for item in payload["participant_outcomes"]} == {"error"}


def test_racing_reservations_never_expose_a_conversation_without_created_event(tmp_path, monkeypatch):
    barrier = threading.Barrier(2)
    returned: list[tuple[str, dict | None]] = []
    errors: list[BaseException] = []

    def reserve():
        barrier.wait(timeout=2)
        controller = _controller(
            tmp_path, monkeypatch, lambda *_a, **_k: _result("codex", "x"), lambda *_a, **_k: _result("codex", "x")
        )
        try:
            try:
                returned.append(controller._reserve(
                    task_digest="a", correlation_digest="b", idempotency_digest="same-key", rounds=1,
                    deadline_at="2099-01-01T00:00:00Z",
                ))
            except acpx_discuss.AcpxDiscussionError as exc:
                errors.append(exc)
        finally:
            controller.close()

    threads = [threading.Thread(target=reserve) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)
    assert len(returned) == 1
    assert len(errors) == 1
    assert "still in progress" in str(errors[0])
    conversation_ids = {item[0] for item in returned}
    assert len(conversation_ids) == 1
    conversation_id = next(iter(conversation_ids))
    conn = sqlite3.connect(tmp_path / "plane" / "comms.sqlite3")
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM acp_conversation_events WHERE conversation_id = ? AND state = 'CREATED'",
            (conversation_id,),
        ).fetchone()[0] == 1
    finally:
        conn.close()
