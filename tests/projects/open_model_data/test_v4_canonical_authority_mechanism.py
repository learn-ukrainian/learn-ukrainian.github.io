"""PR #7662 repair 6 acceptance tests: the operator-approved canonical
Fleet Comms authority store (text-free execution observations + Sources
invocation records), the opaque-ID-only production issuer entrypoints,
fixed Hramatka signing-key custody, and the digest-pinned/rotatable
production trust policy.

Mechanism-only: no test here ever provisions a real production key or
writes to the real default Fleet Comms plane. Every store test opens an
isolated ``ArtifactStore(root=tmp_path)``; every issuer test monkeypatches
the exact module-level indirection points (``_resolve_execution_
observation``/``_resolve_sources_invocation``/``_load_signing_key``) --
never a production bypass argument, since none exists.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import _v4_a7_real_slot_fixture as fx
import pytest

from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

AUTHOR_RECORD: dict[str, Any] = {
    "task_id": "task-1",
    "run_id": "run-1",
    "role": "author",
    "status": "done",
    "return_code": 0,
    "seat_or_model": "claude-sonnet-5-fixture",
    "harness": "claude",
    "session_id": "session-1",
    "completion_state": "complete",
    "terminal_event_observed": True,
    "process_returncode": 0,
    "raw_capture_artifact_id": "artifact-1",
    "raw_capture_sha256": "a" * 64,
    "row_content_sha256": "b" * 64,
    "prompt_sha256": "c" * 64,
    "packet_sha256": "d" * 64,
    "fleet_receipt_sha256": "e" * 64,
    "verification_tool_ids": ["tool-1"],
    "saw_source_text": False,
    "saw_heldout": False,
    "saw_eligible_unit_ids": False,
    "authorship_receipt_sha256": None,
    "rubric_sha256": None,
    "verdict": None,
}

REVIEWER_RECORD: dict[str, Any] = {
    **AUTHOR_RECORD,
    "task_id": "task-2",
    "run_id": "run-2",
    "role": "reviewer",
    "authorship_receipt_sha256": "f" * 64,
    "rubric_sha256": "1" * 64,
    "verdict": "PASS",
}

SOURCES_RECORD: dict[str, Any] = {
    "invocation_id": "inv-1",
    "row_content_sha256": "b" * 64,
    "identifier": "vesum:x",
    "tool_id": "mcp__sources__verify_word",
    "tool_version": "v1",
    "request_id": "req-1",
    "tool_result_sha256": "c" * 64,
    "lookup_ids": ["lk-1"],
    "success": True,
}


# --- canonical store: idempotency / conflict / rollback ---------------------


def test_execution_observation_write_is_idempotent(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        store.record_v4_execution_observation(AUTHOR_RECORD)
        store.record_v4_execution_observation(AUTHOR_RECORD)  # identical retry: silent no-op
        got = store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
        assert got == AUTHOR_RECORD


def test_execution_observation_write_refuses_a_conflicting_duplicate(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        store.record_v4_execution_observation(AUTHOR_RECORD)
        divergent = {**AUTHOR_RECORD, "status": "failed"}
        with pytest.raises(v4_store.ExecutionObservationConflictError, match="different execution observation"):
            store.record_v4_execution_observation(divergent)
        # the original record is untouched by the refused write
        assert store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") == AUTHOR_RECORD


def test_execution_observation_resolves_none_for_an_unknown_key(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="nope", run_id="nope", role="author") is None


def test_execution_observation_write_rejects_a_malformed_record_before_any_persistence(tmp_path: Path) -> None:
    """Validation runs before the DB is touched -- a rejected write leaves
    no partial row behind (rollback/failure handling)."""
    malformed = {k: v for k, v in AUTHOR_RECORD.items() if k != "harness"}  # missing required key
    with ArtifactStore(root=tmp_path) as store:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="exactly"):
            store.record_v4_execution_observation(malformed)
        assert store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") is None


def test_author_execution_observation_refuses_reviewer_only_fields(tmp_path: Path) -> None:
    tainted = {**AUTHOR_RECORD, "verdict": "PASS"}
    with ArtifactStore(root=tmp_path) as store:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            store.record_v4_execution_observation(tainted)


def test_reviewer_execution_observation_requires_every_reviewer_only_field(tmp_path: Path) -> None:
    incomplete = {**REVIEWER_RECORD, "verdict": None}
    with ArtifactStore(root=tmp_path) as store:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            store.record_v4_execution_observation(incomplete)


def test_execution_observation_store_is_isolated_by_role(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        store.record_v4_execution_observation(AUTHOR_RECORD)
        assert store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="reviewer") is None


def test_sources_invocation_write_is_idempotent(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        store.record_v4_sources_invocation(SOURCES_RECORD)
        store.record_v4_sources_invocation(SOURCES_RECORD)
        assert store.resolve_v4_sources_invocation(invocation_id="inv-1") == SOURCES_RECORD


def test_sources_invocation_write_refuses_a_conflicting_duplicate(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        store.record_v4_sources_invocation(SOURCES_RECORD)
        divergent = {**SOURCES_RECORD, "success": False}
        with pytest.raises(v4_store.SourcesInvocationConflictError, match="different sources invocation"):
            store.record_v4_sources_invocation(divergent)


def test_sources_invocation_resolves_none_for_an_unknown_invocation_id(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_sources_invocation(invocation_id="nope") is None


def test_compute_invocation_id_is_deterministic_and_content_addressed() -> None:
    kwargs = dict(tool_id="mcp__sources__verify_word", tool_version="v1", request_id="r1", row_content_sha256="a" * 64, identifier="vesum:x", tool_result_sha256="b" * 64, lookup_ids=["l1", "l2"])
    first = v4_store.compute_invocation_id(**kwargs)
    second = v4_store.compute_invocation_id(**kwargs)
    assert first == second
    different = v4_store.compute_invocation_id(**{**kwargs, "tool_result_sha256": "c" * 64})
    assert different != first


# --- production issuer entrypoints: opaque IDs only, resolve internally -----


def _patch_fleet(monkeypatch: pytest.MonkeyPatch, *, resolver=None, key_loader=None, trust_policy=None) -> None:
    if resolver is not None:
        monkeypatch.setattr(fleet_execution, "_resolve_execution_observation", resolver)
    if key_loader is not None:
        monkeypatch.setattr(fleet_execution, "_load_signing_key", key_loader)
    if trust_policy is not None:
        monkeypatch.setattr(trust, "load_production_trust_policy", lambda: trust_policy)


def test_issue_author_execution_receipt_signature_accepts_only_task_and_run_id() -> None:
    import inspect

    params = list(inspect.signature(fleet_execution.issue_author_execution_receipt).parameters)
    assert params == ["task_id", "run_id"]
    params = list(inspect.signature(fleet_execution.issue_reviewer_execution_receipt).parameters)
    assert params == ["task_id", "run_id"]
    params = list(inspect.signature(sources_authority.issue_verifier_attestation).parameters)
    assert params == ["invocation_id"]


def test_issue_author_execution_receipt_refuses_an_unknown_task_run_before_key_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(role: str) -> tuple[str, str]:
        raise AssertionError("key access must never happen for an unresolved observation")

    _patch_fleet(monkeypatch, resolver=lambda **_: None, key_loader=_boom)
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_author_execution_receipt(task_id="ghost", run_id="ghost")


def test_issue_author_execution_receipt_refuses_without_a_provisioned_production_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unmonkeypatched key custody: the real ``load_production_signing_key``
    always refuses in mechanism-only production (no key file exists)."""
    _patch_fleet(monkeypatch, resolver=lambda **_: dict(AUTHOR_RECORD))
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


def test_issue_author_execution_receipt_end_to_end_and_idempotent_repeat(monkeypatch: pytest.MonkeyPatch) -> None:
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(
        monkeypatch,
        resolver=lambda *, task_id, run_id, role: dict(AUTHOR_RECORD) if (task_id, run_id, role) == ("task-1", "run-1", "author") else None,
        key_loader=lambda role: (priv, "k1"),
        trust_policy=(policy, trust.trust_policy_sha256(policy)),
    )
    receipt = fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")
    fleet_execution.verify_author_execution_receipt(receipt, trust_policy=policy, outcome_sha256=fleet_execution.V4_SHA256, row_content_sha256=AUTHOR_RECORD["row_content_sha256"])
    again = fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")
    assert receipt == again, "repeat issuance against the identical resolved observation must reproduce byte for byte"


@pytest.mark.parametrize("mutation", [{"status": "running"}, {"return_code": 1}, {"completion_state": "failed"}, {"terminal_event_observed": False}])
def test_issue_author_execution_receipt_refuses_a_nonterminal_canonical_record(monkeypatch: pytest.MonkeyPatch, mutation: dict[str, Any]) -> None:
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    bad_record = {**AUTHOR_RECORD, **mutation}
    _patch_fleet(monkeypatch, resolver=lambda **_: bad_record, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    with pytest.raises((fleet_execution.FleetExecutionError, ValueError)):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


def test_issue_reviewer_execution_receipt_resolves_the_reviewer_role(monkeypatch: pytest.MonkeyPatch) -> None:
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})

    def resolver(*, task_id: str, run_id: str, role: str) -> dict[str, Any] | None:
        assert role == "reviewer"
        return dict(REVIEWER_RECORD)

    _patch_fleet(monkeypatch, resolver=resolver, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    receipt = fleet_execution.issue_reviewer_execution_receipt(task_id="task-2", run_id="run-2")
    assert receipt["domain"] == "reviewer"
    assert receipt["verdict"] == "PASS"


def test_issue_verifier_attestation_refuses_an_unknown_invocation_before_key_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(role: str) -> tuple[str, str]:
        raise AssertionError("key access must never happen for an unresolved invocation")

    monkeypatch.setattr(sources_authority, "_resolve_sources_invocation", lambda **_: None)
    monkeypatch.setattr(sources_authority, "_load_signing_key", _boom)
    with pytest.raises(sources_authority.SourcesAuthorityError, match="unknown invocation_id"):
        sources_authority.issue_verifier_attestation(invocation_id="ghost")


def test_issue_verifier_attestation_refuses_an_unsuccessful_canonical_record(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sources_authority, "_resolve_sources_invocation", lambda **_: {**SOURCES_RECORD, "success": False})
    monkeypatch.setattr(sources_authority, "_load_signing_key", lambda role: (_ for _ in ()).throw(AssertionError("no key access for a failed invocation")))
    with pytest.raises(sources_authority.SourcesAuthorityError, match="not recorded as successful"):
        sources_authority.issue_verifier_attestation(invocation_id="inv-1")


def test_issue_verifier_attestation_refuses_without_a_provisioned_production_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sources_authority, "_resolve_sources_invocation", lambda **_: dict(SOURCES_RECORD))
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        sources_authority.issue_verifier_attestation(invocation_id="inv-1")


def test_issue_verifier_attestation_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(sources={"k1": pub})
    monkeypatch.setattr(sources_authority, "_resolve_sources_invocation", lambda **_: dict(SOURCES_RECORD))
    monkeypatch.setattr(sources_authority, "_load_signing_key", lambda role: (priv, "k1"))
    monkeypatch.setattr(trust, "load_production_trust_policy", lambda: (policy, trust.trust_policy_sha256(policy)))
    attestation = sources_authority.issue_verifier_attestation(invocation_id="inv-1")
    sources_authority.verify_verifier_attestation(attestation, trust_policy=policy, outcome_sha256=sources_authority.V4_SHA256, row_content_sha256=SOURCES_RECORD["row_content_sha256"])


# --- signing-key custody: no public-argument path ---------------------------


def test_load_production_signing_key_refuses_an_unprovisioned_role() -> None:
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        trust.load_production_signing_key("fleet_execution")


def test_load_production_signing_key_refuses_an_unknown_role() -> None:
    with pytest.raises(trust.TrustAuthorityError, match="unknown signing-key role"):
        trust.load_production_signing_key("not-a-real-role")


def test_load_production_signing_key_refuses_a_malformed_provisioned_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "HRAMATKA_SIGNING_KEY_ROOT", tmp_path)
    (tmp_path / "fleet_execution.key").write_text("not-hex", encoding="utf-8")
    (tmp_path / "fleet_execution.key_id").write_text("k1", encoding="utf-8")
    with pytest.raises(trust.TrustAuthorityError, match="32 raw bytes"):
        trust.load_production_signing_key("fleet_execution")


def test_load_production_signing_key_succeeds_once_provisioned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "HRAMATKA_SIGNING_KEY_ROOT", tmp_path)
    priv, _pub = trust.generate_test_keypair()
    (tmp_path / "fleet_execution.key").write_text(priv, encoding="utf-8")
    (tmp_path / "fleet_execution.key_id").write_text("prod-key-1", encoding="utf-8")
    got_priv, got_key_id = trust.load_production_signing_key("fleet_execution")
    assert got_priv == priv
    assert got_key_id == "prod-key-1"


# --- production trust-policy digest pinning / rotation / revocation --------


def test_load_production_trust_policy_returns_the_checked_in_empty_policy() -> None:
    policy, digest = trust.load_production_trust_policy()
    assert policy == trust.empty_trust_policy()
    assert digest == trust.trust_policy_sha256(policy)


def test_load_production_trust_policy_refuses_a_one_byte_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    drifted = trust.DEFAULT_TRUST_POLICY_PATH.read_bytes() + b" "  # one extra byte, still valid JSON whitespace
    drifted_path = tmp_path / "drifted.json"
    drifted_path.write_bytes(drifted)
    monkeypatch.setattr(trust, "DEFAULT_TRUST_POLICY_PATH", drifted_path)
    with pytest.raises(trust.TrustAuthorityError, match="not in the code-reviewed active allowlist"):
        trust.load_production_trust_policy()


def test_load_production_trust_policy_refuses_a_revoked_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST", frozenset())
    with pytest.raises(trust.TrustAuthorityError, match="not in the code-reviewed active allowlist"):
        trust.load_production_trust_policy()


def test_load_production_trust_policy_takes_no_arguments() -> None:
    import inspect

    assert list(inspect.signature(trust.load_production_trust_policy).parameters) == []


def test_a7_private_ledger_cli_exposes_no_trust_policy_flag() -> None:
    """``--trust-policy`` is an unrecognized argument now -- argparse itself
    refuses it (exit code 2), never a caller-selected policy path."""
    import contextlib
    import io

    from scripts.projects.open_model_data import v4_a7_private_ledger as ledger

    buf = io.StringIO()
    with contextlib.redirect_stderr(buf), pytest.raises(SystemExit) as excinfo:
        ledger.main(["--trust-policy", "somewhere.json", "--verify-private", "--public-receipt", "x", "--ledger", "x", "--a4-receipt", "x", "--seal-receipt", "x", "--membership-dir", "x", "--packet-dir", "x", "--manifest", "x", "--a2-receipt", "x", "--salt-hex", "aa"])
    assert excinfo.value.code == 2
    assert "unrecognized arguments" in buf.getvalue()
    assert "--trust-policy" in buf.getvalue()


# --- trust_policy_sha256 binding: tamper / cross-chain disagreement --------


def test_require_trust_policy_binding_refuses_a_missing_field() -> None:
    policy = trust.empty_trust_policy()
    with pytest.raises(trust.TrustAuthorityError, match="no well-formed trust_policy_sha256"):
        trust.require_trust_policy_binding({}, policy)


def test_require_trust_policy_binding_refuses_a_mismatched_digest() -> None:
    policy_a = trust.empty_trust_policy()
    policy_b = trust.build_test_trust_policy(a3={"k1": "1" * 64})
    body = {"trust_policy_sha256": trust.trust_policy_sha256(policy_b)}
    with pytest.raises(trust.TrustAuthorityError, match="does not match"):
        trust.require_trust_policy_binding(body, policy_a)


def test_verify_author_execution_receipt_refuses_a_cross_chain_policy_digest_swap() -> None:
    """A receipt honestly signed under one trust policy must refuse when
    checked against a different one, even with a cryptographically valid
    signature over the (differently-keyed) body -- the exact 'cross-chain
    digest disagreement' Sol required."""
    row_content_sha256 = fx.ledger.sha256_text("cross-chain-tamper-check")
    real = fx.build_author_execution_receipt(row_content_sha256)
    other_policy = trust.build_test_trust_policy(fleet_execution={fx.FLEET_KEY_ID: fx.FLEET_PUBLIC_KEY_HEX}, a3={"extra": "2" * 64})
    assert trust.trust_policy_sha256(other_policy) != real["trust_policy_sha256"]
    with pytest.raises(fleet_execution.FleetExecutionError, match="does not match"):
        fleet_execution.verify_author_execution_receipt(real, trust_policy=other_policy, outcome_sha256=fleet_execution.V4_SHA256, row_content_sha256=row_content_sha256)


def test_verify_verifier_attestation_refuses_a_cross_chain_policy_digest_swap() -> None:
    row_content_sha256 = "a" * 64
    attestation = sources_authority._issue_verifier_attestation_from_evidence(
        signing_key_hex=fx.SOURCES_SIGNING_KEY_HEX,
        signer_key_id=fx.SOURCES_KEY_ID,
        outcome_sha256=sources_authority.V4_SHA256,
        row_content_sha256=row_content_sha256,
        identifier="vesum:x",
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        request_id="req-1",
        tool_result_sha256="b" * 64,
        lookup_ids=["l-1"],
        invocation_id="inv-1",
        trust_policy_sha256=fx.TRUST_POLICY_SHA256,
    )
    other_policy = trust.build_test_trust_policy(sources={fx.SOURCES_KEY_ID: fx.SOURCES_PUBLIC_KEY_HEX}, a3={"extra": "3" * 64})
    with pytest.raises(sources_authority.SourcesAuthorityError, match="does not match"):
        sources_authority.verify_verifier_attestation(attestation, trust_policy=other_policy, outcome_sha256=sources_authority.V4_SHA256, row_content_sha256=row_content_sha256)


def test_reference_check_signature_refuses_a_cross_chain_policy_digest_swap() -> None:
    receipt = fx.build_reference_check_receipt()
    signature, _ = fx.build_reference_check_authenticity(receipt)
    other_policy = trust.build_test_trust_policy(a3={fx.A3_KEY_ID: fx.A3_PUBLIC_KEY_HEX}, sources={"extra": "4" * 64})
    with pytest.raises(reference_check.ReferenceCheckError, match="does not match"):
        reference_check.verify_reference_check_receipt_signature(signature, receipt=receipt, trust_policy=other_policy, outcome_sha256=fx.ledger.V4_SHA256)


# --- A3 signing-key custody (repair 6 applies the same custody rule) -------


def test_a3_sign_reference_check_receipt_refuses_without_a_provisioned_production_key() -> None:
    receipt = fx.build_reference_check_receipt()
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        reference_check.sign_reference_check_receipt(receipt=receipt, outcome_sha256=fx.ledger.V4_SHA256)


def test_a3_production_entrypoints_accept_no_signing_key_argument() -> None:
    import inspect

    assert "signing_key_hex" not in inspect.signature(reference_check.sign_reference_check_receipt).parameters
    assert "signer_key_id" not in inspect.signature(reference_check.sign_reference_check_receipt).parameters
    assert "signing_key_hex" not in inspect.signature(reference_check.issue_replay_attestation).parameters
    assert "signer_key_id" not in inspect.signature(reference_check.issue_replay_attestation).parameters
