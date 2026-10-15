"""Native systemd supervision of the sources server, read from the shipped units (#10674)."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.rag.call_governor import GovernorLimits

ROOT = Path(__file__).resolve().parents[2]
PACKAGING = ROOT / "packaging" / "systemd"
SOURCES = "learn-ukrainian-sources.service"
RECORDER = "learn-ukrainian-sources-alert@.service"
PUBLISHER = "learn-ukrainian-sources-alert-publish.service"
# The template's restrictions before #10674; supervision must keep every one.
HARDENING = {
    "UMask": "0077",
    "NoNewPrivileges": "yes",
    "PrivateMounts": "yes",
    "PrivateTmp": "yes",
    "ProtectSystem": "strict",
    "ProtectHome": "yes",
    "ProtectProc": "invisible",
    "ProcSubset": "pid",
    "SystemCallFilter": "~@debug",
    "RestrictSUIDSGID": "yes",
    "LockPersonality": "yes",
    "CapabilityBoundingSet": "",
}
_SPAN = re.compile(r"^(\d+)(s|sec|min|h)?$")


def parse_unit(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Sections of a unit file as ordered (key, value) lists; keys may repeat."""
    sections: dict[str, list[tuple[str, str]]] = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
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
    # Only the state directory is writable; nothing re-opens the checkout.
    assert values(unit, "Service", "ReadWritePaths") == []
    assert values(unit, "Service", "BindPaths") == []
    # Publishing never runs in the restart path.
    assert values(unit, "Service", "ExecStopPost") == []
    assert values(unit, "Service", "ExecStartPost") == []


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


def test_failures_go_to_a_quick_local_recorder_then_a_separate_publisher() -> None:
    sources = parse_unit(PACKAGING / SOURCES)
    assert one(sources, "Unit", "OnFailure") == "learn-ukrainian-sources-alert@%n.service"
    recorder = parse_unit(PACKAGING / RECORDER)
    assert one(recorder, "Unit", "OnSuccess") == PUBLISHER
    assert one(recorder, "Service", "Type") == "oneshot"
    assert one(recorder, "Service", "ExecStart").endswith(
        "-m scripts.orchestration.sources_failure_alert record %i --sources-state-dir %S/learn-ukrainian-sources"
    )
    publisher = parse_unit(PACKAGING / PUBLISHER)
    assert one(publisher, "Service", "ExecStart").endswith("-m scripts.orchestration.sources_failure_alert publish")
    assert one(publisher, "Service", "Restart") == "on-failure"
    assert int(one(publisher, "Unit", "StartLimitBurst")) > 0
    for unit in (recorder, publisher):
        assert 0 < seconds(one(unit, "Service", "TimeoutStartSec")) <= 300
        assert one(unit, "Service", "StateDirectory") == "learn-ukrainian-sources-alerts"
        assert one(unit, "Service", "StateDirectoryMode") == "0700"
        assert one(unit, "Service", "UMask") == "0077"


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
