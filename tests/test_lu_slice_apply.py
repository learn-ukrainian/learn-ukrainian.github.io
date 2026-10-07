"""lu.slice apply/check/rollback helper (#9624) against a fake manager and cgroup."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/ops/lu_slice_apply.sh"
HIGH, MAX, SWAP = "25769803776", "27917287424", "4294967296"


def _sandbox(tmp_path: Path, current: int, reload_applies: bool = True) -> dict[str, str]:
    cg = tmp_path / "cg"
    cg.mkdir()
    (cg / "memory.current").write_text(f"{current}\n")
    for name in ("memory.high", "memory.max", "memory.swap.max"):
        (cg / name).write_text("max\n")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "systemctl.log"
    fake = bindir / "systemctl"
    # daemon-reload applies the installed unit file (or clears limits when it is gone);
    # set-property --runtime writes a control drop-in and applies its values.
    fake.write_text(
        f"""#!/usr/bin/env bash
printf '%s\\n' "$*" >> {log}
cg={cg}
unit="$LU_SLICE_UNIT_DIR/lu.slice"
ctl="$LU_SLICE_RUNTIME_CONTROL_DIR/lu.slice.d"
val() {{ [ "$1" = infinity ] && echo max || echo "$1"; }}
case "$2" in
 daemon-reload)
  if [ -f "$ctl/50-override.conf" ]; then exit 0; fi
  if [ -f "$unit" ] && [ "${{FAKE_RELOAD_APPLIES:-1}}" = 1 ]; then
    echo {HIGH} > $cg/memory.high; echo {MAX} > $cg/memory.max; echo {SWAP} > $cg/memory.swap.max
  elif [ ! -f "$unit" ]; then
    for f in memory.high memory.max memory.swap.max; do echo max > $cg/$f; done
  fi ;;
 set-property)
  mkdir -p "$ctl"; printf '%s\\n' "$*" > "$ctl/50-override.conf"
  for kv in "${{@:5}}"; do
    case "$kv" in
     MemoryHigh=*) val "${{kv#*=}}" > $cg/memory.high ;;
     MemoryMax=*) val "${{kv#*=}}" > $cg/memory.max ;;
     MemorySwapMax=*) val "${{kv#*=}}" > $cg/memory.swap.max ;;
    esac
  done
  ;;
esac
"""
    )
    fake.chmod(0o755)
    return {
        "PATH": f"{bindir}:{os.environ['PATH']}",
        "LU_SLICE_CGROUP": str(cg),
        "LU_SLICE_UNIT_DIR": str(tmp_path / "units"),
        "LU_SLICE_CONTROL_DIR": str(tmp_path / "ctl-persist"),
        "LU_SLICE_RUNTIME_CONTROL_DIR": str(tmp_path / "ctl-runtime"),
        "FAKE_RELOAD_APPLIES": "1" if reload_applies else "0",
    }


def _run(env: dict[str, str], mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(HELPER), mode],
        env={**os.environ, **env},
        capture_output=True,
        text=True,
        timeout=15,
    )


def _limits(env: dict[str, str]) -> tuple[str, str, str]:
    cg = Path(env["LU_SLICE_CGROUP"])
    return tuple((cg / n).read_text().strip() for n in ("memory.high", "memory.max", "memory.swap.max"))  # type: ignore[return-value]


def test_check_refuses_above_max(tmp_path: Path) -> None:
    env = _sandbox(tmp_path, int(MAX) + 1)
    result = _run(env, "apply")
    assert result.returncode == 4
    assert "LU_SLICE_REFUSED" in result.stderr
    assert not (tmp_path / "units/lu.slice").exists()
    assert _limits(env) == ("max", "max", "max")


@pytest.mark.parametrize(("current", "warned"), [(15 * 2**30, False), (int(HIGH), True), (int(MAX), True)])
def test_check_warns_at_or_above_high(tmp_path: Path, current: int, warned: bool) -> None:
    result = _run(_sandbox(tmp_path, current), "check")
    assert result.returncode == 0, result.stderr
    assert ("LU_SLICE_WARN" in result.stderr) is warned


@pytest.mark.parametrize("reload_applies", [True, False])
def test_apply_then_rollback_restores_max(tmp_path: Path, reload_applies: bool) -> None:
    env = _sandbox(tmp_path, 15 * 2**30, reload_applies)
    applied = _run(env, "apply")
    assert applied.returncode == 0, applied.stderr
    assert _limits(env) == (HIGH, MAX, SWAP)
    assert (tmp_path / "units/lu.slice").read_text() == (REPO / "packaging/systemd/lu.slice").read_text()
    rolled = _run(env, "rollback")
    assert rolled.returncode == 0, rolled.stderr
    assert _limits(env) == ("max", "max", "max")
    assert not (tmp_path / "units/lu.slice").exists()
    assert not (tmp_path / "ctl-runtime/lu.slice.d").exists()
    assert not (tmp_path / "ctl-persist/lu.slice.d").exists()


def test_rollback_removes_persistent_control_dropin(tmp_path: Path) -> None:
    env = _sandbox(tmp_path, 1)
    stale = tmp_path / "ctl-persist/lu.slice.d"
    stale.mkdir(parents=True)
    (stale / "50-MemoryMax.conf").write_text("[Slice]\nMemoryMax=27917287424\n")
    result = _run(env, "rollback")
    assert result.returncode == 0, result.stderr
    assert not stale.exists()


def test_never_restarts_or_stops_units(tmp_path: Path) -> None:
    env = _sandbox(tmp_path, 1, reload_applies=False)
    assert _run(env, "apply").returncode == 0
    assert _run(env, "rollback").returncode == 0
    calls = (tmp_path / "systemctl.log").read_text()
    for verb in ("restart", "stop", "kill", "start "):
        assert verb not in calls
