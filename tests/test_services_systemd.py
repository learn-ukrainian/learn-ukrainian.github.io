"""Hermetic systemd routing tests for services.sh; no host unit is contacted."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def harness(tmp_path: Path):
    script = tmp_path / "services.sh"
    script.write_bytes((ROOT / "services.sh").read_bytes())
    script.chmod(0o755)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    ps = bin_dir / "ps"
    ps.write_text(f'#!/bin/sh\nexec "{shutil.which("ps")}" "$@"\n')
    ps.chmod(0o755)
    systemctl = bin_dir / "systemctl"
    systemctl.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$FAKE_CALLS\"\n"
        "printf 'bus=%s runtime=%s\\n' \"$DBUS_SESSION_BUS_ADDRESS\" \"$XDG_RUNTIME_DIR\" >> \"$FAKE_CALLS\"\n"
        "case \"$2\" in\n"
        "show)\n"
        "  [ \"$FAKE_LOAD\" = unreachable ] && exit 1\n"
        "  if [ \"$4\" = LoadState ]; then echo \"$FAKE_LOAD\"; exit 0; fi\n"
        "  case \"$4\" in\n"
        "    MainPID) cat \"$FAKE_MAIN\" ;;\n"
        "    ActiveState) cat \"$FAKE_ACTIVE\" ;;\n"
        "    SubState) echo running ;;\n"
        "    NRestarts) echo 7 ;;\n"
        "  esac ;;\n"
        "stop)\n"
        "  old=$(cat \"$FAKE_MAIN\")\n"
        "  [ \"$(cat \"$FAKE_LISTENERS\")\" = \"$old\" ] && : > \"$FAKE_LISTENERS\"\n"
        "  echo 0 > \"$FAKE_MAIN\"; echo inactive > \"$FAKE_ACTIVE\" ;;\n"
        "start)\n"
        "  echo \"$FAKE_UNIT_PID\" > \"$FAKE_MAIN\"\n"
        "  echo \"$FAKE_UNIT_PID\" > \"$FAKE_LISTENERS\"\n"
        "  echo active > \"$FAKE_ACTIVE\" ;;\n"
        "esac\n"
    )
    systemctl.chmod(0o755)
    lsof = bin_dir / "lsof"
    lsof.write_text(
        "#!/bin/sh\n"
        "while read -r pid; do\n"
        "  [ -n \"$pid\" ] || continue\n"
        "  stat=$(ps -p \"$pid\" -o stat= 2>/dev/null)\n"
        "  case \"$stat\" in ''|Z*) ;; *) echo \"$pid\" ;; esac\n"
        "done < \"$FAKE_LISTENERS\"\n"
    )
    lsof.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text("#!/bin/sh\n[ \"${FAKE_HEALTH:-1}\" = 1 ]\n")
    curl.chmod(0o755)
    supervisor = bin_dir / "supervisor"
    supervisor.write_text("#!/bin/sh\necho \"$*\" >> \"$FAKE_CALLS\"\n")
    supervisor.chmod(0o755)
    journalctl = bin_dir / "journalctl"
    journalctl.write_text("#!/bin/sh\necho \"journal:$*\"\n")
    journalctl.chmod(0o755)
    files = {key: tmp_path / key for key in ("calls", "main", "active", "listeners")}
    files["calls"].write_text("")
    files["main"].write_text("0\n")
    files["active"].write_text("inactive\n")
    files["listeners"].write_text("")
    env = os.environ.copy()
    env.update(
        LU_SERVICES_ROLE="local",
        SVC_SYSTEMCTL_BIN=str(systemctl),
        SVC_LSOF_BIN=str(lsof),
        SVC_JOURNALCTL_BIN=str(journalctl),
        SVC_API_SUPERVISOR_BIN=str(supervisor),
        FAKE_CALLS=str(files["calls"]),
        FAKE_MAIN=str(files["main"]),
        FAKE_ACTIVE=str(files["active"]),
        FAKE_LISTENERS=str(files["listeners"]),
        FAKE_LOAD="loaded",
        PATH=f"{bin_dir}:{env['PATH']}",
        XDG_CONFIG_HOME=str(tmp_path / "config"),
    )
    env.pop("LU_SERVICES_SSH_HOST", None)
    processes: list[subprocess.Popen[bytes]] = []

    def process(argv0: str) -> subprocess.Popen[bytes]:
        child = subprocess.Popen(["bash", "-c", 'exec -a "$0" sleep 60', argv0])
        processes.append(child)
        return child

    def run(action: str, service: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(script), action, service, *args],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=20,
        )

    yield script, env, files, process, run
    for child in processes:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=5)


@pytest.mark.parametrize("service", ["sources", "api", "work", "astro"])
@pytest.mark.parametrize("action", ["start", "restart", "fix", "stop", "status", "logs"])
def test_each_action_routes_to_systemd(harness, service: str, action: str) -> None:
    _, env, files, process, run = harness
    unit = process("unit-main")
    env["FAKE_UNIT_PID"] = str(unit.pid)
    result = run(action, service)
    assert result.returncode == 0, result.stdout + result.stderr
    calls = files["calls"].read_text()
    assert f"show -p LoadState --value learn-ukrainian-{service}.service" in calls
    if action in {"start", "restart", "fix"}:
        assert f"stop learn-ukrainian-{service}.service" in calls
        assert f"start learn-ukrainian-{service}.service" in calls
        assert files["main"].read_text().strip() == str(unit.pid)
    elif action == "stop":
        assert f"stop learn-ukrainian-{service}.service" in calls
    elif action == "status":
        assert "systemd inactive/running restarts=7" in result.stdout
    else:
        assert f"journal:--user -u learn-ukrainian-{service}.service --no-pager -n 80" in result.stdout


@pytest.mark.parametrize("name,argv", [
    ("api", "scripts.api.main:app --host 127.0.0.1 --port 8765"),
    ("astro", "{root}/site/node_modules/astro/bin/astro.mjs preview --port 4321"),
])
def test_owned_stray_is_cleared_before_start(harness, name: str, argv: str) -> None:
    script, env, files, process, run = harness
    unit = process("unit-main")
    stray = process(argv.format(root=script.parent))
    env["FAKE_UNIT_PID"] = str(unit.pid)
    files["listeners"].write_text(f"{stray.pid}\n")
    result = run("start", name)
    assert result.returncode == 0, result.stdout + result.stderr
    assert stray.wait(timeout=2) != 0
    assert files["listeners"].read_text().strip() == str(unit.pid)
    calls = files["calls"].read_text()
    assert calls.index(f"stop learn-ukrainian-{name}.service") < calls.index(f"start learn-ukrainian-{name}.service")


def test_foreign_listener_blocks_start_without_signal(harness) -> None:
    _, env, files, process, run = harness
    unit = process("unit-main")
    foreign = process("unrelated-listener")
    env["FAKE_UNIT_PID"] = str(unit.pid)
    files["listeners"].write_text(f"{foreign.pid}\n")
    result = run("start", "api")
    assert result.returncode != 0
    assert "foreign PID" in result.stderr
    assert foreign.poll() is None
    assert "--user start" not in files["calls"].read_text()


@pytest.mark.parametrize("argv,kind", [
    ("scripts.api.main:app --host 127.0.0.1 --port 8765", "stray"),
    ("unrelated-listener", "foreign"),
])
def test_status_labels_listener_ownership(harness, argv: str, kind: str) -> None:
    _, _, files, process, run = harness
    listener = process(argv)
    files["listeners"].write_text(f"{listener.pid}\n")
    result = run("status", "api")
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{kind}_listener={listener.pid}" in result.stdout
    assert "restarts=7" in result.stdout


def test_stop_clears_stray(harness) -> None:
    _, _, files, process, run = harness
    stray = process("-m work_projection")
    files["listeners"].write_text(f"{stray.pid}\n")
    result = run("stop", "work")
    assert result.returncode == 0, result.stdout + result.stderr
    assert stray.wait(timeout=2) != 0
    assert "--user start" not in files["calls"].read_text()


@pytest.mark.parametrize("load", ["masked", "unreachable"])
def test_unavailable_unit_fails_closed(harness, load: str) -> None:
    _, env, files, _, run = harness
    env["FAKE_LOAD"] = load
    unit_file = Path(env["XDG_CONFIG_HOME"]) / "systemd/user/learn-ukrainian-api.service"
    unit_file.parent.mkdir(parents=True)
    unit_file.write_text("[Unit]\n")
    result = run("start", "api")
    assert result.returncode != 0
    assert "ERROR" in result.stderr
    assert "--user start" not in files["calls"].read_text()


def test_missing_systemctl_with_unit_fails_closed(harness) -> None:
    _, env, _, _, run = harness
    env["SVC_SYSTEMCTL_BIN"] = "/missing/systemctl"
    unit_file = Path(env["XDG_CONFIG_HOME"]) / "systemd/user/learn-ukrainian-api.service"
    unit_file.parent.mkdir(parents=True)
    unit_file.write_text("[Unit]\n")
    result = run("start", "api")
    assert result.returncode != 0
    assert "unavailable" in result.stderr


def test_user_bus_environment_is_exported(harness) -> None:
    _, env, files, _, run = harness
    runtime = Path(f"/run/user/{os.getuid()}")
    if not runtime.is_dir():
        pytest.skip("user runtime directory is absent")
    env.pop("XDG_RUNTIME_DIR", None)
    env.pop("DBUS_SESSION_BUS_ADDRESS", None)
    result = run("status", "api")
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"bus=unix:path={runtime}/bus runtime={runtime}" in files["calls"].read_text()


def test_not_found_uses_launchd_path(harness) -> None:
    _, env, files, _, run = harness
    env["FAKE_LOAD"] = "not-found"
    env["FAKE_HEALTH"] = "0"
    result = run("start", "api", "--live")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "start --repo-root" in files["calls"].read_text()
    assert "--user start" not in files["calls"].read_text()


def test_live_api_refused_under_systemd(harness) -> None:
    _, _, files, _, run = harness
    result = run("start", "api", "--live")
    assert result.returncode != 0
    assert "only to launchd" in result.stderr
    assert "--user stop" not in files["calls"].read_text()
