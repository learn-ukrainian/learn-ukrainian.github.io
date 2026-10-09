"""One family-exclusion policy for routing roles and reviewer independence.

Role eligibility and author independence are distinct checks. Both live here;
no role resolver invents a second family policy or ranking engine.
"""

from __future__ import annotations


def family_exclusion(
    *,
    family: str,
    route: str,
    transport: str,
    risk: str | None = None,
    author_family: str | None = None,
    advisory_only_for_author_families: frozenset[str] = frozenset(),
    union_family: str = "",
    union_families: frozenset[str] = frozenset(),
) -> tuple[str, str] | None:
    """Return the unchanged role or author-family exclusion status and reason."""
    if author_family is None:
        if family in {"moonshot", "deepseek"}:
            return "excluded", "code-review family exclusions"
        if (family == "google" or route == "agy") and not (
            family == "google" and route == "agy" and transport == "agy" and risk in {"low", "medium"}
        ):
            return "excluded", "Gemini code review requires AGY at low/medium risk (#10073)"
        return None
    reviewer_family = family
    family = author_family
    cursor_transport = transport == "cursor" or route == "cursor"
    if family == union_family and cursor_transport:
        return (
            "excluded",
            "candidate uses Cursor transport — Cursor-as-reviewer is ineligible for Cursor-authored work",
        )
    if reviewer_family == family and family in advisory_only_for_author_families:
        return ("advisory_only", f"same family as author ({family}) — advisory-only, not a formal cross-family gate")
    if reviewer_family == family:
        return ("excluded", f"same family as author ({family}) — cross-family review requires a different family")
    if family in union_families and cursor_transport:
        return (
            "excluded",
            f"candidate uses Cursor transport — Cursor-as-reviewer is ineligible "
            f"against {family!r} author (within allowlist union {sorted(union_families)})",
        )
    return None
