"""Unit tests for scripts/gh_merge_queue_status.py (issue #7814 item 13).

Hermetic, offline test suite verifying:
- PR identifier parsing from integers, hashes, branch names, and URLs.
- Human-readable ETA formatting.
- Deterministic summary line generation across all queue and PR states.
- Accurate merge queue status evaluation from recorded GraphQL and Actions API fixtures.
- CLI output modes: default (JSON + line), --json (pure JSON), and --line (single line).
- Integration with scripts/ci/ci_timings.py via --pr flag.
- Error handling for invalid inputs and non-existent pull requests.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.ci.ci_timings import main as ci_timings_main
from scripts.gh_merge_queue_status import (
    build_summary_line,
    evaluate_status_data,
    fetch_live_status,
    find_latest_merge_group_run,
    format_eta_human,
    main,
    parse_pr_identifier,
    render_output,
)

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "gh_merge_queue_status"
_QUEUED_IN_PROGRESS_FIXTURE = _FIXTURE_DIR / "queued_in_progress.json"
_QUEUED_NO_RUN_FIXTURE = _FIXTURE_DIR / "queued_no_run_yet.json"
_QUEUED_UNKNOWN_FIXTURE = _FIXTURE_DIR / "queued_position_unknown.json"
_NOT_QUEUED_CLEAN_FIXTURE = _FIXTURE_DIR / "not_queued_clean.json"
_MERGED_FIXTURE = _FIXTURE_DIR / "merged.json"
_NOT_FOUND_FIXTURE = _FIXTURE_DIR / "pr_not_found.json"


def test_parse_pr_identifier() -> None:
    """Test PR number extraction from diverse input formats."""
    assert parse_pr_identifier(7814) == 7814
    assert parse_pr_identifier("7814") == 7814
    assert parse_pr_identifier("#7814") == 7814
    assert parse_pr_identifier("pr-7814") == 7814
    assert parse_pr_identifier("issue/7814-mq-visibility") == 7814
    assert parse_pr_identifier("codex/fix-7814-description") == 7814
    assert parse_pr_identifier("gh-readonly-queue/main/pr-7814-2cc5a531afe3b14e49db60ffbc7639ebd849dd26") == 7814
    assert parse_pr_identifier("https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/7814") == 7814
    assert parse_pr_identifier("https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/7814/files") == 7814

    with pytest.raises(ValueError, match="Empty pull request identifier"):
        parse_pr_identifier("")
    with pytest.raises(ValueError, match="Empty pull request identifier"):
        parse_pr_identifier("   ")
    with pytest.raises(ValueError, match="Could not parse pull request number"):
        parse_pr_identifier("not_a_valid_pr")


def test_format_eta_human() -> None:
    """Test human-readable ETA conversion from seconds."""
    assert format_eta_human(None) is None
    assert format_eta_human(0) == "<1 min"
    assert format_eta_human(45) == "<1 min"
    assert format_eta_human(60) == "~1 min"
    assert format_eta_human(520) == "~9 min"
    assert format_eta_human(3480) == "~58 min"
    assert format_eta_human(3600) == "~1h"
    assert format_eta_human(5400) == "~1h 30m"
    assert format_eta_human(7200) == "~2h"


def test_build_summary_line() -> None:
    """Verify one-line summary generation across all operational PR states."""
    # 1. In queue with position, state, ETA, and CI run
    line1 = build_summary_line(
        pr_number=7814,
        queued=True,
        position=2,
        state="QUEUED",
        eta_human="~10 min",
        run_url="https://github.com/actions/runs/123",
        pr_state="OPEN",
        pr_merged=False,
        merge_state_status="CLEAN",
    )
    assert line1 == "PR #7814: queued=yes, position=2 (QUEUED, ~10 min ETA), run=https://github.com/actions/runs/123"

    # 2. In queue with position 11, ~58 min ETA, but no CI run yet
    line2 = build_summary_line(
        pr_number=7814,
        queued=True,
        position=11,
        state="QUEUED",
        eta_human="~58 min",
        run_url=None,
        pr_state="OPEN",
        pr_merged=False,
        merge_state_status="CLEAN",
    )
    assert line2 == "PR #7814: queued=yes, position=11 (QUEUED, ~58 min ETA), run=none"

    # 3. In queue, position unknown
    line3 = build_summary_line(
        pr_number=7814,
        queued=True,
        position=None,
        state="QUEUED",
        eta_human=None,
        run_url=None,
        pr_state="OPEN",
        pr_merged=False,
        merge_state_status="CLEAN",
    )
    assert line3 == "PR #7814: queued=yes, position=unknown (in queue, position unknown), run=none"

    # 4. Not in queue: OPEN + CLEAN
    line4 = build_summary_line(
        pr_number=7814,
        queued=False,
        position=None,
        state=None,
        eta_human=None,
        run_url=None,
        pr_state="OPEN",
        pr_merged=False,
        merge_state_status="CLEAN",
    )
    assert line4 == "PR #7814: queued=no (state=OPEN, mergeStateStatus=CLEAN), run=none"

    # 5. Not in queue: MERGED with historical run URL
    line5 = build_summary_line(
        pr_number=7837,
        queued=False,
        position=None,
        state=None,
        eta_human=None,
        run_url="https://github.com/actions/runs/34261938807",
        pr_state="MERGED",
        pr_merged=True,
        merge_state_status="UNKNOWN",
    )
    assert line5 == "PR #7837: queued=no (merged=yes, state=MERGED), run=https://github.com/actions/runs/34261938807"

    # 6. Not in queue: CLOSED without merge
    line6 = build_summary_line(
        pr_number=7000,
        queued=False,
        position=None,
        state=None,
        eta_human=None,
        run_url=None,
        pr_state="CLOSED",
        pr_merged=False,
        merge_state_status=None,
    )
    assert line6 == "PR #7000: queued=no (state=CLOSED), run=none"


def test_find_latest_merge_group_run() -> None:
    """Test matching and prioritizing merge_group workflow runs for a target PR."""
    runs = [
        {
            "id": 1,
            "name": "Hygiene",
            "head_branch": "gh-readonly-queue/main/pr-7814-abc",
            "event": "merge_group",
            "created_at": "2026-09-08T18:00:00Z",
        },
        {
            "id": 2,
            "name": "CI",
            "head_branch": "gh-readonly-queue/main/pr-7814-abc",
            "event": "merge_group",
            "created_at": "2026-09-08T18:00:00Z",
        },
        {
            "id": 3,
            "name": "CI",
            "head_branch": "gh-readonly-queue/main/pr-7813-xyz",
            "event": "merge_group",
            "created_at": "2026-09-08T18:05:00Z",
        },
        {
            # Stale or newer pull_request run must be ignored despite matching PR number
            "id": 4,
            "name": "CI",
            "head_branch": "gh-readonly-queue/main/pr-7814-abc",
            "event": "pull_request",
            "created_at": "2026-09-08T18:15:00Z",
        },
    ]

    match_7814 = find_latest_merge_group_run(runs, 7814)
    assert match_7814 is not None
    assert match_7814["id"] == 2  # Preferred 'CI' over 'Hygiene', ignored 'pull_request' run #4
    assert match_7814["name"] == "CI"

    # When a newer merge_group run arrives, it must be selected over older runs
    runs_with_newer = [
        *runs,
        {
            "id": 5,
            "name": "CI",
            "head_branch": "gh-readonly-queue/main/pr-7814-def",
            "event": "merge_group",
            "created_at": "2026-09-08T18:20:00Z",
        },
    ]
    match_7814_newer = find_latest_merge_group_run(runs_with_newer, 7814)
    assert match_7814_newer is not None
    assert match_7814_newer["id"] == 5

    match_7813 = find_latest_merge_group_run(runs, 7813)
    assert match_7813 is not None
    assert match_7813["id"] == 3

    assert find_latest_merge_group_run(runs, 9999) is None


def test_evaluate_status_queued_in_progress_fixture() -> None:
    """Verify evaluation of PR queued with active CI run from offline fixture."""
    with open(_QUEUED_IN_PROGRESS_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7814, data.get("actions_runs"))
    assert status.pr_number == 7814
    assert status.queued is True
    assert status.position == 2
    assert status.state == "QUEUED"
    assert status.enqueued_at == "2026-09-08T18:00:00Z"
    assert status.estimated_time_to_merge_seconds == 600
    assert status.estimated_time_to_merge_human == "~10 min"
    assert (
        status.latest_merge_group_run_url
        == "https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/12345678"
    )
    assert status.latest_merge_group_run_status == "in_progress"
    assert status.latest_merge_group_run_conclusion is None
    assert status.pr_merged is False
    assert status.pr_state == "OPEN"
    assert "queued=yes" in status.summary_line
    assert "position=2" in status.summary_line
    assert "~10 min ETA" in status.summary_line


def test_evaluate_status_queued_no_run_yet_fixture() -> None:
    """Verify evaluation of PR queued at position 11 with no CI run yet."""
    with open(_QUEUED_NO_RUN_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7814, data.get("actions_runs"))
    assert status.pr_number == 7814
    assert status.queued is True
    assert status.position == 11
    assert status.estimated_time_to_merge_seconds == 3480
    assert status.estimated_time_to_merge_human == "~58 min"
    assert status.latest_merge_group_run_url is None
    assert status.summary_line == "PR #7814: queued=yes, position=11 (QUEUED, ~58 min ETA), run=none"


def test_evaluate_status_queued_position_unknown_fixture() -> None:
    """Verify evaluation when PR isInMergeQueue is true but entry is null."""
    with open(_QUEUED_UNKNOWN_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7814, data.get("actions_runs"))
    assert status.pr_number == 7814
    assert status.queued is True
    assert status.position is None
    assert status.state == "QUEUED"
    assert status.summary_line == "PR #7814: queued=yes, position=unknown (in queue, position unknown), run=none"


def test_evaluate_status_not_queued_clean_fixture() -> None:
    """Verify evaluation when PR is OPEN and CLEAN but not enqueued."""
    with open(_NOT_QUEUED_CLEAN_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7814, data.get("actions_runs"))
    assert status.pr_number == 7814
    assert status.queued is False
    assert status.position is None
    assert status.pr_state == "OPEN"
    assert status.pr_merge_state_status == "CLEAN"
    assert status.summary_line == "PR #7814: queued=no (state=OPEN, mergeStateStatus=CLEAN), run=none"


def test_evaluate_status_merged_fixture() -> None:
    """Verify evaluation when PR is MERGED."""
    with open(_MERGED_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7837, data.get("actions_runs"))
    assert status.pr_number == 7837
    assert status.queued is False
    assert status.pr_merged is True
    assert status.pr_state == "MERGED"
    assert (
        status.latest_merge_group_run_url
        == "https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/34261938807"
    )
    assert (
        status.summary_line
        == "PR #7837: queued=no (merged=yes, state=MERGED), run=https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/34261938807"
    )


def test_render_output_modes() -> None:
    """Test render_output formats: json_only, line_only, and default (JSON + line)."""
    with open(_QUEUED_IN_PROGRESS_FIXTURE, encoding="utf-8") as f:
        data = json.load(f)

    status = evaluate_status_data(data, 7814, data.get("actions_runs"))

    # 1. Pure JSON
    out_json = render_output(status, json_only=True)
    parsed = json.loads(out_json)
    assert parsed["queued"] is True
    assert parsed["position"] == 2
    assert "PR #7814" not in out_json.splitlines()[-1]

    # 2. Line only
    out_line = render_output(status, line_only=True)
    assert out_line == status.summary_line
    assert "\n" not in out_line

    # 3. Default: JSON + line
    out_default = render_output(status, json_only=False, line_only=False)
    lines = out_default.strip().splitlines()
    assert lines[-1] == status.summary_line
    # Preceding lines should be valid JSON
    json_part = "\n".join(lines[:-1])
    parsed_default = json.loads(json_part)
    assert parsed_default["queued"] is True


def test_cli_main_default_emits_json_and_human_line(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI default invocation emits JSON followed by the human line."""
    exit_code = main(["7814", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE)])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    lines = out.strip().splitlines()
    assert (
        lines[-1]
        == "PR #7814: queued=yes, position=2 (QUEUED, ~10 min ETA), run=https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/12345678"
    )
    parsed = json.loads("\n".join(lines[:-1]))
    assert parsed["position"] == 2


def test_cli_main_json_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI with --json emits only valid JSON."""
    exit_code = main(["7814", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE), "--json"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    data = json.loads(out)
    assert data["queued"] is True
    assert data["position"] == 2
    assert data["summary_line"].startswith("PR #7814:")


def test_cli_main_line_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI with --line emits exactly one human-readable line."""
    exit_code = main(["7814", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE), "--line"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    assert (
        out.strip()
        == "PR #7814: queued=yes, position=2 (QUEUED, ~10 min ETA), run=https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/12345678"
    )


def test_cli_main_invalid_pr_identifier(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI with unparseable PR identifier returns exit code 2."""
    exit_code = main(["unparseable-input", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE)])
    assert exit_code == 2
    _out, err = capsys.readouterr()
    assert "Error: Could not parse pull request number from: 'unparseable-input'" in err


def test_cli_main_pr_not_found_in_fixture(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI with non-existent PR returns exit code 1."""
    exit_code = main(["999999", "--fixture", str(_NOT_FOUND_FIXTURE)])
    assert exit_code == 1
    _out, err = capsys.readouterr()
    assert "Error: Pull request #999999 not found in repository." in err


def test_ci_timings_pr_flag_integration(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ci_timings.py --pr delegates to gh_merge_queue_status."""
    exit_code = ci_timings_main(["--pr", "7814", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE), "--json"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    data = json.loads(out)
    assert data["queued"] is True
    assert data["position"] == 2


def test_ci_timings_pr_line_flag_integration(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ci_timings.py --pr --line delegates and emits single line."""
    exit_code = ci_timings_main(["--pr", "7814", "--fixture", str(_QUEUED_IN_PROGRESS_FIXTURE), "--line"])
    assert exit_code == 0
    out, err = capsys.readouterr()
    assert not err
    assert (
        out.strip()
        == "PR #7814: queued=yes, position=2 (QUEUED, ~10 min ETA), run=https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/12345678"
    )


def test_fetch_live_status_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify live GraphQL error handling when gh CLI fails or outputs errors."""

    def fake_subprocess_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "graphql" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout='{"data": {"repository": {"pullRequest": null}}, "errors": [{"message": "Could not resolve to a PullRequest with the number of 123."}]}',
                stderr="gh error",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    with pytest.raises(ValueError, match="Pull request #123 not found in repository"):
        fetch_live_status(123, "learn-ukrainian/learn-ukrainian.github.io")


def test_evaluate_status_check_suites_filters_event_and_picks_latest() -> None:
    """P1: checkSuites on headCommit must filter event=merge_group and pick latest by timestamp."""
    payload = {
        "data": {
            "repository": {
                "pullRequest": {
                    "number": 7814,
                    "state": "OPEN",
                    "merged": False,
                    "mergeStateStatus": "CLEAN",
                    "isInMergeQueue": True,
                    "mergeQueueEntry": {
                        "position": 1,
                        "state": "QUEUED",
                        "enqueuedAt": "2026-09-08T18:00:00Z",
                        "estimatedTimeToMerge": 300,
                        "headCommit": {
                            "oid": "2cc5a531afe3b14e49db60ffbc7639ebd849dd26",
                            "checkSuites": {
                                "nodes": [
                                    {
                                        # Stale pull_request run (earlier in list, newer timestamp)
                                        "status": "completed",
                                        "conclusion": "failure",
                                        "createdAt": "2026-09-08T18:30:00Z",
                                        "workflowRun": {
                                            "id": 101,
                                            "url": "https://github.com/actions/runs/pr-run-101",
                                            "event": "pull_request",
                                            "createdAt": "2026-09-08T18:30:00Z",
                                        },
                                    },
                                    {
                                        # Older merge_group run
                                        "status": "completed",
                                        "conclusion": "success",
                                        "createdAt": "2026-09-08T18:05:00Z",
                                        "workflowRun": {
                                            "id": 102,
                                            "url": "https://github.com/actions/runs/mq-run-102",
                                            "event": "merge_group",
                                            "createdAt": "2026-09-08T18:05:00Z",
                                        },
                                    },
                                    {
                                        # Latest merge_group run by timestamp
                                        "status": "in_progress",
                                        "conclusion": None,
                                        "createdAt": "2026-09-08T18:20:00Z",
                                        "workflowRun": {
                                            "id": 103,
                                            "url": "https://github.com/actions/runs/mq-run-103",
                                            "event": "merge_group",
                                            "createdAt": "2026-09-08T18:20:00Z",
                                        },
                                    },
                                ]
                            },
                        },
                    },
                }
            }
        }
    }

    status = evaluate_status_data(payload, 7814)
    assert status.latest_merge_group_run_url == "https://github.com/actions/runs/mq-run-103"
    assert status.latest_merge_group_run_status == "in_progress"
    assert status.latest_merge_group_run_conclusion is None
    assert "run=https://github.com/actions/runs/mq-run-103" in status.summary_line


def test_evaluate_status_graphql_null_data_with_errors() -> None:
    """P2: GraphQL payloads with data=null and errors must not raise AttributeError."""
    # 1. Arbitrary GraphQL error with data=null
    err_payload = {
        "data": None,
        "errors": [
            {
                "message": "Field 'bad_field' does not exist on type 'Repository'",
                "locations": [{"line": 2, "column": 5}],
            }
        ],
    }
    with pytest.raises(RuntimeError, match=r"GraphQL error: Field 'bad_field' does not exist"):
        evaluate_status_data(err_payload, 7814)

    # 2. PR not found error with data=null
    not_found_payload = {
        "data": None,
        "errors": [
            {
                "message": "Could not resolve to a PullRequest with the number of 9999.",
            }
        ],
    }
    with pytest.raises(ValueError, match="Pull request #9999 not found in repository"):
        evaluate_status_data(not_found_payload, 9999)

    # 3. data=null without errors
    empty_payload = {"data": None}
    with pytest.raises(ValueError, match="Pull request #7814 not found in repository"):
        evaluate_status_data(empty_payload, 7814)

    # 4. repository=null with errors
    repo_null_payload = {
        "data": {"repository": None},
        "errors": [{"message": "Repository not found or access denied"}],
    }
    with pytest.raises(RuntimeError, match="GraphQL error: Repository not found or access denied"):
        evaluate_status_data(repo_null_payload, 7814)


def test_fetch_live_status_null_data_with_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """P2: fetch_live_status must not AttributeError when GraphQL returns data=null."""

    def fake_subprocess_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "graphql" in cmd:
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout='{"data": null, "errors": [{"message": "API rate limit exceeded for user."}]}',
                stderr="rate limit",
            )
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_subprocess_run)

    with pytest.raises(RuntimeError, match="GraphQL error: API rate limit exceeded"):
        fetch_live_status(7814, "learn-ukrainian/learn-ukrainian.github.io")


def test_cli_main_null_data_diagnostics(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """P2: CLI exits cleanly with diagnostic message/JSON when GraphQL returns data=null with errors."""
    fixture_file = tmp_path / "null_data_error.json"
    fixture_file.write_text(
        json.dumps(
            {
                "data": None,
                "errors": [
                    {
                        "message": "GraphQL syntax error near token",
                        "locations": [{"line": 1, "column": 1}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    # Default output mode: exits 1, prints diagnostic to stderr, no AttributeError
    exit_code = main(["7814", "--fixture", str(fixture_file)])
    assert exit_code == 1
    out, err = capsys.readouterr()
    assert not out
    assert "Error: GraphQL error: GraphQL syntax error near token" in err
    assert "AttributeError" not in err

    # --json mode: exits 1, emits structured diagnostic JSON to stdout
    exit_code_json = main(["7814", "--fixture", str(fixture_file), "--json"])
    assert exit_code_json == 1
    out_json, err_json = capsys.readouterr()
    assert not err_json
    data = json.loads(out_json)
    assert data["status"] == "error"
    assert data["pr_number"] == 7814
    assert "GraphQL error: GraphQL syntax error near token" in data["error"]
    assert len(data["errors"]) == 1
