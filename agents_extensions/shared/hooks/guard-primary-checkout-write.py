#!/usr/bin/env python3
"""PreToolUse guard — block write tools from dirtying the primary checkout.

The branch-switch guard (``guard-branch-switch-in-main.py``) stops an agent from
*switching branches* in the primary checkout, but a direct write tool can dirty
tracked files from repo root without ever running a git command. That was the
observed Codex failure chain (issue #4448): the agent investigated from repo
root and then edited from the same cwd.

This hook closes that gap for providers whose PreToolUse hooks expose structured
write payloads. It reads the hook payload on stdin and blocks a write when its
target resolves to a protected file inside the primary checkout while that
checkout sits on a protected branch (``main`` / ``master``). Everything else —
writes into a ``.worktrees/**`` dispatch worktree, any other registered
worktree, gitignored local/runtime state, or paths outside the repo — is
allowed. Read-only commands (``git status``, ``git log``, ``rg``, ``cat`` …) are
never touched because they expose no write target.

Containment is **not** re-derived here: every decision defers to
``scripts.guardrails.worktree_containment`` (issue #4444), the single source of
truth shared with the monitor (#4449) and git shim (#4450). This hook only maps
each provider payload onto the target path(s) that module classifies.

Covered write surfaces
----------------------
* ``Write`` / ``Edit`` / ``MultiEdit`` — ``tool_input.file_path``.
* ``apply_patch`` and Codex ``Edit`` / ``Write`` aliases — file paths parsed from
  the ``*** Add/Update/Delete File:`` / ``*** Move to:`` headers of the patch
  body (issue #4447 verified Codex CLI fires PreToolUse for ``apply_patch``).
* ``Bash`` — write-capable redirection (``>``, ``>>``, ``&>``), ``tee``, and
  in-place editors (``sed -i`` / ``perl -i``). Quote-aware tokenization keeps a
  ``>`` inside a quoted string (e.g. a commit message) from reading as a
  redirect.
* ``Bash`` git-mediated working-tree writes (issues #5396 / #5517) — ``git apply`` /
  ``git am``, ``git add``, ``git stash pop|apply``, ``git mv`` / ``git rm``,
  ``git checkout <ref> -- <path>``, ``git checkout <ref> <path>`` (no ``--``),
  and ``git restore --source=…`` when the effective git worktree (payload cwd
  or ``git -C``) is the protected primary checkout. Rescue clean forms
  ``git checkout -- <path>`` and plain ``git restore <path>`` (no ``--source``)
  remain allowed so operators can discard accidental dirt.

Shell values in Bash paths (issues #5404 / #8500)
-------------------------------------------------
Every Bash word is expanded before classification, in command order.
``$NAME`` / ``${NAME}`` take a value only when the variable is **known**, and
``~`` / ``$HOME`` expand as the shell would. Quoted or backslash-escaped ``$``/``~``
stay literal.

A variable is KNOWN only when its last assignment before the use is an
unconditional, top-level, literal assignment: it starts a statement (after
start-of-command, ``;`` or a newline — never after ``&&``/``||``/``|``/``&``) and
no ``|``/``&`` follows it. The first element of an ``&&``/``||`` chain
(``S=/tmp/x && …``, ``S=/tmp/x || true``) qualifies because it always runs;
``export``/``declare``/``typeset``/``readonly NAME=literal`` count as assignments.
A value with whitespace is not known (an unquoted use would word-split).

Everything else makes the variable UNKNOWN for the rest of the command, and
UNKNOWN shadows the inherited environment (no fallback — ``HOME`` included):
an assignment inside an ``&&``/``||`` branch, ``if``/``case``/loop body, ``{ }``
group, subshell / ``$(...)``, pipeline stage, background job or function;
``NAME+=``, ``NAME[i]=``, ``S=x cmd`` prefix assignments, ``${NAME:=x}``; a
value from ``$(...)``/backticks/another unknown; ``read``, ``for``/``select``,
``unset``, ``mapfile``/``readarray``, ``getopts``, ``printf -v``, ``let``,
``(( … ))``, ``declare``/``local`` without a top-level literal value; ``IFS``
changes, ``source``/``eval``/``trap`` and ``declare -n`` (these reach any
variable). Inside loop, function or subshell bodies — which can run again or
later — a variable is usable only if it never became unknown and only ever held
one literal value in the whole command.

A path containing any unknown expansion is BLOCKED as
``unresolved_shell_variable``: the unknown value may be absolute, empty or hold
``..``, so no literal prefix proves it stays out of the primary. ``git -C``
directories and git pathspecs follow the same rule. Inherited variables that the
command never assigns (other than ``HOME``) are unknown too.

Coverage limitations (documented, by design)
--------------------------------------------
* Bash write detection is heuristic. Arbitrary write vectors — ``dd of=``,
  ``cp``/``mv`` destinations, ``python -c "open(...,'w')"``, ``$EDITOR`` — are
  **not** parsed. Those paths rely on physical worktree isolation plus the
  monitor tripwire (#4449) and git shim (#4450).
* Codex Desktop direct-edit interception is unverified (#4447). Where a provider
  does not emit a hookable write event, this hook cannot enforce that path; the
  enforcement layer is #4445/#4446/#4449 instead. See
  ``docs/runbooks/codex-hooks.md``.

The primary-checkout containment layer fails **open**: any parse/import/git
error there exits 0 (allow). Physical worktree isolation, the primary checkout
tripwire, CI, and protected-branch review gates remain the repository safety
boundary.

Emergency override (explicit operator only): set
``LEARN_UK_ALLOW_PRIMARY_GIT_WRITE=1`` to skip the git-mediated primary block
for one shell invocation. Prefer fixing the cwd / using a worktree instead.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# shared containment predicate (issue #4444) — imported, never re-derived
# ---------------------------------------------------------------------------


def _load_containment():
    """Import ``scripts.guardrails.worktree_containment`` from any launch dir.

    The hook runs from a deployed copy (``<root>/.{claude,codex,agent}/hooks/``)
    or from source (``agents_extensions/shared/hooks/``); in both the repo root
    that owns ``scripts/`` is an ancestor. Walk upward for it and put it on
    ``sys.path``. Returns ``None`` if it cannot be found/imported so the caller
    fails open rather than blocking every write on an import error.
    """
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "scripts" / "guardrails" / "worktree_containment.py").exists():
            if str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
            break
    try:
        from scripts.guardrails import worktree_containment as wc
    except Exception:  # pragma: no cover - defensive fail-open
        return None
    return wc


# ---------------------------------------------------------------------------
# payload plumbing
# ---------------------------------------------------------------------------


def _read_payload() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def _tool_name(payload: dict) -> str:
    return str(
        payload.get("tool_name") or payload.get("tool") or payload.get("name") or ""
    )


def _tool_input(payload: dict) -> dict:
    for key in ("tool_input", "arguments", "input", "params"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _payload_cwd(payload: dict) -> str:
    # A tool-specific working directory is the execution cwd and therefore
    # outranks the session-level cwd carried by the hook envelope. Unified
    # exec calls commonly keep the session cwd at the primary checkout while
    # placing the dispatch worktree in tool_input.workdir.
    tool_input = _tool_input(payload)
    cwd = (
        tool_input.get("cwd")
        or tool_input.get("workdir")
        or tool_input.get("working_directory")
        or payload.get("cwd")
        or payload.get("working_directory")
    )
    return str(cwd) if cwd else os.getcwd()


# ---------------------------------------------------------------------------
# target extraction — structured write tools
# ---------------------------------------------------------------------------

# Headers in an apply_patch body that name a file the patch writes to. The path
# is the remainder of the line. ``Move from`` is a delete of the old location,
# ``Move to`` a create of the new one — both dirty the tree, so both count.
_APPLY_PATCH_HEADERS = (
    "*** Add File:",
    "*** Update File:",
    "*** Delete File:",
    "*** Move to:",
    "*** Move from:",
)


def _apply_patch_targets(patch_text: str) -> list[str]:
    """File paths a ``*** Begin Patch`` body writes to, in order of appearance."""
    targets: list[str] = []
    for raw in patch_text.splitlines():
        line = raw.strip()
        for header in _APPLY_PATCH_HEADERS:
            if line.startswith(header):
                path = line[len(header):].strip()
                if path:
                    targets.append(path)
                break
    return targets


def _strings_in(value: object) -> list[str]:
    """Every string reachable inside a (possibly nested) tool_input value."""
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(_strings_in(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            out.extend(_strings_in(item))
    return out


def write_tool_targets(tool_input: dict) -> list[str]:
    """Candidate target paths for a structured write tool.

    ``Write``/``Edit``/``MultiEdit`` expose ``file_path`` directly.
    ``apply_patch`` (and Codex ``Edit``/``Write`` aliases) carry the patch body
    somewhere in ``tool_input``; scan every string for apply_patch headers and,
    failing that, honor an explicit ``file_path``/``path`` key.
    """
    targets: list[str] = []

    # Direct single-file path keys used by Write/Edit/MultiEdit (and some
    # provider aliases). ``file_path`` is canonical; the rest are defensive.
    for key in ("file_path", "path", "filepath", "target_file", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            targets.append(value)

    # apply_patch / patch-style payloads: parse file headers from any string.
    for text in _strings_in(tool_input):
        if "*** Begin Patch" in text or any(h in text for h in _APPLY_PATCH_HEADERS):
            targets.extend(_apply_patch_targets(text))

    # De-dup while preserving order.
    seen: set[str] = set()
    ordered: list[str] = []
    for path in targets:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


# ---------------------------------------------------------------------------
# target extraction — write-capable Bash
# ---------------------------------------------------------------------------

# Control operators that separate one logical command from the next.
_CONTROL_OPS = frozenset({"&&", "||", ";", ";;", "|", "|&", "&", "(", ")", "\n"})

# Redirection operators that create/append to a *file* (as opposed to ``>&``
# which duplicates a file descriptor). ``&>`` / ``&>>`` redirect both streams.
_FILE_REDIRECTS = frozenset({">", ">>", ">|", "&>", "&>>"})


def _strip_quotes_for_heredoc(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _heredoc_delimiters(line: str) -> list[tuple[str, bool]]:
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
            if nxt == "-":  # spaced: << - DELIM
                strip_tabs = True
                j += 1
                if j < len(tokens):
                    delim_tok = tokens[j]
            elif nxt.startswith("-") and len(nxt) > 1:  # attached: <<-DELIM
                strip_tabs = True
                delim_tok = nxt[1:]
            else:
                delim_tok = nxt
        delimiter = _strip_quotes_for_heredoc(delim_tok)
        if delimiter:
            delimiters.append((delimiter, strip_tabs))
        i = j + 1
    return delimiters


def _strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc BODY lines before tokenizing (#4538 / #4855).

    Content between ``<<'MARKER'`` and ``MARKER`` is document DATA, not shell
    syntax. Without this, body text like ``>15%`` or markdown backtick spans
    is tokenized as redirects and misread as write targets — the recurring
    false-positive class. Pattern shared with guard-secret-print.py.

    Fail-CLOSED on an unclosed heredoc (#4877): if a delimiter never appears
    before EOF, the buffered lines were NOT a real body — a crafted or
    malformed opener must not make trailing REAL writes vanish from the
    tokenized view. Those lines are kept; only a heredoc that actually
    closes has its body + closer dropped.
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


def _collapse_shell_line_continuations(command: str) -> str:
    """Remove shell ``\\`` + newline continuations outside single quotes.

    The shell removes these pairs before parsing command boundaries, including
    inside double quotes. Leaving them in the guard's token stream turns one
    mutating command into two apparent segments and can hide the target of an
    in-place editor. Backslash-newline remains literal inside single quotes.
    """
    collapsed: list[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and not in_single and i + 1 < len(command):
            following = command[i + 1]
            if following == "\n":
                i += 2
                continue
            collapsed.extend((char, following))
            i += 2
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        collapsed.append(char)
        i += 1
    return "".join(collapsed)


# Characters the shell keeps literal inside quotes (or after a backslash) but
# that the expansion pass below would act on. They are swapped for private-use
# sentinels before shlex strips the quotes, so ``'$HOME/x'``, ``"~/x"`` and
# ``"A=b"`` stay literal, and are restored in every emitted word (#8500).
_LITERAL_SENTINELS = {"$": "", "`": "", "~": "", "=": ""}
_UNMASK = str.maketrans({v: k for k, v in _LITERAL_SENTINELS.items()})

# Shell operators a punctuation run is split into, longest first. shlex returns
# a run such as ``);`` or ``)&&`` as one token; the scope tracking below needs
# each ``(`` / ``)`` and each separator on its own.
_SHELL_OPERATORS = (
    "&>>", "<<<", "&>", ">>", ">|", "&&", "||", ";;", "|&", "<<", "<>", ">&", "<&",
    ">", "<", "|", "&", ";", "(", ")", "\n",
)
_PUNCTUATION = frozenset("();<>|&\n")


def _mask_quoted_literals(command: str) -> str:
    """Replace quote- or backslash-protected ``$ ` ~ =`` with sentinels.

    Inside single quotes all four are literal; inside double quotes ``~`` and
    ``=`` are (``$`` and backtick still expand); a backslash protects ``$`` and
    backtick anywhere outside single quotes and ``~`` / ``=`` outside quotes.
    """
    out: list[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and not in_single and i + 1 < len(command):
            following = command[i + 1]
            if following in "$`" or (not in_double and following in "~="):
                out.append(_LITERAL_SENTINELS[following])
            else:
                out.extend((char, following))
            i += 2
            continue
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char in _LITERAL_SENTINELS and (in_single or (in_double and char in "~=")):
            char = _LITERAL_SENTINELS[char]
        out.append(char)
        i += 1
    return "".join(out)


def _split_operator_run(token: str) -> list[str]:
    """Split a pure-punctuation token into shell operators (``);`` → ``)``, ``;``)."""
    if token in _SHELL_OPERATORS or not token or not set(token) <= _PUNCTUATION:
        return [token]
    parts: list[str] = []
    i = 0
    while i < len(token):
        op = next(o for o in _SHELL_OPERATORS if token.startswith(o, i))
        parts.append(op)
        i += len(op)
    return parts


def _tokenize(command: str) -> list[str]:
    """Quote-aware tokens with redirection/control operators kept separate.

    ``punctuation_chars`` makes shlex split ``();<>|&`` runs into their own
    tokens while still respecting quotes, so ``echo a>b`` yields
    ``['echo','a','>','b']`` but ``echo "a>b"`` keeps ``a>b`` intact — the whole
    reason this is Python and not a grep. Heredoc bodies are stripped first:
    document text carries no write targets (#4538). Quote-protected expansion
    characters come back masked (see ``_mask_quoted_literals``); only
    ``_expand_word`` turns tokens into the text the guard classifies.
    """
    try:
        lexer = shlex.shlex(
            _mask_quoted_literals(
                _collapse_shell_line_continuations(_strip_heredoc_bodies(command))
            ),
            posix=True,
            punctuation_chars="();<>|&\n",
        )
        lexer.whitespace_split = True
        # Keep newline out of whitespace so shlex returns it as a control
        # operator. Otherwise adjacent lines collapse into one segment: a later
        # command's option (for example `find -print`) can be mistaken for an
        # earlier `sed` invocation's `-i` flag and produce bogus write targets.
        lexer.whitespace = " \t\r"
        return [part for token in lexer for part in _split_operator_run(token)]
    except ValueError:
        # Unbalanced quotes / un-tokenizable — fail open (the shell will reject
        # the malformed command itself).
        return []


# ---------------------------------------------------------------------------
# same-command shell variable expansion (issues #5404 / #8500)
# ---------------------------------------------------------------------------

_VAR_REF_RE = re.compile(r"\$(?:([A-Za-z_][A-Za-z0-9_]*)|\{([A-Za-z_][A-Za-z0-9_]*)\})")
# ``NAME=``, ``NAME+=`` and ``NAME[i]=`` (group 2 subscript, group 3 ``+``).
_ASSIGN_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(\[[^\]]*\])?(\+?)=", re.DOTALL)
# The identifier a token starts with when an operator or the end follows it.
_LEADING_NAME_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(?=$|[\s=+\[\-*/%<>^|&!,:])")
# ``${NAME=x}`` / ``${NAME:=x}`` assign as a side effect of expanding.
_ASSIGNING_EXPANSION_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):?=")
_WHITESPACE_RE = re.compile(r"\s")

# Builtins whose ``NAME=value`` operands assign in the current shell.
_DECLARATION_BUILTINS = frozenset({"export", "declare", "typeset", "local", "readonly"})
# Of those, the ones that bind a variable in the current (top-level) shell.
_BINDING_DECLARATIONS = frozenset({"export", "declare", "typeset", "readonly"})
# Commands that can reassign any variable behind the parser's back.
_OPAQUE_ASSIGNERS = frozenset({"source", ".", "eval", "trap"})
# Commands whose operands name the variables they overwrite.
_CLOBBERERS = frozenset(
    {"read", "unset", "mapfile", "readarray", "getopts", "printf", "let", "wait", "coproc"}
)
# Reserved words that open / close a compound command, and that only prefix one.
_COMPOUND_OPENERS = frozenset({"if", "while", "until", "for", "select", "case", "{"})
_COMPOUND_CLOSERS = frozenset({"fi", "done", "esac", "}"})
_COMPOUND_PREFIXES = frozenset({"!", "then", "else", "elif", "do", "time"})
# An assignment is unconditional only when it runs whenever the command does: it
# starts a statement (not after ``&&`` / ``||`` / a pipe) and no pipe or
# background operator follows it. ``S=x && cmd`` and ``S=x || cmd`` qualify
# because their first element always runs.
_STATEMENT_START = frozenset({"", ";", "\n"})
_STATEMENT_END = frozenset({";", "\n", "&&", "||"})
# After these a newline continues the list rather than starting a new statement.
_CONTINUING_OPS = frozenset({"&&", "||", "|", "|&"})


class ShellWord(str):
    """A Bash word after same-command expansion; compares equal to its text.

    The string value is the word as the shell would see it. ``unresolved_at`` is
    the offset of the first expansion whose value the guard cannot know
    (``None`` when the word resolved completely); from that offset on the text
    is the raw, unexpanded remainder, kept for messages. ``raw`` is the word as
    written.
    """

    unresolved_at: Optional[int]  # noqa: UP045 - Python 3.9 parser
    raw: str

    def __new__(
        cls,
        text: str,
        unresolved_at: Optional[int] = None,  # noqa: UP045 - Python 3.9 parser
        raw: Optional[str] = None,  # noqa: UP045 - Python 3.9 parser
    ) -> ShellWord:
        word = super().__new__(cls, text)
        word.unresolved_at = unresolved_at
        word.raw = text if raw is None else raw
        return word

    def tail(self, start: int) -> ShellWord:
        """``self[start:]`` keeping the unresolved offset (``-C<path>`` form)."""
        at = self.unresolved_at
        return ShellWord(
            str(self)[start:], None if at is None else max(0, at - start), self.raw
        )


Bindings = dict[str, Optional[str]]  # noqa: UP045 - Python 3.9 parser
Lookup = Callable[[str], Optional[str]]  # noqa: UP045 - Python 3.9 parser


def _expand_word(token: str, lookup: Lookup) -> ShellWord:
    """Expand ``~``, ``$NAME`` and ``${NAME}`` in one masked token.

    ``lookup`` returns a variable's known value or ``None``. Anything else that
    expands — ``$(...)``, backticks, ``${NAME:-x}``, positional/special
    parameters, a name without a known value — stops the expansion there and
    marks the word unresolved at that offset.
    """
    raw = token.translate(_UNMASK)
    out: list[str] = []
    i = 0
    if token.startswith("~"):
        end = token.find("/")
        end = len(token) if end < 0 else end
        user = token[1:end]
        if not user:
            home = lookup("HOME")
            if home is None:
                return ShellWord(raw, 0, raw)
            out.append(home)
            i = end
        elif re.fullmatch(r"[A-Za-z0-9._-]+", user):
            home = os.path.expanduser(token[:end])
            if home != token[:end]:  # unknown user: bash keeps ~user literal
                out.append(home)
                i = end
    while i < len(token):
        char = token[i]
        if char in "$`":
            match = _VAR_REF_RE.match(token, i) if char == "$" else None
            value = lookup(match.group(1) or match.group(2)) if match else None
            if match is None or value is None:
                prefix = "".join(out).translate(_UNMASK)
                return ShellWord(prefix + token[i:].translate(_UNMASK), len(prefix), raw)
            out.append(value)
            i = match.end()
            continue
        out.append(char)
        i += 1
    return ShellWord("".join(out).translate(_UNMASK), None, raw)


class _Expander:
    """Walks the tokens once, tracking which variables hold a *known* value.

    A variable is known only while its last assignment is an unconditional,
    top-level literal one (see the module docstring). Every other way a value
    can change — an assignment in a branch, compound command, subshell, pipeline
    stage or function; ``read``/``for``/``unset``/…; ``$(...)``; ``source`` — makes
    it unknown *from that point on*, and an unknown value shadows the
    inherited environment (``$HOME`` included).

    The walk runs twice. The first pass only collects which names are ever
    assigned and how; the second uses that for code that can run again or later
    (loop bodies, function bodies, subshells): a variable is usable there only
    if it was never made unknown and only ever held one literal value.
    """

    def __init__(self, tokens: list[str], first: Optional[_Expander] = None) -> None:  # noqa: UP045
        self.tokens = tokens
        self.bindings: Bindings = {}
        self.values: dict[str, set[str]] = {}
        self.tainted: set[str] = set()
        self.frames: list[str] = []  # "paren" | "compound" | "case"
        self.poisoned = False  # unbalanced scope: nothing after is unconditional
        self.ifs_changed = False  # unquoted values may split anywhere: none is known
        self.assigned: Optional[set[str]] = None  # noqa: UP045
        self.stable: Optional[set[str]] = None  # noqa: UP045
        if first is not None:
            self.assigned = set(first.values) | first.tainted
            self.stable = {
                name
                for name, seen in first.values.items()
                if name not in first.tainted and len(seen) == 1
            }

    # -- variable state ------------------------------------------------------

    def _lookup(self, name: str) -> Optional[str]:  # noqa: UP045
        replayable = self.assigned is not None and (self.frames or self.poisoned)
        if replayable and name in self.assigned:
            return self.bindings.get(name) if name in (self.stable or ()) else None
        if name in self.bindings:
            return self.bindings[name]
        if name == "HOME":
            return os.environ.get("HOME") or None
        return None

    def _forget(self, name: str) -> None:
        self.bindings[name] = None
        self.tainted.add(name)
        if name == "IFS":
            self.ifs_changed = True
            self._opaque()

    def _opaque(self) -> None:
        for name in {*self.bindings, "HOME"}:
            self.bindings[name] = None
            self.tainted.add(name)

    def _assign(self, token: str, *, unconditional: bool) -> None:
        match = _ASSIGN_RE.match(token)
        name = match.group(1)
        if match.group(2) or match.group(3) or not unconditional or self.ifs_changed:
            self._forget(name)
            return
        word = self._expand(token[match.end():])
        if word.unresolved_at is not None or _WHITESPACE_RE.search(word):
            self._forget(name)  # unquoted use would word-split
            return
        if name == "IFS":
            self._forget(name)
            return
        self.values.setdefault(name, set()).add(str(word))
        self.bindings[name] = str(word)

    def _forget_leading_names(self, tokens: list[str]) -> None:
        for tok in tokens:
            match = _LEADING_NAME_RE.match(tok)
            if match:
                self._forget(match.group(1))

    def _expand(self, token: str) -> ShellWord:
        for match in _ASSIGNING_EXPANSION_RE.finditer(token):
            self._forget(match.group(1))
        return _expand_word(token, self._lookup)

    # -- scope tracking ------------------------------------------------------

    def _operator(self, op: str) -> None:
        if op == "(":
            self.frames.append("paren")
        elif op == ")":
            if self.frames and self.frames[-1] == "paren":
                self.frames.pop()
            elif not self.frames or self.frames[-1] != "case":  # ``pattern)`` is fine
                self.poisoned = True

    def _strip_reserved(self, tokens: list[str]) -> tuple[list[str], str]:
        """Drop leading reserved words (tracking scope); return rest + loop header."""
        header = ""
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in _COMPOUND_OPENERS:
                self.frames.append("case" if tok == "case" else "compound")
                if tok in ("for", "select"):
                    header = tok
            elif tok in _COMPOUND_CLOSERS:
                if self.frames and self.frames[-1] in ("compound", "case"):
                    self.frames.pop()
                else:
                    self.poisoned = True
            elif tok == "function":
                i += 1  # its name
            elif tok not in _COMPOUND_PREFIXES:
                break
            i += 1
        return tokens[i:], header

    # -- segments ------------------------------------------------------------

    def _segment(self, tokens: list[str], prev_op: str, next_op: str) -> list[ShellWord]:
        body, header = self._strip_reserved(tokens)
        if not body:
            return []
        unconditional = (
            not self.frames
            and not self.poisoned
            and prev_op in _STATEMENT_START
            and next_op in _STATEMENT_END
        )
        lead = 0
        while lead < len(body) and _ASSIGN_RE.match(body[lead]):
            lead += 1
        if lead == len(body):
            # Pure assignment statement: bash assigns left to right.
            words = []
            for tok in body:
                words.append(self._expand(tok))
                self._assign(tok, unconditional=unconditional)
            return words

        # Expansion sees the state from before this command's own effects.
        words = [self._expand(tok) for tok in body]
        if header:
            self._forget_leading_names(body)
        for tok in body[:lead]:  # ``S=x cmd``: cmd's environment, never a binding
            self._forget(_ASSIGN_RE.match(tok).group(1))
        if "paren" in self.frames:  # ``(( S = 5 ))``, ``(S++)`` …
            self._forget_leading_names(body[lead:])
        self._command_effects(body, unconditional=unconditional)
        return words

    def _command_effects(self, body: list[str], *, unconditional: bool) -> None:
        cmd, idx = _command_word(body)
        args = body[idx + 1:]
        if cmd in _OPAQUE_ASSIGNERS:
            self._opaque()
        elif cmd in _DECLARATION_BUILTINS:
            if cmd != "export" and any(t.startswith("-") and "n" in t[1:] for t in args):
                self._opaque()  # namerefs alias an arbitrary variable
                return
            for tok in args:
                if _ASSIGN_RE.match(tok):
                    self._assign(
                        tok, unconditional=unconditional and cmd in _BINDING_DECLARATIONS
                    )
                elif cmd != "export":
                    self._forget_leading_names([tok])
        elif cmd in _CLOBBERERS:
            self._forget_leading_names(args)

    def run(self) -> list[list[ShellWord]]:
        segments: list[list[ShellWord]] = []
        current: list[str] = []
        prev_op = ""
        for tok in [*self.tokens, ";"]:
            if tok not in _CONTROL_OPS:
                current.append(tok)
                continue
            if current:
                words = self._segment(current, prev_op, tok)
                if words:
                    segments.append(words)
                current = []
            elif tok == "\n" and prev_op in _CONTINUING_OPS:
                continue
            self._operator(tok)
            prev_op = tok
        return segments


def _expanded_segments(command: str) -> list[list[ShellWord]]:
    """Per-command segments of expanded words, in command order.

    Variable values come only from the command itself — earlier unconditional
    top-level literal assignments — plus ``$HOME``/``~`` from the environment
    while nothing in the command touches ``HOME``. Words whose value is unknown
    carry ``unresolved_at``; ``_bash_path_decision`` blocks those.
    """
    tokens = _tokenize(command)
    first = _Expander(tokens)
    first.run()
    return _Expander(tokens, first=first).run()


def _redirect_targets(tokens: list[str]) -> list[str]:
    """Files named as the destination of a ``>``/``>>``/``&>`` redirection."""
    targets: list[str] = []
    for i, tok in enumerate(tokens):
        if tok in _FILE_REDIRECTS and i + 1 < len(tokens):
            dest = tokens[i + 1]
            # ``>&1`` / ``> &2`` duplicate a descriptor, and a bare number is a
            # descriptor too — neither is a file write.
            if dest.startswith("&") or dest.isdigit():
                continue
            targets.append(dest)
    return targets


def _command_word(segment: list[str]) -> tuple[str, int]:
    """First real command word of a segment and its index, skipping wrappers.

    Skips leading ``VAR=val`` assignments and common wrappers (``sudo``,
    ``env``, ``time``, ``nohup``, ``command``) so ``sudo tee x`` still reads as
    a ``tee``.
    """
    i = 0
    while i < len(segment):
        tok = segment[i]
        if "=" in tok and not tok.startswith("-") and tok.split("=", 1)[0].isidentifier():
            i += 1  # leading environment assignment
            continue
        if tok in {"sudo", "env", "time", "nohup", "command", "builtin", "exec"}:
            i += 1
            continue
        break
    if i >= len(segment):
        return "", i
    return Path(segment[i]).name, i


def _tee_targets(segment: list[str], cmd_index: int) -> list[str]:
    """Non-flag operands of a ``tee`` invocation (its output files)."""
    targets: list[str] = []
    for tok in segment[cmd_index + 1:]:
        if tok.startswith("-"):
            continue  # -a / --append / -i / -p
        targets.append(tok)
    return targets


def _inplace_edit_targets(segment: list[str], cmd_index: int) -> list[str]:
    """File operands of an in-place ``sed -i`` / ``perl -i`` invocation.

    Only fires when an in-place flag is present. The editor's *script* is
    excluded so it is never mistaken for a file path: with an explicit
    ``-e``/``-f`` script every positional is a file; otherwise the first
    positional is the script and the rest are files.
    """
    args = segment[cmd_index + 1:]
    has_inplace = False
    has_explicit_script = False
    files: list[str] = []
    skip_next = False
    first_positional_seen = False

    for tok in args:
        if skip_next:
            skip_next = False
            has_explicit_script = True  # value of -e/-f was the script, not a file
            continue
        if tok.startswith("--"):
            long = tok[2:]
            if long.startswith("in-place"):  # --in-place / --in-place=.bak
                has_inplace = True
            if long in ("expression", "file"):
                skip_next = True
            continue
        if tok.startswith("-") and len(tok) > 1:
            # Short-flag cluster (``-i``, ``-i.bak``, ``-Ei``, perl ``-pi``).
            # Among sed/perl short switches only ``-i`` carries an ``i``.
            if "i" in tok[1:]:
                has_inplace = True
            if tok in ("-e", "-f"):
                skip_next = True
            continue
        # BSD sed's ``-i ''`` has an empty backup suffix. It is neither a
        # script nor a file, and must not consume the real inline script.
        if tok == "":
            continue
        # Positional token.
        if not has_explicit_script and not first_positional_seen:
            first_positional_seen = True  # inline script (no -e); never a file
            continue
        files.append(tok)

    return files if has_inplace else []


def bash_write_targets(command: str) -> list[str]:
    """Best-effort list of files a Bash command would create/modify.

    Covers redirection, ``tee``, and ``sed -i``/``perl -i``. Other write
    vectors are intentionally out of scope (see module docstring); they rely on
    physical worktree isolation and the monitor/git-shim layers.
    """
    targets: list[str] = []
    for segment in _expanded_segments(command):
        targets.extend(_redirect_targets(segment))
        cmd, idx = _command_word(segment)
        if cmd == "tee":
            targets.extend(_tee_targets(segment, idx))
        elif cmd in ("sed", "perl"):
            targets.extend(_inplace_edit_targets(segment, idx))
    return targets


# ---------------------------------------------------------------------------
# git-mediated working-tree writes (issue #5396)
# ---------------------------------------------------------------------------


def _git_global_prefix(
    args: list[str],
) -> tuple[Optional[str], list[str]]:  # noqa: UP045 - Python 3.9 parser
    """Strip git global options; return optional ``-C`` path and remaining args.

    Handles ``-C <path>``, ``-C<path>``, and common no-arg globals (``-c`` is
    two-token). Unknown long options with ``=`` are skipped; bare long options
    that take a value are not fully modeled — fail-open if we cannot parse.
    """
    c_path: Optional[str] = None  # noqa: UP045 - Python 3.9 parser
    i = 0
    n = len(args)
    while i < n:
        tok = args[i]
        if tok == "-C" and i + 1 < n:
            c_path = args[i + 1]
            i += 2
            continue
        if tok.startswith("-C") and len(tok) > 2:
            c_path = tok.tail(2) if isinstance(tok, ShellWord) else tok[2:]
            i += 1
            continue
        if tok in {"-c", "--config-env", "--exec-path", "--git-dir", "--work-tree",
                   "--namespace", "--super-prefix", "--list-cmds"} and i + 1 < n:
            i += 2
            continue
        if tok.startswith("-c") and len(tok) > 2 and "=" in tok:
            i += 1
            continue
        if tok.startswith("--") and "=" in tok:
            i += 1
            continue
        if tok in {"--bare", "--no-replace-objects", "--literal-pathspecs",
                   "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs",
                   "--no-optional-locks", "-p", "--paginate", "-P", "--no-pager"}:
            i += 1
            continue
        # Subcommand or unknown option starts the remainder.
        break
    return c_path, args[i:]


def _is_git_binary(cmd: str) -> bool:
    return cmd in {"git", "git.exe"} or cmd.endswith("/git")


def bash_git_write_intents(command: str) -> list[dict[str, object]]:
    """Parse Bash for git-mediated working-tree mutations (issue #5396).

    Each intent is a dict::

        {
          "kind": "apply"|"add"|"stash_apply"|"path_checkout"|"restore_source",
          "c_path": str|None,          # from git -C
          "paths": list[str],          # pathspecs when known (may be empty)
          "summary": str,              # human-readable for the block message
          "allowlisted": bool,         # True → never block (rescue clean)
        }

    Allowlisted: ``git checkout -- <paths>`` and ``git restore <paths>`` without
    ``--source`` (discard dirt / restore from index — rescue pattern).
    """
    intents: list[dict[str, object]] = []
    for segment in _expanded_segments(command):
        cmd, idx = _command_word(segment)
        if not _is_git_binary(cmd):
            continue
        c_path, rest = _git_global_prefix(segment[idx + 1 :])
        if not rest:
            continue
        sub = rest[0]
        sub_args = rest[1:]

        if sub in {"apply", "am"}:
            intents.append(
                {
                    "kind": "apply" if sub == "apply" else "am",
                    "c_path": c_path,
                    "paths": [],
                    "summary": f"git {sub}",
                    "allowlisted": False,
                }
            )
            continue

        if sub == "add":
            # Drop flags; remaining positionals are pathspecs (may be empty = all).
            paths: list[str] = []
            i = 0
            while i < len(sub_args):
                tok = sub_args[i]
                if tok == "--":
                    paths.extend(sub_args[i + 1 :])
                    break
                if tok.startswith("-"):
                    # Value-taking short options we care about: -u is flag-only.
                    if tok in {"-C"}:  # not expected after subcommand
                        i += 2
                        continue
                    i += 1
                    continue
                paths.append(tok)
                i += 1
            intents.append(
                {
                    "kind": "add",
                    "c_path": c_path,
                    "paths": paths,
                    "summary": "git add" + (f" {' '.join(paths)}" if paths else ""),
                    "allowlisted": False,
                }
            )
            continue

        if sub == "stash":
            if not sub_args:
                continue
            action = sub_args[0]
            if action in {"pop", "apply"}:
                intents.append(
                    {
                        "kind": "stash_apply",
                        "c_path": c_path,
                        "paths": [],
                        "summary": f"git stash {action}",
                        "allowlisted": False,
                    }
                )
            continue

        if sub == "checkout":
            # Allowlist: `git checkout -- <paths>` (restore from index/HEAD).
            # Block: `git checkout <tree-ish> -- <paths>` and the no-dashdash
            # form `git checkout <tree-ish> <path>…` (#5517).
            # Branch-only checkouts (single non-flag arg, no paths) stay out —
            # other guards own branch switches.
            if "--" in sub_args:
                dd = sub_args.index("--")
                before = sub_args[:dd]
                after = sub_args[dd + 1 :]
                treeish = [t for t in before if not t.startswith("-")]
                if not treeish:
                    intents.append(
                        {
                            "kind": "path_checkout",
                            "c_path": c_path,
                            "paths": after,
                            "summary": "git checkout -- " + " ".join(after),
                            "allowlisted": True,
                        }
                    )
                else:
                    intents.append(
                        {
                            "kind": "path_checkout",
                            "c_path": c_path,
                            "paths": after,
                            "summary": f"git checkout {treeish[0]} -- " + " ".join(after),
                            "allowlisted": False,
                        }
                    )
            else:
                positionals = [t for t in sub_args if not t.startswith("-")]
                if len(positionals) >= 2:
                    # tree-ish + one or more pathspecs (no `--` separator).
                    intents.append(
                        {
                            "kind": "path_checkout",
                            "c_path": c_path,
                            "paths": positionals[1:],
                            "summary": (
                                f"git checkout {positionals[0]} "
                                + " ".join(positionals[1:])
                            ),
                            "allowlisted": False,
                        }
                    )
            continue

        if sub == "restore":
            source = None
            paths: list[str] = []
            i = 0
            while i < len(sub_args):
                tok = sub_args[i]
                if tok == "--":
                    paths.extend(sub_args[i + 1 :])
                    break
                if tok.startswith("--source="):
                    source = tok.split("=", 1)[1]
                    i += 1
                    continue
                if tok == "--source" and i + 1 < len(sub_args):
                    source = sub_args[i + 1]
                    i += 2
                    continue
                if tok.startswith("-"):
                    i += 1
                    continue
                paths.append(tok)
                i += 1
            if source is None:
                intents.append(
                    {
                        "kind": "restore_source",
                        "c_path": c_path,
                        "paths": paths,
                        "summary": "git restore " + " ".join(paths),
                        "allowlisted": True,
                    }
                )
            else:
                intents.append(
                    {
                        "kind": "restore_source",
                        "c_path": c_path,
                        "paths": paths,
                        "summary": f"git restore --source={source} " + " ".join(paths),
                        "allowlisted": False,
                    }
                )
            continue

        if sub in {"mv", "rm"}:
            # Both mutate the index and the working tree (#5517).
            paths: list[str] = []
            i = 0
            while i < len(sub_args):
                tok = sub_args[i]
                if tok == "--":
                    paths.extend(sub_args[i + 1 :])
                    break
                if tok.startswith("-"):
                    i += 1
                    continue
                paths.append(tok)
                i += 1
            intents.append(
                {
                    "kind": "mv" if sub == "mv" else "rm",
                    "c_path": c_path,
                    "paths": paths,
                    "summary": f"git {sub}" + (f" {' '.join(paths)}" if paths else ""),
                    "allowlisted": False,
                }
            )
            continue

    return intents


def _effective_git_cwd(intent: dict[str, object], payload_cwd: str) -> Path:
    """Resolve the worktree a git intent would mutate (``-C`` already expanded)."""
    c_path = intent.get("c_path")
    if isinstance(c_path, str) and c_path:
        return _resolve(c_path, payload_cwd, expand_user=False)
    return Path(payload_cwd).expanduser().resolve()


def _block_git_mediated(summary: str, main_root: Path, reason: str) -> int:
    sys.stderr.write(
        f"BLOCKED by guard-primary-checkout-write: git-mediated write "
        f"'{summary}' would mutate the protected primary checkout "
        f"({main_root}) [{reason}] (issue #5396).\n\n"
        "Silent shell cwd resets have applied worker patches into primary "
        "before — never run git apply/add/stash-pop or path-checkout against "
        "the primary tree. Use an explicit worktree:\n\n"
        "  git -C .worktrees/dispatch/<agent>/<task> apply /tmp/worker.diff\n"
        "  # or: cd .worktrees/dispatch/<agent>/<task> && git apply …\n\n"
        "Rescue clean (allowed): git checkout -- <path>  or  git restore <path>\n"
        "Emergency override (one-shot): LEARN_UK_ALLOW_PRIMARY_GIT_WRITE=1\n\n"
        "Hook source: agents_extensions/shared/hooks/"
        "guard-primary-checkout-write.py\n"
    )
    return 2


# ---------------------------------------------------------------------------
# decision
# ---------------------------------------------------------------------------

class _UnresolvedWrite:
    """Decision for a path whose location depends on an unknown shell value."""

    allowed = False
    reason = "unresolved_shell_variable"
    message = (
        "The write target depends on a shell value the guard cannot resolve. "
        "Assign it with a literal value earlier in the same command "
        '(S=/tmp/scratch; echo x > "$S/out.txt") or use a literal path.'
    )


def _resolve(path_str: str, cwd: str, *, expand_user: bool = True) -> Path:
    """Resolve a possibly-relative target against the payload cwd.

    Bash words arrive already tilde-expanded (``_expand_word``), so they pass
    ``expand_user=False``: a ``~`` still present there was quoted and is literal.
    """
    path = Path(path_str).expanduser() if expand_user else Path(path_str)
    if not path.is_absolute():
        path = Path(cwd) / path
    return path


def _bash_path_decision(word: str, base: str, wc) -> object:
    """Containment decision for one expanded Bash path word.

    A word holding any unknown expansion is blocked outright: the unknown value
    may be absolute, empty or contain ``..``, so no literal prefix proves the
    path stays out of the primary checkout.
    """
    if getattr(word, "unresolved_at", None) is not None:
        return _UnresolvedWrite()
    return wc.evaluate_write(_resolve(word, base, expand_user=False), cwd=base)


def _label(word: str) -> str:
    raw = getattr(word, "raw", word)
    return word if raw == word else f"{raw}→{word}"


def main() -> int:
    payload = _read_payload()
    tool_name = _tool_name(payload)
    if not tool_name:
        return 0

    tool_input = _tool_input(payload)
    cwd = _payload_cwd(payload)
    command = ""

    if tool_name == "Bash":
        command = str(tool_input.get("command") or "")
        if not command.strip():
            return 0
        raw_targets = bash_write_targets(command)
    else:
        raw_targets = write_tool_targets(tool_input)

    # Git commands mutate outside shell redirections/write-tool payloads, so
    # retain their parsed intents for the primary-checkout containment pass.
    git_intents: list[dict[str, object]] = []
    if tool_name == "Bash" and command:
        try:
            git_intents = bash_git_write_intents(command)
        except Exception:  # pragma: no cover - defensive fail-open
            git_intents = []

    wc = _load_containment()

    if wc is None:
        return 0

    # Enforce only while the primary checkout sits on a protected branch. If the
    # human has deliberately checked the primary tree onto a feature branch, git
    # can't resolve it, or any classification errors, this hook stays out of the
    # way (fail open) — physical worktree isolation is the real guarantee.
    try:
        main_root = wc.resolve_main_root(cwd)
        if not wc.is_protected_branch(main_root):
            return 0
    except Exception:  # pragma: no cover - defensive fail-open
        return 0

    # --- #5396: git-mediated mutations against the primary worktree ----------
    allow_primary_git = os.environ.get("LEARN_UK_ALLOW_PRIMARY_GIT_WRITE", "") == "1"
    if tool_name == "Bash" and command and not allow_primary_git:
        try:
            for intent in git_intents:
                if intent.get("allowlisted"):
                    continue
                summary = str(intent.get("summary") or "git write")
                c_path = intent.get("c_path")
                if getattr(c_path, "unresolved_at", None) is not None:
                    return _block_git_mediated(
                        summary, main_root, reason="unresolved_shell_variable"
                    )
                git_cwd = _effective_git_cwd(intent, cwd)
                # Only care when the effective git worktree *is* the primary.
                try:
                    if not wc.is_primary_checkout(git_cwd):
                        continue
                except Exception:
                    continue
                paths = list(intent.get("paths") or [])
                if not paths:
                    # Whole-tree mutator (apply / am / stash pop|apply / bare add).
                    return _block_git_mediated(
                        summary, main_root, reason="git_mediated_primary_worktree"
                    )
                # Path-scoped mutators: block if any path is a protected primary write.
                for raw in paths:
                    decision = _bash_path_decision(raw, str(git_cwd), wc)
                    if not decision.allowed:
                        return _block_git_mediated(
                            summary, main_root, reason=decision.reason
                        )
        except Exception:  # pragma: no cover - defensive fail-open
            pass

    if not raw_targets:
        return 0

    try:
        decisions: list[tuple[str, object]] = []
        for raw in raw_targets:
            if tool_name == "Bash":
                # Words were expanded from same-command assignments (#5404 /
                # #8500); any unknown value blocks (_bash_path_decision).
                decision = _bash_path_decision(raw, cwd, wc)
            else:
                decision = wc.evaluate_write(_resolve(raw, cwd), cwd=cwd)
            decisions.append((_label(raw), decision))
    except Exception:  # pragma: no cover - defensive fail-open
        return 0

    for raw, decision in decisions:
        if not decision.allowed:
            sys.stderr.write(
                f"BLOCKED by guard-primary-checkout-write: {tool_name} would write "
                f"'{raw}' inside the protected primary checkout ({main_root}) "
                f"[{decision.reason}].\n\n"
                "The primary checkout must stay clean on `main`. Do all write "
                "work in a dispatch worktree instead:\n\n"
                "  git worktree add .worktrees/dispatch/<agent>/<task> "
                "-b <agent>/<task>\n"
                "  cd .worktrees/dispatch/<agent>/<task>\n"
                "  # ...edits, commits, push, PR...\n\n"
                f"{decision.message}\n"
                "Hook source: agents_extensions/shared/hooks/"
                "guard-primary-checkout-write.py\n"
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
