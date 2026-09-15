"""Operator CLI over the Monitor's native subscription and prepaid probes.

``show`` / ``json`` against a warm Monitor must not import ``state_router`` or
``learn_ukrainian_v4_runtime`` — notebooks often lack the editable v4 package.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.fleet.prepaid_status import api_lane_status_from_account


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
        except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
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
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    return str(info.get("freshness") or native.get("freshness") or "unavailable"), info.get(
        "age_s", native.get("age_s")
    )


def _usd(value: Any) -> str:
    return f"${value:.2f}" if isinstance(value, (int, float)) and not isinstance(value, bool) else "unknown"


def _pct(value: Any) -> str:
    return f"{float(value):.1f}%" if isinstance(value, (int, float)) and not isinstance(value, bool) else "unknown"


def _resets_text(value: Any) -> str:
    """Render reset timestamps; integer epoch seconds/ms → ISO-Z."""
    if value is None or value == "":
        return "unknown"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        ts = float(value)
        if ts > 1e12:  # ms
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=UTC).isoformat().replace("+00:00", "Z")
        except (OverflowError, OSError, ValueError):
            return str(value)
    return str(value)


def _window_kind(minutes: Any, explicit: Any = None) -> str:
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    if not isinstance(minutes, (int, float)) or isinstance(minutes, bool):
        return "window"
    m = float(minutes)
    if 200 <= m <= 400:
        return "5h"
    if 9000 <= m <= 12000:
        return "weekly"
    if 40000 <= m <= 50000:
        return "monthly"
    return f"{int(m)}m"


def _fail_note(info: dict[str, Any]) -> str:
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    kind = (
        info.get("failure_kind")
        or native.get("failure_kind")
        or info.get("error_kind")
        or native.get("error_kind")
    )
    code = info.get("last_failure_code") or native.get("last_failure_code")
    probe = info.get("probe_state") or native.get("probe_state")
    login = info.get("login_state") or native.get("login_state")
    parts: list[str] = []
    if kind:
        parts.append(str(kind))
    if code is not None:
        parts.append(str(code))
    if probe and str(probe).upper() not in {"OK", "HEALTHY", "NONE"}:
        parts.append(f"probe={probe}")
    if login and str(login).upper() not in {"AUTHENTICATED", "OK", "NONE", ""}:
        parts.append(f"login={login}")
    return "/".join(parts)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _lane_has_usable_allotment(info: dict[str, Any]) -> bool:
    """True only when a numeric quota or cool/warm pool status is present."""
    interactive = info.get("interactive") if isinstance(info.get("interactive"), dict) else None
    agentic = info.get("agentic_pool") if isinstance(info.get("agentic_pool"), dict) else None
    if interactive is not None:
        if str(interactive.get("status") or "") in {"cool", "warm", "hot", "near_cap"}:
            return True
        # Cap alone with unknown burn is not enough; need spent or burn.
        if _is_number(interactive.get("burn_pct_7d")) or _is_number(interactive.get("spent_7d_usd")):
            return True
    if agentic is not None:
        if str(agentic.get("status") or "") in {"cool", "warm", "hot", "near_cap"}:
            return True
        if _is_number(agentic.get("burn_pct_cycle")) or _is_number(agentic.get("spent_cycle_usd")):
            return True

    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    provider = info.get("provider_windows")
    if not isinstance(provider, dict):
        provider = native.get("provider_windows")
    if isinstance(provider, dict) and provider:
        for block in provider.values():
            if not isinstance(block, dict):
                continue
            if _is_number(block.get("used_pct")) or _is_number(block.get("remaining_pct")):
                return True
        # Named Cursor (or similar) shell present with only nulls — not a usable meter.
        return False

    windows = native.get("windows") if isinstance(native.get("windows"), dict) else None
    if isinstance(windows, dict):
        for block in windows.values():
            if not isinstance(block, dict):
                continue
            if _is_number(block.get("used_pct")) or _is_number(block.get("remaining_pct")):
                return True

    freshness, _ = _observation(info)
    status = str(info.get("status") or "unknown")
    return (
        freshness != "unavailable"
        and status in {"cool", "warm", "hot", "near_cap"}
        and _is_number(info.get("remaining_pct"))
    )


def _pace_line(
    used_pct: Any,
    resets_at: Any,
    *,
    window_minutes: Any,
) -> str | None:
    """CodexBar-style pace line for one allotment window, or ``None`` if not computable."""
    if not _is_number(used_pct) or resets_at in (None, ""):
        return None
    if not isinstance(window_minutes, (int, float)) or isinstance(window_minutes, bool) or window_minutes <= 0:
        return None
    from scripts.api.subscription_usage import (
        SESSION_WINDOW_MAX_MINUTES,
        compute_usage_pace,
        format_usage_pace_summary,
        pace_is_visible,
    )

    win_mins = int(window_minutes)
    pace = compute_usage_pace(float(used_pct), resets_at, window_minutes=win_mins)
    kind = "session" if win_mins <= SESSION_WINDOW_MAX_MINUTES else "weekly"
    if pace is None or not pace_is_visible(pace, kind=kind):
        return None
    return f"    pace: {format_usage_pace_summary(pace, kind=kind)}"


def _named_allotments(lane: str, info: dict[str, Any]) -> list[str]:
    """Human lines for weekly/monthly/module pools that actually exist on the payload."""
    lines: list[str] = []
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}

    # Claude: interactive weekly + agentic monthly (Fable/dispatch burns agentic).
    interactive = info.get("interactive") if isinstance(info.get("interactive"), dict) else None
    agentic = info.get("agentic_pool") if isinstance(info.get("agentic_pool"), dict) else None
    if interactive is not None:
        spent = interactive.get("spent_7d_usd")
        cap = interactive.get("weekly_cap_usd")
        lines.append(
            "  interactive (weekly): "
            f"status={interactive.get('status', 'unknown')} "
            f"burn={_pct(interactive.get('burn_pct_7d'))} "
            f"spent={_usd(spent)}/{_usd(cap)}"
        )
        pace = _pace_line(interactive.get("burn_pct_7d"), info.get("resets_at"), window_minutes=10080)
        if pace:
            lines.append(pace)
    if agentic is not None:
        spent = agentic.get("spent_cycle_usd")
        cap = agentic.get("monthly_cap_usd")
        lines.append(
            "  agentic/Fable (monthly): "
            f"status={agentic.get('status', 'unknown')} "
            f"burn={_pct(agentic.get('burn_pct_cycle'))} "
            f"spent={_usd(spent)}/{_usd(cap)} "
            f"active={agentic.get('active')}"
        )

    # Cursor / named provider pools (Cursor Models, Other Models, Grok Bot).
    provider = info.get("provider_windows")
    if not isinstance(provider, dict):
        provider = native.get("provider_windows")
    if isinstance(provider, dict) and provider:
        # Stable order: auto, api, grok_bot, total, then any extras.
        order = ["auto", "api", "grok_bot", "total"]
        keys = [k for k in order if k in provider] + [k for k in provider if k not in order]
        for key in keys:
            block = provider.get(key)
            if not isinstance(block, dict):
                continue
            label = str(block.get("label") or key)
            kind = _window_kind(block.get("window_minutes"), block.get("window"))
            lines.append(
                f"  {label} ({kind}): "
                f"used={_pct(block.get('used_pct'))} "
                f"rem={_pct(block.get('remaining_pct'))} "
                f"resets={_resets_text(block.get('resets_at'))}"
            )
            pace = _pace_line(
                block.get("used_pct"), block.get("resets_at"), window_minutes=block.get("window_minutes")
            )
            if pace:
                lines.append(pace)
        return lines

    # Generic primary/secondary/tertiary windows (Kimi 5h+weekly, Codex, Grok…).
    windows = native.get("windows") if isinstance(native.get("windows"), dict) else None
    if isinstance(windows, dict):
        for name, block in windows.items():
            if not isinstance(block, dict):
                continue
            used = block.get("used_pct")
            rem = block.get("remaining_pct")
            if used is None and rem is None and block.get("resets_at") is None:
                continue
            kind = _window_kind(block.get("window_minutes"), block.get("reset_description") or block.get("window"))
            label = str(block.get("label") or name)
            lines.append(
                f"  {label} ({kind}): "
                f"used={_pct(used)} rem={_pct(rem)} "
                f"resets={_resets_text(block.get('resets_at'))}"
            )
            pace = _pace_line(used, block.get("resets_at"), window_minutes=block.get("window_minutes"))
            if pace:
                lines.append(pace)

    return lines


def _display_status(info: dict[str, Any], *, freshness: str) -> str:
    """Allotment-honest status for the CLI (may differ from mix-max dispatch status)."""
    status = str(info.get("status") or "unknown")
    if freshness == "unavailable":
        return "unknown"
    probe = str(info.get("probe_state") or "")
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    if not probe:
        probe = str(native.get("probe_state") or "")
    error_kind = str(info.get("error_kind") or native.get("error_kind") or "")
    # NEED_PROBE / missing session: never show cool from ledger leftovers (e.g. rem=100).
    if probe == "NEED_LOGIN":
        return "need_login"
    if probe == "NEED_PROBE" and not _lane_has_usable_allotment(info):
        return "unknown"
    if error_kind in {"missing_credentials", "missing_session_token"} and not _lane_has_usable_allotment(
        info
    ):
        return "unknown"
    return status


def _lane_tips(lane: str, info: dict[str, Any], *, fail: str) -> list[str]:
    tips: list[str] = []
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    error_kind = str(info.get("error_kind") or native.get("error_kind") or "")
    probe = str(info.get("probe_state") or native.get("probe_state") or "")
    if lane == "cursor" and (
        error_kind in {"missing_credentials", "missing_session_token"}
        or (probe == "NEED_PROBE" and not _lane_has_usable_allotment(info))
    ):
        tips.append(
            "  tip: Auto/API/Grok Bot meters need a session JWT from `agent login` "
            "(writes ~/.config/cursor/auth.json). CURSOR_API_KEY alone is enough for "
            "dispatch, not for allotment percentages."
        )
    if lane == "claude" and ("429" in fail or "rate_limit" in fail.lower()):
        tips.append(
            "  tip: Anthropic rate-limited the usage probe (429). Wait and retry "
            "`usage show --fresh`; interactive/agentic caps above are ledger/LKG when burn is unknown."
        )
    if lane == "gemini" and ("403" in fail or "401" in fail):
        tips.append(
            "  tip: Antigravity quota API rejected the token, but a Gemini/AGY credential "
            "IS present (this is not a missing-credential case). Try `agy --prompt /usage` "
            "(AGY chat) before re-authenticating."
        )
    return tips


def format_human(budget: dict[str, Any]) -> str:
    """Render subscriptions + prepaid without importing Monitor routers."""
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    lines = [
        f"source: {budget.get('source', 'unknown')}",
        "Subscriptions (per-lane allotments; blank pools mean the probe did not return them)",
        "lane | status | remaining% | freshness | age_s | fail",
    ]
    usable = 0
    for lane in sorted(agents):
        info = agents.get(lane) if isinstance(agents.get(lane), dict) else {}
        freshness, age = _observation(info)
        status = _display_status(info, freshness=freshness)
        rem = info.get("remaining_pct")
        rem_text = (
            f"{float(rem):.1f}"
            if isinstance(rem, (int, float))
            and not isinstance(rem, bool)
            and freshness != "unavailable"
            and status not in {"unknown", "need_login"}
            else "unknown"
        )
        fail = _fail_note(info) or "-"
        lines.append(
            f"{lane} | {status} | {rem_text} | {freshness} | "
            f"{age if age is not None else 'unknown'} | {fail}"
        )
        allotments = _named_allotments(lane, info)
        if allotments:
            lines.extend(allotments)
        lines.extend(_lane_tips(lane, info, fail=fail))
        if _lane_has_usable_allotment(info):
            usable += 1
        elif freshness == "unavailable" and fail == "-" and not allotments:
            lines.append("  (no allotment windows; probe returned empty)")

    lines.extend(["", "Prepaid (USD; key cap remaining is not account balance)"])
    for lane, account in (budget.get("api_accounts") or {}).items():
        if not isinstance(account, dict):
            continue
        freshness, age = _observation(account)
        status = api_lane_status_from_account(lane, account)
        pick = (
            "n/a (funding account)"
            if lane == "openrouter"
            else ("AVOID" if status not in {"cool", "warm"} else "eligible")
        )
        lines.append(
            f"{lane} | {status} | pick: {pick} | freshness: {freshness} | "
            f"age_s: {age if age is not None else 'unknown'} | probe: {account.get('probe_state', 'NEED_PROBE')}"
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
                f"  daily spend: {_usd(account.get('usage_daily_usd'))} | "
                f"weekly spend: {_usd(account.get('usage_weekly_usd'))} | "
                f"free tier: {account.get('is_free_tier', False)}"
            )
        else:
            lines.append(
                f"  balance: {account.get('currency') or 'unknown currency'} "
                f"{account.get('total_balance')} | available: {account.get('is_available')}"
            )

    if usable == 0 and agents:
        lines.append("")
        lines.append(
            "WARN: no usable subscription allotment rows — mix-max is blind. "
            "Run: usage doctor && usage show --fresh; check fail= codes above."
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
    ]
    for name in (
        "openrouter.key",
        "openrouter-management.key",
        "deepseek.key",
        "deekseep.key",
        "zai.key",
    ):
        # ~/.secrets is the current host layout; ~/.secret is the legacy path.
        paths.append(home / ".secrets" / name)
        paths.append(home / ".secret" / name)
    lines = ["Credential presence only (does not verify login or balance):"]
    lines.extend(f"env {name}: {'present' if os.environ.get(name, '').strip() else 'absent'}" for name in env_names)
    for path in paths:
        try:
            present = "present" if path.is_file() else "absent"
        except OSError:
            present = "unavailable"
        label = "~/" + str(path.relative_to(home)) if path.is_relative_to(home) else "configured credential path"
        lines.append(f"file {label}: {present}")
    lines.append(
        "OpenCode management entry: openrouter-management (key); presence of auth.json does not verify its entries."
    )
    cursor_auth = home / ".config/cursor/auth.json"
    cursor_key = home / ".config/cursor-agent/api.key.env"
    has_session = False
    if cursor_auth.is_file():
        try:
            data = json.loads(cursor_auth.read_text(encoding="utf-8"))
            tok = data.get("accessToken") if isinstance(data, dict) else None
            has_session = isinstance(tok, str) and bool(tok.strip())
        except (OSError, json.JSONDecodeError):
            has_session = False
    has_api_key = bool(os.environ.get("CURSOR_API_KEY", "").strip()) or cursor_key.is_file()
    if has_api_key and not has_session:
        lines.append(
            "Cursor tip: CURSOR_API_KEY is present but ~/.config/cursor/auth.json has no accessToken — "
            "run `agent login` for Auto/API/Grok Bot allotment meters (API key alone cannot call "
            "GetCurrentPeriodUsage)."
        )
    lines.append(
        "Notebook tip: if `usage show --fresh` ImportErrors on learn_ukrainian_v4_runtime, "
        "run `.venv/bin/pip install -e packages/v4-runtime` (Monitor-backed `show` needs no v4)."
    )
    return "\n".join(lines)


def qa_snapshot(budget: dict[str, Any]) -> tuple[int, str]:
    """Exit 0 only when at least one subscription lane has a usable allotment signal."""
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    if not agents:
        return 1, "QA FAIL: routing-budget agents missing"
    problems: list[str] = []
    usable = 0
    for lane, info in agents.items():
        if not isinstance(info, dict):
            problems.append(f"{lane}: not an object")
            continue
        freshness, _ = _observation(info)
        if _lane_has_usable_allotment(info):
            usable += 1
        elif freshness == "unavailable" and not _fail_note(info) and not _named_allotments(lane, info):
            problems.append(f"{lane}: unavailable with no fail= and no pools")
    if usable == 0:
        problems.append("no usable subscription allotment rows (mix-max blind)")
    if problems:
        return 1, "QA FAIL:\n- " + "\n- ".join(problems)
    return 0, f"QA PASS: {usable} subscription lane(s) have usable allotment signal(s)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect native subscription usage and prepaid funding.\n"
            "Shows per-lane weekly/monthly/module pools when the probe returns them."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python -m scripts.fleet.usage show\n"
            "  .venv/bin/python -m scripts.fleet.usage json --fresh\n"
            "  .venv/bin/python -m scripts.fleet.usage doctor\n"
            "  .venv/bin/python -m scripts.fleet.usage qa\n\n"
            "Default: DELEGATE_MONITOR_API (http://127.0.0.1:8765); offline falls back to blocking probes.\n"
            "Exit codes: 0 ok; 1 read/refresh/qa failed; 2 invalid arguments.\n"
            "Related: /api/state/routing-budget; scripts.fleet.capacity_pick; issue #8074."
        ),
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="show",
        choices=("show", "json", "refresh", "doctor", "qa"),
        help="show (default); json; refresh; doctor; qa (fail if mix-max-blind).",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Block for native probes in this process (default: read Monitor).",
    )
    args = parser.parse_args(argv)
    if args.command == "doctor":
        print(doctor())
        return 0
    try:
        budget = read_budget(fresh=args.fresh or args.command == "refresh")
        if args.command == "qa":
            code, message = qa_snapshot(budget)
            print(message)
            if code == 0:
                print(format_human(budget))
            return code
        print(json.dumps(budget, indent=2, sort_keys=True) if args.command == "json" else format_human(budget))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
        print("Usage snapshot failed; capacity remains unknown. Run usage doctor.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
