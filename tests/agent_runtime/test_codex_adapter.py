from __future__ import annotations

from pathlib import Path

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
