"""Quote-preserving Bash word splitting for shared hook guards.

Non-POSIX shlex preserves surrounding quotes, which these guards need, but
mistakes an escaped double quote for the end of a quoted word. Hide only that
quote while shlex splits, then restore the original spelling in each token.
"""

from __future__ import annotations

import shlex


def heredoc_delimiter(word: str) -> str:
    """Apply Bash quote removal to a here-document delimiter word.

    The splitter keeps quotes and escapes so callers can tell whether the
    body expands. The line that ends the body uses the quote-removed word.
    """
    result: list[str] = []
    quote = ""
    index = 0
    while index < len(word):
        char = word[index]
        if char == "\\" and quote != "'" and index + 1 < len(word):
            following = word[index + 1]
            if not quote or following in {'"', "\\", "$", "`"}:
                result.append(following)
                index += 2
                continue
        if char == "'" and quote != '"':
            quote = "" if quote else "'"
        elif char == '"' and quote != "'":
            quote = "" if quote else '"'
        else:
            result.append(char)
        index += 1
    return "".join(result)


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
