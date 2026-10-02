#!/usr/bin/env python3
"""Shared quote-aware shell redirect reader for the three target guards.

Extracted from guard-pr-merge's #9461 parser. This is a discipline gate's
bounded shell reader; scope/target policy remains with each consumer.
"""

from __future__ import annotations

import re
import shlex
import sys
from collections.abc import Callable

# The sibling module is also imported from deployed, read-only hook trees.
sys.dont_write_bytecode = True
from shell_shlex import (
    _quote_after,
    collapse_line_continuations,
    preprocess_shell_command,
    skippable_heredoc_delimiters,
    strip_shell_comments,
)

# Longest redirect spellings come first; `>&` is one operator, not `>` then `&`.
_REDIRECT_OPERATOR = re.compile(r"&>>?|<<<|<<-?|[<>]&|<>|>\||>>?|<")


def _tokenize(line: str) -> list[str] | None:
    """Quote-aware tokens of one logical line, or None when it does not lex."""
    try:
        # Real operators were separated while quote context was still available.
        lexer = shlex.shlex(line, posix=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return None


def _split_scopes(line: str) -> list[tuple[str, str]]:
    """Split raw shell operators from text before removing quotes.

    A real paren is one the shell would act on: unquoted and unescaped. This scan runs on
    the RAW line because that is the only place quote context still exists — shlex strips
    quotes, so `echo ')'` and a bare `)` reach the token stream as the identical token `)`,
    and the scope scanner read the quoted one as a real subshell close (#5333 r2). That was
    not merely an over-block: in `(cd /a && echo ')' && gh pr merge 9)` the fake close
    popped the REAL subshell and judged PR 9 in the session's repo instead of /a — a
    wrong-repo judgment, the same false-ALLOW class the scope fix set out to close.

    Pairing shlex's posix and non-posix token streams would be the obvious alternative, and
    it is wrong: they diverge on backslashes (`cd /a\\ b` -> 2 posix tokens, 3 raw ones), so
    the two streams cannot be zipped, and a misalignment silently mis-classifies a REAL
    paren — reopening the leak. Splitting the raw text first needs no alignment at all.

    Quote/escape state tracks posix shlex's own rules, so the pieces re-lex as shlex reads
    them: `\\` escapes outside quotes and inside `"..."`, but is literal inside `'...'`.
    """
    pieces: list[tuple[str, str]] = []
    buf: list[str] = []
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(line):
        ch = line[i]
        if escaped:
            buf.append(ch)
            escaped = False
        elif ch == "\\" and quote != "'":
            buf.append(ch)
            escaped = True
        elif quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            buf.append(ch)
            quote = ch
        elif ch == "#" and (not buf or buf[-1].isspace()):
            # Comment punctuation has no scope or redirect meaning.
            buf.extend(line[i:])
            break
        elif line.startswith("&&", i):
            # Bash reads &&>file as the AND-list operator followed by >file,
            # not a background operator followed by &>file.
            pieces.append(("text", "".join(buf)))
            pieces.append(("separator", "&&"))
            buf = []
            i += 2
            continue
        elif redirect := _REDIRECT_OPERATOR.match(line, i):
            # An unquoted numeric word glued to a redirect is a descriptor,
            # whereas `5 >file` retains 5 as a command argument.
            raw = "".join(buf)
            descriptor = re.search(r"(?<!\S)(?:[0-9]+|\{[A-Za-z_][A-Za-z0-9_]*\})$", raw)
            if descriptor and not redirect.group().startswith("&"):
                raw = raw[: descriptor.start()]
            pieces.append(("text", raw))
            pieces.append(("redirect", redirect.group()))
            buf = []
            i = redirect.end()
            continue
        elif ch in "();|&":
            pieces.append(("text", "".join(buf)))
            kind = "open" if ch == "(" else "close" if ch == ")" else "separator"
            pieces.append((kind, ch))
            buf = []
        else:
            buf.append(ch)
        i += 1
    pieces.append(("text", "".join(buf)))
    return pieces


def _redirect_target_dynamic(raw: str) -> bool:
    """Whether the first raw word expands, preserving literal quoted/escaped `$`."""
    quote: str | None = None
    escaped = False
    for ch in raw.lstrip():
        if escaped:
            escaped = False
        elif ch == "\\" and quote != "'":
            escaped = True
        elif ch in "$`" and quote != "'":
            return True
        elif quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch.isspace():
            break
    return False


def unmodeled_shell_offset(line: str) -> int | None:
    """First word containing syntax our scope reader cannot safely model.

    This is a lexical tripwire, not a case/parameter grammar: an unquoted
    command-word `case`, or any parenthesis in an active ${...}, refuses the
    entire command. Call after shared preprocessing (including heredocs).
    The offset is diagnostic only: never split the command at this position.
    """
    command_word = True
    redirect_operand = False
    quote = ""
    word_start = 0
    word = ""
    literal = True
    contexts: list[tuple[str, bool, bool, str, int, bool]] = []
    i = 0

    def finish_word() -> bool:
        nonlocal command_word, redirect_operand, word, literal
        unsafe = False
        if word:
            if redirect_operand:
                redirect_operand = False
            elif command_word:
                unsafe = literal and word == "case"
                assignment = re.match(r"[A-Za-z_][A-Za-z0-9_]*=", word)
                if not assignment and not (
                    literal and word in {"if", "elif", "while", "until", "then", "do", "else", "{", "!", "time", "-p"}
                ):
                    command_word = False
        word = ""
        literal = True
        return unsafe

    while i < len(line):
        ch = line[i]
        if not word:
            word_start = i
        if ch == "`" and quote != "'":
            # Complete backticks were exposed by preprocessing; any active
            # one remaining is unterminated and cannot establish a repository.
            return word_start
        if ch == "\\" and quote != "'":
            if i + 1 == len(line):
                return word_start
            word += line[i : i + 2]
            literal = False
            i += 2
            continue
        if quote != "'" and line.startswith("${", i):
            # Opaque parameter text: quotes and nested expansions cannot hide
            # parens. Quoted braces do not terminate an expansion.
            parameter_quotes = [""]
            inner_quote = ""
            j = i + 2
            while j < len(line) and parameter_quotes:
                char = line[j]
                if char in "()":
                    return word_start
                if char == "\\":
                    if j + 1 < len(line) and line[j + 1] in "()":
                        return word_start
                    j += 2
                    continue
                if inner_quote != "'" and line.startswith("${", j):
                    parameter_quotes.append(inner_quote)
                    inner_quote = ""
                    j += 2
                    continue
                if char in "\"'" and (not inner_quote or inner_quote == char):
                    inner_quote = "" if inner_quote else char
                elif char == "}" and not inner_quote:
                    inner_quote = parameter_quotes.pop()
                j += 1
            if parameter_quotes:
                return word_start
            word += line[i:j]
            literal = False
            i = j
            continue
        if quote != "'" and line.startswith("$(", i):
            contexts.append((quote, command_word, redirect_operand, word + "$()", word_start, False))
            quote = ""
            command_word = True
            redirect_operand = False
            word = ""
            literal = True
            i += 2
            continue
        if quote:
            word += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            word += ch
            literal = False
        elif ch == "#" and not word:
            end = line.find("\n", i)
            i = len(line) if end < 0 else end
            continue
        elif ch.isspace() or ch in "();|&<>":
            # A glued descriptor belongs to the redirect, not the command.
            redirect = _REDIRECT_OPERATOR.match(line, i)
            if redirect and (word.isdecimal() or re.fullmatch(r"\{[A-Za-z_][A-Za-z0-9_]*\}", word)):
                word = ""
            if finish_word():
                return word_start
            if redirect:
                redirect_operand = True
                i = redirect.end()
                continue
            if ch == "\n" or ch in "();|&":
                command_word = True
                redirect_operand = False
                if ch == "(":
                    contexts.append((quote, True, False, "", i, True))
                elif ch == ")" and contexts:
                    quote, command_word, redirect_operand, word, word_start, literal = contexts.pop()
        else:
            word += ch
        i += 1
    return word_start if finish_word() or quote or contexts else None


def command_repository_unknown(command: str) -> bool:
    """Classify the entire command independently of the cwd/scope reader.

    Closed heredoc data is inert. An ambiguous or unterminated heredoc, quote,
    expansion, or detector failure cannot establish a repository. The caller
    must refuse branch operations throughout such a command, in any worktree.
    """
    try:
        if unmodeled_shell_offset(preprocess_shell_command(command)) is not None:
            return True
        if "<<" not in command:
            return False
        lines = collapse_line_continuations(command).split("\n")
        index = 0
        quote = ""
        while index < len(lines):
            line = lines[index]
            index += 1
            opener = strip_shell_comments(line)
            pending = skippable_heredoc_delimiters(opener, initial_quote=quote)
            quote = _quote_after(opener, quote)
            if pending is None:
                return True
            for delimiter, strip_tabs, _ in pending:
                while index < len(lines):
                    candidate = lines[index].lstrip("\t") if strip_tabs else lines[index]
                    index += 1
                    if candidate == delimiter:
                        break
                else:
                    return True
        return False
    except Exception:
        return True


def unknown_repository_segments(command: str) -> list[list[str]]:
    """Read branch-operation candidates without inferring any cwd or scope.

    Quotes still distinguish data from commands. Executable substitutions get
    their own argv stream, including inside double quotes; case arm parentheses
    cannot end a substitution. These lexical contexts never establish a repo.
    Only the branch guard uses this conservative whole-command path.
    """
    command = preprocess_shell_command(command)
    # Preserve the established per-line visibility on malformed quotes and
    # ambiguous heredocs as well. Both readers only collect operations here;
    # neither reader's scope events can establish or restore repository trust.
    segments = [
        argv
        for kind, argv in scope_events(
            command,
            mark_redirect_unreadable=True,
            unreadable_marker="--__guard_unreadable__",
            unparsed=["--__guard_unreadable__"],
            may_match=lambda _: False,
        )
        if kind == "segment"
    ]
    argv: list[str] = []
    word = ""
    quote = ""
    case_depth = 0
    case_parens: list[int] = []
    paren_depth = 0
    contexts: list[tuple[str, str, list[str], int, int]] = []
    i = 0

    def finish_word() -> None:
        nonlocal word, case_depth
        if not word:
            return
        tokens = _tokenize(word)
        command_prefix = all(
            token in {"if", "elif", "while", "until", "then", "do", "else", "{", "!", "time", "-p"}
            or re.match(r"[A-Za-z_][A-Za-z0-9_]*=", token)
            for token in argv
        )
        if word == "case" and command_prefix:
            case_depth += 1
            case_parens.append(paren_depth)
        elif word == "esac" and not argv and case_depth:
            case_depth -= 1
            case_parens.pop()
        if word in {"if", "elif", "while", "until", "then", "do", "else"} and not argv:
            word = ""
            return
        argv.extend(tokens if tokens is not None else ["--__guard_unreadable__"])
        word = ""

    def finish_segment() -> None:
        nonlocal argv
        finish_word()
        if argv:
            segments.append(argv)
        argv = []

    while i < len(command):
        ch = command[i]
        if ch == "\\" and quote != "'":
            word += command[i : i + 2]
            i += 2
            continue
        if quote != "'" and command.startswith("${", i):
            # Parameter punctuation is opaque argument data, never a scope close.
            end = i + 2
            depth = 1
            parameter_quote = ""
            substitutions: list[int] = []
            while end < len(command) and depth:
                char = command[end]
                if char == "\\":
                    end += 2
                    continue
                if parameter_quote != "'" and command.startswith("$(", end):
                    substitutions.append(end)
                if char in "\"'" and (not parameter_quote or parameter_quote == char):
                    parameter_quote = "" if parameter_quote else char
                elif not parameter_quote:
                    if command.startswith("${", end):
                        depth += 1
                        end += 2
                        continue
                    if char == "}":
                        depth -= 1
                end += 1
            for start in substitutions:
                segments.extend(unknown_repository_segments(command[start:end]))
            word += command[i:end]
            i = end
            continue
        if quote != "'" and command.startswith("$(", i):
            contexts.append((quote, word + "$()", argv, case_depth, paren_depth))
            quote, word, argv = "", "", []
            i += 2
            continue
        if quote:
            word += ch
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
            word += ch
        elif ch in "();|&<>\n":
            finish_segment()
            if ch == "(":
                paren_depth += 1
            elif ch == ")":
                if contexts and case_depth == contexts[-1][3] and paren_depth == contexts[-1][4]:
                    quote, word, argv, case_depth, paren_depth = contexts.pop()
                elif paren_depth and (not case_parens or paren_depth > case_parens[-1]):
                    paren_depth -= 1
        elif ch.isspace():
            finish_word()
        else:
            word += ch
        i += 1
    finish_segment()
    # An unterminated substitution must not conceal an outer branch command.
    for _, outer_word, outer_argv, _, _ in contexts:
        segments.append([*outer_argv, *(_tokenize(outer_word) or ["--__guard_unreadable__"])])
    return segments


def scope_events(
    command: str,
    *,
    mark_redirect_unreadable: bool,
    unreadable_marker: str,
    unparsed: list[str],
    may_match: Callable[[str], bool],
    keep_separators: bool = False,
) -> list[tuple[str, list[str]]]:
    """The command as an ordered event stream: argv segments AND subshell boundaries.

    Quote-aware and robust to glued shell operators (#4876). A `gh pr merge` inside a
    quoted commit body (`git commit -m "... gh pr merge ..."`) stays one argv element —
    no false block. A `; gh pr merge 5` glued to a preceding token becomes its own
    segment and is inspected — no evasion. Heredoc bodies are stripped (document text is
    not commands); `\\`-continuations are folded; each logical line lexes separately.

    Events, rather than a flat segment list, because `(` and `)` are the only record of a
    SUBSHELL — and a subshell's `cd` dies at its `)` (#5333). Flattening them away made
    `(cd /inner && true) && gh pr merge 5` read as if the merge ran in /inner: a
    false-ALLOW off whatever PR #5 is there.

    Boundaries come from _split_scopes' scan of the RAW line, which is the only reader that
    still has quote context; the pieces between them are then tokenized. Glued operators
    (`&&(`, `)&&`) remain separate events. Operator characters surviving INSIDE a chunk
    are quoted or escaped text and stay arguments (#5333 r2).
    Redirect operators and their first operand are removed from argv; dynamic
    or missing operands mark that command unreadable under the consumer's policy.

    `(` also opens a command substitution (`cd $(cat f)`), which reads here as a subshell
    scope. That is not a coincidence to paper over: `$(...)` really does run in a
    subshell, so its `cd` really does die at the `)`. Same event, same truth.

    An `("unreadable", [])` event marks a line that does not lex (unbalanced quote —
    which the real shell rejects too). It cannot be scanned for `cd`, so it must not be
    passed off as scope-neutral. It replaces the whole line's events rather than just the
    offending chunk's: a half-scanned line could otherwise leave an `open` whose later
    `close` RESTORES a readable cwd, laundering an unreadable line into a clean one.
    Only a `segment` event carries argv; the rest carry [].

    """
    events: list[tuple[str, list[str]]] = []
    # Each consumer selects when redirect uncertainty must refuse its target.
    for line in preprocess_shell_command(command).splitlines():
        line_events: list[tuple[str, list[str]]] = []
        readable = True
        cur: list[str] = []
        redirect_pending = False
        segment_unreadable = False
        pieces = _split_scopes(line)
        for kind, raw in pieces:
            if kind == "redirect":
                segment_unreadable |= redirect_pending
                redirect_pending = True
                continue
            if kind in {"open", "close", "separator"}:
                # The `$` before a real open paren belongs to a command
                # substitution, not to a statically readable PR/cd target.
                dynamic = bool(cur and cur[-1].endswith("$"))
                if kind == "open" and mark_redirect_unreadable and (segment_unreadable or redirect_pending):
                    # A dynamic prefix redirect may precede the command word.
                    # Keep an explicit refusal across the substitution's scope.
                    line_events.append(("segment", list(unparsed)))
                if (mark_redirect_unreadable and (segment_unreadable or redirect_pending)) or dynamic:
                    cur.append(unreadable_marker)
                if cur:
                    line_events.append(("segment", cur))
                cur = []
                redirect_pending = segment_unreadable = False
                if kind != "separator":
                    line_events.append((kind, []))
                elif keep_separators:
                    line_events.append((kind, [raw]))
                continue
            tokens = _tokenize(raw)
            if tokens is None:
                readable = False
                break
            if redirect_pending and tokens:
                tokens.pop(0)
                segment_unreadable |= _redirect_target_dynamic(raw)
                redirect_pending = False
            cur.extend(tokens)
        if mark_redirect_unreadable and (segment_unreadable or redirect_pending):
            cur.append(unreadable_marker)
        if cur:
            line_events.append(("segment", cur))
        if readable:
            events.extend(line_events)
        else:
            events.append(("unreadable", []))
            if may_match(line):
                events.append(("segment", list(unparsed)))
    return events


def segments_with_following_operator(command: str, **kwargs) -> list[tuple[list[str], str | None]]:
    """Post-redirect argv with the actual command separator, including &&."""
    rows: list[tuple[list[str], str | None]] = []
    for kind, argv in scope_events(command, keep_separators=True, **kwargs):
        if kind == "segment":
            rows.append((argv, None))
        elif kind == "separator" and rows:
            segment, operator = rows[-1]
            rows[-1] = (segment, (operator or "") + argv[0])
        elif kind in {"open", "close", "unreadable"} and rows:
            segment, operator = rows[-1]
            rows[-1] = (segment, (operator or "") + kind)
    return rows
