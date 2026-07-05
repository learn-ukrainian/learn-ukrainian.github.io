#!/usr/bin/env python3
"""Aggregate stored QG evidence without live reviewer calls.

The report is deliberately DB/file-backed: it reads persisted ``llm_qg_runs``
rows plus optional stored ``qg_workflow.py --format json`` outputs. It never
dispatches a reviewer.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.api.resilience import connect_sqlite
from scripts.audit import llm_qg_store, llm_reviewer, qg_schema, qg_workflow
from scripts.audit.content_surface_gates import policy_for_level
from scripts.audit.curriculum_qg_harness import CHECKER_VERSION

REPORT_SCHEMA_VERSION = "qg_corpus_report.v1"
UNLP_METRIC_SCHEMA_VERSION = "unlp_qg_aggregate_metrics.v1"
COMPOSITE_KEY_FIELDS = (
    "level",
    "slug",
    "content_sha",
    "gate_version",
    "prompt_hash",
    "checker_version",
    "level_policy_family",
    "reviewer_model",
)

@dataclass(frozen=True, slots=True)
class ReportTarget:
    level: str
    slug: str
    module_dir: Path


@dataclass(frozen=True, slots=True)
class ReportRecord:
    run_id: str
    level: str
    slug: str
    content_sha: str
    gate_version: str
    prompt_hash: str | None
    checker_version: str | None
    level_policy_family: str | None
    reviewer_model: str | None
    reviewer_family: str | None
    source: str
    payload: dict[str, Any]
    created_at: str

    @property
    def module_id(self) -> str:
        return f"{self.level}/{self.slug}"


def build_report(
    *,
    db_path: Path | None = None,
    targets: Sequence[ReportTarget] = (),
    workflow_payloads: Sequence[Mapping[str, Any] | Sequence[Mapping[str, Any]]] = (),
    gate_version: str = qg_workflow.DEFAULT_GATE_VERSION,
    checker_version: str = CHECKER_VERSION,
    reviewer_model_id: str = qg_workflow.DEFAULT_REVIEWER_MODEL_ID,
) -> dict[str, Any]:
    """Build the corpus report from stored DB rows and optional workflow JSON."""

    resolved_db = llm_qg_store.db_path(db_path)
    raw_records, load_errors = load_db_records(resolved_db)
    latest_records = latest_records_by_composite(raw_records)
    workflow_records = _flatten_workflow_payloads(workflow_payloads)
    cache = cache_status_for_targets(
        targets,
        db_path=resolved_db,
        gate_version=gate_version,
        checker_version=checker_version,
        reviewer_model_id=reviewer_model_id,
    )

    defect_rates = _defect_rates(latest_records, workflow_records)
    gold_metrics = _gold_metrics(latest_records, workflow_records)
    completion = _completion_summary(latest_records, workflow_records)
    warn_conversion = _warn_conversion(workflow_records)
    spend = _spend_summary(latest_records, workflow_records)

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": _now_z(),
        "source": {
            "db": str(resolved_db),
            "db_exists": resolved_db.exists(),
            "workflow_records": len(workflow_records),
            "target_count": len(targets),
            "gate_version": gate_version,
            "checker_version": checker_version,
            "reviewer_model_id": reviewer_model_id,
        },
        "selection": {
            "dedupe_key": list(COMPOSITE_KEY_FIELDS),
            "latest_order": ["created_at DESC", "run_id DESC"],
            "raw_db_rows": len(raw_records),
            "latest_composite_records": len(latest_records),
            "load_errors": load_errors,
        },
        "cache": cache,
        "defect_rates": defect_rates,
        "gold_metrics": gold_metrics,
        "warn_to_reviewer_confirmed": warn_conversion,
        "completion": completion,
        "spend": spend,
        "unlp_metric_schema": unlp_metric_schema(),
    }


def load_db_records(path: Path) -> tuple[list[ReportRecord], list[str]]:
    """Return all persisted DB records; malformed payloads are reported, not fatal."""

    if not path.exists():
        return [], []
    errors: list[str] = []
    records: list[ReportRecord] = []
    try:
        with closing(connect_sqlite(str(path))) as conn:
            llm_qg_store._ensure_composite_columns(conn)
            conn.commit()
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM llm_qg_runs
                ORDER BY created_at DESC, run_id DESC
                """
            ).fetchall()
    except sqlite3.DatabaseError as exc:
        return [], [f"db_error: {exc}"]

    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"]))
        except json.JSONDecodeError as exc:
            errors.append(f"{row['run_id']}: payload_json: {exc}")
            continue
        records.append(
            ReportRecord(
                run_id=str(row["run_id"]),
                level=str(row["level"]),
                slug=str(row["slug"]),
                content_sha=str(row["content_sha"]),
                gate_version=str(row["gate_version"]),
                prompt_hash=row["prompt_hash"],
                checker_version=row["checker_version"],
                level_policy_family=row["level_policy_family"],
                reviewer_model=row["reviewer_model"],
                reviewer_family=row["reviewer_family"],
                source=str(row["source"]),
                payload=payload,
                created_at=str(row["created_at"]),
            )
        )
    return records, errors


def latest_records_by_composite(records: Iterable[ReportRecord]) -> list[ReportRecord]:
    """Keep the newest row per composite identity; row growth is not a signal."""

    latest: dict[tuple[Any, ...], ReportRecord] = {}
    for record in records:
        key = _composite_key(record)
        current = latest.get(key)
        if current is None or (record.created_at, record.run_id) > (current.created_at, current.run_id):
            latest[key] = record
    return sorted(latest.values(), key=lambda item: (item.level, item.slug, item.reviewer_model or "", item.created_at))


def cache_status_for_targets(
    targets: Sequence[ReportTarget],
    *,
    db_path: Path,
    gate_version: str,
    checker_version: str,
    reviewer_model_id: str,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    by_level: dict[str, Counter[str]] = defaultdict(Counter)
    modules: list[dict[str, Any]] = []
    raw_records, _errors = load_db_records(db_path)
    latest_by_composite = {_composite_key(record): record for record in latest_records_by_composite(raw_records)}
    modules_with_any_record = {(record.level, record.slug) for record in raw_records}
    for target in targets:
        clean_level = target.level.strip().lower()
        clean_slug = target.slug.strip()
        key = _target_composite_key(
            target=target,
            gate_version=gate_version,
            checker_version=checker_version,
            reviewer_model_id=reviewer_model_id,
        )
        record = latest_by_composite.get(key)
        status = "hit" if record else "stale" if (clean_level, clean_slug) in modules_with_any_record else "miss"
        counts[status] += 1
        by_level[clean_level][status] += 1
        modules.append(
            {
                "module_id": f"{clean_level}/{clean_slug}",
                "status": status,
                "run_id": record.run_id if record else None,
                "gate_version": record.gate_version if record else None,
                "reviewer_model": record.reviewer_model if record else None,
            }
        )
    return {
        "hit": counts["hit"],
        "stale": counts["stale"],
        "miss": counts["miss"],
        "by_level": {
            level: {"hit": values["hit"], "stale": values["stale"], "miss": values["miss"]}
            for level, values in sorted(by_level.items())
        },
        "modules": modules,
    }


def latest_composite_match_for_target(
    target: ReportTarget,
    *,
    db_path: Path,
    gate_version: str,
    checker_version: str,
    reviewer_model_id: str,
) -> tuple[str, ReportRecord | None]:
    """Return hit/stale/miss using the full workflow cache composite."""

    if not db_path.exists():
        return "miss", None
    clean_level = target.level.strip().lower()
    clean_slug = target.slug.strip()
    prompt_hash = _prompt_hash_for_target(target)
    content_sha = llm_qg_store.content_sha_for_module(target.module_dir)
    policy_family = policy_for_level(clean_level).family
    record = _latest_exact_composite(
        db_path=db_path,
        level=clean_level,
        slug=clean_slug,
        content_sha=content_sha,
        gate_version=gate_version,
        prompt_hash=prompt_hash,
        checker_version=checker_version,
        level_policy_family=policy_family,
        reviewer_model=reviewer_model_id,
    )
    if record is not None:
        return "hit", record
    latest, _errors = load_db_records(db_path)
    stale = any(record.level == clean_level and record.slug == clean_slug for record in latest)
    return ("stale" if stale else "miss"), None


def _target_composite_key(
    *,
    target: ReportTarget,
    gate_version: str,
    checker_version: str,
    reviewer_model_id: str,
) -> tuple[Any, ...]:
    clean_level = target.level.strip().lower()
    return (
        clean_level,
        target.slug.strip(),
        llm_qg_store.content_sha_for_module(target.module_dir),
        gate_version,
        _prompt_hash_for_target(target),
        checker_version,
        _norm_str(policy_for_level(clean_level).family),
        _norm_str(reviewer_model_id),
    )


def backfill_from_workflow_records(
    workflow_payloads: Sequence[Mapping[str, Any] | Sequence[Mapping[str, Any]]],
    *,
    db_path: Path | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Insert missing/stale stored workflow evidence without overwriting matches."""

    resolved_db = llm_qg_store.db_path(db_path)
    records = _flatten_workflow_payloads(workflow_payloads)
    counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for record in records:
        decision = _backfill_decision(record, resolved_db)
        status = str(decision["status"])
        if status in {"missing", "stale"} and not dry_run:
            module_dir = Path(str(record["provenance"]["module_dir"]))
            llm_qg_store.record_llm_qg(
                level=str(record["module_id"]).split("/", 1)[0],
                slug=str(record["module_id"]).split("/", 1)[1],
                module_dir=module_dir,
                payload=_payload_from_workflow_record(record),
                gate_version=str(record["qg_workflow"]["gate_version"]),
                prompt_hash=record["qg_workflow"].get("prompt_hash"),
                checker_version=record["qg_workflow"].get("checker_version"),
                level_policy_family=str(record["level_policy"].get("family") or ""),
                reviewer_model=str(record["qg_workflow"].get("reviewer_model_id") or ""),
                reviewer_family=record["qg_workflow"].get("reviewer_family"),
                source="qg_corpus_report_backfill",
                path=resolved_db,
            )
            status = "inserted"
        counts[status] += 1
        rows.append({**decision, "status": status})
    return {
        "schema_version": "qg_corpus_backfill.v1",
        "dry_run": dry_run,
        "db": str(resolved_db),
        "counts": dict(sorted(counts.items())),
        "records": rows,
    }


def discover_targets(curriculum_root: Path) -> list[ReportTarget]:
    """Discover built module directories under ``curriculum/l2-uk-en``."""

    targets: list[ReportTarget] = []
    if not curriculum_root.exists():
        return targets
    for level_dir in sorted(path for path in curriculum_root.iterdir() if path.is_dir()):
        level = level_dir.name
        for module_md in sorted(level_dir.glob("*/module.md")):
            module_dir = module_md.parent
            targets.append(ReportTarget(level=level, slug=module_dir.name, module_dir=module_dir))
    return targets


def load_workflow_json(path: Path) -> Mapping[str, Any] | Sequence[Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise ValueError(f"{path}: expected workflow record object or list")


def unlp_metric_schema() -> dict[str, Any]:
    """Machine-readable aggregate schema stub for #4312."""

    return {
        "schema_version": UNLP_METRIC_SCHEMA_VERSION,
        "required_aggregates": [
            "gold_metrics.calque.with_contested",
            "gold_metrics.calque.without_contested",
            "gold_metrics.calque.contested_delta",
            "defect_rates.by_level",
            "gold_metrics.per_model_calque_f1",
        ],
        "metric_fields": {
            "precision": "tp / (tp + fp), null when denominator is zero",
            "recall": "tp / (tp + fn), null when denominator is zero",
            "f1": "harmonic mean of precision and recall, null when both are unavailable or zero",
            "contested_delta": "with_contested minus without_contested for precision/recall/f1",
        },
        "identity_fields": list(COMPOSITE_KEY_FIELDS),
    }


def _norm_str(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _latest_exact_composite(
    *,
    db_path: Path,
    level: str,
    slug: str,
    content_sha: str,
    gate_version: str,
    prompt_hash: str | None,
    checker_version: str | None,
    level_policy_family: str | None,
    reviewer_model: str | None,
) -> ReportRecord | None:
    rows, errors = load_db_records(db_path)
    if errors:
        return None
    wanted = (
        level.strip().lower(),
        slug.strip(),
        content_sha,
        gate_version,
        prompt_hash,
        checker_version,
        _norm_str(level_policy_family),
        _norm_str(reviewer_model),
    )
    matches = [record for record in rows if _composite_key(record) == wanted]
    if not matches:
        return None
    return max(matches, key=lambda item: (item.created_at, item.run_id))


def _backfill_decision(record: Mapping[str, Any], db_path: Path) -> dict[str, Any]:
    module_id = str(record.get("module_id") or "")
    if "/" not in module_id:
        return {"module_id": module_id, "status": "invalid", "reason": "missing module_id"}
    workflow = record.get("qg_workflow")
    provenance = record.get("provenance")
    level_policy = record.get("level_policy")
    if not isinstance(workflow, Mapping) or not isinstance(provenance, Mapping) or not isinstance(level_policy, Mapping):
        return {"module_id": module_id, "status": "invalid", "reason": "missing workflow metadata"}
    module_dir = Path(str(provenance.get("module_dir") or ""))
    if not module_dir.exists():
        return {"module_id": module_id, "status": "invalid", "reason": "module_dir missing"}
    current_content_sha = llm_qg_store.content_sha_for_module(module_dir)
    record_content_sha = str(record.get("content_sha") or "")
    if record_content_sha != current_content_sha:
        return {"module_id": module_id, "status": "stale_source", "reason": "content_sha differs from module_dir"}
    level, slug = module_id.split("/", 1)
    exact = _latest_exact_composite(
        db_path=db_path,
        level=level,
        slug=slug,
        content_sha=record_content_sha,
        gate_version=str(workflow.get("gate_version") or ""),
        prompt_hash=workflow.get("prompt_hash"),
        checker_version=workflow.get("checker_version"),
        level_policy_family=level_policy.get("family"),
        reviewer_model=workflow.get("reviewer_model_id"),
    )
    if exact is not None:
        return {"module_id": module_id, "status": "current", "run_id": exact.run_id}
    rows, _errors = load_db_records(db_path)
    stale = any(item.level == level.strip().lower() and item.slug == slug.strip() for item in rows)
    return {"module_id": module_id, "status": "stale" if stale else "missing"}


def _payload_from_workflow_record(record: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": record.get("schema_version", qg_schema.SCHEMA_VERSION),
        "aggregate": dict(record.get("aggregate") if isinstance(record.get("aggregate"), Mapping) else {}),
        "dimensions": dict(record.get("dimensions") if isinstance(record.get("dimensions"), Mapping) else {}),
        "findings": _findings_from_payload(record),
    }


def _defect_rates(
    db_records: Sequence[ReportRecord],
    workflow_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = defaultdict(_empty_defect_bucket)
    policy_buckets: dict[str, dict[str, Any]] = defaultdict(_empty_defect_bucket)
    overall = _empty_defect_bucket()
    for record in [*_records_as_mappings(db_records), *workflow_records]:
        level = _level_for_record(record)
        policy = _policy_family_for_record(record)
        findings = _penalized_findings(_findings_from_payload(record))
        _add_defect_record(overall, findings)
        _add_defect_record(buckets[level], findings)
        _add_defect_record(policy_buckets[policy], findings)
    return {
        "overall": _finalize_defect_bucket(overall),
        "by_level": {key: _finalize_defect_bucket(value) for key, value in sorted(buckets.items())},
        "by_policy_family": {key: _finalize_defect_bucket(value) for key, value in sorted(policy_buckets.items())},
    }


def _gold_metrics(
    db_records: Sequence[ReportRecord],
    workflow_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    axes = {"calque": [], "grammar": []}
    per_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in [*_records_as_mappings(db_records), *workflow_records]:
        model = _reviewer_model_for_record(record)
        for finding in _findings_from_payload(record):
            vote = _metric_vote(finding)
            if vote is None:
                continue
            if vote["axis"] in axes:
                axes[vote["axis"]].append(vote)
            if vote["axis"] == "calque":
                per_model[model].append(vote)

    calque_with = _score_votes(axes["calque"], include_contested=True)
    calque_without = _score_votes(axes["calque"], include_contested=False)
    grammar_with = _score_votes(axes["grammar"], include_contested=True)
    grammar_without = _score_votes(axes["grammar"], include_contested=False)
    return {
        "calque": {
            "with_contested": calque_with,
            "without_contested": calque_without,
            "contested_delta": _metric_delta(calque_with, calque_without),
        },
        "grammar": {
            "with_contested": grammar_with,
            "without_contested": grammar_without,
            "contested_delta": _metric_delta(grammar_with, grammar_without),
        },
        "per_model_calque_f1": {
            model: {
                "with_contested": _score_votes(votes, include_contested=True),
                "without_contested": _score_votes(votes, include_contested=False),
            }
            for model, votes in sorted(per_model.items())
        },
    }


def _completion_summary(
    db_records: Sequence[ReportRecord],
    workflow_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    completion_counts: Counter[str] = Counter()
    workflow_verdict_counts: Counter[str] = Counter()
    tier2_status_counts: Counter[str] = Counter()
    cache_regate_counts: Counter[str] = Counter()
    provider_error = 0
    parse_failure = 0
    skipped_budget = 0
    incomplete = 0
    for record in [*_records_as_mappings(db_records), *workflow_records]:
        aggregate = _aggregate(record)
        completion = str(record.get("completion_status") or aggregate.get("completion_status") or "COMPLETE")
        workflow_verdict = str(record.get("workflow_verdict") or aggregate.get("workflow_verdict") or aggregate.get("verdict") or "UNKNOWN")
        completion_counts[completion] += 1
        workflow_verdict_counts[workflow_verdict] += 1
        if completion == "INCOMPLETE":
            incomplete += 1
        if workflow_verdict == "SKIPPED_BUDGET":
            skipped_budget += 1
        tier2 = _tier(record, 2)
        status = str(tier2.get("status") or "")
        if status:
            tier2_status_counts[status] += 1
        cache_regate = str(tier2.get("cache_regate") or "")
        if cache_regate:
            cache_regate_counts[cache_regate] += 1
        if status == "provider_error" or workflow_verdict == "PROVIDER_FAILURE":
            provider_error += 1
        if status in {"parse_failure", "schema_failure"} or workflow_verdict in {"PARSE_FAILURE", "SCHEMA_FAILURE"}:
            parse_failure += 1
    return {
        "records": len(db_records) + len(workflow_records),
        "completion_status_counts": dict(sorted(completion_counts.items())),
        "workflow_verdict_counts": dict(sorted(workflow_verdict_counts.items())),
        "tier2_status_counts": dict(sorted(tier2_status_counts.items())),
        "cache_regate_counts": dict(sorted(cache_regate_counts.items())),
        "skipped_budget": skipped_budget,
        "incomplete": incomplete,
        "provider_error": provider_error,
        "parse_failure": parse_failure,
    }


def _warn_conversion(workflow_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    warn_findings = 0
    confirmed = 0
    for record in workflow_records:
        findings = _findings_from_payload(record)
        reviewer_findings = [item for item in findings if item.get("confidence") == "llm_judgment"]
        for finding in findings:
            if finding.get("confidence") == "llm_judgment" or finding.get("severity") != "warning":
                continue
            warn_findings += 1
            if _reviewer_confirms(finding, reviewer_findings):
                confirmed += 1
    return {
        "warn_findings": warn_findings,
        "reviewer_confirmed": confirmed,
        "conversion_rate": _ratio(confirmed, warn_findings),
    }


def _spend_summary(
    db_records: Sequence[ReportRecord],
    workflow_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    estimated = 0.0
    observed = 0.0
    records_with_cost = 0
    observed_seen = False
    accepted = 0
    for record in [*_records_as_mappings(db_records), *workflow_records]:
        if str(record.get("terminal_verdict") or _aggregate(record).get("terminal_verdict") or "").upper() == "PASS":
            accepted += 1
        tier2 = _tier(record, 2)
        estimate = tier2.get("estimate") if isinstance(tier2.get("estimate"), Mapping) else {}
        dispatch = tier2.get("dispatch") if isinstance(tier2.get("dispatch"), Mapping) else {}
        cost_seen = False
        if estimate.get("estimated_cost_usd") is not None:
            estimated += float(estimate.get("estimated_cost_usd") or 0.0)
            cost_seen = True
        observed_value = (
            dispatch["observed_cost_usd"]
            if "observed_cost_usd" in dispatch
            else tier2.get("observed_cost_usd")
        )
        if observed_value is not None:
            observed += float(observed_value or 0.0)
            observed_seen = True
            cost_seen = True
        if cost_seen:
            records_with_cost += 1
    numerator = observed if observed_seen else estimated
    return {
        "accepted_evidence": accepted,
        "records_with_cost": records_with_cost,
        "estimated_cost_usd": round(estimated, 6),
        "observed_cost_usd": round(observed, 6),
        "spend_per_accepted_evidence_usd": _round_or_none(_ratio(numerator, accepted)),
    }


def _records_as_mappings(records: Sequence[ReportRecord]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        aggregate = _aggregate(record.payload)
        out.append(
            {
                "schema_version": record.payload.get("schema_version"),
                "module_id": record.module_id,
                "level_policy": {"family": record.level_policy_family},
                "aggregate": aggregate,
                "dimensions": record.payload.get("dimensions"),
                "findings": _findings_from_payload(record.payload),
                "verdict": aggregate.get("verdict"),
                "terminal_verdict": aggregate.get("terminal_verdict"),
                "completion_status": aggregate.get("completion_status", "COMPLETE"),
                "workflow_verdict": aggregate.get("workflow_verdict", aggregate.get("verdict")),
                "_store": {
                    "run_id": record.run_id,
                    "level": record.level,
                    "slug": record.slug,
                    "reviewer_model": record.reviewer_model,
                    "reviewer_family": record.reviewer_family,
                },
            }
        )
    return out


def _flatten_workflow_payloads(
    payloads: Sequence[Mapping[str, Any] | Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for payload in payloads:
        if isinstance(payload, Mapping):
            if payload.get("schema_version") == "qg_workflow_dry_run.v1":
                continue
            out.append(dict(payload))
        else:
            out.extend(dict(item) for item in payload if isinstance(item, Mapping))
    return out


def _findings_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    findings = payload.get("findings")
    if isinstance(findings, list):
        return [dict(item) for item in findings if isinstance(item, Mapping)]
    dimensions = payload.get("dimensions")
    out: list[dict[str, Any]] = []
    if isinstance(dimensions, Mapping):
        for entry in dimensions.values():
            if isinstance(entry, Mapping) and isinstance(entry.get("findings"), list):
                out.extend(dict(item) for item in entry["findings"] if isinstance(item, Mapping))
    return out


def _metric_vote(finding: Mapping[str, Any]) -> dict[str, Any] | None:
    metadata = finding.get("metadata") if isinstance(finding.get("metadata"), Mapping) else {}
    qg_eval = metadata.get("qg_eval") if isinstance(metadata.get("qg_eval"), Mapping) else None
    gold_eval = metadata.get("gold_eval") if isinstance(metadata.get("gold_eval"), Mapping) else None
    ua_gec_gold = metadata.get("ua_gec_gold") if isinstance(metadata.get("ua_gec_gold"), Mapping) else None
    if qg_eval is None and gold_eval is None:
        return None
    source = qg_eval or gold_eval or {}
    axis = str(source.get("axis") or _axis_for_finding(finding, ua_gec_gold))
    gold = bool(source.get("gold_label", source.get("gold", source.get("is_gold", False))))
    predicted = bool(source.get("predicted", source.get("model_flagged", source.get("detected", False))))
    matched = bool(source.get("matched", predicted and gold))
    contested = bool(source.get("contested") or _finding_contested(finding))
    return {
        "axis": axis,
        "gold": gold,
        "predicted": predicted,
        "matched": matched,
        "contested": contested,
    }


def _score_votes(votes: Sequence[Mapping[str, Any]], *, include_contested: bool) -> dict[str, Any]:
    filtered = [vote for vote in votes if include_contested or not vote.get("contested")]
    tp = sum(1 for vote in filtered if vote.get("predicted") and vote.get("gold") and vote.get("matched"))
    fp = sum(1 for vote in filtered if vote.get("predicted") and not (vote.get("gold") and vote.get("matched")))
    fn = sum(1 for vote in filtered if vote.get("gold") and not vote.get("matched"))
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = None
    if precision is not None and recall is not None and precision + recall:
        f1 = round(2 * precision * recall / (precision + recall), 4)
    return {
        "gold_records": sum(1 for vote in filtered if vote.get("gold")),
        "predicted_records": sum(1 for vote in filtered if vote.get("predicted")),
        "contested_records": sum(1 for vote in filtered if vote.get("contested")),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def _metric_delta(with_contested: Mapping[str, Any], without_contested: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: _round_or_none(
            None
            if with_contested.get(key) is None or without_contested.get(key) is None
            else float(with_contested[key]) - float(without_contested[key])
        )
        for key in ("precision", "recall", "f1")
    } | {
        "contested_gold_records": int(with_contested.get("gold_records") or 0)
        - int(without_contested.get("gold_records") or 0),
        "contested_predicted_records": int(with_contested.get("predicted_records") or 0)
        - int(without_contested.get("predicted_records") or 0),
    }


def _empty_defect_bucket() -> dict[str, Any]:
    return {
        "records": 0,
        "records_with_defects": 0,
        "findings": 0,
        "critical_findings": 0,
        "warning_findings": 0,
    }


def _add_defect_record(bucket: dict[str, Any], findings: Sequence[Mapping[str, Any]]) -> None:
    bucket["records"] += 1
    bucket["findings"] += len(findings)
    bucket["critical_findings"] += sum(1 for finding in findings if finding.get("severity") == "critical")
    bucket["warning_findings"] += sum(1 for finding in findings if finding.get("severity") == "warning")
    if findings:
        bucket["records_with_defects"] += 1


def _finalize_defect_bucket(bucket: Mapping[str, Any]) -> dict[str, Any]:
    records = int(bucket["records"])
    return {
        "records": records,
        "records_with_defects": int(bucket["records_with_defects"]),
        "defect_rate": _ratio(int(bucket["records_with_defects"]), records),
        "findings": int(bucket["findings"]),
        "critical_findings": int(bucket["critical_findings"]),
        "warning_findings": int(bucket["warning_findings"]),
    }


def _penalized_findings(findings: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(finding)
        for finding in findings
        if finding.get("disposition", "defect") == "defect" and finding.get("severity") in {"critical", "warning"}
        and not _finding_contested(finding)
    ]


def _reviewer_confirms(warn_finding: Mapping[str, Any], reviewer_findings: Sequence[Mapping[str, Any]]) -> bool:
    for finding in reviewer_findings:
        if finding.get("disposition", "defect") != "defect":
            continue
        if finding.get("excerpt") and finding.get("excerpt") == warn_finding.get("excerpt"):
            return True
        if (
            finding.get("dimension") == warn_finding.get("dimension")
            and finding.get("issue_class") == warn_finding.get("issue_class")
        ):
            return True
    return False


def _prompt_hash_for_target(target: ReportTarget) -> str | None:
    texts = {}
    for name in llm_qg_store.CONTENT_FILES:
        path = target.module_dir / name
        texts[name] = path.read_text(encoding="utf-8") if path.exists() else ""
    prompt = llm_reviewer.build_reviewer_prompt(
        level=target.level.strip().lower(),
        slug=target.slug.strip(),
        module_md=texts.get("module.md", ""),
        activities_yaml=texts.get("activities.yaml", ""),
        vocabulary_yaml=texts.get("vocabulary.yaml", ""),
        resources_yaml=texts.get("resources.yaml", ""),
    )
    return llm_qg_store.prompt_hash_for_text(prompt)


def _composite_key(record: ReportRecord) -> tuple[Any, ...]:
    return (
        record.level,
        record.slug,
        record.content_sha,
        record.gate_version,
        record.prompt_hash,
        record.checker_version,
        _norm_str(record.level_policy_family),
        _norm_str(record.reviewer_model),
    )


def _aggregate(record: Mapping[str, Any]) -> Mapping[str, Any]:
    aggregate = record.get("aggregate")
    return aggregate if isinstance(aggregate, Mapping) else {}


def _tier(record: Mapping[str, Any], tier_number: int) -> dict[str, Any]:
    workflow = record.get("qg_workflow")
    tiers = workflow.get("tiers") if isinstance(workflow, Mapping) else []
    if isinstance(tiers, list):
        for tier in tiers:
            if isinstance(tier, Mapping) and tier.get("tier") == tier_number:
                return dict(tier)
    return {}


def _level_for_record(record: Mapping[str, Any]) -> str:
    module_id = str(record.get("module_id") or "")
    if "/" in module_id:
        return module_id.split("/", 1)[0]
    store = record.get("_store") if isinstance(record.get("_store"), Mapping) else {}
    return str(store.get("level") or "unknown")


def _policy_family_for_record(record: Mapping[str, Any]) -> str:
    policy = record.get("level_policy")
    if isinstance(policy, Mapping) and policy.get("family"):
        return str(policy["family"])
    return "unknown"


def _reviewer_model_for_record(record: Mapping[str, Any]) -> str:
    workflow = record.get("qg_workflow")
    if isinstance(workflow, Mapping) and workflow.get("reviewer_model_id"):
        return str(workflow["reviewer_model_id"])
    store = record.get("_store") if isinstance(record.get("_store"), Mapping) else {}
    return str(store.get("reviewer_model") or "unknown")


def _axis_for_finding(finding: Mapping[str, Any], ua_gec_gold: Mapping[str, Any] | None = None) -> str:
    issue_class = str(finding.get("issue_class") or "")
    if issue_class in {"calque", "collocation", "false_friend"}:
        return "calque"
    if issue_class == "grammar":
        return "grammar"
    tag = str((ua_gec_gold or {}).get("gold_tag") or finding.get("ua_gec_tag") or "")
    if tag.startswith("G/"):
        return "grammar"
    if tag.startswith("F/"):
        return "calque"
    return issue_class or "other"


def _finding_contested(finding: Mapping[str, Any]) -> bool:
    metadata = finding.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    gold = metadata.get("ua_gec_gold")
    if isinstance(gold, Mapping) and (gold.get("contested_flag") or gold.get("contested")):
        return True
    qg_eval = metadata.get("qg_eval")
    return isinstance(qg_eval, Mapping) and bool(qg_eval.get("contested"))


def _ratio(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return round(float(numerator) / float(denominator), 4)


def _round_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 4)


def _now_z() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def format_markdown(report: Mapping[str, Any]) -> str:
    defect = report["defect_rates"]["overall"]
    cache = report["cache"]
    completion = report["completion"]
    calque = report["gold_metrics"]["calque"]
    lines = [
        "# QG Corpus Report",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Latest composite records: {report['selection']['latest_composite_records']}",
        f"- Raw DB rows: {report['selection']['raw_db_rows']}",
        f"- Cache: hit {cache['hit']} / stale {cache['stale']} / miss {cache['miss']}",
        f"- Overall defect rate: {_pct(defect['defect_rate'])}",
        f"- Incomplete: {completion['incomplete']}",
        f"- Provider errors: {completion['provider_error']}",
        f"- Parse/schema failures: {completion['parse_failure']}",
        f"- Calque precision with contested: {_pct(calque['with_contested']['precision'])}",
        f"- Calque precision without contested: {_pct(calque['without_contested']['precision'])}",
    ]
    return "\n".join(lines)


def format_backfill_markdown(backfill: Mapping[str, Any]) -> str:
    counts = backfill.get("counts") if isinstance(backfill.get("counts"), Mapping) else {}
    lines = [
        "# QG Corpus Backfill",
        "",
        f"- Schema: `{backfill.get('schema_version')}`",
        f"- Dry run: {backfill.get('dry_run')}",
        f"- DB: `{backfill.get('db')}`",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _parse_target(raw: str) -> ReportTarget:
    parts = raw.split(":", 2)
    if len(parts) != 3:
        raise ValueError("--target must be level:slug:module_dir")
    return ReportTarget(level=parts[0].strip().lower(), slug=parts[1].strip(), module_dir=Path(parts[2]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, help="Optional LLM-QG SQLite path.")
    parser.add_argument("--curriculum-root", type=Path, help="Discover module targets under this root.")
    parser.add_argument("--target", action="append", default=[], help="Repeatable level:slug:module_dir target.")
    parser.add_argument("--workflow-json", action="append", type=Path, default=[], help="Stored qg_workflow JSON output.")
    parser.add_argument("--backfill-from", action="append", type=Path, default=[], help="Workflow JSON to backfill into DB.")
    parser.add_argument("--apply-backfill", action="store_true", help="Insert missing/stale backfill records.")
    parser.add_argument("--gate-version", default=qg_workflow.DEFAULT_GATE_VERSION)
    parser.add_argument("--checker-version", default=CHECKER_VERSION)
    parser.add_argument("--reviewer-model-id", default=qg_workflow.DEFAULT_REVIEWER_MODEL_ID)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="Optional output path.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        targets = [_parse_target(raw) for raw in args.target]
        if args.curriculum_root:
            targets.extend(discover_targets(args.curriculum_root))
        workflow_payloads = [load_workflow_json(path) for path in args.workflow_json]
        if args.backfill_from:
            payloads = [load_workflow_json(path) for path in args.backfill_from]
            output: Mapping[str, Any] = backfill_from_workflow_records(
                payloads,
                db_path=args.db,
                dry_run=not args.apply_backfill,
            )
        else:
            output = build_report(
                db_path=args.db,
                targets=targets,
                workflow_payloads=workflow_payloads,
                gate_version=args.gate_version,
                checker_version=args.checker_version,
                reviewer_model_id=args.reviewer_model_id,
            )
        if args.format == "json":
            text = json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True)
        elif output.get("schema_version") == "qg_corpus_backfill.v1":
            text = format_backfill_markdown(output)
        else:
            text = format_markdown(output)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
