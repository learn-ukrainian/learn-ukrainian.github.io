"""Native driver hook parity, payload contracts and launcher identity binding."""

from __future__ import annotations

import io
import json
import os
import re
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
    assert [group["matcher"] for group in profile["hooks"]["PreToolUse"]] == [
        f"^({group['matcher']})$" for group in expected
    ]
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
    expected = 0 if shape == "ordinary" else 2
    assert bridge.main() == expected


@pytest.mark.parametrize("raw", ["not-json", "null", "[]", "{}"])
def test_malformed_bound_event_denies(raw):
    assert profile_run(raw).returncode == 2


@pytest.mark.parametrize("kind", ["interactive", "worker", "isolated_review"])
def test_profile_does_not_activate_without_driver_binding(kind, scratch_repo):
    repo, _ = scratch_repo
    env = driver_env()
    for key in tuple(env):
        if key.startswith("LU_GROK_"):
            env.pop(key)
    payload = event("write", {"file_path": str(repo / "tracked.txt")}, cwd=repo, session=kind)
    result = profile_run(payload, 1, env=env)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("session", ["native_child", "new", "resume", "fork", None])
def test_driver_binding_guards_every_native_session(session, scratch_repo):
    repo, _ = scratch_repo
    payload = event("write", {"file_path": str(repo / "tracked.txt")}, cwd=repo, session=session)
    result = profile_run(payload, 1)
    assert result.returncode == 2, result.stdout + result.stderr


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


@pytest.mark.parametrize("failure", ["missing_guard", "timeout", "unknown_group", "unexpected_exception"])
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
    elif failure == "unexpected_exception":

        def unexpected(*args, **kwargs):
            raise AssertionError("unexpected guard failure")

        monkeypatch.setattr(bridge.subprocess, "run", unexpected)
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


@pytest.mark.parametrize("key", ["LU_GROK_PROJECT_PYTHON"])
@pytest.mark.parametrize("value", ["", "/missing/interpreter"])
def test_driver_wrapper_missing_interpreter_denies(key, value):
    env = driver_env()
    env[key] = value
    assert profile_run(event(), env=env).returncode == 2


def test_todo_write_bypasses_native_profile_but_primary_write_denies(scratch_repo):
    groups = json.loads(PROFILE.read_text())["hooks"]["PreToolUse"]
    assert not any(re.search(group["matcher"], "todo_write") for group in groups)
    repo, _ = scratch_repo
    payload = event("write", {"file_path": str(repo / "tracked.txt")}, cwd=repo)
    matched = [i for i, group in enumerate(groups) if re.search(group["matcher"], "write")]
    assert matched == [1]
    assert profile_run(payload, matched[0]).returncode == 2


def test_shell_workdir_is_not_shadowed_by_session_cwd(scratch_repo):
    repo, worktree = scratch_repo
    result = profile_run(
        event(tool_input={"command": "echo overwrite > tracked.txt", "workdir": str(repo)}, cwd=worktree)
    )
    assert result.returncode == 2, result.stdout + result.stderr


@pytest.mark.parametrize("mode", ["danger", "workspace-write", "read-only"])
def test_dispatched_grok_environment_scrubs_driver_binding(monkeypatch, tmp_path, mode):
    from scripts.agent_runtime.env_sanitize import build_agent_env

    bindings = {key: value for key, value in driver_env().items() if key.startswith("LU_GROK_")}
    bindings["LU_GROK_FUTURE_BINDING"] = "future"
    for key, value in bindings.items():
        monkeypatch.setenv(key, value)
    original_which = grok_build.shutil.which
    monkeypatch.setattr(
        grok_build.shutil,
        "which",
        lambda name, *args, **kwargs: "/fixture/grok" if name == "grok" else original_which(name, *args, **kwargs),
    )
    adapter = grok_build.GrokBuildAdapter()
    plan = adapter.build_invocation(
        prompt="fixture",
        cwd=tmp_path,
        task_id="fixture",
        mode=mode,
        model="grok-4.7",
        effort="high",
        session_id=None,
        tool_config={"reviewer_tools": True} if mode == "read-only" else None,
    )
    try:
        env = build_agent_env(provider="grok", overrides=plan.env_overrides)
        for key in plan.env_unsets:
            env.pop(key, None)
        assert not any(key.startswith("LU_GROK_") for key in env)
        assert set(bindings) <= set(plan.env_unsets)
        assert all(os.environ[key] == value for key, value in bindings.items())
    finally:
        adapter.cleanup_invocation(plan)


def test_worker_path_denies_truncated_input(monkeypatch):
    payload = event()
    payload["toolInputTruncated"] = True
    guard = str(ROOT / "agents_extensions/shared/hooks/guard-secret-print.py")
    monkeypatch.setattr(sys, "argv", [str(bridge.__file__), guard])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    def unexpected(*args, **kwargs):
        pytest.fail("truncated payload reached a guard")

    monkeypatch.setattr(bridge.subprocess, "run", unexpected)
    assert bridge.main() == 2


@pytest.mark.parametrize(
    "condition",
    [
        "ok",
        "untrusted",
        "missing_profile",
        "drift",
        "missing_shell",
        "missing_write",
        "wrong_source",
        "wrong_command",
        "disabled",
        "invalid_json",
        "inspect_failed",
    ],
)
def test_driver_launcher_preflight_requires_discovered_trusted_profile(monkeypatch, tmp_path, condition):
    root = tmp_path / "checkout"
    source = root / "agents_extensions/grok/hooks/driver.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(PROFILE.read_bytes())
    deployed = root / ".grok/hooks/driver.json"
    deployed.parent.mkdir(parents=True)
    if condition != "missing_profile":
        deployed.write_bytes(b"{}" if condition == "drift" else source.read_bytes())
    profile = json.loads(source.read_text())
    inspection = {
        "projectTrusted": condition != "untrusted",
        "hooks": [
            {
                "event": "pre_tool_use",
                "hookType": "command",
                "matcher": group["matcher"],
                "target": group["hooks"][0]["command"],
                "source": {"type": "project", "path": str(deployed.parent)},
            }
            for group in profile["hooks"]["PreToolUse"]
        ],
    }
    if condition in {"missing_shell", "missing_write"}:
        inspection["hooks"].pop(0 if condition == "missing_shell" else 1)
    elif condition == "wrong_source":
        inspection["hooks"][0]["source"]["path"] = str(root / "other")
    elif condition == "wrong_command":
        inspection["hooks"][0]["target"] = "true"
    elif condition == "disabled":
        inspection["hooks"][0]["compatibilityStatus"] = "disabled"
    fixture = tmp_path / "inspect.json"
    fixture.write_text("not-json" if condition == "invalid_json" else json.dumps(inspection))
    # Exercise validation directly as well as the launcher wiring below.
    # Native command failure is handled by the shell before validation.
    monkeypatch.setattr(sys, "stdin", io.StringIO(fixture.read_text()))
    if condition == "ok":
        assert bridge._driver_preflight(root) == 0
    elif condition != "inspect_failed":
        with pytest.raises(ValueError, match="Grok driver preflight"):
            bridge._driver_preflight(root)
    script = """
source scripts/launchers/grok.sh
LC_HARNESS=grok
LC_MODE=driver
LC_ROOT="$1"
LC_DURABLE_HELPER_ROOT="$2"
launcher_error() { echo "$*" >&2; }
launcher_require_binary() { return 0; }
grok() { if [ "$FIXTURE_CONDITION" = inspect_failed ]; then return 1; fi; cat "$FIXTURE_INSPECT"; }
launcher_adapter_preflight
"""
    # The source bridge lives in this worktree, while profile data is synthetic.
    bridge_path = root / "scripts/agent_runtime/grok_hook_bridge.py"
    bridge_path.parent.mkdir(parents=True)
    bridge_path.write_bytes(Path(bridge.__file__).read_bytes())
    result = subprocess.run(
        ["bash", "-c", script, "fixture", str(root), str(project_interpreter(ROOT).parents[2])],
        cwd=ROOT,
        env={**os.environ, "FIXTURE_INSPECT": str(fixture), "FIXTURE_CONDITION": condition},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == (0 if condition == "ok" else 2), result.stdout + result.stderr
    if condition != "ok":
        assert "Grok driver preflight" in result.stderr
        assert (
            "trust"
            if condition == "untrusted"
            else "grok inspect --json"
            if condition in {"invalid_json", "inspect_failed"}
            else "npm run agents:deploy"
        ) in result.stderr


def test_grok_deployment_is_gitignored(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    (tmp_path / ".gitignore").write_bytes((ROOT / ".gitignore").read_bytes())
    result = subprocess.run(
        ["git", "check-ignore", ".grok/hooks/driver.json"], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ".grok/hooks/driver.json\n"


def test_worker_translation_keeps_existing_cwd_contract():
    payload = event(
        tool_input={"command": "echo ordinary", "workdir": "worker-tool-directory"}, cwd="worker-session-directory"
    )
    assert bridge._translate(payload)["tool_input"]["cwd"] == "worker-session-directory"


@pytest.mark.parametrize("tool_input", ["invalid", [], None])
def test_driver_write_input_requires_object(tool_input):
    payload = event("write")
    payload["toolInput"] = tool_input
    assert profile_run(payload, 1).returncode == 2


@pytest.mark.parametrize("mode", ["interactive", "driver"])
def test_preflight_dry_run_does_not_inspect_or_require_provider(mode):
    script = """
source scripts/launchers/grok.sh
LC_HARNESS=grok
LC_MODE="$1"
LC_DRY_RUN=1
launcher_require_binary() { return 0; }
grok() { echo 'unexpected provider execution' >&2; return 97; }
launcher_adapter_preflight
"""
    result = subprocess.run(
        ["bash", "-c", script, "fixture", mode], cwd=ROOT, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    if mode == "driver":
        assert "would require a trusted folder" in result.stdout
