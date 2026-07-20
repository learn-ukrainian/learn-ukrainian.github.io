"""Lifecycle state and detached workers for one-shot bridge asks (#4837).

Optional Fleet Comms message-plane hook (PR-E / #5512): when
``FLEET_COMMS_MESSAGE_PLANE`` is ``shadow`` or ``dual_write``, register a durable
request and gate legacy ``replied`` projection via ``may_mark_legacy_replied``.
Default remains ``off`` (no production cutover). Plane import/runtime errors
fail open so the legacy bridge never breaks on the opt-in path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from agent_runtime.errors import AgentStalledError, AgentTimeoutError

from ._broker import _remove_pid_file, _write_pid_file
from ._config import _PARENT_ENV, DB_PATH, PID_DIR, REPO_ROOT
from ._db import get_db

_ASK_AGENT = "ask"
# Stored on the legacy messages.data JSON so reply completion can reload by id.
_FLEET_REQUEST_ID_KEY = "fleet_request_id"
# Tests may point plane storage at a tmp root without touching batch_state/.
_PLANE_ROOT_OVERRIDE: Path | None = None


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
    """
    conn = get_db()
    try:
        ask = conn.execute(
            "SELECT task_id, from_llm, to_llm FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        reply = conn.execute(
            "SELECT task_id, from_llm, to_llm, message_type FROM messages WHERE id = ?",
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
        conn.execute("UPDATE messages SET status = ? WHERE id = ?", (f"replied:{reply_id}", message_id))
        conn.commit()
        return True
    finally:
        conn.close()


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
            legacy_db=DB_PATH,
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
    """Start a detached bridge processor after its ask message has been sent."""
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
    print(f"✅ Ask #{message_id} sent; processing in background (PID {proc.pid}).")
    return proc.pid


def process_background_ask(message_id: int, target: str) -> None:
    """Run one detached ask worker and leave a terminal lifecycle status."""
    options = _background_options(message_id, target)
    mark_ask_processing(message_id)
    try:
        _process_target(message_id, target, options)
    except (AgentStalledError, AgentTimeoutError, subprocess.TimeoutExpired, TimeoutError) as exc:
        record_ask_failure(message_id, str(exc), timed_out=True)
    except SystemExit as exc:
        detail = str(exc)
        record_ask_failure(message_id, detail, timed_out=_looks_like_timeout(detail))
    except Exception as exc:  # pragma: no cover - defensive detached-worker boundary
        record_ask_failure(message_id, f"{type(exc).__name__}: {exc}")
    finally:
        status = _ask_status(message_id)
        if status in {"sent", "processing", "pending", None}:
            record_ask_failure(message_id, "worker ended without a reply")
        _remove_pid_file(_ASK_AGENT, str(message_id))


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
            SELECT id, task_id, to_llm, status, timestamp
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

    print("ID  TASK  TO  STATUS  SENT")
    for row in rows:
        status = _display_status(str(row[3] or "sent"))
        print(f"{row[0]}  {row[1] or '-'}  {row[2]}  {status}  {row[4]}")


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
            legacy_db=DB_PATH,
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
            legacy_db=DB_PATH,
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
