"""Subprocess evidence for the formal-attempt launch boundary (#9251)."""

from __future__ import annotations

import copy
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import threading
import tomllib
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime import runner
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
        paths.update({
            "lessons_lock": f"{state}/lessons.lock.yaml",
            "lesson": "site/src/content/docs/a1/sample/1.mdx",
            "provenance": f"{state}/lesson-1.provenance.yaml",
            "gate_report": f"{state}/lesson-1.gates.yaml",
            "style_card": "docs/style-cards/a1.md",
        })
    else:
        paths.update({
            "requirements": "docs/epics/fresh-build-requirements.md",
            "arc": f"{plans}/_arc.yaml",
            "arc_source": "docs/epics/fresh-build-a1-arc.md",
            "scope": f"{plans}/_scope/sample.yaml",
            "grammar": f"{plans}/_grammar.yaml",
            "validate_report": f"{state}/plan-validate.report.json",
            "pack_verify_report": f"{state}/pack-verify.report.json",
        })

    def pin(name: str) -> dict:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Authorized current input.\n")
        return {"path": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    doc = {
        "manifest_schema": 1, "kind": "lesson" if lesson else "plan", "level": "a1", "slug": "sample",
        "inputs": {name: pin(path) for name, path in paths.items()},
        "learner_state": {"sha256": "a" * 64, "source": "planned_state"},
    }
    if lesson:
        doc.update({
            "lesson": 1, "lesson_kind": "lesson", "recap": False, "review_eligible": True, "blocked_by": [],
            "lesson_lock_entry": {"path": paths["lesson"], "lesson": 1, "entry_sha256": "a" * 64},
            "module_digest": pin(f"{state}/digest-upto-1.yaml"), "digest_generator_version": "1",
            "upstream_lessons": [], "previous_attempt": None, "diff": None,
        })
        doc["inputs"]["activity_data"] = []
        if kind == "rereview":
            doc["previous_attempt"] = {
                "attempt_id": "previous", "review": pin(f"{state}/lesson-1.review.previous.yaml"),
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


def attempt_config(root: Path, tmp_path: Path, manifest: dict, agent: str) -> dict:
    path = root / "attempt.yaml"
    path.write_text(yaml.safe_dump(manifest))
    plan = prepare_review_attempt("review", "current", path, agent, receipts_root=tmp_path / "receipts")
    return {
        **plan.adapter_options, "review_id": "review", "attempt_id": "current", "review_manifest": str(path),
        "review_input_root": str(root),
    }


@pytest.mark.parametrize("agent", ["agy", "codex", "claude"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_subprocess_forbidden_read_matrix(world, tmp_path, agent, kind):
    root, old_home = world
    manifest = manifest_world(root, kind)
    forbidden_names = [
        "batch_state/review-receipts/review/other.jsonl", "batch_state/returns/other.yaml",
        "batch_state/task.json", "scripts/review/record.py", "scripts/review/receipts/ledger.py",
        "scripts/delegate.py", "earlier-edition.yaml",
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
    subprocess.run([
        "git", "-C", str(root), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-qm", "Fixture",
    ], check=True, timeout=30)
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
        cmd, env = boundary.wrap(["/bin/sh", "-c", "echo corrupt > curriculum/l2-uk-en/lesson-plans/a1/sample.yaml"], {})
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


@pytest.mark.parametrize("agent", ["agy", "codex", "claude"])
def test_sources_proxy_records_receipts_outside_seat(world, tmp_path, agent):
    root, _ = world
    doc = manifest_world(root, "plan")
    tc = attempt_config(root, tmp_path, doc, agent)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    try:
        if agent == "codex":
            parsed = tomllib.loads((Path(boundary.tool_config["codex_home_override"]) / "config.toml").read_text())
            assert len(parsed["mcp_servers"]["sources"]["args"]) == 2
        proxy = json.loads(Path(boundary.tool_config["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "boundary-probe", "version": "1"},
            }},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "verify_words", "arguments": {"words": []}}},
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
        ledger = Path(json.loads(Path(tc["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]["env"]["LU_REVIEW_LEDGER_PATH"])
        assert ledger.read_bytes(), proc.stdout
        # The same boundary cannot read even its own runtime ledger.
        cmd, env = boundary.wrap(["/bin/cat", str(ledger)], {})
        assert subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, timeout=30).returncode != 0
    finally:
        processes = boundary.connection.processes
        boundary.cleanup()
    assert processes and all(p.poll() is not None for p in processes)


def test_runner_requires_boundary_and_preserves_nonattempt_behavior(monkeypatch):
    assert prepare_attempt_boundary("agy", "read-only", None, {}) is None
    for tc, mode, session in [
        ({"review_id": "review"}, "read-only", None),
        ({"attempt_id": "current", "strict_mcp_config": True}, "workspace-write", None),
        ({"review_id": "review", "strict_mcp_config": True}, "read-only", "previous"),
    ]:
        with pytest.raises(AgentUnavailableError, match="filesystem boundary refused"):
            runner.invoke("agy", "probe", tool_config=tc, mode=mode, session_id=session)


def test_cursor_attempt_refused_before_files_or_spawn(world, tmp_path):
    root, _ = world
    path = root / "manifest.yaml"
    path.write_text(yaml.safe_dump(manifest_world(root, "plan")))
    with pytest.raises(ValueError, match="Cursor is not admitted"):
        prepare_review_attempt("review", "attempt", path, "cursor", receipts_root=tmp_path / "receipts")
    assert not (tmp_path / "receipts").exists()


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
        script = (
            "import urllib.request\n"
            f"print(urllib.request.urlopen({url!r},timeout=2).read().decode())\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", script], {})
        proc = subprocess.run(cmd, cwd=boundary.workspace, env=env, capture_output=True, text=True, timeout=10)
        assert proc.returncode != 0, "forbidden host HTTP return projection was readable inside the launch boundary"
    finally:
        boundary.cleanup()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("agent", ["agy", "codex", "claude"])
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


@pytest.mark.parametrize("agent", ["agy", "codex", "claude"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_real_adapter_uses_fresh_home_and_attempt_outputs(world, tmp_path, monkeypatch, agent, kind):
    from scripts.agent_runtime.adapters.agy import AgyAdapter
    from scripts.agent_runtime.adapters.claude import ClaudeAdapter
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    root, home = world
    tc = attempt_config(root, tmp_path, manifest_world(root, kind), agent)
    boundary = AttemptBoundary(agent=agent, tool_config=tc)
    try:
        adapter = {"agy": AgyAdapter, "claude": ClaudeAdapter, "codex": CodexAdapter}[agent]()
        if os.environ.get("LU_REVIEW_HOST_PROBES") != "1":
            # CI has no authenticated provider CLIs. Keep the real adapter
            # planning and sandbox seam, using a native executable fixture.
            monkeypatch.setattr(shutil, "which", lambda name: "/bin/true")
            monkeypatch.setattr("scripts.agent_runtime.adapters.agy._require_background_wait_support", lambda binary: None)
            monkeypatch.setattr("scripts.agent_runtime.adapters.claude._default_claude_bin", lambda: "/bin/true")
            monkeypatch.setattr("scripts.agent_runtime.adapters.claude._ensure_supported_claude_cli_version",
                                lambda prefix: (2, 1, 285))
        if agent == "agy":
            monkeypatch.setattr(adapter, "_resolve_model_flag", lambda model: "gemini-3.8-flash-high")
        plan = adapter.build_invocation(prompt="probe", mode="read-only", cwd=boundary.workspace,
                                        model=None, task_id="boundary-probe", session_id=None,
                                        tool_config=boundary.tool_config, effort="high")
        assert plan.cwd == boundary.workspace
        if agent == "agy":
            assert Path(plan.env_overrides["HOME"]).is_relative_to(boundary.write_root)
            assert plan.liveness_paths[0].is_relative_to(boundary.write_root)
        elif agent == "codex":
            assert Path(plan.env_overrides["CODEX_HOME"]).is_relative_to(boundary.write_root)
            assert plan.output_file.is_relative_to(boundary.write_root)
            assert "--dangerously-bypass-approvals-and-sandbox" in plan.cmd
        else:
            assert "--bare" in plan.cmd and "--setting-sources" in plan.cmd
            assert "--strict-mcp-config" in plan.cmd
        # Probe the actual installed executable and its runtime closure inside
        # the production wrapper, without starting a provider/model request.
        cmd, env = boundary.wrap([plan.cmd[0], "--version"], plan.env_overrides)
        probe = subprocess.run(cmd, cwd=plan.cwd, env=env, capture_output=True, text=True, timeout=30)
        assert probe.returncode == 0, probe.stderr
        assert probe.stdout.strip()
        assert env["HOME"] != str(home)
    finally:
        boundary.cleanup()
