"""Seat state from snapshots and occupancy records.

Liveness is the roster or fresh harness process flag. Delegate collection
reports source health only: task rows have no approved seat identity binding.
Screen text is never an input. A missing number stays None.
"""

from __future__ import annotations

import math
import os
import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from scripts.api.delegate_router import seat_delegate_tasks
from scripts.api.epics_router import _response_registry_text
from scripts.api.occupancy import occupancy_payload
from scripts.api.occupancy_sanitize import producer_identity

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
# The same punctuation the prose shape allows. A figure cannot hide behind it.
_PUBLIC_SEP = r"[ _.,:;'\"\u2019\u201c\u201d\u02bc\u00ab\u00bb\u2013\u2014()#!?\-]*"
_PUBLIC_UNIT = (
    rf"(?:%|pct{_EDGE_R}|per{_PUBLIC_SEP}cent(?:ages?|iles?)?{_EDGE_R}"
    rf"|slots?{_EDGE_R}|seats?{_EDGE_R}|tokens?{_EDGE_R}|requests?{_EDGE_R}"
    rf"|(?:rpm|tpm|qps|rps|cps){_EDGE_R}"
    rf"|(?:[kmgt]i?b(?:it|ps)?s?|(?:г|к|м|т)б|(?:giga|mega|kilo|tera)?{_PUBLIC_SEP}bits?"
    rf"|(?:giga|mega|kilo|tera|гіга|мега|кіло|тера)?{_PUBLIC_SEP}байт[^\W_]*"
    rf"|(?:giga|mega|kilo|tera)?{_PUBLIC_SEP}bytes?){_EDGE_R})"
)
# Capacity figures: a number with a unit, a capacity word, or a counted ratio.
_PUBLIC_CAPACITY_RE = re.compile(
    rf"(?i)\d[\d.,]*{_PUBLIC_SEP}{_PUBLIC_UNIT}"
    rf"|{_EDGE_L}(?:capacity|quota|budget|headroom|ceiling|instances?|users?"
    rf"|hard{_PUBLIC_SEP}stop|rate{_PUBLIC_SEP}limit){_EDGE_R}"
    rf"|{_EDGE_L}\d+{_PUBLIC_SEP}of{_PUBLIC_SEP}\d+{_EDGE_R}"
)
# Security mechanisms: auth, keys, network controls, privilege.
_PUBLIC_SECURITY_RE = re.compile(
    rf"(?i){_EDGE_L}(?:2fa|mfa|otp|totp|oauth2?|saml|sso|kerberos|ldap|tls|ssl|certs?|certificates?"
    rf"|passphrases?|passwords?|credentials?|keychain|cookies?|sudo|sshd?|authorized[_ ]keys|pubkeys?"
    rf"|private[_ -]keys?|hmac|csrf|cors|firewalls?|iptables|ufw|selinux|apparmor|fail2ban|vpn"
    rf"|wireguard|allow ?lists?|white ?lists?|block ?lists?|deny ?lists?|api[_ -]?keys?"
    rf"|session[_ -]?tokens?|bearer|jwts?|rbac|admins?|secrets?|id_(?:rsa|ed25519)|root (?:access|login|shell)){_EDGE_R}"
)
# Match complete numbered labels, including hyphenated ones. Known technical
# terms and numbered seat labels remain publishable; substrings never match.
_PUBLIC_HOST_RE = re.compile(
    rf"(?i){_EDGE_L}(?:hostname|host|server|machine|localhost|vps|nas|laptop|workstation|desktop|box|runner)s?{_EDGE_R}"
    rf"|{_EDGE_L}(?<!-)(?!(?:gpt[4]|ipv4|utf8|base64|html5|(?:driver|worker)-\d+){_EDGE_R}(?!-))"
    rf"[a-z]{{2,}}(?:-[a-z]+)*-?\d+{_EDGE_R}(?!-)"
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


def load_occupancy_activity() -> tuple[SourceReport, dict[tuple[str, str], str]]:
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
    candidates: dict[tuple[str, str], list[str | None]] = {}
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
            agent = producer_identity(occupant.get("agent"))
            session = producer_identity(occupant.get("session_id"))
            instance = producer_identity(occupant.get("instance_id"))
            if occupant.get("kind") != "observer" or not agent or not session or not instance:
                continue
            token = _occupant_activity(occupant.get("status"))
            candidates.setdefault((agent, session), []).append(token)
    if saw_stale and not saw_fresh:
        return report("occupancy", "stale", age_s=stale_age), {}
    if saw_unavailable and not saw_fresh:
        return report("occupancy", "unavailable"), {}
    activity = {key: tokens[0] for key, tokens in candidates.items()
                if len(tokens) == 1 and tokens[0] is not None}
    return report("occupancy", "ok"), activity


def activity_token(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    token = value.strip().lower()
    if token in ACTIVITY_TOKENS:
        return token
    return None


# Confusable letters that would otherwise spell a denied Latin token.
_CONFUSABLE = str.maketrans({
    "\u0430": "a", "\u0410": "A",
    "\u0435": "e", "\u0415": "E",
    "\u043e": "o", "\u041e": "O",
    "\u0440": "p", "\u0420": "P",
    "\u0441": "c", "\u0421": "C",
    "\u0443": "y", "\u0423": "Y",
    "\u0445": "x", "\u0425": "X",
    "\u0456": "i", "\u0406": "I",
    "\u0455": "s", "\u0405": "S",
    "\u04cf": "l",
    "\u0412": "B",
    "\u0391": "A", "\u03b1": "a",
    "\u0395": "E", "\u03b5": "e",
    "\u0399": "I", "\u03b9": "i",
    "\u039f": "O", "\u03bf": "o",
    "\u03a1": "P", "\u03c1": "p",
})


def _screen(projected: str) -> str:
    """NFKC form with the stress mark removed. Cyrillic letters stay intact."""
    return unicodedata.normalize("NFKC", projected.replace("\u0301", ""))


def _fold(projected: str) -> str:
    """Accent-stripped, confusable-folded copy used only for denial."""
    decomposed = unicodedata.normalize("NFKD", projected)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFKC", stripped).translate(_CONFUSABLE)


def _publishable(projected: str) -> bool:
    if not _PUBLIC_SHAPE_RE.fullmatch(projected):
        return False
    screened = _screen(projected)
    folded = _fold(projected)
    copies = (screened, folded) if folded != screened else (screened,)
    return not any(
        pattern.search(copy)
        for copy in copies
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
    if require_liveness and norm == "running" and pid_alive is None:
        return "stuck", "liveness unknown"
    if activity == "working" or occupancy == "working":
        return "working", "recorded working"
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
