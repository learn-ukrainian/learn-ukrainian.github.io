"""Credit-period lane state, model allowlist and reset advice (#9518).

A lane whose plan allowance is nearly used can show a prepaid credit balance.
The router cannot see the provider draw it: it sees a balance and our own
runtime outcomes. :func:`lane_credit_state` therefore says only what is known:
``credit_balance_present`` (plan at or below the threshold, fresh positive
balance, and no recent rate limit against it) or a fail-closed state that
keeps the lane in its plan state (near_cap/AVOID as before). That state is the
router's recommendation question only.
:func:`dispatch_refusal` answers a separate admission question: it refuses a
model outside the lane's credit-period allowlist whenever the plan window is at
or below the threshold AND a fresh positive credit balance exists
(:func:`allowlist_applies`: ``credit_balance_present``, ``credit_use_unconfirmed``
and ``credits_unverified`` for unreadable usage records all qualify), and under
``policy_error``, whether or not the router currently recommends the lane;
:func:`reset_advice` says whether a free full reset is worth using now. The policy lives in
``scripts/config/credit_lanes.yaml``. Everything here reads snapshots only:
nothing consumes credits or resets.

Fail closed: a missing, stale, non-numeric or non-positive balance, a balance
fetch time that is not an explicit fresh UTC timestamp, unreadable runtime
usage records, or one or more ``rate_limited`` outcomes for the lane within
``rate_limit_window_s`` keep the lane in its plan state. A malformed policy
file restricts only the lanes in :data:`DEFAULT_ALLOWED_MODELS`.
"""

from __future__ import annotations

import json
import math
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

SCHEMA_VERSION = "credit-lanes.v1"
POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "credit_lanes.yaml"
REFUSAL_CODE = "CREDIT_PERIOD_MODEL_REFUSED"

# Hard-wired minimal policy for a policy file that cannot be read: only these
# lanes stay restricted, to these models. A test pins it to the shipped yaml.
DEFAULT_ALLOWED_MODELS: dict[str, tuple[str, ...]] = {"codex": ("gpt-6.1-sol", "gpt-6-luna")}

NOT_CONFIGURED = "not_configured"
POLICY_ERROR = "policy_error"
PLAN_UNKNOWN = "plan_unknown"
PLAN_HEALTHY = "plan_healthy"
CREDIT_BALANCE_PRESENT = "credit_balance_present"
CREDITS_EXHAUSTED = "credits_exhausted"
CREDITS_UNVERIFIED = "credits_unverified"
CREDIT_USE_UNCONFIRMED = "credit_use_unconfirmed"

USE_RESET_NOW = "use_reset_now"
HOLD_RESET = "hold_reset"
NOT_APPLICABLE = "not_applicable"

DRAW_NOT_VERIFIED = "credit balance present; draw not verified by the router"
RATE_LIMIT_REASON = "recent rate limit while the plan window is exhausted: credit use not confirmed"

# No runtime usage record carries per-task credit consumption (agent_runtime
# usage JSONL has no credit field and its token field is unset for Codex), so
# coverage is reported as unknown rather than estimated from nothing.
COVERAGE_BASIS = "unknown: runtime usage records carry no per-task credit consumption"
ANCHOR_EVIDENCE = (
    "unverified: neither the provider usage record nor repository documentation states "
    "whether a full reset re-anchors the plan window"
)


@dataclass(frozen=True)
class CreditPolicy:
    near_cap_remaining_pct: float
    credit_max_age_s: float
    rate_limit_window_s: float
    reset_hold_hours: float
    allowed_models: dict[str, tuple[str, ...]]
    path: Path

    def lane_models(self, lane: str) -> tuple[str, ...] | None:
        return self.allowed_models.get(lane.strip().lower())


def _policy_number(payload: dict[str, Any], name: str, path: Path, *, positive: bool = False) -> float:
    value = payload.get(name)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        or (positive and value == 0)
    ):
        kind = "a positive" if positive else "a non-negative"
        raise ValueError(f"{path}: {name} must be {kind} number, got {value!r}")
    return float(value)


def load_policy(path: Path | None = None) -> CreditPolicy:
    """Read and validate the credit-period policy (default :data:`POLICY_PATH`); a missing or malformed file raises ``ValueError``."""
    path = path if path is not None else POLICY_PATH
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot read credit-lane policy: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: expected schema_version {SCHEMA_VERSION}")
    lanes = payload.get("lanes")
    if not isinstance(lanes, dict) or not lanes:
        raise ValueError(f"{path}: lanes must be a non-empty mapping")
    allowed: dict[str, tuple[str, ...]] = {}
    for lane, entry in lanes.items():
        models = entry.get("allowed_models") if isinstance(entry, dict) else None
        if not isinstance(models, list) or not models or not all(isinstance(m, str) and m.strip() for m in models):
            raise ValueError(f"{path}: lanes.{lane}.allowed_models must be a non-empty list of model ids")
        allowed[str(lane).strip().lower()] = tuple(m.strip() for m in models)
    return CreditPolicy(
        near_cap_remaining_pct=_policy_number(payload, "near_cap_remaining_pct", path),
        credit_max_age_s=_policy_number(payload, "credit_max_age_s", path),
        rate_limit_window_s=_policy_number(payload, "rate_limit_window_s", path, positive=True),
        reset_hold_hours=_policy_number(payload, "reset_hold_hours", path),
        allowed_models=allowed,
        path=path,
    )


def policy_error_state(lane: str, error: str) -> dict[str, Any]:
    """Credit field for ``lane`` when the policy cannot be read: the plan state applies.

    Lanes in :data:`DEFAULT_ALLOWED_MODELS` read ``policy_error`` with the default
    allowlist; every other lane is ``not_configured`` and unaffected.
    """
    models = DEFAULT_ALLOWED_MODELS.get(lane.strip().lower())
    if models is None:
        return {"state": NOT_CONFIGURED}
    return {
        "state": POLICY_ERROR,
        "reason": f"credit-lane policy unreadable ({error}); plan state applies",
        "allowed_models": list(models),
        "allowlist_applies": True,
    }


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def _field(info: dict[str, Any], key: str) -> Any:
    """``info[key]``, falling back to the native (codexbar) record when absent or null."""
    value = info.get(key)
    if value is None:
        native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
        value = native.get(key)
    return value


def utc_datetime(value: Any) -> datetime | None:
    """The reset reserve's UTC-only rule (naive and non-UTC offsets rejected), imported on use.

    Imported lazily so the shared test conftest can load this module without
    the provider-probe stack ``reset_reserve`` pulls in.
    """
    from scripts.fleet.reset_reserve import utc_datetime as parse

    return parse(value)


def _reset_time(value: Any) -> datetime | None:
    """Natural plan reset: epoch seconds/milliseconds (UTC by definition) or explicit-UTC ISO text."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000.0 if value > 1e12 else float(value)
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    return utc_datetime(value)


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _fresh_at(value: Any, now: datetime, max_age_s: float) -> datetime | None:
    """``value`` as an explicit UTC time no older than ``max_age_s`` and not in the future, else None."""
    parsed = utc_datetime(value)
    if parsed is None or not 0 <= (now - parsed).total_seconds() < max_age_s:
        return None
    return parsed


def plan_remaining_pct(info: dict[str, Any]) -> float | None:
    """Tightest reported plan window remaining-% (credits apply once any window is used up)."""
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    candidates = [
        _number(info.get("remaining_pct")),
        *(
            _number(native.get(key))
            for key in ("weekly_remaining_pct", "primary_remaining_pct", "secondary_remaining_pct")
        ),
    ]
    known = [value for value in candidates if value is not None]
    return min(known) if known else None


def _fresh_probe(info: dict[str, Any], policy: CreditPolicy, *, snapshot_stale: bool) -> tuple[bool, str]:
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    freshness = info.get("freshness", native.get("freshness"))
    age = _number(info.get("age_s", native.get("age_s")))
    if snapshot_stale:
        return False, "routing-budget snapshot is stale"
    if freshness != "fresh" or native.get("stale") is True or info.get("stale") is True:
        return False, f"credit probe freshness={freshness or 'missing'}"
    if age is None or not 0 <= age < policy.credit_max_age_s:
        return False, f"credit probe age_s={age if age is not None else 'missing'} (limit {policy.credit_max_age_s:g})"
    return True, ""


def read_recent_rate_limits(
    lane: str, window_s: float, *, now: datetime | None = None, usage_dir: Path | None = None
) -> dict[str, Any]:
    """``rate_limited`` outcomes for ``lane`` in the runtime usage records within ``window_s``.

    ``usage_dir`` defaults to the shared runtime usage directory. ``unreadable``
    counts relevant records that could not be read (see
    ``summarize_lane_runtime``); a count of 0 with ``unreadable["total"] > 0``
    is not "no rate limits".
    """
    from scripts.agent_runtime.usage import summarize_lane_runtime

    summary = summarize_lane_runtime(
        lane, window_s=window_s, usage_dir=usage_dir, now=now.timestamp() if now is not None else None
    )
    return {
        "count": int(summary["rate_limited"]),
        "last_rate_limited_at": summary["last_rate_limited_at"],
        "unreadable": dict(summary["unreadable"]),
    }


def _rate_limit_evidence(
    lane: str, record: dict[str, Any], policy: CreditPolicy, now: datetime, usage_dir: Path | None = None
) -> tuple[int | None, str | None, dict[str, int] | None]:
    """Recent rate-limit count, newest time and unreadable-record counts.

    ``(None, None, None)`` when the reader fails; the third item is the
    unreadable-record tally when part of the lane's records could not be read
    (the count is then not trusted: ``None``), else ``None``.

    The snapshot's own runtime summary counts as well when its window fits
    inside the policy window (it can come from another usage directory).
    """
    try:
        local = read_recent_rate_limits(lane, policy.rate_limit_window_s, now=now, usage_dir=usage_dir)
        count = local["count"]
        last = local["last_rate_limited_at"]
        unreadable = local.get("unreadable")
    except Exception:  # unreadable evidence is not "no evidence": fail closed
        return None, None, None
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return None, None, None
    if unreadable is not None:
        total = unreadable.get("total") if isinstance(unreadable, dict) else None
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            return None, None, None
        if total > 0:
            return None, last, {k: v for k, v in unreadable.items() if k != "total" and v}
    runtime = record.get("runtime") if isinstance(record.get("runtime"), dict) else {}
    window = _number(runtime.get("window_s"))
    snapshot_count = runtime.get("rate_limited")
    if (
        window is not None
        and window <= policy.rate_limit_window_s
        and isinstance(snapshot_count, int)
        and not isinstance(snapshot_count, bool)
        and snapshot_count > count
    ):
        count = snapshot_count
        last = runtime.get("last_rate_limited_at") or last
    if runtime.get("headroom_blocked") is True:
        # The 5-minute headroom block is itself rate-limit evidence.
        count = max(count, 1)
        last = last or runtime.get("last_rate_limited_at")
    return count, last, None


def lane_credit_state(
    lane: str,
    info: dict[str, Any] | None,
    policy: CreditPolicy,
    *,
    now: datetime | None = None,
    snapshot_stale: bool = False,
    usage_dir: Path | None = None,
    for_pace_deficit: bool = False,
) -> dict[str, Any]:
    """Credit state of one routing-budget lane record; see the module docstring for fail-closed rules.

    ``usage_dir`` is the runtime usage directory the rate-limit evidence is read
    from (default: the shared one). ``for_pace_deficit`` checks reserves even
    above the plan cap; it does not extend the credit-period admission gate.
    """
    models = policy.lane_models(lane)
    if models is None:
        return {"state": NOT_CONFIGURED}
    current = (now or datetime.now(UTC)).astimezone(UTC)
    record = info if isinstance(info, dict) else {}
    remaining = plan_remaining_pct(record)
    evidence: dict[str, Any] = {
        "rate_limited_count": None,
        "rate_limit_window_s": policy.rate_limit_window_s,
        "last_rate_limited_at": None,
        "credit_balance": None,
        "credit_fetched_at": None,
    }
    result: dict[str, Any] = {
        "plan_remaining_pct": remaining,
        "near_cap_remaining_pct": policy.near_cap_remaining_pct,
        "credit_balance": None,
        "allowed_models": list(models),
        "allowlist_applies": False,
        "evidence": evidence,
    }
    if remaining is None:
        return {**result, "state": PLAN_UNKNOWN, "reason": "plan allowance unknown"}
    if remaining > policy.near_cap_remaining_pct and not for_pace_deficit:
        return {
            **result,
            "state": PLAN_HEALTHY,
            "reason": f"plan remaining {remaining:g}% above {policy.near_cap_remaining_pct:g}%",
        }
    fresh, why = _fresh_probe(record, policy, snapshot_stale=snapshot_stale)
    if not fresh:
        return {**result, "state": CREDITS_UNVERIFIED, "reason": why}
    balance = _number(_field(record, "credit_balance"))
    if balance is None:
        return {**result, "state": CREDITS_UNVERIFIED, "reason": "credit balance missing or non-numeric"}
    evidence["credit_balance"] = balance
    fetched_at = _fresh_at(_field(record, "fetched_at"), current, policy.credit_max_age_s)
    if fetched_at is None:
        return {
            **result,
            "state": CREDITS_UNVERIFIED,
            "reason": "credit balance fetch time missing, not explicit UTC, or older than "
            f"{policy.credit_max_age_s:g}s",
        }
    evidence["credit_fetched_at"] = _iso(fetched_at)
    result["credit_balance"] = balance
    if balance <= 0:
        return {**result, "state": CREDITS_EXHAUSTED, "reason": f"credit balance {balance:g}"}
    count, last, unreadable = _rate_limit_evidence(lane, record, policy, current, usage_dir)
    evidence["rate_limited_count"] = count
    evidence["last_rate_limited_at"] = last
    if unreadable is not None:
        evidence["unreadable_records"] = unreadable
    # A fresh positive balance exists from here on: the admission allowlist applies
    # whatever the router's recommendation state says about the rate-limit evidence.
    result["allowlist_applies"] = remaining <= policy.near_cap_remaining_pct
    if unreadable is not None:
        parts = ", ".join(f"{n} {kind}" for kind, n in unreadable.items())
        return {
            **result,
            "state": CREDITS_UNVERIFIED,
            "reason": f"runtime usage records unreadable ({parts}): rate limits cannot be ruled out",
        }
    if count is None:
        return {**result, "state": CREDITS_UNVERIFIED, "reason": "runtime usage records unreadable"}
    if count > 0:
        return {**result, "state": CREDIT_USE_UNCONFIRMED, "reason": RATE_LIMIT_REASON}
    return {
        **result,
        "state": CREDIT_BALANCE_PRESENT,
        "reason": f"plan remaining {remaining:g}%"
        + ("; " if for_pace_deficit else f" at or below {policy.near_cap_remaining_pct:g}%; ")
        + f"fresh credit balance {balance:g}; no rate limit in the last {policy.rate_limit_window_s:g}s; "
        "draw not verified by the router",
        "coverage": {"dispatches": None, "basis": COVERAGE_BASIS},
    }


def pace_deficit_state(
    lane: str,
    info: dict[str, Any] | None,
    *,
    pace: dict[str, Any] | None = None,
    model: str | None = None,
    policy: CreditPolicy | None = None,
    now: datetime | None = None,
    snapshot_stale: bool = False,
    usage_dir: Path | None = None,
) -> dict[str, Any]:
    """Shared uncovered-pace decision for routing, admission and review (#9615).

    A fresh positive balance covers pace only for credit-allowlisted models;
    a fresh unexpired full reset covers any model. Both require readable,
    rate-limit-free runtime evidence. Nothing is consumed. Raw pace remains
    visible, and a runtime hot label or near_cap status is never relaxed here.
    """
    from scripts.api.subscription_usage import pace_is_deficit

    record = info if isinstance(info, dict) else {}
    if pace is None:
        pace = record.get("codexbar") or record.get("pace") or record
    current = (now or datetime.now(UTC)).astimezone(UTC)
    raw = pace_is_deficit(pace, now=current)
    status = record.get("status") or (record.get("interactive") or {}).get("status")
    result: dict[str, Any] = {
        "raw_deficit": raw,
        "uncovered": raw,
        "covered_by": [],
        "status": status,
        "reason": "pace deficit uncovered" if raw is True else "no confirmed pace deficit",
    }
    if raw is not True:
        return result
    remaining = plan_remaining_pct(record)
    if status in {"cool", "warm", "hot"} and remaining is not None and remaining > 10:
        result["status"] = "hot"
    if policy is None:
        try:
            policy = load_policy()
        except ValueError:
            return {**result, "reason": "pace deficit uncovered: reserve policy unreadable"}
    credit = lane_credit_state(
        lane,
        record,
        policy,
        now=current,
        snapshot_stale=snapshot_stale,
        usage_dir=usage_dir,
        for_pace_deficit=True,
    )
    if credit["state"] == CREDIT_BALANCE_PRESENT and (model is None or model_allowed(policy, lane, model)):
        result["covered_by"].append("credits")
    live = _verified_inventory(record, policy, current, snapshot_stale=snapshot_stale)
    if live:
        count, _, _ = _rate_limit_evidence(lane, record, policy, current, usage_dir)
        if count == 0:
            result["covered_by"].append("free full reset")
    if result["covered_by"]:
        result["uncovered"] = False
        result["reason"] = "pace deficit covered by " + " and ".join(result["covered_by"])
        runtime = record.get("runtime") if isinstance(record.get("runtime"), dict) else {}
        if (
            status in {"cool", "warm", "hot"}
            and not runtime.get("headroom_blocked")
            and remaining is not None
            and remaining > 10
        ):
            result["status"] = "cool" if remaining > 50 else "warm"
    return result


def allowlist_applies(state: dict[str, Any]) -> bool:
    """True when the credit-period allowlist gates admission for this lane state.

    The admission question, separate from the router recommendation: the plan
    window is at or below the threshold and a fresh positive balance exists
    (any of ``credit_balance_present``, ``credit_use_unconfirmed`` and the
    unreadable-usage ``credits_unverified``), or the policy is unreadable for a
    default lane. A healthy plan, a missing, stale or zero balance, and lanes
    outside the policy are not gated.
    """
    return state.get("allowlist_applies") is True


def _natural_reset(info: dict[str, Any]) -> datetime | None:
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    windows = native.get("windows") if isinstance(native.get("windows"), dict) else {}
    secondary = windows.get("secondary") if isinstance(windows.get("secondary"), dict) else {}
    for value in (native.get("weekly_resets_at"), secondary.get("resets_at"), info.get("resets_at")):
        parsed = _reset_time(value)
        if parsed is not None:
            return parsed
    return None


def _verified_inventory(
    info: dict[str, Any], policy: CreditPolicy, now: datetime, *, snapshot_stale: bool
) -> list[datetime | None] | None:
    """Unexpired free-reset expiries from a fresh inventory; None when unverified."""
    if not _fresh_probe(info, policy, snapshot_stale=snapshot_stale)[0]:
        return None
    inventory = _field(info, "reset_credits")
    if not isinstance(inventory, dict):
        return None
    count = inventory.get("available_count")
    expirations = inventory.get("expires_at")
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count < 0
        or not isinstance(expirations, list)
        or _fresh_at(inventory.get("fetched_at"), now, policy.credit_max_age_s) is None
    ):
        return None
    live: list[datetime | None] = []
    for value in expirations:
        expiry = utc_datetime(value)
        if value is not None and expiry is None:
            return None
        if expiry is None or expiry > now:
            live.append(expiry)
    return live[: min(count, len(live))]


def reset_advice(
    lane: str,
    info: dict[str, Any] | None,
    policy: CreditPolicy,
    state: str,
    *,
    now: datetime | None = None,
    snapshot_stale: bool = False,
) -> dict[str, Any]:
    """Whether a free full reset is useful now; advisory only, never consumes one."""
    current = (now or datetime.now(UTC)).astimezone(UTC)
    record = info if isinstance(info, dict) else {}
    natural = _natural_reset(record)
    hours = round((natural - current).total_seconds() / 3600.0, 1) if natural is not None else None
    live = _verified_inventory(record, policy, current, snapshot_stale=snapshot_stale)
    advice: dict[str, Any] = {
        "natural_reset_at": _iso(natural) if natural is not None else None,
        "hours_to_natural_reset": hours,
        "free_resets_available": len(live) if live is not None else None,
        "free_reset_expires_at": [_iso(e) if e is not None else None for e in live] if live is not None else None,
        "hold_hours": policy.reset_hold_hours,
        "window_anchor_evidence": ANCHOR_EVIDENCE,
    }

    def decide(verdict: str, reason: str) -> dict[str, Any]:
        return {**advice, "advice": verdict, "reason": reason}

    if live is None:
        return decide(NOT_APPLICABLE, "free-reset inventory missing or stale")
    if not live:
        return decide(NOT_APPLICABLE, "no free full reset available")
    if state in {PLAN_HEALTHY, PLAN_UNKNOWN, NOT_CONFIGURED}:
        return decide(NOT_APPLICABLE, f"plan state {state}: a reset adds nothing now")
    if hours is None:
        return decide(HOLD_RESET, "natural reset time unknown; window anchor behaviour unverified")
    if hours <= policy.reset_hold_hours:
        return decide(
            HOLD_RESET,
            f"natural reset in {hours:g}h is within the {policy.reset_hold_hours:g}h hold window; "
            "window anchor behaviour unverified",
        )
    return decide(
        USE_RESET_NOW,
        f"natural reset in {hours:g}h is beyond the {policy.reset_hold_hours:g}h hold window; "
        "using a reset is an operator decision (window anchor behaviour unverified)",
    )


def lane_credit_report(
    lane: str,
    info: dict[str, Any] | None,
    policy: CreditPolicy,
    *,
    now: datetime | None = None,
    snapshot_stale: bool = False,
) -> dict[str, Any]:
    """Credit state plus reset advice for a configured lane; ``{"state": "not_configured"}`` otherwise."""
    state = lane_credit_state(lane, info, policy, now=now, snapshot_stale=snapshot_stale)
    if state["state"] == NOT_CONFIGURED:
        return state
    return {
        **state,
        "reset_advice": reset_advice(lane, info, policy, state["state"], now=now, snapshot_stale=snapshot_stale),
    }


def published_credit_relief(
    lane: str,
    published: Any,
    model: str | None,
    *,
    policy: CreditPolicy | None = None,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    """Re-check the credit state a routing-budget snapshot published for ``lane`` (``agents.<lane>.credit``).

    For consumers that act on a snapshot (the reviewer resolver and the
    coordinator wave gate). None when there is nothing that could relax the plan
    state: the snapshot does not say ``credit_balance_present``, the lane is
    not in the local policy, or the policy is unreadable. Otherwise a receipt
    with the state, reason, evidence, the local allowlist and whether ``model``
    is on it; the state reads ``credits_unverified`` when the published balance
    fetch time is no longer fresh now (an old snapshot file proves nothing).

    The published rate-limit evidence is as old as the snapshot, so the
    current evidence is re-read through :func:`read_recent_rate_limits` (the
    shared runtime usage records): a rate limit since then reads
    ``credit_use_unconfirmed`` and unreadable records ``credits_unverified``,
    as :func:`lane_credit_state` would decide now.
    """
    if not isinstance(published, dict) or published.get("state") != CREDIT_BALANCE_PRESENT:
        return None
    if policy is None:
        try:
            policy = load_policy()
        except ValueError:
            return None
    allowed = policy.lane_models(lane)
    if allowed is None:
        return None
    current = (now or datetime.now(UTC)).astimezone(UTC)
    evidence = published.get("evidence") if isinstance(published.get("evidence"), dict) else {}
    receipt: dict[str, Any] = {
        "lane": lane.strip().lower(),
        "state": CREDIT_BALANCE_PRESENT,
        "reason": published.get("reason"),
        "credit_balance": published.get("credit_balance"),
        "evidence": dict(evidence),
        "allowed_models": list(allowed),
        "model": model,
        "model_allowed": _allowed(allowed, model),
        "draw": DRAW_NOT_VERIFIED,
    }
    if _fresh_at(evidence.get("credit_fetched_at"), current, policy.credit_max_age_s) is None:
        receipt["state"] = CREDITS_UNVERIFIED
        receipt["reason"] = (
            f"published credit balance fetch time missing, not explicit UTC, or older than {policy.credit_max_age_s:g}s"
        )
        return receipt
    count, last, unreadable = _rate_limit_evidence(lane, {}, policy, current)
    receipt["evidence"].update(
        {"rate_limited_count": count, "last_rate_limited_at": last, "rate_limits_checked_at": _iso(current)}
    )
    if unreadable is not None:
        receipt["evidence"]["unreadable_records"] = unreadable
    if count is None:
        receipt["state"] = CREDITS_UNVERIFIED
        receipt["reason"] = "runtime usage records unreadable now: rate limits cannot be ruled out"
    elif count > 0:
        receipt["state"] = CREDIT_USE_UNCONFIRMED
        receipt["reason"] = RATE_LIMIT_REASON
    return receipt


def _allowed(allowed: tuple[str, ...], model: str | None) -> bool:
    if not model:
        return False
    from scripts.review.model_catalog import canonical_model_id

    return (canonical_model_id(model) or model.strip().lower()) in allowed


def model_allowed(policy: CreditPolicy, lane: str, model: str | None) -> bool:
    """True when ``model`` (catalog-canonicalised) is on ``lane``'s credit-period allowlist."""
    allowed = policy.lane_models(lane)
    return True if allowed is None else _allowed(allowed, model)


def refusal_text(lane: str, model: str | None, state: dict[str, Any], policy: CreditPolicy) -> str:
    return (
        f"{REFUSAL_CODE}: lane {lane} is {state['state']} ({state.get('reason')}); a fresh credit balance "
        f"exists while the plan window is exhausted, so model {model or '(none)'} "
        f"is outside the credit-period allowlist [{', '.join(policy.lane_models(lane) or ())}] "
        f"({policy.path.name}). Dispatch an allowlisted model or another lane."
    )


def read_routing_budget(*, timeout: float = 8.0) -> dict[str, Any] | None:
    """Fresh Monitor routing-budget snapshot, or None when it cannot be read."""
    base = os.environ.get("DELEGATE_MONITOR_API", "http://127.0.0.1:8765").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/state/routing-budget?fresh_codexbar=true", timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _policy_error_refusal(lane: str, model: str | None, error: str) -> str | None:
    """Admission under an unreadable policy: only off-default-allowlist models on default lanes are refused."""
    print(
        f"⚠ credit-lane policy unreadable ({error}); only "
        f"{', '.join(sorted(DEFAULT_ALLOWED_MODELS))} dispatches are restricted, to the built-in allowlist.",
        file=sys.stderr,
    )
    allowed = DEFAULT_ALLOWED_MODELS.get(lane)
    if allowed is None or _allowed(allowed, model):
        return None
    return (
        f"{REFUSAL_CODE}: lane {lane} is {POLICY_ERROR} (credit-lane policy unreadable: {error}); "
        f"model {model or '(none)'} is outside the built-in credit-period allowlist [{', '.join(allowed)}]. "
        "Dispatch an allowlisted model or another lane, and repair the policy file."
    )


def dispatch_refusal(lane: str, model: str | None, *, policy: CreditPolicy | None = None) -> str | None:
    """Refusal text when the credit-period allowlist applies to ``lane`` and ``model`` is off it, else None.

    ``model`` is the model the dispatch launches (the caller resolves the
    lane default first). The snapshot is read only for an off-allowlist model
    on a configured lane; an unreadable snapshot gives no evidence of a credit
    balance, so admission is unchanged from before the credit policy. The
    allowlist does not depend on the router recommending the lane. An
    unreadable policy restricts only :data:`DEFAULT_ALLOWED_MODELS` lanes.
    """
    lane_key = lane.strip().lower()
    if policy is None:
        try:
            policy = load_policy()
        except ValueError as exc:
            return _policy_error_refusal(lane_key, model, str(exc))
    if model_allowed(policy, lane_key, model):
        return None
    budget = read_routing_budget()
    if budget is None:
        return None
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    diagnostics = budget.get("diagnostics") if isinstance(budget.get("diagnostics"), dict) else {}
    state = lane_credit_state(lane_key, agents.get(lane_key), policy, snapshot_stale=bool(diagnostics.get("stale")))
    if not allowlist_applies(state):
        return None
    return refusal_text(lane_key, model, state, policy)
