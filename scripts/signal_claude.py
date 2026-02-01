#!/usr/bin/env python3
"""
DEPRECATED: Use gemini_bridge.py instead!

This script now redirects to gemini_bridge.py for SQLite-based messaging.
Kept for backwards compatibility - will send to SQLite AND trigger notification.

Usage (PREFERRED):
    .venv/bin/python scripts/gemini_bridge.py send "Your message" --type query --task-id task-id

Usage (LEGACY - redirects to new system):
    .venv/bin/python scripts/signal_claude.py "Your message"
"""
import sys
import os
import subprocess
import argparse

# Get project root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE_SCRIPT = os.path.join(ROOT_DIR, "scripts", "gemini_bridge.py")
PYTHON = os.path.join(ROOT_DIR, ".venv", "bin", "python")


def signal_claude(message: str, task_id: str = None, msg_type: str = "response"):
    """
    Send message via gemini_bridge.py (SQLite) and trigger macOS notification.
    """
    print("=" * 60)
    print("DEPRECATION WARNING: signal_claude.py is deprecated!")
    print("Please use: .venv/bin/python scripts/gemini_bridge.py send ...")
    print("=" * 60)
    print()

    # Build command for gemini_bridge.py
    cmd = [PYTHON, BRIDGE_SCRIPT, "send", message, "--type", msg_type]
    if task_id:
        cmd.extend(["--task-id", task_id])

    try:
        # Send via SQLite bridge
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"Error sending message via bridge", file=sys.stderr)
            sys.exit(1)

        # Trigger macOS notification (still useful for alerting human)
        safe_message = message[:100].replace('"', '\\"')  # Truncate for notification
        notification_cmd = f'display notification "{safe_message}..." with title "Gemini → Claude"'
        subprocess.run(["osascript", "-e", notification_cmd], check=True)
        print("Notification sent.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="DEPRECATED: Send message to Claude. Use gemini_bridge.py instead."
    )
    parser.add_argument("message", help="The message to send to Claude.")
    parser.add_argument("--task-id", help="Task ID for grouping messages")
    parser.add_argument("--type", default="response", help="Message type (query, response, handoff)")
    args = parser.parse_args()

    signal_claude(args.message, args.task_id, args.type)
