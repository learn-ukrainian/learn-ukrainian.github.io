"""Headless Claude wrappers enforce background-task controls (#9690, #9750).

Direct wrapper and caller tests verify the child's environment, background-tool
restrictions, timeout handling, and cleanup without a repository spawn inventory.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime.adapters import claude as claude_adapter
from scripts.agent_runtime.adapters.claude import (
    HEADLESS_BACKGROUND_TOOL_DENIES,
    headless_claude_argv,
    popen_headless_claude,
    run_headless_claude,
)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SWITCH = "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"
ADVISOR_SWITCH = "CLAUDE_CODE_DISABLE_ADVISOR_TOOL"
DENIES = ",".join(HEADLESS_BACKGROUND_TOOL_DENIES)

# --- The wrappers ----------------------------------------------------------------------


@pytest.fixture
def ambient_switch_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """The test process's own env has background tasks *enabled*.

    A parent that already carries the switch (a Claude session running the
    suite) would otherwise let a caller that forwards ``os.environ`` pass.
    """
    monkeypatch.setenv(SWITCH, "0")
    monkeypatch.setenv("LU_AMBIENT_PROBE", "ambient")


@pytest.fixture
def spawned(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record every ``subprocess.run``/``Popen`` the wrappers make, without starting a process."""
    calls: list[dict[str, Any]] = []

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"api": "run", "argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, 0, stdout="out", stderr="")

    def fake_popen(argv: list[str], **kwargs: Any) -> str:
        calls.append({"api": "Popen", "argv": argv, **kwargs})
        return "process"

    monkeypatch.setattr(claude_adapter.subprocess, "run", fake_run)
    monkeypatch.setattr(claude_adapter.subprocess, "Popen", fake_popen)
    return calls


def test_argv_builder_adds_denies_before_the_end_of_options_marker() -> None:
    argv = headless_claude_argv(["claude", "-p", "--model", "m", "--", "prompt"])
    assert argv == ["claude", "-p", "--model", "m", "--disallowedTools", DENIES, "--", "prompt"]


def test_argv_builder_appends_denies_without_a_marker_and_is_idempotent() -> None:
    argv = headless_claude_argv(("claude", "-p", "prompt"))
    assert argv == ["claude", "-p", "prompt", "--disallowedTools", DENIES]
    assert headless_claude_argv(argv) == argv


@pytest.mark.parametrize("flag", ["--disallowedTools", "--disallowed-tools"])
def test_argv_builder_merges_into_a_stricter_existing_list(flag: str) -> None:
    base = ["claude", "-p", flag, "Edit,Bash(git push *),Monitor", "--", "a --disallowedTools b"]
    assert headless_claude_argv(base) == [
        "claude",
        "-p",
        flag,
        "Edit,Bash(git push *),Monitor,ScheduleWakeup,CronCreate,Workflow",
        "--",
        "a --disallowedTools b",
    ]


def test_argv_builder_merges_the_equals_form_and_leaves_its_input_unchanged() -> None:
    base = ["claude", "-p", "--disallowedTools=Edit"]
    assert headless_claude_argv(base) == ["claude", "-p", f"--disallowedTools=Edit,{DENIES}"]
    assert base == ["claude", "-p", "--disallowedTools=Edit"]


# How each wrapper's callers bound the run: ``run`` takes a timeout, a Popen caller bounds communicate().
_BOUNDS: dict[Any, dict[str, Any]] = {
    run_headless_claude: {"timeout": 5},
    popen_headless_claude: {"start_new_session": True},
}


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("wrapper", list(_BOUNDS))
def test_wrapper_child_gets_exactly_the_base_env_plus_the_switch(wrapper: Any, spawned: list[dict[str, Any]]) -> None:
    base = {"PATH": "/bin", SWITCH: "0"}
    wrapper(["claude", "-p", "x"], base_env=base, cwd="/w", **_BOUNDS[wrapper])
    (call,) = spawned
    assert call["env"] == {
        "PATH": "/bin",
        SWITCH: "1",
        ADVISOR_SWITCH: "1",
    }, "ambient must not leak into an exact base env"
    assert base == {"PATH": "/bin", SWITCH: "0"}, "the caller's mapping is copied, never mutated"
    assert call["argv"] == ["claude", "-p", "x", "--disallowedTools", DENIES]
    assert call["cwd"] == "/w" and call.items() >= _BOUNDS[wrapper].items()
    assert "shell" not in call and "executable" not in call


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("wrapper", list(_BOUNDS))
def test_wrapper_without_a_base_env_copies_the_ambient_env_and_forces_the_switch(
    wrapper: Any, spawned: list[dict[str, Any]]
) -> None:
    import os

    wrapper(["claude", "-p", "x"], **_BOUNDS[wrapper])
    (call,) = spawned
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert call["env"][SWITCH] == "1"
    assert os.environ[SWITCH] == "0"


@pytest.mark.parametrize("wrapper", list(_BOUNDS))
@pytest.mark.parametrize(
    ("argv", "kwargs"),
    [
        (["claude", "-p"], {"env": {SWITCH: "0"}}),
        (["claude", "-p"], {"shell": True}),
        (["claude", "-p"], {"shell": False}),
        (["claude", "-p"], {"executable": "/bin/sh"}),
        ("claude -p hello", {}),
        (b"claude -p hello", {}),
        (["claude", "-p", Path("prompt")], {}),
    ],
    ids=["env", "shell-true", "shell-false", "executable", "str-argv", "bytes-argv", "non-str-element"],
)
def test_wrapper_refuses_env_shell_executable_and_non_argv(
    wrapper: Any, argv: Any, kwargs: dict[str, Any], spawned: list[dict[str, Any]]
) -> None:
    with pytest.raises(TypeError, match=r"own|argv"):
        wrapper(argv, **kwargs, **_BOUNDS[wrapper])
    assert spawned == []


# --- Behaviour: each caller's child gets both controls and keeps its own policy ---------------


def _assert_child_controlled(argv: list[str], env: dict[str, str]) -> None:
    flag = argv.index("--disallowedTools")
    assert set(HEADLESS_BACKGROUND_TOOL_DENIES) <= set(argv[flag + 1].split(","))
    if "--" in argv:
        assert flag < argv.index("--")
    assert env[SWITCH] == "1"


@pytest.mark.usefixtures("ambient_switch_off")
def test_batch_rebuild_child_is_controlled(monkeypatch: pytest.MonkeyPatch, spawned: list[dict[str, Any]]) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    from batch import batch_dispatcher_helpers as helpers

    monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)

    assert helpers.dispatch_claude_fix("a1", "greetings", 1, timeout=77)["success"] is True
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert call["argv"][call["argv"].index("--permission-mode") + 1] == "bypassPermissions"
    assert (call["timeout"], call["cwd"], call["capture_output"]) == (77, str(helpers.PROJECT_ROOT), True)


def test_batch_rebuild_timeout_is_still_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    from batch import batch_dispatcher_helpers as helpers

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    monkeypatch.setattr(helpers, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    result = helpers.dispatch_claude_fix("a1", "greetings", 1, timeout=3)
    assert (result["success"], result["returncode"], result["stdout_tail"]) == (False, -1, "TimeoutExpired")


@pytest.mark.usefixtures("ambient_switch_off")
def test_pipeline_phase_child_is_controlled_without_claudecode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, spawned: list[dict[str, Any]]
) -> None:
    from scripts.pipeline import dispatch

    monkeypatch.setattr(dispatch, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    monkeypatch.setenv("CLAUDECODE", "1")
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    ok, _ = dispatch.dispatch_claude_phase(prompt_file, "B content", timeout=44)

    assert ok
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert "CLAUDECODE" not in call["env"], "the pipeline's exclusion must survive the wrapper"
    assert call["env"]["LU_AMBIENT_PROBE"] == "ambient"
    assert (call["input"], call["timeout"]) == ("write the content", 44)


def test_pipeline_phase_stops_its_heartbeat_on_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.pipeline import dispatch

    threads: list[Any] = []

    class RecordedThread(dispatch.threading.Thread):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            threads.append(self)

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(dispatch.threading, "Thread", RecordedThread)
    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    monkeypatch.setattr(dispatch, "supports_exclude_dynamic_system_prompt_sections", lambda _bin: False)
    prompt_file = tmp_path / "phase.md"
    prompt_file.write_text("write the content", encoding="utf-8")

    assert dispatch.dispatch_claude_phase(prompt_file, "B content", timeout=1) == (False, "")
    (thread,) = threads
    assert not thread.is_alive(), "the heartbeat thread must stop when the run ends"


@pytest.mark.usefixtures("ambient_switch_off")
@pytest.mark.parametrize("module_name", ["code_review_benchmark", "judge_calibration_matrix"])
def test_native_claude_benchmark_child_is_controlled(
    monkeypatch: pytest.MonkeyPatch, module_name: str, spawned: list[dict[str, Any]]
) -> None:
    import importlib

    module = importlib.import_module(f"scripts.audit.{module_name}")
    cell = module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp")

    call = module.run_native_cli(cell, "prompt")

    assert call.ok
    (child,) = spawned
    _assert_child_controlled(child["argv"], child["env"])
    assert child["argv"][-2:] == ["--", "prompt"]
    assert list(call.cmd) == child["argv"], "telemetry records the argv the child received"
    assert (child["timeout"], child["cwd"]) == (module.REQUEST_TIMEOUT_S, str(module.PROJECT_ROOT))


@pytest.mark.parametrize("module_name", ["code_review_benchmark", "judge_calibration_matrix"])
def test_native_benchmark_timeout_and_other_providers_are_retained(
    monkeypatch: pytest.MonkeyPatch, module_name: str
) -> None:
    import importlib

    module = importlib.import_module(f"scripts.audit.{module_name}")
    direct: list[list[str]] = []

    def timed_out(argv: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    def other_provider(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert "env" not in kwargs
        direct.append(argv)
        return subprocess.CompletedProcess(argv, 0, stdout="verdict", stderr="")

    monkeypatch.setattr(claude_adapter.subprocess, "run", timed_out)
    call = module.run_native_cli(module.Cell("anthropic", "claude-opus-5-5", "native_cli", "high", "no_mcp"), "p")
    assert (call.ok, call.error) == (False, f"timed out after {module.REQUEST_TIMEOUT_S}s")

    monkeypatch.setattr(module.subprocess, "run", other_provider)
    assert module.run_native_cli(module.Cell("openai", "gpt-6.1-sol", "native_cli", "medium", "no_mcp"), "p").ok
    (argv,) = direct
    assert argv[0] == "codex" and "--disallowedTools" not in argv


@pytest.mark.usefixtures("ambient_switch_off")
def test_openai_proxy_claude_child_keeps_the_parent_env_exclusions(spawned: list[dict[str, Any]]) -> None:
    from scripts.ai_agent_bridge import openai_proxy as proxy

    response = proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="hello")])

    assert response.content == "out"
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    expected = {
        "TERM": "xterm-256color",
        "COLORTERM": "truecolor",
        **proxy._PARENT_ENV,
        SWITCH: "1",
        ADVISOR_SWITCH: "1",
    }
    assert call["env"] == expected, "the child gets _PARENT_ENV, never the ambient env"
    assert "LU_AMBIENT_PROBE" not in call["env"]
    assert "hello" in call["input"]
    assert call["timeout"] == proxy._backend_timeout_s()


def test_openai_proxy_claude_failure_is_still_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ai_agent_bridge import openai_proxy as proxy

    monkeypatch.setattr(
        claude_adapter.subprocess,
        "run",
        lambda argv, **kwargs: subprocess.CompletedProcess(argv, 3, stdout="", stderr="quota"),
    )
    with pytest.raises(subprocess.CalledProcessError) as raised:
        proxy._claude_backend("claude-opus-5-5", [proxy.Message(role="user", content="hello")])
    assert (raised.value.returncode, raised.value.stderr) == (3, "quota")


_ZNO_CONFIG = {
    "schema": "zno-nmt.config.v1",
    "adapter": "claude",
    "model": "local-test-model",
    "effort": None,
    "timeout_seconds": 15,
    "max_output_tokens": 100,
    "max_tool_calls": 2,
    "repeats": 1,
    "tools": ["verify_word"],
    "corpus_id": "fixture-corpus",
    "claude_bin": "claude-fixture",
}
_ZNO_PACKET = {
    "schema": "zno-nmt.questions.v1",
    "packet_sha256": "a" * 64,
    "items": [{"id": "opaque-1", "kind": "single", "question": "Q", "options": [{"id": "A", "text": "A"}], "rows": []}],
}


@pytest.mark.usefixtures("ambient_switch_off")
def test_zno_eval_claude_child_keeps_its_restricted_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.eval.zno_nmt import adapters

    seen: dict[str, Any] = {}
    stdout = "\n".join(
        [
            json.dumps({"type": "system", "subtype": "init", "model": "local-test-model", "tools": []}),
            json.dumps({"type": "result", "result": json.dumps({"responses": {"opaque-1": "A"}})}),
        ]
    )

    class FakePopen:
        def __init__(self, argv: list[str], **kwargs: Any) -> None:
            seen.update(argv=argv, **kwargs)
            self.pid = 0
            self.returncode = 0

        def communicate(self, prompt: str | None = None, timeout: float | None = None) -> tuple[str, str]:
            seen["input"] = prompt
            return stdout, ""

    monkeypatch.setattr(adapters, "_claude_capabilities", lambda *_args, **_kwargs: ("claude-fixture", "2.1.fixture"))
    monkeypatch.setattr(claude_adapter.subprocess, "Popen", FakePopen)

    result = adapters.run_claude(_ZNO_PACKET, _ZNO_CONFIG, "closed-book", sources_url=None, prompt="exam")

    assert result["responses"] == {"opaque-1": "A"}
    _assert_child_controlled(seen["argv"], seen["env"])
    assert seen["env"] == {
        **adapters._child_env(100),
        SWITCH: "1",
        ADVISOR_SWITCH: "1",
    }, "only the allowlisted env reaches the child"
    assert "LU_AMBIENT_PROBE" not in seen["env"]
    assert seen["argv"][seen["argv"].index("--tools") + 1] == ""
    assert seen["start_new_session"] is True
    assert seen["input"] == "exam"


def test_zno_eval_timeout_kills_the_process_group_and_drains(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from scripts.eval.zno_nmt import adapters

    seen: dict[str, Any] = {"drained": 0}

    class TimedOutProcess:
        pid = 321

        def communicate(self, _prompt: str | None = None, *, timeout: float | None = None) -> tuple[str, str]:
            if timeout is not None:
                raise subprocess.TimeoutExpired("claude", timeout)
            seen["drained"] += 1
            return "", ""

    monkeypatch.setattr(
        claude_adapter.subprocess, "Popen", lambda argv, **kwargs: seen.update(env=kwargs["env"]) or TimedOutProcess()
    )
    monkeypatch.setattr(adapters.os, "killpg", lambda pid, sig: seen.update(kill=(pid, sig)))

    with pytest.raises(adapters.AdapterError, match="timeout"):
        adapters._run_claude_process(["claude", "-p"], cwd=tmp_path, env={"PATH": "/bin"}, prompt="exam", timeout=1)
    assert seen["kill"] == (321, adapters.signal.SIGKILL)
    assert seen["drained"] == 1
    assert seen["env"] == {"PATH": "/bin", SWITCH: "1", ADVISOR_SWITCH: "1"}


@pytest.mark.usefixtures("ambient_switch_off")
def test_isolated_claude_review_spawn_is_controlled_and_keeps_the_reviewer_env(
    tmp_path: Path, spawned: list[dict[str, Any]]
) -> None:
    from scripts.review.isolation import build_claude_review_argv, run_claude_review

    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\n", encoding="utf-8")
    reviewer_env = {"HOME": "/h", "PATH": "/usr/bin", SWITCH: "0"}

    completed = run_claude_review(
        binary, prompt="review", json_schema={"type": "object"}, env=reviewer_env, timeout=30, cwd=tmp_path
    )

    assert completed.stdout == "out"
    (call,) = spawned
    _assert_child_controlled(call["argv"], call["env"])
    assert call["env"] == {
        "HOME": "/h",
        "PATH": "/usr/bin",
        SWITCH: "1",
        ADVISOR_SWITCH: "1",
    }, "only the reviewer env reaches the child"
    assert call["argv"] == build_claude_review_argv(binary, prompt="review", json_schema={"type": "object"})
    assert call["argv"][call["argv"].index("--tools") + 1] == "Read,Grep,Glob"
    assert call["argv"][-2:] == ["--", "review"]
    assert (call["timeout"], call["cwd"], call["capture_output"]) == (30, str(tmp_path), True)


def test_version_probe_runs_only_literal_version_argvs(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.utils import claude_version

    argvs: list[list[str]] = []
    monkeypatch.setattr(
        claude_version.subprocess,
        "run",
        lambda argv, **_kwargs: argvs.append(argv) or subprocess.CompletedProcess(argv, 0, "2.1.200", ""),
    )
    assert claude_version.run_version_probe(["/opt/claude"], timeout=1) is not None
    assert claude_version.run_version_probe(claude_version.CLAUDE_NPX_PREFIX, timeout=1) is not None
    assert claude_version.run_version_probe(["claude", "-p"], timeout=1) is None
    assert claude_version.run_version_probe(["npx", "other-package"], timeout=1) is None
    assert argvs == [["/opt/claude", "--version"], ["npx", "@anthropic-ai/claude-code@latest", "--version"]]
