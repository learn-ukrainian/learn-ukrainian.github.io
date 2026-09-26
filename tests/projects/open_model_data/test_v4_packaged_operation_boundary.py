"""Source-free tests of the approved packaged operation contract."""

from __future__ import annotations

import psycopg
import pytest
from learn_ukrainian_v4_runtime.operation_auth import (
    AUTHORIZE_SCHEMA,
    EXECUTE_SCHEMA,
    OperationRefused,
    canonical_bytes,
    parse_request,
)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{}",
        b"null",
        b"[]",
        b'{"schema":"hramatka-v4-operation-authorize.v1","schema":"hramatka-v4-operation-authorize.v1"}',
        b'{"schema": "hramatka-v4-operation-authorize.v1"}',
        b'{"schema":"hramatka-v4-operation-authorize.v1"}\n',
        b'{"schema":"hramatka-v4-operation-authorize.v1"}{}',
        b" " * 1025,
        canonical_bytes({"schema": AUTHORIZE_SCHEMA, "target": "foreign"}),
        canonical_bytes({"schema": AUTHORIZE_SCHEMA, "policy": "foreign"}),
        canonical_bytes({"schema": AUTHORIZE_SCHEMA, "dsn": "foreign"}),
        canonical_bytes({"schema": AUTHORIZE_SCHEMA, "model": "foreign"}),
        canonical_bytes({"schema": AUTHORIZE_SCHEMA, "seat": "foreign"}),
    ],
)
def test_authorization_rejects_noncanonical_and_caller_authority(raw):
    with pytest.raises(OperationRefused):
        parse_request(raw, execution=False)


def test_exact_bodies():
    assert parse_request(canonical_bytes({"schema": AUTHORIZE_SCHEMA}), execution=False) == {"schema": AUTHORIZE_SCHEMA}
    value = {"schema": EXECUTE_SCHEMA, "authorization_id": "A" * 43}
    assert parse_request(canonical_bytes(value), execution=True) == value


def test_pg_scoped_role_acl(pg_cluster):
    conn = pg_cluster
    rows = conn.execute("""SELECT
        has_table_privilege('hramatka_v4_control_writer','v4_operation_authorizations','INSERT') AS control_write,
        has_table_privilege('hramatka_v4_control_writer','v4_sources_invocations','INSERT') AS control_sources,
        has_table_privilege('hramatka_v4_sources_writer','v4_sources_invocations','INSERT') AS sources_write,
        has_table_privilege('hramatka_v4_sources_writer','v4_execution_observations','INSERT') AS sources_observation,
        has_function_privilege('hramatka_v4_sources_writer','hramatka_v4_record_sources_invocation_v1(text,text,text,text)','EXECUTE') AS sources_execute,
        has_function_privilege('hramatka_v4_control_writer','hramatka_v4_record_sources_invocation_v1(text,text,text,text)','EXECUTE') AS control_execute
    """).fetchone()
    assert rows == dict(
        control_write=True,
        control_sources=False,
        sources_write=False,
        sources_observation=False,
        sources_execute=True,
        control_execute=False,
    )
    conn.execute("SET ROLE hramatka_v4_sources_writer")
    try:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "INSERT INTO v4_execution_observations VALUES ('forged','forged','author','forged','{}','now','forged')"
            )
        with pytest.raises(psycopg.errors.RaiseException, match="inactive V4 Sources capability"):
            conn.execute("SELECT hramatka_v4_record_sources_invocation_v1(%s,NULL,NULL,NULL)", ("a" * 64,))
    finally:
        conn.execute("RESET ROLE")
