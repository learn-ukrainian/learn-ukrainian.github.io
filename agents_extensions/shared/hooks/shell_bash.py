"""Closed-grammar Bash reader for guarded Git and GitHub operations (#9484, #9480, #10521).

Threat model (frozen by the #10521 ruling): a well-meaning or confused agent
emits one Bash command line; the hook payload supplies that line and its cwd.
These hooks are a discipline gate, not a sandbox. Encoded payloads, scripts on
disk, harness or profile state, concurrent processes and API merges are
recorded residuals, not reader inputs.

The reader never executes shell code and never models control flow. It works
in a fixed order, and every refusal names a typed reason class:

1. parse, repairing only known grammar-0.25 misparses; any parse error refuses;
2. refuse shell-binding changes unconditionally (aliases, hashing, builtin and
   shell-option switches, computed variable names);
3. account for every simple command anywhere in the unpruned tree: function
   and loop bodies, substitutions and literal shell, eval and trap payloads;
4. detect every guarded operation in that same tree;
5. admit only the written grammar (docs/design/guard-hooks-understood-forms.md);
6. only then establish context: the payload cwd, or one leading `cd <literal> &&`.

No filesystem probe or network lookup happens before step 6.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.metadata import version
from itertools import pairwise
from pathlib import Path

import tree_sitter_bash
from tree_sitter import Language, Parser

PINS = {"tree-sitter": "0.26.0", "tree-sitter-bash": "0.25.1"}
for _package, _pin in PINS.items():
    if version(_package) != _pin:
        raise ImportError(f"{_package} must be {_pin}")

REPAIR = (
    "uv pip install --python <canonical-checkout>/.venv/bin/python "
    "--require-hashes --only-binary=:all: -r requirements-hooks.txt"
)
UNREADABLE = "--__guard_unreadable__"
MAX_DEPTH = 8
MAX_WORK = 20000
_LANGUAGE = Language(tree_sitter_bash.language())
_WRAPPERS = {
    "env",
    "command",
    "builtin",
    "exec",
    "time",
    "nice",
    "nohup",
    "timeout",
    "stdbuf",
    "sudo",
    "coproc",
}
_VALUE_OPTIONS = {
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string", "-a", "--argv0"},
    "sudo": {
        "-u",
        "--user",
        "-g",
        "--group",
        "-r",
        "--role",
        "-t",
        "--type",
        "-C",
        "--close-from",
        "-c",
        "--command-timeout",
        "-T",
        "-p",
        "--prompt",
        "-D",
        "--chdir",
        "-h",
        "--host",
        "-R",
        "--chroot",
    },
    "time": {"-f", "--format", "-o", "--output"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-k", "--kill-after", "-s", "--signal"},
    "stdbuf": {"-i", "--input", "-o", "--output", "-e", "--error"},
    "exec": {"-a"},
}
# Grammar 0.25 can silently flatten named coproc compound statements into
# simple commands. Refuse their bare reserved words instead of losing argv.
_RESERVED_WORDS = frozenset(
    word.encode()
    for word in [
        "then",
        "do",
        "done",
        "fi",
        "elif",
        "else",
        "esac",
        "while",
        "until",
        "if",
        "for",
        "select",
        "case",
        "[[",
        "((",
        "{",
        "}",
    ]
)
_SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "fish"}
_INDIRECT_EXECUTORS = {
    "strace",
    "script",
    "numactl",
    "systemd-run",
    "uv",
    "nsenter",
    "unshare",
    "find",
    "setsid",
    "flock",
    "ionice",
    "chrt",
    "taskset",
    "prlimit",
    "chroot",
    "runuser",
    "su",
    "watch",
    "parallel",
    "ssh",
    "at",
    "batch",
    "python",
    "python3",
    "perl",
    "ruby",
    "node",
    "awk",
}
_DIRECTORY_BUILTINS = {"cd", "pushd", "popd"}
# Ruling item 5: these change what later words run, so they refuse whether or
# not a guarded operation is visible.
_BINDING_BUILTINS = {"alias", "unalias", "hash", "enable", "shopt"}
_BINDING_VARIABLES = {"POSIXLY_CORRECT", "SHELLOPTS", "BASHOPTS"}
_NAME_WRITERS = {"read", "readarray", "mapfile", "getopts", "printf", "let"}


class ShellParseError(ValueError):
    """A guarded command cannot be read completely, or is outside the grammar."""

    def __init__(self, message: str, *, reason_class: str | None = "PARSE_INCOMPLETE") -> None:
        super().__init__(message)
        self.reason_class = reason_class


def emit_refusal(reason_class: str) -> None:
    """Emit the existing privacy-safe stderr judgment contract."""
    sys.stderr.write("GUARD_JUDGMENT " + json.dumps({"disposition": "refuse", "reason_class": reason_class}) + "\n")


DEFINITION_REPAIR = (
    "keep shell definitions out of a guarded git/gh command (a semicolon or newline inside one "
    "command does not separate them), and use `git -C <worktree> ...` (for gh, `-R <owner>/<repo>`)"
)
SEPARATE_CALLS_REPAIR = (
    "run definitions and guarded git/gh operations in separate Bash tool calls (a semicolon or newline "
    "inside one call does not separate them), and in the guarded call use `git -C <worktree> ...` "
    "(for gh, `-R <owner>/<repo>`)"
)


class ShellDefinitionError(ShellParseError):
    """A shell definition or binding change shares one command with a guarded operation (#10521)."""

    def __init__(
        self,
        message: str = "a shell function, alias or builtin override can change what any command or `cd` runs",
        *,
        reason_class: str = "ALIAS_EXECUTION",
    ) -> None:
        super().__init__(message, reason_class=reason_class)


# Ruling item 6. Recorded per harness by scripts/hooks/harness_shell_state.py;
# "proven" means functions, aliases and exports from one tool call never reach
# the next call. Only there may a refusal suggest separate calls as the repair.
SHELL_STATE_ISOLATION = {"claude-code": "proven", "codex": "unproven", "grok": "unproven", "unknown": "unproven"}


def harness_name(payload: object) -> str:
    """Name the harness that sent a hook payload; diagnostic wording only."""
    if isinstance(payload, dict) and "toolName" in payload:
        return "grok"
    if os.environ.get("CLAUDECODE") == "1" and isinstance(payload, dict) and "transcript_path" in payload:
        return "claude-code"
    if os.environ.get("CODEX_HOOK_POLICY") == "1":
        return "codex"
    return "unknown"


def definition_repair(payload: object) -> str:
    """The definition repair, naming separate calls only where isolation is proven."""
    return SEPARATE_CALLS_REPAIR if SHELL_STATE_ISOLATION[harness_name(payload)] == "proven" else DEFINITION_REPAIR


@dataclass(frozen=True)
class Invocation:
    """A top-level simple command. Only ``guarded`` rows carry an established cwd."""

    argv: list[str]
    cwd: str | None
    guarded: bool = False
    repository_unknown: bool = False
    redirect_unknown: bool = False
    environment_repo: str | None = None
    context_reason: str | None = None
    via_xargs: bool = False

    @property
    def cwd_unreadable(self) -> bool:
        return self.cwd is None or self.repository_unknown


def literal(node) -> str | None:
    """Decode a single AST word; expansions are deliberately not evaluated."""
    raw = node.text.decode()
    if node.type == "command_name":
        return literal(node.named_children[0])
    if node.type in {
        "command_substitution",
        "process_substitution",
        "expansion",
        "simple_expansion",
        "arithmetic_expansion",
    }:
        return None
    if node.type == "concatenation":
        # Quoted pieces never brace-expand, but they can sit between unquoted braces.
        unquoted = "".join(c.text.decode() if c.type in {"word", "number"} else "q" for c in node.named_children)
        parts = [literal(child) for child in node.named_children]
        return None if None in parts or _brace_expansion(unquoted) else "".join(parts)
    if node.type == "ansi_c_string":
        return ansi_c_value(raw[2:-1])
    # `$"..."` is looked up in the locale's message catalog; its word is not provable.
    # Grammar 0.25 reads it as an anonymous `$` before a plain string.
    dollar = node.prev_sibling
    if node.type == "translated_string" or (
        node.type == "string" and dollar is not None and dollar.type == "$" and dollar.end_byte == node.start_byte
    ):
        return None
    if node.type == "string":
        if any(child.type not in {"string_content"} for child in node.named_children):
            return None
        raw = raw[1:-1]
        return re.sub(r'\\([$`"\\\n])', lambda m: "" if m[1] == "\n" else m[1], raw)
    if node.type == "raw_string":
        return raw[1:-1]
    if node.named_children or re.search(r"(?<!\\)[$`*?\[]", raw) or _brace_expansion(raw):
        return None
    try:
        return shlex.split(raw.replace("\\\n", ""), comments=False)[0] if raw else ""
    except (ValueError, IndexError):
        return None


def _brace_expansion(unquoted: str) -> bool:
    """Whether unquoted text may brace-expand: an unescaped `{` ... `}` around `,` or `..`.

    Bash turns `gh pr {merge,} 5` into `gh pr merge 5`; a superset refuses.
    """
    opened = []
    index = 0
    while index < len(unquoted):
        char = unquoted[index]
        if char == "\\":
            index += 2
            continue
        if char == "{":
            opened.append(index)
        elif char == "}" and opened:
            inner = unquoted[opened.pop() + 1 : index]
            if "," in inner or ".." in inner:
                return True
        index += 1
    return False


_ANSI_C_BYTES = {ord(k): v for k, v in zip("abeEfnrtv\\'\"?", b"\a\b\x1b\x1b\f\n\r\t\v\\'\"?", strict=True)}


def ansi_c_value(content: str) -> str | None:
    """The word Bash 5.3 makes of ``$'content'``, or None where it is not provable.

    Escapes yield bytes: an octal escape takes one to three digits and wraps to
    8 bits, ``\\xHH`` takes one or two hex digits, ``\\cX`` is a control byte
    (``\\c?`` is DEL), and the first NUL ends the quoted text. An unknown escape
    keeps its backslash. None refuses forms whose value depends on the locale or
    the Bash version (``\\u``/``\\U`` above U+007F, ksh-style ``\\x{...}``, and
    ``\\c`` before a backslash, a non-ASCII byte, ``i`` or the end) and values
    that are not UTF-8.
    """
    source = content.encode()
    value = bytearray()
    index = 0
    while index < len(source):
        byte = source[index]
        index += 1
        if byte != 0x5C or index == len(source):
            value.append(byte)
            continue
        escape = source[index]
        index += 1
        if escape in _ANSI_C_BYTES:
            decoded = _ANSI_C_BYTES[escape]
        elif 0x30 <= escape <= 0x37:
            digits = re.match(rb"[0-7]{0,2}", source[index:])[0]
            index += len(digits)
            decoded = int(bytes([escape]) + digits, 8) & 0xFF
        elif escape in b"xuU":
            if escape == ord("x") and source[index : index + 1] == b"{":
                return None
            width = {ord("x"): 2, ord("u"): 4, ord("U"): 8}[escape]
            digits = re.match(rb"[0-9A-Fa-f]{0,%d}" % width, source[index:])[0]
            if not digits:
                value += b"\\" + bytes([escape])
                continue
            index += len(digits)
            decoded = int(digits, 16)
            if escape != ord("x") and decoded > 0x7F:
                return None
        elif escape == ord("c"):
            if index == len(source) or source[index] in b"\\i" or source[index] > 0x7F:
                return None
            decoded = 0x7F if source[index] == ord("?") else source[index] & 0x1F
            index += 1
        else:
            value += b"\\" + bytes([escape])
            continue
        if decoded == 0:
            break
        value.append(decoded)
    try:
        return value.decode()
    except UnicodeDecodeError:
        return None


def wrapper_scopes(argv: list[str]) -> tuple[int, list[tuple[str, list[str]]]]:
    """Keep each transparent utility's options in its own semantic scope."""
    i = 0
    scopes = []
    while i < len(argv):
        name = Path(argv[i]).name
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", argv[i]) or argv[i] in {"!", "{"}:
            i += 1
            continue
        if name not in _WRAPPERS:
            break
        i += 1
        begin = i
        while i < len(argv) and argv[i].startswith("-") and argv[i] != "-":
            option = argv[i]
            i += 1
            if option == "--":
                break
            if option in _VALUE_OPTIONS.get(name, set()):
                i += 1
        if name == "timeout":
            i += 1
        scopes.append((name, argv[begin:i]))
    return min(i, len(argv)), scopes


def utility_name(word: str) -> str:
    """A command word's utility name; `Path(".").name` would drop the `.` builtin."""
    return "." if word == "." else Path(word).name


def invoked_start(argv: list[str]) -> tuple[int, bool]:
    """Locate a utility through explicit wrapper options; xargs is never a prefix."""
    return wrapper_scopes(argv)[0], False


# Bash's alias and hashed-command tables, in any assignment, reference or name operand.
_BINDING_TABLE = re.compile(r"(?:BASH_ALIASES|BASH_CMDS)(?:\[.*\])?(?:\+?=.*)?", re.DOTALL)
_COMMAND_WORDS = {"command_name", "word", "number", "string", "raw_string", "ansi_c_string", "translated_string"}
_COMMAND_WORDS |= {"concatenation", "simple_expansion", "expansion", "command_substitution", "process_substitution"}


def ansi_c_reading(command: str) -> str | None:
    """Decode escapes only inside parsed ``$'...'`` spans, as Bash does.

    Text outside those spans stays raw, so a raw-text gate reads its
    backslashes as plain quoting. A word mixing both spellings, such as
    ``$'\\163cripts'.p\\ublish``, then reads as Bash runs it. None means the
    spans cannot be read; callers fail closed.
    """
    source = command.replace("\\\n", "").encode()
    tree = Parser(_LANGUAGE).parse(source)
    if tree.root_node.has_error:
        return None
    spans, pending = [], [tree.root_node]
    while pending:
        node = pending.pop()
        if node.type == "ansi_c_string":
            spans.append(node)
        else:
            pending.extend(node.named_children)
    pieces, cursor = [], 0
    for node in sorted(spans, key=lambda span: span.start_byte):
        decoded = ansi_c_value(node.text.decode()[2:-1])
        if decoded is None:
            return None
        pieces.extend([source[cursor : node.start_byte].decode(), decoded])
        cursor = node.end_byte
    return "".join(pieces) + source[cursor:].decode()


def operation_candidate(text: str) -> bool:
    """Conservative visible-operation gate for execution payload refusals.

    Bash decodes numeric escapes only inside ``$'...'``; elsewhere ``\\u`` is
    just ``u``. Engage on the raw, the fully decoded, or the parsed span
    reading, so no mix of spellings hides an operation.
    """

    def visible(probe: str) -> bool:
        probe = probe.replace("\\\n", "").replace("\\", "").replace("'", "").replace('"', "")
        return any(name in probe for name in ("git", "gh", "scripts.publish")) and bool(
            re.search(r"\b(?:checkout|switch|branch|merge|symbolic-ref|bisect|rebase)\b", probe)
        )

    if visible(text):
        return True
    decoded = numeric_reading(text)
    if decoded is None or visible(decoded):
        return True
    if "$'" not in text:
        return False
    reading = ansi_c_reading(text)
    return reading is None or visible(reading)


_NUMERIC_ESCAPE = re.compile(r"\\(x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{1,4}|U[0-9a-fA-F]{1,8}|[0-7]{1,3})")


def numeric_reading(text: str) -> str | None:
    """Every numeric escape in text decoded, an octal one wrapped to a byte as Bash does.

    A conservative extra reading for the engagement gates; None (engage) when
    a code point is out of range.
    """
    try:
        return _NUMERIC_ESCAPE.sub(lambda m: chr(int(m[1][1:], 16) if m[1][0] in "xuU" else int(m[1], 8) & 0xFF), text)
    except (ValueError, OverflowError):
        return None


# A blockable operation spelled in text that cannot be parsed as shell (an
# interpreter's code, a remote command, a tool payload). Separators include the
# quotes, commas and brackets of list literals; a command separator ends a shape.
_OPERATION_SHAPE = re.compile(
    r"\bgit\b[^\n;|&]{0,80}?\b(?:checkout|switch|branch|symbolic-ref|bisect|rebase)\b"
    r"|\bgh\b[^\n;|&]{0,60}?\bpr\b[^\n;|&]{0,40}?\b(?:merge|checkout)\b"
    r"|\bscripts\.publish\b[^\n;|&]{0,40}?\bpr-merge\b"
)


def operation_shape(text: str) -> bool:
    """Whether text spells a guarded operation, under any Bash spelling of its words.

    Ruling item 7 (#10521): a mere mention of git, gh or a verb is data; an
    executor payload that spells an operation is a guarded operation the reader
    cannot place, so its consumer refuses. Readings are the raw text, the fully
    decoded text and the parsed ``$'...'`` span reading, as in operation_candidate.
    """

    def visible(probe: str) -> bool:
        probe = probe.replace("\\\n", "").replace("'", "").replace('"', "")
        # Quoting backslashes vanish; printf or echo -e escapes such as \t separate words.
        return bool(
            _OPERATION_SHAPE.search(probe.replace("\\", ""))
            or _OPERATION_SHAPE.search(re.sub(r"\\[abefnrtv]", " ", probe))
        )

    if visible(text):
        return True
    decoded = numeric_reading(text)
    if decoded is None or visible(decoded):
        return True
    if "$'" not in text:
        return False
    reading = ansi_c_reading(text)
    return reading is None or visible(reading)


def utility_executor_options(argv: list[str]) -> bool:
    if not argv:
        return False
    utility = Path(argv[0]).name
    if utility == "rg":
        return any(arg.partition("=")[0] in {"--pre", "--pre-glob"} for arg in argv[1:])
    if utility == "git":
        return any(
            arg == "mergetool"
            or arg.startswith(
                (
                    "--config-env",
                    "--env-filter",
                    "--tree-filter",
                    "--index-filter",
                    "--parent-filter",
                    "--msg-filter",
                    "--commit-filter",
                    "--to-cmd",
                    "--cc-cmd",
                    "--bcc-cmd",
                    "--header-cmd",
                )
            )
            for arg in argv[1:]
        )
    return False


def expanded_merge_candidate(command: str, *, admin: bool = False, depth: int = 0) -> bool:
    """Find operation roles assembled from bounded literal pieces, for engagement only.

    An owned operation still goes through the reader's dynamic-word refusal.
    This never supplies expanded argv to a guard or evaluates shell code.
    """
    if depth > MAX_DEPTH or len(command.encode()) > MAX_WORK:
        return True
    source = command.replace("\\\n", "").encode()
    tree = Parser(_LANGUAGE).parse(source)
    bindings: dict[str, str | None] = {}
    work = 0

    def expanded(node):
        value = literal(node)
        if value is not None:
            return value
        if node.type == "command_name":
            return expanded(node.named_children[0])
        if node.type in {"simple_expansion", "expansion"}:
            match = re.fullmatch(r"\$(?:([A-Za-z_]\w*)|\{([A-Za-z_]\w*)\})", node.text.decode())
            return bindings.get(match[1] or match[2]) if match else None
        if node.type in {"string", "concatenation"}:
            parts = []
            cursor = node.start_byte + (1 if node.type == "string" else 0)
            for child in node.named_children:
                parts.append(source[cursor : child.start_byte].decode())
                if child.type == "string_content":
                    parts.append(re.sub(r'\\([$`"\\\n])', lambda m: "" if m[1] == "\n" else m[1], child.text.decode()))
                else:
                    parts.append(expanded(child))
                cursor = child.end_byte
            end = node.end_byte - (1 if node.type == "string" else 0)
            parts.append(source[cursor:end].decode())
            return None if None in parts else "".join(parts)
        if node.type == "command_substitution":
            # Only fixed logging producers have a bounded literal stdout.
            children = node.named_children
            if len(children) == 1 and children[0].type == "command":
                args = [expanded(child) for child in children[0].named_children]
                if None not in args and args:
                    if args[0] == "echo" and all(not arg.startswith("-") for arg in args[1:]):
                        return " ".join(args[1:]).rstrip("\n")
                    if args[:2] in [["printf", "%s"], ["printf", "%s\\n"]]:
                        return "".join(args[2:]).rstrip("\n")
        return None

    def visit(node, *, top=False):
        nonlocal work
        work += 1
        if work > MAX_WORK:
            return True
        if node.type == "variable_assignment" and top:
            name = node.child_by_field_name("name")
            value = node.child_by_field_name("value")
            if name is not None:
                key = name.text.decode()
                bindings[key] = expanded(value) if value is not None and key not in bindings else None
        if node.type == "command":
            words = [
                child
                for child in node.named_children
                if child.type
                in {
                    "command_name",
                    "word",
                    "number",
                    "string",
                    "raw_string",
                    "ansi_c_string",
                    "translated_string",
                    "concatenation",
                    "simple_expansion",
                    "expansion",
                    "command_substitution",
                    "arithmetic_expansion",
                }
            ]
            args = [expanded(word) for word in words]
            start, _scopes = wrapper_scopes([arg if arg is not None else UNREADABLE for arg in args])
            args, words = args[start:], words[start:]
            if args:
                utility = utility_name(args[0]) if args[0] is not None else UNREADABLE
                if (
                    utility == UNREADABLE
                    and args[1:2] in ([], [None])
                    and any(re.search(r"\$\{?" + re.escape(name) + r"\b", words[0].text.decode()) for name in bindings)
                ):
                    return True
                if utility in {"read", "unset", "declare", "typeset", "source", "."} or (
                    utility == "printf" and "-v" in args
                ):
                    bindings.update(dict.fromkeys(bindings))
                if utility == "gh" or (utility == UNREADABLE and args[1:2] == ["pr"]):
                    if args[1:2] == [None] or (args[1:2] == ["pr"] and args[2:3] == [None]):
                        return True
                    if args[1:3] == ["pr", "merge"] and (
                        not admin
                        or any(
                            literal(word) is None or (arg or "").startswith("--admin")
                            for word, arg in zip(words[3:], args[3:], strict=True)
                        )
                    ):
                        return True
                if (
                    utility in {"git", UNREADABLE}
                    and args[1:2] in [["checkout"], ["switch"], ["branch"], ["worktree"]]
                    and any(literal(word) is None for word in words[1:])
                ):
                    return True
                payload_index = (
                    1 if utility in {"eval", "trap"} else 2 if utility in _SHELLS and args[1:2] == ["-c"] else None
                )
                if payload_index is not None and len(args) > payload_index:
                    payload = args[payload_index]
                    if payload is not None and expanded_merge_candidate(payload, admin=admin, depth=depth + 1):
                        return True
                    if payload is None and any(
                        re.search(r"\$\{?" + re.escape(name) + r"\b", words[payload_index].text.decode())
                        for name in bindings
                    ):
                        return True
                if utility == "find" and any(arg in {"-exec", "-execdir", "-ok", "-okdir"} for arg in args):
                    for i, arg in enumerate(args):
                        if (
                            arg in _SHELLS
                            and args[i + 1 : i + 2] == ["-c"]
                            and len(args) > i + 2
                            and (
                                args[i + 2] is None
                                or expanded_merge_candidate(args[i + 2], admin=admin, depth=depth + 1)
                            )
                        ):
                            return True
        return any(visit(child) for child in node.named_children)

    return any(visit(child, top=True) for child in tree.root_node.named_children)


def cd_target(argv: list[str], cwd: str | None) -> str | None:
    """Bash logical cd (normalise before following symlinks), or physical -P."""
    args = argv[1:]
    physical = False
    while args and args[0].startswith("-") and args[0] not in {"-", UNREADABLE}:
        option = args.pop(0)
        if option == "--":
            break
        if not re.fullmatch(r"-[LPe]+", option):
            return None
        for flag in option[1:]:
            if flag in {"P", "L"}:
                physical = flag == "P"
    target = args[0] if args else os.path.expanduser("~")
    if target in {"-", UNREADABLE} or len(args) > 1:
        return None
    target = os.path.expanduser(target)
    if not os.path.isabs(target):
        if cwd is None:
            return None
        target = os.path.join(cwd, target)
    return str(Path(target).resolve()) if physical else os.path.normpath(target)


# ---------------------------------------------------------------------------
# Parsing (grammar-0.25 repairs only; no shell semantics are modelled here)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Heredoc:
    """A here-document as Bash reads it. Only an unquoted delimiter expands the body."""

    literal: bool
    body: str
    spans: tuple[str, ...] = ()


# The only admitted delimiter words: a plain word, or one quoted whole.
_HEREDOC_DELIMITER = re.compile(rb"[A-Za-z_0-9]+|'[A-Za-z_0-9]+'|\"[A-Za-z_0-9]+\"|\\[A-Za-z_0-9]+")
_HEREDOC_TOKEN = "GUARD_HERE_"
_WORD_END = (b"", b" ", b"\t", b"\n", b";", b"&", b"|", b"<", b">", b"(", b")")
MAX_HEREDOCS = 64
MAX_SPAN_PARSES = 64
_HEREDOC_WORDS = {"command_substitution", "arithmetic_expansion", "expansion", "simple_expansion"}


def _descendants(root):
    pending = [root]
    while pending:
        node = pending.pop()
        yield node
        pending.extend(node.named_children)


def _in_backquotes(node) -> bool:
    """Old-style substitutions are re-read from their own unescaped text, heredocs included."""
    parent = node.parent
    while parent is not None:
        if parent.type == "command_substitution" and parent.text.startswith(b"`"):
            return True
        parent = parent.parent
    return False


def _opener_line_end(encoded: bytes, start: int) -> int | None:
    """The newline that ends a heredoc opener's command line, or None if the rest may span lines."""
    index, quote = start, None
    while index < len(encoded):
        char, pair = encoded[index : index + 1], encoded[index : index + 2]
        if char == b"\n":
            return index if quote is None else None
        if quote == b"'":
            quote = None if char == b"'" else quote
        elif char == b"\\":
            if encoded[index + 1 : index + 2] in (b"\n", b""):
                return None
            index += 1
        elif quote is not None and char == quote[-1:]:
            quote = None
        elif char == b"`" or pair in (b"$(", b"${", b"$[", b"<(", b">("):
            return None
        elif quote is None and pair == b"$'":
            quote, index = pair, index + 1
        elif quote is None and char in (b"'", b'"'):
            quote = char
        elif quote is None and char == b"#" and encoded[index - 1 : index] in b" \t;&|()":
            end = encoded.find(b"\n", index)
            return end if end >= 0 else None
        index += 1
    return None


def _grammar_line_end(encoded: bytes, tree, opener) -> int:
    """Fallback for a complex opener line: where an error-free parse starts the body."""
    if tree.root_node.has_error:
        raise ShellParseError("Bash parse error")
    anchor = next((c for c in opener.parent.named_children if c.type in {"heredoc_body", "heredoc_end"}), None)
    if anchor is None:
        raise ShellParseError("here-document body start cannot be established")
    begin = anchor.start_byte
    while encoded[begin - 1 : begin] in (b" ", b"\t"):
        begin -= 1
    if encoded[begin - 1 : begin] != b"\n" or begin - 1 < opener.end_byte:
        raise ShellParseError("here-document body start cannot be established")
    return begin - 1


def _heredoc_document(encoded: bytes, start: int, delimiter: bytes, strip_tabs: bool, join: bool):
    """Read one here-document as Bash does, from its first body line.

    Returns the document and the source range of its delimiter line. An unquoted
    document joins backslash-newline pairs while it is read, so a joined line can
    be the delimiter; `<<-` strips leading tabs from every line. The delimiter
    line holds the word alone; the last line may lack its newline. Bash reads an
    undelimited document to the end of its input, which a harness may extend,
    so that refuses as a parse error, as grammar 0.25 does.
    """
    document = bytearray()
    position = start
    while position < len(encoded):
        line, line_start, newline = bytearray(), position, False
        while position < len(encoded):
            byte = encoded[position]
            if join and byte == 0x5C:
                if encoded[position + 1 : position + 2] != b"\n":
                    line += encoded[position : position + 2]
                position += 2
                continue
            position += 1
            if byte == 0x0A:
                newline = True
                break
            line.append(byte)
        if strip_tabs:
            line = line.lstrip(b"\t")
        if line == delimiter:
            return document.decode(), line_start, position - newline
        document += line + b"\n"
    raise ShellParseError("Bash parse error")


_PARAMETER = re.compile(r"\$(?:[A-Za-z_][A-Za-z_0-9]*|[0-9@*#?$!-])")
_EXPANSION_KINDS = {
    "(": (")", {"command_substitution", "arithmetic_expansion"}),
    "{": ("}", {"expansion"}),
    "[": ("]", {"arithmetic_expansion"}),
}


def _expansion_spans(document: str) -> tuple[str, ...]:
    """Every expansion Bash performs in an unquoted here-document body, in order.

    A backslash quotes only `$`, a backquote or another backslash there;
    quotes and `$'...'` are plain text.
    """
    spans = []
    index = 0
    while index < len(document):
        char = document[index]
        if char == "\\":
            index += 2 if document[index + 1 : index + 2] in ("$", "`", "\\") else 1
            continue
        if char == "`":
            end = index + 1
            while end < len(document) and document[end] != "`":
                end += 2 if document[end] == "\\" else 1
            if end >= len(document):
                raise ShellParseError("unterminated backquote in a here-document")
            spans.append(document[index : end + 1])
            index = end + 1
            continue
        if char == "$" and document[index + 1 : index + 2] in _EXPANSION_KINDS:
            end = _expansion_end(document, index)
            spans.append(document[index:end])
            index = end
            continue
        parameter = _PARAMETER.match(document, index)
        if parameter:
            spans.append(parameter[0])
            index = parameter.end()
            continue
        index += 1
    return tuple(spans)


def _expansion_end(document: str, start: int) -> int:
    """End of the `$(`, `${` or `$[` expansion at start: the first closer that parses cleanly.

    Inside `${...}` a single quote is read differently by Bash versions and modes,
    so it refuses.
    """
    closer, kinds = _EXPANSION_KINDS[document[start + 1]]
    end = start + 2
    for _ in range(MAX_SPAN_PARSES):
        end = document.find(closer, end) + 1
        if not end:
            raise ShellParseError("unterminated expansion in a here-document")
        span = document[start:end]
        root = Parser(_LANGUAGE).parse((": " + span).encode()).root_node
        words = root.named_children[0].named_children if len(root.named_children) == 1 else []
        if not root.has_error and len(words) == 2 and words[1].type in kinds and words[1].text.decode() == span:
            if closer == "}" and "'" in span:
                raise ShellParseError("single quote in a here-document parameter expansion")
            return end
    raise ShellParseError("here-document expansion limit", reason_class="LIMIT_EXCEEDED")


def _neutralize_heredocs(encoded: bytes, tree, heredocs: dict[str, _Heredoc]) -> bytes | None:
    """Read the first command line's unread here-documents as Bash does; hide their bodies.

    Grammar 0.25 loses expansions after leading whitespace in heredoc bodies and
    fails on others. Each body is read here instead, and its opener and delimiter
    line are renamed to a quoted unique token, so the grammar sees opaque text.
    """
    openers = sorted(
        (
            node
            for node in _descendants(tree.root_node)
            if node.type == "heredoc_start"
            and node.text.strip(b"'").decode() not in heredocs
            and not _in_backquotes(node)
        ),
        key=lambda node: node.start_byte,
    )
    # Bodies follow their openers in order, so reading stops at the first opener
    # the grammar left in an ERROR node; the parse then refuses.
    readable = [
        node.parent.type == "heredoc_redirect"
        and node.prev_sibling is not None
        and node.prev_sibling.type in {"<<", "<<-"}
        for node in openers
    ]
    if False in readable:
        openers = openers[: readable.index(False)]
    if not openers:
        return None
    line_end = _opener_line_end(encoded, openers[0].end_byte)
    if line_end is None:
        line_end = _grammar_line_end(encoded, tree, openers[0])
        if any(node.start_byte < line_end for node in openers[1:]):
            raise ShellParseError("here-document body start cannot be established")
    body_start = line_end + 1
    # A body queued behind an already read heredoc on the same line starts after its delimiter.
    for end in _descendants(tree.root_node):
        if end.type == "heredoc_end" and end.text.decode() in heredocs and end.start_byte > line_end:
            earlier = next(c for c in end.parent.named_children if c.type == "heredoc_start")
            if earlier.end_byte <= openers[0].start_byte and b"\n" not in encoded[earlier.end_byte : line_end]:
                body_start = max(body_start, end.end_byte + 1)
    edits = []
    for opener in (node for node in openers if node.start_byte < line_end):
        operator = opener.prev_sibling
        if (
            not _HEREDOC_DELIMITER.fullmatch(opener.text)
            or encoded[opener.end_byte : opener.end_byte + 1] not in _WORD_END
        ):
            raise ShellParseError("ambiguous heredoc delimiter")
        quoted = bool(re.search(rb"['\"\\]", opener.text))
        delimiter = opener.text.strip(b"'\"").lstrip(b"\\")
        document, closer_start, closer_end = _heredoc_document(
            encoded, body_start, delimiter, operator.type == "<<-", join=not quoted
        )
        token = f"{_HEREDOC_TOKEN}{len(heredocs)}{'Q' if quoted else 'U'}"
        heredocs[token] = _Heredoc(quoted, document, () if quoted else _expansion_spans(document))
        edits += [
            (opener.start_byte, opener.end_byte, f"'{token}'".encode()),
            (closer_start, closer_end, token.encode()),
        ]
        if encoded[body_start : body_start + 1] == b"\\":
            # Grammar 0.25 reads a first body line that starts with a backslash as
            # command words, quoted or not. The body is already read; pad only the grammar's copy.
            edits.append((body_start, body_start, b" "))
        body_start = closer_end + 1
    for begin, end, replacement in sorted(edits, reverse=True):
        encoded = encoded[:begin] + replacement + encoded[end:]
    return encoded


def _queue_heredoc(encoded: bytes, tree) -> bytes | None:
    """Grammar 0.25 cannot queue multiple heredocs: its second opener is an ERROR '<'
    plus a file_redirect. Move it to an inert `:` reader on the line where its body
    starts, after the first heredoc's delimiter line. Shell readers need the final
    stdin specifically and are refused."""
    for candidate in _descendants(tree.root_node):
        if candidate.type != "heredoc_redirect":
            continue
        end = next((c for c in candidate.named_children if c.type == "heredoc_end"), None)
        extra = next((c for c in candidate.named_children if c.type == "file_redirect"), None)
        if end is None or extra is None or encoded[extra.start_byte - 1 : extra.start_byte] != b"<":
            continue
        opener = b"<" + extra.text
        if not opener.startswith(b"<<"):
            continue
        body_start = encoded.find(b"\n", end.end_byte) + 1
        if not body_start:
            continue
        reader = next((c for c in candidate.parent.named_children if c.type == "command"), None)
        if reader is not None:
            arguments = [literal(c) or UNREADABLE for c in reader.named_children if c.type != "variable_assignment"]
            index, _ = invoked_start(arguments)
            if index < len(arguments) and Path(arguments[index]).name in _SHELLS:
                raise ShellParseError("queued shell heredoc payload")
        begin = extra.start_byte - 1
        encoded = encoded[:body_start] + b": " + opener + b"\n" + encoded[body_start:]
        return encoded[:begin] + b" " * (extra.end_byte - begin) + encoded[extra.end_byte :]
    return None


def _parse(source: str):
    """Parse one Bash program, repairing only AST-identified grammar-0.25 misparses.

    Returns the tree and the Bash reading of each here-document, keyed by the
    token that names it in the tree.
    """
    if _HEREDOC_TOKEN in source:
        raise ShellParseError("reserved here-document token in the command")
    encoded = source.encode()
    tree = Parser(_LANGUAGE).parse(encoded)
    heredocs: dict[str, _Heredoc] = {}
    for _ in range(MAX_HEREDOCS):
        rewritten = _neutralize_heredocs(encoded, tree, heredocs)
        if rewritten is None:
            rewritten = _queue_heredoc(encoded, tree)
        if rewritten is None:
            break
        encoded = rewritten
        tree = Parser(_LANGUAGE).parse(encoded)
    else:
        raise ShellParseError("here-document limit", reason_class="LIMIT_EXCEEDED")
    # Grammar 0.25 splits words around line continuations. Repair only
    # gaps between AST words in commands; quoted data and heredocs stay intact.
    pending = [tree.root_node]
    joins = []
    while pending:
        node = pending.pop()
        if node.type == "command":
            for left, right in pairwise(node.named_children):
                if encoded[left.end_byte : right.start_byte] == b"\\\n":
                    joins.append((left.end_byte, right.start_byte))
        pending.extend(node.named_children)
    for begin, end in sorted(joins, reverse=True):
        encoded = encoded[:begin] + encoded[end:]
    if joins:
        tree = Parser(_LANGUAGE).parse(encoded)
    # Repair AST-identified descriptor and escaped-number lexer errors. Bash
    # treats out-of-range descriptors as argv, whereas zero and leading-zero
    # descriptors are redirects. Quoted strings stay untouched.
    edits = []
    pending = [tree.root_node]
    while pending:
        candidate = pending.pop()
        if candidate.type == "file_redirect":
            descriptor = re.match(rb"([0-9]+)[<>]", candidate.text)
            if descriptor:
                digits = descriptor[1]
                if int(digits) > 2147483647 or digits.startswith(b"0"):
                    replacement = b"'" + digits + b"'" if int(digits) > 2147483647 else b"1"
                    edits.append((candidate.start_byte, candidate.start_byte + len(digits), replacement))
        if candidate.type == "number" and candidate.parent.type == "command":
            start = candidate.start_byte
            if encoded[max(0, start - 2) : start] == b"\\ ":
                cursor = start - 2
                while cursor >= 0 and encoded[cursor : cursor + 1] == b"\\":
                    cursor -= 1
                if (start - 2 - cursor) % 2:
                    edits.append((start - 2, candidate.end_byte, b"' " + candidate.text + b"'"))
            elif candidate.text == b"0" and encoded[candidate.end_byte : candidate.end_byte + 1] in {b">", b"<"}:
                edits.append((start, candidate.end_byte, b"1"))
        start = candidate.start_byte
        if (
            candidate.type == "concatenation"
            and re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*\}", candidate.text)
            and start
            and encoded[start - 1 : start] == b"{"
        ):
            start -= 1
        if (
            candidate.type == "concatenation"
            and re.fullmatch(rb"\{[A-Za-z_][A-Za-z_0-9]*\}", encoded[start : candidate.end_byte])
            and encoded[candidate.end_byte : candidate.end_byte + 1] in {b">", b"<"}
        ):
            edits.append((start, candidate.end_byte, b" " * (candidate.end_byte - start - 1) + b"9"))
        elif candidate.type == "heredoc_redirect":
            opener = next(c for c in candidate.named_children if c.type == "heredoc_start")
            quoted = any(q in opener.text for q in (b"'", b'"', b"\\"))
            pending.extend(c for c in candidate.named_children if not quoted or c.type != "heredoc_body")
        else:
            pending.extend(candidate.named_children)
    if edits:
        for start, end, replacement in sorted(edits, reverse=True):
            encoded = encoded[:start] + replacement + encoded[end:]
        tree = Parser(_LANGUAGE).parse(encoded)
    if tree.root_node.has_error:
        raise ShellParseError("Bash parse error")
    for node in _descendants(tree.root_node):
        if node.type != "heredoc_redirect" or _in_backquotes(node):
            continue
        opener = next((c for c in node.named_children if c.type == "heredoc_start"), None)
        end = next((c for c in node.named_children if c.type == "heredoc_end"), None)
        token = opener.text[1:-1].decode() if opener is not None else ""
        if token not in heredocs or opener.text != f"'{token}'".encode() or end is None or end.text != token.encode():
            raise ShellParseError("here-document does not end where Bash ends it")
    return tree, heredocs


# ---------------------------------------------------------------------------
# Collection: every simple command in the unpruned tree, with its position
# ---------------------------------------------------------------------------


@dataclass
class _Command:
    node: object
    redirects: list
    words: list
    argv: list[str]
    start: int
    scopes: list
    assignments: list[str]
    dynamic_redirect: bool
    nested: bool
    item: int | None
    member: int
    left: list = field(default_factory=list)
    payload_error: ShellParseError | None = None
    # Expansions of this command's unquoted heredoc bodies, parsed as words.
    heredoc_words: list = field(default_factory=list)

    @property
    def selected(self) -> list[str]:
        return self.argv[self.start :]

    @property
    def utility(self) -> str:
        if not self.selected:
            return ""
        return utility_name(self.selected[0])


@dataclass
class _Item:
    node: object
    connector: str | None
    background: bool = False
    redirects: list = field(default_factory=list)


@dataclass
class _Program:
    commands: list = field(default_factory=list)
    nodes: list = field(default_factory=list)
    definitions: list = field(default_factory=list)
    items: list = field(default_factory=list)
    compounds: list = field(default_factory=list)
    # By heredoc_redirect node id: Bash's reading of the body, and its expansions as words.
    heredocs: dict = field(default_factory=dict)
    heredoc_words: dict = field(default_factory=dict)


class _Budget:
    def __init__(self) -> None:
        self.work = 0

    def charge(self) -> None:
        self.work += 1
        if self.work > MAX_WORK:
            raise ShellParseError("shell walk work limit", reason_class="LIMIT_EXCEEDED")


def _top_items(root) -> list[_Item]:
    """Flatten the top-level program into items joined by their connectors."""
    items: list[_Item] = []
    separator = None
    group_start = 0

    def flatten(node, connector, redirects=()):
        body = node.child_by_field_name("body") if node.type == "redirected_statement" else None
        if body is not None and body.type == "list":
            # Grammar 0.25 hangs a trailing redirect on the whole `&&`/`||` list;
            # Bash binds it to the list's last command.
            flatten(body, connector, (*(c for c in node.named_children if c != body), *redirects))
        elif node.type == "list":
            parts = [c for c in node.children if c.is_named and c.type != "comment"]
            operator = next((c.type for c in node.children if c.type in {"&&", "||"}), None)
            if len(parts) != 2 or operator is None:
                raise ShellParseError("unexpected list shape")
            flatten(parts[0], connector)
            flatten(parts[1], operator, redirects)
        else:
            items.append(_Item(node, connector, redirects=list(redirects)))

    for child in root.children:
        if child.type == "comment":
            continue
        if not child.is_named:
            if child.type == "&":
                for item in items[group_start:]:
                    item.background = True
            if child.type in {";", "&"}:
                separator = child.type
            continue
        group_start = len(items)
        flatten(child, None if not items else separator or "\n")
        separator = None
    return items


def _redirect_words(command, redirects, budget):
    """Words of a simple command, including trailing argv the grammar put in redirects."""
    words = [c for c in command.named_children if c.type in _COMMAND_WORDS]
    all_redirects = [
        *redirects,
        *(c for c in command.named_children if c.type in {"file_redirect", "heredoc_redirect", "herestring_redirect"}),
    ]
    dynamic_redirect = False
    for redirect in all_redirects:
        budget.charge()
        if redirect.type == "herestring_redirect":
            dynamic_redirect |= any(literal(c) is None for c in redirect.named_children)
        if redirect.type == "file_redirect":
            descriptor = redirect.child_by_field_name("descriptor")
            if descriptor and descriptor.text.isdigit() and int(descriptor.text) > 2147483647:
                raise ShellParseError("redirect descriptor exceeds Bash integer range")
            destinations = [c for c in redirect.named_children if c.type != "file_descriptor"]
            if destinations:
                dynamic_redirect |= literal(destinations[0]) is None
                # The grammar puts ordinary trailing arguments in redirects.
                words.extend(destinations[1:])
            if re.search(rb"\\ [0-9]+[<>]", redirect.parent.text):
                raise ShellParseError("escaped space before glued redirect")
    # Named descriptors are incorrectly attached to the command by grammar 0.25.
    words = [
        w
        for w in words
        if not (
            re.fullmatch(rb"\{[A-Za-z_][A-Za-z_0-9]*\}", w.text)
            and any(r.start_byte == w.end_byte for r in all_redirects)
        )
    ]
    words.sort(key=lambda n: n.start_byte)
    return words, all_redirects, dynamic_redirect


def _shell_payload(selected: list[str], redirects, heredocs: dict) -> tuple[str | None, ShellParseError | None]:
    """The literal code a shell or eval invocation runs, or the refusal for unreadable code."""
    utility = utility_name(selected[0])
    if utility == "eval":
        operands = selected[1:]
        if operands[:1] == ["--"]:
            operands = operands[1:]
        if UNREADABLE in operands:
            return None, ShellParseError("dynamic eval payload", reason_class="DYNAMIC_COMMAND")
        return " ".join(operands), None
    for i, arg in enumerate(selected[1:], 1):
        if arg.startswith(("-", "+")) and "c" in arg[1:] and not arg.startswith("--"):
            # Bash accepts either sign for command options. Each packed -o/-O
            # consumes an option name before the command string.
            if "o" in arg[1:] or "O" in arg[1:]:
                return None, ShellParseError(
                    "packed shell -c with -o/-O cannot establish execution payload", reason_class="EXECUTOR_OPTION"
                )
            payload = selected[i + 1] if i + 1 < len(selected) else UNREADABLE
            # Shells keep processing options after -c, including -- and -o/-O.
            if payload.startswith(("-", "+")) and payload != UNREADABLE:
                return None, ShellParseError(
                    "shell options after -c cannot establish execution payload", reason_class="EXECUTOR_OPTION"
                )
            if payload == UNREADABLE:
                return None, ShellParseError("dynamic shell payload", reason_class="DYNAMIC_COMMAND")
            return payload, None
    documents = [heredocs.get(r.id) for r in redirects if r.type == "heredoc_redirect"]
    if documents:
        # An unquoted body is code only after its expansions run; their output is unknown.
        if any(document is None or document.spans for document in documents):
            return None, ShellParseError("dynamic shell payload", reason_class="DYNAMIC_COMMAND")
        return "\n".join(
            document.body if document.literal else re.sub(r"\\([$`\\])", r"\1", document.body) for document in documents
        ), None
    here_strings = [r for r in redirects if r.type == "herestring_redirect"]
    if here_strings:
        value = literal(here_strings[-1].named_children[-1])
        if value is None:
            return None, ShellParseError("dynamic shell payload", reason_class="DYNAMIC_COMMAND")
        return value, None
    index = 1
    while index < len(selected):
        arg = selected[index]
        if arg in {"-o", "+o", "-O", "+O", "--rcfile", "--init-file"}:
            index += 2
            continue
        if arg == "--" or not arg.startswith(("-", "+")):
            break
        index += 1
    if selected[index : index + 1] == ["--"]:
        index += 1
    if index < len(selected) and selected[index] != UNREADABLE:
        return None, _ScriptFile("shell script file cannot establish execution payload")
    return None, ShellParseError(
        "opaque shell input cannot establish execution payload", reason_class="EXECUTED_REDIRECT"
    )


class _ScriptFile(ShellParseError):
    """A shell runs a script on disk; refused only when this command visibly writes operation text."""

    def __init__(self, message: str) -> None:
        super().__init__(message, reason_class="EXECUTED_REDIRECT")


def _collect(
    source: str, program: _Program, budget: _Budget, depth: int, *, nested: bool = False, left: list | None = None
) -> None:
    """Record every simple command, definition and node, with no pruning."""
    if depth > MAX_DEPTH:
        raise ShellParseError("nested shell depth limit", reason_class="LIMIT_EXCEEDED")
    tree, heredocs = _parse(source)
    root = tree.root_node
    pending = [root]
    while pending:
        node = pending.pop()
        budget.charge()
        if node.type not in GRAMMAR_NODES:
            raise ShellParseError(f"`{node.type}` is outside the written grammar")
        if node.type == "heredoc_redirect" and not _in_backquotes(node):
            opener = next(c for c in node.named_children if c.type == "heredoc_start")
            program.heredocs[node.id] = heredocs[opener.text[1:-1].decode()]
        pending.extend(node.named_children)
    program.nodes.append(root)
    top = not nested and depth == 0
    items = _top_items(root) if top else []
    if top:
        program.items = items

    def visit(node, inner: bool, item: int | None, member: int, left: list, attached: tuple = ()):
        budget.charge()
        kind = node.type
        if kind == "command":
            simple(node, list(attached), inner, item, member, left)
            return
        if kind == "redirected_statement":
            body = node.child_by_field_name("body")
            redirects = [*attached, *(c for c in node.named_children if c != body)]
            if body is not None and body.type == "command":
                simple(body, redirects, inner, item, member, left)
                return
            program.compounds.append(node)
            for redirect in redirects:
                # Through visit, so a heredoc's expansions are read like any other.
                visit(redirect, True, None, 0, [])
            if body is not None:
                visit(body, True, item, member, left)
            return
        if kind == "pipeline":
            members = [c for c in node.named_children if c.type != "comment"]
            for index, child in enumerate(members):
                visit(child, inner, item, index, members[:index], attached if index == len(members) - 1 else ())
            return
        for redirect in attached:
            # Redirects a compound statement carries still run their substitutions.
            visit(redirect, True, None, 0, [])
        if kind == "function_definition":
            program.definitions.append(node)
            visit_children(node, True)
            return
        if kind in {"command_substitution", "process_substitution"}:
            raw = node.text.decode()
            if raw.startswith("`"):
                # Bash removes backslash before $, ` and backslash in old substitutions.
                _collect(re.sub(r"\\([$`\\])", r"\1", raw[1:-1]), program, budget, depth + 1, nested=True)
                return
            visit_children(node, True)
            return
        if kind == "heredoc_redirect":
            document = program.heredocs.get(node.id)
            if document is None:
                raise ShellParseError("here-document was not read")
            if document.spans:
                # Bash expands an unquoted body before the command runs. Read its
                # expansions exactly as the same words outside a heredoc.
                first = len(program.nodes)
                _collect(": " + " ".join(document.spans), program, budget, depth + 1, nested=True)
                synthetic = program.nodes[first].named_children
                words = synthetic[0].named_children[1:] if len(synthetic) == 1 else []
                if len(words) != len(document.spans) or any(w.type not in _HEREDOC_WORDS for w in words):
                    raise ShellParseError("here-document expansions cannot be read")
                program.heredoc_words[node.id] = words
            # The body was read above; the grammar's copy of it is opaque.
            for child in node.named_children:
                if child.type != "heredoc_body":
                    visit(child, True, None, 0, [])
            return
        if kind in {"raw_string", "ansi_c_string", "comment"}:
            return
        if kind in {
            "subshell",
            "compound_statement",
            "if_statement",
            "while_statement",
            "for_statement",
            "c_style_for_statement",
            "case_statement",
            "negated_command",
            "test_command",
        }:
            program.compounds.append(node)
            # A compound pipeline member's commands read the same stdin.
            visit_children(node, True, None, 0, left)
            return
        visit_children(node, inner, item, member, left)

    def visit_children(node, inner, item=None, member=0, left=()):
        for child in node.named_children:
            visit(child, inner, item, member, list(left))

    def simple(node, redirects, inner, item, member, left):
        words, all_redirects, dynamic_redirect = _redirect_words(node, redirects, budget)
        argv = [literal(word) for word in words]
        assignments = [c.text.decode() for c in node.named_children if c.type == "variable_assignment"]
        if argv and argv[0] is None:
            argv = [UNREADABLE if arg is None else arg for arg in argv]
            start, scopes = 0, []
        else:
            argv = [UNREADABLE if arg is None else arg for arg in argv]
            start, scopes = wrapper_scopes(argv)
        command = _Command(
            node=node,
            redirects=all_redirects,
            words=words,
            argv=argv,
            start=start,
            scopes=scopes,
            assignments=assignments,
            dynamic_redirect=dynamic_redirect,
            nested=inner,
            item=item,
            member=member,
            left=list(left),
        )
        program.commands.append(command)
        # Substitutions in words, assignments and redirects run before the command.
        for child in node.named_children:
            if child.type not in {"command_name"}:
                visit(child, True, None, 0, [])
            else:
                visit_children(child, True)
        for redirect in redirects:
            visit(redirect, True, None, 0, [])
        command.heredoc_words = [
            word
            for redirect in all_redirects
            if redirect.type == "heredoc_redirect"
            for word in program.heredoc_words.get(redirect.id, ())
        ]
        selected = command.selected
        if not selected or selected[0] == UNREADABLE:
            return
        utility = utility_name(selected[0])
        if utility in _SHELLS or utility == "eval":
            payload, error = _shell_payload(selected, all_redirects, program.heredocs)
            command.payload_error = error
            if payload is not None:
                # The payload reads the invoking shell's stdin.
                _collect(payload, program, budget, depth + 1, nested=True, left=command.left)
        if utility == "trap" and len(selected) > 1:
            operands = selected[1:]
            if operands[0] == "--":
                operands = operands[1:]
            if operands and operands[0] != UNREADABLE and not operands[0].startswith("-"):
                try:
                    _collect(operands[0], program, budget, depth + 1, nested=True)
                except ShellParseError as exc:
                    if exc.reason_class == "LIMIT_EXCEEDED":
                        raise
                    command.payload_error = ShellParseError(
                        "trap payload cannot be read", reason_class="VISIBLE_SOURCE"
                    )

    if not top:
        # Everything in a payload or substitution runs nested in its parent.
        visit_children(root, True, None, 0, left or ())
        return
    for index, item in enumerate(items):
        visit(item.node, item.background, index, 0, [], tuple(item.redirects))


# ---------------------------------------------------------------------------
# Unconditional refusals (ruling item 5)
# ---------------------------------------------------------------------------

_ARITHMETIC_ASSIGN = re.compile(r"(?:[-+*/%&^|]|<<|>>)?=|\+\+|--")
_DYNAMIC_WORDS = {
    "simple_expansion",
    "expansion",
    "command_substitution",
    "process_substitution",
    "arithmetic_expansion",
}


def _name_computed(name) -> bool:
    """A variable name node that is not a literal name (a computed subscript is fine)."""
    if name.type == "variable_name":
        return False
    if name.type == "subscript":
        inner = name.child_by_field_name("name")
        return inner is None or inner.type != "variable_name"
    return True


def _computed_name(word) -> bool:
    """An assignment-like word whose variable name depends on an expansion."""
    if word.type == "variable_assignment":
        name = word.child_by_field_name("name")
        return name is None or _name_computed(name)
    equals = word.text.find(b"=")
    pending = [word]
    while pending:
        child = pending.pop()
        if child.type in _DYNAMIC_WORDS and (equals < 0 or child.start_byte - word.start_byte < equals):
            return True
        pending.extend(child.named_children)
    return False


def _arithmetic_roots(root):
    """Arithmetic contexts: $((...)), ((...)) commands and C-style for headers."""
    pending = [root]
    while pending:
        node = pending.pop()
        if node.type in {"raw_string", "comment"}:
            continue
        if node.type in {"arithmetic_expansion", "c_style_for_statement"} or (
            node.type == "compound_statement" and node.text.startswith(b"((")
        ):
            yield node
            continue
        pending.extend(node.named_children)


def _arithmetic_computed(root) -> bool:
    """An arithmetic assignment or increment whose target is computed."""
    pending = [root]
    while pending:
        node = pending.pop()
        if node.type in {"binary_expression", "postfix_expression", "unary_expression"}:
            operator = next((c.type for c in node.children if not c.is_named), "")
            target = node.named_children[0] if node.named_children else None
            # C-style for headers parse a plain target name as a `word`.
            if (
                _ARITHMETIC_ASSIGN.fullmatch(operator)
                and operator not in {"==", "<=", ">=", "!="}
                and target is not None
                and target.type not in {"variable_name", "subscript", "number"}
                and not (target.type == "word" and re.fullmatch(rb"[A-Za-z_][A-Za-z_0-9]*", target.text))
            ):
                return True
        pending.extend(node.named_children)
    return False


def _lookup_only(command: _Command) -> bool:
    """`command -v NAME` and `command -V NAME` only look a name up."""
    return any(
        name == "command" and any(re.fullmatch(r"-[pvV]+", o) and ("v" in o or "V" in o) for o in options)
        for name, options in command.scopes
    )


def _binding_reason(program: _Program) -> str | None:
    """The first unconditional binding change in the command, or None."""
    for command in program.commands:
        selected = command.selected
        if not selected or selected[0] == UNREADABLE or _lookup_only(command):
            continue
        utility = utility_name(selected[0])
        args = selected[1:]
        if any(_BINDING_TABLE.fullmatch(arg) for arg in command.argv):
            return "shell alias or command-hash table write"
        if utility in _BINDING_BUILTINS:
            return f"`{utility}` changes what later words run"
        if any(re.match(r"(?:POSIXLY_CORRECT|SHELLOPTS|BASHOPTS)=", a) for a in [*command.assignments, *command.argv]):
            return "shell mode environment change"
        if utility == "set":
            options = []
            for index, arg in enumerate(args):
                if arg == "--" or not arg.startswith(("-", "+")) or arg in {"-", "+"}:
                    if arg == UNREADABLE:
                        return "computed `set` option"
                    break
                options.append((arg, args[index + 1] if index + 1 < len(args) else None))
            for arg, following in options:
                if arg == UNREADABLE:
                    return "computed `set` option"
                if arg[1:] and "k" in arg[1:] and not arg.startswith("--"):
                    return "`set -k` changes how words become environment"
                if "o" in arg[1:] and following in {"posix", "keyword", UNREADABLE}:
                    return "`set -o` switches shell parsing mode"
        if utility in _SHELLS:
            for index, arg in enumerate(args):
                if arg == "--posix" or (
                    re.fullmatch(r"[-+][A-Za-z]*[oO][A-Za-z]*", arg)
                    and args[index + 1 : index + 2] in (["posix"], ["keyword"], [UNREADABLE])
                ):
                    return "shell started in POSIX or keyword mode"
                if re.fullmatch(r"[-+][A-Za-z]*O[A-Za-z]*", arg):
                    return "shell started with `shopt` options"
                if not arg.startswith(("-", "+")):
                    break
        if utility == "env":
            for name, options in command.scopes:
                if name == "env" and any(re.match(r"(?:POSIXLY_CORRECT|SHELLOPTS|BASHOPTS)=", o) for o in options):
                    return "shell mode environment change"
        if utility in _NAME_WRITERS:
            reason = _name_writer_reason(utility, command)
            if reason:
                return reason
    for root in program.nodes:
        pending = [root]
        while pending:
            node = pending.pop()
            kind = node.type
            if kind == "heredoc_redirect":
                opener = next((c for c in node.named_children if c.type == "heredoc_start"), None)
                if opener is not None and any(q in opener.text for q in (b"'", b'"', b"\\")):
                    continue
            if kind in {"raw_string", "comment"}:
                continue
            if kind == "variable_name" and node.text.decode() in {"BASH_ALIASES", "BASH_CMDS"}:
                return "shell alias or command-hash table reference"
            if kind == "variable_assignment":
                name = node.child_by_field_name("name")
                if name is not None and re.match(rb"(?:POSIXLY_CORRECT|SHELLOPTS|BASHOPTS)\b", name.text):
                    return "shell mode variable write"
            if kind == "declaration_command":
                reason = _declaration_reason(node)
                if reason:
                    return reason
            if kind == "expansion":
                text = node.text.decode()
                if text.startswith("${!") and "=" in text.split("}")[0][3:]:
                    return "indirect assignment through a computed name"
            pending.extend(node.named_children)
        if any(_arithmetic_computed(arithmetic) for arithmetic in _arithmetic_roots(root)):
            return "arithmetic assignment to a computed name"
    return None


def _declaration_reason(node) -> str | None:
    keyword = node.children[0].type if node.children else ""
    args = [c for c in node.named_children if c.type != "comment"]
    options = "".join(a.text.decode()[1:] for a in args if a.type == "word" and a.text.startswith(b"-"))
    for arg in args:
        if arg.type == "word" and arg.text.startswith((b"-", b"+")):
            if literal(arg) is None:
                return f"computed `{keyword}` option"
            continue
        if arg.type == "variable_name":
            if arg.text.decode() in _BINDING_VARIABLES:
                return "shell mode variable write"
            continue
        if arg.type == "variable_assignment":
            name = arg.child_by_field_name("name")
            if name is None or _name_computed(name):
                return f"`{keyword}` assigns a computed name"
            if name.text.decode().split("[")[0] in _BINDING_VARIABLES:
                return "shell mode variable write"
            if "n" in options:
                value = arg.child_by_field_name("value")
                target = literal(value) if value is not None else None
                if target is None or _BINDING_TABLE.fullmatch(target) or target in _BINDING_VARIABLES:
                    return "nameref to a computed or binding name"
            continue
        if _computed_name(arg):
            return f"`{keyword}` assigns a computed name"
        text = literal(arg)
        if text is not None and text.split("=")[0].split("[")[0] in _BINDING_VARIABLES:
            return "shell mode variable write"
    return None


def _name_writer_reason(utility: str, command: _Command) -> str | None:
    """Computed names written by read, mapfile, getopts, printf -v and let."""
    words = command.words[command.start + 1 :]
    args = command.selected[1:]
    if utility == "let":
        return "`let` assigns a computed name" if any(_computed_name(w) for w in words) else None
    if utility == "printf":
        for index, arg in enumerate(args):
            if arg == "-v":
                if index + 1 >= len(args) or args[index + 1] == UNREADABLE:
                    return "`printf -v` assigns a computed name"
                if args[index + 1].split("[")[0] in _BINDING_VARIABLES:
                    return "shell mode variable write"
            if arg == UNREADABLE and index == 0:
                return "computed `printf` option"
            if not arg.startswith("-"):
                break
        return None
    value_options = {"read": {"-a", "-d", "-i", "-n", "-N", "-p", "-t", "-u"}, "getopts": set()}
    value_options["readarray"] = value_options["mapfile"] = {"-d", "-n", "-O", "-s", "-u", "-C", "-c"}
    index = 0
    positional = []
    while index < len(args):
        arg = args[index]
        if arg == UNREADABLE and not positional:
            return f"`{utility}` assigns a computed name"
        if arg == "--":
            positional.extend(args[index + 1 :])
            break
        if arg.startswith("-") and not positional and arg != "-":
            if arg == "-a" and utility == "read" and (index + 1 >= len(args) or args[index + 1] == UNREADABLE):
                return "`read -a` assigns a computed name"
            if arg in value_options[utility]:
                index += 1
            index += 1
            continue
        positional.append(arg)
        index += 1
    names = positional[1:] if utility == "getopts" else positional
    if any(name == UNREADABLE for name in names):
        return f"`{utility}` assigns a computed name"
    if any(name.split("[")[0] in _BINDING_VARIABLES for name in names):
        return "shell mode variable write"
    return None


def unconditional_refusal(command: str) -> str | None:
    """Ruling item 5: a shell-binding change in any command, guarded or not.

    Returns a description, or None. Unreadable syntax returns None here; the
    hook's own engagement gate decides whether a parse failure matters.
    """
    if not BINDING_PREFILTER.search(command):
        return None
    program = _Program()
    try:
        _collect(command, program, _Budget(), 0)
    except ShellParseError:
        return None
    return _binding_reason(program)


BINDING_PREFILTER = re.compile(
    r"alias|hash|enable|shopt|POSIXLY|SHELLOPTS|BASHOPTS|BASH_ALIASES|BASH_CMDS|posix|keyword|"
    r"\bset\b|declare|typeset|local|export|readonly|\bread\b|readarray|mapfile|getopts|printf|\blet\b|"
    r"\$\{!|\(\(|\$\[",
)


# ---------------------------------------------------------------------------
# Per-command accounting (every simple command, regardless of position)
# ---------------------------------------------------------------------------

_EXECUTOR_ENVIRONMENT = {
    b"GIT_SSH_COMMAND",
    b"GIT_PAGER",
    b"GIT_EDITOR",
    b"PAGER",
    b"EDITOR",
    b"GH_PAGER",
    b"BROWSER",
}
_FORWARDING = re.compile(rb'^"?\$(?:\{)?[@*](?:\})?"?$')


def _node_checks(program: _Program, guarded_source: bool, consumer: bool) -> tuple[bool, bool]:
    """Indirect references and executor or repository environments, anywhere.

    Arithmetic, indirect and prompt expansions evaluate a value as code; they
    refuse when this command writes operation text that such a value could hold.
    Returns whether CDPATH or HOME is assigned anywhere in the command.
    """
    cdpath = home = False
    evaluated = consumer and guarded_source and _data_shape(program)
    for root in program.nodes:
        pending = [root]
        while pending:
            node = pending.pop()
            kind = node.type
            if kind in {"raw_string", "comment"}:
                continue
            if kind == "heredoc_redirect":
                opener = next((c for c in node.named_children if c.type == "heredoc_start"), None)
                if consumer and any(
                    child.type not in {"heredoc_start", "heredoc_body", "heredoc_end", "file_descriptor"}
                    for child in node.named_children
                ):
                    raise ShellParseError(
                        "executable node misparsed inside heredoc redirect", reason_class="PARSE_INCOMPLETE"
                    )
                if opener is not None and any(q in opener.text for q in (b"'", b'"', b"\\")):
                    continue
            if guarded_source and kind == "declaration_command" and re.search(rb"(?:^|\s)-[^ ]*n", node.text):
                raise ShellParseError(
                    "indirect variable declaration cannot establish execution", reason_class="INDIRECT_REFERENCE"
                )
            if guarded_source and kind == "unset_command":
                raise ShellParseError(
                    "shell executable binding cannot establish command identity", reason_class="ALIAS_EXECUTION"
                )
            if kind == "variable_assignment":
                name = node.child_by_field_name("name")
                if name is not None:
                    text = name.text
                    if consumer and guarded_source and text in {b"BASH_ENV", b"ENV", b"PATH"}:
                        raise ShellParseError(
                            "command-local executor or repository environment cannot establish context",
                            reason_class="EXECUTOR_OPTION",
                        )
                    value = node.child_by_field_name("value")
                    value_text = literal(value) if value is not None else ""
                    if (
                        guarded_source
                        and text in _EXECUTOR_ENVIRONMENT
                        and (value_text is None or operation_shape(value_text))
                    ):
                        # The value is code; a literal value that spells no operation is visible and inert.
                        raise ShellParseError(
                            "executor environment cannot establish execution", reason_class="EXECUTOR_OPTION"
                        )
                    if guarded_source and text == b"GH_REPO" and node.parent.type != "command":
                        raise ShellParseError(
                            "repository environment mutation cannot establish context",
                            reason_class="UNKNOWN_REPOSITORY",
                        )
                    cdpath |= text == b"CDPATH"
                    home |= text == b"HOME"
            if (
                evaluated
                and kind in {"arithmetic_expansion", "arithmetic_expression", "c_style_for_statement"}
                and re.search(rb"[A-Za-z_$`]", node.text)
            ):
                raise ShellParseError(
                    "arithmetic references cannot establish data-only execution", reason_class="INDIRECT_REFERENCE"
                )
            if (
                evaluated
                and kind == "compound_statement"
                and node.text.startswith(b"((")
                and re.search(rb"[A-Za-z_$`]", node.text[2:-2])
            ):
                raise ShellParseError(
                    "arithmetic references cannot establish data-only execution", reason_class="INDIRECT_REFERENCE"
                )
            if evaluated and kind == "expansion" and (node.text.startswith(b"${!") or b"@P" in node.text):
                raise ShellParseError(
                    "indirect or prompt expansion cannot establish data-only execution",
                    reason_class="INDIRECT_REFERENCE",
                )
            if evaluated and kind == "test_operator":
                if node.text in {b"-v", b"-R"}:
                    raise ShellParseError(
                        "variable test cannot establish data-only execution", reason_class="INDIRECT_REFERENCE"
                    )
                if node.text in {b"-eq", b"-ne", b"-lt", b"-le", b"-gt", b"-ge"}:
                    operands = [node.parent.child_by_field_name(f) for f in ("left", "right")]
                    if any(o is None or not re.fullmatch(r"[+-]?\d+", literal(o) or "") for o in operands):
                        raise ShellParseError(
                            "arithmetic test cannot establish data-only execution", reason_class="INDIRECT_REFERENCE"
                        )
            pending.extend(reversed(node.named_children))
    return cdpath, home


def _data_shape(program: _Program) -> bool:
    """Whether operation text appears as data that a later file reader could execute.

    Git, GH and the typed publisher run their own operation words; shells,
    eval and source are judged as executors. Any other command, or an
    assignment value, that spells an operation is visible data.
    """
    for simple in program.commands:
        if simple.utility in {"git", "gh", "eval", "source", ".", *_SHELLS} or simple.selected[1:3] == [
            "-m",
            "scripts.publish",
        ]:
            continue
        text = simple.node.text.decode() + "\n" + "\n".join(r.text.decode() for r in simple.redirects)
        if operation_shape(text):
            return True
    for root in program.nodes:
        pending = [root]
        while pending:
            node = pending.pop()
            if node.type == "variable_assignment" and node.parent.type != "command":
                value = node.child_by_field_name("value")
                if value is not None and operation_shape(value.text.decode()):
                    return True
            pending.extend(node.named_children)
    return False


def _command_checks(
    command: _Command,
    program: _Program,
    *,
    guarded_source: bool,
    consumer_check,
    foreign,
    allow_dynamic_git_arguments: bool,
) -> None:
    """Refusals that depend only on one simple command and its data sources."""
    argv = command.argv
    if not argv:
        return
    words = command.words
    selected = command.selected
    if any(word.text in _RESERVED_WORDS for word in words):
        raise ShellParseError("reserved word parsed as an argument")
    if argv[0] == UNREADABLE or (selected and selected[0] == UNREADABLE):
        if foreign is not None and foreign(argv[command.start :] if selected else argv):
            return
        if guarded_source and _FORWARDING.match(words[command.start].text if selected else words[0].text):
            raise ShellParseError("forwarded arguments name the executable", reason_class="FORWARDED_ARGUMENTS")
        raise ShellParseError("dynamic command name", reason_class="DYNAMIC_COMMAND")
    if UNREADABLE in argv[: command.start]:
        raise ShellParseError("dynamic wrapper argument", reason_class="DYNAMIC_COMMAND")
    scopes = command.scopes
    if guarded_source and any(
        arg in {"-S", "--split-string"} or arg.startswith(("--split-string=", "-S"))
        for name, options in scopes
        if name == "env"
        for arg in options
    ):
        raise ShellParseError(
            "env split-string execution payload cannot establish argv", reason_class="EXECUTOR_OPTION"
        )
    if guarded_source and any(
        name == "command" and any(re.fullmatch(r"-[pVv]+", option) and "p" in option for option in options)
        for name, options in scopes
    ):
        raise ShellParseError(
            "command default-path resolution cannot establish executable identity", reason_class="DYNAMIC_COMMAND"
        )
    if not selected:
        return
    if guarded_source and utility_executor_options(selected):
        raise ShellParseError("executor option cannot establish execution", reason_class="EXECUTOR_OPTION")
    utility = command.utility
    typed_publisher = bool(re.fullmatch(r"python(?:3(?:\.\d+)?)?", utility)) and selected[1:4] == [
        "-m",
        "scripts.publish",
        "pr-merge",
    ]
    if consumer_check is not None:
        # Keep source attached to its consumer, including redirected stdin and
        # data from the pipeline members to its left. Executed git and gh
        # neighbours pass their output, not their own operation words.
        source = command.node.text.decode() + "\n" + "\n".join(r.text.decode() for r in command.redirects)
        for neighbour in command.left:
            producer = next((c for c in program.commands if neighbour in (c.node, c.node.parent)), None)
            if producer is None or producer.utility not in {"git", "gh"}:
                source += "\n" + neighbour.text.decode()
        consumer_check(selected, source, guarded_source)
    if (
        command.dynamic_redirect
        and consumer_check is not None
        and operation_shape(command.node.text.decode())
        and utility not in {"git", "gh"}
    ):
        raise ShellParseError("redirect cannot establish data-only destination", reason_class="DYNAMIC_REDIRECT")
    if guarded_source and consumer_check is not None:
        for redirect in command.redirects:
            if redirect.type != "file_redirect":
                continue
            destinations = [c for c in redirect.named_children if c.type != "file_descriptor"]
            destination = literal(destinations[0]) if destinations else None
            if destination in {".bashrc", ".git/config", ".config/gh/config.yml"} or (
                destination is not None and ".git/hooks/" in destination
            ):
                raise ShellParseError(
                    "redirect cannot establish data-only destination", reason_class="EXECUTED_REDIRECT"
                )
    if not guarded_source:
        return
    if utility in {"source", "."}:
        operands = selected[1:2]
        if operands in ([], [UNREADABLE], ["/dev/stdin"], ["-"]) or any(
            r.type == "herestring_redirect" for r in command.redirects
        ):
            raise ShellParseError("visible sourced payload cannot establish execution", reason_class="VISIBLE_SOURCE")
        # A sourced script on disk is out of scope unless this command writes operation text.
        if _data_shape(program):
            raise ShellParseError(
                "sourced file may run operation text this command writes", reason_class="EXECUTED_REDIRECT"
            )
    if utility == "make" and _data_shape(program):
        # Same shape as `source`: a makefile runs text this command may write.
        raise ShellParseError("make may run operation text this command writes", reason_class="EXECUTED_REDIRECT")
    if utility == "git" and any(
        arg in {"run", "foreach", "--exec", "-x", "--extcmd", "--upload-pack", "--receive-pack"}
        or arg.startswith(("--exec=", "--extcmd=", "--upload-pack=", "--receive-pack=", "--config-env"))
        for arg in selected[1:]
    ):
        raise ShellParseError("Git executor cannot establish execution", reason_class="EXECUTOR_OPTION")
    if utility in {"git", "gh"} and UNREADABLE in selected:
        if any(_FORWARDING.match(word.text) for word in words[command.start + 1 :]):
            raise ShellParseError("forwarded arguments reach the operation", reason_class="FORWARDED_ARGUMENTS")
        if not (utility == "git" and allow_dynamic_git_arguments):
            operation = selected[1:3]
            if (
                operation[0:1] == [UNREADABLE]
                or (utility == "git" and operation[0:1] in [["checkout"], ["switch"], ["branch"], ["worktree"]])
                or (
                    utility == "gh"
                    and operation[0:1] == ["pr"]
                    and operation[1:2] in [["merge"], ["checkout"], [UNREADABLE]]
                )
            ):
                raise ShellParseError("dynamic operation arguments", reason_class="DYNAMIC_OPERATION")
    if utility in {"declare", "typeset", "unset"}:
        raise ShellParseError(
            "shell executable binding cannot establish command identity", reason_class="ALIAS_EXECUTION"
        )
    if utility == "trap":
        if command.payload_error is not None:
            raise command.payload_error
        if any(
            arg == UNREADABLE or operation_shape(arg) or re.search(r"\b(?:cd|pushd|popd)\b", arg)
            for arg in selected[1:]
        ):
            raise ShellParseError(
                "deferred trap payload cannot establish argv or directory", reason_class="VISIBLE_SOURCE"
            )
    if utility == "xargs":
        # Only fixed logging utilities are inert regardless of stdin.
        operands = selected[1:]
        while operands and operands[0].startswith("-"):
            option, *operands = operands
            if option == "--":
                break
            if option in {"-n", "-L", "-P", "-d", "-E", "-s", "-a"}:
                operands = operands[1:]
            elif option not in {"-t", "-r", "-0", "-x"} and not re.fullmatch(r"-[nLP]\d+", option):
                operands = []
                break
        if not operands or operands[0] not in {"echo", "printf", "/bin/echo", "/usr/bin/printf"}:
            raise ShellParseError(
                "xargs input or argument execution cannot establish argv", reason_class="FORWARDED_ARGUMENTS"
            )
    if (
        (utility in _INDIRECT_EXECUTORS or re.fullmatch(r"python(?:3(?:\.\d+)?)?", utility))
        and not typed_publisher
        and (
            (utility == "find" and any(a in {"-exec", "-execdir", "-ok", "-okdir"} for a in selected))
            or (
                (
                    UNREADABLE in argv
                    or any(
                        c.type == "variable_assignment"
                        and (value := c.child_by_field_name("value")) is not None
                        and literal(value) is None
                        for c in command.node.named_children
                    )
                )
                and _data_shape(program)
            )
        )
    ):
        # A dynamic word or environment can carry operation text this command
        # writes as data into code the reader cannot parse. Literal invocations
        # are judged by the consumer check above and the grammar's position rules.
        raise ShellParseError(
            f"{utility} indirect execution payload cannot establish argv or directory",
            reason_class="UNKNOWN_EXECUTOR",
        )
    if any(
        arg in {"-D", "--chdir", "-i", "--login", "-s", "--shell", "-h", "--host", "-R", "--chroot"}
        or arg.startswith(("--chdir=", "-D", "--host=", "--chroot="))
        for name, options in scopes
        if name == "sudo"
        for arg in options
    ):
        raise ShellParseError("sudo directory option cannot establish repository", reason_class="UNKNOWN_CONTEXT")
    if (
        command.start
        and operation_shape(command.node.text.decode())
        and utility not in {"git", "gh", "eval", "cd", "pushd", "popd", "echo", "printf", "true", "false", *_SHELLS}
        and not typed_publisher
    ):
        raise ShellParseError("unsupported wrapper execution semantics", reason_class="UNKNOWN_EXECUTOR")
    if (utility in _SHELLS or utility == "eval") and command.payload_error is not None:
        if isinstance(command.payload_error, _ScriptFile) and not _data_shape(program):
            return
        raise command.payload_error


# ---------------------------------------------------------------------------
# Grammar admission (ruling items 2, 3 and 4)
# ---------------------------------------------------------------------------

# Ruling item 2: the written grammar, as parse-tree node types. ADMITTED_NODES
# is the whole grammar of the region a guarded operation depends on (every
# top-level item up to and including the last guarded operation): simple
# commands, pipelines and redirections of literal or plain-parameter words. Any
# other node there refuses, whatever the reason checks above concluded.
ADMITTED_NODES = frozenset(
    {
        "command",
        "command_name",
        "comment",
        "concatenation",
        "expansion",
        "file_descriptor",
        "file_redirect",
        "heredoc_body",
        "heredoc_content",
        "heredoc_end",
        "heredoc_redirect",
        "heredoc_start",
        "herestring_redirect",
        "number",
        "pipeline",
        "raw_string",
        "ansi_c_string",
        "redirected_statement",
        "simple_expansion",
        "special_variable_name",
        "string",
        "string_content",
        "translated_string",
        "variable_assignment",
        "variable_name",
        "word",
    }
)
# Every tree-sitter-bash 0.25 kind the reader was written for. A kind outside
# this set (a grammar change) refuses anywhere in the command.
GRAMMAR_NODES = ADMITTED_NODES | {
    "arithmetic_expansion",
    "array",
    "binary_expression",
    "brace_expression",
    "c_style_for_statement",
    "case_item",
    "case_statement",
    "command_substitution",
    "compound_statement",
    "declaration_command",
    "do_group",
    "elif_clause",
    "else_clause",
    "extglob_pattern",
    "for_statement",
    "function_definition",
    "if_statement",
    "list",
    "negated_command",
    "parenthesized_expression",
    "postfix_expression",
    "process_substitution",
    "program",
    "regex",
    "subscript",
    "subshell",
    "ternary_expression",
    "test_command",
    "test_operator",
    "unary_expression",
    "unset_command",
    "variable_assignments",
    "while_statement",
}
_OUTSIDE_REASONS = {
    "function_definition": "ALIAS_EXECUTION",
    "command_substitution": "UNKNOWN_CONTEXT",
    "process_substitution": "UNKNOWN_CONTEXT",
    "arithmetic_expansion": "INDIRECT_REFERENCE",
    "brace_expression": "DYNAMIC_OPERATION",
    "extglob_pattern": "DYNAMIC_OPERATION",
}


def _outside_admitted(node) -> str | None:
    """The first node type in a subtree outside ADMITTED_NODES, or None.

    A quoted heredoc body is data, so its children are not grammar.
    """
    pending = [node]
    while pending:
        current = pending.pop()
        if current.type not in ADMITTED_NODES:
            return current.type
        if current.type == "heredoc_redirect":
            opener = next((c for c in current.named_children if c.type == "heredoc_start"), None)
            if opener is not None and any(q in opener.text for q in (b"'", b'"', b"\\")):
                pending.extend(c for c in current.named_children if c.type != "heredoc_body")
                continue
        pending.extend(current.named_children)
    return None


_BEFORE_BUILTINS = frozenset({"echo", "printf", "true", ":", "test", "[", "pwd"})
# Git subcommands that write no config or remotes. Anything else (including
# aliases, which look like unknown subcommands) refuses before a guarded operation.
_GIT_BEFORE = frozenset(
    {
        "add",
        "annotate",
        "apply",
        "blame",
        "branch",
        "cat-file",
        "check-attr",
        "check-ignore",
        "checkout",
        "cherry",
        "cherry-pick",
        "clean",
        "commit",
        "config",
        "count-objects",
        "describe",
        "diff",
        "diff-files",
        "diff-index",
        "diff-tree",
        "fetch",
        "for-each-ref",
        "format-patch",
        "grep",
        "log",
        "ls-files",
        "ls-remote",
        "ls-tree",
        "merge",
        "merge-base",
        "mv",
        "name-rev",
        "pull",
        "push",
        "range-diff",
        "reflog",
        "remote",
        "reset",
        "restore",
        "rev-list",
        "rev-parse",
        "revert",
        "rm",
        "shortlog",
        "show",
        "show-branch",
        "show-ref",
        "sparse-checkout",
        "stash",
        "status",
        "switch",
        "symbolic-ref",
        "tag",
        "version",
        "worktree",
    }
)
_GIT_CONFIG_READS = {
    "--get",
    "--get-all",
    "--get-regexp",
    "-l",
    "--list",
    "--show-origin",
    "--show-scope",
    "--name-only",
    "--global",
    "--local",
    "--system",
    "--worktree",
    "-z",
    "--null",
}
_GH_READ = {
    ("pr", "view"),
    ("pr", "list"),
    ("pr", "checks"),
    ("pr", "diff"),
    ("pr", "status"),
    ("run", "view"),
    ("run", "list"),
    ("run", "watch"),
    ("issue", "view"),
    ("issue", "list"),
    ("issue", "status"),
    ("repo", "view"),
    ("release", "view"),
    ("release", "list"),
    ("workflow", "view"),
    ("workflow", "list"),
    ("label", "list"),
    ("auth", "status"),
}
_SIMPLE_PARAMETER = re.compile(
    rb"\$(?:[A-Za-z_][A-Za-z_0-9]*|[0-9#?$!*@-]|\{(?:[A-Za-z_][A-Za-z_0-9]*|[0-9#?$!*@-])\})"
)


def _plain_words(command: _Command, *, expansions: bool) -> bool:
    """Words are literal, or (when allowed) plain parameter reads with no operator."""
    for word in [*command.words, *(c for c in command.node.named_children if c.type == "variable_assignment")]:
        pending = [word]
        while pending:
            node = pending.pop()
            if node.type in {"command_substitution", "process_substitution", "arithmetic_expansion"}:
                return False
            if node.type in {"simple_expansion", "expansion"}:
                if not expansions or not _SIMPLE_PARAMETER.fullmatch(node.text):
                    return False
                continue
            pending.extend(node.named_children)
    for redirect in command.redirects:
        if redirect.type == "file_redirect":
            destinations = [c for c in redirect.named_children if c.type != "file_descriptor"]
            if destinations and literal(destinations[0]) is None:
                return False
        if redirect.type == "herestring_redirect" and any(literal(c) is None for c in redirect.named_children):
            return False
    # An unquoted heredoc body that expands anything is not plain.
    return not command.heredoc_words


def _before_reason(command: _Command) -> str | None:
    """Why a command may not run before a guarded operation, or None when admitted."""
    if command.assignments:
        return "UNKNOWN_CONTEXT"
    argv = command.argv
    if command.start or not argv:
        return "UNKNOWN_EXECUTOR"
    utility = argv[0]
    if utility in _DIRECTORY_BUILTINS:
        return "UNKNOWN_CONTEXT"
    if utility in _BEFORE_BUILTINS:
        if utility == "printf" and "-v" in argv[1:]:
            return "INDIRECT_REFERENCE"
        return None if _plain_words(command, expansions=True) else "UNKNOWN_CONTEXT"
    if utility not in {"git", "gh"}:
        return "UNKNOWN_EXECUTOR"
    if not _plain_words(command, expansions=False) or UNREADABLE in argv:
        return "DYNAMIC_OPERATION"
    if utility == "git":
        args = argv[1:]
        while args and args[0].startswith("-"):
            option, *args = args
            if option == "-C" and args:
                args = args[1:]
            elif option.startswith("-C") or option in {"--no-pager", "-P", "--no-optional-locks"}:
                continue
            else:
                return "EXECUTOR_OPTION"
        if not args or args[0] not in _GIT_BEFORE:
            return "ALIAS_EXECUTION"
        verb, rest = args[0], args[1:]
        if verb == "config" and not (rest and all(a in _GIT_CONFIG_READS or not a.startswith("-") for a in rest)):
            return "EXECUTOR_OPTION"
        if verb == "config" and not any(a in {"--get", "--get-all", "--get-regexp", "-l", "--list"} for a in rest):
            return "EXECUTOR_OPTION"
        if verb == "remote" and rest[:1] not in ([], ["-v"], ["--verbose"], ["get-url"], ["show"]):
            return "EXECUTOR_OPTION"
        if verb in {"push", "fetch", "pull"} and any(
            a in {"-u", "--set-upstream"} or (re.fullmatch(r"-[A-Za-z]+", a) and "u" in a and verb == "push")
            for a in rest
        ):
            return "EXECUTOR_OPTION"
        if verb in {"branch", "checkout", "switch", "worktree"} and any(
            a in {"-u", "-t", "--track", "--unset-upstream", "--edit-description", "-m", "-M", "-c", "-C"}
            or a.startswith(("--set-upstream-to", "--track=", "-u"))
            for a in rest
        ):
            return "EXECUTOR_OPTION"
        if verb == "sparse-checkout" and rest[:1] != ["list"]:
            return "EXECUTOR_OPTION"
        if verb == "symbolic-ref" and len([a for a in rest if not a.startswith("-")]) > 1:
            return "EXECUTOR_OPTION"
        if any(a in {"--edit", "-e", "--interactive", "-i", "--patch", "-p", "--ext-diff"} for a in rest) and verb in {
            "commit",
            "add",
            "merge",
            "rebase",
            "tag",
            "stash",
            "reset",
            "restore",
            "checkout",
        }:
            return "EXECUTOR_OPTION"
        return None
    args = argv[1:]
    while args and args[0] in {"-R", "--repo"}:
        args = args[2:]
    while args and args[0].startswith(("--repo=", "-R")):
        args = args[1:]
    if any(a in {"--web", "-w", "--editor", "-e"} for a in args):
        return "EXECUTOR_OPTION"
    if args[:1] == ["api"]:
        rest = args[1:]
        for index, arg in enumerate(rest):
            if arg in {"-X", "--method"} and rest[index + 1 : index + 2] != ["GET"]:
                return "UNKNOWN_CONTEXT"
            if arg.startswith(("--method=", "-X")) and arg not in {"--method=GET", "-XGET", "-X"}:
                return "UNKNOWN_CONTEXT"
            if arg in {"-f", "-F", "--field", "--raw-field", "--input"} or arg.startswith(
                ("--field=", "--raw-field=", "--input=", "-f", "-F")
            ):
                return "UNKNOWN_CONTEXT"
        return None
    if args[:1] == ["search"] or tuple(args[:2]) in _GH_READ:
        return None
    return "UNKNOWN_CONTEXT"


def _leading_cd(items: list[_Item], commands_by_item: dict) -> str | None:
    """The literal target of a leading `cd <literal>`, or None."""
    if not items or items[0].background:
        return None
    members = commands_by_item.get(0, [])
    if len(members) != 1 or members[0].nested or items[0].node.type == "pipeline":
        return None
    command = members[0]
    if command.assignments or command.start or len(command.argv) != 2 or command.argv[0] != "cd":
        return None
    target = command.argv[1]
    if target == UNREADABLE or target.startswith("-") or not target:
        return None
    if not _plain_words(command, expansions=False):
        return None
    return target


def _admit(
    program: _Program,
    triggers: list[_Command],
    *,
    explicit: Callable[[list[str]], bool] | None,
    reason_for_item,
) -> tuple[str | None, set[int]]:
    """Refuse guarded operations outside the grammar; return the leading cd and preceded triggers."""
    for trigger in triggers:
        if trigger.nested or trigger.item is None:
            raise ShellParseError(
                "guarded operation inside a compound construct, substitution or payload",
                reason_class="UNKNOWN_CONTEXT",
            )
    items = program.items
    by_item: dict[int, list[_Command]] = {}
    for command in program.commands:
        if command.item is not None and not command.nested:
            by_item.setdefault(command.item, []).append(command)
    last = max(t.item for t in triggers)
    last_member = max(t.member for t in triggers if t.item == last)
    trigger_ids = {id(t) for t in triggers}
    leading = _leading_cd(items, by_item) if last > 0 else None
    if leading is not None and any(item.connector != "&&" for item in items[1 : last + 1]):
        raise ShellParseError(
            "a leading `cd` must reach the guarded operation through `&&` only", reason_class="UNKNOWN_CONTEXT"
        )
    preceded: set[int] = set()
    seen_before = False
    creation = False
    for index in range(last + 1):
        item = items[index]
        if index == 0 and leading is not None:
            continue
        if item.background:
            raise ShellParseError("background job before or at a guarded operation", reason_class="UNKNOWN_CONTEXT")
        node = item.node
        members = [c for c in node.named_children if c.type != "comment"] if node.type == "pipeline" else [node]
        commands = {c.member: c for c in by_item.get(index, [])}
        for member_index, member in enumerate(members):
            if index == last and member_index > last_member:
                break
            command = commands.get(member_index)
            if command is None or (command.node != member and command.node.parent != member):
                raise ShellParseError(
                    "compound construct before a guarded operation", reason_class=reason_for_item(node, creation)
                )
            if id(command) in trigger_ids:
                if seen_before:
                    preceded.add(id(command))
                if any(name == "coproc" for name, _ in command.scopes):
                    raise ShellParseError("coprocess runs asynchronously", reason_class="UNKNOWN_CONTEXT")
                if not _plain_words(command, expansions=True) and _substitution_reason(command):
                    raise ShellParseError(
                        "substitution runs an unadmitted command before the guarded operation",
                        reason_class=_substitution_reason(command),
                    )
                seen_before = True
                continue
            reason = _before_reason(command)
            if reason is not None:
                if reason == "UNKNOWN_CONTEXT" and creation:
                    reason = "CREATION_COMPOUND"
                raise ShellParseError(f"`{command.utility}` before a guarded operation", reason_class=reason)
            creation |= command.argv[:1] == ["git"] and "worktree" in command.argv and "add" in command.argv
            seen_before = True
    for trigger in triggers:
        if id(trigger) in preceded and explicit is not None and not explicit(trigger.argv):
            raise ShellParseError(
                "a merge after other commands must name the PR, repository and head commit",
                reason_class="UNKNOWN_TARGET",
            )
    # The backstop: whatever the checks above admitted, every node in the
    # region up to the last guarded operation must be in the written grammar.
    for index, item in enumerate(items[: last + 1]):
        heredoc_words = [word for command in by_item.get(index, []) for word in command.heredoc_words]
        outside = next(filter(None, map(_outside_admitted, [item.node, *item.redirects, *heredoc_words])), None)
        if outside is not None:
            raise ShellParseError(
                f"`{outside}` is outside the admitted grammar before a guarded operation",
                reason_class=_OUTSIDE_REASONS.get(outside, "UNKNOWN_CONTEXT"),
            )
    return leading, preceded


def _substitution_reason(command: _Command) -> str | None:
    """Commands in a guarded operation's own words run before it and are not admitted."""
    found = None
    pending = [*command.words, *command.redirects, *command.heredoc_words]
    while pending:
        node = pending.pop()
        if node.type in {"command_substitution", "process_substitution"}:
            return "UNKNOWN_CONTEXT"
        if node.type == "arithmetic_expansion":
            found = found or "INDIRECT_REFERENCE"
        if node.type == "expansion" and not _SIMPLE_PARAMETER.fullmatch(node.text):
            found = found or "DYNAMIC_OPERATION"
        if node.type == "heredoc_redirect":
            opener = next(c for c in node.named_children if c.type == "heredoc_start")
            if any(q in opener.text for q in (b"'", b'"', b"\\")):
                continue
        pending.extend(node.named_children)
    return found


def _compound_reason(node, creation: bool) -> str:
    if node.type == "function_definition":
        return "ALIAS_EXECUTION"
    if node.type in {"declaration_command", "variable_assignment", "variable_assignments", "unset_command"}:
        return "UNKNOWN_CONTEXT"
    return "CREATION_COMPOUND" if creation else "UNKNOWN_CONTEXT"


# ---------------------------------------------------------------------------
# Public reader
# ---------------------------------------------------------------------------


def _strict_operation(argv: list[str]) -> bool:
    selected = argv[invoked_start(argv)[0] :]
    return bool(selected) and Path(selected[0]).name not in _DIRECTORY_BUILTINS


def read_commands(
    command: str,
    cwd: str | None = None,
    *,
    operation: Callable[[list[str]], bool] | None = None,
    consumer_check: Callable[[list[str], str, bool], None] | None = None,
    foreign: Callable[[list[str]], bool] | None = None,
    explicit: Callable[[list[str]], bool] | None = None,
    allow_dynamic_git_arguments: bool = False,
) -> list[Invocation]:
    """Read one command line under the closed grammar; refuse anything else.

    ``operation`` is the calling hook's guarded-operation recognition over
    literal argv (UNREADABLE marks a dynamic word). Without it every command
    except a directory change is treated as guarded, so argv and cwd are proven
    or refused for all of them. ``foreign`` names dynamic-identity shapes another
    hook owns and refuses. ``explicit`` says whether a guarded operation names
    its full target; it is required when anything other than the leading
    ``cd`` runs before it.

    Returns one row per top-level simple command; only guarded rows carry a cwd.
    """
    operation = operation or _strict_operation
    guarded_source = operation_candidate(command) or consumer_check is not None
    budget = _Budget()
    program = _Program()
    _collect(command, program, budget, 0)
    # The command parsed, so a failed span reading is an escape Bash cannot decode
    # either; the engagement gate could not rule out an operation spelled in it.
    if "$'" in command and ansi_c_reading(command) is None:
        raise ShellParseError("ANSI-C span cannot be decoded", reason_class="DECODE_FAILURE")
    binding = _binding_reason(program)
    if binding is not None:
        raise ShellDefinitionError(binding)
    cdpath_assigned, home_assigned = _node_checks(program, guarded_source, consumer_check is not None)
    for simple in program.commands:
        budget.charge()
        _command_checks(
            simple,
            program,
            guarded_source=guarded_source,
            consumer_check=consumer_check,
            foreign=foreign,
            allow_dynamic_git_arguments=allow_dynamic_git_arguments,
        )
    triggers = [
        simple
        for simple in program.commands
        if simple.argv and simple.argv[0] != UNREADABLE and simple.selected and operation(simple.argv)
    ]
    # A dynamic operation word is the more specific reason when the shape also fails.
    dynamic = any(UNREADABLE in t.selected[1:] for t in triggers)
    # Ruling item 3. A definition can rebind any word, so operation text that
    # is data elsewhere may become a guarded operation's argv under it.
    if program.definitions and (triggers or operation_shape(command)):
        if dynamic:
            raise ShellDefinitionError(
                "a shell definition shares a command with dynamic operation arguments", reason_class="DYNAMIC_OPERATION"
            )
        raise ShellDefinitionError()
    leading = None
    if triggers:
        try:
            leading, _preceded = _admit(program, triggers, explicit=explicit, reason_for_item=_compound_reason)
        except ShellParseError as exc:
            if dynamic and exc.reason_class == "UNKNOWN_CONTEXT":
                raise ShellParseError(
                    f"{exc}; operation arguments are dynamic", reason_class="DYNAMIC_OPERATION"
                ) from None
            raise
    # Context: established only now, and only for guarded operations.
    initial = os.getcwd() if cwd is None else cwd
    trigger_ids = {id(t) for t in triggers}
    inherited_repository = any(name in os.environ for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"))
    rows = []
    for simple in program.commands:
        if simple.nested or simple.item is None or not simple.argv:
            continue
        if id(simple) not in trigger_ids:
            rows.append(Invocation(list(simple.argv), None, redirect_unknown=simple.dynamic_redirect))
            continue
        state = initial
        if leading is not None and simple.item >= 1:
            directory_options = {"physical"} & set(os.environ.get("SHELLOPTS", "").split(":")) or {
                "cdable_vars",
                "cdspell",
            } & set(os.environ.get("BASHOPTS", "").split(":"))
            if (
                os.environ.get("CDPATH")
                or cdpath_assigned
                or directory_options
                or (leading.startswith("~") and home_assigned)
            ):
                raise ShellParseError("leading `cd` target depends on shell state", reason_class="UNKNOWN_CONTEXT")
            target = cd_target(["cd", leading], initial)
            if target is None or not Path(target).is_dir():
                raise ShellParseError("leading `cd` target is not a directory", reason_class="UNKNOWN_CONTEXT")
            state = target
        # env -C affects the wrapped utility, never its parent shell.
        for wrapper, options in simple.scopes:
            if wrapper != "env":
                continue
            index = 0
            while index < len(options):
                arg = options[index]
                target = (
                    options[index + 1]
                    if arg in {"-C", "--chdir"} and index + 1 < len(options)
                    else arg.partition("=")[2]
                    if arg.startswith("--chdir=")
                    else arg[2:]
                    if arg.startswith("-C") and len(arg) > 2
                    else None
                )
                if target is not None:
                    state = cd_target(["cd", "-P", target], state)
                index += 2 if arg in _VALUE_OPTIONS["env"] else 1
        environment_repo = None
        for assignment in [*simple.assignments, *simple.argv[: simple.start]]:
            if assignment.startswith("GH_REPO="):
                value = assignment.partition("=")[2]
                try:
                    values = shlex.split(value)
                except ValueError:
                    values = []
                if len(values) != 1 or re.search(r"[$`*?]", value):
                    raise ShellParseError("dynamic repository environment", reason_class="UNKNOWN_REPOSITORY")
                environment_repo = values[0]
        unknown_repository = inherited_repository or any(
            re.match(r"(?:GIT_DIR|GIT_WORK_TREE|GIT_COMMON_DIR)=", arg)
            for arg in [*simple.assignments, *simple.argv[: simple.start]]
        )
        argv = list(simple.argv)
        utility = simple.utility
        if utility in {"git", "gh"}:
            argv[simple.start] = utility
        protected = utility in {"git", "gh"} or "scripts.publish" in simple.selected
        if simple.dynamic_redirect and protected:
            argv.append(UNREADABLE)
        rows.append(
            Invocation(
                argv,
                state,
                guarded=True,
                repository_unknown=unknown_repository,
                redirect_unknown=simple.dynamic_redirect,
                environment_repo=environment_repo,
                context_reason=(
                    "UNKNOWN_REPOSITORY" if unknown_repository else "UNKNOWN_CONTEXT" if state is None else None
                ),
            )
        )
    return rows


def command_argvs(command: str) -> list[list[str]]:
    """Literal argv of every simple command, unpruned and in source order (diagnostics and tests)."""
    program = _Program()
    _collect(command, program, _Budget(), 0)
    return [list(simple.argv) for simple in program.commands if simple.argv]
