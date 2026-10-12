"""The ACP Claude seat pins and version-gates the host Claude Code (#10500)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.agent_runtime.adapters import acpx as acpx_module
from scripts.agent_runtime.adapters import claude as claude_module
from scripts.agent_runtime.adapters.acpx import (
    AcpxClaudeShadowAdapter,
    AcpxShadowRefusalError,
    ClaudeCodeExecutableRefusal,
)
from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.env_sanitize import build_agent_env
from tests.agent_runtime import test_acpx_adapter as _acpx_tests
from tests.agent_runtime.test_acpx_adapter import _stub_binary

# Reuse the suite's registered-worktree fixtures: pytest registers them under
# their own names (``_acpx_worktree`` and the ``tmp_path`` override).
_acpx_worktree = _acpx_tests._acpx_worktree
_worktree_tmp_path = _acpx_tests.tmp_path

_SESSION_ID = "0f6c2f8e-1d2b-4c3a-9e8f-7a6b5c4d3e2f"
_REAL_GATE = acpx_module._require_host_claude_code


def _fake_claude(root: Path, version_line: str, *, name: str = "2.1.296", exit_code: int = 0) -> Path:
    """A native-install shaped tree: <root>/share/claude/versions/<name>."""
    versions = root / "share" / "claude" / "versions"
    versions.mkdir(parents=True, exist_ok=True)
    for directory in (root, root / "share", root / "share" / "claude", versions):
        directory.chmod(0o755)
    executable = versions / name
    executable.write_text(f"#!/bin/sh\nprintf '%s\\n' '{version_line}'\nexit {exit_code}\n", encoding="utf-8")
    executable.chmod(0o755)
    return executable


@pytest.fixture
def host(tmp_path, monkeypatch):
    """Point host resolution at a private tree and check ancestors only inside it."""
    root = tmp_path / "local"
    monkeypatch.setattr(acpx_module, "_CLAUDE_CODE_TRUST_ROOT", tmp_path)
    monkeypatch.setattr(acpx_module, "CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE", False)

    def install(version_line: str = "2.1.296 (Claude Code)", **kwargs) -> Path:
        executable = _fake_claude(root, version_line, **kwargs)
        monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: str(executable))
        return executable

    return SimpleNamespace(root=root, install=install)


def _refusal(**kwargs) -> ClaudeCodeExecutableRefusal:
    with pytest.raises(ClaudeCodeExecutableRefusal) as raised:
        acpx_module._require_host_claude_code(adapter_label="AcpxClaudeShadowAdapter", **kwargs)
    return raised.value


# --- per-model floor (condition 2) -----------------------------------------


def test_opus_floor_lives_in_the_adapter_model_table_and_global_floor_is_unchanged():
    from scripts.review.isolation import CLAUDE_MIN_SUPPORTED_CLI_VERSION

    assert set(acpx_module.CLAUDE_ACP_MIN_CLAUDE_CODE_VERSIONS) <= acpx_module.CLAUDE_ACP_MODELS
    assert acpx_module.CLAUDE_ACP_MIN_CLAUDE_CODE_VERSIONS["claude-opus-5-5"] == (2, 1, 280)
    assert CLAUDE_MIN_SUPPORTED_CLI_VERSION == (2, 1, 116)
    assert acpx_module._claude_code_floor("claude-opus-5-5") == (2, 1, 280)
    assert acpx_module._claude_code_floor("claude-sonnet-5-5") == (2, 1, 116)
    assert acpx_module._claude_code_floor(None) == (2, 1, 116)


def test_host_claude_code_meeting_the_opus_floor_is_pinned_by_real_path(host):
    executable = host.install("2.1.280 (Claude Code)", name="2.1.280")
    metadata = acpx_module._require_host_claude_code(model="claude-opus-5-5", adapter_label="X")
    assert metadata["claude_code_executable"] == str(executable.resolve())
    assert metadata["claude_code_version"] == "2.1.280"
    assert metadata["claude_code_version_floor"] == "2.1.280"
    assert metadata["claude_code_executable_identity"] == acpx_module._claude_code_identity(executable.lstat())


def test_too_old_host_claude_code_is_a_typed_readable_refusal_for_opus_only(host):
    host.install("2.1.279 (Claude Code)", name="2.1.279")
    refusal = _refusal(model="claude-opus-5-5")
    assert isinstance(refusal, AcpxShadowRefusalError)
    assert refusal.reason == "too_old"
    assert refusal.failure_code == "acp_adapter_incompatible"
    assert "2.1.279" in str(refusal) and "2.1.280" in str(refusal) and "claude update" in str(refusal)
    # The same executable still serves a model without the Opus floor.
    assert acpx_module._require_host_claude_code(model="claude-sonnet-5-5", adapter_label="X")


@pytest.mark.parametrize(
    "version_line",
    ["Claude Code", "2.1", "2.1.296.4", "2.1." + "9" * 5000, "v99999.1.1"],
)
def test_unparseable_version_is_typed_never_a_value_error(host, version_line):
    host.install(version_line)
    refusal = _refusal(model="claude-opus-5-5")
    assert refusal.reason == "unparseable"
    assert refusal.failure_code == "acp_adapter_incompatible"


def test_failing_or_hanging_probe_is_typed(host, monkeypatch):
    host.install(exit_code=3)
    assert _refusal(model=None).reason == "probe_failed"

    host.install()

    def hang(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="claude --version", timeout=10)

    monkeypatch.setattr("scripts.utils.claude_version.run_version_probe", hang)
    assert _refusal(model=None).reason == "probe_failed"


def test_probe_uses_the_pinned_path_with_a_minimal_env(host, monkeypatch):
    executable = host.install()
    seen = {}

    def probe(cmd_prefix, *, timeout, env, stdin, **_kwargs):
        seen.update(cmd_prefix=list(cmd_prefix), env=env, stdin=stdin, timeout=timeout)
        return subprocess.CompletedProcess(cmd_prefix, 0, stdout="2.1.296 (Claude Code)\n", stderr="")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    monkeypatch.setattr("scripts.utils.claude_version.run_version_probe", probe)
    acpx_module._require_host_claude_code(model=None, adapter_label="X")
    assert seen["cmd_prefix"] == [str(executable.resolve())]
    assert set(seen["env"]) == {"PATH", "HOME"}
    assert seen["stdin"] == subprocess.DEVNULL


# --- resolution on every launch, vanish and replacement (conditions 1, 3) --


def test_missing_host_claude_code_is_refused_without_bundled_fallback(monkeypatch):
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: None)
    refusal = _refusal(model=None)
    assert refusal.reason == "missing"
    assert refusal.failure_code == "acp_adapter_missing"
    assert "bundled" in str(refusal)


def test_each_launch_resolves_the_current_auto_update_target(host, tmp_path, monkeypatch):
    old = _fake_claude(host.root, "2.1.290 (Claude Code)", name="2.1.290")
    new = _fake_claude(host.root, "2.1.296 (Claude Code)", name="2.1.296")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(mode=0o755)
    link = bin_dir / "claude"
    link.symlink_to(old)
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: str(link))

    first = acpx_module._require_host_claude_code(model=None, adapter_label="X")
    link.unlink()
    link.symlink_to(new)
    second = acpx_module._require_host_claude_code(model=None, adapter_label="X")

    assert first["claude_code_executable"] == str(old)
    assert second["claude_code_executable"] == str(new)
    assert second["claude_code_version"] == "2.1.296"


def test_executable_removed_during_probe_is_typed_vanished(host, monkeypatch):
    executable = host.install()

    def remove_then_spawn(cmd_prefix, **_kwargs):
        executable.unlink()
        raise FileNotFoundError(cmd_prefix[0])

    monkeypatch.setattr("scripts.utils.claude_version.run_version_probe", remove_then_spawn)
    refusal = _refusal(model=None)
    assert refusal.reason == "vanished"
    assert refusal.failure_code == "acp_adapter_missing"


def test_executable_replaced_during_probe_is_typed_vanished(host, monkeypatch):
    executable = host.install()

    def replace_then_answer(cmd_prefix, **_kwargs):
        executable.write_text("#!/bin/sh\necho replaced-binary-with-other-bytes\n", encoding="utf-8")
        return subprocess.CompletedProcess(cmd_prefix, 0, stdout="2.1.296 (Claude Code)\n", stderr="")

    monkeypatch.setattr("scripts.utils.claude_version.run_version_probe", replace_then_answer)
    refusal = _refusal(model=None)
    assert refusal.reason == "vanished"
    assert "changed during its version probe" in str(refusal)


# --- ownership, mode and symlink checks; open group-write policy (cond. 4) -


def test_strict_policy_refuses_a_group_writable_ancestor(host):
    host.install()
    (host.root / "share" / "claude").chmod(0o775)
    refusal = _refusal(model=None)
    assert refusal.reason == "untrusted_path"
    assert "group-writable" in str(refusal)


def test_strict_policy_is_the_default():
    assert acpx_module.CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE is False


def _fake_accounts(monkeypatch, *, members=(), primary_users=()):
    caller = SimpleNamespace(pw_name="caller", pw_uid=os.getuid(), pw_gid=os.getgid())
    others = [SimpleNamespace(pw_name=name, pw_uid=os.getuid() + 1 + index, pw_gid=os.getgid())
              for index, name in enumerate(primary_users)]
    monkeypatch.setattr(
        acpx_module,
        "pwd",
        SimpleNamespace(getpwuid=lambda _uid: caller, getpwall=lambda: [caller, *others]),
    )
    monkeypatch.setattr(acpx_module, "grp", SimpleNamespace(getgrgid=lambda _gid: SimpleNamespace(gr_mem=list(members))))


def test_private_group_policy_admits_the_callers_private_primary_group(host, monkeypatch):
    executable = host.install()
    (host.root / "share" / "claude").chmod(0o775)
    (host.root / "share" / "claude" / "versions").chmod(0o775)
    monkeypatch.setattr(acpx_module, "CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE", True)
    _fake_accounts(monkeypatch, members=("caller",))
    metadata = acpx_module._require_host_claude_code(model="claude-opus-5-5", adapter_label="X")
    assert metadata["claude_code_executable"] == str(executable.resolve())


@pytest.mark.parametrize(
    ("members", "primary_users"),
    [(("caller", "other"), ()), ((), ("other",))],
)
def test_private_group_policy_refuses_a_shared_group(host, monkeypatch, members, primary_users):
    host.install()
    (host.root / "share" / "claude").chmod(0o775)
    monkeypatch.setattr(acpx_module, "CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE", True)
    _fake_accounts(monkeypatch, members=members, primary_users=primary_users)
    assert "group-writable" in str(_refusal(model=None))


def test_private_group_policy_refuses_a_group_other_than_the_primary_one(monkeypatch):
    monkeypatch.setattr(acpx_module, "CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE", True)
    _fake_accounts(monkeypatch, members=("caller",))
    assert acpx_module._claude_code_group_write_permitted(os.getgid()) is True
    assert acpx_module._claude_code_group_write_permitted(os.getgid() + 1) is False


@pytest.mark.parametrize("allow_private_group_write", [False, True])
def test_world_writable_component_is_refused_under_either_policy(host, monkeypatch, allow_private_group_write):
    host.install()
    monkeypatch.setattr(acpx_module, "CLAUDE_CODE_ALLOW_PRIVATE_GROUP_WRITE", allow_private_group_write)
    _fake_accounts(monkeypatch, members=("caller",))
    (host.root / "share").chmod(0o757)
    assert "world-writable" in str(_refusal(model=None))


def test_writable_executable_is_refused(host):
    executable = host.install()
    executable.chmod(0o775)
    assert "group-writable" in str(_refusal(model=None))


def test_symlinked_ancestor_and_non_executable_file_are_refused(host, tmp_path):
    executable = host.install()
    alias = tmp_path / "alias"
    alias.symlink_to(host.root / "share", target_is_directory=True)
    linked = alias / "claude" / "versions" / executable.name
    with pytest.raises(ClaudeCodeExecutableRefusal, match="is a symlink"):
        acpx_module._require_trusted_claude_code_path(linked, adapter_label="X")
    executable.chmod(0o644)
    with pytest.raises(ClaudeCodeExecutableRefusal, match="not executable"):
        acpx_module._require_trusted_claude_code_path(executable, adapter_label="X")


def test_foreign_owner_is_refused():
    directory = os.stat_result((stat.S_IFDIR | 0o755, 1, 1, 1, os.getuid() + 4242, os.getgid(), 0, 0, 0, 0))
    root_owned = os.stat_result((stat.S_IFDIR | 0o755, 1, 1, 1, 0, 0, 0, 0, 0, 0))
    assert "neither the caller nor root" in acpx_module._claude_code_path_refusal(
        Path("/x"), directory, expect_dir=True
    )
    assert acpx_module._claude_code_path_refusal(Path("/"), root_owned, expect_dir=True) is None


# --- launch env, sealed review and refusal before spawn (conditions 1, 2) --


def _build(tmp_path, *, model="claude-opus-5-5", sealed=None):
    tool_config = {
        "acpx_discussion": True,
        "target_agent": "claude",
        "correlation_id": "corr-claude",
        "idempotency_key": "idem-claude",
        **({"sealed_review_mcp_config": sealed} if sealed else {}),
    }
    with acpx_module.active_discussion_scope():
        return AcpxClaudeShadowAdapter().build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model=model,
            task_id="t-claude",
            session_id=None,
            tool_config=tool_config,
        )


@pytest.mark.parametrize("sealed", [False, True])
def test_launch_env_pins_the_host_executable_over_caller_values(tmp_path, monkeypatch, sealed):
    _stub_binary(monkeypatch, tmp_path)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    sealed_config = None
    if sealed:
        sealed_config = str(tmp_path / "sealed-config.json")
        monkeypatch.setattr(acpx_module, "_validate_sealed_review_mcp_config", lambda raw, *, adapter_label: str(raw))
        monkeypatch.setattr(acpx_module, "_claude_sealed_review_max_turns", lambda _config: 9)

    plan = _build(tmp_path, sealed=sealed_config)

    # A caller export and an ambient secret never displace the launch values.
    monkeypatch.setenv("CLAUDE_CODE_EXECUTABLE", "/caller/bundled-claude")
    monkeypatch.setenv("CLAUDE_CODE_EFFORT_LEVEL", "low")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fixture-secret")
    env = build_agent_env(provider="acpx-claude-shadow", model="claude-opus-5-5", overrides=plan.env_overrides)
    assert env["CLAUDE_CODE_EXECUTABLE"] == "/installed/claude/versions/2.1.296"
    assert env["CLAUDE_CODE_EFFORT_LEVEL"] == "high"
    assert "ANTHROPIC_API_KEY" not in env
    assert env["PATH"] == plan.env_overrides["PATH"]
    assert plan.metadata["claude_code_version"] == "2.1.296"
    assert plan.metadata["claude_code_version_floor"] == "2.1.280"
    pairs = list(zip(plan.cmd, plan.cmd[1:], strict=False))
    if sealed:
        policy = json.loads(plan.cmd[plan.cmd.index("--permission-policy") + 1])
        assert policy["defaultAction"] == "deny"
        assert ("--allowed-tools", "mcp__sealed_review__read_required") in pairs
        assert ("--mcp-config", sealed_config) in pairs
    else:
        assert "--deny-all" in plan.cmd
        assert ("--allowed-tools", "") in pairs


def test_other_acp_seats_never_receive_the_claude_pin(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_EXECUTABLE", "/caller/claude")
    for provider in ("acpx-codex-shadow", "acpx-grok-shadow", "acpx-cursor-shadow"):
        assert "CLAUDE_CODE_EXECUTABLE" not in build_agent_env(provider=provider)


def test_too_old_host_refuses_the_opus_launch_before_any_plan(tmp_path, host, monkeypatch):
    _stub_binary(monkeypatch, tmp_path)
    # Keep the ACPX stubs but run the real host gate against the fake install.
    monkeypatch.setattr(acpx_module, "_require_host_claude_code", _REAL_GATE)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    host.install("2.1.279 (Claude Code)", name="2.1.279")

    with pytest.raises(ClaudeCodeExecutableRefusal, match=r"older than 2\.1\.280") as raised:
        _build(tmp_path, model="claude-opus-5-5")
    assert raised.value.reason == "too_old"
    assert _build(tmp_path, model="claude-sonnet-5-5").metadata["claude_code_version"] == "2.1.279"


# --- post-run attestation and vanish (conditions 3, 5) ---------------------


def _ok_stream(session_id: str = _SESSION_ID) -> str:
    events = [
        {"jsonrpc": "2.0", "id": 1, "method": "session/new", "params": {}},
        {"jsonrpc": "2.0", "id": 1, "result": {"sessionId": session_id}},
        {"jsonrpc": "2.0", "id": 2, "method": "session/prompt", "params": {}},
        {
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": session_id,
                "update": {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": "51"}},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "result": {"stopReason": "end_turn"}},
    ]
    return "\n".join(json.dumps(event) for event in events)


def _failed_stream() -> str:
    events = [
        {"jsonrpc": "2.0", "id": 1, "method": "session/new", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32603, "message": "Internal error", "data": {"details": "native binary not found"}},
        },
    ]
    return "\n".join(json.dumps(event) for event in events)


def _plan(executable: Path, *, version: str = "2.1.296") -> InvocationPlan:
    return InvocationPlan(
        cmd=["acpx"],
        cwd=executable.parent,
        stdin_payload="ping",
        output_file=None,
        env_overrides={},
        env_unsets=(),
        liveness_paths=(),
        metadata={
            "claude_code_executable": str(executable),
            "claude_code_executable_identity": acpx_module._claude_code_identity(executable.lstat()),
            "claude_code_version": version,
        },
    )


def _parse(plan: InvocationPlan, stdout: str, *, returncode: int = 0):
    return AcpxClaudeShadowAdapter().parse_response(
        stdout=stdout, stderr="", returncode=returncode, output_file=None, plan=plan
    )


def _transcript(home: Path, version: str) -> None:
    project = home / ".claude" / "projects" / "-some-worktree"
    project.mkdir(parents=True)
    lines = [
        {"type": "queue-operation", "sessionId": _SESSION_ID},
        {"type": "user", "version": version, "sessionId": _SESSION_ID},
    ]
    (project / f"{_SESSION_ID}.jsonl").write_text("\n".join(json.dumps(line) for line in lines), encoding="utf-8")


def test_child_transcript_version_attests_the_pinned_executable(host, tmp_path, monkeypatch):
    executable = host.install()
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _transcript(home, "2.1.296")
    plan = _plan(executable)
    parsed = _parse(plan, _ok_stream())
    assert parsed.ok is True
    assert parsed.response == "51"
    assert plan.metadata["claude_code_child_version"] == "2.1.296"
    assert plan.metadata["claude_code_child_attestation"] == "session-transcript"


def test_a_different_child_version_fails_closed(host, tmp_path, monkeypatch):
    executable = host.install()
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _transcript(home, "2.1.220")
    plan = _plan(executable)
    parsed = _parse(plan, _ok_stream())
    assert parsed.ok is False
    assert parsed.response == ""
    assert parsed.failure_code == "acp_adapter_incompatible"
    assert "2.1.220" in parsed.stderr_excerpt
    assert plan.metadata["claude_code_child_attestation"] == "mismatch"


def test_unobservable_child_is_recorded_unavailable_not_attested(host, tmp_path, monkeypatch):
    executable = host.install()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    plan = _plan(executable)
    assert _parse(plan, _ok_stream()).ok is True
    assert plan.metadata["claude_code_child_attestation"] == "unavailable"
    assert "claude_code_child_version" not in plan.metadata
    # A session id that is not a UUID is never used as a path component.
    plan = _plan(executable)
    assert _parse(plan, _ok_stream(session_id="../../etc/passwd")).ok is True
    assert plan.metadata["claude_code_child_attestation"] == "unavailable"


def test_executable_removed_between_probe_and_launch_is_typed(host):
    executable = host.install()
    plan = _plan(executable)
    executable.unlink()
    parsed = _parse(plan, _failed_stream(), returncode=1)
    assert parsed.ok is False
    assert parsed.failure_code == "acp_adapter_missing"
    assert "removed or replaced between the version probe and the launch" in parsed.stderr_excerpt
    assert "ENOENT" not in parsed.stderr_excerpt


def test_unrelated_failure_with_intact_executable_is_unchanged(host):
    executable = host.install()
    plan = _plan(executable)
    parsed = _parse(plan, _failed_stream(), returncode=1)
    plain = acpx_module.AcpxAdapter().parse_response(
        stdout=_failed_stream(), stderr="", returncode=1, output_file=None, plan=plan
    )
    assert parsed == plain


# --- sandbox (condition 6) -------------------------------------------------


@pytest.mark.parametrize("access", ["isolated", "full"])
def test_claude_acp_never_launches_inside_the_attempt_boundary(access):
    """No Claude ACP path enters the bwrap boundary, so no runtime_reads entry is needed."""
    from scripts.agent_runtime.attempt_boundary import prepare_attempt_boundary
    from scripts.review.isolation import ReviewIsolationError

    tool_config = {
        "review_id": "r",
        "attempt_id": "a",
        "review_manifest": "m",
        "review_input_root": "i",
        "mcp_config_path": "c",
        "strict_mcp_config": True,
        "review_access": access,
    }
    with pytest.raises(ReviewIsolationError, match="harness_unsupported"):
        prepare_attempt_boundary("acpx-claude-shadow", "read-only", None, tool_config)


@pytest.mark.parametrize("key", ["review_id", "review_isolation", "review_attempt_boundary", "attempt_os_sandbox"])
def test_claude_acp_adapter_refuses_boundary_tool_config(tmp_path, monkeypatch, key):
    _stub_binary(monkeypatch, tmp_path)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    with acpx_module.active_discussion_scope(), pytest.raises(AcpxShadowRefusalError, match="unsupported tool_config"):
        AcpxClaudeShadowAdapter().build_invocation(
            prompt="ping",
            mode="read-only",
            cwd=tmp_path,
            model="claude-opus-5-5",
            task_id="t-claude",
            session_id=None,
            tool_config={
                "acpx_discussion": True,
                "target_agent": "claude",
                "correlation_id": "c",
                "idempotency_key": "i",
                key: True,
            },
        )
