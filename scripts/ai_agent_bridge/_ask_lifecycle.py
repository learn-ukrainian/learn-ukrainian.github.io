"""Lifecycle state and detached workers for one-shot bridge asks (#4837).

Optional Fleet Comms message-plane hook (PR-E / #5512): when
``FLEET_COMMS_MESSAGE_PLANE`` is ``shadow`` or ``dual_write``, register a durable
request and gate legacy ``replied`` projection via ``may_mark_legacy_replied``.
Default remains ``off`` (no production cutover). Plane import/runtime errors
fail open so the legacy bridge never breaks on the opt-in path.
"""

from __future__ import annotations

import atexit
import contextlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agent_runtime.errors import AgentStalledError, AgentTimeoutError

from . import _config
from ._broker import _remove_pid_file, _write_pid_file
from ._config import _PARENT_ENV, PID_DIR, REPO_ROOT
from ._db import get_db

_ASK_AGENT = "ask"
# Stored on the legacy messages.data JSON so reply completion can reload by id.
_FLEET_REQUEST_ID_KEY = "fleet_request_id"
# Tests may point plane storage at a tmp root without touching batch_state/.
_PLANE_ROOT_OVERRIDE: Path | None = None


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _ask_state_root() -> Path:
    return REPO_ROOT / "batch_state" / "asks"


def _ask_task_key(message_id: int) -> str:
    row = _load_ask_row(message_id)
    task_id = str(row[0]) if row and row[0] else f"message-{message_id}"
    return re.sub(r"[^A-Za-z0-9._-]+", "-", task_id)[:80] or f"message-{message_id}"


def _ask_state_dir(message_id: int) -> Path:
    return _ask_state_root() / _ask_task_key(message_id)


def _ask_log_path(message_id: int) -> Path:
    return REPO_ROOT / ".mcp" / "servers" / "message-broker" / "logs" / f"ask-{message_id}.log"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Durably replace a small lifecycle record without a partially-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _stderr_tail(message_id: int) -> str:
    try:
        return _ask_log_path(message_id).read_bytes()[-2048:].decode("utf-8", errors="replace")
    except OSError:
        return ""


def _write_ask_launch_record(message_id: int, *, pid: int, target: str) -> None:
    row = _load_ask_row(message_id)
    metadata: dict[str, Any] = {}
    if row and row[4]:
        try:
            decoded = json.loads(str(row[4]))
            if isinstance(decoded, dict):
                metadata = decoded
        except (TypeError, json.JSONDecodeError):
            pass
    _atomic_write_json(
        _ask_state_dir(message_id) / "launch.json",
        {
            "message_id": message_id,
            "pid": pid,
            "agent": target,
            "harness": target,
            "model": metadata.get("to_model"),
            "started_at": _now_iso(),
        },
    )


def _read_ask_record(message_id: int, name: str) -> dict[str, Any] | None:
    try:
        value = json.loads((_ask_state_dir(message_id) / name).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _pid_is_alive(pid: object) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class _AskTerminalRecorder:
    """Single-write terminal artifact for a detached ask worker."""

    def __init__(self, message_id: int):
        self.message_id = message_id
        self.written = False

    def write(self, rc_or_signal: int | str, stage: str) -> None:
        if self.written:
            return
        _atomic_write_json(
            _ask_state_dir(self.message_id) / "terminal.json",
            {
                "rc_or_signal": rc_or_signal,
                "stage": stage,
                "stderr_tail": _stderr_tail(self.message_id),
                "ended_at": _now_iso(),
            },
        )
        self.written = True

    def atexit(self) -> None:
        self.write("unknown", "atexit")

    def signal_handler(self, signum: int, _frame: Any) -> None:
        self.write(signal.Signals(signum).name, "signal")
        raise SystemExit(128 + signum)


class AskWorkerStartupError(RuntimeError):
    """Background ask worker died before recording a durable terminal status."""


# Positive content signals — optional boosts, NOT a formatting contract on workers.
# Presence of any one is enough to treat a body as useful.
_USEFUL_REPLY_SIGNAL_RE = re.compile(
    r"(?is)"
    r"(?:\bVERDICT\s*:)"
    r"|(?:^\#{1,6}\s+\S)"
    r"|(?:```)"
    r"|(?:\b[\w./+-]+\.(?:py|ts|tsx|js|jsx|md|ya?ml|json|toml|sh|rs|go)\b(?::\d+)?)"
    r"|(?:\b(?:FINDING|CHANGES[_ ]?REQUESTED|APPROVED|BLOCKED|REQUEST CHANGES)\b)"
    r"|(?:\b(?:AssertionError|Traceback|FAILED|PASSED)\b)"
)

# Entire-body intent / plan scaffolding ("I'll check out the branch…") with no
# actual answer. Inferred from observable language — workers are not required to
# emit a magic marker line.
_INTENT_SCAFFOLD_RE = re.compile(
    r"(?is)^\s*(?:"
    r"(?:okay|ok|sure|alright|right|got it)[,!.]?\s+"
    r")?"
    r"(?:"
    r"i(?:'ll| will)\b|"
    r"i(?:'m| am)\s+(?:just\s+)?(?:going to|about to|gonna)\b|"
    r"let me\b|"
    r"going to\b|"
    r"i need to\b|"
    r"planning to\b|"
    r"first[, ]+i(?:'ll| will)\b"
    r").+\s*$"
)


def register_ask(message_id: int) -> None:
    """Record a newly sent ask using the legacy table's existing status field."""
    _set_ask_status(message_id, "sent")
    _plane_try_open_ask(message_id)


def mark_ask_processing(message_id: int) -> None:
    """Record that a detached worker has started processing an ask."""
    _set_ask_status(message_id, "processing")


def record_ask_reply(message_id: int, reply_id: int) -> bool:
    """Link an ask to its exact reply without a schema migration.

    The response must belong to this exact query's task and transport pair.
    This guards concurrent detached asks from ever displaying another ask's
    reply ID when a transport or database call misreports an insert ID.

    When ``FLEET_COMMS_MESSAGE_PLANE=dual_write`` and a durable request exists
    that is not proven complete, refuse to mark legacy ``replied`` (incomplete
    never becomes replied). ``shadow`` / ``off`` never block this path.

    Completion also requires a stored reply body that meets a usefulness bar
    (see :func:`reply_body_is_useful`). Thin intent-only scaffolding recorded as
    a "reply" is a terminal failure, not success — that is the hollow-reply
    class that motivated this gate (narration like "I'll check out the branch
    and run the tests" exiting 0).
    """
    thin_preview: str | None = None
    conn = get_db()
    try:
        ask = conn.execute(
            "SELECT task_id, from_llm, to_llm FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        reply = conn.execute(
            "SELECT task_id, from_llm, to_llm, message_type, content FROM messages WHERE id = ?",
            (reply_id,),
        ).fetchone()
        if not ask or not reply:
            # Test doubles and callers outside the legacy message table have
            # no durable row to link; leave lifecycle state unchanged.
            return False
        matches = (
            ask[0] == reply[0]
            and ask[1] == reply[2]
            and ask[2] == reply[1]
            and reply[3] == "response"
        )
        if not matches:
            return False
        if not _plane_may_mark_legacy_replied(message_id):
            return False
        raw_body = reply[4]
        body = raw_body if isinstance(raw_body, str) else ""
        if not reply_body_is_useful(body):
            # Defer failure write until the reader conn is closed.
            thin_preview = " ".join(body.split())[:120] or "(empty)"
            return False
        conn.execute("UPDATE messages SET status = ? WHERE id = ?", (f"replied:{reply_id}", message_id))
        conn.commit()
        return True
    finally:
        conn.close()
        # Thin scaffolding: refuse replied:… and record a terminal failure.
        # Runs after close so record_ask_failure can open its own writer.
        if thin_preview is not None:
            status = _ask_status(message_id)
            if status in {"sent", "processing", "pending", None}:
                record_ask_failure(
                    message_id,
                    f"thin scaffolding reply #{reply_id}: {thin_preview}",
                )


def reply_body_is_useful(body: str) -> bool:
    """Return True when a stored reply body is more than empty/intent scaffolding.

    Infer from observable facts only — do **not** require a magic marker line on
    every worker (that over-correction broke legitimate dispatches on the
    sibling delegate path). Positive structured signals (``VERDICT:``, headings,
    code fences, file paths, review tokens) pass immediately. Empty bodies and
    pure future-intent narration ("I'll check out the branch and run the tests")
    fail. Everything else with real non-scaffold content passes, including short
    legitimate answers like ``yes`` or ``42``.
    """
    text = (body or "").strip()
    if not text:
        return False
    if _USEFUL_REPLY_SIGNAL_RE.search(text):
        return True
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return False
    if all(_INTENT_SCAFFOLD_RE.match(line) for line in lines):
        return False
    # Single-paragraph intent-only (no newlines, or blank-line-only splits).
    if len(lines) == 1 and _INTENT_SCAFFOLD_RE.match(lines[0]):
        return False
    # Whole body as one intent sentence even when split oddly.
    return not _INTENT_SCAFFOLD_RE.match(text)


def note_ask_plane_capture(
    message_id: int,
    *,
    adapter: str | None = None,
    stdout: str = "",
    stderr: str = "",
    returncode: int | None = 0,
    events: tuple[dict[str, Any], ...] = (),
    raw_bytes: bytes | None = None,
    session_id: str | None = None,
) -> bool:
    """Feed an adapter capture into the opt-in message plane (shadow/dual_write).

    Process paths call this after a harness run so dual_write can prove
    completion before ``record_ask_reply``. Fail-open: returns False on off mode
    or any plane error; never raises into the legacy bridge.
    """
    try:
        plane_mod = _import_message_plane()
        if plane_mod is None:
            return False
        mode = plane_mod.resolve_plane_mode()
        if mode == "off":
            return False
        request_id = _load_fleet_request_id(message_id)
        if not request_id:
            return False
        with plane_mod.open_message_plane(
            mode=mode,
            root=_plane_root(),
            legacy_db=_config.DB_PATH,
        ) as plane:
            plane.complete_ask(
                request_id,
                adapter=adapter,
                stdout=stdout,
                stderr=stderr,
                returncode=returncode,
                events=events,
                raw_bytes=raw_bytes,
                session_id=session_id,
                legacy_message_id=message_id,
            )
        return True
    except Exception:
        return False


def record_ask_failure(message_id: int, reason: str, *, timed_out: bool = False) -> None:
    """Record a terminal failure, retaining a bounded diagnostic for ``asks``."""
    prefix = "timed-out" if timed_out else "failed"
    detail = " ".join(reason.split())[:300] or "worker ended without a reply"
    _set_ask_status(message_id, f"{prefix}:{detail}")


def launch_background_ask(message_id: int, target: str, options: dict[str, Any]) -> int:
    """Start a detached bridge processor after its ask message has been sent.

    Returns the worker PID only when startup confirmation succeeds. On recorded
    startup death this raises :class:`AskWorkerStartupError` and does **not**
    print the success banner — callers that key on return value / stdout must
    not treat a dead worker as a successful dispatch.
    """
    task_key = str(message_id)
    log_dir = REPO_ROOT / ".mcp" / "servers" / "message-broker" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"ask-{message_id}.log"

    # The child reads this established broker state-file convention. Write it
    # before Popen so the child cannot race the parent for its invocation data.
    _write_pid_file(
        _ASK_AGENT,
        task_key,
        {"message_id": message_id, "target": target, "options": options},
    )
    try:
        with log_file.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                [
                    str(REPO_ROOT / ".venv" / "bin" / "python"),
                    str(REPO_ROOT / "scripts" / "ai_agent_bridge" / "__main__.py"),
                    "process-ask",
                    str(message_id),
                    target,
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=str(REPO_ROOT),
                env=_PARENT_ENV,
                start_new_session=True,
            )
    except OSError as exc:
        _remove_pid_file(_ASK_AGENT, task_key)
        record_ask_failure(message_id, f"could not spawn background worker: {exc}")
        raise

    _write_pid_file(
        _ASK_AGENT,
        task_key,
        {"message_id": message_id, "target": target, "options": options},
        pid=proc.pid,
    )
    _write_ask_launch_record(message_id, pid=proc.pid, target=target)

    # A worker can die BEFORE `process_background_ask` runs — a bad adapter path, an
    # import error, a missing binary — in which case its `finally:` never executes and
    # nothing is ever recorded. Observed live on the kimi lane 2026-07-25: message id
    # returned, worker gone, log file 0 bytes, no usage record. The ask reported
    # SUCCESS and produced nothing, which is the worst possible failure shape for a
    # review gate: silence is indistinguishable from "still thinking".
    #
    # So confirm the worker actually came up, and fail LOUDLY if it did not —
    # including a non-success return path (raise), not only a stderr message.
    if not _confirm_worker_started(message_id, target, proc, log_file):
        raise AskWorkerStartupError(
            f"Ask #{message_id}: the {target} worker died at startup "
            f"(PID {proc.pid}); no answer is coming. Log: {log_file}"
        )
    print(f"✅ Ask #{message_id} sent; processing in background (PID {proc.pid}).")
    return proc.pid


_WORKER_START_GRACE_S = 5.0
_WORKER_POLL_S = 0.25


def _confirm_worker_started(message_id: int, target: str, proc, log_file: Path) -> bool:
    """Detect a worker that dies without recording anything, and say so.

    Returns True when the worker looks started enough for the caller to proceed,
    False when a startup death was recorded (caller must not print ✅ / return a
    success PID).

    **Success here means only liveness, not ask completion.** A worker that exits
    0 having written nothing is still a failure, because a completed ask always
    leaves either a useful reply or a recorded failure. Terminal usefulness of a
    stored reply body is enforced later by :func:`record_ask_reply` /
    :func:`reply_body_is_useful`.

    **Residual race (documented, not fully closable at this gate):** if the child
    flushes early output (banner, import warning, partial traceback) while still
    alive, this function returns True on "alive + log bytes" and the parent may
    print the success banner. The child can then die before writing a durable
    terminal status. Output is a liveness proxy, not completion proof. The
    worker's ``process_background_ask`` ``finally:`` still records
    ``failed:worker ended without a reply`` when no terminal status was written,
    and :func:`record_ask_reply` refuses thin scaffolding — so the durable ask
    state does not stay a silent success. Callers that only watch the launch
    banner remain exposed to this short window; re-check ask status / reply body
    for completion, do not trust the banner alone.
    """
    deadline = time.monotonic() + _WORKER_START_GRACE_S
    while time.monotonic() < deadline:
        rc = proc.poll()
        if rc is None:
            try:
                if log_file.stat().st_size > 0:
                    return True  # alive and talking (liveness only — see residual race)
            except OSError:
                pass
            time.sleep(_WORKER_POLL_S)
            continue

        # Exited within the grace window. Only a recorded terminal status makes that OK.
        status = _ask_status(message_id)
        if status is not None and not status.startswith(("sent", "processing", "pending")):
            # Terminal status present — still reject thin replied: scaffolding if we can.
            if status.startswith("replied:"):
                reply_id_s = status.split(":", 1)[1]
                try:
                    reply_id = int(reply_id_s)
                except ValueError:
                    return True
                if not _stored_reply_is_useful(reply_id):
                    record_ask_failure(
                        message_id,
                        f"thin scaffolding reply #{reply_id} at startup",
                    )
                    _remove_pid_file(_ASK_AGENT, str(message_id))
                    print(
                        f"❌ Ask #{message_id}: the {target} worker exited with a hollow "
                        f"scaffolding reply (#{reply_id}); no useful answer was recorded.\n"
                        f"   Route this ask to another lane.",
                        file=sys.stderr,
                    )
                    return False
            return True
        try:
            tail = log_file.read_text(encoding="utf-8", errors="replace").strip()[-400:]
        except OSError:
            tail = ""
        detail = tail or f"worker exited rc={rc} without writing any output"
        record_ask_failure(message_id, f"{target} worker died at startup: {detail}")
        _AskTerminalRecorder(message_id).write(rc if rc is not None else 1, "startup")
        _remove_pid_file(_ASK_AGENT, str(message_id))
        print(
            f"❌ Ask #{message_id}: the {target} worker DIED AT STARTUP (rc={rc}) without "
            f"recording anything.\n"
            f"   This is not a slow reply — no answer is coming. Log: {log_file}\n"
            f"   {('Log tail: ' + tail) if tail else 'The log file is empty.'}\n"
            f"   Route this ask to another lane.",
            file=sys.stderr,
        )
        return False
    # Still running after the grace window: normal, long-running ask.
    return True


def _stored_reply_is_useful(reply_id: int) -> bool:
    """Load a reply row's body and apply the usefulness bar (fail closed on missing)."""
    conn = get_db()
    try:
        row = conn.execute("SELECT content FROM messages WHERE id = ?", (reply_id,)).fetchone()
        if not row:
            return False
        body = row[0] if isinstance(row[0], str) else ""
        return reply_body_is_useful(body)
    finally:
        conn.close()


def process_background_ask(message_id: int, target: str) -> None:
    """Run one detached ask worker and leave a terminal lifecycle status."""
    terminal = _AskTerminalRecorder(message_id)
    atexit.register(terminal.atexit)
    previous_handlers: dict[int, Any] = {}
    for signum in (signal.SIGTERM, signal.SIGINT):
        previous_handlers[signum] = signal.getsignal(signum)
        signal.signal(signum, terminal.signal_handler)
    rc_or_signal: int | str = 1
    stage = "startup"
    try:
        options = _background_options(message_id, target)
        mark_ask_processing(message_id)
        stage = "processing"
        _process_target(message_id, target, options)
        status = _ask_status(message_id)
        if status and status.startswith("replied:"):
            rc_or_signal = 0
            stage = "success"
        else:
            stage = "missing-reply" if status in {"sent", "processing", "pending", None} else "failed"
    except (AgentStalledError, AgentTimeoutError, subprocess.TimeoutExpired, TimeoutError) as exc:
        record_ask_failure(message_id, str(exc), timed_out=True)
        stage = "timeout"
    except SystemExit as exc:
        detail = str(exc)
        record_ask_failure(message_id, detail, timed_out=_looks_like_timeout(detail))
        stage = "system-exit"
        rc_or_signal = exc.code if isinstance(exc.code, int) else "SystemExit"
    except Exception as exc:  # pragma: no cover - defensive detached-worker boundary
        record_ask_failure(message_id, f"{type(exc).__name__}: {exc}")
        stage = "exception"
    finally:
        status = _ask_status(message_id)
        if status in {"sent", "processing", "pending", None}:
            record_ask_failure(message_id, "worker ended without a reply")
            stage = "missing-reply"
        terminal.write(rc_or_signal, stage)
        _remove_pid_file(_ASK_AGENT, str(message_id))
        for signum, previous in previous_handlers.items():
            signal.signal(signum, previous)


def print_asks(task_id: str | None = None) -> None:
    """Print recent tracked asks, optionally restricted to a bridge task."""
    clauses = ["(status = 'sent' OR status = 'processing' OR status LIKE 'replied:%' OR status LIKE 'timed-out:%' OR status LIKE 'timed-out-notified:%' OR status LIKE 'failed:%')"]
    params: list[str] = []
    if task_id:
        clauses.append("task_id = ?")
        params.append(task_id)
    where = " AND ".join(clauses)

    conn = get_db()
    try:
        rows = conn.execute(
            f"""
            SELECT id, task_id, to_llm, status, timestamp, acknowledged, consumed_by_live_driver
            FROM messages
            WHERE {where}
            ORDER BY id DESC
            LIMIT 100
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        print("No tracked asks.")
        return

    print("ID  TASK  TO  STATUS  CONSUMPTION  SENT")
    for row in rows:
        status = _ask_display_status(int(row[0]), str(row[3] or "sent"))
        consumption = _message_consumption_state(row[5], row[6])
        print(f"{row[0]}  {row[1] or '-'}  {row[2]}  {status}  {consumption}  {row[4]}")


def maybe_print_timeout_notice() -> None:
    """Surface newly timed-out detached asks on the next bridge CLI command."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT id, task_id, to_llm
            FROM messages
            WHERE status LIKE 'timed-out:%'
            ORDER BY id ASC
            """
        ).fetchall()
        if not rows:
            return
        labels = ", ".join(f"#{row[0]} ({row[2]}, task {row[1] or '-'})" for row in rows)
        print(f"⚠️  Background ask timed out: {labels}. Run 'ab asks' for details.", file=sys.stderr)
        conn.executemany(
            "UPDATE messages SET status = 'timed-out-notified:' || substr(status, 11) WHERE id = ?",
            [(row[0],) for row in rows],
        )
        conn.commit()
    finally:
        conn.close()


def assert_ask_content_present(msg: dict[str, Any], *, message_id: int, target: str) -> str:
    """Return non-empty ask content or record a transport-leg failure (#4915).

    Background workers must feed the model from the *stored* message body,
    never from inherited stdin. An empty body is a transport bug, not a model
    stall — surface that distinction so failover logic does not misattribute.
    """
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str) and content.strip():
        return content
    reason = (
        f"transport empty-ask-body: message #{message_id} target={target} "
        f"has no stored content (stdin was not re-read; body must come from DB)"
    )
    record_ask_failure(message_id, reason)
    raise ValueError(reason)


def fetch_ask_message(message_id: int, target: str) -> dict[str, Any] | None:
    """Load the original ask payload for one-shot processors."""
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT id, task_id, from_llm, to_llm, message_type, content, data
            FROM messages
            WHERE id = ? AND to_llm = ?
            """,
            (message_id, target),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
    }


def ask_attachment(msg: dict[str, Any]) -> str | None:
    """Recover the original ``--data`` value stored in message metadata."""
    metadata = _ask_metadata(msg)
    raw = metadata.get("raw")
    return str(raw) if raw is not None else None


def ask_target_model(msg: dict[str, Any]) -> str | None:
    """Recover the model selected when the original ask was sent."""
    model = _ask_metadata(msg).get("to_model")
    return str(model) if model else None


def ask_sender_model(msg: dict[str, Any]) -> str | None:
    """Recover the sender model for reply routing compatibility."""
    model = _ask_metadata(msg).get("from_model")
    return str(model) if model else None


def _process_target(message_id: int, target: str, options: dict[str, Any]) -> None:
    """Route the worker to the same processor as its synchronous ask path."""
    no_timeout = bool(options.get("no_timeout", False))
    review = bool(options.get("review", False))
    new_session = bool(options.get("new_session", False))
    if target == "claude":
        from ._claude import process_for_claude

        process_for_claude(message_id, new_session, no_timeout=no_timeout, review=review)
    elif target == "codex":
        from ._codex import process_for_codex

        process_for_codex(message_id, new_session, no_timeout, review=review)
    elif target == "agy":
        from ._agy import process_for_agy

        process_for_agy(message_id, new_session, no_timeout, review=review)
    elif target in {"grok", "grok-build"}:
        # Canonical native seat is `grok`; `grok-build` is a permanent alias.
        from ._grok_build import process_for_grok_build

        process_for_grok_build(message_id, new_session, no_timeout, review)
    elif target == "kimi":
        from ._kimi import process_for_kimi

        process_for_kimi(message_id, new_session, no_timeout, review)
    elif target == "cursor":
        from ._cursor import process_for_cursor

        process_for_cursor(message_id, no_timeout=no_timeout)
    elif target == "hermes":
        from ._hermes import process_for_hermes

        process_for_hermes(message_id, no_timeout=no_timeout)
    elif target in {"opencode", "pool", "glm", "gemma"}:
        from ._opencode import process_for_opencode

        process_for_opencode(message_id, target=target, no_timeout=no_timeout, variant=options.get("variant"))
    else:
        raise ValueError(f"unsupported background ask target {target!r}")


def _background_options(message_id: int, target: str) -> dict[str, Any]:
    state_path = PID_DIR / f"{_ASK_AGENT}-{message_id}.json"
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if payload.get("target") != target:
        raise ValueError(f"background target mismatch for ask #{message_id}")
    options = payload.get("options")
    if not isinstance(options, dict):
        raise ValueError(f"background options missing for ask #{message_id}")
    return options


def _set_ask_status(message_id: int, status: str) -> None:
    conn = get_db()
    try:
        conn.execute("UPDATE messages SET status = ? WHERE id = ?", (status, message_id))
        conn.commit()
    finally:
        conn.close()


def _ask_metadata(msg: dict[str, Any]) -> dict[str, Any]:
    raw = msg.get("data")
    if not raw:
        return {}
    try:
        metadata = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return metadata if isinstance(metadata, dict) else {}


def _ask_status(message_id: int) -> str | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT status FROM messages WHERE id = ?", (message_id,)).fetchone()
        return str(row[0]) if row else None
    finally:
        conn.close()


def _display_status(status: str) -> str:
    if status.startswith("replied:"):
        return f"replied (reply #{status.split(':', 1)[1]})"
    if status.startswith("timed-out"):
        return "timed-out"
    if status.startswith("failed:"):
        return "failed"
    return status


def _ask_display_status(message_id: int, status: str) -> str:
    """Render durable worker-death evidence before the legacy status string."""
    terminal = _read_ask_record(message_id, "terminal.json")
    if terminal is not None:
        rc_or_signal = terminal.get("rc_or_signal")
        stage = str(terminal.get("stage") or "unknown")
        failed = rc_or_signal not in {0, "0"} or stage in {
            "atexit",
            "exception",
            "failed",
            "missing-reply",
            "signal",
            "startup",
            "system-exit",
            "timeout",
        }
        if failed:
            return f"FAILED ({stage}; retry recommended)"

    launch = _read_ask_record(message_id, "launch.json")
    if (
        launch is not None
        and terminal is None
        and not status.startswith("replied:")
        and not _pid_is_alive(launch.get("pid"))
    ):
        return "DIED-SILENT (retry recommended)"
    return _display_status(status)


def _message_consumption_state(acknowledged: int, consumed_by_live_driver: int) -> str:
    """Return the legacy-message consumption state shown by ``asks``."""
    if consumed_by_live_driver:
        return "live-consumed"
    if acknowledged:
        return "read-but-not-live-consumed"
    return "unread"


def _looks_like_timeout(detail: str) -> bool:
    lowered = detail.lower()
    return "timeout" in lowered or "timed out" in lowered or "stalled" in lowered


def _import_message_plane() -> Any | None:
    """Load message_plane fail-open (missing package/import must not break bridge)."""
    try:
        from scripts.fleet_comms import message_plane as plane_mod

        return plane_mod
    except Exception:
        return None


def _plane_root() -> Path:
    if _PLANE_ROOT_OVERRIDE is not None:
        return _PLANE_ROOT_OVERRIDE
    env = os.environ.get("FLEET_COMMS_ROOT")
    if env:
        return Path(env)
    return REPO_ROOT / "batch_state" / "fleet-comms" / "v1"


def _plane_try_open_ask(message_id: int) -> None:
    """Create a durable plane request for shadow/dual_write; no-op when off."""
    try:
        plane_mod = _import_message_plane()
        if plane_mod is None:
            return
        mode = plane_mod.resolve_plane_mode()
        if mode == "off":
            return
        row = _load_ask_row(message_id)
        if row is None:
            return
        task_id, from_llm, to_llm, content, data_raw = row
        model = None
        try:
            meta = json.loads(data_raw) if data_raw else {}
            if isinstance(meta, dict):
                model = meta.get("to_model")
                if model is not None:
                    model = str(model)
        except (TypeError, json.JSONDecodeError):
            model = None
        with plane_mod.open_message_plane(
            mode=mode,
            root=_plane_root(),
            legacy_db=_config.DB_PATH,
        ) as plane:
            req = plane.open_ask(
                recipient=str(to_llm or "unknown"),
                body=str(content or ""),
                sender=str(from_llm or "bridge"),
                legacy_message_id=message_id,
                task_id=str(task_id) if task_id else None,
                model=model,
                transport_mode="bridge-ask",
            )
            if req is not None:
                _store_fleet_request_id(message_id, req.request_id)
    except Exception:
        return


def _plane_may_mark_legacy_replied(message_id: int) -> bool:
    """Gate dual_write legacy replied; shadow/off always allow (fail-open)."""
    try:
        plane_mod = _import_message_plane()
        if plane_mod is None:
            return True
        mode = plane_mod.resolve_plane_mode()
        if mode != "dual_write":
            # off + shadow: plane does not control legacy status
            return True
        request_id = _load_fleet_request_id(message_id)
        if not request_id:
            # No durable request was recorded — fail open (plane open failed).
            return True
        with plane_mod.open_message_plane(
            mode=mode,
            root=_plane_root(),
            legacy_db=_config.DB_PATH,
        ) as plane:
            return bool(plane.may_mark_legacy_replied(request_id))
    except Exception:
        return True


def _load_ask_row(
    message_id: int,
) -> tuple[Any, Any, Any, Any, Any] | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT task_id, from_llm, to_llm, content, data FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        if not row:
            return None
        return (row[0], row[1], row[2], row[3], row[4])
    finally:
        conn.close()


def _load_fleet_request_id(message_id: int) -> str | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT data FROM messages WHERE id = ?", (message_id,)).fetchone()
        if not row or not row[0]:
            return None
        try:
            meta = json.loads(str(row[0]))
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(meta, dict):
            return None
        value = meta.get(_FLEET_REQUEST_ID_KEY)
        return str(value) if value else None
    finally:
        conn.close()


def _store_fleet_request_id(message_id: int, request_id: str) -> None:
    conn = get_db()
    try:
        row = conn.execute("SELECT data FROM messages WHERE id = ?", (message_id,)).fetchone()
        metadata: dict[str, Any] = {}
        if row and row[0]:
            try:
                loaded = json.loads(str(row[0]))
                metadata = loaded if isinstance(loaded, dict) else {"raw": row[0]}
            except (TypeError, json.JSONDecodeError):
                metadata = {"raw": row[0]}
        metadata[_FLEET_REQUEST_ID_KEY] = request_id
        conn.execute(
            "UPDATE messages SET data = ? WHERE id = ?",
            (json.dumps(metadata, sort_keys=True), message_id),
        )
        conn.commit()
    finally:
        conn.close()
