"""Deterministic fix-merger for dimensional wiki review.

Implements `docs/design/dimensional-review.md` §6c. The merger is a pure
Python function — NO LLM. Per ADR-001 (FROM-SCRATCH rewrites degraded
content 9.6→9.2→8.4), centralized generative patchers are banned. Each
dimensional reviewer emits surgical `<fixes>` localized to its dim; this
module composes them.

Contract:

    inputs:  list of (dim_name, fixes) — each fix has `find`/`replace`
    outputs: applied_fixes, conflicts, skipped_missing

Rules:

1. **Non-conflict** (unique `find:` string appearing in exactly one
   reviewer's fix list): apply as-is.
2. **Identical-replace conflict** (multiple dims propose the same
   `find:` → `replace:`): dedupe; apply once; crediting the
   highest-priority dim.
3. **Different-replace conflict** (multiple dims propose the same
   `find:` with different `replace:` values): resolve by dim priority
   (configurable; default `DEFAULT_DIM_PRIORITY`). A DIFFERENT_REPLACE
   `Conflict` is always emitted so losing proposals stay visible.
4. **Span-overlap conflict** (one fix's `find:` is a strict substring of
   another's): the LONGER `find:` wins (more context = more specific).
   A SPAN_OVERLAP `Conflict` is always emitted so shorter proposals
   that were discarded stay visible.
5. **Missing-find** (the winning fix's `find:` is not present in article
   text): skip; emit MISSING `Conflict`. Not fatal — a prior fix in the
   same round may have already removed or changed the text.
6. **Ambiguous-find** (the winning fix's `find:` appears MORE THAN ONCE
   in article text): skip; emit AMBIGUOUS `Conflict`. `str.replace(...,
   1)` would silently patch the first occurrence, which may not be the
   one the reviewer flagged. Reviewers should emit unique enough
   find-strings; when they don't, the merger refuses rather than
   corrupting the wrong span. Surfaced in adversarial review 2026-04-18.

Design §9 Q3 is still OPEN: the default priority list below is a
placeholder. User judgment on which error type is "worst" to ship has
not been collected. Callers may override via `dim_priority=`.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

# Default dim priority (highest first). Factual errors most concrete and
# user-impactful; source-grounding protects editorial integrity; register
# catches linguistic defects; perspective framing is often subjective.
# DESIGN §9 Q3: open for user resolution.
DEFAULT_DIM_PRIORITY: tuple[str, ...] = (
    "factual_accuracy",
    "source_grounding",
    "register",
    "ukrainian_perspective",
)


@dataclass(frozen=True)
class Fix:
    """A single find/replace fix proposed by a dimensional reviewer."""

    dim: str
    find: str
    replace: str

    def __post_init__(self) -> None:
        if not self.find:
            raise ValueError("Fix.find must be non-empty")
        # replace MAY be empty (deletion is legitimate)


@dataclass(frozen=True)
class Conflict:
    """A conflict the merger observed (whether resolvable or not)."""

    kind: str            # "DIFFERENT_REPLACE" | "SPAN_OVERLAP" | "MISSING"
    find: str
    dims: tuple[str, ...]
    proposals: tuple[tuple[str, str], ...]  # (dim, replace) pairs
    chosen: str | None   # Which dim won, if any; None if fully unresolvable
    reason: str


@dataclass(frozen=True)
class _Resolution:
    """Internal: the outcome of resolving one overlap group.

    `winner` is the Fix to apply (None means nothing to apply).
    `conflict` is the conflict record (None means no conflict was observed).
    The two fields are independent — a resolvable conflict has BOTH a
    winner and a conflict record.
    """

    winner: Fix | None
    conflict: Conflict | None


@dataclass
class MergeReport:
    applied: list[Fix] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    skipped_missing: list[Fix] = field(default_factory=list)

    @property
    def has_unresolvable_conflicts(self) -> bool:
        """True iff any conflict has chosen=None (genuine deadlock)."""
        return any(c.chosen is None for c in self.conflicts)


def merge_fixes(
    all_fixes: Iterable[Fix],
    article_text: str,
    *,
    dim_priority: tuple[str, ...] = DEFAULT_DIM_PRIORITY,
) -> MergeReport:
    """Group fixes by `find:` string, resolve conflicts, return a report.

    Does NOT apply fixes to `article_text` — returns which fixes should
    be applied. Callers apply them via `apply_fixes()` below. This
    separation lets the orchestrator log the merge outcome before
    mutating the article.

    Args:
        all_fixes: iterable of Fix objects from all dimensional reviewers
        article_text: the article text (used for MISSING detection and
            span-overlap resolution)
        dim_priority: tiebreaker order when multiple dims propose
            different replacements for the same find-string
    """
    priority_index = {dim: i for i, dim in enumerate(dim_priority)}
    report = MergeReport()

    by_find: dict[str, list[Fix]] = {}
    for fix in all_fixes:
        by_find.setdefault(fix.find, []).append(fix)

    overlap_groups = _group_by_span_overlap(list(by_find.keys()))

    for group in overlap_groups:
        if len(group) == 1:
            resolution = _resolve_same_find(by_find[group[0]], priority_index)
        else:
            resolution = _resolve_span_overlap(group, by_find, priority_index)

        if resolution.conflict is not None:
            report.conflicts.append(resolution.conflict)

        winner = resolution.winner
        if winner is None:
            continue

        occurrences = article_text.count(winner.find)
        if occurrences == 0:
            report.skipped_missing.append(winner)
            report.conflicts.append(Conflict(
                kind="MISSING",
                find=winner.find,
                dims=(winner.dim,),
                proposals=((winner.dim, winner.replace),),
                chosen=None,
                reason="find-string not present in article text",
            ))
        elif occurrences > 1:
            # str.replace(..., 1) would silently patch the FIRST occurrence,
            # which may not be the one the reviewer flagged. Refuse to
            # corrupt the wrong span; reviewer must re-emit with more
            # disambiguating context. Surfaced in adversarial review 2026-04-18.
            report.skipped_missing.append(winner)
            report.conflicts.append(Conflict(
                kind="AMBIGUOUS",
                find=winner.find,
                dims=(winner.dim,),
                proposals=((winner.dim, winner.replace),),
                chosen=None,
                reason=(
                    f"find-string appears {occurrences}× in article; "
                    "reviewer must include more context to disambiguate"
                ),
            ))
        else:
            report.applied.append(winner)

    return report


def _resolve_same_find(
    fixes: list[Fix],
    priority_index: dict[str, int],
) -> _Resolution:
    """Resolve multiple fixes with identical `find:` strings."""
    if len(fixes) == 1:
        return _Resolution(winner=fixes[0], conflict=None)

    # Dedupe identical (find, replace) pairs — may come from different dims
    by_replace: dict[str, list[Fix]] = {}
    for f in fixes:
        by_replace.setdefault(f.replace, []).append(f)

    if len(by_replace) == 1:
        # All dims agree on the replacement — credit the highest-priority dim
        agreeing = next(iter(by_replace.values()))
        winner = _highest_priority(agreeing, priority_index)
        return _Resolution(winner=winner, conflict=None)

    # Genuine different-replace conflict — apply priority
    winner = _highest_priority(fixes, priority_index)
    return _Resolution(
        winner=winner,
        conflict=Conflict(
            kind="DIFFERENT_REPLACE",
            find=fixes[0].find,
            dims=tuple(sorted({f.dim for f in fixes})),
            proposals=tuple((f.dim, f.replace) for f in fixes),
            chosen=winner.dim,
            reason=f"priority tiebreaker: {winner.dim} outranks others",
        ),
    )


def _group_by_span_overlap(find_strings: list[str]) -> list[list[str]]:
    """Group find-strings by substring containment.

    Two strings are in the same group iff one is a substring of the
    other. Overlap is transitive through containment so union-find
    correctly captures three-way chains (A ⊂ B ⊂ C).
    """
    if not find_strings:
        return []

    n = len(find_strings)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            a, b = find_strings[i], find_strings[j]
            if a == b:
                continue  # identical — handled by _resolve_same_find
            if a in b or b in a:
                union(i, j)

    groups: dict[int, list[str]] = {}
    for i, s in enumerate(find_strings):
        groups.setdefault(find(i), []).append(s)

    return list(groups.values())


def _resolve_span_overlap(
    group: list[str],
    by_find: dict[str, list[Fix]],
    priority_index: dict[str, int],
) -> _Resolution:
    """Resolve a span-overlap group — longest find wins.

    Always emits a SPAN_OVERLAP conflict even when the longest find has
    a unique proposer, so the shorter variants that were discarded
    remain visible in the report.
    """
    longest = max(group, key=len)
    longest_fixes = by_find[longest]
    all_proposals: list[tuple[str, str]] = [
        (f.dim, f.replace) for find_str in group for f in by_find[find_str]
    ]
    all_dims = tuple(sorted({dim for dim, _ in all_proposals}))

    # Delegate the "which fix on the longest" decision to _resolve_same_find.
    inner = _resolve_same_find(longest_fixes, priority_index)
    winner = inner.winner  # guaranteed non-None — there's at least one fix

    return _Resolution(
        winner=winner,
        conflict=Conflict(
            kind="SPAN_OVERLAP",
            find=longest,
            dims=all_dims,
            proposals=tuple(all_proposals),
            chosen=winner.dim if winner is not None else None,
            reason=(
                "span-overlap; longest find selected"
                + (
                    "; priority tiebreaker applied"
                    if inner.conflict is not None
                    else ""
                )
            ),
        ),
    )


def _highest_priority(fixes: list[Fix], priority_index: dict[str, int]) -> Fix:
    """Return the fix whose dim has the smallest priority_index."""
    return min(fixes, key=lambda f: priority_index.get(f.dim, 10_000))


def apply_fixes(article_text: str, fixes: list[Fix]) -> str:
    """Apply fixes to article text via sequential find/replace.

    Fixes are applied in order. Each `find:` is replaced on its FIRST
    occurrence only (using `str.replace(find, replace, 1)`) to avoid
    accidentally mass-replacing a common substring. Reviewers are
    instructed to emit unique enough `find:` strings that this is safe.

    If a fix's `find:` is not present at application time (e.g. a prior
    fix ate it), the fix is silently skipped — the upstream `merge_fixes`
    already surfaced MISSING conflicts.
    """
    out = article_text
    for fix in fixes:
        if fix.find in out:
            out = out.replace(fix.find, fix.replace, 1)
    return out
