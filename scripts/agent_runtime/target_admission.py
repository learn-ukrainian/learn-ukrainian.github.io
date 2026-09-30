"""Targets are admitted in the same step they are resolved.

Every delivery, insertion, wake and launch sink in the bridge, channels, ACP,
fleet-comms and delegate code takes an ``AdmittedTarget``, and
``resolve_and_admit`` is the only producer of one. It performs every step that
decides who a request reaches — the explicit recipients and model, the models
and recipients its ``data`` attachments carry, legacy compat command names,
the ACP route registry's adapter agent and model pin, retired-CLI aliases,
role slots resolved to their live holder, quota substitution, and a launch
route (``delegate.py``'s budget substitution) — and runs the Kimi gate
(``kimi_admission.refuse_kimi_if_disallowed``) twice: on the original request
before any resolution step reads state or has an effect, and on the final
seats and models together with the original request, raising
``KimiAdmissionRefused`` before it returns. A sink therefore receives exactly
the target that was gated; nothing resolves after the gate.

The named resolvers are called from this module only
(``tests/test_target_admission_structure.py`` scans the callers). That scan is
bounded — named calls and local bindings, not callbacks or aliased calls — so
the execution-time re-check (``kimi_admission.refuse_kimi_execution``) stays
the backstop.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Collection, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .kimi_admission import (
    BRIDGE_MODE,
    KimiAdmissionRefused,
    effective_request_targets,
    refuse_kimi_if_disallowed,
)

# Legacy ``ask-<name>`` command names and the ACP participant each one selects.
COMPAT_TARGETS: dict[str, str] = {
    "claude": "claude",
    "codex": "codex",
    "agy": "agy",
    "gemini": "agy",
    "hermes": "deepseek",
    "deepseek": "deepseek",
    "pool": "pool",
    "glm": "glm",
    "gemma": "gemma",
    "cursor": "cursor",
    "grok": "grok",
    "grok-build": "grok",
    "kimi": "kimi",
}

_MINTING: ContextVar[bool] = ContextVar("admitted_target_minting", default=False)


class SubstituteUnavailable(Exception):
    """No enabled ACP seat substitutes for an over-quota seat; the message says why."""


@dataclass(frozen=True)
class RouteRequest:
    """One requested seat, as a caller's launch ``route`` sees it inside ``resolve_and_admit``.

    ``seat`` and ``model`` are what the request named; ``retired_successor``
    is the live CLI a retired seat name resolves to (None: not retired);
    ``fallbacks`` is the ``dispatch_fallbacks`` table, the only source of
    budget substitutes. The route runs after the original request is gated.
    """

    seat: str
    model: str | None
    retired_successor: str | None
    fallbacks: Mapping[str, str]


# A launch route: the ``(seat, model, reason)`` a request is launched as.
Route = Callable[[RouteRequest], tuple[str, str | None, str]]


@dataclass(frozen=True)
class AdmittedTarget:
    """A recipient and model that ``resolve_and_admit`` resolved and the Kimi gate admitted.

    ``recipient`` is the final seat (after compat names, slot holders and
    substitution); ``model`` is the model the request pins (None: the seat's
    registered pin applies); ``reason`` records how the recipient was reached
    (``explicit``, ``compat:<name>``, ``slot:<slot>``,
    ``substitute:<seat>:<reason>``, or the reason a launch route gives).
    Only ``resolve_and_admit`` constructs one.
    """

    recipient: str
    model: str | None
    reason: str

    def __post_init__(self) -> None:
        if not _MINTING.get():
            raise TypeError("an AdmittedTarget is produced only by resolve_and_admit")


@contextmanager
def _minting() -> Iterator[None]:
    token = _MINTING.set(True)
    try:
        yield
    finally:
        _MINTING.reset(token)


def require_admitted(target: Any) -> AdmittedTarget:
    """The sink-side check: ``target`` must be an ``AdmittedTarget`` from ``resolve_and_admit``.

    The ``agent_runtime`` and ``scripts.agent_runtime`` import paths load this
    module twice, so the class is recognised by name and module suffix.
    """
    cls = type(target)
    if cls.__name__ != "AdmittedTarget" or not cls.__module__.endswith("agent_runtime.target_admission"):
        raise TypeError(f"a delivery sink takes an AdmittedTarget from resolve_and_admit, not {cls.__name__}")
    return target


def resolve_and_admit(
    recipients: Iterable[str | None],
    *,
    mode: str,
    model: str | None = None,
    attachments: Iterable[Any] = (),
    also_models: Iterable[str | None] = (),
    compat: bool = False,
    slots: Collection[str] | None = None,
    substitute: str | None = None,
    fallbacks_path: Path | None = None,
    route: Route | None = None,
    resolver: Callable[[str], str] | None = None,
    warnings: list[str] | None = None,
    **gate: Any,
) -> tuple[AdmittedTarget, ...]:
    """Resolve every recipient to its final seat, gate the result, and return one target per recipient.

    ``mode`` and ``**gate`` are the Kimi gate's (``refuse_kimi_if_disallowed``).
    ``model`` is the explicit model every target pins; ``attachments`` are the
    request's ``data`` payloads, whose model and recipient keys are gated
    (an explicit ``model`` overrides an attached ``to_model``); ``also_models``
    are further models the request selects (per-participant overrides).
    Resolution steps, in order:

    - ``compat``: a legacy command name maps to its ACP participant; an unknown
      name raises ``ValueError``.
    - ``substitute``: the seat is replaced by its ``dispatch_fallbacks``
      substitute (read from ``fallbacks_path``) for that typed capacity
      reason, whose registered pins apply (``model`` is dropped); none raises
      ``SubstituteUnavailable``.
    - ``route``: a caller's launch route (``RouteRequest`` to ``(seat, model,
      reason)``), given the seat's retired-CLI successor and the
      ``dispatch_fallbacks`` table (read from ``fallbacks_path``); it may
      replace both the seat and the model, and its errors propagate.
    - ``resolver``: a caller's registry lookup (e.g. a retired endpoint to its
      successor) maps the seat to the one it names; its errors propagate.
    - ``slots``: a role slot (a hyphenated name outside ``slots``) resolves to
      its live holder; an unheld slot, or a failed lookup, keeps the slot
      identity and appends a warning to ``warnings``.

    The gate runs first on the original request — every seat and model it
    carries, with their compat participants, retired-CLI successors and ACP
    route pins — in every mode, before any step above reads state or has an
    effect (a budget probe, a model probe). It runs again on the final seats
    and models together with the original request, unless resolution added
    no name the first run did not already gate. Raises ``KimiAdmissionRefused``
    before returning; writes nothing.
    """
    raw = ["" if item is None else str(item) for item in recipients]
    explicit_model = model or None
    seats, models = effective_request_targets(raw, explicit_model, *attachments)
    models.extend(item for item in also_models if item)
    requested = _gate_names(seats, models)
    refuse_kimi_if_disallowed(*requested, mode=mode, **gate)

    fallbacks: Mapping[str, str] = {}
    if route is not None and fallbacks_path is not None:
        from scripts.common.fallback_substitutions import load_dispatch_fallbacks

        fallbacks = load_dispatch_fallbacks(fallbacks_path)
    resolved: list[tuple[str, str | None, str]] = []
    for name in raw:
        recipient, target_model, reason = name, explicit_model, "explicit"
        if compat:
            participant = COMPAT_TARGETS.get(name.strip().lower())
            if participant is None:
                raise ValueError(f"legacy ask target {name!r} has no enabled ACP route")
            recipient, reason = participant, f"compat:{name}"
        if substitute is not None:
            reason = f"substitute:{recipient}:{substitute}"
            recipient, target_model = _substitute_seat(recipient, substitute, fallbacks_path), None
        if route is not None:
            recipient, target_model, reason = route(
                RouteRequest(recipient, target_model, _retired_successor(recipient), fallbacks)
            )
        if resolver is not None:
            looked_up = resolver(recipient)
            if looked_up != recipient:
                recipient, reason = looked_up, f"registry:{recipient}"
        if slots is not None:
            holder = _slot_holder(recipient, static_agents=slots, warnings=warnings, warn_if_unheld=True)
            if holder != recipient:
                recipient, reason = holder, f"slot:{recipient}"
        resolved.append((recipient, target_model, reason))

    final = _gate_names(
        [*seats, *(recipient for recipient, _, _ in resolved)],
        [*models, *(target_model for _, target_model, _ in resolved)],
    )
    if not (set(final[0]) <= set(requested[0]) and set(final[1]) <= set(requested[1])):
        refuse_kimi_if_disallowed(*final, mode=mode, **gate)
    with _minting():
        return tuple(AdmittedTarget(recipient, target_model, reason) for recipient, target_model, reason in resolved)


def stored_kimi_row(agent: object, model: object = None) -> bool:
    """True when a stored row is addressed to a Kimi seat or model, which the bridge gate refuses.

    For generic drains and sweeps only, never a delivery target: Kimi is not a
    bridge recipient and nothing new can be addressed to it, but legacy rows
    may remain. A drain skips them before any claim, lease, attempt, status,
    error or telemetry write; reading them is allowed. Decided by
    ``resolve_and_admit`` in bridge mode, from names and the static route
    registry.
    """
    return _stored_kimi_row(str(agent or "").strip(), str(model or "").strip() or None)


@lru_cache(maxsize=1024)
def _stored_kimi_row(agent: str, model: str | None) -> bool:
    try:
        resolve_and_admit((agent,), mode=BRIDGE_MODE, model=model)
    except KimiAdmissionRefused:
        return True
    return False


def resolve_sender(agent: str, *, static_agents: Collection[str], warnings: list[str]) -> str:
    """The live holder of a sending slot, for self-fanout checks only; never a delivery target.

    An unheld sender is not a delivery concern, so it adds no warning; a
    failed lookup does.
    """
    return _slot_holder(agent, static_agents=static_agents, warnings=warnings, warn_if_unheld=False)


def describe_slot_holder(slot: str) -> Any:
    """The read-only lease facts for ``slot`` (``SlotHolderResult``), for display; never a delivery target."""
    from scripts.orchestration import slot_routing

    return slot_routing.resolve_slot_holder(slot)


def launch_seat(agent: str) -> str:
    """The seat a retired CLI name launches as (its successor), for naming its dispatch worktree only; never a launch target."""
    return _retired_successor(agent) or agent


def _retired_successor(seat: str | None) -> str | None:
    from .agent_identity import resolve_retired_agent_alias

    return resolve_retired_agent_alias(seat)


def _gate_names(seats: Iterable[str | None], models: Iterable[str | None]) -> tuple[list[Any], list[Any]]:
    """Every seat and model a request reaches: with compat participants, retired successors and ACP route pins."""
    participants: list[Any] = list(seats)
    participants.extend(_compat_names(participants))
    participants.extend(successor for seat in participants if (successor := _retired_successor(seat)))
    routes = _acp_routes(participants)
    return (
        [*participants, *(route.get("agent") for route in routes)],
        [*models, *(route.get("model") for route in routes)],
    )


def _compat_names(seats: Iterable[str | None]) -> list[str]:
    return [participant for seat in seats if (participant := COMPAT_TARGETS.get(str(seat or "").strip().lower()))]


def _acp_routes(seats: Iterable[str | None]) -> list[dict[str, Any]]:
    from .adapters.acpx import ACPX_SUPPORTED_PARTICIPANTS

    routes = (ACPX_SUPPORTED_PARTICIPANTS.get(str(seat or "").strip().lower()) for seat in seats)
    return [route for route in routes if isinstance(route, dict)]


def _slot_holder(
    agent: str,
    *,
    static_agents: Collection[str],
    warnings: list[str] | None,
    warn_if_unheld: bool,
) -> str:
    """Resolve a slot to its live holder, retaining unheld slots unchanged.

    Two distinct failure categories, both surfaced (#5889):

    - **Resolver/import failure** (``resolve_slot_holder`` raises, or the
      module cannot be imported): an infrastructure problem, NOT a "no live
      holder" state. Always appended to ``warnings`` — never silent-dropped
      — and the slot identity is returned so the post still queues.
    - **No live holder** (resolver returned ``has_holder=False``): the
      normal bounce. Appended to ``warnings`` only when ``warn_if_unheld``
      is set (recipient side); the sender side stays quiet because an
      unheld sender is not a delivery concern.
    """
    if "-" not in agent or agent in static_agents:
        return agent
    try:
        from scripts.orchestration import slot_routing

        res = slot_routing.resolve_slot_holder(agent)
    except Exception as exc:
        _warn(
            warnings,
            f"⚠️ channel-bridge: slot resolver failed for '{agent}' ({type(exc).__name__}: {exc}) — queued at identity",
        )
        return agent
    if res.has_holder:
        return res.holder_agent or agent
    if warn_if_unheld:
        _warn(
            warnings,
            f"⚠️ channel-bridge: recipient slot '{agent}' has no live holder (queued at {res.queue_location})",
        )
    return agent


def _warn(warnings: list[str] | None, message: str) -> None:
    if warnings is not None:
        warnings.append(message)
    print(message, file=sys.stderr)


def _substitute_seat(seat: str, reason: str, fallbacks_path: Path | None) -> str:
    """The enabled ACP seat ``dispatch_fallbacks`` maps an over-quota ``seat`` to (#8499)."""
    from scripts.common.fallback_substitutions import load_dispatch_fallbacks

    if fallbacks_path is None:
        raise SubstituteUnavailable(f"ACP seat '{seat}' substitution needs the dispatch_fallbacks path")
    substitute = load_dispatch_fallbacks(fallbacks_path).get(seat)
    if not substitute or substitute == seat:
        raise SubstituteUnavailable(
            f"ACP seat '{seat}' is over quota/rate-limited (reason: {reason}) and "
            "agent_fallback_substitutions.yaml dispatch_fallbacks has no substitute "
            "for it; failing without bridge/provider fallback."
        )
    if substitute not in set(COMPAT_TARGETS.values()):
        raise SubstituteUnavailable(
            f"ACP seat '{seat}' is over quota/rate-limited (reason: {reason}) but "
            f"dispatch_fallbacks maps it to '{substitute}', which is not an enabled "
            "ACP ask seat; failing without bridge/provider fallback."
        )
    return substitute
