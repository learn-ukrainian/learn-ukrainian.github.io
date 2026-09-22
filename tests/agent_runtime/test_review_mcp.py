"""Tests for per-attempt stdio sources MCP launcher and ledger provisioner (#8517)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.delegate as delegate_cli
from scripts.agent_runtime.adapters.claude import ClaudeAdapter
from scripts.agent_runtime.adapters.cursor import CursorAdapter
from scripts.agent_runtime.adapters.grok_build import GrokBuildAdapter
from scripts.agent_runtime.review_mcp import (
    ENV_ATTEMPT_ID,
    ENV_LEDGER_PATH,
    ENV_MANIFEST_SHA256,
    SUPPORTED_HARNESSES,
    prepare_review_attempt,
)
from scripts.common.repo_root import resolve_repo_root


@pytest.fixture
def manifest_file(tmp_path: Path) -> Path:
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text("review_id: rev-test-001\nattempt_id: att-test-001\n", encoding="utf-8")
    return manifest


@pytest.mark.parametrize("harness", sorted(SUPPORTED_HARNESSES))
def test_prepare_review_attempt_exact_config_json_and_ledger(harness: str, manifest_file: Path, tmp_path: Path) -> None:
    receipts_root = tmp_path / "receipts"
    review_id = "rev-test-001"
    attempt_id = f"att-{harness}-001"

    manifest_bytes = manifest_file.read_bytes()
    expected_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    empty_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    plan = prepare_review_attempt(
        review_id=review_id,
        attempt_id=attempt_id,
        manifest_path=manifest_file,
        harness=harness,
        receipts_root=receipts_root,
    )

    primary_root = resolve_repo_root(Path(__file__), 2)
    expected_python = primary_root / ".venv" / "bin" / "python"
    expected_server = primary_root / ".mcp" / "servers" / "sources" / "server.py"

    # 1. Config path exists and has 0o644 permissions
    assert plan.config_path.is_file()
    assert (plan.config_path.stat().st_mode & 0o777) == 0o644

    # 2. Ledger exists, is empty (0 bytes), and has 0o644 permissions
    assert plan.ledger_path.is_file()
    assert plan.ledger_path.stat().st_size == 0
    assert (plan.ledger_path.stat().st_mode & 0o777) == 0o644

    # 3. Sidecars exist, hold <sha256>\n, and have 0o644 permissions
    assert plan.sidecar_path.is_file()
    assert plan.sidecar_path.read_text(encoding="ascii") == f"{empty_sha256}\n"
    assert (plan.sidecar_path.stat().st_mode & 0o777) == 0o644

    alt_sidecar = plan.ledger_path.parent / f"{attempt_id}.sha256"
    assert alt_sidecar.is_file()
    assert alt_sidecar.read_text(encoding="ascii") == f"{empty_sha256}\n"

    # 4. Exact config JSON defines ONLY sources over stdio
    config_data = json.loads(plan.config_path.read_text(encoding="utf-8"))
    assert set(config_data.keys()) == {"mcpServers"}
    servers = config_data["mcpServers"]
    assert set(servers.keys()) == {"sources"}

    sources_conf = servers["sources"]
    assert sources_conf["command"] == str(expected_python)
    assert sources_conf["args"] == [str(expected_server)]
    assert sources_conf["env"] == {
        ENV_ATTEMPT_ID: attempt_id,
        ENV_MANIFEST_SHA256: expected_manifest_sha,
        ENV_LEDGER_PATH: str(plan.ledger_path),
    }

    # 5. Plan properties and adapter options
    assert plan.manifest_sha256 == expected_manifest_sha
    assert plan.adapter_options == {
        "mcp_config_path": str(plan.config_path),
        "strict_mcp_config": True,
        "mcp_server_names": ["sources"],
    }
    assert plan.mcp_config_path == plan.config_path
    assert plan.strict_mcp_config is True


def test_prepare_review_attempt_refuses_agy(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"review attempt refused for agy:.*#8517"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-001",
            manifest_path=manifest_file,
            harness="agy",
            receipts_root=tmp_path,
        )


def test_prepare_review_attempt_refuses_codex(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"review attempt refused for codex:.*#8517"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-001",
            manifest_path=manifest_file,
            harness="codex",
            receipts_root=tmp_path,
        )


def test_delegate_dispatch_refusal_for_agy(manifest_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "agy",
            "--task-id",
            "review-task-agy",
            "--prompt",
            "perform review",
            "--review-attempt",
            str(manifest_file),
            "--review-id",
            "rev-001",
            "--attempt-id",
            "att-001",
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "review attempt refused for agy" in captured.err
    assert "#8517" in captured.err


def test_delegate_dispatch_refusal_for_codex(manifest_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "codex",
            "--task-id",
            "review-task-codex",
            "--prompt",
            "perform review",
            "--review-attempt",
            str(manifest_file),
            "--review-id",
            "rev-001",
            "--attempt-id",
            "att-001",
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "review attempt refused for codex" in captured.err
    assert "#8517" in captured.err


def test_delegate_dispatch_incomplete_review_attempt_flags(
    manifest_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "claude",
            "--task-id",
            "review-task-partial",
            "--prompt",
            "perform review",
            "--review-attempt",
            str(manifest_file),
            # Missing --review-id and --attempt-id
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "--review-attempt, --review-id, and --attempt-id must be used together" in captured.err


def test_claude_adapter_command_line_contains_strict_flags(tmp_path: Path) -> None:
    config_file = tmp_path / "custom-mcp.json"
    config_file.write_text('{"mcpServers":{}}\n', encoding="utf-8")

    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="review content",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="review-claude-task",
        session_id=None,
        tool_config={
            "mcp_config_path": str(config_file),
            "strict_mcp_config": True,
            "allowed_tools": "Read,Grep",
        },
    )

    assert "--strict-mcp-config" in plan.cmd
    assert "--mcp-config" in plan.cmd
    idx = plan.cmd.index("--mcp-config")
    assert plan.cmd[idx + 1] == str(config_file)
    tools_idx = plan.cmd.index("--allowedTools")
    assert plan.cmd[tools_idx + 1] == "Read,Grep"


def test_grok_adapter_command_line_contains_strict_flags(tmp_path: Path) -> None:
    config_file = tmp_path / "custom-mcp.json"
    config_file.write_text('{"mcpServers":{}}\n', encoding="utf-8")

    with patch("shutil.which", return_value="/usr/local/bin/grok"):
        adapter = GrokBuildAdapter()
        plan = adapter.build_invocation(
            prompt="review content",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id="review-grok-task",
            session_id=None,
            tool_config={
                "mcp_config_path": str(config_file),
                "strict_mcp_config": True,
            },
        )

    assert "--strict-mcp-config" in plan.cmd
    assert "--mcp-config" in plan.cmd
    idx = plan.cmd.index("--mcp-config")
    assert plan.cmd[idx + 1] == str(config_file)


def test_cursor_adapter_mirrors_config_and_drops_daemon_fallback(tmp_path: Path) -> None:
    # 1. Setup worktree with pre-existing daemon entry
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir(parents=True, exist_ok=True)
    cursor_mcp = cursor_dir / "mcp.json"
    cursor_mcp.write_text(
        json.dumps({"mcpServers": {"sources": {"url": "http://127.0.0.1:8766/mcp"}}}) + "\n",
        encoding="utf-8",
    )

    # 2. Written per-attempt config defining stdio sources
    attempt_conf = tmp_path / "attempt.mcp.json"
    attempt_conf.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "sources": {
                        "command": "/usr/bin/python3",
                        "args": ["server.py"],
                        "env": {"LU_REVIEW_ATTEMPT_ID": "att-1"},
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with patch("shutil.which", return_value="/usr/local/bin/cursor-agent"):
        adapter = CursorAdapter()
        adapter.build_invocation(
            prompt="review content",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id="review-cursor-task",
            session_id=None,
            tool_config={
                "cursor_workspace": str(tmp_path),
                "mcp_config_path": str(attempt_conf),
                "strict_mcp_config": True,
            },
        )

    # 3. Worktree's .cursor/mcp.json now has the stdio server replacing the daemon URL
    updated = json.loads(cursor_mcp.read_text(encoding="utf-8"))
    assert "sources" in updated["mcpServers"]
    sources = updated["mcpServers"]["sources"]
    assert "url" not in sources
    assert sources["command"] == "/usr/bin/python3"
    assert sources["args"] == ["server.py"]
    assert sources["env"] == {"LU_REVIEW_ATTEMPT_ID": "att-1"}

    # 4. Strict mode fails closed when sources is missing from the per-attempt config (no daemon fallback)
    empty_conf = tmp_path / "empty.mcp.json"
    empty_conf.write_text(json.dumps({"mcpServers": {}}) + "\n", encoding="utf-8")
    with patch("shutil.which", return_value="/usr/local/bin/cursor-agent"):
        with pytest.raises(RuntimeError, match="could not resolve MCP server config for: sources"):
            adapter.build_invocation(
                prompt="review content",
                mode="read-only",
                cwd=tmp_path,
                model=None,
                task_id="review-cursor-task-2",
                session_id=None,
                tool_config={
                    "cursor_workspace": str(tmp_path),
                    "mcp_config_path": str(empty_conf),
                    "strict_mcp_config": True,
                    "mcp_server_names": ["sources"],
                },
            )


def test_sources_server_stdio_integration(manifest_file: Path, tmp_path: Path) -> None:
    primary_root = resolve_repo_root(Path(__file__), 2)
    sources_db = primary_root / "data" / "sources.db"
    if not sources_db.is_file():
        pytest.skip(f"data/sources.db is absent at {sources_db}")

    plan = prepare_review_attempt(
        review_id="rev-integration-001",
        attempt_id="att-integration-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )

    config_data = json.loads(plan.config_path.read_text(encoding="utf-8"))
    sources_conf = config_data["mcpServers"]["sources"]

    cmd = [sources_conf["command"], *sources_conf["args"]]
    env = {**os.environ, **sources_conf["env"]}

    init_request = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
        ).encode("utf-8")
        + b"\n"
    )

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(primary_root),
    )
    try:
        stdout_bytes, stderr_bytes = proc.communicate(input=init_request, timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate(timeout=5)
        raise

    assert proc.returncode == 0, f"server failed with stderr: {stderr_bytes.decode('utf-8')}"
    lines = [line.strip() for line in stdout_bytes.decode("utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    resp = json.loads(lines[0])
    assert resp.get("id") == 1
    assert resp.get("result", {}).get("serverInfo", {}).get("name") == "sources"
