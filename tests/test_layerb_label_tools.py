"""Focused offline tests for Layer B label-union, scaffold, and merge tooling."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from scripts.audit.layerb_label_common import LabelJoinError, sha256_text
from scripts.audit.layerb_label_merge import merge_annotator_sidecars
from scripts.audit.layerb_label_scaffold import (
    JUDGMENT_CASE_FIELDS,
    _artifact_events,
    _build_event_index,
    build_scaffold,
    validate_annotator_record,
)
from scripts.audit.layerb_label_union import attach_keys, derive_union
from scripts.audit.layerb_shadow import _stable_grounding_key

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((REPO_ROOT / "schemas" / "qg-layer-b-labels.v2.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
RAW_OUTPUT = "source evidence used for deterministic label checks"
EXCERPT = "source evidence"


def _sha(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _candidate(index: int, event_output_id: str) -> dict[str, Any]:
    normalized = RAW_OUTPUT
    return {
        "schema_version": "qg-anchor-candidate.v1",
        "candidate_id": _sha(f"candidate-{index}"),
        "event_output_id": event_output_id,
        "canonical_source_id": _sha("synthetic-source"),
        "source_index": 0,
        "tool_identity": {"raw_name": "sources_query_wikipedia", "canonical_name": "query_wikipedia"},
        "query_identity": {"canonical_json": '{"query":"synthetic"}', "sha256": _sha('{"query":"synthetic"}')},
        "raw_output_sha256": _sha(RAW_OUTPUT),
        "normalized_output_sha256": _sha(normalized),
        "output_capture_complete": True,
        "anchor_scan_complete": True,
        "match_type": "EXACT_CONTIGUOUS",
        "similarity": 1.0,
        "tool_query_matched": True,
        "eligibility": "ELIGIBLE",
        "error_status": "NONE",
        "ordered_segment_spans": [
            {
                "segment_index": 0,
                "excerpt_normalized_start": 0,
                "excerpt_normalized_end": len(EXCERPT),
                "output_normalized_start": 0,
                "output_normalized_end": len(EXCERPT),
                "output_raw_start": 0,
                "output_raw_end": len(EXCERPT),
                "normalized_segment_sha256": _sha(EXCERPT),
                "raw_segment_sha256": _sha(EXCERPT),
            }
        ],
    }


def _inputs(tmp_path: Path, count: int = 8) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Path]:
    corpus_dir = tmp_path / "audit-corpus"
    corpus_dir.mkdir()
    metadata = {"pin_slug": "synthetic-pin", "family": "synthetic"}
    artifact_name = "synthetic-pin__ahatanhel-krymskyi.json"
    event = {
        "tool": "sources_query_wikipedia",
        "input": {"query": "synthetic"},
        "status": "completed",
        "output": RAW_OUTPUT,
    }
    event_output_id = next(iter(_build_event_index([event])))
    fact_checks: list[dict[str, Any]] = []
    for index in range(count):
        fact_checks.append(
            {
                "fact_check_id": f"fact-{index}",
                "claim": f"Synthetic claim {index}",
                "verdict": "CONFIRMED",
                "grounding": {
                    "evidence_excerpt": EXCERPT,
                    "tool": "sources_query_wikipedia",
                    "query": "synthetic",
                },
            }
        )
    artifact = {
        "schema_version": "qg_bakeoff_run.v1",
        "seat_arm": metadata,
        "fixture": {"slug": "ahatanhel-krymskyi"},
        "payload": {"fact_checks": fact_checks},
        "dispatch": {"tool_events": [event]},
    }
    (corpus_dir / artifact_name).write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
    derivations: list[dict[str, Any]] = []
    shadows: list[dict[str, Any]] = []
    union_rows: list[dict[str, Any]] = []
    for index, fact_check in enumerate(fact_checks):
        v1_admissible = index in {1, 3, 4}
        v2_effective = index in {0, 2, 3, 4}
        v2_abstained = index == 2
        base = {
            "fixture": "ahatanhel-krymskyi",
            "seat_arm": repr(metadata) + "/tooled",
            "claim": fact_check["claim"],
            "excerpt": EXCERPT,
            "v1_admissible": v1_admissible,
            "v2_anchored": v2_effective and not v2_abstained,
            "v2_abstained": v2_abstained,
            "similarity": 1.0,
            "abstain_recovered": v2_abstained,
            "v2_effective": v2_effective,
            "tool_query_matched": True,
            "best_span_preview": EXCERPT,
            "gold_is_true": True,
        }
        derivations.append(base)
        key = _stable_grounding_key(Path(artifact_name), index, fact_check)
        shadows.append(
            {
                "grounding_key": key,
                "artifact": artifact_name,
                "seat_metadata": metadata,
                "fixture": "ahatanhel-krymskyi",
                "fact_check_id": key,
                "claim": fact_check["claim"],
                "reviewer_verdict": "CONFIRMED",
                "layer_a": {
                    "decision": "ANCHOR",
                    "reason": "ANCHORED_CONTIGUOUS",
                    "candidate_set_complete": True,
                    "candidates": [_candidate(index, event_output_id)],
                },
                "candidate_details": [{"candidate": _candidate(index, event_output_id)}],
            }
        )
        union = dict(base)
        union["source_index"] = index
        union["union_categories"] = ["recovered"]
        union_rows.append(union)
    return (
        {"kind": "qg-layer-b-label-union-input", "rows": union_rows, "total_rows": len(union_rows)},
        {"records": derivations},
        {"records": list(reversed(shadows))},
        corpus_dir,
    )


def _completed_case(case: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(case))
    result.update(
        {
            "claim_is_true": True,
            "expected_reviewer_verdict": "CONFIRMED",
            "expected_layer_a_decision": "ANCHOR",
            "expected_layer_a_reason": "ANCHORED_CONTIGUOUS",
            "expected_aggregate_relation": "ENTAILS",
            "expected_fact_check_decision": "ACCEPT",
            "context_sufficient": True,
            "failure_class": "ELLIPSIZED_GENUINE_EXCERPT",
            "corpus_verification_status": "VERIFIED",
            "annotators": ["annotator-a", "annotator-b"],
            "adjudication": {"status": "AGREED", "adjudicator": None, "note": "Original completed case."},
        }
    )
    for candidates in result["candidates_by_event_output_id"].values():
        for candidate in candidates:
            candidate["expected_source_relation"] = "ENTAILS"
            candidate["expected_support_spans"] = [{"start": 0, "end": len(EXCERPT), "role": "SUPPORTS"}]
    return result


def _keyed_inputs(tmp_path: Path, count: int = 8) -> tuple[dict[str, Any], dict[str, Any], Path]:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count)
    keyed, _report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)
    return keyed, shadow, corpus_dir


def test_attach_totality_bijection_and_original_row_preservation_for_535_rows(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=535)

    keyed, report = attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)

    assert report["matched_rows"] == report["union_rows"] == 535
    assert report["total"] is True
    assert report["bijective"] is True
    assert len({row["grounding_key"] for row in keyed["rows"]}) == 535
    for original, emitted in zip(union["rows"], keyed["rows"], strict=True):
        preserved = {key: value for key, value in emitted.items() if key not in {"grounding_key", "fact_check_index"}}
        assert preserved == original


def test_attach_hard_fails_with_exact_ambiguous_key(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=2)
    duplicate = copy.deepcopy(derivation["records"][0])
    derivation["records"].append(duplicate)
    ambiguous = copy.deepcopy(union["rows"][0])
    ambiguous.pop("source_index")
    union["rows"] = [ambiguous]

    with pytest.raises(LabelJoinError, match=r"ambiguous keys=.*Synthetic claim 0"):
        attach_keys(union, derivation, shadow, corpus_dir=corpus_dir)


def test_attached_keys_equal_shadow_helper_for_sampled_rows(tmp_path: Path) -> None:
    keyed, _shadow, corpus_dir = _keyed_inputs(tmp_path, count=12)
    artifact_path = next(corpus_dir.glob("*.json"))
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    for row in keyed["rows"][::5]:
        index = row["fact_check_index"]
        assert row["grounding_key"] == _stable_grounding_key(
            artifact_path, index, artifact["payload"]["fact_checks"][index]
        )


def test_mode_b_is_byte_identical_for_the_same_seed(tmp_path: Path) -> None:
    union, derivation, shadow, corpus_dir = _inputs(tmp_path, count=8)
    del union

    first, first_report = derive_union(derivation, shadow, corpus_dir=corpus_dir, seed=4913, control_per_stratum=1)
    second, second_report = derive_union(derivation, shadow, corpus_dir=corpus_dir, seed=4913, control_per_stratum=1)

    assert json.dumps(first, ensure_ascii=False, separators=(",", ":")) == json.dumps(
        second, ensure_ascii=False, separators=(",", ":")
    )
    assert first_report == second_report
    assert first_report["frozen_control_sample_reproduction_guaranteed"] is False


def test_scaffold_null_judgments_hashes_windows_and_resume(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path, count=8)
    output_dir = tmp_path / "scaffold"

    with pytest.raises(RuntimeError, match="simulated crash"):
        build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=output_dir, shard_count=4, crash_after_shards=1)
    scaffold, report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=output_dir, shard_count=4)

    assert report["cases"] == 8
    assert all(case[field] is None for case in scaffold["cases"] for field in JUDGMENT_CASE_FIELDS)
    packet_case_ids: list[str] = []
    for packet_path in sorted((output_dir / "packets").glob("shard-*.jsonl")):
        marker = packet_path.with_suffix(".done.json")
        assert marker.is_file()
        for line in packet_path.read_text(encoding="utf-8").splitlines():
            packet = json.loads(line)
            packet_case_ids.append(packet["case"]["case_id"])
            for navigation in packet["candidate_navigation"]:
                assert navigation["full_output_sha256"] == _sha(RAW_OUTPUT)
                assert navigation["full_output_bytes"] == len(RAW_OUTPUT.encode("utf-8"))
                assert (
                    navigation["raw_window_text"]
                    == RAW_OUTPUT[navigation["raw_window_start"] : navigation["raw_window_end"]]
                )
                assert navigation["comment"].startswith("NAVIGATION AID ONLY")
    assert sorted(packet_case_ids) == sorted(case["case_id"] for case in scaffold["cases"])
    assert len(packet_case_ids) == len(set(packet_case_ids)) == 8
    for case in scaffold["cases"]:
        for event_output_id, candidates in case["candidates_by_event_output_id"].items():
            for candidate in candidates:
                assert candidate["raw_output_sha256"] == sha256_text(RAW_OUTPUT)
                assert candidate["normalized_output_sha256"] == sha256_text(RAW_OUTPUT)
                assert event_output_id
                for segment in candidate["ordered_segment_spans"]:
                    raw = RAW_OUTPUT[segment["output_raw_start"] : segment["output_raw_end"]]
                    assert sha256_text(raw) == segment["raw_segment_sha256"]


def test_validate_annotator_record_rejects_out_of_bounds_spans(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path)
    scaffold, _report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=tmp_path / "scaffold")
    working = _completed_case(scaffold["cases"][0])
    working.pop("annotators")
    working.pop("adjudication")
    artifact = json.loads(next(corpus_dir.glob("*.json")).read_text(encoding="utf-8"))
    outputs = _build_event_index(_artifact_events(artifact))

    validate_annotator_record(working, outputs)
    invalid = copy.deepcopy(working)
    candidate = next(iter(invalid["candidates_by_event_output_id"].values()))[0]
    candidate["ordered_segment_spans"][0]["output_raw_end"] = len(RAW_OUTPUT) + 1
    with pytest.raises(LabelJoinError, match="out of bounds"):
        validate_annotator_record(invalid, outputs)


def test_merge_agreement_and_exact_span_disagreement(tmp_path: Path) -> None:
    keyed, shadow, corpus_dir = _keyed_inputs(tmp_path)
    scaffold, _report = build_scaffold(keyed, shadow, corpus_dir=corpus_dir, output_dir=tmp_path / "scaffold")
    completed = copy.deepcopy(scaffold)
    completed["cases"] = [_completed_case(case) for case in scaffold["cases"]]

    report, merged = merge_annotator_sidecars(completed, copy.deepcopy(completed))
    assert report["counts"]["agreed"] == len(completed["cases"])
    assert all(case["adjudication"]["status"] == "AGREED" for case in merged["cases"])
    assert not list(VALIDATOR.iter_errors(merged))

    right = copy.deepcopy(completed)
    target = next(iter(right["cases"][0]["candidates_by_event_output_id"].values()))[0]
    target["ordered_segment_spans"][0]["output_raw_end"] -= 1
    report, merged = merge_annotator_sidecars(completed, right)
    assert report["counts"]["material_disagreements"] == 1
    assert report["counts"]["span_only_disagreements"] == 1
    assert report["cases"][0]["material_differences"][0]["field"].endswith("ordered_segment_spans")
    assert "adjudication" not in merged["cases"][0]
    assert list(VALIDATOR.iter_errors(merged))
