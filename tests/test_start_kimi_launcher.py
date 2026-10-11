"""Native Kimi launcher behavior after the interactive/driver split."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.kimi_hook_registration import config_path, ensure
from tests.rules_core_view import rules_core_absent_when_marked  # noqa: F401  (autouse: serves @rules_core_absent)
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def test_kimi_native_is_default_and_interactive_rejects_epic() -> None:
    interactive = run_launcher("start-kimi.sh")
    epic = run_launcher("start-kimi.sh", "--epic", "devops")
    assert interactive.returncode == 0, interactive.stderr
    # Catalog-resolved native id, never the bare alias (review finding, #5958 r3).
    # Operator 2026-08-13: the omitted-model default is k3-256k.
    assert "would exec kimi --model kimi-code/k3-256k" in interactive.stdout
    assert epic.returncode == 2
    assert "interactive launchers reject --epic" in epic.stderr


@pytest.mark.parametrize("harness", ("claude", "native", "agy"))
def test_kimi_rejects_harnesses_outside_native_or_claude_code(harness: str) -> None:
    result = run_launcher("start-kimi.sh", "--harness", harness)
    assert result.returncode == 2
    assert "kimi-code|claude-code" in result.stderr


@pytest.mark.rules_core_absent
def test_kimi_native_accepts_explicit_model_and_provider_arguments() -> None:
    result = run_launcher("start-kimi.sh", "--model", "k3", "--", "--yolo")
    assert result.returncode == 0, result.stderr
    assert "would exec kimi --model kimi-code/k3 --yolo" in result.stdout


def test_kimi_native_rejects_unknown_alias_via_catalog() -> None:
    """Review finding on #5958 r3: the native branch must resolve aliases through
    the catalog and refuse unknown ones (bare aliases are rejected by the CLI)."""
    result = run_launcher("start-kimi.sh", "--model", "not-a-kimi-model")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unknown --model" in (result.stdout + result.stderr)


def test_kimi_claude_code_requires_a_kimi_credential_in_noninteractive_dry_run(tmp_path) -> None:
    result = run_launcher(
        "start-kimi.sh",
        "--harness",
        "claude-code",
        env={
            "HOME": str(tmp_path / "home"),
            "KIMICC_AUTH_TOKEN": "",
            "MOONSHOT_API_KEY": "",
            "KIMI_API_KEY": "",
        },
    )
    assert result.returncode == 3
    assert "no Kimi API credential" in result.stderr


def test_kimi_rejects_unknown_launcher_flag_with_usage_exit() -> None:
    result = run_launcher("start-kimi.sh", "--not-a-real-flag")
    assert result.returncode == 2
    assert "run --help" in result.stderr


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("KIMI_CODE_HOME", str(tmp_path / "kimi-home"))


@pytest.mark.parametrize("state", ["absent", "stale", "malformed", "correct"])
@pytest.mark.parametrize("gate", ["preflight", "exec"])
def test_native_launcher_exec_checks_registration_with_explicit_environment(tmp_path, state, gate):
    env = {
        "HOME": str(tmp_path / "home"),
        "KIMI_CODE_HOME": str(tmp_path / "kimi-home"),
        "PATH": f"{tmp_path / 'bin'}{os.pathsep}{os.defpath}",
        "LC_ROOT": str(Path(__file__).resolve().parents[1]),
        "LC_HARNESS": "kimi-code",
        "LC_DRY_RUN": "0",
        "LC_MODEL": "k3-256k",
        "PROJECT_TEST_PYTHON": sys.executable,
    }
    binary = tmp_path / "bin/kimi"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nprintf 'native-child-ran\\n'\n")
    binary.chmod(0o700)
    path = config_path("launcher", env)
    if state != "absent":
        ensure("launcher", env)
        if state == "stale":
            path.write_bytes(path.read_bytes().replace(b"timeout = 10", b"timeout = 11"))
        elif state == "malformed":
            path.write_bytes(b'value = "private fixture"\n[broken')
    before = path.read_bytes() if path.exists() else None
    script = """
source "$LC_ROOT/scripts/launchers/kimi.sh"
launcher_project_python() { printf '%s\\n' "$PROJECT_TEST_PYTHON"; }
launcher_require_binary() { command -v "$1" >/dev/null; }
launcher_error() { printf '%s\\n' "$1" >&2; }
LC_FORWARD_ARGS=()
"""
    if gate == "preflight":
        script += "launcher_adapter_preflight\n"
    script += "launcher_adapter_exec\n"
    result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == (0 if state == "correct" else 3), result.stdout + result.stderr
    assert ("native-child-ran" in result.stdout) == (state == "correct")
    if state != "correct":
        assert "ensure" in result.stderr and "npm run agents:deploy" in result.stderr
    assert "private fixture" not in result.stdout + result.stderr
    assert (path.read_bytes() if path.exists() else None) == before


def test_claude_code_exec_does_not_require_native_registration(tmp_path):
    binary = tmp_path / "bin/claude"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nprintf 'claude-child-ran\\n'\n")
    binary.chmod(0o700)
    env = {
        "HOME": str(tmp_path / "home"),
        "KIMI_CODE_HOME": str(tmp_path / "kimi-home"),
        "PATH": f"{binary.parent}{os.pathsep}{os.defpath}",
        "LC_ROOT": str(Path(__file__).resolve().parents[1]),
        "LC_HARNESS": "claude-code",
        "LC_DRY_RUN": "0",
        "LEAD_MODEL": "synthetic-model",
    }
    result = subprocess.run(
        [
            "bash",
            "-c",
            """
source "$LC_ROOT/scripts/launchers/kimi.sh"
LC_FORWARD_ARGS=()
launcher_adapter_exec
""",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "claude-child-ran\n"
    assert not config_path("launcher", env).exists()
