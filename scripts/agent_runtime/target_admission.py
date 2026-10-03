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
    REVIEW_MODE,
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


class ReviewAdmissionRefused(Exception):
    """A review cannot retain its requested identity or resolve an eligible substitute."""


ReviewSelector = Callable[[Mapping[str, Any] | None, str], tuple[str, str | None]]


@dataclass(frozen=True)
class RouteRequest:
    """One requested seat, as a caller's launch ``route`` sees it inside ``resolve_and_admit``.

    ``seat`` and ``model`` are what the request named; ``retired_successor``
    is the live CLI a retired seat name resolves to (None: not retired);
    ``fallbacks`` is the coding ``dispatch_fallbacks`` table. For a review,
    ``review_select`` instead selects or retains a reviewer using trusted
    author/profile/risk inputs and the canonical resolver. Pass the current
    over-budget seat with the snapshot, or a None snapshot for the initial check.
    The route runs after the original request is gated.

    Known limitation: a route's own probes (a Monitor budget probe) run
    before the final gate, so a non-Kimi request that a fallback row mapped
    onto Kimi would probe once and then be refused. No ``dispatch_fallbacks``
    row maps onto a Kimi seat or model, and
    ``tests/test_target_admission.py`` fails if one ever does.
    """

    seat: str
    model: str | None
    retired_successor: str | None
    fallbacks: Mapping[str, str]
    review_select: ReviewSelector | None = None
    retired_model_resolution: tuple[str, str] | None = None


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
    review_dispatch: bool = False,
    review_author_model: str | None = None,
    review_risk: str | None = None,
    review_profile: str | None = None,
    review_attempt: bool = False,
    review_alias_model_resolver: Callable[[str, str | None], tuple[str, str]] | None = None,
    review_owned_paths: tuple[str, ...] = (),
    review_changed_paths: tuple[str, ...] | Callable[[], tuple[str, ...]] = (),
    review_subject_seats: frozenset[str] = frozenset(),
    review_subject_families: frozenset[str] = frozenset(),
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

    A review activity (``review_dispatch``, ``REVIEW_MODE`` or the gate's
    ``review`` flag) refuses, with ``ReviewAdmissionRefused``, every requested
    and final model whose catalog roles admit no review (#9583).
    Review dispatches additionally constrain routes to ``review_select``'s
    admitted identities. Budget substitutions require both ``review_author_model``
    and ``review_risk``; review attempts never change identity. Retired aliases
    use ``review_alias_model_resolver`` once before selection and carry that
    model resolution into the launch route. Review owned paths and explicit
    subject seats/families use the canonical resolver's exclusion semantics.
    ``review_changed_paths`` may collect paths lazily after original-request
    gates; its result is shared by every subsequent reviewer evaluation.
    """
    raw = ["" if item is None else str(item) for item in recipients]
    explicit_model = model or None
    seats, models = effective_request_targets(raw, explicit_model, *attachments)
    models.extend(item for item in also_models if item)
    requested = _gate_names(seats, models)
    refuse_kimi_if_disallowed(*requested, mode=mode, **gate)
    review_activity = review_dispatch or mode == REVIEW_MODE or bool(gate.get("review"))
    if review_activity:
        _refuse_non_review_models(requested[1])
    # Target reads follow the original-request gates, but precede every
    # candidate evaluation, route probe and substitution.
    if callable(review_changed_paths):
        review_changed_paths = review_changed_paths()

    fallbacks: Mapping[str, str] = {}
    if route is not None and fallbacks_path is not None:
        from scripts.common.fallback_substitutions import load_dispatch_fallbacks

        fallbacks = load_dispatch_fallbacks(fallbacks_path)
    resolved: list[tuple[str, str | None, str]] = []
    for name in raw:
        recipient, target_model, reason = name, explicit_model, "explicit"
        approved_review_targets: set[tuple[str, str | None]] = set()
        review_seat = name
        retired_model_resolution = None
        if review_dispatch:
            review_seat = COMPAT_TARGETS.get(name.strip().lower(), name) if compat else name
            successor = _retired_successor(review_seat)
            if review_attempt and successor:
                raise ReviewAdmissionRefused(
                    "REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused: "
                    f"agent substitution from {review_seat} to {successor} (retired CLI) "
                    "is not allowed (#8517)"
                )
            review_seat = successor or review_seat
        review_model = explicit_model
        if review_dispatch and review_seat != name:
            if successor and review_alias_model_resolver is not None:
                retired_model_resolution = review_alias_model_resolver(review_seat, explicit_model)
                review_model = retired_model_resolution[0]
            elif review_model is None:
                from .telemetry import _default_model_for

                review_model = _default_model_for(review_seat)

        def review_select(
            snapshot: Mapping[str, Any] | None,
            budget_seat: str,
            *,
            requested_seat: str = review_seat,
            requested_model: str | None = review_model,
            approved: set[tuple[str, str | None]] = approved_review_targets,
        ) -> tuple[str, str | None]:
            selected = _resolve_review_target(
                requested_seat,
                requested_model,
                author_model=review_author_model,
                risk=review_risk,
                profile=review_profile or "code",
                attempt=review_attempt,
                snapshot=snapshot,
                budget_seat=budget_seat,
                budget_substitute=fallbacks.get(budget_seat),
                owned_paths=review_owned_paths,
                changed_paths=review_changed_paths,
                subject_seats=review_subject_seats,
                subject_families=review_subject_families,
            )
            approved.add(selected)
            return selected

        if review_dispatch:
            review_select(None, name)  # Refuse ineligible requests before a route can probe or print a substitute.
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
                RouteRequest(
                    recipient,
                    target_model,
                    _retired_successor(recipient),
                    fallbacks,
                    review_select if review_dispatch else None,
                    retired_model_resolution,
                )
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
        if review_dispatch and (recipient, target_model) not in approved_review_targets:
            raise ReviewAdmissionRefused(
                "REVIEW_ROUTE_REFUSED: resolved review identity was not admitted by the reviewer resolver"
            )

    final = _gate_names(
        [*seats, *(recipient for recipient, _, _ in resolved)],
        [*models, *(target_model for _, target_model, _ in resolved)],
    )
    if not (set(final[0]) <= set(requested[0]) and set(final[1]) <= set(requested[1])):
        refuse_kimi_if_disallowed(*final, mode=mode, **gate)
    if review_activity:
        _refuse_non_review_models(target_model for _, target_model, _ in resolved)
    with _minting():
        return tuple(AdmittedTarget(recipient, target_model, reason) for recipient, target_model, reason in resolved)


def _refuse_non_review_models(models: Iterable[str | None]) -> None:
    """Raise ``ReviewAdmissionRefused`` for a model the catalog gives no review role (#9583)."""
    from scripts.review.model_catalog import REVIEW_ACTIVITY, activity_role_refusal

    for model in models:
        if refusal := activity_role_refusal(model, REVIEW_ACTIVITY):
            raise ReviewAdmissionRefused(f"REVIEW_ROUTE_REFUSED: {refusal}")


def _resolve_review_target(
    seat: str,
    model: str | None,
    *,
    author_model: str | None,
    risk: str | None,
    profile: str,
    attempt: bool,
    snapshot: Mapping[str, Any] | None,
    budget_seat: str,
    budget_substitute: str | None = None,
    owned_paths: tuple[str, ...] = (),
    changed_paths: tuple[str, ...] = (),
    subject_seats: frozenset[str] = frozenset(),
    subject_families: frozenset[str] = frozenset(),
) -> tuple[str, str | None]:
    """Keep an eligible reviewer or select the canonical cross-family seat, never a coding fallback.

    A snapshot means the budget guard requires a substitute. Without both trusted
    inputs, only intrinsic eligibility can be proven and the requested identity is
    retained. This does not attest cross-family independence for those legacy calls.
    An existing attempt's seat AND model are immutable.
    """
    from scripts.review.model_catalog import risk_reviewer_refusal
    from scripts.review.reviewer_resolver import (
        REVIEW_CANDIDATES,
        REVIEW_LADDERS,
        UNKNOWN_AUTHOR_FAMILY,
        UNRESOLVED_AUTHOR_FAMILIES,
        ResolverInputs,
        candidate_dispatch_model,
        evaluate_candidate,
        resolve_author_family,
        resolve_family,
        resolve_reviewer,
    )
    from scripts.review.security_paths import effective_review_risk
    from scripts.review.subject_seat import prepare_subject_exclusion

    from .telemetry import _default_model_for

    requested_model = model or _default_model_for(seat) or ""
    concrete = requested_model.split("[", 1)[0]
    family = resolve_family(concrete or "")
    # The seat's registered pin reviews too when no model is named (#9583).
    _refuse_non_review_models((requested_model,))
    # Composer/Kimi never review. Grok is admitted only as the resolver's
    # runtime-attested Cursor seat (#9488); native Grok is excluded there.
    forbidden = {"moonshot"}
    if profile != "ukrainian":
        forbidden.add("google")
    trusted = bool(author_model and risk)
    if profile != "code" and (author_model or risk):
        raise ReviewAdmissionRefused(
            "REVIEW_ROUTE_REFUSED: --review-author-model and --review-risk support the code profile only; "
            "Ukrainian reviews use --review-profile ukrainian without these flags"
        )
    if attempt and snapshot is not None:
        if budget_substitute and budget_substitute != budget_seat:
            detail = (
                f"review attempt refused: agent substitution from {budget_seat} to {budget_substitute} "
                "(budget guard) is not allowed"
            )
        else:
            detail = (
                f"review attempt refused for {seat}: budget guard requires substitution; attempt identity is immutable"
            )
        raise ReviewAdmissionRefused(f"REVIEW_ATTEMPT_IDENTITY_REFUSED: {detail} (#8517)")
    subject = prepare_subject_exclusion(
        owned_paths=owned_paths, subject_seats=subject_seats, subject_families=subject_families
    )
    if subject.fail_closed_reason:
        raise ReviewAdmissionRefused(f"REVIEW_ROUTE_REFUSED: {subject.fail_closed_reason}")
    inputs = ResolverInputs(
        author_model=author_model or "",
        review_profile=profile,
        domain=profile,
        risk=effective_review_risk(risk or "medium", changed_paths, owned_paths),
        routing_snapshot=snapshot if trusted else None,
        owned_paths=owned_paths,
        changed_paths=changed_paths,
        subject_seats=subject.seats,
        subject_families=subject.families,
        subject_evidence=subject.evidence,
    )
    author_family = resolve_author_family(author_model or "") if trusted else UNKNOWN_AUTHOR_FAMILY
    if trusted and author_family in UNRESOLVED_AUTHOR_FAMILIES:
        raise ReviewAdmissionRefused("REVIEW_ROUTE_REFUSED: author's concrete model family cannot be resolved")
    if profile == "ukrainian":
        eligible = seat in {"claude", "codex", "agy"} and family in {"anthropic", "openai", "google"}
    else:
        # A Cursor seat is admitted only at its exact pinned slug: the adapter
        # sends the requested string unchanged, so a bracket suffix
        # (``grok-4.7-high[fast]``) would run an unattested variant (#9488).
        eligible = family not in forbidden and any(
            candidate.route == seat
            and candidate_dispatch_model(candidate)
            == (requested_model if candidate.transport == "cursor" else concrete)
            and evaluate_candidate(candidate, inputs, author_family=author_family).status == "eligible"
            for candidate in REVIEW_CANDIDATES.values()
        )
    # #9538: name the high-risk reviewer rule when it is why the request fails.
    risk_note = "" if eligible or profile == "ukrainian" else risk_reviewer_refusal(concrete, inputs.risk) or ""
    risk_note = f" ({risk_note})" if risk_note else ""
    if attempt and not eligible:
        from .review_mcp import UNSUPPORTED_HARNESS_REASONS

        detail = UNSUPPORTED_HARNESS_REASONS.get(
            seat,
            f"requested model {concrete!r} is ineligible for --review-profile {profile}; "
            "attempt identities cannot be substituted",
        )
        raise ReviewAdmissionRefused(
            f"REVIEW_ATTEMPT_IDENTITY_REFUSED: review attempt refused for {seat}: {detail}{risk_note} (#8517)"
        )
    if eligible and (snapshot is None or not trusted):
        return seat, model
    if not trusted:
        hint = (
            "choose an eligible Claude, GPT or Gemini Ukrainian reviewer"
            if profile == "ukrainian"
            else "code profile substitution requires --review-author-model and --review-risk"
        )
        raise ReviewAdmissionRefused(
            f"REVIEW_ROUTE_REFUSED: requested reviewer is ineligible for --review-profile {profile}{risk_note}; {hint}"
        )
    # Dispatch prohibitions constrain the ladder, rather than masquerading as
    # subject-boundary exclusions. Per-candidate eligibility above is independent
    # of ladder membership; only a necessary substitute uses ladder selection.
    ladder = tuple(
        tuple(candidate for candidate in rung if candidate.family not in forbidden)
        for rung in REVIEW_LADDERS[inputs.risk]
    )
    resolution = resolve_reviewer(
        inputs,
        ladder=ladder,
        excluded_quota_buckets=frozenset({budget_seat}) if snapshot else frozenset(),
    )
    if resolution.fail_closed_reason:
        raise ReviewAdmissionRefused(f"REVIEW_ROUTE_REFUSED: {resolution.fail_closed_reason}")
    selected = resolution.selected
    # #9394: weekly pace is a forecast, not exhaustion. If excluding this
    # bucket leaves no eligible substitute, retain the already cross-family,
    # snapshot-validated reviewer only when its lane still has capacity.
    # Health, circuit, subject, suitability and near-cap gates remain binding.
    lane_info = (snapshot.get("agents") or {}).get(budget_seat, {}) if snapshot else {}
    lane_status = (
        (lane_info.get("interactive") or {}).get("status") or lane_info.get("status")
        if budget_seat == "claude"
        else lane_info.get("status")
    )
    if (
        selected is None
        and snapshot is not None
        and lane_status in {"cool", "warm"}
        and not (lane_info.get("runtime") or {}).get("headroom_blocked")
    ):
        if eligible and seat == budget_seat:
            return seat, model
        # The initial admission may already have replaced a same-family request.
        # Recover that reviewer with the same snapshot and all hard gates intact.
        retained = resolve_reviewer(inputs, ladder=ladder).selected
        if retained is not None and retained.route == budget_seat:
            return retained.route, candidate_dispatch_model(REVIEW_CANDIDATES[retained.name])
    if selected is None or selected.family in forbidden:
        raise ReviewAdmissionRefused(
            f"REVIEW_ROUTE_REFUSED: no resolver-selected eligible substitute for --review-profile {profile}{risk_note}"
        )
    return selected.route, candidate_dispatch_model(REVIEW_CANDIDATES[selected.name])


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


def stored_kimi_request(recipients: Iterable[object], *, attachments: Iterable[Any] = ()) -> bool:
    """``stored_kimi_row`` for a stored request with several recipients or attachments (an authority job payload).

    True when any recipient, or any model or recipient key an attachment
    carries, is a Kimi seat or model. Same bridge-mode decision; for generic
    drains and sweeps only, never a delivery target.
    """
    names = tuple(str(item or "").strip() for item in recipients)
    try:
        resolve_and_admit(names, mode=BRIDGE_MODE, attachments=tuple(attachments))
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
