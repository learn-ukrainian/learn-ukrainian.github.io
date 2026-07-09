"""CLI entry point: argument parsing, interactive mode, batch processing."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from agent_runtime import usage as runtime_usage

from ._agy import ask_agy
from ._ask_lifecycle import maybe_print_timeout_notice, print_asks, process_background_ask
from ._broker import bridge_status, broker_cleanup
from ._claude import ask_claude, process_for_claude
from ._codex import (
    ask_codex,
    ask_codex_chain,
    has_codex_headroom,
    process_all_codex,
    process_for_codex,
)
from ._config import GEMINI_DEFAULT_MODEL
from ._cursor import CURSOR_DEFAULT_MODEL, ask_cursor
from ._db import get_db
from ._dispatch_wrappers import (
    MANDATORY_COMMIT_PUSH_PR_CHECKLIST,
    REVIEW_DEEP_INSTRUCTIONS,
    handle_dispatch_fix,
    handle_review_deep,
)
from ._gemini import ask_gemini, converse_gemini, process_and_respond
from ._grok_build import (
    GROK_BUILD_DEFAULT_MODEL,
    ask_grok_build,
    process_for_grok_build,
)
from ._hermes import HERMES_DEFAULT_MODEL, ask_hermes
from ._messaging import (
    acknowledge,
    acknowledge_all,
    check_inbox,
    get_conversation,
    read_message,
    send_message,
)
from ._model import check_model
from ._opencode import (
    GEMMA_MODEL,
    GLM_MODEL,
    OPENCODE_DEFAULT_MODEL,
    POOL_DEFAULT_VARIANT,
    POOL_MODEL,
    ask_gemma,
    ask_glm,
    ask_opencode,
    ask_pool,
)

_CALLER_IDENTITY_ENV_HINTS = (
    # Order mirrors _detect_caller_identity_from_env; SESSION_HANDOFF_AGENT is
    # checked FIRST there — omitting it here left the "Cannot infer sender"
    # hint incomplete and let launcher-exported identity leak into tests.
    "SESSION_HANDOFF_AGENT",
    "CLAUDE_AGENT_NAME",
    "CODEX_SESSION",
    "CLAUDE_PROJECT_DIR",
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS",
    "GEMINI_SESSION",
)

_LEGACY_GEMINI_TO_AGY_MODEL = {
    "gemini-3.1-pro-preview": "gemini-3.1-pro-high",
    "gemini-3.0-flash-preview": "gemini-3.5-flash-high",
}


def _map_legacy_gemini_model_to_agy(model: str | None) -> str | None:
    if not model:
        return None
    return _LEGACY_GEMINI_TO_AGY_MODEL.get(model, model)


def _detect_caller_identity_from_env() -> str | None:
    """Infer the sending agent for legacy ask-* commands from wrapper env."""
    from ._channels import VALID_AGENTS

    handoff_agent = os.environ.get("SESSION_HANDOFF_AGENT")
    if handoff_agent:
        normalized = handoff_agent.strip().lower()
        if normalized in VALID_AGENTS:
            return normalized
    claude_name = os.environ.get("CLAUDE_AGENT_NAME")
    if claude_name:
        return claude_name.strip().lower()
    if os.environ.get("CODEX_SESSION"):
        return "codex"
    if os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS"):
        return "claude"
    if os.environ.get("GEMINI_SESSION"):
        return "gemini"
    return None


def _resolve_from_llm(args) -> str:
    """Return explicit --from or fail loudly if caller identity is unknown."""
    explicit = getattr(args, "from_llm", None)
    if explicit:
        return explicit
    detected = _detect_caller_identity_from_env()
    if detected:
        return detected
    hint_list = ", ".join(_CALLER_IDENTITY_ENV_HINTS)
    raise SystemExit(
        "Cannot infer sender for ask-* command. Pass --from explicitly or "
        f"run under a known agent wrapper that sets one of: {hint_list}."
    )


def interactive_mode():
    """Interactive mode for testing."""
    print("🔄 AI Agent Bridge Interactive Mode")
    print("Commands: inbox [agent], read <id>, send <text> --to <agent>, ack <id>, conv <task_id>, process <id>, quit")
    print()

    while True:
        try:
            cmd = input("bridge> ").strip()
            if not cmd:
                continue

            if cmd.lower() in ["quit", "q", "exit"]:
                break

            parts = cmd.split()
            action = parts[0].lower()

            _dispatch_interactive(action, parts)

        except KeyboardInterrupt:
            print("\nBye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def _dispatch_interactive(action: str, parts: list[str]):
    """Dispatch a single interactive mode command."""
    if action == "inbox":
        agent = parts[1] if len(parts) > 1 else "gemini"
        check_inbox(agent)
    elif action == "read" and len(parts) > 1:
        read_message(int(parts[1]))
    elif action == "send" and len(parts) > 1:
        content = " ".join(parts[1:])
        send_message(content)
    elif action == "ack" and len(parts) > 1:
        ids = [int(x) for x in parts[1:]]
        acknowledge(ids)
    elif action == "conv" and len(parts) > 1:
        get_conversation(parts[1])
    elif action == "process" and len(parts) > 1:
        process_and_respond(int(parts[1]))
    else:
        print("Unknown command or missing arguments.")


def process_all_gemini(model: str = GEMINI_DEFAULT_MODEL):
    """Process ALL unread messages for Gemini in batch."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'gemini' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Gemini to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Gemini...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, _task_id, from_llm, _msg_type, preview = row
        preview = preview.replace("\n", " ")[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_and_respond(msg_id, model)
            success += 1
            print("    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def process_all_claude(new_session: bool = False):
    """Process ALL unread messages for Claude in batch (headless)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, task_id, from_llm, message_type, substr(content, 1, 50)
        FROM messages
        WHERE to_llm = 'claude' AND acknowledged = 0
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("📭 No unread messages for Claude to process")
        return

    print(f"📬 Processing {len(rows)} unread message(s) for Claude (headless)...\n")

    success = 0
    failed = 0

    for row in rows:
        msg_id, _task_id, from_llm, _msg_type, preview = row
        preview = preview.replace("\n", " ")[:40]
        print(f"━━━ Processing [{msg_id}] from {from_llm}: {preview}...")

        try:
            process_for_claude(msg_id, new_session)
            success += 1
            print("    ✅ Done\n")
        except Exception as e:
            failed += 1
            print(f"    ❌ Failed: {e}\n")

    print(f"\n{'═' * 50}")
    print(f"📊 Results: {success} succeeded, {failed} failed out of {len(rows)} total")


def _parse_usage_window(window: str) -> int:
    """Return the reporting window in seconds."""
    windows = {
        "5h": 5 * 60 * 60,
        "24h": 24 * 60 * 60,
        "7d": 7 * 24 * 60 * 60,
        "30d": 30 * 24 * 60 * 60,
    }
    return windows[window]


def _iter_codex_usage_records(window: str, entrypoint: str):
    """Yield Codex usage records within the reporting window."""
    cutoff_ts = datetime.now(UTC).timestamp() - _parse_usage_window(window)

    for path in runtime_usage._usage_dir().glob("usage_codex-*.jsonl"):
        try:
            if path.stat().st_mtime < cutoff_ts:
                continue
        except OSError:
            continue

        try:
            with open(path, encoding="utf-8") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if entrypoint != "all" and record.get("entrypoint") != entrypoint:
                        continue
                    ts_str = record.get("ts")
                    if not ts_str:
                        continue
                    try:
                        record_ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00")).timestamp()
                    except (TypeError, ValueError):
                        continue
                    if record_ts < cutoff_ts:
                        continue
                    yield record
        except OSError:
            continue


def _build_codex_usage_report(window: str, entrypoint: str) -> dict:
    """Aggregate usage records into a printable report."""
    records = list(_iter_codex_usage_records(window, entrypoint))
    outcomes = ("ok", "error", "rate_limited", "timeout")
    by_outcome: dict[str, dict[str, object]] = {}
    by_entrypoint: dict[str, int] = {}
    recent_rate_limits: list[str] = []
    total_duration_s = 0.0

    for record in records:
        outcome = str(record.get("outcome") or "error")
        entry = str(record.get("entrypoint") or "unknown")
        duration = float(record.get("duration_s") or 0.0)
        total_duration_s += duration

        outcome_bucket = by_outcome.setdefault(
            outcome,
            {"count": 0, "total_duration_s": 0.0, "recent_events": []},
        )
        outcome_bucket["count"] = int(outcome_bucket["count"]) + 1
        outcome_bucket["total_duration_s"] = float(outcome_bucket["total_duration_s"]) + duration

        by_entrypoint[entry] = by_entrypoint.get(entry, 0) + 1

        if outcome == "rate_limited" and record.get("ts"):
            ts = str(record["ts"])
            recent_rate_limits.append(ts)
            cast_events = outcome_bucket["recent_events"]
            assert isinstance(cast_events, list)
            cast_events.append(ts)

    for outcome in outcomes:
        bucket = by_outcome.setdefault(
            outcome,
            {"count": 0, "total_duration_s": 0.0, "recent_events": []},
        )
        count = int(bucket["count"])
        bucket["avg_duration_s"] = round(float(bucket["total_duration_s"]) / count, 1) if count else 0.0
        bucket["total_duration_s"] = round(float(bucket["total_duration_s"]), 1)

    has_room, headroom_reason = has_codex_headroom("gpt-5.6-terra")
    return {
        "window": window,
        "entrypoint": entrypoint,
        "total_calls": len(records),
        "total_duration_s": round(total_duration_s, 1),
        "by_outcome": by_outcome,
        "by_entrypoint": dict(sorted(by_entrypoint.items())),
        "recent_rate_limits": sorted(recent_rate_limits),
        "headroom": {
            "model": "gpt-5.6-terra",
            "has_headroom": has_room,
            "reason": headroom_reason,
        },
    }


def _print_codex_usage_report(report: dict) -> None:
    """Render a human-readable Codex usage report."""
    print(f"Codex usage report - window: {report['window']}, entrypoint: {report['entrypoint']}")
    print("-" * 48)
    print(f"Total calls: {report['total_calls']}")
    print(f"Total duration: {report['total_duration_s']:.1f}s")
    print("By outcome:")

    for outcome in ("ok", "error", "rate_limited", "timeout"):
        bucket = report["by_outcome"][outcome]
        count = int(bucket["count"])
        pct = ((count / report["total_calls"]) * 100.0) if report["total_calls"] else 0.0
        line = f"  {outcome:<12} {count:>3}   ({pct:>4.1f}%)"
        total_duration = float(bucket["total_duration_s"])
        avg_duration = float(bucket["avg_duration_s"])
        recent_events = bucket["recent_events"]
        if outcome == "rate_limited" and recent_events:
            joined = ", ".join(str(ts) for ts in recent_events)
            line += f"   at {joined}"
        elif count:
            line += f"   total {total_duration:>6.1f}s"
            if avg_duration:
                line += f"   avg {avg_duration:.1f}s"
        print(line)

    print("\nBy entrypoint:")
    if report["by_entrypoint"]:
        for name, count in report["by_entrypoint"].items():
            print(f"  {name:<10} {count}")
    else:
        print("  (none)")

    headroom = report["headroom"]
    symbol = "✓" if headroom["has_headroom"] else "✗"
    line = f"\nHeadroom check: {headroom['model']} - has headroom {symbol}"
    if not headroom["has_headroom"] and headroom["reason"]:
        line += f" ({headroom['reason']})"
    print(line)


def _handle_codex_usage(args) -> None:
    """Handle codex-usage subcommand."""
    report = _build_codex_usage_report(args.window, args.entrypoint)
    if args.json:
        print(json.dumps(report, indent=2))
        return
    _print_codex_usage_report(report)


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Bridge CLI for Claude, Gemini, and Codex message passing.\n"
            "Use it for brokered multi-agent communication; do not use it as a substitute for direct local shell commands."
        ),
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ai_agent_bridge/__main__.py inbox --for gemini\n"
            "  .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex - --task-id review-123 < prompt.md\n"
            "  .venv/bin/python scripts/ai_agent_bridge/__main__.py process-codex 4812 --new-session\n\n"
            "Outputs:\n"
            "  Reads and writes broker messages, may invoke agent CLIs, and can post follow-up data to GitHub.\n\n"
            "Exit codes:\n"
            "  0 on successful command completion; non-zero on CLI misuse, broker failures, or agent invocation failures.\n\n"
            "Related:\n"
            "  Broker DB: batch_state/agent_comms.db\n"
            "  Runtime: scripts/agent_runtime/\n"
            "  Issue: #1379\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # inbox
    inbox_parser = subparsers.add_parser("inbox", help="Check inbox for messages")
    inbox_parser.add_argument(
        "--for",
        dest="for_llm",
        default="gemini",
        choices=["gemini", "claude", "codex"],
        help="Check inbox for which agent (default: gemini)",
    )

    # read
    read_parser = subparsers.add_parser("read", help="Read a specific message")
    read_parser.add_argument("message_id", type=int, help="Message ID to read")

    # send
    send_parser = subparsers.add_parser("send", help="Send message to another agent")
    send_parser.add_argument("content", help="Message content")
    send_parser.add_argument(
        "--to",
        dest="to_llm",
        default="claude",
        choices=["claude", "gemini", "codex"],
        help="Target agent (default: claude)",
    )
    send_parser.add_argument("--from", dest="from_llm", default="gemini", help="Sender agent name (default: gemini)")
    send_parser.add_argument("--task-id", help="Task ID for grouping")
    send_parser.add_argument("--type", default="response", help="Message type")
    send_parser.add_argument("--data", help="Path to data file to attach")
    send_parser.add_argument("--from-model", dest="from_model", help="Specific model ID of sender")
    send_parser.add_argument("--to-model", dest="to_model", help="Specific model ID of receiver")

    # ack
    ack_parser = subparsers.add_parser("ack", help="Acknowledge message(s)")
    ack_parser.add_argument("message_ids", type=int, nargs="+", help="Message ID(s) to acknowledge")

    # ack-all
    ack_all_parser = subparsers.add_parser("ack-all", help="Acknowledge ALL unread messages for an agent")
    ack_all_parser.add_argument("agent", choices=["claude", "gemini", "codex"], help="Agent whose inbox to clear")

    # conversation
    conv_parser = subparsers.add_parser("conversation", help="Get conversation history")
    conv_parser.add_argument("task_id", help="Task ID")

    # process (for Gemini)
    proc_parser = subparsers.add_parser("process", help="Process message with Gemini and respond")
    proc_parser.add_argument("message_id", type=int, help="Message ID to process")
    proc_parser.add_argument("--model", default=GEMINI_DEFAULT_MODEL, help="Gemini model")
    proc_parser.add_argument(
        "--no-timeout",
        dest="no_timeout",
        action="store_true",
        help="Run sync without timeout (used internally by fire-and-forget)",
    )

    # process-claude
    proc_claude_parser = subparsers.add_parser("process-claude", help="Process message with Claude CLI (headless)")
    proc_claude_parser.add_argument("message_id", type=int, help="Message ID for Claude to process")
    proc_claude_parser.add_argument(
        "--new-session",
        dest="new_session",
        action="store_true",
        help="Force new session even if one exists for this task",
    )
    proc_claude_parser.add_argument(
        "--async", dest="fire_and_forget", action="store_true", help="Launch Claude in background (no timeout)."
    )
    proc_claude_parser.add_argument(
        "--no-timeout",
        dest="no_timeout",
        action="store_true",
        help="Run sync without timeout (used internally by fire-and-forget)",
    )

    # process-codex
    proc_codex_parser = subparsers.add_parser("process-codex", help="Process message with Codex CLI (headless)")
    proc_codex_parser.add_argument("message_id", type=int, help="Message ID for Codex to process")
    proc_codex_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new session even if one exists"
    )
    proc_codex_parser.add_argument(
        "--no-timeout", dest="no_timeout", action="store_true", help="Run sync without timeout"
    )

    # process-grok-build
    proc_grok_build_parser = subparsers.add_parser(
        "process-grok-build",
        help="Process message with native Grok Build CLI (headless)",
    )
    proc_grok_build_parser.add_argument("message_id", type=int, help="Message ID for Grok Build to process")
    proc_grok_build_parser.add_argument(
        "--new-session",
        dest="new_session",
        action="store_true",
        help="Accepted for parity; grok-build always starts fresh",
    )
    proc_grok_build_parser.add_argument(
        "--no-timeout", dest="no_timeout", action="store_true", help="Run sync without timeout"
    )
    proc_grok_build_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    # process-ask is the detached-worker re-entry point for ``ask-* --background``.
    proc_ask_parser = subparsers.add_parser("process-ask", help=argparse.SUPPRESS)
    proc_ask_parser.add_argument("message_id", type=int)
    proc_ask_parser.add_argument("target")

    asks_parser = subparsers.add_parser("asks", help="List tracked one-shot ask lifecycle states")
    asks_parser.add_argument("--task-id", help="Only show asks for this task ID")

    # ask-claude
    ask_claude_parser = subparsers.add_parser("ask-claude", help="Send message AND invoke Claude (one-step)")
    ask_claude_parser.add_argument("content", help="Message content")
    ask_claude_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_claude_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_claude_parser.add_argument("--data", help="Path to data file to attach")
    ask_claude_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new session even if one exists"
    )
    ask_claude_parser.add_argument(
        "--from", dest="from_llm", help="Sender agent family. Default: inferred from environment"
    )
    ask_claude_parser.add_argument("--from-model", dest="from_model", help="Exact sender model ID")
    ask_claude_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_claude_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    # ask-codex
    ask_codex_parser = subparsers.add_parser(
        "ask-codex", help="Send message AND invoke Codex (one-step; use '-' to read from stdin)"
    )
    ask_codex_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_codex_parser.add_argument("--task-id", help="Task ID (required unless --chain is used)")
    ask_codex_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_codex_parser.add_argument("--data", help="Path to data file to attach")
    ask_codex_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new session even if one exists"
    )
    ask_codex_parser.add_argument(
        "--from", dest="from_llm", help="Sender agent family. Default: inferred from environment"
    )
    ask_codex_parser.add_argument("--from-model", dest="from_model", help="Exact sender model ID")
    ask_codex_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_codex_parser.add_argument(
        "--no-timeout", dest="no_timeout", action="store_true", help="Run sync without timeout"
    )
    ask_codex_parser.add_argument(
        "--chain",
        nargs="+",
        metavar="ISSUE",
        help="Dispatch multiple GitHub issues sequentially (e.g. 1212 #1213 issue-1214)",
    )
    ask_codex_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    # ask-gemini legacy compatibility shim
    ask_gemini_parser = subparsers.add_parser(
        "ask-gemini",
        help="Retired compatibility alias; routes through ask-agy",
    )
    ask_gemini_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_gemini_parser.add_argument("--task-id", required=True, help="Task ID (required for session tracking)")
    ask_gemini_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_gemini_parser.add_argument("--data", help="Path to data file to attach")
    ask_gemini_parser.add_argument(
        "--model", default=GEMINI_DEFAULT_MODEL, help="Legacy Gemini model slug; mapped to AGY where needed"
    )
    ask_gemini_parser.add_argument("--from-model", dest="from_model", help="Exact sender model ID")
    ask_gemini_parser.add_argument(
        "--from", dest="from_llm", help="Sender agent family. Default: inferred from environment"
    )
    ask_gemini_parser.add_argument(
        "--async", dest="async_mode", action="store_true", help="Queue only; legacy no-op for AGY shim"
    )
    ask_gemini_parser.add_argument(
        "--stdout-only",
        dest="stdout_only",
        action="store_true",
        help="Print AGY response body to stdout for the "
        "caller to parse; a thin summary still goes to the "
        "broker so the thread stays consistent. Suppresses "
        "all bridge progress logging on stdout.",
    )
    ask_gemini_parser.add_argument("--output-path", dest="output_path", help="Gemini writes output to this file.")
    ask_gemini_parser.add_argument("--extract", nargs="*", metavar="TAG", help="Extract delimited content from output.")
    ask_gemini_parser.add_argument(
        "--skip-model-check",
        dest="skip_model_check",
        action="store_true",
        help="Skip the model availability pre-flight check.",
    )
    ask_gemini_parser.add_argument(
        "--allow-write", dest="allow_write", action="store_true", help="Grant Gemini full bash + write access."
    )
    ask_gemini_parser.add_argument(
        "--delimiters", dest="delimiters", help="Comma-separated delimiter names for --allow-write mode."
    )
    ask_gemini_parser.add_argument(
        "--no-github", dest="no_github", action="store_true", help="Skip auto-posting review to GitHub issue"
    )
    # `--auth` mirrors the option on `inbox run` / `sync` (defined in
    # _channels_cli.py, value space ["auto", "subscription", "api-key",
    # "api"]). Wired through ask_gemini() → process_and_respond() →
    # runtime_invoke() as tool_config.auth_mode. Default None lets the
    # runtime fall back to its environment-driven detection.
    ask_gemini_parser.add_argument(
        "--auth",
        dest="auth",
        default=None,
        choices=["auto", "subscription", "api-key", "api"],
        help="Gemini auth mode override for this invocation",
    )
    ask_gemini_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    # ask-agy
    ask_agy_parser = subparsers.add_parser(
        "ask-agy",
        help="Send message AND invoke Agy (Antigravity CLI, Gemini-3.5-Flash-High)",
    )
    ask_agy_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_agy_parser.add_argument("--task-id", help="Task ID for session tracking")
    ask_agy_parser.add_argument("--type", default="query", help="Message type (default: query)")
    ask_agy_parser.add_argument("--data", help="Path to data file to attach")
    ask_agy_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new session (no-op today; reserved)"
    )
    ask_agy_parser.add_argument(
        "--from", dest="from_llm", help="Sender agent family. Default: inferred from environment"
    )
    ask_agy_parser.add_argument("--from-model", dest="from_model", help="Exact sender model ID")
    ask_agy_parser.add_argument(
        "--to-model", dest="to_model", help="Target Agy model ID (default: gemini-3.5-flash-high)"
    )
    ask_agy_parser.add_argument(
        "--stdout-only",
        dest="stdout_only",
        action="store_true",
        help="Print Agy response body to stdout for caller parsing",
    )
    ask_agy_parser.add_argument("--output-path", dest="output_path", help="Write Agy response body to a file")
    ask_agy_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true", help="Run sync without timeout")
    ask_agy_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    # ask-hermes
    ask_hermes_parser = subparsers.add_parser(
        "ask-hermes",
        help="Send message AND invoke Hermes one-shot (use '-' to read from stdin)",
    )
    ask_hermes_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_hermes_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_hermes_parser.add_argument("--type", default="query", help="Message type")
    ask_hermes_parser.add_argument("--data", help="Path to data file to attach")
    ask_hermes_parser.add_argument(
        "--model",
        default=HERMES_DEFAULT_MODEL,
        help=f"Hermes model (default {HERMES_DEFAULT_MODEL})",
    )
    ask_hermes_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_hermes_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_hermes_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_hermes_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-opencode
    ask_opencode_parser = subparsers.add_parser(
        "ask-opencode",
        help="Send message AND invoke opencode one-shot (use '-' to read from stdin)",
    )
    ask_opencode_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_opencode_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_opencode_parser.add_argument("--type", default="query", help="Message type")
    ask_opencode_parser.add_argument("--data", help="Path to data file to attach")
    ask_opencode_parser.add_argument(
        "--model",
        default=OPENCODE_DEFAULT_MODEL,
        help=f"Opencode model (default {OPENCODE_DEFAULT_MODEL})",
    )
    ask_opencode_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_opencode_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_opencode_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_opencode_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-pool (poolside.ai laguna-m.1 — cross-family CODE + web-verify specialist)
    ask_pool_parser = subparsers.add_parser(
        "ask-pool",
        help="Send message AND invoke poolside.ai (laguna-m.1) via the opencode router (use '-' for stdin)",
    )
    ask_pool_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_pool_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_pool_parser.add_argument("--type", default="query", help="Message type")
    ask_pool_parser.add_argument("--data", help="Path to data file to attach")
    ask_pool_parser.add_argument(
        "--variant",
        default=POOL_DEFAULT_VARIANT,
        choices=["minimal", "high", "max"],
        help=f"Reasoning effort (default {POOL_DEFAULT_VARIANT}; use high/max for harder tasks)",
    )
    ask_pool_parser.add_argument("--model", default=None, help=f"Override model (default {POOL_MODEL})")
    ask_pool_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_pool_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_pool_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-glm (Zhipu glm-5.2 — cross-family CODE + review; ⚠️ China-hosted, LOCAL-ONLY)
    ask_glm_parser = subparsers.add_parser(
        "ask-glm",
        help="Send message AND invoke Zhipu GLM (glm-5.2) via opencode. LOCAL-ONLY: data egresses to China, never in CI (use '-' for stdin)",
    )
    ask_glm_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_glm_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_glm_parser.add_argument("--type", default="query", help="Message type")
    ask_glm_parser.add_argument("--data", help="Path to data file to attach")
    ask_glm_parser.add_argument(
        "--model", default=None, help=f"Override GLM model (default {GLM_MODEL}; e.g. openrouter/z-ai/glm-5.2)"
    )
    ask_glm_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_glm_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_glm_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-gemma (Google Gemma 4 31B-it — cheap Google-family lane; ⚠️ not a sole seminar writer / factual reviewer)
    ask_gemma_parser = subparsers.add_parser(
        "ask-gemma",
        help="Send message AND invoke Google Gemma 4 (31B-it, cheap ~$0.12/$0.35 per M tok; :free variant via --model) via opencode. Cheap surface review + source-constrained wiki drafting; ⚠️ NOT a sole seminar writer / factual reviewer (use '-' for stdin)",
    )
    ask_gemma_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_gemma_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_gemma_parser.add_argument("--type", default="query", help="Message type")
    ask_gemma_parser.add_argument("--data", help="Path to data file to attach")
    ask_gemma_parser.add_argument(
        "--model",
        default=None,
        help=f"Override Gemma model (default {GEMMA_MODEL} — $0 via Google AI Studio direct; e.g. google-ais/gemma-4-26b-a4b-it, or the PAID openrouter/google/gemma-4-31b-it fallback)",
    )
    ask_gemma_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_gemma_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_gemma_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-cursor
    ask_cursor_parser = subparsers.add_parser(
        "ask-cursor",
        help="Send message AND invoke Cursor Agent one-shot (use '-' to read from stdin)",
    )
    ask_cursor_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_cursor_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_cursor_parser.add_argument("--type", default="query", help="Message type")
    ask_cursor_parser.add_argument("--data", help="Path to data file to attach")
    ask_cursor_parser.add_argument(
        "--model",
        default=CURSOR_DEFAULT_MODEL,
        help=f"Cursor model (default {CURSOR_DEFAULT_MODEL})",
    )
    ask_cursor_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_cursor_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_cursor_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_cursor_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")

    # ask-grok-build
    ask_grok_build_parser = subparsers.add_parser(
        "ask-grok-build",
        help="Send message AND invoke native Grok Build one-shot (use '-' to read from stdin)",
    )
    ask_grok_build_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    ask_grok_build_parser.add_argument("--task-id", required=True, help="Task ID")
    ask_grok_build_parser.add_argument("--type", default="query", help="Message type")
    ask_grok_build_parser.add_argument("--data", help="Path to data file to attach")
    ask_grok_build_parser.add_argument(
        "--new-session",
        dest="new_session",
        action="store_true",
        help="Accepted for parity; grok-build always starts fresh",
    )
    ask_grok_build_parser.add_argument(
        "--model",
        default=GROK_BUILD_DEFAULT_MODEL,
        help=f"Grok Build model (default {GROK_BUILD_DEFAULT_MODEL})",
    )
    ask_grok_build_parser.add_argument("--from", dest="from_llm", help="Sender agent family")
    ask_grok_build_parser.add_argument("--from-model", dest="from_model", help="Exact sender model")
    ask_grok_build_parser.add_argument("--to-model", dest="to_model", help="Target model ID")
    ask_grok_build_parser.add_argument("--no-timeout", dest="no_timeout", action="store_true")
    ask_grok_build_parser.add_argument("--review", action="store_true", help="Prepend docs/review-protocol.md")

    for ask_parser in (
        ask_claude_parser,
        ask_codex_parser,
        ask_gemini_parser,
        ask_agy_parser,
        ask_hermes_parser,
        ask_opencode_parser,
        ask_pool_parser,
        ask_glm_parser,
        ask_gemma_parser,
        ask_cursor_parser,
        ask_grok_build_parser,
    ):
        ask_parser.add_argument(
            "--background",
            action="store_true",
            help="Send immediately and process in a detached worker; print the message ID.",
        )

    # converse — multi-turn conversation with Gemini
    converse_parser = subparsers.add_parser("converse", help="Multi-turn conversation with Gemini (includes history)")
    converse_parser.add_argument("content", help="Message content (use '-' to read from stdin)")
    converse_parser.add_argument("--task-id", required=True, help="Conversation thread ID (e.g., 'a1-1-planning')")
    converse_parser.add_argument("--model", default="gemini-3.1-pro-preview", help="Gemini model")
    converse_parser.add_argument(
        "--no-github", dest="no_github", action="store_true", help="Skip auto-posting to GitHub"
    )

    # process-all
    proc_all_parser = subparsers.add_parser("process-all", help="Process ALL unread messages with Gemini")
    proc_all_parser.add_argument("--model", default=GEMINI_DEFAULT_MODEL, help="Gemini model")

    # process-claude-all
    proc_claude_all_parser = subparsers.add_parser("process-claude-all", help="Process ALL unread messages with Claude")
    proc_claude_all_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new sessions for each message"
    )

    # process-codex-all
    proc_codex_all_parser = subparsers.add_parser("process-codex-all", help="Process ALL unread messages with Codex")
    proc_codex_all_parser.add_argument(
        "--new-session", dest="new_session", action="store_true", help="Force new sessions for each message"
    )

    # codex-usage
    codex_usage_parser = subparsers.add_parser(
        "codex-usage",
        help="Summarize recent Codex runtime usage from batch_state/api_usage/",
    )
    codex_usage_parser.add_argument(
        "--window",
        default="5h",
        choices=["5h", "24h", "7d", "30d"],
        help="Reporting window (default: 5h)",
    )
    codex_usage_parser.add_argument(
        "--entrypoint",
        default="all",
        choices=["bridge", "dispatch", "delegate", "all"],
        help="Filter by Codex entrypoint (default: all)",
    )
    codex_usage_parser.add_argument(
        "--json",
        dest="json",
        action="store_true",
        help="Emit machine-readable JSON instead of text",
    )

    dispatch_fix_parser = subparsers.add_parser(
        "dispatch-fix",
        help="Dispatch a Codex worktree fix run with commit/push/PR guardrails",
        description=(
            "Dispatch a Codex worktree run using the hardcoded model assignment "
            "for code changes: Codex, danger mode, worktree, origin/main base, "
            "high effort."
        ),
        epilog=(
            "Example:\n"
            "  ab dispatch-fix 1701 --dry-run\n\n"
            "Mandatory checklist appended to dispatch-fix briefs:\n"
            f"{MANDATORY_COMMIT_PUSH_PR_CHECKLIST}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    dispatch_fix_parser.add_argument(
        "task_id",
        metavar="issue-or-task-id",
        help="GitHub issue number or stable task ID to use for delegate.py --task-id.",
    )
    dispatch_fix_parser.add_argument(
        "--brief-file",
        help="Use an existing brief file instead of generating one from gh issue view.",
    )
    dispatch_fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the prompt/state preview and print the delegate.py command without dispatching.",
    )

    review_deep_parser = subparsers.add_parser(
        "review-deep",
        help="Dispatch an adversarial Claude Opus read-only review run",
        description=(
            "Dispatch an adversarial Claude review using the hardcoded model "
            "assignment for deep design/code review: read-only Opus 4.7, xhigh "
            "effort by default."
        ),
        epilog=(
            "Example:\n"
            "  ab review-deep 1740 --dry-run\n"
            "  ab review-deep scripts/ai_agent_bridge --effort high --dry-run\n\n"
            "Prompt wrapper:\n"
            f"{REVIEW_DEEP_INSTRUCTIONS}"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    review_deep_parser.add_argument(
        "target",
        metavar="PR-or-path",
        help="PR number, #PR, file path, or directory path to review.",
    )
    review_deep_parser.add_argument(
        "--effort",
        default="xhigh",
        choices=["low", "medium", "high", "xhigh", "max"],
        help="Claude effort level (default: xhigh).",
    )
    review_deep_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write the prompt/state preview and print the delegate.py command without dispatching.",
    )

    # check-model
    check_model_parser = subparsers.add_parser(
        "check-model",
        help="Check if an AGY model is available (slug or display label)",
    )
    check_model_parser.add_argument("model", help="AGY model slug or display label")

    # cleanup
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean stuck broker state and old acknowledged rows")
    cleanup_parser.add_argument("--max-age", type=int, default=24, help="Force-ack stuck messages older than N hours")
    cleanup_parser.add_argument(
        "--older-than",
        default="30d",
        help="Delete acknowledged/terminal broker rows older than this age (default: 30d)",
    )
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Report what would be cleaned")

    # status
    subparsers.add_parser("status", help="Show running bridge processes")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Serve local HTTP bridge surfaces")
    serve_parser.add_argument(
        "--openai",
        action="store_true",
        help="Serve the OpenAI-compatible proxy",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for --openai (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8767,
        help="Port for --openai (default: 8767)",
    )
    serve_parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow binding to non-localhost (unsafe: no auth)",
    )

    # interactive
    subparsers.add_parser("interactive", help="Interactive mode")

    # send-codex-ui — Lane 1 from issue #2285 (agent bridge to running UI)
    send_codex_ui_parser = subparsers.add_parser(
        "send-codex-ui",
        help="Send a prompt to a running Codex Desktop UI session via `codex exec resume`",
    )
    send_codex_ui_parser.add_argument(
        "--thread",
        required=True,
        help="Codex thread UUID (find via `codex sessions list --last` or ~/.codex/sessions/)",
    )
    send_codex_ui_parser.add_argument(
        "--bridge-id",
        default=None,
        help="Correlation id (auto-generated if not given)",
    )
    send_codex_ui_parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the codex subprocess (default: caller's cwd)",
    )
    send_codex_ui_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Max wall-clock seconds (default 1800 = 30min)",
    )
    send_codex_ui_parser.add_argument(
        "--from-file",
        default=None,
        help="Read message body from a file (use '-' for stdin)",
    )
    send_codex_ui_parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as compact JSON (excludes verbose events list)",
    )
    send_codex_ui_parser.add_argument(
        "message",
        nargs="?",
        help="Inline message text. Mutually exclusive with --from-file.",
    )

    # send-agy-ui — Antigravity UI bridge mirroring send-codex-ui
    send_agy_ui_parser = subparsers.add_parser(
        "send-agy-ui",
        help="Send a prompt to an Antigravity UI conversation via `agy --print`",
    )
    send_agy_ui_parser.add_argument(
        "--thread",
        required=False,
        default=None,
        help="Antigravity conversation id (omit or pass 'new' for a fresh conversation)",
    )
    send_agy_ui_parser.add_argument(
        "--bridge-id",
        default=None,
        help="Correlation id (auto-generated if not given)",
    )
    send_agy_ui_parser.add_argument(
        "--cwd",
        default=None,
        help="Working directory for the agy subprocess (default: caller's cwd)",
    )
    send_agy_ui_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Max wall-clock seconds (default 1800 = 30min)",
    )
    send_agy_ui_parser.add_argument(
        "--from-file",
        default=None,
        help="Read message body from a file (use '-' for stdin)",
    )
    send_agy_ui_parser.add_argument(
        "--json",
        action="store_true",
        help="Print result as compact JSON (excludes verbose events list)",
    )
    send_agy_ui_parser.add_argument(
        "message",
        nargs="?",
        help="Inline message text. Mutually exclusive with --from-file.",
    )

    # Channel bridge commands (#1190) — registered in _channels_cli
    from ._channels_cli import register_channel_commands

    register_channel_commands(subparsers)

    return parser


def _dispatch_command(args):
    """Dispatch parsed CLI arguments to the appropriate handler."""
    if args.command == "serve":
        if not args.openai:
            raise SystemExit("serve currently requires --openai")

        if args.host != "127.0.0.1" and not args.allow_remote:
            raise SystemExit(
                "refusing to bind to non-localhost host without --allow-remote. "
                "the proxy has no auth and exposes 4 agent CLIs to anyone on the network."
            )

        import uvicorn

        from .openai_proxy import app

        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    elif args.command == "inbox":
        if getattr(args, "inbox_command", None):
            from ._channels_cli import dispatch_channel_command

            rc = dispatch_channel_command(args)
            sys.exit(rc)
        check_inbox(args.for_llm)
    elif args.command == "read":
        read_message(args.message_id)
    elif args.command == "send":
        data = None
        if args.data:
            data = Path(args.data).read_text()
        send_message(
            args.content, args.task_id, args.type, data, args.from_llm, args.to_llm, args.from_model, args.to_model
        )
    elif args.command == "ack":
        acknowledge(args.message_ids)
    elif args.command == "ack-all":
        acknowledge_all(args.agent)
    elif args.command == "conversation":
        get_conversation(args.task_id)
    elif args.command == "process":
        process_and_respond(args.message_id, args.model, no_timeout=args.no_timeout)
    elif args.command == "process-claude":
        process_for_claude(args.message_id, args.new_session, args.fire_and_forget, args.no_timeout)
    elif args.command == "process-codex":
        process_for_codex(args.message_id, args.new_session, args.no_timeout)
    elif args.command == "process-grok-build":
        process_for_grok_build(args.message_id, args.new_session, args.no_timeout, args.review)
    elif args.command == "process-ask":
        process_background_ask(args.message_id, args.target)
    elif args.command == "asks":
        print_asks(args.task_id)
    elif args.command == "ask-claude":
        _handle_ask_claude(args)
    elif args.command == "ask-codex":
        _handle_ask_codex(args)
    elif args.command == "ask-gemini":
        _handle_ask_gemini(args)
    elif args.command == "ask-agy":
        _handle_ask_agy(args)
    elif args.command == "ask-hermes":
        _handle_ask_hermes(args)
    elif args.command == "ask-opencode":
        _handle_ask_opencode(args)
    elif args.command == "ask-pool":
        _handle_ask_pool(args)
    elif args.command == "ask-glm":
        _handle_ask_glm(args)
    elif args.command == "ask-gemma":
        _handle_ask_gemma(args)
    elif args.command == "ask-cursor":
        _handle_ask_cursor(args)
    elif args.command == "ask-grok-build":
        _handle_ask_grok_build(args)
    elif args.command == "converse":
        content = sys.stdin.read() if args.content == "-" else args.content
        converse_gemini(content, args.task_id, args.model, getattr(args, "no_github", False))
    elif args.command == "process-all":
        process_all_gemini(args.model)
    elif args.command == "process-claude-all":
        process_all_claude(args.new_session)
    elif args.command == "process-codex-all":
        process_all_codex(args.new_session)
    elif args.command == "codex-usage":
        _handle_codex_usage(args)
    elif args.command == "dispatch-fix":
        sys.exit(handle_dispatch_fix(args))
    elif args.command == "review-deep":
        sys.exit(handle_review_deep(args))
    elif args.command == "check-model":
        ok = check_model(args.model, force=True)
        sys.exit(0 if ok else 1)
    elif args.command == "cleanup":
        broker_cleanup(args.max_age, args.dry_run, args.older_than)
    elif args.command == "status":
        bridge_status()
    elif args.command == "serve":
        if not args.openai:
            raise SystemExit("serve currently requires --openai")
        import uvicorn

        from .openai_proxy import app

        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    elif args.command == "interactive":
        interactive_mode()
    elif args.command == "send-codex-ui":
        from ._ui_codex import cli_main as _ui_codex_cli_main

        argv: list[str] = ["--thread", args.thread]
        if args.bridge_id:
            argv += ["--bridge-id", args.bridge_id]
        if args.cwd:
            argv += ["--cwd", args.cwd]
        if args.timeout != 1800:
            argv += ["--timeout", str(args.timeout)]
        if getattr(args, "json", False):
            argv += ["--json"]
        if args.from_file:
            argv += ["--from-file", args.from_file]
        if args.message:
            argv += [args.message]
        rc = _ui_codex_cli_main(argv)
        sys.exit(rc)
    elif args.command == "send-agy-ui":
        from ._ui_agy import cli_main as _ui_agy_cli_main

        argv = []
        if args.thread:
            argv += ["--thread", args.thread]
        if args.bridge_id:
            argv += ["--bridge-id", args.bridge_id]
        if args.cwd:
            argv += ["--cwd", args.cwd]
        if args.timeout != 1800:
            argv += ["--timeout", str(args.timeout)]
        if getattr(args, "json", False):
            argv += ["--json"]
        if args.from_file:
            argv += ["--from-file", args.from_file]
        if args.message is not None:
            argv += [args.message]
        rc = _ui_agy_cli_main(argv)
        sys.exit(rc)
    elif args.command in ("channel", "post", "p", "reconcile", "sync", "discuss"):
        # Channel bridge commands (#1190)
        from ._channels_cli import dispatch_channel_command

        rc = dispatch_channel_command(args)
        sys.exit(rc)
    else:
        return False
    return True


def _background_kwargs(args) -> dict[str, bool]:
    """Only pass the new option when requested to preserve compatibility shims."""
    return {"background": True} if getattr(args, "background", False) else {}


def _handle_ask_claude(args):
    """Handle ask-claude subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    kwargs = {"review": True} if getattr(args, "review", False) else {}
    from_llm = _resolve_from_llm(args)
    ask_claude(
        args.content,
        args.task_id,
        args.type,
        data,
        args.new_session,
        from_llm,
        args.from_model,
        args.to_model,
        **kwargs,
        **_background_kwargs(args),
    )


def _handle_ask_codex(args):
    """Handle ask-codex subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    content = sys.stdin.read() if args.content == "-" else args.content
    if args.chain:
        if args.task_id:
            raise SystemExit("ask-codex --chain derives issue task IDs automatically; omit --task-id")
        try:
            kwargs = {"review": True} if getattr(args, "review", False) else {}
            from_llm = _resolve_from_llm(args)
            ask_codex_chain(
                content,
                args.chain,
                args.type,
                data,
                args.new_session,
                from_llm,
                args.from_model,
                args.to_model,
                args.no_timeout,
                **kwargs,
                **_background_kwargs(args),
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        return
    if not args.task_id:
        raise SystemExit("ask-codex requires --task-id unless --chain is used")
    kwargs = {"review": True} if getattr(args, "review", False) else {}
    from_llm = _resolve_from_llm(args)
    ask_codex(
        content,
        args.task_id,
        args.type,
        data,
        args.new_session,
        from_llm,
        args.from_model,
        args.to_model,
        args.no_timeout,
        **kwargs,
        **_background_kwargs(args),
    )


def _handle_ask_agy(args):
    """Handle ask-agy subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    content = sys.stdin.read() if args.content == "-" else args.content
    kwargs = {"review": True} if getattr(args, "review", False) else {}
    from_llm = _resolve_from_llm(args)
    ask_agy(
        content,
        args.task_id,
        args.type,
        data,
        args.new_session,
        from_llm,
        args.from_model,
        args.to_model,
        args.no_timeout,
        stdout_only=getattr(args, "stdout_only", False),
        output_path=getattr(args, "output_path", None),
        **kwargs,
        **_background_kwargs(args),
    )


def _handle_ask_hermes(args):
    """Handle ask-hermes subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_hermes(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_opencode(args):
    """Handle ask-opencode subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_opencode(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_pool(args):
    """Handle ask-pool subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_pool(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        variant=args.variant,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_glm(args):
    """Handle ask-glm subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_glm(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_gemma(args):
    """Handle ask-gemma subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_gemma(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_cursor(args):
    """Handle ask-cursor subcommand."""
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_cursor(
        content,
        args.task_id,
        msg_type=args.type,
        data=args.data,
        model=args.model,
        from_llm=from_llm,
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
        **_background_kwargs(args),
    )


def _handle_ask_grok_build(args):
    """Handle ask-grok-build subcommand."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    content = sys.stdin.read() if args.content == "-" else args.content
    from_llm = _resolve_from_llm(args)
    ask_grok_build(
        content,
        args.task_id,
        msg_type=args.type,
        data=data,
        new_session=args.new_session,
        from_llm=from_llm,
        from_model=args.from_model,
        to_model=args.to_model,
        no_timeout=args.no_timeout,
        review=args.review,
        model=args.model,
        **_background_kwargs(args),
    )


def _handle_ask_gemini(args):
    """Compatibility shim: ask-gemini is retired and delegates to ask-agy."""
    data = None
    if args.data:
        data = Path(args.data).read_text()
    content = sys.stdin.read() if args.content == "-" else args.content
    kwargs = {"review": True} if getattr(args, "review", False) else {}
    from_llm = _resolve_from_llm(args)
    if not getattr(args, "stdout_only", False):
        print("⚠️ ask-gemini is retired; routing through ask-agy.", file=sys.stderr)
    ask_agy(
        content,
        args.task_id,
        args.type,
        data,
        new_session=False,
        from_llm=from_llm,
        from_model=getattr(args, "from_model", None),
        to_model=_map_legacy_gemini_model_to_agy(getattr(args, "model", None)) or "gemini-3.5-flash-high",
        no_timeout=False,
        stdout_only=getattr(args, "stdout_only", False),
        output_path=getattr(args, "output_path", None),
        **kwargs,
        **_background_kwargs(args),
    )


def main():
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()
    if args.command is not None:
        from ._channels_cli import _maybe_print_backlog_warnings

        _maybe_print_backlog_warnings()
        maybe_print_timeout_notice()
    if not _dispatch_command(args):
        parser.print_help()
