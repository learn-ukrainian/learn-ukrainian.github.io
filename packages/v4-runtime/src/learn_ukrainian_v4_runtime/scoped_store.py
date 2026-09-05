"""Fixed systemd-scoped PostgreSQL custody for opaque V4 receipt issuers."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from learn_ukrainian_v4_runtime import credential_custody as custody
from learn_ukrainian_v4_runtime import v4_canonical_authority_store as records
from learn_ukrainian_v4_runtime.operation_auth import OperationRefused


class Authority(StrEnum):
    PG = "pg"


def control_credential_path() -> Path:
    return Path("/run/credentials/hramatka-api.service/v4-control-dsn")


class ScopedAuthorityStore:
    authority = Authority.PG

    def __init__(self, *, write: bool = False):
        # The unit's own systemd credential: owner-private, or root-owned with
        # an access ACL naming only this service uid (kernel ACL semantics,
        # descriptor-bound; see credential_custody).
        try:
            dsn = custody.read_credential(control_credential_path()).decode("utf-8").strip()
        except (OSError, custody.CredentialCustodyError) as exc:
            raise OperationRefused("scoped_control_credential_required") from exc
        except UnicodeDecodeError:
            raise OperationRefused("scoped_control_credential_required") from None
        self.connection = psycopg.connect(dsn, autocommit=True, row_factory=dict_row)
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
