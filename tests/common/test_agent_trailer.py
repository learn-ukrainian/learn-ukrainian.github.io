"""The shared X-Agent recogniser agrees with git's trailer parser (#10450)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.common.agent_trailer import AgentTrailerError, x_agent_trailers

REFUSE = "refuse"

# (message, recogniser values or REFUSE, values `git interpret-trailers --parse --no-divider` reports).
CASES: dict[str, tuple[str, tuple[str, ...] | str, tuple[str, ...]]] = {
    "canonical": ("feat: x\n\nX-Agent: codex/one\n", ("codex/one",), ("codex/one",)),
    "lower-case": (
        "feat: x\n\nX-Agent: codex/one\nx-agent: claude/two\n",
        ("codex/one", "claude/two"),
        ("codex/one", "claude/two"),
    ),
    "upper-case": ("feat: x\n\nX-AGENT: claude/two\n", ("claude/two",), ("claude/two",)),
    "mixed-case": (
        "feat: x\n\nX-Agent: codex/one\nx-AgEnT: claude/two\n",
        ("codex/one", "claude/two"),
        ("codex/one", "claude/two"),
    ),
    "space-before-colon": ("feat: x\n\nX-Agent : claude/two\n", ("claude/two",), ("claude/two",)),
    "tab-before-colon": ("feat: x\n\nX-Agent\t: claude/two\n", ("claude/two",), ("claude/two",)),
    "tab-after-colon": ("feat: x\n\nX-Agent:\tclaude/two\n", ("claude/two",), ("claude/two",)),
    "no-space-after-colon": ("feat: x\n\nX-Agent:claude/two\n", ("claude/two",), ("claude/two",)),
    "crlf": (
        "feat: x\r\n\r\nX-Agent: codex/one\r\nx-agent: claude/two\r\n",
        ("codex/one", "claude/two"),
        ("codex/one", "claude/two"),
    ),
    "blank-value": ("feat: x\n\nX-Agent:\nX-Agent: codex/one\n", ("", "codex/one"), ("", "codex/one")),
    "beside-other-trailers": (
        "feat: x\n\nX-Agent: codex/one\nCo-Authored-By: C <c@example.invalid>\n",
        ("codex/one",),
        ("codex/one",),
    ),
    # git's trailer block is the last paragraph; the recogniser also reads earlier ones (squash merges).
    "earlier-paragraph": (
        "feat: x\n\nX-Agent: claude/two\n\nCo-Authored-By: C <c@example.invalid>\n",
        ("claude/two",),
        (),
    ),
    "prose-paragraph": ("feat: x\n\nX-Agent: claude/two\nsome prose\n", ("claude/two",), ()),
    "comment-line": ("feat: x\n\n# X-Agent: claude/two\nX-Agent: codex/one\n", ("codex/one",), ("codex/one",)),
    "prose-after-key": (
        "feat: x\n\nX-Agent trailers are parsed now.\n\nX-Agent: codex/one\n",
        ("codex/one",),
        ("codex/one",),
    ),
    "longer-key": ("feat: x\n\nX-Agent-Model: claude-opus-5-5\nX-Agent: codex/one\n", ("codex/one",), ("codex/one",)),
    "underscore": ("feat: x\n\nX-Agent: codex/one\nX_Agent: claude/two\n", REFUSE, ()),
    "space-in-key": ("feat: x\n\nX Agent: claude/two\nX-Agent: codex/one\n", REFUSE, ()),
    "no-hyphen": ("feat: x\n\nX-Agent: codex/one\nXAgent: claude/two\n", REFUSE, ("codex/one",)),
    "equals": ("feat: x\n\nX-Agent= claude/two\nX-Agent: codex/one\n", REFUSE, ()),
    "no-separator": ("feat: x\n\nX-Agent: codex/one\nX-Agent claude/two\n", REFUSE, ()),
    "indented": ("feat: x\n\nX-Agent: codex/one\n X-Agent: claude/two\n", REFUSE, ("codex/one X-Agent: claude/two",)),
    "folded-value": ("feat: x\n\nX-Agent: codex/one\n two\n", REFUSE, ("codex/one two",)),
    "loose-only": ("feat: x\n\nx_agent: claude/two\n", REFUSE, ()),
}


def _git_x_agent_values(message: str, cwd: Path) -> tuple[str, ...]:
    """Ask git with no system, global or repository configuration (trailer.* settings change parsing)."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_CEILING_DIRECTORIES=str(cwd.parent))
    parsed = subprocess.run(
        ["git", "interpret-trailers", "--parse", "--no-divider"],
        input=message.encode(),
        cwd=cwd,
        env=env,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout.decode()
    values = []
    for line in parsed.split("\n"):
        key, separator, value = line.partition(":")
        if separator and key.strip().lower() == "x-agent":
            values.append(value.strip())
    return tuple(values)


@pytest.mark.parametrize("case", sorted(CASES))
def test_recogniser_matches_git_and_refuses_what_git_does_not_parse(tmp_path, case):
    message, expected, git_expected = CASES[case]
    git_values = _git_x_agent_values(message, tmp_path)
    assert git_values == git_expected
    if expected == REFUSE:
        with pytest.raises(AgentTrailerError):
            x_agent_trailers(message)
        return
    values = tuple(trailer.value for trailer in x_agent_trailers(message))
    assert values == expected
    # Every X-Agent trailer git parses is attributed, in git's order.
    remaining = iter(values)
    assert all(value in remaining for value in git_values)


def test_trailer_keeps_its_stripped_line_and_value():
    (trailer,) = x_agent_trailers("feat: x\n\nX-Agent :\tcodex/one \r\n")
    assert (trailer.line, trailer.value) == ("X-Agent :\tcodex/one", "codex/one")


def test_a_message_without_x_agent_lines_has_no_trailers():
    assert x_agent_trailers("feat: x\n\nCo-Authored-By: C <c@example.invalid>\n") == ()
    assert x_agent_trailers("") == ()


def test_only_newline_separates_lines_as_in_git():
    """git splits on LF only, so a Unicode line separator never starts a new trailer line."""
    trailers = x_agent_trailers("feat: x\n\nNote: a X-Agent: claude/two\nX-Agent: codex/one\n")
    assert [each.value for each in trailers] == ["codex/one"]


def test_a_blank_next_line_is_not_a_continuation():
    assert [each.value for each in x_agent_trailers("feat: x\n\nX-Agent: codex/one\n \t\nmore\n")] == ["codex/one"]


# --- Attempt detection: any line that reads as an X-Agent trailer but is not git's key refuses (#10450) ---

NBSP, ZWSP, ZWJ, BOM, FULLWIDTH_COLON = " ", "​", "‍", "﻿", "："

# (line, class). Each is a trailer attempt git does not parse as the X-Agent key.
ATTEMPTS: dict[str, tuple[str, str]] = {
    "nbsp-before-colon": (f"X-Agent{NBSP}: claude/two", "non-ASCII or control characters"),
    "nbsp-after-key": (f"X-Agent{NBSP}claude/two", "non-ASCII or control characters"),
    "ideographic-space-before-colon": ("X-Agent　: claude/two", "non-ASCII or control characters"),
    "zero-width-prefix": (f"{ZWSP}X-Agent: claude/two", "non-ASCII or control characters"),
    "zero-width-inside-key": (f"X-{ZWSP}Agent: claude/two", "non-ASCII or control characters"),
    "zero-width-joiner-inside-word": (f"X-Ag{ZWJ}ent: claude/two", "non-ASCII or control characters"),
    "byte-order-mark-prefix": (f"{BOM}X-Agent: claude/two", "non-ASCII or control characters"),
    "fullwidth-colon": (f"X-Agent{FULLWIDTH_COLON} claude/two", "non-ASCII or control characters"),
    "fullwidth-letters": ("Ｘ-Ａgent: claude/two", "non-ASCII or control characters"),
    "combining-mark-in-key": ("X-Agent́: claude/two", "non-ASCII or control characters"),
    "control-character-in-key": ("X-\x00Agent: claude/two", "non-ASCII or control characters"),
    "ascii-no-colon": ("X-Agent claude/two trailing", "no separator"),
    "ascii-no-colon-lower": ("x-agent claude/two", "no separator"),
    "equals": ("X-Agent= claude/two", "separator other than a colon"),
    "underscore": ("X_Agent: claude/two", "key spelling"),
    "space-in-key": ("X Agent: claude/two", "key spelling"),
    "no-hyphen": ("XAgent: claude/two", "key spelling"),
    "dot-in-key": ("X.Agent: claude/two", "key spelling"),
    "indented": (" X-Agent: claude/two", "indented"),
    "tab-indented": ("\tx-agent: claude/two", "indented"),
}


@pytest.mark.parametrize("name", sorted(ATTEMPTS))
@pytest.mark.parametrize("placement", ["alone", "before-valid", "after-valid", "other-paragraph"])
def test_a_trailer_attempt_in_any_other_form_refuses_with_line_and_class(name, placement):
    line, attempt_class = ATTEMPTS[name]
    layouts = {
        "alone": ("feat: x\n\n" + line + "\n", 3),
        "before-valid": ("feat: x\n\n" + line + "\nX-Agent: codex/one\n", 3),
        "after-valid": ("feat: x\n\nX-Agent: codex/one\n" + line + "\n", 4),
        "other-paragraph": ("feat: x\n\nX-Agent: codex/one\n\nprose\n\n" + line + "\n", 7),
    }
    message, line_number = layouts[placement]
    with pytest.raises(AgentTrailerError) as raised:
        x_agent_trailers(message)
    error = raised.value
    if placement == "after-valid" and attempt_class == "indented":
        attempt_class = "continuation"  # git folds an indented line into the trailer value above it
    assert (error.line_number, error.attempt_class) == (line_number, attempt_class)
    # The typed refusal names the line and the class, never the raw value.
    assert f"line {error.line_number}" in str(error)
    assert error.attempt_class in str(error)
    assert "claude" not in str(error) and "two" not in str(error)


# (line, expected recogniser values) controls: round-2 behaviour must not move.
CONTROLS: dict[str, tuple[str, tuple[str, ...]]] = {
    "canonical": ("X-Agent: claude/two", ("claude/two",)),
    "lower-case": ("x-agent: claude/two", ("claude/two",)),
    "upper-case": ("X-AGENT: claude/two", ("claude/two",)),
    "space-before-colon": ("X-Agent : claude/two", ("claude/two",)),
    "tab-before-colon": ("X-Agent\t: claude/two", ("claude/two",)),
    "nbsp-in-value": (f"X-Agent: claude/two{NBSP}", (f"claude/two{NBSP}",)),
    "longer-key": ("X-Agent-Model: claude-opus-5-5", ()),
    "longer-key-colon-space": ("x-agent-model : claude-opus-5-5", ()),
    "plural-key": ("x-agents: plural keys are other trailers", ()),
    "comment": ("# X-Agent: claude/two", ()),
    "comment-nbsp": (f"# X-Agent{NBSP}: claude/two", ()),
    "markdown-quote": ("> X-Agent: claude/two", ()),
    "markdown-quote-nbsp": (f"> X-Agent{NBSP}: claude/two", ()),
    "mid-line-prose": ("The X-Agent: key is spelled as git parses it.", ()),
    "mid-line-prose-nbsp": (f"The X-Agent{NBSP}: key is a trailer.", ()),
    "prose-after-key": ("X-Agent trailers are matched case-insensitively now.", ()),
    "prose-after-key-colonless-sentence": ("X-Agent lines such as codex/one are trailers.", ()),
    "ukrainian-prose": ("Агент: claude/two", ()),
    "bullet-item": ("- X-Agent: claude/two", ()),
}


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_round_two_controls_are_unchanged(name):
    line, expected = CONTROLS[name]
    message = "feat: x\n\n" + line + "\n\nX-Agent: codex/one\n"
    values = tuple(trailer.value for trailer in x_agent_trailers(message))
    assert values == (*expected, "codex/one")


def test_a_refused_attempt_is_not_masked_by_a_following_canonical_trailer():
    with pytest.raises(AgentTrailerError):
        x_agent_trailers(f"X-Agent: codex/one\nX-Agent{NBSP}: claude/two\nX-Agent: codex/three\n")
