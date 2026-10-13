"""The ACP Claude seat pins and version-gates the host Claude Code (#10500)."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
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

# The suite's registered isolated worktree: ACPX refuses a primary-checkout cwd,
# and pytest's basetemp may sit inside the primary checkout.
_acpx_worktree = _acpx_tests._acpx_worktree


@pytest.fixture
def worktree_dir(_acpx_worktree):
    with TemporaryDirectory(prefix="claude-host-", dir=_acpx_worktree) as directory:
        yield Path(directory)

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
    # A private primary group by default, independent of the runner's accounts.
    _fake_accounts(monkeypatch, members=("caller",))

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


# --- ownership, mode and symlink checks; operator group-write rule (cond. 4)


def _fake_accounts(monkeypatch, *, members=(), primary_users=()):
    """Replace the account databases the live check reads; ``members`` are supplementary."""
    caller = SimpleNamespace(pw_name="caller", pw_uid=os.getuid(), pw_gid=os.getgid())
    others = [
        SimpleNamespace(pw_name=name, pw_uid=os.getuid() + 1 + index, pw_gid=os.getgid())
        for index, name in enumerate(primary_users)
    ]
    monkeypatch.setattr(
        acpx_module,
        "pwd",
        SimpleNamespace(getpwuid=lambda _uid: caller, getpwall=lambda: [caller, *others]),
    )
    monkeypatch.setattr(acpx_module, "grp", SimpleNamespace(getgrgid=lambda _gid: SimpleNamespace(gr_mem=list(members))))


def _group_writable_ancestors(host) -> None:
    """The native-install layout: 0775 directories above a 0755 versioned binary."""
    for directory in (host.root, host.root / "share", host.root / "share" / "claude",
                      host.root / "share" / "claude" / "versions"):
        directory.chmod(0o775)


def test_private_primary_group_write_is_accepted(host):
    executable = host.install()
    _group_writable_ancestors(host)
    metadata = acpx_module._require_host_claude_code(model="claude-opus-5-5", adapter_label="X")
    assert metadata["claude_code_executable"] == str(executable.resolve())


@pytest.mark.parametrize(
    ("members", "primary_users"),
    [(("caller", "other"), ()), (("other",), ()), ((), ("other",))],
    ids=["supplementary-member", "only-another-member", "another-primary-user"],
)
def test_group_write_with_another_member_is_rejected(host, monkeypatch, members, primary_users):
    host.install()
    _group_writable_ancestors(host)
    _fake_accounts(monkeypatch, members=members, primary_users=primary_users)
    refusal = _refusal(model=None)
    assert refusal.reason == "untrusted_path"
    assert "group-writable" in str(refusal)


def test_group_write_by_a_group_other_than_the_primary_one_is_rejected():
    assert acpx_module._claude_code_group_write_permitted(os.getgid()) is True
    assert acpx_module._claude_code_group_write_permitted(os.getgid() + 1) is False


def test_group_membership_is_checked_live_on_every_launch(host, monkeypatch):
    host.install()
    _group_writable_ancestors(host)
    assert acpx_module._require_host_claude_code(model=None, adapter_label="X")
    _fake_accounts(monkeypatch, members=("caller", "other"))
    assert "group-writable" in str(_refusal(model=None))


def test_world_write_is_rejected(host):
    host.install()
    (host.root / "share").chmod(0o777)
    refusal = _refusal(model=None)
    assert refusal.reason == "untrusted_path"
    assert "world-writable" in str(refusal)


def test_group_writable_executable_is_rejected_even_in_a_private_group(host):
    executable = host.install()
    executable.chmod(0o775)
    assert "group-writable" in str(_refusal(model=None))


def test_symlink_is_rejected(host, tmp_path):
    executable = host.install()
    alias = tmp_path / "alias"
    alias.symlink_to(host.root / "share", target_is_directory=True)
    linked = alias / "claude" / "versions" / executable.name
    with pytest.raises(ClaudeCodeExecutableRefusal, match="is a symlink") as raised:
        acpx_module._require_unshared_claude_code_path(linked, adapter_label="X")
    assert raised.value.reason == "untrusted_path"


def test_non_executable_file_is_rejected(host):
    executable = host.install()
    executable.chmod(0o644)
    with pytest.raises(ClaudeCodeExecutableRefusal, match="not executable"):
        acpx_module._require_unshared_claude_code_path(executable, adapter_label="X")


def test_foreign_owner_is_rejected(host, monkeypatch):
    executable = host.install()
    foreign_dir = host.root / "share" / "claude"
    real_lstat = Path.lstat

    def lstat(path):
        result = real_lstat(path)
        if path == foreign_dir:
            fields = list(result)
            fields[stat.ST_UID] = os.getuid() + 4242
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(Path, "lstat", lstat)
    refusal = _refusal(model=None)
    assert refusal.reason == "untrusted_path"
    assert "neither the caller nor root" in str(refusal)
    root_owned = os.stat_result((stat.S_IFDIR | 0o755, 1, 1, 1, 0, 0, 0, 0, 0, 0))
    assert acpx_module._claude_code_path_refusal(Path("/"), root_owned, expect_dir=True) is None
    assert executable.exists()


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
def test_launch_env_pins_the_host_executable_over_caller_values(worktree_dir, monkeypatch, sealed):
    tmp_path = worktree_dir
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
    monkeypatch.setenv("LU_CLAUDE_ACP_HOST", "/caller/claude")
    env = build_agent_env(provider="acpx-claude-shadow", model="claude-opus-5-5", overrides=plan.env_overrides)
    assert env["CLAUDE_CODE_EXECUTABLE"] == "/repo/claude_acp_exec.sh"
    assert env["LU_CLAUDE_ACP_HOST"] == "/installed/claude/versions/2.1.296"
    assert env["LU_CLAUDE_ACP_HOST_IDENTITY"] == "1:2:3:4:5"
    assert plan.metadata["claude_code_launcher"] == "/repo/claude_acp_exec.sh"
    assert env["CLAUDE_CODE_EFFORT_LEVEL"] == "high"
    assert env["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    assert env["CLAUDE_CODE_DISABLE_ADVISOR_TOOL"] == "1"
    assert env["CLAUDE_CODE_DISABLE_CRON"] == "1"
    assert env["CLAUDE_CODE_DISABLE_WORKFLOWS"] == "1"
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


def test_too_old_host_refuses_the_opus_launch_before_any_plan(worktree_dir, host, monkeypatch):
    tmp_path = worktree_dir
    _stub_binary(monkeypatch, tmp_path)
    # Keep the ACPX stubs but run the real host gate against the fake install.
    monkeypatch.setattr(acpx_module, "_require_host_claude_code", _REAL_GATE)
    monkeypatch.setattr(acpx_module, "_require_claude_acp_launcher", lambda *, adapter_label: "/repo/launcher")
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
def test_claude_acp_adapter_refuses_boundary_tool_config(worktree_dir, monkeypatch, key):
    tmp_path = worktree_dir
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


# --- repo-owned launcher (approved design, #10500) --------------------------

_LAUNCHER = Path(acpx_module.__file__).resolve().parents[1] / "claude_acp_exec.sh"
_SDK_ARGS = [
    "--output-format",
    "stream-json",
    "--verbose",
    "--input-format",
    "stream-json",
    "--disallowedTools",
    "AskUserQuestion",
]


def _dumping_claude(directory: Path) -> Path:
    """A fake host binary that records its argv and environment."""
    directory.mkdir(parents=True, exist_ok=True)
    fake = directory / "claude"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "json.dump({'argv': sys.argv, 'env': dict(os.environ)}, open(os.environ['LU_TEST_DUMP'], 'w'))\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    return fake


def _run_launcher(tmp_path: Path, *, host: str | None, identity: str | None):
    dump = tmp_path / "dump.json"
    env = {"PATH": "/usr/bin:/bin", "LU_TEST_DUMP": str(dump)}
    if host is not None:
        env["LU_CLAUDE_ACP_HOST"] = host
    if identity is not None:
        env["LU_CLAUDE_ACP_HOST_IDENTITY"] = identity
    proc = subprocess.run(
        [str(_LAUNCHER), *_SDK_ARGS], env=env, capture_output=True, text=True, timeout=30, check=False
    )
    return proc, dump


def test_launcher_deny_list_equals_the_headless_background_denies():
    from scripts.agent_runtime.adapters.claude import HEADLESS_BACKGROUND_TOOL_DENIES

    text = _LAUNCHER.read_text(encoding="utf-8")
    exec_lines = [line for line in text.splitlines() if line.startswith("exec ")]
    assert exec_lines == ['exec "$host" --disallowedTools ' + ",".join(HEADLESS_BACKGROUND_TOOL_DENIES) + ' "$@"']
    assert text.startswith("#!/bin/sh\n")
    assert "eval" not in text


def test_launcher_execs_the_pinned_binary_with_merged_denies_and_a_clean_env(tmp_path):
    fake = _dumping_claude(tmp_path / "host")
    proc, dump = _run_launcher(tmp_path, host=str(fake), identity=acpx_module._claude_code_launch_identity(fake.stat()))
    assert proc.returncode == 0, proc.stderr
    record = json.loads(dump.read_text(encoding="utf-8"))
    assert record["argv"][1:] == [
        "--disallowedTools",
        "Monitor,ScheduleWakeup,CronCreate,Workflow",
        *_SDK_ARGS,
    ]
    assert "LU_CLAUDE_ACP_HOST" not in record["env"]
    assert "LU_CLAUDE_ACP_HOST_IDENTITY" not in record["env"]


@pytest.mark.parametrize(
    ("host", "identity", "message"),
    [
        (None, "1:2:3:4:5", "missing or relative"),
        ("relative/claude", "1:2:3:4:5", "missing or relative"),
        ("HOST", None, "identity is missing"),
        ("HOST", "1:2", "identity is missing"),
        ("HOST", "0:0:0:0:0", "changed since its version probe"),
    ],
)
def test_launcher_refuses_without_executing(tmp_path, host, identity, message):
    fake = _dumping_claude(tmp_path / "host")
    proc, dump = _run_launcher(tmp_path, host=str(fake) if host == "HOST" else host, identity=identity)
    assert proc.returncode == 126
    assert message in proc.stderr
    assert not dump.exists()


_LAUNCHER_REL = Path("scripts/agent_runtime/claude_acp_exec.sh")
_REAL_LAUNCHER_GATE = acpx_module._require_claude_acp_launcher


def _git(cwd: Path, *args: str) -> None:
    from scripts.common.git_context import sanitized_git_env

    env = {**sanitized_git_env(), "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
         "-c", "commit.gpgsign=false", "-c", f"core.hooksPath={os.devnull}", *args],
        cwd=cwd, env=env, check=True, capture_output=True, timeout=30,
    )


@pytest.fixture
def launcher_checkouts(tmp_path, monkeypatch):
    """A primary checkout and its dispatch worktree, each with a mode-clean launcher copy.

    The adapter anchor is the worktree, as for an ordinary ask whose adapter code
    runs from the caller's worktree; its git links name the primary.
    """
    root = tmp_path.resolve()
    primary = root / "primary"
    primary.mkdir()
    _git(primary, "init", "-q", "-b", "main")
    (primary / _LAUNCHER_REL).parent.mkdir(parents=True)
    (primary / _LAUNCHER_REL).write_bytes(_LAUNCHER.read_bytes())
    _git(primary, "add", "scripts")
    _git(primary, "commit", "-q", "-m", "fixture")
    worktree = primary / ".worktrees" / "dispatch" / "agent" / "task"
    _git(primary, "worktree", "add", "-q", "-b", "task", str(worktree))
    for checkout in (primary, worktree):
        for directory in (checkout, checkout / "scripts", checkout / "scripts" / "agent_runtime"):
            directory.chmod(0o755)
        (checkout / _LAUNCHER_REL).chmod(0o755)
    root.chmod(0o700)
    copies = root / "copies"
    # Unrelated unreadable host processes must not decide these copy lifecycle tests.
    proc = root / "proc"
    proc.mkdir()
    (proc / str(os.getpid())).symlink_to(Path("/proc") / str(os.getpid()), target_is_directory=True)
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_PROC_ROOT", proc)
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_ANCHOR", worktree)
    monkeypatch.setattr(acpx_module, "_CLAUDE_CODE_TRUST_ROOT", root)
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_COPY_BASE", copies)
    _fake_accounts(monkeypatch, members=("caller",))
    return SimpleNamespace(
        root=root,
        primary=primary,
        worktree=worktree,
        copies=copies,
        proc=proc,
        launcher=primary / _LAUNCHER_REL,
        worktree_launcher=worktree / _LAUNCHER_REL,
    )


def _launcher_refusal() -> ClaudeCodeExecutableRefusal:
    with pytest.raises(ClaudeCodeExecutableRefusal) as raised:
        acpx_module._require_claude_acp_launcher(adapter_label="X")
    return raised.value


def _accepted_copy(checkouts) -> Path:
    """Run the gate; prove it returns a fresh private copy of the pinned bytes."""
    copy = Path(acpx_module._require_claude_acp_launcher(adapter_label="X"))
    copy_dir = copy.parents[len(_LAUNCHER_REL.parts) - 1]
    assert copy == copy_dir / _LAUNCHER_REL
    assert copy_dir.parent == checkouts.copies
    assert copy_dir.name.startswith("launch-")
    assert stat.S_IMODE(copy_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(copy.stat().st_mode) == 0o500
    pinned = acpx_module._CLAUDE_ACP_LAUNCHER_CLOSURE[acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH]
    assert hashlib.sha256(copy.read_bytes()).hexdigest() == pinned
    return copy


def test_the_pin_is_the_digest_of_the_tracked_self_contained_launcher():
    """Launcher bytes and the adapter's pinned digest change in the same commit."""
    closure = acpx_module._CLAUDE_ACP_LAUNCHER_CLOSURE
    assert list(closure) == [acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH]
    assert Path(*acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH.parts) == _LAUNCHER_REL
    assert closure[acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH] == hashlib.sha256(_LAUNCHER.read_bytes()).hexdigest()
    # Self-contained: it sources no file and execs only the pinned host binary.
    lines = [line.strip() for line in _LAUNCHER.read_text(encoding="utf-8").splitlines()]
    assert not [line for line in lines if line.startswith((". ", "source "))]
    assert [line for line in lines if line.startswith("exec ")] == [
        'exec "$host" --disallowedTools Monitor,ScheduleWakeup,CronCreate,Workflow "$@"'
    ]


def test_launcher_loads_from_the_primary_checkout_not_the_callers_worktree(launcher_checkouts):
    worktree_copy = launcher_checkouts.worktree_launcher
    assert worktree_copy.read_bytes() == launcher_checkouts.launcher.read_bytes()
    assert stat.S_IMODE(worktree_copy.stat().st_mode) == 0o755
    assert acpx_module._claude_acp_primary_checkout(adapter_label="X") == launcher_checkouts.primary
    _accepted_copy(launcher_checkouts)
    # The worktree copy is never read: an unreadable one changes nothing.
    worktree_copy.chmod(0o000)
    _accepted_copy(launcher_checkouts)


def test_a_clean_worktree_copy_never_stands_in_for_a_missing_primary_launcher(launcher_checkouts):
    launcher_checkouts.launcher.unlink()
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("missing", "acp_adapter_missing")
    assert "pull main there" in str(refusal)
    assert not list(launcher_checkouts.copies.glob("launch-*"))


@pytest.mark.parametrize(
    "error",
    [
        acpx_module.NotAGitRepositoryError("fixture"),
        PermissionError(13, "Permission denied"),
        OSError(5, "Input/output error"),
        RuntimeError("fixture"),
    ],
)
def test_every_primary_resolution_failure_is_a_typed_missing_refusal(launcher_checkouts, monkeypatch, error):
    def unresolvable(_start):
        raise error

    monkeypatch.setattr(acpx_module, "resolve_main_root_without_git", unresolvable)
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("missing", "acp_adapter_missing")
    assert type(error).__name__ in str(refusal)


@pytest.mark.parametrize(
    "corrupt",
    ["gitdir: /elsewhere/.git\n", "not a git link\n", "", "gitdir: ../../../../.git/worktrees/missing\n"],
)
def test_a_worktree_with_corrupt_git_links_is_a_typed_missing_refusal(launcher_checkouts, corrupt):
    (launcher_checkouts.worktree / ".git").write_text(corrupt, encoding="utf-8")
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("missing", "acp_adapter_missing")


def test_a_worktree_link_without_the_back_link_is_refused(launcher_checkouts):
    """A forged .git file must be confirmed by the gitdir that it names."""
    link = (launcher_checkouts.worktree / ".git").read_text(encoding="utf-8").removeprefix("gitdir:").strip()
    (Path(link) / "gitdir").write_text("/somewhere/else/.git\n", encoding="utf-8")
    assert _launcher_refusal().reason == "missing"


def _launch_identity(path: Path) -> str:
    """Device, inode, size and nanosecond mtime and ctime, as the launcher's GNU stat prints them."""
    st = path.lstat()
    times = [f"{ns // 10**9}.{ns % 10**9:09d}" for ns in (st.st_mtime_ns, st.st_ctime_ns)]
    return f"{st.st_dev}:{st.st_ino}:{st.st_size}:{times[0]}:{times[1]}"


# The launcher's choice: GNU stat, installed as gnustat where stat is uutils.
_GNU_STAT = "/usr/bin/gnustat" if os.access("/usr/bin/gnustat", os.X_OK) else "/usr/bin/stat"


def _hostile_git(directory: Path, answer: Path, marker: Path) -> Path:
    """A git on PATH that records it ran and names the worktree as the shared store."""
    directory.mkdir(parents=True, exist_ok=True)
    shim = directory / "git"
    shim.write_text(f"#!/bin/sh\n: > '{marker}'\nprintf '%s\\n' '{answer}'\n", encoding="utf-8")
    shim.chmod(0o755)
    return shim


def test_environment_cwd_and_a_hostile_git_on_path_never_redirect_the_launcher(launcher_checkouts, monkeypatch):
    worktree = launcher_checkouts.worktree
    worktree_git_dir = (worktree / ".git").read_text(encoding="utf-8").removeprefix("gitdir:").strip()
    marker = launcher_checkouts.root / "hostile-git-ran"
    shim = _hostile_git(launcher_checkouts.root / "hostile-bin", worktree / ".git", marker)
    for name, value in {
        "GIT_DIR": worktree_git_dir,
        "GIT_WORK_TREE": str(worktree),
        "GIT_COMMON_DIR": worktree_git_dir,
        "CLAUDE_CODE_EXECUTABLE": str(launcher_checkouts.worktree_launcher),
        "PATH": f"{shim.parent}{os.pathsep}{launcher_checkouts.worktree_launcher.parent}{os.pathsep}/usr/bin:/bin",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(worktree)
    returned = Path(acpx_module._require_claude_acp_launcher(adapter_label="X"))
    assert not marker.exists(), "the launcher gate ran a PATH-searched git"
    assert not returned.is_relative_to(worktree)
    _accepted_copy(launcher_checkouts)
    assert acpx_module._claude_acp_primary_checkout(adapter_label="X") == launcher_checkouts.primary


def test_an_unusable_git_on_path_does_not_affect_resolution(launcher_checkouts, monkeypatch):
    """The only git on PATH cannot execute (PermissionError); no git is needed."""
    bad = launcher_checkouts.root / "bad-bin"
    bad.mkdir()
    (bad / "git").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (bad / "git").chmod(0o644)
    monkeypatch.setenv("PATH", str(bad))
    _accepted_copy(launcher_checkouts)


def test_post_hash_replacement_of_the_primary_launcher_never_executes(launcher_checkouts, tmp_path):
    """Execution is bound to the verified bytes, not to the checkout path."""
    copy = Path(acpx_module._require_claude_acp_launcher(adapter_label="X"))
    unpinned_marker = tmp_path / "unpinned-ran"
    replacement = launcher_checkouts.launcher.with_name("replacement.sh")
    replacement.write_text(f"#!/bin/sh\n: > '{unpinned_marker}'\n", encoding="utf-8")
    replacement.chmod(0o755)
    os.replace(replacement, launcher_checkouts.launcher)

    fake = _dumping_claude(tmp_path / "host")
    dump = tmp_path / "dump.json"
    proc = subprocess.run(
        [str(copy), *_SDK_ARGS],
        env={
            "PATH": "/usr/bin:/bin",
            "LU_TEST_DUMP": str(dump),
            "LU_CLAUDE_ACP_HOST": str(fake),
            "LU_CLAUDE_ACP_HOST_IDENTITY": _launch_identity(fake),
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert not unpinned_marker.exists(), "the replaced checkout launcher executed"
    assert proc.returncode == 0, proc.stderr
    assert json.loads(dump.read_text(encoding="utf-8"))["argv"][1:3] == [
        "--disallowedTools",
        "Monitor,ScheduleWakeup,CronCreate,Workflow",
    ]
    assert copy.parents[2].parent == launcher_checkouts.copies


def test_each_launch_gets_its_own_copy_and_cleanup_removes_only_it(launcher_checkouts):
    first = _accepted_copy(launcher_checkouts)
    second = _accepted_copy(launcher_checkouts)
    assert first.parents[2] != second.parents[2]
    plan = SimpleNamespace(metadata={"claude_code_launcher": str(first)})
    AcpxClaudeShadowAdapter().cleanup_invocation(plan)
    assert not first.parents[2].exists()
    assert second.exists()
    # A path outside the copy base is never removed.
    acpx_module._remove_claude_acp_launcher_copy(str(launcher_checkouts.launcher))
    acpx_module._remove_claude_acp_launcher_copy("/repo/claude_acp_exec.sh")
    acpx_module._remove_claude_acp_launcher_copy(None)
    assert launcher_checkouts.launcher.exists()


def test_stale_copies_are_swept_and_fresh_ones_kept(launcher_checkouts):
    stale = _accepted_copy(launcher_checkouts).parents[2]
    fresh = _accepted_copy(launcher_checkouts).parents[2]
    old = time.time() - acpx_module._CLAUDE_ACP_LAUNCHER_COPY_MAX_AGE_S - 60
    os.utime(stale, (old, old))
    _accepted_copy(launcher_checkouts)
    assert not stale.exists()
    assert fresh.exists()


def _stale_entry(directory: Path, name: str = "launch-abcdefgh", *, mode: int = 0o700) -> Path:
    """An entry older than any ask, holding one unrelated file."""
    entry = directory / name
    entry.mkdir(parents=True)
    (entry / "payload").write_text("unrelated", encoding="utf-8")
    entry.chmod(mode)
    old = time.time() - acpx_module._CLAUDE_ACP_LAUNCHER_COPY_MAX_AGE_S - 60
    os.utime(entry, (old, old))
    return entry


@contextlib.contextmanager
def _held_open(path: Path, proc_root: Path):
    """Another live process holds ``path`` open for the duration."""
    with path.open("rb") as handle:
        holder = subprocess.Popen(["sleep", "300"], stdin=handle)
    process = proc_root / str(holder.pid)
    process.symlink_to(Path("/proc") / str(holder.pid), target_is_directory=True)
    try:
        yield holder
    finally:
        holder.kill()
        holder.wait(timeout=30)
        process.unlink()


def test_a_symlinked_copy_base_is_refused_before_anything_in_it_is_removed(launcher_checkouts):
    elsewhere = launcher_checkouts.root / "elsewhere"
    elsewhere.mkdir(mode=0o700)
    payload = _stale_entry(elsewhere)
    launcher_checkouts.copies.symlink_to(elsewhere, target_is_directory=True)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert "the directory is a symlink" in str(refusal)
    assert (payload / "payload").exists()
    assert [entry.name for entry in elsewhere.iterdir()] == [payload.name]


@pytest.mark.parametrize(("mode", "message"), [(0o777, "world-writable"), (0o770, "group-writable")])
def test_a_copy_base_others_can_write_is_refused_before_the_sweep(launcher_checkouts, monkeypatch, mode, message):
    _fake_accounts(monkeypatch, members=("caller", "other"))
    launcher_checkouts.copies.mkdir(mode=0o700)
    payload = _stale_entry(launcher_checkouts.copies)
    launcher_checkouts.copies.chmod(mode)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert message in str(refusal)
    assert [entry.name for entry in launcher_checkouts.copies.iterdir()] == [payload.name]


def test_a_copy_base_that_is_not_a_directory_is_refused(launcher_checkouts):
    launcher_checkouts.copies.write_text("not a directory", encoding="utf-8")
    launcher_checkouts.copies.chmod(0o600)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert "the directory is not a directory" in str(refusal)


def test_a_copy_base_owned_by_another_account_is_refused_before_the_sweep(launcher_checkouts, monkeypatch):
    """The caller does not own the base, so nothing in it is touched."""
    launcher_checkouts.copies.mkdir(mode=0o700)
    payload = _stale_entry(launcher_checkouts.copies)
    real_uid = os.getuid()
    monkeypatch.setattr(acpx_module.os, "getuid", lambda: real_uid + 1)
    with pytest.raises(ClaudeCodeExecutableRefusal) as raised:
        acpx_module._private_claude_acp_launcher_copy(
            {acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH: b"#!/bin/sh\n"}, adapter_label="X"
        )
    monkeypatch.undo()
    assert raised.value.reason == "untrusted_path"
    assert "owned by uid" in str(raised.value)
    assert [entry.name for entry in launcher_checkouts.copies.iterdir()] == [payload.name]


def test_the_sweep_removes_only_stale_copies_it_provably_owns(launcher_checkouts):
    copies = launcher_checkouts.copies
    copies.mkdir(mode=0o700)
    owned = _stale_entry(copies, "launch-aaaaaaaa")
    other_mode = _stale_entry(copies, "launch-bbbbbbbb", mode=0o755)
    other_name = _stale_entry(copies, "launch-not-a-copy")
    regular = copies / "launch-cccccccc"
    regular.write_text("x", encoding="utf-8")
    old = time.time() - acpx_module._CLAUDE_ACP_LAUNCHER_COPY_MAX_AGE_S - 60
    os.utime(regular, (old, old))
    _accepted_copy(launcher_checkouts)
    assert not owned.exists()
    assert other_mode.exists() and other_name.exists() and regular.exists()


def test_the_sweep_keeps_a_stale_copy_a_live_process_holds(launcher_checkouts):
    copy = _accepted_copy(launcher_checkouts)
    stale = copy.parents[2]
    old = time.time() - acpx_module._CLAUDE_ACP_LAUNCHER_COPY_MAX_AGE_S - 60
    os.utime(stale, (old, old))
    with _held_open(copy, launcher_checkouts.proc):
        _accepted_copy(launcher_checkouts)
        assert copy.exists()
    _accepted_copy(launcher_checkouts)
    assert not stale.exists()


def test_cleanup_leaves_a_held_copy_and_reports_it_typed_and_logged(launcher_checkouts, caplog):
    copy = _accepted_copy(launcher_checkouts)
    with _held_open(copy, launcher_checkouts.proc), pytest.raises(acpx_module.ClaudeAcpLauncherCleanupError) as raised:
        acpx_module._remove_claude_acp_launcher_copy(str(copy))
    assert raised.value.reason == "cleanup_busy"
    assert copy.exists()
    assert "a live process still holds it" in caplog.text
    _assert_path_free(str(raised.value), launcher_checkouts.root)
    acpx_module._remove_claude_acp_launcher_copy(str(copy))
    assert not copy.parents[2].exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="root removes any entry")
def test_a_copy_that_cannot_be_removed_is_a_typed_logged_failure(launcher_checkouts, caplog):
    copy = _accepted_copy(launcher_checkouts)
    copy.parent.chmod(0o500)
    try:
        with pytest.raises(acpx_module.ClaudeAcpLauncherCleanupError) as raised:
            acpx_module._remove_claude_acp_launcher_copy(str(copy))
        assert copy.exists()
    finally:
        copy.parent.chmod(0o700)
    assert (raised.value.reason, raised.value.failure_code) == ("cleanup_failed", "acp_adapter_incompatible")
    assert "Permission denied" in str(raised.value)
    assert "cannot remove private launcher copy" in caplog.text


@pytest.mark.parametrize("code", [errno.ENOSPC, errno.EBUSY])
def test_a_removal_error_is_a_typed_failure(launcher_checkouts, monkeypatch, code):
    copy = _accepted_copy(launcher_checkouts)

    def fail(path, *, dir_fd, onexc):
        onexc(os.rmdir, path, OSError(code, os.strerror(code)))

    monkeypatch.setattr(acpx_module.shutil, "rmtree", fail)
    with pytest.raises(acpx_module.ClaudeAcpLauncherCleanupError) as raised:
        acpx_module._remove_claude_acp_launcher_copy(str(copy))
    monkeypatch.undo()
    assert raised.value.reason == "cleanup_failed"
    assert os.strerror(code) in str(raised.value)
    assert copy.exists()


def _copy_plan(copy: Path) -> InvocationPlan:
    return InvocationPlan(
        cmd=["acpx"],
        cwd=copy.parent,
        stdin_payload="ping",
        output_file=None,
        env_overrides={},
        env_unsets=(),
        liveness_paths=(),
        metadata={"claude_code_launcher": str(copy)},
    )


def test_parsing_removes_the_copy_and_the_final_cleanup_is_a_no_op(launcher_checkouts):
    copy = _accepted_copy(launcher_checkouts)
    plan = _copy_plan(copy)
    parsed = _parse(plan, _ok_stream())
    assert (parsed.ok, parsed.response) == (True, "51")
    assert not copy.parents[2].exists()
    assert plan.metadata["claude_code_launcher_cleanup"] == "removed"
    AcpxClaudeShadowAdapter().cleanup_invocation(plan)


def test_a_copy_left_after_the_ask_fails_the_parsed_result(launcher_checkouts, caplog):
    """The failure reaches the result, which the runner writes to the receipt."""
    copy = _accepted_copy(launcher_checkouts)
    plan = _copy_plan(copy)
    with _held_open(copy, launcher_checkouts.proc):
        parsed = _parse(plan, _ok_stream())
    assert (parsed.ok, parsed.response, parsed.failure_code) == (False, "", "acp_adapter_incompatible")
    assert "a live process still holds it" in parsed.stderr_excerpt
    assert plan.metadata["claude_code_launcher_cleanup"] == "cleanup_busy"
    assert "a live process still holds it" in caplog.text
    _assert_path_free(parsed.stderr_excerpt, launcher_checkouts.root)
    # The runner's final cleanup retries once the holder has exited.
    AcpxClaudeShadowAdapter().cleanup_invocation(plan)
    assert not copy.parents[2].exists()


@pytest.mark.parametrize(
    "visibility",
    ["held", "fd_denied", "link_denied", "owner_denied", "foreign", "exited_enoent", "exited_esrch", "free"],
)
def test_cleanup_refuses_unknown_holders_and_reports_the_failure(launcher_checkouts, monkeypatch, caplog, visibility):
    copy = _accepted_copy(launcher_checkouts)
    plan = _copy_plan(copy)
    proc = launcher_checkouts.root / "synthetic-proc"
    process = proc / "123"
    fds = process / "fd"
    fds.mkdir(parents=True)
    for name in ("cwd", "root", "exe"):
        (process / name).symlink_to(launcher_checkouts.root)
    if visibility not in {"free", "exited_enoent", "exited_esrch"}:
        (fds / "0").symlink_to(copy)
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_PROC_ROOT", proc)
    real_listdir, real_readlink, real_stat = os.listdir, os.readlink, Path.stat

    def listdir(path):
        if path == fds:
            if visibility in {"fd_denied", "foreign"}:
                raise PermissionError(errno.EACCES, "Permission denied")
            if visibility in {"exited_enoent", "exited_esrch"}:
                code = errno.ENOENT if visibility == "exited_enoent" else errno.ESRCH
                raise OSError(code, os.strerror(code))
        return real_listdir(path)

    def readlink(path, *args, **kwargs):
        if path == fds / "0" and visibility == "link_denied":
            raise PermissionError(errno.EACCES, "Permission denied")
        return real_readlink(path, *args, **kwargs)

    def process_stat(path, *args, **kwargs):
        if path == process:
            if visibility == "owner_denied":
                raise PermissionError(errno.EACCES, "Permission denied")
            if visibility == "foreign":
                return SimpleNamespace(st_uid=os.getuid() + 1)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(acpx_module.os, "listdir", listdir)
    monkeypatch.setattr(acpx_module.os, "readlink", readlink)
    monkeypatch.setattr(Path, "stat", process_stat)
    parsed = _parse(plan, _ok_stream())
    if visibility in {"held", "fd_denied", "link_denied", "owner_denied"}:
        message = "a live process still holds it" if visibility == "held" else "the process table is unreadable"
        assert (parsed.ok, parsed.response, parsed.failure_code) == (False, "", "acp_adapter_incompatible")
        assert plan.metadata["claude_code_launcher_cleanup"] == "cleanup_busy"
        assert message in parsed.stderr_excerpt
        assert message in caplog.text
        with pytest.raises(acpx_module.ClaudeAcpLauncherCleanupError) as raised:
            AcpxClaudeShadowAdapter().cleanup_invocation(plan)
        assert raised.value.reason == "cleanup_busy"
        assert copy.exists()
    else:
        assert (parsed.ok, parsed.response) == (True, "51")
        assert plan.metadata["claude_code_launcher_cleanup"] == "removed"
        assert not copy.parents[2].exists()


@pytest.mark.parametrize(("mode", "message"), [(0o777, "world-writable"), (0o775, "group-writable")])
def test_an_unsafe_copy_base_is_refused_and_leaves_no_copy(launcher_checkouts, monkeypatch, mode, message):
    launcher_checkouts.copies.mkdir(mode=0o700)
    launcher_checkouts.copies.chmod(mode)
    _fake_accounts(monkeypatch, members=("caller", "other"))
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert message in str(refusal)
    assert not list(launcher_checkouts.copies.glob("launch-*"))


@pytest.mark.skipif(os.geteuid() == 0, reason="root writes any directory")
def test_an_unwritable_copy_base_is_a_typed_copy_failure(launcher_checkouts):
    launcher_checkouts.copies.mkdir(mode=0o500)
    try:
        refusal = _launcher_refusal()
    finally:
        launcher_checkouts.copies.chmod(0o700)
    assert (refusal.reason, refusal.failure_code) == ("copy_failed", "acp_adapter_incompatible")


def test_launcher_with_private_group_parents_is_accepted(launcher_checkouts):
    (launcher_checkouts.primary / "scripts").chmod(0o775)
    _accepted_copy(launcher_checkouts)


@pytest.mark.parametrize(("mode", "message"), [(0o775, "group-writable"), (0o757, "world-writable")])
def test_group_or_world_writable_launcher_is_refused(launcher_checkouts, mode, message):
    launcher_checkouts.launcher.chmod(mode)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert message in str(refusal)


def test_world_writable_launcher_parent_is_refused(launcher_checkouts):
    (launcher_checkouts.primary / "scripts").chmod(0o777)
    assert "world-writable" in str(_launcher_refusal())


def test_launcher_parent_writable_by_a_shared_group_is_refused(launcher_checkouts, monkeypatch):
    (launcher_checkouts.primary / "scripts").chmod(0o775)
    _fake_accounts(monkeypatch, members=("caller", "other"))
    assert "group-writable" in str(_launcher_refusal())


def test_symlinked_launcher_is_refused(launcher_checkouts):
    launcher = launcher_checkouts.launcher
    target = launcher.with_name("real.sh")
    launcher.rename(target)
    launcher.symlink_to(target)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert "the file is a symlink" in str(refusal)


def test_symlinked_launcher_parent_is_refused(launcher_checkouts):
    """A symlink below the primary root is seen, never resolved past."""
    scripts = launcher_checkouts.primary / "scripts"
    real = launcher_checkouts.primary / "real-scripts"
    scripts.rename(real)
    scripts.symlink_to(real, target_is_directory=True)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert ": scripts is a symlink" in str(refusal)
    assert str(launcher_checkouts.root) not in str(refusal)


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads any file")
def test_unreadable_launcher_is_refused(launcher_checkouts):
    launcher_checkouts.launcher.chmod(0o311)
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("unreadable", "acp_adapter_incompatible")


def test_one_edited_launcher_byte_is_a_digest_mismatch(launcher_checkouts):
    launcher = launcher_checkouts.launcher
    data = bytearray(launcher.read_bytes())
    data[-2] ^= 0x01
    launcher.write_bytes(bytes(data))
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("digest_mismatch", "acp_adapter_incompatible")
    assert acpx_module._CLAUDE_ACP_LAUNCHER_CLOSURE[acpx_module._CLAUDE_ACP_LAUNCHER_RELPATH] in str(refusal)
    assert not list(launcher_checkouts.copies.glob("launch-*"))


def test_an_oversized_launcher_is_refused_unhashed(launcher_checkouts):
    launcher_checkouts.launcher.write_bytes(b"#" * (acpx_module._CLAUDE_ACP_LAUNCHER_MAX_BYTES + 1))
    assert _launcher_refusal().reason == "untrusted_path"


def test_every_closure_member_is_pinned_and_copied(launcher_checkouts, monkeypatch):
    """A file the launcher would source is pinned like the launcher and copied beside it."""
    member_rel = acpx_module.PurePosixPath("scripts/agent_runtime/claude_acp_lib.sh")
    member = launcher_checkouts.primary / member_rel
    member.write_bytes(b"deny=Monitor\n")
    member.chmod(0o644)
    monkeypatch.setattr(
        acpx_module,
        "_CLAUDE_ACP_LAUNCHER_CLOSURE",
        {**acpx_module._CLAUDE_ACP_LAUNCHER_CLOSURE, member_rel: hashlib.sha256(member.read_bytes()).hexdigest()},
    )
    copy = _accepted_copy(launcher_checkouts)
    copied_member = copy.parents[2] / member_rel
    assert copied_member.read_bytes() == b"deny=Monitor\n"
    assert stat.S_IMODE(copied_member.stat().st_mode) == 0o400

    member.write_bytes(b"deny=\n")
    refusal = _launcher_refusal()
    assert refusal.reason == "digest_mismatch"
    assert str(member_rel) in str(refusal)

    member.unlink()
    assert _launcher_refusal().reason == "missing"


def test_launcher_refusal_precedes_the_host_probe_and_any_acp_message(launcher_checkouts, worktree_dir, monkeypatch):
    """No plan exists, so the runner never spawns ACPX or sends an ACP message."""
    _stub_binary(monkeypatch, worktree_dir)
    marker = worktree_dir / "acpx-ran"
    (worktree_dir / "fake-acpx-bin").write_text(f"#!/bin/sh\n: > '{marker}'\n", encoding="utf-8")
    monkeypatch.setattr(acpx_module, "_require_claude_acp_launcher", _REAL_LAUNCHER_GATE)

    def no_host_probe(**_kwargs):
        raise AssertionError("the host Claude Code was probed before the launcher gate refused")

    monkeypatch.setattr(acpx_module, "_require_host_claude_code", no_host_probe)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    launcher_checkouts.launcher.unlink()

    with pytest.raises(ClaudeCodeExecutableRefusal) as raised:
        _build(worktree_dir)
    assert raised.value.reason == "missing"
    assert not marker.exists()


def test_a_host_refusal_removes_the_launch_copy(launcher_checkouts, worktree_dir, monkeypatch):
    _stub_binary(monkeypatch, worktree_dir)
    monkeypatch.setattr(acpx_module, "_require_claude_acp_launcher", _REAL_LAUNCHER_GATE)

    def refuse(**_kwargs):
        raise ClaudeCodeExecutableRefusal("fixture", reason="too_old")

    monkeypatch.setattr(acpx_module, "_require_host_claude_code", refuse)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    with pytest.raises(ClaudeCodeExecutableRefusal):
        _build(worktree_dir)
    assert not list(launcher_checkouts.copies.glob("launch-*"))


def test_host_that_is_the_launcher_itself_is_refused(worktree_dir, monkeypatch):
    _stub_binary(monkeypatch, worktree_dir)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    monkeypatch.setattr(acpx_module, "_require_claude_acp_launcher", lambda *, adapter_label: str(_LAUNCHER))
    monkeypatch.setattr(
        acpx_module,
        "_require_host_claude_code",
        lambda **_kw: {"claude_code_executable": str(_LAUNCHER), "claude_code_launch_identity": "1:2:3:4:5"},
    )
    with pytest.raises(ClaudeCodeExecutableRefusal, match="launcher itself"):
        _build(worktree_dir)


# --- in-place host edits (reviewer reproductions, #10500) -------------------


def _edit_in_place(executable: Path) -> None:
    """Append to the executable through its existing inode, as an in-place writer would."""
    inode = executable.stat().st_ino
    with executable.open("ab") as handle:
        handle.write(b"# modified\n")
    assert executable.stat().st_ino == inode


def test_launcher_refuses_a_host_edited_in_place_after_the_probe(tmp_path):
    fake = _dumping_claude(tmp_path / "host")
    identity = _launch_identity(fake)
    _edit_in_place(fake)
    proc, dump = _run_launcher(tmp_path, host=str(fake), identity=identity)
    assert proc.returncode == 126
    assert "changed since its version probe" in proc.stderr
    assert not dump.exists()


def test_a_successful_ask_with_a_host_edited_in_place_and_no_transcript_fails(host, tmp_path, monkeypatch):
    executable = host.install()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    plan = _plan(executable)
    _edit_in_place(executable)
    parsed = _parse(plan, _ok_stream())
    assert parsed.ok is False
    assert parsed.response == ""
    assert parsed.failure_code == "acp_adapter_missing"
    assert "changed during the ask" in parsed.stderr_excerpt
    assert plan.metadata["claude_code_child_attestation"] == "host_changed"


def test_a_successful_ask_whose_host_vanished_fails(host, tmp_path, monkeypatch):
    executable = host.install()
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _transcript(home, "2.1.296")
    plan = _plan(executable)
    executable.unlink()
    parsed = _parse(plan, _ok_stream())
    assert (parsed.ok, parsed.failure_code) == (False, "acp_adapter_missing")


def test_the_identity_covers_size_mtime_and_ctime(tmp_path):
    target = tmp_path / "file"
    target.write_bytes(b"a")
    before = target.lstat()
    _edit_in_place(target)
    after = target.lstat()
    assert acpx_module._claude_code_identity(before) != acpx_module._claude_code_identity(after)
    assert acpx_module._claude_code_launch_identity(after) == _launch_identity(target)
    stat_cli = subprocess.run(
        [_GNU_STAT, "-c", "%d:%i:%s:%.9Y:%.9Z", "--", str(target)],
        capture_output=True, text=True, timeout=30, check=True,
    )
    assert stat_cli.stdout.strip() == _launch_identity(target)


def test_launcher_refuses_a_same_size_edit_with_restored_mtime(tmp_path):
    """Only the nanosecond ctime records the edit; whole seconds would miss it."""
    for attempt in range(5):
        # Start early in a second, so the edit keeps the whole-second ctime.
        if time.time() % 1.0 > 0.5:
            time.sleep(1.0 - time.time() % 1.0 + 0.01)
        fake = _dumping_claude(tmp_path / f"host-{attempt}")
        before = fake.lstat()
        identity = acpx_module._claude_code_launch_identity(before)
        time.sleep(0.01)
        original = fake.read_bytes()
        edited = original.replace(b"import json, os, sys", b"import json,os, sys ")
        assert len(edited) == len(original) and edited != original
        fake.write_bytes(edited)
        os.utime(fake, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = fake.lstat()
        if after.st_ctime_ns // 10**9 == before.st_ctime_ns // 10**9:
            break
    assert (after.st_ino, after.st_size, after.st_mtime_ns) == (before.st_ino, before.st_size, before.st_mtime_ns)
    assert after.st_ctime_ns // 10**9 == before.st_ctime_ns // 10**9, "every attempt crossed a second boundary"
    assert after.st_ctime_ns != before.st_ctime_ns
    proc, dump = _run_launcher(tmp_path, host=str(fake), identity=identity)
    assert proc.returncode == 126, proc.stderr
    assert "changed since its version probe" in proc.stderr
    assert not dump.exists()


# --- no absolute host path in refusal or diagnostic text (#10500) -----------

_ABSOLUTE_PATH = re.compile(r"(?<![\w.~<-])/[\w.-]")


def _assert_path_free(text: str, *paths: Path) -> None:
    for path in paths:
        assert str(path) not in text
    assert not _ABSOLUTE_PATH.search(text), text


def test_launcher_refusals_name_no_absolute_host_path(launcher_checkouts, monkeypatch):
    checkouts = launcher_checkouts
    messages = []

    def refuse() -> None:
        messages.append(str(_launcher_refusal()))

    checkouts.launcher.chmod(0o775)
    refuse()
    checkouts.launcher.chmod(0o755)
    (checkouts.primary / "scripts").chmod(0o777)
    refuse()
    (checkouts.primary / "scripts").chmod(0o755)
    checkouts.root.chmod(0o777)
    refuse()
    checkouts.root.chmod(0o700)
    original = checkouts.launcher.read_bytes()
    checkouts.launcher.write_bytes(original + b"\n")
    refuse()
    checkouts.launcher.write_bytes(original)
    checkouts.copies.mkdir(mode=0o700)
    checkouts.copies.chmod(0o777)
    refuse()
    checkouts.copies.chmod(0o700)
    checkouts.launcher.unlink()
    refuse()
    (checkouts.worktree / ".git").write_text("gitdir: /elsewhere/.git\n", encoding="utf-8")
    refuse()
    assert len(messages) == 7
    for message in messages:
        _assert_path_free(message, checkouts.root)


def test_host_refusals_and_post_run_text_name_no_absolute_host_path(host, tmp_path, monkeypatch):
    messages = []
    executable = host.install("2.1.279 (Claude Code)", name="2.1.279")
    messages.append(str(_refusal(model="claude-opus-5-5")))
    executable = host.install("no version here", name="2.1.300")
    messages.append(str(_refusal(model=None)))
    executable.chmod(0o777)
    messages.append(str(_refusal(model=None)))
    executable.chmod(0o755)
    (host.root / "share").chmod(0o777)
    messages.append(str(_refusal(model=None)))
    (host.root / "share").chmod(0o755)

    def remove_then_spawn(argv, **kwargs):
        Path(argv[0]).unlink()
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr("scripts.utils.claude_version.run_version_probe", remove_then_spawn)
    messages.append(str(_refusal(model=None)))
    monkeypatch.setattr(claude_module, "_default_claude_bin", lambda: str(tmp_path / "gone" / "claude"))
    messages.append(str(_refusal(model=None)))
    for message in messages:
        _assert_path_free(message, tmp_path)

    executable = host.install()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_COPY_BASE", tmp_path / "copies")
    plan = _plan(executable)
    plan.metadata["claude_code_launcher"] = str(tmp_path / "copies" / "launch-x" / _LAUNCHER_REL)
    failed = AcpxClaudeShadowAdapter().parse_response(
        stdout=_failed_stream(),
        stderr=f"spawn {plan.metadata['claude_code_launcher']} EACCES; host {executable}",
        returncode=1,
        output_file=None,
        plan=plan,
    )
    assert failed.ok is False
    _assert_path_free(failed.stderr_excerpt or "", tmp_path)
    assert "<acp-launcher-copy>" in (failed.stderr_excerpt or "")
    _edit_in_place(executable)
    _assert_path_free(_parse(plan, _ok_stream()).stderr_excerpt, tmp_path)


def test_paths_are_redacted_before_the_excerpt_is_bounded(host, tmp_path, monkeypatch):
    """A path that crosses the 500-character excerpt limit leaves no prefix behind."""
    executable = host.install()
    monkeypatch.setenv("HOME", str(tmp_path / "empty-home"))
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_COPY_BASE", tmp_path / "copies")
    launcher = tmp_path / "copies" / "launch-abcdefgh" / _LAUNCHER_REL
    paths = f"{launcher} {launcher.parents[2]} {executable} "
    for pad in range(len(paths) + 1):
        plan = _plan(executable)
        plan.metadata["claude_code_launcher"] = str(launcher)
        parsed = AcpxClaudeShadowAdapter().parse_response(
            stdout=_failed_stream(),
            stderr="e" * pad + paths * 12,
            returncode=1,
            output_file=None,
            plan=plan,
        )
        assert parsed.ok is False
        assert len(parsed.stderr_excerpt) <= 500
        _assert_path_free(parsed.stderr_excerpt, tmp_path)
        if pad == 0:
            assert "<acp-launcher-copy>" in parsed.stderr_excerpt


@pytest.mark.repo_wide
def test_tracked_launcher_is_executable_in_git():
    listed = subprocess.run(
        ["git", "ls-files", "-s", "scripts/agent_runtime/claude_acp_exec.sh"],
        cwd=Path(acpx_module.__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    ).stdout
    assert listed.startswith("100755 ")
