"""Shared shell preprocessing cases for executable substitution boundaries."""

from __future__ import annotations

import pytest

from agents_extensions.shared.hooks.shell_shlex import preprocess_shell_command


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


def test_issue_9115_quoted_hash_inside_backticks_is_literal():
    assert preprocess_shell_command("echo `printf '%s' '# value'`") == "echo $(printf '%s' '# value')"


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
