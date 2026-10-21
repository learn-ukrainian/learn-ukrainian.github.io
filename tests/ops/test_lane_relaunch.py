"""Boot-time lane relaunch against a fake tmux (#10814)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops import context_guard as cg
from scripts.ops import lane_relaunch as lr
from scripts.ops.driver_lanes import PANE_SCRIPT, Registry, load_local_config, load_registry
from tests.ops._fake_tmux import FakePane, FakeTmux

REPO = Path(__file__).resolve().parents[2]
SESSIONS = ["infra-muse", "devops-muse", "harness", "atlas", "practice", "open-model-data", "cto"]


def run(fake: FakeTmux, tmp_path: Path, registry: Registry | None = None, **kwargs) -> list[lr.Outcome]:
    return lr.relaunch(
        registry or load_registry(),
        repo_root=tmp_path,
        tmux=cg.Tmux(run=fake.run, sleep=fake.sleep, clock=fake.clock),
        local={},
        log=lambda _m: None,
        settle_s=kwargs.pop("settle_s", 4),
        **kwargs,
    )


def created(fake: FakeTmux) -> list[str]:
    out = []
    for call in fake.calls:
        argv = call[call.index("tmux"):] if call[0] == "systemd-run" else call
        if argv[:2] == ["tmux", "new-session"]:
            out.append(argv[argv.index("-s") + 1])
    return out


def test_relaunch_creates_every_lane_with_cto_last_and_second_run_is_noop(tmp_path: Path) -> None:
    fake = FakeTmux(server_running=False)
    first = run(fake, tmp_path)
    assert created(fake) == SESSIONS
    assert [o.status for o in first] == ["started"] * 7
    fake.calls.clear()
    second = run(fake, tmp_path)
    assert created(fake) == []
    assert [o.status for o in second] == ["exists"] * 7
    assert not any(call[:2] == ["tmux", "send-keys"] for call in fake.calls)


def test_existing_session_is_skipped_and_never_typed_into(tmp_path: Path) -> None:
    fake = FakeTmux(sessions={"atlas": FakePane(agent="codex")}, clients=[("atlas", int(1e6))])
    outcomes = run(fake, tmp_path)
    assert "atlas" not in created(fake)
    assert {o.session: o.status for o in outcomes}["atlas"] == "exists"
    assert not any("=atlas" in call for call in fake.calls if call[1] not in {"has-session", "capture-pane"})


def test_lead_lane_starts_last_even_when_listed_first(tmp_path: Path) -> None:
    registry = load_registry()
    lanes = sorted(registry.lanes, key=lambda lane: not lane.lead)  # cto first in data order
    assert lanes[0].session == "cto"
    fake = FakeTmux()
    run(fake, tmp_path, Registry(lanes=tuple(lanes), settings=registry.settings, guard_sender=registry.guard_sender))
    assert created(fake)[-1] == "cto"


def test_launcher_exit_is_logged_and_relaunch_moves_on(tmp_path: Path) -> None:
    fake = FakeTmux(exit_on_create={"harness": 1})
    outcomes = {o.session: o for o in run(fake, tmp_path)}
    assert outcomes["harness"].status == "launcher-exited" and outcomes["harness"].detail == "rc=1"
    assert created(fake) == SESSIONS
    assert not any("--force" in arg for call in fake.calls for arg in call)


def test_codex_lanes_get_shims_first_and_repo_root_cwd(tmp_path: Path) -> None:
    fake = FakeTmux()
    run(fake, tmp_path)
    by_session = {c[c.index("-s") + 1]: c for c in fake.calls if c[:2] == ["tmux", "new-session"]}
    for session in ("harness", "atlas", "open-model-data"):
        call = by_session[session]
        assert call[call.index("-c") + 1] == str(tmp_path)
        assert call[call.index("-e") + 1].startswith(f"PATH={tmp_path / 'scripts/agent_runtime/shims'}:")
        command = call[call.index("bash"):]
        assert command[:4] == ["bash", "-c", PANE_SCRIPT, "lane-launch"]
        assert command[4:6] == ["./start-codex-driver.sh", "--epic"]
    assert "-e" not in by_session["infra-muse"]  # no local config: launcher default account


def test_missing_server_is_started_in_its_own_scope_once(tmp_path: Path) -> None:
    fake = FakeTmux(server_running=False)
    run(fake, tmp_path, server_scope=True)
    scoped = [c for c in fake.calls if c[0] == "systemd-run"]
    assert len(scoped) == 1 and "--scope" in scoped[0] and "--user" in scoped[0]
    assert scoped[0][scoped[0].index("tmux") + 4] == "infra-muse"


def test_dry_run_prints_full_plan_and_starts_nothing(tmp_path: Path) -> None:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    marker = tmp_path / "tmux-called"
    for tool in ("tmux", "systemd-run"):
        stub = bin_dir / tool
        stub.write_text(f"#!/bin/sh\necho \"$0 $*\" >> '{marker}'\n", encoding="utf-8")
        stub.chmod(0o755)
    local = tmp_path / "lanes.local.json"
    local.write_text(json.dumps({"lanes": {
        "cto": {"wrapper": ["lane-wrapper-cto", "--here"], "env": {"CLAUDE_CONFIG_DIR": "secret-account-dir"}},
    }}), encoding="utf-8")
    local.chmod(0o600)
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ.get('PATH', '')}", LU_DRIVER_LANES_LOCAL=str(local))
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/ops/lane_relaunch.py"), "--dry-run"],
        capture_output=True, text=True, env=env, check=True, timeout=60,
    )
    plan = json.loads(result.stdout)
    assert [entry["session"] for entry in plan] == SESSIONS
    assert all(set(entry) == {"session", "command", "cwd", "env_keys", "source"} for entry in plan)
    assert all(entry["cwd"] == str(REPO) for entry in plan)
    assert plan[-1]["command"] == "lane-wrapper-cto --here" and plan[-1]["env_keys"] == ["CLAUDE_CONFIG_DIR"]
    assert plan[2]["env_keys"] == ["PATH"]
    assert "secret-account-dir" not in result.stdout
    assert not marker.exists()


def test_main_exit_code_reports_failed_lanes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeTmux(exit_on_create={"atlas": 1})
    real = cg.Tmux
    monkeypatch.setattr(lr, "Tmux", lambda: real(run=fake.run, sleep=fake.sleep, clock=fake.clock))
    monkeypatch.setenv("LU_DRIVER_LANES_LOCAL", str(tmp_path / "absent.json"))
    assert lr.main(["--settle-seconds", "2"]) == 3
    assert lr.main(["--settle-seconds", "2"]) == 0  # every session exists now


# ---- refused or unreadable lanes (review of 69264fbb, #10814) ----------------------
def refusing_local(tmp_path: Path) -> Path:
    local = tmp_path / "lanes.local.json"
    local.write_text(json.dumps({"lanes": {"atlas": {"wrapper": "printf expected; printf INJECTED"}}}), encoding="utf-8")
    local.chmod(0o600)
    return local


def test_refused_wrapper_lane_is_logged_and_not_started(tmp_path: Path) -> None:
    fake = FakeTmux()
    logs: list[str] = []
    outcomes = lr.relaunch(
        load_registry(),
        repo_root=tmp_path,
        tmux=cg.Tmux(run=fake.run, sleep=fake.sleep, clock=fake.clock),
        local=load_local_config(refusing_local(tmp_path)),
        log=logs.append,
        settle_s=2,
    )
    assert created(fake) == [s for s in SESSIONS if s != "atlas"]
    assert {o.session: o.status for o in outcomes}["atlas"] == "config-refused"
    assert any(line.startswith("atlas: not started, local lane config: atlas: wrapper word") for line in logs)
    assert not any("INJECTED" in arg for call in fake.calls for arg in call)


def test_refused_lane_fails_main_and_shows_in_dry_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = FakeTmux()
    real = cg.Tmux
    monkeypatch.setattr(lr, "Tmux", lambda: real(run=fake.run, sleep=fake.sleep, clock=fake.clock))
    monkeypatch.setenv("LU_DRIVER_LANES_LOCAL", str(refusing_local(tmp_path)))
    assert lr.main(["--dry-run"]) == 0
    plan = {entry["session"]: entry for entry in json.loads(capsys.readouterr().out)}
    assert set(plan["atlas"]) == {"session", "refused"} and "shell syntax" in plan["atlas"]["refused"]
    assert fake.calls == []
    assert lr.main(["--settle-seconds", "2"]) == 3
    assert "atlas" not in created(fake)


def test_unreadable_new_pane_is_unverified_and_relaunch_moves_on(tmp_path: Path) -> None:
    fake = FakeTmux(override={"capture-pane": subprocess.CompletedProcess([], 1, "", "can't find pane")})
    outcomes = run(fake, tmp_path)
    assert [o.status for o in outcomes] == ["unverified"] * 7
    assert created(fake) == SESSIONS
