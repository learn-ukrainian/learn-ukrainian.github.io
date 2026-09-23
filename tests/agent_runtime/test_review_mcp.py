"""Tests for per-attempt stdio sources MCP launcher and ledger provisioner (#8517)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tomllib
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

import scripts.delegate as delegate_cli
from scripts.agent_runtime.adapters.claude import ClaudeAdapter
from scripts.agent_runtime.adapters.codex import CodexAdapter
from scripts.agent_runtime.adapters.cursor import CursorAdapter
from scripts.agent_runtime.review_mcp import (
    ENV_ATTEMPT_ID,
    ENV_LEDGER_PATH,
    ENV_MANIFEST_SHA256,
    SUPPORTED_HARNESSES,
    CodexReviewMcpGateError,
    codex_review_home_path,
    prepare_review_attempt,
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


def test_prepare_review_attempt_refuses_agy(manifest_file: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"review attempt refused for agy:.*#8517"):
        prepare_review_attempt(
            review_id="rev-001",
            attempt_id="att-001",
            manifest_path=manifest_file,
            harness="agy",
            receipts_root=tmp_path,
        )


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
