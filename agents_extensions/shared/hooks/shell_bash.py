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
from dataclasses import dataclass, replace
from importlib.metadata import version
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
    "xargs",
}
_VALUE_OPTIONS = {
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
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
    },
    "time": {"-f", "--format", "-o", "--output"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-k", "--kill-after", "-s", "--signal"},
    "stdbuf": {"-i", "--input", "-o", "--output", "-e", "--error"},
    "xargs": {
        "-n",
        "--max-args",
        "-L",
        "--max-lines",
        "-I",
        "--replace",
        "-P",
        "--max-procs",
        "-d",
        "--delimiter",
        "-E",
        "--eof",
        "-a",
        "--arg-file",
        "-s",
        "--max-chars",
    },
    "exec": {"-a"},
}
_SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "fish"}


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
        return shlex.split(raw, comments=False)[0] if raw else ""
    except (ValueError, IndexError):
        return None


def invoked_start(argv: list[str]) -> tuple[int, bool]:
    """Skip transparent utility wrappers, including their value options."""
    i, xargs = 0, False
    while i < len(argv):
        name = Path(argv[i]).name
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", argv[i]) or argv[i] in {"!", "{"}:
            i += 1
            continue
        if name not in _WRAPPERS:
            break
        xargs |= name == "xargs"
        i += 1
        while i < len(argv) and argv[i].startswith("-") and argv[i] != "-":
            option = argv[i]
            i += 1
            if option == "--":
                break
            if option in _VALUE_OPTIONS.get(name, set()):
                i += 1
        if name == "timeout":
            i += 1  # duration
    return min(i, len(argv)), xargs


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
    command: str, cwd: str | None = None, *, depth: int = 0, include_payloads: bool = True, diagnostic: bool = False
) -> list[Invocation]:
    """Walk simple commands with conservative sets of Bash working directories."""
    out: list[Invocation] = []
    initial = {os.getcwd() if cwd is None else cwd}
    tainted_bodies = False
    branch_scope_refusal = False
    repo_names = {"GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}
    inherited_repo_override = any(name in os.environ for name in repo_names)
    cdpath_unknown = bool(os.environ.get("CDPATH"))

    def parse(source: str, states: set[str | None], level: int) -> set[str | None]:
        nonlocal branch_scope_refusal, inherited_repo_override, cdpath_unknown
        if level > MAX_DEPTH:
            raise ShellParseError("nested shell depth limit")
        encoded = source.encode()
        tree = Parser(_LANGUAGE).parse(encoded)
        if diagnostic and tree.root_node.has_error and b"``" in encoded:
            # Historical extraction also probes Markdown prose. Normalise
            # doubled code ticks only in this non-admitting diagnostic mode.
            encoded = encoded.replace(b"``", b"`")
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
        # Grammar 0.25 mistakes Bash named descriptors for words, including
        # an ERROR at a prefix descriptor. Repair only AST-identified words
        # immediately glued to a redirect; quoted strings and bodies are untouched.
        edits = []
        pending = [tree.root_node]
        while pending:
            candidate = pending.pop()
            # Retain the branch guard's existing conservative admission policy
            # for case scopes and parameter parentheses; this is not a parser limit.
            if candidate.type == "case_statement" or (
                candidate.type == "expansion" and (b"(" in candidate.text or b")" in candidate.text)
            ):
                branch_scope_refusal = True
            if candidate.type == "variable_assignment":
                name = candidate.child_by_field_name("name")
                if name is not None:
                    inherited_repo_override |= name.text.decode() in repo_names
                    cdpath_unknown |= name.text == b"CDPATH"
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
                edits.append((start, candidate.end_byte))
            else:
                if candidate.type == "heredoc_redirect":
                    opener = next(c for c in candidate.named_children if c.type == "heredoc_start")
                    quoted = any(q in opener.text for q in (b"'", b'"', b"\\"))
                    pending.extend(c for c in candidate.named_children if not quoted or c.type != "heredoc_body")
                else:
                    pending.extend(candidate.named_children)
        if edits:
            for start, end in edits:
                encoded = encoded[:start] + b" " * (end - start - 1) + b"9" + encoded[end:]
            tree = Parser(_LANGUAGE).parse(encoded)
        if tree.root_node.has_error and not diagnostic:
            raise ShellParseError("Bash parse error")
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
                if not diagnostic and not re.fullmatch(
                    rb"(?:[A-Za-z_0-9]+|'[A-Za-z_0-9]+'|\"[A-Za-z_0-9]+\"|\\[A-Za-z_0-9]+)", opener
                ):
                    raise ShellParseError("ambiguous heredoc delimiter")
                body = next((c for c in redirect.named_children if c.type == "heredoc_body"), None)
                if (
                    diagnostic
                    and body is not None
                    and (
                        tainted_bodies
                        or redirect.has_error
                        or not re.fullmatch(
                            rb"(?:[A-Za-z_0-9]+|'[A-Za-z_0-9]+'|\"[A-Za-z_0-9]+\"|\\[A-Za-z_0-9]+)", opener
                        )
                    )
                ):
                    parse(body.text.decode(), set(states), level + 1)
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
            if diagnostic:
                return states
            raise ShellParseError("dynamic command name")
        if not diagnostic and any(word.type == "word" and word.text in {b"{", b"}"} for word in words):
            raise ShellParseError("reserved word parsed as an argument")
        argv = [UNREADABLE if arg is None else arg for arg in argv]
        start, xargs = invoked_start(argv)
        selected = argv[start:]
        if UNREADABLE in argv[:start]:
            raise ShellParseError("dynamic wrapper argument")
        if not selected:
            return states
        if selected[0] == UNREADABLE and not diagnostic:
            raise ShellParseError("dynamic command name")
        utility = Path(selected[0]).name
        if utility in {"git", "gh"}:
            argv[start] = utility
        execution_states = set(states)
        # env -C affects the wrapped utility, never its parent shell.
        if "env" in argv[:start]:
            for i, arg in enumerate(argv[:start]):
                target = (
                    argv[i + 1]
                    if arg in {"-C", "--chdir"} and i + 1 < start
                    else arg.partition("=")[2]
                    if arg.startswith("--chdir=")
                    else arg[2:]
                    if arg.startswith("-C") and len(arg) > 2
                    else None
                )
                if target is not None:
                    execution_states = {cd_target(["cd", "-P", target], state) for state in execution_states}
                if arg in {"-S", "--split-string"} or arg.startswith("--split-string="):
                    raise ShellParseError("dynamic env split-string payload")
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
                )
            )
        if include_payloads and (utility in _SHELLS or utility == "eval"):
            if utility == "eval":
                payload = " ".join(selected[1:])
            else:
                payload = None
                for i, arg in enumerate(selected[1:], 1):
                    if arg.startswith("-") and "c" in arg[1:] and not arg.startswith("--"):
                        payload = selected[i + 1] if i + 1 < len(selected) else UNREADABLE
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
            ):
                return {None}
            # Non-existent literal targets leave PWD untouched. Unknown can succeed anywhere.
            targets = set()
            for state in states:
                target = cd_target(["cd", *selected[1:]], state)
                targets.add(target if target is None or Path(target).is_dir() else state)
            return targets
        return states

    def walk(node, states, level, attached=()):
        nonlocal tainted_bodies
        kind = node.type
        if level > MAX_DEPTH:
            raise ShellParseError("nested shell depth limit")
        if diagnostic and kind == "ERROR" and any(c.type == "heredoc_start" for c in node.named_children):
            # Diagnostic extraction only: unreadable bodies remain visible to
            # legacy detection tests. Enforcement always refuses this parse.
            remainder = node.text.decode().partition("\n")[2]
            previous = tainted_bodies
            tainted_bodies = True
            try:
                return parse(remainder, states, level + 1) if remainder else states
            finally:
                tainted_bodies = previous
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
            for index, child in enumerate(node.named_children):
                walk(child, set(states), level + 1, attached if index == len(node.named_children) - 1 else ())
            return states
        if kind in {"subshell", "command_substitution", "process_substitution", "negated_command"}:
            current = set(states)
            for index, child in enumerate(node.named_children):
                current = walk(child, current, level + 1, attached if index == len(node.named_children) - 1 else ())
            return current if kind == "negated_command" else states
        if kind in {"if_statement", "case_statement", "while_statement", "for_statement", "c_style_for_statement"}:
            possible = set(states)
            for child in node.named_children:
                possible |= walk(child, set(possible), level + 1)
            if kind in {"while_statement", "for_statement", "c_style_for_statement"} and possible != states:
                # An unbounded number of relative directory changes cannot be
                # represented by one traversal; never guess the final repository.
                possible.add(None)
            return possible
        if kind == "function_definition":
            for child in node.named_children:
                walk(child, set(states), level + 1)
            return states
        if kind == "list":
            children = [c for c in node.named_children if c.type != "ERROR"]
            left, right = children[0], children[-1]
            after = walk(left, states, level)
            operator = next((c.type for c in node.children if c.type in {"&&", "||"}), None)
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
