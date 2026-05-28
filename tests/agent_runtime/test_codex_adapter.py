from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from scripts.agent_runtime.adapters.base import InvocationPlan
from scripts.agent_runtime.adapters.codex import CodexAdapter


def test_codex_build_invocation_sends_prompt_via_stdin(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    adapter = CodexAdapter()

    plan = adapter.build_invocation(
        prompt="write the module",
        mode="workspace-write",
        cwd=tmp_path,
        model="gpt-5.5",
        task_id=None,
        session_id=None,
        tool_config=None,
        effort="xhigh",
    )

    assert plan.cwd == tmp_path
    assert plan.stdin_payload == "write the module"
    assert plan.cmd[-1] == "-"


def test_codex_build_invocation_honors_scoped_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("scripts.agent_runtime.adapters.codex.shutil.which", lambda _: "codex")
    adapter = CodexAdapter()
    scoped_home = tmp_path / "codex-home"

    plan = adapter.build_invocation(
        prompt="write the module",
        mode="workspace-write",
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"codex_home_override": str(scoped_home)},
        effort=None,
    )

    assert plan.env_overrides["CODEX_HOME"] == str(scoped_home)


def test_codex_rollout_capture_includes_local_date_midnight_straddle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    adapter = CodexAdapter()
    scoped_home = tmp_path / "codex-home"
    local_rollout_dir = scoped_home / "sessions" / "2026" / "05" / "29"
    local_rollout_dir.mkdir(parents=True)
    rollout = local_rollout_dir / "rollout-2026-05-29T00-12-26-test.jsonl"
    prompt = "write the lesson"
    rollout.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": prompt},
                    }
                ),
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "function_call",
                            "namespace": "mcp__sources__",
                            "name": "verify_words",
                            "arguments": json.dumps({"words": ["ранок"]}),
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    output_file = tmp_path / "codex-output.txt"
    output_file.write_text("done", encoding="utf-8")
    utc_now = datetime(2026, 5, 28, 22, 12, tzinfo=UTC)
    local_now = datetime(2026, 5, 29, 0, 12, tzinfo=timezone(timedelta(hours=2)))

    adapter._codex_home_scope = str(scoped_home)
    monkeypatch.setattr(adapter, "_rollout_discovery_times", lambda: (utc_now, local_now))
    adapter._rollout_snapshot = set()

    assert local_rollout_dir in adapter._candidate_rollout_dirs()

    result = adapter.parse_response(
        stdout="",
        stderr="",
        returncode=0,
        output_file=output_file,
        plan=InvocationPlan(cmd=["codex"], cwd=tmp_path, stdin_payload=prompt),
    )

    assert [call["name"] for call in result.tool_calls] == ["mcp__sources__verify_words"]
