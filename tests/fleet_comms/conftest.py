"""Keep Fleet Comms Postgres tests in a private database per xdist worker."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

_PG_DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"


@pytest.fixture(scope="session")
def fleet_comms_pg_dsn(worker_id: str) -> Iterator[str]:
    """One disposable database for every PG test in this worker process.

    The V4 migration contains explicit public-schema references, so changing
    search_path alone cannot isolate all of its DDL.
    """
    base_dsn = os.environ[_PG_DSN_ENV].strip()
    database_name = f"fleet_test_{worker_id}_{uuid.uuid4().hex}"
    database = sql.Identifier(database_name)
    scoped_dsn = make_conninfo(base_dsn, dbname=database_name)
    with psycopg.connect(base_dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(database))
        try:
            yield scoped_dsn
        finally:
            conn.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(database))


@pytest.fixture(autouse=True)
def isolate_fleet_comms_pg(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Route marked PG cases, including direct psycopg connections, to the database."""
    if request.node.get_closest_marker("postgres") and os.environ.get(_PG_DSN_ENV, "").strip():
        monkeypatch.setenv(_PG_DSN_ENV, request.getfixturevalue("fleet_comms_pg_dsn"))
