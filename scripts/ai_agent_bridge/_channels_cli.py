"""CLI subcommands for the channel bridge (#1190 Phase B.3).

This module is deliberately SEPARATE from ``_cli.py`` so that adding
channel commands doesn't touch the 600-line legacy CLI file more than
necessary. ``_cli.py`` imports ``register_channel_commands`` and
``dispatch_channel_command`` from this module — one line each — and
everything else lives here.

## CLI surface

```
ab channel new <name> [--description D] [--include C,...] [--agents A,...]
ab channel list
ab channel info <name>
ab channel context <name> [--edit] [--show]
ab channel tail <name> [--n N] [--thread TID]

ab post <channel> <body> [--to A,...] [--parent ID] [--corr ID]
ab p <channel> <agent> <body>                    # shorthand

ab discuss <channel> <body> --with A,B [--max-rounds N]   # B.4, stub for now
```

All commands use the storage primitives in ``_channels``. They do NOT
invoke agents — that's B.4 (``ab discuss``) and the legacy ``ask-*``
commands handle the agent-calling side.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from typing import Any

from . import _channels

# ── argparse registration ────────────────────────────────────────────


def register_channel_commands(subparsers: Any) -> None:
    """Register all channel-related CLI subcommands on a subparsers object.

    Called from ``_cli._build_parser()`` so that ``ai_agent_bridge -h``
    shows the channel commands alongside the legacy ``ask-*`` commands.
    """
    # ── top-level: channel group ──────────────────────────────────
    channel_parser = subparsers.add_parser(
        "channel",
        help="Channel management (new/list/info/context/tail)",
    )
    channel_sub = channel_parser.add_subparsers(
        dest="channel_command",
        required=True,
    )

    # ab channel new
    new_parser = channel_sub.add_parser("new", help="Create a new channel")
    new_parser.add_argument("name", help="Channel name (lowercase-kebab-case)")
    new_parser.add_argument(
        "--description", "-d", default="",
        help="One-line description of the channel's topic",
    )
    new_parser.add_argument(
        "--include", default="",
        help="Comma-separated list of channels to auto-include (e.g. 'shared')",
    )
    new_parser.add_argument(
        "--agents", default="",
        help="Comma-separated list of default subscriber agents",
    )

    # ab channel list
    channel_sub.add_parser(
        "list",
        help="List all channels with row counts and last activity",
    )

    # ab channel info
    info_parser = channel_sub.add_parser(
        "info",
        help="Show channel metadata + context preview + pending counts",
    )
    info_parser.add_argument("name", help="Channel name")

    # ab channel context
    ctx_parser = channel_sub.add_parser(
        "context",
        help="Edit or show a channel's pinned context.md",
    )
    ctx_parser.add_argument("name", help="Channel name")
    ctx_parser.add_argument(
        "--edit", action="store_true",
        help="Open context.md in $EDITOR (creates it if missing)",
    )
    ctx_parser.add_argument(
        "--show", action="store_true",
        help="Print context.md to stdout (default if no flags)",
    )

    # ab channel tail
    tail_parser = channel_sub.add_parser(
        "tail",
        help="Read the most recent messages from a channel",
    )
    tail_parser.add_argument("name", help="Channel name")
    tail_parser.add_argument(
        "-n", "--limit", type=int, default=20,
        help="How many recent messages to show (default: 20)",
    )
    tail_parser.add_argument(
        "--thread", default=None,
        help="Show all messages in a specific thread_id instead of channel tail",
    )
    tail_parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of human-readable",
    )

    # ── top-level: post ───────────────────────────────────────────
    post_parser = subparsers.add_parser(
        "post",
        help="Post a message to a channel (full form)",
    )
    post_parser.add_argument("channel", help="Channel name")
    post_parser.add_argument("body", help="Message body (use '-' for stdin)")
    post_parser.add_argument(
        "--to", default="",
        help="Comma-separated list of recipient agents (default: channel subscribers)",
    )
    post_parser.add_argument(
        "--parent", default=None,
        help="parent message_id — marks this as a reply",
    )
    post_parser.add_argument(
        "--corr", default=None,
        help="correlation_id — shared across a fanout event",
    )
    post_parser.add_argument(
        "--from-agent", default="user",
        choices=list(_channels.VALID_AGENTS),
        help="Sender agent (default: user)",
    )
    post_parser.add_argument(
        "--no-snapshot", action="store_true",
        help="Skip context/monitor snapshot (tests and system posts)",
    )

    # ── top-level: p (shortcut) ───────────────────────────────────
    p_parser = subparsers.add_parser(
        "p",
        help="Quick post: ab p <channel> <agent> <body>",
    )
    p_parser.add_argument("channel", help="Channel name")
    p_parser.add_argument(
        "agent",
        choices=list(_channels.VALID_AGENTS),
        help="Single recipient agent",
    )
    p_parser.add_argument("body", help="Message body (use '-' for stdin)")

    # ── top-level: discuss (B.4 stub) ─────────────────────────────
    discuss_parser = subparsers.add_parser(
        "discuss",
        help="Multi-agent discussion with round limit (B.4)",
    )
    discuss_parser.add_argument("channel", help="Channel name")
    discuss_parser.add_argument("body", help="Discussion topic (use '-' for stdin)")
    discuss_parser.add_argument(
        "--with", dest="with_agents", required=True,
        help="Comma-separated list of participating agents",
    )
    discuss_parser.add_argument(
        "--max-rounds", type=int, default=2,
        help="Maximum discussion rounds (default: 2, cap: 4)",
    )


# ── dispatch ──────────────────────────────────────────────────────────


def dispatch_channel_command(args) -> int:
    """Route an argparse ``Namespace`` to the right handler.

    Returns the process exit code (0 on success, non-zero on failure).
    Called from ``_cli._dispatch_command()`` when ``args.command`` is
    one of the channel commands.
    """
    command = args.command
    if command == "channel":
        return _dispatch_channel_group(args)
    if command == "post":
        return _handle_post(args)
    if command == "p":
        return _handle_p(args)
    if command == "discuss":
        return _handle_discuss(args)
    print(f"unknown channel command: {command}", file=sys.stderr)
    return 2


def _dispatch_channel_group(args) -> int:
    sub = args.channel_command
    if sub == "new":
        return _handle_channel_new(args)
    if sub == "list":
        return _handle_channel_list(args)
    if sub == "info":
        return _handle_channel_info(args)
    if sub == "context":
        return _handle_channel_context(args)
    if sub == "tail":
        return _handle_channel_tail(args)
    print(f"unknown subcommand: channel {sub}", file=sys.stderr)
    return 2


# ── handlers ──────────────────────────────────────────────────────────


def _resolve_body(body_arg: str) -> str:
    """Accept '-' to mean 'read from stdin'."""
    if body_arg == "-":
        return sys.stdin.read()
    return body_arg


def _parse_csv(s: str) -> list[str]:
    return [item.strip() for item in s.split(",") if item.strip()]


def _handle_channel_new(args) -> int:
    include = _parse_csv(args.include) if args.include else []
    agents = _parse_csv(args.agents) if args.agents else []
    try:
        ch = _channels.create_channel(
            args.name,
            description=args.description,
            include=include,
            subscribers=agents,
            exist_ok=True,
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    print(f"✅ channel '{ch['name']}' ready")
    if ch["include"]:
        print(f"   includes: {', '.join(ch['include'])}")
    if ch["subscribers"]:
        print(f"   subscribers: {', '.join(ch['subscribers'])}")
    return 0


def _handle_channel_list(args) -> int:
    channels = _channels.list_channels()
    if not channels:
        print("(no channels yet — try 'ab channel new shared')")
        return 0
    # Resolve row counts + latest message timestamps per channel
    from ._db import get_db
    conn = get_db()
    try:
        counts: dict[str, int] = {}
        latest: dict[str, str] = {}
        rows = conn.execute(
            """
            SELECT channel, COUNT(*) AS n, MAX(created_at) AS latest
            FROM channel_messages GROUP BY channel
            """
        ).fetchall()
        for r in rows:
            counts[r["channel"]] = r["n"]
            latest[r["channel"]] = r["latest"] or ""
    finally:
        conn.close()

    print(f"{'NAME':<20} {'MSGS':>6}  {'INCLUDES':<20}  {'SUBSCRIBERS':<30}  LATEST")
    print("-" * 100)
    for ch in channels:
        inc = ",".join(ch["include"]) or "-"
        sub = ",".join(ch["subscribers"]) or "-"
        n = counts.get(ch["name"], 0)
        ts = latest.get(ch["name"], "")[:19]
        print(f"{ch['name']:<20} {n:>6}  {inc:<20}  {sub:<30}  {ts}")
    return 0


def _handle_channel_info(args) -> int:
    ch = _channels.get_channel(args.name)
    if ch is None:
        print(f"❌ channel '{args.name}' does not exist", file=sys.stderr)
        return 1
    print(f"channel:     {ch['name']}")
    print(f"description: {ch['description'] or '(none)'}")
    print(f"created:     {ch['created_at']}")
    print(f"includes:    {', '.join(ch['include']) or '(none)'}")
    print(f"subscribers: {', '.join(ch['subscribers']) or '(none)'}")

    # Context preview
    ctx = _channels.load_channel_context(args.name)
    ctx_path = _channels.channel_context_path(args.name)
    if ctx_path.exists():
        size = ctx_path.stat().st_size
        print(f"\ncontext.md:  {ctx_path} ({size} bytes)")
        preview = ctx["body"].strip().split("\n")[:5]
        for line in preview:
            print(f"  | {line}")
    else:
        print(f"\ncontext.md:  {ctx_path} (missing)")
    if ctx["missing"]:
        print(f"⚠️  missing context for: {', '.join(ctx['missing'])}")
    return 0


def _handle_channel_context(args) -> int:
    path = _channels.channel_context_path(args.name)

    if args.edit:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        # Create the file with a helpful template if it doesn't exist
        if not path.exists():
            template = (
                f"# {args.name} — pinned context\n\n"
                f"This file holds project-wide rules and conventions that "
                f"agents should see on every post to the '{args.name}' channel. "
                f"Keep it STABLE — volatile state (current sprint, commits) "
                f"comes from the Monitor API snapshot per-post.\n\n"
                f"## Rules\n\n- (add rules here)\n"
            )
            path.write_text(template, encoding="utf-8")
        editor = os.environ.get("EDITOR", "vi")
        # Support EDITOR="code --wait" style values where the env var
        # contains the launcher plus flags. shlex splits the string
        # respecting POSIX quoting so "nvim -R" and similar work.
        editor_argv = shlex.split(editor) if editor else ["vi"]
        try:
            result = subprocess.run([*editor_argv, str(path)])
        except FileNotFoundError:
            print(
                f"❌ editor '{editor_argv[0]}' not found on PATH "
                f"(set $EDITOR to a valid command)",
                file=sys.stderr,
            )
            return 1
        except PermissionError:
            print(
                f"❌ editor '{editor_argv[0]}' is not executable "
                f"(check file permissions)",
                file=sys.stderr,
            )
            return 1
        return result.returncode

    # Default = show
    if not path.exists():
        print(f"(no context.md at {path})")
        print(f"create one with: ab channel context {args.name} --edit")
        return 0
    print(path.read_text("utf-8"))
    return 0


def _handle_channel_tail(args) -> int:
    # Verify the channel exists before hitting the storage layer so
    # the user gets a clean error instead of a raw traceback.
    if _channels.get_channel(args.name) is None:
        print(f"❌ channel '{args.name}' does not exist", file=sys.stderr)
        return 1

    try:
        if args.thread:
            msgs = _channels.read(args.name, thread_id=args.thread)
            header = f"thread {args.thread[:12]} in {args.name}"
        else:
            msgs = _channels.read(args.name, tail=args.limit)
            header = f"{args.name} tail {len(msgs)} / {args.limit}"
    except (ValueError, KeyError) as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(msgs, indent=2, ensure_ascii=False))
        return 0

    print(f"=== {header} ===")
    if not msgs:
        print("(no messages)")
        return 0
    for m in msgs:
        ts = m["created_at"][:19]
        parent_str = f" ← {m['parent_id'][:8]}" if m["parent_id"] else ""
        print(
            f"[{ts}] {m['from_agent']}"
            f" (r{m['round_index']}{parent_str}): {m['body'][:200]}"
        )
        if len(m["body"]) > 200:
            print(f"   ... [{len(m['body']) - 200} more chars]")
    return 0


def _handle_post(args) -> int:
    body = _resolve_body(args.body)
    if not body.strip():
        print("❌ empty body", file=sys.stderr)
        return 1

    ch = _channels.get_channel(args.channel)
    if ch is None:
        print(f"❌ channel '{args.channel}' does not exist", file=sys.stderr)
        return 1

    # Default recipients = channel subscribers
    to_agents = _parse_csv(args.to) if args.to else ch["subscribers"]

    try:
        result = _channels.post(
            args.channel,
            args.from_agent,
            body,
            to_agents=to_agents,
            parent_id=args.parent,
            correlation_id=args.corr,
            auto_snapshot=not args.no_snapshot,
        )
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    print(f"✅ posted to #{args.channel}")
    print(f"   message_id: {result['message_id']}")
    print(f"   thread_id:  {result['thread_id']}")
    if to_agents:
        print(f"   → {', '.join(to_agents)}  ({len(result['delivery_ids'])} deliveries)")
    return 0


def _handle_p(args) -> int:
    """Shortcut: ab p <channel> <agent> <body>."""
    # Rewrite to _handle_post's args shape
    class _Args:
        channel = args.channel
        body = args.body
        to = args.agent
        parent = None
        corr = None
        from_agent = "user"
        no_snapshot = False

    return _handle_post(_Args())


def _handle_discuss(args) -> int:
    """Stub for B.4 — prints the plan but doesn't invoke agents yet."""
    with_agents = _parse_csv(args.with_agents)
    rounds = min(max(1, args.max_rounds), 4)  # hard cap at 4
    print(f"[B.4 stub] would open a discussion on #{args.channel}")
    print(f"  participants: {', '.join(with_agents)}")
    print(f"  max rounds:   {rounds}")
    print(f"  topic:        {_resolve_body(args.body)[:100]}...")
    print()
    print("ab discuss is implemented in B.4 — tracking issue: #1190")
    return 0
