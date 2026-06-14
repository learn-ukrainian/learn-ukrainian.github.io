from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.cursor import CursorAdapter


@pytest.fixture
def adapter():
    return CursorAdapter()


def test_cursor_adapter_resume_first_run(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/cursor-agent")

    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id="new-task-1",
        session_id=None,
        tool_config=None,
    )

    assert "--resume" not in plan.cmd


def test_cursor_adapter_prefers_cursor_agent_over_generic_agent(adapter, tmp_path, monkeypatch):
    """Regression: a generic ``agent`` binary on PATH (e.g. grok's Grok Build
    TUI at ~/.local/bin/agent) must NOT shadow ``cursor-agent``. Resolving
    ``agent`` first silently misfired every cursor dispatch to grok
    (returncode 2: "a value is required for '--single <PROMPT>'")."""
    resolved = {
        "cursor-agent": "/Users/x/.local/bin/cursor-agent",
        "agent": "/Users/x/.local/bin/agent",  # impostor: grok Build TUI
    }
    monkeypatch.setattr("shutil.which", lambda name: resolved.get(name))

    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id="bin-resolve-1",
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[0] == "/Users/x/.local/bin/cursor-agent"


def test_cursor_adapter_falls_back_to_agent_when_no_cursor_agent(adapter, tmp_path, monkeypatch):
    """When ``cursor-agent`` is absent, fall back to a generic ``agent`` binary
    (legacy cursor installs shipped under the bare ``agent`` name)."""
    monkeypatch.setattr(
        "shutil.which",
        lambda name: "/usr/local/bin/agent" if name == "agent" else None,
    )

    plan = adapter.build_invocation(
        prompt="hi",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id="bin-resolve-2",
        session_id=None,
        tool_config=None,
    )

    assert plan.cmd[0] == "/usr/local/bin/agent"


def test_cursor_adapter_resume_explicit_session(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/cursor-agent")

    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id="new-task-1",
        session_id="session-explicit-123",
        tool_config=None,
    )

    # Verify `--resume` and `session-explicit-123` are passed in argv
    idx = plan.cmd.index("--resume")
    assert plan.cmd[idx + 1] == "session-explicit-123"


def test_cursor_adapter_does_not_resume_from_disk(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/cursor-agent")

    # Mock Path.home() so we can construct a fake .cursor directory
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    # Create a fake transcript directory
    encoded = adapter._encode_workspace_path(str(tmp_path))
    transcript_dir = fake_home / ".cursor" / "projects" / encoded / "agent-transcripts" / "session-disk-789"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    plan = adapter.build_invocation(
        prompt="hello",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id="task-disk",
        session_id=None,
        tool_config=None,
    )

    assert "--resume" not in plan.cmd


def test_cursor_adapter_does_not_resume_from_api_usage(adapter, tmp_path, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda _: "/usr/local/bin/cursor-agent")

    # Create fake api_usage directory and write log
    repo_root = Path(__file__).resolve().parents[2]
    usage_dir = repo_root / "batch_state" / "api_usage"
    usage_dir.mkdir(parents=True, exist_ok=True)

    log_file = usage_dir / "usage_cursor-delegate_test.jsonl"
    record = {
        "ts": "2026-05-26T00:00:00Z",
        "agent": "cursor",
        "entrypoint": "delegate",
        "task_id": "task-api-usage",
        "session_id": "session-api-usage-456",
    }

    # Write a test log record
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    try:
        plan = adapter.build_invocation(
            prompt="hello",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id="task-api-usage",
            session_id=None,
            tool_config=None,
        )

        assert "--resume" not in plan.cmd
    finally:
        # Clean up the test log
        if log_file.exists():
            log_file.unlink()


def test_cursor_adapter_parse_response_session_id_stdout(adapter):
    stdout = '{"type": "message", "role": "assistant", "sessionId": "session-stdout-111", "content": "Done"}'
    res = adapter.parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert res.ok is True
    assert res.session_id == "session-stdout-111"


def test_cursor_adapter_parse_response_session_id_disk(adapter, tmp_path, monkeypatch):
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    # Initialize workspace and snapshot
    workspace = str(tmp_path)
    adapter._workspace = workspace
    adapter._transcripts_snapshot = adapter._snapshot_preexisting_transcripts(workspace)

    # Now simulate running the session, which creates a new directory on disk
    encoded = adapter._encode_workspace_path(workspace)
    session_dir = fake_home / ".cursor" / "projects" / encoded / "agent-transcripts" / "session-new-999"
    session_dir.mkdir(parents=True, exist_ok=True)

    res = adapter.parse_response(
        stdout='{"type": "text", "content": "Hello"}',
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert res.ok is True
    assert res.session_id == "session-new-999"


def test_cursor_adapter_recovers_response_from_session_transcript(
    adapter,
    tmp_path,
    monkeypatch,
):
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)

    workspace = str(tmp_path)
    adapter._workspace = workspace
    adapter._transcripts_snapshot = adapter._snapshot_preexisting_transcripts(workspace)
    session_id = "session-transcript-123"
    encoded = adapter._encode_workspace_path(workspace)
    transcript = (
        fake_home
        / ".cursor"
        / "projects"
        / encoded
        / "agent-transcripts"
        / session_id
        / f"{session_id}.jsonl"
    )
    transcript.parent.mkdir(parents=True)
    transcript.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "role": "assistant",
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": '{"score": 8, "verdict": "PASS", "findings": []}',
                                },
                                {
                                    "type": "tool_use",
                                    "name": "mcp_sources_search_style_guide",
                                    "input": {"query": "фокусування"},
                                },
                            ]
                        },
                    }
                ),
                json.dumps({"type": "turn_ended", "status": "success"}),
            ]
        ),
        encoding="utf-8",
    )

    stdout = "\n".join(
        [
            json.dumps({"type": "system", "session_id": session_id}),
            json.dumps({"type": "user", "message": {"content": "prompt"}}),
        ]
    )

    res = adapter.parse_response(
        stdout=stdout,
        stderr="",
        returncode=0,
        output_file=None,
    )

    assert res.ok is True
    assert res.response == '{"score": 8, "verdict": "PASS", "findings": []}'
    assert res.session_id == session_id
    assert res.tool_calls[0]["name"] == "mcp_sources_search_style_guide"
