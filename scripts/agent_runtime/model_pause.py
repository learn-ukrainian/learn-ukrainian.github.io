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
plan usage (routing-budget) is at or above ``max_weekly_used_pct``. The
``claude`` lane's usage is the meter of the account the claude seat runs as,
which every reader names (``account_used_pct``, #10619, #10630). An AGY seat
also stops ``claude-*`` models on ``agents.gemini.claude_gpt_windows`` (the
five-hour window and the weekly window). Unknown or stale usage refuses
models matching a headroom entry; a missing or invalid policy file means no
pauses.
"""

from __future__ import annotations

import fnmatch
import functools
import http.client
import json
import math
import os
import re
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from scripts.agent_runtime.mechanical_admission import MechanicalAdmissionRefused
from scripts.orchestration.task_record_store import REVIEW_TASK_FLAG_FIELDS

if TYPE_CHECKING:
    from scripts.fleet.claude_account_lane import ClaudeAccount

DEFAULT_POLICY = Path("~/.config/learn-ukrainian/model-pause.json")


class ModelPausedRefused(MechanicalAdmissionRefused):
    """A requested model is paused by operator policy or out of plan headroom."""


class ModelRoleRefused(ModelPausedRefused):
    """A role ban, unpaired trial or invalid CTO role policy refused admission."""


def role_policy_path() -> Path:
    return Path(os.environ.get("LU_MODEL_ROLES_FILE") or policy_path().with_name("model-roles.json")).expanduser()


def normalize_role(role: str) -> str:
    value = role.strip().lower()
    return {
        "implementation": "authoring", "author": "authoring", "coding": "authoring",
        "driver": "driving", "orchestration": "driving", "orchestrator": "driving",
        "advisory": "advice", "advisor": "advice", "consult": "advice",
        "reviewer": "review", "critique": "review",
    }.get(value, value)


def dispatch_roles(record: Mapping[str, Any], *, review: bool = False) -> frozenset[str]:
    """Infer activity as well as keeping the explicitly named role."""
    roles = {normalize_role(str(record["research_role"]))} if record.get("research_role") else set()
    if review or record.get("type") == "review" or any(record.get(field) for field in (
        *REVIEW_TASK_FLAG_FIELDS, "review_mode", "risk", "language_lane", "subject_seat", "subject_family",
        "review_subject_seats", "review_subject_families",
    )):
        roles.add("review")
    if record.get("advisory_role"):
        roles.add("advice")
    if record.get("mode") == "workspace-write":
        roles.add("authoring")
    return frozenset(roles)


def load_role_policy(path: Path | None = None) -> dict[str, Any]:
    """Missing means no role controls; unreadable or malformed fails closed."""
    try:
        raw = (path or role_policy_path()).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"bans": [], "trials": []}
    except OSError:
        raise ModelRoleRefused("MODEL_ROLE_POLICY_INVALID: role policy cannot be read") from None
    try:
        return _validate_role_policy(json.loads(raw))
    except (OSError, ValueError, TypeError, KeyError):
        raise ModelRoleRefused("MODEL_ROLE_POLICY_INVALID: role policy cannot be validated") from None


def _validate_role_policy(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != {"bans", "trials"}:
        raise ValueError("invalid role policy")
    for kind in ("bans", "trials"):
        if not isinstance(data[kind], list):
            raise ValueError("invalid role entries")
        for entry in data[kind]:
            _validate_role_entry(entry)
    return data


def _validate_role_entry(entry: Any) -> None:
    from scripts.review.model_catalog import canonical_model_id

    if not isinstance(entry, dict):
        raise ValueError("invalid role entry")
    for key in ("model", "reason", "decided_by"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise ValueError("missing role decision field")
    if any(char in entry["model"] for char in "*?[]"):
        raise ValueError("role decisions name concrete models")
    if canonical_model_id(entry["model"]) != entry["model"]:
        raise ValueError("role decisions name concrete catalog identities")
    roles = entry.get("roles")
    if not isinstance(roles, list) or not roles or any(
        not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9_-]*", role) for role in roles
    ):
        raise ValueError("invalid roles")
    start, review = _utc(entry.get("start")), _utc(entry.get("review_date"))
    if start is None or review is None or start >= review:
        raise ValueError("invalid role decision dates")
    evidence = entry.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("missing dispatch evidence")
    begin, end = _utc(evidence.get("window_start")), _utc(evidence.get("window_end"))
    if begin is None or end is None or begin > end or end > start:
        raise ValueError("invalid evidence window")
    runs = evidence.get("dispatch_records")
    if not isinstance(runs, list):
        raise ValueError("missing dispatch records")
    for run in runs:
        if not isinstance(run, dict) or not isinstance(run.get("task_id"), str) or not run["task_id"]:
            raise ValueError("invalid dispatch reference")
        if run["task_id"] not in entry["reason"]:
            raise ValueError("reason must cite dispatch records")
        if run.get("status") not in {
            "done", "failed", "timeout", "rate_limited", "cancelled", "crashed", "no_deliverable",
        }:
            raise ValueError("invalid dispatch status")
        duration = run.get("duration_s")
        if isinstance(duration, bool) or not isinstance(duration, int | float) or not math.isfinite(duration) or duration < 0:
            raise ValueError("invalid dispatch duration")
        if run.get("timeout_source") not in {"caller", "watchdog", "provider", "none", "unknown"}:
            raise ValueError("missing timeout source")
        if not isinstance(run.get("cause"), str) or not run["cause"].strip():
            raise ValueError("missing dispatch cause")
        if not isinstance(run.get("model_failure"), bool):
            raise ValueError("missing failure attribution")
        if run["model_failure"] and run["timeout_source"] in {"caller", "unknown"}:
            raise ValueError("caller limits and unknown causes do not establish model failure")
        recorded = role_dispatch_evidence(run["task_id"])
        if any(run.get(key) != recorded[key] for key in recorded):
            raise ValueError("dispatch evidence differs from its record")
        from scripts.dispatcher import store

        task = store.read(run["task_id"])
        started = _utc(task.get("started_at"))
        if (not _names(entry["model"]).intersection(_names(str(task.get("model") or "")))
                or started is None or not begin <= started <= end):
            raise ValueError("dispatch evidence is outside this model's window")


def role_dispatch_evidence(task_id: str) -> dict[str, Any]:
    """Build evidence from the canonical dispatch record, including archived runs."""
    from scripts.dispatcher import store

    task = store.read(task_id)
    source = "none"
    if task.get("status") == "timeout":
        source = {"hard_timeout": "caller", "stdout_silence_timeout": "watchdog",
                  "initial_response_timeout": "watchdog"}.get(task.get("kill_reason"), "unknown")
        if task.get("error") == "process deadline exceeded":
            source = "caller"
    elif task.get("status") == "cancelled":
        source = "caller"
    return {"task_id": task_id, "status": task.get("status"), "duration_s": task.get("duration_s"),
            "timeout_source": source, "cause": task.get("error") or str(task.get("status"))}


def role_refusal_reason(
    model: str | None, roles: Iterable[str], *, policy: Mapping[str, Any] | None = None,
    now: datetime | None = None, shadow: bool = False,
) -> str | None:
    """Role controls only restrict; a shadow never acquires gate authority."""
    try:
        policy = load_role_policy() if policy is None else _validate_role_policy(policy)
    except (OSError, ModelRoleRefused, ValueError, TypeError, KeyError):
        return "MODEL_ROLE_POLICY_INVALID: role policy cannot be validated"
    now = now or datetime.now(UTC)
    wanted = {normalize_role(role) for role in roles}
    for kind in ("bans", "trials"):
        for entry in policy[kind]:
            if (model and _names(model).intersection(_names(entry["model"]))
                    and _utc(entry["start"]) <= now < _utc(entry["review_date"])):
                if not wanted:
                    return f"MODEL_ROLE_REQUIRED: {model} needs an explicit dispatch role"
                matching = wanted.intersection(normalize_role(role) for role in entry["roles"])
                if matching and (kind == "bans" or not shadow):
                    code = "MODEL_ROLE_BANNED" if kind == "bans" else "MODEL_ROLE_TRIAL_SHADOW_REQUIRED"
                    return f"{code}: {model} is restricted for {','.join(sorted(matching))}"
    return None


def refuse_model_roles(model: str | None, roles: Iterable[str], *, shadow: bool = False) -> None:
    if reason := role_refusal_reason(model, roles, shadow=shadow):
        raise ModelRoleRefused(reason)


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


def _newest_claude(family: str) -> str | None:
    """The concrete model a native Claude alias runs: the newest catalog id of that family."""
    try:
        from scripts.review.model_catalog import load_model_catalog

        models = load_model_catalog().get("models") or {}
    except Exception:  # no catalog: the alias is matched by family name only
        return None
    prefix = f"claude-{family}-"

    def version(model_id: str) -> tuple[int, ...]:
        return tuple(int(part) for part in model_id[len(prefix) :].split("-") if part.isdigit())

    ids = [
        mid
        for mid, info in models.items()
        if isinstance(mid, str)
        and mid.startswith(prefix)
        and isinstance(info, dict)
        and info.get("family") == "anthropic"
    ]
    return max(ids, key=version) if ids else None


def _names(model: str) -> set[str]:
    names = {model}
    # Native Claude aliases ("opus", "sonnet[1m]") run that family's current
    # model: match them as such, so a family pause cannot be sidestepped.
    family = model.strip().lower().split("[", 1)[0]
    if family in _NATIVE_CLAUDE_ALIASES:
        names.add(f"claude-{family}-latest")
        concrete = _newest_claude(family)
        if concrete:
            names.add(concrete)
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


# AGY publishes on the gemini lane. Claude models on that seat draw
# claude_gpt_windows, not Gemini's own weekly percent and not the native plan.
AGY_CLAUDE_WINDOW_LANE = "agy_claude"
_AGY_CLAUDE_PROBE_LANE = "gemini"
_AGY_CLAUDE_WINDOW_KEYS = ("five_hour", "weekly")
_AGY_CLAUDE_WINDOW_CAP = 100


def _fresh_probe_record(info: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """The lane's codexbar block when the probe is fresh, else None.

    Missing, unknown, stale, or any freshness other than fresh is not a usable
    meter. This is the same rule as the weekly plan reading.
    """
    if not info or info.get("status") == "unknown":
        return None
    codexbar = info.get("codexbar")
    if not isinstance(codexbar, Mapping):
        return None
    if codexbar.get("stale") is not False or codexbar.get("freshness") != "fresh":
        return None
    return codexbar


def _finite_pct(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _window_used_pct(block: object) -> float | None:
    """Used percent for one window, or None when that window has no fresh number.

    A remaining percent at or below zero is exhaustion. A present ``used_pct``
    that is not a finite number makes the window unusable; remaining does not
    replace it. A present freshness value other than the string ``fresh`` does
    the same. A window that carries its own stale flag uses the fresh-probe rule.
    """
    if not isinstance(block, Mapping):
        return None
    if block.get("stale") is True:
        return None
    if "freshness" in block and block.get("freshness") != "fresh":
        return None
    remaining = _finite_pct(block.get("remaining_pct"))
    if "used_pct" in block:
        used = _finite_pct(block.get("used_pct"))
        if used is None:
            return None
        if remaining is not None and remaining <= 0:
            return 100.0
        return used
    if remaining is None:
        return None
    if remaining <= 0:
        return 100.0
    return 100.0 - remaining


def _agy_claude_windows_used_pct(view: Mapping[str, Any]) -> float | None:
    """The stricter fresh AGY Claude window, or None when the reading is unusable.

    Both the five-hour window and the weekly window must be fresh numbers.
    The headroom stop then compares that used percent with its cap.
    """
    from scripts.fleet import claude_account_lane

    info = claude_account_lane.other_lane_record(view, _AGY_CLAUDE_PROBE_LANE)
    if _fresh_probe_record(info) is None:
        return None
    windows = info.get("claude_gpt_windows")
    if not isinstance(windows, Mapping):
        probe = info.get("codexbar")
        windows = probe.get("claude_gpt_windows") if isinstance(probe, Mapping) else None
    if not isinstance(windows, Mapping):
        return None
    readings = [_window_used_pct(windows.get(key)) for key in _AGY_CLAUDE_WINDOW_KEYS]
    if any(reading is None for reading in readings):
        return None
    return max(readings)


def _bound_routing_view(account: ClaudeAccount | None) -> Mapping[str, Any] | None:
    from scripts.fleet import claude_account_lane

    base = _monitor_base()
    try:
        with urllib.request.urlopen(f"{base}/api/state/routing-budget", timeout=3) as resp:
            data = json.load(resp)
    except (OSError, ValueError, http.client.HTTPException):
        return None  # unreachable, unreadable or truncated: no usable reading
    if not isinstance(data, dict):
        return None
    # Bound where it enters (#10770): the claude lane is only ever ``account``'s meter; with no account, none.
    return claude_account_lane.bind_snapshot(data, account=account or claude_account_lane.no_claude_account())


def routing_budget_used_pct(lane: str, *, account: ClaudeAccount | None) -> float | None:
    """Weekly plan usage for ``lane`` from the Monitor routing-budget, or None.

    ``account`` is required: the ``claude`` lane is that account's meter
    (``claude_account_lane.account_weekly_used_pct``), and None (no account
    named, for a structural check) reads the ``claude`` lane as unknown. Other
    lanes ignore it. ``agy_claude`` reads the fresh AGY Claude windows on the
    gemini lane. Only a fresh probe reading counts.
    """
    from scripts.fleet import claude_account_lane

    if account is not None:
        claude_account_lane.require_account(account)
    elif lane == "claude":
        return None
    view = _bound_routing_view(account)
    if view is None:
        return None
    if lane == "claude" and account is not None:
        return claude_account_lane.account_weekly_used_pct(view, account=account)
    if lane == AGY_CLAUDE_WINDOW_LANE:
        return _agy_claude_windows_used_pct(view)
    info = claude_account_lane.other_lane_record(view, lane)
    probe = _fresh_probe_record(info)
    if probe is None:
        return None
    value = probe.get("weekly_used_pct")
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def account_used_pct(account: ClaudeAccount | None) -> Callable[[str], float | None]:
    """The usage reader for work whose claude seat runs as ``account`` (#10619, #10630).

    Required: None names no account, so the claude lane then reads as unknown.
    """
    if account is not None:
        from scripts.fleet.claude_account_lane import require_account

        require_account(account)
    return functools.partial(routing_budget_used_pct, account=account)


def policy_for_seat(seat: str, *, review: bool = False, check_headroom: bool = True) -> dict[str, Any]:
    """Keep pauses and only the headroom entries that fund this seat.

    Review admission protects the native Claude plan only. An AGY seat also
    stops ``claude-*`` models on that seat's Claude windows. Structural
    qualification and checks of unselected models omit headroom explicitly.
    """
    policy = load_policy()
    headroom = [
        entry for entry in _entries(policy, "headroom")
        if check_headroom
        and (not review or entry.get("lane") == "claude")
        and (seat == "claude" or entry.get("lane") != "claude")
    ]
    if check_headroom and seat == "agy":
        headroom.append({
            "lane": AGY_CLAUDE_WINDOW_LANE,
            "pattern": "claude-*",
            "max_weekly_used_pct": _AGY_CLAUDE_WINDOW_CAP,
        })
    return {**policy, "headroom": headroom}


def headroom_stop(
    model: str | None,
    policy: Mapping[str, Any],
    used_pct: Callable[[str], float | None],
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
        if used is None or not math.isfinite(used) or not 0 <= used <= 100:
            return {**entry, "used_pct": None}
        if used >= float(cap):
            return {**entry, "used_pct": used}
    return None


def refusal_reason(
    model: str | None,
    *,
    policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    used_pct: Callable[[str], float | None],
) -> str | None:
    policy = load_policy() if policy is None else policy
    if not policy or not model:
        return None
    now = now or datetime.now(UTC)
    # Public-safe codes only: reasons, times and usage stay in the private policy.
    if active_pause(model, policy, now):
        return f"MODEL_PAUSED: {model} is paused by operator policy"
    stop = headroom_stop(model, policy, used_pct)
    if stop is not None and stop["used_pct"] is None:
        return f"MODEL_HEADROOM_USAGE_UNKNOWN: {model} has no fresh plan usage reading"
    if stop is not None:
        return f"MODEL_HEADROOM: {model} is held for plan headroom"
    return None


def refuse_paused_models(
    models: Iterable[str | None],
    *,
    policy: Mapping[str, Any] | None = None,
    now: datetime | None = None,
    used_pct: Callable[[str], float | None],
) -> None:
    """Raise ``ModelPausedRefused`` for the first paused or out-of-headroom model.

    ``used_pct`` is required: :func:`account_used_pct` of the account the work's claude seat runs as.
    """
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
