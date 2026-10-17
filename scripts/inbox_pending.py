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

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.agent_runtime.agent_identity import seat_read_aliases
from scripts.ai_agent_bridge._channels import resolve_recipient_alias
from scripts.common.bridge_paths import configured_bridge_db_path
from scripts.common.repo_root import main_checkout_root
from scripts.fleet_comms.paths import default_plane_root
from scripts.lib.readonly_sqlite import open_readonly
from scripts.orchestration.handoff_slot_registry import is_registered_slot, registry_readable

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN_LINE = (
    "PENDING ORDERS: unknown; legacy: ai_agent_bridge inbox for the registered handoff slot; "
    "authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
)
LEGACY_PENDING = "COALESCE(acknowledged, 0) = 0 AND COALESCE(consumed_by_live_driver, 0) = 0"
AUTHORITY_WHERE = """recipient = ? AND state IN ('queued', 'running')
    AND (deadline_at IS NULL OR deadline_at > ?)
    AND NOT EXISTS (SELECT 1 FROM authority_idempotency i
                    WHERE i.namespace = 'supervisory-consumption:' || d.delivery_id)"""


def probe(recipient: str, *, limit: int = 5) -> dict:
    """Return only counts and identifiers; any uncertainty invalidates the result."""
    unknown = {
        "count": 0,
        "ids": [],
        "truncated": False,
        "stores": {"legacy": None, "authority": None},
        "probe": "unknown",
    }
    if type(limit) is not int or limit < 1 or limit > 500:
        return unknown
    try:
        from scripts.agent_runtime.kimi_admission import BRIDGE_MODE
        from scripts.agent_runtime.target_admission import resolve_and_admit

        if not re.fullmatch(r"[a-z]+-[a-z0-9]+(?:-[a-z0-9]+)*", recipient):
            return unknown
        if not registry_readable() or not is_registered_slot(recipient):
            return unknown
        # Match check_inbox's canonical legacy read set, never a family-wide
        # fallback for a dedicated slot. Unknown alias policy fails closed.
        legacy_recipients = seat_read_aliases(resolve_recipient_alias(recipient))
        if not legacy_recipients:
            return unknown
        # Authority publish/claim admit exact names without a roster resolver.
        # Legacy aliases are not authority aliases. Refuse unavailable or
        # changed admission rather than guessing another authority address.
        targets = resolve_and_admit((recipient,), mode=BRIDGE_MODE)
        if len(targets) != 1 or targets[0].recipient != recipient:
            return unknown
        placeholders = ",".join("?" for _ in legacy_recipients)
        legacy_where = f"to_llm IN ({placeholders}) AND {LEGACY_PENDING}"
        legacy = configured_bridge_db_path(main_checkout_root(ROOT))
        authority = default_plane_root(repo_root=ROOT) / "comms.sqlite3"
        stores = {}
        ids = []
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        for name, path, table, column, where, params in (
            ("legacy", legacy, "messages", "id", legacy_where, legacy_recipients),
            ("authority", authority, "authority_deliveries d", "message_id", AUTHORITY_WHERE, (recipient, now)),
        ):
            # Never create a missing store, migrate schema, claim, or read bodies.
            if not path.is_absolute() or not path.is_file():
                return unknown
            with closing(open_readonly(path, timeout=0.2)) as conn:
                conn.execute("BEGIN")
                if name == "authority":
                    # Preserve schema uncertainty without treating receiver
                    # observation as generation-bound supervisory consumption.
                    conn.execute("SELECT delivery_id, state FROM authority_wake_receipts LIMIT 0")
                stores[name] = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}", params).fetchone()[0]
                rows = conn.execute(
                    f"SELECT {column} FROM {table} WHERE {where} ORDER BY {column} LIMIT ?",
                    (*tuple(params), limit),
                )
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
        shown = ids[:limit]
        return {"count": count, "ids": shown, "truncated": count > len(shown), "stores": stores, "probe": "ok"}
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
            suffix = ""
            if result["stores"]["legacy"]:
                suffix += f"; legacy: ai_agent_bridge inbox --for {resolve_recipient_alias(recipient)}"
            if result["stores"]["authority"]:
                suffix += "; authority: .venv/bin/python -m scripts.fleet_comms deliveries --help"
            prefix = f"PENDING ORDERS: {result['count']} (ids "
            shown = []
            for identifier in result["ids"]:
                candidate = [*shown, str(identifier)]
                ending = "; truncated)" if len(candidate) < result["count"] else ")"
                if len(prefix + ",".join(candidate) + ending + suffix) > 200:
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
