"""The Ukrainian review seats. Every gate reads this module and no other copy.

Operator order of 2026-10-30, recorded in
``agents_extensions/shared/skills/review-loop/references/ukrainian.md`` § Seats:

| Author families | Review of record |
| --- | --- |
| exactly ``openai`` | Gemini (``google``) |
| exactly ``google`` | Sol (``openai``) |
| any other set | Gemini and Sol |

No author gets a Claude seat. An unattested author is "any other".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

GEMINI = "google"
SOL = "openai"
# Families that can fill a Ukrainian seat. Anthropic is never one of them.
UKRAINIAN_SEAT_FAMILIES = frozenset({GEMINI, SOL})
# Harness and family of each seat. A Claude route is not a seat.
UKRAINIAN_SEAT_ROUTES = frozenset({("agy", GEMINI), ("codex", SOL)})


def required_ukrainian_seats(author_families: Iterable[str]) -> frozenset[str]:
    """The reviewer families that must approve a Ukrainian head for these authors."""
    authors = frozenset(author_families)
    if authors == frozenset({SOL}):
        return frozenset({GEMINI})
    if authors == frozenset({GEMINI}):
        return frozenset({SOL})
    return UKRAINIAN_SEAT_FAMILIES


def attested_author_families(markers: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """Author families named on these verdict markers.

    A missing, malformed or unresolved author is unattested, which requires both
    seats. The markers are the recorder's own comments, so the names are the
    models it wrote on ``Authored by``.

    The identity import stays inside this function. Catalog validation imports
    this module, and the freshness check does not install the runtime package.
    """
    from learn_ukrainian_v4_runtime.identity import (
        _VALID_CONCRETE_FAMILIES,
        UNKNOWN_AUTHOR_FAMILY,
        UNRESOLVED_AUTHOR_FAMILIES,
        resolve_author_family,
    )

    models: list[str] = []
    for marker in markers:
        # A missing or empty attestation is not "no extra authors". One blank
        # marker beside an attested one would otherwise drop the blank and
        # approve on a single seat.
        if "author_models" not in marker:
            return frozenset({UNKNOWN_AUTHOR_FAMILY})
        recorded = marker["author_models"]
        if not isinstance(recorded, (tuple, list)) or not recorded:
            return frozenset({UNKNOWN_AUTHOR_FAMILY})
        if not all(isinstance(model, str) and model for model in recorded):
            return frozenset({UNKNOWN_AUTHOR_FAMILY})
        models.extend(recorded)
    if not models:
        return frozenset({UNKNOWN_AUTHOR_FAMILY})
    families: set[str] = set()
    for model in models:
        family = resolve_author_family(model)
        if family in UNRESOLVED_AUTHOR_FAMILIES or family not in _VALID_CONCRETE_FAMILIES:
            return frozenset({UNKNOWN_AUTHOR_FAMILY})
        families.add(family)
    return frozenset(families)
