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
import codecs
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import ijson

from scripts.common.jsonl import jsonl_lines as split_jsonl_lines

CODEX_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
DEFAULT_TIMEOUT_S = 1800  # 30 min — covers most multi-turn dispatches


# Wire names observed in installed CLI rollouts; task_* are v1 wire names for
# TurnStarted/TurnComplete in codex-rs/protocol/src/protocol.rs.
_TURN_START = frozenset({"task_started", "turn_started"})
_TURN_END = frozenset({"task_complete", "turn_complete", "turn_aborted"})
_READ_CHUNK = 64 * 1024
_CACHE_GUARD_BYTES = 4096
_STABLE_READ_ATTEMPTS = 3


class _RolloutRecord:
    """Validate one JSON record, retaining only bounded strings and two types.

    ijson validates grammar. The lexical filter validates every string's escapes
    and UTF-8, but replaces long strings with an empty string before ijson sees
    them: its normal string events would otherwise allocate the entire body.
    No lifecycle decision is made from text, key order or a record prefix.
    """

    def __init__(self) -> None:
        self.depth = 0
        self.payload_depth = None
        self.key = None
        self.outer_type = None
        self.payload_type = None
        self.turn_id = None
        self.turn_id_valid = True
        self.turn_id_seen = False
        self.seen = set()
        self.has_content = False
        self.in_string = False
        self.escape = False
        self.unicode_left = 0
        self.string = bytearray()
        self.long_string = False
        self.number_length = 0
        self.decoder = codecs.getincrementaldecoder("utf-8")()
        self.target = self._events()
        self.parser = ijson.basic_parse_coro(self.target)

    @ijson.coroutine
    def _events(self):
        while True:
            event, value = (yield)
            if event == "map_key":
                if self.depth == self.payload_depth and value == "turn_id":
                    if self.turn_id_seen:
                        self.turn_id_valid = False
                    self.turn_id_seen = True
                self.key = value
                if (self.depth == 1 and value in {"type", "payload"}) or (
                    self.depth == self.payload_depth and value == "type"
                ):
                    identity = (self.depth, value)
                    if identity in self.seen:
                        raise ValueError("duplicate lifecycle field")
                    self.seen.add(identity)
                continue
            if self.depth == self.payload_depth and self.key == "turn_id" and event in {"start_map", "start_array"}:
                self.turn_id_valid = False
            if event in {"start_map", "start_array"}:
                if self.depth == 0 and event != "start_map":
                    raise ValueError("rollout record is not an object")
                if self.depth == 1 and self.key == "payload" and event == "start_map":
                    self.payload_depth = 2
                self.depth += 1
                if self.depth > 256:
                    raise RecursionError("rollout JSON nesting exceeds decoder safety limit")
            elif event in {"end_map", "end_array"}:
                if self.depth == self.payload_depth:
                    self.payload_depth = None
                self.depth -= 1
            elif self.depth == 0:
                raise ValueError("rollout record is not an object")
            elif event == "string" and self.key == "type":
                if self.depth == 1:
                    self.outer_type = value
                elif self.depth == self.payload_depth:
                    self.payload_type = value
            if self.depth == self.payload_depth and self.key == "turn_id":
                if event == "string" and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
                    self.turn_id = value
                else:
                    self.turn_id_valid = False
            self.key = None

    def feed(self, data: bytes) -> None:
        self.decoder.decode(data)  # Strict validation, including skipped bodies.
        output = bytearray()
        index = 0
        while index < len(data):
            byte = data[index]
            if not self.in_string:
                self.has_content |= byte not in b" \t\r"
                if byte == 34:
                    self.in_string = True
                    self.string = bytearray(b'"')
                    self.long_string = False
                    self.number_length = 0
                else:
                    output.append(byte)
                    if byte in b"0123456789.eE+-":
                        self.number_length += 1
                        if self.number_length > 4300:
                            raise ValueError("rollout numeric token exceeds decoder safety limit")
                    else:
                        self.number_length = 0
                index += 1
                continue
            # Skip ordinary string spans in bulk, with bounded capture. This
            # regex only locates JSON string delimiters/escapes/control bytes.
            if not self.escape and not self.unicode_left:
                special = _STRING_SPECIAL.search(data, index)
                end = special.start() if special else len(data)
                if end > index:
                    if not self.long_string:
                        if len(self.string) + end - index <= 256:
                            self.string.extend(data[index:end])
                        else:
                            self.long_string = True
                            self.string.clear()
                    index = end
                    if index == len(data):
                        break
                    byte = data[index]
            if not self.long_string:
                self.string.append(byte)
                if len(self.string) > 256:
                    self.long_string = True
                    self.string.clear()
            if self.unicode_left:
                if byte not in b"0123456789abcdefABCDEF":
                    raise ValueError("invalid JSON unicode escape")
                self.unicode_left -= 1
            elif self.escape:
                if byte == ord("u"):
                    self.unicode_left = 4
                elif byte not in b'"\\/bfnrt':
                    raise ValueError("invalid JSON escape")
                self.escape = False
            elif byte == 92:
                self.escape = True
            elif byte == 34:
                self.in_string = False
                if self.long_string:
                    output.extend(b'""')
                elif b"\\u" in self.string:
                    # The streaming backend may reject lone surrogate escapes.
                    # Decode bounded strings using JSON's escape grammar, then
                    # replace unpaired code units before passing them on. They
                    # cannot match the ASCII lifecycle keys or event names.
                    output.extend(json.dumps(json.loads(self.string), ensure_ascii=False).encode("utf-8", errors="replace"))
                else:
                    output.extend(self.string)
                self.string.clear()
            elif byte < 32:
                raise ValueError("unescaped control byte in JSON string")
            index += 1
        if output:
            self.parser.send(bytes(output))

    def finish(self) -> str | None:
        self.decoder.decode(b"", final=True)
        if self.in_string:
            raise ValueError("unterminated JSON string")
        try:
            if self.has_content:
                self.parser.close()  # Reject incomplete/malformed records before deciding.
        finally:
            self.target.close()
        return self.payload_type if self.outer_type == "event_msg" else None


_STRING_SPECIAL = re.compile(br'["\\\x00-\x1f]')


class _OpenTurns:
    """Separate from readiness: count open turns and retain any overlap."""

    def __init__(self):
        self.ids = set()
        self.anonymous = 0
        self.begin()

    @property
    def count(self):
        return len(self.ids) + self.anonymous

    def begin(self):
        self.starts = 0
        self.ends = 0
        self.peak = self.count
        self.overlap_ids = []
        self.overlap = False
        self.ambiguous = False

    def observe(self, kind, record):
        if kind not in _TURN_START | _TURN_END:
            return
        if not record.turn_id_valid:
            self.ambiguous = True
            return
        turn_id = record.turn_id
        if kind in _TURN_START:
            if turn_id and turn_id in self.ids:
                return  # Repeated wire record for the same open turn.
            if self.count >= 1024:
                self.ambiguous = True  # Bound retained IDs, never guess CLEAN.
                return
            self.starts += 1
            if turn_id:
                self.ids.add(turn_id)
            else:
                self.anonymous += 1
            self.peak = max(self.peak, self.count)
            if self.count > 1:
                if not self.overlap:
                    self.overlap_ids = sorted(self.ids)
                self.overlap = True
        else:
            if turn_id in self.ids:
                self.ids.remove(turn_id)
            elif self.anonymous:
                self.anonymous -= 1
            elif not turn_id and self.ids:
                if len(self.ids) > 1:
                    # An idless end decrements the count, but cannot identify
                    # which named turn remains. Retain uncertainty this wake.
                    self.anonymous = len(self.ids) - 1
                    self.ambiguous = True
                self.ids.clear()
            else:
                self.ambiguous = True
                return
            self.ends += 1


class RolloutReader:
    """Forward incremental lifecycle reader for one live rollout, bounded memory.

    Keep this instance across watcher polls. Partial records remain in the
    streaming parser; a decoder failure remains BUSY until file replacement or
    truncation. Inode change, truncation, same-size rewrites and changes to the
    cached prefix fingerprint reset the cache. The fingerprint samples the head
    and bytes immediately before the cached offset, keeping append polls bounded.
    ``after_read`` is a deterministic race-test hook, never a sleep or a clock.
    """

    def __init__(self, *, after_read: Callable[[], None] | None = None) -> None:
        self.after_read = after_read
        self.path = None
        self.signature = None
        self.offset = 0
        self.state = (True, "no_lifecycle_event")
        self.record = None
        self.error = None
        self.guard_offset = 0
        self.guard_digest = None
        self.turns = _OpenTurns()
        self.epoch = 0

    def _reset(self, path, signature):
        if self.record is not None:
            self.record.target.close()
        self.path = path
        self.signature = signature
        self.offset = 0
        self.state = (True, "no_lifecycle_event")
        self.record = None
        self.error = None
        self.guard_offset = 0
        self.guard_digest = None
        self.turns = _OpenTurns()
        self.epoch += 1

    @staticmethod
    def _prefix_fingerprint(stream, offset):
        """Hash two bounded cached-history spans without reparsing old records."""
        stream.seek(0)
        head = stream.read(min(offset, _CACHE_GUARD_BYTES))
        stream.seek(max(0, offset - _CACHE_GUARD_BYTES))
        boundary = stream.read(min(offset, _CACHE_GUARD_BYTES))
        return hashlib.sha256(head + boundary).digest()

    def ready(self, path: Path) -> tuple[bool, str]:
        if self.error and self.error.startswith("read_error:"):
            self._reset(path, None)  # Transient I/O faults are retried on the next poll.
        try:
            for _ in range(_STABLE_READ_ATTEMPTS):
                with path.open("rb") as stream:
                    before = os.fstat(stream.fileno())
                    signature = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
                    if self.path != path or self.signature is None or (
                        signature[:2] != self.signature[:2] or before.st_size < self.signature[2]
                        or (signature[2] == self.signature[2] and signature[3] != self.signature[3])
                        or (self.guard_digest is not None and self._prefix_fingerprint(stream, self.guard_offset) != self.guard_digest)
                    ):
                        self._reset(path, signature)
                    stream.seek(self.offset)
                    while self.offset < before.st_size and self.error is None:
                        data = stream.read(min(_READ_CHUNK, before.st_size - self.offset))
                        if not data:
                            break
                        self.offset += len(data)
                        pieces = data.split(b"\n")
                        for index, piece in enumerate(pieces):
                            if piece:
                                if self.record is None:
                                    self.record = _RolloutRecord()
                                self.record.feed(piece)
                            if index < len(pieces) - 1 and self.record is not None:
                                kind = self.record.finish()
                                self.turns.observe(kind, self.record)
                                if kind in _TURN_START:
                                    self.state = (False, f"start_event:{kind}")
                                elif kind in _TURN_END:
                                    self.state = (True, f"end_event:{kind}")
                                self.record = None
                    self.guard_digest = self._prefix_fingerprint(stream, self.offset)
                    self.guard_offset = self.offset
                    if self.after_read:
                        self.after_read()
                    after = path.stat()
                    final = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
                    self.signature = signature
                    if final != signature or (self.offset != before.st_size and self.error is None):
                        continue
                    if self.error:
                        return False, self.error
                    if self.record is not None:
                        return False, "partial_final_line"
                    return self.state
            return False, "rollout_changing"
        except Exception as exc:
            if self.record is not None:
                self.record.target.close()
            # No diagnostics contain transcript bodies, paths or decoder text.
            self.error = f"decode_error:{type(exc).__name__}" if not isinstance(exc, OSError) else f"read_error:{type(exc).__name__}"
            return False, self.error

    def begin_wake(self):
        """Freeze the final pre-send observation without changing readiness."""
        self.turns.begin()
        return self.epoch

    def wake_result(self, path: Path, *, epoch: int, resume_exited: bool) -> dict:
        """Read after resume, including starts appended after process exit."""
        _, reason = self.ready(path)
        turns = self.turns
        status = "UNKNOWN"
        if not resume_exited:
            reason = "resume_not_exited"
        elif reason.startswith(("decode_error:", "read_error:", "rollout_changing", "partial_final_line")):
            pass
        elif epoch != self.epoch:
            reason = "rollout_replaced"
        elif turns.ambiguous:
            reason = "ambiguous_turn_lifecycle"
        elif turns.overlap:
            status, reason = "OVERLAP", "concurrent_turn_starts"
        elif turns.count:
            reason = "open_turns"
        elif not turns.starts or not turns.ends:
            reason = "missing_wake_lifecycle"
        else:
            status, reason = "CLEAN", "completed_turns_without_overlap"
        return {
            "schema": "codex-wake.v1", "status": status, "reason": reason,
            "rollout": {
                "path_sha256": hashlib.sha256(os.fsencode(path)).hexdigest(),
                "device": self.signature[0] if self.signature else None,
                "inode": self.signature[1] if self.signature else None,
                "offset": self.offset,
            },
            "starts": turns.starts, "ends": turns.ends,
            "open_count": turns.count, "peak_open_count": turns.peak,
            "turn_ids": turns.overlap_ids or sorted(turns.ids),
        }


def rollout_is_ready(path: Path, *, reader: RolloutReader | None = None) -> tuple[bool, str]:
    """Fail closed unless a stable complete rollout has no unmatched start."""
    return (reader or RolloutReader()).ready(path)


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
                    with path.open("rb") as handle:
                        metadata = json.loads(handle.readline())
                    if metadata.get("type") != "session_meta":
                        continue
                    payload = metadata["payload"]
                    thread_id = str(uuid.UUID(payload["id"]))
                    cwd = Path(payload["cwd"])
                    if not cwd.is_absolute():
                        continue
                    matches[thread_id] = LiveSession(thread_id, cwd, environment, rollout=path)
            except (psutil.Error, OSError, ValueError, KeyError, TypeError, RecursionError):
                continue
    except psutil.Error:
        return None
    return next(iter(matches.values())) if len(matches) == 1 else None


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
    before_resume: Callable[[], None] | None = None,
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
        before_resume: optional final admission check immediately before spawning.

    Returns:
        dict with:
            bridge_id (str), thread_id (str), exit_code (int),
            events (list[dict] of parsed JSON event lines from stdout),
            final_message (str | None) — best-effort extraction,
            duration_s (float), session_file (str | None) — path to the
            original UI session JSONL if locatable, stderr (str),
            resume_exited (bool) — false when termination is not evidenced.
    """
    bridge_id = bridge_id or f"bridge-{uuid.uuid4().hex[:8]}"
    framed_message = f"Bridge-ID: {bridge_id}\n\n{message}"
    session_file = find_session_file(thread_id)

    start = datetime.now(UTC)
    try:
        if before_resume is not None:
            before_resume()
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
        resume_exited = True
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode("utf-8", errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode("utf-8", errors="replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        stderr = f"[timeout after {timeout_s}s]\n{stderr}"
        exit_code = -1
        resume_exited = False
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
        "resume_exited": resume_exited,
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
            "Returns the codex subprocess exit code.\n"
            "Use for explicit delivery to a known thread; use the inbox watcher for gated driver wakes."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.ai_agent_bridge._ui_codex --thread <UUID> "ping"
  .venv/bin/python -m scripts.ai_agent_bridge._ui_codex --thread <UUID> --from-file relay.md

Outputs: a resume turn in the persisted thread; final response or JSON receipt on stdout.
Exit codes: Codex subprocess status; timeout is -1 (shell 255); 2 invalid arguments.
Related: scripts.ai_agent_bridge._inbox_watch; docs/runbooks/session-supervisor.md; #10217.
""",
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
        compact = {k: v for k, v in result.items() if k != "events"}
        compact["event_count"] = len(result["events"])
        print(json.dumps(compact, indent=2, default=str))
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
