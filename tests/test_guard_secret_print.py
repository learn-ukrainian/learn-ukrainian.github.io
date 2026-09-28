"""Unit tests for the secret-print guard hook (#M-5 / #1908).

Exercises the narrow decision logic in
``agents_extensions/shared/hooks/guard-secret-print.py``:

  * clear secret dump shapes are blocked,
  * key-only/count/presence checks are allowed,
  * quoted command-message bodies do not trigger substring false positives, and
  * the LEARN_UK_SECRETS_OK=1 override is honored.

The hook filename has hyphens, so it is loaded by path via importlib. ``main``
is guarded by ``__name__ == "__main__"``, so import has no side effects.
"""

from __future__ import annotations

import importlib.util
import io
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-secret-print.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_secret_print", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()


def _run(monkeypatch, command: str, *, env_override: bool = False) -> int:
    payload = json.dumps({"tool_input": {"command": command}})
    monkeypatch.setattr("sys.stdin", io.StringIO(payload))
    if env_override:
        monkeypatch.setenv("LEARN_UK_SECRETS_OK", "1")
    else:
        monkeypatch.delenv("LEARN_UK_SECRETS_OK", raising=False)
    return guard.main()


@pytest.mark.parametrize(
    "cmd",
    [
        "env",
        "cat ~/.aws/credentials",
        "cat .env",
        "tail .envrc",
        "grep KEY .envrc",
        "echo $GH_TOKEN",
    ],
)
def test_secret_dump_shapes_blocked(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    err = capsys.readouterr().err
    assert "BLOCKED by guard-secret-print (#M-5)" in err
    assert "cut -d= -f1" in err
    assert "jq keys" in err
    assert '[ -n "${X:-}" ]' in err
    assert "LEARN_UK_SECRETS_OK=1" in err


@pytest.mark.parametrize(
    "command",
    [
        "echo hi\ncat .env",
        "cat < .env",
        "cat<.env",
        'cat <<< "$GH_TOKEN"',
        "echo $(cat .env)",
        "echo $(echo ok; cat .env)",
        "echo `cat .env`",
        'echo "$(cat .env)"',
        'echo "`cat .env`"',
        "eval 'cat .env'",
        "eval 'echo $GH_TOKEN'",
        'export X=$GH_TOKEN; printf %s "$X"',
        'export X=$GH_TOKEN; Y=$X; printf %s "$Y"',
        'export X=$GH_TOKEN; echo $(printf %s "$X")',
    ],
)
def test_issue_8896_secret_bypasses_block(monkeypatch, capsys, command):
    assert _run(monkeypatch, command) == 2
    assert "BLOCKED by guard-secret-print" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "cat <<EOF\n$(cat .env)\nEOF",
        "cat <<-EOF\n\t$(cat .env)\n\tEOF",
        'eval "$(echo cat .env)"',
        "eval \"$(printf %s 'cat .env')\"",
        "bash -c 'cat .env'",
        "sh -c 'cat .env'",
        "while read l; do echo $l; done < .env",
        "awk '{print}' < .env",
        'read X <<< "$GH_TOKEN"; printf %s "$X"',
        'declare -n X=GH_TOKEN; printf %s "$X"',
        'f() { local X=$GH_TOKEN; printf %s "$X"; }; f',
        'name=GH_TOKEN; printf %s "${!name}"',
        "cat <(cat .env)",
        'source <(cat .env); printf %s "$FOO"',
        "echo ok >(cat .env)",
        'printf -v X %s "$GH_TOKEN"',
    ],
)
def test_issue_8896_review_round_two_secret_bypasses_block(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "{ cat .env; }",
        "( cat .env )",
        "if true; then cat .env; elif false; then echo ok; else echo ok; fi",
        'while read l; do echo "$l"; done < .env',
        "until false; do cat .env; done",
        "for x in one; do cat .env; done",
        "case x in x) cat .env;; esac",
        "! cat .env",
        "exec cat .env",
        'builtin printf %s "$GH_TOKEN"',
        "command -p cat .env",
        "env -i cat .env",
        "nice cat .env",
        "timeout 3 cat .env",
        "stdbuf -o0 cat .env",
        "cat $'.env'",
        "eval $'cat .env'",
        "bash -c $'cat .env'",
        "bash --posix -c 'cat .env'",
        "bash -e -x -c 'cat .env'",
        "bash -o posix -c 'cat .env'",
        "dash -c 'cat .env'",
        "zsh -c 'cat .env'",
        "ksh -c 'cat .env'",
        "busybox sh -c 'cat .env'",
        "cat <<EOF\n$(cat \\\n.env)\nEOF",
    ],
)
def test_issue_8896_review_round_three_secret_shapes_block(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "echo ${GH_TOKEN}",
        "printf %s ${GH_TOKEN}",
        "echo ${x#y}; cat .env",
        "echo a & { cat .env; }",
        "echo ${GH_TOKEN:-x}",
        "name=GH_TOKEN; echo ${!name}",
        "echo ${x:-${GH_TOKEN}}",
        'echo ${x:-$(printf %s "$GH_TOKEN")}',
    ],
)
def test_issue_8896_unquoted_parameter_expansions_block(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "echo a{b,c}",
        "find . -name '*.py' -exec wc -l {} \\;",
        "echo }",
        "echo {}",
        "{ echo a; echo b; } > /tmp/x",
        "f() { echo ok; }; f",
        "echo a & { echo b; }",
    ],
)
def test_issue_8896_literal_and_command_braces_allow(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


def test_issue_8896_parameter_expansion_stays_one_word():
    assert guard._tokenize('echo ${x:-$(printf %s "${GH_TOKEN:-x}")}') == [
        "echo",
        '${x:-$(printf %s "${GH_TOKEN:-x}")}',
    ]
    assert guard._tokenize("echo ${x#y}; cat .env") == ["echo", "${x#y}", ";", "cat", ".env"]


@pytest.mark.parametrize(
    "command",
    [
        r'''grep -rn "\"why\"\|'why'" scripts/ --include=*.py | head -8''',
        r'echo "a \" b"',
        r'printf "%s\n" "x\"y"',
        r'''echo 'single' "double \" quoted" | head -8''',
    ],
)
def test_issue_9088_escaped_double_quote_commands_allow(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


def test_issue_9088_double_quote_escapes_keep_quote_preserving_tokens():
    assert guard._tokenize(r'echo "a \" b"') == ["echo", r'"a \" b"']
    assert guard._tokenize(r'printf "%s\n" "x\"y"') == ["printf", r'"%s\n"', r'"x\"y"']
    assert guard._tokenize(r'echo "a \\ \$ \` b"') == ["echo", r'"a \\ \$ \` b"']
    assert guard._tokenize(r'echo "a \\"') == ["echo", r'"a \\"']


def test_issue_9088_heredoc_opener_after_escaped_quote_is_found():
    assert guard._heredoc_delimiters(r'echo "a \" b" <<EOF') == [("EOF", False, False)]


@pytest.mark.parametrize("opener,closer,quoted", [
    ("<<'EOF'", "EOF", True),
    ('<<"EOF"', "EOF", True),
    ("<<EOF", "EOF", False),
    ("<<-EOF", "\tEOF", False),
])
def test_issue_9088_standard_heredoc_delimiters(opener, closer, quoted):
    assert guard._heredoc_delimiters(f"cat {opener}") == [("EOF", opener == "<<-EOF", quoted)]
    assert guard._strip_heredoc_bodies(f"cat {opener}\ncat .env\n{closer}\necho $GH_TOKEN") == (
        f"cat {opener}\necho $GH_TOKEN"
    )


@pytest.mark.parametrize("word,delimiter", [
    (r"'EO\F'", r"EO\F"),
    (r'"EO\"F"', 'EO"F'),
    (r'"EO\\F"', r'EO\F'),
    (r'"EO\$F"', 'EO$F'),
    (r'"EO\`F"', 'EO`F'),
    (r'"EO\qF"', r'EO\qF'),
    (r'EO\F', 'EOF'),
    (r"EO\'F", "EO'F"),
])
def test_issue_9088_bash_quote_removal_for_heredoc(word, delimiter):
    assert guard.heredoc_delimiter(word) == delimiter
    assert guard._strip_heredoc_bodies(f"cat <<{word}\nnote\n{delimiter}\ncat .env") == (
        f"cat <<{word}\ncat .env"
    )


def test_issue_9088_reviewer_heredoc_bypass_blocks(monkeypatch):
    command = 'cat <<"EO\\"F"\nnote\nEO"F\ngh pr merge 1 --admin\ngit checkout -b feature\ntee AGENTS.md\necho $GH_TOKEN\ncat .env\nEO\\"F'
    assert _run(monkeypatch, command) == 2


def test_issue_9088_missing_shell_helper_blocks(tmp_path):
    guard_copy = tmp_path / HOOK_PATH.name
    shutil.copy2(HOOK_PATH, guard_copy)
    result = subprocess.run(
        [sys.executable, str(guard_copy)],
        input=json.dumps({"tool_input": {"command": "cat .env"}}),
        text=True, capture_output=True, check=False, timeout=30,
    )
    assert result.returncode == 2
    assert "guard dependency unavailable: shell_shlex" in result.stderr


def test_issue_9088_secret_after_escaped_quote_still_blocks(monkeypatch):
    assert _run(monkeypatch, r'echo "escaped quote: \" and $GH_TOKEN"') == 2


def test_issue_9088_unbalanced_double_quote_still_blocks(monkeypatch):
    assert _run(monkeypatch, r'echo "a \"') == 2


def test_issue_8896_secret_recursion_limit_blocks(monkeypatch):
    command = "cat .env"
    for _ in range(12):
        command = f"echo $({command})"
    assert _run(monkeypatch, command) == 2


def test_issue_8896_nested_shell_quote_concatenation_blocks(monkeypatch):
    command = "cat .env"
    for _ in range(4):
        command = f"bash -c {shlex.quote(command)}"
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize("command", ['source .env; printf %s "$FOO"', '. .env; printf %s "$FOO"'])
def test_issue_8896_source_data_flow_named_residual(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "ls -la",
        "echo ok > /tmp/x",
        "cat <<EOF\nordinary text\nEOF",
        "cat <<-EOF\n\tordinary text\n\tEOF",
        "cat <<'EOF'\n$(cat .env)\nEOF",
        "bash -c 'echo ok'",
        "while read l; do echo $l; done < notes.txt",
        "if [ -f x ]; then echo ok; fi",
        "( cd /tmp && ls )",
        "{ echo a; echo b; } > /tmp/x",
        "gh pr view 8896",
        'eval "$(echo ok)"',
        "echo '$(cat .env)'",
    ],
)
def test_issue_8896_review_round_two_ordinary_allow(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


@pytest.mark.parametrize(
    "command",
    [
        "git status",
        "ls -la",
        "echo ok > /tmp/x",
        "cat <<EOF\ncat .env\nEOF",
        "cat <<-EOF\n\tcat .env\n\tEOF",
        "echo '$GH_TOKEN'",
        "git commit -m 'echo `cat .env`'",
        "echo \\`cat .env\\`",
        "cat <<< hello",
        "echo hi \\\ncat .env",
        'X=$GH_TOKEN echo ok; printf %s "$X"',
        'export X=$GH_TOKEN; X=plain; printf %s "$X"',
        'export X=$GH_TOKEN; unset X; printf %s "$X"',
    ],
)
def test_issue_8896_ordinary_commands_allow(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


def test_issue_8896_continued_secret_file_operand_blocks(monkeypatch):
    assert _run(monkeypatch, "cat \\\n.env") == 2


@pytest.mark.parametrize(
    "cmd",
    [
        "git commit -m fix#123 && cat .env",
        "echo hi#$GH_TOKEN",
    ],
)
def test_unquoted_midword_hash_keeps_secret_checks_active(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    assert "BLOCKED by guard-secret-print (#M-5)" in capsys.readouterr().err


@pytest.mark.parametrize("blank", ["\r", "\v", "\f", "\u00a0"])
def test_non_bash_blank_before_hash_keeps_secret_checks_active(monkeypatch, capsys, blank):
    assert _run(monkeypatch, f"echo hi{blank}#$GH_TOKEN") == 2
    assert "BLOCKED by guard-secret-print (#M-5)" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "\r#; echo $GH_TOKEN",
        "\v#; cat .env",
        "\u00a0#; cat .env",
        "\u2003#; echo $GH_TOKEN",
        "\f#; cat .env",
        "\u2028#; echo $GH_TOKEN",
    ],
)
def test_leading_non_bash_blank_does_not_hide_secret_command(monkeypatch, capsys, command):
    assert _run(monkeypatch, command) == 2
    assert "BLOCKED by guard-secret-print (#M-5)" in capsys.readouterr().err


@pytest.mark.parametrize("blank", [" ", "\t"])
def test_leading_bash_blank_keeps_comment_inert(monkeypatch, blank):
    assert _run(monkeypatch, f"{blank}#; echo $GH_TOKEN") == 0


@pytest.mark.parametrize(
    "command",
    [
        "git status # echo x > AGENTS.md",
        "echo hi # $GH_TOKEN",
        "echo hi\t# $GH_TOKEN",
        "echo hi # $GH_TOKEN\r\necho safe",
        "# tee AGENTS.md",
        "echo hi # cat .env",
        "echo '#' ; echo safe",
        "echo $(printf '# hidden') # $GH_TOKEN",
        "echo `printf '# hidden'` # cat .env",
    ],
)
def test_bash_comments_do_not_trigger_secret_guard(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


@pytest.mark.parametrize(
    "command",
    [
        "git commit -m fix#123 && cat .env",
        "echo hi#$GH_TOKEN",
        "echo '#' ; cat .env",
        "echo hi # <<EOF\ncat .env",
    ],
)
def test_bash_comments_keep_executable_secret_words(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


def test_bash_comment_stripping_keeps_next_line_for_secret_parser():
    # Parsing newline separators in this hook is tracked separately.
    assert guard._strip_shell_comments("echo hi # c; cat .env\ncat .env") == "echo hi \ncat .env"
    assert guard._strip_heredoc_bodies("echo hi # <<EOF\ncat .env") == "echo hi # <<EOF\ncat .env"


@pytest.mark.parametrize("operator", [";", "&", "|", "(", ")"])
def test_bash_comment_starts_after_control_operator_in_secret_hook(operator):
    assert guard._strip_shell_comments(f"echo hi{operator}# hidden\ncat .env") == (f"echo hi{operator}\ncat .env")


@pytest.mark.parametrize(
    "cmd",
    [
        "env | cut -d= -f1",
        '[ -n "${X:-}" ] && echo SET',
        "cat README.md",
        "cat agents_extensions/shared/hooks/guard-secret-print.py",
        "cat test_api_key.py",
        "cat token_utils.py",
        "python -m pytest tests/foo.py -q 2>&1 | tail -3",
        "tail secret-print",
        "tail -n 5",
        "head -20 file.py",
        "jq keys",
        'git commit -m "notes: gh pr merge --admin and echo $GH_TOKEN"',
        'git commit -m "ref guard-secret-print.py"',
        'git commit -m "document scripts.session_supervisor worker-env"',
        "git commit -F - <<EOF\nref guard-secret-print\nEOF",
        "tail -3 <<EOF\n.env\nEOF",
        "LEARN_UK_SECRETS_OK=1 env",
    ],
)
def test_safe_commands_allowed(monkeypatch, cmd):
    assert _run(monkeypatch, cmd) == 0


def test_environment_override_allowed(monkeypatch):
    assert _run(monkeypatch, "env", env_override=True) == 0


def test_single_quoted_secret_var_literal_allowed(monkeypatch):
    assert _run(monkeypatch, "echo '$GH_TOKEN'") == 0


def test_unrelated_echo_after_secret_export_allowed(monkeypatch):
    assert _run(monkeypatch, 'export HCLOUD_TOKEN=placeholder; echo "server=$s"') == 0
    assert _run(monkeypatch, 'HCLOUD_TOKEN=placeholder echo "server=$s"') == 0


def test_echo_of_exported_secret_still_blocked(monkeypatch):
    assert _run(monkeypatch, 'export HCLOUD_TOKEN=placeholder; echo "$HCLOUD_TOKEN"') == 2


@pytest.mark.parametrize(
    "cmd",
    [
        "scripts.session_supervisor worker-env",
        "python -m scripts.session_supervisor worker-env",
        ".venv/bin/python -m scripts.session_supervisor worker-env --all",
        "python3 -m scripts.session_supervisor --all worker-env",
    ],
)
def test_worker_env_commands_are_blocked(monkeypatch, capsys, cmd):
    assert _run(monkeypatch, cmd) == 2
    assert "worker-env" in capsys.readouterr().err
