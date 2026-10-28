"""Claude print-mode flags and terminal result events."""

import json
import platform
import subprocess
from collections.abc import Mapping
from pathlib import Path

from scripts.common.jsonl import jsonl_lines
from scripts.dispatcher.types import Invocation, ParsedResult, TaskSpec
from scripts.lib import rules_core

# Static permission profile from adapters/claude.py; account env belongs to core.
# Read-only grants no blanket Bash: under dontAsk only Claude Code's built-in read-only commands
# (ls, cat, grep, find, read-only git forms) and the gh reads below run, every other command is
# denied, and an output redirect is checked against the Edit deny like a direct write
# (https://code.claude.com/docs/en/permissions, "Read-only commands" and "Redirections").
# Its OS sandbox would allow tests too, but it needs socat on Linux and refuses to start without it.
# dontAsk still runs anything a loaded settings file pre-approves, and a worktree loads the main
# checkout's local settings file, so read-only runs --restricted: Claude Code then reads no
# user, project or local settings file (managed settings and --settings still apply) and drops every
# code-running tool and WebFetch that --tools does not name (https://code.claude.com/docs/en/cli-reference,
# "--restricted"; settings, "Lists merge instead of overriding"). The rules below are the whole policy
# once ``managed_policy`` finds no managed source. --restricted also skips CLAUDE.md, so the rules
# core that ``require_core`` checks is appended to the system prompt instead.
_READ_TOOLSET = "Read,Grep,Glob,Bash,WebFetch,WebSearch"
_READ_TOOLS = (
    "Read,Grep,Glob,LS,WebFetch,WebSearch,Bash(gh pr view *),Bash(gh pr diff *),Bash(gh pr checks *),"
    "Bash(gh issue view *),Bash(gh run view *)"
)
_WRITE_TOOLS = "Bash,Read,Edit,Write,Grep,Glob,LS,WebFetch,WebSearch"
_READ_DENIES = (
    "Edit,Write,NotebookEdit,Bash(git push *),Bash(git commit *),Bash(git merge *),"
    "Bash(git rebase *),Bash(git reset *),Bash(git tag *),Bash(git branch -D *),"
    "Bash(gh pr merge *),Bash(gh pr create *),Bash(gh pr comment *),Bash(gh pr review *),"
    "Bash(gh pr edit *),Bash(gh pr close *),Bash(gh pr reopen *),Bash(gh issue create *),"
    "Bash(gh issue comment *),Bash(gh issue edit *),Bash(gh issue close *),Bash(gh issue reopen *),"
    "Bash(gh api -X *),Bash(gh api --method *),Bash(gh release *),Bash(gh api -f *),"
    "Bash(gh api -F *),Bash(gh api --field *),Bash(gh api --raw-field *),Bash(gh api --input *),"
    "Bash(gh workflow run *)"
)
# Print mode ends with its final turn; no work may remain scheduled after it.
_BACKGROUND_DENIES = "Monitor,ScheduleWakeup,CronCreate,Workflow"
# A non-default account loads none of its login directory's user settings (hooks, permission rules,
# MCP servers, plugins; #10619): adapters/claude.py LABELLED_ACCOUNT_SETTING_SOURCES. The launch
# guard and ``claude auth status`` read the run's ``--settings``, so a labelled run always carries one.
_LABELLED_SETTING_SOURCES = "project,local"
_LABELLED_SETTINGS = json.dumps({"permissions": {"deny": _BACKGROUND_DENIES.split(",")}}, separators=(",", ":"))
_BACKGROUND_ENV = {
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1",
}
# The managed sources --restricted keeps (https://code.claude.com/docs/en/managed-settings, "Where each
# mechanism stores the policy"): on Linux the files under /etc/claude-code, which env_sanitize checks
# as one root, and server-managed settings, cached in the config directory and fetched at start
# (https://code.claude.com/docs/en/server-managed-settings). ``claude doctor`` reports that fetch for
# the run's own credentials; only these outcomes mean no server policy can reach the run. The
# dispatcher is the run's parent and passes it no parent settings.
_REMOTE_NOT_FETCHED = (
    "not fetched — requires an Enterprise or Team subscription",
    "not fetched — no usable credentials",
)


def managed_policy(env: Mapping[str, str]) -> str | None:
    """Why managed policy could widen a read-only run in ``env``, or None when no managed source exists.

    Presence decides, not what a policy holds; a source whose state cannot be read counts as present,
    and an empty server-managed cache (``{}``) delivers no policy key.
    """
    from scripts.agent_runtime.attempt_boundary import _claude_host_is_wsl
    from scripts.agent_runtime.env_sanitize import claude_machine_policy_state

    if platform.system() != "Linux" or _claude_host_is_wsl(env):
        return "managed policy sources are checked on Linux only, not on this host"
    if (state := claude_machine_policy_state()) != "absent":
        return f"managed policy in /etc/claude-code is {state}"
    config = Path(env.get("CLAUDE_CONFIG_DIR") or Path(env.get("HOME") or Path.home()) / ".claude")
    try:
        cached = json.loads((config / "remote-settings.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        cached = {}
    except (OSError, ValueError):
        return "the server-managed settings cache cannot be read"
    if cached != {}:
        return "the server-managed settings cache holds a policy"
    try:
        doctor = subprocess.run(["claude", "doctor"], env=dict(env), stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        doctor = ""
    remote = next((line.partition(":")[2].strip() for line in doctor.splitlines()
                   if line.startswith("Managed settings (remote):")), None)
    if remote is None:
        return "claude doctor did not report server-managed settings"
    if not remote.startswith(_REMOTE_NOT_FETCHED):
        return f"server-managed settings are {remote!r}"
    return None


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    argv = ["claude", "-p", "--model", spec.model]
    if spec.effort is not None:
        argv += ["--effort", spec.effort]
    argv += ["--output-format", "stream-json", "--verbose", "--permission-mode", "dontAsk"]
    if spec.mode == "read-only":
        allowed_tools, denies = _READ_TOOLS, f"{_READ_DENIES},{_BACKGROUND_DENIES}"
    elif spec.mode == "workspace-write":
        allowed_tools, denies = _WRITE_TOOLS, _BACKGROUND_DENIES
    else:
        raise ValueError(f"claude: unsupported mode {spec.mode!r}")
    if spec.mode == "read-only":
        core = rules_core.source_path(rules_core.CORE_REL)
        argv += ["--restricted", "--tools", _READ_TOOLSET, "--append-system-prompt-file", str(core)]
    argv += ["--allowedTools", allowed_tools]
    argv += ["--disallowedTools", denies]
    if spec.claude_account not in (None, "a"):
        argv += ["--settings", _LABELLED_SETTINGS, "--setting-sources", _LABELLED_SETTING_SOURCES]
    return Invocation(argv, spec.prompt_file.read_bytes(), {**env, **_BACKGROUND_ENV}, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    result, error = {}, None
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = "claude: invalid JSON stream"
            continue
        if not isinstance(event, dict):
            error = "claude: invalid event"
        elif event.get("type") == "result":
            result = event
            if event.get("is_error") or event.get("subtype") != "success":
                error = "claude: terminal result unsuccessful"
        elif event.get("type") == "error":
            error = "claude: terminal error"
    text = result.get("result")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    if returncode:
        error = f"claude: exited with status {returncode}"
    return ParsedResult(
        text, usage if isinstance(usage, dict) else None, error or (None if text else "claude: missing final text")
    )
