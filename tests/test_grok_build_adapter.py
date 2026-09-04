"""GrokBuildAdapter tests — native `grok` CLI headless adapter.

Kept deliberately separate from the Hermes-backed `grok` agent
(HermesGrokAdapter, grok-4.5). These tests don't require the grok binary
to be installed — `shutil.which` is mocked.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import registry
from agent_runtime.adapters.base import AgentAdapter, InvocationPlan
from agent_runtime.adapters.grok_build import (
    _MCP_REVIEW_DENY_RULES,
    _READ_ONLY_DENY_RULES,
    GROK_BUILD_DEFAULT_EFFORT,
    GROK_BUILD_DEFAULT_MODEL,
    GROK_SUPPORTED_EFFORTS,
    GrokBuildAdapter,
    _adapt_prompt_for_grok_build_mcp,
    _parse_json_object,
    _translate_mcp_prefix_for_grok_build,
    grok_session_dir,
    resolve_grok_home,
)

FAKE_GROK = "/usr/local/bin/grok"


def _build(prompt: str, tmp_path: Path, **kw):
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        return GrokBuildAdapter().build_invocation(
            prompt=prompt,
            mode=kw.pop("mode", "danger"),
            cwd=tmp_path,
            model=kw.pop("model", None),
            task_id=kw.pop("task_id", None),
            session_id=kw.pop("session_id", None),
            tool_config=kw.pop("tool_config", None),
            effort=kw.pop("effort", None),
        )


def _val(cmd: list[str], flag: str) -> str:
    return cmd[cmd.index(flag) + 1]


def test_basic_headless_invocation(tmp_path):
    plan = _build("Fix the bug in foo.py", tmp_path)
    assert plan.cmd[0] == FAKE_GROK
    assert _val(plan.cmd, "-p") == "Fix the bug in foo.py"
    assert _val(plan.cmd, "--output-format") == "json"
    assert "--no-alt-screen" in plan.cmd
    assert _val(plan.cmd, "--cwd") == str(tmp_path)
    assert plan.stdin_payload == ""
    assert plan.output_file is None


def test_mode_permission_mapping(tmp_path):
    for mode, perm in [
        ("read-only", "auto"),
        ("workspace-write", "auto"),
        ("danger", "bypassPermissions"),
    ]:
        plan = _build("do x", tmp_path, mode=mode)
        assert _val(plan.cmd, "--permission-mode") == perm


@pytest.mark.parametrize("mode", ["workspace-write", "danger"])
def test_write_capable_modes_auto_approve_headless_tool_execution(tmp_path, mode):
    plan = _build("commit and push", tmp_path, mode=mode)

    assert "--always-approve" in plan.cmd


def test_read_only_mode_does_not_auto_approve_tool_execution(tmp_path):
    plan = _build("inspect only", tmp_path, mode="read-only")

    assert _val(plan.cmd, "--permission-mode") == "auto"
    assert "--always-approve" not in plan.cmd


def test_read_only_mode_applies_mutation_deny_rules(tmp_path):
    plan = _build("inspect only", tmp_path, mode="read-only")

    assert _val(plan.cmd, "--permission-mode") == "auto"
    assert "--always-approve" not in plan.cmd
    assert _val(plan.cmd, "--disallowed-tools") == "search_replace"
    denied = [plan.cmd[i + 1] for i, item in enumerate(plan.cmd) if item == "--deny"]
    assert denied == list(_READ_ONLY_DENY_RULES)
    assert "Bash" in denied
    assert set(_READ_ONLY_DENY_RULES) == {"Write", "Edit", "Bash"}
    # Fail-closed: no prefix-only Bash rules that leave gh api / tee / sed -i open.
    assert not any(rule.startswith("Bash(") for rule in _READ_ONLY_DENY_RULES)


def test_grok_deny_rules_use_documented_native_permission_prefixes():
    # Pinned to the native Grok CLI headless documentation. These are
    # permission-rule prefixes, not Claude-shaped built-in tool IDs.
    documented_prefixes = {
        "Bash",
        "Edit",
        "Grep",
        "MCPTool",
        "Read",
        "WebFetch",
        "Write",
    }
    assert set(_READ_ONLY_DENY_RULES) <= documented_prefixes
    assert set(_MCP_REVIEW_DENY_RULES) <= documented_prefixes
    assert "Bash" in _READ_ONLY_DENY_RULES
    assert "NotebookEdit" not in _READ_ONLY_DENY_RULES
    assert "NotebookEdit" not in _MCP_REVIEW_DENY_RULES


def test_exact_argv_per_mode(tmp_path):
    # read-only: auto, no always-approve, fail-closed deny on write tools + Bash
    ro_plan = _build("inspect", tmp_path, mode="read-only", model="grok-4.6", effort="high")
    assert ro_plan.cmd == [
        FAKE_GROK,
        "-p",
        "inspect",
        "--output-format",
        "json",
        "--no-alt-screen",
        "--permission-mode",
        "auto",
        "--cwd",
        str(tmp_path),
        "--deny",
        "Write",
        "--deny",
        "Edit",
        "--deny",
        "Bash",
        "-m",
        "grok-4.6",
        "--effort",
        "high",
        "--disallowed-tools",
        "search_replace",
    ]

    # workspace-write: auto, always-approve, no default deny rules
    ww_plan = _build("edit code", tmp_path, mode="workspace-write", model="grok-4.6", effort="high")
    assert ww_plan.cmd == [
        FAKE_GROK,
        "-p",
        "edit code",
        "--output-format",
        "json",
        "--no-alt-screen",
        "--permission-mode",
        "auto",
        "--cwd",
        str(tmp_path),
        "--always-approve",
        "-m",
        "grok-4.6",
        "--effort",
        "high",
    ]

    # danger: bypassPermissions, always-approve, no default deny rules
    danger_plan = _build("danger task", tmp_path, mode="danger", model="grok-4.6", effort="high")
    assert danger_plan.cmd == [
        FAKE_GROK,
        "-p",
        "danger task",
        "--output-format",
        "json",
        "--no-alt-screen",
        "--permission-mode",
        "bypassPermissions",
        "--cwd",
        str(tmp_path),
        "--always-approve",
        "-m",
        "grok-4.6",
        "--effort",
        "high",
    ]


def test_trail_isolation_does_not_inherit_write_approval(tmp_path):
    tool_config = {
        "trail_isolation": True,
        "allowed_tools": "Read,Grep,Glob",
        "mcp_config_path": str(tmp_path / ".mcp.json"),
        "setting_sources": "",
        "strict_mcp_config": True,
        "tools": "Read,Grep,Glob",
        "trail_isolation_cwd": str(tmp_path),
    }
    with patch(
        "agent_runtime.adapters.grok_build.assert_trail_isolation_config",
        return_value=tmp_path,
    ):
        plan = _build("inspect trail", tmp_path, mode="read-only", tool_config=tool_config)

    assert _val(plan.cmd, "--permission-mode") == "default"
    assert "--always-approve" not in plan.cmd
    assert "Bash" in [plan.cmd[index + 1] for index, item in enumerate(plan.cmd) if item == "--deny"]


def test_review_isolation_keeps_its_existing_approval_and_denies(tmp_path):
    review_root = tmp_path / "review"
    for child in ("tmp", "home", "exec"):
        (review_root / child).mkdir(parents=True, exist_ok=True)
    tool_config = {
        "review_isolation": True,
        "review_engine_binary": "/usr/bin/true",
    }
    with patch(
        "scripts.review.isolation.validated_review_write_root",
        return_value=review_root,
    ):
        plan = _build("review evidence", tmp_path, mode="read-only", tool_config=tool_config)

    assert _val(plan.cmd, "--permission-mode") == "bypassPermissions"
    assert "--always-approve" in plan.cmd
    denied = [plan.cmd[index + 1] for index, item in enumerate(plan.cmd) if item == "--deny"]
    assert "Bash" in denied
    assert denied == list(_MCP_REVIEW_DENY_RULES)
    assert _val(plan.cmd, "--disallowed-tools") == "search_replace"


@pytest.mark.parametrize(
    "review_deny_tools",
    ["Bash", ["NotebookEdit"], ["Write", "Bash"], ["Write", "Edit", "Bash", "Glob"]],
)
def test_review_isolation_rejects_unsupported_or_weak_deny_overrides(tmp_path, review_deny_tools):
    review_root = tmp_path / "review"
    for child in ("tmp", "home", "exec"):
        (review_root / child).mkdir(parents=True, exist_ok=True)
    tool_config = {
        "review_isolation": True,
        "review_engine_binary": "/usr/bin/true",
        "review_deny_tools": review_deny_tools,
    }
    with patch("scripts.review.isolation.validated_review_write_root", return_value=review_root):
        with pytest.raises(ValueError, match="review_deny_tools"):
            _build("review evidence", tmp_path, mode="read-only", tool_config=tool_config)


def test_unsupported_mode_raises(tmp_path):
    with pytest.raises(ValueError, match="unsupported mode"):
        _build("x", tmp_path, mode="bogus")


def test_model_and_effort_flags(tmp_path):
    plan = _build("x", tmp_path, model="grok-4.6", effort="high")
    assert _val(plan.cmd, "-m") == "grok-4.6"
    assert _val(plan.cmd, "--effort") == "high"


def test_default_effort_is_applied(tmp_path):
    plan = _build("x", tmp_path)
    assert _val(plan.cmd, "-m") == GROK_BUILD_DEFAULT_MODEL
    assert _val(plan.cmd, "--effort") == GROK_BUILD_DEFAULT_EFFORT


@pytest.mark.parametrize("effort", ["xhigh", "max"])
def test_unsupported_native_effort_raises_before_invocation(tmp_path, effort):
    with pytest.raises(ValueError, match="native Grok CLI supports --effort values"):
        _build("x", tmp_path, effort=effort)


def test_native_grok_effort_vocabulary_matches_cli_contract():
    assert frozenset({"low", "medium", "high"}) == GROK_SUPPORTED_EFFORTS


def test_hyphen_leading_prompt_uses_prompt_file(tmp_path):
    plan = _build("--- context: shared\nfix it", tmp_path)
    assert "-p" not in plan.cmd
    pf = Path(_val(plan.cmd, "--prompt-file"))
    assert pf.read_text(encoding="utf-8").startswith("--- context")


def test_tool_config_allow_deny(tmp_path):
    plan = _build("x", tmp_path, tool_config={"allowed_tools": "Read,Grep", "disallowed_tools": "Bash"})
    assert _val(plan.cmd, "--tools") == "Read,Grep"
    assert _val(plan.cmd, "--disallowed-tools") == "Bash"


def test_tool_config_mcp_servers_enables_always_approve(tmp_path):
    plan = _build("x", tmp_path, tool_config={"mcp_server_names": ["sources"]})

    assert "--always-approve" in plan.cmd
    assert "--no-plan" in plan.cmd


def test_mcp_sources_prompt_prefix_translates_to_native_grok_tool_names(tmp_path):
    prompt = "Use mcp__sources__search_style_guide and mcp__sources__verify_words."
    plan = _build(prompt, tmp_path, tool_config={"mcp_server_names": ["sources"]})

    assert "mcp__sources__" not in _val(plan.cmd, "-p")
    assert "sources__search_style_guide" in _val(plan.cmd, "-p")
    assert "sources__verify_words" in _val(plan.cmd, "-p")


def test_translate_mcp_prefix_for_grok_build_is_scoped():
    prompt = "mcp__sources__search_text mcp__rag__legacy"

    assert _translate_mcp_prefix_for_grok_build(prompt) == ("sources__search_text mcp__rag__legacy")


def test_adapt_prompt_for_grok_build_mcp_adds_headless_suffix():
    prompt = "Use mcp__sources__search_text."

    adapted = _adapt_prompt_for_grok_build_mcp(prompt)

    assert "sources__search_text" in adapted
    assert "mcp__sources__" not in adapted
    assert "native grok-build single-turn headless mode" in adapted
    assert "Return the final JSON object now" in adapted


def test_missing_grok_binary_raises(tmp_path):
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="grok CLI"):
            GrokBuildAdapter().build_invocation(
                prompt="x",
                mode="danger",
                cwd=tmp_path,
                model=None,
                task_id=None,
                session_id=None,
                tool_config=None,
            )


def test_parse_success_json():
    out = json.dumps({"text": "done\n", "stopReason": "EndTurn", "sessionId": "abc-123"})
    r = GrokBuildAdapter().parse_response(stdout=out, stderr="", returncode=0, output_file=None)
    assert r.ok
    assert r.response == "done"
    assert r.session_id == "abc-123"
    assert r.rate_limited is False


def test_parse_failure_nonzero():
    r = GrokBuildAdapter().parse_response(stdout="", stderr="boom", returncode=1, output_file=None)
    assert not r.ok
    assert r.response == ""
    assert r.stderr_excerpt == "boom"


def test_parse_rate_limited():
    r = GrokBuildAdapter().parse_response(
        stdout="", stderr="HTTP 429 too many requests", returncode=1, output_file=None
    )
    assert r.rate_limited is True
    assert not r.ok


def test_parse_json_with_log_noise():
    out = "some startup log\n" + json.dumps({"text": "ok"}) + "\ntrailing line"
    assert _parse_json_object(out) == {"text": "ok"}


def test_parse_plain_fallback():
    r = GrokBuildAdapter().parse_response(stdout="just plain text", stderr="", returncode=0, output_file=None)
    assert r.ok
    assert r.response == "just plain text"


def test_registry_native_grok_distinct_from_hermes_grok():
    native = registry.get_agent_entry("grok")
    alias = registry.get_agent_entry("grok-build")
    hermes = registry.get_agent_entry("grok-hermes")
    assert "grok_build:GrokBuildAdapter" in native["adapter"]
    assert "grok_build:GrokBuildAdapter" in alias["adapter"]
    assert "hermes_grok:HermesGrokAdapter" in hermes["adapter"]
    assert native["adapter"] != hermes["adapter"]
    assert native["default_model"] == GROK_BUILD_DEFAULT_MODEL
    assert native["default_effort"] == GROK_BUILD_DEFAULT_EFFORT
    assert "code_writing" in native["capabilities"]
    assert "grok" in registry.available_agents()
    assert "grok-build" in registry.available_agents()
    assert "grok-hermes" not in registry.available_agents()
    assert "grok-hermes" in registry.AGENTS


def test_grok_build_lane_defaults_to_grok_46():
    assert registry.get_agent_entry("grok")["default_model"] == "grok-4.6"
    assert registry.get_agent_entry("grok-build")["default_model"] == "grok-4.6"
    assert GROK_BUILD_DEFAULT_MODEL == "grok-4.6"


def test_grok_build_rejects_retired_model_pin(tmp_path):
    """#6870: pin the literal retired model id, not the grok-build agent alias."""
    with pytest.raises(ValueError, match=r"unsupported Grok model 'grok-4\.5'"):
        _build("x", tmp_path, model="grok-4.5", effort="high")


def test_grok_build_default_model_is_listed_by_cli():
    if os.environ.get("CI"):
        pytest.skip("real grok CLI smoke test is skipped in CI")
    grok_bin = shutil.which("grok")
    if not grok_bin:
        pytest.skip("grok CLI not installed")

    result = subprocess.run(
        [grok_bin, "models"],
        capture_output=True,
        text=True,
        timeout=20,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert GROK_BUILD_DEFAULT_MODEL in result.stdout.split()


def test_conforms_to_agent_adapter_protocol():
    assert isinstance(GrokBuildAdapter(), AgentAdapter)


def test_liveness_signal_paths_returns_tuple(tmp_path, monkeypatch):
    from urllib.parse import quote

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)
    paths = GrokBuildAdapter().liveness_signal_paths(InvocationPlan(cmd=[], cwd=tmp_path))
    assert isinstance(paths, tuple)
    # Always cwd-scoped sessions root — never the shared ~/.grok home (#6933).
    assert paths == (fake_home / ".grok" / "sessions" / quote(str(tmp_path.resolve()), safe=""),)


def test_liveness_signal_paths_ignore_peer_session_and_shared_home(tmp_path, monkeypatch):
    """Two sessions under the same cwd: only OUR session is a liveness path.

    Mutation check (#6933): reverting ``_liveness_paths_for_cwd`` to return the
    shared ``GROK_HOME`` root makes ``assert grok_home not in paths`` fail.
    """
    from urllib.parse import quote

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()
    peer = grok_session_dir(grok_home, project, "peer-session-aaaa")
    peer.mkdir(parents=True)
    peer_events = peer / "events.jsonl"
    peer_events.write_text("{}\n", encoding="utf-8")
    # Shared-home contaminants from the #6921 campaign.
    (grok_home / "logs").mkdir(parents=True)
    (grok_home / "logs" / "unified.jsonl").write_text("peer\n", encoding="utf-8")
    (grok_home / "active_sessions.json").write_text("[]\n", encoding="utf-8")

    adapter = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan = adapter.build_invocation(
            prompt="do the work",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    # Peer was snapshotted at build_invocation — must not bind as ours.
    assert peer in adapter._session_dir_snapshot
    assert "peer-session-aaaa" in plan.metadata["liveness_session_dir_snapshot"]

    ours = grok_session_dir(grok_home, project, "our-session-bbbb")
    ours.mkdir(parents=True)
    our_events = ours / "events.jsonl"
    our_events.write_text("{}\n", encoding="utf-8")

    # Peer + shared home keep moving while ours is the only new session.
    peer_events.write_text("{}\n{}\n", encoding="utf-8")
    (grok_home / "logs" / "unified.jsonl").write_text("peer\nmore\n", encoding="utf-8")
    grok_home.touch()

    paths = adapter.liveness_signal_paths(plan)
    sessions_root = grok_home / "sessions" / quote(str(project.resolve()), safe="")

    assert grok_home not in paths
    assert (grok_home / "logs" / "unified.jsonl") not in paths
    assert peer not in paths
    assert peer_events not in paths
    assert sessions_root in paths
    assert ours in paths
    assert our_events in paths
    assert plan.metadata["liveness_session_id"] == "our-session-bbbb"


def test_liveness_signal_paths_resume_binds_exact_session(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()
    peer = grok_session_dir(grok_home, project, "peer-session")
    peer.mkdir(parents=True)
    (peer / "events.jsonl").write_text("{}\n", encoding="utf-8")
    target = grok_session_dir(grok_home, project, "resume-me")
    target.mkdir(parents=True)
    (target / "events.jsonl").write_text("{}\n", encoding="utf-8")

    plan = _build(
        "continue",
        project,
        session_id="resume-me",
        tool_config={"resume": True},
    )
    paths = GrokBuildAdapter().liveness_signal_paths(plan)
    # Fresh adapter instance: resume id comes from plan.metadata.
    assert paths == (target, target / "events.jsonl")
    assert grok_home not in paths
    assert peer not in paths


def test_liveness_newest_post_snapshot_cannot_steal_bound_session(tmp_path, monkeypatch):
    """#6935: pin the first post-snapshot child; a later sibling must not steal.

    Mutation check: clearing ``liveness_session_id`` and re-picking newest on
    every poll makes ``assert later not in paths_after`` fail.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()

    adapter = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan = adapter.build_invocation(
            prompt="supervised",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    ours = grok_session_dir(grok_home, project, "bound-first")
    ours.mkdir(parents=True)
    (ours / "events.jsonl").write_text("{}\n", encoding="utf-8")

    paths_first = adapter.liveness_signal_paths(plan)
    assert ours in paths_first
    assert plan.metadata["liveness_session_id"] == "bound-first"

    # Later same-cwd peer is newer; unpinned re-pick would bind it.
    later = grok_session_dir(grok_home, project, "later-peer")
    later.mkdir(parents=True)
    (later / "events.jsonl").write_text("{}\n", encoding="utf-8")
    # Ensure later wins a pure-mtime newest contest.
    later.touch()

    paths_after = adapter.liveness_signal_paths(plan)
    assert paths_after == (ours, ours / "events.jsonl")
    assert later not in paths_after
    assert plan.metadata["liveness_session_id"] == "bound-first"


def test_liveness_split_instance_non_resume_uses_plan_snapshot(tmp_path, monkeypatch):
    """#6935: plan-only poller must not treat pre-existing peers as new.

    Mutation check: dropping ``liveness_session_dir_snapshot`` from metadata
    makes a fresh adapter bind the pre-existing peer before ours appears.
    """
    from urllib.parse import quote

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()
    peer = grok_session_dir(grok_home, project, "preexisting-peer")
    peer.mkdir(parents=True)
    (peer / "events.jsonl").write_text("{}\n", encoding="utf-8")

    builder = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan = builder.build_invocation(
            prompt="supervised",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    assert "preexisting-peer" in plan.metadata["liveness_session_dir_snapshot"]

    poller = GrokBuildAdapter()
    sessions_root = grok_home / "sessions" / quote(str(project.resolve()), safe="")
    before = poller.liveness_signal_paths(plan)
    assert before == (sessions_root,)
    assert peer not in before
    assert "liveness_session_id" not in plan.metadata

    ours = grok_session_dir(grok_home, project, "ours-after-build")
    ours.mkdir(parents=True)
    (ours / "events.jsonl").write_text("{}\n", encoding="utf-8")

    after = poller.liveness_signal_paths(plan)
    assert peer not in after
    assert ours in after
    assert plan.metadata["liveness_session_id"] == "ours-after-build"

    # Pin must survive yet another fresh instance + a newer sibling.
    later = grok_session_dir(grok_home, project, "even-later")
    later.mkdir(parents=True)
    (later / "events.jsonl").write_text("{}\n", encoding="utf-8")
    later.touch()
    pinned = GrokBuildAdapter().liveness_signal_paths(plan)
    assert pinned == (ours, ours / "events.jsonl")
    assert later not in pinned


def test_liveness_respects_grok_home_override(tmp_path, monkeypatch):
    """#6935: liveness paths follow GROK_HOME (env and plan.env_overrides)."""
    from urllib.parse import quote

    default_home = tmp_path / "default-home"
    default_home.mkdir()
    monkeypatch.setenv("HOME", str(default_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    custom = tmp_path / "custom-grok-home"
    custom.mkdir()
    project = tmp_path / "project"
    project.mkdir()

    monkeypatch.setenv("GROK_HOME", str(custom))
    adapter = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan = adapter.build_invocation(
            prompt="env home",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
    sessions_root = custom / "sessions" / quote(str(project.resolve()), safe="")
    assert adapter.liveness_signal_paths(plan) == (sessions_root,)
    assert not str(sessions_root).startswith(str(default_home / ".grok"))

    override_home = tmp_path / "override-grok-home"
    override_home.mkdir()
    override_root = override_home / "sessions" / quote(str(project.resolve()), safe="")
    plan_override = InvocationPlan(
        cmd=[],
        cwd=project,
        env_overrides={"GROK_HOME": str(override_home)},
        metadata={"liveness_session_dir_snapshot": []},
    )
    assert GrokBuildAdapter().liveness_signal_paths(plan_override) == (override_root,)


def test_liveness_shared_adapter_two_plans_no_cross_pin(tmp_path, monkeypatch):
    """#6935 delta: shared adapter must not hand plan A's pin to unpinned plan B.

    Fleet shape: both plans already built, then interleaved polls. Plan B's
    snapshot is stamped to exclude A's session as "new" so the only way B
    can watch A's dir is via the forbidden instance bind.

    Mutation check: restoring instance ``_liveness_session_id`` /
    ``_resume_session_id`` fallback in ``_bound_liveness_session_id`` plus
    writing the discover pin onto ``self._liveness_session_id`` makes plan B
    resolve to A's session id (false-LIVE contamination).
    """
    from urllib.parse import quote

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()
    sessions_root = grok_home / "sessions" / quote(str(project.resolve()), safe="")

    adapter = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan_a = adapter.build_invocation(
            prompt="plan A",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )
        plan_b = adapter.build_invocation(
            prompt="plan B",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    # Treat A's forthcoming session as already known to B (peer / prior run),
    # so unpinned B correctly stays on sessions_root unless instance-bound.
    plan_b.metadata["liveness_session_dir_snapshot"] = ["plan-a-session"]

    session_a = grok_session_dir(grok_home, project, "plan-a-session")
    session_a.mkdir(parents=True)
    (session_a / "events.jsonl").write_text("{}\n", encoding="utf-8")
    assert session_a in adapter.liveness_signal_paths(plan_a)
    assert plan_a.metadata["liveness_session_id"] == "plan-a-session"
    assert adapter.liveness_signal_paths(plan_a) == (
        session_a,
        session_a / "events.jsonl",
    )

    # Instance bind would hand B A's id here.
    paths_b = adapter.liveness_signal_paths(plan_b)
    assert paths_b == (sessions_root,)
    assert session_a not in paths_b
    assert "liveness_session_id" not in plan_b.metadata

    session_b = grok_session_dir(grok_home, project, "plan-b-session")
    session_b.mkdir(parents=True)
    (session_b / "events.jsonl").write_text("{}\n", encoding="utf-8")
    paths_b_bound = adapter.liveness_signal_paths(plan_b)
    assert session_b in paths_b_bound
    assert plan_b.metadata["liveness_session_id"] == "plan-b-session"
    assert session_a not in paths_b_bound
    assert adapter.liveness_signal_paths(plan_b) == (
        session_b,
        session_b / "events.jsonl",
    )
    assert plan_a.metadata["liveness_session_id"] == "plan-a-session"


def test_liveness_pinned_dir_deleted_mid_run_stays_bound(tmp_path, monkeypatch):
    """#6935: deleted pinned session dir stays bound (false-dead OK).

    Watching the missing path is preferred over re-picking a peer and going
    false-LIVE — the stall timer will correctly treat the deleted pin as dead.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.delenv("GROK_HOME", raising=False)

    project = tmp_path / "project"
    project.mkdir()
    grok_home = resolve_grok_home()

    adapter = GrokBuildAdapter()
    with patch("agent_runtime.adapters.grok_build.shutil.which", return_value=FAKE_GROK):
        plan = adapter.build_invocation(
            prompt="supervised",
            mode="danger",
            cwd=project,
            model=None,
            task_id=None,
            session_id=None,
            tool_config=None,
        )

    pinned = grok_session_dir(grok_home, project, "pinned-then-gone")
    pinned.mkdir(parents=True)
    (pinned / "events.jsonl").write_text("{}\n", encoding="utf-8")
    assert pinned in adapter.liveness_signal_paths(plan)
    assert plan.metadata["liveness_session_id"] == "pinned-then-gone"
    assert adapter.liveness_signal_paths(plan) == (pinned, pinned / "events.jsonl")

    shutil.rmtree(pinned)
    peer = grok_session_dir(grok_home, project, "alive-peer")
    peer.mkdir(parents=True)
    (peer / "events.jsonl").write_text("{}\n", encoding="utf-8")
    peer.touch()

    after = adapter.liveness_signal_paths(plan)
    assert after == (pinned, pinned / "events.jsonl")
    assert peer not in after
    assert plan.metadata["liveness_session_id"] == "pinned-then-gone"
