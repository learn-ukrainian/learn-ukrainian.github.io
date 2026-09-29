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
_MAX_BACKTICK_DEPTH = 16
_SHELL_OPERATORS = (
    "&>>",
    "<<<",
    "<<-",
    "&>",
    ">>",
    ">|",
    "&&",
    "||",
    ";;",
    "|&",
    "<<",
    "<>",
    ">&",
    "<&",
    ">",
    "<",
    "|",
    "&",
    ";",
    "(",
    ")",
    "\n",
)
_OPERATOR_CHARS = frozenset("();<>|&\n")


class ShellPreprocessLimit(RuntimeError):
    """A nested command could not be exposed within the parser's depth cap."""


def split_operator_run(token: str) -> list[str]:
    """Split a pure shell-punctuation run, keeping redirects intact."""
    if token in _SHELL_OPERATORS or not token or not set(token) <= _OPERATOR_CHARS:
        return [token]
    parts: list[str] = []
    index = 0
    while index < len(token):
        operator = next(op for op in _SHELL_OPERATORS if token.startswith(op, index))
        parts.append(operator)
        index += len(operator)
    return parts


def collapse_line_continuations(command: str) -> str:
    """Join Bash continuations while respecting physical-line comments."""
    out: list[str] = []
    quote = ""
    outer_quote = ""
    backtick_outer_quote = ""
    substitution_depth = 0
    backticks = False
    comment = False
    word_start = True
    i = 0
    while i < len(command):
        char = command[i]
        if comment:
            # A backtick closes its body before Bash parses that body's
            # comment. Only an unescaped closer can resume the outer command.
            if backticks and char == "`":
                slash = i - 1
                while slash >= 0 and command[slash] == "\\":
                    slash -= 1
                if (i - 1 - slash) % 2 == 0:
                    comment = False
            if comment:
                out.append(char)
                if char == "\n":
                    comment = False
                    word_start = True
                i += 1
                continue
        if char == "\\" and quote != "'" and i + 1 < len(command):
            following = command[i + 1]
            if following != "\n":
                out.extend((char, following))
                word_start = False
            i += 2
            continue
        if char == "'" and quote != '"':
            quote = "" if quote == "'" else "'"
            word_start = False
        elif char == '"' and quote != "'":
            quote = "" if quote == '"' else '"'
            word_start = False
        elif char == "`" and quote != "'":
            if not backticks:
                backtick_outer_quote = quote
                quote = ""
            else:
                quote = backtick_outer_quote
            backticks = not backticks
            word_start = backticks
        elif quote != "'" and not backticks and command.startswith("$(", i):
            if not substitution_depth:
                outer_quote = quote
                quote = ""
            substitution_depth += 1
            out.append("$(")
            word_start = True
            i += 2
            continue
        elif substitution_depth and not quote and not backticks and char == "(":
            substitution_depth += 1
        elif substitution_depth and not quote and not backticks and char == ")":
            substitution_depth -= 1
            if not substitution_depth:
                quote = outer_quote
            word_start = False
        elif not quote:
            if char == "#" and word_start:
                comment = True
            word_start = char in " \t\n;&|()"
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
    backtick_outer_quote = ""
    word_start = True
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            out.append(command[i : i + 2])
            word_start = False
            i += 2
            continue
        if char == "'" and quote != '"':
            quote = "" if quote == "'" else "'"
            word_start = False
        elif char == '"' and quote != "'":
            quote = "" if quote == '"' else '"'
            word_start = False
        elif char == "`" and quote != "'":
            if not backticks:
                backtick_outer_quote = quote
                quote = ""
            else:
                quote = backtick_outer_quote
            backticks = not backticks
            word_start = backticks
        elif quote != "'" and not backticks and command.startswith("$(", i):
            if not substitution_depth:
                outer_quote = quote
                quote = ""
            substitution_depth += 1
            out.append("$(")
            word_start = True
            i += 2
            continue
        elif substitution_depth and not quote and not backticks and char == "(":
            substitution_depth += 1
        elif substitution_depth and not quote and not backticks and char == ")":
            substitution_depth -= 1
            if not substitution_depth:
                quote = outer_quote
            word_start = False
        elif not quote:
            if char == "#" and word_start:
                end = i + 1
                while end < len(command):
                    if command[end] == "\n" or (backticks and command[end] == "`"):
                        break
                    if backticks and command[end] == "\\" and end + 1 < len(command) and command[end + 1] != "\n":
                        end += 2
                    else:
                        end += 1
                if end == len(command):
                    break
                i = end
                continue
            word_start = char in " \t\n;&|()"
        out.append(char)
        i += 1
    return "".join(out)


def _expose_backtick_bodies(command: str, *, depth: int = 0) -> str:
    """Expose executable backticks as inline command substitutions for guards."""
    if depth >= _MAX_BACKTICK_DEPTH and "`" in command:
        raise ShellPreprocessLimit("nested backtick depth exceeded")
    out: list[str] = []
    quote = ""
    substitutions: list[tuple[str, int]] = []
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            out.append(command[index : index + 2])
            index += 2
            continue
        if char == "'" and quote != '"':
            quote = "" if quote == "'" else "'"
        elif char == '"' and quote != "'":
            quote = "" if quote == '"' else '"'
        elif quote != "'" and command.startswith("$(", index):
            substitutions.append((quote, 1))
            quote = ""
            out.append("$(")
            index += 2
            continue
        elif quote != "'" and char == "`":
            end = index + 1
            while end < len(command) and command[end] != "`":
                end += 2 if command[end] == "\\" else 1
            if end < len(command):
                if quote == '"':
                    out.append('"')
                body = re.sub(r"\\([\\`])", r"\1", command[index + 1 : end])
                if "`" in body:
                    body = _expose_backtick_bodies(body, depth=depth + 1)
                out.extend(("$(", body, ")"))
                if quote == '"':
                    out.append('"')
                index = end + 1
                continue
        elif char == "(" and not quote and substitutions:
            outer_quote, paren_depth = substitutions[-1]
            substitutions[-1] = (outer_quote, paren_depth + 1)
        elif char == ")" and not quote and substitutions:
            outer_quote, paren_depth = substitutions[-1]
            if paren_depth == 1:
                substitutions.pop()
                quote = outer_quote
            else:
                substitutions[-1] = (outer_quote, paren_depth - 1)
        out.append(char)
        index += 1
    return "".join(out)


def _body_substitutions(body: str) -> list[str] | None:
    """Expose complete substitutions, including ones spanning body lines.

    A substitution we cannot close leaves the entire body visible to guards.
    """
    found: list[str] = []
    i = 0
    while i < len(body):
        if body[i] == "\\":
            i += 2
            continue
        if body.startswith("$((", i):
            i += 3
            continue
        if body.startswith("$(", i):
            start = i
            depth = 1
            quote = ""
            backticks = False
            comment = False
            word_start = True
            i += 2
            while i < len(body) and depth:
                char = body[i]
                if comment:
                    if char == "\n":
                        comment = False
                        word_start = True
                    i += 1
                    continue
                if char == "\\" and quote != "'":
                    i += 2
                    word_start = False
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
                elif not quote and not backticks:
                    if char == "#" and word_start:
                        comment = True
                    elif char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    word_start = char in " \t\n;&|()"
                i += 1
            if depth:
                return None
            found.append(body[start:i])
            continue
        if body[i] == "`":
            start = i + 1
            i += 1
            while i < len(body) and body[i] != "`":
                i += 2 if body[i] == "\\" else 1
            if i >= len(body):
                return None
            found.append("$(" + body[start:i] + ")")
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
    return _expose_backtick_bodies(strip_shell_comments(visible))


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
        if line.startswith("$[", index):
            contexts.append("arithmetic_bracket")
            index += 2
            continue
        if char == "[" and re.search(r"[A-Za-z_][A-Za-z0-9_]*\Z", line[:index]):
            contexts.append("arithmetic_bracket")
            index += 1
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
        if contexts and contexts[-1] == "arithmetic_bracket" and char == "]":
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
        if contexts and contexts[-1] in {"arithmetic", "arithmetic_bracket", "parameter"}:
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
        elif len(word) >= 3 and word[0] in "\"'" and word[-1] == word[0] and _HEREDOC_IDENTIFIER.fullmatch(word[1:-1]):
            delimiters.append((word[1:-1], strip_tabs, True))
        else:
            ambiguous = True
    # A later safe-looking opener must not hide lines after an exotic opener
    # on the same command line.
    return (
        None
        if ambiguous
        or (arithmetic_shift and delimiters)
        or any(c in {"arithmetic", "arithmetic_bracket", "parameter"} for c in contexts)
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


def strip_skippable_heredoc_bodies(
    command: str,
    *,
    opener_transform: Callable[[str], str] | None = None,
    body_substitutions: Callable[[str], list[str] | None] | None = None,
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
        undecidable_body = False
        while pending and index < len(lines):
            delimiter, strip_tabs, quoted = pending[0]
            part_start = index
            while index < len(lines):
                candidate = lines[index].lstrip("\t") if strip_tabs else lines[index]
                if candidate == delimiter:
                    break
                index += 1
            if index == len(lines):
                break
            if not quoted and body_substitutions:
                body = "\n".join(lines[part_start:index])
                extracted = body_substitutions(body)
                if extracted is None:
                    undecidable_body = True
                else:
                    substitutions.extend(extracted)
            pending.pop(0)
            index += 1
        if pending or undecidable_body:
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
