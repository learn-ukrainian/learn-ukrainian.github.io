"""Lexicon runner memory caps come from configuration, with generic defaults."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.lexicon.runner import contracts

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "lexicon" / "runner"
LAUNCHERS = ("launch_enrich.sh", "launch_reduce.sh", "launch_reenrich_class_b.sh")
ENV_NAMES = (
    contracts.ENV_MEMORY_HIGH_MIB,
    contracts.ENV_MEMORY_MAX_MIB,
    contracts.ENV_JOB_MEMORY_HIGH_MIB,
    contracts.ENV_JOB_MEMORY_MAX_MIB,
)
BASH = shutil.which("bash") or "bash"
INVALID = ("0", "-1", "2.25", "1G", "lots", "007x", "000", "1" * 19, "\x1c777", "\u00a0777")


def _clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in ENV_NAMES}


def _fake_systemd(tmp_path: Path) -> tuple[Path, Path]:
    """Fake systemctl/systemd-run on PATH; systemd-run records its argv."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    record = tmp_path / "systemd-run.args"
    # Like a real --wait unit, the wrapper stays alive while the launcher polls.
    run_script = [
        f"#!{BASH}",
        f'printf "%s\\n" "$@" > "{record}.tmp" && mv "{record}.tmp" "{record}"',
        "sleep 1",
    ]
    ctl_script = [
        f"#!{BASH}",
        'case "$*" in',
        "  *is-system-running*) exit 0 ;;",
        f'  *MainPID*) [[ -f "{record}" ]] && echo 4242 ;;',
        "esac",
        "exit 0",
    ]
    (bin_dir / "systemd-run").write_text("\n".join(run_script) + "\n", encoding="utf-8")
    (bin_dir / "systemctl").write_text("\n".join(ctl_script) + "\n", encoding="utf-8")
    for tool in bin_dir.iterdir():
        tool.chmod(0o755)
    return bin_dir, record


def _launcher_env(tmp_path: Path, bin_dir: Path, **extra: str) -> dict[str, str]:
    work = tmp_path / "work"
    inputs = tmp_path / "inputs"
    inputs.mkdir(exist_ok=True)
    for name in ("candidate.json", "sources.db", "kaikki.json"):
        (inputs / name).write_text("{}", encoding="utf-8")
    return {
        **_clean_env(),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "ATLAS_RUN_ROOT": str(tmp_path),
        "ATLAS_REPO": str(ROOT),
        "ATLAS_WORK_DIR": str(work),
        "ATLAS_CANDIDATE": str(inputs / "candidate.json"),
        "ATLAS_SOURCES_DB": str(inputs / "sources.db"),
        "ATLAS_KAIKKI_JSON": str(inputs / "kaikki.json"),
        "ATLAS_ENRICH_UNIT": "lu-test-enrich.service",
        "ATLAS_REDUCE_UNIT": "lu-test-reduce.service",
        **extra,
    }


@pytest.mark.parametrize("launcher", ("launch_enrich.sh", "launch_reduce.sh"))
@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, (contracts.GENERIC_JOB_MEMORY_HIGH_MIB, contracts.GENERIC_JOB_MEMORY_MAX_MIB)),
        ({contracts.ENV_JOB_MEMORY_HIGH_MIB: " 900 ", contracts.ENV_JOB_MEMORY_MAX_MIB: "1100"}, (900, 1100)),
        ({contracts.ENV_JOB_MEMORY_HIGH_MIB: "0900", contracts.ENV_JOB_MEMORY_MAX_MIB: "01100"}, (900, 1100)),
        (
            {contracts.ENV_JOB_MEMORY_HIGH_MIB: "   ", contracts.ENV_JOB_MEMORY_MAX_MIB: "\t"},
            (contracts.GENERIC_JOB_MEMORY_HIGH_MIB, contracts.GENERIC_JOB_MEMORY_MAX_MIB),
        ),
    ],
)
def test_launcher_forwards_resolved_caps_across_the_service_boundary(
    launcher: str, env: dict[str, str], expected: tuple[int, int], tmp_path: Path
) -> None:
    bin_dir, record = _fake_systemd(tmp_path)
    out = subprocess.run(
        ["bash", str(RUNNER / launcher)],
        env=_launcher_env(tmp_path, bin_dir, **env),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert out.returncode == 0, out.stderr
    argv = record.read_text(encoding="utf-8").splitlines()
    high, cap = expected
    assert f"--property=MemoryHigh={high}M" in argv
    assert f"--property=MemoryMax={cap}M" in argv
    assert f"--property=Environment=LU_LEXICON_JOB_MEMORY_HIGH_MIB={high}" in argv
    assert f"--property=Environment=LU_LEXICON_JOB_MEMORY_MAX_MIB={cap}" in argv
    i = argv.index("--memory-high-mib")
    assert argv[i + 1] == str(high)
    j = argv.index("--memory-max-mib")
    assert argv[j + 1] == str(cap)


@pytest.mark.parametrize("launcher", LAUNCHERS)
@pytest.mark.parametrize("bad", INVALID)
def test_launcher_refuses_invalid_caps_before_side_effects(launcher: str, bad: str, tmp_path: Path) -> None:
    bin_dir, record = _fake_systemd(tmp_path)
    env = _launcher_env(tmp_path, bin_dir, **{contracts.ENV_JOB_MEMORY_MAX_MIB: bad})
    env["ATLAS_RE_ENRICH_WORK_DIR"] = str(tmp_path / "work")
    out = subprocess.run(
        ["bash", str(RUNNER / launcher)], env=env, capture_output=True, text=True, timeout=60, check=False
    )
    assert out.returncode == 2
    assert "positive whole number of MiB" in out.stderr
    assert not (tmp_path / "work").exists()
    assert not record.exists()


@pytest.mark.parametrize("launcher", ("launch_enrich.sh", "launch_reduce.sh"))
@pytest.mark.parametrize(
    "flag",
    [
        ["--memory-high-mib", "777"],
        ["--memory-max-mib=777"],
        ["--memory-h", "777"],
        ["--mem=777"],
    ],
)
def test_launcher_refuses_caller_memory_flags_before_side_effects(
    launcher: str, flag: list[str], tmp_path: Path
) -> None:
    bin_dir, record = _fake_systemd(tmp_path)
    out = subprocess.run(
        ["bash", str(RUNNER / launcher), *flag],
        env=_launcher_env(tmp_path, bin_dir),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert out.returncode == 2
    assert "is not accepted" in out.stderr
    assert not (tmp_path / "work").exists()
    assert not record.exists()


@pytest.mark.parametrize("launcher", LAUNCHERS)
@pytest.mark.parametrize("raw", ["", "   ", "\t\n", "\x1c777", "\u00a0777", "\u0661\u0662", "+777", " 0777 "])
def test_launcher_and_python_agree_on_each_raw_value(launcher: str, raw: str) -> None:
    text = (RUNNER / launcher).read_text(encoding="utf-8")
    start = text.index("_trim_mib() {")
    end = text.index("export LU_LEXICON_JOB_MEMORY_HIGH_MIB=")
    end = text.index("\n", end) + 1
    script = text[start:end] + 'printf "%s" "$LU_LEXICON_JOB_MEMORY_HIGH_MIB"'
    env = {**_clean_env(), contracts.ENV_JOB_MEMORY_HIGH_MIB: raw}
    out = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=10, check=False)
    try:
        expected = str(contracts.env_mib(contracts.ENV_JOB_MEMORY_HIGH_MIB, contracts.GENERIC_JOB_MEMORY_HIGH_MIB, env))
    except ValueError:
        assert out.returncode == 2
    else:
        assert out.returncode == 0, out.stderr
        assert out.stdout == expected
