"""PR #7662 repair 8 acceptance tests: canonical Fleet Comms authority store,
opaque-ID issuers, Hramatka signing-key custody, and digest-pinned trust
policy. ``RequestExecutor.execute_capture`` is not a V4 origin; runner-owned
observations are produced in ``test_v4_runner_origin_mechanism.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import _v4_a7_real_slot_fixture as fx
import pytest
from test_v4_runner_origin_mechanism import (
    FIXTURE_MODEL,
    FIXTURE_SESSION,
)

from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.request_executor import RequestExecutor, RequestExecutorError
from scripts.projects.open_model_data import v4_a3_reference_check as reference_check
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

# Bound at import, before any test-policy seam is installed.
_REAL_LOAD_PRODUCTION_TRUST_POLICY = trust.load_production_trust_policy

ROW_SHA = "b" * 64
PACKET_SHA = "d" * 64
AUTHORSHIP_SHA = "f" * 64
RUBRIC_SHA = "1" * 64


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


def _authorized_author_request(executor: RequestExecutor, *, model: str = FIXTURE_MODEL) -> tuple[str, dict[str, Any]]:
    request = executor.create_request(recipient="claude", body="source-free fixture prompt")
    binding = executor.authorize_author_execution(
        request_id=request.request_id,
        slot_id=fx.TARGET_SLOT_ID,
        expected_seat=model,
    )
    return request.request_id, binding


def _isolate_plane(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path))
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    monkeypatch.setattr(v4_store, "open_production_authority_store", lambda *, write=False: ArtifactStore(root=tmp_path))


_OWNED_PG = None
_OWNED_WHEEL = None


@pytest.fixture(autouse=True)
def _owned_resources(pg_cluster, built_wheel, monkeypatch):
    monkeypatch.setitem(globals(), "_OWNED_PG", pg_cluster)
    monkeypatch.setitem(globals(), "_OWNED_WHEEL", built_wheel)


pytest_plugins = ("test_v4_protected_parent_mechanism",)


def _run_author_via_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compatibility helper now produces actual parent-owned PG observations."""
    from _v4_packaged_runtime_fixture import produce_author_record
    return produce_author_record(tmp_path, _OWNED_PG, monkeypatch, _OWNED_WHEEL)


# --- execute_capture is not a V4 origin ------------------------------------


def test_execute_capture_never_writes_a_v4_observation(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id, binding = _authorized_author_request(executor)
        result = executor.execute_capture(request_id, events=_capture_events(), returncode=0)
        assert result.state in {"complete", "incomplete", "failed"}
        assert executor.resolve_v4_execution_observation(
            task_id=binding["task_id"], run_id=binding["run_id"], role="author"
        ) is None
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 0


def test_authorize_author_execution_takes_no_caller_hashes() -> None:
    import inspect

    params = inspect.signature(RequestExecutor.authorize_author_execution).parameters
    assert "prompt_sha256" not in params
    assert "row_content_sha256" not in params
    assert "packet_sha256" not in params
    assert list(params) == ["self", "request_id", "slot_id", "expected_seat"]


def test_a_slot_cannot_be_authorized_after_execution_starts(tmp_path: Path) -> None:
    """There is no retroactive authorization: once a request has left
    ``queued`` the dispatch binding can never be minted for it."""
    with RequestExecutor(root=tmp_path) as executor:
        request = executor.create_request(recipient="claude", body="late-binding fixture prompt")
        executor.execute_capture(request.request_id, events=_capture_events(), returncode=0)
        with pytest.raises(RequestExecutorError, match="not authorizable"):
            executor.authorize_author_execution(
                request_id=request.request_id,
                slot_id=fx.TARGET_SLOT_ID,
                expected_seat=FIXTURE_MODEL,
            )


def test_an_already_bound_request_cannot_be_rebound(tmp_path: Path) -> None:
    with RequestExecutor(root=tmp_path) as executor:
        request_id, _binding = _authorized_author_request(executor)
        with pytest.raises(v4_store.ExecutionDispatchBindingConflictError):
            executor.authorize_author_execution(
                request_id=request_id,
                slot_id="v4p-standard-correct-002",
                expected_seat=FIXTURE_MODEL,
            )


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


def test_a_caller_selected_sqlite_plane_is_not_production_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    """The production selector never consults a caller-chosen SQLite root."""
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "sqlite")
    monkeypatch.setattr(fleet_execution, "_load_signing_key", lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(fleet_execution.FleetExecutionError, match="unavailable"):
        fleet_execution.issue_author_execution_receipt(task_id="task-1", run_id="run-1")


# --- production issuers over a real resolved observation --------------------


def _patch_authority_plane(monkeypatch: pytest.MonkeyPatch, module: Any, tmp_path: Path) -> None:
    """Use only an owned scoped credential resource with the real PG opener."""
    from learn_ukrainian_v4_runtime import scoped_store
    from psycopg.conninfo import make_conninfo
    _OWNED_PG.execute("ALTER ROLE hramatka_v4_control_writer LOGIN")
    path = tmp_path / "control.dsn"
    path.write_text(make_conninfo(_OWNED_PG.info.dsn, user="hramatka_v4_control_writer"))
    path.chmod(0o600)
    monkeypatch.setattr(scoped_store, "control_credential_path", lambda: path)


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
            v4_store._persist_execution_observation(record, conn=conn, is_pg=store.authority.value == "pg", commit=False)


def _recorded_author_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, Any], dict[str, Any]]:
    return _run_author_via_runner(tmp_path, monkeypatch)


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
    binding, _record = _recorded_author_record(tmp_path, monkeypatch)
    _patch_fleet(monkeypatch, tmp_path=tmp_path)
    with pytest.raises(trust.TrustAuthorityError, match="no production signing key is provisioned"):
        fleet_execution.issue_author_execution_receipt(task_id=binding["task_id"], run_id=binding["run_id"])


def test_issue_author_execution_receipt_end_to_end_and_idempotent_repeat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The full chain: a genuine runner-owned execution produces the
    observation, the production issuer resolves it by opaque id alone, and
    repeat issuance is byte-identical."""
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    binding, record = _recorded_author_record(tmp_path, monkeypatch)

    receipt = fleet_execution.issue_author_execution_receipt(task_id=binding["task_id"], run_id=binding["run_id"])
    fleet_execution.verify_author_execution_receipt(
        receipt, trust_policy=policy, outcome_sha256=fleet_execution.V4_SHA256, row_content_sha256=record["row_content_sha256"]
    )
    assert receipt["exact_model"] == FIXTURE_MODEL
    assert receipt["harness"] == "claude"
    assert receipt["provider_session_id"] == record["session_id"]
    again = fleet_execution.issue_author_execution_receipt(task_id=binding["task_id"], run_id=binding["run_id"])
    assert receipt == again, "repeat issuance against the identical resolved observation must reproduce byte for byte"


def test_issue_reviewer_execution_receipt_refuses_an_author_slot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binding, _record = _recorded_author_record(tmp_path, monkeypatch)
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_reviewer_execution_receipt(task_id=binding["task_id"], run_id=binding["run_id"])


def test_issue_author_execution_receipt_refuses_a_cross_run_lookup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binding, _record = _recorded_author_record(tmp_path, monkeypatch)
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access")))
    with pytest.raises(fleet_execution.FleetExecutionError, match="unknown task_id/run_id"):
        fleet_execution.issue_author_execution_receipt(task_id=binding["task_id"], run_id="run-OTHER")


@pytest.mark.parametrize("mutation", [{"status": "running"}, {"return_code": 1}, {"completion_state": "failed"}, {"terminal_event_observed": False}])
def test_issue_author_execution_receipt_refuses_a_nonterminal_canonical_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: dict[str, Any]) -> None:
    _binding, base = _recorded_author_record(tmp_path, monkeypatch)
    bad = {**base, **mutation, "task_id": "task-bad", "run_id": "run-bad"}
    _seed_observation(tmp_path, bad)
    priv, pub = trust.generate_test_keypair()
    policy = trust.build_test_trust_policy(fleet_execution={"k1": pub})
    _patch_fleet(monkeypatch, tmp_path=tmp_path, key_loader=lambda role: (priv, "k1"), trust_policy=(policy, trust.trust_policy_sha256(policy)))
    with pytest.raises((fleet_execution.FleetExecutionError, ValueError)):
        fleet_execution.issue_author_execution_receipt(task_id="task-bad", run_id="run-bad")


# --- canonical store: idempotency / conflict / rollback ---------------------


def test_execution_observation_write_refuses_a_conflicting_duplicate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binding, base = _recorded_author_record(tmp_path, monkeypatch)
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.ExecutionObservationConflictError, match="different execution observation"):
            v4_store._persist_execution_observation({**base, "status": "failed"}, conn=conn, is_pg=store.authority.value == "pg", commit=False)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id=binding["task_id"], run_id=binding["run_id"], role="author") == base


def test_execution_observation_resolves_none_for_an_unknown_key(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="nope", run_id="nope", role="author") is None


def test_execution_observation_write_rejects_a_malformed_record_before_any_persistence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Validation runs before the DB is touched -- a rejected write leaves
    no partial row behind (rollback/failure handling)."""
    _binding, base = _recorded_author_record(tmp_path, monkeypatch)
    malformed = {k: v for k, v in base.items() if k != "harness"}
    malformed["task_id"] = "task-malformed"
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="exactly"):
            v4_store._persist_execution_observation(malformed, conn=conn, is_pg=store.authority.value == "pg", commit=False)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id="task-malformed", run_id=base["run_id"], role="author") is None


def test_author_execution_observation_refuses_reviewer_only_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _binding, base = _recorded_author_record(tmp_path, monkeypatch)
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            v4_store._persist_execution_observation({**base, "task_id": "t-x", "verdict": "PASS"}, conn=conn, is_pg=store.authority.value == "pg", commit=False)


def test_reviewer_execution_observation_requires_every_reviewer_only_field(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _binding, base = _recorded_author_record(tmp_path, monkeypatch)
    incomplete = {**base, "task_id": "t-y", "role": "reviewer", "authorship_receipt_sha256": AUTHORSHIP_SHA, "rubric_sha256": RUBRIC_SHA, "verdict": None}
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        with pytest.raises(v4_store.CanonicalAuthorityStoreError, match="reviewer-only"):
            v4_store._persist_execution_observation(incomplete, conn=conn, is_pg=store.authority.value == "pg", commit=False)


def test_execution_observation_store_is_isolated_by_role(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    binding, _record = _recorded_author_record(tmp_path, monkeypatch)
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_execution_observation(task_id=binding["task_id"], run_id=binding["run_id"], role="reviewer") is None


# --- the real Sources recording boundary -----------------------------------

TOOL_VERSION = "e" * 64
TYPED_IDENTIFIER = "vesum:" + "c" * 64
TYPED_SUPPORTED = {
    "tool": "verify_word",
    "disposition": "supported",
    "success": True,
    "evidence_identifiers": [TYPED_IDENTIFIER],
    "result": {"word": "книга", "matches": [{"lemma": "книга"}]},
}


def _running_attempt(tmp_path: Path) -> dict[str, Any]:
    with RequestExecutor(root=tmp_path) as executor:
        request_id, binding = _authorized_author_request(executor)
        claim = executor.claim_v4_runner_execution(request_id=request_id)
    return {**claim, "binding": binding, "request_id": request_id}


def _record_invocation(tmp_path: Path, *, tool_name: str = "verify_word", typed_outcome: dict[str, Any] | None = None) -> dict[str, Any] | None:
    claim = _running_attempt(tmp_path)
    with ArtifactStore(root=tmp_path) as store:
        return store.record_v4_sources_invocation_from_typed_outcome(
            attempt_id=claim["attempt_id"],
            tool_name=tool_name,
            tool_version=TOOL_VERSION,
            typed_outcome=typed_outcome if typed_outcome is not None else TYPED_SUPPORTED,
        )


def test_sources_invocation_records_a_typed_call(tmp_path: Path) -> None:
    record = _record_invocation(tmp_path)
    assert record is not None
    assert record["identifier"] == TYPED_IDENTIFIER
    assert record["identifier"] != "книга"
    assert record["tool_id"] == "mcp__sources__verify_word"
    assert record["tool_version"] == TOOL_VERSION
    assert record["success"] is True
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_sources_invocation(invocation_id=record["invocation_id"]) == record


def test_sources_invocation_identifier_cannot_be_declared_by_the_caller() -> None:
    """The retired caller identifier/row-hash path has no replacement
    parameter: a spoofed identifier is structurally impossible."""
    import inspect

    params = inspect.signature(v4_store.record_sources_invocation_from_typed_outcome).parameters
    assert "identifier" not in params
    assert "tool_id" not in params
    assert "row_content_sha256" not in params
    assert "request_id" not in params
    assert "success" not in params


@pytest.mark.parametrize(
    ("kwargs", "why"),
    [
        pytest.param({"tool_name": "search_literary"}, "unsanctioned tool", id="unsanctioned-tool"),
        pytest.param({"tool_name": "verify_quote"}, "text-argument tool is not sanctioned", id="text-argument-tool"),
        pytest.param({"tool_name": "vet_vocabulary"}, "Sol-approved exclusion until typed contract", id="excluded-vet"),
        pytest.param(
            {"typed_outcome": {"tool": "verify_word", "disposition": "supported", "success": True, "evidence_identifiers": ["книга"]}},
            "lexical echo is not a vesum:/sources: identifier",
            id="echoed-word",
        ),
    ],
)
def test_sources_invocation_refuses_to_record_a_fabricated_or_failed_call(tmp_path: Path, kwargs: dict[str, Any], why: str) -> None:
    assert _record_invocation(tmp_path, **kwargs) is None, why
    with ArtifactStore(root=tmp_path) as store:
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchone()
        assert int(rows["n"]) == 0


def test_retired_caller_correlation_path_records_nothing(tmp_path: Path) -> None:
    claim = _running_attempt(tmp_path)
    with ArtifactStore(root=tmp_path) as store:
        assert (
            v4_store.record_sources_invocation_from_tool_result(
                conn=store.connection,
                is_pg=False,
                tool_name="verify_word",
                arguments={"word": "книга"},
                result_text="книга | VESUM: valid",
                tool_version=TOOL_VERSION,
                request_id=claim["request_id"],
                row_content_sha256=ROW_SHA,
                claimed_lookup_ids=["vesum:12345"],
            )
            is None
        )
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchone()
        assert int(rows["n"]) == 0


def test_sources_invocation_is_idempotent_on_a_canonical_retry(tmp_path: Path) -> None:
    first = _record_invocation(tmp_path)
    assert first is not None
    with ArtifactStore(root=tmp_path) as store, store._transaction() as conn:
        v4_store._persist_sources_invocation(first, conn=conn, is_pg=store.authority.value == "pg", commit=False)
        v4_store._persist_sources_invocation(first, conn=conn, is_pg=store.authority.value == "pg", commit=False)
    with ArtifactStore(root=tmp_path) as store:
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchone()
        assert int(rows["n"]) == 1
        assert store.resolve_v4_sources_invocation(invocation_id=first["invocation_id"]) == first


def test_sources_invocation_conflicting_duplicate_leaves_prior_evidence_unchanged(tmp_path: Path) -> None:
    original = _record_invocation(tmp_path)
    assert original is not None
    with ArtifactStore(root=tmp_path) as store:
        with store._transaction() as conn:
            with pytest.raises(v4_store.SourcesInvocationConflictError, match="different sources invocation"):
                v4_store._persist_sources_invocation({**original, "success": False}, conn=conn, is_pg=store.authority.value == "pg", commit=False)
        assert store.resolve_v4_sources_invocation(invocation_id=original["invocation_id"]) == original


def test_sources_invocation_resolves_none_for_an_unknown_invocation_id(tmp_path: Path) -> None:
    with ArtifactStore(root=tmp_path) as store:
        assert store.resolve_v4_sources_invocation(invocation_id="nope") is None


def test_verification_tool_ids_join_attempt_not_request() -> None:
    import inspect

    params = inspect.signature(v4_store.resolve_sources_invocation_tool_ids).parameters
    assert "attempt_id" in params
    assert "request_id" not in params


def test_compute_invocation_id_is_deterministic_and_content_addressed() -> None:
    kwargs = dict(
        tool_id="mcp__sources__verify_word",
        tool_version="v1",
        attempt_id="a1",
        ordinal=1,
        identifier="vesum:x",
        structured_result_sha256="b" * 64,
        lookup_ids=["l1", "l2"],
    )
    first = v4_store.compute_invocation_id(**kwargs)
    second = v4_store.compute_invocation_id(**kwargs)
    assert first == second
    assert v4_store.compute_invocation_id(**{**kwargs, "structured_result_sha256": "c" * 64}) != first


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
    record = _record_invocation(
        tmp_path,
        typed_outcome={"tool": "verify_word", "disposition": "not_found", "success": False, "evidence_identifiers": [], "result": {}},
    )
    assert record is not None
    assert record["success"] is False
    _patch_sources(monkeypatch, tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access for a failed invocation")))
    with pytest.raises(sources_authority.SourcesAuthorityError, match="not recorded as successful"):
        sources_authority.issue_verifier_attestation(invocation_id=record["invocation_id"])


def test_issue_verifier_attestation_refuses_without_a_terminal_author_observation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    record = _record_invocation(tmp_path)
    assert record is not None
    _patch_sources(monkeypatch, tmp_path, key_loader=lambda role: (_ for _ in ()).throw(AssertionError("no key access without a terminal author join")))
    with pytest.raises(sources_authority.SourcesAuthorityError, match="no terminal author execution"):
        sources_authority.issue_verifier_attestation(invocation_id=record["invocation_id"])


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
    (tmp_path / "fleet_execution.key").chmod(0o600)
    (tmp_path / "fleet_execution.key_id").chmod(0o600)
    with pytest.raises(trust.TrustAuthorityError, match="32 raw bytes"):
        trust.load_production_signing_key("fleet_execution")


def test_load_production_signing_key_succeeds_once_provisioned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "HRAMATKA_SIGNING_KEY_ROOT", tmp_path)
    priv, _pub = trust.generate_test_keypair()
    (tmp_path / "fleet_execution.key").write_text(priv, encoding="utf-8")
    (tmp_path / "fleet_execution.key_id").write_text("prod-key-1", encoding="utf-8")
    (tmp_path / "fleet_execution.key").chmod(0o600)
    (tmp_path / "fleet_execution.key_id").chmod(0o600)
    got_priv, got_key_id = trust.load_production_signing_key("fleet_execution")
    assert got_priv == priv
    assert got_key_id == "prod-key-1"


# --- production trust-policy digest pinning / rotation / revocation --------


def test_load_production_trust_policy_returns_the_checked_in_empty_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "load_production_trust_policy", _REAL_LOAD_PRODUCTION_TRUST_POLICY)
    policy, digest = trust.load_production_trust_policy()
    assert policy == trust.empty_trust_policy()
    assert digest == trust.trust_policy_sha256(policy)


def test_load_production_trust_policy_refuses_a_one_byte_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "load_production_trust_policy", _REAL_LOAD_PRODUCTION_TRUST_POLICY)
    drifted = trust.DEFAULT_TRUST_POLICY_PATH.read_bytes() + b" "  # one extra byte, still valid JSON whitespace
    drifted_path = tmp_path / "drifted.json"
    drifted_path.write_bytes(drifted)
    monkeypatch.setattr(trust, "DEFAULT_TRUST_POLICY_PATH", drifted_path)
    with pytest.raises(trust.TrustAuthorityError, match="not in the code-reviewed active allowlist"):
        trust.load_production_trust_policy()


def test_load_production_trust_policy_refuses_a_revoked_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(trust, "load_production_trust_policy", _REAL_LOAD_PRODUCTION_TRUST_POLICY)
    monkeypatch.setattr(trust, "PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST", frozenset())
    with pytest.raises(trust.TrustAuthorityError, match="not in the code-reviewed active allowlist"):
        trust.load_production_trust_policy()


def test_load_production_trust_policy_takes_no_arguments() -> None:
    import inspect

    assert list(inspect.signature(_REAL_LOAD_PRODUCTION_TRUST_POLICY).parameters) == []


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
