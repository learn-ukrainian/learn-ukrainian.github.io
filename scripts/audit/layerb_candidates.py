#!/usr/bin/env python3
"""Deterministic QG Layer A candidate materialization for Layer B.

``materialize_candidates`` is offline handoff code: it never changes the
enforcement gate's ``AnchorResult``.  It uses only the public stateless API in
``anchor_primitives`` and returns immutable records suitable for sidecars and
offline review.

Decision and reason contract
----------------------------
``ANCHOR`` is emitted only for a complete set of one or more candidates.
``REJECT`` is emitted for a complete absence of provenance (including an
explicit cross-event ellipsis join).  ``AUDIT`` is emitted for any incomplete
scan/capture, alignment failure, or flat gate reason with no registered Layer A
equivalent.  Reasons always use the registered 15-value Layer A vocabulary.

Candidate identity and canonicalization
---------------------------------------
Near-duplicate candidate windows are canonicalized *before* IDs are assigned.
The canonical content form normalizes Unicode/case/stress/whitespace and strips
punctuation.  Overlapping or two-code-point-jitter occurrences with identical
ordered canonical segment content merge to the lexicographically first span.
Separated repeated occurrences remain distinct: a deterministic occurrence
ordinal, derived from canonical output ordering rather than raw offsets, is
included with the canonical segment-content hashes.  This preserves complete
enumeration without making candidate IDs depend directly on raw offsets.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any

from scripts.audit import anchor_primitives

CANDIDATE_SCHEMA_VERSION = "qg-anchor-candidate.v1"
ANCHOR_SET_SCHEMA_VERSION = "qg-anchor-set.v1"
EVENT_OUTPUT_IDENTITY_VERSION = "qg-event-output.v1"
CANONICAL_SOURCE_IDENTITY_VERSION = "qg-canonical-source.v1"
MAX_SCANNED_OUTPUT_CHARS = 50_000
MAX_CANDIDATE_WINDOWS = 64
MAX_ELLIPSIS_ASSIGNMENTS = 64

REGISTERED_REASONS = frozenset(
    {
        "ANCHORED_CONTIGUOUS",
        "ANCHORED_ORDERED_SEGMENTS",
        "PRESENT_MULTI",
        "ABSENT",
        "FUZZY_AMBIGUOUS",
        "OUTSIDE_SCAN",
        "RAW_MAPPING_AMBIGUOUS",
        "CROSS_EVENT_STITCH_FORBIDDEN",
        "INCOMPLETE_CAPTURE",
        "INCOMPLETE_CANDIDATE_SET",
        "TOOL_ERROR",
        "INSUFFICIENT_MASS",
        "BELOW_TAU",
        "DIGIT_NOT_ALIGNED",
        "SALIENT_NOT_ALIGNED",
    }
)


@dataclass(frozen=True)
class AnchorSegment:
    """One losslessly mapped ordered evidence segment."""

    segment_index: int
    excerpt_normalized_start: int
    excerpt_normalized_end: int
    output_normalized_start: int
    output_normalized_end: int
    output_raw_start: int
    output_raw_end: int
    normalized_segment_sha256: str
    raw_segment_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnchorCandidate:
    """Immutable runtime candidate corresponding to one captured event output."""

    schema_version: str
    candidate_id: str
    event_output_id: str
    canonical_source_id: str
    source_index: int
    tool_identity: Mapping[str, str]
    query_identity: Mapping[str, str]
    raw_output_sha256: str
    normalized_output_sha256: str
    output_capture_complete: bool
    anchor_scan_complete: bool
    match_type: str
    similarity: float
    tool_query_matched: bool
    eligibility: str
    error_status: str
    ordered_segment_spans: tuple[AnchorSegment, ...]

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["tool_identity"] = dict(self.tool_identity)
        result["query_identity"] = dict(self.query_identity)
        result["ordered_segment_spans"] = [segment.to_dict() for segment in self.ordered_segment_spans]
        return result


@dataclass(frozen=True)
class AnchorSetResult:
    """Complete candidate enumeration result for one grounding."""

    schema_version: str
    decision: str
    reason: str
    candidate_set_complete: bool
    candidate_count_before_dedup: int
    candidates: tuple[AnchorCandidate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "decision": self.decision,
            "reason": self.reason,
            "candidate_set_complete": self.candidate_set_complete,
            "candidate_count_before_dedup": self.candidate_count_before_dedup,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass(frozen=True)
class _DraftCandidate:
    """Candidate before near-duplicate canonicalization and ID assignment."""

    event_output_id: str
    canonical_source_id: str
    source_index: int
    tool_identity: Mapping[str, str]
    query_identity: Mapping[str, str]
    raw_output_sha256: str
    normalized_output_sha256: str
    output_capture_complete: bool
    anchor_scan_complete: bool
    match_type: str
    similarity: float
    tool_query_matched: bool
    eligibility: str
    error_status: str
    ordered_segment_spans: tuple[AnchorSegment, ...]
    canonical_segment_hashes: tuple[str, ...]


def _sha256(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _capture_complete(event: Mapping[str, Any]) -> bool:
    """Return explicit capture completeness; unknown is treated as complete capture."""
    return (
        not any(event.get(key) is True for key in ("output_truncated", "truncated", "capture_truncated"))
        and event.get("output_capture_complete") is not False
    )


def _error_classification(event: Mapping[str, Any], output: Any, capture_complete: bool) -> tuple[str, str]:
    """Classify recognized output errors before textual matching."""
    if not capture_complete:
        return "INCOMPLETE_CAPTURE", "TRUNCATED_OUTPUT"
    if event.get("source_admissible") is False or event.get("admissible") is False:
        return "INADMISSIBLE_SOURCE", "NONE"
    status = str(event.get("status") or "").casefold()
    if status in {"error", "failed", "failure", "timeout", "cancelled"}:
        return "TOOL_ERROR", "TRANSPORT_ERROR"
    if isinstance(output, Mapping) and any(key in output for key in ("error", "errors", "exception")):
        return "TOOL_ERROR", "STRUCTURED_ERROR"
    if isinstance(output, str) and re.match(r"^\s*(?:error|помилка|exception)\b", output, flags=re.IGNORECASE):
        return "AMBIGUOUS_ERROR", "AMBIGUOUS_STRING_ERROR"
    return "ELIGIBLE", "NONE"


def _stable_source_material(event: Mapping[str, Any]) -> dict[str, Any]:
    """Extract only declared stable source fields; never infer IDs from prose."""
    keys = ("document_id", "source_id", "url", "revision", "section_id", "item_id")
    material: dict[str, Any] = {}
    for container in (event, event.get("input")):
        if isinstance(container, Mapping):
            for key in keys:
                value = container.get(key)
                if value not in (None, ""):
                    material[key] = value
    return material


def _event_identity(
    event: Mapping[str, Any],
    output_text: str,
    capture_complete: bool,
) -> tuple[str, str, Mapping[str, str], Mapping[str, str]]:
    raw_name = str(event.get("tool") or "")
    canonical_name = anchor_primitives.canonical_tool_name(raw_name)
    canonical_input = _canonical_json(event.get("input") if "input" in event else {})
    query_identity: Mapping[str, str] = {
        "canonical_json": canonical_input,
        "sha256": _sha256(canonical_input),
    }
    status_envelope = {
        "status": event.get("status"),
        "error": event.get("error"),
        "errors": event.get("errors"),
    }
    identity_material = {
        "version": EVENT_OUTPUT_IDENTITY_VERSION,
        "tool": canonical_name,
        "query": canonical_input,
        "status_envelope": status_envelope,
        "stable_source": _stable_source_material(event),
        "raw_output_sha256": _sha256(output_text),
        "output_capture_complete": capture_complete,
    }
    event_output_id = _sha256(_canonical_json(identity_material))
    stable_source = _stable_source_material(event)
    if stable_source:
        source_material = {
            "version": CANONICAL_SOURCE_IDENTITY_VERSION,
            "tool": canonical_name,
            "stable_source": stable_source,
            "query_mode": (event.get("input") or {}).get("mode") if isinstance(event.get("input"), Mapping) else None,
        }
        canonical_source_id = _sha256(_canonical_json(source_material))
    else:
        # Design §3.5: EVENT_OUTPUT_ONLY is the fail-closed fallback where no
        # stable source document identity was captured.
        canonical_source_id = event_output_id
    return (
        event_output_id,
        canonical_source_id,
        {"raw_name": raw_name, "canonical_name": canonical_name},
        query_identity,
    )


def _canonical_segment_content(normalized_segment: str) -> str:
    """Canonicalize formatting/punctuation jitter before candidate IDs exist."""
    return re.sub(r"[^\w]+", " ", anchor_primitives.normalize_for_match(normalized_segment)).strip()


def _make_segment(
    offset: anchor_primitives.OrderedSegmentOffset,
    *,
    normalized_output: str,
    raw_output: str,
) -> AnchorSegment | None:
    if offset.raw_start is None or offset.raw_end is None or offset.mapping_error is not None:
        return None
    if offset.output_normalized_start >= offset.output_normalized_end:
        return None
    if offset.raw_start >= offset.raw_end:
        return None
    normalized_segment = normalized_output[offset.output_normalized_start : offset.output_normalized_end]
    raw_segment = raw_output[offset.raw_start : offset.raw_end]
    if anchor_primitives.normalize_for_match(raw_segment) != normalized_segment:
        return None
    return AnchorSegment(
        segment_index=offset.segment_index,
        excerpt_normalized_start=offset.excerpt_normalized_start,
        excerpt_normalized_end=offset.excerpt_normalized_end,
        output_normalized_start=offset.output_normalized_start,
        output_normalized_end=offset.output_normalized_end,
        output_raw_start=offset.raw_start,
        output_raw_end=offset.raw_end,
        normalized_segment_sha256=_sha256(normalized_segment),
        raw_segment_sha256=_sha256(raw_segment),
    )


def _ellipsis_assignments(
    excerpt: str,
    normalized_output: str,
    alignment: anchor_primitives.NormalizedRawAlignment,
    *,
    max_assignments: int,
) -> tuple[tuple[tuple[AnchorSegment, ...], ...], bool, bool]:
    """Enumerate ordered same-event ellipsis assignments without stitching."""
    pieces = [piece for piece in anchor_primitives.excerpt_segments(excerpt) if len(piece[0]) >= 4]
    if not pieces:
        return (), False, False
    locations: list[list[int]] = []
    for segment, _excerpt_start, _excerpt_end in pieces:
        starts: list[int] = []
        cursor = 0
        while (position := normalized_output.find(segment, cursor)) != -1:
            starts.append(position)
            cursor = position + 1
        if not starts:
            return (), False, False
        locations.append(starts)

    assignments: list[tuple[AnchorSegment, ...]] = []
    mapping_failed = False
    truncated = False

    def visit(piece_index: int, previous_end: int, current: list[AnchorSegment]) -> None:
        nonlocal mapping_failed, truncated
        if len(assignments) >= max_assignments:
            truncated = True
            return
        if piece_index == len(pieces):
            assignments.append(tuple(current))
            return
        segment, excerpt_start, excerpt_end = pieces[piece_index]
        for output_start in locations[piece_index]:
            if output_start < previous_end:
                continue
            output_end = output_start + len(segment)
            raw_span = alignment.raw_span_for(output_start, output_end)
            if raw_span is None:
                mapping_failed = True
                continue
            raw_start, raw_end = raw_span
            raw_segment = alignment.raw[raw_start:raw_end]
            if anchor_primitives.normalize_for_match(raw_segment) != segment:
                mapping_failed = True
                continue
            current.append(
                AnchorSegment(
                    segment_index=piece_index,
                    excerpt_normalized_start=excerpt_start,
                    excerpt_normalized_end=excerpt_end,
                    output_normalized_start=output_start,
                    output_normalized_end=output_end,
                    output_raw_start=raw_start,
                    output_raw_end=raw_end,
                    normalized_segment_sha256=_sha256(segment),
                    raw_segment_sha256=_sha256(raw_segment),
                )
            )
            visit(piece_index + 1, output_end, current)
            current.pop()
            if truncated:
                return

    visit(0, 0, [])
    return tuple(assignments), truncated, mapping_failed


def _candidate_id(draft: _DraftCandidate, occurrence_ordinal: int) -> str:
    """Hash canonical content and ordering ordinal, never raw offsets."""
    material = {
        "version": CANDIDATE_SCHEMA_VERSION,
        "event_output_id": draft.event_output_id,
        "match_type": draft.match_type,
        "canonical_segment_sha256": draft.canonical_segment_hashes,
        "occurrence_ordinal": occurrence_ordinal,
        "raw_output_sha256": draft.raw_output_sha256,
        "normalized_output_sha256": draft.normalized_output_sha256,
    }
    return _sha256(_canonical_json(material))


def _near_duplicate(left: _DraftCandidate, right: _DraftCandidate) -> bool:
    if left.event_output_id != right.event_output_id or left.canonical_segment_hashes != right.canonical_segment_hashes:
        return False
    if len(left.ordered_segment_spans) != len(right.ordered_segment_spans):
        return False
    return all(
        max(a.output_normalized_start, b.output_normalized_start)
        <= min(a.output_normalized_end, b.output_normalized_end) + 2
        for a, b in zip(left.ordered_segment_spans, right.ordered_segment_spans, strict=True)
    )


def _draft_order_key(draft: _DraftCandidate) -> tuple[Any, ...]:
    return (
        draft.event_output_id,
        draft.match_type,
        draft.canonical_segment_hashes,
        tuple(
            (segment.output_normalized_start, segment.output_normalized_end) for segment in draft.ordered_segment_spans
        ),
    )


def _canonicalize_drafts(drafts: Iterable[_DraftCandidate]) -> tuple[AnchorCandidate, ...]:
    """Merge near-duplicate windows before stable candidate ID assignment."""
    retained: list[_DraftCandidate] = []
    for draft in sorted(drafts, key=_draft_order_key):
        if retained and _near_duplicate(retained[-1], draft):
            continue
        retained.append(draft)
    ordinals: dict[tuple[str, str, tuple[str, ...]], int] = {}
    candidates: list[AnchorCandidate] = []
    for draft in retained:
        identity_key = (draft.event_output_id, draft.match_type, draft.canonical_segment_hashes)
        ordinal = ordinals.get(identity_key, 0)
        ordinals[identity_key] = ordinal + 1
        candidates.append(
            AnchorCandidate(
                schema_version=CANDIDATE_SCHEMA_VERSION,
                candidate_id=_candidate_id(draft, ordinal),
                event_output_id=draft.event_output_id,
                canonical_source_id=draft.canonical_source_id,
                source_index=draft.source_index,
                tool_identity=draft.tool_identity,
                query_identity=draft.query_identity,
                raw_output_sha256=draft.raw_output_sha256,
                normalized_output_sha256=draft.normalized_output_sha256,
                output_capture_complete=draft.output_capture_complete,
                anchor_scan_complete=draft.anchor_scan_complete,
                match_type=draft.match_type,
                similarity=draft.similarity,
                tool_query_matched=draft.tool_query_matched,
                eligibility=draft.eligibility,
                error_status=draft.error_status,
                ordered_segment_spans=draft.ordered_segment_spans,
            )
        )
    return tuple(candidates)


def map_flat_anchor_reason(flat_reason: str, *, has_ellipsis: bool = False) -> tuple[str, str]:
    """Map every legacy flat gate reason into a registered reason and decision.

    ``no_output`` and ``no_salient_anchor`` have no registered Layer A enum
    equivalent.  They deliberately map to an AUDIT-class completeness failure,
    as does any future unknown reason; no value is silently invented.
    """
    if flat_reason == "anchored":
        return "ANCHOR", "ANCHORED_ORDERED_SEGMENTS" if has_ellipsis else "ANCHORED_CONTIGUOUS"
    if flat_reason == "abstain_ambiguous":
        return "AUDIT", "FUZZY_AMBIGUOUS"
    if flat_reason == "candidate_truncated":
        return "AUDIT", "OUTSIDE_SCAN"
    if flat_reason in {"below_tau", "digit_not_aligned", "insufficient_mass", "salient_not_aligned"}:
        return "REJECT", flat_reason.upper()
    return "AUDIT", "INCOMPLETE_CANDIDATE_SET"


def _cross_event_stitch_attempt(excerpt: str, normalized_outputs: Sequence[str]) -> bool:
    """Detect fragments that occur only across multiple event outputs."""
    pieces = [piece for piece, _, _ in anchor_primitives.excerpt_segments(excerpt) if len(piece) >= 4]
    if len(pieces) < 2:
        return False
    matched_outputs = {
        output_index for piece in pieces for output_index, output in enumerate(normalized_outputs) if piece in output
    }
    return len(matched_outputs) > 1


def _draft_from_segments(
    *,
    segments: tuple[AnchorSegment, ...],
    normalized_output: str,
    event_output_id: str,
    canonical_source_id: str,
    source_index: int,
    tool_identity: Mapping[str, str],
    query_identity: Mapping[str, str],
    raw_output: str,
    output_capture_complete: bool,
    anchor_scan_complete: bool,
    match_type: str,
    similarity: float,
    tool_query_matched: bool,
    eligibility: str,
    error_status: str,
) -> _DraftCandidate:
    """Build a pre-ID candidate from one complete, mapped segment sequence."""
    canonical_hashes = tuple(
        _sha256(
            _canonical_segment_content(
                normalized_output[segment.output_normalized_start : segment.output_normalized_end]
            )
        )
        for segment in segments
    )
    return _DraftCandidate(
        event_output_id=event_output_id,
        canonical_source_id=canonical_source_id,
        source_index=source_index,
        tool_identity=tool_identity,
        query_identity=query_identity,
        raw_output_sha256=_sha256(raw_output),
        normalized_output_sha256=_sha256(anchor_primitives.normalize_for_match(raw_output)),
        output_capture_complete=output_capture_complete,
        anchor_scan_complete=anchor_scan_complete,
        match_type=match_type,
        similarity=similarity,
        tool_query_matched=tool_query_matched,
        eligibility=eligibility,
        error_status=error_status,
        ordered_segment_spans=segments,
        canonical_segment_hashes=canonical_hashes,
    )


def materialize_candidates(
    grounding: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    *,
    tau: float = 0.75,
    max_scanned_output_chars: int = MAX_SCANNED_OUTPUT_CHARS,
    max_candidate_windows: int = MAX_CANDIDATE_WINDOWS,
    max_ellipsis_assignments: int = MAX_ELLIPSIS_ASSIGNMENTS,
) -> AnchorSetResult:
    """Enumerate immutable Layer B candidates for one grounding.

    Bounds are explicit because a bounded/partial enumeration is not an anchor:
    it returns ``AUDIT`` with a registered completeness reason.
    """
    excerpt = str(grounding.get("evidence_excerpt") or "").strip()
    if not excerpt:
        return AnchorSetResult(ANCHOR_SET_SCHEMA_VERSION, "REJECT", "INSUFFICIENT_MASS", True, 0, ())
    normalized_excerpt = anchor_primitives.normalize_for_match(excerpt)
    salient_tokens = anchor_primitives.find_salient_tokens(excerpt, normalized_excerpt)
    if not salient_tokens:
        # The legacy flat `no_salient_anchor` is outside the registered enum.
        decision, reason = map_flat_anchor_reason("no_salient_anchor")
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            decision,
            reason,
            False,
            0,
            (),
        )

    has_ellipsis = bool(anchor_primitives.ELLIPSIS_RE.search(excerpt))
    drafts: list[_DraftCandidate] = []
    normalized_outputs: list[str] = []
    any_output = False
    complete = True
    saw_mapping_failure = False
    saw_capture_incomplete = False
    saw_scan_truncation = False

    for source_index, event in enumerate(events):
        raw_output = anchor_primitives.event_output_text(event)
        if raw_output is None:
            if event.get("status") not in (None, "completed"):
                saw_capture_incomplete = True
            continue
        any_output = True
        capture_complete = _capture_complete(event)
        if not capture_complete:
            complete = False
            saw_capture_incomplete = True
        output_for_scan = raw_output[:max_scanned_output_chars]
        if len(raw_output) > max_scanned_output_chars:
            complete = False
            saw_scan_truncation = True
        alignment = anchor_primitives.build_normalized_raw_alignment(output_for_scan)
        normalized_output = alignment.normalized
        normalized_outputs.append(normalized_output)
        event_output_id, canonical_source_id, tool_identity, query_identity = _event_identity(
            event, raw_output, capture_complete
        )
        eligibility, error_status = _error_classification(event, event.get("output"), capture_complete)
        tool_query_matched = _tool_query_match(grounding, event)

        if has_ellipsis:
            assignments, truncated, mapping_failed = _ellipsis_assignments(
                excerpt,
                normalized_output,
                alignment,
                max_assignments=max_ellipsis_assignments,
            )
            if truncated:
                complete = False
                saw_scan_truncation = True
            if mapping_failed:
                complete = False
                saw_mapping_failure = True
            evidence_mass = sum(
                len(segment.replace(" ", ""))
                for segment, _, _ in anchor_primitives.excerpt_segments(excerpt)
                if len(segment) >= 4
            )
            if evidence_mass < 12:
                continue
            for segments in assignments:
                # Exact fragments make every salient token within a fragment
                # aligned by construction; no enclosing-window collapse occurs.
                drafts.append(
                    _draft_from_segments(
                        segments=segments,
                        normalized_output=normalized_output,
                        event_output_id=event_output_id,
                        canonical_source_id=canonical_source_id,
                        source_index=source_index,
                        tool_identity=tool_identity,
                        query_identity=query_identity,
                        raw_output=raw_output,
                        output_capture_complete=capture_complete,
                        anchor_scan_complete=not truncated and len(raw_output) <= max_scanned_output_chars,
                        match_type="ORDERED_EXACT_SEGMENTS",
                        similarity=1.0,
                        tool_query_matched=tool_query_matched,
                        eligibility=eligibility,
                        error_status=error_status,
                    )
                )
            continue

        search = anchor_primitives.find_candidate_windows(
            normalized_excerpt,
            normalized_output,
            salient_tokens=salient_tokens,
            max_candidates=max_candidate_windows,
        )
        if search.truncated:
            complete = False
            saw_scan_truncation = True
            continue
        for match in search.matches:
            if match.span is None:
                continue
            assessment = anchor_primitives.assess_window(
                normalized_excerpt, normalized_output[match.span[0] : match.span[1]], salient_tokens
            )
            required_threshold = tau - 0.05 if tool_query_matched else tau
            if (
                assessment.similarity < required_threshold
                or match.matched_non_space_mass < 12
                or not assessment.digit_aligned
                or not assessment.salient_aligned
            ):
                continue
            raw_span = alignment.raw_span_for(*match.span)
            if raw_span is None:
                complete = False
                saw_mapping_failure = True
                continue
            raw_start, raw_end = raw_span
            segment = AnchorSegment(
                segment_index=0,
                excerpt_normalized_start=0,
                excerpt_normalized_end=len(normalized_excerpt),
                output_normalized_start=match.span[0],
                output_normalized_end=match.span[1],
                output_raw_start=raw_start,
                output_raw_end=raw_end,
                normalized_segment_sha256=_sha256(normalized_output[match.span[0] : match.span[1]]),
                raw_segment_sha256=_sha256(output_for_scan[raw_start:raw_end]),
            )
            match_type = "EXACT_CONTIGUOUS" if assessment.similarity == 1.0 else "FUZZY_CONTIGUOUS"
            drafts.append(
                _draft_from_segments(
                    segments=(segment,),
                    normalized_output=normalized_output,
                    event_output_id=event_output_id,
                    canonical_source_id=canonical_source_id,
                    source_index=source_index,
                    tool_identity=tool_identity,
                    query_identity=query_identity,
                    raw_output=raw_output,
                    output_capture_complete=capture_complete,
                    anchor_scan_complete=len(raw_output) <= max_scanned_output_chars,
                    match_type=match_type,
                    similarity=assessment.similarity,
                    tool_query_matched=tool_query_matched,
                    eligibility=eligibility,
                    error_status=error_status,
                )
            )

    candidates = _canonicalize_drafts(drafts)
    if saw_mapping_failure:
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            "AUDIT",
            "RAW_MAPPING_AMBIGUOUS",
            False,
            len(drafts),
            candidates,
        )
    if saw_capture_incomplete:
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            "AUDIT",
            "INCOMPLETE_CAPTURE",
            False,
            len(drafts),
            candidates,
        )
    if not complete or saw_scan_truncation:
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            "AUDIT",
            "OUTSIDE_SCAN",
            False,
            len(drafts),
            candidates,
        )
    if candidates:
        reason = "ANCHORED_ORDERED_SEGMENTS" if has_ellipsis else "ANCHORED_CONTIGUOUS"
        return AnchorSetResult(ANCHOR_SET_SCHEMA_VERSION, "ANCHOR", reason, True, len(drafts), candidates)
    if has_ellipsis and _cross_event_stitch_attempt(excerpt, normalized_outputs):
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            "REJECT",
            "CROSS_EVENT_STITCH_FORBIDDEN",
            True,
            0,
            (),
        )
    if not any_output:
        decision, reason = map_flat_anchor_reason("no_output")
        return AnchorSetResult(
            ANCHOR_SET_SCHEMA_VERSION,
            decision,
            reason,
            False,
            0,
            (),
        )
    decision, reason = map_flat_anchor_reason("below_tau")
    return AnchorSetResult(ANCHOR_SET_SCHEMA_VERSION, decision, reason, True, 0, ())


def _tool_query_match(grounding: Mapping[str, Any], event: Mapping[str, Any]) -> bool:
    tool = anchor_primitives.canonical_tool_name(grounding.get("tool"))
    if tool and anchor_primitives.canonical_tool_name(event.get("tool")) != tool:
        return False
    query = str(grounding.get("query") or "").strip()
    return bool(query) and anchor_primitives.event_input_matches_query(event, query)


def diff_runtime_records_to_label_case(
    runtime: AnchorSetResult | Mapping[str, Any], label_case: Mapping[str, Any]
) -> tuple[str, ...]:
    """Return deterministic field-level differences against a Phase 0 label case.

    Label-only expected relation/support fields are intentionally excluded.  The
    label schema groups candidates by ``event_output_id``; runtime carries it
    explicitly, so this function reconciles the two shapes without guessing.
    """
    runtime_record = runtime.to_dict() if isinstance(runtime, AnchorSetResult) else dict(runtime)
    differences: list[str] = []
    expected_decision = label_case.get("expected_layer_a_decision")
    if runtime_record.get("decision") != expected_decision:
        differences.append(f"decision: runtime={runtime_record.get('decision')!r} label={expected_decision!r}")
    expected_reason = label_case.get("expected_layer_a_reason")
    if runtime_record.get("reason") != expected_reason:
        differences.append(f"reason: runtime={runtime_record.get('reason')!r} label={expected_reason!r}")
    if runtime_record.get("candidate_set_complete") != label_case.get("candidate_set_complete"):
        differences.append("candidate_set_complete differs")
    labels_by_id = label_case.get("candidates_by_event_output_id")
    if not isinstance(labels_by_id, Mapping):
        return (*differences, "label candidates_by_event_output_id is missing or malformed")
    runtime_candidates = runtime_record.get("candidates")
    if not isinstance(runtime_candidates, list):
        return (*differences, "runtime candidates is missing or malformed")
    label_candidates = {
        candidate.get("candidate_id"): (event_output_id, candidate)
        for event_output_id, grouped in labels_by_id.items()
        if isinstance(grouped, list)
        for candidate in grouped
        if isinstance(candidate, Mapping) and isinstance(candidate.get("candidate_id"), str)
    }
    runtime_ids = {candidate.get("candidate_id") for candidate in runtime_candidates if isinstance(candidate, Mapping)}
    for candidate_id in sorted(identifier for identifier in runtime_ids if isinstance(identifier, str)):
        runtime_candidate = next(
            candidate for candidate in runtime_candidates if candidate.get("candidate_id") == candidate_id
        )
        label_pair = label_candidates.get(candidate_id)
        if label_pair is None:
            differences.append(f"unexpected runtime candidate {candidate_id}")
            continue
        event_output_id, label_candidate = label_pair
        if runtime_candidate.get("event_output_id") != event_output_id:
            differences.append(f"{candidate_id}: event_output_id differs")
        for field in (
            "canonical_source_id",
            "source_index",
            "tool_identity",
            "query_identity",
            "raw_output_sha256",
            "normalized_output_sha256",
            "output_capture_complete",
            "anchor_scan_complete",
            "match_type",
            "eligibility",
            "error_status",
            "ordered_segment_spans",
        ):
            if runtime_candidate.get(field) != label_candidate.get(field):
                differences.append(f"{candidate_id}: {field} differs")
        if repr(runtime_candidate.get("similarity")) != repr(label_candidate.get("similarity")):
            differences.append(f"{candidate_id}: similarity differs")
    for candidate_id in sorted(identifier for identifier in label_candidates if identifier not in runtime_ids):
        differences.append(f"missing runtime candidate {candidate_id}")
    return tuple(differences)
