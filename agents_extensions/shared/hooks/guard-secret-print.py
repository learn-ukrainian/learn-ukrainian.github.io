#!/usr/bin/env python3
"""PreToolUse guard - block clear secret-value dumps (#M-5 / #1908).

Reads the Claude Code hook payload on stdin (JSON with `tool_input.command`) and
exits 2 (block) when a Bash command would print known secret values into the
transcript. Exit 0 (allow) otherwise.

This guard is deliberately narrow. It catches high-confidence dump shapes only:

  - environment and declaration dumps, named `printenv`, and unsafe filters
  - inline interpreter environment access and environment pseudo-file reads
  - expanding here-documents and here-strings
  - redirected environment dumps displayed later in the same command
  - commands reading sensitive file operands, except value-free checks
  - `grep` / `rg` / `ugrep` reading dotenv-style secret files without a
    key-only/count transform
  - `echo` / `printf` expanding known secret environment variables
  - `scripts.session_supervisor worker-env` environment views, including the
    explicit `--all` form

Quote-aware tokenization keeps dangerous-looking strings inside a quoted commit
message from becoming false positives. This is defense-in-depth, not a sandbox.
"""

# Known limits
# A string-matching guard cannot be complete. It does not resolve aliases,
# functions that shadow safe commands, external scripts or file lists, computed
# paths, or arbitrary programs. Interpreter aliases and dynamically assembled
# environment accesses are not modeled. Values loaded by `source .env` or
# `. .env` and printed through other variable names remain a data-flow limit.
# Captured dumps are tracked within one invocation, not across separate events.
# Variable-name tracking covers configured names and suffixes, and their copies.
# Nested script inputs retain literal expansion syntax rather than evaluating
# Bash expansions, and script-word joining is conservative about adjacency.
# Explicit override and value-free transform policies remain trusted boundaries.
# Interpreter identifier mentions are default-denied, including os.environ[k].
# Import aliases (import os as o), getattr(os, "environ") and
# __import__("os").environ do not bypass literal identifier checks; dynamically
# constructing those attribute names with string concatenation still can.
# Command aliases, functions shadowing commands, external script files, computed
# paths and interpreter aliases such as renamed binaries remain limits.
# ENVIRONMENT_API_INVENTORY covers the documented whole-environment APIs the
# authors enumerated for each listed language as of 2026-10-11, with the limits
# above and below. Aliasing global environment objects before reading them is a
# known limit, for example `const p = process; p.env` and `const {env} = process`.
# This class includes object aliasing and destructuring of the global environment
# object, including assignment destructuring and Deno/Bun destructuring.
# Literal `import {env} from "process"` has a row.
# Generic process launchers that inherit the environment are another known
# limit, including asyncio.create_subprocess_exec/shell, pty.spawn,
# os.posix_spawn* and subprocess calls of arbitrary programs. Rows for dumpers
# named literally in command text remain enforced.
# Python/Lua getenv require a name; invalid no-name calls deny conservatively.
# Node binding is undocumented; getBuiltinModule('os') alone does not dump the
# environment. Both are conservative namespace denials required by this policy.
# nt.environ, Go and Rust are out of scope, including FFI. Existing compatibility
# denials do not imply support for those runtimes.
# Stopping rule: a missing identifier blocks only when it is a documented
# standard-library API of a listed language returning the whole environment or
# a report containing it in one call, writable in command text without aliasing
# or launching another program, and absent from the table. All else is Consider.
# grep -c TOKEN .env and cp .env backup remain conservative denials even though
# those operations do not print values.

from __future__ import annotations

import codecs
import json
import os
import re
import shlex
import sys

# Use the sibling helper in either the source tree or a deployed hook copy.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Don't write __pycache__ next to deployed hooks (#9108).
sys.dont_write_bytecode = True
try:
    from shell_shlex import (
        ShellPreprocessLimit,
        preprocess_shell_command,
        skippable_heredoc_delimiters,
        split_operator_run,
        split_quote_preserving,
        strip_skippable_heredoc_bodies,
    )
    from shell_shlex import (
        _quote_after as shell_quote_after,
    )
except ImportError as exc:
    print(f"guard dependency unavailable: shell_shlex ({exc})", file=sys.stderr)
    raise SystemExit(2) from exc

SEPARATORS = {"&&", "||", ";", "&", "\n"}
DISPLAY_FILE_COMMANDS = {"cat", "bat", "less", "head", "tail"}
# Language, documented API family, detector kind, spelling after normalization.
# identifier rows deny mentions except approved literal lookups; literal rows
# reuse the shell command rules on program strings, never lowercase bare env.
ENVIRONMENT_API_INVENTORY = (
    # Python: os.environ, including mapping views/copies (docs.python.org/3/library/os.html).
    ("python", "os.environ", "identifier", r"(?i:os(?:\.environ|\[environ\])|environ)"),
    # Python: os.environb is the complete bytes mapping, not an environ prefix.
    ("python", "os.environb", "identifier", r"(?i:os(?:\.environb|\[environb\])|environb)"),
    # Python: os.getenv requires a name; aliases retain the getenv identifier.
    ("python", "os.getenv", "identifier", r"(?i:os\.getenv|getenv)"),
    # Python: os.getenvb requires a bytes name.
    ("python", "os.getenvb", "identifier", r"(?i:os\.getenvb|getenvb)"),
    # Python: posix.environ (docs.python.org/3/library/posix.html), inherited bytes mapping.
    ("python", "posix.environ", "identifier", r"(?i:posix\.environ)"),
    # Python: os.popen/system/exec*/spawn*, subprocess run/Popen/call/check_*/get*output.
    (
        "python",
        "os/subprocess child dumpers",
        "literal",
        r"(?:popen|Popen|system|exec\w*|spawn\w*|run|call|check_call|check_output|getoutput|getstatusoutput)\(",
    ),
    # Node: process.env, dot/bracket access (nodejs.org/api/process.html).
    ("node", "process.env", "identifier", r"(?i:process(?:\.env|\[env\]))"),
    # Node: require('node:process').env/report and static import/destructuring of env.
    (
        "node",
        "process module env/report",
        "identifier",
        r"(?:require|import)\((?:node:)?process\)(?:\.(?:env|report)|\[(?:env|report)\])",
    ),
    # Node: importing the complete env object transfers the mapping, so deny aliases.
    (
        "node",
        "process module env imports",
        "identifier",
        r"(?:import|const|let|var)\x00?\{[^}]*\benv\b[^}]*\}(?:=\x00?require\((?:node:)?process\)|\x00?from\x00?(?:node:)?process)",
    ),
    # Node: process.report contains environmentVariables, even through a report alias.
    ("node", "process.report", "identifier", r"(?i:process(?:\.report|\[report\]))"),
    # Node: report.getReport includes environment values unless explicitly excluded.
    ("node", "report.getReport", "identifier", r"(?i:getreport)"),
    # Node: report.writeReport writes that report, possibly to a visible descriptor.
    ("node", "report.writeReport", "identifier", r"(?i:writereport)"),
    # Node: process.binding is an undocumented internal namespace, conservatively denied.
    ("node", "process.binding", "identifier", r"(?i:process(?:\.binding|\[binding\]))"),
    # Node: process.getBuiltinModule loads built-ins, conservatively denied as a namespace.
    ("node", "process.getBuiltinModule", "identifier", r"(?i:process(?:\.getbuiltinmodule|\[getbuiltinmodule\]))"),
    # Node: child_process exec/execFile/spawn/fork and synchronous variants inherit env.
    ("node", "child_process dumpers", "literal", r"(?:exec|execFile|spawn|fork)(?:Sync)?\("),
    # Deno: env.toObject/get (docs.deno.com/api/deno/~/Deno.Env).
    ("deno", "Deno.env", "identifier", r"(?i:deno(?:\.env|\[env\]))"),
    # Deno: Command and legacy run can execute literal environment dumpers.
    ("deno", "Deno.Command/run dumpers", "literal", r"(?:Command|run)\("),
    # Bun: Bun.env, process.env and import.meta.env (bun.sh/docs/runtime/environment-variables).
    ("bun", "Bun.env/import.meta.env", "identifier", r"(?i:(?:bun|import\.meta)(?:\.env|\.?\[env\]))"),
    # Bun: spawn/spawnSync and the shell $ tagged template inherit env.
    ("bun", "Bun.spawn/shell dumpers", "literal", r"spawn(?:Sync)?\(|\$`"),
    # Ruby: ENV and every ENV method such as to_h/to_a/each (docs.ruby-lang.org/en/master/ENV.html).
    ("ruby", "ENV", "identifier", r"ENV"),
    # Ruby: Kernel system/exec/spawn/backticks, IO.popen and Open3 capture*/popen*/pipeline*.
    ("ruby", "Kernel/IO/Open3 dumpers", "literal", r"(?:system|exec|spawn|popen|capture\w*|popen\w*|pipeline\w*)\("),
    # Ruby: %x command literals (docs.ruby-lang.org/en/master/syntax/literals_rdoc.html).
    (
        "ruby",
        "%x command literals",
        "command_literal",
        r"%x\s*(?:\((?P<paren>[^)]*)\)|\{(?P<brace>[^}]*)\}|\[(?P<bracket>[^]]*)\]|<(?P<angle>[^>]*)>|(?P<delimiter>[^\w\s])(?P<value>.*?)(?P=delimiter))",
    ),
    # Perl: %ENV, qualified hashes and $ENV{NAME} (perldoc.perl.org/variables/%25ENV).
    ("perl", "%ENV/$ENV", "identifier", r"(?i:%(?:main::|::)?env|\$(?:main::|::)?env)"),
    # Perl: Env imports or ties the environment (perldoc.perl.org/Env).
    ("perl", "Env module", "identifier", r"(?:use|require)(?:\x00|\()Env|tie\x00?\(?%[^;]*,\x00?Env"),
    # Perl: system/exec/readpipe/backticks/open pipes (perldoc.perl.org/perlfunc).
    ("perl", "Perl child dumpers", "literal", r"(?:system|exec|readpipe|open)\("),
    # Perl: qx command literals (perldoc.perl.org/perlop, Quote-Like Operators).
    (
        "perl",
        "qx command literals",
        "command_literal",
        r"qx\s*(?:\((?P<paren>[^)]*)\)|\{(?P<brace>[^}]*)\}|\[(?P<bracket>[^]]*)\]|<(?P<angle>[^>]*)>|(?P<delimiter>[^\w\s])(?P<value>.*?)(?P=delimiter))",
    ),
    # PHP: $_ENV (php.net/manual/en/reserved.variables.environment.php).
    ("php", "$_ENV", "identifier", r"(?i:\$_env)"),
    # PHP: $_SERVER (php.net/manual/en/reserved.variables.server.php), includes CLI env.
    ("php", "$_SERVER", "identifier", r"(?i:\$_server)"),
    # PHP: getenv() returns the whole env (php.net/manual/en/function.getenv.php).
    ("php", "getenv", "identifier", r"(?i:getenv)"),
    # PHP: filter_input_array reads complete input mappings; related calls without
    # literal keys deny conservatively (php.net/manual/en/function.filter-input-array.php).
    (
        "php",
        "filter input environment/server",
        "identifier",
        r"(?i:filter_(?:input_array|var_array|input)\(INPUT_(?:SERVER|ENV))",
    ),
    # PHP: apache_getenv is a named Apache subprocess-env lookup, never a bulk API.
    ("php", "apache_getenv", "identifier", r"(?i:apache_getenv)"),
    # PHP: phpinfo/INFO_ENVIRONMENT (php.net/manual/en/function.phpinfo.php).
    ("php", "phpinfo", "identifier", r"(?i:phpinfo)"),
    # PHP: get_defined_vars may include loaded superglobals in the current scope.
    ("php", "get_defined_vars", "identifier", r"(?i:get_defined_vars)"),
    # PHP: $GLOBALS includes superglobals (php.net/manual/en/reserved.variables.globals.php).
    ("php", "$GLOBALS", "identifier", r"(?i:\$globals)"),
    # PHP: exec/system/passthru/shell_exec/popen/proc_open/backticks inherit env.
    ("php", "PHP child dumpers", "literal", r"(?:exec|system|passthru|shell_exec|popen|proc_open)\("),
    # Lua: os.getenv(name) only; no standard bulk accessor (lua.org/manual/5.4/manual.html).
    ("lua", "os.getenv", "identifier", r"(?i:os\.getenv|getenv)"),
    # Lua: os.execute/io.popen may run environment dumpers.
    ("lua", "os.execute/io.popen dumpers", "literal", r"(?:execute|popen)\("),
    # Lua: long bracket strings in child commands (lua.org/manual/5.4/manual.html#3.1).
    ("lua", "long bracket child literals", "command_literal", r"\[(?P<equals>=*)\[(?P<value>.*?)\](?P=equals)\]"),
    # Awk: ENVIRON mapping (GNU gawk manual, Auto-set Variables).
    ("awk", "ENVIRON", "identifier", r"ENVIRON"),
    # Shell: printenv [NAME] (GNU coreutils manual, printenv invocation).
    ("shell", "printenv", "command", "printenv"),
    # Shell: env without a utility (GNU coreutils manual, env invocation).
    ("shell", "env", "command", "env"),
    # Shell: set without arguments (GNU Bash manual, Bourne Shell Builtins).
    ("shell", "set", "command", "set"),
    # Shell: export -p (GNU Bash manual, Bourne Shell Builtins).
    ("shell", "export -p", "command", "export"),
    # Shell: declare -p (GNU Bash manual, Bash Builtins).
    ("shell", "declare -p", "command", "declare"),
    # Shell: typeset -p, synonym of declare (GNU Bash manual, Bash Builtins).
    ("shell", "typeset -p", "command", "typeset"),
    # Shell: compgen -e/-A export enumerates names only; conservative inventory denial.
    ("shell", "compgen -e/-A export", "command", "compgen"),
    # Shell/Linux: strings or any reader of /proc/*/environ uses the sensitive-file rule.
    ("shell", "/proc/*/environ", "file", "/proc/*/environ"),
    # Rust: std::env is reserved as a language-object identifier; execution is not modeled.
    ("rust", "std::env", "identifier", r"std::env"),
    # Go: os.Environ/syscall.Environ and os/exec (pkg.go.dev/os); go run is out of scope.
    ("go", "os.Environ/syscall.Environ/os/exec", "out_of_scope", "go run"),
    # Compatibility: previously denied identifier aliases, including foreign runtimes.
    ("compatibility", "getenvironment/printenv/os.env", "identifier", r"(?i:getenvironment|printenv|os\.env)"),
)
ENV_DUMP_COMMANDS = {spelling for _, _, kind, spelling in ENVIRONMENT_API_INVENTORY if kind == "command"}
GREP_COMMANDS = {"grep", "rg", "ugrep"}
SHELL_COMMANDS = {"bash", "sh", "zsh", "dash", "ksh", "eval", "source", "."}
NON_PRINTING_COMMANDS = {"test", "[", "stat", "ls", "true", "false", ":"}
SAFE_DOTENV_SUFFIXES = (".example", ".sample", ".template", ".dist")
KNOWN_SECRET_VARS = {
    "ANTHROPIC_API_KEY",
    "DAGGER_CLOUD_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
}
WORKER_ENV_MODULE = "scripts.session_supervisor"
WORKER_ENV_COMMAND = "worker-env"

_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*\Z")
_VAR_REF_RE = re.compile(
    r"(?<!\\)\$(?:\{!(?P<indirect>[A-Za-z_][A-Za-z0-9_]*)\}|"
    r"\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)(?::[-=?+][^}]*)?\}|"
    r"(?P<plain>[A-Za-z_][A-Za-z0-9_]*))"
)


def _read_payload() -> dict | None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (ValueError, RecursionError):
        return None
    return payload if isinstance(payload, dict) else None


def _command(payload: dict) -> str:
    return (payload.get("tool_input") or {}).get("command") or ""


def _strip_shell_comments(command: str) -> str:
    """Remove Bash comments at word boundaries, retaining each newline.

    Keep hashes inside words, quotes, command substitutions, and backticks for
    the existing tokenizer. Heredoc bodies are removed before this is called
    on the complete command.
    """
    out: list[str] = []
    quote = ""
    in_backticks = False
    substitution_depth = 0
    substitution_outer_quote = ""
    word_start = True
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            out.append(command[i : i + 2])
            if command[i + 1] != "\n":
                word_start = False
            i += 2
            continue
        if char == "'" and quote != '"' and not in_backticks:
            quote = "" if quote == "'" else "'"
            word_start = False
        elif char == '"' and quote != "'" and not in_backticks:
            quote = "" if quote == '"' else '"'
            word_start = False
        elif char == "`" and quote != "'":
            in_backticks = not in_backticks
            word_start = False
        elif quote != "'" and not in_backticks and command.startswith("$(", i):
            if not substitution_depth:
                substitution_outer_quote = quote
                quote = ""
            substitution_depth += 1
            out.append("$(")
            word_start = False
            i += 2
            continue
        elif substitution_depth and not quote and not in_backticks and char == "(":
            substitution_depth += 1
        elif substitution_depth and not quote and not in_backticks and char == ")":
            substitution_depth -= 1
            if not substitution_depth:
                quote = substitution_outer_quote
        elif not quote and not in_backticks and not substitution_depth:
            if char == "#" and word_start:
                end = command.find("\n", i)
                if end < 0:
                    break
                i = end
                continue
            # Bash blanks are ASCII; keep # after redirects as a filename for the guard.
            word_start = char in " \t\n;&|()"
        out.append(char)
        i += 1
    return "".join(out)


def _collapse_shell_line_continuations(command: str) -> str:
    """Remove Bash's escaped newlines before splitting command statements."""
    out: list[str] = []
    single = False
    double = False
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and not single and index + 1 < len(command):
            following = command[index + 1]
            if following != "\n":
                out.extend((char, following))
            index += 2
            continue
        if char == "'" and not double:
            single = not single
        elif char == '"' and not single:
            double = not double
        out.append(char)
        index += 1
    return "".join(out)


def _separate_program_flag_quotes(command: str) -> str:
    """Give shlex's non-POSIX lexer a word boundary before attached scripts."""
    out = []
    quote = ""
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and quote != "'":
            out.append(command[index : index + 2])
            index += 2
            continue
        if not quote and (index == 0 or command[index - 1] in " \t\n;|&("):
            # Options are opaque here; quote handling must not depend on the
            # interpreter's option letters or their position in a cluster.
            flag = re.match(r"(-{1,2}[A-Za-z][A-Za-z0-9_-]*=?)(?=[\"'])", command[index:])
            if flag:
                out.append(flag[0].rstrip("=") + " ")
                index += flag.end()
                continue
        if quote == char and index + 1 < len(command) and command[index + 1] == char:
            # Adjacent fragments of the same shell quote are one word. Preserve
            # their join before the non-POSIX lexer can invent an argv boundary.
            index += 2
            continue
        if char in {"'", '"'} and (not quote or quote == char):
            quote = "" if quote else char
        out.append(char)
        index += 1
    return "".join(out)


def _tokenize(command: str) -> list[str]:
    try:
        executable = _decode_ansi_c_quotes(preprocess_shell_command(command))
        protected, parameters = _protect_parameters(_separate_program_flag_quotes(executable))
        tokens = split_quote_preserving(protected, punctuation_chars="();&|<>\n", whitespace=" \t")
        restored = [_restore_parameters(token, parameters) for token in tokens]
        # shlex can combine an arithmetic close and newline as one punctuation
        # run (`))\n`). The newline still starts a new executable command.
        return [
            part
            for token in restored
            for part in (
                re.findall(r"[^\n]+|\n", token) if "\n" in token and set(token) <= set("();&|<>\n") else [token]
            )
        ]
    except ValueError:
        return ["__UNDECIDABLE_SECRET_COMMAND__"]


def _protect_parameters(command: str) -> tuple[str, dict[str, str]]:
    """Keep complete Bash ${...} words intact while shlex splits operators."""
    substitutions = {start: end for start, end, _ in _substitution_spans(command)}
    parameters: dict[str, str] = {}
    out: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            out.append(command[i : i + 2])
            i += 2
            continue
        if char == "'" and quote != '"':
            quote = "" if quote else "'"
        elif char == '"' and quote != "'":
            quote = "" if quote else '"'
        if quote != "'" and command.startswith("${", i):
            depth = 1
            inner_quote = ""
            end = i + 2
            while end < len(command) and depth:
                current = command[end]
                if current == "\\" and inner_quote != "'":
                    end += 2
                    continue
                if current == "'" and inner_quote != '"':
                    inner_quote = "" if inner_quote else "'"
                elif current == '"' and inner_quote != "'":
                    inner_quote = "" if inner_quote else '"'
                elif inner_quote != "'" and end in substitutions:
                    end = substitutions[end]
                    continue
                elif not inner_quote and command.startswith("${", end):
                    depth += 1
                    end += 2
                    continue
                elif not inner_quote and current == "}":
                    depth -= 1
                end += 1
            if not depth:
                marker = f"\ue000{len(parameters)}\ue001"
                while marker in command:
                    marker += "\ue002"
                parameters[marker] = command[i:end]
                out.append(marker)
                i = end
                continue
        out.append(char)
        i += 1
    return "".join(out), parameters


def _restore_parameters(token: str, parameters: dict[str, str]) -> str:
    for marker, value in parameters.items():
        token = token.replace(marker, value)
    return token


def _strip_quotes(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token


def _decode_ansi_c_quotes(command: str) -> str:
    """Turn Bash ANSI-C words into shell-quoted decoded words before parsing."""
    out: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        char = command[i]
        if char == "\\" and quote != "'" and i + 1 < len(command):
            out.append(command[i : i + 2])
            i += 2
            continue
        if not quote and command.startswith("$'", i):
            end = i + 2
            while end < len(command):
                if command[end] == "\\":
                    end += 2
                elif command[end] == "'":
                    break
                else:
                    end += 1
            if end < len(command):
                try:
                    value = codecs.decode(command[i + 2 : end], "unicode_escape")
                except UnicodeError:
                    value = command[i + 2 : end]
                out.append(shlex.quote(value))
                i = end + 1
                continue
        if char in {"'", '"'}:
            quote = "" if quote == char else quote if quote else char
        out.append(char)
        i += 1
    return "".join(out)


def _is_single_quoted(token: str) -> bool:
    return len(token) >= 2 and token[0] == token[-1] == "'"


def _is_assignment(token: str) -> bool:
    return bool(_ASSIGNMENT_RE.match(_strip_quotes(token)))


def _heredoc_delimiters(line: str) -> list[tuple[str, bool, bool]] | None:
    """Keep only the shared parser's unambiguous here-doc delimiters."""
    return skippable_heredoc_delimiters(line)


def _strip_heredoc_bodies(command: str) -> str:
    return strip_skippable_heredoc_bodies(
        command, opener_transform=_strip_shell_comments, body_substitutions=_substitution_fragments
    )


def _substitution_fragments(line: str) -> list[str]:
    """Keep only executable substitutions from an unquoted heredoc line."""
    return [line[start:end] for start, end, _ in _substitution_spans(line, heredoc=True)]


def _is_command_brace(token: str, segment: list[str]) -> bool:
    """Bash treats a separate brace as syntax only at command position."""
    if token not in {"{", "}"}:
        return False
    if not segment:
        return True
    if token == "}":
        return False
    if len(segment) == 1 and segment[0] in {"then", "else", "do", "!"}:
        return True
    if len(segment) == 2:
        name, suffix = segment
        return bool(
            (suffix == "()" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))
            or (name == "function" and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", suffix))
        )
    return bool(
        len(segment) == 3
        and segment[0] == "function"
        and segment[2] == "()"
        and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", segment[1])
    )


def _pipelines(command: str) -> list[list[list[str]]]:
    """Return command pipelines, split quote-aware on pipes and separators."""
    # shlex groups adjacent punctuation into runs such as `);`. Split those
    # before segmenting, or a command after a substitution can be hidden.
    tokens = [part for token in _tokenize(command) for part in split_operator_run(token)]
    pipelines: list[list[list[str]]] = []
    pipeline: list[list[str]] = []
    segment: list[str] = []

    def flush_segment() -> None:
        nonlocal segment
        if segment:
            pipeline.append(segment)
            segment = []

    def flush_pipeline() -> None:
        nonlocal pipeline
        flush_segment()
        if pipeline:
            pipelines.append(pipeline)
            pipeline = []

    for token in tokens:
        if token in {"|", "|&"}:
            flush_segment()
        elif token in SEPARATORS or token in {"(", ")", ";;"} or _is_command_brace(token, segment):
            flush_pipeline()
        else:
            segment.append(token)
    flush_pipeline()
    return pipelines


def _command_at(seg: list[str]) -> tuple[str, list[str], int] | None:
    """Return `(command, raw_args, index)` after simple wrappers/assignments."""
    i = 0
    # A function body's first command shares its segment with the definition
    # opener; later body commands are split at semicolons as usual.
    if len(seg) >= 3 and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\(\)", seg[0]) and seg[1] == "{":
        i = 2
    elif len(seg) >= 4 and seg[0] == "function" and seg[2] == "{":
        i = 3
    reserved = {
        "{",
        "}",
        "(",
        ")",
        "if",
        "then",
        "elif",
        "else",
        "fi",
        "while",
        "until",
        "for",
        "select",
        "do",
        "done",
        "case",
        "in",
        "esac",
        "!",
    }
    while i < len(seg) and _strip_quotes(seg[i]) in reserved:
        i += 1
    while i < len(seg):
        while i < len(seg) and _is_assignment(seg[i]):
            i += 1
        if i >= len(seg):
            return None
        wrapper = _strip_quotes(seg[i]).rsplit("/", 1)[-1]
        if wrapper in {"sudo", "time", "nohup", "exec", "builtin", "command"}:
            i += 1
            if wrapper == "command":
                while i < len(seg) and _strip_quotes(seg[i]) in {"-p", "--"}:
                    i += 1
            continue
        if wrapper in {"nice", "timeout", "stdbuf"}:
            i += 1
            if wrapper == "nice":
                if i < len(seg) and _strip_quotes(seg[i]) == "-n":
                    i += 2
                elif i < len(seg) and re.fullmatch(r"-\d+", _strip_quotes(seg[i])):
                    i += 1
            elif wrapper == "timeout":
                while i < len(seg) and _strip_quotes(seg[i]).startswith("-"):
                    i += 2 if _strip_quotes(seg[i]) in {"-s", "--signal", "-k", "--kill-after"} else 1
                i += 1  # duration
            else:
                while i < len(seg) and re.fullmatch(r"-[ioe](?:\d+)?", _strip_quotes(seg[i])):
                    i += 1
            continue
        if wrapper == "env":
            j = i + 1
            while j < len(seg):
                token = _strip_quotes(seg[j])
                if _redirection_skip_count(token) or token.isdigit():
                    return "env", seg[i + 1 :], i
                if _is_assignment(seg[j]):
                    j += 1
                elif token in {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"} and j + 1 < len(seg):
                    j += 2
                elif (
                    token.startswith(("--unset=", "--chdir=", "--split-string="))
                    or token in {"-i", "-0", "--ignore-environment", "--null"}
                    or token.startswith("-")
                ):
                    j += 1
                else:
                    break
            if j >= len(seg):
                return "env", seg[i + 1 :], i
            i = j
            continue
        break
    if i >= len(seg):
        return None

    cmd = _strip_quotes(seg[i]).rsplit("/", 1)[-1]
    if cmd == "busybox" and i + 1 < len(seg) and _strip_quotes(seg[i + 1]) == "sh":
        return "sh", seg[i + 2 :], i + 1
    return cmd, seg[i + 1 :], i


def _has_override(seg: list[str]) -> bool:
    """True when this command segment opts out with LEARN_UK_SECRETS_OK=1."""
    for token in seg:
        clean = _strip_quotes(token)
        if clean in {"sudo", "time", "nohup", "command"}:
            continue
        if clean == "env":
            continue
        if clean == "LEARN_UK_SECRETS_OK=1":
            return True
        if _is_assignment(clean):
            continue
        return False
    return False


def _is_secret_var_name(name: str) -> bool:
    upper = name.upper()
    return (
        upper in KNOWN_SECRET_VARS
        or upper.endswith("_TOKEN")
        or upper.endswith("_API_KEY")
        or upper.endswith("_PAT")
        or upper.endswith("_SECRET")
    )


def _expanded_secret_var(arg: str, copied: set[str] | None = None, named: dict[str, str] | None = None) -> str | None:
    if _is_single_quoted(arg):
        return None
    # Check each dollar position: an outer default such as ${x:-${GH_TOKEN}}
    # otherwise consumes the inner reference before finditer can see it.
    for index, char in enumerate(arg):
        if char != "$":
            continue
        match = _VAR_REF_RE.match(arg, index)
        if match is None:
            continue
        indirect = match.group("indirect")
        if indirect:
            target = (named or {}).get(indirect, "")
            if _is_secret_var_name(target) or target in (copied or ()):
                return target
            continue
        name = match.group("braced") or match.group("plain") or ""
        if _is_secret_var_name(name) or name in (copied or ()):
            return name
    return None


def _path_name(path: str) -> str:
    clean = _strip_quotes(path).rstrip("/")
    if not clean:
        return ""
    return clean.rsplit("/", 1)[-1].lower()


def _is_dotenv_secret_file(path: str) -> bool:
    clean = _strip_quotes(path).lower()
    name = _path_name(clean)
    return (
        clean in {"~/.bash_secrets"}
        or name in {".env", ".envrc", ".bash_secrets"}
        or name.endswith(".env")
        or (name.startswith(".env.") and not name.endswith(SAFE_DOTENV_SUFFIXES))
    )


def _is_known_secret_file(path: str) -> bool:
    clean = _strip_quotes(path).lower()
    if not clean or clean == "-":
        return False
    name = _path_name(clean)
    if clean in {"~/.aws/credentials", "$home/.aws/credentials", "${home}/.aws/credentials", "~/.bash_secrets"}:
        return True
    if clean.endswith("/.aws/credentials"):
        return True
    if name in {".env", ".envrc", ".bash_secrets", "id_rsa"}:
        return True
    if name.endswith(".env") or name.endswith(".pem"):
        return True
    return name.startswith(".env.") and not name.endswith(SAFE_DOTENV_SUFFIXES)


def _cut_is_key_only(args: list[str]) -> bool:
    fields_one = False
    delimiter_equals = False
    i = 0
    while i < len(args):
        token = _strip_quotes(args[i])
        if token in {"-f", "--fields"} and i + 1 < len(args):
            fields_one = _strip_quotes(args[i + 1]) == "1"
            i += 2
            continue
        if token.startswith("-f"):
            fields_one = token[2:] == "1"
        if token.startswith("--fields="):
            fields_one = token.split("=", 1)[1] == "1"
        if token in {"-d", "--delimiter"} and i + 1 < len(args):
            delimiter_equals = _strip_quotes(args[i + 1]) == "="
            i += 2
            continue
        if token == "-d=" or token == "--delimiter==":
            delimiter_equals = True
        if token.startswith("--delimiter="):
            delimiter_equals = token.split("=", 1)[1] == "="
        i += 1
    return fields_one and delimiter_equals


def _has_short_flag(args: list[str], flag: str) -> bool:
    for arg in args:
        token = _strip_quotes(arg)
        if token == f"-{flag}":
            return True
        if token.startswith("-") and not token.startswith("--") and flag in token[1:]:
            return True
    return False


def _grep_is_key_only(args: list[str]) -> bool:
    """Accept only anchored patterns that cannot consume an equals or value."""
    if not (_has_short_flag(args, "o") or "--only-matching" in args):
        return False
    if _has_short_flag(args, "v") or "--invert-match" in args:
        return False
    clean = [_strip_quotes(arg) for arg in args]
    patterns = []
    index = 0
    while index < len(clean):
        token = clean[index]
        if token in {"-e", "--regexp"} and index + 1 < len(clean):
            patterns.append(clean[index + 1])
            index += 2
            continue
        if token.startswith("--regexp="):
            patterns.append(token.split("=", 1)[1])
        elif token.startswith("-e") and len(token) > 2:
            patterns.append(token[2:])
        elif token.startswith("-"):
            if token in {"-f", "--file"} or token.startswith(("--file=", "-f")):
                return False
        elif not patterns:
            patterns.append(token)
        index += 1
    return bool(patterns) and all(pattern in {"^[^=]*", "^[^=]+", "^[A-Za-z_][A-Za-z0-9_]*"} for pattern in patterns)


def _is_safe_transform(seg: list[str]) -> bool:
    command = _command_at(seg)
    if command is None:
        return False
    cmd, args, _idx = command
    clean = [_strip_quotes(arg) for arg in args]
    if cmd == "cut":
        return _cut_is_key_only(args)
    if cmd == "jq":
        programs = [arg for arg in clean if not arg.startswith("-")]
        return len(programs) == 1 and re.sub(r"\s+", "", programs[0]) in {
            "keys",
            "keys_unsorted",
            "to_entries|map(.key)",
            "[to_entries[]|.key]",
        }
    if cmd == "wc":
        return clean in [["-l"], ["--lines"]]
    if cmd in GREP_COMMANDS:
        return _grep_is_key_only(args)
    if cmd == "sed":
        return clean in [["s/=.*//"], ["s/=.*$//"], ["-e", "s/=.*//"], ["-e", "s/=.*$//"]]
    if cmd == "awk":
        return len(clean) == 2 and clean[0] == "-F=" and re.sub(r"\s+", "", clean[1]) == "{print$1}"
    return False


def _has_safe_downstream(pipeline: list[list[str]], seg_index: int) -> bool:
    # A later transform cannot undo a value already copied by tee or xargs.
    return len(pipeline) > seg_index + 1 and _is_safe_transform(pipeline[seg_index + 1])


def _without_redirects(args: list[str]) -> list[str]:
    result = []
    index = 0
    while index < len(args):
        skip = _redirection_skip_count(_strip_quotes(args[index]))
        if skip:
            if result and result[-1].isdigit():
                result.pop()
            index += skip
        else:
            result.append(_strip_quotes(args[index]))
            index += 1
    return result


def _stdout_target(args: list[str]) -> str | None:
    target = None
    for index, token in enumerate(args[:-1]):
        if token in {">", ">>", ">|", "&>", "&>>"}:
            if index and args[index - 1].isdigit() and args[index - 1] != "1":
                continue
            target = _strip_quotes(args[index + 1])
    return target


def _env_source_reason(segment: list[str]) -> str | None:
    command = _command_at(segment)
    if command is None:
        return None
    cmd, raw_args, _idx = command
    if cmd not in ENV_DUMP_COMMANDS:
        return None
    args = _without_redirects(raw_args)
    if cmd == "compgen":
        if not _has_short_flag(args, "e") and not any(
            args[index : index + 2] == ["-A", "export"] for index in range(len(args))
        ):
            return None
    elif cmd == "printenv":
        names = [arg for arg in args if not arg.startswith("-")]
        if names and not any(_is_secret_var_name(name) for name in names):
            return None
    elif cmd == "set" and args:
        return None
    elif cmd in {"declare", "export", "typeset"}:
        if _has_short_flag(args, "f") and not _has_short_flag(args, "p"):
            return None
        names = [arg for arg in args if not arg.startswith("-")]
        if names and not _has_short_flag(args, "p"):
            return None
        if names and not any(_is_secret_var_name(name) for name in names):
            return None
    return f"`{cmd}` would print shell environment values"


def _env_dump_reason(
    pipeline: list[list[str]], dumped_files: set[str], substitutions: dict[str, tuple[str, str]]
) -> str | None:
    for index, segment in enumerate(pipeline):
        reason = _env_source_reason(segment)
        if not reason or _has_override(segment):
            continue
        found = _command_at(segment)
        target = _stdout_target(found[1]) if found else None
        # Process substitutions are output consumers, not capture filenames.
        sinks = [substitutions[arg][1] for arg in segment if arg in substitutions and substitutions[arg][0] == ">("]
        if sinks:
            if not all(_output_sink_safe(sink) for sink in sinks):
                return reason
            if target in substitutions:
                continue
        if not target:
            if _has_safe_downstream(pipeline, index):
                continue
            return reason
        visible = target in {"/dev/stdout", "/dev/stderr", "/dev/tty"} or bool(
            target and re.fullmatch(r"/(?:dev/fd|proc/(?:self|\$\$|[0-9]+)/fd)/[0-9]+", target)
        )
        if target and not visible:
            if target != "/dev/null":
                dumped_files.add(os.path.normpath(target))
            continue
        return reason
    return None


_PROGRAM_STRINGS = re.compile(
    r"(?i:(?<!\w)(?:rb|br|rf|fr|f|r|u|b))?"
    r"(?P<quote>\"\"\"|'''|\"|'|`)(?P<value>.*?)(?P=quote)",
    re.DOTALL,
)
_ENV_IDENTIFIERS = re.compile(
    "(?:"
    + "|".join(spelling for _, _, kind, spelling in ENVIRONMENT_API_INVENTORY if kind == "identifier")
    + r")(?![\w$])"
)
_KEYED_ENV = re.compile(
    r"(?:(?:os(?:\.environb?|\[environb?\])|posix\.environ)"
    r"(?:\[(?P<py_index>\w+)\]|\.get\((?P<py_get>\w+)\))|"
    r"os\.getenvb?\((?P<py_env>\w+)\)|"
    r"(?:process|Bun|import\.meta|require\((?:node:)?process\))(?:\.env|\[env\])"
    r"(?:\.(?P<js_property>[A-Za-z_$][\w$]*)|\[(?P<js_index>\w+)\])|"
    r"Deno(?:\.env|\[env\])\.get\((?P<deno_key>\w+)\)|"
    r"ENV(?:\[(?P<rb_index>:?\w+)\]|\.fetch\((?P<rb_fetch>:?\w+)\))|"
    r"\$(?:main::|::)?ENV\{(?P<perl_key>\w+)\}|"
    r"\$_(?:ENV|SERVER)\[(?P<php_key>\w+)\]|"
    r"(?:getenv|apache_getenv)\((?P<php_get>\w+)\)|"
    r"filter_input\(INPUT_(?:SERVER|ENV),\x00?(?P<php_filter>\w+)\)|"
    r"ENVIRON\[(?P<awk_key>\w+)\])(?![\w$]|\(|\.\()"
)
_CHILD_PROCESS_APIS = tuple(
    (language, re.compile(r"(?<![\w$])(?:" + spelling + ")"))
    for language, _, kind, spelling in ENVIRONMENT_API_INVENTORY
    if kind == "literal"
)
_CHILD_COMMAND_LITERALS = tuple(
    (language, re.compile(spelling, re.DOTALL))
    for language, _, kind, spelling in ENVIRONMENT_API_INVENTORY
    if kind == "command_literal"
)


def _normalize_program(program: str) -> tuple[str, list[bool], set[int], set[int]]:
    """Compact spelling while retaining literal keys and whitespace boundaries."""
    program = program.replace("\\\n", "").replace("?.", ".")
    pieces: list[tuple[str, bool, bool]] = []
    cursor = 0
    for match in _PROGRAM_STRINGS.finditer(program):
        pieces.append((program[cursor : match.start()], False, False))
        pieces.append((match["value"], True, match["quote"] == "`"))
        cursor = match.end()
    pieces.append((program[cursor:], False, False))
    text: list[str] = []
    literals: list[bool] = []
    boundaries: set[int] = set()
    templates: set[int] = set()
    pending_space = False
    for piece, literal, template in pieces:
        if template:
            templates.add(len(text))
        for char in piece:
            if char.isspace():
                boundaries.add(len(text))
                pending_space = True
            elif char not in "\"'`":
                # Retain a barrier between distinct words, but still compact
                # member syntax and adjacent quoted fragments such as "HO" "ME".
                if (
                    pending_space
                    and text
                    and text[-1] not in ".:[{("
                    and (char.isalnum() or char in "_$")
                    and not (literal and literals[-1])
                ):
                    text.append("\0")
                    literals.append(False)
                pending_space = False
                text.append(char)
                literals.append(literal)
    return "".join(text), literals, boundaries, templates


def _is_interpreter_command(cmd: str) -> bool:
    return cmd.startswith("python") or cmd in {
        "node",
        "nodejs",
        "perl",
        "ruby",
        "php",
        "lua",
        "deno",
        "bun",
        "awk",
        "gawk",
        "mawk",
        "nawk",
    }


def _program_reason(cmd: str, program: str) -> str | None:
    if not _is_interpreter_command(cmd):
        return None
    text, literals, boundaries, templates = _normalize_program(program)
    # Literal dumpers count in child-process calls or shell-executing backticks,
    # not in printed text, paths or ordinary flag values. Ruby/Perl also accept
    # unparenthesized process calls, so inspect their original word boundaries.
    runtime = "python" if cmd.startswith("python") else "node" if cmd == "nodejs" else cmd
    child_call = (
        any(
            pattern.search(text)
            for language, pattern in _CHILD_PROCESS_APIS
            if language == runtime or (runtime in {"bun", "deno"} and language == "node")
        )
        or (cmd in {"ruby", "perl"} and re.search(r"\b(?:system|exec|spawn|open|readpipe)\s+", program))
        or (cmd == "bun" and re.search(r"\$\s*`", program))
    )
    for literal in _PROGRAM_STRINGS.finditer(program):
        executes = child_call or (literal["quote"] == "`" and cmd in {"ruby", "perl", "php"})
        if executes and any(
            _env_source_reason(segment) for pipeline in _pipelines(literal["value"]) for segment in pipeline
        ):
            return "inline program contains a literal environment dumper"
    for language, pattern in _CHILD_COMMAND_LITERALS:
        if cmd != language or (language == "lua" and not child_call):
            continue
        for literal in pattern.finditer(program):
            body = next(
                value
                for key, value in literal.groupdict().items()
                if key not in {"delimiter", "equals"} and value is not None
            )
            if any(_env_source_reason(segment) for pipeline in _pipelines(body) for segment in pipeline):
                return "inline program contains a literal environment dumper"
    cursor = 0
    for mention in _ENV_IDENTIFIERS.finditer(text):
        start, end = mention.span()
        if start < cursor:
            continue
        if start and start not in boundaries and (text[start - 1].isalnum() or text[start - 1] in "_$"):
            continue
        if end < len(text) and end not in boundaries and (text[end].isalnum() or text[end] in "_$"):
            continue
        access = _KEYED_ENV.match(text, start)
        if access and access.end() not in templates:
            kind, name = next((kind, name) for kind, name in access.groupdict().items() if name is not None)
            if kind in {"php_key", "php_get", "php_filter"} and cmd != "php":
                return "inline program lookup does not belong to this runtime"
            key_start, key_end = access.span(kind)
            literal = kind in {"js_property", "perl_key"} or name.startswith(":") or all(literals[key_start:key_end])
            if literal and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name.lstrip(":")):
                if _is_secret_var_name(name.lstrip(":")):
                    return "inline program can expose a secret environment value"
                cursor = access.end()
                continue
        return "inline program mentions an environment identifier without an allowed literal lookup"
    return None


def _inline_program_reason(segment: list[str], dumped_files: set[str]) -> str | None:
    found = _command_at(segment)
    if not found:
        return None
    cmd, args, _ = found
    if not _is_interpreter_command(cmd):
        return None
    reason = _worker_env_reason(segment)
    if reason:
        return reason
    try:
        # Decode shell quoting across all arguments, including glued values.
        # Do not infer which interpreter flags select program text.
        program = " ".join(shlex.split(" ".join(args), posix=True))
    except ValueError:
        return "interpreter arguments could not be parsed safely"
    reason = _program_reason(cmd, program)
    if reason:
        return reason
    if _is_python_command(cmd) and re.search(r"\b(?:open|read_text|read_bytes)\s*\(", program):
        paths = re.findall(r"[\"']([^\"']+)[\"']", program)
        if any(os.path.normpath(path) in dumped_files for path in paths):
            return "inline program would display a redirected environment dump"
    return None


def _heredoc_inputs(command: str) -> dict[str, list[tuple[str, bool]]]:
    """Retain closed script inputs for inspection at their consumer statement."""
    documents: dict[str, list[tuple[str, bool]]] = {}
    lines = _collapse_shell_line_continuations(command).split("\n")
    index = 0
    quote = ""
    while index < len(lines):
        opener = _strip_shell_comments(lines[index])
        index += 1
        pending = skippable_heredoc_delimiters(opener, initial_quote=quote)
        quote = shell_quote_after(opener, quote)
        if not pending:
            continue
        for delimiter, strip_tabs, quoted in pending:
            start = index
            while index < len(lines) and (lines[index].lstrip("\t") if strip_tabs else lines[index]) != delimiter:
                index += 1
            if index == len(lines):
                break
            body = "\n".join(line.lstrip("\t") if strip_tabs else line for line in lines[start:index])
            index += 1
            documents.setdefault(delimiter, []).append((body, quoted))
    return documents


def _heredoc_reason(
    segment: list[str],
    documents: dict[str, list[tuple[str, bool]]],
    copied: set[str],
    named: dict[str, str],
    dumped_files: set[str],
    depth: int,
) -> str | None:
    found = _command_at(segment)
    if not found:
        return None
    cmd, args, _ = found
    for index, token in enumerate(args[:-1]):
        if token == "<<<":
            inputs = [(body, True) for body in _script_words(args, index + 1)]
        elif token in {"<<", "<<-"}:
            pending = documents.get(_strip_quotes(args[index + 1]), [])
            inputs = [pending.pop(0)] if pending else []
        else:
            continue
        for body, quoted in inputs:
            if _has_override(segment):
                continue
            if not quoted and _expanded_secret_var('"' + body + '"', copied, named):
                return "expanding here-document can expose a secret value"
            if cmd in SHELL_COMMANDS:
                reason = _scan_command(body, set(copied), dict(named), depth=depth + 1, dumped_files=dumped_files)
            else:
                reason = _program_reason(cmd, body)
            if reason:
                return reason
    return None


def _is_python_command(command: str) -> bool:
    return bool(re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", command.rsplit("/", 1)[-1]))


def _worker_env_reason(seg: list[str]) -> str | None:
    command = _command_at(seg)
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd == WORKER_ENV_MODULE and WORKER_ENV_COMMAND in args:
        return "`worker-env` can print environment values"
    if _is_python_command(cmd):
        for index, arg in enumerate(args[:-1]):
            if (
                _strip_quotes(arg) == "-m"
                and _strip_quotes(args[index + 1]) == WORKER_ENV_MODULE
                and any(_strip_quotes(candidate) == WORKER_ENV_COMMAND for candidate in args[index + 2 :])
            ):
                return "`python -m scripts.session_supervisor worker-env` can print environment values"
    return None


def _file_args(cmd: str, args: list[str]) -> list[str]:
    files: list[str] = []
    i = 0
    while i < len(args):
        token = _strip_quotes(args[i])
        redirection_skip = _redirection_skip_count(token)
        if redirection_skip:
            i += redirection_skip
            continue
        if token == "--":
            files.extend(args[i + 1 :])
            break
        if cmd in {"head", "tail"} and token in {"-n", "--lines", "-c", "--bytes"} and i + 1 < len(args):
            i += 2
            continue
        if token.startswith("--lines=") or token.startswith("--bytes="):
            i += 1
            continue
        if token.startswith("-") or token.startswith("+"):
            i += 1
            continue
        files.append(args[i])
        i += 1
    return files


def _redirection_skip_count(token: str) -> int:
    if token in {"<<", "<<-", "<", ">", ">>", "<>", ">|", "&>", "&>>", "<<<"}:
        return 2
    if token.startswith("<<"):
        return 1
    fd_trimmed = token.lstrip("0123456789")
    if fd_trimmed in {"<", ">", ">>", "<>", ">|"}:
        return 2
    if fd_trimmed.startswith(("<", ">")):
        return 1
    if fd_trimmed.startswith("&>"):
        return 1
    return 0


def _grep_has_safe_flag(cmd: str, args: list[str]) -> bool:
    if _grep_is_key_only(args):
        return True
    return cmd in {"grep", "ugrep"} and (
        _has_short_flag(args, "L") or any(_strip_quotes(arg) == "--files-without-match" for arg in args)
    )


def _grep_file_args(args: list[str]) -> list[str]:
    positionals: list[str] = []
    pattern_from_option = False
    i = 0
    opts_with_value = {
        "-A",
        "-B",
        "-C",
        "-e",
        "-f",
        "-m",
        "--after-context",
        "--before-context",
        "--context",
        "--file",
        "--max-count",
        "--regexp",
    }
    while i < len(args):
        token = _strip_quotes(args[i])
        if token == "--":
            positionals.extend(args[i + 1 :])
            break
        if token in opts_with_value and i + 1 < len(args):
            if token in {"-e", "--regexp"}:
                pattern_from_option = True
            i += 2
            continue
        if token.startswith("--regexp=") or token.startswith("--file="):
            pattern_from_option = True
            i += 1
            continue
        if token.startswith("-e") and len(token) > 2:
            pattern_from_option = True
            i += 1
            continue
        if token.startswith("-"):
            i += 1
            continue
        positionals.append(args[i])
        i += 1
    if pattern_from_option:
        return positionals
    return positionals[1:] if len(positionals) > 1 else []


def _echo_secret_reason(seg: list[str], copied: set[str], named: dict[str, str]) -> str | None:
    command = _command_at(seg)
    if command is None:
        return None
    cmd, args, _idx = command
    if cmd not in {"echo", "printf"}:
        return None
    for arg in args:
        secret_name = _expanded_secret_var(arg, copied, named)
        if secret_name:
            return f"`{cmd}` would print ${secret_name}"
    return None


def _track_secret_copies(seg: list[str], copied: set[str], named: dict[str, str]) -> None:
    """Remember simple assignments to secret values within this shell command."""
    command = _command_at(seg)
    nameref = False
    if command is None:
        assignments = seg
    else:
        cmd, args, _ = command
        if cmd in {"unset", "read"}:
            names = {_strip_quotes(arg) for arg in args if not arg.startswith("-")}
            copied.difference_update(names)
            for name in names:
                named.pop(name, None)
        if cmd == "read":
            for index, token in enumerate(args[:-1]):
                if token == "<<<" and _expanded_secret_var(args[index + 1], copied, named):
                    copied.update(_strip_quotes(arg) for arg in args[:index] if not arg.startswith("-"))
        # A prefix assignment belongs to this invocation only. Declarations
        # and assignment-only statements can affect later commands.
        assignments = args if cmd in {"export", "declare", "typeset", "readonly", "local"} else []
        nameref = cmd in {"declare", "typeset", "local"} and any(
            token.startswith("-") and "n" in token[1:] for token in args
        )
    for token in assignments:
        clean = _strip_quotes(token)
        if not _is_assignment(clean):
            continue
        name, value = clean.split("=", 1)
        if _expanded_secret_var(value, copied, named) or (nameref and (_is_secret_var_name(value) or value in copied)):
            copied.add(name)
            named.pop(name, None)
        else:
            copied.discard(name)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
                named[name] = value
            else:
                named.pop(name, None)


def _danger_reason(
    pipeline: list[list[str]],
    copied: set[str],
    named: dict[str, str],
    dumped_files: set[str],
    documents: dict[str, list[tuple[str, bool]]],
    substitutions: dict[str, tuple[str, str]],
    depth: int,
) -> str | None:
    if not pipeline:
        return None
    if _has_override(pipeline[0]):
        # Inputs still belong to this pipeline even when its policy is bypassed.
        # Consume them so a later owner reusing a delimiter gets its own body.
        for segment in pipeline:
            for index, token in enumerate(segment[:-1]):
                pending = documents.get(_strip_quotes(segment[index + 1]), [])
                if token in {"<<", "<<-"} and pending:
                    pending.pop(0)
        return None

    reason = _env_dump_reason(pipeline, dumped_files, substitutions)
    if reason:
        return reason

    for i, segment in enumerate(pipeline):
        for token in segment:
            for marker, (_, body) in substitutions.items():
                if marker in token:
                    reason = _scan_command(body, set(copied), dict(named), depth=depth + 1, dumped_files=dumped_files)
                    if reason:
                        return reason
        reason = _sensitive_file_reason(pipeline, i, dumped_files)
        if reason:
            return reason
        reason = _inline_program_reason(segment, dumped_files)
        if reason:
            return reason
        for index, token in enumerate(segment[:-1]):
            source = segment[index + 1]
            if token == "<<<" and _expanded_secret_var(source, copied, named):
                found = _command_at(segment)
                if found and found[0] != "read":
                    return "here-string would expose a secret value"
        reason = _worker_env_reason(segment)
        if reason:
            return reason
        reason = _echo_secret_reason(segment, copied, named)
        if reason:
            return reason
        _track_secret_copies(segment, copied, named)
        reason = _heredoc_reason(segment, documents, copied, named, dumped_files, depth)
        if reason:
            return reason
    return None


def _sensitive_path(path: str) -> bool:
    clean = os.path.normpath(_strip_quotes(path))
    if clean.startswith("//"):
        clean = clean[1:]
    return _is_known_secret_file(clean) or bool(re.fullmatch(r"/proc/[^/]+/environ", clean))


def _non_printing_command(cmd: str, args: list[str]) -> bool:
    if cmd == "file":
        options = args[: args.index("--")] if "--" in args else args
        return not (_has_short_flag(options, "f") or any(arg.split("=", 1)[0] == "--files-from" for arg in options))
    if cmd in NON_PRINTING_COMMANDS:
        return True
    return cmd == "wc" and args in [["-c"], ["--bytes"], ["-l"], ["--lines"]]


def _output_sink_safe(body: str) -> bool:
    pipelines = _pipelines(body)
    return bool(pipelines) and all(
        (found := _command_at(segment)) is not None
        and (_non_printing_command(found[0], _without_redirects(found[1])) or _is_safe_transform(segment))
        for pipeline in pipelines
        for segment in pipeline
    )


def _sensitive_file_reason(pipeline: list[list[str]], index: int, dumped_files: set[str]) -> str | None:
    found = _command_at(pipeline[index])
    if not found:
        return None
    cmd, args, _ = found
    if cmd == "file" and not _non_printing_command(cmd, _without_redirects(args)):
        return "file-list input could expose sensitive values as filenames"
    # Preserve the explicitly documented source-data-flow residual.
    if cmd in {"source", "."}:
        return None
    # Echo/printf arguments are literal text, not file operands. Their input
    # redirections still follow the sensitive-input policy below.
    operands = (
        [] if cmd in {"echo", "printf"} else _grep_file_args(args) if cmd in GREP_COMMANDS else _file_args(cmd, args)
    )
    operands += [args[i + 1] for i, token in enumerate(args[:-1]) if token in {"<", "<>"}]
    # Named file operands (e.g. dd's if=) and long options carry the same path.
    operands += [_strip_quotes(arg).split("=", 1)[1] for arg in args if "=" in arg and not _redirection_skip_count(arg)]
    paths = [_strip_quotes(arg) for arg in operands]
    sensitive = [path for path in paths if _sensitive_path(path) or os.path.normpath(path) in dumped_files]
    if not sensitive:
        return None
    options = [arg for arg in _without_redirects(args) if arg not in sensitive]
    if _non_printing_command(cmd, options) or _is_safe_transform([cmd, *options]):
        return None
    if cmd in GREP_COMMANDS and _grep_has_safe_flag(cmd, args):
        return None
    if cmd in DISPLAY_FILE_COMMANDS | GREP_COMMANDS and _has_safe_downstream(pipeline, index):
        return None
    return "command could expose contents of a sensitive file"


def _substitution_spans(command: str, *, heredoc: bool = False) -> list[tuple[int, int, str]]:
    """Executable command and process substitutions with their source spans."""
    spans: list[tuple[int, int, str]] = []
    quote = ""
    index = 0
    while index < len(command):
        char = command[index]
        if char == "\\" and (quote != "'" or heredoc):
            index += 2
            continue
        if not heredoc and char == "'" and quote != '"':
            quote = "" if quote else "'"
        elif not heredoc and char == '"' and quote != "'":
            quote = "" if quote else '"'
        elif quote != "'" and char == "`":
            end = index + 1
            while end < len(command) and command[end] != "`":
                end += 2 if command[end] == "\\" else 1
            if end < len(command):
                spans.append((index, end + 1, command[index + 1 : end]))
                index = end
        elif quote != "'" and (
            command.startswith("$(", index) or (not heredoc and command[index : index + 2] in {"<(", ">("})
        ):
            if command.startswith("$((", index):
                index += 1
                continue
            start = index + 2
            depth = 1
            quotes = [""]
            end = start
            while end < len(command) and depth:
                current = command[end]
                if current == "\\" and quotes[-1] != "'":
                    end += 2
                    continue
                if command.startswith("$(", end) and not command.startswith("$((", end) and quotes[-1] != "'":
                    depth += 1
                    quotes.append("")
                    end += 2
                    continue
                if current == "'" and quotes[-1] != '"':
                    quotes[-1] = "" if quotes[-1] else "'"
                elif current == '"' and quotes[-1] != "'":
                    quotes[-1] = "" if quotes[-1] else '"'
                elif not quotes[-1]:
                    if current == "(":
                        depth += 1
                        quotes.append("")
                    elif current == ")":
                        depth -= 1
                        quotes.pop()
                end += 1
            if not depth:
                spans.append((index, end, command[start : end - 1]))
                index = end - 1
        index += 1
    return spans


def _substitution_bodies(command: str) -> list[str]:
    return [body for _, _, body in _substitution_spans(command)]


def _eval_secret_source(args: list[str], copied: set[str], named: dict[str, str]) -> bool:
    """Whether a dynamic eval operand can assemble a known secret source."""
    for word in re.findall(r"[^\s;'\"()]+", " ".join(args)):
        if _is_known_secret_file(word) or _expanded_secret_var(word, copied, named):
            return True
    return False


def _script_words(args: list[str], index: int) -> list[str]:
    """Decode adjacent quote fragments for shell and interpreter script words."""
    if index >= len(args):
        return []
    try:
        words = shlex.split("".join(args[index:]), posix=True)
    except ValueError:
        return [_strip_quotes(args[index])]
    return [words[0]] if words else []


def _shell_script(args: list[str]) -> list[str]:
    """Extract the script operand of a shell -c invocation."""

    i = 0
    while i < len(args):
        option = _strip_quotes(args[i])
        if option in {"-o", "-O", "+O", "--rcfile", "--init-file"}:
            i += 2
            continue
        if option.startswith(("--rcfile=", "--init-file=")):
            i += 1
            continue
        if option.startswith("--"):
            i += 1
            continue
        if option.startswith("-") and not option.startswith("--"):
            script_index = i + 1 + sum(flag in {"o", "O"} for flag in option[1:])
            if "c" in option[1:]:
                return _script_words(args, script_index)
            i = script_index
            continue
        break
    return []


def _hide_substitutions(command: str) -> tuple[str, dict[str, tuple[str, str]]]:
    """Keep each executable substitution attached to its containing statement."""
    substitutions = {}
    out = []
    cursor = 0
    for start, end, body in _substitution_spans(command):
        marker = f"__GUARD_SUBSTITUTION_{len(substitutions)}__"
        while marker in command:
            marker += "_"
        substitutions[marker] = ("`" if command[start] == "`" else command[start : start + 2], body)
        out.extend((command[cursor:start], marker))
        cursor = end
    out.append(command[cursor:])
    return "".join(out), substitutions


def _scan_command(
    command: str,
    copied: set[str],
    named: dict[str, str] | None = None,
    *,
    depth: int = 0,
    dumped_files: set[str] | None = None,
) -> str | None:
    if depth >= 12:
        return "shell recursion limit reached while scanning for secret output"
    if named is None:
        named = {}
    documents = _heredoc_inputs(command)
    if dumped_files is None:
        # Files written by nested shells remain readable by their parent.
        dumped_files = set()
    # Leave ANSI-C delimiters undecoded until tokenization, so the shared
    # parser cannot strip an exotic here-doc on a second pass.
    executable = preprocess_shell_command(command)
    executable, substitutions = _hide_substitutions(executable)
    for pipeline in _pipelines(executable):
        reason = _danger_reason(pipeline, copied, named, dumped_files, documents, substitutions, depth)
        if reason:
            return reason
        for segment in pipeline:
            found = _command_at(segment)
            if found is None:
                continue
            cmd, args, _ = found
            # Restore substitution syntax for the dynamic-eval and -c checks.
            for marker, (prefix, body) in substitutions.items():
                spelling = prefix + body + ("`" if prefix.startswith("`") else ")")
                args = [arg.replace(marker, spelling) for arg in args]
            if cmd == "__UNDECIDABLE_SECRET_COMMAND__":
                return "shell command could not be parsed safely"
            if cmd == "eval" and args:
                if any(_substitution_bodies(arg) for arg in args) and _eval_secret_source(args, copied, named):
                    return "dynamic eval can reach a known secret source"
                reason = _scan_command(
                    " ".join(_strip_quotes(arg) for arg in args),
                    set(copied),
                    dict(named),
                    depth=depth + 1,
                    dumped_files=dumped_files,
                )
                if reason:
                    return reason
            elif cmd in {"bash", "sh", "dash", "zsh", "ksh"}:
                for script in _shell_script(args):
                    reason = _scan_command(script, set(copied), dict(named), depth=depth + 1, dumped_files=dumped_files)
                    if reason:
                        return reason
    return None


def _block_msg(reason: str) -> str:
    return (
        f"BLOCKED by guard-secret-print (#M-5): {reason}.\n\n"
        "Do not print secret values into the transcript. Use a value-free check instead:\n"
        "  - JSON: `jq keys <file>`\n"
        "  - shell env/dotenv: `cut -d= -f1 <file>` or `env | cut -d= -f1`\n"
        '  - presence: `[ -n "${X:-}" ] && echo SET`\n\n'
        "Override for a deliberate exception: `LEARN_UK_SECRETS_OK=1 <command>`.\n"
        "Hook source: agents_extensions/shared/hooks/guard-secret-print.py\n"
    )


def main() -> int:
    if os.environ.get("LEARN_UK_SECRETS_OK") == "1":
        return 0

    payload = _read_payload()
    if payload is None or not isinstance(payload.get("tool_input", {}), dict):
        sys.stderr.write(_block_msg("malformed hook payload"))
        return 2
    if not isinstance(payload.get("tool_input", {}).get("command", ""), str):
        sys.stderr.write(_block_msg("malformed hook command"))
        return 2
    command = _command(payload)
    if not command:
        return 0

    try:
        reason = _scan_command(command, set())
    except ShellPreprocessLimit:
        reason = "nested shell command could not be parsed safely"
    if reason:
        sys.stderr.write(_block_msg(reason))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
