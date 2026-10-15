"""Subprocess evidence for the formal-attempt launch boundary (#9251)."""

from __future__ import annotations

import copy
import errno
import hashlib
import http.client
import http.server
import json
import os
import shutil
import socket
import string
import subprocess
import sys
import tempfile
import threading
import tomllib
import urllib.request
import warnings
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.agent_runtime import attempt_boundary, env_sanitize, runner
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.attempt_boundary import (
    AttemptBoundary,
    authorized_closure,
    prepare_attempt_boundary,
    runtime_files,
)
from scripts.agent_runtime.errors import AgentUnavailableError
from scripts.agent_runtime.result import ParseResult
from scripts.agent_runtime.review_mcp import prepare_review_attempt
from scripts.review.isolation import ReviewIsolationError


def manifest_world(root: Path, kind: str) -> dict:
    state = "curriculum/l2-uk-en/evidence/a1/_state/sample"
    plans = "curriculum/l2-uk-en/lesson-plans/a1"
    paths = {
        "plan": f"{plans}/sample.yaml",
        "pack": "curriculum/l2-uk-en/evidence/a1/sample.yaml",
        "pack_lock": "curriculum/l2-uk-en/evidence/a1/sample.yaml.lock",
        "words": "curriculum/l2-uk-en/evidence/a1/_words.yaml",
        "words_lock": "curriculum/l2-uk-en/evidence/a1/_words.yaml.lock",
        "decisions": f"{plans}/_decisions.yaml",
    }
    lesson = kind != "plan"
    paths["learner_state"] = f"{state}/{'lesson-1' if lesson else 'plan-review'}.learner-state.yaml"
    if lesson:
        paths.update(
            {
                "lessons_lock": f"{state}/lessons.lock.yaml",
                "lesson": "site/src/content/docs/a1/sample/1.mdx",
                "provenance": f"{state}/lesson-1.provenance.yaml",
                "gate_report": f"{state}/lesson-1.gates.yaml",
                "style_card": "docs/style-cards/a1.md",
            }
        )
    else:
        paths.update(
            {
                "requirements": "docs/epics/fresh-build-requirements.md",
                "arc": f"{plans}/_arc.yaml",
                "arc_source": "docs/epics/fresh-build-a1-arc.md",
                "scope": f"{plans}/_scope/sample.yaml",
                "grammar": f"{plans}/_grammar.yaml",
                "validate_report": f"{state}/plan-validate.report.json",
                "pack_verify_report": f"{state}/pack-verify.report.json",
            }
        )

    def pin(name: str) -> dict:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Authorized current input.\n")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    doc = {
        "manifest_schema": 1,
        "kind": "lesson" if lesson else "plan",
        "level": "a1",
        "slug": "sample",
        "inputs": {name: pin(path) for name, path in paths.items()},
        "learner_state": {"sha256": "a" * 64, "source": "planned_state"},
    }
    if lesson:
        doc.update(
            {
                "lesson": 1,
                "lesson_kind": "lesson",
                "recap": False,
                "review_eligible": True,
                "blocked_by": [],
                "lesson_lock_entry": {"path": paths["lesson"], "lesson": 1, "entry_sha256": "a" * 64},
                "module_digest": pin(f"{state}/digest-upto-1.yaml"),
                "digest_generator_version": "1",
                "upstream_lessons": [],
                "previous_attempt": None,
                "diff": None,
            }
        )
        doc["inputs"]["activity_data"] = []
        if kind == "rereview":
            doc["previous_attempt"] = {
                "attempt_id": "previous",
                "review": pin(f"{state}/lesson-1.review.previous.yaml"),
                "ledger": pin("batch_state/review-receipts/review/previous.jsonl"),
            }
            doc["diff"] = pin(f"{state}/lesson-1.diff.previous.{'a' * 16}.patch")
    else:
        doc["position"] = 1
    return doc


@pytest.fixture
def world(tmp_path, monkeypatch):
    root = tmp_path / "repository"
    root.mkdir()
    home = tmp_path / "old-home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "auth.json").write_text("{}")
    (home / ".codex" / "auth.json").chmod(0o600)
    token = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    token.parent.mkdir(parents=True)
    token.write_text("{}")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("CODEX_HOME", str(home / ".codex"))
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(token.parent))
    return root, home


def attempt_config(root: Path, tmp_path: Path, manifest: dict, agent: str, *, review_access: str = "isolated") -> dict:
    path = root / "attempt.yaml"
    path.write_text(yaml.safe_dump(manifest))
    plan = prepare_review_attempt(
        "review", "current", path, agent, receipts_root=tmp_path / "receipts", review_access=review_access
    )
    return {
        **plan.adapter_options,
        "review_id": "review",
        "attempt_id": "current",
        "review_manifest": str(path),
        "review_input_root": str(root),
        "review_access": review_access,
    }


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_agy_attempt_home_registers_same_guard_as_review_provisioner(world, tmp_path, access):
    from scripts.agent_runtime.agy_hook_config import HookConfigResult, check_hook_config
    from scripts.agent_runtime.review_mcp import _populate_agy_review_home

    root, old_home = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy", review_access=access)
    if access == "full":
        tc["review_cwd"] = str(root)
    boundary = AttemptBoundary(agent="agy", tool_config=tc)
    try:
        hooks = Path(boundary.tool_config["agy_home_override"]) / ".gemini/config/hooks.json"
        assert check_hook_config((hooks,)) == HookConfigResult("PASS", "guard_registered")
        comparison = tmp_path / "comparison-home"
        comparison.mkdir(mode=0o700)
        fd = os.open(comparison, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            _populate_agy_review_home(
                fd,
                old_home / ".gemini/antigravity-cli/antigravity-oauth-token",
                Path(boundary.tool_config["mcp_config_path"]).read_bytes(),
                boundary.workspace,
            )
        finally:
            os.close(fd)
        assert hooks.read_bytes() == (comparison / ".gemini/config/hooks.json").read_bytes()
        assert hooks.stat().st_mode & 0o777 == 0o600
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("agent", ["agy", "codex"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_subprocess_forbidden_read_matrix(world, tmp_path, agent, kind):
    root, old_home = world
    manifest = manifest_world(root, kind)
    forbidden_names = [
        "batch_state/review-receipts/review/other.jsonl",
        "batch_state/returns/other.yaml",
        "batch_state/task.json",
        "scripts/review/record.py",
        "scripts/review/receipts/ledger.py",
        "scripts/delegate.py",
        "earlier-edition.yaml",
    ]
    for name in forbidden_names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Forbidden evidence\n")
    prior = old_home / ".codex" / "sessions" / "previous.jsonl"
    prior.parent.mkdir()
    prior.write_text("Prior session\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        ],
        check=True,
        timeout=30,
    )
    tc = attempt_config(root, tmp_path, manifest, agent)
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    try:
        # Symlinks created INSIDE the writable seat tree still cannot expose
        # an unmounted target. The original Git object database is unmounted.
        link = boundary.write_root / "escape"
        link.symlink_to(root, target_is_directory=True)
        relative = os.path.relpath(root, boundary.workspace)
        forbidden = [str(root / name) for name in forbidden_names]
        forbidden += [str(Path(relative) / name) for name in forbidden_names]
        forbidden += [str(link / name) for name in forbidden_names]
        forbidden += [str(prior), str(old_home / ".codex" / "config.toml")]
        (old_home / ".codex" / "config.toml").write_text("Prior config\n")
        authorized = authorized_closure(manifest, root)
        script = (
            "import json,pathlib,subprocess,os\n"
            f"denied={forbidden!r}\n"
            "for name in denied:\n"
            " try: pathlib.Path(name).read_bytes()\n"
            " except OSError: pass\n"
            " else: raise AssertionError('forbidden read succeeded')\n"
            f"expected={authorized!r}\n"
            "for name,data in expected.items(): assert pathlib.Path(name).read_bytes()==data\n"
            f"repo={str(root)!r}\n"
            "for args in [('show','HEAD:scripts/review/record.py'),('log','-p')]:\n"
            " assert subprocess.run(['git','-C',repo,*args],capture_output=True,timeout=5).returncode!=0\n"
            f"os.environ['GIT_DIR']={str(root / '.git')!r}\n"
            "assert subprocess.run(['git','show','HEAD:scripts/review/record.py'],capture_output=True,timeout=5).returncode!=0\n"
            f"pathlib.Path({str(boundary.write_root / 'return.yaml')!r}).write_text('own return')\n"
            "print(json.dumps({'denied':len(denied),'authorized':len(expected),'git':3}))\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout)["denied"] == 23
        assert (boundary.write_root / "return.yaml").read_text() == "own return"
        # A manifest projection is immutable even when the seat has a shell.
        cmd, env = boundary.wrap(
            ["/bin/sh", "-c", "echo corrupt > curriculum/l2-uk-en/lesson-plans/a1/sample.yaml"], {}
        )
        assert subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, timeout=30).returncode != 0
    finally:
        boundary.cleanup()
    assert not boundary.workspace.exists()


@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_closure_rejects_hash_drift_and_extra_pins(world, kind):
    root, _ = world
    doc = manifest_world(root, kind)
    assert authorized_closure(doc, root)
    changed = copy.deepcopy(doc)
    changed["inputs"]["plan"]["sha256"] = "b" * 64
    with pytest.raises(ReviewIsolationError, match="hash_mismatch"):
        authorized_closure(changed, root)
    changed = copy.deepcopy(doc)
    changed["inputs"]["harness"] = {"path": "scripts/review/record.py", "sha256": "a" * 64}
    with pytest.raises(ReviewIsolationError, match="ineligible"):
        authorized_closure(changed, root)
    with pytest.raises(ReviewIsolationError, match="kind"):
        authorized_closure({"kind": "settle"}, root)


def test_runtime_files_does_not_grant_native_binary_parent():
    binary = Path(shutil.which("true")).resolve()
    assert binary in runtime_files(binary)
    assert binary.parent not in runtime_files(binary)


@pytest.mark.parametrize(
    "agent,access", [("agy", "isolated"), ("codex", "isolated"), ("agy", "full"), ("codex", "full"), ("claude", "full")]
)
def test_sources_proxy_records_receipts_outside_seat(world, tmp_path, agent, access):
    root, _ = world
    doc = manifest_world(root, "plan")
    tc = attempt_config(root, tmp_path, doc, agent, review_access=access)
    tc.update(review_access=access, review_cwd=str(root))
    if access == "full":
        subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    try:
        if agent == "codex":
            parsed = tomllib.loads((Path(boundary.tool_config["codex_home_override"]) / "config.toml").read_text())
            assert len(parsed["mcp_servers"]["sources"]["args"]) == 2
        proxy = json.loads(Path(boundary.tool_config["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "boundary-probe", "version": "1"},
                },
            },
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "verify_words", "arguments": {"words": []}},
            },
        ]
        cmd, env = boundary.wrap([proxy["command"], *proxy["args"]], {})
        # Use a real MCP handshake and keep stdin open until the tool result:
        # EOF is allowed to cancel pending tool tasks in the server.
        script = (
            "import subprocess,json\n"
            f"p=subprocess.Popen({[proxy['command'], *proxy['args']]!r},stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)\n"
            f"requests={requests!r}\n"
            "for r in requests:\n"
            " p.stdin.write(json.dumps(r)+'\\n'); p.stdin.flush()\n"
            " if 'id' in r:\n"
            "  response=json.loads(p.stdout.readline()); assert response.get('id')==r['id']\n"
            "  print(json.dumps(response),flush=True)\n"
            "p.stdin.close(); assert p.wait(timeout=10)==0\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, proc.stderr
        responses = [json.loads(line) for line in proc.stdout.splitlines()]
        assert any(r.get("id") == 2 and "result" in r for r in responses), proc.stdout
        ledger = Path(
            json.loads(Path(tc["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]["env"][
                "LU_REVIEW_LEDGER_PATH"
            ]
        )
        assert ledger.read_bytes(), proc.stdout
        # The same boundary cannot read even its own runtime ledger.
        cmd, env = boundary.wrap(["/bin/cat", str(ledger)], {})
        read_result = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, timeout=30)
        assert read_result.returncode != 0
        cmd, env = boundary.wrap(["/bin/sh", "-c", 'printf forged >> "$1"', "probe", str(ledger)], {})
        assert subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, timeout=30).returncode != 0
    finally:
        processes = boundary.connection.processes
        boundary.cleanup()
    assert processes and all(p.poll() is not None for p in processes)


def test_runner_requires_boundary_and_preserves_nonattempt_behavior(monkeypatch):
    for agent in ("agy", "codex", "claude"):
        assert prepare_attempt_boundary(agent, "read-only", None, {}) is None
    for tc, mode, session in [
        ({"review_id": "review"}, "read-only", None),
        ({"attempt_id": "current", "strict_mcp_config": True}, "workspace-write", None),
        ({"review_id": "review", "strict_mcp_config": True}, "read-only", "previous"),
    ]:
        with pytest.raises(AgentUnavailableError, match="filesystem boundary refused"):
            runner.invoke("agy", "probe", tool_config=tc, mode=mode, session_id=session)


@pytest.mark.parametrize("site", ["prepare", "wrap"])
@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (ReviewIsolationError("attempt_egress_unavailable"), "attempt_egress_unavailable"),
        (ReviewIsolationError("sandbox_probe_allow_failed:private diagnostic"), "sandbox_probe_allow_failed"),
        (ReviewIsolationError("attempt_boundary_claude_adapter_pending"), "attempt_boundary_claude_adapter_pending"),
        (ReviewIsolationError("invalid private diagnostic"), "ReviewIsolationError"),
        (OSError("private diagnostic"), "OSError"),
        (ValueError("private diagnostic"), "ValueError"),
        (RuntimeError("attempt_boundary_claude_adapter_pending"), "RuntimeError"),
    ],
)
def test_runner_boundary_refusal_reports_only_code_or_exception_class(tmp_path, monkeypatch, site, error, detail):
    def refuse(*args, **kwargs):
        raise error

    def unexpected(*args, **kwargs):
        pytest.fail("refused attempts must not plan or spawn a provider invocation")

    monkeypatch.setattr(subprocess, "Popen", unexpected)
    with pytest.raises(AgentUnavailableError) as caught:
        if site == "prepare":
            monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.prepare_attempt_boundary", refuse)
            monkeypatch.setattr(runner, "_load_adapter", unexpected)
            runner.invoke("agy", "probe", cwd=tmp_path, tool_config={"review_id": "review"})
        else:
            boundary = SimpleNamespace(workspace=tmp_path, verify_seat=lambda *a: None, wrap=refuse)
            runner._execute_invocation_plan(
                agent_name="agy",
                adapter=None,
                plan=InvocationPlan(cmd=["agy", "--version"], cwd=tmp_path),
                prompt="probe",
                mode="read-only",
                cwd=tmp_path,
                model="fixture-model",
                task_id="probe",
                session_id=None,
                entrypoint="runtime",
                hard_timeout=30,
                stall_timeout=30,
                tool_config={"review_attempt_boundary": boundary},
            )
    assert str(caught.value) == f"formal attempt filesystem boundary refused: {site}: {detail}"
    assert caught.value.__cause__ is error


@pytest.mark.parametrize(
    ("prefix", "diagnostic", "expected_identifier"),
    [
        ("sandbox_probe_allow_failed", "seat_controlled_identifier", "sandbox_probe_allow_failed"),
        ("sandbox_probe_allow_failed", "secret/path", "sandbox_probe_allow_failed"),
        ("sandbox_probe_allow_failed", "wrap: spoofed", "sandbox_probe_allow_failed"),
        ("sandbox_probe_allow_failed", "\nspoofed", "sandbox_probe_allow_failed"),
        ("Seat Text", "x", "ReviewIsolationError"),
    ],
)
def test_runner_boundary_refusal_pins_identifier_before_colon(prefix, diagnostic, expected_identifier):
    error = ReviewIsolationError(f"{prefix}:{diagnostic}")
    refusal = runner._attempt_boundary_refusal(error, stage="prepare")
    assert refusal == f"formal attempt filesystem boundary refused: prepare: {expected_identifier}"
    identifier = refusal.removeprefix("formal attempt filesystem boundary refused: prepare: ")
    if expected_identifier == "sandbox_probe_allow_failed":
        assert identifier == str(error).partition(":")[0] == "sandbox_probe_allow_failed"
    else:
        assert identifier == "ReviewIsolationError"
        assert prefix not in refusal
    assert diagnostic not in refusal


@pytest.mark.parametrize("error", [KeyError("private diagnostic"), TypeError("private diagnostic")])
def test_runner_preparation_error_redacts_exception_text(tmp_path, monkeypatch, error):
    def refuse(*args, **kwargs):
        raise error

    monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.prepare_attempt_boundary", refuse)
    with pytest.raises(AgentUnavailableError) as caught:
        runner.invoke("agy", "probe", cwd=tmp_path, tool_config={"review_id": "review"})
    assert str(caught.value) == f"formal attempt filesystem boundary refused: prepare: {type(error).__name__}"
    assert caught.value.__cause__ is error


def test_runner_reports_real_input_hash_refusal_before_provider_launch(world, tmp_path, monkeypatch):
    root, _ = world
    manifest = manifest_world(root, "plan")
    tc = attempt_config(root, tmp_path, manifest, "agy")
    (root / manifest["inputs"]["plan"]["path"]).write_text("Changed after the manifest was pinned.\n")

    def unexpected(*args, **kwargs):
        pytest.fail("input drift must refuse before provider planning or launch")

    monkeypatch.setattr(runner, "_load_adapter", unexpected)
    monkeypatch.setattr(runner, "_spawn_pipe_subprocess", unexpected)
    with pytest.raises(AgentUnavailableError) as caught:
        runner.invoke("agy", "probe", cwd=root, tool_config=tc)
    assert str(caught.value) == "formal attempt filesystem boundary refused: prepare: attempt_input_hash_mismatch"
    assert isinstance(caught.value.__cause__, ReviewIsolationError)


def test_cursor_attempt_refused_before_files_or_spawn(world, tmp_path):
    root, _ = world
    path = root / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest_world(root, "plan")))
    with pytest.raises(ValueError, match="Cursor is not admitted"):
        prepare_review_attempt("review", "attempt", path, "cursor", receipts_root=tmp_path / "receipts")
    assert not (tmp_path / "receipts").exists()


def test_claude_boundary_refuses_before_input_reads_or_provisioning(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("pending Claude adapter must refuse before boundary side effects")

    monkeypatch.setattr("scripts.agent_runtime.review_mcp.verify_review_attempt_paths", unexpected)
    monkeypatch.setattr(tempfile, "TemporaryDirectory", unexpected)
    monkeypatch.setattr("scripts.review.isolation.stage_engine_auth", unexpected)
    monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.SourcesConnection", unexpected)
    monkeypatch.setattr("scripts.agent_runtime.attempt_network.AttemptEgress", unexpected)
    with pytest.raises(ReviewIsolationError, match=r"^attempt_boundary_claude_adapter_pending$"):
        AttemptBoundary(agent="claude", tool_config={})


@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_runner_refuses_claude_attempt_before_adapter_or_spawn(world, tmp_path, monkeypatch, kind):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, kind), "claude")

    def unexpected(*args, **kwargs):
        pytest.fail("pending Claude adapter must refuse before adapter planning or spawn")

    monkeypatch.setattr(runner, "_load_adapter", unexpected)
    monkeypatch.setattr(subprocess, "Popen", unexpected)
    with pytest.raises(AgentUnavailableError, match="attempt_boundary_claude_adapter_pending"):
        runner.invoke("claude", "probe", cwd=root, tool_config=tc, hard_timeout=30)


def test_seat_cannot_read_other_attempt_through_host_http_projection(world, tmp_path):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy")

    class Projection(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"FORBIDDEN_OTHER_ATTEMPT_RETURN")

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Projection)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    boundary = AttemptBoundary(agent="agy", tool_config=tc)
    try:
        url = f"http://127.0.0.1:{server.server_port}/other-attempt-return"
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url, timeout=2) as control:
            assert control.read() == b"FORBIDDEN_OTHER_ATTEMPT_RETURN"
        script = (
            "import urllib.request,urllib.error\n"
            "opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))\n"
            "try:\n"
            f" opener.open({url!r},timeout=2).read()\n"
            "except urllib.error.URLError: print('DENIED:host_http')\n"
            "else: raise AssertionError('forbidden host HTTP projection readable')\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, text=True, timeout=10)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "DENIED:host_http"
    finally:
        boundary.cleanup()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("agent", ["agy", "codex"])
def test_runner_executes_attempt_boundary_and_cleans_after_parse(world, tmp_path, monkeypatch, agent):
    root, home = world
    forbidden = home / "previous-session.txt"
    forbidden.write_text("Forbidden")
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    observed = []

    class Adapter:
        default_model = "fixture-model"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, **kwargs):
            workspace = kwargs["cwd"]
            boundary = kwargs["tool_config"]["review_attempt_boundary"]
            observed.append(boundary)
            script = (
                "import pathlib,sys\n"
                f"assert not pathlib.Path({str(forbidden)!r}).exists()\n"
                "assert pathlib.Path('curriculum/l2-uk-en/lesson-plans/a1/sample.yaml').read_bytes()\n"
                "print(sys.stdin.read(),flush=True)\n"
            )
            return InvocationPlan(cmd=[sys.executable, "-c", script], cwd=workspace, stdin_payload="own return")

        def parse_response(self, **kwargs):
            assert observed[0].workspace.exists()  # extraction happens before cleanup
            return ParseResult(ok=kwargs["returncode"] == 0, response=kwargs["stdout"].strip())

        def liveness_signal_paths(self, plan):
            return ()

    monkeypatch.setattr(runner, "_load_adapter", lambda *args, **kwargs: Adapter())
    monkeypatch.setattr(runner, "has_headroom", lambda *args, **kwargs: (True, "fixture"))
    monkeypatch.setattr(runner, "write_record", lambda record: None)
    result = runner.invoke(agent, "probe", cwd=root, tool_config=tc, model="fixture-model", hard_timeout=30)
    assert result.ok and result.response == "own return"
    assert observed and not observed[0].workspace.exists()


@pytest.mark.parametrize("agent", ["agy", "codex"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
@pytest.mark.parametrize("review_access", ["isolated", "full"])
def test_real_adapter_uses_fresh_home_and_attempt_outputs(world, tmp_path, monkeypatch, agent, kind, review_access):
    from scripts.agent_runtime.adapters.agy import AgyAdapter
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    root, home = world
    tc = attempt_config(root, tmp_path, manifest_world(root, kind), agent, review_access=review_access)
    if review_access == "full":
        subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
        tc["review_cwd"] = str(root)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    try:
        adapter = {"agy": AgyAdapter, "codex": CodexAdapter}[agent]()
        if os.environ.get("LU_REVIEW_HOST_PROBES") != "1":
            # CI has no authenticated provider CLIs. Keep the real adapter
            # planning and sandbox seam, using a native executable fixture.
            monkeypatch.setattr(shutil, "which", lambda name: "/bin/true")
            monkeypatch.setattr(
                "scripts.agent_runtime.adapters.agy._require_background_wait_support", lambda binary: None
            )
        if agent == "agy":
            settings = json.loads(
                (Path(boundary.tool_config["agy_home_override"]) / ".gemini/antigravity-cli/settings.json").read_text()
            )["permissions"]
            assert [r for r in settings["allow"] if r.startswith("read_file(")] == [f"read_file({boundary.workspace})"]
            assert not any(r.startswith(("command(", "write_file(")) for r in settings["allow"])
            assert "command(*)" in settings["deny"] and "write_file(*)" in settings["deny"]
            monkeypatch.setattr(adapter, "_resolve_model_flag", lambda model: "gemini-3.8-flash-high")
        plan = adapter.build_invocation(
            prompt="probe",
            mode="read-only",
            cwd=boundary.workspace,
            model=None,
            task_id="boundary-probe",
            session_id=None,
            tool_config=boundary.tool_config,
            effort="high",
        )
        assert plan.cwd == boundary.workspace
        if agent == "agy":
            assert Path(plan.env_overrides["HOME"]).is_relative_to(boundary.write_root)
            assert plan.liveness_paths[0].is_relative_to(boundary.write_root)
        elif agent == "codex":
            assert Path(plan.env_overrides["CODEX_HOME"]).is_relative_to(boundary.write_root)
            assert plan.output_file.is_relative_to(boundary.write_root)
            assert "--dangerously-bypass-approvals-and-sandbox" in plan.cmd
            from scripts.agent_runtime.sources_read_only import sources_tool_sets
            from scripts.review.receipts.ledger import review_tools
            from tests.agent_runtime.test_sources_read_only import _server_config

            sources = tomllib.loads((Path(plan.env_overrides["CODEX_HOME"]) / "config.toml").read_text())[
                "mcp_servers"
            ]["sources"]
            sources.update(_server_config(plan.cmd))
            exposed = sources["enabled_tools"]
            assert set(exposed) == review_tools(review_access)
            assert set(sources["tools"]) == review_tools(review_access)
            assert "verify_words" in exposed
            assert not set(sources_tool_sets()[1]) & set(exposed)
        # Probe the actual installed executable and its runtime closure inside
        # the production wrapper, without starting a provider/model request.
        cmd, env = boundary.wrap([plan.cmd[0], "--version"], plan.env_overrides)
        probe = subprocess.run(cmd, cwd=plan.cwd, env=env, capture_output=True, text=True, timeout=30)
        assert probe.returncode == 0, probe.stderr
        assert probe.stdout.strip()
        assert env["HOME"] != str(home)
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("proxy_mode", ["normal", "cleared", "overridden"])
@pytest.mark.live_network  # Positive controls target this fixture on enumerated local interfaces only.
def test_namespace_escape_matrix_with_positive_controls(world, tmp_path, proxy_mode):
    from scripts.agent_runtime.attempt_network import host_addresses

    root, _ = world
    boundary = AttemptBoundary(
        agent="agy", tool_config=attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy")
    )
    listeners, peers, descriptors, threads = [], [], [], []
    socket_directory = tempfile.TemporaryDirectory(prefix="attempt-fixture-", dir="/tmp")
    sentinel = b"FORBIDDEN_SOCKET_SENTINEL"

    def serve(listener):
        while True:
            try:
                client, _ = listener.accept()
                with client:
                    client.sendall(sentinel)
            except OSError:
                return

    try:
        targets = []
        for address in host_addresses():
            if address.version == 6 and address.is_link_local:
                warnings.warn("Skipping IPv6 link-local address: interface scope unavailable", stacklevel=2)
                continue
            family = socket.AF_INET if address.version == 4 else socket.AF_INET6
            target = str(address)
            listener = socket.socket(family)
            try:
                if family == socket.AF_INET6:
                    listener.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                listener.bind((target, 0))
            except OSError as exc:
                listener.close()
                warnings.warn(f"Skipping IPv{address.version} address: bind failed (errno={exc.errno})", stacklevel=2)
                continue
            listener.listen()
            listeners.append(listener)
            thread = threading.Thread(target=serve, args=(listener,), daemon=True)
            thread.start()
            threads.append(thread)
            targets.append((family, (target, listener.getsockname()[1])))
            if family == socket.AF_INET:
                targets.append((socket.AF_INET6, (f"::ffff:{target}", listener.getsockname()[1])))
        assert targets, "No host addresses could be bound for positive controls"
        # Host abstract namespace and a neighboring attempt's filesystem socket.
        abstract = "\0attempt-fixture-" + str(os.getpid()) + "-" + proxy_mode
        neighbor = str(Path(socket_directory.name) / "neighbor.sock")
        for name in (abstract, neighbor):
            listener = socket.socket(socket.AF_UNIX)
            listener.bind(name)
            listener.listen()
            listeners.append(listener)
            thread = threading.Thread(target=serve, args=(listener,), daemon=True)
            thread.start()
            threads.append(thread)
            targets.append((socket.AF_UNIX, name))
        # Every target really serves outside the boundary, including the host's
        # interface addresses (never stored in public evidence).
        for family, address in targets:
            with socket.socket(family) as control:
                control.settimeout(2)
                control.connect(address)
                assert control.recv(1024) == sentinel
        forbidden_file = tmp_path / "inherited.txt"
        forbidden_file.write_bytes(sentinel)
        file_fd = os.open(forbidden_file, os.O_RDONLY)
        namespace_fd = os.open("/proc/self/ns/net", os.O_RDONLY)
        peer, other = socket.socketpair()
        peers.extend([peer, other])
        other.sendall(sentinel)
        # Seed high inheritable descriptors, then use the production runner seam
        # (Popen defaults to close_fds) rather than treating launch errors as denial.
        for index, original in enumerate((file_fd, namespace_fd, peer.fileno()), 100):
            os.dup2(original, index, inheritable=True)
            descriptors.append(index)
        os.close(file_fd)
        os.close(namespace_fd)
        parent_namespace = os.readlink("/proc/self/ns/net")
        script = (
            "import socket,os,pathlib,json\n"
            f"targets={[(int(family), address) for family, address in targets]!r}\n"
            f"mode={proxy_mode!r}\n"
            "if mode!='normal':\n"
            " for k in list(os.environ):\n"
            "  if k.lower().endswith('_proxy'): os.environ.pop(k)\n"
            " if mode=='overridden': os.environ['HTTPS_PROXY']='http://127.0.0.1:1'\n"
            "for family,address in targets:\n"
            " with socket.socket(family) as client:\n"
            "  client.settimeout(.5)\n"
            "  try: client.connect(address)\n"
            "  except OSError as e: print('DENIED:socket:'+str(e.errno))\n"
            "  else: raise AssertionError('host socket reachable')\n"
            f"assert os.readlink('/proc/self/ns/net')!={parent_namespace!r}\n"
            "assert not pathlib.Path('/sys/class/net').exists()\n"
            f"for fd in {descriptors!r}:\n"
            " try: os.fstat(fd)\n"
            " except OSError: print('DENIED:inherited_fd')\n"
            " else: raise AssertionError('inherited descriptor')\n"
            f"for name in {[str(forbidden_file), '/proc/self/root' + str(forbidden_file), f'/proc/{os.getpid()}/root' + str(forbidden_file), f'/proc/{os.getpid()}/fd/100', f'/proc/{os.getpid()}/ns/net']!r}:\n"
            " try: pathlib.Path(name).read_bytes()\n"
            " except OSError: print('DENIED:proc_or_root')\n"
            " else: raise AssertionError('host proc/root exposed')\n"
            "# DNS cannot provide an alternative route: even known numeric host\n"
            "# destinations were denied above; only the parent resolves egress.\n"
            "print('DENIED:sys_and_host_namespace')\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc, _, _ = runner._spawn_pipe_subprocess(cmd, cwd=boundary.workspace, env=env)
        stdout, stderr = proc.communicate(timeout=30)
        assert proc.returncode == 0, stderr
        assert len(stdout.splitlines()) == len(targets) + 3 + 5 + 1
        if isinstance(stdout, bytes):
            stdout = stdout.decode()
        assert all(line.startswith("DENIED:") for line in stdout.splitlines())
        assert "--unshare-net" in cmd and boundary.sandbox.network_allowed is False
    finally:
        for descriptor in descriptors:
            os.close(descriptor)
        for peer in peers:
            peer.close()
        for listener in listeners:
            listener.shutdown(socket.SHUT_RDWR)
            listener.close()
        for thread in threads:
            thread.join(2)
        boundary.cleanup()
        socket_directory.cleanup()


def test_proxy_crash_refuses_launch_and_never_shares_network(world, tmp_path):
    root, _ = world
    boundary = AttemptBoundary(
        agent="agy", tool_config=attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy")
    )
    try:
        cmd, env = boundary.wrap([sys.executable, "-c", "print('MUST_NOT_LAUNCH')"], {})
        boundary.egress.cleanup()
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 125
        assert result.stdout == "" and "attempt_forwarder_start_failed" in result.stderr
        assert "--unshare-net" in cmd
        with pytest.raises(ReviewIsolationError, match="egress_unavailable"):
            boundary.wrap([sys.executable, "-c", "print('MUST_NOT_LAUNCH')"], {})
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("agent,access", [("agy", "isolated"), ("agy", "full"), ("codex", "full"), ("claude", "full")])
@pytest.mark.parametrize("denial", ["hostname", "loopback", "mixed", "non_connect", "redirect", "allowed"])
def test_seat_proxy_denials_have_successful_oracles(world, tmp_path, monkeypatch, denial, agent, access):
    import asyncio
    import ssl

    from scripts.agent_runtime.attempt_network import load_allowlist

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent, review_access=access)
    tc.update(review_access=access, review_cwd=str(root))
    if access == "full":
        subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    allowed = sorted(load_allowlist(agent))[0]

    class Forbidden(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"FORBIDDEN_HTTP_SENTINEL")

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Forbidden)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    tls_server = None
    tls_thread = None
    try:
        control_url = f"http://127.0.0.1:{server.server_port}/"
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(control_url, timeout=2) as control:
            assert control.read() == b"FORBIDDEN_HTTP_SENTINEL"

        async def resolve(host):
            return ["8.8.8.8", "::ffff:127.0.0.1"] if denial == "mixed" else ["127.0.0.1"]

        monkeypatch.setattr(boundary.egress, "_resolve", resolve)
        url = "https://not-allowed.example/" if denial == "hostname" else f"https://{allowed}/"
        if denial in {"redirect", "allowed"}:
            # A provider-shaped TLS fixture redirects the native HTTP client
            # toward a forbidden host service; the redirect never reaches it.
            cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "1",
                    "-subj",
                    "/CN=provider.example",
                    "-keyout",
                    str(key),
                    "-out",
                    str(cert),
                ],
                capture_output=True,
                check=True,
                timeout=10,
            )

            class Redirect(Forbidden):
                def do_GET(self):
                    if denial == "allowed":
                        return super().do_GET()
                    self.send_response(302)
                    self.send_header("Location", f"https://127.0.0.1:{server.server_port}/forbidden")
                    self.end_headers()

            tls_server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.load_cert_chain(cert, key)
            tls_server.socket = context.wrap_socket(tls_server.socket, server_side=True)
            tls_thread = threading.Thread(target=tls_server.serve_forever, daemon=True)
            tls_thread.start()

            async def good_resolve(host):
                return ["8.8.8.8"]

            async def fixture_connect(addresses):
                return await asyncio.open_connection("127.0.0.1", tls_server.server_port)

            monkeypatch.setattr(boundary.egress, "_resolve", good_resolve)
            monkeypatch.setattr(boundary.egress, "_connect", fixture_connect)
        if denial == "non_connect":
            script = (
                "import socket,os,urllib.parse\n"
                "p=urllib.parse.urlsplit(os.environ['HTTPS_PROXY'])\n"
                "with socket.create_connection((p.hostname,p.port),timeout=2) as client:\n"
                " client.sendall(b'GET / HTTP/1.1\\r\\n\\r\\n')\n"
                " assert client.recv(1024).startswith(b'HTTP/1.1 403')\n"
                "print('DENIED:proxy_method')\n"
            )
        elif denial == "allowed":
            script = (
                "import urllib.request,ssl\n"
                f"assert urllib.request.urlopen({url!r},context=ssl._create_unverified_context(),timeout=3).read() == b'FORBIDDEN_HTTP_SENTINEL'\n"
                "print('ALLOWED:provider')\n"
            )
        else:
            script = (
                "import urllib.request,urllib.error,ssl\n"
                "context=ssl._create_unverified_context()\n"
                "context.minimum_version=ssl.TLSVersion.TLSv1_2\n"
                "try:\n"
                f" urllib.request.urlopen({url!r},context=context,timeout=3).read()\n"
                "except urllib.error.URLError as e:\n"
                " assert '403 Forbidden' in str(e),str(e)\n"
                " print('DENIED:proxy_target')\n"
                "else: raise AssertionError('forbidden destination exposed')\n"
            )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, text=True, timeout=15)
        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip().startswith("ALLOWED:" if denial == "allowed" else "DENIED:")
        if denial in {"redirect", "allowed"}:
            assert any(record["bytes"] > 0 for record in boundary.egress.records)
    finally:
        if tls_server is not None:
            tls_server.shutdown()
            tls_server.server_close()
            tls_thread.join(2)
        server.shutdown()
        server.server_close()
        thread.join(2)
        boundary.cleanup()


def test_namespace_and_forwarder_failure_have_no_fallback(world, tmp_path, monkeypatch):
    root, _ = world
    boundary = AttemptBoundary(
        agent="agy", tool_config=attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy")
    )
    try:
        cmd, env = boundary.wrap([sys.executable, "-c", "print('MUST_NOT_LAUNCH')"], {})
        boundary.forwarder.write_text("raise SystemExit(125)\n")
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 125 and result.stdout == ""
        assert "--unshare-net" in cmd

        def fail(**kwargs):
            assert kwargs["network_allowed"] is False
            raise ReviewIsolationError("sandbox_probe_allow_failed:fixture")

        monkeypatch.setattr("scripts.review.isolation.prepare_host_sandbox", fail)
        with pytest.raises(ReviewIsolationError, match="sandbox_probe_allow_failed"):
            boundary.wrap([sys.executable, "-c", "print('MUST_NOT_LAUNCH')"], {})
    finally:
        boundary.cleanup()


def test_linux_claude_auth_selects_only_fresh_token(world, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    _, home = world
    credential = home / ".claude" / ".credentials.json"
    credential.parent.mkdir()
    access = "fixture-access-" + "x" * 30
    refresh = "fixture-refresh-" + "y" * 30
    credential.write_text(
        json.dumps({"claudeAiOauth": {"accessToken": access, "refreshToken": refresh, "expiresAt": 4_102_444_800_000}})
    )
    credential.chmod(0o600)
    assert linux_claude_auth() == {"CLAUDE_CODE_OAUTH_TOKEN": access}
    credential.chmod(0o644)
    with pytest.raises(ReviewIsolationError, match="not_private"):
        linux_claude_auth()
    credential.chmod(0o600)
    credential.write_text(json.dumps({"claudeAiOauth": {"accessToken": access, "expiresAt": 0}}))
    with pytest.raises(ReviewIsolationError, match="expired"):
        linux_claude_auth()
    credential.write_text("not json")
    with pytest.raises(ReviewIsolationError, match="invalid"):
        linux_claude_auth()
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", access)
    assert linux_claude_auth() == {"CLAUDE_CODE_OAUTH_TOKEN": access}  # selected token reaches the private seat


# Fixture-only account identities; real ones live in private local configuration.
DEFAULT_ACCOUNT_UUID = "00000000-0000-4000-8000-00000000000a"
BOUND_ACCOUNT_UUID = "00000000-0000-4000-8000-00000000000b"
CLAUDE_AMBIENT_AUTH = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
ACCOUNT_ORG_UUIDS = {
    DEFAULT_ACCOUNT_UUID: "00000000-0000-4000-8000-0000000000a0",
    BOUND_ACCOUNT_UUID: "00000000-0000-4000-8000-0000000000b0",
}
# The organisation each fixture account's live profile reports (a consumer Max
# plan); a test replaces or deletes an entry to model another plan.
PROFILE_ORGANIZATIONS = {
    account: {"uuid": organization, "organization_type": "claude_max"}
    for account, organization in ACCOUNT_ORG_UUIDS.items()
}


def _private_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    path.chmod(0o600)


def _private_json(path: Path, data: object) -> None:
    _private_text(path, json.dumps(data))


# Committed synthetic Claude Code login files with obviously fake values.
_LOGIN_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "claude_login"


def _credentials(path: Path, token: str, *, plan: str | None = "max") -> None:
    """A login's credential file, filled in from the committed template.

    ``token`` is the fixture access token and ``plan`` the subscription type
    Claude Code stored with it (``None`` takes the template without one). As
    in a real login, the record carries inference scope, which the installed
    CLI needs before it reports a subscription login.
    """
    name = "credentials-with-plan" if plan is not None else "credentials-without-plan"
    template = _LOGIN_FIXTURES / f"{name}.template.json"
    _private_text(path, string.Template(template.read_text()).substitute(access_token=token, subscription_type=plan))


def _login_identity(account_uuid: str) -> dict:
    """The account record Claude Code keeps in a login's global config, with its organisation."""
    return {"accountUuid": account_uuid, "organizationUuid": ACCOUNT_ORG_UUIDS[account_uuid]}


def _machine_policy_text(relative: str, text: str) -> None:
    path = env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _machine_policy_link() -> None:
    root = env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR
    root.mkdir()
    (root / "managed-settings.json").symlink_to(root / "absent-target")


def _machine_policy_root_link() -> None:
    root = env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR
    root.with_name("machine-policy-target").mkdir()
    root.symlink_to(root.with_name("machine-policy-target"), target_is_directory=True)


# Machine-level policy Claude Code 2.1.300 reads on Linux, all under its one
# machine policy root (synthetic here; see _mock_selected_account_runtime):
# managed settings, which may name a policyHelper program whose output becomes
# policy, their drop-ins, managed MCP servers, a managed CLAUDE.md and managed
# rules. Presence alone refuses a labelled account (#10619), whatever it holds,
# and so does a root that is not a plain directory.
MACHINE_POLICY = {
    "managed_settings": lambda: _machine_policy_text("managed-settings.json", "{}"),
    "policy_helper": lambda: _machine_policy_text(
        "managed-settings.json", json.dumps({"policyHelper": {"path": "/fixture/policy-helper", "timeoutMs": 3000}})
    ),
    "drop_in": lambda: _machine_policy_text("managed-settings.d/50-fixture.json", "{}"),
    "drop_in_directory": lambda: (env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR / "managed-settings.d").mkdir(parents=True),
    "managed_mcp": lambda: _machine_policy_text("managed-mcp.json", json.dumps({"mcpServers": {}})),
    "managed_memory": lambda: _machine_policy_text("CLAUDE.md", "fixture\n"),
    "managed_rules": lambda: _machine_policy_text(".claude/rules/fixture.md", "fixture\n"),
    "dangling_link": _machine_policy_link,
    "root_is_a_file": lambda: env_sanitize._CLAUDE_MANAGED_SETTINGS_DIR.write_text("{}", encoding="utf-8"),
    "root_is_a_link": _machine_policy_root_link,
}


def _mock_selected_account_runtime(tmp_path, monkeypatch):
    """Model safe system ancestry without changing shared scratch permissions."""
    ancestors = {(p.stat().st_dev, p.stat().st_ino) for p in tmp_path.parents}
    fstat = os.fstat

    def checked_stat(fd):
        info = fstat(fd)
        if (info.st_dev, info.st_ino) in ancestors:
            fields = list(info)
            fields[0] &= ~0o022
            return os.stat_result(fields)
        return info

    monkeypatch.setattr(os, "fstat", checked_stat)
    # A synthetic machine policy root, absent unless a test writes policy there,
    # on a host that is not WSL unless a test says so (#10619).
    monkeypatch.setattr(env_sanitize, "_CLAUDE_MANAGED_SETTINGS_DIR", tmp_path / "machine-policy")
    monkeypatch.setattr(attempt_boundary, "_CLAUDE_PROC_VERSION", tmp_path / "proc-version")
    for name in ("WSL_DISTRO_NAME", "WSL_INTEROP"):
        monkeypatch.delenv(name, raising=False)
    calls = []
    identities = {}

    # A subclass, so urllib still finds the class attributes its default HTTPS
    # handler reads when another caller builds its first opener.
    class ProfileConnection(http.client.HTTPSConnection):
        def __init__(self, host, *, timeout):  # no socket is ever opened
            assert host == "api.anthropic.com" and timeout == 10

        def request(self, method, path, *, headers):
            assert method == "GET" and path == "/api/oauth/profile"
            self.selected = headers["Authorization"].removeprefix("Bearer ")
            calls.append(self.selected)

        def getresponse(self):
            account = identities[self.selected]
            profile = {"account": {"uuid": account}}
            if account in PROFILE_ORGANIZATIONS:
                profile["organization"] = PROFILE_ORGANIZATIONS[account]
            return SimpleNamespace(status=200, read=lambda _limit: json.dumps(profile).encode())

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPSConnection", ProfileConnection)
    return identities, calls


@pytest.fixture
def two_accounts(world, tmp_path, monkeypatch):
    """The default account in HOME and a second one under its own config directory."""
    _, home = world
    home.chmod(0o700)
    identities, calls = _mock_selected_account_runtime(tmp_path, monkeypatch)
    for key in (*CLAUDE_AMBIENT_AUTH, "CLAUDE_CONFIG_DIR"):
        monkeypatch.delenv(key, raising=False)
    accounts = SimpleNamespace(
        home=home,
        default_token="fixture-default-" + "d" * 30,
        bound_token="fixture-bound-" + "b" * 30,
        config_dir=tmp_path / "bound-config",
        binding=tmp_path / "private-config" / "claude_accounts.json",
    )
    identities.update({accounts.default_token: DEFAULT_ACCOUNT_UUID, accounts.bound_token: BOUND_ACCOUNT_UUID})
    accounts.profile_calls = calls
    _credentials(home / ".claude" / ".credentials.json", accounts.default_token)
    (home / ".claude").chmod(0o700)
    _private_json(home / ".claude.json", {"oauthAccount": {"accountUuid": DEFAULT_ACCOUNT_UUID}})
    accounts.config_dir.mkdir(mode=0o700)
    _credentials(accounts.config_dir / ".credentials.json", accounts.bound_token)
    _private_json(accounts.config_dir / ".claude.json", {"oauthAccount": _login_identity(BOUND_ACCOUNT_UUID)})
    _private_json(
        accounts.binding,
        {
            "schema_version": 1,
            "accounts": {"b": {"config_dir": str(accounts.config_dir), "account_uuid": BOUND_ACCOUNT_UUID}},
        },
    )
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(accounts.binding))
    return accounts


def test_selected_material_must_match_bound_identity(two_accounts):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    _credentials(two_accounts.config_dir / ".credentials.json", two_accounts.default_token)
    with pytest.raises(ReviewIsolationError, match=r"^claude_account_unverified$"):
        linux_claude_auth("b")


def test_selected_directory_swap_cannot_redirect_use(two_accounts, monkeypatch):
    from scripts.agent_runtime import attempt_boundary as module

    # The selected directory's global config is read through the held descriptor (#10619).
    original = module._checked_login_global_config
    swapped = False

    def swap_after_login_read(directory, account_uuid):
        nonlocal swapped
        result = original(directory, account_uuid)
        if not swapped:
            swapped = True
            two_accounts.config_dir.rename(two_accounts.config_dir.with_name("checked-config"))
            two_accounts.config_dir.symlink_to(two_accounts.home / ".claude")
        return result

    monkeypatch.setattr(module, "_checked_login_global_config", swap_after_login_read)
    assert module.linux_claude_auth("b") == {"CLAUDE_CODE_OAUTH_TOKEN": two_accounts.bound_token}
    assert swapped


@pytest.mark.parametrize(
    "case",
    [
        "symlink_ancestor",
        "group_writable_ancestor",
        "world_writable_ancestor",
        "group_writable_selected",
        "world_writable_selected",
    ],
)
def test_selected_directory_rejects_unsafe_ancestry(two_accounts, case):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    if case.endswith("selected"):
        two_accounts.config_dir.chmod(0o770 if case.startswith("group") else 0o707)
    else:
        parent = two_accounts.config_dir.parent / "ancestor"
        parent.mkdir(mode=0o700)
        two_accounts.config_dir.rename(parent / "bound-config")
        if case == "symlink_ancestor":
            link = parent.with_name("linked-ancestor")
            link.symlink_to(parent)
            selected = link / "bound-config"
        else:
            parent.chmod(0o770 if case.startswith("group") else 0o707)
            selected = parent / "bound-config"
        _private_json(
            two_accounts.binding,
            {"schema_version": 1, "accounts": {"b": {"config_dir": str(selected), "account_uuid": BOUND_ACCOUNT_UUID}}},
        )
    with pytest.raises(ReviewIsolationError, match=r"^claude_account_config_dir_not_private$"):
        linux_claude_auth("b")


def test_selection_path_loop_is_a_value_free_refusal(two_accounts, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES, linux_claude_auth

    loop = two_accounts.config_dir.parent / "loop"
    loop.symlink_to(loop)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(loop))
    with pytest.raises(ReviewIsolationError) as refused:
        linux_claude_auth("b")
    assert str(refused.value) in CLAUDE_ACCOUNT_REFUSAL_CODES
    assert str(loop) not in str(refused.value)


@pytest.mark.parametrize(
    "error,code",
    [
        (errno.ENOENT, "claude_account_config_dir_missing"),
        (errno.ENOTDIR, "claude_account_config_dir_not_private"),
        (errno.ELOOP, "claude_account_config_dir_not_private"),
        (errno.EACCES, "claude_account_config_dir_unavailable"),
        (errno.ENAMETOOLONG, "claude_account_config_dir_unavailable"),
    ],
)
def test_selected_path_errors_are_sanitized(two_accounts, monkeypatch, error, code):
    import traceback

    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    original = os.open

    def fail_selected(path, *args, **kwargs):
        if path == two_accounts.config_dir.name:
            raise OSError(error, "fixture-private-detail", str(two_accounts.config_dir))
        return original(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", fail_selected)
    with pytest.raises(ReviewIsolationError) as refused:
        linux_claude_auth("b")
    assert str(refused.value) == code
    rendered = "".join(traceback.format_exception(refused.value))
    assert "fixture-private-detail" not in rendered
    assert str(two_accounts.config_dir) not in rendered


@pytest.mark.parametrize(
    "case",
    [
        "offline",
        "unauthorized",
        "redirect",
        "oversized",
        "invalid_json",
        "missing_identity",
        "wrong_identity_type",
        "duplicate_identity",
    ],
)
def test_selected_identity_failure_is_value_free(two_accounts, monkeypatch, case):
    import traceback

    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    class FailedProfile:
        def __init__(self, *_args, **_kwargs):
            if case == "offline":
                raise OSError("fixture-private-detail")

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            bodies = {
                "oversized": b"x" * 65537,
                "invalid_json": b"fixture-private-detail",
                "missing_identity": b"{}",
                "wrong_identity_type": b'{"account":{"uuid":1}}',
                "duplicate_identity": b'{"account":{},"account":{}}',
            }
            return SimpleNamespace(
                status={"unauthorized": 401, "redirect": 302}.get(case, 200),
                read=lambda _limit: bodies.get(case, b"{}"),
            )

        def close(self):
            pass

    monkeypatch.setattr(http.client, "HTTPSConnection", FailedProfile)
    with pytest.raises(ReviewIsolationError, match=r"^claude_account_identity_unavailable$") as refused:
        linux_claude_auth("b")
    rendered = "".join(traceback.format_exception(refused.value))
    for value in ("fixture-private-detail", two_accounts.bound_token, BOUND_ACCOUNT_UUID):
        assert value not in rendered


def test_selected_material_is_not_reopened_after_identity_check(two_accounts, monkeypatch):
    from scripts.agent_runtime import attempt_boundary as module

    original = module._claude_selected_identity

    def swap_after_identity(token):
        identity = original(token)
        _credentials(two_accounts.config_dir / ".credentials.json", two_accounts.default_token)
        return identity

    monkeypatch.setattr(module, "_claude_selected_identity", swap_after_identity)
    assert module.linux_claude_auth("b") == {"CLAUDE_CODE_OAUTH_TOKEN": two_accounts.bound_token}
    assert two_accounts.profile_calls == [two_accounts.bound_token]


def test_complete_preflight_rechecks_selected_state_at_use(two_accounts):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth, verify_claude_account

    assert verify_claude_account("b").label == "b"
    _credentials(two_accounts.config_dir / ".credentials.json", two_accounts.default_token)
    with pytest.raises(ReviewIsolationError, match=r"^claude_account_unverified$"):
        linux_claude_auth("b")


@pytest.mark.parametrize("organization_type", ["claude_team", "claude_enterprise", None])
def test_sealed_attempt_refuses_an_account_outside_the_consumer_plans(two_accounts, monkeypatch, organization_type):
    """Held-out (#10619): a labelled account is admitted only on a consumer plan, at the sealed boundary too."""
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    organization = {"uuid": ACCOUNT_ORG_UUIDS[BOUND_ACCOUNT_UUID], "organization_type": organization_type}
    monkeypatch.setitem(PROFILE_ORGANIZATIONS, BOUND_ACCOUNT_UUID, organization)

    with pytest.raises(ReviewIsolationError, match=r"^claude_account_plan_unsupported$"):
        linux_claude_auth("b")


def test_default_claude_account_keeps_legacy_selection(two_accounts, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    # The default label never consults the private binding, even when it is absent.
    monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", str(two_accounts.binding.with_name("absent.json")))
    expected = {"CLAUDE_CODE_OAUTH_TOKEN": two_accounts.default_token}
    assert linux_claude_auth() == linux_claude_auth(None) == linux_claude_auth("a") == expected
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "e" * 30)
    assert linux_claude_auth("a") == linux_claude_auth() == {"CLAUDE_CODE_OAUTH_TOKEN": "fixture-ambient-" + "e" * 30}


def test_second_claude_account_reads_only_its_bound_credential(two_accounts, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    assert linux_claude_auth("b") == {"CLAUDE_CODE_OAUTH_TOKEN": two_accounts.bound_token}
    # Naming the same directory ambiently is not a conflict.
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(two_accounts.config_dir))
    assert linux_claude_auth("b") == {"CLAUDE_CODE_OAUTH_TOKEN": two_accounts.bound_token}


@pytest.mark.parametrize("label", ["c", "B", "", " b", "a\n", 1])
def test_unknown_claude_account_label_is_refused(two_accounts, label):
    """AC-01: base code has no label parameter (TypeError); the label is refused with its typed code."""
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    with pytest.raises(ReviewIsolationError) as refused:
        linux_claude_auth(label)
    assert str(refused.value) == "claude_account_unknown"


def _conflict(accounts: SimpleNamespace, monkeypatch, case: str) -> None:
    config, binding = accounts.config_dir, accounts.binding
    entry = {"config_dir": str(config), "account_uuid": BOUND_ACCOUNT_UUID}
    if case in CLAUDE_AMBIENT_AUTH:
        monkeypatch.setenv(case, "fixture-ambient-" + "e" * 30)
    elif case == "ambient_config_dir":
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(accounts.home / ".claude"))
    elif case == "binding_absent":
        binding.unlink()
    elif case == "binding_disabled":
        monkeypatch.setenv("LU_CLAUDE_ACCOUNTS_FILE", "")
    elif case == "binding_shared":
        binding.chmod(0o640)
    elif case == "binding_symlink":
        target = binding.with_name("target.json")
        binding.rename(target)
        binding.symlink_to(target)
    elif case == "binding_without_label":
        _private_json(binding, {"schema_version": 1, "accounts": {}})
    elif case == "binding_for_default":
        _private_json(binding, {"schema_version": 1, "accounts": {"a": entry, "b": entry}})
    elif case == "binding_duplicate_key":
        binding.write_text(f'{{"schema_version": 1, "accounts": {{}}, "accounts": {{"b": {json.dumps(entry)}}}}}')
    elif case == "binding_relative_dir":
        _private_json(binding, {"schema_version": 1, "accounts": {"b": {**entry, "config_dir": "bound-config"}}})
    elif case == "binding_extra_key":
        _private_json(binding, {"schema_version": 1, "accounts": {"b": {**entry, "token": "x"}}})
    elif case == "binding_schema":
        _private_json(binding, {"schema_version": True, "accounts": {"b": entry}})
    elif case == "config_dir_absent":
        shutil.rmtree(config)
    elif case == "config_dir_symlink":
        moved = config.with_name("moved-config")
        config.rename(moved)
        config.symlink_to(moved)
    elif case == "config_is_default_dir":
        _private_json(
            binding, {"schema_version": 1, "accounts": {"b": {**entry, "config_dir": str(accounts.home / ".claude")}}}
        )
    elif case == "default_holds_bound_account":
        _private_json(accounts.home / ".claude.json", {"oauthAccount": {"accountUuid": BOUND_ACCOUNT_UUID}})
    elif case == "other_account_logged_in":
        _private_json(config / ".claude.json", {"oauthAccount": {"accountUuid": DEFAULT_ACCOUNT_UUID}})
    elif case == "login_record_absent":
        (config / ".claude.json").unlink()
    elif case == "credentials_absent":
        (config / ".credentials.json").unlink()
    else:
        raise AssertionError(case)


@pytest.mark.parametrize(
    "case,code",
    [
        *((key, "claude_account_ambient_conflict") for key in CLAUDE_AMBIENT_AUTH),
        ("ambient_config_dir", "claude_account_ambient_conflict"),
        ("binding_absent", "claude_account_binding_missing"),
        ("binding_disabled", "claude_account_binding_missing"),
        ("binding_shared", "claude_account_binding_not_private"),
        ("binding_symlink", "claude_account_binding_unavailable"),
        ("binding_without_label", "claude_account_binding_missing"),
        ("binding_for_default", "claude_account_binding_invalid"),
        ("binding_duplicate_key", "claude_account_binding_invalid"),
        ("binding_relative_dir", "claude_account_binding_invalid"),
        ("binding_extra_key", "claude_account_binding_invalid"),
        ("binding_schema", "claude_account_binding_invalid"),
        ("config_dir_absent", "claude_account_config_dir_missing"),
        ("config_dir_symlink", "claude_account_config_dir_not_private"),
        ("config_is_default_dir", "claude_account_binding_is_default"),
        ("default_holds_bound_account", "claude_account_binding_is_default"),
        ("other_account_logged_in", "claude_account_unverified"),
        ("login_record_absent", "claude_account_unverified"),
        ("credentials_absent", "claude_account_credentials_missing"),
    ],
)
def test_second_claude_account_refuses_conflicting_sources(two_accounts, monkeypatch, case, code):
    """AC-01: each conflicting or unverifiable source is refused by code alone, before any token is returned."""
    from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES, linux_claude_auth

    assert linux_claude_auth("b")  # positive control: the unchanged fixture authenticates
    _conflict(two_accounts, monkeypatch, case)
    with pytest.raises(ReviewIsolationError) as refused:
        linux_claude_auth("b")
    assert str(refused.value) == code and code in CLAUDE_ACCOUNT_REFUSAL_CODES
    rendered = repr(refused.value) + str(refused.value.__cause__) + str(refused.value.__context__)
    for value in (
        two_accounts.bound_token,
        two_accounts.default_token,
        BOUND_ACCOUNT_UUID,
        str(two_accounts.config_dir),
    ):
        assert value not in rendered


@pytest.mark.parametrize("entry", sorted(MACHINE_POLICY))
def test_second_claude_account_refuses_a_host_with_machine_policy(two_accounts, entry):
    """Held-out (#10619): any machine policy source refuses the labelled account, at a sealed attempt too.

    On f8dce2b219 every case returned the bound token.
    """
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    assert linux_claude_auth("b")  # positive control: no machine policy
    two_accounts.profile_calls.clear()
    MACHINE_POLICY[entry]()

    with pytest.raises(ReviewIsolationError, match=r"^claude_account_machine_policy_present$"):
        linux_claude_auth("b")
    assert two_accounts.profile_calls == []


@pytest.mark.parametrize("marker", ["WSL_DISTRO_NAME", "WSL_INTEROP", "Microsoft", "WSL2"])
def test_second_claude_account_refuses_wsl(two_accounts, monkeypatch, tmp_path, marker):
    """Held-out (#10619): under WSL Claude Code also reads Windows machine policy, which is not enumerable here.

    WSL is what the CLI takes it for: either variable set, or a kernel string naming it.
    """
    from scripts.agent_runtime.attempt_boundary import linux_claude_auth

    assert linux_claude_auth("b")  # positive control: a plain Linux kernel string
    (tmp_path / "proc-version").write_text("Linux version 6.0.0-fixture\n", encoding="utf-8")
    assert linux_claude_auth("b")
    two_accounts.profile_calls.clear()
    if marker.startswith("WSL_"):
        monkeypatch.setenv(marker, "fixture")
    else:
        (tmp_path / "proc-version").write_text(f"Linux version 6.0.0-fixture-{marker}-standard\n", encoding="utf-8")

    with pytest.raises(ReviewIsolationError, match=r"^claude_account_platform_unsupported$"):
        linux_claude_auth("b")
    assert two_accounts.profile_calls == []


def test_attempt_boundary_authenticates_claude_seat_as_the_labelled_account(world, tmp_path, two_accounts, monkeypatch):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "claude", review_access="full")
    tc.update(review_cwd=str(root), claude_account="b")
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    boundary = AttemptBoundary(agent="claude", tool_config=tc)
    try:
        assert boundary.env["CLAUDE_CODE_OAUTH_TOKEN"] == two_accounts.bound_token
        # Sealing is unchanged: a disposable home, no host config directory.
        assert Path(boundary.env["HOME"]).is_relative_to(boundary.write_root)
        assert "CLAUDE_CONFIG_DIR" not in boundary.env
    finally:
        boundary.cleanup()
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "fixture-ambient-" + "e" * 30)
    with pytest.raises(ReviewIsolationError, match=r"^claude_account_ambient_conflict$"):
        AttemptBoundary(agent="claude", tool_config=tc)


@pytest.mark.parametrize("agent", ["codex", "agy"])
def test_sandboxed_seat_swap_is_refused_by_parent(world, tmp_path, monkeypatch, agent):
    """Reproduce B1/B1b through the real sandbox and runner parse boundary."""
    from scripts.agent_runtime.adapters import agy as agy_module
    from scripts.agent_runtime.adapters.agy import AgyAdapter
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    root, home = world
    forbidden = home / "forbidden.jsonl"
    sentinel = "FORBIDDEN_PARENT_READ_SENTINEL"
    forbidden.write_text(json.dumps({"type": "USER_INPUT", "content": sentinel}) + "\n")
    assert sentinel in forbidden.read_text()  # outside-boundary positive control
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    observed = []
    parsed = []
    conversation_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    real_adapter = {"codex": CodexAdapter, "agy": AgyAdapter}[agent]()

    class SwapAdapter:
        default_model = "fixture-model"
        supported_modes = frozenset({"read-only"})

        def build_invocation(self, **kwargs):
            attempt = kwargs["tool_config"]["review_attempt_boundary"]
            observed.append(attempt)
            plan = real_adapter.build_invocation(**{**kwargs, "model": real_adapter.default_model})
            assert plan.metadata["parent_read_root"] == str(attempt.write_root)
            app_data = Path(plan.env_overrides.get("AGY_APP_DATA_DIR", attempt.write_root / "app-data"))
            output = plan.output_file
            transcript = agy_module._brain_transcript_path(app_data, conversation_id)
            target = output if agent == "codex" else transcript
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("own return")
            if agent == "agy":
                assert plan.metadata["log_read_root"] == str(attempt.write_root)
                log = Path(plan.env_overrides[agy_module._AGY_LOG_ENV])
                log.write_text(f"Created conversation {conversation_id}\n")
            script = (
                "import pathlib\n"
                f"forbidden=pathlib.Path({str(forbidden)!r})\n"
                "try: forbidden.read_bytes()\n"
                "except OSError: print('DENIED:direct-host-read',flush=True)\n"
                "else: raise AssertionError('host file readable')\n"
                f"target=pathlib.Path({str(target)!r})\n"
                "target.unlink()\n"
                "target.symlink_to(forbidden)\n"
                "print('SWAPPED:seat-name',flush=True)\n"
            )
            return replace(plan, cmd=[sys.executable, "-c", script], stdin_payload=None)

        def parse_response(self, **kwargs):
            assert kwargs["returncode"] == 0
            assert kwargs["stdout"].splitlines() == ["DENIED:direct-host-read", "SWAPPED:seat-name"]
            parsed.append(True)
            return real_adapter.parse_response(**kwargs)

        def liveness_signal_paths(self, plan):
            return ()

    monkeypatch.setattr(runner, "_load_adapter", lambda *a, **k: SwapAdapter())
    monkeypatch.setattr(runner, "has_headroom", lambda *a, **k: (True, "fixture"))
    monkeypatch.setattr(runner, "write_record", lambda record: None)
    result = runner.invoke(agent, "probe", cwd=root, tool_config=tc, model="fixture-model", hard_timeout=30)
    assert parsed and not result.ok and result.response == ""
    assert result.stderr_excerpt == "attempt_read_unsafe_path"
    assert sentinel not in repr(result)
    assert observed and not observed[0].workspace.exists()


# The fleet-wide default account file (#10619 PR1c): read once at dispatch, fail closed.
def _default_file(tmp_path: Path, monkeypatch, content: bytes, *, mode: int = 0o600) -> Path:
    path = tmp_path / "operator-config" / "claude-default-account"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(content)
    path.chmod(mode)
    monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", str(path))
    return path


@pytest.mark.parametrize(
    "content,label",
    [(b"b", "b"), (b"b\n", "b"), (b"  a\r\n", "a"), (b"\tb \n\n", "b"), (b"", None), (b" \n", None)],
)
def test_default_account_file_names_one_label_or_none(tmp_path, monkeypatch, content, label):
    from scripts.agent_runtime.attempt_boundary import read_claude_default_account

    _default_file(tmp_path, monkeypatch, content)
    assert read_claude_default_account() == label


def test_default_account_file_may_be_readable_by_others(tmp_path, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import read_claude_default_account

    _default_file(tmp_path, monkeypatch, b"b\n", mode=0o644)
    assert read_claude_default_account() == "b"


def test_default_account_file_lives_in_the_user_config_directory(tmp_path, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import claude_default_account_file, read_claude_default_account

    monkeypatch.delenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    expected = tmp_path / "xdg" / "learn-ukrainian" / "claude-default-account"
    assert claude_default_account_file() == expected
    assert read_claude_default_account() is None  # absent
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    assert claude_default_account_file() == tmp_path / "home" / ".config" / "learn-ukrainian" / "claude-default-account"
    monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", "")
    assert claude_default_account_file() is None


def test_dispatch_resolution_prefers_explicit_then_file_then_builtin(tmp_path, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import ClaudeAccountRefused, resolve_dispatch_claude_account

    monkeypatch.setenv("LU_CLAUDE_DEFAULT_ACCOUNT_FILE", str(tmp_path / "absent"))
    assert resolve_dispatch_claude_account(None) == ("a", "builtin")
    path = _default_file(tmp_path, monkeypatch, b"b\n")
    assert resolve_dispatch_claude_account(None) == ("b", "default-file")
    assert resolve_dispatch_claude_account("a") == ("a", "explicit")
    path.write_bytes(b"c")
    assert resolve_dispatch_claude_account("b") == ("b", "explicit")  # the file is not read
    with pytest.raises(ClaudeAccountRefused) as refused:
        resolve_dispatch_claude_account(None)
    assert refused.value.code == "claude_account_default_file_invalid"
    with pytest.raises(ClaudeAccountRefused) as refused:
        resolve_dispatch_claude_account("c")
    assert refused.value.code == "claude_account_unknown"


def test_default_file_refusal_names_no_value_or_location(tmp_path, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import ClaudeAccountRefused, read_claude_default_account

    path = _default_file(tmp_path, monkeypatch, b"fixture-secretish-content\n")
    with pytest.raises(ClaudeAccountRefused) as refused:
        read_claude_default_account()
    rendered = (
        repr(refused.value) + str(refused.value) + repr(refused.value.__cause__) + repr(refused.value.__context__)
    )
    assert "fixture-secretish" not in rendered
    assert str(path) not in rendered


def test_new_default_file_and_record_codes_are_registered():
    from scripts.agent_runtime.attempt_boundary import CLAUDE_ACCOUNT_REFUSAL_CODES

    assert {
        "claude_account_record_conflict",
        "claude_account_forward_unsupported",
        *(
            f"claude_account_default_file_{failure}"
            for failure in ("unavailable", "not_private", "oversized", "invalid")
        ),
    } <= CLAUDE_ACCOUNT_REFUSAL_CODES


def test_sealed_attempt_selection_records_a_verified_receipt(two_accounts):
    """The sealed boundary's verified selection of the bound credential is this run's receipt."""
    from scripts.agent_runtime.attempt_boundary import (
        claude_account_auth_receipt,
        linux_claude_auth,
        reset_claude_account_receipts,
    )

    reset_claude_account_receipts()
    assert claude_account_auth_receipt("b", source="explicit")["verified"] is False
    linux_claude_auth("b")
    assert claude_account_auth_receipt("b", source="explicit") == {
        "label": "b",
        "source": "explicit",
        "method": "bound_account_token",
        "verified": True,
    }
    reset_claude_account_receipts()
    assert claude_account_auth_receipt("b", source="explicit")["verified"] is False


def test_receipt_is_shared_by_both_import_names_of_the_binding_module():
    """The worker imports ``scripts.agent_runtime``; the runner loads the same files as ``agent_runtime``."""
    import agent_runtime.attempt_boundary as short_name
    import scripts.agent_runtime.attempt_boundary as canonical

    canonical.reset_claude_account_receipts()
    short_name.note_claude_account_verified("b", "subscription_login")
    assert canonical.claude_account_auth_receipt("b", source="default-file")["verified"] is True
    short_name.reset_claude_account_receipts()
    assert canonical.claude_account_auth_receipt("b", source="default-file")["verified"] is False


def test_receipt_carries_only_fixed_vocabulary():
    from scripts.agent_runtime.attempt_boundary import (
        claude_account_auth_receipt,
        note_claude_account_verified,
        reset_claude_account_receipts,
    )

    reset_claude_account_receipts()
    with pytest.raises(AssertionError):
        note_claude_account_verified("b", "fixture-token-value")
    with pytest.raises(AssertionError):
        note_claude_account_verified("a", "subscription_login")
    assert claude_account_auth_receipt("a", source="not-a-source") == {
        "label": "a",
        "source": None,
        "method": "host_login",
        "verified": False,
    }
