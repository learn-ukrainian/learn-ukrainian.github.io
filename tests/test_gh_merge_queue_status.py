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

import copy
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

    # Patch the typed read the function calls. Patching subprocess.run never reached it: the real
    # client answered with its own refusal and the "not found" below was produced by that refusal.
    monkeypatch.setattr(
        "scripts.gh_merge_queue_status.read", lambda *a, **kw: fake_subprocess_run(["gh", "api", "graphql"])
    )

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

    monkeypatch.setattr("scripts.gh_merge_queue_status.read", lambda *a, **kw: fake_subprocess_run(["gh", "api", "graphql"]))

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


@pytest.fixture(autouse=True)
def _publisher_transport(publisher_transport):
    """Inject the subprocess spy into typed GitHub read transport."""


_REFUSALS = {
    "rate_refusal_reset_only": (75, json.dumps({"error": "github_rate_limited", "reset_at": 1790000000})),
    "generic_non_zero": (1, json.dumps({"error": "github_http_error", "reset_at": None, "status": 502})),
    "empty_output": (0, ""),
    "malformed_output": (0, "not json"),
    "refusal_json_with_zero_rc": (0, json.dumps({"error": "github_rate_limited", "reset_at": None})),
}
_REPO = "learn-ukrainian/learn-ukrainian.github.io"
_FOUND = {
    "data": {
        "repository": {
            "pullRequest": {"number": 123, "state": "OPEN", "merged": False, "isInMergeQueue": False},
            "mergeQueue": None,
        }
    }
}


def _live(monkeypatch: pytest.MonkeyPatch, graphql: tuple[int, str], runs: list[tuple[int, str]]) -> list[list[str]]:
    """Canned graphql read and ordered Actions-run reads; returns the later lookups issued."""
    lookups: list[list[str]] = []

    def read_stub(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["gh", "api", "graphql"], graphql[0], graphql[1], "")

    def run_stub(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        lookups.append(cmd)
        code, out = runs[min(len(lookups), len(runs)) - 1]
        return subprocess.CompletedProcess(cmd, code, out, "")

    monkeypatch.setattr("scripts.gh_merge_queue_status.read", read_stub)
    monkeypatch.setattr("scripts.gh_merge_queue_status.github_client.run", run_stub)
    return lookups


@pytest.mark.parametrize("shape", _REFUSALS)
def test_refused_graphql_read_is_unavailable_not_pr_not_found(
    monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    lookups = _live(monkeypatch, _REFUSALS[shape], [(0, '{"workflow_runs": []}')])
    with pytest.raises(RuntimeError, match=r"unavailable|Failed to parse") as excinfo:
        fetch_live_status(123, _REPO)
    assert "not found" not in str(excinfo.value)
    assert lookups == []  # no Actions lookup after the refusal


@pytest.mark.parametrize("shape", _REFUSALS)
def test_refused_runs_read_is_unavailable_not_empty_and_has_no_fallback(
    monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [_REFUSALS[shape], (0, "[]")])
    with pytest.raises(RuntimeError, match="unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 1  # the `gh run list` fallback is never attempted


def test_refused_fallback_run_list_is_unavailable_not_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    lookups = _live(
        monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), _REFUSALS["rate_refusal_reset_only"]]
    )
    with pytest.raises(RuntimeError, match="Actions run list read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 2


def test_cli_reports_unavailable_read_as_error_not_pr_not_found(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _live(monkeypatch, _REFUSALS["rate_refusal_reset_only"], [])
    assert main(["123", "--repo", _REPO, "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "unavailable" in payload["error"]
    assert "not found" not in payload["error"]


def test_successful_live_reads_are_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    run = {"url": "https://example.invalid/run/1", "status": "completed", "conclusion": "success"}
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, json.dumps({"workflow_runs": [run]}))])
    status = fetch_live_status(123, _REPO)
    assert (status.pr_number, status.queued, status.pr_state) == (123, False, "OPEN")
    assert len(lookups) == 1
    # An empty (successful) runs list still falls back to the run list, as before.
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), (0, json.dumps([run]))])
    assert fetch_live_status(123, _REPO).pr_number == 123
    assert len(lookups) == 2


_NOT_FOUND_ERROR = [{"type": "NOT_FOUND", "message": "Could not resolve to a PullRequest with the number of 123."}]


@pytest.mark.parametrize(
    "stdout",
    [
        json.dumps(_FOUND),  # complete-shaped data, but the read failed
        json.dumps({"data": None}),
        json.dumps({"data": {"repository": {"pullRequest": None}}}),
        json.dumps({**_FOUND, "errors": [{"message": "API rate limit exceeded for user."}]}),
    ],
)
def test_failed_graphql_read_with_envelope_is_rejected_before_any_request(
    monkeypatch: pytest.MonkeyPatch, stdout: str
) -> None:
    """Return code 1 plus a data envelope once passed, or became "not found" after more requests."""
    lookups = _live(monkeypatch, (1, stdout), [(0, '{"workflow_runs": []}')])
    with pytest.raises(RuntimeError, match=r"unavailable|GraphQL error") as excinfo:
        fetch_live_status(123, _REPO)
    assert "not found" not in str(excinfo.value)
    assert lookups == []


def test_positively_identified_not_found_keeps_its_meaning_with_no_further_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"data": {"repository": {"pullRequest": None}}, "errors": _NOT_FOUND_ERROR}
    lookups = _live(monkeypatch, (1, json.dumps(payload)), [(0, '{"workflow_runs": []}')])
    with pytest.raises(ValueError, match="Pull request #123 not found in repository"):
        fetch_live_status(123, _REPO)
    assert lookups == []


def test_not_found_error_cannot_discard_a_resolved_pull_request(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {**_FOUND, "errors": _NOT_FOUND_ERROR}
    lookups = _live(monkeypatch, (1, json.dumps(payload)), [(0, '{"workflow_runs": []}')])
    with pytest.raises(RuntimeError, match="GraphQL error"):
        fetch_live_status(123, _REPO)
    assert lookups == []


def test_successful_empty_envelope_is_unavailable_not_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    lookups = _live(monkeypatch, (0, json.dumps({"data": None})), [(0, '{"workflow_runs": []}')])
    with pytest.raises(RuntimeError, match="GraphQL read unavailable") as excinfo:
        fetch_live_status(123, _REPO)
    assert "not found" not in str(excinfo.value)
    assert lookups == []


_MALFORMED_RUNS = {
    "empty_element": {"workflow_runs": [{}]},
    "null_element": {"workflow_runs": [None]},
    "scalar_element": {"workflow_runs": ["x"]},
    "no_status": {"workflow_runs": [{"html_url": "https://example.invalid/run/1"}]},
    "no_url": {"workflow_runs": [{"status": "completed"}]},
    "one_bad_among_good": {
        "workflow_runs": [{"html_url": "https://example.invalid/run/1", "status": "completed"}, {}]
    },
}


@pytest.mark.parametrize("shape", _MALFORMED_RUNS)
def test_malformed_run_elements_are_unavailable_not_run_none(monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, json.dumps(_MALFORMED_RUNS[shape])), (0, "[]")])
    with pytest.raises(RuntimeError, match="Actions runs read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 1  # no run-list fallback after a malformed read


def test_malformed_fallback_run_list_elements_are_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), (0, "[{}]")])
    with pytest.raises(RuntimeError, match="Actions run list read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 2


@pytest.mark.parametrize("failure", [subprocess.TimeoutExpired("gh", 30), PermissionError("gh")])
def test_process_failures_are_structured_unavailable_outcomes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], failure: Exception
) -> None:
    def broken(*args: Any, **kwargs: Any) -> Any:
        raise failure

    monkeypatch.setattr("scripts.gh_merge_queue_status.read", broken)
    assert main(["123", "--repo", _REPO, "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"

    _live(monkeypatch, (0, json.dumps(_FOUND)), [])
    monkeypatch.setattr("scripts.gh_merge_queue_status.github_client.run", broken)
    assert main(["123", "--repo", _REPO, "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"


# --- Round 3: one strict parse-or-unavailable choke point per payload kind (#10792) -------------
#
# The GraphQL document and the Actions run lists are each validated by whitelist in one place; the
# live read, the offline fixture evaluator and the run-list fallback all consume them through it.
# The matrices cross payload kind x malformation and assert the unavailable outcome AND that no
# further request was made.


def _pr(**overrides: Any) -> dict[str, Any]:
    pull: dict[str, Any] = {
        "number": 123,
        "state": "OPEN",
        "merged": False,
        "mergeStateStatus": "CLEAN",
        "isInMergeQueue": False,
    }
    pull.update(overrides)
    return pull


def _doc(pull: Any = None, queue: Any = None, **extra: Any) -> dict[str, Any]:
    repository = {"pullRequest": _pr() if pull is None else pull, "mergeQueue": queue}
    return {"data": {"repository": repository}, **extra}


def _without(pull: dict[str, Any], key: str) -> dict[str, Any]:
    return {k: v for k, v in pull.items() if k != key}


_ENTRY = {"position": 2, "state": "QUEUED", "enqueuedAt": "2026-09-08T18:00:00Z", "estimatedTimeToMerge": 600}
_SUITE = {"status": "completed", "conclusion": "success", "workflowRun": {"url": "https://example.invalid/r/1"}}
_QUEUE = {"url": "https://example.invalid/q", "nextEntryEstimatedTimeToMerge": 300, "entries": {"nodes": []}}


def _queued(entry: Any = ..., **overrides: Any) -> dict[str, Any]:
    return _pr(isInMergeQueue=True, mergeQueueEntry=_ENTRY if entry is ... else entry, **overrides)


def _with_suites(*nodes: Any, head: Any = ...) -> dict[str, Any]:
    commit = {"oid": "a" * 40, "checkSuites": {"nodes": list(nodes)}} if head is ... else head
    return _queued({**_ENTRY, "headCommit": commit})


_BAD_GRAPHQL: dict[str, Any] = {
    # the exact shapes from the review
    "repository_empty_object": {"data": {"repository": {}}},
    "pull_request_empty_list": {"data": {"repository": {"pullRequest": []}}},
    "pull_request_empty_object": {"data": {"repository": {"pullRequest": {}}}},
    # containers
    "document_list": [],
    "document_null": None,
    "document_string": "x",
    "data_list": {"data": []},
    "data_string": {"data": "x"},
    "repository_list": {"data": {"repository": []}},
    "repository_null": {"data": {"repository": None}},
    "repository_string": {"data": {"repository": "x"}},
    "pull_request_missing": {"data": {"repository": {"mergeQueue": None}}},
    "pull_request_null_without_errors": {"data": {"repository": {"pullRequest": None}}},
    "pull_request_string": {"data": {"repository": {"pullRequest": "x"}}},
    "pull_request_list_of_valid": _doc([_pr()]),
    "pull_request_true": _doc(True),
    "pull_request_list_with_not_found_error": {
        "data": {"repository": {"pullRequest": []}},
        "errors": [{"message": "Could not resolve to a PullRequest with the number of 123."}],
    },
    "errors_not_a_list": _doc(errors="boom"),
    "errors_nested_object": _doc(errors={"message": "x"}),
    "errors_with_a_resolved_pull_request": _doc(errors=[{"message": "partial failure"}]),
    "errors_without_message": _doc(errors=[{"type": "X"}]),
    # required keys: missing, null, wrong type, bool-as-int, out of domain
    **{f"missing_{k}": _doc(_without(_pr(), k)) for k in ("number", "state", "merged", "isInMergeQueue")},
    "number_null": _doc(_pr(number=None)),
    "number_zero": _doc(_pr(number=0)),
    "number_negative": _doc(_pr(number=-1)),
    "number_string": _doc(_pr(number="123")),
    "number_bool": _doc(_pr(number=True)),
    "number_for_another_pull_request": _doc(_pr(number=124)),
    "state_null": _doc(_pr(state=None)),
    "state_int": _doc(_pr(state=1)),
    "state_lowercase": _doc(_pr(state="open")),
    "state_unknown": _doc(_pr(state="DRAFT")),
    "state_empty": _doc(_pr(state="")),
    "merged_null": _doc(_pr(merged=None)),
    "merged_string": _doc(_pr(merged="false")),
    "merged_int": _doc(_pr(merged=0)),
    "merged_with_open_state": _doc(_pr(merged=True, state="OPEN")),
    "merged_state_without_merged": _doc(_pr(merged=False, state="MERGED")),
    "in_queue_null": _doc(_pr(isInMergeQueue=None)),
    "in_queue_string": _doc(_pr(isInMergeQueue="true")),
    "in_queue_int": _doc(_pr(isInMergeQueue=1)),
    "merge_state_status_int": _doc(_pr(mergeStateStatus=5)),
    "merge_state_status_list": _doc(_pr(mergeStateStatus=["CLEAN"])),
    # the queue entry
    "entry_list": _doc(_queued([])),
    "entry_string": _doc(_queued("x")),
    "entry_without_membership": _doc(_pr(mergeQueueEntry=_ENTRY)),
    "entry_position_zero": _doc(_queued({**_ENTRY, "position": 0})),
    "entry_position_negative": _doc(_queued({**_ENTRY, "position": -1})),
    "entry_position_bool": _doc(_queued({**_ENTRY, "position": True})),
    "entry_position_string": _doc(_queued({**_ENTRY, "position": "2"})),
    "entry_position_float": _doc(_queued({**_ENTRY, "position": 2.0})),
    "entry_state_int": _doc(_queued({**_ENTRY, "state": 2})),
    "entry_state_empty": _doc(_queued({**_ENTRY, "state": ""})),
    "entry_enqueued_at_int": _doc(_queued({**_ENTRY, "enqueuedAt": 5})),
    "entry_eta_negative": _doc(_queued({**_ENTRY, "estimatedTimeToMerge": -1})),
    "entry_eta_bool": _doc(_queued({**_ENTRY, "estimatedTimeToMerge": True})),
    "entry_eta_string": _doc(_queued({**_ENTRY, "estimatedTimeToMerge": "600"})),
    "entry_head_commit_list": _doc(_queued({**_ENTRY, "headCommit": []})),
    "entry_check_suites_list": _doc(_queued({**_ENTRY, "headCommit": {"checkSuites": []}})),
    "entry_check_suite_nodes_object": _doc(_queued({**_ENTRY, "headCommit": {"checkSuites": {"nodes": {}}}})),
    "entry_check_suite_node_null": _doc(_with_suites(None)),
    "entry_check_suite_node_string": _doc(_with_suites("x")),
    "entry_check_suite_good_then_null": _doc(_with_suites(_SUITE, None)),
    "entry_check_suite_status_int": _doc(_with_suites({**_SUITE, "status": 1})),
    "entry_check_suite_conclusion_int": _doc(_with_suites({**_SUITE, "conclusion": 1})),
    "entry_check_suite_run_list": _doc(_with_suites({**_SUITE, "workflowRun": []})),
    "entry_check_suite_run_without_url": _doc(_with_suites({**_SUITE, "workflowRun": {"event": "merge_group"}})),
    "entry_check_suite_run_url_int": _doc(_with_suites({**_SUITE, "workflowRun": {"url": 5}})),
    "entry_check_suite_run_event_int": _doc(
        _with_suites({**_SUITE, "workflowRun": {"url": "https://example.invalid/r/1", "event": 5}})
    ),
    # the repository merge queue
    "merge_queue_list": _doc(queue=[]),
    "merge_queue_string": _doc(queue="x"),
    "merge_queue_url_int": _doc(queue={**_QUEUE, "url": 5}),
    "merge_queue_next_eta_negative": _doc(queue={**_QUEUE, "nextEntryEstimatedTimeToMerge": -1}),
    "merge_queue_next_eta_bool": _doc(queue={**_QUEUE, "nextEntryEstimatedTimeToMerge": True}),
    "merge_queue_entries_list": _doc(queue={**_QUEUE, "entries": []}),
    "merge_queue_nodes_object": _doc(queue={**_QUEUE, "entries": {"nodes": {}}}),
    "merge_queue_node_null": _doc(queue={**_QUEUE, "entries": {"nodes": [None]}}),
    "merge_queue_node_pull_list": _doc(queue={**_QUEUE, "entries": {"nodes": [{"pullRequest": []}]}}),
    "merge_queue_node_pull_number_zero": _doc(
        queue={**_QUEUE, "entries": {"nodes": [{**_ENTRY, "pullRequest": {"number": 0}}]}}
    ),
    "merge_queue_node_pull_number_bool": _doc(
        queue={**_QUEUE, "entries": {"nodes": [{**_ENTRY, "pullRequest": {"number": True}}]}}
    ),
    "merge_queue_node_position_negative": _doc(
        queue={**_QUEUE, "entries": {"nodes": [{**_ENTRY, "position": -3, "pullRequest": {"number": 9}}]}}
    ),
}


@pytest.mark.parametrize("shape", _BAD_GRAPHQL)
def test_graphql_matrix_is_unavailable_before_any_further_request(monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
    """``{"data":{"repository":{}}}``, ``pullRequest=[]`` and ``pullRequest={}`` once ended as
    "not found" after two more requests, or as "queued=no (state=OPEN), run=none"."""
    lookups = _live(monkeypatch, (0, json.dumps(_BAD_GRAPHQL[shape])), [(0, '{"workflow_runs": []}'), (0, "[]")])
    with pytest.raises(RuntimeError, match=r"unavailable|GraphQL error") as excinfo:
        fetch_live_status(123, _REPO)
    assert "not found" not in str(excinfo.value)
    assert lookups == []


@pytest.mark.parametrize("shape", _BAD_GRAPHQL)
def test_graphql_matrix_is_unavailable_in_the_offline_evaluator_too(shape: str) -> None:
    with pytest.raises(RuntimeError) as excinfo:
        evaluate_status_data(_BAD_GRAPHQL[shape], 123)
    assert "not found" not in str(excinfo.value)


@pytest.mark.parametrize("shape", ["repository_empty_object", "pull_request_empty_list", "pull_request_empty_object"])
def test_graphql_review_shapes_exit_nonzero_from_a_fixture_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], shape: str
) -> None:
    fixture = tmp_path / "doc.json"
    fixture.write_text(json.dumps(_BAD_GRAPHQL[shape]))
    assert main(["123", "--fixture", str(fixture), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "not found" not in payload["error"]
    assert "queued=no" not in payload["error"]


@pytest.mark.parametrize("failed_rc", [1, 75])
@pytest.mark.parametrize("shape", ["repository_empty_object", "pull_request_empty_list", "pull_request_empty_object"])
def test_graphql_review_shapes_with_a_failed_read_are_unavailable_too(
    monkeypatch: pytest.MonkeyPatch, shape: str, failed_rc: int
) -> None:
    lookups = _live(monkeypatch, (failed_rc, json.dumps(_BAD_GRAPHQL[shape])), [(0, '{"workflow_runs": []}')])
    with pytest.raises(RuntimeError) as excinfo:
        fetch_live_status(123, _REPO)
    assert "not found" not in str(excinfo.value)
    assert lookups == []


_GOOD_GRAPHQL: dict[str, tuple[dict[str, Any], str]] = {
    "open_not_queued": (_doc(), "PR #123: queued=no (state=OPEN, mergeStateStatus=CLEAN), run=none"),
    "queued_with_entry": (
        _doc(_queued(), queue=_QUEUE),
        "PR #123: queued=yes, position=2 (QUEUED, ~10 min ETA), run=none",
    ),
    "queued_position_resolved_from_the_queue_nodes": (
        _doc(
            _pr(isInMergeQueue=True),
            queue={**_QUEUE, "entries": {"nodes": [{**_ENTRY, "position": 4, "pullRequest": {"number": 123}}]}},
        ),
        "PR #123: queued=yes, position=4 (QUEUED, ~10 min ETA), run=none",
    ),
    "queued_position_unknown": (
        _doc(_pr(isInMergeQueue=True), queue=_QUEUE),
        "PR #123: queued=yes, position=unknown (in queue, position unknown), run=none",
    ),
    "merged": (
        _doc(_pr(merged=True, state="MERGED", mergeStateStatus="UNKNOWN")),
        "PR #123: queued=no (merged=yes, state=MERGED), run=none",
    ),
    "closed": (_doc(_pr(state="CLOSED")), "PR #123: queued=no (state=CLOSED), run=none"),
    "merge_queue_absent": ({"data": {"repository": {"pullRequest": _pr()}}}, None),
    "nullable_optional_fields": (_doc(_pr(mergeStateStatus=None, mergeQueueEntry=None), queue=None), None),
    "empty_errors_list": (_doc(errors=[]), None),
    "null_errors": (_doc(errors=None), None),
}


@pytest.mark.parametrize("shape", _GOOD_GRAPHQL)
def test_well_formed_graphql_documents_keep_their_meaning(shape: str) -> None:
    document, line = _GOOD_GRAPHQL[shape]
    status = evaluate_status_data(copy.deepcopy(document), 123)
    assert status.pr_number == 123
    if line is not None:
        assert status.summary_line == line


def test_well_formed_check_suite_run_is_reported() -> None:
    suite = {**_SUITE, "workflowRun": {"url": "https://example.invalid/r/1", "event": "merge_group"}}
    status = evaluate_status_data(_doc(_with_suites(suite)), 123)
    assert status.latest_merge_group_run_url == "https://example.invalid/r/1"
    assert status.latest_merge_group_run_status == "completed"
    status = evaluate_status_data(_doc(_with_suites({"status": "queued", "workflowRun": None})), 123)
    assert status.latest_merge_group_run_url is None


def test_legacy_bare_null_data_fixture_keeps_its_not_found_contract() -> None:
    """The one recorded offline contract kept as is; the live read never reaches it (it is unavailable)."""
    with pytest.raises(ValueError, match="Pull request #7814 not found in repository"):
        evaluate_status_data({"data": None}, 7814)


_RUN = {"html_url": "https://example.invalid/run/1", "status": "completed", "conclusion": "success"}

_BAD_RUN_ELEMENTS: dict[str, Any] = {
    "empty_object": {},
    "null": None,
    "string": "x",
    "list": [],
    "int": 5,
    "no_url": {"status": "completed"},
    "no_status": {"html_url": "https://example.invalid/run/1"},
    "url_empty": {**_RUN, "html_url": ""},
    "url_int": {**_RUN, "html_url": 5},
    "url_list": {**_RUN, "html_url": ["https://example.invalid/run/1"]},
    "status_null": {**_RUN, "status": None},
    "status_int": {**_RUN, "status": 1},
    "status_empty": {**_RUN, "status": ""},
    "conclusion_int": {**_RUN, "conclusion": 1},
    "conclusion_list": {**_RUN, "conclusion": ["success"]},
    "event_int": {**_RUN, "event": 5},
    "head_branch_int": {**_RUN, "head_branch": 5},
    "head_branch_camel_list": {**_RUN, "headBranch": []},
    "name_int": {**_RUN, "name": 5},
    "created_at_int": {**_RUN, "created_at": 5},
    "created_at_camel_int": {**_RUN, "createdAt": 5},
    "id_bool": {**_RUN, "id": True},
    "id_negative": {**_RUN, "id": -1},
    "id_list": {**_RUN, "id": [1]},
}


@pytest.mark.parametrize("shape", _BAD_RUN_ELEMENTS)
def test_run_element_matrix_in_the_rest_list_is_unavailable_with_no_fallback(
    monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    runs = {"workflow_runs": [_RUN, _BAD_RUN_ELEMENTS[shape]]}  # one bad element spoils the whole read
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, json.dumps(runs)), (0, "[]")])
    with pytest.raises(RuntimeError, match="Actions runs read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 1


@pytest.mark.parametrize("shape", _BAD_RUN_ELEMENTS)
def test_run_element_matrix_in_the_fallback_list_is_unavailable(monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
    lookups = _live(
        monkeypatch,
        (0, json.dumps(_FOUND)),
        [(0, '{"workflow_runs": []}'), (0, json.dumps([_RUN, _BAD_RUN_ELEMENTS[shape]]))],
    )
    with pytest.raises(RuntimeError, match="Actions run list read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 2


_BAD_RUN_CONTAINERS: dict[str, Any] = {
    "list_for_the_rest_object": [_RUN],
    "json_null": None,
    "string": "x",
    "int": 5,
    "empty_object": {},
    "key_missing": {"runs": [_RUN]},
    "key_null": {"workflow_runs": None},
    "key_object": {"workflow_runs": {}},
    "key_string": {"workflow_runs": "[]"},
    "nested_error_object": {"error": {"message": "x"}},
}


@pytest.mark.parametrize("shape", _BAD_RUN_CONTAINERS)
def test_run_container_matrix_in_the_rest_read_is_unavailable_with_no_fallback(
    monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, json.dumps(_BAD_RUN_CONTAINERS[shape])), (0, "[]")])
    with pytest.raises(RuntimeError, match="Actions runs read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 1


@pytest.mark.parametrize("shape", ["json_null", "string", "int", "empty_object", "key_object", "nested_error_object"])
def test_run_container_matrix_in_the_fallback_read_is_unavailable(
    monkeypatch: pytest.MonkeyPatch, shape: str
) -> None:
    payload = {"workflow_runs": []} if shape == "key_object" else _BAD_RUN_CONTAINERS[shape]
    lookups = _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), (0, json.dumps(payload))])
    with pytest.raises(RuntimeError, match="Actions run list read unavailable"):
        fetch_live_status(123, _REPO)
    assert len(lookups) == 2


def test_well_formed_runs_of_every_accepted_spelling_keep_their_meaning(monkeypatch: pytest.MonkeyPatch) -> None:
    camel = {
        "url": "https://example.invalid/run/2",
        "status": "in_progress",
        "conclusion": None,
        "headBranch": "gh-readonly-queue/main/pr-123-abc",
        "createdAt": "2026-09-08T18:00:00Z",
        "name": "CI",
        "event": "merge_group",
    }
    rest = {**_RUN, "id": 9, "head_branch": "gh-readonly-queue/main/pr-123-abc", "created_at": "2026-09-08T18:30:00Z"}
    _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, json.dumps({"workflow_runs": [rest]}))])
    assert fetch_live_status(123, _REPO).latest_merge_group_run_url == "https://example.invalid/run/1"
    _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), (0, json.dumps([camel]))])
    assert fetch_live_status(123, _REPO).latest_merge_group_run_url == "https://example.invalid/run/2"
    _live(monkeypatch, (0, json.dumps(_FOUND)), [(0, '{"workflow_runs": []}'), (0, "[]")])
    assert fetch_live_status(123, _REPO).latest_merge_group_run_url is None


@pytest.mark.parametrize(
    ("runs_fixture", "key"),
    [
        ({"workflow_runs": [{}]}, "actions"),
        ({"runs": [None]}, "actions"),
        ({"other": []}, "actions"),
        ({"workflow_runs": {}}, "actions"),
        ({"workflow_runs": "x"}, "actions"),
        ([{}], "actions"),
        (["x"], "actions"),
        (None, "actions"),
        ("x", "actions"),
        (5, "actions"),
        ([{}], "embedded"),
        ({}, "embedded"),
        (None, "embedded"),
        ("x", "embedded"),
        (5, "embedded"),
        ([None], "embedded"),
    ],
)
def test_offline_run_fixtures_are_validated_like_live_runs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], runs_fixture: Any, key: str
) -> None:
    graphql = tmp_path / "doc.json"
    argv = ["123", "--fixture", str(graphql), "--json"]
    if key == "actions":
        graphql.write_text(json.dumps(_doc()))
        runs = tmp_path / "runs.json"
        runs.write_text(json.dumps(runs_fixture))
        argv += ["--actions-fixture", str(runs)]
    else:
        graphql.write_text(json.dumps({**_doc(), "actions_runs": runs_fixture}))
    assert main(argv) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "error"


def test_offline_run_fixtures_that_are_well_formed_still_evaluate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    graphql = tmp_path / "doc.json"
    graphql.write_text(json.dumps({**_doc(), "actions_runs": []}))
    assert main(["123", "--fixture", str(graphql), "--line"]) == 0
    assert "queued=no" in capsys.readouterr().out
    runs = tmp_path / "runs.json"
    runs.write_text(json.dumps({"runs": [_RUN]}))
    assert main(["123", "--fixture", str(graphql), "--actions-fixture", str(runs), "--line"]) == 0
