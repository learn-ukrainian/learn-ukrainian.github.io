from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.projects.ua_eval_harness import analyze_v011_evidence as analysis

ROOT = Path(__file__).resolve().parents[1]


def test_analysis_reproduces_metrics_and_complete_join(tmp_path: Path) -> None:
    summary = analysis.write_analysis(tmp_path)
    rows = [json.loads(line) for line in (tmp_path / "item_evidence.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len({row["item_id"] for row in rows}) == 677
    assert summary["reproduced_aggregate_metrics"]["gpt_5_6_terra"]["edit_correction"]["f0_5"] == 0.24390243902439027
    assert summary["reproduced_aggregate_metrics"]["gemma_4_31b_it"]["edit_correction"]["f0_5"] == 0.19335142469470828
    assert summary["counts"]["needs_ua_review"] == 14
    assert summary["counts"]["possible_benchmark_defect"] == 12
    assert summary["counts"]["protected_variation_risk"] == 3
    gaps = summary["category_gap_evidence"]
    assert gaps["strata"]["clean_no_change_control"]["items"] == 0
    assert gaps["strata"]["hard_positive_must_not_normalize"]["items"] == 0
    assert gaps["strata"]["core_grammar"]["items"] == 557
    assert gaps["strata"]["calque_lexical_choice"]["items"] == 194
    assert gaps["strata"]["cognate_contested_or_protected_review"]["items"] == 14
    assert gaps["strata"]["multiple_acceptable_references"]["items"] == 241
    assert gaps["eligible_tag_item_support"]["G/Aspect"] == 15
    assert all("exact_mismatch_not_linguistic_error" in row["uncertainty"] for row in rows)


def test_analysis_is_byte_deterministic_and_preserves_freeze(tmp_path: Path) -> None:
    freeze = ROOT / "data/projects/ua_eval_harness/releases/v0.1.1/freeze_manifest.json"
    before = hashlib.sha256(freeze.read_bytes()).hexdigest()
    first, second = tmp_path / "first", tmp_path / "second"
    analysis.write_analysis(first)
    analysis.write_analysis(second)
    for name in ("item_evidence.jsonl", "summary.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == before


def test_ordered_responses_rejects_invalid_id_sequences(tmp_path: Path) -> None:
    source = ROOT / "data/projects/ua_eval_harness/baselines/v1/gpt-5.6-terra.responses.jsonl"
    rows = analysis.read_jsonl(source)
    ids = [row["item_id"] for row in rows[1:]]
    variants = {
        "missing": rows[:-1],
        "duplicate": [rows[0], rows[1], rows[1], *rows[2:-1]],
        "reordered": [rows[0], rows[2], rows[1], *rows[3:]],
        "mismatched": [rows[0], {**rows[1], "item_id": "not-an-item"}, *rows[2:]],
    }
    for name, value in variants.items():
        path = tmp_path / f"{name}.jsonl"
        path.write_text("".join(analysis.canonical(row) + "\n" for row in value), encoding="utf-8")
        with pytest.raises(analysis.EvidenceError):
            analysis.ordered_responses(path, ids)
