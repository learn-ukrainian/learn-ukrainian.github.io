"""PR #7662 repair 6/7 acceptance tests: the operator-approved canonical
Fleet Comms authority store, the real execution-boundary writer, the fixed
canonical-PostgreSQL production resolution, the opaque-ID-only production
issuer entrypoints, fixed Hramatka signing-key custody, and the
digest-pinned/rotatable production trust policy.

Mechanism-only: no test here ever provisions a real production key, applies
a live migration, or writes to the real default Fleet Comms plane. Every
store test opens an isolated ``ArtifactStore(root=tmp_path)``/
``RequestExecutor(root=tmp_path)``.

Repair 7 moves the issuer test seam DOWN a layer: instead of replacing the
resolver wholesale, tests substitute the single fixed store opener
(``_open_canonical_authority_store``) with an isolated ``tmp_path`` plane,
so the real resolve path -- including record validation and readback --
runs for real. Execution observations are produced by driving the actual
``RequestExecutor.execute_capture`` finalization against a controlled,
source-free runtime capture; no test hands the executor a pre-built
observation, because no such API exists.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import _v4_a7_real_slot_fixture as fx
import pytest

from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.request_executor import RequestExecutor, RequestExecutorError
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

ROW_SHA = "b" * 64
PACKET_SHA = "d" * 64
AUTHORSHIP_SHA = "f" * 64
RUBRIC_SHA = "1" * 64
FIXTURE_MODEL = "claude-sonnet-5-fixture"
FIXTURE_SESSION = "session-fixture-1"

# A source-free controlled runtime capture: Claude stream-json shaped, with
# a terminal ``result`` event, one assistant segment, and the provider's own
# model/session identity. Nothing here is Ukrainian source text, a row, or
# corpus content.
def _capture_events(*, model: str = FIXTURE_MODEL, session_id: str = FIXTURE_SESSION, text: str = "fixture output", terminal: bool = True) -> tuple[dict[str, Any], ...]:
    events: list[dict[str, Any]] = [
        {"type": "system", "subtype": "init", "session_id": session_id, "model": model},
        {
            "type": "assistant",
            "session_id": session_id,
            "message": {"model": model, "content": [{"type": "text", "text": text}]},
        },
    ]
    if terminal:
        events.append({"type": "result", "subtype": "success", "session_id": session_id, "is_error": False})
    return tuple(events)


def _authorized_author_request(executor: RequestExecutor, *, task_id: str = "task-1", run_id: str = "run-1", model: str = FIXTURE_MODEL) -> str:
    request = executor.create_request(recipient="claude", body="source-free fixture prompt")
    executor.authorize_v4_execution(
        request_id=request.request_id,
        task_id=task_id,
        run_id=run_id,
        role="author",
        expected_seat_or_model=model,
        row_content_sha256=ROW_SHA,
        packet_sha256=PACKET_SHA,
    )
    return request.request_id


def _authorized_reviewer_request(executor: RequestExecutor, *, task_id: str = "task-2", run_id: str = "run-2") -> str:
    request = executor.create_request(recipient="claude", body="source-free reviewer fixture prompt")
    executor.authorize_v4_execution(
        request_id=request.request_id,
        task_id=task_id,
        run_id=run_id,
        role="reviewer",
        expected_seat_or_model=FIXTURE_MODEL,
        row_content_sha256=ROW_SHA,
        packet_sha256=PACKET_SHA,
        authorship_receipt_sha256=AUTHORSHIP_SHA,
        rubric_sha256=RUBRIC_SHA,
    )
    return request.request_id


def _observation_outcome(executor: RequestExecutor, request_id: str) -> str:
    row = executor._conn.execute(
        "SELECT invocation_spec_json FROM requests WHERE request_id = ?", (request_id,)
    ).fetchone()
    return json.loads(str(row["invocation_spec_json"])).get("v4_execution_observation", "")


# --- the real execution boundary produces the observation -------------------


def test_execution_finalization_derives_a_complete_author_observation(tmp_path: Path) -> None:
    """The genuine capture path -- not a caller-built record -- is what
    produces an admissible author observation, and every runtime fact in it
    is derived from the boundary's own evidence."""
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        result = executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        assert result.state == "complete"
        assert _observation_outcome(executor, request_id) == "recorded"

        record = executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
        assert record is not None
        # Runtime identity comes from the provider's own capture events.
        assert record["seat_or_model"] == FIXTURE_MODEL
        assert record["session_id"] == FIXTURE_SESSION
        # Harness comes from the registry-resolved recipient.
        assert record["harness"] == "claude"
        # Result digest comes from the artifact the store actually persisted.
        assert record["raw_capture_artifact_id"] == result.raw_capture_artifact_id
        assert record["raw_capture_sha256"] == result.envelope.raw_capture_sha256
        # Terminality comes from the conformance envelope.
        assert record["status"] == "done"
        assert record["return_code"] == 0
        assert record["completion_state"] == "complete"
        assert record["terminal_event_observed"] is True
        # Blindness is structural: the boundary has no argument that could
        # ever set one of these true.
        assert record["saw_source_text"] is False
        assert record["saw_heldout"] is False
        assert record["saw_eligible_unit_ids"] is False
        # Author observations carry no reviewer-only field.
        assert record["verdict"] is None
        assert record["authorship_receipt_sha256"] is None


def test_execution_finalization_derives_the_prompt_digest_from_the_stored_body(tmp_path: Path) -> None:
    """``prompt_sha256`` is the digest of the exact bytes this executor
    durably stored as the request body -- never a caller-supplied digest
    (``authorize_v4_execution`` has no such parameter)."""
    import hashlib
    import inspect

    assert "prompt_sha256" not in inspect.signature(RequestExecutor.authorize_v4_execution).parameters
    body = "source-free fixture prompt"
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        record = executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
        assert record is not None
        assert record["prompt_sha256"] == hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_reviewer_observation_derives_the_verdict_from_the_models_own_output(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_reviewer_request(executor)
        executor.execute_capture(
            request_id,
            events=_capture_events(text="review body\nV4-REVIEW-VERDICT: PASS\n"),
            returncode=0,
        )
        record = executor.resolve_v4_execution_observation(task_id="task-2", run_id="run-2", role="reviewer")
        assert record is not None
        assert record["verdict"] == "PASS"
        assert record["authorship_receipt_sha256"] == AUTHORSHIP_SHA
        assert record["rubric_sha256"] == RUBRIC_SHA


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        pytest.param({"returncode": 1, "events": _capture_events(terminal=False)}, "refused:not-complete", id="failed-process"),
        pytest.param({"returncode": 0, "events": _capture_events(terminal=False)}, "refused:not-complete", id="interrupted-no-terminal-event"),
        pytest.param({"returncode": 0, "events": _capture_events(model="some-other-model")}, "refused:model-mismatch", id="cross-model"),
        pytest.param({"returncode": 0, "events": ({"type": "result", "subtype": "success", "session_id": FIXTURE_SESSION},)}, "refused:model-unobserved", id="model-unobserved"),
    ],
)
def test_no_observation_is_recorded_for_an_inadmissible_execution(tmp_path: Path, kwargs: dict[str, Any], expected: str) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, **kwargs)
        assert _observation_outcome(executor, request_id) == expected
        assert executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") is None


def test_ambiguous_capture_model_is_never_resolved_to_the_dispatch_expectation(tmp_path: Path) -> None:
    """Two disagreeing model identities in one capture are unobservable --
    the boundary must not fall back to what the dispatch expected."""
    contradictory = (
        {"type": "system", "subtype": "init", "session_id": FIXTURE_SESSION, "model": FIXTURE_MODEL},
        {"type": "assistant", "session_id": FIXTURE_SESSION, "message": {"model": "other-model", "content": [{"type": "text", "text": "x"}]}},
        {"type": "result", "subtype": "success", "session_id": FIXTURE_SESSION},
    )
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, events=contradictory, returncode=0)
        assert _observation_outcome(executor, request_id) == "refused:model-unobserved"


def test_reviewer_execution_without_an_observable_verdict_records_nothing(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_reviewer_request(executor)
        executor.execute_capture(request_id, events=_capture_events(text="a review with no verdict marker"), returncode=0)
        assert _observation_outcome(executor, request_id) == "refused:verdict-unobserved"
        assert executor.resolve_v4_execution_observation(task_id="task-2", run_id="run-2", role="reviewer") is None


def test_contradictory_reviewer_verdicts_are_unobservable(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_reviewer_request(executor)
        executor.execute_capture(
            request_id,
            events=_capture_events(text="V4-REVIEW-VERDICT: PASS\nV4-REVIEW-VERDICT: FAIL\n"),
            returncode=0,
        )
        assert _observation_outcome(executor, request_id) == "refused:verdict-unobserved"


def test_an_unauthorized_execution_produces_no_observation(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request = executor.create_request(recipient="claude", body="unbound fixture prompt")
        executor.execute_capture(request.request_id, events=_capture_events(), returncode=0)
        assert _observation_outcome(executor, request.request_id) == "unbound"


def test_a_slot_cannot_be_authorized_after_execution_starts(tmp_path: Path) -> None:
    """There is no retroactive authorization: once a request has left
    ``queued`` the dispatch binding can never be minted for it."""
    with RequestExecutor(root=tmp_path) as executor:
        request = executor.create_request(recipient="claude", body="late-binding fixture prompt")
        executor.execute_capture(request.request_id, events=_capture_events(), returncode=0)
        with pytest.raises(RequestExecutorError, match="not authorizable"):
            executor.authorize_v4_execution(
                request_id=request.request_id,
                task_id="task-late",
                run_id="run-late",
                role="author",
                expected_seat_or_model=FIXTURE_MODEL,
                row_content_sha256=ROW_SHA,
                packet_sha256=PACKET_SHA,
            )
        assert executor.resolve_v4_execution_observation(task_id="task-late", run_id="run-late", role="author") is None


def test_two_requests_cannot_claim_one_slot(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        _authorized_author_request(executor)
        with pytest.raises((v4_store.ExecutionDispatchBindingConflictError, sqlite3.IntegrityError)):
            _authorized_author_request(executor)


def test_a_completed_request_can_neither_re_execute_nor_re_record(tmp_path: Path) -> None:
    """Two layers of at-least-once safety: the executor refuses to re-run a
    request that already finalized, and even a direct retry of the identical
    canonical write is a silent no-op rather than a second row."""
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        first = executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
        assert first is not None
        with pytest.raises(RequestExecutorError, match="not executable"):
            executor.execute_capture(request_id, events=_capture_events(), returncode=0, reclaim=True)
        with executor.store._transaction() as conn:
            v4_store._persist_execution_observation(first, conn=conn, is_pg=False, request_id=request_id, commit=False)
        assert executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") == first
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 1


def test_the_execution_boundary_exposes_no_caller_built_observation_writer() -> None:
    """The adjudicated F3 blocker: a public passthrough ``record(dict)``
    method is not authorization, so none exists on either surface."""
    for surface in (ArtifactStore, RequestExecutor):
        assert not hasattr(surface, "record_v4_execution_observation")
        assert not hasattr(surface, "record_v4_sources_invocation")
    assert not hasattr(v4_store, "record_execution_observation")
    assert not hasattr(v4_store, "record_sources_invocation")


# --- fixed canonical PostgreSQL production resolution -----------------------


def test_production_authority_selection_takes_no_plane_argument() -> None:
    """No root, path, DSN, connection or authority parameter exists on the
    production selector, so no caller-level substitution is possible."""
    import inspect

    assert list(inspect.signature(v4_store.open_production_authority_store).parameters) == ["write"]
    assert list(inspect.signature(fleet_execution._open_canonical_authority_store).parameters) == []
    assert list(inspect.signature(sources_authority._open_canonical_authority_store).parameters) == []


def test_production_authority_refuses_the_sqlite_default() -> None:
    """A bare shell's SQLite default is not the deployed service authority."""
    with pytest.raises(v4_store.CanonicalAuthorityUnavailableError, match="PostgreSQL"):
        v4_store.open_production_authority_store()


def test_production_authority_refuses_an_unavailable_pg_plane(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configured for pg but with no reachable plane: refuse, never fall
    back to a local store."""
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", "")
    with pytest.raises(v4_store.CanonicalAuthorityUnavailableError, match="unavailable"):
        v4_store.open_production_authority_store()


def test_issue_author_execution_receipt_refuses_a_non_pg_authority_before_key_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(role: str) -> tuple[str, str]:
        raise AssertionError("key access must never happen without the canonical PG authority")

    monkeypatch.setattr(fleet_execution, "_load_signing_key", _boom)
    with pytest.raises(fleet_execution.FleetExecutionError, match="canonical V4 execution authority unavailable"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


def test_issue_verifier_attestation_refuses_a_non_pg_authority_before_key_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(role: str) -> tuple[str, str]:
        raise AssertionError("key access must never happen without the canonical PG authority")

    monkeypatch.setattr(sources_authority, "_load_signing_key", _boom)
    with pytest.raises(sources_authority.SourcesAuthorityError, match="canonical V4 Sources authority unavailable"):
        sources_authority.issue_verifier_attestation(invocation_id="inv-1")


def test_a_caller_selected_sqlite_plane_is_not_production_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An adversary who populates their own SQLite plane with a perfectly
    well-formed observation still cannot make production resolve it: the
    production selector never consults a caller-chosen root."""
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        assert executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") is not None

    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "sqlite")
    monkeypatch.setattr(fleet_execution, "_load_signing_key", lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(fleet_execution.FleetExecutionError, match="unavailable"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


# --- production issuers over a real resolved observation --------------------


def _patch_authority_plane(monkeypatch: pytest.MonkeyPatch, module: Any, tmp_path: Path) -> None:
    """Substitute the single fixed store opener with an isolated plane.

    This is the only in-process seam, and it is the same
    monkeypatch-the-fixed-internal-loader pattern the Sol acceptance matrix
    sanctions for key custody and the production policy resolver. There is
    no runtime argument, environment variable, or admission switch that can
    do this in production.
    """
    monkeypatch.setattr(module, "_open_canonical_authority_store", lambda: ArtifactStore(root=tmp_path))


def _patch_fleet(monkeypatch: pytest.MonkeyPatch, *, tmp_path: Path | None = None, key_loader=None, trust_policy=None) -> None:
    if tmp_path is not None:
        _patch_authority_plane(monkeypatch, fleet_execution, tmp_path)
    if key_loader is not None:
        monkeypatch.setattr(fleet_execution, "_load_signing_key", key_loader)
    if trust_policy is not None:
        monkeypatch.setattr(trust, "load_production_trust_policy", lambda: trust_policy)


def _seed_observation(tmp_path: Path, record: dict[str, Any]) -> None:
    """Write a record straight through the private persistence primitive.

    Used only to reach issuer branches an honest execution boundary can
    never produce (a canonical row that is somehow non-terminal). Production
    has no path here: the primitive is private, and the canonical plane is
    reachable only with the deployed PostgreSQL service credentials.
    """
    with ArtifactStore(root=tmp_path) as store:
        with store._transaction() as conn:
            v4_store._persist_execution_observation(record, conn=conn, is_pg=False, commit=False)


def _recorded_author_record(tmp_path: Path) -> dict[str, Any]:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        record = executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
    assert record is not None
    return record


def test_issue_author_execution_receipt_signature_accepts_only_task_and_run_id() -> None:
    import inspect

    assert list(inspect.signature(fleet_execution.issue_author_execution_receipt).parameters) == ["task_id", "run_id"]
    assert list(inspect.signature(fleet_execution.issue_reviewer_execution_receipt).parameters) == ["task_id", "run_id"]
    assert list(inspect.signature(sources_authority.issue_verifier_attestation).parameters) == ["invocation_id"]


def test_issue_author_execution_receipt_refuses_an_unknown_task_run_before_key_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(role: str) -> tuple[str, str]:
        raise AssertionError("key access must never happen for an unresolved observation")

    ArtifactStore(root=tmp_path).close()
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=_boom)
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_author_execution_receipt(task_id="ghost", run_id="ghost")


def test_issue_author_execution_receipt_refuses_without_a_provisioned_production_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unmonkeypatched key custody: the real ``load_production_signing_key``
    always refuses in mechanism-only production (no key file exists)."""
    _recorded_author_record(tmp_path)
    _patch_fleet(monkeypatch, tmp_path=tmp_path)
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


def test_issue_author_execution_receipt_end_to_end_and_idempotent_repeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The full chain: a genuine controlled execution produces the
    observation, the production issuer resolves it by opaque id alone, and
    repeat issuance is byte-identical."""
    record = _recorded_author_record(tmp_path)
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))

    receipt = fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")
    fleet_execution.verify_author_execution_receipt(
        receipt, trust_policy=policy, outcome_sha256=fleet_execution.V4_SHA256, row_content_sha256=record["row_content_sha256"]
    )
    assert receipt["exact_model"] == FIXTURE_MODEL
    assert receipt["harness"] == "claude"
    assert receipt["provider_session_id"] == FIXTURE_SESSION
    again = fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")
    assert receipt == again, "repeat issuance against the identical resolved observation must reproduce byte for byte"


def test_issue_reviewer_execution_receipt_resolves_the_reviewer_role(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_reviewer_request(executor)
        executor.execute_capture(request_id, events=_capture_events(text="V4-REVIEW-VERDICT: PASS"), returncode=0)
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))

    receipt = fleet_execution.issue_reviewer_execution_receipt(task_id="task-2", run_id="run-2")
    assert receipt["domain"] == "reviewer"
    assert receipt["verdict"] == "PASS"
    # An author receipt must not resolve from a reviewer-role slot.
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_author_execution_receipt(task_id="task-2", run_id="run-2")


def test_issue_author_execution_receipt_refuses_a_cross_run_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _recorded_author_record(tmp_path)
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-OTHER")


@pytest.mark.parametrize("mutation", [{"status": "running"}, {"return_code": 1}, {"completion_state": "failed"}, {"terminal_event_observed": False}])
def test_issue_author_execution_receipt_refuses_a_nonterminal_canonical_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: dict[str, Any]) -> None:
    base = _recorded_author_record(tmp_path)
    bad = {**base, **mutation, "task_id": "task-bad", "run_id": "run-bad"}
    _seed_observation(tmp_path, bad)
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    with pytest.raises((fleet_execution.FleetExecutionError, ValueError)):
        fleet_execution.issue_author_execution_receipt(task_id="task-bad", run_id="run-bad")


# --- canonical store: idempotency / conflict / rollback ---------------------


def test_execution_observation_write_refuses_a_conflicting_duplicate(tmp_path: Path) -> None:
    base = _recorded_author_record(tmp_path)
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.ExecutionObservationConflictError, match="different execution observation"):
            v4_store._persist_execution_observation({**base, "status": "failed"}, conn=conn, is_pg=False, commit=False)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author") == base


def test_execution_observation_resolves_none_for_an_unknown_key(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="nope", run_id="nope", role="author") is None


def test_execution_observation_write_rejects_a_malformed_record_before_any_persistence(tmp_path: Path) -> None:
    """Validation runs before the DB is touched -- a rejected write leaves
    no partial row behind (rollback/failure handling)."""
    base = dict(_recorded_author_record(tmp_path))
    malformed = {k: v for k, v in base.items() if k != "harness"}
    malformed["task_id"] = "task-malformed"
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="exactly"):
            v4_store._persist_execution_observation(malformed, conn=conn, is_pg=False, commit=False)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="task-malformed", run_id="run-1", role="author") is None


def test_author_execution_observation_refuses_reviewer_only_fields(tmp_path: Path) -> None:
    base = _recorded_author_record(tmp_path)
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            v4_store._persist_execution_observation({**base, "task_id": "t-x", "verdict": "PASS"}, conn=conn, is_pg=False, commit=False)


def test_reviewer_execution_observation_requires_every_reviewer_only_field(tmp_path: Path) -> None:
    base = _recorded_author_record(tmp_path)
    incomplete = {**base, "task_id": "t-y", "role": "reviewer", "authorship_receipt_sha256": AUTHORSHIP_SHA, "rubric_sha256": RUBRIC_SHA, "verdict": None}
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            v4_store._persist_execution_observation(incomplete, conn=conn, is_pg=False, commit=False)


def test_execution_observation_store_is_isolated_by_role(tmp_path: Path) -> None:
    _recorded_author_record(tmp_path)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="reviewer") is None


# --- the real Sources recording boundary -----------------------------------

VERIFY_WORD_ARGS = {"word": "книга"}
VERIFY_WORD_RESULT = "книга | VESUM: valid (lemma=книга, id=vesum:12345, tag=noun)"
TOOL_VERSION = "e" * 64


def _record_invocation(store: ArtifactStore, **overrides: Any) -> dict[str, Any] | None:
    kwargs: dict[str, Any] = {
        "tool_name": "verify_word",
        "arguments": VERIFY_WORD_ARGS,
        "result_text": VERIFY_WORD_RESULT,
        "tool_version": TOOL_VERSION,
        "request_id": "req-1",
        "row_content_sha256": ROW_SHA,
        "claimed_lookup_ids": ["vesum:12345"],
    }
    kwargs.update(overrides)
    return store.record_v4_sources_invocation_from_tool_result(**kwargs)


def test_sources_invocation_records_a_genuine_call(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        record = _record_invocation(store)
        assert record is not None
        # The identifier is derived from the arguments the tool really ran on.
        assert record["identifier"] == "книга"
        assert record["tool_id"] == "mcp__sources__verify_word"
        assert record["tool_version"] == TOOL_VERSION
        assert record["success"] is True
        assert store.resolve_v4_sources_invocation(invocation_id=record["invocation_id"]) == record


def test_sources_invocation_identifier_cannot_be_declared_by_the_caller() -> None:
    """The retired ``_v4_evidence_identifier`` has no replacement parameter:
    a spoofed identifier is structurally impossible, not merely rejected."""
    import inspect

    params = inspect.signature(v4_store.record_sources_invocation_from_tool_result).parameters
    assert "identifier" not in params
    assert "tool_id" not in params
    assert "tool_result_sha256" not in params
    assert "success" not in params


@pytest.mark.parametrize(
    ("overrides", "why"),
    [
        pytest.param({"tool_name": "search_literary"}, "unsanctioned tool", id="unsanctioned-tool"),
        pytest.param({"tool_name": "verify_quote"}, "text-argument tool is not sanctioned", id="text-argument-tool"),
        pytest.param({"result_text": ""}, "an empty result proves nothing", id="empty-result"),
        pytest.param({"claimed_lookup_ids": ["vesum:99999"]}, "claim absent from the genuine result", id="fabricated-lookup-id"),
        pytest.param({"claimed_lookup_ids": ["123"]}, "substring coincidence inside vesum:12345", id="substring-coincidence"),
        pytest.param({"claimed_lookup_ids": []}, "no claim at all", id="no-claims"),
        pytest.param({"claimed_lookup_ids": ["vesum:12345", "vesum:12345"]}, "duplicate claims", id="duplicate-claims"),
        pytest.param({"arguments": {"word": "інше"}}, "the result does not mention this word", id="argument-result-mismatch"),
        pytest.param({"arguments": {}}, "no primary argument to derive an identifier from", id="missing-argument"),
        pytest.param({"row_content_sha256": "not-a-digest"}, "malformed row binding", id="malformed-row-binding"),
        pytest.param({"request_id": ""}, "no request correlation", id="missing-request-id"),
    ],
)
def test_sources_invocation_refuses_to_record_a_fabricated_or_failed_call(tmp_path: Path, overrides: dict[str, Any], why: str) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert _record_invocation(store, **overrides) is None, why
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchone()
        assert int(rows["n"]) == 0


def test_sources_invocation_is_idempotent_on_a_canonical_retry(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        first = _record_invocation(store)
        second = _record_invocation(store)
        assert first == second
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchone()
        assert int(rows["n"]) == 1


def test_sources_invocation_conflicting_duplicate_leaves_prior_evidence_unchanged(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        original = _record_invocation(store)
        assert original is not None
        with store._transaction() as conn:
            with pytest.raises(v4_store.SourcesInvocationConflictError, match="different sources invocation"):
                v4_store._persist_sources_invocation({**original, "success": False}, conn=conn, is_pg=False, commit=False)
        assert store.resolve_v4_sources_invocation(invocation_id=original["invocation_id"]) == original


def test_sources_invocation_resolves_none_for_an_unknown_invocation_id(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_sources_invocation(invocation_id="nope") is None


def test_verification_tool_ids_are_derived_from_canonical_invocations(tmp_path: Path) -> None:
    """An observation's ``verification_tool_ids`` come from canonically
    recorded invocations bound to the same request -- never from a list the
    dispatch caller supplies (there is no such parameter)."""
    with RequestExecutor(root=tmp_path) as executor:
        request_id = _authorized_author_request(executor)
        recorded = executor.store.record_v4_sources_invocation_from_tool_result(
            tool_name="verify_word",
            arguments=VERIFY_WORD_ARGS,
            result_text=VERIFY_WORD_RESULT,
            tool_version=TOOL_VERSION,
            request_id=request_id,
            row_content_sha256=ROW_SHA,
            claimed_lookup_ids=["vesum:12345"],
        )
        assert recorded is not None
        executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        record = executor.resolve_v4_execution_observation(task_id="task-1", run_id="run-1", role="author")
        assert record is not None
        assert record["verification_tool_ids"] == ["mcp__sources__verify_word"]


def test_compute_invocation_id_is_deterministic_and_content_addressed() -> None:
    kwargs = dict(tool_id="mcp__sources__verify_word", tool_version="v1", request_id="r1", row_content_sha256="a" * 64, identifier="vesum:x", tool_result_sha256="b" * 64, lookup_ids=["l1", "l2"])
    first = v4_store.compute_invocation_id(**kwargs)
    second = v4_store.compute_invocation_id(**kwargs)
    assert first == second
    assert v4_store.compute_invocation_id(**{**kwargs, "tool_result_sha256": "c" * 64}) != first


def _patch_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, key_loader=None, trust_policy=None) -> None:
    _patch_authority_plane(monkeypatch, sources_authority, tmp_path)
    if key_loader is not None:
        monkeypatch.setattr(sources_authority, "_load_signing_key", key_loader)
    if trust_policy is not None:
        monkeypatch.setattr(trust, "load_production_trust_policy", lambda: trust_policy)


def test_issue_verifier_attestation_refuses_an_unknown_invocation_before_key_access(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ArtifactStore(root=tmp_path).close()
    _patch_sources(monkeypatch, tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(sources_authority.SourcesAuthorityError, match="unknown invocation_id"):
        sources_authority.issue_verifier_attestation(invocation_id="ghost")


def test_issue_verifier_attestation_refuses_an_unsuccessful_canonical_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with ArtifactStore(root=tmp_path) as store:
        record = _record_invocation(store)
        assert record is not None
        failed = {**record, "invocation_id": "inv-failed", "success": False}
        with store._transaction() as conn:
            v4_store._persist_sources_invocation(failed, conn=conn, is_pg=False, commit=False)
    _patch_sources(monkeypatch, tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access for a failed invocation")))
    with pytest.raises(sources_authority.SourcesAuthorityError, match="not recorded as successful"):
        sources_authority.issue_verifier_attestation(invocation_id="inv-failed")


def test_issue_verifier_attestation_refuses_without_a_provisioned_production_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with ArtifactStore(root=tmp_path) as store:
        record = _record_invocation(store)
    assert record is not None
    _patch_sources(monkeypatch, tmp_path)
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        sources_authority.issue_verifier_attestation(invocation_id=record["invocation_id"])


def test_issue_verifier_attestation_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with ArtifactStore(root=tmp_path) as store:
        record = _record_invocation(store)
    assert record is not None
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(sources={"k1": pub})
    _patch_sources(monkeypatch, tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    attestation = sources_authority.issue_verifier_attestation(invocation_id=record["invocation_id"])
    sources_authority.verify_verifier_attestation(
        attestation, trust_policy=policy, outcome_sha256=sources_authority.V4_SHA256, row_content_sha256=ROW_SHA
    )
    assert attestation["tool_id"] == "mcp__sources__verify_word"


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
