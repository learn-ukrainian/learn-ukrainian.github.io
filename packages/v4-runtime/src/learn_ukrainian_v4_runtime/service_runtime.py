"""Public package interface consumed by the existing protected private API.

Only authorize/execute are route methods. The trusted private startup adapter
owns authentication, the scoped PG connection and unit qualification. Capture,
parsing, artifact insertion and terminalization stay in this parent process.
"""

from __future__ import annotations

import json

from learn_ukrainian_v4_runtime import child_runtime
from learn_ukrainian_v4_runtime import v4_canonical_authority_store as authority
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import (
    ActionsVerifier,
    OperationRefused,
    canonical_bytes,
    digest,
    parse_request,
)
from learn_ukrainian_v4_runtime.operation_store import OperationStore
from learn_ukrainian_v4_runtime.readiness import require_execution_enabled, require_readiness


class V4ServiceRuntime:
    def __init__(self, *, store: OperationStore, verifier: ActionsVerifier):
        self._store = store
        self._verifier = verifier

    def authorize(self, raw_body: bytes, *, oidc_token: str, github_bearer: str) -> dict | None:
        parse_request(raw_body, execution=False)
        principal = self._verifier.authenticate(oidc_token=oidc_token, github_bearer=github_bearer)
        principal.ownership()
        require_execution_enabled()
        require_readiness()
        _, policy_digest = trust.load_production_trust_policy()
        identifier = self._store.authorize(principal=principal, raw=raw_body, policy_digest=policy_digest)
        return {"authorization_id": identifier} if identifier else None

    def execute(self, raw_body: bytes, *, oidc_token: str, github_bearer: str) -> dict:
        body = parse_request(raw_body, execution=True)
        principal = self._verifier.authenticate(oidc_token=oidc_token, github_bearer=github_bearer)
        principal.ownership()
        require_execution_enabled()
        require_readiness()
        _, policy_digest = trust.load_production_trust_policy()
        claim = self._store.claim(
            principal=principal, raw=raw_body, authorization_id=body["authorization_id"], policy_digest=policy_digest
        )
        try:
            capture = child_runtime.run_child(
                claim, provider_credential=_provider_credential(claim["binding"]["expected_harness"])
            )
            parsed = child_runtime.parse_child(capture, claim["binding"])
            with self._store.finalization(claim) as (conn, fresh):
                if not fresh:
                    self._store.finish(conn, claim, success=False)
                    return {"state": "terminal", "outcome": "expired"}
                # Recheck the fixed policy after execution, before artifact side effects.
                _, current_policy = trust.load_production_trust_policy()
                if current_policy != claim["trust_policy_sha256"]:
                    self._store.finish(conn, claim, success=False)
                    return {"state": "terminal", "outcome": "policy_changed"}
                binding = claim["binding"]
                art_id = "v4capture_" + digest(capture.stdout)
                conn.execute(
                    """INSERT INTO fleet_comms_artifact_blobs(sha256,artifact_id,bytes,mime_type,
                    logical_filename,producer,retention_class,created_at,payload)
                    VALUES(%s,%s,%s,'application/x-ndjson','v4-capture','v4-service','raw-capture',clock_timestamp()::text,%s)
                    ON CONFLICT(sha256) DO NOTHING""",
                    (digest(capture.stdout), art_id, len(capture.stdout), capture.stdout),
                )
                if binding["role"] == "author":
                    row_hash = digest(parsed["row"]["row_text"].encode())
                else:
                    authorship = authority.resolve_authorship_receipt(
                        receipt_id=binding["authorship_receipt_id"], conn=conn, is_pg=True
                    )
                    if authorship is None:
                        raise OperationRefused("authorship_unresolved")
                    row_hash = authorship["row_content_sha256"]
                record = {
                    "task_id": binding["task_id"],
                    "run_id": binding["run_id"],
                    "role": binding["role"],
                    "attempt_id": claim["attempt_id"],
                    "status": "done",
                    "return_code": 0,
                    "seat_or_model": parsed["model"],
                    "requested_model": binding["expected_seat_or_model"],
                    "harness": capture.harness,
                    "executable": capture.harness,
                    "argv_digest": capture.argv_sha256,
                    "session_id": parsed["session_id"],
                    "completion_state": "complete",
                    "terminal_event_observed": True,
                    "process_returncode": 0,
                    "raw_capture_artifact_id": art_id,
                    "raw_capture_sha256": digest(capture.stdout),
                    "stdout_sha256": digest(capture.stdout),
                    "stderr_sha256": digest(capture.stderr),
                    "output_artifact_sha256": digest(b""),
                    "aggregate_artifact_sha256": digest(
                        canonical_bytes(
                            {
                                "stdout_sha256": digest(capture.stdout),
                                "stderr_sha256": digest(capture.stderr),
                                "output_sha256": digest(b""),
                            }
                        )
                    ),
                    "row_content_sha256": row_hash,
                    "prompt_profile": binding["prompt_profile"],
                    "prompt_sha256": capture.prompt_sha256,
                    "packet_sha256": binding["packet_sha256"],
                    "fleet_receipt_sha256": digest(
                        canonical_bytes(
                            {
                                "request_id": claim["request_id"],
                                "attempt_id": claim["attempt_id"],
                                "artifact_sha256": digest(capture.stdout),
                            }
                        )
                    ),
                    "verification_tool_ids": authority.resolve_sources_invocation_tool_ids(
                        attempt_id=claim["attempt_id"], conn=conn, is_pg=True
                    ),
                    "saw_source_text": False,
                    "saw_heldout": False,
                    "saw_eligible_unit_ids": False,
                    "authorship_receipt_sha256": binding["authorship_receipt_sha256"],
                    "rubric_sha256": binding["rubric_sha256"],
                    "verdict": parsed.get("verdict"),
                }
                authority._persist_execution_observation(
                    record, conn=conn, is_pg=True, request_id=claim["request_id"], commit=False
                )
                self._store.finish(conn, claim, success=True)
            return {
                "state": "terminal",
                "task_id": binding["task_id"],
                "run_id": binding["run_id"],
                "role": binding["role"],
            }
        except Exception:
            with self._store.finalization(claim) as (conn, _):
                self._store.finish(conn, claim, success=False)
            raise


def _provider_credential(harness: str) -> str:
    from pathlib import Path

    if harness not in ("claude", "codex"):
        raise OperationRefused("adapter_unqualified")
    payload = json.loads((Path("/run/credentials/hramatka-api.service") / ("v4-provider-" + harness)).read_bytes())
    if set(payload) != {"credential"} or not isinstance(payload["credential"], str) or not payload["credential"]:
        raise OperationRefused("provider_credential_missing")
    return payload["credential"]
