"""Native systemd supervision of the sources server, read from the shipped units (#10674)."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.orchestration import sources_failure_alert as alert
from scripts.rag import sources_supervision as sup
from scripts.rag.call_governor import GovernorLimits

ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging" / "systemd"
SOURCES = "learn-ukrainian-sources.service"
NOTIFIER = "learn-ukrainian-sources-alert.service"
TIMER = "learn-ukrainian-sources-alert.timer"
# The template's restrictions before #10674; supervision keeps every one,
# except that the home trees are hidden behind tmpfs with narrow binds back.
HARDENING = {
    "UMask": "0077",
    "NoNewPrivileges": "yes",
    "PrivateMounts": "yes",
    "PrivateTmp": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "tmpfs",
    "ProtectProc": "invisible",
    "ProcSubset": "pid",
    "SystemCallFilter": "~@debug",
    "RestrictSUIDSGID": "yes",
    "LockPersonality": "yes",
    "CapabilityBoundingSet": "",
}
_SPAN = re.compile(r"^(\d+)(s|sec|min|h)?$")


def parse_unit(path: Path, text: str | None = None) -> dict[str, list[tuple[str, str]]]:
    """Sections of a unit file as ordered (key, value) lists; keys may repeat."""
    sections: dict[str, list[tuple[str, str]]] = {}
    current = None
    for raw in (path.read_text(encoding="utf-8") if text is None else text).splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = sections.setdefault(line[1:-1], [])
            continue
        assert current is not None, f"{path.name}: setting outside a section: {line}"
        key, _, value = line.partition("=")
        current.append((key.strip(), value.strip()))
    return sections


def values(unit: dict[str, list[tuple[str, str]]], section: str, key: str) -> list[str]:
    return [value for name, value in unit.get(section, []) if name == key]


def one(unit: dict[str, list[tuple[str, str]]], section: str, key: str) -> str:
    found = values(unit, section, key)
    assert len(found) == 1, f"[{section}] {key}= set {len(found)} times: {found}"
    return found[0]


def seconds(span: str) -> float:
    match = _SPAN.fullmatch(span)
    assert match, f"not a finite time span: {span!r}"
    return int(match.group(1)) * {None: 1, "s": 1, "sec": 1, "min": 60, "h": 3600}[match.group(2)]


def test_sources_unit_is_a_notify_service_with_a_watchdog() -> None:
    unit = parse_unit(PACKAGING / SOURCES)
    assert one(unit, "Service", "Type") == "notify"
    assert one(unit, "Service", "NotifyAccess") == "main"
    watchdog = seconds(one(unit, "Service", "WatchdogSec"))
    # A probe may wait the governor's whole queue timeout for a slot and must
    # still meet its deadline of half the watchdog interval.
    assert watchdog / 2 > GovernorLimits().queue_timeout
    # SIGABRT (the default) is what faulthandler dumps on.
    assert values(unit, "Service", "WatchdogSignal") in ([], ["SIGABRT"])
    assert one(unit, "Service", "Restart") == "on-failure"
    assert one(unit, "Service", "ExecStart").endswith(
        ".mcp/servers/sources/server.py --standalone --host 127.0.0.1 --port 8766"
    )


def test_sources_unit_dumps_then_kills_with_finite_deadlines_and_no_core() -> None:
    unit = parse_unit(PACKAGING / SOURCES)
    for key in ("TimeoutAbortSec", "TimeoutStopSec", "TimeoutStartSec"):
        assert 0 < seconds(one(unit, "Service", key)) <= 300, key
    assert one(unit, "Service", "SendSIGKILL") == "yes"
    assert one(unit, "Service", "KillMode") == "control-group"
    assert one(unit, "Service", "LimitCORE") == "0"
    assert one(unit, "Service", "StateDirectory") == "learn-ukrainian-sources"
    assert one(unit, "Service", "StateDirectoryMode") == "0700"


def test_sources_unit_keeps_every_earlier_restriction() -> None:
    unit = parse_unit(PACKAGING / SOURCES)
    for key, value in HARDENING.items():
        assert one(unit, "Service", key) == value, key
    assert values(unit, "Service", "Environment")[:2] == [
        "HRAMATKA_V4_EXECUTION_ENABLED=0",
        "HRAMATKA_V4_ADMISSION_ENABLED=0",
    ]
    assert values(unit, "Service", "BindReadOnlyPaths") == ["@REPO_ROOT@", "@VENV_ROOT@", "@PYTHON_ROOT@"]
    assert values(unit, "Service", "BindPaths") == ["@DATA_ROOT@"]
    # Only a local recorder runs in the stop path; publishing never does.
    assert values(unit, "Service", "ExecStopPost") == [
        "-@REPO_ROOT@/.venv/bin/python -m scripts.orchestration.sources_failure_alert record"
    ]
    assert values(unit, "Service", "ExecStartPost") == []


# Settings that grant a unit a writable or extra path (systemd.exec(5)).
WRITABLE_PATH_SETTINGS = (
    "ReadWritePaths",
    "BindPaths",
    "TemporaryFileSystem",
    "StateDirectory",
    "RuntimeDirectory",
    "CacheDirectory",
    "LogsDirectory",
    "ConfigurationDirectory",
)


def test_the_rendered_unit_binds_back_exactly_the_narrow_paths(tmp_path: Path) -> None:
    """Read-only: checkout, virtual environment, interpreter installation; writable: data and state only."""
    home = tmp_path / "home" / "op"
    paths = sup.UnitPaths(
        repo_root=home / "repo",
        venv_root=home / "repo" / ".venv",
        python_root=home / ".local" / "python" / "cpython-3.12",
        data_root=home / "repo" / "data",
    )
    template = (PACKAGING / SOURCES).read_text(encoding="utf-8")
    unit = parse_unit(PACKAGING / SOURCES, sup.render_unit(template, paths))
    assert one(unit, "Service", "ProtectHome") == "tmpfs"
    assert one(unit, "Service", "ProtectSystem") == "strict"
    assert values(unit, "Service", "BindReadOnlyPaths") == [
        str(paths.repo_root),
        str(paths.venv_root),
        str(paths.python_root),
    ]
    granted = {key: values(unit, "Service", key) for key in WRITABLE_PATH_SETTINGS if values(unit, "Service", key)}
    assert granted == {"BindPaths": [str(paths.data_root)], "StateDirectory": ["learn-ukrainian-sources"]}
    for key in ("InaccessiblePaths", "ReadOnlyPaths", "RootDirectory", "PrivateUsers", "DynamicUser"):
        assert values(unit, "Service", key) == [], key
    assert "LU_MCP_SOURCES_LOG_DIR=%S/learn-ukrainian-sources" in values(unit, "Service", "Environment")
    # The data-volume drop-in replaces only the start command.
    dropin = parse_unit(PACKAGING / "dropins" / f"{SOURCES}.d" / "data-volume.conf")
    assert {key for key, _value in dropin["Service"]} == {"ExecStart", "RestartPreventExitStatus"}


def test_the_start_limit_catches_repeated_watchdog_cycles() -> None:
    unit = parse_unit(PACKAGING / SOURCES)
    assert values(unit, "Service", "StartLimitIntervalSec") == []  # only [Unit] counts
    interval = seconds(one(unit, "Unit", "StartLimitIntervalSec"))
    burst = int(one(unit, "Unit", "StartLimitBurst"))
    assert one(unit, "Unit", "StartLimitAction") == "none"
    # The shortest watchdog cycle: missed pings for WatchdogSec, then the
    # restart delay. A server that hangs right after every start must spend
    # its whole budget inside one interval.
    cycle = seconds(one(unit, "Service", "WatchdogSec")) + seconds(one(unit, "Service", "RestartSec"))
    assert burst * cycle < interval
    assert burst >= 3


def test_no_notice_depends_on_a_trigger_surviving() -> None:
    """Each run is recorded in its own stop path; the notifier is started by failures and a timer."""
    sources = parse_unit(PACKAGING / SOURCES)
    assert one(sources, "Unit", "OnFailure") == NOTIFIER
    [record] = values(sources, "Service", "ExecStopPost")
    assert record.startswith("-") and record.endswith("-m scripts.orchestration.sources_failure_alert record")
    notifier = parse_unit(PACKAGING / NOTIFIER)
    assert one(notifier, "Service", "Type") == "oneshot"
    assert one(notifier, "Service", "ExecStart").endswith("-m scripts.orchestration.sources_failure_alert notify")
    # The timer is the retry: no restart loop, and no start limit that could refuse it.
    assert values(notifier, "Service", "Restart") == []
    assert one(notifier, "Unit", "StartLimitIntervalSec") == "0"
    # A run never outlives its unit: the budget, then one started publish call.
    assert seconds(one(notifier, "Service", "TimeoutStartSec")) >= alert.PUBLISH_BUDGET_S + 120 + 10
    assert one(notifier, "Service", "StateDirectory") == one(sources, "Service", "StateDirectory")
    assert one(notifier, "Service", "StateDirectoryMode") == "0700"
    assert one(notifier, "Service", "UMask") == "0077"
    timer = parse_unit(PACKAGING / TIMER)
    assert one(timer, "Timer", "Unit") == NOTIFIER
    assert one(timer, "Timer", "OnCalendar") == "*:0/5"
    assert one(timer, "Install", "WantedBy") == "timers.target"
    guarded = values(parse_unit(PACKAGING / "dropins" / f"{NOTIFIER}.d" / "data-volume.conf"), "Service", "ExecStart")
    assert guarded[0] == "" and guarded[1].endswith(one(notifier, "Service", "ExecStart"))
    # The earlier recorder/publisher pair, which depended on its triggers, is gone.
    assert not (PACKAGING / "learn-ukrainian-sources-alert@.service").exists()
    assert not (PACKAGING / "learn-ukrainian-sources-alert-publish.service").exists()


def test_the_volume_guard_keeps_the_server_as_the_notifying_main_process() -> None:
    """NotifyAccess=main: the guard must exec into the server, keeping its PID."""
    dropin = parse_unit(PACKAGING / "dropins" / f"{SOURCES}.d" / "data-volume.conf")
    assert values(dropin, "Service", "ExecStart")[0] == ""
    guarded = values(dropin, "Service", "ExecStart")[1]
    assert guarded.startswith("/usr/bin/env bash @REPO_ROOT@/scripts/storage/data_volume_guard.sh -- ")
    assert guarded.endswith(one(parse_unit(PACKAGING / SOURCES), "Service", "ExecStart"))
    assert one(dropin, "Service", "RestartPreventExitStatus") == "78"
    guard = (ROOT / "scripts" / "storage" / "data_volume_guard.sh").read_text(encoding="utf-8")
    assert guard.count('exec "$@"') == 2  # root-disk and verified-volume paths both exec


def test_no_second_supervisor_unit_is_shipped() -> None:
    """The parked custom watchdog's units must never ship beside native supervision."""
    shipped = [path.name for path in PACKAGING.rglob("*") if "sources-watchdog" in path.name]
    assert shipped == []
