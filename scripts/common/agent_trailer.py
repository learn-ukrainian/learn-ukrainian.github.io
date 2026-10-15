"""Recognise a commit message's ``X-Agent`` trailers, refusing every other attempt (#10450).

A line that git reads as the ``X-Agent`` key is a trailer. git reads a key as
ASCII letters, digits and ``-``, compares it case-insensitively, and allows
spaces or tabs before the ``:`` separator (``trailer.c``: ``find_separator``,
``token_matches_item``). So ``x-agent:``, ``X-AGENT:`` and ``X-Agent :`` are
all the ``X-Agent`` trailer, and each one is returned here.

Every line of the message is read, not only git's final trailer block: squash
merges keep each commit's trailer in an earlier paragraph, and an author must
never drop out because of where its line sits.

Any *other* line that reads as an ``X-Agent`` trailer attempt raises
:class:`AgentTrailerError` instead of being ignored, so an author can never
vanish behind a spelling git does not parse (no-break or zero-width characters,
a fullwidth colon, ``X_Agent:``, indentation, ``X-Agent claude/two``...). An
indented line directly after a trailer is folded into that trailer's value by
git and refuses too. The refusal names the line number and the class of the
attempt and never echoes the raw value.

An attempt is detected on a *skeleton* of the line: Unicode NFKC, with format
(``Cf``), combining (``Mn``/``Me``) and control characters removed or mapped to
a plain space, casefolded. The skeleton is an attempt when it starts (after
optional whitespace) with ``x``, an optional run of separators, ``agent``, and
then a colon-like character (``:`` ``=`` ``∶`` ``꞉``) or whitespace and an
``agent/task`` value token. Prose that merely mentions the key mid-line, longer
keys such as ``X-Agent-Model:``, ``#`` comments and Markdown ``>`` quotations
are not attempts. A line that starts with the key followed by ordinary words
(``X-Agent trailers are parsed...``) is prose, not an attempt.

Documented limit: cross-script homoglyphs, such as Cyrillic lookalike letters
inside the key, survive NFKC and are not detected. No confusables table is used.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# The key git accepts: case-insensitive token, optional spaces or tabs, ':'.
_TRAILER_LINE = re.compile(r"x-agent[ \t]*:(?P<value>.*)", re.IGNORECASE | re.ASCII)
# An attempt, matched on the skeleton: key shape, then a colon-like character or an agent/task value.
_ATTEMPT = re.compile(
    r" *x[\W_]*agent(?:(?P<colon> *[:=∶꞉])| +(?P<value>[^\s/]+/\S))",
)
# git trims its own whitespace set (sane_ctype isspace), not Unicode whitespace.
_GIT_SPACE = " \t\n\r"

_CLASS_HIDDEN = "non-ASCII or control characters"
_CLASS_INDENTED = "indented"
_CLASS_NO_SEPARATOR = "no separator"
_CLASS_SEPARATOR = "separator other than a colon"
_CLASS_KEY = "key spelling"
_CLASS_CONTINUATION = "continuation"


class AgentTrailerError(ValueError):
    """A line claims to be an ``X-Agent`` trailer in a form git does not parse as one.

    ``line_number`` is 1-based; ``attempt_class`` names the kind of attempt.
    The message carries both and never the raw line.
    """

    def __init__(self, line_number: int, attempt_class: str) -> None:
        self.line_number = line_number
        self.attempt_class = attempt_class
        if attempt_class == _CLASS_CONTINUATION:
            detail = f"an X-Agent trailer value continues onto the next line (line {line_number}, {attempt_class})"
        else:
            detail = f"an X-Agent line (line {line_number}, {attempt_class}) is not in a form git parses as a trailer"
        super().__init__(detail)


@dataclass(frozen=True)
class AgentTrailer:
    """One ``X-Agent`` trailer: its line and its value, each without git's surrounding whitespace."""

    line: str
    value: str


def _skeleton(line: str) -> str:
    """The line with hidden, combining and control characters removed and spacing made plain."""
    kept: list[str] = []
    for char in unicodedata.normalize("NFKC", line):
        category = unicodedata.category(char)
        if category in {"Cf", "Mn", "Me"}:
            continue
        kept.append(" " if category == "Cc" or char.isspace() else char)
    return "".join(kept).casefold()


def _attempt_class(line: str, separator_is_colon: bool, has_value_only: bool) -> str:
    if any(ord(char) > 127 or (ord(char) < 32 and char != "\t") for char in line):
        return _CLASS_HIDDEN
    if line[:1] in {" ", "\t"}:
        return _CLASS_INDENTED
    if has_value_only:
        return _CLASS_NO_SEPARATOR
    if not separator_is_colon:
        return _CLASS_SEPARATOR
    return _CLASS_KEY


def x_agent_trailers(message: str) -> tuple[AgentTrailer, ...]:
    """Every ``X-Agent`` trailer of ``message`` in order; duplicates and blank values are kept.

    Raises :class:`AgentTrailerError` for any other line that reads as a trailer attempt.
    """
    lines = [line.removesuffix("\r") for line in message.split("\n")]
    trailers: list[AgentTrailer] = []
    for index, line in enumerate(lines):
        match = _TRAILER_LINE.match(line)
        if match is None:
            attempt = _ATTEMPT.match(_skeleton(line))
            if attempt is not None:
                colon = attempt["colon"]
                raise AgentTrailerError(
                    index + 1,
                    _attempt_class(
                        line,
                        separator_is_colon=colon is not None and colon.strip() == ":",
                        has_value_only=colon is None,
                    ),
                )
            continue
        following = lines[index + 1] if index + 1 < len(lines) else ""
        if following[:1] in {" ", "\t"} and following.strip(_GIT_SPACE):
            raise AgentTrailerError(index + 2, _CLASS_CONTINUATION)
        trailers.append(AgentTrailer(line.strip(_GIT_SPACE), match["value"].strip(_GIT_SPACE)))
    return tuple(trailers)
