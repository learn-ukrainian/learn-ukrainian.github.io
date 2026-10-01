"""Full content review keeps attempt binding and native write denial (#9464)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.attempt_boundary import prepare_attempt_boundary, verify_full_review_tree
from scripts.review.isolation import ReviewIsolationError
from tests.agent_runtime.test_attempt_boundary import attempt_config, manifest_world
from tests.agent_runtime.test_attempt_boundary import world as boundary_world  # noqa: F401


@pytest.fixture
def world(request):
    root, home = request.getfixturevalue("boundary_world")
    subprocess.run(["git", "init", "-q", str(root)], check=True, timeout=30)
    return root, home


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_full_review_kind_and_family_matrix(world, tmp_path, agent, kind):
    root, _ = world
    manifest = manifest_world(root, kind)
    tc = attempt_config(root, tmp_path, manifest, agent)
    tc.update(review_access="full", review_cwd=str(root))
    tc.pop("allowed_tools", None)
    if agent == "claude":
        tc["reviewer_tools"] = True
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    try:
        assert boundary.full and boundary.workspace == root
        assert not boundary.egress
    finally:
        boundary.cleanup()
    assert (root / manifest["inputs"]["plan"]["path"]).is_file()
    assert (
        json.loads(Path(tc["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]["env"]["LU_REVIEW_ATTEMPT_ID"]
        == "current"
    )


@pytest.mark.parametrize("kind", ["plan", "lesson", "rereview"])
def test_full_review_checks_actual_cwd_not_render_copy(world, tmp_path, kind):
    root, _ = world
    manifest = manifest_world(root, kind)
    tc = attempt_config(root, tmp_path, manifest, "claude")
    other = tmp_path / "other"
    other.mkdir()
    tc.update(review_access="full", review_cwd=str(other), reviewer_tools=True)
    tc.pop("allowed_tools", None)
    with pytest.raises(ReviewIsolationError, match="full_review_tree_mismatch"):
        prepare_attempt_boundary("claude", "read-only", None, tc)
    # A separate tree with identical inputs is permitted; one differing input is refused.
    import shutil

    shutil.copytree(root, other, dirs_exist_ok=True)
    boundary = prepare_attempt_boundary("claude", "read-only", None, tc)
    assert boundary.workspace == other
    boundary.cleanup()
    (other / manifest["inputs"]["plan"]["path"]).write_text("changed")
    with pytest.raises(ReviewIsolationError, match="full_review_tree_mismatch"):
        verify_full_review_tree(Path(tc["review_manifest"]), other)


@pytest.mark.parametrize(
    "mutation,code",
    [
        ({"review_access": "unknown"}, "review_access_invalid"),
        ({"review_cwd": None}, "full_review_cwd_missing"),
        ({"reviewer_tools": False}, "full_review_write_denial_missing"),
        ({"attempt_os_sandbox": True}, "full_review_write_denial_conflict"),
        ({"attempt_id": "different"}, "attempt_identity_mismatch"),
    ],
)
def test_full_review_refuses_incomplete_or_write_capable_launch(world, tmp_path, mutation, code):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "claude")
    tc.pop("allowed_tools", None)
    tc.update({"review_access": "full", "review_cwd": str(root), "reviewer_tools": True, **mutation})
    with pytest.raises(ReviewIsolationError, match=code):
        prepare_attempt_boundary("claude", "read-only", None, tc)


def test_full_review_still_checks_manifest_digest(world, tmp_path):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    tc.update(review_access="full", review_cwd=str(root))
    Path(tc["review_manifest"]).write_bytes(Path(tc["review_manifest"]).read_bytes() + b"# changed\n")
    with pytest.raises(ReviewIsolationError, match="attempt_manifest_hash_mismatch"):
        prepare_attempt_boundary("codex", "read-only", None, tc)


def test_agy_full_review_uses_native_sandbox_without_permission_bypass(tmp_path, monkeypatch):
    from scripts.agent_runtime.adapters import agy

    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    monkeypatch.setattr(agy, "_build_log_path", lambda *a: tmp_path / "agy.log")
    kw = dict(prompt="review", mode="read-only", cwd=tmp_path, model=None, task_id="review", session_id=None)
    plan = AgyAdapter().build_invocation(**kw, tool_config={"review_access": "full", "agy_review_sandbox": False})
    assert "--sandbox" in plan.cmd
    assert "--dangerously-skip-permissions" not in plan.cmd
    with pytest.raises(ValueError, match="forbids"):
        AgyAdapter().build_invocation(**kw, tool_config={"review_access": "full", "agy_skip_permissions": True})
    with pytest.raises(ValueError, match="full_review_requires_read_only"):
        AgyAdapter().build_invocation(**{**kw, "mode": "workspace-write"}, tool_config={"review_access": "full"})


@pytest.mark.parametrize("formal", [True, False])
def test_runner_preserves_actual_checkout_and_disables_formal_failover(tmp_path, monkeypatch, formal):
    from scripts.agent_runtime import attempt_boundary, runner

    seen = {}
    monkeypatch.setattr(attempt_boundary, "prepare_attempt_boundary", lambda a, m, s, tc: seen.update(config=tc))
    monkeypatch.setattr(runner, "prepare_trail_isolation", lambda **kw: None)
    monkeypatch.setattr(runner, "_invoke_impl", lambda *a, **kw: seen.update(invocation=kw))
    tc = (
        {"review_access": "full", "review_id": "r", "attempt_id": "a", "review_cwd": str(tmp_path / "wrong")}
        if formal
        else None
    )
    runner.invoke("claude", "review", mode="read-only", cwd=tmp_path, tool_config=tc)
    assert seen["invocation"]["cwd"] == tmp_path
    assert seen["invocation"]["allow_runner_failover"] is (not formal)
    if formal:
        assert seen["config"]["review_cwd"] == str(tmp_path)


def test_full_review_refuses_a_sparse_checkout(world, tmp_path):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    subprocess.run(["git", "-C", str(root), "config", "core.sparseCheckout", "true"], check=True, timeout=30)
    with pytest.raises(ReviewIsolationError, match="full_review_requires_full_checkout"):
        verify_full_review_tree(Path(tc["review_manifest"]), root)


def test_native_claude_full_review_keeps_shell_sources_deny_list_and_hooks(tmp_path):
    from scripts.agent_runtime.adapters.claude import ClaudeAdapter

    config = tmp_path / "mcp.json"
    config.write_text('{"mcpServers": {}}')
    plan = ClaudeAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "review_access": "full",
            "reviewer_tools": True,
            "mcp_config_path": str(config),
            "strict_mcp_config": True,
        },
    )
    assert "Bash" in plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert "mcp__sources__*" in plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    assert {"Edit", "Write"} <= set(plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(","))
    assert "--settings" in plan.cmd and "--bare" not in plan.cmd and "--safe-mode" not in plan.cmd


def test_native_codex_full_review_keeps_read_only_sandbox(tmp_path, monkeypatch):
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    lease = tmp_path / "scratch" / "learn-ukrainian" / "review"
    lease.mkdir(parents=True)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_path / "scratch"))
    plan = CodexAdapter().build_invocation(
        prompt="review using mcp__sources__verify_words",
        mode="read-only",
        cwd=checkout,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"review_access": "full", "read_only_tmp_root": str(lease)},
    )
    try:
        assert 'sandbox_mode="read-only"' in plan.cmd
        assert "--dangerously-bypass-approvals-and-sandbox" not in plan.cmd
        assert 'mcp_servers.sources.default_tools_approval_mode="approve"' in plan.cmd
    finally:
        Path(plan.output_file).unlink()


def test_full_review_refuses_unsupported_harness_and_resumption(world, tmp_path):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    tc.update(review_access="full", review_cwd=str(root))
    with pytest.raises(ReviewIsolationError, match="full_review_harness_unsupported"):
        prepare_attempt_boundary("cursor", "read-only", None, tc)
    with pytest.raises(ReviewIsolationError, match="attempt_requires_fresh_read_only_sources"):
        prepare_attempt_boundary("codex", "read-only", "old-session", tc)
    with pytest.raises(ReviewIsolationError, match="attempt_requires_fresh_read_only_sources"):
        prepare_attempt_boundary("codex", "workspace-write", None, tc)


def test_full_review_requires_git_checkout_and_eligible_manifest(world, tmp_path):
    from scripts.curriculum.evidence import lock

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    other = tmp_path / "without-git"
    import shutil

    shutil.copytree(root, other, ignore=shutil.ignore_patterns(".git"))
    with pytest.raises(ReviewIsolationError, match="full_review_checkout_missing"):
        verify_full_review_tree(Path(tc["review_manifest"]), other)
    manifest = yaml.safe_load(Path(tc["review_manifest"]).read_bytes())
    manifest["extra"] = "not admitted by the schema"
    Path(tc["review_manifest"]).write_bytes(lock.yaml_bytes(manifest))
    with pytest.raises(ReviewIsolationError, match="full_review_manifest_ineligible"):
        verify_full_review_tree(Path(tc["review_manifest"]), root)


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_full_seat_adapter_host_write_and_process_denial(world, tmp_path, monkeypatch, agent):
    """Real adapter argv, fake seat payload, actual Bubblewrap and detached child."""
    import os
    import sys
    import time
    from dataclasses import replace

    from scripts.agent_runtime.adapters.claude import ClaudeAdapter
    from scripts.agent_runtime.adapters.codex import CodexAdapter

    root, _home = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    tc.update(review_access="full", review_cwd=str(root), reviewer_tools=True)
    tc.pop("allowed_tools", None)
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    try:
        adapter = {"claude": ClaudeAdapter, "codex": CodexAdapter, "agy": AgyAdapter}[agent]()
        monkeypatch.setattr("scripts.agent_runtime.adapters.agy._require_background_wait_support", lambda *a: None)
        plan = adapter.build_invocation(
            prompt="probe",
            mode="read-only",
            cwd=root,
            model=adapter.default_model,
            task_id="full-probe",
            session_id=None,
            tool_config=boundary.tool_config,
            effort="high",
        )
        config = json.loads(Path(tc["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]
        ledger = Path(config["env"]["LU_REVIEW_LEDGER_PATH"])
        targets = [
            ledger,
            ledger.parent / "forged.jsonl",
            root / "reviewed.txt",
            root / "batch_state/tasks/task.json",
            root / "batch_state/tasks/task.result",
        ]
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target != ledger:
                target.write_text("host-sentinel")
        original = [p.read_bytes() for p in targets]
        private = boundary.write_root / "return.yaml"
        child_marker = boundary.write_root / "child-alive"
        # The child detaches its session and closes streams so ordinary pipe cleanup
        # cannot accidentally be the reason it exits. The PID namespace must kill it.
        child = (
            "import time,pathlib; time.sleep(1); pathlib.Path("
            + repr(str(child_marker))
            + ").write_text('escaped'); time.sleep(30)"
        )
        payload = (
            "import pathlib,os,subprocess,time,json\n"
            f"targets={list(map(str, targets))!r}\n"
            "for target in targets:\n"
            " p=pathlib.Path(target); p.read_bytes()\n"
            " try: p.write_text('FORGED')\n"
            " except OSError: pass\n"
            " else: raise AssertionError('host write allowed')\n"
            f"pathlib.Path({str(private)!r}).write_text('own return')\n"
            "assert os.readlink('/proc/self/ns/net') == " + repr(os.readlink("/proc/self/ns/net")) + "\n"
            "assert os.readlink('/proc/self/ns/pid') != " + repr(os.readlink("/proc/self/ns/pid")) + "\n"
            f"child=subprocess.Popen({[sys.executable, '-c', child]!r},start_new_session=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
            "print(json.dumps({'denied':len(targets),'host_read':len(targets),'network_shared':True,'private_pid':True}),flush=True)\n"
        )
        plan = replace(plan, cmd=[sys.executable, "-c", payload], stdin_payload=None)
        cmd, env = boundary.wrap(plan.cmd, plan.env_overrides)
        assert cmd[1:4] == ["--ro-bind", "/", "/"]
        assert "--unshare-net" not in cmd and "--die-with-parent" in cmd
        result = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {"denied": 5, "host_read": 5, "network_shared": True, "private_pid": True}
        assert private.read_text() == "own return"
        time.sleep(1.3)
        assert not child_marker.exists(), "detached child survived seat exit"
        assert [p.read_bytes() for p in targets] == original
        print(f"{agent}: 5 denied writes, 5 readable host controls, detached child killed, network shared")
    finally:
        boundary.cleanup()
    assert root.exists() and not boundary.write_root.exists()


def test_full_bwrap_unavailable_and_failed_probe_refuse(tmp_path, monkeypatch):
    from scripts.review import isolation

    write = tmp_path / "runtime"
    write.mkdir()
    monkeypatch.setattr(
        isolation,
        "_resolve_fixed_system_executable",
        lambda *a, **k: (_ for _ in ()).throw(ReviewIsolationError("missing")),
    )
    with pytest.raises(ReviewIsolationError, match="full_review_bwrap_unavailable"):
        isolation.prepare_full_host_sandbox(write_root=write, cwd=tmp_path)
    monkeypatch.setattr(isolation, "_resolve_fixed_system_executable", lambda *a, **k: Path("/usr/bin/bwrap"))
    monkeypatch.setattr(isolation.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 1))
    with pytest.raises(ReviewIsolationError, match="full_review_bwrap_probe_failed"):
        isolation.prepare_full_host_sandbox(write_root=write, cwd=tmp_path)


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_full_cli_compatibility_and_mcp_probes_are_sandboxed(world, tmp_path, agent):
    import shlex

    from scripts.agent_runtime.review_mcp import verify_agy_review_effective_mcp, verify_codex_review_effective_mcp

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    tc.update(review_access="full", review_cwd=str(root), reviewer_tools=True)
    tc.pop("allowed_tools", None)
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    sentinel = root / "version-probe-target"
    sentinel.write_text("original")
    try:
        proxy = json.loads(Path(boundary.tool_config["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]
        if agent == "codex":
            rows = json.dumps(
                [{"name": "sources", "enabled": True, "transport": {"type": "stdio", **proxy, "env": {}}}]
            )
        else:
            rows = f"{'NAME':<12}{'TYPE':<10}{'STATUS':<12}COMMAND/URL\n"
            rows += f"{'sources':<12}{'stdio':<10}{'enabled':<12}{proxy['command']} {' '.join(proxy['args'])}\n"
        binary = root / "fake-seat"
        binary.write_text(
            "#!/bin/sh\n"
            f"if (printf forged > {shlex.quote(str(sentinel))}) 2>/dev/null; then exit 99; fi\n"
            'if test "$1" = --version; then echo \''
            + ("2.1.200" if agent == "claude" else "1.2.10")
            + "'; else printf '%s' "
            + shlex.quote(rows)
            + "; fi\n"
        )
        binary.chmod(0o700)
        boundary.verify_seat([str(binary)], {})
        assert sentinel.read_text() == "original"
        if agent != "claude":
            # Extra effective servers still fail closed through the wrapped gate.
            binary.write_text("#!/bin/sh\nprintf '%s' " + shlex.quote(rows.replace("sources", "foreign")) + "\n")
            binary.chmod(0o700)
            gate = verify_codex_review_effective_mcp if agent == "codex" else verify_agy_review_effective_mcp
            kw = {"codex_bin": str(binary)} if agent == "codex" else {"agy_bin": str(binary), "env": boundary.env}
            with pytest.raises(ValueError, match="exactly"):
                gate(config_path=boundary.config_path, cwd=root, boundary=boundary, **kw)
    finally:
        boundary.cleanup()


def test_full_dispatch_telemetry_does_not_execute_cli(monkeypatch):
    from scripts.agent_runtime import telemetry

    monkeypatch.setattr(telemetry, "_resolve_cli_version", lambda *a: pytest.fail("unconfined CLI probe"))
    result = telemetry.resolve_dispatch_start_telemetry(
        agent_name="codex", requested_model="gpt-6.1-sol", requested_effort="high", probe_cli_version=False
    )
    assert result.cli_version == "unknown" and result.model == "gpt-6.1-sol"
