from __future__ import annotations

import json
import os
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
            workspace_dir=linear_pipeline.PROJECT_ROOT,
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
        workspace_dir=linear_pipeline.PROJECT_ROOT,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["mcp_servers"]["sources"]["url"].endswith("/mcp")
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


def test_runtime_tool_config_codex_tools_disables_writer_unsafe_features(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """V7 codex-tools writer must disable Codex's non-MCP tool families.

    Failure trail:
    1. 2026-05-22 a1-my-morning-20260522-181103 — writer called
       ``exec_command`` (surfaced by ``shell_tool``) 18× and tripped
       ``writer_trace_isolation`` with ``wrong_tool_family``. PR #2227
       added ``shell_tool`` to ``disable_features``.
    2. 2026-05-22 a1-my-morning-20260522-191117 — with shell_tool
       disabled, writer gravitated to ``mcp__node_repl__js`` (5×) +
       ``get_goal`` (1×). Issue #2228. The disable list is now broadened
       to also cover ``goals``, ``browser_use``, ``in_app_browser``,
       ``image_generation``, ``apps``, ``plugins``, ``multi_agent`` —
       per `ab ask-codex` recommendation 2026-05-22.

    Defense-in-depth: also applies when codex-tools is invoked as the
    reviewer — reviewers should also only call ``mcp__sources__*``.
    """
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    config = linear_pipeline._runtime_tool_config("codex-tools", workspace_dir=linear_pipeline.PROJECT_ROOT)

    disable_features = config.get("disable_features") or []
    expected_disables = {
        "shell_tool",
        "goals",
        "browser_use",
        "in_app_browser",
        "image_generation",
        "apps",
        "plugins",
        "multi_agent",
    }
    assert set(disable_features) >= expected_disables, (
        f"missing disables: {expected_disables - set(disable_features)}; "
        f"got: {disable_features}"
    )


def test_runtime_tool_config_cursor_tools_scoped_workspace(
    tmp_path: Path,
) -> None:
    """cursor-tools must materialize a scoped .cursor/mcp.json in the workspace."""
    module_dir = tmp_path / "a1" / "my-morning"
    module_dir.mkdir(parents=True)

    config = linear_pipeline._runtime_tool_config("cursor-tools", workspace_dir=module_dir)

    workspace_str = config.get("cursor_workspace")
    assert workspace_str == str(module_dir.resolve())

    mcp_config_path = module_dir / ".cursor" / "mcp.json"
    assert mcp_config_path.exists()
    content = mcp_config_path.read_text(encoding="utf-8")
    assert '"url": "http://127.0.0.1:8766/mcp"' in content


def test_runtime_tool_config_codex_tools_scoped_codex_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """codex-tools must materialize a scoped ``$CODEX_HOME``.

    Per-invocation ``-c mcp_servers.X.url=...`` MERGES with the
    user-level config; it doesn't REPLACE. Codex.app's
    ``node_repl``/``openaiDeveloperDocs``/``codex_apps.github`` MCP
    server registrations therefore survive ``--ignore-user-config`` and
    ``-c`` overrides. The real isolation mechanism is a scoped
    ``$CODEX_HOME`` containing ONLY the sources MCP definition + a
    symlink of the user's ``auth.json``. Verified empirically (smoke
    test 2026-05-22) and confirmed via ``ab ask-codex``.
    """
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    # Stand in a fake $CODEX_HOME so we don't depend on a real Codex
    # login on the runner; auth.json just needs to exist for the helper
    # to accept the symlink target.
    fake_home = tmp_path / "fake-codex-home"
    fake_home.mkdir()
    (fake_home / "auth.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(fake_home))

    config = linear_pipeline._runtime_tool_config("codex-tools", workspace_dir=linear_pipeline.PROJECT_ROOT)

    scoped_home_str = config.get("codex_home_override")
    assert scoped_home_str, "codex-tools must populate codex_home_override"

    scoped_home = Path(scoped_home_str)
    assert scoped_home.exists()
    assert scoped_home != fake_home, "scoped home must NOT be the user's CODEX_HOME"

    # Config must register sources and nothing else.
    config_toml = (scoped_home / "config.toml").read_text(encoding="utf-8")
    assert "[mcp_servers.sources]" in config_toml
    assert "node_repl" not in config_toml
    assert "openaiDeveloperDocs" not in config_toml
    assert "codex_apps" not in config_toml
    assert 'url = "http://127.0.0.1:8766/mcp"' in config_toml

    # Auth must be a symlink to the user's auth.json — copies would mean
    # token refreshes don't propagate.
    auth_link = scoped_home / "auth.json"
    assert auth_link.is_symlink()
    assert Path(auth_link.resolve()) == (fake_home / "auth.json").resolve()


def test_runtime_tool_config_codex_tools_nests_home_in_runtime_tmp_lease(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    fake_home = tmp_path / "fake-codex-home"
    fake_home.mkdir()
    (fake_home / "auth.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(fake_home))

    tmp_root = tmp_path / "os-tmp"
    tmp_root.mkdir()
    lease_root = tmp_root / "learn-ukrainian" / "task-4956"
    lease_root.mkdir(parents=True)
    monkeypatch.setattr(linear_pipeline.tempfile, "gettempdir", lambda: str(lease_root))
    monkeypatch.setenv("TMPDIR", str(lease_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_ROOT", str(lease_root))
    monkeypatch.setenv("LU_RUNTIME_TMP_BASE_ROOT", str(tmp_root))

    config = linear_pipeline._runtime_tool_config(
        "codex-tools",
        workspace_dir=linear_pipeline.PROJECT_ROOT,
    )

    assert config["codex_home_override"] == str(
        lease_root / f"codex-v7-writer-{os.getuid()}",
    )


def test_ensure_codex_writer_home_keeps_shared_no_task_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_home = tmp_path / "fake-codex-home"
    fake_home.mkdir()
    (fake_home / "auth.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(fake_home))
    monkeypatch.delenv("LU_RUNTIME_TMP_ROOT", raising=False)
    monkeypatch.setattr(linear_pipeline.tempfile, "gettempdir", lambda: str(tmp_path))

    scoped_home = linear_pipeline._ensure_codex_writer_home()

    assert scoped_home == str(tmp_path / f"codex-v7-writer-{os.getuid()}")


def test_runtime_tool_config_codex_tools_scoped_home_emits_event(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Materialization fires ``codex_writer_home_resolved`` AFTER
    ``mcp_config_resolved`` so downstream observability sees the
    expected first event unchanged."""
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    fake_home = tmp_path / "fake-codex-home"
    fake_home.mkdir()
    (fake_home / "auth.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(fake_home))

    events: list[tuple[str, dict[str, Any]]] = []
    linear_pipeline._runtime_tool_config(
        "codex-tools",
        workspace_dir=linear_pipeline.PROJECT_ROOT,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    event_names = [name for name, _ in events]
    assert event_names[0] == "mcp_config_resolved", (
        f"first event must remain mcp_config_resolved, got {event_names!r}"
    )
    assert "codex_writer_home_resolved" in event_names

    home_event = next(fields for name, fields in events if name == "codex_writer_home_resolved")
    assert home_event["real_home"] == str(fake_home)
    assert home_event["scoped_home"].endswith(f"codex-v7-writer-{os.getuid()}")


def test_runtime_tool_config_codex_tools_missing_auth_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When CODEX_HOME has no auth.json, emit a warning event but don't
    raise — config resolution must work on CI runners that have never
    run ``codex login``. The actual ``codex exec`` invocation will fail
    loud with its own missing-auth error if it tries to run."""
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    bad_home = tmp_path / "no-auth-codex-home"
    bad_home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(bad_home))

    events: list[tuple[str, dict[str, Any]]] = []
    config = linear_pipeline._runtime_tool_config(
        "codex-tools",
        workspace_dir=linear_pipeline.PROJECT_ROOT,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    # Config resolution succeeds.
    assert config.get("codex_home_override")

    # But the missing-auth warning event is emitted.
    event_names = [name for name, _ in events]
    assert "codex_writer_home_auth_missing" in event_names

    # And the resolved event records auth_present=False.
    resolved = next(fields for name, fields in events if name == "codex_writer_home_resolved")
    assert resolved["auth_present"] is False

    # No broken symlink left in the scoped home.
    scoped_home = Path(config["codex_home_override"])
    auth_link = scoped_home / "auth.json"
    assert not auth_link.exists() and not auth_link.is_symlink()


def test_runtime_tool_config_non_codex_tools_no_disable_features(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-codex writers must NOT inherit the codex-specific disable.

    The ``disable_features`` flag is a Codex CLI feature; other adapters
    don't understand the key. The pipeline emits it only for codex-tools.
    """
    config_path = _valid_sources_config(tmp_path / ".mcp.json")
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", config_path)

    for agent in ("claude-tools", "gemini-tools", "grok-tools", "deepseek-tools"):
        config = linear_pipeline._runtime_tool_config(agent, workspace_dir=linear_pipeline.PROJECT_ROOT)
        assert "disable_features" not in config, (
            f"{agent} unexpectedly carries disable_features={config.get('disable_features')!r}"
        )


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
        workspace_dir=linear_pipeline.PROJECT_ROOT,
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
            workspace_dir=linear_pipeline.PROJECT_ROOT,
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
        workspace_dir=linear_pipeline.PROJECT_ROOT,
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
            workspace_dir=linear_pipeline.PROJECT_ROOT,
            event_sink=lambda event, **fields: events.append((event, fields)),
        )

    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "gemini-tools"
    assert events[0][1]["resolution_status"] == "config_empty"
    assert events[0][1]["resolved_servers"] == []


def test_runtime_tool_config_agy_tools_emits_resolution_event_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """agy-tools resolves the ``sources`` MCP from agy's global Antigravity
    config (``AGY_APP_DATA_DIR/mcp_config.json``, ``httpUrl`` streamable-HTTP).
    The runtime MCP_TOOLS_NEVER_INVOKED gate remains the load-bearing check
    that a configured server is actually invoked."""
    app_data_dir = tmp_path / "antigravity-cli"
    app_data_dir.mkdir()
    _write_mcp_config(
        app_data_dir / "mcp_config.json",
        {"mcpServers": {"sources": {"httpUrl": "http://127.0.0.1:8766/mcp"}}},
    )
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data_dir))
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        "agy-tools",
        workspace_dir=linear_pipeline.PROJECT_ROOT,
        event_sink=lambda event, **fields: events.append((event, fields)),
    )

    assert config["output_format"] == "stream-json"
    assert config["mcp_server_names"] == ["sources"]
    assert events[0][0] == "mcp_config_resolved"
    assert events[0][1]["writer"] == "agy-tools"
    assert events[0][1]["resolution_status"] == "ok"
    assert events[0][1]["resolved_servers"] == ["sources"]


@pytest.mark.parametrize("writer", ["deepseek-tools"])
def test_runtime_tool_config_hermes_tools_emits_resolution_event_success(
    writer: str,
) -> None:
    events: list[tuple[str, dict[str, Any]]] = []

    config = linear_pipeline._runtime_tool_config(
        writer,
        workspace_dir=linear_pipeline.PROJECT_ROOT,
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
        linear_pipeline._runtime_tool_config(
            "phantom-tools", workspace_dir=linear_pipeline.PROJECT_ROOT
        )


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
