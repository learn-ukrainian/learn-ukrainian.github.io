"""Real protected parent capture/HTTP/PG and opaque issuance, below private auth.

Every operation claim is produced by the canonical store. Source-free resources
replace only the executable/profile, lexical data, credentials and public keys.
This deliberately makes no actual-unit, provider or private JWT integration claim.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace

import _v4_a7_real_slot_fixture as fx
import pytest
from _v4_packaged_runtime_fixture import RuntimeResources, WheelRelease
from learn_ukrainian_v4_runtime import semantic_inputs, service_runtime
from learn_ukrainian_v4_runtime import v4_a7_private_ledger as ledger
from learn_ukrainian_v4_runtime import v4_canonical_authority_store as authority
from learn_ukrainian_v4_runtime import v4_fleet_execution_authority as fleet
from learn_ukrainian_v4_runtime import v4_trust_authority as trust
from learn_ukrainian_v4_runtime.operation_auth import canonical_bytes, digest
from learn_ukrainian_v4_runtime.operation_store import OperationStore
from test_v4_operation_lifecycle import principal, role_connection

from scripts.fleet_comms.request_executor import RequestExecutor

pytest_plugins = ("test_v4_operation_lifecycle",)


@pytest.fixture(scope="module")
def built_wheel(tmp_path_factory):
    output = tmp_path_factory.mktemp("owned-wheel")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "packages/v4-runtime",
            "--wheel-dir",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    return next(output.glob("*.whl"))


@pytest.fixture
def signing_resources(tmp_path, monkeypatch):
    raw = json.dumps(fx.TRUST_POLICY, sort_keys=True).encode()
    path = tmp_path / "policy.json"
    path.write_bytes(raw)
    monkeypatch.setattr(trust, "DEFAULT_TRUST_POLICY_PATH", path)
    monkeypatch.setattr(trust, "PRODUCTION_TRUST_POLICY_FILE_DIGEST_ALLOWLIST", frozenset({digest(raw)}))
    root = tmp_path / "keys"
    root.mkdir(mode=0o700)
    for role, private, key_id in [
        ("fleet_execution", fx.FLEET_SIGNING_KEY_HEX, fx.FLEET_KEY_ID),
        ("sources", fx.SOURCES_SIGNING_KEY_HEX, fx.SOURCES_KEY_ID),
        ("a3", fx.A3_SIGNING_KEY_HEX, fx.A3_KEY_ID),
    ]:
        for suffix, value in [(".key", private), (".key_id", key_id)]:
            key = root / (role + suffix)
            key.write_text(value)
            key.chmod(0o600)
    monkeypatch.setattr(trust, "HRAMATKA_SIGNING_KEY_ROOT", root)


@pytest.mark.parametrize("defect", [False, True])
def test_real_parent_consumes_author_constraints_and_reviewer_row(
    pg_cluster, tmp_path, monkeypatch, built_wheel, signing_resources, defect
):
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", pg_cluster.info.dsn)
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    io = RuntimeResources(tmp_path, pg_cluster, monkeypatch, defect=defect)
    constraints = {
        "task_kind": "original_row",
        "cefr_level": "A1",
        "required_fields": ["row_text", "answer"],
        "allowed_evidence_tools": ["verify_word"],
    }
    release = WheelRelease(built_wheel)
    try:
        with role_connection(pg_cluster, "hramatka_v4_control_writer") as conn:
            store = OperationStore(conn)
            service = service_runtime.V4ServiceRuntime(store=store, verifier=None, release_provider=release)

            def run(request_id, snapshot):
                semantic_inputs.freeze_semantic_input(conn, request_id=request_id, snapshot=snapshot)
                p = principal(request_id + "-authorize")
                policy = trust.load_production_trust_policy()[1]
                identifier = store.authorize(
                    principal=p,
                    raw=canonical_bytes({"schema": "hramatka-v4-operation-authorize.v1"}),
                    policy_digest=policy,
                )
                assert identifier
                owned = store.claim(
                    principal=replace(p, jti=request_id + "-execute"),
                    raw=canonical_bytes({"schema": "hramatka-v4-operation-execute.v1", "authorization_id": identifier}),
                    authorization_id=identifier,
                    policy_digest=policy,
                )
                assert owned["request_id"] == request_id
                result = service._execute_owned_claim(owned)
                assert result["state"] == "terminal"
                record = authority.resolve_execution_observation(
                    task_id=result["task_id"], run_id=result["run_id"], role=result["role"], conn=conn, is_pg=True
                )
                assert record and record["verification_tool_ids"]
                assert record["runtime_identity"] == release.verify(
                    __import__(
                        "learn_ukrainian_v4_runtime.provenance", fromlist=["verify_current_identity"]
                    ).verify_current_identity()
                )
                return owned, record

            with RequestExecutor(root=tmp_path) as executor:
                request = executor.create_request(recipient="claude", body="source-free fixture")
                executor.authorize_author_execution(
                    request_id=request.request_id, slot_id="v4p-standard-correct-001", expected_seat="claude-sonnet-5"
                )
            owned, record = run(request.request_id, {"constraints": constraints})
            signed = fleet.issue_author_execution_receipt(task_id=record["task_id"], run_id=record["run_id"])
            authored = ledger.build_authorship_receipt(
                author_execution_receipt=signed, row_content_sha256=record["row_content_sha256"]
            )
            authority.persist_authorship_receipt(
                authored, task_id=record["task_id"], run_id=record["run_id"], conn=conn, is_pg=True
            )
            row = {"row_text": "fixture-one"}
            if not defect:
                row["answer"] = "fixture-one"
            with RequestExecutor(root=tmp_path) as executor:
                reviewer = executor.create_request(recipient="codex", body="source-free reviewer")
                binding = executor.authorize_reviewer_execution(
                    request_id=reviewer.request_id,
                    authorship_receipt_id=authored["receipt_id"],
                    expected_seat="gpt-5.6-luna",
                )
            _, review = run(
                reviewer.request_id,
                {"authored_row": row, "constraints": constraints, "rubric_sha256": binding["rubric_sha256"]},
            )
            signed_review = fleet.issue_reviewer_execution_receipt(task_id=review["task_id"], run_id=review["run_id"])
            assert signed_review["verdict"] == ("FAIL" if defect else "PASS")
            assert review["row_content_sha256"] == record["row_content_sha256"]
            assert review["seat_or_model"] != record["seat_or_model"]
            assert (
                conn.execute(
                    "SELECT count(*) AS n FROM v4_sources_invocations WHERE attempt_id=%s", (owned["attempt_id"],)
                ).fetchone()["n"]
                == 1
            )
    finally:
        io.close()
