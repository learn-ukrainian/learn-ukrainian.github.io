"""Pinned Bash AST reader for guarded operations (#9484, #9480).

Only callers' raw-text gates engage this reader. It does not execute shell code.
Unknown words retain an explicit marker; unknown directory state is never guessed.
The real-bash oracle must pass before changing either parser dependency.
"""

from __future__ import annotations

import codecs
import os
import re
import shlex
from collections.abc import Callable
from dataclasses import dataclass, replace
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
_STATE_MUTATORS = {"mkdir", "rmdir", "mv", "rm", "ln", "chmod", "install", "set", "shopt"}


class ShellParseError(ValueError):
    """A guarded command cannot be read completely."""


@dataclass(frozen=True)
class Invocation:
    argv: list[str]
    cwd: str | None
    via_xargs: bool = False
    repository_unknown: bool = False
    redirect_unknown: bool = False
    branch_scope_refusal: bool = False
    environment_repo: str | None = None

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
        parts = [literal(child) for child in node.named_children]
        return None if None in parts else "".join(parts)
    if node.type == "ansi_c_string":
        # Unsupported control escapes refuse rather than manufacture shell text.
        if re.search(r"\\[ce]", raw):
            return None
        return codecs.decode(raw[2:-1], "unicode_escape")
    if node.type == "translated_string":
        return literal(node.named_children[0])
    if node.type == "string":
        if any(child.type not in {"string_content"} for child in node.named_children):
            return None
        raw = raw.removeprefix("$")[1:-1]
        return re.sub(r'\\([$`"\\\n])', lambda m: "" if m[1] == "\n" else m[1], raw)
    if node.type == "raw_string":
        return raw[1:-1]
    if node.named_children or re.search(r"(?<!\\)[$`*?\[]", raw):
        return None
    try:
        return shlex.split(raw.replace("\\\n", ""), comments=False)[0] if raw else ""
    except (ValueError, IndexError):
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


def invoked_start(argv: list[str]) -> tuple[int, bool]:
    """Locate a utility through explicit wrapper options; xargs is never a prefix."""
    return wrapper_scopes(argv)[0], False


def operation_candidate(text: str) -> bool:
    """Conservative visible-operation gate for execution payload refusals."""
    try:
        text = re.sub(
            r"\\(x[0-9a-fA-F]{1,2}|u[0-9a-fA-F]{1,4}|U[0-9a-fA-F]{1,8}|[0-7]{1,3})",
            lambda m: chr(int(m[1][1:], 16) if m[1][0] in "xuU" else int(m[1], 8)),
            text,
        )
    except ValueError:
        return True
    text = text.replace("\\\n", "").replace("\\", "").replace("'", "").replace('"', "")
    return any(name in text for name in ("git", "gh", "scripts.publish")) and bool(
        re.search(r"\b(?:checkout|switch|branch|merge)\b", text)
    )


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


def read_commands(
    command: str,
    cwd: str | None = None,
    *,
    depth: int = 0,
    include_payloads: bool = True,
    consumer_check: Callable[[list[str], str, bool], None] | None = None,
    follow_directory_functions: bool = False,
    allow_dynamic_git_arguments: bool = False,
) -> list[Invocation]:
    """Walk simple commands with conservative sets of Bash working directories."""
    out: list[Invocation] = []
    initial = {os.getcwd() if cwd is None else cwd}
    branch_scope_refusal = False
    repo_names = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    inherited_repo_override = any(name in os.environ for name in repo_names)
    cdpath_unknown = bool(os.environ.get("CDPATH"))
    directory_options_unknown = bool(
        {"physical"} & set(os.environ.get("SHELLOPTS", "").split(":"))
        or {"lastpipe", "cdable_vars", "cdspell"} & set(os.environ.get("BASHOPTS", "").split(":"))
    )
    if directory_options_unknown:
        initial = {None}
    # A hook-supplied consumer boundary has already engaged on a candidate,
    # including dynamic operation shapes with no literal git/gh spelling.
    guarded_source = operation_candidate(command) or consumer_check is not None
    functions = {}
    pipeline_sources: list[str] = []
    work = 0

    def charge():
        nonlocal work
        work += 1
        if work > MAX_WORK:
            raise ShellParseError("shell walk work limit")

    def function_sensitive(name, seen=None):
        seen = set() if seen is None else seen
        if name in seen or len(seen) > MAX_DEPTH:
            return True
        seen = seen | {name}
        bodies = functions.get(name, [])
        for body in bodies:
            if operation_candidate(body.text.decode()):
                return True
            pending = [body]
            while pending:
                charge()
                node = pending.pop()
                if node.type == "command_name":
                    called = literal(node)
                    if consumer_check is not None and called not in {
                        "echo",
                        "printf",
                        "true",
                        "false",
                        ":",
                        *functions,
                    }:
                        return True
                    if called is None or called in {
                        "cd",
                        "pushd",
                        "popd",
                        "eval",
                        "source",
                        ".",
                        "trap",
                        "exec",
                        "xargs",
                        "find",
                        *_SHELLS,
                        *_INDIRECT_EXECUTORS,
                        *_WRAPPERS,
                        *_STATE_MUTATORS,
                        "git",
                        "gh",
                    }:
                        return True
                    if called in functions and function_sensitive(called, seen):
                        return True
                pending.extend(node.named_children)
        return False

    def parse(source: str, states: set[str | None], level: int) -> set[str | None]:
        nonlocal branch_scope_refusal, inherited_repo_override, cdpath_unknown, directory_options_unknown
        if level > MAX_DEPTH:
            raise ShellParseError("nested shell depth limit")
        encoded = source.encode()
        tree = Parser(_LANGUAGE).parse(encoded)
        # Grammar 0.25 splits words around line continuations. Repair only
        # gaps between AST words in commands; quoted data and heredocs stay intact.
        pending = [tree.root_node]
        joins = []
        while pending:
            node = pending.pop()
            if node.type == "command":
                children = node.named_children
                for left, right in pairwise(children):
                    if encoded[left.end_byte : right.start_byte] == b"\\\n":
                        joins.append((left.end_byte, right.start_byte))
            pending.extend(node.named_children)
        for begin, end in sorted(joins, reverse=True):
            encoded = encoded[:begin] + encoded[end:]
        if joins:
            tree = Parser(_LANGUAGE).parse(encoded)
        # Grammar 0.25 cannot queue multiple heredocs: its second opener is
        # an ERROR '<' plus a file_redirect. Reparse it as a separate inert
        # reader, preserving each body's expansion and quoting semantics.
        # Shell readers need the final stdin specifically and are refused.
        for _ in range(MAX_DEPTH):
            pending = [tree.root_node]
            queued = None
            while pending:
                candidate = pending.pop()
                if candidate.type == "heredoc_redirect":
                    end = next((c for c in candidate.named_children if c.type == "heredoc_end"), None)
                    extra = next((c for c in candidate.named_children if c.type == "file_redirect"), None)
                    if (
                        end is not None
                        and extra is not None
                        and encoded[extra.start_byte - 1 : extra.start_byte] == b"<"
                    ):
                        opener = b"<" + extra.text
                        if not opener.startswith(b"<<"):
                            continue
                        try:
                            token = shlex.split(opener[3 if opener.startswith(b"<<-") else 2 :].decode())[0].encode()
                        except (ValueError, IndexError):
                            continue
                        body_start = encoded.find(b"\n", end.end_byte) + 1
                        closer = re.search(
                            rb"(?m)^" + (rb"\t*" if opener.startswith(b"<<-") else b"") + re.escape(token) + rb"$",
                            encoded[body_start:],
                        )
                        if body_start and closer:
                            parent = candidate.parent
                            reader = next((c for c in parent.named_children if c.type == "command"), None)
                            if reader is not None:
                                arguments = [
                                    literal(c) or UNREADABLE
                                    for c in reader.named_children
                                    if c.type != "variable_assignment"
                                ]
                                index, _ = invoked_start(arguments)
                                if index < len(arguments) and Path(arguments[index]).name in _SHELLS:
                                    raise ShellParseError("queued shell heredoc payload")
                            queued = (extra.start_byte - 1, extra.end_byte, body_start, opener)
                            break
                pending.extend(candidate.named_children)
            if queued is None:
                break
            begin, end, body_start, opener = queued
            encoded = encoded[:body_start] + b": " + opener + b"\n" + encoded[body_start:]
            encoded = encoded[:begin] + b" " * (end - begin) + encoded[end:]
            tree = Parser(_LANGUAGE).parse(encoded)
        # The external lexer can close <<- on a delimiter PREFIX. Rename
        # only AST-identified openers and their exact physical-line closer.
        # Body bytes, quoting semantics, and executed words are preserved.
        pending = [tree.root_node]
        heredoc_edits = []
        while pending:
            candidate = pending.pop()
            if candidate.type == "heredoc_start":
                start = candidate
                end = next((c for c in start.parent.named_children if c.type == "heredoc_end"), None)
                try:
                    delimiter = shlex.split(start.text.decode(), comments=False)[0].encode()
                except (ValueError, IndexError):
                    continue
                if end is not None:
                    line_end = encoded.find(b"\n", end.end_byte)
                    line_end = len(encoded) if line_end < 0 else line_end
                    if encoded[end.end_byte : line_end] not in {b"", b"\r"}:
                        body_start = encoded.find(b"\n", start.end_byte) + 1
                        strip_tabs = b"<<-" in encoded[start.parent.start_byte : start.start_byte]
                        closer = re.search(
                            rb"(?m)^" + (rb"\t*" if strip_tabs else b"") + re.escape(delimiter) + rb"$",
                            encoded[body_start:],
                        )
                        if closer:
                            position = body_start + closer.end() - len(delimiter)
                            token = f"GUARD_HERE_{start.start_byte}".encode()
                            quoted = any(q in start.text for q in (b"'", b'"', b"\\"))
                            heredoc_edits.extend(
                                [
                                    (start.start_byte, start.end_byte, b"'" + token + b"'" if quoted else token),
                                    (position, position + len(delimiter), token),
                                ]
                            )
            else:
                pending.extend(candidate.named_children)
        for begin, end, replacement in sorted(heredoc_edits, reverse=True):
            encoded = encoded[:begin] + replacement + encoded[end:]
        if heredoc_edits:
            tree = Parser(_LANGUAGE).parse(encoded)
        # Repair AST-identified descriptor and escaped-number lexer errors.
        # Bash treats out-of-range descriptors as argv, whereas zero and
        # leading-zero descriptors are redirects. Quoted strings stay untouched.
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
            # Retain the branch guard's existing conservative admission policy
            # for case scopes and parameter parentheses; this is not a parser limit.
            if candidate.type == "case_statement" or (
                candidate.type == "expansion" and (b"(" in candidate.text or b")" in candidate.text)
            ):
                branch_scope_refusal = True
            if guarded_source and candidate.type == "declaration_command" and re.search(rb"-[^ ]*n", candidate.text):
                raise ShellParseError("indirect variable declaration cannot establish execution")
            if candidate.type == "variable_assignment":
                if guarded_source and candidate.text.startswith((b"BASH_CMDS[", b"BASH_ALIASES[")):
                    raise ShellParseError("shell executable binding cannot establish command identity")
                name = candidate.child_by_field_name("name")
                if name is not None:
                    if (
                        consumer_check is not None
                        and guarded_source
                        and name.text
                        in {
                            b"BASH_ENV",
                            b"ENV",
                            b"PATH",
                        }
                    ):
                        raise ShellParseError(
                            "command-local executor or repository environment cannot establish context"
                        )
                    if guarded_source and name.text in {
                        b"GIT_SSH_COMMAND",
                        b"GIT_PAGER",
                        b"GIT_EDITOR",
                        b"PAGER",
                        b"EDITOR",
                        b"GH_PAGER",
                        b"BROWSER",
                    }:
                        raise ShellParseError("executor environment cannot establish execution")
                    if guarded_source and name.text == b"GH_REPO" and candidate.parent.type != "command":
                        raise ShellParseError("repository environment mutation cannot establish context")
                    if guarded_source and name.text == b"HOME" and candidate.parent.type != "command":
                        directory_options_unknown = True
                    inherited_repo_override |= name.text.decode() in repo_names
                    cdpath_unknown |= name.text == b"CDPATH"
            if (
                consumer_check is not None
                and guarded_source
                and candidate.type
                in {
                    "arithmetic_expansion",
                    "arithmetic_expression",
                    "c_style_for_statement",
                }
                and re.search(rb"[A-Za-z_$`]", candidate.text)
            ):
                raise ShellParseError("arithmetic references cannot establish data-only execution")
            if (
                consumer_check is not None
                and guarded_source
                and candidate.type == "expansion"
                and (candidate.text.startswith(b"${!") or b"@P" in candidate.text)
            ):
                raise ShellParseError("indirect or prompt expansion cannot establish data-only execution")
            if consumer_check is not None and candidate.type == "test_operator":
                if candidate.text in {b"-v", b"-R"}:
                    raise ShellParseError("variable test cannot establish data-only execution")
                if candidate.text in {b"-eq", b"-ne", b"-lt", b"-le", b"-gt", b"-ge"}:
                    operands = [candidate.parent.child_by_field_name(field) for field in ("left", "right")]
                    if any(
                        operand is None or not re.fullmatch(r"[+-]?\d+", literal(operand) or "") for operand in operands
                    ):
                        raise ShellParseError("arithmetic test cannot establish data-only execution")
            if (
                consumer_check is not None
                and candidate.type == "heredoc_redirect"
                and any(
                    child.type not in {"heredoc_start", "heredoc_body", "heredoc_end", "file_descriptor"}
                    for child in candidate.named_children
                )
            ):
                raise ShellParseError("executable node misparsed inside heredoc redirect")
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
            else:
                if candidate.type == "heredoc_redirect":
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
        # Definitions are inert until called. Include all potential definitions
        # conservatively: conditional definitions and nested scopes cannot license
        # a safe call based on source order alone.
        pending = [tree.root_node]
        while pending:
            charge()
            node = pending.pop()
            if node.type == "function_definition":
                name = node.child_by_field_name("name")
                body = node.child_by_field_name("body")
                if name is not None and body is not None:
                    functions.setdefault(name.text.decode(), []).append(body)
            pending.extend(node.named_children)
        return walk(tree.root_node, states, level)

    def substitutions(node, states, level):
        for child in node.named_children:
            if child.type in {"command_substitution", "process_substitution"}:
                raw = child.text.decode()
                if raw.startswith("`"):
                    # Bash removes backslash before $, ` and backslash in old substitutions.
                    body = re.sub(r"\\([$`\\])", r"\1", raw[1:-1])
                    parse(body, set(states), level + 1)
                else:
                    walk(child, set(states), level + 1)
            elif child.type not in {"raw_string", "ansi_c_string"}:
                substitutions(child, states, level)

    def simple(node, redirects, states, level):
        nonlocal directory_options_unknown, inherited_repo_override
        if not states:
            return states
        substitutions(node, states, level)
        words = [
            c
            for c in node.named_children
            if c.type
            in {
                "command_name",
                "word",
                "number",
                "string",
                "raw_string",
                "ansi_c_string",
                "translated_string",
                "concatenation",
                "command_substitution",
                "process_substitution",
                "expansion",
                "simple_expansion",
            }
        ]
        assignments = [c.text.decode() for c in node.named_children if c.type == "variable_assignment"]
        all_redirects = [
            *redirects,
            *(c for c in node.named_children if c.type in {"file_redirect", "heredoc_redirect", "herestring_redirect"}),
        ]
        dynamic_redirect = False
        for redirect in all_redirects:
            substitutions(redirect, states, level)
            if redirect.type == "heredoc_redirect":
                opener = next(c for c in redirect.named_children if c.type == "heredoc_start").text
                if not re.fullmatch(rb"(?:[A-Za-z_0-9]+|'[A-Za-z_0-9]+'|\"[A-Za-z_0-9]+\"|\\[A-Za-z_0-9]+)", opener):
                    raise ShellParseError("ambiguous heredoc delimiter")
                body = next((c for c in redirect.named_children if c.type == "heredoc_body"), None)
                if body is not None and not any(q in opener for q in (b"'", b'"', b"\\")):
                    # Grammar 0.25 omits old-style substitutions in heredoc bodies.
                    for match in re.finditer(r"(?<!\\)`(?:\\.|[^`])*`", body.text.decode()):
                        parse("echo " + match[0], set(states), level + 1)
            if redirect.type == "herestring_redirect":
                dynamic_redirect |= any(literal(c) is None for c in redirect.named_children)
            if redirect.type == "file_redirect":
                descriptor = redirect.child_by_field_name("descriptor")
                if descriptor and descriptor.text.isdigit() and int(descriptor.text) > 2147483647:
                    raise ShellParseError("redirect descriptor exceeds Bash integer range")
                destinations = [c for c in redirect.named_children if c.type != "file_descriptor"]
                if guarded_source and consumer_check is not None and destinations:
                    destination = literal(destinations[0])
                    if destination in {".bashrc", ".git/config", ".config/gh/config.yml"} or (
                        destination is not None and ".git/hooks/" in destination
                    ):
                        raise ShellParseError("redirect cannot establish data-only destination")
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
        argv = [literal(word) for word in words]
        if not argv:
            return states
        if argv[0] is None:
            raise ShellParseError("dynamic command name")
        if any(word.text in _RESERVED_WORDS for word in words):
            raise ShellParseError("reserved word parsed as an argument")
        argv = [UNREADABLE if arg is None else arg for arg in argv]
        start, scopes = wrapper_scopes(argv)
        xargs = False
        selected = argv[start:]
        if UNREADABLE in argv[:start]:
            raise ShellParseError("dynamic wrapper argument")
        if (
            any(name == "env" for name, _ in scopes)
            and any(
                arg in {"-S", "--split-string"} or arg.startswith(("--split-string=", "-S"))
                for name, options in scopes
                if name == "env"
                for arg in options
            )
            and guarded_source
        ):
            raise ShellParseError("env split-string execution payload cannot establish argv")
        if guarded_source and any(
            name == "command" and any(re.fullmatch(r"-[pVv]+", option) and "p" in option for option in options)
            for name, options in scopes
        ):
            raise ShellParseError("command default-path resolution cannot establish executable identity")
        if not selected:
            return states
        if guarded_source and utility_executor_options(selected):
            raise ShellParseError("executor option cannot establish execution")
        if selected[0] == UNREADABLE:
            raise ShellParseError("dynamic command name")
        utility = Path(selected[0]).name
        if consumer_check is not None:
            # Keep source attached to its consumer, including redirected stdin
            # and pipeline input. A heredoc is data only if its reader is known.
            source = node.text.decode() + "\n" + "\n".join(r.text.decode() for r in all_redirects)
            source += "\n" + "\n".join(pipeline_sources)
            consumer_check(selected, source, guarded_source)
        if (
            dynamic_redirect
            and consumer_check is not None
            and operation_candidate(node.text.decode())
            and utility not in {"git", "gh"}
        ):
            raise ShellParseError("redirect cannot establish data-only destination")
        typed_publisher = re.fullmatch(r"python(?:3(?:\.\d+)?)?", utility) and selected[1:4] == [
            "-m",
            "scripts.publish",
            "pr-merge",
        ]
        if guarded_source:
            if utility in {"source", "."}:
                raise ShellParseError("visible sourced payload cannot establish execution")
            if utility == "git" and any(
                arg in {"run", "foreach", "--exec", "-x", "--extcmd", "--upload-pack", "--receive-pack"}
                or arg.startswith(("--exec=", "--extcmd=", "--upload-pack=", "--receive-pack=", "--config-env"))
                for arg in selected[1:]
            ):
                raise ShellParseError("Git executor cannot establish execution")
            if (
                utility in {"git", "gh"}
                and UNREADABLE in selected
                and not (utility == "git" and allow_dynamic_git_arguments)
            ):
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
                    raise ShellParseError("dynamic operation arguments")
            if follow_directory_functions and selected[0] in functions and len(functions[selected[0]]) == 1:
                body = functions[selected[0]][0]
                commands = body.named_children
                if len(commands) == 1 and commands[0].type == "command":
                    args = [literal(c) for c in commands[0].named_children]
                    if len(args) == 2 and args[0] == "cd" and args[1] is not None:
                        return walk(body, states, level + 1)
            if selected[0] in functions and function_sensitive(selected[0]):
                raise ShellParseError("called function has guarded operation or directory effects")
            if utility in {"alias", "hash", "declare", "typeset", "unset", "enable"}:
                raise ShellParseError("shell executable binding cannot establish command identity")
            if utility == "trap" and any(
                arg == UNREADABLE
                or operation_candidate(arg)
                or re.search(r"\b(?:cd|pushd|popd)\b", arg)
                or any(
                    re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", arg) and function_sensitive(name)
                    for name in functions
                )
                for arg in selected[1:]
            ):
                raise ShellParseError("deferred trap payload cannot establish argv or directory")
            if utility == "xargs":
                # Only fixed logging utilities are inert regardless of stdin.
                # Replacement options can rewrite even the executable name.
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
                    raise ShellParseError("xargs input or argument execution cannot establish argv")
            if (
                (utility in _INDIRECT_EXECUTORS or re.fullmatch(r"python(?:3(?:\.\d+)?)?", utility))
                and not typed_publisher
                and (utility != "find" or any(a in {"-exec", "-execdir", "-ok", "-okdir"} for a in selected))
            ):
                raise ShellParseError(f"{utility} indirect execution payload cannot establish argv or directory")
            if any(
                arg in {"-D", "--chdir", "-i", "--login", "-s", "--shell", "-h", "--host", "-R", "--chroot"}
                or arg.startswith(("--chdir=", "-D", "--host=", "--chroot="))
                for name, options in scopes
                if name == "sudo"
                for arg in options
            ):
                raise ShellParseError("sudo directory option cannot establish repository")
            if utility in {"set", "shopt"}:
                # physical cd, lastpipe, cdable_vars and cdspell change state;
                # shell option mutations are not transparent.
                directory_options_unknown = True
                return {None}
            if utility in {"mkdir", "rmdir", "mv", "rm", "ln", "chmod", "install"} or (
                utility == "mktemp"
                and any(
                    arg == UNREADABLE or arg.startswith("--directory") or re.fullmatch(r"-[^-]*d[^-]*", arg)
                    for arg in selected[1:]
                )
            ):
                # Filesystem changes invalidate earlier existence/access probes,
                # including explicit absolute Git/env directories.
                inherited_repo_override = True
                return {None}
        if (
            guarded_source
            and start
            and operation_candidate(node.text.decode())
            and utility
            not in {
                "git",
                "gh",
                "eval",
                "cd",
                "pushd",
                "popd",
                "echo",
                "printf",
                "true",
                "false",
                *_SHELLS,
            }
            and not typed_publisher
        ):
            raise ShellParseError("unsupported wrapper execution semantics")
        if utility in {"git", "gh"}:
            argv[start] = utility
        # Multiple possible locations cannot license judging only whichever
        # set element happens to be visited first. Refuse the unresolved target.
        execution_states = set(states) if not guarded_source or len(states) == 1 else {None}
        # env -C affects the wrapped utility, never its parent shell.
        for wrapper, options in scopes:
            if wrapper != "env":
                continue
            i = 0
            while i < len(options):
                arg = options[i]
                target = (
                    options[i + 1]
                    if arg in {"-C", "--chdir"} and i + 1 < len(options)
                    else arg.partition("=")[2]
                    if arg.startswith("--chdir=")
                    else arg[2:]
                    if arg.startswith("-C") and len(arg) > 2
                    else None
                )
                if target is not None:
                    execution_states = {cd_target(["cd", "-P", target], state) for state in execution_states}
                i += 2 if arg in _VALUE_OPTIONS["env"] else 1
        environment_repo = None
        for assignment in [*assignments, *argv[:start]]:
            if assignment.startswith("GH_REPO="):
                value = assignment.partition("=")[2]
                try:
                    values = shlex.split(value)
                except ValueError:
                    values = []
                if len(values) != 1 or re.search(r"[$`*?]", value):
                    raise ShellParseError("dynamic repository environment")
                environment_repo = values[0]
        if environment_repo is not None and utility in _SHELLS:
            raise ShellParseError("nested shell repository environment cannot establish context")
        unknown_repo = any(
            re.match(r"(?:GIT_DIR|GIT_WORK_TREE|GIT_COMMON_DIR)=", arg) for arg in [*assignments, *argv[:start]]
        )
        protected_utility = utility in {"git", "gh"} or "scripts.publish" in selected
        if dynamic_redirect and protected_utility:
            selected = [*selected, UNREADABLE]
        for state in execution_states:
            out.append(
                Invocation(
                    [*argv, *([UNREADABLE] if dynamic_redirect and protected_utility else [])],
                    state,
                    xargs,
                    unknown_repo,
                    dynamic_redirect,
                    environment_repo=environment_repo,
                )
            )
        if include_payloads and (utility in _SHELLS or utility == "eval"):
            if utility == "eval":
                payload = " ".join(selected[1:])
            else:
                payload = None
                for i, arg in enumerate(selected[1:], 1):
                    if arg.startswith(("-", "+")) and "c" in arg[1:] and not arg.startswith("--"):
                        # Bash accepts either sign for command options.
                        # Each packed -o/-O consumes an option name before the
                        # command string. Refuse rather than judge that name
                        # as code and silently miss the executable payload.
                        if "o" in arg[1:] or "O" in arg[1:]:
                            raise ShellParseError("packed shell -c with -o/-O cannot establish execution payload")
                        payload = selected[i + 1] if i + 1 < len(selected) else UNREADABLE
                        # Shells keep processing options after -c, including --
                        # and -o/-O/+o/+O with values. Do not parse an option as
                        # code and silently lose the actual guarded payload.
                        if payload.startswith(("-", "+")):
                            raise ShellParseError("shell options after -c cannot establish execution payload")
                        break
                if payload is None:
                    bodies = [
                        r.child_by_field_name("body")
                        or next((c for c in r.named_children if c.type == "heredoc_body"), None)
                        for r in all_redirects
                        if r.type == "heredoc_redirect"
                    ]
                    payload = "\n".join(b.text.decode() for b in bodies if b is not None) if bodies else None
                    if payload is None:
                        here_strings = [r for r in all_redirects if r.type == "herestring_redirect"]
                        if here_strings:
                            payload = literal(here_strings[-1].named_children[-1]) or UNREADABLE
            if payload is None and guarded_source:
                raise ShellParseError("opaque shell input cannot establish execution payload")
            if utility in _SHELLS and any(re.fullmatch(r"[-+][a-zA-Z]*[PoO][a-zA-Z]*", a) for a in selected[1:]):
                directory_options_unknown = True
                execution_states = {None}
            if payload is not None:
                if UNREADABLE in payload:
                    raise ShellParseError("dynamic shell payload")
                after_payload = parse(payload, execution_states, level + 1)
                if utility == "eval" and start == 0:
                    return after_payload
        if utility in {"cd", "pushd", "popd"}:
            if utility == "pushd" and "-n" in selected[1:]:
                return states
            if (
                (start and any(Path(arg).name not in {"command", "builtin", "--"} for arg in argv[:start]))
                or (
                    utility == "pushd"
                    and (len(selected) == 1 or any(re.fullmatch(r"[+-][0-9]+", a) for a in selected[1:]))
                )
                or utility == "popd"
                or any(a.startswith("CDPATH=") for a in assignments)
                or cdpath_unknown
                or directory_options_unknown
            ):
                return {None}
            # Non-existent literal targets leave PWD untouched. Unknown can succeed anywhere.
            targets = set()
            for state in states:
                cd_args = ["cd", *selected[1:]]
                home = next(
                    (a for a in node.named_children if a.type == "variable_assignment" and a.text.startswith(b"HOME=")),
                    None,
                )
                if home is not None and len(cd_args) == 1:
                    value = home.child_by_field_name("value")
                    target_home = literal(value) if value is not None else None
                    if target_home is None and value is not None:
                        raw = value.text.decode().strip('"')
                        match = re.fullmatch(r"\$([A-Za-z_][A-Za-z_0-9]*)(/[^$`\s\"']*)?", raw)
                        # Read only a simple inherited parameter whose binding
                        # the submitted shell program does not replace.
                        if match and not re.search(r"\b" + re.escape(match[1]) + r"=", command):
                            inherited = os.environ.get(match[1])
                            if inherited is not None:
                                target_home = inherited + (match[2] or "")
                    cd_args = ["cd", target_home or UNREADABLE]
                target = cd_target(cd_args, state)
                targets.add(target if target is None or Path(target).is_dir() else state)
            # Redirection can fail before cd runs. Keep its failure state for
            # sequential execution; && also remains conservative.
            holder = node.parent if node.parent and node.parent.type == "redirected_statement" else node
            parent = holder.parent
            success_only = (
                parent is not None
                and parent.type == "list"
                and parent.named_children[0] == holder
                and any(c.type == "&&" for c in parent.children)
            )
            return targets | states if all_redirects and not success_only else targets
        return states

    def walk(node, states, level, attached=()):
        charge()
        kind = node.type
        if level > MAX_DEPTH:
            raise ShellParseError("nested shell depth limit")
        if kind == "unset_command" and guarded_source and states:
            raise ShellParseError("shell executable binding cannot establish command identity")
        if kind == "command":
            return simple(node, list(attached), states, level)
        if kind == "redirected_statement":
            body = node.child_by_field_name("body")
            redirects = [*attached, *(c for c in node.named_children if c != body)]
            if body and body.type == "command":
                return simple(body, redirects, states, level)
            if body and body.type == "list" and any(r.type == "heredoc_redirect" for r in redirects):
                before_count = len(out)
                after = walk(body, states, level, redirects)
                possible = states | after | {row.cwd for row in out[before_count:]}
                for redirect in redirects:
                    substitutions(redirect, possible, level)
                return after
            return walk(body, states, level, redirects) if body else states
        if kind == "pipeline":
            if guarded_source:
                pending = list(node.named_children)
                while pending:
                    charge()
                    child = pending.pop()
                    if child.type == "command":
                        name = child.child_by_field_name("name")
                        if name is not None and literal(name) is not None:
                            args = [
                                literal(c) or UNREADABLE
                                for c in child.named_children
                                if c.type not in {"variable_assignment", "file_redirect"}
                            ]
                            start, _ = invoked_start(args)
                            selected = args[start:]
                            # A -c payload is independent of pipe input; every
                            # other shell reader can execute bytes on stdin.
                            if (
                                selected
                                and Path(selected[0]).name in _SHELLS
                                and not any(re.fullmatch(r"-[^-]*c[^-]*", a) for a in selected[1:])
                            ):
                                raise ShellParseError("piped shell input cannot establish execution payload")
                    pending.extend(child.named_children)
            pipeline_sources.append(node.text.decode())
            try:
                for index, child in enumerate(node.named_children):
                    walk(child, set(states), level + 1, attached if index == len(node.named_children) - 1 else ())
            finally:
                pipeline_sources.pop()
            return states
        if kind in {"subshell", "command_substitution", "process_substitution", "negated_command"}:
            current = set(states)
            for index, child in enumerate(node.named_children):
                current = walk(child, current, level + 1, attached if index == len(node.named_children) - 1 else ())
            return current if kind == "negated_command" else states
        if kind == "while_statement" and node.text.lstrip().startswith(b"while "):
            condition = node.child_by_field_name("condition")
            if condition is not None and condition.text.strip(b" ;\n") == b"false":
                return states
        if kind in {"if_statement", "case_statement", "while_statement", "for_statement", "c_style_for_statement"}:
            possible = set(states)
            if kind in {"while_statement", "for_statement", "c_style_for_statement"}:
                # Later iterations can start in any directory reached by a
                # previous body. Refuse unknown state before judging the body.
                pending = list(node.named_children)
                while pending:
                    charge()
                    child = pending.pop()
                    if child.type == "command_name" and literal(child) in {"cd", "pushd", "popd"}:
                        possible.add(None)
                    pending.extend(child.named_children)
            for child in node.named_children:
                possible |= walk(child, set(possible), level + 1)
            if kind in {"while_statement", "for_statement", "c_style_for_statement"} and possible != states:
                # An unbounded number of relative directory changes cannot be
                # represented by one traversal; never guess the final repository.
                possible.add(None)
            return possible
        if kind == "function_definition":
            return states
        if kind == "list":
            children = [c for c in node.named_children if c.type != "ERROR"]
            left, right = children[0], children[-1]
            after = walk(left, states, level)
            operator = next((c.type for c in node.children if c.type in {"&&", "||"}), None)
            if operator == "||" and right.text.strip() == b"exit" and left.type == "command":
                args = [literal(c) for c in left.named_children]
                if args and args[0] == "cd" and None not in args:
                    targets = {cd_target(args, state) for state in states}
                    return {target for target in targets if target is None or Path(target).is_dir()}
            return walk(right, after if operator == "&&" else after | states, level, attached)
        if kind in {"variable_assignment", "string", "heredoc_body", "word", "concatenation"}:
            substitutions(node, states, level)
            return states
        current = set(states)
        for child in node.named_children:
            # Asynchronous lists do not export their cd to the following command.
            following = node.children[node.children.index(child) + 1 :]
            background = bool(following and following[0].type == "&")
            changed = walk(child, set(current), level)
            if not background:
                current = changed
        return current

    parse(command, initial, depth)
    return [
        replace(
            row,
            branch_scope_refusal=branch_scope_refusal,
            repository_unknown=row.repository_unknown or inherited_repo_override,
        )
        for row in out
    ]
