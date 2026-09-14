"""Operator CLI over the Monitor's native subscription and prepaid probes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def read_budget(*, fresh: bool = False, transport: str = "dispatch") -> dict[str, Any]:
    """Use the warm Monitor snapshot, or a blocking refresh when explicitly fresh/offline."""
    if not fresh:
        base = os.environ.get("DELEGATE_MONITOR_API", "http://127.0.0.1:8765").rstrip("/")
        query = urllib.parse.urlencode({"transport": transport})
        try:
            with urllib.request.urlopen(f"{base}/api/state/routing-budget?{query}", timeout=5) as response:
                budget = json.load(response)
            if not isinstance(budget, dict) or not all(
                isinstance(budget.get(k), dict) for k in ("agents", "api_accounts")
            ):
                raise ValueError("invalid routing-budget payload")
            return {**budget, "source": "monitor-api"}
        except (OSError, urllib.error.URLError, ValueError):
            print("Monitor snapshot unavailable; running blocking native probes.", file=sys.stderr)
    from scripts.api.state_router import compute_routing_budget
    from scripts.api.subscription_usage import (
        API_ACCOUNT_PROVIDERS,
        SUBSCRIPTION_PROVIDERS,
        refresh_api_account_data,
        refresh_provider_usage_data,
    )

    with ThreadPoolExecutor(max_workers=2) as executor:
        subscription = executor.submit(refresh_provider_usage_data, SUBSCRIPTION_PROVIDERS)
        prepaid = executor.submit(refresh_api_account_data, API_ACCOUNT_PROVIDERS)
        subscription.result()
        prepaid.result()
    budget = compute_routing_budget(transport=transport)
    return {**budget, "source": "in-process-fresh"}


def _observation(info: dict[str, Any]) -> tuple[str, Any]:
    native = info.get("codexbar") or {}
    return str(info.get("freshness") or native.get("freshness") or "unavailable"), info.get(
        "age_s", native.get("age_s")
    )


def _usd(value: Any) -> str:
    return f"${value:.2f}" if isinstance(value, (int, float)) and not isinstance(value, bool) else "unknown"


def format_human(budget: dict[str, Any]) -> str:
    from scripts.api.state_router import _api_lane_status_from_account
    from scripts.fleet.capacity_pick import build_lane_rows

    agents = budget.get("agents") or {}
    lines = [
        f"source: {budget.get('source', 'unknown')}",
        "Subscriptions",
        "lane | status | remaining% | freshness | age_s | pace",
    ]
    for row in build_lane_rows(budget, lanes=tuple(agents)):
        lane = row["lane"]
        freshness, age = _observation(agents[lane])
        status = row["status"] if freshness != "unavailable" else "unknown"
        remaining = row["remaining_pct"]
        remaining_text = f"{remaining:.1f}" if remaining is not None and freshness != "unavailable" else "unknown"
        lines.append(
            f"{lane} | {status} | {remaining_text} | {freshness} | {age if age is not None else 'unknown'} | {row['pace']}"
        )
    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    for lane, account in (budget.get("api_accounts") or {}).items():
        freshness, age = _observation(account)
        status = _api_lane_status_from_account(lane, account)
        pick = (
            "n/a (funding account)"
            if lane == "openrouter"
            else ("AVOID" if status not in {"cool", "warm"} else "eligible")
        )
        lines.append(
            f"{lane} | {status} | pick: {pick} | freshness: {freshness} | age_s: {age if age is not None else 'unknown'} | probe: {account.get('probe_state', 'NEED_PROBE')}"
        )
        if lane == "openrouter":
            balance = _usd(account.get("account_remaining_usd"))
            if account.get("account_remaining_usd") is None:
                balance = (
                    "probe unavailable"
                    if account.get("balance_probe_state") == "NEED_PROBE"
                    else "needs management key"
                )
            lines.append(f"  balance: {balance} | key cap remaining: {_usd(account.get('limit_remaining_usd'))}")
            lines.append(
                f"  daily spend: {_usd(account.get('usage_daily_usd'))} | weekly spend: {_usd(account.get('usage_weekly_usd'))} | free tier: {account.get('is_free_tier', False)}"
            )
        else:
            lines.append(
                f"  balance: {account.get('currency') or 'unknown currency'} {account.get('total_balance')} | available: {account.get('is_available')}"
            )
    return "\n".join(lines)


def doctor() -> str:
    """Inspect credential locations only; never load or display credential contents."""
    home = Path.home()
    env_names = (
        "CLAUDE_CODE_OAUTH_TOKEN",
        "ANTHROPIC_AUTH_TOKEN",
        "KIMI_CODE_API_KEY",
        "GROK_OAUTH_TOKEN",
        "CURSOR_API_KEY",
        "OPENROUTER_API_KEY",
        "OPENROUTER_MANAGEMENT_API_KEY",
        "DEEPSEEK_API_KEY",
    )
    paths = [
        home / ".claude/.credentials.json",
        Path(os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser() / "auth.json",
        home / ".config/codex/auth.json",
        Path(os.environ.get("GROK_HOME", str(home / ".grok"))).expanduser() / "auth.json",
        Path(
            os.environ.get(
                "KIMI_CODE_CREDENTIALS_PATH",
                str(
                    Path(os.environ.get("KIMI_CODE_HOME", str(home / ".kimi-code"))).expanduser()
                    / "credentials/kimi-code.json"
                ),
            )
        ).expanduser(),
        home / ".gemini/antigravity-cli/antigravity-oauth-token",
        home / ".agy/credentials.json",
        home / ".config/agy/credentials.json",
        home / ".config/cursor/auth.json",
        home / ".config/cursor-agent/api.key.env",
        home / ".local/share/opencode/auth.json",
        home / ".secret/openrouter.key",
        home / ".secret/openrouter-management.key",
        home / ".secret/deepseek.key",
        home / ".secret/deekseep.key",
    ]
    lines = ["Credential presence only (does not verify login or balance):"]
    lines.extend(f"env {name}: {'present' if os.environ.get(name, '').strip() else 'absent'}" for name in env_names)
    for path in paths:
        try:
            present = "present" if path.is_file() else "absent"
        except OSError:
            present = "unavailable"
        # Standard locations stay portable; configured paths are not echoed.
        label = "~/" + str(path.relative_to(home)) if path.is_relative_to(home) else "configured credential path"
        lines.append(f"file {label}: {present}")
    lines.append(
        "OpenCode management entry: openrouter-management (key); presence of auth.json does not verify its entries."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect native subscription usage and prepaid funding.\n"
            "Use before routing work; this checks capacity, not model or review eligibility."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.fleet.usage show\n"
            "  .venv/bin/python -m scripts.fleet.usage json --fresh\n"
            "  .venv/bin/python -m scripts.fleet.usage doctor\n\n"
            "Outputs: stdout table/JSON; refresh updates process-local probe caches.\n"
            "Default: DELEGATE_MONITOR_API (http://127.0.0.1:8765); offline falls back to blocking probes.\n"
            "Exit codes: 0 snapshot/doctor printed (unknown is explicit); 1 read/refresh failed; 2 invalid arguments.\n"
            "Related: /api/state/routing-budget; scripts.fleet.capacity_pick; issue #8074."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="show",
        choices=("show", "json", "refresh", "doctor"),
        help="show (default): table; json: snapshot; refresh: blocking refresh/table; doctor: credential presence.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Block for native probes in this process (default: read Monitor); e.g. show --fresh.",
    )
    args = parser.parse_args(argv)
    if args.command == "doctor":
        print(doctor())
        return 0
    try:
        budget = read_budget(fresh=args.fresh or args.command == "refresh")
        print(json.dumps(budget, indent=2, sort_keys=True) if args.command == "json" else format_human(budget))
    except (OSError, ValueError, RuntimeError):
        print("Usage snapshot failed; capacity remains unknown. Run usage doctor.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
