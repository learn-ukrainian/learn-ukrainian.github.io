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

import logging
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from scripts.audit import anchor_primitives

DEFAULT_TAU = 0.75

# Legacy private names remain import-compatible while delegating to the public,
# stateless primitives.  Gate state and AnchorResult composition stay here.
_ELLIPSIS_RE = anchor_primitives.ELLIPSIS_RE
_event_output_text = anchor_primitives.event_output_text
_normalize_for_match = anchor_primitives.normalize_for_match
_output_contains_excerpt = anchor_primitives.output_contains_excerpt


@dataclass(frozen=True)
class AnchorResult:
    anchored: bool  # True only when confidently anchored to one real output
    abstained: bool  # True when ambiguous (excerpt matches multiple unrelated outputs)
    similarity: float  # best score in [0,1]
    source_index: int | None  # index of the anchored event, or None
    span: tuple[int, int] | None  # (start,end) char window in that event's normalized output
    reason: str  # short machine tag
    anchor_low_signal_reason: str | None = None  # diagnostic: e.g. "no_digits", "single_anchor"


def find_salient_tokens(excerpt: str, normalized_excerpt: str) -> list[dict[str, Any]]:
    """Compatibility projection of the pure primitive's public token records."""
    return [
        {
            "original": token.original,
            "norm": token.norm,
            "start": token.start,
            "end": token.end,
            "is_digit": token.is_digit,
        }
        for token in anchor_primitives.find_salient_tokens(excerpt, normalized_excerpt)
    ]


_last_search_truncated = False


def _find_best_window_original(
    normalized_excerpt: str,
    normalized_output: str,
    factor: float = 2.0,
) -> tuple[float, tuple[int, int] | None, int]:
    """Delegate legacy tuple API to the stateless primitive."""
    result = anchor_primitives.find_best_window_original(
        normalized_excerpt,
        normalized_output,
        factor=factor,
    )
    return result.score, result.span, result.matched_non_space_mass


def _find_best_window(
    normalized_excerpt: str,
    normalized_output: str,
    factor: float = 2.0,
    salient_tokens: list[dict[str, Any]] | None = None,
) -> tuple[float, tuple[int, int] | None, int]:
    """Delegate legacy tuple API to the stateless primitive."""
    global _last_search_truncated
    primitive_tokens = None
    if salient_tokens is not None:
        primitive_tokens = tuple(
            anchor_primitives.SalientToken(
                str(token.get("original") or ""),
                str(token.get("norm") or ""),
                int(token.get("start") or 0),
                int(token.get("end") or 0),
                bool(token.get("is_digit")),
            )
            for token in salient_tokens
        )
    result = anchor_primitives.find_best_window(
        normalized_excerpt,
        normalized_output,
        factor=factor,
        salient_tokens=primitive_tokens,
    )
    if result.truncated:
        _last_search_truncated = True
        logging.getLogger("grounding_gate_v2").warning(
            f"Truncated candidate windows from {result.candidate_count} to 64 for excerpt length {len(normalized_excerpt)}"
        )
        return 0.0, None, 0
    best = result.best
    return best.score, best.span, best.matched_non_space_mass


def _match_ellipsis_excerpt(
    excerpt: str,
    normalized_output: str,
) -> tuple[float, tuple[int, int] | None, int]:
    """Delegate legacy enclosing-span diagnostics to ordered segment records."""
    result = anchor_primitives.match_ellipsis_excerpt(excerpt, normalized_output)
    return result.similarity, result.enclosing_span, result.matched_non_space_mass


def _tool_query_match(grounding: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    """Check if the event matches the grounding tool/query canonical signature."""
    tool = anchor_primitives.canonical_tool_name(grounding.get("tool"))
    if tool and anchor_primitives.canonical_tool_name(event.get("tool")) != tool:
        return False
    query = str(grounding.get("query") or "").strip()
    if not query:
        return False
    return anchor_primitives.event_input_matches_query(event, query)


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
            span_locality_ok = span[1] - span[0] <= max_window_len

            W_norm = normalized_output[span[0] : span[1]]
            assessment = anchor_primitives.assess_window(
                normalized_excerpt,
                W_norm,
                tuple(
                    anchor_primitives.SalientToken(t["original"], t["norm"], t["start"], t["end"], t["is_digit"])
                    for t in salient_tokens
                ),
            )

            event_results.append(
                {
                    "index": idx,
                    "raw_sim": raw_sim,  # Keep similarity = 1.0 for backwards compatibility
                    "span": span,
                    "matched_mass": matched_mass,
                    "span_locality_ok": span_locality_ok,
                    "digit_aligned": assessment.digit_aligned,
                    "salient_aligned": assessment.salient_aligned,
                    "tool_query_matched": tool_query_matched,
                    "normalized_output": normalized_output,
                    "mass_ok": True,
                    "sim_ok": True,
                }
            )
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

            W_norm = normalized_output[span[0] : span[1]]
            assessment = anchor_primitives.assess_window(
                normalized_excerpt,
                W_norm,
                tuple(
                    anchor_primitives.SalientToken(t["original"], t["norm"], t["start"], t["end"], t["is_digit"])
                    for t in salient_tokens
                ),
            )
            raw_sim = assessment.similarity

            required_threshold = (tau - 0.05) if tool_query_matched else tau
            sim_ok = raw_sim >= required_threshold
            mass_ok = matched_mass >= 12

            event_results.append(
                {
                    "index": idx,
                    "raw_sim": raw_sim,
                    "span": span,
                    "matched_mass": matched_mass,
                    "span_locality_ok": True,
                    "digit_aligned": assessment.digit_aligned,
                    "salient_aligned": assessment.salient_aligned,
                    "tool_query_matched": tool_query_matched,
                    "normalized_output": normalized_output,
                    "mass_ok": mass_ok,
                    "sim_ok": sim_ok,
                }
            )

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
