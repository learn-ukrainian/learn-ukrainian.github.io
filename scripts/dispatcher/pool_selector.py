"""Shadow funding selection. Nothing here changes a launch or consumes a reset.

Private ``budget_pools.json`` has ``version``, ``max_age_s``,
``claude_active_pool`` and ``pools``. Each pool has a private ``key``, ``agent``,
``kind`` (subscription/api/reset/held), ``source`` (a key in budget_sources),
``required_windows``, ``authorized`` and ``binding_verified``. Optional fields
are ``provider``, ``models``, ``held`` and ``protects_held``. Subscription pools
require explicit protection against drawing held credits. Policy and account
assertions belong in host config, never in the repository.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Route:
    agent: str
    model: str
    provider: str | None = None


@dataclass(frozen=True)
class Task:
    headless: bool = False


@dataclass(frozen=True)
class Window:
    name: str
    left: float | None
    ends_at: datetime | None
    unit: str = "%"


@dataclass(frozen=True)
class Meter:
    observed_at: datetime | None
    windows: tuple[Window, ...]
    status: str = "unknown"


@dataclass(frozen=True)
class Pool:
    key: str
    agent: str
    kind: Literal["subscription", "api", "reset", "held"]
    source: str
    required_windows: tuple[str, ...]
    authorized: bool = False
    binding_verified: bool = False
    protects_held: bool = False
    held: bool = False
    provider: str | None = None
    models: tuple[str, ...] = ()
    check_command: str = ""


@dataclass(frozen=True)
class Policy:
    version: str
    pools: tuple[Pool, ...]
    max_age_s: float = 720
    claude_active_pool: str | None = None


@dataclass(frozen=True)
class Rejected:
    pool: str
    reason: str


@dataclass(frozen=True)
class Selected:
    pool: str
    reasons: tuple[str, ...]
    rejected: tuple[Rejected, ...]


@dataclass(frozen=True)
class Refused:
    reasons: tuple[str, ...]
    rejected: tuple[Rejected, ...]


@dataclass(frozen=True)
class ResetRequired:
    pool: str
    reasons: tuple[str, ...]
    rejected: tuple[Rejected, ...]


def choose_pool(route: Route, task: Task, meters: dict[str, Meter], policy: Policy,
                now: datetime) -> Selected | Refused | ResetRequired:
    """Choose only funding, with operator orders preceding earliest lapse and key."""
    rejected: list[Rejected] = []
    eligible: list[tuple[Pool, Meter]] = []
    if not policy.version or not math.isfinite(policy.max_age_s) or policy.max_age_s <= 0:
        return Refused(("policy_not_checked",), ())
    for pool in policy.pools:
        meter = meters.get(pool.key)
        reason = None
        if (pool.agent, pool.provider) != (route.agent, route.provider) or (
            pool.models and route.model not in pool.models
        ):
            reason = "route_mismatch"
        elif pool.held or pool.kind == "held":
            reason = "held"
        elif not pool.authorized or not pool.binding_verified:
            reason = "authorization_or_binding_not_checked"
        elif task.headless and pool.kind != "api":
            reason = "headless_requires_api"
        elif pool.kind == "subscription" and not pool.protects_held:
            reason = "held_credit_protection_not_checked"
        elif meter is None or meter.status != "ok" or meter.observed_at is None:
            reason = "meter_not_checked"
        elif not 0 <= (now - meter.observed_at).total_seconds() < policy.max_age_s:
            reason = "meter_stale"
        else:
            windows = {w.name: w for w in meter.windows}
            if (not pool.required_windows or not set(pool.required_windows) <= windows.keys()
                    or any(w.left is None or not math.isfinite(w.left) or w.left < 0
                           or (w.unit == "%" and w.left > 100) for w in meter.windows)):
                reason = "window_not_checked"
            elif any(w.ends_at is None for w in meter.windows):
                reason = "deadline_not_checked"
            elif any(w.ends_at <= now for w in meter.windows):
                reason = "capacity_lapsed"
            elif any(w.left <= 0 for w in meter.windows):
                reason = "window_exhausted"
            elif pool.kind == "subscription" and pool.agent == "claude":
                weekly = windows.get("weekly")
                if weekly is None or weekly.unit != "%":
                    reason = "weekly_not_checked"
                elif weekly.left <= 1:
                    reason = "claude_99_percent_switch"
                elif policy.claude_active_pool is None:
                    reason = "active_account_not_checked"
        if reason:
            rejected.append(Rejected(pool.key, reason))
        else:
            eligible.append((pool, meter))
    if not eligible:
        return Refused(("no_eligible_pool",), tuple(sorted(rejected, key=lambda r: r.pool)))

    def rank(candidate):
        pool, meter = candidate
        # Resets never become launchable capacity. The operator must consume one.
        order = {"subscription": 0, "reset": 1, "api": 2}[pool.kind]
        drain = 0 if pool.key == policy.claude_active_pool else 1
        return order, drain, min(w.ends_at for w in meter.windows), pool.key

    chosen, _ = min(eligible, key=rank)
    rejected.extend(Rejected(p.key, "lower_priority") for p, _ in eligible if p.key != chosen.key)
    reasons = ["operator_order", "earliest_lapse", "deterministic_key"]
    if chosen.agent == "claude" and chosen.kind == "subscription":
        reasons.append("active_drain" if chosen.key == policy.claude_active_pool else "temporary_or_drain_switch")
    rejected.sort(key=lambda r: r.pool)
    if chosen.kind == "reset":
        return ResetRequired(chosen.key, (*reasons, "operator_reset_and_fresh_meter_required"), tuple(rejected))
    return Selected(chosen.key, tuple(reasons), tuple(rejected))


def timestamp(value) -> datetime | None:
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return datetime.fromtimestamp(value, UTC)
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.astimezone(UTC) if result.tzinfo else None
    except (AttributeError, TypeError, ValueError, OverflowError, OSError):
        return None


def config_path() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "learn-ukrainian" / "budget_pools.json"


def read_policy(path: Path | None = None) -> Policy:
    data = json.loads((path or config_path()).read_text())
    pools = []
    for row in data["pools"]:
        pool = Pool(**{**row, "required_windows": tuple(row["required_windows"]),
                       "models": tuple(row.get("models", ()))})
        if (not isinstance(pool.key, str) or not pool.key or pool.kind not in {"subscription", "api", "reset", "held"}
                or not all(isinstance(v, str) for v in (pool.agent, pool.source, *pool.required_windows, *pool.models))
                or any(type(getattr(pool, name)) is not bool
                       for name in ("authorized", "binding_verified", "protects_held", "held"))):
            raise ValueError("invalid private pool policy")
        pools.append(pool)
    if len({p.key for p in pools}) != len(pools):
        raise ValueError("duplicate private pool key")
    age = data.get("max_age_s", 720)
    version = data["version"]
    active = data.get("claude_active_pool")
    if (not isinstance(version, str) or not version or isinstance(age, bool)
            or not isinstance(age, (int, float)) or not math.isfinite(age) or age <= 0
            or (active is not None and active not in {
                p.key for p in pools if p.agent == "claude" and p.kind == "subscription"})):
        raise ValueError("invalid private allocator policy")
    return Policy(version, tuple(pools), age, active)


def read_budget() -> dict:
    """Reuse Monitor's cache-only reading. No provider probe or refresh is started."""
    base = os.environ.get("DELEGATE_MONITOR_API", "http://127.0.0.1:8765").rstrip("/")
    with urllib.request.urlopen(base + "/api/state/routing-budget", timeout=2) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError("invalid budget snapshot")
    return data


def _number(value) -> float | None:
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def budget_sources(budget: dict, now: datetime) -> dict[str, Meter]:
    """Normalize only measured capacity. Fleet spend estimates are never meters."""
    result = {}
    for key, row in budget.get("claude_accounts", {}).items():
        windows = tuple(Window(name, _number(row.get(name, {}).get("left_pct")),
                               timestamp(row.get(name, {}).get("resets_at"))) for name in ("session5h", "weekly"))
        result[key] = Meter(timestamp(row.get("updated")), windows,
                            "ok" if row.get("status") == "ok" and row.get("stale") is False else "unknown")
    for key, row in budget.get("agents", {}).items():
        if key == "claude":
            continue  # account-unattributed Claude capacity is never usable
        raw = row.get("codexbar") or {}
        windows = tuple(Window(name, _number(w.get("remaining_pct")), timestamp(w.get("resets_at")))
                        for name, w in (raw.get("windows") or {}).items()
                        if w.get("window_minutes") is not None or w.get("remaining_pct") is not None)
        age = _number(raw.get("age_s"))
        observed = timestamp(raw.get("fetched_at"))
        # Source cache age must agree with the timestamp; a newly served response is not a fresh observation.
        ok = (raw.get("freshness") == "fresh" and raw.get("stale") is False and age is not None
              and age >= 0 and observed is not None and (now - observed).total_seconds() >= age - 1)
        result[key] = Meter(observed, windows, "ok" if ok else "unknown")
        resets = raw.get("reset_credits")
        if isinstance(resets, dict):
            expiries = resets.get("expires_at")
            if isinstance(expiries, list):
                for index, expiry in enumerate(expiries):
                    result[f"{key}:reset:{index}"] = Meter(timestamp(resets.get("fetched_at")),
                        (Window("credit", 1, timestamp(expiry), "count"),), "ok" if ok else "unknown")
        balance = _number(raw.get("credit_balance"))
        if balance is not None:
            result[f"{key}:held"] = Meter(observed, (Window("credit", balance, None, "credits"),), "unknown")
    for key, row in budget.get("api_accounts", {}).items():
        left = _number(row.get("account_remaining_usd"))
        if left is None:
            left = _number(row.get("total_balance"))
        result[f"{key}:api"] = Meter(timestamp(row.get("fetched_at")),
            (Window("balance", left, timestamp(row.get("expires_at") or row.get("limit_reset")), "USD"),),
            "ok" if row.get("freshness") == "fresh" and row.get("stale") is False else "unknown")
    for key in ("openai:api", "claude:api", "muse"):
        result.setdefault(key, Meter(None, ()))
    return result


def shadow_decision(record: dict) -> dict:
    """Read and decide under the existing admission lock; never mutate the record."""
    from scripts.common.task_store_paths import tasks_dir
    from scripts.orchestration.dispatch_admission import admission_lock

    now = datetime.now(UTC)
    result = {"schema": "pool-shadow.v1", "observed_at": now.isoformat(), "shadow_only": True,
              "policy_version": None, "meter_sha256": None, "meters": {}}
    try:
        with admission_lock(tasks_dir()):
            policy = read_policy()
            sources = budget_sources(read_budget(), now)
            meters = {p.key: sources[p.source] for p in policy.pools if p.source in sources}
            decision = choose_pool(Route(record["agent"], record["model"], record.get("provider")),
                                   Task(headless=True), meters, policy, now)
            result.update(decision=type(decision).__name__, **asdict(decision), policy_version=policy.version,
                          meters=asdict_meter(meters),
                          meter_sha256=hashlib.sha256(json.dumps(asdict_meter(meters), sort_keys=True).encode()).hexdigest())
    except Exception:
        # Shadow telemetry can never become a new admission gate. Private exception text stays private.
        result.update(decision="Refused", reasons=["shadow_inputs_not_checked"], rejected=[])
    return result


def asdict_meter(meters: dict[str, Meter]) -> dict:
    return {key: {"observed_at": m.observed_at.isoformat() if m.observed_at else None,
                  "status": m.status, "windows": [dict(asdict(w), ends_at=w.ends_at.isoformat() if w.ends_at else None)
                                                   for w in m.windows]} for key, m in meters.items()}
