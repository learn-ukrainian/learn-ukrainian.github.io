"""Unit tests for thin fleet-comms CLI (plane-status + formal-job get)."""

from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts.fleet_comms import cli as comms_cli
from scripts.fleet_comms.cli import (
    EXIT_ERROR,
    EXIT_NOT_FOUND,
    EXIT_OK,
    build_parser,
    get_formal_review_job,
    main,
)
from scripts.fleet_comms.migrations import MIGRATIONS, apply_migrations
from scripts.fleet_comms.paths import PlaneRootAnchorError


def _seed_plane_db(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    db_path = root / "comms.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        assert apply_migrations(conn) == MIGRATIONS[-1].version
        conn.execute(
            """INSERT INTO formal_review_jobs(
                review_id, repository, pr_number, head_sha, gate_kind,
                state, snapshot_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "rev-abc",
                "learn-ukrainian/learn-ukrainian.github.io",
                5512,
                "deadbeefcafebabe0123456789abcdef01234567",
                "cross-family-review",
                "open",
                None,
                "2026-07-20T12:00:00Z",
            ),
        )
        conn.execute(
            """INSERT INTO formal_review_attempts(
                review_attempt_id, review_id, attempt_number,
                completion_state, raw_capture_artifact_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                "att-1",
                "rev-abc",
                1,
                "incomplete",
                None,
                "2026-07-20T12:01:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_plane_status_cli_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "shadow")
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(tmp_path / "plane"))
    tele = tmp_path / "tele.jsonl"
    tele.write_text(
        json.dumps({"event": "plane_complete", "parity_ok": True}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FLEET_COMMS_PLANE_TELEMETRY", str(tele))

    rc = main(["plane-status"])
    assert rc == EXIT_OK
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["mode"] == "shadow"
    assert data["enabled"] is True
    assert data["read_only"] is True
    assert data["response_schema_version"] == "comms.v2"
    assert data["store"]["kind"] == "comms-plane"
    assert data["store"]["reachable"] is False
    assert "plane_root" not in data
    assert data["parity_telemetry"]["event_count"] == 1


def test_plane_status_cli_root_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """Every --root entrypoint refuses a checkout before invoking its handler."""
    monkeypatch.delenv("FLEET_COMMS_MESSAGE_PLANE", raising=False)
    monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
    root = tmp_path / "custom-root"
    root.mkdir()
    rc = main(["plane-status", "--root", str(root)])
    assert rc == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    # Config default is authority; --root only redirects storage, not mode.
    assert data["mode"] == "authority"
    assert data["response_schema_version"] == "comms.v2"
    assert data["store"]["kind"] == "comms-plane"
    assert "plane_root" not in data

    checkout = tmp_path / "checkout"
    (checkout / ".git").mkdir(parents=True)
    before = sorted(checkout.rglob("*"))
    pending = [((), build_parser())]
    entrypoints = []
    while pending:
        command, parser = pending.pop()
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                pending.extend(((*command, name), child) for name, child in action.choices.items())
        if not any("--root" in action.option_strings for action in parser._actions):
            continue
        argv = list(command)
        required = [action for action in parser._actions if action.required]
        for group in parser._mutually_exclusive_groups:
            if group.required:
                required.append(group._group_actions[0])
        for action in required:
            if action.option_strings:
                argv.append(action.option_strings[0])
            argv.append("1" if action.type is int else "fixture")
        entrypoints.append((argv, parser.get_default("func").__name__))
    assert len(entrypoints) == 27
    for argv, handler_name in entrypoints:
        handler = Mock(side_effect=AssertionError("unsafe root reached command handler"))
        with monkeypatch.context() as guard:
            guard.setattr(f"scripts.fleet_comms.cli.{handler_name}", handler)
            assert main([*argv, "--root", str(checkout)]) == EXIT_ERROR
        output = capsys.readouterr()
        assert output.out == ""
        assert output.err == "plane_root_is_git_checkout\n"
        handler.assert_not_called()
    assert sorted(checkout.rglob("*")) == before

    boundary_args = SimpleNamespace(root=str(checkout), tasks_dir=str(tmp_path / "uncreated"))
    with pytest.raises(PlaneRootAnchorError, match=r"^plane_root_is_git_checkout$"):
        comms_cli._resolve_plane_db(boundary_args)
    with pytest.raises(PlaneRootAnchorError, match=r"^plane_root_is_git_checkout$"):
        comms_cli.cmd_bottleneck_metrics(boundary_args)
    assert not (tmp_path / "uncreated").exists()
    assert comms_cli._resolve_plane_db(SimpleNamespace(root=str(root))) == root / "comms.sqlite3"

    alias = tmp_path / "checkout-alias"
    alias.symlink_to(checkout, target_is_directory=True)
    monkeypatch.chdir(tmp_path)
    assert main(["plane-status", "--root", "checkout-alias/absent/.."]) == EXIT_ERROR
    assert capsys.readouterr().err == "plane_root_is_git_checkout\n"
    monkeypatch.setenv("FLEET_COMMS_ROOT", str(alias))
    assert main(["plane-status"]) == EXIT_ERROR
    assert capsys.readouterr().err == "plane_root_is_git_checkout\n"

    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    default_root = checkout / "batch_state" / "fleet-comms" / "v1"
    default_root.parent.mkdir(parents=True)
    default_root.symlink_to(loop)
    before = sorted(tmp_path.rglob("*"))
    monkeypatch.chdir(checkout)
    connect = Mock(side_effect=AssertionError("unresolvable root reached backend"))
    monkeypatch.setattr(comms_cli, "cp_connect", connect)
    monkeypatch.setattr("scripts.fleet_comms.message_plane.cp_connect", connect)
    for env_root in (str(loop), None):
        if env_root is not None:
            monkeypatch.setenv("FLEET_COMMS_ROOT", env_root)
        else:
            monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
        assert main(["plane-status"]) == EXIT_ERROR
        output = capsys.readouterr()
        assert output.out == ""
        assert output.err == "plane_root_unresolvable\n"
        with pytest.raises(PlaneRootAnchorError, match=r"^plane_root_unresolvable$"):
            comms_cli._resolve_plane_db(SimpleNamespace(root=None))
    connect.assert_not_called()
    assert sorted(tmp_path.rglob("*")) == before


def test_get_formal_review_job_helper(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    job = get_formal_review_job("rev-abc", root=root)
    assert job["review_id"] == "rev-abc"
    assert job["pr_number"] == 5512
    assert job["gate_kind"] == "cross-family-review"
    assert len(job["attempts"]) == 1
    assert job["attempts"][0]["review_attempt_id"] == "att-1"

    # Even an existing DB at a checkout root must be refused before opening it.
    (root / ".git").mkdir()
    before = (root / "comms.sqlite3").read_bytes()
    connect = Mock(side_effect=AssertionError("checkout root reached a connection"))
    monkeypatch.setattr("scripts.fleet_comms.cli.cp_connect", connect)
    with pytest.raises(PlaneRootAnchorError, match=r"^plane_root_is_git_checkout$"):
        get_formal_review_job("rev-abc", root=root)
    connect.assert_not_called()
    assert (root / "comms.sqlite3").read_bytes() == before


def test_formal_job_get_cli(tmp_path: Path, capsys) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    rc = main(["formal-job", "get", "rev-abc", "--root", str(root)])
    assert rc == EXIT_OK
    data = json.loads(capsys.readouterr().out)
    assert data["review_id"] == "rev-abc"
    assert data["repository"] == "learn-ukrainian/learn-ukrainian.github.io"
    assert data["attempts"][0]["completion_state"] == "incomplete"


def test_formal_job_get_not_found(tmp_path: Path, capsys) -> None:
    root = tmp_path / "plane"
    _seed_plane_db(root)
    rc = main(["formal-job", "get", "missing", "--root", str(root)])
    assert rc == EXIT_NOT_FOUND
    err = capsys.readouterr().err
    assert "not found" in err


def test_formal_job_get_missing_db(tmp_path: Path, capsys) -> None:
    rc = main(["formal-job", "get", "rev-abc", "--root", str(tmp_path / "empty")])
    assert rc == EXIT_ERROR
    assert "plane DB not found" in capsys.readouterr().err


def test_acp_discuss_cli_scopes_active_transport_and_restores_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    observed: list[str | None] = []

    def fake_run_discussion(**_kwargs):
        observed.append(os.environ.get("LU_ACPX_TRANSPORT"))
        return {"state": "COMPLETE"}

    monkeypatch.setenv("LU_ACPX_TRANSPORT", "shadow")
    monkeypatch.setattr(acpx_discuss, "run_discussion", fake_run_discussion)
    monkeypatch.setattr("sys.stdin", io.StringIO("bounded design question"))

    rc = main(
        [
            "acp-discuss",
            "--cwd",
            str(tmp_path),
            "--task-id",
            "task-6094",
            "--correlation-id",
            "corr-6094",
            "--idempotency-key",
            "idem-6094",
            "--rounds",
            "2",
            "--json",
        ]
    )

    assert rc == EXIT_OK
    assert observed == ["active"]
    assert os.environ["LU_ACPX_TRANSPORT"] == "shadow"
    assert json.loads(capsys.readouterr().out) == {"state": "COMPLETE"}


def test_supported_bridge_command_defaults_to_durable_acp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.ai_agent_bridge import _channels, _channels_cli, _config, _db

    db_path = tmp_path / "bridge.db"
    monkeypatch.setattr(_config, "DB_PATH", db_path)
    monkeypatch.setattr(_db, "DB_PATH", db_path)
    monkeypatch.setattr(
        "scripts.fleet_comms.artifacts.default_plane_root",
        lambda **_kwargs: tmp_path / "authority-plane",
    )
    monkeypatch.setattr(_channels, "fetch_monitor_state", lambda: None)
    monkeypatch.setattr(_channels, "context_sha256", lambda path: "")
    monkeypatch.setattr(
        _channels,
        "load_channel_context",
        lambda channel: {"body": "", "revs": {}, "missing": []},
    )
    monkeypatch.delenv("LU_AGENT_COMM_TRANSPORT", raising=False)
    monkeypatch.delenv("LU_RUNTIME_INITIATOR", raising=False)
    monkeypatch.delenv("LU_RUNTIME_INITIATOR_SOURCE", raising=False)
    # Keep launcher-provided seat identity out of the default-initiator check.
    for variable in (
        "SESSION_HANDOFF_AGENT",
        "SESSION_STREAM_AGENT",
        "CODEX_SESSION",
        "CLAUDE_AGENT_NAME",
        "GROK_AGENT",
        "GEMINI_SESSION",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("CODEX_THREAD_ID", "thread-6159")
    _channels.create_channel("architecture", exist_ok=False)
    observed: dict[str, object] = {}

    def fake_run_discussion(**kwargs):
        observed.update(kwargs)
        return {
            "conversation_id": "conversation_" + ("a" * 32),
            "state": "COMPLETE",
            "rounds_completed": 2,
            "synthesis": "ACP synthesis",
        }

    monkeypatch.setattr("agent_runtime.acpx_discuss.run_discussion", fake_run_discussion)
    monkeypatch.setattr(
        "agent_runtime.runner.invoke",
        lambda *_a, **_k: pytest.fail("eligible ACP discussion must not call bridge runtime"),
    )
    args = SimpleNamespace(
        channel="architecture",
        body="Compare the bounded options.",
        with_agents="cursor,pool",
        max_rounds=2,
        review=False,
        models=None,
    )

    assert _channels_cli._handle_discuss(args) == 0
    assert observed["participants"] == ("cursor", "pool")
    assert observed["initiator"] == "codex"
    assert "Compare the bounded options." in str(observed["prompt"])
    assert "--- monitor: project state" not in str(observed["prompt"])
    output = capsys.readouterr().out
    assert "transport: ACP (cursor, pool)" in output
    assert "/fleet.html?conversation=conversation_" in output
    from scripts.fleet_comms.authority import AuthorityService

    with AuthorityService(root=tmp_path / "authority-plane") as authority:
        result = authority.store.connection.execute(
            "SELECT body_inline FROM comms_messages WHERE kind = 'discussion-result'"
        ).fetchone()
    assert result is not None
    assert "[ACP COMPLETE]" in str(result["body_inline"])


def test_acp_discuss_cli_busy_is_body_free_no_queue_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    def refuse_busy(**_kwargs):
        raise acpx_discuss.AcpxDiscussionBusyError("private holder details")

    monkeypatch.setattr(acpx_discuss, "run_discussion", refuse_busy)
    monkeypatch.setattr("sys.stdin", io.StringIO("bounded design question"))

    rc = main(
        [
            "acp-discuss",
            "--cwd",
            str(tmp_path),
            "--task-id",
            "task-6094",
            "--correlation-id",
            "corr-6094",
            "--idempotency-key",
            "idem-6094",
            "--json",
        ]
    )

    output = capsys.readouterr()
    assert rc == EXIT_ERROR
    assert json.loads(output.out) == {
        "classification": "busy",
        "queued": False,
        "retryable": False,
        "state": "BUSY",
    }
    assert output.err == ""
    assert "private holder details" not in output.out


def test_acp_verify_cli_exit_codes_and_compact_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from scripts.agent_runtime import acpx_discuss

    conversation_id = "conversation_" + ("a" * 32)
    monkeypatch.setattr(
        acpx_discuss,
        "verify_discussion_receipt",
        lambda **_kwargs: {
            "conversation_id": conversation_id,
            "verified": True,
            "content_included": False,
        },
    )

    rc = main(
        [
            "acp-verify",
            "--conversation-id",
            conversation_id,
            "--root",
            str(tmp_path),
            "--require-replay",
            "--json",
        ]
    )

    assert rc == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {
        "content_included": False,
        "conversation_id": conversation_id,
        "verified": True,
    }


def test_cli_collectors_emit_store_not_db_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("FLEET_COMMS_ROOT", raising=False)
    monkeypatch.setenv("FLEET_COMMS_MESSAGE_PLANE", "off")
    missing_broker = tmp_path / "missing.db"
    monkeypatch.setenv("AB_DB_PATH", str(missing_broker))

    for command in ("metrics", "backlog", "dead-letters"):
        rc = main([command, "--legacy"])
        assert rc == EXIT_OK
        payload = json.loads(capsys.readouterr().out)
        assert payload["response_schema_version"] == "comms.v2"
        assert payload["store"]["kind"] == "legacy-broker"
        assert payload["store"]["reachable"] is False
        assert "db_path" not in payload
