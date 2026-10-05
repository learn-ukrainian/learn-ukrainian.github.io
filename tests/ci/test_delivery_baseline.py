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


# Held-out regressions from the independent review of 23e310dfad: an at-floor
# cohort (five per arm in one stratum) mirrors the reviewer's base input, and
# each test applies one of the reviewer's mutations to it.
CLAIM = {"stratum": "architecture_change", "metric": "ci_landing.check_wall"}


def _check_run(start: str, end: str) -> dict:
    return {
        "stage": "ci_landing",
        "kind": "check_wall",
        "start_field": "github.check_run.startedAt",
        "end_field": "github.check_run.completedAt",
        "start": f"2026-03-01T{start}:00Z",
        "end": f"2026-03-01T{end}:00Z",
    }


def _floor_cohort() -> dict:
    records = []
    for index in range(2 * db.MIN_DELIVERED_PER_ARM):
        arm = db.ARMS[index % 2]
        head = f"{index:040x}"
        records.append(
            {
                "task_id": f"heldout-{arm}-{index}",
                "arm": arm,
                "stratum": "architecture_change",
                "matched_setup": {"required_check": "CI Gate", "review_profile": "code"},
                "outcome": {"issue": 900 + index, "pr": 950 + index},
                "review_of_record": {
                    "verdict": "APPROVE",
                    "head_sha": head,
                    "author_family": "anthropic",
                    "reviewer_family": "openai",
                },
                "merge": {"merged_at": "2026-03-01T13:00:00Z", "head_sha": head},
                "cleanup": {"state": "CLEANED_UP", "observed_at": "2026-03-01T14:00:00Z"},
                "spans": [_check_run("12:00", "12:04"), _check_run("12:02", "12:07"), _check_run("12:10", "12:11")],
            }
        )
    return {"schema_version": db.SCHEMA_VERSION, "records": records, "claims": [CLAIM]}


def _verdict(cohort: dict) -> tuple[dict, dict, dict | None]:
    report = db.evaluate(cohort)
    stratum = report["strata"]["architecture_change"]
    return report, stratum, stratum["metrics"].get("ci_landing.check_wall")


def test_heldout_base_cohort_at_floor_is_reportable() -> None:
    report, stratum, metric = _verdict(_floor_cohort())
    assert _record(report, "heldout-before-0")["metrics"]["ci_landing.check_wall"]["spans_s"] == [240.0, 300.0, 60.0]
    assert _record(report, "heldout-before-0")["metrics"]["ci_landing.check_wall"]["union_s"] == 480.0
    assert stratum["verdict"] == "reportable"
    assert metric["before"]["n"] == metric["after"]["n"] == 5
    assert report["claims"][0]["status"] == "admissible"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("author_family", None),
        ("author_family", ""),
        ("author_family", "   "),
        ("author_family", 7),
        ("reviewer_family", None),
    ],
)
def test_unknown_author_or_reviewer_family_never_establishes_independence(field: str, value: object) -> None:
    cohort = _floor_cohort()
    for record in cohort["records"]:
        if value is None:
            record["review_of_record"].pop(field)
        else:
            record["review_of_record"][field] = value
    report, stratum, metric = _verdict(cohort)
    assert metric is None
    assert {tuple(item["reasons"]) for item in report["records"]} == {("review_identity_unknown",)}
    assert stratum["denominators"]["before"]["not_delivered_reasons"] == {"review_identity_unknown": 5}
    assert stratum["verdict"] == "inconclusive"
    assert report["claims"][0]["status"] == "rejected"


def test_family_comparison_ignores_case_and_whitespace() -> None:
    cohort = _floor_cohort()
    cohort["records"][0]["review_of_record"].update(author_family="Anthropic ", reviewer_family="anthropic")
    assert _record(db.evaluate(cohort), "heldout-before-0")["reasons"] == ["review_not_independent"]


def _one_outcome_per_arm(cohort: dict) -> dict:
    for record in cohort["records"]:
        first = cohort["records"][db.ARMS.index(record["arm"])]
        for key in ("outcome", "review_of_record", "merge", "cleanup"):
            record[key] = json.loads(json.dumps(first[key]))
    return cohort


def test_repeated_attempts_at_one_outcome_are_refused_not_counted(tmp_path: Path) -> None:
    cohort = _one_outcome_per_arm(_floor_cohort())
    with pytest.raises(db.CohortError, match="share outcome pr 950"):
        db.evaluate(cohort)
    path = tmp_path / "repeated.json"
    path.write_text(json.dumps(cohort), encoding="utf-8")
    assert db.main([str(path)]) == 2


def test_shared_merged_head_under_different_pr_numbers_is_one_outcome() -> None:
    cohort = _floor_cohort()
    cohort["records"][1]["merge"]["head_sha"] = cohort["records"][0]["merge"]["head_sha"]
    with pytest.raises(db.CohortError, match="share outcome merged_head"):
        db.evaluate(cohort)


def test_explicitly_excluded_repeats_count_once_and_miss_the_floor() -> None:
    cohort = _one_outcome_per_arm(_floor_cohort())
    for record in cohort["records"][2:]:
        record["exclusion"] = "duplicate_attempt"
    report, stratum, metric = _verdict(cohort)
    assert {arm: stratum["denominators"][arm]["delivered"] for arm in db.ARMS} == {"before": 1, "after": 1}
    assert len(report["excluded"]) == 8
    assert stratum["floor_met"] is False
    assert metric["reasons"] == ["fewer_than_five_delivered_in_stratum"]
    assert report["claims"][0]["status"] == "rejected"


@pytest.mark.parametrize("setup", ["absent", None, {}, {"required_check": None, "review_profile": "code"}])
def test_missing_or_empty_setup_is_unknown_and_inconclusive(setup: object) -> None:
    cohort = _floor_cohort()
    for record in cohort["records"]:
        if setup == "absent":
            record.pop("matched_setup")
        else:
            record["matched_setup"] = setup
    report, stratum, metric = _verdict(cohort)
    assert metric == {"verdict": "inconclusive", "reasons": ["unknown_setup"]}
    assert stratum["verdict"] == "inconclusive"
    assert report["claims"][0] == {**CLAIM, "status": "rejected", "reason": "comparison_inconclusive"}


def test_one_record_without_setup_makes_the_comparison_inconclusive() -> None:
    cohort = _floor_cohort()
    cohort["records"][3].pop("matched_setup")
    assert _verdict(cohort)[2]["reasons"] == ["unknown_setup"]


@pytest.mark.parametrize(
    "outcome",
    [
        {"issue": False, "pr": True},
        {"issue": True, "pr": 950},
        {"issue": 0, "pr": 950},
        {"issue": -1, "pr": 950},
        {"issue": "900", "pr": 950},
        {"issue": 900, "pr": 950.0},
    ],
)
def test_outcome_identifiers_must_be_positive_integers(outcome: dict) -> None:
    cohort = _floor_cohort()
    for index, record in enumerate(cohort["records"]):
        record["outcome"] = dict(outcome) if index == 0 else record["outcome"]
    report = db.evaluate(cohort)
    assert _record(report, "heldout-before-0")["reasons"] == ["unlinked_outcome"]
    assert report["claims"][0]["status"] == "rejected"


def test_boolean_identifiers_everywhere_are_not_delivered() -> None:
    cohort = _floor_cohort()
    for record in cohort["records"]:
        record["outcome"] = {"issue": False, "pr": True}
    report, stratum, _ = _verdict(cohort)
    assert {tuple(item["reasons"]) for item in report["records"]} == {("unlinked_outcome",)}
    assert stratum["verdict"] == "inconclusive"


@pytest.mark.parametrize(
    ("cohort", "message"),
    [
        ([], "cohort must be a JSON object"),
        ({"schema_version": db.SCHEMA_VERSION, "records": [None]}, "each record must be an object"),
        (
            {"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before", "spans": [False]}]},
            "each span must be an object",
        ),
        (
            {"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before", "spans": {"a": 1}}]},
            "spans must be a list",
        ),
        (
            {"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before", "outcome": [1]}]},
            "outcome must be an object",
        ),
        (
            {
                "schema_version": db.SCHEMA_VERSION,
                "records": [{"task_id": "x", "arm": "before", "exclusion": "dry_run", "merge": "yes"}],
            },
            "merge must be an object",
        ),
        (
            {"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before", "matched_setup": "x"}]},
            "matched_setup must be an object",
        ),
        ({"schema_version": db.SCHEMA_VERSION, "records": [], "claims": {}}, "claims must be a list"),
        ({"schema_version": db.SCHEMA_VERSION, "records": [], "claims": [None]}, "each claim must be an object"),
        (
            {"schema_version": db.SCHEMA_VERSION, "records": [], "claims": [{"stratum": "x", "metric": ["m"]}]},
            "string metric",
        ),
    ],
)
def test_malformed_structures_raise_cohort_error(cohort: object, message: str) -> None:
    with pytest.raises(db.CohortError, match=message):
        db.evaluate(cohort)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "document",
    [
        [],
        {"schema_version": db.SCHEMA_VERSION, "records": [None]},
        {"schema_version": db.SCHEMA_VERSION, "records": [{"task_id": "x", "arm": "before", "spans": [False]}]},
    ],
)
def test_cli_exits_two_on_malformed_structures(
    document: object, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "malformed.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    assert db.main([str(path)]) == 2
    assert capsys.readouterr().err.startswith("delivery_baseline: ")


def test_unhashable_span_fields_are_non_canonical_not_a_crash() -> None:
    span = {
        "stage": "authoring",
        "kind": "worker_wall",
        "start_field": ["task.started_at"],
        "end_field": "task.finished_at",
        "start": "2026-01-01T10:00:00Z",
        "end": "2026-01-01T11:00:00Z",
    }
    assert db._span_value(span) == (None, "non_canonical_source")


def test_actions_job_span_is_a_qualified_check_wall() -> None:
    span = {
        "stage": "ci_landing",
        "kind": "check_wall",
        "start_field": "github.actions_job.started_at",
        "end_field": "github.actions_job.completed_at",
        "start": "2026-01-01T10:00:00Z",
        "end": "2026-01-01T10:07:00Z",
    }
    interval, reason = db._span_value(span)
    assert reason is None
    assert interval is not None
    assert (interval[1] - interval[0]).total_seconds() == 420.0


def test_help_documents_examples_outputs_exit_codes_and_related(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exited:
        db.main(["--help"])
    assert exited.value.code == 0
    text = capsys.readouterr().out
    for section in ("Examples:", "Outputs:", "Side effects: none", "Exit codes:", "Related:"):
        assert section in text
    assert ".venv/bin/python -m scripts.ci.delivery_baseline cohort.json" in text
    assert "docs/design/agent-friendly-delivery-baseline.md" in text
