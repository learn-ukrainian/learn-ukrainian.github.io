"""Source-free IO resources for the real public parent mechanism.

No auth verifier, canonical row, observation writer, child runner, parser or
finalizer is replaced. The private adapter boundary is deliberately not tested.
The fixture CLI consumes stdin and Sources HTTP but makes no model-quality claim.
"""

from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import sysconfig
import threading
import time
import zipfile
from pathlib import Path

import uvicorn
from learn_ukrainian_v4_runtime import child_runtime, scoped_store, service_runtime, sources_handlers, sources_transport
from learn_ukrainian_v4_runtime.operation_auth import digest
from learn_ukrainian_v4_runtime.provenance import verify_current_identity
from test_v4_preserved_provenance import LexicalResources

CHILD = """#!/runtime/py/bin/python
import json, os, sys, urllib.request
args=sys.argv[1:]
prompt=sys.stdin.read()
assert prompt.count("V4-SEMANTIC-INPUT: ")==1
payload=json.loads(prompt.split("V4-SEMANTIC-INPUT: ",1)[1])
model=args[args.index("--model")+1]
if "--mcp-config" in args:
    config=json.loads(args[args.index("--mcp-config")+1])
    assert set(config["mcpServers"])=={"sources"}
    source=config["mcpServers"]["sources"]
    url=source["url"]
    token=source["headers"]["Authorization"]
    assert "--strict-mcp-config" in args and args[args.index("--tools")+1]==""
else:
    values=[args[i+1] for i,x in enumerate(args) if x=="-c"]
    url=json.loads(next(x.split("=",1)[1] for x in values if x.startswith("mcp_servers.sources.url=")))
    assert 'mcp_servers.sources.bearer_token_env_var="V4_SOURCES_ATTEMPT_CAPABILITY"' in values
    token="Bearer "+os.environ["V4_SOURCES_ATTEMPT_CAPABILITY"]
assert token=="Bearer "+os.environ["V4_SOURCES_ATTEMPT_CAPABILITY"]
assert not os.path.exists("/home/ops") and not os.path.exists("/run/credentials")
assert not os.path.exists("/usr/bin/sh") and not os.path.exists("/usr/bin/psql")
body=json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"verify_word","arguments":{"word":"fixture-one"}}}).encode()
request=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","Authorization":token})
with urllib.request.urlopen(request,timeout=10) as response:
    evidence=json.load(response)
assert "error" not in evidence, evidence
if payload["role"]=="author":
    row={key:"fixture-one" for key in payload["constraints"]["required_fields"]}
    if DEFECT: row.pop("answer",None)
    text="V4-AUTHOR-ROW: "+json.dumps(row)
else:
    assert payload["rubric"] and len(payload["authorship_receipt_sha256"])==64
    valid=all(isinstance(payload["authored_row"].get(key),str) and payload["authored_row"][key] for key in payload["constraints"]["required_fields"])
    text="V4-REVIEW-VERDICT: "+("PASS" if valid else "FAIL")
session="fixture-"+payload["role"]
for event in [{"type":"system","subtype":"init","model":model,"session_id":session},{"type":"assistant","session_id":session,"message":{"model":model,"content":[{"type":"text","text":text}]}},{"type":"result","subtype":"success","session_id":session,"is_error":False}]:
    print(json.dumps(event),flush=True)
"""


def pinned_profile(root, *, sources_url, defect=False):
    """Pin an owned fixture executable and its CPython closure, one file per mount."""
    executable = root / "fixture-cli"
    executable.write_text(CHILD.replace("DEFECT", repr(defect)))
    executable.chmod(0o700)
    base = Path(sys.base_prefix)
    stdlib = Path(sysconfig.get_path("stdlib"))
    selected = {Path(sys.executable).resolve(): "/runtime/py/bin/python", executable: "/runtime/fixture-cli"}
    for path in stdlib.rglob("*"):
        if (
            path.is_file()
            and path.suffix in (".py", ".so")
            and not {"site-packages", "__pycache__", "test", "tests"} & set(path.parts)
        ):
            selected[path.resolve()] = "/runtime/py/" + str(path.relative_to(base))
    for path in (base / "lib").glob("*.so*"):
        if path.is_file():
            selected[path.resolve()] = "/runtime/py/lib/" + path.resolve().name
    # This is only test interpreter dependency discovery, not product asset
    # discovery. Never expose loader addresses or local dependency paths in logs.
    for binary in [Path(sys.executable).resolve(), *[p for p in selected if p.suffix == ".so"]]:
        result = subprocess.run(["ldd", str(binary)], capture_output=True, text=True, check=False)
        for name in re.findall(r"(/[\w./+\-]+)", result.stdout):
            path = Path(name)
            if path.is_file() and not path.is_relative_to(base):
                selected[path.resolve()] = name
    files = []
    closure = root / "fixture-interpreter-files"
    closure.mkdir()
    for index, (path, target) in enumerate(sorted(selected.items())):
        if path.stat().st_mode & 0o022:
            copied = closure / str(index)
            copied.write_bytes(path.read_bytes())
            copied.chmod(0o700 if path.stat().st_mode & 0o111 else 0o600)
            path = copied
        files.append({"source": str(path), "destination": target, "sha256": digest(path.read_bytes())})
    adapter = {
        "version": "input-consuming-fixture.v1",
        "models": ["claude-sonnet-5", "gpt-5.6-luna"],
        "files": files,
        "executable": "/runtime/fixture-cli",
    }
    profile = {
        "schema": "hramatka-v4-child-profile.v1",
        "bwrap": "/usr/bin/bwrap",
        "bwrap_sha256": digest(Path("/usr/bin/bwrap").read_bytes()),
        "sources_url": sources_url,
        "adapters": {
            name: {**adapter, "provider_env": env}
            for name, env in [("claude", "ANTHROPIC_API_KEY"), ("codex", "OPENAI_API_KEY")]
        },
    }
    path = root / "profile.json"
    path.write_text(json.dumps(profile))
    return path


class WheelRelease:
    """Verify this test's owned wheel bytes; not a private vendor attestation."""

    def __init__(self, wheel):
        self.wheel = wheel

    def verify(self, installed_identity):
        actual = verify_current_identity()
        assert actual == installed_identity
        with zipfile.ZipFile(self.wheel) as archive:
            for name, sha in actual["installed_files"].items():
                assert digest(archive.read("learn_ukrainian_v4_runtime/" + name)) == sha
        return {**actual, "wheel_sha256": digest(self.wheel.read_bytes())}


class RuntimeResources:
    def __init__(self, root, pg, monkeypatch, *, defect=False):
        self.root = root
        # LOGIN applies only to this owned ephemeral cluster. Production roles,
        # credentials and services are never touched.
        pg.execute("ALTER ROLE hramatka_v4_sources_writer LOGIN")
        pg.execute("ALTER ROLE hramatka_v4_control_writer LOGIN")
        from psycopg.conninfo import make_conninfo

        for module, role, attribute in [
            (sources_transport, "hramatka_v4_sources_writer", "credential_path"),
            (scoped_store, "hramatka_v4_control_writer", "control_credential_path"),
        ]:
            path = root / (role + ".dsn")
            path.write_text(make_conninfo(pg.info.dsn, user=role))
            path.chmod(0o600)
            monkeypatch.setattr(module, attribute, lambda path=path: path)
        key = root / "provider.json"
        key.write_text('{"credential":"source-free-fixture"}')
        key.chmod(0o600)
        monkeypatch.setattr(service_runtime, "provider_credential_path", lambda harness: key)
        monkeypatch.setattr(sources_handlers, "_backend", LexicalResources())
        listener = socket.socket()
        listener.bind(("localhost", 0))
        listener.listen(16)
        self.server = uvicorn.Server(
            uvicorn.Config(sources_transport.create_sources_app(), log_level="critical", access_log=False)
        )
        self.thread = threading.Thread(target=self.server.run, kwargs={"sockets": [listener]}, daemon=True)
        self.thread.start()
        deadline = time.monotonic() + 10
        while not self.server.started and self.thread.is_alive() and time.monotonic() < deadline:
            time.sleep(0.01)
        assert self.server.started
        self.url = f"http://{socket.gethostbyname('localhost')}:{listener.getsockname()[1]}/mcp"
        path = pinned_profile(root, sources_url=self.url, defect=defect)
        monkeypatch.setattr(child_runtime, "profile_path", lambda: path)

    def close(self):
        self.server.should_exit = True
        self.thread.join(timeout=10)
        assert not self.thread.is_alive()


def produce_author_record(root, pg, monkeypatch, wheel):
    """Produce a record through the public parent, never through a fixture writer."""
    from dataclasses import replace

    from learn_ukrainian_v4_runtime import semantic_inputs
    from learn_ukrainian_v4_runtime import v4_canonical_authority_store as authority
    from learn_ukrainian_v4_runtime import v4_trust_authority as trust
    from learn_ukrainian_v4_runtime.operation_auth import canonical_bytes
    from learn_ukrainian_v4_runtime.operation_store import OperationStore
    from test_v4_operation_lifecycle import principal, role_connection

    from scripts.fleet_comms.request_executor import RequestExecutor

    monkeypatch.setenv("LEARN_UKRAINIAN_CP_PG_DSN", pg.info.dsn)
    monkeypatch.setenv("LEARN_UKRAINIAN_CP_AUTHORITY_FLEET_COMMS", "pg")
    io = RuntimeResources(root, pg, monkeypatch)
    try:
        with RequestExecutor(root=root) as executor:
            request = executor.create_request(recipient="claude", body="source-free operation")
            executor.authorize_author_execution(
                request_id=request.request_id, slot_id="v4p-standard-correct-001", expected_seat="claude-sonnet-5"
            )
        with role_connection(pg, "hramatka_v4_control_writer") as conn:
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
            auth = principal(request.request_id + "-auth")
            policy = trust.load_production_trust_policy()[1]
            identifier = store.authorize(
                principal=auth,
                raw=canonical_bytes({"schema": "hramatka-v4-operation-authorize.v1"}),
                policy_digest=policy,
            )
            owned = store.claim(
                principal=replace(auth, jti=request.request_id + "-execute"),
                raw=canonical_bytes({"schema": "hramatka-v4-operation-execute.v1", "authorization_id": identifier}),
                authorization_id=identifier,
                policy_digest=policy,
            )
            runtime = service_runtime.V4ServiceRuntime(store=store, verifier=None, release_provider=WheelRelease(wheel))
            result = runtime._execute_owned_claim(owned)
            record = authority.resolve_execution_observation(
                task_id=result["task_id"], run_id=result["run_id"], role="author", conn=conn, is_pg=True
            )
            assert record
            return owned["binding"], record
    finally:
        io.close()
