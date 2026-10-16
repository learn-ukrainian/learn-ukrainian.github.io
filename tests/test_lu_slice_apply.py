"""lu.slice apply/check/rollback helper (#9624) against a fake manager and cgroup.

The unit file carries no limits; a deployment drop-in supplies them. The byte
values here are synthetic test values, not any host's sizing.
"""

from __future__ import annotations

import configparser
import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/ops/lu_slice_apply.sh"
HIGH, MAX, SWAP = str(3 * 2**30), str(4 * 2**30), str(2**29)
DROPIN = f"[Slice]\nMemoryHigh={HIGH}\nMemoryMax={MAX}\nMemorySwapMax={SWAP}\n"


def _sandbox(tmp_path: Path, current: int, reload_applies: bool = True, dropin: str | None = DROPIN) -> dict[str, str]:
    cg = tmp_path / "cg"
    cg.mkdir()
    (cg / "memory.current").write_text(f"{current}\n")
    for name in ("memory.high", "memory.max", "memory.swap.max"):
        (cg / name).write_text("max\n")
    units = tmp_path / "units"
    if dropin is not None:
        (units / "lu.slice.d").mkdir(parents=True)
        (units / "lu.slice.d/10-limits.conf").write_text(dropin)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    log = tmp_path / "systemctl.log"
    fake = bindir / "systemctl"
    # show resolves the limits drop-in like the manager does (infinity without
    # it); daemon-reload applies the drop-in values (or clears limits when it is
    # gone); set-property --runtime writes a control drop-in and applies it.
    fake.write_text(
        f"""#!/usr/bin/env bash
printf '%s\\n' "$*" >> {log}
cg={cg}
drop="$LU_SLICE_UNIT_DIR/lu.slice.d/10-limits.conf"
ctl="$LU_SLICE_RUNTIME_CONTROL_DIR/lu.slice.d"
val() {{ [ "$1" = infinity ] && echo max || echo "$1"; }}
key() {{ sed -n "s/^$1=//p" "$drop" 2>/dev/null | tail -n 1; }}
case "$2" in
 show)
  if [ -f "$drop" ]; then
    printf 'MemoryHigh=%s\\nMemoryMax=%s\\nMemorySwapMax=%s\\nDropInPaths=%s\\n' \\
      "$(key MemoryHigh)" "$(key MemoryMax)" "$(key MemorySwapMax)" "$drop"
  else
    printf 'MemoryHigh=infinity\\nMemoryMax=infinity\\nMemorySwapMax=infinity\\nDropInPaths=\\n'
  fi ;;
 daemon-reload)
  if [ -f "$ctl/50-override.conf" ]; then exit 0; fi
  if [ -f "$drop" ] && [ "${{FAKE_RELOAD_APPLIES:-1}}" = 1 ]; then
    key MemoryHigh > $cg/memory.high; key MemoryMax > $cg/memory.max; key MemorySwapMax > $cg/memory.swap.max
  elif [ ! -f "$drop" ]; then
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
        "LU_SLICE_UNIT_DIR": str(units),
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
    names = ("memory.high", "memory.max", "memory.swap.max")
    return tuple((cg / n).read_text().strip() for n in names)  # type: ignore[return-value]


def test_unit_file_carries_no_limits() -> None:
    body = (REPO / "packaging/systemd/lu.slice").read_text()
    section = body.split("[Slice]", 1)[1]
    keys = {line.split("=", 1)[0] for line in section.splitlines() if "=" in line and not line.startswith("#")}
    assert keys == {"MemoryAccounting"}
    assert "lu.slice.d/10-limits.conf" in body


def test_check_refuses_above_max(tmp_path: Path) -> None:
    env = _sandbox(tmp_path, int(MAX) + 1)
    result = _run(env, "apply")
    assert result.returncode == 4
    assert "LU_SLICE_REFUSED" in result.stderr
    assert not (tmp_path / "units/lu.slice").exists()
    assert _limits(env) == ("max", "max", "max")


@pytest.mark.parametrize(
    "dropin",
    [None, "[Slice]\nMemoryHigh=infinity\nMemoryMax=infinity\nMemorySwapMax=infinity\n"],
    ids=["missing", "infinite"],
)
@pytest.mark.parametrize("mode", ["check", "apply"])
def test_refuses_without_finite_limits_dropin(tmp_path: Path, mode: str, dropin: str | None) -> None:
    env = _sandbox(tmp_path, 1, dropin=dropin)
    result = _run(env, mode)
    assert result.returncode == 7, result.stderr
    assert "LU_SLICE_REFUSED limits-" in result.stderr
    assert not (tmp_path / "units/lu.slice").exists()
    assert _limits(env) == ("max", "max", "max")


@pytest.mark.parametrize(("current", "warned"), [(2**30, False), (int(HIGH), True), (int(MAX), True)])
def test_check_warns_at_or_above_high(tmp_path: Path, current: int, warned: bool) -> None:
    result = _run(_sandbox(tmp_path, current), "check")
    assert result.returncode == 0, result.stderr
    assert ("LU_SLICE_WARN" in result.stderr) is warned
    assert f"high={HIGH} max={MAX}" in result.stdout


@pytest.mark.parametrize("reload_applies", [True, False])
def test_apply_then_rollback_restores_max(tmp_path: Path, reload_applies: bool) -> None:
    env = _sandbox(tmp_path, 2**30, reload_applies)
    applied = _run(env, "apply")
    assert applied.returncode == 0, applied.stderr
    assert _limits(env) == (HIGH, MAX, SWAP)
    unit = (REPO / "packaging/systemd/lu.slice").read_text()
    assert (tmp_path / "units/lu.slice").read_text() == unit
    rolled = _run(env, "rollback")
    assert rolled.returncode == 0, rolled.stderr
    assert _limits(env) == ("max", "max", "max")
    assert not (tmp_path / "units/lu.slice").exists()
    assert not (tmp_path / "units/lu.slice.d").exists()
    assert not (tmp_path / "ctl-runtime/lu.slice.d").exists()
    assert not (tmp_path / "ctl-persist/lu.slice.d").exists()


def test_rollback_removes_persistent_control_dropin(tmp_path: Path) -> None:
    env = _sandbox(tmp_path, 1)
    stale = tmp_path / "ctl-persist/lu.slice.d"
    stale.mkdir(parents=True)
    (stale / "50-MemoryMax.conf").write_text(f"[Slice]\nMemoryMax={MAX}\n")
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


# CPU-time containment (#10735): the ceiling is documentation plus an inert example.
CPU_DROPIN_DIR = REPO / "packaging/systemd/dropins/lu.slice.d"
WEIGHT_EXAMPLE = CPU_DROPIN_DIR / "20-cpu-weight.conf.example"
QUOTA_EXAMPLE = CPU_DROPIN_DIR / "30-cpu-quota.conf.example"
RUNBOOK = REPO / "docs/runbooks/driver-memory-scope.md"


def _slice_keys(path: Path) -> dict[str, str]:
    assert path.name.endswith(".example")  # systemd never loads it
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    parser.read_string(path.read_text())
    assert parser.sections() == ["Slice"]
    return dict(parser["Slice"])


def test_cpu_examples_are_inert_and_have_exactly_the_documented_keys() -> None:
    # CPUAccounting= is deprecated since systemd 258 (no effect), so it is absent.
    assert _slice_keys(WEIGHT_EXAMPLE) == {"CPUWeight": "50"}
    assert _slice_keys(QUOTA_EXAMPLE) == {"CPUQuota": "1200%", "CPUQuotaPeriodSec": "100ms"}


def test_cpu_examples_are_the_only_cpu_dropins_and_leave_the_memory_dropin_alone() -> None:
    names = sorted(path.name for path in CPU_DROPIN_DIR.iterdir())
    assert names == ["20-cpu-weight.conf.example", "30-cpu-quota.conf.example"]
    assert not (CPU_DROPIN_DIR / "10-limits.conf").exists()


# The tests below pin runbook and example prose. A deliberate procedure edit is
# expected to update them in the same change.
def _cpu_section() -> str:
    body = RUNBOOK.read_text()
    return body.split("## CPU-time containment", 1)[1].split("\n## ", 1)[0]


def test_runbook_cpu_section_names_each_verification_property() -> None:
    section = _cpu_section()
    for needle in (
        "CPUQuotaPerSecUSec", "CPUQuotaPeriodUSec", "CPUWeight",
        "MemoryMax", "MemoryHigh", "MemorySwapMax", "cpu.max", "cpu.weight",
        "nr_throttled", "throttled_usec", "cpu.pressure", "/api/health",
        "20-cpu-weight.conf", "30-cpu-quota.conf", "daemon-reload", "1200%", "100ms",
    ):  # fmt: skip
        assert needle in section, needle
    assert "not a load-average bound and not a thread-count bound" in section
    assert "no script" in section


def test_runbook_records_memory_snapshot_before_the_change() -> None:
    section = _cpu_section()
    snapshot = "systemctl --user show lu.slice -p MemoryHigh -p MemoryMax -p MemorySwapMax"
    assert snapshot in section
    assert section.index(snapshot) < section.index("install -m 0644")


def test_runbook_persistent_dropin_is_the_only_path() -> None:
    section = _cpu_section()
    assert "set-property --runtime" not in section
    assert "CPUQuota= CPUWeight=" not in section
    rollback = section.split("### Rollback", 1)[1]
    assert rollback.count("rm ") == 2  # one CPU file per stage, never both at once
    assert 'rm "$D/30-cpu-quota.conf"' in rollback
    assert 'rm "$D/20-cpu-weight.conf"' in rollback
    assert "Never run `systemctl --user revert lu.slice`" in " ".join(section.split())
    assert "10-limits.conf" in rollback and "never touched" in rollback
    assert "cpu.max" in rollback and "stop and report to" in rollback


def test_runbook_rollback_checks_first_cpu_max_field_and_snapshots() -> None:
    rollback = " ".join(_cpu_section().split("### Rollback", 1)[1].split())
    assert "`max 100000`" in rollback
    assert "compare the first field with `max`" in rollback
    assert "treat `max <period>` as cleared" in rollback
    assert "`cpu.weight` back to the default `100`" in rollback
    assert "equal the snapshot recorded before the change" in rollback
    condition, action = rollback.split("stop and report to the driver", 1)
    condition = condition.rsplit("If the first field", 1)[1]
    for needle in ("of `cpu.max` is not `max`", "`MemoryHigh`", "`MemoryMax`", "`MemorySwapMax`"):
        assert needle in condition, needle
    assert "do not add a runtime override" in action


def test_runbook_verify_states_the_apply_time_cpu_max_line() -> None:
    verify = " ".join(_cpu_section().split("### Verify", 1)[1].split("### Observe", 1)[0].split())
    assert "`<quota> <period>`" in verify
    assert "apply-time expected line is `1200000 100000`" in verify
    assert "`cpu.weight` `50`" in verify
    assert "`CPUQuotaPerSecUSec=12s`" in verify and "`CPUQuotaPeriodUSec=100ms`" in verify
    assert "There is no `CPUAccounting` property" in verify


def test_runbook_quota_rationale_is_an_average_cap_not_a_reservation() -> None:
    section = _cpu_section()
    assert "average cap per period" in section
    assert "does not reserve any CPUs" in section
    assert "only makes the slice yield CPU to its siblings while the parent cgroup is contended" in " ".join(
        section.split()
    )
    assert "is not a cap" in section
    assert "1.2 CPU-seconds per 100 ms, then" in " ".join(section.split())


def test_runbook_publishes_no_host_sizing() -> None:
    body = RUNBOOK.read_text()
    assert not re.search(r"\b(16|sixteen)\s+CPUs?\b|\bof sixteen\b", body, re.IGNORECASE)
    assert not re.search(r"CPU-equivalents|\bmean of\b", body, re.IGNORECASE)
    assert "private operations" in _cpu_section()


def test_runbook_cpu_section_is_staged_with_gates_and_the_approved_scope() -> None:
    section = " ".join(_cpu_section().split())
    for needle in (
        "weight approved now, quota approved only after gate G2",
        "Stage 0: sampler (read-only",
        "Stage 1: weight only",
        "Gate G1: the PR that added these files is merged and stage 0 has at least 1 hour of samples",
        "rehearse the stage 1 rollback once",
        "controlled 10-worker pytest burst once under weight only",
        "Stage 2: quota",
        "Gate G2",
        "24 hours of samples under weight 50",
        "at or below 12.0 CPUs",
        "no stage 1 stop trigger fired",
        "do not apply the quota",
        "report the distribution to the advisors or the operator",
        "rerun the same burst, and observe for 24 hours",
    ):
        assert needle in section, needle


def test_runbook_cpu_section_lists_the_five_stop_triggers() -> None:
    triggers = _cpu_section().split("### Stop triggers", 1)[1].split("### Rollback", 1)[0]
    flat = " ".join(triggers.split())
    assert len(re.findall(r"^\d\. ", triggers, re.MULTILINE)) == 5
    for needle in (
        "`/api/health` call takes over 1 s",
        "more than 2x the stage 1 burst's",
        "3600 s wait limit",
        "pre-push gate stage times out",
        "`throttled_usec` is growing",
        "exceeds 25% over any hour",
        "`lu-driver.slice` CPU-pressure rate is more than 2x",
        "A memory limit differs from the snapshot",
        "`cpu.max` / `cpu.weight` do not read as expected",
    ):
        assert needle in flat, needle


def test_runbook_cpu_section_notes_work_outside_the_slice_and_the_sampler() -> None:
    section = " ".join(_cpu_section().split())
    assert "About 1.4 CPUs on average of fleet work" in section
    assert "runs outside `lu.slice` and is uncapped" in section
    assert "Moving that work into the slice is a separate approval" in section
    assert "sleep 10; done >> batch_state/reports/10735-cpu-samples.log" in section
    assert "never add a runtime override" in section


def test_cpu_examples_do_not_claim_accounting_enforces_the_quota() -> None:
    weight = " ".join(WEIGHT_EXAMPLE.read_text().replace("# ", " ").split())
    quota = " ".join(QUOTA_EXAMPLE.read_text().replace("# ", " ").split())
    assert "CPUAccounting" not in weight + quota
    assert "It is enforced through cpu.max" in quota
    assert "only while the parent cgroup is contended" in weight
    assert "not a cap" in weight
    assert "host is busy" not in weight + quota


# sha256 of scripts/ops/lu_slice_apply.sh at the #10735 base commit. The CPU
# ceiling is documentation plus an inert example, so the apply script must not
# change: it must not parse unit or drop-in text. A deliberate edit to the
# script must update this recorded hash.
APPLY_SCRIPT_SHA256 = "e7beafca407a619b6b96dbd0adce55371c69be84d931d69224cd92711c0c94fd"


def test_apply_script_matches_recorded_hash() -> None:
    assert hashlib.sha256(HELPER.read_bytes()).hexdigest() == APPLY_SCRIPT_SHA256
