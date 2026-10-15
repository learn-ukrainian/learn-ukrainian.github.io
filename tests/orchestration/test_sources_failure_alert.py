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
UNIT = alert.UNIT
INVOCATION = "0123456789abcdef0123456789abcdef"
OTHER_INVOCATION = "fedcba9876543210fedcba9876543210"
MESSAGE = re.compile(
    r"\[sources-alert\] schema=1 service=sources class=(watchdog|start_limit|startup|other) "
    r"episode=[0-9a-f]{32} at=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\n[^\n/]+\n"
)


class Recorder:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.fail = fail

    def __call__(self, message: str, key: str) -> None:
        self.calls.append((message, key))
        if self.fail:
            raise AlertError("fleet_comms publish exited 1: /home/op/private/plane.sqlite3 locked")


@pytest.fixture
def dirs(tmp_path: Path) -> Iterator[tuple[int, int, Path, Path]]:
    alerts, sources = tmp_path / "alerts", tmp_path / "sources"
    alerts.mkdir(mode=0o700)
    sources.mkdir(mode=0o700)
    alerts_fd, sources_fd = open_state_dir(str(alerts)), open_state_dir(str(sources))
    try:
        yield alerts_fd, sources_fd, alerts, sources
    finally:
        os.close(alerts_fd)
        os.close(sources_fd)


def _monitor(result: str, invocation: str = INVOCATION, **extra: str) -> dict[str, str]:
    return {
        "MONITOR_UNIT": UNIT,
        "MONITOR_SERVICE_RESULT": result,
        "MONITOR_INVOCATION_ID": invocation,
        **extra,
    }


def _records(alerts: Path) -> list[dict[str, object]]:
    return [json.loads(path.read_text()) for path in sorted(alerts.glob("*.json"))]


def _ready(sources: Path, invocation: str) -> None:
    (sources / READY_MARKER).write_text(invocation + "\n")


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
    alerts_fd, sources_fd, alerts, sources = dirs
    _ready(sources, INVOCATION)
    note = alert.record_failure(
        _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    assert note.startswith("watchdog episode ") and note.endswith(" recorded")
    [record] = _records(alerts)
    assert set(record) == {"schema", "service", "episode", "class", "at"}
    assert record["class"] == "watchdog" and record["service"] == "sources" and record["schema"] == 1
    assert record["episode"] == alert.episode_id(INVOCATION, "watchdog")
    assert INVOCATION not in json.dumps(record)  # the episode id is opaque
    [path] = alerts.glob("*.json")
    assert oct(path.stat().st_mode & 0o777) == "0o600"


def test_start_up_and_later_failures_are_told_apart_by_the_ready_marker(dirs) -> None:
    alerts_fd, sources_fd, alerts, sources = dirs
    _ready(sources, OTHER_INVOCATION)  # an earlier run reached readiness, this one did not
    alert.record_failure(
        _monitor("exit-code"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    _ready(sources, INVOCATION)
    alert.record_failure(
        _monitor("exit-code", OTHER_INVOCATION),
        UNIT,
        alerts_fd=alerts_fd,
        sources_fd=sources_fd,
        now="2026-10-15T15:01:00Z",
    )
    alert.record_failure(
        _monitor("exit-code", "f" * 32), UNIT, alerts_fd=alerts_fd, sources_fd=None, now="2026-10-15T15:02:00Z"
    )
    assert [record["class"] for record in sorted(_records(alerts), key=lambda r: r["at"])] == [
        "startup",
        "startup",
        "other",
    ]


def test_the_start_limit_is_its_own_episode_after_the_last_failure(dirs) -> None:
    alerts_fd, sources_fd, alerts, sources = dirs
    _ready(sources, INVOCATION)
    alert.record_failure(
        _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    # systemd refuses the restart: no new invocation, the previous id is passed on.
    alert.record_failure(
        _monitor("start-limit-hit"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:05Z"
    )
    records = _records(alerts)
    assert sorted(record["class"] for record in records) == ["start_limit", "watchdog"]
    assert len({record["episode"] for record in records}) == 2


def test_recording_the_same_failure_twice_keeps_one_record_and_its_first_time(dirs) -> None:
    alerts_fd, sources_fd, alerts, _sources = dirs
    environ = _monitor("watchdog")
    alert.record_failure(environ, UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z")
    note = alert.record_failure(environ, UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T16:00:00Z")
    assert note.endswith("already recorded")
    assert [record["at"] for record in _records(alerts)] == ["2026-10-15T15:00:00Z"]


def test_an_interrupted_record_write_leaves_nothing_half_written(dirs, monkeypatch: pytest.MonkeyPatch) -> None:
    alerts_fd, sources_fd, alerts, _sources = dirs
    real_link = os.link

    def interrupted(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(alert.os, "link", interrupted)
    with pytest.raises(KeyboardInterrupt):
        alert.record_failure(
            _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
        )
    assert list(alerts.iterdir()) == []
    # A killed writer can leave its temporary file: it is never a record.
    (alerts / f".{'a' * 32}-0000.tmp").write_text('{"partial": ')
    monkeypatch.setattr(alert.os, "link", real_link)
    alert.record_failure(
        _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:01Z"
    )
    publish = Recorder()
    assert alert.publish_pending(alerts_fd, publish) == (1, 0)
    assert len(publish.calls) == 1


def test_only_sources_failures_are_recorded(dirs) -> None:
    alerts_fd, sources_fd, alerts, _sources = dirs
    for unit, environ in (
        ("learn-ukrainian-api.service", _monitor("watchdog")),
        (UNIT, {**_monitor("watchdog"), "MONITOR_UNIT": "learn-ukrainian-api.service"}),
        (UNIT, {key: value for key, value in _monitor("watchdog").items() if key != "MONITOR_UNIT"}),
    ):
        with pytest.raises(AlertError):
            alert.record_failure(environ, unit, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z")
    assert alert.record_failure(_monitor("success"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="x") == (
        "no failure to record"
    )
    assert list(alerts.iterdir()) == []


def test_injected_paths_and_errors_never_reach_the_message(dirs) -> None:
    """Only the allowlisted fields leave the host, whatever systemd or old state carries."""
    alerts_fd, sources_fd, alerts, sources = dirs
    _ready(sources, INVOCATION)
    secrets_seen = (
        "/home/op/learn-ukrainian/batch_state/sources-dumps/x.txt",
        "Traceback (most recent call last)",
        "sqlite3.OperationalError: database is locked",
        '{"status": "ok"',
    )
    environ = _monitor(
        "exit-code",
        MONITOR_EXIT_CODE="exited " + secrets_seen[0],
        MONITOR_EXIT_STATUS="1\n" + secrets_seen[1] + "\n" + secrets_seen[2],
        MONITOR_HEALTH_BODY=secrets_seen[3],
    )
    alert.record_failure(environ, UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z")
    alert.record_failure(
        _monitor(f"watchdog {secrets_seen[0]}", OTHER_INVOCATION),
        UNIT,
        alerts_fd=alerts_fd,
        sources_fd=sources_fd,
        now="2026-10-15T15:00:01Z",
    )
    # A pending notice queued by the old watchdog, and tampered records.
    (alerts / "old-incident.json").write_text(json.dumps({"message": f"hung; dump at {secrets_seen[0]}"}))
    good = alert.Record("b" * 32, "watchdog", "2026-10-15T14:00:00Z")
    (alerts / good.name).write_text(json.dumps({**json.loads(good.as_json()), "detail": secrets_seen[1]}))
    bad_time = alert.Record("c" * 32, "other", "2026-10-15T14:00:00Z")
    (alerts / bad_time.name).write_text(bad_time.as_json().replace("2026-10-15T14:00:00Z", secrets_seen[0]))
    misnamed = alert.Record("d" * 32, "other", "2026-10-15T14:00:00Z")
    (alerts / ("e" * 32 + ".json")).write_text(misnamed.as_json())
    publish = Recorder()
    assert alert.publish_pending(alerts_fd, publish) == (2, 0)
    assert len(publish.calls) == 2
    for message, key in publish.calls:
        assert MESSAGE.fullmatch(message), message
        assert re.fullmatch(r"lu-sources-alert:v1:[0-9a-f]{32}", key)
        for secret in secrets_seen:
            assert secret not in message
    assert [message.split()[3] for message, _key in publish.calls] == ["class=other", "class=startup"]
    assert list(alerts.iterdir()) == []


def test_the_message_is_a_function_of_the_record_alone() -> None:
    record = alert.Record("a" * 32, "start_limit", "2026-10-15T15:00:00Z")
    assert alert.render(record) == (
        "[sources-alert] schema=1 service=sources class=start_limit episode=" + "a" * 32 + " at=2026-10-15T15:00:00Z\n"
        "systemd stopped restarting the sources MCP server: its restart budget is exhausted. "
        "It stays down until an operator runs reset-failed and start.\n"
    )
    assert all("/" not in summary for summary in alert.SUMMARIES.values())


def test_a_failed_publish_keeps_the_record_for_the_next_run(dirs, capsys) -> None:
    alerts_fd, sources_fd, alerts, _sources = dirs
    alert.record_failure(
        _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    failing = Recorder(fail=True)
    assert alert.publish_pending(alerts_fd, failing) == (0, 1)
    assert len(failing.calls) == 1  # no hot retry inside one run
    assert len(_records(alerts)) == 1
    working = Recorder()
    assert alert.publish_pending(alerts_fd, working) == (1, 0)
    assert working.calls[0] == failing.calls[0]  # identical bytes and key on retry
    assert _records(alerts) == []


def test_the_backlog_is_bounded_and_keeps_the_newest(dirs, monkeypatch: pytest.MonkeyPatch) -> None:
    alerts_fd, sources_fd, alerts, _sources = dirs
    monkeypatch.setattr(alert, "MAX_PENDING", 3)
    for minute in range(5):
        alert.record_failure(
            _monitor("watchdog", f"{minute:032x}"),
            UNIT,
            alerts_fd=alerts_fd,
            sources_fd=sources_fd,
            now=f"2026-10-15T15:0{minute}:00Z",
        )
    assert [record["at"] for record in sorted(_records(alerts), key=lambda r: r["at"])] == [
        "2026-10-15T15:02:00Z",
        "2026-10-15T15:03:00Z",
        "2026-10-15T15:04:00Z",
    ]


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
    alerts_fd, sources_fd, alerts, _sources = dirs
    alert.record_failure(
        _monitor("watchdog"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    real = fleet_comms_publisher(ROOT)

    def killed_after_publish(message: str, key: str) -> None:
        real(message, key)
        raise KeyboardInterrupt  # the publisher dies before it deletes the record

    with pytest.raises(KeyboardInterrupt):
        alert.publish_pending(alerts_fd, killed_after_publish)
    assert len(_records(alerts)) == 1
    assert alert.publish_pending(alerts_fd, real) == (1, 0)
    assert _records(alerts) == []
    [body] = _stored(fleet_root)
    assert MESSAGE.fullmatch(body)
    assert "class=watchdog" in body


def test_a_retry_after_the_channel_changed_is_still_one_message(dirs, fleet_root: Path) -> None:
    """New subscribers change the stored payload; the episode key still marks it sent."""
    from scripts.fleet_comms.authority import AuthorityService

    alerts_fd, sources_fd, alerts, _sources = dirs
    alert.record_failure(
        _monitor("start-limit-hit"), UNIT, alerts_fd=alerts_fd, sources_fd=sources_fd, now="2026-10-15T15:00:00Z"
    )
    real = fleet_comms_publisher(ROOT)

    def killed_after_publish(message: str, key: str) -> None:
        real(message, key)
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        alert.publish_pending(alerts_fd, killed_after_publish)
    with AuthorityService(root=fleet_root) as service:
        service.subscribe("cto", ("codex",))
    assert alert.publish_pending(alerts_fd, real) == (1, 0)
    assert _records(alerts) == []
    assert len(_stored(fleet_root)) == 1


def test_the_recorder_finishes_well_inside_the_restart_delay(tmp_path: Path) -> None:
    """The recorder is done before the next failure can trigger it again.

    systemd merges a second OnFailure= start into a still-running one; the
    next trigger comes at least RestartSec after the failure that started
    this one.
    """
    unit = (ROOT / "packaging" / "systemd" / "learn-ukrainian-sources.service").read_text(encoding="utf-8")
    restart_sec = float(re.search(r"^RestartSec=(\d+)$", unit, re.MULTILINE).group(1))  # type: ignore[union-attr]
    alerts, sources = tmp_path / "alerts", tmp_path / "sources"
    alerts.mkdir(mode=0o700)
    sources.mkdir(mode=0o700)
    env = {**os.environ, **_monitor("watchdog"), "STATE_DIRECTORY": str(alerts)}
    began = time.monotonic()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.orchestration.sources_failure_alert",
            "record",
            UNIT,
            "--sources-state-dir",
            str(sources),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    elapsed = time.monotonic() - began
    assert result.returncode == 0, result.stderr
    assert len(list(alerts.glob("*.json"))) == 1
    assert elapsed < restart_sec / 2, f"recorder took {elapsed:.2f}s"


def test_cli_publish_exits_non_zero_while_a_record_is_unsent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    alerts, sources = tmp_path / "alerts", tmp_path / "sources"
    alerts.mkdir(mode=0o700)
    sources.mkdir(mode=0o700)
    for key, value in _monitor("watchdog").items():
        monkeypatch.setenv(key, value)
    assert alert.main(["--state-dir", str(alerts), "record", UNIT, "--sources-state-dir", str(sources)]) == 0
    assert alert.main(["--state-dir", str(alerts), "publish"], publish=Recorder(fail=True)) == 1
    assert alert.main(["--state-dir", str(alerts), "publish"], publish=Recorder()) == 0
    assert alert.main(["publish"], publish=Recorder()) == 1  # no state directory
