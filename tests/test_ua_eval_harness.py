import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts/projects/ua_eval_harness"))

from evaluate_model import (
    ItemResult,
    compute_metrics,
    evaluate_item,
    mock_generate_correction,
    normalize_text,
    run_evaluation,
)


def test_normalize_text_strips_punctuation_and_whitespace():
    assert normalize_text("  Вітаю!  ") == "вітаю"
    assert normalize_text("Слідуючі пункти.") == "слідуючі пункти"


def test_mock_generate_correction_replaces_spans():
    text = "Я беру участь у слідуючих заходах."
    target = "Я беру участь у наступних заходах."
    edits = [{"source_span": "слідуючих", "target_span": "наступних"}]
    res = mock_generate_correction(text, target, edits)
    assert res == "Я беру участь у наступних заходах."


def test_evaluate_item_exact_match():
    item = {
        "id": "test-1",
        "text": "Я приймаю участь.",
        "target": "Я беру участь.",
        "edits": [{"category": "F/Calque", "source_span": "приймаю участь", "target_span": "беру участь"}],
    }
    res = evaluate_item(item, "Я беру участь.")
    assert res.exact_match is True
    assert res.target_span_retained is True
    assert res.source_span_eliminated is True
    assert res.score == 1.0


def test_compute_metrics_summary():
    results = [
        ItemResult("1", "F/Calque", "src", "tgt", "tgt", True, True, True, 1.0),
        ItemResult("2", "G/Case", "src", "tgt", "partial", False, False, True, 0.5),
    ]
    metrics = compute_metrics(results)
    assert metrics.total_items == 2
    assert metrics.exact_match_count == 1
    assert metrics.exact_match_accuracy == 0.5
    assert metrics.source_elimination_rate == 1.0
    assert "F/Calque" in metrics.category_breakdown
    assert "G/Case" in metrics.category_breakdown


def test_run_evaluation_raises_not_implemented_for_non_mock_models(tmp_path: Path):
    evalset_file = tmp_path / "evalset.jsonl"
    evalset_file.write_text('{"id":"1","text":"a","target":"b","edits":[]}\n', encoding="utf-8")

    with pytest.raises(NotImplementedError, match="Live model evaluation"):
        run_evaluation("gemini-3.6-flash-high", evalset_file)
