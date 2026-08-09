"""Deterministic controller tests for the bounded active ACPX discussion."""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
import subprocess
import threading
from pathlib import Path

import pytest

from scripts.agent_runtime import acpx_discuss
from scripts.agent_runtime.errors import AgentTimeoutError
from scripts.agent_runtime.result import Result
from scripts.fleet_comms import migrations
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.authority import AuthorityService
from scripts.fleet_comms.message_plane import default_plane_root
from scripts.guardrails.worktree_containment import resolve_main_root


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


def test_controller_adopts_exact_authority_reservation_without_second_conversation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "plane"
    prompt = "Compare the bounded fixture."
    task_id = "task-6243"
    correlation_id = "correlation-6243"
    idempotency_key = "discussion-6243"
    with AuthorityService(root=root) as service:
        job = service.enqueue_discussion(
            channel="acp-health",
            prompt=prompt,
            participants=("kimi", "glm"),
            rounds=1,
            task_digest=hashlib.sha256(task_id.encode()).hexdigest(),
            correlation_id=correlation_id,
            deadline_at="2036-06-01T01:00:00Z",
            source="codex",
            task_id=task_id,
            idempotency_key=idempotency_key,
        )

    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda agent, *_a, **_k: _result(agent, f"{agent} evidence"),
        lambda agent, *_a, **_k: _result(agent, "synthesis"),
    )
    try:
        payload = controller.run(
            prompt=prompt,
            cwd=Path.cwd(),
            task_id=task_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            rounds=1,
            participants=("kimi", "glm"),
            source="codex",
            reserved_conversation_id=job.subject_id,
        )
        conversation_count = controller.conn.execute(
            "SELECT COUNT(*) FROM acp_conversations"
        ).fetchone()[0]
        created_count = controller.conn.execute(
            """SELECT COUNT(*) FROM acp_conversation_events
               WHERE conversation_id = ? AND event_type = 'CREATED'""",
            (job.subject_id,),
        ).fetchone()[0]
    finally:
        controller.close()

    assert payload["conversation_id"] == job.subject_id
    assert payload["classification"] == "complete"
    assert conversation_count == 1
    assert created_count == 1


def test_expired_authority_reservation_uses_existing_terminal_orphan_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "plane"
    with AuthorityService(root=root) as service:
        job = service.enqueue_discussion(
            channel="acp-health",
            prompt="Recover without calling providers.",
            participants=("kimi", "glm"),
            rounds=1,
            task_digest=hashlib.sha256(b"task-6243-orphan").hexdigest(),
            correlation_id="correlation-6243-orphan",
            deadline_at="2000-01-01T00:00:00Z",
            source="codex",
            task_id="task-6243-orphan",
            idempotency_key="discussion-6243-orphan",
        )

    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: pytest.fail("orphan recovery must not call a participant"),
        lambda *_a, **_k: pytest.fail("orphan recovery must not synthesize"),
    )
    try:
        with acpx_discuss._discussion_admission(controller.store.root):
            recovered = controller.recover_expired_reservations()
        terminal = controller._state(job.subject_id)
    finally:
        controller.close()

    assert recovered == [job.subject_id]
    assert terminal == "PARTIAL_COMPLETE"


def test_enabled_nondefault_pair_uses_fixed_acp_seats_and_persists_participants(
    tmp_path, monkeypatch
):
    calls: list[tuple[str, str]] = []

    def participant(agent: str, _prompt: str, **kwargs):
        calls.append((agent, kwargs["tool_config"]["target_agent"]))
        return _result(agent, f"{agent} evidence")

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
    try:
        result = controller.run(
            prompt="Compare the two bounded options.",
            cwd=Path.cwd(),
            task_id="task-6130",
            correlation_id="corr-6130",
            idempotency_key="idem-6130-generic",
            rounds=1,
            participants=("claude", "kimicc"),
        )
        stored = controller.conn.execute(
            "SELECT participants_json FROM acp_conversations WHERE conversation_id = ?",
            (result["conversation_id"],),
        ).fetchone()[0]
    finally:
        controller.close()

    assert sorted(calls) == [
        ("acpx-claude-shadow", "claude"),
        ("acpx-kimicc-shadow", "kimi"),
    ]
    assert stored == '["claude", "kimicc"]'
    receipt = acpx_discuss.verify_discussion_receipt(
        root=tmp_path / "plane", conversation_id=result["conversation_id"]
    )
    assert receipt["participants"] == ["claude", "kimicc"]
    assert receipt["checks"]["fixed_participants"] is True


def test_conversation_survives_dispatch_worktree_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("LU_ACPX_TRANSPORT", "active")
    monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
    monkeypatch.setattr(acpx_discuss, "classify_repo_path", lambda *_a, **_k: "dispatch_worktree")
    primary = tmp_path / "primary"
    (primary / ".git").mkdir(parents=True)
    worktree = primary / ".worktrees" / "dispatch" / "codex" / "acp-proof"
    worktree.mkdir(parents=True)
    (worktree / ".git").write_text(
        f"gitdir: {primary / '.git' / 'worktrees' / 'acp-proof'}\n",
        encoding="utf-8",
    )
    root = default_plane_root(repo_root=worktree)
    with ArtifactStore(repo_root=worktree) as default_store:
        assert default_store.root == root
    controller = acpx_discuss.AcpxDiscussionController(
        root=root,
        participant_call=lambda agent, _prompt, **_kwargs: _result(agent, f"{agent} evidence"),
        synthesis_call=lambda agent, _prompt, **_kwargs: _result(agent, "durable synthesis"),
    )
    try:
        payload = controller.run(
            prompt="Prove cleanup durability.",
            cwd=worktree,
            task_id="task-6087",
            correlation_id="corr-6087",
            idempotency_key="idem-6087",
            rounds=1,
        )
    finally:
        controller.close()

    shutil.rmtree(primary / ".worktrees")

    assert root == primary / "batch_state" / "fleet-comms" / "v1"
    assert not worktree.exists()
    with ArtifactStore(root=root) as reopened:
        row = reopened.connection.execute(
            "SELECT state FROM acp_conversation_events "
            "WHERE conversation_id = ? ORDER BY sequence DESC LIMIT 1",
            (payload["conversation_id"],),
        ).fetchone()
        assert row is not None
        assert row[0] == "COMPLETE"


class _InjectedPersistenceCrash(RuntimeError):
    """Simulates process loss at a named ACP body-persistence boundary."""


@pytest.mark.parametrize("boundary", ("blob", "artifact", "message", "link"))
def test_message_persistence_rolls_back_every_precommit_boundary(
    tmp_path, monkeypatch, boundary
):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: _result("codex", "unused"),
        lambda *_a, **_k: _result("codex", "unused"),
    )
    conversation_id, replay = controller._reserve(
        task_digest="task",
        correlation_digest="correlation",
        idempotency_digest=f"crash-{boundary}",
        rounds=1,
        deadline_at="2099-01-01T00:00:00Z",
    )
    assert replay is None

    if boundary == "blob":
        original_write = controller.store._write_blob_atomic

        def crash_after_blob_write(dest, data):
            original_write(dest, data)
            raise _InjectedPersistenceCrash("after blob write")

        monkeypatch.setattr(controller.store, "_write_blob_atomic", crash_after_blob_write)
    elif boundary == "artifact":
        original_store_text = controller.store.store_text

        def crash_after_artifact(*args, **kwargs):
            original_store_text(*args, **kwargs)
            raise _InjectedPersistenceCrash("after artifact insert")

        monkeypatch.setattr(controller.store, "store_text", crash_after_artifact)
    elif boundary == "message":
        def crash_before_link(*_args, **_kwargs):
            raise _InjectedPersistenceCrash("after message insert")

        monkeypatch.setattr(controller.store, "reference", crash_before_link)
    else:
        original_reference = controller.store.reference

        def crash_after_link(*args, **kwargs):
            original_reference(*args, **kwargs)
            raise _InjectedPersistenceCrash("after link insert")

        monkeypatch.setattr(controller.store, "reference", crash_after_link)

    root = controller.store.root
    try:
        with pytest.raises(_InjectedPersistenceCrash):
            controller._message(
                conversation_id,
                sender="codex",
                recipient="root",
                body="crash-boundary body",
                reply_to=None,
            )
    finally:
        controller.close()

    with ArtifactStore(root=root) as reopened:
        assert reopened.connection.execute(
            "SELECT COUNT(*) FROM comms_messages WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()[0] == 0
        assert reopened.connection.execute(
            "SELECT COUNT(*) FROM message_artifacts",
        ).fetchone()[0] == 0
        assert reopened.connection.execute(
            "SELECT COUNT(*) FROM artifacts",
        ).fetchone()[0] == 0
        assert reopened.garbage_collect_unreferenced(grace_seconds=0) == []


def test_committed_message_body_is_gc_visible_after_zero_grace(tmp_path, monkeypatch):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: _result("codex", "unused"),
        lambda *_a, **_k: _result("codex", "unused"),
    )
    root = controller.store.root
    try:
        conversation_id, replay = controller._reserve(
            task_digest="task",
            correlation_digest="correlation",
            idempotency_digest="committed-message",
            rounds=1,
            deadline_at="2099-01-01T00:00:00Z",
        )
        assert replay is None
        message_id = controller._message(
            conversation_id,
            sender="codex",
            recipient="root",
            body="durable body",
            reply_to=None,
        )
        artifact_id = controller.conn.execute(
            "SELECT body_artifact_id FROM comms_messages WHERE message_id = ?",
            (message_id,),
        ).fetchone()[0]
        assert controller.conn.execute(
            "SELECT 1 FROM message_artifacts WHERE message_id = ? AND artifact_id = ?",
            (message_id, artifact_id),
        ).fetchone() is not None
    finally:
        controller.close()

    with ArtifactStore(root=root) as reopened:
        assert reopened.connection.execute(
            "SELECT 1 FROM comms_messages WHERE message_id = ?",
            (message_id,),
        ).fetchone() is not None
        assert reopened.connection.execute(
            "SELECT 1 FROM message_artifacts WHERE message_id = ? AND artifact_id = ?",
            (message_id, artifact_id),
        ).fetchone() is not None
        assert reopened.garbage_collect_unreferenced(grace_seconds=0) == []
        assert reopened.get(artifact_id).artifact_id == artifact_id


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

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
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
        terminal_events = controller.conn.execute(
            """SELECT event_type, state, outcome
               FROM acp_conversation_events
               WHERE conversation_id = ?
                 AND event_type IN ('ORPHAN_RESERVATION', 'DUPLICATE_SUPPRESSED')
               ORDER BY sequence""",
            (conversation_id,),
        ).fetchall()
    finally:
        controller.close()

    assert replay_payload["state"] == "PARTIAL_COMPLETE"
    assert replay_payload["duplicate_suppressed"] is True
    assert [tuple(event) for event in terminal_events] == [
        ("ORPHAN_RESERVATION", "PARTIAL_COMPLETE", "orphan"),
        ("DUPLICATE_SUPPRESSED", "PARTIAL_COMPLETE", "duplicate_suppressed"),
    ]


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


def test_concurrent_expired_orphan_recovery_returns_idempotent_replays(
    tmp_path, monkeypatch
):
    seed = _controller(
        tmp_path,
        monkeypatch,
        lambda *_a, **_k: pytest.fail("orphan must not invoke participants"),
        lambda *_a, **_k: pytest.fail("orphan must not invoke synthesis"),
    )
    digest = acpx_discuss._digest("racing-orphan")
    try:
        conversation_id, replay = seed._reserve(
            task_digest="a",
            correlation_digest="b",
            idempotency_digest=digest,
            rounds=2,
            deadline_at="2000-01-01T00:00:00Z",
        )
        assert replay is None
        seed._append(
            conversation_id,
            event_type="STATE",
            state="INITIAL_FANOUT",
            transition=True,
        )
    finally:
        seed.close()

    recovery_barrier = threading.Barrier(2)
    original_append = acpx_discuss.AcpxDiscussionController._append

    def synchronized_append(self, *args, **kwargs):
        if kwargs.get("event_type") == "ORPHAN_RESERVATION":
            recovery_barrier.wait(timeout=2)
        return original_append(self, *args, **kwargs)

    monkeypatch.setattr(
        acpx_discuss.AcpxDiscussionController,
        "_append",
        synchronized_append,
    )
    returned: list[tuple[str, dict | None]] = []
    errors: list[BaseException] = []

    def recover():
        controller = _controller(
            tmp_path,
            monkeypatch,
            lambda *_a, **_k: pytest.fail("orphan must not invoke participants"),
            lambda *_a, **_k: pytest.fail("orphan must not invoke synthesis"),
        )
        try:
            try:
                returned.append(
                    controller._reserve(
                        task_digest="a",
                        correlation_digest="b",
                        idempotency_digest=digest,
                        rounds=2,
                        deadline_at="2000-01-01T00:00:00Z",
                    )
                )
            except BaseException as exc:
                errors.append(exc)
        finally:
            controller.close()

    threads = [threading.Thread(target=recover) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)

    assert errors == []
    assert len(returned) == 2
    assert {item[0] for item in returned} == {conversation_id}
    assert all(item[1]["state"] == "PARTIAL_COMPLETE" for item in returned)
    assert all(item[1]["duplicate_suppressed"] is True for item in returned)


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


def test_repository_wide_busy_rejects_without_queueing_or_retries(tmp_path, monkeypatch):
    calls = 0

    def participant(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("repository admission refusal must not invoke a participant")

    controller = _controller(tmp_path, monkeypatch, participant, lambda *_a, **_k: _result("codex", "partial"))
    try:
        with acpx_discuss._discussion_admission(controller.store.root):
            with pytest.raises(acpx_discuss.AcpxDiscussionBusyError, match="already running"):
                _run(controller, rounds=1)
    finally:
        controller.close()

    assert calls == 0


def test_terminal_replay_bypasses_repository_busy_admission(tmp_path, monkeypatch):
    calls: list[str] = []

    def participant(agent: str, _prompt: str, **_kwargs):
        calls.append(agent)
        return _result(agent, f"{agent} evidence")

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
    try:
        first = _run(controller, rounds=1)
        with acpx_discuss._discussion_admission(controller.store.root):
            replay = _run(controller, rounds=1)
    finally:
        controller.close()

    assert first["state"] == "COMPLETE"
    assert replay["conversation_id"] == first["conversation_id"]
    assert replay["duplicate_suppressed"] is True
    assert sorted(calls) == ["acpx-codex-shadow", "acpx-grok-shadow"]


def test_crashed_process_releases_repository_admission_lock(tmp_path):
    root = tmp_path / "plane"
    root.mkdir()
    repo_root = Path(__file__).resolve().parents[2]
    python = resolve_main_root(repo_root) / ".venv" / "bin" / "python"
    code = """
import os
import sys
from pathlib import Path
from scripts.agent_runtime.acpx_discuss import _discussion_admission
with _discussion_admission(Path(sys.argv[1])):
    os._exit(17)
"""
    completed = subprocess.run(
        [str(python), "-c", code, str(root)],
        cwd=repo_root,
        check=False, timeout=30,
    )

    assert completed.returncode == 17
    with acpx_discuss._discussion_admission(root):
        pass


def test_body_free_receipt_verifies_complete_replayed_conversation(tmp_path, monkeypatch):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda agent, _prompt, **_kwargs: _result(agent, "private participant body"),
        lambda agent, _prompt, **_kwargs: _result(agent, "private synthesis body"),
    )
    try:
        first = _run(controller, rounds=2)
        replay = _run(controller, rounds=2)
    finally:
        controller.close()

    receipt = acpx_discuss.verify_discussion_receipt(
        root=tmp_path / "plane",
        conversation_id=first["conversation_id"],
        require_replay=True,
    )

    assert replay["duplicate_suppressed"] is True
    assert receipt["verified"] is True
    assert receipt["content_included"] is False
    assert receipt["successful_rounds"] == 2
    assert receipt["duplicate_suppressed_count"] == 1
    assert receipt["checks"] == {
        "storage_metadata_valid": True,
        "fixed_participants": True,
        "terminal_complete": True,
        "all_rounds_succeeded": True,
        "synthesis_succeeded": True,
        "replay_observed": True,
    }
    serialized = str(receipt)
    assert "private participant body" not in serialized
    assert "private synthesis body" not in serialized


def test_body_free_receipt_reports_partial_without_claiming_success(tmp_path, monkeypatch):
    def participant(agent: str, _prompt: str, **_kwargs):
        if agent.endswith("grok-shadow"):
            raise AgentTimeoutError("fixture timeout")
        return _result(agent, "private codex body")

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "private partial synthesis"),
    )
    try:
        result = _run(controller, rounds=1)
    finally:
        controller.close()

    receipt = acpx_discuss.verify_discussion_receipt(
        root=tmp_path / "plane",
        conversation_id=result["conversation_id"],
    )

    assert result["state"] == "PARTIAL_COMPLETE"
    assert receipt["verified"] is False
    assert "terminal_complete" in receipt["reasons"]
    assert "all_rounds_succeeded" in receipt["reasons"]
    assert receipt["content_included"] is False


def test_body_free_receipt_never_reflects_poisoned_storage_text(tmp_path, monkeypatch):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda agent, _prompt, **_kwargs: _result(agent, "private participant body"),
        lambda agent, _prompt, **_kwargs: _result(agent, "private synthesis body"),
    )
    try:
        result = _run(controller, rounds=1)
        controller.conn.execute(
            """UPDATE acp_conversation_events
               SET outcome = 'PRIVATE_PROMPT', created_at = 'PRIVATE_RESPONSE'
               WHERE conversation_id = ? AND event_type = 'CALL_TERMINAL'
                 AND sender = 'grok'""",
            (result["conversation_id"],),
        )
        controller.conn.execute(
            "UPDATE acp_conversations SET created_at = 'PRIVATE_TASK' WHERE conversation_id = ?",
            (result["conversation_id"],),
        )
        controller.conn.execute(
            """UPDATE acp_conversation_events SET created_at = 'PRIVATE_TERMINAL'
               WHERE conversation_id = ? AND event_type = 'STATE' AND state = 'COMPLETE'""",
            (result["conversation_id"],),
        )
        controller.conn.commit()
    finally:
        controller.close()

    receipt = acpx_discuss.verify_discussion_receipt(
        root=tmp_path / "plane",
        conversation_id=result["conversation_id"],
    )

    serialized = str(receipt)
    assert receipt["verified"] is False
    assert receipt["checks"]["storage_metadata_valid"] is False
    assert receipt["participant_outcomes"][1]["outcomes"] == {"other_failure": 1}
    assert "PRIVATE_PROMPT" not in serialized
    assert "PRIVATE_RESPONSE" not in serialized
    assert "PRIVATE_TASK" not in serialized
    assert "PRIVATE_TERMINAL" not in serialized
    assert "private participant body" not in serialized
    assert "private synthesis body" not in serialized


def test_body_free_receipt_refuses_missing_or_invalid_conversation(tmp_path):
    with pytest.raises(acpx_discuss.AcpxDiscussionError, match="canonical"):
        acpx_discuss.verify_discussion_receipt(
            root=tmp_path,
            conversation_id="not-a-conversation",
        )
    with pytest.raises(acpx_discuss.AcpxDiscussionNotFoundError, match="storage"):
        acpx_discuss.verify_discussion_receipt(
            root=tmp_path,
            conversation_id="conversation_" + ("a" * 32),
        )


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


def test_fast_participant_is_persisted_before_slow_participant_finishes(tmp_path, monkeypatch):
    fast_recorded = threading.Event()

    def participant(agent: str, _prompt: str, **_kwargs):
        if agent.endswith("codex-shadow"):
            assert fast_recorded.wait(timeout=1)
            return _result(agent, "slow")
        return _result(agent, "fast")

    controller = _controller(tmp_path, monkeypatch, participant, lambda *_a, **_k: _result("codex", "unused"))
    original_append = controller._append

    def observing_append(*args, **kwargs):
        original_append(*args, **kwargs)
        if kwargs.get("event_type") == "CALL_TERMINAL" and kwargs.get("sender") == "grok":
            fast_recorded.set()

    controller._append = observing_append  # type: ignore[method-assign]
    try:
        conversation_id, replay = controller._reserve(
            task_digest="task", correlation_digest="corr", idempotency_digest="idem",
            rounds=1, deadline_at="2099-01-01T00:00:00Z",
        )
        assert replay is None
        outcomes = controller._call_wave(
            conversation_id=conversation_id,
            task_id="task",
            correlation_id="corr",
            idempotency_key="idem",
            cwd=Path.cwd(),
            round_no=1,
            prompts={"codex": "prompt", "grok": "prompt"},
            deliveries={"codex": ("root", "prompt", None), "grok": ("root", "prompt", None)},
            state="INITIAL_FANOUT",
            deadline=controller.clock() + 10,
        )
    finally:
        controller.close()

    assert fast_recorded.is_set()
    assert [outcome.participant for outcome in outcomes] == ["codex", "grok"]


def test_expired_recovery_is_terminal_without_provider_retry(tmp_path, monkeypatch):
    calls: list[str] = []

    def participant(agent: str, _prompt: str, **_kwargs):
        calls.append(agent)
        return _result(agent, "must not run")

    controller = _controller(tmp_path, monkeypatch, participant, participant)
    try:
        conversation_id, replay = controller._reserve(
            task_digest="task", correlation_digest="corr", idempotency_digest="expired-idem",
            rounds=1, deadline_at="2000-01-01T00:00:00Z",
        )
        assert replay is None
        controller._append(
            conversation_id, event_type="STATE", state="INITIAL_FANOUT", transition=True,
        )
    finally:
        controller.close()

    recovered = acpx_discuss.recover_expired_discussions(root=tmp_path / "plane")
    conn = sqlite3.connect(tmp_path / "plane" / "comms.sqlite3")
    try:
        event = conn.execute(
            "SELECT event_type, state, outcome FROM acp_conversation_events "
            "WHERE conversation_id = ? ORDER BY sequence DESC LIMIT 1",
            (conversation_id,),
        ).fetchone()
    finally:
        conn.close()

    assert recovered == [conversation_id]
    assert tuple(event) == ("ORPHAN_RESERVATION", "PARTIAL_COMPLETE", "orphan")
    assert calls == []


def test_recovery_ignores_authority_native_discussion_rows(tmp_path, monkeypatch):
    controller = _controller(
        tmp_path,
        monkeypatch,
        lambda agent, _prompt, **_kwargs: _result(agent, f"{agent} evidence"),
        lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
    authority_conversation_id = "conversation_" + ("a" * 32)
    try:
        controller.conn.execute(
            "INSERT INTO conversations(conversation_id, created_at, source, title) "
            "VALUES (?, '2000-01-01T00:00:00Z', 'authority-discussion', 'authority')",
            (authority_conversation_id,),
        )
        controller.conn.execute(
            """INSERT INTO acp_conversations(
                   conversation_id, task_digest, correlation_digest, idempotency_digest,
                   rounds_requested, participants_json, created_at, deadline_at,
                   token_budget, content_budget_bytes
               ) VALUES (?, 'task', 'correlation', 'authority-idempotency', 1,
                         '["codex","grok"]', '2000-01-01T00:00:00Z',
                         '2000-01-01T00:00:00Z', 100, 100)""",
            (authority_conversation_id,),
        )
        controller.conn.commit()

        payload = _run(controller, key="fresh-acpx-after-authority", rounds=1)
        authority_events = controller.conn.execute(
            "SELECT COUNT(*) FROM acp_conversation_events WHERE conversation_id = ?",
            (authority_conversation_id,),
        ).fetchone()[0]
    finally:
        controller.close()

    assert payload["state"] == "COMPLETE"
    assert authority_events == 0


def test_next_admitted_discussion_recovers_expired_reservation_before_new_calls(
    tmp_path, monkeypatch
):
    calls: list[str] = []

    def participant(agent: str, _prompt: str, **_kwargs):
        calls.append(agent)
        return _result(agent, "fresh evidence")

    controller = _controller(
        tmp_path,
        monkeypatch,
        participant,
        lambda agent, _prompt, **_kwargs: _result(agent, "synthesis"),
    )
    try:
        expired_id, _ = controller._reserve(
            task_digest="old-task",
            correlation_digest="old-corr",
            idempotency_digest="old-idem",
            rounds=1,
            deadline_at="2000-01-01T00:00:00Z",
        )
        controller._append(
            expired_id, event_type="STATE", state="INITIAL_FANOUT", transition=True
        )
        fresh = _run(controller, key="fresh-idem", rounds=1)
        expired_state = controller._state(expired_id)
    finally:
        controller.close()

    assert expired_state == "PARTIAL_COMPLETE"
    assert fresh["state"] == "COMPLETE"
    assert sorted(calls) == ["acpx-codex-shadow", "acpx-grok-shadow"]


def test_racing_reservations_never_expose_a_conversation_without_created_event(tmp_path, monkeypatch):
    barrier = threading.Barrier(2)
    migration_read_barrier = threading.Barrier(2)
    migration_read_state = threading.local()
    returned: list[tuple[str, dict | None]] = []
    errors: list[BaseException] = []

    original_applied_migrations = migrations._applied_migrations

    def synchronize_initial_migration_read(conn):
        applied = original_applied_migrations(conn)
        if not getattr(migration_read_state, "initial_read_complete", False):
            migration_read_state.initial_read_complete = True
            migration_read_barrier.wait(timeout=2)
        return applied

    monkeypatch.setattr(migrations, "_applied_migrations", synchronize_initial_migration_read)

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
            except BaseException as exc:
                errors.append(exc)
        finally:
            controller.close()

    threads = [threading.Thread(target=reserve) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=3)
    assert not any(thread.is_alive() for thread in threads)
    assert len(returned) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], acpx_discuss.AcpxDiscussionError)
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


def test_optional_projection_failure_never_changes_complete_discussion_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from scripts.entire_context import reconcile

    expected = {
        "conversation_id": "conversation_" + "a" * 32,
        "state": "COMPLETE",
        "classification": "complete",
    }

    class FakeController:
        def __init__(self, *, root: Path):
            self.root = root

        def run(self, **kwargs):
            del kwargs
            return dict(expected)

        def close(self):
            return None

    def fail_projection(**kwargs):
        del kwargs
        raise sqlite3.DatabaseError("projection-only failure")

    monkeypatch.setattr(acpx_discuss, "AcpxDiscussionController", FakeController)
    monkeypatch.setattr(reconcile, "project_terminal_acp_receipt", fail_projection)

    result = acpx_discuss.run_discussion(cwd=tmp_path)

    assert result == expected
    assert "optional ACP context projection failed: DatabaseError" in caplog.text
