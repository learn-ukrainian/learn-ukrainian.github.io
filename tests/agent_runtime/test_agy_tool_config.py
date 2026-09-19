"""Focused tests for agy MCP tool_config resolution."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from agent_runtime import tool_config as tool_config_mod
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


def test_agy_resolves_current_default_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / ".gemini" / "config"
    config_path = _write_agy_mcp_config(
        config_dir,
        {
            "mcpServers": {
                "sources": {"url": "http://127.0.0.1:8766/mcp"},
            }
        },
    )
    monkeypatch.delenv("AGY_APP_DATA_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    tool_config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}
    assert diagnostics["config_path"] == str(config_path.resolve())
    assert diagnostics["resolution_status"] == "ok"
    assert diagnostics["resolved_servers"] == ["sources"]


def test_agy_falls_back_to_legacy_antigravity_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / ".gemini" / "antigravity-cli"
    config_path = _write_agy_mcp_config(
        config_dir,
        {
            "mcpServers": {
                "sources": {"httpUrl": "http://127.0.0.1:8766/mcp"},
            }
        },
    )
    monkeypatch.delenv("AGY_APP_DATA_DIR", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    tool_config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}
    assert diagnostics["config_path"] == str(config_path.resolve())
    assert diagnostics["resolution_status"] == "ok"
    assert diagnostics["resolved_servers"] == ["sources"]


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


# --- #7994: `agy mcp list` catalog register + fail-closed preflight ---------

_SOURCES_URL = "http://127.0.0.1:8766/mcp"

_FAKE_AGY = '''#!{python}
"""Hermetic `agy mcp` stand-in: JSON state file, real CLI table output."""
import json, os, sys
from pathlib import Path

state_path = Path(os.environ["FAKE_AGY_STATE"])
state = json.loads(state_path.read_text())
args = sys.argv[1:]
assert args[0] == "mcp", args
state["calls"].append(args[1:])
if args[1] == "list":
    print("NAME     TYPE   STATUS   COMMAND/URL")
    for name, row in state["servers"].items():
        print(f"{{name}}  {{row['type']}}  {{row['status']}}  {{row['target']}}")
elif args[1] == "add":
    assert args[2:4] == ["--type", "http"], args
    if not state.get("add_is_noop"):
        state["servers"][args[4]] = {{"type": "http", "status": "enabled", "target": args[5]}}
    print(f'Added MCP server "{{args[4]}}" (http)')
else:
    sys.exit(2)
state_path.write_text(json.dumps(state))
'''

_DEAD_STDIO = {"sources": {"type": "stdio", "status": "enabled", "target": ""}}
_LIVE_HTTP = {"sources": {"type": "http", "status": "enabled", "target": _SOURCES_URL}}


@pytest.fixture
def fake_agy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Install a fake `agy` on PATH; returns (seed, calls) accessors."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    agy = bin_dir / "agy"
    agy.write_text(_FAKE_AGY.format(python=sys.executable), encoding="utf-8")
    agy.chmod(0o755)
    state_path = tmp_path / "fake-agy-state.json"
    monkeypatch.setenv("FAKE_AGY_STATE", str(state_path))
    monkeypatch.setenv("PATH", f"{bin_dir}:/usr/bin:/bin")

    repo_mcp = tmp_path / ".mcp.json"
    repo_mcp.write_text(
        json.dumps({"mcpServers": {"sources": {"type": "streamable-http", "url": _SOURCES_URL}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(tool_config_mod, "_DEFAULT_MCP_CONFIG_PATH", repo_mcp)

    def seed(servers: dict, **extra) -> None:
        state_path.write_text(json.dumps({"servers": servers, "calls": [], **extra}))

    def calls() -> list[list[str]]:
        return json.loads(state_path.read_text())["calls"]

    return seed, calls


def test_agy_server_usable_accepts_cli_server_url_shape() -> None:
    usable = tool_config_mod._agy_server_is_usable
    # Exact shape `agy mcp add --type http` writes.
    assert usable({"disabled": False, "serverUrl": _SOURCES_URL})
    assert usable({"httpUrl": _SOURCES_URL})
    assert usable({"command": "npx", "args": ["-y", "server"]})
    assert not usable({"disabled": True, "serverUrl": _SOURCES_URL})
    assert not usable({"args": ["orphan"]})


def test_agy_resolver_accepts_server_url_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app_data_dir = tmp_path / "agy"
    _write_agy_mcp_config(
        app_data_dir,
        {"mcpServers": {"sources": {"disabled": False, "serverUrl": _SOURCES_URL}}},
    )
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data_dir))

    tool_config, diagnostics = build_mcp_tool_config("agy", mcp_servers=["sources"])

    assert tool_config == {"mcp_server_names": ["sources"]}
    assert diagnostics["resolution_status"] == "ok"


def test_dead_stdio_catalog_fails_preflight(fake_agy) -> None:
    seed, _calls = fake_agy
    seed(_DEAD_STDIO)

    with pytest.raises(tool_config_mod.AgyMcpCatalogError, match="no command/URL") as excinfo:
        tool_config_mod.assert_agy_mcp_catalog_visible(["sources"])
    assert "re-run the register helper" in str(excinfo.value)


@pytest.mark.parametrize(
    "servers",
    [
        {},
        {"sources": {"type": "http", "status": "disabled", "target": _SOURCES_URL}},
        {"sources": {"type": "http", "status": "enabled", "target": "http://127.0.0.1:9999/mcp"}},
    ],
    ids=["unregistered", "disabled", "wrong-url"],
)
def test_unusable_catalog_rows_fail_preflight(fake_agy, servers: dict) -> None:
    seed, _calls = fake_agy
    seed(servers)

    with pytest.raises(tool_config_mod.AgyMcpCatalogError):
        tool_config_mod.assert_agy_mcp_catalog_visible(["sources"])


def test_http_catalog_passes_preflight(fake_agy) -> None:
    seed, calls = fake_agy
    seed(_LIVE_HTTP)

    assert tool_config_mod.assert_agy_mcp_catalog_visible(["sources"]) == _LIVE_HTTP
    assert calls() == [["list"]]


def test_register_helper_repairs_dead_stdio_and_is_idempotent(fake_agy) -> None:
    seed, calls = fake_agy
    seed(_DEAD_STDIO)

    first = tool_config_mod.ensure_agy_mcp_catalog(["sources"])
    second = tool_config_mod.ensure_agy_mcp_catalog(["sources"])

    assert first == {"registered": ["sources"], "catalog": _LIVE_HTTP}
    assert second == {"registered": [], "catalog": _LIVE_HTTP}
    adds = [call for call in calls() if call[0] == "add"]
    assert adds == [["add", "--type", "http", "sources", _SOURCES_URL]]


def test_register_helper_fails_closed_when_add_does_not_take(fake_agy) -> None:
    seed, _calls = fake_agy
    seed(_DEAD_STDIO, add_is_noop=True)

    with pytest.raises(tool_config_mod.AgyMcpCatalogError, match="still shows"):
        tool_config_mod.ensure_agy_mcp_catalog(["sources"])


def test_missing_agy_binary_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tool_config_mod, "_agy_binary", lambda: str(tmp_path / "no-agy"))

    with pytest.raises(tool_config_mod.AgyMcpCatalogError, match="could not run"):
        tool_config_mod.agy_mcp_catalog()
