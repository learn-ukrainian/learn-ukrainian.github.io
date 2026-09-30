"""Subject-seat exclusion for formal reviewer selection.

A change that governs a seat (its adapter, or that seat's reviewer hooks)
must not be formally reviewed by that seat. Callers name the seat or family
directly, or pass owned paths. Unambiguous adapter and hook paths infer one
seat. A path that belongs to more than one seat, or to a shared adapter
surface, is ambiguous: inference stops and the caller must pass
``--subject-seat`` or ``--subject-family``. Guessing a seat is refused.

Omitting seats, families, and owned paths is not an inference. Selection
stays on the ordinary author-family ladder.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal, Protocol

from learn_ukrainian_v4_runtime.agent_identity import normalize_seat
from learn_ukrainian_v4_runtime.identity import _VALID_CONCRETE_FAMILIES

ClassificationKind = Literal["seat", "ambiguous", "unrelated"]

# Registry and catalog aliases that name one subject seat. Family names are
# intentionally absent — those belong on --subject-family.
_SUBJECT_ALIASES: dict[str, str] = {
    "grok-build": "grok",
    "grok-hermes": "grok",
    "hermes-grok": "grok",
    "grok-4.7": "grok",
    "grok-4.6": "grok",
    "grok-4.5": "grok",
    "grok-4.7-cursor-fallback": "grok",
    "hermes-deepseek": "deepseek",
    "kimicc": "kimi",
    "kimi-k3": "kimi",
    "kimi-code/k3": "kimi",
    "claude-desktop": "claude",
    "claude-infra": "claude",
    "claude-monitor": "claude",
    "codex-desktop": "codex",
}

# Reviewer-hook paths that govern exactly one seat. Shared hooks are listed
# separately so inference fails closed instead of picking one consumer.
_HOOK_SEATS: dict[str, str] = {
    "scripts/agent_runtime/grok_hook_bridge.py": "grok",
    "scripts/hooks/apply_grok_hook_profile.py": "grok",
    "scripts/agent_runtime/profiles/acpx-grok-read-only.md": "grok",
    "scripts/agent_runtime/profiles/acpx-grok-sealed-review.md": "grok",
    "scripts/agent_runtime/codex_hook_entry.sh": "codex",
    "scripts/agent_runtime/codex_hook_policy.py": "codex",
    "scripts/agent_runtime/codex_hook_probe.py": "codex",
    "agents_extensions/codex/hooks.json": "codex",
}

_AMBIGUOUS_PATHS = frozenset(
    {
        "agents_extensions/shared/hooks/guard-reviewer-publish.py",
    }
)

_AMBIGUOUS_PREFIXES = (
    "scripts/agent_runtime/hermes_hooks/",
)

_ADAPTER_PREFIX = "scripts/agent_runtime/adapters/"


class _SeatCandidate(Protocol):
    name: str
    family: str
    concrete_model: str
    route: str
    transport: str


def _matches_grok(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    route = candidate.route.casefold()
    return route in {"grok", "grok-hermes"} or name.startswith("grok") or model.startswith("grok")


def _matches_claude(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "claude" or name.startswith("claude") or model.startswith("claude")


def _matches_codex(candidate: _SeatCandidate) -> bool:
    return candidate.route.casefold() == "codex" or candidate.family.casefold() == "openai"


def _matches_cursor(candidate: _SeatCandidate) -> bool:
    return candidate.route.casefold() == "cursor" or candidate.transport.casefold() == "cursor"


def _matches_kimi(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() in {"kimi", "kimicc"} or name.startswith("kimi") or model.startswith("kimi")


def _matches_deepseek(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "deepseek" or name.startswith("deepseek") or model.startswith("deepseek")


def _matches_glm(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "glm" or name.startswith("glm") or model.startswith("glm")


def _matches_qwen(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "qwen" or "qwen" in name or "qwen" in model or candidate.family.casefold() == "qwen"


def _matches_pool(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "pool" or name.startswith("pool") or "poolside" in model or "laguna" in model


def _matches_agy(candidate: _SeatCandidate) -> bool:
    return candidate.route.casefold() == "agy" or candidate.name.casefold().startswith("agy")


def _matches_gemini(candidate: _SeatCandidate) -> bool:
    # The agy route runs Gemini models on a different adapter. A gemini.py
    # change does not by itself govern that seat.
    return candidate.route.casefold() == "gemini" or (
        candidate.concrete_model.casefold().startswith("gemini") and candidate.route.casefold() != "agy"
    )


def _matches_gemma(candidate: _SeatCandidate) -> bool:
    name = candidate.name.casefold()
    model = candidate.concrete_model.casefold()
    return candidate.route.casefold() == "gemma" or "gemma" in name or "gemma" in model


_MATCHERS: dict[str, Callable[[_SeatCandidate], bool]] = {
    "agy": _matches_agy,
    "claude": _matches_claude,
    "codex": _matches_codex,
    "cursor": _matches_cursor,
    "deepseek": _matches_deepseek,
    "gemini": _matches_gemini,
    "gemma": _matches_gemma,
    "glm": _matches_glm,
    "grok": _matches_grok,
    "kimi": _matches_kimi,
    "pool": _matches_pool,
    "qwen": _matches_qwen,
}

KNOWN_SUBJECT_SEATS = frozenset(_MATCHERS)


@dataclass(frozen=True)
class OwnedPathClassification:
    kind: ClassificationKind
    seats: frozenset[str]
    detail: str


@dataclass(frozen=True)
class SubjectExclusion:
    seats: frozenset[str]
    families: frozenset[str]
    evidence: tuple[str, ...]
    fail_closed_reason: str | None = None


def normalize_owned_path(path: str) -> str:
    """Return a repo-relative posix path, keeping the adapter/hook suffix."""
    text = str(path).strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    text = text.rstrip("/")
    for marker in (_ADAPTER_PREFIX, "scripts/agent_runtime/", "scripts/hooks/", "agents_extensions/"):
        index = text.find(marker)
        if index >= 0:
            return text[index:]
    return text


def canonical_subject_seat(registry_name: str) -> str:
    """Collapse a registry agent id to the seat a reviewer candidate matches."""
    seat = (normalize_seat(registry_name) or registry_name).strip().casefold()
    prefix = "acpx-"
    suffix = "-shadow"
    if seat.startswith(prefix) and seat.endswith(suffix):
        seat = seat[len(prefix) : -len(suffix)]
    return _SUBJECT_ALIASES.get(seat, seat)


@lru_cache(maxsize=1)
def adapter_subject_index() -> Mapping[str, frozenset[str]]:
    """Map ``scripts/agent_runtime/adapters/<file>.py`` to the seats that own it.

    Built from the agent registry so a new per-seat adapter is classified
    without a second hand-written ladder. ``kimicc.py`` is the Kimi Claude Code
    harness; the registry names the seat ``kimi`` and points the
    dispatch adapter at ``kimi.py``.
    """
    from scripts.agent_runtime.registry import AGENTS

    by_file: dict[str, set[str]] = {}
    for name, entry in AGENTS.items():
        module = str(entry["adapter"]).split(":", 1)[0]
        filename = module.rsplit(".", 1)[-1] + ".py"
        rel = f"{_ADAPTER_PREFIX}{filename}"
        by_file.setdefault(rel, set()).add(canonical_subject_seat(name))
    by_file.setdefault(f"{_ADAPTER_PREFIX}kimicc.py", set()).add("kimi")
    return {path: frozenset(seats) for path, seats in by_file.items()}


def classify_owned_path(path: str) -> OwnedPathClassification:
    """Classify one owned path as one seat, ambiguous, or unrelated.

    Unrelated paths (a README, a generic timing hook) do not imply a subject
    seat. Ambiguous paths must not be turned into a guess.
    """
    rel = normalize_owned_path(path)
    hooked = _HOOK_SEATS.get(rel)
    if hooked is not None:
        return OwnedPathClassification("seat", frozenset({hooked}), hooked)
    ambiguous_prefix = any(
        rel.startswith(prefix) or rel == prefix.rstrip("/") for prefix in _AMBIGUOUS_PREFIXES
    )
    if rel in _AMBIGUOUS_PATHS or ambiguous_prefix:
        return OwnedPathClassification("ambiguous", frozenset(), "shared reviewer-hook surface")
    if rel.startswith(_ADAPTER_PREFIX) and rel.endswith(".py"):
        seats = adapter_subject_index().get(rel)
        if seats is None or len(seats) != 1 or not seats <= KNOWN_SUBJECT_SEATS:
            listed = ", ".join(sorted(seats)) if seats else "shared adapter surface"
            return OwnedPathClassification("ambiguous", frozenset(seats or ()), listed)
        seat = next(iter(seats))
        return OwnedPathClassification("seat", frozenset({seat}), seat)
    return OwnedPathClassification("unrelated", frozenset(), "not a per-seat adapter or reviewer hook")


def normalize_subject_seat(raw: str) -> str:
    """Validate an explicit subject seat. Unknown tokens fail closed."""
    text = str(raw).strip().casefold().replace("_", "-")
    if not text:
        raise ValueError("subject seat must be a non-empty seat id (example: grok)")
    text = (normalize_seat(text) or text).casefold()
    text = _SUBJECT_ALIASES.get(text, text)
    if text not in KNOWN_SUBJECT_SEATS:
        known = ", ".join(sorted(KNOWN_SUBJECT_SEATS))
        raise ValueError(
            f"unknown subject seat {raw!r}; expected one of {known} "
            "(or a documented alias such as grok-build or grok-4.7)"
        )
    return text


def normalize_subject_family(raw: str) -> str:
    """Validate an explicit subject family against the concrete family vocabulary."""
    text = str(raw).strip().casefold()
    if not text:
        raise ValueError("subject family must be a non-empty family id (example: xai)")
    if text not in _VALID_CONCRETE_FAMILIES:
        known = ", ".join(sorted(_VALID_CONCRETE_FAMILIES))
        raise ValueError(f"unknown subject family {raw!r}; expected one of {known}")
    return text


def prepare_subject_exclusion(
    *,
    subject_seats: frozenset[str] = frozenset(),
    subject_families: frozenset[str] = frozenset(),
    owned_paths: tuple[str, ...] = (),
) -> SubjectExclusion:
    """Resolve explicit seats/families plus unambiguous owned paths.

    An ambiguous owned path fails closed when the caller did not also pass an
    explicit seat or family. Explicit input is the required argument from the
    stop policy; inference does not add a guessed seat for that path.
    """
    explicit_requested = any(str(seat).strip() for seat in subject_seats) or any(
        str(family).strip() for family in subject_families
    )
    try:
        seats = {normalize_subject_seat(seat) for seat in subject_seats}
        families = {normalize_subject_family(family) for family in subject_families}
    except ValueError as exc:
        return SubjectExclusion(frozenset(), frozenset(), (), str(exc))

    evidence: list[str] = []
    ambiguous: list[str] = []
    for raw_path in owned_paths:
        classification = classify_owned_path(raw_path)
        rel = normalize_owned_path(raw_path)
        if classification.kind == "seat":
            seats.update(classification.seats)
            evidence.append(rel)
        elif classification.kind == "ambiguous":
            ambiguous.append(f"{rel} ({classification.detail})")
    if ambiguous and not explicit_requested:
        joined = "; ".join(sorted(ambiguous))
        return SubjectExclusion(
            frozenset(),
            frozenset(),
            (),
            (
                f"ambiguous subject-seat inference for {joined} — "
                "pass --subject-seat or --subject-family; refusing to guess"
            ),
        )
    return SubjectExclusion(frozenset(seats), frozenset(families), tuple(sorted(set(evidence))))


def candidate_matches_subject_seat(candidate: _SeatCandidate, seat: str) -> bool:
    matcher = _MATCHERS.get(seat)
    if matcher is None:
        return False
    return matcher(candidate)


def subject_exclusion_reason(
    candidate: _SeatCandidate,
    *,
    seats: frozenset[str],
    families: frozenset[str],
    evidence: tuple[str, ...] = (),
) -> str | None:
    """Return the trace reason when ``candidate`` is a governed seat, else None."""
    if not seats and not families:
        return None
    matched_seats = [seat for seat in sorted(seats) if candidate_matches_subject_seat(candidate, seat)]
    matched_families = [family for family in sorted(families) if candidate.family.casefold() == family]
    if not matched_seats and not matched_families:
        return None
    parts: list[str] = []
    if matched_seats:
        parts.append("subject seat " + ",".join(matched_seats))
    if matched_families:
        parts.append("subject family " + ",".join(matched_families))
    where = f" paths={','.join(evidence)}" if evidence else ""
    return (
        f"subject exclusion: {candidate.name} cannot review a change that governs "
        f"its own boundary ({'; '.join(parts)}{where})"
    )
