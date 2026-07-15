"""Contract tests for the committed Layer B adversarial fixture corpus."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from scripts.audit import qg_bakeoff, qg_schema
from scripts.audit.layerb_keys import _build_event_index
from scripts.audit.layerb_label_scaffold import (
    _artifact_events,
    _schema_candidate,
    validate_annotator_record,
    verify_candidate_segments,
)
from scripts.audit.layerb_shadow import JudgeRoute, _extract_lineages, _injection_screen, _select_route

CORPUS_DIR = Path("tests/fixtures/curriculum_qg/layer_b_adversarial")
ARTIFACT_PATH = CORPUS_DIR / "adversarial-layer-b-fixture.json"
MANIFEST_PATH = CORPUS_DIR / "manifest.yaml"
EXPECTED_PROBE_CLASSES = {
    "digit",
    "name-swap",
    "meaning-inversion",
    "over-generalization",
    "tool-error-as-evidence",
    "multi-span",
    "cross-event-join",
    "lexical-variant",
    "irrelevant-support-offset",
    "prompt-injection",
}
EXPECTED_INJECTION_PROBES = {
    "delimiter-escape",
    "instruction-in-output",
    "query-echo",
    "boilerplate-double-false-evidence",
}
ARTIFACT_ENVELOPE_FIELDS = {
    "schema_version",
    "arm",
    "run_index",
    "created_at",
    "fixture",
    "model",
    "status",
    "workflow_verdict",
    "findings_schema_invalid",
    "response_parse_lenient",
    "attempt_count",
    "timed_out",
    "transport_retry",
    "dispatch",
    "gate_outcomes",
    "payload",
    "raw_response",
    "score",
    "tool_call_count",
    "wall_seconds",
}


def _load_corpus() -> tuple[dict[str, Any], dict[str, Any]]:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(artifact, dict)
    assert isinstance(manifest, dict)
    return artifact, manifest


def _event_for_call_id(events: list[Mapping[str, Any]], call_id: str) -> Mapping[str, Any]:
    return next(event for event in events if event.get("tool_call_id") == call_id)


def test_adversarial_corpus_has_required_coverage_and_exact_injection_set() -> None:
    _artifact, manifest = _load_corpus()
    cases = manifest["cases"]

    assert manifest["annotation_status"] == "PROPOSED"
    assert len(cases) == 24
    assert all(case["annotation_status"] == "PROPOSED" for case in cases.values())
    counts = Counter(case["probe_class"] for case in cases.values())
    assert set(counts) == EXPECTED_PROBE_CLASSES
    assert all(counts[probe_class] >= 2 for probe_class in EXPECTED_PROBE_CLASSES)
    assert counts["multi-span"] == 3
    assert counts["prompt-injection"] == 4
    assert counts["digit"] >= 3
    assert "wrong-occurrence-17-preface" in cases
    assert cases["wrong-occurrence-17-preface"].get("wrong_occurrence_probe") is True
    assert {
        case["injection_probe"] for case in cases.values() if case["probe_class"] == "prompt-injection"
    } == EXPECTED_INJECTION_PROBES


def test_adversarial_artifact_is_qg_bakeoff_shaped_and_lineage_safe() -> None:
    artifact, manifest = _load_corpus()

    assert artifact["schema_version"] == qg_bakeoff.RUN_SCHEMA_VERSION
    assert qg_bakeoff._load_all_artifacts(CORPUS_DIR) == [artifact]
    assert artifact.keys() >= ARTIFACT_ENVELOPE_FIELDS
    assert artifact["fixture"]["synthetic_fixture"] is True
    assert artifact["dispatch"]["reviewer_family"] == "adversarial-fixture"
    assert artifact["dispatch"]["reviewer_model_id"] == "adversarial-fixture"
    assert {event["tool"] for event in artifact["dispatch"]["tool_events"]} == {
        "query_wikipedia",
        "search_literary",
        "verify_word",
    }
    qg_schema.validate_reviewer_payload(artifact["payload"], "seminar")
    assert len(artifact["payload"]["fact_checks"]) == len(manifest["cases"])
    assert hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest() == next(iter(manifest["cases"].values()))[
        "artifact_sha256"
    ]

    fact_check = artifact["payload"]["fact_checks"][0]
    writer_family, reviewer_family = _extract_lineages(artifact, fact_check, fact_check["grounding"])
    assert (writer_family, reviewer_family) == ("fixture", "fixture")
    assert _select_route((JudgeRoute("gemini", "gemini-3.1-pro"),), writer_family, reviewer_family) is not None


def test_adversarial_candidates_pass_existing_event_index_and_scaffold_integrity() -> None:
    artifact, manifest = _load_corpus()
    events = _artifact_events(artifact)
    event_outputs = _build_event_index(events)
    cases = manifest["cases"]

    assert len(event_outputs) == 26
    for case in cases.values():
        validate_annotator_record(case, event_outputs)
        candidates_by_output = case["candidates_by_event_output_id"]
        if case["expected_layer_a_decision"] == "ANCHOR":
            assert candidates_by_output
        for event_output_id, candidates in candidates_by_output.items():
            for candidate in candidates:
                projected_event_output_id, _mechanical_projection = _schema_candidate(candidate)
                assert projected_event_output_id == event_output_id
                raw_output, _normalized_output = verify_candidate_segments(candidate, event_output_id, event_outputs)
                assert candidate["raw_output_sha256"] == hashlib.sha256(raw_output.encode("utf-8")).hexdigest()


def test_adversarial_injection_and_offset_probes_are_unsafe_to_accept() -> None:
    artifact, manifest = _load_corpus()
    events = _artifact_events(artifact)
    fact_checks = {fact_check["fact_check_id"]: fact_check for fact_check in artifact["payload"]["fact_checks"]}

    for case in manifest["cases"].values():
        fact_check = fact_checks[case["fact_check_id"]]
        source_event = _event_for_call_id(events, fact_check["grounding"]["tool_call_id"])
        raw_output = str(source_event["output"])
        if case["probe_class"] == "prompt-injection":
            assert case["expected_fact_check_decision"] == "AUDIT"
            assert _injection_screen(raw_output)
        if case["probe_class"] == "irrelevant-support-offset":
            assert case["expected_fact_check_decision"] == "AUDIT"
            simulated = case["simulated_judge_result"]["support_spans"][0]
            assert 0 <= simulated["start"] < simulated["end"] <= len(raw_output)
            anchored_spans = [
                segment
                for candidates in case["candidates_by_event_output_id"].values()
                for candidate in candidates
                for segment in candidate["ordered_segment_spans"]
            ]
            assert all(simulated["end"] <= span["output_raw_start"] for span in anchored_spans)
