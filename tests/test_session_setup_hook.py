"""Run the SessionStart-hook handoff-routing fixtures under the required pytest gate.

``scripts/audit/test_session_setup_hook.sh`` exercises the cold-start handoff
selection logic in ``agents_extensions/shared/hooks/session-setup.sh`` — including
the regression guard that ``SESSION_HANDOFF_AGENT`` routes each lane (e.g.
``claude`` vs ``claude-infra``) to its OWN ``.agent/<agent>-thread-handoff.md``
slot. The shell script was previously not wired into CI, so this thin wrapper
makes the guard load-bearing: it runs in the required ``Test (pytest)`` job.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HOOK_TEST = _REPO_ROOT / "scripts" / "audit" / "test_session_setup_hook.sh"


def _canonical_python() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
        text=True, timeout=30,
    )
    return Path(result.stdout.strip()).parent / ".venv" / "bin" / "python"


def _stream_id_from_registry(stream_key: str) -> str:
    registry = yaml.safe_load(
        (_REPO_ROOT / "scripts/config/issue_streams.yaml").read_text(encoding="utf-8")
    )
    epic = registry["streams"][stream_key]["epics"][0]
    return f"epic:{epic}"


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
@pytest.mark.slow
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


def test_session_setup_renders_remote_epic_state_and_fails_open(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    subprocess.run(["git", "init", "-q", str(project_dir)], check=True, timeout=30)

    monitor_stream_id = _stream_id_from_registry("monitor")

    fake_python = project_dir / ".venv" / "bin" / "python"
    fake_python.parent.mkdir(parents=True)
    fake_python.write_text("#!/bin/sh\nprintf 'Python 3.12.8\\n'\n", encoding="utf-8")
    fake_python.chmod(0o755)
    (project_dir / ".python-version").write_text("3.12.8\n", encoding="utf-8")

    remote_payload = {
        "schema": "remote-epic-lifecycle.v1",
        "stream_id": monitor_stream_id,
        "lease": {
            "state": "active",
            "holder": {
                "agent": "remote-agent",
                "harness": "remote-harness",
                "host_id": "host-job",
            },
        },
        "digest": {
            "pinned": [
                {
                    "entry_id": 2,
                    "type": "state",
                    "body": "remote state from handoff",
                }
            ],
            "recent": [
                {
                    "entry_id": 3,
                    "type": "next_action",
                    "body": "claim remote lease",
                }
            ],
        },
    }
    requested_paths: list[str] = []
    return_non_200 = False

    class RemoteEpicHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requested_paths.append(self.path)
            if return_non_200:
                self.send_response(503)
                self.end_headers()
                return
            if self.path != f"/api/epics/v1/{monitor_stream_id}":
                self.send_response(404)
                self.end_headers()
                return
            body = json.dumps(remote_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), RemoteEpicHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    hook = _REPO_ROOT / "agents_extensions/shared/hooks/session-setup.sh"
    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": str(project_dir),
            "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "32000",
            "HOME": str(tmp_path / "home"),
            "XDG_CONFIG_HOME": str(tmp_path / "xdg-config"),
            "XDG_CACHE_HOME": str(tmp_path / "xdg-cache"),
            "XDG_DATA_HOME": str(tmp_path / "xdg-data"),
            "XDG_STATE_HOME": str(tmp_path / "xdg-state"),
            "GH_CONFIG_DIR": str(tmp_path / "gh-config"),
            "CODEX_THREAD_ID": "remote-epic-session",
            "CODEX_CANONICAL_REPO_ROOT": str(project_dir),
            "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID": "native_claude",
            "CLAUDE_PROFILE_RESOLVER_SH": str(_REPO_ROOT / "scripts/lib/profile_resolver.sh"),
            "CLAUDE_PROFILE_RESOLVER_PY": str(_REPO_ROOT / "scripts/lib/context_profiles.py"),
            "CLAUDE_PROFILE_RESOLVER_PYTHON": str(_canonical_python()),
            "CLAUDE_SESSION_RECORD_PYTHON": str(fake_python),
            "SESSION_BOUNDED_RUNNER": str(_REPO_ROOT / "scripts/agent_runtime/bounded_command.py"),
            "CLAUDE_HANDOFF_IDENTITY_SH": str(_REPO_ROOT / "scripts/lib/handoff_identity.sh"),
            "THREAD_ROLLOVER_PYTHON": str(fake_python),
            "THREAD_ROLLOVER_SCRIPT": str(_REPO_ROOT / "scripts/orchestration/thread_handoff.py"),
            "SESSION_HANDOFF_AGENT": "claude",
            "SESSION_EPIC": "monitor",
            "LU_MONITOR_LOOPBACK": f"http://127.0.0.1:{server.server_port}",
        }
    )

    def run_hook(loopback: str) -> tuple[subprocess.CompletedProcess[str], str]:
        run_env = {**env, "LU_MONITOR_LOOPBACK": loopback}
        result = subprocess.run(
            ["bash", str(hook)],
            input="",
            cwd=_REPO_ROOT,
            env=run_env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        return result, context

    try:
        result, context = run_hook(env["LU_MONITOR_LOOPBACK"])
        assert result.returncode == 0, result.stderr
        assert f"/api/epics/v1/{monitor_stream_id}" in requested_paths
        assert "REMOTE EPIC STATE (Monitor API)" in context
        assert f"Stream: {monitor_stream_id}" in context
        assert "Holder: remote-agent · remote-harness · host-job" in context
        assert "Lease: active" in context
        assert "Latest state: remote state from handoff" in context
        assert "Latest next action: claim remote lease" in context
        assert str(project_dir) not in context

        return_non_200 = True
        unavailable_result, unavailable_context = run_hook(env["LU_MONITOR_LOOPBACK"])
        assert unavailable_result.returncode == 0, unavailable_result.stderr
        assert "REMOTE EPIC STATE (Monitor API)" not in unavailable_context

        dead_result, dead_context = run_hook("http://127.0.0.1:1")
        assert dead_result.returncode == 0, dead_result.stderr
        assert "REMOTE EPIC STATE (Monitor API)" not in dead_context
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_session_setup_reports_machine_repairs_without_applying_them(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    subprocess.run(["git", "init", "-q", str(project)], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(project), "config", "--local", "core.bare", "true"],
        check=True,
        timeout=30,
    )

    pyenv_root = tmp_path / "pyenv"
    lock = pyenv_root / "shims" / ".pyenv-shim"
    lock.parent.mkdir(parents=True)
    lock.write_text("", encoding="utf-8")
    old = time.time() - 180
    lock.touch()
    os.utime(lock, (old, old))

    node_modules = project / "node_modules"
    node_modules.symlink_to(node_modules)
    env = os.environ.copy()
    env.update(
        {
            "CLAUDE_PROJECT_DIR": str(project),
            "CLAUDE_NON_INTERACTIVE": "1",
            "PYENV_ROOT": str(pyenv_root),
        }
    )

    result = subprocess.run(
        ["bash", str(_REPO_ROOT / "agents_extensions/shared/hooks/session-setup.sh")],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert lock.is_file(), "startup must not delete a heuristic-age pyenv lock"
    assert node_modules.is_symlink(), "startup must not remove machine state"
    core_bare = subprocess.run(
        ["git", "-C", str(project), "config", "--get", "core.bare"],
        capture_output=True,
        check=True,
        text=True,
        timeout=30,
    )
    assert core_bare.stdout.strip() == "false", "core.bare is the bounded repair exception"
    assert "inspect it" in result.stderr
    assert "check_self_symlinks.py --fix" in result.stderr


def test_session_setup_drift_fp_regression(tmp_path: Path) -> None:
    import json

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

    # Linked worktrees do not have a local venv: SessionStart must resolve the
    # canonical checkout interpreter and exact pin instead.
    canonical_dir = tmp_path / "canonical"
    canonical_dir.mkdir()
    venv_bin = canonical_dir / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").write_text("#!/bin/sh\necho 'Python 3.12.8'", encoding="utf-8")
    (venv_bin / "python").chmod(0o755)
    (canonical_dir / ".python-version").write_text("3.12.8\n", encoding="utf-8")

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
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "CODEX_CANONICAL_REPO_ROOT": str(canonical_dir),
        "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID": "native_claude",
        "CLAUDE_PROFILE_RESOLVER_SH": str(
            _REPO_ROOT / "scripts/lib/profile_resolver.sh"
        ),
        "CLAUDE_PROFILE_RESOLVER_PY": str(
            _REPO_ROOT / "scripts/lib/context_profiles.py"
        ),
        "CLAUDE_PROFILE_RESOLVER_PYTHON": str(_canonical_python()),
        "CLAUDE_SESSION_RECORD_SCRIPT": str(
            _REPO_ROOT / "scripts/lib/session_record.py"
        ),
        "CLAUDE_SESSION_RECORD_PYTHON": str(_canonical_python()),
        "SESSION_BOUNDED_RUNNER": str(
            _REPO_ROOT / "scripts" / "agent_runtime" / "bounded_command.py"
        ),
    }

    result = subprocess.run(
        ["bash", str(hook_path)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"session-setup.sh failed: {result.stderr}\n{result.stdout}"

    try:
        output_data = json.loads(result.stdout)
        context = output_data.get("hookSpecificOutput", {}).get("additionalContext", "")
    except Exception as e:
        pytest.fail(f"Failed to parse JSON output: {e}\nStdout: {result.stdout}\nStderr: {result.stderr}")

    assert "DEPLOY DRIFT" not in context, f"False positive drift detected! Context:\n{context}"
    assert "VENV MISSING" not in context
    assert "VENV WRONG PYTHON" not in context
