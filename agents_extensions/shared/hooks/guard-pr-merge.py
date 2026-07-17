#!/usr/bin/env python3
"""PreToolUse guard — block `gh pr merge` (no `--admin`) that GitHub itself cannot refuse.

Reads the Claude Code hook payload on stdin (JSON with `tool_input.command`) and exits
2 (block) when the command is a `gh pr merge ...` whose target PR is a draft, has red
checks, has checks still running, or arms `--auto` on a branch that enforces nothing.

Division of labor with guard-admin-merge.py: that hook owns `gh pr merge --admin`
(the deliberate branch-protection bypass, #M-0.5); this hook owns every OTHER
`gh pr merge`. Segments carrying `--admin` are skipped here so a merge is never
double-judged.

Why a hook: branch protection is a paid feature for private repos, so on the free-plan
private repo the protection API answers 403 and NOTHING is a "required" check. Two
consequences bit us in one day: a draft PR was squash-merged before review (#189 class),
and two merges landed with the boundary-and-tests job RED because `--auto` only ever
waits for *required* checks — of which that repo has none. The fleet works across repos
with and without protection (this public repo's `main` does have it), so the guard
decides per-repo rather than assuming either.

FAIL-CLOSED: if the PR, its draft flag, its check states, or the base branch's
protection can't be determined (gh error/timeout, no PR number), BLOCK. A merge gate
must not let an *unverifiable* merge through; a human can always run the merge directly,
outside the agent harness.

A red check blocks regardless of whether GitHub calls it required: "required" is a
config accident, red is red. So EVERY check counts unless its name marks it advisory.
`--auto` is the one verdict that consults protection, because it is the one thing
protection actually changes.

SCOPE, stated honestly: this is a discipline gate, not a sandbox. It matches the shapes a
careless merge actually takes — direct, wrapper-prefixed, `bash -c` wrapped, and xargs-fed
`gh pr merge`, in gh's real flag spellings — and fails closed on what it cannot read. It
cannot stop an agent that sets out to evade it: `gh api -X PUT repos/{o}/{r}/pulls/{n}/merge`
never says "gh pr merge" at all, and neither does a Python script hitting the REST API.
Nothing matching on Bash commands can close that, so the job is to make the CARELESS path
refuse, not the deliberate path impossible. A shell here-string (`sh <<< '<cmd>'`) is
likewise unread — a deliberate-only shape, documented rather than papered over.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from typing import NamedTuple

# Agent harnesses export CLICOLOR_FORCE/FORCE_COLOR, which beat NO_COLOR and make
# `gh --json` emit ANSI-colorized JSON on pipes -> json.loads fails -> every merge
# fail-closes (review B1, PR #5324). Every gh subprocess below runs with the force
# vars REMOVED and NO_COLOR pinned; _decolorize() strips any residual escapes.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _gh_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"CLICOLOR_FORCE", "FORCE_COLOR"}}
    env["NO_COLOR"] = "1"
    env["CLICOLOR"] = "0"
    return env


def _decolorize(text: str) -> str:
    return _ANSI_RE.sub("", text)

# A check is treated as merge-blocking unless its name marks it explicitly advisory.
# Same inversion as guard-admin-merge.py, and it matters more here: an allowlist of
# "known required" names would UNDER-block, and on a repo where GitHub marks nothing
# required, under-blocking is the entire failure mode this hook exists to close.
ADVISORY_NAME_MARKERS = ("advisory",)

_FAIL_BUCKETS = {"fail", "failure", "error", "cancel", "canceled", "cancelled", "timed_out", "action_required"}
_PENDING_BUCKETS = {"pending", "queued", "in_progress", "waiting", "expected"}
# Only these mean "done and fine". A non-advisory check in ANY other state — including a
# bucket gh grows later, or a row with no bucket at all — is undeterminable, not green.
_PASS_BUCKETS = {"pass", "success", "skipping", "skipped", "neutral"}

# strconv.ParseBool's false spellings (lowercased). gh is cobra/pflag, so every boolean
# flag also accepts `--flag=value`: `gh pr list --draft=notabool` fails with
# "strconv.ParseBool: parsing \"notabool\": invalid syntax", which proves the =value path
# is real and must be parsed here too — `--auto` and `--auto=true` are the same flag.
_FALSE_VALUES = {"false", "f", "0"}


def _flag_enabled(args: list[str], name: str) -> bool:
    """Whether a gh boolean flag is on, in either spelling (`--auto` / `--auto=true`).

    LAST occurrence wins, as pflag applies repeated flags in argument order — verified:
    `gh pr list --draft=false --draft=true` returns draft PRs. Returning on the FIRST
    match would read `--auto=false --auto` as off and wave through the very auto-merge
    gh is about to arm.

    A malformed value (`--auto=maybe`) makes gh itself exit non-zero, so reading it as ON
    is the fail-closed direction: the guard judges a command that could never merge anyway.
    """
    enabled = False
    for a in args:
        if a == f"--{name}":
            enabled = True
        elif a.startswith(f"--{name}="):
            enabled = a.split("=", 1)[1].strip().lower() not in _FALSE_VALUES
    return enabled


def _is_advisory(name: str) -> bool:
    low = name.lower()
    return any(m in low for m in ADVISORY_NAME_MARKERS)


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}


def _command(payload: dict) -> str:
    return ((payload.get("tool_input") or {}).get("command") or "").strip()


# --- Command segmentation hardened against glued shell operators (#4876). ---
# Pattern lifted from guard-secret-print.py. Hooks are standalone by design,
# so the helpers are copied, not imported. Keep the four copies in
# guard-branch-switch-in-main.py, guard-admin-merge.py, guard-push-pytest.py,
# and guard-pr-merge.py in sync.
#
# This copy alone splits the tokenizer into _scope_events() with _segments() derived from
# it: only this hook cares WHERE a subshell begins and ends, because only this hook tracks
# `cd` (#5333). The sync target is tokenizing semantics, not line count
# (guard-branch-switch-in-main.py likewise grew _segments_with_following_operator for what it
# needed). Do NOT collapse the events back into a flat list to "re-sync": that flattening
# WAS the bug.
#
# One deliberate semantic divergence (#5333 r2): the siblings read a QUOTED lone paren
# (`echo ')'`) as an operator, because shlex strips the quotes before they see it. Here that
# splits a subshell scope and judges a merge in the wrong repo, so this copy scans the raw
# line for its parens (_split_scopes) and keeps quoted ones as argv. In the siblings the same
# quirk only ever splits a segment that neither `git checkout` nor `gh pr merge` matches, so
# it is harmless there and they are left alone rather than churned.


def _strip_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _heredoc_delimiters(line: str) -> list[tuple[str, bool]]:
    """Return (delimiter, strip_tabs) per heredoc opener; handles spaced
    ``<< EOF`` / ``<< - EOF`` and attached ``<<-EOF`` / ``<<-'EOF'`` (#4877)."""
    try:
        lexer = shlex.shlex(line, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []

    delimiters: list[tuple[str, bool]] = []
    i = 0
    while i < len(tokens):
        if tokens[i] != "<<":
            i += 1
            continue
        strip_tabs = False
        j = i + 1
        delim_tok = ""
        if j < len(tokens):
            nxt = tokens[j]
            if nxt == "-":
                strip_tabs = True
                j += 1
                if j < len(tokens):
                    delim_tok = tokens[j]
            elif nxt.startswith("-") and len(nxt) > 1:
                strip_tabs = True
                delim_tok = nxt[1:]
            else:
                delim_tok = nxt
        delimiter = _strip_quotes(delim_tok)
        if delimiter:
            delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc BODY lines — document text is data, not commands.

    Fail-CLOSED on an unclosed heredoc (#4877): a never-closing / mis-parsed
    opener must not make a trailing real `gh pr merge` vanish. Only a heredoc
    that actually closes has its body + closer dropped.
    """
    if "<<" not in command:
        return command

    lines = command.splitlines()
    kept: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        kept.append(lines[i])
        i += 1
        pending = _heredoc_delimiters(lines[i - 1])
        if not pending:
            continue
        body_start = i
        while i < n and pending:
            delimiter, strip_tabs = pending[0]
            candidate = lines[i].lstrip("\t") if strip_tabs else lines[i]
            if candidate == delimiter:
                pending.pop(0)
            i += 1
        if pending:
            kept.extend(lines[body_start:i])
    return "\n".join(kept)


def _join_line_continuations(text: str) -> str:
    r"""Fold `\<newline>` into one logical line, as the shell does — so a
    `\`-continued `gh pr merge` is not split across physical lines and missed.
    Over-folding a quoted literal `\` only merges argv text."""
    return text.replace("\\\n", "")


_PUNCTUATION = ";|&()<>"
# The parens are split out of the raw line by _split_scopes BEFORE a chunk is tokenized,
# so any paren still inside a chunk is quoted or escaped text, never an operator (#5333 r2).
_ARGV_PUNCTUATION = ";|&<>"


def _is_operator(tok: str, punctuation: str = _PUNCTUATION) -> bool:
    """A token that is nothing but shell punctuation — a separator, not argv."""
    return bool(tok) and all(c in punctuation for c in tok)


def _tokenize(line: str) -> list[str] | None:
    """Quote-aware tokens of one logical line, or None when it does not lex."""
    try:
        lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return None


def _split_scopes(line: str) -> list[tuple[str, str]]:
    """One raw line as ("text"|"open"|"close", raw) pieces, split at its REAL parens.

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
    for ch in line:
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
        elif ch in "()":
            pieces.append(("text", "".join(buf)))
            pieces.append(("open" if ch == "(" else "close", ch))
            buf = []
        else:
            buf.append(ch)
    pieces.append(("text", "".join(buf)))
    return pieces


def _scope_events(command: str) -> list[tuple[str, list[str]]]:
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
    still has quote context; the pieces between them are then tokenized. Glue (`&&(`, `)&&`)
    needs no special handling — the raw split cuts at the paren, leaving `&&` in the
    neighbouring chunk, so boundaries stay in sequence with the segments. A paren surviving
    INSIDE a chunk is quoted or escaped text, so `_ARGV_PUNCTUATION` (parens excluded) is
    what separates segments there: `echo ')'` keeps its `)` as the argument it is (#5333 r2).

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
    for line in _join_line_continuations(_strip_heredoc_bodies(command)).splitlines():
        line_events: list[tuple[str, list[str]]] = []
        readable = True
        for kind, raw in _split_scopes(line):
            if kind != "text":
                line_events.append((kind, []))
                continue
            tokens = _tokenize(raw)
            if tokens is None:
                readable = False
                break
            cur: list[str] = []
            for tok in tokens:
                if not _is_operator(tok, _ARGV_PUNCTUATION):
                    cur.append(tok)
                    continue
                if cur:
                    line_events.append(("segment", cur))
                    cur = []
            if cur:
                line_events.append(("segment", cur))
        events.extend(line_events if readable else [("unreadable", [])])
    return events


def _segments(command: str) -> list[list[str]]:
    """Just the argv segments of `command`, scope boundaries discarded."""
    return [argv for kind, argv in _scope_events(command) if kind == "segment" and argv]


def _is_env_assignment(tok: str) -> bool:
    return "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier()


def _skip_command_prefix(seg: list[str], i: int) -> int:
    """Advance past wrappers / env-assignments / brace-group open so a
    `env FOO=1 gh pr merge` or `{ gh pr merge; }` is not missed (#4877)."""
    while i < len(seg):
        tok = seg[i]
        if tok in {"sudo", "time", "env", "nohup", "command", "exec", "{"} or _is_env_assignment(
            tok
        ):
            i += 1
        else:
            break
    return i


_SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "busybox"}


def _find_merge(seg: list[str], start: int) -> int | None:
    """Index of the `gh pr merge` token run at or after `start`, else None."""
    for j in range(start, len(seg) - 2):
        if seg[j : j + 3] == ["gh", "pr", "merge"]:
            return j
    return None


# xargs options that consume a value; everything else short is a switch.
_XARGS_VALUE_OPTS = {"-n", "-P", "-I", "-i", "-L", "-l", "-s", "-d", "-E", "-e", "-a", "--max-args",
                     "--max-procs", "--replace", "--max-lines", "--max-chars", "--delimiter",
                     "--eof", "--arg-file"}


def _invoked_start(seg: list[str]) -> tuple[int, bool]:
    """Index where the actually-executed command begins → (index, reached_via_xargs).

    `xargs` is NOT a transparent prefix: it appends stdin items to the command it runs.
    Its own options must be stepped over, and the command boundary respected — otherwise
    `xargs echo gh pr merge 5` (which runs `echo`) reads as a merge, while
    `printf '5' | xargs gh pr merge --squash` (which really does merge PR 5) hides its
    selector on stdin.
    """
    i = _skip_command_prefix(seg, 0)
    if i >= len(seg) or seg[i] != "xargs":
        return i, False
    i += 1
    while i < len(seg):
        tok = seg[i]
        if not tok.startswith("-"):
            break
        if tok in _XARGS_VALUE_OPTS:
            i += 2
            continue
        if "=" in tok and tok.startswith("--"):
            i += 1
            continue
        i += 1
    return _skip_command_prefix(seg, i), True


def _strip_dollar_quote(payload: str) -> str:
    """Drop the `$` that `$'...'` / `$"..."` leave glued to a payload after tokenizing."""
    return payload[1:] if payload.startswith("$") else payload


def _shell_c_payload(seg: list[str]) -> str | None:
    """The command string of a `bash -c '<cmd>'` segment, else None.

    `bash -c 'gh pr merge 5 --squash'` really does merge, but the segment starts with
    `bash`, so a direct-command match alone never sees it. The payload is a command
    string and must be parsed as one.

    Bash's `$'...'` (ANSI-C) and `$"..."` (locale) quoting survive shlex as a literal
    `$` glued to the front — `bash -c $'gh pr merge 5'` yields `$gh pr merge 5`, whose
    first token is `$gh`, matching nothing. Bash runs that command for real (verified),
    so the marker is stripped rather than left to hide the merge.
    """
    i, _ = _invoked_start(seg)
    if i >= len(seg):
        return None
    if seg[i].rsplit("/", 1)[-1] not in _SHELLS:
        return None
    for j in range(i + 1, len(seg) - 1):
        tok = seg[j]
        # `-c`, and any short cluster CONTAINING c — `bash -cx 'cmd'` runs cmd just as
        # `-c` does, so requiring c to be last would miss a real merge (verified:
        # `bash -cx 'echo hi'` executes and exits 0).
        if tok.startswith("-") and not tok.startswith("--") and "c" in tok[1:]:
            return _strip_dollar_quote(seg[j + 1])
        if tok == "--command":
            return _strip_dollar_quote(seg[j + 1])
        if tok.startswith("--command="):
            return _strip_dollar_quote(tok.split("=", 1)[1])
    return None


_MAX_SHELL_DEPTH = 8

# Stand-in segment for a shell payload left uninspected at the recursion cap. _judge()
# recognizes the marker and refuses outright — the cap costs a refusal, never a free
# pass. Bounding the work must not bound the guarantee.
#
# It must be matched EXPLICITLY: relying on "no PR selector → block" would be wrong,
# because _pr_ref falls back to the CURRENT BRANCH's PR, so a green current branch would
# silently approve the payload nobody read.
_UNREADABLE_MARKER = "--__guard_unreadable__"
_UNPARSED = ["gh", "pr", "merge", _UNREADABLE_MARKER]

# Sentinel: a `cd` whose target the guard cannot statically read (`cd -`, `cd "$DIR"`,
# `cd $(...)`). Distinct from None ("this segment is not a cd").
_CD_UNREADABLE = object()


# bash's `cd` options (`cd -LP@ /x` is one legal cluster), minus `-` which is a TARGET.
_CD_FLAG_CHARS = set("LPe@")


def _is_cd_flag(tok: str) -> bool:
    return len(tok) >= 2 and tok[0] == "-" and set(tok[1:]) <= _CD_FLAG_CHARS


def _cd_target(seg: list[str]):
    """The literal directory a `cd` segment changes into, expanded.

    Returns None when the segment is not a cd; _CD_UNREADABLE when it is a cd the
    guard cannot statically resolve (variable/substitution/`cd -`). A bare `cd` goes
    to $HOME, as the shell does. Relative paths resolve against the hook process's
    cwd — the same base the real command's cd uses.

    Options are stepped over rather than matched literally, and `--` ends them: reading
    `cd -- /tmp`'s target as `--` (or `cd -LP /tmp`'s as `-LP`) would resolve a path that
    does not exist, and a wrong path is not a safe one — gh would miss there and the
    merge would fail closed on a command that is perfectly fine.

    `--` does NOT demote `-` to a plain directory name, though it reads as if it should:
    `cd -- -` still toggles to $OLDPWD (verified against bash with a real `./-` directory
    in place, which only `cd -- ./-` reaches). So `-` stays unreadable in both spellings.
    """
    i = _skip_command_prefix(seg, 0)
    if i >= len(seg) or seg[i] != "cd":
        return None
    rest: list[str] = []
    options_done = False
    for tok in seg[i + 1 :]:
        if not options_done:
            if tok == "--":
                options_done = True
                continue
            if _is_cd_flag(tok):
                continue
        rest.append(tok)
    if not rest:
        return os.path.expanduser("~")
    target = rest[0]
    if target == "-" or "$" in target or "`" in target:
        return _CD_UNREADABLE
    return os.path.abspath(os.path.expanduser(target))


class _JudgedSegment(NamedTuple):
    """One argv segment, with the cwd it actually runs in already resolved."""

    argv: list[str]
    cwd: str | None
    cwd_unreadable: bool


def _judged_segments(
    command: str,
    depth: int = 0,
    cwd: str | None = None,
    cwd_unreadable: bool = False,
) -> list[_JudgedSegment]:
    """Every segment worth judging, each tagged with the cwd it runs in.

    A `cd` is scoped to the shell level that runs it, so cwd is resolved HERE, during the
    walk that knows the nesting — not by a caller reading a flattened list, which cannot
    see where one shell ends and the next begins (#5333). Two boundaries close the leak:

    * subshell `( ... )` — cwd is saved at `(` and restored at `)`.
    * `bash -c '<payload>'` — the payload INHERITS the spawning shell's cwd (passed down),
      but its own cds die with it (the recursion's final state is discarded).

    Both leaked in both directions before: an inner `cd` was adopted by an outer merge
    (`bash -c 'cd /inner && true' && gh pr merge 9` judged 9 in /inner), and an outer
    merge inherited an inner one it never saw (`cd /outer && bash -c 'cd /inner &&
    gh pr merge 1' && gh pr merge 2` judged BOTH in /inner, though 2 runs in /outer).
    Judging a merge in the wrong repo is wrong in both directions, and the dangerous one
    is the false ALLOW off a same-numbered green PR.

    An unattributable boundary — a `)` with no `(` (a `case` arm, a stray paren) — desyncs
    the model, so cwd is marked unreadable rather than guessed: the walk no longer knows
    which shell it is standing in, and _judge never sees a cwd this function is unsure of.
    """
    out: list[_JudgedSegment] = []
    stack: list[tuple[str | None, bool]] = []
    for kind, argv in _scope_events(command):
        if kind == "open":
            stack.append((cwd, cwd_unreadable))
            continue
        if kind == "close":
            if stack:
                cwd, cwd_unreadable = stack.pop()
            else:
                cwd_unreadable = True
            continue
        if kind == "unreadable":
            cwd_unreadable = True
            continue
        target = _cd_target(argv)
        if target is _CD_UNREADABLE:
            cwd_unreadable = True
        elif target is not None:
            # A literal cd RESOLVES the cwd — including after an unreadable one, whose
            # target no longer matters now that a readable cd has overwritten it.
            cwd, cwd_unreadable = target, False
        out.append(_JudgedSegment(argv, cwd, cwd_unreadable))
        payload = _shell_c_payload(argv)
        if not payload:
            continue
        if depth >= _MAX_SHELL_DEPTH:
            out.append(_JudgedSegment(list(_UNPARSED), cwd, cwd_unreadable))
            continue
        out.extend(_judged_segments(payload, depth + 1, cwd, cwd_unreadable))
    return out


def _merge_args(seg: list[str]) -> list[str] | None:
    """Return the args of a `gh pr merge ...` segment this hook judges, else None.

    Skipped: `--disable-auto` (any spelling), which disarms auto-merge rather than
    merging anything and is exactly the remedy this hook's --auto verdict asks for.

    Also skipped: a bare `--admin`, which is guard-admin-merge.py's job — but ONLY that
    exact spelling, because that is precisely what the sibling matches. `--admin=true` is
    a real admin merge the sibling misses, so it is judged HERE rather than falling
    between the two hooks. Judging it cannot double-judge: the sibling never sees it.
    """
    i, via_xargs = _invoked_start(seg)
    if seg[i : i + 3] == ["gh", "pr", "merge"]:
        args = seg[i + 3 :]
    elif i > 0 and not via_xargs:
        # A known wrapper brought its own options/operands (`sudo -u bot gh pr merge`,
        # `env -i gh pr merge`), so the command does not begin at `i`. Find it instead of
        # letting the merge through unjudged. Only wrapper-prefixed segments are scanned,
        # so an unwrapped `echo gh pr merge 5` is still not treated as a merge — and the
        # scan is skipped for xargs, whose trailing tokens are DATA for another command
        # (`xargs echo gh pr merge 5` runs echo).
        j = _find_merge(seg, i)
        if j is None:
            return None
        args = seg[j + 3 :]
    else:
        return None
    if via_xargs and _pr_selector(args) is None:
        # xargs appends stdin items, so the real selector is not in this command at all.
        # Falling back to the current branch's PR would judge one PR while gh merges
        # another; refuse instead.
        args = [*args, _UNREADABLE_MARKER]
    flags, _ = _classify(args)
    # `gh pr merge --help` prints help and merges nothing — reading the manual is not
    # the offence this guard is for. --help is a bool like any other, so it gets the same
    # spelling treatment (`--help=true`) rather than a bare-token check.
    if _flag_enabled(flags, "help") or "-h" in flags:
        return None
    if "--admin" in flags or _flag_enabled(flags, "disable-auto"):
        return None
    return args


# Options of `gh pr merge` that consume the NEXT argv token as their value. Their values
# must never be mistaken for the PR selector: in `gh pr merge --subject 5`, the 5 is the
# commit subject and the real target is the current branch's PR. Judging the wrong PR is a
# fail-open (green PR #5 waves through a red current branch), not a cosmetic slip.
_VALUE_FLAGS = {
    "--subject", "-t",
    "--body", "-b",
    "--body-file", "-F",
    "--match-head-commit",
    "--author-email", "-A",
    # Inherited by every `gh pr` subcommand: `-R, --repo [HOST/]OWNER/REPO`.
    "--repo", "-R",
}


# Value-taking SHORTHANDS, by letter → canonical long name. pflag allows these inside a
# cluster (`-st subj` = squash + subject), with the value attached (`-tsubj`, `-Rowner/repo`
# — both verified against real gh), `=`-joined (`-t=subj`), or in the next token.
_VALUE_SHORTS = {"t": "--subject", "b": "--body", "F": "--body-file", "A": "--author-email", "R": "--repo"}

_LONG_VALUE_FLAGS = {"--subject", "--body", "--body-file", "--match-head-commit", "--author-email", "--repo"}


def _cluster_value(tok: str) -> tuple[str | None, str | None, bool]:
    """Inspect a shorthand cluster: → (canonical long name, attached value, needs_next).

    pflag scans a cluster left to right; the first value-taking letter consumes the rest
    of the token as its value, or the next token when nothing is attached. So in
    `-st green-subject`, `green-subject` is the SUBJECT — treating it as the PR selector
    would judge some other PR entirely.
    """
    j = 1
    while j < len(tok):
        ch = tok[j]
        if ch in _VALUE_SHORTS:
            name = _VALUE_SHORTS[ch]
            rest = tok[j + 1 :]
            if rest.startswith("="):
                return name, rest[1:], False
            if rest:
                return name, rest, False
            return name, None, True
        j += 1
    return None, None, False


def _parse_args(args: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    """Split argv into (flag tokens, positionals, option values keyed by long name).

    pflag takes the NEXT token as a string flag's value even when it looks like a flag,
    so `gh pr merge 5 --subject --disable-auto` is a normal merge whose subject happens
    to be "--disable-auto". Scanning raw argv would read that value as the flag and skip
    judging the merge entirely — a fail-open. Only tokens in FLAG position count.
    """
    flags: list[str] = []
    positionals: list[str] = []
    values: dict[str, str] = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            flags.append(a)
            name, _, value = a.partition("=")
            if value:
                if name in _LONG_VALUE_FLAGS:
                    values[name] = value
                i += 1
                continue
            if a in _LONG_VALUE_FLAGS and i + 1 < len(args):
                values[a] = args[i + 1]
                i += 2
                continue
            i += 1
            continue
        if a.startswith("-") and len(a) > 1:
            flags.append(a)
            name, attached, needs_next = _cluster_value(a)
            if name and attached is not None:
                values[name] = attached
                i += 1
                continue
            if name and needs_next and i + 1 < len(args):
                values[name] = args[i + 1]
                i += 2
                continue
            i += 1
            continue
        positionals.append(a)
        i += 1
    return flags, positionals, values


def _classify(args: list[str]) -> tuple[list[str], list[str]]:
    """(flags, positionals) — see _parse_args."""
    flags, positionals, _ = _parse_args(args)
    return flags, positionals


def _repo_option(args: list[str]) -> str | None:
    """The `-R/--repo` value, which retargets the whole command at another repo."""
    return _parse_args(args)[2].get("--repo")


def _repo_args(repo: str | None) -> list[str]:
    """`--repo X` argv for gh, so every lookup targets the repo the MERGE targets."""
    return ["--repo", repo] if repo else []


def _pr_selector(args: list[str]) -> str | None:
    """The `<number|url|branch>` selector of `gh pr merge`, or None for the current branch.

    gh accepts all three forms, so the selector is passed through verbatim rather than
    forced to a number — a URL selector names a PR in a possibly different repo, and
    resolving it as "whatever PR the cwd is on" would judge a different PR than gh merges.
    """
    _, positionals = _classify(args)
    return positionals[0] if positionals else None


def _pr_ref(args: list[str], repo: str | None = None, cwd: str | None = None) -> str | None:
    """The PR to judge: the explicit selector, else the current branch's PR number."""
    selector = _pr_selector(args)
    if selector:
        return selector
    try:
        out = subprocess.run(
            ["gh", "pr", "view", *_repo_args(repo), "--json", "number", "-q", ".number"],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def _owner_repo_from_url(url: str) -> str | None:
    """`owner/repo` from a PR URL — the PR's BASE repo, which is what protection guards.

    Taken from the PR's own `url` rather than `gh repo view` in cwd: the cwd can be a
    different repo entirely (a URL selector), and it is the base repo — not the fork a PR
    may come from — whose branch protection decides what `--auto` waits for.
    """
    m = re.match(r"https?://[^/]+/([^/]+)/([^/]+)/pull/\d+", url.strip())
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _pr_meta(pr: str, repo: str | None = None, cwd: str | None = None) -> dict | None:
    """`{isDraft, baseRefName, url}` for the PR, or None if undeterminable (→ fail-closed).

    A payload without a boolean `isDraft` is undeterminable, not "not a draft" — `{}` or
    `isDraft: null` must never read as a green light.
    """
    try:
        out = subprocess.run(
            ["gh", "pr", "view", pr, *_repo_args(repo), "--json", "isDraft,baseRefName,url"],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    try:
        data = json.loads(_decolorize(out.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("isDraft"), bool):
        return None
    return data


def _check_states(pr: str, repo: str | None = None, cwd: str | None = None) -> tuple[list[str], list[str]] | None:
    """(failing, pending) non-advisory check names, or None if undeterminable."""
    try:
        out = subprocess.run(
            ["gh", "pr", "checks", pr, *_repo_args(repo), "--json", "name,bucket,state"],
            capture_output=True,
            env=_gh_env(),
            cwd=cwd,
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    text = (out.stdout or "").strip()
    if not text:
        # Empty output is ambiguous: a PR with zero checks (rc 0 → nothing to wait for)
        # vs a gh error / non-existent PR (rc != 0 → fail-CLOSED block). Reading an
        # *error* as "no failing checks" is the fail-open bug guard-admin-merge closed.
        return ([], []) if out.returncode == 0 else None
    try:
        rows = json.loads(_decolorize(text))
    except json.JSONDecodeError:
        return None
    if not isinstance(rows, list):
        return None
    failing: list[str] = []
    pending: list[str] = []
    for r in rows:
        if not isinstance(r, dict):
            return None
        name = str(r.get("name") or "")
        if _is_advisory(name):
            continue
        bucket = str(r.get("bucket") or r.get("state") or "").lower()
        if bucket in _FAIL_BUCKETS:
            failing.append(name)
        elif bucket in _PENDING_BUCKETS:
            pending.append(name)
        elif bucket not in _PASS_BUCKETS:
            # Schema drift or a partial row on a non-advisory check. "I don't recognize
            # this state" must never fall through to green — that is the fail-open bug
            # this hook exists to prevent, arriving by a different door.
            return None
    return failing, pending


def _base_protected(owner_repo: str, base: str) -> bool | None:
    """True = protection with at least one required status check, False = the branch
    enforces nothing (403 on a free plan, 404 unprotected, protection without required
    checks, or an EMPTY required-checks list), None = undeterminable (→ fail-closed).

    The empty list matters: `required_status_checks` can be present with `contexts: []`
    and `checks: []`, which is truthy but requires nothing — auto-merge would wait for
    nothing and merge red, exactly as on an unprotected branch. Only a non-empty list
    gives `--auto` something to wait on.
    """
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{owner_repo}/branches/{base}/protection"],
            capture_output=True,
            env=_gh_env(),
            text=True,
            timeout=8,
        )
    except Exception:
        return None
    if out.returncode != 0:
        err = f"{out.stderr or ''}{out.stdout or ''}"
        if "HTTP 403" in err or "HTTP 404" in err or "Branch not protected" in err:
            return False
        return None
    try:
        data = json.loads(_decolorize(out.stdout or "").strip() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    required = data.get("required_status_checks")
    if not isinstance(required, dict):
        return False
    contexts = required.get("contexts") or []
    checks = required.get("checks") or []
    return bool(contexts or checks)


_FOOTER = (
    "GitHub will merge a draft or a red PR without complaint — branch protection stops only\n"
    "what it was configured to require, and on a free-plan private repo it cannot be configured\n"
    "at all. That is the gap this hook covers. If the merge is genuinely intended, a human can\n"
    "run it directly, outside the agent harness.\n\n"
    "Hook source: .claude/hooks/guard-pr-merge.py\n"
)


def _block_msg(reason: str, guidance: str) -> str:
    return f"BLOCKED by guard-pr-merge: {reason}.\n\n{guidance}\n\n{_FOOTER}"


def _judge(args: list[str], cwd: str | None = None) -> str | None:
    """Block message for this `gh pr merge`, or None to allow."""
    if _UNREADABLE_MARKER in args:
        return _block_msg(
            "this merge's target cannot be read from the command itself",
            "The PR is not named here — it arrives on stdin (`xargs`), or is buried under more\n"
            "layers of `bash -c` than this guard unwraps. Judging the current branch's PR\n"
            "instead would verify one PR while gh merges another. Run the merge with the PR\n"
            "named explicitly (`gh pr merge <number> ...`).",
        )
    repo = _repo_option(args)
    pr = _pr_ref(args, repo, cwd=cwd)
    if not pr:
        return _block_msg(
            "could not determine which PR this merges",
            "Name the PR explicitly (`gh pr merge <number> ...`) so the merge can be verified.",
        )
    meta = _pr_meta(pr, repo, cwd=cwd)
    if meta is None:
        return _block_msg(
            f"could not verify PR {pr}'s draft status (gh error, timeout, or unexpected schema)",
            "An unverifiable merge is refused, not assumed safe. Re-check the PR with\n"
            "`gh pr view` and retry once gh answers.",
        )
    if meta.get("isDraft"):
        return _block_msg(
            f"PR {pr} is a DRAFT",
            "Draft PRs are never merged or armed — a draft is by definition not review-ready\n"
            "(the #189 incident: a draft was squash-merged before anyone reviewed it). Mark it\n"
            "ready (`gh pr ready`) and get the review gate first.",
        )
    states = _check_states(pr, repo, cwd=cwd)
    if states is None:
        return _block_msg(
            f"could not verify PR {pr} check states (gh error, timeout, or an unrecognized check state)",
            "An unverifiable merge is refused, not assumed safe. Re-read the checks with\n"
            "`gh pr checks` and retry once gh answers.",
        )
    failing, pending = states
    if failing:
        return _block_msg(
            f"PR {pr} has FAILING checks: {', '.join(failing)}",
            "Every non-advisory check counts, whether or not GitHub marks it required —\n"
            "'required' is a config accident, red is red. Fix the failures and re-run;\n"
            "do not merge over them.",
        )
    if _flag_enabled(_classify(args)[0], "auto"):
        base = str(meta.get("baseRefName") or "")
        if not base:
            return _block_msg(
                f"could not determine PR {pr}'s base branch",
                "--auto can only be verified against a known base branch.",
            )
        owner_repo = _owner_repo_from_url(str(meta.get("url") or ""))
        if not owner_repo:
            return _block_msg(
                f"could not determine which repo owns PR {pr} (no usable PR url)",
                "--auto is refused while its safety is unverifiable.",
            )
        protected = _base_protected(owner_repo, base)
        if protected is None:
            return _block_msg(
                f"could not determine whether {owner_repo}@{base} is protected (gh error/timeout)",
                "--auto is refused while its safety is unverifiable.",
            )
        if not protected:
            return _block_msg(
                f"--auto on {owner_repo}@{base}, which has no required status checks",
                "auto-merge fires regardless of checks here — merge manually after an explicit\n"
                "all-green read. Auto-merge only ever waits for REQUIRED checks, and this branch\n"
                "has none, so arming it merges the moment the PR is mergeable (two merges landed\n"
                "red this way).",
            )
        # Protected base with required checks: --auto is what it claims to be, so
        # still-running checks are exactly what it will wait for.
        return None
    if pending:
        return _block_msg(
            f"PR {pr} has checks still running: {', '.join(pending)}",
            "Wait for them to finish and read the result, or re-run with --auto — which this\n"
            "guard allows once it confirms the base branch really does have required checks\n"
            "for auto-merge to wait on. Merging now merges an unknown result.",
        )
    return None


def main() -> int:
    payload = _read_payload()
    command = _command(payload)
    # Fast path: only engage on `gh ... pr ... merge` (leave every other command untouched).
    # Quote/backslash marks are dropped first, because the shell drops them BEFORE running
    # the command: `g\h pr merge 5` and `g'h' pr merge 5` both execute gh (verified:
    # `bash -c 'g\h --version'` prints gh's version). Testing the raw source would let a
    # merge past this early return before the real parser ever sees it. Normalizing only
    # ever sends MORE commands to the full parse — never fewer.
    if not command:
        return 0
    probe = command.replace("\\", "").replace("'", "").replace('"', "")
    if "gh" not in probe or "pr" not in probe or "merge" not in probe:
        return 0
    # Each segment arrives carrying the cwd it runs in, so a PR number is judged in the
    # repo the MERGE runs in, not the session's repo — `cd private-repo && gh pr merge 203`
    # judged from the public repo resolves a DIFFERENT PR #203, wrong in BOTH directions
    # (false block, or worse: false allow off a same-numbered green PR). Scoping that cwd
    # to its own shell level is _judged_segments' job: it is the only reader that knows
    # where a subshell or `bash -c` payload begins and ends.
    for seg in _judged_segments(command):
        args = _merge_args(seg.argv)
        if args is None:
            continue
        # `-R owner/repo` names the repo outright, so this merge does not depend on the cwd
        # it runs in — and an unreadable cwd has nothing left to fail closed about. Blocking
        # anyway made the escape hatch this very message advertises a no-op (#5333 r2).
        # Verified against real gh from /tmp, which is not a git repo at all:
        # `gh pr view 9 --repo cli/cli --json number` -> rc=0 `{"number":9}`. Without a
        # selector gh refuses (`argument required when using the --repo flag` -> rc=1), so
        # `-R` alone cannot wave a merge through: _pr_ref reads that rc and fails closed.
        if seg.cwd_unreadable and not _repo_option(args):
            sys.stderr.write(
                _block_msg(
                    "this merge's working directory cannot be read (a `cd` to a variable, "
                    "a substitution, or `cd -`; or a shell nesting this guard cannot follow)",
                    "The guard must judge the PR in the repo the merge actually runs in.\n"
                    "Use a literal `cd /path && gh pr merge ...`, or name the repo with\n"
                    "`-R owner/repo` (with the PR number: `gh pr merge 5 -R owner/repo`).",
                )
            )
            return 2
        # An unreadable cwd is a guess, not a location — `-R` got us here, so let gh resolve
        # from the repo name in this hook's own cwd rather than hand it a stale directory.
        blocked = _judge(args, cwd=None if seg.cwd_unreadable else seg.cwd)
        if blocked:
            sys.stderr.write(blocked)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
