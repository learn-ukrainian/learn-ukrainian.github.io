"""Opt-in lexical refusal for syntax the shared scope scanner cannot model."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_extensions/shared/hooks"))
from shell_redirects import command_repository_unknown, scope_events, unmodeled_shell_offset
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


def test_whole_command_detector_does_not_split_scope_events():
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    command = 'git switch -c fixture; echo "$(case x in x) true;; esac)"'
    assert command_repository_unknown(command)
    events = scope_events(command, **kwargs)
    assert events[0] == ("segment", ["git", "switch", "-c", "fixture"])
    assert not any(kind in {"syntax_unreadable", "line_end", "unreadable"} for kind, _ in events)


@pytest.mark.parametrize(
    "command",
    [
        'echo "unterminated',
        "echo '${x:-word}",
        "cat <<EOF\nnever closed",
        "cat <<'EOF'\nnever closed",
        "echo ${x:-word",
        "echo $(true",
        "echo `unterminated",
        "echo \\",
    ],
)
def test_undecidable_detector_fails_closed(command):
    assert command_repository_unknown(command)


@pytest.mark.parametrize(
    "command",
    [
        "echo case\ngit switch -c fixture",
        "echo ${#arr[@]}",
        "cat <<'EOF'\ncase x in x) ${x:-(}\nEOF\ngit switch -c fixture",
        'echo "two\nlines"',
    ],
)
def test_whole_command_detector_controls(command):
    assert not command_repository_unknown(command)


def test_detector_internal_failure_fails_closed(monkeypatch):
    import shell_redirects

    def broken(command):
        raise RuntimeError("synthetic detector failure")

    monkeypatch.setattr(shell_redirects, "unmodeled_shell_offset", broken)
    assert command_repository_unknown("git switch -c fixture")


@pytest.mark.parametrize(
    "command",
    [
        'echo "$(case x in x) git switch -c fixture;; esac)"',
        'echo "$(case x in\nx) git switch -c fixture;;\nesac)"',
        'echo "$(case x in x) (true);; esac)" && git switch -c fixture',
        'echo "$(case x in x) (git switch -c fixture);; esac)"',
        'echo "$(if true; then case x in x) git switch -c fixture;; esac; fi)"',
        "echo ${x:-$(git switch -c fixture)}",
        "echo ${x:-'('}; git switch -c fixture",
        'git switch -c fixture; echo "unterminated',
        'echo "$(echo $(case x in x) git switch -c fixture;; esac))"',
    ],
)
def test_unknown_repository_reader_keeps_branch_commands_visible(command):
    from shell_redirects import unknown_repository_segments

    assert ["git", "switch", "-c", "fixture"] in unknown_repository_segments(command)


@pytest.mark.parametrize(
    "command",
    [
        'case x in x) echo "git switch -c literal";; esac',
        "echo '${x:-$(git switch -c literal)}'",
        "echo ${x:-'$(git switch -c literal)'}",
        "echo \"$(case x in x) echo 'git switch -c literal';; esac)\"",
    ],
)
def test_unknown_repository_reader_keeps_quoted_branch_prose_inert(command):
    from shell_redirects import unknown_repository_segments

    assert not any(argv[:2] == ["git", "switch"] for argv in unknown_repository_segments(command))


def test_original_argv_order_survives_whole_command_refusal():
    kwargs = dict(mark_redirect_unreadable=True, unreadable_marker="?", unparsed=["?"], may_match=lambda _: False)
    command = "git status; git switch -c ${x:-(}"
    assert command_repository_unknown(command)
    events = scope_events(command, **kwargs)
    assert events[0] == ("segment", ["git", "status"])
    switch = next(i for i, (kind, argv) in enumerate(events) if kind == "segment" and argv[:2] == ["git", "switch"])
    assert switch > 0
    assert not any(kind in {"syntax_unreadable", "line_end"} for kind, _ in events)
