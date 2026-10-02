"""Read-only, fail-closed access to the operator's shared Codex reset reserve."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.api.subscription_usage import get_provider_usage_data, pace_is_deficit
except ImportError:  # pragma: no cover - script path fallback
    from api.subscription_usage import get_provider_usage_data, pace_is_deficit  # type: ignore

try:
    from scripts.common.repo_root import main_checkout_root
except ImportError:  # pragma: no cover - script path fallback
    from common.repo_root import main_checkout_root  # type: ignore


SCHEMA_VERSION = "operator-reset-reserve.v1"
MAX_PROVIDER_AGE_SECONDS = 15 * 60
RESERVE_RELATIVE_PATH = Path("batch_state/routing_budget/operator_reset_reserve.json")


def utc_datetime(value: object) -> datetime | None:
    """Parse explicit UTC timestamps; naive and non-UTC offsets are rejected by design.

    The one timestamp rule for provider snapshots: ``credit_lane`` uses it too (#9518).
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC)


def unavailable_reserve() -> dict[str, Any]:
    """Return the stable sanitized representation of an unavailable assertion."""
    return {
        "available": False,
        "provider": "codex",
        "remaining_resets": None,
        "confirmed_at": None,
        "expires_at": None,
    }


def effective_reset_reserve(
    reserve: dict[str, Any], codex_info: dict[str, Any] | None, *, now: datetime | None = None
) -> dict[str, Any]:
    """Bound an assertion by the fresh live inventory, without changing it.

    A null credit expiry represents a provider-reported non-expiring credit.
    Otherwise the last unexpired credit bounds the assertion's own expiry.
    """
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if not isinstance(reserve, dict) or reserve.get("available") is not True:
        return unavailable_reserve()
    remaining = reserve.get("remaining_resets")
    confirmed_at = utc_datetime(reserve.get("confirmed_at"))
    expires_at = utc_datetime(reserve.get("expires_at"))
    if (
        isinstance(remaining, bool)
        or not isinstance(remaining, int)
        or remaining <= 0
        or confirmed_at is None
        or expires_at is None
        or confirmed_at > current
        or expires_at <= current
        or expires_at <= confirmed_at
    ):
        return unavailable_reserve()
    info = codex_info if isinstance(codex_info, dict) else {}
    cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    age = info.get("age_s", cb.get("age_s"))
    if (
        info.get("freshness", cb.get("freshness")) != "fresh"
        or isinstance(age, bool)
        or not isinstance(age, (int, float))
        or not math.isfinite(age)
        or not 0 <= age < MAX_PROVIDER_AGE_SECONDS
        or cb.get("stale") is True
        or info.get("stale") is True
    ):
        return unavailable_reserve()
    inventory = info.get("reset_credits", cb.get("reset_credits"))
    if not isinstance(inventory, dict):
        return unavailable_reserve()
    count = inventory.get("available_count")
    expirations = inventory.get("expires_at")
    fetched_at = utc_datetime(inventory.get("fetched_at"))
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count <= 0
        or not isinstance(expirations, list)
        or fetched_at is None
        or not 0 <= (current - fetched_at).total_seconds() < MAX_PROVIDER_AGE_SECONDS
    ):
        return unavailable_reserve()
    live_expirations: list[datetime | None] = []
    for value in expirations:
        expiry = utc_datetime(value)
        if value is not None and expiry is None:
            return unavailable_reserve()
        if expiry is None or expiry > current:
            live_expirations.append(expiry)
    effective_count = min(remaining, count, len(live_expirations))
    if effective_count <= 0:
        return unavailable_reserve()
    if None not in live_expirations:
        expires_at = min(expires_at, max(expiry for expiry in live_expirations if expiry is not None))
    return {
        "available": True,
        "provider": "codex",
        "remaining_resets": effective_count,
        "confirmed_at": confirmed_at.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


def load_reset_reserve(
    repo_root: Path, *, now: datetime | None = None, codex_info: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Load the primary checkout assertion and expose only its safe fields.

    The assertion is never changed or consumed. Invalid, absent, expired, or
    unknown/stale live inventory produces the same unavailable result. CLI
    consumers pass their Monitor provider snapshot; in-process API consumers
    use the shared provider cache.
    """
    path = main_checkout_root(Path(repo_root).resolve()) / RESERVE_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return unavailable_reserve()
    if not isinstance(payload, dict):
        return unavailable_reserve()
    expected = {"schema_version", "provider", "remaining_resets", "confirmed_at", "expires_at"}
    if set(payload) != expected:
        return unavailable_reserve()
    remaining = payload.get("remaining_resets")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("provider") != "codex"
        or isinstance(remaining, bool)
        or not isinstance(remaining, int)
        or remaining <= 0
    ):
        return unavailable_reserve()
    if codex_info is None:
        try:
            codex_info = get_provider_usage_data("codex")
        except (OSError, ValueError):
            return unavailable_reserve()
    return effective_reset_reserve({**payload, "available": True}, codex_info, now=now)


def codex_reset_reserve_eligible(
    reserve: dict[str, Any],
    codex_info: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    snapshot_stale: bool = False,
) -> bool:
    """Whether a valid reserve may relax an otherwise threatened Codex lane.

    Requires fresh authoritative provider windows, positive headroom, healthy
    and eligible lane state, no explicit auth failure, and clean runtime
    headroom diagnostics. Unknown/missing signals fail closed.
    """
    if snapshot_stale or not isinstance(reserve, dict) or reserve.get("available") is not True:
        return False
    if not effective_reset_reserve(reserve, codex_info, now=now)["available"]:
        return False
    info = codex_info if isinstance(codex_info, dict) else {}
    health = info.get("health")
    if not isinstance(health, dict) or health.get("healthy") is not True:
        return False
    if info.get("eligible") is False:
        return False

    cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    if any(
        str(value or "").upper() == "NEED_LOGIN"
        for value in (info.get("login_state"), cb.get("login_state"), info.get("probe_state"), cb.get("probe_state"))
    ):
        return False
    freshness = info.get("freshness", cb.get("freshness"))
    age = info.get("age_s", cb.get("age_s"))
    if (
        freshness != "fresh"
        or isinstance(age, bool)
        or not isinstance(age, (int, float))
        or not math.isfinite(age)
        or not 0 <= age < MAX_PROVIDER_AGE_SECONDS
        or cb.get("stale") is True
    ):
        return False
    probe_state = str(info.get("probe_state", cb.get("probe_state", ""))).upper()
    if probe_state in {"NEED_LOGIN", "NEED_PROBE", "ERROR", "UNAVAILABLE"}:
        return False

    runtime = info.get("runtime")
    if (
        not isinstance(runtime, dict)
        or runtime.get("headroom_blocked") is not False
        or runtime.get("summary_error")
        or isinstance(runtime.get("rate_limited"), bool)
        or not isinstance(runtime.get("rate_limited"), int)
        or runtime.get("rate_limited") != 0
        or runtime.get("last_rate_limited_at") is not None
    ):
        return False

    windows: list[object] = []
    weekly_windows: list[object] = []
    for source in (info.get("windows"), cb.get("windows"), info.get("provider_windows"), cb.get("provider_windows")):
        if isinstance(source, dict):
            windows.extend(source.values())
            weekly_windows.extend(block for name, block in source.items() if name == "weekly")
    # CodexBar exposes both named windows and flat fields. A flat used value
    # can report exhaustion even when its matching remaining value is absent.
    for name in ("primary", "secondary", "tertiary", "weekly"):
        block = {"remaining_pct": cb.get(f"{name}_remaining_pct"), "used_pct": cb.get(f"{name}_used_pct")}
        windows.append(block)
        if name == "weekly":
            weekly_windows.append(block)
    # The fresh notebook weekly report fills gaps in CodexBar. It is a
    # governing allotment window, not a cost-ledger estimate.
    notebook = info.get("notebook_report")
    if notebook is not None:
        if not isinstance(notebook, dict) or notebook.get("source") != "notebook-report":
            return False
        notebook_age = notebook.get("age_s")
        if (
            notebook.get("freshness") != "fresh"
            or isinstance(notebook_age, bool)
            or not isinstance(notebook_age, (int, float))
            or not math.isfinite(notebook_age)
            or not 0 <= notebook_age < MAX_PROVIDER_AGE_SECONDS
        ):
            return False
        weekly_block = {
            "remaining_pct": notebook.get("weekly_remaining_pct"),
            "used_pct": notebook.get("weekly_used_pct"),
        }
        windows.append(weekly_block)
        weekly_windows.append(weekly_block)
    has_positive_window = False
    has_positive_weekly = False
    weekly_ids = {id(block) for block in weekly_windows}
    for block in windows:
        if not isinstance(block, dict):
            continue
        remaining = next(
            (
                block.get(key)
                for key in ("remaining_pct", "remaining_percent", "remainingPercent")
                if block.get(key) is not None
            ),
            None,
        )
        used = next(
            (block.get(key) for key in ("used_pct", "used_percent", "usedPercent") if block.get(key) is not None),
            None,
        )
        if isinstance(remaining, (int, float)) and not isinstance(remaining, bool) and math.isfinite(remaining):
            if remaining <= 0:
                return False
            if remaining <= 100:
                has_positive_window = True
                if id(block) in weekly_ids:
                    has_positive_weekly = True
        if isinstance(used, (int, float)) and not isinstance(used, bool) and math.isfinite(used):
            if used >= 100:
                return False
            if 0 <= used < 100:
                has_positive_window = True
                if id(block) in weekly_ids:
                    has_positive_weekly = True
    return has_positive_window and has_positive_weekly


def codex_is_threatened(info: dict[str, Any] | None) -> bool:
    """True when status/pace would normally block or avoid Codex."""
    info = info if isinstance(info, dict) else {}
    status = str(info.get("status") or "")
    cb = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    return status in {"hot", "near_cap"} or pace_is_deficit(cb) is True
