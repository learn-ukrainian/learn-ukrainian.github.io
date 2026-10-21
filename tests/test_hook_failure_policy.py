"""Hook fail-closed contract (#10848): no agent guard may be skipped by failing.

Claude Code lets a PreToolUse tool call proceed when its command hook times
out, crashes or cannot start, unless the hook sets ``onFailure: "block"``
(https://code.claude.com/docs/en/hooks, "Block the action when a hook fails").
Every refusing guard therefore carries that field, and its timeout leaves wide
headroom over the measured loaded latency. Hooks that refuse nothing stay
fail-open, so a stalled helper never wedges a session.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
HOOKS = REPO / "agents_extensions/shared/hooks"
SETTINGS = REPO / "agents_extensions/shared/settings.json"
DEPLOYED_PREFIX = "$CLAUDE_PROJECT_DIR/.claude/hooks/"

# Every refusing PreToolUse guard wired in the shared settings. A new guard must
# be added here deliberately, which forces it through the fail-closed contract.
REFUSING_GUARDS = frozenset(
    {
        "enforce-venv.sh",
        "guard-admin-merge.py",
        "guard-branch-switch-in-main.py",
        "guard-pr-merge.py",
        "guard-primary-checkout-write.py",
        "guard-public-github-text.py",
        "guard-secret-print.py",
    }
)
# Guards the Claude adapter adds outside the shared settings, with loaded p99
# measured the same way (sequential, 200 calls, 16 busy loops, load about 23).
ADAPTER_GUARD_LOADED_P99_MS = {"guard-reviewer-publish.py": 226}
TIMEOUT_FLOOR_S = 10
def _pre_tool_hooks() -> list[tuple[str, dict]]:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    return [(group.get("matcher", ""), hook) for group in settings["hooks"]["PreToolUse"] for hook in group["hooks"]]


def _deployed_name(hook: dict) -> str | None:
    command = hook.get("command", "")
    return command.removeprefix(DEPLOYED_PREFIX) if command.startswith(DEPLOYED_PREFIX) else None


def _is_refusing_guard(name: str | None) -> bool:
    return name is not None and (name == "enforce-venv.sh" or (name.startswith("guard-") and name.endswith(".py")))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_refusing_guard_blocks_on_failure() -> None:
    entries = [(matcher, hook) for matcher, hook in _pre_tool_hooks() if _is_refusing_guard(_deployed_name(hook))]
    # guard-primary-checkout-write is wired twice: Bash and Write|Edit|MultiEdit.
    assert len(entries) == len(REFUSING_GUARDS) + 1
    assert {matcher for matcher, _ in entries} == {"Bash", "Write|Edit|MultiEdit"}
    for matcher, hook in entries:
        name = _deployed_name(hook)
        assert hook["type"] == "command", name
        assert hook.get("onFailure") == "block", f"{name} ({matcher}) fails open on timeout or crash"
        assert not hook.get("async") and not hook.get("asyncRewake"), f"{name}: onFailure has no effect on async hooks"


def test_every_adapter_added_guard_blocks_on_failure() -> None:
    """Any refusing guard the adapter adds beyond the shared settings must carry the policy too."""
    from scripts.agent_runtime.adapters import claude

    groups = json.loads(claude._worker_guard_settings(publish_guard=True))["hooks"]["PreToolUse"]
    guards = [hook for group in groups for hook in group["hooks"] if _is_refusing_guard(Path(hook["command"]).name)]
    assert {Path(hook["command"]).name for hook in guards} == REFUSING_GUARDS | set(ADAPTER_GUARD_LOADED_P99_MS)
    for hook in guards:
        assert hook.get("onFailure") == "block", hook["command"]
        assert hook["timeout"] >= TIMEOUT_FLOOR_S, hook["command"]


# --- Forced timeout through the real runner (opt-in live canary) -------------


def _claude_canary_enabled() -> bool:
    return os.environ.get("LU_LIVE_CLAUDE_HOOK_CANARY") == "1" and shutil.which("claude") is not None


_LIVE_CANARY = pytest.mark.skipif(
    not _claude_canary_enabled(),
    reason="live Claude Code canary: set LU_LIVE_CLAUDE_HOOK_CANARY=1 with the claude CLI on PATH (one model call)",
)


def _run_live_canary(tmp_path: Path, stub: dict) -> tuple[subprocess.CompletedProcess[str], Path]:
    """Ask Claude Code to run one Bash command behind ``stub`` as its only PreToolUse hook."""
    (tmp_path / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [stub]}]}}), encoding="utf-8"
    )
    marker = tmp_path / "ran"
    work = tmp_path / "work"
    work.mkdir()
    result = subprocess.run(
        [
            "claude",
            "-p",
            f"Use the Bash tool exactly once to run this command and nothing else: touch {marker} . Then reply DONE.",
            "--settings",
            str(tmp_path / "settings.json"),
            "--setting-sources",
            "project",
            "--model",
            "claude-haiku-5-5",
            "--allowedTools",
            "Bash",
            "--output-format",
            "stream-json",
            "--verbose",
        ],
        cwd=work,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert '"tool_use"' in result.stdout, "the model never attempted the Bash call; the canary proved nothing"
    return result, marker


def _timing_out_stub() -> dict:
    """The real Bash guard entry, rewired to a command that outlives its timeout."""
    entry = next(
        hook for matcher, hook in _pre_tool_hooks() if matcher == "Bash" and _is_refusing_guard(_deployed_name(hook))
    )
    return {**entry, "command": "sleep 6", "timeout": 2}


@_LIVE_CANARY
def test_live_claude_blocks_a_tool_call_when_a_guard_times_out(tmp_path: Path) -> None:
    """The stub keeps the guard's own ``onFailure`` field, so reverting the policy fails this test.

    The repository has no other Claude Code hook runner; CI cannot run this
    without the CLI and a model.
    """
    result, marker = _run_live_canary(tmp_path, _timing_out_stub())
    assert not marker.exists(), "the tool call ran although its guard timed out"
    assert 'blocking because onFailure is \\"block\\"' in result.stdout


# --- Guards fail closed when their own dependencies fail ---------------------


def _fake_bin(directory: Path, name: str, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def _bash_payload(command: str, cwd: Path | None = None) -> str:
    payload: dict = {"tool_name": "Bash", "tool_input": {"command": command}}
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return json.dumps(payload)


@pytest.mark.parametrize("failure", ["jq_fails", "unreadable_payload"])
def test_enforce_venv_blocks_when_the_payload_cannot_be_read(tmp_path: Path, failure: str) -> None:
    env = dict(os.environ)
    payload = _bash_payload("python3 -c 1")
    if failure == "jq_fails":
        fake = tmp_path / "bin"
        _fake_bin(fake, "jq", "exit 3")
        env["PATH"] = f"{fake}{os.pathsep}{env['PATH']}"
    else:
        payload = "not json"
    result = subprocess.run(
        ["bash", str(HOOKS / "enforce-venv.sh")], input=payload, env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 2, result.stderr
    assert "could not be read" in result.stderr


# --- Start-up cost: no avoidable git processes on the hot path ----------------


def _recording_git(directory: Path, log: Path) -> None:
    real = shutil.which("git")
    assert real
    _fake_bin(directory, "git", f'printf "%s\\n" "$*" >> "{log}"\nexec "{real}" "$@"')


@pytest.mark.parametrize(
    ("segment", "dangerous"),
    [
        (["git", "status"], False),
        (["git", "log", "--oneline"], False),
        (["git", "checkout", "--", "file"], False),
        (["git", "switch", "main"], False),
        (["git", "branch", "-d", "old"], False),
        (["git", "branch", "-m", "new"], False),
        (["git", "checkout", "-b", "x"], True),
        (["git", "switch", "feature"], True),
        (["git", "branch", "-D", "main"], True),
        (["git", "branch", "-M", "new"], True),
        (["git", "branch", "-f", "x", "HEAD"], True),
        (["git", "branch", "--force", "x"], True),
        (["sudo", "-u", "root", "git", "checkout", "-b", "x"], True),
    ],
)
def test_branch_guard_prefilter_never_hides_a_dangerous_segment(segment: list[str], dangerous: bool) -> None:
    guard = _load("guard_branch_switch_prefilter", HOOKS / "guard-branch-switch-in-main.py")
    assert guard._may_be_dangerous(segment) is dangerous
    if not dangerous:
        # The prefilter may skip the repository probes only when no checked-out
        # branch could make the segment dangerous.
        for branch in ("main", "x", "new", "old", "feature", None):
            assert guard._segment_is_dangerous(segment, branch) is None


def _shim_path(tmp_path: Path, log: Path) -> Path:
    shims = tmp_path / "scripts/agent_runtime/shims"
    _recording_git(shims, log)
    return shims


def test_guard_git_probes_bypass_the_agent_shim(tmp_path: Path) -> None:
    log = tmp_path / "shim.log"
    shims = _shim_path(tmp_path, log)
    env = dict(os.environ, PATH=f"{shims}{os.pathsep}{os.environ['PATH']}")
    result = subprocess.run(
        [sys.executable, str(HOOKS / "guard-primary-checkout-write.py")],
        input=_bash_payload("ls -la", REPO),
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert not log.exists() or log.read_text(encoding="utf-8") == ""

    guard = _load("guard_branch_switch_shim", HOOKS / "guard-branch-switch-in-main.py")
    original = os.environ["PATH"]
    try:
        os.environ["PATH"] = env["PATH"]
        assert str(shims) not in guard._git_probe_env()["PATH"].split(os.pathsep)
    finally:
        os.environ["PATH"] = original


# --- heal-core-bare: in-process config read, fixer only on possible drift -----


@pytest.mark.parametrize(
    ("config", "may_be_bare"),
    [
        ("[core]\n\trepositoryformatversion = 0\n\tbare = false\n", False),
        ('[core]\n\tbare = "false"\n[remote "origin"]\n\turl = x\n', False),
        ("[core]\n\tbare =\n", False),
        ("[core]\n\tbare = true\n", True),
        ("[CORE]\n\tBare = yes\n", True),
        ("[core]\n\tbare\n", True),
        ("[core] bare = on\n", True),
        ("[core]\n\tbare = 1 # comment\n", True),
        ("[core]\n\tbare = false\n[include]\n\tpath = other\n", True),
        ('[includeIf "gitdir:/x/"]\n\tpath = other\n[core]\n\tbare = false\n', True),
        ("[remote]\n\tbare = true\n", False),
        ("[core]\n\tbare = true\n\tbare = false\n", False),
    ],
)
def test_heal_core_bare_reads_the_shared_config(tmp_path: Path, config: str, may_be_bare: bool) -> None:
    heal = _load("heal_core_bare_config", HOOKS / "heal-core-bare.py")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git/config").write_text(config, encoding="utf-8")
    assert heal._may_be_bare(tmp_path) is may_be_bare


def test_heal_core_bare_follows_a_linked_worktree_to_the_common_config(tmp_path: Path) -> None:
    heal = _load("heal_core_bare_worktree", HOOKS / "heal-core-bare.py")
    common = tmp_path / "primary/.git"
    worktree_git = common / "worktrees/w1"
    worktree_git.mkdir(parents=True)
    (worktree_git / "commondir").write_text("../..\n", encoding="utf-8")
    (common / "config").write_text("[core]\n\tbare = true\n", encoding="utf-8")
    checkout = tmp_path / "w1"
    checkout.mkdir()
    (checkout / ".git").write_text(f"gitdir: {worktree_git}\n", encoding="utf-8")
    assert heal._may_be_bare(checkout) is True
    (common / "config").write_text("[core]\n\tbare = false\n", encoding="utf-8")
    assert heal._may_be_bare(checkout) is False


def test_heal_core_bare_reads_config_worktree_when_enabled(tmp_path: Path) -> None:
    heal = _load("heal_core_bare_worktree_config", HOOKS / "heal-core-bare.py")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git/config").write_text("[core]\n\tbare = false\n[extensions]\n\tworktreeConfig = true\n")
    assert heal._may_be_bare(tmp_path) is False
    (tmp_path / ".git/config.worktree").write_text("[core]\n\tbare = true\n")
    assert heal._may_be_bare(tmp_path) is True
    (tmp_path / ".git/config").write_text("[core]\n\tbare = false\n")
    assert heal._may_be_bare(tmp_path) is False, "git ignores config.worktree without worktreeConfig"


def test_heal_core_bare_defers_to_the_checker_when_config_is_unreadable(tmp_path: Path) -> None:
    heal = _load("heal_core_bare_unreadable", HOOKS / "heal-core-bare.py")
    (tmp_path / ".git").mkdir()
    assert heal._may_be_bare(tmp_path) is True


# --- Other harnesses: inner fail-closed deadlines fire before the outer one ----
#
# Codex, Antigravity and Grok document no fail-closed setting for a hook that
# times out (Grok: "timeouts, crashes, malformed output — is fail-open"). Each
# wrapper below converts a guard timeout into a refusal itself, so the gap is
# only the wrapper's own start-up. These tests keep each inner deadline below
# the harness timeout, so the wrapper refuses before the harness gives up.


def test_codex_outer_timeout_exceeds_the_inner_deadline_chain() -> None:
    from scripts.agent_runtime import codex_hook_policy as policy

    hooks = json.loads((REPO / "agents_extensions/codex/hooks.json").read_text(encoding="utf-8"))
    (pre,) = hooks["hooks"]["PreToolUse"]
    (entry,) = pre["hooks"]
    assert "codex_hook_entry.sh" in entry["command"] and "pre-tool-use" in entry["command"]
    serial = policy.ENFORCE_VENV_TIMEOUT + sum(t for _, t in policy.LOCAL_BASH_GUARDS) + policy.PRIMARY_WRITE_GUARD[1]
    merge = max(t for _, t in policy.MERGE_GUARDS)
    snapshot = policy.DIRT_AUDIT_SNAPSHOT[1]
    # Two seconds cover the entry script's own git probe and interpreter start-up.
    assert entry["timeout"] >= serial + merge + snapshot + 2, (entry["timeout"], serial, merge, snapshot)


@pytest.mark.parametrize(
    ("guard_code", "reason"),
    [("import time; time.sleep(30)", "TimeoutExpired"), ("raise SystemExit(1)", None)],
)
def test_grok_bridge_denies_a_guard_that_times_out_or_crashes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], guard_code: str, reason: str | None
) -> None:
    """Grok fails open on any hook failure, so the bridge itself must turn one into a deny."""
    import io

    from scripts.agent_runtime import grok_hook_bridge as bridge

    real_run = subprocess.run

    def short_deadline(*args, **kwargs):
        # The real bridge call, with its fixed deadline shortened so the test stays fast.
        assert kwargs["timeout"] == 10
        return real_run(*args, **{**kwargs, "timeout": 0.5})

    monkeypatch.setattr(bridge, "guard_argv", lambda _: [sys.executable, "-c", guard_code])
    monkeypatch.setattr(bridge.subprocess, "run", short_deadline)
    monkeypatch.setattr(sys, "argv", ["grok_hook_bridge.py", "guard"])
    event = {"hook_event_name": "PreToolUse", "toolName": "run_terminal_command", "toolInput": {"command": "ls"}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event)))
    assert bridge.main() == 2
    if reason:
        assert reason in capsys.readouterr().err


def _cursor_fail_open_guards(config: dict) -> list[str]:
    """Commands of guard hooks in a Cursor ``hooks.json`` that do not set ``failClosed: true``."""
    return [
        hook.get("command", "")
        for hooks in config.get("hooks", {}).values()
        for hook in hooks
        if "guard" in hook.get("command", "") and hook.get("failClosed") is not True
    ]


def test_tracked_cursor_guard_hooks_fail_closed() -> None:
    """Cursor fails open on exit codes other than 0 and 2 unless a hook sets ``failClosed: true``."""
    # Cursor reads project hooks from .cursor/hooks.json; agents_extensions/cursor is its source.
    for path in (REPO / ".cursor/hooks.json", REPO / "agents_extensions/cursor/hooks.json"):
        if path.is_file():
            config = json.loads(path.read_text(encoding="utf-8"))
            assert _cursor_fail_open_guards(config) == [], path
