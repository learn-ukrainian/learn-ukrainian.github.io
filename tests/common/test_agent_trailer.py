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
