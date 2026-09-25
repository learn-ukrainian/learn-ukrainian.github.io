"""Tests for per-attempt stdio sources MCP launcher and ledger provisioner (#8517)."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tomllib
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.agent_runtime.review_mcp as review_mcp_module
import scripts.delegate as delegate_cli
from scripts.agent_runtime.adapters.claude import ClaudeAdapter
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.adapters.cursor import CursorAdapter
from scripts.agent_runtime.review_mcp import (
    ENV_ATTEMPT_ID,
    ENV_KEYS,
    ENV_LEDGER_PATH,
    ENV_MANIFEST_SHA256,
    SUPPORTED_HARNESSES,
    UNSUPPORTED_HARNESS_REASONS,
    AgyReviewMcpGateError,
    CodexReviewMcpGateError,
    agy_oauth_link_problem,
    agy_review_app_data_dir,
    agy_review_home_path,
    agy_review_mcp_config_path,
    codex_review_home_path,
    prepare_review_attempt,
    review_diagnostics_path,
    verify_agy_review_effective_mcp,
    verify_agy_review_launch,
    verify_codex_review_effective_mcp,
)
from scripts.common.repo_root import resolve_repo_root
from scripts.review.receipts.ledger import REVIEW_TOOLS


@pytest.fixture(autouse=True)
def fake_codex_user_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Hermetic stand-in for the user's Codex home (auth source for the scoped review home)."""
    home = tmp_path / "user-codex"
    home.mkdir()
    (home / "auth.json").write_text('{"fixture": true}\n', encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(home))
    return home


@pytest.fixture(autouse=True)
def fake_agy_user_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Hermetic stand-in for the user's AGY app data (OAuth token source for the scoped home)."""
    app_data = tmp_path / "user-agy" / ".gemini" / "antigravity-cli"
    app_data.mkdir(parents=True)
    (app_data / "antigravity-oauth-token").write_text('{"fixture": true}\n', encoding="utf-8")
    monkeypatch.setenv("AGY_APP_DATA_DIR", str(app_data))
    return app_data


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

    # 1. Config path exists and has 0o600 permissions
    assert plan.config_path.is_file()
    assert (plan.config_path.stat().st_mode & 0o777) == 0o600

    # 2. Ledger exists, is empty (0 bytes), and has 0o600 permissions
    assert plan.ledger_path.is_file()
    assert plan.ledger_path.stat().st_size == 0
    assert (plan.ledger_path.stat().st_mode & 0o777) == 0o600

    # 3. Sidecar exists, holds <sha256>\n, and has 0o600 permissions (second sidecar removed #8517)
    assert plan.sidecar_path.is_file()
    assert plan.sidecar_path.read_text(encoding="ascii") == f"{empty_sha256}\n"
    assert (plan.sidecar_path.stat().st_mode & 0o777) == 0o600

    alt_sidecar = plan.ledger_path.parent / f"{attempt_id}.sha256"
    assert not alt_sidecar.exists()

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
    expected_options = {
        "mcp_config_path": str(plan.config_path),
        "strict_mcp_config": True,
        "mcp_server_names": ["sources"],
    }
    if harness == "claude":
        expected_options["allowed_tools"] = ",".join(f"mcp__sources__{name}" for name in sorted(REVIEW_TOOLS))
    if harness == "codex":
        expected_options["codex_home_override"] = str(plan.config_path.parent / f"{attempt_id}.codex-home")
    if harness == "agy":
        expected_options["agy_home_override"] = str(plan.config_path.parent / f"{attempt_id}.agy-home")
    assert plan.adapter_options == expected_options
    assert plan.mcp_config_path == plan.config_path
    assert plan.strict_mcp_config is True


def test_prepare_review_attempt_files_mode_0o600(manifest_file: Path, tmp_path: Path) -> None:
    plan = prepare_review_attempt(
        review_id="rev-mode-001",
        attempt_id="att-mode-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )
    assert plan.ledger_path.is_file()
    assert (plan.ledger_path.stat().st_mode & 0o777) == 0o600
    assert plan.sidecar_path.is_file()
    assert (plan.sidecar_path.stat().st_mode & 0o777) == 0o600
    assert plan.config_path.is_file()
    assert (plan.config_path.stat().st_mode & 0o777) == 0o600


def test_prepare_review_attempt_refuses_grok(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"review attempt refused for grok: not yet proven \(#8517\)"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-001",
            manifest_path=manifest_file,
            harness="grok",
            receipts_root=tmp_path,
        )


def test_prepare_review_attempt_refuses_kimicc(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"review attempt refused for kimicc: not yet supported \(#8517\)"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-001",
            manifest_path=manifest_file,
            harness="kimicc",
            receipts_root=tmp_path,
        )


def test_prepare_review_attempt_refuses_reused_attempt_id(manifest_file: Path, tmp_path: Path) -> None:
    receipts_root = tmp_path / "receipts"
    prepare_review_attempt(
        review_id="rev-001",
        attempt_id="att-unique-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=receipts_root,
    )
    with pytest.raises(FileExistsError, match=r"review attempt 'att-unique-001' already exists for review 'rev-001'"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-unique-001",
            manifest_path=manifest_file,
            harness="claude",
            receipts_root=receipts_root,
        )


def test_delegate_dispatch_refusal_for_grok(manifest_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "grok",
            "--task-id",
            "review-task-grok",
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
    assert "review attempt refused for grok: not yet proven (#8517)" in captured.err


def test_delegate_dispatch_refusal_for_kimicc(manifest_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "kimi",
            "--harness",
            "kimicc",
            "--task-id",
            "review-task-kimicc",
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
    assert "review attempt refused for kimi: not yet supported (#8517)" in captured.err


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


def test_claude_adapter_command_line_contains_review_grant(manifest_file: Path, tmp_path: Path) -> None:
    review_plan = prepare_review_attempt(
        review_id="rev-cli-001",
        attempt_id="att-cli-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="review content",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="review-claude-task",
        session_id=None,
        tool_config=review_plan.adapter_options,
    )

    idx = plan.cmd.index("--strict-mcp-config")
    assert plan.cmd[idx : idx + 5] == [
        "--strict-mcp-config",
        "--mcp-config",
        str(review_plan.config_path),
        "--allowedTools",
        ",".join(f"mcp__sources__{name}" for name in sorted(REVIEW_TOOLS)),
    ]


def test_claude_adapter_ordinary_dispatch_has_no_review_flags(tmp_path: Path) -> None:
    plan = ClaudeAdapter().build_invocation(
        prompt="ordinary task",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="ordinary-claude-task",
        session_id=None,
        tool_config=None,
    )

    assert "--strict-mcp-config" not in plan.cmd
    assert "--mcp-config" not in plan.cmd
    assert "--allowedTools" not in plan.cmd


def test_cursor_adapter_refuses_primary_checkout_workspace(tmp_path: Path) -> None:
    adapter = CursorAdapter()
    config_file = tmp_path / "custom-mcp.json"
    config_file.write_text('{"mcpServers":{}}\n', encoding="utf-8")
    primary_root = resolve_repo_root(Path(__file__), 2)

    with patch("shutil.which", return_value="/usr/local/bin/cursor-agent"):
        with pytest.raises(RuntimeError, match=r"Cursor review attempt requires a dispatch worktree"):
            adapter.build_invocation(
                prompt="review content",
                mode="read-only",
                cwd=primary_root,
                model=None,
                task_id="review-cursor-task-primary",
                session_id=None,
                tool_config={
                    "cursor_workspace": str(primary_root),
                    "mcp_config_path": str(config_file),
                    "strict_mcp_config": True,
                },
            )


def test_delegate_dispatch_cursor_refuses_primary_checkout(
    manifest_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "cursor",
            "--task-id",
            "review-task-cursor-primary",
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
    assert "review attempt for cursor requires a dispatch worktree; refusing primary checkout (#8517)" in captured.err


def test_delegate_dispatch_refuses_budget_guard_substitution(
    manifest_file: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("LU_DISPATCH_CHECK_BUDGET", "1")
    fake_budget = {
        "diagnostics": {"records_loaded": 10, "stale": False},
        "recommendation": {"primary_agent_for_code": "codex"},
        "agents": {
            "claude": {
                "interactive": {"status": "near_cap", "burn_pct_7d": 95.0},
                "status": "near_cap",
                "burn_pct_7d": 95.0,
                "will_last_to_reset": False,
            },
            "codex": {
                "status": "cool",
                "burn_pct_7d": 20.0,
                "will_last_to_reset": True,
            },
        },
    }
    monkeypatch.setattr("scripts.delegate._fetch_routing_budget", lambda: fake_budget)
    monkeypatch.setattr("scripts.delegate._load_dispatch_fallbacks", lambda: {"claude": "codex"})

    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "claude",
            "--task-id",
            "review-task-budget-sub",
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
    assert (
        "review attempt refused: agent substitution from claude to codex (budget guard) is not allowed (#8517)"
        in captured.err
    )


def test_delegate_dispatch_refuses_retired_alias_substitution(
    manifest_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = delegate_cli.main(
        [
            "dispatch",
            "--agent",
            "gemini",
            "--task-id",
            "review-task-retired-alias",
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
    assert (
        "review attempt refused: agent substitution from gemini to agy (retired CLI) is not allowed (#8517)"
        in captured.err
    )


def test_delegate_dispatch_dry_run_skips_prepare_review_attempt(
    manifest_file: Path,
) -> None:
    task_id = f"review-task-dry-run-{uuid.uuid4().hex[:8]}"
    import agent_runtime.review_mcp

    with (
        patch("scripts.agent_runtime.review_mcp.prepare_review_attempt") as mock_prep_scripts,
        patch.object(agent_runtime.review_mcp, "prepare_review_attempt") as mock_prep_agent,
    ):
        rc = delegate_cli.main(
            [
                "dispatch",
                "--agent",
                "claude",
                "--task-id",
                task_id,
                "--prompt",
                "perform review",
                "--review-attempt",
                str(manifest_file),
                "--review-id",
                "rev-dry-001",
                "--attempt-id",
                "att-dry-001",
                "--dry-run",
            ]
        )
        assert rc == 0
        mock_prep_scripts.assert_not_called()
        mock_prep_agent.assert_not_called()


def test_delegate_dispatch_refuses_reused_attempt_id(
    manifest_file: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    receipts_root = tmp_path / "batch_state" / "review-receipts"
    attempt_dir = receipts_root / "rev-dup-001"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    (attempt_dir / "att-dup-001.jsonl").write_bytes(b"prior-receipts\n")

    task_id = f"review-task-dup-{uuid.uuid4().hex[:8]}"
    import agent_runtime.review_mcp

    with (
        patch("scripts.agent_runtime.review_mcp.resolve_repo_root", return_value=tmp_path),
        patch.object(agent_runtime.review_mcp, "resolve_repo_root", return_value=tmp_path),
    ):
        rc = delegate_cli.main(
            [
                "dispatch",
                "--agent",
                "claude",
                "--task-id",
                task_id,
                "--prompt",
                "perform review",
                "--review-attempt",
                str(manifest_file),
                "--review-id",
                "rev-dup-001",
                "--attempt-id",
                "att-dup-001",
            ]
        )
    assert rc == 2
    captured = capsys.readouterr()
    assert "review attempt 'att-dup-001' already exists for review 'rev-dup-001'" in captured.err


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
        cursor_plan = adapter.build_invocation(
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
                "mcp_server_names": ["sources"],
            },
        )
    assert "--approve-mcps" in cursor_plan.cmd

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


# ---------------------------------------------------------------------------
# Codex: scoped CODEX_HOME + effective-config gate (#8517)
# ---------------------------------------------------------------------------


def _prepare_codex(manifest_file: Path, tmp_path: Path, attempt_id: str = "att-codex-001"):
    return prepare_review_attempt(
        review_id="rev-codex-001",
        attempt_id=attempt_id,
        manifest_path=manifest_file,
        harness="codex",
        receipts_root=tmp_path / "receipts",
    )


def test_codex_is_a_supported_review_harness() -> None:
    assert "codex" in SUPPORTED_HARNESSES


def test_codex_home_is_sibling_of_mcp_config(manifest_file: Path, tmp_path: Path) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    assert plan.codex_home == plan.config_path.parent / "att-codex-001.codex-home"
    assert codex_review_home_path(plan.config_path) == plan.codex_home
    assert plan.codex_home.is_dir()
    assert stat.S_IMODE(plan.codex_home.stat().st_mode) == 0o700


def test_codex_scoped_config_names_only_stdio_sources(
    manifest_file: Path, tmp_path: Path, fake_codex_user_home: Path
) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    assert plan.codex_home is not None
    config_toml = plan.codex_home / "config.toml"
    assert stat.S_IMODE(config_toml.stat().st_mode) == 0o600
    parsed = tomllib.loads(config_toml.read_text(encoding="utf-8"))
    assert set(parsed) == {"mcp_servers"}
    assert set(parsed["mcp_servers"]) == {"sources"}
    sources = parsed["mcp_servers"]["sources"]
    assert "url" not in sources
    mcp_json = json.loads(plan.config_path.read_text(encoding="utf-8"))["mcpServers"]["sources"]
    assert sources["command"] == mcp_json["command"]
    assert sources["args"] == mcp_json["args"]
    assert sources["env"] == mcp_json["env"]
    assert set(sources["env"]) == {ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH}
    assert sources["default_tools_approval_mode"] == "approve"
    assert sources["required"] is True
    auth = plan.codex_home / "auth.json"
    assert auth.is_symlink()
    assert Path(os.readlink(auth)) == fake_codex_user_home / "auth.json"


def test_codex_home_without_user_auth_skips_symlink(
    manifest_file: Path, tmp_path: Path, fake_codex_user_home: Path
) -> None:
    (fake_codex_user_home / "auth.json").unlink()
    plan = _prepare_codex(manifest_file, tmp_path)
    assert plan.codex_home is not None
    assert not (plan.codex_home / "auth.json").exists()
    assert (plan.codex_home / "config.toml").is_file()


def test_non_codex_harness_creates_no_codex_home(manifest_file: Path, tmp_path: Path) -> None:
    plan = prepare_review_attempt(
        review_id="rev-claude-001",
        attempt_id="att-claude-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )
    assert plan.codex_home is None
    assert "codex_home_override" not in plan.adapter_options
    assert list(plan.config_path.parent.glob("*.codex-home")) == []


def test_failed_codex_preparation_leaves_nothing_behind(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.agent_runtime.review_mcp as review_mcp

    def boom(_home: Path) -> None:
        raise OSError("auth link failed")

    monkeypatch.setattr(review_mcp, "_link_codex_auth", boom)
    with pytest.raises(OSError, match="auth link failed"):
        _prepare_codex(manifest_file, tmp_path)
    assert list((tmp_path / "receipts" / "rev-codex-001").iterdir()) == []


def test_codex_preexisting_home_is_refused_and_untouched(manifest_file: Path, tmp_path: Path) -> None:
    review_dir = tmp_path / "receipts" / "rev-codex-001"
    planted = review_dir / "att-codex-001.codex-home"
    planted.mkdir(parents=True)
    (planted / "config.toml").write_text("planted\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        _prepare_codex(manifest_file, tmp_path)
    assert (planted / "config.toml").read_text(encoding="utf-8") == "planted\n"
    assert sorted(path.name for path in review_dir.iterdir()) == ["att-codex-001.codex-home"]


def test_codex_home_race_after_precheck_rolls_back_other_files(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_mkdir = os.mkdir

    def racing_mkdir(path, *args, **kwargs):
        if str(path).endswith(".codex-home"):
            raise FileExistsError(path)
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", racing_mkdir)
    with pytest.raises(FileExistsError):
        _prepare_codex(manifest_file, tmp_path)
    assert list((tmp_path / "receipts" / "rev-codex-001").iterdir()) == []


def _install_fake_codex(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, servers: list[dict]) -> Path:
    """Fake ``codex`` that logs cwd/CODEX_HOME/argv and prints canned ``mcp list --json``."""
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir(exist_ok=True)
    canned = tmp_path / "servers.json"
    canned.write_text(json.dumps(servers), encoding="utf-8")
    log = tmp_path / "fake-codex.log"
    script = bin_dir / "codex"
    script.write_text(
        f'#!/bin/sh\nprintf \'%s|%s|%s\\n\' "$PWD" "$CODEX_HOME" "$*" >> {log}\ncat {canned}\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return log


def _sources_entry(config_path: Path) -> dict:
    expected = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"]["sources"]
    return {
        "name": "sources",
        "enabled": True,
        "transport": {
            "type": "stdio",
            "command": expected["command"],
            "args": expected["args"],
            "env": expected["env"],
        },
    }


def test_effective_mcp_gate_accepts_exactly_sources(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    log = _install_fake_codex(tmp_path, monkeypatch, [_sources_entry(plan.config_path)])
    cwd = tmp_path / "wt"
    cwd.mkdir()
    verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=cwd, config_flags=["--disable", "apps"])
    logged_cwd, logged_home, logged_args = log.read_text(encoding="utf-8").strip().split("|")
    assert Path(logged_cwd) == cwd.resolve()
    assert logged_home == str(plan.codex_home)
    assert logged_args == "mcp list --json --disable apps"


@pytest.mark.parametrize(
    ("mutate", "needle"),
    [
        (
            lambda servers, _entry: servers.append({"name": "leak", "enabled": True, "transport": {"type": "stdio"}}),
            "leak",
        ),
        (lambda servers, _entry: servers.clear(), "exactly"),
        (lambda _s, entry: entry["transport"].update(type="streamable_http"), "not stdio"),
        (lambda _s, entry: entry["transport"].update(command="/bin/other"), "command/args differ"),
        (lambda _s, entry: entry["transport"].update(args=[]), "command/args differ"),
        (lambda _s, entry: entry["transport"].update(env={}), "env differs"),
        (lambda _s, entry: entry.update(enabled=False), "not enabled"),
    ],
)
def test_effective_mcp_gate_refuses_deviation(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutate, needle: str
) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    entry = _sources_entry(plan.config_path)
    servers = [entry]
    mutate(servers, entry)
    _install_fake_codex(tmp_path, monkeypatch, servers)
    with pytest.raises(CodexReviewMcpGateError, match=r"#8517") as excinfo:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    assert needle in str(excinfo.value)


def test_effective_mcp_gate_fails_closed_when_probe_breaks(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    script = bin_dir / "codex"
    script.write_text("#!/bin/sh\necho boom >&2\nexit 3\n", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    with pytest.raises(CodexReviewMcpGateError, match=r"exited 3.*#8517"):
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    script.write_text("#!/bin/sh\necho not-json\n", encoding="utf-8")
    with pytest.raises(CodexReviewMcpGateError, match=r"did not return JSON.*#8517"):
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)


def test_effective_mcp_gate_refuses_missing_scoped_home(manifest_file: Path, tmp_path: Path) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    assert plan.codex_home is not None
    shutil.rmtree(plan.codex_home)
    with pytest.raises(CodexReviewMcpGateError, match=r"no config.toml.*#8517"):
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)


@pytest.mark.skipif(shutil.which("codex") is None, reason="codex CLI not installed")
def test_real_codex_cli_accepts_scoped_home_and_refuses_trusted_project_server(
    manifest_file: Path, tmp_path: Path
) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    assert plan.codex_home is not None
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    # Untrusted project config is not loaded; the scoped home alone is the effective set.
    (project / ".codex" / "config.toml").write_text('[mcp_servers.leak]\ncommand = "/bin/true"\n', encoding="utf-8")
    verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=project)
    # A trusted project (trust recorded in the user/scoped config) DOES add servers: refuse.
    with (plan.codex_home / "config.toml").open("a", encoding="utf-8") as handle:
        handle.write(f'\n[projects.{json.dumps(str(project.resolve()))}]\ntrust_level = "trusted"\n')
    with pytest.raises(CodexReviewMcpGateError, match=r"leak.*#8517"):
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=project)


def test_codex_adapter_final_argv_and_env_use_scoped_home(manifest_file: Path, tmp_path: Path) -> None:
    plan = _prepare_codex(manifest_file, tmp_path)
    invocation = CodexAdapter().build_invocation(
        prompt="review with mcp__sources__verify_word",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="review-codex-task",
        session_id=None,
        tool_config={**plan.adapter_options, "review_id": "rev-codex-001", "attempt_id": "att-codex-001"},
    )
    assert invocation.env_overrides["CODEX_HOME"] == str(plan.codex_home)
    joined = " ".join(invocation.cmd)
    assert "mcp_servers.sources.url" not in joined
    assert "8766" not in joined
    assert 'mcp_servers.sources.default_tools_approval_mode="approve"' in invocation.cmd


def test_codex_ordinary_dispatch_has_no_scoped_home_or_url_override(tmp_path: Path) -> None:
    invocation = CodexAdapter().build_invocation(
        prompt="ordinary task",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="ordinary-codex-task",
        session_id=None,
        tool_config=None,
    )
    assert "CODEX_HOME" not in invocation.env_overrides
    assert not any("mcp_servers.sources.url" in item for item in invocation.cmd)


# --- AGY scoped-home receipts seat (#8617) --------------------------------------------


def _prepare_agy(manifest_file: Path, tmp_path: Path, attempt_id: str = "att-agy-001"):
    return prepare_review_attempt(
        review_id="rev-agy-001",
        attempt_id=attempt_id,
        manifest_path=manifest_file,
        harness="agy",
        receipts_root=tmp_path / "receipts",
    )


def test_agy_is_a_supported_review_harness() -> None:
    assert "agy" in SUPPORTED_HARNESSES
    assert "agy" not in UNSUPPORTED_HARNESS_REASONS


def test_agy_home_layout_modes_and_single_source_config(
    manifest_file: Path, tmp_path: Path, fake_agy_user_home: Path
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    assert plan.agy_home is not None
    assert plan.agy_home == plan.config_path.with_name("att-agy-001.agy-home")
    assert plan.agy_home == agy_review_home_path(plan.config_path)
    assert plan.adapter_options["agy_home_override"] == str(plan.agy_home)
    # Directories are private; the config file is 0600.
    app_data = agy_review_app_data_dir(plan.agy_home)
    mcp_config = agy_review_mcp_config_path(plan.agy_home)
    assert app_data == plan.agy_home / ".gemini" / "antigravity-cli"
    assert mcp_config == plan.agy_home / ".gemini" / "config" / "mcp_config.json"
    for directory in (plan.agy_home, plan.agy_home / ".gemini", mcp_config.parent, app_data):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700, directory
    assert stat.S_IMODE(mcp_config.stat().st_mode) == 0o600
    # The only config file agy -p loads holds exactly the attempt's stdio sources server.
    assert json.loads(mcp_config.read_text(encoding="utf-8")) == json.loads(
        plan.config_path.read_text(encoding="utf-8")
    )
    assert not (app_data / "mcp_config.json").exists()
    # The OAuth token is a symlink to the user's token, never a copy.
    token = app_data / "antigravity-oauth-token"
    assert token.is_symlink()
    assert Path(os.readlink(token)) == fake_agy_user_home / "antigravity-oauth-token"
    assert sorted(entry.name for entry in app_data.iterdir()) == ["antigravity-oauth-token"]


def test_agy_home_token_source_defaults_to_real_home_without_override(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("AGY_APP_DATA_DIR")
    home = tmp_path / "fake-home"
    token = home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    token.parent.mkdir(parents=True)
    token.write_text("{}\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    plan = _prepare_agy(manifest_file, tmp_path)
    assert plan.agy_home is not None
    linked = agy_review_app_data_dir(plan.agy_home) / "antigravity-oauth-token"
    assert Path(os.readlink(linked)) == token


def test_non_agy_harness_creates_no_agy_home(manifest_file: Path, tmp_path: Path) -> None:
    plan = prepare_review_attempt(
        review_id="rev-claude-001",
        attempt_id="att-claude-001",
        manifest_path=manifest_file,
        harness="claude",
        receipts_root=tmp_path / "receipts",
    )
    assert plan.agy_home is None
    assert "agy_home_override" not in plan.adapter_options
    assert list(plan.config_path.parent.glob("*.agy-home")) == []


_AGY_LINK_LABEL = "att-agy-001.agy-home/.gemini/antigravity-cli/antigravity-oauth-token"


def test_agy_oauth_link_problem_is_none_when_intact(manifest_file: Path, tmp_path: Path) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    assert agy_oauth_link_problem(plan.config_path) is None


@pytest.mark.parametrize(
    ("breakage", "expected"),
    [
        ("missing", f"{_AGY_LINK_LABEL} is missing, not a symlink to the real AGY OAuth token"),
        ("file", f"{_AGY_LINK_LABEL} is a regular file, not a symlink to the real AGY OAuth token"),
        ("retarget", f"{_AGY_LINK_LABEL} points elsewhere, not to the real AGY OAuth token"),
    ],
)
def test_agy_oauth_link_problem_names_each_case_without_any_absolute_path(
    manifest_file: Path,
    tmp_path: Path,
    fake_agy_user_home: Path,
    breakage: str,
    expected: str,
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    link = agy_review_app_data_dir(plan.agy_home) / "antigravity-oauth-token"
    link.unlink()
    if breakage == "file":
        link.write_text("{}\n", encoding="utf-8")
    elif breakage == "retarget":
        other = tmp_path / "elsewhere-token"
        other.write_text("{}\n", encoding="utf-8")
        link.symlink_to(other)

    problem = agy_oauth_link_problem(plan.config_path)

    assert problem == expected
    # The message is quoted into task state, logs, issues and PRs: it must expose no
    # absolute path (the operator's home, the real token, the retargeted path, or the
    # attempt directory).
    for leaked in (str(Path.home()), str(fake_agy_user_home), str(tmp_path), str(plan.agy_home), "elsewhere-token"):
        assert leaked not in problem
    assert "/" not in problem.replace(_AGY_LINK_LABEL, "")


def test_agy_missing_user_token_is_refused_before_anything_is_created(
    manifest_file: Path, tmp_path: Path, fake_agy_user_home: Path
) -> None:
    (fake_agy_user_home / "antigravity-oauth-token").unlink()
    with pytest.raises(ValueError, match=r"OAuth token not found.*AGY_APP_DATA_DIR.*#8617") as refused:
        _prepare_agy(manifest_file, tmp_path)
    # The refusal names the variable, never its value (#8652).
    assert str(tmp_path) not in str(refused.value)
    assert list((tmp_path / "receipts" / "rev-agy-001").iterdir()) == []


def test_agy_preexisting_home_is_refused_and_untouched(manifest_file: Path, tmp_path: Path) -> None:
    review_dir = tmp_path / "receipts" / "rev-agy-001"
    planted = review_dir / "att-agy-001.agy-home"
    planted.mkdir(parents=True)
    (planted / "marker").write_text("planted\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="already exists"):
        _prepare_agy(manifest_file, tmp_path)
    assert (planted / "marker").read_text(encoding="utf-8") == "planted\n"
    assert sorted(path.name for path in review_dir.iterdir()) == ["att-agy-001.agy-home"]


def test_agy_preexisting_dangling_symlink_home_is_refused(manifest_file: Path, tmp_path: Path) -> None:
    review_dir = tmp_path / "receipts" / "rev-agy-001"
    review_dir.mkdir(parents=True)
    (review_dir / "att-agy-001.agy-home").symlink_to(tmp_path / "nowhere")
    with pytest.raises(FileExistsError, match="already exists"):
        _prepare_agy(manifest_file, tmp_path)
    assert sorted(path.name for path in review_dir.iterdir()) == ["att-agy-001.agy-home"]


def test_failed_agy_preparation_leaves_nothing_behind(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.agent_runtime.review_mcp as review_mcp

    def boom(*_args: object) -> None:
        raise OSError("populate failed")

    monkeypatch.setattr(review_mcp, "_populate_agy_review_home", boom)
    with pytest.raises(OSError, match="populate failed"):
        _prepare_agy(manifest_file, tmp_path)
    assert list((tmp_path / "receipts" / "rev-agy-001").iterdir()) == []


def test_agy_home_race_after_precheck_rolls_back_other_files_and_spares_the_planted_home(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_dir = tmp_path / "receipts" / "rev-agy-001"
    real_mkdir = os.mkdir

    def racing_mkdir(path, *args, **kwargs):
        if str(path).endswith(".agy-home"):
            real_mkdir(path, 0o700)  # someone else won the race
            (Path(path) / "marker").write_text("theirs\n", encoding="utf-8")
            raise FileExistsError(path)
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", racing_mkdir)
    with pytest.raises(FileExistsError):
        _prepare_agy(manifest_file, tmp_path)
    assert sorted(path.name for path in review_dir.iterdir()) == ["att-agy-001.agy-home"]
    assert (review_dir / "att-agy-001.agy-home" / "marker").read_text(encoding="utf-8") == "theirs\n"


def _agy_expected_target(config_path: Path) -> str:
    expected = json.loads(config_path.read_text(encoding="utf-8"))["mcpServers"]["sources"]
    return " ".join([expected["command"], *expected["args"]])


def _agy_table(
    rows: list[tuple[str, ...]], *, header: tuple[str, ...] = ("NAME", "TYPE", "STATUS", "COMMAND/URL")
) -> str:
    """Render rows like agy's tabwriter: each cell padded to its column's width plus two spaces."""
    everything = [header, *rows]
    widths = [max(len(row[i]) for row in everything if i < len(row)) + 2 for i in range(len(header))]
    lines = []
    for row in everything:
        cells = [cell.ljust(widths[i]) if i < len(row) - 1 else cell for i, cell in enumerate(row)]
        lines.append("".join(cells))
    return "\n".join(lines) + "\n"


def _agy_good_rows(config_path: Path) -> list[tuple[str, ...]]:
    return [("sources", "stdio", "enabled", _agy_expected_target(config_path))]


def _install_fake_agy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stdout: str, *, body: str = "") -> Path:
    """Fake ``agy`` on PATH: logs ``cwd|HOME|AGY_APP_DATA_DIR|argv`` and prints canned stdout.

    ``--version`` answers a supported build (#8502 floor) without logging.
    """
    bin_dir = tmp_path / "fake-agy-bin"
    bin_dir.mkdir(exist_ok=True)
    canned = tmp_path / "agy-table.txt"
    canned.write_text(stdout, encoding="utf-8")
    log = tmp_path / "fake-agy.log"
    script = bin_dir / "agy"
    script.write_text(
        '#!/bin/sh\n[ "$1" = --version ] && echo 1.2.10 && exit 0\n'
        f'printf \'%s|%s|%s|%s\\n\' "$PWD" "$HOME" "$AGY_APP_DATA_DIR" "$*" >> {log}\n{body}cat {canned}\n',
        encoding="utf-8",
    )
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return log


def _agy_env(plan) -> dict[str, str]:
    return {
        "HOME": str(plan.agy_home),
        "AGY_APP_DATA_DIR": str(agy_review_app_data_dir(plan.agy_home)),
        "PATH": os.environ["PATH"],
    }


def _verify_agy(plan, tmp_path: Path, **kwargs) -> None:
    agy_bin = shutil.which("agy")
    assert agy_bin is not None
    verify_agy_review_effective_mcp(
        config_path=plan.config_path, cwd=tmp_path, env=_agy_env(plan), agy_bin=agy_bin, **kwargs
    )


def _rewrite_agy_config(plan, mutate) -> None:
    path = agy_review_mcp_config_path(plan.agy_home)
    data = json.loads(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_agy_gate_accepts_exactly_sources_with_padded_table(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    log = _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    cwd = tmp_path / "wt"
    cwd.mkdir()
    agy_bin = shutil.which("agy")
    assert agy_bin is not None
    verify_agy_review_effective_mcp(config_path=plan.config_path, cwd=cwd, env=_agy_env(plan), agy_bin=agy_bin)
    logged_cwd, logged_home, logged_app_data, logged_args = log.read_text(encoding="utf-8").strip().split("|")
    assert Path(logged_cwd) == cwd.resolve()
    assert logged_home == str(plan.agy_home)
    assert logged_app_data == str(agy_review_app_data_dir(plan.agy_home))
    assert logged_args == "mcp list"


@pytest.mark.parametrize(
    ("table", "needle"),
    [
        # extra row
        (
            lambda good: _agy_table([*good, ("leak", "http", "enabled", "http://127.0.0.1:8766/mcp")]),
            "exactly ['sources']",
        ),
        # duplicate row
        (lambda good: _agy_table([*good, *good]), "repeats a server name"),
        # no rows at all
        (lambda _good: _agy_table([]), "exactly ['sources']"),
        # only a differently named row
        (lambda good: _agy_table([("other", *good[0][1:])]), "exactly ['sources']"),
        # missing header: the first data row would be swallowed as one
        (lambda good: "\n".join(f"{n}  {t}  {s}  {c}" for n, t, s, c in good) + "\n", "header"),
        # altered headers
        (lambda good: _agy_table(good, header=("NAME", "TYPE", "STATE", "COMMAND/URL")), "header"),
        (lambda good: _agy_table(good, header=("TYPE", "NAME", "STATUS", "COMMAND/URL")), "header"),
        (lambda good: _agy_table(good, header=("NAME", "TYPE", "STATUS")), "header"),
        # truncated row: cells missing
        (lambda _good: _agy_table([]) + "sources  stdio\n", "truncated"),
        (lambda _good: _agy_table([]) + "sources  stdio  enabled\n", "truncated"),
        # misaligned row (target starts at the wrong column)
        (lambda good: _agy_table([]) + f"sources stdio enabled {good[0][3]}\n", "truncated or misaligned"),
        (lambda _good: "", "no table"),
        (lambda _good: "\n\n", "no table"),
        # wrong transport / status / command / args
        (lambda good: _agy_table([(good[0][0], "http", good[0][2], good[0][3])]), "not stdio"),
        (lambda good: _agy_table([(good[0][0], good[0][1], "disabled", good[0][3])]), "not enabled"),
        (lambda good: _agy_table([(*good[0][:3], "/bin/other " + good[0][3].split(" ", 1)[1])]), "command/args differ"),
        (lambda good: _agy_table([(*good[0][:3], good[0][3].split(" ", 1)[0])]), "command/args differ"),
        (lambda good: _agy_table([(*good[0][:3], good[0][3] + " --extra")]), "command/args differ"),
    ],
)
def test_agy_gate_refuses_table_deviation(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, table, needle: str
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, table(_agy_good_rows(plan.config_path)))
    with pytest.raises(AgyReviewMcpGateError, match=r"#8617") as excinfo:
        _verify_agy(plan, tmp_path)
    assert needle in str(excinfo.value)


@pytest.mark.parametrize(
    ("mutate", "needle"),
    [
        (lambda data: data["mcpServers"]["sources"]["env"].update({ENV_ATTEMPT_ID: "someone-else"}), "differs"),
        (lambda data: data["mcpServers"]["sources"]["env"].update({ENV_MANIFEST_SHA256: "0" * 64}), "differs"),
        (lambda data: data["mcpServers"]["sources"]["env"].update({ENV_LEDGER_PATH: "/tmp/other.jsonl"}), "differs"),
        (lambda data: data["mcpServers"]["sources"]["env"].pop(ENV_LEDGER_PATH), "differs"),
        (lambda data: data["mcpServers"]["sources"].pop("env"), "differs"),
        (lambda data: data["mcpServers"]["sources"]["env"].update({"EXTRA": "1"}), "differs"),
        (lambda data: data["mcpServers"]["sources"].update(command="/bin/other"), "differs"),
        (lambda data: data["mcpServers"]["sources"].update(disabled=True), "differs"),
        (lambda data: data["mcpServers"].update(leak={"serverUrl": "http://127.0.0.1:8766/mcp"}), "exactly the one"),
        (lambda data: data["mcpServers"].clear(), "exactly the one"),
        (lambda data: data.update(extra={}), "keys other than"),
    ],
)
def test_agy_gate_refuses_scoped_config_deviation(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutate, needle: str
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    _rewrite_agy_config(plan, mutate)
    with pytest.raises(AgyReviewMcpGateError, match=r"#8617") as excinfo:
        _verify_agy(plan, tmp_path)
    assert needle in str(excinfo.value)


def test_agy_gate_refuses_missing_unreadable_or_duplicate_key_config(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    config = agy_review_mcp_config_path(plan.agy_home)
    original = config.read_text(encoding="utf-8")
    config.write_text("{not json", encoding="utf-8")
    with pytest.raises(AgyReviewMcpGateError, match=r"cannot read the scoped agy MCP config.*#8617"):
        _verify_agy(plan, tmp_path)
    # A duplicate key would let a second `sources` silently win under a lenient parser.
    config.write_text(original.replace('"sources": {', '"sources": {}, "sources": {', 1), encoding="utf-8")
    with pytest.raises(AgyReviewMcpGateError, match=r"cannot read the scoped agy MCP config.*#8617"):
        _verify_agy(plan, tmp_path)
    config.unlink()
    with pytest.raises(AgyReviewMcpGateError, match=r"cannot read the scoped agy MCP config.*#8617"):
        _verify_agy(plan, tmp_path)


def test_agy_gate_refuses_a_stray_antigravity_cli_mcp_config(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    (agy_review_app_data_dir(plan.agy_home) / "mcp_config.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(AgyReviewMcpGateError, match=r"unexpected.*mcp_config.json.*#8617"):
        _verify_agy(plan, tmp_path)


def test_agy_gate_refuses_a_launch_environment_without_the_scoped_home(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    log = _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    agy_bin = shutil.which("agy")
    assert agy_bin is not None
    good = _agy_env(plan)
    for bad in (
        {**good, "HOME": str(tmp_path / "real-home")},
        {**good, "AGY_APP_DATA_DIR": str(tmp_path / "real-home" / ".gemini" / "antigravity-cli")},
        {key: value for key, value in good.items() if key != "HOME"},
        {key: value for key, value in good.items() if key != "AGY_APP_DATA_DIR"},
    ):
        with pytest.raises(AgyReviewMcpGateError, match=r"scoped HOME/AGY_APP_DATA_DIR.*#8617") as refused:
            verify_agy_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path, env=bad, agy_bin=agy_bin)
        # The refusal names the variables, never their values (#8652).
        message = str(refused.value)
        for value in {bad.get("HOME"), bad.get("AGY_APP_DATA_DIR"), good["HOME"], good["AGY_APP_DATA_DIR"]} - {None}:
            assert value not in message
        assert str(tmp_path) not in message
    assert not log.exists(), "the CLI must not run under a launch environment that is not scoped"


def test_agy_gate_refuses_paths_the_flat_command_text_cannot_identify(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``agy mcp list`` flattens command and args with single spaces: a space in a part is ambiguous."""
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))

    def spaced(data: dict) -> None:
        data["mcpServers"]["sources"]["args"] = ["/opt/my dir/server.py"]

    for target in (plan.config_path, agy_review_mcp_config_path(plan.agy_home)):
        data = json.loads(target.read_text(encoding="utf-8"))
        spaced(data)
        target.write_text(json.dumps(data), encoding="utf-8")
    _install_fake_agy(
        tmp_path,
        monkeypatch,
        _agy_table([("sources", "stdio", "enabled", _agy_expected_target(plan.config_path))]),
    )
    with pytest.raises(AgyReviewMcpGateError, match=r"whitespace.*#8617"):
        _verify_agy(plan, tmp_path)


def test_agy_gate_fails_closed_when_probe_breaks(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    good = _agy_table(_agy_good_rows(plan.config_path))
    # non-zero exit (even with a perfectly valid table on stdout)
    _install_fake_agy(
        tmp_path, monkeypatch, good, body="echo boom >&2\ncat " + str(tmp_path / "agy-table.txt") + "\nexit 3\n"
    )
    with pytest.raises(AgyReviewMcpGateError, match=r"exited 3: <stderr: 5 chars, sha256 [0-9a-f]{12}; .*#8617"):
        _verify_agy(plan, tmp_path)
    assert "boom" in review_diagnostics_path(plan.config_path).read_text(encoding="utf-8")
    # timeout
    _install_fake_agy(tmp_path, monkeypatch, good, body="exec sleep 5\n")
    with pytest.raises(AgyReviewMcpGateError, match=r"TimeoutExpired.*#8617"):
        _verify_agy(plan, tmp_path, timeout=0.3)
    # missing CLI
    with pytest.raises(AgyReviewMcpGateError, match=r"could not compute.*#8617"):
        verify_agy_review_effective_mcp(
            config_path=plan.config_path,
            cwd=tmp_path,
            env=_agy_env(plan),
            agy_bin=str(tmp_path / "no-such-agy"),
        )


def test_agy_gate_refuses_an_unreadable_attempt_config(tmp_path: Path) -> None:
    with pytest.raises(AgyReviewMcpGateError, match=r"cannot read the attempt MCP config.*#8617"):
        verify_agy_review_effective_mcp(
            config_path=tmp_path / "missing.mcp.json", cwd=tmp_path, env={}, agy_bin="/bin/true"
        )


def test_agy_gate_refusals_never_embed_home_or_app_data_values(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No refusal carries the scoped HOME / AGY_APP_DATA_DIR values or the operator's home (#8652).

    Each case is one the gate used to answer with a path: its own message, an ``OSError``
    file name, the missing binary's path, or probe output echoed back.
    """
    operator_home = tmp_path / "operator-home-marker-8652"
    monkeypatch.setenv("HOME", str(operator_home))
    plan = prepare_review_attempt(
        review_id="rev-agy-001",
        attempt_id="att-agy-001",
        manifest_path=manifest_file,
        harness="agy",
        receipts_root=operator_home / "scoped-marker-8652" / "receipts",
    )
    env = _agy_env(plan)
    app_data = Path(env["AGY_APP_DATA_DIR"])
    scoped_config = agy_review_mcp_config_path(plan.agy_home)
    good = _agy_table(_agy_good_rows(plan.config_path))
    agy_bin = str(tmp_path / "fake-agy-bin" / "agy")
    messages: list[str] = []

    def refusal(*, binary: str = agy_bin, config_path: Path = plan.config_path) -> None:
        with pytest.raises(AgyReviewMcpGateError, match=r"#8617") as refused:
            verify_agy_review_effective_mcp(config_path=config_path, cwd=tmp_path, env=env, agy_bin=binary)
        messages.append(str(refused.value))

    _install_fake_agy(tmp_path, monkeypatch, good)
    (app_data / "mcp_config.json").write_text("{}\n", encoding="utf-8")
    refusal()
    (app_data / "mcp_config.json").unlink()
    original = scoped_config.read_text(encoding="utf-8")
    scoped_config.unlink()
    refusal()
    scoped_config.write_text(original, encoding="utf-8")
    refusal(binary=str(plan.agy_home / "no-such-agy"))
    refusal(config_path=app_data / "missing.mcp.json")
    _install_fake_agy(tmp_path, monkeypatch, good, body='echo "boom $HOME $AGY_APP_DATA_DIR" >&2\nexit 3\n')
    refusal()
    _install_fake_agy(tmp_path, monkeypatch, f"NAME TYPE {env['HOME']}\n")
    refusal()
    _install_fake_agy(tmp_path, monkeypatch, _agy_table([]) + f"sources  stdio  {env['AGY_APP_DATA_DIR']}\n")
    refusal()

    assert "unexpected mcp_config.json" in messages[0]
    assert "cannot read the scoped agy MCP config" in messages[1]
    assert "could not compute" in messages[2]
    assert "cannot read the attempt MCP config" in messages[3]
    # Probe output is never echoed: the refusal carries only its size and fingerprint.
    assert "exited 3: <stderr: " in messages[4]
    assert "boom" not in messages[4]
    for message in messages:
        for value in (env["HOME"], env["AGY_APP_DATA_DIR"], str(operator_home), "marker-8652", str(tmp_path)):
            assert value not in message, message


def test_codex_gate_refusals_never_embed_codex_home_or_home_values(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Codex gate masks the scoped CODEX_HOME and the operator's home the same way (#8652)."""
    operator_home = tmp_path / "operator-home-marker-8652"
    monkeypatch.setenv("HOME", str(operator_home))
    plan = prepare_review_attempt(
        review_id="rev-codex-001",
        attempt_id="att-codex-001",
        manifest_path=manifest_file,
        harness="codex",
        receipts_root=operator_home / "scoped-marker-8652" / "receipts",
    )
    assert plan.codex_home is not None
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    script = bin_dir / "codex"
    script.write_text('#!/bin/sh\necho "boom $CODEX_HOME $HOME" >&2\nexit 3\n', encoding="utf-8")
    script.chmod(0o755)
    messages: list[str] = []

    def refusal(*, binary: str = str(script), config_path: Path = plan.config_path) -> None:
        with pytest.raises(CodexReviewMcpGateError, match=r"#8517") as refused:
            verify_codex_review_effective_mcp(config_path=config_path, cwd=tmp_path, codex_bin=binary)
        messages.append(str(refused.value))

    refusal()
    refusal(binary=str(plan.codex_home / "no-such-codex"))
    refusal(config_path=plan.codex_home / "missing.mcp.json")
    (plan.codex_home / "config.toml").unlink()
    refusal()

    assert "exited 3: <stderr: " in messages[0]
    assert "boom" not in messages[0]
    assert "could not compute" in messages[1]
    assert "cannot read the attempt MCP config" in messages[2]
    assert "scoped CODEX_HOME has no config.toml" in messages[3]
    for message in messages:
        for value in (str(plan.codex_home), str(operator_home), "marker-8652", str(tmp_path)):
            assert value not in message, message


def test_path_input_errors_name_the_file_never_its_directory(tmp_path: Path) -> None:
    """Bad config names and a missing manifest are reported by file name only (#8652)."""
    for helper in (codex_review_home_path, agy_review_home_path):
        with pytest.raises(ValueError, match=r"must end in \.mcp\.json: 'att\.json'") as refused:
            helper(tmp_path / "att.json")
        assert str(tmp_path) not in str(refused.value)
    with pytest.raises(FileNotFoundError, match=r"not found: 'missing\.yaml'") as refused:
        prepare_review_attempt("rev-001", "att-001", tmp_path / "missing.yaml", "claude", receipts_root=tmp_path)
    assert str(tmp_path) not in str(refused.value)


def _agy_tool_config(plan, **extra) -> dict:
    return {**plan.adapter_options, "review_id": "rev-agy-001", "attempt_id": "att-agy-001", **extra}


def test_agy_launch_gate_runs_under_the_final_spawned_environment(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _prepare_agy(manifest_file, tmp_path)
    log = _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    cwd = tmp_path / "wt"
    cwd.mkdir()
    verify_agy_review_launch(
        config_path=plan.config_path,
        cwd=cwd,
        mode="read-only",
        model=None,
        effort=None,
        task_id="review-agy-task",
        tool_config=_agy_tool_config(plan),
    )
    logged_cwd, logged_home, logged_app_data, logged_args = log.read_text(encoding="utf-8").strip().split("|")
    assert Path(logged_cwd) == cwd.resolve()
    assert logged_home == str(plan.agy_home)
    assert logged_app_data == str(agy_review_app_data_dir(plan.agy_home))
    assert logged_args == "mcp list"


def test_agy_launch_gate_refuses_when_the_sanitizer_would_drop_the_scoped_home(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An attempt id containing ``sk-`` looks like a secret to the value redactor: HOME would vanish."""
    plan = prepare_review_attempt(
        review_id="rev-agy-001",
        attempt_id="task-sk-att",
        manifest_path=manifest_file,
        harness="agy",
        receipts_root=tmp_path / "receipts",
    )
    log = _install_fake_agy(tmp_path, monkeypatch, _agy_table(_agy_good_rows(plan.config_path)))
    with pytest.raises(AgyReviewMcpGateError, match=r"scoped HOME/AGY_APP_DATA_DIR.*#8617"):
        verify_agy_review_launch(
            config_path=plan.config_path,
            cwd=tmp_path,
            mode="read-only",
            model=None,
            effort=None,
            task_id="review-agy-task",
            tool_config=_agy_tool_config(plan),
        )
    assert not log.exists()


def test_agy_final_spawned_environment_carries_scoped_home_only_for_review(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.agent_runtime.adapters.agy import AgyAdapter
    from scripts.agent_runtime.env_sanitize import build_agent_env

    real_home = tmp_path / "real-home"
    real_home.mkdir()
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.delenv("AGY_APP_DATA_DIR")
    token = real_home / ".gemini" / "antigravity-cli" / "antigravity-oauth-token"
    token.parent.mkdir(parents=True)
    token.write_text("{}\n", encoding="utf-8")
    plan = _prepare_agy(manifest_file, tmp_path)

    review = AgyAdapter().build_invocation(
        prompt="review",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="review-agy-task",
        session_id=None,
        tool_config=_agy_tool_config(plan),
    )
    review_env = build_agent_env(provider="agy", overrides=review.env_overrides)
    assert review_env["HOME"] == str(plan.agy_home)
    assert review_env["AGY_APP_DATA_DIR"] == str(agy_review_app_data_dir(plan.agy_home))
    assert not any(item.startswith("mcp") for item in review.cmd[1:2])  # no MCP flag exists for agy
    assert "8766" not in " ".join(review.cmd)

    ordinary = AgyAdapter().build_invocation(
        prompt="ordinary",
        mode="read-only",
        cwd=tmp_path,
        model=None,
        task_id="ordinary-agy-task",
        session_id=None,
        tool_config=None,
    )
    ordinary_env = build_agent_env(provider="agy", overrides=ordinary.env_overrides)
    assert "HOME" not in ordinary.env_overrides
    assert "AGY_APP_DATA_DIR" not in ordinary.env_overrides
    assert ordinary_env["HOME"] == str(real_home)
    assert "AGY_APP_DATA_DIR" not in ordinary_env


def test_env_keys_are_exactly_the_three_recording_variables() -> None:
    assert set(ENV_KEYS) == {ENV_ATTEMPT_ID, ENV_MANIFEST_SHA256, ENV_LEDGER_PATH}


@pytest.mark.skipif(shutil.which("agy") is None, reason="agy CLI not installed")
def test_real_agy_cli_lists_exactly_the_scoped_sources_server(manifest_file: Path, tmp_path: Path) -> None:
    """Live CLI: the gate accepts the scoped home and its table matches the strict parser."""
    plan = _prepare_agy(manifest_file, tmp_path)
    verify_agy_review_launch(
        config_path=plan.config_path,
        cwd=tmp_path,
        mode="read-only",
        model=None,
        effort=None,
        task_id="review-agy-live",
        tool_config=_agy_tool_config(plan),
    )


# --- #8652: one sanitizer for every refusal built from untrusted text ---------------------------

_MARKER = "private-marker-8652"
_MARKER_PATHS = [
    pytest.param(f"/srv/{_MARKER}/secret.json", id="absolute"),
    pytest.param(f"~/{_MARKER}", id="tilde"),
    pytest.param(f"C:\\{_MARKER}\\x", id="windows"),
    pytest.param(f"/srv/with space/{_MARKER}/secret.json", id="absolute-with-spaces"),
    pytest.param(f"x/srv/{_MARKER}/x", id="relative"),
    pytest.param(f"%2Fsrv%2F{_MARKER}%2Fx", id="url-encoded-slash"),
    pytest.param(f"C%3A%5C{_MARKER}%5Cx", id="url-encoded-backslash"),
    pytest.param(f"%252Fsrv%252F{_MARKER}%252Fx", id="double-encoded-slash"),
    pytest.param(f"file:///srv/{_MARKER}/x", id="file-url"),
    pytest.param(f"srv\u2215{_MARKER}\u2215x", id="unicode-division-slash"),
    pytest.param(f"srv\uff0f{_MARKER}\uff0fx", id="unicode-fullwidth-slash"),
    pytest.param(f"srv\\{_MARKER}\\x", id="backslash"),
    pytest.param(f"x/srv/a {_MARKER}", id="whitespace-split"),
    pytest.param(f"x%252Fsrv%252Fa {_MARKER}", id="whitespace-split-double-encoded"),
    pytest.param(f"a\t{_MARKER}", id="tab-split"),
]


def _refusal_from_prepare(tmp_path: Path, manifest_file: Path, **overrides: str) -> str:
    kwargs = {"review_id": "rev-001", "attempt_id": "att-001", "harness": "claude", **overrides}
    with pytest.raises(ValueError, match=r"invalid|unsupported") as refused:
        prepare_review_attempt(manifest_path=manifest_file, receipts_root=tmp_path / "receipts", **kwargs)
    return str(refused.value)


def _codex_refusal(tmp_path: Path, manifest_file: Path, monkeypatch: pytest.MonkeyPatch, servers, **script) -> str:
    plan = _prepare_codex(manifest_file, tmp_path)
    if servers is not None:
        _install_fake_codex(tmp_path, monkeypatch, servers)
    else:
        bin_dir = tmp_path / "fake-bin"
        bin_dir.mkdir()
        fake = bin_dir / "codex"
        fake.write_text(f"#!/bin/sh\n{script['body']}", encoding="utf-8")
        fake.chmod(0o755)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    with pytest.raises(CodexReviewMcpGateError) as refused:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    return str(refused.value)


def _agy_refusal(tmp_path: Path, manifest_file: Path, monkeypatch: pytest.MonkeyPatch, stdout: str, **kwargs) -> str:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, monkeypatch, stdout(plan) if callable(stdout) else stdout, **kwargs)
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _agy_row(plan, **cells: str) -> str:
    row = {"name": "sources", "type": "stdio", "status": "enabled", "target": _agy_expected_target(plan.config_path)}
    row.update(cells)
    return _agy_table([tuple(row.values())])


def _surface_review_id(marker, tmp_path, manifest_file, _mp):
    return _refusal_from_prepare(tmp_path, manifest_file, review_id=marker)


def _surface_attempt_id(marker, tmp_path, manifest_file, _mp):
    return _refusal_from_prepare(tmp_path, manifest_file, attempt_id=marker)


def _surface_harness(marker, tmp_path, manifest_file, _mp):
    return _refusal_from_prepare(tmp_path, manifest_file, harness=marker)


def _surface_codex_server_name(marker, tmp_path, manifest_file, mp):
    return _codex_refusal(tmp_path, manifest_file, mp, [{"name": marker, "enabled": True}])


def _surface_codex_non_dict_server(marker, tmp_path, manifest_file, mp):
    return _codex_refusal(tmp_path, manifest_file, mp, [marker])


def _surface_codex_transport_type(marker, tmp_path, manifest_file, mp):
    plan = _prepare_codex(manifest_file, tmp_path)
    entry = _sources_entry(plan.config_path)
    entry["transport"]["type"] = marker
    _install_fake_codex(tmp_path, monkeypatch=mp, servers=[entry])
    with pytest.raises(CodexReviewMcpGateError) as refused:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    return str(refused.value)


def _surface_codex_stderr(marker, tmp_path, manifest_file, mp):
    return _codex_refusal(tmp_path, manifest_file, mp, None, body=f'echo "boom {marker} more" >&2\nexit 3\n')


def _surface_codex_bad_json(marker, tmp_path, manifest_file, mp):
    return _codex_refusal(tmp_path, manifest_file, mp, None, body=f'echo "{{{marker}"\n')


def _surface_agy_stderr(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, "", body=f'echo "boom {marker} more" >&2\nexit 3\n')


def _surface_agy_header(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, f"NAME TYPE STATUS {marker}\n")


def _surface_agy_row_misaligned(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, _agy_table([]) + f"sources stdio enabled {marker}\n")


def _surface_agy_row_unparseable(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, _agy_table([]) + f"sources  stdio  {marker} x  cmd\n")


def _surface_agy_server_name(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, lambda plan: _agy_row(plan, name=marker))


def _surface_agy_repeated_server_name(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(
        tmp_path,
        manifest_file,
        mp,
        lambda plan: _agy_table([(marker, "stdio", "enabled", "c"), (marker, "a", "b", "c")]),
    )


def _surface_agy_type(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, lambda plan: _agy_row(plan, type=marker))


def _surface_agy_status(marker, tmp_path, manifest_file, mp):
    return _agy_refusal(tmp_path, manifest_file, mp, lambda plan: _agy_row(plan, status=marker))


def _surface_agy_scoped_config_keys(marker, tmp_path, manifest_file, mp):
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, mp, _agy_table(_agy_good_rows(plan.config_path)))
    duplicated = json.dumps(marker)
    agy_review_mcp_config_path(plan.agy_home).write_text(f"{{{duplicated}: 1, {duplicated}: 2}}", encoding="utf-8")
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _fail_probe(monkeypatch: pytest.MonkeyPatch, exc: BaseException) -> None:
    """Make the gate's probe subprocess fail with ``exc`` (patched after the attempt is prepared)."""

    def boom(*_args, **_kwargs):
        raise exc

    monkeypatch.setattr(review_mcp_module.subprocess, "run", boom)


def _fail_reads(monkeypatch: pytest.MonkeyPatch, exc: BaseException, *, name: str) -> None:
    """Make ``Path.read_text`` fail with ``exc`` for files called ``name``."""
    real = Path.read_text

    def read_text(self, *args, **kwargs):
        if self.name == name:
            raise exc
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", read_text)


def _codex_probe_failure(tmp_path, manifest_file, mp, exc) -> str:
    plan = _prepare_codex(manifest_file, tmp_path)
    _fail_probe(mp, exc)
    with pytest.raises(CodexReviewMcpGateError) as refused:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    return str(refused.value)


def _agy_probe_failure(tmp_path, manifest_file, mp, exc) -> str:
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, mp, "")
    _fail_probe(mp, exc)
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _surface_codex_probe_strerror(marker, tmp_path, manifest_file, mp):
    return _codex_probe_failure(tmp_path, manifest_file, mp, OSError(errno.ENOENT, marker))


def _surface_codex_probe_filename(marker, tmp_path, manifest_file, mp):
    return _codex_probe_failure(
        tmp_path, manifest_file, mp, OSError(errno.ENOENT, "No such file", marker, None, marker)
    )


def _surface_codex_probe_subprocess_error(marker, tmp_path, manifest_file, mp):
    return _codex_probe_failure(tmp_path, manifest_file, mp, subprocess.SubprocessError(marker))


def _surface_codex_probe_timeout(marker, tmp_path, manifest_file, mp):
    return _codex_probe_failure(tmp_path, manifest_file, mp, subprocess.TimeoutExpired(cmd=marker, timeout=1))


def _surface_codex_config_read_strerror(marker, tmp_path, manifest_file, mp):
    plan = _prepare_codex(manifest_file, tmp_path)
    _fail_reads(mp, OSError(errno.EACCES, marker), name=plan.config_path.name)
    with pytest.raises(CodexReviewMcpGateError) as refused:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    return str(refused.value)


def _surface_codex_config_read_value_error(marker, tmp_path, manifest_file, mp):
    plan = _prepare_codex(manifest_file, tmp_path)
    _fail_reads(mp, ValueError(marker), name=plan.config_path.name)
    with pytest.raises(CodexReviewMcpGateError) as refused:
        verify_codex_review_effective_mcp(config_path=plan.config_path, cwd=tmp_path)
    return str(refused.value)


def _surface_agy_probe_strerror(marker, tmp_path, manifest_file, mp):
    return _agy_probe_failure(tmp_path, manifest_file, mp, OSError(errno.ENOENT, marker))


def _surface_agy_probe_filename(marker, tmp_path, manifest_file, mp):
    return _agy_probe_failure(tmp_path, manifest_file, mp, OSError(errno.ENOENT, "No such file", marker, None, marker))


def _surface_agy_probe_subprocess_error(marker, tmp_path, manifest_file, mp):
    return _agy_probe_failure(tmp_path, manifest_file, mp, subprocess.SubprocessError(marker))


def _surface_agy_probe_timeout(marker, tmp_path, manifest_file, mp):
    return _agy_probe_failure(tmp_path, manifest_file, mp, subprocess.TimeoutExpired(cmd=marker, timeout=1))


def _surface_agy_config_read_strerror(marker, tmp_path, manifest_file, mp):
    plan = _prepare_agy(manifest_file, tmp_path)
    _fail_reads(mp, OSError(errno.EACCES, marker), name=plan.config_path.name)
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _surface_agy_scoped_config_read_strerror(marker, tmp_path, manifest_file, mp):
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, mp, _agy_table(_agy_good_rows(plan.config_path)))
    _fail_reads(mp, OSError(errno.EACCES, marker), name="mcp_config.json")
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _surface_agy_scoped_config_bad_json(marker, tmp_path, manifest_file, mp):
    plan = _prepare_agy(manifest_file, tmp_path)
    _install_fake_agy(tmp_path, mp, _agy_table(_agy_good_rows(plan.config_path)))
    agy_review_mcp_config_path(plan.agy_home).write_text(f"{{{marker}", encoding="utf-8")
    with pytest.raises(AgyReviewMcpGateError) as refused:
        _verify_agy(plan, tmp_path)
    return str(refused.value)


def _surface_agy_oauth_link(marker, tmp_path, manifest_file, mp):
    plan = _prepare_agy(manifest_file, tmp_path)
    link = agy_review_app_data_dir(plan.agy_home) / "antigravity-oauth-token"
    link.unlink()
    link.symlink_to(tmp_path / marker.replace("/", "_").replace("\\", "_"))
    with pytest.raises(AgyReviewMcpGateError) as refused:
        verify_agy_review_launch(
            config_path=plan.config_path,
            cwd=tmp_path,
            mode="read-only",
            model=None,
            effort=None,
            task_id="review-agy-link",
            tool_config=_agy_tool_config(plan),
        )
    return str(refused.value)


_UNTRUSTED_SURFACES = [
    _surface_codex_probe_strerror,
    _surface_codex_probe_filename,
    _surface_codex_probe_subprocess_error,
    _surface_codex_probe_timeout,
    _surface_codex_config_read_strerror,
    _surface_codex_config_read_value_error,
    _surface_agy_probe_strerror,
    _surface_agy_probe_filename,
    _surface_agy_probe_subprocess_error,
    _surface_agy_probe_timeout,
    _surface_agy_config_read_strerror,
    _surface_agy_scoped_config_read_strerror,
    _surface_agy_scoped_config_bad_json,
    _surface_agy_oauth_link,
    _surface_review_id,
    _surface_attempt_id,
    _surface_harness,
    _surface_codex_server_name,
    _surface_codex_non_dict_server,
    _surface_codex_transport_type,
    _surface_codex_stderr,
    _surface_codex_bad_json,
    _surface_agy_stderr,
    _surface_agy_header,
    _surface_agy_row_misaligned,
    _surface_agy_row_unparseable,
    _surface_agy_server_name,
    _surface_agy_repeated_server_name,
    _surface_agy_type,
    _surface_agy_status,
    _surface_agy_scoped_config_keys,
]


@pytest.mark.parametrize("marker", _MARKER_PATHS)
@pytest.mark.parametrize("surface", _UNTRUSTED_SURFACES, ids=lambda fn: fn.__name__.removeprefix("_surface_"))
def test_refusals_never_echo_a_path_from_untrusted_input(
    surface, marker: str, manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A path injected into any untrusted input never reaches a refusal message (#8652)."""
    message = surface(marker, tmp_path, manifest_file, monkeypatch)
    assert message
    assert _MARKER not in message, message
    assert "with space" not in message, message


@pytest.mark.parametrize("field", ["review_id", "attempt_id"])
def test_invalid_identifier_refusal_names_the_rule_and_a_short_prefix_only(
    field: str, manifest_file: Path, tmp_path: Path
) -> None:
    value = "bad id with spaces " + "x" * 300
    message = _refusal_from_prepare(tmp_path, manifest_file, **{field: value})
    assert f"invalid {field}: must match " in message
    assert value not in message
    assert len(message) < 200


def test_echo_identifier_shows_clean_names_verbatim_and_redacts_everything_else() -> None:
    from scripts.agent_runtime.review_mcp import _echo_identifier

    for clean in ("sources", "mcp__sources__verify_words", "att-001", "a.b:c_d-9", "x" * 64):
        assert _echo_identifier(clean) == clean
    for unclean, size in (("x" * 65, 65), ("", 0), ("a b", 3), ("a/b", 3), ("a\\b", 3), ("a%2Fb", 5), ("~x", 2)):
        assert _echo_identifier(unclean) == f"<redacted: {size} chars>"
    assert _echo_identifier("sources\n") == "<redacted: 8 chars>"  # fullmatch, not ``$``
    assert _echo_identifier("sourc\u0435s") == "<redacted: 7 chars>"  # non-ASCII look-alike
    assert _echo_identifier(None) == "<redacted: a NoneType>"


_ENTRY_RE = re.compile(r"--- (?P<label>\w+) \((?P<size>\d+) chars, sha256 (?P<fp>[0-9a-f]{12})\) ---\n")


def test_review_mcp_has_no_free_text_renderer() -> None:
    """The allowlist/blocklist free-text path is gone: nothing renders untrusted text into a refusal (#8652)."""
    assert not hasattr(review_mcp_module, "_free_text")


def test_untrusted_stand_in_carries_size_and_fingerprint_and_the_file_holds_the_text(tmp_path: Path) -> None:
    text = f"boom x/srv/a {_MARKER} \u2215 %252Fsrv\nsecond line\n"
    diagnostics = tmp_path / "att-001.diagnostics.log"

    stand_in = review_mcp_module._untrusted("stderr", text, diagnostics)

    fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    assert stand_in == f"<stderr: {len(text)} chars, sha256 {fingerprint}; details in att-001.diagnostics.log>"
    assert _MARKER not in stand_in
    assert stat.S_IMODE(diagnostics.stat().st_mode) == 0o600
    content = diagnostics.read_text(encoding="utf-8")
    header = _ENTRY_RE.match(content)
    assert header is not None
    assert (header["label"], int(header["size"]), header["fp"]) == ("stderr", len(text), fingerprint)
    assert content[header.end() :] == text + "\n"


def test_untrusted_appends_entries_and_tightens_a_loose_file(tmp_path: Path) -> None:
    diagnostics = tmp_path / "att-001.diagnostics.log"
    diagnostics.write_text("earlier\n", encoding="utf-8")
    diagnostics.chmod(0o644)

    review_mcp_module._untrusted("stderr", "one", diagnostics)
    review_mcp_module._untrusted("row", "two", diagnostics)

    assert stat.S_IMODE(diagnostics.stat().st_mode) == 0o600
    content = diagnostics.read_text(encoding="utf-8")
    assert content.startswith("earlier\n--- stderr (3 chars")
    assert "\none\n--- row (3 chars" in content
    assert content.endswith("\ntwo\n")


def test_untrusted_still_reports_size_and_fingerprint_when_the_file_cannot_be_written(tmp_path: Path) -> None:
    stand_in = review_mcp_module._untrusted("stderr", f"x/srv/a {_MARKER}", tmp_path / "missing-dir" / "d.log")
    assert "details not saved: ENOENT" in stand_in
    assert "sha256 " in stand_in
    assert _MARKER not in stand_in
    assert "missing-dir" not in stand_in
    planted = tmp_path / "planted.diagnostics.log"
    planted.symlink_to(tmp_path / "elsewhere")
    assert "details not saved: ELOOP" in review_mcp_module._untrusted("stderr", "x", planted)
    assert not (tmp_path / "elsewhere").exists()


@pytest.mark.parametrize(
    ("exc", "expected_head"),
    [
        (OSError(errno.ENOENT, "No such file", "/srv/x"), "FileNotFoundError (ENOENT): <exception: "),
        (PermissionError(errno.EACCES, "denied"), "PermissionError (EACCES): <exception: "),
        (OSError("bare"), "OSError: <exception: "),
        (OSError(-99999, "unknown code"), "OSError: <exception: "),
        (subprocess.TimeoutExpired(cmd="x", timeout=2.5), "TimeoutExpired after 2.5s: <exception: "),
        (subprocess.SubprocessError(_MARKER), "SubprocessError: <exception: "),
        (KeyError(_MARKER), "KeyError: <exception: "),
        (ValueError(f"x/srv/a {_MARKER}"), "ValueError: <exception: "),
    ],
)
def test_exc_reason_names_class_and_errno_only(exc: BaseException, expected_head: str, tmp_path: Path) -> None:
    reason = review_mcp_module._exc_reason(exc, tmp_path / "att.diagnostics.log")
    assert reason.startswith(expected_head), reason
    assert _MARKER not in reason
    assert "/srv/x" not in reason
    assert "details in att.diagnostics.log" in reason


def test_refusal_names_the_diagnostics_file_and_the_file_holds_the_full_probe_text(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex/AGY stderr is fingerprinted in the refusal and kept whole in a 0600 file beside the attempt config."""
    for harness, refusal in (
        ("codex", lambda mp: _codex_refusal(tmp_path, manifest_file, mp, None, body=_STDERR_BODY)),
        ("agy", lambda mp: _agy_refusal(tmp_path, manifest_file, mp, "", body=_STDERR_BODY)),
    ):
        message = refusal(monkeypatch)
        diagnostics = next(tmp_path.rglob(f"att-{harness}-001.diagnostics.log"))
        assert diagnostics.parent == next(tmp_path.rglob(f"att-{harness}-001.mcp.json")).parent
        assert stat.S_IMODE(diagnostics.stat().st_mode) == 0o600
        assert f"details in {diagnostics.name}" in message
        assert str(diagnostics.parent) not in message
        entry = diagnostics.read_text(encoding="utf-8")
        header = _ENTRY_RE.match(entry)
        assert header is not None
        body = entry[header.end() :].removesuffix("\n")
        assert body == f"boom x/srv/a {_MARKER} more\n"
        assert f"<stderr: {header['size']} chars, sha256 {header['fp']};" in message
        assert hashlib.sha256(body.encode("utf-8")).hexdigest()[:12] == header["fp"]
        assert _MARKER not in message


_STDERR_BODY = f'echo "boom x/srv/a {_MARKER} more" >&2\nexit 3\n'


def test_refusals_name_the_error_class_and_errno(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.MonkeyPatch.context() as mp:
        message = _surface_codex_probe_strerror(_MARKER, tmp_path, manifest_file, mp)
    assert "could not compute the effective MCP set (FileNotFoundError (ENOENT): <exception: " in message
    other = tmp_path / "second"
    other.mkdir()
    with pytest.MonkeyPatch.context() as mp:
        message = _surface_agy_scoped_config_read_strerror(_MARKER, other, manifest_file, mp)
    assert "PermissionError (EACCES): <exception: " in message
    diagnostics = next(other.rglob("att-agy-001.diagnostics.log"))
    assert _MARKER in diagnostics.read_text(encoding="utf-8")
    assert stat.S_IMODE(diagnostics.stat().st_mode) == 0o600


def test_refusals_keep_allowlisted_names_and_counts_verbatim(
    manifest_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A clean name still appears, so a refusal stays actionable; an unclean one shows its size."""
    message = _codex_refusal(
        tmp_path,
        manifest_file,
        monkeypatch,
        [{"name": "rogue-server", "enabled": True}, {"name": "a/b", "enabled": True}],
    )
    assert "'rogue-server'" in message
    assert "'<redacted: 3 chars>'" in message
    assert "exactly ['sources'] is allowed" in message
    message = _refusal_from_prepare(tmp_path, manifest_file, harness="mystery-harness")
    assert "got mystery-harness" in message
    message = _refusal_from_prepare(tmp_path, manifest_file, harness="a/b")
    assert "got <redacted: 3 chars>" in message
