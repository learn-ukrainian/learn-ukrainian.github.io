"""Claude print-mode flags and terminal result events."""

import json
import platform
import subprocess
from collections.abc import Mapping
from pathlib import Path

from scripts.agent_runtime.sources_read_only import sources_tool_sets
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
# Every run, read-only or workspace-write, gets the Sources MCP server explicitly: from the dispatcher's
# own checkout, never the task's worktree, whose .mcp.json the change in it could turn into a command,
# and alone, as --strict-mcp-config drops every other server (#10074); --restricted would skip the
# project settings that approve .mcp.json servers anyway. Only the tools the server annotates read-only
# are allowed, so authors, judges and fixers can check their own words; the ones that persist fetched
# entries (sources_read_only.sources_tool_sets) are denied by name.
_SOURCES_SERVER = "sources"
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
_BACKGROUND_ENV = {"CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
_ADVISOR_OFF_ENV = {"CLAUDE_CODE_DISABLE_ADVISOR_TOOL": "1"}
# Opus 5.5 advises headless workspace-write workers on Sonnet 5.5, and on Haiku 5.5 only when the dispatch
# asks with --advisor opus (#12094, operator decision 2026-10-30). Every other run, read-only reviews and
# Opus included, keeps the advisor disabled. The advisor needs Claude Code's feature-flag fetch: the child
# environment is an allowlist that carries no telemetry opt-out, and the flag is silently inert if
# DISABLE_TELEMETRY is set (https://code.claude.com/docs/en/advisor). Claude Code has no call cap, so
# the worker brief limits consultations to two.
_ADVISOR_MODEL = "opus"
_ADVISED_MODEL = "claude-sonnet-5-5"
_ADVISED_ON_REQUEST_MODEL = "claude-haiku-5-5"
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


def _sources_mcp_config() -> str:
    servers = json.loads(rules_core.source_path(".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
    return json.dumps({"mcpServers": {_SOURCES_SERVER: servers[_SOURCES_SERVER]}}, separators=(",", ":"))


def advisor_enabled(spec: TaskSpec) -> bool:
    """Whether this run gets the Opus advisor: a workspace-write Sonnet 5.5, or a Haiku 5.5 that asked for it."""
    from scripts.review.model_catalog import canonical_model_id

    if spec.mode != "workspace-write":
        return False
    model = canonical_model_id(spec.model)
    return model == _ADVISED_MODEL or (model == _ADVISED_ON_REQUEST_MODEL and spec.options.get("advisor") == _ADVISOR_MODEL)


def build(spec: TaskSpec, env: dict[str, str]) -> Invocation:
    from scripts.agent_runtime.attempt_boundary import resolve_claude_budget_usd

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
    argv += ["--mcp-config", _sources_mcp_config(), "--strict-mcp-config"]
    readers, writers = sources_tool_sets()
    allowed_tools = ",".join([allowed_tools, *(f"mcp__{_SOURCES_SERVER}__{name}" for name in readers)])
    denies = ",".join([denies, *(f"mcp__{_SOURCES_SERVER}__{name}" for name in writers)])
    argv += ["--allowedTools", allowed_tools]
    argv += ["--disallowedTools", denies]
    if spec.claude_account not in (None, "a"):
        argv += ["--settings", _LABELLED_SETTINGS, "--setting-sources", _LABELLED_SETTING_SOURCES]
    env = {**env, **_BACKGROUND_ENV}
    if advisor_enabled(spec):
        argv += ["--advisor", _ADVISOR_MODEL]
        env.pop("CLAUDE_CODE_DISABLE_ADVISOR_TOOL", None)
    else:
        env.update(_ADVISOR_OFF_ENV)
    if (budget := resolve_claude_budget_usd(spec.claude_account, spec.options.get("max_budget_usd"))) is not None:
        # An API-key run is billed per token: cap it, and keep its cache for an hour, since a test run
        # between two requests can outlast the 5 minute default that print mode gives an API key
        # (https://code.claude.com/docs/en/prompt-caching). A read-only run is short, so it keeps the default.
        argv += ["--max-budget-usd", f"{budget:.2f}"]
        if spec.mode == "workspace-write":
            env["CLAUDE_CODE_PROMPT_CACHE_TTL"] = "1h"
    return Invocation(argv, spec.prompt_file.read_bytes(), env, None)


def parse(stdout: str, stderr: str, returncode: int, final_text: str | None) -> ParsedResult:
    result, error, overloaded = {}, None, False
    stream_clean, terminals = True, 0
    # Runtime evidence for Ukrainian reviews: Sources tool calls whose result came back without error.
    sources_calls, completed = set(), set()
    for line in jsonl_lines(stdout):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            error = "claude: invalid JSON stream"
            stream_clean = False
            continue
        if terminals:
            # Anything after the terminal result (another result, an event) makes the stream untrustworthy.
            stream_clean = False
        if not isinstance(event, dict):
            error = "claude: invalid event"
            stream_clean = False
        elif event.get("type") == "result":
            terminals += 1
            result = event
            if event.get("is_error") or event.get("subtype") != "success":
                error = "claude: terminal result unsuccessful"
            # The structured HTTP status of the API failure, as in the 529 Overloaded result stream.
            overloaded = event.get("is_error") is True and event.get("api_error_status") == 529
        elif event.get("type") == "error":
            error = "claude: terminal error"
        elif event.get("type") in ("assistant", "user"):
            for item in _content(event):
                name, call_id, result_id = item.get("name"), item.get("id"), item.get("tool_use_id")
                if item.get("type") == "tool_use" and isinstance(name, str) and isinstance(call_id, str):
                    if name.startswith(f"mcp__{_SOURCES_SERVER}__"):
                        sources_calls.add(call_id)
                elif item.get("type") == "tool_result" and isinstance(result_id, str) and item.get("is_error") is not True:
                    completed.add(result_id)
    text = result.get("result")
    text = text if isinstance(text, str) and text.strip() else None
    usage = result.get("usage")
    if overloaded and stream_clean and terminals == 1 and error == "claude: terminal result unsuccessful" and isinstance(result.get("result"), str):
        return ParsedResult(None, None, f"claude: {result['result']}", rate_limited=True)
    if returncode:
        error = f"claude: exited with status {returncode}"
    return ParsedResult(
        text, usage if isinstance(usage, dict) else None, error or (None if text else "claude: missing final text"),
        sources_mcp_call_count=len(sources_calls & completed),
    )


def _content(event: dict) -> list[dict]:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return [item for item in content if isinstance(item, dict)] if isinstance(content, list) else []
