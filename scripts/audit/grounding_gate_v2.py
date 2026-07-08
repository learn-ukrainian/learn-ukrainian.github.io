#!/usr/bin/env python3
"""Grounding Gate V2 — Layer A fuzzy provenance anchoring.

This module replaces the v1 exact substring match gate with a fuzzy provenance
anchoring algorithm using SequenceMatcher. It checks if evidence excerpts are
confidently backed by real captured tool events without enforcing brittle
exact matches on transport IDs, spelling, query decorations, or formatting.

Note: Layer B entailment MUST run against the RAW tool output, never the
extracted excerpt (the fail-closed handoff depends on it). Layer B itself
is a later chunk.
"""

from __future__ import annotations

import difflib
import logging
import os
import re
from collections import Counter
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
    _output_contains_excerpt,
)

DEFAULT_TAU = 0.75


@dataclass(frozen=True)
class AnchorResult:
    anchored: bool          # True only when confidently anchored to one real output
    abstained: bool         # True when ambiguous (excerpt matches multiple unrelated outputs)
    similarity: float       # best score in [0,1]
    source_index: int | None   # index of the anchored event, or None
    span: tuple[int, int] | None  # (start,end) char window in that event's normalized output
    reason: str             # short machine tag
    anchor_low_signal_reason: str | None = None  # diagnostic: e.g. "no_digits", "single_anchor"


def find_salient_tokens(excerpt: str, E_norm: str) -> list[dict[str, Any]]:
    """Extract salient tokens from excerpt and locate their spans in E_norm.

    Salient token: a token containing a digit, OR whose original (pre-casefold)
    form begins with an uppercase Cyrillic letter (proper-noun-like).
    """
    raw_matches = list(_TOKEN_RE.finditer(excerpt))
    salient_tokens = []

    # We will search sequentially in E_norm
    cursor = 0
    cyrillic_upper = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯ"

    for match in raw_matches:
        original = match.group()
        # Check if it is salient
        is_digit = any(c.isdigit() for c in original)
        is_proper = len(original) > 0 and original[0] in cyrillic_upper

        if not (is_digit or is_proper):
            # Advance cursor for non-salient tokens to maintain sequential tracking
            norm_tok = _normalize_for_match(original)
            if norm_tok:
                pos = E_norm.find(norm_tok, cursor)
                if pos != -1:
                    cursor = pos + len(norm_tok)
            continue

        norm_tok = _normalize_for_match(original)
        if not norm_tok:
            continue

        pos = E_norm.find(norm_tok, cursor)
        if pos == -1:
            # Fallback: search from beginning if sequence got slightly out of alignment
            pos = E_norm.find(norm_tok, 0)

        if pos != -1:
            start = pos
            end = pos + len(norm_tok)
            cursor = end
            salient_tokens.append({
                "original": original,
                "norm": norm_tok,
                "start": start,
                "end": end,
                "is_digit": is_digit
            })
    return salient_tokens


_last_search_truncated = False


def _find_best_window_original(
    normalized_excerpt: str,
    normalized_output: str,
    factor: float = 2.0,
) -> tuple[float, tuple[int, int] | None, int]:
    """Find the best contiguous window in normalized_output matching normalized_excerpt in O(blocks) time.

    Returns:
        (best_score, best_span, matched_non_space_mass)
    """
    if not normalized_excerpt or not normalized_output:
        return 0.0, None, 0

    # Hard defensive guard: never pass > 4*len(excerpt)+256 chars to a single SequenceMatcher call
    max_matcher_len = 4 * len(normalized_excerpt) + 256
    matcher_output = normalized_output
    if len(normalized_output) > max_matcher_len:
        matcher_output = normalized_output[:max_matcher_len]

    autojunk = (len(normalized_excerpt) > 500 or len(matcher_output) > 1000)
    s = difflib.SequenceMatcher(None, normalized_excerpt, matcher_output, autojunk=autojunk)
    blocks = [b for b in s.get_matching_blocks() if b.size > 0]
    if not blocks:
        return 0.0, None, 0

    # Guard 1: Span-locality window limit
    max_window_len = max(len(normalized_excerpt) * factor, len(normalized_excerpt) + 50)

    # Precompute prefix sums of block sizes and non-space masses
    n_blocks = len(blocks)
    P_size = [0] * (n_blocks + 1)
    P_mass = [0] * (n_blocks + 1)
    for i, b in enumerate(blocks):
        P_size[i + 1] = P_size[i] + b.size
        matched_str = normalized_excerpt[b.a : b.a + b.size]
        block_mass = len(matched_str.replace(" ", ""))
        P_mass[i + 1] = P_mass[i] + block_mass

    best_score = -1.0
    best_span = None
    best_mass = 0

    k = 0
    for m in range(n_blocks):
        b_end = blocks[m].b + blocks[m].size
        while k <= m and b_end - blocks[k].b > max_window_len:
            k += 1
        if k <= m:
            sum_sizes = P_size[m + 1] - P_size[k]
            score = sum_sizes / len(normalized_excerpt)
            sum_non_space = P_mass[m + 1] - P_mass[k]
            if score > best_score:
                best_score = score
                best_span = (blocks[k].b, b_end)
                best_mass = sum_non_space

    return best_score, best_span, best_mass


def _find_best_window(
    normalized_excerpt: str,
    normalized_output: str,
    factor: float = 2.0,
    salient_tokens: list[dict[str, Any]] | None = None,
) -> tuple[float, tuple[int, int] | None, int]:
    """Find the best contiguous window in normalized_output matching normalized_excerpt.

    Uses anchor-pre-scan to bound SequenceMatcher calls for correctness and speed.
    """
    global _last_search_truncated

    if not normalized_excerpt or not normalized_output:
        return 0.0, None, 0

    if salient_tokens is None:
        salient_tokens = find_salient_tokens(normalized_excerpt, normalized_excerpt)

    # Filter out short proper-noun tokens (length < 4) to avoid anchoring on common prepositions/words
    filtered_salient = [t for t in salient_tokens if t.get("is_digit") or len(t["norm"]) >= 4]

    if not filtered_salient:
        # Fallback anchor: if there are no distinctive salient tokens, pick a prefix of the excerpt
        # to ensure that we still bound SequenceMatcher on generic repetitive inputs.
        fallback_len = min(12, len(normalized_excerpt))
        if fallback_len > 0:
            fallback_sub = normalized_excerpt[:fallback_len]
            filtered_salient = [{
                "norm": fallback_sub,
                "start": 0,
                "end": fallback_len,
                "is_digit": False,
            }]
        else:
            return _find_best_window_original(normalized_excerpt, normalized_output, factor)

    # 1. Identify the single most distinctive salient anchor
    # "the RAREST/longest salient token (prefer the longest proper-noun token; tiebreak the longest digit run), NOT a common one."
    def anchor_key(t: dict[str, Any]) -> tuple[int, int, int]:
        sub = t["norm"]
        count = normalized_output.count(sub)
        is_proper = not t.get("is_digit", False)
        length = len(sub)
        return (count, 0 if is_proper else 1, -length)

    best_anchor = min(filtered_salient, key=anchor_key)

    # 2. Locate candidate window START positions by fast exact str.find of the chosen distinctive anchor
    candidate_starts = []
    sub = best_anchor["norm"]
    start_in_excerpt = best_anchor["start"]

    pos = normalized_output.find(sub)
    while pos != -1:
        win_start = max(0, pos - start_in_excerpt - 32)
        candidate_starts.append(win_start)
        pos = normalized_output.find(sub, pos + len(sub))

    if not candidate_starts:
        # If the excerpt has NO salient anchor present in the output at all -> reject.
        # Fall back to original SequenceMatcher if output is small to maintain exact behavior/reasons.
        if len(normalized_output) < 1000:
            return _find_best_window_original(normalized_excerpt, normalized_output, factor)
        return 0.0, None, 0

    # Deduplicate/merge candidate start positions that are very close to each other
    unique_starts = []
    for start in sorted(candidate_starts):
        if not unique_starts or start - unique_starts[-1] >= len(normalized_excerpt):
            unique_starts.append(start)

    # 4. Cap the number of candidate windows evaluated (e.g. first 64)
    MAX_CANDIDATES = 64
    total_candidates = len(unique_starts)
    if total_candidates > MAX_CANDIDATES:
        _last_search_truncated = True
        logging.getLogger("grounding_gate_v2").warning(
            f"Truncated candidate windows from {total_candidates} to {MAX_CANDIDATES} for excerpt length {len(normalized_excerpt)}"
        )
        return 0.0, None, 0

    best_score = -1.0
    best_span = None
    best_mass = 0

    evaluated_w_norms = set()

    # 3. For each candidate occurrence, run SequenceMatcher ONLY on a bounded window
    for win_start in unique_starts:
        win_len = 3 * len(normalized_excerpt) + 64
        # 5. Keep a hard defensive guard: never pass > 4*len(excerpt)+256 chars to a single SequenceMatcher call
        hard_guard_len = 4 * len(normalized_excerpt) + 256
        win_len = min(win_len, hard_guard_len)

        win_end = min(len(normalized_output), win_start + win_len)
        W_norm = normalized_output[win_start:win_end]

        if W_norm in evaluated_w_norms:
            continue
        evaluated_w_norms.add(W_norm)

        sub_score, sub_span, sub_mass = _find_best_window_original(normalized_excerpt, W_norm, factor)
        if sub_span is not None:
            mapped_span = (win_start + sub_span[0], win_start + sub_span[1])
            if sub_score > best_score:
                best_score = sub_score
                best_span = mapped_span
                best_mass = sub_mass

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
) -> AnchorResult:
    """Fuzzy anchor a grounding evidence excerpt to the list of captured tool events.

    Args:
        grounding: Grounding metadata from finding/fact_check.
        events: Captured tool run events.
        tau: Confidence threshold for anchoring. Defaults to DEFAULT_TAU or env override.

    Returns:
        AnchorResult indicating the status and metadata of the anchoring match.
    """
    global _last_search_truncated
    _last_search_truncated = False

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

    # Extract salient tokens
    salient_tokens = find_salient_tokens(excerpt, normalized_excerpt)
    if not salient_tokens:
        return AnchorResult(
            anchored=False,
            abstained=False,
            similarity=0.0,
            source_index=None,
            span=None,
            reason="no_salient_anchor",
        )

    # Max length of output to process to guard against pathological performance issues
    MAX_SCANNED_OUTPUT_CHARS = 50000

    # Evaluate matching for each event
    event_results = []

    for idx, event in enumerate(events):
        output_text = _event_output_text(event)
        if output_text is None:
            continue

        # Cap scanned output chars
        if len(output_text) > MAX_SCANNED_OUTPUT_CHARS:
            output_text = output_text[:MAX_SCANNED_OUTPUT_CHARS]

        normalized_output = _normalize_for_match(output_text)
        tool_query_matched = _tool_query_match(grounding, event)

        if has_ellipsis:
            # Ellipsis path: delegate provenance to v1 helper first
            if not _output_contains_excerpt(output_text, excerpt):
                continue
            raw_sim, span, matched_mass = _match_ellipsis_excerpt(excerpt, normalized_output)
            if span is None:
                continue

            max_window_len = max(len(normalized_excerpt) * 2.0, len(normalized_excerpt) + 50)
            span_locality_ok = (span[1] - span[0] <= max_window_len)

            W_norm = normalized_output[span[0]:span[1]]
            # Hard defensive guard: never pass > 4*len(excerpt)+256 chars to a single SequenceMatcher call
            hard_guard_len = 4 * len(normalized_excerpt) + 256
            if len(W_norm) > hard_guard_len:
                W_norm = W_norm[:hard_guard_len]
            autojunk = (len(normalized_excerpt) > 500 or len(W_norm) > 1000)
            matcher = difflib.SequenceMatcher(None, normalized_excerpt, W_norm, autojunk=autojunk)
            ops = matcher.get_opcodes()

            digit_aligned = True
            salient_aligned = True
            for t in salient_tokens:
                aligned = any(
                    op == "equal" and i1 <= t["start"] and t["end"] <= i2
                    for op, i1, i2, j1, j2 in ops
                )
                # TODO(#4797): optional VESUM lemma tightening when db present
                if not aligned:
                    if t["is_digit"]:
                        digit_aligned = False
                    else:
                        salient_aligned = False

            event_results.append({
                "index": idx,
                "raw_sim": raw_sim,  # Keep similarity = 1.0 for backwards compatibility
                "span": span,
                "matched_mass": matched_mass,
                "span_locality_ok": span_locality_ok,
                "digit_aligned": digit_aligned,
                "salient_aligned": salient_aligned,
                "tool_query_matched": tool_query_matched,
                "normalized_output": normalized_output,
                "mass_ok": True,
                "sim_ok": True,
            })
        else:
            # Non-ellipsis path
            # Search best window span
            _, span, matched_mass = _find_best_window(
                normalized_excerpt,
                normalized_output,
                salient_tokens=salient_tokens,
            )
            if span is None:
                continue

            W_norm = normalized_output[span[0]:span[1]]
            # Hard defensive guard: never pass > 4*len(excerpt)+256 chars to a single SequenceMatcher call
            hard_guard_len = 4 * len(normalized_excerpt) + 256
            if len(W_norm) > hard_guard_len:
                W_norm = W_norm[:hard_guard_len]
            autojunk = (len(normalized_excerpt) > 500 or len(W_norm) > 1000)
            matcher = difflib.SequenceMatcher(None, normalized_excerpt, W_norm, autojunk=autojunk)
            raw_sim = matcher.ratio()

            required_threshold = (tau - 0.05) if tool_query_matched else tau
            sim_ok = (raw_sim >= required_threshold)
            mass_ok = (matched_mass >= 12)

            ops = matcher.get_opcodes()
            digit_aligned = True
            salient_aligned = True
            for t in salient_tokens:
                aligned = any(
                    op == "equal" and i1 <= t["start"] and t["end"] <= i2
                    for op, i1, i2, j1, j2 in ops
                )
                # TODO(#4797): optional VESUM lemma tightening when db present
                if not aligned:
                    if t["is_digit"]:
                        digit_aligned = False
                    else:
                        salient_aligned = False

            event_results.append({
                "index": idx,
                "raw_sim": raw_sim,
                "span": span,
                "matched_mass": matched_mass,
                "span_locality_ok": True,
                "digit_aligned": digit_aligned,
                "salient_aligned": salient_aligned,
                "tool_query_matched": tool_query_matched,
                "normalized_output": normalized_output,
                "mass_ok": mass_ok,
                "sim_ok": sim_ok,
            })

    if _last_search_truncated:
        return AnchorResult(
            anchored=False,
            abstained=False,
            similarity=0.0,
            source_index=None,
            span=None,
            reason="candidate_truncated",
        )

    # Filter to candidates that pass all guards
    valid_candidates = []
    for res in event_results:
        if (
            res["sim_ok"]
            and res["mass_ok"]
            and res["span_locality_ok"]
            and res["digit_aligned"]
            and res["salient_aligned"]
        ):
            valid_candidates.append(res)

    if valid_candidates:
        # Sort valid candidates: primary key raw_sim descending, secondary tool_query_matched descending
        valid_candidates.sort(key=lambda x: (x["raw_sim"], x["tool_query_matched"]), reverse=True)
        best_cand = valid_candidates[0]

        # Guard 3: distinctiveness / ambiguity abstain
        abstained = False
        for other in valid_candidates[1:]:
            if (
                other["normalized_output"] != best_cand["normalized_output"]
                and (best_cand["raw_sim"] - other["raw_sim"]) <= 0.05
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

        # Compute low signal reasons
        low_signal_reasons = []
        if not any(c.isdigit() for c in normalized_excerpt):
            low_signal_reasons.append("no_digits")
        if len(salient_tokens) <= 1:
            low_signal_reasons.append("single_anchor")
        if _last_search_truncated:
            low_signal_reasons.append("candidate_truncated")
        anchor_low_signal_reason = ",".join(low_signal_reasons) if low_signal_reasons else None

        return AnchorResult(
            anchored=True,
            abstained=False,
            similarity=best_cand["raw_sim"],
            source_index=best_cand["index"],
            span=best_cand["span"],
            reason="anchored",
            anchor_low_signal_reason=anchor_low_signal_reason,
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

    # Find the event with the highest raw_sim (or tool_query_matched if equal)
    event_results.sort(key=lambda x: (x["raw_sim"], x["tool_query_matched"]), reverse=True)
    best_attempt = event_results[0]

    if has_ellipsis:
        if not best_attempt["span_locality_ok"]:
            reason = "below_tau"
        elif not best_attempt["digit_aligned"]:
            reason = "digit_not_aligned"
        elif not best_attempt["salient_aligned"]:
            reason = "salient_not_aligned"
        else:
            reason = "below_tau"
    else:
        if not best_attempt["sim_ok"]:
            reason = "below_tau"
        elif not best_attempt["mass_ok"]:
            reason = "insufficient_mass"
        elif not best_attempt["digit_aligned"]:
            reason = "digit_not_aligned"
        elif not best_attempt["salient_aligned"]:
            reason = "salient_not_aligned"
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
