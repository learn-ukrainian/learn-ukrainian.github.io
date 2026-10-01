"""Full content review keeps attempt binding and native write denial (#9464)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from functools import partial
from pathlib import Path

import pytest
import yaml

from scripts.agent_runtime.adapters.agy import AgyAdapter
from scripts.agent_runtime.attempt_boundary import prepare_attempt_boundary, verify_full_review_tree
from scripts.review.isolation import ReviewIsolationError
from tests.agent_runtime.test_attempt_boundary import attempt_config as _attempt_config
from tests.agent_runtime.test_attempt_boundary import manifest_world
from tests.agent_runtime.test_attempt_boundary import world as boundary_world  # noqa: F401

attempt_config = partial(_attempt_config, review_access="full")


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
@pytest.mark.parametrize("access", ["isolated", "full"])
def test_review_mcp_provisions_attempt_access_and_exact_claude_tools(world, tmp_path, agent, access):
    from scripts.agent_runtime.review_mcp import prepare_review_attempt, review_tools_allowed_csv
    from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS, REVIEW_TOOLS

    root, _ = world
    manifest = root / "manifest.yaml"
    manifest.write_text(yaml.safe_dump(manifest_world(root, "plan")))
    plan = prepare_review_attempt(
        "tool-contract", agent, manifest, agent, receipts_root=tmp_path / "receipts", review_access=access
    )
    server = json.loads(plan.config_path.read_bytes())["mcpServers"]["sources"]
    assert server["env"]["LU_REVIEW_ACCESS"] == access
    tools = FULL_REVIEW_TOOLS if access == "full" else REVIEW_TOOLS
    if agent == "claude":
        assert set(review_tools_allowed_csv(agent, access).split(",")) == {f"mcp__sources__{t}" for t in tools}
        if access == "full":
            assert plan.adapter_options["reviewer_tools"] is True
            assert "allowed_tools" not in plan.adapter_options
        else:
            assert plan.adapter_options["allowed_tools"] == review_tools_allowed_csv(agent)
    elif agent == "codex":
        import tomllib

        config = tomllib.loads((plan.codex_home / "config.toml").read_text())
        assert config["mcp_servers"]["sources"]["env"] == server["env"]
    else:
        from scripts.agent_runtime.review_mcp import agy_full_review_settings, agy_review_mcp_config_path

        assert json.loads(agy_review_mcp_config_path(plan.agy_home).read_bytes())["mcpServers"]["sources"] == server
        assert agy_full_review_settings()["permissions"]["allow"] == [
            f"mcp(sources/{t})" for t in sorted(FULL_REVIEW_TOOLS)
        ]


def full_probe_code(targets, host_home, pinned, corpus, child_marker, abstract):
    """One immutable script shared by fake adapters and authenticated seats."""
    settings = {
        "targets": list(map(str, targets)),
        "host_home": str(host_home),
        "pinned": pinned,
        "corpus": str(corpus),
        "child_marker": str(child_marker),
        "abstract": abstract,
        "host_pid": os.readlink("/proc/self/ns/pid"),
        "host_net": os.readlink("/proc/self/ns/net"),
        "host_uid": os.getuid(),
        "interpreter": str(Path(sys.executable).resolve()),
    }
    return f"settings={settings!r}\n" + textwrap.dedent("""\
        import json,os,pathlib,socket,subprocess
        proof = {}
        for target in settings['targets']:
            try: pathlib.Path(target).write_text('FORGED')
            except OSError: pass
            else: raise AssertionError('host write allowed')
        proof['denied_writes'] = len(settings['targets'])
        for base in (pathlib.Path.home(), pathlib.Path(settings['host_home'])):
            for name in ('.ssh/id_test', '.config/gh/hosts.yml'):
                try: (base / name).read_bytes()
                except OSError: pass
                else: raise AssertionError('host credentials exposed')
        proof['host_secrets_denied'] = 4
        bus = '/run/user/' + str(settings['host_uid']) + '/bus'
        try:
            result = subprocess.run(['systemd-run','--user','--wait','--quiet','/bin/sh','-c',
                'printf FORGED > "$1"', 'probe', settings['targets'][2]],
                env={**os.environ,'DBUS_SESSION_BUS_ADDRESS':'unix:path='+bus},
                capture_output=True,timeout=3)
            assert result.returncode != 0, 'systemd escaped'
        except FileNotFoundError: pass
        proof['systemd_denied'] = True
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(1)
            try: client.connect(bus)
            except OSError: pass
            else: raise AssertionError('host D-Bus exposed')
        proof['dbus_denied'] = True
        for port in (22,8765):
            try: client = socket.create_connection(('127.0.0.1',port),timeout=1)
            except OSError: pass
            else:
                client.close()
                raise AssertionError('host TCP exposed')
        proof['host_tcp_denied'] = [22,8765]
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(1)
            try: client.connect(settings['abstract'])
            except OSError: pass
            else: raise AssertionError('host abstract socket exposed')
        proof['abstract_denied'] = True
        for key,ns in (('private_pid','pid'),('private_network','net')):
            assert os.readlink('/proc/self/ns/'+ns) != settings['host_'+('pid' if ns=='pid' else 'net')]
            proof[key] = True
        assert subprocess.run(['git','log','-1'],capture_output=True,timeout=5).returncode == 0
        proof['git_log'] = True
        shown = subprocess.run(['git','show','HEAD:'+settings['pinned']],capture_output=True,timeout=5)
        assert shown.returncode == 0 and shown.stdout == pathlib.Path(settings['pinned']).read_bytes()
        proof['git_show'] = True
        assert pathlib.Path(settings['corpus']).read_text() == 'corpus control'
        try: pathlib.Path(settings['corpus']).write_text('corrupt')
        except OSError: pass
        else: raise AssertionError('corpus write allowed')
        proof['corpus_read'] = True
        marker = settings['child_marker'] if settings['child_marker'] != ':runtime:' else str(pathlib.Path(os.environ['TMPDIR']).parent / 'child-alive')
        child = 'import time,pathlib; time.sleep(1); p=pathlib.Path('+repr(marker)+');\\nwhile True: p.write_text(str(time.monotonic_ns())); time.sleep(.1)'
        subprocess.Popen([settings['interpreter'],'-c',child],start_new_session=True,
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        print(json.dumps(proof),flush=True)
        """)


def captured_probe(value):
    """Find the probe JSON through native exec's nested content/JSON envelopes."""
    if isinstance(value, dict):
        if value.get("denied_writes") == 5 and value.get("git_show") is True and value.get("private_network") is True:
            return value
        children = value.values()
    elif isinstance(value, list):
        children = value
    elif isinstance(value, str):
        for line in value.splitlines():
            try:
                parsed = json.loads(line)
            except ValueError:
                continue
            if parsed != value and (proof := captured_probe(parsed)):
                return proof
        return None
    else:
        return None
    return next((proof for child in children if (proof := captured_probe(child))), None)


def test_captured_probe_reads_nested_exec_output():
    proof = {"denied_writes": 5, "git_show": True, "private_network": True}
    envelope = [{"type": "input_text", "text": json.dumps({"output": json.dumps(proof) + "\n"})}]
    assert captured_probe(envelope) == proof
    assert captured_probe("Traceback\nnot a successful probe") is None


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
        assert boundary.egress and boundary.egress.thread.is_alive()
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


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
@pytest.mark.parametrize("server_access", [None, "isolated", "invalid"])
def test_full_review_refuses_mismatched_sources_access(world, tmp_path, agent, server_access):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    tc.update(review_access="full", review_cwd=str(root), reviewer_tools=True)
    config = Path(tc["mcp_config_path"])
    data = json.loads(config.read_bytes())
    if server_access is None:
        data["mcpServers"]["sources"]["env"].pop("LU_REVIEW_ACCESS")
    else:
        data["mcpServers"]["sources"]["env"]["LU_REVIEW_ACCESS"] = server_access
    config.write_text(json.dumps(data))
    with pytest.raises(ReviewIsolationError, match="attempt_review_access_mismatch"):
        prepare_attempt_boundary(agent, "read-only", None, tc)


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


@pytest.mark.parametrize("access", ["full", "isolated"])
def test_agy_sources_permission_is_only_projected_for_full_attempts(world, tmp_path, monkeypatch, access):
    from scripts.agent_runtime.adapters import agy

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy", review_access=access)
    tc.update(review_access=access, review_cwd=str(root))
    boundary = prepare_attempt_boundary("agy", "read-only", None, tc)
    monkeypatch.setattr(agy, "_require_background_wait_support", lambda *a: None)
    try:
        plan = AgyAdapter().build_invocation(
            prompt="probe",
            mode="read-only",
            cwd=boundary.workspace,
            model=None,
            task_id="probe",
            session_id=None,
            tool_config=boundary.tool_config,
        )
        settings = Path(plan.env_overrides["AGY_APP_DATA_DIR"]) / "settings.json"
        if access == "full":
            from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS

            assert json.loads(settings.read_bytes()) == {
                "permissions": {"allow": [f"mcp(sources/{name})" for name in sorted(FULL_REVIEW_TOOLS)]}
            }
            assert "--sandbox" in plan.cmd
            assert "--dangerously-skip-permissions" not in plan.cmd
        else:
            assert not settings.exists()
            assert "--sandbox" not in plan.cmd
            assert "--dangerously-skip-permissions" in plan.cmd
    finally:
        boundary.cleanup()


@pytest.mark.parametrize(
    "settings",
    [
        {"permissions": {"allow": ["mcp(*)"]}},
        {"permissions": {"allow": ["mcp(sources/*)"]}},
        {"permissions": {"allow": ["mcp(other/verify_words)"]}},
        {"permissions": {"allow": ["mcp(sources)", "command(*)"]}},
        {"permissions": {"allow": ["mcp(sources)"]}, "dangerouslySkipPermissions": True},
        {},
    ],
)
def test_full_agy_permission_widening_is_refused_before_cli(world, tmp_path, monkeypatch, settings):
    from scripts.agent_runtime.review_mcp import verify_agy_review_effective_mcp

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "agy")
    tc.update(review_access="full", review_cwd=str(root))
    boundary = prepare_attempt_boundary("agy", "read-only", None, tc)
    try:
        (Path(boundary.env["AGY_APP_DATA_DIR"]) / "settings.json").write_text(json.dumps(settings))
        monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("unsafe CLI launch"))
        with pytest.raises(ValueError, match="requires exactly the sources review tool"):
            verify_agy_review_effective_mcp(
                config_path=boundary.config_path,
                cwd=root,
                env=boundary.env,
                agy_bin="agy",
                boundary=boundary,
            )
    finally:
        boundary.cleanup()


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
    from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS

    granted = set(plan.cmd[plan.cmd.index("--allowedTools") + 1].split(","))
    assert {tool for tool in granted if tool.startswith("mcp__")} == {
        f"mcp__sources__{tool}" for tool in FULL_REVIEW_TOOLS
    }
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
    import socket
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
        child_marker = boundary.write_root / "child-alive"
        corpus = root / "data/textbook-text/probe.txt"
        corpus.parent.mkdir(parents=True)
        corpus.write_text("corpus control")
        pinned = yaml.safe_load(Path(tc["review_manifest"]).read_bytes())["inputs"]["plan"]["path"]
        subprocess.run(["git", "-C", str(root), "add", pinned], check=True, timeout=10)
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
            timeout=10,
        )
        for name in (".ssh/id_test", ".config/gh/hosts.yml"):
            secret = _home / name
            secret.parent.mkdir(parents=True, exist_ok=True)
            secret.write_text("private sentinel")
        host_listener = socket.socket(socket.AF_UNIX)
        abstract = "\0full-review-" + str(os.getpid()) + "-" + agent
        host_listener.bind(abstract)
        host_listener.listen()
        # The listener really exists outside the namespace.
        with socket.socket(socket.AF_UNIX) as control:
            control.connect(abstract)
        payload = full_probe_code(targets, _home, pinned, corpus, child_marker, abstract)
        plan = replace(plan, cmd=[sys.executable, "-c", payload], stdin_payload=None)
        cmd, env = boundary.wrap(plan.cmd, plan.env_overrides)
        assert cmd[1:4] != ["--ro-bind", "/", "/"]
        assert "--unshare-net" in cmd and "--die-with-parent" in cmd
        result = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        proof = json.loads(result.stdout)
        assert proof == {
            "denied_writes": 5,
            "host_secrets_denied": 4,
            "systemd_denied": True,
            "dbus_denied": True,
            "host_tcp_denied": [22, 8765],
            "abstract_denied": True,
            "private_pid": True,
            "private_network": True,
            "git_log": True,
            "git_show": True,
            "corpus_read": True,
        }
        host_listener.close()
        time.sleep(1.3)
        assert not child_marker.exists(), "detached child survived seat exit"
        assert [p.read_bytes() for p in targets] == original
        print(json.dumps({"seat": agent, **proof, "detached_child_killed": True}))
    finally:
        boundary.cleanup()
    assert root.exists() and not boundary.write_root.exists()


def test_full_bwrap_unavailable_and_failed_probe_refuse(world, tmp_path, monkeypatch):
    from scripts.agent_runtime.attempt_boundary import full_review_reads
    from scripts.review import isolation

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    tc.update(review_access="full", review_cwd=str(root))
    boundary = prepare_attempt_boundary("codex", "read-only", None, tc)
    try:
        monkeypatch.setattr(
            isolation,
            "_resolve_fixed_system_executable",
            lambda *a, **k: (_ for _ in ()).throw(ReviewIsolationError("missing")),
        )
        with pytest.raises(ReviewIsolationError, match="sandbox_unavailable:linux_bwrap_missing"):
            boundary.wrap(["/bin/true"], {})
        reads = full_review_reads(root)
        monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.full_review_reads", lambda workspace: reads)
        monkeypatch.setattr(isolation, "_resolve_fixed_system_executable", lambda *a, **k: Path("/usr/bin/bwrap"))
        monkeypatch.setattr(isolation.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 1))
        with pytest.raises(ReviewIsolationError, match="sandbox_probe_allow_failed"):
            boundary.wrap(["/bin/true"], {})
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_full_cli_compatibility_and_mcp_probes_are_sandboxed(world, tmp_path, monkeypatch, agent):
    import shlex

    from scripts.agent_runtime.attempt_boundary import runtime_files
    from scripts.agent_runtime.review_mcp import verify_agy_review_effective_mcp, verify_codex_review_effective_mcp

    monkeypatch.setattr(
        "scripts.agent_runtime.attempt_boundary.runtime_files", lambda binary: runtime_files(Path("/bin/sh"))
    )

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


def test_linked_full_tree_has_git_and_corpus_without_other_checkouts(world, tmp_path):
    root, _ = world
    doc = manifest_world(root, "plan")
    pinned = doc["inputs"]["plan"]["path"]
    subprocess.run(["git", "-C", str(root), "add", "curriculum", "docs"], check=True, timeout=10)
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
        timeout=10,
    )
    reviewed = tmp_path / "linked"
    other = tmp_path / "other-checkout"
    for path in (reviewed, other):
        subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(path)],
            check=True,
            capture_output=True,
            timeout=10,
        )
    tc = attempt_config(root, tmp_path, doc, "codex")
    tc.update(review_access="full", review_cwd=str(reviewed))
    corpus = root / "data/textbook-text/probe.txt"
    corpus.parent.mkdir(parents=True)
    corpus.write_text("corpus control")
    (root / "private-control").write_text("outside checkout")
    (other / "private-control").write_text("other checkout")
    boundary = prepare_attempt_boundary("codex", "read-only", None, tc)
    try:
        payload = (
            "import pathlib,subprocess\n"
            f"assert pathlib.Path({str(corpus)!r}).read_text() == 'corpus control'\n"
            f"assert subprocess.run(['git','show','HEAD:'+{pinned!r}],capture_output=True).returncode == 0\n"
            "assert subprocess.run(['git','log','-1'],capture_output=True).returncode == 0\n"
            f"for path in {[str(root / 'private-control'), str(other / 'private-control'), str(root / '.git/worktrees/other-checkout/HEAD')]!r}:\n"
            " try: pathlib.Path(path).read_bytes()\n"
            " except OSError: pass\n"
            " else: raise AssertionError('outside checkout exposed')\n"
            "print('linked git and corpus: allowed; other checkouts: denied')\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", payload], {})
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("location", ["checkout", "corpus"])
def test_full_read_set_refuses_host_socket_files(world, tmp_path, location):
    import socket

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    tc.update(review_access="full", review_cwd=str(root))
    directory = root if location == "checkout" else root / "data"
    directory.mkdir(exist_ok=True)
    # Relative bind keeps the pathname within sockaddr_un's size limit.
    previous = os.getcwd()
    with socket.socket(socket.AF_UNIX) as listener:
        try:
            os.chdir(directory)
            listener.bind("host-control.sock")
        finally:
            os.chdir(previous)
        listener.listen()
        boundary = prepare_attempt_boundary("codex", "read-only", None, tc)
        try:
            with pytest.raises(ReviewIsolationError, match="full_review_special_file_refused"):
                boundary.wrap(["/bin/true"], {})
        finally:
            boundary.cleanup()


def test_full_review_refuses_external_git_object_alternates(world, tmp_path):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), "codex")
    tc.update(review_access="full", review_cwd=str(root))
    (root / ".git/objects/info/alternates").write_text(str(tmp_path / "external-objects"))
    boundary = prepare_attempt_boundary("codex", "read-only", None, tc)
    try:
        with pytest.raises(ReviewIsolationError, match="full_review_git_alternates_unsupported"):
            boundary.wrap(["/bin/true"], {})
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_native_user_lookup_uses_only_private_home(world, tmp_path, agent):
    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    tc.update(review_access="full", review_cwd=str(root), reviewer_tools=True)
    tc.pop("allowed_tools", None)
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    try:
        payload = (
            "import pwd,grp,os,pathlib\n"
            "entry=pwd.getpwuid(os.getuid())\n"
            "assert entry.pw_name == 'review' and entry.pw_dir == os.environ['HOME']\n"
            "assert entry.pw_shell == '/bin/bash'\n"
            "assert len(pwd.getpwall()) == len(grp.getgrall()) == 1\n"
            "assert pathlib.Path(entry.pw_dir).is_dir()\n"
            "print('private user lookup: allowed')\n"
        )
        cmd, env = boundary.wrap([sys.executable, "-c", payload], {})
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
    finally:
        boundary.cleanup()


@pytest.mark.parametrize("agent", ["claude", "codex", "agy"])
def test_full_sources_success_is_issued_outside_the_seat(world, tmp_path, agent):
    """CI's controlled source service uses the production socket and ledger writer."""
    from scripts.review.receipts.ledger import records

    root, _ = world
    tc = attempt_config(root, tmp_path, manifest_world(root, "plan"), agent)
    tc.update(review_access="full", review_cwd=str(root), reviewer_tools=True)
    tc.pop("allowed_tools", None)
    boundary = prepare_attempt_boundary(agent, "read-only", None, tc)
    original = boundary.connection.server
    ledger = Path(original["env"]["LU_REVIEW_LEDGER_PATH"])
    server_code = textwrap.dedent("""\
        import json,os,sys,pathlib
        from scripts.review.receipts.ledger import append
        for line in sys.stdin:
            request=json.loads(line)
            if 'id' not in request: continue
            if request['method']=='initialize':
                result={'protocolVersion':'2024-11-05','capabilities':{'tools':{}},'serverInfo':{'name':'source-control','version':'1'}}
            else:
                path=pathlib.Path(os.environ['LU_REVIEW_LEDGER_PATH'])
                receipt=append(path,review_id=path.parent.name,attempt_id=os.environ['LU_REVIEW_ATTEMPT_ID'],
                    manifest_sha256=os.environ['LU_REVIEW_MANIFEST_SHA256'],tool='verify_words',server_version='f'*64,
                    arguments=request['params']['arguments'],snapshots={},status='ok',result='source positive control')
                result={'content':[{'type':'text','text':'source positive control\\nreceipt: '+receipt}],'isError':False}
            print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}),flush=True)
        """)
    # Swap only the CI backend after canonical attempt admission. No production
    # configuration, bindings, forwarder, mount policy or ledger implementation
    # is replaced. The writer runs outside; the seat cannot reach its store.
    boundary.connection.server = {**original, "args": ["-c", server_code]}
    proxy = json.loads(Path(boundary.tool_config["mcp_config_path"]).read_bytes())["mcpServers"]["sources"]
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "control", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "verify_words", "arguments": {"words": ["fixture"]}},
        },
    ]
    payload = (
        "import subprocess,json,pathlib\n"
        f"p=subprocess.Popen({[proxy['command'], *proxy['args']]!r},stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)\n"
        f"for request in {requests!r}:\n"
        " p.stdin.write(json.dumps(request)+'\\n'); p.stdin.flush()\n"
        " if 'id' in request:\n"
        "  response=json.loads(p.stdout.readline()); assert response['id']==request['id']\n"
        "assert response['result']['isError'] is False\n"
        "assert 'source positive control' in response['result']['content'][0]['text']\n"
        "p.stdin.close(); assert p.wait(timeout=5)==0\n"
        f"try: pathlib.Path({str(ledger)!r}).read_bytes()\n"
        "except OSError: pass\n"
        "else: raise AssertionError('ledger exposed')\n"
        "print('sources success and outside receipt: allowed; ledger read: denied')\n"
    )
    try:
        cmd, env = boundary.wrap([sys.executable, "-c", payload], {})
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stderr
        [receipt] = records(ledger)
        assert receipt["status"] == "ok" and receipt["result"] == "source positive control"
        assert receipt["attempt_id"] == tc["attempt_id"]
        print(f"{agent}: sources success and valid outside receipt; ledger inaccessible")
    finally:
        boundary.cleanup()
