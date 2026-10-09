"""Send a prompt to a running Codex Desktop UI session via `codex exec resume`.

Lane 1 implementation from issue #2285 (agent bridge — send + receive to
running Codex UI / Cursor / Claude Code Desktop sessions).

## How it works

`codex exec resume <THREAD_UUID> --json -` (Codex CLI 0.133.0+) resumes a
persisted thread non-interactively. The subprocess emits a JSON event stream
on stdout containing turn events, item executions, and the agent's final
message. We feed the prompt via stdin (prefixed with a `Bridge-ID:` line for
correlation), then parse the stream.

## Empirical findings (2026-05-25 bridge probe)

The probe ran `codex exec resume 019e6063-... --json -` with a small prompt,
targeting a thread that the Codex Desktop process held open for write.
Observed behavior:

1. The original session JSONL grew (codex APPENDED events). The live UI
   process (PID 83697) and the resume subprocess BOTH wrote to the same
   rollout file. The thread state is consistent on disk regardless of
   which subprocess produced an event.
2. A NEW parallel rollout JSONL was ALSO created (new UUID, sharing thread
   history). This is harmless overhead — both files reflect the same turn.
3. The resume subprocess inherits the caller's CWD. Codex executed
   `git rev-parse --short HEAD` and saw the caller's commit SHA, NOT the
   UI session's worktree HEAD. Callers wanting the work to happen in a
   specific worktree must `cd` there before invoking (or use `cwd=` here).
4. Whether the visible Codex Desktop window displays the new turn live is
   not verified here. The thread state is consistent on disk — re-opening
   the same thread in the UI shows the appended events regardless.

## Usage from CLI

    ab send-codex-ui --thread <UUID> "your message"
    ab send-codex-ui --thread <UUID> --from-file relay.md
    ab send-codex-ui --thread <UUID> --cwd ~/some/worktree "message"

## Usage from Python

From outside the package (tests, tools), import `send` from the module
`scripts.ai_agent_bridge._ui_codex`; from inside the package, siblings use
the relative form (`from ._ui_codex import send`):

    result = send(thread_id="019e6063-...", message="ping", cwd=Path("/tmp"))
    print(result["final_message"])
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.common.jsonl import jsonl_lines as split_jsonl_lines

CODEX_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_TIMEOUT_S = 1800  # 30 min — covers most multi-turn dispatches


# Rollout `event_msg` names from codex-rs protocol::EventMsg (v1 wire, plus aliases).
_TURN_START = frozenset({"task_started", "turn_started"})
_TURN_END = frozenset({"task_complete", "turn_complete", "turn_aborted"})


@dataclass(frozen=True)
class LiveSession:
    """An exact thread and execution context from the lease owner's child."""

    thread_id: str
    cwd: Path
    environment: dict[str, str] = field(repr=False)
    rollout: Path | None = None


def find_live_session(lease: dict) -> LiveSession | None:
    """Read only the matching local Codex process's open rollout metadata.

    Supervisor session IDs are not native thread UUIDs. Never select a rollout
    by recency, or use a PID without checking its inherited lease envelope.
    """
    import psutil

    pid = lease.get("holder", {}).get("process_id")
    if type(pid) is not int or pid <= 0:
        return None
    expected = {
        "SESSION_STREAM_SESSION_ID": str(lease["session_id"]),
        "SESSION_STREAM_LEASE_ID": str(lease["lease_id"]),
        "SESSION_STREAM_GENERATION": str(lease["generation"]),
        "SESSION_STREAM_FENCING_TOKEN": str(lease["fencing_token"]),
    }
    matches: dict[str, LiveSession] = {}
    try:
        root = psutil.Process(pid)
        processes = [root, *root.children(recursive=True)]
        for process in processes:
            try:
                if process.name() != "codex":
                    continue
                environment = process.environ()
                if any(environment.get(key) != value for key, value in expected.items()):
                    continue
                for opened in process.open_files():
                    path = Path(opened.path)
                    if not path.name.startswith("rollout-") or path.suffix != ".jsonl":
                        continue
                    with path.open(encoding="utf-8") as handle:
                        metadata = json.loads(handle.readline())
                    if metadata.get("type") != "session_meta":
                        continue
                    payload = metadata["payload"]
                    thread_id = str(uuid.UUID(payload["id"]))
                    cwd = Path(payload["cwd"])
                    if not cwd.is_absolute():
                        continue
                    matches[thread_id] = LiveSession(thread_id, cwd, environment, rollout=path)
            except (psutil.Error, OSError, ValueError, KeyError, TypeError):
                continue
    except psutil.Error:
        return None
    return next(iter(matches.values())) if len(matches) == 1 else None


STALE_TURN_SECONDS = 600  # 10 minutes without a write means a mid-turn crash


def rollout_is_ready(path: Path) -> bool:
    """Return whether this rollout has no open turn.

    A file that only has ``session_meta`` is idle at the prompt. ``task_started``
    (and the ``turn_started`` alias) opens a turn; ``task_complete``,
    ``turn_complete``, or ``turn_aborted`` closes the matching ``turn_id``.
    A truncated last line is an in-flight append and fails closed.

    Reads backwards in chunks to bound work. Fails closed if the turn state
    cannot be determined within the cap.

    An unmatched historical start left by a crash is considered stale
    (and the pane ready) if the rollout has no writes for STALE_TURN_SECONDS.
    """
    import time
    try:
        stat = path.stat()
        size = stat.st_size
        mtime = stat.st_mtime
    except OSError:
        return False

    if size == 0:
        return False

    open_ids: set[str] = set()
    anonymous = 0
    cap_bytes = 1024 * 1024  # 1 MB cap
    chunk_size = 64 * 1024   # 64 KB chunk

    bytes_read = 0
    remainder = b""
    pos = size

    def _check_stale(busy: bool) -> bool:
        if busy:
            return time.time() - mtime > STALE_TURN_SECONDS
        return True

    try:
        with path.open("rb") as f:
            while pos > 0 and bytes_read < cap_bytes:
                read_size = min(chunk_size, pos)
                pos -= read_size
                f.seek(pos)
                chunk = f.read(read_size)
                bytes_read += read_size

                lines = (chunk + remainder).split(b"\n")
                if pos > 0:
                    remainder = lines[0]
                    lines = lines[1:]
                else:
                    remainder = b""

                for line in reversed(lines):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        record = json.loads(stripped)
                    except json.JSONDecodeError:
                        return False  # fail closed on incomplete json

                    if not isinstance(record, dict):
                        return False

                    kind, turn_id = _rollout_turn_marker(record)
                    if kind in _TURN_END:
                        if turn_id:
                            open_ids.add(turn_id)
                        elif kind == "turn_aborted":
                            return _check_stale(False)
                        else:
                            anonymous += 1
                    elif kind in _TURN_START:
                        if turn_id:
                            if turn_id in open_ids:
                                open_ids.discard(turn_id)
                            else:
                                return _check_stale(True)
                        else:
                            if anonymous > 0:
                                anonymous -= 1
                            else:
                                return _check_stale(True)
            if remainder:
                stripped = remainder.strip()
                if stripped:
                    try:
                        record = json.loads(stripped)
                        if isinstance(record, dict):
                            kind, turn_id = _rollout_turn_marker(record)
                            if kind in _TURN_START:
                                if turn_id:
                                    if turn_id not in open_ids:
                                        return _check_stale(True)
                                else:
                                    if anonymous == 0:
                                        return _check_stale(True)
                    except json.JSONDecodeError:
                        return False
    except OSError:
        return False

    if pos > 0:
        return False

    return _check_stale(bool(open_ids or anonymous > 0))


def _rollout_turn_marker(record: dict) -> tuple[str | None, str | None]:
    """Return the turn boundary name and turn id from one rollout record."""
    payload = record.get("payload") if record.get("type") == "event_msg" else record
    if not isinstance(payload, dict):
        return None, None
    kind = payload.get("type")
    turn_id = payload.get("turn_id")
    if not isinstance(kind, str) or kind not in _TURN_START | _TURN_END:
        return None, None
    return kind, turn_id if isinstance(turn_id, str) and turn_id else None


def resume_receipt(result: dict) -> dict:
    """Compact proof that a resume landed: thread, exit, and turn ids."""
    events = result.get("events") or []
    compact = {key: value for key, value in result.items() if key != "events"}
    compact["event_count"] = len(events)
    compact["event_types"] = [
        event.get("type") for event in events if isinstance(event, dict) and isinstance(event.get("type"), str)
    ]
    turn_ids: list[str] = []
    for event in events:
        if not isinstance(event, dict) or event.get("type") != "turn.started":
            continue
        turn_id = event.get("turn_id") or event.get("id")
        if isinstance(turn_id, str) and turn_id:
            turn_ids.append(turn_id)
    compact["turn_ids"] = turn_ids
    return compact


def find_session_file(thread_id: str) -> Path | None:
    """Locate the most recent rollout JSONL for a given thread UUID.

    Codex stores session JSONLs as
    `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<UUID>.jsonl`. The
    `<UUID>` segment matches the thread id. There may be multiple files
    per thread when `codex exec resume` has been invoked previously; we
    return the most recently modified.
    """
    matches = sorted(
        CODEX_SESSIONS_ROOT.glob(f"**/rollout-*{thread_id}.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def _extract_final_message(events: list[dict]) -> str | None:
    """Pick the last informative message from a stream of resume events.

    Prefer the last `agent_message` content. Fall back to the last
    completed `command_execution`'s aggregated_output if no agent_message
    fired (e.g. when the prompt asked codex to print a shell line directly).
    """
    final_agent_msg: str | None = None
    final_cmd_output: str | None = None
    for evt in events:
        if evt.get("type") != "item.completed":
            continue
        item = evt.get("item", {})
        item_type = item.get("type")
        if item_type == "agent_message":
            final_agent_msg = item.get("text") or item.get("content")
        elif item_type == "command_execution":
            final_cmd_output = item.get("aggregated_output")
    return final_agent_msg or final_cmd_output


def send(
    thread_id: str,
    message: str,
    *,
    bridge_id: str | None = None,
    cwd: Path | None = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    environment: dict[str, str] | None = None,
) -> dict:
    """Send a prompt to a running Codex Desktop UI session via `codex exec resume`.

    Args:
        thread_id: UUID of the persisted codex thread (find via
            `codex sessions list` or by inspecting `~/.codex/sessions/`
            for a rollout JSONL whose codex process holds it open for write).
        message: prompt body. A `Bridge-ID: <id>` line is prepended for
            correlation; the receiving agent should echo the Bridge-ID
            in its reply if asked.
        bridge_id: correlation id (auto-generated if None).
        cwd: working directory for the codex subprocess. If None, inherits
            the caller's cwd. Codex will run shell commands against this
            directory's git state — important when targeting a worktree.
        timeout_s: max wall-clock for the codex subprocess (default 30 min).
        environment: inherited driver environment when resuming a leased thread.

    Returns:
        dict with:
            bridge_id (str), thread_id (str), exit_code (int),
            events (list[dict] of parsed JSON event lines from stdout),
            final_message (str | None) — best-effort extraction,
            duration_s (float), session_file (str | None) — path to the
            original UI session JSONL if locatable, stderr (str).
    """
    bridge_id = bridge_id or f"bridge-{uuid.uuid4().hex[:8]}"
    framed_message = f"Bridge-ID: {bridge_id}\n\n{message}"
    session_file = find_session_file(thread_id)

    start = datetime.now(UTC)
    try:
        proc = subprocess.run(
            ["codex", "exec", "resume", "--json", "--disable", "apps", thread_id, "-"],
            input=framed_message,
            cwd=str(cwd) if cwd else None,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except FileNotFoundError as exc:
        stdout = ""
        stderr = f"codex exec resume unavailable: {exc}"
        exit_code = 127
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        stderr = f"[timeout after {timeout_s}s]\n{stderr}"
        exit_code = -1
    duration_s = (datetime.now(UTC) - start).total_seconds()

    events: list[dict] = []
    for line in split_jsonl_lines(stdout):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    return {
        "bridge_id": bridge_id,
        "thread_id": thread_id,
        "exit_code": exit_code,
        "events": events,
        "final_message": _extract_final_message(events),
        "duration_s": duration_s,
        "session_file": str(session_file) if session_file else None,
        "stderr": stderr,
    }


def cli_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ab send-codex-ui",
        description=(
            "Send a prompt to a running Codex Desktop UI session via "
            "`codex exec resume`. Lane 1 from issue #2285. "
            "Returns the codex subprocess exit code."
        ),
    )
    parser.add_argument(
        "--thread",
        required=True,
        help=(
            "Codex thread UUID. Find via `codex sessions list --last` or "
            "by inspecting `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`"
            " (the file whose codex process holds it open for write)."
        ),
    )
    parser.add_argument(
        "--bridge-id",
        default=None,
        help="Correlation id (auto-generated if not given).",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help=(
            "Working directory for the codex subprocess. Codex will run "
            "shell commands against this directory's git state — point it "
            "at the target worktree when relevant."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_S,
        help=f"Max wall-clock seconds (default {DEFAULT_TIMEOUT_S}).",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        help="Read message body from a file (use '-' for stdin).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as compact JSON (excludes the verbose events list).",
    )
    parser.add_argument(
        "message",
        nargs="?",
        help="Inline message text. Mutually exclusive with --from-file.",
    )
    args = parser.parse_args(argv)

    if args.from_file and args.message:
        parser.error("provide either --from-file or a positional message, not both")
    if args.from_file:
        message = (
            sys.stdin.read()
            if str(args.from_file) == "-"
            else args.from_file.read_text(encoding="utf-8")
        )
    elif args.message:
        message = args.message
    else:
        parser.error("must provide a message via positional arg or --from-file")

    result = send(
        thread_id=args.thread,
        message=message,
        bridge_id=args.bridge_id,
        cwd=args.cwd,
        timeout_s=args.timeout,
    )

    if args.json:
        print(json.dumps(resume_receipt(result), indent=2, default=str))
    else:
        print(f"thread:       {result['thread_id']}")
        print(f"bridge_id:    {result['bridge_id']}")
        print(f"exit_code:    {result['exit_code']}")
        print(f"duration_s:   {result['duration_s']:.2f}")
        print(f"events:       {len(result['events'])}")
        print(f"session_file: {result['session_file']}")
        if result["final_message"]:
            print()
            print("=== final message ===")
            print(result["final_message"])
        if result["stderr"]:
            print()
            print("=== stderr (truncated) ===")
            print(result["stderr"][:2000])

    return 0 if result["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(cli_main())
