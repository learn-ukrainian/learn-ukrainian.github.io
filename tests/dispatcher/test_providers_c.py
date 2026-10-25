"""Provider C contracts, exercised through local executables without inference."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.dispatcher.providers import hermes, load, muse, opencode
from scripts.dispatcher.types import ParsedResult, TaskSpec


def ndjson(*events: object) -> str:
    return "\n".join(json.dumps(event) for event in events)


def muse_event(kind: str, **payload: object) -> dict:
    return {"payload_type": kind, "payload": payload}


def opencode_event(kind: str, **part: object) -> dict:
    return {"type": kind, "part": part}


@pytest.fixture
def spec(tmp_path: Path) -> TaskSpec:
    workspace = tmp_path / "public workspace"
    workspace.mkdir()
    prompt = tmp_path / "prompt file.txt"
    prompt.write_text("Reply 'ready'.\nKeep $HOME and --literal unchanged. Привіт!\n", encoding="utf-8")
    return TaskSpec(
        "provider-c", "muse", "muse-wonder-full-1.0", "high", "read-only", workspace, prompt, tmp_path / "final.txt"
    )


@pytest.fixture
def stub_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir()
    script = (
        f"#!{sys.executable}\n"
        + """import json, os, pathlib, sys
args = sys.argv[1:]
prompt = None
if "--prompt-file" in args:
    prompt = pathlib.Path(args[args.index("--prompt-file") + 1]).read_text(encoding="utf-8")
elif "--" in args:
    prompt = args[args.index("--") + 1]
elif "-z" in args:
    prompt = args[args.index("-z") + 1]
pathlib.Path(os.environ["CAPTURE"]).write_text(json.dumps({
    "argv": args, "prompt": prompt, "cwd": os.getcwd(), "stdin": sys.stdin.read(),
    "marker": os.environ.get("PROVIDER_MARKER"),
}), encoding="utf-8")
print(os.environ.get("STUB_STDOUT", ""))
print(os.environ.get("STUB_STDERR", ""), file=sys.stderr)
sys.exit(int(os.environ.get("STUB_EXIT", "0")))
"""
    )
    for name in ("muse", "opencode", "hermes"):
        executable = bindir / name
        executable.write_text(script, encoding="utf-8")
        executable.chmod(0o700)
    return {"PATH": str(bindir), "CAPTURE": str(tmp_path / "capture.json"), "PROVIDER_MARKER": "kept"}


def execute(provider, task: TaskSpec, env: dict[str, str]) -> tuple[ParsedResult, dict]:
    original = env.copy()
    invocation = provider.build(task, env)
    assert env == original
    assert invocation.env == env
    assert invocation.final_file is None
    assert invocation.stdin is None
    run = subprocess.run(
        invocation.argv,
        input=invocation.stdin or b"",
        cwd=task.worktree,
        env=invocation.env,
        capture_output=True,
        timeout=10,
        check=False,
    )
    result = provider.parse(run.stdout.decode(), run.stderr.decode(), run.returncode, None)
    capture = json.loads(Path(env["CAPTURE"]).read_text(encoding="utf-8"))
    assert capture["cwd"] == str(task.worktree)
    assert capture["prompt"] == task.prompt_file.read_text(encoding="utf-8")
    assert capture["stdin"] == ""
    assert capture["marker"] == "kept"
    return result, capture


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("model", ["muse-spark-1.3", "muse-wonder-1.0", "muse-wonder-full-1.0"])
@pytest.mark.parametrize("contributor", [None, "on"])
def test_muse_argv_prompt_file_and_success(spec, stub_env, mode, model, contributor):
    task = replace(
        spec, mode=mode, model=model, options={} if contributor is None else {"contributor_mode": contributor}
    )
    stub_env["STUB_STDOUT"] = ndjson(muse_event("run.terminal.completed", terminal="completed", text="ready"))
    result, capture = execute(muse, task, stub_env)
    argv = [
        "exec",
        "--json",
        "--model",
        model,
        "--workspace",
        str(task.worktree),
        "--worktree",
        "off",
        "--prompt-file",
        str(task.prompt_file),
        "--contributor-mode",
        contributor or "off",
        "--no-foreign-personal-context",
        "--reasoning-effort",
        "high",
    ]
    argv += ["--yolo"] if mode == "workspace-write" else ["--permission-profile", ":read-only", "--disable-shell"]
    assert capture["argv"] == argv
    assert result == ParsedResult("ready", None, None)


def test_muse_optional_effort_and_explicit_contributor_off(spec, stub_env):
    task = replace(spec, effort=None, options={"contributor_mode": "off"})
    stub_env["STUB_STDOUT"] = ndjson(muse_event("run.terminal.completed", text="ready"))
    result, capture = execute(muse, task, stub_env)
    assert "--reasoning-effort" not in capture["argv"]
    assert capture["argv"][capture["argv"].index("--contributor-mode") + 1] == "off"
    assert result.text == "ready"


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_opencode_argv_argument_prompt_and_success(spec, stub_env, mode):
    task = replace(spec, agent="opencode", model="deepseek/deepseek-flash", mode=mode)
    stub_env["STUB_STDOUT"] = ndjson(opencode_event("text", text="ready"), opencode_event("step_finish", reason="stop"))
    result, capture = execute(opencode, task, stub_env)
    argv = ["run", "--model", "deepseek/deepseek-flash", "--format", "json", "--variant", "high"]
    if mode == "workspace-write":
        argv.append("--auto")
    assert capture["argv"] == [*argv, "--", task.prompt_file.read_text(encoding="utf-8")]
    assert result == ParsedResult("ready", None, None)


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
@pytest.mark.parametrize("model", ["vendor/model-a", "vendor/model-b"])
def test_hermes_explicit_model_argument_prompt_and_ansi_response(spec, stub_env, mode, model):
    task = replace(spec, agent="hermes", provider="openrouter", model=model, mode=mode)
    stub_env["STUB_STDOUT"] = "\x1b[32mready\x1b[0m"
    result, capture = execute(hermes, task, stub_env)
    assert capture["argv"] == [
        "-z",
        task.prompt_file.read_text(encoding="utf-8"),
        "-m",
        model,
        "--provider",
        "openrouter",
    ]
    assert result == ParsedResult("ready", None, None)


def test_hermes_missing_explicit_model_cannot_activate_default_qwen(spec):
    with pytest.raises(ValueError, match="explicit model"):
        hermes.build(replace(spec, model=" "), {})


@pytest.mark.parametrize(
    ("provider", "stdout"),
    [
        (muse, ndjson(muse_event("run.terminal.completed", text="ready"))),
        (opencode, ndjson(opencode_event("text", text="ready"), opencode_event("step_finish", reason="stop"))),
        (hermes, "ready"),
    ],
)
def test_nonzero_exit_overrides_reassuring_text(provider, stdout, spec, stub_env):
    stub_env.update(STUB_STDOUT=stdout, STUB_EXIT="7", STUB_STDERR="provider failed")
    result, _ = execute(provider, spec, stub_env)
    assert result.text is None
    assert result.error and "7" in result.error


@pytest.mark.parametrize("terminal", ["failed", "cancelled", "unknown"])
def test_muse_terminal_failure_is_sticky(terminal):
    stream = ndjson(
        muse_event("run.terminal." + terminal, reason="failure"), muse_event("run.terminal.completed", text="ready")
    )
    assert muse.parse(stream, "", 0, "ready").error


@pytest.mark.parametrize(
    "payload", [None, {}, {"text": "ready", "terminal": "failed"}, {"text": "ready", "reason": "aborted"}, {"text": 12}]
)
def test_muse_invalid_terminal_cannot_supply_success(payload):
    assert muse.parse(ndjson({"payload_type": "run.terminal.completed", "payload": payload}), "", 0, None).error


def test_muse_optional_usage_and_unknown_informational_events():
    usage = {"input_tokens": 3, "output_tokens": 1}
    stream = ndjson(
        muse_event("new.informational.event", note="ignored"),
        [],
        muse_event("run.usage", **usage),
        muse_event("run.terminal.completed", text="ready"),
    )
    assert muse.parse(stream, "warning", 0, None) == ParsedResult("ready", usage, None)


@pytest.mark.parametrize("reason", ["length", "error", "cancelled", "permission_denied", "unknown", "new_terminal"])
def test_opencode_unsuccessful_finish_cannot_become_success(reason):
    stream = ndjson(opencode_event("text", text="ready"), opencode_event("step_finish", reason=reason))
    assert opencode.parse(stream, "", 0, "ready").error
    stream += "\n" + ndjson(opencode_event("text", text="ready"), opencode_event("step_finish", reason="stop"))
    assert opencode.parse(stream, "", 0, None).error


@pytest.mark.parametrize(
    "event",
    [
        {"type": "error", "error": {"name": "APIError"}},
        {"type": "new_event", "error": "failed"},
        opencode_event("tool", state={"status": "permission_rejected"}),
    ],
)
def test_opencode_terminal_error_is_sticky(event):
    stream = ndjson(event, opencode_event("text", text="ready"), opencode_event("step_finish", reason="stop"))
    assert opencode.parse(stream, "", 0, None).error


def test_opencode_last_assistant_turn_chunks_and_optional_usage():
    stream = ndjson(
        opencode_event("text", text="I will inspect files"),
        opencode_event("tool", tool="read"),
        opencode_event("step_finish", reason="tool-calls"),
        opencode_event("step_start"),
        opencode_event("text", text="rea"),
        {"type": "new.info", "error": None},
        opencode_event("text", text="dy"),
        opencode_event("step_finish", reason="stop", tokens={"input": 5}),
    )
    assert opencode.parse(stream, "", 0, None) == ParsedResult("ready", {"input": 5}, None)


@pytest.mark.parametrize("provider", [muse, opencode, hermes])
def test_missing_final_response_does_not_use_unrelated_final_file(provider):
    assert provider.parse("", "", 0, "ready").error


@pytest.mark.parametrize("stream", ["garbage", ndjson({"type": "new.info"}), ndjson([], None)])
@pytest.mark.parametrize("provider", [muse, opencode])
def test_non_response_json_or_noise_cannot_supply_success(provider, stream):
    assert provider.parse(stream, "", 0, None).error


def test_opencode_text_without_final_outcome_is_incomplete():
    assert opencode.parse(ndjson(opencode_event("text", text="ready")), "", 0, None).error


def test_hermes_zero_exit_http_error_is_failure():
    assert hermes.parse("\x1b[31mHTTP 429: quota exceeded\x1b[0m", "", 0, None).error


@pytest.mark.parametrize("name", ["muse", "opencode", "hermes"])
def test_registry_loads_provider_c(name):
    assert load(name).__name__ == f"scripts.dispatcher.providers.{name}"
