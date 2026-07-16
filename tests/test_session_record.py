from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

from scripts.lib.session_record import (
    PROJECT_ROOT,
    SessionRecordError,
    append_to_env_file,
    canonical_state_root,
    get_record_path,
    read_record,
    update_session,
    validate_session_id,
    validate_transcript_path,
    write_record,
)


def test_canonical_state_root_uses_git_common_directory() -> None:
    result = subprocess.run(
        [
            "git",
            "-C",
            os.fspath(PROJECT_ROOT),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert canonical_state_root(PROJECT_ROOT) == Path(result.stdout.strip()).parent.resolve()


@pytest.mark.parametrize("session_id", ["abc-123", "thread_name", "A" * 128])
def test_validate_session_id_accepts_bounded_safe_identifiers(session_id: str) -> None:
    assert validate_session_id(session_id)


@pytest.mark.parametrize("session_id", ["", "../other", "has space", "A" * 129])
def test_validate_session_id_rejects_unsafe_identifiers(session_id: str) -> None:
    assert not validate_session_id(session_id)


def test_validate_transcript_path_requires_absolute_non_traversing_path() -> None:
    assert validate_transcript_path("/tmp/claude/session.jsonl")
    assert not validate_transcript_path("relative/session.jsonl")
    assert not validate_transcript_path("/tmp/../secret.jsonl")
    assert not validate_transcript_path("/tmp/bad\x00name.jsonl")


def test_update_session_writes_private_atomic_sol_record(tmp_path: Path) -> None:
    transcript = tmp_path / "Claude Sessions" / "sol.jsonl"
    record = update_session(
        "sol-session",
        transcript_path=os.fspath(transcript),
        source="startup",
        observed_model="gpt-5.6-sol",
        agent_type="infra-orchestrator",
        profile_id="sol_lead",
        provenance="session-start",
        transcript_path_provenance="session-start.transcript_path",
        observed_model_provenance="session-start.model",
        state_root=tmp_path,
    )
    path = get_record_path("sol-session", state_root=tmp_path)

    assert path.is_file()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert not list(path.parent.glob("*.tmp"))
    assert record["effective_profile_id"] == "sol_lead"
    assert record["effective_context_window_tokens"] == 372_000
    assert record["auto_compact_capacity_tokens"] == 353_000
    assert record["actual_context_window_tokens"] == 372_000
    assert record["actual_context_window_provenance"] == "declared-profile"
    assert record["transcript_path"] == os.fspath(transcript)
    assert record["transcript_path_provenance"] == "session-start.transcript_path"
    assert record["observed_model_provenance"] == "session-start.model"
    assert record["created_at"].endswith("Z") and "+00:00Z" not in record["created_at"]
    assert read_record("sol-session", state_root=tmp_path) == record


def test_observed_statusline_window_wins_and_records_mismatch(tmp_path: Path) -> None:
    update_session(
        "native-session",
        observed_model="claude-opus-4-8",
        profile_id="native_claude",
        provenance="session-start",
        state_root=tmp_path,
    )
    record = update_session(
        "native-session",
        observed_context_window=900_000,
        provenance="statusline",
        observed_context_window_provenance="statusline.context_window.context_window_size",
        state_root=tmp_path,
    )

    assert record["expected_context_window_tokens"] == 1_000_000
    assert record["observed_context_window_tokens"] == 900_000
    assert record["actual_context_window_tokens"] == 900_000
    assert record["actual_context_window_provenance"].startswith("statusline.")
    assert record["window_mismatch"]
    assert not record["model_mismatch"]


def test_missing_or_mismatched_route_fails_closed(tmp_path: Path) -> None:
    missing = update_session(
        "missing-route",
        observed_model="gpt-5.6-sol",
        provenance="session-start",
        state_root=tmp_path,
    )
    mismatch = update_session(
        "mismatch-route",
        observed_model="gpt-5.6-sol",
        profile_id="native_claude",
        provenance="session-start",
        state_root=tmp_path,
    )

    assert missing["effective_profile_id"] == "fallback"
    assert missing["actual_context_window_tokens"] is None
    assert missing["actual_context_window_provenance"] == "unavailable"
    assert mismatch["effective_profile_id"] == "fallback"
    assert mismatch["expected_context_window_tokens"] == 1_000_000
    assert mismatch["effective_context_window_tokens"] == 0
    assert mismatch["actual_context_window_tokens"] is None
    assert mismatch["model_mismatch"]


def test_corrupt_record_is_loud_instead_of_treated_as_missing(tmp_path: Path) -> None:
    path = get_record_path("broken", state_root=tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SessionRecordError, match="cannot read session record"):
        read_record("broken", state_root=tmp_path)


def test_record_writer_rejects_unapproved_secret_bearing_fields(tmp_path: Path) -> None:
    record = update_session(
        "safe-record",
        profile_id="sol_lead",
        provenance="launcher",
        state_root=tmp_path,
    )
    record["authorization"] = "must-not-persist"

    with pytest.raises(SessionRecordError, match="unsupported fields: authorization"):
        write_record("safe-record", record, state_root=tmp_path)


def test_update_session_rejects_relative_transcript_path(tmp_path: Path) -> None:
    with pytest.raises(SessionRecordError, match="must be an absolute path"):
        update_session(
            "relative-path",
            transcript_path="relative.jsonl",
            profile_id="sol_lead",
            state_root=tmp_path,
        )


def test_env_file_exports_are_shell_safe_and_project_private(tmp_path: Path) -> None:
    transcript = tmp_path / "session's transcript.jsonl"
    record = update_session(
        "quoted-session",
        transcript_path=os.fspath(transcript),
        observed_model="gpt-5.6-sol",
        profile_id="sol_lead",
        provenance="session-start",
        state_root=tmp_path,
    )
    env_file = tmp_path / "claude-env.sh"
    env_file.touch()
    append_to_env_file(record, env_file=env_file, state_root=tmp_path)
    contents = env_file.read_text(encoding="utf-8")

    assert "CLAUDE_SESSION_" not in contents
    assert "LEARN_UKRAINIAN_SESSION_ID" in contents
    assert "ANTHROPIC" not in contents
    result = subprocess.run(
        [
            "bash",
            "-c",
            'set -eu; source "$1"; printf "%s\\n%s\\n" '
            '"$LEARN_UKRAINIAN_SESSION_ID" "$LEARN_UKRAINIAN_TRANSCRIPT_PATH"',
            "_",
            os.fspath(env_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.splitlines() == ["quoted-session", os.fspath(transcript.resolve())]


def test_cli_round_trip_uses_explicit_state_root(tmp_path: Path) -> None:
    script = PROJECT_ROOT / "scripts" / "lib" / "session_record.py"
    update = subprocess.run(
        [
            os.fspath(PROJECT_ROOT / ".venv" / "bin" / "python"),
            os.fspath(script),
            "--state-root",
            os.fspath(tmp_path),
            "update",
            "--session-id",
            "cli-session",
            "--profile-id",
            "sol_lead",
            "--observed-model",
            "gpt-5.6-sol",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    get = subprocess.run(
        [
            os.fspath(PROJECT_ROOT / ".venv" / "bin" / "python"),
            os.fspath(script),
            "--state-root",
            os.fspath(tmp_path),
            "get",
            "--session-id",
            "cli-session",
            "--field",
            "actual_context_window_tokens",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(update.stdout)["effective_profile_id"] == "sol_lead"
    assert get.stdout.strip() == "372000"
