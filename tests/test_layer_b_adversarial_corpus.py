"""Contract tests for the committed Layer B adversarial fixture corpus."""

from __future__ import annotations

import hashlib
import json
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
from scripts.audit.layerb_shadow import JudgeRoute, _extract_lineages, _select_route

CORPUS_DIR = Path("tests/fixtures/curriculum_qg/layer_b_adversarial")
ARTIFACT_PATH = CORPUS_DIR / "adversarial-layer-b-fixture.json"
MANIFEST_PATH = CORPUS_DIR / "manifest.yaml"
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
