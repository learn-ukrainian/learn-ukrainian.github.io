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
    # Any quoting of the delimiter makes the body literal.
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


def test_inert_controls_stay_allowed(differential) -> None:
    heredocs, ansi_c, report = differential
    inert = [
        (case, observation)
        for case, (*_, observation) in zip(heredocs + ansi_c, report["cases"], strict=True)
        if case[2]
    ]
    assert len(inert) >= 40
    assert not [case for case, observation in inert if observation["operation_executed"]]
    assert not [case for case, observation in inert if observation["blocked"]]


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
