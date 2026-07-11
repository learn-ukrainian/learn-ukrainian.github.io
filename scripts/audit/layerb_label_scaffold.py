#!/usr/bin/env python3
"""Emit resumable Layer B annotation scaffolds from frozen keyed evidence.

This is offline handoff tooling.  It fills source-derived identity material and
leaves every human judgment field as ``null``.  Packets include navigation
windows, but their explicit contract requires annotators to read the complete
raw captured output before deciding any relation or support span.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "scripts"))

from scripts.audit import anchor_primitives
from scripts.audit.layerb_keys import _build_event_index
from scripts.audit.layerb_label_common import (
    LabelJoinError,
    atomic_write_json,
    atomic_write_jsonl,
    fact_check_index_from_key,
    load_corpus,
    read_json,
    sha256_file,
    sha256_text,
    shadow_rows,
    union_rows,
)

JUDGMENT_CASE_FIELDS = (
    "claim_is_true",
    "expected_reviewer_verdict",
    "expected_layer_a_decision",
    "expected_layer_a_reason",
    "expected_aggregate_relation",
    "expected_fact_check_decision",
    "context_sufficient",
    "failure_class",
    "corpus_verification_status",
    "annotators",
    "adjudication",
)
JUDGMENT_CANDIDATE_FIELDS = ("expected_source_relation", "expected_support_spans")
WORKING_CASE_REQUIRED = (
    "case_id",
    "artifact_sha256",
    "fixture_id",
    "fact_check_id",
    "fact_check_index",
    "claim",
    "evidence_excerpt",
    "claim_is_true",
    "expected_reviewer_verdict",
    "expected_layer_a_decision",
    "expected_layer_a_reason",
    "anchor_scan_complete",
    "candidate_set_complete",
    "candidates_by_event_output_id",
    "expected_aggregate_relation",
    "expected_fact_check_decision",
    "context_sufficient",
    "failure_class",
    "corpus_verification_status",
)
WORKING_CANDIDATE_REQUIRED = (
    "candidate_id",
    "canonical_source_id",
    "source_index",
    "tool_identity",
    "query_identity",
    "raw_output_sha256",
    "normalized_output_sha256",
    "output_capture_complete",
    "anchor_scan_complete",
    "match_type",
    "similarity",
    "eligibility",
    "error_status",
    "ordered_segment_spans",
    "expected_source_relation",
    "expected_support_spans",
)
SHA_FIELDS = (
    "candidate_id",
    "canonical_source_id",
    "raw_output_sha256",
    "normalized_output_sha256",
)
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
WINDOW_COMMENT = "NAVIGATION AID ONLY — decisions require the full raw artifact read."
HINT_COMMENT = "NON-authoritative fixture hint; establish claim truth independently per the annotation guide."
REVIEWER_VERDICTS = {
    "CONFIRMED",
    "REFUTED_BY_CONTRADICTION",
    "UNATTESTED_AFTER_SEARCH",
    "CONTESTED",
    "UNVERIFIED_INSUFFICIENT_SEARCH",
}
LAYER_A_DECISIONS = {"ANCHOR", "REJECT", "AUDIT"}
LAYER_A_REASONS = {
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
SOURCE_RELATIONS = {
    "ENTAILS",
    "CONTRADICTS",
    "EXPLICITLY_UNCERTAIN",
    "NO_RELATION",
    "MIXED",
    "TOOL_ERROR",
    "INSUFFICIENT_CONTEXT",
}
AGGREGATE_RELATIONS = SOURCE_RELATIONS | {"ABSTAIN"}
FACT_CHECK_DECISIONS = {"ACCEPT", "REJECT", "AUDIT"}
FAILURE_CLASSES = {
    "FABRICATED_EXCERPT_VALUE",
    "ALTERED_CLAIM_VALUE",
    "MEANING_INVERSION",
    "ATTRIBUTION_OR_ROLE_SWAP",
    "OVER_GENERALIZATION",
    "ELLIPSIZED_GENUINE_EXCERPT",
    "CROSS_EVENT_JOIN",
    "LEXICAL_VARIANT",
    "TOOL_ERROR_AS_EVIDENCE",
    "MISSING_CONTRADICTORY_CANDIDATE",
    "WRONG_NORMALIZED_RAW_MAPPING",
    "CANONICAL_IDENTITY_FAILURE",
    "PROMPT_INJECTION",
    "IRRELEVANT_SUPPORT_OFFSET",
    "JUDGE_TIMEOUT_OR_MALFORMED_RESULT",
    "SEARCH_ONLY_WITHOUT_COVERAGE_PROOF",
}
CORPUS_STATUSES = {"VERIFIED", "FIXTURE_ATTESTED", "UNVERIFIED", "NOT_APPLICABLE"}
SUPPORT_ROLES = {"SUPPORTS", "CONTRADICTS", "UNCERTAINTY"}


def _artifact_events(artifact: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    dispatch = artifact.get("dispatch")
    events = dispatch.get("tool_events") if isinstance(dispatch, Mapping) else None
    if not isinstance(events, list):
        return []
    return [event for event in events if isinstance(event, Mapping)]


def verify_candidate_segments(
    candidate: Mapping[str, Any], event_output_id: str, outputs: Mapping[str, str]
) -> tuple[str, str]:
    """Re-hash every recorded segment against the captured raw source bytes.

    The shadow record is immutable input, not an authority for its own offsets
    or hashes.  Every candidate copied into a scaffold therefore has to prove
    its raw and normalized spans again at emission time.
    """
    raw_output = outputs.get(event_output_id)
    if raw_output is None:
        raise LabelJoinError(f"candidate event output is unavailable: {event_output_id}")
    if sha256_text(raw_output) != candidate.get("raw_output_sha256"):
        raise LabelJoinError(f"candidate raw-output hash mismatch: {event_output_id}")
    normalized_output = anchor_primitives.normalize_for_match(raw_output)
    if sha256_text(normalized_output) != candidate.get("normalized_output_sha256"):
        raise LabelJoinError(f"candidate normalized-output hash mismatch: {event_output_id}")
    segments = candidate.get("ordered_segment_spans")
    if not isinstance(segments, list) or not segments:
        raise LabelJoinError(f"candidate has no ordered segment spans: {event_output_id}")
    previous_normalized_end = 0
    previous_raw_end = 0
    for expected_index, segment in enumerate(segments):
        if not isinstance(segment, Mapping) or segment.get("segment_index") != expected_index:
            raise LabelJoinError(f"candidate segment indices are not consecutive: {event_output_id}")
        offsets = (
            "output_normalized_start",
            "output_normalized_end",
            "output_raw_start",
            "output_raw_end",
        )
        values = [segment.get(name) for name in offsets]
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            raise LabelJoinError(f"candidate segment offsets are not integer values: {event_output_id}")
        normalized_start, normalized_end, raw_start, raw_end = values
        if not (
            0 <= normalized_start < normalized_end <= len(normalized_output)
            and 0 <= raw_start < raw_end <= len(raw_output)
            and previous_normalized_end <= normalized_start
            and previous_raw_end <= raw_start
        ):
            raise LabelJoinError(f"candidate segment spans are out of bounds or overlap: {event_output_id}")
        normalized_segment = normalized_output[normalized_start:normalized_end]
        raw_segment = raw_output[raw_start:raw_end]
        if anchor_primitives.normalize_for_match(raw_segment) != normalized_segment:
            raise LabelJoinError(f"candidate normalized-to-raw segment mapping does not round trip: {event_output_id}")
        if sha256_text(normalized_segment) != segment.get("normalized_segment_sha256") or sha256_text(
            raw_segment
        ) != segment.get("raw_segment_sha256"):
            raise LabelJoinError(f"candidate segment SHA-256 does not match captured output: {event_output_id}")
        previous_normalized_end = normalized_end
        previous_raw_end = raw_end
    return raw_output, normalized_output


def _schema_candidate(candidate: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    event_output_id = candidate.get("event_output_id")
    if not isinstance(event_output_id, str) or not SHA_RE.fullmatch(event_output_id):
        raise LabelJoinError(f"candidate has invalid event_output_id: {event_output_id!r}")
    result = {
        key: candidate[key]
        for key in WORKING_CANDIDATE_REQUIRED
        if key not in JUDGMENT_CANDIDATE_FIELDS and key in candidate
    }
    missing = sorted(set(WORKING_CANDIDATE_REQUIRED) - set(result) - set(JUDGMENT_CANDIDATE_FIELDS))
    if missing:
        raise LabelJoinError(f"candidate {event_output_id} is missing mechanical fields: {', '.join(missing)}")
    result["expected_source_relation"] = None
    result["expected_support_spans"] = None
    return event_output_id, result


def _source_artifact_path(corpus_dir: Path, artifact_name: str) -> str:
    """Produce the required repository-relative path where the caller supplied one."""
    path = corpus_dir / artifact_name
    for ancestor in (path, *path.parents):
        if ancestor.name == "audit":
            return str(path.relative_to(ancestor.parent))
    return artifact_name


def _fixture_source(
    fixture_id: str,
    *,
    corpus_dir: Path,
    artifact_name: str,
    corpus: Mapping[str, Mapping[str, Any]],
    selection_mode: str | None,
) -> dict[str, str]:
    """Pin a canonical fixture or an explicitly embedded corpus fixture."""
    fixture_path = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "qg_bakeoff" / f"{fixture_id}.json"
    if fixture_path.is_file():
        return {"path": str(fixture_path), "sha256": sha256_file(fixture_path)}
    if selection_mode != "select-all-from-source-artifacts":
        raise LabelJoinError(f"fixture file required for scaffold source hashes is absent: {fixture_path}")
    artifact = corpus.get(artifact_name)
    fixture = artifact.get("fixture") if isinstance(artifact, Mapping) else None
    if not isinstance(fixture, Mapping) or fixture.get("slug") != fixture_id:
        raise LabelJoinError(
            f"embedded fixture source does not match {fixture_id!r} in corpus artifact {artifact_name!r}"
        )
    artifact_path = corpus_dir / artifact_name
    return {
        "path": str(artifact_path),
        "sha256": sha256_file(artifact_path),
        "provenance": "embedded-corpus-artifact",
    }


def _case_from_row(
    row: Mapping[str, Any],
    shadow: Mapping[str, Any],
    *,
    corpus_dir: Path,
    corpus: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], str, int]:
    grounding_key = row.get("grounding_key")
    if not isinstance(grounding_key, str) or grounding_key != shadow.get("grounding_key"):
        raise LabelJoinError(f"keyed row does not exactly resolve to a shadow grounding key: {grounding_key!r}")
    if row.get("fact_check_index") != fact_check_index_from_key(grounding_key):
        raise LabelJoinError(f"keyed row fact_check_index does not match grounding key: {grounding_key!r}")
    artifact_name = shadow.get("artifact")
    if not isinstance(artifact_name, str) or artifact_name not in corpus:
        raise LabelJoinError(f"shadow artifact is unavailable: {artifact_name!r}")
    artifact_path = corpus_dir / artifact_name
    artifact = corpus[artifact_name]
    layer_a = shadow.get("layer_a")
    if not isinstance(layer_a, Mapping):
        raise LabelJoinError(f"shadow {grounding_key} has no Layer A record")
    candidates = layer_a.get("candidates")
    if not isinstance(candidates, list):
        raise LabelJoinError(f"shadow {grounding_key} has malformed Layer A candidates")
    event_outputs = _build_event_index(_artifact_events(artifact))
    grouped_candidates: dict[str, list[dict[str, Any]]] = {}
    segment_verified_candidates = 0
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise LabelJoinError(f"shadow {grounding_key} includes a non-object candidate")
        event_output_id, shaped = _schema_candidate(candidate)
        verify_candidate_segments(shaped, event_output_id, event_outputs)
        segment_verified_candidates += 1
        grouped_candidates.setdefault(event_output_id, []).append(shaped)
    all_scans_complete = all(candidate.get("anchor_scan_complete") is True for candidate in candidates)
    case: dict[str, Any] = {
        "case_id": grounding_key,
        "artifact_sha256": sha256_file(artifact_path),
        "fixture_id": str(shadow.get("fixture") or row.get("fixture") or ""),
        "fact_check_id": str(shadow.get("fact_check_id") or grounding_key),
        "fact_check_index": fact_check_index_from_key(grounding_key),
        "claim": str(row.get("claim") or shadow.get("claim") or ""),
        "evidence_excerpt": str(row.get("excerpt") or ""),
        "claim_is_true": None,
        "expected_reviewer_verdict": None,
        "expected_layer_a_decision": None,
        "expected_layer_a_reason": None,
        "anchor_scan_complete": all_scans_complete,
        "candidate_set_complete": layer_a.get("candidate_set_complete") is True,
        "candidates_by_event_output_id": grouped_candidates,
        "expected_aggregate_relation": None,
        "expected_fact_check_decision": None,
        "context_sufficient": None,
        "failure_class": None,
        "corpus_verification_status": None,
        "annotators": None,
        "adjudication": None,
    }
    if not case["fixture_id"] or not case["claim"] or not case["evidence_excerpt"]:
        raise LabelJoinError(f"shadow {grounding_key} cannot produce a complete mechanical case identity")
    packet = _packet_case(case, row, artifact, corpus_dir=corpus_dir)
    return case, packet, artifact_name, segment_verified_candidates


def _candidate_navigation(
    candidate: Mapping[str, Any], event_output_id: str, outputs: Mapping[str, str]
) -> dict[str, Any]:
    raw_output, normalized_output = verify_candidate_segments(candidate, event_output_id, outputs)
    segments = candidate.get("ordered_segment_spans")
    assert isinstance(segments, list) and segments
    normalized_start = min(int(segment["output_normalized_start"]) for segment in segments)
    normalized_end = max(int(segment["output_normalized_end"]) for segment in segments)
    raw_start = min(int(segment["output_raw_start"]) for segment in segments)
    raw_end = max(int(segment["output_raw_end"]) for segment in segments)
    if not (
        0 <= normalized_start < normalized_end <= len(normalized_output) and 0 <= raw_start < raw_end <= len(raw_output)
    ):
        raise LabelJoinError(f"candidate span is outside captured output: {event_output_id}")
    return {
        "event_output_id": event_output_id,
        "full_output_sha256": sha256_text(raw_output),
        "full_output_bytes": len(raw_output.encode("utf-8")),
        "normalized_window_start": max(0, normalized_start - 800),
        "normalized_window_end": min(len(normalized_output), normalized_end + 800),
        "normalized_window_text": normalized_output[
            max(0, normalized_start - 800) : min(len(normalized_output), normalized_end + 800)
        ],
        "raw_window_start": max(0, raw_start - 800),
        "raw_window_end": min(len(raw_output), raw_end + 800),
        "raw_window_text": raw_output[max(0, raw_start - 800) : min(len(raw_output), raw_end + 800)],
        "comment": WINDOW_COMMENT,
    }


def _packet_case(
    case: Mapping[str, Any], row: Mapping[str, Any], artifact: Mapping[str, Any], *, corpus_dir: Path
) -> dict[str, Any]:
    outputs = _build_event_index(_artifact_events(artifact))
    navigation: list[dict[str, Any]] = []
    candidates_by_output = case["candidates_by_event_output_id"]
    for event_output_id in sorted(candidates_by_output):
        for candidate in candidates_by_output[event_output_id]:
            navigation.append(_candidate_navigation(candidate, event_output_id, outputs))
    artifact_name = str(case["case_id"]).split("#fact_checks[", maxsplit=1)[0]
    return {
        "packet_version": "qg-layer-b-work-packet.v2",
        "comment": WINDOW_COMMENT,
        "case": dict(case),
        "gold_is_true_hint": row.get("gold_is_true"),
        "gold_is_true_hint_comment": HINT_COMMENT,
        "union_categories": list(row.get("union_categories") or []),
        "corpus_artifact_path": _source_artifact_path(corpus_dir, artifact_name),
        "source_index": row.get("source_index"),
        "candidate_navigation": navigation,
    }


def _done_marker_path(packets_dir: Path, shard: int) -> Path:
    return packets_dir / f"shard-{shard:02d}.done.json"


def _packet_checksum(path: Path) -> str:
    return sha256_file(path)


def _write_shard(path: Path, rows: list[dict[str, Any]], shard: int, *, resume: bool) -> None:
    marker = _done_marker_path(path.parent, shard)
    if resume and path.is_file() and marker.is_file():
        state = read_json(marker)
        if (
            isinstance(state, Mapping)
            and state.get("sha256") == _packet_checksum(path)
            and state.get("count") == len(rows)
        ):
            expected_ids = [str(row["case"]["case_id"]) for row in rows]
            if state.get("case_ids") == expected_ids:
                return
    atomic_write_jsonl(path, rows)
    atomic_write_json(
        marker,
        {
            "shard": shard,
            "sha256": _packet_checksum(path),
            "count": len(rows),
            "case_ids": [str(row["case"]["case_id"]) for row in rows],
        },
    )


def build_scaffold(
    keyed_document: Mapping[str, Any],
    shadow_document: Mapping[str, Any],
    *,
    corpus_dir: Path,
    output_dir: Path,
    shard_count: int = 4,
    resume: bool = True,
    crash_after_shards: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the null-judgment scaffold and atomically materialize its packets."""
    if shard_count < 1:
        raise LabelJoinError("shard_count must be positive")
    keyed_rows = union_rows(keyed_document)
    shadows = shadow_rows(shadow_document)
    shadow_by_key = {str(row.get("grounding_key")): row for row in shadows}
    if len(shadow_by_key) != len(shadows):
        raise LabelJoinError("phase1 shadow contains duplicate grounding_key values")
    corpus = load_corpus(corpus_dir)
    cases: list[dict[str, Any]] = []
    packets: list[dict[str, Any]] = []
    used_artifacts: set[str] = set()
    seen_cases: set[str] = set()
    segment_verified_candidates = 0
    for row in keyed_rows:
        key = row.get("grounding_key")
        shadow = shadow_by_key.get(str(key))
        if shadow is None:
            raise LabelJoinError(f"keyed union contains missing shadow grounding key: {key!r}")
        case, packet, artifact_name, verified_count = _case_from_row(row, shadow, corpus_dir=corpus_dir, corpus=corpus)
        if case["case_id"] in seen_cases:
            raise LabelJoinError(f"keyed union has duplicate case_id: {case['case_id']}")
        seen_cases.add(case["case_id"])
        cases.append(case)
        packets.append(packet)
        used_artifacts.add(artifact_name)
        segment_verified_candidates += verified_count
    ordered_pairs = sorted(zip(cases, packets, strict=True), key=lambda pair: str(pair[0]["case_id"]))
    cases = [case for case, _packet in ordered_pairs]
    packets = [packet for _case, packet in ordered_pairs]
    selection_mode = (keyed_document.get("keying") or {}).get("mode")
    source_artifacts = [
        {
            "artifact_sha256": sha256_file(corpus_dir / artifact_name),
            "fixture_set_sha256": _fixture_source(
                str(next(case for case in cases if case["case_id"].startswith(artifact_name + "#"))["fixture_id"]),
                corpus_dir=corpus_dir,
                artifact_name=artifact_name,
                corpus=corpus,
                selection_mode=selection_mode if isinstance(selection_mode, str) else None,
            )["sha256"],
        }
        for artifact_name in sorted(used_artifacts)
    ]
    scaffold = {
        "schema_version": "qg-layer-b-labels.v2",
        "dataset_id": "qg-layer-b-phase0-scaffold",
        "source_artifacts": source_artifacts,
        "qualification_eligible": False,
        "qualification_blockers": ["Scaffold only: all annotation and adjudication fields remain null."],
        "cases": cases,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "labels-scaffold.v2.json", scaffold)
    packets_dir = output_dir / "packets"
    per_shard = (len(packets) + shard_count - 1) // shard_count
    written = 0
    for shard in range(shard_count):
        start = shard * per_shard
        packet_rows = packets[start : start + per_shard]
        if not packet_rows:
            continue
        shard_path = packets_dir / f"shard-{shard:02d}.jsonl"
        _write_shard(shard_path, packet_rows, shard, resume=resume)
        written += 1
        if crash_after_shards is not None and written >= crash_after_shards:
            raise RuntimeError("simulated crash after atomic shard write")
    report = {
        "keyed_rows": len(keyed_rows),
        "cases": len(cases),
        "shards": sum(1 for shard in range(shard_count) if packets[shard * per_shard : (shard + 1) * per_shard]),
        "candidates": sum(len(group) for case in cases for group in case["candidates_by_event_output_id"].values()),
        "segment_verified_candidates": segment_verified_candidates,
        "judgment_fields_prefilled": 0,
        "join_report": dict((keyed_document.get("keying") or {}).get("join_report") or {}),
    }
    return scaffold, report


def write_scaffold(
    keyed_path: Path,
    shadow_path: Path,
    *,
    corpus_dir: Path,
    output_dir: Path,
    shard_count: int = 4,
    resume: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build scaffold outputs and atomically write the input-pinned manifest."""
    keyed_document = read_json(keyed_path)
    shadow_document = read_json(shadow_path)
    scaffold, report = build_scaffold(
        keyed_document,
        shadow_document,
        corpus_dir=corpus_dir,
        output_dir=output_dir,
        shard_count=shard_count,
        resume=resume,
    )
    used_artifacts = sorted({str(case["case_id"]).split("#fact_checks[", maxsplit=1)[0] for case in scaffold["cases"]})
    corpus = load_corpus(corpus_dir)
    selection_mode = (keyed_document.get("keying") or {}).get("mode")
    fixture_sets: dict[str, dict[str, str]] = {}
    for fixture_id in sorted({str(case["fixture_id"]) for case in scaffold["cases"]}):
        artifact_names = sorted(
            {
                str(case["case_id"]).split("#fact_checks[", maxsplit=1)[0]
                for case in scaffold["cases"]
                if case["fixture_id"] == fixture_id
            }
        )
        if not artifact_names:
            raise LabelJoinError(f"scaffold has no source artifact for fixture {fixture_id!r}")
        fixture_sets[fixture_id] = _fixture_source(
            fixture_id,
            corpus_dir=corpus_dir,
            artifact_name=artifact_names[0],
            corpus=corpus,
            selection_mode=selection_mode if isinstance(selection_mode, str) else None,
        )
    manifest = {
        "manifest_version": "qg-layer-b-scaffold-manifest.v2",
        "inputs": {
            "keyed_union": {"path": str(keyed_path), "sha256": sha256_file(keyed_path)},
            "phase1_shadow": {"path": str(shadow_path), "sha256": sha256_file(shadow_path)},
            "corpus_artifacts": {
                artifact_name: sha256_file(corpus_dir / artifact_name) for artifact_name in used_artifacts
            },
            "fixture_sets": fixture_sets,
        },
        "join_report": report["join_report"],
        "counts": {key: value for key, value in report.items() if key != "join_report"},
        "scaffold_sha256": sha256_file(output_dir / "labels-scaffold.v2.json"),
    }
    atomic_write_json(output_dir / "scaffold-manifest.json", manifest)
    return scaffold, manifest


def _require_hash(value: Any, field: str) -> None:
    if not isinstance(value, str) or SHA_RE.fullmatch(value) is None:
        raise LabelJoinError(f"{field} must be a lowercase SHA-256")


def validate_annotator_record(record: Mapping[str, Any], event_outputs: Mapping[str, str]) -> None:
    """Validate one completed working case before two-way sidecar merge.

    The working format deliberately omits ``annotators`` and ``adjudication``;
    those are added only by the merged sidecar.  This validator checks the
    schema-shaped required fields and deterministic source-byte invariants.
    """
    missing = [field for field in WORKING_CASE_REQUIRED if field not in record]
    forbidden = [field for field in ("annotators", "adjudication") if field in record]
    if missing or forbidden:
        raise LabelJoinError(
            "invalid working record shape: "
            + ("missing=" + ", ".join(missing) if missing else "")
            + (" forbidden=" + ", ".join(forbidden) if forbidden else "")
        )
    if (
        not isinstance(record.get("case_id"), str)
        or not record["case_id"]
        or not isinstance(record.get("fixture_id"), str)
        or not record["fixture_id"]
        or not isinstance(record.get("fact_check_id"), str)
        or not record["fact_check_id"]
        or not isinstance(record.get("fact_check_index"), int)
        or record["fact_check_index"] < 0
        or not isinstance(record.get("claim"), str)
        or not record["claim"]
        or not isinstance(record.get("evidence_excerpt"), str)
        or not record["evidence_excerpt"]
    ):
        raise LabelJoinError("working record has an invalid case identity")
    if not isinstance(record.get("claim_is_true"), bool):
        raise LabelJoinError("claim_is_true must be a completed boolean in an annotator record")
    enum_checks = {
        "expected_reviewer_verdict": REVIEWER_VERDICTS,
        "expected_layer_a_decision": LAYER_A_DECISIONS,
        "expected_layer_a_reason": LAYER_A_REASONS,
        "expected_aggregate_relation": AGGREGATE_RELATIONS,
        "expected_fact_check_decision": FACT_CHECK_DECISIONS,
        "failure_class": FAILURE_CLASSES,
        "corpus_verification_status": CORPUS_STATUSES,
    }
    for field, allowed in enum_checks.items():
        if record.get(field) not in allowed:
            raise LabelJoinError(f"{field} must be a completed registered enum")
    if not isinstance(record.get("anchor_scan_complete"), bool) or not isinstance(
        record.get("candidate_set_complete"), bool
    ):
        raise LabelJoinError("scan and candidate-set completeness must be booleans")
    if not isinstance(record.get("context_sufficient"), bool):
        raise LabelJoinError("context_sufficient must be a completed boolean")
    _require_hash(record.get("artifact_sha256"), "artifact_sha256")
    candidates_by_output = record.get("candidates_by_event_output_id")
    if not isinstance(candidates_by_output, Mapping):
        raise LabelJoinError("candidates_by_event_output_id must be an object")
    if record.get("expected_layer_a_decision") == "ANCHOR" and (
        record.get("candidate_set_complete") is not True or not candidates_by_output
    ):
        raise LabelJoinError("ANCHOR working records require a complete non-empty candidate set")
    for event_output_id, candidates in candidates_by_output.items():
        _require_hash(event_output_id, "event_output_id")
        raw_output = event_outputs.get(str(event_output_id))
        if raw_output is None:
            raise LabelJoinError(f"missing raw output for event_output_id={event_output_id}")
        normalized_output = anchor_primitives.normalize_for_match(raw_output)
        if not isinstance(candidates, list) or not candidates:
            raise LabelJoinError(f"event output {event_output_id} needs a non-empty candidate list")
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                raise LabelJoinError(f"event output {event_output_id} has a non-object candidate")
            missing_candidate = [field for field in WORKING_CANDIDATE_REQUIRED if field not in candidate]
            if missing_candidate:
                raise LabelJoinError("candidate missing=" + ", ".join(missing_candidate))
            for field in SHA_FIELDS:
                _require_hash(candidate.get(field), field)
            if sha256_text(raw_output) != candidate["raw_output_sha256"]:
                raise LabelJoinError(f"raw output hash mismatch for {event_output_id}")
            if sha256_text(normalized_output) != candidate["normalized_output_sha256"]:
                raise LabelJoinError(f"normalized output hash mismatch for {event_output_id}")
            if candidate.get("expected_source_relation") not in SOURCE_RELATIONS:
                raise LabelJoinError("candidate expected_source_relation must be a completed registered enum")
            previous_normalized_end = 0
            previous_raw_end = 0
            segments = candidate["ordered_segment_spans"]
            if not isinstance(segments, list) or not segments:
                raise LabelJoinError("candidate ordered_segment_spans must be a non-empty list")
            for expected_index, segment in enumerate(segments):
                if not isinstance(segment, Mapping) or segment.get("segment_index") != expected_index:
                    raise LabelJoinError("segment indices must be consecutive and ordered")
                try:
                    normalized_start = int(segment["output_normalized_start"])
                    normalized_end = int(segment["output_normalized_end"])
                    raw_start = int(segment["output_raw_start"])
                    raw_end = int(segment["output_raw_end"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise LabelJoinError("segment offsets must be integer values") from exc
                if not (
                    0 <= normalized_start < normalized_end <= len(normalized_output)
                    and 0 <= raw_start < raw_end <= len(raw_output)
                    and previous_normalized_end <= normalized_start
                    and previous_raw_end <= raw_start
                ):
                    raise LabelJoinError("segment spans are out of bounds or overlap")
                normalized_segment = normalized_output[normalized_start:normalized_end]
                raw_segment = raw_output[raw_start:raw_end]
                if anchor_primitives.normalize_for_match(raw_segment) != normalized_segment:
                    raise LabelJoinError("normalized-to-raw segment mapping does not round trip")
                _require_hash(segment.get("normalized_segment_sha256"), "normalized_segment_sha256")
                _require_hash(segment.get("raw_segment_sha256"), "raw_segment_sha256")
                if (
                    sha256_text(normalized_segment) != segment["normalized_segment_sha256"]
                    or sha256_text(raw_segment) != segment["raw_segment_sha256"]
                ):
                    raise LabelJoinError("segment SHA-256 does not match captured output")
                previous_normalized_end = normalized_end
                previous_raw_end = raw_end
            support_spans = candidate["expected_support_spans"]
            if not isinstance(support_spans, list):
                raise LabelJoinError("expected_support_spans must be a list")
            for support in support_spans:
                if (
                    not isinstance(support, Mapping)
                    or not isinstance(support.get("start"), int)
                    or not isinstance(support.get("end"), int)
                ):
                    raise LabelJoinError("support spans must carry integer offsets")
                if not 0 <= support["start"] < support["end"] <= len(raw_output):
                    raise LabelJoinError("support span is out of bounds")
                if support.get("role") not in SUPPORT_ROLES:
                    raise LabelJoinError("support span role is not registered")
            relation = candidate["expected_source_relation"]
            roles = {str(support.get("role")) for support in support_spans if isinstance(support, Mapping)}
            if relation == "ENTAILS" and "SUPPORTS" not in roles:
                raise LabelJoinError("ENTAILS requires a SUPPORTS span")
            if relation == "CONTRADICTS" and "CONTRADICTS" not in roles:
                raise LabelJoinError("CONTRADICTS requires a CONTRADICTS span")
            if relation == "EXPLICITLY_UNCERTAIN" and "UNCERTAINTY" not in roles:
                raise LabelJoinError("EXPLICITLY_UNCERTAIN requires an UNCERTAINTY span")
            if relation == "MIXED" and not ({"SUPPORTS"} <= roles and ({"CONTRADICTS", "UNCERTAINTY"} & roles)):
                raise LabelJoinError("MIXED requires support and contradiction/uncertainty spans")
            if relation in {"NO_RELATION", "INSUFFICIENT_CONTEXT", "TOOL_ERROR"} and support_spans:
                raise LabelJoinError(f"{relation} requires no support spans")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keyed-union", type=Path, required=True)
    parser.add_argument("--shadow", type=Path, required=True)
    parser.add_argument("--corpus-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=4)
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    write_scaffold(
        args.keyed_union,
        args.shadow,
        corpus_dir=args.corpus_dir,
        output_dir=args.output_dir,
        shard_count=args.shards,
        resume=not args.no_resume,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
