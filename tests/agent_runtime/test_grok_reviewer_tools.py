"""Opt-in Grok reviewer shell and hook boundary."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.agent_runtime.env_sanitize import build_agent_env

ROOT = Path(__file__).resolve().parents[2]


def _plan(tmp_path: Path, config: dict | None):
    with patch("scripts.agent_runtime.adapters.grok_build.shutil.which", return_value="/usr/bin/grok"):
        return GrokBuildAdapter().build_invocation(
            prompt="inspect",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=config,
            effort="low",
        )


def test_reviewer_opt_in_adds_bash_and_all_tracked_guards(tmp_path: Path) -> None:
    adapter = GrokBuildAdapter()
    baseline = _plan(tmp_path, None)
    reviewer = _plan(tmp_path, {"reviewer_tools": True})
    try:
        agent_path = Path(reviewer.cmd[reviewer.cmd.index("--agent") + 1])
        definition = agent_path.read_text(encoding="utf-8")
        assert definition.count("type: command") == 11
        for name in (
            "enforce-venv.sh",
            "heal-core-bare.py",
            "guard-branch-switch-in-main.py",
            "guard-admin-merge.py",
            "guard-pr-merge.py",
            "guard-secret-print.py",
            "guard-primary-checkout-write.py",
            "guard-public-github-text.py",
            "guard-reviewer-publish.py",
        ):
            assert str(ROOT / "agents_extensions/shared/hooks" / name) in definition
        assert str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py") in definition
        assert reviewer.cmd[reviewer.cmd.index("--permission-mode") + 1] == "auto"
        assert "--always-approve" not in reviewer.cmd
        allows = [reviewer.cmd[i + 1] for i, arg in enumerate(reviewer.cmd) if arg == "--allow"]
        assert "Bash" not in allows
        from scripts.agent_runtime.grok_reviewer_permissions import GROK_REVIEWER_TOOLS

        assert reviewer.cmd[reviewer.cmd.index("--tools") + 1].split(",") == list(GROK_REVIEWER_TOOLS)
        assert allows == ["Read", "Grep"]
        assert "grok_reviewer_permissions.py" in definition
        assert "Approval-requiring tools are denied without prompting" in definition
        assert "--no-subagents" in reviewer.cmd and "--disable-web-search" in reviewer.cmd
        denies = [reviewer.cmd[i + 1] for i, arg in enumerate(reviewer.cmd) if arg == "--deny"]
        assert set(denies) == {"Write", "Edit", "Bash", "MCPTool", "WebFetch", "WebSearch"}
        assert "search_replace" in reviewer.cmd[reviewer.cmd.index("--disallowed-tools") + 1].split(",")
        assert baseline.cmd[baseline.cmd.index("--permission-mode") + 1] == "auto"
        assert reviewer.env_overrides == {"LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK": "1"}
        env = build_agent_env(provider="grok", overrides=reviewer.env_overrides)
        assert any(
            value == "url.file:///dev/null/claude-read-only/.pushInsteadOf"
            for key, value in env.items()
            if key.startswith("GIT_CONFIG_KEY_")
        )
    finally:
        adapter.cleanup_invocation(reviewer)
    assert not agent_path.exists()


@pytest.mark.parametrize(
    "config",
    [
        {"reviewer_tools": True, "allowed_tools": "Read"},
        {"reviewer_tools": True, "strict_mcp_config": True},
        {"reviewer_tools": True, "mcp_server_names": ["sources"]},
        {"reviewer_tools": False},
    ],
)
def test_nonordinary_callers_keep_baseline_argv(tmp_path: Path, config: dict) -> None:
    baseline_config = {key: value for key, value in config.items() if key != "reviewer_tools"}
    assert _plan(tmp_path, config).cmd == _plan(tmp_path, baseline_config).cmd


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("gh pr view 8912 --json number", False),
        ("git push --dry-run", True),
        ("python -m scripts.publish issue-comment --number 1 --body unit", True),
        ("python -m scripts.publish --help", False),
        ("python -m scripts.publish pr-comment --help", False),
        ("gh pr comment 8912 --body test", True),
    ],
)
def test_grok_hook_bridge_runs_publish_guard(command: str, blocked: bool) -> None:
    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": command},
        "cwd": str(ROOT),
    }
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
            str(ROOT / "agents_extensions/shared/hooks/guard-reviewer-publish.py"),
        ],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert (result.returncode == 2) is blocked, (command, result.stderr)


def test_grok_hook_bridge_denies_unreadable_event() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
            str(ROOT / "agents_extensions/shared/hooks/guard-reviewer-publish.py"),
        ],
        input="{}",
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2


_PINNED_GUARDS = ("guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py")
_HOOKS = ROOT / "agents_extensions/shared/hooks"


def _pinned(name: str) -> str:
    from scripts.agent_runtime.adapters.claude import _worker_guard_invocation

    command = _worker_guard_invocation(
        f'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh" {name}', ROOT
    )
    assert command is not None
    return command


def _bridge(guard_command: str, shell_command: str) -> subprocess.CompletedProcess[str]:
    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": shell_command},
        "cwd": str(ROOT),
    }
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"), guard_command],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_grok_bridge_guard_set_matches_the_claude_adapter() -> None:
    from scripts.agent_runtime.adapters.claude import PROJECT_PYTHON_GUARDS as adapter_guards
    from scripts.agent_runtime.grok_hook_bridge import PROJECT_PYTHON_GUARDS as bridge_guards

    assert bridge_guards == adapter_guards == set(_PINNED_GUARDS)


@pytest.mark.parametrize("name", _PINNED_GUARDS)
def test_grok_bridge_runs_the_adapters_pinned_invocation(name: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import guard_argv
    from scripts.common.repo_root import project_interpreter

    command = _pinned(name)
    assert guard_argv(command) == [str(project_interpreter(ROOT)), str(_HOOKS / name)]
    allowed = _bridge(command, "echo 'git checkout -b fixture; gh pr merge 5 --admin'")
    assert allowed.returncode == 0, allowed.stderr


def test_grok_bridge_pinned_guard_still_blocks() -> None:
    result = _bridge(_pinned("guard-pr-merge.py"), "gh pr merge 5 --auto")
    assert result.returncode == 2, result.stderr


@pytest.mark.parametrize("name", ["guard-pr-merge.py", "guard-secret-print.py", "enforce-venv.sh"])
def test_grok_bridge_keeps_the_plain_guard_path(name: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import guard_argv

    guard = str(_HOOKS / name)
    assert guard_argv(guard) == [guard]


@pytest.mark.parametrize(
    "command",
    [
        "{python} '{hooks}/guard-pr-'merge.py",
        '"{python}" "{hooks}/guard-pr-merge.py"',
        "{python} {hooks}/guard\\-pr-merge.py",
    ],
)
def test_grok_bridge_classifies_the_pinned_invocation_after_tokenization(command: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import guard_argv
    from scripts.common.repo_root import project_interpreter

    python = project_interpreter(ROOT)
    assert guard_argv(command.format(python=python, hooks=_HOOKS)) == [str(python), str(_HOOKS / "guard-pr-merge.py")]


@pytest.mark.parametrize("command", ["'{hooks}/guard-secret-'print.py", "{hooks}/guard\\-secret-print.py"])
def test_grok_bridge_classifies_the_plain_path_after_tokenization(command: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import guard_argv

    assert guard_argv(command.format(hooks=_HOOKS)) == [str(_HOOKS / "guard-secret-print.py")]


@pytest.mark.parametrize(
    ("command", "reason"),
    [
        # Extra arguments, behind split quoting and backslash spellings too.
        ("{python} '{hooks}/guard-pr-'merge.py --extra", "pinned interpreter invocation required"),
        ("{python} {hooks}/guard\\-pr-merge.py extra", "pinned interpreter invocation required"),
        ("'{hooks}/guard-secret-'print.py --extra", "only tracked parser guards"),
        # Missing arguments: the interpreter or nothing at all.
        ("{python}", "only tracked fleet guards may run"),
        ("'{python}'", "only tracked fleet guards may run"),
        ("", "pinned interpreter invocation required"),
        # The wrapper, an untracked path, or a tracked path in another spelling of the directory.
        ("{hooks}/run-project-python-hook.sh", "only tracked fleet guards may run"),
        ("{python} '{hooks}/run-project-python-'hook.sh", "only tracked parser guards"),
        ("/bin/true", "only tracked fleet guards may run"),
        ("{hooks}/../hooks/guard-secret-print.py", "only tracked fleet guards may run"),
    ],
)
def test_grok_bridge_refuses_noncanonical_spellings(command: str, reason: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import GuardInvocationError, guard_argv
    from scripts.common.repo_root import project_interpreter

    command = command.format(python=project_interpreter(ROOT), hooks=_HOOKS)
    with pytest.raises(GuardInvocationError, match=reason):
        guard_argv(command)
    result = _bridge(command, "echo hello")
    assert result.returncode == 2
    assert reason in result.stderr


@pytest.mark.parametrize(
    ("argv", "reason"),
    [
        (["/usr/bin/python3", "{hooks}/guard-pr-merge.py"], "not the project interpreter"),
        (["{python}", "{hooks}/guard-secret-print.py"], "only tracked parser guards"),
        (["{python}", "/tmp/elsewhere/guard-pr-merge.py"], "only tracked parser guards"),
        (["{python}", "{hooks}/guard-pr-merge.py", "--extra"], "pinned interpreter invocation required"),
        (["{python}", "-I", "{hooks}/guard-pr-merge.py"], "pinned interpreter invocation required"),
        (["/tmp/elsewhere/guard-pr-merge.py"], "only tracked fleet guards may run"),
    ],
)
def test_grok_bridge_refuses_other_invocations(argv: list[str], reason: str) -> None:
    from scripts.agent_runtime.grok_hook_bridge import GuardInvocationError, guard_argv
    from scripts.common.repo_root import project_interpreter

    command = shlex.join(arg.format(python=project_interpreter(ROOT), hooks=_HOOKS) for arg in argv)
    with pytest.raises(GuardInvocationError, match=reason):
        guard_argv(command)
    result = _bridge(command, "echo hello")
    assert result.returncode == 2
    assert reason in result.stderr


def test_grok_bridge_refuses_an_unreadable_invocation() -> None:
    from scripts.agent_runtime.grok_hook_bridge import GuardInvocationError, guard_argv

    with pytest.raises(GuardInvocationError, match="unreadable"):
        guard_argv(f"python '{_HOOKS / 'guard-pr-merge.py'}")


@pytest.mark.parametrize("pinned", [True, False])
def test_grok_bridge_refuses_a_missing_guard(tmp_path: Path, monkeypatch, pinned: bool) -> None:
    from scripts.agent_runtime import grok_hook_bridge

    hooks = tmp_path / "agents_extensions/shared/hooks"
    hooks.mkdir(parents=True)
    monkeypatch.setattr(grok_hook_bridge, "__file__", str(tmp_path / "scripts/agent_runtime/grok_hook_bridge.py"))
    guard = str(hooks / "guard-pr-merge.py")
    command = shlex.join([sys.executable, guard] if pinned else [guard])
    with pytest.raises(grok_hook_bridge.GuardInvocationError, match="fleet guard unavailable"):
        grok_hook_bridge.guard_argv(command)


_FLEET_GUARD_NAMES = (
    "enforce-venv.sh",
    "heal-core-bare.py",
    "guard-branch-switch-in-main.py",
    "guard-admin-merge.py",
    "guard-pr-merge.py",
    "guard-secret-print.py",
    "guard-primary-checkout-write.py",
    "guard-public-github-text.py",
)


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_write_mode_installs_fleet_guards_without_reviewer_publish_or_push_rewrite(tmp_path: Path, mode: str) -> None:
    """Write sessions load the fleet PreToolUse guards and can still push (#8965).

    Grok 1.0.41 leaves yolo off when ``--permission-mode auto`` is set, and the
    auto classifier then refuses ``git push`` before execution. Write mode uses
    ``bypassPermissions`` plus the tracked worker guards. The agent is the write
    worker, not the read-only reviewer: no publish guard and no push rewrite.
    """
    adapter = GrokBuildAdapter()
    agent_path: Path | None = None
    with patch("scripts.agent_runtime.adapters.grok_build.shutil.which", return_value="/usr/bin/grok"):
        write_plan = adapter.build_invocation(
            prompt="push the dispatch branch",
            mode=mode,
            cwd=tmp_path,
            model=None,
            task_id="impl-8965",
            session_id=None,
            tool_config={"reviewer_tools": True},
            effort="low",
        )
    try:
        assert write_plan.cmd[write_plan.cmd.index("--permission-mode") + 1] == "bypassPermissions"
        assert "--always-approve" in write_plan.cmd
        assert "--deny" not in write_plan.cmd
        assert "reviewer_agent_file" not in write_plan.metadata
        agent_path = Path(write_plan.cmd[write_plan.cmd.index("--agent") + 1])
        assert agent_path.name.endswith(".grok-write-agent.md")
        definition = agent_path.read_text(encoding="utf-8")
        assert "name: lu-write-worker" in definition
        assert "lu-read-only-reviewer" not in definition
        assert definition.count("type: command") == 9
        for name in _FLEET_GUARD_NAMES:
            assert str(ROOT / "agents_extensions/shared/hooks" / name) in definition
        assert "guard-reviewer-publish.py" not in definition
        assert "run_terminal_command" in definition
        assert "search_replace" in definition
        assert str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py") in definition
        assert write_plan.env_overrides == {}
        env = build_agent_env(provider="grok", overrides=write_plan.env_overrides)
        assert not any(
            value == "url.file:///dev/null/claude-read-only/.pushInsteadOf"
            for key, value in env.items()
            if key.startswith("GIT_CONFIG_KEY_")
        )
    finally:
        adapter.cleanup_invocation(write_plan)
        if agent_path is not None:
            assert not agent_path.exists()

    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": "git push -u origin HEAD"},
        "cwd": str(ROOT),
    }
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
            str(ROOT / "agents_extensions/shared/hooks/guard-reviewer-publish.py"),
        ],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "git push" in result.stderr


def _protected_primary() -> Path | None:
    """Primary checkout when it is on main/master; otherwise None."""
    common = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        text=True,
        timeout=30,
    ).strip()
    common_path = Path(common)
    if common_path.name != ".git":
        return None
    primary = common_path.parent
    branch = subprocess.check_output(
        ["git", "-C", str(primary), "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
        timeout=30,
    ).strip()
    if branch not in {"main", "master"}:
        return None
    return primary


def test_grok_hook_bridge_primary_checkout_write_guard() -> None:
    """The bridge lets the fleet guard classify Grok write and shell tools."""
    primary = _protected_primary()
    if primary is None:
        pytest.skip("primary checkout is not on a protected branch")
    probe = primary / "probe.txt"
    allow = Path("/tmp/grok-write-guard-allow.txt") if ROOT.resolve() == primary.resolve() else ROOT / "probe-allow.txt"
    cases = [
        ("write", {"file_path": str(probe), "content": "probe"}, True),
        (
            "search_replace",
            {"file_path": str(probe), "old_string": "a", "new_string": "b"},
            True,
        ),
        ("run_terminal_command", {"command": f"printf probe > {probe}"}, True),
        ("write", {"file_path": str(allow), "content": "ok"}, False),
    ]
    for tool_name, tool_input, blocked in cases:
        event = {
            "hook_event_name": "PreToolUse",
            "toolName": tool_name,
            "toolInput": tool_input,
            "cwd": str(ROOT),
        }
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
                str(ROOT / "agents_extensions/shared/hooks/guard-primary-checkout-write.py"),
            ],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (result.returncode == 2) is blocked, (tool_name, result.returncode, result.stderr)
        if blocked:
            assert "BLOCKED by guard-primary-checkout-write" in result.stderr
            assert str(probe) in result.stderr


def test_grok_hook_bridge_runs_fleet_venv_guard() -> None:
    event = {
        "hook_event_name": "PreToolUse",
        "toolName": "run_terminal_command",
        "toolInput": {"command": "python3 --version"},
        "cwd": str(ROOT),
    }
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/agent_runtime/grok_hook_bridge.py"),
            str(ROOT / "agents_extensions/shared/hooks/enforce-venv.sh"),
        ],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 2
    assert "Unqualified interpreter blocked" in result.stderr


@pytest.mark.parametrize("tool", ["run_terminal_command", "run_terminal_cmd", "Bash"])
def test_literal_read_commands_pass_guard_but_keep_native_bash_backstop(tmp_path, tool):
    from scripts.agent_runtime.grok_reviewer_permissions import GROK_REVIEWER_READ_COMMANDS, reviewer_command_allowed

    plan = _plan(tmp_path, {"reviewer_tools": True})
    try:
        allows = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd) if arg == "--allow"]
        for command in GROK_REVIEWER_READ_COMMANDS:
            assert reviewer_command_allowed({
                "hook_event_name": "PreToolUse", "toolName": tool, "toolInput": {"command": command},
            })
            assert f"Bash({command})" not in allows
        denies = [plan.cmd[i + 1] for i, arg in enumerate(plan.cmd) if arg == "--deny"]
        assert "Bash" in denies
    finally:
        GrokBuildAdapter().cleanup_invocation(plan)


@pytest.mark.parametrize("command", [
    "touch output.txt", "git push", "curl https://example.invalid", "wget https://example.invalid",
    "git -c color.ui=false diff", "python - <<'PY'\nprint('probe')\nPY",
    "cat ~/.grok/auth.json", "git diff --output=out", "git diff --ext-diff",
    "git diff --textconv", "env git diff", "git diff; touch output.txt",
])
def test_disallowed_shell_actions_return_typed_refusal_before_native_permissions(command):
    from scripts.agent_runtime.grok_reviewer_permissions import REFUSAL_CODE

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"), "--review-root", str(ROOT)],
        input=json.dumps({
            "hook_event_name": "PreToolUse", "toolName": "run_terminal_command", "toolInput": {"command": command},
        }), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert result.stderr.startswith(REFUSAL_CODE + ":")
    assert command not in result.stderr
    assert "Continue the review" in result.stderr


@pytest.mark.parametrize("payload", [None, [], {},
    {"hook_event_name": "PreToolUse", "toolName": "run_terminal_command", "toolInput": {}},
    {"hook_event_name": "PreToolUse", "toolName": "write", "toolInput": {"command": "pwd"}},
    {"hook_event_name": "PostToolUse", "toolName": "Bash", "toolInput": {"command": "pwd"}},
])
def test_permission_guard_fails_closed_on_unreadable_or_unknown_tools(payload):
    from scripts.agent_runtime.grok_reviewer_permissions import reviewer_command_allowed

    assert not reviewer_command_allowed(payload)


def test_literal_permissions_cannot_be_extended_or_wrapped():
    from scripts.agent_runtime.grok_reviewer_permissions import GROK_REVIEWER_READ_COMMANDS, reviewer_command_allowed

    for command in GROK_REVIEWER_READ_COMMANDS:
        for altered in (command + " > out", command + " && touch out", "env " + command,
                        command + " --output=out", command + " --ext-diff", command + "\n"):
            assert not reviewer_command_allowed({
                "hook_event_name": "PreToolUse", "toolName": "Bash", "toolInput": {"command": altered},
            })


def test_permission_guard_cli_admits_read_command_and_denies_bad_json():
    from scripts.agent_runtime.grok_reviewer_permissions import REFUSAL_CODE

    for event, expected in [(json.dumps({
        "hook_event_name": "PreToolUse", "toolName": "run_terminal_command", "toolInput": {"command": "pwd"},
    }), 0), ("broken json", 2)]:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"), "--review-root", str(ROOT)],
            input=event, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == expected
        assert result.stderr.startswith(REFUSAL_CODE) if expected else result.stderr == ""


@pytest.fixture
def tracked_review_root(tmp_path):
    root = tmp_path / "review"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    (root / "tracked.txt").write_text("public fixture", encoding="utf-8")
    (root / "untracked.txt").write_text("private fixture", encoding="utf-8")
    (root / "tracked[1].txt").write_text("private fixture", encoding="utf-8")
    (root / "tracked1.txt").write_text("public fixture", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt", "tracked1.txt"], cwd=root, check=True, timeout=30)
    return root


@pytest.mark.parametrize("tool,inputs,allowed", [
    ("read_file", {"target_file": "tracked.txt"}, True),
    ("grep", {"path": "tracked.txt", "pattern": "fixture"}, True),
    ("list_dir", {"target_directory": "."}, True),
    ("read_file", {"target_file": "untracked.txt"}, False),
    ("read_file", {"target_file": "tracked[1].txt"}, False),
    ("read_file", {"target_file": "missing.txt"}, False),
    ("read_file", {"target_file": ".git/config"}, False),
    ("read_file", {"target_file": "."}, False),
    ("grep", {"path": ".", "pattern": "fixture"}, False),
    ("grep", {"pattern": "fixture"}, False),
    ("list_dir", {"target_directory": ".git"}, False),
    ("read_file", {"target_file": ""}, False),
    ("read_file", {"target_file": "a\x00b"}, False),
    ("unknown", {}, False),
    ([], {}, False),
])
def test_review_reads_remain_within_tracked_checkout(tracked_review_root, tool, inputs, allowed):
    from scripts.agent_runtime.grok_reviewer_permissions import reviewer_tool_allowed

    assert reviewer_tool_allowed({
        "hook_event_name": "PreToolUse", "toolName": tool, "toolInput": inputs,
    }, tracked_review_root) is allowed


def test_read_guard_denies_absolute_and_symlink_escape(tracked_review_root):
    from scripts.agent_runtime.grok_reviewer_permissions import reviewer_tool_allowed

    outside = tracked_review_root.parent / "outside.txt"
    outside.write_text("private fixture", encoding="utf-8")
    (tracked_review_root / "escape.txt").symlink_to(outside)
    subprocess.run(["git", "add", "escape.txt"], cwd=tracked_review_root, check=True, timeout=30)
    for path in (str(outside), "../outside.txt", "escape.txt"):
        assert not reviewer_tool_allowed({
            "hook_event_name": "PreToolUse", "toolName": "read_file", "toolInput": {"target_file": path},
        }, tracked_review_root)


def test_read_guard_denies_unavailable_git(tracked_review_root, monkeypatch):
    from scripts.agent_runtime import grok_reviewer_permissions as policy

    def unavailable(*args, **kwargs):
        raise OSError("unavailable")
    monkeypatch.setattr(policy.subprocess, "run", unavailable)
    assert not policy.reviewer_tool_allowed({
        "hook_event_name": "PreToolUse", "toolName": "read_file", "toolInput": {"target_file": "tracked.txt"},
    }, tracked_review_root)


@pytest.mark.parametrize("event,expected", [
    (json.dumps({"hook_event_name": "PreToolUse", "toolName": "Bash", "toolInput": {"command": "pwd"}}), 0),
    ("broken json", 2),
    ("{}", 2),
])
def test_permission_cli_main_returns_typed_disposition(monkeypatch, capsys, tracked_review_root, event, expected):
    import io

    from scripts.agent_runtime import grok_reviewer_permissions as policy

    monkeypatch.setattr(sys, "argv", ["guard", "--review-root", str(tracked_review_root)])
    monkeypatch.setattr(sys, "stdin", io.StringIO(event))
    assert policy.main() == expected
    captured = capsys.readouterr()
    assert policy.REFUSAL_CODE in captured.err if expected else captured.err == ""


def test_tracked_symlink_loop_is_a_typed_denial(tracked_review_root):
    from scripts.agent_runtime import grok_reviewer_permissions as policy

    (tracked_review_root / "loop").symlink_to("loop")
    subprocess.run(["git", "add", "loop"], cwd=tracked_review_root, check=True, timeout=30)
    event = {"hook_event_name": "PreToolUse", "toolName": "read_file", "toolInput": {"target_file": "loop"}}
    assert not policy.reviewer_tool_allowed(event, tracked_review_root)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"),
         "--review-root", str(tracked_review_root)],
        input=json.dumps(event), capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 2
    assert result.stderr.startswith(policy.REFUSAL_CODE + ":")
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("error", [RuntimeError, PermissionError, MemoryError, KeyboardInterrupt, SystemExit])
def test_permission_boundary_denies_every_evaluation_exception(tracked_review_root, monkeypatch, capsys, error):
    import io

    from scripts.agent_runtime import grok_reviewer_permissions as policy

    def fail(*args, **kwargs):
        raise error("private error detail")

    event = {"hook_event_name": "PreToolUse", "toolName": "read_file", "toolInput": {"target_file": "tracked.txt"}}
    monkeypatch.setattr(Path, "open", fail)
    assert not policy.reviewer_tool_allowed(event, tracked_review_root)
    monkeypatch.setattr(sys, "argv", ["guard", "--review-root", str(tracked_review_root)])
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event)))
    assert policy.main() == 2
    captured = capsys.readouterr()
    assert captured.err.startswith(policy.REFUSAL_CODE + ":")
    assert "private error detail" not in captured.err


@pytest.mark.parametrize("error", [RuntimeError, PermissionError, MemoryError, KeyboardInterrupt])
def test_main_denies_interpreter_level_input_errors(tracked_review_root, monkeypatch, capsys, error):
    from scripts.agent_runtime import grok_reviewer_permissions as policy

    def fail(*args, **kwargs):
        raise error("private input error")

    monkeypatch.setattr(policy.json, "load", fail)
    monkeypatch.setattr(sys, "argv", ["guard", "--review-root", str(tracked_review_root)])
    assert policy.main() == 2
    assert capsys.readouterr().err.startswith(policy.REFUSAL_CODE + ":")


def test_guard_git_never_lazily_fetches(tracked_review_root, monkeypatch):
    from scripts.agent_runtime import grok_reviewer_permissions as policy

    calls = []
    real_run = policy.subprocess.run

    def record(argv, **kwargs):
        calls.append(argv)
        return real_run(argv, **kwargs)

    monkeypatch.setattr(policy.subprocess, "run", record)
    assert policy.reviewer_tool_allowed({
        "hook_event_name": "PreToolUse", "toolName": "read_file", "toolInput": {"target_file": "tracked.txt"},
    }, tracked_review_root)
    assert calls and all("--no-lazy-fetch" in argv for argv in calls)
    assert all("--no-lazy-fetch" in command for command in policy.GROK_REVIEWER_READ_COMMANDS if command.startswith("git "))


def test_unreadable_tracked_file_is_denied(tracked_review_root):
    from scripts.agent_runtime import grok_reviewer_permissions as policy

    target = tracked_review_root / "tracked.txt"
    target.chmod(0)
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"),
             "--review-root", str(tracked_review_root)],
            input=json.dumps({"hook_event_name": "PreToolUse", "toolName": "read_file",
                              "toolInput": {"target_file": "tracked.txt"}}),
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 2
        assert result.stderr.startswith(policy.REFUSAL_CODE + ":")
    finally:
        target.chmod(0o600)


def test_main_does_not_treat_evaluator_system_exit_as_help(monkeypatch, capsys, tracked_review_root):
    import io

    from scripts.agent_runtime import grok_reviewer_permissions as policy

    def fail(*args):
        raise SystemExit(0)

    monkeypatch.setattr(policy, "reviewer_tool_allowed", fail)
    monkeypatch.setattr(sys, "argv", ["guard", "--review-root", str(tracked_review_root)])
    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
    assert policy.main() == 2
    assert capsys.readouterr().err.startswith(policy.REFUSAL_CODE + ":")


def test_guard_help_does_not_require_a_review_event():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/agent_runtime/grok_reviewer_permissions.py"), "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0
    assert "Exit codes:" in result.stdout
