"""Codex interaction: ask_codex and process_for_codex.

Phase 4 of #1184 migrated the subprocess path onto scripts.agent_runtime.
The subprocess-building helpers below (_build_codex_exec_cmd,
_build_codex_resume_cmd) are kept ONLY for backward compatibility with
test mocks; they are no longer called by production code paths. They
will be deleted in Phase 6 cleanup.

Note: this module used to attempt Codex session resume for multi-turn
bridge conversations. Phase 4 drops that — Codex always starts fresh,
consistent with the runtime's resume_policy="never" for Codex (see
docs/design/agent-runtime.md § 6.3). Short bridge consultations don't
benefit from resume, and resume is the cross-worktree contamination
footgun that Codex flagged in his own consultation.
"""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from agent_runtime.errors import (
    AgentStalledError,
    AgentTimeoutError,
    AgentUnavailableError,
    RateLimitedError,
)
from agent_runtime.runner import invoke as runtime_invoke

from ._config import CODEX_CLI, REPO_ROOT
from ._db import get_db, get_session, set_session
from ._messaging import acknowledge, send_message
from ._prompts import build_codex_prompt

_SESSION_RE = re.compile(r"session id:\s*([0-9a-f-]{8,})", re.IGNORECASE)
_CODEX_MODES = {"safe", "workspace-write", "full-auto", "danger"}


def _codex_bridge_mode() -> str:
    """Resolve Codex sandbox mode for ai_agent_bridge calls."""
    requested = (
        os.environ.get("CODEX_BRIDGE_MODE")
        or os.environ.get("CODEX_CLI_MODE")
        or "safe"
    ).strip().lower()
    if requested in _CODEX_MODES:
        return "workspace-write" if requested == "full-auto" else requested
    print(f"⚠️  Invalid CODEX_BRIDGE_MODE='{requested}' — falling back to safe")
    return "safe"


def _codex_bridge_runtime_mode() -> str:
    """Translate CODEX_BRIDGE_MODE env var to runtime vocabulary.

    Runtime uses {read-only, workspace-write, danger}.
    Bridge legacy uses {safe, workspace-write, full-auto, danger}.
    """
    legacy = _codex_bridge_mode()
    if legacy == "danger":
        return "danger"
    if legacy == "workspace-write":
        return "workspace-write"
    return "read-only"  # "safe" → "read-only"


def _codex_bridge_flags() -> list[str]:
    """Translate bridge mode to Codex CLI flags.

    DEPRECATED: kept for test-mock backward compat. Production code uses
    scripts.agent_runtime.adapters.codex.CodexAdapter which builds its
    own flags from mode.
    """
    mode = _codex_bridge_mode()
    if mode == "danger":
        return ["--dangerously-bypass-approvals-and-sandbox"]
    if mode == "workspace-write":
        return ["--full-auto"]
    return ["-s", "read-only"]


def _build_codex_exec_cmd(output_path: Path, model: str | None) -> list[str]:
    """Build a fresh non-resume Codex exec command."""
    cmd = [
        CODEX_CLI,
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(REPO_ROOT),
        "--color",
        "never",
        "-o",
        str(output_path),
    ]
    cmd.extend(_codex_bridge_flags())
    if model:
        cmd.extend(["-m", model])
    cmd.append("-")  # Explicit stdin prompt mode
    return cmd


def _build_codex_resume_cmd(session_id: str, output_path: Path, model: str | None) -> list[str]:
    """Build a Codex resume command using only resume-supported flags."""
    cmd = [
        CODEX_CLI,
        "exec",
        "resume",
        "--skip-git-repo-check",
        "-o",
        str(output_path),
    ]
    mode = _codex_bridge_mode()
    if mode == "danger":
        cmd.append("--dangerously-bypass-approvals-and-sandbox")
    elif mode == "workspace-write":
        cmd.append("--full-auto")
    else:
        # `codex exec resume` does not expose `-s read-only`, so preserve safety
        # by starting a fresh non-resume session instead.
        return _build_codex_exec_cmd(output_path, model)

    if model:
        cmd.extend(["-m", model])
    cmd.extend([session_id, "-"])
    return cmd


def ask_codex(content: str, task_id: str | None = None, msg_type: str = "query",
              data: str | None = None, new_session: bool = False,
              from_llm: str = "gemini", from_model: str | None = None,
              to_model: str | None = None):
    """Send message to Codex AND invoke Codex to process it."""
    msg_id = send_message(content, task_id, msg_type, data, from_llm=from_llm,
                          to_llm="codex", from_model=from_model, to_model=to_model)
    print(f"\n🚀 Invoking Codex to process message #{msg_id}...")
    process_for_codex(msg_id, new_session)
    return msg_id


def process_for_codex(message_id: int, new_session: bool = False, no_timeout: bool = False):
    """Read message addressed to Codex, invoke via agent_runtime, send response.

    Phase 4: routes through scripts.agent_runtime.runner.invoke(). Resume
    is dropped (Codex resume_policy="never" in the registry); new_session
    parameter is accepted for backward compatibility but now always True
    in effect.
    """
    msg = _fetch_codex_message(message_id)
    if not msg:
        return

    _ = new_session  # No-op: Codex always starts fresh (resume_policy="never")
    prompt = build_codex_prompt(msg)
    timeout_val = 1800 if no_timeout else 900  # runner has its own hard_timeout
    model = _extract_target_model(msg)

    print(f"📨 Message #{msg['id']}")
    print(f"   From: {msg['from']} → To: {msg['to']}")
    print(f"   Type: {msg['type']}")
    print(f"   Task: {msg['task_id'] or 'N/A'}")
    print("   Session: NEW (Codex runtime always fresh)")

    try:
        result = runtime_invoke(
            "codex",
            prompt,
            mode=_codex_bridge_runtime_mode(),
            cwd=REPO_ROOT,
            model=model,
            task_id=msg["task_id"],
            session_id=None,  # Codex resume_policy="never"
            tool_config=None,
            entrypoint="bridge",
            hard_timeout=timeout_val,
            stall_timeout=min(180, timeout_val),
        )
    except RateLimitedError as exc:
        _handle_codex_error(msg, message_id, f"Rate limited: {exc}")
        return
    except AgentStalledError as exc:
        _handle_codex_error(msg, message_id, f"Codex stalled: {exc}")
        return
    except AgentTimeoutError as exc:
        _handle_codex_error(msg, message_id, f"Codex hard timeout: {exc}")
        return
    except AgentUnavailableError as exc:
        _handle_codex_error(msg, message_id, f"Codex unavailable: {exc}")
        return

    if not result.ok:
        _handle_codex_error(
            msg,
            message_id,
            result.stderr_excerpt or "Codex returned no final message",
        )
        return

    # Persist session ID for observability (though we never reuse it).
    if result.session_id and msg["task_id"]:
        set_session(msg["task_id"], "codex", result.session_id)

    response = result.response
    if not response:
        _handle_codex_error(msg, message_id, "Codex returned no final message")
        return

    print(f"\n✅ Codex finished ({len(response)} chars)")
    reply_id = send_message(
        content=response,
        task_id=msg["task_id"],
        msg_type="response",
        from_llm="codex",
        to_llm=msg["from"],
    )
    acknowledge(message_id)
    acknowledge(reply_id)


def _fetch_codex_message(message_id: int) -> dict | None:
    """Fetch a message addressed to Codex from the database."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, task_id, from_llm, to_llm, message_type, content, data, timestamp
        FROM messages
        WHERE id = ? AND to_llm = 'codex'
    """, (message_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        print(f"❌ Message {message_id} not found or not addressed to Codex")
        return None

    return {
        "id": row[0],
        "task_id": row[1],
        "from": row[2],
        "to": row[3],
        "type": row[4],
        "content": row[5],
        "data": row[6],
        "timestamp": row[7],
    }


def _extract_session_id(stdout: str) -> str | None:
    """Parse Codex session id from CLI stdout."""
    match = _SESSION_RE.search(stdout or "")
    return match.group(1) if match else None


def _extract_target_model(msg: dict) -> str | None:
    """Read optional to_model from message metadata JSON."""
    data = msg.get("data")
    if not data:
        return None
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return None
    return payload.get("to_model")


def _handle_codex_error(msg: dict, message_id: int, error_msg: str) -> None:
    """Send bridge error back to sender."""
    print(f"\n❌ Codex CLI error: {error_msg[:500]}")
    err_id = send_message(
        content=f"[Bridge Error] Codex CLI failed:\n{error_msg[:500]}",
        task_id=msg["task_id"],
        msg_type="error",
        from_llm="codex",
        to_llm=msg["from"],
        from_model="codex-bridge-error",
    )
    acknowledge(message_id)
    acknowledge(err_id)


def process_all_codex(new_session: bool = False):
    """Process ALL unread messages for Codex in batch."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'codex' AND acknowledged = 0
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Codex to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Codex...\n")
    success = 0
    failed = 0

    for row in rows:
        msg_id, _task_id, from_llm, _msg_type, preview = row
        preview = preview.replace("\n", " ")[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")
        try:
            process_for_codex(msg_id, new_session)
            success += 1
            print("    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")
