"""Credit-period lane state, model allowlist and reset advice (#9518).

A lane whose plan allowance is nearly used can keep working on prepaid
credits. :func:`lane_credit_state` decides that from one routing-budget agent
record; :func:`dispatch_refusal` refuses a model outside the lane's
credit-period allowlist while the lane runs on credits; :func:`reset_advice`
says whether a free full reset is worth using now. The policy lives in
``scripts/config/credit_lanes.yaml``. Everything here reads snapshots only:
nothing consumes credits or resets.

Fail closed: a missing, stale or non-numeric credit balance, or runtime
headroom blocked by rate limits, keeps the lane in its plan state
(near_cap/AVOID as before), never ``credit_backed``.
"""

from __future__ import annotations

import json
import math
import os
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

NOT_CONFIGURED = "not_configured"
PLAN_UNKNOWN = "plan_unknown"
PLAN_HEALTHY = "plan_healthy"
CREDIT_BACKED = "credit_backed"
CREDITS_EXHAUSTED = "credits_exhausted"
CREDITS_UNVERIFIED = "credits_unverified"

USE_RESET_NOW = "use_reset_now"
HOLD_RESET = "hold_reset"
NOT_APPLICABLE = "not_applicable"

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
    reset_hold_hours: float
    allowed_models: dict[str, tuple[str, ...]]
    path: Path

    def lane_models(self, lane: str) -> tuple[str, ...] | None:
        return self.allowed_models.get(lane.strip().lower())


def _positive_number(value: Any, name: str, path: Path) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{path}: {name} must be a non-negative number, got {value!r}")
    return float(value)


def load_policy(path: Path = POLICY_PATH) -> CreditPolicy:
    """Read and validate the credit-period policy; a malformed file raises ``ValueError``."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"{path}: cannot read credit-lane policy: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{path}: expected schema_version {SCHEMA_VERSION}")
    lanes = payload.get("lanes")
    if not isinstance(lanes, dict):
        raise ValueError(f"{path}: lanes must be a mapping")
    allowed: dict[str, tuple[str, ...]] = {}
    for lane, entry in lanes.items():
        models = entry.get("allowed_models") if isinstance(entry, dict) else None
        if not isinstance(models, list) or not models or not all(isinstance(m, str) and m.strip() for m in models):
            raise ValueError(f"{path}: lanes.{lane}.allowed_models must be a non-empty list of model ids")
        allowed[str(lane).strip().lower()] = tuple(m.strip() for m in models)
    return CreditPolicy(
        near_cap_remaining_pct=_positive_number(payload.get("near_cap_remaining_pct"), "near_cap_remaining_pct", path),
        credit_max_age_s=_positive_number(payload.get("credit_max_age_s"), "credit_max_age_s", path),
        reset_hold_hours=_positive_number(payload.get("reset_hold_hours"), "reset_hold_hours", path),
        allowed_models=allowed,
        path=path,
    )


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


def _parse_time(value: Any) -> datetime | None:
    """ISO-8601 text or epoch seconds/milliseconds as an aware UTC datetime."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        seconds = float(value) / 1000.0 if value > 1e12 else float(value)
        try:
            return datetime.fromtimestamp(seconds, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    return None


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


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


def lane_credit_state(
    lane: str,
    info: dict[str, Any] | None,
    policy: CreditPolicy,
    *,
    snapshot_stale: bool = False,
) -> dict[str, Any]:
    """Credit state of one routing-budget lane record; see the module docstring for fail-closed rules."""
    models = policy.lane_models(lane)
    if models is None:
        return {"state": NOT_CONFIGURED}
    record = info if isinstance(info, dict) else {}
    remaining = plan_remaining_pct(record)
    result: dict[str, Any] = {
        "plan_remaining_pct": remaining,
        "near_cap_remaining_pct": policy.near_cap_remaining_pct,
        "credit_balance": None,
        "allowed_models": list(models),
    }
    if remaining is None:
        return {**result, "state": PLAN_UNKNOWN, "reason": "plan allowance unknown"}
    if remaining > policy.near_cap_remaining_pct:
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
    result["credit_balance"] = balance
    if balance <= 0:
        return {**result, "state": CREDITS_EXHAUSTED, "reason": f"credit balance {balance:g}"}
    runtime = record.get("runtime") if isinstance(record.get("runtime"), dict) else {}
    if runtime.get("headroom_blocked") is True:
        # Rate limits despite a positive balance: the credits are not backing calls now.
        return {**result, "state": CREDITS_UNVERIFIED, "reason": "runtime headroom blocked by recent rate limits"}
    return {
        **result,
        "state": CREDIT_BACKED,
        "reason": f"plan remaining {remaining:g}% at or below {policy.near_cap_remaining_pct:g}%; "
        f"fresh credit balance {balance:g}",
        "coverage": {"dispatches": None, "basis": COVERAGE_BASIS},
    }


def _natural_reset(info: dict[str, Any]) -> datetime | None:
    native = info.get("codexbar") if isinstance(info.get("codexbar"), dict) else {}
    windows = native.get("windows") if isinstance(native.get("windows"), dict) else {}
    secondary = windows.get("secondary") if isinstance(windows.get("secondary"), dict) else {}
    for value in (native.get("weekly_resets_at"), secondary.get("resets_at"), info.get("resets_at")):
        parsed = _parse_time(value)
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
    fetched_at = _parse_time(inventory.get("fetched_at"))
    if (
        isinstance(count, bool)
        or not isinstance(count, int)
        or count < 0
        or not isinstance(expirations, list)
        or fetched_at is None
        or not 0 <= (now - fetched_at).total_seconds() < policy.credit_max_age_s
    ):
        return None
    live: list[datetime | None] = []
    for value in expirations:
        expiry = _parse_time(value)
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
    state = lane_credit_state(lane, info, policy, snapshot_stale=snapshot_stale)
    if state["state"] == NOT_CONFIGURED:
        return state
    return {
        **state,
        "reset_advice": reset_advice(lane, info, policy, state["state"], now=now, snapshot_stale=snapshot_stale),
    }


def model_allowed(policy: CreditPolicy, lane: str, model: str | None) -> bool:
    """True when ``model`` (catalog-canonicalised) is on ``lane``'s credit-period allowlist."""
    allowed = policy.lane_models(lane)
    if allowed is None:
        return True
    if not model:
        return False
    from scripts.review.model_catalog import canonical_model_id

    canonical = canonical_model_id(model) or model.strip().lower()
    return canonical in allowed


def refusal_text(lane: str, model: str | None, state: dict[str, Any], policy: CreditPolicy) -> str:
    return (
        f"{REFUSAL_CODE}: lane {lane} is {state['state']} ({state.get('reason')}); model {model or '(none)'} "
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


def dispatch_refusal(lane: str, model: str | None, *, policy: CreditPolicy | None = None) -> str | None:
    """Refusal text when ``lane`` is credit-backed and ``model`` is off its allowlist, else None.

    ``model`` is the model the dispatch launches (the caller resolves the
    lane default first). The snapshot is read only for an off-allowlist model
    on a configured lane; an unreadable snapshot leaves the lane in its plan
    state, so admission is unchanged from before the credit policy.
    """
    active = policy or load_policy()
    lane_key = lane.strip().lower()
    if model_allowed(active, lane_key, model):
        return None
    budget = read_routing_budget()
    if budget is None:
        return None
    agents = budget.get("agents") if isinstance(budget.get("agents"), dict) else {}
    diagnostics = budget.get("diagnostics") if isinstance(budget.get("diagnostics"), dict) else {}
    state = lane_credit_state(lane_key, agents.get(lane_key), active, snapshot_stale=bool(diagnostics.get("stale")))
    if state["state"] != CREDIT_BACKED:
        return None
    return refusal_text(lane_key, model, state, active)
