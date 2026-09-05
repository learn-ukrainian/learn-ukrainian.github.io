"""Real PG operation ownership and interleavings below the private auth adapter.

The principal represents that adapter's output for unit-level store tests; these
are not OIDC/API qualification. Requests/bindings are created through the real
Fleet preparation API. No observation or Sources invocation is hand-inserted.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import psycopg
import pytest
from learn_ukrainian_v4_runtime import semantic_inputs
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import ActionsPrincipal, OperationRefused, canonical_bytes, digest
from learn_ukrainian_v4_runtime.operation_store import OperationStore
from psycopg.rows import dict_row

from scripts.fleet_comms.request_executor import RequestExecutor

pytest_plugins = ("test_v4_packaged_operation_boundary",)


def principal(jti):
    return ActionsPrincipal(
        repository_id=1,
        workflow_ref="fixture/workflow@refs/heads/main",
        ref="refs/heads/main",
        subject="repo:fixture:ref:refs/heads/main",
        workflow_sha256="a" * 64,
        run_id=1,
        run_attempt=1,
        check_run_id=1,
        runner_id=1,
        runner_group_id=1,
        runner_label="fixture-runner",
        authz_policy_sha256="b" * 64,
        jti=jti,
    )


def role_connection(pg, role):
    connection = psycopg.connect(pg.info.dsn, autocommit=True, row_factory=dict_row)
    assert role in ("hramatka_v4_control_writer", "hramatka_v4_sources_writer")
    connection.execute("SET ROLE " + role)
    return connection


@pytest.fixture
def prepared(pg_cluster, monkeypatch, tmp_path):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", pg_cluster.info.dsn)
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    with RequestExecutor(root=tmp_path) as executor:
        request = executor.create_request(recipient="claude", body="source-free operation fixture")
        binding = executor.authorize_author_execution(
            request_id=request.request_id, slot_id="v4p-standard-correct-001", expected_seat="claude-sonnet-5"
        )
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        semantic_inputs.freeze_semantic_input(
            conn,
            request_id=request.request_id,
            snapshot={
                "constraints": {
                    "task_kind": "original_row",
                    "cefr_level": "A1",
                    "required_fields": ["row_text", "answer"],
                    "allowed_evidence_tools": ["verify_word"],
                }
            },
        )
        store = OperationStore(conn)
        policy = trust.load_production_trust_policy()[1]
        auth_principal = principal("authorize-" + request.request_id)
        raw = canonical_bytes({"schema": "hramatka-v4-operation-authorize.v1"})
        identifier = store.authorize(principal=auth_principal, raw=raw, policy_digest=policy)
        assert identifier
    execution = canonical_bytes({"authorization_id": identifier, "schema": "hramatka-v4-operation-execute.v1"})
    return {
        "request_id": request.request_id,
        "binding": binding,
        "identifier": identifier,
        "raw": execution,
        "policy": policy,
        "principal": replace(auth_principal, jti="execute-" + request.request_id),
    }


def claim(conn, prepared, **overrides):
    fields = dict(
        principal=prepared["principal"],
        raw=prepared["raw"],
        authorization_id=prepared["identifier"],
        policy_digest=prepared["policy"],
    )
    fields.update(overrides)
    return OperationStore(conn).claim(**fields)


def test_actual_claim_binds_semantic_input_and_deadlines(pg_cluster, prepared):
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        value = claim(conn, prepared)
        assert '"required_fields":["row_text","answer"]' in value["prompt"]
        assert digest(value["prompt"].encode()) == value["binding"]["prompt_sha256"]
        row = conn.execute(
            "SELECT deadline_at > clock_timestamp() AS fresh FROM v4_execution_attempts WHERE attempt_id=%s",
            (value["attempt_id"],),
        ).fetchone()
        assert row["fresh"]
        with OperationStore(conn).finalization(value) as (tx, fresh):
            assert fresh
            OperationStore.finish(tx, value, success=False)


@pytest.mark.parametrize(
    "field",
    [
        "repository_id",
        "run_id",
        "run_attempt",
        "check_run_id",
        "runner_id",
        "runner_group_id",
        "workflow_ref",
        "ref",
        "subject",
        "authz_policy_sha256",
    ],
)
def test_foreign_authenticated_ownership_refuses(pg_cluster, prepared, field):
    original = getattr(prepared["principal"], field)
    foreign = replace(
        prepared["principal"], **{field: original + 1 if isinstance(original, int) else original + "foreign"}
    )
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        with pytest.raises(OperationRefused):
            claim(conn, prepared, principal=foreign)
        assert (
            conn.execute(
                "SELECT count(*) AS n FROM v4_execution_attempts WHERE request_id=%s", (prepared["request_id"],)
            ).fetchone()["n"]
            == 0
        )


def test_real_concurrent_double_claim_has_one_winner(pg_cluster, prepared):
    barrier = threading.Barrier(2)

    def compete(index):
        with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
            barrier.wait(timeout=5)
            try:
                claim(
                    conn,
                    prepared,
                    principal=replace(prepared["principal"], jti="race-" + str(index) + prepared["request_id"]),
                )
                return "claimed"
            except OperationRefused:
                return "refused"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, range(2)))
    assert sorted(results) == ["claimed", "refused"]


def test_expired_authorization_refuses(pg_cluster, prepared):
    pg_cluster.execute(
        "UPDATE v4_operation_authorizations SET expires_at=clock_timestamp()-interval '1 second' WHERE request_id=%s",
        (prepared["request_id"],),
    )
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        with pytest.raises(OperationRefused, match="inactive"):
            claim(conn, prepared)


def test_sources_waits_for_terminalization_and_then_refuses(pg_cluster, prepared):
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        value = claim(conn, prepared)
        started = threading.Event()

        def record():
            with role_connection(pg_cluster, "hramatka_v4_sources_writer") as sources:
                started.set()
                try:
                    sources.execute(
                        "SELECT hramatka_v4_record_sources_invocation_v1(%s,NULL,NULL,NULL)",
                        (digest(value["capability_token"].encode()),),
                    )
                    return "accepted"
                except psycopg.errors.RaiseException:
                    return "refused"

        with ThreadPoolExecutor(max_workers=1) as pool:
            with OperationStore(conn).finalization(value) as (tx, fresh):
                assert fresh
                future = pool.submit(record)
                assert started.wait(5)
                OperationStore.finish(tx, value, success=False)
            assert future.result(timeout=5) == "refused"


def test_authorization_jti_cannot_be_reused_for_execution(pg_cluster, prepared):
    replay = replace(prepared["principal"], jti="authorize-" + prepared["request_id"])
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        with pytest.raises(OperationRefused, match="consumed_jti"):
            claim(conn, prepared, principal=replay)


def test_revoked_authorization_refuses(pg_cluster, prepared):
    pg_cluster.execute(
        "UPDATE v4_operation_authorizations SET state='revoked',revoked_at=clock_timestamp() WHERE request_id=%s",
        (prepared["request_id"],),
    )
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        with pytest.raises(OperationRefused, match="inactive"):
            claim(conn, prepared)


def test_expired_sources_capability_refuses_before_recording(pg_cluster, prepared):
    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        value = claim(conn, prepared)
    pg_cluster.execute(
        "UPDATE v4_execution_attempts SET deadline_at=clock_timestamp()-interval '1 second' WHERE attempt_id=%s",
        (value["attempt_id"],),
    )
    with role_connection(pg_cluster, "hramatka_v4_sources_writer") as conn:
        with pytest.raises(psycopg.errors.RaiseException, match="inactive"):
            conn.execute(
                "SELECT hramatka_v4_record_sources_invocation_v1(%s,NULL,NULL,NULL)",
                (digest(value["capability_token"].encode()),),
            )
    assert (
        pg_cluster.execute(
            "SELECT count(*) AS n FROM v4_sources_invocations WHERE attempt_id=%s", (value["attempt_id"],)
        ).fetchone()["n"]
        == 0
    )


def test_sources_recording_commits_before_waiting_finalization(pg_cluster, prepared):
    import asyncio
    from unittest.mock import patch

    from learn_ukrainian_v4_runtime import sources_handlers
    from test_v4_preserved_provenance import LexicalResources

    with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
        value = claim(conn, prepared)
    with patch.object(sources_handlers, "_backend", LexicalResources()):
        _, outcome = asyncio.run(sources_handlers.handle_verify_word({"word": "fixture-one"}))
    waiting = threading.Event()

    def finalize():
        with role_connection(pg_cluster, "hramatka_v4_control_writer") as control:
            waiting.set()
            with OperationStore(control).finalization(value) as (tx, fresh):
                assert fresh
                row = tx.execute(
                    "SELECT count(*) AS n FROM v4_sources_invocations WHERE attempt_id=%s", (value["attempt_id"],)
                ).fetchone()
                OperationStore.finish(tx, value, success=False)
                return row["n"]

    with ThreadPoolExecutor(max_workers=1) as pool:
        with role_connection(pg_cluster, "hramatka_v4_sources_writer") as sources:
            with sources.transaction():
                sources.execute(
                    "SELECT hramatka_v4_record_sources_invocation_v1(%s,%s,%s,%s)",
                    (
                        digest(value["capability_token"].encode()),
                        "verify_word",
                        "c" * 64,
                        canonical_bytes(outcome).decode(),
                    ),
                )
                future = pool.submit(finalize)
                assert waiting.wait(5)
                assert not future.done()
            assert future.result(timeout=5) == 1
