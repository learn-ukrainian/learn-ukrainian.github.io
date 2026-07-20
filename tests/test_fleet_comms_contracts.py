from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.fleet_comms.contracts import AssistantSegment, CompletionState, ResponseEnvelope, new_id
from scripts.fleet_comms.endpoints import load_endpoint_registry
from scripts.fleet_comms.migrations import CommsMigrationError, apply_migrations


def test_response_envelope_round_trips_every_completion_state() -> None:
    for state in CompletionState:
        envelope = ResponseEnvelope(
            segments=(AssistantSegment(text="first", sequence=0), AssistantSegment(text="second", sequence=1)),
            completion_state=state,
            terminal_event_observed=state is CompletionState.COMPLETE,
            raw_capture_artifact_id="artifact_1",
            raw_capture_sha256="a" * 64,
        )
        restored = ResponseEnvelope.from_dict(envelope.to_dict())
        assert restored == envelope
        assert restored.response_text == "firstsecond"
        assert restored.is_formal_review_eligible is (state is CompletionState.COMPLETE)


def test_complete_envelope_requires_terminal_evidence() -> None:
    with pytest.raises(ValueError, match="terminal event"):
        ResponseEnvelope(segments=(), completion_state=CompletionState.COMPLETE)


def test_shared_ids_are_namespaced_and_validate_kind() -> None:
    assert new_id("request").startswith("request_")
    with pytest.raises(ValueError, match="lowercase"):
        new_id("Request")


def test_endpoint_registry_retires_gemini_to_agy() -> None:
    registry = load_endpoint_registry()
    endpoint, requested = registry.resolve("gemini")
    assert requested == "gemini"
    assert endpoint.name == "agy"
    assert endpoint.state == "live"


def test_endpoint_registry_formal_review_eligibility_is_fail_closed() -> None:
    """Sealed CF only for proven seats; unproven live lanes stay false until isolation issues close."""
    registry = load_endpoint_registry()
    by_name = {endpoint.name: endpoint for endpoint in registry.endpoints}

    assert by_name["claude"].formal_review_eligible is True
    assert by_name["codex"].formal_review_eligible is True

    for name in ("agy", "grok", "kimi", "cursor", "gemini", "glm-local"):
        assert name in by_name, f"missing registry endpoint: {name}"
        assert by_name[name].formal_review_eligible is False, name

    for name in ("grok", "kimi", "agy", "cursor"):
        endpoint, resolved = registry.resolve(name)
        assert resolved == name
        assert endpoint.state == "live"
        assert endpoint.formal_review_eligible is False


def test_endpoint_registry_rejects_duplicate_aliases(tmp_path: Path) -> None:
    path = tmp_path / "fleet.yaml"
    path.write_text(
        """version: 1
endpoints:
  - name: one
    aliases: [one]
    state: live
    transports: [test]
    completion_evidence: []
    default_ttl_seconds: 1
    retry_class: none
    concurrency_limit: 1
    formal_review_eligible: false
    model_family_resolver: resolver
  - name: two
    aliases: [one, two]
    state: live
    transports: [test]
    completion_evidence: []
    default_ttl_seconds: 1
    retry_class: none
    concurrency_limit: 1
    formal_review_eligible: false
    model_family_resolver: resolver
""",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate endpoint alias"):
        load_endpoint_registry(path)


def test_migrations_are_idempotent_and_reject_unknown_future_version(tmp_path: Path) -> None:
    db_path = tmp_path / "messages.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE deliveries (delivery_id TEXT PRIMARY KEY, status TEXT)")
    assert apply_migrations(conn) == 2
    first = conn.execute("SELECT version, checksum FROM comms_schema_migrations").fetchall()
    assert apply_migrations(conn) == 2
    assert conn.execute("SELECT version, checksum FROM comms_schema_migrations").fetchall() == first
    assert {"request_id", "endpoint_id", "expires_at", "fence_token"}.issubset(
        {row[1] for row in conn.execute("PRAGMA table_info(deliveries)")}
    )
    conn.execute(
        "INSERT INTO comms_schema_migrations(version, name, checksum, applied_at) VALUES (99, 'future', 'x', 'now')"
    )
    conn.commit()
    with pytest.raises(CommsMigrationError, match="future communications schema"):
        apply_migrations(conn)
    conn.close()
