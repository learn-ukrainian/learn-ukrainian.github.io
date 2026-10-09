"""Native driver hook parity, payload contracts and launcher identity binding."""

from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import pytest

from scripts.agent_runtime import grok_hook_bridge as bridge
from scripts.agent_runtime.adapters import grok_build
from scripts.common.repo_root import main_checkout_root, project_interpreter

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "agents_extensions/grok/hooks/driver.json"
SESSION = "00000000-0000-4000-8000-000000000267"
GUARDS = (
    "enforce-venv.sh",
    "heal-core-bare.py",
    "guard-branch-switch-in-main.py",
    "guard-admin-merge.py",
    "guard-pr-merge.py",
    "guard-secret-print.py",
    "guard-primary-checkout-write.py",
    "guard-public-github-text.py",
)


def _fleet_guard_groups(**kwargs):
    return grok_build._fleet_guard_groups(**kwargs)


def event(tool="run_terminal_command", tool_input=None, *, cwd=ROOT, session=SESSION):
    return {
        "hookEventName": "pre_tool_use",
        "sessionId": session,
        "promptId": "fixture-prompt",
        "cwd": str(cwd),
        "workspaceRoot": str(cwd),
        "timestamp": "2026-10-09T00:00:00Z",
        "permissionMode": "default",
        "toolName": tool,
        "toolUseId": "fixture-tool",
        "toolInputTruncated": False,
        "toolInput": {"command": "echo ordinary"} if tool_input is None else tool_input,
    }


def driver_env():
    return {
        **os.environ,
        "LU_GROK_DRIVER_SESSION_ID": SESSION,
        "LU_GROK_SOURCE_ROOT": str(ROOT),
        "LU_GROK_PROJECT_PYTHON": str(project_interpreter(ROOT)),
        "SESSION_STREAM_AGENT": "grok",
        "SESSION_STREAM_HARNESS": "grok-tui",
        "LEARN_UK_SECRETS_OK": "0",
    }


def profile_run(payload, group=0, *, env=None):
    command = json.loads(PROFILE.read_text())["hooks"]["PreToolUse"][group]["hooks"][0]["command"]
    return subprocess.run(
        ["bash", "-c", command],
        cwd=ROOT,
        env=driver_env() if env is None else env,
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def scratch_repo(tmp_path):
    """The protected checkout in these probes is a synthetic Git repository."""
    repo = tmp_path / "primary with spaces"
    repo.mkdir()
    for args in (
        ("init", "-q", "-b", "main"),
        ("config", "user.email", "fixture@example.invalid"),
        ("config", "user.name", "Fixture"),
    ):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, timeout=30)
    (repo / "tracked.txt").write_text("keep\n")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True, timeout=30)
    worktree = repo / ".worktrees/dispatch/fixture/task"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-qb", "fixture", str(worktree)], check=True, timeout=30)
    return repo, worktree


def test_profile_matches_all_shared_pretool_guards():
    profile = json.loads(PROFILE.read_text())
    assert set(profile["hooks"]) == {"PreToolUse"}
    expected = _fleet_guard_groups(publish_guard=False, native_aliases=True)
    assert [group["matcher"] for group in profile["hooks"]["PreToolUse"]] == [group["matcher"] for group in expected]
    for actual, group in zip(profile["hooks"]["PreToolUse"], expected, strict=True):
        # The bridge must return an explicit deny before Grok's outer timeout,
        # whose failure posture is open. Include startup/translation headroom.
        assert actual["hooks"][0]["timeout"] > sum(max(15, int(hook.get("timeout", 5))) for hook in group["hooks"])
    assert [Path(shlex.split(hook["command"])[-1]).name for hook in expected[0]["hooks"]] == list(GUARDS)
    assert len(expected[1]["hooks"]) == 1
    assert "guard-primary-checkout-write.py" in expected[1]["hooks"][0]["command"]
    assert "reviewer" not in PROFILE.read_text()


@pytest.mark.parametrize("tool", ["write", "search_replace", "hashline_edit", "Write", "Edit", "MultiEdit"])
def test_native_primary_write_denied_dispatch_write_allowed(scratch_repo, tool):
    repo, worktree = scratch_repo
    blocked = profile_run(event(tool, {"file_path": str(repo / "tracked.txt")}, cwd=repo), 1)
    allowed = profile_run(event(tool, {"file_path": str(worktree / "tracked.txt")}, cwd=worktree), 1)
    assert blocked.returncode == 2, blocked.stdout + blocked.stderr
    assert "primary" in blocked.stderr.lower()
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert (repo / "tracked.txt").read_text() == "keep\n"


@pytest.mark.parametrize("tool", ["run_terminal_command", "run_terminal_cmd", "Bash"])
def test_native_shell_primary_write_denied_dispatch_and_ordinary_allowed(scratch_repo, tool):
    repo, worktree = scratch_repo
    for cwd, command, expected in (
        (repo, "echo overwrite > tracked.txt", 2),
        (worktree, "echo overwrite > tracked.txt", 0),
        (repo, "echo ordinary", 0),
    ):
        result = profile_run(event(tool, {"command": command}, cwd=cwd))
        assert result.returncode == expected, result.stdout + result.stderr


@pytest.mark.parametrize("guard_name", GUARDS)
@pytest.mark.parametrize("shape", ["ordinary", "missing_command", "malformed_input", "malformed_command", "truncated"])
def test_native_payload_through_each_driver_guard(monkeypatch, guard_name, shape):
    """Isolate each real guard; compare its input contract without changing it."""
    groups = _fleet_guard_groups(publish_guard=False, native_aliases=True)
    selected = next(hook for hook in groups[0]["hooks"] if Path(shlex.split(hook["command"])[-1]).name == guard_name)
    payload = event()
    if shape == "missing_command":
        payload["toolInput"] = {}
    elif shape == "malformed_input":
        payload["toolInput"] = "invalid"
    elif shape == "malformed_command":
        payload["toolInput"] = {"command": []}
    elif shape == "truncated":
        payload["toolInputTruncated"] = True
    for key, value in driver_env().items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "argv", [str(bridge.__file__), "--driver", groups[0]["matcher"]])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setattr(
        "scripts.agent_runtime.adapters.grok_build._fleet_guard_groups",
        lambda **kwargs: [{**groups[0], "hooks": [selected]}],
    )
    expected = 0
    if shape == "truncated":
        expected = 2  # No guard can certify an input Grok explicitly clipped.
    elif shape in {"malformed_input", "malformed_command"}:
        # Empty list commands are treated as absent by the older soft guards.
        # String inputs instead crash those guards; the bridge converts their
        # nonzero exit to Grok's blocking exit 2. No guard contract is changed.
        soft = {"enforce-venv.sh"}
        if shape == "malformed_command":
            soft.update({"heal-core-bare.py", "guard-branch-switch-in-main.py", "guard-admin-merge.py"})
        expected = 0 if guard_name in soft else 2
    assert bridge.main() == expected


@pytest.mark.parametrize("raw", ["not-json", "null", "[]", "{}"])
def test_malformed_bound_event_denies(raw):
    assert profile_run(raw).returncode == 2


@pytest.mark.parametrize("kind", ["interactive", "worker", "isolated_review", "native_child"])
def test_profile_does_not_activate_outside_bound_driver(kind, scratch_repo):
    repo, _ = scratch_repo
    env = driver_env()
    payload = event("write", {"file_path": str(repo / "tracked.txt")}, cwd=repo)
    if kind == "interactive":
        env.pop("LU_GROK_DRIVER_SESSION_ID")
    else:
        payload["sessionId"] = "other-session"
    result = profile_run(payload, 1, env=env)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("key", ["SESSION_STREAM_AGENT", "SESSION_STREAM_HARNESS"])
def test_bound_event_refuses_wrong_launcher_identity(key):
    env = driver_env()
    env[key] = "worker"
    assert profile_run(event(), env=env).returncode == 2


def test_driver_preserves_publication_shim_rewrite():
    result = profile_run(event(tool_input={"command": "gh --version"}))
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    rewritten = output["hookSpecificOutput"]["updatedInput"]["command"]
    assert "scripts/agent_runtime/shims" in rewritten
    assert rewritten.endswith("gh --version")


@pytest.mark.parametrize("command", ["python -c 'pass'", "gh pr merge 5 --auto", "gh pr merge --admin", "cat .env"])
def test_native_shell_guard_denials(command):
    result = profile_run(event(tool_input={"command": command}))
    assert result.returncode == 2, result.stdout + result.stderr


def test_native_branch_switch_guard_denial():
    # This guard protects this source tree's canonical primary specifically.
    # The command is hook input only: no branch switch is ever executed.
    repo = main_checkout_root(ROOT)
    command = shlex.join(["git", "-C", str(repo), "checkout", "-b", "forbidden"])
    result = profile_run(event(tool_input={"command": command}, cwd=repo))
    assert result.returncode == 2, result.stdout + result.stderr
    assert "guard-branch-switch-in-main" in result.stderr


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("guard_returncode", [0, 2])
def test_worker_bridge_keeps_native_and_legacy_contract(monkeypatch, native, guard_returncode):
    payload = event()
    if not native:
        payload.pop("hookEventName")
        payload["hook_event_name"] = "PreToolUse"
    translated = bridge._translate(payload)
    guard = str(ROOT / "agents_extensions/shared/hooks/guard-secret-print.py")
    monkeypatch.setattr(sys, "argv", [str(bridge.__file__), guard])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, json.loads(kwargs["input"])))
        return subprocess.CompletedProcess(argv, guard_returncode)

    monkeypatch.setattr(bridge.subprocess, "run", run)
    assert bridge.main() == guard_returncode
    assert calls[0][0] == [guard]
    assert calls[0][1] == translated
    assert calls[0][1]["tool_name"] == "Bash"
    assert calls[0][1]["tool_input"]["command"] == "echo ordinary"


@pytest.mark.parametrize("failure", ["missing_guard", "timeout", "unknown_group"])
def test_driver_guard_runtime_failure_denies(monkeypatch, failure):
    groups = _fleet_guard_groups(publish_guard=False, native_aliases=True)
    for key, value in driver_env().items():
        monkeypatch.setenv(key, value)
    matcher = "unknown" if failure == "unknown_group" else groups[0]["matcher"]
    monkeypatch.setattr(sys, "argv", [str(bridge.__file__), "--driver", matcher])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event())))
    if failure == "missing_guard":
        groups[0]["hooks"][0]["command"] = str(ROOT / "agents_extensions/shared/hooks/missing.py")
        monkeypatch.setattr(grok_build, "_fleet_guard_groups", lambda **kwargs: groups)
    elif failure == "timeout":

        def timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired("fixture", 15)

        monkeypatch.setattr(bridge.subprocess, "run", timeout)
    assert bridge.main() == 2


def test_launcher_binds_uuid_and_clears_inherited_binding(tmp_path):
    """Exercise the adapter exec seam; no lease or provider is started."""
    output = tmp_path / "captured.json"
    script = """
set -eu
source scripts/launchers/grok.sh
LC_ROOT="$PWD"
LC_DURABLE_HELPER_ROOT="$1"
LC_FORWARD_ARGS=()
LC_HARNESS=grok
LC_MODE="$2"
LC_DRY_RUN=0
LC_MODEL=""
LC_EFFORT=""
LC_RULES_CORE=""
export SESSION_STREAM_AGENT=grok SESSION_STREAM_HARNESS=grok-tui
export LU_GROK_DRIVER_SESSION_ID=parent-binding
launcher_exec_command() {
  "$3" -c 'import json,os,sys; print(json.dumps({"argv":sys.argv[1:], "binding":os.environ.get("LU_GROK_DRIVER_SESSION_ID"), "root":os.environ.get("LU_GROK_SOURCE_ROOT"), "python":os.environ.get("LU_GROK_PROJECT_PYTHON")}))' "${@:1}"
}
launcher_adapter_exec
"""
    # Function positional parameters differ from the shell's; supply the
    # interpreter through an exported fixture variable instead.
    script = script.replace('"$3" -c', '"$FIXTURE_PYTHON" -c')
    for mode in ("driver", "interactive"):
        result = subprocess.run(
            ["bash", "-c", script, "fixture", str(project_interpreter(ROOT).parents[2]), mode],
            cwd=ROOT,
            env={**os.environ, "FIXTURE_PYTHON": sys.executable},
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0, result.stderr
        output.write_text(result.stdout)
        data = json.loads(output.read_text())
        if mode == "driver":
            UUID(data["binding"])
            assert data["argv"] == ["grok", "--session-id", data["binding"]]
            assert data["root"] == str(ROOT)
            assert data["python"] == str(project_interpreter(ROOT))
        else:
            assert data["argv"] == ["grok"]
            assert data["binding"] is None and data["root"] is None and data["python"] is None


@pytest.mark.parametrize("arg", ["--session-id=other", "-sother", "--resume", "-r", "--continue", "--fork-session"])
def test_driver_refuses_forwarded_identity_override(arg):
    from tests.test_launcher_contract import run_launcher

    result = run_launcher("start-grok-driver.sh", "--epic", "infra", "--", arg)
    assert result.returncode == 2
    assert "launcher-bound" in result.stderr
