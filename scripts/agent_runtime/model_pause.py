"""Operator model pauses and plan-headroom stops for new dispatches.

The operator policy lives in ``~/.config/learn-ukrainian/model-pause.json``
(override with ``LU_MODEL_PAUSE_FILE``). It applies to NEW dispatches and
review selections only; running work is never touched.

    {
      "pauses": [
        {"pattern": "claude-opus-*", "until": "2026-10-12T07:00:00Z",
         "reason": "operator: no Opus until the weekly reset"}
      ],
      "headroom": [
        {"lane": "claude", "pattern": "claude-*", "max_weekly_used_pct": 87}
      ]
    }

``pauses``: a model matching ``pattern`` (fnmatch, on the requested id and its
catalog id) is refused until ``until`` (explicit-UTC ISO). After that time the
entry is inert, so the pause lifts by itself at the reset.

``headroom``: a model matching ``pattern`` is refused while the lane's weekly
plan usage (routing-budget) is at or above ``max_weekly_used_pct``. Unreadable
usage does not block (a warning is the caller's to log); a missing or invalid
policy file means no pauses.
"""

from __future__ import annotations

import fnmatch
import http.client
import json
import os
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused

DEFAULT_POLICY = Path("~/.config/learn-ukrainian/model-pause.json")


class ModelPausedRefused(MechanicalAdmissionRefused):
    """A requested model is paused by operator policy or out of plan headroom."""


def policy_path() -> Path:
    return Path(os.environ.get("LU_MODEL_PAUSE_FILE") or DEFAULT_POLICY).expanduser()


def load_policy(path: Path | None = None) -> dict[str, Any]:
    try:
        data = json.loads((path or policy_path()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(None):
        return None
    return parsed


_NATIVE_CLAUDE_ALIASES = ("opus", "sonnet", "haiku", "fable")


def _names(model: str) -> set[str]:
    names = {model}
    # Native Claude aliases ("opus", "sonnet[1m]") run that family's current
    # model: match them as such, so a family pause cannot be sidestepped.
    family = model.strip().lower().split("[", 1)[0]
    if family in _NATIVE_CLAUDE_ALIASES:
        names.add(f"claude-{family}-latest")
    try:
        from scripts.review.model_catalog import canonical_model_id

        canonical = canonical_model_id(model)
        if canonical:
            names.add(str(canonical))
    except Exception:  # an unknown id is matched as given
        pass
    return names


def _matches(pattern: str, model: str) -> bool:
    return any(fnmatch.fnmatchcase(name, pattern) for name in _names(model))


def _entries(policy: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    """The mapping entries of ``policy[key]``; any other shape is inert."""
    value = policy.get(key) if isinstance(policy, Mapping) else None
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, Mapping)]


def active_pause(model: str | None, policy: Mapping[str, Any], now: datetime) -> dict[str, Any] | None:
    if not model:
        return None
    for entry in _entries(policy, "pauses"):
        if not isinstance(entry.get("pattern"), str):
            continue
        until = _utc(entry.get("until"))
        if until is None or now >= until:
            continue
        if _matches(entry["pattern"], model):
            return dict(entry)
    return None


def _monitor_base() -> str:
    """The Monitor base URL: DELEGATE_MONITOR_API, else the bridge client's default."""
    from scripts.ai_agent_bridge.monitor_client import DEFAULT_BASE_URL

    return (os.environ.get("DELEGATE_MONITOR_API") or DEFAULT_BASE_URL).rstrip("/")


def routing_budget_used_pct(lane: str) -> float | None:
    """Weekly plan usage for ``lane`` from the Monitor routing-budget, or None."""
    base = _monitor_base()
    try:
        with urllib.request.urlopen(f"{base}/api/state/routing-budget", timeout=3) as resp:
            data = json.load(resp)
    except (OSError, ValueError, http.client.HTTPException):
        return None  # unreachable, unreadable or truncated: no usable reading
    if not isinstance(data, dict):
        return None
    agents = data.get("agents")
    info = agents.get(lane) if isinstance(agents, dict) else None
    if not isinstance(info, dict) or info.get("status") == "unknown":
        return None  # missing, or withdrawn as stale by Monitor
    codexbar = info.get("codexbar")
    if not isinstance(codexbar, dict):
        return None
    if codexbar.get("stale") is not False or codexbar.get("freshness") != "fresh":
        return None  # only a fresh probe reading may block a dispatch
    value = codexbar.get("weekly_used_pct")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def headroom_stop(
    model: str | None,
    policy: Mapping[str, Any],
    used_pct: Callable[[str], float | None] = routing_budget_used_pct,
) -> dict[str, Any] | None:
    if not model:
        return None
    for entry in _entries(policy, "headroom"):
        lane, pattern, cap = entry.get("lane"), entry.get("pattern"), entry.get("max_weekly_used_pct")
        if not (isinstance(lane, str) and isinstance(pattern, str) and isinstance(cap, int | float)):
            continue
        if not _matches(pattern, model):
            continue
        used = used_pct(lane)
        if used is not None and used >= float(cap):
            return {**entry, "used_pct": used}
    return None


def refusal_reason(
    model: str | None,
    *,
    policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    used_pct: Callable[[str], float | None] = routing_budget_used_pct,
) -> str | None:
    policy = load_policy() if policy is None else policy
    if not policy or not model:
        return None
    now = now or datetime.now(UTC)
    # Public-safe codes only: reasons, times and usage stay in the private policy.
    if active_pause(model, policy, now):
        return f"MODEL_PAUSED: {model} is paused by operator policy"
    if headroom_stop(model, policy, used_pct):
        return f"MODEL_HEADROOM: {model} is held for plan headroom"
    return None


def refuse_paused_models(
    models: Iterable[str | None],
    *,
    policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    used_pct: Callable[[str], float | None] = routing_budget_used_pct,
) -> None:
    """Raise ``ModelPausedRefused`` for the first paused or out-of-headroom model."""
    wanted = [m for m in models if m]
    if not wanted:
        return
    policy = load_policy() if policy is None else policy
    if not policy:
        return
    for model in wanted:
        reason = refusal_reason(model, policy=policy, now=now, used_pct=used_pct)
        if reason:
            raise ModelPausedRefused(reason)
