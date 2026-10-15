"""Recognise a commit message's ``X-Agent`` trailers by git's trailer-key rules (#10450).

git reads a trailer key as ASCII letters, digits and ``-``, compares it
case-insensitively, and allows spaces or tabs before the ``:`` separator
(``trailer.c``: ``find_separator``, ``token_matches_item``). So ``x-agent:``,
``X-AGENT:`` and ``X-Agent :`` are all the ``X-Agent`` trailer, and each one
is returned here.

Every line of the message is read, not only git's final trailer block: squash
merges keep each commit's trailer in an earlier paragraph, and an author must
never drop out because of where its line sits. A line that spells the key
loosely (another separator, internal whitespace or punctuation, indentation,
no separator before an ``agent/task`` value) is not a trailer to git, and an
indented line after a trailer is folded into that trailer's value. Both raise
:class:`AgentTrailerError` instead of being guessed or ignored. Any other line,
such as prose that only mentions the key, is not a trailer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# The key git accepts: case-insensitive token, optional spaces or tabs, ':'.
_TRAILER_LINE = re.compile(r"x-agent[ \t]*:(?P<value>.*)", re.IGNORECASE | re.ASCII)
# A line that reads as an X-Agent trailer under a looser spelling of the key.
_LOOSE_LINE = re.compile(
    r"[ \t]*x[^a-z0-9\n]*agent(?:[ \t]*[:=]|[ \t]+\S*/\S*[ \t]*\Z)",
    re.IGNORECASE | re.ASCII,
)
# git trims its own whitespace set (sane_ctype isspace), not Unicode whitespace.
_GIT_SPACE = " \t\n\r"


class AgentTrailerError(ValueError):
    """A line claims to be an ``X-Agent`` trailer in a form git does not parse as one."""


@dataclass(frozen=True)
class AgentTrailer:
    """One ``X-Agent`` trailer: its line and its value, each without git's surrounding whitespace."""

    line: str
    value: str


def x_agent_trailers(message: str) -> tuple[AgentTrailer, ...]:
    """Every ``X-Agent`` trailer of ``message`` in order; duplicates and blank values are kept."""
    lines = [line.removesuffix("\r") for line in message.split("\n")]
    trailers: list[AgentTrailer] = []
    for index, line in enumerate(lines):
        match = _TRAILER_LINE.match(line)
        if match is None:
            if _LOOSE_LINE.match(line):
                raise AgentTrailerError("an X-Agent line is not in a form git parses as a trailer")
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if following[:1] in {" ", "\t"} and following.strip(_GIT_SPACE):
            raise AgentTrailerError("an X-Agent trailer value continues onto the next line")
        trailers.append(AgentTrailer(line.strip(_GIT_SPACE), match["value"].strip(_GIT_SPACE)))
    return tuple(trailers)
