"""Lexicon runner memory caps come from configuration, with generic defaults."""

from __future__ import annotations

import importlib
import os
import re
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


def test_env_mib_reads_a_positive_whole_number_or_the_default() -> None:
    assert contracts.env_mib("X", 7, {}) == 7
    assert contracts.env_mib("X", 7, {"X": "  "}) == 7
    assert contracts.env_mib("X", 7, {"X": " 640 "}) == 640
    for bad in ("0", "-1", "1.5", "1G", "lots"):
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


def test_policy_defaults_follow_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(contracts.ENV_MEMORY_HIGH_MIB, "3000")
    monkeypatch.setenv(contracts.ENV_MEMORY_MAX_MIB, "3500")
    try:
        reloaded = importlib.reload(contracts)
        assert reloaded.DEFAULT_MEMORY_HIGH_BYTES == 3000 * 1024**2
        assert reloaded.DEFAULT_MEMORY_MAX_BYTES == 3500 * 1024**2
    finally:
        monkeypatch.delenv(contracts.ENV_MEMORY_HIGH_MIB)
        monkeypatch.delenv(contracts.ENV_MEMORY_MAX_MIB)
        importlib.reload(contracts)


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launchers_take_job_caps_from_the_environment_with_the_generic_defaults(launcher: str) -> None:
    text = (RUNNER / launcher).read_text(encoding="utf-8")
    assert re.search(r"--property=MemoryHigh=\d", text) is None
    assert re.search(r"--property=MemoryMax=\d", text) is None
    assert 'MemoryHigh="${JOB_MEMORY_HIGH_MIB}M"' in text
    assert 'MemoryMax="${JOB_MEMORY_MAX_MIB}M"' in text
    high = re.search(r'^JOB_MEMORY_HIGH_MIB="\$\{LU_LEXICON_JOB_MEMORY_HIGH_MIB:-(\d+)\}"$', text, re.M)
    cap = re.search(r'^JOB_MEMORY_MAX_MIB="\$\{LU_LEXICON_JOB_MEMORY_MAX_MIB:-(\d+)\}"$', text, re.M)
    assert high and int(high.group(1)) == contracts.GENERIC_JOB_MEMORY_HIGH_MIB
    assert cap and int(cap.group(1)) == contracts.GENERIC_JOB_MEMORY_MAX_MIB


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_launcher_cap_variables_resolve_from_env_or_default(launcher: str) -> None:
    text = (RUNNER / launcher).read_text(encoding="utf-8")
    block = "\n".join(line for line in text.splitlines() if line.startswith("JOB_MEMORY_"))
    script = block + '\nprintf "%s %s" "$JOB_MEMORY_HIGH_MIB" "$JOB_MEMORY_MAX_MIB"'
    clean = {k: v for k, v in os.environ.items() if k not in ENV_NAMES}
    out = subprocess.run(["bash", "-c", script], env=clean, capture_output=True, text=True, timeout=10, check=True)
    assert out.stdout == f"{contracts.GENERIC_JOB_MEMORY_HIGH_MIB} {contracts.GENERIC_JOB_MEMORY_MAX_MIB}"
    env = {**clean, contracts.ENV_JOB_MEMORY_HIGH_MIB: "900", contracts.ENV_JOB_MEMORY_MAX_MIB: "1100"}
    out = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=10, check=True)
    assert out.stdout == "900 1100"


@pytest.mark.parametrize(
    ("module", "pattern"),
    [
        ("enrich_offline_20k.py", r'"LU_LEXICON_JOB_MEMORY_(HIGH|MAX)_MIB", ""\)\.strip\(\) or (\d+)\)'),
        ("reduce_ulif_20k.py", r'"LU_LEXICON_JOB_MEMORY_(HIGH|MAX)_MIB", ""\)\.strip\(\) or (\d+)\)'),
    ],
)
def test_runner_cli_defaults_match_the_generic_job_caps(module: str, pattern: str) -> None:
    found = dict(re.findall(pattern, (RUNNER / module).read_text(encoding="utf-8")))
    assert found == {
        "HIGH": str(contracts.GENERIC_JOB_MEMORY_HIGH_MIB),
        "MAX": str(contracts.GENERIC_JOB_MEMORY_MAX_MIB),
    }


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
