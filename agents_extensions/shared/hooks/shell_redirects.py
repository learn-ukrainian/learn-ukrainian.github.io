#!/usr/bin/env python3
"""Shared quote-aware shell redirect reader for the three target guards.

Extracted from guard-pr-merge's #9461 parser. This is a discipline gate's
bounded shell reader; scope/target policy remains with each consumer.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Callable

from shell_shlex import preprocess_shell_command

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
        elif redirect := _REDIRECT_OPERATOR.match(line, i):
            # An unquoted numeric word glued to a redirect is a descriptor,
            # whereas `5 >file` retains 5 as a command argument.
            raw = "".join(buf)
            descriptor = re.search(r"(?<!\S)[0-9]+$", raw)
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
        for kind, raw in _split_scopes(line):
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
            segment, _ = rows[-1]
            rows[-1] = (segment, kind)
    return rows
