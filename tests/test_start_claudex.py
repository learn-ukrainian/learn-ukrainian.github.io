"""Behavior checks for the CLIProxyAPI-backed Claude Code launcher."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-claudex.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run_with_fakes(
    tmp_path: Path,
    arguments: list[str],
    env_overrides: dict[str, str] | None = None,
) -> str:
    home_bin = tmp_path / "home" / ".local" / "bin"
    home_bin.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        home_bin / "claude",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
    echo "test-claude"
    exit 0
fi
{
    printf 'base=%s\n' "$ANTHROPIC_BASE_URL"
    printf 'auth=%s\n' "$ANTHROPIC_AUTH_TOKEN"
    printf 'api_key=%s\n' "${ANTHROPIC_API_KEY-unset}"
    printf 'subagent=%s\n' "$CLAUDE_CODE_SUBAGENT_MODEL"
    printf 'effort=%s\n' "$CLAUDE_CODE_ALWAYS_ENABLE_EFFORT"
    printf 'concurrency=%s\n' "$CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY"
    printf 'tool_search=%s\n' "$ENABLE_TOOL_SEARCH"
    printf 'epic=%s\n' "${SESSION_EPIC:-}"
    printf 'arg=%s\n' "$@"
} > "$CLAUDEX_TEST_CAPTURE"
""",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "curl", "#!/usr/bin/env bash\nexit 0\n")
    _write_executable(fake_bin / "npm", "#!/usr/bin/env bash\nexit 0\n")

    env = os.environ.copy()
    for variable in (
        "ANTHROPIC_API_KEY",
        "CLAUDEX_BASE_URL",
        "CLAUDEX_AUTH_TOKEN",
        "CLAUDEX_SUBAGENT",
    ):
        env.pop(variable, None)
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CLAUDEX_TEST_CAPTURE": str(capture),
        }
    )
    env.update(env_overrides or {})
    result = subprocess.run(
        [
            str(_LAUNCHER),
            *arguments,
            "--epic",
            "harness",
            "--resume",
            "session-id",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    return capture.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], "gpt-5.6-sol"),
        (["--subagent", "sol"], "gpt-5.6-sol"),
        (["--subagent=terra"], "gpt-5.6-terra"),
        (["--subagent", "luna"], "gpt-5.6-luna"),
    ],
)
def test_routes_lead_and_subagent_models(tmp_path: Path, arguments: list[str], expected: str) -> None:
    output = _run_with_fakes(tmp_path, arguments)
    assert "base=http://127.0.0.1:8317" in output
    assert "auth=sk-dummy" in output
    assert "api_key=unset" in output
    assert f"subagent={expected}" in output
    assert "effort=1" in output
    assert "concurrency=3" in output
    assert "tool_search=false" in output
    assert "epic=harness" in output
    assert "arg=--model" in output
    assert "arg=gpt-5.6-sol" in output
    assert "arg=session-id" in output
    assert "arg=harness" not in output


def test_forwards_proxy_overrides_without_anthropic_api_key(tmp_path: Path) -> None:
    output = _run_with_fakes(
        tmp_path,
        [],
        {
            "ANTHROPIC_API_KEY": "must-be-unset",
            "CLAUDEX_BASE_URL": "https://proxy.example.com:8443/",
            "CLAUDEX_AUTH_TOKEN": "custom-token",
        },
    )

    assert "base=https://proxy.example.com:8443" in output
    assert "auth=custom-token" in output
    assert "api_key=unset" in output


def test_rejects_unknown_subagent() -> None:
    result = subprocess.run(
        [str(_LAUNCHER), "--subagent", "unknown"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "unsupported subagent" in result.stderr


def test_rejects_missing_subagent_value() -> None:
    result = subprocess.run(
        [str(_LAUNCHER), "--subagent"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "requires sol, terra, or luna" in result.stderr


@pytest.mark.parametrize("argument", ["--model", "--model=gpt-5.6-luna"])
def test_rejects_lead_model_override(argument: str) -> None:
    result = subprocess.run(
        [str(_LAUNCHER), argument],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "keeps the lead model on gpt-5.6-sol" in result.stderr


def test_reports_proxy_check_failure(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "curl", "#!/usr/bin/env bash\nexit 22\n")
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"

    result = subprocess.run(
        [str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "CLIProxyAPI check failed" in result.stderr


def test_reports_missing_curl(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    (fake_bin / "dirname").symlink_to("/usr/bin/dirname")
    env = os.environ.copy()
    env["PATH"] = str(fake_bin)

    result = subprocess.run(
        ["/bin/bash", str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "curl is required" in result.stderr


@pytest.mark.parametrize("argument", ["-h", "--help"])
def test_prints_launcher_help(argument: str) -> None:
    result = subprocess.run(
        [str(_LAUNCHER), argument],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "Usage: ./start-claudex.sh" in result.stdout
