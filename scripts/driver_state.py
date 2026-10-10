"""Pinned per-epic driver state: who am I, what epic, which goals.

Long-running driver sessions lose their launch prompt when the harness
compacts context: the epic binding and the current goals lived only in the
first user turn. This module keeps them in a small local state file that the
harness re-reads on every model call, so compaction cannot drop them.

State file: ``<repo>/.claude/<epic>-epic/DRIVER-STATE.md`` (gitignored local
state, next to the epic's driver handoffs). The launcher exports
``LU_DRIVER_STATE_FILE`` for driver sessions; without it, nothing is injected.

Commands::

    .venv/bin/python -m scripts.driver_state whoami     # epic, seat, model, next step
    .venv/bin/python -m scripts.driver_state goals      # full pinned state
    .venv/bin/python -m scripts.driver_state path [--epic E]
    .venv/bin/python -m scripts.driver_state init --epic E [--force]
    .venv/bin/python -m scripts.driver_state agy-hook          # AGY PreInvocation hook
    .venv/bin/python -m scripts.driver_state agy-stop-hook     # AGY Stop hook
    .venv/bin/python -m scripts.driver_state agy-pretool-hook  # AGY PreToolUse(ask_question)

The ``agy-hook`` command implements the AGY ``PreInvocation`` contract: it
reads the hook payload on stdin and prints ``{"injectSteps": [{"ephemeralMessage":
...}]}``. An ephemeral message is transient (not stored in the transcript), so
it is re-injected before every model call and survives any compaction. The
hook rejects an oversized rendered envelope visibly, without clipping goals.

``agy-stop-hook`` implements the AGY ``Stop`` contract. A driver must not end a
turn on a question or a plan, with fewer of its own workers running than the
private ``LU_DRIVER_MIN_WORKERS`` target, or with nothing armed to wake it.
An absent or invalid target is unknown and cannot force a worker-count continuation. In those cases it returns
``{"decision": "continue", "reason": ...}`` and AGY re-enters the loop with the
reason as a system message. A turn whose final text starts with
``CTO-ESCALATION:`` (deletes, money, security, rule changes) may stop. A
per-conversation counter caps consecutive continuations when its private storage
is available. Exhaustion returns ``decision: allow`` with a visible gate failure and
records its typed cause. Counter errors preserve required continuation while
allowing clean reports and escalations to stop.
``agy-pretool-hook`` denies the interactive
``ask_question`` tool for driver sessions: nobody answers it in a driver pane.
Uses the shared project interpreter and its installed CommonMark parser.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from markdown_it import MarkdownIt

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.common.jsonl import jsonl_lines
from scripts.common.task_store_paths import tasks_dir
from scripts.driver_blockers import LEDGER_NAME, USAGE_RULE, show_summary

STATE_ENV = "LU_DRIVER_STATE_FILE"
STATE_NAME = "DRIVER-STATE.md"
MAX_INJECT_CHARS = 6000
MIN_WORKERS_ENV = "LU_DRIVER_MIN_WORKERS"
MAX_CONSECUTIVE_CONTINUES = 4
ESCALATION_MARKER = "CTO-ESCALATION:"
LIVE_WORKER_STATUSES = frozenset({"spawning", "running"})
# AGY reports a normal end of turn as NO_TOOL_CALL (docs also show model_stop).
SKIP_TERMINATION_REASONS = frozenset({"ERROR", "MAX_INVOCATIONS", "MAX_STEPS_EXCEEDED", "USER_CANCELED", "HALTED_STEP"})

POLICY_TITLE = "Standing decision policy"
POLICY = f"""## {POLICY_TITLE}
- Decide reversible, rule-following choices yourself and execute them now. Pick the option that obeys the rules (cross-family review, then CI Gate, then merge queue) and do it.
- Never ask for an admission or gate override; the answer is always no. Use the clean path (fresh recorded branch, rebase, new commit).
- When you list an action for yourself, do it in the same turn; never end a turn on a plan.
- Ask the CTO only about deleting data, spending money, security or secrets, rule changes, or a true conflict between two operator rules. Post it through Fleet Comms and start the final message with `{ESCALATION_MARKER}`.
- End every turn with the privately configured worker target met and a wake-up armed (a background `delegate.py wait` or the `schedule` tool), never with a question.
"""
BLOCKER_POLICY_TITLE = "CTO blocker delta policy"
BLOCKER_POLICY = f"## {BLOCKER_POLICY_TITLE}\n{USAGE_RULE}\n"
# Preserve the former total envelope budget (state, policy and wrapper), but
# apply it to the complete rendered message rather than truncating the state.
MAX_ENVELOPE_CHARS = MAX_INJECT_CHARS + len(POLICY) + len(BLOCKER_POLICY) + 600

TEMPLATE = """# Driver state: {epic}

<!-- Pinned driver state. Re-injected before every model call (AGY hook).
     Keep it short (under ~4 KB). Update Goals/Next as work lands. -->

## Epic
- Stream: {epic}
- Seat: driver (one per stream; the launcher owns the lease)
- Handoff: .claude/{epic}-epic/ (read the newest driver handoff on cold start)

## Current goals (bounded, each with a definition of done)
1. <goal> — DONE WHEN: <observable, tool-checkable condition>

## Hard rules
- Never self-merge; landing order is cross-family review at the exact head, then CI Gate, then the merge queue.
- No secrets or deployment details in the public repo.

{policy}
{blocker_policy}
## Next step
- <single next action>
"""


def _repo_root(start: Path | None = None) -> Path:
    start = start or Path.cwd()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        if out:
            return Path(out)
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def state_path(epic: str | None = None, root: Path | None = None) -> Path | None:
    """Resolve the state file: explicit epic wins, then the launcher env."""
    if epic:
        return (root or _repo_root()) / ".claude" / f"{epic}-epic" / STATE_NAME
    env = os.environ.get(STATE_ENV, "").strip()
    if env:
        return Path(env)
    session_epic = os.environ.get("SESSION_EPIC", "").strip()
    if session_epic:
        return (root or _repo_root()) / ".claude" / f"{session_epic}-epic" / STATE_NAME
    return None


def _state_root(path: Path) -> Path:
    # <root>/.claude/<epic>-epic/DRIVER-STATE.md -> <root>
    return path.resolve().parent.parent.parent


def _read_state(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section(text: str, title: str) -> list[str]:
    lines, inside = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line[3:].strip().lower().startswith(title.lower())
            continue
        if inside and line.strip():
            lines.append(line)
    return lines


def render_injection(text: str, path: Path) -> str:
    if POLICY_TITLE.lower() not in text.lower():
        text = text.rstrip() + "\n\n" + POLICY
    tokens = MarkdownIt().parse(text)
    lines = text.splitlines()
    headings = {
        tokens[index + 1].content
        for index, token in enumerate(tokens)
        if token.type == "heading_open"
        and token.markup == "##"
        and token.level == 0
        and lines[token.map[0]].startswith("## ")
    }
    if BLOCKER_POLICY_TITLE not in headings:
        text = text.rstrip() + "\n\n" + BLOCKER_POLICY
    message = (
        "PINNED DRIVER STATE (re-injected every model call; authoritative over any "
        "compacted summary). You are the driver for the epic below. Re-orient from it "
        "before acting; update the file when a goal lands. Full file: "
        f"{path.name} under .claude/; CLI: `.venv/bin/python -m scripts.driver_state whoami|goals`.\n\n" + text.strip()
    )
    if len(message) > MAX_ENVELOPE_CHARS:
        raise ValueError(
            "DRIVER-GATE-FAILED: complete driver-state envelope exceeds the allowed size; no goals injected."
        )
    return message


def _payload(stdin_text: str) -> dict:
    try:
        payload = json.loads(stdin_text) if stdin_text.strip() else {}
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _driver_session(payload: dict) -> Path | None:
    """State path when this hook runs inside the launcher's driver session."""
    path = state_path() if os.environ.get(STATE_ENV, "").strip() else None
    if path is None or not path.is_file() or not os.environ.get("SESSION_HANDOFF_AGENT", "").strip():
        return None
    workspaces = payload.get("workspacePaths")
    if not isinstance(workspaces, list) or len(workspaces) != 1 or not isinstance(workspaces[0], str):
        return None
    try:
        if not workspaces[0].strip() or Path(workspaces[0]).resolve() != _state_root(path):
            return None
    except (OSError, RuntimeError, ValueError):
        return None
    return path


def cmd_agy_hook(stdin_text: str) -> dict:
    payload = _payload(stdin_text)
    path = _driver_session(payload)
    if path is None:
        return {}
    text = _read_state(path)
    try:
        message = render_injection(text, path)
    except ValueError as exc:
        return _gate_failure(
            path, str(payload.get("conversationId") or ""), "state_envelope_oversized", str(exc), hook="agy-hook"
        )
    return {"injectSteps": [{"ephemeralMessage": message}]}


_QUESTION_RE = re.compile(
    r"\b(should i|shall i|do you want|would you like|which (option|path) (do|would|should)|"
    r"please (confirm|choose|decide|advise)|awaiting (your|cto|operator)|let me know|"
    r"need(s)? (your|cto|operator) (decision|approval|input))",
    re.IGNORECASE,
)
_PLAN_RE = re.compile(
    r"\bi([’']ll| will)\s+(?:(?:now|next|then)\s+)?"
    r"(dispatch|rebase|start|run|open|fix|merge|enqueue|commit|push|implement|update|"
    r"check(?!\s+back\s+when\s+the\s+armed\s+wait\s+fires\b)|verify)\b",
    re.IGNORECASE | re.MULTILINE,
)
_PLAN_HEADING_RE = re.compile(r"^(?:#+\s*)?(next (steps?|actions?)|plan|pending actions?)(?:\s*:\s*(.*)|\s*)$", re.I)
_NO_PENDING_ACTION_RE = re.compile(r"^(?:none|nothing|complete|completed|done)\b(?:\s*[.!;—–-]|\s*$)", re.I)


def _message_prose(text: str) -> str:
    """Extract authored prose using CommonMark block and inline structure."""
    lines = []
    quote_depth = 0
    heading = False
    for token in MarkdownIt("commonmark").parse(text):
        if token.type == "blockquote_open":
            quote_depth += 1
        elif token.type == "blockquote_close":
            quote_depth -= 1
        elif token.type == "heading_open":
            heading = True
        elif token.type == "heading_close":
            heading = False
        elif token.type == "inline" and not quote_depth:
            prose = "".join(
                child.content if child.type == "text" else "\n" if child.type in {"softbreak", "hardbreak"} else " "
                for child in token.children or []
            )
            # Literal quoted questions in review prose are reported speech too.
            prose = re.sub(r'"[^"\n]*"|“[^”\n]*”|(?<!\w)\x27[^\x27\n]*\x27|‘[^’\n]*’', " ", prose)
            if prose.strip():
                lines.append(("# " if heading else "") + prose.strip())
    return "\n".join(lines)


def ends_on_question_or_plan(text: str) -> str | None:
    """Name why a final message must not end the turn, or None."""
    body = _message_prose(text).strip()
    if not body:
        return None
    tail = body[-1500:]
    last_line = body.splitlines()[-1].strip().rstrip("*_` ")
    if last_line.endswith("?"):
        return "your final message ends on a question"
    if _QUESTION_RE.search(tail):
        return "your final message asks for a decision"
    if _PLAN_RE.search(tail):
        return "your final message lists actions you have not done"
    lines = tail.splitlines()
    for i, line in enumerate(lines):
        match = _PLAN_HEADING_RE.match(line.strip())
        if match:
            actions = [(match[3] or "").strip(), *lines[i + 1 :]]
            actions = [action.strip() for action in actions if action.strip()]
            if actions and not _NO_PENDING_ACTION_RE.match(actions[0]):
                return "your final message lists actions you have not done"
    return None


def last_model_text(transcript_path: str | None) -> str:
    """Final text of the latest model response in an AGY transcript.jsonl."""
    if not transcript_path:
        return ""
    path = Path(os.path.expanduser(transcript_path))
    if not path.is_file():
        return ""
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - 512_000))
        chunk = handle.read().decode("utf-8", errors="replace")
    for line in reversed(jsonl_lines(chunk)):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("source") == "MODEL" and row.get("type") == "PLANNER_RESPONSE":
            content = row.get("content")
            if isinstance(content, str) and content.strip():
                return content
            if not row.get("tool_calls"):
                return ""
    return ""


def minimum_workers() -> int | None:
    """Read the private worker target; absent or invalid configuration is unknown."""
    raw = os.environ.get(MIN_WORKERS_ENV, "").strip()
    if not raw.isascii() or not raw.isdecimal():
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    return value if value > 0 else None


def running_workers(initiator: str) -> int | None:
    """Count own workers only after a nonce-bound live Monitor status probe."""
    from scripts.delegate import _TERMINAL_STATUSES, MonitorApiUnavailable, _fetch_monitor_task

    tasks = tasks_dir()
    if not initiator or not tasks.is_dir():
        return None
    count = 0
    deadline = time.monotonic() + 6
    for record in tasks.glob("*.json"):
        try:
            data = json.loads(record.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        if data.get("initiator") == initiator and data.get("status") in LIVE_WORKER_STATUSES:
            task_id, nonce = data.get("task_id"), data.get("run_nonce")
            if not isinstance(task_id, str) or not task_id or not isinstance(nonce, str) or not nonce:
                return None
            if time.monotonic() >= deadline:
                return None
            try:
                live = _fetch_monitor_task(task_id, run_nonce=nonce)
            except MonitorApiUnavailable:
                return None
            task = live.get("task") if isinstance(live, dict) else None
            if (
                not isinstance(task, dict)
                or task.get("task_id") != task_id
                or task.get("run_nonce") != nonce
                or task.get("initiator") != initiator
            ):
                return None
            if task.get("status") not in LIVE_WORKER_STATUSES | _TERMINAL_STATUSES:
                return None
            if task.get("status") in LIVE_WORKER_STATUSES:
                if live.get("alive") is not True:
                    continue
                count += 1
    return count


def _counter_path(state: Path, conversation_id: str) -> Path:
    directory = state.parent / "stop-counters"
    directory.mkdir(mode=0o700, exist_ok=True)
    info = directory.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise PermissionError("continuation counter directory must be private and owned by the current user")
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", conversation_id or "unknown")[:80]
    return directory / f"stop-{safe}.count"


def _bump_counter(state: Path, conversation_id: str) -> int:
    path = _counter_path(state, conversation_id)
    try:
        value = int(path.read_text(encoding="utf-8").strip() or "0") + 1
    except FileNotFoundError:
        value = 1
    if value <= 0:
        raise ValueError("invalid continuation counter")
    # Once exhausted, report the failure even if counter writes are broken.
    if value <= MAX_CONSECUTIVE_CONTINUES:
        path.write_text(str(value), encoding="utf-8")
    return value


def _reset_counter(state: Path, conversation_id: str) -> None:
    _counter_path(state, conversation_id).write_text("0", encoding="utf-8")


def _gate_failure(state: Path, conversation: str, code: str, reason: str, *, hook: str = "agy-stop-hook") -> dict:
    """Persist a typed failure and return the hook's visible protocol result.

    Counter mutation belongs exclusively to Stop, never PreInvocation.
    """
    failure = {
        "schema": "driver-gate-failure.v1",
        "status": "failed",
        "code": code,
        "recorded_at": datetime.now(UTC).isoformat(),
        "reason": reason,
    }
    try:
        _counter_path(state, conversation).with_suffix(".failure.json").write_text(
            json.dumps(failure), encoding="utf-8"
        )
    except OSError:
        # A storage fault must never turn a policy failure into a silent allow.
        print(json.dumps(failure), file=sys.stderr)
    if hook == "agy-hook":
        return {"injectSteps": [{"ephemeralMessage": reason}]}
    return {"decision": "allow" if hook == "agy-stop-hook" else "deny", "reason": reason}


def cmd_agy_stop_hook(stdin_text: str) -> dict:
    payload = _payload(stdin_text)
    path = _driver_session(payload)
    if path is None:
        return {"decision": "allow"}
    conversation = str(payload.get("conversationId") or "")
    reason = str(payload.get("terminationReason") or "").upper().removeprefix("EXECUTOR_TERMINATION_REASON_")
    if reason in SKIP_TERMINATION_REASONS:
        with contextlib.suppress(OSError):
            _reset_counter(path, conversation)
        return {"decision": "allow"}  # errors, limits and user cancels are not policy decisions
    text = last_model_text(payload.get("transcriptPath"))
    if text.strip().startswith(ESCALATION_MARKER) and _message_prose(text).startswith(ESCALATION_MARKER):
        with contextlib.suppress(OSError):
            _reset_counter(path, conversation)
        return {"decision": "allow"}
    reasons = []
    seat = os.environ.get("SESSION_HANDOFF_AGENT", "").strip()
    minimum = minimum_workers()
    workers = running_workers(seat) if minimum is not None else None
    if minimum is not None and workers is None:
        reasons.append("live worker count is unknown; restore worker telemetry before stopping")
    elif workers is not None and workers < minimum:
        reasons.append("your running workers are below the privately configured target; dispatch ready work")
    why = ends_on_question_or_plan(text)
    if why:
        reasons.append(f"{why}; decide per the policy and execute it now")
    if not reasons and payload.get("fullyIdle") is True:
        reasons.append(
            "nothing is armed to wake you; start a background `delegate.py wait` or set a `schedule` timer, then end the turn"
        )
    if not reasons:
        with contextlib.suppress(OSError):
            _reset_counter(path, conversation)
        return {"decision": "allow"}
    try:
        if _bump_counter(path, conversation) > MAX_CONSECUTIVE_CONTINUES:
            with contextlib.suppress(OSError):
                _reset_counter(path, conversation)
            return _gate_failure(
                path,
                conversation,
                "corrective_retry_budget_exhausted",
                "DRIVER-GATE-FAILED: corrective retry budget exhausted.",
            )
    except (OSError, ValueError):
        reasons.append("continuation counter unavailable")
    return {
        "decision": "continue",
        "reason": (
            "DRIVER-STATE standing decision policy: "
            + "; ".join(reasons)
            + f". Ask the CTO only about deletes, money, security or rule changes, via Fleet Comms, "
            f"with a final message starting `{ESCALATION_MARKER}`."
        ),
    }


def cmd_agy_pretool_hook(stdin_text: str) -> dict:
    payload = _payload(stdin_text)
    tool = (payload.get("toolCall") or {}).get("name")
    if tool != "ask_question":
        return {"decision": "allow"}
    if _driver_session(payload) is None:
        return {"decision": "allow"}
    return {
        "decision": "deny",
        "reason": (
            "Driver sessions have no one at the prompt. Decide reversible, rule-following choices "
            "yourself and execute them. For deletes, money, security or rule changes, post to the CTO "
            f"via Fleet Comms and start your final message with `{ESCALATION_MARKER}`."
        ),
    }


def cmd_whoami(path: Path | None) -> int:
    epic = os.environ.get("SESSION_EPIC", "") or "(unset)"
    seat = os.environ.get("SESSION_HANDOFF_AGENT", "") or "(unset)"
    print(f"epic: {epic}")
    print(f"seat: {seat}")
    if path is None:
        print("state: (no LU_DRIVER_STATE_FILE / SESSION_EPIC; not a driver session)")
        return 1
    print("state: (configured)")
    print(show_summary(path.parent / LEDGER_NAME, epic))
    if not path.is_file():
        print("state file missing; create it with: init --epic <epic>")
        return 1
    text = path.read_text(encoding="utf-8")
    for title in ("Epic", "Next step"):
        body = _section(text, title)
        if body:
            print(f"{title.lower()}:")
            print("\n".join(body))
    goals = _section(text, "Current goals")
    if goals:
        print("goals:")
        print("\n".join(goals))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="driver_state",
        description="Pinned per-epic driver state survives context compaction.\nUse in launcher-owned drivers; ordinary sessions receive no driver policy.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.driver_state whoami
  .venv/bin/python -m scripts.driver_state init --epic infra
  .venv/bin/python -m scripts.driver_state agy-stop-hook < hook-payload.json
Outputs: init writes private driver state; hooks emit JSON and private failure/counter records.
Exit codes: 0 success (hooks report failures in JSON); 1 missing state or refused overwrite.
Related: scripts/agy_hooks/driver_state_inject.sh; #10201, #10297.
""",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami", help="Print epic, seat, goals, next step and CTO blocker baseline summary.")
    sub.add_parser("goals", help="Print the full pinned state file.")
    p_path = sub.add_parser("path", help="Print the state file path.")
    p_path.add_argument("--epic", help="Epic selector, for example infra (default: launcher environment).")
    p_init = sub.add_parser("init", help="Write a template state file for an epic.")
    p_init.add_argument("--epic", required=True, help="Epic selector to initialize, for example infra.")
    p_init.add_argument("--force", action="store_true", help="Overwrite an existing file (default: false).")
    sub.add_parser("agy-hook", help="AGY PreInvocation hook: stdin payload -> injectSteps JSON.")
    sub.add_parser("agy-stop-hook", help="AGY Stop hook: continue when the turn ends against policy.")
    sub.add_parser("agy-pretool-hook", help="AGY PreToolUse hook: deny ask_question for drivers.")
    args = parser.parse_args(argv)

    hooks = {"agy-hook": cmd_agy_hook, "agy-stop-hook": cmd_agy_stop_hook, "agy-pretool-hook": cmd_agy_pretool_hook}
    if args.cmd in hooks:
        stdin_text = sys.stdin.read()
        try:
            result = hooks[args.cmd](stdin_text)
        except Exception:  # keep the hook protocol valid and expose driver errors
            payload = _payload(stdin_text)
            path = _driver_session(payload)
            if path is not None:
                if args.cmd == "agy-stop-hook":
                    with contextlib.suppress(OSError):
                        _reset_counter(path, str(payload.get("conversationId") or ""))
                result = _gate_failure(
                    path,
                    str(payload.get("conversationId") or ""),
                    "hook_error",
                    "DRIVER-GATE-FAILED: driver-state hook error.",
                    hook=args.cmd,
                )
            else:
                result = {} if args.cmd == "agy-hook" else {"decision": "allow"}
        sys.stdout.write(json.dumps(result))
        return 0
    if args.cmd == "whoami":
        return cmd_whoami(state_path())
    if args.cmd == "goals":
        path = state_path()
        if path is None or not path.is_file():
            print("no pinned driver state (see: whoami)", file=sys.stderr)
            return 1
        sys.stdout.write(path.read_text(encoding="utf-8"))
        return 0
    if args.cmd == "path":
        path = state_path(args.epic)
        if path is None:
            print("no epic: pass --epic or run inside a driver session", file=sys.stderr)
            return 1
        print(path)
        return 0
    if args.cmd == "init":
        path = state_path(args.epic)
        assert path is not None
        if path.exists() and not args.force:
            print(f"exists: {path} (use --force to overwrite)", file=sys.stderr)
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(TEMPLATE.format(epic=args.epic, policy=POLICY, blocker_policy=BLOCKER_POLICY), encoding="utf-8")
        print(path)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
