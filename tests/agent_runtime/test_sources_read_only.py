"""Every review route excludes each behavior-audited sources writer (#9560)."""

import ast
import asyncio
import importlib.util
import tomllib
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.review_mcp import (
    _render_codex_review_config,
    agy_full_review_settings,
    review_tools_allowed_csv,
)
from scripts.agent_runtime.sources_read_only import (
    SERVER_PATH,
    SOURCES_PERSISTING_TOOLS,
    SOURCES_READ_ONLY_TOOLS,
    sources_tool_sets,
)
from scripts.review.receipts.ledger import FULL_REVIEW_TOOLS, REVIEW_TOOLS


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


@pytest.mark.parametrize("access", ["isolated", "full"])
@pytest.mark.parametrize("writer", SOURCES_PERSISTING_TOOLS)
def test_claude_ad_hoc_and_full_routes_deny_every_writer(tmp_path, access, writer):
    from scripts.agent_runtime.adapters.claude import ClaudeAdapter

    tc = {"reviewer_tools": True}
    if access == "full":
        config = tmp_path / "mcp.json"
        config.write_text('{"mcpServers":{"sources":{}}}')
        tc.update(mcp_config_path=str(config), strict_mcp_config=True, review_access="full")
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


@pytest.mark.parametrize("flag", ["review_isolation"])
def test_parent_sandbox_codex_keeps_bypass_with_writers_unexposed(tmp_path, flag):
    snapshot, write = tmp_path / "snapshot", tmp_path / "write"
    snapshot.mkdir(mode=0o700)
    write.mkdir(mode=0o700)
    for child in ("tmp", "exec", "home", "xdg", "state"):
        (write / child).mkdir()
    tc = {flag: True, "review_write_root": str(write)}
    if flag == "review_isolation":
        tc.update(review_snapshot_root=str(snapshot), review_engine_binary="/bin/true")
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
        sources = _server_config(plan.cmd)
        assert set(sources["enabled_tools"]) == set(SOURCES_READ_ONLY_TOOLS)
        assert not set(SOURCES_PERSISTING_TOOLS) & set(sources["enabled_tools"])
        assert sources["tools"]["verify_words"]["approval_mode"] == "approve"
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
