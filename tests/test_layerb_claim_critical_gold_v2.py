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
