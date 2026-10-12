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
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tests.test_guard_benign_corpus import BENIGN_COMMANDS

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "agents_extensions/shared" / "hooks" / "guard-secret-print.py"


def _load_hook():
    spec = importlib.util.spec_from_file_location("guard_secret_print", HOOK_PATH)
    assert spec and spec.loader, f"could not load hook at {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = _load_hook()

ROUND_SEVEN_DENIED = [
    ("bun-bracket", "bun -e 'console.log(import.meta[\"env\"])'"),
    ("bun-optional-bracket", "bun -e 'console.log(import.meta?.[\"env\"])'"),
    ("php-filter-server", "php -r 'print_r(filter_input_array(INPUT_SERVER));'"),
    ("php-filter-env", "php -r 'print_r(filter_input_array(INPUT_ENV));'"),
    ("php-filter-var-server", "php -r 'print_r(filter_var_array(INPUT_SERVER));'"),
    ("php-filter-var-env", "php -r 'print_r(filter_var_array(INPUT_ENV));'"),
    ("php-filter-input-server", "php -r 'print_r(filter_input(INPUT_SERVER));'"),
    ("php-filter-input-env", "php -r 'print_r(filter_input(INPUT_ENV));'"),
    ("php-filter-dynamic-key", "php -r 'echo filter_input(INPUT_ENV, $name);'"),
    ("php-filter-secret-key", "php -r 'echo filter_input(INPUT_ENV, \"ARBITRARY_TOKEN\");'"),
    ("perl-use-env", "perl -e 'use Env; print $value'"),
    ("perl-require-env", "perl -e 'require Env; print $value'"),
    ("perl-tie-env", "perl -e 'tie %h, \"Env\"; print %h'"),
    ("perl-use-env-parenthesized", "perl -e 'use(Env); print $value'"),
    ("perl-require-env-parenthesized", "perl -e 'require(Env); print $value'"),
    ("perl-tie-env-parenthesized", "perl -e 'tie(%h, \"Env\"); print %h'"),
    ("compatibility-getenvironment", "python -c 'print(getenvironment())'"),
    ("shell-compgen-export", "compgen -A export"),
]

ROUND_SEVEN_ALLOWED = [
    "python -c 'environ_x = 1; print(environ_x)'",
    "python -c 'print(os.environ_x)'",
    "perl -e 'use Envoy; print 1'",
    "perl -e 'tie %h, \"Envelope\"; print 1'",
    "perl -e 'require(Envoy); print 1'",
    "perl -e 'tie(%h, \"Envelope\"); print 1'",
    "php -r 'echo filter_input(INPUT_ENV, \"HOME\");'",
    'bun -e \'console.log(import.meta["env"]["HOME"])\'',
]


@pytest.mark.parametrize("api,command", ROUND_SEVEN_DENIED, ids=[row[0] for row in ROUND_SEVEN_DENIED])
def test_round_seven_inventory_denied(api, command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout
    assert SENTINEL not in result.stderr


@pytest.mark.parametrize("command", ROUND_SEVEN_ALLOWED)
def test_round_seven_neighbors_allowed(command):
    result = _subprocess_guard(command)
    assert result.returncode == 0
    assert SENTINEL not in result.stdout
    assert SENTINEL not in result.stderr


@pytest.mark.parametrize(
    "command,code",
    [
        ("php -r 'echo filter_input(INPUT_ENV, \"HOME\");'", 0),
        ("php -r 'echo filter_input(INPUT_ENV, \"ARBITRARY_TOKEN\");'", 2),
        ("python -c 'print(os.popen(\"env\").read())'", 2),
    ],
)
def test_round_seven_literal_decisions_in_process(monkeypatch, capsys, command, code):
    monkeypatch.setenv("ARBITRARY_TOKEN", SENTINEL)
    assert _run(monkeypatch, command) == code
    captured = capsys.readouterr()
    assert SENTINEL not in captured.out
    assert SENTINEL not in captured.err
    assert captured.out == ""
    assert captured.err.startswith("BLOCKED by guard-secret-print") if code == 2 else captured.err == ""


@pytest.mark.parametrize("language,api", [("php", "getenv"), ("lua", "os.getenv")])
def test_getenv_inventory_rows_deny_without_other_rows(monkeypatch, language, api):
    row = next(row for row in guard.ENVIRONMENT_API_INVENTORY if row[:2] == (language, api))
    assert row[2] == "identifier"
    monkeypatch.setattr(guard, "_ENV_IDENTIFIERS", re.compile("(?:" + row[3] + r")(?![\w$])"))
    call = "getenv()" if language == "php" else "os.getenv()"
    assert guard._program_reason(language, call) is not None


@pytest.mark.parametrize("command", BENIGN_COMMANDS)
def test_issue_9102_benign_corpus_allowed(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


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
        "cat ~/.secrets/*",
        "cat ~/.secrets/example.key",
        "env | grep KEY",
        "env | grep PATH",
        "printenv *_KEY",
        "printenv CURSOR_API_KEY",
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
        r"""grep -rn "\"why\"\|'why'" scripts/ --include=*.py | head -8""",
        r'echo "a \" b"',
        r'printf "%s\n" "x\"y"',
        r"""echo 'single' "double \" quoted" | head -8""",
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


@pytest.mark.parametrize(
    "shape",
    [
        "echo $((1 << EOF))\n{payload}\nEOF",
        "((1 << EOF))\n{payload}\nEOF",
        "echo ${x#<<EOF }\n{payload}\nEOF",
        "let 'x=1<<EOF'\n{payload}\nEOF",
        "true # <<EOF\n{payload}\nEOF",
        ": <<EOF; \\\n{payload}\nnote\nEOF",
        ": <<EOF\n$({payload})\nEOF",
        ": <<EOF\n`{payload}`\nEOF",
        "echo '\n: <<EOF\n'\n" + "{payload}" + "\nEOF",
        ": << -EOF\nnote\n-EOF\n{payload}\nEOF",
        "echo foo # comment \\\n{payload}",
        ": <<EOF\n$(echo x\n{payload}\n)\nEOF",
        ": <<EOF\n$(echo x # )\n{payload}\n)\nEOF",
        ": <<EOF\n`echo x\n{payload}\n`\nEOF",
        ": <<EOF\n$(echo ')'; {payload})\nEOF",
        "x[1 << EOF ]=1\n{payload}\nEOF",
        "echo $[1 << EOF ]\n{payload}\nEOF",
    ],
)
def test_issue_9102_executable_payload_stays_visible(monkeypatch, shape):
    assert _run(monkeypatch, shape.replace("{payload}", "cat .env")) == 2


def test_issue_9102_real_let_heredoc_body_is_inert(monkeypatch):
    assert _run(monkeypatch, "let x=1<<EOF\ncat .env\nEOF") == 0


@pytest.mark.parametrize(
    "command",
    [
        "echo $(echo foo # comment \\\ncat .env)",
        "echo `cat .env`",
        'echo "`cat .env`"',
        "echo `echo foo # comment \\\ncat .env`",
        "echo $(echo foo # comment \\\n`cat .env`)",
    ],
)
def test_issue_9115_nested_and_backtick_secret_reads_blocked(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "x=`pwd`; cat .env",
        "echo `true`; cat .env",
        "echo $(true); cat .env",
        "echo `echo # `; cat .env",
        "echo $(true )#; cat .env",
    ],
)
def test_issue_9115_substitution_operator_and_comment_boundaries_block_secret_reads(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


def test_issue_9115_escaped_nested_backtick_secret_read_is_visible(monkeypatch):
    assert _run(monkeypatch, r"echo `echo \`cat .env\``") == 2


@pytest.mark.parametrize(
    "command",
    [
        "cat 2>&1 .env",
        "cat >&2 .env",
        "head -n5 >&2 .env",
        "cat 1>&2 ~/.ssh/id_rsa",
        "cat <&0 .env",
        "cat 2>&- .env",
        "cat &> /dev/null .env",
        "cat &>> /dev/null .env",
        "echo $(cat 2>&1 .env)",
        "grep -r KEY 2>/dev/null >&2 .env",
    ],
)
def test_issue_9115_redirection_does_not_hide_secret_file(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


def test_issue_9115_backtick_depth_limit_blocks_secret_hook(monkeypatch):
    monkeypatch.setattr(sys.modules["shell_shlex"], "_MAX_BACKTICK_DEPTH", 2)
    body = "cat .env"
    for _ in range(3):
        body = "`" + body.replace("\\", "\\\\").replace("`", r"\`") + "`"
    assert _run(monkeypatch, "echo " + body) == 2


@pytest.mark.parametrize("payload", ["not-json", "null", '{"tool_input":{"command":[]}}'])
def test_issue_9115_malformed_secret_hook_input_blocks(monkeypatch, payload):
    monkeypatch.setattr(sys, "stdin", io.StringIO(payload))
    assert guard.main() == 2


@pytest.mark.parametrize(
    "opener,closer,quoted",
    [
        ("<<'EOF'", "EOF", True),
        ('<<"EOF"', "EOF", True),
        ("<<EOF", "EOF", False),
        ("<<-EOF", "\tEOF", False),
    ],
)
def test_issue_9088_standard_heredoc_delimiters(opener, closer, quoted):
    assert guard._heredoc_delimiters(f"cat {opener}") == [("EOF", opener == "<<-EOF", quoted)]
    assert guard._strip_heredoc_bodies(f"cat {opener}\ncat .env\n{closer}\necho $GH_TOKEN") == (
        f"cat {opener}\necho $GH_TOKEN"
    )


@pytest.mark.parametrize(
    "first",
    [
        "true <<<EOF",
        "true <<< EOF",
        "true <<<'EOF'",
        'true <<<"EOF"',
        "true<<<EOF",
    ],
)
def test_issue_9088_here_strings_keep_secret_dump_visible(monkeypatch, first):
    command = f"{first}\ncat .env\nEOF"
    assert guard._heredoc_delimiters(first) == []
    assert "cat .env" in guard._strip_heredoc_bodies(command)
    assert _run(monkeypatch, command) == 2


def test_issue_9088_crlf_closer_keeps_secret_dump_visible(monkeypatch):
    command = "cat <<EOF\r\nEOF\r\ncat .env\nEOF"
    assert "cat .env" in guard._strip_heredoc_bodies(command)
    assert _run(monkeypatch, command) == 2


def test_issue_9088_quoted_identifier_heredoc_body_is_inert(monkeypatch):
    assert _run(monkeypatch, "cat <<'EOF'\ncat .env\necho $GH_TOKEN\nEOF") == 0


@pytest.mark.parametrize(
    "opener,closer",
    [
        (r'<<"EO\"F"', 'EO"F'),
        (r"<<$'EOF'", "EOF"),
        ('<<$"EOF"', "EOF"),
        (r"<<$'EO\x22F'", 'EO"F'),
        (r"<<EO$'F'", "EOF"),
        (r"<<E\OF", "EOF"),
        (r"<<-$'EOF'", "\tEOF"),
        (r"<<$'EOF' <<SAFE", "EOF\nSAFE"),
        (r"<<SAFE <<$'EOF'", "SAFE\nEOF"),
    ],
)
def test_issue_9088_exotic_heredoc_keeps_secret_dump_visible(monkeypatch, opener, closer):
    command = f"cat {opener}\ncat .env\necho $GH_TOKEN\n{closer}"
    assert guard._heredoc_delimiters(f"cat {opener}") is None
    assert _run(monkeypatch, command) == 2


def test_issue_9088_exotic_body_cannot_skip_later_safe_opener(monkeypatch):
    command = "cat <<$'EOF'\ncat <<SAFE\ncat .env\nSAFE\nEOF"
    assert "cat .env" in guard._strip_heredoc_bodies(command)
    assert _run(monkeypatch, command) == 2


def test_issue_9088_reviewer_heredoc_bypass_blocks(monkeypatch):
    command = 'cat <<"EO\\"F"\nnote\nEO"F\ngh pr merge 1 --admin\ngit checkout -b feature\ntee AGENTS.md\necho $GH_TOKEN\ncat .env\nEO\\"F'
    assert _run(monkeypatch, command) == 2


def test_issue_9088_missing_shell_helper_blocks(tmp_path):
    guard_copy = tmp_path / HOOK_PATH.name
    shutil.copy2(HOOK_PATH, guard_copy)
    result = subprocess.run(
        [sys.executable, str(guard_copy)],
        input=json.dumps({"tool_input": {"command": "cat .env"}}),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
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
        "printenv PATH",
        "printenv HOME",
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


# Audit candidates are detector input only; the shell never executes them.
AUDIT_NAMES = [
    "ANTHROPIC_API_KEY",
    "DAGGER_CLOUD_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
    "ARBITRARY_API_KEY",
    "ARBITRARY_TOKEN",
    "ARBITRARY_SECRET",
    "ARBITRARY_PAT",
    "CURSOR_API_KEY",
    "CURSOR_API_TOKEN",
    "arbitrary_token",
    "API_KEY",
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "AWS_SECRET_ACCESS_KEY",
]
# (shape, expected exit for a guarded name, expected exit for other names)
AUDIT_SHAPES = [
    ('echo "${name}"', 2, 0),
    ('printf "%s\\n" "${name}"', 2, 0),
    ("python -c 'import os; print(os.environ[\"{name}\"])'", 2, 0),
    ("node -e 'console.log(process.env.{name})'", 2, 0),
    ("env", 2, 2),
    ("printenv", 2, 2),
    ("set", 2, 2),
    ("env | grep {name}", 2, 2),
    ("printenv {name}", 2, 0),
    ('echo "${name}" > /dev/null', 2, 0),
    ("env > /dev/null", 0, 0),
    ("env > /dev/stdout", 2, 2),
    ("env > audit-placeholder.txt; cat audit-placeholder.txt", 2, 2),
    ("cat < .env", 2, 2),
    ("cat <<EOF\n${name}\nEOF", 2, 0),
    ("python - <<'PYCODE'\nimport os\nprint(os.environ[\"{name}\"])\nPYCODE", 2, 0),
    ("cat <<'EOF'\n${name}\nEOF", 0, 0),
    ("declare -p {name}", 2, 0),
    ("declare -p", 2, 2),
    ("export -p", 2, 2),
    ("cat /proc/self/environ", 2, 2),
    ("cat /proc/$$/environ", 2, 2),
    ("set | grep {name}", 2, 2),
    ("cat .env", 2, 2),
    ("env | cut -d= -f1", 0, 0),
    ("cat .env | jq -r '.keys, .{name}'", 2, 2),
    ("cat .env | grep -o '.*'", 2, 2),
    ('LEARN_UK_SECRETS_OK=1 echo "${name}"', 0, 0),
]
SENTINEL = "synthetic_guard_value_91b8"


def _subprocess_guard(command):
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps({"tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        timeout=10,
        env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(AUDIT_NAMES, SENTINEL)},
    )


@pytest.mark.parametrize("name", AUDIT_NAMES)
@pytest.mark.parametrize("shape,secret_exit,other_exit", AUDIT_SHAPES)
def test_audit_shapes(name, shape, secret_exit, other_exit):
    expected = secret_exit if guard._is_secret_var_name(name) else other_exit
    if shape == "printenv {name}" and name in {"API_KEY", "PASSWORD", "SECRET", "TOKEN", "AWS_SECRET_ACCESS_KEY"}:
        expected = 2
    result = _subprocess_guard(shape.replace("{name}", name))
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == expected


@pytest.mark.parametrize(
    "command",
    [
        "env | cut -d= -f1",
        "cat <<'EOF'\n$OPENAI_API_KEY\nEOF",
        'git commit -m "echo $OPENAI_API_KEY; env | grep OPENAI_API_KEY"',
        'echo "$HOME"',
        "echo $PATH",
        "LEARN_UK_SECRETS_OK=1 env",
        'git commit -m "document OPENAI_API_KEY handling"',
        "grep -c API_KEY file",
        "env -i FOO=bar cmd",
        "compgen -v",
        "env > capture.txt",
        "env | sed 's/=.*//'",
        "env | awk -F= '{print $1}'",
        "env | wc -l",
        "env | cut -d= -f1 | sort | head | tail",
        "cat .env | jq keys",
        "cat .env | jq keys_unsorted",
        "cat .env | jq 'to_entries|map(.key)'",
        "cat .env | grep -o '^[^=]*'",
        "python -c 'print(\"OPENAI_API_KEY\")'",
        "python -c 'import os; print(os.getenv(\"HOME\"))'",
    ],
)
def test_audit_false_positive_controls(command):
    result = _subprocess_guard(command)
    assert result.returncode == 0
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "env | rg ARBITRARY_TOKEN",
        "env | sed -n '/ARBITRARY_TOKEN/p'",
        "env | awk '/ARBITRARY_TOKEN/'",
        "typeset -p ARBITRARY_SECRET",
        "typeset -p",
        "declare -px ARBITRARY_PAT",
        "export -p | head",
        "env | sort",
        "env | head",
        "env | tail",
        "env | tee dump | cut -d= -f1",
        "cat /proc/1234/environ",
        "strings /proc/self/environ",
        "tr '\\0' '\\n' < /proc/$$/environ",
        "xargs -0 < /proc/self/environ",
        "python -c 'print(open(\"/proc/self/environ\").read())'",
        "cat <<EOF\n${ARBITRARY_SECRET}\nEOF",
        'cat <<<"$ARBITRARY_PAT"',
        "python -c 'import os; print(os.getenv(\"ARBITRARY_TOKEN\"))'",
        "python -c 'import os; k=\"ARBITRARY_SECRET\"; print(os.environ[k])'",
        "perl -e 'print $ENV{ARBITRARY_TOKEN}'",
        "ruby -e 'puts ENV[\"ARBITRARY_SECRET\"]'",
        "node -e 'console.log(process.env[\"ARBITRARY_API_KEY\"])'",
        "env > /dev/tty",
        "declare -p > dump; head dump",
        "env > dump && strings dump",
        "cat .env | jq '.keys, .[]'",
        "cat .env | jq 'keys, .[]'",
        "cat .env | grep -o 'API_KEY=.*'",
        "env | sed 's/=.*//;p'",
        "env | awk -F= '{print $0,$1}'",
        "cat .env | grep -ov KEY",
    ],
)
def test_additional_credential_print_shapes(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "export",
        "declare",
        "typeset",
        "declare -x | grep ARBITRARY_TOKEN",
        "env > /dev/stderr",
        "env > /dev/fd/2",
        "env > dump; python -c 'print(open(\"dump\").read())'",
        "env > dump; cat ./dump",
        "env | grep -o -e '^[^=]*' -e '.*'",
        "cat .env | grep -o --regexp='.*'",
    ],
)
def test_dump_boundary_siblings(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


def test_deny_diagnostic_does_not_echo_candidate_filename():
    result = _subprocess_guard(f"cat .env.{SENTINEL}")
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "LEARN_UK_SECRETS_OK=1 echo ok; cat <<EOF\n$ARBITRARY_TOKEN\nEOF",
        'env > dump; bash -c "cat dump"',
        'env > dump; echo "$(cat dump)"',
    ],
)
def test_dump_boundaries_across_shell_scopes(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "LEARN_UK_SECRETS_OK=1 cat <<EOF\n$ARBITRARY_TOKEN\nEOF",
        'LEARN_UK_SECRETS_OK=1 cat <<EOF\n$ARBITRARY_TOKEN\nEOF\necho "$HOME"',
    ],
)
def test_override_on_heredoc_owner(command):
    result = _subprocess_guard(command)
    assert result.returncode == 0
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "env -u HOME | grep ARBITRARY_TOKEN",
        "env | tee /dev/stdout > dump",
        "env | grep ARBITRARY_TOKEN > dump",
        "env > dump | cut -d= -f1; cat dump",
    ],
)
def test_redirect_does_not_hide_unsanitized_pipeline(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        'bash -c "env > dump"; cat dump',
        'echo "$(env > dump)"; cat dump',
        'eval "env > dump"; cat dump',
    ],
)
def test_nested_dump_remains_visible_to_outer_shell(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "env > >(cat)",
        "printenv > >(tee /dev/tty)",
        "env > >(base64)",
        "env > >(wc -c; cat)",
    ],
)
def test_output_substitution_dump_denied(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize("consumer", ["bash", "sh", "zsh", "dash", "ksh", "eval", "source", "."])
@pytest.mark.parametrize("body", ["env", "printenv", "cat .env", "echo $ARBITRARY_TOKEN"])
@pytest.mark.parametrize("redirect", ["<<'EOF'", "<<EOF", "<<<"])
def test_shell_standard_input_denied(consumer, body, redirect):
    command = f"{consumer} <<< {shlex.quote(body)}" if redirect == "<<<" else f"{consumer} {redirect}\n{body}\nEOF"
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "prefix,body",
    [
        ("export X=$ARBITRARY_TOKEN;", "$X"),
        ("name=ARBITRARY_TOKEN;", "${!name}"),
        ("declare -n X=ARBITRARY_TOKEN;", "$X"),
        ("export X=$ARBITRARY_TOKEN; Y=$X;", "$Y"),
    ],
)
def test_expanding_heredoc_observes_prior_assignments(prefix, body):
    result = _subprocess_guard(f"{prefix} cat <<EOF\n{body}\nEOF")
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "python -c 'import os; print(os.environ)'",
        "python -c 'import os; print([*os.environ.values()])'",
        "node -e 'console.log(process.env)'",
        "node -e 'console.log(JSON.stringify(process.env))'",
        "perl -e 'print %ENV'",
        "ruby -e 'puts ENV.to_h'",
        "ruby -e 'puts ENV.to_a'",
        "ruby -e 'ENV.each { |k,v| puts v }'",
        "ruby -e 'puts ENV.inspect'",
        "python -c 'import os; print(os.en''viron)'",
        "python -c 'import os; print(os.environ[\"ARBITRARY_''TOKEN\"])'",
        "node -e 'console.log(process.en''v.ARBITRARY_TOKEN)'",
        "python -c 'import os; print(os.environ.get(\"ARBITRARY_''TOKEN\"))'",
    ],
)
def test_inline_environment_mapping_denied(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize("path", ["/proc/self/environ", "/proc/$$/environ", "/proc/123/environ", ".env"])
@pytest.mark.parametrize("reader", ["base64", "xxd", "od -An -tx1", "hexdump -C", "dd if=", "cut -c1-"])
def test_sensitive_file_operand_denied(path, reader):
    separator = "" if reader.endswith("=") else " "
    result = _subprocess_guard(reader + separator + path)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize("command", ["unknown-reader < .env", "unknown-reader < /proc/self/environ", "wc -L .env"])
def test_sensitive_file_input_denied(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "declare -f",
        "typeset -f",
        "export -f",
        "env > >(wc -c)",
        "env > >(cut -d= -f1)",
        "env > >(true)",
        "echo ordinary > >(cat)",
        "env > capture.txt",
        "echo $PATH",
        "compgen -v",
        "bash <<'EOF'\necho ordinary\nEOF",
        "sh <<EOF\ncat README.md\nEOF",
        "bash <<<'echo $PATH'",
        "cat <<'EOF'\nprintenv\nEOF",
        "cat <<<'printenv'",
        "X=ordinary; cat <<EOF\n$X\nEOF",
        "name=PATH; cat <<EOF\n${!name}\nEOF",
        "python -c 'import os; print(os.environ[\"PATH\"])'",
        "python -c 'import os; print(os.environ.get(\"PATH\"))'",
        "node -e 'console.log(process.env.PATH)'",
        "node -e 'console.log(process.env[\"PATH\"])'",
        "perl -e 'print $ENV{PATH}'",
        "ruby -e 'puts ENV[\"PATH\"]'",
        "python -c 'import os; print(os.environ[\"PA''TH\"])'",
        "base64 README.md",
        "xxd .env.example",
        "dd if=README.md",
        "cut -c1- notes.txt",
        "test -f .env",
        "[ -f .env ]",
        "stat .env",
        "ls .env",
        "wc -c .env",
        "file .env",
        "wc -c < .env",
        "stat /proc/self/environ",
        "file /proc/self/environ",
        "cut -d= -f1 .env",
        "cut -d= -f1 < .env",
        "sed 's/=.*//' .env",
        "awk -F= '{print $1}' .env",
        "cat .env | jq keys",
        "grep TOKEN file",
        "git log --grep=token",
        'echo "set the token"',
    ],
)
def test_structural_dump_rule_neighbors_allowed(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


def test_later_substitution_does_not_preempt_earlier_denial(monkeypatch, capsys):
    assert _run(monkeypatch, 'echo "$ARBITRARY_TOKEN"; echo $(cat .env)') == 2
    assert "`echo` would print" in capsys.readouterr().err


@pytest.mark.parametrize(
    "command",
    [
        "env > >(wc -c) > capture.txt; cat capture.txt",
        "LEARN_UK_SECRETS_OK=1 cat <<'EOF'\nordinary\nEOF\ncat <<EOF\n$ARBITRARY_TOKEN\nEOF",
    ],
)
def test_nested_input_owner_boundaries_denied(monkeypatch, command):
    assert _run(monkeypatch, command) == 2


@pytest.mark.parametrize(
    "command",
    [
        "env > >(wc -c) > capture.txt",
        "LEARN_UK_SECRETS_OK=1 cat <<'EOF'\nordinary\nEOF\ncat <<EOF\nordinary\nEOF",
    ],
)
def test_nested_input_owner_neighbors_allowed(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


@pytest.mark.parametrize(
    "command",
    [
        "file -f .env",
        "file --files-from=.env",
        "file --files-from .env",
        "file -f.env",
        "file -bf .env",
        "file -bf.env",
        "env > >(file -f -)",
        "env > >(file --files-from=-)",
        "env > >(file -bf -)",
        "env > >(file -f-)",
    ],
)
def test_file_list_variants_denied(command):
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "consumer,program",
    [
        ("python", "import os; print(os.environ)"),
        ("node", "console.log(process.env)"),
        ("perl", "print %ENV"),
        ("ruby", "puts ENV.to_h"),
    ],
)
@pytest.mark.parametrize("redirect", ["<<<", "<<'EOF'", "<<EOF"])
def test_interpreter_stdin_variants_denied(consumer, program, redirect):
    command = (
        f"{consumer} <<< {shlex.quote(program)}" if redirect == "<<<" else f"{consumer} {redirect}\n{program}\nEOF"
    )
    result = _subprocess_guard(command)
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


def test_shell_inline_cat_heredoc_current_behavior_denied():
    result = _subprocess_guard("bash -c 'cat' <<'EOF'\nenv\nEOF")
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "path",
    [
        "/proc/./self/environ",
        "/proc/self//environ",
        "/proc/self/../self/environ",
        "//proc//self/environ",
        "./.env",
        "dir/../.env",
        ".env.example/../.env",
    ],
)
def test_normalized_sensitive_path_variants_denied(path):
    result = _subprocess_guard(f"base64 {path}")
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "consumer,program",
    [
        ("python", 'import os; print(os["environ"])'),
        ("python", "import os; print(os [ 'environ' ])"),
        ("python", "import os; print(os.getenv())"),
        ("node", 'console.log(process["env"])'),
        ("node", "console.log(process [ 'env' ])"),
        ("node", "console.log(process.env.valueOf())"),
        ("node", "console.log(process.env.values())"),
        ("ruby", "puts ENV.to_hash"),
        ("ruby", "puts ENV.values"),
        ("ruby", "p ENV"),
        ("ruby", "puts ENV"),
        ("ruby", "puts ENV.to_h"),
        ("perl", "say %ENV"),
    ],
)
@pytest.mark.parametrize("flag", ["-c", "-e", "-E", "--eval", "--command", "-pe", "-ne"])
@pytest.mark.parametrize("attached", [False, True])
def test_inline_mapping_flag_variants_denied(consumer, program, flag, attached):
    separator = "" if attached else " "
    if attached and flag.startswith("--"):
        separator = "="
    result = _subprocess_guard(f"{consumer} {flag}{separator}{shlex.quote(program)}")
    assert result.returncode == 2
    assert SENTINEL not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "ls .env.example",
        "git diff -- .env.example",
        "python -c 'print(1)'",
        "python -c'print(1)'",
        "node --eval 'console.log(1)'",
        "file -- .env",
        "file -- -f .env",
        "env > >(file -)",
        'python -c \'import os; print(os["environ"]["PATH"])\'',
        "python -c 'import os; print(os.environ.get(\"PATH\"))'",
        "node -e 'console.log(process[\"env\"].PATH)'",
        'node -e \'console.log(process ["env"] ["PATH"])\'',
        "ruby -e 'puts ENV.fetch(\"PATH\")'",
        "ruby -e 'puts ENV.fetch( :PATH )'",
        "ruby -e 'puts ENV[ :PATH ]'",
        "perl -E 'say $ENV{PATH}'",
    ],
)
def test_round_four_neighbors_allowed(monkeypatch, command):
    assert _run(monkeypatch, command) == 0


# Each review spelling is a separate subprocess row; no candidate is executed.
ROUND_FIVE_SPELLINGS = [
    "perl -le 'say %ENV'",
    "perl -lE 'say %ENV'",
    "perl -we 'say %ENV'",
    "perl -le'say %ENV'",
    "ruby -le 'puts ENV'",
    "ruby -we 'puts ENV'",
    "python -uc 'import os; print(os.environ)'",
    "python -Ic 'import os; print(os.environ)'",
    "python3 -Bc 'import os; print(os.environ)'",
    "python -uc'import os; print(os.environ)'",
    "perl -nle 'say %ENV'",
    "perl -ple 'say %ENV'",
    "python -c 'print(os[f\"environ\"])'",
    "python -c 'print(os[r\"environ\"])'",
    "python -c 'print(os[u\"environ\"])'",
    'python -c \'print(os["""environ"""])\'',
    "node -e 'console.log(process[`env`])'",
    "node -e 'console.log(process?.env)'",
    "node -e 'console.log(process.env[\"valueOf\"]())'",
    'node -e \'console.log(process["env"]["valueOf"]())\'',
    "perl -e 'say %::ENV'",
    "perl -e 'say %main::ENV'",
]


@pytest.mark.parametrize("command", ROUND_FIVE_SPELLINGS)
def test_round_five_review_spellings_denied(command):
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


@pytest.mark.parametrize("redirect", ["<<<", "<<'EOF'", "<<EOF"])
@pytest.mark.parametrize("command", ROUND_FIVE_SPELLINGS)
def test_round_five_review_stdin_denied(command, redirect):
    consumer = command.split()[0]
    # Drop the inline option, retaining the exact script for stdin inspection.
    program = command.split("'", 1)[1].rsplit("'", 1)[0]
    candidate = (
        f"{consumer} <<< {shlex.quote(program)}" if redirect == "<<<" else f"{consumer} {redirect}\n{program}\nEOF"
    )
    result = _subprocess_guard(candidate)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


@pytest.mark.parametrize("consumer", ["python3.12", "node", "nodejs", "perl", "ruby", "php", "lua", "deno", "bun"])
@pytest.mark.parametrize("prefix", ["", "env ", "/usr/bin/env "])
@pytest.mark.parametrize(
    "program",
    [
        "environ",
        "getenv()",
        "process.env",
        "process[env]",
        "%ENV",
        "%main::ENV",
        "%::ENV",
        "$ENV",
        "ENV",
        "Deno.env",
        "Bun.env",
        "os.environ",
        "printenv",
        "getenvironment",
    ],
)
def test_round_five_identifiers_deny_every_interpreter(consumer, prefix, program):
    result = _subprocess_guard(f"{prefix}{consumer} --arbitrary-flag {shlex.quote(program)} trailing-argument")
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


ROUND_FIVE_KEYED = [
    ("python", 'print(os.environ.get("{name}"))'),
    ("python", 'print(os.environ["{name}"])'),
    ("python", 'print(os.getenv("{name}"))'),
    ("node", "console.log(process.env.{name})"),
    ("node", 'console.log(process.env["{name}"])'),
    ("ruby", 'puts ENV["{name}"]'),
    ("ruby", 'puts ENV.fetch("{name}")'),
    ("perl", "say $ENV{{{name}}}"),
]


@pytest.mark.parametrize("consumer,program", ROUND_FIVE_KEYED)
@pytest.mark.parametrize("name,code", [("HOME", 0), ("ARBITRARY_TOKEN", 2)])
@pytest.mark.parametrize("input_kind", ["argv", "here-string", "quoted-heredoc", "heredoc"])
def test_round_five_keyed_literal_policy(consumer, program, name, code, input_kind):
    program = program.format(name=name)
    if input_kind == "argv":
        command = f"{consumer} --unknown {shlex.quote(program)}"
    elif input_kind == "here-string":
        command = f"{consumer} <<< {shlex.quote(program)}"
    else:
        delimiter = "'EOF'" if input_kind == "quoted-heredoc" else "EOF"
        command = f"{consumer} <<{delimiter}\n{program}\nEOF"
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == code


@pytest.mark.parametrize(
    "program",
    [
        "print(os.environ[k])",
        "print(os.environ.get(k))",
        "print(os.getenv(k))",
        'print(os.environ["HO" + "ME"])',
        'print(os.getenv("HO" + "ME"))',
        "console.log(process.env[k])",
        'console.log(process.env["HOME"]())',
        "console.log(process.env.HOME())",
        'console.log(process.env["valueOf"]?.())',
        "console.log(process.env.valueOf?.())",
        "console.log(process.env.valueOf``)",
        'console.log(process.env["valueOf"]``)',
        'print("İ"); print(os.environ)',
        "puts ENV[k]",
        "puts ENV.fetch(k)",
        "say $ENV{$k}",
        'print(os.environ.get("HOME")); print(os.environ)',
        'print(os.environ.get("HOME")); printenv',
    ],
)
def test_round_five_nonliteral_and_additional_mentions_denied(program):
    result = _subprocess_guard(f"python -c {shlex.quote(program)}")
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


@pytest.mark.parametrize(
    "program,code",
    [
        ('print( os . environ . get ( rb"HOME" ) )', 0),
        ('print(os.environ[b"HOME"])', 0),
        ("console.log(process?.env[`HOME`])", 0),
        ('print(os.en\\\nviron["HOME"])', 0),
        ('print(os.environ["HO" "ME"])', 0),
        ('print(os.environ[f"{k}"])', 2),
        ('print(os.environ["{k}"])', 2),
        ('print(os.environ.get("HOME", k))', 2),
        ('getenv("HOME")', 2),
        ('print("İ"); print(os.environ.get("HOME"))', 0),
        ("envelope = environment = myenviron = 1; print(envelope)", 0),
        ("import os as o; print(o.environ)", 2),
        ('print(getattr(os, "environ"))', 2),
        ('print(__import__("os").environ)', 2),
        ('import os as o; print(o.__dict__["en" + "viron"])', 0),
        ('print(getattr(os, "en" + "viron"))', 0),
        ('print(getattr(__import__("os"), "en" + "viron"))', 0),
    ],
)
def test_round_five_normalization_and_documented_limits(program, code):
    result = _subprocess_guard(f"python -c {shlex.quote(program)}")
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == code


@pytest.mark.parametrize("consumer", ["python", "ruby", "perl", "php", "nodejs", "lua", "deno", "bun"])
@pytest.mark.parametrize("flag", ["-uc", "-Ic", "-Bc", "-nle", "-ple", "-we", "--unknown-option="])
@pytest.mark.parametrize(
    "program,code", [('print(os.environ.get("HOME"))', 0), ("print(os.environ)", 2), ("print(1)", 0)]
)
def test_round_five_glued_options_are_opaque(consumer, flag, program, code):
    result = _subprocess_guard(f"{consumer} {flag}{shlex.quote(program)}")
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == code


# Independent commands exercise the documented API families, not generated regexes.
ROUND_SIX_INVENTORY = [
    ("python-environ", "python -c 'import os; print(os.environ)'"),
    ("python-environb", "python -c 'import os; print(os.environb)'"),
    ("python-getenv", "python -c 'import os; print(os.getenv())'"),
    ("python-getenvb", "python -c 'import os; print(os.getenvb())'"),
    ("python-posix", "python -c 'import posix; print(posix.environ)'"),
    ("python-child", "python -c 'import os; print(os.popen(\"env\").read())'"),
    ("node-env", "node -e 'console.log(process.env)'"),
    ("node-module", "node -e 'console.log(require(\"node:process\").env)'"),
    ("node-import", "node -e 'import {env} from \"node:process\"; console.log(env)'"),
    ("node-report", "node -e 'console.log(process.report.getReport())'"),
    ("node-getReport", "node -e 'const {report} = require(\"node:process\"); console.log(report.getReport())'"),
    ("node-writeReport", "node -e 'process.report.writeReport()'"),
    ("node-binding", "node -e 'console.log(process.binding(\"os\"))'"),
    ("node-builtin", "node -e 'console.log(process.getBuiltinModule(\"os\"))'"),
    ("node-child", 'node -e \'console.log(require("child_process").execSync("env"))\''),
    ("deno-env", "deno eval 'console.log(Deno.env.toObject())'"),
    ("deno-child", "deno eval 'console.log(new Deno.Command(\"env\").outputSync())'"),
    ("bun-env", "bun -e 'console.log(Bun.env)'"),
    ("bun-import-meta", "bun -e 'console.log(import.meta.env)'"),
    ("bun-child", "bun -e 'console.log(Bun.spawnSync([\"env\"]))'"),
    ("ruby-env", "ruby -e 'puts ENV.to_h'"),
    ("ruby-command-literal", "ruby -e 'puts %x{env}'"),
    ("ruby-child", "ruby -e 'puts IO.popen(\"env\").read'"),
    ("perl-env", "perl -e 'print %ENV'"),
    ("perl-command-literal", "perl -e 'print qx/env/'"),
    ("perl-child", "perl -e 'print `env`'"),
    ("php-env", "php -r 'print_r($_ENV);'"),
    ("php-server", "php -r 'print_r($_SERVER);'"),
    ("php-getenv", "php -r 'print_r(getenv());'"),
    ("php-apache", "php -r 'print_r(apache_getenv());'"),
    ("php-info", "php -r 'phpinfo();'"),
    ("php-defined", "php -r 'print_r(get_defined_vars());'"),
    ("php-globals", "php -r 'print_r($GLOBALS);'"),
    ("php-child", "php -r 'echo shell_exec(\"env\");'"),
    ("lua-getenv", "lua -e 'print(os.getenv())'"),
    ("lua-long-literal", "lua -e 'print(io.popen([=[env]=]):read())'"),
    ("lua-child", 'lua -e \'print(io.popen("env"):read("*a"))\''),
    ("awk-environ", "awk 'BEGIN{for(k in ENVIRON) print ENVIRON[k]}'"),
    ("shell-printenv", "printenv"),
    ("shell-env", "env"),
    ("shell-set", "set"),
    ("shell-export", "export -p"),
    ("shell-declare", "declare -p"),
    ("shell-typeset", "typeset -p"),
    ("shell-compgen", "compgen -e"),
    ("shell-proc", "strings /proc/self/environ"),
    ("rust-std-env", "node -e 'std::env::vars()'"),
    ("compatibility-os-env", "python -c 'print(os.env)'"),
]


@pytest.mark.parametrize("api,command", ROUND_SIX_INVENTORY, ids=[row[0] for row in ROUND_SIX_INVENTORY])
def test_round_six_inventory_denied(api, command):
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout
    assert SENTINEL not in result.stderr
    assert result.returncode == 2


ROUND_SIX_KEYED = [
    ("python-environ", "python", 'print(os.environ["{name}"])'),
    ("python-environb", "python", 'print(os.environb[b"{name}"])'),
    ("python-getenv", "python", 'print(os.getenv("{name}"))'),
    ("python-getenvb", "python", 'print(os.getenvb(b"{name}"))'),
    ("python-posix", "python", 'print(posix.environ[b"{name}"])'),
    ("node-env", "node", 'console.log(process.env["{name}"])'),
    ("node-module", "node", 'console.log(require("node:process").env["{name}"])'),
    ("deno-env", "deno", 'console.log(Deno.env.get("{name}"))'),
    ("bun-env", "bun", 'console.log(Bun.env["{name}"])'),
    ("bun-import-meta", "bun", 'console.log(import.meta.env["{name}"])'),
    ("ruby-env", "ruby", 'puts ENV["{name}"]'),
    ("perl-env", "perl", "say $ENV{{{name}}}"),
    ("php-env", "php", 'echo $_ENV["{name}"];'),
    ("php-server", "php", 'echo $_SERVER["{name}"];'),
    ("php-getenv", "php", 'echo getenv("{name}");'),
    ("php-apache", "php", 'echo apache_getenv("{name}");'),
    ("lua-getenv", "lua", 'print(os.getenv("{name}"))'),
    ("awk-environ", "awk", 'BEGIN{{print ENVIRON["{name}"]}}'),
]


@pytest.mark.parametrize("api,consumer,program", ROUND_SIX_KEYED, ids=[row[0] for row in ROUND_SIX_KEYED])
@pytest.mark.parametrize("name,code", [("HOME", 0), ("ARBITRARY_TOKEN", 2)])
@pytest.mark.parametrize("input_kind", ["argv", "heredoc"])
def test_round_six_keyed_literal_policy(api, consumer, program, name, code, input_kind):
    program = program.format(name=name)
    command = (
        f"{consumer} --unknown {shlex.quote(program)}"
        if input_kind == "argv"
        else f"{consumer} <<'EOF'\n{program}\nEOF"
    )
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == code


ROUND_SIX_NEIGHBORS = [
    "python src/env/app.py",
    "node app.js --env production",
    "node scripts/env.js",
    "deno run --allow-env main.ts",
    "python -c 'print(1)'",
    "python -c 'import os; print(os.environ.get(\"HOME\"))'",
    "node -e 'console.log(1)'",
    "ruby -e 'puts 1'",
    "python -m venv .venv",
    "git diff -- environment.yml",
    "python manage.py runserver --environment prod",
    "node -e 'let env = environment = myenviron = 1; console.log(env)'",
    "compgen -c",
    "printenv HOME",
    "declare -p HOME",
    "export -p HOME",
    "typeset -p HOME",
    "go run env.go",
    "node app.js --env env",
    "node -e 'console.log(\"env\")'",
    "python -c 'print(\"env\")'",
    "node -e 'console.log(`env`)'",
    "python -c 'print(open(\"env\").read())'",
    "lua -e 'print([[env]])'",
]


@pytest.mark.parametrize("command", ROUND_SIX_NEIGHBORS)
def test_round_six_false_positive_neighbors_allowed(command):
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 0


@pytest.mark.parametrize(
    "command",
    [
        "python -c 'import subprocess; subprocess.run([\"env\"])'",
        "python -c 'from subprocess import check_output; print(check_output([\"/usr/bin/env\"]))'",
        "python -c 'print(os.system(\"env\"))'",
        'python -c \'os.execvp("env", ["env"])\'',
        'python -c \'os.spawnlp(0, "env", "env")\'',
        'node -e \'require("child_process").spawn("env")\'',
        'node -e \'require("child_process").execFileSync("/usr/bin/env")\'',
        "bun -e 'console.log($`env`)'",
        "ruby -e 'puts Open3.capture3(\"env\")'",
        "ruby -e 'system \"env\"'",
        "ruby -e 'puts `env`'",
        "perl -e 'system \"env\"'",
        "perl -e 'print readpipe(\"env\")'",
        "php -r 'passthru(\"env\");'",
        "php -r 'echo `env`;'",
        "lua -e 'os.execute(\"env\")'",
        "python -c 'os.popen(\"true; env\").read()'",
        "node -e 'const {env} = require(\"node:process\"); console.log(env)'",
        "ruby -e 'puts %x(env)'",
        "ruby -e 'puts %x[env]'",
        "ruby -e 'puts %x<env>'",
        "ruby -e 'puts %x!env!'",
        "perl -e 'print qx{env}'",
        "perl -e 'print qx(env)'",
        "perl -e 'print qx[env]'",
        "perl -e 'print qx<env>'",
        "lua -e 'os.execute([[env]])'",
        'bun -e \'require("child_process").execSync("env")\'',
        'deno eval \'import {execSync} from "node:child_process"; console.log(execSync("env"))\'',
    ],
)
def test_round_six_child_process_api_variants_denied(command):
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


@pytest.mark.parametrize(
    "program",
    [
        "os.environb.get(k)",
        'os.getenvb(b"HO" + b"ME")',
        "posix.environ[k]",
        "Deno.env.get(k)",
        "Bun.env[k]",
        '$_ENV["HOME"]()',
        "$_SERVER[$k]",
        "getenv($k)",
        "apache_getenv($k)",
        'getenv("HOME", true)',
        'apache_getenv("HOME", true)',
        "ENVIRON[k]",
    ],
)
def test_round_six_nonliteral_lookup_denied(program):
    result = _subprocess_guard(f"php -r {shlex.quote(program)}")
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == 2


@pytest.mark.parametrize(
    "command,code",
    [
        ("python -c 'print(os.en''vironb)'", 2),
        ('node -e "console.log(process.en""v)"', 2),
        ("node -e 'console.log(process.en' 'v)'", 0),
        ("python -c 'print(os.en' 'vironb)'", 0),
        ("node --unknown 'ENV' 'HOME'", 2),
    ],
)
def test_round_six_shell_fragment_boundaries(command, code):
    result = _subprocess_guard(command)
    assert SENTINEL not in result.stdout + result.stderr
    assert result.returncode == code
