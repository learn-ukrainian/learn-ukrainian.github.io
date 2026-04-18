#!/usr/bin/env python3
"""Dimensional review benchmark driver — Phase 2 Step 3 of rollout.

Per `docs/design/dimensional-review.md` §7b, freezing reviewer-agent
assignments and per-dim thresholds requires measured recall/precision/
stability on a labeled corpus. This driver runs the review orchestrator
across a benchmark corpus and reports:

- **Per (agent, dim): recall** = caught_defects / total_planted_defects
- **Per (agent, dim): precision** = true_positive_findings / total_findings
  (requires findings on the CLEAN version to quantify false positives)
- **Per (agent, dim): stability** = score variance across reruns
- **Per (agent, dim): cost** = seconds per call, from the usage log

Ground-truth matching is fuzzy:

- A planted defect counts as caught iff the reviewer emits at least one
  finding with (a) the matching `dim`, (b) an `issue_type` in the
  defect's compatible-types set (configurable per dim), and (c) a
  `location`/`quote` that either contains the defect's `find` substring
  or reports a byte offset within tolerance.

### Benchmark corpus layout

```
benchmarks/wiki/
├── aspect/                          # case name
│   ├── clean.md                     # clean baseline
│   ├── light/
│   │   ├── defective.md            # 2-3 defects
│   │   └── ground_truth.yaml
│   └── heavy/
│       ├── defective.md            # 8-10 defects
│       └── ground_truth.yaml
├── vocative/
│   └── ...
```

### Usage

    # Smoke test: 1 case × 1 agent × 4 dims × 1 rerun (proves wiring)
    .venv/bin/python scripts/wiki/benchmark.py \\
        --corpus benchmarks/wiki \\
        --smoke

    # Full benchmark: all cases × all agents × all dims × N reruns
    .venv/bin/python scripts/wiki/benchmark.py \\
        --corpus benchmarks/wiki \\
        --reruns 3 \\
        --agents claude,gemini,codex \\
        --out benchmarks/wiki/.results/$(date +%Y-%m-%d).json

The full run is ~540 calls per §7b — CALLER's responsibility to have
budget headroom. This driver does NOT rate-limit itself; the underlying
runner will raise RateLimitedError and the driver records it.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# sys.path shim matching review.py
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from wiki.review import DIMS, _run_single_dim

#: Default fan-out for the benchmark outer loop. Each cell is one
#: subprocess-bound LLM call, so threads don't fight the GIL — they
#: just wait on IO. Bounded low to respect rate limits; override with
#: --concurrency.
DEFAULT_CONCURRENCY = 4

# ── Config ─────────────────────────────────────────────────────────

#: Which issue_types reported by the reviewer count as catching a
#: planted defect of each type. Lets the benchmark match up reviewer
#: taxonomy with spec taxonomy somewhat loosely. Entries are "ideal
#: match" — exact-match is preferred, but compatible types also count
#: (with a small score penalty in the scoring function).
COMPATIBLE_ISSUE_TYPES: dict[str, set[str]] = {
    # factual_accuracy prompt taxonomy
    "FACTUAL_ERROR": {"FACTUAL_ERROR", "LINGUISTIC_ERROR", "OUTDATED_CLAIM"},
    "LINGUISTIC_ERROR": {"LINGUISTIC_ERROR", "FACTUAL_ERROR"},
    "FABRICATED_ENTITY": {"FABRICATED_ENTITY", "FACTUAL_ERROR"},
    "HALLUCINATED_QUOTE": {"HALLUCINATED_QUOTE", "FACTUAL_ERROR"},
    "UNVERIFIABLE": {"UNVERIFIABLE"},
    "CONTESTED_AS_CONSENSUS": {"CONTESTED_AS_CONSENSUS"},
    "OUTDATED_CLAIM": {"OUTDATED_CLAIM", "FACTUAL_ERROR"},
    # source_grounding prompt taxonomy
    "OVERCLAIM": {"OVERCLAIM", "WEAK_SUPPORT"},
    "MISATTRIBUTION": {"MISATTRIBUTION"},
    "UNSUPPORTED_CLAIM": {"UNSUPPORTED_CLAIM"},
    "STALE_CITATION": {"STALE_CITATION"},
    "WEAK_SUPPORT": {"WEAK_SUPPORT", "OVERCLAIM"},
    # ukrainian_perspective prompt taxonomy
    "LIKE_RUSSIAN_BUT": {"LIKE_RUSSIAN_BUT", "DEFENSIVE_POSTURE"},
    "SOVIET_CHRONOLOGY": {"SOVIET_CHRONOLOGY"},
    "DISMISSED_AGENCY": {"DISMISSED_AGENCY"},
    "CONTESTED_FIGURE_AS_UKRAINIAN": {"CONTESTED_FIGURE_AS_UKRAINIAN"},
    "FABRICATED_CANON": {"FABRICATED_CANON", "FABRICATED_ENTITY"},
    "SOFT_NAMING_VIOLENCE": {"SOFT_NAMING_VIOLENCE"},
    "BOTHSIDESISM": {"BOTHSIDESISM"},
    "TOURISTIC_VOICE": {"TOURISTIC_VOICE"},
    "SOFT_PROVINCIAL": {"SOFT_PROVINCIAL"},
    "DEFENSIVE_POSTURE": {"DEFENSIVE_POSTURE", "LIKE_RUSSIAN_BUT"},
    # register prompt taxonomy
    "CALQUE": {"CALQUE", "TRANSLATIONESE"},
    "RUSSIANISM": {"RUSSIANISM", "CALQUE"},
    "TRANSLATIONESE": {"TRANSLATIONESE", "MT_SMELL"},
    "MT_SMELL": {"MT_SMELL", "TRANSLATIONESE"},
    "REGISTER_MISMATCH": {"REGISTER_MISMATCH"},
    "UNNATURAL_COLLOCATION": {"UNNATURAL_COLLOCATION"},
    "AWKWARD_PREPOSITION": {"AWKWARD_PREPOSITION", "CALQUE"},
    "SURZHYK_IN_FORMAL": {"SURZHYK_IN_FORMAL", "RUSSIANISM"},
}


# ── Dataclasses ────────────────────────────────────────────────────


@dataclass
class BenchmarkCase:
    name: str
    clean_path: Path
    variants: dict[str, tuple[Path, Path]]  # "light"/"heavy" → (defective, ground_truth)


@dataclass
class RunRecord:
    """One (case, variant, agent, dim, rerun) measurement."""

    case: str
    variant: str
    agent: str
    dim: str
    rerun: int
    score: int
    verdict: str
    findings_count: int
    duration_s: float
    caught_defect_ids: list[str]
    false_positive_findings: list[dict] = field(default_factory=list)
    error: str = ""


# ── Corpus loading ─────────────────────────────────────────────────


def load_corpus(corpus_dir: Path) -> list[BenchmarkCase]:
    """Scan corpus_dir for benchmark cases."""
    cases: list[BenchmarkCase] = []
    for case_dir in sorted(corpus_dir.iterdir()):
        if not case_dir.is_dir() or case_dir.name.startswith("."):
            continue
        clean_path = case_dir / "clean.md"
        if not clean_path.exists():
            continue

        variants: dict[str, tuple[Path, Path]] = {}
        for variant_name in ("light", "heavy"):
            variant_dir = case_dir / variant_name
            if not variant_dir.is_dir():
                continue
            defective = variant_dir / "defective.md"
            truth = variant_dir / "ground_truth.yaml"
            if defective.exists() and truth.exists():
                variants[variant_name] = (defective, truth)

        if variants:
            cases.append(BenchmarkCase(
                name=case_dir.name,
                clean_path=clean_path,
                variants=variants,
            ))
    return cases


def load_ground_truth(truth_path: Path) -> list[dict]:
    data = yaml.safe_load(truth_path.read_text(encoding="utf-8")) or {}
    return list(data.get("defects") or [])


# ── Finding-to-defect matching ─────────────────────────────────────


#: Quote-length cap for shotgun-gaming defense. A reviewer could "catch"
#: many defects by returning a quote that spans most of the article. We
#: only count a substring-in-quote match when the quote is within this
#: multiplier of the defect's own length. Surfaced in adversarial review
#: 2026-04-18. If a reviewer genuinely needs a huge quote, they'll
#: still score via the offset-based fallback.
_SHOTGUN_QUOTE_MULTIPLIER = 5


def _finding_catches_defect(finding: dict, defect: dict, article_text: str) -> bool:
    """Heuristic: does `finding` correspond to `defect`?

    Match requires:
      - finding's dim matches defect's dim (enforced by caller)
      - finding's issue_type is in compatible set for defect's issue_type
      - finding's quote or location text overlaps with the defect site

    Overlap check is done by substring: the defect's `replace:` text
    (= what's present in the defective article) should appear in the
    finding's quote/location when possible. If the quote is missing
    or empty, we fall back to offset-within-tolerance (±200 chars).

    Shotgun-gaming defense: substring-in-quote matches only count when
    the quote is not more than 5× longer than the defect itself —
    prevents a reviewer from scoring recall via "the whole article is
    broken" quotes that tautologically contain every defect.
    """
    defect_type = defect.get("issue_type", "")
    compatible = COMPATIBLE_ISSUE_TYPES.get(defect_type, {defect_type})
    finding_type = finding.get("issue_type", "")
    if finding_type not in compatible:
        return False

    defect_text = defect.get("replace", "")
    quote = (
        finding.get("claim_quote")
        or finding.get("framing_quote")
        or finding.get("quote", "")
    )
    if defect_text and quote:
        max_quote_len = _SHOTGUN_QUOTE_MULTIPLIER * max(len(defect_text), 40)
        if len(quote) <= max_quote_len and (
            defect_text in quote or quote in defect_text
        ):
            return True

    # Offset-based fallback (applies when quote is vague or shortened)
    offset = defect.get("offset", -1)
    if offset >= 0 and defect_text:
        window_start = max(0, offset - 200)
        window_end = min(len(article_text), offset + len(defect_text) + 200)
        window = article_text[window_start:window_end]
        # If reviewer returned a location string, check it against the window
        location = str(finding.get("location", ""))
        if location and location in window:
            return True

    return False


def _score_single_result(
    dim_result_findings: list[dict],
    ground_truth: list[dict],
    article_text: str,
    dim: str,
) -> tuple[list[str], list[dict]]:
    """Return (caught_defect_ids, false_positive_findings) for one dim."""
    # Filter ground truth to this dim only
    relevant_defects = [d for d in ground_truth if d.get("dim") == dim]
    caught_ids: list[str] = []

    for defect in relevant_defects:
        for finding in dim_result_findings:
            if _finding_catches_defect(finding, defect, article_text):
                caught_ids.append(str(defect.get("id", "")))
                break  # one match per defect is enough

    # False positives: findings that don't map back to any planted defect
    false_positives: list[dict] = []
    for finding in dim_result_findings:
        matched = False
        for defect in relevant_defects:
            if _finding_catches_defect(finding, defect, article_text):
                matched = True
                break
        if not matched:
            false_positives.append({
                "issue_type": finding.get("issue_type", ""),
                "location": finding.get("location", ""),
                "severity": finding.get("severity", ""),
            })

    return caught_ids, false_positives


# ── Runner ─────────────────────────────────────────────────────────


def run_benchmark(
    corpus: list[BenchmarkCase],
    *,
    agents: list[str],
    reruns: int,
    cwd: Path,
    include_clean: bool = True,
    smoke: bool = False,
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[RunRecord]:
    """Execute benchmark calls and return per-run records.

    Each (case, variant, agent, dim, rerun) cell is an independent
    subprocess-bound LLM call. Cells are fanned out via
    ``ThreadPoolExecutor`` at `concurrency` — the per-cell work
    blocks on subprocess IO so threads don't contend for the GIL.

    Args:
        corpus: benchmark cases
        agents: list of agents to try as primary for each dim
        reruns: how many times to repeat each cell for stability
        cwd: working directory for runner.invoke()
        include_clean: if True, also run against clean.md to measure
            false-positive rate (§7b precision component)
        smoke: if True, reduce to 1 case × 1 variant × 1 agent × 1 dim × 1 rerun
        concurrency: max parallel in-flight cells; respect rate limits
    """
    if smoke and corpus:
        corpus = corpus[:1]
        for c in corpus:
            c.variants = {k: v for k, v in list(c.variants.items())[:1]}
        agents = agents[:1]
        reruns = 1

    # Pre-load every distinct article once — the same file is re-used
    # across (agent × dim × rerun) cells and ground-truth YAML is read
    # per variant (not per cell).
    article_cache: dict[Path, str] = {}
    truth_cache: dict[Path, list[dict]] = {}
    for case in corpus:
        article_cache[case.clean_path] = case.clean_path.read_text(encoding="utf-8")
        for _, (defective, truth) in case.variants.items():
            article_cache[defective] = defective.read_text(encoding="utf-8")
            truth_cache[truth] = load_ground_truth(truth)

    # Build a flat job list, then fan out.
    jobs: list[dict[str, Any]] = []
    for case in corpus:
        if include_clean:
            for agent in agents:
                for dim in DIMS:
                    for rerun in range(reruns):
                        jobs.append({
                            "case": case, "variant": "clean",
                            "article_path": case.clean_path,
                            "article_text": article_cache[case.clean_path],
                            "ground_truth": [],
                            "agent": agent, "dim": dim, "rerun": rerun,
                            "cwd": cwd,
                        })
        for variant_name, (defective, truth) in case.variants.items():
            for agent in agents:
                for dim in DIMS:
                    for rerun in range(reruns):
                        jobs.append({
                            "case": case, "variant": variant_name,
                            "article_path": defective,
                            "article_text": article_cache[defective],
                            "ground_truth": truth_cache[truth],
                            "agent": agent, "dim": dim, "rerun": rerun,
                            "cwd": cwd,
                        })

    records: list[RunRecord] = []
    if not jobs:
        return records

    max_workers = max(1, min(concurrency, len(jobs)))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_one_run, **job) for job in jobs]
        for future in as_completed(futures):
            records.append(future.result())
    return records


def _one_run(
    *,
    case: BenchmarkCase,
    variant: str,
    article_path: Path,
    article_text: str,
    ground_truth: list[dict],
    agent: str,
    dim: str,
    rerun: int,
    cwd: Path,
) -> RunRecord:
    """Execute a single (case, variant, agent, dim, rerun) call."""
    # Force primary=agent, no fallback — we want to measure each agent
    # in isolation for the benchmark.
    dim_result = _run_single_dim(
        dim=dim,
        article_path=article_path,
        article_text=article_text,
        primary=agent,
        fallbacks=(),
        cwd=cwd,
    )

    if dim_result.error:
        return RunRecord(
            case=case.name,
            variant=variant,
            agent=agent,
            dim=dim,
            rerun=rerun,
            score=0,
            verdict="ERROR",
            findings_count=0,
            duration_s=dim_result.duration_s,
            caught_defect_ids=[],
            error=dim_result.error,
        )

    findings_raw = [f.raw for f in dim_result.findings]
    caught_ids, false_positives = _score_single_result(
        findings_raw,
        ground_truth,
        article_text,
        dim,
    )

    return RunRecord(
        case=case.name,
        variant=variant,
        agent=agent,
        dim=dim,
        rerun=rerun,
        score=dim_result.score,
        verdict=dim_result.verdict,
        findings_count=len(dim_result.findings),
        duration_s=dim_result.duration_s,
        caught_defect_ids=caught_ids,
        false_positive_findings=false_positives,
    )


# ── Aggregation ────────────────────────────────────────────────────


def aggregate(
    records: list[RunRecord],
    corpus: list[BenchmarkCase],
) -> dict[str, Any]:
    """Produce recall/precision/stability per (agent, dim).

    Recall    = caught_defects / total_planted_defects  (across variants × reruns)
    Precision = true_positives / total_findings         (on defective variants)
    Stability = stdev(scores)                           (across reruns)
    """
    # Tally planted defects per (case, variant, dim)
    planted: dict[tuple[str, str, str], int] = {}
    for case in corpus:
        for variant_name, (_, truth_path) in case.variants.items():
            gt = load_ground_truth(truth_path)
            for defect in gt:
                key = (case.name, variant_name, str(defect.get("dim", "")))
                planted[key] = planted.get(key, 0) + 1

    # Group records
    per_agent_dim: dict[tuple[str, str], list[RunRecord]] = {}
    for r in records:
        per_agent_dim.setdefault((r.agent, r.dim), []).append(r)

    summary: dict[str, Any] = {}
    for (agent, dim), group in sorted(per_agent_dim.items()):
        defective_runs = [r for r in group if r.variant != "clean" and not r.error]
        clean_runs = [r for r in group if r.variant == "clean" and not r.error]

        # Recall per variant
        total_planted = 0
        total_caught = 0
        for r in defective_runs:
            key = (r.case, r.variant, r.dim)
            total_planted += planted.get(key, 0)
            total_caught += len(r.caught_defect_ids)

        # Precision: true positives / (true positives + false positives)
        total_fp = sum(len(r.false_positive_findings) for r in defective_runs)
        precision = (
            total_caught / (total_caught + total_fp) if (total_caught + total_fp) else 0.0
        )
        recall = total_caught / total_planted if total_planted else 0.0

        # Stability
        scores = [r.score for r in group if not r.error]
        stability = statistics.stdev(scores) if len(scores) > 1 else 0.0

        # Cost
        durations = [r.duration_s for r in group if not r.error]
        mean_duration = statistics.fmean(durations) if durations else 0.0

        # Clean-run findings count (pure false-positive rate on clean)
        clean_findings = sum(r.findings_count for r in clean_runs)

        summary[f"{agent}:{dim}"] = {
            "agent": agent,
            "dim": dim,
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "f1": round(
                2 * recall * precision / (recall + precision) if (recall + precision) else 0.0,
                3,
            ),
            "stability_stdev": round(stability, 3),
            "mean_duration_s": round(mean_duration, 2),
            "runs_total": len(group),
            "runs_error": sum(1 for r in group if r.error),
            "clean_findings_total": clean_findings,
            "planted_total": total_planted,
            "caught_total": total_caught,
            "false_positives_total": total_fp,
        }

    return summary


def derive_thresholds(aggregated: dict[str, Any]) -> dict[str, int]:
    """Derive per-dim threshold suggestions from aggregated data.

    Stub implementation per §7b step 5: "score distributions on clean
    vs. defective artifacts determine per-dim min score. Threshold set
    at the separation point where defective artifacts reliably fall
    below."

    Proper implementation needs clean-vs-defective score histograms;
    the current benchmark records scores per run but this stub just
    picks the highest-F1 agent per dim and rounds its clean-run-mean.
    Intended as placeholder; calibration is an open design question
    pending real benchmark data.
    """
    by_dim: dict[str, list[dict]] = {}
    for entry in aggregated.values():
        by_dim.setdefault(entry["dim"], []).append(entry)

    thresholds: dict[str, int] = {}
    for dim in by_dim:
        # Placeholder: middle-ground threshold. Real calibration — score
        # distributions on clean vs. defective variants (§7b step 5) —
        # will replace this; until then all dims share the uncalibrated
        # default of 8.
        thresholds[dim] = 8
    return thresholds


# ── CLI ────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    # RawDescriptionHelpFormatter: the module docstring contains literal
    # strftime directives (%Y-%m-%d) in usage examples that would otherwise
    # blow up argparse's default %-substitution on --help.
    parser = argparse.ArgumentParser(
        description=__doc__ or "",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--corpus",
        required=True,
        help="Path to benchmark corpus directory",
    )
    parser.add_argument(
        "--agents",
        default="claude,gemini,codex",
        help="Comma-separated agent list (default: claude,gemini,codex)",
    )
    parser.add_argument(
        "--reruns",
        type=int,
        default=3,
        help="Reruns per (case, variant, agent, dim) for stability (default 3)",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Smoke test: 1 case × 1 variant × 1 agent × 1 dim × 1 rerun",
    )
    parser.add_argument(
        "--out",
        help="Output JSON path (default: stdout)",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip clean-variant runs (saves ~25%% calls; no precision measurement)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Max parallel in-flight cells (default {DEFAULT_CONCURRENCY}). "
             "Set low enough to respect per-agent rate limits.",
    )
    args = parser.parse_args(argv)

    corpus_dir = Path(args.corpus).resolve()
    if not corpus_dir.exists():
        print(f"error: corpus dir not found: {corpus_dir}", file=sys.stderr)
        return 2

    corpus = load_corpus(corpus_dir)
    if not corpus:
        print(f"error: no benchmark cases found in {corpus_dir}", file=sys.stderr)
        return 2

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]

    started_at = time.time()
    records = run_benchmark(
        corpus,
        agents=agents,
        reruns=args.reruns,
        cwd=_REPO_ROOT,
        include_clean=not args.skip_clean,
        smoke=args.smoke,
        concurrency=args.concurrency,
    )
    finished_at = time.time()

    aggregated = aggregate(records, corpus)
    thresholds = derive_thresholds(aggregated)

    output = {
        "corpus_dir": str(corpus_dir),
        "cases": [c.name for c in corpus],
        "agents": agents,
        "reruns": args.reruns,
        "smoke_mode": args.smoke,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_s": round(finished_at - started_at, 2),
        "runs_total": len(records),
        "runs_error": sum(1 for r in records if r.error),
        "per_agent_dim": aggregated,
        "derived_thresholds": thresholds,
        "thresholds_calibrated": False,  # stub derive_thresholds; flip when real
    }

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote: {out_path}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


# Re-export for orchestrator convenience
__all__ = [
    "BenchmarkCase",
    "RunRecord",
    "aggregate",
    "derive_thresholds",
    "load_corpus",
    "load_ground_truth",
    "run_benchmark",
]


if __name__ == "__main__":
    raise SystemExit(main())
