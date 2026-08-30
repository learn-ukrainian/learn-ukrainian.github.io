"""#7485 exactly-once execution: atomic claim, reclaim, atomic finalize."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.fleet_comms.request_executor import (
    RequestExecutor,
    RequestExecutorError,
)

pytestmark = pytest.mark.repo_invariant


@pytest.fixture
def executor(tmp_path: Path) -> RequestExecutor:
    with RequestExecutor(root=tmp_path) as ex:
        yield ex


def _create(ex: RequestExecutor):
    return ex.create_request(recipient="codex", body="ping")


def test_second_claim_raises_instead_of_double_running(executor: RequestExecutor) -> None:
    req = _create(executor)
    done = executor.execute_capture(req.request_id, adapter="codex", stdout="ok")
    assert done.state in {"complete", "incomplete", "failed"}
    # A finished request is terminal — not claimable at all.
    with pytest.raises(RequestExecutorError, match="not executable"):
        executor.execute_capture(req.request_id, adapter="codex", stdout="again")


def test_running_request_requires_explicit_reclaim(executor: RequestExecutor) -> None:
    req = _create(executor)
    # Simulate a crashed executor: claim without finalizing.
    executor.connection_claim = None  # no-op attr; clarity only
    cur = executor.store.connection.execute(
        "UPDATE requests SET state = 'running' WHERE request_id = ?",
        (req.request_id,),
    )
    executor.store.connection.commit()
    assert cur.rowcount == 1
    with pytest.raises(RequestExecutorError, match="already claimed"):
        executor.execute_capture(req.request_id, adapter="codex", stdout="ok")
    done = executor.execute_capture(
        req.request_id, adapter="codex", stdout="ok", reclaim=True
    )
    assert done.state in {"complete", "incomplete"}


def test_finalize_failure_is_atomic(
    executor: RequestExecutor, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure inside finalize must leave NO partial state: request stays
    running (reconcilable via reclaim), no reply row, artifact unreferenced."""
    req = _create(executor)

    def boom(**_kw):
        raise RuntimeError("induced finalize failure")

    monkeypatch.setattr(executor, "_finalize_capture", boom)
    with pytest.raises(RuntimeError, match="induced finalize failure"):
        executor.execute_capture(req.request_id, adapter="codex", stdout="ok")

    current = executor.get_request(req.request_id)
    assert current.state == "running"  # claimed, unfinalized → reconcilable
    conn = executor.store.connection
    reply = conn.execute(
        "SELECT 1 FROM comms_messages WHERE kind = 'reply' AND in_reply_to = ?",
        (req.request_message_id,),
    ).fetchone()
    assert reply is None
    refs = conn.execute("SELECT COUNT(*) FROM message_artifacts").fetchone()[0]
    assert refs == 0  # capture artifact exists but is unreferenced → GC-able

    monkeypatch.undo()
    done = executor.execute_capture(
        req.request_id, adapter="codex", stdout="ok", reclaim=True
    )
    assert done.state in {"complete", "incomplete"}


def test_expired_request_still_expires_on_claim(executor: RequestExecutor) -> None:
    req = executor.create_request(recipient="codex", body="ping", ttl_seconds=-1)
    with pytest.raises(RequestExecutorError, match="expired"):
        executor.execute_capture(req.request_id, adapter="codex", stdout="ok")
    assert executor.get_request(req.request_id).state == "expired"
