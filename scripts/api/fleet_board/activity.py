"""Seat state from snapshots and occupancy records.

Liveness is the roster or fresh harness process flag. Delegate collection
reports source health only: task rows have no approved seat identity binding.
Screen text is never an input. A missing number stays None.
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from typing import Any

from scripts.api.delegate_router import seat_delegate_tasks
from scripts.api.epics_router import _response_registry_text
from scripts.api.occupancy import occupancy_payload

from .snapshot import finite_number, mapping
from .sources import SourceReport, report

STATES = frozenset({"working", "idle", "stuck", "dead", "paused", "off"})
STUCK_IDLE_MIN = 30.0
ACTIVITY_TOKENS = frozenset({"working", "idle"})
PUBLIC_REDACTED = "[redacted]"
# Prose and enum tokens: letters, digits, spaces, underscores and light punctuation,
# including Ukrainian apostrophes, quotes, guillemets and stress marks.
# Everything else (slashes, percent signs, at signs, symbols, emoji) fails closed.
_PUBLIC_SHAPE_RE = re.compile(
    r"(?:[^\W_]|[ _.,:;'\"\u2019\u201c\u201d\u02bc\u00ab\u00bb\u2013\u2014()#!?\-\u0301])+"
)
# Word edges where an underscore separates words, so "ssh_key" and "build_box" match.
_EDGE_L = r"(?<![^\W_])"
_EDGE_R = r"(?![^\W_])"
# Capacity figures: a number with a unit, or a capacity word.
_PUBLIC_CAPACITY_RE = re.compile(
    rf"(?i)\d[\d.,]*\s*(?:%|pct{_EDGE_R}|percent{_EDGE_R}|slots?{_EDGE_R}|seats?{_EDGE_R}"
    rf"|tokens?{_EDGE_R}|requests?{_EDGE_R}|rpm{_EDGE_R}|tpm{_EDGE_R}|[kmgt]i?b{_EDGE_R}|bytes?{_EDGE_R})"
    rf"|{_EDGE_L}(?:capacity|quota|budget|headroom|ceiling|hard[ _-]stop|rate[ _-]limit){_EDGE_R}"
    rf"|{_EDGE_L}\d+\s+of\s+\d+{_EDGE_R}"
)
# Security mechanisms: auth, keys, network controls, privilege.
_PUBLIC_SECURITY_RE = re.compile(
    rf"(?i){_EDGE_L}(?:2fa|mfa|otp|totp|oauth2?|saml|sso|kerberos|ldap|tls|ssl|certs?|certificates?"
    rf"|passphrases?|passwords?|credentials?|keychain|cookies?|sudo|sshd?|authorized[_ ]keys|pubkeys?"
    rf"|private[_ -]keys?|hmac|csrf|cors|firewalls?|iptables|ufw|selinux|apparmor|fail2ban|vpn"
    rf"|wireguard|allow ?lists?|white ?lists?|block ?lists?|deny ?lists?|api[_ -]?keys?"
    rf"|session[_ -]?tokens?|bearer|root (?:access|login|shell)){_EDGE_R}"
)
# Machine names: host words, or a letter run glued to a digit (buildbox7, gpu01).
# Hyphenated agent ids such as driver-kept or worker-2 stay publishable.
_PUBLIC_HOST_RE = re.compile(
    rf"(?i){_EDGE_L}(?:hostname|host|server|machine|localhost|vps|nas|laptop|workstation|desktop|box|runner)s?{_EDGE_R}"
    r"|[a-z]{3,}\d"
)


def load_delegate_health() -> SourceReport:
    """Report collector health without interpreting unbound task identities."""
    try:
        payload = seat_delegate_tasks()
    except Exception:
        return report("delegate", "unavailable")
    return report("delegate", "ok" if isinstance(payload, dict) else "unavailable")


def _occupant_activity(status: object) -> str | None:
    """Explicit activity only. Presence without a status is not working."""
    if not isinstance(status, str):
        return None
    token = status.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


def _observation_age(host: Mapping[str, Any]) -> float | None:
    age = host.get("age_seconds")
    if isinstance(age, bool) or not isinstance(age, (int, float)):
        return None
    try:
        number = float(age)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(number) or number < 0:
        return None
    return number


def load_occupancy_activity() -> tuple[SourceReport, dict[str, str]]:
    """Working or idle per agent id. Host identity is not copied out.

    Only fresh hosts contribute explicit working/idle activity. With no fresh
    host, retained stale observations report ``stale``; otherwise failed
    observations report ``unavailable`` with unknown age. An empty valid host
    collection is ``ok`` with no activity.
    """
    try:
        payload = occupancy_payload()
    except Exception:
        return report("occupancy", "unavailable"), {}
    if not isinstance(payload, dict):
        return report("occupancy", "unavailable"), {}
    hosts = payload.get("hosts")
    if not isinstance(hosts, dict):
        return report("occupancy", "unavailable"), {}
    activity: dict[str, str] = {}
    saw_fresh = False
    saw_stale = False
    saw_unavailable = False
    stale_age: float | None = None
    for host in hosts.values():
        if not isinstance(host, dict):
            saw_unavailable = True
            continue
        status = host.get("status")
        if status == "stale":
            saw_stale = True
            age = _observation_age(host)
            if age is not None and (stale_age is None or age > stale_age):
                stale_age = age
            continue
        if status != "fresh":
            saw_unavailable = True
            continue
        saw_fresh = True
        occupants = host.get("occupants")
        if not isinstance(occupants, list):
            continue
        for occupant in occupants:
            if not isinstance(occupant, dict):
                continue
            agent = occupant.get("agent")
            if not isinstance(agent, str) or not agent.strip():
                continue
            token = _occupant_activity(occupant.get("status"))
            if token is None:
                continue
            agent_id = agent.strip()
            if activity.get(agent_id) == "working":
                continue
            activity[agent_id] = token
    if saw_stale and not saw_fresh:
        return report("occupancy", "stale", age_s=stale_age), {}
    if saw_unavailable and not saw_fresh:
        return report("occupancy", "unavailable"), {}
    return report("occupancy", "ok"), activity


def activity_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


def _publishable(projected: str) -> bool:
    if not _PUBLIC_SHAPE_RE.fullmatch(projected):
        return False
    return not any(
        pattern.search(projected)
        for pattern in (_PUBLIC_CAPACITY_RE, _PUBLIC_SECURITY_RE, _PUBLIC_HOST_RE)
    )


def text(value: object) -> str | None:
    """Project one emitted string through the publication text boundary.

    The epic-registry bound runs first. Then only prose shapes pass, and no
    capacity figure, machine name, or security-mechanism detail. Anything
    else becomes ``[redacted]``.
    """
    if not isinstance(value, str):
        return None
    projected = _response_registry_text(value)
    if projected is None or projected == PUBLIC_REDACTED:
        return projected
    if _publishable(projected):
        return projected
    return PUBLIC_REDACTED


def seat_id(value: object) -> str | None:
    """An identity string. A redacted value is omitted rather than published."""
    projected = text(value)
    if not projected or projected == PUBLIC_REDACTED:
        return None
    return projected


def derive_state(
    *,
    intended: str | None,
    pid_alive: bool | None,
    idle_min: float | None,
    activity: str | None,
    occupancy: str | None,
    seat_present: bool,
    require_liveness: bool,
) -> tuple[str, str]:
    """One of the six states, always with a reason."""
    norm = (intended or "").strip().lower()
    if norm in {"off", "postponed"}:
        reason = "postponed" if norm == "postponed" else "off by roster"
        return "off", reason
    if norm == "paused":
        return "paused", "paused by roster"
    if pid_alive is False:
        return "dead", "process is not alive"
    if not seat_present and norm == "running":
        return "stuck", "no driver while intended running"
    long_idle = idle_min is not None and idle_min >= STUCK_IDLE_MIN
    if norm == "running" and long_idle:
        return "stuck", "idle while intended running"
    if activity == "working" or occupancy == "working":
        return "working", "recorded working"
    if require_liveness and norm == "running" and pid_alive is None:
        return "stuck", "liveness unknown"
    return "idle", "idle"


def pr_stale_minutes(environ: Mapping[str, str] | None = None) -> float:
    """Minutes a green, approved, unqueued PR must exceed before it is flagged."""
    source = os.environ if environ is None else environ
    raw = source.get("FLEET_PR_STALE_MIN")
    if raw is None or not str(raw).strip():
        return 60.0
    try:
        value = float(str(raw).strip())
    except ValueError:
        return 60.0
    if not math.isfinite(value) or value < 0:
        return 60.0
    return value


def harness_row(snapshot: dict[str, Any] | None, agent_id: str) -> dict[str, Any]:
    if not snapshot:
        return {}
    agents = snapshot.get("agents")
    if isinstance(agents, dict):
        return mapping(agents.get(agent_id))
    if isinstance(agents, list):
        for item in agents:
            row = mapping(item)
            if row.get("agent_id") == agent_id:
                return row
    return {}


def resolve_pid(roster_pid: object, harness: Mapping[str, Any]) -> bool | None:
    """Process flag. A harness bool wins. Anything else stays unknown."""
    if "pid_alive" in harness and isinstance(harness.get("pid_alive"), bool):
        return harness.get("pid_alive")
    if isinstance(roster_pid, bool):
        return roster_pid
    return None


def resolve_idle_min(roster: Mapping[str, Any], harness: Mapping[str, Any]) -> float | None:
    if "idle_min" in harness:
        h_idle = finite_number(harness.get("idle_min"))
        if h_idle is not None:
            return h_idle
    if "idle_min" in roster:
        return finite_number(roster.get("idle_min"))
    return None


def resolve_activity(roster: Mapping[str, Any], harness: Mapping[str, Any]) -> str | None:
    if "activity" in harness:
        h_act = activity_token(harness.get("activity"))
        if h_act is not None:
            return h_act
    if "activity" in roster:
        return activity_token(roster.get("activity"))
    return None
