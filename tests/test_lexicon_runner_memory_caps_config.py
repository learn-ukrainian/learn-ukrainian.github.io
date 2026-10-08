"""Lexicon runner memory caps come from configuration, with generic defaults."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lexicon.runner import contracts, enrich_offline_20k, reduce_ulif_20k

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


def test_env_mib_reads_a_positive_whole_number_or_the_default() -> None:
    assert contracts.env_mib("X", 7, {}) == 7
    assert contracts.env_mib("X", 7, {"X": "  "}) == 7
    assert contracts.env_mib("X", 7, {"X": " \t\n"}) == 7
    assert contracts.env_mib("X", 7, {"X": " 640 "}) == 640
    assert contracts.env_mib("X", 7, {"X": "0640"}) == 640
    for bad in (*INVALID, "\u0661\u0662"):
        with pytest.raises(ValueError, match="positive whole number of MiB"):
            contracts.env_mib("X", 7, {"X": bad})


def test_job_caps_default_generically_and_follow_the_environment() -> None:
    assert contracts.job_memory_mib({}) == (
        contracts.GENERIC_JOB_MEMORY_HIGH_MIB,
        contracts.GENERIC_JOB_MEMORY_MAX_MIB,
    )
    env = {contracts.ENV_JOB_MEMORY_HIGH_MIB: "900", contracts.ENV_JOB_MEMORY_MAX_MIB: "1100"}
    assert contracts.job_memory_mib(env) == (900, 1100)


def test_generic_defaults_keep_high_below_max() -> None:
    assert contracts.GENERIC_JOB_MEMORY_HIGH_MIB < contracts.GENERIC_JOB_MEMORY_MAX_MIB
    assert contracts.GENERIC_MEMORY_HIGH_MIB < contracts.GENERIC_MEMORY_MAX_MIB


def _policy_bytes(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    code = (
        "import json; from scripts.lexicon.runner import contracts as c; "
        "print(json.dumps([c.DEFAULT_MEMORY_HIGH_BYTES, c.DEFAULT_MEMORY_MAX_BYTES]))"
    )
    return subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, timeout=60, check=False
    )


def test_policy_defaults_follow_the_environment_in_a_fresh_process() -> None:
    env = {**_clean_env(), contracts.ENV_MEMORY_HIGH_MIB: "3000", contracts.ENV_MEMORY_MAX_MIB: "3500"}
    out = _policy_bytes(env)
    assert out.returncode == 0, out.stderr
    assert json.loads(out.stdout) == [3000 * 1024**2, 3500 * 1024**2]
    out = _policy_bytes(_clean_env())
    assert json.loads(out.stdout) == [
        contracts.GENERIC_MEMORY_HIGH_MIB * 1024**2,
        contracts.GENERIC_MEMORY_MAX_MIB * 1024**2,
    ]


def test_invalid_policy_environment_is_refused_at_import() -> None:
    out = _policy_bytes({**_clean_env(), contracts.ENV_MEMORY_MAX_MIB: "0"})
    assert out.returncode != 0
    assert "positive whole number of MiB" in out.stderr


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launchers_carry_no_fixed_caps_and_forward_the_environment(launcher: str) -> None:
    text = (RUNNER / launcher).read_text(encoding="utf-8")
    assert re.search(r"--property=MemoryHigh=\d", text) is None
    assert re.search(r"--property=MemoryMax=\d", text) is None
    assert 'Environment=LU_LEXICON_JOB_MEMORY_HIGH_MIB="${JOB_MEMORY_HIGH_MIB}"' in text
    assert 'Environment=LU_LEXICON_JOB_MEMORY_MAX_MIB="${JOB_MEMORY_MAX_MIB}"' in text
    defaults = re.findall(r"\|\| JOB_MEMORY_(HIGH|MAX)_MIB=(\d+)\n", text)
    assert dict(defaults) == {
        "HIGH": str(contracts.GENERIC_JOB_MEMORY_HIGH_MIB),
        "MAX": str(contracts.GENERIC_JOB_MEMORY_MAX_MIB),
    }
    # Validation runs before any directory, PID file or unit is touched.
    assert text.index("_require_positive_mib LU_LEXICON_JOB_MEMORY_MAX_MIB") < text.index("mkdir -p")


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


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launchers_export_resolved_caps_for_unmanaged_children(launcher: str) -> None:
    text = (RUNNER / launcher).read_text(encoding="utf-8")
    start = text.index("_trim_mib() {")
    end = text.index("export LU_LEXICON_JOB_MEMORY_HIGH_MIB=")
    end = text.index("\n", end) + 1
    script = (
        text[start:end]
        + 'bash -c \'printf "%s %s" "$LU_LEXICON_JOB_MEMORY_HIGH_MIB" "$LU_LEXICON_JOB_MEMORY_MAX_MIB"\''
    )
    env = {**_clean_env(), contracts.ENV_JOB_MEMORY_HIGH_MIB: " 0900 "}
    out = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=10, check=True)
    assert out.stdout == f"900 {contracts.GENERIC_JOB_MEMORY_MAX_MIB}"


RESOLVERS = (enrich_offline_20k._resolve_job_memory_mib, reduce_ulif_20k._resolve_job_memory_mib)


@pytest.mark.parametrize("resolve", RESOLVERS)
def test_runner_cli_caps_follow_the_environment(resolve, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(contracts.ENV_JOB_MEMORY_HIGH_MIB, "900")
    monkeypatch.setenv(contracts.ENV_JOB_MEMORY_MAX_MIB, "1100")
    args = argparse.Namespace(memory_high_mib=None, memory_max_mib=None)
    resolve(args)
    assert (args.memory_high_mib, args.memory_max_mib) == (900, 1100)
    explicit = argparse.Namespace(memory_high_mib=700, memory_max_mib=800)
    resolve(explicit)
    assert (explicit.memory_high_mib, explicit.memory_max_mib) == (700, 800)


@pytest.mark.parametrize("resolve", RESOLVERS)
@pytest.mark.parametrize("bad", INVALID)
def test_runner_cli_refuses_invalid_environment(resolve, bad: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(contracts.ENV_JOB_MEMORY_HIGH_MIB, bad)
    with pytest.raises(ValueError, match="positive whole number of MiB"):
        resolve(argparse.Namespace(memory_high_mib=None, memory_max_mib=None))


@pytest.mark.parametrize("resolve", RESOLVERS)
@pytest.mark.parametrize("field", ("memory_high_mib", "memory_max_mib"))
@pytest.mark.parametrize("value", (0, -5))
def test_runner_cli_refuses_non_positive_flags(
    resolve, field: str, value: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(contracts.ENV_JOB_MEMORY_HIGH_MIB, raising=False)
    monkeypatch.delenv(contracts.ENV_JOB_MEMORY_MAX_MIB, raising=False)
    args = argparse.Namespace(memory_high_mib=None, memory_max_mib=None)
    setattr(args, field, value)
    with pytest.raises(SystemExit, match="positive whole number of MiB"):
        resolve(args)


def test_runner_clis_read_no_cap_environment_directly() -> None:
    for name in ("enrich_offline_20k.py", "reduce_ulif_20k.py"):
        text = (RUNNER / name).read_text(encoding="utf-8")
        assert "LU_LEXICON_JOB_MEMORY_" not in text, name


CAP_MODULES = (
    "contracts.py",
    "enrich_offline_20k.py",
    "fetch_ulif_20k.py",
    "memory.py",
    "offline_engine.py",
    "reduce_ulif_20k.py",
    "worker.py",
)


def test_runner_code_carries_no_fixed_cap_literals() -> None:
    for name in CAP_MODULES:
        path = RUNNER / name
        text = path.read_text(encoding="utf-8")
        assert re.search(r"MemoryPolicy\(high_bytes=\d", text) is None, path.name


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
