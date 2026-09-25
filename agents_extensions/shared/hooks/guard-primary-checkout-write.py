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
allowed. Recognized read-only commands (``git status``, ``git log``, ``rg``,
``cat`` …) expose no write target.

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
* ``Bash`` — write-capable redirection (including ``>&`` file operands and
  ``<>``), ``tee``, ``dd of=``, copy/move/link/install/rsync destinations,
  removed ``mv`` / ``rsync --remove-source-files`` sources, direct filesystem
  mutators (``rm``, ``unlink``, ``rmdir``, ``truncate``, ``shred``, ``chmod``,
  ``chown``, ``touch``), and in-place editors (``sed -i`` / ``perl -i``).
  Quote-aware tokenization keeps a
  ``>`` inside a quoted string (e.g. a commit message) from reading as a
  redirect. Literal ``cd``/``pushd`` change the base of following relative
  targets; uncertain navigation blocks those targets. Common command wrappers,
  ``find -exec`` writers, and executable substitutions in unquoted heredocs
  feed the same writer parser. Decidable ``eval`` strings are parsed
  recursively; undecidable ones always block. ``xargs`` / ``parallel`` writers block when their
  generated arguments can supply a primary target.
* ``Bash`` git-mediated working-tree writes (issues #5396 / #5517) — ``git apply`` /
  ``git am``, ``git add``, ``git stash pop|apply``, ``git mv`` / ``git rm``,
  ``git checkout <ref> -- <path>``, ``git checkout <ref> <path>`` (no ``--``),
  ``git clean`` / destructive ``reset`` / ``read-tree -u`` / forced ``checkout``,
  and ``git restore --source=…`` when the effective git worktree (payload cwd
  or ``git -C``) is the protected primary checkout. Rescue clean forms
  ``git checkout -- <path>`` and plain ``git restore <path>`` (no ``--source``)
  remain allowed so operators can discard accidental dirt.
* Precise transfer parsing for rsync and git archive; conservative positional
  classification for long-tail writers (curl, wget, sort, SQLite, tar, unzip,
  patch, tee, truncate, split, csplit, ffmpeg, convert). Known short-option
  values are parsed by command. Curl ``-K``/``-T`` and patch ``-i`` are read
  inputs; curl ``-O`` and wget default output use a cwd-relative remote
  filename. cp/mv ``--backup`` and
  ``--suffix`` modify the classified destination; rsync ``--compare-dest`` and
  ``--link-dest`` only read their paths.

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
* Codex Desktop direct-edit interception is unverified (#4447). Where a provider
  does not emit a hookable write event, this hook cannot enforce that path; the
  enforcement layer is #4445/#4446/#4449 instead. See
  ``docs/runbooks/codex-hooks.md``.

Known residuals
---------------
This command parser does not model arbitrary interpreters (for example,
``python -c``, ``node -e``, or ``perl -e`` writing files), ``$EDITOR``, or
binaries that write without path arguments. Long-tail writers conservatively
classify every path-like argument, including read-only inputs such as
``sort PRIMARY/file -o /tmp/out``; this accepted false positive keeps new
output options from silently escaping the guard. Targets supplied only through
stdin or an external file list with unknown contents remain invisible: for
example, ``find -files0-from /tmp/list -delete`` and
``cat /tmp/list | xargs -I{} sh -c 'echo x > {}'`` are allowed from a dispatch
worktree. This is the same rule as ``cat /tmp/list | xargs tee``: fail closed
only when a command literal names the primary checkout or the effective cwd
is the primary checkout. Config files such as curl ``-K`` may themselves
direct writes; their contents are not inspected. Unlisted writers and shell
features not parsed here remain residuals. This is defense-in-depth, not a
sandbox; physical worktree isolation and the monitor remain necessary.

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
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


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
                path = line[len(header) :].strip()
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

# ``>&`` duplicates a descriptor only for a numeric operand (or closes it for
# ``-``); otherwise it opens a file. ``<>`` opens read-write and can create.
_FILE_REDIRECTS = frozenset({">", ">>", ">|", "&>", "&>>", ">&", "<>"})


def _strip_quotes_for_heredoc(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _heredoc_delimiters(line: str) -> list[tuple[str, bool, bool]]:
    try:
        lexer = shlex.shlex(line, posix=False, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return []

    delimiters: list[tuple[str, bool, bool]] = []
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
            delimiters.append((delimiter, strip_tabs, delim_tok != delimiter))
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
        substitutions: list[str] = []
        while i < n and pending:
            delimiter, strip_tabs, quoted = pending[0]
            candidate = lines[i].lstrip("\t") if strip_tabs else lines[i]
            if candidate == delimiter:
                pending.pop(0)
            elif not quoted:
                substitutions.extend(_heredoc_substitutions(lines[i]))
            i += 1
        if pending:
            kept.extend(lines[body_start:i])
        else:
            # Unquoted delimiters expand command substitutions in the body.
            # Keep only those executable fragments, never ordinary document
            # text (which may contain redirect-looking punctuation).
            kept.extend(substitutions)
    return "\n".join(kept)


def _heredoc_substitutions(line: str) -> list[str]:
    """Executable substitutions in one unquoted heredoc body line."""
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
            start = i
            i += 1
            while i < len(line) and line[i] != "`":
                i += 2 if line[i] == "\\" else 1
            i = min(i + 1, len(line))
            found.append("$(" + line[start + 1 : i - 1] + ")")
            continue
        i += 1
    return found


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
    "&>>",
    "<<<",
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
            _mask_quoted_literals(_collapse_shell_line_continuations(_strip_heredoc_bodies(command))),
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
_CLOBBERERS = frozenset({"read", "unset", "mapfile", "readarray", "getopts", "printf", "let", "wait", "coproc"})
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
    base: str | None
    decision_reason: str | None

    def __new__(
        cls,
        text: str,
        unresolved_at: Optional[int] = None,  # noqa: UP045 - Python 3.9 parser
        raw: Optional[str] = None,  # noqa: UP045 - Python 3.9 parser
    ) -> ShellWord:
        word = super().__new__(cls, text)
        word.unresolved_at = unresolved_at
        word.raw = text if raw is None else raw
        word.base = None
        word.decision_reason = None
        return word

    def tail(self, start: int) -> ShellWord:
        """``self[start:]`` keeping the unresolved offset (``-C<path>`` form)."""
        at = self.unresolved_at
        return ShellWord(str(self)[start:], None if at is None else max(0, at - start), self.raw)


class ShellSegment(list):
    """Expanded words with their shell scope and neighboring control operators."""

    def __init__(self, words: list[ShellWord], scope: tuple[int, ...], prev_op: str, next_op: str) -> None:
        super().__init__(words)
        self.scope = scope
        self.prev_op = prev_op
        self.next_op = next_op


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
        self.paren_serial = 0
        self.poisoned = False  # unbalanced scope: nothing after is unconditional
        self.ifs_changed = False  # unquoted values may split anywhere: none is known
        self.assigned: Optional[set[str]] = None  # noqa: UP045
        self.stable: Optional[set[str]] = None  # noqa: UP045
        if first is not None:
            self.assigned = set(first.values) | first.tainted
            self.stable = {name for name, seen in first.values.items() if name not in first.tainted and len(seen) == 1}

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
        word = self._expand(token[match.end() :])
        if word.unresolved_at is not None:
            self._forget(name)
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

    def _expand(self, token: str, *, eval_arg: bool = False) -> ShellWord:
        for match in _ASSIGNING_EXPANSION_RE.finditer(token):
            self._forget(match.group(1))
        # A quoted command string may contain spaces. Other uses of such a
        # binding are undecidable because unquoted expansion may word-split.
        lookup = (
            self._lookup
            if eval_arg
            else lambda name: (
                value if (value := self._lookup(name)) is not None and not _WHITESPACE_RE.search(value) else None
            )
        )
        return _expand_word(token, lookup)

    # -- scope tracking ------------------------------------------------------

    def _operator(self, op: str) -> None:
        if op == "(":
            self.paren_serial += 1
            self.frames.append(f"paren:{self.paren_serial}")
        elif op == ")":
            if self.frames and self.frames[-1].startswith("paren:"):
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
            not self.frames and not self.poisoned and prev_op in _STATEMENT_START and next_op in _STATEMENT_END
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
        cmd, cmd_index = _command_word(body)
        words = [self._expand(tok, eval_arg=cmd == "eval" and i > cmd_index) for i, tok in enumerate(body)]
        if header:
            self._forget_leading_names(body)
        for tok in body[:lead]:  # ``S=x cmd``: cmd's environment, never a binding
            self._forget(_ASSIGN_RE.match(tok).group(1))
        if any(frame.startswith("paren:") for frame in self.frames):
            self._forget_leading_names(body[lead:])
        self._command_effects(body, unconditional=unconditional)
        return words

    def _command_effects(self, body: list[str], *, unconditional: bool) -> None:
        cmd, idx = _command_word(body)
        args = body[idx + 1 :]
        if cmd in _OPAQUE_ASSIGNERS:
            self._opaque()
        elif cmd in _DECLARATION_BUILTINS:
            if cmd != "export" and any(t.startswith("-") and "n" in t[1:] for t in args):
                self._opaque()  # namerefs alias an arbitrary variable
                return
            for tok in args:
                if _ASSIGN_RE.match(tok):
                    self._assign(tok, unconditional=unconditional and cmd in _BINDING_DECLARATIONS)
                elif cmd != "export":
                    self._forget_leading_names([tok])
        elif cmd in _CLOBBERERS:
            self._forget_leading_names(args)

    def run(self) -> list[ShellSegment]:
        segments: list[ShellSegment] = []
        current: list[str] = []
        prev_op = ""
        for tok in [*self.tokens, ";"]:
            if tok not in _CONTROL_OPS:
                current.append(tok)
                continue
            if current:
                words = self._segment(current, prev_op, tok)
                if words:
                    scope = tuple(int(frame.split(":", 1)[1]) for frame in self.frames if frame.startswith("paren:"))
                    segments.append(ShellSegment(words, scope, prev_op, tok))
                current = []
            elif tok == "\n" and prev_op in _CONTINUING_OPS:
                continue
            self._operator(tok)
            prev_op = tok
        return segments


def _expanded_segments(command: str) -> list[ShellSegment]:
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
    """Files opened for writing by shell redirections."""
    targets: list[str] = []
    for i, tok in enumerate(tokens):
        if tok in _FILE_REDIRECTS and i + 1 < len(tokens):
            dest = tokens[i + 1]
            # ``>&1`` duplicates a descriptor; ``>&-`` closes it. Ordinary
            # ``> 123`` writes a file named 123, so only ``>&`` gets this rule.
            if tok == ">&" and (dest.isdigit() or dest == "-"):
                continue
            if tok != ">&" and dest.startswith("&"):
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
        if _ASSIGN_RE.match(tok):
            i += 1  # leading environment assignment
            continue
        if tok in {"time", "nohup", "builtin", "exec"}:
            i += 1
            continue
        if tok == "command":
            i += 1
            while i < len(segment) and segment[i] in {"-p", "--"}:
                i += 1
            continue
        if tok == "env":
            i += 1
            while i < len(segment):
                arg = segment[i]
                if arg in {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}:
                    i += 2
                elif (
                    arg in {"-i", "--ignore-environment", "-0", "--null", "--"}
                    or arg.startswith(("--unset=", "--chdir="))
                    or _ASSIGN_RE.match(arg)
                ):
                    i += 1
                else:
                    break
            continue
        if tok in {"nice", "timeout", "stdbuf", "sudo"}:
            wrapper = tok
            i += 1
            value_opts = {
                "nice": {"-n", "--adjustment"},
                "timeout": {"-s", "--signal", "-k", "--kill-after"},
                "sudo": {"-u", "-g", "-h", "-p", "-C", "-T"},
                "stdbuf": {"-i", "-o", "-e"},
            }[wrapper]
            while i < len(segment) and segment[i].startswith("-"):
                option = segment[i]
                i += 2 if option in value_opts else 1
            if wrapper == "timeout" and i < len(segment):
                i += 1  # duration
            continue
        break
    if i >= len(segment):
        return "", i
    return Path(segment[i]).name, i


def _inplace_edit_targets(segment: list[str], cmd_index: int) -> list[str]:
    """File operands of an in-place ``sed -i`` / ``perl -i`` invocation.

    Only fires when an in-place flag is present. The editor's *script* is
    excluded so it is never mistaken for a file path: with an explicit
    ``-e``/``-f`` script every positional is a file; otherwise the first
    positional is the script and the rest are files.
    """
    args = segment[cmd_index + 1 :]
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


_DESTINATION_WRITERS = frozenset({"cp", "mv", "install", "ln", "rsync"})
# GNU getopt operands: an option's value is never a source or destination.
# Keep the short options per command; a value can follow a cluster (-at DIR)
# or be attached to its final option (-atDIR). Long options accept =VALUE.
_VALUE_OPTIONS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "cp": (frozenset("St"), frozenset({"suffix", "target-directory"})),
    "mv": (frozenset("St"), frozenset({"suffix", "target-directory"})),
    "ln": (frozenset("St"), frozenset({"suffix", "target-directory"})),
    "install": (
        frozenset("gmoSt"),
        frozenset({"group", "mode", "owner", "suffix", "target-directory", "strip-program"}),
    ),
    "rsync": (
        frozenset("e"),
        frozenset(
            {
                "rsh",
                "exclude",
                "include",
                "filter",
                "files-from",
                "exclude-from",
                "include-from",
                "chmod",
                "backup-dir",
                "temp-dir",
                "partial-dir",
                "log-file",
                "write-batch",
                "only-write-batch",
                "out-format",
                "bwlimit",
                "port",
                "address",
                "iconv",
                "usermap",
                "groupmap",
                "sockopts",
                "rsync-path",
            }
        ),
    ),
    "rm": (frozenset(), frozenset()),
    "unlink": (frozenset(), frozenset()),
    "rmdir": (frozenset(), frozenset()),
    "shred": (frozenset("ns"), frozenset({"iterations", "size"})),
    "chmod": (frozenset(), frozenset({"reference"})),
    "chown": (frozenset(), frozenset({"reference", "from"})),
    "touch": (frozenset("drt"), frozenset({"date", "reference", "time"})),
    "git-archive": (frozenset("o"), frozenset({"output"})),
}

# Only these option values name additional write destinations. cp/mv --backup
# takes a control word, and --suffix takes a filename suffix; their output is
# still under the already-classified destination. rsync --compare-dest and
# --link-dest are read inputs, not write locations.
_PATH_WRITING_OPTIONS: dict[str, frozenset[str]] = {
    "rsync": frozenset({"backup-dir", "log-file", "write-batch", "only-write-batch", "partial-dir", "temp-dir"}),
    "git-archive": frozenset({"o", "output"}),
}

# Commands without a complete source/destination grammar are intentionally
# conservative. Adding a writer here covers future output options as well as
# current ones, without maintaining another table of flags.
_LONG_TAIL_WRITERS = frozenset(
    {
        "curl",
        "wget",
        "sort",
        "sqlite3",
        "tar",
        "unzip",
        "patch",
        "tee",
        "truncate",
        "split",
        "csplit",
        "ffmpeg",
        "convert",
    }
)


# Short options that consume a value. True means the value may name a write
# location; False means it is an input or a non-path control value. Positional
# inputs remain conservatively classified by the long-tail rule above.
_LONG_TAIL_SHORT_VALUES: dict[str, dict[str, bool]] = {
    "curl": {**dict.fromkeys("oDc", True), **dict.fromkeys("KT", False)},
    "wget": dict.fromkeys("OoaP", True),
    "sort": {**dict.fromkeys("oT", True), **dict.fromkeys("kt", False)},
    "tar": dict.fromkeys("fC", True),
    "unzip": {"d": True},
    "patch": {**dict.fromkeys("orBd", True), "i": False},
    "split": dict.fromkeys("aCbln", False),
}
_LONG_TAIL_LONG_VALUES: dict[str, dict[str, bool]] = {
    "curl": {
        "output": True,
        "output-dir": True,
        "dump-header": True,
        "cookie-jar": True,
        "config": False,
        "upload-file": False,
    },
    "wget": {"output-document": True, "output-file": True, "append-output": True, "directory-prefix": True},
    "sort": {"output": True, "temporary-directory": True, "key": False, "field-separator": False},
    "tar": {"file": True, "directory": True},
    "unzip": {"directory": True},
    "patch": {"output": True, "reject-file": True, "prefix": True, "directory": True, "input": False},
}


def _long_tail_targets(args: list[str], command: str) -> list[str]:
    """Path-like argv words, including values attached to options and dot commands."""
    targets: list[str] = []
    short_values = _LONG_TAIL_SHORT_VALUES.get(command, {})
    long_values = _LONG_TAIL_LONG_VALUES.get(command, {})
    i = 0
    options_done = False
    while i < len(args):
        arg = args[i]
        i += 1
        if arg == "--":
            options_done = True
            continue
        words: list[str] = []
        if not options_done and arg.startswith("--"):
            name, sep, attached = str(arg[2:]).partition("=")
            if sep:
                value = arg.tail(len(name) + 3) if isinstance(arg, ShellWord) else attached
                if long_values.get(name, True):
                    words.append(value)
            elif name in long_values and i < len(args):
                value = args[i]
                i += 1
                if long_values[name]:
                    words.append(value)
        elif not options_done and arg.startswith("-") and arg != "-":
            for offset, flag in enumerate(arg[1:], 1):
                if flag not in short_values:
                    continue
                if offset + 1 < len(arg):
                    value = arg.tail(offset + 1) if isinstance(arg, ShellWord) else arg[offset + 1 :]
                elif i < len(args):
                    value = args[i]
                    i += 1
                else:
                    break
                if short_values[flag]:
                    words.append(value)
                break
        elif command not in {"curl", "wget"}:
            words.append(arg)
        # Absolute embedded values and SQLite dot commands.
        for word in tuple(words):
            for match in re.finditer(r"(?:^|\s|=|-[A-Za-z]+)(/[^\s]+)", word):
                words.append(
                    ShellWord(match.group(1), getattr(word, "unresolved_at", None), getattr(word, "raw", word))
                )
            if any(char.isspace() for char in word):
                words.extend(ShellWord(part, getattr(word, "unresolved_at", None)) for part in str(word).split())
        targets.extend(word for word in words if word and not str(word).startswith("-") and "://" not in word)
    return list(dict.fromkeys(targets))


def _has_short_option(args: list[str], command: str, flag: str) -> bool:
    """Find a short flag before a value ends its option cluster."""
    value_options = _LONG_TAIL_SHORT_VALUES.get(command, {})
    for arg in args:
        if arg == "--":
            break
        if not arg.startswith("-") or arg.startswith("--"):
            continue
        for letter in arg[1:]:
            if letter == flag:
                return True
            if letter in value_options:
                break
    return False


_INPLACE_FIXERS = frozenset(
    {
        "ruff",
        "black",
        "isort",
        "prettier",
        "eslint",
        "clang-format",
        "gofmt",
        "rustfmt",
        "shfmt",
        "markdownlint",
        "markdownlint-cli2",
    }
)


def _inplace_fixer_targets(command: str, args: list[str]) -> list[str]:
    """Primary file operands of formatters and linters in write mode."""
    if command == "ruff":
        if not args or args[0] not in {"format", "check"}:
            return []
        writing = args[0] == "format" and "--check" not in args and "--diff" not in args
        writing |= args[0] == "check" and any(a in {"--fix", "--fix-only"} for a in args)
        args = args[1:]
    elif command in {"black", "isort"}:
        writing = not any(a in {"--check", "--check-only", "--diff"} for a in args)
    elif command == "rustfmt":
        writing = (
            "--check" not in args
            and "--emit=stdout" not in args
            and not any(args[i : i + 2] == ["--emit", "stdout"] for i in range(len(args) - 1))
        )
    else:
        write_flags = {
            "prettier": {"--write", "-w"},
            "eslint": {"--fix"},
            "clang-format": {"-i"},
            "gofmt": {"-w"},
            "shfmt": {"-w"},
            "markdownlint": {"--fix"},
            "markdownlint-cli2": {"--fix"},
        }
        writing = any(a in write_flags.get(command, ()) for a in args)
        if command in {"gofmt", "shfmt"}:
            writing |= any(a.startswith("-") and not a.startswith("--") and "w" in a[1:] for a in args)
    if not writing:
        return []
    # These options consume a non-target value; the rest of the positional
    # words are paths. The guard's containment layer decides which are primary.
    value_options = {
        "--config",
        "--ignore-path",
        "--stdin-filepath",
        "--extension",
        "--target-version",
        "--line-length",
        "--output-format",
        "--range",
        "--emit",
        "--edition",
        "--config-path",
        "-c",
        "-l",
        "-e",
    }
    targets: list[str] = []
    skip = False
    options_done = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg == "--":
            options_done = True
            continue
        if not options_done and arg in value_options:
            skip = True
            continue
        if not options_done and command == "shfmt" and arg in {"-i", "-ln"}:
            skip = True
            continue
        if not options_done and arg.startswith("-"):
            continue
        targets.append(arg)
    return targets


def _shell_command_script(args: list[str]) -> str | None:
    """Return the script after a shell -c cluster, stepping over option values."""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            return None
        if arg in {"-o", "-O", "+O", "--rcfile", "--init-file"}:
            i += 2
            continue
        if arg.startswith(("--rcfile=", "--init-file=")):
            i += 1
            continue
        if arg.startswith("--"):
            i += 1
            continue
        if arg.startswith("-") and not arg.startswith("--"):
            if "c" in arg[1:]:
                script_index = i + 1
                if script_index < len(args) and args[script_index] == "--":
                    script_index += 1
                return args[script_index] if script_index < len(args) else None
            i += 1
            continue
        if arg.startswith(("+O", "-O")):
            i += 1
            continue
        return None
    return None


def _operands(args: list[str], command: str) -> tuple[list[str], str | None, set[str], list[str]]:
    """Return getopt operands, target directory, seen options and written option paths."""
    short_values, long_values = _VALUE_OPTIONS[command]
    positionals: list[str] = []
    target_dir: str | None = None
    seen: set[str] = set()
    option_targets: list[str] = []
    options_done = False
    i = 0
    while i < len(args):
        arg = args[i]
        i += 1
        if options_done or arg == "-" or not arg.startswith("-"):
            positionals.append(arg)
            continue
        if arg == "--":
            options_done = True
            continue
        if arg.startswith("--"):
            name, sep, attached = str(arg[2:]).partition("=")
            seen.add(name)
            if name in long_values:
                if sep:
                    value = arg.tail(len(name) + 3) if isinstance(arg, ShellWord) else attached
                elif i < len(args):
                    value = args[i]
                    i += 1
                else:
                    continue
                if name == "target-directory":
                    target_dir = value
                if name in _PATH_WRITING_OPTIONS.get(command, ()):
                    option_targets.append(value)
            continue
        for offset, flag in enumerate(arg[1:], 1):
            seen.add(flag)
            if flag not in short_values:
                continue
            if offset + 1 < len(arg):
                value = arg.tail(offset + 1) if isinstance(arg, ShellWord) else arg[offset + 1 :]
            elif i < len(args):
                value = args[i]
                i += 1
            else:
                break
            if flag == "t" and command in _DESTINATION_WRITERS:
                target_dir = value
            if flag in _PATH_WRITING_OPTIONS.get(command, ()):
                option_targets.append(value)
            break
    return positionals, target_dir, seen, option_targets


def _destination_targets(segment: list[str], cmd_index: int, command: str) -> list[str]:
    """Destination and removed sources of a filesystem transfer."""
    args = segment[cmd_index + 1 :]
    positionals, target_dir, seen, option_targets = _operands(args, command)
    if command == "install" and ("d" in seen or "directory" in seen):
        return [*positionals, *option_targets]
    sources = positionals if target_dir is not None else positionals[:-1]
    removed_sources = command == "mv" or (command == "rsync" and "remove-source-files" in seen)
    targets = sources if removed_sources else []
    if target_dir is not None:
        return [*targets, target_dir, *option_targets]
    return [*targets, positionals[-1], *option_targets] if len(positionals) >= 2 else [*targets, *option_targets]


def _mutation_targets(segment: list[str], cmd_index: int, command: str) -> list[str]:
    positionals, _, seen, _ = _operands(segment[cmd_index + 1 :], command)
    if command in {"chmod", "chown"} and "reference" not in seen:
        positionals = positionals[1:]  # mode or owner, then paths
    return positionals


def _dd_targets(segment: list[str], cmd_index: int) -> list[str]:
    return [
        arg.tail(3) if isinstance(arg, ShellWord) else arg[3:]
        for arg in segment[cmd_index + 1 :]
        if arg.startswith("of=")
    ]


def _find_start_paths(args: list[str]) -> list[str]:
    """Parse find globals before start paths; files0 input hides start paths."""
    i = 0
    while i < len(args):
        if args[i] in {"-H", "-L", "-P"} or re.fullmatch(r"-O[0-9]+", args[i]):
            i += 1
        elif args[i] == "-D" and i + 1 < len(args):
            i += 2
        else:
            break
    if i < len(args) and args[i] == "--":
        i += 1
    starts: list[str] = []
    for arg in args[i:]:
        if arg == "-files0-from":
            break
        if arg.startswith("-") or arg in {"!", "(", ")"}:
            break
        starts.append(arg)
    return starts or ["."]


def _find_targets(args: list[str], *, cwd: str | None, main_root: Path | None, depth: int) -> list[str]:
    starts = _find_start_paths(args)
    targets: list[str] = []
    if "-delete" in args:
        targets.extend(starts)
    for i, tok in enumerate(args):
        if tok in {"-fprint", "-fprint0", "-fprintf", "-fls"} and i + 1 < len(args):
            targets.append(args[i + 1])
        # The input is read, but its contents can name any start path.
        if (
            tok == "-files0-from"
            and i + 1 < len(args)
            and main_root is not None
            and (
                cwd is None
                or _names_primary_literal(str(args[i + 1]), cwd, main_root)
                or _names_primary_literal(".", cwd, main_root)
            )
        ):
            unknown = ShellWord("find files0 start paths")
            unknown.decision_reason = "undecidable_find_start_paths"
            targets.append(unknown)
        if tok not in {"-exec", "-execdir", "-ok", "-okdir"}:
            continue
        template: list[str] = []
        for arg in args[i + 1 :]:
            if arg in {";", "+"}:
                break
            template.append(arg)
        exec_cwd = None if tok.endswith("dir") else cwd
        if "{}" in template:
            for start in starts:
                instantiated = [start if word == "{}" else word for word in template]
                nested = _writer_targets(
                    instantiated, cwd=exec_cwd, redirect_cwd=exec_cwd, main_root=main_root, depth=depth + 1
                )
                for target in nested:
                    if exec_cwd is None and not Path(target).is_absolute():
                        target = target if isinstance(target, ShellWord) else ShellWord(str(target))
                        target.decision_reason = "undecidable_find_execdir_target"
                    targets.append(target)
        else:
            nested = _writer_targets(
                template, cwd=exec_cwd, redirect_cwd=exec_cwd, main_root=main_root, depth=depth + 1
            )
            for target in nested:
                if exec_cwd is None and not Path(target).is_absolute():
                    target = target if isinstance(target, ShellWord) else ShellWord(str(target))
                    target.decision_reason = "undecidable_find_execdir_target"
                targets.append(target)
    return targets


def _writer_targets(
    segment: list[str], *, cwd: str | None, redirect_cwd: str | None, main_root: Path | None, depth: int
) -> list[str]:
    """Targets of the writer in one expanded segment, including exec wrappers."""
    targets = _redirect_targets(segment)
    for target in targets:
        if isinstance(target, ShellWord):
            target.base = redirect_cwd
            if redirect_cwd is None and not Path(target).is_absolute():
                target.decision_reason = "undecidable_write_target_after_cd"
    cmd, idx = _command_word(segment)
    if cmd in _LONG_TAIL_WRITERS:
        targets.extend(_long_tail_targets(segment[idx + 1 :], cmd))
        if cmd == "curl" and (_has_short_option(segment[idx + 1 :], cmd, "O") or "--remote-name" in segment[idx + 1 :]):
            targets.extend(
                ShellWord(Path(str(arg).split("?", 1)[0]).name) for arg in segment[idx + 1 :] if "://" in arg
            )
        if cmd == "wget" and not (
            _has_short_option(segment[idx + 1 :], cmd, "O")
            or _has_short_option(segment[idx + 1 :], cmd, "P")
            or any(
                arg in {"--output-document", "--directory-prefix"}
                or arg.startswith(("--output-document=", "--directory-prefix="))
                for arg in segment[idx + 1 :]
            )
        ):
            targets.extend(
                ShellWord(Path(str(arg).split("?", 1)[0]).name) for arg in segment[idx + 1 :] if "://" in arg
            )
    elif cmd in ("sed", "perl"):
        targets.extend(_inplace_edit_targets(segment, idx))
    elif cmd in _INPLACE_FIXERS:
        targets.extend(_inplace_fixer_targets(cmd, segment[idx + 1 :]))
    elif cmd in _DESTINATION_WRITERS:
        targets.extend(_destination_targets(segment, idx, cmd))
    elif cmd in {"rm", "unlink", "rmdir", "shred", "chmod", "chown", "touch"}:
        targets.extend(_mutation_targets(segment, idx, cmd))
    elif cmd == "dd":
        targets.extend(_dd_targets(segment, idx))
    elif _is_git_binary(cmd):
        c_path, rest = _git_global_prefix(segment[idx + 1 :])
        if rest and rest[0] == "archive":
            _, _, _, option_targets = _operands(rest[1:], "git-archive")
            git_base = _resolve(c_path, cwd, expand_user=False) if c_path and cwd else cwd
            for target in option_targets:
                word = target if isinstance(target, ShellWord) else ShellWord(str(target))
                if c_path and getattr(c_path, "unresolved_at", None) is not None and not Path(word).is_absolute():
                    word.decision_reason = "unresolved_shell_variable"
                word.base = str(git_base) if git_base is not None else None
                targets.append(word)
    elif cmd == "eval" and depth < 3:
        args = segment[idx + 1 :]
        if any(getattr(arg, "unresolved_at", None) is not None for arg in args):
            unknown = ShellWord("eval dynamic target")
            unknown.decision_reason = "undecidable_eval_primary_target"
            targets.append(unknown)
        else:
            targets.extend(bash_write_targets(" ".join(args), cwd=cwd, main_root=main_root, depth=depth + 1))
    elif cmd in {"sh", "bash", "zsh", "dash"} and depth < 3:
        script = _shell_command_script(segment[idx + 1 :])
        if script is not None:
            if getattr(script, "unresolved_at", None) is not None:
                unknown = ShellWord("dynamic shell script")
                unknown.decision_reason = "undecidable_shell_script_target"
                targets.append(unknown)
            else:
                targets.extend(bash_write_targets(str(script), cwd=cwd, main_root=main_root, depth=depth + 1))
    elif cmd == "find" and depth < 3:
        targets.extend(_find_targets(segment[idx + 1 :], cwd=cwd, main_root=main_root, depth=depth))
    return targets


def _xargs_template(segment: list[str]) -> list[str]:
    cmd, idx = _command_word(segment)
    if cmd not in {"xargs", "parallel"}:
        return []
    args = segment[idx + 1 :]
    i = 0
    value_opts = {
        "-n",
        "--max-args",
        "-L",
        "--max-lines",
        "-P",
        "--max-procs",
        "-j",
        "--jobs",
        "-I",
        "--replace",
        "-s",
        "--max-chars",
        "-d",
        "--delimiter",
    }
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in value_opts else 1
    template = args[i:]
    return template[: template.index(":::")] if ":::" in template else template


def _xargs_writer(template: list[str]) -> bool:
    writer, _ = _command_word(template)
    return writer in {
        "tee",
        "sed",
        "perl",
        "dd",
        "rm",
        "unlink",
        "rmdir",
        "truncate",
        "shred",
        "chmod",
        "chown",
        "touch",
        *_DESTINATION_WRITERS,
        *_LONG_TAIL_WRITERS,
        "find",
        "sh",
        "bash",
        "zsh",
        "dash",
        "eval",
        *_INPLACE_FIXERS,
    }


def _names_primary_literal(word: str, cwd: str, main_root: Path) -> bool:
    """Whether a path-looking pipeline word identifies the primary tree."""
    if "/" not in word and not word.startswith("."):
        return False
    path = _resolve(word, cwd, expand_user=False).resolve()
    try:
        relative = path.relative_to(main_root)
    except ValueError:
        return False
    return relative.parts[:2] != (".worktrees", "dispatch")


def _env_command_cwd(segment: list[str], cwd: str | None) -> str | None:
    """Apply ``env -C`` / ``--chdir`` before resolving a wrapped writer."""
    _, command_index = _command_word(segment)
    i = 0
    while i < command_index:
        if segment[i] != "env":
            i += 1
            continue
        i += 1
        while i < command_index:
            arg = segment[i]
            if arg in {"-C", "--chdir"} and i + 1 < len(segment):
                path = segment[i + 1]
                i += 2
            elif arg.startswith("--chdir="):
                path = arg.tail(len("--chdir=")) if isinstance(arg, ShellWord) else arg.split("=", 1)[1]
                i += 1
            else:
                path = None
            if path is not None:
                if getattr(path, "unresolved_at", None) is not None or re.search(r"[*?\[\]{}]", path):
                    cwd = None
                elif Path(path).is_absolute():
                    cwd = str(Path(path).resolve())
                elif cwd is not None:
                    cwd = str(_resolve(path, cwd, expand_user=False).resolve())
                continue
            if arg in {"-u", "--unset", "-S", "--split-string"}:
                i += 2
            elif (
                arg in {"-i", "--ignore-environment", "-0", "--null", "--"}
                or arg.startswith("--unset=")
                or _ASSIGN_RE.match(arg)
            ):
                i += 1
            else:
                break
    return cwd


def _cdpath_binding(segment: list[str]) -> bool | None:
    """Return an explicit CDPATH binding, or None when untouched."""
    cmd, idx = _command_word(segment)
    if cmd == "unset" and "CDPATH" in segment[idx + 1 :]:
        return True
    for word in segment:
        if word.startswith("CDPATH="):
            return word == "CDPATH="
    return None


def _segments_with_cwd(command: str, cwd: str | None):
    """Yield expanded segments with the cwd they execute from."""
    scope_cwds: dict[tuple[int, ...], str | None] = {(): cwd}
    scope_dirs: dict[tuple[int, ...], list[str | None]] = {(): []}
    scope_cdpath_empty: dict[tuple[int, ...], bool] = {(): False}
    for segment in _expanded_segments(command):
        scope = segment.scope
        if scope not in scope_cwds:
            scope_cwds[scope] = scope_cwds.get(scope[:-1], cwd)
            scope_dirs[scope] = list(scope_dirs.get(scope[:-1], []))
            scope_cdpath_empty[scope] = scope_cdpath_empty.get(scope[:-1], False)
        effective_cwd = scope_cwds[scope]
        cmd, idx = _command_word(segment)
        isolated = segment.prev_op in {"|", "|&"} or segment.next_op in {"|", "|&", "&"}
        cdpath_binding = _cdpath_binding(segment)
        cdpath_empty_here = cdpath_binding if cdpath_binding is not None else scope_cdpath_empty[scope]
        stack_only = cmd in {"pushd", "popd"} and "-n" in segment[idx + 1 :]
        if cmd in {"cd", "pushd"} and not isolated:
            args = [word for word in segment[idx + 1 :] if not word.startswith("-")]
            path = args[0] if args else None
            if cmd == "pushd":
                scope_dirs[scope].append(path if stack_only else effective_cwd)
            if stack_only:
                pass  # pushd -n changes the stack, never the process cwd.
            elif (
                path is None
                or path.unresolved_at is not None
                or re.search(r"[*?\[\]{}]", path)
                or (not Path(path).is_absolute() and effective_cwd is None)
                or (not Path(path).is_absolute() and not str(path).startswith(("./", "../")) and not cdpath_empty_here)
            ):
                scope_cwds[scope] = None
            else:
                scope_cwds[scope] = str(_resolve(path, effective_cwd or "/", expand_user=False).resolve())
        elif cmd == "popd" and not isolated:
            popped = scope_dirs[scope].pop() if scope_dirs[scope] else None
            if not stack_only:
                scope_cwds[scope] = popped
        # Prefix assignments (``CDPATH= cmd``) affect only that command.
        # Conditional assignment may not run, so it can only invalidate a
        # known-empty binding; it cannot establish one for later commands.
        persists = cmd == "" or cmd in _BINDING_DECLARATIONS or cmd == "unset"
        if cdpath_binding is not None and persists and not isolated:
            if segment.prev_op in _STATEMENT_START:
                scope_cdpath_empty[scope] = cdpath_binding
            elif not cdpath_binding:
                scope_cdpath_empty[scope] = False
        yield segment, _env_command_cwd(segment, effective_cwd), effective_cwd


def bash_write_targets(
    command: str, *, cwd: str | None = None, main_root: Path | None = None, depth: int = 0
) -> list[str]:
    """Best-effort list of files a Bash command would create/modify.

    Covers redirection and the writer commands listed above. Other write
    vectors are intentionally out of scope (see module docstring); they rely on
    physical worktree isolation and the monitor/git-shim layers.
    """
    targets: list[str] = []
    pipeline: list[str] = []
    for segment, effective_cwd, shell_cwd in _segments_with_cwd(command, cwd):
        if segment.prev_op not in {"|", "|&"}:
            pipeline = []
        pipeline.extend(segment)
        segment_targets = _writer_targets(
            segment, cwd=effective_cwd, redirect_cwd=shell_cwd, main_root=main_root, depth=depth
        )
        template = _xargs_template(segment)
        if (
            _xargs_writer(template)
            and main_root is not None
            and (
                _names_primary_literal(".", effective_cwd or "/", main_root)
                or any(
                    not word.startswith("-")
                    and _names_primary_literal(str(word), effective_cwd or cwd or "/", main_root)
                    for word in pipeline
                )
            )
        ):
            unknown = ShellWord("xargs stdin write target")
            unknown.decision_reason = "undecidable_xargs_stdin_target"
            segment_targets.append(unknown)
        if template and depth < 3:
            segment_targets.extend(
                _writer_targets(
                    template, cwd=effective_cwd, redirect_cwd=effective_cwd, main_root=main_root, depth=depth + 1
                )
            )
        for target in segment_targets:
            word = target if isinstance(target, ShellWord) else ShellWord(str(target))
            if (
                not Path(word).is_absolute()
                and effective_cwd is None
                and word.decision_reason is None
                and word.base is None
            ):
                word.decision_reason = "undecidable_write_target_after_cd"
            if word.base is None and word.decision_reason is None:
                word.base = effective_cwd
            targets.append(word)
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
        if (
            tok
            in {
                "-c",
                "--config-env",
                "--exec-path",
                "--git-dir",
                "--work-tree",
                "--namespace",
                "--super-prefix",
                "--list-cmds",
            }
            and i + 1 < n
        ):
            i += 2
            continue
        if tok.startswith("-c") and len(tok) > 2 and "=" in tok:
            i += 1
            continue
        if tok.startswith("--") and "=" in tok:
            i += 1
            continue
        if tok in {
            "--bare",
            "--no-replace-objects",
            "--literal-pathspecs",
            "--glob-pathspecs",
            "--noglob-pathspecs",
            "--icase-pathspecs",
            "--no-optional-locks",
            "-p",
            "--paginate",
            "-P",
            "--no-pager",
        }:
            i += 1
            continue
        # Subcommand or unknown option starts the remainder.
        break
    return c_path, args[i:]


def _is_git_binary(cmd: str) -> bool:
    return cmd in {"git", "git.exe"} or cmd.endswith("/git")


def bash_git_write_intents(command: str, *, cwd: str | None = None, depth: int = 0) -> list[dict[str, object]]:
    """Parse Bash for git-mediated working-tree mutations (issue #5396).

    Each intent is a dict::

        {
          "kind": "apply"|"add"|"stash_apply"|"path_checkout"|"restore_source",
          "c_path": str|None,          # from git -C
          "segment_cwd": str|None,     # after literal cd/pushd
          "paths": list[str],          # pathspecs when known (may be empty)
          "summary": str,              # human-readable for the block message
          "allowlisted": bool,         # True → never block (rescue clean)
        }

    Allowlisted: ``git checkout -- <paths>`` and ``git restore <paths>`` without
    ``--source`` (discard dirt / restore from index — rescue pattern).
    """
    intents: list[dict[str, object]] = []

    def record(intent: dict[str, object]) -> None:
        intent["segment_cwd"] = effective_cwd
        intents.append(intent)

    for segment, effective_cwd, _shell_cwd in _segments_with_cwd(command, cwd):
        cmd, idx = _command_word(segment)
        if cmd == "eval" and depth < 3:
            args = segment[idx + 1 :]
            if all(getattr(arg, "unresolved_at", None) is None for arg in args):
                intents.extend(bash_git_write_intents(" ".join(args), cwd=effective_cwd, depth=depth + 1))
            continue
        if cmd in {"sh", "bash", "zsh", "dash"} and depth < 3:
            script = _shell_command_script(segment[idx + 1 :])
            if script is not None and getattr(script, "unresolved_at", None) is None:
                intents.extend(bash_git_write_intents(str(script), cwd=effective_cwd, depth=depth + 1))
            continue
        if not _is_git_binary(cmd):
            continue
        c_path, rest = _git_global_prefix(segment[idx + 1 :])
        if not rest:
            continue
        sub = rest[0]
        sub_args = rest[1:]
        option_args = sub_args[: sub_args.index("--")] if "--" in sub_args else sub_args

        if sub in {"apply", "am"}:
            record(
                {
                    "kind": "apply" if sub == "apply" else "am",
                    "c_path": c_path,
                    "paths": [],
                    "summary": f"git {sub}",
                    "allowlisted": False,
                }
            )
            continue

        if sub in {"merge", "pull", "rebase", "cherry-pick", "revert"}:
            record({"kind": sub, "c_path": c_path, "paths": [], "summary": f"git {sub}", "allowlisted": False})
            continue

        # This hook owns git mutations targeted at the protected worktree via
        # effective cwd or -C. The branch-switch hook retains its separate
        # direct-command policy for all primary checkouts.
        if sub == "switch":
            record({"kind": "switch", "c_path": c_path, "paths": [], "summary": "git switch", "allowlisted": False})
            continue

        if sub == "worktree" and sub_args[:1] == ["remove"]:
            paths = [arg for arg in sub_args[1:] if not arg.startswith("-")]
            record(
                {
                    "kind": "worktree_remove",
                    "c_path": c_path,
                    "paths": paths,
                    "summary": "git worktree remove",
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
            record(
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
                record(
                    {
                        "kind": "stash_apply",
                        "c_path": c_path,
                        "paths": [],
                        "summary": f"git stash {action}",
                        "allowlisted": False,
                    }
                )
            continue

        if sub == "clean":
            dry_run = False
            i = 0
            while i < len(option_args):
                tok = option_args[i]
                if tok in {"-e", "--exclude"}:
                    i += 2  # the following exclude pattern may itself be "-n"
                    continue
                if tok == "--dry-run" or (tok.startswith("-") and not tok.startswith("--") and "n" in tok[1:]):
                    dry_run = True
                i += 1
            if not dry_run:
                record({"kind": "clean", "c_path": c_path, "paths": [], "summary": "git clean", "allowlisted": False})
            continue

        if sub == "reset" and any(tok in {"--hard", "--merge", "--keep"} for tok in option_args):
            record({"kind": "reset", "c_path": c_path, "paths": [], "summary": "git reset", "allowlisted": False})
            continue

        if sub == "read-tree" and any(
            tok == "--update" or (tok.startswith("-") and not tok.startswith("--") and "u" in tok[1:])
            for tok in option_args
        ):
            record(
                {"kind": "read-tree", "c_path": c_path, "paths": [], "summary": "git read-tree", "allowlisted": False}
            )
            continue

        if sub == "checkout":
            # Allowlist: `git checkout -- <paths>` (restore from index/HEAD).
            # Block: `git checkout <tree-ish> -- <paths>` and the no-dashdash
            # form `git checkout <tree-ish> <path>…` (#5517).
            # Branch-only checkouts are primary worktree mutations too; the
            # rescue targets below remain available.
            if any(
                tok == "--force" or (tok.startswith("-") and not tok.startswith("--") and "f" in tok[1:])
                for tok in option_args
            ):
                record(
                    {
                        "kind": "forced_checkout",
                        "c_path": c_path,
                        "paths": [],
                        "summary": "git checkout -f",
                        "allowlisted": False,
                    }
                )
                continue
            if "--" in sub_args:
                dd = sub_args.index("--")
                before = sub_args[:dd]
                after = sub_args[dd + 1 :]
                treeish = [t for t in before if not t.startswith("-")]
                if not treeish and not before:
                    record(
                        {
                            "kind": "path_checkout",
                            "c_path": c_path,
                            "paths": after,
                            "summary": "git checkout -- " + " ".join(after),
                            "allowlisted": True,
                        }
                    )
                else:
                    record(
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
                    record(
                        {
                            "kind": "path_checkout",
                            "c_path": c_path,
                            "paths": positionals[1:],
                            "summary": (f"git checkout {positionals[0]} " + " ".join(positionals[1:])),
                            "allowlisted": False,
                        }
                    )
                elif len(positionals) == 1 and positionals[0] not in {"main", "master", "HEAD", "-"}:
                    record(
                        {
                            "kind": "branch_checkout",
                            "c_path": c_path,
                            "paths": [],
                            "summary": "git checkout " + str(positionals[0]),
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
            if source is None and paths and all(not tok.startswith("-") for tok in sub_args):
                record(
                    {
                        "kind": "restore_source",
                        "c_path": c_path,
                        "paths": paths,
                        "summary": "git restore " + " ".join(paths),
                        "allowlisted": True,
                    }
                )
            else:
                record(
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
            record(
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


def _effective_git_cwd(intent: dict[str, object], payload_cwd: str) -> Path | None:
    """Resolve a git intent's worktree, or return unknown after navigation."""
    segment_cwd = intent.get("segment_cwd", payload_cwd)
    c_path = intent.get("c_path")
    if isinstance(c_path, str) and c_path:
        if Path(c_path).is_absolute():
            return Path(c_path).resolve()
        if not isinstance(segment_cwd, str):
            return None
        return _resolve(c_path, segment_cwd, expand_user=False).resolve()
    return Path(segment_cwd).resolve() if isinstance(segment_cwd, str) else None


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


class _UndecidableWrite:
    allowed = False

    def __init__(self, reason: str, message: str) -> None:
        self.reason = reason
        self.message = message


def _resolve(path_str: str, cwd: str, *, expand_user: bool = True) -> Path:
    """Resolve a possibly-relative target against the payload cwd.

    Bash words arrive already tilde-expanded (``_expand_word``), so they pass
    ``expand_user=False``: a ``~`` still present there was quoted and is literal.
    """
    path = Path(path_str).expanduser() if expand_user else Path(path_str)
    if not path.is_absolute():
        path = Path(cwd) / path
    return path


def _bash_path_decision(word: str, base: str, wc, main_root: Path | None = None) -> object:
    """Containment decision for one expanded Bash path word.

    A word holding any unknown expansion is blocked outright: the unknown value
    may be absolute, empty or contain ``..``, so no literal prefix proves the
    path stays out of the primary checkout.
    """
    if getattr(word, "unresolved_at", None) is not None:
        return _UnresolvedWrite()
    reason = getattr(word, "decision_reason", None)
    if reason is not None:
        return _UndecidableWrite(reason, "Use a literal target and a known working directory.")
    if main_root is not None and re.search(r"[*?\[\]{}]", word):
        parts = Path(word).parts
        first = next(i for i, part in enumerate(parts) if re.search(r"[*?\[\]{}]", part))
        prefix = Path(*parts[:first]) if first else Path(".")
        prefix = _resolve(str(prefix), getattr(word, "base", None) or base, expand_user=False).resolve()
        may_reach_primary = prefix == main_root or prefix in main_root.parents
        if main_root in prefix.parents:
            may_reach_primary = not wc.evaluate_write(prefix / "__guard_glob_probe__", cwd=base).allowed
        if may_reach_primary:
            return _UndecidableWrite(
                "undecidable_glob_write_target",
                "A glob or brace target may resolve inside the primary checkout. Use a literal path.",
            )
    base = getattr(word, "base", None) or base
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
        raw_targets = []
    else:
        raw_targets = write_tool_targets(tool_input)

    # Git commands mutate outside shell redirections/write-tool payloads, so
    # retain their parsed intents for the primary-checkout containment pass.
    git_intents: list[dict[str, object]] = []
    if tool_name == "Bash" and command:
        try:
            git_intents = bash_git_write_intents(command, cwd=cwd)
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

    if tool_name == "Bash":
        raw_targets = bash_write_targets(command, cwd=cwd, main_root=main_root)

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
                    return _block_git_mediated(summary, main_root, reason="unresolved_shell_variable")
                git_cwd = _effective_git_cwd(intent, cwd)
                if git_cwd is None:
                    return _block_git_mediated(summary, main_root, reason="undecidable_git_cwd_after_cd")
                if intent.get("kind") == "worktree_remove":
                    for raw in intent.get("paths") or []:
                        decision = _bash_path_decision(raw, str(git_cwd), wc, main_root)
                        if not decision.allowed:
                            return _block_git_mediated(summary, main_root, reason=decision.reason)
                    continue
                # Only care when the effective git worktree *is* the primary.
                try:
                    if not wc.is_primary_checkout(git_cwd):
                        continue
                except Exception:
                    continue
                paths = list(intent.get("paths") or [])
                if not paths:
                    # Whole-tree mutator (apply / am / stash pop|apply / bare add).
                    return _block_git_mediated(summary, main_root, reason="git_mediated_primary_worktree")
                # Path-scoped mutators: block if any path is a protected primary write.
                for raw in paths:
                    decision = _bash_path_decision(raw, str(git_cwd), wc)
                    if not decision.allowed:
                        return _block_git_mediated(summary, main_root, reason=decision.reason)
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
                decision = _bash_path_decision(raw, cwd, wc, main_root)
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
