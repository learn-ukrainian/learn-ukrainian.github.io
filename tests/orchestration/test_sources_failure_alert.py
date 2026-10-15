"""Safe-field, once-per-episode Fleet Comms notices for sources failures (#10674)."""

from __future__ import annotations

import contextlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.orchestration import sources_failure_alert as alert
from scripts.orchestration.backup_failure_alert import AlertError, fleet_comms_publisher
from scripts.rag.hang_diagnostics import READY_MARKER, open_state_dir

ROOT = Path(__file__).resolve().parents[2]
INVOCATION = "0123456789abcdef0123456789abcdef"
OTHER_INVOCATION = "fedcba9876543210fedcba9876543210"
NOW = "2026-10-15T15:00:00Z"
MESSAGE = re.compile(
    r"\[sources-alert\] schema=1 service=sources class=(watchdog|start_limit|startup|other) "
    r"episode=[0-9a-f]{32} at=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\n[^\n/]+\n"
)


class Publisher:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail = fail

    def __call__(self, message: str, key: str) -> None:
        self.calls.append((message, key))
        if self.fail:
            raise AlertError("fleet_comms publish exited 1: /home/op/private/plane.sqlite3 locked")

    @property
    def classes(self) -> list[str]:
        return [message.split()[3].removeprefix("class=") for message, _key in self.calls]


class FakeSystemd:
    """The server unit's state as ``systemctl show`` reports it."""

    def __init__(
        self, active: str = "active", sub: str = "running", result: str = "success", invocation: str = INVOCATION
    ):
        self.state = {"ActiveState": active, "SubState": sub, "Result": result, "InvocationID": invocation}
        self.reads = 0

    def set(self, active: str, sub: str, result: str, invocation: str = INVOCATION) -> None:
        self.state = {"ActiveState": active, "SubState": sub, "Result": result, "InvocationID": invocation}

    def __call__(self) -> dict[str, str]:
        self.reads += 1
        return dict(self.state)


@pytest.fixture
def dirs(tmp_path: Path) -> Iterator[tuple[int, int, Path, Path]]:
    """The sources unit's state directory and its notices directory."""
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    state_fd = open_state_dir(str(state))
    notices_fd = alert.open_notices(state_fd)
    try:
        yield state_fd, notices_fd, state, state / alert.NOTICES_DIR
    finally:
        os.close(notices_fd)
        os.close(state_fd)


def _stopped(result: str, invocation: str = INVOCATION, **extra: str) -> dict[str, str]:
    """The environment systemd gives ``ExecStopPost=``."""
    return {"SERVICE_RESULT": result, "INVOCATION_ID": invocation, **extra}


def _records(notices: Path) -> list[dict[str, object]]:
    return [json.loads(path.read_text()) for path in sorted(notices.glob("*.json"))]


def _ready(state: Path, invocation: str) -> None:
    (state / READY_MARKER).write_text(invocation + "\n")


@pytest.mark.parametrize(
    ("result", "reached_ready", "expected"),
    [
        ("watchdog", True, "watchdog"),
        ("watchdog", None, "watchdog"),
        ("start-limit-hit", None, "start_limit"),
        ("start-limit-hit", False, "start_limit"),
        ("exit-code", False, "startup"),
        ("protocol", False, "startup"),
        ("timeout", False, "startup"),
        ("exit-code", True, "other"),
        ("signal", True, "other"),
        ("oom-kill", None, "other"),
    ],
)
def test_classification(result: str, reached_ready: bool | None, expected: str) -> None:
    assert alert.classify(result, reached_ready) == expected


def test_a_watchdog_kill_after_readiness_records_one_safe_record(dirs) -> None:
    state_fd, notices_fd, state, notices = dirs
    _ready(state, INVOCATION)
    note = alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    assert note.startswith("watchdog episode ") and note.endswith(" recorded")
    [record] = _records(notices)
    assert set(record) == {"schema", "service", "episode", "class", "at"}
    assert record["class"] == "watchdog" and record["service"] == "sources" and record["schema"] == 1
    assert record["episode"] == alert.episode_id(INVOCATION, "watchdog")
    assert INVOCATION not in json.dumps(record)  # the episode id is opaque
    [path] = notices.glob("*.json")
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert oct(notices.stat().st_mode & 0o777) == "0o700"


def test_start_up_and_later_failures_are_told_apart_by_the_ready_marker(dirs) -> None:
    state_fd, notices_fd, state, notices = dirs
    _ready(state, OTHER_INVOCATION)  # an earlier run reached readiness, this one did not
    alert.record_stopped_run(_stopped("exit-code"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    _ready(state, INVOCATION)
    alert.record_stopped_run(
        _stopped("exit-code", OTHER_INVOCATION), state_fd=state_fd, notices_fd=notices_fd, now="2026-10-15T15:01:00Z"
    )
    # Without the server's state directory the class falls back to other.
    unit = FakeSystemd("failed", "failed", "exit-code", "f" * 32)
    alert.record_unit_state(unit, state_fd=None, notices_fd=notices_fd, now="2026-10-15T15:02:00Z")
    assert [record["class"] for record in sorted(_records(notices), key=lambda r: r["at"])] == [
        "startup",
        "startup",
        "other",
    ]


def test_the_start_limit_is_recorded_from_the_unit_state_after_the_last_failure(dirs) -> None:
    state_fd, notices_fd, state, notices = dirs
    _ready(state, INVOCATION)
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    # systemd refuses the restart: no process runs and no new invocation id.
    unit = FakeSystemd("failed", "failed", "start-limit-hit")
    alert.record_unit_state(unit, state_fd=state_fd, notices_fd=notices_fd, now="2026-10-15T15:00:05Z")
    records = _records(notices)
    assert sorted(record["class"] for record in records) == ["start_limit", "watchdog"]
    assert len({record["episode"] for record in records}) == 2


def test_the_stop_path_and_the_unit_state_record_the_same_run_once(dirs) -> None:
    """``ExecStopPost=`` and the notifier's state check key a run alike: one record, its first time."""
    state_fd, notices_fd, state, notices = dirs
    _ready(state, INVOCATION)
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    again = alert.record_stopped_run(
        _stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now="2026-10-15T16:00:00Z"
    )
    waiting = FakeSystemd("activating", "auto-restart", "watchdog")
    from_state = alert.record_unit_state(waiting, state_fd=state_fd, notices_fd=notices_fd, now="2026-10-15T16:00:01Z")
    assert again.endswith("already recorded") and from_state.endswith("already recorded")
    assert [record["at"] for record in _records(notices)] == [NOW]


@pytest.mark.parametrize(
    "unit_state",
    [
        ("active", "running", "success"),
        ("inactive", "dead", "success"),
        ("activating", "start", "success"),
        ("deactivating", "stop-sigterm", "success"),
        ("failed", "failed", ""),
    ],
)
def test_a_healthy_or_cleanly_stopped_unit_records_nothing(dirs, unit_state: tuple[str, str, str]) -> None:
    state_fd, notices_fd, _state, notices = dirs
    assert alert.record_unit_state(FakeSystemd(*unit_state), state_fd=state_fd, notices_fd=notices_fd, now=NOW) == (
        "the unit is not in a failed state"
    )
    for environ in (_stopped("success"), {"INVOCATION_ID": INVOCATION}, {}):
        assert alert.record_stopped_run(environ, state_fd=state_fd, notices_fd=notices_fd, now=NOW) == (
            "no failure to record"
        )
    assert list(notices.iterdir()) == []


def test_a_failure_without_a_valid_invocation_id_is_refused_not_given_a_random_key(dirs) -> None:
    """A random key would make the persisting start-limit state notify on every timer run."""
    state_fd, notices_fd, _state, notices = dirs
    for invocation in ("", "../../etc", "A" * 32):
        with pytest.raises(AlertError):
            alert.record_unit_state(
                FakeSystemd("failed", "failed", "start-limit-hit", invocation),
                state_fd=state_fd,
                notices_fd=notices_fd,
                now=NOW,
            )
        with pytest.raises(AlertError):
            alert.record_stopped_run(
                _stopped("watchdog", invocation), state_fd=state_fd, notices_fd=notices_fd, now=NOW
            )
    assert list(notices.iterdir()) == []


def test_an_interrupted_record_write_leaves_nothing_half_written(dirs, monkeypatch: pytest.MonkeyPatch) -> None:
    state_fd, notices_fd, _state, notices = dirs
    real_link = os.link

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(alert.os, "link", interrupted)
    with pytest.raises(KeyboardInterrupt):
        alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    assert list(notices.iterdir()) == []
    # A killed writer can leave its temporary file: it is never a record.
    (notices / f".{'a' * 32}-0000.tmp").write_text('{"partial": ')
    monkeypatch.setattr(alert.os, "link", real_link)
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    publish = Publisher()
    assert alert.publish_pending(notices_fd, publish) == alert.PublishResult(sent=1, failed=0, pending=0)
    assert len(publish.calls) == 1


def test_injected_paths_and_errors_never_reach_the_message(dirs) -> None:
    """Only the allowlisted fields leave the host, whatever systemd or old state carries."""
    state_fd, notices_fd, state, notices = dirs
    _ready(state, INVOCATION)
    secrets_seen = (
        "/home/op/learn-ukrainian/batch_state/sources-dumps/x.txt",
        "Traceback (most recent call last)",
        "sqlite3.OperationalError: database is locked",
        '{"status": "ok"',
    )
    environ = _stopped(
        "exit-code",
        EXIT_CODE="exited " + secrets_seen[0],
        EXIT_STATUS="1\n" + secrets_seen[1] + "\n" + secrets_seen[2],
        HEALTH_BODY=secrets_seen[3],
    )
    alert.record_stopped_run(environ, state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    alert.record_unit_state(
        FakeSystemd("failed", "failed", f"watchdog {secrets_seen[0]}", OTHER_INVOCATION),
        state_fd=state_fd,
        notices_fd=notices_fd,
        now="2026-10-15T15:00:01Z",
    )
    # A notice queued by the old watchdog, and tampered records.
    (notices / "old-incident.json").write_text(json.dumps({"message": f"hung; dump at {secrets_seen[0]}"}))
    good = alert.Record("b" * 32, "watchdog", "2026-10-15T14:00:00Z")
    (notices / good.name).write_text(json.dumps({**json.loads(good.as_json()), "detail": secrets_seen[1]}))
    bad_time = alert.Record("c" * 32, "other", "2026-10-15T14:00:00Z")
    (notices / bad_time.name).write_text(bad_time.as_json().replace("2026-10-15T14:00:00Z", secrets_seen[0]))
    misnamed = alert.Record("d" * 32, "other", "2026-10-15T14:00:00Z")
    (notices / ("e" * 32 + ".json")).write_text(misnamed.as_json())
    publish = Publisher()
    assert alert.publish_pending(notices_fd, publish) == alert.PublishResult(sent=2, failed=0, pending=0)
    assert len(publish.calls) == 2
    for message, key in publish.calls:
        assert MESSAGE.fullmatch(message), message
        assert re.fullmatch(r"lu-sources-alert:v1:[0-9a-f]{32}", key)
        for secret in secrets_seen:
            assert secret not in message
    assert publish.classes == ["other", "startup"]
    assert sorted(path.suffix for path in notices.iterdir()) == [".sent", ".sent"]


def test_the_message_is_a_function_of_the_record_alone() -> None:
    record = alert.Record("a" * 32, "start_limit", "2026-10-15T15:00:00Z")
    assert alert.render(record) == (
        "[sources-alert] schema=1 service=sources class=start_limit episode=" + "a" * 32 + " at=2026-10-15T15:00:00Z\n"
        "systemd stopped restarting the sources MCP server: its restart budget is exhausted. "
        "It stays down until an operator runs reset-failed and start.\n"
    )
    assert all("/" not in summary for summary in alert.SUMMARIES.values())


def test_a_failed_publish_keeps_the_record_for_the_next_run(dirs) -> None:
    state_fd, notices_fd, _state, notices = dirs
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    failing = Publisher(fail=True)
    assert alert.publish_pending(notices_fd, failing) == alert.PublishResult(sent=0, failed=1, pending=1)
    assert len(failing.calls) == 1  # no hot retry inside one run
    assert len(_records(notices)) == 1
    working = Publisher()
    assert alert.publish_pending(notices_fd, working) == alert.PublishResult(sent=1, failed=0, pending=0)
    assert working.calls[0] == failing.calls[0]  # identical bytes and key on retry
    assert _records(notices) == []


def test_the_backlog_is_bounded_and_keeps_the_newest(dirs, monkeypatch: pytest.MonkeyPatch) -> None:
    state_fd, notices_fd, _state, notices = dirs
    monkeypatch.setattr(alert, "MAX_PENDING", 3)
    for minute in range(5):
        alert.record_stopped_run(
            _stopped("watchdog", f"{minute:032x}"),
            state_fd=state_fd,
            notices_fd=notices_fd,
            now=f"2026-10-15T15:0{minute}:00Z",
        )
    assert [record["at"] for record in sorted(_records(notices), key=lambda r: r["at"])] == [
        "2026-10-15T15:02:00Z",
        "2026-10-15T15:03:00Z",
        "2026-10-15T15:04:00Z",
    ]


def test_sent_markers_are_bounded_and_keep_the_newest(dirs, monkeypatch: pytest.MonkeyPatch) -> None:
    state_fd, notices_fd, _state, notices = dirs
    monkeypatch.setattr(alert, "MAX_SENT", 2)
    episodes = []
    for minute in range(4):
        alert.record_stopped_run(
            _stopped("watchdog", f"{minute:032x}"), state_fd=state_fd, notices_fd=notices_fd, now=NOW
        )
        episodes.append(alert.episode_id(f"{minute:032x}", "watchdog"))
        stamp = 1_760_000_000 + 60 * minute  # a marker keeps its record's time
        os.utime(notices / (episodes[-1] + alert.RECORD_SUFFIX), (stamp, stamp))
    assert alert.publish_pending(notices_fd, Publisher()) == alert.PublishResult(sent=4, failed=0, pending=0)
    assert sorted(path.name for path in notices.iterdir()) == sorted(e + alert.SENT_SUFFIX for e in episodes[2:])


# --- review blocker 2: the publication deadline --------------------------------------


class SlowFleet(Publisher):
    """Each publish succeeds after 80 s of an injected clock, inside the publisher's 120 s call timeout."""

    def __init__(self) -> None:
        super().__init__()
        self.now = 0.0

    def clock(self) -> float:
        return self.now

    def __call__(self, message: str, key: str) -> None:
        self.now += 80.0
        super().__call__(message, key)


def test_a_notice_left_at_the_deadline_fails_the_run_and_the_next_run_sends_it(dirs) -> None:
    """The reviewer's case: two watchdog notices, then the budget-exhausted one."""
    state_fd, notices_fd, state, notices = dirs
    for minute, invocation in enumerate(("1" * 32, "2" * 32)):
        _ready(state, invocation)
        alert.record_stopped_run(
            _stopped("watchdog", invocation),
            state_fd=state_fd,
            notices_fd=notices_fd,
            now=f"2026-10-15T15:0{minute}:00Z",
        )
    unit = FakeSystemd("failed", "failed", "start-limit-hit", "2" * 32)
    fleet = SlowFleet()
    args = ["--state-dir", str(state), "notify"]
    assert alert.main(args, publish=fleet, unit_state=unit, clock=fleet.clock) == alert.EXIT_PENDING
    assert (len(fleet.calls), fleet.now) == (2, 160.0)
    assert [record["class"] for record in _records(notices)] == ["start_limit"]
    # The timer's next run sends it, and a later run sends nothing again.
    assert alert.main(args, publish=fleet, unit_state=unit, clock=fleet.clock) == 0
    assert alert.main(args, publish=fleet, unit_state=unit, clock=fleet.clock) == 0
    assert fleet.classes == ["watchdog", "watchdog", "start_limit"]
    assert len({key for _message, key in fleet.calls}) == 3
    assert _records(notices) == []


def test_a_failed_publish_fails_the_run(dirs) -> None:
    state_fd, notices_fd, state, _notices = dirs
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    args = ["--state-dir", str(state), "notify"]
    assert alert.main(args, publish=Publisher(fail=True), unit_state=FakeSystemd()) == alert.EXIT_PENDING
    assert alert.main(args, publish=Publisher(), unit_state=FakeSystemd()) == 0


def test_an_unreadable_unit_state_fails_the_run_but_still_publishes(dirs) -> None:
    state_fd, notices_fd, state, notices = dirs
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)

    def broken() -> dict[str, str]:
        raise AlertError("systemctl show exited 1")

    publish = Publisher()
    assert alert.main(["--state-dir", str(state), "notify"], publish=publish, unit_state=broken) == 1
    assert publish.classes == ["watchdog"]
    assert _records(notices) == []


# --- review blocker 3: merged triggers ------------------------------------------------


def test_a_start_limit_trigger_merged_into_a_running_notify_is_published_once(dirs) -> None:
    """Two failures, one notify run: the second trigger never starts a run of its own."""
    state_fd, notices_fd, state, _notices = dirs
    _ready(state, INVOCATION)
    unit = FakeSystemd("activating", "auto-restart", "watchdog")
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)

    class RefusedRestartDuringPublish(Publisher):
        def __call__(self, message: str, key: str) -> None:
            super().__call__(message, key)
            # The restart delay ends while this run publishes: systemd refuses
            # the start, and its OnFailure= start merges into this run.
            unit.set("failed", "failed", "start-limit-hit")

    fleet = RefusedRestartDuringPublish()
    args = ["--state-dir", str(state), "notify"]
    assert alert.main(args, publish=fleet, unit_state=unit) == 0
    assert fleet.classes == ["watchdog", "start_limit"]  # the same run rescanned and sent it
    assert alert.main(args, publish=fleet, unit_state=unit) == 0  # a timer run: nothing new
    assert fleet.classes == ["watchdog", "start_limit"]
    assert len({key for _message, key in fleet.calls}) == 2


def test_a_start_limit_reached_after_the_last_scan_is_sent_by_the_timer_run(dirs) -> None:
    """The worst case: the trigger merges into a run that has already scanned for the last time."""
    state_fd, notices_fd, state, _notices = dirs
    _ready(state, INVOCATION)
    unit = FakeSystemd("activating", "auto-restart", "watchdog")
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    fleet = Publisher()
    args = ["--state-dir", str(state), "notify"]
    assert alert.main(args, publish=fleet, unit_state=unit) == 0
    unit.set("failed", "failed", "start-limit-hit")  # no run of its own: merged away
    assert fleet.classes == ["watchdog"]
    for _timer_run in range(3):  # the unit stays failed until an operator resets it
        assert alert.main(args, publish=fleet, unit_state=unit) == 0
    assert fleet.classes == ["watchdog", "start_limit"]
    assert len({key for _message, key in fleet.calls}) == 2
    # After reset-failed and a start, a new run's failures are new episodes.
    unit.set("failed", "failed", "start-limit-hit", OTHER_INVOCATION)
    assert alert.main(args, publish=fleet, unit_state=unit) == 0
    assert fleet.classes == ["watchdog", "start_limit", "start_limit"]


# --- reading systemd -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("choice", "environ", "expected"),
    [
        ("auto", {"MANAGERPID": "1234"}, "user"),
        ("auto", {}, "system"),
        ("user", {}, "user"),
        ("system", {"MANAGERPID": "1234"}, "system"),
    ],
)
def test_the_manager_is_the_one_running_the_notifier(choice: str, environ: dict[str, str], expected: str) -> None:
    assert alert._manager(choice, environ) == expected


def test_systemctl_show_is_read_from_the_chosen_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[list[str]] = []

    def run(command, **kwargs):
        seen.append(command)
        assert kwargs["timeout"] == alert.SYSTEMCTL_TIMEOUT_S
        stdout = "ActiveState=failed\nSubState=failed\nResult=start-limit-hit\nInvocationID=" + INVOCATION + "\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(alert.subprocess, "run", run)
    assert alert.systemctl_unit_state("user")() == {
        "ActiveState": "failed",
        "SubState": "failed",
        "Result": "start-limit-hit",
        "InvocationID": INVOCATION,
    }
    alert.systemctl_unit_state("system")()
    assert seen[0][:4] == ["systemctl", "--user", "show", alert.UNIT]
    assert seen[1][:3] == ["systemctl", "show", alert.UNIT]
    monkeypatch.setattr(
        alert.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 1, "", "denied")
    )
    with pytest.raises(AlertError, match="exited 1"):
        alert.systemctl_unit_state("user")()


# --- the real Fleet Comms idempotency facility ---------------------------------------


@pytest.fixture
def fleet_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from scripts.fleet_comms.authority import AuthorityService

    root = tmp_path / "plane"
    root.mkdir()
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(root))
    monkeypatch.setenv("AB_DB_PATH", str(tmp_path / "unused-legacy.db"))
    with AuthorityService(root=root) as service:
        service.create_channel("cto", subscribers=("claude",))
    return root


def _stored(root: Path) -> list[str]:
    from scripts.fleet_comms.authority import AuthorityService

    with contextlib.closing(sqlite3.connect(f"file:{root / 'comms.sqlite3'}?mode=ro", uri=True)) as conn:
        ids = [row[0] for row in conn.execute("SELECT message_id FROM comms_messages WHERE sender = 'sre-timers'")]
    with AuthorityService(root=root) as service:
        return [service.read_message_body(message_id) for message_id in ids]


def test_a_publish_interrupted_after_fleet_comms_stored_it_is_not_sent_twice(dirs, fleet_root: Path) -> None:
    state_fd, notices_fd, _state, notices = dirs
    alert.record_stopped_run(_stopped("watchdog"), state_fd=state_fd, notices_fd=notices_fd, now=NOW)
    real = fleet_comms_publisher(ROOT)

    def killed_after_publish(message: str, key: str) -> None:
        real(message, key)
        raise KeyboardInterrupt  # the publisher dies before it marks the record sent

    with pytest.raises(KeyboardInterrupt):
        alert.publish_pending(notices_fd, killed_after_publish)
    assert len(_records(notices)) == 1
    assert alert.publish_pending(notices_fd, real) == alert.PublishResult(sent=1, failed=0, pending=0)
    assert _records(notices) == []
    [body] = _stored(fleet_root)
    assert MESSAGE.fullmatch(body)
    assert "class=watchdog" in body


def test_a_retry_after_the_channel_changed_is_still_one_message(dirs, fleet_root: Path) -> None:
    """New subscribers change the stored payload; the episode key still marks it sent."""
    from scripts.fleet_comms.authority import AuthorityService

    state_fd, notices_fd, _state, notices = dirs
    alert.record_unit_state(
        FakeSystemd("failed", "failed", "start-limit-hit"), state_fd=state_fd, notices_fd=notices_fd, now=NOW
    )
    real = fleet_comms_publisher(ROOT)

    def killed_after_publish(message: str, key: str) -> None:
        real(message, key)
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        alert.publish_pending(notices_fd, killed_after_publish)
    with AuthorityService(root=fleet_root) as service:
        service.subscribe("cto", ("codex",))
    assert alert.publish_pending(notices_fd, real) == alert.PublishResult(sent=1, failed=0, pending=0)
    assert _records(notices) == []
    assert len(_stored(fleet_root)) == 1


# --- the command line ----------------------------------------------------------------


def test_the_stop_path_recorder_is_quick(tmp_path: Path) -> None:
    """``record`` runs in the server's stop path, before systemd can restart it."""
    unit = (ROOT / "packaging" / "systemd" / "learn-ukrainian-sources.service").read_text(encoding="utf-8")
    restart_sec = float(re.search(r"^RestartSec=(\d+)$", unit, re.MULTILINE).group(1))  # type: ignore[union-attr]
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    env = {**os.environ, **_stopped("watchdog"), "STATE_DIRECTORY": str(state)}
    began = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "scripts.orchestration.sources_failure_alert", "record"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    elapsed = time.monotonic() - began
    assert result.returncode == 0, result.stderr
    assert len(list((state / alert.NOTICES_DIR).glob("*.json"))) == 1
    assert elapsed < restart_sec / 2, f"recorder took {elapsed:.2f}s"


def test_cli_exit_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state = tmp_path / "state"
    state.mkdir(mode=0o700)
    for key, value in _stopped("watchdog").items():
        monkeypatch.setenv(key, value)
    assert alert.main(["--state-dir", str(state), "record"]) == 0
    notify = ["--state-dir", str(state), "notify"]
    assert alert.main(notify, publish=Publisher(fail=True), unit_state=FakeSystemd()) == alert.EXIT_PENDING
    assert alert.main(notify, publish=Publisher(), unit_state=FakeSystemd()) == 0
    monkeypatch.delenv("STATE_DIRECTORY", raising=False)
    assert alert.main(["notify"], publish=Publisher(), unit_state=FakeSystemd()) == 1  # no state directory
    (state / alert.NOTICES_DIR).chmod(0o750)
    assert alert.main(notify, publish=Publisher(), unit_state=FakeSystemd()) == 1  # not owner-only
