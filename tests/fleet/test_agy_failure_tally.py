"""Read-only failure census, diagnostic precedence and CLI contract (#10206)."""

import importlib
import json
from datetime import UTC, datetime

import pytest

from tests.agent_runtime.test_agy_transient_fault import API_503, ELIGIBILITY_503, INTERRUPTED, LOAD_503


def _module():
    return importlib.import_module("scripts.fleet.agy_failure_tally")


@pytest.mark.parametrize(
    "text,cause",
    [
        ("agy_background_task_canceled\nmore", "cancellation"),
        ("agy_background_task_unconfirmed", "unconfirmed"),
        ("agy_headless_permission_denied", "permission denied"),
        ("Eligibility check failed: PERMISSION_DENIED (code 403): quotes UNAVAILABLE (code 503)", "permission denied"),
        ("API error (attempt 1): INVALID_ARGUMENT (code 400): quotes UNAVAILABLE (code 503)", "other"),
        ("read-only checkout mutation", "read-only checkout mutation"),
        ("worktree preparation failed", "worktree preparation"),
        ("cut off because it exceeded output token limit", "output token cutoff"),
        ("agy_stream_result_error: " + API_503, "transient provider fault"),
        (API_503, "transient provider fault"),
        ("agy_stream_result_error: " + INTERRUPTED, "transient provider fault"),
        (ELIGIBILITY_503, "transient provider fault"),
        (LOAD_503, "transient provider fault"),
        ("agy_stream_output_invalid: missing terminal result", "transient provider fault"),
        (API_503 + ' quotes "agy_background_task_canceled"', "transient provider fault"),
        ("ordinary prose mentions agy_background_task_canceled", "other"),
        ("agy_stream_output_invalid: malformed NDJSON event", "other"),
    ],
)
@pytest.mark.parametrize("field", ["last_error", "failure_code", "stderr_excerpt", "returncode_reason"])
def test_classifies_only_diagnostic_fields_with_shared_header_parser(text, cause, field):
    assert _module().classify_failure({field: text, "response": API_503}) == cause


def _record(**extra):
    return {"agent": "agy", "status": "failed", "started_at": "2026-10-06T00:00:00Z", "last_error": API_503, **extra}


def test_filters_dates_agents_status_and_dry_runs_and_splits_boundary():
    module = _module()
    records = [
        _record(started_at="2026-09-25T00:00:00Z", last_error="agy_background_task_canceled"),
        _record(agent="gemini"),
        _record(),
        _record(started_at="2026-09-24T23:59:59Z"),
        _record(agent="codex"),
        _record(status="done"),
        _record(status="dry_run"),
        _record(dry_run=True),
        _record(launch_mode="dry_run"),
        _record(started_at="broken"),
        _record(started_at=None),
    ]
    report = module.tally(
        records, since=datetime(2026, 9, 25, tzinfo=UTC), before_after=datetime(2026, 10, 6, tzinfo=UTC)
    )
    assert report["tasks"] == 3
    assert report["before"]["tasks"] == 1
    assert report["after"]["tasks"] == 2
    assert report["counts"]["cancellation"] == 1
    assert report["counts"]["transient provider fault"] == 2
    assert report["skipped_undated"] == 2
    assert sum(report["counts"].values()) == 3
    assert "before_after" in module.format_report(report)


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_reads_top_level_only_and_never_writes(tmp_path, capsys, json_output):
    module = _module()
    (tmp_path / "task.json").write_text(json.dumps(_record()))
    (tmp_path / "bad.json").write_text("broken")
    (tmp_path / "array.json").write_text("[]")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "excluded.json").write_text(json.dumps(_record()))
    paths = list(tmp_path.rglob("*.json"))
    before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
    args = ["--tasks-dir", str(tmp_path), "--since", "2026-09-25", "--before-after", "2026-10-06"]
    assert module.main(args + (["--json"] if json_output else [])) == 0
    output = capsys.readouterr().out
    if json_output:
        report = json.loads(output)
        assert report["after"]["counts"]["transient provider fault"] == 1
        assert report["skipped_unreadable"] == 2
    else:
        assert "transient provider fault: 1" in output
        assert "skipped_unreadable: 2" in output
    assert {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.rglob("*.json")} == before


@pytest.mark.parametrize("args", [["--since", "invalid"], ["--since", "2026-09-25", "--before-after", "invalid"]])
def test_invalid_dates_have_nonzero_exit_without_writes(capsys, args):
    assert _module().main(args) == 2
    assert "YYYY-MM-DD" in capsys.readouterr().err


def test_missing_directory_is_reported_without_private_path(tmp_path, capsys):
    assert _module().main(["--since", "2026-09-25", "--tasks-dir", str(tmp_path / "missing")]) == 2
    output = capsys.readouterr().err
    assert "tasks directory not found" in output
    assert str(tmp_path) not in output


def test_help_describes_defaults_examples_outputs_exit_codes_and_related():
    text = _module().build_parser().format_help()
    for expected in [
        "Examples:",
        "Outputs:",
        "Exit codes:",
        "Related:",
        "Default:",
        "--since",
        "--before-after",
        "--json",
    ]:
        assert expected in text


def test_tally_imports_the_adapter_parser():
    from scripts.agent_runtime.adapters.agy import parse_agy_provider_fault

    assert _module().parse_agy_provider_fault is parse_agy_provider_fault


@pytest.mark.parametrize("field", ["last_error", "failure_code", "stderr_excerpt", "returncode_reason"])
@pytest.mark.parametrize(
    "text",
    [
        "API error (attempt 1): INVALID_ARGUMENT (code 400): permission denied while validating input",
        "Eligibility check failed: INVALID_ARGUMENT (code 400): quotes permission_denied",
        "ordinary prose mentions permission denied",
    ],
)
def test_permission_denied_message_text_is_not_a_permission_cause(field, text):
    module = _module()
    assert module.classify_failure({field: text}) == "other"
    # Native reason fields and the parsed provider status still count.
    for reason in (
        "permission_denied",
        "permission denied: refused",
        "agy_headless_permission_denied",
        "Eligibility check failed: PERMISSION_DENIED (code 403): access refused",
    ):
        assert module.classify_failure({field: reason}) == "permission denied"
