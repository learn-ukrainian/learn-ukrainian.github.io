"""PR #7662 repair 8: native-runner V4 origin, typed Sources, fixed policy.

The progress criterion is one boundary-to-boundary positive path plus the
six accepted P1 adversarial repros. Fixtures substitute executable, VESUM
backend, and custody roots at the lowest IO edge. They do not insert
canonical observation rows, fake terminal observations, replace the runtime
writer/authorization, or add a test-only admission bypass.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import _v4_a7_real_slot_fixture as fx
import _v4_synthetic_chain_fixture as base_fixture
import pytest

from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.request_executor import RequestExecutor, RequestExecutorError
from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

FIXTURE_MODEL = "claude-sonnet-5"
FIXTURE_SESSION = "v4-runner-session-1"
REVIEWER_MODEL = "gpt-5.6-luna"
REVIEWER_SESSION = "11111111-1111-1111-1111-111111111111"
ROW_TEXT = fx.ROW_TEXT


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def isolated_plane(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    plane = tmp_path / "fleet-plane"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    return plane


def test_execute_capture_does_not_write_v4_observations(isolated_plane: Path) -> None:
    with RequestExecutor(root=isolated_plane) as executor:
        request = executor.create_request(recipient="claude", body="not a v4 origin")
        result = executor.execute_capture(
            request.request_id,
            events=(
                {"type": "system", "subtype": "init", "session_id": "s", "model": FIXTURE_MODEL},
                {"type": "result", "subtype": "success", "session_id": "s"},
            ),
            returncode=0,
        )
        assert result.state in {"complete", "incomplete", "failed"}
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 0


def test_authorize_author_execution_refuses_caller_row_hash(isolated_plane: Path) -> None:
    import inspect

    params = inspect.signature(RequestExecutor.authorize_author_execution).parameters
    assert "row_content_sha256" not in params
    assert "packet_sha256" not in params
    assert list(params) == ["self", "request_id", "slot_id", "expected_seat"]


def test_construct_completion_rejects_caller_policy_argument() -> None:
    import inspect

    assert "trust_policy" not in inspect.signature(ledger.construct_completion).parameters
    assert "trust_policy" not in inspect.signature(ledger.verify_private_replay).parameters


def test_authorization_race_against_start_sqlite(isolated_plane: Path) -> None:
    """Two sqlite connections: once start has left queued, late authorize refuses."""
    with RequestExecutor(root=isolated_plane) as authorizer, RequestExecutor(root=isolated_plane) as starter:
        request = authorizer.create_request(recipient="claude", body="race")
        binding = authorizer.authorize_author_execution(
            request_id=request.request_id,
            slot_id=fx.TARGET_SLOT_ID,
            expected_seat=FIXTURE_MODEL,
        )
        assert binding["role"] == "author"
        starter.claim_v4_runner_execution(request_id=request.request_id)
        late = authorizer.create_request(recipient="claude", body="late")
        # A second request can authorize a different slot, but the started
        # request cannot acquire another binding.
        with pytest.raises(RequestExecutorError, match="not authorizable"):
            authorizer.authorize_author_execution(
                request_id=request.request_id,
                slot_id="v4p-standard-correct-002",
                expected_seat=FIXTURE_MODEL,
            )
        assert late.state == "queued"


def test_fabricated_capture_cannot_mint_authority(isolated_plane: Path) -> None:
    with RequestExecutor(root=isolated_plane) as executor:
        request = executor.create_request(recipient="claude", body="fabricated")
        executor.authorize_author_execution(
            request_id=request.request_id, slot_id=fx.TARGET_SLOT_ID, expected_seat=FIXTURE_MODEL
        )
        executor.execute_capture(
            request.request_id,
            adapter="claude",
            events=(
                {"type": "system", "subtype": "init", "session_id": "other", "model": FIXTURE_MODEL},
                {"type": "result", "subtype": "success", "session_id": "other"},
            ),
            raw_bytes=b"NOT THE EVENTS",
            returncode=0,
        )
        assert executor.resolve_v4_execution_observation(
            task_id="missing", run_id="missing", role="author"
        ) is None
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 0


def test_sources_invalid_input_is_not_successful(isolated_plane: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio
    import importlib.util
    import sys

    server_path = Path(__file__).resolve().parents[3] / ".mcp" / "servers" / "sources" / "server.py"
    spec = importlib.util.spec_from_file_location("sources_server_v4_neg", server_path)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v4_neg"] = srv
    spec.loader.exec_module(srv)
    monkeypatch.setattr(v4_store, "open_production_authority_store", lambda *, write=False: ArtifactStore(root=isolated_plane))
    _content, is_error, typed = asyncio.run(srv._dispatch_tool_call("verify_word", {"word": ""}))
    assert is_error is False
    assert typed is not None
    assert typed["success"] is False
    assert typed["disposition"] == "invalid_input"
    _stress_content, stress_error, stress_typed = asyncio.run(srv._dispatch_tool_call("verify_stress", {"word": "vesum:made-up"}))
    if stress_error is False and stress_typed is not None:
        assert stress_typed["success"] is False
        assert stress_typed["disposition"] in {"invalid_input", "not_found", "negative", "ambiguous"}
    with ArtifactStore(root=isolated_plane) as store:
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchall()
        # No attempt capability => nothing recorded.
        assert int(rows[0]["n"]) == 0


def test_foreign_stale_attempt_capability_fails_closed(isolated_plane: Path) -> None:
    with ArtifactStore(root=isolated_plane) as store:
        resolved = v4_store.resolve_active_attempt_by_capability_digest(
            capability_digest="a" * 64, conn=store.connection, is_pg=False
        )
        assert resolved is None


def test_caller_policy_is_not_an_admission_argument() -> None:
    import inspect

    assert "trust_policy" not in inspect.signature(ledger.construct_completion).parameters
    with pytest.raises(TypeError):
        ledger.construct_completion(trust_policy={"schema_version": "nope"})  # type: ignore[call-arg]


def test_revoked_production_policy_invalidates_the_previous_chain(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    row_content_sha256 = _sha(ROW_TEXT)
    real = fx.build_author_execution_receipt(row_content_sha256)
    revoked = trust.build_test_trust_policy(
        fleet_execution={fx.FLEET_KEY_ID: fx.FLEET_PUBLIC_KEY_HEX},
        revoked_key_ids=frozenset({fx.FLEET_KEY_ID}),
    )
    fx.install_policy_resource(monkeypatch, tmp_path, revoked)
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=real, row_content_sha256=row_content_sha256)


def test_sources_echoed_lexical_argument_is_not_the_identifier() -> None:
    identifier = v4_store.immutable_evidence_identifier(
        namespace="vesum",
        source_version="fixture-version",
        typed_result={"word": "книга", "matches": [{"lemma": "книга"}]},
    )
    assert identifier.startswith("vesum:")
    assert identifier != "книга"
    assert "книга" not in identifier


# Register the owners of every cross-module fixture explicitly. This test must
# collect the real PostgreSQL cluster and prepared operation without depending
# on another module's collection order.
pytest_plugins = (
    "test_v4_packaged_operation_boundary",
    "test_v4_operation_lifecycle",
    "test_v4_protected_parent_mechanism",
)


@pytest.fixture
def synthetic_trust_bundle(signing_resources, monkeypatch):
    from _v4_provenance_resource_fixture import synthetic_resources

    monkeypatch.setenv("HRAMATKA_V4_ADMISSION_ENABLED", "1")
    with synthetic_resources():
        yield


def test_boundary_to_boundary_positive_source_free(tmp_path, monkeypatch, pg_cluster, built_wheel, signing_resources, synthetic_trust_bundle) -> None:
    """Parent capture → actual Sources HTTP → opaque issuance → A7/A8 replay.

    This proves the public mechanism below the separate private auth adapter.
    """
    from _v4_provenance_resource_fixture import synthetic_wheel
    from test_v4_protected_parent_mechanism import _run_real_pair

    tmp_root = base_fixture.build_synthetic_chain_root(tmp_path / "slot-root", resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path / "slot-root")
    fixture_wheel = synthetic_wheel(built_wheel, tmp_path / "synthetic-runtime.whl")
    pair = _run_real_pair(pg_cluster, tmp_path, monkeypatch, fixture_wheel, signing_resources, False)
    row_text = pair["row"]["row_text"]
    author_receipt = pair["author_receipt"]
    reviewer_receipt = pair["reviewer_receipt"]
    record = pair["record"]
    assert record["harness"] == "claude" and record["seat_or_model"] == FIXTURE_MODEL
    assert record["row_content_sha256"] == _sha(row_text)
    assert not any(record[key] for key in ("saw_source_text", "saw_heldout", "saw_eligible_unit_ids"))
    inv = pair["invocation"]
    assert inv["success"] is True and inv["identifier"].startswith(("vesum:", "sources:"))
    attestation = sources_authority.issue_verifier_attestation(invocation_id=inv["invocation_id"])
    assert attestation["identifier"] == inv["identifier"]
    verifier_receipt = evidence_binder.build_verifier_receipt(attestation=attestation)
    evidence_receipt = evidence_binder.build_evidence_receipt(_sha(row_text), [verifier_receipt])
    monkeypatch.setenv("HRAMATKA_V4_ADMISSION_ENABLED", "1")

    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (tmp_root / "data/projects/open_model_data/admission/dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))
    reference_check_receipt = fx.build_reference_check_receipt(row_text=row_text)
    reference_check_signature, replay_attestation = fx.build_reference_check_authenticity(reference_check_receipt, row_text=row_text)
    completion = ledger.construct_completion(
        slot_id=fx.TARGET_SLOT_ID,
        salt=fx.TEST_SALT,
        candidate_unit_ids=list(fx.CANDIDATE_UNIT_IDS),
        a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
        seal_receipt_path=sealed["seal_receipt_path"],
        membership_dir=sealed["membership_dir"],
        packet_dir=sealed["packet_dir"],
        manifest=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text()),
        a2_receipt=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text()),
        row_text=row_text,
        tier="silver",
        author_execution_receipt=author_receipt,
        reviewer_execution_receipt=reviewer_receipt,
        evidence_receipt=evidence_receipt,
        reference_check_receipt=reference_check_receipt,
        reference_check_signature=reference_check_signature,
        replay_attestation=replay_attestation,
        rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
    )
    public_completion = completion["public_completion"]
    ledger_path = tmp_path / "batch_state/open-model-data/v4-a7-factory/v4_a7_private_ledger_v1.json"
    ledger.write_ledger({public_completion["slot_id"]: completion["private_entry"]}, ledger_path)
    admission_dir = tmp_root / "data/projects/open_model_data/admission"
    a7_receipt = a7.build_receipt(tmp_root, a7_completions=[public_completion])
    a7.validate_receipt_independently(a7_receipt, tmp_root)
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7_receipt))
    a8_completion = {
        "stage": "A8",
        "slot_id": public_completion["slot_id"],
        "row_id": public_completion["row_id"],
        "row_content_sha256": public_completion["row_content_sha256"],
        "trust_policy_sha256": public_completion["trust_policy_sha256"],
    }
    a8_receipt = a8.build_receipt(tmp_root, a8_completions=[a8_completion])
    a8.validate_receipt_independently(a8_receipt, tmp_root)
    a8.validate_a8_completions_match_a7(a8_receipt["a8_completions"], a7_receipt["a7_completions"])
    stored_ledger = ledger.load_ledger(ledger_path)
    ledger.verify_private_replay(
        a7_receipt,
        stored_ledger,
        salt=fx.TEST_SALT,
        a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
        seal_receipt_path=sealed["seal_receipt_path"],
        membership_dir=sealed["membership_dir"],
        packet_dir=sealed["packet_dir"],
        manifest=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text()),
        a2_receipt=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text()),
    )


@pytest.mark.postgres
def test_authorization_race_against_start_postgres(tmp_path, monkeypatch, pg_cluster, prepared) -> None:
    from test_v4_operation_lifecycle import claim, role_connection

    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        owned = claim(conn, prepared)
    with RequestExecutor(root=tmp_path) as authorizer:
        with pytest.raises(RequestExecutorError, match="not authorizable"):
            authorizer.authorize_author_execution(request_id=owned["request_id"], slot_id="v4p-standard-correct-002", expected_seat=FIXTURE_MODEL)
        with pytest.raises(RequestExecutorError, match="retired"):
            authorizer.claim_v4_runner_execution(request_id=owned["request_id"])
