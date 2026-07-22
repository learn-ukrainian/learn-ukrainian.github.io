#!/usr/bin/env python3
"""Evaluate LLM models against the Ukrainian Calque + Grammar Evaluation Dataset (UNLP 2027 target).

Reads the compiled HuggingFace-compatible JSONL dataset (e.g. ``evalset_v1.jsonl``),
queries the target model via AI Agent Bridge or mock baseline, and computes
per-category and overall Exact Match Accuracy, Source Span Elimination Rate,
Target Span Retention Rate, and Composite Span Correction Score.

Usage
-----
    .venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py --model mock
    .venv/bin/python scripts/projects/ua_eval_harness/evaluate_model.py --model mock --limit 10
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DEFAULT_EVALSET = ROOT / "data" / "projects" / "ua_eval_harness" / "evalset_v1.jsonl"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "projects" / "ua_eval_harness"


@dataclass
class ItemResult:
    item_id: str
    category: str
    source_text: str
    target_text: str
    model_output: str
    exact_match: bool
    target_span_retained: bool
    source_span_eliminated: bool
    score: float


@dataclass
class MetricSummary:
    total_items: int
    exact_match_count: int
    exact_match_accuracy: float
    source_elimination_rate: float
    target_retention_rate: float
    composite_span_score: float
    category_breakdown: dict[str, dict[str, Any]]


def load_evalset(evalset_path: Path) -> list[dict[str, Any]]:
    """Load items from the compiled JSONL evalset file."""
    if not evalset_path.exists():
        raise FileNotFoundError(f"Evalset file not found: {evalset_path}")
    items: list[dict[str, Any]] = []
    with evalset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def mock_generate_correction(text: str, target: str, edits: list[dict[str, Any]]) -> str:
    """Mock generator simulating a high-quality LLM correction baseline."""
    corrected = text
    for edit in edits:
        src = edit.get("source_span", "")
        tgt = edit.get("target_span", "")
        if src and tgt:
            corrected = corrected.replace(src, tgt)
    return corrected


def normalize_text(text: str) -> str:
    """Normalize whitespace and punctuation for string comparison."""
    text = re.sub(r"\s+", " ", text.strip())
    text = text.rstrip(".!?")
    return text.lower()


def evaluate_item(item: dict[str, Any], model_output: str) -> ItemResult:
    """Evaluate a single model output against the gold item annotations."""
    item_id = item["id"]
    edits = item.get("edits", [])
    category = edits[0]["category"] if edits else "Unknown"
    target_text = item.get("target", "")

    norm_output = normalize_text(model_output)
    norm_target = normalize_text(target_text)

    exact_match = (norm_output == norm_target)

    # Check span-level correction accuracy
    target_retained = True
    source_eliminated = True

    for edit in edits:
        src = normalize_text(edit.get("source_span", ""))
        tgt = normalize_text(edit.get("target_span", ""))

        if tgt and tgt not in norm_output:
            target_retained = False
        if src and src in norm_output:
            source_eliminated = False

    score = 1.0 if exact_match else (0.5 if (target_retained and source_eliminated) else 0.0)

    return ItemResult(
        item_id=item_id,
        category=category,
        source_text=item.get("text", ""),
        target_text=target_text,
        model_output=model_output,
        exact_match=exact_match,
        target_span_retained=target_retained,
        source_span_eliminated=source_eliminated,
        score=score,
    )


def compute_metrics(results: list[ItemResult]) -> MetricSummary:
    """Compute overall and category-level exact match, span elimination, and span retention metrics."""
    if not results:
        return MetricSummary(
            total_items=0,
            exact_match_count=0,
            exact_match_accuracy=0.0,
            source_elimination_rate=0.0,
            target_retention_rate=0.0,
            composite_span_score=0.0,
            category_breakdown={},
        )

    total = len(results)
    exact_matches = sum(1 for r in results if r.exact_match)
    eliminated_count = sum(1 for r in results if r.source_span_eliminated)
    retained_count = sum(1 for r in results if r.target_span_retained)

    elim_rate = eliminated_count / total
    ret_rate = retained_count / total
    composite = (2 * elim_rate * ret_rate / (elim_rate + ret_rate)) if (elim_rate + ret_rate) > 0 else 0.0

    cat_groups: dict[str, list[ItemResult]] = {}
    for r in results:
        cat_groups.setdefault(r.category, []).append(r)

    cat_breakdown: dict[str, dict[str, Any]] = {}
    for cat, items in cat_groups.items():
        c_total = len(items)
        c_exact = sum(1 for i in items if i.exact_match)
        c_elim = sum(1 for i in items if i.source_span_eliminated)
        c_ret = sum(1 for i in items if i.target_span_retained)
        c_e_rate = c_elim / c_total
        c_r_rate = c_ret / c_total
        c_comp = (2 * c_e_rate * c_r_rate / (c_e_rate + c_r_rate)) if (c_e_rate + c_r_rate) > 0 else 0.0

        cat_breakdown[cat] = {
            "total": c_total,
            "exact_match_acc": round(c_exact / c_total, 4),
            "source_elimination_rate": round(c_e_rate, 4),
            "target_retention_rate": round(c_r_rate, 4),
            "composite_span_score": round(c_comp, 4),
        }

    return MetricSummary(
        total_items=total,
        exact_match_count=exact_matches,
        exact_match_accuracy=round(exact_matches / total, 4),
        source_elimination_rate=round(elim_rate, 4),
        target_retention_rate=round(ret_rate, 4),
        composite_span_score=round(composite, 4),
        category_breakdown=cat_breakdown,
    )


def run_evaluation(model: str, evalset_path: Path, limit: int | None = None) -> tuple[MetricSummary, list[ItemResult]]:
    """Run full evaluation suite for specified model on given evalset."""
    items = load_evalset(evalset_path)
    if limit is not None and limit > 0:
        items = items[:limit]

    results: list[ItemResult] = []

    for item in items:
        if model == "mock":
            output = mock_generate_correction(item["text"], item.get("target", ""), item.get("edits", []))
        else:
            raise NotImplementedError(
                f"Live model evaluation for '{model}' is not yet connected to the bridge runtime. "
                "Use '--model mock' for baseline harness verification."
            )

        result = evaluate_item(item, output)
        results.append(result)

    summary = compute_metrics(results)
    return summary, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate LLM models on UNLP 2027 Ukrainian Calque/Grammar Dataset.")
    parser.add_argument("--model", default="mock", help="Target model identifier (default: mock)")
    parser.add_argument("--evalset", type=Path, default=DEFAULT_EVALSET, help="Path to input evalset.jsonl")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory to save evaluation results")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of items evaluated")
    args = parser.parse_args()

    print(f"🚀 Running UNLP 2027 Calque/Grammar evaluation for model: [{args.model}]")
    print(f"📄 Evalset: {args.evalset}")

    start_time = time.time()
    summary, results = run_evaluation(args.model, args.evalset, limit=args.limit)
    elapsed = time.time() - start_time

    args.output_dir.mkdir(parents=True, exist_ok=True)
    out_file = args.output_dir / f"results_{args.model.replace('/', '_')}.json"

    output_payload = {
        "model": args.model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 2),
        "summary": asdict(summary),
        "item_results": [asdict(r) for r in results],
    }

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(output_payload, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Evaluation complete in {elapsed:.2f}s!")
    print(f"📊 Overall Exact Match Accuracy: {summary.exact_match_accuracy * 100:.1f}% ({summary.exact_match_count}/{summary.total_items})")
    print(f"🎯 Composite Span Score: {summary.composite_span_score:.4f} (Elimination: {summary.source_elimination_rate:.4f}, Retention: {summary.target_retention_rate:.4f})")
    print("\n📂 Category Breakdown:")
    for cat, cat_m in summary.category_breakdown.items():
        print(f"  - {cat:12s}: Acc={cat_m['exact_match_acc']*100:5.1f}%, Composite={cat_m['composite_span_score']:.4f} (n={cat_m['total']})")

    print(f"\n💾 Results written to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
