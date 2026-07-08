#!/usr/bin/env python3
"""Grounding Gate V2 — Layer A fuzzy provenance anchoring.

This module replaces the v1 exact substring match gate with a fuzzy provenance
anchoring algorithm using SequenceMatcher. It checks if evidence excerpts are
confidently backed by real captured tool events without enforcing brittle
exact matches on transport IDs, spelling, query decorations, or formatting.
"""

from __future__ import annotations

import difflib
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# Reuse existing normalization and tool event helpers from v1 gate
from scripts.audit.llm_reviewer_dispatch import (
    _ELLIPSIS_RE,
    _TOKEN_RE,
    _canonical_tool_name,
    _event_input_matches_query,
    _event_output_text,
    _excerpt_segments,
    _normalize_for_match,
)

# PROVISIONAL — lead-eng tunes on real 2026-07-08 rejected cells post-merge
DEFAULT_TAU = 0.75


@dataclass(frozen=True)
class AnchorResult:
    anchored: bool          # True only when confidently anchored to one real output
    abstained: bool         # True when ambiguous (excerpt matches multiple unrelated outputs)
    similarity: float       # best score in [0,1]
    source_index: int | None   # index of the anchored event, or None
    span: tuple[int, int] | None  # (start,end) char window in that event's normalized output
    reason: str             # short machine tag: "anchored" | "below_tau" | "abstain_ambiguous"
                            #   | "insufficient_mass" | "no_content_token" | "no_output"


def _get_content_bearing_tokens(excerpt: str) -> set[str]:
    """Extract capitalized words, digit runs, or quoted titles from excerpt."""
    quoted_phrases = re.findall(r'["\'«»“”‘’]([^"\'«»“”‘’]+)["\'«»“”‘’]', excerpt)
    content_tokens = set()
    for phrase in quoted_phrases:
        for t in _TOKEN_RE.findall(phrase):
            if t.strip():
                content_tokens.add(_normalize_for_match(t))

    for t in _TOKEN_RE.findall(excerpt):
        if not t.strip():
            continue
        # Capitalized word or digit run
        if t[0].isupper() or any(c.isdigit() for c in t):
            content_tokens.add(_normalize_for_match(t))

    return content_tokens


def _find_best_window(
    normalized_excerpt: str,
    normalized_output: str,
    factor: float = 2.0,
) -> tuple[float, tuple[int, int] | None, int]:
    """Find the best contiguous window in normalized_output matching normalized_excerpt.

    Returns:
        (best_score, best_span, matched_non_space_mass)
    """
    if not normalized_excerpt or not normalized_output:
        return 0.0, None, 0

    s = difflib.SequenceMatcher(None, normalized_excerpt, normalized_output, autojunk=False)
    blocks = [b for b in s.get_matching_blocks() if b.size > 0]
    if not blocks:
        return 0.0, None, 0

    # Guard 1: Span-locality window limit
    max_window_len = max(len(normalized_excerpt) * factor, len(normalized_excerpt) + 50)

    best_score = -1.0
    best_span = None
    best_mass = 0

    n_blocks = len(blocks)
    for k in range(n_blocks):
        for m in range(k, n_blocks):
            b_start = blocks[k].b
            b_end = blocks[m].b + blocks[m].size
            if b_end - b_start <= max_window_len:
                # Sum sizes of matching blocks
                sum_sizes = sum(blocks[x].size for x in range(k, m + 1))
                score = sum_sizes / len(normalized_excerpt)

                # Compute matched mass (non-whitespace chars)
                sum_non_space = 0
                for x in range(k, m + 1):
                    block = blocks[x]
                    matched_str = normalized_excerpt[block.a : block.a + block.size]
                    sum_non_space += len(matched_str.replace(" ", ""))

                if score > best_score:
                    best_score = score
                    best_span = (b_start, b_end)
                    best_mass = sum_non_space

    return best_score, best_span, best_mass


def _match_ellipsis_excerpt(
    excerpt: str,
    normalized_output: str,
) -> tuple[float, tuple[int, int] | None, int]:
    """Ordered segment matching for excerpts with ellipsis."""
    segments = [segment for segment in _excerpt_segments(excerpt) if len(segment) >= 4]
    if not segments:
        return 0.0, None, 0

    evidence_mass = sum(len(segment.replace(" ", "")) for segment in segments)

    cursor = 0
    first_start = None
    last_end = None
    for segment in segments:
        index = normalized_output.find(segment, cursor)
        if index == -1:
            return 0.0, None, 0
        if first_start is None:
            first_start = index
        last_end = index + len(segment)
        cursor = last_end

    return 1.0, (first_start, last_end), evidence_mass


def _tool_query_match(grounding: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    """Check if the event matches the grounding tool/query canonical signature."""
    tool = _canonical_tool_name(grounding.get("tool"))
    if tool and _canonical_tool_name(event.get("tool")) != tool:
        return False
    query = str(grounding.get("query") or "").strip()
    if not query:
        return False
    return _event_input_matches_query(event, query)


def anchor_evidence_to_events(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    tau: float | None = None,
    tool_query_bonus: float = 0.15,
) -> AnchorResult:
    """Fuzzy anchor a grounding evidence excerpt to the list of captured tool events.

    Args:
        grounding: Grounding metadata from finding/fact_check.
        events: Captured tool run events.
        tau: Confidence threshold for anchoring. Defaults to DEFAULT_TAU or env override.
        tool_query_bonus: Score bonus added to events matching cited tool/query.

    Returns:
        AnchorResult indicating the status and metadata of the anchoring match.
    """
    if tau is None:
        env_tau = os.environ.get("QG_GROUNDING_GATE_V2_TAU")
        if env_tau is not None:
            try:
                tau = float(env_tau)
            except ValueError:
                tau = DEFAULT_TAU
        else:
            tau = DEFAULT_TAU

    excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not excerpt:
        return AnchorResult(
            anchored=False,
            abstained=False,
            similarity=0.0,
            source_index=None,
            span=None,
            reason="insufficient_mass",
        )

    # Check if there are any events with output
    has_any_output = False
    for event in events:
        if _event_output_text(event) is not None:
            has_any_output = True
            break

    if not has_any_output:
        return AnchorResult(
            anchored=False,
            abstained=False,
            similarity=0.0,
            source_index=None,
            span=None,
            reason="no_output",
        )

    normalized_excerpt = _normalize_for_match(excerpt)
    has_ellipsis = bool(_ELLIPSIS_RE.search(excerpt))
    content_tokens = _get_content_bearing_tokens(excerpt)

    # Evaluate matching for each event
    event_results = []

    for idx, event in enumerate(events):
        output_text = _event_output_text(event)
        if output_text is None:
            continue

        normalized_output = _normalize_for_match(output_text)

        if has_ellipsis:
            raw_sim, span, matched_mass = _match_ellipsis_excerpt(excerpt, normalized_output)
        else:
            raw_sim, span, matched_mass = _find_best_window(normalized_excerpt, normalized_output)

        if span is None or raw_sim <= 0.0:
            continue

        # Check Guards per event
        mass_ok = (matched_mass >= 15)

        if content_tokens:
            matched_span_text = normalized_output[span[0]:span[1]]
            content_ok = any(tok in matched_span_text for tok in content_tokens)
        else:
            content_ok = True

        tool_query_matched = _tool_query_match(grounding, event)

        # Calculate score with bonus
        score_with_bonus = raw_sim + (tool_query_bonus if tool_query_matched else 0.0)
        score_with_bonus = min(score_with_bonus, 1.0)

        event_results.append({
            "index": idx,
            "raw_sim": raw_sim,
            "span": span,
            "matched_mass": matched_mass,
            "mass_ok": mass_ok,
            "content_ok": content_ok,
            "tool_query_matched": tool_query_matched,
            "score_with_bonus": score_with_bonus,
            "normalized_output": normalized_output,
        })

    # Filter to candidates that pass all guards and have score >= tau
    valid_candidates = []
    for res in event_results:
        if res["mass_ok"] and res["content_ok"] and res["score_with_bonus"] >= tau:
            valid_candidates.append(res)

    if valid_candidates:
        # Sort valid candidates: primary key score_with_bonus descending, secondary raw_sim descending
        valid_candidates.sort(key=lambda x: (x["score_with_bonus"], x["raw_sim"]), reverse=True)
        best_cand = valid_candidates[0]

        # Guard 3: distinctiveness / ambiguity abstain
        abstained = False
        for other in valid_candidates[1:]:
            if (
                other["normalized_output"] != best_cand["normalized_output"]
                and (best_cand["score_with_bonus"] - other["score_with_bonus"]) <= 0.05
            ):
                abstained = True
                break

        if abstained:
            return AnchorResult(
                anchored=False,
                abstained=True,
                similarity=best_cand["raw_sim"],
                source_index=None,
                span=None,
                reason="abstain_ambiguous",
            )

        return AnchorResult(
            anchored=True,
            abstained=False,
            similarity=best_cand["raw_sim"],
            source_index=best_cand["index"],
            span=best_cand["span"],
            reason="anchored",
        )

    # If no candidate passes, return the best failure reason
    if not event_results:
        return AnchorResult(
            anchored=False,
            abstained=False,
            similarity=0.0,
            source_index=None,
            span=None,
            reason="below_tau",
        )

    # Find the event with the highest score_with_bonus (or raw_sim if equal)
    event_results.sort(key=lambda x: (x["score_with_bonus"], x["raw_sim"]), reverse=True)
    best_attempt = event_results[0]

    if not best_attempt["mass_ok"]:
        reason = "insufficient_mass"
    elif not best_attempt["content_ok"]:
        reason = "no_content_token"
    else:
        reason = "below_tau"

    return AnchorResult(
        anchored=False,
        abstained=False,
        similarity=best_attempt["raw_sim"],
        source_index=None,
        span=None,
        reason=reason,
    )
