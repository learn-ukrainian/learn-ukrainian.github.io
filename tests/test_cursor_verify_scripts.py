"""Cursor script regressions and offline checks of the npm install policy."""

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "agents_extensions/cursor/skills/verify-learn-ukrainian"


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "repo"
    scripts = root / ".cursor/skills/verify-learn-ukrainian/bin"
    shutil.copytree(SKILL / "bin", scripts)
    (root / "site/node_modules").mkdir(parents=True)
    commands = tmp_path / "commands"
    commands.mkdir()
    env = os.environ.copy()
    for key in tuple(env):
        if key.startswith("LU_VERIFY_"):
            env.pop(key)
    env.update(
        PATH=f"{commands}:/usr/bin:/bin",
        TMPDIR=str(tmp_path),
        LU_VERIFY_PYTHON=sys.executable,
        LU_VERIFY_STATE_DIR=str(tmp_path / "lu-verify-test"),
        LU_VERIFY_EVIDENCE_DIR=str(tmp_path / "evidence"),
    )
    return root, scripts, commands, env


def command(commands, name, body):
    path = commands / name
    path.write_text("#!/bin/bash\nset -euo pipefail\n" + body + "\n")
    path.chmod(0o755)
    return path


def run(sandbox, name, *args):
    root, scripts, _, env = sandbox
    return subprocess.run(
        ["/bin/bash", str(scripts / name), *args],
        cwd=root, env=env, text=True, capture_output=True, timeout=15,
    )


def test_launch_propagates_npm_ci_refusal(sandbox):
    root, _, commands, _ = sandbox
    (root / "site/node_modules").rmdir()
    command(commands, "curl", "exit 1")
    command(commands, "npm", '[[ "$PWD" == */site && "$*" == ci ]]; echo "npm error code EBADENGINE" >&2; exit 42')
    result = run(sandbox, "launch.sh", "dev")
    assert result.returncode == 42
    assert "npm error code EBADENGINE" in result.stderr


def test_npm_refuses_wrong_engine_for_both_projects(tmp_path):
    npm = shutil.which("npm")
    node = shutil.which("node")
    if npm is None or node is None:
        pytest.skip("real Node and npm are required for the npm CLI offline check")
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path),
        "npm_config_cache": str(tmp_path / "cache"),
        "npm_config_userconfig": str(tmp_path / "user.npmrc"),
        "npm_config_globalconfig": str(tmp_path / "global.npmrc"),
    }
    node_version = subprocess.check_output([node, "--version"], env=env, text=True, timeout=15).strip()
    pins = json.loads((ROOT / "package.json").read_text())["engines"]
    assert pins["node"] == (ROOT / ".nvmrc").read_text().strip()
    for name, source in (("root", ROOT), ("site", ROOT / "site")):
        assert json.loads((source / "package.json").read_text())["engines"] == pins
        project = tmp_path / name
        project.mkdir()
        shutil.copyfile(source / ".npmrc", project / ".npmrc")
        # A dependency-free copy of the install policy isolates the npm mismatch.
        package = {
            "name": "engine-probe",
            "version": "1.0.0",
            "engines": {"node": node_version, "npm": "0.0.0"},
        }
        (project / "package.json").write_text(json.dumps(package))
        (project / "package-lock.json").write_text(json.dumps({
            "name": package["name"],
            "version": package["version"],
            "lockfileVersion": 3,
            "packages": {"": package},
        }))
        for action in ("ci", "install"):
            result = subprocess.run(
                [npm, action, "--offline", "--no-audit", "--no-fund"],
                cwd=project, env=env, text=True, capture_output=True, timeout=15,
            )
            assert result.returncode != 0, f"{name}: npm {action} accepted the wrong npm version"
            assert "EBADENGINE" in result.stderr, result.stderr


@pytest.mark.parametrize("script", ["launch.sh", "cleanup.sh"])
@pytest.mark.parametrize("unsafe", ["root", "temp-root", "traversal", "nested", "symlink", "symlink-slash"])
def test_unsafe_state_is_rejected_before_side_effects(sandbox, script, unsafe):
    _, _, _, env = sandbox
    temp = Path(env["TMPDIR"])
    target = temp / "keep"
    target.mkdir()
    marker = target / "sentinel"
    marker.write_text("keep")
    link = temp / "lu-verify-link"
    link.symlink_to(target, target_is_directory=True)
    paths = {
        "root": "/", "temp-root": str(temp),
        "traversal": str(temp / "lu-verify-x/../keep"),
        "nested": str(temp / "lu-verify-x/lu-verify-y"),
        "symlink": str(link), "symlink-slash": str(link) + "/",
    }
    env["LU_VERIFY_STATE_DIR"] = paths[unsafe]
    result = run(sandbox, script)
    assert result.returncode == 1
    assert "unsafe state directory" in result.stderr
    assert marker.read_text() == "keep"
    assert not Path(env["LU_VERIFY_EVIDENCE_DIR"]).exists()


@pytest.mark.parametrize("script", ["launch.sh", "doctor.sh", "cleanup.sh", "drive-playwright.sh", "run-checks.sh"])
def test_help_has_no_side_effects(sandbox, script):
    _, _, _, env = sandbox
    result = run(sandbox, script, "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "Inputs:" in result.stdout
    assert "Outputs:" in result.stdout
    assert "Exit:" in result.stdout
    assert not Path(env["LU_VERIFY_STATE_DIR"]).exists()
    assert not Path(env["LU_VERIFY_EVIDENCE_DIR"]).exists()


def test_cleanup_preserves_evidence(sandbox):
    _, _, _, env = sandbox
    state = Path(env["LU_VERIFY_STATE_DIR"])
    state.mkdir()
    (state / "site.log").write_text("scratch")
    evidence = Path(env["LU_VERIFY_EVIDENCE_DIR"])
    evidence.mkdir()
    (evidence / "proof").write_text("retained")
    result = run(sandbox, "cleanup.sh")
    assert result.returncode == 0, result.stderr
    assert not state.exists()
    assert (evidence / "proof").read_text() == "retained"


@pytest.mark.parametrize("foreign", [False, True])
def test_doctor_checks_real_child_listener_group(sandbox, foreign):
    _, _, _, env = sandbox
    ready = Path(env["TMPDIR"]) / "listener-ready"
    server_code = (
        "import http.server, pathlib, sys; "
        "handler = type('Handler', (http.server.BaseHTTPRequestHandler,), "
        "{'do_GET': lambda self: (self.send_response(200), self.end_headers()), "
        "'log_message': lambda *args: None}); "
        "server = http.server.HTTPServer(('127.0.0.1', 0), handler); "
        "pathlib.Path(sys.argv[1]).write_text(str(server.server_port)); "
        "server.serve_forever()"
    )
    parent_code = (
        "import subprocess, sys, time; "
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]]); "
        "time.sleep(60)"
    )
    processes = []
    try:
        leader = subprocess.Popen(
            [sys.executable, "-c", parent_code, server_code, str(ready)],
            start_new_session=True,
        )
        processes.append(leader)
        for _ in range(100):
            if ready.exists():
                break
            time.sleep(0.02)
        assert ready.exists(), "child listener did not become ready"
        if foreign:
            leader = subprocess.Popen(["/bin/sleep", "60"], start_new_session=True)
            processes.append(leader)
        pid_file = Path(env["TMPDIR"]) / "site.pid"
        pid_file.write_text(str(leader.pid))
        env.update(LU_VERIFY_PID_FILE=str(pid_file), LU_VERIFY_HOST="127.0.0.1",
                   LU_VERIFY_PORT=ready.read_text())
        result = run(sandbox, "doctor.sh")
        assert result.returncode == int(foreign), result.stdout + result.stderr
        if foreign:
            assert "not owned by process group" in result.stderr
        else:
            assert f"owned by process group {leader.pid}" in result.stdout
    finally:
        for process in processes:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)


@pytest.mark.parametrize("fail_ruff", [False, True])
def test_checks_aggregate_and_share_interpreter(sandbox, fail_ruff):
    root, _, commands, env = sandbox
    manifest = root / "site/src/data/lexicon-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}")
    log = Path(env["TMPDIR"]) / "calls"
    env["CALL_LOG"] = str(log)
    env["FAIL_RUFF"] = str(int(fail_ruff))
    interpreter = command(
        commands, "project interpreter",
        'printf "%s\\n" "$*" >> "$CALL_LOG"\n'
        'if [[ "$*" == "-m ruff "* && "$FAIL_RUFF" == 1 ]]; then exit 7; fi',
    )
    env["LU_VERIFY_PYTHON"] = str(interpreter)
    command(commands, "git", "exit 0")
    result = run(sandbox, "run-checks.sh")
    assert result.returncode == int(fail_ruff), result.stdout + result.stderr
    calls = log.read_text()
    assert "-m scripts.practice_deck.io" in calls
    assert "scripts/audit/lint_word_atlas.py" in calls
    assert "tests/validate/test_permissions_register.py" in calls
    assert "Summary:" in result.stdout
    assert "1 failed" in result.stdout if fail_ruff else "0 failed" in result.stdout
