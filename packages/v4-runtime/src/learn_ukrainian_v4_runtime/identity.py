"""Shared harness and model family identity; no routing or subprocess dependency."""

from learn_ukrainian_v4_runtime import model_families
from learn_ukrainian_v4_runtime.agent_identity import normalize_seat, tools_writer_runtime_agent

KNOWN_HARNESS_EXECUTABLES = frozenset({"claude", "codex", "agy", "kimi", "cursor", "opencode", "hermes"})


def resolve_family(seat_or_model: str) -> str:
    """Resolve a seat/CLI-alias/model-id string to its model family.

    Returns ``"unknown"`` for anything unrecognized — callers must not treat
    unknown as any specific family (including the author's own), since that
    would either wrongly admit or wrongly exclude a candidate.
    """
    normalized = (seat_or_model or "").strip().lower()
    if not normalized:
        return "unknown"

    canonical = normalize_seat(normalized) or normalized

    if canonical.endswith("-tools"):
        base = tools_writer_runtime_agent(canonical)
        canonical = base

    family = model_families.normalize_family(canonical)
    if family in {model_families.Family.UNKNOWN, model_families.Family.FIXTURE}:
        return UNKNOWN_AUTHOR_FAMILY
    return family.value


# --- ambiguous-harness / fail-closed author identity --------------------------

# Harnesses that route to more than one underlying model family depending on
# per-session configuration — the harness name alone is NOT a model family.
# Cursor is multi-model (a session may run GPT, Claude, or another model
# underneath); resolving it to a synthetic "cursor" family would let an
# author dodge the cross-family requirement whenever the real underlying
# model happens to collide with whatever the ladder picks.
AMBIGUOUS_HARNESS_SEATS: frozenset[str] = frozenset({"cursor", "cursor-tools"})

# Concrete model-vendor families a caller may assert via an explicit
# ``author_family`` override. Deliberately excludes harness pseudo-families
# (nothing routes to "cursor" as if it were a vendor) and the fail-closed
# sentinels below — an override must name a real family or be rejected.
_VALID_CONCRETE_FAMILIES: frozenset[str] = frozenset(
    family.value
    for family in model_families.Family
    if family not in {model_families.Family.UNKNOWN, model_families.Family.FIXTURE}
)

# Fail-closed author-identity outcomes: none of these is a real model family,
# and a caller must never treat one as matching (or not matching) any
# candidate's family — resolve_reviewer refuses to select a formal reviewer
# for any of them. The unattested-harness sentinel is still unresolved (no
# single-reviewer selection is possible against it), but unlike the others it
# resolves to a dual-family quorum plan instead of a bare refusal.
UNKNOWN_AUTHOR_FAMILY = "unknown"
AMBIGUOUS_AUTHOR_FAMILY = "ambiguous"
CONFLICTING_AUTHOR_FAMILY = "conflict"
UNATTESTED_AUTHOR_FAMILY = "unattested-harness"
UNRESOLVED_AUTHOR_FAMILIES: frozenset[str] = frozenset(
    {UNKNOWN_AUTHOR_FAMILY, AMBIGUOUS_AUTHOR_FAMILY, CONFLICTING_AUTHOR_FAMILY, UNATTESTED_AUTHOR_FAMILY}
)

# Cursor Auto union-family resolution (#6952, #6955):
# When Cursor runs in Auto mode with an unknown / unattested resolved model
# (model="auto", resolved_model=null or "unknown"), its author identity resolves
# to the allowlist-union family {xAI, Moonshot}. Cursor-authored PRs require a
# single cross-family reviewer from outside {xAI, Moonshot} (no quorum needed).
# Cursor-as-reviewer is ineligible against authors in {xAI, Moonshot}.
CURSOR_AUTO_UNION_FAMILY = "cursor-auto-union"
CURSOR_AUTO_UNION_FAMILIES: frozenset[str] = frozenset({"xai", "moonshot"})
CURSOR_AUTO_MODEL_TOKENS: frozenset[str] = frozenset({"auto", "unknown", "unattested-harness"})
CURSOR_AUTO_HARNESS_SEATS: frozenset[str] = frozenset(
    {"cursor-auto", "cursor-auto-unknown", "cursor-auto-unattested-harness"}
)

UNATTESTED_MODEL_TOKENS: frozenset[str] = frozenset({"auto"})
UNATTESTED_HARNESS_SEATS: frozenset[str] = frozenset({"cursor-auto"})


def resolve_author_family(author_model: str, author_family: str | None = None) -> str:
    """Resolve the author's model family, failing closed for ambiguous harnesses.

    ``author_model`` is either a concrete seat/model id (resolved exactly as
    :func:`resolve_family` always has), or a ``"<harness>:<concrete-model>"``
    composite for a multi-model harness (e.g. ``"cursor:gpt-5.6-sol"``,
    ``"cursor:claude-opus-4-8"``) that disambiguates which model that harness
    session actually ran. ``author_family`` is an optional explicit,
    caller-asserted family (e.g. from session logs) used to corroborate or,
    for a bare ambiguous-harness identity with no embedded model, to supply
    the disambiguation on its own.

    Cursor Auto / unknown-Auto (``"cursor:auto"``, ``"cursor:unknown"``,
    ``"cursor-auto"``) resolves to the allowlist-union family
    ``CURSOR_AUTO_UNION_FAMILY`` ({xAI, Moonshot}), requiring a single
    cross-family reviewer from outside {xAI, Moonshot}. A caller-asserted
    single family override against Auto attestation is a fail-closed conflict.

    Returns a concrete family string, or one of the sentinels:

    - ``"unknown"`` — no usable identity signal at all.
    - ``"ambiguous"`` — a multi-model harness with no concrete model and no
      valid override to disambiguate it.
    - ``"conflict"`` — the embedded/resolved model family and an explicit
      ``author_family`` override disagree, or an override was declared
      against a positive no-pinned-model (auto) attestation.
    - ``"cursor-auto-union"`` — Cursor Auto with unknown resolved_model,
      resolving to union-family {xAI, Moonshot}.
    - ``"unattested-harness"`` — generic unattested multi-model harness.

    Callers (:func:`resolve_reviewer`) must never select a formal reviewer
    against a fail-closed sentinel — an unresolved author identity is not
    evidence that a candidate is (or isn't) the same family.
    """
    normalized = (author_model or "").strip().lower()
    override = (author_family or "").strip().lower() or None
    if override is not None and override not in _VALID_CONCRETE_FAMILIES:
        override = None  # an invalid/unrecognized override does not count as validated

    harness_token, sep, embedded = normalized.partition(":")
    embedded_token = embedded.strip()
    if (sep and harness_token in AMBIGUOUS_HARNESS_SEATS and embedded_token in CURSOR_AUTO_MODEL_TOKENS) or (
        normalized in CURSOR_AUTO_HARNESS_SEATS
    ):
        # The harness attests the model was Auto/unattested; a caller-asserted
        # single family contradicts that attestation instead of resolving it.
        return CONFLICTING_AUTHOR_FAMILY if override else CURSOR_AUTO_UNION_FAMILY
    if sep and harness_token in AMBIGUOUS_HARNESS_SEATS and embedded_token:
        resolved = resolve_family(embedded_token)
    elif normalized in AMBIGUOUS_HARNESS_SEATS or (normalize_seat(normalized) or "") in AMBIGUOUS_HARNESS_SEATS:
        resolved = None  # bare ambiguous harness, no embedded concrete model
    else:
        resolved = resolve_family(normalized)

    if resolved is None:
        # Bare ambiguous harness: only a validated override can disambiguate it.
        return override if override else AMBIGUOUS_AUTHOR_FAMILY
    if resolved == "unknown":
        return override if override else UNKNOWN_AUTHOR_FAMILY
    if override and override != resolved:
        return CONFLICTING_AUTHOR_FAMILY
    return resolved
