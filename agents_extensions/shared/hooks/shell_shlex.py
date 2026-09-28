"""Quote-preserving Bash word splitting for shared hook guards.

Non-POSIX shlex preserves surrounding quotes, which these guards need, but
mistakes an escaped double quote for the end of a quoted word. Hide only that
quote while shlex splits, then restore the original spelling in each token.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Callable

_HEREDOC_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def collapse_line_continuations(command: str) -> str:
    """Apply Bash's backslash-newline removal before finding here-doc openers."""
    out: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            following = command[i + 1]
            if following != "\n":
                out.extend((char, following))
            i += 2
            continue
        if char in "\"'" and (not quote or quote == char):
            quote = "" if quote else char
        out.append(char)
        i += 1
    return "".join(out)


def strip_shell_comments(command: str) -> str:
    """Remove Bash comments at word boundaries without changing quoted text."""
    out: list[str] = []
    quote = ""
    backticks = False
    substitution_depth = 0
    outer_quote = ""
    word_start = True
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            out.append(command[i : i + 2])
            word_start = False
            i += 2
            continue
        if char == "'" and quote != '"' and not backticks:
            quote = "" if quote == "'" else "'"
            word_start = False
        elif char == '"' and quote != "'" and not backticks:
            quote = "" if quote == '"' else '"'
            word_start = False
        elif char == "`" and quote != "'":
            backticks = not backticks
            word_start = False
        elif quote != "'" and not backticks and command.startswith("$(", i):
            if not substitution_depth:
                outer_quote = quote
                quote = ""
            substitution_depth += 1
            out.append("$(")
            word_start = False
            i += 2
            continue
        elif substitution_depth and not quote and not backticks and char == "(":
            substitution_depth += 1
        elif substitution_depth and not quote and not backticks and char == ")":
            substitution_depth -= 1
            if not substitution_depth:
                quote = outer_quote
        elif not quote and not backticks and not substitution_depth:
            if char == "#" and word_start:
                end = command.find("\n", i)
                if end < 0:
                    break
                i = end
                continue
            word_start = char in " \t\n;&|()"
        out.append(char)
        i += 1
    return "".join(out)


def _body_substitutions(line: str) -> list[str]:
    """Expose executable substitutions from an unquoted here-doc body."""
    found: list[str] = []
    i = 0
    while i < len(line):
        if line[i] == "\\":
            i += 2
            continue
        if line.startswith("$((", i):
            i += 3
            continue
        if line.startswith("$(", i):
            start = i
            depth = 1
            i += 2
            while i < len(line) and depth:
                if line[i] == "\\":
                    i += 2
                    continue
                if line[i] == "(":
                    depth += 1
                elif line[i] == ")":
                    depth -= 1
                i += 1
            found.append(line[start:i])
            continue
        if line[i] == "`":
            start = i + 1
            i += 1
            while i < len(line) and line[i] != "`":
                i += 2 if line[i] == "\\" else 1
            found.append("$(" + line[start:i] + ")")
            i += 1
            continue
        i += 1
    return found


def preprocess_shell_command(command: str) -> str:
    """Prepare executable text for every guard in one conservative order.

    Comments are removed from opener lines before recognizing here-docs, but
    body lines are preserved until substitutions are extracted. A hash at the
    start of a body line is data, and its substitution can still execute.
    """
    collapsed = collapse_line_continuations(command)
    visible = strip_skippable_heredoc_bodies(
        collapsed, opener_transform=strip_shell_comments, body_substitutions=_body_substitutions
    )
    return strip_shell_comments(visible)


def skippable_heredoc_delimiters(line: str, *, initial_quote: str = "") -> list[tuple[str, bool, bool]] | None:
    """Find only here-doc words whose literal closer is unambiguous.

    Return (closer, strip_tabs, quoted), or None for any ambiguous opener.
    Callers then keep every remaining line visible to their command scanner.
    """
    delimiters: list[tuple[str, bool, bool]] = []
    ambiguous = False
    index = 0
    quote = initial_quote
    contexts: list[str] = []
    arithmetic_shift = False
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
        if line.startswith("$((", index):
            contexts.append("arithmetic")
            index += 3
            continue
        if line.startswith("${", index):
            contexts.append("parameter")
            index += 2
            continue
        if line.startswith("$(", index):
            contexts.append("command")
            index += 2
            continue
        if line.startswith("((", index):
            contexts.append("arithmetic")
            index += 2
            continue
        if contexts and contexts[-1] == "arithmetic" and line.startswith("))", index):
            contexts.pop()
            index += 2
            continue
        if contexts and contexts[-1] == "parameter" and char == "}":
            contexts.pop()
            index += 1
            continue
        if contexts and contexts[-1] == "command" and char == ")":
            contexts.pop()
            index += 1
            continue
        if contexts and contexts[-1] == "command" and char == "(":
            contexts.append("command")
            index += 1
            continue
        if line.startswith("<<<", index):
            index += 3
            continue
        if not line.startswith("<<", index):
            index += 1
            continue
        if contexts and contexts[-1] in {"arithmetic", "parameter"}:
            arithmetic_shift = True
            index += 2
            continue

        index += 2
        strip_tabs = index < len(line) and line[index] == "-"
        if strip_tabs:
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
    return (
        None
        if ambiguous or (arithmetic_shift and delimiters) or any(c in {"arithmetic", "parameter"} for c in contexts)
        else delimiters
    )


def _quote_after(line: str, initial_quote: str) -> str:
    quote = initial_quote
    i = 0
    while i < len(line):
        char = line[i]
        if char == "\\" and quote != "'":
            i += 2
            continue
        if char in "\"'" and (not quote or quote == char):
            quote = "" if quote else char
        i += 1
    return quote


def has_multiline_quoted_heredoc(command: str) -> bool:
    """Whether a `<<` occurs inside a quote opened on an earlier line.

    Such input was already undecidable to the deeper write and secret scanners.
    Keep their conservative refusal even after the shared pipeline preserves
    the line correctly for guards that can still recognize their own payload.
    """
    quote = ""
    saw_quoted_opener = False
    lines = collapse_line_continuations(command).split("\n")
    for number, line in enumerate(lines):
        opened_before_line = bool(quote)
        i = 0
        while i < len(line):
            char = line[i]
            if char == "\\" and quote != "'":
                i += 2
                continue
            if char in "\"'" and (not quote or quote == char):
                quote = "" if quote else char
            elif opened_before_line and quote and line.startswith("<<", i):
                saw_quoted_opener = True
            i += 1
        if saw_quoted_opener and not quote and any(rest.strip() for rest in lines[number + 1 :]):
            return True
    return False


def strip_skippable_heredoc_bodies(
    command: str,
    *,
    opener_transform: Callable[[str], str] | None = None,
    body_substitutions: Callable[[str], list[str]] | None = None,
) -> str:
    """Skip only closed, unambiguous here-doc bodies in all hook guards.

    Bash retains carriage returns in here-doc delimiters. A command containing
    one is left intact, so a mismatched closer can never conceal later commands.
    """
    if "<<" not in command or "\r" in command:
        return command

    lines = command.split("\n")
    kept: list[str] = []
    index = 0
    quote = ""
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        opener = opener_transform(line) if opener_transform else line
        pending = skippable_heredoc_delimiters(opener, initial_quote=quote)
        quote = _quote_after(opener, quote)
        if pending is None:
            kept.extend(lines[index:])
            break
        body_start = index
        substitutions: list[str] = []
        while pending and index < len(lines):
            delimiter, strip_tabs, quoted = pending[0]
            candidate = lines[index].lstrip("\t") if strip_tabs else lines[index]
            if candidate == delimiter:
                pending.pop(0)
            elif not quoted and body_substitutions:
                substitutions.extend(body_substitutions(lines[index]))
            index += 1
        if pending:
            kept.extend(lines[body_start:index])
        else:
            kept.extend(substitutions)
    return "\n".join(kept)


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
