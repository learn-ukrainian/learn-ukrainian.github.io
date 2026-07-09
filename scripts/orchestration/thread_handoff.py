#!/usr/bin/env python
"""Prepare and guard agent-specific thread handoffs.

The Codex app can expose thread and automation tools to an agent, but a local
repo script cannot assume those app-only tools exist. This helper gathers the
durable local state, writes a handoff packet, generates the replacement-thread
bootstrap prompt, and records a lease that prevents old automation cleanup
until the replacement thread is explicitly confirmed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import subprocess
import urllib.error
import urllib.request
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DEFAULT_MONITOR_BASE_URL = "http://127.0.0.1:8765"
DEFAULT_AGENT = "orchestrator"
DEFAULT_ROUTER_AGENTS = ("orchestrator", "codex", "claude", "gemini")
AGENT_NAME_RE = re.compile(r"^[a-z][a-z0-9-]*$")
DEFAULT_ROUTER_PATH = Path("docs/session-state/current.md")
ORCHESTRATOR_HANDOFF_PATH = Path("docs/session-state/codex-orchestrator-handoff.md")
DEFAULT_STALE_HOURS = 12
# Rollover warn point as a percent of the context window. Raised 82.0 → 88.0
# (user direction 2026-06-15): Opus 4.8 has NO >200K long-context premium and no
# brain-rot cliff, so staying high is cheap (cache-read tax ≈ $0.50 per 1M-of-context
# per turn) — warn later to avoid early-nag and waste less of the window. 88% on a 1M
# window ≈ 880K, leaving ~120K margin below the hard wall for the handoff write (~35K)
# + clean-execution headroom. Measure context deterministically, not by gut estimate
# (self-estimate runs ~1.8× high; see memory/MEMORY.md #2).
DEFAULT_CONTEXT_THRESHOLD = 88.0


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str


def repo_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_agent_name(value: str | None) -> str:
    agent = (value or DEFAULT_AGENT).strip().lower()
    if not AGENT_NAME_RE.fullmatch(agent):
        raise ValueError(
            "agent names must match [a-z][a-z0-9-]* so handoff paths cannot escape the repo"
        )
    return agent


def argparse_agent_name(value: str) -> str:
    try:
        return normalize_agent_name(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def default_state_path(agent: str) -> Path:
    return Path(f".agent/{agent}-thread-lease.json")


def default_bootstrap_path(agent: str) -> Path:
    return Path(f".agent/{agent}-thread-bootstrap.md")


def default_thread_handoff_path(agent: str) -> Path:
    return Path(f".agent/{agent}-thread-handoff.md")


def default_handoff_path(agent: str) -> Path:
    if agent == DEFAULT_AGENT:
        return ORCHESTRATOR_HANDOFF_PATH
    if agent == "codex":
        # Codex UI rollovers read the orchestrator compatibility pointer. There
        # is no separate Codex-specific durable handoff file in this repo.
        return Path("docs/session-state/current.orchestrator.md")
    return Path(f"docs/session-state/current.{agent}.md")


def router_agents(selected_agent: str) -> list[str]:
    agents = list(DEFAULT_ROUTER_AGENTS)
    if selected_agent not in agents:
        agents.append(selected_agent)
    return agents


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def isoformat_z(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout_s: int = 10,
) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        return CommandResult(returncode=127, stdout="", stderr=str(exc))
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return CommandResult(
            returncode=124,
            stdout=str(stdout).strip(),
            stderr=(str(stderr).strip() or f"timeout after {timeout_s}s"),
        )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def git_output(repo_root: Path, *args: str, timeout_s: int = 10) -> str:
    result = run_command(["git", *args], cwd=repo_root, timeout_s=timeout_s)
    if result.returncode != 0:
        return ""
    return result.stdout


def http_get_json(base_url: str, path: str, timeout_s: float = 3.0) -> dict[str, Any]:
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (OSError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        return {"_error": f"{type(exc).__name__}: {exc}"}
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return {"_error": f"JSONDecodeError: {exc}"}
    return data if isinstance(data, dict) else {"value": data}


def gh_json(repo_root: Path, args: list[str], timeout_s: int = 15) -> Any:
    result = run_command(["gh", *args], cwd=repo_root, timeout_s=timeout_s)
    if result.returncode != 0:
        return {"_error": result.stderr or result.stdout or "gh command failed"}
    try:
        return json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        return {"_error": f"JSONDecodeError: {exc}"}


def parse_git_log(raw: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        if not parts or not parts[0]:
            continue
        commits.append({
            "sha": parts[0],
            "subject": parts[1] if len(parts) > 1 else "",
        })
    return commits


def parse_status(raw: str) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line:
            continue
        files.append({
            "status": line[:2].strip() or line[:2],
            "path": line[3:] if len(line) > 3 else "",
        })
    return files


def parse_ahead_behind(raw: str, upstream: str) -> dict[str, Any] | None:
    if not raw:
        return None
    parts = raw.split()
    if len(parts) < 2:
        return {"upstream": upstream, "parse_error": f"unexpected rev-list output: {raw!r}"}
    try:
        behind = int(parts[0])
        ahead = int(parts[1])
    except ValueError:
        return {"upstream": upstream, "parse_error": f"non-integer rev-list output: {raw!r}"}
    return {"ahead": ahead, "behind": behind, "upstream": upstream}


def gather_git_state(repo_root: Path) -> dict[str, Any]:
    branch = git_output(repo_root, "branch", "--show-current") or "DETACHED"
    head = git_output(repo_root, "rev-parse", "--short=10", "HEAD")
    full_head = git_output(repo_root, "rev-parse", "HEAD")
    upstream = git_output(repo_root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
    ahead_behind = None
    if upstream:
        counts = git_output(repo_root, "rev-list", "--left-right", "--count", f"{upstream}...HEAD")
        ahead_behind = parse_ahead_behind(counts, upstream)

    return {
        "repo_root": str(repo_root),
        "branch": branch,
        "head": head,
        "full_head": full_head,
        "ahead_behind": ahead_behind,
        "last_commits": parse_git_log(
            git_output(repo_root, "log", "-5", "--pretty=format:%h%x09%s")
        ),
        "modified_files": parse_status(git_output(repo_root, "status", "--short")),
    }


def gather_monitor_state(base_url: str) -> dict[str, Any]:
    return {
        "base_url": base_url.rstrip("/"),
        "orient": http_get_json(base_url, "/api/orient?fresh=true"),
        "active_delegates": http_get_json(base_url, "/api/delegate/active"),
        "completed_delegates": http_get_json(base_url, "/api/delegate/tasks?status=done&limit=5"),
        "worktrees": http_get_json(base_url, "/api/worktrees"),
    }


def gather_github_state(repo_root: Path) -> dict[str, Any]:
    return {
        "open_prs": gh_json(repo_root, [
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision",
            "--limit",
            "20",
        ]),
        "open_issues": gh_json(repo_root, [
            "issue",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,url,updatedAt,labels",
            "--limit",
            "10",
        ]),
    }


def gather_snapshot(repo_root: Path, base_url: str) -> dict[str, Any]:
    return {
        "generated_at": isoformat_z(utc_now()),
        "git": gather_git_state(repo_root),
        "monitor": gather_monitor_state(base_url),
        "github": gather_github_state(repo_root),
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "state_error": f"unreadable state file: {path}: {type(exc).__name__}: {exc}",
        }
    if not isinstance(data, dict):
        return {"schema_version": SCHEMA_VERSION, "state_error": f"state file is not a JSON object: {path}"}
    data.setdefault("schema_version", SCHEMA_VERSION)
    return data


def state_error_payload(state: dict[str, Any], state_path: Path, repo_root: Path) -> dict[str, Any] | None:
    error = state.get("state_error")
    if not error:
        return None
    return {
        "error": str(error),
        "state_file": rel(state_path, repo_root),
        "hint": "Inspect the file, restore it, or rerun prepare with --force-reset-state to start a new lease.",
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def active_thread_id_from_env() -> str | None:
    return os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")


def generation_id(prefix: str, now: datetime) -> str:
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}"


def prepare_state(
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    now: datetime,
    active_thread_id: str | None,
    active_automation_id: str | None,
    bootstrap_path: Path,
    context_percent: float | None,
    force_new_replacement: bool,
) -> dict[str, Any]:
    prepared = dict(state)
    prepared["schema_version"] = SCHEMA_VERSION
    prepared["agent"] = agent

    active = dict(prepared.get("active") or {})
    if not active.get("generation"):
        active["generation"] = generation_id(agent, now)
        active["started_at"] = isoformat_z(now)
    if active_thread_id:
        active["thread_id"] = active_thread_id
    elif active_thread_id_from_env() and not active.get("thread_id"):
        active["thread_id"] = active_thread_id_from_env()
    if active_automation_id:
        active["automation_id"] = active_automation_id
    active["last_seen_at"] = isoformat_z(now)
    prepared["active"] = active

    replacement = dict(prepared.get("replacement") or {})
    if force_new_replacement or replacement.get("status") not in {"pending_start", "started"}:
        replacement = {
            "generation": generation_id(f"{agent}-next", now),
            "status": "pending_start",
            "prepared_at": isoformat_z(now),
            "thread_id": None,
            "bootstrap_prompt_path": bootstrap_path.as_posix(),
        }
    else:
        replacement["prepared_at"] = isoformat_z(now)
        replacement["bootstrap_prompt_path"] = bootstrap_path.as_posix()
    prepared["replacement"] = replacement

    cleanup = dict(prepared.get("cleanup") or {})
    cleanup["old_automation_ready_to_delete"] = False
    cleanup["reason"] = "replacement thread has not been explicitly confirmed"
    prepared["cleanup"] = cleanup

    prepared["last_handoff"] = {
        "prepared_at": isoformat_z(now),
        "context_percent": context_percent,
    }
    return prepared


def confirm_started(
    state: dict[str, Any],
    *,
    new_thread_id: str,
    new_automation_id: str | None,
    confirmed_by: str,
    now: datetime,
) -> dict[str, Any]:
    if not new_thread_id.strip():
        raise ValueError("--new-thread-id is required")
    if not state.get("replacement"):
        raise ValueError("no pending replacement exists; run prepare first")

    confirmed = dict(state)
    replacement = dict(confirmed["replacement"])
    replacement["status"] = "started"
    replacement["thread_id"] = new_thread_id.strip()
    replacement["confirmed_at"] = isoformat_z(now)
    if new_automation_id:
        replacement["automation_id"] = new_automation_id
    confirmed["replacement"] = replacement

    cleanup = dict(confirmed.get("cleanup") or {})
    cleanup["old_automation_ready_to_delete"] = True
    cleanup["confirmed_by"] = confirmed_by
    cleanup["confirmed_at"] = isoformat_z(now)
    cleanup["reason"] = "replacement thread start confirmed by operator command"
    confirmed["cleanup"] = cleanup
    confirmed["updated_at"] = isoformat_z(now)
    return confirmed


def format_table(rows: list[list[str]], headers: list[str]) -> str:
    if not rows:
        return "_None._"
    widths = [len(header) for header in headers]
    for row in rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))
    header_line = "| " + " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * widths[idx] for idx in range(len(headers))) + " |"
    row_lines = [
        "| " + " | ".join(value.ljust(widths[idx]) for idx, value in enumerate(row)) + " |"
        for row in rows
    ]
    return "\n".join([header_line, sep_line, *row_lines])


def summarize_prs(open_prs: Any) -> str:
    if isinstance(open_prs, dict) and open_prs.get("_error"):
        return f"_Unavailable: {open_prs['_error']}_"
    rows = []
    for pr in open_prs if isinstance(open_prs, list) else []:
        rows.append([
            f"#{pr.get('number')}",
            str(pr.get("headRefName") or ""),
            str(pr.get("mergeStateStatus") or ""),
            "yes" if pr.get("isDraft") else "no",
            str(pr.get("title") or ""),
        ])
    return format_table(rows, ["PR", "Branch", "Merge", "Draft", "Title"])


def summarize_issues(open_issues: Any) -> str:
    if isinstance(open_issues, dict) and open_issues.get("_error"):
        return f"_Unavailable: {open_issues['_error']}_"
    rows = []
    for issue in open_issues if isinstance(open_issues, list) else []:
        rows.append([
            f"#{issue.get('number')}",
            str(issue.get("updatedAt") or ""),
            str(issue.get("title") or ""),
        ])
    return format_table(rows, ["Issue", "Updated", "Title"])


def summarize_tasks(tasks_payload: Any) -> str:
    if not isinstance(tasks_payload, dict):
        return "_Unavailable._"
    if tasks_payload.get("_error"):
        return f"_Unavailable: {tasks_payload['_error']}_"
    rows = []
    for task in tasks_payload.get("tasks") or []:
        rows.append([
            str(task.get("task_id") or ""),
            str(task.get("agent") or ""),
            str(task.get("status") or ""),
            str(task.get("age_s") or task.get("duration_s") or ""),
        ])
    return format_table(rows, ["Task", "Agent", "Status", "Age/Duration"])


def summarize_modified_files(files: list[dict[str, str]]) -> str:
    if not files:
        return "_None._"
    rows = [[item.get("status", ""), item.get("path", "")] for item in files]
    return format_table(rows, ["Status", "Path"])


def summarize_commits(commits: list[dict[str, str]]) -> str:
    rows = [[item.get("sha", ""), item.get("subject", "")] for item in commits]
    return format_table(rows, ["SHA", "Subject"])


def context_line(context_percent: float | None, threshold: float) -> str:
    if context_percent is None:
        return "Context percent was not supplied; use --context-percent from a statusline or manual estimate."
    state = "ROLL OVER NOW" if context_percent >= threshold else "below rollover threshold"
    return f"Context estimate: {context_percent:.1f}% ({state}; threshold {threshold:.1f}%)."


def first_turn_checklist_lines(
    *,
    repo_root: str,
    thread_handoff_text: str,
    role_handoff_text: str,
) -> list[str]:
    return [
        "First-turn checklist:",
        f"1. `cd {repo_root}`",
        "2. `git status --short --branch`",
        f"3. Read `{thread_handoff_text}` and `{role_handoff_text}`.",
        "4. Check `/api/orient?fresh=true` from the local monitor.",
        "5. If `/api/orient` returns an `issues_error` or the GitHub issue subsection times out, run `.venv/bin/python scripts/orchestration/issue_stream_audit.py --json`.",
        "6. `gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision --limit 20`",
        "7. `git worktree list` and verify the active worktree is the one you intend to edit.",
    ]


def render_bootstrap_prompt(
    snapshot: dict[str, Any],
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    router_path: Path = DEFAULT_ROUTER_PATH,
    handoff_path: Path | None = None,
    role_handoff_path: Path | None = None,
    context_threshold: float,
) -> str:
    git = snapshot["git"]
    monitor = snapshot["monitor"]
    github = snapshot["github"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or default_bootstrap_path(agent).as_posix()
    handoff_path = handoff_path or default_thread_handoff_path(agent)
    role_handoff_path = role_handoff_path or default_handoff_path(agent)
    handoff_text = role_handoff_path.as_posix()
    thread_handoff_text = handoff_path.as_posix()
    active_generation = active.get("generation") or "unknown"
    replacement_generation = replacement.get("generation") or "unknown"
    context_percent = (state.get("last_handoff") or {}).get("context_percent")
    agent_label = "Codex orchestrator" if agent == "orchestrator" else agent

    return "\n".join([
        f"Work locally in {git.get('repo_root')}.",
        "",
        f"You are the replacement {agent_label} thread.",
        f"Replacement generation: {replacement_generation}",
        f"Previous active generation: {active_generation}",
        f"Role handoff: {handoff_text}",
        f"Thread handoff: {thread_handoff_text}",
        "",
        "Read first:",
        f"- {thread_handoff_text}",
        f"- {handoff_text}",
        "- AGENTS.md",
        "- docs/best-practices/agent-cooperation.md",
        "- docs/best-practices/codex-thread-handoff.md",
        "",
        "Rules:",
        "- Continue from the handoff exactly; do not restart from scratch.",
        "- Keep the main checkout read-only; thread rollover state belongs in gitignored .agent/ files.",
        "- Use dispatch worktrees for implementation work: .worktrees/dispatch/<agent>/<task>/.",
        "- Do not edit generated status/audit/review artifacts, linter configs, or .python-version.",
        "- Do not write docs/session-state/current.md for thread rollover.",
        "- Do not delete or migrate the old heartbeat automation until the confirm-started command below has succeeded.",
        "",
        *first_turn_checklist_lines(
            repo_root=str(git.get("repo_root")),
            thread_handoff_text=thread_handoff_text,
            role_handoff_text=handoff_text,
        ),
        "",
        "Local monitor follow-up:",
        "```bash",
        "curl -sS http://127.0.0.1:8765/api/delegate/active",
        "curl -sS http://127.0.0.1:8765/api/worktrees",
        ".venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results",
        "```",
        "",
        "After the replacement thread is actually running, confirm it from the repo root:",
        "```bash",
        f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent {agent} --new-thread-id <replacement-thread-id>",
        "```",
        "",
        "Only after that command reports old_automation_ready_to_delete=true may the old heartbeat automation be deleted or paused.",
        "",
        "Current snapshot:",
        f"- Branch: {git.get('branch')} @ {git.get('head')}",
        f"- {context_line(float(context_percent) if context_percent is not None else None, context_threshold)}",
        f"- Active delegates: {(monitor.get('active_delegates') or {}).get('total', 'unknown') if isinstance(monitor.get('active_delegates'), dict) else 'unknown'}",
        f"- Open PRs: {len(github.get('open_prs')) if isinstance(github.get('open_prs'), list) else 'unknown'}",
        f"- Bootstrap prompt source: {prompt_path}",
    ]) + "\n"


def render_current_markdown(
    snapshot: dict[str, Any],
    state: dict[str, Any],
    *,
    agent: str = DEFAULT_AGENT,
    role_handoff_path: Path | None = None,
    context_threshold: float,
) -> str:
    git = snapshot["git"]
    monitor = snapshot["monitor"]
    github = snapshot["github"]
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    cleanup = state.get("cleanup") or {}
    handoff = state.get("last_handoff") or {}
    prompt_path = replacement.get("bootstrap_prompt_path") or default_bootstrap_path(agent).as_posix()
    thread_handoff_text = default_thread_handoff_path(agent).as_posix()
    role_handoff = (role_handoff_path or default_handoff_path(agent)).as_posix()
    title_agent = "Orchestrator" if agent == "orchestrator" else agent.title()

    lines = [
        f"# Current - {title_agent} thread handoff ({snapshot['generated_at']})",
        "",
        "> Generated by `scripts/orchestration/thread_handoff.py prepare`.",
        "> This is a rollover handoff, not proof that the replacement thread started.",
        f"> Agent: `{agent}`.",
        "",
        "## Thread Lease",
        "",
        f"- Active generation: `{active.get('generation', 'unknown')}`",
        f"- Active thread id: `{active.get('thread_id', 'unknown')}`",
        f"- Active automation id: `{active.get('automation_id', 'unknown')}`",
        f"- Replacement generation: `{replacement.get('generation', 'unknown')}`",
        f"- Replacement status: `{replacement.get('status', 'unknown')}`",
        f"- Replacement thread id: `{replacement.get('thread_id') or 'not-confirmed'}`",
        f"- Old automation ready to delete: `{cleanup.get('old_automation_ready_to_delete', False)}`",
        f"- Bootstrap prompt: `{prompt_path}`",
        f"- Durable role handoff: `{role_handoff}`",
        "",
        "## Context Budget",
        "",
        context_line(
            float(handoff["context_percent"]) if handoff.get("context_percent") is not None else None,
            context_threshold,
        ),
        "",
        "## Git State",
        "",
        f"- Repo: `{git.get('repo_root')}`",
        f"- Branch: `{git.get('branch')}`",
        f"- HEAD: `{git.get('head')}` (`{git.get('full_head')}`)",
        f"- Upstream: `{(git.get('ahead_behind') or {}).get('upstream', 'none')}`",
        f"- Ahead/behind: `{git.get('ahead_behind')}`",
        "",
        "### Last 5 Commits",
        "",
        summarize_commits(git.get("last_commits") or []),
        "",
        "### Modified Files",
        "",
        summarize_modified_files(git.get("modified_files") or []),
        "",
        "## Open PRs",
        "",
        summarize_prs(github.get("open_prs")),
        "",
        "## Open Issues",
        "",
        summarize_issues(github.get("open_issues")),
        "",
        "## Delegated Tasks",
        "",
        "### Active",
        "",
        summarize_tasks(monitor.get("active_delegates")),
        "",
        "### Recently Completed",
        "",
        summarize_tasks(monitor.get("completed_delegates")),
        "",
        "## Worktrees",
        "",
        f"- Count: `{(monitor.get('worktrees') or {}).get('count', 'unknown') if isinstance(monitor.get('worktrees'), dict) else 'unknown'}`",
        "",
        "## First-Turn Checklist",
        "",
        *first_turn_checklist_lines(
            repo_root=str(git.get("repo_root")),
            thread_handoff_text=thread_handoff_text,
            role_handoff_text=role_handoff,
        ),
        "",
        "## Local Monitor Follow-Up",
        "",
        "```bash",
        "curl -sS http://127.0.0.1:8765/api/delegate/active",
        "curl -sS http://127.0.0.1:8765/api/worktrees",
        ".venv/bin/python scripts/orchestration/orchestrator_control.py inbox --recent 20 --include-results",
        "```",
        "",
        "## Replacement Bootstrap Prompt",
        "",
        "Paste the generated bootstrap prompt into the new Codex thread, or use the Codex app `create_thread` tool when available.",
        "After the new thread is actually running, run:",
        "",
        "```bash",
        f".venv/bin/python scripts/orchestration/thread_handoff.py confirm-started --agent {agent} --new-thread-id <replacement-thread-id>",
        "```",
        "",
        "Do not delete the old heartbeat automation before this confirmation.",
        "",
    ]
    return "\n".join(lines)


def render_router_markdown(
    *,
    generated_at: str,
    default_agent: str,
    agents: list[str],
) -> str:
    default_handoff = default_handoff_path(default_agent).as_posix()
    lines = [
        "# Current Session Router",
        "",
        f"Latest-Brief: {default_handoff}",
        "",
        "Agent-Handoff:",
    ]
    for agent in agents:
        lines.append(f"- {agent}: {default_handoff_path(agent).as_posix()}")
    lines.extend([
        "",
        f"Default-Agent: {default_agent}",
        f"Generated-At: {generated_at}",
        "",
        "This file is a small compatibility router. Durable role state lives in",
        "the mapped Agent-Handoff files. Thread rollover packets live under",
        "`.agent/<agent>-thread-handoff.md` unless explicitly overridden.",
        "",
    ])
    return "\n".join(lines)


def inspect_codex_home(codex_home: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "codex_home": str(codex_home),
        "exists": codex_home.exists(),
        "session_index": str(codex_home / "session_index.jsonl"),
        "automations_dir": str(codex_home / "automations"),
    }
    automations_dir = codex_home / "automations"
    if automations_dir.exists():
        result["automation_toml_files"] = [
            str(path)
            for path in sorted(automations_dir.glob("**/automation.toml"))
        ]
    else:
        result["automation_toml_files"] = []

    state_dbs = sorted(codex_home.glob("state_*.sqlite"), key=lambda p: p.stat().st_mtime, reverse=True)
    result["state_databases"] = [str(path) for path in state_dbs[:3]]
    if state_dbs:
        db_path = state_dbs[0]
        try:
            with closing(sqlite3.connect(db_path)) as conn:
                tables = [
                    row[0]
                    for row in conn.execute("select name from sqlite_master where type='table' order by name")
                ]
                result["latest_state_db"] = str(db_path)
                result["tables"] = tables
                if "threads" in tables:
                    result["thread_count"] = conn.execute("select count(*) from threads").fetchone()[0]
                    result["recent_threads"] = [
                        {"id": row[0], "title": row[1], "cwd": row[2], "archived": bool(row[3])}
                        for row in conn.execute(
                            "select id, title, cwd, archived from threads order by updated_at desc limit 5"
                        )
                    ]
        except sqlite3.Error as exc:
            result["sqlite_error"] = f"{type(exc).__name__}: {exc}"

    codex_help = run_command(["codex", "exec", "resume", "--help"], cwd=Path.cwd(), timeout_s=5)
    result["codex_exec_resume_available"] = codex_help.returncode == 0
    if codex_help.returncode != 0:
        result["codex_exec_resume_error"] = codex_help.stderr or codex_help.stdout
    return result


def check_state(
    state: dict[str, Any],
    *,
    now: datetime,
    stale_after: timedelta,
    context_percent: float | None,
    context_threshold: float,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    facts: list[str] = []
    active = state.get("active") or {}
    replacement = state.get("replacement") or {}
    cleanup = state.get("cleanup") or {}

    if state.get("state_error"):
        warnings.append(str(state["state_error"]))

    facts.append(f"active_generation={active.get('generation', 'unknown')}")
    facts.append(f"replacement_status={replacement.get('status', 'none')}")
    facts.append(f"old_automation_ready_to_delete={cleanup.get('old_automation_ready_to_delete', False)}")

    active_seen = parse_iso_datetime(active.get("last_seen_at") or active.get("started_at"))
    if active_seen and now - active_seen > stale_after:
        warnings.append(f"active generation last seen {now - active_seen} ago")

    prepared_at = parse_iso_datetime(replacement.get("prepared_at"))
    if replacement.get("status") == "pending_start":
        warnings.append("replacement thread is pending_start; old automation must stay active")
        if prepared_at and now - prepared_at > stale_after:
            warnings.append(f"replacement has been pending for {now - prepared_at}")

    if cleanup.get("old_automation_ready_to_delete") and not replacement.get("thread_id"):
        warnings.append("cleanup says ready, but replacement thread_id is missing")

    if context_percent is not None and context_percent >= context_threshold:
        warnings.append(f"context estimate {context_percent:.1f}% is at/above threshold {context_threshold:.1f}%")

    return facts, warnings


def cmd_prepare(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    now = utc_now()
    agent = normalize_agent_name(args.agent)
    state_file = args.state_file or default_state_path(agent)
    bootstrap_file = args.bootstrap_file or default_bootstrap_path(agent)
    handoff_file = args.handoff_file or default_thread_handoff_path(agent)
    role_handoff_file = default_handoff_path(agent)
    router_file = args.current_file or DEFAULT_ROUTER_PATH
    state_path = repo_root / state_file
    bootstrap_path = repo_root / bootstrap_file
    handoff_path = repo_root / handoff_file
    role_handoff_path = repo_root / role_handoff_file
    router_path = repo_root / router_file

    if args.write_current and not args.allow_git_router:
        print(json.dumps({
            "error": "--write-current is disabled by default because docs/session-state/current.md is git-tracked. "
            "Use the default .agent/ handoff files for thread rollover, or pass --allow-git-router only for an explicitly approved compatibility-router update.",
            "agent": agent,
            "thread_handoff_file": rel(handoff_path, repo_root),
            "bootstrap_file": rel(bootstrap_path, repo_root),
        }, indent=2))
        return 2

    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, repo_root)
    if state_error and not args.force_reset_state:
        print(json.dumps(state_error, indent=2))
        return 2
    if state_error and args.force_reset_state:
        state = {
            "schema_version": SCHEMA_VERSION,
            "reset_from_error": state_error["error"],
        }
    prepared_state = prepare_state(
        state,
        agent=agent,
        now=now,
        active_thread_id=args.active_thread_id,
        active_automation_id=args.active_automation_id,
        bootstrap_path=Path(bootstrap_file),
        context_percent=args.context_percent,
        force_new_replacement=args.force_new_replacement,
    )
    snapshot = gather_snapshot(repo_root, args.monitor_base_url)
    prompt = render_bootstrap_prompt(
        snapshot,
        prepared_state,
        agent=agent,
        router_path=Path(router_file),
        handoff_path=Path(handoff_file),
        role_handoff_path=Path(role_handoff_file),
        context_threshold=args.context_threshold,
    )
    handoff_md = render_current_markdown(
        snapshot,
        prepared_state,
        agent=agent,
        role_handoff_path=Path(role_handoff_file),
        context_threshold=args.context_threshold,
    )
    router_md = render_router_markdown(
        generated_at=snapshot["generated_at"],
        default_agent=DEFAULT_AGENT,
        agents=router_agents(agent),
    )

    if args.dry_run:
        output = {
            "dry_run": True,
            "agent": agent,
            "state_file": state_path.as_posix(),
            "bootstrap_file": bootstrap_path.as_posix(),
            "handoff_file": handoff_path.as_posix(),
            "thread_handoff_file": handoff_path.as_posix(),
            "role_handoff_file": role_handoff_path.as_posix(),
            "router_file": router_path.as_posix(),
            "current_file": router_path.as_posix(),
            "would_write_router": bool(args.write_current),
            "old_automation_ready_to_delete": False,
            "bootstrap_prompt": prompt,
        }
        print(json.dumps(output, indent=2))
        return 0

    bootstrap_path.parent.mkdir(parents=True, exist_ok=True)
    bootstrap_path.write_text(prompt, encoding="utf-8")
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(handoff_md, encoding="utf-8")
    write_json_atomic(state_path, prepared_state)
    wrote_router = False
    if args.write_current:
        router_path.parent.mkdir(parents=True, exist_ok=True)
        router_path.write_text(router_md, encoding="utf-8")
        wrote_router = True

    output = {
        "agent": agent,
        "state_file": rel(state_path, repo_root),
        "bootstrap_file": rel(bootstrap_path, repo_root),
        "handoff_file": rel(handoff_path, repo_root),
        "thread_handoff_file": rel(handoff_path, repo_root),
        "role_handoff_file": rel(role_handoff_path, repo_root),
        "router_file": rel(router_path, repo_root) if wrote_router else None,
        "current_file": rel(router_path, repo_root) if wrote_router else None,
        "replacement_status": prepared_state["replacement"]["status"],
        "old_automation_ready_to_delete": prepared_state["cleanup"]["old_automation_ready_to_delete"],
    }
    print(json.dumps(output, indent=2))
    return 0


def cmd_confirm_started(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    agent = normalize_agent_name(args.agent)
    state_path = repo_root / (args.state_file or default_state_path(agent))
    state = load_state(state_path)
    state_error = state_error_payload(state, state_path, repo_root)
    if state_error:
        print(json.dumps(state_error, indent=2))
        return 2
    try:
        confirmed = confirm_started(
            state,
            new_thread_id=args.new_thread_id,
            new_automation_id=args.new_automation_id,
            confirmed_by=args.confirmed_by,
            now=utc_now(),
        )
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, indent=2))
        return 2
    write_json_atomic(state_path, confirmed)
    print(json.dumps({
        "agent": agent,
        "state_file": rel(state_path, repo_root),
        "replacement_status": confirmed["replacement"]["status"],
        "replacement_thread_id": confirmed["replacement"]["thread_id"],
        "old_automation_ready_to_delete": confirmed["cleanup"]["old_automation_ready_to_delete"],
    }, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    agent = normalize_agent_name(args.agent)
    state_path = repo_root / (args.state_file or default_state_path(agent))
    state = load_state(state_path)
    facts, warnings = check_state(
        state,
        now=utc_now(),
        stale_after=timedelta(hours=args.stale_hours),
        context_percent=args.context_percent,
        context_threshold=args.context_threshold,
    )
    payload = {"agent": agent, "facts": facts, "warnings": warnings, "state_file": rel(state_path, repo_root)}
    print(json.dumps(payload, indent=2))
    return 2 if warnings else 0


def cmd_audit(args: argparse.Namespace) -> int:
    codex_home = Path(args.codex_home).expanduser().resolve()
    audit = inspect_codex_home(codex_home)
    audit["monitor"] = gather_monitor_state(args.monitor_base_url) if args.include_monitor else "skipped"
    print(json.dumps(audit, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo_root_from_file())
    parser.add_argument("--monitor-base-url", default=os.environ.get("MONITOR_API_BASE_URL", DEFAULT_MONITOR_BASE_URL))
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Prepare a rollover handoff and bootstrap prompt.")
    prepare.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    prepare.add_argument("--state-file", type=Path)
    prepare.add_argument("--bootstrap-file", type=Path)
    prepare.add_argument("--handoff-file", type=Path, help="Override the local thread rollover handoff path.")
    prepare.add_argument("--current-file", type=Path, help="Override the shared docs/session-state/current.md router.")
    prepare.add_argument("--active-thread-id")
    prepare.add_argument("--active-automation-id")
    prepare.add_argument("--context-percent", type=float)
    prepare.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    prepare.add_argument("--force-new-replacement", action="store_true")
    prepare.add_argument(
        "--force-reset-state",
        action="store_true",
        help="Discard an unreadable lease state file and start a new lease.",
    )
    prepare.add_argument(
        "--write-current",
        action="store_true",
        help="Deprecated: also overwrite the shared current.md router. Requires --allow-git-router.",
    )
    prepare.add_argument(
        "--allow-git-router",
        action="store_true",
        help="Explicitly unlock --write-current for an approved compatibility-router update.",
    )
    prepare.add_argument("--dry-run", action="store_true", help="Print the generated packet without writing files.")
    prepare.set_defaults(func=cmd_prepare)

    confirm = subparsers.add_parser("confirm-started", help="Confirm that the replacement agent thread is running.")
    confirm.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    confirm.add_argument("--state-file", type=Path)
    confirm.add_argument("--new-thread-id", required=True)
    confirm.add_argument("--new-automation-id")
    confirm.add_argument("--confirmed-by", default=os.environ.get("USER", "operator"))
    confirm.set_defaults(func=cmd_confirm_started)

    check = subparsers.add_parser("check", help="Detect stale or unsafe handoff state.")
    check.add_argument("--agent", type=argparse_agent_name, default=DEFAULT_AGENT)
    check.add_argument("--state-file", type=Path)
    check.add_argument("--stale-hours", type=float, default=DEFAULT_STALE_HOURS)
    check.add_argument("--context-percent", type=float)
    check.add_argument("--context-threshold", type=float, default=DEFAULT_CONTEXT_THRESHOLD)
    check.set_defaults(func=cmd_check)

    audit = subparsers.add_parser("audit", help="Inspect local Codex thread/automation metadata.")
    audit.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    audit.add_argument("--include-monitor", action="store_true")
    audit.set_defaults(func=cmd_audit)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
