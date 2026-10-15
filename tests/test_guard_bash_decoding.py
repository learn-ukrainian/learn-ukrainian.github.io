"""Bash-exact reading of ANSI-C words and unquoted heredoc bodies (#10521).

The critical review of f7626455 found two P1 bypasses that every guard allowed
while real Bash ran the operation:

- an unquoted heredoc body hid an indented ``$(...)`` from the collector, because
  grammar 0.25 drops expansions after leading whitespace in heredoc bodies;
- ``$'...'`` decoding disagreed with Bash: an octal escape wraps to one byte
  (``\\547`` is ``g``), a NUL ends the quoted text and ``\\cX`` is a control byte.

Every expectation here is measured against real Bash. The decoder and heredoc
tests compare bytes with Bash's own output. The hook tests run through
``bash_oracle.run_oracle``: its private recorders log each git/gh call Bash
really makes, so an allowed row whose operation Bash executed is a miss,
whatever the reader concluded.
"""

from __future__ import annotations

import importlib.util
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HOOKS = ROOT / "agents_extensions/shared/hooks"
sys.path.insert(0, str(HOOKS))

import shell_bash

GUARDS = {"merge": "guard-pr-merge", "admin": "guard-admin-merge", "branch": "guard-branch-switch-in-main"}
OPERATIONS = {
    "branch": "git switch audit-topic",
    "merge": "gh pr merge 5 --squash",
    "admin": "gh pr merge 5 --admin",
}
BASH = ["bash", "--norc", "--noprofile"]


def _oracle():
    spec = importlib.util.spec_from_file_location("guard_decoding_oracle", ROOT / "scripts/hooks/bash_oracle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _oracle_report(cases: list[tuple[str, str]]) -> dict:
    """One oracle run; each case is (hook, command). Adds ``cases``: (hook, command, observation)."""
    rows = [
        {"id": f"decoding-{index}", "family": "decoding", "hook": hook, "command": command, "accepted": False}
        | ({"oracle_pr": "5"} if hook == "admin" else {})
        for index, (hook, command) in enumerate(cases)
    ]
    report = _oracle().run_oracle(rows=rows, traffic=[])
    observed = {observation["id"]: observation for observation in report["observations"]}
    report["cases"] = [(row["hook"], row["command"], observed[row["id"]]) for row in rows]
    return report


def _misses(report: dict) -> list[str]:
    return [f"{hook} {command!r}: {obs}" for hook, command, obs in report["cases"] if obs["miss"]]


# --------------------------------------------------------------------------- ANSI-C decoding

_WORDS = ("gh", "git", "merge", "switch", "checkout", "--admin", "audit-topic")
_ENCODINGS = (
    lambda char: char,
    lambda char: f"\\{ord(char):03o}",
    lambda char: f"\\{ord(char) + 0o400:o}",  # Bash keeps the low byte: \547 is g.
    lambda char: f"\\x{ord(char):02x}",
    lambda char: f"\\u{ord(char):04x}",
    lambda char: f"\\U{ord(char):08X}",
)
_NUL_TAILS = ("", "\\0junk", "\\x0junk", "\\x00", "\\000", "\\400tail", "\\c@x", "\\u0000x", "\\c`x")


def _encoded(word: str, rng: random.Random, tail: str = "") -> str:
    return "".join(rng.choice(_ENCODINGS)(char) for char in word) + tail


def _ansi_c_contents() -> list[str]:
    rng = random.Random(10521)
    generated = [_encoded(rng.choice(_WORDS), rng, rng.choice(_NUL_TAILS)) for _ in range(160)]
    fixed = [
        "\\a\\b\\e\\E\\f\\n\\r\\t\\v",
        "\\\\",
        "\\'",
        '\\"',
        "\\?",
        "\\q\\8\\9\\%",
        "\\x",
        "\\xg",
        "\\u",
        "\\Uz",
        "\\cA\\cz\\c?\\c[\\c]\\c^\\c_\\c1\\c~",
        "\\1234",
        "\\0101",
        "\\x41\\x4",
        "a\\\nb",
        "\\303\\251",
        "é\\q",
        "x\\x0",
    ]
    return generated + fixed


# Forms whose Bash value depends on the locale or Bash version, or is not UTF-8.
_REFUSED_ANSI_C = ["\\x{67}", "\\u00e9", "\\U0001F600", "\\c\\\\b", "\\ci", "a\\c", "\\cé", "\\xff", "\\777"]


@pytest.mark.parametrize("locale", ["C", "C.UTF-8"])
def test_ansi_c_value_matches_bash_bytes(tmp_path, locale) -> None:
    contents = _ansi_c_contents()
    script = tmp_path / "words.sh"
    script.write_text("".join(f"printf '%s\\0' $'{content}'\n" for content in contents), encoding="utf-8")
    output = subprocess.run(
        [*BASH, str(script)],
        env={"LC_ALL": locale, "PATH": "/usr/bin:/bin"},
        capture_output=True,
        check=True,
        timeout=60,
    ).stdout
    words = output.split(b"\0")[:-1]
    assert len(words) == len(contents)
    mismatched = [
        (content, word, shell_bash.ansi_c_value(content))
        for content, word in zip(contents, words, strict=True)
        if shell_bash.ansi_c_value(content) is None or shell_bash.ansi_c_value(content).encode() != word
    ]
    assert not mismatched, mismatched


def test_reviewer_ansi_c_words_decode_to_the_bytes_bash_runs() -> None:
    assert shell_bash.ansi_c_value("\\547h") == "gh"
    assert shell_bash.ansi_c_value("\\547it") == "git"
    assert shell_bash.ansi_c_value("\\555erge") == "merge"
    assert shell_bash.ansi_c_value("--admin\\0no") == "--admin"
    assert shell_bash.ansi_c_value("gh\\0ignored") == "gh"
    assert shell_bash.ansi_c_value("--\\541dmin") == "--admin"


@pytest.mark.parametrize("content", _REFUSED_ANSI_C)
def test_unprovable_ansi_c_words_refuse(content) -> None:
    assert shell_bash.ansi_c_value(content) is None


def test_numeric_reading_wraps_octal_to_one_byte() -> None:
    assert shell_bash.numeric_reading("\\547h \\555erge") == "gh merge"
    assert shell_bash.operation_shape("$'\\547h' pr $'\\555erge' 5")
    assert shell_bash.operation_candidate("$'\\547it' switch audit-topic")


# --------------------------------------------------------------------------- heredoc documents

_BODY_LINES = (
    "plain text",
    "\tone tab",
    "\t\ttwo tabs",
    "  two spaces",
    "trailing\\",
    "a \\\\ b",
    "dollar \\$HOME",
    "back\\`tick\\`",
    "quote ' \" kept",
    "$'\\x41' $\"B\" stay literal",
    "EOFX",
    "\tEOFX",
    " EOF",
    "EOF ",
    "\\",
)


def _heredoc_documents() -> list[tuple[str, str]]:
    """(command, its heredoc as Bash prints it): generated bodies without expansions."""
    rng = random.Random(9484)
    cases = []
    for operator in ("<<", "<<-"):
        for opener, closer in (("EOF", "EOF"), ("'EOF'", "EOF"), ('"EOF"', "EOF"), ("\\EOF", "EOF")):
            for _ in range(6):
                # The last line ends the body cleanly: a trailing backslash would join the delimiter.
                body = "\n".join([*rng.sample(_BODY_LINES, 5), "last line"])
                tab = "\t" if operator == "<<-" and rng.random() < 0.5 else ""
                cases.append(f"cat {operator}{opener}\n{body}\n{tab}{closer}\nprintf %s __END__")
    cases += [
        "cat <<-EOF\n\tbody\n\t\tEOF\nprintf %s __END__",
        "cat <<EOF\nbody\\\nEOF\nEOF\nprintf %s __END__",
        "cat <<'DELIM'\nbody\\\nDELIM\nprintf %s __END__",
        "cat <<EOF\n\\\\\nEOF\nprintf %s __END__",
        "cat <<EOF\nEOF\nprintf %s __END__",
    ]
    return cases


def _bash_stdout(command: str, cwd: Path) -> str:
    return subprocess.run(
        [*BASH, "-c", command],
        cwd=cwd,
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout


def test_heredoc_documents_match_bash(tmp_path) -> None:
    failures = []
    for command in _heredoc_documents():
        _tree, heredocs = shell_bash._parse(command)
        (document,) = heredocs.values()
        # Unquoted, Bash removes the backslash before `\`, `$` and a backquote, left to right.
        unescaped = document.body.replace("\\\\", "\0").replace("\\$", "$").replace("\\`", "`").replace("\0", "\\")
        expected = document.body if document.literal else unescaped
        assert not document.spans, command
        if _bash_stdout(command, tmp_path) != expected + "__END__":
            failures.append((command, expected, _bash_stdout(command, tmp_path)))
        assert ["printf", "%s", "__END__"] in shell_bash.command_argvs(command), command
    assert not failures, failures


def test_heredoc_expansions_are_read_as_words() -> None:
    _tree, heredocs = shell_bash._parse(
        "cat <<-AUDIT\n\t$(git switch audit-topic) `echo a` ${x:-$(echo b)} $((1+2)) $HOME \\$(no) '$(q)'\n\tAUDIT"
    )
    (document,) = heredocs.values()
    assert document.spans == (
        "$(git switch audit-topic)",
        "`echo a`",
        "${x:-$(echo b)}",
        "$((1+2))",
        "$HOME",
        "$(q)",
    )
    argvs = shell_bash.command_argvs("cat <<A\n\t$(git switch audit-topic)\nA")
    assert ["git", "switch", "audit-topic"] in argvs


@pytest.mark.parametrize(
    "command",
    [
        "cat <<A\n$(echo a\nA\n)\nA",  # the delimiter ends the body inside the substitution
        "cat <<A\n${x:-'a}'}\nA",  # quotes inside ${...} differ by Bash version and mode
        "cat <<A\n`echo a\nA",
        "cat <<A\n$(echo a\nA",
        "cat <<A\nbody",  # Bash reads to the end of input, which a harness may extend
        "cat <<GUARD_HERE_1U\nx\nGUARD_HERE_1U",
        # Bash ends this body at the joined line `DELIM`; grammar 0.25 sees no end and the
        # opener lands in an ERROR node, so the reader cannot establish the body and refuses.
        "cat <<DELIM\nbody\nDE\\\nLIM\nprintf %s __END__",
    ],
)
def test_unreadable_heredoc_bodies_refuse(command) -> None:
    with pytest.raises(shell_bash.ShellParseError):
        shell_bash.command_argvs(command)


# --------------------------------------------------------------------------- reviewer reproducers

_REVIEWER_HEREDOC = [
    "cat <<-AUDIT\n\t$({op})\n\tAUDIT",
    "cat <<-AUDIT\n$({op})\nAUDIT",
    "cat <<AUDIT\n\t$({op})\nAUDIT",
    "cat <<-AUDIT\n\t$({op})\nAUDIT",
    "cat <<AUDIT\n$({op})\nAUDIT",
    "cat <<-AUDIT\n\t`{op}`\n\tAUDIT",
]
_REVIEWER_ANSI_C = [
    ("merge", "$'\\547h' pr merge 5 --squash"),
    ("admin", "$'\\547h' pr merge 5 --admin"),
    ("merge", "$'g\\550' pr merge 5 --squash"),
    ("branch", "$'\\547it' switch audit-topic"),
    ("branch", "$'g\\551t' checkout -B audit-topic"),
    ("merge", "gh pr $'\\555erge' 5 --squash"),
    ("admin", "gh pr $'\\555erge' 5 --admin"),
    ("admin", "gh pr merge 5 $'--\\541dmin'"),
    ("branch", "$'git\\0other' switch audit-topic"),
    ("admin", "gh pr merge 5 $'--admin\\0no'"),
    ("merge", "$'g\\x68' pr merge 5 --squash"),
]


@pytest.fixture(scope="module")
def reviewer_report() -> dict:
    cases = [(hook, form.format(op=OPERATIONS[hook])) for form in _REVIEWER_HEREDOC for hook in OPERATIONS]
    cases += [("branch", form.format(op="git checkout -B audit-topic")) for form in _REVIEWER_HEREDOC]
    return _oracle_report(cases + _REVIEWER_ANSI_C)


def test_reviewer_reproducers_execute_in_bash_and_block(reviewer_report) -> None:
    for hook, command, observation in reviewer_report["cases"]:
        assert observation["operation_executed"], (hook, command, observation)
        assert observation["blocked"], (hook, command, observation)
    assert not _misses(reviewer_report)


# --------------------------------------------------------------------------- generated differential


def _heredoc_differential() -> list[tuple[str, str, bool]]:
    """(hook, command, inert): Bash runs the operation unless the case is inert."""
    forms = (
        ("$({op})", False),
        ("`{op}`", False),
        ("${{unset:-$({op})}}", False),
        ("$((0*$({op}; echo 1)))", False),
        ("x $({op}) y", False),
        ("'$({op})'", False),
        ('"$({op})"', False),
        ("\\\\$({op})", False),
        ("$(echo $({op}))", False),
        ("\\$({op})", True),
    )
    hooks = tuple(OPERATIONS)
    cases = []
    index = 0
    # Unquoted openers: every form after every leading whitespace the grammar mishandles.
    for form, escaped in forms:
        for opener in ("<<AUDIT", "<<-AUDIT"):
            for prefix in ("", "\t", "\t\t", "  "):
                hook = hooks[index % 3]
                closer = "\tAUDIT" if opener == "<<-AUDIT" and index % 2 else "AUDIT"
                cases.append((hook, f"cat {opener}\n{prefix}{form.format(op=OPERATIONS[hook])}\n{closer}", escaped))
                index += 1
    # Any quoting of the delimiter makes the body literal. The merge and admin
    # guards still refuse `<<\AUDIT` (see _main_parity_refusal).
    for form, _escaped in forms:
        for opener in ("<<'AUDIT'", '<<"AUDIT"', "<<\\AUDIT", "<<-'AUDIT'"):
            hook = hooks[index % 3]
            cases.append((hook, f"cat {opener}\n\t{form.format(op=OPERATIONS[hook])}\nAUDIT", True))
            index += 1
    for hook in hooks:
        op = OPERATIONS[hook]
        cases += [
            (hook, f"cat <<A /dev/fd/3 3<<B\nx\nA\n\t$({op})\nB", False),
            (hook, f'echo "$(cat <<A\n\t$({op})\nA\n)"', False),
            (hook, f"f() {{ cat <<A\n\t$({op})\nA\n}}; f", False),
            (hook, f"cat <<A\n$(true\n{op})\nA", False),
            (hook, f"cat <<A\n\t$(true \\\n; {op})\nA", False),
            (hook, f"cat <<A\nA\n{op}", False),
            (hook, f"cat <<A\n$(echo a\nA\n{op}\n)\nA", False),
            (hook, f"bash <<A\n\\\n{op}\nA", False),
            (hook, f"while read -r l; do :; done <<A\n\t$({op})\nA", False),
            (hook, f"{{ cat; }} <<-A\n\t$({op})\n\tA", False),
            (hook, f"cat <<'A' <<B\n$({op})\nA\n\t$({op})\nB", False),
            (hook, f"cat <<'A'\n{op}\nA", True),
            (hook, f"cat <<'A'\n\\\\$({op})\nA", True),
            (hook, f"cat <<A <<'B'\nx\nA\n\t$({op})\nB", True),
        ]
    return cases


def _ansi_c_differential() -> list[tuple[str, str, bool]]:
    """(hook, command, inert): words spelled with Bash ANSI-C escapes, plus inert controls."""
    rng = random.Random(1052)
    templates = {
        "branch": ("{git} switch audit-topic", "git {switch} audit-topic", "{git} checkout -B audit-topic"),
        "merge": ("{gh} pr merge 5 --squash", "gh pr {merge} 5 --squash"),
        "admin": ("{gh} pr merge 5 --admin", "gh pr merge 5 {--admin}", "gh pr {merge} 5 --admin"),
    }
    cases = []
    for hook, forms in templates.items():
        for _ in range(16):
            form = rng.choice(forms)
            word = form[form.index("{") + 1 : form.index("}")]
            split = rng.randrange(len(word) + 1)
            spelled = f"$'{_encoded(word[:split], rng, rng.choice(_NUL_TAILS))}'{word[split:]}"
            cases.append((hook, form.replace("{" + word + "}", spelled), False))
        target = "git" if hook == "branch" else "gh"
        last = ord(target[-1])
        for spelled in (f"{target[:-1]}\\x{{{last:x}}}", f"{target[:-1]}\\u{last:04x}", f"{target}\\c@x"):
            cases.append((hook, forms[0].replace("{" + target + "}", f"$'{spelled}'"), False))
    cases += [
        ("merge", "$'\\547x' pr merge 5 --squash", True),
        ("admin", "gh pr merge 5 $'--\\541dmix'", True),
        ("branch", "$'\\547ix' switch audit-topic", True),
        ("branch", "echo $'\\547it switch audit-topic'", True),
        ("merge", "printf '%s\\n' $'\\547h pr merge 5'", True),
    ]
    return cases


@pytest.fixture(scope="module")
def differential() -> tuple[list, list, dict]:
    heredocs, ansi_c = _heredoc_differential(), _ansi_c_differential()
    report = _oracle_report([(hook, command) for hook, command, _inert in heredocs + ansi_c])
    return heredocs, ansi_c, report


def test_generated_differential_has_forty_executing_cases_per_blocker(differential) -> None:
    heredocs, ansi_c, report = differential
    observed = [observation for _hook, _command, observation in report["cases"]]
    for cases, observations in ((heredocs, observed[: len(heredocs)]), (ansi_c, observed[len(heredocs) :])):
        operations = [obs for (_hook, _command, inert), obs in zip(cases, observations, strict=True) if not inert]
        assert len(operations) >= 40
        assert all(obs["operation_executed"] for obs in operations), "every generated operation must run in Bash"


def test_generated_heredoc_and_ansi_c_cases_have_no_miss(differential) -> None:
    _heredocs, _ansi_c, report = differential
    assert not _misses(report), "\n".join(_misses(report))
    assert report["failures"] == []


def _main_parity_refusal(hook: str, command: str) -> bool:
    """Inert in Bash, yet origin/main's merge and admin guards refuse it (review-10521-70a19bba).

    Main's merge guards read a `<<\\WORD` body as commands, so the frozen
    main-parity rule keeps their refusal; main's branch guard reads it as Bash does.
    """
    return hook != "branch" and "<<\\" in command


def test_inert_controls_stay_allowed(differential) -> None:
    heredocs, ansi_c, report = differential
    inert = [
        (case, observation)
        for case, (*_, observation) in zip(heredocs + ansi_c, report["cases"], strict=True)
        if case[2]
    ]
    assert len(inert) >= 40
    assert not [case for case, observation in inert if observation["operation_executed"]]
    refused = [(case, observation) for case, observation in inert if _main_parity_refusal(*case[:2])]
    assert len(refused) == 7
    assert all(observation["blocked"] for _case, observation in refused)
    assert not [case for case, observation in inert if observation["blocked"] and not _main_parity_refusal(*case[:2])]


# --------------------------------------------------------------------------- siblings of the same class

_SIBLINGS = [
    ("merge", "gh pr {merge,} 5 --squash"),
    ("admin", "gh pr merge 5 {--admin,}"),
    ("branch", "git {switch,} audit-topic"),
    ("branch", "{git,} switch audit-topic"),
    ("merge", '$"gh" pr merge 5 --squash'),
    ("admin", 'gh pr merge 5 --$"admin"'),
    ("branch", 'git $"switch" audit-topic'),
    ("merge", "x='; gh pr merge 5 --squash'; bash <<EOF\necho $x\nEOF"),
    ("branch", "x='; git switch audit-topic'; sh <<-EOF\n\techo $x\n\tEOF"),
    ("admin", "export x=gh; bash <<EOF\n\\$x pr merge 5 --admin\nEOF"),
]


def test_sibling_decodings_block() -> None:
    report = _oracle_report(_SIBLINGS)
    for hook, command, observation in report["cases"]:
        assert observation["operation_executed"], (hook, command, observation)
        assert observation["blocked"], (hook, command, observation)
    assert not _misses(report)


def test_heldout_attribution_names_the_decoding_ruling() -> None:
    from scripts.hooks import guard_main_parity as parity

    row = {"id": "pm-decoded-word-001", "class": "decoded_word", "command": "$'\\547h' pr merge --squash 5"}
    exact = parity.attribute(row, parity.Run(2, None, True, False, True))
    refused = parity.attribute(row, parity.Run(2, "DYNAMIC_OPERATION", False, False, False))
    assert (exact["ruling_item"], refused["ruling_item"]) == ("1", "2")
    assert "decodes" in exact["why"] and "cannot prove" in refused["why"]


# --------------------------------------------------------------------------- main-parity refusals

# The review of 70a19bba (review-10521-70a19bba) found two inert forms that
# origin/main's merge and admin guards refuse and this reader allowed. The frozen
# contract keeps every main refusal, so both refuse again.
#
# 1. A backslash-escaped heredoc delimiter makes the body literal in Bash, and
#    main's branch guard reads it so. Main's merge and admin guards do not: they
#    read the body as commands and refuse an operation spelled there. The merge
#    and admin guards therefore refuse the delimiter; the branch guard keeps
#    Bash's reading, which main's own branch tests (#9479) require.
# 2. A command name holding a non-printing character, such as the BEL of
#    ``$'\cG'``, names no utility the reader can prove. The head before
#    70a19bba refused it as DYNAMIC_COMMAND; it refuses so again.

_ESCAPED_DELIMITER_FORMS = [
    "cat <<\\BOUND\n$({op})\nBOUND",
    "cat <<-\\BOUND\n\t$({op})\n\tBOUND",
    "cat << \\BOUND\n$({op})\nBOUND",
    "cat <<\\BOUND\n\t$({op})\nBOUND",
    "cat <<\\BOUND\n{op}\nBOUND",
    "cat <<\\BOUND\nuse `{op}` later\nBOUND",
    "x=$(cat <<\\BOUND\n$({op})\nBOUND\n); :",
    "cat <<A <<\\BOUND\nx\nA\n$({op})\nBOUND",
    "echo `cat <<\\\\BOUND\n$({op})\nBOUND`",
]


@pytest.fixture(scope="module")
def escaped_delimiter_report() -> dict:
    cases = [(hook, form.format(op=OPERATIONS[hook])) for form in _ESCAPED_DELIMITER_FORMS for hook in OPERATIONS]
    return _oracle_report(cases)


def test_escaped_heredoc_delimiter_is_inert_and_refused_by_merge_guards(escaped_delimiter_report) -> None:
    for hook, command, observation in escaped_delimiter_report["cases"]:
        assert not observation["operation_executed"], (hook, command, observation)
        if hook != "branch":
            assert observation["blocked"], (hook, command, observation)


def test_escaped_heredoc_delimiter_keeps_the_branch_guards_bash_reading() -> None:
    command = "git commit -F - <<\\EOF\nuses `git checkout -b x` in text\nEOF"
    with pytest.raises(shell_bash.ShellParseError, match="ambiguous heredoc delimiter"):
        shell_bash.read_commands(command, operation=lambda argv: False)
    rows = shell_bash.read_commands(command, operation=lambda argv: False, allow_escaped_heredoc_delimiters=True)
    quoted = shell_bash.read_commands(command.replace("<<\\EOF", "<<'EOF'"), operation=lambda argv: False)
    assert [row.argv for row in rows] == [row.argv for row in quoted]
    _tree, heredocs = shell_bash._parse("cat <<\\EOF\n$(x)\nEOF")
    (document,) = heredocs.values()
    assert document.literal and document.escaped and not document.spans


@pytest.mark.parametrize("opener", ["'BOUND'", '"BOUND"', "-'BOUND'", ' "BOUND"', "BOUND"])
def test_whole_quoted_and_plain_delimiters_are_not_escaped(opener) -> None:
    rows = shell_bash.read_commands(f"cat <<{opener}\nbody\n{chr(9) if opener.startswith('-') else ''}BOUND")
    assert [row.argv for row in rows] == [["cat"]]


# The review of 3c85a581 (review-10521-redo-3c85a581) found a quoted delimiter that
# starts with a digit (`'9_Z'`) read as literal, while origin/main's merge and admin
# guards find no closer for it and read the body as commands. Only an identifier, as
# main's guards define one, bare, quoted whole or escaped, is a literal delimiter; any
# other spelling refuses in every guard. Each pair is (opener, the closer Bash 5.3 uses).
_OUTSIDE_THE_ALLOWLIST = [
    # a digit first, quoted and unquoted
    ("'9_Z'", "9_Z"), ('"9_Z"', "9_Z"), ("'9'", "9"), ('"9"', "9"), ("'123'", "123"), ('"123"', "123"),
    ("'9Z'", "9Z"), ('"9Z"', "9Z"), ("'0_A'", "0_A"), ('"0_A"', "0_A"), ("9_Z", "9_Z"), ("9", "9"),
    ("123", "123"), ("9Z", "9Z"), ("0_A", "0_A"), ("'9_'", "9_"), ("9_", "9_"), ("'0'", "0"), ('"0"', "0"),
    ("'00'", "00"), ("0", "0"), ("'1EOF'", "1EOF"), ("1EOF", "1EOF"),
    # escaped
    ("\\9Z", "9Z"), ("\\9", "9"), ("\\0_A", "0_A"), ("\\\\A", "\\A"), ("\\E\\O\\F", "EOF"), ("\\-", "-"),
    ("\\'A\\'", "'A'"),
    # mixed quoting and concatenation
    ("'9'Z", "9Z"), ('"A"B', "AB"), ("A\\B", "AB"), ("E\\OF", "EOF"), ("'A'B", "AB"), ("A'B'", "AB"),
    ('A"B"', "AB"), ("'A'\"B\"", "AB"), ("'9'\"Z\"", "9Z"), ("9'Z'", "9Z"), ("'EO'F", "EOF"),
    ("\"EO\"'F'", "EOF"), ("'A''B'", "AB"), ('"A""B"', "AB"), ("A\\'\\'", "A''"), ("'\\A'", "\\A"),
    # $'...' and $"..."
    ("$'EOF'", "EOF"), ('$"EOF"', "EOF"), ("$'9Z'", "9Z"), ("$'\\x45OF'", "EOF"), ("EO$'F'", "EOF"),
    ("$'E'OF", "EOF"), ("$'A'", "A"), ('$"A"', "A"), ("$'_9'", "_9"),
    # a hyphen, dot, space or non-ASCII character
    ("A-B", "A-B"), ("'A-B'", "A-B"), ('"A-B"', "A-B"), ("A.B", "A.B"), ("'A.B'", "A.B"), ('"A.B"', "A.B"),
    ("'a-'", "a-"), ("'-'", "-"), ("'.'", "."), ("'A B'", "A B"), ("'A\tB'", "A\tB"), ("É", "É"),
    ("'É'", "É"), ('"É"', "É"), ("'é'", "é"), ("'ЕОФ'", "ЕОФ"), ("ЕОФ", "ЕОФ"), ("'Ⅸ'", "Ⅸ"),
    ("'٩'", "٩"), ("'Ａ'", "Ａ"), ("Ａ", "Ａ"),
    # empty
    ("''", ""), ('""', ""),
    # other shell characters
    ("{A}", "{A}"), ("A}", "A}"), ("$A", "$A"), ("${A}", "${A}"), ("`A`", "`A`"), ("~A", "~A"),
    ("A*", "A*"), ("A?", "A?"), ("[A]", "[A]"), ("!A", "!A"), ("%A", "%A"), ("A=B", "A=B"), ("A:B", "A:B"),
    ("A,B", "A,B"), ("A@", "A@"), ("+A", "+A"), ("A/B", "A/B"), ("A$", "A$"),
]  # fmt: skip
# Identifiers main's guards admit too: a leading underscore is a letter there.
_ALLOWLISTED = [
    ("_X", "_X"), ("_", "_"), ("Z", "Z"), ("A9", "A9"), ("EOF1", "EOF1"), ("'_9'", "_9"), ('"_"', "_"),
    ("'_1'", "_1"), ("'Z'", "Z"), ('"A9"', "A9"), ("\\_A", "_A"), ("\\EOF", "EOF"),
]  # fmt: skip


@pytest.mark.parametrize("opener,closer", _OUTSIDE_THE_ALLOWLIST)
def test_delimiter_outside_the_allowlist_refuses(opener, closer) -> None:
    with pytest.raises(shell_bash.ShellParseError):
        shell_bash.read_commands(f"cat <<{opener}\nbody\n{closer}", allow_escaped_heredoc_delimiters=True)


@pytest.mark.parametrize("opener,closer", _ALLOWLISTED)
def test_allowlisted_delimiter_is_read(opener, closer) -> None:
    _tree, heredocs = shell_bash._parse(f"cat <<{opener}\nbody\n{closer}")
    (document,) = heredocs.values()
    assert document.body == "body\n"
    assert document.literal == (opener[0] in "'\"\\")


def test_delimiter_allowlist_is_mains_identifier() -> None:
    """The one definition admits exactly what origin/main's shell_shlex reads as a closer.

    Main also reads `\\WORD` as ambiguous; the reader admits it with the identifier
    rule and the escaped flag refuses it in the merge and admin guards.
    """
    import shell_shlex

    def mains(word: str) -> bool:
        whole = len(word) >= 3 and word[0] in "'\"" and word[-1] == word[0]
        return bool(shell_shlex._HEREDOC_IDENTIFIER.fullmatch(word[1:-1] if whole else word))

    words = {opener for opener, _closer in _OUTSIDE_THE_ALLOWLIST + _ALLOWLISTED}
    words |= {f"{quote}{core}{quote}" for core in ("A", "_", "9", "A-B", "") for quote in ("", "'", '"')}
    for word in words:
        expected = mains(word[1:]) and word[1] not in "'\"" if word.startswith("\\") else mains(word)
        assert bool(shell_bash._HEREDOC_DELIMITER.fullmatch(word.encode())) == expected, word


@pytest.fixture(scope="module")
def delimiter_report() -> dict:
    cases = []
    for opener, closer in _OUTSIDE_THE_ALLOWLIST + _ALLOWLISTED:
        cases += [
            ("merge", f"cat <<{opener}\n$({OPERATIONS['merge']})\n{closer}"),
            ("admin", f"cat <<{opener}\n$({OPERATIONS['admin']})\n{closer}"),
            ("branch", f"cat <<{opener}\n$({OPERATIONS['branch']})\n{closer}"),
        ]
    return _oracle_report(cases)


def test_delimiter_outside_the_allowlist_refuses_in_every_guard(delimiter_report) -> None:
    assert not _misses(delimiter_report)
    outside = 3 * len(_OUTSIDE_THE_ALLOWLIST)
    for hook, command, observation in delimiter_report["cases"][:outside]:
        assert observation["blocked"], (hook, command, observation)


def test_allowlisted_delimiters_keep_their_reading(delimiter_report) -> None:
    outside = 3 * len(_OUTSIDE_THE_ALLOWLIST)
    for hook, command, observation in delimiter_report["cases"][outside:]:
        opener = command.split("\n", 1)[0].removeprefix("cat <<")
        # An unquoted body runs its substitution; a quoted one is data; `\WORD` refuses in the merge guards.
        executes = opener[0] not in "'\"\\"
        assert observation["operation_executed"] == executes, (hook, command, observation)
        refuses = executes or (opener[0] == "\\" and hook != "branch")
        assert observation["blocked"] == refuses, (hook, command, observation)


_CONTROL_ESCAPES = [
    "\\cG", "\\cA", "\\c[", "\\c?", "\\a", "\\b", "\\e", "\\E", "\\f", "\\n", "\\r", "\\t", "\\v",
    "\\x01", "\\x1f", "\\x7f", "\\001", "\\177", "\\u0007", "\\U0000001b",
]  # fmt: skip
# A NUL ends the quoted text: before any other character it leaves an empty command name.
_NUL_ESCAPES = ["\\0", "\\000", "\\x00", "\\c@", "\\u0000"]
_CONTROL_NAME_FORMS = [
    "$'{esc}' pr merge 5 --admin",
    "$'{esc}gh' pr merge 5 --admin",
    "$'gh{esc}' pr merge 5 --admin",
    "command $'{esc}' pr merge 5 --admin",
    "env $'{esc}' pr merge 5 --squash",
]
_DYNAMIC_NAMES = [form.format(esc=esc) for form in _CONTROL_NAME_FORMS for esc in _CONTROL_ESCAPES] + [
    form.format(esc=esc) for form in _CONTROL_NAME_FORMS if "gh{esc}" not in form for esc in _NUL_ESCAPES
]


@pytest.mark.parametrize("command", _DYNAMIC_NAMES)
def test_command_name_with_a_decoded_control_character_is_dynamic(command) -> None:
    with pytest.raises(shell_bash.ShellParseError) as refused:
        shell_bash.read_commands(command)
    assert refused.value.reason_class == "DYNAMIC_COMMAND"


@pytest.fixture(scope="module")
def control_name_report() -> dict:
    forms = [*_CONTROL_NAME_FORMS[:4], "gh $'{esc}pr' merge 5 --admin", "gh $'{esc}' pr merge 5 --admin"]
    cases = []
    for index, esc in enumerate(_CONTROL_ESCAPES):
        command = forms[index % len(forms)].format(esc=esc)
        cases += [("merge", command.replace("--admin", "--squash")), ("admin", command)]
    for esc in _NUL_ESCAPES:
        cases += [("merge", f"$'{esc}' pr merge 5 --squash"), ("admin", f"command $'{esc}gh' pr merge 5 --admin")]
    return _oracle_report(cases)


def test_control_character_command_words_are_inert_and_refused(control_name_report) -> None:
    for hook, command, observation in control_name_report["cases"]:
        assert not observation["operation_executed"], (hook, command, observation)
        assert observation["blocked"], (hook, command, observation)


# --------------------------------------------------------------------------- degraded runtime


@pytest.mark.parametrize(
    "hook,command",
    [
        ("branch", "$'\\547it' switch audit-topic"),
        ("branch", "$'g\\551t' checkout -B audit-topic"),
        ("branch", "git $'s\\0junk'witch audit-topic"),
        ("merge", "$'\\547h' pr merge 5 --squash"),
        ("merge", "gh pr $'m\\x{65}rge' 5"),
        ("admin", "$'\\547h' pr merge 5 --admin"),
        ("admin", "gh pr merge 5 $'--admin\\0no'"),
    ],
)
def test_parser_import_failure_cannot_allow_a_decoded_operation(tmp_path, hook, command) -> None:
    guard_copy = tmp_path / f"{GUARDS[hook]}.py"
    shutil.copy2(HOOKS / guard_copy.name, guard_copy)
    result = subprocess.run(
        [sys.executable, str(guard_copy)],
        input=json.dumps({"tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 2, result.stderr
    assert "guard dependency unavailable: shell_bash" in result.stderr
