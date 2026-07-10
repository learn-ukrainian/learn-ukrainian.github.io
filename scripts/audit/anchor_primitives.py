#!/usr/bin/env python3
"""Pure, stateless Layer A anchoring primitives.

This module owns only deterministic normalization, output extraction, matching,
and normalized-to-raw alignment.  It deliberately owns neither environment
handling nor mutable gate state nor ``AnchorResult`` composition; those stay in
``grounding_gate_v2`` so extraction cannot change an enforcement decision.

All offsets are half-open Unicode code-point offsets.  Callers must explicitly
select output scan and candidate-window bounds; a truncated scan is reported in
the return value and is never silently treated as complete.
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from itertools import pairwise
from typing import Any

ELLIPSIS_RE = re.compile(r"\[…\]|\[\.\.\.\]|…|\.{3,}")
TOKEN_RE = re.compile(r"[\w’'-]+", re.UNICODE)


@dataclass(frozen=True)
class SalientToken:
    """A digit or proper-noun-like token located in normalized excerpt space."""

    original: str
    norm: str
    start: int
    end: int
    is_digit: bool


@dataclass(frozen=True)
class WindowMatch:
    """One contiguous candidate window in normalized output space."""

    score: float
    span: tuple[int, int] | None
    matched_non_space_mass: int
    window_normalized: str


@dataclass(frozen=True)
class WindowSearchResult:
    """All evaluated windows plus explicit completeness metadata."""

    matches: tuple[WindowMatch, ...]
    truncated: bool
    candidate_count: int

    @property
    def best(self) -> WindowMatch:
        """Return the legacy best match, preserving first-match tie behavior."""
        best = WindowMatch(0.0, None, 0, "")
        best_score = -1.0
        for match in self.matches:
            if match.score > best_score:
                best = match
                best_score = match.score
        return best


@dataclass(frozen=True)
class OrderedSegmentOffset:
    """An ordered ellipsis fragment in normalized and optionally raw space.

    ``raw_start``/``raw_end`` are ``None`` only when no alignment map was
    supplied.  An alignment failure is conveyed separately by ``mapping_error``
    rather than guessed offsets.
    """

    segment_index: int
    excerpt_normalized_start: int
    excerpt_normalized_end: int
    output_normalized_start: int
    output_normalized_end: int
    raw_start: int | None
    raw_end: int | None
    mapping_error: str | None = None


@dataclass(frozen=True)
class EllipsisMatch:
    """Same-output ordered segment match result."""

    similarity: float
    ordered_segments: tuple[OrderedSegmentOffset, ...]
    matched_non_space_mass: int

    @property
    def enclosing_span(self) -> tuple[int, int] | None:
        """Diagnostic-only enclosing span; never a replacement for segments."""
        if not self.ordered_segments:
            return None
        return (
            self.ordered_segments[0].output_normalized_start,
            self.ordered_segments[-1].output_normalized_end,
        )


@dataclass(frozen=True)
class WindowAssessment:
    """Similarity and salient-token alignment for one normalized window."""

    similarity: float
    digit_aligned: bool
    salient_aligned: bool


@dataclass(frozen=True)
class NormalizedRawAlignment:
    """A per-output stateful normalized-to-raw character alignment map.

    Each normalized code point maps to the raw code-point interval that
    generated it.  A requested span is accepted only if normalizing its raw
    interval round-trips exactly; expansions and normalization boundaries are
    therefore reported as ambiguous instead of inferred.
    """

    raw: str
    normalized: str
    _raw_ranges: tuple[tuple[int, int], ...]

    def raw_span_for(self, start: int, end: int) -> tuple[int, int] | None:
        """Map a normalized half-open span to raw space or return ``None``."""
        if start < 0 or end <= start or end > len(self.normalized):
            return None
        ranges = self._raw_ranges[start:end]
        if not ranges:
            return None
        raw_start = ranges[0][0]
        raw_end = ranges[-1][1]
        for left, right in pairwise(ranges):
            # Casefold/NFKC expansion can map consecutive normalized code
            # points to the same raw code point.  That is valid only when the
            # requested span includes the whole expansion; round-trip below
            # rejects a boundary inside it without guessing.
            if right[0] > raw_end or right[0] < left[0]:
                return None
            raw_end = max(raw_end, right[1])
        if normalize_for_match(self.raw[raw_start:raw_end]) != self.normalized[start:end]:
            return None
        return raw_start, raw_end


def normalize_for_match(text: str) -> str:
    """Apply the exact established Layer A formatting normalization."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u0301", "").replace("\u0341", "")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.casefold().strip()


def build_normalized_raw_alignment(raw: str) -> NormalizedRawAlignment:
    """Build a lossless normalized-to-raw map for one captured output.

    Accent marks are attached to their preceding base-code-point cluster and a
    whitespace run maps to its one normalized space.  The final round-trip
    check in :meth:`NormalizedRawAlignment.raw_span_for` is the authority for
    whether a particular boundary is unambiguous.
    """
    pieces: list[str] = []
    ranges: list[tuple[int, int]] = []
    index = 0
    while index < len(raw):
        start = index
        if raw[index].isspace():
            index += 1
            while index < len(raw) and raw[index].isspace():
                index += 1
            normalized_piece = " "
        else:
            index += 1
            while index < len(raw) and unicodedata.combining(raw[index]):
                index += 1
            normalized_piece = normalize_for_match(raw[start:index])
        if not normalized_piece:
            # A removed mark belongs to the preceding cluster when possible.
            if ranges:
                previous_start, _ = ranges[-1]
                ranges[-1] = (previous_start, index)
            continue
        pieces.append(normalized_piece)
        ranges.extend([(start, index)] * len(normalized_piece))

    untrimmed = "".join(pieces)
    left = len(untrimmed) - len(untrimmed.lstrip())
    right = len(untrimmed.rstrip())
    normalized = untrimmed.strip()
    trimmed_ranges = tuple(ranges[left:right])
    if normalized != normalize_for_match(raw):
        # This cannot be safely represented.  Preserve the exact normalized
        # string and an empty map so every queried span fails closed.
        return NormalizedRawAlignment(raw, normalize_for_match(raw), ())
    return NormalizedRawAlignment(raw, normalized, trimmed_ranges)


def event_output_text(event: Mapping[str, Any]) -> str | None:
    """Extract captured output text using the established deterministic form."""
    output = event.get("output")
    if output is None:
        return None
    if isinstance(output, str):
        return output
    if isinstance(output, (Mapping, list)):
        return json.dumps(output, ensure_ascii=False, default=str)
    return str(output)


def canonical_tool_name(name: Any) -> str:
    """Canonicalize a tool identity without widening malformed names."""
    canonical = str(name or "").strip()
    if not canonical:
        return ""
    for prefix in ("mcp__", "mcp_"):
        if canonical.startswith(prefix):
            canonical = canonical[len(prefix) :]
            break
    if "." in canonical:
        server, _, tool = canonical.partition(".")
        if server and tool:
            canonical = tool
    else:
        for prefix in ("sources__", "sources_"):
            if canonical.startswith(prefix):
                canonical = canonical[len(prefix) :]
                break
    return canonical.casefold()


def event_input_matches_query(event: Mapping[str, Any], query: str) -> bool:
    """Return the established bounded-prefix query match for one event."""
    cited = " ".join(str(query).strip().lower().split())
    if not cited:
        return False
    candidates = _tool_query_candidates(event)
    for candidate in candidates:
        normalized_candidate = " ".join(str(candidate).strip().lower().split())
        if normalized_candidate and (cited == normalized_candidate or cited.startswith(normalized_candidate + " ")):
            return True
    return False


def _tool_query_candidates(event: Mapping[str, Any]) -> tuple[Any, ...]:
    """Match the dispatch helper's accepted query-bearing event fields."""
    values: list[Any] = []
    event_input = event.get("input")
    if isinstance(event_input, Mapping):
        for key in ("query", "q", "claim", "word", "headword", "lemma", "text"):
            value = event_input.get(key)
            if isinstance(value, str) and value.strip():
                values.append(value.strip())
        query = event_input.get("query") or event_input.get("q")
        mode = event_input.get("mode")
        if isinstance(query, str) and isinstance(mode, str):
            values.append(f"{query.strip()} mode={mode.strip()}")
        with suppress(TypeError, ValueError):
            values.append(json.dumps(event_input, ensure_ascii=False, sort_keys=True))
    elif isinstance(event_input, str) and event_input.strip():
        values.append(event_input.strip())
    return tuple(values)


def excerpt_segments(excerpt: str) -> tuple[tuple[str, int, int], ...]:
    """Return non-empty normalized ellipsis fragments with excerpt offsets."""
    normalized_excerpt = normalize_for_match(excerpt)
    records: list[tuple[str, int, int]] = []
    cursor = 0
    for part in ELLIPSIS_RE.split(excerpt):
        segment = normalize_for_match(part)
        if not segment:
            continue
        start = normalized_excerpt.find(segment, cursor)
        if start == -1:
            return ()
        end = start + len(segment)
        records.append((segment, start, end))
        cursor = end
    return tuple(records)


def output_contains_excerpt(output: str, excerpt: str) -> bool:
    """Return whether exact/ordered normalized excerpt evidence occurs in output."""
    normalized_output = normalize_for_match(output)
    if not ELLIPSIS_RE.search(excerpt):
        normalized_excerpt = normalize_for_match(excerpt)
        return bool(normalized_output and normalized_excerpt and normalized_excerpt in normalized_output)
    segments = [segment for segment, _, _ in excerpt_segments(excerpt) if len(segment) >= 4]
    if not segments:
        return False
    if sum(len(segment.replace(" ", "")) for segment in segments) < 12:
        return False
    cursor = 0
    for segment in segments:
        index = normalized_output.find(segment, cursor)
        if index == -1:
            return False
        cursor = index + len(segment)
    return True


def find_salient_tokens(excerpt: str, normalized_excerpt: str) -> tuple[SalientToken, ...]:
    """Extract digit/proper-noun-like tokens in normalized excerpt space."""
    cursor = 0
    salient_tokens: list[SalientToken] = []
    cyrillic_upper = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯ"
    for match in TOKEN_RE.finditer(excerpt):
        original = match.group()
        is_digit = any(character.isdigit() for character in original)
        is_proper = bool(original) and original[0] in cyrillic_upper
        normalized_token = normalize_for_match(original)
        if not (is_digit or is_proper):
            if normalized_token:
                position = normalized_excerpt.find(normalized_token, cursor)
                if position != -1:
                    cursor = position + len(normalized_token)
            continue
        if not normalized_token:
            continue
        position = normalized_excerpt.find(normalized_token, cursor)
        if position == -1:
            position = normalized_excerpt.find(normalized_token, 0)
        if position != -1:
            end = position + len(normalized_token)
            cursor = end
            salient_tokens.append(SalientToken(original, normalized_token, position, end, is_digit))
    return tuple(salient_tokens)


def find_best_window_original(
    normalized_excerpt: str,
    normalized_output: str,
    *,
    factor: float = 2.0,
    max_matcher_extra_chars: int = 256,
) -> WindowMatch:
    """Find the legacy best contiguous window in one bounded output string."""
    if not normalized_excerpt or not normalized_output:
        return WindowMatch(0.0, None, 0, "")
    max_matcher_len = 4 * len(normalized_excerpt) + max_matcher_extra_chars
    matcher_output = normalized_output[:max_matcher_len]
    autojunk = len(normalized_excerpt) > 500 or len(matcher_output) > 1000
    matcher = difflib.SequenceMatcher(None, normalized_excerpt, matcher_output, autojunk=autojunk)
    blocks = [block for block in matcher.get_matching_blocks() if block.size > 0]
    if not blocks:
        return WindowMatch(0.0, None, 0, matcher_output)
    max_window_len = max(len(normalized_excerpt) * factor, len(normalized_excerpt) + 50)
    count = len(blocks)
    sizes = [0] * (count + 1)
    masses = [0] * (count + 1)
    for index, block in enumerate(blocks):
        sizes[index + 1] = sizes[index] + block.size
        masses[index + 1] = masses[index] + len(normalized_excerpt[block.a : block.a + block.size].replace(" ", ""))
    best_score = -1.0
    best_span: tuple[int, int] | None = None
    best_mass = 0
    first = 0
    for last in range(count):
        block_end = blocks[last].b + blocks[last].size
        while first <= last and block_end - blocks[first].b > max_window_len:
            first += 1
        if first <= last:
            score = (sizes[last + 1] - sizes[first]) / len(normalized_excerpt)
            if score > best_score:
                best_score = score
                best_span = (blocks[first].b, block_end)
                best_mass = masses[last + 1] - masses[first]
    return WindowMatch(best_score, best_span, best_mass, matcher_output)


def find_candidate_windows(
    normalized_excerpt: str,
    normalized_output: str,
    *,
    salient_tokens: tuple[SalientToken, ...] | None = None,
    factor: float = 2.0,
    max_candidates: int = 64,
    max_matcher_extra_chars: int = 256,
) -> WindowSearchResult:
    """Enumerate bounded candidate windows with an explicit truncation result.

    The selection and first-best tie semantics deliberately mirror the original
    gate.  Unlike the old helper, every independently evaluated window is made
    available to the candidate materializer.
    """
    if not normalized_excerpt or not normalized_output:
        return WindowSearchResult((), False, 0)
    tokens = salient_tokens or find_salient_tokens(normalized_excerpt, normalized_excerpt)
    filtered = [token for token in tokens if token.is_digit or len(token.norm) >= 4]
    if not filtered:
        fallback_length = min(12, len(normalized_excerpt))
        if not fallback_length:
            return WindowSearchResult((), False, 0)
        filtered = [SalientToken("", normalized_excerpt[:fallback_length], 0, fallback_length, False)]

    def anchor_key(token: SalientToken) -> tuple[int, int, int]:
        return (
            normalized_output.count(token.norm),
            0 if not token.is_digit else 1,
            -len(token.norm),
        )

    anchor = min(filtered, key=anchor_key)
    candidate_starts: list[int] = []
    position = normalized_output.find(anchor.norm)
    while position != -1:
        candidate_starts.append(max(0, position - anchor.start - 32))
        position = normalized_output.find(anchor.norm, position + len(anchor.norm))
    if not candidate_starts:
        if len(normalized_output) < 1000:
            match = find_best_window_original(
                normalized_excerpt,
                normalized_output,
                factor=factor,
                max_matcher_extra_chars=max_matcher_extra_chars,
            )
            return WindowSearchResult((match,), False, 1)
        return WindowSearchResult((), False, 0)
    unique_starts: list[int] = []
    for start in sorted(candidate_starts):
        if not unique_starts or start - unique_starts[-1] >= len(normalized_excerpt):
            unique_starts.append(start)
    total_candidates = len(unique_starts)
    if total_candidates > max_candidates:
        return WindowSearchResult((), True, total_candidates)

    matches: list[WindowMatch] = []
    evaluated_windows: set[str] = set()
    for window_start in unique_starts:
        window_length = min(
            3 * len(normalized_excerpt) + 64,
            4 * len(normalized_excerpt) + max_matcher_extra_chars,
        )
        window_end = min(len(normalized_output), window_start + window_length)
        window = normalized_output[window_start:window_end]
        if window in evaluated_windows:
            continue
        evaluated_windows.add(window)
        result = find_best_window_original(
            normalized_excerpt,
            window,
            factor=factor,
            max_matcher_extra_chars=max_matcher_extra_chars,
        )
        span = None
        if result.span is not None:
            span = (window_start + result.span[0], window_start + result.span[1])
        matches.append(WindowMatch(result.score, span, result.matched_non_space_mass, window))
    return WindowSearchResult(tuple(matches), False, total_candidates)


def find_best_window(
    normalized_excerpt: str,
    normalized_output: str,
    *,
    factor: float = 2.0,
    salient_tokens: tuple[SalientToken, ...] | None = None,
    max_candidates: int = 64,
    max_matcher_extra_chars: int = 256,
) -> WindowSearchResult:
    """Return the full stateless window search result for an excerpt/output pair."""
    return find_candidate_windows(
        normalized_excerpt,
        normalized_output,
        salient_tokens=salient_tokens,
        factor=factor,
        max_candidates=max_candidates,
        max_matcher_extra_chars=max_matcher_extra_chars,
    )


def assess_window(
    normalized_excerpt: str,
    normalized_window: str,
    salient_tokens: tuple[SalientToken, ...],
    *,
    max_matcher_extra_chars: int = 256,
) -> WindowAssessment:
    """Assess fuzzy similarity and salient alignment in one bounded window."""
    hard_guard_length = 4 * len(normalized_excerpt) + max_matcher_extra_chars
    bounded_window = normalized_window[:hard_guard_length]
    autojunk = len(normalized_excerpt) > 500 or len(bounded_window) > 1000
    matcher = difflib.SequenceMatcher(None, normalized_excerpt, bounded_window, autojunk=autojunk)
    opcodes = matcher.get_opcodes()
    digit_aligned = True
    salient_aligned = True
    for token in salient_tokens:
        aligned = any(
            operation == "equal" and start_a <= token.start and token.end <= end_a
            for operation, start_a, end_a, _start_b, _end_b in opcodes
        )
        if not aligned:
            if token.is_digit:
                digit_aligned = False
            else:
                salient_aligned = False
    return WindowAssessment(matcher.ratio(), digit_aligned, salient_aligned)


def match_ellipsis_excerpt(
    excerpt: str,
    normalized_output: str,
    *,
    alignment: NormalizedRawAlignment | None = None,
    minimum_segment_length: int = 4,
) -> EllipsisMatch:
    """Match all ellipsis fragments in order inside one output.

    This function cannot stitch segments between events: it receives exactly one
    output.  It returns one record per non-empty qualifying fragment rather
    than collapsing the records to a single authoritative enclosing span.
    """
    segments = [record for record in excerpt_segments(excerpt) if len(record[0]) >= minimum_segment_length]
    if not segments:
        return EllipsisMatch(0.0, (), 0)
    mass = sum(len(segment.replace(" ", "")) for segment, _, _ in segments)
    cursor = 0
    offsets: list[OrderedSegmentOffset] = []
    for index, (segment, excerpt_start, excerpt_end) in enumerate(segments):
        output_start = normalized_output.find(segment, cursor)
        if output_start == -1:
            return EllipsisMatch(0.0, (), 0)
        output_end = output_start + len(segment)
        raw_start: int | None = None
        raw_end: int | None = None
        mapping_error: str | None = None
        if alignment is not None:
            mapped = alignment.raw_span_for(output_start, output_end)
            if mapped is None:
                mapping_error = "RAW_MAPPING_AMBIGUOUS"
            else:
                raw_start, raw_end = mapped
        offsets.append(
            OrderedSegmentOffset(
                index,
                excerpt_start,
                excerpt_end,
                output_start,
                output_end,
                raw_start,
                raw_end,
                mapping_error,
            )
        )
        cursor = output_end
    return EllipsisMatch(1.0, tuple(offsets), mass)
