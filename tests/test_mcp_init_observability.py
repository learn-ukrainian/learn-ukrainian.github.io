from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime import tool_config as wiki_tool_config_mod

from scripts.agent_runtime import tool_config as tool_config_mod
from scripts.agent_runtime.runner import _MCP_TOOL_EVENT_RE, _McpRuntimeObserver
from scripts.build import linear_pipeline
from scripts.wiki import review as wiki_review


@pytest.fixture(autouse=True)
def _clear_mcp_config_cache() -> None:
    tool_config_mod._load_mcp_config.cache_clear()
    wiki_tool_config_mod._load_mcp_config.cache_clear()
    yield
    tool_config_mod._load_mcp_config.cache_clear()
    wiki_tool_config_mod._load_mcp_config.cache_clear()


def _write_mcp_config(path: Path, data: dict[str, Any]) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _valid_sources_config(path: Path) -> Path:
    return _write_mcp_config(
        path,
        {
            "mcpServers": {
                "sources": {
                    "type": "streamable-http",
                    "url": "http://127.0.0.1:8766/mcp",
                }
            }
        },
    )


def test_build_mcp_tool_config_diagnostics_ok(tmp_path: Path) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")

    config, diagnostics = tool_config_mod.build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert config == {
        "mcp_servers": {
            "sources": {
                "url": "http://127.0.0.1:8766/mcp",
            }
        }
    }
    assert diagnostics == {
        "requested_servers": ["sources"],
        "resolved_servers": ["sources"],
        "config_path": str(config_path.resolve()),
        "resolution_status": "ok",
        "missing_server_names": [],
    }


def test_build_mcp_tool_config_diagnostics_config_missing(tmp_path: Path) -> None:
    config_path = tmp_path / ".mcp.json"

    config, diagnostics = tool_config_mod.build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert config is None
    assert diagnostics["resolution_status"] == "config_missing"
    assert diagnostics["requested_servers"] == ["sources"]
    assert diagnostics["resolved_servers"] == []


def test_build_mcp_tool_config_diagnostics_config_empty(tmp_path: Path) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})

    config, diagnostics = tool_config_mod.build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert config is None
    assert diagnostics["resolution_status"] == "config_empty"
    assert diagnostics["requested_servers"] == ["sources"]
    assert diagnostics["resolved_servers"] == []


def test_build_mcp_tool_config_diagnostics_servers_not_found(tmp_path: Path) -> None:
    config_path = _write_mcp_config(
        tmp_path / ".mcp.json",
        {
            "mcpServers": {
                "other": {
                    "type": "streamable-http",
                    "url": "http://127.0.0.1:9999/mcp",
                }
            }
        },
    )

    config, diagnostics = tool_config_mod.build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["missing_server_names"] == ["sources"]
    assert diagnostics["resolved_servers"] == []


def test_build_mcp_tool_config_rejects_legacy_sse_codex_endpoint(
    tmp_path: Path,
) -> None:
    config_path = _write_mcp_config(
        tmp_path / ".mcp.json",
        {
            "mcpServers": {
                "sources": {
                    "type": "sse",
                    "url": "http://127.0.0.1:8766/sse",
                }
            }
        },
    )

    config, diagnostics = tool_config_mod.build_mcp_tool_config(
        "codex",
        mcp_servers=["sources"],
        mcp_config_path=config_path,
    )

    assert config is None
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["missing_server_names"] == ["sources"]


def test_runtime_tool_config_raises_and_emits_resolution_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="tool-less"):
        linear_pipeline._runtime_tool_config(
            "codex-tools",
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events == [
        (
            "mcp_config_resolved",
            {
                "writer": "codex-tools",
                "requested_servers": ["sources"],
                "resolved_servers": [],
                "config_path": str(config_path.resolve()),
                "resolution_status": "config_empty",
                "missing_server_names": [],
            },
        )
    ]


def test_runtime_tool_config_emits_resolution_event_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        "codex-tools",
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["mcp_servers"]["sources"]["url"].endswith("/mcp")
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_wiki_review_codex_emits_resolution_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(wiki_tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    config = wiki_review._tool_config_for(
        "codex",
        needs_mcp=True,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config is not None
    assert config["mcp_servers"]["sources"]["url"].endswith("/mcp")
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["reviewer"] == "codex"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_wiki_review_codex_raises_when_unconfigured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})
    monkeypatch.setattr(wiki_tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    with pytest.raises(wiki_review.WikiReviewError, match="tool-less"):
        wiki_review._tool_config_for(
            "codex",
            needs_mcp=True,
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["reviewer"] == "codex"
    assert events[0][1]["resolution_status"] == "config_empty"
    assert events[0][1]["resolved_servers"] == []


def test_wiki_review_claude_no_raise_when_unconfigured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / ".mcp.json"
    monkeypatch.setattr(wiki_tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    config = wiki_review._tool_config_for(
        "claude",
        needs_mcp=True,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config is None
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["reviewer"] == "claude"
    assert events[0][1]["resolution_status"] == "config_missing"
    assert events[0][1]["resolved_servers"] == []


def test_runtime_tool_config_claude_tools_emits_resolution_event_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        "claude-tools",
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["mcp_config_path"] == str(config_path.resolve())
    assert config["allowed_tools"] == "mcp__sources__*"
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "claude-tools"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_runtime_tool_config_claude_tools_raises_when_unconfigured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="tool-less"):
        linear_pipeline._runtime_tool_config(
            "claude-tools",
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "claude-tools"
    assert events[0][1]["resolution_status"] == "config_empty"
    assert events[0][1]["resolved_servers"] == []


def test_runtime_tool_config_gemini_tools_emits_resolution_event_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        "gemini-tools",
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["mcp_server_names"] == ["sources"]
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "gemini-tools"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_runtime_tool_config_gemini_tools_raises_when_unconfigured(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    with pytest.raises(linear_pipeline.LinearPipelineError, match="tool-less"):
        linear_pipeline._runtime_tool_config(
            "gemini-tools",
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "gemini-tools"
    assert events[0][1]["resolution_status"] == "config_empty"
    assert events[0][1]["resolved_servers"] == []


@pytest.mark.parametrize("writer", ["grok-tools", "deepseek-tools", "qwen-tools"])
def test_runtime_tool_config_hermes_tools_emits_resolution_event_success(
    writer: str,
) -> None:
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        writer,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["hermes_mcp_servers"] == ["sources"]
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == writer
    assert events[0][1]["config_path"] == str(Path.home() / ".hermes" / "config.yaml")
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_runtime_tool_config_unknown_tools_writer_raises() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="Unknown -tools writer",
    ):
        linear_pipeline._runtime_tool_config("phantom-tools")


def test_invoke_writer_refuses_tool_less_codex_before_invoker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _write_mcp_config(tmp_path / ".mcp.json", {"mcpServers": {}})
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)
    events: list[tuple[str, dict[str, Any]]] = []

    def fail_if_called(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("writer invoker should not run without MCP servers")

    with pytest.raises(linear_pipeline.LinearPipelineError, match="tool-less"):
        linear_pipeline.invoke_writer(
            "Write the module.",
            "codex-tools",
            cwd=tmp_path,
            invoker=fail_if_called,
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["resolution_status"] == "config_empty"


def test_mcp_runtime_observer_emits_ready() -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None

    observer.observe_line("mcp: sources/verify_words started", stream="stdout")
    observer.finalize()

    assert events[0][0] == "mcp_runtime_init"
    assert events[0][1]["server"] == "sources"
    assert events[0][1]["status"] == "ready"
    assert events[0][1]["tool"] == "verify_words"


def test_mcp_runtime_observer_emits_failed_for_codex_rmcp_error() -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:9999/sse"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None

    observer.observe_line(
        "2026-05-08T11:37:32.975327Z ERROR rmcp::transport::worker: "
        "worker quit with fatal: Transport channel closed, when "
        'Client(HttpRequest(HttpRequest("http/request failed: error sending '
        'request for url (http://127.0.0.1:9999/sse)")))',
        stream="stderr",
    )

    assert events[0][0] == "mcp_runtime_init"
    assert events[0][1]["server"] == "sources"
    assert events[0][1]["status"] == "failed"


def test_mcp_runtime_observer_matches_failed_url_with_trailing_slash() -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp/"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None

    observer.observe_line(
        "2026-05-08T11:37:32.975327Z ERROR rmcp::transport::worker: "
        "worker quit with fatal: Transport channel closed, when "
        'Client(HttpRequest(HttpRequest("http/request failed: error sending '
        'request for url (http://127.0.0.1:8766/mcp)")))',
        stream="stderr",
    )

    assert events[0][0] == "mcp_runtime_init"
    assert events[0][1]["server"] == "sources"
    assert events[0][1]["status"] == "failed"


@pytest.mark.parametrize(
    "line",
    [
        "2026-05-08T11:37:32.975327Z ERROR rmcp::transport::worker: "
        "worker quit with fatal: Transport channel closed",
        "2026-05-08T11:37:32.975327Z ERROR rmcp::transport::worker: "
        "worker quit with fatal: Transport channel closed, when "
        'Client(HttpRequest(HttpRequest("http/request failed: error sending '
        'request for url (http://127.0.0.1:4444/mcp)")))',
    ],
)
def test_mcp_runtime_observer_warns_for_unattributed_failure(line: str) -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp"},
                "wikipedia": {"url": "http://127.0.0.1:8767/mcp"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None

    observer.observe_line(line, stream="stderr")

    assert [event for event, _fields in events] == [
        "mcp_runtime_unattributed_failure"
    ]
    assert events[0][1]["raw_line"] == line[:500]
    assert events[0][1]["task_id"] == "writer"
    assert events[0][1]["stream"] == "stderr"


def test_mcp_runtime_observer_failed_suppresses_prior_ready() -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None

    observer.observe_lines(
        [
            "mcp: sources/verify_words started",
            "2026-05-08T11:37:32.975327Z ERROR rmcp::transport::worker: "
            "worker quit with fatal: Transport channel closed, when "
            'Client(HttpRequest(HttpRequest("http/request failed: error sending '
            'request for url (http://127.0.0.1:8766/mcp)")))',
        ],
        start_index=0,
        stream="stdout",
    )
    observer.finalize()

    assert [event for event, _fields in events] == ["mcp_runtime_init"]
    assert events[0][1]["server"] == "sources"
    assert events[0][1]["status"] == "failed"


def test_mcp_runtime_observer_emits_timeout() -> None:
    events: list[tuple[str, dict[str, Any]]] = []
    observer = _McpRuntimeObserver.from_tool_config(
        agent_name="codex",
        task_id="writer",
        tool_config={
            "mcp_servers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp"},
            }
        },
        event_sink=lambda event, **fields: events.append((event, fields)),
        start_time=time.monotonic(),
    )
    assert observer is not None
    observer.timeout_s = 0

    observer.maybe_emit_timeout(time.monotonic())

    assert events[0][0] == "mcp_runtime_init"
    assert events[0][1]["server"] == "sources"
    assert events[0][1]["status"] == "timeout"


def test_mcp_tool_event_regex_matches_real_codex_fixture() -> None:
    fixture = (
        Path(__file__).parent
        / "fixtures"
        / "codex_mcp_init_stdout.txt"
    ).read_text(encoding="utf-8")

    matches = list(_MCP_TOOL_EVENT_RE.finditer(fixture))

    assert len(matches) == 2
    assert Counter(
        (match.group("server"), match.group("tool")) for match in matches
    ) == {("sources", "verify_word"): 2}
    assert [match.group(0) for match in matches] == [
        "mcp: sources/verify_word started",
        "mcp: sources/verify_word (completed)",
    ]
