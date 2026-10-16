"""The Claude account is part of the route key (#10619, #10630).

A claude seat runs as one Claude account, so every decision about a claude
route is a decision about that account: the dispatch budget guard, reviewer
selection (dispatch admission and ``closeout_cli resolve-reviewer``) and the
plan-headroom stop (``scripts.agent_runtime.model_pause``). This module owns
that key and the only reads of the routing snapshot's claude meter:

- :class:`ClaudeAccount` is the account part of a route key. It is built only
  here: :func:`resolve_route_account` resolves and binds a dispatch's account
  before admission, :func:`account_from_record` reads a task record's, and
  :func:`no_claude_account` is the account of a route that reaches no claude seat.
- :func:`bind_snapshot` turns a raw routing-budget payload into an
  :class:`AccountSnapshot`: the snapshot a decision reads, holding one
  account's claude meter and no other account's (#10770). Decision consumers
  bind where a snapshot enters them; a decision helper that reaches the claude
  lane of an unbound snapshot raises :class:`AccountRequired`. Display
  consumers (``scripts.fleet.usage``, ``capacity_pick`` and the Monitor
  endpoint) keep the plain payload. A bound snapshot is deeply immutable, and
  its account identity survives conversion to a plain mapping
  (:data:`BINDING_KEY`): no derivation, copy or splice turns one account's
  meter into another's.
- :func:`select_account`, :func:`account_agents`, :func:`lane_record`,
  :func:`account_weekly_used_pct` and :func:`capacity_verdict` read the
  snapshot for a named account; none has a default, and a call without a
  ``ClaudeAccount`` raises ``TypeError``. :func:`other_lane_record` reads a
  lane no account owns and refuses the claude lane.

The routing-budget ``claude`` lane row is the Monitor host's default account
(``a``). Another account is read from its ``claude_accounts`` row instead. The
account view keeps the lane row's route facts, which no account owns
(``SHARED_ROUTE_FACT_KEYS``): spawn-phase lane health (one streak over every
account's claude tasks, so start-up, sandbox and CLI faults), route
eligibility, the route circuit, the review scheduler's concurrency state, and
the runtime outcome counts. It drops everything that is one account's meter:
the default account's usage windows, pace, credit, login and probe state, the
scheduler's quota reading (``SCHEDULER_QUOTA_FIELDS``), and the runtime
rate-limit evidence (``ACCOUNT_RATE_LIMIT_FIELDS``). A Claude rate limit is one
account's quota event, but runtime usage records carry no account label, so a
rate-limit cluster cannot be attributed to an account; it is reported as
unattributed evidence and never becomes another account's capacity verdict.
An unresolved account's meter reads as unknown, and no claude seat is
selected on it.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import secrets
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, NoReturn

CLAUDE_LANE = "claude"
# The reserved entry of a bound snapshot that carries a claude meter: its account label, evidence and
# meter seal. It survives ``dict(view)``, ``{**view}`` and a JSON round trip, so such a copy is bound
# again only unaltered and only as its own account (#10770).
BINDING_KEY = "claude_account_binding"
# The top-level fields that carry a Claude account's meter.
METER_FIELDS = frozenset({"agents", "claude_accounts", "ranked_by_headroom", "preferred_claude_account"})
# An ``agents`` key denoting a Claude seat's meter: ``claude``, a ``claude-<model>`` or other ``claude-<seat>``
# key, a ``claude:<account>`` key, or the ``anthropic`` family key the reviewer scheduler also searches.
_CLAUDE_LANE_KEY = re.compile(r"claude(?:$|[^a-z0-9])|anthropic$")
_ACCOUNT_LANE_KEY = re.compile(r"claude:(.*)$")
# Process-local: a snapshot's meter seal verifies only in the process that bound it.
_SEAL_KEY = secrets.token_bytes(32)
SHARED_ROUTE_FACT_KEYS = ("health", "runtime", "scheduler", "circuit_open", "eligible")
# The meter fields of a ``ranked_by_headroom`` row; its ``lane``, ``type``,
# ``in_flight`` and ``health`` are route facts.
RANKED_METER_KEYS = ("status", "burn_pct_7d", "remaining_pct", "resets_at")
ACCOUNT_RATE_LIMIT_FIELDS = frozenset(
    {"rate_limited", "last_rate_limited_at", "models_rate_limited", "headroom_blocked", "headroom_reason"}
)
SCHEDULER_QUOTA_FIELDS = frozenset({"quota_remaining_pct", "quota_stale"})
# The normalizer's error-shape keys, which the producer leaves out of a lane's ``codexbar``.
_NATIVE_ERROR_SHAPE_KEYS = frozenset({"lane", "status", "auth_error", "error_kind", "error_code"})
# The source of an account that could not be resolved or bound.
UNRESOLVED_SOURCE = "unresolved"
# The capacity verdict on one account's claude seat (:func:`capacity_verdict`).
HOT, HEALTHY, UNKNOWN = "hot", "healthy", "unknown"


@dataclass(frozen=True)
class ClaudeAccount:
    """The account a claude route runs as: the account part of its route key (#10630).

    A resolved account has a ``label`` and the ``source`` it came from. An
    unresolved one has no label, source ``unresolved`` and the
    ``ClaudeAccountRefused`` code in ``refusal``: its meter reads as unknown
    and no claude seat is selected on it. Built only by this module.
    """

    label: str | None
    source: str
    refusal: str | None = None

    def __post_init__(self) -> None:
        from scripts.agent_runtime.attempt_boundary import (
            CLAUDE_ACCOUNT_LABELS,
            CLAUDE_ACCOUNT_REFUSAL_CODES,
            CLAUDE_ACCOUNT_SOURCES,
        )

        if self.label is None:
            valid = self.source == UNRESOLVED_SOURCE and self.refusal in CLAUDE_ACCOUNT_REFUSAL_CODES
        else:
            valid = self.label in CLAUDE_ACCOUNT_LABELS and self.source in CLAUDE_ACCOUNT_SOURCES
            valid = valid and self.refusal is None
        if not valid:
            raise ValueError("invalid Claude account route key")

    @property
    def resolved(self) -> bool:
        return self.label is not None


def require_account(account: object) -> ClaudeAccount:
    """``account`` when it is a :class:`ClaudeAccount`; anything else (a bare label, None) raises ``TypeError``."""
    if not isinstance(account, ClaudeAccount):
        raise TypeError(f"the claude lane is read for a named ClaudeAccount (#10630), not {type(account).__name__}")
    return account


class AccountRequired(BaseException):
    """A claude meter was read from a snapshot not bound to a :class:`ClaudeAccount` (#10770).

    A programming-contract failure, never missing data. Like
    ``asyncio.CancelledError`` it derives from ``BaseException``, so the broad
    ``except Exception`` and ``except ValueError`` handlers around snapshot
    acquisition cannot turn it into an unknown reading: it reaches the caller.
    """


_BINDER = object()


def is_claude_lane_key(key: object) -> bool:
    """Whether an ``agents`` key (or ``ranked_by_headroom`` lane) denotes a Claude seat's meter, canonical or alias."""
    return isinstance(key, str) and _CLAUDE_LANE_KEY.match(key.strip().casefold()) is not None


def _in_account_view(key: object, account: ClaudeAccount, *, host: bool) -> bool:
    """Whether the ``agents`` record (or ``ranked_by_headroom`` row) under ``key`` stays in ``account``'s view.

    A record that names no Claude seat, and the canonical ``claude`` lane
    (rebuilt for another account), stay. A claude alias carries no account
    label, so it is the meter of the host account whose payload it is, like
    the lane row: the host account (``host``) keeps it and every other account
    drops it. A ``claude:<account>`` key is kept only by the host account and
    only when it names that account.
    """
    if key == CLAUDE_LANE or not is_claude_lane_key(key):
        return True
    named = _ACCOUNT_LANE_KEY.match(str(key).strip().casefold())
    return host and (named is None or named.group(1) == account.label)


def _refuse_mutation(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise TypeError("a bound routing snapshot is immutable: derive a view with AccountSnapshot.evolve (#10770)")


class _FrozenDict(dict[str, Any]):
    """A ``dict`` inside a bound snapshot: every mutator raises, and it remembers the account it was bound to.

    A ``dict`` subclass so the consumers' ``isinstance(record, dict)`` readings
    are unchanged; a copy (``dict(record)``, ``record.copy()``, ``record | x``)
    is a plain ``dict`` whose nested values stay frozen.
    """

    __slots__ = ("_label",)
    _label: str | None
    __setitem__ = __delitem__ = __ior__ = _refuse_mutation  # type: ignore[assignment]
    clear = pop = popitem = setdefault = update = _refuse_mutation  # type: ignore[assignment]

    def __setattr__(self, name: str, value: Any) -> NoReturn:
        _refuse_mutation()

    def __copy__(self) -> _FrozenDict:
        return self

    def __deepcopy__(self, memo: Any) -> _FrozenDict:
        return self

    def __reduce_ex__(self, protocol: Any) -> tuple[Any, ...]:
        return dict, (dict(self),)


class _FrozenList(list[Any]):
    """A ``list`` inside a bound snapshot: every mutator raises, and it remembers the account it was bound to."""

    __slots__ = ("_label",)
    _label: str | None
    __setitem__ = __delitem__ = __iadd__ = __imul__ = _refuse_mutation  # type: ignore[assignment]
    append = extend = insert = pop = remove = clear = sort = reverse = _refuse_mutation  # type: ignore[assignment]

    def __setattr__(self, name: str, value: Any) -> NoReturn:
        _refuse_mutation()

    def __copy__(self) -> _FrozenList:
        return self

    def __deepcopy__(self, memo: Any) -> _FrozenList:
        return self

    def __reduce_ex__(self, protocol: Any) -> tuple[Any, ...]:
        return list, (list(self),)


def _freeze(value: Any, label: str | None) -> Any:
    """``value`` with every mapping and list replaced by a frozen copy bound to ``label``; tuples stay tuples."""
    frozen: _FrozenDict | _FrozenList
    if isinstance(value, _FrozenDict | _FrozenList) and value._label == label:
        return value  # already frozen for this account
    if isinstance(value, Mapping):
        frozen = _FrozenDict((key, _freeze(item, label)) for key, item in value.items())
    elif isinstance(value, list):
        frozen = _FrozenList(_freeze(item, label) for item in value)
    elif type(value) is tuple:
        return tuple(_freeze(item, label) for item in value)
    else:
        return value
    object.__setattr__(frozen, "_label", label)
    return frozen


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_thaw(item) for item in value]
    return value


def _bound_label(value: object) -> tuple[bool, str | None]:
    """``(True, label)`` for a value taken from a bound snapshot, else ``(False, None)``."""
    if isinstance(value, AccountSnapshot):
        return True, value._account.label
    if isinstance(value, _FrozenDict | _FrozenList):
        return True, value._label
    return False, None


def _other_account_value(value: Any, label: str | None) -> tuple[str, str | None] | None:
    """``(path, owner)`` of the first value in ``value`` taken from a snapshot bound to another account, else None."""
    bound, owner = _bound_label(value)
    if bound:
        return None if owner == label else ("", owner)  # a value bound to this account holds nothing else
    items = value.items() if isinstance(value, Mapping) else enumerate(value) if isinstance(value, list | tuple) else ()
    for key, item in items:
        found = _other_account_value(item, label)
        if found is not None:
            return f"[{key!r}]{found[0]}", found[1]
    return None


def _refuse_other_accounts(value: Any, label: str | None, *, path: str = "payload") -> None:
    """Raise :class:`AccountRequired` when ``value`` holds anything taken from a snapshot bound to another account.

    A bound snapshot's frozen values remember their account, so a plain
    mapping spliced from another account's view (``{**view}`` without its
    binding, ``{"agents": view["agents"]}``) is never read as ``label``.
    """
    found = _other_account_value(value, label)
    if found is not None:
        raise AccountRequired(
            f"{path}{found[0]} was taken from a snapshot bound to claude account {found[1]!r} and is not read as "
            f"{label!r}: bind the raw payload for that account (#10770)"
        )


def _material(value: Any) -> Any:
    """``value`` as canonical JSON-ready data: mappings keyed by ``str``, sequences as lists, the rest as ``repr``."""
    if isinstance(value, Mapping):
        return {str(key): _material(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_material(item) for item in value]
    if value is None or isinstance(value, str | int | float):
        return value
    return repr(value)


def _meter_seal(label: str | None, evidence: Mapping[str, Any], data: Mapping[str, Any]) -> str:
    """The keyed digest of ``label``, ``evidence`` and every claude meter in ``data``.

    The meter is every ``agents`` record of a Claude seat (canonical or alias), the
    claude rows of ``ranked_by_headroom``, ``claude_accounts`` and
    ``preferred_claude_account``. Another top-level field (a decision's
    ``review_capacity_exclusions``) or another lane's record is not part of it.
    """
    agents = data.get("agents")
    ranked = data.get("ranked_by_headroom")
    # An empty or non-mapping claude record carries no meter, as an absent one.
    meter = {
        "agents": {
            str(key): record
            for key, record in agents.items()
            if is_claude_lane_key(key) and isinstance(record, Mapping) and record
        }
        if isinstance(agents, Mapping)
        else agents,
        "ranked_by_headroom": [
            row for row in ranked if not isinstance(row, Mapping) or is_claude_lane_key(row.get("lane"))
        ]
        if isinstance(ranked, list | tuple)
        else ranked,
        **{field: data[field] for field in ("claude_accounts", "preferred_claude_account") if field in data},
    }
    material = json.dumps(
        _material({"label": label, "evidence": evidence, "meter": meter}),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hmac.new(_SEAL_KEY, material.encode("utf-8"), hashlib.sha256).hexdigest()


class AccountSnapshot(Mapping[str, Any]):
    """A routing-budget snapshot read as one :class:`ClaudeAccount` (#10770).

    Built only by :func:`bind_snapshot`. Its ``agents.claude`` is the account's
    lane record: the default account's lane row unchanged, another account's
    record rebuilt from its ``claude_accounts`` row (:func:`lane_view`), an
    unresolved account's an unknown meter. No other account's meter remains:
    ``claude_accounts`` keeps only the account's own row,
    ``preferred_claude_account`` and every other account's claude alias
    record are gone (:func:`_in_account_view`), and
    the claude rows of ``ranked_by_headroom`` carry the account's meter
    fields. Every other key is the payload's own. A snapshot holding a meter
    field carries :data:`BINDING_KEY`: its account label, evidence and meter
    seal.

    The view is deeply immutable and is not a ``dict``: every nested mapping
    and list raises on mutation, and ``dict`` methods and ``vars`` cannot
    reach a raw payload through it. It is never serialized (JSON refuses it
    and pickling raises). A plain copy of it (``dict(view)``, a JSON round
    trip) is bound again only as its own account and only with its meter
    unaltered; a derived view comes from :meth:`evolve`.
    """

    __slots__ = ("_account", "_data", "_evidence")
    _account: ClaudeAccount
    _data: _FrozenDict
    _evidence: dict[str, Any]

    def __init__(
        self, data: _FrozenDict, account: ClaudeAccount, evidence: Mapping[str, Any], *, binder: object = None
    ) -> None:
        if binder is not _BINDER:
            raise TypeError("an AccountSnapshot is built only by claude_account_lane.bind_snapshot (#10770)")
        object.__setattr__(self, "_data", data)
        object.__setattr__(self, "_account", account)
        object.__setattr__(self, "_evidence", dict(evidence))

    @property
    def account(self) -> ClaudeAccount:
        """The account this snapshot's claude meter belongs to."""
        return self._account

    def evolve(self, **changes: Any) -> AccountSnapshot:
        """This snapshot with top-level keys replaced, bound to the same account (a decision's derived view).

        A change may not alter the account's meter (:func:`_meter_seal`): an
        ``agents`` map keeps the claude record unchanged and adds no claude
        alias, and ``claude_accounts``, ``ranked_by_headroom``,
        ``preferred_claude_account`` and :data:`BINDING_KEY` are not replaced.
        Such a change raises :class:`AccountRequired`; bind the raw payload
        instead.
        """
        _refuse_other_accounts(changes, self._account.label, path="evolve")
        data = {key: value for key, value in self._data.items() if key != BINDING_KEY}
        changed = {**data, **changes}
        if BINDING_KEY in changes or _meter_seal(self._account.label, self._evidence, changed) != _meter_seal(
            self._account.label, self._evidence, data
        ):
            raise AccountRequired(
                f"a view derived from a snapshot bound to claude account {self._account.label!r} may not change "
                "its claude meter: bind the raw payload (#10770)"
            )
        return _bound(changed, self._account, self._evidence)[0]

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"AccountSnapshot(account={self._account.label!r}, keys={sorted(self._data)!r})"

    def __setattr__(self, name: str, value: Any) -> NoReturn:
        raise AttributeError("an AccountSnapshot is immutable")

    def __delattr__(self, name: str) -> NoReturn:
        raise AttributeError("an AccountSnapshot is immutable")

    def __reduce_ex__(self, protocol: Any) -> NoReturn:
        raise TypeError("an AccountSnapshot is never serialized; bind the deserialized payload again (#10770)")


def require_bound(snapshot: object, *, reading: str) -> AccountSnapshot:
    """``snapshot`` when it is bound to an account and its meter verifies; anything else raises :class:`AccountRequired`."""
    if not isinstance(snapshot, AccountSnapshot):
        raise AccountRequired(
            f"{reading} reads the claude lane of an unbound {type(snapshot).__name__}: "
            "bind it with claude_account_lane.bind_snapshot (#10770)"
        )
    _verify_binding(snapshot._data, snapshot._account.label, snapshot._evidence)
    return snapshot


def resolve_route_account(
    explicit: object = None,
    *,
    strict: bool,
    recorded: Callable[[], str | None] | None = None,
    environ: Mapping[str, str] | None = None,
) -> ClaudeAccount:
    """The account a request's claude routes run as, resolved and bound before admission (#10619, #10733).

    The label is, in order: ``recorded()`` (a ``--force-new`` re-run's earlier
    record; a different ``explicit`` label is refused), ``explicit``, the
    default-account file, then the built-in default. A non-default label then
    has its binding and credential sources verified (``verify_claude_account``),
    so no claude seat is admitted on an account that was not bound. ``strict``
    (a claude request) raises ``ClaudeAccountRefused``; otherwise a refusal
    returns the unresolved account with its code.
    """
    from scripts.agent_runtime.attempt_boundary import (
        ClaudeAccountRefused,
        resolve_claude_account_label,
        resolve_dispatch_claude_account,
        verify_claude_account,
    )

    try:
        previous = recorded() if recorded is not None else None
        if previous is None:
            label, source = resolve_dispatch_claude_account(explicit, environ=environ)
        elif explicit is None:
            label, source = previous, "record"
        elif resolve_claude_account_label(explicit) == previous:
            label, source = previous, "explicit"
        else:
            raise ClaudeAccountRefused("claude_account_record_conflict")
        verify_claude_account(label, environ=environ)
    except ClaudeAccountRefused as exc:
        if strict:
            raise
        return ClaudeAccount(None, UNRESOLVED_SOURCE, exc.code)
    return ClaudeAccount(label, source)


def no_claude_account() -> ClaudeAccount:
    """The account of a route that reaches no claude seat: unresolved, so nothing claude is judged or admitted on it."""
    return ClaudeAccount(None, UNRESOLVED_SOURCE, "claude_account_seat_unsupported")


def account_from_record(record: Mapping[str, Any], *, agent: str) -> ClaudeAccount:
    """The account a task record's seat runs as (#10619).

    A claude record names its label, bound at dispatch and verified again
    where the worker authenticates; a claude record without one predates
    labels and ran as the default account. Another seat's record names no
    Claude account, so the result is unresolved and no claude reading is
    judged on it.
    """
    from scripts.agent_runtime.attempt_boundary import (
        CLAUDE_ACCOUNT_KEY,
        ClaudeAccountRefused,
        resolve_claude_account_label,
    )

    if agent != "claude":
        return no_claude_account()
    try:
        label = resolve_claude_account_label(record.get(CLAUDE_ACCOUNT_KEY))
    except ClaudeAccountRefused as exc:
        return ClaudeAccount(None, UNRESOLVED_SOURCE, exc.code)
    return ClaudeAccount(label, "record")


def account_left_pct(window: Any) -> float | None:
    """A ``claude_accounts`` window's ``left_pct`` when it is a real percentage, else None."""
    value = window.get("left_pct") if isinstance(window, Mapping) else None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value) if 0 <= value <= 100 else None


def _without(record: Any, keys: frozenset[str]) -> Any:
    return {key: value for key, value in record.items() if key not in keys} if isinstance(record, Mapping) else record


def route_facts(lane_row: Any) -> dict[str, Any]:
    """The lane row's route facts with every account meter field removed."""
    lane = lane_row if isinstance(lane_row, Mapping) else {}
    route = {key: lane[key] for key in SHARED_ROUTE_FACT_KEYS if key in lane}
    if "runtime" in route:
        route["runtime"] = _without(route["runtime"], ACCOUNT_RATE_LIMIT_FIELDS)
    if "scheduler" in route:
        route["scheduler"] = _without(route["scheduler"], SCHEDULER_QUOTA_FIELDS)
    return route


def lane_view(row: Any, lane_row: Any) -> tuple[dict[str, Any], str | None]:
    """The ``claude`` lane record for one ``claude_accounts`` row, and why its meter is unknown.

    An ``ok`` or ``stale`` row with known weekly and session ``left_pct`` takes the
    producer's path for the default account: the windows ``_probe_claude_native``
    builds, ``_normalize_provider_data`` and ``_status_from_weekly_used`` on the
    weekly used-%, so near cap, warm and pace deficit use the default lane's
    thresholds. A stale row reads ``stale_last_good`` like a stale default
    probe. Any other row reads status ``unknown`` with the probe
    ``unavailable`` and no pace, and the reason is returned (otherwise None).
    Both carry :func:`route_facts` of the lane row and nothing of the default
    account's own meter, credit or login state.
    """
    from scripts.api.state_router import _status_from_weekly_used
    from scripts.api.subscription_usage import _normalize_provider_data, _window_from_used_pct

    route = route_facts(lane_row)
    meter: Mapping[str, Any] = row if isinstance(row, Mapping) else {}
    # A non-string status (a list or mapping) is unhashable and never healthy.
    state = meter.get("status") if isinstance(meter.get("status"), str) else None
    session, weekly = meter.get("session5h"), meter.get("weekly")
    session_left, weekly_left = account_left_pct(session), account_left_pct(weekly)
    if (
        state not in {"ok", "stale"}
        or session_left is None
        or weekly_left is None
        or not isinstance(session, Mapping)
        or not isinstance(weekly, Mapping)
    ):
        if not meter:
            reason = "no account row"
        elif state not in {"ok", "stale"}:
            reason = str(meter.get("reason") or f"status {state or 'missing'}")
        else:
            reason = "weekly or session left_pct unknown"
        return {"status": "unknown", "freshness": "unavailable", **route}, reason
    stale = state == "stale"
    usage = {
        "primary": _window_from_used_pct(100.0 - session_left, window_minutes=300, resets_at=session.get("resets_at")),
        "secondary": _window_from_used_pct(
            100.0 - weekly_left, window_minutes=10080, resets_at=weekly.get("resets_at")
        ),
    }
    native = _normalize_provider_data("claude", {"provider": "claude", "source": "claude_account", "usage": usage})
    native.update({"freshness": "stale_last_good" if stale else "fresh", "stale": stale, "age_s": meter.get("age_s")})
    used = 100.0 - weekly_left  # the producer's capacity used-%: the weekly window's
    status = _status_from_weekly_used(
        used, native, lane="claude", info={**native, "codexbar": native}, snapshot_stale=stale
    )
    return {
        "status": status,
        "status_source": "weekly_pace",
        "interactive": {"status": status, "burn_pct_7d": used},
        "burn_pct_7d": used,
        "remaining_pct": 100.0 - used,
        "resets_at": native.get("weekly_resets_at"),
        "freshness": native["freshness"],
        "age_s": native["age_s"],
        "codexbar": {key: value for key, value in native.items() if key not in _NATIVE_ERROR_SHAPE_KEYS},
        **route,
    }, None


def _ranked_row(item: Any, record: Mapping[str, Any] | None) -> Any:
    """A ``ranked_by_headroom`` claude row with the producer's meter fields taken from ``record``."""
    if not isinstance(item, Mapping) or item.get("lane") != CLAUDE_LANE:
        return item
    lane = record or {}
    meter = {key: lane.get(key) for key in RANKED_METER_KEYS}
    return {**item, **meter, "status": lane.get("status", "unknown")}


def select_account(payload: Mapping[str, Any], *, account: ClaudeAccount) -> tuple[AccountSnapshot, dict[str, Any]]:
    """``payload`` bound to ``account`` (:class:`AccountSnapshot`), and the account evidence.

    The default account keeps the lane row (``meter`` ``agents.claude``).
    Another resolved account's ``agents.claude`` is :func:`lane_view` of its
    ``claude_accounts`` row; the evidence names that ``meter``, its ``state``
    (``ok``, ``stale`` or ``unknown``), the ``reason`` it is unknown, and the
    lane row's ``unattributed_rate_limits`` when they blocked it. An
    unresolved account reads the lane's route facts with an unknown meter,
    state ``unresolved`` and its refusal code as the reason. A payload without
    lane records (no or an empty ``agents`` map) has ``meter`` None. Every
    other account's meter is removed (:class:`AccountSnapshot`); the caller's
    payload is not modified.

    A claude alias (an ``agents`` key or ``ranked_by_headroom`` row denoting a
    Claude seat other than ``claude`` itself, :func:`is_claude_lane_key`)
    carries no account label, so it is the host account's meter, as the lane
    row is: the default account keeps it as the payload has it, and every
    other account's view drops it. A ``claude:<account>`` key naming another
    account is dropped from every view (:func:`_in_account_view`).

    Selecting a snapshot again for its own account returns it unchanged with
    its evidence (a fixed point) once its meter seal verifies; selecting it
    for another account raises :class:`AccountRequired`, because it no longer
    holds that account's meter. A plain mapping carrying :data:`BINDING_KEY`
    (a copy of a bound snapshot) is bound again only as that account and only
    with its meter seal intact, and a mapping holding a value taken from a
    snapshot bound to another account is refused (:class:`AccountRequired`).
    """
    from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT

    account = require_account(account)
    if isinstance(payload, AccountSnapshot):
        if payload.account.label != account.label:
            raise AccountRequired(
                f"a snapshot bound to claude account {payload.account.label!r} is not read as "
                f"{account.label!r}: bind the raw payload for that account (#10770)"
            )
        _verify_binding(payload._data, payload._account.label, payload._evidence)
        return payload, dict(payload._evidence)
    if not isinstance(payload, Mapping):
        raise TypeError(f"a routing snapshot is a mapping, not {type(payload).__name__}")
    _refuse_other_accounts(payload, account.label)
    if BINDING_KEY in payload:
        return _rebind_copy(payload, account)
    data = dict(payload)
    data.pop("preferred_claude_account", None)
    if "claude_accounts" in data:
        rows = data["claude_accounts"]
        row_key = f"claude:{account.label}"
        own = isinstance(rows, Mapping) and account.resolved and row_key in rows
        data["claude_accounts"] = {row_key: rows[row_key]} if own else {}
    host = account.label == DEFAULT_CLAUDE_ACCOUNT
    agents = payload.get("agents")
    if isinstance(agents, Mapping):
        agents = {key: record for key, record in agents.items() if _in_account_view(key, account, host=host)}
        data["agents"] = agents
    ranked = data.get("ranked_by_headroom")
    if isinstance(ranked, list):
        data["ranked_by_headroom"] = ranked = [
            item
            for item in ranked
            if not isinstance(item, Mapping) or _in_account_view(item.get("lane"), account, host=host)
        ]
    if host:
        return _bound(data, account, {"label": account.label, "meter": "agents.claude"})
    unresolved = {} if account.resolved else {"state": "unresolved", "reason": account.refusal}
    view: dict[str, Any] | None = None
    if not isinstance(agents, Mapping) or not agents:
        agents = {}
        evidence: dict[str, Any] = {"label": account.label, "meter": None, **unresolved}
    elif account.label is None:
        view = {"status": "unknown", "freshness": "unavailable", **route_facts(agents.get(CLAUDE_LANE))}
        evidence = {"label": None, "meter": None, **unresolved}
    else:
        lane_row = agents.get(CLAUDE_LANE)
        row_key = f"claude:{account.label}"
        rows = payload.get("claude_accounts")
        view, unknown = lane_view(rows.get(row_key) if isinstance(rows, Mapping) else None, lane_row)
        evidence = {
            "label": account.label,
            "meter": f"claude_accounts.{row_key}",
            "state": "unknown" if unknown is not None else "stale" if view["freshness"] != "fresh" else "ok",
            "reason": unknown,
        }
        runtime = lane_row.get("runtime") if isinstance(lane_row, Mapping) else None
        if isinstance(runtime, Mapping) and runtime.get("headroom_blocked"):
            evidence["unattributed_rate_limits"] = {
                key: runtime[key] for key in sorted(ACCOUNT_RATE_LIMIT_FIELDS) if key in runtime
            }
    if view is not None:
        data["agents"] = {**agents, CLAUDE_LANE: view}
    if isinstance(ranked, list):
        data["ranked_by_headroom"] = [_ranked_row(item, view) for item in ranked]
    return _bound(data, account, evidence)


def _rebind_copy(payload: Mapping[str, Any], account: ClaudeAccount) -> tuple[AccountSnapshot, dict[str, Any]]:
    """A plain copy of a bound snapshot, bound again as ``account``: only its own account, only unaltered."""
    binding = payload[BINDING_KEY]
    owner = binding.get("label") if isinstance(binding, Mapping) else None
    if not isinstance(binding, Mapping) or owner != account.label:
        raise AccountRequired(
            f"a copy of a snapshot bound to claude account {owner!r} is not read as {account.label!r}: "
            "bind the raw payload for that account (#10770)"
        )
    evidence = _thaw(binding.get("evidence"))
    data = {key: value for key, value in payload.items() if key != BINDING_KEY}
    if not isinstance(evidence, dict):
        evidence = {}
    _verify_binding({**data, BINDING_KEY: binding}, owner, evidence)
    return _bound(data, account, evidence)


def _verify_binding(data: Mapping[str, Any], label: str | None, evidence: Mapping[str, Any]) -> None:
    """Raise :class:`AccountRequired` unless ``data``'s claude meter is the one bound to ``label`` with ``evidence``.

    A snapshot without a meter field has no binding to verify. The seal is
    keyed by this process, so a copy bound in another process, or a meter
    altered after binding, is refused: bind the raw payload.
    """
    binding = data.get(BINDING_KEY)
    unsealed = {key: value for key, value in data.items() if key != BINDING_KEY}
    if binding is None and not METER_FIELDS.intersection(unsealed):
        return
    seal = binding.get("seal") if isinstance(binding, Mapping) else None
    if not (
        isinstance(binding, Mapping)
        and binding.get("label") == label
        and isinstance(seal, str)
        and hmac.compare_digest(seal, _meter_seal(label, evidence, unsealed))
    ):
        raise AccountRequired(
            f"the claude meter of a snapshot bound to claude account {label!r} does not verify: it was altered "
            "after binding or bound in another process; bind the raw payload (#10770)"
        )


def _bound(
    data: Mapping[str, Any], account: ClaudeAccount, evidence: dict[str, Any]
) -> tuple[AccountSnapshot, dict[str, Any]]:
    label = account.label
    frozen = {key: _freeze(value, label) for key, value in data.items() if key != BINDING_KEY}
    if METER_FIELDS.intersection(frozen):
        seal = _meter_seal(label, evidence, frozen)
        frozen[BINDING_KEY] = {"label": label, "evidence": evidence, "seal": seal}
    snapshot = AccountSnapshot(_freeze(frozen, label), account, evidence, binder=_BINDER)
    return snapshot, dict(evidence)


def bind_snapshot(payload: Mapping[str, Any], *, account: ClaudeAccount) -> AccountSnapshot:
    """``payload`` bound to ``account``: :func:`select_account` without the evidence."""
    return select_account(payload, account=account)[0]


def account_agents(payload: Mapping[str, Any] | None, *, account: ClaudeAccount) -> Mapping[str, Any]:
    """The snapshot's lane records with the claude lane read as ``account`` (empty when it has none)."""
    view, _ = select_account(payload or {}, account=account)
    agents = view.get("agents")
    return agents if isinstance(agents, Mapping) else {}


def lane_record(payload: Mapping[str, Any] | None, lane: str, *, account: ClaudeAccount) -> Mapping[str, Any]:
    """One lane's record from the snapshot, the claude lane read as ``account`` (empty when absent)."""
    record = account_agents(payload, account=account).get(lane)
    return record if isinstance(record, Mapping) else {}


def other_lane_record(payload: Any, lane: str) -> Mapping[str, Any]:
    """A lane no Claude account owns, read without one; the claude lane raises :class:`AccountRequired`."""
    if lane.strip().casefold() == CLAUDE_LANE:
        raise AccountRequired("the claude lane is read for a named account: use lane_record (#10630, #10770)")
    agents = payload.get("agents") if isinstance(payload, Mapping) else None
    record = agents.get(lane) if isinstance(agents, Mapping) else None
    return record if isinstance(record, Mapping) else {}


def account_weekly_used_pct(payload: Any, *, account: ClaudeAccount) -> float | None:
    """``account``'s weekly used-% from a routing-budget payload, or None.

    Only a fresh reading may block: the default account's lane row when its
    probe is fresh and not withdrawn (status ``unknown``), another account's
    ``ok`` row (measured within the cache TTL, no failure since) with a known
    weekly ``left_pct``. A stale, unknown or missing reading, and an
    unresolved account, give None.
    """
    from scripts.agent_runtime.attempt_boundary import DEFAULT_CLAUDE_ACCOUNT

    account = require_account(account)
    if not isinstance(payload, Mapping) or account.label is None:
        return None
    payload = bind_snapshot(payload, account=account)
    if account.label == DEFAULT_CLAUDE_ACCOUNT:
        agents = payload.get("agents")
        info = agents.get(CLAUDE_LANE) if isinstance(agents, Mapping) else None
        if not isinstance(info, Mapping) or info.get("status") == "unknown":
            return None  # missing, or withdrawn as stale by Monitor
        codexbar = info.get("codexbar")
        if not isinstance(codexbar, Mapping):
            return None
        if codexbar.get("stale") is not False or codexbar.get("freshness") != "fresh":
            return None  # only a fresh probe reading may block a dispatch
        value = codexbar.get("weekly_used_pct")
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
        return None
    rows = payload.get("claude_accounts")
    row = rows.get(f"claude:{account.label}") if isinstance(rows, Mapping) else None
    if not isinstance(row, Mapping) or row.get("status") != "ok" or row.get("stale") is not False:
        return None
    left = account_left_pct(row.get("weekly"))
    return None if left is None else 100.0 - left


def capacity_verdict(payload: Mapping[str, Any] | None, *, account: ClaudeAccount) -> str:
    """The capacity verdict on ``account``'s claude seat: :data:`HOT`, :data:`HEALTHY` or :data:`UNKNOWN`.

    The capacity owner's class (:func:`credit_lane.routing_facts`) of the
    claude lane record read as ``account``: ``avoid`` is hot, ``verified`` is
    healthy, and any unknown reading is unknown. Only a fresh reading is hot or
    healthy: a stale meter is advisory and reads unknown, as the dispatch guard
    (a stale account meter never substitutes), reviewer selection
    (``review_capacity`` keeps stale allowance advisory) and the plan-headroom
    stop (only a fresh reading blocks) treat it. A route fact no meter owns
    (ineligible, unhealthy, NEED_LOGIN, a runtime block) stays hot at any
    freshness. An unresolved account is unknown whatever the lane row says.
    Every decision consumer reaches the same verdict.
    """
    from scripts.fleet import credit_lane

    if not require_account(account).resolved:
        return UNKNOWN
    diagnostics = payload.get("diagnostics") if isinstance(payload, Mapping) else None
    record = lane_record(payload, "claude", account=account)
    facts = credit_lane.routing_facts(
        "claude",
        record,
        model=None,
        snapshot_metadata=diagnostics if isinstance(diagnostics, Mapping) else None,
    )
    runtime = record.get("runtime")
    route_refusal = (
        record.get("eligible") is False
        or facts.health == credit_lane.UNHEALTHY
        or "NEED_LOGIN" in (record.get("login_state"), record.get("probe_state"))
        or (isinstance(runtime, Mapping) and bool(runtime.get("headroom_blocked")))
    )
    if facts.capacity == credit_lane.CAPACITY_AVOID and route_refusal:
        return HOT
    if facts.observation_freshness != credit_lane.FRESH:
        return UNKNOWN
    return {credit_lane.CAPACITY_AVOID: HOT, credit_lane.CAPACITY_VERIFIED: HEALTHY}.get(facts.capacity, UNKNOWN)
