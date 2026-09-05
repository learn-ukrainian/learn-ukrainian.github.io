"""Public package interface consumed by the existing protected private API.

Only authorize/execute are route methods. The trusted private startup adapter
owns authentication, the scoped PG connection and unit qualification. Capture,
parsing, artifact insertion and terminalization stay in this parent process.
"""

from __future__ import annotations

import os
import stat

from learn_ukrainian_v4_runtime import child_runtime
from learn_ukrainian_v4_runtime import v4_canonical_authority_store as authority
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.execution_identity import VerifiedReleaseProvider, execution_identity
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
    def __init__(self, *, store: OperationStore, verifier: ActionsVerifier, release_provider: VerifiedReleaseProvider):
        self._store = store
        self._verifier = verifier
        self._release_provider = release_provider

    def authorize(self, raw_body: bytes, *, oidc_token: str, github_bearer: str) -> dict | None:
        parse_request(raw_body, execution=False)
        principal = self._verifier.authenticate(oidc_token=oidc_token, github_bearer=github_bearer)
        principal.ownership()
        require_execution_enabled()
        require_readiness()
        execution_identity(self._release_provider)
        _, policy_digest = trust.load_production_trust_policy()
        identifier = self._store.authorize(principal=principal, raw=raw_body, policy_digest=policy_digest)
        return {"authorization_id": identifier} if identifier else None

    def execute(self, raw_body: bytes, *, oidc_token: str, github_bearer: str) -> dict:
        body = parse_request(raw_body, execution=True)
        principal = self._verifier.authenticate(oidc_token=oidc_token, github_bearer=github_bearer)
        principal.ownership()
        require_execution_enabled()
        require_readiness()
        execution_identity(self._release_provider)
        _, policy_digest = trust.load_production_trust_policy()
        claim = self._store.claim(
            principal=principal, raw=raw_body, authorization_id=body["authorization_id"], policy_digest=policy_digest
        )
        return self._execute_owned_claim(claim)

    def _execute_owned_claim(self, claim: dict) -> dict:
        """Internal parent path; the route supplies only its atomic store claim."""
        with self._store.finalization(claim) as (_, fresh):
            if not fresh:
                raise OperationRefused("execution_expired")
        release = execution_identity(self._release_provider)
        try:
            capture = child_runtime.run_child(
                claim, provider_credential=_provider_credential(claim["binding"]["expected_harness"])
            )
            if capture.request_id != claim["request_id"] or capture.attempt_id != claim["attempt_id"]:
                raise OperationRefused("foreign_child_capture")
            parsed = child_runtime.parse_child(capture, claim["binding"])
            from learn_ukrainian_v4_runtime.v4_execution_origin import blindness_from_prompt_profile

            saw_source, saw_heldout, saw_eligible = blindness_from_prompt_profile(
                prompt_profile=claim["binding"]["prompt_profile"],
                transported_digest=capture.prompt_sha256,
                authorized_digest=claim["binding"]["prompt_sha256"],
            )
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
                if execution_identity(self._release_provider) != release:
                    raise OperationRefused("execution_release_changed")
                record = {
                    "runtime_identity": release,
                    "trust_policy_sha256": claim["trust_policy_sha256"],
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
                    "saw_source_text": saw_source,
                    "saw_heldout": saw_heldout,
                    "saw_eligible_unit_ids": saw_eligible,
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


def _provider_credential(harness: str) -> child_runtime.ProviderCredential:
    # Qualify the fixed adapter BEFORE reading its sole systemd credential.
    # Neither request fields nor the payload can select the file or the mode.
    mode = child_runtime.credential_mode(child_runtime.load_profile(), harness)
    fd = None
    try:
        fd = os.open(provider_credential_path(harness), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        before = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid not in (0, os.geteuid())
            or before.st_mode & 0o077
            or not 0 < before.st_size <= child_runtime.MAX_CREDENTIAL_BYTES
        ):
            raise OperationRefused("provider_credential_file")
        chunks = bytearray()
        while len(chunks) <= child_runtime.MAX_CREDENTIAL_BYTES:
            chunk = os.read(fd, child_runtime.MAX_CREDENTIAL_BYTES + 1 - len(chunks))
            if not chunk:
                break
            chunks.extend(chunk)
        after = os.fstat(fd)
        if before.st_size != len(chunks) or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise OperationRefused("provider_credential_file_changed")
        return child_runtime.parse_provider_credential(bytes(chunks), harness=harness, mode=mode)
    except OSError:
        raise OperationRefused("provider_credential_file") from None
    finally:
        if fd is not None:
            os.close(fd)


def provider_credential_path(harness: str):
    from pathlib import Path

    if harness not in ("claude", "codex"):
        raise OperationRefused("adapter_unqualified")
    return Path("/run/credentials/hramatka-api.service") / ("v4-provider-" + harness)
