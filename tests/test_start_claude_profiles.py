"""Native Claude adapter profile and route-isolation regression tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.review.model_catalog import load_model_catalog
from tests.test_launcher_contract import run_launcher

pytestmark = pytest.mark.usefixtures("hermetic_monitor")


def _stub_claude(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "claude"
    binary.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'base=%s\\n' \"${ANTHROPIC_BASE_URL:-unset}\"\n"
        "printf 'max=%s\\n' \"${CLAUDE_CODE_MAX_CONTEXT_TOKENS:-unset}\"\n"
        "printf 'compact=%s\\n' \"${CLAUDE_CODE_AUTO_COMPACT_WINDOW:-unset}\"\n"
        "printf 'safe=%s\\n' \"${CLAUDE_CODE_SAFE_MODE:-unset}\"\n"
        "printf 'simple=%s\\n' \"${CLAUDE_CODE_SIMPLE:-unset}\"\n"
        "printf 'profile=%s\\n' \"${LEARN_UKRAINIAN_PROFILE_ID:-unset}\"\n"
        "printf 'args=%s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return bin_dir


def test_claude_interactive_keeps_tui_model_unless_explicit() -> None:
    default = run_launcher("start-claude.sh")
    fable = run_launcher("start-claude.sh", "--model", "fable")
    sonnet = run_launcher("start-claude.sh", "--model", "sonnet")
    assert default.returncode == sonnet.returncode == 0
    assert fable.returncode == 0
    assert "would exec claude --model" not in default.stdout
    assert "--effort" not in default.stdout
    assert "would exec claude " in default.stdout
    assert "would exec claude --model claude-fable-5-1" in fable.stdout
    assert "would exec claude --model claude-sonnet-5-5" in sonnet.stdout


def test_claude_interactive_injects_effort_when_explicit() -> None:
    result = run_launcher("start-claude.sh", "--effort", "high")
    assert result.returncode == 0, result.stderr
    assert "would exec claude --effort high" in result.stdout
    assert "would exec claude --model" not in result.stdout

    both = run_launcher("start-claude.sh", "--model", "fable", "--effort", "xhigh")
    assert both.returncode == 0, both.stderr
    assert "would exec claude --model claude-fable-5-1 --effort xhigh" in both.stdout

@pytest.mark.parametrize("model", ("not-certified", "gpt-6.1-sol"))
def test_claude_rejects_models_outside_native_profile(model: str) -> None:
    result = run_launcher("start-claude.sh", "--model", model)
    assert result.returncode == 2
    assert "profile" in result.stderr


def test_certified_claude_driver_models_are_revalidated() -> None:
    for model in ("opus", "fable", "sonnet"):
        result = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", model)
        assert result.returncode == 0, result.stderr
        assert "would claim lease" in result.stdout
    untrusted = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", "claude-haiku-5")
    assert untrusted.returncode == 4


def test_explicit_retired_sonnet_driver_pin_is_refused() -> None:
    result = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", "claude-sonnet-5")
    assert result.returncode == 2
    assert "would exec claude" not in result.stdout

@pytest.mark.parametrize("alias", ["fable-5", "opus-5"])
@pytest.mark.parametrize("script", ["start-claude.sh", "start-claude-driver.sh"])
def test_versioned_retired_claude_alias_is_refused(alias, script) -> None:
    args = ("--epic", "devops") if script == "start-claude-driver.sh" else ()
    result = run_launcher(script, *args, "--model", alias)
    assert result.returncode != 0
    assert "is retired in the model catalog" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would exec claude" not in result.stdout


def test_full_retired_fable_id_is_refused() -> None:
    retired = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", "claude-fable-5")
    assert retired.returncode != 0
    assert "would claim lease" not in retired.stdout
    assert "would exec claude" not in retired.stdout

@pytest.mark.parametrize(
    "model", [model_id for model_id, entry in load_model_catalog()["models"].items() if entry["lifecycle"] == "retired"]
)
@pytest.mark.parametrize("suffix", ["", "[1m]"])
@pytest.mark.parametrize("via_env", [False, True])
def test_interactive_launcher_refuses_every_retired_catalog_id(model, suffix, via_env) -> None:
    pin = model + suffix
    result = run_launcher(
        "start-claude.sh",
        *(() if via_env else ("--model", pin)),
        env={"LAUNCHER_MODEL": pin} if via_env else {},
    )
    assert result.returncode == 2
    assert "is retired in the model catalog" in result.stderr
    assert "would exec claude" not in result.stdout


OPUS_5_5_1M = "claude-opus-5-5\\[1m\\]"  # printf %q form of claude-opus-5-5[1m]


def test_claude_driver_defaults_to_opus_5_5_at_high() -> None:
    """Operator 2026-09-22: the Claude orchestrator seat is Opus 5.5 (1M) at high."""
    result = run_launcher("start-claude-driver.sh", "--epic", "devops")
    assert result.returncode == 0, result.stderr
    assert f"would exec claude --model {OPUS_5_5_1M} --effort high" in result.stdout


def test_claude_driver_default_yields_to_launcher_env() -> None:
    result = run_launcher(
        "start-claude-driver.sh",
        "--epic",
        "devops",
        env={"LAUNCHER_MODEL": "fable", "LAUNCHER_EFFORT": "medium"},
    )
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model claude-fable-5-1 --effort medium" in result.stdout


def test_claude_opus_aliases_resolve_to_5_5() -> None:
    for alias in ("opus", "opus-5-5", "opus-5.5", "claude-opus-5-5"):
        result = run_launcher("start-claude-driver.sh", "--epic", "devops", "--model", alias)
        assert result.returncode == 0, (alias, result.stderr)
        assert "would exec claude --model claude-opus-5-5" in result.stdout


def test_claude_interactive_does_not_inherit_driver_default() -> None:
    result = run_launcher("start-claude.sh")
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model" not in result.stdout
    assert "--effort" not in result.stdout

@pytest.mark.parametrize(
    "argv",
    (
        ("--effort", "xhigh", "--epic", "devops"),
        ("--effort=xhigh", "--epic", "devops"),
        ("--epic", "devops", "--effort", "xhigh"),
    ),
)
def test_claude_driver_accepts_effort_before_or_after_epic(argv: tuple[str, ...]) -> None:
    result = run_launcher("start-claude-driver.sh", *argv)
    assert result.returncode == 0, result.stderr
    assert f"would exec claude --model {OPUS_5_5_1M} --effort xhigh" in result.stdout


def test_claude_driver_injects_model_and_effort_when_explicit() -> None:
    result = run_launcher(
        "start-claude-driver.sh",
        "--epic",
        "devops",
        "--model",
        "fable",
        "--effort",
        "high",
    )
    assert result.returncode == 0, result.stderr
    assert "would exec claude --model claude-fable-5-1 --effort high" in result.stdout


def test_claude_rejects_unknown_effort() -> None:
    result = run_launcher("start-claude.sh", "--effort", "ludicrous")
    assert result.returncode == 2
    assert "effort" in result.stderr.lower()


def test_native_claude_clears_foreign_route_and_capacity_overrides(tmp_path: Path) -> None:
    bin_dir = _stub_claude(tmp_path)
    result = run_launcher(
        "start-claude.sh",
        env={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "ANTHROPIC_BASE_URL": "https://foreign.invalid",
            "ANTHROPIC_AUTH_TOKEN": "foreign-secret",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "123",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "122",
            "CLAUDE_CODE_SAFE_MODE": "1",
            "CLAUDE_CODE_SIMPLE": "1",
        },
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    assert "base=unset" in result.stdout
    assert "max=unset" in result.stdout
    assert "compact=unset" in result.stdout
    assert "safe=unset" in result.stdout
    assert "simple=unset" in result.stdout
    assert "profile=native_claude" in result.stdout
    assert "foreign-secret" not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "launcher,args",
    [("start-claude.sh", ()), ("start-claude-driver.sh", ("--epic", "devops"))],
)
@pytest.mark.parametrize("inherited", [False, True])
def test_interactive_launcher_installs_guard_despite_inherited_markers(launcher, args, inherited):
    env = {
        "CODEX_SESSION": "1", "LEARN_UKRAINIAN_DISPATCH_TASK_ID": "parent-worker",
        "CLAUDE_NON_INTERACTIVE": "1", "LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH": "1",
        "LEARN_UKRAINIAN_GLMCC_MANAGED_LAUNCH": "1",
    } if inherited else {}
    result = run_launcher(launcher, *args, env=env)
    assert result.returncode == 0, result.stderr
    assert "--settings" in result.stdout
    assert "agents_extensions/shared/settings/driver-compaction-guard.json" in result.stdout
    assert "Never compact a Claude driver" in result.stdout.replace("\\ ", " ")
    assert "HANDOFF-DONE" in result.stdout

@pytest.mark.parametrize("flag", ["-p", "--print", "--print=true", "-cp", "-pc", "-ccpp"])
def test_print_mode_launcher_omits_driver_guard(flag):
    result = run_launcher("start-claude.sh", "--", flag, "inspect")
    assert result.returncode == 0, result.stderr
    assert "--settings" not in result.stdout
    assert "driver-compaction-guard" not in result.stdout
    assert "HANDOFF-DONE" not in result.stdout


REFUSED_FORWARD_ARGS = [
    ("--settings", "private-value"), ("--settings=private-value",),
    ("--settings", '{"disableAllHooks":true}'),
    ("--bare",), ("--bare=true",), ("--safe-mode",), ("--safe-mode=true",),
    ("--setting-sources", "private-value"), ("--setting-sources=private-value",),
    ("--managed-settings", "private-value"), ("--managed-settings=private-value",),
    ("--client-data-url", "private-value"), ("--client-data-url=private-value",),
    ("--project-config-root", "private-value"), ("--project-config-root=private-value",),
    ("--restricted",), ("--desktop",), ("--cloud",), ("--environment", "private-value"),
    ("--bg",), ("--background",), ("--worktree",), ("-w",), ("--tmux",),
    ("--disable-hooks",), ("--no-hooks",), ("--future-option", "private-value"),
    ("--set", "private-value"), ("--sett=private-value",), ("--bar",), ("--safe",),
    ("-b",), ("-bc",), ("--settings\nprivate-value",),
    ("attach", "private-value"), ("agents",), ("remote-control",),
]


@pytest.mark.parametrize("launcher,args", [
    ("start-claude.sh", ()), ("start-claude-driver.sh", ("--epic", "devops")),
])
@pytest.mark.parametrize("forwarded", REFUSED_FORWARD_ARGS)
def test_interactive_forwarding_refuses_unaudited_arguments(launcher, args, forwarded):
    result = run_launcher(launcher, *args, "--", *forwarded)
    assert result.returncode == 2, result.stderr
    assert "refused in interactive Claude" in result.stderr
    assert "preserve launcher settings and compaction hooks" in result.stderr
    if "\n" not in forwarded[0]:
        assert forwarded[0].split("=", 1)[0] in result.stderr
    assert "private-value" not in result.stdout + result.stderr
    assert "disableAllHooks" not in result.stdout + result.stderr
    assert "would exec claude" not in result.stdout
    assert "would claim lease" not in result.stdout
    assert "would run provider canary" not in result.stdout


@pytest.mark.parametrize("forwarded", [
    ("--model", "opus"), ("--model=opus",),
    ("--effort", "high"), ("--effort=high",),
    ("--resume",), ("--resume", "session"), ("--resume=session",),
    ("-r",), ("-r", "session"), ("--continue",), ("-c",),
    ("--append-system-prompt", "fixture prompt"), ("--append-system-prompt=fixture",),
    ("--append-system-prompt-file", "fixture.txt"), ("--append-system-prompt-file=fixture.txt",),
    ("--agent", "infra-orchestrator"), ("--agent=infra-orchestrator",),
    ("--session-id", "session"), ("--session-id=session",),
    ("--name", "fixture"), ("--name=fixture",), ("-n", "fixture"),
    ("--permission-mode", "plan"), ("--permission-mode=plan",),
    ("--debug",), ("--debug", "hooks"), ("--debug=hooks",), ("-d",), ("-d", "hooks"),
    ("--fork-session",), ("--verbose",), ("--dangerously-skip-permissions",),
    ("--allow-dangerously-skip-permissions",), ("--help",), ("-h",),
    ("--version",), ("-v",), ("fixture prompt",),
    ("--", "--settings", "fixture"), ("--", "--print"), ("--", "attach"),
    ("fixture --print prose",),
    ("--resume", "abc"), ("--append-system-prompt", "extra"),
    ("-r", "abc", "--fork-session"),
])
@pytest.mark.parametrize("launcher,args", [
    ("start-claude.sh", ()), ("start-claude-driver.sh", ("--epic", "devops")),
])
def test_audited_interactive_forwarding_preserves_guard(launcher, args, forwarded):
    result = run_launcher(launcher, *args, "--", *forwarded)
    assert result.returncode == 0, result.stderr
    assert "driver-compaction-guard.json" in result.stdout
    assert "would exec claude" in result.stdout


@pytest.mark.parametrize("forwarded", [
    ("--settings", "fixture", "-p", "inspect"),
    ("--settings=fixture", "--print", "inspect"),
    ("--setting-sources", "", "-p", "inspect"),
    ("--managed-settings", "{}", "--print", "inspect"),
    ("-p", "--future-headless-option", "inspect"),
    ("--mcp-config", "{}", "{}", "-p", "inspect"),
    ("--resume", "session", "--print", "inspect"),
])
def test_headless_forwarding_retains_native_settings_behavior(forwarded):
    result = run_launcher("start-claude.sh", "--", *forwarded)
    assert result.returncode == 0, result.stderr
    assert "driver-compaction-guard" not in result.stdout
    assert "HANDOFF-DONE" not in result.stdout


@pytest.mark.parametrize("forwarded", [
    ("--settings", "--print"), ("--managed-settings", "--print"),
    ("--client-data-url", "-p"), ("--project-config-root", "--print"),
    ("--append-system-prompt", "--print", "--bare"),
    ("--append-system-prompt", "-p", "--settings=private-value"),
    ("--unknown", "--print"),
])
def test_option_values_cannot_hide_interactive_settings_bypass(forwarded):
    result = run_launcher("start-claude.sh", "--", *forwarded)
    assert result.returncode == 2, result.stderr
    assert "would exec claude" not in result.stdout
    assert "private-value" not in result.stdout + result.stderr


CLAUDE_LAUNCH_FORMS = [
    ("start-claude.sh", ("--",)),
    ("start-claude-driver.sh", ("--epic", "devops")),
    ("start-claude-driver.sh", ("--epic", "devops", "--")),
]
HOOK_DISABLING_FLAGS = ["--bare", "--safe-mode", "--bg", "--background"]
AUDITED_REQUIRED_VALUE_FLAGS = [
    "--model", "--effort", "--append-system-prompt", "--append-system-prompt-file",
    "--agent", "--session-id", "--name", "-n", "--permission-mode",
]


@pytest.mark.parametrize("launcher,args", CLAUDE_LAUNCH_FORMS)
def test_malformed_delimiter_does_not_end_argument_validation(launcher, args):
    result = run_launcher(launcher, *args, "--=private-value", "--settings", "private-value")
    assert result.returncode == 2, result.stderr
    assert "unrecognized option" in result.stderr
    assert "private-value" not in result.stdout + result.stderr
    assert "would claim lease" not in result.stdout
    assert "would run provider canary" not in result.stdout
    assert "would exec claude" not in result.stdout


@pytest.mark.parametrize("launcher,args", CLAUDE_LAUNCH_FORMS)
@pytest.mark.parametrize("flag", ["--name", "-n", "--append-system-prompt", "--agent", "--session-id"])
@pytest.mark.parametrize("value", [value + suffix for value in HOOK_DISABLING_FLAGS for suffix in ("", "=true")])
@pytest.mark.parametrize("equals", [False, True])
def test_hook_disabling_option_values_refused_before_side_effects(launcher, args, flag, value, equals):
    forwarded = (f"{flag}={value}",) if equals else (flag, value)
    result = run_launcher(launcher, *args, *forwarded)
    assert result.returncode == 2, result.stderr
    assert "preserve launcher settings and compaction hooks" in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would run provider canary" not in result.stdout
    assert "would exec claude" not in result.stdout


@pytest.mark.parametrize("launcher,args", CLAUDE_LAUNCH_FORMS)
@pytest.mark.parametrize("flag", HOOK_DISABLING_FLAGS)
@pytest.mark.parametrize("suffix", ["", "=true", "=false"])
@pytest.mark.parametrize("headless", [False, True])
def test_raw_hook_disabling_flags_refused_before_client_delimiter(launcher, args, flag, suffix, headless):
    # Inspect the entire raw prefix, including tokens hidden in option values
    # or following a positional prompt, independently of print-mode parsing.
    result = run_launcher(launcher, *args, "prompt", flag + suffix, *(("-p", "hi") if headless else ()))
    assert result.returncode == 2, result.stderr
    assert flag in result.stderr
    assert "would claim lease" not in result.stdout
    assert "would run provider canary" not in result.stdout
    assert "would exec claude" not in result.stdout


@pytest.mark.parametrize("flag", AUDITED_REQUIRED_VALUE_FLAGS)
@pytest.mark.parametrize("equals", [False, True])
@pytest.mark.parametrize("value", ["--print", "-p", "-private-value"])
def test_required_option_values_cannot_start_with_dash(flag, equals, value):
    forwarded = (f"{flag}={value}",) if equals else (flag, value)
    result = run_launcher("start-claude.sh", "--", *forwarded)
    assert result.returncode == 2, result.stderr
    assert "would exec claude" not in result.stdout
    assert "private-value" not in result.stdout + result.stderr


@pytest.mark.parametrize("flag", ["--resume", "-r", "--debug", "-d", "--mcp-config", "--settings"])
def test_explicit_values_for_optional_and_variadic_flags_cannot_start_with_dash(flag):
    result = run_launcher("start-claude.sh", "--", f"{flag}=-private-value", "-p", "hi")
    assert result.returncode == 2, result.stderr
    assert "would exec claude" not in result.stdout
    assert "private-value" not in result.stdout + result.stderr


@pytest.mark.parametrize("flag", AUDITED_REQUIRED_VALUE_FLAGS)
def test_required_option_value_cannot_be_missing_or_client_delimiter(flag):
    for trailing in [(), ("--", "--safe-mode")]:
        result = run_launcher("start-claude.sh", "--", flag, *trailing)
        assert result.returncode == 2, result.stderr
        assert "would exec claude" not in result.stdout


@pytest.mark.parametrize("launcher,args", CLAUDE_LAUNCH_FORMS)
@pytest.mark.parametrize("flag", HOOK_DISABLING_FLAGS)
@pytest.mark.parametrize("suffix", ["", "=true"])
def test_client_delimiter_preserves_hook_disabling_prompt_text(launcher, args, flag, suffix):
    # A direct driver form still needs the launcher delimiter before it can
    # pass a literal client delimiter. They are distinct argument boundaries.
    if args[-1] != "--":
        args = (*args, "--")
    result = run_launcher(launcher, *args, "--", flag + suffix)
    assert result.returncode == 0, result.stderr
    assert "driver-compaction-guard.json" in result.stdout
    assert f" -- {flag + suffix}" in result.stdout


@pytest.mark.parametrize("launcher,args", CLAUDE_LAUNCH_FORMS)
def test_legitimate_print_mode_still_launches(launcher, args):
    result = run_launcher(launcher, *args, "-p", "hi")
    assert result.returncode == 0, result.stderr
    assert "would exec claude" in result.stdout
    assert "driver-compaction-guard" not in result.stdout


@pytest.mark.parametrize("mode,args", [("interactive", ()), ("driver", ("--epic", "devops"))])
@pytest.mark.parametrize("variable", ["CLAUDE_CODE_SAFE_MODE", "CLAUDE_CODE_SIMPLE"])
def test_claude_dry_run_clears_inherited_hook_disabling_environment(mode, args, variable):
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["bash", "-c", '\n'.join([
            'source scripts/lib/launcher_core.sh',
            # Observe the environment at the dry-run client boundary.
            'launcher_print_argv() { printf "safe=%s simple=%s\\n" "${CLAUDE_CODE_SAFE_MODE-unset}" "${CLAUDE_CODE_SIMPLE-unset}"; }',
            'launcher_main claude "$@"',
        ]), "--", mode, *args],
        cwd=repo, env={**os.environ, variable: "1", "LAUNCHER_DRY_RUN": "1"},
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "would exec safe=unset simple=unset" in result.stdout


AUDITED_REFUSED_SCALAR_FLAGS = [
    "--settings", "--setting-sources", "--managed-settings", "--client-data-url",
    "--project-config-root", "--debug-file", "--output-format", "--json-schema", "--input-format",
    "--thinking", "--thinking-display", "--max-thinking-tokens", "--max-turns", "--max-budget-usd",
    "--task-budget", "--permission-prompt-tool", "--permission-prompts", "--system-prompt",
    "--system-prompt-file", "--system-prompt-snapshot", "--append-subagent-system-prompt",
    "--append-subagent-system-prompt-file", "--plan-mode-instructions",
    "--inherit-permission-mode", "--watch-artifact", "--watch-artifact-no-autoreact", "--prefill",
    "--deep-link-repo", "--deep-link-last-fetch", "--prefill-b64", "--deep-link-cwd-b64",
    "--resume-session-at", "--resume-drops-turn", "--rewind-files", "--fallback-model",
    "--workload", "--agents", "--plugin-dir", "--plugin-dir-no-mcp", "--plugin-url",
    "--autocompact", "--environment", "--from-pr", "--prompt-suggestions", "--cloud", "--teleport",
    "--worktree", "-w", "--tmux", "--allowedTools", "--allowed-tools", "--tools",
    "--disallowedTools", "--disallowed-tools", "--mcp-config", "--betas", "--add-dir", "--file",
]
AUDITED_REFUSED_BOOLEAN_FLAGS = [
    "--bare", "--safe-mode", "--restricted", "--init", "--init-only", "--maintenance",
    "--include-hook-events", "--include-partial-messages", "--forward-subagent-text",
    "--session-mirror", "--await-claim", "--await-initialize", "--replay-user-messages",
    "--enable-auth-status", "--exclude-dynamic-system-prompt-sections", "--deep-link-origin",
    "--no-session-persistence", "--reply-on-resume", "--ide", "--desktop", "--strict-mcp-config",
    "--disable-slash-commands", "--chrome", "--no-chrome", "--bg", "--background", "--brief",
    "--ax-screen-reader",
]


@pytest.mark.parametrize("forwarded", [
    *REFUSED_FORWARD_ARGS,
    *((flag, "private-value") for flag in AUDITED_REFUSED_SCALAR_FLAGS),
    *((flag + "=private-value",) for flag in AUDITED_REFUSED_SCALAR_FLAGS if flag.startswith("--")),
    *((flag,) for flag in AUDITED_REFUSED_BOOLEAN_FLAGS),
])
def test_adapter_refuses_before_provider_exec(forwarded):
    import subprocess

    adapter = Path(__file__).resolve().parents[1] / "scripts/launchers/claude.sh"
    result = subprocess.run(
        ["bash", "-c", '\n'.join([
            'source "$1"; LC_ROOT="$2"; shift 2',
            'LC_FORWARD_ARGS=("$@"); LC_MODEL=""; LC_EFFORT=""; LC_RULES_CORE=""; LC_DRY_RUN=0',
            'launcher_error() { printf "%s\\n" "$*" >&2; }',
            'launcher_exec_command() { echo UNEXPECTED_LAUNCH; }',
            'launcher_adapter_exec',
        ]), "--", os.fspath(adapter), os.fspath(adapter.parents[2]), *forwarded],
        capture_output=True, text=True, check=False, timeout=10, cwd=adapter.parents[2],
    )
    assert result.returncode == 2, result.stderr
    assert "refused in interactive Claude" in result.stderr
    assert "UNEXPECTED_LAUNCH" not in result.stdout
    assert "private-value" not in result.stdout + result.stderr

@pytest.mark.parametrize("forwarded", [(), ("--", "--settings", "fixture.json", "--bare", "--safe-mode")])
@pytest.mark.parametrize(
    "launcher,args,credentials",
    [
        ("start-codex.sh", ("--harness", "claude-code"), {}),
        ("start-kimi.sh", ("--harness", "claude-code"), {"KIMICC_AUTH_TOKEN": "test-key"}),
        ("start-glmcc.sh", (), {"GLMCC_AUTH_TOKEN": "test-key"}),
    ],
)
def test_other_model_launchers_omit_claude_driver_guard(tmp_path, launcher, args, credentials, forwarded):
    result = run_launcher(launcher, *args, *forwarded, env={"HOME": os.fspath(tmp_path / "home"), **credentials})
    assert result.returncode == 0, result.stderr
    assert "would exec claude" in result.stdout
    assert result.stdout.count("--settings") == (1 if forwarded else 0)
    if forwarded:
        assert "--settings fixture.json --bare --safe-mode" in result.stdout
    assert "driver-compaction-guard" not in result.stdout

@pytest.mark.parametrize("failure", ["missing", "directory", "unreadable"])
def test_interactive_adapter_refuses_unavailable_fragment(tmp_path, failure):
    import subprocess

    fragment = tmp_path / "agents_extensions/shared/settings/driver-compaction-guard.json"
    fragment.parent.mkdir(parents=True)
    if failure == "directory":
        fragment.mkdir()
    elif failure == "unreadable":
        fragment.write_text("{}")
        fragment.chmod(0)
    adapter = Path(__file__).resolve().parents[1] / "scripts/launchers/claude.sh"
    result = subprocess.run(
        ["bash", "-c", '\n'.join([
            'source "$1"',
            'LC_ROOT="$2"; LC_MODEL=""; LC_EFFORT=""; LC_RULES_CORE=""; LC_FORWARD_ARGS=(); LC_DRY_RUN=0',
            # The launcher uses [, so intercept only its readability check.
            '[() { if builtin [ "$1" = "-r" ]; then return 1; fi; builtin [ "$@"; }' if failure == "unreadable" else ':',
            'launcher_error() { printf "%s\\n" "$*" >&2; }',
            'launcher_exec_command() { echo UNEXPECTED_LAUNCH; }',
            'launcher_adapter_exec',
        ]), "--", os.fspath(adapter), os.fspath(tmp_path)],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert result.returncode == 2, result.stderr
    assert "missing or unreadable" in result.stderr
    assert "UNEXPECTED_LAUNCH" not in result.stdout
