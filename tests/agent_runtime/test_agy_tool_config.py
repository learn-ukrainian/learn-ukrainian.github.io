"""Focused tests for agy MCP tool_config resolution."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime.tool_config import _load_mcp_config, build_mcp_tool_config


@pytest.fixture(autouse=True)
def _clear_mcp_config_cache() -> None:
    _load_mcp_config.cache_clear()
    yield
    _load_mcp_config.cache_clear()


def _write_agy_mcp_config(app_data_dir: Path, data: dict) -> Path:
    app_data_dir.mkdir(parents=True, exist_ok=True)
    config_path = app_data_dir / "mcp_config.json"
    config_path.write_text(json.dumps(data), encoding="utf-8")
    return config_path


def test_agy_resolves_requested_global_mcp_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_data_dir = tmp_path / "antigravity-cli"
    config_path = _write_agy_mcp_config(
        app_data_dir,
        {
            "mcpServers": {
                "sources": {"httpUrl": "http://127.0.0.1:8766/mcp"},
            }
        },
    )
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data_dir))

    tool_config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}
    assert diagnostics["config_path"] == str(config_path.resolve())
    assert diagnostics["resolution_status"] == "ok"
    assert diagnostics["resolved_servers"] == ["sources"]
    assert diagnostics["missing_server_names"] == []


def test_agy_reports_missing_requested_global_mcp_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_data_dir = tmp_path / "antigravity-cli"
    config_path = _write_agy_mcp_config(
        app_data_dir,
        {
            "mcpServers": {
                "sources": {"httpUrl": "http://127.0.0.1:8766/mcp"},
            }
        },
    )
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data_dir))

    tool_config, diagnostics = build_mcp_tool_config(
        "agy",
        mcp_servers=["nonexistent"],
    )

    assert tool_config is None
    assert diagnostics["config_path"] == str(config_path.resolve())
    assert diagnostics["resolution_status"] == "servers_not_found"
    assert diagnostics["resolved_servers"] == []
    assert diagnostics["missing_server_names"] == ["nonexistent"]


def test_agy_missing_global_mcp_config_is_config_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_data_dir = tmp_path / "antigravity-cli"
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data_dir))

    tool_config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])

    assert tool_config is None
    assert diagnostics["config_path"] == str(
        (app_data_dir / "mcp_config.json").resolve()
    )
    assert diagnostics["resolution_status"] == "config_empty"
    assert diagnostics["resolved_servers"] == []
    assert diagnostics["missing_server_names"] == []
