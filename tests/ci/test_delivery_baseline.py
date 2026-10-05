"""Tests for the offline delivery-baseline evaluator (#9738)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.ci import delivery_baseline as db

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "delivery_baseline"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _record(report: dict, task_id: str) -> dict:
    return next(item for item in report["records"] if item["task_id"] == task_id)


def _at(minute: int) -> datetime:
    return datetime(2026, 1, 1, 10, minute, tzinfo=UTC)


def test_canonical_task_and_linked_pr_check_spans_are_qualified() -> None:
    report = db.evaluate(_load("canonical_linked.json"))
    record = _record(report, "fixture-canonical-1")
    assert record["disposition"] == "delivered"
    assert {name: metric["status"] for name, metric in record["metrics"].items()} == {
        "intake.elapsed": "qualified",
        "authoring.worker_wall": "qualified",
        "ci_landing.check_wall": "qualified",
        "ci_landing.queue_delay": "qualified",
        "ci_landing.elapsed": "qualified",
    }
    assert record["metrics"]["authoring.worker_wall"]["union_s"] == 2700.0
    assert record["metrics"]["ci_landing.queue_delay"]["union_s"] == 60.0


def test_missing_or_non_canonical_span_is_unknown_never_zero() -> None:
    record = _record(db.evaluate(_load("unknown_span.json")), "fixture-missing-1")
    authoring = record["metrics"]["authoring.worker_wall"]
    assert authoring == {"status": "unknown", "union_s": None, "spans_s": [None], "reasons": ["missing_endpoint"]}
    review = record["metrics"]["verification_review.worker_wall"]
    assert review["status"] == "unknown"
    assert review["reasons"] == ["non_canonical_source"]
    assert record["metrics"]["onboarding.elapsed"]["status"] == "unqualified"


def test_unknown_value_makes_the_comparison_inconclusive() -> None:
    report = db.evaluate(_load("unknown_span.json"))
    metric = report["strata"]["routine_product_change"]["metrics"]["authoring.worker_wall"]
    assert metric["verdict"] == "inconclusive"
    assert "unknown_value_in_before" in metric["reasons"]


def test_overlapping_spans_report_union_not_sum() -> None:
    record = _record(db.evaluate(_load("overlapping_spans.json")), "fixture-overlap-1")
    checks = record["metrics"]["ci_landing.check_wall"]
    assert checks["spans_s"] == [600.0, 600.0]
    assert checks["union_s"] == 900.0
    assert checks["union_s"] != sum(checks["spans_s"])


@pytest.mark.parametrize(
    ("task_id", "reason"),
    [
        ("fixture-unlinked", "unlinked_outcome"),
        ("fixture-no-merge", "not_merged"),
        ("fixture-no-review", "no_review_of_record"),
        ("fixture-no-cleanup", "no_cleanup_evidence"),
        ("fixture-self-review", "review_not_independent"),
        ("fixture-stale-head", "review_not_exact_head"),
    ],
)
def test_finished_but_unproven_records_are_not_delivered(task_id: str, reason: str) -> None:
    record = _record(db.evaluate(_load("not_delivered.json")), task_id)
    assert record["disposition"] == "not_delivered"
    assert record["reasons"] == [reason]


def test_exclusions_and_out_of_strata_records_are_excluded_not_counted() -> None:
    report = db.evaluate(_load("not_delivered.json"))
    assert report["excluded"] == ["fixture-excluded-dry-run", "fixture-outside-strata"]
    denominators = report["strata"]["routine_product_change"]["denominators"]["before"]
    assert denominators["members"] == 6
    assert denominators["delivered"] == 0


def test_floor_applies_per_stratum_never_pooled() -> None:
    report = db.evaluate(_load("stratum_floor.json"))
    delivered = {
        arm: sum(1 for r in report["records"] if r["arm"] == arm and r["disposition"] == "delivered") for arm in db.ARMS
    }
    assert delivered == {"before": 11, "after": 11}
    for stratum in ("routine_product_change", "architecture_change"):
        assert report["strata"][stratum]["verdict"] == "inconclusive"
        assert report["strata"][stratum]["metrics"]["authoring.worker_wall"]["reasons"] == [
            "fewer_than_five_delivered_in_stratum"
        ]
    launcher = report["strata"]["launcher_repair"]
    assert launcher["verdict"] == "reportable"
    assert launcher["metrics"]["authoring.worker_wall"]["before"]["n"] == 5


def test_claims_on_inconclusive_or_pooled_comparisons_are_rejected() -> None:
    claims = {(c["stratum"], c["metric"]): c for c in db.evaluate(_load("stratum_floor.json"))["claims"]}
    assert claims[("routine_product_change", "authoring.worker_wall")]["status"] == "rejected"
    assert claims[("launcher_repair", "ci_landing.check_wall")]["reason"] == "comparison_inconclusive"
    assert claims[("pooled", "authoring.worker_wall")]["reason"] == "not_a_single_frozen_stratum"
    admissible = claims[("launcher_repair", "authoring.worker_wall")]
    assert admissible["status"] == "admissible"
    assert admissible["reason"] == "reportable_distribution_only_not_significance"


def test_incomparable_setup_is_inconclusive() -> None:
    cohort = _load("stratum_floor.json")
    for record in cohort["records"]:
        if record["arm"] == "after" and record["stratum"] == "launcher_repair":
            record["matched_setup"] = {"required_check": "other"}
    metric = db.evaluate(cohort)["strata"]["launcher_repair"]["metrics"]["authoring.worker_wall"]
    assert metric["verdict"] == "inconclusive"
    assert metric["reasons"] == ["incomparable_setup"]


def test_missing_metric_in_one_arm_is_inconclusive() -> None:
    cohort = _load("stratum_floor.json")
    target = next(r for r in cohort["records"] if r["arm"] == "before" and r["stratum"] == "launcher_repair")
    target["spans"].append(
        {
            "stage": "ci_landing",
            "kind": "check_wall",
            "start_field": "github.check_run.startedAt",
            "end_field": "github.check_run.completedAt",
            "start": "2026-01-01T11:00:00Z",
            "end": "2026-01-01T11:05:00Z",
        }
    )
    metric = db.evaluate(cohort)["strata"]["launcher_repair"]["metrics"]["ci_landing.check_wall"]
    assert metric["verdict"] == "inconclusive"
    assert "missing_value_in_after" in metric["reasons"]


def test_negative_interval_and_naive_timestamp_are_unknown() -> None:
    negative = {
        "stage": "authoring",
        "kind": "worker_wall",
        "start_field": "task.started_at",
        "end_field": "task.finished_at",
    }
    assert db._span_value({**negative, "start": "2026-01-01T11:00:00Z", "end": "2026-01-01T10:00:00Z"}) == (
        None,
        "negative_interval",
    )
    assert db._span_value({**negative, "start": "2026-01-01T10:00:00", "end": "2026-01-01T11:00:00Z"}) == (
        None,
        "missing_endpoint",
    )


def test_union_seconds_merges_overlaps_and_keeps_gaps() -> None:
    assert db.union_seconds([]) == 0.0
    intervals = [(_at(0), _at(10)), (_at(5), _at(12)), (_at(20), _at(25)), (_at(21), _at(22))]
    assert db.union_seconds(intervals) == (12 + 5) * 60.0


def test_unqualified_stages_are_exactly_onboarding_and_capacity() -> None:
    assert frozenset({"onboarding", "capacity"}) == db.UNQUALIFIED_STAGES


@pytest.mark.parametrize(
    ("cohort", "message"),
    [
        ({"schema_version": "other", "records": []}, "schema_version"),
        ({"schema_version": db.SCHEMA_VERSION, "records": {}}, "records must be a list"),
        ({"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "during"}]}, "arm must be"),
        ({"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before"}] * 2}, "duplicated"),
        (
            {
                "schema_version": db.SCHEMA_VERSION,
                "records": [{"task_id": "x", "arm": "before", "spans": [{"stage": "deploy", "kind": "elapsed"}]}],
            },
            "unknown stage",
        ),
    ],
)
def test_malformed_cohorts_are_refused(cohort: dict, message: str) -> None:
    with pytest.raises(db.CohortError, match=message):
        db.evaluate(cohort)


def test_report_records_input_digest_and_is_deterministic() -> None:
    first = db.evaluate(_load("stratum_floor.json"))
    second = db.evaluate(_load("stratum_floor.json"))
    assert first == second
    assert len(first["input_sha256"]) == 64


def test_cli_prints_report_and_refuses_bad_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert db.main([str(FIXTURES / "overlapping_spans.json")]) == 0
    assert json.loads(capsys.readouterr().out)["schema_version"] == "delivery-baseline-report.v1"
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    assert db.main([str(bad)]) == 2
    assert "schema_version" in capsys.readouterr().err
