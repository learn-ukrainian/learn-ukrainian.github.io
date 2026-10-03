"""Paired variant-vs-baseline differences with bootstrap CIs and the pre-registered adoption rule.

Pairing unit: the set item. Each item's value for a variant is its mean over
repeats; the bootstrap resamples items with replacement (a cluster bootstrap,
since errors in one paragraph are not independent) and recomputes the ratio
statistics, giving percentile 95% intervals.

Adoption rule (Protocol v2, fixed before any run), applied per seat:
adopt ``adapted-v2`` (else ``original``) only when
  1. seeded-error recall improves with the 95% CI of the paired difference
     excluding zero (lower bound > 0);
  2. the false-alarm rate (all false alarms per 100 protected spans) does not
     rise by more than 2 points (point estimate of the paired difference);
  3. writing calque density (verdict-tier check_text calque/Russianism
     occurrences per 100 tokens; suspicions are reported, not ruled on) does not rise (point estimate <= 0), and every writing answer of
     both variants was scored (a failed writing item makes it inconclusive).
Anything else, including an inconclusive result, means no change for that seat.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np

from .common import BASELINE_VARIANT, CANDIDATE_ORDER, FALSE_ALARM_MAX_RISE
from .runner import ordered_labels

CI_LEVEL = 0.95


def _per_item(
    records: Sequence[dict[str, Any]], seat: str, variant: str, fields: Sequence[str]
) -> dict[str, np.ndarray]:
    sums: dict[str, np.ndarray] = {}
    counts: dict[str, int] = defaultdict(int)
    for record in records:
        if record["seat"] != seat or record["variant"] != variant:
            continue
        values = np.array([float(record[f]) for f in fields])
        sums[record["item_id"]] = sums.get(record["item_id"], np.zeros(len(fields))) + values
        counts[record["item_id"]] += 1
    return {item: total / counts[item] for item, total in sums.items()}


def bootstrap_paired(
    matrix: np.ndarray, statistic: Callable[[np.ndarray], float], iterations: int, seed: int
) -> tuple[float, float, float]:
    """Point estimate and percentile CI of ``statistic`` over item-resampled rows of ``matrix``."""
    point = statistic(matrix)
    rng = np.random.default_rng(seed)
    n = matrix.shape[0]
    draws = np.array([statistic(matrix[rng.integers(0, n, n)]) for _ in range(iterations)])
    draws = draws[np.isfinite(draws)]
    alpha = (1.0 - CI_LEVEL) / 2.0
    if draws.size == 0:
        return point, float("nan"), float("nan")
    return point, float(np.quantile(draws, alpha)), float(np.quantile(draws, 1.0 - alpha))


def _ratio_delta(num_v: int, den: int, num_b: int) -> Callable[[np.ndarray], float]:
    def statistic(m: np.ndarray) -> float:
        total = m[:, den].sum()
        return float("nan") if total == 0 else 100.0 * (m[:, num_v].sum() - m[:, num_b].sum()) / total

    return statistic


def _review_comparison(
    review: Sequence[dict[str, Any]], seat: str, variant: str, iterations: int, seed: int
) -> dict[str, Any]:
    fields = ("hits", "false_alarms", "n_errors", "protected_count", "failed")
    enriched = [{**r, "n_errors": len(r["errors"]), "failed": int(r["failed"])} for r in review]
    base = _per_item(enriched, seat, BASELINE_VARIANT, fields)
    cand = _per_item(enriched, seat, variant, fields)
    items = sorted(base.keys() & cand.keys())
    if not items:
        return {"available": False}
    # columns: hits_v, fa_v, hits_b, fa_b, n_errors, protected
    m = np.array([[cand[i][0], cand[i][1], base[i][0], base[i][1], base[i][2], base[i][3]] for i in items])
    recall = bootstrap_paired(m, _ratio_delta(0, 4, 2), iterations, seed)
    false_alarms = bootstrap_paired(m, _ratio_delta(1, 5, 3), iterations, seed + 1)
    errors, protected = m[:, 4].sum(), m[:, 5].sum()
    return {
        "available": True,
        "items": len(items),
        "errors": int(errors),
        "protected": int(protected),
        "recall_baseline": 100.0 * m[:, 2].sum() / errors if errors else None,
        "recall_variant": 100.0 * m[:, 0].sum() / errors if errors else None,
        "recall_delta": recall,
        "fa_baseline": 100.0 * m[:, 3].sum() / protected if protected else None,
        "fa_variant": 100.0 * m[:, 1].sum() / protected if protected else None,
        "fa_delta": false_alarms,
        "failed_items_baseline": float(sum(base[i][4] for i in items)),
        "failed_items_variant": float(sum(cand[i][4] for i in items)),
    }


def _writing_comparison(
    writing: Sequence[dict[str, Any]], seat: str, variant: str, iterations: int, seed: int
) -> dict[str, Any]:
    def densities(label: str) -> tuple[dict[str, float], int]:
        values: dict[str, list[float]] = defaultdict(list)
        failed = 0
        for r in writing:
            if r["seat"] == seat and r["variant"] == label:
                if r["failed"]:
                    failed += 1
                else:
                    values[r["item_id"]].append(r["metrics"]["calque_density"])
        return {k: float(np.mean(v)) for k, v in values.items()}, failed

    base, failed_b = densities(BASELINE_VARIANT)
    cand, failed_v = densities(variant)
    items = sorted(base.keys() & cand.keys())
    if not items:
        return {"available": False, "failed_baseline": failed_b, "failed_variant": failed_v}
    m = np.array([[cand[i] - base[i]] for i in items])
    delta = bootstrap_paired(m, lambda x: float(x[:, 0].mean()), iterations, seed + 2)
    return {
        "available": True,
        "tasks": len(items),
        "density_baseline": float(np.mean([base[i] for i in items])),
        "density_variant": float(np.mean([cand[i] for i in items])),
        "density_delta": delta,
        "failed_baseline": failed_b,
        "failed_variant": failed_v,
    }


def _adoption_check(review: dict[str, Any], writing: dict[str, Any]) -> dict[str, Any]:
    reasons = []
    recall_ok = review.get("available") and review["recall_delta"][1] > 0
    if not recall_ok:
        reasons.append("recall CI does not exclude zero" if review.get("available") else "no review data")
    fa_ok = review.get("available") and review["fa_delta"][0] <= FALSE_ALARM_MAX_RISE
    if review.get("available") and not fa_ok:
        reasons.append(
            f"false alarms rise by {review['fa_delta'][0]:.2f} > {FALSE_ALARM_MAX_RISE} per 100 protected spans"
        )
    writing_complete = writing.get("available") and not writing["failed_baseline"] and not writing["failed_variant"]
    calque_ok = writing_complete and writing["density_delta"][0] <= 0
    if not writing_complete:
        reasons.append("writing inconclusive (missing or failed writing answers)")
    elif not calque_ok:
        reasons.append(f"calque density rises by {writing['density_delta'][0]:.3f} per 100 tokens")
    return {"passes": bool(recall_ok and fa_ok and calque_ok), "reasons": reasons}


def _per_type(review: Sequence[dict[str, Any]], seat: str, variant: str) -> dict[str, list[int]]:
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for record in review:
        if record["seat"] == seat and record["variant"] == variant:
            for err in record["errors"]:
                tally[err["type"]][0] += int(err["hit"])
                tally[err["type"]][1] += 1
    return dict(sorted(tally.items()))


def _variant_totals(
    review: Sequence[dict[str, Any]], writing: Sequence[dict[str, Any]], seat: str, variant: str
) -> dict[str, Any]:
    rows = [r for r in review if r["seat"] == seat and r["variant"] == variant]
    wrows = [r for r in writing if r["seat"] == seat and r["variant"] == variant]
    ok = [r["metrics"] for r in wrows if not r["failed"]]

    def mean(key: str) -> float | None:
        values = [m[key] for m in ok if m.get(key) is not None]
        return float(np.mean(values)) if values else None

    return {
        "review_answers": len(rows),
        "review_failed": sum(r["failed"] for r in rows),
        "fa_protected": sum(r["fa_protected"] for r in rows),
        "fa_other": sum(r["fa_other"] for r in rows),
        "fa_unanchored": sum(r["fa_unanchored"] for r in rows),
        "wrong_corrections": sum(r["wrong_corrections"] for r in rows),
        "unlogged_changes": sum(r["unlogged_changes"] for r in rows),
        "new_invalid_forms": sum(len(r["new_invalid_forms"]) for r in rows),
        "style_total": sum(r["style"]["total"] for r in rows),
        "style_on_protected": sum(r["style"]["on_protected"] for r in rows),
        "style_on_error": sum(r["style"]["on_error"] for r in rows),
        "writing_answers": len(wrows),
        "writing_failed": sum(r["failed"] for r in wrows),
        "calque_density": mean("calque_density"),
        "calque_suspicion_density": mean("calque_suspicion_density"),
        "vesum_invalid_mean": mean("vesum_invalid"),
        "level_adherence": mean("level_adherence"),
        "english_intrusion": mean("english_intrusion"),
        "within_word_range": mean("within_word_range"),
        "per_type": _per_type(review, seat, variant),
    }


def _judge_summary(judge: Sequence[dict[str, Any]], seat: str) -> list[dict[str, Any]]:
    out = []
    pairs = sorted({tuple(r["pair"]) for r in judge if r["candidate_seat"] == seat})
    for pair in pairs:
        rows = [r for r in judge if r["candidate_seat"] == seat and tuple(r["pair"]) == pair]
        for judge_seat in sorted({r["judge_seat"] for r in rows}):
            sub = [r for r in rows if r["judge_seat"] == judge_seat]
            out.append(
                {
                    "pair": list(pair),
                    "judge_seat": judge_seat,
                    "wins": {label: sum(r["winner"] == label for r in sub) for label in pair},
                    "ties": sum(r["winner"] == "tie" for r in sub),
                    "failed": sum(r["failed"] for r in sub),
                }
            )
    return out


def build_report(scores: dict[str, Any], iterations: int = 10_000, seed: int = 9623) -> dict[str, Any]:
    review, writing, judge = scores["review"], scores["writing"], scores.get("judge", [])
    seats = list(dict.fromkeys(r["seat"] for r in [*review, *writing]))
    labels = ordered_labels({r["variant"] for r in [*review, *writing]})
    report: dict[str, Any] = {"denominator": scores.get("denominator", {}), "seats": {}}
    for seat in seats:
        seat_report: dict[str, Any] = {
            "totals": {label: _variant_totals(review, writing, seat, label) for label in labels},
            "comparisons": {},
            "judge": _judge_summary(judge, seat),
        }
        for label in labels:
            if label == BASELINE_VARIANT:
                continue
            rev = _review_comparison(review, seat, label, iterations, seed)
            wri = _writing_comparison(writing, seat, label, iterations, seed)
            seat_report["comparisons"][label] = {
                "review": rev,
                "writing": wri,
                "eligible": label in CANDIDATE_ORDER,
                "rule": _adoption_check(rev, wri),
            }
        adopted = next(
            (
                label
                for label in CANDIDATE_ORDER
                if label in seat_report["comparisons"] and seat_report["comparisons"][label]["rule"]["passes"]
            ),
            None,
        )
        seat_report["decision"] = adopted or "no change"
        report["seats"][seat] = seat_report
    return report


def _fmt(value: Any, digits: int = 1) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (tuple, list)):
        point, lo, hi = value
        return f"{point:+.{digits}f} [{lo:+.{digits}f}, {hi:+.{digits}f}]"
    return f"{value:.{digits}f}"


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Ukrainian preamble comparison (#9623)", ""]
    denominator = report.get("denominator") or {}
    if denominator:
        lines.append("Denominator: " + ", ".join(f"{k} {v}" for k, v in denominator.items()))
        lines.append("")
    lines += [
        "| Seat | Variant | Recall % (base → var) | Δ recall pp [95% CI] | FA /100 protected (base → var) "
        "| Δ FA [95% CI] | Δ calque density /100 tokens [95% CI] | Rule |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for seat, data in report["seats"].items():
        for label, comp in data["comparisons"].items():
            rev, wri = comp["review"], comp["writing"]
            recall = (
                f"{_fmt(rev.get('recall_baseline'))} → {_fmt(rev.get('recall_variant'))}"
                if rev.get("available")
                else "n/a"
            )
            fa = f"{_fmt(rev.get('fa_baseline'))} → {_fmt(rev.get('fa_variant'))}" if rev.get("available") else "n/a"
            rule = "pass" if comp["rule"]["passes"] else "fail: " + "; ".join(comp["rule"]["reasons"])
            if not comp["eligible"]:
                rule = "not eligible (" + rule + ")"
            lines.append(
                f"| {seat} | {label} | {recall} | {_fmt(rev.get('recall_delta'))} | {fa} | {_fmt(rev.get('fa_delta'))} "
                f"| {_fmt(wri.get('density_delta'), 3)} | {rule} |"
            )
    lines += ["", "## Decisions", ""]
    lines += [f"- {seat}: **{data['decision']}**" for seat, data in report["seats"].items()]
    lines += ["", "## Per-variant totals", ""]
    lines.append(
        "| Seat | Variant | Failed review | FA protected / other / unanchored | Wrong fixes | Unlogged edits "
        "| New invalid forms | Style (all / protected / on error) | Failed writing | Calque density (verdict / suspicion) | VESUM-invalid "
        "| Level adherence | English intrusion |"
    )
    lines.append("| " + " | ".join(["---"] * 13) + " |")
    for seat, data in report["seats"].items():
        for label, t in data["totals"].items():
            lines.append(
                f"| {seat} | {label} | {t['review_failed']}/{t['review_answers']} "
                f"| {t['fa_protected']} / {t['fa_other']} / {t['fa_unanchored']} | {t['wrong_corrections']} "
                f"| {t['unlogged_changes']} | {t['new_invalid_forms']} "
                f"| {t['style_total']} / {t['style_on_protected']} / {t['style_on_error']} "
                f"| {t['writing_failed']}/{t['writing_answers']} "
                f"| {_fmt(t['calque_density'], 3)} / {_fmt(t['calque_suspicion_density'], 3)} "
                f"| {_fmt(t['vesum_invalid_mean'], 2)} | {_fmt(t['level_adherence'], 3)} | {_fmt(t['english_intrusion'], 3)} |"
            )
    lines += ["", "## Recall by error type (hits/errors over all repeats)", ""]
    for seat, data in report["seats"].items():
        types = sorted({t for totals in data["totals"].values() for t in totals["per_type"]})
        labels = list(data["totals"])
        lines.append(f"### {seat}")
        lines.append("| Type | " + " | ".join(labels) + " |")
        lines.append("| --- |" + " --- |" * len(labels))
        for error_type in types:
            cells = []
            for label in labels:
                hit, total = data["totals"][label]["per_type"].get(error_type, [0, 0])
                cells.append(f"{hit}/{total}")
            lines.append(f"| {error_type} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Blind pairwise judgements", ""]
    lines.append("| Candidate seat | Pair | Judge | Wins | Ties | Failed |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for seat, data in report["seats"].items():
        for row in data["judge"]:
            wins = ", ".join(f"{k} {v}" for k, v in row["wins"].items())
            lines.append(
                f"| {seat} | {' vs '.join(row['pair'])} | {row['judge_seat']} | {wins} | {row['ties']} | {row['failed']} |"
            )
    return "\n".join(lines) + "\n"
