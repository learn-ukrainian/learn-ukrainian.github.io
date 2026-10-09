"""Native Claude adapter profile and route-isolation regression tests."""

from __future__ import annotations

import os
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
        },
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    assert "base=unset" in result.stdout
    assert "max=unset" in result.stdout
    assert "compact=unset" in result.stdout
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

@pytest.mark.parametrize("flag", ["-p", "--print", "--print=true"])
def test_print_mode_launcher_omits_driver_guard(flag):
    result = run_launcher("start-claude.sh", "--", flag, "inspect")
    assert result.returncode == 0, result.stderr
    assert "--settings" not in result.stdout
    assert "driver-compaction-guard" not in result.stdout
    assert "HANDOFF-DONE" not in result.stdout

@pytest.mark.parametrize(
    "launcher,args,credentials",
    [
        ("start-codex.sh", ("--harness", "claude-code"), {}),
        ("start-kimi.sh", ("--harness", "claude-code"), {"KIMICC_AUTH_TOKEN": "test-key"}),
        ("start-glmcc.sh", (), {"GLMCC_AUTH_TOKEN": "test-key"}),
    ],
)
def test_other_model_launchers_omit_claude_driver_guard(tmp_path, launcher, args, credentials):
    result = run_launcher(launcher, *args, env={"HOME": os.fspath(tmp_path / "home"), **credentials})
    assert result.returncode == 0, result.stderr
    assert "would exec claude" in result.stdout
    assert "--settings" not in result.stdout
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
