#!/usr/bin/env python3
"""Collect hermetic, module-envelope emissions for Layer-B qualification.

The qualification scorer intentionally never invokes a judge.  This collector
is the only boundary that does: it recovers the captured full tool-output bytes
from the source artifacts identified by immutable labels, sends one
tool-disabled request for each artifact envelope, and records one scorer-ready
emission for every anchored fact check in that artifact.

The collected files are deliberately distinct from the scorer's output
directory.  ``layerb_qualify`` writes its own derived raw-call manifest while
scoring/attesting; pointing both tools at the same directory would overwrite
this collector's richer, transport-level manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "scripts"))

from scripts.audit import layerb_candidates, layerb_judge_bridge, layerb_qualify, layerb_shadow
from scripts.audit.layerb_keys import _build_event_index
from scripts.audit.layerb_label_common import atomic_write_json
from scripts.audit.llm_reviewer_dispatch import tool_events_from_dispatch_meta

EMISSIONS_VERSION = "qg-layer-b-qualification-emissions.v1"
CACHE_VERSION = "qg-layer-b-qualification-collector-cache.v3"
COLLECTOR_VERSION = "qg-layer-b-qualification-collector.v1"


class CollectionError(ValueError):
    """Input cannot be collected without weakening the qualification contract."""


class ProbeFailure(RuntimeError):
    """A probe response failed before the collector was allowed to run main rows."""


@dataclass(frozen=True, slots=True)
class PreparedCase:
    """One label row with full, hash-verified windows ready for a module request."""

    corpus: str
    case: Mapping[str, Any]
    windows: tuple[dict[str, Any], ...]

    @property
    def case_id(self) -> str:
        return str(self.case["case_id"])

    @property
    def artifact_sha256(self) -> str:
        return str(self.case["artifact_sha256"])


@dataclass(frozen=True, slots=True)
class ModuleEnvelope:
    """All judgeable fact checks from one immutable source artifact."""

    corpus: str
    artifact_sha256: str
    cases: tuple[PreparedCase, ...]
    attempt: int = 0


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value).encode("utf-8"))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CollectionError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise CollectionError(f"JSON object required at {path}")
    return value


def _cases(document: Mapping[str, Any], label: str) -> list[Mapping[str, Any]]:
    rows = document.get("cases")
    if not isinstance(rows, list):
        raise CollectionError(f"{label} labels require a cases list")
    malformed = [index for index, row in enumerate(rows) if not isinstance(row, Mapping)]
    if malformed:
        raise CollectionError(f"{label} labels contain non-object cases at indexes {malformed}")
    return [row for row in rows if isinstance(row, Mapping)]


def _candidate_rows(case: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    grouped = case.get("candidates_by_event_output_id")
    if not isinstance(grouped, Mapping):
        return []
    candidates: list[tuple[str, Mapping[str, Any]]] = []
    for event_output_id in sorted(grouped, key=str):
        values = grouped[event_output_id]
        if not isinstance(values, list):
            raise CollectionError(f"{case.get('case_id')}: candidate group {event_output_id!r} is not a list")
        for candidate in values:
            if not isinstance(candidate, Mapping):
                raise CollectionError(f"{case.get('case_id')}: candidate is not an object")
            candidates.append((str(event_output_id), candidate))
    return candidates


def _required_str(value: Mapping[str, Any], field: str, context: str) -> str:
    result = value.get(field)
    if not isinstance(result, str) or not result:
        raise CollectionError(f"{context}: {field} must be a non-empty string")
    return result


def _required_bool(value: Mapping[str, Any], field: str, context: str) -> bool:
    result = value.get(field)
    if not isinstance(result, bool):
        raise CollectionError(f"{context}: {field} must be boolean")
    return result


def _label_candidate_runtime(candidate: Mapping[str, Any], event_output_id: str) -> layerb_candidates.AnchorCandidate:
    """Materialize only the production candidate object needed by ``_judge_window``.

    Qualification labels preserve every source-derived candidate field except
    runtime-only schema/event fields.  Reconstructing this dataclass lets the
    production window builder verify event-output and segment hashes instead of
    trusting a reimplemented copy of its logic.
    """

    context = f"candidate {candidate.get('candidate_id', '<unknown>')}"
    segments_value = candidate.get("ordered_segment_spans")
    if not isinstance(segments_value, list):
        raise CollectionError(f"{context}: ordered_segment_spans must be a list")
    segments: list[layerb_candidates.AnchorSegment] = []
    for index, value in enumerate(segments_value):
        if not isinstance(value, Mapping):
            raise CollectionError(f"{context}: segment {index} is not an object")
        required_ints = (
            "segment_index",
            "excerpt_normalized_start",
            "excerpt_normalized_end",
            "output_normalized_start",
            "output_normalized_end",
            "output_raw_start",
            "output_raw_end",
        )
        if any(not isinstance(value.get(field), int) or isinstance(value.get(field), bool) for field in required_ints):
            raise CollectionError(f"{context}: segment {index} has non-integer offsets")
        segments.append(
            layerb_candidates.AnchorSegment(
                segment_index=int(value["segment_index"]),
                excerpt_normalized_start=int(value["excerpt_normalized_start"]),
                excerpt_normalized_end=int(value["excerpt_normalized_end"]),
                output_normalized_start=int(value["output_normalized_start"]),
                output_normalized_end=int(value["output_normalized_end"]),
                output_raw_start=int(value["output_raw_start"]),
                output_raw_end=int(value["output_raw_end"]),
                normalized_segment_sha256=_required_str(value, "normalized_segment_sha256", context),
                raw_segment_sha256=_required_str(value, "raw_segment_sha256", context),
            )
        )
    tool_identity = candidate.get("tool_identity")
    query_identity = candidate.get("query_identity")
    if not isinstance(tool_identity, Mapping) or not isinstance(query_identity, Mapping):
        raise CollectionError(f"{context}: tool_identity and query_identity must be objects")
    similarity = candidate.get("similarity")
    source_index = candidate.get("source_index")
    if not isinstance(similarity, (int, float)) or isinstance(similarity, bool):
        raise CollectionError(f"{context}: similarity must be numeric")
    if not isinstance(source_index, int) or isinstance(source_index, bool):
        raise CollectionError(f"{context}: source_index must be an integer")
    return layerb_candidates.AnchorCandidate(
        schema_version=layerb_candidates.CANDIDATE_SCHEMA_VERSION,
        candidate_id=_required_str(candidate, "candidate_id", context),
        event_output_id=event_output_id,
        canonical_source_id=_required_str(candidate, "canonical_source_id", context),
        source_index=source_index,
        tool_identity={str(key): str(value) for key, value in tool_identity.items()},
        query_identity={str(key): str(value) for key, value in query_identity.items()},
        raw_output_sha256=_required_str(candidate, "raw_output_sha256", context),
        normalized_output_sha256=_required_str(candidate, "normalized_output_sha256", context),
        output_capture_complete=_required_bool(candidate, "output_capture_complete", context),
        anchor_scan_complete=_required_bool(candidate, "anchor_scan_complete", context),
        match_type=_required_str(candidate, "match_type", context),
        similarity=float(similarity),
        tool_query_matched=True,
        eligibility=_required_str(candidate, "eligibility", context),
        error_status=_required_str(candidate, "error_status", context),
        ordered_segment_spans=tuple(segments),
    )


def _embedded_raw_windows(case: Mapping[str, Any]) -> dict[str, str]:
    """Read optional embedded raw windows without requiring a non-schema field.

    Current v2 labels deliberately contain no raw evidence.  Supporting either
    candidate-level ``raw_window`` or a case-level ``windows`` list makes this
    collector safe for future label formats while retaining the same hash and
    serializer checks.
    """

    windows: dict[str, str] = {}
    supplied = case.get("windows")
    if isinstance(supplied, list):
        for window in supplied:
            if (
                isinstance(window, Mapping)
                and isinstance(window.get("candidate_id"), str)
                and isinstance(window.get("raw_window"), str)
            ):
                windows[str(window["candidate_id"])] = str(window["raw_window"])
    for _event_output_id, candidate in _candidate_rows(case):
        candidate_id = candidate.get("candidate_id")
        raw_window = candidate.get("raw_window")
        if isinstance(candidate_id, str) and isinstance(raw_window, str):
            windows[candidate_id] = raw_window
    return windows


def _embedded_window(candidate: Mapping[str, Any], raw: str) -> dict[str, Any]:
    candidate_id = _required_str(candidate, "candidate_id", "embedded window")
    raw_hash = _sha256_bytes(raw.encode("utf-8"))
    if raw_hash != _required_str(candidate, "raw_output_sha256", f"candidate {candidate_id}"):
        raise CollectionError(f"candidate {candidate_id}: embedded raw window hash differs from label")
    return {
        "candidate_id": candidate_id,
        "canonical_source_id": _required_str(candidate, "canonical_source_id", f"candidate {candidate_id}"),
        "raw_output_sha256": raw_hash,
        "raw_window_start": 0,
        "raw_window_end": len(raw),
        "raw_window_sha256": raw_hash,
        "logical_unit_kind": "FULL_OUTPUT",
        "logical_unit_complete": True,
        "contains_all_anchor_segments": True,
        "raw_window": raw,
    }


def _source_roots(label_paths: Iterable[Path]) -> list[Path]:
    """Find only deterministic local roots that can contain labelled artifacts."""

    roots = {Path(__file__).resolve().parents[2] / "tests" / "fixtures"}
    for label_path in label_paths:
        resolved = label_path.resolve()
        roots.add(resolved.parent)
        for ancestor in resolved.parents:
            if ancestor.name == "audit":
                roots.add(ancestor)
            audit_child = ancestor / "audit"
            if audit_child.is_dir():
                roots.add(audit_child)
    return sorted((root for root in roots if root.is_dir()), key=lambda root: str(root))


def _artifact_sources(
    required_hashes: set[str], label_paths: Iterable[Path]
) -> dict[str, tuple[Path, Mapping[str, Any]]]:
    """Resolve exact source-artifact bytes by the immutable hashes in labels."""

    located: dict[str, tuple[Path, Mapping[str, Any]]] = {}
    for root in _source_roots(label_paths):
        for path in sorted(root.rglob("*.json")):
            try:
                digest = _sha256_bytes(path.read_bytes())
            except OSError as exc:
                raise CollectionError(f"cannot hash candidate source artifact {path}: {exc}") from exc
            if digest not in required_hashes or digest in located:
                continue
            document = _read_json(path)
            located[digest] = (path, document)
            if len(located) == len(required_hashes):
                return located
    missing = sorted(required_hashes - set(located))
    raise CollectionError(
        "source artifact bytes are unavailable for label hashes: "
        + ", ".join(missing[:8])
        + (" ..." if len(missing) > 8 else "")
    )


def _prepared_case(
    corpus: str,
    case: Mapping[str, Any],
    artifact_sources: Mapping[str, tuple[Path, Mapping[str, Any]]],
) -> PreparedCase:
    case_id = _required_str(case, "case_id", f"{corpus} case")
    candidate_rows = _candidate_rows(case)
    if not candidate_rows:
        return PreparedCase(corpus=corpus, case=case, windows=())
    embedded = _embedded_raw_windows(case)
    candidate_ids = {_required_str(candidate, "candidate_id", case_id) for _event_id, candidate in candidate_rows}
    if candidate_ids <= set(embedded):
        windows = tuple(
            _embedded_window(candidate, embedded[str(candidate["candidate_id"])])
            for _event_id, candidate in candidate_rows
        )
    else:
        artifact_sha = _required_str(case, "artifact_sha256", case_id)
        source = artifact_sources.get(artifact_sha)
        if source is None:
            raise CollectionError(f"{case_id}: source artifact {artifact_sha} was not resolved")
        _path, artifact = source
        dispatch = artifact.get("dispatch")
        if not isinstance(dispatch, Mapping):
            raise CollectionError(f"{case_id}: source artifact has no dispatch metadata")
        event_index = _build_event_index(tool_events_from_dispatch_meta(dispatch))
        max_reconstructed_chars = max((len(raw) for raw in event_index.values()), default=0)
        prepared_windows: list[dict[str, Any]] = []
        for event_output_id, candidate in candidate_rows:
            runtime_candidate = _label_candidate_runtime(candidate, event_output_id)
            try:
                # Labels bind the complete captured output hash, and the scorer
                # requires those exact bytes.  The shadow runner's 10k-char
                # replay guard cannot be used here because it would make
                # otherwise valid labels unreplayable; spend reservations below
                # use a conservative request-byte token bound instead.
                window = layerb_shadow._judge_window(runtime_candidate, event_index, max_reconstructed_chars)
            except layerb_shadow.JudgeValidationError as exc:
                raise CollectionError(
                    f"{case_id}: cannot reconstruct candidate {runtime_candidate.candidate_id}: {exc}"
                ) from exc
            prepared_windows.append(window)
        windows = tuple(prepared_windows)
    for window in windows:
        try:
            layerb_shadow._serialize_untrusted_window(window, prompt_version=layerb_shadow.PROMPT_VERSION)
        except layerb_shadow.JudgeValidationError as exc:
            raise CollectionError(f"{case_id}: production serializer rejected a reconstructed window: {exc}") from exc
    return PreparedCase(corpus=corpus, case=case, windows=windows)


def _planned_modules(
    prepared_cases: Iterable[PreparedCase],
    *,
    eligibility: str,
    effective_route: layerb_qualify.EffectiveRoute,
    attempt: int = 0,
) -> list[ModuleEnvelope]:
    grouped: dict[tuple[str, str], list[PreparedCase]] = defaultdict(list)
    skipped: Counter[str] = Counter()
    for prepared in prepared_cases:
        if prepared.case.get("expected_layer_a_decision") != "ANCHOR":
            continue
        if not prepared.windows:
            raise CollectionError(f"{prepared.case_id}: an ANCHOR row has no candidate windows")
        if prepared.corpus == "main":
            # Route eligibility binds in EVERY mode: filtering only under
            # --eligibility deepseek-only let the default 'all' mode schedule
            # rows the route may never judge (e.g. a grok-lineage-authored row
            # on the grok route) — the exclusion existed but nothing enforced
            # it at planning time (PR #5203 review finding). UNKNOWN_LINEAGE
            # is likewise fail-closed here: an unresolvable lineage can hide a
            # self-family author, and the frozen r2 labels resolve lineage for
            # all 535 rows, so this costs nothing operationally.
            matrix = layerb_qualify.route_eligibility(prepared.case, effective_route)
            if matrix.get("eligible") is not True:
                skipped[str(matrix.get("reason") or "INELIGIBLE")] += 1
                continue
        grouped[(prepared.corpus, prepared.artifact_sha256)].append(prepared)
    if skipped:
        # No silent caps: an operator must see exactly what the route was
        # not allowed to judge.
        print(
            "route-eligibility skips: " + ", ".join(f"{reason}={count}" for reason, count in sorted(skipped.items())),
            file=sys.stderr,
        )
    return [
        ModuleEnvelope(
            corpus=corpus,
            artifact_sha256=artifact_sha,
            cases=tuple(sorted(cases, key=lambda item: item.case_id)),
            attempt=attempt,
        )
        for (corpus, artifact_sha), cases in sorted(
            grouped.items(), key=lambda item: (0 if item[0][0] == "probe" else 1, item[0][1])
        )
    ]


def _stability_modules(
    prepared_cases: Sequence[PreparedCase],
    *,
    main_cases: Sequence[Mapping[str, Any]],
    probe_cases: Sequence[Mapping[str, Any]],
    eligibility: str,
    effective_route: layerb_qualify.EffectiveRoute,
) -> tuple[list[str], list[ModuleEnvelope]]:
    """Plan exactly the fixed scorer-selected replay subset as attempt one."""

    selected = layerb_qualify.stability_case_ids(main_cases, probe_cases)
    selected_ids = set(selected)
    prepared_by_id = {prepared.case_id: prepared for prepared in prepared_cases}
    if len(prepared_by_id) != len(prepared_cases):
        raise CollectionError("qualification labels contain duplicate case_id values")
    missing = sorted(selected_ids - set(prepared_by_id))
    if missing:
        raise CollectionError(f"stability selection is absent from prepared labels: {', '.join(missing[:8])}")
    return selected, _planned_modules(
        [prepared_by_id[case_id] for case_id in selected],
        eligibility=eligibility,
        effective_route=effective_route,
        attempt=1,
    )


def _module_request(module: ModuleEnvelope) -> tuple[dict[str, Any], dict[str, str]]:
    """Build one no-tools request, deduplicating repeated full source outputs."""

    seen_windows: dict[str, dict[str, Any]] = {}
    serialized_hashes: dict[str, str] = {}
    fact_checks: list[dict[str, Any]] = []
    for prepared in module.cases:
        sources: list[dict[str, Any]] = []
        for window in prepared.windows:
            candidate_id = str(window["candidate_id"])
            nonce, block = layerb_shadow._serialize_untrusted_window(
                window, prompt_version=layerb_shadow.PROMPT_VERSION
            )
            raw_hash = str(window["raw_window_sha256"])
            prior = seen_windows.get(raw_hash)
            if prior is not None and prior["raw_window"] != window["raw_window"]:
                raise CollectionError(f"{prepared.case_id}: raw output hash {raw_hash} has conflicting window bytes")
            if prior is None:
                seen_windows[raw_hash] = {
                    "block": block,
                    "nonce": nonce,
                    "raw_window": window["raw_window"],
                    "candidate_ids": [candidate_id],
                }
                serialized_hashes[candidate_id] = _sha256_bytes(block.encode("utf-8"))
            else:
                prior["candidate_ids"].append(candidate_id)
                serialized_hashes[candidate_id] = _sha256_bytes(str(prior["block"]).encode("utf-8"))
            source = {key: value for key, value in window.items() if key != "raw_window"}
            source["untrusted_window_sha256"] = raw_hash
            sources.append(source)
        fact_checks.append(
            {
                "fact_check_id": _required_str(prepared.case, "fact_check_id", prepared.case_id),
                "claim": _required_str(prepared.case, "claim", prepared.case_id),
                "candidate_sources": sources,
            }
        )
    untrusted_data = [
        {
            "window_sha256": raw_hash,
            "candidate_ids": sorted(window["candidate_ids"]),
            "nonce": window["nonce"],
            "block": window["block"],
        }
        for raw_hash, window in sorted(seen_windows.items())
    ]
    request = {
        "schema_version": layerb_shadow.JUDGE_INPUT_VERSION,
        "prompt_version": layerb_shadow.PROMPT_VERSION,
        "system_instruction": layerb_shadow.SYSTEM_INSTRUCTION,
        "max_output_tokens": 800,
        "tool_access": {"enabled": False, "mcp": False},
        "tools": [],
        "fact_checks": fact_checks,
        "untrusted_data": untrusted_data,
    }
    return request, serialized_hashes


def _validation_substitutions_by_case(
    module: ModuleEnvelope,
    response: Mapping[str, Any],
    normalized_substitutions: Sequence[Mapping[str, str]],
) -> dict[str, list[dict[str, str]]]:
    """Extract bridge sidecars and locally generated substitutions by pair."""

    expected_cases = {
        (
            _required_str(prepared.case, "fact_check_id", prepared.case_id),
            str(window["candidate_id"]),
        ): prepared.case_id
        for prepared in module.cases
        for window in prepared.windows
    }
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_pairs: set[tuple[str, str]] = set()
    bridge_substitutions = response.get("_bridge_substituted")
    records: Iterable[Mapping[str, Any]] = (
        [record for record in bridge_substitutions if isinstance(record, Mapping)]
        if isinstance(bridge_substitutions, list)
        else []
    )
    for record in [*records, *normalized_substitutions]:
        fact_check_id = record.get("fact_check_id")
        candidate_id = record.get("candidate_id")
        reason = record.get("reason")
        if not all(isinstance(value, str) and value for value in (fact_check_id, candidate_id, reason)):
            continue
        pair = (fact_check_id, candidate_id)
        case_id = expected_cases.get(pair)
        if case_id is None or pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        by_case[case_id].append({"fact_check_id": fact_check_id, "candidate_id": candidate_id, "reason": reason})
    return dict(by_case)


def _validated_response_by_case(
    module: ModuleEnvelope, response: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, str]]]]:
    """Normalize a module and return schema-pure responses plus substitutions."""

    expected_by_fact = {
        _required_str(prepared.case, "fact_check_id", prepared.case_id): prepared for prepared in module.cases
    }
    normalized_response, substitutions = layerb_shadow.normalize_judge_module_response(
        response,
        expected_windows_by_fact={
            fact_check_id: prepared.windows for fact_check_id, prepared in expected_by_fact.items()
        },
    )
    normalized_by_fact = {str(fact["fact_check_id"]): fact for fact in normalized_response["fact_checks"]}
    normalized = {
        prepared.case_id: {
            "schema_version": layerb_shadow.JUDGE_OUTPUT_VERSION,
            "fact_checks": [dict(normalized_by_fact[fact_check_id])],
        }
        for fact_check_id, prepared in expected_by_fact.items()
    }
    return normalized, _validation_substitutions_by_case(module, response, substitutions)


def _evidence_pattern_hits_by_case(
    module: ModuleEnvelope, response: Mapping[str, Any]
) -> dict[str, list[dict[str, str]]]:
    """Extract valid, de-duplicated bridge detector hits into their owning case."""

    expected_cases = {
        (
            _required_str(prepared.case, "fact_check_id", prepared.case_id),
            str(window["candidate_id"]),
        ): prepared.case_id
        for prepared in module.cases
        for window in prepared.windows
    }
    raw_hits = response.get("_evidence_pattern_hits")
    records: Iterable[Mapping[str, Any]] = (
        [record for record in raw_hits if isinstance(record, Mapping)] if isinstance(raw_hits, list) else []
    )
    by_case: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        fact_check_id = record.get("fact_check_id")
        candidate_id = record.get("candidate_id")
        pattern = record.get("pattern")
        if not all(isinstance(value, str) and value for value in (fact_check_id, candidate_id, pattern)):
            continue
        pair = (fact_check_id, candidate_id)
        case_id = expected_cases.get(pair)
        key = (fact_check_id, candidate_id, pattern)
        if case_id is None or key in seen:
            continue
        seen.add(key)
        by_case[case_id].append({"fact_check_id": fact_check_id, "candidate_id": candidate_id, "pattern": pattern})
    return dict(by_case)


def _bridge_forensics_sidecar(response: Mapping[str, Any]) -> dict[str, str] | None:
    """Extract a bridge-owned forensic pointer without admitting it to scoring payloads."""

    sidecar = response.get("_bridge_forensics")
    if not isinstance(sidecar, Mapping):
        return None
    path = sidecar.get("path")
    content_sha256 = sidecar.get("sha256")
    if (
        not isinstance(path, str)
        or not path
        or not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(character not in "0123456789abcdef" for character in content_sha256)
    ):
        return None
    return {"path": path, "sha256": content_sha256}


def _failure_response(prepared: PreparedCase) -> dict[str, Any]:
    return {
        "schema_version": layerb_shadow.JUDGE_OUTPUT_VERSION,
        "fact_checks": [
            {
                "fact_check_id": _required_str(prepared.case, "fact_check_id", prepared.case_id),
                "source_relations": [
                    layerb_shadow.conservative_candidate_response(str(window["candidate_id"]))
                    for window in prepared.windows
                ],
            }
        ],
    }


def _observed(call: layerb_shadow.JudgeCall | None, route: layerb_shadow.JudgeRoute) -> dict[str, float]:
    prompt_tokens = call.prompt_tokens if call is not None and call.prompt_tokens is not None else 10_000
    completion_tokens = call.completion_tokens if call is not None and call.completion_tokens is not None else 800
    cost = call.cost_usd if call is not None and call.cost_usd is not None else route.worst_case_usd
    return {
        "prompt_tokens": float(prompt_tokens),
        "completion_tokens": float(completion_tokens),
        "cost_usd": float(cost),
    }


def _emission(
    prepared: PreparedCase,
    *,
    call_id: str,
    attempt: int = 0,
    observed: Mapping[str, float],
    response: Mapping[str, Any],
    status: str,
    validation_substituted: Sequence[Mapping[str, str]] = (),
    evidence_pattern_hits: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    windows = [
        {"candidate_id": str(window["candidate_id"]), "raw_window": str(window["raw_window"])}
        for window in prepared.windows
    ]
    result: dict[str, Any] = {
        "status": status,
        # The scorer currently binds module_id to fixture_id.  The shared
        # call_id remains the immutable artifact-envelope identity.
        "module_id": _required_str(prepared.case, "fixture_id", prepared.case_id),
        "call_id": call_id,
        "attempt": attempt,
        "observed": dict(observed),
        "windows": windows,
        "response": dict(response),
    }
    if validation_substituted:
        result["validation_substituted"] = [dict(record) for record in validation_substituted]
    if evidence_pattern_hits:
        result["evidence_pattern_hits"] = [dict(record) for record in evidence_pattern_hits]
    if windows:
        result["serializer_window"] = dict(windows[0])
    return result


def _cache_path(cache_dir: Path, request: Mapping[str, Any], route: Mapping[str, Any], *, attempt: int) -> Path:
    key = _sha256_json(
        {
            "version": CACHE_VERSION,
            "request": request,
            "route": route,
            "attempt": attempt,
            "prompt_version": layerb_shadow.PROMPT_VERSION,
            "output_version": layerb_shadow.JUDGE_OUTPUT_VERSION,
        }
    )
    return cache_dir / f"{key}.json"


def _module_id(module: ModuleEnvelope) -> str:
    module_ids = {_required_str(prepared.case, "fixture_id", prepared.case_id) for prepared in module.cases}
    if len(module_ids) != 1:
        raise CollectionError(
            f"artifact {module.artifact_sha256} spans multiple fixture_id values: {', '.join(sorted(module_ids))}"
        )
    return next(iter(module_ids))


def _call_id(module: ModuleEnvelope) -> str:
    base = f"artifact-{module.artifact_sha256}"
    return base if module.attempt == 0 else f"{base}-attempt-{module.attempt}"


def _module_call_plan(
    modules: Sequence[ModuleEnvelope],
    module_requests: Sequence[tuple[Mapping[str, Any], Mapping[str, str]]],
    request_routes: Sequence[layerb_shadow.JudgeRoute],
) -> dict[str, dict[str, Any]]:
    """Derive every per-fixture envelope from the collector's concrete batch plan."""

    plans: dict[str, dict[str, Any]] = {}
    for module, (request, _serialized_hashes), route in zip(modules, module_requests, request_routes, strict=True):
        module_id = _module_id(module)
        max_output_tokens = request.get("max_output_tokens")
        if not isinstance(max_output_tokens, int) or isinstance(max_output_tokens, bool) or max_output_tokens < 1:
            raise CollectionError(f"{module_id}: request has no positive max_output_tokens")
        plan = plans.setdefault(
            module_id,
            {
                "expected_call_ids": [],
                "expected_call_count": 0,
                "expected_prompt_tokens": 0,
                "expected_completion_tokens": 0,
                "expected_cost_usd": 0.0,
            },
        )
        call_id = _call_id(module)
        if call_id in plan["expected_call_ids"]:
            raise CollectionError(f"{module_id}: duplicate planned call identity {call_id}")
        plan["expected_call_ids"].append(call_id)
        plan["expected_call_count"] += 1
        plan["expected_prompt_tokens"] += route.max_input_tokens
        plan["expected_completion_tokens"] += max_output_tokens
        plan["expected_cost_usd"] += route.worst_case_usd
    return {
        module_id: {**plan, "expected_call_ids": sorted(plan["expected_call_ids"])}
        for module_id, plan in sorted(plans.items())
    }


def _route_metadata(
    args: argparse.Namespace,
) -> tuple[layerb_qualify.EffectiveRoute, layerb_shadow.JudgeRoute, str, dict[str, Any]]:
    if not all(
        (args.judge_command, args.judge_family, args.judge_model, args.judge_model_version, args.provider_account_lane)
    ):
        raise CollectionError(
            "--judge-command, --judge-family, --judge-model, --judge-model-version, and --provider-account-lane are required"
        )
    command = shlex.split(args.judge_command)
    if not command:
        raise CollectionError("--judge-command must not be empty")
    bridge_config = {
        "argv": command,
        "bridge_version": layerb_judge_bridge.BRIDGE_VERSION,
        "judge_input_version": layerb_shadow.JUDGE_INPUT_VERSION,
        "prompt_version": layerb_shadow.PROMPT_VERSION,
        "tools": [],
        "tool_access": {"enabled": False, "mcp": False},
    }
    # Fresh output directories and no --resume remain a defence-in-depth
    # operational rule for Grok qualification. This identity fold independently
    # prevents a response cache from crossing a flat-contract revision.
    if str(args.judge_family).casefold() == "grok":
        bridge_config["family_internal_sha"] = layerb_judge_bridge.grok_flat_contract_fingerprint()
    route_data = {
        "family": args.judge_family,
        "resolved_model": args.judge_model,
        "resolved_model_version": args.judge_model_version,
        "bridge_executable": command[0],
        "bridge_config_sha256": _sha256_json(bridge_config),
        "provider_account_lane": args.provider_account_lane,
        "tools_disabled": True,
        "tools_disabled_evidence": (
            "collector request declares tool_access.enabled=false, tool_access.mcp=false, and tools=[]; "
            "layerb_shadow.SubprocessJudge exposes no in-process tool client"
        ),
    }
    effective = layerb_qualify.EffectiveRoute.from_mapping(route_data)
    route = layerb_shadow.JudgeRoute(
        family=effective.family,
        model=effective.resolved_model,
        input_usd_per_mtok=args.judge_input_usd_per_mtok,
        output_usd_per_mtok=args.judge_output_usd_per_mtok,
    )
    seat_key, seat_metadata = layerb_shadow.normalize_seat_key(
        {
            "family": effective.family,
            "resolved_model": effective.resolved_model,
            "resolved_model_version": effective.resolved_model_version,
            "provider_account_lane": effective.provider_account_lane,
        }
    )
    return effective, route, seat_key, seat_metadata


def _parse_seat_caps(values: Sequence[str]) -> dict[str, float]:
    try:
        return layerb_shadow._parse_seat_caps(values)
    except (argparse.ArgumentTypeError, ValueError) as exc:
        raise CollectionError(str(exc)) from exc


def _request_route(route: layerb_shadow.JudgeRoute, request: Mapping[str, Any]) -> layerb_shadow.JudgeRoute:
    """Reserve against a conservative UTF-8-byte upper bound on prompt tokens."""

    input_token_upper_bound = len(_canonical_json(request).encode("utf-8"))
    return replace(route, max_input_tokens=max(1, input_token_upper_bound))


def _preflight_caps(
    *,
    args: argparse.Namespace,
    request_routes: Sequence[layerb_shadow.JudgeRoute],
    seat_key: str,
    seat_caps: Mapping[str, float],
) -> None:
    required_calls = len(request_routes)
    unexpected_seat_caps = sorted(set(seat_caps) - {seat_key})
    if unexpected_seat_caps:
        raise CollectionError(f"--seat-cap names no collected route seat: {', '.join(unexpected_seat_caps)}")
    if args.max_judge_calls is not None and args.max_judge_calls != required_calls:
        raise CollectionError(f"--max-judge-calls must equal {required_calls}, got {args.max_judge_calls}")
    if not args.dry_run and args.max_judge_calls is None:
        raise CollectionError(
            f"--max-judge-calls must equal {required_calls}; collection refuses an unbounded live run"
        )
    total_worst_case = sum(route.worst_case_usd for route in request_routes)
    if args.max_usd is not None and total_worst_case > args.max_usd + 1e-12:
        raise CollectionError(
            f"--max-usd {args.max_usd} cannot cover all {required_calls} module calls at worst-case {total_worst_case}"
        )
    seat_cap = seat_caps.get(seat_key)
    if seat_cap is not None and total_worst_case > seat_cap + 1e-12:
        raise CollectionError(
            f"--seat-cap {seat_key}={seat_cap} cannot cover all {required_calls} module calls at worst-case {total_worst_case}"
        )


def _probe_error(
    prepared: PreparedCase, emission: Mapping[str, Any], route: layerb_qualify.EffectiveRoute
) -> str | None:
    """Use the scorer's own per-case validation before authorizing main calls."""

    runner = layerb_qualify.QualificationRunner(route=route, layer_a_probe_results=())
    record = runner._score_case(prepared.case, 0, emission)
    if record["hard_failure"]:
        return ",".join(str(value) for value in record["integrity_failures"])
    injection_probe = (
        prepared.case.get("failure_class") == "PROMPT_INJECTION"
        or prepared.case.get("probe_class") == "prompt-injection"
    )
    if injection_probe:
        if record["actual_final_decision"] != "AUDIT":
            return "PROBE_TERMINAL_DECISION_MISMATCH"
        if not any(score.get("injection_flagged") is True for score in record["candidate_scores"]):
            return "PROMPT_INJECTION_FLAG_MISSING"
        return None
    if record["actual_final_decision"] != record["expected_fact_check_decision"]:
        return "PROBE_TERMINAL_DECISION_MISMATCH"
    if record["agreement_successes"] != record["agreement_weight"]:
        return "PROBE_RELATION_OR_SPAN_MISMATCH"
    return None


def _write_collector_outputs(
    output_dir: Path,
    emissions: Mapping[str, Any],
    route: Mapping[str, Any],
    manifest: Sequence[Mapping[str, Any]],
    module_call_plan: Mapping[str, Mapping[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "emissions.json", {"version": EMISSIONS_VERSION, "emissions": dict(emissions)})
    atomic_write_json(output_dir / "route.json", dict(route))
    atomic_write_json(
        output_dir / "raw-call-manifest.json",
        {
            "version": "qg-layer-b-qualification-collector-manifest.v2",
            "calls": list(manifest),
            "module_call_plan": dict(module_call_plan),
        },
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect tool-disabled Layer-B qualification emissions.")
    parser.add_argument("--main-labels", type=Path, required=True)
    parser.add_argument("--probe-labels", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--judge-command")
    parser.add_argument("--judge-family")
    parser.add_argument("--judge-model")
    parser.add_argument(
        "--judge-model-version", help="Immutable resolved model/version recorded in the attested route."
    )
    parser.add_argument("--provider-account-lane", help="Exact provider/account lane recorded in the attested route.")
    parser.add_argument("--judge-input-usd-per-mtok", type=float, default=0.0)
    parser.add_argument("--judge-output-usd-per-mtok", type=float, default=0.0)
    parser.add_argument("--judge-timeout-seconds", type=float, default=90.0)
    parser.add_argument("--eligibility", choices=("all", "deepseek-only"), default="all")
    parser.add_argument("--probes-first", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-judge-calls", type=int)
    parser.add_argument("--max-usd", type=float)
    parser.add_argument("--seat-cap", action="append", default=[], metavar="SEAT=USD")
    parser.add_argument(
        "--dry-run", action="store_true", help="Reconstruct and serialize windows without calling the judge."
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Reuse validated per-module response cache entries. Grok qualification must use a fresh output directory "
            "without --resume; the flat-contract identity fold is defence in depth."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if not args.probes_first:
            raise CollectionError("qualification collection requires --probes-first")
        if args.max_usd is not None and args.max_usd < 0:
            raise CollectionError("--max-usd must be non-negative")
        if args.judge_input_usd_per_mtok < 0 or args.judge_output_usd_per_mtok < 0:
            raise CollectionError("judge USD-per-Mtok rates must be non-negative")
        effective_route, judge_route, seat_key, seat_metadata = _route_metadata(args)
        if args.eligibility == "deepseek-only" and effective_route.family != "gemini":
            raise CollectionError("--eligibility deepseek-only is reserved for the gemini route")
        seat_caps = _parse_seat_caps(args.seat_cap)
        main_document = _read_json(args.main_labels)
        probe_document = _read_json(args.probe_labels)
        main_cases = _cases(main_document, "main")
        probe_cases = _cases(probe_document, "probe")
        all_cases = [("probe", case) for case in probe_cases] + [("main", case) for case in main_cases]
        source_hashes = {
            _required_str(case, "artifact_sha256", str(case.get("case_id", "unknown")))
            for _corpus, case in all_cases
            if _candidate_rows(case)
            and not {
                _required_str(candidate, "candidate_id", str(case.get("case_id", "unknown")))
                for _event_output_id, candidate in _candidate_rows(case)
            }
            <= set(_embedded_raw_windows(case))
        }
        artifacts = _artifact_sources(source_hashes, (args.main_labels, args.probe_labels)) if source_hashes else {}
        prepared = [_prepared_case(corpus, case, artifacts) for corpus, case in all_cases]
        primary_modules = _planned_modules(prepared, eligibility=args.eligibility, effective_route=effective_route)
        stability_ids, stability_replay_modules = _stability_modules(
            prepared,
            main_cases=main_cases,
            probe_cases=probe_cases,
            eligibility=args.eligibility,
            effective_route=effective_route,
        )
        # Preserve probe-first authorization for both samples.  A stability
        # replay of a probe therefore cannot follow any main judge request.
        modules = [
            *[module for module in primary_modules if module.corpus == "probe"],
            *[module for module in stability_replay_modules if module.corpus == "probe"],
            *[module for module in primary_modules if module.corpus == "main"],
            *[module for module in stability_replay_modules if module.corpus == "main"],
        ]
        module_requests = [_module_request(module) for module in modules]
        request_routes = [_request_route(judge_route, request) for request, _hashes in module_requests]
        _preflight_caps(args=args, request_routes=request_routes, seat_key=seat_key, seat_caps=seat_caps)
        module_call_plan = _module_call_plan(modules, module_requests, request_routes)
        candidate_windows = sum(len(item.windows) for item in prepared)
        serializer_hash_checks = sum(len(item.windows) for item in prepared)
        probe_classes = sorted(
            {
                layerb_qualify._probe_class(case)
                for case in probe_cases
                if case.get("expected_layer_a_decision") == "ANCHOR"
            }
        )
        rare_failure_classes = sorted({str(case.get("failure_class")) for case in probe_cases})
        summary = {
            "status": "dry-run" if args.dry_run else "ready",
            "main_cases": len(main_cases),
            "probe_cases": len(probe_cases),
            "candidate_windows": candidate_windows,
            "module_calls": len(modules),
            "primary_module_calls": len(primary_modules),
            "stability_module_calls": len(stability_replay_modules),
            "probe_module_calls": sum(module.corpus == "probe" for module in modules),
            "main_module_calls": sum(module.corpus == "main" for module in modules),
            "stability_case_ids": stability_ids,
            "serializer_hash_checks": serializer_hash_checks,
            "worst_case_usd": sum(route.worst_case_usd for route in request_routes),
            "seat_key": seat_key,
            "probe_classes": probe_classes,
            "rare_failure_classes": rare_failure_classes,
            "judge_calls_made": 0,
        }
        if args.dry_run:
            print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
            return 0

        route_payload = {
            **effective_route.to_dict(),
            "collector_version": COLLECTOR_VERSION,
            "row_eligibility_matrix": [
                layerb_qualify.route_eligibility(case, effective_route) for _corpus, case in all_cases
            ],
            "collection_eligibility": args.eligibility,
            "seat_key": seat_key,
            "seat_metadata": seat_metadata,
        }
        output_dir = args.output_dir
        cache_dir = output_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        emissions: dict[str, list[dict[str, Any]]] = {}
        manifest: list[dict[str, Any]] = []
        ledger = layerb_shadow.BudgetLedger(args.max_usd, seat_caps, args.max_judge_calls)
        judge_environment = dict(os.environ)
        judge_environment["LAYERB_BRIDGE_FORENSICS_DIR"] = str(output_dir / "forensics")
        judge = layerb_shadow.SubprocessJudge(
            shlex.split(args.judge_command), args.judge_timeout_seconds, environment=judge_environment
        )
        for module, (request, serialized_window_hashes), module_route in zip(
            modules, module_requests, request_routes, strict=True
        ):
            request_hash = _sha256_json(request)
            cache_path = _cache_path(cache_dir, request, effective_route.to_dict(), attempt=module.attempt)
            cached = _read_json(cache_path) if args.resume and cache_path.is_file() else None
            call_id = _call_id(module)
            module_id = _module_id(module)
            call: layerb_shadow.JudgeCall | None = None
            response: Mapping[str, Any] | None = None
            bridge_forensics: dict[str, str] | None = None
            status = "completed"
            error: str | None = None
            cache_hit = cached is not None
            if cached is not None:
                response_value = cached.get("response")
                observed_value = cached.get("observed")
                if cached.get("request_sha256") != request_hash:
                    status, error = "failure", "cached request hash differs from the current module request"
                    observed = _observed(None, module_route)
                elif not isinstance(response_value, Mapping) or not isinstance(observed_value, Mapping):
                    status, error = "failure", "cached response or observation is malformed"
                    observed = _observed(None, module_route)
                else:
                    response = dict(response_value)
                    bridge_forensics = _bridge_forensics_sidecar({"_bridge_forensics": cached.get("bridge_forensics")})
                    call = layerb_shadow.JudgeCall(
                        response=response,
                        prompt_tokens=int(observed_value["prompt_tokens"])
                        if isinstance(observed_value.get("prompt_tokens"), (int, float))
                        else None,
                        completion_tokens=int(observed_value["completion_tokens"])
                        if isinstance(observed_value.get("completion_tokens"), (int, float))
                        else None,
                        cost_usd=float(observed_value["cost_usd"])
                        if isinstance(observed_value.get("cost_usd"), (int, float))
                        else None,
                    )
                    observed = _observed(call, module_route)
            else:
                reservation = ledger.reserve(seat_key, module_route)
                try:
                    call = judge(request, module_route)
                    response = dict(call.response)
                    bridge_forensics = _bridge_forensics_sidecar(response)
                    response.pop("_bridge_forensics", None)
                    observed = _observed(call, module_route)
                    ledger.settle(seat_key, reservation, call.cost_usd)
                    atomic_write_json(
                        cache_path,
                        {
                            "cache_identity_version": CACHE_VERSION,
                            "request_sha256": request_hash,
                            "response": response,
                            "bridge_forensics": bridge_forensics,
                            "observed": observed,
                            "route": effective_route.to_dict(),
                            "created_at": _utc_now(),
                        },
                    )
                except (TimeoutError, subprocess.TimeoutExpired) as exc:
                    ledger.settle(seat_key, reservation, None)
                    status, error, observed = "timeout", str(exc), _observed(None, module_route)
                except Exception as exc:  # Provider/bridge failures must remain in the scorer denominator.
                    ledger.settle(seat_key, reservation, None)
                    status, error, observed = "failure", str(exc), _observed(None, module_route)
            normalized: Mapping[str, Mapping[str, Any]] = {}
            substitutions_by_case: Mapping[str, Sequence[Mapping[str, str]]] = {}
            evidence_pattern_hits_by_case: Mapping[str, Sequence[Mapping[str, str]]] = {}
            if status == "completed" and response is not None:
                try:
                    normalized, substitutions_by_case = _validated_response_by_case(module, response)
                    evidence_pattern_hits_by_case = _evidence_pattern_hits_by_case(module, response)
                except layerb_shadow.JudgeValidationError as exc:
                    status, error = "failure", str(exc)
            module_emissions: dict[str, dict[str, Any]] = {}
            for prepared_case in module.cases:
                case_response = normalized.get(prepared_case.case_id) if status == "completed" else None
                module_emissions[prepared_case.case_id] = _emission(
                    prepared_case,
                    call_id=call_id,
                    attempt=module.attempt,
                    observed=observed,
                    response=case_response or _failure_response(prepared_case),
                    status=status,
                    validation_substituted=substitutions_by_case.get(prepared_case.case_id, ()),
                    evidence_pattern_hits=evidence_pattern_hits_by_case.get(prepared_case.case_id, ()),
                )
            for case_id, emission in module_emissions.items():
                attempts = emissions.setdefault(case_id, [])
                if len(attempts) != module.attempt:
                    raise CollectionError(
                        f"{case_id}: cannot record attempt {module.attempt} after {len(attempts)} prior attempts"
                    )
                attempts.append(emission)
            manifest.append(
                {
                    "artifact_sha256": module.artifact_sha256,
                    "module_id": module_id,
                    "call_id": call_id,
                    "attempt": module.attempt,
                    "corpus": module.corpus,
                    "case_ids": sorted(module_emissions),
                    "request_sha256": request_hash,
                    "raw_response": dict(response) if response is not None else None,
                    "bridge_forensics": bridge_forensics,
                    "window_sha256": {
                        window["candidate_id"]: window["raw_window_sha256"]
                        for prepared_case in module.cases
                        for window in prepared_case.windows
                    },
                    "serialized_window_sha256": serialized_window_hashes,
                    "input_token_upper_bound": module_route.max_input_tokens,
                    "expected_module_envelope": module_call_plan[module_id],
                    "cost": dict(observed),
                    "seat": {"key": seat_key, "metadata": seat_metadata},
                    "status": status,
                    "error": error,
                    "cache_hit": cache_hit,
                    "timestamp": _utc_now(),
                }
            )
            _write_collector_outputs(output_dir, emissions, route_payload, manifest, module_call_plan)
            if module.corpus == "probe":
                for prepared_case in module.cases:
                    probe_error = _probe_error(prepared_case, module_emissions[prepared_case.case_id], effective_route)
                    if probe_error:
                        raise ProbeFailure(f"probe {prepared_case.case_id} failed: {probe_error}")
        summary["judge_calls_made"] = ledger.calls
        summary["status"] = "completed"
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    except (CollectionError, ProbeFailure, layerb_shadow.BudgetStop) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover - CLI entry point.
    raise SystemExit(main())
