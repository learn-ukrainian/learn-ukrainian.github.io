"""Operation ownership on the canonical Fleet PostgreSQL connection.

Connections are supplied by the protected API's scoped credential integration.
No generic Fleet DSN resolution or SQLite fallback exists on this path.
"""

from __future__ import annotations

import json
import secrets
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from learn_ukrainian_v4_runtime.operation_auth import (
    EXECUTE_SCHEMA,
    ActionsPrincipal,
    OperationRefused,
    canonical_bytes,
    digest,
)


class OperationStore:
    def __init__(self, connection: Any):
        self.connection = connection
        row = connection.execute("SELECT current_user AS principal").fetchone()
        if row["principal"] != "hramatka_v4_control_writer":
            raise OperationRefused("control_role_required")

    @contextmanager
    def transaction(self):
        with self.connection.transaction():
            yield self.connection

    @staticmethod
    def _consume_jti(conn, principal: ActionsPrincipal) -> str:
        jti = digest(principal.jti.encode())
        row = conn.execute(
            "INSERT INTO v4_operation_jtis(jti_digest) VALUES (%s) ON CONFLICT DO NOTHING RETURNING jti_digest",
            (jti,),
        ).fetchone()
        if row is None:
            raise OperationRefused("consumed_jti")
        return jti

    def authorize(self, *, principal: ActionsPrincipal, raw: bytes, policy_digest: str) -> str | None:
        owner = canonical_bytes(principal.ownership()).decode()
        with self.transaction() as conn:
            jti = self._consume_jti(conn, principal)
            row = conn.execute("""
                SELECT r.request_id, r.expires_at, b.record_json, b.record_sha256, b.semantic_input_json
                FROM requests r JOIN v4_execution_dispatch_bindings b USING (request_id)
                WHERE r.state = 'queued' AND r.expires_at::timestamptz > clock_timestamp()
                  AND b.semantic_input_json IS NOT NULL
                  AND NOT EXISTS (SELECT FROM v4_operation_authorizations o WHERE o.request_id = r.request_id)
                ORDER BY r.created_at, r.request_id FOR UPDATE OF r, b SKIP LOCKED LIMIT 1
            """).fetchone()
            if row is None:
                return None
            binding = json.loads(row["record_json"])
            if digest(canonical_bytes(binding)) != row["record_sha256"]:
                raise OperationRefused("binding_digest")
            from learn_ukrainian_v4_runtime.semantic_inputs import prompt_from_snapshot

            prompt = prompt_from_snapshot(binding, json.loads(row["semantic_input_json"]))
            if digest(prompt.encode()) != binding["prompt_sha256"]:
                raise OperationRefused("semantic_input_digest")
            opaque_id = secrets.token_urlsafe(32)
            execution_body = canonical_bytes({"authorization_id": opaque_id, "schema": EXECUTE_SCHEMA})
            conn.execute(
                """
                INSERT INTO v4_operation_authorizations (
                  authorization_digest,request_id,operation,target,role,seat,harness,timeout_seconds,
                  principal_json,authz_policy_sha256,trust_policy_sha256,binding_sha256,
                  authorization_body_sha256,execution_body_sha256,authorization_jti_digest,state,expires_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1800,%s,%s,%s,%s,%s,%s,%s,'armed',LEAST(clock_timestamp()+interval '5 minutes',%s::timestamptz))
            """,
                (
                    digest(opaque_id.encode()),
                    row["request_id"],
                    binding["role"],
                    binding["slot_id"] or binding["authorship_receipt_id"],
                    binding["role"],
                    binding["expected_seat_or_model"],
                    binding["expected_harness"],
                    owner,
                    principal.authz_policy_sha256,
                    policy_digest,
                    row["record_sha256"],
                    digest(raw),
                    digest(execution_body),
                    jti,
                    row["expires_at"],
                ),
            )
            conn.execute(
                """UPDATE requests r SET expires_at = o.expires_at::text
                FROM v4_operation_authorizations o WHERE r.request_id = %s AND o.request_id = r.request_id""",
                (row["request_id"],),
            )
            return opaque_id

    def claim(self, *, principal: ActionsPrincipal, raw: bytes, authorization_id: str, policy_digest: str) -> dict:
        owner = canonical_bytes(principal.ownership()).decode()
        with self.transaction() as conn:
            auth = conn.execute(
                """SELECT *, expires_at > clock_timestamp() AS fresh
                FROM v4_operation_authorizations WHERE authorization_digest = %s FOR UPDATE""",
                (digest(authorization_id.encode()),),
            ).fetchone()
            if auth is None or auth["state"] != "armed" or not auth["fresh"]:
                raise OperationRefused("authorization_inactive")
            if (
                auth["principal_json"] != owner
                or auth["authz_policy_sha256"] != principal.authz_policy_sha256
                or auth["trust_policy_sha256"] != policy_digest
                or auth["execution_body_sha256"] != digest(raw)
            ):
                raise OperationRefused("authorization_ownership")
            request = conn.execute(
                """SELECT *, expires_at::timestamptz > clock_timestamp() AS fresh
                FROM requests WHERE request_id = %s FOR UPDATE""",
                (auth["request_id"],),
            ).fetchone()
            binding_row = conn.execute(
                "SELECT * FROM v4_execution_dispatch_bindings WHERE request_id = %s FOR UPDATE", (auth["request_id"],)
            ).fetchone()
            if request is None or request["state"] != "queued" or not request["fresh"] or binding_row is None:
                raise OperationRefused("request_inactive")
            binding = json.loads(binding_row["record_json"])
            if (
                digest(canonical_bytes(binding)) != auth["binding_sha256"]
                or binding_row["record_sha256"] != auth["binding_sha256"]
                or binding["request_id"] != request["request_id"]
                or binding["role"] != auth["operation"]
                or binding["role"] != auth["role"]
                or binding["expected_seat_or_model"] != auth["seat"]
                or binding["expected_harness"] != auth["harness"]
                or request["resolved_recipient"] != auth["harness"]
                or (binding["slot_id"] or binding["authorship_receipt_id"]) != auth["target"]
            ):
                raise OperationRefused("binding_ownership")
            if datetime.fromisoformat(request["expires_at"]) != auth["expires_at"]:
                raise OperationRefused("request_deadline_ownership")
            now = conn.execute("SELECT clock_timestamp() AS now").fetchone()["now"]
            if auth["expires_at"] <= now or datetime.fromisoformat(request["expires_at"]) <= now:
                raise OperationRefused("authorization_inactive")
            jti = self._consume_jti(conn, principal)
            from learn_ukrainian_v4_runtime.semantic_inputs import prompt_from_snapshot

            prompt = prompt_from_snapshot(binding, json.loads(binding_row["semantic_input_json"]))
            if digest(prompt.encode()) != binding["prompt_sha256"]:
                raise OperationRefused("semantic_input_digest")
            deadline = conn.execute(
                """UPDATE v4_operation_authorizations SET state='claimed',
                execution_jti_digest=%s,claimed_at=clock_timestamp(),deadline_at=clock_timestamp()+interval '1800 seconds'
                WHERE authorization_digest=%s RETURNING deadline_at""",
                (jti, auth["authorization_digest"]),
            ).fetchone()["deadline_at"]
            token = secrets.token_urlsafe(32)
            attempt_id = "v4attempt_" + secrets.token_hex(16)
            conn.execute(
                """INSERT INTO v4_execution_attempts(attempt_id,request_id,task_id,run_id,role,state,
                capability_digest,binding_sha256,started_at,deadline_at)
                VALUES(%s,%s,%s,%s,%s,'running',%s,%s,clock_timestamp()::text,%s)""",
                (
                    attempt_id,
                    request["request_id"],
                    binding["task_id"],
                    binding["run_id"],
                    binding["role"],
                    digest(token.encode()),
                    auth["binding_sha256"],
                    deadline,
                ),
            )
            conn.execute(
                "UPDATE requests SET state='running',expires_at=%s,updated_at=clock_timestamp()::text WHERE request_id=%s",
                (str(deadline), request["request_id"]),
            )
            return {
                "authorization_digest": auth["authorization_digest"],
                "request_id": request["request_id"],
                "attempt_id": attempt_id,
                "capability_token": token,
                "binding": binding,
                "prompt": prompt,
                "deadline_at": deadline,
                "trust_policy_sha256": policy_digest,
            }

    @contextmanager
    def finalization(self, claim: dict):
        """Lock and validate ownership before the parent writes any artifacts.

        This takes an internal claim; it accepts no process or parser facts.
        The service parent owns capture, parsing and the complete transaction.
        """
        with self.transaction() as conn:
            auth = conn.execute(
                "SELECT * FROM v4_operation_authorizations WHERE authorization_digest=%s FOR UPDATE",
                (claim["authorization_digest"],),
            ).fetchone()
            attempt = conn.execute(
                """SELECT *, deadline_at > clock_timestamp() AS fresh
                FROM v4_execution_attempts WHERE attempt_id=%s FOR UPDATE""",
                (claim["attempt_id"],),
            ).fetchone()
            req = conn.execute(
                "SELECT state, expires_at FROM requests WHERE request_id=%s FOR UPDATE", (claim["request_id"],)
            ).fetchone()
            binding = conn.execute(
                "SELECT * FROM v4_execution_dispatch_bindings WHERE request_id=%s FOR UPDATE", (claim["request_id"],)
            ).fetchone()
            if (
                auth is None
                or attempt is None
                or binding is None
                or req is None
                or auth["request_id"] != claim["request_id"]
                or attempt["request_id"] != claim["request_id"]
                or attempt["state"] != "running"
                or auth["state"] != "claimed"
                or req["state"] != "running"
                or attempt["binding_sha256"] != auth["binding_sha256"]
                or binding["record_sha256"] != auth["binding_sha256"]
                or digest(canonical_bytes(claim["binding"])) != auth["binding_sha256"]
                or attempt["task_id"] != claim["binding"]["task_id"]
                or attempt["run_id"] != claim["binding"]["run_id"]
                or attempt["role"] != claim["binding"]["role"]
                or attempt["deadline_at"] != auth["deadline_at"]
                or datetime.fromisoformat(req["expires_at"]) != auth["deadline_at"]
                or claim["deadline_at"] != auth["deadline_at"]
                or claim["trust_policy_sha256"] != auth["trust_policy_sha256"]
                or digest(claim["capability_token"].encode()) != attempt["capability_digest"]
            ):
                raise OperationRefused("finalization_ownership")
            # FOR UPDATE may wait after its target-list expression was evaluated.
            # Read the database clock again after every ownership lock is held.
            now = conn.execute("SELECT clock_timestamp() AS now").fetchone()["now"]
            yield conn, attempt["deadline_at"] > now

    @staticmethod
    def finish(conn, claim: dict, *, success: bool):
        conn.execute(
            "UPDATE v4_execution_attempts SET state='terminal',terminal_at=clock_timestamp()::text WHERE attempt_id=%s",
            (claim["attempt_id"],),
        )
        conn.execute(
            "UPDATE v4_operation_authorizations SET state='terminal',terminal_at=clock_timestamp() WHERE authorization_digest=%s",
            (claim["authorization_digest"],),
        )
        conn.execute(
            "UPDATE requests SET state=%s,completion_state=%s,updated_at=clock_timestamp()::text WHERE request_id=%s",
            ("complete" if success else "failed", "complete" if success else "failed", claim["request_id"]),
        )
