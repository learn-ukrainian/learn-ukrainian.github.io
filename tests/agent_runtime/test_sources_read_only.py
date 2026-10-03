"""Every review route excludes each behavior-audited sources writer (#9560)."""

import ast
import asyncio
import importlib.util
import tomllib
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters import claude
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.review_mcp import (
    _render_codex_review_config,
    agy_full_review_settings,
    review_tools_allowed_csv,
)
from scripts.agent_runtime.sources_read_only import (
    SERVER_PATH,
    sources_tool_sets,
)
from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS, REVIEW_TOOLS

SOURCES_READ_ONLY_TOOLS, SOURCES_PERSISTING_TOOLS = sources_tool_sets()


def _server_config(cmd):
    """Apply config overrides in CLI order, including deliberate hostile grants."""
    server = {}
    for i, arg in enumerate(cmd[:-1]):
        if arg == "-c" and cmd[i + 1].startswith("mcp_servers.sources."):
            value = tomllib.loads(cmd[i + 1])["mcp_servers"]["sources"]
            server.update(value)
    return server


def test_shared_tool_set_equals_wire_annotations():
    spec = importlib.util.spec_from_file_location("sources_review_readers", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    tools = asyncio.run(server.list_tools())
    assert set(SOURCES_READ_ONLY_TOOLS) == {t.name for t in tools if t.annotations.read_only_hint is True}
    assert set(SOURCES_PERSISTING_TOOLS) == {t.name for t in tools if t.annotations.read_only_hint is not True}
    assert len(SOURCES_PERSISTING_TOOLS) == 5
    assert REVIEW_TOOLS <= FULL_REVIEW_TOOLS <= set(SOURCES_READ_ONLY_TOOLS)


def test_claude_adapter_keeps_no_tool_list_of_its_own():
    assert claude.sources_tool_sets is sources_tool_sets
    assert not hasattr(claude, "SOURCES_READ_ONLY_TOOLS")
    assert not hasattr(claude, "SOURCES_PERSISTING_TOOLS")


@pytest.mark.parametrize(
    "tool_config",
    [{"reviewer_tools": True}, {"allowed_tools": "mcp__sources__*"}, {"discussion_readonly": True}, None],
    ids=["reviewer", "explicit", "discussion", "ad-hoc"],
)
def test_claude_annotation_change_denies_new_writer_without_updating_a_list(tmp_path, monkeypatch, tool_config):
    path = tmp_path / "server.py"
    path.write_text(
        SERVER_PATH.read_text().replace(
            'name="verify_word",', 'name="verify_word", annotations=_PERSISTING_LOOKUP_TOOL,'
        )
    )
    monkeypatch.setattr(claude, "sources_tool_sets", lambda: sources_tool_sets(path))
    plan = claude.ClaudeAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=tool_config,
    )
    denies = plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
    assert "mcp__sources__verify_word" in denies
    assert "mcp__sources__verify_words" not in denies
    if "--allowedTools" in plan.cmd and tool_config == {"reviewer_tools": True}:
        allows = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
        assert "mcp__sources__verify_word" not in allows
        assert "mcp__sources__verify_words" in allows


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("writer", SOURCES_PERSISTING_TOOLS)
def test_formal_contracts_exclude_every_writer(access, writer):
    tools = REVIEW_TOOLS if access == "isolated" else FULL_REVIEW_TOOLS
    config = tomllib.loads(
        _render_codex_review_config(Path("/bin/python"), Path("/server.py"), {"LU_REVIEW_ACCESS": access})
    )
    sources = config["mcp_servers"]["sources"]
    assert set(sources["enabled_tools"]) == tools
    assert writer not in sources["enabled_tools"] and writer not in sources["tools"]
    assert sources["default_tools_approval_mode"] == "prompt"
    assert all(sources["tools"][tool]["approval_mode"] == "approve" for tool in tools)
    assert "verify_words" in tools
    assert f"mcp__sources__{writer}" not in review_tools_allowed_csv("claude", access).split(",")
    assert f"mcp(sources/{writer})" not in agy_full_review_settings()["permissions"]["allow"]
    assert "mcp(sources/verify_words)" in agy_full_review_settings()["permissions"]["allow"]


@pytest.mark.parametrize("session", [None, "resume-reader"])
@pytest.mark.parametrize("writer", SOURCES_PERSISTING_TOOLS)
def test_ad_hoc_codex_exposes_only_readers_even_with_caller_override(tmp_path, session, writer):
    plan = CodexAdapter().build_invocation(
        prompt="lookup",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session,
        tool_config={
            "mcp_servers": {
                "sources": {
                    "enabled_tools": [writer],
                    "default_tools_approval_mode": "approve",
                    "tools": {writer: {"approval_mode": "approve"}},
                }
            }
        },
    )
    try:
        server = _server_config(plan.cmd)
        assert set(server["enabled_tools"]) == set(SOURCES_READ_ONLY_TOOLS)
        assert set(server["tools"]) == set(SOURCES_READ_ONLY_TOOLS)
        assert writer not in server["enabled_tools"]
        assert server["tools"]["verify_word"]["approval_mode"] == "approve"
        assert server["default_tools_approval_mode"] == "prompt"
        assert "--dangerously-bypass-approvals-and-sandbox" not in plan.cmd
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("unknown_annotation", "sources_tool_annotation_unknown"),
        ("unknown_default", "sources_tool_annotation_default_unknown"),
        ("dynamic_list", "sources_tool_declarations_unknown"),
        ("dynamic_tool", "sources_tool_declaration_unknown"),
        ("duplicate", "sources_tool_name_unknown_or_duplicate"),
        ("empty", "sources_read_only_tools_empty"),
    ],
)
def test_annotation_reader_fails_closed(tmp_path, mutation, error):
    source = SERVER_PATH.read_text()
    if mutation == "unknown_annotation":
        source = source.replace("annotations=_PERSISTING_LOOKUP_TOOL", "annotations=unexpected")
    elif mutation == "unknown_default":
        source = source.replace(
            'kwargs.setdefault("annotations", _READ_ONLY_TOOL)', 'kwargs.setdefault("annotations", get_hint())'
        )
    elif mutation == "dynamic_list":
        tree = ast.parse(source)
        func = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "list_tools")
        func.body[-1].value = ast.Call(func=ast.Name(id="dynamic_tools", ctx=ast.Load()), args=[], keywords=[])
        source = ast.unparse(tree)
    elif mutation == "dynamic_tool":
        source = source.replace('_tool(\n            name="search_sources"', 'Tool(\n            name="search_sources"')
    elif mutation == "duplicate":
        source = source.replace('name="search_text"', 'name="search_sources"')
    elif mutation == "empty":
        source = source.replace("readOnlyHint=True", "readOnlyHint=False")
    path = tmp_path / "server.py"
    path.write_text(source)
    with pytest.raises(ValueError, match=error):
        sources_tool_sets(path)


def test_annotation_change_removes_new_writer_without_updating_a_list(tmp_path):
    path = tmp_path / "server.py"
    path.write_text(
        SERVER_PATH.read_text().replace(
            'name="verify_word",', 'name="verify_word", annotations=_PERSISTING_LOOKUP_TOOL,'
        )
    )
    readers, writers = sources_tool_sets(path)
    assert "verify_word" not in readers and "verify_word" in writers


def test_tool_sets_cache_successful_reads(tmp_path, monkeypatch):
    path = tmp_path / "server.py"
    path.write_text(SERVER_PATH.read_text())
    read_text = Path.read_text
    reads = []

    def counted_read(self, *args, **kwargs):
        reads.append(self)
        return read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counted_read)
    first = sources_tool_sets(path)
    assert sources_tool_sets(path) is first
    assert reads == [path]


def test_missing_server_fails_closed_and_can_be_retried(tmp_path):
    path = tmp_path / "server.py"
    with pytest.raises(FileNotFoundError):
        sources_tool_sets(path)
    path.write_text(SERVER_PATH.read_text())
    assert sources_tool_sets(path) == (SOURCES_READ_ONLY_TOOLS, SOURCES_PERSISTING_TOOLS)


@pytest.mark.parametrize("session", [None, "resume-reader"])
def test_ad_hoc_codex_missing_server_refuses_even_hostile_grants(tmp_path, monkeypatch, session):
    from scripts.agent_runtime.adapters import codex

    def missing():
        return sources_tool_sets(tmp_path / "missing.py")

    monkeypatch.setattr(codex, "sources_tool_sets", missing)
    with pytest.raises(FileNotFoundError):
        CodexAdapter().build_invocation(
            prompt="use mcp__sources__verify_words",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=session,
            tool_config={"mcp_servers": {"sources": {"default_tools_approval_mode": "approve"}}},
        )


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("session", [None, "resume-reader"])
def test_formal_codex_missing_server_keeps_explicit_contract(tmp_path, monkeypatch, access, session):
    from scripts.agent_runtime import review_mcp
    from scripts.agent_runtime.adapters import codex
    from scripts.review.receipts import ledger

    def unexpected():
        pytest.fail("formal explicit tool contracts must not read the server file")

    monkeypatch.setattr(codex, "sources_tool_sets", unexpected)
    monkeypatch.setattr(review_mcp, "sources_tool_sets", unexpected)
    monkeypatch.setattr(ledger, "sources_tool_sets", lambda: sources_tool_sets(tmp_path / "missing.py"))
    config = tomllib.loads(
        _render_codex_review_config(Path("/bin/python"), tmp_path / "missing.py", {"LU_REVIEW_ACCESS": access})
    )
    plan = CodexAdapter().build_invocation(
        prompt="use mcp__sources__verify_words",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session,
        tool_config={
            "codex_home_override": str(tmp_path / "scoped-home"),
            "mcp_config_path": str(tmp_path / "attempt.mcp.json"),
            "review_access": access,
        },
    )
    try:
        expected = REVIEW_TOOLS if access == "isolated" else FULL_REVIEW_TOOLS
        for sources in (config["mcp_servers"]["sources"], _server_config(plan.cmd)):
            assert set(sources["enabled_tools"]) == expected
            assert sources["tools"] == {tool: {"approval_mode": "approve"} for tool in expected}
            assert sources["default_tools_approval_mode"] == "prompt"
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("writer", ["verify_words", "search_resources"])
def test_formal_contract_refuses_reclassified_writer_at_call_time(tmp_path, monkeypatch, access, writer):
    from scripts.review.receipts import ledger

    path = tmp_path / "server.py"
    path.write_text(
        SERVER_PATH.read_text().replace(f'name="{writer}",', f'name="{writer}", annotations=_PERSISTING_LOOKUP_TOOL,')
    )
    monkeypatch.setattr(ledger, "sources_tool_sets", lambda: sources_tool_sets(path))
    with pytest.raises(ValueError, match="review_contract_contains_non_read_only_sources_tool"):
        ledger.review_tools(access)


def test_ad_hoc_config_missing_server_refuses(tmp_path, monkeypatch):
    from scripts.agent_runtime import review_mcp

    monkeypatch.setattr(review_mcp, "sources_tool_sets", lambda: sources_tool_sets(tmp_path / "missing.py"))
    with pytest.raises(FileNotFoundError):
        _render_codex_review_config(Path("/bin/python"), tmp_path / "missing.py", {})


@pytest.mark.parametrize("writer", SOURCES_PERSISTING_TOOLS)
def test_claude_ad_hoc_reviewer_denies_every_writer(tmp_path, writer):
    from scripts.agent_runtime.adapters.claude import ClaudeAdapter

    tc = {"reviewer_tools": True}
    plan = ClaudeAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=tc,
    )
    allows = plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    denies = plan.cmd[plan.cmd.index("--disallowedTools") + 1].split(",")
    assert f"mcp__sources__{writer}" in denies
    assert f"mcp__sources__{writer}" not in allows
    assert "mcp__sources__verify_words" in allows


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("writer", SOURCES_PERSISTING_TOOLS)
def test_formal_sources_wire_hides_and_refuses_writers_before_handler(monkeypatch, access, writer):
    """AGY and every formal route share this server contract, independent of CLI permissions."""
    from types import SimpleNamespace

    spec = importlib.util.spec_from_file_location("sources_review_wire", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(server)
    monkeypatch.setattr(server, "_review_env_engaged", lambda: True)
    monkeypatch.setattr(server, "_review_recorder", lambda: SimpleNamespace(mode="on", review_access=access))
    observed = []

    def record(_recorder, name, _args, content, *, status):
        observed.append((name, status))
        return content, False, None, None

    monkeypatch.setattr(server, "_review_record", record)
    listed = asyncio.run(server._on_list_tools(None, None))
    assert writer not in {tool.name for tool in listed.tools}
    assert "verify_words" in {tool.name for tool in listed.tools}
    result = asyncio.run(server._on_call_tool(None, server.CallToolRequestParams(name=writer, arguments={})))
    assert result.is_error is True
    assert result.content[0].text == f"Tool {writer} is not in the review tool list."
    assert observed == [(writer, "refused")]


def test_unverified_formal_codex_boundary_never_plans_or_launches_bypass(tmp_path, monkeypatch):
    from scripts.agent_runtime import runner
    from scripts.agent_runtime.errors import AgentUnavailableError

    def refused(*args, **kwargs):
        raise RuntimeError("filesystem_boundary_unverified")

    def unexpected(*args, **kwargs):
        pytest.fail("unverified parent must not construct or execute bypass argv")

    monkeypatch.setattr("scripts.agent_runtime.attempt_boundary.prepare_attempt_boundary", refused)
    monkeypatch.setattr(runner, "_load_adapter", unexpected)
    with pytest.raises(AgentUnavailableError, match="filesystem boundary refused"):
        runner.invoke("codex", "probe", cwd=tmp_path, tool_config={"review_id": "review"})


def test_sealed_codex_keeps_bypass_without_defining_sources(tmp_path):
    from scripts.review.isolation import review_isolation_tool_config
    from tests.agent_runtime.test_codex_sources_config_layers import write_config_probe_binary

    fake = write_config_probe_binary(tmp_path / "codex")
    snapshot, write = tmp_path / "snapshot", tmp_path / "write"
    snapshot.mkdir(mode=0o700)
    write.mkdir(mode=0o700)
    for child in ("tmp", "exec", "home", "xdg", "state"):
        (write / child).mkdir()
    tc = {
        **review_isolation_tool_config("codex"),
        "review_write_root": str(write),
        "review_snapshot_root": str(snapshot),
        "review_engine_binary": str(fake),
    }
    plan = CodexAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=snapshot,
        model=None,
        task_id=None,
        session_id=None,
        tool_config=tc,
    )
    try:
        assert "--dangerously-bypass-approvals-and-sandbox" in plan.cmd
        assert "--ignore-user-config" in plan.cmd
        assert not any(arg.startswith("mcp_servers.sources.") for arg in plan.cmd)
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize("session", [None, "resume-reader"])
def test_ignore_user_config_without_sources_never_defines_partial_server(tmp_path, session):
    plan = CodexAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session,
        tool_config={"ignore_user_config": True},
    )
    try:
        assert "--ignore-user-config" in plan.cmd
        assert not any(arg.startswith("mcp_servers.sources.") for arg in plan.cmd)
    finally:
        plan.output_file.unlink()


def test_ignore_user_config_with_explicit_sources_still_excludes_writers(tmp_path):
    plan = CodexAdapter().build_invocation(
        prompt="lookup",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={
            "ignore_user_config": True,
            "mcp_servers": {"sources": {"command": "/bin/true", "enabled_tools": list(SOURCES_PERSISTING_TOOLS)}},
        },
    )
    try:
        assert set(_server_config(plan.cmd)["enabled_tools"]) == set(SOURCES_READ_ONLY_TOOLS)
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("session", [None, "resume-reader"])
def test_scoped_codex_effective_exposure_matches_contract(tmp_path, access, session):
    home = tmp_path / "scoped-home"
    home.mkdir()
    config = _render_codex_review_config(Path("/bin/python"), Path("/server.py"), {"LU_REVIEW_ACCESS": access})
    (home / "config.toml").write_text(config)
    plan = CodexAdapter().build_invocation(
        prompt="use mcp__sources__verify_words",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=session,
        tool_config={
            "codex_home_override": str(home),
            "mcp_config_path": str(tmp_path / "attempt.mcp.json"),
            "strict_mcp_config": True,
            "mcp_server_names": ["sources"],
            "review_access": access,
        },
    )
    try:
        sources = tomllib.loads(config)["mcp_servers"]["sources"]
        sources.update(_server_config(plan.cmd))
        contract = REVIEW_TOOLS if access == "isolated" else FULL_REVIEW_TOOLS
        assert set(sources["enabled_tools"]) == contract
        assert set(sources["tools"]) == contract
        assert not set(SOURCES_PERSISTING_TOOLS) & set(sources["enabled_tools"])
    finally:
        plan.output_file.unlink()


@pytest.mark.parametrize("boundary", [None, object()])
def test_unbound_attempt_sandbox_flag_cannot_enable_codex_bypass(tmp_path, boundary):
    with pytest.raises(ValueError, match="attempt_os_sandbox requires the parent attempt boundary"):
        CodexAdapter().build_invocation(
            prompt="review",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"attempt_os_sandbox": True, "review_attempt_boundary": boundary},
        )
