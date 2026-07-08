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


UK_STOPWORDS = {
    # Pronouns
    "котрий", "котра", "котре", "котрі", "котрого", "котрій", "котрих", "котрими",
    "стільки", "деякий", "деяка", "деяке", "деякі", "деякого", "деяких",
    "ніякий", "ніяка", "ніяке", "ніякі", "ніякого", "ніяких",
    "якийсь", "якась", "якесь", "якісь", "якогось", "якихось",
    "хтось", "щось", "чийсь", "чиясь", "чиєсь", "чиїсь",
    "увесь", "усякий", "усяка", "усяке", "усякі", "усього", "усьому",
    "ввесь", "всякий", "всяка", "всяке", "всякі", "всього", "всьому",
    "кожен", "кожна", "кожне", "кожні", "кожного", "кожнім", "кожних",
    "жоден", "жодна", "жодне", "жодні", "жодного", "жодних",
    "інший", "інша", "інше", "інші", "іншого", "інших", "іншому",
    "собою", "соби",
    # Prepositions
    "перед", "через", "серед", "проти", "окрім", "округ", "заради", "вдовж",
    "опріч", "поміж", "понад", "поруч", "позаду",
    # Conjunctions
    "оскільки", "нібито", "неначе", "немовби", "немовбито", "причому", "начебто",
    # Particles & adverbs (commonly used as fillers/conjunctions)
    "тільки", "навіть", "мабуть", "невже", "нехай", "майже", "також", "знову",
    "просто", "ніби", "наче", "мовби",
    # English equivalents/function words of length >= 5
    "which", "about", "their", "there", "these", "those", "would", "could",
    "should", "under", "after", "before", "while", "where", "since", "until",
    "unless", "though", "although", "either", "neither", "other", "another",
    "every", "yours", "herself", "himself", "itself", "myself", "yourself",
    "themselves", "ourselves"
}


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein distance between two strings using standard DP."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if not s2:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def is_salient_token(token: str) -> bool:
    """Determine if a token is salient (length >= 5, Cyrillic capitalized or content word)."""
    if len(token) < 5:
        return False
    # Check if alphabetic (letters plus internal apostrophe/hyphen)
    if not all(c.isalpha() or c in "'’ʼ-" for c in token):
        return False
    cyrillic_upper = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯ"
    if token[0] in cyrillic_upper:
        return True
    return token.casefold() not in UK_STOPWORDS


def _find_best_window(
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

    s = difflib.SequenceMatcher(None, normalized_excerpt, normalized_output, autojunk=False)
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

    # Extract anchors from the excerpt
    excerpt_digits = re.findall(r'\d+', normalized_excerpt)
    excerpt_digit_counts = Counter(excerpt_digits)
    raw_tokens = _TOKEN_RE.findall(excerpt)
    excerpt_salient_tokens = [t for t in raw_tokens if is_salient_token(t)]

    # Group proper nouns that are adjacent to form a single name/proper-noun anchor
    cyrillic_upper = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЮЯ"
    proper_noun_anchors = []
    current_name = []
    for t in raw_tokens:
        if len(t) >= 5 and all(c.isalpha() or c in "'’ʼ-" for c in t) and t[0] in cyrillic_upper:
            current_name.append(t.casefold())
        else:
            if current_name:
                proper_noun_anchors.append(" ".join(current_name))
                current_name = []
    if current_name:
        proper_noun_anchors.append(" ".join(current_name))

    # Other salient tokens that are not part of proper nouns
    other_salient = []
    for t in raw_tokens:
        if (
            len(t) >= 5
            and all(c.isalpha() or c in "'’ʼ-" for c in t)
            and t[0] not in cyrillic_upper
            and t.casefold() not in UK_STOPWORDS
        ):
            other_salient.append(t.casefold())

    excerpt_content_anchors = set(excerpt_digits) | set(proper_noun_anchors) | set(other_salient)

    # Evaluate matching for each event
    event_results = []

    for idx, event in enumerate(events):
        output_text = _event_output_text(event)
        if output_text is None:
            continue

        normalized_output = _normalize_for_match(output_text)
        tool_query_matched = _tool_query_match(grounding, event)

        if has_ellipsis:
            # Ellipsis path
            if not _output_contains_excerpt(output_text, excerpt):
                continue
            raw_sim, span, matched_mass = _match_ellipsis_excerpt(excerpt, normalized_output)
            if span is None:
                continue

            max_window_len = max(len(normalized_excerpt) * 2.0, len(normalized_excerpt) + 50)
            span_locality_ok = (span[1] - span[0] <= max_window_len)

            # Check digit-completeness
            matched_span_text = normalized_output[span[0]:span[1]]
            span_digits = re.findall(r'\d+', matched_span_text)
            span_counts = Counter(span_digits)
            digit_ok = True
            for d, count in excerpt_digit_counts.items():
                if span_counts[d] < count:
                    digit_ok = False
                    break

            event_results.append({
                "index": idx,
                "raw_sim": raw_sim,
                "span": span,
                "matched_mass": matched_mass,
                "span_locality_ok": span_locality_ok,
                "digit_ok": digit_ok,
                "tool_query_matched": tool_query_matched,
                "normalized_output": normalized_output,
                "mass_ok": True,
                "sim_ok": True,
                "content_ok": True,
                "salient_ok": True,
                "anchor_ok": True,
            })
        else:
            # Non-ellipsis path
            raw_sim, span, matched_mass = _find_best_window(normalized_excerpt, normalized_output)
            if span is None or raw_sim <= 0.0:
                continue

            required_threshold = (tau - 0.05) if tool_query_matched else tau
            sim_ok = (raw_sim >= required_threshold)
            mass_ok = (matched_mass >= 12)

            matched_span_text = normalized_output[span[0]:span[1]]

            # Check digit-completeness
            span_digits = re.findall(r'\d+', matched_span_text)
            span_counts = Counter(span_digits)
            digit_ok = True
            for d, count in excerpt_digit_counts.items():
                if span_counts[d] < count:
                    digit_ok = False
                    break

            # Check salient-token presence
            span_tokens = _TOKEN_RE.findall(matched_span_text)
            salient_ok = True
            for t in excerpt_salient_tokens:
                if not any(levenshtein_distance(t.casefold(), st.casefold()) <= 2 for st in span_tokens):
                    salient_ok = False
                    break

            # Check content anchors
            matched_anchors = set()
            for d in excerpt_digits:
                if span_counts[d] > 0:
                    matched_anchors.add(d)
            for name in proper_noun_anchors:
                # all words in the proper noun must be matched
                if all(any(levenshtein_distance(w, st.casefold()) <= 2 for st in span_tokens) for w in name.split()):
                    matched_anchors.add(name)
            for w in other_salient:
                if any(levenshtein_distance(w, st.casefold()) <= 2 for st in span_tokens):
                    matched_anchors.add(w)

            num_excerpt_anchors = len(excerpt_content_anchors)
            num_matched_anchors = len(matched_anchors)
            anchor_ok = True
            if num_excerpt_anchors >= 2 and num_matched_anchors < 2:
                anchor_ok = False

            event_results.append({
                "index": idx,
                "raw_sim": raw_sim,
                "span": span,
                "matched_mass": matched_mass,
                "span_locality_ok": True,
                "digit_ok": digit_ok,
                "tool_query_matched": tool_query_matched,
                "normalized_output": normalized_output,
                "mass_ok": mass_ok,
                "sim_ok": sim_ok,
                "content_ok": True,
                "salient_ok": salient_ok,
                "anchor_ok": anchor_ok,
            })

    # Filter to candidates that pass all guards
    valid_candidates = []
    for res in event_results:
        if has_ellipsis:
            if res["span_locality_ok"] and res["digit_ok"]:
                valid_candidates.append(res)
        else:
            if (
                res["sim_ok"]
                and res["mass_ok"]
                and res["digit_ok"]
                and res["salient_ok"]
                and res["anchor_ok"]
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
        if not excerpt_digits:
            low_signal_reasons.append("no_digits")
        if len(excerpt_content_anchors) <= 1:
            low_signal_reasons.append("single_anchor")
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
        elif not best_attempt["digit_ok"]:
            reason = "digit_absent"
        else:
            reason = "below_tau"
    else:
        if not best_attempt["sim_ok"]:
            reason = "below_tau"
        elif not best_attempt["mass_ok"]:
            reason = "insufficient_mass"
        elif not best_attempt["digit_ok"]:
            reason = "digit_absent"
        elif not best_attempt["anchor_ok"]:
            reason = "single_anchor"
        elif not best_attempt["salient_ok"]:
            reason = "salient_token_absent"
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

