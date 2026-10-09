"""Synthetic command-position regressions for issue #9490; no shell execution."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest


def _load_hook(name):
    source = Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks" / f"guard-{name}.py"
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


public = _load_hook("public-github-text")
reviewer = _load_hook("reviewer-publish")
primary = reviewer._shell_parser()

PREFIXES = [">sink", "> sink", "2>sink", "2>&1", "<f", "<f 2>&1 >sink", "&>sink", ">sink X=1 <f", "X=1 >sink"]


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("command", ["gh pr comment 1 --body ok", "env -i gh pr comment 1 --body ok"])
def test_public_text_sees_gh_after_redirect(prefix, command):
    assert public.invokes_gh(f"{prefix} {command}")


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize(
    "command,reason",
    [("gh pr comment 1 --body ok", "gh pr comment"), ("git push", "git push")],
)
def test_reviewer_blocks_publish_after_redirect(prefix, command, reason, monkeypatch, capsys):
    monkeypatch.setattr(reviewer, "_shell_parser", lambda: primary)
    payload = {"tool_name": "Bash", "tool_input": {"command": f"{prefix} {command}"}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    assert reviewer.main() == 2
    assert reason in capsys.readouterr().err


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("command", ["gh pr view 1", "git status"])
def test_reviewer_keeps_reads_available_after_redirect(prefix, command):
    assert reviewer.blocked(f"{prefix} {command}", primary) is None


@pytest.mark.parametrize("command", [">sink printf '%s' gh", "printf '%s' '>sink gh'", "<f printf '%s' gh"])
def test_redirect_operands_and_quoted_arguments_are_not_programs(command):
    assert not public.invokes_gh(command)
    assert reviewer.blocked(command, primary) is None


def test_public_text_installs_shim_after_redirect(monkeypatch, capsys):
    from scripts.opsec import prepublish

    command = ">sink gh pr comment 1 --body ok"
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setenv("PATH", "")
    monkeypatch.setattr(prepublish, "real_gh", lambda environment: "gh")
    assert public.main() == 0
    updated = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["updatedInput"]["command"]
    assert updated.startswith("export PATH=")
    assert updated.endswith(command)


@pytest.mark.parametrize("prefix", PREFIXES)
def test_nested_publish_after_redirect(prefix):
    command = f"{prefix} bash -c 'gh pr comment 1 --body ok'"
    assert public.invokes_gh(command)
    assert reviewer.blocked(command, primary) == "gh pr comment"


def test_redirect_between_program_and_publish_verb():
    assert reviewer.blocked("gh >sink pr comment 1 --body ok", primary) == "gh pr comment"
    assert reviewer.blocked("git >sink push", primary) == "git push"


@pytest.mark.parametrize("command", ["printf '%s' 'gh pr comment 1'", ">sink printf '%s' 'git push'"])
def test_quoted_publish_text_stays_inert(command):
    assert not public.invokes_gh(command)
    assert reviewer.blocked(command, primary) is None
