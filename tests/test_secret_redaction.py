"""Secret redaction for config repr, child envs, and the no-print hook.

The live helper and the agent hook live in learn-ukrainian/learn-ukrainian.github.io.
These tests use synthetic values only.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime.env_sanitize import (
    CAPTURED_SECRET_MIN_LENGTH,
    credential_env_names,
    unneeded_secret_names,
    without_unneeded_secrets,
)

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "agents_extensions/shared/hooks/guard-secret-print.py"
SYNTHETIC_KEY = "synthetic-cursor-key-0123456789"


def test_github_identity_token_is_omitted_from_repr() -> None:
    from agent_runtime.agent_github_identity import GitHubIdentity

    identity = GitHubIdentity(token=SYNTHETIC_KEY, source="test")
    rendered = repr(identity)
    assert SYNTHETIC_KEY not in rendered
    assert "token" not in rendered
    assert identity.token == SYNTHETIC_KEY


def test_unneeded_secret_names_drop_cursor_key_except_for_cursor() -> None:
    env = {
        "CURSOR_API_KEY": SYNTHETIC_KEY,
        "OPENAI_API_KEY": "synthetic-openai-key-0123456789",
        "GH_TOKEN": "ghp_synthetic",
        "PATH": "/usr/bin",
    }
    assert unneeded_secret_names(env, "claude") == ["CURSOR_API_KEY", "OPENAI_API_KEY"]
    assert unneeded_secret_names(env, "cursor") == ["OPENAI_API_KEY"]
    assert unneeded_secret_names(env, "codex") == ["CURSOR_API_KEY"]
    assert unneeded_secret_names(env, "dispatcher") == ["CURSOR_API_KEY", "OPENAI_API_KEY"]
    kept = without_unneeded_secrets(env, "cursor")
    assert kept["CURSOR_API_KEY"] == SYNTHETIC_KEY
    assert "OPENAI_API_KEY" not in kept
    assert kept["GH_TOKEN"] == "ghp_synthetic"


def test_conftest_keeps_harness_and_later_tokens() -> None:
    from tests.conftest import _INHERITED_CREDENTIAL_NAMES, inherited_credential_names

    env = {
        "CURSOR_API_KEY": SYNTHETIC_KEY,
        "LU_TEST_CURSOR_SESSION_TOKEN": "synthetic-session-token-0123456789",
        "AGENT_MONITOR_TOKEN": "test-agent-monitor-token-5652",
        "PATH": "/usr/bin",
    }
    assert inherited_credential_names(env) == ("CURSOR_API_KEY", "AGENT_MONITOR_TOKEN")
    assert not any(name.startswith("LU_TEST_") for name in _INHERITED_CREDENTIAL_NAMES)


def test_credential_env_names_keep_session_identity() -> None:
    env = {
        "CURSOR_API_KEY": SYNTHETIC_KEY,
        "GITHUB_TOKEN": "ghp_synthetic",
        "SESSION_STREAM_FENCING_TOKEN": "fence",
        "PATH": "/usr/bin",
    }
    names = credential_env_names(env, keep={"SESSION_STREAM_FENCING_TOKEN"})
    assert names == ["CURSOR_API_KEY", "GITHUB_TOKEN"]
    assert CAPTURED_SECRET_MIN_LENGTH >= 8


def test_launchers_and_dispatcher_call_the_sanitizer() -> None:
    launcher = (REPO / "scripts/lib/launcher_core.sh").read_text(encoding="utf-8")
    assert "launcher_drop_unneeded_secrets" in launcher
    assert "env_sanitize.py" in launcher
    assert '--provider "$LC_PROVIDER"' in launcher
    delegate = (REPO / "scripts/delegate.py").read_text(encoding="utf-8")
    assert "without_unneeded_secrets(worker_env, dispatch_agent)" in delegate
    dispatcher = (REPO / "scripts/batch/batch_dispatcher.py").read_text(encoding="utf-8")
    assert "unneeded_secret_names(os.environ, \"dispatcher\")" in dispatcher
    wrapper = (REPO / "run-dispatcher.sh").read_text(encoding="utf-8")
    assert "--provider dispatcher" in wrapper
    for name in ("kimi.sh", "glm.sh"):
        launcher_text = (REPO / "scripts" / "launchers" / name).read_text(encoding="utf-8")
        assert "launcher_drop_unneeded_secrets" in launcher_text


def test_no_print_hook_blocks_seeded_echo() -> None:
    proc = subprocess.run(
        [sys.executable, str(HOOK), "--self-test"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    assert SYNTHETIC_KEY not in proc.stdout
    assert SYNTHETIC_KEY not in proc.stderr


def test_conftest_scrubs_api_keys_and_fails_when_output_contains_one() -> None:
    import shutil
    import uuid

    scratch = REPO / "tests" / f"_secret_redaction_scratch_{uuid.uuid4().hex}"
    scratch.mkdir()
    sample = scratch / "test_sample.py"
    secret_file = scratch / "sample.txt"
    other_key = "synthetic-openai-key-0123456789"
    secret_file.write_text(SYNTHETIC_KEY + "\n" + other_key, encoding="utf-8")
    sample.write_text(
        "import os\n"
        "from pathlib import Path\n"
        "def test_api_key_is_absent():\n"
        "    assert 'CURSOR_API_KEY' not in os.environ\n"
        "    assert 'OPENAI_API_KEY' not in os.environ\n"
        "def test_prints_the_parent_key():\n"
        f"    print(Path({str(secret_file)!r}).read_text())\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["CURSOR_API_KEY"] = SYNTHETIC_KEY
    env["OPENAI_API_KEY"] = other_key
    env["GITHUB_TOKEN"] = "synthetic-github-token-0123456789"
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                str(sample),
                "-p",
                "no:cacheprovider",
                "--override-ini",
                "addopts=-q --tb=line",
                "-p",
                "no:xdist",
            ],
            cwd=REPO,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    combined = proc.stdout + proc.stderr
    assert "1 passed" in combined
    assert SYNTHETIC_KEY not in combined
    assert other_key not in combined
    assert "synthetic-github-token-0123456789" not in combined
    assert proc.returncode != 0
    assert "scrubbed env var" in combined
    assert "CURSOR_API_KEY" in combined
    assert "OPENAI_API_KEY" in combined


def test_launcher_unsets_unneeded_api_key_and_fails_closed(tmp_path: Path) -> None:
    helper = tmp_path / "primary"
    python = helper / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n", encoding="utf-8")
    python.chmod(0o755)
    core = REPO / "scripts/lib/launcher_core.sh"
    clear = f"""
set -euo pipefail
export LC_PROVIDER=claude LC_MODE=interactive LC_DRY_RUN=0
export LC_ROOT={shlex.quote(str(REPO))}
export LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper))}
export CURSOR_API_KEY={shlex.quote(SYNTHETIC_KEY)}
source {shlex.quote(str(core))}
launcher_drop_unneeded_secrets
if [ -n "${{CURSOR_API_KEY:-}}" ]; then
  printf 'still-set\\n'
  exit 2
fi
printf 'cleared\\n'
"""
    cleared = subprocess.run(
        ["bash", "-c", clear],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert cleared.returncode == 0, cleared.stderr
    assert cleared.stdout.strip() == "cleared"
    assert SYNTHETIC_KEY not in cleared.stdout + cleared.stderr

    python.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    marker = tmp_path / "provider-started"
    refuse = f"""
set -euo pipefail
export LC_PROVIDER=claude LC_MODE=interactive LC_DRY_RUN=0
export LC_ROOT={shlex.quote(str(REPO))}
export LC_DURABLE_HELPER_ROOT={shlex.quote(str(helper))}
source {shlex.quote(str(core))}
launcher_exec_command touch {shlex.quote(str(marker))}
"""
    refused = subprocess.run(
        ["bash", "-c", refuse],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert refused.returncode != 0
    assert not marker.exists()
    assert "could not drop unneeded API keys" in refused.stderr


@pytest.mark.parametrize(
    "command",
    ["cat ~/.secrets/*", "env | grep KEY", "printenv *_KEY"],
)
def test_seeded_commands_are_blocked_by_the_hook(command: str) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("guard_secret_print_redaction", HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._scan_command(command, set())
