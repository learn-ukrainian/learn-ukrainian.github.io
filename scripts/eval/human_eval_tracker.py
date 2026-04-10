#!/usr/bin/env python3
"""Human evaluation tracker (issue #1084).

Loads per-module human ratings from ``docs/eval/evaluations/*.yaml`` and
compares them against LLM review scores from the pipeline. Produces:

* Summary of human evaluations (count, mean, range)
* Inter-rater correlation between human and LLM scores (per-dimension
  and overall)
* A golden-reference list: modules rated >= 9 by a native reviewer
* A fix-candidate list: modules rated <= 7

Usage::

    .venv/bin/python scripts/eval/human_eval_tracker.py
    .venv/bin/python scripts/eval/human_eval_tracker.py --json
    .venv/bin/python scripts/eval/human_eval_tracker.py --module a1/my-family

No third-party dependencies beyond ``pyyaml`` — we compute Pearson
correlation by hand to keep the install surface small. Kendall tau-b
would be more robust for ordinal data but requires scipy.stats, which is
overkill for the current sample size.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = ROOT / "docs" / "eval" / "evaluations"
CURRICULUM_ROOT = ROOT / "curriculum" / "l2-uk-en"

# Canonical dimension names (match audit/aggregate_review_findings.py)
DIMENSIONS: tuple[str, ...] = (
    "plan_adherence",
    "linguistic_accuracy",
    "pedagogical_quality",
    "cultural_accuracy",
    "vocabulary_coverage",
    "exercise_quality",
    "dialogue_quality",
    "structural_integrity",
    "engagement_and_tone",
)


@dataclass
class HumanEval:
    """A single human evaluation record loaded from YAML."""

    path: Path
    reviewer: str
    reviewer_role: str
    evaluated_on: str
    level: str
    slug: str
    scores: dict[str, int]
    overall: str = ""
    publishable: str | bool = "unknown"
    notes: dict[str, str] = field(default_factory=dict)

    @property
    def module_id(self) -> str:
        return f"{self.level}/{self.slug}"

    @property
    def average(self) -> float:
        vals = [v for v in self.scores.values() if isinstance(v, (int, float))]
        return sum(vals) / len(vals) if vals else 0.0


def load_evaluations(eval_dir: Path = EVAL_DIR) -> list[HumanEval]:
    """Load every human evaluation YAML under ``eval_dir``."""
    if not eval_dir.exists():
        return []

    evals: list[HumanEval] = []
    for yml in sorted(eval_dir.glob("*.yaml")):
        try:
            raw = yaml.safe_load(yml.read_text())
        except yaml.YAMLError as e:
            print(f"[warn] {yml.name}: YAML error: {e}", file=sys.stderr)
            continue
        if not isinstance(raw, dict):
            continue
        module = raw.get("module", {}) or {}
        scores = raw.get("scores", {}) or {}
        evals.append(
            HumanEval(
                path=yml,
                reviewer=str(raw.get("reviewer", "unknown")),
                reviewer_role=str(raw.get("reviewer_role", "unknown")),
                evaluated_on=str(raw.get("evaluated_on", "unknown")),
                level=str(module.get("level", "unknown")),
                slug=str(module.get("slug", "unknown")),
                scores={k: int(v) for k, v in scores.items() if isinstance(v, (int, float))},
                overall=str(raw.get("overall", "")),
                publishable=raw.get("publishable", "unknown"),
                notes=raw.get("notes", {}) or {},
            )
        )
    return evals


def load_llm_scores(level: str, slug: str) -> dict[str, float] | None:
    """Pull the most recent LLM review scores for a module, if any.

    Looks in ``curriculum/l2-uk-en/{level}/review/{slug}-scores.yaml``
    (the pipeline's standard emit path). Returns ``None`` if no review
    scores are recorded yet.
    """
    review_path = CURRICULUM_ROOT / level / "review" / f"{slug}-scores.yaml"
    if not review_path.exists():
        return None
    try:
        data = yaml.safe_load(review_path.read_text()) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None

    scores = data.get("dimension_scores", data.get("scores"))
    if not isinstance(scores, dict):
        return None

    out: dict[str, float] = {}
    for k, v in scores.items():
        canon = _canonical_dimension(k)
        if canon and isinstance(v, (int, float)):
            out[canon] = float(v)
    return out


def _canonical_dimension(name: str) -> str | None:
    """Normalize a dimension label to our snake_case key."""
    key = name.strip().lower()
    key = key.replace("&", "and").replace("-", "_").replace(" ", "_")
    aliases = {
        "plan_adherence": "plan_adherence",
        "linguistic_accuracy": "linguistic_accuracy",
        "linguistic": "linguistic_accuracy",
        "pedagogical_quality": "pedagogical_quality",
        "pedagogical": "pedagogical_quality",
        "cultural_accuracy": "cultural_accuracy",
        "cultural": "cultural_accuracy",
        "vocabulary_coverage": "vocabulary_coverage",
        "vocabulary": "vocabulary_coverage",
        "exercise_quality": "exercise_quality",
        "exercise": "exercise_quality",
        "dialogue_quality": "dialogue_quality",
        "dialogue": "dialogue_quality",
        "structural_integrity": "structural_integrity",
        "structural": "structural_integrity",
        "engagement_and_tone": "engagement_and_tone",
        "engagement": "engagement_and_tone",
        "tone": "engagement_and_tone",
    }
    return aliases.get(key)


def pearson(xs: list[float], ys: list[float]) -> float | None:
    """Pearson correlation coefficient. Returns ``None`` if undefined."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=False))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return num / (denom_x * denom_y)


def compute_correlation(evals: list[HumanEval]) -> dict[str, Any]:
    """Compare human scores to LLM review scores per dimension.

    Returns a dict with per-dimension Pearson correlation and per-module
    average deltas (human minus LLM). When a module has no LLM scores on
    disk it contributes to ``missing_llm``.
    """
    per_dim_pairs: dict[str, tuple[list[float], list[float]]] = {
        d: ([], []) for d in DIMENSIONS
    }
    per_module: list[dict[str, Any]] = []
    missing_llm: list[str] = []

    for ev in evals:
        llm = load_llm_scores(ev.level, ev.slug)
        if llm is None:
            missing_llm.append(ev.module_id)
            continue
        row = {"module": ev.module_id, "reviewer": ev.reviewer, "deltas": {}}
        for dim in DIMENSIONS:
            if dim in ev.scores and dim in llm:
                per_dim_pairs[dim][0].append(float(ev.scores[dim]))
                per_dim_pairs[dim][1].append(llm[dim])
                row["deltas"][dim] = round(ev.scores[dim] - llm[dim], 2)
        per_module.append(row)

    dim_corr: dict[str, dict[str, Any]] = {}
    for dim, (hs, ls) in per_dim_pairs.items():
        dim_corr[dim] = {
            "n": len(hs),
            "human_mean": round(statistics.fmean(hs), 2) if hs else None,
            "llm_mean": round(statistics.fmean(ls), 2) if ls else None,
            "pearson_r": (round(r, 3) if (r := pearson(hs, ls)) is not None else None),
        }

    return {
        "per_dimension": dim_corr,
        "per_module": per_module,
        "missing_llm_scores": missing_llm,
    }


def build_summary(evals: list[HumanEval]) -> dict[str, Any]:
    """Top-level roll-up. Safe to JSON-dump."""
    if not evals:
        return {
            "count": 0,
            "reviewers": [],
            "golden_reference": [],
            "fix_candidates": [],
            "mean_overall": None,
            "per_dimension_means": {},
        }

    averages = [e.average for e in evals]
    per_dim: dict[str, list[int]] = {d: [] for d in DIMENSIONS}
    for e in evals:
        for dim in DIMENSIONS:
            if dim in e.scores:
                per_dim[dim].append(e.scores[dim])

    return {
        "count": len(evals),
        "reviewers": sorted({e.reviewer for e in evals}),
        "mean_overall": round(statistics.fmean(averages), 2),
        "per_dimension_means": {
            d: round(statistics.fmean(vs), 2) for d, vs in per_dim.items() if vs
        },
        "golden_reference": sorted({e.module_id for e in evals if e.average >= 9.0}),
        "fix_candidates": sorted({e.module_id for e in evals if e.average <= 7.0}),
    }


def format_report(summary: dict[str, Any], correlation: dict[str, Any]) -> str:
    """Render a plain-text report for the terminal."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("HUMAN EVALUATION TRACKER")
    lines.append("=" * 60)
    lines.append(f"Total human evaluations: {summary['count']}")
    if summary["count"] == 0:
        lines.append("")
        lines.append("No evaluations loaded. Drop YAML files into")
        lines.append(f"  {EVAL_DIR.relative_to(ROOT)}")
        lines.append("following docs/eval/human-eval-rubric.md.")
        return "\n".join(lines)

    lines.append(f"Reviewers: {', '.join(summary['reviewers'])}")
    lines.append(f"Mean overall score: {summary['mean_overall']}/10")
    lines.append("")
    lines.append("Per-dimension human means:")
    for dim, mean in sorted(summary["per_dimension_means"].items()):
        lines.append(f"  {dim:<25} {mean}")

    lines.append("")
    lines.append("Golden reference modules (>= 9):")
    for m in summary["golden_reference"]:
        lines.append(f"  ✓ {m}")

    lines.append("")
    lines.append("Fix candidates (<= 7):")
    for m in summary["fix_candidates"]:
        lines.append(f"  ✗ {m}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("Human vs LLM correlation (per dimension)")
    lines.append("-" * 60)
    for dim, stats in correlation["per_dimension"].items():
        n = stats["n"]
        r = stats["pearson_r"]
        hmean = stats["human_mean"]
        lmean = stats["llm_mean"]
        r_str = f"r={r:+.3f}" if r is not None else "r=n/a (need >=2 pairs)"
        lines.append(
            f"  {dim:<25} n={n:<3} human={hmean} llm={lmean} {r_str}"
        )

    if correlation["missing_llm_scores"]:
        lines.append("")
        lines.append(
            f"⚠  {len(correlation['missing_llm_scores'])} evaluated modules "
            "have no LLM review scores on disk:"
        )
        for m in correlation["missing_llm_scores"]:
            lines.append(f"    {m}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eval-dir", type=Path, default=EVAL_DIR,
        help="Directory of evaluation YAML files",
    )
    parser.add_argument(
        "--module", type=str, default=None,
        help="Filter to a single module (e.g. 'a1/my-family')",
    )
    parser.add_argument(
        "--json", action="store_true", help="Machine-readable JSON output",
    )
    args = parser.parse_args(argv)

    evals = load_evaluations(args.eval_dir)
    if args.module:
        evals = [e for e in evals if e.module_id == args.module]

    summary = build_summary(evals)
    correlation = compute_correlation(evals)

    if args.json:
        print(json.dumps({"summary": summary, "correlation": correlation}, indent=2))
    else:
        print(format_report(summary, correlation))
    return 0


if __name__ == "__main__":
    sys.exit(main())
