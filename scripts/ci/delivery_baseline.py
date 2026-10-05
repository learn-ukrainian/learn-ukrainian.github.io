"""Evaluate a frozen before/after delivery cohort against the baseline specification.

Pure and offline: the input is an authored JSON cohort (canonical field values
already extracted), the output is a JSON verdict. Nothing here reads task
records, GitHub or Fleet stores. The rules implement
docs/design/agent-friendly-delivery-baseline.md (#9738):

- a span counts only when both endpoints come from a registered canonical
  field pair; anything else (file mtimes, chat, missing endpoint) is unknown;
- unknown is ``None`` with a reason, never zero and never qualified;
- concurrent spans are never summed: each metric reports the union of its
  intervals plus the per-span durations;
- a record is delivered only with linked outcome, exact-head independent
  review of record, merge and cleanup evidence;
- a comparison is reported per stratum and metric only when each arm has at
  least five delivered records, every one with a qualified value and matched
  setup; otherwise it is ``inconclusive``. Strata are never pooled.

    .venv/bin/python -m scripts.ci.delivery_baseline cohort.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "delivery-baseline-input.v1"
ARMS = ("before", "after")
STRATA = (
    "launcher_repair",
    "provider_runtime_failure",
    "routine_product_change",
    "architecture_change",
    "ukrainian_content",
    "long_epic_resume",
)
STAGES = (
    "intake",
    "onboarding",
    "capacity",
    "authoring",
    "verification_review",
    "ci_landing",
    "recovery_closeout",
)
KINDS = ("worker_wall", "check_wall", "queue_delay", "elapsed")
MIN_DELIVERED_PER_ARM = 5

# (stage, kind) -> admissible (start_field, end_field) pairs. Onboarding and
# capacity have no canonical paired fields, so they are absent: unqualified.
CANONICAL_SPANS: dict[tuple[str, str], frozenset[tuple[str, str]]] = {
    ("intake", "elapsed"): frozenset({("github.issue.createdAt", "task.started_at")}),
    ("authoring", "worker_wall"): frozenset({("task.started_at", "task.finished_at")}),
    ("verification_review", "worker_wall"): frozenset({("review_task.started_at", "review_task.finished_at")}),
    ("verification_review", "elapsed"): frozenset(
        {("fleet.formal_review_jobs.created_at", "fleet.github_publications.published_at")}
    ),
    ("ci_landing", "check_wall"): frozenset({("github.check_run.startedAt", "github.check_run.completedAt")}),
    ("ci_landing", "queue_delay"): frozenset(
        {
            ("github.actions_job.created_at", "github.actions_job.started_at"),
            ("github.timeline.AddedToMergeQueueEvent.createdAt", "github.pr.mergedAt"),
        }
    ),
    ("ci_landing", "elapsed"): frozenset(
        {
            ("github.pr.createdAt", "github.pr.mergedAt"),
            ("fleet.github_publications.published_at", "github.pr.mergedAt"),
        }
    ),
    ("recovery_closeout", "elapsed"): frozenset(
        {
            ("failed_task.finished_at", "retry_task.started_at"),
            ("github.pr.mergedAt", "lifecycle.observation_receipts.observed_at"),
        }
    ),
}
UNQUALIFIED_STAGES = frozenset(stage for stage in STAGES if not any(key[0] == stage for key in CANONICAL_SPANS))


class CohortError(ValueError):
    """The cohort input is malformed; no verdict is produced."""


def _timestamp(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _span_value(span: Mapping[str, Any]) -> tuple[tuple[datetime, datetime] | None, str | None]:
    """Return the interval, or None with the reason it is unknown."""
    key = (span.get("stage"), span.get("kind"))
    fields = (span.get("start_field"), span.get("end_field"))
    if fields not in CANONICAL_SPANS.get(key, frozenset()):
        return None, "non_canonical_source"
    start, end = _timestamp(span.get("start")), _timestamp(span.get("end"))
    if start is None or end is None:
        return None, "missing_endpoint"
    if end < start:
        return None, "negative_interval"
    return (start, end), None


def union_seconds(intervals: Sequence[tuple[datetime, datetime]]) -> float:
    """Length of the union of intervals: overlapping time is counted once."""
    total = 0.0
    current: tuple[datetime, datetime] | None = None
    for start, end in sorted(intervals):
        if current is None or start > current[1]:
            if current is not None:
                total += (current[1] - current[0]).total_seconds()
            current = (start, end)
        else:
            current = (current[0], max(current[1], end))
    if current is not None:
        total += (current[1] - current[0]).total_seconds()
    return total


def delivery_status(record: Mapping[str, Any]) -> list[str]:
    """Reasons a record is not delivered; an empty list means delivered."""
    reasons: list[str] = []
    outcome = record.get("outcome") or {}
    if not isinstance(outcome.get("issue"), int) or not isinstance(outcome.get("pr"), int):
        reasons.append("unlinked_outcome")
    merge = record.get("merge") or {}
    if _timestamp(merge.get("merged_at")) is None or not merge.get("head_sha"):
        reasons.append("not_merged")
    review = record.get("review_of_record") or {}
    if review.get("verdict") != "APPROVE" or not review.get("head_sha"):
        reasons.append("no_review_of_record")
    elif not review.get("reviewer_family") or review.get("reviewer_family") == review.get("author_family"):
        reasons.append("review_not_independent")
    elif merge.get("head_sha") and review.get("head_sha") != merge.get("head_sha"):
        reasons.append("review_not_exact_head")
    cleanup = record.get("cleanup") or {}
    if cleanup.get("state") != "CLEANED_UP" or _timestamp(cleanup.get("observed_at")) is None:
        reasons.append("no_cleanup_evidence")
    return reasons


def record_metrics(record: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Per stage.kind metric: qualified union seconds, or unknown/unqualified."""
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for span in record.get("spans") or []:
        if span.get("stage") not in STAGES or span.get("kind") not in KINDS:
            raise CohortError(f"record {record.get('task_id')!r}: unknown stage or kind in span")
        grouped.setdefault(f"{span['stage']}.{span['kind']}", []).append(span)
    metrics: dict[str, dict[str, Any]] = {}
    for name, spans in sorted(grouped.items()):
        stage = name.split(".", 1)[0]
        if stage in UNQUALIFIED_STAGES:
            metrics[name] = {"status": "unqualified", "union_s": None, "spans_s": [], "reasons": ["no_canonical_field"]}
            continue
        intervals, durations, reasons = [], [], []
        for span in spans:
            interval, reason = _span_value(span)
            if interval is None:
                reasons.append(reason)
                durations.append(None)
            else:
                intervals.append(interval)
                durations.append((interval[1] - interval[0]).total_seconds())
        if reasons:
            metrics[name] = {
                "status": "unknown",
                "union_s": None,
                "spans_s": durations,
                "reasons": sorted(set(reasons)),
            }
        else:
            metrics[name] = {
                "status": "qualified",
                "union_s": union_seconds(intervals),
                "spans_s": durations,
                "reasons": [],
            }
    return metrics


def _distribution(values: list[float]) -> dict[str, float | int]:
    return {"n": len(values), "min": min(values), "median": statistics.median(values), "max": max(values)}


def _compare(delivered: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    names = sorted({name for arm in ARMS for item in delivered[arm] for name in item["metrics"]})
    setups = {arm: {json.dumps(item["setup"], sort_keys=True) for item in delivered[arm]} for arm in ARMS}
    result: dict[str, dict[str, Any]] = {}
    for name in names:
        reasons = []
        if any(len(delivered[arm]) < MIN_DELIVERED_PER_ARM for arm in ARMS):
            reasons.append("fewer_than_five_delivered_in_stratum")
        if len(setups["before"] | setups["after"]) > 1:
            reasons.append("incomparable_setup")
        values: dict[str, list[float]] = {arm: [] for arm in ARMS}
        for arm in ARMS:
            for item in delivered[arm]:
                metric = item["metrics"].get(name)
                if metric is None or metric["status"] != "qualified":
                    status = "missing" if metric is None else metric["status"]
                    reasons.append(f"{status}_value_in_{arm}")
                else:
                    values[arm].append(metric["union_s"])
        reasons = sorted(set(reasons))
        if reasons:
            result[name] = {"verdict": "inconclusive", "reasons": reasons}
        else:
            result[name] = {"verdict": "reportable", "reasons": [], **{arm: _distribution(values[arm]) for arm in ARMS}}
    return result


def evaluate(cohort: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate a cohort document; raises CohortError on malformed input."""
    if cohort.get("schema_version") != SCHEMA_VERSION:
        raise CohortError(f"schema_version must be {SCHEMA_VERSION}")
    records = cohort.get("records")
    if not isinstance(records, list):
        raise CohortError("records must be a list")
    evaluated = []
    seen: set[str] = set()
    for record in records:
        task_id = record.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in seen:
            raise CohortError(f"task_id missing or duplicated: {task_id!r}")
        seen.add(task_id)
        if record.get("arm") not in ARMS:
            raise CohortError(f"record {task_id!r}: arm must be one of {ARMS}")
        item: dict[str, Any] = {
            "task_id": task_id,
            "arm": record["arm"],
            "stratum": record.get("stratum"),
            "setup": record.get("matched_setup") or {},
            "metrics": record_metrics(record),
        }
        if record.get("exclusion"):
            item["disposition"], item["reasons"] = "excluded", [str(record["exclusion"])]
        elif record.get("stratum") not in STRATA:
            item["disposition"], item["reasons"] = "excluded", ["outside_frozen_strata"]
        else:
            reasons = delivery_status(record)
            item["disposition"], item["reasons"] = ("not_delivered", reasons) if reasons else ("delivered", [])
        evaluated.append(item)

    strata: dict[str, Any] = {}
    for stratum in STRATA:
        members = [item for item in evaluated if item["stratum"] == stratum and item["disposition"] != "excluded"]
        delivered = {arm: [m for m in members if m["arm"] == arm and m["disposition"] == "delivered"] for arm in ARMS}
        denominators = {}
        for arm in ARMS:
            not_delivered: dict[str, int] = {}
            for member in members:
                if member["arm"] == arm and member["disposition"] == "not_delivered":
                    for reason in member["reasons"]:
                        not_delivered[reason] = not_delivered.get(reason, 0) + 1
            denominators[arm] = {
                "members": sum(1 for m in members if m["arm"] == arm),
                "delivered": len(delivered[arm]),
                "not_delivered_reasons": dict(sorted(not_delivered.items())),
            }
        metrics = _compare(delivered)
        floor_met = all(len(delivered[arm]) >= MIN_DELIVERED_PER_ARM for arm in ARMS)
        reportable = floor_met and any(m["verdict"] == "reportable" for m in metrics.values())
        strata[stratum] = {
            "verdict": "reportable" if reportable else "inconclusive",
            "floor_met": floor_met,
            "denominators": denominators,
            "metrics": metrics,
        }

    claims = []
    for claim in cohort.get("claims") or []:
        stratum, metric = claim.get("stratum"), claim.get("metric")
        if stratum not in STRATA:
            status, reason = "rejected", "not_a_single_frozen_stratum"
        elif strata[stratum]["metrics"].get(metric, {}).get("verdict") != "reportable":
            status, reason = "rejected", "comparison_inconclusive"
        else:
            status, reason = "admissible", "reportable_distribution_only_not_significance"
        claims.append({"stratum": stratum, "metric": metric, "status": status, "reason": reason})

    canonical = json.dumps(cohort, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "delivery-baseline-report.v1",
        "input_sha256": hashlib.sha256(canonical).hexdigest(),
        "min_delivered_per_arm": MIN_DELIVERED_PER_ARM,
        "records": evaluated,
        "excluded": sorted(item["task_id"] for item in evaluated if item["disposition"] == "excluded"),
        "strata": strata,
        "claims": claims,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a frozen delivery cohort (offline, no network).")
    parser.add_argument("cohort", type=Path, help="cohort JSON (schema delivery-baseline-input.v1)")
    args = parser.parse_args(argv)
    try:
        report = evaluate(json.loads(args.cohort.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, CohortError) as exc:
        print(f"delivery_baseline: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
