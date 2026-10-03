"""Deterministic span-level scoring of review answers, writing metrics and judge tallies.

Review scoring contract (``common.SCORING_VERSION``; designated decision on
#9623, 2026-10-03; documented in ``docs/evaluations/uk-preamble.md``). The
answer's ``corrected_text`` is the only evidence of what the model changed. Its
``corrections`` are claims: they never create, split or merge a counted unit.

- Tokens: ``common.tokenize`` (NFC; apostrophe variants, U+2010/U+2011 and
  ``…`` folded; format characters deleted; whitespace is never a token;
  case-sensitive).
- One canonical alignment (``align``) of the original's tokens to the corrected
  text's tokens, computed without looking at seeds, protected spans or claims.
- Hits. Seeds with no correct token between them form a cluster, and its window
  runs between the nearest correct tokens aligned as unchanged on either side.
  When the corrected window equals the original window with every seed in it
  given an accepted form or left as it was, the seeds that take an accepted form
  in every such assignment are hits and nothing else in the window counts.
  Otherwise each seed is a hit when its slice (the target tokens aligned to it
  plus insertions strictly inside it; for an empty seed, the insertions at its
  point) equals an accepted form, trying no edge insertion, then the left one,
  the right one, then both; an edge insertion is used only when that match
  needs it. A seed changed but not hit is a wrong correction: a miss, never a
  false alarm.
- False alarms (the primary units): each protected span affected once (one of
  its tokens changed or an insertion strictly inside it); each changed correct
  token outside protected spans once; each other insertion site once (an
  insertion at a protected span's edge is an ordinary site).
- Logging diagnostics, never part of adoption: changed units some claim covers,
  claims the corrected text applies, unapplied, no-op and unanchored claims,
  protected spans a claim accuses that stay unchanged, and the tokens inserted
  at false-alarm sites.
- Style suggestions are tallied separately and never count as hits or false
  alarms. A failed item (no answer, malformed answer, or a task that was not
  run or not accepted) keeps its errors in the denominator as misses.
"""

from __future__ import annotations

import bisect
import functools
import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from .common import CEFR_LEVELS, ResultsDir, cyrillic_words, fold_apostrophes, latin_words, token_keys
from .dataset import EvalSet, Geometry, ReviewItem, Span, TokenSpan, WritingTask, review_geometry
from .prompts import JUDGE_CRITERIA, validate_response
from .runner import Slot, TaskSpec, load_raw, valid_entries

# --------------------------------------------------------------------------- canonical alignment

TIE_ORDER = ("equal", "delete", "insert", "substitute")


@dataclass(frozen=True)
class Op:
    """One alignment step from source token ``i`` and target token ``j``.

    ``equal`` and ``substitute`` consume both tokens, ``delete`` consumes source
    token ``i`` and ``insert`` consumes target token ``j`` at the source boundary
    before token ``i``.
    """

    tag: str
    i: int
    j: int


@functools.lru_cache(maxsize=1 << 16)
def char_distance(a: str, b: str) -> int:
    """Levenshtein distance between two tokens (unit-cost insert, delete and substitute)."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for x, char_a in enumerate(a, 1):
        current = [x]
        for y, char_b in enumerate(b, 1):
            current.append(min(previous[y] + 1, current[y - 1] + 1, previous[y - 1] + (char_a != char_b)))
        previous = current
    return previous[-1]


def align(source: Sequence[str], target: Sequence[str]) -> list[Op]:
    """The canonical alignment of source token keys to target token keys.

    Cost is lexicographic: first the number of token edits (a delete, insert or
    substitute counts one; an equal pair, allowed only for identical keys, zero),
    then the character edits (a substitution costs the Levenshtein distance of
    its two tokens, a deletion or insertion the token's length). Among
    minimum-cost alignments the path is fixed by forward reconstruction from the
    start: each step takes the first admissible operation in ``TIE_ORDER``.

    The result depends only on the two key sequences, never on seeds, protected
    spans, claims or any random state. ``difflib`` is deliberately not used: its
    longest-matching-block heuristic is not a minimum-cost alignment.
    """
    n, m = len(source), len(target)
    # One token edit outweighs every possible character cost (each token is used at most once).
    edit = sum(map(len, source)) + sum(map(len, target)) + 1
    # cost[i][j]: the cheapest alignment of source[i:] to target[j:], as edits * edit + characters.
    cost = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        cost[i][m] = cost[i + 1][m] + edit + len(source[i])
    for j in range(m - 1, -1, -1):
        cost[n][j] = cost[n][j + 1] + edit + len(target[j])
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            if source[i] == target[j]:
                pair = cost[i + 1][j + 1]
            else:
                pair = cost[i + 1][j + 1] + edit + char_distance(source[i], target[j])
            cost[i][j] = min(pair, cost[i + 1][j] + edit + len(source[i]), cost[i][j + 1] + edit + len(target[j]))
    ops: list[Op] = []
    i = j = 0
    while i < n or j < m:
        here = cost[i][j]
        if i < n and j < m and source[i] == target[j] and cost[i + 1][j + 1] == here:
            ops.append(Op("equal", i, j))
            i, j = i + 1, j + 1
        elif i < n and cost[i + 1][j] + edit + len(source[i]) == here:
            ops.append(Op("delete", i, j))
            i += 1
        elif j < m and cost[i][j + 1] + edit + len(target[j]) == here:
            ops.append(Op("insert", i, j))
            j += 1
        else:
            ops.append(Op("substitute", i, j))
            i, j = i + 1, j + 1
    return ops


class Alignment:
    """The canonical alignment of one paragraph's tokens to one corrected text, indexed for slicing."""

    def __init__(self, source: Sequence[str], target: Sequence[str]) -> None:
        self.target = tuple(target)
        self.mapped: list[int | None] = [None] * len(source)  # target token of each kept source token
        self.equal = [False] * len(source)
        self.runs: dict[int, tuple[int, ...]] = {}  # source boundary -> target tokens inserted there
        for op in align(source, target):
            if op.tag == "insert":
                self.runs[op.i] = (*self.runs.get(op.i, ()), op.j)
            elif op.tag != "delete":
                self.mapped[op.i] = op.j
                self.equal[op.i] = op.tag == "equal"

    def run(self, k: int) -> tuple[str, ...]:
        return tuple(self.target[j] for j in self.runs.get(k, ()))

    def slice(self, i1: int, i2: int) -> tuple[str, ...]:
        """Target tokens aligned to source tokens [i1, i2) plus insertions strictly inside; the point's for i1 == i2."""
        if i1 == i2:
            return self.run(i1)
        out: list[str] = []
        for k in range(i1, i2):
            if k > i1:
                out.extend(self.run(k))
            if self.mapped[k] is not None:
                out.append(self.target[self.mapped[k]])
        return tuple(out)

    def window(self, left: int, right: int) -> tuple[str, ...]:
        """Target tokens strictly between source tokens ``left`` and ``right`` (aligned as equal; -1/len = the ends)."""
        j1 = self.mapped[left] + 1 if left >= 0 else 0  # type: ignore[operator]
        j2 = self.mapped[right] if right < len(self.mapped) else len(self.target)
        return self.target[j1:j2]

    def realise(
        self, i1: int, i2: int, forms: Collection[tuple[str, ...]], edges: Collection[int]
    ) -> tuple[int, ...] | None:
        """The edge insertions the slice of [i1, i2) needs to equal one of ``forms``, or None.

        Tries no edge insertion, then the left one, the right one, then both, and
        stops at the first match; only boundaries in ``edges`` may be used.
        """
        core = self.slice(i1, i2)
        tries: list[tuple[int, ...]] = [()]
        if i1 < i2:
            tries += [(k,) for k in (i1, i2) if k in edges]
            if i1 in edges and i2 in edges:
                tries.append((i1, i2))
        for used in tries:
            left = self.run(i1) if i1 in used else ()
            right = self.run(i2) if i2 in used else ()
            if (*left, *core, *right) in forms:
                return used
        return None


# --------------------------------------------------------------------------- review: primary counts


Segment = tuple[tuple[tuple[str, ...], ...], str | None]  # (options, seed id or None)


def _window_hits(segments: Sequence[Segment], target: Sequence[str]) -> frozenset[str] | None:
    """Seeds credited by an exact window match, or None when no assignment matches.

    ``segments`` run in source order as (options, seed id): a correct token has
    its own key as the only option; a seed has its own tokens first, then its
    accepted forms. A seed is credited when every assignment that reproduces
    ``target`` gives it an accepted form (computed by forward and backward
    reachability, so no assignment is enumerated and none is preferred).
    """
    target = tuple(target)
    count = len(segments)

    def fits(p: int, option: tuple[str, ...]) -> bool:
        return target[p : p + len(option)] == option

    forward: list[set[int]] = [{0}] + [set() for _ in segments]
    for s, (options, _) in enumerate(segments):
        forward[s + 1] = {p + len(o) for p in forward[s] for o in options if fits(p, o)}
    if len(target) not in forward[count]:
        return None
    backward: list[set[int]] = [set() for _ in segments] + [{len(target)}]
    for s in range(count - 1, -1, -1):
        options = segments[s][0]
        backward[s] = {p for p in forward[s] if any(fits(p, o) and p + len(o) in backward[s + 1] for o in options)}
    credited = set()
    for s, (options, seed) in enumerate(segments):
        own = options[0]
        if seed is not None and not any(fits(p, own) and p + len(own) in backward[s + 1] for p in backward[s]):
            credited.add(seed)
    return frozenset(credited)


def _segments(geo: Geometry, left: int, right: int, seeds: Sequence[TokenSpan]) -> list[Segment]:
    """The window between source tokens ``left`` and ``right`` as segments in source order.

    An empty seed at a boundary comes before the token (or seed) that starts there.
    """
    keys = geo.keys
    starting: dict[int, list[TokenSpan]] = {}
    for seed in sorted(seeds, key=lambda s: (s.i1, s.i2)):
        starting.setdefault(seed.i1, []).append(seed)
    segments: list[Segment] = []
    k = left + 1
    while True:
        here = starting.get(k, [])
        for seed in here:
            if seed.i1 == seed.i2:
                segments.append((((), *geo.accepted[seed.span.id]), seed.span.id))
        if k >= right:
            return segments
        seed = next((s for s in here if s.i2 > s.i1), None)
        if seed is None:
            segments.append((((keys[k],),), None))
            k += 1
        else:
            segments.append(((keys[seed.i1 : seed.i2], *geo.accepted[seed.span.id]), seed.span.id))
            k = seed.i2


@dataclass(frozen=True)
class ReviewCounts:
    """The primary review counts of one corrected text; claims never enter them."""

    hits: frozenset[str]
    wrong: frozenset[str]  # seeds changed but not hit: misses
    protected: frozenset[str]  # protected spans affected
    tokens: frozenset[int]  # changed correct source tokens outside protected spans
    insertions: frozenset[int]  # extra insertion sites (source boundaries)
    inserted_tokens: int  # tokens inserted at false-alarm sites (diagnostic)
    geometry: Geometry = field(repr=False, compare=False)
    alignment: Alignment = field(repr=False, compare=False)

    @property
    def false_alarms(self) -> int:
        return len(self.protected) + len(self.tokens) + len(self.insertions)


def review_counts(item: ReviewItem, corrected_text: str) -> ReviewCounts:
    """Hits, wrong corrections and false-alarm units from the two texts alone (see the module docstring)."""
    geo = review_geometry(item)
    n = len(geo.tokens)
    alignment = Alignment(geo.keys, token_keys(corrected_text))
    seed_tokens = {t for seed in geo.seeds for t in range(seed.i1, seed.i2)}
    # Insertion points that belong to a seed: strictly inside it, or an empty seed's own point.
    owned = {k for seed in geo.seeds for k in (range(seed.i1 + 1, seed.i2) if seed.i1 < seed.i2 else (seed.i1,))}
    anchors = [t for t in range(n) if alignment.equal[t] and t not in seed_tokens]

    windows: dict[tuple[int, int], list[TokenSpan]] = {}
    for cluster in geo.clusters:
        first, end = cluster[0].i1, max(seed.i2 for seed in cluster)
        lo, hi = bisect.bisect_left(anchors, first), bisect.bisect_left(anchors, end)
        left = anchors[lo - 1] if lo else -1
        right = anchors[hi] if hi < len(anchors) else n
        windows.setdefault((left, right), []).extend(cluster)

    hits: set[str] = set()
    wrong: set[str] = set()
    explained_tokens: set[int] = set()
    explained_points: set[int] = set()
    unmatched: list[TokenSpan] = []
    for (left, right), seeds in sorted(windows.items()):
        credited = _window_hits(_segments(geo, left, right, seeds), alignment.window(left, right))
        if credited is None:
            unmatched += seeds
            continue
        hits |= credited
        explained_tokens.update(range(left + 1, right))
        explained_points.update(range(left + 1, right + 1))

    consumed: set[int] = set()
    for seed in sorted(unmatched, key=lambda s: (s.i1, s.i2)):
        edges = {k for k in (seed.i1, seed.i2) if k in alignment.runs and k not in owned | consumed}
        used = alignment.realise(seed.i1, seed.i2, geo.accepted[seed.span.id], edges)
        if used is not None:
            hits.add(seed.span.id)
            consumed.update(used)
        elif alignment.slice(seed.i1, seed.i2) != geo.keys[seed.i1 : seed.i2]:
            wrong.add(seed.span.id)

    protected: set[str] = set()
    tokens: set[int] = set()
    insertions: set[int] = set()
    inserted = 0
    for t in range(n):
        if alignment.equal[t] or t in seed_tokens or t in explained_tokens:
            continue
        spans = {p.span.id for p in geo.protected if p.i1 <= t < p.i2}
        if spans:
            protected |= spans
        else:
            tokens.add(t)
    for k, run in alignment.runs.items():
        if k in owned or k in consumed or k in explained_points:
            continue
        spans = {p.span.id for p in geo.protected if p.i1 < k < p.i2}
        if spans:
            protected |= spans
        else:
            insertions.add(k)
        inserted += len(run)
    return ReviewCounts(
        frozenset(hits),
        frozenset(wrong),
        frozenset(protected),
        frozenset(tokens),
        frozenset(insertions),
        inserted,
        geo,
        alignment,
    )


# --------------------------------------------------------------------------- review: logging diagnostics

LOGGING_KEYS = (
    "change_units",
    "claimed_change_units",
    "claims",
    "applied_claims",
    "unapplied_claims",
    "noop_claims",
    "unanchored_claims",
    "protected_accused_unchanged",
)


def resolve_span(text: str, span: str, start: Any, end: Any) -> tuple[int, int] | None:
    """Anchor a model-reported span in the original text, or None."""
    folded_text, folded_span = fold_apostrophes(text), fold_apostrophes(span)
    if (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start <= end <= len(text)
        and folded_text[start:end] == folded_span
    ):
        return start, end
    if not span:
        return None
    hits = [m.start() for m in re.finditer(re.escape(folded_span), folded_text)]
    if not hits:
        return None
    anchor = start if isinstance(start, int) else 0
    best = min(hits, key=lambda pos: (abs(pos - anchor), pos))
    return best, best + len(span)


def _token_range(geo: Geometry, start: int, end: int) -> tuple[int, int]:
    """Source tokens a claim over characters [start, end) covers.

    An empty claim covers the tokens it touches, because its text joins them
    (``r`` inserted after ``safe`` claims ``safer``); a claim that covers or
    touches no token is the boundary at its position.
    """
    if start == end:
        covered = [t for t, token in enumerate(geo.tokens) if token.start <= start <= token.end]
    else:
        covered = [t for t, token in enumerate(geo.tokens) if token.start < end and start < token.end]
    if covered:
        return covered[0], covered[-1] + 1
    k = sum(token.end <= start for token in geo.tokens)
    return k, k


def _touches(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Token ranges meet: ranges overlap; a point meets a range it lies in or at the edge of."""
    if a[0] == a[1] and b[0] == b[1]:
        return a[0] == b[0]
    if a[0] == a[1]:
        return b[0] <= a[0] <= b[1]
    if b[0] == b[1]:
        return a[0] <= b[0] <= a[1]
    return a[0] < b[1] and b[0] < a[1]


def logging_metrics(item: ReviewItem, counts: ReviewCounts, corrections: Sequence[dict[str, Any]]) -> dict[str, int]:
    """How the claims relate to the scored change; reported next to, never inside, the primary counts.

    A claim covers a changed unit when its token range meets the unit's. A claim
    is applied when the corrected text realises its replacement over its tokens
    (by the same slice rule as a seed's hit), so overlap alone never makes a
    broad, wrong claim count as applied. An unapplied claim whose own edit
    touches a protected span accuses it; such spans that stay unchanged are
    counted.
    """
    geo, alignment, keys, text = counts.geometry, counts.alignment, counts.geometry.keys, item.text
    changed = counts.hits | counts.wrong
    units = [(s.i1, s.i2) for s in geo.seeds if s.span.id in changed]
    units += [(p.i1, p.i2) for p in geo.protected if p.span.id in counts.protected]
    units += [(t, t + 1) for t in counts.tokens] + [(k, k) for k in counts.insertions]
    claimed: list[tuple[int, int]] = []
    applied = noop = unanchored = 0
    accused: set[str] = set()
    for correction in corrections:
        span = resolve_span(text, correction["span"], correction["start"], correction["end"])
        if span is None:
            unanchored += 1
            continue
        c1, c2 = _token_range(geo, *span)
        lo = min(span[0], geo.tokens[c1].start) if c1 < c2 else span[0]
        hi = max(span[1], geo.tokens[c2 - 1].end) if c1 < c2 else span[1]
        expected = token_keys(text[lo : span[0]] + correction["correction"] + text[span[1] : hi])
        edit = [op for op in align(keys[c1:c2], expected) if op.tag != "equal"]
        if not edit:
            noop += 1
            continue
        claimed.append((c1, c2))
        edges = {k for k in (c1, c2) if k in alignment.runs}
        if alignment.realise(c1, c2, {expected}, edges) is not None:
            applied += 1
            continue
        for op in edit:
            k = c1 + op.i
            for p in geo.protected:
                if (p.i1 < k < p.i2) if op.tag == "insert" else (p.i1 <= k < p.i2):
                    accused.add(p.span.id)
    return {
        "change_units": len(units),
        "claimed_change_units": sum(any(_touches(unit, claim) for claim in claimed) for unit in units),
        "claims": len(corrections),
        "applied_claims": applied,
        "unapplied_claims": len(claimed) - applied,
        "noop_claims": noop,
        "unanchored_claims": unanchored,
        "protected_accused_unchanged": len(accused - counts.protected),
    }


# --------------------------------------------------------------------------- review: one item


def _reaches(start: int, end: int, span: Span) -> bool:
    """Characters [start, end) address ``span`` (insertions at its edges included)."""
    if start == end:
        return span.start <= start <= span.end
    if span.start == span.end:
        return start <= span.start <= end
    return start < span.end and span.start < end


def _overlaps(start: int, end: int, span: Span) -> bool:
    """Characters [start, end) lie inside ``span`` (an insertion only when strictly inside)."""
    if start == end:
        return span.start < start < span.end or span.start == span.end == start
    if span.start == span.end:
        return start < span.start < end
    return start < span.end and span.start < end


def _failed_review(item: ReviewItem, reason: str) -> dict[str, Any]:
    return {
        "item_id": item.id,
        "failed": True,
        "reason": reason,
        "errors": [{"id": e.id, "type": e.kind, "hit": False} for e in item.errors],
        "protected_count": len(item.protected),
        "hits": 0,
        "fa_protected": 0,
        "fa_tokens": 0,
        "fa_insertions": 0,
        "false_alarms": 0,
        "wrong_corrections": 0,
        "protected_touched": [],
        "fa_inserted_tokens": 0,
        "logging": dict.fromkeys(LOGGING_KEYS, 0),
        "style": {"total": 0, "on_protected": 0, "on_error": 0, "unanchored": 0},
        "new_invalid_forms": [],
    }


def score_review_item(
    item: ReviewItem,
    entry: dict[str, Any] | None,
    failure: str | None = None,
    sources: SourcesClient | None = None,
) -> dict[str, Any]:
    if entry is None:
        return _failed_review(item, failure or "no answer")
    text = item.text
    counts = review_counts(item, entry["corrected_text"])

    style = {"total": 0, "on_protected": 0, "on_error": 0, "unanchored": 0}
    for suggestion in entry["style_suggestions"]:
        style["total"] += 1
        anchored = resolve_span(text, suggestion["span"], suggestion["start"], suggestion["end"])
        if anchored is None:
            style["unanchored"] += 1
            continue
        if any(_overlaps(*anchored, p) for p in item.protected):
            style["on_protected"] += 1
        if any(_reaches(*anchored, err) for err in item.errors):
            style["on_error"] += 1

    new_invalid: list[str] = []
    if sources is not None:
        new_invalid = sorted(sources.invalid_forms(entry["corrected_text"]) - sources.invalid_forms(text))
    return {
        "item_id": item.id,
        "failed": False,
        "reason": None,
        "errors": [{"id": e.id, "type": e.kind, "hit": e.id in counts.hits} for e in item.errors],
        "protected_count": len(item.protected),
        "hits": len(counts.hits),
        "fa_protected": len(counts.protected),
        "fa_tokens": len(counts.tokens),
        "fa_insertions": len(counts.insertions),
        "false_alarms": counts.false_alarms,
        "wrong_corrections": len(counts.wrong),
        "protected_touched": sorted(counts.protected),
        "fa_inserted_tokens": counts.inserted_tokens,
        "logging": logging_metrics(item, counts, entry["corrections"]),
        "style": style,
        "new_invalid_forms": new_invalid,
    }


class SourcesClient(Protocol):
    def invalid_forms(self, text: str) -> set[str]:
        """Word forms of ``text`` that VESUM does not attest."""

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        """Calque/Russianism, VESUM, CEFR and English-intrusion metrics for one text."""


# --------------------------------------------------------------------------- writing

_CALQUE_CHECKS = frozenset({"russian_shadow", "ua_gec"})


class LocalSources:
    """The ``sources`` tool implementations, called in-process on the local databases."""

    def __init__(self) -> None:
        from scripts.verification.check_text import check_text
        from scripts.verification.vesum import verify_words
        from scripts.wiki.sources_db import query_cefr_levels

        self._check_text = check_text
        self._verify_words = verify_words
        self._cefr = query_cefr_levels

    def _check(self, text: str, checks: list[str]) -> dict[str, Any]:
        result = self._check_text(text=text, checks=checks, max_findings=100_000)
        if result.get("status") == "error":
            raise RuntimeError(f"check_text failed: {result.get('error')}")
        return result

    def invalid_forms(self, text: str) -> set[str]:
        return {p["form"] for p in self._check(text, ["vesum"])["problems"] if p["check"] == "vesum"}

    def writing_metrics(self, text: str, level: str) -> dict[str, Any]:
        result = self._check(text, ["vesum", "russian_shadow", "ua_gec"])
        tokens = int(result["summary"]["tokens"])
        # Verdict tier only (curated Russian shadows grounded in Антоненко-Давидович and other
        # sources, multi-token UA-GEC calques); check_text labels the rest "suspicion, not a verdict".
        calques = [
            {"form": f["form"], "check": f["check"], "occurrences": len(f["locations"])}
            for f in result["problems"]
            if f["check"] in _CALQUE_CHECKS
        ]
        suspicions = [
            {"form": f["form"], "check": f["check"], "occurrences": len(f["locations"])}
            for f in result["suspicions"]
            if f["check"] in _CALQUE_CHECKS
        ]
        calque_hits = sum(c["occurrences"] for c in calques)
        suspicion_hits = sum(c["occurrences"] for c in suspicions)
        invalid = sorted({p["form"] for p in result["problems"] if p["check"] == "vesum"})
        cyrillic = cyrillic_words(text)
        latin = latin_words(text)
        forms = sorted({word.lower() for word in cyrillic})
        lemmas_by_form = self._verify_words(forms) if forms else {}
        lemmas = sorted({m["lemma"] for matches in lemmas_by_form.values() for m in matches})
        levels = self._cefr(lemmas) if lemmas else {}
        target = CEFR_LEVELS.index(level)
        known = above = 0
        above_words: list[str] = []
        for form in forms:
            ranks = [
                CEFR_LEVELS.index(hit["level"])
                for match in lemmas_by_form.get(form, [])
                for hit in levels.get(match["lemma"], [])
                if hit.get("level") in CEFR_LEVELS
            ]
            if ranks:
                known += 1
                if min(ranks) > target:
                    above += 1
                    above_words.append(form)
        words = len(cyrillic) + len(latin)
        return {
            "tokens": tokens,
            "words": words,
            "calque_hits": calque_hits,
            "calque_density": 100.0 * calque_hits / tokens if tokens else 0.0,
            "calques": calques,
            "calque_suspicion_hits": suspicion_hits,
            "calque_suspicion_density": 100.0 * suspicion_hits / tokens if tokens else 0.0,
            "calque_suspicions": suspicions,
            "vesum_invalid": len(invalid),
            "vesum_invalid_forms": invalid,
            "cefr_known_forms": known,
            "cefr_above_level": above,
            "cefr_above_level_forms": above_words,
            "level_adherence": 1.0 - above / known if known else None,
            "english_words": len(latin),
            "english_intrusion": len(latin) / words if words else 0.0,
        }


def score_writing_item(
    task: WritingTask, entry: dict[str, Any] | None, failure: str | None, sources: SourcesClient
) -> dict[str, Any]:
    if entry is None:
        return {
            "item_id": task.id,
            "level": task.level,
            "failed": True,
            "reason": failure or "no answer",
            "metrics": None,
        }
    metrics = sources.writing_metrics(entry["text"], task.level)
    words = metrics.get("words", 0)
    metrics["within_word_range"] = (task.min_words is None or words >= task.min_words) and (
        task.max_words is None or words <= task.max_words
    )
    return {"item_id": task.id, "level": task.level, "failed": False, "reason": None, "metrics": metrics}


# --------------------------------------------------------------------------- whole run


def task_state(raw: dict[str, Any] | None) -> str:
    """accepted, not_accepted (ran but failed or unattributable) or not_run."""
    if raw is None:
        return "not_run"
    return "accepted" if raw.get("accepted") else "not_accepted"


def _item_results(raw: dict[str, Any] | None, kind: str, item_ids: Sequence[str]) -> dict[str, tuple[Any, str | None]]:
    if raw is None:
        return {item_id: (None, "task not run") for item_id in item_ids}
    if not raw.get("accepted"):
        reason = raw.get("identity_problem") or raw.get("condition_problem") or f"task status {raw.get('status')}"
        return {item_id: (None, reason) for item_id in item_ids}
    return {r.item_id: (r.entry, r.error) for r in validate_response(kind, raw.get("response_text"), item_ids)}


def score_candidates(
    results: ResultsDir, eval_set: EvalSet, slots: Sequence[Slot], sources: SourcesClient | None
) -> dict[str, list[dict[str, Any]]]:
    """Score every planned slot; unrun or failed tasks score as failed items, never dropped."""
    reviews, writings = eval_set.review_by_id(), eval_set.writing_by_id()
    scored: dict[str, list[dict[str, Any]]] = {"review": [], "writing": []}
    for slot in slots:
        raw = load_raw(results, slot.task_id)
        cell = {
            "seat": slot.seat.seat_id,
            "variant": slot.variant,
            "repeat": slot.repeat,
            "task_id": slot.task_id,
            "task_state": task_state(raw),
        }
        for item_id, (entry, failure) in _item_results(raw, slot.kind, slot.item_ids).items():
            if slot.kind == "review":
                record = score_review_item(reviews[item_id], entry, failure, sources)
            else:
                if sources is None:
                    raise RuntimeError("writing metrics need the sources tools")
                record = score_writing_item(writings[item_id], entry, failure, sources)
            scored[slot.kind].append({**cell, **record})
    return scored


def score_judgements(results: ResultsDir, judge_tasks: Sequence[TaskSpec]) -> list[dict[str, Any]]:
    """Map each blind verdict back to variant labels; failed or unrun judgements are kept as failed."""
    records = []
    for task in judge_tasks:
        raw = load_raw(results, task.task_id)
        entries = valid_entries(raw, "judge")
        failures: dict[str, str | None] = {}
        if raw is not None and raw.get("accepted"):
            failures = {r.item_id: r.error for r in validate_response("judge", raw["response_text"], task.item_ids)}
        for item_id in task.item_ids:
            mapping = task.meta["order"][item_id]
            record = {
                "task_id": task.task_id,
                "judge_seat": task.seat.seat_id,
                "candidate_seat": task.meta["candidate_seat"],
                "pair": task.meta["pair"],
                "repeat": task.repeat,
                "item_id": item_id,
                "words": task.meta["words"][item_id],
            }
            entry = entries.get(item_id)
            if entry is None:
                if raw is None:
                    reason = "task not run"
                else:
                    reason = (
                        failures.get(item_id)
                        or raw.get("identity_problem")
                        or raw.get("condition_problem")
                        or f"task status {raw.get('status')}"
                    )
                records.append({**record, "failed": True, "reason": reason, "winner": None, "scores": None})
                continue
            winner = "tie" if entry["winner"] == "tie" else mapping[entry["winner"]]
            scores = {mapping[side]: {c: entry["scores"][side][c] for c in JUDGE_CRITERIA} for side in ("A", "B")}
            records.append({**record, "failed": False, "reason": None, "winner": winner, "scores": scores})
    return records
