"""Contract tests for adversarial probe gold v2 (claim_critical_spans)."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.audit import layerb_qualify
from scripts.audit.layerb_keys import _build_event_index
from scripts.audit.layerb_label_scaffold import _artifact_events

CORPUS_DIR = Path("tests/fixtures/curriculum_qg/layer_b_adversarial")
GOLD_V2 = CORPUS_DIR / "labels-final.gold.v2.json"
ARTIFACT = CORPUS_DIR / "adversarial-layer-b-fixture.json"
DECISIVE = layerb_qualify.DECISIVE_RELATIONS


def _load_gold() -> dict:
    return json.loads(GOLD_V2.read_text(encoding="utf-8"))


def test_gold_v2_is_versioned_benchmark_semantic_change() -> None:
    gold = _load_gold()
    assert gold["schema_version"] == "qg-layer-b-labels.v2"
    assert gold["dataset_id"] == "qg-layer-b-adversarial-gold.v2-claim-critical-spans"
    assert gold["qualification_eligible"] is True
    assert gold["qualification_blockers"] == []
    assert len(gold["cases"]) == 24
    assert any(case["fact_check_id"] == "wrong-occurrence-17-preface" for case in gold["cases"])


def test_gold_v2_claim_critical_spans_slice_raw_windows() -> None:
    gold = _load_gold()
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    outputs = _build_event_index(_artifact_events(artifact))
    decisive_with_critical = 0
    for case in gold["cases"]:
        for event_output_id, candidates in case.get("candidates_by_event_output_id", {}).items():
            raw = outputs[event_output_id]
            for candidate in candidates:
                if candidate.get("expected_source_relation") not in DECISIVE:
                    continue
                critical = candidate.get("claim_critical_spans")
                assert isinstance(critical, list) and critical, case["fact_check_id"]
                decisive_with_critical += 1
                for span in critical:
                    start, end, role = span["start"], span["end"], span["role"]
                    assert isinstance(start, int) and isinstance(end, int)
                    assert 0 <= start < end <= len(raw)
                    assert isinstance(role, str) and role
                    # Slice must resolve on the same raw_window the scorer uses.
                    assert raw[start:end]
                    broad = candidate.get("expected_support_spans") or []
                    assert broad, "phrase-level expected_support_spans retained as context"
    assert decisive_with_critical >= 19


def test_gold_v2_wrong_occurrence_probe_fails_when_only_preface_spanned() -> None:
    gold = _load_gold()
    case = next(c for c in gold["cases"] if c["fact_check_id"] == "wrong-occurrence-17-preface")
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    outputs = _build_event_index(_artifact_events(artifact))
    event_output_id, candidates = next(iter(case["candidates_by_event_output_id"].items()))
    raw = outputs[event_output_id]
    candidate = candidates[0]
    critical = candidate["claim_critical_spans"][0]
    assert raw[critical["start"] : critical["end"]] == "17"
    first = raw.index("17")
    second = raw.index("17", first + 1)
    assert first != second
    assert critical["start"] == second
    assert not layerb_qualify.decisive_span_agreement(
        candidate, [{"start": first, "end": first + 2, "role": "CONTRADICTS"}]
    )
    assert layerb_qualify.decisive_span_agreement(
        candidate, [{"start": second, "end": second + 2, "role": "CONTRADICTS"}]
    )
