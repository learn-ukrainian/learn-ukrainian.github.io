"""Tests for scripts/safe_env.sh — the leak-proof environment probe (#1896, #M-5).

The load-bearing guarantee is negative: a variable's *value* must never appear
in stdout or stderr, regardless of subcommand. These tests set a sentinel
"secret" value and assert it is absent from all output.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "safe_env.sh"
SENTINEL = "S3CR3T_do_not_leak_8f3c1d_sentinel_value"


def _run(args: list[str], env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_script_exists_and_executable():
    assert SCRIPT.exists(), f"missing {SCRIPT}"
    assert os.access(SCRIPT, os.X_OK), f"{SCRIPT} is not executable (chmod +x)"


def test_check_reports_set_without_leaking_value():
    res = _run(["check", "SAFE_ENV_SENTINEL"], {"SAFE_ENV_SENTINEL": SENTINEL})
    assert res.returncode == 0
    assert "SAFE_ENV_SENTINEL: SET" in res.stdout
    # The load-bearing assertion: value must never appear in any stream.
    assert SENTINEL not in res.stdout
    assert SENTINEL not in res.stderr


def test_check_reports_unset_for_absent_var():
    env = {k: v for k, v in os.environ.items() if k != "SAFE_ENV_DEFINITELY_ABSENT"}
    res = subprocess.run(
        ["bash", str(SCRIPT), "check", "SAFE_ENV_DEFINITELY_ABSENT"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 1
    assert "SAFE_ENV_DEFINITELY_ABSENT: UNSET" in res.stdout


def test_empty_var_counts_as_unset():
    res = _run(["check", "SAFE_ENV_EMPTY"], {"SAFE_ENV_EMPTY": ""})
    assert res.returncode == 1
    assert "SAFE_ENV_EMPTY: UNSET" in res.stdout


def test_is_set_is_silent_and_uses_exit_code():
    set_res = _run(["is-set", "SAFE_ENV_SENTINEL"], {"SAFE_ENV_SENTINEL": SENTINEL})
    assert set_res.returncode == 0
    assert set_res.stdout.strip() == ""
    assert SENTINEL not in set_res.stdout
    assert SENTINEL not in set_res.stderr

    unset_res = subprocess.run(
        ["bash", str(SCRIPT), "is-set", "SAFE_ENV_DEFINITELY_ABSENT"],
        capture_output=True,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "SAFE_ENV_DEFINITELY_ABSENT"},
    )
    assert unset_res.returncode == 1


def test_count_reports_ratio_without_names_or_values():
    res = _run(
        ["count", "SAFE_ENV_SENTINEL", "SAFE_ENV_DEFINITELY_ABSENT"],
        {"SAFE_ENV_SENTINEL": SENTINEL},
    )
    assert "1/2 set" in res.stdout
    assert res.returncode == 1  # not all set
    assert SENTINEL not in res.stdout
    assert SENTINEL not in res.stderr


@pytest.mark.parametrize("subcmd", ["check", "is-set", "count"])
def test_missing_arg_exits_2(subcmd):
    res = _run([subcmd])
    assert res.returncode == 2


def test_unknown_command_exits_2():
    res = _run(["frobnicate", "VAR"])
    assert res.returncode == 2


def test_help_does_not_require_args():
    res = _run(["--help"])
    assert res.returncode == 0
    assert "safe_env.sh" in res.stdout
