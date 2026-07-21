"""Per-session telemetry for Monitor API JSON responses."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.api.main import app
from scripts.api.telemetry import response as telemetry_response
from scripts.api.telemetry import transcript_tokens
from scripts.lib.session_record import update_session


def _write_transcript(path: Path, *, tokens: int = 187_000, prev: int = 125_000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": prev - 25_000,
                                "cache_read_input_tokens": 20_000,
                                "cache_creation_input_tokens": 5_000,
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "usage": {
                                "input_tokens": tokens - 37_000,
                                "cache_read_input_tokens": 30_000,
                                "cache_creation_input_tokens": 7_000,
                            }
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def telemetry_enabled(monkeypatch):
    monkeypatch.delenv("AGENT_NO_TELEMETRY_FOOTER", raising=False)
    monkeypatch.setenv("LEARN_UKRAINIAN_TELEMETRY_FOOTER", "1")
    monkeypatch.delenv("LEARN_UKRAINIAN_TRANSCRIPT_PATH", raising=False)
    monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
    # These hermetic roots are not Git repositories. Model the canonical primary
    # checkout as the supplied root; a separate regression below covers linked roots.
    monkeypatch.setattr(
        transcript_tokens, "canonical_state_root", lambda project_root: project_root
    )


def test_session_hit_returns_caller_match_telemetry(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    session_id = "abc-session-123"
    flat = str(project_root.resolve()).replace("/", "-")
    transcript = home / ".claude" / "projects" / flat / f"{session_id}.jsonl"
    _write_transcript(transcript)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get(f"/api/state/manifest?session={session_id}")

    assert response.status_code == 200
    telemetry = response.json()["_telemetry"]
    assert telemetry["ctx"] == 187_000
    assert telemetry["caller_match"] is True
    assert telemetry["transcript"] == f"{session_id}.jsonl"
    assert telemetry["source"] == "transcript-jsonl"


def test_session_record_drives_capacity_provenance_and_mismatch(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    session_id = "recorded-sol-session"
    transcript = tmp_path / "official transcripts" / "sol.jsonl"
    _write_transcript(transcript)
    update_session(
        session_id,
        transcript_path=str(transcript),
        observed_model="gpt-5.6-sol",
        profile_id="sol_lead",
        provenance="SessionStart",
        state_root=project_root,
    )
    update_session(
        session_id,
        observed_context_window=360_000,
        observed_context_window_provenance=(
            "statusline.context_window.context_window_size"
        ),
        provenance="statusline",
        state_root=project_root,
    )
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get(f"/api/state/manifest?session={session_id}")

    assert response.status_code == 200
    telemetry = response.json()["_telemetry"]
    assert telemetry["caller_match"] is True
    assert telemetry["transcript"] == "sol.jsonl"
    assert telemetry["declared_model"] == "gpt-5.6-sol"
    assert telemetry["observed_model"] == "gpt-5.6-sol"
    assert telemetry["declared_context_limit"] == 272_000
    assert telemetry["actual_context_limit"] == 360_000
    assert telemetry["selected_profile"] == "sol_lead"
    assert telemetry["percentage"] == pytest.approx(187_000 * 100 / 360_000)
    assert telemetry["provenance"] == (
        "statusline.context_window.context_window_size"
    )
    assert telemetry["mismatch"] is True
    assert telemetry["profile_trusted"] is True
    assert telemetry["profile_resolution_reason"] == "explicit-profile"


def test_linked_worktree_reads_record_from_canonical_primary_checkout(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    linked_root = tmp_path / "linked-worktree"
    primary_root = tmp_path / "primary-checkout"
    linked_root.mkdir()
    primary_root.mkdir()
    session_id = "linked-worktree-session"
    transcript = tmp_path / "official transcripts" / "linked.jsonl"
    _write_transcript(transcript, tokens=144_000)
    update_session(
        session_id,
        transcript_path=str(transcript),
        observed_model="gpt-5.6-sol",
        profile_id="sol_lead",
        provenance="SessionStart",
        state_root=primary_root,
    )
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", linked_root)
    monkeypatch.setattr(
        transcript_tokens,
        "canonical_state_root",
        lambda project_root: primary_root if project_root == linked_root else project_root,
    )

    response = TestClient(app).get(f"/api/state/manifest?session={session_id}")

    telemetry = response.json()["_telemetry"]
    assert telemetry["caller_match"] is True
    assert telemetry["ctx"] == 144_000
    assert telemetry["transcript"] == "linked.jsonl"
    assert telemetry["actual_context_limit"] == 272_000
    assert telemetry["selected_profile"] == "sol_lead"


def test_session_miss_returns_not_found_reason(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get("/api/state/manifest?session=missing-session")

    telemetry = response.json()["_telemetry"]
    assert telemetry["ctx"] is None
    assert telemetry["caller_match"] is False
    assert telemetry["reason"] == "session-transcript-not-found"


@pytest.mark.parametrize(
    "request_kwargs",
    [
        {"params": {"session": "bad..id!"}},
        {"headers": {"X-Session-Id": "x" * 129}},
    ],
)
def test_invalid_session_id_degrades_without_failing_manifest(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
    request_kwargs,
) -> None:
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get("/api/state/manifest", **request_kwargs)

    assert response.status_code == 200
    telemetry = response.json()["_telemetry"]
    assert telemetry["caller_match"] is False
    assert telemetry["reason"] == "invalid-session-id"


def test_corrupt_session_record_degrades_without_failing_manifest(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    session_id = "corrupt-session"
    records = project_root / ".agent" / "sessions"
    records.mkdir(parents=True)
    (records / f"{session_id}.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get(f"/api/state/manifest?session={session_id}")

    assert response.status_code == 200
    telemetry = response.json()["_telemetry"]
    assert telemetry["caller_match"] is False
    assert telemetry["reason"] == "session-record-error"


def test_no_session_param_shape_with_newest_sidecar(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    flat = str(project_root.resolve()).replace("/", "-")
    transcript = home / ".claude" / "projects" / flat / "newest.jsonl"
    _write_transcript(transcript)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get("/api/state/manifest")

    telemetry = response.json()["_telemetry"]
    assert telemetry["ctx"] is None
    assert telemetry["reason"] == "no-session-param"
    assert telemetry["newest_transcript"]["ctx"] == 187_000
    assert telemetry["newest_transcript"]["transcript"] == "newest.jsonl"


def test_query_session_wins_over_header(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    flat = str(project_root.resolve()).replace("/", "-")
    query_session = "query-session"
    header_session = "header-session"
    _write_transcript(
        home / ".claude" / "projects" / flat / f"{query_session}.jsonl",
        tokens=111_000,
    )
    _write_transcript(
        home / ".claude" / "projects" / flat / f"{header_session}.jsonl",
        tokens=222_000,
    )

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get(
        f"/api/state/manifest?session={query_session}",
        headers={"X-Session-Id": header_session},
    )

    assert response.json()["_telemetry"]["ctx"] == 111_000
    assert response.json()["_telemetry"]["transcript"] == f"{query_session}.jsonl"


def test_header_session_used_when_query_absent(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    session_id = "header-only"
    flat = str(project_root.resolve()).replace("/", "-")
    _write_transcript(home / ".claude" / "projects" / flat / f"{session_id}.jsonl")

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    response = TestClient(app).get(
        "/api/state/manifest",
        headers={"X-Session-Id": session_id},
    )

    assert response.json()["_telemetry"]["caller_match"] is True
    assert response.json()["_telemetry"]["transcript"] == f"{session_id}.jsonl"


def test_session_given_does_not_use_cross_checkout_fallback(
    tmp_path,
    monkeypatch,
    telemetry_enabled,
) -> None:
    home = tmp_path / "home"
    project_root = tmp_path / "learn-ukrainian"
    project_root.mkdir()
    other_project = home / ".claude" / "projects" / "other-learn-ukrainian-clone"
    other_project.mkdir(parents=True)
    _write_transcript(other_project / "foreign.jsonl", tokens=999_000)

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(telemetry_response, "PROJECT_ROOT", project_root)

    paths = transcript_tokens.resolve_transcript_paths(
        project_root,
        session="missing-but-foreign-exists",
    )
    assert paths == []

    response = TestClient(app).get(
        "/api/state/manifest?session=missing-but-foreign-exists",
    )
    assert response.json()["_telemetry"]["reason"] == "session-transcript-not-found"
