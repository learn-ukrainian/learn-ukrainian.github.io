"""Per-task win/tie/loss, paired metric differences, judge agreement and the human-rating slot.

Orientation: before unblinding the two sides are the blind labels A and B,
which only mean something per task. With the key, each task's A and B map to
the two writers and every statistic is writer-versus-writer.

- Task outcome: each judgement (judge x order) is one vote; the side with more
  votes wins the task, equal votes are a tie. Failed and abstaining
  judgements are counted and shown, never dropped, and never vote.
- Sign test: exact two-sided binomial test on decided tasks (ties excluded).
- Metrics: per task, the value for each side (judge score and criteria are
  means over every valid judgement); the paired difference first minus second
  with a percentile bootstrap 95% CI over tasks (``uk_preamble.report``).
- Judge agreement: a judge's verdict on a task combines its two orders; the
  same preference in both is that preference, different preferences are a tie
  (position-inconsistent, counted). Pairwise percent agreement and Cohen's
  kappa use tasks both judges decided in both orders.
"""

from __future__ import annotations

import itertools
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Any

import numpy as np

from scripts.eval.human_eval_tracker import HumanEval, pearson
from scripts.eval.uk_preamble.report import bootstrap_paired

from .core import SIDES, Manifest
from .judge import JUDGE_CRITERIA, ORDERS

MECHANICAL_METRICS = (
    "words",
    "vesum_invalid",
    "vesum_capitalised",
    "calque_hits",
    "calque_suspicion_hits",
    "cefr_above_level",
    "level_adherence",
    "english_intrusion",
    "stress_mark_coverage",
    "stress_wrong",
    "stress_unverified",
    "stress_ambiguous_unresolved",
)
JUDGE_METRICS = ("judge_score", *(f"judge_{c}" for c in JUDGE_CRITERIA))


def sign_test(wins: int, losses: int) -> float | None:
    """Exact two-sided sign-test p-value; None when no task was decided."""
    n = wins + losses
    if n == 0:
        return None
    tail = sum(math.comb(n, i) for i in range(min(wins, losses) + 1)) / 2**n
    return min(1.0, 2 * tail)


def cohen_kappa(left: Sequence[str], right: Sequence[str]) -> float | None:
    n = len(left)
    if n == 0:
        return None
    observed = sum(a == b for a, b in zip(left, right, strict=True)) / n
    count_l, count_r = Counter(left), Counter(right)
    expected = sum(count_l[c] * count_r[c] for c in set(left) | set(right)) / n**2
    return None if expected == 1 else (observed - expected) / (1 - expected)


def _mean(values: Sequence[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return statistics.fmean(present) if present else None


def _text_values(
    mechanical: dict[tuple[str, str], dict[str, Any]],
    judgements: Sequence[dict[str, Any]],
    human: dict[tuple[str, str], list[float]],
    task_id: str,
    side: str,
) -> dict[str, Any]:
    record = mechanical.get((task_id, side))
    metrics = record["metrics"] if record and not record["failed"] else {}
    values: dict[str, Any] = {m: metrics.get(m) for m in MECHANICAL_METRICS}
    valid = [r["texts"][side] for r in judgements if not r["failed"]]
    values["judge_score"] = _mean([t["score"] for t in valid])
    for criterion in JUDGE_CRITERIA:
        values[f"judge_{criterion}"] = _mean([t["criteria"][criterion] for t in valid])
    values["judge_findings"] = dict(Counter(e["severity"] for t in valid for e in t["errors"]))
    ratings = human.get((task_id, side), [])
    values["human_score"] = _mean(ratings)
    values["human_raters"] = len(ratings)
    return values


def _combined(records: Sequence[dict[str, Any]], orient: dict[str, str]) -> tuple[str | None, bool]:
    """(verdict over both orders or None, position-inconsistent)."""
    by_order = {r["order"]: r["preferred"] for r in records if not r["failed"]}
    if set(by_order) != set(ORDERS) or "abstain" in by_order.values():
        return None, False
    verdicts = {orient.get(v, v) for v in by_order.values()}
    if len(verdicts) == 1:
        return verdicts.pop(), False
    return "tie", True


def _judge_agreement(
    judgements: Sequence[dict[str, Any]], judges: Sequence[str], orients: dict[str, dict[str, str]]
) -> dict[str, Any]:
    by_judge_task: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in judgements:
        by_judge_task[(record["judge"], record["task_id"])].append(record)
    combined: dict[str, dict[str, str]] = {}
    per_judge = {}
    for judge in judges:
        verdicts, inconsistent = {}, 0
        for task_id, orient in orients.items():
            verdict, flipped = _combined(by_judge_task.get((judge, task_id), []), orient)
            if verdict is not None:
                verdicts[task_id] = verdict
                inconsistent += flipped
        records = [r for r in judgements if r["judge"] == judge]
        positional = [
            r["preferred_position"] for r in records if not r["failed"] and r["preferred_position"] in ("1", "2")
        ]
        per_judge[judge] = {
            "judgements": len(records),
            "failed": sum(r["failed"] for r in records),
            "abstained": sum(1 for r in records if r["preferred"] == "abstain"),
            "tasks_decided_both_orders": len(verdicts),
            "position_inconsistent": inconsistent,
            "position_consistency": (len(verdicts) - inconsistent) / len(verdicts) if verdicts else None,
            "first_position_preferred": positional.count("1") / len(positional) if positional else None,
        }
        combined[judge] = verdicts
    pairs = []
    for left, right in itertools.combinations(judges, 2):
        shared = sorted(set(combined[left]) & set(combined[right]))
        a = [combined[left][t] for t in shared]
        b = [combined[right][t] for t in shared]
        scores_l, scores_r = [], []
        for task_id in orients:
            for side in SIDES:
                values = []
                for judge in (left, right):
                    scores = [
                        r["texts"][side]["score"] for r in by_judge_task.get((judge, task_id), []) if not r["failed"]
                    ]
                    values.append(_mean(scores))
                if None not in values:
                    scores_l.append(values[0])
                    scores_r.append(values[1])
        pairs.append(
            {
                "judges": [left, right],
                "tasks": len(shared),
                "agreement": sum(x == y for x, y in zip(a, b, strict=True)) / len(shared) if shared else None,
                "kappa": cohen_kappa(a, b),
                "score_pearson": pearson(scores_l, scores_r),
                "texts_scored_by_both": len(scores_l),
            }
        )
    return {"per_judge": per_judge, "pairs": pairs}


def human_ratings(evaluations: Sequence[HumanEval], manifest: Manifest) -> dict[tuple[str, str], list[float]]:
    """Native-expert ratings in the ``human_eval_tracker`` YAML format, matched by ``module.slug``
    equal to ``<task id>-A`` or ``<task id>-B`` (the blind label, so raters stay blind)."""
    wanted = {f"{task.task_id}-{side}": (task.task_id, side) for task in manifest.tasks for side in SIDES}
    ratings: dict[tuple[str, str], list[float]] = defaultdict(list)
    for evaluation in evaluations:
        target = wanted.get(evaluation.slug)
        if target is not None and evaluation.scores:
            ratings[target].append(evaluation.average)
    return dict(ratings)


def build_report(
    manifest: Manifest,
    mechanical: Sequence[dict[str, Any]],
    judgements: Sequence[dict[str, Any]],
    *,
    judges: Sequence[str],
    key: dict[str, Any] | None = None,
    human: dict[tuple[str, str], list[float]] | None = None,
    frozen: dict[str, Any] | None = None,
    iterations: int = 2000,
    seed: int = 1028,
) -> dict[str, Any]:
    human = human or {}
    if key is None:
        orients = {task.task_id: {side: side for side in SIDES} for task in manifest.tasks}
        labels = list(SIDES)
    else:
        orients = {task_id: dict(sides) for task_id, sides in key["tasks"].items()}
        labels = sorted(key["writers"])
    first, second = labels
    mech = {(r["task_id"], r["side"]): r for r in mechanical}
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in judgements:
        by_task[record["task_id"]].append(record)

    tasks = []
    for task in manifest.tasks:
        orient = orients[task.task_id]
        side_of = {writer: side for side, writer in orient.items()}
        records = by_task.get(task.task_id, [])
        votes: Counter[str] = Counter()
        for record in records:
            if record["failed"]:
                votes["failed"] += 1
            else:
                votes[orient.get(record["preferred"], record["preferred"])] += 1
        if votes[first] != votes[second]:
            outcome = first if votes[first] > votes[second] else second
        else:
            outcome = "tie" if votes[first] + votes["tie"] else "no verdict"
        tasks.append(
            {
                "task_id": task.task_id,
                "level": task.level,
                "sides": {label: side_of[label] for label in labels},
                "votes": {k: votes.get(k, 0) for k in (first, second, "tie", "abstain", "failed")},
                "outcome": outcome,
                "values": {label: _text_values(mech, records, human, task.task_id, side_of[label]) for label in labels},
                "mechanical_failed": [
                    side for side in SIDES if mech.get((task.task_id, side), {"failed": True})["failed"]
                ],
            }
        )

    outcomes = Counter(t["outcome"] for t in tasks)
    wins, losses = outcomes.get(first, 0), outcomes.get(second, 0)
    metrics = {}
    metric_names = (*MECHANICAL_METRICS, *JUDGE_METRICS, *(("human_score",) if human else ()))
    for index, metric in enumerate(metric_names):
        pairs = [
            (t["values"][first][metric], t["values"][second][metric])
            for t in tasks
            if t["values"][first][metric] is not None and t["values"][second][metric] is not None
        ]
        if not pairs:
            metrics[metric] = {"tasks": 0}
            continue
        matrix = np.array(pairs, dtype=float)
        point, low, high = bootstrap_paired(
            matrix, lambda m: float(np.mean(m[:, 0] - m[:, 1])), iterations, seed + index
        )
        metrics[metric] = {
            "tasks": len(pairs),
            first: float(matrix[:, 0].mean()),
            second: float(matrix[:, 1].mean()),
            "difference": point,
            "ci95": [low, high],
        }

    human_pairs = [
        (statistics.fmean(ratings), t["values"][label]["judge_score"])
        for t in tasks
        for label in labels
        if (ratings := human.get((t["task_id"], t["sides"][label]))) and t["values"][label]["judge_score"] is not None
    ]
    writer_families = set(manifest.writer_families) | (set(key["writers"].values()) if key else set())
    judge_families = sorted({r["judge_family"] for r in judgements})
    return {
        "evaluation_id": manifest.evaluation_id,
        "label": f"exploratory: {len(tasks)} tasks",
        "blinded": key is None,
        "labels": labels,
        "orientation": "blind labels A/B (per task only; not writer identities)"
        if key is None
        else f"writers {first} vs {second} (difference = {first} - {second})",
        "provenance": {
            "outputs": "imported: generated outside this harness; no execution attestation, file digests only",
            "note": manifest.provenance,
            "manifest_sha256": manifest.sha256,
            "key_sha256": key["sha256"] if key else None,
            "key_commitment": key["commitment"] if key else None,
            "frozen": frozen,
        },
        "families": {
            "writers": sorted(writer_families),
            "judges": judge_families,
            "violations": sorted(writer_families & set(judge_families)),
            "key_families_outside_manifest": sorted(set(key["writers"].values()) - set(manifest.writer_families))
            if key
            else [],
        },
        "totals": {
            "wins": wins,
            "ties": outcomes.get("tie", 0),
            "losses": losses,
            "no_verdict": outcomes.get("no verdict", 0),
            "sign_test_p": sign_test(wins, losses),
        },
        "tasks": tasks,
        "metrics": metrics,
        "judges": _judge_agreement(judgements, judges, orients),
        "human": {
            "texts_rated": sum(1 for ratings in human.values() if ratings),
            "pearson_with_judge_score": pearson([h for h, _ in human_pairs], [j for _, j in human_pairs]),
            "pairs": len(human_pairs),
        },
    }


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return "—" if math.isnan(value) else f"{value:.{digits}f}"
    return str(value)


def render_markdown(report: dict[str, Any]) -> str:
    first, second = report["labels"]
    totals, prov, fam = report["totals"], report["provenance"], report["families"]
    lines = [
        f"# Lesson-section A/B: {report['evaluation_id']}",
        "",
        f"**{report['label'].capitalize()}.** Orientation: {report['orientation']}.",
        "",
        f"- Outputs: {prov['outputs']}. Note: {prov['note']}.",
        f"- Manifest SHA-256: `{prov['manifest_sha256']}`.",
        f"- Key: {'not read (blinded)' if report['blinded'] else prov['key_commitment'] + ', `' + prov['key_sha256'] + '`'}.",
        f"- Writer families: {', '.join(fam['writers'])}; judge families: {', '.join(fam['judges']) or 'none'}"
        + (f"; **FAMILY VIOLATION: {', '.join(fam['violations'])}**" if fam["violations"] else "")
        + (
            f"; **key families not declared in the manifest: {', '.join(fam['key_families_outside_manifest'])}**"
            if fam["key_families_outside_manifest"]
            else ""
        )
        + ".",
        "",
        f"## Result: {first} {totals['wins']} wins, {totals['ties']} ties, {totals['losses']} losses"
        f" ({totals['no_verdict']} without verdict); sign test p = {_fmt(totals['sign_test_p'], 3)}",
        "",
        f"| Task | Level | {first} | {second} | Votes {first}/{second}/tie/abstain/failed | Outcome |"
        f" Judge score {first} | Judge score {second} |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for task in report["tasks"]:
        v = task["votes"]
        lines.append(
            f"| {task['task_id']} | {task['level']} | {task['sides'][first]} | {task['sides'][second]} |"
            f" {v[first]}/{v[second]}/{v['tie']}/{v['abstain']}/{v['failed']} | {task['outcome']} |"
            f" {_fmt(task['values'][first]['judge_score'])} | {_fmt(task['values'][second]['judge_score'])} |"
        )
    lines += [
        "",
        f"## Metrics (paired over tasks; difference = {first} - {second}, bootstrap 95% CI)",
        "",
        f"| Metric | Tasks | {first} | {second} | Difference | 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    for name, metric in report["metrics"].items():
        if not metric["tasks"]:
            lines.append(f"| {name} | 0 | — | — | — | — |")
            continue
        low, high = metric["ci95"]
        lines.append(
            f"| {name} | {metric['tasks']} | {_fmt(metric[first])} | {_fmt(metric[second])} |"
            f" {_fmt(metric['difference'])} | [{_fmt(low)}, {_fmt(high)}] |"
        )
    lines += [
        "",
        "## Mechanical findings per text",
        "",
        "| Task | Side | VESUM-invalid | Capitalised only | Calques | Above level | Wrong stress | Unverified stress | Ambiguous stress |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for task in report["tasks"]:
        for label in (first, second):
            values = task["values"][label]
            lines.append(
                f"| {task['task_id']} | {label} | {_fmt(values['vesum_invalid'])} |"
                f" {_fmt(values['vesum_capitalised'])} | {_fmt(values['calque_hits'])} |"
                f" {_fmt(values['cefr_above_level'])} | {_fmt(values['stress_wrong'])} |"
                f" {_fmt(values['stress_unverified'])} | {_fmt(values['stress_ambiguous_unresolved'])} |"
            )
        if task["mechanical_failed"]:
            lines.append(f"| {task['task_id']} | failed: {', '.join(task['mechanical_failed'])} | | | | | | | |")
    lines += [
        "",
        "## Judges",
        "",
        "| Judge | Judgements | Failed | Abstained | Decided both orders | Position-inconsistent |"
        " Position consistency | Text 1 preferred |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for judge, stats in report["judges"]["per_judge"].items():
        lines.append(
            f"| {judge} | {stats['judgements']} | {stats['failed']} | {stats['abstained']} |"
            f" {stats['tasks_decided_both_orders']} | {stats['position_inconsistent']} |"
            f" {_fmt(stats['position_consistency'])} | {_fmt(stats['first_position_preferred'])} |"
        )
    for pair in report["judges"]["pairs"]:
        lines.append(
            f"\nAgreement {pair['judges'][0]} vs {pair['judges'][1]}: {_fmt(pair['agreement'])} over"
            f" {pair['tasks']} tasks, kappa {_fmt(pair['kappa'])}; score Pearson {_fmt(pair['score_pearson'])}"
            f" over {pair['texts_scored_by_both']} texts."
        )
    human = report["human"]
    lines += [
        "",
        "## Native-expert ratings (calibration slot)",
        "",
        f"Texts rated: {human['texts_rated']}; Pearson with the mean judge score: "
        f"{_fmt(human['pearson_with_judge_score'])} over {human['pairs']} texts.",
        "",
    ]
    return "\n".join(lines)
