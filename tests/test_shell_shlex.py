"""Shared shell preprocessing cases for executable substitution boundaries."""

from __future__ import annotations

import pytest

from agents_extensions.shared.hooks.shell_shlex import (
    ShellPreprocessLimit,
    _expose_backtick_bodies,
    collapse_line_continuations,
    preprocess_shell_command,
)


@pytest.mark.parametrize(
    "command",
    [
        "echo $(printf '%s' '# gh pr merge 5 --admin')",
        'echo $(printf "%s" "# gh pr merge 5 --admin")',
        "echo $(printf '%s' $# ${#var} a#b)",
        r"echo \`gh pr merge 5 --admin\`",
        "echo 'literal `gh pr merge 5 --admin`'",
    ],
)
def test_issue_9115_literal_hashes_and_backticks_are_preserved(command: str):
    assert preprocess_shell_command(command).splitlines()[0] == command
    assert "\ngh pr merge 5 --admin" not in preprocess_shell_command(command)


@pytest.mark.parametrize(
    "command",
    [
        "echo $(echo foo # comment \\\ngh pr merge 5 --admin)",
        "echo `echo foo # comment \\\ngh pr merge 5 --admin`",
    ],
)
def test_issue_9115_comment_continuation_exposes_next_command(command: str):
    visible = preprocess_shell_command(command)
    assert "# comment" not in visible
    assert "\\\n" not in visible
    assert "gh pr merge 5 --admin" in visible


def test_issue_9115_nested_backtick_body_is_exposed():
    visible = preprocess_shell_command("echo $(echo `gh pr merge 5 --admin`)")
    assert visible == "echo $(echo $(gh pr merge 5 --admin))"


@pytest.mark.parametrize(
    "command, suffix",
    [
        ("echo `echo # `; tee AGENTS.md", "; tee AGENTS.md"),
        ("echo `echo # `; cat .env", "; cat .env"),
        (r"echo `echo # \` hidden `; tee AGENTS.md", "; tee AGENTS.md"),
        (r"echo `echo # \\`; tee AGENTS.md", "; tee AGENTS.md"),
        ("echo $(true )#; tee AGENTS.md", "#; tee AGENTS.md"),
    ],
)
def test_issue_9115_closing_substitution_keeps_following_command(command: str, suffix: str):
    assert collapse_line_continuations(command).endswith(suffix)
    assert preprocess_shell_command(command).endswith(suffix)


def test_issue_9115_real_backtick_nesting_crosses_cap(monkeypatch):
    import agents_extensions.shared.hooks.shell_shlex as shared

    monkeypatch.setattr(shared, "_MAX_BACKTICK_DEPTH", 2)
    body = "cat .env"
    for _ in range(3):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    with pytest.raises(ShellPreprocessLimit, match="depth exceeded"):
        _expose_backtick_bodies("echo " + body)


def test_issue_9115_arithmetic_prefix_does_not_reset_backtick_cap():
    command = r"echo `echo \`cat .env\``"
    with pytest.raises(ShellPreprocessLimit, match="depth exceeded"):
        _expose_backtick_bodies("$(()) " + command, depth=15)
