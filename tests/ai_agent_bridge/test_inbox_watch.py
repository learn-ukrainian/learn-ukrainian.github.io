"""Unit coverage for the live-driver legacy-inbox wakeup watcher."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from scripts.ai_agent_bridge import _db, _inbox_watch, _messaging


@pytest.fixture(autouse=True)
def isolate_db(tmp_path: Path):
    """Create an isolated broker database with the current messages schema."""
    db_path = tmp_path / "messages.db"
    with (
        patch("scripts.ai_agent_bridge._config.DB_PATH", db_path),
        patch("scripts.ai_agent_bridge._db.DB_PATH", db_path),
    ):
        _db.init_db().close()
        yield db_path


def _send(
    content: str,
    *,
    task_id: str = "review-pr-5687",
    to_llm: str = "grok",
    consumed: bool = False,
) -> int:
    message_id = _messaging.send_message(
        content,
        task_id=task_id,
        from_llm="claude",
        to_llm=to_llm,
        quiet=True,
    )
    if consumed:
        _messaging.acknowledge(message_id, quiet=True, consumed_by_live_driver=True)
    return message_id


def test_cold_start_surfaces_existing_unconsumed_alias_rows(isolate_db: Path):
    """A watcher begins at zero and includes permanent read aliases."""
    canonical_id = _send("canonical pending", to_llm="grok")
    alias_id = _send("historical pending", to_llm="grok-build")
    _send("already consumed", to_llm="grok", consumed=True)

    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
    finally:
        conn.close()

    assert [event.message_id for event in events] == [canonical_id, alias_id]
    query = _inbox_watch.build_poll_query(("grok", "grok-build"))
    assert "to_llm IN (?, ?)" in query
    assert "consumed_by_live_driver = 0" in query
    assert "ORDER BY id ASC" in query


def test_cursor_advances_after_emission_and_does_not_reemit(isolate_db: Path):
    """The in-memory cursor suppresses events only after their flush succeeds."""
    message_id = _send("please drain")
    output = io.StringIO()
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
        cursor = _inbox_watch.emit_notifications(events, last_seen=0, output=output)
        repeated = _inbox_watch.poll_once(conn, "grok", last_seen=cursor)
    finally:
        conn.close()

    assert cursor == message_id
    assert repeated == []
    assert f"id={message_id}" in output.getvalue()


def test_empty_poll_is_silent(isolate_db: Path, tmp_path: Path):
    """An empty monitor tick writes no stdout notification."""
    output = io.StringIO()
    cursor = _inbox_watch.run_watcher(
        "grok",
        db_path=isolate_db,
        lock_dir=tmp_path / "locks",
        output=output,
        once=True,
    )

    assert cursor == 0
    assert output.getvalue() == ""


def test_notification_escapes_newlines_and_bounds_preview(isolate_db: Path):
    """One message always creates one bounded Monitor event line."""
    message_id = _send("first line\nsecond line\r\n" + ("x" * 400))
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        event = _inbox_watch.poll_once(conn, "grok", last_seen=0)[0]
    finally:
        conn.close()

    line = event.notification_line()
    preview = line.split("preview=", maxsplit=1)[1]
    assert f"id={message_id}" in line
    assert "sender=claude" in line
    assert "request_id=review-pr-5687" in line
    assert "first line\\nsecond line\\r\\n" in line
    assert "\n" not in line
    assert len(preview) == _inbox_watch.MAX_PREVIEW_CHARS + len("...")


def test_duplicate_watcher_lock_blocks_second_start(isolate_db: Path, tmp_path: Path):
    """A second process cannot own the same canonical agent-slot watcher lock."""
    lock_dir = tmp_path / "locks"
    first = _inbox_watch.acquire_watcher_lock("grok", lock_dir)
    try:
        with pytest.raises(_inbox_watch.WatcherAlreadyRunningError, match="already running"):
            _inbox_watch.run_watcher(
                "grok-build",
                db_path=isolate_db,
                lock_dir=lock_dir,
                once=True,
            )
    finally:
        first.release()

    assert (
        _inbox_watch.run_watcher(
            "grok-build",
            db_path=isolate_db,
            lock_dir=lock_dir,
            once=True,
        )
        == 0
    )


def test_cursor_does_not_advance_when_stdout_flush_fails(isolate_db: Path):
    """A failed event flush leaves the caller's cursor unchanged for replay."""
    _send("retry this")
    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok", last_seen=0)
    finally:
        conn.close()

    class BrokenOutput:
        def write(self, _line: str) -> int:
            return 1

        def flush(self) -> None:
            raise OSError("stdout closed")

    last_seen = 0
    with pytest.raises(OSError, match="stdout closed"):
        last_seen = _inbox_watch.emit_notifications(events, last_seen=last_seen, output=BrokenOutput())
    assert last_seen == 0


def test_inbox_watcher_tick_invokes_ask_watchdog(isolate_db: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """The persistent inbox watcher loop invokes run_ask_watchdog on each tick (#5893)."""
    watchdog_mock = patch("scripts.ai_agent_bridge._ask_lifecycle.run_ask_watchdog").start()
    try:
        _inbox_watch.run_watcher(
            "grok",
            db_path=isolate_db,
            lock_dir=tmp_path / "locks",
            output=io.StringIO(),
            once=True,
        )
        watchdog_mock.assert_called_once()
    finally:
        patch.stopall()


def test_inbox_watcher_watchdog_failure_warns_and_continues(
    isolate_db: Path, tmp_path: Path, capsys: pytest.CaptureFixture
):
    """A raising ask watchdog emits a stderr warning and does not crash the watcher loop (#5893)."""
    watchdog_mock = patch(
        "scripts.ai_agent_bridge._ask_lifecycle.run_ask_watchdog", side_effect=RuntimeError("watchdog exploded")
    ).start()
    try:
        cursor = _inbox_watch.run_watcher(
            "grok",
            db_path=isolate_db,
            lock_dir=tmp_path / "locks",
            output=io.StringIO(),
            once=True,
        )
        assert cursor == 0
        watchdog_mock.assert_called_once()
        stderr = capsys.readouterr().err
        assert "⚠️  inbox watcher: ask watchdog failed: RuntimeError: watchdog exploded" in stderr
    finally:
        patch.stopall()


def test_recipients_for_agent_resolves_phantom_empty_roster_identity():
    """A phantom {provider}-{empty-slots-area} identity resolves to provider aliases (#7597)."""
    recipients = _inbox_watch.recipients_for_agent("grok-open-model-data")
    assert recipients == ("grok", "grok-build")
    assert "grok-open-model-data" not in recipients
    assert _inbox_watch.canonical_slot("grok-open-model-data") == "grok"


def test_poll_once_surfaces_messages_for_phantom_empty_roster_identity(isolate_db: Path):
    """Watcher polling for a phantom identity queries messages for the resolved provider aliases."""
    canonical_id = _send("canonical message", to_llm="grok")
    alias_id = _send("historical message", to_llm="grok-build")

    conn = _inbox_watch.open_readonly_db(isolate_db)
    try:
        events = _inbox_watch.poll_once(conn, "grok-open-model-data", last_seen=0)
    finally:
        conn.close()

    assert [event.message_id for event in events] == [canonical_id, alias_id]


def test_live_supervisory_retries_outages_until_prepared(capsys):
    from scripts.session_supervisor.remote import RemoteUnavailableError, RemoteUnreachableError

    request = _inbox_watch.SupervisoryRequest("delivery-test", "epic:9999", "restart", 1)
    with (
        patch("agents_extensions.shared.session_streams.hooks.lease_from_environment"),
        patch("scripts.fleet_comms.authority.AuthorityService"),
        patch("scripts.session_supervisor.SessionSupervisor"),
        patch.object(_inbox_watch, "consume_supervisory_event", side_effect=[
            RemoteUnreachableError("hostile $(secret)"), None,
            RemoteUnavailableError("hostile $(secret)"), request,
        ]) as consume,
        patch.object(_inbox_watch.time, "sleep") as sleep,
    ):
        assert _inbox_watch.run_live_supervisory_watcher(interval_seconds=0.25) == 75
    assert consume.call_count == 4
    assert sleep.call_args_list == [((0.25,),)] * 3
    captured = capsys.readouterr()
    assert captured.out == "delivery-test\n"
    assert captured.err.count("waiting for Monitor API to recover") == 2
    assert "secret" not in captured.err


@pytest.mark.parametrize("result", [75, 2, 76, "permanent", "transient"])
def test_live_supervisory_notifies_only_prepared_wake(result):
    from scripts.session_supervisor.remote import RemoteUnreachableError

    error = None
    if result == "permanent":
        error = ValueError("bad lease")
    elif result == "transient":
        error = RemoteUnreachableError("unreachable")
    with (
        patch("agents_extensions.shared.session_streams.hooks.lease_from_environment") as lease,
        patch.object(_inbox_watch.os, "getppid", return_value=12345),
        patch.object(_inbox_watch.os, "kill") as kill,
        patch.object(_inbox_watch, "run_live_supervisory_watcher", return_value=result, side_effect=error),
    ):
        lease.return_value.holder.process_id = 12345
        expected = 2 if result == "permanent" else 76 if result == "transient" else result
        assert _inbox_watch.main(["grok", "--live-supervisory", "--notify-parent"]) == expected
    if result == 75:
        kill.assert_called_once_with(12345, _inbox_watch.signal.SIGUSR1)
    else:
        kill.assert_not_called()


def test_live_supervisory_rejects_wrong_parent_without_notification():
    with (
        patch("agents_extensions.shared.session_streams.hooks.lease_from_environment") as lease,
        patch.object(_inbox_watch.os, "getppid", return_value=12345),
        patch.object(_inbox_watch.os, "kill") as kill,
        patch.object(_inbox_watch, "run_live_supervisory_watcher") as run,
    ):
        lease.return_value.holder.process_id = 54321
        assert _inbox_watch.main(["grok", "--live-supervisory", "--notify-parent"]) == 2
    kill.assert_not_called()
    run.assert_not_called()


@pytest.mark.parametrize("http_error", [False, True])
def test_monitor_server_failure_is_retryable_without_remote_diagnostics(http_error):
    import urllib.error
    from unittest.mock import MagicMock

    from scripts.session_supervisor.remote import RemoteEpicClient, RemoteUnavailableError

    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 503
    response.read.return_value = b'{"detail":"hostile-secret"}'

    def opener(*args, **kwargs):
        if http_error:
            raise urllib.error.HTTPError("http://localhost", 503, "unavailable", {}, io.BytesIO(response.read()))
        return response

    with pytest.raises(RemoteUnavailableError) as error:
        RemoteEpicClient(opener=opener).health()
    assert str(error.value) == "Monitor API temporarily unavailable (503)"
