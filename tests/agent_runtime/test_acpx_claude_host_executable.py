"""The ACP Claude seat pins and version-gates the host Claude Code (#10500)."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
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
        acpx_module._require_trusted_claude_code_path(linked, adapter_label="X")
    assert raised.value.reason == "untrusted_path"


def test_non_executable_file_is_rejected(host):
    executable = host.install()
    executable.chmod(0o644)
    with pytest.raises(ClaudeCodeExecutableRefusal, match="not executable"):
        acpx_module._require_trusted_claude_code_path(executable, adapter_label="X")


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
    assert env["LU_CLAUDE_ACP_HOST_DEV_INO"] == "1:2"
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
        env["LU_CLAUDE_ACP_HOST_DEV_INO"] = identity
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
    fake_stat = fake.stat()
    proc, dump = _run_launcher(tmp_path, host=str(fake), identity=f"{fake_stat.st_dev}:{fake_stat.st_ino}")
    assert proc.returncode == 0, proc.stderr
    record = json.loads(dump.read_text(encoding="utf-8"))
    assert record["argv"][1:] == [
        "--disallowedTools",
        "Monitor,ScheduleWakeup,CronCreate,Workflow",
        *_SDK_ARGS,
    ]
    assert "LU_CLAUDE_ACP_HOST" not in record["env"]
    assert "LU_CLAUDE_ACP_HOST_DEV_INO" not in record["env"]


@pytest.mark.parametrize(
    ("host", "identity", "message"),
    [
        (None, "1:2", "missing or relative"),
        ("relative/claude", "1:2", "missing or relative"),
        ("HOST", None, "identity is missing"),
        ("HOST", "0:0", "changed since its version probe"),
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
    runs from the caller's worktree; git resolves the primary from it.
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
    monkeypatch.setattr(acpx_module, "_CLAUDE_ACP_LAUNCHER_ANCHOR", worktree)
    monkeypatch.setattr(acpx_module, "_CLAUDE_CODE_TRUST_ROOT", root)
    _fake_accounts(monkeypatch, members=("caller",))
    return SimpleNamespace(
        primary=primary,
        worktree=worktree,
        launcher=primary / _LAUNCHER_REL,
        worktree_launcher=worktree / _LAUNCHER_REL,
    )


def _launcher_refusal() -> ClaudeCodeExecutableRefusal:
    with pytest.raises(ClaudeCodeExecutableRefusal) as raised:
        acpx_module._require_claude_acp_launcher(adapter_label="X")
    return raised.value


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
    assert acpx_module._require_claude_acp_launcher(adapter_label="X") == str(launcher_checkouts.launcher)


def test_a_clean_worktree_copy_never_stands_in_for_a_missing_primary_launcher(launcher_checkouts):
    launcher_checkouts.launcher.unlink()
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("missing", "acp_adapter_missing")
    assert "pull main there" in str(refusal)


def test_an_unresolvable_primary_checkout_is_missing(launcher_checkouts, monkeypatch):
    def unresolvable(_start):
        raise acpx_module.NotAGitRepositoryError("fixture")

    monkeypatch.setattr(acpx_module, "resolve_main_root", unresolvable)
    refusal = _launcher_refusal()
    assert (refusal.reason, refusal.failure_code) == ("missing", "acp_adapter_missing")


def test_environment_and_cwd_never_redirect_the_launcher(launcher_checkouts, monkeypatch):
    worktree = launcher_checkouts.worktree
    worktree_git_dir = (worktree / ".git").read_text(encoding="utf-8").removeprefix("gitdir:").strip()
    for name, value in {
        "GIT_DIR": worktree_git_dir,
        "GIT_WORK_TREE": str(worktree),
        "GIT_COMMON_DIR": worktree_git_dir,
        "CLAUDE_CODE_EXECUTABLE": str(launcher_checkouts.worktree_launcher),
        "PATH": f"{launcher_checkouts.worktree_launcher.parent}{os.pathsep}/usr/bin:/bin",
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(worktree)
    assert acpx_module._require_claude_acp_launcher(adapter_label="X") == str(launcher_checkouts.launcher)


def test_trusted_launcher_is_accepted_with_private_group_parents(launcher_checkouts):
    (launcher_checkouts.primary / "scripts").chmod(0o775)
    assert acpx_module._require_claude_acp_launcher(adapter_label="X") == str(launcher_checkouts.launcher)


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
    assert "is a symlink" in str(refusal)


def test_symlinked_launcher_parent_is_refused(launcher_checkouts):
    """A symlink below the primary root is seen, never resolved past."""
    scripts = launcher_checkouts.primary / "scripts"
    real = launcher_checkouts.primary / "real-scripts"
    scripts.rename(real)
    scripts.symlink_to(real, target_is_directory=True)
    refusal = _launcher_refusal()
    assert refusal.reason == "untrusted_path"
    assert f"{scripts} is a symlink" in str(refusal)


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


def test_every_closure_member_is_pinned(launcher_checkouts, monkeypatch):
    """A file the launcher would source is pinned like the launcher itself."""
    member_rel = acpx_module.PurePosixPath("scripts/agent_runtime/claude_acp_lib.sh")
    member = launcher_checkouts.primary / member_rel
    member.write_bytes(b"deny=Monitor\n")
    member.chmod(0o644)
    monkeypatch.setattr(
        acpx_module,
        "_CLAUDE_ACP_LAUNCHER_CLOSURE",
        {**acpx_module._CLAUDE_ACP_LAUNCHER_CLOSURE, member_rel: hashlib.sha256(member.read_bytes()).hexdigest()},
    )
    assert acpx_module._require_claude_acp_launcher(adapter_label="X") == str(launcher_checkouts.launcher)

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


def test_host_that_is_the_launcher_itself_is_refused(worktree_dir, monkeypatch):
    _stub_binary(monkeypatch, worktree_dir)
    monkeypatch.setenv(acpx_module.TRANSPORT_ENV, "active")
    monkeypatch.setattr(acpx_module, "_require_claude_acp_launcher", lambda *, adapter_label: str(_LAUNCHER))
    monkeypatch.setattr(
        acpx_module,
        "_require_host_claude_code",
        lambda **_kw: {"claude_code_executable": str(_LAUNCHER), "claude_code_dev_ino": "1:2"},
    )
    with pytest.raises(ClaudeCodeExecutableRefusal, match="launcher itself"):
        _build(worktree_dir)


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
