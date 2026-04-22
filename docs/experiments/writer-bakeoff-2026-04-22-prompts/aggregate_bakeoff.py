#!/usr/bin/env python3
"""Aggregate 20 round-robin bakeoff reviews into per-writer / per-reviewer scores.

Reads each review's result file at batch_state/tasks/review-<reviewer>-on-<writer>.result,
extracts the YAML block, saves to experiments/writer-bakeoff-2026-04-22/reviews/,
computes aggregate statistics, writes a JSON summary.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path("/Users/krisztiankoos/projects/learn-ukrainian")
TASKS = ROOT / "batch_state" / "tasks"
REVIEWS_OUT = ROOT / "experiments" / "writer-bakeoff-2026-04-22" / "reviews"
REVIEWS_OUT.mkdir(parents=True, exist_ok=True)

WRITERS = ["gemini-pro", "gemini-flash", "codex", "opus", "sonnet"]
AXES = [
    "linguistic_correctness",
    "pedagogical_accuracy",
    "decodability_a1",
    "plan_adherence",
    "register_naturalness",
    "honesty",
]


def extract_yaml(text: str) -> dict | None:
    """Extract the YAML block from a result file body. Tolerates ```yaml fences, preambles."""
    candidates: list[str] = []
    # 1. Fenced ```yaml ... ```
    for m in re.finditer(r"```(?:yaml)?\s*\n(.*?)```", text, re.DOTALL):
        candidates.append(m.group(1))
    # 2. From first "reviewer_model:" line to end
    m = re.search(r"^(reviewer_model:.*)", text, re.MULTILINE | re.DOTALL)
    if m:
        candidates.append(m.group(1))
    # 3. Whole thing as fallback
    candidates.append(text)
    for body in candidates:
        # Strip trailing fence marker if present
        body = re.sub(r"```\s*$", "", body.rstrip())
        try:
            data = yaml.safe_load(body)
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and ("axes" in data or "summary" in data):
            return data
    return None


def main() -> None:
    reviews: dict[tuple[str, str], dict] = {}  # (reviewer, writer) -> parsed review
    parse_failures: list[tuple[str, str, str]] = []

    for reviewer in WRITERS:
        for writer in WRITERS:
            if reviewer == writer:
                continue
            out_path = REVIEWS_OUT / f"{reviewer}-on-{writer}.yaml"
            # Prefer an existing handcrafted yaml (e.g. for parse failures we fixed by hand)
            if out_path.exists():
                parsed = yaml.safe_load(out_path.read_text())
                if isinstance(parsed, dict) and ("axes" in parsed or "summary" in parsed):
                    reviews[(reviewer, writer)] = parsed
                    continue
            task_id = f"review-{reviewer}-on-{writer}"
            result_path = TASKS / f"{task_id}.result"
            if not result_path.exists():
                parse_failures.append((reviewer, writer, "missing result file"))
                continue
            text = result_path.read_text()
            parsed = extract_yaml(text)
            if parsed is None:
                parse_failures.append((reviewer, writer, "could not parse YAML"))
                # Still save the raw text for inspection
                raw_out = REVIEWS_OUT / f"{reviewer}-on-{writer}.raw.txt"
                raw_out.write_text(text)
                continue
            reviews[(reviewer, writer)] = parsed
            out_path.write_text(yaml.safe_dump(parsed, allow_unicode=True, sort_keys=False))

    print(f"Parsed {len(reviews)} / 20 reviews")
    if parse_failures:
        print(f"Parse failures ({len(parse_failures)}):")
        for r, w, reason in parse_failures:
            print(f"  {r}-on-{w}: {reason}")

    # Per-writer aggregate (mean across 4 reviewers, per axis)
    per_writer: dict[str, dict] = {}
    for writer in WRITERS:
        axis_scores: dict[str, list[float]] = {a: [] for a in AXES}
        overall_scores: list[float] = []
        verdicts: list[str] = []
        word_counts: list[int] = []
        for reviewer in WRITERS:
            if reviewer == writer:
                continue
            rev = reviews.get((reviewer, writer))
            if rev is None:
                continue
            axes = rev.get("axes") or {}
            for axis in AXES:
                ax = axes.get(axis) or {}
                s = ax.get("score")
                if isinstance(s, (int, float)):
                    axis_scores[axis].append(float(s))
            summary = rev.get("summary") or {}
            ov = summary.get("overall_score")
            if isinstance(ov, (int, float)):
                overall_scores.append(float(ov))
            v = summary.get("verdict")
            if v:
                verdicts.append(str(v))
            wc = summary.get("word_count_estimate")
            if isinstance(wc, int):
                word_counts.append(wc)
        per_writer[writer] = {
            "mean_per_axis": {
                a: round(sum(v) / len(v), 2) if v else None
                for a, v in axis_scores.items()
            },
            "mean_overall": round(sum(overall_scores) / len(overall_scores), 2) if overall_scores else None,
            "n_reviews": len(overall_scores),
            "verdicts": verdicts,
            "word_count_estimates": word_counts,
        }

    # Per-reviewer calibration
    per_reviewer: dict[str, dict] = {}
    for reviewer in WRITERS:
        given_scores: list[float] = []
        verdict_counts: dict[str, int] = {"PASS": 0, "REVISE": 0, "FAIL": 0}
        evidence_counts: list[int] = []  # number of evidence entries across axes
        for writer in WRITERS:
            if reviewer == writer:
                continue
            rev = reviews.get((reviewer, writer))
            if rev is None:
                continue
            summary = rev.get("summary") or {}
            ov = summary.get("overall_score")
            if isinstance(ov, (int, float)):
                given_scores.append(float(ov))
            v = summary.get("verdict")
            if v in verdict_counts:
                verdict_counts[v] += 1
            axes = rev.get("axes") or {}
            ec = 0
            for axis in AXES:
                ax = axes.get(axis) or {}
                for key in ("evidence", "missing_from_plan", "extra_not_in_plan"):
                    val = ax.get(key)
                    if isinstance(val, list):
                        ec += len(val)
            evidence_counts.append(ec)
        per_reviewer[reviewer] = {
            "mean_score_given": round(sum(given_scores) / len(given_scores), 2) if given_scores else None,
            "score_range_given": (min(given_scores), max(given_scores)) if given_scores else None,
            "verdict_counts": verdict_counts,
            "mean_evidence_entries": round(sum(evidence_counts) / len(evidence_counts), 1) if evidence_counts else None,
            "n_reviews_given": len(given_scores),
        }

    aggregate = {
        "parsed_reviews": len(reviews),
        "parse_failures": [f"{r}-on-{w}: {msg}" for r, w, msg in parse_failures],
        "per_writer": per_writer,
        "per_reviewer": per_reviewer,
    }
    out_path = REVIEWS_OUT / "_aggregate.json"
    out_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False))
    print(f"\nAggregate written to {out_path}")

    # Print quick human-readable summary
    print("\n=== PER WRITER ===")
    ranked = sorted(
        [(w, d.get("mean_overall") or 0) for w, d in per_writer.items()],
        key=lambda x: -x[1],
    )
    for w, s in ranked:
        d = per_writer[w]
        print(f"  {w:15s}  overall={s:5.2f}  n={d['n_reviews']}  verdicts={dict((v, d['verdicts'].count(v)) for v in set(d['verdicts']))}")

    print("\n=== PER REVIEWER CALIBRATION ===")
    for r, d in per_reviewer.items():
        print(f"  {r:15s}  mean_given={d.get('mean_score_given')}  range={d.get('score_range_given')}  evidence={d.get('mean_evidence_entries')}  verdicts={d['verdict_counts']}")


if __name__ == "__main__":
    main()
