"""PR #7662 repair 8: native-runner V4 origin, typed Sources, fixed policy.

The progress criterion is one boundary-to-boundary positive path plus the
six accepted P1 adversarial repros. Fixtures substitute executable, VESUM
backend, and custody roots at the lowest IO edge. They do not insert
canonical observation rows, fake terminal observations, replace the runtime
writer/authorization, or add a test-only admission bypass.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import _v4_a7_real_slot_fixture as fx
import _v4_synthetic_chain_fixture as base_fixture
import pytest

from scripts.agent_runtime import runner as runtime_runner
from scripts.fleet_comms import v4_canonical_authority_store as v4_store
from scripts.fleet_comms.artifacts import ArtifactStore
from scripts.fleet_comms.request_executor import RequestExecutor, RequestExecutorError
from scripts.projects.open_model_data import v4_a6_blind_arena as a6
from scripts.projects.open_model_data import v4_a7_evidence_binder as evidence_binder
from scripts.projects.open_model_data import v4_a7_original_row_factory as a7
from scripts.projects.open_model_data import v4_a7_private_ledger as ledger
from scripts.projects.open_model_data import v4_a8_admission_assembly as a8
from scripts.projects.open_model_data import v4_fleet_execution_authority as fleet_execution
from scripts.projects.open_model_data import v4_sources_authority as sources_authority
from scripts.projects.open_model_data import v4_trust_authority as trust

FIXTURE_MODEL = "claude-sonnet-5"
FIXTURE_SESSION = "v4-runner-session-1"
REVIEWER_MODEL = "gpt-5.6-luna"
REVIEWER_SESSION = "11111111-1111-1111-1111-111111111111"
ROW_TEXT = fx.ROW_TEXT
PG_BIN = Path("/usr/lib/postgresql/18/bin")


def _sha(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def isolated_plane(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    plane = tmp_path / "fleet-plane"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(plane))
    monkeypatch.setenv("FLEET_COMMS_ALLOW_LOCAL_SHADOW", "1")
    monkeypatch.setattr(v4_store, "open_production_authority_store", lambda *, write=False: ArtifactStore(root=plane))
    return plane


def _write_vesum_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE forms (word_form TEXT, lemma TEXT, pos TEXT, tags TEXT)")
    conn.execute("INSERT INTO forms VALUES ('книга', 'книга', 'noun', '')")
    conn.commit()
    conn.close()
    return path


def _write_claude_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """#!/usr/bin/env python3
import json, os, sys, urllib.request
from pathlib import Path
if "--version" in sys.argv:
    print("2.1.200 (Claude Code)")
    raise SystemExit(0)
token = os.environ.get("V4_SOURCES_ATTEMPT_CAPABILITY", "")
url = os.environ.get("V4_SOURCES_MCP_URL", "")
args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg == "--mcp-config" and i + 1 < len(args):
        payload = json.loads(Path(args[i + 1]).read_text(encoding="utf-8"))
        sources = (payload.get("mcpServers") or {}).get("sources") or {}
        url = sources.get("url") or url
        headers = sources.get("headers") or {}
        auth = headers.get("Authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip() or token
        break
if token and url:
    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "verify_word", "arguments": {"word": "книга"}},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer " + token,
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()
prompt = " ".join(sys.argv)
if "role=reviewer" in prompt:
    text = "V4-REVIEW-VERDICT: PASS"
    session = "v4-runner-session-reviewer"
else:
    row = json.dumps({"row_text": """
        + json.dumps(ROW_TEXT)
        + """}, ensure_ascii=False)
    text = "V4-AUTHOR-ROW: " + row
    session = "v4-runner-session-1"
events = [
    {"type": "system", "subtype": "init", "session_id": session, "model": "claude-sonnet-5"},
    {"type": "assistant", "session_id": session, "message": {"model": "claude-sonnet-5", "content": [{"type": "text", "text": text}]}},
    {"type": "result", "subtype": "success", "session_id": session, "is_error": False},
]
for event in events:
    print(json.dumps(event, ensure_ascii=False), flush=True)
raise SystemExit(0)
"""
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def _write_codex_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """#!/usr/bin/env python3
import json, sys
from pathlib import Path
if "--version" in sys.argv:
    print("codex-cli 0.0.0-fixture")
    raise SystemExit(0)
args = sys.argv[1:]
out = None
for i, arg in enumerate(args):
    if arg == "-o" and i + 1 < len(args):
        out = args[i + 1]
if out:
    Path(out).write_text("V4-REVIEW-VERDICT: PASS\\n", encoding="utf-8")
session = "11111111-1111-1111-1111-111111111111"
print("session id: " + session, flush=True)
events = [
    {"type": "system", "subtype": "init", "session_id": session, "model": "gpt-5.6-luna"},
    {"type": "assistant", "session_id": session, "message": {"model": "gpt-5.6-luna", "content": [{"type": "text", "text": "V4-REVIEW-VERDICT: PASS"}]}},
    {"type": "result", "subtype": "success", "session_id": session, "is_error": False},
]
for event in events:
    print(json.dumps(event), flush=True)
raise SystemExit(0)
"""
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


@contextmanager
def _ephemeral_postgres(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Owned UTF-8 PG18 cluster. Never a live production DSN."""
    if not (PG_BIN / "initdb").is_file():
        pytest.skip("PostgreSQL 18 binaries are not installed")
    tmp = Path(tempfile.mkdtemp(prefix="v4-repair8-pg-", dir="/var/tmp"))
    tmp.chmod(0o700)
    sock = tmp / "socket"
    sock.mkdir(mode=0o700)
    port = 55481
    started = False
    try:
        subprocess.run(
            [str(PG_BIN / "initdb"), "-D", str(tmp / "db"), "--auth=trust", "--no-locale", "--encoding=UTF8"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        subprocess.run(
            [str(PG_BIN / "pg_ctl"), "-D", str(tmp / "db"), "-l", str(tmp / "server.log"), "-o", f"-k {sock} -h '' -p {port}", "-w", "start"],
            check=True,
            capture_output=True,
            timeout=60,
        )
        started = True
        dsn = f"host={sock} port={port} dbname=postgres user=ops"
        monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", dsn)
        monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
        yield dsn
    finally:
        if started:
            subprocess.run(
                [str(PG_BIN / "pg_ctl"), "-D", str(tmp / "db"), "-m", "fast", "-w", "stop"],
                capture_output=True,
                check=False,
                timeout=30,
            )
        shutil.rmtree(tmp, ignore_errors=True)


def _install_fixture_attesters(monkeypatch: pytest.MonkeyPatch, plane: Path) -> None:
    monkeypatch.setattr(trust, "load_production_trust_policy", lambda: (fx.TRUST_POLICY, fx.TRUST_POLICY_SHA256))
    monkeypatch.setattr(fleet_execution, "_load_signing_key", lambda role: (fx.FLEET_SIGNING_KEY_HEX, fx.FLEET_KEY_ID))
    monkeypatch.setattr(sources_authority, "_load_signing_key", lambda role: (fx.SOURCES_SIGNING_KEY_HEX, fx.SOURCES_KEY_ID))
    monkeypatch.setattr(fleet_execution, "_open_canonical_authority_store", lambda: ArtifactStore(root=plane))
    monkeypatch.setattr(sources_authority, "_open_canonical_authority_store", lambda: ArtifactStore(root=plane))


def _start_sources_http(monkeypatch: pytest.MonkeyPatch, vesum_db: Path) -> tuple[str, Any]:
    import importlib.util
    import sys

    from scripts.verification import vesum as vesum_mod

    monkeypatch.setattr(vesum_mod, "_resolve_vesum_db_path", lambda db_path=None: vesum_db)
    vesum_mod._vesum_conn = None
    vesum_mod._vesum_conn_path = None
    server_path = Path(__file__).resolve().parents[3] / ".mcp" / "servers" / "sources" / "server.py"
    spec = importlib.util.spec_from_file_location("sources_server_v4_origin", server_path)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v4_origin"] = srv
    spec.loader.exec_module(srv)
    app = srv.create_http_app()
    import uvicorn

    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    return f"http://127.0.0.1:{port}/mcp", server


def test_execute_capture_does_not_write_v4_observations(isolated_plane: Path) -> None:
    with RequestExecutor(root=isolated_plane) as executor:
        request = executor.create_request(recipient="claude", body="not a v4 origin")
        result = executor.execute_capture(
            request.request_id,
            events=(
                {"type": "system", "subtype": "init", "session_id": "s", "model": FIXTURE_MODEL},
                {"type": "result", "subtype": "success", "session_id": "s"},
            ),
            returncode=0,
        )
        assert result.state in {"complete", "incomplete", "failed"}
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 0


def test_authorize_author_execution_refuses_caller_row_hash(isolated_plane: Path) -> None:
    import inspect

    params = inspect.signature(RequestExecutor.authorize_author_execution).parameters
    assert "row_content_sha256" not in params
    assert "packet_sha256" not in params
    assert list(params) == ["self", "request_id", "slot_id", "expected_seat"]


def test_construct_completion_rejects_caller_policy_argument() -> None:
    import inspect

    assert "trust_policy" not in inspect.signature(ledger.construct_completion).parameters
    assert "trust_policy" not in inspect.signature(ledger.verify_private_replay).parameters


def test_authorization_race_against_start_sqlite(isolated_plane: Path) -> None:
    """Two sqlite connections: once start has left queued, late authorize refuses."""
    with RequestExecutor(root=isolated_plane) as authorizer, RequestExecutor(root=isolated_plane) as starter:
        request = authorizer.create_request(recipient="claude", body="race")
        binding = authorizer.authorize_author_execution(
            request_id=request.request_id,
            slot_id=fx.TARGET_SLOT_ID,
            expected_seat=FIXTURE_MODEL,
        )
        assert binding["role"] == "author"
        starter.claim_v4_runner_execution(request_id=request.request_id)
        late = authorizer.create_request(recipient="claude", body="late")
        # A second request can authorize a different slot, but the started
        # request cannot acquire another binding.
        with pytest.raises(RequestExecutorError, match="not authorizable"):
            authorizer.authorize_author_execution(
                request_id=request.request_id,
                slot_id="v4p-standard-correct-002",
                expected_seat=FIXTURE_MODEL,
            )
        assert late.state == "queued"


def test_fabricated_capture_cannot_mint_authority(isolated_plane: Path) -> None:
    with RequestExecutor(root=isolated_plane) as executor:
        request = executor.create_request(recipient="claude", body="fabricated")
        executor.authorize_author_execution(
            request_id=request.request_id, slot_id=fx.TARGET_SLOT_ID, expected_seat=FIXTURE_MODEL
        )
        executor.execute_capture(
            request.request_id,
            adapter="claude",
            events=(
                {"type": "system", "subtype": "init", "session_id": "other", "model": FIXTURE_MODEL},
                {"type": "result", "subtype": "success", "session_id": "other"},
            ),
            raw_bytes=b"NOT THE EVENTS",
            returncode=0,
        )
        assert executor.resolve_v4_execution_observation(
            task_id="missing", run_id="missing", role="author"
        ) is None
        rows = executor._conn.execute("SELECT COUNT(*) AS n FROM v4_execution_observations").fetchone()
        assert int(rows["n"]) == 0


def test_sources_invalid_input_is_not_successful(isolated_plane: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio
    import importlib.util
    import sys

    server_path = Path(__file__).resolve().parents[3] / ".mcp" / "servers" / "sources" / "server.py"
    spec = importlib.util.spec_from_file_location("sources_server_v4_neg", server_path)
    srv = importlib.util.module_from_spec(spec)
    sys.modules["sources_server_v4_neg"] = srv
    spec.loader.exec_module(srv)
    monkeypatch.setattr(v4_store, "open_production_authority_store", lambda *, write=False: ArtifactStore(root=isolated_plane))
    _content, is_error, typed = asyncio.run(srv._dispatch_tool_call("verify_word", {"word": ""}))
    assert is_error is False
    assert typed is not None
    assert typed["success"] is False
    assert typed["disposition"] == "invalid_input"
    _stress_content, stress_error, stress_typed = asyncio.run(srv._dispatch_tool_call("verify_stress", {"word": "vesum:made-up"}))
    if stress_error is False and stress_typed is not None:
        assert stress_typed["success"] is False
        assert stress_typed["disposition"] in {"invalid_input", "not_found", "negative", "ambiguous"}
    with ArtifactStore(root=isolated_plane) as store:
        rows = store.connection.execute("SELECT COUNT(*) AS n FROM v4_sources_invocations").fetchall()
        # No attempt capability => nothing recorded.
        assert int(rows[0]["n"]) == 0


def test_foreign_stale_attempt_capability_fails_closed(isolated_plane: Path) -> None:
    with ArtifactStore(root=isolated_plane) as store:
        resolved = v4_store.resolve_active_attempt_by_capability_digest(
            capability_digest="a" * 64, conn=store.connection, is_pg=False
        )
        assert resolved is None


def test_caller_policy_is_not_an_admission_argument() -> None:
    import inspect

    assert "trust_policy" not in inspect.signature(ledger.construct_completion).parameters
    with pytest.raises(TypeError):
        ledger.construct_completion(trust_policy={"schema_version": "nope"})  # type: ignore[call-arg]


def test_revoked_production_policy_invalidates_the_previous_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    row_content_sha256 = _sha(ROW_TEXT)
    real = fx.build_author_execution_receipt(row_content_sha256)
    revoked = trust.build_test_trust_policy(
        fleet_execution={fx.FLEET_KEY_ID: fx.FLEET_PUBLIC_KEY_HEX},
        revoked_key_ids=frozenset({fx.FLEET_KEY_ID}),
    )
    monkeypatch.setattr(trust, "load_production_trust_policy", lambda: (revoked, trust.trust_policy_sha256(revoked)))
    with pytest.raises(ledger.PrivateLedgerError, match="authenticity"):
        ledger.build_authorship_receipt(author_execution_receipt=real, row_content_sha256=row_content_sha256)


def test_sources_echoed_lexical_argument_is_not_the_identifier() -> None:
    identifier = v4_store.immutable_evidence_identifier(
        namespace="vesum",
        source_version="fixture-version",
        typed_result={"word": "книга", "matches": [{"lemma": "книга"}]},
    )
    assert identifier.startswith("vesum:")
    assert identifier != "книга"
    assert "книга" not in identifier


def test_boundary_to_boundary_positive_source_free(
    tmp_path: Path, isolated_plane: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Service authorize/claim → real runner → real Sources wire → observation
    → opaque issuers → construct/replay → A7/A8."""
    vesum_db = _write_vesum_fixture(tmp_path / "vesum.db")
    claude_bin = _write_claude_fixture(tmp_path / "bin" / "claude")
    _write_codex_fixture(tmp_path / "bin" / "codex")
    monkeypatch.setenv("PATH", str(claude_bin.parent) + os.pathsep + os.environ.get("PATH", ""))
    from scripts.agent_runtime.adapters import claude as claude_adapter

    claude_adapter._probe_claude_cli_version.cache_clear()
    monkeypatch.setattr("scripts.agent_runtime.adapters.claude._default_claude_bin", lambda: str(claude_bin))
    url, _server = _start_sources_http(monkeypatch, vesum_db)
    monkeypatch.setenv("V4_SOURCES_MCP_URL", url)
    _install_fixture_attesters(monkeypatch, isolated_plane)

    mcp_config = tmp_path / "mcp.json"
    mcp_config.write_text(json.dumps({"mcpServers": {"sources": {"type": "streamable-http", "url": url}}}))

    with RequestExecutor(root=isolated_plane) as executor:
        request = executor.create_request(recipient="claude", body="ignored-caller-prompt")
        binding = executor.authorize_author_execution(
            request_id=request.request_id,
            slot_id=fx.TARGET_SLOT_ID,
            expected_seat=FIXTURE_MODEL,
        )
        assert "ignored-caller-prompt" not in binding["authorized_prompt"]
        result = runtime_runner.invoke(
            "claude",
            "caller prompt must not be transported",
            cwd=tmp_path,
            model=FIXTURE_MODEL,
            tool_config={"mcp_config_path": str(mcp_config), "allowed_tools": "mcp__sources__verify_word", "use_bare": True},
            v4_authorization_id=request.request_id,
            hard_timeout=30,
        )
        assert result.ok is True
        record = executor.resolve_v4_execution_observation(
            task_id=binding["task_id"], run_id=binding["run_id"], role="author"
        )
        assert record is not None
        assert record["seat_or_model"] == FIXTURE_MODEL
        assert record["session_id"] == FIXTURE_SESSION
        assert record["harness"] == "claude"
        assert record["row_content_sha256"] == _sha(ROW_TEXT)
        assert record["saw_source_text"] is False
        assert record["prompt_sha256"] == binding["prompt_sha256"]
        assert "mcp__sources__verify_word" in record["verification_tool_ids"]

    author_receipt = fleet_execution.issue_author_execution_receipt(task_id=binding["task_id"], run_id=binding["run_id"])
    authorship = ledger.build_authorship_receipt(
        author_execution_receipt=author_receipt, row_content_sha256=_sha(ROW_TEXT)
    )
    with RequestExecutor(root=isolated_plane) as executor:
        executor.persist_v4_authorship_receipt(authorship, task_id=binding["task_id"], run_id=binding["run_id"])
        review_request = executor.create_request(recipient="codex", body="ignored-reviewer-prompt")
        review_binding = executor.authorize_reviewer_execution(
            request_id=review_request.request_id,
            authorship_receipt_id=authorship["receipt_id"],
            expected_seat=REVIEWER_MODEL,
        )
        review_result = runtime_runner.invoke(
            "codex",
            "caller reviewer prompt must not be transported",
            cwd=tmp_path,
            model=REVIEWER_MODEL,
            v4_authorization_id=review_request.request_id,
            hard_timeout=30,
        )
        assert review_result.ok is True
        review_record = executor.resolve_v4_execution_observation(
            task_id=review_binding["task_id"], run_id=review_binding["run_id"], role="reviewer"
        )
        assert review_record is not None
        assert review_record["harness"] == "codex"
        assert review_record["seat_or_model"] == REVIEWER_MODEL
        assert review_record["verdict"] == "PASS"
        assert review_record["prompt_sha256"] == review_binding["prompt_sha256"]

    reviewer_receipt = fleet_execution.issue_reviewer_execution_receipt(
        task_id=review_binding["task_id"], run_id=review_binding["run_id"]
    )

    with ArtifactStore(root=isolated_plane) as store:
        inv_rows = store.connection.execute("SELECT record_json FROM v4_sources_invocations").fetchall()
    assert inv_rows, "real Sources wire must have recorded a typed invocation for the running attempt"
    inv = json.loads(str(inv_rows[0]["record_json"]))
    assert inv["success"] is True
    assert inv["identifier"].startswith(("vesum:", "sources:"))
    assert inv["identifier"] != "книга"
    attestation = sources_authority.issue_verifier_attestation(invocation_id=inv["invocation_id"])
    assert attestation["identifier"] == inv["identifier"]
    verifier_receipt = evidence_binder.build_verifier_receipt(attestation=attestation)
    evidence_receipt = evidence_binder.build_evidence_receipt(_sha(ROW_TEXT), [verifier_receipt])

    tmp_root = base_fixture.build_synthetic_chain_root(tmp_path / "slot-root", resolved_stratum="standard_correct")
    sealed = fx.build_sealed_receipt_and_packet(tmp_path / "slot-root")
    a6_receipt = a6.build_receipt(tmp_root)
    a6.validate_receipt_independently(a6_receipt, tmp_root)
    (tmp_root / "data/projects/open_model_data/admission/dataset_v4_a6_blind_arena_receipt_v1.json").write_text(json.dumps(a6_receipt))
    reference_check_receipt = fx.build_reference_check_receipt()
    reference_check_signature, replay_attestation = fx.build_reference_check_authenticity(reference_check_receipt)
    completion = ledger.construct_completion(
        slot_id=fx.TARGET_SLOT_ID,
        salt=fx.TEST_SALT,
        candidate_unit_ids=list(fx.CANDIDATE_UNIT_IDS),
        a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
        seal_receipt_path=sealed["seal_receipt_path"],
        membership_dir=sealed["membership_dir"],
        packet_dir=sealed["packet_dir"],
        manifest=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text()),
        a2_receipt=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text()),
        row_text=ROW_TEXT,
        tier="silver",
        author_execution_receipt=author_receipt,
        reviewer_execution_receipt=reviewer_receipt,
        evidence_receipt=evidence_receipt,
        reference_check_receipt=reference_check_receipt,
        reference_check_signature=reference_check_signature,
        replay_attestation=replay_attestation,
        rights_receipt_id=fx.RIGHTS_RECEIPT_ID,
    )
    public_completion = completion["public_completion"]
    ledger_path = tmp_path / "batch_state/open-model-data/v4-a7-factory/v4_a7_private_ledger_v1.json"
    ledger.write_ledger({public_completion["slot_id"]: completion["private_entry"]}, ledger_path)
    admission_dir = tmp_root / "data/projects/open_model_data/admission"
    a7_receipt = a7.build_receipt(tmp_root, a7_completions=[public_completion])
    a7.validate_receipt_independently(a7_receipt, tmp_root)
    (admission_dir / "dataset_v4_a7_original_row_factory_receipt_v1.json").write_text(json.dumps(a7_receipt))
    a8_completion = {
        "stage": "A8",
        "slot_id": public_completion["slot_id"],
        "row_id": public_completion["row_id"],
        "row_content_sha256": public_completion["row_content_sha256"],
        "trust_policy_sha256": public_completion["trust_policy_sha256"],
    }
    a8_receipt = a8.build_receipt(tmp_root, a8_completions=[a8_completion])
    a8.validate_receipt_independently(a8_receipt, tmp_root)
    a8.validate_a8_completions_match_a7(a8_receipt["a8_completions"], a7_receipt["a7_completions"])
    stored_ledger = ledger.load_ledger(ledger_path)
    ledger.verify_private_replay(
        a7_receipt,
        stored_ledger,
        salt=fx.TEST_SALT,
        a4_unit_commitments=fx.a4_unit_commitments(tmp_root),
        seal_receipt_path=sealed["seal_receipt_path"],
        membership_dir=sealed["membership_dir"],
        packet_dir=sealed["packet_dir"],
        manifest=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json").read_text()),
        a2_receipt=json.loads((tmp_root / "data/projects/open_model_data/admission/dataset_v4_a2_source_operation_admission_receipt_v1.json").read_text()),
    )


@pytest.mark.postgres
def test_authorization_race_against_start_postgres(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.control_plane.storage import Authority

    with _ephemeral_postgres(monkeypatch):
        with RequestExecutor(root=tmp_path / "pg-a") as authorizer, RequestExecutor(root=tmp_path / "pg-b") as starter:
            assert authorizer.authority is Authority.PG
            assert starter.authority is Authority.PG
            request = authorizer.create_request(recipient="claude", body="pg-race")
            authorizer.authorize_author_execution(
                request_id=request.request_id, slot_id=fx.TARGET_SLOT_ID, expected_seat=FIXTURE_MODEL
            )
            starter.claim_v4_runner_execution(request_id=request.request_id)
            with pytest.raises(RequestExecutorError, match="not authorizable"):
                authorizer.authorize_author_execution(
                    request_id=request.request_id, slot_id="v4p-standard-correct-002", expected_seat=FIXTURE_MODEL
                )
