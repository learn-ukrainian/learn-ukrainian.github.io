"""Native decisions never execute candidate commands or disclose their values."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_guard_secret_print import (
    ROUND_FIVE_KEYED,
    ROUND_FIVE_SPELLINGS,
    ROUND_SIX_INVENTORY,
    ROUND_SIX_NEIGHBORS,
)

HARNESS_NAMES = ["claude", "codex", "grok", "kimi", "cursor", "agy", "hermes", "opencode"]
ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "scripts/agent_runtime/secret_print_hook.py"
SENTINEL = "synthetic_adapter_value_91b8"
NATIVE_ENV = {"PATH": "/usr/bin:/bin", "ARBITRARY_TOKEN": SENTINEL, "PYTHONDONTWRITEBYTECODE": "1"}


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("api,command", ROUND_SIX_INVENTORY, ids=[row[0] for row in ROUND_SIX_INVENTORY])
def test_native_round_six_inventory(harness, api, command):
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, command)),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, False)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("command", ROUND_SIX_NEIGHBORS)
def test_native_round_six_neighbors(harness, command):
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, command)),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, True)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("command", ROUND_FIVE_SPELLINGS)
def test_native_round_five_review_spellings(harness, command):
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, command)),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, False)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("consumer,program", ROUND_FIVE_KEYED)
@pytest.mark.parametrize("name,allowed", [("HOME", True), ("ARBITRARY_TOKEN", False)])
def test_native_round_five_literal_policy(harness, consumer, program, name, allowed):
    import shlex

    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, f"{consumer} --unknown {shlex.quote(program.format(name=name))}")),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, allowed)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize(
    "command",
    [
        "env > >(cat)",
        "bash <<'EOF'\nprintenv\nEOF",
        "export X=$ARBITRARY_TOKEN; cat <<EOF\n$X\nEOF",
        "python -c 'import os; print(os.environ)'",
        "base64 /proc/self/environ",
    ],
)
def test_native_structural_dump_denials(harness, command):
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, command)),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr
    assert_decision(harness, result.returncode, result.stdout, result.stderr, False)


def event(harness, command):
    if harness == "cursor":
        return {"hook_event_name": "beforeShellExecution", "command": command}
    if harness == "grok":
        return {"toolName": "run_terminal_command", "toolInput": {"command": command}}
    if harness == "agy":
        return {"toolCall": {"name": "run_command"}, "tool_input": {"command": command}}
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def assert_decision(harness, code, stdout, stderr, allowed):
    assert SENTINEL not in stdout + stderr
    assert code == (0 if allowed else 2)
    if harness in {"cursor", "agy"}:
        key = "permission" if harness == "cursor" else "decision"
        assert json.loads(stdout)[key] == ("allow" if allowed else "deny")
    else:
        assert stdout == ""
    if not allowed:
        assert "BLOCKED by guard-secret-print" in stderr


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("case", ["allow", "deny", "unparseable", "missing", "wrong_type"])
def test_native_cli_decisions(harness, case):
    command = 'echo "$HOME"' if case == "allow" else f'echo "$ARBITRARY_TOKEN"; echo {SENTINEL}'
    payload = event(harness, command)
    if case == "missing":
        payload = {}
    if case == "wrong_type":
        payload = event(harness, ["env"])
    raw = "{" + SENTINEL if case == "unparseable" else json.dumps(payload)
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness], input=raw, text=True, capture_output=True, timeout=10
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, case == "allow")


@pytest.mark.parametrize("harness", HARNESS_NAMES)
def test_native_timeout(harness, monkeypatch, capsys):
    from scripts.agent_runtime import secret_print_hook as hook

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event(harness, "env"))))
    code = hook.main(["--harness", harness, "--timeout", "0.000001"])
    captured = capsys.readouterr()
    assert_decision(harness, code, captured.out, captured.err, False)
    assert "deadline" in captured.err


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("failure", ["missing_guard", "launch", "crash", "stdout", "stderr"])
def test_native_guard_failures(harness, failure, monkeypatch, capsys, tmp_path):
    from scripts.agent_runtime import codex_hook_policy
    from scripts.agent_runtime import secret_print_hook as hook

    if failure == "missing_guard":
        monkeypatch.setattr(hook, "GUARD_PATH", tmp_path / "absent.py")
    else:

        def broken_run(*args, **kwargs):
            if failure == "launch":
                raise OSError(SENTINEL)
            return subprocess.CompletedProcess(
                args[0],
                1 if failure == "crash" else 0,
                SENTINEL if failure == "stdout" else "",
                SENTINEL if failure == "stderr" else "",
            )

        monkeypatch.setattr(codex_hook_policy.subprocess, "run", broken_run)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event(harness, f"env; echo {SENTINEL}"))))
    code = hook.main(["--harness", harness])
    captured = capsys.readouterr()
    assert_decision(harness, code, captured.out, captured.err, False)


@pytest.mark.parametrize("timed_out", [False, True])
def test_shared_runner_pins_guard_and_sanitizes_timeout(timed_out, monkeypatch):
    from scripts.agent_runtime import codex_hook_policy
    from scripts.agent_runtime import secret_print_hook as hook

    calls = []
    command = f'echo "{SENTINEL}"'

    def guard_process(argv, **kwargs):
        calls.append((argv, kwargs))
        if timed_out:
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"], output=SENTINEL, stderr=SENTINEL)
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(codex_hook_policy.subprocess, "run", guard_process)
    assert hook.run_guard(command, timeout=1.25) == (
        (False, "BLOCKED by guard-secret-print (#M-5): shared guard deadline exceeded.\n") if timed_out else (True, "")
    )
    assert calls == [
        (
            [sys.executable, str(ROOT / "agents_extensions/shared/hooks/guard-secret-print.py")],
            {
                "input": json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
                "text": True,
                "capture_output": True,
                "check": False,
                "timeout": 1.25,
            },
        )
    ]


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--harness", "unknown"],
        ["--harness", "cursor", "--timeout", "nan"],
        ["--harness", "agy", "--timeout", "inf"],
        ["--harness", "grok", "--timeout", "0"],
        ["--harness", "kimi", "--timeout", "6"],
    ],
)
def test_invalid_options_fail_closed(argv, monkeypatch, capsys):
    from scripts.agent_runtime import secret_print_hook as hook

    monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
    assert hook.main(argv) == 2
    assert SENTINEL not in "".join(capsys.readouterr())


def test_cli_help():
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--help"], text=True, capture_output=True, env=NATIVE_ENV, timeout=10
    )
    assert result.returncode == 0
    for term in ["--harness", "--timeout", "Outputs:", "Exit codes:", "Related:"]:
        assert term in result.stdout


@pytest.mark.parametrize("harness", HARNESS_NAMES)
def test_actual_guard_stderr_is_forwarded(harness, monkeypatch, capsys):
    from scripts.agent_runtime import secret_print_hook as hook

    command = 'echo "$ARBITRARY_TOKEN"'
    guard = subprocess.run(
        [sys.executable, str(hook.GUARD_PATH)],
        input=json.dumps(event("claude", command)),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event(harness, command))))
    assert hook.main(["--harness", harness]) == 2
    captured = capsys.readouterr()
    assert captured.err == guard.stderr


@pytest.mark.parametrize("harness", HARNESS_NAMES)
def test_denial_never_includes_candidate_filename(harness):
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "--harness", harness],
        input=json.dumps(event(harness, f"cat .env.{SENTINEL}")),
        text=True,
        capture_output=True,
        env=NATIVE_ENV,
        timeout=10,
    )
    assert_decision(harness, result.returncode, result.stdout, result.stderr, False)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
@pytest.mark.parametrize("payload", [None, [], {"tool_input": None}, {"command": ""}, {"tool_input": {"command": ""}}])
def test_malformed_event_objects(harness, payload, monkeypatch, capsys):
    from scripts.agent_runtime import secret_print_hook as hook

    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    code = hook.main(["--harness", harness])
    captured = capsys.readouterr()
    assert_decision(harness, code, captured.out, captured.err, False)


@pytest.mark.parametrize("harness", HARNESS_NAMES)
def test_unexpected_adapter_failure_denies(harness, monkeypatch, capsys):
    from scripts.agent_runtime import secret_print_hook as hook

    def broken_guard(*args, **kwargs):
        raise ImportError(SENTINEL)

    monkeypatch.setattr(hook, "run_guard", broken_guard)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(event(harness, "env"))))
    code = hook.main(["--harness", harness])
    captured = capsys.readouterr()
    assert_decision(harness, code, captured.out, captured.err, False)
