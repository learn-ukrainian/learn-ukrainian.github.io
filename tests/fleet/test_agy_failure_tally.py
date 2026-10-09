"""Cause counts for failed AGY task records (#10206)."""

import json
from datetime import UTC, datetime

import pytest

from scripts.fleet.agy_failure_tally import (
    CAUSE_LABELS,
    classify_failure,
    format_report,
    main,
    tally,
)

SINCE = datetime(2026, 9, 25, tzinfo=UTC)
SPLIT = datetime(2026, 10, 6, tzinfo=UTC)


def _record(**fields):
    base = {
        "agent": "agy",
        "status": "failed",
        "started_at": "2026-10-01T00:00:00+00:00",
        "last_error": "",
        "failure_code": "",
        "stderr_excerpt": "",
        "returncode_reason": "",
    }
    base.update(fields)
    return base


@pytest.mark.parametrize(
    ("fields", "cause"),
    [
        ({"last_error": "agy_background_task_canceled"}, "cancellation"),
        ({"last_error": "agy_background_task_unconfirmed"}, "unconfirmed"),
        ({"last_error": "agy_headless_permission_denied"}, "permission denied"),
        ({"last_error": "read-only checkout mutation detected: data/sources.db"}, "read-only checkout mutation"),
        ({"returncode_reason": "worktree preparation failed"}, "worktree preparation"),
        (
            {
                "stderr_excerpt": (
                    "agy_stream_result_error: Your previous response was cut off because it exceeded "
                    "the output token limit."
                )
            },
            "output token cutoff",
        ),
        (
            {
                "last_error": "provider_error",
                "stderr_excerpt": (
                    "agy_stream_result_error: API error (attempt 1): UNAVAILABLE (code 503): "
                    "The service is currently unavailable."
                ),
            },
            "transient provider fault",
        ),
        (
            {
                "stderr_excerpt": (
                    "agy_stream_result_error: The stream was interrupted. "
                    "Please continue the task you were working on."
                )
            },
            "transient provider fault",
        ),
        (
            {"stderr_excerpt": "agy_stream_output_invalid: missing terminal result"},
            "transient provider fault",
        ),
        (
            {
                "stderr_excerpt": (
                    "agy_stream_result_error: Eligibility check failed: failed to get load code assist "
                    "response: UNAVAILABLE (code 503): The service is currently unavailable."
                )
            },
            "transient provider fault",
        ),
        ({"last_error": "review_missing_verdict_line"}, "other"),
        (
            {
                "last_error": "agy_background_task_canceled; read-only checkout mutation detected: data/sources.db",
                "stderr_excerpt": "agy_background_task_canceled API error (attempt 1): UNAVAILABLE (code 503)",
            },
            "cancellation",
        ),
    ],
)
def test_every_cause_class_is_classified_from_record_fields(fields, cause):
    assert classify_failure(_record(**fields)) == cause
    assert cause in CAUSE_LABELS


def test_tally_excludes_dry_run_other_agents_and_splits_the_window():
    records = [
        _record(started_at="2026-09-20T00:00:00+00:00", last_error="agy_background_task_canceled"),
        _record(started_at="2026-10-01T00:00:00+00:00", last_error="agy_background_task_canceled"),
        _record(started_at="2026-10-08T00:00:00+00:00", stderr_excerpt="agy_stream_output_invalid: missing terminal result"),
        _record(status="dry_run", last_error="agy_background_task_canceled"),
        _record(dry_run=True, last_error="agy_background_task_unconfirmed"),
        _record(launch_mode="dry_run", last_error="agy_headless_permission_denied"),
        _record(agent="codex", last_error="agy_background_task_canceled"),
        _record(status="done", last_error="agy_background_task_canceled"),
        _record(agent="gemini", started_at="2026-10-07T00:00:00+00:00", last_error="review_missing_verdict_line"),
        _record(started_at="not-a-date", last_error="agy_background_task_canceled"),
    ]
    report = tally(records, since=SINCE, before_after=SPLIT)
    assert report["tasks"] == 3
    assert report["skipped_undated"] == 1
    assert report["before"]["counts"]["cancellation"] == 1
    assert report["before"]["tasks"] == 1
    assert report["after"]["counts"]["transient provider fault"] == 1
    assert report["after"]["counts"]["other"] == 1
    assert report["after"]["tasks"] == 2
    assert report["counts"]["cancellation"] == 1
    text = format_report(report)
    assert "before:" in text
    assert "transient provider fault: 1" in text
    assert "data/sources.db" not in text


def test_cli_help_and_json_counts(tmp_path, capsys):
    payload = _record(
        started_at="2026-10-08T14:01:38+00:00",
        stderr_excerpt=(
            "agy_stream_result_error: API error (attempt 1): UNAVAILABLE (code 503): "
            "The service is currently unavailable."
        ),
    )
    (tmp_path / "impl-fixture.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    help_text = capsys.readouterr().out
    assert "Count failed AGY and Gemini task records by cause." in help_text
    assert "--since" in help_text
    assert "--before-after" in help_text
    assert "Examples:" in help_text
    assert "Exit codes:" in help_text
    assert "Outputs:" in help_text
    assert "#10206" in help_text

    assert main(["--since", "2026-09-25", "--tasks-dir", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["tasks"] == 1
    assert report["counts"]["transient provider fault"] == 1
    assert report["before_after"] is None

    missing = tmp_path / "absent"
    assert main(["--since", "2026-09-25", "--tasks-dir", str(missing)]) == 2
    assert "not found" in capsys.readouterr().err
