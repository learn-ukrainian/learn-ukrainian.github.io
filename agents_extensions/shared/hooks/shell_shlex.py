"""Quote-preserving Bash word splitting for shared hook guards.

Non-POSIX shlex preserves surrounding quotes, which these guards need, but
mistakes an escaped double quote for the end of a quoted word. Hide only that
quote while shlex splits, then restore the original spelling in each token.
"""

from __future__ import annotations

import re
import shlex

_HEREDOC_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def skippable_heredoc_delimiters(line: str) -> list[tuple[str, bool, bool]] | None:
    """Find only here-doc words whose literal closer is unambiguous.

    Return (closer, strip_tabs, quoted), or None for any ambiguous opener.
    Callers then keep every remaining line visible to their command scanner.
    """
    delimiters: list[tuple[str, bool, bool]] = []
    ambiguous = False
    index = 0
    quote = ""
    while index < len(line):
        char = line[index]
        if quote:
            if char == "\\" and quote == '"' and index + 1 < len(line):
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char == "\\":
            index += 2
            continue
        if char in "\"'":
            quote = char
            index += 1
            continue
        if not line.startswith("<<", index) or line.startswith("<<<", index):
            index += 1
            continue

        index += 2
        strip_tabs = index < len(line) and line[index] == "-"
        if strip_tabs:
            index += 1
        while index < len(line) and line[index] in " \t":
            index += 1
        if not strip_tabs and index < len(line) and line[index] == "-":
            strip_tabs = True
            index += 1
            while index < len(line) and line[index] in " \t":
                index += 1

        start = index
        word_quote = ""
        while index < len(line):
            char = line[index]
            if char == "\\" and word_quote != "'" and index + 1 < len(line):
                index += 2
                continue
            if char in "\"'" and (not word_quote or word_quote == char):
                word_quote = "" if word_quote else char
            elif not word_quote and char in " \t\r\n;|&()<>":
                break
            index += 1
        word = line[start:index]
        if _HEREDOC_IDENTIFIER.fullmatch(word):
            delimiters.append((word, strip_tabs, False))
        elif (
            len(word) >= 3
            and word[0] in "\"'"
            and word[-1] == word[0]
            and _HEREDOC_IDENTIFIER.fullmatch(word[1:-1])
        ):
            delimiters.append((word[1:-1], strip_tabs, True))
        else:
            ambiguous = True
    # A later safe-looking opener must not hide lines after an exotic opener
    # on the same command line.
    return None if ambiguous else delimiters


def split_quote_preserving(command: str, *, punctuation_chars: str | bool, whitespace: str) -> list[str]:
    marker_code = 0xE000
    while chr(marker_code) in command:
        marker_code += 1
        if marker_code > 0xF8FF:
            raise ValueError("no unused quote marker")
    marker = chr(marker_code)

    protected: list[str] = []
    quote = ""
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote == '"' and index + 1 < len(command):
            following = command[index + 1]
            if following in {'"', "\\", "$", "`"}:
                protected.append(marker if following == '"' else command[index : index + 2])
                index += 2
                continue
        if char == "'" and quote != '"':
            quote = "" if quote else "'"
        elif char == '"' and quote != "'":
            quote = "" if quote else '"'
        protected.append(char)
        index += 1

    lexer = shlex.shlex("".join(protected), posix=False, punctuation_chars=punctuation_chars)
    lexer.whitespace_split = True
    lexer.whitespace = whitespace
    lexer.commenters = ""
    return [token.replace(marker, '\\"') for token in lexer]
