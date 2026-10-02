"""Opt-in lexical refusal for syntax the shared scope scanner cannot model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks"))
from shell_redirects import scope_events, unmodeled_shell_offset
from shell_shlex import preprocess_shell_command


@pytest.mark.parametrize(
    "prefix",
    [
        "",
        "true; ",
        "true && ",
        "true || ",
        "(",
        "x=$(",
        "then ",
        "do ",
        "else ",
        "{ ",
        "! ",
        "time ",
        "X=1 ",
        ">out ",
        "2>out ",
        "time ! { ",
        "time -p ",
        "if ",
        "while ",
        ">$(echo /dev/null) ",
        ">out$(true) ",
    ],
)
def test_case_command_word_refuses_at_its_position(prefix):
    line = prefix + "case x in x) true;; esac"
    assert unmodeled_shell_offset(line) == len(prefix)


@pytest.mark.parametrize(
    "line",
    [
        "echo case",
        "case=1 git status",
        'git commit -m "case x"',
        "'case' x",
        '"case" x',
        r"ca\se x",
        "echo 'case x in x)'",
        'echo "case x in x)"',
        "echo ${x:-word}",
        "echo '${x:-(}'",
        r"echo \${x:-word}",
        "echo x # case x in x)",
        "echo ${case:-word}",
        "echo case >case",
        "echo $(true) case",
        'echo "$(true) case"',
        "git checkout -b feat-$(date +%s)",
        'echo ${x:-"${y:-word}"} && git switch -c fixture',
        "echo ${x:-'${y}'} && git switch -c fixture",
    ],
)
def test_data_words_and_plain_parameter_expansions_are_not_refused(line):
    assert unmodeled_shell_offset(line) is None


@pytest.mark.parametrize(
    "word",
    [
        "${x:-(}",
        "${x:-)}",
        "${x//[(]/}",
        "${x//[)]/}",
        '"${x:-(}"',
        '${x:-"("}',
        "${x:-'('}",
        "${x:-${y:-(}}",
        '${x:-"}"}${y:-(}',
        r"${x:-\(}",
        '"${x:-${y:-)}}"',
    ],
)
def test_parameter_parentheses_refuse_from_containing_word(word):
    assert unmodeled_shell_offset("echo " + word) == 5


def test_quoted_substitution_exposes_case_command_word():
    line = 'echo "$(case x in x) true;; esac)"'
    assert unmodeled_shell_offset(line) == line.index("case")


def test_safe_nested_parameter_does_not_move_a_later_case_tripwire_earlier():
    line = 'echo ${x:-"${y:-word}"} && git switch -c fixture; case x in x) true;; esac'
    assert unmodeled_shell_offset(line) == line.index("case")


def test_heredoc_body_does_not_trigger_refusal():
    command = "cat <<'EOF'\ncase x in x) ${x:-(}\nEOF\ngit switch -c fixture"
    assert all(unmodeled_shell_offset(line) is None for line in preprocess_shell_command(command).splitlines())


def test_scope_refusal_is_opt_in_and_precedes_current_command():
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    command = "git status; git switch -c ${x:-(}"
    original = scope_events(command, **kwargs)
    assert not any(kind in {"syntax_unreadable", "line_end"} for kind, _ in original)
    events = scope_events(command, unmodeled_offset=unmodeled_shell_offset, **kwargs)
    assert events[0] == ("segment", ["git", "status"])
    refused = next(i for i, (kind, _) in enumerate(events) if kind == "syntax_unreadable")
    switch = next(i for i, (kind, argv) in enumerate(events) if kind == "segment" and argv[:2] == ["git", "switch"])
    assert refused < switch
    assert events[-1] == ("line_end", [])
