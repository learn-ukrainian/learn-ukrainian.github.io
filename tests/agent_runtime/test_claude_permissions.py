"""Command and deployed-hook coverage for headless Claude workers.

The fnmatch helper below is a model, not proof of the installed CLI matcher.
Evidence: installed Claude Code 2.1.288 ``claude --help``, ``claude doctor
--help`` and ``claude mcp --help`` expose no permission-evaluation-only command.
``--print`` runs a model turn; doctor checks installation/settings, and MCP
commands manage servers, not tool authorization. Thus a live matcher check
cannot be exercised through the documented CLI without a potentially paid
call. Set LU_LIVE_CLAUDE_PERMISSIONS=1 to opt into the isolated stub-server
test below. CI skips it by default; no real sources writer is ever launched.
"""

import asyncio
import fnmatch
import importlib.util
import io
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import (
    REVIEWER_PERMISSION_PROFILE,
    ClaudeAdapter,
)
from scripts.agent_runtime.env_sanitize import build_agent_env
from scripts.agent_runtime.review_mcp import review_tools_allowed_csv
from scripts.agent_runtime.sources_read_only import sources_tool_sets

SOURCES_READ_ONLY_TOOLS, SOURCES_PERSISTING_TOOLS = sources_tool_sets()
SOURCES_RULES = [f"mcp__sources__{name}" for name in SOURCES_READ_ONLY_TOOLS]
PERSISTING_RULES = [f"mcp__sources__{name}" for name in SOURCES_PERSISTING_TOOLS]
# Claude matches MCP rules against the configured server name, so writers are
# also denied under any name: a deny glob must match the whole tool name.
WRITER_DENIES = [*PERSISTING_RULES, *(f"mcp__*__{name}" for name in SOURCES_PERSISTING_TOOLS)]
ALTERNATE_SERVER_NAMES = ("sources_alias", "plugin_lu_sources", "srv")


def _claude_denies(rules: list[str], tool: str) -> bool:
    """Claude's documented deny match: an exact name, or a glob over the full tool name."""
    return any(fnmatch.fnmatchcase(tool, rule) for rule in rules)


@pytest.mark.live_network
@pytest.mark.skipif(os.environ.get("LU_LIVE_CLAUDE_PERMISSIONS") != "1", reason="opt-in paid Claude CLI matcher check")
def test_live_claude_reader_allowed_writer_denied(tmp_path: Path) -> None:
    """Require native permission-denial evidence and independent stub execution evidence."""
    binary = shutil.which("claude")
    assert binary is not None, "opted-in live test requires the installed Claude CLI"
    audit = tmp_path / "calls.jsonl"
    stub = tmp_path / "stub_sources.py"
    stub.write_text(
        "import json, sys\n"
        "from pathlib import Path\n"
        "from mcp.server.fastmcp import FastMCP\n"
        "mcp = FastMCP('permission-fixture')\n"
        "def record(name):\n"
        "    with Path(sys.argv[1]).open('a') as f: f.write(json.dumps(name) + '\\n')\n"
        "    return name\n"
        "@mcp.tool()\n"
        "def inspect_word(word: str) -> str:\n"
        "    return record('inspect_word')\n"
        "@mcp.tool()\n"
        "def query_wikipedia(query: str) -> str:\n"
        "    return record('query_wikipedia')\n"
        "mcp.run(transport='stdio')\n"
    )
    cmd = _reviewer_plan(tmp_path)
    # Keep the generated settings, allow/deny lists and dontAsk mode intact;
    # replace only the real server with harmless, independently logged tools.
    cmd[0] = binary
    cmd[cmd.index("--mcp-config") + 1] = json.dumps(
        {"mcpServers": {"sources": {"command": sys.executable, "args": [str(stub), str(audit)]}}}
    )
    cmd[cmd.index("--output-format") + 1] = "json"
    cmd.extend(["--setting-sources", "", "--no-session-persistence", "--max-turns", "4"])
    # stdin carries the prompt in the adapter's normal print invocation.
    proc = subprocess.run(
        cmd,
        input=(
            "Test only these two MCP tools. Call mcp__sources__inspect_word with word='fixture'. "
            "Then attempt mcp__sources__query_wikipedia with query='fixture' once, even if it is denied. "
            "Do not use other tools or substitute a tool."
        ),
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=90,
        env=build_agent_env(provider="claude"),
    )
    # Do not echo a paid response, credentials or stderr into public diagnostics.
    assert proc.returncode == 0, f"Claude live matcher process exited {proc.returncode}"
    result = json.loads(proc.stdout)
    assert result.get("is_error") is False
    assert audit.is_file(), "allowed read tool never reached the stub"
    assert set(json.loads(line) for line in audit.read_text().splitlines()) == {"inspect_word"}
    assert any(
        denial.get("tool_name") == "mcp__sources__query_wikipedia" for denial in result.get("permission_denials", [])
    ), "no native writer permission denial: a model refusing to call is insufficient evidence"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_claude_worker_modes_install_guards(mode: str, tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--bare" not in plan.cmd
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    hooks = settings["hooks"]["PreToolUse"]
    assert {"Bash", "Write|Edit|MultiEdit"} <= {group["matcher"] for group in hooks}
    commands = [hook["command"] for group in hooks for hook in group["hooks"]]
    tracked_hooks = Path(__file__).resolve().parents[2] / "agents_extensions/shared/hooks"
    for name in (
        "guard-primary-checkout-write.py",
        "guard-secret-print.py",
        "guard-pr-merge.py",
        "guard-branch-switch-in-main.py",
        "guard-admin-merge.py",
        "enforce-venv.sh",
        "heal-core-bare.py",
    ):
        assert str(tracked_hooks / name) in commands
    assert all(Path(command).is_file() for command in commands)
    assert str(tracked_hooks / "guard-reviewer-publish.py") not in commands
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
    if mode == "read-only":
        assert plan.cmd.count("--disallowedTools") == 1
        assert plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",") == WRITER_DENIES
    else:
        assert "--disallowedTools" not in plan.cmd
    if mode == "workspace-write":
        # Headless print mode denies approval-requiring tools. dontAsk plus the
        # worker allow list is the documented non-interactive mode. Danger keeps
        # its own flag and must not grow a --permission-mode.
        assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
        granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        assert granted == [
            "Bash",
            "Read",
            "Edit",
            "Write",
            "Grep",
            "Glob",
            "LS",
            "WebFetch",
            "WebSearch",
        ]
        assert "NotebookEdit" not in granted
        assert not any(name.startswith("mcp__") for name in granted)
        assert plan.cmd.count("--allowedTools") == 1
        assert "--dangerously-skip-permissions" not in plan.cmd
    else:
        assert "--permission-mode" not in plan.cmd
        assert "--allowedTools" not in plan.cmd
        assert ("--dangerously-skip-permissions" in plan.cmd) is (mode == "danger")


def test_workspace_write_keeps_explicit_allowed_tools(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"allowed_tools": "mcp__sources__*"},
    )
    assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
    assert plan.cmd.count("--allowedTools") == 1
    assert plan.cmd[plan.cmd.index("--allowedTools") + 1] == "mcp__sources__*"
    assert "Bash" not in plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "--disallowedTools" not in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd


def test_workspace_write_names_mcp_servers_from_config(tmp_path: Path) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(
        json.dumps({"mcpServers": {"sources": {}, "other_tool": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(config)},
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__sources__*" in granted
    assert "mcp__other_tool__*" in granted
    assert "mcp__sources" not in granted
    assert "NotebookEdit" not in granted


def test_workspace_write_mcp_config_comes_from_worker_cwd(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"worker_only": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__worker_only__*" in granted
    assert "mcp__sources__*" not in granted


def test_explicit_mcp_config_path_wins_over_worker_cwd(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"from_cwd": {}}}),
        encoding="utf-8",
    )
    explicit = tmp_path / "explicit.json"
    explicit.write_text(
        json.dumps({"mcpServers": {"from_explicit": {}}}),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(explicit)},
    )
    granted = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_explicit__*" in granted
    assert "mcp__from_cwd__*" not in granted

    missing = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"mcp_config_path": str(tmp_path / "absent.json")},
    )
    missing_granted = missing.cmd[missing.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__from_cwd__*" not in missing_granted
    assert not any(name.startswith("mcp__") for name in missing_granted)


def test_workspace_write_rejects_invalid_mcp_config(tmp_path: Path) -> None:
    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    shaped = tmp_path / "shaped"
    shaped.mkdir()
    (shaped / ".mcp.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="mcpServers"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=shaped,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )


def test_workspace_write_rejects_unreadable_mcp_config(tmp_path: Path) -> None:
    config = tmp_path / ".mcp.json"
    config.write_text('{"mcpServers": {}}\n', encoding="utf-8")
    config.chmod(0)
    try:
        with pytest.raises(ValueError, match="unreadable"):
            ClaudeAdapter().build_invocation(
                prompt="inspect",
                mode="workspace-write",
                cwd=tmp_path,
                model=None,
                task_id=None,
                session_id=None,
                tool_config=None,
            )
    finally:
        config.chmod(0o644)


def test_workspace_write_rejects_inexpressible_mcp_server_name(tmp_path: Path) -> None:
    config = tmp_path / "mcp.json"
    config.write_text(
        json.dumps({"mcpServers": {"ok": {}, "bad,name": {}}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="cannot be expressed"):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"mcp_config_path": str(config)},
        )


def test_reviewer_tools_opt_in_installs_profile(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    assert plan.cmd[plan.cmd.index("--permission-mode") + 1] == "dontAsk"
    sources_read = {f"mcp__sources__{name}" for name in SOURCES_READ_ONLY_TOOLS}
    assert set(REVIEWER_PERMISSION_PROFILE["allow"]) | sources_read == set(
        plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    )
    assert set(REVIEWER_PERMISSION_PROFILE["deny"]) | set(WRITER_DENIES) == set(
        plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
    )
    assert plan.env_overrides["LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK"] == "1"
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)


def test_discussion_readonly_keeps_separate_permissions(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"discussion_readonly": True},
    )
    assert "--settings" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--allowedTools" not in plan.cmd
    assert _denied(plan.cmd) == WRITER_DENIES
    assert plan.cmd[plan.cmd.index("--tools") + 1] == "Read,Grep,Glob,LS"
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides


def test_review_isolation_keeps_separate_permissions(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters import claude
    from scripts.review import isolation

    mcp = tmp_path / "empty.json"
    mcp.write_text('{"mcpServers":{}}\n', encoding="utf-8")
    monkeypatch.setattr(isolation, "validated_review_write_root", lambda _: tmp_path)
    monkeypatch.setattr(claude, "_isolated_review_response_schema", lambda _: "{}")
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "review_isolation": True,
            "review_engine_binary": "/bin/true",
            "strict_mcp_config": True,
            "mcp_config_path": str(mcp),
            "setting_sources": "",
            "allowed_tools": "",
        },
    )
    assert "--settings" in plan.cmd
    assert "--safe-mode" in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert "--allowedTools" not in plan.cmd
    assert _denied(plan.cmd) == WRITER_DENIES
    assert plan.cmd[plan.cmd.index("--tools") + 1] == ""


@pytest.mark.repo_wide
def test_tracked_hooks_work_in_fresh_clone_without_deployed_claude(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters import claude

    # Fixture clone of the tracked hook tree. Cloning this repository
    # (`git clone --shared`) exceeds the 30s bound when the host is busy (#8947).
    root = Path(__file__).resolve().parents[2]
    seed = tmp_path / "fixture"
    clone = tmp_path / "fresh"
    seed.mkdir()
    tracked_claude = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "--name-only", "HEAD", ".claude"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert tracked_claude.stdout == ""
    archived = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "archive",
            "--format=tar",
            "HEAD",
            "agents_extensions/shared/settings.json",
            "agents_extensions/shared/hooks",
            "scripts/agent_runtime/adapters/claude.py",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    with tarfile.open(fileobj=io.BytesIO(archived.stdout), mode="r|") as bundle:
        bundle.extractall(seed, filter="data")
    for args in (
        ["init"],
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.invalid"],
        ["add", "agents_extensions", "scripts"],
        ["commit", "-m", "fixture"],
    ):
        subprocess.run(["git", "-C", str(seed), *args], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "clone", str(seed), str(clone)], check=True, capture_output=True, timeout=30)
    assert not (clone / ".claude").exists()
    monkeypatch.setattr(claude, "__file__", str(clone / "scripts/agent_runtime/adapters/claude.py"))
    settings = json.loads(claude._worker_guard_settings(publish_guard=True))
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert str(clone / "agents_extensions/shared/hooks/guard-reviewer-publish.py") in commands
    assert all(Path(command).is_file() for command in commands)


_ROOT = Path(__file__).resolve().parents[2]
_WRAPPER = 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh"'
_PINNED_GUARDS = ("guard-pr-merge.py", "guard-admin-merge.py", "guard-branch-switch-in-main.py")


def _guard_source_tree(root: Path, commands: list[str], *, interpreter: bool = True) -> Path:
    """A checkout-shaped tree whose settings name ``commands`` as Bash PreToolUse hooks."""
    hooks = root / "agents_extensions/shared/hooks"
    hooks.mkdir(parents=True)
    for name in ("enforce-venv.sh", "guard-secret-print.py", *_PINNED_GUARDS):
        (hooks / name).write_text("#!/bin/sh\n", encoding="utf-8")
    groups = [{"matcher": "Bash", "hooks": [{"type": "command", "command": c, "timeout": 7} for c in commands]}]
    (root / "agents_extensions/shared/settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": groups}}), encoding="utf-8"
    )
    if interpreter:
        python = root / ".venv/bin/python"
        python.parent.mkdir(parents=True)
        python.write_text("", encoding="utf-8")
    return hooks


def _settings_from(root: Path, monkeypatch) -> list[dict]:
    from scripts.agent_runtime.adapters import claude

    monkeypatch.setattr(claude, "__file__", str(root / "scripts/agent_runtime/adapters/claude.py"))
    settings = json.loads(claude._worker_guard_settings())
    return [hook for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]


def test_worker_guards_run_parser_guards_under_the_project_interpreter(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters.claude import PROJECT_PYTHON_GUARDS

    assert set(_PINNED_GUARDS) == PROJECT_PYTHON_GUARDS
    hooks_dir = _guard_source_tree(
        tmp_path,
        [
            "$CLAUDE_PROJECT_DIR/.claude/hooks/enforce-venv.sh",
            *(f"{_WRAPPER} {name}" for name in _PINNED_GUARDS),
            "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-secret-print.py",
            "sh -c 'entire hooks claude-code pre-task || true'",
        ],
    )
    hooks = _settings_from(tmp_path, monkeypatch)
    python = str(tmp_path / ".venv/bin/python")
    assert [hook["command"] for hook in hooks] == [
        str(hooks_dir / "enforce-venv.sh"),
        *(shlex.join([python, str(hooks_dir / name)]) for name in _PINNED_GUARDS),
        str(hooks_dir / "guard-secret-print.py"),
    ]
    assert all(hook["timeout"] == 7 and hook["type"] == "command" for hook in hooks)


_SPLIT_WRAPPER = 'bash "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-"hook.sh'
_ESCAPED_WRAPPER = r"bash $CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python\-hook.sh"


@pytest.mark.parametrize(
    "command",
    [
        f"{_SPLIT_WRAPPER} guard-pr-merge.py",
        f"{_WRAPPER} 'guard-pr-'merge.py",
        f"{_ESCAPED_WRAPPER} guard\\-pr-merge.py",
        f'{_WRAPPER} "guard-pr-merge.py"',
    ],
)
def test_worker_guards_classify_the_wrapper_after_tokenization(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    [hook] = _settings_from(tmp_path, monkeypatch)
    assert hook["command"] == shlex.join([str(tmp_path / ".venv/bin/python"), str(hooks_dir / "guard-pr-merge.py")])


@pytest.mark.parametrize(
    "command",
    [
        '"$CLAUDE_PROJECT_DIR/.claude/hooks/guard-secret-"print.py',
        r"$CLAUDE_PROJECT_DIR/.claude/hooks/guard\-secret-print.py",
    ],
)
def test_worker_guards_classify_the_plain_path_after_tokenization(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    [hook] = _settings_from(tmp_path, monkeypatch)
    assert hook["command"] == str(hooks_dir / "guard-secret-print.py")


@pytest.mark.parametrize(
    "command",
    [
        "sh -c 'entire hooks claude-code pre-task || true'",
        "echo hello",
        "",
    ],
)
def test_worker_guards_leave_unrelated_hooks_untouched(tmp_path: Path, command: str) -> None:
    from scripts.agent_runtime.adapters.claude import _worker_guard_invocation

    assert _worker_guard_invocation(command, tmp_path) is None


@pytest.mark.parametrize(
    "command",
    [
        # Unknown guard, extra or missing arguments in the canonical spelling.
        f"{_WRAPPER} guard-secret-print.py",
        f"{_WRAPPER} guard-pr-merge.py --extra",
        f"{_WRAPPER} ../hooks/guard-pr-merge.py",
        f"{_WRAPPER}",
        # The same defects behind split quoting and backslash spellings.
        f"{_SPLIT_WRAPPER} guard-pr-merge.py --extra",
        f"{_SPLIT_WRAPPER}",
        f"{_SPLIT_WRAPPER} guard-secret-print.py",
        f"{_ESCAPED_WRAPPER} guard-pr-merge.py extra",
        f"{_ESCAPED_WRAPPER}",
        f"{_WRAPPER} 'guard-pr-'merge.py --extra",
        # Another launcher, wrapper path or nesting.
        'sh "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh" guard-pr-merge.py',
        '"$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh" guard-pr-merge.py',
        'bash "/elsewhere/run-project-python-hook.sh" guard-pr-merge.py',
        "sh -c 'bash \"$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh\" guard-pr-merge.py'",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/run-project-python-hook.sh",
        # A parser guard or the hooks directory outside both supported forms.
        "/usr/bin/python3 'guard-pr-'merge.py",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-pr-merge.py --extra",
        "bash $CLAUDE_PROJECT_DIR/.claude/hooks/enforce-venv.sh",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/../hooks/guard-pr-merge.py",
        "$CLAUDE_PROJECT_DIR/.claude/hooks/",
    ],
)
def test_worker_guards_refuse_other_fleet_guard_forms(tmp_path: Path, monkeypatch, command: str) -> None:
    _guard_source_tree(tmp_path, [command])
    with pytest.raises(RuntimeError, match="Claude worker guard has an unsupported form"):
        _settings_from(tmp_path, monkeypatch)


@pytest.mark.parametrize(
    "command",
    [f"{_WRAPPER} 'guard-pr-merge.py", "sh -c 'entire hooks claude-code pre-task"],
)
def test_worker_guards_refuse_an_unreadable_hook_command(tmp_path: Path, monkeypatch, command: str) -> None:
    _guard_source_tree(tmp_path, [command])
    with pytest.raises(RuntimeError, match="unreadable"):
        _settings_from(tmp_path, monkeypatch)


def test_grok_agent_definition_keeps_a_split_quoted_parser_guard(tmp_path: Path, monkeypatch) -> None:
    from scripts.agent_runtime.adapters.grok_build import _guard_agent_definition

    hooks_dir = _guard_source_tree(tmp_path, [f"{_SPLIT_WRAPPER} guard-pr-merge.py"])
    _settings_from(tmp_path, monkeypatch)  # points the adapter at the fixture tree
    definition = _guard_agent_definition(
        name="probe", description="probe", body="probe", publish_guard=False, native_aliases=False
    )
    pinned = shlex.join([str(tmp_path / ".venv/bin/python"), str(hooks_dir / "guard-pr-merge.py")])
    bridge = shlex.quote(str(_ROOT / "scripts/agent_runtime/grok_hook_bridge.py"))
    assert json.dumps(f"{bridge} {shlex.quote(pinned)}") in definition


@pytest.mark.parametrize(
    "command",
    [f"{_WRAPPER} guard-pr-merge.py", "$CLAUDE_PROJECT_DIR/.claude/hooks/guard-pr-merge.py"],
)
def test_worker_guards_refuse_a_missing_guard_file(tmp_path: Path, monkeypatch, command: str) -> None:
    hooks_dir = _guard_source_tree(tmp_path, [command])
    (hooks_dir / "guard-pr-merge.py").unlink()
    with pytest.raises(RuntimeError, match="Claude worker guard unavailable"):
        _settings_from(tmp_path, monkeypatch)


def test_worker_guards_fail_closed_without_a_project_interpreter(tmp_path: Path, monkeypatch) -> None:
    # No .venv in the tree, and the running interpreter belongs to another checkout.
    root = tmp_path / "checkout"
    _guard_source_tree(root, [f"{_WRAPPER} guard-pr-merge.py"], interpreter=False)
    foreign = tmp_path / "other/.venv/bin/python"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(foreign))
    with pytest.raises(FileNotFoundError, match="project interpreter not found"):
        _settings_from(root, monkeypatch)


def test_readonly_transport_rejects_every_push_wrapper(tmp_path: Path) -> None:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True, timeout=30)
    subprocess.run(["git", "init", str(work)], check=True, capture_output=True, timeout=30)
    (work / "sample.txt").write_text("sample\n", encoding="utf-8")
    for args in (
        ["config", "user.name", "Test"],
        ["config", "user.email", "test@example.invalid"],
        ["add", "sample.txt"],
        ["commit", "-m", "fixture"],
        ["remote", "add", "origin", str(remote)],
        ["config", "remote.origin.push", "HEAD:refs/heads/probe"],
    ):
        subprocess.run(["git", "-C", str(work), *args], check=True, capture_output=True, timeout=30)

    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=work,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    assert (
        subprocess.run(
            ["git", "-C", str(work), "status", "--porcelain"], env=env, capture_output=True, timeout=30
        ).returncode
        == 0
    )
    assert (
        subprocess.run(
            ["git", "-C", str(work), "ls-remote", "origin"], env=env, capture_output=True, timeout=30
        ).returncode
        == 0
    )
    for command, cwd in (
        (["git", "push"], work),
        (["git", "-C", str(work), "push"], tmp_path),
        (["bash", "-c", "git push"], work),
        (
            [sys.executable, "-c", "import subprocess; raise SystemExit(subprocess.run(['git','push']).returncode)"],
            work,
        ),
    ):
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode != 0, (command, result.stdout, result.stderr)
        refs = subprocess.run(
            ["git", "--git-dir", str(remote), "for-each-ref", "--format=%(refname)"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        assert refs.stdout == ""


@pytest.mark.parametrize(
    ("command", "blocked"),
    [
        ("git push", True),
        ("git -C /tmp/example push --dry-run", True),
        ("git -c core.quotePath=false push", True),
        ("env X=1 git push", True),
        ("bash -c 'git push'", True),
        ("sh -c 'gh api -f body=probe repos/o/r/issues/1/comments'", True),
        ("eval 'gh pr merge 1'", True),
        ("gh issue reopen 1", True),
        ("gh pr create --help", True),
        ("gh api --method PATCH repos/o/r", True),
        ("gh api -X POST repos/o/r", True),
        ("gh api --raw-field body=x repos/o/r", True),
        ("gh release create v1", True),
        ("gh workflow run ci.yml", True),
        ("gh pr view 1 --json number", False),
        ("gh api -X GET repos/o/r", False),
        ("git status --short", False),
    ],
)
def test_reviewer_publish_hook(command: str, blocked: bool) -> None:
    hook = Path(__file__).resolve().parents[2] / "agents_extensions/shared/hooks/guard-reviewer-publish.py"
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run([sys.executable, str(hook)], input=payload, capture_output=True, text=True, timeout=30)
    assert (result.returncode == 2) is blocked, (command, result.stderr)


SOURCES_SERVER_PATH = Path(__file__).resolve().parents[2] / ".mcp/servers/sources/server.py"


def _reviewer_plan(cwd: Path, **extra) -> list[str]:
    return (
        ClaudeAdapter()
        .build_invocation(
            prompt="inspect",
            mode="read-only",
            cwd=cwd,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"reviewer_tools": True, **extra},
        )
        .cmd
    )


def _granted(cmd: list[str]) -> list[str]:
    assert cmd.count("--allowedTools") == 1
    return cmd[cmd.index("--allowedTools") + 1].split(",")


def _denied(cmd: list[str]) -> list[str]:
    assert cmd.count("--disallowedTools") == 1
    return cmd[cmd.index("--disallowedTools") + 1].split(",")


def _mcp_config(cmd: list[str]) -> dict:
    """The one MCP config the argv loads; it must be strict so nothing else is merged in."""
    assert cmd.count("--mcp-config") == 1
    assert cmd.count("--strict-mcp-config") == 1
    index = cmd.index("--mcp-config")
    assert cmd[index - 1] == "--strict-mcp-config"
    return json.loads(cmd[index + 1])


def test_sources_tool_split_matches_server_annotations() -> None:
    """Granted tools are exactly the read-only ones; persisting ones are exactly the rest (#9551).

    tests/mcp/test_sources_tool_side_effects.py ties the annotations to the writes each tool attempts.
    """
    spec = importlib.util.spec_from_file_location("sources_server_contract", SOURCES_SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    tools = asyncio.run(server.list_tools())
    assert sorted(tool.name for tool in tools if tool.annotations.read_only_hint is True) == list(
        SOURCES_READ_ONLY_TOOLS
    )
    assert sorted(tool.name for tool in tools if tool.annotations.read_only_hint is False) == list(
        SOURCES_PERSISTING_TOOLS
    )
    assert "query_wikipedia" in SOURCES_PERSISTING_TOOLS
    assert all(tool.annotations.destructive_hint is False for tool in tools)


def test_reviewer_loads_only_the_trusted_sources_server(tmp_path: Path) -> None:
    from scripts.agent_runtime.review_mcp import (
        isolated_sources_mcp_config,
        review_server_checkout,
        sources_server_launch,
    )
    from scripts.common.repo_root import project_interpreter

    cmd = _reviewer_plan(tmp_path)
    config = _mcp_config(cmd)
    assert config == isolated_sources_mcp_config(*sources_server_launch())
    server = config["mcpServers"]["sources"]
    assert list(config["mcpServers"]) == ["sources"]
    # tests/agent_runtime/test_review_mcp.py launches this under a hostile session environment.
    assert server == {
        "command": "/usr/bin/env",
        "args": [
            "-i",
            "PATH=/usr/bin:/bin",
            "LC_ALL=C.UTF-8",
            str(project_interpreter()),
            "-I",
            str(review_server_checkout() / ".mcp" / "servers" / "sources" / "server.py"),
        ],
    }
    granted = _granted(cmd)
    assert granted == [*REVIEWER_PERMISSION_PROFILE["allow"], *SOURCES_RULES]
    assert "mcp__sources__*" not in granted
    assert not set(PERSISTING_RULES) & set(granted)
    # Deny outranks any allow rule a reviewed checkout's settings file could add.
    assert _denied(cmd) == [*REVIEWER_PERMISSION_PROFILE["deny"], *WRITER_DENIES]
    assert "mcp__sources__query_wikipedia" in _denied(cmd)
    assert not {"Edit", "Write", "NotebookEdit", "MultiEdit"} & set(granted)
    assert cmd[cmd.index("--permission-mode") + 1] == "dontAsk"
    settings = json.loads(cmd[cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert any(command.endswith("guard-reviewer-publish.py") for command in commands)
    assert any(command.endswith("guard-primary-checkout-write.py") for command in commands)


@pytest.mark.parametrize(
    "worktree_config",
    [
        {"mcpServers": {"sources": {"type": "streamable-http", "url": "http://127.0.0.1:9/mcp"}}},
        {"mcpServers": {"sources": {"command": "/bin/sh", "args": ["-c", "write-anything"]}}},
        {"mcpServers": {"sources": {"command": "python", "args": ["evil_server.py"]}, "other_tool": {}}},
        {"mcpServers": {"other_tool": {"command": "python", "args": ["other.py"]}}},
        "{not json",
    ],
    ids=["sources-url", "sources-command", "sources-plus-other", "other-only", "invalid"],
)
def test_worktree_mcp_json_gains_the_reviewer_nothing(tmp_path: Path, worktree_config) -> None:
    """A reviewed branch's .mcp.json never reaches the reviewer argv, whatever it names `sources` (#9551)."""
    clean = tmp_path / "clean"
    clean.mkdir()
    reviewed = tmp_path / "reviewed"
    reviewed.mkdir()
    text = worktree_config if isinstance(worktree_config, str) else json.dumps(worktree_config)
    (reviewed / ".mcp.json").write_text(text, encoding="utf-8")
    cmd = _reviewer_plan(reviewed)
    assert cmd == _reviewer_plan(clean)
    joined = "\n".join(cmd)
    for planted in ("127.0.0.1:9", "/bin/sh", "evil_server.py", "other_tool", "other.py"):
        assert planted not in joined
    assert not any(name.startswith("mcp__other_tool") for name in _granted(cmd))


def test_reviewer_refuses_a_caller_mcp_config_outside_formal_full_access(tmp_path: Path) -> None:
    config = tmp_path / "sources.json"
    config.write_text(json.dumps({"mcpServers": {"sources": {"command": "/bin/sh"}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="formal full-access"):
        _reviewer_plan(tmp_path, mcp_config_path=str(config))
    with pytest.raises(ValueError, match="formal full-access"):
        _reviewer_plan(tmp_path, mcp_config_path=str(config), review_access="isolated")


def test_full_review_access_keeps_review_tool_set(tmp_path: Path) -> None:
    from scripts.agent_runtime.review_mcp import review_tools_allowed_csv

    (tmp_path / ".mcp.json").write_text("{", encoding="utf-8")  # never read for formal attempts
    attempt = tmp_path / "attempt.json"
    cmd = _reviewer_plan(tmp_path, mcp_config_path=str(attempt), strict_mcp_config=True, review_access="full")
    assert _granted(cmd) == [
        *REVIEWER_PERMISSION_PROFILE["allow"],
        *review_tools_allowed_csv("claude", "full").split(","),
    ]
    # Deny wins over the formal allow list: a writer added to it stays denied.
    assert _denied(cmd) == [*REVIEWER_PERMISSION_PROFILE["deny"], *WRITER_DENIES]
    # The formal attempt's own harness-written config is the only one loaded.
    assert cmd.count("--mcp-config") == 1
    assert cmd[cmd.index("--mcp-config") + 1] == str(attempt)
    assert cmd[cmd.index("--mcp-config") - 1] == "--strict-mcp-config"


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_sources_config_leaves_write_and_danger_argv_unchanged(tmp_path: Path, mode: str) -> None:
    (tmp_path / ".mcp.json").write_text(json.dumps({"mcpServers": {"sources": {}}}), encoding="utf-8")
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"reviewer_tools": True},
    )
    assert "--disallowedTools" not in plan.cmd
    assert not any(rule in plan.cmd for rule in SOURCES_RULES)
    if mode == "workspace-write":
        assert _granted(plan.cmd) == [
            "Bash",
            "Read",
            "Edit",
            "Write",
            "Grep",
            "Glob",
            "LS",
            "WebFetch",
            "WebSearch",
            "mcp__sources__*",
        ]
    else:
        assert "--allowedTools" not in plan.cmd
        assert "--dangerously-skip-permissions" in plan.cmd


@pytest.mark.parametrize("allowed_tools", ["mcp__sources__*", "Read,Bash(git push *)", ""])
@pytest.mark.parametrize("strict_mcp_config", [False, True])
def test_explicit_allowed_tools_are_not_widened_or_narrowed(
    tmp_path: Path,
    allowed_tools: str,
    strict_mcp_config: bool,
) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "reviewer_tools": True,
            "allowed_tools": allowed_tools,
            "mcp_config_path": str(tmp_path / "sources.json"),
            "strict_mcp_config": strict_mcp_config,
        },
    )
    assert plan.cmd.count("--allowedTools") == 1
    assert plan.cmd[plan.cmd.index("--allowedTools") + 1] == allowed_tools
    assert "--permission-mode" not in plan.cmd
    # Only the sources writers are added; the reviewer deny list is not.
    assert _denied(plan.cmd) == WRITER_DENIES
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    commands = [hook["command"] for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]
    assert not any(command.endswith("guard-reviewer-publish.py") for command in commands)


def test_readonly_without_profile_keeps_legacy_permissions_and_denies_writers(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="write content",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={},
    )
    assert "--allowedTools" not in plan.cmd
    assert "--permission-mode" not in plan.cmd
    assert _denied(plan.cmd) == WRITER_DENIES
    assert "LU_CLAUDE_READ_ONLY_GIT_PUSH_BLOCK" not in plan.env_overrides


def _isolated_review_config(tmp_path: Path, monkeypatch) -> dict:
    from scripts.agent_runtime.adapters import claude
    from scripts.review import isolation

    mcp = tmp_path / "empty.json"
    mcp.write_text('{"mcpServers":{}}\n', encoding="utf-8")
    monkeypatch.setattr(isolation, "validated_review_write_root", lambda _: tmp_path)
    monkeypatch.setattr(claude, "_isolated_review_response_schema", lambda _: "{}")
    return {
        "review_isolation": True,
        "review_engine_binary": "/bin/true",
        "strict_mcp_config": True,
        "mcp_config_path": str(mcp),
        "setting_sources": "",
        "allowed_tools": "Read,Grep,Glob",
    }


# Every read-only route a caller can reach, as a tool_config builder.
READ_ONLY_PATHS = {
    "ordinary-reviewer": lambda tmp, _mp: {"reviewer_tools": True},
    "formal-full-review": lambda tmp, _mp: {
        "reviewer_tools": True,
        "mcp_config_path": str(tmp / "attempt.json"),
        "strict_mcp_config": True,
        "review_access": "full",
    },
    "formal-isolated-review": lambda tmp, _mp: {
        "allowed_tools": review_tools_allowed_csv("claude"),
        "mcp_config_path": str(tmp / "attempt.json"),
        "strict_mcp_config": True,
        "review_access": "isolated",
    },
    "explicit-sources-glob": lambda tmp, _mp: {"allowed_tools": "mcp__sources__*"},
    "explicit-writer-grant": lambda tmp, _mp: {"allowed_tools": ",".join(["Read", *PERSISTING_RULES])},
    "explicit-with-reviewer-tools": lambda tmp, _mp: {
        "reviewer_tools": True,
        "allowed_tools": "mcp__sources__*",
        "mcp_config_path": str(tmp / "sources.json"),
        "strict_mcp_config": True,
    },
    "ad-hoc-none": lambda tmp, _mp: None,
    "ad-hoc-empty": lambda tmp, _mp: {},
    "ad-hoc-mcp-config": lambda tmp, _mp: {"mcp_config_path": str(tmp / "sources.json")},
    "discussion-readonly": lambda tmp, _mp: {"discussion_readonly": True},
    "discussion-with-reviewer-tools": lambda tmp, _mp: {"discussion_readonly": True, "reviewer_tools": True},
    "review-isolation": _isolated_review_config,
}


@pytest.mark.parametrize("session_id", [None, "00000000-0000-4000-8000-000000000000"])
@pytest.mark.parametrize("path", sorted(READ_ONLY_PATHS))
def test_every_read_only_path_denies_every_sources_writer(
    tmp_path: Path, monkeypatch, path: str, session_id: str | None
) -> None:
    """AC-01 (#9560): deny is a single list on every read-only argv; Claude applies deny before allow."""
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session_id,
        tool_config=READ_ONLY_PATHS[path](tmp_path, monkeypatch),
    )
    denied = _denied(plan.cmd)
    assert set(PERSISTING_RULES) <= set(denied)
    # Readers are never denied: ordinary lookups keep working.
    assert not set(SOURCES_RULES) & set(denied)
    # The same holds whatever name the server is registered under.
    for server in ALTERNATE_SERVER_NAMES:
        assert all(_claude_denies(denied, f"mcp__{server}__{name}") for name in SOURCES_PERSISTING_TOOLS)
        assert not any(_claude_denies(denied, f"mcp__{server}__{name}") for name in SOURCES_READ_ONLY_TOOLS)
    if "--allowedTools" in plan.cmd and path != "explicit-writer-grant":
        # The adapter itself never grants a writer; only a caller's own list can name one.
        assert not set(PERSISTING_RULES) & set(_granted(plan.cmd))


def _alias_sources_config(path: Path, server: str) -> Path:
    """An MCP config that registers the real sources launcher under ``server``."""
    from scripts.agent_runtime.review_mcp import isolated_sources_mcp_config, sources_server_launch

    launch = isolated_sources_mcp_config(*sources_server_launch())["mcpServers"]["sources"]
    path.write_text(json.dumps({"mcpServers": {server: launch}}), encoding="utf-8")
    return path


@pytest.mark.parametrize("strict_mcp_config", [False, True])
@pytest.mark.parametrize("server", ALTERNATE_SERVER_NAMES)
@pytest.mark.parametrize("session", ["fresh", "resumed"])
def test_explicit_config_alternate_server_name_cannot_expose_a_writer(
    tmp_path: Path, server: str, session: str, strict_mcp_config: bool
) -> None:
    """Review blocker (#9560): an explicit config naming sources otherwise escapes ``mcp__sources__<writer>``."""
    config = _alias_sources_config(tmp_path / "alias.json", server)
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id="00000000-0000-4000-8000-000000000000",
        tool_config={
            "is_new_session": session == "fresh",
            "mcp_config_path": str(config),
            "strict_mcp_config": strict_mcp_config,
            "allowed_tools": f"mcp__{server}__*",
        },
    )
    assert ("--session-id" if session == "fresh" else "--resume") in plan.cmd
    assert plan.cmd[plan.cmd.index("--mcp-config") + 1] == str(config)
    denied = _denied(plan.cmd)
    for name in SOURCES_PERSISTING_TOOLS:
        assert _claude_denies(denied, f"mcp__{server}__{name}"), name
    # Readers under the alias stay allowed by the caller's glob and are not denied.
    assert _granted(plan.cmd) == [f"mcp__{server}__*"]
    for name in SOURCES_READ_ONLY_TOOLS:
        assert not _claude_denies(denied, f"mcp__{server}__{name}"), name


@pytest.mark.parametrize("tool_config", [None, {"allowed_tools": "mcp__sources_alias__*"}, {"reviewer_tools": True}])
def test_settings_provided_alternate_server_name_cannot_expose_a_writer(tmp_path: Path, tool_config) -> None:
    """A checkout's ``.mcp.json`` and settings can register and allow sources under another name.

    The adapter never reads those files for a read-only run; the deny covers every server name instead.
    """
    _alias_sources_config(tmp_path / ".mcp.json", "sources_alias")
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "enabledMcpjsonServers": ["sources_alias"],
                "permissions": {"allow": ["mcp__sources_alias__*"]},
            }
        ),
        encoding="utf-8",
    )
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=tool_config,
    )
    denied = _denied(plan.cmd)
    for name in SOURCES_PERSISTING_TOOLS:
        assert _claude_denies(denied, f"mcp__sources_alias__{name}"), name
    for name in SOURCES_READ_ONLY_TOOLS:
        assert not _claude_denies(denied, f"mcp__sources_alias__{name}"), name


def test_any_server_writer_deny_leaves_longer_reader_names_alone() -> None:
    """``mcp__*__query_ulif`` must match the whole name, so ``query_ulif_records`` stays reachable."""
    denies = [f"mcp__*__{name}" for name in SOURCES_PERSISTING_TOOLS]
    assert "query_ulif_records" in SOURCES_READ_ONLY_TOOLS
    assert _claude_denies(denies, "mcp__sources_alias__query_ulif")
    assert not _claude_denies(denies, "mcp__sources_alias__query_ulif_records")


def test_ad_hoc_discuss_env_denies_every_sources_writer(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("AB_DISCUSS_READONLY", "1")
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert _denied(plan.cmd) == WRITER_DENIES


def test_readers_stay_allowed_where_they_were(tmp_path: Path) -> None:
    """AC-02 (#9560): the ordinary reviewer keeps every reader; the formal full reviewer keeps its contract."""
    from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS

    ordinary = _reviewer_plan(tmp_path)
    assert set(SOURCES_RULES) <= set(_granted(ordinary))
    assert "mcp__sources__verify_word" in _granted(ordinary)
    full = _reviewer_plan(
        tmp_path,
        mcp_config_path=str(tmp_path / "attempt.json"),
        strict_mcp_config=True,
        review_access="full",
    )
    full_rules = {f"mcp__sources__{name}" for name in FULL_REVIEW_TOOLS}
    assert full_rules <= set(_granted(full))
    assert not full_rules & set(_denied(full))


@pytest.mark.parametrize(
    "tool_config",
    [
        None,
        {"reviewer_tools": True},
        {"allowed_tools": "mcp__sources__*"},
        {"allowed_tools": ",".join(PERSISTING_RULES)},
    ],
    ids=["none", "reviewer-tools", "explicit-glob", "explicit-writers"],
)
@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_write_and_danger_modes_never_deny_sources_writers(tmp_path: Path, mode: str, tool_config) -> None:
    """AC-02 (#9560): builds and writers keep their cache access."""
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=tool_config,
    )
    assert "--disallowedTools" not in plan.cmd
    if tool_config and "allowed_tools" in tool_config:
        assert _granted(plan.cmd) == tool_config["allowed_tools"].split(",")
    elif mode == "danger":
        assert "--allowedTools" not in plan.cmd
    else:
        assert "Bash" in _granted(plan.cmd)


@pytest.mark.parametrize("tool_config", [None, {"reviewer_tools": True}, {"allowed_tools": "mcp__sources__*"}])
def test_unreadable_server_declarations_refuse_read_only_launch(tmp_path: Path, monkeypatch, tool_config) -> None:
    from scripts.agent_runtime.adapters import claude

    monkeypatch.setattr(claude, "sources_tool_sets", lambda: sources_tool_sets(tmp_path / "missing.py"))
    with pytest.raises(FileNotFoundError):
        ClaudeAdapter().build_invocation(
            prompt="inspect",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=tool_config,
        )
    # Write mode never reads the declarations, so it is unaffected.
    plan = ClaudeAdapter().build_invocation(
        prompt="inspect",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=None,
    )
    assert "--disallowedTools" not in plan.cmd
