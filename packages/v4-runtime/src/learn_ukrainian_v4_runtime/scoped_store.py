"""Fixed systemd-scoped PostgreSQL custody for opaque V4 receipt issuers."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from learn_ukrainian_v4_runtime import v4_canonical_authority_store as records
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused


class Authority(StrEnum):
    PG = "pg"


def control_credential_path() -> Path:
    return Path("/run/credentials/hramatka-api.service/v4-control-dsn")


class ScopedAuthorityStore:
    authority = Authority.PG

    def __init__(self, *, write: bool = False):
        path = control_credential_path()
        if not path.is_file() or path.is_symlink() or path.stat().st_mode & 0o077:
            raise OperationRefused("scoped_control_credential_required")
        self.connection = psycopg.connect(path.read_text().strip(), autocommit=True, row_factory=dict_row)
        principal = self.connection.execute("SELECT current_user AS principal").fetchone()["principal"]
        if principal != "hramatka_v4_control_writer":
            self.connection.close()
            raise OperationRefused("control_role_required")
        if not write:
            self.connection.execute("SET default_transaction_read_only=on")

    def close(self):
        self.connection.close()

    def resolve_v4_execution_observation(self, *, task_id, run_id, role):
        return records.resolve_execution_observation(
            task_id=task_id, run_id=run_id, role=role, conn=self.connection, is_pg=True
        )

    def resolve_v4_sources_invocation(self, *, invocation_id):
        return records.resolve_sources_invocation(invocation_id=invocation_id, conn=self.connection, is_pg=True)

    def persist_v4_authorship_receipt(self, receipt, *, task_id, run_id):
        return records.persist_authorship_receipt(
            receipt, task_id=task_id, run_id=run_id, conn=self.connection, is_pg=True
        )
