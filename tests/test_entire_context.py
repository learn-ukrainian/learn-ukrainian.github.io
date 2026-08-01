"""Acceptance coverage for the public body-free context-link index (#6174).

Proves: schema allowlist and forbidden-field rejection, deterministic locator
IDs, duplicate/replay idempotency, pending/tombstoned invisibility, stale /
partial-terminal / digest-mismatched evidence refusal, rebuild parity,
missing/disabled projection behavior, and body-free CLI output.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.entire_context import cli
from scripts.entire_context.model import (
    ContextLink,
    LinkKind,
    SchemaError,
    VerificationEvidence,
    VerificationStatus,
    isoformat_z,
)
from scripts.entire_context.store import AdmitOutcome, ContextLinkStore

NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
GIT_SHA = "0" * 40

# Tokens that must never appear in any CLI output (body-free contract).
FORBIDDEN_OUTPUT_TOKENS = (
    "prompt",
    "response",
    "transcript",
    "summar",
    "raw_capture",
    "message",
    "artifact",
    "secret",
    "password",
    "credential",
    "api_key",
    "refs/entire",
    "-----BEGIN",
    "ghp_",
    "sk-",
)


def make_link(**overrides) -> ContextLink:
    fields = {
        "kind": LinkKind.GIT_COMMIT,
        "canonical_namespace": "git:learn-ukrainian/learn-ukrainian.github.io",
        "canonical_id": GIT_SHA,
        "canonical_digest": DIGEST_A,
        "git_sha": GIT_SHA,
        "facets": {
            "repository": "learn-ukrainian/learn-ukrainian.github.io",
            "stream_epic": "4707",
            "track": "infra-harness",
            "title": "Public context-link index",
            "labels": ["infra", "entire"],
            "token_bucket": "small",
        },
    }
    fields.update(overrides)
    return ContextLink(**fields)


def make_verification(**overrides) -> VerificationEvidence:
    fields = {
        "verifier": "git",
        "canonical_digest": DIGEST_A,
        "status": VerificationStatus.VERIFIED,
        "evidence_locator": "git:commit/" + GIT_SHA,
        "checked_at": isoformat_z(NOW),
    }
    fields.update(overrides)
    return VerificationEvidence(**fields)


def make_store(tmp_path: Path) -> ContextLinkStore:
    return ContextLinkStore(tmp_path / "context-links.sqlite3")


def event_count(store: ContextLinkStore) -> int:
    with sqlite3.connect(store.db_path) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM link_events").fetchone()[0])


# ── schema: allowlist and forbidden-field rejection ──────────────────────────


def test_valid_link_roundtrips_and_validates() -> None:
    link = make_link()
    link.validate()
    parsed = ContextLink.from_dict(link.to_dict())
    assert parsed.locator_id == link.locator_id


def test_locator_id_format() -> None:
    assert make_link().locator_id.startswith("clink_")
    assert len(make_link().locator_id) == len("clink_") + 64


@pytest.mark.parametrize(
    "field",
    [
        "prompt",
        "response",
        "transcript",
        "summary",
        "raw_capture",
        "message_body",
        "artifact_body",
        "transcript_path",
        "secret_token",
        "session_notes",
        "entire_ref",
    ],
)
def test_from_dict_rejects_unknown_and_body_bearing_fields(field: str) -> None:
    payload = make_link().to_dict()
    payload[field] = "x"
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize("facet_key", ["prompt", "body", "transcript_path", "unknown_field"])
def test_facets_reject_forbidden_and_unknown_keys(facet_key: str) -> None:
    payload = make_link().to_dict()
    payload["facets"] = {facet_key: "x"}
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize(
    "value",
    [
        "ghp_" + "x" * 32,
        "sk-" + "y" * 32,
        "-----BEGIN " + "OPENSSH PRIVATE KEY-----",
        "password: supersecret1",
        "api_key=abcdefgh123",
        "refs/entire/checkpoints/abc",
        "AKIA" + "A" * 16,
        "xoxb-" + "A" * 24,
        "eyJ" + "A" * 12 + "." + "B" * 12 + "." + "C" * 12,
        "Bearer " + "A" * 32,
        "A" * 64,
    ],
)
def test_facet_values_reject_secrets_and_public_entire_refs(value: str) -> None:
    payload = make_link().to_dict()
    payload["facets"] = {"title": value}
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize("separator", [" ", ",", "\u2022"])
def test_facet_values_reject_separator_split_opaque_tokens(separator: str) -> None:
    payload = make_link().to_dict()
    payload["facets"] = {"title": "A" * 47 + separator + "A" * 47}
    with pytest.raises(SchemaError, match="long-opaque-token"):
        ContextLink.from_dict(payload)


def test_long_natural_language_facet_remains_allowed() -> None:
    payload = make_link().to_dict()
    payload["facets"] = {
        "title": "Public context links keep canonical systems authoritative across every agent harness"
    }
    assert ContextLink.from_dict(payload).facets == payload["facets"]


@pytest.mark.parametrize("field", ["canonical_id", "entire_checkpoint_id"])
def test_non_facet_identity_fields_reject_token_like_values(field: str) -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload[field] = "ghp_" + "x" * 32
    with pytest.raises(SchemaError, match="credential-token"):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize("field", ["canonical_id", "entire_checkpoint_id"])
def test_non_facet_identity_fields_reject_long_opaque_values(field: str) -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload[field] = "A" * 64
    with pytest.raises(SchemaError, match="long-opaque-token"):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize("field", ["canonical_id", "entire_checkpoint_id"])
def test_non_facet_identity_fields_reject_delimiter_split_opaque_values(field: str) -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload[field] = "A" * 47 + "." + "A" * 47
    with pytest.raises(SchemaError, match="long-opaque-token"):
        ContextLink.from_dict(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entire_checkpoint_id", 123),
        ("entire_checkpoint_id", True),
        ("git_sha", 123),
        ("git_sha", True),
    ],
)
def test_optional_identity_fields_reject_non_strings(field: str, value: object) -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload[field] = value
    with pytest.raises(SchemaError, match=field):
        ContextLink.from_dict(payload)


def test_canonical_namespace_rejects_long_opaque_path_component() -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload["canonical_namespace"] = "github:" + "A" * 64
    with pytest.raises(SchemaError, match="long-opaque-token"):
        ContextLink.from_dict(payload)


def test_canonical_namespace_rejects_delimiter_split_opaque_value() -> None:
    payload = make_link().to_dict()
    payload.pop("locator_id")
    payload["canonical_namespace"] = "github:" + "A" * 30 + "." + "A" * 30
    with pytest.raises(SchemaError, match="long-opaque-token"):
        ContextLink.from_dict(payload)


def test_verification_locator_rejects_token_like_values() -> None:
    payload = make_verification().to_dict()
    payload["evidence_locator"] = "ghp_" + "x" * 32
    with pytest.raises(SchemaError, match="credential-token"):
        VerificationEvidence.from_dict(payload)


@pytest.mark.parametrize("field", ["verifier", "evidence_locator"])
def test_verification_identity_fields_reject_long_opaque_values(field: str) -> None:
    payload = make_verification().to_dict()
    payload[field] = "A" * 64
    with pytest.raises(SchemaError, match="long-opaque-token"):
        VerificationEvidence.from_dict(payload)


@pytest.mark.parametrize("field", ["verifier", "evidence_locator"])
def test_verification_identity_fields_reject_delimiter_split_opaque_values(field: str) -> None:
    payload = make_verification().to_dict()
    payload[field] = "A" * 47 + "." + "A" * 47
    with pytest.raises(SchemaError, match="long-opaque-token"):
        VerificationEvidence.from_dict(payload)


def test_typed_verification_locator_rejects_long_opaque_path_component() -> None:
    payload = make_verification().to_dict()
    payload["evidence_locator"] = "github:" + "A" * 64
    with pytest.raises(SchemaError, match="long-opaque-token"):
        VerificationEvidence.from_dict(payload)


def test_git_commit_evidence_locator_remains_allowed() -> None:
    payload = make_verification().to_dict()
    payload["evidence_locator"] = "git:commit/" + GIT_SHA
    assert VerificationEvidence.from_dict(payload).evidence_locator == payload["evidence_locator"]


def test_from_dict_rejects_unsupported_schema_version() -> None:
    payload = make_link().to_dict()
    payload["schema_version"] = 99
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


def test_from_dict_rejects_tampered_locator_id() -> None:
    payload = make_link().to_dict()
    payload["locator_id"] = "clink_" + "f" * 64
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


def test_from_dict_rejects_caller_supplied_ingested_at() -> None:
    payload = make_link().to_dict()
    payload["ingested_at"] = isoformat_z(NOW)
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


def test_from_dict_rejects_bad_digest_and_kind() -> None:
    payload = make_link().to_dict()
    payload["canonical_digest"] = "not-a-digest"
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)
    payload = make_link().to_dict()
    payload["kind"] = "entire_session"
    with pytest.raises(SchemaError):
        ContextLink.from_dict(payload)


# ── deterministic locator IDs ────────────────────────────────────────────────


def test_locator_id_is_deterministic() -> None:
    first = make_link().locator_id
    second = make_link(facets={"title": "different facets do not matter"}).locator_id
    assert first == second


def test_changed_digest_produces_new_locator_id() -> None:
    assert make_link().locator_id != make_link(canonical_digest=DIGEST_B).locator_id


def test_changed_kind_namespace_or_id_produce_new_locator_id() -> None:
    base = make_link()
    assert base.locator_id != make_link(kind=LinkKind.GITHUB_ISSUE).locator_id
    assert base.locator_id != make_link(canonical_namespace="github:learn-ukrainian/learn-ukrainian.github.io").locator_id
    assert base.locator_id != make_link(canonical_id="6174").locator_id


# ── admission lifecycle ──────────────────────────────────────────────────────


def test_admit_promotes_with_valid_verification(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    result = store.admit(make_link(), make_verification(), actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.PROMOTED
    assert store.lookup(result.locator_id) is not None


def test_duplicate_admission_is_idempotent(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    first = store.admit(link, make_verification(), actor="test", now=NOW)
    events_after_first = event_count(store)
    second = store.admit(link, make_verification(), actor="test", now=NOW)
    assert second.outcome is AdmitOutcome.ALREADY_PROMOTED
    assert event_count(store) == events_after_first
    assert store.lookup(first.locator_id) is not None


def test_actor_must_be_a_body_free_identity(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    with pytest.raises(SchemaError, match="credential-token"):
        store.admit(
            make_link(),
            make_verification(),
            actor="ghp_" + "x" * 32,
            now=NOW,
        )
    assert not store.db_path.exists()


def test_pending_claims_are_invisible(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    locator_id = store.submit_claim(link, actor="test", now=NOW)
    assert store.lookup(locator_id) is None
    detail = store.explain(locator_id)
    assert detail is not None
    assert detail["state"] == "pending"
    assert [event["event_type"] for event in detail["events"]] == ["claimed"]
    # Re-submitting the same claim is a no-op.
    store.submit_claim(link, actor="test", now=NOW)
    assert event_count(store) == 1


def test_pending_claim_promotes_on_replayed_admission(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    store.submit_claim(link, actor="test", now=NOW)
    result = store.admit(link, make_verification(), actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.PROMOTED
    assert store.lookup(result.locator_id) is not None
    detail = store.explain(result.locator_id)
    assert detail is not None
    assert [event["event_type"] for event in detail["events"]] == ["claimed", "promoted"]


def test_pending_claim_payload_conflict_tombstones_instead_of_promoting(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    pending = make_link(entire_checkpoint_id="unverified-checkpoint", facets={"title": "unverified"})
    admitted = make_link(entire_checkpoint_id="verified-checkpoint", facets={"title": "verified"})
    store.submit_claim(pending, actor="test", now=NOW)

    result = store.admit(admitted, make_verification(), actor="test", now=NOW)

    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "claim_payload_conflict"
    assert result.state == "tombstoned"
    assert store.lookup(result.locator_id) is None
    detail = store.explain(result.locator_id)
    assert detail is not None
    assert detail["tombstone_reason"] == "claim_payload_conflict"


def test_promoted_claim_payload_conflict_is_refused_without_replacement(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    original = make_link(entire_checkpoint_id="verified-checkpoint", facets={"title": "verified"})
    first = store.admit(original, make_verification(), actor="test", now=NOW)
    conflicting = make_link(entire_checkpoint_id="other-checkpoint", facets={"title": "other"})

    result = store.admit(conflicting, make_verification(), actor="test", now=NOW)

    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "claim_payload_conflict"
    stored = store.lookup(first.locator_id)
    assert stored is not None
    assert stored["entire_checkpoint_id"] == "verified-checkpoint"
    assert stored["facets"] == {"title": "verified"}


def test_missing_verification_is_tombstoned_and_invisible(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    locator_id = link.locator_id
    store.admit(link, None, actor="test", now=NOW)
    assert store.lookup(locator_id) is None
    detail = store.explain(locator_id)
    assert detail is not None
    assert detail["state"] == "tombstoned"
    assert detail["tombstone_reason"] == "verification_missing"


def test_tombstoned_claims_are_invisible_and_terminal(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    refused = store.admit(link, None, actor="test", now=NOW)
    assert refused.outcome is AdmitOutcome.REFUSED
    events_after_refusal = event_count(store)
    retry = store.admit(link, make_verification(), actor="test", now=NOW)
    assert retry.outcome is AdmitOutcome.ALREADY_TOMBSTONED
    assert event_count(store) == events_after_refusal
    assert store.lookup(refused.locator_id) is None


def test_stale_evidence_cannot_promote(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    stale = make_verification(status=VerificationStatus.STALE)
    result = store.admit(make_link(), stale, actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "verification_stale"
    assert store.lookup(result.locator_id) is None


def test_old_checked_at_evidence_cannot_promote(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    old = make_verification(checked_at=isoformat_z(NOW - timedelta(hours=2)))
    result = store.admit(make_link(), old, actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "verification_stale"


def test_partial_terminal_evidence_cannot_promote(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    partial = make_verification(status=VerificationStatus.PARTIAL_TERMINAL)
    result = store.admit(make_link(), partial, actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "verification_partial_terminal"
    assert store.lookup(result.locator_id) is None


def test_digest_mismatched_evidence_cannot_promote(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    mismatch = make_verification(
        status=VerificationStatus.DIGEST_MISMATCH, canonical_digest=DIGEST_B
    )
    result = store.admit(make_link(), mismatch, actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "verification_digest_mismatch"
    assert store.lookup(result.locator_id) is None


def test_verified_status_with_wrong_digest_cannot_promote(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    wrong_digest = make_verification(canonical_digest=DIGEST_B)
    result = store.admit(make_link(), wrong_digest, actor="test", now=NOW)
    assert result.outcome is AdmitOutcome.REFUSED
    assert result.reason == "digest_mismatch"


def test_explain_returns_body_free_audit_trail(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    link = make_link()
    result = store.admit(link, make_verification(), actor="test", now=NOW)
    detail = store.explain(result.locator_id)
    assert detail is not None
    assert [event["event_type"] for event in detail["events"]] == ["claimed", "promoted"]
    rendered = json.dumps(detail, ensure_ascii=False).lower()
    for token in FORBIDDEN_OUTPUT_TOKENS:
        assert token not in rendered


def test_multiple_links_stay_distinct(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    first = store.admit(make_link(), make_verification(), actor="test", now=NOW)
    second = store.admit(
        make_link(canonical_digest=DIGEST_B),
        make_verification(canonical_digest=DIGEST_B),
        actor="test",
        now=NOW,
    )
    assert first.locator_id != second.locator_id
    assert store.lookup(first.locator_id)["canonical_digest"] == DIGEST_A
    assert store.lookup(second.locator_id)["canonical_digest"] == DIGEST_B


# ── rebuild parity ───────────────────────────────────────────────────────────


def test_rebuild_reproduces_identical_projection(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.admit(make_link(), make_verification(), actor="test", now=NOW)
    store.admit(
        make_link(canonical_digest=DIGEST_B),
        make_verification(canonical_digest=DIGEST_B),
        actor="test",
        now=NOW,
    )
    store.admit(make_link(canonical_id="6174"), None, actor="test", now=NOW)
    result = store.rebuild()
    assert result["parity"] is True
    assert result["applied"] is True
    assert result["drift_repaired"] is False
    assert result["links"] == 3
    again = store.rebuild()
    assert again["parity"] is True
    status = store.status()
    assert status["counts"] == {"promoted": 2, "tombstoned": 1}
    assert status["events"] == 6


def test_rebuild_repairs_projection_drift_and_reports_applied_state(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    admitted = store.admit(make_link(), make_verification(), actor="test", now=NOW)
    with sqlite3.connect(store.db_path) as connection:
        connection.execute(
            "UPDATE context_links SET state = 'pending', promoted_at = NULL WHERE locator_id = ?",
            (admitted.locator_id,),
        )

    result = store.rebuild()

    assert result["parity"] is False
    assert result["applied"] is True
    assert result["drift_repaired"] is True
    assert store.lookup(admitted.locator_id) is not None


# ── cross-harness equivalence ────────────────────────────────────────────────


def test_same_fixture_yields_same_body_free_result_across_projections(tmp_path: Path) -> None:
    link_payload = make_link().to_dict()
    verification = make_verification()
    results = []
    for seat in ("codex", "kimi", "glm"):
        store = ContextLinkStore(tmp_path / f"{seat}.sqlite3")
        link = ContextLink.from_dict(link_payload)
        admitted = store.admit(link, verification, actor=seat, now=NOW)
        results.append(store.lookup(admitted.locator_id))
    assert results[0] is not None
    assert results[0] == results[1] == results[2]


# ── CLI: status / lookup / explain / rebuild / admit ─────────────────────────


def run_cli(argv: list[str]) -> tuple[int, dict]:
    from io import StringIO
    from unittest.mock import patch

    buffer = StringIO()
    with patch("sys.stdout", buffer):
        code = cli.main(argv)
    return code, json.loads(buffer.getvalue())


def test_cli_status_missing_projection_does_not_create_state(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite3"
    code, payload = run_cli(["status", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["available"] is False
    assert payload["reason"] == "projection_missing"
    assert not db.exists()


def test_cli_lookup_missing_projection_is_clean(tmp_path: Path) -> None:
    code, payload = run_cli(["lookup", "clink_" + "0" * 64, "--db", str(tmp_path / "m.sqlite3")])
    assert code == cli.EXIT_OK
    assert payload["available"] is False


def test_cli_rebuild_missing_projection_is_clean(tmp_path: Path) -> None:
    db = tmp_path / "missing.sqlite3"
    code, payload = run_cli(["rebuild", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["available"] is False
    assert not db.exists()


def test_cli_disabled_projection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(cli.ENV_DISABLED, "1")
    db = tmp_path / "disabled.sqlite3"
    code, payload = run_cli(["status", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["enabled"] is False
    assert payload["reason"] == "projection_disabled"
    link_file = tmp_path / "link.json"
    link_file.write_text(json.dumps(make_link().to_dict()), encoding="utf-8")
    code, payload = run_cli(["admit", "--link", str(link_file), "--db", str(db)])
    assert code == cli.EXIT_REFUSED
    assert payload["reason"] == "projection_disabled"
    assert not db.exists()


def test_cli_corrupt_projection_fails_open(tmp_path: Path) -> None:
    db = tmp_path / "corrupt.sqlite3"
    db.write_bytes(b"not a sqlite database at all")
    code, payload = run_cli(["status", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["available"] is False
    assert payload["reason"] == "projection_unreadable"


def test_cli_rebuild_corrupt_projection_refuses_without_traceback(tmp_path: Path) -> None:
    db = tmp_path / "corrupt.sqlite3"
    db.write_bytes(b"not a sqlite database at all")

    code, payload = run_cli(["rebuild", "--db", str(db)])

    assert code == cli.EXIT_REFUSED
    assert payload["available"] is False
    assert payload["reason"] == "projection_unreadable"


def test_cli_admit_corrupt_projection_fails_closed_without_traceback(tmp_path: Path) -> None:
    db = tmp_path / "corrupt.sqlite3"
    db.write_bytes(b"not a sqlite database at all")
    link_file = tmp_path / "link.json"
    link_file.write_text(json.dumps(make_link().to_dict()), encoding="utf-8")

    code, payload = run_cli(["admit", "--link", str(link_file), "--db", str(db)])

    assert code == cli.EXIT_REFUSED
    assert payload["available"] is False
    assert payload["reason"] == "projection_unreadable"


def test_cli_malformed_projection_row_fails_open_without_traceback(tmp_path: Path) -> None:
    db = tmp_path / "malformed.sqlite3"
    store = ContextLinkStore(db)
    result = store.admit(make_link(), make_verification(), actor="test", now=NOW)
    with sqlite3.connect(db) as connection:
        connection.execute(
            "UPDATE context_links SET facets_json = ? WHERE locator_id = ?",
            ("not-json", result.locator_id),
        )

    code, payload = run_cli(["lookup", result.locator_id, "--db", str(db)])

    assert code == cli.EXIT_OK
    assert payload["available"] is False
    assert payload["reason"] == "projection_unreadable"


def test_cli_admit_lookup_explain_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "roundtrip.sqlite3"
    link_file = tmp_path / "link.json"
    verification_file = tmp_path / "verification.json"
    link = make_link()
    link_file.write_text(json.dumps(link.to_dict()), encoding="utf-8")
    verification_file.write_text(
        json.dumps(make_verification(checked_at=isoformat_z(datetime.now(UTC))).to_dict()),
        encoding="utf-8",
    )

    code, payload = run_cli(
        ["admit", "--link", str(link_file), "--verification", str(verification_file), "--db", str(db)]
    )
    assert code == cli.EXIT_OK
    assert payload["outcome"] == "promoted"
    locator_id = payload["locator_id"]
    assert locator_id == link.locator_id

    code, payload = run_cli(["lookup", locator_id, "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["found"] is True
    assert payload["link"]["canonical_id"] == GIT_SHA

    code, payload = run_cli(["explain", locator_id, "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["found"] is True
    assert payload["state"] == "promoted"

    code, payload = run_cli(["status", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["counts"] == {"promoted": 1}

    code, payload = run_cli(["rebuild", "--db", str(db)])
    assert code == cli.EXIT_OK
    assert payload["parity"] is True
    assert payload["applied"] is True
    assert payload["drift_repaired"] is False

    code, payload = run_cli(["lookup", "clink_" + "f" * 64, "--db", str(db)])
    assert code == cli.EXIT_NOT_FOUND
    assert payload["found"] is False


def test_cli_admit_without_verification_refuses(tmp_path: Path) -> None:
    db = tmp_path / "noverif.sqlite3"
    link_file = tmp_path / "link.json"
    link_file.write_text(json.dumps(make_link().to_dict()), encoding="utf-8")
    code, payload = run_cli(["admit", "--link", str(link_file), "--db", str(db)])
    assert code == cli.EXIT_REFUSED
    assert payload["reason"] == "verification_missing"
    lookup_code, lookup_payload = run_cli(["lookup", make_link().locator_id, "--db", str(db)])
    assert lookup_code == cli.EXIT_NOT_FOUND
    assert lookup_payload["found"] is False


def test_cli_admit_rejects_schema_violations(tmp_path: Path) -> None:
    db = tmp_path / "schema.sqlite3"
    link_file = tmp_path / "link.json"
    payload = make_link().to_dict()
    payload["prompt"] = "ignored"
    link_file.write_text(json.dumps(payload), encoding="utf-8")
    code, out = run_cli(["admit", "--link", str(link_file), "--db", str(db)])
    assert code == cli.EXIT_REFUSED
    assert out["reason"] == "schema_invalid"
    assert not db.exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entire_checkpoint_id", 123),
        ("entire_checkpoint_id", True),
        ("git_sha", 123),
        ("git_sha", True),
    ],
)
def test_cli_admit_rejects_non_string_optional_identifiers(
    tmp_path: Path, field: str, value: object
) -> None:
    db = tmp_path / "schema.sqlite3"
    link_file = tmp_path / "link.json"
    payload = make_link().to_dict()
    payload[field] = value
    link_file.write_text(json.dumps(payload), encoding="utf-8")

    code, out = run_cli(["admit", "--link", str(link_file), "--db", str(db)])

    assert code == cli.EXIT_REFUSED
    assert out["outcome"] == "refused"
    assert out["reason"] == "schema_invalid"
    assert field in out["detail"]
    assert not db.exists()


def test_cli_admit_rejects_non_utf8_json_without_traceback(tmp_path: Path) -> None:
    db = tmp_path / "non-utf8.sqlite3"
    link_file = tmp_path / "link.json"
    link_file.write_bytes(b"\xff\xfe\x00\x01")

    code, payload = run_cli(["admit", "--link", str(link_file), "--db", str(db)])

    assert code == cli.EXIT_REFUSED
    assert payload["outcome"] == "refused"
    assert payload["reason"] == "schema_invalid"
    assert "not readable JSON" in payload["detail"]
    assert not db.exists()


def test_cli_output_is_body_free(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    db = tmp_path / "bodyfree.sqlite3"
    store = ContextLinkStore(db)
    promoted = store.admit(make_link(), make_verification(), actor="test", now=NOW)
    store.admit(make_link(canonical_id="6174"), None, actor="test", now=NOW)

    outputs: list[str] = []
    for argv in (
        ["status", "--db", str(db)],
        ["lookup", promoted.locator_id, "--db", str(db)],
        ["explain", promoted.locator_id, "--db", str(db)],
        ["rebuild", "--db", str(db)],
        ["status", "--db", str(tmp_path / "missing.sqlite3")],
    ):
        code = cli.main(argv)
        outputs.append(capsys.readouterr().out)
    rendered = "\n".join(outputs).lower()
    for token in FORBIDDEN_OUTPUT_TOKENS:
        assert token not in rendered
