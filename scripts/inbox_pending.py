"""Body-free, read-only pending-order probe for AGY PreInvocation (#10558)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from scripts.common.bridge_paths import configured_bridge_db_path
from scripts.common.repo_root import main_checkout_root
from scripts.fleet_comms.paths import default_plane_root
from scripts.lib.readonly_sqlite import open_readonly
from scripts.orchestration.handoff_slot_registry import is_registered_slot, registry_readable

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_LINE = "PENDING ORDERS: unknown; run ai_agent_bridge inbox for the registered handoff slot"
LEGACY_WHERE = "to_llm = ? AND COALESCE(acknowledged, 0) = 0 AND COALESCE(consumed_by_live_driver, 0) = 0"
AUTHORITY_WHERE = """recipient = ? AND state IN ('queued', 'running')
    AND (deadline_at IS NULL OR deadline_at > ?)
    AND NOT EXISTS (SELECT 1 FROM authority_idempotency i
                    WHERE i.namespace = 'supervisory-consumption:' || d.delivery_id)
    AND NOT EXISTS (SELECT 1 FROM authority_wake_receipts w
                    WHERE w.delivery_id = d.delivery_id AND w.state = 'consumed')"""


def probe(recipient: str) -> dict:
    """Return only counts and identifiers; any uncertainty invalidates the result."""
    unknown = {
        "count": 0,
        "ids": [],
        "truncated": False,
        "stores": {"legacy": None, "authority": None},
        "probe": "unknown",
    }
    try:
        if not re.fullmatch(r"[a-z]+-[a-z0-9]+(?:-[a-z0-9]+)*", recipient):
            return unknown
        if not registry_readable() or not is_registered_slot(recipient):
            return unknown
        legacy = configured_bridge_db_path(main_checkout_root(ROOT))
        authority = default_plane_root(repo_root=ROOT) / "comms.sqlite3"
        stores = {}
        ids = []
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        for name, path, table, column, where, params in (
            ("legacy", legacy, "messages", "id", LEGACY_WHERE, (recipient,)),
            ("authority", authority, "authority_deliveries d", "message_id", AUTHORITY_WHERE, (recipient, now)),
        ):
            # Never create a missing store, migrate schema, claim, or read bodies.
            if not path.is_absolute() or not path.is_file():
                return unknown
            with closing(open_readonly(path, timeout=0.2)) as conn:
                conn.execute("BEGIN")
                stores[name] = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
                rows = conn.execute(f"SELECT {column} FROM {table} WHERE {where} ORDER BY {column} LIMIT 5", params)
                for (identifier,) in rows:
                    if name == "legacy":
                        if not isinstance(identifier, int) or identifier < 1:
                            return unknown
                    elif not isinstance(identifier, str) or not re.fullmatch(
                        r"(?:[a-z][a-z0-9-]*_|legacy-message-)[0-9a-f]{32}", identifier
                    ):
                        return unknown
                    ids.append(identifier)
        count = sum(stores.values())
        return {"count": count, "ids": ids[:5], "truncated": count > 5, "stores": stores, "probe": "ok"}
    except Exception:
        # Exception text can contain paths or data. It never leaves this boundary.
        return unknown


def _reject_constant(_value: str) -> None:
    raise ValueError("invalid_json")


def hook(stdin_text: str, recipient: str) -> dict:
    """Render one bounded ephemeral announcement, or silence for proven zero."""
    try:
        payload = json.loads(stdin_text, parse_constant=_reject_constant)
        if not isinstance(payload, dict):
            raise ValueError
        result = probe(recipient)
        if result["probe"] != "ok":
            message = UNKNOWN_LINE
        elif not result["count"]:
            return {}
        else:
            suffix = f"; ai_agent_bridge inbox --for {recipient}; ack --consumed-by-live-driver"
            prefix = f"PENDING ORDERS: {result['count']} (ids "
            shown = []
            for identifier in result["ids"]:
                candidate = [*shown, str(identifier)]
                if len(prefix + ",".join(candidate) + "; truncated)" + suffix) > 200:
                    break
                shown = candidate
            truncated = len(shown) < result["count"]
            message = prefix + ",".join(shown) + ("; truncated" if truncated else "") + ")" + suffix
            if not shown:
                message = UNKNOWN_LINE
    except Exception:
        message = UNKNOWN_LINE
    return {"injectSteps": [{"ephemeralMessage": message}]}


class _SilentParser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise ValueError("invalid_arguments")


def main(argv: list[str] | None = None) -> int:
    parser = _SilentParser(
        description="Report pending orders without bodies or writes.\nUse for per-call announcements, never to consume or acknowledge orders.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n  .venv/bin/python -m scripts.inbox_pending --recipient "$SESSION_HANDOFF_AGENT"\n'
            "  .venv/bin/python -m scripts.inbox_pending --agy-hook < hook-input.json\n"
            "Outputs: JSON on stdout; no files or database writes.\n"
            "Exit codes: 0 including unknown probes; argparse help exits 0.\n"
            "Related: #10558, docs/agent-runtime-guide.md."
        ),
    )
    parser.add_argument(
        "--recipient", default=None, help="Registered provider-lane handoff slot (default: SESSION_HANDOFF_AGENT)"
    )
    parser.add_argument(
        "--agy-hook",
        action="store_true",
        help="Read AGY JSON stdin and emit injectSteps (default: emit probe metadata)",
    )
    try:
        args = parser.parse_args(argv)
        recipient = args.recipient if args.recipient is not None else os.environ.get("SESSION_HANDOFF_AGENT", "")
        result = hook(sys.stdin.read(), recipient) if args.agy_hook else probe(recipient)
    except SystemExit as exc:
        if exc.code == 0:
            return 0
        result = hook("", "") if "--agy-hook" in (argv if argv is not None else sys.argv[1:]) else probe("")
    except Exception:
        result = hook("", "") if "--agy-hook" in (argv if argv is not None else sys.argv[1:]) else probe("")
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
