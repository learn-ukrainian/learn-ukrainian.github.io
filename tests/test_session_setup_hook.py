"""Run the SessionStart-hook handoff-routing fixtures under the required pytest gate.

``scripts/audit/test_session_setup_hook.sh`` exercises the cold-start handoff
selection logic in ``agents_extensions/shared/hooks/session-setup.sh`` — including
the regression guard that ``SESSION_HANDOFF_AGENT`` routes each lane (e.g.
``claude`` vs ``claude-infra``) to its OWN ``.agent/<agent>-thread-handoff.md``
slot. The shell script was previously not wired into CI, so this thin wrapper
makes the guard load-bearing: it runs in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_session_setup_hook.sh"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_session_setup_hook_handoff_fixtures() -> None:
    assert _HOOK_TEST.is_file(), f"missing hook test: {_HOOK_TEST}"
    result = subprocess.run(
        ["bash", str(_HOOK_TEST)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"hook fixtures failed (rc={result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "ok - session setup hook handoff fixtures passed" in result.stdout


def test_legacy_table_parser_avoids_gnu_sed_anchor_escape() -> None:
    hook = _REPO_ROOT / "agents_extensions/shared/hooks/session-setup.sh"
    parser_line = next(
        line for line in hook.read_text(encoding="utf-8").splitlines()
        if "TABLE_BRIEF=$(sed -n" in line
    )

    assert "\\`" not in parser_line


def test_session_setup_drift_fp_regression(tmp_path: Path) -> None:
    import json
    import os

    # 1. Setup the project structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Create the minimal mock sources
    shared_dir = project_dir / "agents_extensions" / "shared"
    shared_dir.mkdir(parents=True)
    shared_rules = shared_dir / "rules"
    shared_rules.mkdir()

    # Create a rule file that is present in both
    (shared_rules / "pipeline.md").write_text("pipeline rule content", encoding="utf-8")
    # Create operator-expectations.md which is excluded from autoload
    (shared_rules / "operator-expectations.md").write_text("operator expectations content", encoding="utf-8")

    # Create the target directory .claude/
    claude_dir = project_dir / ".claude"
    claude_dir.mkdir()
    claude_rules = claude_dir / "rules"
    claude_rules.mkdir()

    # pipeline.md is deployed
    (claude_rules / "pipeline.md").write_text("pipeline rule content", encoding="utf-8")
    # operator-expectations.md is MISSING from .claude/rules/ by design (autoload exclude)

    # Create atlas-epic/ in .claude/
    atlas_epic = claude_dir / "atlas-epic"
    atlas_epic.mkdir()
    (atlas_epic / "CLAUDE-DRIVER-HANDOFF.md").write_text("driver handoff", encoding="utf-8")

    # Create .agent/canary-x.json
    agent_dir = project_dir / ".agent"
    agent_dir.mkdir()
    (agent_dir / "canary-x.json").write_text("{}", encoding="utf-8")

    # Mock other things to avoid unrelated warnings/issues
    venv_bin = project_dir / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("#!/bin/sh\necho 'Python 3.12.8'", encoding="utf-8")
    (venv_bin / "python").chmod(0o755)

    db_dir = project_dir / ".mcp" / "servers" / "message-broker"
    db_dir.mkdir(parents=True)
    (db_dir / "messages.db").write_text("dummy", encoding="utf-8")

    # Copy scripts/deploy_orphan_paths.sh to the project_dir
    scripts_dir = project_dir / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(_REPO_ROOT / "scripts" / "deploy_orphan_paths.sh", scripts_dir / "deploy_orphan_paths.sh")

    # Run the hook script
    hook_path = _REPO_ROOT / "agents_extensions" / "shared" / "hooks" / "session-setup.sh"

    # Environment variables
    isolated_home = tmp_path / "home"
    env = {
        "CLAUDE_PROJECT_DIR": str(project_dir),
        "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "32000",
        "HOME": str(isolated_home),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg-config"),
        "XDG_CACHE_HOME": str(tmp_path / "xdg-cache"),
        "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
        "XDG_STATE_HOME": str(tmp_path / "xdg-state"),
        "GH_CONFIG_DIR": str(tmp_path / "gh-config"),
        "PATH": f"{venv_bin}:{os.environ.get('PATH', '')}",
        "CODEX_CANONICAL_REPO_ROOT": str(project_dir),
        "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID": "native_claude",
        "CLAUDE_PROFILE_RESOLVER_SH": str(
            _REPO_ROOT / "scripts/lib/profile_resolver.sh"
        ),
        "CLAUDE_PROFILE_RESOLVER_PY": str(
            _REPO_ROOT / "scripts/lib/context_profiles.py"
        ),
        "CLAUDE_PROFILE_RESOLVER_PYTHON": str(_REPO_ROOT / ".venv/bin/python"),
        "CLAUDE_SESSION_RECORD_SCRIPT": str(
            _REPO_ROOT / "scripts/lib/session_record.py"
        ),
        "CLAUDE_SESSION_RECORD_PYTHON": str(_REPO_ROOT / ".venv/bin/python"),
    }

    result = subprocess.run(
        ["bash", str(hook_path)],
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"session-setup.sh failed: {result.stderr}\n{result.stdout}"

    try:
        output_data = json.loads(result.stdout)
        context = output_data.get("hookSpecificOutput", {}).get("additionalContext", "")
    except Exception as e:
        pytest.fail(f"Failed to parse JSON output: {e}\nStdout: {result.stdout}\nStderr: {result.stderr}")

    assert "DEPLOY DRIFT" not in context, f"False positive drift detected! Context:\n{context}"
